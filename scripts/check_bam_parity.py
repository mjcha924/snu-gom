"""Compare the experimental adapter's equations with pinned upstream BAM."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from runtime import ROOT
from snu_gom_walk.bam import BAM_COMMIT, load_profile, motor_torque, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True)
    args = parser.parse_args()
    upstream = args.upstream.resolve()
    if not upstream.is_relative_to(ROOT):
        parser.error("Keep the comparison checkout inside the workspace")
    revision = subprocess.check_output(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(upstream), "status", "--porcelain"], text=True).strip()
    if revision != BAM_COMMIT or dirty:
        raise ValueError("Expected a clean pinned upstream checkout")
    sys.path.insert(0, str(upstream))
    import numpy as np
    import torch
    from bam.model import load_model

    path = upstream / "bam/params/xl330/m1.json"
    parameters = load_profile(path)
    model = load_model(str(path))
    model.actuator.vin = 5.0
    model.actuator.kp = 400
    random = np.random.default_rng(42)
    target, position, velocity = random.normal(size=(3, 64, 8))
    control = model.actuator.compute_control(target, position, velocity, 0.002)
    expected = model.actuator.compute_torque(control, True, position, velocity)
    actual = motor_torque(*(torch.tensor(value) for value in [target, position, velocity]), parameters, 5.0, 400)
    np.testing.assert_allclose(actual.numpy(), expected, atol=1e-12, rtol=1e-12)
    friction, damping = model.compute_frictions(expected, random.normal(size=(64, 8)), velocity)
    assert friction == parameters["friction_base"]
    assert damping == parameters["friction_viscous"]
    assert model.actuator.get_extra_inertia() == parameters["armature"]
    report = {
        **provenance(), "electrical_parity_passed": True, "friction_parameter_parity_passed": True,
        "armature_parity_passed": True, "max_torque_difference_nm": float(np.abs(expected - actual.numpy()).max()),
        "samples": 512, "scope": "Equation/parameter parity only, not cross-engine dynamics or hardware validation",
    }
    output = ROOT / "reports/bam-parity.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
