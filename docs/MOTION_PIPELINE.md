# URDF-bound motion authoring and imitation-training pipeline

[한국어 상세 안내](MOTION_PIPELINE_KO.md) · [Existing Isaac setup](../HEADLESS_TRAINING.md) · [Local evidence](experiments/motion-pipeline-local.md)

[Developer/AI handoff and NPZ schema](MOTION_PIPELINE_HANDOFF.md) · [Current branch review](experiments/motion-pipeline-review.md). The earlier local evidence has its own source fingerprints; regenerate data after updating this branch.

This branch connects CPU reference authoring to the repository's existing `snu_gom_walk`, `scripts/train.py`, and `scripts/play.py`. Source URDFs, meshes, axes and inertias remain intact. No GPU training or server connection was performed for this change. Passing kinematics is explicitly separate from passing free-base dynamics or demonstrating natural walking.

## Local use

Use Python 3.11 and a personal environment. On Linux, replace the Windows Python path below with `.venv-motion/bin/python`.

```powershell
git clone --branch feature/urdf-motion-pipeline https://github.com/mjcha924/snu-gom.git
cd snu-gom
python -m venv .venv-motion
.\.venv-motion\Scripts\python.exe -m pip install -r requirements-motion-pipeline.txt
# Only if Torch is absent in a CPU test environment; do not replace a server's CUDA Torch.
.\.venv-motion\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py inspect
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py run --count 4 --seconds 4 --fps 50
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py review
```

The Windows launcher `모션_검토.cmd` opens the latest review. The self-contained HTML displays authored and physically simulated collision geometry, clip selection, camera rotation, pause/seek controls, joint angles, applied torques and acceptance reports. It does not need a web server or CDN. Replaying a finite clip in that viewer does not certify seamless periodic walking.

## Model changes

Edit [`configs/motion_pipeline/gom.json`](../configs/motion_pipeline/gom.json) or supply `--profile` / `--urdf` to `inspect` and `run`. URDF contents, referenced visual/collision mesh contents, the explicit profile, and authoring/validation code are fingerprinted. Changed masses, geometry, joint limits or meshes invalidate old training references. USD cache keys use the selected live model. Renderer-only changes do not invalidate dynamics.

The profile defines joint names/order, body roles, nominal posture, planning ranges, motor assumptions and gates. The Isaac adapter currently requires the SNU GOM ten-leg-plus-two-neck joint contract. Geometry/inertia/limit updates with that contract are supported; changed topology/names need an explicit adapter review. Unknown mappings are rejected rather than guessed.

Relative meshes work directly. Map `package://` URIs using `package_roots`. Single box soles have an automatic contact datum; multiple colliders require a selected `sole_collisions` entry or explicit frame. STL/OBJ mesh soles require per-foot `sole_frames` entries containing link-local `xyz` and `rpy`. Contact sampling uses their convex hull. Other sole primitives require an adapter. Mesh convexification and unmeasured rigid contacts remain approximations.

Default self-collision checking is strict. Optional `allowed_collision_pairs` state both the pair and maximum planning penetration in metres. They do not disable whole pairs in physics or Isaac. Planning knee windows are not added as fictional physical stops: MuJoCo retains the original URDF stops.

## Authoring and acceptance

