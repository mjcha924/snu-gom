"""Lazy Gym registrations: safe to import before AppLauncher starts Kit."""
import gymnasium as gym

for name, cfg in [("HoldSit", "HoldSitCfg"), ("HoldLow", "HoldLowCfg"),
                  ("SitToLow", "SitToLowCfg"), ("LowToSit", "LowToSitCfg"),
                  ("CrawlForward", "CrawlForwardCfg")]:
    task_id = f"SNU-Bear-{name}-v0"
    if task_id not in gym.registry:
        gym.register(id=task_id, entry_point="snu_bear_motion.isaaclab_tasks.env:BearEnv",
            disable_env_checker=True,
            kwargs={"env_cfg_entry_point": f"snu_bear_motion.isaaclab_tasks.config:{cfg}",
                    "rsl_rl_cfg_entry_point": "snu_bear_motion.isaaclab_tasks.ppo:BearPPOCfg"})
