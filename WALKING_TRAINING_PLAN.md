# SNU-GOM walking policy: implementation and validation plan

Date: 2026-11-16

Status: headless Isaac startup, URDF fidelity, initial standing, PPO training/export, and flat/home video playback work. The 250-update policy survives 20 seconds but slides/pivots with zero clear steps: **walking is not validated**. The lightweight home scene is implemented. Source, URDF/STLs, instructions, and selected review artifacts are included for collaborators, including a 16-robot exploration GIF.

Workspace: `/home/mjcha/snu-gom`

## 1. Objective and first deliverable

Train SNU-GOM to stand, start walking slowly forward on a flat floor, and stop on command in simulation. The intended character is a small, expressive bear companion: short deliberate steps, gentle weight shifts, and a stable posture from which it can look at and interact with people. Use the supplied robot geometry and mass model, with an explicitly documented actuator model. The first deliverable is a reproducible training setup, a trained checkpoint, a playback video, and an evaluation report showing actual locomotion performance.

Start with ten controlled leg joints. Keep both neck joints in the physical model and hold them near their calibrated neutral angles using bounded position control. Their mass and motion still affect balance.

Initial walking target: **0.04 m/s forward**, zero lateral velocity, and zero yaw rate. After that works, train a small forward-speed range of **0.02–0.06 m/s**, including zero-command standing. These are proposed experiment settings, not established robot capabilities.

Turning, rough terrain, recovery from falls, vision, expressive head motion, and physical deployment are later extensions. A successful simulated walk does not establish hardware feasibility while the actuator limits and masses remain estimates.

### Project vision and relationship to the GitHub repository

The project repository was reviewed at commit `00e538cf3001df17e4eaee2d3c93f9b530533484`, including its README, project brief, roadmap, HRI/interface documents, paper-informed design notes, motion specification, and simulation/validation notes.

