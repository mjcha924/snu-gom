"""Prevent survival or sliding alone from unlocking terrain curricula."""

import unittest

from snu_gom_walk.evaluation import straight_walk_gate


class GateTests(unittest.TestCase):
    def setUp(self):
        self.success = {
            "survived": True, "duration": 30, "forward_distance": 0.55,
            "lateral_distance": 0.01, "heading_change_degrees": 3,
            "clear_touchdowns_left_right": [8, 8], "alternating_touchdowns": 15,
            "speed_mae": 0.005,
        }

    def test_clear_repeatable_walk_passes_straight_gate(self):
        self.assertTrue(straight_walk_gate([self.success] * 20)["passed"])

    def test_stationary_sliding_and_short_evaluations_do_not_pass(self):
        for change in [{"forward_distance": 0.005}, {"clear_touchdowns_left_right": [0, 0]}, {"duration": 10}, {"survived": False}]:
            self.assertFalse(straight_walk_gate([{**self.success, **change}] * 20)["passed"])
        self.assertFalse(straight_walk_gate([self.success] * 3)["passed"])
        self.assertFalse(straight_walk_gate([])["passed"])
