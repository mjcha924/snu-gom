"""Pinned BAM XL330 M1 parameters and simulator-independent motor equations."""

import csv
import hashlib
import json
import math
from pathlib import Path


BAM_COMMIT = "b9e11118e17fe8ec803d430202f6fcf31d57901e"
BAM_PROFILE_URL = f"https://raw.githubusercontent.com/Rhoban/bam/{BAM_COMMIT}/bam/params/xl330/m1.json"
BAM_PROFILE_SHA256 = "3774df0ea9e329b9e1ae6b1debb18d701d674a84006def89e23f90e38883acf2"
BAM_PARAMETERS_SHA256 = "8716ab166568165205d18616f651892707a25b6e08ea2aadf6c93e37b8ae13f7"
XL330_ERROR_GAIN = 4096 / (2 * math.pi * 256 * 885)
XC330_JOINTS = [f"{side}_{joint}_joint" for side in ["left", "right"] for joint in ["hip_pitch", "knee_pitch"]]
XL330_JOINTS = [f"{side}_{joint}_joint" for side in ["left", "right"] for joint in ["hip_yaw", "hip_roll", "ankle_pitch"]]
XL330_JOINTS += ["neck_yaw_joint", "neck_pitch_joint"]


def validate_parameters(parameters):
    digest = hashlib.sha256(json.dumps(parameters, sort_keys=True).encode()).hexdigest()
    if digest != BAM_PARAMETERS_SHA256:
        raise ValueError("Expected the pinned BAM XL330 M1 profile; other motors/fits require explicit validation")


def load_profile(path):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != BAM_PROFILE_SHA256:
        raise ValueError("BAM profile checksum differs from the pinned upstream file")
    parameters = json.loads(data)
    validate_parameters(parameters)
    return parameters


def validate_operating_point(voltage, firmware_kp):
    if voltage is None or not math.isfinite(voltage) or not 3.7 <= voltage <= 6.0:
        raise ValueError("Explicit XL330 supply voltage must be within 3.7–6.0 V")
    if firmware_kp is None or not math.isfinite(firmware_kp) or not 0 < firmware_kp <= 16383:
        raise ValueError("Explicit positive firmware P gain is required (at most 16383)")


def validate_motor_mapping(path):
    with Path(path).open(newline="") as stream:
        actual = {row["joint"]: row["motor_model"] for row in csv.DictReader(stream)}
    expected = {name: "XL330-M288-T" for name in XL330_JOINTS}
    expected.update({name: "XC330-M288-T" for name in XC330_JOINTS})
    if actual != expected:
        raise ValueError("Joint/motor table changed; audit BAM assignment before proceeding")


def motor_torque(target, position, velocity, parameters, voltage, firmware_kp):
    duty = ((target - position) * firmware_kp * XL330_ERROR_GAIN).clamp(-1.0, 1.0)
    torque_constant = parameters["kt"]
    return torque_constant * (voltage * duty - torque_constant * velocity) / parameters["R"]


def add_bam_arguments(parser):
    parser.add_argument("--actuator-model", choices=["implicit", "bam-xl330-m1"], default="implicit")
    parser.add_argument("--bam-profile", type=Path)
    parser.add_argument("--bam-voltage", type=float)
    parser.add_argument("--bam-kp", type=float)


def bam_settings(args):
    if args.actuator_model == "implicit":
        if any(value is not None for value in [args.bam_profile, args.bam_voltage, args.bam_kp]):
            raise ValueError("BAM options require --actuator-model bam-xl330-m1")
        return {"actuator_model": "implicit", "bam_parameters": None, "bam_voltage": None, "bam_kp": None}
    validate_operating_point(args.bam_voltage, args.bam_kp)
    if args.bam_profile is None:
        raise ValueError("Fetch a pinned profile and provide --bam-profile")
    return {
        "actuator_model": args.actuator_model, "bam_parameters": load_profile(args.bam_profile),
        "bam_voltage": args.bam_voltage, "bam_kp": args.bam_kp,
    }


def provenance():
    return {
        "upstream_commit": BAM_COMMIT, "profile_url": BAM_PROFILE_URL,
        "profile_sha256": BAM_PROFILE_SHA256, "model": "xl330/m1",
        "adapter": "experimental_isaac_physx_not_upstream_backend",
        "hardware_calibrated": False, "xc330_identified": False,
        "q_offset_applied": False, "command_delay_applied": False,
    }