The [project brief](https://github.com/mjcha924/snu-gom/blob/00e538cf3001df17e4eaee2d3c93f9b530533484/docs/PROJECT_BRIEF.md) describes a bear with short legs and large paws, progressing from standing and short walks to expressive waddles and body tilts. The [motion specification](https://github.com/mjcha924/snu-gom/blob/00e538cf3001df17e4eaee2d3c93f9b530533484/motion/design/character_motion_spec.json) groups behavior into standing/looking, periodic small waddles, and episodic greetings. Those files express design intent; their motions are not validated hardware behaviors.

Apply that vision to this workspace as follows:

- Prioritize repeatable short steps, gentle starts/stops, and stable standing between interactions.
- Allow modest, purposeful side-to-side weight transfer while limiting abrupt torso/head oscillation. Do not maximize walking speed or remove all natural waddle through an excessively rigid upright reward.
- Track foot touchdown velocity/impulse and head angular motion as motion-quality metrics. Simulated impact is a useful proxy, but actual quietness requires acoustic measurements later.
- Preserve the head/camera/electronics mass when training. After basic walking, test small commanded neck motions while standing before combining them with walking.
- Keep a compact local policy with a versioned interface suitable for later onboard timing tests. Conversation and perception should request bounded behaviors; local control owns balance and joint commands. This follows the repository's [HRI design](https://github.com/mjcha924/snu-gom/blob/00e538cf3001df17e4eaee2d3c93f9b530533484/docs/HRI.md).

The user confirmed that the concept carries over even though the geometry differs. Therefore **the local URDF is authoritative for this training model**, while GitHub supplies the product vision and project-level evaluation goals.

| Aspect | GitHub design snapshot | Current local training asset |
|---|---|---|
| Leg layout | Hip roll/pitch, knee pitch, ankle pitch/roll | Hip yaw/roll/pitch, knee pitch, ankle pitch |
| Neck | One pitch joint | Yaw and pitch joints |
| Motor model allocation | Eleven XL330 motors in the described design | Eight XL330 and four XC330 assignments |
| Mass baseline | Earlier primitive proxy is 0.600 kg; later CAD has a separate estimate | Current itemized URDF is approximately 1.193 kg |
| Prior motion interface | Earlier joint order and model revisions | New explicit mapping for this URDF |

The GitHub [README](https://github.com/mjcha924/snu-gom/blob/00e538cf3001df17e4eaee2d3c93f9b530533484/README.md), [interface draft](https://github.com/mjcha924/snu-gom/blob/00e538cf3001df17e4eaee2d3c93f9b530533484/docs/INTERFACES.md), and [validation notes](https://github.com/mjcha924/snu-gom/blob/00e538cf3001df17e4eaee2d3c93f9b530533484/docs/GOM_VALIDATION.md) document those older assumptions. Do not import their ankle-roll commands, fixed-base proxy, mass values, collision exclusions, or old checkpoints into the new training setup without an explicit model conversion.

## 2. What has already been inspected

### Robot files

The starting asset is `snu_gom_description/urdf/snu_gom_preview_relative.urdf`. The ROS package-path variant is `snu_gom_preview.urdf`. The original CAD export is retained under `source/`.

Read during preparation:

- `snu_gom_description/README.txt`
- `snu_gom_description/docs/START_HERE.txt`
- `snu_gom_description/docs/MASS_BUDGET.txt`
- `snu_gom_description/docs/MASS_ASSUMPTIONS.txt`
- `snu_gom_description/docs/VALIDATION.txt`
- `snu_gom_description/docs/COLLISION_CHECK.txt`
- `snu_gom_description/config/joint_parameters.csv`
- `snu_gom_description/config/additional_masses.csv`
- The relative-path URDF and relevant portions of `tools/rebuild.py`.

| Property | Finding | Consequence for training |
|---|---|---|
| Physical structure | 13 physical bodies plus `base_reference` | Preserve physical inertias; keep the root free to move |
| Actuated joints | 12: five per leg, two in the neck | Ten-dimensional walking action; separate neck controller |
| Leg topology | Hip yaw → hip roll → hip pitch → knee pitch → ankle pitch | There is no ankle-roll joint; balance must use the available joints |
| Total URDF mass | 1.19250734231 kg, independently summed from XML | Match the imported simulator mass to this value |
| Visuals/collisions | 79 visual instances; 29 collision boxes | Use supplied simplified collision geometry initially |
| Mesh references | All referenced visual meshes exist | No missing asset paths found |
| Root convention | Approximately +X forward, +Y left, +Z up | Confirm physically in the viewer before defining commands |
| Neutral sole bounds | Right minimum z ≈ −0.160559 m; left ≈ −0.160953 m | Start near 0.164 m pelvis height, then compute height from the chosen pose |
| Motors in supplied configuration | XC330-M288-T at both hip-pitch and knee-pitch joints; XL330-M288-T elsewhere | Use separate actuator groups; do not assign one borrowed motor model to every joint |
| Current effort/speed | Every joint has 0.15 N·m and 1 rad/s | These are explicitly provisional preview values |
| Current angular limits | Hip yaw ±30°, roll ±20°, pitch ±45°, knee ±60°, ankle ±25° | Treat as provisional bounds and inspect swept clearances |

The supplied validation reports positive-definite inertias and no nonadjacent box overlap at the exported neutral pose. Those checks have not yet been reproduced in a simulator, and do not establish clearance throughout a gait.

**Important kinematic finding:** forward kinematics of the supplied URDF gives approximately −Y for the right knee's positive rotation axis and +Y for the left knee's. The ankle axes are approximately +Y on both sides. A shared knee angle sign would therefore produce different physical motions. Joint names alone are insufficient for mirroring poses or reference trajectories.

### Local software and hardware

Read-only inspection found:

- NVIDIA RTX 3070 with 8 GB VRAM; accessible when checked outside the tool sandbox.
- Approximately 32 GB system RAM, with about 26 GiB available during inspection.
- Isaac Lab source under `/home/mjcha/IsaacLab`.
- Existing Python interpreter: `/home/mjcha/miniconda3/envs/env_isaaclab/bin/python`.
- Installed metadata: Isaac Sim `5.1.0.0`, Isaac Lab `0.54.3`, RSL-RL `5.0.1`, MuJoCo `3.6.0`, Stable-Baselines3 `2.7.1`.
- `warp` is present in that interpreter; `mjlab`, `mujoco_warp`, and `onnxruntime` are not. A compatible mjlab stack will need a separate workspace-local installation.

Installed packages and a working GPU query do not prove that a full Isaac Sim application or training run works. Check that in Phase 1. The initial sandbox GPU-query failure was not evidence of a broken host driver.

## 3. Lessons to adapt from Open Duck and MicroDuck

These references inform the design; their checkpoints, joint coordinates, and dynamics are specific to their robots.

| Reference inspected | Useful pattern | Adaptation for SNU-GOM |
|---|---|---|
| [MicroDuck RL README](https://github.com/pollen-robotics/microduck_rl/blob/develop/README.md) | MuJoCo Warp/mjlab with PPO, 50 Hz policies, deployment through exported ONNX | Use PPO and an explicit observation/action interface; export normalization with the policy |
| [MicroDuck velocity environment](https://github.com/pollen-robotics/microduck_rl/blob/develop/src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py) | Velocity tracking, upright posture, foot clearance/contact terms, gradual action smoothing, explicit standing commands | Begin with a small speed range and inspect individual reward terms rather than copying weights |
| [Open Duck sim-to-real notes](https://github.com/apirrone/Open_Duck_Mini/blob/v2/docs/sim2real.md) | Model mass and servo behavior carefully; use generated motion for imitation | Validate our inertias/actuators; generate reference poses from our own robot if basic RL stalls |
| [Open Duck joystick environment](https://github.com/apirrone/Open_Duck_Playground/blob/main/playground/open_duck_mini_v2/joystick.py) | Position targets around a home pose, command-rate limiting, action/IMU delay, optional imitation | Bound and smooth targets; preserve the same controller semantics in training and playback |
| [Open Duck reference generator](https://github.com/apirrone/Open_Duck_reference_motion_generator) | Placo-based generation of walking references | Adapt the method to SNU-GOM's kinematics; validate references before using them for learning |
| [BAM actuator project](https://github.com/Rhoban/bam) | Identification and simulation of more detailed servo friction models, including XL330 | Investigate a matching XL330 model later; XC330 needs its own evidence or identification |

MicroDuck's training README describes five joints per leg and four neck/head joints. SNU-GOM has five per leg but only two neck joints, and a different mass distribution. This makes the locomotion problem relevant, while requiring a new policy interface and retraining. [Source](https://github.com/pollen-robotics/microduck_rl/blob/develop/README.md)

Open Duck's documented actuator example uses Feetech STS3215 parameters. Those numeric parameters are not suitable defaults for SNU-GOM's XL330/XC330 motors. [Source](https://github.com/apirrone/Open_Duck_Mini/blob/v2/docs/sim2real.md)

Record upstream commit IDs when material is actually adopted. The links above were inspected on the plan date and point to moving branches. Preserve required attribution and license terms if copying source; reference ideas alone do not require importing whole repositories.

## 4. Simulator choice and workspace rules

**Selected primary stack: installed Isaac Sim 5.1 + Isaac Lab + RSL-RL PPO, headless.** The user selected this path on 2026-11-16. First validate startup, a single floating-base robot, and bounded-control standing; then increase parallel environments based on measured memory. Use the existing Isaac Python interpreter without changing its packages.

**Memory constraint:** NVIDIA's published Isaac Sim 5.1 minimum lists an RTX 4080 and 16 GB VRAM, above this machine's RTX 3070/8 GB. Validate the requested reduced headless configuration experimentally. [Isaac Sim 5.1 requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)

**Checkpoint reviews:** save checkpoints during training, then render short deterministic single-robot MP4/GIF rollouts in a separate headless Isaac process. Training runs without cameras; video rendering runs after the training process releases GPU memory. Save the initial stance, early policy, intermediate policy, and best evaluated policy with numerical metrics and links. Label failed or untrained rollouts honestly. Use CPU MuJoCo later only as an explicitly labeled cross-engine check or visualization fallback.

**Fallback:** if Isaac cannot run reliably after diagnosing startup/import/memory failures, record the failure before proposing MuJoCo Warp/mjlab. Do not silently change the selected simulator. [mjlab project](https://github.com/mujocolab/mjlab)

### Lightweight home curriculum

1. Keep initial PPO training on a flat primitive floor with no cameras. Household meshes, photorealistic assets, people, and soft-body simulation are unnecessary for learning balance.
2. Use `play.py --scene home` for the first home checkpoints: two walls, a box sofa, and a four-legged box table (nine static colliders total), with a clear central lane. These objects are collidable, not part of the observation. A flush visual rug is cosmetic only, not a carpet contact model.
3. Compare the same checkpoint on flat/home scenes using identical commands and initial states. Report furniture contacts or falls. This is indoor locomotion evaluation, **not** visual navigation or collision avoidance.
4. Only after reliable flat walking, add friction variants representative of hard flooring and carpet, then measured low rug lips/thresholds (start a few millimeters high). Add one difficulty at a time, retain flat trials, and measure the throughput cost. These terrain/randomization stages are not implemented in the initial home scene.
5. `train.py --scene home` is available for an explicit primitive-room experiment; clone rooms with 5 m spacing. Prefer flat training until room interactions provide a concrete training benefit.
6. Later navigation should command the locomotion controller and manage obstacle clearance separately; do not pretend the present 45-value proprioceptive policy sees furniture.

### Is the RTX 3070 good enough?

**Assessment: sufficient to begin this small state-based locomotion project; benchmark before promising throughput or convergence time.** The ten-action neural policy is small. Physics contacts, parallel simulation state, rollout storage, and rendering are the more important memory consumers. Camera-based learning is unnecessary for the first walking policy.

Resource plan:

1. Validate one robot in headless Isaac, then start the GPU training check at 32–64 environments.
2. Benchmark 64, 128, and 256 environments with identical geometry and settings; increase to 512 only if memory and throughput support it. These are trial sizes, not verified capacities.
3. Measure peak total GPU memory through compilation/warm-up, rollout collection, and optimizer updates. PyTorch's own allocation report misses memory allocated by the simulator.
4. Aim to keep roughly 1–1.5 GB free for the desktop and transient allocations; reduce environments/contact buffers if required.
5. Train headlessly with primitive collisions and no camera observations; render one robot for evaluation videos separately.
6. Record transitions per second and wall time per update. Estimate a full run only after this benchmark; no training duration is established yet.

No GPU purchase is needed to start. If a validated environment later proves too slow, fewer environments and longer runs remain options before changing hardware. The main unresolved feasibility questions today are robot contact/actuator behavior, not neural-network size.

Workspace rules:

1. Put new source, configuration, converted assets, reference checkouts, logs, checkpoints, videos, and reports inside `/home/mjcha/snu-gom`.
2. Read the existing simulator installation as a dependency; do not patch `/home/mjcha/IsaacLab` or change the shared Conda environment.
3. If additional packages are required, create an isolated environment under `.venv/` and configure package caches inside `.cache/`. Capture the dependency versions.
4. Configure simulator caches and logs inside the workspace where supported; record any unavoidable simulator-managed external files before using that runtime.
5. Preserve the supplied URDF and CSV files as the initial baseline. Generate simulator assets under `assets/generated/`; represent experimental changes in explicit configuration overrides.
6. If source-model corrections become necessary, update the authoritative CSV/rebuild workflow and retain the baseline hashes. Avoid hand-editing only a generated URDF.

Implemented layout (alongside the preserved upstream project):

```text
snu-gom/
├── WALKING_TRAINING_PLAN.md
├── HEADLESS_TRAINING.md          installation and team command guide
├── requirements-walking.txt     tested supporting dependencies
├── snu_gom_description/          supplied URDF, STL, source tables, assumptions
├── snu_gom_walk/
│   ├── model.py                 CPU model audit and joint mapping
│   ├── env.py                   Isaac scene, controller, observations, rewards
│   ├── home.py                  static primitive home scene
│   └── agent.py                 PPO configuration
├── scripts/
│   ├── check_setup.py
│   ├── check_model.py
│   ├── check_stand.py
│   ├── train.py
│   ├── play.py                  evaluation and optional MP4/GIF rendering
│   └── runtime.py
├── tests/walking/               CPU model contracts
├── docs/experiments/            selected shareable results/media
├── assets/generated/
├── runs/                        per-run configs, checkpoints, metrics, videos
└── reports/                     model audit, validation, evaluation
```

Generated assets, runs, and reports are local outputs. Preserve the versioned model
and source contracts when exchanging policies between collaborators.

## 5. Phase 1 — establish a reproducible baseline

**Goal:** know exactly which model and software each experiment uses.

Steps:

1. Run from the workspace root. Record file hashes for the URDF, mass/limit CSVs, and mesh assets.
2. Implement `scripts/check_setup.py` to report Python/package versions, GPU access, CUDA availability, and simulator startup status.
3. Start the existing Isaac interpreter with workspace-local log/cache paths and a simple headless scene. Check GPU access and memory; no shared dependency upgrades.
4. Record dependency/source revisions and RSL-RL API compatibility against the installed Isaac examples.
5. Create a run-directory convention and local logging; external experiment tracking is unnecessary for this first task.
6. Select the primary backend based on these results and update this plan with that decision. Measure memory/throughput at small parallel-environment counts before committing to a long run.

Outputs: `reports/setup.json`, `reports/model_manifest.json`, pinned environment details.

Pass condition: simulator starts and steps reliably on the available device, outputs stay in the configured workspace locations, and no dependency changes to unrelated projects are needed.

## 6. Phase 2 — validate kinematics and import the robot

**Goal:** establish that the simulated mechanism matches the supplied URDF.

Steps:

1. Implement an audit of link/joint counts, mesh paths, mass totals, inertia validity, and joint bounds.
2. Import with a floating root. `base_reference_joint` is an internal fixed connection, not a world attachment. Verify that fixed-link merging preserves mass/inertia and resolves a usable pelvis body name.
3. Preserve the 29 supplied collision boxes initially. Show both visuals and collision geometry in the viewer.
4. Match total simulator mass to the URDF within 0.1%; compare body CoMs and inertia transforms, not only the total mass.
5. On a temporarily supported robot, move each joint by a small positive angle, such as 0.05 rad, and record its physical direction. This support is a diagnostic fixture and must be removed for standing/walking tests.
6. Produce an explicit policy joint order. Never use whatever ordering the importer happens to return.
7. Verify left/right feet, knee-bending directions, torso forward axis, and IMU orientation. Do not force both knees to share a sign or assume exact bilateral symmetry.
8. Sweep conservative candidate poses, inspect nonadjacent collisions, and check foot contact planes. Apply only justified parent/child collision filtering; retain meaningful leg/torso/head contacts.
9. Compute initial pelvis height from the lowest collision point at the chosen neutral pose plus a small clearance, instead of hard-coding a height from another robot.
10. For MuJoCo, generate an MJCF with a free joint, explicit inertias, actuators, and floor from the URDF; preserve mesh transforms and collision origins. Verify conversion rather than assuming a bare URDF import already provides a complete locomotion scene. USD is needed only for an Isaac experiment.

Outputs: `reports/model_audit.json`, joint-direction table, converted asset, neutral-pose screenshots.

Pass condition: free root, correct scale and mass, expected joint motion, valid foot geometry, no unexplained neutral-pose penetration or unstable import behavior.

## 7. Phase 3 — calibrate position control and find a stable stance

**Goal:** confirm that contact and motor behavior are plausible before spending time on PPO.

Steps:

1. Start with a 0.002 s physics timestep and a 0.02 s policy/controller update interval: 500 Hz physics, 50 Hz decisions. These are proposed simulation settings to validate for this model, not a selected hardware bus rate. The project's motion specification leaves hardware rates open pending measured latency.
2. Use finite-torque position control. Start from the supplied 0.15 N·m and 1 rad/s assumptions and log saturation explicitly.
3. Tune stiffness/damping using small joint steps, with realistic effort bounds. Separate XL330 and XC330 groups, and include neck holding torque.
4. Determine whether exported zero is a useful stance. If necessary, use forward/inverse kinematics to create a mild crouch with flat soles and the projected CoM between the feet.
5. Estimate static joint loads in double support and near single support using a contact-constrained equilibrium calculation. Avoid treating floating-base inverse dynamics without contact forces as a valid support-load estimate.
6. Hold the unsupported floating-base robot at its stance for ten seconds. Log pelvis height, orientation, joint errors, foot forces, sliding, and motor saturation.
7. If the robot cannot stand, diagnose contact geometry, pose, CoM, gains, and torque requirements before training. Persistent saturation is evidence to revisit the actuator assumptions or mechanics.
8. Author a small bear-style weight-shift/step sketch in this robot's kinematics and keep a bounded nonlearned controller as a comparison baseline. Record if the sketch is only kinematic or cannot walk dynamically. This gives the later learned waddle a concrete style target without treating animation as a successful controller.

Any changed effort/speed values must be labeled as either measured/calibrated or an explicit simulation hypothesis. A larger torque value that makes learning easier is not evidence of physical motor capability. Continuous usable torque must not be inferred directly from a stall-torque specification.

Outputs: stance configuration, controller settings, torque/contact plots, a ten-second standing video.

Pass condition: ten-second stance without falling or numerical instability, physically sensible contacts, and acceptable tracking without persistent actuator saturation. If this fails under the chosen motor assumptions, report that finding and resolve it before longer training.

## 8. Phase 4 — implement the walking environment

### Action interface

Use ten bounded position offsets around the validated stance, ordered explicitly as:

```text
left_hip_yaw_joint
left_hip_roll_joint
left_hip_pitch_joint
left_knee_pitch_joint
left_ankle_pitch_joint
right_hip_yaw_joint
right_hip_roll_joint
right_hip_pitch_joint
right_knee_pitch_joint
right_ankle_pitch_joint
```

Map normalized actions to per-joint angle scales. Start with modest exploration, about 0.1–0.25 rad where the validated range permits it, and tune by joint. Bound targets within joint limits and apply a target slew limit consistent with the selected motor model. A target slew limit alone does not enforce actual physical joint-speed limits; monitor/enforce those in the actuator/simulator as well.

Reset previous targets, action history, contact history, delay buffers, and gait state consistently at each episode reset. Keep all physical joints, including the neck, under a defined controller.

### Observation interface

Proposed initial actor observation, with fixed ordering and saved normalization:

| Signal | Dimensions | Meaning |
|---|---:|---|
| Body angular velocity | 3 | IMU-like gyro expressed in the body frame |
| Projected gravity | 3 | Orientation estimate expressed in the same frame |
| Command | 3 | Forward/lateral velocity and yaw rate; unused components initially zero |
| Joint position offsets | 12 | All leg and neck angles relative to the calibrated stance |
| Joint velocities | 12 | Same explicit joint ordering as positions |
| Previous leg action | 10 | Previous bounded policy action |
| Gait phase | 2 | Sine/cosine clock; fixed neutral encoding at zero command |
| **Total** | **45** | Version this interface and verify it at runtime/export |

The critic may additionally observe true base velocity, pelvis height, foot contacts, applied torque, and randomized physical parameters. True base linear velocity and force contacts should remain training-only unless the robot has a validated estimator/sensor for them. The supplied BNO085 mass entry does not itself create a simulated IMU.

History stacking is a later option if the single-frame actor cannot handle delay or hidden dynamics; changing it requires a new observation version.

### Rewards and episode termination

Start with a small set of individually logged terms:

| Term | Purpose | Implementation caution |
|---|---|---|
| Forward/lateral velocity tracking | Follow the command | Use body/yaw-frame velocity consistently; choose tolerance appropriate for 0.04 m/s |
| Yaw-rate tracking | Walk straight initially | Avoid uncontrolled spinning to exploit translational rewards |
| Upright torso and plausible pelvis height | Maintain useful posture | Allow small natural lean and vertical motion |
| Alternating support and swing clearance | Encourage stepping | Gate on nonzero commands; measure clearance at the sole, not the foot-link origin |
| Stance-foot slip | Discourage skating | Apply when loaded/in contact; do not punish swing motion |
| Touchdown and head-motion costs | Encourage gentle steps and a steady gaze | Use weak initial penalties; leave room for necessary weight shifts and do not infer acoustic quietness |
| Action changes and joint effort | Reduce jerk and waste | Start weak; inspect magnitudes before increasing weights |
| Joint-limit proximity and undesired contacts | Avoid destructive or implausible poses | Match the validated geometry and joint limits |
| Zero-command settling | Stop and stand | Disable walking-phase incentives while standing |

Initial gait hypothesis: a 1.6–2.4 s full left/right cycle, double-support intervals, and 5–10 mm swing-sole clearance. Check kinematic reachability and the provisional speed limit before adopting it. Parameter choices may change after stance/controller experiments.

Terminate on a fall, sustained invalid body contact, nonfinite state, or elapsed episode time. Determine the low-height threshold from stance geometry; start with a conservative tilt threshold around 45° and validate it against legitimate stepping. Treat timeouts separately from failure terminations for value-function bootstrapping.

Validate reward behavior using diagnostic rollouts: standing under a walking command, feet sliding, hopping, body-on-floor motion, and genuine steps. A high score for standing or falling must be corrected before a long run.

Outputs: environment/configuration modules, reset/action/observation checks, random/zero-action rollout report.

Pass condition: correct shapes and joint mapping; finite observations/rewards; independent parallel environments; reliable resets; intended reward ranking in diagnostic cases.

## 9. Phase 5 — train in short, inspectable stages

### Initial PPO configuration

These are experiment starting values, not settings copied verbatim from another robot:

| Setting | Initial choice |
|---|---|
| Algorithm | PPO through the selected backend's supported RSL-RL interface |
| Actor/critic | Separate MLPs, hidden sizes `[128, 128, 64]` |
| Rollout length | 32 control steps per environment |
| Learning rate | 3e-4 initially |
| Discount / GAE lambda | 0.99 / 0.95 |
| PPO clipping | 0.2 |
| Update epochs / minibatches | 4 / 4, subject to batch-size validation |
| Exploration | Modest initial action standard deviation, e.g. 0.3 normalized units |
| Episode duration | 10 s during early training; 20 s for evaluation |
| Logging | Reward components, survival, velocity error, contacts, saturation, throughput, VRAM |

### Training sequence

1. **Training plumbing check:** 32–64 environments, 10–20 updates. Verify a saved checkpoint reloads and reproduces deterministic actions; confirm loss/reward values remain finite.
2. **Standing behavior:** zero commands and small reset perturbations. If a learned standing stage is used, retain the same action/observation interface and normalization rules needed for walking. Avoid a normalizer that collapses unused command variance; do not blindly warm-start incompatible statistics.
3. **First walk:** fixed 0.04 m/s forward command with a small fraction of zero-command episodes. Start at 128–256 environments and review every 100–250 updates.
4. **Start/stop and speed variation:** introduce 0.02–0.06 m/s commands, transitions to zero, and roughly 20% standing samples. Keep lateral and yaw commands zero.
5. **Repeatability:** evaluate multiple training seeds once the first run succeeds. Preserve unsuccessful runs and their diagnostics as evidence for tuning.

### Beyond the first 0.5 m milestone

The 0.5 m target is an acceptance test, not a fixed-distance policy or the final robot
capability. The eventual controller should walk continuously until commanded to stop.
The actor already has `(forward speed, lateral speed, yaw rate)` command inputs, but
unused commands are not trained skills. After reliable forward/start-stop behavior:

1. Expand commands to small left/right yaw rates and forward speeds in the **same**
   locomotion policy; evaluate curved walking before sharp turns or turning in place.
   Keep lateral stepping out of the curriculum until the five-joint legs demonstrate it.
2. Add a separately commanded neck yaw/pitch controller with joint/velocity bounds.
   Begin with slow head sweeps while standing, then randomize bounded head poses and
   trajectories during locomotion training so balance accommodates their inertial effect.
3. Keep head targets separate from body-turn commands: looking left need not turn the
   feet. A later behavior layer may coordinate gaze and body heading intentionally.
4. Validate combined turning/head motion, then progress to the basic home curriculum.
   Navigation chooses velocity/heading commands; the low-level policy stabilizes the robot.

This avoids diagnosing import, stepping, steering, gaze, and navigation failures all
at once without requiring unrelated policies or a new control architecture for each skill.

Profile before increasing to 512 environments on the 8 GB GPU. Use headless runs with simplified visuals and render videos separately. Do not copy MicroDuck's large parallel-environment count or advertised wall time onto this different setup.

Use updates as checkpoints for inspection rather than a promise of convergence. At 256 environments and 32 rollout steps, 1,000 updates produce 8,192,000 transitions. Measure actual throughput before estimating runtime or expanding the compute budget.

Save full configs, model hashes, random seed, normalization state, optimizer state, simulator versions, and evaluation metrics with every retained checkpoint. Select the best checkpoint by a held-out evaluation score, not just training reward or latest iteration number.

## 10. Phase 6 — add a reference gait if needed

Trigger: the model can stand and the training pipeline works, but two documented tuning rounds still produce skating, hopping, persistent asymmetry, or no forward progress. Also use this phase if a functional walk succeeds but does not match the short, deliberate waddle defined in the character brief. The small style sketch is authored in Phase 3; this phase turns it into a validated learning reference.

Steps:

1. Use SNU-GOM forward/inverse kinematics, or adapt the Placo-based reference-generation approach linked in Section 3.
2. Create short alternating foot trajectories with double support and lateral weight shift. Solve for the actual five-joint leg chains, prioritizing achievable constraints; do not demand arbitrary six-dimensional foot poses from five joints.
3. Use explicit left/right joint signs and nominal offsets. Recompute trajectories for SNU-GOM instead of replaying Open Duck/MicroDuck joint angles.
4. Check joint positions, velocities, accelerations, swept collisions, and estimated torque/contact feasibility across the cycle.
5. Replay the reference under bounded control. A kinematically valid animation alone does not show dynamic balance.
6. Add a moderate reference-tracking reward, or evaluate a residual-action policy around the reference. Keep velocity, contact, and balance objectives active.
7. Compare reference-assisted and unassisted policies with the same evaluation suite. Record any action/observation contract change as a new experiment version.

Outputs: SNU-GOM reference-motion file with metadata, feasibility report, replay video, comparison results.

Pass condition: measurable improvement in walking success and foot alternation without dependence on unsupported torque, invalid contact, or externally held balance.

## 11. Phase 7 — evaluate walking with explicit success criteria

Separate training metrics from evaluation. Use deterministic policy actions, fixed evaluation seeds and commands, and no training updates. Do not auto-reset a fallen robot and count the rest of the rollout as one successful walk.

### Project-aligned milestone

Retain the repository's proposed standing and forward-walking goals: unsupported standing for 30 seconds in at least 8/10 trials, and 0.5 m forward travel within 30 seconds in at least 7/10 trials. Track the additional two expressive behaviors as a later project milestone. These are project targets, not achieved results. [Project brief](https://github.com/mjcha924/snu-gom/blob/00e538cf3001df17e4eaee2d3c93f9b530533484/docs/PROJECT_BRIEF.md)

For this simulation task, add repeatable start/stop behavior and explicit evidence of alternating steps. Label simulation results separately from hardware results. Compare the nonlearned baseline and learned policy under matched conditions, including failed trials. Report torso-angle RMS and effort; current and temperature require calibrated electrical/thermal models or hardware measurements.

### Additional engineering targets

The following are proposed diagnostic/stretch targets, to be finalized after model/controller validation. They supplement the project criteria and do not silently replace them:

| Test | Proposed acceptance target |
|---|---|
| Standing | At least 19/20 trials remain standing for 10 s; horizontal drift below 3 cm |
| Straight walking | At least 18/20 trials complete 20 s without falling at 0.04 m/s |
| Actual progress | At least 0.6 m forward displacement per successful 20 s walking trial |
| Velocity tracking | Mean absolute forward-speed error ≤0.015 m/s after a 2 s startup period |
| Straightness | Lateral displacement <0.10 m and final yaw error <15° |
| Stepping | Repeated alternating foot unload/lift/landing events on both feet, with measurable clearance; inspect contact plots and video |
| Start/stop | For a stand → walk → stand command sequence, settle within 2 s of the stop command and remain upright for 5 s |
| Valid dynamics | No nonfinite state, persistent joint-limit violation, floor-supported torso/head, or sustained actuator saturation |

Report foot-slip speed, stance duty factors, clearance distribution, orientation distribution, peak/RMS effort, and saturation fractions even when they are not yet pass/fail criteria. Include failed trials in success-rate denominators.

Save front/side videos and an evaluation CSV/JSON. Export the selected policy with normalization and compare exported versus training-runtime actions on recorded observations before replaying the exported model.

Outputs: `reports/walking_evaluation.md`, numerical evaluation data, selected checkpoint, playback video, exported policy plus interface manifest.

Definition of the first milestone: a reproducible simulation policy that meets the project-aligned standing/walking criteria and the agreed stopping criterion, with the additional engineering metrics reported. Include a short visual review of step length, weight shift, head steadiness, and touchdown quality against the bear-character brief. A running training process or a rising reward curve does not complete this milestone.

## 12. Phase 8 — robustness and later transfer work

After nominal walking passes, add uncertainty gradually and compare against the same held-out tests:

1. Small reset-pose perturbations and observation noise.
2. Foot friction variation, initially around the chosen nominal value rather than a very broad range.
3. Mass/inertia and CoM variation based on the supplied uncertainty budget. Scale inertias consistently and sample around the nominal model on every reset, without cumulative drift.
4. Small encoder/IMU biases and measured command/observation delay.
5. Motor strength, friction, gain, voltage behavior, and backlash variation justified by actuator evidence.
6. Small disturbances appropriate to this robot's size and walking speed.

The existing mass budget spans roughly 0.954–1.543 kg. A first ±5% mass experiment only probes local robustness; it does not cover that entire uncertainty range. Test the low/nominal/high design cases explicitly before claiming broad tolerance.

For cross-simulator replay, match inertias, collision geometry, friction, actuator semantics, timing, joint order, and normalization before interpreting a failure as policy fragility. BAM integration in Isaac requires a deliberate compatible implementation; a MuJoCo BAM configuration cannot simply be pasted into an Isaac actuator.

Physical-robot transfer is a separate future stage requiring measured limits, joint directions/zero offsets, usable servo performance, sensor conventions, and a runtime that preserves the saved interface. No hardware control is part of this plan's first implementation milestone.

## 13. Implemented command workflow

These scripts are implemented. Run from the repository root using an Isaac-enabled Python interpreter. Team installation and version pins are in `HEADLESS_TRAINING.md`; checkpoints must be selected from actual run directories.

```bash
cd /home/mjcha/snu-gom
export SNU_GOM_PYTHON=/home/mjcha/miniconda3/envs/env_isaaclab/bin/python

"$SNU_GOM_PYTHON" scripts/check_setup.py --headless
"$SNU_GOM_PYTHON" scripts/check_model.py --headless
"$SNU_GOM_PYTHON" scripts/check_stand.py --seconds 10 --video --headless

"$SNU_GOM_PYTHON" scripts/train.py --task stand --num-envs 64 --iterations 20 --headless
"$SNU_GOM_PYTHON" scripts/train.py --task walk --num-envs 256 --iterations 250 --headless

"$SNU_GOM_PYTHON" scripts/play.py --checkpoint runs/SELECTED_RUN/model.pt --episodes 20 --seconds 20 --headless
"$SNU_GOM_PYTHON" scripts/play.py --checkpoint runs/SELECTED_RUN/model.pt --headless --video
"$SNU_GOM_PYTHON" scripts/play.py --checkpoint runs/SELECTED_RUN/model.pt --scene home --seconds 10 --headless --video
"$SNU_GOM_PYTHON" scripts/play.py --checkpoint runs/SELECTED_RUN/model.pt --seconds 15 --stop-at 8 --headless --video
"$SNU_GOM_PYTHON" scripts/train.py --task walk --checkpoint runs/SELECTED_RUN/model.pt --iterations 250 --headless
```

Training automatically exports `policy_jit.pt` and verifies action equivalence. Playback/evaluation/resume loads saved settings and normalization and refuses changed package source/model hashes. New runs retain source snapshots. The review reports count lifted-foot touchdowns separately from displacement, so sliding is not accepted as walking.

## 14. Failure diagnosis and next actions

| Symptom | First checks | Next action |
|---|---|---|
| Robot falls immediately | Floating-base placement, initial penetration, stance, signs, controller limits | Repair import/controller setup before PPO |
| Stands but never walks | Command scaling, tracking tolerance, excessive posture/smoothness rewards, support transfer | Inspect reward components and reduce conflicting incentives |
| Slides or hops forward | Foot contacts, clearance, slip and alternation metrics | Refine gait objectives or add validated references |
| Knees move inconsistently | Joint order and left/right axis signs | Verify the mapping using individual joint motions |
| Excessive torque saturation | Mass/CoM, stance lever arms, actuator model | Reassess feasibility; record any experimental motor changes |
| NaNs or contact explosions | Timestep, contact offsets, collision filtering, gains | Reproduce in one environment and correct physics |
| GPU out of memory | Environment count, meshes, camera rendering, contact buffers | Reduce count and render separately |
| Good training reward, poor evaluation | Reward exploitation, reset counting, command mismatch | Use measured progress and full-trial success rates |
| Exported policy differs | Normalization, observation order, action clipping, controller history | Compare actions on identical saved observations |

## 15. Execution checklist

- [x] Inspect the supplied description and its documented assumptions.
- [x] Confirm mesh availability, total mass, neutral foot bounds, and knee-axis sign difference.
- [x] Inspect installed simulator/RL packages and host GPU availability.
- [x] Read primary Open Duck/MicroDuck sources and write this plan.
- [x] Read the SNU-GOM GitHub vision, motion/HRI specifications, roadmap, and proposed acceptance criteria; reconcile them with the newer local URDF.
- [x] Assess the RTX 3070/8 GB; user selected headless Isaac first with checkpoint videos.
- [x] Phase 1: headless Isaac startup and GPU access verified.
- [x] Phase 2: validate imported kinematics, mass, and inertia against the URDF (not hardware identification).
- [x] Phase 3: initial 10-second bounded-control standing check; broader repeatability remains pending.
- [x] Phase 4: implement the flat walking task and verify PPO integration; reward quality remains experimental.
- [x] Phase 5: 20-update smoke run, export action equivalence, and deterministic failed-checkpoint playback.
- [x] Phase 5 follow-up: 256 environments, 250 updates; deterministic flat/home checkpoint review identifies sliding, not walking. Multi-trial walking acceptance remains unpassed.
- [x] Render and compare the lightweight home scene.
- [x] Package source, all supplied URDF/STL assets, setup directions, measured results, and team-facing videos/GIF for the shared GitHub repository.
- [ ] Phase 6, if needed: generate SNU-GOM reference motion.
- [ ] Phase 7: demonstrate evaluated standing, walking, and stopping; export artifacts.
- [ ] Phase 8: add uncertainty and optional cross-simulator validation.

## 16. Execution evidence (2026-11-16)

| Check | Measured result | Interpretation |
|---|---|---|
| Isaac startup | 100 physics steps; approximately 2.56 GB total GPU use | Reduced headless configuration runs on this RTX 3070 |
| Import fidelity | 21 poses; max position error 1.06e-7 m, rotation error 7.37e-6 rad; max inertia-relative error 3.14e-7 | Importer preserved URDF kinematics/inertia despite axis-reorientation warnings |
| Initial stance | 10 s, 3.33 mm horizontal drift, imported mass 1.19250727 kg | Initial bounded-control stance passed, not a walking policy |
| 64-env PPO smoke | 20 updates, 40,960 transitions, 32.80 s, approximately 1,249 transitions/s; 2,846 MiB GPU use at end | Learning, checkpoint save, and TorchScript export work |
| Smoke evaluation | Fall after 1.10 s; forward displacement 0.097 m | Failed policy; forward falling is not walking |
| 256-env PPO | 250 updates, 2,048,000 transitions, 444.44 s, approximately 4,608 transitions/s; 3,197 MiB at end | Training and export passed; not a walking result |
| Flat deterministic evaluation | 20 s upright; final forward/lateral displacement +0.104/+0.093 m; zero lifted-foot touchdowns | Slides/pivots in a curved path; fails walking acceptance |
| Home deterministic evaluation | 10 s upright; zero lifted-foot touchdowns | Primitive room renders and runs; still not walking |
| Full inertia/CoM follow-up | Full link-frame tensor relative error ≤2.24e-7; CoM error ≤2.22e-9 m | Full tensor and CoM preserved, not just eigenvalues |
| CPU contracts | Seven new tests; eight legacy proxy tests; 14 legacy motion tests pass, one optional mesh test skipped | Assets, model separation, cache invalidation, error exits, and preserved legacy behavior checked |

The initial stance video is `reports/standing.mp4`; smoke video is under
`runs/20261116_210554_walk/review_model/`. Local run directories and large logs are
excluded from Git; publish small selected review artifacts and experiment summaries
under `docs/experiments/`. Final outcomes are maintained in
`docs/experiments/isaac-headless-baseline.md`.

**Next tuning round:** retain this baseline and its videos. Penalize persistent
stance-foot slip and uncommanded yaw without the saturating yaw-reward loophole,
strengthen alternating swing/clearance objectives, and test whether the provisional
actuator limits permit the intended weight transfer. Start a distinct experiment
with saved source/configuration; do not simply claim that more iterations solved
the observed reward exploitation. If the next documented round still fails, use
the reference-gait phase. Keep hardware deployment and household robustness as unpassed gates.
