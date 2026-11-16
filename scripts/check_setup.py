"""Start headless Isaac, step physics, and record the local software baseline."""

import argparse
import importlib.metadata
import json
import platform
import subprocess
import time

from runtime import ROOT, close_app, configure_runtime


def main():
    kit_args = configure_runtime("setup")
    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser()
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    args.headless = True
    args.kit_args = f"{kit_args} {args.kit_args}"
    started = time.monotonic()
    launcher = AppLauncher(args)
    try:
        import torch
        import warp
        import isaaclab.sim as sim_utils

        warp.config.kernel_cache_dir = str(ROOT / ".cache/warp")
        sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=0.002, device=args.device))
        sim_utils.CuboidCfg(
            size=(4.0, 4.0, 0.1),
            collision_props=sim_utils.CollisionPropertiesCfg(),
        ).func("/World/floor", sim_utils.CuboidCfg(
            size=(4.0, 4.0, 0.1),
            collision_props=sim_utils.CollisionPropertiesCfg(),
        ), translation=(0.0, 0.0, -0.05))
        sim.reset()
        for step in range(100):
            sim.step(render=False)
        result = {
            "status": "passed",
            "physics_steps": 100,
            "elapsed_seconds": time.monotonic() - started,
            "python": platform.python_version(),
            "device": args.device,
            "gpu": torch.cuda.get_device_name(0),
            "versions": {
                name: importlib.metadata.version(name)
                for name in ["isaacsim", "isaaclab", "rsl-rl-lib", "torch"]
            },
            "gpu_memory": subprocess.check_output([
                "nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader"
            ], text=True).strip(),
        }
        (ROOT / "reports/setup.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2), flush=True)
    finally:
        close_app(launcher)


if __name__ == "__main__":
    main()
