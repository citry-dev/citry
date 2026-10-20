"""Write the run's report as one self-contained HTML file that opens from disk.

The page draws the same data as results.json: a stacked bar per framework
with the six outcomes, then every mistake grouped by category. It has no
scripts and loads nothing, so it reads the same in any browser, offline.
"""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

# Greens: reported before the app ran; oranges: at runtime; red and dark gray:
# nothing reported it. The lighter shade of each pair is the warning, so a
# warning reads as a weaker form of the error beside it. The docs page's
# chart (docs_site/_internal/components/error_benchmark.py) uses the same colors.
BUCKET_COLORS = {
    "static-error": "#2f855a",
    "static-warning": "#9ae6b4",
    "runtime-error": "#dd6b20",
    "runtime-warning": "#f6c177",
    "silent": "#c53030",
    "never": "#4a5568",
}

# Records outside the six buckets still take their share of the bar, so
# every bar is as long as the number of mistakes.
EXTRA = {
    "not-scored": ("Not scored (runtime check skipped)", "#e2e8f0"),
    "no-case": ("No case written", "#a0aec0"),
    "does-not-apply": ("Does not apply or prevented by design", "#cbd5e0"),
}

_CSS = """
:root {
  --bg: #ffffff; --fg: #1a202c; --muted: #4a5568; --line: #e2e8f0; --head: #f7fafc;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #171923; --fg: #e2e8f0; --muted: #a0aec0; --line: #2d3748; --head: #1f2533; }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 24px 16px 48px; background: var(--bg); color: var(--fg);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
}
main { max-width: 1100px; margin: 0 auto; }
h1 { font-size: 1.6rem; margin: 0 0 4px; }
h2 { font-size: 1.2rem; margin: 32px 0 8px; }
.meta { color: var(--muted); margin: 0 0 20px; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 16px; padding: 0; margin: 0 0 12px; list-style: none; }
.legend li { display: flex; align-items: center; gap: 6px; }
.swatch { width: 14px; height: 14px; border-radius: 3px; flex: none; }
.row { display: grid; grid-template-columns: 190px 1fr 36px; gap: 10px; align-items: center; margin: 6px 0; }
.row .name { text-align: right; }
.row.reference .name { font-weight: 700; }
.bar { display: flex; height: 26px; border-radius: 4px; overflow: hidden; background: var(--line); }
.part { display: flex; align-items: center; justify-content: center; font-size: 12px; color: #fff; }
.part.light { color: #1a202c; }
.total { font-weight: 700; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { border: 1px solid var(--line); padding: 4px 8px; text-align: center; }
th:first-child, td:first-child { text-align: left; }
thead th { background: var(--head); position: sticky; top: 0; }
tr.group th { background: var(--head); text-align: left; font-weight: 700; }
td.cell { white-space: nowrap; }
.wrap { overflow-x: auto; }
dl.codes { display: grid; grid-template-columns: max-content 1fr; gap: 2px 12px; margin: 0 0 12px; }
dl.codes dt { font-weight: 700; font-family: ui-monospace, monospace; }
dl.codes dd { margin: 0; }
@media (max-width: 640px) {
  .row { grid-template-columns: 1fr 36px; }
  .row .name { grid-column: 1 / -1; text-align: left; }
}
"""

# Shades light enough that black text reads better on them than white.
_LIGHT = {"#9ae6b4", "#f6c177", "#cbd5e0", "#e2e8f0", "#a0aec0"}


def _part(record: dict[str, Any]) -> str:
    """Return the bar part one record counts towards."""
    if record["status"] in {"not-applicable", "prevented"}:
        return "does-not-apply"
    if record["status"] == "missing":
        return "no-case"
    return record["bucket"] or "not-scored"


def _tint(color: str) -> str:
    # A light mix of the bucket color keeps the cell's code readable in both themes.
    return f"background: color-mix(in srgb, {color} 35%, var(--bg))"


