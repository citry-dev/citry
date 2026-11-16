"""Write the stage matrix for one run as Markdown and compact JSON."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from . import html_report
from .config import CACHE, OUTCOMES, REPO_ROOT, STATIC_STAGES, ConfigError, load_catalogue, load_frameworks

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
# the Python frameworks, then the TypeScript frameworks.
ORDER = (
    "citry",
    "django",
    "rusty",
    "jinja",
    "tetra",
    "unicorn",
    "django-components",
    "fasthtml",
    "reactpy",
    "reflex",
    "nuxt",
    "next",
)

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
    # A record kept from an earlier report has lost its stages, which the
    # marks need, so it keeps the cell that report worked out.
    if "cell" in record:
        return record["cell"]
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


def _kept(keep_from: Path, measured: set[str], mistake_ids: set[str]) -> tuple[list[dict], list[dict], dict[str, str]]:
    """
    Take the records of every framework this run did not measure from an earlier report's results.json.

    Returns three things: those records; for each group of frameworks, the
    run that measured them (the earlier report's own run, or the run that
    report kept them from); and the name the earlier report gave each
    framework.
    """
    path = keep_from / "results.json" if keep_from.is_dir() else keep_from
    earlier = json.loads(path.read_text(encoding="utf-8"))
    records = [record for record in earlier["results"] if record["framework"] not in measured]
    stray = sorted({record["mistake"] for record in records} - mistake_ids)
    if stray:
        # A mistake the catalogue does not list would reach the page with no row to sit in.
        raise ConfigError(f"{path} has results for mistakes the catalogue does not list: {stray}")
    keys = {record["framework"] for record in records}
    for key in sorted(keys):
        # A mistake added since the earlier run has no cell in a kept column,
        # and the docs page needs one for every mistake.
        missing = sorted(mistake_ids - {record["mistake"] for record in records if record["framework"] == key})
        if missing:
            raise ConfigError(f"{path} has no result for {key} on {missing}; measure {key} again")
    origins = []
    # Frameworks the earlier report kept from a still earlier one keep that origin.
    for origin in earlier.get("kept", []):
        frameworks = [key for key in origin["frameworks"] if key in keys]
        if frameworks:
            origins.append(origin | {"frameworks": frameworks, "source": _origin_source(origin["source"], frameworks)})
    inherited = {key for origin in origins for key in origin["frameworks"]}
    own = [row["key"] for row in earlier["frameworks"] if row["key"] in keys - inherited]
    if own:
        source = _origin_source(earlier.get("source") or {}, own)
        origins.insert(0, {"run": earlier["run"], "source": source, "frameworks": own})
    return records, origins, {row["key"]: row["name"] for row in earlier["frameworks"]}


def _origin_source(source: dict, frameworks: list[str]) -> dict:
    """Keep what a reader needs to know about the run that measured these frameworks, and nothing about the others."""
    kept = {key: source[key] for key in ("commit", "inputs_tree") if source.get(key)}
    kept["inputs_changed"] = bool(source.get("inputs_changed", source.get("benchmark_files_changed")))
    # A kept framework built from this repository is still not a release.
    checkout = {key: packages for key, packages in (source.get("from_checkout") or {}).items() if key in frameworks}
    if checkout:
        kept["from_checkout"] = checkout
    return kept


def _kept_notices(origin: dict, names: dict[str, str]) -> list[str]:
    """Say which frameworks' results come from an earlier run, which run, and what it measured, in Markdown."""
    listed = ", ".join(names.get(key, key) for key in origin["frameworks"])
    source = origin["source"]
    notice = f"{listed}: kept from run {origin['run']}"
    if source.get("commit"):
        notice += f", cases and tools from commit `{source['commit']}`"
    if source.get("inputs_tree"):
        notice += f", benchmark inputs tree `{source['inputs_tree']}`"
    notice += " plus uncommitted changes to the benchmark" if source.get("inputs_changed") else ""
    lines = [notice + "."]
    for key, packages, changed in html_report.checkout_packages(source):
        lines.append(
            f"{names.get(key, key)}: {packages} built from this repository at commit `{source.get('commit', '')}`"
            f"{' plus uncommitted changes to them' if changed else ''}, not a published release."
        )
    return lines


