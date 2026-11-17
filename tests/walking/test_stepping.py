import unittest

import torch

from snu_gom_walk.stepping import TouchdownTracker, reference_tracking_reward, supported_lift_rewards


class ReferenceRewardTests(unittest.TestCase):
    def test_default_equivalence_and_weight_scaling(self):
        positions = torch.tensor([[0.0] * 10, [0.15] * 10])
        reference = torch.zeros_like(positions)
        original = 3.0 * torch.exp(-((positions - reference) / 0.15).square().mean(dim=-1))
        torch.testing.assert_close(reference_tracking_reward(positions, reference), original)
        torch.testing.assert_close(reference_tracking_reward(positions, reference, 1.0), original / 3)
        torch.testing.assert_close(reference_tracking_reward(positions, reference, 0.0), torch.zeros(2))

    def test_invalid_weight(self):
        positions = torch.zeros(2, 10)
        for weight in [-1, float("nan"), float("inf")]:
            with self.subTest(weight=weight), self.assertRaises(ValueError):
                reference_tracking_reward(positions, positions, weight)


class LiftRewardTests(unittest.TestCase):
    def test_progress_unloading_and_support(self):
        desired = torch.tensor([[0.004, 0.0]] * 4)
        heights = torch.tensor([[0.0, 0.0], [0.001, 0.0], [0.003, 0.0], [0.004, 0.004]])
        forces = torch.tensor([[5.0, 5.0], [2.0, 8.0], [0.0, 10.0], [0.0, 0.0]])
        lift, unloading = supported_lift_rewards(heights, desired, forces, 10, torch.ones(4, dtype=torch.bool))
        self.assertEqual(float(lift[0]), 0)
        self.assertGreater(float(lift[1]), float(lift[0]))
        self.assertGreater(float(lift[2]), float(lift[1]))
        self.assertGreater(float(unloading[1]), float(unloading[0]))
        self.assertEqual(float(lift[3]), 0)
        self.assertEqual(float(unloading[3]), 0)

    def test_zero_command_and_overshoot(self):
        heights = torch.tensor([[0.004, 0.0], [0.020, 0.0], [0.004, 0.0]])
        desired = torch.tensor([[0.004, 0.0]] * 3)
        forces = torch.tensor([[0.0, 10.0]] * 3)
        lift, unloading = supported_lift_rewards(heights, desired, forces, 10, torch.tensor([True, True, False]))
        self.assertTrue(torch.isfinite(lift).all())
        self.assertLess(float(lift[1]), float(lift[0]))
        self.assertEqual(float(lift[2] + unloading[2]), 0)


class TouchdownTests(unittest.TestCase):
    def setUp(self):
        self.tracker = TouchdownTracker(2, 0.02)

    def update(self, contacts, heights=(0.0, 0.0), moving=True, terminal=False):
        return self.tracker.update(torch.tensor([contacts] * 2), torch.tensor([heights] * 2), torch.tensor([moving] * 2), torch.tensor([terminal] * 2))

    def lift_land(self, foot, frames=3):
        contacts = [True, True]
        heights = [0.0, 0.0]
        contacts[foot] = False
        heights[foot] = 0.003
        for _ in range(frames):
            self.update(contacts, heights)
        return self.update([True, True])

    def test_alternation_and_repeated_foot(self):
        touchdown, alternating = self.lift_land(0)
        self.assertTrue(touchdown[:, 0].all())
        self.assertFalse(alternating.any())
        _, alternating = self.lift_land(1)
        self.assertTrue(alternating.all())
        _, alternating = self.lift_land(1)
        self.assertFalse(alternating.any())
        self.assertFalse(self.update([True, True])[0].any())

    def test_chatter_sliding_and_hopping(self):
        self.assertFalse(self.lift_land(0, frames=2)[0].any())
        for _ in range(4):
            self.update([False, True], [0.001, 0.0])
        self.assertFalse(self.update([True, True])[0].any())
        for _ in range(4):
            self.update([False, False], [0.004, 0.004])
        self.assertFalse(self.update([True, True])[0].any())

    def test_reset_terminal_and_stopping(self):
        for _ in range(3):
            self.update([False, True], [0.004, 0.0])
        self.tracker.reset(torch.tensor([0]))
        touchdown, _ = self.update([True, True])
        self.assertFalse(touchdown[0].any())
        self.assertTrue(touchdown[1, 0])
        for _ in range(3):
            self.update([False, True], [0.004, 0.0])
        self.assertFalse(self.update([True, True], terminal=True)[0].any())
        for _ in range(3):
            self.update([False, True], [0.004, 0.0], moving=False)
        self.assertFalse(self.update([True, True])[0].any())


if __name__ == "__main__":
    unittest.main()
