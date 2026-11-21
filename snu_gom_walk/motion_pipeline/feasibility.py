"""Inverse-dynamics reference screen, independent of a tracking controller.

All frames use floating-base equations and unilateral friction-limited point
forces over the *outer* projected stance soles. This is deliberately optimistic:
failure of a tracker is not a motor failure, and passing this screen does not
certify the narrower instantaneous rolling contact patch or hardware thermals.
"""

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull

from .motors import torque_envelope


def screen_reference(robot, a):
    import mujoco

    m = robot.model
    d = mujoco.MjData(m)
    n = len(a["time"])
    N = len(robot.names)
    dt = 1 / float(a["fps"])
    poses = np.repeat(m.qpos0[None], n, axis=0)
    poses[:, :3] = a["root_pos"]
    poses[:, 3:7] = a["root_quat"][:, [3, 0, 1, 2]]
    poses[:, robot.qi] = a["joints_pos"]
    velocity = np.zeros((n, m.nv))
    for i in range(n):
        lo = max(i - 1, 0)
        hi = min(i + 1, n - 1)
        mujoco.mj_differentiatePos(m, velocity[i], (hi - lo) * dt, poses[lo], poses[hi])
    acceleration = np.gradient(velocity, dt, axis=0, edge_order=2)
    utilization = []
    balance_unresolved = []
    torques = []
    residuals = []
    statuses = []
    solver_retries = []
    S = np.eye(m.nv)[:, robot.vi]
    mu = robot.profile["physics"]["friction"]
    for i in range(n):
        d.qpos[:] = poses[i]
        d.qvel[:] = velocity[i]
        mujoco.mj_forward(m, d)
        M = np.empty((m.nv, m.nv))
        mujoco.mj_fullM(m, M, d.qM)
        required = M @ acceleration[i] + d.qfrc_bias - d.qfrc_passive
        columns = []
        for side, body in enumerate(robot.foot_ids):
            if not a["planned_contacts"][i, side]:
                continue
            points = (
                robot.foot_points[side] @ d.xmat[body].reshape(3, 3).T + d.xpos[body]
            )
            # Outer footprint is an optimistic motor screen, NOT a contact model.
            points = np.unique(points[:, :2], axis=0)
            points = points[ConvexHull(points).vertices]
            for xy in points:
                J = np.zeros((3, m.nv))
                mujoco.mj_jac(m, d, J, None, np.r_[xy, 0.0], body)
                columns.append(J.T)
        k = len(columns)
        F = np.concatenate(columns, axis=1) if k else np.empty((m.nv, 0))
        nf = 3 * k
        cap = torque_envelope(
            robot.profile, robot.names, velocity[i, robot.vi], robot.effort
        )
        # Dimensionless variables avoid ill-conditioned force/torque columns
        # when a revised URDF changes mass and inertia by different amounts.
        # f = body_weight * f_normalized; tau = cap * tau_normalized.
        force_scale = max(robot.mass * 9.81, 1e-6)
        physical_eq = np.c_[F * force_scale, S * cap[None, :], np.zeros(m.nv)]
        row_scale = np.maximum(np.maximum(abs(physical_eq).max(1), abs(required)), 1e-6)
        eq = physical_eq / row_scale[:, None]
        rhs = required / row_scale
        ub = []
        for j in range(k):
            # Inscribed friction pyramid: |fx| + |fy| <= mu*fz.
            for sx, sy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                row = np.zeros(nf + N + 1)
                row[3 * j : 3 * j + 3] = [sx, sy, -mu]
                ub.append(row)
        for j in range(N):
            for sign in [-1, 1]:
                row = np.zeros(nf + N + 1)
                row[nf + j] = sign
                row[-1] = -1.0
                ub.append(row)
        cost = np.zeros(nf + N + 1)
        cost[-1] = 1.0
        bounds = (
            [(None, None) if j % 3 != 2 else (0, None) for j in range(nf)]
            + [(None, None)] * N
            + [(0, None)]
        )
        solved = linprog(
            cost,
            A_ub=ub,
            b_ub=np.zeros(len(ub)),
            A_eq=eq,
            b_eq=rhs,
            bounds=bounds,
            method="highs",
            options={"time_limit": 5.0},
        )
        for method in ["highs-ipm", "highs-ds"]:
            if solved.status in (0, 2):
                break
            initial = str(solved.message)
            solved = linprog(
                cost,
                A_ub=ub,
                b_ub=np.zeros(len(ub)),
                A_eq=eq,
                b_eq=rhs,
                bounds=bounds,
                method=method,
                options={"presolve": False, "time_limit": 5.0},
            )
            solver_retries.append(
                dict(
                    frame=i,
                    method=method,
                    initial_message=initial,
                    final_status=int(solved.status),
                )
            )
        statuses.append(int(solved.status))
        if solved.success:
            utilization.append(float(solved.x[-1]))
            torques.append(solved.x[nf : nf + N] * cap)
            residuals.append(float(abs(physical_eq @ solved.x - required).max()))
        elif solved.status == 2:
            balance_unresolved.append(i)
        else:
            raise ValueError(
                f"Reference dynamics solver failed at frame {i}: {solved.message}"
            )
    peak = max(utilization, default=None)
    speed_ratio = float(np.max(abs(a["joints_vel"]) / robot.speed))
    # Unresolved contact balance remains visible and does not masquerade as a
    # proved excessive joint torque. At least one solved frame is required.
    motor_exceeded = peak is not None and peak > 1.0001
    eligible = bool(utilization) and speed_ratio <= 1.0001 and not motor_exceeded
    status = (
        "exceeds_planning_envelope"
        if motor_exceeded
        else (
            "balance_unresolved" if balance_unresolved else "within_planning_envelope"
        )
    )
    return dict(
        schema="gom_reference_screen_v1",
        model_id=robot.model_id,
        reference_eligible=eligible,
        motor_status=status,
        frames_checked=n,
        solved_frames=len(utilization),
        balance_unresolved_frames=balance_unresolved,
        peak_minimum_torque_utilization=peak,
        peak_speed_utilization=speed_ratio,
        joint_peak_allocated_torque_nm=(
            dict(zip(robot.names, np.max(abs(np.asarray(torques)), axis=0).tolist()))
            if torques
            else {}
        ),
        max_equation_residual=max(residuals, default=None),
        solver_statuses=statuses,
        solver_retries=solver_retries,
        torque_allocation="minimum maximum normalized joint torque; all floating-base equations enforced",
        solver_scaling="body-weight-scaled forces, envelope-scaled torques and row-normalized equations; physical residuals reported",
        support_assumption="Optimistic outer projected sole polygon, planned stance only; positive forces, inscribed Coulomb friction pyramid.",
        planning_motor_profile=robot.profile["motors"],
        tracking_controller_used=False,
        dynamics_verified=False,
        hardware_ready=False,
        limitations=[
            "An optimistic necessary-condition screen, not proof of realizable rolling contact or tracking.",
            "Unresolved balance frames are conditional references, not motor-infeasibility evidence.",
            "No continuous-duty, temperature, voltage-drop or measured actuator model.",
        ],
    )
