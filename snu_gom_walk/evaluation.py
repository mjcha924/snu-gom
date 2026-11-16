"""Conservative straight-walking gates, independent of training reward."""


def straight_walk_gate(episodes):
    checks = []
    for episode in episodes:
        checks.append({
            "survival": episode["survived"] and 29.9 <= episode["duration"] <= 30.1,
            "distance": episode["forward_distance"] >= 0.5,
            "lateral_drift": abs(episode["lateral_distance"]) <= 0.10,
            "heading": abs(episode["heading_change_degrees"]) <= 15,
            "real_steps": min(episode["clear_touchdowns_left_right"]) >= 3 and episode["alternating_touchdowns"] >= 5,
            "tracking": episode["speed_mae"] <= 0.012,
        })
    successes = sum(all(check.values()) for check in checks)
    return {
        "passed": len(episodes) >= 20 and successes / len(episodes) >= 0.90,
        "trials": len(episodes), "successful_trials": successes, "checks": checks,
        "required_trials": 20, "required_success_fraction": 0.90,
        "additional_gates": ["start_stop", "actuator_calibration", "multiple_training_seeds"],
    }
