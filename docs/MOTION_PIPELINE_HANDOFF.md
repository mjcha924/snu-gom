# Motion pipeline handoff / 개발 인수인계

This is the entry point for a teammate or coding agent continuing the
`feature/urdf-motion-pipeline` branch. It explains what can be reproduced on a
CPU, where to make changes, and what the results mean.

처음 사용하는 사람은 [한국어 실행 안내](MOTION_PIPELINE_KO.md)를 따라
설치·생성·확인 화면·학습 전 점검을 실행하면 됩니다. 이 문서는 코드 위치와
데이터 규격, URDF 변경 시 다시 해야 할 작업을 설명합니다.

- [English usage guide](MOTION_PIPELINE.md)
- [Branch review and current evidence](experiments/motion-pipeline-review.md)
- [Earlier CPU experiment](experiments/motion-pipeline-local.md) — historical,
  with its own fingerprints; regenerate data for the current source.
- [Pinned Isaac environment](../HEADLESS_TRAINING.md)

## Start from the right branch

All commands below assume the repository root. The environments and generated
datasets are local outputs; they are not supplied in Git.

```bash
git clone --branch feature/urdf-motion-pipeline https://github.com/mjcha924/snu-gom.git
cd snu-gom
python -m venv .venv-motion
# Windows: .venv-motion\Scripts\activate
# Linux:   source .venv-motion/bin/activate
python -m pip install -r requirements-motion-pipeline.txt
# CPU tests only; keep an existing server's CUDA Torch intact.
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python scripts/motion_pipeline.py inspect
python scripts/motion_pipeline.py run --output reports/motion_pipeline --count 4 --seconds 4 --fps 50
python scripts/motion_pipeline.py review
```

The `run` command prints `RUN_DIRECTORY`. Substitute that directory for
`<run-directory>` below. A relative output directory is resolved from the current
working directory. Relative URDF/profile package-root entries are resolved from
the repository root; relative mesh URIs are resolved from the URDF directory.

```bash
python scripts/motion_pipeline.py train-plan --run <run-directory> --kind stand
python scripts/motion_pipeline.py train-plan --run <run-directory> --kind walk
python scripts/motion_pipeline.py export --run <run-directory>
```

`train-plan` validates both train and val and writes the exact small GPU command
to `train-plan.json`. It does not launch Isaac or train a policy. Each invocation
replaces that file for the selected kind. Run this in the server checkout again
after extracting the exported data there.

The exporter writes a data-only ZIP with paths relative to the repository root.
Extract it at the root of the **same code/model revision** on the server. URDFs,
meshes, dependencies, videos, private local CAD and checkpoints are not in this
ZIP. Use portable relative or `package://` mesh URIs; keep the selected URDF and
assets in the repository for server export. Export rejects external assets and
absolute mesh URIs. Source files use LF so Windows and Linux checkouts retain
the same authoring fingerprints.

## Code map

| File | Responsibility / change here when… |
| --- | --- |
| `configs/motion_pipeline/gom.json` | Body/joint roles, working ROM, nominal pose, motor assumptions, gait parameters, gates |
| `scripts/motion_pipeline.py` | Public CPU commands: inspect, run, review, train-plan, export |
| `motion_pipeline/model.py` | Read URDF, resolve/hash assets, preserve inertia, construct the MuJoCo adapter and sole datum |
| `motion_pipeline/generate.py` | Task-space curves, CoM/CoP QP, contact-patch refinement, whole-body IK, NPZ fields |
| `motion_pipeline/contract.py` | Cheap NPZ shape/time/unit conventions and the current Isaac adapter preflight |
| `motion_pipeline/validate.py` | Full-frame FK, derivatives, collision, floor, ROM/speed and task-error checks |
| `motion_pipeline/motors.py` | Shared CPU/Torch torque-speed curves and provisional effort/speed planning caps |
| `motion_pipeline/feasibility.py` | Independent inverse-dynamics torque screen, solved/unresolved frame accounting |
| `motion_pipeline/physics.py` | Free-root MuJoCo diagnostic, bounded torque tracker, loaded contacts and stepping checks |
| `motion_pipeline/library.py` | Seeded train/val authoring, bounded retries, provenance checks, dataset export |
| `motion_pipeline/bank.py` | Finite-clip Torch interpolation and reference observation features |
| `motion_pipeline/review.py` | Standalone HTML review of reference and diagnostic collision geometry |
| `snu_gom_walk/env.py` | Isaac residual actions, explicit bounded PD, observations/rewards, resets and episode endpoints |
| `scripts/train.py`, `scripts/play.py` | Dataset/model preflight, training configuration and checkpoint provenance |
| `tests/motion_pipeline/` | CPU integration and failure-mode regression tests |

