"""Bounded free-base flat-floor gait search with no PPO or root assistance."""

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

from runtime import ROOT, close_app, configure_asset_cache, configure_runtime
from train import source_hashes


def main():
    kit_args = configure_runtime("flat_probe")
    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--seconds", type=float, default=18)
    parser.add_argument("--initial-joint-noise", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--video", action="store_true")
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT) or not 6 <= args.seconds <= 60:
        parser.error("Use a workspace output and 6–60 seconds")
    if args.candidates and not args.candidates.resolve().is_relative_to(ROOT):
        parser.error("Candidate file must be inside the workspace")
    if not math.isfinite(args.initial_joint_noise) or not 0 <= args.initial_joint_noise <= 0.01:
        parser.error("Initial joint noise must be 0–0.01 rad")
    args.headless = True
    args.enable_cameras = args.video
    args.kit_args = f"{kit_args} {args.kit_args}"
    launcher = AppLauncher(args)
    try:
        import torch
        import warp
        from isaaclab.utils.math import euler_xyz_from_quat
        from snu_gom_walk.env import GomEnv, GomEnvCfg, MODEL
        from flat_probe_motion import PARAMETERS, ankle_pitch_correction, guard_inward_roll, probe_targets, swing_weights

        torch.set_num_threads(4)
        warp.config.kernel_cache_dir = str(ROOT / ".cache/warp")
        probe_hashes = {name: hashlib.sha256((ROOT / "scripts" / name).read_bytes()).hexdigest() for name in ["flat_probe_motion.py", "probe_flat_gait.py"]}
        candidates = json.loads(args.candidates.read_text()) if args.candidates else [
            dict(zip(PARAMETERS, values)) for values in itertools.product(
                [0.10, 0.20, 0.30], [0.15, 0.25, 0.35], [0.06, 0.12], [-0.06, 0.0, 0.06], [4.0, 6.0],
            )
        ]
        if not 1 <= len(candidates) <= 1024:
            raise ValueError("Use 1–1024 candidates")
        if args.video and len(candidates) > 16:
            raise ValueError("Render at most 16 candidates, separately from the search")
        parameters = torch.tensor([[candidate[key] for key in PARAMETERS] for candidate in candidates], device=args.device)
        pitch_gains = torch.tensor([[candidate.get("pitch_kp", 0.0), candidate.get("pitch_kd", 0.0)] for candidate in candidates], device=args.device)
        swing_level = torch.tensor([candidate.get("swing_level", 0.0) for candidate in candidates], device=args.device)
        inward_limit = torch.tensor([candidate.get("inward_roll_limit", 10.0) for candidate in candidates], device=args.device)
        if not torch.isfinite(inward_limit).all() or (inward_limit <= 0).any():
            raise ValueError("Inward roll guard must be finite and positive")
        if not torch.isfinite(swing_level).all() or ((swing_level < 0) | (swing_level > 1)).any():
            raise ValueError("Swing leveling blend must be in [0, 1]")

        class ProbeEnv(GomEnv):
            def _pre_physics_step(self, actions):
                self.previous_actions.copy_(self.actions)
                time = self.episode_length_buf * self.step_dt
                desired = probe_targets(time, parameters)
                roll, pitch, _ = euler_xyz_from_quat(self.robot.data.root_quat_w)
                roll = (roll + torch.pi) % (2 * torch.pi) - torch.pi
                pitch = (pitch + torch.pi) % (2 * torch.pi) - torch.pi
                correction = ankle_pitch_correction(pitch, self.robot.data.root_ang_vel_b[:, 1], pitch_gains)
                desired[:, [4, 9]] += correction[:, None]
                blend = swing_level[:, None] * swing_weights(time, parameters[:, 4])
                desired[:, [1, 6]] = torch.lerp(desired[:, [1, 6]], -roll[:, None].expand(-1, 2), blend)
                desired[:, [4, 9]] -= (correction + pitch)[:, None] * blend
                desired = guard_inward_roll(desired, inward_limit)
                limits = self.robot.data.soft_joint_pos_limits[:, self.leg_ids]
                self.position_clipped = (desired < limits[..., 0]) | (desired > limits[..., 1])
                desired = desired.clamp(limits[..., 0], limits[..., 1])
                previous = self.targets[:, self.leg_ids]
                maximum = self.robot.data.joint_vel_limits[:, self.leg_ids] * self.step_dt
                self.rate_limited = (desired - previous).abs() > maximum + 1e-6
                self.targets[:, self.leg_ids] = previous + (desired - previous).clamp(-maximum, maximum)
                self.actions = (self.targets[:, self.leg_ids] - self.robot.data.default_joint_pos[:, self.leg_ids]) / self.scales
                self.peak_velocity = torch.zeros(self.num_envs, device=self.device)

            def _apply_action(self):
                self.peak_velocity = torch.maximum(self.peak_velocity, self.robot.data.joint_vel[:, self.leg_ids].abs().amax(dim=-1))
                super()._apply_action()

            def _get_rewards(self):
                reward = super()._get_rewards()
                roll, pitch, yaw = euler_xyz_from_quat(self.robot.data.root_quat_w)
                angles = torch.stack((roll, pitch, yaw), dim=-1)
                angles = (angles + torch.pi) % (2 * torch.pi) - torch.pi
                self.snapshot = torch.cat((
                    self.robot.data.root_pos_w - self.scene.env_origins,
                    angles,
                    self.last_metrics["sole_heights"],
                    self.last_metrics["contacts"].float(),
                    self.last_metrics["qualified_touchdowns"].float(),
                    self.last_metrics["alternating_touchdowns"][:, None].float(),
                    self.peak_velocity[:, None],
                    self.rate_limited.float().mean(dim=-1, keepdim=True),
                    self.position_clipped.float().mean(dim=-1, keepdim=True),
                    self.robot.data.applied_torque[:, self.leg_ids].abs().amax(dim=-1, keepdim=True),
                    self.robot.data.joint_pos[:, self.leg_ids],
                    self.targets[:, self.leg_ids],
                    self.robot.data.applied_torque[:, self.leg_ids],
                    self.contacts.data.net_forces_w[:, self.contact_foot_ids, 2],
                ), dim=-1).clone()
                return reward

        cfg = GomEnvCfg()
        cfg.evaluation = True
        cfg.seed = args.seed
        cfg.scene_layout = "flat"
        cfg.scene.num_envs = len(candidates)
        cfg.sim.device = args.device
        cfg.speed = 0.01
        cfg.episode_length_s = args.seconds + 1
        cfg.viewer.resolution = (800, 600)
        if args.video:
            cfg.scene.env_spacing = 0.6
        configure_asset_cache(cfg, MODEL)
        env = ProbeEnv(cfg, render_mode="rgb_array" if args.video else None)
        env.reset()
        if args.initial_joint_noise:
            positions = env.robot.data.default_joint_pos + (2 * torch.rand_like(env.robot.data.joint_pos) - 1) * args.initial_joint_noise
            env.robot.write_joint_state_to_sim(positions, torch.zeros_like(positions))
        frames = []
        if args.video:
            import imageio.v2 as imageio
            import numpy as np
            from PIL import Image, ImageDraw, ImageFont

            center = env.scene.env_origins.mean(dim=0).cpu().tolist()
            span = max(float(env.scene.env_origins[:, :2].max() - env.scene.env_origins[:, :2].min()), 0.6)
            env.sim.set_camera_view((center[0] + span, center[1] - 1.3 * span, 1.05 * span), (center[0], center[1], 0.12))
            font = ImageFont.truetype("DejaVuSans.ttf", 17)
        alive = torch.ones(len(candidates), device=env.device, dtype=torch.bool)
        traces = []
        alive_traces = []
        termination_details = [None] * len(candidates)
        for step in range(round(args.seconds / env.step_dt)):
            with torch.no_grad():
                _, _, terminated, truncated, _ = env.step(torch.zeros(len(candidates), 10, device=env.device))
            traces.append(env.snapshot.cpu())
            alive_traces.append(alive.cpu())
            for index in (alive & terminated).nonzero().flatten().tolist():
                forces = env.last_terminal["body_contact_forces"][index].norm(dim=-1).cpu().tolist()
                termination_details[index] = {
                    "time": (step + 1) * env.step_dt,
                    "body_contact_force_norms": dict(zip(env.contacts.body_names, forces)),
                    "height_below_threshold": bool(env.snapshot[index, 2] < 0.10),
                    "tilt_below_threshold": bool(env.last_metrics["upright"][index] < 0.707),
                    "nonfoot_contact_above_threshold": any(forces[body] > 2 for body in env.nonfoot_ids),
                }
            alive = alive & ~(terminated | truncated)
            if args.video and step % 2 == 0:
                frame = Image.fromarray(env.render())
                draw = ImageDraw.Draw(frame)
                draw.rectangle((0, 0, 800, 60), fill=(24, 32, 45))
                draw.text((12, 7), "SNU-GOM | scripted flat-floor feasibility test | NOT a trained policy", font=font, fill="white")
                draw.text((12, 33), f"t={(step + 1) * env.step_dt:.1f}s | first-trial survivors: {int(alive.sum())}/{len(candidates)} | no root assistance", font=font, fill="white")
                frames.append(np.array(frame))
            if step % 250 == 0:
                print(f"time={(step + 1) * env.step_dt:.2f}, alive={int(alive.sum())}/{len(candidates)}", flush=True)
        trace = torch.stack(traces)
        valid = torch.stack(alive_traces)
        results = []
        for index, candidate in enumerate(candidates):
            samples = trace[valid[:, index], index]
            settled = samples[min(150, len(samples) - 1):]
            steps = samples[:, 10:12].sum(dim=0).int().tolist()
            alternating = int(samples[:, 12].sum())
            survived = bool(alive[index])
            results.append({
                "candidate": index, "parameters": candidate,
                "termination": termination_details[index],
                "survived": survived, "duration": len(samples) * env.step_dt,
                "final_position": samples[-1, :3].tolist(),
                "maximum_clearance": samples[:, 6:8].amax(dim=0).tolist(),
                "qualified_touchdowns": steps, "alternating_touchdowns": alternating,
                "peak_joint_speed_after_settling": float(settled[:, 13].max()),
                "target_rate_limited_fraction": float(samples[:, 14].mean()),
                "target_position_clipped_fraction": float(samples[:, 15].mean()),
                "peak_estimated_torque": float(samples[:, 16].max()),
                "max_abs_pitch_roll_after_settling": settled[:, 3:5].abs().amax(dim=0).tolist(),
                "stepping_screen_passed": survived and min(steps) >= 2 and alternating >= 3,
            })
        ranked = sorted(results, key=lambda row: (row["stepping_screen_passed"], row["survived"], min(row["qualified_touchdowns"]), row["alternating_touchdowns"], row["duration"]), reverse=True)
        report = {
            "kind": "scripted_free_base_feasibility_search_not_trained_policy",
            "optimizer_updates": 0, "root_assistance": False, "scene": "flat", "seconds": args.seconds,
            "seed": args.seed, "initial_joint_noise_rad": args.initial_joint_noise,
            "model_hashes": MODEL["hashes"], "source_hashes": source_hashes(),
            "probe_hashes": probe_hashes,
            "controller": {"stiffness": cfg.stiffness, "damping": cfg.damping, "limits": "Unchanged supplied URDF limits", "settling_seconds": 3, "pitch_feedback": "Optional per-candidate IMU pitch/angular-velocity ankle correction, bounded to +/-0.15 rad", "swing_leveling": "Optional phase-weighted IMU roll/pitch compensation at swing hip-roll/ankle-pitch; no external forces", "inward_roll_guard": "Optional asymmetric target bound: left roll >= -limit, right roll <= limit; unchanged physical joint limits and collision shapes"},
            "survivors": int(alive.sum()), "stepping_screen_passes": sum(row["stepping_screen_passed"] for row in results),
            "results": ranked,
            "trace_columns": ["x", "y", "z", "roll", "pitch", "yaw", "left_clearance", "right_clearance", "left_contact", "right_contact", "left_touchdown", "right_touchdown", "alternating", "peak_joint_speed", "rate_limited_fraction", "position_clipped_fraction", "peak_torque"] + [f"{kind}/{joint}" for kind in ["joint_position", "target", "torque"] for joint in MODEL["policy_joint_order"]] + ["left_normal_force", "right_normal_force"],
            "trace_dt": env.step_dt,
            "best_traces": {str(row["candidate"]): trace[valid[:, row["candidate"]], row["candidate"]].tolist() for row in (ranked if len(candidates) <= 16 else ranked[:3])},
            "scope": "Screen only; selection on these trials is not independent validation, forward walking, or hardware feasibility",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        if frames:
            imageio.mimsave(args.output.with_suffix(".mp4"), frames, fps=25)
            imageio.imwrite(args.output.with_suffix(".png"), frames[len(frames) // 2])
        print(json.dumps({key: report[key] for key in ["survivors", "stepping_screen_passes"]}), flush=True)
        print(json.dumps(ranked[:5], indent=2), flush=True)
    finally:
        close_app(launcher)


if __name__ == "__main__":
    main()