def render(summary: dict[str, Any]) -> str:
    frameworks = summary["frameworks"]
    labels = {row["id"]: row["label"] for row in summary["buckets"]}
    parts = {key: (labels[key], color) for key, color in BUCKET_COLORS.items()} | EXTRA
    by = {(row["framework"], row["mistake"]): row for row in summary["results"]}
    total = len(summary["mistakes"])

    counts = {
        framework["key"]: {
            key: sum(1 for row in summary["results"] if row["framework"] == framework["key"] and _part(row) == key)
            for key in parts
        }
        for framework in frameworks
    }
    # A part that no framework has stays out of the legend; the six outcomes always show.
    shown = [key for key in parts if key in BUCKET_COLORS or any(counts[f["key"]][key] for f in frameworks)]

    out = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Error-prevention results</title>",
        f"<style>{_CSS}</style></head><body><main>",
        "<h1>Error-prevention results</h1>",
    ]
    source = summary.get("source") or {}
    meta = f"Run {escape(summary['run'])}"
    if source:
        meta += f", cases and tools from commit <code>{escape(source['commit'][:12])}</code>"
        meta += " with uncommitted benchmark changes" if source.get("benchmark_files_changed") else ""
    out.append(f'<p class="meta">{meta}. The same {total} mistakes in each framework; earlier is better.</p>')

    out.append("<h2>How each mistake ended</h2>")
    out.append('<ul class="legend">')
    for key in shown:
        label, color = parts[key]
        out.append(f'<li><span class="swatch" style="background:{color}"></span>{escape(label)}</li>')
    out.append("</ul>")
    out.append('<div role="img" aria-label="Stacked bars of how each mistake ended, per framework">')
    for index, framework in enumerate(frameworks):
        row_counts = counts[framework["key"]]
        reference = " reference" if index == 0 else ""
        out.append(
            f'<div class="row{reference}"><span class="name">{escape(framework["name"])}</span><span class="bar">'
        )
        for key in shown:
            count = row_counts[key]
            if not count:
                continue
            label, color = parts[key]
            light = " light" if color in _LIGHT else ""
            out.append(
                f'<span class="part{light}" style="width:{count / total * 100:.3f}%;background:{color}"'
                f' title="{escape(label)}: {count}">{count}</span>'
            )
        out.append(
            f'</span><span class="total" title="Error before running">{row_counts["static-error"]}</span></div>'
        )
    out.append("</div>")

    # The same counts as numbers, for exact values and for screen readers.
    out.append('<div class="wrap"><table><thead><tr><th>Outcome</th>')
    out += [f"<th>{escape(framework['name'])}</th>" for framework in frameworks]
    out.append("</tr></thead><tbody>")
    for key in shown:
        out.append(f"<tr><td>{escape(parts[key][0])}</td>")
        out += [f"<td>{counts[framework['key']][key]}</td>" for framework in frameworks]
        out.append("</tr>")
    out.append("</tbody></table></div>")

    out.append("<h2>Every mistake</h2>")
    out.append('<dl class="codes">')
    for row in summary["codes"]:
        out.append(f"<dt>{escape(row['code'])}</dt><dd>{escape(row['meaning'])}</dd>")
    out.append("</dl>")
    out.append(
        '<p class="meta">Hover over a cell to see what the tools printed, or why the mistake does not apply.</p>'
    )
    out.append('<div class="wrap"><table><thead><tr><th>Mistake</th>')
    out += [f"<th>{escape(framework['name'])}</th>" for framework in frameworks]
    out.append("</tr></thead><tbody>")
    for category in summary["categories"]:
        group = [mistake for mistake in summary["mistakes"] if mistake["category"] == category["id"]]
        if not group:
            continue
        out.append(f'<tr class="group"><th colspan="{len(frameworks) + 1}" scope="rowgroup">')
        out.append(f"{escape(category['heading'])}</th></tr>")
        for mistake in group:
            out.append(f'<tr><th scope="row" style="font-weight:400">{escape(mistake["title"])}</th>')
            for framework in frameworks:
                record = by.get((framework["key"], mistake["id"]))
                if record is None:
                    out.append("<td>-</td>")
                    continue
                color = BUCKET_COLORS.get(record.get("bucket") or "")
                style = f' style="{_tint(color)}"' if color else ""
                hover = "\n".join(record.get("evidence") or []) or record.get("reason") or ""
                title = f' title="{escape(hover.strip())}"' if hover.strip() else ""
                out.append(f'<td class="cell"{style}{title}>{escape(record["cell"])}</td>')
            out.append("</tr>")
    out.append("</tbody></table></div>")
    out.append("</main></body></html>")
    return "\n".join(out) + "\n"


def write(summary: dict[str, Any], output: Path) -> None:
    (output / "report.html").write_text(render(summary), encoding="utf-8")
