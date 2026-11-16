"""Generate and audit a kinematic seed without starting Isaac."""

import argparse
import json

from runtime import ROOT
from snu_gom_walk.reference import build_reference


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", type=float, default=4.0)
    parser.add_argument("--speed", type=float, default=0.01)
    parser.add_argument("--clearance", type=float, default=0.005)
    parser.add_argument("--lean", type=float, default=0.20)
    args = parser.parse_args()
    report = build_reference(period=args.period, speed=args.speed, clearance=args.clearance, lean=args.lean)
    output = ROOT / "reports/reference.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key not in ["rows", "model_hashes"]}, indent=2))


if __name__ == "__main__":
    main()
