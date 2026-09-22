"""Isaac Lab 2.3.0 target API. Numerical values need physical calibration."""
import os
from pathlib import Path
import isaaclab.sim as sim
from isaaclab.actuators import DelayedPDActuatorCfg
from isaaclab.assets import ArticulationCfg
from isaaclab.envs import DirectRLEnvCfg, mdp
from isaaclab.managers import EventTermCfg, SceneEntityCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass
from snu_bear_motion.contract import CONTRACT as C, DATA

@configclass
class RandomizationCfg:
    material = EventTermCfg(func=mdp.randomize_rigid_body_material, mode="startup", params={
        "asset_cfg": SceneEntityCfg("robot", body_names=".*"),
        "static_friction_range": (0.5, 1.0), "dynamic_friction_range": (0.4, 0.9),
        "restitution_range": (0.0, 0.05), "num_buckets": 32, "make_consistent": True})
    mass = EventTermCfg(func=mdp.randomize_rigid_body_mass, mode="startup", params={
        "asset_cfg": SceneEntityCfg("robot", body_names=".*"),
        "mass_distribution_params": (0.8, 1.2), "operation": "scale", "recompute_inertia": True})
    gains = EventTermCfg(func=mdp.randomize_actuator_gains, mode="reset", params={
        "asset_cfg": SceneEntityCfg("robot", joint_names=".*"),
        "stiffness_distribution_params": (0.8, 1.2), "damping_distribution_params": (0.8, 1.2),
        "operation": "scale"})

@configclass
class BearEnvCfg(DirectRLEnvCfg):
    skill = "hold_sit"
    decimation = 4
    episode_length_s = 10.0
    action_space = 9
    observation_space = 136
    state_space = 0
    seed = 42
    sim = sim.SimulationCfg(dt=1/C["physics_hz"], render_interval=decimation,
        physics_material=sim.RigidBodyMaterialCfg(static_friction=0.8, dynamic_friction=0.6,
                                                  restitution=0.0))
    scene = InteractiveSceneCfg(num_envs=256, env_spacing=1.5, replicate_physics=True)
    robot_cfg = ArticulationCfg(
        prim_path="/World/envs/env_.*/Robot",
        spawn=sim.UrdfFileCfg(
            asset_path=str(DATA / "robot/snu_bear_v06.urdf"),
            usd_dir=str(Path(os.environ.get("SNU_BEAR_CACHE", "~/.cache/snu_bear")).expanduser()),
            usd_file_name="snu_bear_v06.usd", force_usd_conversion=True,
            fix_base=False, merge_fixed_joints=False, self_collision=True,
            collider_type="convex_decomposition", activate_contact_sensors=True,
            joint_drive=sim.UrdfConverterCfg.JointDriveCfg(
                target_type="none", gains=sim.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(stiffness=0.0, damping=0.0)),
            rigid_props=sim.RigidBodyPropertiesCfg(disable_gravity=False, max_depenetration_velocity=0.1),
            collision_props=sim.CollisionPropertiesCfg(contact_offset=0.00005, rest_offset=0.0),
            articulation_props=sim.ArticulationRootPropertiesCfg(enabled_self_collisions=True,
                solver_position_iteration_count=8, solver_velocity_iteration_count=4)),
        init_state=ArticulationCfg.InitialStateCfg(pos=(0.0, 0.0, 0.053),
            joint_pos=dict(zip(C["joints"], C["poses"]["sit"]["q_rad"])), joint_vel={".*": 0.0}),
        soft_joint_pos_limit_factor=1.0,
        actuators={"motors": DelayedPDActuatorCfg(joint_names_expr=[".*"],
            stiffness=C["kp_nm_per_rad"], damping=C["kd_nm_s_per_rad"],
            effort_limit=C["effort_limit_nm"], effort_limit_sim=C["effort_limit_nm"],
            velocity_limit_sim=1.0, min_delay=0, max_delay=4)})
    contacts = ContactSensorCfg(prim_path="/World/envs/env_.*/Robot/.*", update_period=0.0,
                               history_length=1, track_air_time=False)
    events = RandomizationCfg()
    reset_joint_noise_rad = 0.01
    observation_noise = True
    command_m_s = -1.0  # negative => sample 0.003..0.02 for crawl; other skills use zero

@configclass
class HoldSitCfg(BearEnvCfg):
    skill = "hold_sit"

@configclass
class HoldLowCfg(BearEnvCfg):
    skill = "hold_low"

@configclass
class SitToLowCfg(BearEnvCfg):
    skill = "sit_to_low"
    episode_length_s = 15.0

@configclass
class LowToSitCfg(BearEnvCfg):
    skill = "low_to_sit"
    episode_length_s = 15.0

@configclass
class CrawlForwardCfg(BearEnvCfg):
    skill = "crawl_forward"
    episode_length_s = 20.0
