# Simulating SNU Bear V0.6

This model is the original 9-joint bear, not the purple biped concept. A URDF describes geometry, joints and inertias; it does not contain a walking controller. Start with playback, then investigate physics, and only then train a policy.

## 1. Install and watch motion (no GPU required)

Use Python 3.11 in a virtual environment on a desktop with a display:

```bash
git clone https://github.com/mjcha924/snu-bear.git
cd snu-bear
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-sim.txt
python scripts/simulate.py --mode replay
```

Windows PowerShell activation: `.venv\Scripts\Activate.ps1`. If you already cloned the repository, use `git pull` instead of cloning again. If PyBullet has no wheel for your platform/Python, use Python 3.11 with a supported desktop environment or consult the upstream installation instructions.

The runner automatically restores all ten original STL meshes from the included compressed text assets and verifies SHA-256. This is offline after dependencies are installed. You can also run `python scripts/restore_meshes.py` separately. Keep the mesh folder beside the URDF.

Replay shows the saved **3 mm forward shuffle**, with short paw lifts, once and holds the last frame. The 83 CAD samples are displayed at 80 ms per sample; this timing is an illustration, not a designed motor trajectory. The body and joints are directly positioned, gravity is disabled, and the base is fixed. It is not evidence the robot can physically execute the motion. No sit-to-crawl trajectory is included.

```bash
python scripts/simulate.py --mode pose --pose sit
python scripts/simulate.py --mode pose --pose crawl
```

These display the two endpoint poses. `--seconds 60` keeps the window open longer. Headless machines can use `--headless`.

## 2. Try a real physics step

```bash
python scripts/simulate.py --mode physics --pose crawl
python scripts/simulate.py --mode physics --motion crawl
```

The first command tries to hold the low stance. The second tracks the saved crawl joint targets. Both use a floating base, gravity, ground contact and finite-strength position motors. **The body is never prescribed after initialization in physics mode.** The robot may fall, slip or fail to follow the targets; no trained stabilizing policy is supplied.

These are experimental diagnostics, not calibrated DYNAMIXEL simulations. Current settings are inherited placeholders: 0.2 N·m maximum command and 1 rad/s maximum velocity. The exact X330 variant, torque-speed envelope, thermal limits, backlash, lag and gains remain unresolved. Joint ranges ±π are not collision-safe ranges. Masses use 18 g per motor and estimated printed parts.

PyBullet's default moving-mesh collision representation is a coarse convex approximation. Shell openings can be filled; adjacent parent-child collision pairs are excluded by this runner. Inspect and improve collision shapes/filtering before using results for feasibility or RL. A model import or finite numerical rollout does not establish walking or stability.

## 3. Edit motion targets

- `motion/src/snu_bear_motion/data/robot/pose_presets.json`: saved CAD sitting/low poses, including base transform.
- `.../joint_registry.json`: names, local origins and CAD neutral-angle offsets.
- `.../crawl_states.json`: historical CAD sample sequence. The final legacy stage label says 4 mm, but the stored base displacement is 3 mm.
- `.../actuators.json`: unresolved motor model and calibration fields.
- `scripts/simulate.py`: position targets and explicit placeholder gains/force limits.

Use radians and metres. All nine axes are local +Y. The paw and bend motor case form one lower link. Geometric offsets are not hardware encoder zeros. The root is `torso`; there is no fixed world joint in the URDF itself. Do not apply a second 0.001 mesh scale.

The existing motion library has its own revised target poses in `data/contract.json`. They are not identical to the historical CAD presets used by this viewer; keep the distinction when comparing behavior.

## 4. Move to Isaac Sim / Isaac Lab for RL

1. Restore meshes, then import `motion/src/snu_bear_motion/data/robot/snu_bear_v06.urdf` using Isaac Sim's URDF importer.
2. Check ten links, nine revolute joints, metre scale and imported inertias. Start with gravity disabled/fixed base for inspection, then make the base movable for locomotion.
3. Inspect collision meshes. Evaluate convex decomposition to preserve the concave shell shape better than one convex hull; check resulting contacts and narrow clearances visually.
4. Set the full base transform and joint pose, add a ground plane, configure realistic drives, and test holding a pose before asking it to walk.
5. Follow [the existing training guide](../motion/docs/TRAINING.md). Its API target remains Isaac Lab 2.3.0 / Isaac Sim 5.1.0 / Python 3.11, not verified against current newer versions. Train holding skills first; all supplied policy entries remain untrained.

The lightweight PyBullet viewer is a separate entry point and does not replace the Isaac training stack. Neither the sit-to-crawl transition nor a bipedal gait is validated by this release.

## Checks and sources

The local environment verified exact mesh reconstruction and the existing CPU model tests. PyBullet could not be installed in that environment, so its runtime tests are provided in the GitHub workflow. Check the workflow result before treating the runner as runtime-tested. Isaac Sim was not run.

- [PyBullet upstream quickstart](https://github.com/bulletphysics/bullet3/blob/master/docs/pybullet_quickstart_guide/PyBulletQuickstartGuide.md.html)
- [Isaac Sim 5.1 URDF importer](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html)
