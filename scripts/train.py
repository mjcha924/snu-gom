"""Train a small SNU-GOM PPO policy in headless Isaac Sim."""

import argparse
from datetime import datetime
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import shutil
import time

from runtime import ROOT, close_app, configure_asset_cache, configure_runtime


def source_hashes():
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / "snu_gom_walk").glob("*.py"))
    }


def main():
    kit_args = configure_runtime("training")
    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=["stand", "walk"], default="walk")
    parser.add_argument("--num-envs", type=int, default=64)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scene", choices=["flat", "home"], default="flat")
    parser.add_argument("--speed", type=float, default=0.025)
    parser.add_argument("--gait-period", type=float, default=2.4)
    parser.add_argument("--reference", action="store_true")
    parser.add_argument("--support-reference", action="store_true")
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if args.num_envs < 1 or args.iterations < 1:
        parser.error("Environment count and iterations must be positive")
    if not math.isfinite(args.speed) or args.speed < 0:
        parser.error("Speed must be finite and nonnegative")
    if not math.isfinite(args.gait_period) or args.gait_period <= 0:
        parser.error("Gait period must be finite and positive")
    args.headless = True
    args.enable_cameras = False
    args.kit_args = f"{kit_args} {args.kit_args}"
    launcher = AppLauncher(args)
    try:
        import torch
        import warp
        from isaaclab.utils.io import dump_yaml
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from rsl_rl.runners import OnPolicyRunner
        from snu_gom_walk.agent import agent_config
        from snu_gom_walk.env import GomEnv, GomEnvCfg, MODEL

        torch.set_num_threads(4)
        warp.config.kernel_cache_dir = str(ROOT / ".cache/warp")
        run_dir = (args.output or ROOT / "runs" / f"{datetime.now():%Y%m%d_%H%M%S}_{args.task}").resolve()
        if not run_dir.is_relative_to(ROOT):
            raise ValueError("Run output must be inside the snu-gom workspace")
        run_dir.mkdir(parents=True, exist_ok=False)
        cfg = GomEnvCfg()
        cfg.scene.num_envs = args.num_envs
        cfg.sim.device = args.device
        cfg.task = args.task
        cfg.seed = args.seed
        cfg.scene_layout = args.scene
        cfg.speed = args.speed
        cfg.gait_period = args.gait_period
        cfg.reference_assistance = args.reference or args.support_reference
        if cfg.reference_assistance:
            cfg.foot_clearance = 0.005
        if args.support_reference:
            cfg.reference_kind = "support"
            cfg.reference_lean = 0.30
        if args.scene == "home":
            cfg.scene.env_spacing = 5.0
        agent = agent_config()
        agent["seed"] = args.seed
        agent["device"] = args.device
        settings = {"task": cfg.task, "speed": cfg.speed, "seed": cfg.seed,
                    "stiffness": cfg.stiffness, "damping": cfg.damping, "gait_period": cfg.gait_period,
                    "scene_layout": cfg.scene_layout}
        settings.update(stance_knee=cfg.stance_knee, foot_clearance=cfg.foot_clearance)
        settings.update(reference_assistance=cfg.reference_assistance, reference_lean=cfg.reference_lean)
        settings["reference_kind"] = cfg.reference_kind
        if args.checkpoint:
            saved = json.loads((args.checkpoint.resolve().parent / "config.json").read_text())
            if saved["model_hashes"] != MODEL["hashes"] or saved["source_hashes"] != source_hashes():
                raise ValueError("Checkpoint model/source differs; start a new experiment")
            if saved["settings"] != settings:
                raise ValueError("Resume settings differ from the saved run")
            agent = saved["agent"]
        manifest = {
            "settings": settings,
            "agent": agent,
            "model_hashes": MODEL["hashes"],
            "source_hashes": source_hashes(),
            "num_envs": args.num_envs,
            "iterations_requested": args.iterations,
            "parent_checkpoint": str(args.checkpoint.resolve()) if args.checkpoint else None,
            "versions": {name: importlib.metadata.version(name) for name in ["isaacsim", "isaaclab", "rsl-rl-lib", "torch"]},
        }
        (run_dir / "config.json").write_text(json.dumps(manifest, indent=2) + "\n")
        for directory in ["snu_gom_walk", "scripts"]:
            shutil.copytree(ROOT / directory, run_dir / "source" / directory, ignore=shutil.ignore_patterns("__pycache__"))
        configure_asset_cache(cfg, MODEL)
        env = GomEnv(cfg)
        if env.reference_report is not None:
            (run_dir / "reference.json").write_text(json.dumps(env.reference_report, indent=2) + "\n")
        dump_yaml(str(run_dir / "environment.yaml"), env.cfg)
        wrapped = RslRlVecEnvWrapper(env, clip_actions=1.0)
        runner = OnPolicyRunner(wrapped, agent, log_dir=str(run_dir), device=args.device)
        if args.checkpoint:
            runner.load(str(args.checkpoint.resolve()))
            runner.current_learning_iteration += 1
        started = time.monotonic()
        print(f"RUN_DIRECTORY={run_dir}", flush=True)
        runner.learn(num_learning_iterations=args.iterations, init_at_random_ep_len=False)
        runner.save(str(run_dir / "model.pt"))
        runner.export_policy_to_jit(str(run_dir), filename="policy_jit.pt")
        with torch.inference_mode():
            observations = wrapped.get_observations()
            original = runner.get_inference_policy()(observations)
            exported = torch.jit.load(str(run_dir / "policy_jit.pt"), map_location=args.device)
            reproduced = exported(observations["policy"])
            torch.testing.assert_close(reproduced, original, atol=1e-5, rtol=1e-5)
        duration = time.monotonic() - started
        summary = {
            "status": "training_completed",
            "walking_validated": False,
            "iteration": runner.current_learning_iteration,
            "duration_seconds": duration,
            "transitions": args.iterations * args.num_envs * agent["num_steps_per_env"],
            "transitions_per_second": args.iterations * args.num_envs * agent["num_steps_per_env"] / duration,
            "export_action_equivalence": "passed",
            "gpu_memory_at_end": subprocess.check_output([
                "nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader"
            ], text=True).strip(),
        }
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2), flush=True)
    finally:
        close_app(launcher)


if __name__ == "__main__":
    main()
