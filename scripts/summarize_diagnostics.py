"""Summarize recorded control diagnostics without importing Isaac Sim."""

import argparse
import json
from pathlib import Path

import numpy as np

from runtime import ROOT, configure_runtime


def summarize(report):
    samples = report["samples"]
    times = np.array([sample["time"] for sample in samples])
    selected = times >= min(2.0, times[-1] / 2)
    positions = np.array([sample["joint_position"] for sample in samples])
    targets = np.array([sample["target"] for sample in samples])
    reference = np.array([sample["reference"] for sample in samples])
    residual = np.array([sample["residual"] for sample in samples])
    heights = np.array([sample["heights"] for sample in samples])
    contacts = np.array([sample["contacts"] for sample in samples])
    forces = np.array([sample["contact_forces"] for sample in samples])
    velocities = np.array([sample["substep_joint_velocity"] for sample in samples])
    torques = np.array([sample["substep_torque"] for sample in samples])
    slip = np.linalg.norm(np.array([sample["contact_point_velocity"] for sample in samples])[..., :2], axis=-1)
    foot_ids = report["foot_contact_ids"]
    other_ids = [index for index in range(forces.shape[1]) if index not in foot_ids]
    return {
        "duration": float(times[-1]), "fallen": samples[-1]["fallen"],
        "final_position": samples[-1]["position"],
        "statistics_start_seconds": float(times[selected][0]),
        "max_sole_height_left_right": heights.max(axis=0).tolist(),
        "stance_sliding_distance_left_right": ((slip * contacts).sum(axis=0) * report["control_dt"]).tolist(),
        "both_contact_fraction": float(contacts.all(axis=1).mean()),
        "peak_substep_speed": float(np.abs(velocities).max()),
        "peak_substep_speed_after_statistics_start": float(np.abs(velocities[selected]).max()),
        "peak_reported_torque": float(np.abs(torques).max()),
        "mean_foot_vertical_force": forces[selected][:, foot_ids, 2].mean(axis=0).tolist(),
        "max_nonfoot_force": float(np.linalg.norm(forces[:, other_ids], axis=-1).max()),
        "joints": {name: {
            "target_tracking_rmse": float(np.sqrt(((targets[selected, index] - positions[selected, index]) ** 2).mean())),
            "reference_tracking_rmse": float(np.sqrt(((reference[selected, index] - positions[selected, index]) ** 2).mean())),
            "reference_range": float(np.ptp(reference[selected, index])),
            "actual_range": float(np.ptp(positions[selected, index])),
            "residual_rms": float(np.sqrt((residual[selected, index] ** 2).mean())),
            "effort_near_limit_fraction": float((np.abs(torques[selected, :, index]) >= 0.1425).mean()),
        } for index, name in enumerate(report["joint_order"])},
    }


def main():
    configure_runtime("diagnostic_plot")
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT):
        parser.error("Output must stay inside workspace")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summaries = {}
    for path in args.inputs:
        report = json.loads(path.read_text())
        summaries[report["mode"]] = summarize(report)
        samples = report["samples"]
        times = [sample["time"] for sample in samples]
        figure, axes = plt.subplots(3, 2, figsize=(12, 9), constrained_layout=True)
        for axis, joint in zip(axes.flat[:4], [1, 3, 6, 8]):
            for key in ["reference", "target", "joint_position"]:
                axis.plot(times, [sample[key][joint] for sample in samples], label=key)
            axis.set_title(report["joint_order"][joint])
            axis.set_ylabel("rad")
            axis.legend(fontsize=8)
        for foot_index, name in enumerate(["left", "right"]):
            axes[2, 0].plot(times, [sample["heights"][foot_index] * 1000 for sample in samples], label=name)
            axes[2, 1].plot(times, [sample["contact_forces"][report["foot_contact_ids"][foot_index]][2] for sample in samples], label=name)
        axes[2, 0].set_title("Minimum sole height (mm)")
        axes[2, 1].set_title("Vertical foot force (N)")
        for axis in axes.flat:
            axis.grid(alpha=0.25)
            axis.set_xlabel("seconds")
        axes[2, 0].legend()
        axes[2, 1].legend()
        figure.suptitle(f"SNU-GOM diagnostics: {report['mode']}")
        figure.savefig(output.with_name(f"{output.stem}-{report['mode']}.png"), dpi=120)
        plt.close(figure)
    output.write_text(json.dumps(summaries, indent=2) + "\n")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
