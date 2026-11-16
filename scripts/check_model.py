"""Compare imported PhysX kinematics and inertias against the source URDF."""

import argparse
import json
import xml.etree.ElementTree as ET

from runtime import ROOT, close_app, configure_asset_cache, configure_runtime


def main():
    kit_args = configure_runtime("model_check")
    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser()
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    args.headless = True
    args.kit_args = f"{kit_args} {args.kit_args}"
    launcher = AppLauncher(args)
    try:
        import numpy as np
        import torch
        from scipy.spatial.transform import Rotation
        from snu_gom_walk.env import GomEnv, GomEnvCfg, MODEL
        from snu_gom_walk.model import ALL_JOINTS, URDF, origin_matrix

        cfg = GomEnvCfg()
        cfg.evaluation = True
        cfg.scene.num_envs = 1
        configure_asset_cache(cfg, MODEL)
        env = GomEnv(cfg)
        env.reset()
        description = ET.parse(URDF).getroot()
        joints = description.findall("joint")
        positions = env.robot.data.default_joint_pos.clone()
        body_ids = {name: index for index, name in enumerate(env.robot.body_names)}
        joint_ids = {name: index for index, name in enumerate(env.robot.joint_names)}
        samples = [{}, *[{name: 0.05} for name in ALL_JOINTS]]
        rng = np.random.default_rng(42)
        samples += [{name: float(rng.uniform(-0.08, 0.08)) for name in ALL_JOINTS} for sample in range(8)]
        errors = []
        for angles in samples:
            positions.zero_()
            for name, angle in angles.items():
                positions[0, joint_ids[name]] = angle
            env.robot.write_joint_state_to_sim(positions, torch.zeros_like(positions))
            actual = env.robot.data.body_link_pose_w[0].cpu().numpy()
            frames = {"base_reference": np.eye(4)}
            frames["base_reference"][:3, 3] = env.robot.data.root_pos_w[0].cpu().numpy()
            for joint in joints:
                parent = joint.find("parent").get("link")
                child = joint.find("child").get("link")
                motion = np.eye(4)
                if joint.get("type") == "revolute":
                    axis = np.fromstring(joint.find("axis").get("xyz"), sep=" ")
                    axis /= np.linalg.norm(axis)
                    motion[:3, :3] = Rotation.from_rotvec(axis * angles.get(joint.get("name"), 0.0)).as_matrix()
                frames[child] = frames[parent] @ origin_matrix(joint) @ motion
            for name, body_id in body_ids.items():
                position_error = np.linalg.norm(actual[body_id, :3] - frames[name][:3, 3])
                rotation = Rotation.from_quat(actual[body_id, [4, 5, 6, 3]]).as_matrix()
                rotation_error = Rotation.from_matrix(rotation @ frames[name][:3, :3].T).magnitude()
                errors.append({"body": name, "position_m": float(position_error), "rotation_rad": float(rotation_error)})
        masses = env.robot.root_physx_view.get_masses()[0].cpu().numpy()
        tensors = env.robot.root_physx_view.get_inertias()[0].cpu().numpy().reshape(-1, 3, 3)
        centers = env.robot.root_physx_view.get_coms()[0].cpu().numpy()
        inertia_errors = {}
        tensor_errors = {}
        center_errors = {}
        for name, body_id in body_ids.items():
            source = "base_link" if name == "base_reference" else name
            expected = np.array(MODEL["inertias"][source]["principal_moments"])
            measured = np.linalg.eigvalsh(tensors[body_id])
            inertia_errors[name] = float(np.max(np.abs(measured - expected) / expected))
            np.testing.assert_allclose(masses[body_id], MODEL["body_masses"][source], rtol=1e-4)
            inertial = description.find(f"link[@name='{source}']/inertial")
            source_frame = origin_matrix(inertial)
            values = {key: float(value) for key, value in inertial.find("inertia").attrib.items()}
            source_tensor = np.array([
                [values["ixx"], values["ixy"], values["ixz"]],
                [values["ixy"], values["iyy"], values["iyz"]],
                [values["ixz"], values["iyz"], values["izz"]],
            ])
            source_tensor = source_frame[:3, :3] @ source_tensor @ source_frame[:3, :3].T
            actual_tensor = tensors[body_id]
            tensor_errors[name] = float(np.linalg.norm(actual_tensor - source_tensor) / np.linalg.norm(source_tensor))
            center_errors[name] = float(np.linalg.norm(centers[body_id, :3] - source_frame[:3, 3]))
        result = {
            "poses_checked": len(samples),
            "max_position_error_m": max(error["position_m"] for error in errors),
            "max_rotation_error_rad": max(error["rotation_rad"] for error in errors),
            "max_inertia_relative_error": max(inertia_errors.values()),
            "per_body_inertia_relative_error": inertia_errors,
            "max_full_tensor_relative_error": max(tensor_errors.values()),
            "max_center_of_mass_error_m": max(center_errors.values()),
            "per_body_full_tensor_relative_error": tensor_errors,
        }
        result["passed"] = (
            result["max_position_error_m"] < 1e-4
            and result["max_rotation_error_rad"] < 1e-3
            and result["max_inertia_relative_error"] < 0.01
            and result["max_full_tensor_relative_error"] < 0.01
            and result["max_center_of_mass_error_m"] < 1e-4
        )
        (ROOT / "reports/import_validation.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2), flush=True)
        assert result["passed"], "Imported physics differs from the URDF; inspect report before training"
    finally:
        close_app(launcher)


if __name__ == "__main__":
    main()