Paths beginning with `motion_pipeline/` in this table are under
`snu_gom_walk/`. The native Isaac importer is `snu_gom_walk/native_model.py`.
It is separate from the MuJoCo adapter; passing the latter cannot validate the
former's runtime by itself.

## Pipeline and acceptance meanings

1. Read the live URDF/profile/assets and compute a model fingerprint.
2. Sample gait parameters using the run seed; generate finite stand/walk clips
   with initial/final double support, authored pelvis/torso curves, a planar
   LIPM CoM/CoP QP, and constrained whole-body IK.
3. Check every exported frame against geometry, derivatives and planning limits.
4. Independently minimize maximum normalized joint torque using floating-base
   equations and unilateral friction-limited forces over the outer sole hull.
5. Run a separate bounded-torque, free-root MuJoCo tracking diagnostic.
6. Save eligible train/val clips, all attempted results, HTML review, and a
   manifest that binds the input assets, authoring sources and reports.
7. Load eligible references in the existing Isaac policy as position/velocity
   targets with residual leg actions. Validate new GPU behavior separately.

| Result | Meaning | Default learning gate |
| --- | --- | --- |
| `kinematic_verified` | Full-frame geometric/derivative checks pass | Required |
| `reference_eligible` | Kinematics and independent motor screen permit the candidate | Required |
| `motor_status=balance_unresolved` | Some contact-balance frames could not be solved; solved frames fit the planning envelope | Conditional reference allowed; unresolved frames remain visible |
| `dynamics_verified` | This free-root tracker passed every full-duration physics gate | Required only with `--require-dynamics` |
| `hardware_ready` | Actual hardware qualification | Always false for this pipeline |

Excessive required torque/speed, no solved motor-screen frames, numerical solver
errors, malformed data or stale hashes cannot be bypassed with
`--allow-kinematic`. That option is a compatibility alias. An LP numerical error
raises an error; an infeasible contact-balance equation is reported separately.
The LP uses normalized forces/torques and reports residuals in physical units.

`summary.json.complete` means all four required kind/split pairs are present:
stand/train, stand/val, walk/train, walk/val. Up to three attempts are made per
requested clip. An incomplete `run` exits unsuccessfully after saving its review
and summary. `accepted_kinematic` counts all attempted clips passing kinematics;
`accepted_reference` counts admitted references, which can be fewer.
`latest.json` points to the latest attempt, so check `complete` before handoff.

## NPZ data contract

NPZ files load with `allow_pickle=False`. Let `F` be the number of frames and
`J` the number of named joints. Units are SI: seconds, metres, radians, kg,
N·m. The world frame is Z-up. Root poses refer to the URDF root link, not the
whole-body CoM. Foot side order is `profile.feet` (left, right in the default).

