"""Write the shallow support-leg seed for standalone audits."""

import json

from runtime import ROOT
from snu_gom_walk.support_reference import build_support_seed


if __name__ == "__main__":
    report = build_support_seed()
    output = ROOT / "reports/support-seed.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key not in ["rows", "model_hashes"]}, indent=2))
