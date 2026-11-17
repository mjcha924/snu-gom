"""Experimental BAM M1 motor with native Isaac Sim 5 joint friction/inertia."""

from dataclasses import MISSING

import torch

from isaaclab.actuators import ActuatorBase, ActuatorBaseCfg, ImplicitActuatorCfg
from isaaclab.utils import configclass

from .bam import XL330_JOINTS, XC330_JOINTS, motor_torque, validate_motor_mapping, validate_operating_point, validate_parameters
from .model import ROOT


class BamXL330Actuator(ActuatorBase):
    def __init__(self, cfg, *args, **kwargs):
        validate_parameters(cfg.parameters)
        validate_operating_point(cfg.voltage, cfg.firmware_kp)
        super().__init__(cfg, *args, **kwargs)

    def reset(self, env_ids):
        self.computed_effort[env_ids] = 0
        self.applied_effort[env_ids] = 0

    def compute(self, control_action, joint_pos, joint_vel):
        self.computed_effort = motor_torque(
            control_action.joint_positions, joint_pos, joint_vel,
            self.cfg.parameters, self.cfg.voltage, self.cfg.firmware_kp,
        )
        self.applied_effort = self._clip_effort(self.computed_effort)
        control_action.joint_efforts = self.applied_effort
        control_action.joint_positions = None
        control_action.joint_velocities = None
        return control_action


@configclass
class BamXL330ActuatorCfg(ActuatorBaseCfg):
    class_type: type = BamXL330Actuator
    parameters: dict = MISSING
    voltage: float = MISSING
    firmware_kp: float = MISSING


def configure_bam_actuators(cfg, model):
    from isaaclab.utils.version import get_isaac_sim_version

    if get_isaac_sim_version().major < 5:
        raise ValueError("BAM M1 adapter requires Isaac Sim 5 torque-valued joint friction")
    parameters = cfg.bam_parameters
    validate_parameters(parameters)
    validate_operating_point(cfg.bam_voltage, cfg.bam_kp)
    validate_motor_mapping(ROOT / "snu_gom_description/config/joint_parameters.csv")
    if set(model["joints"]) != set(XL330_JOINTS + XC330_JOINTS):
        raise ValueError("Robot joint layout differs; audit actuator assignment before using BAM")
    cfg.robot.actuators = {
        "xc330_provisional": ImplicitActuatorCfg(
            joint_names_expr=XC330_JOINTS, stiffness=cfg.stiffness, damping=cfg.damping,
            effort_limit_sim={name: model["joints"][name]["effort"] for name in XC330_JOINTS},
            velocity_limit_sim={name: model["joints"][name]["velocity"] for name in XC330_JOINTS},
        ),
        "xl330_bam_m1": BamXL330ActuatorCfg(
            joint_names_expr=XL330_JOINTS, parameters=parameters,
            voltage=cfg.bam_voltage, firmware_kp=cfg.bam_kp,
            stiffness=0.0, damping=0.0, armature=parameters["armature"],
            friction=parameters["friction_base"], dynamic_friction=parameters["friction_base"],
            viscous_friction=parameters["friction_viscous"],
            effort_limit={name: model["joints"][name]["effort"] for name in XL330_JOINTS},
            effort_limit_sim={name: model["joints"][name]["effort"] for name in XL330_JOINTS},
            velocity_limit_sim={name: model["joints"][name]["velocity"] for name in XL330_JOINTS},
        ),
    }


def verify_bam_runtime(robot, parameters):
    actuator = robot.actuators["xl330_bam_m1"]
    indices = actuator.joint_indices.cpu()
    view = robot.root_physx_view
    friction = view.get_dof_friction_properties().cpu()[:, indices]
    expected_friction = torch.tensor([
        parameters["friction_base"], parameters["friction_base"], parameters["friction_viscous"],
    ], dtype=friction.dtype).expand_as(friction)
    torch.testing.assert_close(friction, expected_friction)
    armature = view.get_dof_armatures().cpu()[:, indices]
    torch.testing.assert_close(armature, torch.full_like(armature, parameters["armature"]))
    for values in [view.get_dof_stiffnesses(), view.get_dof_dampings()]:
        selected = values.cpu()[:, indices]
        torch.testing.assert_close(selected, torch.zeros_like(selected))
    return {
        "passed": True, "environments": robot.num_instances,
        "bam_joint_names": actuator.joint_names,
        "friction_static_dynamic_viscous": friction[0].tolist(),
        "armature": armature[0].tolist(), "implicit_drives_disabled_on_bam_joints": True,
        "scope": "PhysX parameter wiring, not hardware or cross-engine dynamic validation",
    }
