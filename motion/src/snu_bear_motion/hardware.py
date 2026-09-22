"""Calibrated unit conversion and a transport interface; motor model is unspecified."""
from typing import Protocol
import numpy as np
from .contract import JOINTS, vector
from .runtime import SensorState

class Transport(Protocol):
    def read_state(self) -> SensorState:
        """Return synchronized URDF-radian encoders and body-frame IMU estimates."""
        ...

    def write_goal_ticks(self, goals: dict[int, int]) -> None:
        """Send position goals with model-specific, calibrated servo settings."""
        ...

    def stop(self, reason: str) -> None:
        """Execute this robot's tested fault response; do not assume torque-off is safe."""
        ...

class ServoCalibration:
    def __init__(self, config):
        if config.get("status") != "measured":
            raise ValueError("Fill in measured servo calibration before converting hardware commands")
        self.rows = [config["joints"][name] for name in JOINTS]
        ids = [r["id"] for r in self.rows]
        if len(set(ids)) != 9 or any(type(i) is not int or not 0 <= i <= 252 for i in ids):
            raise ValueError("Nine unique valid servo IDs are required")
        for r in self.rows:
            values = [r[k] for k in ("zero_tick", "ticks_per_turn", "min_tick", "max_tick", "direction")]
            if not all(isinstance(x, (int, float)) and np.isfinite(x) for x in values):
                raise ValueError("Calibration must contain measured finite numbers")
            if r["direction"] not in (-1, 1) or r["ticks_per_turn"] <= 0 or r["min_tick"] >= r["max_tick"]:
                raise ValueError("Invalid servo direction, resolution or limits")

    def to_ticks(self, q):
        q = vector(q, 9, "q")
        goals = {}
        for angle, r in zip(q, self.rows):
            tick = int(round(r["zero_tick"] + r["direction"]*float(angle)*r["ticks_per_turn"]/(2*np.pi)))
            if not r["min_tick"] <= tick <= r["max_tick"]:
                raise ValueError(f"Goal exceeds measured travel on servo {r['id']}")
            goals[r["id"]] = tick
        return goals

    def positions_to_urdf(self, positions):
        result = []
        for r in self.rows:
            tick = positions[r["id"]]
            if not isinstance(tick, (int, float)) or not np.isfinite(tick):
                raise ValueError("Non-finite encoder position")
            result.append(r["direction"]*(tick-r["zero_tick"])*2*np.pi/r["ticks_per_turn"])
        return np.array(result, dtype=np.float32)
