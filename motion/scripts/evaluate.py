"""Evaluate one exported ONNX skill in physics, recording actual outcomes."""
import argparse
import json
from pathlib import Path
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument("--skill", required=True)
parser.add_argument("--registry", default="policies/registry.json")
parser.add_argument("--episodes", type=int, default=100)
parser.add_argument("--seed", type=int, default=10001)
parser.add_argument("--nominal", action="store_true")
parser.add_argument("--output", type=Path, default=Path("evaluation.json"))
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.episodes < 1:
    parser.error("--episodes must be positive")
launcher = AppLauncher(args)
try:
    import gymnasium as gym
    import torch
    import snu_bear_motion.isaaclab_tasks
    from isaaclab_tasks.utils import parse_env_cfg
    from snu_bear_motion.contract import SKILLS, fingerprint
    from snu_bear_motion.registry import Registry, sha256
    from snu_bear_motion.runtime import OnnxPolicy
    checkpoint = Registry(args.registry).resolve(args.skill)
    policy = OnnxPolicy(checkpoint)
    task = SKILLS[args.skill]["task_id"]
    cfg = parse_env_cfg(task, device=args.device, num_envs=1)
    cfg.seed = args.seed
    if args.nominal:
        cfg.events = None
        cfg.observation_noise = False
        cfg.reset_joint_noise_rad = 0.0
        cfg.robot_cfg.actuators["motors"].max_delay = 0
    else:
        # Batch-one evaluation can afford CPU material/mass updates on each reset.
        # Training keeps these events at startup for vectorized throughput.
        cfg.events.material.mode = "reset"
        cfg.events.mass.mode = "reset"
    env = gym.make(task, cfg=cfg)
    obs, _ = env.reset()
    rows, elapsed, total_reward = [], 0.0, 0.0
    while len(rows) < args.episodes and launcher.app.is_running():
        action = torch.as_tensor(policy(obs["policy"][0].cpu().numpy()), device=env.unwrapped.device)[None]
        obs, reward, terminated, truncated, _ = env.step(action)
        elapsed += env.unwrapped.step_dt
        total_reward += reward.item()
        if bool(terminated[0] | truncated[0]):
            b = env.unwrapped
            rows.append({"episode": len(rows), "elapsed_s": elapsed, "return": total_reward,
                "goal_reached": bool(b.last_success[0]), "failed": bool(b.last_failure[0]),
                "travel_m": float(b.last_travel[0])})
            elapsed, total_reward = 0.0, 0.0
    report = {"skill": args.skill, "contract_sha256": fingerprint(), "onnx_sha256": sha256(checkpoint),
        "requested_episodes": args.episodes, "completed_episodes": len(rows), "seed": args.seed,
        "nominal": args.nominal, "status": "measured_simulation_results_not_hardware_validation",
        "goal_without_failure_rate": sum(r["goal_reached"] and not r["failed"] for r in rows)/max(1, len(rows)),
        "episodes": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(f"Saved {len(rows)} actual simulation trials to {args.output}")
    env.close()
finally:
    launcher.app.close()
