"""Publish compact flat-floor feasibility results and measured diagnostic plots."""

import argparse
import json
from pathlib import Path

import numpy as np

from runtime import ROOT, configure_runtime


def main():
    configure_runtime("flat_probe_summary")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--searches", type=Path, nargs="+", required=True)
    parser.add_argument("--contacts", type=Path, required=True)
    parser.add_argument("--clearance", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(not path.resolve().is_relative_to(ROOT) for path in [*args.searches, args.contacts, args.clearance, args.output]):
        parser.error("Keep analysis inputs and outputs in the workspace")
    searches = [json.loads(path.read_text()) for path in args.searches]
    contacts = json.loads(args.contacts.read_text())
    clearance = json.loads(args.clearance.read_text())
    if any(report["model_hashes"] != contacts["model_hashes"] for report in [*searches, clearance]):
        raise ValueError("Model hashes must match")
    summary = {
        "optimizer_updates": 0, "walking_validated": False,
        "searches": [{"input": str(path), **{key: value for key, value in report.items() if key != "best_traces"}} for path, report in zip(args.searches, searches)],
        "contact_cases": contacts["results"], "hip_clearance": clearance,
        "scope": "Scripted parameter screening, not learning or independent walking validation; survivors may rock without lifting either foot",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    labels = [path.stem.removeprefix("flat_probe_") for path in args.searches]
    locations = np.arange(len(searches))
    axes[0, 0].bar(locations, [len(report["results"]) for report in searches], label="tested", color="lightgray")
    axes[0, 0].bar(locations, [report["survivors"] for report in searches], label="no termination", color="steelblue")
    axes[0, 0].set_xticks(locations, labels, rotation=20, ha="right")
    axes[0, 0].set(title="No candidate passes the alternating-step screen", ylabel="candidates")
    axes[0, 0].legend()
    columns = contacts["trace_columns"]
    high_transfer = np.array(contacts["best_traces"]["4"])
    times = np.arange(1, len(high_transfer) + 1) * contacts["trace_dt"]
    for key, label in [("target/left_hip_roll_joint", "target hip roll"), ("joint_position/left_hip_roll_joint", "actual hip roll"), ("roll", "body roll")]:
        axes[0, 1].plot(times, np.degrees(high_transfer[:, columns.index(key)]), label=label)
    axes[0, 1].axvline(times[-1], color="crimson", linestyle="--", label="hip/thigh contact termination")
    axes[0, 1].set(title="Termination while still upright (larger transfer)", xlabel="seconds", ylabel="degrees")
    axes[0, 1].legend(fontsize=8)
    rows = clearance["rows"]
    for kind in ["collision", "visual"]:
        axes[1, 0].plot([row["time"] for row in rows], [max(row[kind]["minimum_surface_distance_m"], 0) * 1000 for row in rows], "o-", label=kind)
    axes[1, 0].set(title="Hip/thigh clearance closes during weight transfer", xlabel="seconds", ylabel="minimum surface distance (mm)")
    axes[1, 0].legend()
    larger_lift = np.array(contacts["best_traces"]["2"])
    times = np.arange(1, len(larger_lift) + 1) * contacts["trace_dt"]
    for key in ["left_normal_force", "right_normal_force"]:
        axes[1, 1].plot(times, larger_lift[:, columns.index(key)], label=key.replace("_normal_force", " foot"))
    axes[1, 1].set(xlim=(3, 7), title="Larger left-knee bend does not unload the left foot", xlabel="seconds", ylabel="normal contact force (N)")
    axes[1, 1].legend()
    for axis in axes.flat:
        axis.grid(alpha=0.2)
    figure.savefig(args.output.with_suffix(".png"), dpi=130)
    plt.close(figure)
    print(args.output)


if __name__ == "__main__":
    main()
