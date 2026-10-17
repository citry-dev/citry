# ruff: noqa: T201 - a maintenance script that prints the file it wrote
"""
Refresh the numbers behind the Benchmarks page
(``docs_site/data/benchmark_time_to_interactive.json``).

The framework benchmark runner writes a report folder: ``report.html``, which
carries every observation as one embedded JSON script element, and
``manifest.json``, which records how and where the run happened. This script
reads both and keeps only what the ``<c-benchmark-chart />`` component draws:
for each framework, the time until the page is ready for input at 1,400
outputs, split into phases, for the first and the second page load. The docs
build then never needs the benchmark repository.

Run it from the repository root with the report folder:

    uv run --no-sync python -m docs_site.scripts.benchmark_data REPORT_DIR
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

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
    (None, (("citry_vue", "Citry"),)),
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
        if "citry_vue" not in group.get("apps", ()):
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


def extract(document: str, manifest: dict[str, Any]) -> dict[str, Any]:
    """Build the docs data file's content from a report and its manifest."""
    data = embedded_report_data(document)
    rows = [row for row in data["samples"] if row["count"] == OUTPUTS and row["action"] == "initial"]
    provenance = manifest.get("cell_provenance", {})
    loads = []
    for load_id, page_load in LOADS:
        frameworks = []
        for group, members in GROUPS:
            for key, name in members:
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
                frameworks.append(
                    {
                        "key": key,
                        "name": name,
                        "group": group,
                        "total_ms": round(ok[0]["layout_inclusive_elapsed_ms"], 1),
                        "phases_ms": {phase: round(ms, 1) for phase, ms in _phases(ok[0]).items() if ms > 0},
                        # A "retained" cell was copied from an earlier run.
                        "measured_in_run": cell.get("latency_run"),
                        "retained": cell.get("latency") == "retained",
                    },
                )
        loads.append({"id": load_id, "page_load": page_load, "frameworks": frameworks})
    profile = manifest["inputs"]["inputs"]["profile"]
    return {
        "generated_by": "docs_site/scripts/benchmark_data.py",
        "source": {
            "report_id": manifest["id"],
            "report_status": manifest.get("status"),
            "composed_at": manifest.get("composed_at"),
            "recomposed_at": manifest.get("recomposed", {}).get("at"),
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
        },
        "loads": loads,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("report", type=Path, help="report folder holding report.html and manifest.json")
    args = parser.parse_args()
    document = (args.report / "report.html").read_text(encoding="utf-8")
    manifest = json.loads((args.report / "manifest.json").read_text(encoding="utf-8"))
    DATA_PATH.write_text(json.dumps(extract(document, manifest), indent=2) + "\n", encoding="utf-8")
    print(DATA_PATH)


if __name__ == "__main__":
    main()
