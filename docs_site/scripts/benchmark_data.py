# ruff: noqa: T201 - a maintenance script that prints the file it wrote
r"""
Refresh the numbers behind the Benchmarks page
(``docs_site/data/benchmark_time_to_interactive.json``).

The framework benchmark runner's ``citry-bench compose`` command
(``benchmarks/web``) writes a report folder: ``report.html``, which carries
every observation as one embedded JSON script element, and ``manifest.json``,
which records which runs measured each framework and how. This script
reads both and keeps only what the ``<c-benchmark-chart />`` component draws:
for each framework, the time until the page is ready for input at 1,400
outputs, split into phases, for the first and the second page load. The docs
build then never needs the benchmark repository.

Run it from the repository root with the report folder:

    uv run --no-sync python -m docs_site.scripts.benchmark_data REPORT_DIR

By default every framework's numbers come from the report, so it must have
measured all of them. To measure only some frameworks again, name them with
``--only``; every other framework keeps its entry from the current data file:

    uv run --no-sync python -m docs_site.scripts.benchmark_data REPORT_DIR \
        --only citry

A kept entry keeps its numbers and its ``measured_in_run``, and is marked
``"retained": true``: its numbers come from an earlier report, not from the
one this run of the script read. ``source`` then describes the new report,
and its ``kept_from`` list names the earlier report each kept entry came
from. The Citry fields in ``source`` (``citry_report_id``,
``citry_configuration`` and ``citry_build``) describe the report Citry's own
entry comes from, because the README's note under the speed chart names the
Citry version by that report.

A report may also measure a framework you do not name, as a control: a
framework measured again only to check that the machine still gives the same
times as it did for the kept numbers. The script does not publish a
control's new numbers. It prints them beside the kept ones, and you decide
whether the two runs agree.

The script refuses to write the file when:

- ``--only`` names a framework the page does not draw, or one the report did
  not measure;
- a framework the page draws is neither named with ``--only`` nor in the
  current data file, or its entry there came from the same report, so it
  should be named with ``--only`` instead of kept;
- a control's observations fail the same checks as a published framework's,
  so the comparison cannot be made;
- the report or the current data file lacks a field in
  ``COMPARED_SOURCE_FIELDS``, or the two disagree on one: the scenario and its
  revision, the number of outputs, the observations per framework and load,
  the host's operating system and its version, the processor type, the
  browser and its version, the network, the cache and the compression.

The data file records nothing else about how its numbers were taken, so the
script cannot check the rest: which machine ran it (the file leaves out the
host name, so another computer with the same operating system and processor
type passes), the runner and scenario source files, the Python version, the
number of cycles, the timeouts and the seed. ``citry-bench compose`` checks
those only among the runs it combines into one report, not against the
report the kept entries came from. So measure again on the same machine,
with a copy of the earlier run's profile that changes only its name, its apps
and its ``[local_wheels]`` table.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Collection

DOCS_SITE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = DOCS_SITE_DIR / "data" / "benchmark_time_to_interactive.json"

# The page shows the larger of the report's two page sizes, where framework
# differences are easiest to see.
OUTPUTS = 1400

# The report's own framework groups and names (the runner's report.js), minus
# its "Server API + CSR" group: those apps build the page in the browser, while
# the docs page compares pages rendered on the server. A group of None draws
# no heading, which is how Citry's own row sits on top unlabeled.
GROUPS: tuple[tuple[str | None, tuple[tuple[str, str], ...]], ...] = (
    (None, (("citry", "Citry"),)),
    (
        "Django libraries",
        (
            ("django_htmx_alpine", "Django + HTMX + Alpine"),
            ("django_rusty_templates", "Rusty + HTMX + Alpine"),
            ("jinja_htmx_alpine", "Jinja + HTMX + Alpine"),
            ("tetra", "Tetra"),
            ("unicorn", "django-unicorn"),
            ("django_components", "django-components"),
        ),
    ),
    (
        "Other Python libraries",
        (("fasthtml", "FastHTML"), ("reactpy", "ReactPy"), ("reflex", "Reflex")),
    ),
    ("JavaScript SSR", (("next", "Next.js"), ("nuxt", "Nuxt"))),
)

# Phase keys in the order the report stacks them. The last one is the wait
# from "ready" until the browser's next layout, which the report adds on top.
PHASES = (
    "browser_before",
    "server",
    "exchange_residual",
    "response_receive",
    "browser_after",
    "unclassified",
    "layout_wait",
)
LOADS = (("first", 1), ("second", 2))
# The layout measurement the report's own charts require (report.js).
LAYOUT_ENDPOINT = "second-rAF-layout-opportunity-v1"
# Source fields that must match before a kept entry and a new one share a
# chart: a different page, machine, browser or connection changes the times.
COMPARED_SOURCE_FIELDS = (
    "scenario",
    "outputs",
    "observations_per_framework_and_load",
    "host",
    "browser",
    "network",
    "cache",
    "compression",
)
# The report checks phases against the end time with this tolerance.
_TOLERANCE_MS = 1e-6
_DATA_START = '<script id="report-data" type="application/json">'


def embedded_report_data(document: str) -> dict[str, Any]:
    """Return the observations ``report.html`` carries in its data script."""
    if _DATA_START not in document:
        msg = "report.html has no embedded report data"
        raise ValueError(msg)
    payload = document.split(_DATA_START, 1)[1].split("</script>", 1)[0]
    return json.loads(payload)


def _phases(row: dict[str, Any]) -> dict[str, float]:
    # Mirrors the report's phaseVector(): the phase segments must add up to the
    # "ready" time, and the layout wait must close the gap to the drawn total.
    # A row that fails either check would draw a bar of the wrong length, so
    # stop rather than publish it.
    label = f"{row['app']} load {row['page_load']}"
    phase = row.get("latency_phase") or {}
    if phase.get("status") != "measured":
        msg = f"{label}: phases were not measured"
        raise ValueError(msg)
    totals = dict.fromkeys(PHASES, 0.0)
    for segment in phase["segments"]:
        totals[segment["key"]] += segment["ms"]
    if abs(sum(totals.values()) - row["ready_elapsed_ms"]) > _TOLERANCE_MS:
        msg = f"{label}: phases do not add up to the ready time"
        raise ValueError(msg)
    # The report only adds the layout wait for rows that measured it with this
    # endpoint; a row copied from an older run could have measured another one.
    if row.get("layout_endpoint") != LAYOUT_ENDPOINT:
        msg = f"{label}: the layout wait was not measured with {LAYOUT_ENDPOINT}"
        raise ValueError(msg)
    totals["layout_wait"] = row["layout_extra_wait_ms"]
    if abs(row["ready_elapsed_ms"] + totals["layout_wait"] - row["layout_inclusive_elapsed_ms"]) > _TOLERANCE_MS:
        msg = f"{label}: layout wait does not close the gap to the total"
        raise ValueError(msg)
    return totals


def _citry_build(manifest: dict[str, Any]) -> dict[str, Any]:
    # The run group that measured Citry names the wheels it installed; the
    # run's own manifest, when it is still on disk, names the source commit.
    for group in manifest.get("source_runs", {}).get("run_groups", {}).values():
        if "citry" not in group.get("apps", ()):
            continue
        latency = group["latency"]
        build: dict[str, Any] = {
            name: Path(wheel["path"]).name for name, wheel in latency.get("local_wheels", {}).items()
        }
        run_manifest = Path(latency["path"]) / "manifest.json"
        if run_manifest.exists():
            run = json.loads(run_manifest.read_text(encoding="utf-8"))
            build["source_commit"] = run.get("git_head")
            build["source_had_uncommitted_changes"] = bool(run.get("git_status"))
        return build
    return {}


def _initial_rows(document: str) -> list[dict[str, Any]]:
    # Only the first and second page loads at the size the page shows matter;
    # the report also holds the other sizes and the actions after the load.
    data = embedded_report_data(document)
    return [row for row in data["samples"] if row["count"] == OUTPUTS and row["action"] == "initial"]


def measured_frameworks(document: str) -> list[str]:
    """Return the keys of the frameworks the page draws that the report measured, in the page's order."""
    apps = {row["app"] for row in _initial_rows(document)}
    return [key for _, members in GROUPS for key, _ in members if key in apps]


