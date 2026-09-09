"""
Draw README and docs-site charts from a retained publication benchmark report.

Run with ``uv run --no-project --with matplotlib python benchmarks/plot.py``.
The report supplies every timing value; this script does not measure rendering.
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATHS = (
    REPO_ROOT / "docs" / "assets" / "benchmark.png",
    REPO_ROOT / "docs_site" / "static" / "img" / "benchmark.png",
)
SERIES = (
    ("django", "Django", "#64748b"),
    ("django-components", "django-components", "#f97316"),
    ("jinja2", "Jinja2", "#3b82f6"),
    ("simple", "Citry*", "#10b981"),
)
METRICS = (("first_ms", "First render"), ("second_ms", "Second render"), ("warm_ms", "Warmed render"))


def main() -> None:
    """Draw the measured cells and save identical images for both documentation roots."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=REPO_ROOT / "benchmarks/results/publication-20260910-release-0.5.0.json"
    )
    args = parser.parse_args()
    report = json.loads(args.input.read_text())
    summary = report["summary"]
    blocks = report["measurement"]["blocks"]
    warm_count = report["measurement"]["warm_renders_per_worker"]
    x = np.arange(len(METRICS))
    fig, ax = plt.subplots(figsize=(11, 6), dpi=200)
    width = 0.19
    for index, (key, label, color) in enumerate(SERIES):
        values = [summary[key][metric] for metric, _label in METRICS]
        offset = (index - (len(SERIES) - 1) / 2) * width
        bars = ax.bar(x + offset, values, width, label=label, color=color, edgecolor="white", linewidth=0.6, zorder=3)
        ax.bar_label(bars, labels=[f"{value:.1f}" for value in values], padding=3, fontsize=8, color="#334155")
    ax.set_xticks(x)
    ax.set_xticklabels([label for _key, label in METRICS], fontsize=11)
    ax.set_ylabel("Milliseconds per render (lower is better)", fontsize=10)
    ax.set_title("Rendering a large project page", fontsize=15, pad=32, fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, 1.085), ncol=len(SERIES))
    ax.spines["top"].set(visible=False)
    ax.spines["right"].set(visible=False)
    ax.yaxis.grid(visible=True, color="#e8edf2", linewidth=0.9, zorder=0)
    ax.set(axisbelow=True)
    ax.margins(y=0.13)
    ax.tick_params(length=0)
    caption = (
        f"Apple M4, Python 3.14.3. {blocks} balanced fresh-process blocks; "
        f"{warm_count} retained warm outputs per worker.\n"
        "* Citry uses simple and pure optimizations: citry.dev/advanced/performance/\n"
        "Output and framework features differ.\n"
        "2026-09-10 · Django 6.0.6 · django-components 0.152.0 · Jinja2 3.1.6 · Citry 0.5.0 / Core 1.7.0"
    )
    fig.text(0.5, 0.014, caption, ha="center", fontsize=8, color="#64748b", linespacing=1.5)
    fig.tight_layout(rect=(0, 0.145, 1, 1))
    for path in OUT_PATHS:
        fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
        print(f"saved {path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
