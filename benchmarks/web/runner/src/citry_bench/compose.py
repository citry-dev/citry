"""Combine passed benchmark runs into one report folder for the docs page.

A profile run measures every app it lists. When one app has to be measured
again, or a group of apps runs under its own profile, `citry-bench compose`
puts the runs back together: it copies each app's records from the run that
measured it, writes a manifest that says which run measured which app, and
redraws `report.html` from the combined records. The docs script
`docs_site/scripts/benchmark_data.py` reads that folder.

Every run must have passed, and every run must follow the same settings
except for its name, its apps and its `[local_wheels]` table, with the same
runner and scenario sources, so the combined report compares like with like.
Each app comes from exactly one run.
"""

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from citry_bench.prepare import write_json
from citry_bench.results import report

RECORDS = ("samples.jsonl", "sizes.jsonl", "server-timings.jsonl")
# A run's name and app list say what it measured, and its local wheels are
# recorded per run, so only these profile fields may differ between runs.
PER_RUN_FIELDS = {"name", "apps", "local_wheels"}


def _manifest(directory: Path) -> tuple[dict, str]:
    path = directory / "manifest.json"
    if not path.is_file():
        raise ValueError(f"{directory} has no manifest.json; pass a run folder")
    data = path.read_bytes()
    return json.loads(data), hashlib.sha256(data).hexdigest()


def _rows(directory: Path, name: str) -> list[dict]:
    path = directory / name
    return [json.loads(line) for line in path.read_text().splitlines()] if path.is_file() else []


def _load(qualification_dir: Path, run_dir: Path) -> dict:
    qualification, qualification_sha = _manifest(qualification_dir)
    run, run_sha = _manifest(run_dir)
    # A failed or incomplete run has missing or failed observations, which
    # would draw a shorter bar instead of a gap.
    if qualification.get("qualification") is not True or qualification.get("status") != "passed":
        raise ValueError(f"{qualification_dir} is not a passed qualification run")
    if run.get("qualification") is not False or run.get("kind") is not None or run.get("status") != "passed":
        raise ValueError(f"{run_dir} is not a passed measurement run")
    # The qualification only vouches for the build it checked.
    if qualification.get("build") != run.get("build") or qualification.get("inputs") != run.get("inputs"):
        raise ValueError(f"{qualification_dir} and {run_dir} were not made from the same prepared build")
    profile = run["inputs"]["inputs"]["profile"]
    return {
        "qualification": qualification,
        "qualification_sha256": qualification_sha,
        "qualification_dir": qualification_dir,
        "run": run,
        "run_sha256": run_sha,
        "run_dir": run_dir,
        "profile": profile,
        "apps": list(profile["apps"]),
    }


def _citry_configuration(group: dict) -> str:
    # Say which Citry release the bars measure, from what the run installed.
    # Installed metadata may spell a name `citry_core`, so compare normalized
    # names (PEP 503).
    packages = {
        re.sub(r"[-_.]+", "-", name).lower(): version
        for name, version in group["run"]["inputs"]["installed"]["citry"]["packages"]
    }
    wheels = group["run"]["inputs"]["inputs"].get("local_wheels", {})
    source = (
        "wheels built locally (" + ", ".join(Path(wheel["path"]).name for wheel in wheels.values()) + ")"
        if wheels
        else "the lockfile"
    )
    return (
        "The Citry app benchmarks/web/apps/citry with default settings, running "
        f"citry {packages.get('citry')} and citry-core {packages.get('citry-core')} installed from {source}."
    )