The architecture takes inspiration from [BDX §V-A](https://arxiv.org/html/2501.05204v1): task-space gait authoring, CoM/CoP planning, whole-body motion, pre-sampled interpolation. It is an independent implementation, not Disney's private generator or equivalent performance. Gaussian episodic time features/sensor noise in the paper are not interpreted as a distribution of walking clips.

The finite reference uses C2 swing/landing curves, initial/final double support, a full-horizon LIPM CoP/CoM QP with 2D convex support polygons, and analytic-Jacobian whole-body IK. A second QP softly follows the observed low-edge contact patch within a 2 mm CoM trust region, retaining hard outer-support constraints. It does not certify exact rocking contact. Pelvis height and torso style are authored separately; actual CoM height varies. Joint position/slew constraints are enforced. With no ankle roll, the sole can passively rock while its lowest collision surface remains above the floor.

Bounded seeded parameter sampling produces stand/walk train/val clips. Each kind has an independent held-out clip, and attempts are capped. Retrying reduces task demands rather than relaxing gates. Full-frame checks cover names, hashes, FK, velocity consistency, ROM/speed, task errors, self-collision and foot/body ground penetration. Support AABB margin is a diagnostic, not a dynamic certificate.

An independent full-frame inverse-dynamics screen minimizes the maximum normalized joint torque under floating-base equations, unilateral forces and friction constraints. It uses the optimistic outer stance-sole footprint, so passing is a necessary-condition screen, not contact feasibility proof. Excessive required torque rejects a reference. Unresolved contact-balance frames are labeled conditional rather than confused with excessive motor torque; zero solved frames rejects the reference. `*.screen.json` records this separately from tracking performance.

MuJoCo diagnostics use gravity, friction, a free root and bounded joint efforts. The controller includes joint/CoM/foot velocity and acceleration feedforward. Loaded support uses vertical force with hysteresis rather than geometry proximity. It obtains acceleration sensitivity from MuJoCo's own soft-contact inverse dynamics and verifies candidates through actual forward dynamics. No root force or post-reset root teleportation is applied. Physical qualification requires full-duration survival, motor/ROM/speed/tilt/collision limits, loaded contact agreement, single support, supported qualified alternating touchdowns and progress. Short `--physics-seconds` diagnostics never qualify the full clip. These diagnostics do not automatically block imitation training.

Outputs under `reports/motion_pipeline/<model-id>-<run-id>/` include NPZ motion arrays, metadata, full-frame validation, physical reports/trace/torque CSV, manifest, summary and offline review HTML. `latest.json` points at the newest run. Generated datasets and large HTML traces are not committed as source.

`summary.json.complete` requires eligible stand/walk clips in both train and val. If bounded retries cannot produce all four pairs, the command saves its review and exits unsuccessfully with the missing pairs. Relative `--output` paths are supported. Source fingerprints normalize Python CRLF/LF differences; data, reports and robot-asset hashes remain byte-exact.

## CPU handoff checks and dataset export

```powershell
$motionRun = (Get-Content reports/motion_pipeline/latest.json -Raw | ConvertFrom-Json).run
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py train-plan --run $motionRun --kind stand
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py train-plan --run $motionRun --kind walk
# Add --require-dynamics only if a passing local tracking rollout is required.
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py export --run $motionRun
.\.venv-motion\Scripts\python.exe -m unittest discover -s tests/motion_pipeline -v
```

`train-plan` performs live asset/data/report integrity checks and writes eligible train/val IDs plus the exact command. It imports no Isaac and starts no training. Default training admits full-frame kinematic and motor-screened references independently of tracking-controller success. `--require-dynamics` additionally demands passing physics. The compatibility flag `--allow-kinematic` cannot bypass motor screening. Duplicate/tampered/stale data and train/val leaks are rejected. The export ZIP whitelists motion arrays and reports, preserving repository-relative paths for extraction at the server repository root. It includes no credentials, VPN profiles, recordings or environments.

## Later on the GPU server

Use a personal checkout of this branch and the environment pinned in [HEADLESS_TRAINING.md](../HEADLESS_TRAINING.md). Do not modify a shared IsaacLab/conda installation. Upload the data ZIP once to the team's designated location; keep code and model revision consistent. The runtime loader needs the existing NumPy/SciPy/Torch environment, not the complete CPU-authoring dependency set.

Check `nvitop`, then start with 32 environments and two iterations:

```bash
python scripts/train.py --task stand --motion-manifest reports/motion_pipeline/<run>/manifest.json \
  --num-envs 32 --iterations 2 --memory-fraction .35 --headless
python scripts/train.py --task walk --motion-manifest reports/motion_pipeline/<run>/manifest.json \
  --num-envs 32 --iterations 2 --memory-fraction .35 --headless
python scripts/play.py --checkpoint runs/<run>/model.pt --episodes 2 --seconds 4 --headless
```

Library mode keeps ten leg actions and twelve measured joints. Reference-conditioned observations have 72 policy / 90 critic values. Clip sampling is random during training; evaluation cycles through held-out val clips. Finite endpoints terminate rather than silently wrapping. The neck follows the reference. Targets are interpolated from 50 Hz to the existing 500 Hz simulation, with explicit bounded PD effort and a symmetric 5 V torque-speed envelope. The offline inverse-dynamics controller and training PD controller are intentionally different controllers within the same provisional effort envelope.

The manufacturer lists [XL330-M288](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/) at 0.52 N·m stall / 103 rpm no-load and [XC330-M288](https://emanual.robotis.com/docs/en/dxl/x/xc330-m288/) at 0.93 N·m / 81 rpm, at 5 V. The generous reference-planning cap is 60% stall: **0.312 / 0.558 N·m**, further limited by speed. XC330 uses approximate points read from the official loaded performance graph; XL330 retains an assumed linear envelope. These are **not continuous/thermal ratings**. The profile explicitly overrides placeholder URDF effort/velocity (0.15 N·m / 1 rad/s); turn that override off to preserve smaller URDF limits. Original position stops remain active. Planning speed is 35% no-load; IK slew remains at most 0.8 rad/s. Both CPU and Isaac paths use the same profile and curve; BAM is separate.

Torch's default memory fraction is .35 (maximum .4), which does not bound PhysX/renderer memory. Source/model/dataset changes require a new experiment; existing checkpoint provenance is not bypassed. See [hip-roll causal diagnosis](experiments/hip-roll-torque-diagnosis.md) for the self-contact counterfactual and hardware implications.

The new Isaac path was checked against the repository's pinned public source revision `f4aa17f87e2e5db5484f0b5974918573e8918ce2` for explicit actuators and root-link velocity APIs, and syntax/CPU data contracts were checked locally. It has **not** been run in Isaac for this change. Online speed/turn blending, seamless infinite cycles, identified hardware parameters, GPU smoke tests and physical transfer remain future work.

The dataset exporter includes data only. Keep the selected URDF and all referenced meshes in the checkout with relative or `package://` URIs; external assets and absolute mesh URIs are rejected for portable export. Full motor curves must have increasing speeds starting at zero and nonnegative decreasing torques ending at zero. Unknown joint overrides and partial/invalid curves are rejected before generation. `motors.planning_stall_fraction` is active; `physics.stall_fraction` is a legacy fallback, not an additional multiplier.
