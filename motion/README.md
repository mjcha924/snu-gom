# SNU Bear motion library · v0.1

**CAD-free GitHub release:** robot meshes are intentionally omitted. CPU tooling works; simulation and training require the [matching external assets](../docs/SIMULATION_ASSETS.md). The URDF, parameters and joint registry are retained as text metadata. The CAD workspace is linked in the [Onshape guide](../docs/ONSHAPE.md).

A feedback-policy library for your **nine-motor SNU Bear V0.6**: two pitch joints per limb and one neck joint. Train the skills in Isaac Lab, export their neural networks, and select them at runtime using joint encoders and an IMU.

**This release contains implementation and training tasks, not pretrained weights.** All five registry entries are `untrained`. Isaac Sim, Isaac Lab, PyTorch and a GPU runtime were unavailable in the build workspace. The simulation import, training convergence and hardware motion have not been tested. See `VALIDATION.md` for the checks actually run.

## Included skills

| Skill | Start → goal | Task ID | Current status |
|---|---|---|---|
| `hold_sit` | Sitting → stable sitting | `SNU-Bear-HoldSit-v0` | Task implemented; untrained |
| `hold_low` | Low stance → stable low stance | `SNU-Bear-HoldLow-v0` | Task implemented; untrained |
| `sit_to_low` | Sitting → low stance | `SNU-Bear-SitToLow-v0` | Task implemented; untrained |
| `low_to_sit` | Low stance → sitting | `SNU-Bear-LowToSit-v0` | Task implemented; untrained |
| `crawl_forward` | Low stance → forward travel | `SNU-Bear-CrawlForward-v0` | Task implemented; untrained |

Turning and recovery are recorded as future feasibility work. No additional motor is assumed. The return transition and gait from the revised low stance still need physical simulation to establish feasibility.

## First commands

Open a terminal in this directory and install the small core package:

```bash
python -m pip install -e .
snu-bear list
snu-bear doctor
python -m unittest discover -s tests -v
```

For training, use an **Isaac Lab v2.3.0 checkout with Isaac Sim 5.1.0, Python 3.11, and its matching RSL-RL dependencies**. This is the API target, not an integration-tested compatibility claim. Follow NVIDIA's [versioned installation instructions](https://isaac-sim.github.io/IsaacLab/v2.3.0/source/setup/installation/pip_installation.html), then install this package into that environment. `pip install -e .` alone does not install Isaac.

```bash
# Inside the activated Isaac Lab Python environment, from this package directory:
python -m pip install -e '.[inference]'
python scripts/smoke_sim.py --skill hold_sit --device cuda:0
python scripts/smoke_sim.py --skill hold_low --device cuda:0

# Replace /absolute/path/to/IsaacLab with your v2.3.0 checkout.
python scripts/isaac.py train --isaac-lab /absolute/path/to/IsaacLab \
  --skill hold_sit --num_envs 256 --max_iterations 3000 --headless \
  --run_name hold_sit
```

The smoke script exercises asset import, reset and stepping with a stationary target. It does not demonstrate a learned skill. Inspect the imported collisions before spending time on training. The iteration count is an initial budget, not a convergence estimate.

Train `hold_low` next, then each transition, then crawling. Use the same command with the corresponding `--skill` and `--run_name`. Tasks train independently; training a hold skill does not automatically initialize another skill's weights. [TRAINING.md](docs/TRAINING.md) covers export, evaluation and tuning.

## What the robot learns

Each policy receives four frames of encoder positions, encoder velocities, IMU angular velocity, estimated gravity direction, previous position targets and a forward-speed command. It outputs nine bounded position-target actions at a proposed 50 Hz. A motor model tracks these targets in physics; on hardware, the servo controller does that job.

Rewards describe the goal: posture, balance, forward speed and moderate effort. They do not prescribe when to lean, plant a paw or lift the belly. **The torso is free to move in simulation.** Its pose is set only when resetting an episode. Belly support is permitted during sit/low transitions. Reference joint positions define endpoint regions, not a timed movement sequence.

The previous 111-state motion study is included in `data/optional_reference.json` as optional analysis data. No training task reads it. It is kinematic evidence, not a learned controller or a dynamically validated trajectory.

## Files to use

| Location | Purpose |
|---|---|
| `src/snu_bear_motion/data/robot/` | Original V0.6 URDF, joint registry and parameters; meshes supplied separately |
| `src/snu_bear_motion/data/contract.json` | Joint order, units, control rates, endpoint poses and exploratory motor assumptions |
| `src/snu_bear_motion/isaaclab_tasks/` | Five Gym tasks, scene, goal rewards, randomization and PPO configuration |
| `scripts/isaac.py` | Launch the official Isaac Lab training or playback script with these tasks |
| `scripts/evaluate.py` | Evaluate a real exported ONNX policy and save episode measurements |
| `policies/registry.json` | Track skill checkpoints; currently all untrained |
| `src/snu_bear_motion/runtime.py` | Observation history, ONNX inference and skill selector |
| `src/snu_bear_motion/hardware.py` | Measured servo-coordinate conversion and transport interface |
| `examples/` | Controller-loop integration and an unfilled hardware calibration template |
| `tests/` | CPU checks of coordinates, model structure, policy IO and runtime faults |

## What needs your hardware measurements

The exact Dynamixel model, motor IDs, zero offsets, directions, allowable travel, measured torque/speed response, communication delay and IMU mounting are still unknown. The included 0.2 Nm torque cap, 1 rad/s speed/target-slew limit, PD gains and 50 Hz policy rate are **simulation assumptions**, not motor specifications. The software therefore includes a transport interface rather than guessing a serial driver or register layout.

The CAD model also has very small clearances: the earlier kinematic study found about 0.107 mm at the neck and 0.349 mm between approaching paws. Convex decomposition may change those gaps. The earlier static support margin also became negative under some ±20% mass combinations. Passing those earlier geometry checks does not establish reliable dynamics or successful training.

After obtaining policies that work in physics, calibrate the real robot and evaluate skill handoffs before deploying them. [DEPLOYMENT.md](docs/DEPLOYMENT.md) defines the exact interface and what remains to implement for your selected motors.
