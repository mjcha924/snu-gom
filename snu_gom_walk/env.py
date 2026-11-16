"""Floating-base SNU-GOM environment for the installed Isaac Lab runtime."""

import math

import torch

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.envs import DirectRLEnv, DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensor, ContactSensorCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import quat_apply, quat_apply_inverse

from .model import ALL_JOINTS, FOOT_LINKS, LEG_JOINTS, ROOT, URDF, audit_model, stance_configuration
from .gait import gait_targets


MODEL = audit_model()


@configclass
class GomEnvCfg(DirectRLEnvCfg):
    decimation = 10
    episode_length_s = 10.0
    action_space = 10
    observation_space = 45
    state_space = 63
    seed = 42
    task = "walk"
    evaluation = False
    scene_layout = "flat"
    speed = 0.025
    gait_period = 2.4
    stance_knee = 0.30
    foot_clearance = 0.006
    stiffness = 4.0
    damping = 0.08
    sim = sim_utils.SimulationCfg(
        dt=0.002,
        render_interval=10,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            static_friction=0.8, dynamic_friction=0.7, restitution=0.0,
        ),
    )
    scene = InteractiveSceneCfg(num_envs=64, env_spacing=1.5, replicate_physics=True)
    robot = ArticulationCfg(
        prim_path="/World/envs/env_.*/Robot",
        spawn=sim_utils.UrdfFileCfg(
            asset_path=str(URDF),
            usd_dir=str(ROOT / "assets/generated/isaac"),
            usd_file_name="snu_gom.usd",
            fix_base=False,
            merge_fixed_joints=True,
            self_collision=True,
            activate_contact_sensors=True,
            joint_drive=sim_utils.UrdfConverterCfg.JointDriveCfg(
                gains=sim_utils.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(stiffness=0.0, damping=0.0),
            ),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False, max_depenetration_velocity=1.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=2,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, MODEL["initial_height"]), joint_pos={".*": 0.0}, joint_vel={".*": 0.0},
        ),
        actuators={
            "legs": ImplicitActuatorCfg(
                joint_names_expr=LEG_JOINTS,
                stiffness=4.0,
                damping=0.08,
                effort_limit_sim={name: MODEL["joints"][name]["effort"] for name in LEG_JOINTS},
                velocity_limit_sim={name: MODEL["joints"][name]["velocity"] for name in LEG_JOINTS},
            ),
            "neck": ImplicitActuatorCfg(
                joint_names_expr=["neck_.*"], stiffness=1.0, damping=0.04,
                effort_limit_sim=0.15, velocity_limit_sim=1.0,
            ),
        },
    )


