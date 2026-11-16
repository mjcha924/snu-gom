"""Plot lightweight progress figures from a completed or ongoing PPO run."""

import argparse
import json
from pathlib import Path

from runtime import ROOT, configure_runtime


def main():
    configure_runtime("plot")
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    args = parser.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    run = args.run.resolve()
    if not run.is_relative_to(ROOT):
        parser.error("Run directory must be within the workspace")
    events = EventAccumulator(str(run), size_guidance={"scalars": 0}).Reload()
    figure, axes = plt.subplots(2, 2, figsize=(10, 6), constrained_layout=True)
    plots = [
        ("Train/mean_episode_length", "Training episode duration (s)", 0.02),
        ("Metrics/forward_speed", "Mean forward speed (m/s)", 1.0),
        ("Reward/clearance", "Weighted swing-clearance reward", 1.0),
        ("Train/mean_reward", "Training return (not a success score)", 1.0),
    ]
    for axis, (tag, title, scale) in zip(axes.flat, plots):
        samples = events.Scalars(tag)
        axis.plot([sample.step for sample in samples], [sample.value * scale for sample in samples])
        axis.set(title=title, xlabel="PPO update")
        axis.grid(alpha=0.25)
    settings = json.loads((run / "config.json").read_text())["settings"]
    axes[0, 1].axhline(settings["speed"], color="orange", linestyle="--", label="moving command")
    axes[0, 1].legend()
    figure.suptitle("SNU-GOM training progress — evaluate stepping separately")
    path = run / "training_progress.png"
    figure.savefig(path, dpi=130)
    plt.close(figure)
    print(path)


if __name__ == "__main__":
    main()
