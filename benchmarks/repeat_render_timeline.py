"""Plot adopted runtime checkpoints using each run's contemporaneous baseline."""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmarks/results/repeat-render"
CHECKPOINTS = [
    (1, "Initial six areas", "final-comparison.json"),
    (2, "Selection and attributes", "round2-comparison.json"),
    (4, "Retain empty frames", "round4-comparison.json"),
    (6, "Skip active graph scope", "round6-comparison.json"),
    (9, "Input constness loop", "round9-comparison.json"),
    (10, "Simple-name evaluation", "round10-comparison.json"),
    (17, "Attribute-output cache", "round17-comparison.json"),
    (18, "Value conversion", "round18-comparison.json"),
    (47, "Current, native ownership", "round47-comparison.json"),
]


def main() -> None:
    """Keep local experiment gains out of the cumulative time series."""
    timeline = []
    for iteration, label, filename in CHECKPOINTS:
        report = json.loads((RESULTS / filename).read_text())
        row = {"iteration": iteration, "checkpoint": label, "report": filename}
        for variant in ("baseline", "candidate", "django"):
            observations = [
                item for item in report["observations"] if item["size"] == "lg" and item["variant"] == variant
            ]
            if len(observations) != 5 or any(len(item["warm_samples_ms"]) != 20 for item in observations):
                raise RuntimeError(f"Unexpected checkpoint sampling: {filename}")
            row[f"{variant}_warm_ms"] = statistics.median(item["warm_median_ms"] for item in observations)
            row[f"{variant}_second_ms"] = statistics.median(item["second_ms"] for item in observations)
        row["warm_reduction_percent"] = 100 * (1 - row["candidate_warm_ms"] / row["baseline_warm_ms"])
        row["second_reduction_percent"] = 100 * (1 - row["candidate_second_ms"] / row["baseline_second_ms"])
        row["django_ratio"] = row["candidate_warm_ms"] / row["django_warm_ms"]
        timeline.append(row)
    (RESULTS / "performance-timeline.json").write_text(json.dumps(timeline, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), layout="constrained")
    x = [0, *(row["iteration"] for row in timeline)]
    axes[0].plot(x, [0, *(row["warm_reduction_percent"] for row in timeline)], "o-", color="#1769aa")
    axes[0].set(
        ylabel="Warm render time reduction (%)",
        xlabel="Research iteration",
        title="Cumulative reduction vs original Citry",
    )
    axes[0].set_ylim(bottom=0)
    for variant, label, color in (
        ("baseline", "Original Citry", "#8b8b8b"),
        ("candidate", "Adopted Citry", "#1769aa"),
        ("django", "Django scenario", "#238b45"),
    ):
        axes[1].plot(
            [row["iteration"] for row in timeline],
            [row[f"{variant}_warm_ms"] for row in timeline],
            "o-",
            label=label,
            color=color,
        )
    axes[1].set(
        ylabel="Warm median (ms/render)", xlabel="Research iteration", title="Contemporaneous checkpoint comparisons"
    )
    axes[1].legend(frameon=False)
    for axis in axes:
        axis.grid(alpha=0.2)
    fig.suptitle("Large scenario: measured adopted-runtime checkpoints, not added prototype savings")
    fig.savefig(RESULTS / "performance-timeline.png", dpi=180)
    fig.savefig(RESULTS / "performance-timeline.svg")
    plt.close(fig)
    lines = [
        "## Performance across adopted checkpoints",
        "",
        "Each row compares the adopted runtime with the original branch and Django in",
        "the same five-round run, using 20 warm samples per process after six renders.",
        "The x-axis shows research progression, not elapsed engineering hours; straight",
        "lines connect measured checkpoints and do not locate intervening gains.",
        "Differences between rows include desktop timing variation, so individual",
        "changes must be assessed through the local comparisons above.",
        "",
        "| Iteration | Adopted checkpoint | Original Citry, ms | Adopted Citry, ms |"
        " Reduction | Django, ms | Citry / Django |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in timeline:
        lines.append(
            f"| {row['iteration']} | {row['checkpoint']} | {row['baseline_warm_ms']:.3f} |"
            f" {row['candidate_warm_ms']:.3f} | {row['warm_reduction_percent']:.2f}% |"
            f" {row['django_warm_ms']:.3f} | {row['django_ratio']:.2f}x |"
        )
    last = timeline[-1]
    lines.extend(
        [
            "",
            f"The current warm comparison is **{last['baseline_warm_ms']:.3f} to {last['candidate_warm_ms']:.3f} ms,"
            f" a {last['warm_reduction_percent']:.2f}% reduction**;",
            f"Django takes {last['django_warm_ms']:.3f} ms,"
            f" leaving Citry at {last['django_ratio']:.2f} times its time.",
            f"Actual second-render medians are {last['baseline_second_ms']:.3f}"
            f" to {last['candidate_second_ms']:.3f} ms",
            f"({last['second_reduction_percent']:.2f}% lower), with Django at {last['django_second_ms']:.3f} ms.",
            "Second-render figures contain only five observations per variant.",
            "",
            "The current measurement uses unchanged production runtime code from `b11a895`,",
            "at research HEAD `e0c77ad1`; both Citry checkouts load the same current release",
            "ABI3 binary, and the original checkout's binary was restored afterward.",
            "Earlier checkpoints use their then-current matching native artifacts.",
            "Citry emits 1,013,746 bytes and Django 456,422 bytes in these scenarios:",
            "the comparison includes different output and framework features.",
            "",
            "![Performance across measured checkpoints]"
            "(../../benchmarks/results/repeat-render/performance-timeline.png)",
            "",
            "[Raw timeline](../../benchmarks/results/repeat-render/performance-timeline.json),",
            "[current observations](../../benchmarks/results/repeat-render/round47-comparison.json),",
            "[current provenance](../../benchmarks/results/repeat-render/round47-comparison-provenance.json).",
            "Regenerate with `uv run --no-project --with matplotlib python benchmarks/repeat_render_timeline.py`.",
        ]
    )
    target = ROOT / "docs/design/repeat_render_experiment_summary.md"
    before, rest = target.read_text().split("<!-- timeline:start -->")
    _, after = rest.split("<!-- timeline:end -->")
    target.write_text(before + "<!-- timeline:start -->\n" + "\n".join(lines) + "\n<!-- timeline:end -->" + after)


if __name__ == "__main__":
    main()