def extract(document: str, manifest: dict[str, Any], frameworks: Collection[str] | None = None) -> dict[str, Any]:
    """
    Build the docs data file's content from a report and its manifest.

    Every framework the page draws must be in the report, unless
    ``frameworks`` names the ones to take; then only those are taken, and
    each of them must be in the report.
    """
    rows = _initial_rows(document)
    provenance = manifest.get("cell_provenance", {})
    loads = []
    for load_id, page_load in LOADS:
        frameworks_out = []
        for group, members in GROUPS:
            for key, name in members:
                if frameworks is not None and key not in frameworks:
                    continue
                matches = [row for row in rows if row["app"] == key and row["page_load"] == page_load]
                ok = [row for row in matches if row["status"] == "ok"]
                # The page plots one bar per framework; with several
                # observations it would need the report's median selection,
                # which this script does not reproduce.
                if len(ok) != 1 or len(matches) != 1:
                    msg = (
                        f"{key} load {page_load}: expected one observation, which succeeded; "
                        f"found {len(matches)} with {len(ok)} successful"
                    )
                    raise ValueError(msg)
                cell = provenance.get(f"{key}/{OUTPUTS}", {})
                frameworks_out.append(
                    {
                        "key": key,
                        "name": name,
                        "group": group,
                        "total_ms": round(ok[0]["layout_inclusive_elapsed_ms"], 1),
                        "phases_ms": {phase: round(ms, 1) for phase, ms in _phases(ok[0]).items() if ms > 0},
                        # compose writes only "measured"; a cell marked
                        # "retained" would come from an earlier run, and
                        # keep_from_current() marks kept entries the same way.
                        "measured_in_run": cell.get("latency_run"),
                        "retained": cell.get("latency") == "retained",
                    },
                )
        loads.append({"id": load_id, "page_load": page_load, "frameworks": frameworks_out})
    profile = manifest["inputs"]["inputs"]["profile"]
    return {
        "generated_by": "docs_site/scripts/benchmark_data.py",
        "source": {
            "report_id": manifest["id"],
            "report_status": manifest.get("status"),
            "composed_at": manifest.get("composed_at"),
            "recomposed_at": manifest.get("recomposed", {}).get("at"),
            # The report Citry's numbers come from;
            # benchmark_readme.SPEED_VERSION_NOTES looks up the Citry version
            # by it.
            "citry_report_id": manifest["id"],
            # How the Citry app was configured, in the benchmark's own words.
            "citry_configuration": manifest.get("citry_configuration"),
            "scenario": f"{profile['scenario']} ({manifest.get('scenario_revision')})",
            "outputs": OUTPUTS,
            "observations_per_framework_and_load": 1,
            "citry_build": _citry_build(manifest),
            # The host name is left out; it identifies a machine, not a setup.
            "host": {key: value for key, value in manifest.get("host", {}).items() if key != "node"},
            "browser": f"{manifest['browser']['engine']} {manifest['browser']['version']}",
            "network": profile["network"],
            "cache": profile["cache"],
            "compression": profile["compression"],
            # Earlier reports whose entries this file kept; see keep_from_current().
            "kept_from": [],
        },
        "loads": loads,
    }


