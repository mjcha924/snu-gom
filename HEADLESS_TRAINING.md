# SNU-GOM headless walking experiments

The supplied robot remains in `snu_gom_description/`. New code uses Isaac Sim 5.1,
Isaac Lab, and RSL-RL 5.x from the existing local environment. No shared simulator
source or packages are modified. See [the plan](WALKING_TRAINING_PLAN.md) for
the character goals, validation stages, and model assumptions.

## Team setup: clone and reproduce

An opt-in [BAM XL330 M1 actuator experiment](docs/experiments/bam-actuators.md)
is available for Isaac Sim 5. It leaves the default implicit controller unchanged,
does not reuse XL330 fits on XC330 joints, and is not hardware-calibrated. Its first
neutral standing trial fails; use it for actuator validation, not a proven walking
upgrade. The linked guide contains fetch, standing, smoke-training, and parity commands.

The URDFs and all referenced STL visuals are committed directly: no private CAD
download, absolute mesh path, or Git LFS setup is required for this model. Generated
USDs, runtime caches, and training runs are intentionally not committed. The older
`robot/` proxy and its tools are retained separately; do not use that proxy's joint
mapping or mass as the contract for this policy.

The supplied robot package retains its existing `Proprietary` metadata and its
third-party CAD caveat in `snu_gom_description/docs/START_HERE.txt`. Including the
assets for team experiments does not relicense vendor CAD under the root code license.

Tested host: Ubuntu 22.04, Python 3.11.15, NVIDIA driver 580.178.04, RTX 3070 8 GB,
32 GB system RAM. The tested packages are Isaac Sim 5.1.0.0, Isaac Lab 0.54.3,
Isaac Lab RL 0.5.0, PyTorch 2.7.0+cu128, and RSL-RL 5.0.1. Isaac Lab source revision:
`f4aa17f87e2e5db5484f0b5974918573e8918ce2`.

For a new Linux workstation, install NVIDIA drivers and Python 3.11 first, then use
an isolated environment. These instructions reproduce the inspected package/source
versions; a fresh installation on a second machine has not yet been tested.
Review NVIDIA's [Isaac Sim Python installation and prerequisites](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_python.html).
The baseline intentionally pins the installed 5.1 release, which NVIDIA now marks
unsupported; upgrading requires rerunning the import and control checks.

```bash
git clone https://github.com/mjcha924/snu-gom.git
cd snu-gom
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'isaacsim[all,extscache]==5.1.0' --extra-index-url https://pypi.nvidia.com
python -m pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128
git clone https://github.com/isaac-sim/IsaacLab.git .deps/IsaacLab
git -C .deps/IsaacLab checkout f4aa17f87e2e5db5484f0b5974918573e8918ce2
./.deps/IsaacLab/isaaclab.sh --install rsl_rl
python -m pip install -r requirements-walking.txt
export SNU_GOM_PYTHON="$(command -v python)"
```

Isaac installation is large and requires accepting NVIDIA's license. The first
launch can download importer extensions and compile shaders; it is not an offline
installation. Run the validation commands below before a long experiment. An 8 GB
GPU runs this reduced configuration here, but is below NVIDIA's published 16 GB
minimum for the full Isaac Sim application. Do not extrapolate to camera training.

For CPU-only model checks (no Isaac installation required):

```bash
python -m pip install numpy==1.26.4 scipy==1.15.3
python -m pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cpu
python -m unittest discover -s tests/walking -v
```

## Run from the repository root

```bash
export SNU_GOM_PYTHON="${SNU_GOM_PYTHON:-python}"

"$SNU_GOM_PYTHON" -u scripts/check_setup.py --headless
"$SNU_GOM_PYTHON" -u scripts/check_model.py --headless
"$SNU_GOM_PYTHON" -u scripts/check_stand.py --headless --video

"$SNU_GOM_PYTHON" -u scripts/train.py --task walk --num-envs 64 --iterations 20 --headless
```

Training prints `RUN_DIRECTORY=...` and saves `model.pt`, numbered checkpoints,
`config.json`, `environment.yaml`, TensorBoard events, and `policy_jit.pt` there.
Successful completion writes `summary.json`, including throughput and an action
equivalence check between the original policy and exported TorchScript policy.

### Stepping follow-up

The next isolated reward ablation adds `--dense-lift` alongside
`--support-reference`: opposite-foot-supported clearance progress and swing-foot
unloading, with unchanged reference geometry and actuator limits. See
[v5 diagnostics and commands](docs/experiments/stepping-v5-diagnostics.md).
Qualified touchdown logging now rejects unsupported hops as well as insufficient
airtime/clearance, contact chatter, resets, and zero-command stepping. This changes
the environment-source hash; replay old checkpoints at their recorded revision.

#### Reference-assisted flat experiment

The next experiment is opt-in and separate from the reward-only baseline. It uses
an actual-URDF inverse-kinematics seed plus learned bounded position corrections.
The seed is checked for joint position/rate limits and foot placement, but that
does **not** establish dynamic balance. Physics remains free-base; no body pose,
contact, or foot trajectory is forced after reset. It starts from the checked
neutral crouch and blends the seed in over two seconds.

