"""Shared reference-planning envelope, distinct from a continuous motor rating."""

import numpy as np


def motor_rows(profile, names):
    motors = profile["motors"]
    if not set(motors.get("overrides", {})) <= set(names):
        raise ValueError("Unknown joint in motor overrides")
    return [
        dict(motors["default"], **motors.get("overrides", {}).get(n, {})) for n in names
    ]


def motor_curve(row):
    """Validate a full loaded curve; its endpoints must include zero speed/torque.

    Missing curves use the explicitly provisional linear stall/no-load model.
    A partial measured curve must be completed deliberately in the profile.
    """
    supplied = ("curve_speed_rpm" in row, "curve_torque_nm" in row)
    if any(supplied) and not all(supplied):
        raise ValueError("Motor curve requires both speed and torque samples")
    speeds = (
        np.asarray(
            row.get("curve_speed_rpm", [0, row["no_load_rad_s"] * 30 / np.pi]),
            dtype=float,
        )
        * np.pi
        / 30
    )
    torques = np.asarray(
        row.get("curve_torque_nm", [row["stall_nm"], 0.0]), dtype=float
    )
    if (
        speeds.ndim != 1
        or torques.shape != speeds.shape
        or len(speeds) < 2
        or not np.isfinite(speeds).all()
        or not np.isfinite(torques).all()
    ):
        raise ValueError(
            "Motor curve must contain matching finite one-dimensional samples"
        )
    if (
        speeds[0] != 0
        or torques[-1] != 0
        or (torques < 0).any()
        or not (np.diff(speeds) > 0).all()
        or not (np.diff(torques) <= 0).all()
    ):
        raise ValueError(
            "Motor curve needs increasing speeds from zero, decreasing nonnegative torques ending at zero"
        )
    return speeds, torques


def limits(profile, names, urdf_effort, urdf_speed):
    rows = motor_rows(profile, names)
    settings = profile["motors"]
    stall = np.array([r["stall_nm"] for r in rows])
    no_load = np.array([r["no_load_rad_s"] for r in rows])
    fraction = float(
        settings.get(
            "planning_stall_fraction",
            profile.get("physics", {}).get("stall_fraction", 0.6),
        )
    )
    speed_fraction = float(settings.get("planning_speed_fraction", 1.0))
    if (
        not (0 < fraction <= 1 and 0 < speed_fraction <= 1)
        or not np.isfinite([stall, no_load]).all()
        or min(stall.min(), no_load.min()) <= 0
    ):
        raise ValueError("Invalid motor planning envelope")
    for row in rows:
        motor_curve(row)
    effort = stall * fraction
    speed = no_load * speed_fraction
    if not settings.get("override_provisional_urdf_effort_velocity", False):
        effort = np.minimum(effort, urdf_effort)
        speed = np.minimum(speed, urdf_speed)
    return effort, speed


def torque_envelope(profile, names, velocity, effort):
    """Symmetric motoring bound; conservative for regenerative/braking quadrants.

    XC curve is manually read from ROBOTIS's graph, not measured on this robot.
    Loaded curves include zero-speed and zero-torque endpoints. Beyond the last
    speed the cap is zero. This is still not a thermal model.
    """
    rows = motor_rows(profile, names)
    v = np.abs(np.asarray(velocity))
    caps = []
    for i, row in enumerate(rows):
        bound = row["stall_nm"] * max(0.0, 1 - v[i] / row["no_load_rad_s"])
        if "curve_speed_rpm" in row:
            speeds, torques = motor_curve(row)
            bound = min(
                bound,
                float(np.interp(v[i], speeds, torques, left=torques[0], right=0.0)),
            )
        caps.append(min(float(effort[i]), bound))
    return np.array(caps)


def torch_curve_cap(velocity, speeds, torques):
    """Vectorized piecewise interpolation shared by CPU tests and Isaac runtime."""
    import torch

    v = velocity.abs()
    x = speeds.expand(*v.shape, speeds.shape[-1])
    y = torques.expand_as(x)
    index = ((v[..., None] >= x).sum(-1) - 1).clamp(0, x.shape[-1] - 2)[..., None]
    lo = x.gather(-1, index).squeeze(-1)
    hi = x.gather(-1, index + 1).squeeze(-1)
    yl = y.gather(-1, index).squeeze(-1)
    yh = y.gather(-1, index + 1).squeeze(-1)
    return torch.lerp(yl, yh, ((v - lo) / (hi - lo)).clamp(0, 1)).clamp_min(0)


def curve_arrays(profile, names):
    rows = motor_rows(profile, names)
    curves = []
    for row in rows:
        x, y = motor_curve(row)
        curves.append((x.tolist(), y.tolist()))
    width = max(len(x) for x, y in curves)
    return (
        np.array(
            [x + [x[-1] + i + 1 for i in range(width - len(x))] for x, y in curves]
        ),
        np.array([y + [0.0] * (width - len(y)) for x, y in curves]),
    )
