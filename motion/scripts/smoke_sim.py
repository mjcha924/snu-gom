"""Import/reset/step smoke check, not a learned motion demonstration."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument("--skill", default="hold_sit")
parser.add_argument("--steps", type=int, default=100)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
launcher = AppLauncher(args)
try:
    import gymnasium as gym
    import torch
    import snu_bear_motion.isaaclab_tasks
    from isaaclab_tasks.utils import parse_env_cfg
    from snu_bear_motion.contract import SKILLS
    task = SKILLS[args.skill]["task_id"]
    cfg = parse_env_cfg(task, device=args.device, num_envs=1)
    cfg.events = None
    cfg.observation_noise = False
    cfg.reset_joint_noise_rad = 0.0
    env = gym.make(task, cfg=cfg)
    obs, _ = env.reset()
    assert tuple(obs["policy"].shape) == (1, 136)
    for _ in range(args.steps):
        b = env.unwrapped
        # Hold the current commanded targets only to exercise the import and API.
        action = ((b.targets-b.mid)/b.half).clone()
        obs, reward, terminated, truncated, _ = env.step(action)
        assert torch.isfinite(obs["policy"]).all() and torch.isfinite(reward).all()
    print("Import/reset/step check completed. No motion capability established.")
    env.close()
finally:
    launcher.app.close()
