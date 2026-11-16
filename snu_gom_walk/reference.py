"""Robot-specific kinematic stepping seed; not a dynamic walking controller."""

import math
import xml.etree.ElementTree as ET

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from .model import FOOT_LINKS, LEG_JOINTS, URDF, audit_model, origin_matrix, stance_configuration


class KinematicModel:
    def __init__(self):
        robot = ET.parse(URDF).getroot()
        pending = list(robot.findall("joint"))
        available = {"base_reference"}
        self.joints = []
        while pending:
            progressed = False
            for joint in pending[:]:
                parent = joint.find("parent").get("link")
                child = joint.find("child").get("link")
                if parent not in available:
                    continue
                axis_element = joint.find("axis")
                axis = np.fromstring(axis_element.get("xyz"), sep=" ") if axis_element is not None else np.zeros(3)
                if np.linalg.norm(axis) > 0:
                    axis /= np.linalg.norm(axis)
                self.joints.append((joint.get("name"), parent, child, origin_matrix(joint), axis))
                pending.remove(joint)
                available.add(child)
                progressed = True
            if not progressed:
                raise ValueError("Disconnected or cyclic robot")
        self.inertials = []
        for link in robot.findall("link"):
            inertial = link.find("inertial")
            if inertial is not None:
                self.inertials.append((link.get("name"), float(inertial.find("mass").get("value")), origin_matrix(inertial)[:3, 3]))

    def frames(self, positions):
        frames = {"base_reference": np.eye(4)}
        for name, parent, child, origin, axis in self.joints:
            motion = np.eye(4)
            motion[:3, :3] = Rotation.from_rotvec(axis * positions.get(name, 0.0)).as_matrix()
            frames[child] = frames[parent] @ origin @ motion
        return frames

    def center_of_mass(self, frames):
        total = sum(mass for _, mass, _ in self.inertials)
        return sum(mass * (frames[name][:3, :3] @ local + frames[name][:3, 3]) for name, mass, local in self.inertials) / total


def build_reference(samples=80, period=4.0, speed=0.01, clearance=0.005, lean=0.20):
    if samples < 16 or period <= 0 or speed < 0 or clearance < 0 or not 0 <= lean <= 0.32:
        raise ValueError("Invalid reference configuration")
    model = audit_model()
    kinematics = KinematicModel()
    neutral, height, centers = stance_configuration(0.30, model)
    initial_frames = kinematics.frames(neutral)
    corners = {name: np.array(model["foot_corners"][name]) for name in FOOT_LINKS}
    local_centers = {name: corners[name].mean(axis=0) for name in FOOT_LINKS}
    initial_soles = {
        name: (corners[name] @ initial_frames[name][:3, :3].T + initial_frames[name][:3, 3])[:, 2].min()
        for name in FOOT_LINKS
    }
    lower = np.array([model["joints"][name]["lower"] * 0.98 for name in LEG_JOINTS] + [-0.04, height - 0.03])
    upper = np.array([model["joints"][name]["upper"] * 0.98 for name in LEG_JOINTS] + [0.04, height + 0.02])
    lower[LEG_JOINTS.index("left_knee_pitch_joint")] = 0.08
    upper[LEG_JOINTS.index("right_knee_pitch_joint")] = -0.08
    solution = np.array([neutral[name] for name in LEG_JOINTS] + [0.0, height])
    rows = []
    for phase in np.arange(samples) / samples:
        root_roll = lean * np.tanh(2 * np.sin(2 * np.pi * (phase - 0.025))) / np.tanh(2)
        root_rotation = Rotation.from_euler("x", root_roll).as_matrix()
        goals = []
        swings = []
        for foot_index, name in enumerate(FOOT_LINKS):
            local_phase = (phase - [0.10, 0.60][foot_index]) % 1
            progress = np.clip(local_phase / 0.35, 0, 1)
            swing = local_phase < 0.35
            half_excursion = speed * period * 0.65 / 2
            horizontal = half_excursion * (2 * progress ** 2 * (3 - 2 * progress) - 1) if swing else half_excursion * (1 - 2 * (local_phase - 0.35) / 0.65)
            lift = clearance * math.sin(math.pi * progress) ** 2 if swing else 0.0
            goals.append(np.array(centers[name]) + [horizontal, 0, -initial_soles[name] + lift])
            swings.append(bool(swing))

        def residual(values):
            frames = kinematics.frames(dict(zip(LEG_JOINTS, values[:10])))
            translation = np.array([0, values[10], values[11]])
            errors = []
            for foot_index, name in enumerate(FOOT_LINKS):
                rotation = root_rotation @ frames[name][:3, :3]
                center = root_rotation @ (frames[name][:3, :3] @ local_centers[name] + frames[name][:3, 3]) + translation
                errors.extend((center - goals[foot_index]) / 0.02)
                errors.extend(Rotation.from_matrix(rotation @ initial_frames[name][:3, :3].T).as_rotvec() / 0.3)
            errors.append((values[11] - 0.156) / 0.005)
            errors.extend(0.02 * (values[:10] - np.array([neutral[name] for name in LEG_JOINTS])))
            return errors

        result = least_squares(residual, solution, bounds=(lower, upper), max_nfev=80, ftol=1e-9, xtol=1e-9, gtol=1e-9)
        solution = result.x
        frames = kinematics.frames(dict(zip(LEG_JOINTS, solution[:10])))
        translation = np.array([0, solution[10], solution[11]])
        world_corners = [corners[name] @ (root_rotation @ frames[name][:3, :3]).T + root_rotation @ frames[name][:3, 3] + translation for name in FOOT_LINKS]
        com = root_rotation @ kinematics.center_of_mass(frames) + translation
        rows.append({
            "phase": float(phase), "joints": solution[:10].tolist(),
            "root_pose": [0.0, float(solution[10]), float(solution[11]), float(root_roll)],
            "position_error_m": float(np.abs(np.array(residual(solution))[:12].reshape(2, 6)[:, :3]).max() * 0.02),
            "rotation_error_rad": float(np.abs(np.array(residual(solution))[:12].reshape(2, 6)[:, 3:]).max() * 0.3),
            "sole_heights": [float(foot[:, 2].min()) for foot in world_corners],
            "support_margin_y": [float(min(com[1] - foot[:, 1].min(), foot[:, 1].max() - com[1])) for foot in world_corners],
            "swing": swings,
        })
    joint_table = np.array([row["joints"] for row in rows])
    velocities = (np.roll(joint_table, -1, axis=0) - joint_table) * samples / period
    return {
        "kind": "kinematic_seed_not_validated_walking", "period": period, "speed": speed,
        "clearance": clearance, "lean": lean, "joint_order": LEG_JOINTS,
        "model_hashes": model["hashes"], "rows": rows,
        "max_position_error_m": max(row["position_error_m"] for row in rows),
        "max_rotation_error_rad": max(row["rotation_error_rad"] for row in rows),
        "peak_reference_speed": float(np.abs(velocities).max()),
        "velocity_limits_passed": bool((np.abs(velocities) <= np.array([model["joints"][name]["velocity"] for name in LEG_JOINTS]) + 1e-6).all()),
    }
