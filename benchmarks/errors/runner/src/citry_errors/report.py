"""Write the stage matrix for one run as Markdown and compact JSON."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .config import OUTCOMES, REPO_ROOT, STATIC_STAGES, load_catalogue, load_frameworks

# One short letter per outcome keeps the matrix readable at 24 x 6 cells.
# A runtime warning shares R with a runtime error; the `w` mark tells them apart.
SHORT = {
    "editor": "E",
    "check": "C",
    "build": "B",
    "runtime-error": "R",
    "runtime-warning": "R",
    "silent": "S",
    "never": "N",
    "not-run": "?",
    "not-applicable": "n/a",
    "prevented": "P",
    "missing": "-",
}

# What each cell code means. matrix.md shows it as the legend, and the docs
# page reads it from results.json, so the two never drift apart.
CODES = (
    ("E", "reported in the editor"),
    ("C", "reported by a command-line check, type check or linter"),
    ("B", "reported by the production build"),
    ("R", "reported at runtime by a server error, an error response or a browser error (Rw: only a warning)"),
    ("w", "the stage before it gave only a warning; after the comma, the first stage that gave an error, or S or N"),
    ("S", "nothing reports it, and the page looks or behaves differently"),
    ("N", "nothing reports it, and the page looks the same"),
    ("?", "the runtime check was skipped and no tool reported it"),
    ("P", "the framework's design prevents the mistake"),
    ("-", "no case was written for this framework"),
    ("n/a", "the mistake has no natural equivalent in this framework"),
    ("!", "the clean app reported problems in this run, so the cell is unreliable"),
    ("~", "a tool timed out or skipped this case, so it may have caught the mistake earlier"),
    ("°", "the report points away from the change, and the case explains why it still counts"),
)
LEGEND = "| Code | Meaning |\n| --- | --- |\n" + "".join(f"| {code} | {meaning} |\n" for code, meaning in CODES)


# Enough of a tool's message to recognise the finding; the full output stays in the run folder.
_EVIDENCE_CHARS = 300

# Citry comes first, so every other column reads as a comparison with it; then
# the Python server stacks, then the TypeScript frameworks.
ORDER = ("citry", "django", "jinja", "fasthtml", "nuxt", "next")

CATEGORIES = {
    "naming": "Names: components, inputs, slots, variables",
    "types": "Types",
    "templates": "Template and script syntax",
    "html": "HTML and CSS",
    "events": "Events and server requests",
    "server-browser": "Server and browser",
}

# The six ways a mistake can end, from best to worst. A developer is better
# off the earlier a mistake is reported and the louder the report.
BUCKETS = {
    "static-error": "Error before running",
    "static-warning": "Warning before running",
    "runtime-error": "Error at runtime",
    "runtime-warning": "Warning at runtime",
    "silent": "Missed, page wrong",
    "never": "Missed, no visible change",
}


def bucket(record: dict) -> str | None:
    """Put a scored case in the first of the six buckets it reaches, or None when it was not scored."""
    if record["status"] != "ported":
        return None
    strict, lenient = record["strict"], record["lenient"]
    if strict in STATIC_STAGES:
        return "static-error"
    if lenient in STATIC_STAGES:
        return "static-warning"
    if strict == "runtime-error":
        return "runtime-error"
    if lenient == "runtime-warning":
        return "runtime-warning"
    return strict if strict in {"silent", "never"} else None


def cell(record: dict) -> str:
    """Show the earliest report, and when it was only a warning, the first error after it."""
    if record["status"] != "ported":
        return SHORT[record["status"]]
    if record["strict"] == record["lenient"]:
        return _cell(record, "strict")
    return f"{_cell(record, 'lenient')}w, {_cell(record, 'strict')}"


def _cell(record: dict, column: str) -> str:
    if record["status"] != "ported":
        return SHORT[record["status"]]
    mark = "" if record.get("baseline_clean", True) else "!"
    # A stage that timed out before the stage shown could have reported the
    # mistake, so the cell may be later than the truth.
    # `not-run` comes after every stage, so any timed-out stage could have been earlier.
    outcome = OUTCOMES.index(record[column]) if record[column] in OUTCOMES else len(OUTCOMES)
    mark += (
        "~"
        if any(stage["timed_out"] and OUTCOMES.index(stage["stage"]) < outcome for stage in record.get("stages", []))
        else ""
    )
    mark += "°" if record.get("indirect") else ""
    return SHORT[record[column]] + mark


def _public(text: str) -> str:
    """Make one evidence line fit to publish: no local folders, and short enough to read on hover."""
    # A traceback names the machine's folders, which say nothing about the result.
    text = text.replace(str(REPO_ROOT) + "/", "").replace(str(Path.home()), "~")
    return text if len(text) <= _EVIDENCE_CHARS else text[: _EVIDENCE_CHARS - 3] + "..."


def write(run_dir: Path, output: Path) -> None:
    records = [json.loads(line) for line in (run_dir / "results.jsonl").read_text().splitlines() if line]
    mistakes = load_catalogue()
    frameworks = load_frameworks()
    present = {record["framework"] for record in records}
    keys = [key for key in ORDER if key in present] + sorted(present - set(ORDER))
    by = {(record["mistake"], record["framework"]): record for record in records}
    names = " | ".join(frameworks[key].name for key in keys)
    source_file = run_dir / "run.json"
    source = json.loads(source_file.read_text()) if source_file.is_file() else {}
    lines = [f"# Error-prevention results, run {run_dir.name}", ""]
    if source:
        dirty = " plus uncommitted changes to the benchmark" if source["benchmark_files_changed"] else ""
        lines += [f"Cases and tools from commit `{source['commit']}`{dirty}.", ""]

    lines += ["## How each mistake ended", "", f"| Outcome | {names} |", "| --- |" + " --- |" * len(keys)]
    counts = {
        key: Counter(bucket(record) or record["status"] for record in records if record["framework"] == key)
        for key in keys
    }
    for outcome, label in (
        *BUCKETS.items(),
        ("not-applicable", "Does not apply"),
        ("prevented", "Prevented by design"),
        ("ported", "Not scored (runtime skipped)"),
        ("missing", "No case written"),
    ):
        if any(counts[key][outcome] for key in keys) or outcome in BUCKETS:
            lines.append(f"| {label} | " + " | ".join(str(counts[key][outcome]) for key in keys) + " |")
    lines += ["", "## Every mistake", "", LEGEND, f"| Mistake | {names} |", "| --- |" + " --- |" * len(keys)]
    for category, heading in CATEGORIES.items():
        group = [mistake for mistake in mistakes if mistake.category == category]
        if not group:
            continue
        lines.append(f"| **{heading}** |" + " |" * len(keys))
        for mistake in group:
            cells = [cell(by[(mistake.id, key)]) if (mistake.id, key) in by else "-" for key in keys]
            lines.append(f"| {mistake.title} | " + " | ".join(cells) + " |")
    lines.append("")
    output.mkdir(parents=True, exist_ok=True)
    (output / "matrix.md").write_text("\n".join(lines))

    titles = {mistake.id: mistake for mistake in mistakes}
    compact = [
        {
            key: record.get(key)
            for key in (
                "framework",
                "mistake",
                "status",
                "reason",
                "strict",
                "lenient",
                "baseline_clean",
                "timed_out",
                "indirect",
                "accepted_indirect",
                "unconfirmed_indirect",
            )
        }
        | {
            "category": titles[record["mistake"]].category,
            "bucket": bucket(record),
            "cell": cell(record),
            "evidence": [
                _public(f"{stage['label']}: {finding['code']} {finding['message']}")
                for stage in record.get("stages", [])
                for finding in stage["evidence"] + stage["indirect"]
            ][:5]
            + [_public(line) for line in (record.get("runtime") or {}).get("evidence", [])[:5]],
        }
        for record in records
    ]
    # The docs page reads this file, so it carries the order and the labels too.
    summary = {
        "run": run_dir.name,
        "source": source,
        "frameworks": [{"key": key, "name": frameworks[key].name} for key in keys],
        "categories": [{"id": key, "heading": heading} for key, heading in CATEGORIES.items()],
        "buckets": [{"id": key, "label": label} for key, label in BUCKETS.items()],
        "codes": [{"code": code, "meaning": meaning} for code, meaning in CODES],
        "mistakes": [{"id": mistake.id, "title": mistake.title, "category": mistake.category} for mistake in mistakes],
        "results": compact,
    }
    (output / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
