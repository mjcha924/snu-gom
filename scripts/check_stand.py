"""Validate the URDF import and record a bounded-control standing rollout."""

import argparse
import json

from runtime import ROOT, close_app, configure_asset_cache, configure_runtime


def main():
    kit_args = configure_runtime("standing")
    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--stiffness", type=float, default=4.0)
    parser.add_argument("--damping", type=float, default=0.08)
    parser.add_argument("--video", action="store_true")
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if args.seconds <= 0 or args.stiffness <= 0 or args.damping < 0:
        parser.error("Duration and stiffness must be positive; damping must be nonnegative")
    args.headless = True
    args.enable_cameras = args.video
    args.kit_args = f"{kit_args} {args.kit_args}"
    launcher = AppLauncher(args)
    try:
        import numpy as np
        import torch
        import warp
        from snu_gom_walk.env import GomEnv, GomEnvCfg, MODEL

        warp.config.kernel_cache_dir = str(ROOT / ".cache/warp")
        cfg = GomEnvCfg()
        cfg.scene.num_envs = 1
        cfg.sim.device = args.device
        cfg.task = "stand"
        cfg.evaluation = True
        cfg.episode_length_s = args.seconds + 1
        cfg.stiffness = args.stiffness
        cfg.damping = args.damping
        cfg.viewer.eye = (0.65, -0.7, 0.4)
        cfg.viewer.lookat = (0.0, 0.0, 0.18)
        cfg.viewer.resolution = (640, 480)
        configure_asset_cache(cfg, MODEL)
        env = GomEnv(cfg, render_mode="rgb_array" if args.video else None)
        env.reset()
        mass = float(env.robot.root_physx_view.get_masses()[0].sum())
        assert abs(mass - MODEL["mass_kg"]) / MODEL["mass_kg"] < 0.001, (mass, MODEL["mass_kg"])
        assert not env.robot.is_fixed_base
        report = {
            "import_mass_kg": mass,
            "model": MODEL,
            "sim_joint_order": env.robot.joint_names,
            "sim_body_names": env.robot.body_names,
            "stiffness": args.stiffness,
            "damping": args.damping,
            "samples": [],
        }
        frames = []
        action = torch.zeros(1, 10, device=env.device)
        for step in range(round(args.seconds / env.step_dt)):
            with torch.inference_mode():
                observations, reward, terminated, truncated, extras = env.step(action)
            assert torch.isfinite(observations["policy"]).all()
            contacts, heights = env.foot_state()
            sample = {
                "time": (step + 1) * env.step_dt,
                "position": env.last_terminal["position"][0].tolist(),
                "upright": float(env.last_metrics["upright"][0]),
                "joint_positions": env.robot.data.joint_pos[0].tolist(),
                "torques": env.robot.data.applied_torque[0].tolist(),
                "contacts": contacts[0].tolist(),
                "sole_heights": heights[0].tolist(),
                "failed": bool(terminated[0]),
            }
            report["samples"].append(sample)
            if args.video and step % 2 == 0:
                frames.append(env.render())
            if terminated.any():
                break
        report["passed"] = not any(sample["failed"] for sample in report["samples"])
        report["duration"] = report["samples"][-1]["time"]
        report["horizontal_drift"] = float(np.linalg.norm(np.array(report["samples"][-1]["position"][:2])))
        path = ROOT / "reports/standing.json"
        path.write_text(json.dumps(report, indent=2) + "\n")
        (ROOT / "reports/model_audit.json").write_text(json.dumps(MODEL, indent=2) + "\n")
        if frames:
            import imageio.v2 as imageio
            imageio.mimsave(ROOT / "reports/standing.mp4", frames, fps=25)
            imageio.mimsave(ROOT / "reports/standing.gif", frames[::2], duration=80, loop=0)
        print(json.dumps({key: report[key] for key in ["passed", "duration", "horizontal_drift", "import_mass_kg"]}), flush=True)
    finally:
        close_app(launcher)


if __name__ == "__main__":
    main()
