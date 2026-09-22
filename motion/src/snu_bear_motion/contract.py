"""One shared sensor/action contract for simulation and inference."""
import hashlib
import json
from pathlib import Path
import numpy as np

DATA = Path(__file__).resolve().parent / "data"
CONTRACT = json.loads((DATA / "contract.json").read_text())
SKILLS = json.loads((DATA / "skills.json").read_text())
JOINTS = tuple(CONTRACT["joints"])
LOWER = np.array(CONTRACT["q_lower_rad"], dtype=np.float32)
UPPER = np.array(CONTRACT["q_upper_rad"], dtype=np.float32)
MID = (LOWER + UPPER) / 2
HALF = (UPPER - LOWER) / 2

def fingerprint():
    """Changes to geometry, masses or IO invalidate checkpoint compatibility."""
    h = hashlib.sha256()
    root = DATA.parent
    files = [DATA / "contract.json", DATA / "skills.json", *sorted((DATA / "robot").rglob("*")),
             *sorted(root.rglob("*.py"))]
    for path in files:
        if path.is_file():
            h.update(str(path.relative_to(root)).encode())
            h.update(path.read_bytes())
    return h.hexdigest()

def vector(value, size, name):
    a = np.asarray(value, dtype=np.float32)
    if a.shape != (size,) or not np.isfinite(a).all():
        raise ValueError(f"{name} must be {size} finite values")
    return a

def geometric_to_urdf(angles_deg):
    registry = json.loads((DATA / "robot/joint_registry.json").read_text())
    return np.array([np.deg2rad(angles_deg[j["angle_key"]]) - j["origin_pitch_rad"]
                     for j in registry], dtype=np.float32)

def action_target(action, previous_target, dt=0.02):
    """Absolute bounded target with the same slew limit used in training."""
    if not np.isfinite(dt) or dt <= 0 or dt > 0.1:
        raise ValueError("dt must be positive and <= 0.1 s")
    a = np.clip(vector(action, 9, "action"), -1, 1)
    old = vector(previous_target, 9, "previous_target")
    if np.any(old < LOWER - 1e-5) or np.any(old > UPPER + 1e-5):
        raise ValueError("Previous target is outside the training envelope")
    desired = MID + HALF * a
    step = CONTRACT["target_slew_rad_s"] * dt
    return np.clip(old + np.clip(desired - old, -step, step), LOWER, UPPER)

def observation_frame(q, dq, gyro_body, gravity_body, previous_target, command_m_s=0.0):
    q, dq = vector(q, 9, "q"), vector(dq, 9, "dq")
    gyro = vector(gyro_body, 3, "gyro_body")
    gravity = vector(gravity_body, 3, "gravity_body")
    norm = np.linalg.norm(gravity)
    if not 0.8 <= norm <= 1.2:
        raise ValueError("gravity_body must be an estimated unit downward vector, not raw acceleration")
    if not np.isfinite(command_m_s) or not 0 <= command_m_s <= CONTRACT["max_command_m_s"]:
        raise ValueError("Forward speed must be in [0, 0.02] m/s")
    target = vector(previous_target, 9, "previous_target")
    return np.concatenate(((q-MID)/HALF, dq*CONTRACT["velocity_scale"],
        gyro*CONTRACT["gyro_scale"], gravity/norm, (target-MID)/HALF,
        [command_m_s/CONTRACT["command_scale_m_s"]])).astype(np.float32)

class ObservationHistory:
    def __init__(self):
        self.frames = None

    def reset(self):
        self.frames = None

    def push(self, frame):
        f = vector(frame, CONTRACT["frame_size"], "frame")
        if self.frames is None:
            self.frames = np.repeat(f[None, :], CONTRACT["history_length"], axis=0)
        else:
            self.frames = np.concatenate((self.frames[1:], f[None, :]), axis=0)
        return self.frames.reshape(-1).copy()
