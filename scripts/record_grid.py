"""Render parallel training-style rollouts without performing optimizer updates."""

import argparse
import json
from pathlib import Path

from runtime import ROOT, close_app, configure_asset_cache, configure_runtime
from train import source_hashes


def main():
    kit_args = configure_runtime("grid_preview")
    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--num-envs", type=int, default=16)
    parser.add_argument("--seconds", type=float, default=8.0)
    parser.add_argument("--deterministic", action="store_true")
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if not 1 <= args.num_envs <= 64 or args.seconds <= 0:
        parser.error("Use 1–64 environments and a positive duration")
    args.headless = True
    args.enable_cameras = True
    args.kit_args = f"{kit_args} {args.kit_args}"
    launcher = AppLauncher(args)
    try:
        import imageio.v2 as imageio
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        import torch
        import warp
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from rsl_rl.runners import OnPolicyRunner
        from snu_gom_walk.env import GomEnv, GomEnvCfg, MODEL

        torch.set_num_threads(4)
        warp.config.kernel_cache_dir = str(ROOT / ".cache/warp")
        checkpoint = args.checkpoint.resolve()
        if not checkpoint.is_relative_to(ROOT):
            parser.error("Checkpoint must be inside the workspace")
        saved = json.loads((checkpoint.parent / "config.json").read_text())
        if saved["model_hashes"] != MODEL["hashes"] or saved["source_hashes"] != source_hashes():
            raise ValueError("Checkpoint source/model mismatch")
        cfg = GomEnvCfg()
        for key, value in saved["settings"].items():
            setattr(cfg, key, value)
        cfg.scene_layout = "flat"
        cfg.evaluation = False
        cfg.scene.num_envs = args.num_envs
        cfg.scene.env_spacing = 0.7
        cfg.sim.device = args.device
        cfg.viewer.resolution = (960, 720)
        configure_asset_cache(cfg, MODEL)
        env = GomEnv(cfg, render_mode="rgb_array")
        center = env.scene.env_origins.mean(dim=0).cpu().numpy()
        span = max(float(env.scene.env_origins[:, :2].max() - env.scene.env_origins[:, :2].min()), 1.0)
        env.sim.set_camera_view(
            (center[0] + span * 1.1, center[1] - span * 1.25, span * 1.2),
            (center[0], center[1], 0.12),
        )
        wrapped = RslRlVecEnvWrapper(env, clip_actions=1.0)
        runner = OnPolicyRunner(wrapped, saved["agent"], log_dir=None, device=args.device)
        runner.load(str(checkpoint))
        policy = runner.get_inference_policy()
        observations, _ = wrapped.reset()
        frames = []
        fall_counts = torch.zeros(args.num_envs, dtype=torch.long, device=env.device)
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
        small_font = ImageFont.truetype("DejaVuSans.ttf", 16)
        for step in range(round(args.seconds / env.step_dt)):
            with torch.inference_mode():
                actions = policy(observations, stochastic_output=not args.deterministic)
                observations, rewards, dones, extras = wrapped.step(actions)
            fall_counts += env.last_terminal["fallen"].long()
            if step % 2 == 0:
                frame = Image.fromarray(env.render())
                draw = ImageDraw.Draw(frame)
                draw.rectangle((0, 0, 960, 72), fill=(24, 32, 45))
                draw.text((16, 9), f"SNU-GOM | {args.num_envs} parallel robots | checkpoint {checkpoint.stem}", font=font, fill="white")
                mode = "deterministic" if args.deterministic else "exploration enabled"
                draw.text((16, 40), f"Rollout preview, no optimizer updates | {mode} | t={(step + 1) * env.step_dt:.1f}s | falls/resets: {int(fall_counts.sum())}", font=small_font, fill=(208, 221, 236))
                frames.append(np.array(frame))
        output = checkpoint.parent / f"grid_{checkpoint.stem}_{args.num_envs}{'_deterministic' if args.deterministic else '_exploration'}"
        output.mkdir(exist_ok=True)
        imageio.mimsave(output / "parallel_rollout.mp4", frames, fps=25)
        imageio.imwrite(output / "preview.png", frames[len(frames) // 2])
        gif_frames = [Image.fromarray(frame).quantize(colors=128, method=Image.Quantize.FASTOCTREE) for frame in frames[::2]]
        gif_frames[0].save(output / "parallel_rollout.gif", save_all=True, append_images=gif_frames[1:], duration=80, loop=0, optimize=False)
        summary = {
            "checkpoint": str(checkpoint.relative_to(ROOT)),
            "num_envs": args.num_envs,
            "duration_seconds": args.seconds,
            "exploration": not args.deterministic,
            "optimizer_updates": 0,
            "fall_resets_per_environment": fall_counts.tolist(),
            "purpose": "Parallel training-style rollout visualization, not a walking-success evaluation",
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2), flush=True)
        print(f"GRID_DIRECTORY={output}", flush=True)
    finally:
        close_app(launcher)


if __name__ == "__main__":
    main()
