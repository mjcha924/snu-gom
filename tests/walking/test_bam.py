import argparse
import copy
import json
from pathlib import Path
import tempfile
import unittest

import torch

from snu_gom_walk.bam import (
    XL330_ERROR_GAIN, XL330_JOINTS, XC330_JOINTS, add_bam_arguments,
    bam_settings, load_profile, motor_torque, validate_motor_mapping, validate_operating_point, validate_parameters,
)
from snu_gom_walk.model import ALL_JOINTS


PARAMETERS = {
    "kt": 0.37062307455549115,
    "R": 3.452252366570699,
    "armature": 0.001609112468267143,
    "q_offset": 0.023520136285463317,
    "command_delay": 0.005934804684998987,
    "friction_base": 0.01909359679968616,
    "friction_viscous": 0.003923501485844748,
    "model": "m1",
    "actuator": "xl330",
}


class BamTests(unittest.TestCase):
    def test_joint_assignment(self):
        self.assertEqual(set(XL330_JOINTS + XC330_JOINTS), set(ALL_JOINTS))
        self.assertFalse(set(XL330_JOINTS) & set(XC330_JOINTS))
        self.assertEqual(len(XL330_JOINTS), 8)
        self.assertEqual(len(XC330_JOINTS), 4)
        self.assertTrue(all("hip_pitch" in name or "knee_pitch" in name for name in XC330_JOINTS))
        validate_motor_mapping(Path(__file__).resolve().parents[2] / "snu_gom_description/config/joint_parameters.csv")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "motors.csv"
            path.write_text("joint,motor_model\nleft_hip_pitch_joint,XL330-M288-T\n")
            with self.assertRaises(ValueError):
                validate_motor_mapping(path)

    def test_profile_guard(self):
        validate_parameters(PARAMETERS)
        for key, value in [("actuator", "xc330"), ("model", "m6"), ("kt", 0.8)]:
            changed = copy.deepcopy(PARAMETERS)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_parameters(changed)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text(json.dumps(PARAMETERS))
            with self.assertRaisesRegex(ValueError, "checksum"):
                load_profile(path)

    def test_operating_point_guard(self):
        validate_operating_point(5.0, 400)
        for voltage, gain in [(None, 400), (7.5, 400), (3.6, 400), (float("nan"), 400), (5, None), (5, 0), (5, float("inf"))]:
            with self.subTest(voltage=voltage, gain=gain), self.assertRaises(ValueError):
                validate_operating_point(voltage, gain)

    def test_no_silent_enable(self):
        parser = argparse.ArgumentParser()
        add_bam_arguments(parser)
        self.assertEqual(bam_settings(parser.parse_args([]))["actuator_model"], "implicit")
        for arguments in [["--bam-voltage", "5"], ["--actuator-model", "bam-xl330-m1"]]:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                bam_settings(parser.parse_args(arguments))

    def test_electrical_equation_pwm_and_back_emf(self):
        target = torch.tensor([0.0, 0.1, -0.1, 20, -20], dtype=torch.float64)
        velocity = torch.tensor([0.0, 0.2, -0.2, 1, -1], dtype=torch.float64)
        actual = motor_torque(target, torch.zeros_like(target), velocity, PARAMETERS, 5, 400)
        expected = [
            PARAMETERS["kt"] * (5 * max(-1, min(1, float(goal) * 400 * XL330_ERROR_GAIN)) - PARAMETERS["kt"] * float(speed)) / PARAMETERS["R"]
            for goal, speed in zip(target, velocity)
        ]
        torch.testing.assert_close(actual, torch.tensor(expected, dtype=torch.float64))
        torch.testing.assert_close(actual[1::2], -actual[2::2])
        self.assertEqual(float(actual[0]), 0.0)
        braking = motor_torque(torch.zeros_like(target), torch.zeros_like(target), velocity, PARAMETERS, 5, 400)
        self.assertTrue((braking * velocity <= 0).all())

    def test_batch_and_cuda_equivalence(self):
        generator = torch.Generator().manual_seed(42)
        target = torch.randn(64, 8, generator=generator)
        position = torch.randn(64, 8, generator=generator)
        velocity = torch.randn(64, 8, generator=generator)
        expected = motor_torque(target, position, velocity, PARAMETERS, 5, 400)
        self.assertEqual(expected.shape, (64, 8))
        self.assertTrue(torch.isfinite(expected).all())
        if torch.cuda.is_available():
            actual = motor_torque(target.cuda(), position.cuda(), velocity.cuda(), PARAMETERS, 5, 400)
            torch.testing.assert_close(actual.cpu(), expected)


if __name__ == "__main__":
    unittest.main()
