# ruff: noqa: T201 - a maintenance script that prints the file it wrote
"""
Refresh the results behind the "Catching errors" section of the Benchmarks page
(``docs_site/data/error_prevention.json``).

The error-prevention benchmark (``benchmarks/errors``) writes the same
developer mistakes in each framework, runs each framework's editor checks,
command-line checks, production build and development server on them, and
records how early each mistake was reported. Its report step writes
``results.json`` into the report folder. This script reads that file and keeps
only what the ``<c-error-benchmark-chart />`` and ``<c-error-benchmark-table />``
components draw, plus the run id, so the docs build never needs the benchmark
folder.

Run it from the repository root with the report folder or its results.json:

    uv run --no-sync python -m docs_site.scripts.error_benchmark_data REPORT
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DOCS_SITE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = DOCS_SITE_DIR / "data" / "error_prevention.json"

# The statuses the benchmark runner gives a record: the case statuses (`PORT_STATUSES`) from its
# config.py, plus "missing" for a mistake with no case (its cli.py). Only a
# "ported" record was run through the framework's tools, so only it can have
# a bucket.
STATUSES = frozenset({"ported", "not-applicable", "prevented", "missing"})


def _check_unique(kind: str, ids: list[str]) -> None:
    # A repeated id would draw one framework, category or mistake twice.
    repeated = sorted({value for value in ids if ids.count(value) > 1})
    if repeated:
        msg = f"results.json lists these {kind} more than once: {repeated}"
        raise ValueError(msg)


def extract(report: dict[str, Any], *, allow_partial: bool = False) -> dict[str, Any]:
    """
    Build the docs data file's content from a report's ``results.json``.

    Every framework must have exactly one record for every mistake, so every
    bar on the page has the same length. A record that the report itself could
    not have written (an unknown framework, mistake, status or bucket) stops
    the script rather than reaching the page.
    """
    frameworks = [{"key": row["key"], "name": row["name"]} for row in report["frameworks"]]
    categories = [{"id": row["id"], "heading": row["heading"]} for row in report["categories"]]
    buckets = [{"id": row["id"], "label": row["label"]} for row in report["buckets"]]
    mistakes = [{"id": row["id"], "title": row["title"], "category": row["category"]} for row in report["mistakes"]]
    _check_unique("frameworks", [row["key"] for row in frameworks])
    _check_unique("categories", [row["id"] for row in categories])
    _check_unique("buckets", [row["id"] for row in buckets])
    _check_unique("mistakes", [row["id"] for row in mistakes])

    category_ids = {row["id"] for row in categories}
    stray = sorted({row["category"] for row in mistakes} - category_ids)
    if stray:
        # The table groups mistakes under category headings; one outside every
        # heading would be left off the page.
        msg = f"results.json has mistakes in categories it does not list: {stray}"
        raise ValueError(msg)

    framework_keys = [row["key"] for row in frameworks]
    mistake_ids = [row["id"] for row in mistakes]
    bucket_ids = {row["id"] for row in buckets}
    by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for record in report["results"]:
        pair = (record["framework"], record["mistake"])
        label = f"{pair[0]} / {pair[1]}"
        if pair[0] not in framework_keys or pair[1] not in mistake_ids:
            msg = f"{label}: the record names a framework or mistake that results.json does not list"
            raise ValueError(msg)
        if pair in by_pair:
            msg = f"{label}: results.json has more than one record"
            raise ValueError(msg)
        if record["status"] not in STATUSES:
            msg = f"{label}: unknown status {record['status']!r}"
            raise ValueError(msg)
        bucket = record.get("bucket")
        if bucket is None and record["status"] == "ported" and not allow_partial:
            # A scored case always ends in a bucket; one without came from a
            # run that skipped the runtime check, which the page must not show
            # as a published result.
            msg = f"{label}: the case was not scored; rerun with the runtime check, or pass --allow-partial"
            raise ValueError(msg)
        if bucket is not None and (record["status"] != "ported" or bucket not in bucket_ids):
            msg = f"{label}: bucket {bucket!r} is unknown or set on a {record['status']} record"
            raise ValueError(msg)
        by_pair[pair] = record

    absent = [
        f"{key} / {mistake}" for key in framework_keys for mistake in mistake_ids if (key, mistake) not in by_pair
    ]
    if absent:
        msg = f"results.json has no record for: {absent}"
        raise ValueError(msg)

    return {
        "generated_by": "docs_site/scripts/error_benchmark_data.py",
        "run": report["run"],
        "frameworks": frameworks,
        "categories": categories,
        "buckets": buckets,
        "mistakes": mistakes,
        "codes": [{"code": row["code"], "meaning": row["meaning"]} for row in report["codes"]],
        # Framework order first, then mistake order, so a rerun on the same
        # report writes the same file whatever order the runner logged in.
        "results": [
            {
                "framework": key,
                "mistake": mistake,
                "status": by_pair[key, mistake]["status"],
                "bucket": by_pair[key, mistake].get("bucket"),
                "cell": by_pair[key, mistake]["cell"],
                # The reason explains a not-applicable or prevented cell.
                "reason": by_pair[key, mistake].get("reason"),
                "evidence": list(by_pair[key, mistake].get("evidence") or []),
            }
            for key in framework_keys
            for mistake in mistake_ids
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("report", type=Path, help="the report folder, or the results.json inside it")
    parser.add_argument(
        "--allow-partial", action="store_true", help="accept a run whose runtime check was skipped, for a preview"
    )
    args = parser.parse_args()
    source = args.report / "results.json" if args.report.is_dir() else args.report
    report = json.loads(source.read_text(encoding="utf-8"))
    data = extract(report, allow_partial=args.allow_partial)
    DATA_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(DATA_PATH)


if __name__ == "__main__":
    main()