```bash
"$SNU_GOM_PYTHON" scripts/build_reference.py
"$SNU_GOM_PYTHON" scripts/check_stand.py --reference --seconds 12 --headless
"$SNU_GOM_PYTHON" scripts/train.py --reference --speed 0.01 --gait-period 4 --num-envs 512 --iterations 250 --output runs/reference_v3_512 --headless
"$SNU_GOM_PYTHON" scripts/compare_scenes.py --checkpoint runs/reference_v3_512/model.pt --episodes 3
```

The v3 reference converged to standing, not walking: all three 30-second trials
survived on each scene, but none had a clear touchdown. Its frozen source revision
is `dbfa33f`; old checkpoints cannot silently replay with newer environment code.

The next bounded experiment keeps the support knee shallow and derives foot
targets from the actual URDF geometry:

```bash
"$SNU_GOM_PYTHON" scripts/build_support_seed.py
"$SNU_GOM_PYTHON" scripts/audit_reference_support.py reports/support-seed.json
"$SNU_GOM_PYTHON" scripts/check_stand.py --support-seed --seconds 12 --headless
"$SNU_GOM_PYTHON" scripts/train.py --support-reference --speed 0.01 --gait-period 4 --num-envs 512 --iterations 250 --output runs/support_v4_512 --headless
"$SNU_GOM_PYTHON" scripts/play.py --checkpoint runs/support_v4_512/model.pt --scene flat --seconds 12 --video --headless
"$SNU_GOM_PYTHON" scripts/play.py --checkpoint runs/support_v4_512/model.pt --scene home --seconds 12 --video --headless
"$SNU_GOM_PYTHON" scripts/record_grid.py --checkpoint runs/support_v4_512/model.pt --num-envs 16 --seconds 8 --headless
```

This is an experimental joint-target seed, **not a balanced reference gait**.
Its ideal static support audit improves from 6/20 to 18/20 sampled phases, but
the unassisted dynamic replay still falls. Root poses in the reference JSON are
geometry-audit data only; they are never imposed on the simulated robot. Original
actuator limits and self-collision remain enabled. The 0.01 m/s command is for
stepping discovery and cannot satisfy the 0.5 m / 30 s acceptance milestone even
with perfect tracking. These short videos are diagnostics, not acceptance tests.

V3 reference targets: 5 mm swing clearance, 4-second cycle, 0.01 m/s, 40 mm same-foot
stride, 0.20 rad torso-roll geometry. They are exploratory targets, not achieved
walking measurements. The torso-roll geometry is used only to solve joint targets;
the controller does not apply a torso pose or external balancing force.

`compare_scenes.py` runs the **same checkpoint** for 30 seconds in both layouts,
checks its SHA-256 before/after, and saves both metric sets and gate results. There
are no optimizer updates. Three trials are a quick diagnostic; use at least 20
for the straight-walking gate. Even a straight-gate pass does not authorize the
next curriculum without start/stop, actuator, and multiple-training-seed checks.
The deliberately slow seed cannot meet 0.5 m in 30 seconds by tracking its command;
it is a stepping-discovery stage, not a relaxation of that milestone.

Keep flat training first. Optional `--scene home` training clones the primitive
scene at 5 m spacing as a **separate experiment**, not an automatic curriculum.
After reliable walking/stopping, introduce measured friction variation, explicit
rug edges, and very low thresholds one at a time. The existing rug is cosmetic and
flush. Camera-aware obstacle avoidance remains a later task; scene decoration or
navigation rewards cannot substitute for locomotion validation.

#### Reward-only baseline

The current experiment starts from a mild 0.30 rad knee crouch, commands 0.025 m/s,
and uses a 2.4-second gait period with 6 mm target swing clearance. The intended
same-foot stride is 60 mm (approximately 30 mm per alternating step). These are
reward targets, not demonstrated walking measurements. Original joint effort and
speed limits remain unchanged. To reproduce the larger follow-up run:

```bash
"$SNU_GOM_PYTHON" -u scripts/train.py --task walk --num-envs 512 --iterations 250 --speed 0.025 --gait-period 2.4 --output runs/stepping_v2_512 --headless
```

Use a new output directory for each experiment. The original sliding baseline is
preserved at Git revision `d5103c1`; its checkpoints require that revision's policy
source. Do not bypass source-hash checks to replay or resume old policies with new
rewards, action scaling, or initialization.

Evaluation now reports clear touchdowns, consecutive same-foot landing displacement,
unwrapped heading change, and peak joint speed/torque. A clear touchdown requires at
least 60 ms airborne and more than 2 mm sole clearance; contact flicker alone does
not count as stepping. A policy can remain upright and still fail this test.

For progress plots without starting Isaac:
`"$SNU_GOM_PYTHON" scripts/plot_training.py runs/SELECTED_RUN`.
This writes `training_progress.png`; training return alone is not a walking metric.

To make a team-facing GIF/MP4 of many robots, including exploration, falls, and resets:

