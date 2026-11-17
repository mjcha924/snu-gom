import unittest

import torch

from scripts.flat_probe_motion import ankle_pitch_correction, guard_inward_roll, probe_targets, swing_weights


class FlatProbeTests(unittest.TestCase):
    def test_starts_at_existing_neutral(self):
        parameters = torch.tensor([[0.10, 0.25, 0.12, 0.06, 4.0]])
        targets = probe_targets(torch.tensor([0.0]), parameters)
        torch.testing.assert_close(targets, torch.tensor([[0, 0, 0.15, 0.30, -0.15, 0, 0, 0.15, -0.30, -0.15]]))

    def test_transfer_precedes_lift(self):
        parameters = torch.tensor([[0.10, 0.25, 0.12, 0.0, 4.0]])
        targets = probe_targets(torch.tensor([3.4]), parameters)
        self.assertGreater(abs(float(targets[0, 1])), 0.18)
        self.assertAlmostEqual(float(targets[0, 3]), 0.10, places=5)

    def test_periodic_and_rate_feasible(self):
        times = torch.arange(3.0, 7.02, 0.02)
        parameters = torch.tensor([[0.10, 0.35, 0.12, 0.06, 4.0]]).expand(len(times), -1)
        targets = probe_targets(times, parameters)
        self.assertLess(float(torch.diff(targets, dim=0).abs().max() / 0.02), 1.0)
        torch.testing.assert_close(targets[0], targets[200], atol=1e-6, rtol=1e-5)

    def test_invalid_period(self):
        with self.assertRaises(ValueError):
            probe_targets(torch.tensor([0.0]), torch.tensor([[0.1, 0.2, 0.1, 0.0, 0.0]]))

    def test_feedback_is_bounded_and_zero_gains_preserve_open_loop(self):
        pitch = torch.tensor([-0.4, 0.4])
        velocity = torch.tensor([-1.0, 1.0])
        torch.testing.assert_close(ankle_pitch_correction(pitch, velocity, torch.zeros(2, 2)), torch.zeros(2))
        torch.testing.assert_close(ankle_pitch_correction(pitch, velocity, torch.ones(2, 2)), torch.tensor([-0.15, 0.15]))
        with self.assertRaises(ValueError):
            ankle_pitch_correction(pitch, velocity, torch.full((2, 2), float("nan")))

    def test_swing_weights_alternate_without_hopping(self):
        times = torch.arange(0.0, 15.0, 0.02)
        weights = swing_weights(times, torch.full_like(times, 4.0))
        self.assertFalse(((weights[:, 0] > 1e-6) & (weights[:, 1] > 1e-6)).any())
        self.assertLess(float(weights[times < 3].abs().max()), 1e-6)
        torch.testing.assert_close(swing_weights(torch.tensor([4.0, 6.0]), torch.tensor([4.0, 4.0])), torch.eye(2), atol=1e-6, rtol=1e-5)

    def test_inward_guard_preserves_outward_transfer_and_other_joints(self):
        targets = torch.ones(2, 10) * 0.3
        targets[0, [1, 6]] = -0.3
        guarded = guard_inward_roll(targets, torch.tensor([0.18, 0.18]))
        torch.testing.assert_close(guarded[:, [1, 6]], torch.tensor([[-0.18, -0.3], [0.3, 0.18]]))
        torch.testing.assert_close(guarded[:, [0, 2, 3, 4, 5, 7, 8, 9]], targets[:, [0, 2, 3, 4, 5, 7, 8, 9]])
        torch.testing.assert_close(targets[:, 1], torch.tensor([-0.3, 0.3]))


if __name__ == "__main__":
    unittest.main()
