"""Audit recorded rewards, command jitter, and support geometry; never train."""

import argparse
import json
from pathlib import Path

import numpy as np

from runtime import ROOT, configure_runtime
from summarize_diagnostics import summarize


def summarize_trace(report):
    result = summarize(report)
    samples = report["samples"]
    selected = [sample for sample in samples if sample["time"] >= result["statistics_start_seconds"]]
    timestep = report["control_dt"]
    result["total_return"] = sum(sample["reward"] for sample in samples)
    result["mean_reward_terms_after_settling"] = {
        key: float(np.mean([sample["reward_terms"][key] for sample in selected]))
        for key in selected[0]["reward_terms"]
    }
    result["qualified_touchdowns"] = np.array([sample["qualified_touchdowns"] for sample in samples]).sum(axis=0).tolist()
    result["alternating_touchdowns"] = sum(sample["alternating_touchdown"] for sample in samples)
    result["final_rpy_degrees"] = np.degrees(samples[-1]["rpy"]).tolist()
    delta = np.array([sample["target_delta"] for sample in selected])
    limited = np.array([sample["slew_limited"] for sample in selected])
    actions = np.array([sample["raw_actions"] for sample in selected])
    frequencies = np.fft.rfftfreq(len(selected), timestep)
    result["wrapped_action_near_clip_fraction"] = float((np.abs(actions) >= 0.999).mean())
    for index, name in enumerate(report["joint_order"]):
        power = np.abs(np.fft.rfft(delta[:, index] - delta[:, index].mean())) ** 2
        result["joints"][name].update({
            "slew_limited_fraction": float(limited[:, index].mean()),
            "target_direction_reversals_per_second": float((delta[1:, index] * delta[:-1, index] < -1e-8).mean() / timestep),
            "target_rate_dominant_frequency_hz": float(frequencies[power.argmax()]) if power.sum() > 1e-12 else None,
            "target_rate_power_above_5hz_fraction": float(power[frequencies > 5].sum() / power.sum()) if power.sum() > 1e-12 else None,
        })
    return result


def summarize_reference(reference):
    rows = reference["rows"]
    heights = np.array([row["sole_heights"] for row in rows])
    active = heights > 0.002
    margins = np.array([row["support_margin_y"] for row in rows])
    return {
        "period_seconds": reference["period"],
        "reference_fore_aft_speed_m_s": reference["speed"],
        "active_swing_fraction": float(active.any(axis=1).mean()),
        "maximum_sole_height_m": heights.max(axis=0).tolist(),
        "reference_peak_joint_speed_rad_s": reference["peak_reference_speed"],
        "expected_contact_reward_for_both_feet_grounded": float(2 * (~active).mean()),
        "intended_support_lateral_com_margin": [{
            "swing_foot": foot,
            "active_samples": int(active[:, foot].sum()),
            "minimum_m": float(margins[active[:, foot], 1 - foot].min()),
            "maximum_m": float(margins[active[:, foot], 1 - foot].max()),
            "fraction_nonnegative": float((margins[active[:, foot], 1 - foot] >= 0).mean()),
        } for foot in range(2)],
        "scope": "Ideal reference geometry only; static margin is not a dynamic stability criterion",
    }


def training_counts(run):
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    config = json.loads((run / "config.json").read_text())
    events = EventAccumulator(str(run)).Reload()
    scale = config["num_envs"] * config["agent"]["num_steps_per_env"]
    return {
        "run": str(run.relative_to(ROOT)),
        "transitions": scale * config["iterations_requested"],
        "logged_event_equivalents": {
            name: float(sum(event.value * scale for event in events.Scalars(tag)))
            for name, tag in [
                ("qualified_touchdowns", "Metrics/qualified_touchdowns"),
                ("alternating_touchdowns", "Metrics/alternating_touchdowns"),
            ]
        },
        "method": "Per-update mean of per-step event counts/num_envs, multiplied by num_envs * rollout_steps; not deterministic success counts",
    }