```bash
"$SNU_GOM_PYTHON" scripts/record_grid.py --checkpoint runs/SELECTED_RUN/model_0.pt --num-envs 16 --seconds 8 --headless
```

This is a parallel rollout from saved weights, **not** footage of optimizer updates.
It samples the saved policy distribution by default; add `--deterministic` to show
mean policy actions. Outputs live under `grid_<checkpoint>_<count>_exploration/`.
Use normal single-robot evaluation, not these auto-reset clips, to judge success.

For a selected checkpoint, replace the path below with its actual run directory:

```bash
"$SNU_GOM_PYTHON" -u scripts/play.py --checkpoint runs/SELECTED_RUN/model.pt --seconds 20 --episodes 20 --headless
"$SNU_GOM_PYTHON" -u scripts/play.py --checkpoint runs/SELECTED_RUN/model.pt --seconds 10 --video --headless
"$SNU_GOM_PYTHON" -u scripts/play.py --checkpoint runs/SELECTED_RUN/model.pt --scene home --seconds 10 --video --headless
"$SNU_GOM_PYTHON" -u scripts/play.py --checkpoint runs/SELECTED_RUN/model.pt --seconds 15 --stop-at 8 --video --headless
"$SNU_GOM_PYTHON" -u scripts/train.py --task walk --num-envs 256 --iterations 250 --checkpoint runs/SELECTED_RUN/model.pt --headless
```

Reviews live beside the checkpoint under `review_<checkpoint>_<scene>_<duration>_<episodes>/`, containing
`evaluation.json`, `summary.json`, and, when requested, `rollout.mp4`,
`rollout.gif`, and `preview.png`. Each fallen trial ends immediately; a reset is
not counted as continued survival. The first evaluation trial uses exact neutral
initialization; subsequent trials add small joint offsets.

Training has no cameras. Run video playback after training exits so both processes
do not compete for the 8 GB GPU. All scripts use headless mode; video output does
not require a visible simulator window. Initial shader compilation can take longer
than later renders. GPU access must be available outside a restricted tool sandbox.

## Model and controller

- Source: `snu_gom_preview_relative.urdf`, floating base, 12 actuated joints.
- The policy controls ten leg joints; neck yaw/pitch have separate bounded drives.
- The importer merges the pelvis into `base_reference`; this is a moving body.
- Original effort limits of 0.15 N·m and velocity limits of 1 rad/s are retained.
  These are unmeasured preview values, not verified motor specifications.
- Initial leg position gains: 4 N·m/rad and 0.08 N·m·s/rad. Neck gains: 1 and 0.04.
- Physics: 500 Hz; policy: 50 Hz; action targets have joint-limit and slew limits.
- Actor observations: 45 values. Critic observations: 63 values, including true
  velocity and contact information used only during training.
- The actor's previous-action field contains the applied, slew-limited normalized
  position offset. Preserve this definition when exporting to another runtime.

`config.json` stores robot/mesh/configuration hashes, source hashes, settings, and
package versions. Resume/playback refuses changed robot or environment sources.
Use a new experiment for changed rewards or controller behavior; old policy
evaluation requires its original source version. Each new run archives the Python
sources in `source/`; keep `config.json` beside checkpoints when sharing them.
Use `--output runs/my_experiment` to give a new run a descriptive, unused directory.
Change `snu_gom_walk/agent.py` for PPO settings and `snu_gom_walk/env.py` for rewards
and controller settings; start a new run after either change. Never alter the
supplied model just to make a training score look better.

## Lightweight home environment

`--scene home` adds nine static box colliders: two walls, a sofa, and a small table.
The central walking lane remains clear. A flush visual rug has no separate
collision/friction behavior: this does **not** claim to model soft carpet. There
are no downloaded household meshes, cameras in the policy, people, deformables,
stairs, or navigation stack. Furniture is collidable, but this state-only actor
cannot see it or plan around it.

Keep early training on the default flat floor, then compare the same checkpoint
on the home scene. Optional `train.py --scene home` clones this primitive scene
with 5 m spacing; it is a separate experiment rather than an automatic difficulty
increase. After flat walking is reliable, add measured friction variation, rug
edges, and very low thresholds as separate curriculum stages. Camera-aware
obstacle avoidance is a later task, not a locomotion reward shortcut.

Reports and checkpoints describe simulation experiments. Standing success and
training completion do not establish walking success or physical-robot readiness.
Inspect the measured distance, foot contacts, and videos before judging a policy.

## Runtime notes

The startup check exposed a hang during ordinary Isaac shutdown in this installed
version. Scripts use Isaac's immediate shutdown option after saving artifacts.
On an uncaught exception they print the traceback and exit with status 1 rather
than letting Isaac's shutdown hide the error. Check for the expected completion
report as well as the process exit code. Do not interpret an absent report as success.

Application logs are directed to `reports/`; converted USD assets go to
`assets/generated/`, keyed by model/mesh/config hashes so changed meshes cannot
silently reuse a stale converted asset; requested Python/CUDA/Warp cache paths go to `.cache/`.
Isaac also uses its installation-managed extension and shader caches; these are
runtime-managed dependencies, not project source edits.
