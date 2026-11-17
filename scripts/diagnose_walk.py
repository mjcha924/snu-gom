"""Record free-base control, contact, and substep actuator diagnostics."""

import argparse
import json
from pathlib import Path

from runtime import ROOT, close_app, configure_asset_cache, configure_runtime
from train import source_hashes


def main():
    kit_args = configure_runtime("walk_diagnostics")
    from isaaclab.app import AppLauncher

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["policy", "seed", "neutral"], required=True)
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "policies/support-v4/model.pt")
    parser.add_argument("--seconds", type=float, default=12)
    parser.add_argument("--output", type=Path, required=True)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or args.seconds <= 0:
        parser.error("Output must be inside the workspace and duration positive")
    args.headless = True
    args.enable_cameras = False
    args.kit_args = f"{kit_args} {args.kit_args}"
    launcher = AppLauncher(args)
    try:
        import torch
        import warp
        from isaaclab.utils.math import quat_apply, euler_xyz_from_quat
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from rsl_rl.runners import OnPolicyRunner
        from snu_gom_walk.env import GomEnv, GomEnvCfg, MODEL
        from snu_gom_walk.model import LEG_JOINTS

        torch.set_num_threads(4)
        warp.config.kernel_cache_dir = str(ROOT / ".cache/warp")

        class DiagnosticEnv(GomEnv):
            def _pre_physics_step(self, actions):
                self.commanded_reference = self.reference_positions().clone()
                self.requested_residual = actions.clamp(-1, 1) * self.scales
                self.substep_velocities = []
                self.substep_torques = []
                super()._pre_physics_step(actions)

            def _apply_action(self):
                self.substep_velocities.append(self.robot.data.joint_vel[0, self.leg_ids].tolist())
                self.substep_torques.append(self.robot.data.applied_torque[0, self.leg_ids].tolist())
                super()._apply_action()

            def _get_dones(self):
                result = super()._get_dones()
                contacts, heights = self.foot_state()
                corners = self.foot_corners_world()
                mask = (corners[..., 2] < corners[..., 2].amin(dim=-1, keepdim=True) + 0.001).float()
                point = (corners * mask[..., None]).sum(dim=-2) / mask.sum(dim=-1, keepdim=True)
                offset = point - self.robot.data.body_com_pos_w[:, self.foot_ids]
                velocity = self.robot.data.body_com_lin_vel_w[:, self.foot_ids] + torch.cross(
                    self.robot.data.body_com_ang_vel_w[:, self.foot_ids], offset, dim=-1,
                )
                roll, pitch, yaw = euler_xyz_from_quat(self.robot.data.root_quat_w)
                centers = self.robot.data.body_pos_w[:, self.foot_ids] + quat_apply(
                    self.robot.data.body_quat_w[:, self.foot_ids], self.corner_offsets.mean(dim=1)[None],
                )
                self.diagnostic = {
                    "position": self.robot.data.root_pos_w[0].tolist(),
                    "rpy": [float(roll[0]), float(pitch[0]), float(yaw[0])],
                    "reference": self.commanded_reference[0].tolist(),
                    "residual": self.requested_residual[0].tolist(),
                    "target": self.targets[0, self.leg_ids].tolist(),
                    "joint_position": self.robot.data.joint_pos[0, self.leg_ids].tolist(),
                    "joint_velocity": self.robot.data.joint_vel[0, self.leg_ids].tolist(),
                    "torque": self.robot.data.applied_torque[0, self.leg_ids].tolist(),
                    "contact_forces": self.contacts.data.net_forces_w[0].tolist(),
                    "contacts": contacts[0].tolist(), "heights": heights[0].tolist(),
                    "foot_centers": centers[0].tolist(),
                    "contact_point_velocity": velocity[0].tolist(),
                    "fallen": bool(result[0][0]),
                    "substep_joint_velocity": self.substep_velocities,
                    "substep_torque": self.substep_torques,
                }
                return result

        saved = json.loads((args.checkpoint.resolve().parent / "config.json").read_text())
        if saved["model_hashes"] != MODEL["hashes"]:
            raise ValueError("Model hash mismatch")
        if args.mode == "policy" and saved["source_hashes"] != source_hashes():
            raise ValueError("Policy source hash mismatch")
        cfg = GomEnvCfg()
        for key, value in saved["settings"].items():
            setattr(cfg, key, value)
        if args.mode == "neutral":
            cfg.reference_assistance = False
        cfg.evaluation = True
        cfg.scene_layout = "flat"
        cfg.scene.num_envs = 1
        cfg.sim.device = args.device
        cfg.episode_length_s = args.seconds + 1
        configure_asset_cache(cfg, MODEL)
        env = DiagnosticEnv(cfg)
        wrapped = RslRlVecEnvWrapper(env, clip_actions=1.0)
        policy = None
        if args.mode == "policy":
            runner = OnPolicyRunner(wrapped, saved["agent"], log_dir=None, device=args.device)
            runner.load(str(args.checkpoint.resolve()))
            policy = runner.get_inference_policy()
        observations, _ = wrapped.reset()
        samples = []
        for step in range(round(args.seconds / env.step_dt)):
            with torch.no_grad():
                action = policy(observations) if policy else torch.zeros(1, 10, device=env.device)
                observations, _, dones, _ = wrapped.step(action)
            samples.append({"time": (step + 1) * env.step_dt, **env.diagnostic})
            if dones.any():
                break
        report = {
            "mode": args.mode, "checkpoint": str(args.checkpoint.relative_to(ROOT)) if args.checkpoint.is_absolute() else str(args.checkpoint),
            "source_hashes": source_hashes(), "joint_order": LEG_JOINTS,
            "contact_body_names": env.contacts.body_names, "foot_contact_ids": env.contact_foot_ids,
            "substep_sample_timing": "Before each physics substep; final state also sampled before autoreset",
            "physics_dt": cfg.sim.dt, "control_dt": env.step_dt, "samples": samples,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report) + "\n")
        print(json.dumps({"mode": args.mode, "duration": samples[-1]["time"], "fallen": samples[-1]["fallen"], "position": samples[-1]["position"], "output": str(output)}), flush=True)
    finally:
        close_app(launcher)


if __name__ == "__main__":
    main()
