"""C2 task-space gait curves -> finite-horizon CoP/CoM QP -> whole-body IK.

Inspired by the high-level BDX workflow, not Disney code or a claim of equivalent
performance. The resulting motion is kinematic until the separate rollout passes.
"""

import numpy as np
from scipy import sparse
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from scipy.special import logsumexp
from scipy.spatial import ConvexHull


def smooth(t):
    t = np.clip(t, 0, 1)
    return t**3 * (10 - 15 * t + 6 * t * t)


def preview_com(
    nominal, feet, contacts, half_sizes, height, dt, support_polygons=None, prior=None
):
    import clarabel

    n = len(nominal)
    D1 = np.diff(np.eye(n), axis=0) / dt
    D2 = np.diff(np.eye(n), n=2, axis=0) / dt**2
    curvature = np.zeros((n, n))
    curvature[1:-1] = D2
    Z = np.eye(n) - np.broadcast_to(height, (n,))[:, None] / 9.81 * curvature
    H = 2 * (np.eye(n) + 0.025 * D1.T @ D1 + 0.00001 * D2.T @ D2)
    rows = []
    rhs = []
    for i in range(n):
        if support_polygons is None:
            points = np.concatenate(
                [
                    feet[i, s, :2]
                    + np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]]) * half_sizes[s]
                    for s in range(2)
                    if contacts[i, s]
                ]
            )
        else:
            points = np.asarray(support_polygons[i])
        # A numerical 0.05 mm buffer permits line/point contacts in the QP. It
        # is not a modeled pad width or a balance certificate.
        points = np.concatenate(
            [
                points + [dx, dy]
                for dx, dy in [(-0.00005, 0), (0.00005, 0), (0, -0.00005), (0, 0.00005)]
            ]
        )
        hull = ConvexHull(points)
        for ax, ay, c in hull.equations:
            rows.append(np.r_[ax * Z[i], ay * Z[i]])
            rhs.append(-c)
    E = np.eye(n)[[0, 1, n - 2, n - 1]]
    end = sparse.block_diag([E, E]).toarray()
    A = np.r_[end, np.asarray(rows)]
    b = np.r_[nominal[[0, 1, n - 2, n - 1], :2].T.ravel(), rhs]
    settings = clarabel.DefaultSettings()
    settings.verbose = False
    P = sparse.block_diag([H, H]).tocsc()
    q = -2 * nominal[:, :2].T.ravel()
    if prior is not None:
        # A rigid rocking edge can be incompatible with the authored torso and
        # current ROM. Treat the observed patch as a soft correction, bounded
        # to 2 mm per pass, while preserving the hard outer support polygon.
        outer = []
        outer_rhs = []
        for i in range(n):
            points = np.concatenate(
                [
                    feet[i, s, :2]
                    + np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]]) * half_sizes[s]
                    for s in range(2)
                    if contacts[i, s]
                ]
            )
            for ax, ay, c in ConvexHull(points).equations:
                outer.append(np.r_[ax * Z[i], ay * Z[i]])
                outer_rhs.append(-c + 0.00005)
        k = len(rows)
        zero = sparse.csc_matrix
        A = sparse.vstack(
            [
                sparse.hstack([end, zero((8, k))]),
                sparse.hstack([outer, zero((len(outer), k))]),
                sparse.hstack([rows, -sparse.eye(k)]),
                sparse.hstack([zero((k, 2 * n)), -sparse.eye(k)]),
                sparse.hstack([sparse.eye(2 * n), zero((2 * n, k))]),
                sparse.hstack([-sparse.eye(2 * n), zero((2 * n, k))]),
            ]
        ).tocsc()
        b = np.r_[
            b[:8],
            outer_rhs,
            rhs,
            np.zeros(k),
            prior[:, :2].T.ravel() + 0.002,
            -prior[:, :2].T.ravel() + 0.002,
        ]
        P = sparse.block_diag([P, sparse.eye(k) * 4000]).tocsc()
        q = np.r_[q, np.zeros(k)]
    solution = clarabel.DefaultSolver(
        sparse.triu(P).tocsc(),
        q,
        sparse.csc_matrix(A),
        b,
        [clarabel.ZeroConeT(8), clarabel.NonnegativeConeT(len(b) - 8)],
        settings,
    ).solve()
    if str(solution.status) not in ("Solved", "AlmostSolved"):
        raise ValueError("CoM/CoP plan infeasible: " + str(solution.status))
    result = nominal.copy()
    result[:, :2] = np.asarray(solution.x)[: 2 * n].reshape(2, n).T
    return result