| Required field | Shape | Convention |
| --- | --- | --- |
| `time`, `fps` | `(F,)`, scalar | Start at zero; positive uniform `1/fps`; at least 3 frames |
| `model_id`, `quaternion_order` | scalar strings | Live model hash; exactly `xyzw` in the NPZ |
| `joint_names` | `(J,)` strings | Exactly the profile's joint order |
| `joints_pos`, `joints_vel` | `(F,J)` | rad, rad/s; stored velocity checked against finite differences |
| `root_pos`, `root_quat` | `(F,3)`, `(F,4)` | World metres, unit quaternion in XYZW |
| `world_linear_vel`, `world_angular_vel` | `(F,3)` each | Root-link world linear/angular velocity, m/s and rad/s |
| `foot_positions_world`, `target_foot_positions_world` | `(F,2,3)` | Actual FK sole-datum position and task-space target, world metres |
| `foot_positions_body` | `(F,2,3)` | Actual sole-datum positions in the root frame |
| `sole_points_link` | `(2,3)` | Sole datum in each foot link's local frame, metres |
| `target_sole_height_m` | `(F,2)` | Authored swing clearance above the flat floor |
| `com_world`, `target_com_world` | `(F,3)` each | Whole-body actual CoM and planar-planning target; only XY task error is gated |
| `planned_contacts` | `(F,2)` | Binary stance schedule, at least one stance foot; no flight support |
| `phase` | `(F,)` | Authored gait phase used by the policy's phase features |

The generator also emits `joints_acc (F,J)`, `com_velocity_world (F,3)`,
`com_acceleration_world (F,3)`, `foot_velocities_world (F,2,3)`, and
`foot_accelerations_world (F,2,3)`. These feed the offline tracker. The schema
permits their omission for compatibility; the tracker then uses its documented
fallbacks. Numeric arrays must be finite. Additional metadata arrays are allowed.

`MotionBank` maps joints by name, converts root quaternion XYZW to Isaac/Torch
WXYZ, interpolates numeric states linearly and quaternions on the shortest arc,
and holds the preceding frame's discrete contacts. At the final or clamped end
time, contacts and state both use the final frame. It clamps finite clips;
the environment terminates rather than looping or switching to a default clip.

Library mode has 10 leg actions and 12 measured joints, with 72 policy / 90
critic observations (legacy mode: 45 / 63). The neck follows the reference.
Old checkpoints have a different observation contract and source fingerprint;
they are not interchangeable with newly trained library policies.

## What to do after a change

| Change | Required next step |
| --- | --- |
| Mass, inertia, geometry, mesh contents, limits or profile | Inspect; regenerate; full-frame validation and motor/physics diagnostics; review; train-plan; export |
| New sole shape or multiple colliders | Define `sole_frames`/`sole_collisions`, then the same complete cycle |
| Joint names/topology/root datum | Update profile and explicit CPU/native Isaac adapters, action/observation mapping and tests before training |
| Generator, contract, validator, motor or physics source | Rebuild references; source hashes intentionally reject stale datasets |
| Torch bank / Isaac observation or reward code | CPU contract checks and a new GPU smoke test; old checkpoint source provenance still rejects mismatches |
| HTML review only | Test viewer behavior; authoring data need not be rebuilt solely for rendering |

Only `bank.py` and `review.py` are excluded from the authoring-package source
hash. Training/checkpoint provenance separately covers the walking source.
Never fix a stale dataset by manually replacing its fingerprint strings.

## Known limits and the next useful experiment

The present references move slowly and still do not demonstrate natural walking.
The outer-sole motor LP is optimistic about actual rocking contact. The planar
planner and whole-body IK are not a contact-implicit trajectory optimizer or
Disney's private BDX generator. Rigid convexified contacts, estimated inertia,
unidentified pad properties and provisional 5 V motor curves limit transfer.
Planning caps are not measured continuous/thermal ratings. Passive foot roll
and missing ankle-roll actuation remain material hardware constraints.

No new Isaac training was run on this PC. On a suitable GPU machine, use the
pinned setup, re-run `train-plan`, and start with the printed 32-environment,
two-iteration command for stand and walk. Check reference resets, finite-clip
termination, held-out evaluation, applied torque caps, root-link velocities and
observation dimensions before a long run. Judge walking using clearance,
loaded alternating landings, progress, heading and survival as well as reward.
Online speed/turn blending, periodic transitions and hardware identification
are subsequent work.
