"""Write the run's report as one self-contained HTML file that opens from disk.

The page follows the framework interaction benchmark's report: white cards on
a light page, each chart an SVG with its legend on top, framework groups with
bold headings, and light grid lines with an axis. It draws the same data as results.json: a stacked bar per
framework with the six outcomes, then every mistake grouped by category. It
has no scripts and loads nothing, so it reads the same in any browser,
offline.
"""

from __future__ import annotations

import math
from html import escape
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

if TYPE_CHECKING:
    from pathlib import Path

# Greens: reported before the app ran; oranges: at runtime; red: nothing
# reported it. The lighter shade of each pair is the warning, so a
# warning reads as a weaker form of the error beside it. The docs page's
# chart (docs_site/_internal/components/error_benchmark.py) uses the same colors.
BUCKET_COLORS = {
    "static-error": "#2f855a",
    "static-warning": "#9ae6b4",
    "runtime-error": "#dd6b20",
    "runtime-warning": "#f6c177",
    "missed": "#c53030",
}

# A mistake that cannot be written in a framework still takes its share of
# the bar, just before the misses, so every bar counts all the mistakes.
NOT_APPLICABLE = ("N/A or prevented", "#cbd5e0")

# The outcomes in which a tool or the running app reported the mistake.
CAUGHT = ("static-error", "static-warning", "runtime-error", "runtime-warning")

# A case the runtime check skipped still takes its share of the bar, drawn
# apart, so a partial run cannot pass for a finished one.
NOT_SCORED = ("Not scored (runtime check skipped)", "#e2e8f0")
NO_CASE = ("No case written", "#a0aec0")

# The interaction benchmark's report groups frameworks the same way, so a
# reader of both finds each framework in the same place.
GROUPS: tuple[tuple[str | None, tuple[str, ...]], ...] = (
    (None, ("citry",)),
    ("Django libraries", ("django", "rusty", "jinja", "tetra", "unicorn", "django-components")),
    ("Other Python libraries", ("fasthtml", "reactpy", "reflex")),
    ("JavaScript SSR", ("next", "nuxt")),
)

# Segment colors on which dark text reads better than white; on the orange,
# white text at this size would fall short of the WCAG AA contrast ratio.
_DARK_TEXT = {"#9ae6b4", "#f6c177", "#cbd5e0", "#dd6b20", "#e2e8f0", "#a0aec0"}

# Chart geometry in SVG units, matching the interaction report's charts.
_WIDTH = 700
_LABEL_RIGHT = 168
_BAR_LEFT = 180
_BAR_WIDTH = 490
_ROW = 36
_HEADING_ROW = 28
_BAR_HEIGHT = 20
_REFERENCE_COLOR = "#2455a0"

_CSS = """
:root{color-scheme:light;font:14px system-ui;color:#172638;background:#f3f6fa}
body{max-width:1500px;margin:0 auto;padding:28px}h1{font-size:24px;margin-bottom:6px}
p{line-height:1.5;max-width:1000px}.muted{color:#526275}
.group-body{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,580px),1fr));gap:18px;margin-top:10px}
article.chart{max-width:780px;background:white;border:1px solid #dbe3ed;border-radius:12px;padding:18px;min-width:0}
h2{font-size:19px;margin:0;display:inline}h3{font-size:16px;margin:0;display:inline}
.description{font-size:13px;color:#526275;margin:6px 0 10px}
details>summary{cursor:pointer;list-style:none}details>summary::-webkit-details-marker{display:none}
details>summary::before{content:'\\25B8';display:inline-block;width:1.1em;color:#526275}
details[open]>summary::before{content:'\\25BE'}
section.group{margin-top:24px}
.chart.wide{max-width:none;grid-column:1/-1}
svg{width:100%;height:auto;display:block}svg text{font-family:system-ui;font-size:11px;fill:#26394c}
.download{display:inline-block;font-size:12px;margin-top:8px;color:#2455a0}
.notice{padding:10px 14px;background:#fff2d6;border-radius:8px;max-width:1000px;font-size:13px}
.table-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:12px}
th,td{border-bottom:1px solid #e0e7ef;padding:4px 8px;text-align:center}
th:first-child,td:first-child{text-align:left}
thead th{color:#526275;font-weight:600;border-bottom:1px solid #dbe3ed}
tr.category th{padding-top:12px;font-weight:700;border-bottom:1px solid #dbe3ed}
tr.category td{padding-top:12px;color:#526275;border-bottom:1px solid #dbe3ed}
tr.counts td{color:#526275;font-weight:400}
tbody th[scope=row]{font-weight:400}
td.cell{white-space:nowrap;font-variant-numeric:tabular-nums}
dl.codes{display:grid;grid-template-columns:max-content 1fr;gap:2px 10px;font-size:12px;margin:14px 0 0}
dl.codes dt{font-weight:700;font-family:ui-monospace,monospace}dl.codes dd{margin:0;color:#526275}
footer{font-size:12px;color:#526275;margin-top:20px}
@media(max-width:600px){body{padding:14px}article.chart{padding:10px}}
"""