def build(
    document: str,
    manifest: dict[str, Any],
    *,
    only: Collection[str] | None = None,
    current: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """
    Return the data file's content and the lines that compare each control framework.

    Without ``only``, every framework comes from the report and there are no
    controls. With ``only``, those frameworks come from the report and every
    other one is kept from ``current``, the data file as it is now; a
    framework the report measured but ``only`` does not name is a control.
    Raises ``ValueError`` in each case the module docstring lists.
    """
    if only is None:
        return extract(document, manifest), []
    if not only:
        msg = "--only needs at least one framework to take from the report"
        raise ValueError(msg)
    if current is None:
        msg = "--only keeps the other frameworks from the current data file, so it needs that file"
        raise ValueError(msg)
    known = [key for _, members in GROUPS for key, _ in members]
    unknown = [key for key in only if key not in known]
    if unknown:
        msg = f"--only names frameworks the page does not draw: {unknown}; use some of {known}"
        raise ValueError(msg)
    measured = measured_frameworks(document)
    absent = [key for key in only if key not in measured]
    if absent:
        msg = (
            f"the report did not measure {absent} at {OUTPUTS:,} outputs, so it has no numbers to publish "
            "for them; leave them out of --only or measure them"
        )
        raise ValueError(msg)
    fresh = extract(document, manifest, frameworks=only)
    controls = [key for key in measured if key not in only]
    try:
        # A control goes through the same checks, so a broken row cannot pass
        # for a run that agrees with the kept numbers.
        control_data = extract(document, manifest, frameworks=controls)
    except ValueError as exc:
        msg = f"cannot compare the control frameworks {controls}: {exc}"
        raise ValueError(msg) from exc
    return keep_from_current(fresh, current, only), compare_controls(control_data, current)


def keep_from_current(fresh: dict[str, Any], current: dict[str, Any], only: Collection[str]) -> dict[str, Any]:
    """
    Return ``fresh`` with the frameworks named in ``only`` and every other framework from ``current``.

    ``fresh`` is what ``extract()`` built from the new report. A kept entry
    keeps its numbers and its ``measured_in_run`` and is marked retained;
    its name and group follow ``GROUPS``, as for a new entry. Raises
    ``ValueError`` when a field in ``COMPARED_SOURCE_FIELDS`` is missing or
    differs, or when a framework is in neither source.
    """
    # A field missing on both sides would compare equal, so a missing field
    # counts as a difference too.
    different = [
        f"{field}: the report has {_recorded(fresh['source'], field)}, "
        f"the current data file {_recorded(current['source'], field)}"
        for field in COMPARED_SOURCE_FIELDS
        if field not in fresh["source"]
        or field not in current["source"]
        or fresh["source"][field] != current["source"][field]
    ]
    if different:
        msg = (
            "the report was not measured like the numbers it would join, so they cannot share a chart: "
            + "; ".join(different)
            + ". Measure again on the same machine with a copy of the earlier profile"
        )
        raise ValueError(msg)

    # Where each entry of the current file came from: the report it names in
    # kept_from, or else the current file's own report.
    earlier = {key: origin for origin in current["source"].get("kept_from", []) for key in origin["frameworks"]}
    report_id = fresh["source"]["report_id"]
    fresh_rows = {load["id"]: {row["key"]: row for row in load["frameworks"]} for load in fresh["loads"]}
    current_rows = {load["id"]: {row["key"]: row for row in load["frameworks"]} for load in current["loads"]}
    loads = []
    kept: list[str] = []
    for load_id, page_load in LOADS:
        frameworks = []
        for group, members in GROUPS:
            for key, name in members:
                if key in only:
                    frameworks.append(fresh_rows[load_id][key])
                    continue
                entry = current_rows.get(load_id, {}).get(key)
                if entry is None:
                    msg = (
                        f"{key} load {page_load}: not named with --only and not in the current data file, "
                        f"so neither source has its numbers; pass --only {key} if the report measured it"
                    )
                    raise ValueError(msg)
                # An entry this report already measured is not an earlier
                # result; keeping it would list the report in its own kept_from.
                if earlier.get(key, current["source"])["report_id"] == report_id:
                    msg = (
                        f"{key}: the current data file already took its numbers from this report; "
                        f"pass --only {key} to take them again, or run without --only to take every "
                        "framework from this report"
                    )
                    raise ValueError(msg)
                frameworks.append({**entry, "name": name, "group": group, "retained": True})
                if key not in kept:
                    kept.append(key)
        loads.append({"id": load_id, "page_load": page_load, "frameworks": frameworks})

    source = dict(fresh["source"])
    # Citry's fields belong to the report its own entry comes from, so the
    # README names the version that report measured.
    if "citry" not in only:
        source["citry_report_id"] = current["source"].get("citry_report_id", current["source"]["report_id"])
        for field in ("citry_configuration", "citry_build"):
            source[field] = current["source"].get(field)
    origins: dict[str, dict[str, Any]] = {}
    for key in kept:
        origin = earlier.get(key, current["source"])
        record = origins.setdefault(
            origin["report_id"],
            {"report_id": origin["report_id"], "composed_at": origin.get("composed_at"), "frameworks": []},
        )
        record["frameworks"].append(key)
    source["kept_from"] = list(origins.values())
    return {**fresh, "source": source, "loads": loads}


def _recorded(source: dict[str, Any], field: str) -> str:
    # A missing field reads as a value if printed as None, so say it is missing.
    return repr(source[field]) if field in source else "does not record it"


def compare_controls(controls: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """
    Return one line per control framework and load: its new numbers beside the kept ones.

    ``controls`` is what ``extract()`` built from the report for the control
    frameworks. Each line shows the total and the two phases that make up
    most of it, because two changes can cancel out in the total.
    """
    current_rows = {load["id"]: {row["key"]: row for row in load["frameworks"]} for load in current["loads"]}
    lines = []
    for load in controls["loads"]:
        for row in load["frameworks"]:
            kept = current_rows.get(load["id"], {}).get(row["key"])
            if kept is None:
                continue
            change = (row["total_ms"] - kept["total_ms"]) / kept["total_ms"]
            phases = ", ".join(
                f"{label} {row['phases_ms'].get(phase, 0.0):,.1f} against {kept['phases_ms'].get(phase, 0.0):,.1f}"
                for phase, label in (("server", "server"), ("browser_after", "browser"))
            )
            lines.append(
                f"{row['name']}, {load['id']} load: {row['total_ms']:,.1f} ms in the report, "
                f"{kept['total_ms']:,.1f} ms kept ({change:+.1%}); {phases} ms"
            )
    return lines


def main(argv: list[str] | None = None) -> int:
    """Write the data file from the report folder; return 1 when the report cannot be published."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("report", type=Path, help="report folder holding report.html and manifest.json")
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="FRAMEWORK",
        help="take only these frameworks (keys such as citry) from the report; keep the rest from the data file",
    )
    args = parser.parse_args(argv)
    try:
        document = (args.report / "report.html").read_text(encoding="utf-8")
        manifest = _read_json(args.report / "manifest.json")
        # Read the file before it is rewritten: its entries are the ones kept.
        current = _read_json(DATA_PATH) if args.only else None
        if current is not None and not (isinstance(current, dict) and {"source", "loads"} <= current.keys()):
            msg = f"{DATA_PATH} is not a benchmark data file: it needs 'source' and 'loads'"
            raise ValueError(msg)
        data, controls = build(document, manifest, only=args.only, current=current)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    DATA_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(DATA_PATH)
    if controls:
        print("Measured as controls and not published; check that they agree with the kept numbers:")
        for line in controls:
            print(f"  {line}")
    return 0


def _read_json(path: Path) -> Any:
    # A decoding error names only a line and column, so add the file.
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"cannot read {path}: {exc}"
        raise ValueError(msg) from exc


if __name__ == "__main__":
    sys.exit(main())