def _check_complete(records: list[dict], measured: set[str], mistake_ids: set[str]) -> None:
    """Stop when a framework this run measured lacks a mistake, which no kept report could fill in."""
    for key in sorted(measured):
        missing = sorted(mistake_ids - {record["mistake"] for record in records if record["framework"] == key})
        if missing:
            raise ConfigError(
                f"the run measured {key} without {missing}; --keep-from keeps whole frameworks, "
                f"so run every mistake of {key}"
            )


def write(run_dir: Path, output: Path, keep_from: Path | None = None) -> None:
    """
    Write matrix.md, results.json and report.html for one run into `output`.

    With `keep_from`, an earlier report folder or its results.json, every
    framework the run did not measure keeps its results from that report,
    and each report names the run they come from.
    """
    records = [json.loads(line) for line in (run_dir / "results.jsonl").read_text().splitlines() if line]
    mistakes = load_catalogue()
    kept, origins, kept_names = [], [], {}
    if keep_from:
        measured = {record["framework"] for record in records}
        mistake_ids = {mistake.id for mistake in mistakes}
        _check_complete(records, measured, mistake_ids)
        kept, origins, kept_names = _kept(keep_from, measured, mistake_ids)
    records += kept
    frameworks = load_frameworks()
    present = {record["framework"] for record in records}
    keys = [key for key in ORDER if key in present] + sorted(present - set(ORDER))
    by = {(record["mistake"], record["framework"]): record for record in records}
    # A kept framework this checkout no longer configures keeps its earlier name.
    framework_names = kept_names | {key: framework.name for key, framework in frameworks.items()}
    names = " | ".join(framework_names[key] for key in keys)
    source_file = run_dir / "run.json"
    source = json.loads(source_file.read_text()) if source_file.is_file() else {}
    lines = [f"# Error-prevention results, run {run_dir.name}", ""]
    if source:
        # Uncommitted changes to the inputs mean no commit has what the run
        # scored; runs recorded before the inputs had their own flag use the
        # whole folder's.
        dirty = (
            " plus uncommitted changes to the benchmark"
            if source.get("inputs_changed", source["benchmark_files_changed"])
            else ""
        )
        # Runs recorded before the inputs tree was added have no tree id.
        tree = f", benchmark inputs tree `{source['inputs_tree']}`" if source.get("inputs_tree") else ""
        lines += [f"Cases and tools from commit `{source['commit']}`{tree}{dirty}.", ""]
        for key, packages, changed in html_report.checkout_packages(source):
            # Such a framework is measured from unreleased sources, which the
            # reader needs before comparing it with a release.
            name = framework_names.get(key, key)
            lines += [
                f"{name}: {packages} built from this repository at commit `{source['commit']}`"
                f"{' plus uncommitted changes to them' if changed else ''}, not a published release.",
                "",
            ]
    # The reader must see that the columns were not all measured in one run.
    for origin in origins:
        for notice in _kept_notices(origin, framework_names):
            lines += [notice, ""]

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
    # A kept record is already in this compact form.
    compact = [
        record
        if "cell" in record
        else {
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
        "frameworks": [{"key": key, "name": framework_names[key]} for key in keys],
        "categories": [{"id": key, "heading": heading} for key, heading in CATEGORIES.items()],
        "buckets": [{"id": key, "label": label} for key, label in BUCKETS.items()],
        "codes": [{"code": code, "meaning": meaning} for code, meaning in CODES],
        "mistakes": [{"id": mistake.id, "title": mistake.title, "category": mistake.category} for mistake in mistakes],
        "results": compact,
    }
    if origins:
        summary["kept"] = origins
    (output / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    # The same data as a page that opens from disk, with no docs site to start.
    html_report.write(summary, output)