class GomEnv(DirectRLEnv):
    cfg: GomEnvCfg

    def __init__(self, cfg, render_mode=None, **kwargs):
        positions, height, centers = stance_configuration(cfg.stance_knee, MODEL)
        cfg.robot.init_state.joint_pos = positions
        cfg.robot.init_state.pos = (0.0, 0.0, height + 0.003)
        cfg.robot.actuators["legs"].stiffness = cfg.stiffness
        cfg.robot.actuators["legs"].damping = cfg.damping
        super().__init__(cfg, render_mode, **kwargs)
        self.leg_ids, names = self.robot.find_joints(LEG_JOINTS, preserve_order=True)
        assert names == LEG_JOINTS
        self.obs_ids, names = self.robot.find_joints(ALL_JOINTS, preserve_order=True)
        assert names == ALL_JOINTS
        self.foot_ids, _ = self.robot.find_bodies(FOOT_LINKS, preserve_order=True)
        self.contact_foot_ids, _ = self.contacts.find_bodies(FOOT_LINKS, preserve_order=True)
        self.nonfoot_ids = [index for index, name in enumerate(self.contacts.body_names) if name not in FOOT_LINKS]
        self.scales = torch.tensor([0.15, 0.32, 0.65, 0.95, 0.40] * 2, device=self.device)
        self.stance_height = height
        self.nominal_foot_centers = torch.tensor([centers[name] for name in FOOT_LINKS], device=self.device)
        self.corner_offsets = torch.tensor([MODEL["foot_corners"][name] for name in FOOT_LINKS], device=self.device)
        self.actions = torch.zeros(self.num_envs, 10, device=self.device)
        self.previous_actions = self.actions.clone()
        self.targets = self.robot.data.default_joint_pos.clone()
        self.commands = torch.zeros(self.num_envs, 3, device=self.device)
        self.phase_offsets = torch.zeros(self.num_envs, device=self.device)
        self.episode_returns = torch.zeros(self.num_envs, device=self.device)
        self.last_metrics = {}
        self.last_terminal = {}

    def _setup_scene(self):
        self.robot = Articulation(self.cfg.robot)
        from pxr import Usd

        robot_path = "/World/envs/env_0/Robot"
        for prim in Usd.PrimRange(self.scene.stage.GetPrimAtPath(robot_path)):
            if prim.IsInstance() and prim.GetName() == "collisions":
                prim.SetInstanceable(False)
        sim_utils.modify_collision_properties(
            robot_path, sim_utils.CollisionPropertiesCfg(contact_offset=0.001, rest_offset=0.0),
        )
        self.contacts = ContactSensor(ContactSensorCfg(
            prim_path="/World/envs/env_.*/Robot/.*", history_length=2, track_air_time=True,
        ))
        floor = sim_utils.CuboidCfg(
            size=(100.0, 100.0, 0.1),
            collision_props=sim_utils.CollisionPropertiesCfg(contact_offset=0.001, rest_offset=0.0),
            physics_material=sim_utils.RigidBodyMaterialCfg(static_friction=0.8, dynamic_friction=0.7),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.18, 0.22, 0.27), roughness=0.9),
        )
        floor.func("/World/floor", floor, translation=(0.0, 0.0, -0.05))
        if self.cfg.scene_layout == "home":
            from .home import build_home

            build_home("/World/envs/env_0/Home")
        self.scene.clone_environments(copy_from_source=False)
        self.scene.filter_collisions(global_prim_paths=["/World/floor"])
        self.scene.articulations["robot"] = self.robot
        self.scene.sensors["contacts"] = self.contacts
        light = sim_utils.DomeLightCfg(intensity=1500.0, color=(0.9, 0.92, 1.0))
        light.func("/World/Light", light)

    def _pre_physics_step(self, actions):
        self.previous_actions.copy_(self.actions)
        desired = self.robot.data.default_joint_pos[:, self.leg_ids] + actions.clamp(-1, 1) * self.scales
        limits = self.robot.data.soft_joint_pos_limits[:, self.leg_ids]
        desired = torch.clamp(desired, limits[..., 0], limits[..., 1])
        previous = self.targets[:, self.leg_ids]
        max_change = self.robot.data.joint_vel_limits[:, self.leg_ids] * self.step_dt
        self.targets[:, self.leg_ids] = previous + torch.clamp(desired - previous, -max_change, max_change)
        self.actions = (self.targets[:, self.leg_ids] - self.robot.data.default_joint_pos[:, self.leg_ids]) / self.scales

    def _apply_action(self):
        self.robot.set_joint_position_target(self.targets)

    def phase(self):
        phase = self.episode_length_buf * self.step_dt / self.cfg.gait_period + self.phase_offsets
        return torch.remainder(phase, 1.0)

    def foot_state(self):
        forces = self.contacts.data.net_forces_w[:, self.contact_foot_ids]
        contacts = torch.linalg.vector_norm(forces, dim=-1) > 0.3
        rotations = self.robot.data.body_quat_w[:, self.foot_ids, None, :].expand(-1, -1, 8, -1)
        corners = self.corner_offsets[None].expand(self.num_envs, -1, -1, -1)
        world = quat_apply(rotations.reshape(-1, 4), corners.reshape(-1, 3)).reshape(self.num_envs, 2, 8, 3)
        world += self.robot.data.body_pos_w[:, self.foot_ids, None, :]
        heights = world[..., 2].min(dim=-1).values
        return contacts, heights

    def _get_observations(self):
        phase = self.phase() * (2 * math.pi)
        clock = torch.stack((phase.sin(), phase.cos()), dim=-1)
        clock = torch.where(self.commands[:, :1] > 0.005, clock, torch.zeros_like(clock))
        policy = torch.cat([
            self.robot.data.root_ang_vel_b * 0.25,
            self.robot.data.projected_gravity_b,
            self.commands * 10,
            self.robot.data.joint_pos[:, self.obs_ids] - self.robot.data.default_joint_pos[:, self.obs_ids],
            self.robot.data.joint_vel[:, self.obs_ids] * 0.25,
            self.actions,
            clock,
        ], dim=-1)
        contacts, heights = self.foot_state()
        critic = torch.cat([
            policy, self.robot.data.root_lin_vel_b,
            self.robot.data.root_pos_w[:, 2:3], contacts.float(), heights,
            self.robot.data.applied_torque[:, self.leg_ids],
        ], dim=-1)
        return {"policy": policy, "critic": critic}

    def _get_dones(self):
        height = self.robot.data.root_pos_w[:, 2]
        upright = -self.robot.data.projected_gravity_b[:, 2]
        nonfoot_force = self.contacts.data.net_forces_w[:, self.nonfoot_ids].norm(dim=-1).max(dim=-1).values
        invalid = ~torch.isfinite(self.robot.data.root_state_w).all(dim=-1)
        invalid |= ~torch.isfinite(self.robot.data.joint_pos).all(dim=-1)
        fallen = (height < 0.10) | (upright < 0.707) | (nonfoot_force > 2.0) | invalid
        timeout = self.episode_length_buf >= self.max_episode_length - 1
        self.last_terminal = {
            "position": self.robot.data.root_pos_w.detach().clone(),
            "velocity": self.robot.data.root_lin_vel_b.detach().clone(),
            "fallen": fallen.detach().clone(),
            "quaternion": self.robot.data.root_quat_w.detach().clone(),
            "foot_positions": self.robot.data.body_pos_w[:, self.foot_ids].detach().clone(),
            "joint_velocities": self.robot.data.joint_vel.detach().clone(),
            "torques": self.robot.data.applied_torque.detach().clone(),
        }
        return fallen, timeout

    def _get_rewards(self):
        velocity = self.robot.data.root_lin_vel_b
        angular = self.robot.data.root_ang_vel_b
        gravity = self.robot.data.projected_gravity_b
        contacts, heights = self.foot_state()
        phase = self.phase()
        swing, desired_heights, desired_x = gait_targets(
            phase, self.commands[:, 0], self.cfg.gait_period, self.cfg.foot_clearance,
        )
        expected_contacts = ~swing
        tracking = torch.exp(-((velocity[:, :2] - self.commands[:, :2]) / 0.025).square().sum(dim=-1))
        yaw = torch.exp(-((angular[:, 2] - self.commands[:, 2]) / 0.2).square())
        posture = torch.exp(-gravity[:, :2].square().sum(dim=-1) / 0.08)
        contact_match = (contacts == expected_contacts).float().mean(dim=-1)
        clearance = torch.exp(-((heights - desired_heights) / 0.003).square()).mean(dim=-1)
        foot_rotations = self.robot.data.body_quat_w[:, self.foot_ids]
        local_centers = self.corner_offsets.mean(dim=1)[None].expand(self.num_envs, -1, -1)
        centers = self.robot.data.body_pos_w[:, self.foot_ids] + quat_apply(foot_rotations, local_centers)
        relative = quat_apply_inverse(
            self.robot.data.root_quat_w[:, None].expand(-1, 2, -1),
            centers - self.robot.data.root_pos_w[:, None],
        )
        foot_x_error = relative[..., 0] - self.nominal_foot_centers[None, :, 0] - desired_x
        stride = torch.exp(-(foot_x_error / 0.015).square()).mean(dim=-1)
        slip = (self.robot.data.body_lin_vel_w[:, self.foot_ids, :2].square().sum(dim=-1) * contacts).sum(dim=-1)
        height_error = self.robot.data.root_pos_w[:, 2] - self.stance_height
        terms = {
            "tracking": 3.0 * tracking,
            "yaw": 0.5 * yaw - 2.0 * (angular[:, 2] - self.commands[:, 2]).square(),
            "upright": 0.5 * posture,
            "contact": 2.0 * contact_match,
            "clearance": 2.0 * clearance,
            "stride": 2.0 * stride,
            "height": -100.0 * height_error.square(),
            "vertical": -2.0 * velocity[:, 2].square(),
            "angular": -0.03 * angular[:, :2].square().sum(dim=-1),
            "slip": -200.0 * slip,
            "action_rate": -0.02 * (self.actions - self.previous_actions).square().sum(dim=-1),
            "effort": -0.02 * self.robot.data.applied_torque.square().sum(dim=-1),
            "pose": -0.05 * (self.robot.data.joint_pos - self.robot.data.default_joint_pos).square().sum(dim=-1),
        }
        reward = sum(terms.values()) * self.step_dt - self.reset_terminated.float()
        self.episode_returns += reward
        self.last_metrics = {
            "speed": velocity[:, 0].detach(),
            "contacts": contacts.detach(),
            "sole_heights": heights.detach(),
            "upright": (-gravity[:, 2]).detach(),
        }
        self.extras["log"] = {f"Reward/{name}": value.mean() for name, value in terms.items()}
        self.extras["log"]["Metrics/forward_speed"] = velocity[:, 0].mean()
        self.extras["log"]["Metrics/sole_clearance"] = heights.max(dim=-1).values.mean()
        return reward

    def _reset_idx(self, env_ids):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        super()._reset_idx(env_ids)
        positions = self.robot.data.default_joint_pos[env_ids].clone()
        if not self.cfg.evaluation:
            positions += (torch.rand_like(positions) - 0.5) * 0.01
        velocities = torch.zeros_like(positions)
        root = self.robot.data.default_root_state[env_ids].clone()
        root[:, :3] += self.scene.env_origins[env_ids]
        self.robot.write_root_pose_to_sim(root[:, :7], env_ids)
        self.robot.write_root_velocity_to_sim(root[:, 7:], env_ids)
        self.robot.write_joint_state_to_sim(positions, velocities, env_ids=env_ids)
        self.targets[env_ids] = positions
        self.robot.set_joint_position_target(positions, env_ids=env_ids)
        self.actions[env_ids] = 0
        self.previous_actions[env_ids] = 0
        self.commands[env_ids] = 0
        if self.cfg.task == "walk":
            self.commands[env_ids, 0] = self.cfg.speed
            if not self.cfg.evaluation:
                standing = torch.rand(len(env_ids), device=self.device) < 0.15
                self.commands[env_ids[standing], 0] = 0
        self.phase_offsets[env_ids] = 0
        self.episode_returns[env_ids] = 0
