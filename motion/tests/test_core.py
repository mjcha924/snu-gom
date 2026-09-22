import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from snu_bear_motion.contract import (CONTRACT as C, DATA, JOINTS, LOWER, UPPER, MID, HALF,
    ObservationHistory, action_target, geometric_to_urdf, observation_frame, fingerprint)
from snu_bear_motion.runtime import SensorState, PolicyController, SkillSelector, posture_matches
from snu_bear_motion.registry import Registry
from snu_bear_motion.hardware import ServoCalibration

ROOT = Path(__file__).resolve().parents[1]

def state(pose="sit", t=0.0):
    p = C["poses"][pose]
    return SensorState(np.array(p["q_rad"], dtype=np.float32), np.zeros(9), np.zeros(3),
                       np.array(p["gravity_body"], dtype=np.float32), t)

class ContractTests(unittest.TestCase):
    def test_original_crawl_is_urdf_zero_not_new_low(self):
        registry = json.loads((DATA/"robot/joint_registry.json").read_text())
        original = {j["angle_key"]: j["neutral_angle_deg"] for j in registry}
        np.testing.assert_allclose(geometric_to_urdf(original), np.zeros(9), atol=1e-7)
        self.assertGreater(abs(C["poses"]["low"]["q_rad"][2]), 0.3)

    def test_sensor_frame_order_and_history(self):
        frame = observation_frame(MID, np.ones(9)*2, np.ones(3)*4, [0,0,-1], MID, 0.015)
        expected = np.r_[np.zeros(9), np.ones(9), np.ones(3), [0,0,-1], np.zeros(9), .5]
        np.testing.assert_allclose(frame, expected)
        h = ObservationHistory()
        first = h.push(frame).reshape(4, 34)
        np.testing.assert_allclose(first, np.repeat(expected[None], 4, axis=0))
        second = h.push(frame+0.1).reshape(4,34)
        np.testing.assert_allclose(second[:3], first[1:], atol=1e-6)
        np.testing.assert_allclose(second[-1], frame+0.1, atol=1e-6)

    def test_target_limits_slew_and_invalid_outputs(self):
        q = np.array(C["poses"]["sit"]["q_rad"], dtype=np.float32)
        for _ in range(200):
            new = action_target(np.ones(9)*1e6, q)
            self.assertTrue(np.all(abs(new-q) <= 0.020001))
            self.assertTrue(np.all(new <= UPPER))
            q = new
        np.testing.assert_allclose(q, UPPER, atol=1e-7)
        for bad in [np.full(9, np.nan), np.ones(8), np.full(9, np.inf)]:
            with self.assertRaises(ValueError): action_target(bad, MID)

    def test_gravity_is_estimated_direction(self):
        with self.assertRaises(ValueError):
            observation_frame(MID, np.zeros(9), np.zeros(3), [0,0,-9.81], MID)

    def test_all_reference_states_in_envelope(self):
        qs = np.array(json.loads((DATA/"optional_reference.json").read_text())["q_rad"])
        self.assertEqual(qs.shape, (111, 9))
        self.assertTrue(np.all((qs > LOWER) & (qs < UPPER)))

class RuntimeTests(unittest.TestCase):
    def test_no_motion_without_weights(self):
        reg = Registry(ROOT/"policies/registry.json")
        for skill in reg.data["skills"]:
            with self.assertRaisesRegex(RuntimeError, "no trained policy"): reg.resolve(skill)

    def test_posture_and_timed_handoffs(self):
        selector = SkillSelector()
        selector.request("crawl")
        for _ in range(26): selector.update(state(), .02)
        self.assertEqual(selector.active, "sit_to_low")
        for _ in range(24): selector.update(state("low"), .02)
        self.assertEqual(selector.active, "sit_to_low")
        selector.update(state("low"), .02)
        self.assertEqual(selector.active, "hold_low")
        for _ in range(26): selector.update(state("low"), .02)
        self.assertEqual(selector.active, "crawl_forward")
        selector.request("sit")
        selector.update(state("low"), .02)
        self.assertEqual(selector.active, "hold_low")
        for _ in range(26): selector.update(state("low"), .02)
        self.assertEqual(selector.active, "low_to_sit")

    def test_transition_timeout_and_unstable_guard(self):
        selector = SkillSelector()
        selector.request("low")
        moving = state(); moving.dq[:] = 1
        for _ in range(50): selector.update(moving, .02)
        self.assertEqual(selector.active, "hold_sit")
        for _ in range(26): selector.update(state(), .02)
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            for _ in range(800): selector.update(state(), .02)

    def test_sensor_faults_and_nan_policy(self):
        controller = PolicyController({"hold_sit": lambda o: np.zeros(9)})
        with self.assertRaisesRegex(RuntimeError, "stale"):
            controller.step("hold_sit", state(t=0), .2)
        q = controller.step("hold_sit", state(t=1), 1)
        self.assertTrue(np.all(abs(q-state().q) <= .020001))
        with self.assertRaisesRegex(RuntimeError, "monotonically"):
            controller.step("hold_sit", state(t=1), 1)
        nan_policy = PolicyController({"hold_sit": lambda o: np.full(9, np.nan)})
        with self.assertRaises(ValueError): nan_policy.step("hold_sit", state(), 0)

    def test_switch_has_no_target_jump(self):
        seen = []
        def fake_policy(o):
            seen.append(o.copy()); return np.ones(9)
        control = PolicyController({"hold_sit": fake_policy, "sit_to_low": fake_policy})
        q1 = control.step("hold_sit", state(t=0), 0)
        q2 = control.step("sit_to_low", state(t=.02), .02)
        self.assertTrue(np.all(abs(q2-q1) <= .020001))
        frames = seen[-1].reshape(4,34)
        np.testing.assert_allclose(frames[0], frames[-1])

    def test_servo_calibration_roundtrip_and_rejection(self):
        with self.assertRaises(ValueError): ServoCalibration({"status":"unmeasured"})
        cfg = {"status":"measured", "joints": {name: {"id":i+1, "zero_tick":2048,
            "direction":1 if i%2 else -1, "ticks_per_turn":4096,
            "min_tick":0, "max_tick":4095} for i,name in enumerate(JOINTS)}}
        calibration = ServoCalibration(cfg)
        q = state().q
        np.testing.assert_allclose(calibration.positions_to_urdf(calibration.to_ticks(q)), q,
                                   atol=np.pi/4096 + 1e-6)
        with self.assertRaises(ValueError): calibration.to_ticks(np.full(9, 10.0))

    def test_checkpoint_contract_rejected_before_execution(self):
        data = json.loads((ROOT/"policies/registry.json").read_text())
        data["skills"]["hold_sit"].update(status="trained_unverified", onnx="missing.onnx",
                                            contract_sha256="old-contract")
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"registry.json"; p.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "contract"):
                Registry(p).resolve("hold_sit")
        self.assertEqual(len(fingerprint()), 64)

if __name__ == "__main__": unittest.main()
