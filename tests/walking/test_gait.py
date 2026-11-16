"""Check the stepping curriculum's phase, geometry, and distance conventions."""

import unittest

import numpy as np

from snu_gom_walk.model import ALL_JOINTS, FOOT_LINKS, audit_model, forward_kinematics, stance_configuration

try:
    import torch
    from snu_gom_walk.gait import gait_targets
except ImportError:
    torch = None


class StanceTests(unittest.TestCase):
    def test_crouch_respects_source_limits_and_floor(self):
        model = audit_model()
        positions, height, centers = stance_configuration(0.30, model)
        self.assertEqual(set(positions), set(ALL_JOINTS))
        frames = forward_kinematics(positions)
        for name, angle in positions.items():
            self.assertGreaterEqual(angle, model["joints"][name]["lower"])
            self.assertLessEqual(angle, model["joints"][name]["upper"])
        lowest = []
        for name in FOOT_LINKS:
            corners = np.array(model["foot_corners"][name]) @ frames[name][:3, :3].T + frames[name][:3, 3]
            lowest.append(corners[:, 2].min() + height)
            np.testing.assert_allclose(corners.mean(axis=0), centers[name])
        self.assertAlmostEqual(min(lowest), 0.0)


@unittest.skipIf(torch is None, "PyTorch required for gait tensor checks")
class GaitTests(unittest.TestCase):
    def test_stopping_disables_gait(self):
        phase = torch.linspace(0, 1, 101)
        swing, heights, horizontal = gait_targets(phase, torch.zeros_like(phase), 2.4, 0.006)
        self.assertFalse(swing.any())
        self.assertEqual(float(heights.abs().sum() + horizontal.abs().sum()), 0.0)

    def test_feet_alternate_with_bounded_targets(self):
        phase = torch.linspace(0, 0.999, 1000)
        speed = torch.full_like(phase, 0.025)
        swing, heights, horizontal = gait_targets(phase, speed, 2.4, 0.006)
        self.assertFalse(swing.all(dim=1).any())
        self.assertTrue((heights >= 0).all())
        self.assertLessEqual(float(heights.max()), 0.006001)
        self.assertLessEqual(float(horizontal.abs().max()), 0.025 * 2.4 * 0.65 / 2 + 1e-6)
        shifted = gait_targets(phase + 0.5, speed, 2.4, 0.006)
        torch.testing.assert_close(shifted[1], heights.flip(1), atol=1e-7, rtol=1e-4)
        torch.testing.assert_close(shifted[2], horizontal.flip(1), atol=1e-7, rtol=1e-4)

    def test_cycle_is_continuous(self):
        for boundary in [0.10, 0.45, 0.60, 0.95, 1.0]:
            phase = torch.tensor([boundary - 1e-6, boundary + 1e-6])
            _, heights, horizontal = gait_targets(phase, torch.full_like(phase, 0.025), 2.4, 0.006)
            self.assertLess(float((heights[0] - heights[1]).abs().max()), 1e-5)
            self.assertLess(float((horizontal[0] - horizontal[1]).abs().max()), 1e-5)