def main():
    configure_runtime("stall_analysis")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--traces", type=Path, nargs="+", required=True)
    parser.add_argument("--training-runs", type=Path, nargs="*", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = [args.checkpoint, args.reference, *args.traces, *args.training_runs, args.output]
    if any(not path.resolve().is_relative_to(ROOT) for path in paths):
        parser.error("Keep analysis inputs and outputs inside the workspace")
    config = json.loads((args.checkpoint.parent / "config.json").read_text())
    traces = {report["mode"]: report for report in [json.loads(path.read_text()) for path in args.traces]}
    for report in traces.values():
        if report["source_hashes"] != config["source_hashes"] or report["saved_settings"] != config["settings"]:
            raise ValueError("Diagnostic source/settings mismatch")
        if report["optimizer_updates"] != 0 or report["reference_disabled_for_neutral_mode"]:
            raise ValueError("Use policy/hold/seed under the same reward task, without optimization")
    reference = json.loads(args.reference.read_text())
    if reference["model_hashes"] != config["model_hashes"]:
        raise ValueError("Reference model mismatch")
    timestep = traces["policy"]["control_dt"]
    discount = config["agent"]["algorithm"]["gamma"]
    gae = config["agent"]["algorithm"]["lam"]
    result = {
        "optimizer_updates": 0,
        "checkpoint": str(args.checkpoint),
        "traces": {mode: summarize_trace(report) for mode, report in traces.items()},
        "reference": summarize_reference(reference),
        "stationary_velocity_reward_fraction": float(np.exp(-(config["settings"]["speed"] / 0.025) ** 2)),
        "training_event_history": [training_counts(path.resolve()) for path in args.training_runs],
        "credit_assignment": {
            "rollout_seconds": timestep * config["agent"]["num_steps_per_env"],
            "discount_e_folding_seconds": float(-timestep / np.log(discount)),
            "gae_e_folding_seconds": float(-timestep / np.log(discount * gae)),
            "full_cycle_discount": float(discount ** (reference["period"] / timestep)),
            "scope": "Secondary considerations, not hard learning horizons; bootstrapping can propagate longer-term value",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    terms = ["tracking", "contact", "stride", "reference", "unloading", "clearance"]
    locations = np.arange(len(terms))
    for offset, mode in [(-0.18, "policy"), (0.18, "hold")]:
        values = result["traces"][mode]["mean_reward_terms_after_settling"]
        axes[0, 0].bar(locations + offset, [values[term] for term in terms], width=0.36, label=mode)
    axes[0, 0].set_xticks(locations, terms, rotation=20)
    axes[0, 0].set_title("Reward rates after settling: no steps in either rollout")
    axes[0, 0].legend()
    for foot, name in enumerate(["left swing", "right swing"]):
        rows = [row for row in reference["rows"] if row["sole_heights"][foot] > 0.002]
        axes[0, 1].plot([row["phase"] for row in rows], [row["support_margin_y"][1 - foot] * 1000 for row in rows], "o-", label=name)
    axes[0, 1].axhline(0, color="black", linestyle="--")
    axes[0, 1].set(title="Reference CoM remains outside intended support foot", xlabel="cycle phase", ylabel="lateral static margin (mm)")
    axes[0, 1].legend()
    selected = [sample for sample in traces["policy"]["samples"] if 6 <= sample["time"] <= 6.4]
    joint_index = traces["policy"]["joint_order"].index("left_knee_pitch_joint")
    for key in ["reference", "target", "joint_position"]:
        axes[1, 0].plot([sample["time"] for sample in selected], [sample[key][joint_index] for sample in selected], ".-", label=key)
    axes[1, 0].set(title="Left knee: rapid command oscillation", xlabel="seconds", ylabel="rad")
    axes[1, 0].legend()
    joints = result["traces"]["policy"]["joints"]
    axes[1, 1].bar(np.arange(len(joints)), [100 * joint["slew_limited_fraction"] for joint in joints.values()])
    axes[1, 1].set_xticks(np.arange(len(joints)), [name.replace("_joint", "").replace("left_", "L ").replace("right_", "R ") for name in joints], rotation=60, ha="right")
    axes[1, 1].set(title="Policy commands frequently hit the target rate limiter", ylabel="limited control updates (%)")
    for axis in axes.flat:
        axis.grid(alpha=0.2)
    figure.savefig(args.output.with_suffix(".png"), dpi=130)
    plt.close(figure)
    print(args.output)


if __name__ == "__main__":
    main()