def generate(
    robot,
    kind="walk",
    seconds=4.0,
    fps=50,
    parameters=None,
    *,
    _support_polygons=None,
    _prior=None,
    _refinements=None
):
    import mujoco

    p = dict(robot.profile["generation"])
    p.update(parameters or {})
    if kind not in ("stand", "walk"):
        raise ValueError(
            "Authoring currently supports stand/walk; turning requires a heading-aware support polygon"
        )
    if (
        not np.isfinite([seconds, fps, *p.values()]).all()
        or seconds < 2
        or not 10 <= fps <= 100
    ):
        raise ValueError("Invalid duration/FPS/parameters")
    if (
        p["period_s"] <= 0.4
        or not 0 < p["swing_fraction"] < 0.5
        or not 0 <= p["clearance_m"] <= 0.02
        or not 0 <= p["speed_m_s"] <= 0.04
    ):
        raise ValueError("Invalid gait ranges")
    n = round(seconds * fps) + 1
    t = np.arange(n) / fps
    N = len(robot.names)
    robot.set_state(robot.nominal, [0, 0, robot.height], [0, 0, 0, 1])
    d = robot.data
    m = robot.model
    start = robot.sole_positions()
    start[:, 2] = 0.0
    foot_R = robot.sole_rotations
    start_com = d.subtree_com[robot.root_id].copy()
    half = np.array(
        [np.ptp(points[:, :2], axis=0) / 2 for points in robot.world_feet()]
    )
    feet = np.repeat(start[None], n, axis=0)
    contacts = np.ones((n, 2), dtype=np.int8)
    period = p["period_s"]
    step = period / 2
    stride = p["speed_m_s"] * period if kind == "walk" else 0.0
    lead = 0.7
    last_landing = seconds - 0.5
    phase = np.maximum(0, t - lead) / period
    for side in range(2):
        if kind == "stand":
            continue
        for k in range(int(seconds / step) + 1):
            if k % 2 != side:
                continue
            begin = lead + k * step
            end = begin + p["swing_fraction"] * period
            if end > last_landing:
                continue
            a = np.clip((t - begin) / (end - begin), 0, 1)
            # Each foot advances one cycle's displacement; derivatives vanish at touchdown.
            advance = stride if k >= 2 else stride * (0.5 if side == 0 else 1.0)
            feet[:, side, 0] += advance * smooth(a)
            active = (t > begin) & (t < end)
            contacts[active, side] = 0
            feet[:, side, 2] += p["clearance_m"] * 64 * a**3 * (1 - a) ** 3 * active
    center_shift = feet[:, :, 0].mean(1) - start[:, 0].mean()
    nominal = np.repeat(start_com[None], n, axis=0)
    nominal[:, 0] += center_shift
    com = (
        preview_com(nominal, feet, contacts, half, start_com[2], 1 / fps)
        if kind == "walk"
        else nominal
    )
    phase_envelope = smooth(t / 0.35) * smooth((seconds - t) / 0.35)
    wave = np.sin(2 * np.pi * phase) * phase_envelope
    rpy = np.zeros((n, 3))
    rpy[:, 0] = np.deg2rad(p["torso_roll_deg"]) * wave if kind == "walk" else 0
    rpy[:, 1] = np.deg2rad(p["torso_pitch_deg"])
    quats = Rotation.from_euler("xyz", rpy).as_quat()
    pelvis = (
        robot.height
        + p.get("pelvis_offset_m", 0.0)
        + p["pelvis_bob_m"] * 0.5 * (1 - np.cos(4 * np.pi * phase)) * phase_envelope
    )
    if _support_polygons is not None:
        com = preview_com(
            nominal,
            feet,
            contacts,
            half,
            start_com[2] + pelvis - robot.height,
            1 / fps,
            _support_polygons,
            _prior,
        )
    qlist = []
    roots = []
    actual_feet = []
    corrected_targets = []
    actual_com = []
    errors = []
    statuses = []
    patches = []
    x = np.r_[robot.nominal, 0.0, 0.0, robot.height]
    bounds = (
        np.r_[robot.lower, -1.0, -1.0, robot.height - 0.03],
        np.r_[robot.upper, 1.0, 1.0, robot.height + 0.03],
    )
    for i in range(n):
        posture = robot.nominal.copy()
        if "neck_yaw_joint" in robot.names:
            posture[robot.names.index("neck_yaw_joint")] = (
                np.deg2rad(p["neck_yaw_deg"]) * wave[i]
            )
        cached_x = None
        cached = None

        def evaluate(values):
            nonlocal cached_x, cached
            if cached_x is not None and np.array_equal(values, cached_x):
                return cached
            robot.set_state(values[:N], values[N:], quats[i])
            res = []
            jac = []
            for s, b in enumerate(robot.foot_ids):
                R = d.xmat[b].reshape(3, 3)
                point = R @ robot.sole_local[s] + d.xpos[b]
                J = np.zeros((3, m.nv))
                W = J.copy()
                mujoco.mj_jac(m, d, J, W, point, b)
                scale = 0.001 if contacts[i, s] else 0.0015
                points = robot.foot_points[s] @ R.T + d.xpos[b]
                temperature = 0.0002
                weights = np.exp(
                    -points[:, 2] / temperature - logsumexp(-points[:, 2] / temperature)
                )
                soft_low = -temperature * logsumexp(-points[:, 2] / temperature)
                Jlow = np.zeros((3, m.nv))
                mujoco.mj_jac(m, d, Jlow, None, weights @ points, b)
                error = point - feet[i, s]
                error[2] = soft_low - feet[i, s, 2]
                J[2] = Jlow[2]
                scales = np.array([scale, scale, 0.0003])
                res.extend(error / scales)
                jac.extend(np.c_[J[:, robot.vi], np.eye(3)] / scales[:, None])
                # No ankle roll on this robot: the sole may passively rock.
                # Keep pitch/yaw directed, while the lowest-point task above
                # keeps the actual rotated collision shape out of the floor.
                angular = (
                    Rotation.from_matrix(R) * Rotation.from_matrix(foot_R[s]).inv()
                ).as_rotvec()
                res.extend(angular[1:] / 0.025)
                jac.extend(np.c_[W[1:, robot.vi], np.zeros((2, 3))] / 0.025)
            J = np.zeros((3, m.nv))
            mujoco.mj_jacSubtreeCom(m, d, J, robot.root_id)
            res.extend((d.subtree_com[robot.root_id, :2] - com[i, :2]) / 0.0015)
            jac.extend(np.c_[J[:2, robot.vi], np.eye(3)[:2]] / 0.0015)
            res.append((values[-1] - pelvis[i]) / 0.008)
            row = np.zeros(N + 3)
            row[-1] = 125
            jac.append(row)
            weights = np.array(
                [50.0 if name.startswith("neck_") else 0.1 for name in robot.names]
            )
            res.extend((values[:N] - posture) * weights)
            jac.extend(np.c_[np.diag(weights), np.zeros((N, 3))])
            cached_x = values.copy()
            cached = (np.asarray(res), np.asarray(jac))
            return cached

        lower = bounds[0].copy()
        upper = bounds[1].copy()
        if i:
            # Hard slew bounds prevent IK branch changes from becoming servo targets.
            delta = np.minimum(robot.speed * 0.8, p.get("ik_slew_rad_s", 0.8)) / fps
            lower[:N] = np.maximum(lower[:N], x[:N] - delta)
            upper[:N] = np.minimum(upper[:N], x[:N] + delta)
        solution = least_squares(
            lambda v: evaluate(v)[0],
            np.clip(x, lower + 1e-10, upper - 1e-10),
            jac=lambda v: evaluate(v)[1],
            bounds=(lower, upper),
            max_nfev=45,
            ftol=1e-7,
            xtol=1e-8,
            gtol=1e-6,
        )
        x = solution.x
        robot.set_state(x[:N], x[N:], quats[i])
        qlist.append(x[:N].copy())
        roots.append(x[N:].copy())
        actual_feet.append(robot.sole_positions())
        actual_com.append(d.subtree_com[robot.root_id].copy())
        corrected = feet[i].copy()
        for s, b in enumerate(robot.foot_ids):
            R = d.xmat[b].reshape(3, 3)
            corrected[s, 2] += float(
                (R @ robot.sole_local[s])[2] - (robot.foot_points[s] @ R.T)[:, 2].min()
            )
        corrected_targets.append(corrected)
        errors.append(float(np.max(abs(actual_feet[-1] - corrected))))
        statuses.append(bool(solution.success))
        support = []
        for s, points in enumerate(robot.world_feet()):
            if contacts[i, s]:
                support.extend(
                    points[
                        points[:, 2]
                        <= points[:, 2].min() + p.get("contact_band_m", 0.0005),
                        :2,
                    ]
                )
        patches.append(np.asarray(support))
    refinements = (
        p.get("contact_refinement_passes", 0) if _refinements is None else _refinements
    )
    if kind == "walk" and refinements > 0:
        return generate(
            robot,
            kind,
            seconds,
            fps,
            p,
            _support_polygons=patches,
            _prior=com,
            _refinements=refinements - 1,
        )
    q = np.asarray(qlist)
    root = np.asarray(roots)
    actual_feet = np.asarray(actual_feet)
    R = Rotation.from_quat(quats)
    omega = (R[1:] * R[:-1].inv()).as_rotvec() * fps
    omega = np.vstack([omega[:1], omega])
    arrays = dict(
        time=t,
        fps=np.asarray(fps),
        joint_names=np.asarray(robot.names),
        joints_pos=q,
        joints_vel=np.gradient(q, 1 / fps, axis=0, edge_order=2),
        root_pos=root,
        root_quat=quats,
        world_linear_vel=np.gradient(root, 1 / fps, axis=0, edge_order=2),
        world_angular_vel=omega,
        foot_positions_world=actual_feet,
        target_foot_positions_world=np.asarray(corrected_targets),
        target_sole_height_m=feet[:, :, 2],
        com_world=np.asarray(actual_com),
        target_com_world=com,
        planned_contacts=contacts,
        phase=phase,
        model_id=np.asarray(robot.model_id),
        quaternion_order=np.asarray("xyzw"),
    )
    arrays["sole_points_link"] = np.asarray(robot.sole_local)
    for position, velocity, acceleration in [
        ("joints_pos", "joints_vel", "joints_acc"),
        ("com_world", "com_velocity_world", "com_acceleration_world"),
        ("foot_positions_world", "foot_velocities_world", "foot_accelerations_world"),
    ]:
        arrays[velocity] = np.gradient(arrays[position], 1 / fps, axis=0, edge_order=2)
        arrays[acceleration] = np.gradient(
            arrays[velocity], 1 / fps, axis=0, edge_order=2
        )
    arrays["foot_positions_body"] = np.stack(
        [R.inv().apply(actual_feet[:, s] - root) for s in range(2)], axis=1
    )
    return arrays, dict(
        kind=kind,
        parameters=p,
        ik_converged_fraction=float(np.mean(statuses)),
        max_foot_error_m=max(errors),
        generator="C2 swing + 2D convex support-polygon CoM/CoP QP + rolling-patch refinement + whole-body IK",
        contact_patch_refinements=(
            int(p.get("contact_refinement_passes", 0)) if kind == "walk" else 0
        ),
        contact_patch_method="Hard outer support hull; observed low-edge patch is a soft QP objective with a 2 mm CoM trust region. No claim of exact contact feasibility.",
        balance_is_approximate=True,
        dynamics_verified=False,
        hardware_ready=False,
    )
