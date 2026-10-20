"""Write the stage matrix for one run as Markdown and compact JSON."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from . import html_report
from .config import CACHE, OUTCOMES, REPO_ROOT, STATIC_STAGES, load_catalogue, load_frameworks

# One short letter per outcome keeps the matrix readable at 24 x 6 cells.
# A runtime warning shares R with a runtime error; the `w` mark tells them apart.
SHORT = {
    "editor": "E",
    "check": "C",
    "build": "B",
    "runtime-error": "R",
    "runtime-warning": "R",
    # Nothing reported the mistake; whether the page changed does not matter.
    "silent": "M",
    "never": "M",
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
    ("w", "after a letter: that stage gave only a warning, such as Ew for a warning in the editor"),
    ("M", "missed: nothing reports it"),
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
ORDER = ("citry", "django", "rusty", "jinja", "django-components", "fasthtml", "nuxt", "next")

CATEGORIES = {
    "naming": "Names: components, inputs, slots, variables",
    "types": "Types",
    "templates": "Template and script syntax",
    "html": "HTML and CSS",
    "events": "Events and server requests",
    "server-browser": "Server and browser",
}

# The five ways a mistake can end, from best to worst. A developer is better
# off the earlier a mistake is reported and the louder the report. A missed
# mistake is a miss whether or not the page visibly changed.
BUCKETS = {
    "static-error": "Static/IDE error",
    "static-warning": "Static/IDE warning",
    "runtime-error": "Runtime error",
    "runtime-warning": "Runtime warning",
    "missed": "Missed",
}


# The buckets in which some tool or the running app reported the mistake.
CAUGHT = ("static-error", "static-warning", "runtime-error", "runtime-warning")


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
    return "missed" if strict in {"silent", "never"} else None


def caught_total(by: dict, framework: str, mistake_ids: list[str]) -> str:
    """Count the mistakes a framework reported at all, out of those that apply to it, as "(caught/total)"."""
    records = [by[(mistake, framework)] for mistake in mistake_ids if (mistake, framework) in by]
    scored = [record for record in records if record["status"] == "ported"]
    caught = sum(bucket(record) in CAUGHT for record in scored)
    return f"({caught}/{len(scored)})"


def cell(record: dict) -> str:
    """Show where the mistake was first reported, marked `w` when that report was only a warning."""
    if record["status"] != "ported":
        return SHORT[record["status"]]
    if record["strict"] == record["lenient"]:
        return _cell(record, "strict")
    return _cell(record, "lenient", warning=True)


def _cell(record: dict, column: str, *, warning: bool = False) -> str:
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
    return SHORT[record[column]] + ("w" if warning else "") + mark


# An absolute or home-relative folder path that ends in a benchmark cache.
_CACHE_FOLDER = re.compile(r"(?<![\w.~-])~?/[^\s'\"()]*?/\.benchmarks/errors/")


def _public(text: str) -> str:
    """Make one evidence line fit to publish: no local folders, and short enough to read on hover."""
    # A traceback names the machine's folders, which say nothing about the result.
    # A run can keep its cache outside this checkout (CITRY_ERRORS_CACHE, here or
    # when the run was made), so any folder that holds a `.benchmarks/errors`
    # cache is cut back to that name, the way the default cache reads.
    text = text.replace(str(CACHE) + "/", ".benchmarks/errors/")
    text = _CACHE_FOLDER.sub(".benchmarks/errors/", text)
    text = text.replace(str(REPO_ROOT) + "/", "").replace(str(Path.home()), "~")
    # Each dev server listens on a random port, which would change every rerun's file.
    text = re.sub(r"127\.0\.0\.1:\d+", "127.0.0.1:<port>", text)
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
    for key in keys:
        # A mistake that cannot be written in a framework, for either reason, is one row.
        counts[key]["n/a"] = counts[key]["not-applicable"] + counts[key]["prevented"]
    for outcome, label in (
        *((bucket_id, BUCKETS[bucket_id]) for bucket_id in CAUGHT),
        ("n/a", "N/A or prevented"),
        ("missed", BUCKETS["missed"]),
        ("ported", "Not scored (runtime skipped)"),
        ("missing", "No case written"),
    ):
        if any(counts[key][outcome] for key in keys) or outcome in BUCKETS:
            lines.append(f"| {label} | " + " | ".join(str(counts[key][outcome]) for key in keys) + " |")
    lines += ["", "## Every mistake", "", LEGEND, f"| Mistake | {names} |", "| --- |" + " --- |" * len(keys)]
    every = [mistake.id for mistake in mistakes]
    lines.append("| (caught/total) | " + " | ".join(caught_total(by, key, every) for key in keys) + " |")
    for category, heading in CATEGORIES.items():
        group = [mistake for mistake in mistakes if mistake.category == category]
        if not group:
            continue
        ids = [mistake.id for mistake in group]
        lines.append(f"| **{heading}** | " + " | ".join(caught_total(by, key, ids) for key in keys) + " |")
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
                "runtime_skipped",
            )
        }
        | {
            key: [_public(line) for line in record.get(key) or []]
            for key in ("accepted_indirect", "unconfirmed_indirect")
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
    # The same data as a page that opens from disk, with no docs site to start.
    html_report.write(summary, output)
