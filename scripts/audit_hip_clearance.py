"""Compare hip/thigh box proxies and supplied visual meshes at recorded poses."""

import argparse
import importlib.metadata
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from runtime import ROOT

sys.path.insert(0, str(ROOT / ".deps/collision-audit"))

import trimesh

from snu_gom_walk.model import LEG_JOINTS, URDF, audit_model, forward_kinematics, origin_matrix, stance_configuration


def link_geometry(link, kind):
    result = []
    for index, element in enumerate(link.findall(kind)):
        if kind == "visual":
            description = element.find("geometry/mesh")
            path = (URDF.parent / description.get("filename")).resolve()
            mesh = trimesh.load_mesh(path)
            mesh.apply_scale(np.fromstring(description.get("scale", "1 1 1"), sep=" "))
            name = f"{index}/{path.name}"
        else:
            size = np.fromstring(element.find("geometry/box").get("size"), sep=" ")
            mesh = trimesh.creation.box(extents=size)
            name = f"box_{index}"
        mesh.apply_transform(origin_matrix(element))
        result.append((name, mesh))
    return result


def pair_clearance(geometries, frames, links):
    managers = []
    for link in links:
        manager = trimesh.collision.CollisionManager()
        for name, mesh in geometries[link]:
            manager.add_object(f"{link}/{name}", mesh, transform=frames[link])
        managers.append(manager)
    collision, pairs = managers[0].in_collision_other(managers[1], return_names=True)
    if collision:
        distance, nearest = 0.0, sorted(pairs)[0]
    else:
        distance, nearest = managers[0].min_distance_other(managers[1], return_names=True)
    return {"surface_intersection": bool(collision), "intersecting_pairs": sorted(pairs), "minimum_surface_distance_m": float(distance), "nearest_pair": nearest}


def scan_clearance(root, model):
    neutral = stance_configuration(0.1, model)[0]
    rows = []
    for side in ["left", "right"]:
        links = [f"{side}_hip_yaw_link", f"{side}_thigh_link"]
        geometries = {name: link_geometry(root.find(f"link[@name='{name}']"), "visual") for name in links}
        for roll in [-0.35, -0.30, -0.25, -0.20, 0.20, 0.25, 0.30, 0.35]:
            for pitch in [-0.15, 0.0, 0.15, 0.30, 0.45]:
                positions = neutral.copy()
                positions[f"{side}_hip_roll_joint"] = roll
                positions[f"{side}_hip_pitch_joint"] = pitch
                rows.append({"side": side, "roll": roll, "pitch": pitch, **pair_clearance(geometries, forward_kinematics(positions), links)})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--candidate", default="4")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scan", action="store_true", help="Also scan 80 hip poses; can take several minutes")
    args = parser.parse_args()
    if any(not path.resolve().is_relative_to(ROOT) for path in [args.trace, args.output]):
        parser.error("Keep inputs and outputs in the workspace")
    report = json.loads(args.trace.read_text())
    model = audit_model()
    if report["model_hashes"] != model["hashes"]:
        raise ValueError("Trace/model mismatch")
    samples = report["best_traces"][args.candidate]
    indices = [report["trace_columns"].index(f"joint_position/{joint}") for joint in LEG_JOINTS]
    links = ["left_hip_yaw_link", "left_thigh_link"]
    root = ET.parse(URDF).getroot()
    geometries = {kind: {name: link_geometry(root.find(f"link[@name='{name}']"), kind) for name in links} for kind in ["collision", "visual"]}
    rows = []
    for sample_index in sorted(set([min(139, len(samples) - 1), max(0, len(samples) - 15), len(samples) - 1])):
        positions = dict(zip(LEG_JOINTS, np.array(samples[sample_index])[indices].tolist()))
        frames = forward_kinematics(positions)
        rows.append({
            "time": (sample_index + 1) * report["trace_dt"], "joint_positions": positions,
            **{kind: pair_clearance(geometries[kind], frames, links) for kind in geometries},
        })
    output = {
        "trace": str(args.trace), "candidate": args.candidate, "model_hashes": model["hashes"],
        "versions": {name: importlib.metadata.version(name) for name in ["trimesh", "python-fcl"]},
        "rows": rows,
        "scope": "CPU surface-intersection/distance queries on supplied visual triangle meshes and box proxies, at recorded joint poses; not a manufacturing tolerance or hardware clearance certification",
    }
    if args.scan:
        output["static_scan"] = scan_clearance(root, model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
