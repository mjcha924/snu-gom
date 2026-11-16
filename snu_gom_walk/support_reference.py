"""Shallow support-leg reference; joint targets only, not balanced walking."""

import numpy as np
from scipy.spatial.transform import Rotation

from .model import FOOT_LINKS, LEG_JOINTS, audit_model, stance_configuration
from .reference import KinematicModel


def build_support_seed(samples=80, period=4.0, speed=0.01, lean=0.30):
    if not isinstance(samples, int) or samples < 4:
        raise ValueError("At least four samples are required")
    if not np.isfinite([period, speed, lean]).all() or period <= 0 or speed < 0 or lean < 0:
        raise ValueError("Period must be positive; speed and lean must be nonnegative and finite")
    model = audit_model()
    kinematics = KinematicModel()
    neutral, _, centers = stance_configuration(0.30, model)
    neutral_frames = kinematics.frames(neutral)
    rows = []
    for phase in np.arange(samples) / samples:
        root_roll = lean * np.tanh(2 * np.sin(2 * np.pi * (phase - 0.025))) / np.tanh(2)
        positions = neutral.copy()
        swings = []
        for foot_index, side in enumerate(["left", "right"]):
            local_phase = (phase - [0.10, 0.60][foot_index]) % 1
            progress = np.clip(local_phase / 0.35, 0, 1)
            swing = local_phase < 0.35
            half_excursion = speed * period * 0.65 / 2
            horizontal = half_excursion * (2 * progress ** 2 * (3 - 2 * progress) - 1) if swing else half_excursion * (1 - 2 * (local_phase - 0.35) / 0.65)
            knee = 0.30 + 0.25 * np.sin(np.pi * progress) ** 2 * swing
            pitch = knee / 2 + horizontal / 0.105
            positions[f"{side}_hip_roll_joint"] = -root_roll
            positions[f"{side}_hip_pitch_joint"] = pitch
            positions[f"{side}_knee_pitch_joint"] = knee * [1, -1][foot_index]
            positions[f"{side}_ankle_pitch_joint"] = pitch - knee
            swings.append(bool(swing))
        frames = kinematics.frames(positions)
        support = FOOT_LINKS[1 if root_roll >= 0 else 0]
        rotation = neutral_frames[support][:3, :3] @ frames[support][:3, :3].T
        support_corners = np.array(model["foot_corners"][support]) @ (rotation @ frames[support][:3, :3]).T + rotation @ frames[support][:3, 3]
        translation = np.array([0, centers[support][1] - support_corners[:, 1].mean(), -support_corners[:, 2].min()])
        world = [np.array(model["foot_corners"][name]) @ (rotation @ frames[name][:3, :3]).T + rotation @ frames[name][:3, 3] + translation for name in FOOT_LINKS]
        com = rotation @ kinematics.center_of_mass(frames) + translation
        rows.append({
            "phase": float(phase), "joints": [float(positions[name]) for name in LEG_JOINTS],
            "root_pose": [*translation.tolist(), float(Rotation.from_matrix(rotation).as_euler("xyz")[0])],
            "root_rotation": rotation.tolist(), "swing": swings,
            "foot_x_offsets": [float((frames[name][:3, :3] @ np.array(model["foot_corners"][name]).mean(axis=0) + frames[name][:3, 3])[0] - centers[name][0]) for name in FOOT_LINKS],
            "sole_heights": [float(corners[:, 2].min()) for corners in world],
            "support_margin_y": [float(min(com[1] - corners[:, 1].min(), corners[:, 1].max() - com[1])) for corners in world],
        })
    table = np.array([row["joints"] for row in rows])
    velocity = (np.roll(table, -1, axis=0) - table) * samples / period
    return {
        "kind": "shallow_support_seed_not_validated_walking", "period": period, "speed": speed,
        "lean": lean,
        "joint_order": LEG_JOINTS, "model_hashes": model["hashes"], "rows": rows,
        "peak_reference_speed": float(np.abs(velocity).max()),
        "velocity_limits_passed": bool((np.abs(velocity) <= np.array([model["joints"][name]["velocity"] for name in LEG_JOINTS])).all()),
        "position_limits_passed": all(bool(((table[:, index] >= model["joints"][name]["lower"]) & (table[:, index] <= model["joints"][name]["upper"])).all()) for index, name in enumerate(LEG_JOINTS)),
    }
