"""Feedback inference and posture-based skill routing. No serial port is opened."""
from dataclasses import dataclass
import numpy as np
from .contract import (CONTRACT, SKILLS, LOWER, UPPER, ObservationHistory,
                       action_target, observation_frame, vector)

@dataclass
class SensorState:
    q: np.ndarray
    dq: np.ndarray
    gyro_body: np.ndarray
    gravity_body: np.ndarray
    timestamp_s: float

class OnnxPolicy:
    def __init__(self, path):
        import onnxruntime as ort
        self.session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        ins, outs = self.session.get_inputs(), self.session.get_outputs()
        if len(ins) != 1 or len(outs) != 1:
            raise ValueError("Expected a feed-forward policy with one input and output")
        if len(ins[0].shape) != 2 or ins[0].shape[-1] != 136 or ins[0].type != "tensor(float)":
            raise ValueError("Expected float32 observation shape [batch, 136]")
        if len(outs[0].shape) != 2 or outs[0].shape[-1] != 9:
            raise ValueError("Expected action shape [batch, 9]")
        self.input_name = ins[0].name

    def __call__(self, observation):
        obs = vector(observation, 136, "observation")
        return vector(self.session.run(None, {self.input_name: obs[None, :]})[0][0], 9, "policy output")

def posture_matches(state, name):
    p = CONTRACT["poses"][name]
    q, dq = vector(state.q, 9, "q"), vector(state.dq, 9, "dq")
    g = vector(state.gravity_body, 3, "gravity")
    gyro = vector(state.gyro_body, 3, "gyro")
    norm = np.linalg.norm(g)
    return bool(0.8 <= norm <= 1.2 and np.max(np.abs(q-p["q_rad"])) < 0.18
                and np.dot(g / norm, p["gravity_body"]) > np.cos(np.deg2rad(8))
                and np.max(np.abs(dq)) < 0.3 and np.linalg.norm(gyro) < 0.25)

class SkillSelector:
    """Routes requests after a stable posture; never synthesizes motor trajectories.

    A posture guard uses encoders/IMU only. It is not a ground-contact certificate.
    Transition timeout is a fault, not an automatic switch to an incompatible pose.
    """
    def __init__(self, initial_posture="sit"):
        if initial_posture not in ("sit", "low"):
            raise ValueError("Initial posture must be sit or low")
        self.active = "hold_" + initial_posture
        self.desired = initial_posture
        self.stable_s = 0.0
        self.elapsed_s = 0.0

    def request(self, behavior):
        if behavior not in ("sit", "low", "crawl"):
            raise ValueError("Supported behaviors: sit, low, crawl")
        self.desired = behavior

    def update(self, state, dt):
        if not np.isfinite(dt) or not 0 < dt <= 0.1:
            raise ValueError("Invalid controller timestep")
        self.elapsed_s += dt
        goal = SKILLS[self.active]["goal"]
        self.stable_s = self.stable_s + dt if posture_matches(state, goal) else 0.0
        if self.active in ("sit_to_low", "low_to_sit"):
            if self.elapsed_s > SKILLS[self.active]["episode_seconds"]:
                raise RuntimeError("Transition timed out; operator recovery required")
            if self.stable_s < 0.5:
                return self.active
            next_skill = "hold_" + goal
        elif self.active == "crawl_forward":
            next_skill = "crawl_forward" if self.desired == "crawl" else "hold_low"
        elif self.stable_s < 0.5:
            return self.active
        elif goal == "sit":
            next_skill = "hold_sit" if self.desired == "sit" else "sit_to_low"
        else:
            next_skill = {"sit": "low_to_sit", "low": "hold_low", "crawl": "crawl_forward"}[self.desired]
        if next_skill != self.active:
            self.active, self.elapsed_s, self.stable_s = next_skill, 0.0, 0.0
        return self.active

class PolicyController:
    def __init__(self, policies):
        """policies is {skill: callable(observation)->9 actions}."""
        self.policies = policies
        self.history = ObservationHistory()
        self.active = None
        self.target = None
        self.last_timestamp = None

    def step(self, skill, state, now_s, command_m_s=0.0):
        if skill not in self.policies:
            raise RuntimeError(f"No trained policy loaded for {skill}")
        if not np.isfinite(now_s) or not np.isfinite(state.timestamp_s):
            raise ValueError("Invalid clock value")
        if not 0 <= now_s-state.timestamp_s <= 0.06:
            raise RuntimeError("Sensor sample stale or timestamp is in the future")
        if self.last_timestamp is not None and state.timestamp_s <= self.last_timestamp:
            raise RuntimeError("Sensor samples must advance monotonically")
        dt = 1 / CONTRACT["policy_hz"]
        if self.last_timestamp is not None and abs(state.timestamp_s-self.last_timestamp-dt) > 0.01:
            raise RuntimeError("Policy timing is outside the trained 50 Hz tolerance")
        q = vector(state.q, 9, "q")
        if np.any(q < LOWER) or np.any(q > UPPER):
            raise RuntimeError("Measured joint outside the simulation envelope")
        if self.target is None:
            self.target = q.copy()
        if skill != self.active:
            self.history.reset()
            self.active = skill
        command = command_m_s if skill == "crawl_forward" else 0.0
        frame = observation_frame(q, state.dq, state.gyro_body, state.gravity_body, self.target, command)
        action = self.policies[skill](self.history.push(frame))
        self.target = action_target(action, self.target, dt)
        self.last_timestamp = state.timestamp_s
        return self.target.copy()
