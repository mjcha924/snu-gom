# Training, export and evaluation

## 1. Check the imported robot

Use `scripts/smoke_sim.py` with one environment and the GUI. Verify nine revolute joints, meter units, a floating torso, correct sitting/low endpoint poses, and ten rigid links. Estimated total mass is 0.664790 kg. Joint names are resolved explicitly into the library order; import order is never assumed.

The original URDF zero is the old crawl pose, not the revised low stance. The library converts geometric angles with `q_urdf = radians(angle_geometric) - origin_pitch_rad`. The revised fore bend at the low endpoint is approximately −0.38879 rad in URDF coordinates.

Inspect convex collision shapes and pair filtering, particularly the neck, paw-to-paw approach, paw/upper-link assemblies and torso underside. Some directly connected collision pairs may be filtered by the importer. Imported PhysX contact geometry is not the original exact BRep collision model. The proposed contact offset is 0.05 mm per shape; adjust based on imported geometry and simulation behavior, then rerun evaluation. Do not disable physical collision pairs merely to make a policy succeed.

Before long runs, make a short training API check:

```bash
python scripts/isaac.py train --isaac-lab /absolute/path/to/IsaacLab \
  --skill hold_sit --num_envs 16 --max_iterations 2 --headless --run_name api_check
```

## 2. Train one policy per skill

Use the README training command, initially for the two hold skills. All policies have the same observation/action layout but different weights and goal rewards.

| Setting | Initial choice | Meaning |
|---|---|---|
| Physics | 200 Hz | Proposed integration rate; verify small-link contact behavior |
| Policy | 50 Hz | Four physics steps per policy update |
| History | Four 34-value frames | 136 inputs; oldest frame first |
| Network | 256 → 128 → 64, ELU | Feed-forward actor and critic |
| PPO rollout | 32 steps × 256 environments | Starting batch size |
| Training budget | 3,000 iterations | Tune based on measured success and reward traces |
| Forward command | 0.003–0.020 m/s | Sampled per crawl episode; not a demonstrated speed |

Mass and inertia scale independently per body between 0.8 and 1.2 at training startup. Friction, restitution, per-reset PD gains, 0–20 ms actuator delay, small encoder/IMU noise and initial joint perturbations provide an initial range of variation. These are engineering starting ranges. They do not yet model backlash, deadband, voltage sag, thermal limits, soft coverings, measured torque-speed curves or IMU estimator bias.

Pose and gravity rewards provide continuous feedback toward the endpoint. Transitions have no required intermediate trajectory. The crawl reward uses horizontal world velocity along the reset heading, not the body's tilted X component. Actor observations use only intended onboard measurements; world position, contact force and linear velocity are used for rewards/evaluation, not policy inputs.

A successful optimizer run may still discover undesirable motion. Inspect actual contact sequences and failures. If transitions stall, first resolve asset/motor/contact fidelity, then tune reward scales, starting-state perturbations or a reset curriculum. The optional reference can support later imitation training, but this release does not implement an imitation objective or automatic curriculum.

The launcher saves a run manifest under `run_metadata/`, including a hash of the bundled model, IO data and source. Keep the matching manifest with each checkpoint. Changes to the physical model, control contract or source invalidate compatibility checks. Also retain the official run's saved environment/agent configs; command-line overrides are recorded but are not folded into the bundled source hash.

## 3. Export the trained policy

The wrapper delegates playback to the official versioned RSL-RL `play.py`, which exports policies during playback. Use the checkpoint from the run you intend to deploy:

```bash
python scripts/isaac.py play --isaac-lab /absolute/path/to/IsaacLab \
  --skill hold_sit --num_envs 1 --checkpoint /absolute/path/to/model_3000.pt
```

Use the `policy.onnx` emitted in that checkpoint run's export directory. Confirm the export location in the official script's log. For this library it must accept one float32 input `[batch, 136]` and produce one output `[batch, 9]`. Do not substitute actor-only weights that change the observation preprocessing.

Register the file using the `contract_sha256` recorded for its training run:

```bash
snu-bear register hold_sit /absolute/path/to/exported/policy.onnx \
  --contract-sha256 PASTE_THE_MATCHING_TRAINING_MANIFEST_HASH
```

Registration loads the ONNX model to check input/output shape and stores a file checksum. It sets status to `trained_unverified`; matching shape and checksums do not establish competent motion.

## 4. Evaluate actual behavior

```bash
python scripts/evaluate.py --skill hold_sit --episodes 100 --nominal \
  --seed 10001 --headless --output reports/hold_sit_nominal.json
python scripts/evaluate.py --skill hold_sit --episodes 100 \
  --seed 20001 --headless --output reports/hold_sit_randomized.json
```

The evaluator uses batch size one for compatibility with fixed-batch exports. In randomized evaluation, mass/friction and gains are resampled on every reset. Record videos with the official playback command and inspect failures; the score is only a baseline metric.

For pose skills, `goal_reached` means a 0.5-second settled endpoint was observed at least once. For crawling it means at least 30 mm of forward travel with approximately correct speed, low attitude and unloaded belly was observed at least once. `goal_without_failure_rate` additionally requires no terminating failure that episode. It does not certify the entire contact sequence, continuous stability, lack of self-contact or reliable long-duration motion.

This release does not automatically mark policies hardware-ready, and does not include a chained-policy simulation evaluator. Test the complete sequence hold-sit → transition → hold-low → crawl → hold-low → return → hold-sit in simulation before hardware use. The runtime selector is implemented, but that sequence has not been dynamically validated.

Use a fresh evaluation seed and inspect outcomes across actual mass/friction/servo uncertainty. Train and evaluate the return transition independently. Its existence in the registry is not evidence that the mechanism can perform it.
# Asset prerequisite for the GitHub release

The geometry meshes are intentionally omitted from this checkout. Complete [simulation asset setup](../../docs/SIMULATION_ASSETS.md) before any simulator import, smoke check or training command below. The URDF alone is insufficient.
