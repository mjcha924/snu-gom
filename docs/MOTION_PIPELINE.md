# URDF-bound motion authoring and imitation-training pipeline

[한국어 상세 안내](MOTION_PIPELINE_KO.md) · [Existing Isaac setup](../HEADLESS_TRAINING.md) · [Local evidence](experiments/motion-pipeline-local.md)

This branch connects CPU reference authoring to the repository's existing `snu_gom_walk`, `scripts/train.py`, and `scripts/play.py`. Source URDFs, meshes, axes and inertias remain intact. No GPU training or server connection was performed for this change. Passing kinematics is explicitly separate from passing free-base dynamics or demonstrating natural walking.

## Local use

Use Python 3.11 and a personal environment. On Linux, replace the Windows Python path below with `.venv-motion/bin/python`.

```powershell
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

The finite reference uses C2 swing/landing curves, initial/final double support, a full-horizon nominal-height LIPM CoP/CoM QP, and analytic-Jacobian whole-body IK. Pelvis height and torso style are authored separately; actual CoM height is free to vary. Joint position/slew constraints are enforced. With no ankle roll, the sole can passively rock while its actual lowest collision surface remains above the floor.

Bounded seeded parameter sampling produces stand/walk train/val clips. Each kind has an independent held-out clip, and attempts are capped. Retrying reduces task demands rather than relaxing gates. Full-frame checks cover names, hashes, FK, velocity consistency, ROM/speed, task errors, self-collision and foot/body ground penetration. Support AABB margin is a diagnostic, not a dynamic certificate.

MuJoCo diagnostics use gravity, friction, a free root and bounded joint efforts. The controller obtains acceleration sensitivity from MuJoCo's own soft-contact inverse dynamics and verifies candidates through actual forward dynamics. No root force or post-reset root teleportation is applied. Acceptance additionally requires full-duration survival, motor/ROM/speed/tilt/collision limits, contact agreement, single support, supported qualified alternating touchdowns and path progress. Short `--physics-seconds` diagnostics never qualify the full clip. Thresholds are provisional engineering choices, not paper constants.

Outputs under `reports/motion_pipeline/<model-id>-<run-id>/` include NPZ motion arrays, metadata, full-frame validation, physical reports/trace/torque CSV, manifest, summary and offline review HTML. `latest.json` points at the newest run. Generated datasets and large HTML traces are not committed as source.

## CPU handoff checks and dataset export

```powershell
$motionRun = (Get-Content reports/motion_pipeline/latest.json -Raw | ConvertFrom-Json).run
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py train-plan --run $motionRun --kind stand
# Explicit experimental use of a kinematic walking reference that may fail dynamics:
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py train-plan --run $motionRun --kind walk --allow-kinematic
.\.venv-motion\Scripts\python.exe scripts/motion_pipeline.py export --run $motionRun
.\.venv-motion\Scripts\python.exe -m unittest discover -s tests/motion_pipeline -v
```

`train-plan` performs live asset/data/report integrity checks and writes eligible train/val IDs plus the exact command. It imports no Isaac and starts no training. Default training rejects non-passing physics references; provisional imitation requires `--allow-kinematic`. Duplicate/tampered/stale data and train/val leaks are rejected. The export ZIP whitelists motion arrays and reports, preserving repository-relative paths for extraction at the server repository root. It includes no credentials, VPN profiles, recordings or environments.

## Later on the GPU server

Use a personal checkout of this branch and the environment pinned in [HEADLESS_TRAINING.md](../HEADLESS_TRAINING.md). Do not modify a shared IsaacLab/conda installation. Upload the data ZIP once to the team's designated location; keep code and model revision consistent. The runtime loader needs the existing NumPy/SciPy/Torch environment, not the complete CPU-authoring dependency set.

Check `nvitop`, then start with 32 environments and two iterations:

```bash
python scripts/train.py --task stand --motion-manifest reports/motion_pipeline/<run>/manifest.json \
  --num-envs 32 --iterations 2 --memory-fraction .35 --headless
python scripts/train.py --task walk --motion-manifest reports/motion_pipeline/<run>/manifest.json \
  --allow-kinematic --num-envs 32 --iterations 2 --memory-fraction .35 --headless
python scripts/play.py --checkpoint runs/<run>/model.pt --episodes 2 --seconds 4 --headless
```

Library mode keeps ten leg actions and twelve measured joints. Reference-conditioned observations have 72 policy / 90 critic values. Clip sampling is random during training; evaluation cycles through held-out val clips. Finite endpoints terminate rather than silently wrapping. The neck follows the reference. Targets are interpolated from 50 Hz to the existing 500 Hz simulation, with explicit bounded PD effort and a symmetric 5 V torque-speed envelope. The offline inverse-dynamics controller and training PD controller are intentionally different controllers within the same provisional effort envelope.

Effort is bounded by the smaller of the URDF limit, 20% of manufacturer stall, and the assumed linear speed envelope. These are **not measured continuous/thermal ratings**. Dynamics and training use the XL330/XC330 mapping; the separate BAM experiment is not silently enabled. Torch's default memory fraction is .35 (maximum .4), which does not bound PhysX/renderer memory. Follow team sharing rules for long/large jobs. Source/model/dataset changes require a new experiment; existing checkpoint provenance is not bypassed.

The new Isaac path was checked against the repository's pinned public source revision `f4aa17f87e2e5db5484f0b5974918573e8918ce2` for explicit actuators and root-link velocity APIs, and syntax/CPU data contracts were checked locally. It has **not** been run in Isaac for this change. Online speed/turn blending, seamless infinite cycles, identified hardware parameters, GPU smoke tests and physical transfer remain future work.
