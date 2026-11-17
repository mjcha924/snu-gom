"""Screen hypothetical outward hip spacing; do not modify any supplied geometry."""

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from audit_hip_clearance import link_geometry
from runtime import ROOT
from snu_gom_walk.model import URDF, audit_model, forward_kinematics

import numpy as np
import trimesh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extensions-mm", type=float, nargs="+", default=[0, 3, 4, 5, 6, 8])
    parser.add_argument("--roll-step-deg", type=float, default=5)
    parser.add_argument("--pitch-step-deg", type=float, default=15)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT):
        parser.error("Keep outputs inside the workspace")
    if args.roll_step_deg <= 0 or args.pitch_step_deg <= 0 or min(args.extensions_mm) < 0:
        parser.error("Steps must be positive and extensions nonnegative")
    robot = ET.parse(URDF).getroot()
    rows = []
    for side, direction in [("left", 1), ("right", -1)]:
        links = [f"{side}_hip_yaw_link", f"{side}_thigh_link"]
        managers = []
        object_names = []
        for name in links:
            manager = trimesh.collision.CollisionManager()
            names = []
            for mesh_name, mesh in link_geometry(robot.find(f"link[@name='{name}']"), "visual"):
                object_name = f"{name}/{mesh_name}"
                manager.add_object(object_name, mesh)
                names.append(object_name)
            managers.append(manager)
            object_names.append(names)
        roll_angles = np.unique(np.r_[np.arange(-20, 20, args.roll_step_deg), 20.0])
        pitch_angles = np.unique(np.r_[np.arange(-45, 45, args.pitch_step_deg), 45.0])
        for roll_deg in roll_angles:
            for pitch_deg in pitch_angles:
                frames = forward_kinematics({
                    f"{side}_hip_roll_joint": np.deg2rad(roll_deg),
                    f"{side}_hip_pitch_joint": np.deg2rad(pitch_deg),
                })
                outward = frames[f"{side}_hip_roll_link"][:3, :3] @ np.array([direction, 0, 0])
                for extension in args.extensions_mm:
                    for index, name in enumerate(links):
                        transform = frames[name].copy()
                        if index == 1:
                            transform[:3, 3] += outward * extension / 1000
                        for mesh_name in object_names[index]:
                            managers[index].set_transform(mesh_name, transform)
                    intersects, pairs = managers[0].in_collision_other(managers[1], return_names=True)
                    if intersects:
                        clearance, nearest = 0.0, sorted(pairs)[0]
                    else:
                        clearance, nearest = managers[0].min_distance_other(managers[1], return_names=True)
                    rows.append({
                        "side": side, "roll_deg": float(roll_deg), "pitch_deg": float(pitch_deg),
                        "extension_mm": extension, "intersects": bool(intersects),
                        "clearance_mm": float(clearance * 1000), "nearest_pair": nearest,
                    })
        print(f"Finished {side}", flush=True)
    summaries = []
    for extension in args.extensions_mm:
        for envelope in [15, 20]:
            selected = [row for row in rows if row["extension_mm"] == extension and abs(row["roll_deg"]) <= envelope]
            worst = min(selected, key=lambda row: row["clearance_mm"])
            summaries.append({
                "extension_mm": extension, "roll_envelope_deg": envelope,
                "sample_count": len(selected), "intersecting_samples": sum(row["intersects"] for row in selected),
                "worst_sample": worst,
            })
    result = {
        "model_hashes": audit_model()["hashes"],
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "assumption": "Translate the thigh assembly along hip-roll local +X on the left and -X on the right; this moves it outward at neutral and rotates with hip roll. No files or meshes changed.",
        "scope": "Visual surface queries between hip-yaw and thigh assemblies only, at discrete poses. Does not model the redesigned bracket or validate other pairs, strength, stiffness, wiring, tolerances, actuator loads, or walking.",
        "roll_step_deg": args.roll_step_deg, "pitch_step_deg": args.pitch_step_deg,
        "summary": summaries, "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summaries, indent=2), flush=True)


if __name__ == "__main__":
    main()