def compose(output: Path, pairs: list[tuple[Path, Path]], *, command: list[str] | None = None) -> Path:
    """Write one report folder from (qualification run, measurement run) pairs."""
    if not pairs:
        raise ValueError("Pass at least one qualification and measurement run pair")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"{output} is not empty; choose a new folder")
    groups = [_load(qualification, run) for qualification, run in pairs]

    first = groups[0]
    for group in groups[1:]:
        different = sorted(
            key
            for key in set(first["profile"]) | set(group["profile"])
            if key not in PER_RUN_FIELDS and first["profile"].get(key) != group["profile"].get(key)
        )
        if different:
            raise ValueError(f"{group['run_dir']} uses different settings from {first['run_dir']}: {different}")
        # The same browser build and host keep the timings comparable.
        if group["run"]["browser"]["version"] != first["run"]["browser"]["version"]:
            raise ValueError(f"{group['run_dir']} used a different browser version")
        if group["run"]["host"] != first["run"]["host"]:
            raise ValueError(f"{group['run_dir']} ran on a different host")
        # Different runner or scenario code checks and times differently.
        for key in ("runner", "scenario"):
            if group["run"]["inputs"]["inputs"].get(key) != first["run"]["inputs"]["inputs"].get(key):
                raise ValueError(f"{group['run_dir']} used different {key} sources from {first['run_dir']}")
        if group["run"]["scenario_revision"] != first["run"]["scenario_revision"]:
            raise ValueError(f"{group['run_dir']} measured a different scenario revision")

    owners: dict[str, dict] = {}
    for group in groups:
        for app in group["apps"]:
            if app in owners:
                raise ValueError(f"{app} is in both {owners[app]['run_dir']} and {group['run_dir']}")
            owners[app] = group
    apps = list(owners)

    output.mkdir(parents=True, exist_ok=True)
    # Each app's records come only from the run that measured it, in run order.
    for name in RECORDS:
        lines = [
            json.dumps(row, sort_keys=True)
            for group in groups
            for row in _rows(group["run_dir"], name)
            if row.get("app") in group["apps"]
        ]
        (output / name).write_text("".join(line + "\n" for line in lines))

    run_ids = [group["run"]["id"] for group in groups]
    profile = {
        **{key: value for key, value in first["profile"].items() if key not in PER_RUN_FIELDS},
        "name": " + ".join(dict.fromkeys(group["profile"]["name"] for group in groups)) + " (composed)",
        "apps": apps,
    }
    manifest = {
        "schema": 1,
        "id": "composed-" + hashlib.sha256("\n".join(run_ids).encode()).hexdigest()[:12],
        "status": "composed",
        "composed_at": datetime.now(UTC).isoformat(),
        "command": command or [],
        "scenario_revision": first["run"]["scenario_revision"],
        "citry_configuration": _citry_configuration(owners["citry"]) if "citry" in owners else None,
        "host": first["run"]["host"],
        "browser": {"engine": first["profile"]["browser"], "version": first["run"]["browser"]["version"]},
        "inputs": {"inputs": {"profile": profile}},
        "source_runs": {
            "run_groups": {
                group["run"]["id"]: {
                    "apps": group["apps"],
                    "qualification": {
                        "id": group["qualification"]["id"],
                        "path": str(group["qualification_dir"]),
                        "status": group["qualification"]["status"],
                        "manifest_sha256": group["qualification_sha256"],
                    },
                    "latency": {
                        "id": group["run"]["id"],
                        "path": str(group["run_dir"]),
                        "status": group["run"]["status"],
                        "manifest_sha256": group["run_sha256"],
                        "profile": group["profile"],
                        "local_wheels": group["run"]["inputs"]["inputs"].get("local_wheels", {}),
                        "git_head": group["run"].get("git_head"),
                        "git_status": group["run"].get("git_status"),
                    },
                }
                for group in groups
            },
        },
        "cell_provenance": {
            f"{app}/{count}": {
                "latency": "measured",
                "latency_run": group["run"]["id"],
                "qualification_run": group["qualification"]["id"],
            }
            for app, group in owners.items()
            for count in profile["counts"]
        },
        "limitations": list(dict.fromkeys(item for group in groups for item in group["run"].get("limitations", []))),
    }
    write_json(output / "manifest.json", manifest)
    report(output)
    return output
