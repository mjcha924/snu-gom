"""Integrate with your measured motor/IMU transport; this does not open hardware."""
import time
from snu_bear_motion.contract import SKILLS
from snu_bear_motion.hardware import ServoCalibration, Transport
from snu_bear_motion.registry import Registry
from snu_bear_motion.runtime import OnnxPolicy, PolicyController, SkillSelector

def run(transport: Transport, measured_calibration, get_requested_behavior,
        registry_path="policies/registry.json", initial_posture="sit"):
    calibration = ServoCalibration(measured_calibration)
    registry = Registry(registry_path)
    policies = {name: OnnxPolicy(registry.resolve(name)) for name in SKILLS}
    control = PolicyController(policies)
    selector = SkillSelector(initial_posture)
    deadline = time.monotonic()
    try:
        while True:
            state = transport.read_state()
            selector.request(get_requested_behavior())  # sit / low / crawl
            skill = selector.update(state, 0.02)
            q_target = control.step(skill, state, time.monotonic(), command_m_s=0.01)
            transport.write_goal_ticks(calibration.to_ticks(q_target))
            deadline += 0.02
            remaining = deadline - time.monotonic()
            if remaining < -0.01:
                raise RuntimeError("Control loop missed its timing budget")
            time.sleep(max(0.0, remaining))
    except BaseException as error:
        transport.stop(str(error))
        raise
