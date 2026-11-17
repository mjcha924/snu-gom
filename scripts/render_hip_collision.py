"""Render a labeled CAD inspection from recorded poses; never advance physics."""

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from runtime import ROOT, close_app, configure_asset_cache, configure_runtime
from audit_hip_clearance import link_geometry, pair_clearance


def main():
    kit_args = configure_runtime("hip_collision_closeup")
    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, default=ROOT / "docs/experiments/media/flat-recovery/contacts-trace.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", action="store_true")
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if any(not path.resolve().is_relative_to(ROOT) for path in [args.trace, args.output]):
        parser.error("Keep inputs and outputs in the workspace")
    args.headless = True
    args.enable_cameras = True
    args.kit_args = f"{kit_args} {args.kit_args}"
    launcher = AppLauncher(args)
    try:
        import imageio.v2 as imageio
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        from pxr import Gf, UsdGeom, UsdShade, Vt
        import torch
        import warp
        import isaaclab.sim as sim_utils
        from snu_gom_walk.env import GomEnv, GomEnvCfg, MODEL
        from snu_gom_walk.model import LEG_JOINTS, URDF, forward_kinematics
        import trimesh

        torch.set_num_threads(4)
        warp.config.kernel_cache_dir = str(ROOT / ".cache/warp")
        trace = json.loads(args.trace.read_text())
        if trace["model_hashes"] != MODEL["hashes"]:
            raise ValueError("Recorded poses and model must match")
        samples = np.array(trace["best_traces"]["4"])
        indices = [trace["trace_columns"].index(f"joint_position/{name}") for name in LEG_JOINTS]
        final_positions = dict(zip(LEG_JOINTS, samples[-1, indices]))
        swept_positions = {**final_positions, "left_hip_roll_joint": -0.25}
        robot_xml = ET.parse(URDF).getroot()
        links = ["left_hip_yaw_link", "left_thigh_link"]
        geometry = {kind: {name: link_geometry(robot_xml.find(f"link[@name='{name}']"), kind) for name in links} for kind in ["visual", "collision"]}
        measured = {kind: pair_clearance(geometry[kind], forward_kinematics(final_positions), links) for kind in geometry}
        swept = pair_clearance(geometry["visual"], forward_kinematics(swept_positions), links)
        if measured["visual"]["surface_intersection"] or not measured["collision"]["surface_intersection"] or not swept["surface_intersection"]:
            raise ValueError("Expected measured geometry cases changed; review captions before rendering")
        managers = []
        final_frames = forward_kinematics(final_positions)
        for name in links:
            manager = trimesh.collision.CollisionManager()
            for mesh_name, mesh in geometry["visual"][name]:
                manager.add_object(f"{name}/{mesh_name}", mesh, transform=final_frames[name])
            managers.append(manager)
        _, _, nearest = managers[0].min_distance_other(managers[1], return_names=True, return_data=True)
        focus = np.mean([nearest.point(name) for name in nearest.names], axis=0)
        lift = np.array([0.0, 0.0, 0.18])
        focus += lift

        cfg = GomEnvCfg()
        cfg.scene.num_envs = 1
        cfg.evaluation = True
        cfg.sim.device = args.device
        cfg.viewer.resolution = (960, 720)
        configure_asset_cache(cfg, MODEL)
        env = GomEnv(cfg, render_mode="rgb_array")
        env.reset()
        stage = env.scene.stage
        UsdGeom.Imageable(stage.GetPrimAtPath("/World/envs/env_0/Robot")).MakeInvisible()
        camera = UsdGeom.Camera.Get(stage, cfg.viewer.cam_prim_path)
        camera.CreateClippingRangeAttr(Gf.Vec2f(0.0001, 1000.0))
        materials = {}
        for name, color in [("motor", (0.95, 0.32, 0.04)), ("plate", (0.65, 0.04, 0.35)), ("context", (0.45, 0.52, 0.59)), ("wire", (0.0, 0.8, 1.0))]:
            path = f"/World/InspectionMaterials/{name}"
            material_cfg = sim_utils.PreviewSurfaceCfg(diffuse_color=color, roughness=0.75)
            material_cfg.func(path, material_cfg)
            materials[name] = UsdShade.Material.Get(stage, path)
        transforms = {}
        context_prims = []
        wire_prims = []
        selected_links = ["base_link", "left_hip_yaw_link", "left_hip_roll_link", "left_thigh_link", "left_shank_link", "left_foot_link"]
        for name in selected_links:
            path = f"/World/Inspection/{name}"
            body = UsdGeom.Xform.Define(stage, path)
            transforms[name] = body.AddTransformOp()
            visual = geometry["visual"].get(name)
            if visual is None:
                visual = link_geometry(robot_xml.find(f"link[@name='{name}']"), "visual")
            for index, (_, mesh) in enumerate(visual):
                shape = UsdGeom.Mesh.Define(stage, f"{path}/visual_{index}")
                shape.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(mesh.vertices.astype(np.float32)))
                shape.CreateFaceVertexCountsAttr([3] * len(mesh.faces))
                shape.CreateFaceVertexIndicesAttr(mesh.faces.reshape(-1).tolist())
                shape.CreateSubdivisionSchemeAttr("none")
                shape.CreateDoubleSidedAttr(True)
                material = "motor" if name == links[0] and index == 2 else "plate" if name == links[1] and index == 1 else "context"
                UsdShade.MaterialBindingAPI.Apply(shape.GetPrim()).Bind(materials[material])
                if material == "context":
                    context_prims.append(shape)
            if name in links:
                box_index = 0 if name == links[0] else 1
                box = geometry["collision"][name][box_index][1]
                edges = sorted({tuple(sorted(edge)) for boundary in box.facets_boundary for edge in boundary})
                points = box.vertices[np.array(edges).reshape(-1)]
                wire = UsdGeom.BasisCurves.Define(stage, f"{path}/collision_box_outline")
                wire.CreateTypeAttr("linear")
                wire.CreateCurveVertexCountsAttr([2] * len(edges))
                wire.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(points.astype(np.float32)))
                wire.CreateWidthsAttr([0.0001])
                wire.SetWidthsInterpolation("constant")
                UsdShade.MaterialBindingAPI.Apply(wire.GetPrim()).Bind(materials["wire"])
                wire_prims.append(wire)
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
        small_font = ImageFont.truetype("DejaVuSans.ttf", 17)
        args.output.mkdir(parents=True, exist_ok=True)
        duration = 22
        fps = 24
        times = [1.0, 11.0, 20.0] if args.preview else np.arange(duration * fps) / fps
        writer = None if args.preview else imageio.get_writer(args.output / "hip-collision-closeup.mp4", fps=fps)
        saved_frames = set()
        try:
            for video_time in times:
                if video_time < 3:
                    positions = dict(zip(LEG_JOINTS, samples[149, indices]))
                    title = "LEFT HIP ASSEMBLY | supplied CAD, highlighted contact pair"
                    detail = "Orange: hip-yaw motor housing. Magenta: thigh side plate."
                    scope = "Geometry inspection only | original STL and URDF unchanged"
                elif video_time < 13:
                    coordinate = np.clip((video_time - 3) / 7, 0, 1)
                    sample_index = 149 + coordinate * (len(samples) - 150)
                    lower = min(int(sample_index), len(samples) - 1)
                    upper = min(lower + 1, len(samples) - 1)
                    joints = (1 - sample_index % 1) * samples[lower, indices] + (sample_index % 1) * samples[upper, indices]
                    positions = dict(zip(LEG_JOINTS, joints))
                    title = "A | RECORDED POSES approaching the simulator contact"
                    detail = f"Recorded t={(sample_index + 1) * trace['trace_dt']:.2f}s | hip roll={np.degrees(joints[1]):.2f} deg"
                    scope = "Cyan wires: collision boxes | yellow ring: clearance region"
                    if video_time >= 10:
                        detail = f"At t=3.78s: boxes touch; CAD surfaces still {measured['visual']['minimum_surface_distance_m'] * 1000:.3f} mm apart"
                else:
                    coordinate = np.clip((video_time - 13) / 5, 0, 1)
                    positions = {**final_positions, "left_hip_roll_joint": (1 - coordinate) * final_positions["left_hip_roll_joint"] + coordinate * -0.25}
                    title = "B | CAD-ONLY ANGLE SWEEP beyond the stopped simulation"
                    detail = f"Inward hip roll={np.degrees(positions['left_hip_roll_joint']):.2f} deg | no physics or training"
                    scope = "Hypothetical pose inspection; NOT footage of the robot reaching this pose"
                    if video_time >= 18:
                        detail = "At -14.32 deg: supplied motor and side-plate meshes INTERSECT"
                        scope = "Review clearance or avoid this range; do not just disable collisions"
                for shape in context_prims:
                    shape.MakeVisible() if video_time < 3 else shape.MakeInvisible()
                for shape in wire_prims:
                    shape.MakeVisible() if 3 <= video_time < 13 else shape.MakeInvisible()
                body_frames = forward_kinematics(positions)
                for name, operation in transforms.items():
                    matrix = body_frames[name].copy()
                    matrix[:3, 3] += lift
                    operation.Set(Gf.Matrix4d(matrix.T.tolist()))
                camera_offset = np.array([0.18, 0.10, 0.06]) if video_time < 3 else np.array([-0.060, 0.0, 0.0])
                lookat = focus + (np.array([0.0, 0.0, -0.012]) if video_time < 3 else 0)
                env.sim.set_camera_view(tuple(lookat + camera_offset), tuple(lookat))
                if video_time == times[0]:
                    env.render()
                for _ in range(30 if video_time == times[0] else 3 if video_time in [3, 13] else 1):
                    env.sim.render()
                frame = Image.fromarray(env.render())
                if video_time >= 3:
                    detail_image = frame.crop((420, 300, 540, 420)).resize((300, 300))
                    frame.paste(detail_image, (640, 365))
                draw = ImageDraw.Draw(frame)
                if video_time >= 3:
                    draw.ellipse((430, 310, 530, 410), outline=(255, 220, 0), width=3)
                    draw.rectangle((638, 337, 942, 667), outline=(255, 220, 0), width=2)
                    draw.rectangle((640, 339, 940, 365), fill=(20, 27, 39))
                    draw.text((648, 342), "2.5x detail (same frame)", font=small_font, fill="white")
                draw.rectangle((0, 0, 960, 98), fill=(20, 27, 39))
                draw.text((16, 10), title, font=font, fill="white")
                draw.text((16, 43), detail, font=small_font, fill=(255, 210, 150))
                draw.text((16, 72), scope, font=small_font, fill=(205, 225, 241))
                draw.rectangle((0, 680, 960, 720), fill=(20, 27, 39))
                draw.text((16, 689), "Isolated CAD components | orange = motor | magenta = thigh plate | no geometry edits", font=small_font, fill="white")
                frame_array = np.array(frame)
                if writer:
                    writer.append_data(frame_array)
                section = "context" if video_time < 3 else "simulation-contact" if video_time < 13 else "cad-interference"
                if (args.preview or video_time in [1, 11, 20]) and section not in saved_frames:
                    imageio.imwrite(args.output / f"{section}.png", frame_array)
                    saved_frames.add(section)
        finally:
            if writer:
                writer.close()
        report = {
            "kind": "CAD pose inspection, not a physical rollout or walking demonstration",
            "physics_steps_after_initialization": 0, "optimizer_updates": 0,
            "input_trace_sha256": hashlib.sha256(args.trace.read_bytes()).hexdigest(),
            "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "model_hashes": MODEL["hashes"], "candidate": 4,
            "recorded_end_time_s": len(samples) * trace["trace_dt"],
            "recorded_end_joint_positions": final_positions,
            "recorded_end_geometry": measured, "hypothetical_sweep_joint_positions": swept_positions,
            "hypothetical_sweep_geometry": swept, "focus_world_m": focus.tolist(),
            "scope": "Recorded joint poses reconstructed at a fixed root for clear inspection, followed by an explicitly labeled hypothetical hip-angle sweep; meshes and collision boxes are unchanged",
        }
        (args.output / "inspection.json").write_text(json.dumps(report, indent=2) + "\n")
        print(args.output, flush=True)
    finally:
        close_app(launcher)


if __name__ == "__main__":
    main()
