"""Evaluate identical saved weights on flat and primitive-home scenes."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from runtime import ROOT
from snu_gom_walk.evaluation import straight_walk_gate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=20)
    args = parser.parse_args()
    if args.episodes < 1:
        parser.error("Episode count must be positive")
    checkpoint = args.checkpoint.resolve()
    if not checkpoint.is_relative_to(ROOT):
        parser.error("Checkpoint and output must stay in the workspace")
    fingerprint = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    output = checkpoint.parent / f"comparison_{checkpoint.stem}_{args.episodes}ep"
    output.mkdir(exist_ok=True)
    report = {"checkpoint_sha256": fingerprint, "episodes_per_scene": args.episodes, "scenes": {}}
    for scene in ["flat", "home"]:
        with (output / f"{scene}.log").open("w") as log:
            subprocess.run([
                sys.executable, "-u", str(ROOT / "scripts/play.py"), "--checkpoint", str(checkpoint),
                "--scene", scene, "--seconds", "30", "--episodes", str(args.episodes), "--headless",
            ], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != fingerprint:
            raise RuntimeError("Checkpoint changed during comparison")
        review = checkpoint.parent / f"review_{checkpoint.stem}_{scene}_30s_{args.episodes}ep"
        episodes = json.loads((review / "summary.json").read_text())
        report["scenes"][scene] = {"straight_walk_gate": straight_walk_gate(episodes), "episodes": episodes}
        print(f"{scene}: {report['scenes'][scene]['straight_walk_gate']}", flush=True)
    report["curriculum_advance_allowed"] = False
    report["reason"] = "Straight walking comparison does not replace start/stop, multiple-seed, or actuator checks."
    (output / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"COMPARISON_DIRECTORY={output}", flush=True)


if __name__ == "__main__":
    main()
