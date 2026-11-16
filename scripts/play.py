"""Evaluate a saved policy and optionally render a headless checkpoint video."""

import argparse
import json
from pathlib import Path

from runtime import ROOT, close_app, configure_asset_cache, configure_runtime
from train import source_hashes


def main():
    kit_args = configure_runtime("playback")
    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--stop-at", type=float)
    parser.add_argument("--scene", choices=["flat", "home"])
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if args.seconds <= 0 or args.episodes < 1:
        parser.error("Duration and episode count must be positive")
    args.headless = True
    args.enable_cameras = args.video
    args.kit_args = f"{kit_args} {args.kit_args}"
    launcher = AppLauncher(args)
    try:
        import imageio.v2 as imageio
        import numpy as np
        import torch
        import warp
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from rsl_rl.runners import OnPolicyRunner
        from snu_gom_walk.env import GomEnv, GomEnvCfg, MODEL

        torch.set_num_threads(4)
        warp.config.kernel_cache_dir = str(ROOT / ".cache/warp")
        checkpoint = args.checkpoint.resolve()
        saved = json.loads((checkpoint.parent / "config.json").read_text())
        if saved["model_hashes"] != MODEL["hashes"] or saved["source_hashes"] != source_hashes():
            raise ValueError("Saved model/source hash differs; playback cannot silently use edited defaults")
        cfg = GomEnvCfg()
        for key, value in saved["settings"].items():
            setattr(cfg, key, value)
        cfg.evaluation = True
        if args.scene:
            cfg.scene_layout = args.scene
        cfg.scene.num_envs = 1
        cfg.sim.device = args.device
        cfg.episode_length_s = args.seconds + 1
        cfg.viewer.eye = (0.65, -0.7, 0.4)
        cfg.viewer.lookat = (0.0, 0.0, 0.18)
        if cfg.scene_layout == "home":
            cfg.viewer.eye = (-0.6, -1.1, 0.55)
            cfg.viewer.lookat = (0.3, 0.25, 0.22)
        cfg.viewer.resolution = (640, 480)
        configure_asset_cache(cfg, MODEL)
        env = GomEnv(cfg, render_mode="rgb_array" if args.video else None)
        wrapped = RslRlVecEnvWrapper(env, clip_actions=1.0)
        runner = OnPolicyRunner(wrapped, saved["agent"], log_dir=None, device=args.device)
        runner.load(str(checkpoint))
        policy = runner.get_inference_policy()
        output = checkpoint.parent / f"review_{checkpoint.stem}_{cfg.scene_layout}{'_stop' if args.stop_at is not None else ''}_{args.seconds:g}s_{args.episodes}ep"
        output.mkdir(exist_ok=True)
        results = []
        frames = []
        for episode in range(args.episodes):
            observations, _ = wrapped.reset()
            if episode:
                offsets = (torch.rand_like(env.robot.data.joint_pos) - 0.5) * 0.01
                env.robot.write_joint_state_to_sim(env.robot.data.default_joint_pos + offsets, torch.zeros_like(offsets))
                observations = wrapped.get_observations()
            samples = []
            for step in range(round(args.seconds / env.step_dt)):
                if args.stop_at is not None and step * env.step_dt >= args.stop_at:
                    env.commands.zero_()
                    observations = wrapped.get_observations()
                with torch.no_grad():
                    observations, rewards, dones, extras = wrapped.step(policy(observations))
                sample = {
                    "time": (step + 1) * env.step_dt,
                    "position": env.last_terminal["position"][0].tolist(),
                    "velocity": env.last_terminal["velocity"][0].tolist(),
                    "upright": float(env.last_metrics["upright"][0]),
                    "contacts": env.last_metrics["contacts"][0].tolist(),
                    "sole_heights": env.last_metrics["sole_heights"][0].tolist(),
                    "fallen": bool(env.last_terminal["fallen"][0]),
                    "quaternion": env.last_terminal["quaternion"][0].tolist(),
                    "foot_positions": env.last_terminal["foot_positions"][0].tolist(),
                    "peak_joint_speed": float(env.last_terminal["joint_velocities"][0].abs().max()),
                    "peak_torque": float(env.last_terminal["torques"][0].abs().max()),
                }
                samples.append(sample)
                if args.video and episode == 0 and step % 2 == 0 and not dones.any():
                    position = sample["position"]
                    env.sim.set_camera_view(
                        (position[0] + cfg.viewer.eye[0], position[1] + cfg.viewer.eye[1], cfg.viewer.eye[2]),
                        (position[0] + cfg.viewer.lookat[0], position[1] + cfg.viewer.lookat[1], cfg.viewer.lookat[2]),
                    )
                    frames.append(env.render())
                if dones.any():
                    break
            contact_array = np.array([sample["contacts"] for sample in samples], dtype=bool)
            height_array = np.array([sample["sole_heights"] for sample in samples])
            clear_steps = [0, 0]
            lifted = [False, False]
            landing_order = []
            air_frames = [0, 0]
            previous_landings = [None, None]
            strides = [[], []]
            for sample_index in range(len(samples)):
                for foot_index in range(2):
                    if not contact_array[sample_index, foot_index]:
                        air_frames[foot_index] += 1
                    if not contact_array[sample_index, foot_index] and height_array[sample_index, foot_index] > 0.002:
                        lifted[foot_index] = True
                    if contact_array[sample_index, foot_index] and lifted[foot_index] and air_frames[foot_index] >= 3:
                        clear_steps[foot_index] += 1
                        landing_order.append(foot_index)
                        landing = np.array(samples[sample_index]["foot_positions"][foot_index][:2])
                        if previous_landings[foot_index] is not None:
                            strides[foot_index].append((landing - previous_landings[foot_index]).tolist())
                        previous_landings[foot_index] = landing
                    if contact_array[sample_index, foot_index]:
                        lifted[foot_index] = False
                        air_frames[foot_index] = 0
            quaternions = np.array([sample["quaternion"] for sample in samples])
            yaw = np.unwrap(np.arctan2(
                2 * (quaternions[:, 0] * quaternions[:, 3] + quaternions[:, 1] * quaternions[:, 2]),
                1 - 2 * (quaternions[:, 2] ** 2 + quaternions[:, 3] ** 2),
            ))
            results.append({
                "episode": episode,
                "survived": not any(sample["fallen"] for sample in samples),
                "duration": samples[-1]["time"],
                "forward_distance": samples[-1]["position"][0],
                "lateral_distance": samples[-1]["position"][1],
                "mean_speed": float(np.mean([sample["velocity"][0] for sample in samples])),
                "clear_touchdowns_left_right": clear_steps,
                "alternating_touchdowns": sum(first != second for first, second in zip(landing_order, landing_order[1:])),
                "same_foot_stride_xy_left_right": strides,
                "heading_change_degrees": float(np.degrees(yaw[-1] - yaw[0])),
                "peak_joint_speed": max(sample["peak_joint_speed"] for sample in samples),
                "peak_torque": max(sample["peak_torque"] for sample in samples),
                "max_sole_height_left_right": height_array.max(axis=0).tolist(),
                "both_feet_contact_fraction": float(contact_array.all(axis=1).mean()),
                "speed_mae": float(np.mean([
                    abs(sample["velocity"][0] - (0.0 if args.stop_at is not None and sample["time"] > args.stop_at else cfg.speed))
                    for sample in samples if sample["time"] > min(2.0, samples[-1]["time"] / 2)
                ])),
                "samples": samples,
            })
        summary = [{key: value for key, value in result.items() if key != "samples"} for result in results]
        (output / "evaluation.json").write_text(json.dumps({"checkpoint": str(checkpoint), "scene_layout": cfg.scene_layout, "episodes": results}, indent=2) + "\n")
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        if frames:
            imageio.mimsave(output / "rollout.mp4", frames, fps=25)
            imageio.mimsave(output / "rollout.gif", frames[::2], duration=80, loop=0)
            imageio.imwrite(output / "preview.png", frames[len(frames) // 2])
        print(json.dumps(summary, indent=2), flush=True)
        print(f"REVIEW_DIRECTORY={output}", flush=True)
    finally:
        close_app(launcher)


if __name__ == "__main__":
    main()
