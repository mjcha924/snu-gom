"""Regression checks for portable data and explicit failure modes."""

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import numpy as np
import torch

from snu_gom_walk.motion_pipeline.bank import MotionBank
from snu_gom_walk.motion_pipeline.contract import (
    validate_contract,
    validate_training_adapter,
)
from snu_gom_walk.motion_pipeline.feasibility import screen_reference
from snu_gom_walk.motion_pipeline.generate import generate
from snu_gom_walk.motion_pipeline.library import build, source_hashes
from snu_gom_walk.motion_pipeline.model import ROOT, RobotModel, write_json
from snu_gom_walk.motion_pipeline.motors import (
    curve_arrays,
    torque_envelope,
    torch_curve_cap,
)
from snu_gom_walk.motion_pipeline.physics import sample
from snu_gom_walk.motion_pipeline.validate import validate_arrays
from test_pipeline import fixture


class ContractTests(unittest.TestCase):
    def test_source_fingerprints_ignore_checkout_newlines_but_detect_code_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "generate.py"
            source.write_bytes(b"def f():\n    return 1\n")
            original = source_hashes(directory)
            source.write_bytes(b"def f():\r\n    return 1\r\n")
            self.assertEqual(original, source_hashes(directory))
            source.write_bytes(b"def f():\n    return 2\n")
            self.assertNotEqual(original, source_hashes(directory))

    @classmethod
    def setUpClass(cls):
        cls.robot = RobotModel()
        cls.arrays, _ = generate(cls.robot, "stand", seconds=2, fps=10)

    def test_missing_fields_have_actionable_errors(self):
        for field in [
            "world_linear_vel",
            "phase",
            "foot_positions_body",
            "sole_points_link",
        ]:
            arrays = dict(self.arrays)
            del arrays[field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                validate_contract(arrays, self.robot.names, self.robot.model_id)

    def test_time_and_quaternion_conventions_are_enforced(self):
        edits = {
            "time": self.arrays["time"] + 1.0,
            "fps": np.asarray(-10),
            "quaternion_order": np.asarray("wxyz"),
            "root_quat": self.arrays["root_quat"] * 2,
            "sole_points_link": np.zeros((1, 3)),
        }
        for key, value in edits.items():
            with self.subTest(field=key), self.assertRaises(ValueError):
                validate_contract(
                    dict(self.arrays, **{key: value}),
                    self.robot.names,
                    self.robot.model_id,
                )

    def test_flight_and_nonbinary_contacts_fail_before_geometry(self):
        for value in [0.0, 0.5, -1.0]:
            contacts = self.arrays["planned_contacts"].astype(float)
            contacts[4] = value
            with self.subTest(value=value), self.assertRaisesRegex(
                ValueError, "Contacts"
            ):
                validate_arrays(
                    self.robot, dict(self.arrays, planned_contacts=contacts)
                )

    def test_root_velocity_and_body_coordinates_are_checked(self):
        for field, check in [
            ("world_linear_vel", "stored_root_velocities_consistent"),
            ("world_angular_vel", "stored_root_velocities_consistent"),
            ("foot_positions_body", "body_foot_coordinates_consistent"),
        ]:
            arrays = dict(self.arrays, **{field: self.arrays[field] + 0.1})
            report, _ = validate_arrays(self.robot, arrays)
            with self.subTest(field=field):
                self.assertFalse(report["passed"])
                self.assertFalse(report["checks"][check])

    def test_endpoint_contacts_match_final_state_in_both_samplers(self):
        with tempfile.TemporaryDirectory() as directory:
            path, arrays = fixture(directory)
            bank = MotionBank(path, self.robot.names, kind="stand")
            # A discrete final-frame change exposes the old N-2 indexing bug.
            bank.data["planned_contacts"][0, -1] = torch.tensor([0.0, 1.0])
            arrays["planned_contacts"][-1] = [0, 1]
            for time in [2.0, 100.0]:
                torch.testing.assert_close(
                    bank.sample([0], [time])["planned_contacts"],
                    torch.tensor([[0.0, 1.0]]),
                )
                np.testing.assert_array_equal(
                    sample(arrays, time)["planned_contacts"], [0, 1]
                )
            np.testing.assert_array_equal(
                sample(arrays, 1.99)["planned_contacts"], [1, 1]
            )
            torch.testing.assert_close(
                bank.sample([0], [1.99])["planned_contacts"], torch.ones((1, 2))
            )

    def test_incomplete_library_reports_missing_splits_with_relative_output(self):
        def failed_validation(robot, path):
            report = {"passed": False, "checks": {"joint_positions": False}}
            write_json(path.with_suffix(".validation.json"), report)
            return report, {}

        # Windows runners can keep the checkout and system temp on different
        # drives. A relative-output test needs its temporary directory on ROOT.
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            relative = Path(directory).relative_to(ROOT)
            with patch(
                "snu_gom_walk.motion_pipeline.generate.generate",
                return_value=(self.arrays, {}),
            ), patch(
                "snu_gom_walk.motion_pipeline.validate.validate_file",
                side_effect=failed_validation,
            ), patch(
                "snu_gom_walk.motion_pipeline.review.render"
            ):
                run, summary = build(self.robot, relative, count=4)
            self.assertTrue(run.is_absolute())
            self.assertFalse(summary["complete"])
            self.assertEqual(
                summary["missing_required_splits"],
                ["stand/train", "stand/val", "walk/train", "walk/val"],
            )
            self.assertEqual(summary["rejected_attempts"], 12)
            self.assertEqual(summary["accepted_kinematic"], 0)
            latest = json.loads((Path(directory) / "latest.json").read_text())
            self.assertEqual(latest["run"], run.relative_to(ROOT).as_posix())

    def test_absolute_and_relative_package_roots_inside_repo_have_same_id(self):
        relative = copy.deepcopy(self.robot.profile)
        relative["package_roots"] = {"gom": "snu_gom_description"}
        absolute = copy.deepcopy(relative)
        absolute["package_roots"]["gom"] = str(ROOT / "snu_gom_description")
        self.assertEqual(
            RobotModel(relative, with_physics=False).model_id,
            RobotModel(absolute, with_physics=False).model_id,
        )

    def test_partial_negative_or_mismatched_motor_curves_are_rejected(self):
        for speeds, torques in [
            ([0, 20], [0.5, 0.2]),
            ([0, 20], [0.5, -0.1]),
            ([1, 20], [0.5, 0]),
            ([0, 20], [0.5]),
            ([0, float("nan")], [0.5, 0]),
        ]:
            profile = copy.deepcopy(self.robot.profile)
            profile["motors"]["default"].update(
                curve_speed_rpm=speeds, curve_torque_nm=torques
            )
            with self.subTest(speeds=speeds, torques=torques), self.assertRaisesRegex(
                ValueError, "Motor curve"
            ):
                RobotModel(profile, with_physics=False)

    def test_unknown_motor_joint_is_rejected(self):
        profile = copy.deepcopy(self.robot.profile)
        profile["motors"]["overrides"]["left_hip_rol_joint"] = {"stall_nm": 0.6}
        with self.assertRaisesRegex(ValueError, "Unknown joint"):
            RobotModel(profile, with_physics=False)

    def test_cpu_and_torch_curves_match_at_and_beyond_loaded_samples(self):
        robot = self.robot
        x, y = curve_arrays(robot.profile, robot.names)
        # Dense signed samples include padding and the no-load endpoint.
        for speed in np.r_[np.linspace(-14, 14, 81), x.ravel()]:
            velocity = np.full(len(robot.names), speed)
            curve = torch_curve_cap(
                torch.tensor(velocity)[None], torch.tensor(x), torch.tensor(y)
            ).numpy()[0]
            rows = [
                dict(
                    robot.profile["motors"]["default"],
                    **robot.profile["motors"]["overrides"].get(name, {})
                )
                for name in robot.names
            ]
            linear = np.array(
                [
                    row["stall_nm"] * max(0.0, 1 - abs(speed) / row["no_load_rad_s"])
                    for row in rows
                ]
            )
            np.testing.assert_allclose(
                np.minimum(np.minimum(curve, linear), robot.effort),
                torque_envelope(robot.profile, robot.names, velocity, robot.effort),
                atol=1e-12,
            )

    def test_numerical_solver_failure_never_becomes_conditional_reference(self):
        failure = SimpleNamespace(
            status=4, success=False, message="synthetic numerical failure"
        )
        with patch(
            "snu_gom_walk.motion_pipeline.feasibility.linprog", return_value=failure
        ), self.assertRaisesRegex(ValueError, "solver failed"):
            screen_reference(self.robot, self.arrays)

    def test_changed_root_datum_is_rejected_before_isaac_starts(self):
        validate_training_adapter(self.robot)
        changed = copy.copy(self.robot)
        changed.robot = copy.deepcopy(self.robot.robot)
        fixed = next(
            j
            for j in changed.robot.findall("joint")
            if j.find("child").get("link") == "base_link"
        )
        transform = fixed.find("origin")
        if transform is None:
            transform = ET.SubElement(fixed, "origin")
        transform.set("xyz", "0 0 .01")
        with self.assertRaisesRegex(ValueError, "root datum"):
            validate_training_adapter(changed)


if __name__ == "__main__":
    unittest.main()
