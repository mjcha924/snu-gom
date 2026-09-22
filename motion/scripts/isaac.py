"""Launch the matching official Isaac Lab RSL-RL train/play script.

Use Isaac Lab's Python environment. Task registration is deliberately lazy:
modules needing Kit are imported only after the official script launches AppLauncher.
"""
import argparse
import json
import runpy
import sys
from datetime import datetime, timezone
from pathlib import Path
from snu_bear_motion.contract import fingerprint, SKILLS

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("mode", choices=("train", "play"))
parser.add_argument("--isaac-lab", type=Path, required=True)
parser.add_argument("--skill", choices=SKILLS, required=True)
args, rest = parser.parse_known_args()
script = args.isaac_lab.resolve() / "scripts/reinforcement_learning/rsl_rl" / f"{args.mode}.py"
if not script.is_file():
    raise SystemExit(f"Official launcher not found: {script}. Supply your Isaac Lab v2.3.0 checkout.")
if "--task" in rest:
    raise SystemExit("Choose --skill; the wrapper sets the matching --task.")
import snu_bear_motion.isaaclab_tasks  # noqa: E402 -- Gym string registrations only

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
path = Path("run_metadata") / f"{args.skill}_{stamp}.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps({"created_utc": stamp, "skill": args.skill,
    "contract_sha256": fingerprint(), "arguments": rest,
    "target_version": "Isaac Lab 2.3.0", "mode": args.mode}, indent=2)+"\n")
print(f"Run contract: {path.resolve()}", flush=True)
sys.path.insert(0, str(script.parent))  # official scripts import sibling cli_args.py
sys.argv = [str(script), "--task", SKILLS[args.skill]["task_id"], *rest]
runpy.run_path(str(script), run_name="__main__")
