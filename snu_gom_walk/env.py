"""Floating-base SNU-GOM environment for the installed Isaac Lab runtime."""

import math

import torch

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg, IdealPDActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.envs import DirectRLEnv, DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensor, ContactSensorCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import quat_apply, quat_apply_inverse

from .model import ALL_JOINTS, FOOT_LINKS, LEG_JOINTS, ROOT, URDF, audit_model, stance_configuration
from .gait import gait_targets
from .stepping import TouchdownTracker, reference_tracking_reward, supported_lift_rewards


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
    reference_assistance = False
    motion_manifest = ''
    motion_allow_kinematic = None
    motion_require_dynamics = False
    motion_split = 'train'
    motion_manifest_sha256 = ''
    motion_model_id = ''
    reference_kind = "ik"
    reference_lean = 0.20
    reference_reward_weight = 3.0
    dense_lift_rewards = False
    reference_swing_fraction = 0.35
    reference_knee_amplitude = 0.25
    reference_speed_scale = 1.0
    reference_roll_pulse = False
    stiffness = 4.0
    damping = 0.08
    actuator_model = "implicit"
    bam_parameters = None
    bam_voltage = None
    bam_kp = None
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
        if cfg.motion_manifest:
            cfg.observation_space=72;cfg.state_space=90
            cfg.reference_kind='library';cfg.reference_assistance=True
        positions, height, centers = stance_configuration(cfg.stance_knee, MODEL)
        cfg.robot.init_state.joint_pos = positions
        cfg.robot.init_state.pos = (0.0, 0.0, height + 0.003)
        reference = None
        if cfg.reference_assistance and not cfg.motion_manifest:
            if cfg.reference_kind == "support":
                from .support_reference import build_support_seed

                reference = build_support_seed(
                    period=cfg.gait_period, speed=cfg.speed * cfg.reference_speed_scale, lean=cfg.reference_lean,
                    swing_fraction=cfg.reference_swing_fraction, knee_amplitude=cfg.reference_knee_amplitude,
                    roll_pulse=cfg.reference_roll_pulse,
                )
                geometry_valid = reference["position_limits_passed"]
            elif cfg.reference_kind == "ik":
                from .reference import build_reference

                reference = build_reference(period=cfg.gait_period, speed=cfg.speed, clearance=cfg.foot_clearance, lean=cfg.reference_lean)
                geometry_valid = reference["max_position_error_m"] <= 0.002
            else:
                raise ValueError("Unknown reference kind")
            if not reference["velocity_limits_passed"] or not geometry_valid:
                raise ValueError("Reference fails joint-speed or foot-placement feasibility checks")
        self.motion_motor_parameters=None
        if cfg.motion_manifest:
            if cfg.actuator_model!='implicit':raise ValueError('Library mode uses explicit bounded PD efforts; BAM remains a separate actuator experiment')
            from .motion_pipeline.library import load_library
            selected,_,selected_clips=load_library(ROOT/cfg.motion_manifest,kind=cfg.task,split=cfg.motion_split,
                                     allow_kinematic=cfg.motion_allow_kinematic,require_dynamics=cfg.motion_require_dynamics,urdf=URDF)
            from .motion_pipeline.motors import motor_rows
            params=dict(zip(ALL_JOINTS,motor_rows(selected.profile,ALL_JOINTS)))
            caps={n:float(selected.effort[selected.names.index(n)]) for n in ALL_JOINTS}
            speeds={n:float(selected.speed[selected.names.index(n)]) for n in ALL_JOINTS}
            self.motion_motor_parameters=(params,caps)
            cfg.robot.actuators={'library_effort':IdealPDActuatorCfg(joint_names_expr=ALL_JOINTS,
                stiffness=0.,damping=0.,effort_limit=caps,effort_limit_sim=caps,
                velocity_limit_sim=speeds)}
            cfg.episode_length_s=max(cfg.episode_length_s,max(float(a['time'][-1]) for _,a in selected_clips)+cfg.sim.dt*cfg.decimation)
        elif cfg.actuator_model == "bam-xl330-m1":
            from .bam_actuator import configure_bam_actuators

            configure_bam_actuators(cfg, MODEL)
        elif cfg.actuator_model == "implicit":
            cfg.robot.actuators["legs"].stiffness = cfg.stiffness
            cfg.robot.actuators["legs"].damping = cfg.damping
        else:
            raise ValueError("Unknown actuator model")
        super().__init__(cfg, render_mode, **kwargs)
        self.bam_audit = None
        if cfg.actuator_model == "bam-xl330-m1":
            from .bam_actuator import verify_bam_runtime

            self.bam_audit = verify_bam_runtime(self.robot, cfg.bam_parameters)
        self.leg_ids, names = self.robot.find_joints(LEG_JOINTS, preserve_order=True)
        assert names == LEG_JOINTS
        self.obs_ids, names = self.robot.find_joints(ALL_JOINTS, preserve_order=True)
        assert names == ALL_JOINTS
        self.foot_ids, _ = self.robot.find_bodies(FOOT_LINKS, preserve_order=True)
        self.contact_foot_ids, _ = self.contacts.find_bodies(FOOT_LINKS, preserve_order=True)
        self.nonfoot_ids = [index for index, name in enumerate(self.contacts.body_names) if name not in FOOT_LINKS]
        self.scales = torch.tensor([0.15, 0.32, 0.65, 0.95, 0.40] * 2, device=self.device)
        self.reference_report = reference
        self.reference_table = None
        self.motion_bank = None
        if cfg.motion_manifest:
            from .motion_pipeline.bank import MotionBank
            self.motion_bank=MotionBank(ROOT/cfg.motion_manifest,ALL_JOINTS,device=self.device,kind=cfg.task,
                                       split=cfg.motion_split,allow_kinematic=cfg.motion_allow_kinematic,require_dynamics=cfg.motion_require_dynamics,urdf=URDF)
            self.motion_ids=torch.zeros(self.num_envs,dtype=torch.long,device=self.device)
            self.motion_sole_offsets=self.motion_bank.sole_points_link
            self.motion_evaluation_cursor=0
            params,caps=self.motion_motor_parameters
            self.motion_stall=torch.tensor([params[n]['stall_nm'] for n in ALL_JOINTS],device=self.device)
            self.motion_no_load=torch.tensor([params[n]['no_load_rad_s'] for n in ALL_JOINTS],device=self.device)
            self.motion_effort_cap=torch.tensor([caps[n] for n in ALL_JOINTS],device=self.device)
            from .motion_pipeline.motors import curve_arrays
            curve_speed,curve_torque=curve_arrays(selected.profile,ALL_JOINTS)
            self.motion_curve_speed=torch.tensor(curve_speed,dtype=torch.float32,device=self.device)
            self.motion_curve_torque=torch.tensor(curve_torque,dtype=torch.float32,device=self.device)
            self.motion_leg_indices=[ALL_JOINTS.index(n) for n in LEG_JOINTS]
            self.motion_neck_indices=[ALL_JOINTS.index(n) for n in ['neck_yaw_joint','neck_pitch_joint']]
            self.motion_speeds=torch.tensor([e['parameters']['speed_m_s'] if e['kind']=='walk' else 0. for e in self.motion_bank.entries],device=self.device)
            self.reference_report={'kind':'versioned_motion_library','model_id':self.motion_bank.model_id,
                                   'split':cfg.motion_split,'clips':[e['id'] for e in self.motion_bank.entries],
                                   'allow_kinematic':cfg.motion_allow_kinematic,'require_dynamics':cfg.motion_require_dynamics,'finite_clips':True}
            self.scales=torch.tensor([.08,.16,.25,.30,.20]*2,device=self.device)
        if reference is not None:
            self.reference_table = torch.tensor([row["joints"] for row in reference["rows"]], device=self.device)
            if cfg.reference_kind == "support":
                self.reference_heights = torch.tensor([row["sole_heights"] for row in reference["rows"]], device=self.device).clamp_min(0)
                self.reference_foot_x = torch.tensor([row["foot_x_offsets"] for row in reference["rows"]], device=self.device)
            self.scales = torch.tensor([0.08, 0.16, 0.25, 0.30, 0.20] * 2, device=self.device)
        self.stance_height = height
        self.nominal_foot_centers = torch.tensor([centers[name] for name in FOOT_LINKS], device=self.device)
        points=[MODEL['foot_corners'][name] for name in FOOT_LINKS];count=max(len(p) for p in points)
        self.center_offsets=torch.tensor([[sum(p[axis] for p in rows)/len(rows) for axis in range(3)] for rows in points],device=self.device)
        self.corner_offsets=torch.tensor([p+[p[-1]]*(count-len(p)) for p in points],device=self.device)
        self.corner_mask=torch.tensor([[i<len(p) for i in range(count)] for p in points],device=self.device)
        self.actions = torch.zeros(self.num_envs, 10, device=self.device)
        self.previous_actions = self.actions.clone()
        self.second_previous_actions = self.actions.clone()
        self.motion_previous_targets = self.robot.data.default_joint_pos.clone()
        self.motion_substep = 0
        self.targets = self.robot.data.default_joint_pos.clone()
        self.commands = torch.zeros(self.num_envs, 3, device=self.device)
        self.phase_offsets = torch.zeros(self.num_envs, device=self.device)
        self.episode_returns = torch.zeros(self.num_envs, device=self.device)
        self.last_metrics = {}
        self.last_terminal = {}
        self.touchdowns = TouchdownTracker(self.num_envs, self.step_dt, self.device)

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
        self.second_previous_actions.copy_(self.previous_actions)
        self.previous_actions.copy_(self.actions)
        self.motion_previous_targets.copy_(self.targets);self.motion_substep=0
        baseline = self.reference_positions()
        desired = baseline + actions.clamp(-1, 1) * self.scales
        limits = self.robot.data.soft_joint_pos_limits[:, self.leg_ids]
        desired = torch.clamp(desired, limits[..., 0], limits[..., 1])
        previous = self.targets[:, self.leg_ids]
        max_change = self.robot.data.joint_vel_limits[:, self.leg_ids] * self.step_dt
        self.targets[:, self.leg_ids] = previous + torch.clamp(desired - previous, -max_change, max_change)
        self.actions = (self.targets[:, self.leg_ids] - baseline) / self.scales
        if self.motion_bank is not None:
            ref=self.motion_reference()
            self.targets[:,self.obs_ids[-2:]]=ref['joints_pos'][:,self.motion_neck_indices]

    def reference_positions(self):
        neutral = self.robot.data.default_joint_pos[:, self.leg_ids]
        if self.motion_bank is not None:
            return self.motion_reference()['joints_pos'][:,self.motion_leg_indices]
        if self.reference_table is None:
            return neutral
        reference = self.reference_values(self.reference_table)
        ramp = (self.episode_length_buf * self.step_dt / 2.0).clamp(0, 1)[:, None]
        reference = torch.lerp(neutral, reference, ramp)
        return torch.where(self.commands[:, :1] > 0.005, reference, neutral)

    def motion_reference(self):
        return self.motion_bank.sample(self.motion_ids,self.episode_length_buf*self.step_dt)

    def reference_values(self, table):
        coordinate = self.phase() * len(table)
        index = coordinate.long() % len(table)
        fraction = (coordinate - coordinate.floor())[:, None]
        return torch.lerp(table[index], table[(index + 1) % len(table)], fraction)

    def _apply_action(self):
        if self.motion_bank is not None:
            self.motion_substep+=1
            target=torch.lerp(self.motion_previous_targets,self.targets,min(self.motion_substep/self.cfg.decimation,1.))
            velocity=self.robot.data.joint_vel[:,self.obs_ids]
            request=self.cfg.stiffness*(target[:,self.obs_ids]-self.robot.data.joint_pos[:,self.obs_ids])-self.cfg.damping*velocity
            cap=torch.minimum(self.motion_effort_cap,self.motion_stall*(1-velocity.abs()/self.motion_no_load).clamp_min(0))
            from .motion_pipeline.motors import torch_curve_cap
            cap=torch.minimum(cap,torch_curve_cap(velocity,self.motion_curve_speed,self.motion_curve_torque))
            self.robot.set_joint_effort_target(request.clamp(-cap,cap),joint_ids=self.obs_ids)
        else:self.robot.set_joint_position_target(self.targets)

    def phase(self):
        if self.motion_bank is not None:
            return torch.remainder(self.motion_reference()['phase'],1.0)
        phase = self.episode_length_buf * self.step_dt / self.cfg.gait_period + self.phase_offsets
        return torch.remainder(phase, 1.0)

    def foot_corners_world(self):
        count=self.corner_offsets.shape[1]
        rotations = self.robot.data.body_quat_w[:, self.foot_ids, None, :].expand(-1, -1, count, -1)
        corners = self.corner_offsets[None].expand(self.num_envs, -1, -1, -1)
        world = quat_apply(rotations.reshape(-1, 4), corners.reshape(-1, 3)).reshape(self.num_envs, 2, count, 3)
        world += self.robot.data.body_pos_w[:, self.foot_ids, None, :]
        return world

    def foot_state(self):
        forces = self.contacts.data.net_forces_w[:, self.contact_foot_ids]
        contacts = torch.linalg.vector_norm(forces, dim=-1) > 0.3
        world = self.foot_corners_world()
        heights = world[..., 2].min(dim=-1).values
        return contacts, heights

    def _get_observations(self):
        phase = self.phase() * (2 * math.pi)
        clock = torch.stack((phase.sin(), phase.cos()), dim=-1)
        if self.reference_table is not None:
            clock *= (self.episode_length_buf * self.step_dt / 2.0).clamp(0, 1)[:, None]
        if self.motion_bank is None:
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
        if self.motion_bank is not None:
            from .motion_pipeline.bank import observation_features
            policy=torch.cat([policy,observation_features(self.motion_reference(),self.motion_leg_indices,self.motion_neck_indices)],dim=-1)
        contacts, heights = self.foot_state()
        critic = torch.cat([
            policy, self.robot.data.root_link_lin_vel_b if self.motion_bank is not None else self.robot.data.root_lin_vel_b,
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
        if self.motion_bank is not None:
            timeout |= self.episode_length_buf*self.step_dt >= self.motion_bank.duration[self.motion_ids]-self.step_dt
        self.last_terminal = {
            "position": self.robot.data.root_pos_w.detach().clone(),
            "velocity": (self.robot.data.root_link_lin_vel_b if self.motion_bank is not None else self.robot.data.root_lin_vel_b).detach().clone(),
            "fallen": fallen.detach().clone(),
            "quaternion": self.robot.data.root_quat_w.detach().clone(),
            "foot_positions": self.robot.data.body_pos_w[:, self.foot_ids].detach().clone(),
            "joint_velocities": self.robot.data.joint_vel.detach().clone(),
            "torques": self.robot.data.applied_torque.detach().clone(),
            "body_contact_forces": self.contacts.data.net_forces_w.detach().clone(),
        }
        return fallen, timeout

    def _get_rewards(self):
        velocity = self.robot.data.root_link_lin_vel_b if self.motion_bank is not None else self.robot.data.root_lin_vel_b
        angular = self.robot.data.root_ang_vel_b
        gravity = self.robot.data.projected_gravity_b
        contacts, heights = self.foot_state()
        phase = self.phase()
        swing, desired_heights, desired_x = gait_targets(
            phase, self.commands[:, 0], self.cfg.gait_period, self.cfg.foot_clearance,
        )
        if self.reference_table is not None and self.cfg.reference_kind == "support":
            ramp = (self.episode_length_buf * self.step_dt / 2.0).clamp(0, 1)[:, None]
            moving = self.commands[:, :1] > 0.005
            desired_heights = self.reference_values(self.reference_heights) * ramp * moving
            desired_x = self.reference_values(self.reference_foot_x) * ramp * moving
            swing = desired_heights > 0.002
        expected_contacts = ~swing
        if self.motion_bank is not None:
            reference=self.motion_reference()
            expected_contacts=reference['planned_contacts'].bool();swing=~expected_contacts
            desired_heights=reference['sole_heights']
            desired_x=reference['foot_positions_body'][...,0]-self.nominal_foot_centers[None,:,0]
        tracking = torch.exp(-((velocity[:, :2] - self.commands[:, :2]) / 0.025).square().sum(dim=-1))
        yaw = torch.exp(-((angular[:, 2] - self.commands[:, 2]) / 0.2).square())
        posture = torch.exp(-gravity[:, :2].square().sum(dim=-1) / 0.08)
        contact_match = (contacts == expected_contacts).float().mean(dim=-1)
        clearance = torch.exp(-((heights - desired_heights) / 0.003).square()).mean(dim=-1)
        foot_rotations = self.robot.data.body_quat_w[:, self.foot_ids]
        offsets=self.motion_sole_offsets if self.motion_bank is not None else self.center_offsets
        local_centers = offsets[None].expand(self.num_envs, -1, -1)
        centers = self.robot.data.body_pos_w[:, self.foot_ids] + quat_apply(foot_rotations, local_centers)
        relative = quat_apply_inverse(
            self.robot.data.root_quat_w[:, None].expand(-1, 2, -1),
            centers - self.robot.data.root_pos_w[:, None],
        )
        foot_x_error = relative[..., 0] - self.nominal_foot_centers[None, :, 0] - desired_x
        stride = torch.exp(-(foot_x_error / 0.015).square()).mean(dim=-1)
        slip = (self.robot.data.body_lin_vel_w[:, self.foot_ids, :2].square().sum(dim=-1) * contacts).sum(dim=-1)
        if self.reference_table is not None or self.motion_bank is not None:
            corners = self.foot_corners_world()
            lowest = corners[..., 2].amin(dim=-1, keepdim=True)
            mask = ((corners[..., 2] < lowest + 0.001)&self.corner_mask[None]).float()
            point = (corners * mask[..., None]).sum(dim=-2) / mask.sum(dim=-1, keepdim=True)
            offset = point - self.robot.data.body_com_pos_w[:, self.foot_ids]
            point_velocity = self.robot.data.body_com_lin_vel_w[:, self.foot_ids] + torch.cross(
                self.robot.data.body_com_ang_vel_w[:, self.foot_ids], offset, dim=-1,
            )
            slip = (point_velocity[..., :2].square().sum(dim=-1) * contacts).sum(dim=-1)
        height_error = self.robot.data.root_pos_w[:, 2] - self.stance_height
        if self.motion_bank is not None:
            height_error=self.robot.data.root_pos_w[:,2]-reference['root_pos'][:,2]
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
        if self.reference_table is not None or self.motion_bank is not None:
            terms["reference"] = reference_tracking_reward(
                self.robot.data.joint_pos[:, self.leg_ids], self.reference_positions(), self.cfg.reference_reward_weight,
            )
            terms["slip"] = -30.0 * slip
            terms["clearance"] = 4.0 * (torch.exp(-((heights - desired_heights) / 0.003).square()) * swing).sum(dim=-1)
        if self.motion_bank is not None:
            orientation=(self.robot.data.root_quat_w*reference['root_quat']).sum(-1).square().clamp(0,1)
            terms['reference_orientation']=torch.exp(-20*(1-orientation))
            terms['reference_velocity']=.1*torch.exp(-.1*(self.robot.data.joint_vel[:,self.obs_ids]-reference['joints_vel']).square().mean(-1))
            terms['action_acceleration']=-.02*(self.actions-2*self.previous_actions+self.second_previous_actions).square().sum(-1)
        if self.cfg.dense_lift_rewards:
            vertical_forces = self.contacts.data.net_forces_w[:, self.contact_foot_ids, 2]
            lift, unloading = supported_lift_rewards(
                heights, desired_heights, vertical_forces, MODEL["mass_kg"] * 9.81,
                self.commands[:, 0] > 0.005,
            )
            stable = (-gravity[:, 2] > 0.9) & ~self.reset_terminated
            terms["clearance"] = 4.0 * lift * stable
            terms["unloading"] = 2.0 * unloading * stable
        moving=self.commands[:,0]>.005 if self.motion_bank is None else torch.full((self.num_envs,),self.cfg.task=='walk',device=self.device,dtype=torch.bool)
        touchdown, alternating = self.touchdowns.update(
            contacts, heights, moving, self.reset_terminated,
        )
        reward = sum(terms.values()) * self.step_dt - self.reset_terminated.float()
        self.episode_returns += reward
        self.last_metrics = {
            "speed": velocity[:, 0].detach(),
            "contacts": contacts.detach(),
            "sole_heights": heights.detach(),
            "upright": (-gravity[:, 2]).detach(),
            "qualified_touchdowns": touchdown.detach(),
            "alternating_touchdowns": alternating.detach(),
        }
        self.extras["log"] = {f"Reward/{name}": value.mean() for name, value in terms.items()}
        self.extras["log"]["Metrics/forward_speed"] = velocity[:, 0].mean()
        self.extras["log"]["Metrics/sole_clearance"] = heights.max(dim=-1).values.mean()
        self.extras["log"]["Metrics/qualified_touchdowns"] = touchdown.float().sum(dim=-1).mean()
        self.extras["log"]["Metrics/alternating_touchdowns"] = alternating.float().mean()
        return reward

    def _reset_idx(self, env_ids):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        super()._reset_idx(env_ids)
        self.touchdowns.reset(env_ids)
        positions = self.robot.data.default_joint_pos[env_ids].clone()
        if not self.cfg.evaluation:
            positions += (torch.rand_like(positions) - 0.5) * 0.01
        velocities = torch.zeros_like(positions)
        root = self.robot.data.default_root_state[env_ids].clone()
        if self.motion_bank is not None:
            if self.cfg.evaluation:
                self.motion_ids[env_ids]=(torch.arange(len(env_ids),device=self.device)+self.motion_evaluation_cursor)%len(self.motion_bank.entries)
                self.motion_evaluation_cursor=(self.motion_evaluation_cursor+len(env_ids))%len(self.motion_bank.entries)
            else:
                self.motion_ids[env_ids]=torch.randint(len(self.motion_bank.entries),(len(env_ids),),device=self.device)
            ref=self.motion_bank.sample(self.motion_ids[env_ids],torch.zeros(len(env_ids),device=self.device))
            positions[:,self.obs_ids]=ref['joints_pos'];velocities[:,self.obs_ids]=ref['joints_vel']
            root[:,:3]=ref['root_pos'];root[:,3:7]=ref['root_quat']
            root[:,7:10]=ref['world_linear_vel'];root[:,10:13]=ref['world_angular_vel']
        root[:, :3] += self.scene.env_origins[env_ids]
        self.robot.write_root_pose_to_sim(root[:, :7], env_ids)
        if self.motion_bank is not None:self.robot.write_root_link_velocity_to_sim(root[:,7:],env_ids)
        else:self.robot.write_root_velocity_to_sim(root[:, 7:], env_ids)
        self.robot.write_joint_state_to_sim(positions, velocities, env_ids=env_ids)
        self.targets[env_ids] = positions
        self.robot.set_joint_position_target(positions, env_ids=env_ids)
        self.actions[env_ids] = 0
        self.previous_actions[env_ids] = 0
        self.second_previous_actions[env_ids] = 0
        self.motion_previous_targets[env_ids] = positions
        self.commands[env_ids] = 0
        if self.cfg.task == "walk":
            self.commands[env_ids, 0] = self.cfg.speed
            if not self.cfg.evaluation and self.motion_bank is None:
                standing = torch.rand(len(env_ids), device=self.device) < 0.15
                self.commands[env_ids[standing], 0] = 0
        if self.motion_bank is not None:self.commands[env_ids,0]=self.motion_speeds[self.motion_ids[env_ids]]
        self.phase_offsets[env_ids] = 0
        self.episode_returns[env_ids] = 0
