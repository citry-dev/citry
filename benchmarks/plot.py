"""
Regenerate the README and docs-site performance charts.

The numbers below are the published large-scenario results from
``benchmarks/README.md`` (its "Results (large scenario)" table). They are not
measured here: ``compare.py`` produces them in a controlled run, that table is
the source of truth, and this script only draws it. When the table is
re-measured, update ``SERIES`` and ``CAPTION`` below to match, then re-run.

Requires matplotlib, which is not part of the dev install. Run from the
repository root in an ephemeral environment so the project venv is untouched::

    uv run --no-project --with matplotlib python benchmarks/plot.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Source: benchmarks/README.md "Results (large scenario)", measured 2026-08-21
# (Apple M4, Python 3.14.3, median of 5 fresh-process runs). Times in
# milliseconds, lower is better. Keep SERIES and CAPTION in step with the table.
CAPTION = (
    "Apple M4, Python 3.14.3, median of 5 fresh-process runs.  "
    "django 6.0.6, django-components 0.151.1, jinja2 3.1.6, citry source 0.4.1."
)
METRICS = ["Startup", "Import", "First render", "Repeat render"]
# Each row: engine label, [startup, import, first render, repeat render], bar color.
SERIES = [
    ("Django", [88.51, 78.98, 18.96, 10.95], "#64748b"),
    ("django-components", [82.95, 76.14, 68.39, 50.65], "#f97316"),
    ("jinja2", [16.59, 13.59, 62.26, 6.91], "#3b82f6"),
    ("Citry", [116.03, 99.04, 76.59, 38.65], "#10b981"),
]
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATHS = (
    REPO_ROOT / "docs" / "assets" / "benchmark.png",
    REPO_ROOT / "docs_site" / "static" / "img" / "benchmark.png",
)
BAR_WIDTH = 0.20


def main() -> None:
    """Draw the grouped bar chart and write every configured output copy."""
    x = np.arange(len(METRICS))
    fig, ax = plt.subplots(figsize=(10.5, 5.5), dpi=200)

    for i, (label, values, color) in enumerate(SERIES):
        offset = (i - (len(SERIES) - 1) / 2) * BAR_WIDTH
        bars = ax.bar(
            x + offset, values, BAR_WIDTH, label=label, color=color, edgecolor="white", linewidth=0.6, zorder=3
        )
        ax.bar_label(bars, labels=[f"{v:.0f}" for v in values], padding=2, fontsize=7.5, color="#334155")

    ax.set_xticks(x)
    ax.set_xticklabels(METRICS, fontsize=10.5)
    ax.set_ylabel("Time in milliseconds (lower is better)", fontsize=10)
    ax.set_title("Rendering a large page (~350 Citry component markers)", fontsize=13, pad=10, fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    ax.spines["top"].set(visible=False)
    ax.spines["right"].set(visible=False)
    ax.yaxis.grid(visible=True, color="#e8edf2", linewidth=0.9, zorder=0)
    ax.set(axisbelow=True)
    ax.margins(y=0.16)
    ax.tick_params(length=0)

    fig.text(0.5, 0.015, CAPTION, ha="center", fontsize=7.5, color="#94a3b8")
    fig.tight_layout(rect=(0, 0.04, 1, 1))

    for out_path in OUT_PATHS:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
        print(f"saved {out_path}")


if __name__ == "__main__":
    main()
