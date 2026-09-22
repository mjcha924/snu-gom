"""Goal rewards; root motion is produced by physics, never by playback."""
import math
import torch
import isaaclab.sim as sim
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv
from isaaclab.sensors import ContactSensor
from snu_bear_motion.contract import CONTRACT as C, SKILLS, JOINTS
from .config import BearEnvCfg

class BearEnv(DirectRLEnv):
    cfg: BearEnvCfg

    def __init__(self, cfg, render_mode=None, **kwargs):
        if abs(cfg.sim.dt*cfg.decimation-1/C["policy_hz"]) > 1e-9:
            raise ValueError("Policy timestep must match contract.json")
        super().__init__(cfg, render_mode, **kwargs)
        self.specification = SKILLS[cfg.skill]
        self.jids, found = self.robot.find_joints(list(JOINTS), preserve_order=True)
        if tuple(found) != JOINTS or self.robot.num_joints != 9:
            raise RuntimeError(f"Unexpected imported joint order: {found}")
        self.paw_ids, _ = self.contacts.find_bodies(".*_lower")
        self.hind_ids, _ = self.contacts.find_bodies(".*_hind_lower")
        self.head_ids, _ = self.contacts.find_bodies("head")
        self.belly_ids, _ = self.contacts.find_bodies("torso")
        if len(self.paw_ids) != 4 or len(self.head_ids) != 1 or len(self.belly_ids) != 1:
            raise RuntimeError("Check imported contact-sensor body paths")
        self.lower = self.tensor(C["q_lower_rad"])
        self.upper = self.tensor(C["q_upper_rad"])
        self.mid, self.half = (self.lower+self.upper)/2, (self.upper-self.lower)/2
        self.goal = C["poses"][self.specification["goal"]]
        self.goal_q = self.tensor(self.goal["q_rad"])
        self.goal_g = self.tensor(self.goal["gravity_body"])
        self.targets = torch.zeros((self.num_envs, 9), device=self.device)
        self.old_targets = self.targets.clone()
        self.history = torch.zeros((self.num_envs, 4, 34), device=self.device)
        self.fresh = torch.ones(self.num_envs, dtype=torch.bool, device=self.device)
        self.command = torch.zeros(self.num_envs, device=self.device)
        self.goal_streak = torch.zeros(self.num_envs, device=self.device)
        self.success = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self.last_success = self.success.clone()
        self.last_travel = torch.zeros(self.num_envs, device=self.device)
        self.last_failure = self.success.clone()
        self._obs_step = -1
        self._cached_obs = None

    def tensor(self, value):
        return torch.tensor(value, device=self.device, dtype=torch.float32)

    def _setup_scene(self):
        self.robot = Articulation(self.cfg.robot_cfg)
        self.contacts = ContactSensor(self.cfg.contacts)
        sim.spawn_ground_plane("/World/ground", sim.GroundPlaneCfg())
        self.scene.clone_environments(copy_from_source=False)
        self.scene.articulations["robot"] = self.robot
        self.scene.sensors["contacts"] = self.contacts
        self.scene.filter_collisions(global_prim_paths=["/World/ground"])
        light = sim.DomeLightCfg(intensity=2000.0)
        light.func("/World/light", light)

    def _pre_physics_step(self, actions):
        self.old_targets.copy_(self.targets)
        desired = self.mid + self.half * actions.clamp(-1.0, 1.0)
        delta = C["target_slew_rad_s"] * self.step_dt
        self.targets = torch.clamp(self.targets + (desired-self.targets).clamp(-delta, delta),
                                   self.lower, self.upper)

    def _apply_action(self):
        self.robot.set_joint_position_target(self.targets, joint_ids=self.jids)

    def _get_observations(self):
        # Repeated reads in one physics step must not consume multiple history slots.
        if self._obs_step == self.common_step_counter and not self.fresh.any():
            return {"policy": self._cached_obs}
        q = self.robot.data.joint_pos[:, self.jids].clone()
        dq = self.robot.data.joint_vel[:, self.jids].clone()
        gyro = self.robot.data.root_ang_vel_b.clone()
        g = self.robot.data.projected_gravity_b.clone()
        if self.cfg.observation_noise:
            q += 0.003 * torch.randn_like(q)
            dq += 0.02 * torch.randn_like(dq)
            gyro += 0.01 * torch.randn_like(gyro)
            g += 0.005 * torch.randn_like(g)
        g = torch.nn.functional.normalize(g, dim=-1)
        frame = torch.cat(((q-self.mid)/self.half, dq*C["velocity_scale"], gyro*C["gyro_scale"],
            g, (self.targets-self.mid)/self.half, self.command[:, None]/C["command_scale_m_s"]), dim=-1)
        self.history = torch.cat((self.history[:, 1:], frame[:, None]), dim=1)
        self.history[self.fresh] = frame[self.fresh, None].expand(-1, 4, -1)
        self.fresh[:] = False
        self._cached_obs = self.history.reshape(self.num_envs, 136).clone()
        self._obs_step = self.common_step_counter
        return {"policy": self._cached_obs}

    def _measure(self):
        q = self.robot.data.joint_pos[:, self.jids]
        dq = self.robot.data.joint_vel[:, self.jids]
        g = self.robot.data.projected_gravity_b
        forces = torch.linalg.vector_norm(self.contacts.data.net_forces_w, dim=-1)
        height = self.robot.data.root_pos_w[:, 2] - self.scene.env_origins[:, 2]
        # Horizontal WORLD X is forward at reset. Body X points down at a 55-degree pitch.
        velocity = self.robot.data.root_lin_vel_w
        return q, dq, g, forces, height, velocity

    def _get_rewards(self):
        q, dq, g, f, height, v = self._measure()
        pose = torch.exp(-((q-self.goal_q)**2).mean(-1)/0.3)
        attitude = torch.exp(-((g-self.goal_g)**2).sum(-1)/0.15)
        elevation = torch.exp(-((height-self.goal["root_height_m"])/0.008)**2)
        gyro_cost = (self.robot.data.root_ang_vel_b**2).sum(-1)
        crawl = self.cfg.skill == "crawl_forward"
        reward = (0.15 if crawl else 2.0)*pose + 2.0*attitude + elevation
        if crawl:
            reward += 3.0*torch.exp(-((v[:, 0]-self.command)/0.006)**2)
            reward -= 20.0*(v[:, 1]**2 + v[:, 2]**2)
            # Belly support is allowed during transitions; crawling should unload it.
            reward -= 0.5*(f[:, self.belly_ids].amax(-1) > 0.1).float()
        else:
            reward += 0.5*torch.exp(-(v**2).sum(-1)/0.0001)
        reward -= 0.03*gyro_cost + 0.001*(dq**2).sum(-1)
        reward -= 0.002*(((self.targets-self.old_targets)/self.step_dt)**2).sum(-1)
        reward -= 0.002*(torch.abs(self.robot.data.applied_torque[:, self.jids]*dq)).sum(-1)
        reward += 1.0*(self.goal_streak >= 0.5).float()
        reward -= 5.0*self.reset_terminated.float()
        return reward*self.step_dt

    def _get_dones(self):
        q, dq, g, f, height, v = self._measure()
        warm = self.episode_length_buf > 5
        head_hit = f[:, self.head_ids].amax(-1) > 1.0
        fallen = (height < 0.023) | (height > 0.22) | (g[:, 2] > 0.3) | (g[:, 1].abs() > 0.85)
        outside = ((q < self.lower-0.03) | (q > self.upper+0.03)).any(-1)
        travel = self.robot.data.root_pos_w[:, 0]-self.scene.env_origins[:, 0]
        lateral = self.robot.data.root_pos_w[:, 1]-self.scene.env_origins[:, 1]
        failed = (fallen | head_hit | outside | (travel.abs() > 0.55) | (lateral.abs() > 0.2)) & warm
        settled = ((q-self.goal_q).abs().amax(-1) < 0.18)
        settled &= (g*self.goal_g).sum(-1) > math.cos(math.radians(8))
        settled &= (height-self.goal["root_height_m"]).abs() < 0.005
        settled &= dq.abs().amax(-1) < 0.3
        settled &= torch.linalg.vector_norm(self.robot.data.root_ang_vel_b, dim=-1) < 0.25
        if self.specification["goal"] == "low":
            settled &= (f[:, self.paw_ids] > 0.05).sum(-1) >= 3
            settled &= f[:, self.belly_ids].amax(-1) < 0.1
        else:
            settled &= (f[:, self.hind_ids] > 0.05).sum(-1) == 2
        settled &= ~failed & warm
        self.goal_streak = torch.where(settled, self.goal_streak+self.step_dt, 0.0)
        if self.cfg.skill == "crawl_forward":
            # Requires measurable forward travel, a low stance, and no current fall.
            moving = (travel > 0.03) & ((v[:, 0]-self.command).abs() < 0.006)
            moving &= (g*self.goal_g).sum(-1) > math.cos(math.radians(12))
            moving &= f[:, self.belly_ids].amax(-1) < 0.1
            self.success |= moving & ~failed
        else:
            self.success |= self.goal_streak >= 0.5
        self.last_success = self.success.clone()
        self.last_travel = travel.clone()
        self.last_failure = failed.clone()
        timeout = self.episode_length_buf >= self.max_episode_length-1
        return failed, timeout

    def _reset_idx(self, env_ids):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        ended = self.episode_length_buf[env_ids] > 0
        if ended.any():
            ids = env_ids[ended]
            self.extras["log"] = {
                "Task/goal_without_failure": (self.last_success[ids] & ~self.last_failure[ids]).float().mean(),
                "Task/forward_travel_m": self.last_travel[ids].mean()}
        super()._reset_idx(env_ids)
        start = C["poses"][self.specification["start"]]
        n = len(env_ids)
        root = self.robot.data.default_root_state[env_ids].clone()
        root[:, :3] = self.scene.env_origins[env_ids]
        root[:, 2] += start["root_height_m"] + 0.001
        root[:, 3:7] = self.tensor(start["quaternion_wxyz"])
        root[:, 7:] = 0.0
        q = self.robot.data.default_joint_pos[env_ids].clone()
        start_q = self.tensor(start["q_rad"]).repeat(n, 1)
        start_q += (torch.rand_like(start_q)*2-1)*self.cfg.reset_joint_noise_rad
        start_q = torch.clamp(start_q, self.lower, self.upper)
        q[:, self.jids] = start_q
        dq = torch.zeros_like(q)
        # The only root-state writes are episode resets. No root forces/trajectories.
        self.robot.write_root_pose_to_sim(root[:, :7], env_ids=env_ids)
        self.robot.write_root_velocity_to_sim(root[:, 7:], env_ids=env_ids)
        self.robot.write_joint_state_to_sim(q, dq, env_ids=env_ids)
        self.robot.set_joint_position_target(q, env_ids=env_ids)
        self.targets[env_ids] = start_q
        self.old_targets[env_ids] = start_q
        self.fresh[env_ids] = True
        self.success[env_ids] = False
        self.goal_streak[env_ids] = 0.0
        if self.cfg.skill == "crawl_forward":
            if self.cfg.command_m_s < 0:
                self.command[env_ids] = 0.003 + 0.017*torch.rand(n, device=self.device)
            else:
                if not 0 <= self.cfg.command_m_s <= 0.02:
                    raise ValueError("command_m_s must be <= 0.02")
                self.command[env_ids] = self.cfg.command_m_s
        else:
            self.command[env_ids] = 0.0
