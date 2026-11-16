import json
import unittest

import numpy as np

from snu_gom_walk.support_reference import build_support_seed


class SupportReferenceTests(unittest.TestCase):
    def test_default_seed_respects_joint_limits(self):
        report = build_support_seed()
        json.dumps(report)
        self.assertTrue(report["position_limits_passed"])
        self.assertTrue(report["velocity_limits_passed"])
        self.assertEqual(len(report["rows"]), 80)
        self.assertLess(report["peak_reference_speed"], 1.0)
        heights = np.array([row["sole_heights"] for row in report["rows"]])
        self.assertTrue((heights.max(axis=0) > 0.002).all())
        for row in report["rows"]:
            self.assertEqual(len(row["foot_x_offsets"]), 2)
            for foot_index in range(2):
                if not row["swing"][foot_index]:
                    self.assertAlmostEqual(abs(row["joints"][foot_index * 5 + 3]), 0.30)

    def test_invalid_inputs(self):
        for arguments in [{"samples": 0}, {"samples": 4.5}, {"period": 0}, {"period": float("nan")}, {"speed": -1}, {"lean": float("inf")}]:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                build_support_seed(**arguments)

    def test_fast_seed_is_rejected_by_velocity_check(self):
        self.assertFalse(build_support_seed(period=0.1)["velocity_limits_passed"])


if __name__ == "__main__":
    unittest.main()
