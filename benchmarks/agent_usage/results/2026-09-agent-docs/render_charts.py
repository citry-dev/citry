"""Render recording-ready figures from the curated agent experiment data."""

import json
from pathlib import Path
from statistics import mean

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
COLORS = {"llms": "#176b87", "guidance": "#9b621d", "skill": "#7952a0"}
LABELS = {"llms": "llms.txt", "guidance": "Short guidance", "skill": "Explicit skill"}


def render(batch: str, title: str, arms: tuple[str, ...]) -> None:
    """Keep models and execution batches separate so comparisons share a task."""
    runs = json.loads((ROOT / "records.json").read_text())["runs"]
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharex=True)
    for axis, model in zip(axes, ("terra", "luna"), strict=True):
        for row, arm in enumerate(arms):
            values = [
                run["elapsed_seconds"] for run in runs if run["batch"] == f"{batch}-{model}" and run["arm"] == arm
            ]
            # Separate overlapping attempts vertically without altering their measured duration.
            offsets = [(index - (len(values) - 1) / 2) * 0.075 for index in range(len(values))]
            axis.scatter(values, [row + offset for offset in offsets], color=COLORS[arm], s=55, alpha=0.8)
            average = mean(values)
            axis.scatter([average], [row], marker="D", color="#152536", s=70, zorder=3)
            axis.text(510, row, f"{average:.1f} s", ha="right", va="center", fontsize=10)
        axis.set_title(f"gpt-5.6-{model}", fontsize=13, fontweight="bold")
        axis.set_yticks(range(len(arms)), [LABELS[arm] for arm in arms])
        axis.set_ylim(len(arms) - 0.5, -0.5)
        axis.set_xlim(0, 520)
        axis.set_xlabel("Measured agent time (seconds)")
        axis.grid(axis="x", alpha=0.18)
        axis.set_axisbelow(True)
        for spine in ("top", "right", "left"):
            axis.spines[spine].set_visible(False)
        axis.tick_params(axis="y", length=0)
    figure.suptitle(title, fontsize=16, fontweight="bold", y=0.98)
    figure.text(
        0.5,
        0.035,
        "Circles: individual attempts. Diamonds: means. Every attempt passed its three grader tests.\n"
        "One server-events task, high effort, Citry 0.4.6. Live services; no causal speed claim.",
        ha="center",
        fontsize=10,
    )
    figure.tight_layout(rect=(0, 0.13, 1, 0.92))
    destination = ROOT / "charts"
    destination.mkdir(exist_ok=True)
    for extension in ("png", "svg"):
        figure.savefig(destination / f"{batch}-timings.{extension}", dpi=180, facecolor="white")
    plt.close(figure)


if __name__ == "__main__":
    render("events", "Initial event comparison: two attempts per condition", ("llms", "guidance", "skill"))
    render("repeat", "Repeat event comparison: five attempts per condition", ("llms", "skill"))
