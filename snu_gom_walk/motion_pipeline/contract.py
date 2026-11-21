"""Portable NPZ contract, shared by CPU validation and the training loader.

This module needs NumPy/SciPy only. It checks structure before geometry or
controller code sees a clip; it does not certify physical feasibility.
"""

import numpy as np


def validate_contract(arrays, joint_names, model_id):
    """Reject ambiguous units, missing fields and unsupported contact schedules."""
    shapes = {
        "time": (None,),
        "fps": (),
        "model_id": (),
        "quaternion_order": (),
        "joint_names": (len(joint_names),),
        "sole_points_link": (2, 3),
        "joints_pos": (None, len(joint_names)),
        "joints_vel": (None, len(joint_names)),
        "root_pos": (None, 3),
        "root_quat": (None, 4),
        "world_linear_vel": (None, 3),
        "world_angular_vel": (None, 3),
        "foot_positions_world": (None, 2, 3),
        "foot_positions_body": (None, 2, 3),
        "target_foot_positions_world": (None, 2, 3),
        "target_sole_height_m": (None, 2),
        "com_world": (None, 3),
        "target_com_world": (None, 3),
        "planned_contacts": (None, 2),
        "phase": (None,),
    }
    missing = sorted(set(shapes) - set(arrays))
    if missing:
        raise ValueError("Missing reference fields: " + ", ".join(missing))
    if arrays["time"].ndim != 1 or len(arrays["time"]) < 3:
        raise ValueError("Malformed reference time: at least three frames required")
    n = len(arrays["time"])
    for key, shape in shapes.items():
        expected = tuple(n if value is None else value for value in shape)
        if arrays[key].shape != expected:
            raise ValueError(
                f"Malformed reference shape for {key}: expected {expected}"
            )
    numeric = set(shapes) - {"model_id", "joint_names", "quaternion_order"}
    for key in numeric:
        if not np.issubdtype(arrays[key].dtype, np.number):
            raise ValueError("Expected numeric reference field: " + key)
    for key, value in arrays.items():
        if np.issubdtype(value.dtype, np.number) and not np.isfinite(value).all():
            raise ValueError("Nonfinite reference rejected before physics: " + key)
    optional = {
        "joints_acc": (n, len(joint_names)),
        "com_velocity_world": (n, 3),
        "com_acceleration_world": (n, 3),
        "foot_velocities_world": (n, 2, 3),
        "foot_accelerations_world": (n, 2, 3),
    }
    for key, shape in optional.items():
        if key in arrays and arrays[key].shape != shape:
            raise ValueError("Malformed reference shape for " + key)
    fps = float(arrays["fps"])
    time = arrays["time"]
    if (
        fps <= 0
        or not np.isclose(time[0], 0.0, atol=1e-10)
        or not np.allclose(np.diff(time), 1 / fps, atol=1e-8, rtol=1e-6)
    ):
        raise ValueError(
            "Reference time must start at zero and increase uniformly at positive fps"
        )
    if str(arrays["model_id"]) != model_id or arrays["joint_names"].tolist() != list(
        joint_names
    ):
        raise ValueError("Motion joint/model contract mismatch")
    if str(arrays["quaternion_order"]) != "xyzw":
        raise ValueError("NPZ quaternion_order must be xyzw")
    if not np.allclose(np.linalg.norm(arrays["root_quat"], axis=1), 1.0, atol=1e-6):
        raise ValueError("Reference requires unit quaternions")
    contacts = arrays["planned_contacts"]
    if not np.isin(contacts, [0, 1]).all() or not (contacts.sum(axis=1) >= 1).all():
        raise ValueError(
            "Contacts must be binary with at least one stance foot per frame; flight is unsupported"
        )


def validate_training_adapter(robot):
    """Fail before Isaac starts when the existing GOM adapter needs an update."""
    from snu_gom_walk.model import ALL_JOINTS
    from .model import origin

    if set(robot.names) != set(ALL_JOINTS):
        raise ValueError("Current Isaac adapter requires the SNU GOM 12-joint contract")
    if robot.profile["root_link"] != "base_reference" or robot.feet != [
        "left_foot_link",
        "right_foot_link",
    ]:
        raise ValueError("Changed root/foot roles require an Isaac adapter update")
    fixed = next(
        (
            joint
            for joint in robot.robot.findall("joint")
            if joint.find("parent").get("link") == "base_reference"
            and joint.find("child").get("link") == "base_link"
        ),
        None,
    )
    if (
        fixed is None
        or fixed.get("type") != "fixed"
        or not np.allclose(origin(fixed), np.eye(4), atol=1e-9)
    ):
        raise ValueError("Changed root datum requires an Isaac adapter update")
    if any(joint.get("type") not in ("fixed", "revolute") for joint in robot.tree):
        raise ValueError("Current Isaac adapter supports fixed/revolute joints only")
