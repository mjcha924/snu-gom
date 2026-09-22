# Primary references

The original robot geometry and revised endpoint/reference data come from the user's SNU Bear V0.6 project and the preceding motion study. They remain estimates until the assembled robot is measured. No external pretrained weights are included.

The integration targets these NVIDIA/Isaac Lab APIs:

- [Isaac Lab v2.3.0 installation](https://isaac-sim.github.io/IsaacLab/v2.3.0/source/setup/installation/pip_installation.html): simulator and Python environment.
- [Direct workflow environment tutorial](https://isaac-sim.github.io/IsaacLab/v2.3.0/source/tutorials/03_envs/create_direct_rl_env.html): reset, step, reward and observation hooks.
- [URDF converter configuration](https://isaac-sim.github.io/IsaacLab/v2.3.0/_modules/isaaclab/sim/converters/urdf_converter_cfg.html): floating import and collision decomposition.
- [Actuator configuration](https://isaac-sim.github.io/IsaacLab/v2.3.0/_modules/isaaclab/actuators/actuator_cfg.html): delayed PD actuator settings.
- [Randomization events](https://isaac-sim.github.io/IsaacLab/v2.3.0/_modules/isaaclab/envs/mdp/events.html): material, mass/inertia and actuator-gain variation.
- [RSL-RL configuration](https://isaac-sim.github.io/IsaacLab/v2.3.0/_modules/isaaclab_rl/rsl_rl/rl_cfg.html): policy/critic and PPO configuration.

This package supplies original task and runtime code around those APIs. Isaac Lab, Isaac Sim, RSL-RL, ONNX Runtime and their licenses are distributed separately; their source and pretrained assets are not bundled here.
