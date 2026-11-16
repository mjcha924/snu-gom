"""Validate the kinematic seed without confusing it with balanced walking."""

import json
import unittest

import numpy as np

from snu_gom_walk.model import LEG_JOINTS, audit_model, forward_kinematics
from snu_gom_walk.reference import KinematicModel, build_reference


class ReferenceTests(unittest.TestCase):
    def test_cached_kinematics_matches_source(self):
        positions = {name: 0.1 for name in LEG_JOINTS}
        cached = KinematicModel().frames(positions)
        for name, matrix in forward_kinematics(positions).items():
            np.testing.assert_allclose(cached[name], matrix, atol=1e-8)

    def test_seed_respects_geometry_and_slew_not_dynamic_claim(self):
        report = build_reference()
        json.dumps(report)
        self.assertEqual(report["kind"], "kinematic_seed_not_validated_walking")
        self.assertTrue(report["velocity_limits_passed"])
        self.assertLess(report["max_position_error_m"], 0.002)
        self.assertLess(report["max_rotation_error_rad"], 0.02)
        model = audit_model()
        joints = np.array([row["joints"] for row in report["rows"]])
        for index, name in enumerate(LEG_JOINTS):
            self.assertGreaterEqual(joints[:, index].min(), model["joints"][name]["lower"])
            self.assertLessEqual(joints[:, index].max(), model["joints"][name]["upper"])
        heights = np.array([row["sole_heights"] for row in report["rows"]])
        self.assertTrue((heights.max(axis=0) > 0.003).all())

    def test_invalid_configuration_rejected(self):
        with self.assertRaises(ValueError):
            build_reference(period=0)
