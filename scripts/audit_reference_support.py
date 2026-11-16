"""Audit ideal quasi-static vertical support; not a dynamic feasibility proof."""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.spatial.transform import Rotation

from runtime import ROOT
from snu_gom_walk.model import FOOT_LINKS, LEG_JOINTS, audit_model
from snu_gom_walk.reference import KinematicModel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    args = parser.parse_args()
    reference_path = args.reference.resolve()
    if not reference_path.is_relative_to(ROOT):
        parser.error("Input/output must stay inside the workspace")
    reference = json.loads(reference_path.read_text())
    model = audit_model()
    if reference["model_hashes"] != model["hashes"]:
        raise ValueError("Reference/model hash mismatch")
    kinematics = KinematicModel()
    effort = np.array([model["joints"][name]["effort"] for name in LEG_JOINTS])
    results = []
    for row in reference["rows"][::4]:
        rotation = np.array(row["root_rotation"]) if "root_rotation" in row else Rotation.from_euler("x", row["root_pose"][3]).as_matrix()
        translation = np.array(row["root_pose"][:3])
        positions = np.array(row["joints"])
        stance = [index for index, swing in enumerate(row["swing"]) if not swing]

        def geometry(values):
            frames = kinematics.frames(dict(zip(LEG_JOINTS, values)))
            com = rotation @ kinematics.center_of_mass(frames) + translation
            points = []
            for index in stance:
                name = FOOT_LINKS[index]
                corners = np.array(model["foot_corners"][name])
                world = corners @ (rotation @ frames[name][:3, :3]).T + rotation @ frames[name][:3, 3] + translation
                points.extend(world[np.sort(np.argsort(world[:, 2])[:4])])
            return com, np.array(points)

        com, points = geometry(positions)
        com_jacobian = np.empty(10)
        contact_jacobian = np.empty((len(points), 10))
        for index in range(10):
            delta = np.zeros(10)
            delta[index] = 1e-5
            plus_com, plus_points = geometry(positions + delta)
            minus_com, minus_points = geometry(positions - delta)
            com_jacobian[index] = (plus_com[2] - minus_com[2]) / 2e-5
            contact_jacobian[:, index] = (plus_points[:, 2] - minus_points[:, 2]) / 2e-5
        weight = model["mass_kg"] * 9.81
        gravity = weight * com_jacobian
        equalities = np.vstack((np.ones(len(points)), points[:, 0], points[:, 1]))
        solution = linprog(
            np.r_[np.zeros(len(points)), 1],
            A_ub=np.vstack((np.c_[-contact_jacobian.T, -effort], np.c_[contact_jacobian.T, -effort])),
            b_ub=np.r_[-gravity, gravity],
            A_eq=np.c_[equalities, np.zeros(3)], b_eq=weight * np.r_[1, com[:2]],
            bounds=[(0, None)] * (len(points) + 1), method="highs",
        )
        results.append({
            "phase": row["phase"], "stance_feet": stance,
            "vertical_static_support_possible": bool(solution.success),
            "minimum_peak_effort_fraction": float(solution.x[-1]) if solution.success else None,
            "joint_torques_at_optimum": dict(zip(LEG_JOINTS, (gravity - contact_jacobian.T @ solution.x[:-1]).tolist())) if solution.success else None,
        })
    report = {
        "scope": "Ideal vertical corner forces and static gravity only; no acceleration, frictional wrench, compliance, or collision clearance proof",
        "rows": results,
        "supported_within_effort_limits": sum(row["vertical_static_support_possible"] and row["minimum_peak_effort_fraction"] <= 1 for row in results),
        "sampled_phases": len(results),
    }
    output = reference_path.with_name("reference-support.json")
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