def _part(record: dict[str, Any]) -> str:
    """Return the bar part a record counts towards."""
    if record["status"] in {"not-applicable", "prevented"}:
        return "n/a"
    if record["status"] == "missing":
        return "no-case"
    return record["bucket"] or "not-scored"


def _ticks(maximum: int) -> list[int]:
    """Grid lines from 0 up to the first one at or above `maximum`, at most five intervals.

    From ten up the step is a multiple of 5, because readers count in fives
    and tens more easily than in sixes; below ten it is 1 or 2.
    """
    steps = (1, 2) if maximum < 10 else (5, 10, 20, 25, 50, 100)
    step = next((step for step in steps if step * 5 >= maximum), steps[-1])
    return list(range(0, math.ceil(maximum / step) * step + 1, step))


def chart_svg(summary: dict[str, Any]) -> str:
    """Draw the stacked outcome bars as a standalone SVG document."""
    labels = {row["id"]: row["label"] for row in summary["buckets"]}
    reported = {key: (labels[key], BUCKET_COLORS[key]) for key in CAUGHT}
    parts = (
        reported
        | {"n/a": NOT_APPLICABLE, "missed": (labels["missed"], BUCKET_COLORS["missed"])}
        | {"not-scored": NOT_SCORED, "no-case": NO_CASE}
    )
    names = {row["key"]: row["name"] for row in summary["frameworks"]}
    counts = {
        key: {
            part: sum(1 for row in summary["results"] if row["framework"] == key and _part(row) == part)
            for part in parts
        }
        for key in names
    }
    shown = [part for part in parts if part in BUCKET_COLORS or any(counts[key][part] for key in names)]
    # Every bar counts all the mistakes; the axis ends at the next round tick.
    totals = {key: sum(counts[key].values()) for key in names}
    ticks = _ticks(max(totals.values()))
    scale = _BAR_WIDTH / ticks[-1]

    title = "How each mistake ended, per framework"
    legend: list[str] = []
    # Legend: three columns, as in the interaction report.
    for index, part in enumerate(shown):
        x, y = 12 + (index % 3) * 229, 12 + (index // 3) * 20
        label, color = parts[part]
        legend.append(f'<rect x="{x}" y="{y}" width="11" height="11" fill="{color}"/>')
        legend.append(f'<text x="{x + 16}" y="{y + 10}">{escape(label)}</text>')
    # The extra room above the bars holds the dashed line's label.
    top = 12 + math.ceil(len(shown) / 3) * 20 + 34

    rows: list[str] = []
    y = top
    known = {key for _, keys in GROUPS for key in keys}
    groups = [*GROUPS, ("Other frameworks", tuple(key for key in names if key not in known))]
    for heading, group_keys in groups:
        keys = tuple(key for key in group_keys if key in names)
        if not keys:
            continue
        if heading:
            y += 8
            rows.append(
                f'<text x="{_LABEL_RIGHT}" y="{y + 12}" font-weight="700" text-anchor="end">{escape(heading)}</text>'
            )
            y += _HEADING_ROW
        for key in keys:
            row = counts[key]
            rows.append(f'<text x="{_LABEL_RIGHT}" y="{y + 14}" text-anchor="end">{escape(names[key])}</text>')
            x = float(_BAR_LEFT)
            for part in shown:
                count = row[part]
                if not count:
                    continue
                label, color = parts[part]
                width = count * scale
                tip = f"{names[key]}, {label}: {count}"
                rows.append(
                    f'<rect x="{x:.2f}" y="{y}" width="{width:.2f}" height="{_BAR_HEIGHT}" fill="{color}"'
                    f' tabindex="0" aria-label="{escape(tip)}"><title>{escape(tip)}</title></rect>'
                )
                if width >= 14:
                    fill = "#172638" if color in _DARK_TEXT else "#ffffff"
                    rows.append(
                        f'<text x="{x + width / 2:.2f}" y="{y + 14}" text-anchor="middle"'
                        f' style="fill:{fill}">{count}</text>'
                    )
                x += width
            y += _ROW
    bottom = y
    grid = []
    for tick in ticks:
        gx = _BAR_LEFT + tick * scale
        grid.append(f'<line x1="{gx:.2f}" x2="{gx:.2f}" y1="{top - 5}" y2="{bottom}" stroke="#e0e7ef"/>')
        grid.append(f'<text x="{gx:.2f}" y="{bottom + 22}" text-anchor="middle">{tick}</text>')
    # The dashed line marks where Citry's count of mistakes reported before
    # the app runs (errors plus warnings) ends, so a reader sees which frameworks report more or fewer
    # mistakes before the app runs. It is drawn over the bars.
    reference = []
    if "citry" in names:
        static = counts["citry"]["static-error"] + counts["citry"]["static-warning"]
        rx = _BAR_LEFT + static * scale
        reference = [
            f'<line x1="{rx:.2f}" x2="{rx:.2f}" y1="{top - 5}" y2="{bottom}" stroke="{_REFERENCE_COLOR}"'
            ' stroke-width="2" stroke-dasharray="5 4"/>',
            f'<text x="{rx:.2f}" y="{top - 9}" text-anchor="middle" font-weight="700"'
            f' style="fill:{_REFERENCE_COLOR}">{escape(names["citry"])} static/IDE: {static}</text>',
        ]
    height = bottom + 36
    body = "".join(legend + grid + rows + reference)
    return (
        f'<svg viewBox="0 0 {_WIDTH} {height}" role="img" aria-label="{escape(title)}"'
        ' xmlns="http://www.w3.org/2000/svg"><style>text{font:11px system-ui;fill:#26394c}'
        'text[font-weight="700"]{font-weight:700}</style>'
        f"<title>{escape(title)}</title>{body}</svg>"
    )


def _caught_total(by: dict[tuple[str, str], dict[str, Any]], framework: str, mistake_ids: list[str]) -> str:
    """Count the mistakes a framework reported at all, out of those that apply to it."""
    scored = [
        by[framework, mistake]
        for mistake in mistake_ids
        if (framework, mistake) in by and by[framework, mistake]["status"] == "ported"
    ]
    caught = sum(record.get("bucket") in CAUGHT for record in scored)
    return f"({caught}/{len(scored)})"


def _tint(color: str) -> str:
    # A light mix of the bucket color keeps the cell's code readable.
    return f"background: color-mix(in srgb, {color} 30%, white)"


def checkout_packages(source: dict[str, Any]) -> list[tuple[str, str, bool]]:
    """
    Give each framework a run installed partly from this repository's sources, instead of a release.

    Each item is the framework's key, its packages with their versions
    ("citry 0.6.0 and citry-lsp 0.2.0"), and whether those sources had
    uncommitted changes. The version is the one the sources declare, which
    a release may not have yet.
    """
    return [
        (
            key,
            " and ".join(f"{package['name']} {package['version']}".strip() for package in packages),
            any(package["changed"] for package in packages),
        )
        for key, packages in (source.get("from_checkout") or {}).items()
    ]


def render(summary: dict[str, Any]) -> str:
    frameworks = summary["frameworks"]
    by = {(row["framework"], row["mistake"]): row for row in summary["results"]}
    total = len(summary["mistakes"])
    svg = chart_svg(summary)

    out = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Error-prevention benchmark</title>",
        f"<style>{_CSS}</style></head><body>",
        "<h1>Error-prevention benchmark</h1>",
        f'<p class="muted">The same {total} developer mistakes, written in each framework where they apply. '
        "Each one is counted where it was first reported: an error or a warning before the app runs "
        "(editor, check or build), an error or a warning at runtime, or not at all. Earlier is better. "
        "Hover or focus a bar part, or a table cell, for its details.</p>",
    ]
    source = summary.get("source") or {}
    notice = f"Run {escape(summary['run'])}"
    if source:
        notice += f": cases and tools from commit {escape(source['commit'][:12])}"
        if source.get("inputs_tree"):
            notice += f", benchmark inputs tree {escape(source['inputs_tree'][:12])}"
        changed = source.get("inputs_changed", source.get("benchmark_files_changed"))
        notice += ", with uncommitted benchmark changes" if changed else ""
    out.append(f'<p class="notice">{notice}.</p>')
    names = {framework["key"]: framework["name"] for framework in summary["frameworks"]}
    for key, packages, dirty in checkout_packages(source):
        # The commit is the run's own: the benchmark and the packages come from one checkout.
        out.append(
            f'<p class="notice">{escape(names.get(key, key))}: {escape(packages)} built from this '
            f"repository at commit {escape(source['commit'][:12])}"
            f"{' plus uncommitted changes to them' if dirty else ''}, not a published release.</p>"
        )

    out.append('<section class="group"><details open><summary><h2>Outcomes</h2></summary><div class="group-body">')
    out.append('<article class="chart"><details open><summary><h3>How each mistake ended</h3></summary>')
    out.append(
        '<p class="description">One bar per framework, covering every mistake. '
        "Green: reported before running; orange: at runtime; gray: N/A or prevented; red: missed. "
        "The lighter shade of each pair is a warning.</p>"
    )
    out.append(svg)
    href = "data:image/svg+xml;charset=utf-8," + quote(svg)
    out.append(f'<a class="download" download="error-outcomes.svg" href="{href}">Download SVG</a>')
    out.append("</details></article></div></details></section>")

    out.append(
        '<section class="group"><details open><summary><h2>Every mistake</h2></summary><div class="group-body">'
    )
    out.append('<article class="chart wide"><div class="table-wrap"><table><thead><tr><th>Mistake</th>')
    out += [f'<th scope="col">{escape(framework["name"])}</th>' for framework in frameworks]
    out.append('</tr><tr class="counts"><td>(caught/total)</td>')
    every = [mistake["id"] for mistake in summary["mistakes"]]
    out += [f"<td>{_caught_total(by, framework['key'], every)}</td>" for framework in frameworks]
    out.append("</tr></thead><tbody>")
    for category in summary["categories"]:
        group = [mistake for mistake in summary["mistakes"] if mistake["category"] == category["id"]]
        if not group:
            continue
        ids = [mistake["id"] for mistake in group]
        out.append(f'<tr class="category"><th scope="rowgroup">{escape(category["heading"])}</th>')
        out += [f"<td>{_caught_total(by, framework['key'], ids)}</td>" for framework in frameworks]
        out.append("</tr>")
        for mistake in group:
            out.append(f'<tr><th scope="row">{escape(mistake["title"])}</th>')
            for framework in frameworks:
                record = by.get((framework["key"], mistake["id"]))
                if record is None:
                    out.append("<td>-</td>")
                    continue
                color = BUCKET_COLORS.get(record.get("bucket") or "")
                style = f' style="{_tint(color)}"' if color else ""
                hover = ("\n".join(record.get("evidence") or []) or record.get("reason") or "").strip()
                title = f' title="{escape(hover)}"' if hover else ""
                out.append(f'<td class="cell"{style}{title}>{escape(record["cell"])}</td>')
            out.append("</tr>")
    out.append("</tbody></table></div>")
    # The codes explain the table, so they follow it rather than push it down the page.
    out.append('<dl class="codes">')
    for row in summary["codes"]:
        out.append(f"<dt>{escape(row['code'])}</dt><dd>{escape(row['meaning'])}</dd>")
    out.append("</dl></article></div></details></section>")
    out.append(
        "<footer>Written by the error-prevention runner in benchmarks/errors. "
        "results.json beside this file has the same data.</footer>"
    )
    out.append("</body></html>")
    return "\n".join(out) + "\n"


def write(summary: dict[str, Any], output: Path) -> None:
    (output / "report.html").write_text(render(summary), encoding="utf-8")
