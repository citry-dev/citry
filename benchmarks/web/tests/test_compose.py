"""Composed reports take each app from one passed run and feed the docs page."""

import importlib.util
import json
from pathlib import Path

import pytest
from citry_bench.compose import compose
from citry_bench.config import ROOT
from citry_bench.prepare import write_json

DOCS_SCRIPT = ROOT / "docs_site" / "scripts" / "benchmark_data.py"


def _sample(app: str, page_load: int, server_ms: float) -> dict:
    # The fields the docs script reads from one initial page load.
    return {
        "app": app,
        "count": 1400,
        "action": "initial",
        "page_load": page_load,
        "status": "ok",
        "elapsed_ms": server_ms + 5.0,
        "ready_elapsed_ms": server_ms + 5.0,
        "layout_extra_wait_ms": 2.0,
        "layout_endpoint": "second-rAF-layout-opportunity-v1",
        "layout_inclusive_elapsed_ms": server_ms + 7.0,
        "latency_phase": {
            "status": "measured",
            "segments": [{"key": "server", "ms": server_ms}, {"key": "browser_after", "ms": 5.0}],
        },
    }


def _run(directory: Path, run_id: str, apps: list[str], *, qualification: bool, **changes) -> Path:
    folder = directory / run_id
    folder.mkdir(parents=True)
    profile = {
        "name": changes.pop("name", "release"),
        "apps": apps,
        "counts": [1400],
        "browser": "chromium",
        "scenario": "project_board",
        "network": "loopback",
        "cache": "cold-context",
        "compression": "identity",
        "cycles": changes.pop("cycles", 2),
    }
    inputs = {
        "inputs": {"profile": profile, "local_wheels": {}, "runner": {"cli.py": changes.pop("runner", "a" * 64)}},
        "installed": {"citry": {"packages": [["citry", "0.6.0"], ["citry_core", "1.8.0"]]}},
    }
    write_json(
        folder / "manifest.json",
        {
            "id": run_id,
            "status": changes.pop("status", "passed"),
            "qualification": qualification,
            "scenario_revision": "canonical-project-v1",
            "build": changes.pop("build", f"/builds/{'-'.join(apps)}"),
            "inputs": inputs,
            "host": {"system": "Darwin", "machine": "arm64", "node": "private-host"},
            "browser": {"version": changes.pop("browser_version", "151.0")},
            "git_head": "abc123",
            "git_status": "",
            "limitations": ["native loopback HTTP"],
        },
    )
    rows = [_sample(app, load, 10.0 * (index + 1)) for index, app in enumerate(apps) for load in (1, 2)]
    # A row for an app this run did not select must never reach the report.
    rows.append(_sample("stray", 1, 1.0))
    (folder / "samples.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    return folder


def _pair(directory: Path, label: str, apps: list[str], **changes) -> tuple[Path, Path]:
    qualification = _run(directory, f"{label}-qualify", apps, qualification=True, **dict(changes))
    return qualification, _run(directory, f"{label}-run", apps, qualification=False, **changes)


def _docs_script():
    spec = importlib.util.spec_from_file_location("benchmark_data", DOCS_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_compose_takes_each_app_from_its_own_run_and_feeds_the_docs_script(tmp_path):
    docs = _docs_script()
    keys = [key for _, members in docs.GROUPS for key, _ in members]
    # Next.js was measured again in its own run, as in a release with one retry.
    first = _pair(tmp_path / "runs", "cohort", [key for key in keys if key != "next"])
    second = _pair(tmp_path / "runs", "next", ["next"], name="next-only")

    output = compose(tmp_path / "report", [first, second], command=["citry-bench", "compose"])

    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "composed"
    assert manifest["inputs"]["inputs"]["profile"]["apps"] == [*keys[:-2], "nuxt", "next"]
    assert manifest["inputs"]["inputs"]["profile"]["name"] == "release + next-only (composed)"
    assert manifest["cell_provenance"]["next/1400"] == {
        "latency": "measured",
        "latency_run": "next-run",
        "qualification_run": "next-qualify",
    }
    assert "citry 0.6.0 and citry-core 1.8.0 installed from the lockfile" in manifest["citry_configuration"]
    samples = [json.loads(line) for line in (output / "samples.jsonl").read_text().splitlines()]
    assert "stray" not in {row["app"] for row in samples}
    assert (output / "report.html").is_file()

    document = (output / "report.html").read_text()
    data = docs.extract(document, manifest)
    citry = data["loads"][0]["frameworks"][0]
    assert (citry["key"], citry["total_ms"], citry["measured_in_run"], citry["retained"]) == (
        "citry",
        17.0,
        "cohort-run",
        False,
    )
    assert data["source"]["citry_build"] == {"source_commit": "abc123", "source_had_uncommitted_changes": False}
    assert data["source"]["browser"] == "chromium 151.0"


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"status": "failed"}, "is not a passed qualification run"),
        ({"cycles": 1}, r"uses different settings .*\['cycles'\]"),
        ({"browser_version": "152.0"}, "different browser version"),
        ({"runner": "b" * 64}, "different runner sources"),
    ],
)
def test_compose_refuses_runs_that_do_not_compare(tmp_path, changes, message):
    first = _pair(tmp_path / "runs", "cohort", ["citry"])
    second = _pair(tmp_path / "runs", "other", ["nuxt"], **changes)
    with pytest.raises(ValueError, match=message):
        compose(tmp_path / "report", [first, second])
    assert not (tmp_path / "report").exists()


def test_compose_refuses_an_app_from_two_runs_and_a_used_folder(tmp_path):
    first = _pair(tmp_path / "runs", "cohort", ["citry", "nuxt"])
    second = _pair(tmp_path / "runs", "again", ["nuxt"])
    with pytest.raises(ValueError, match="nuxt is in both"):
        compose(tmp_path / "report", [first, second])
    (tmp_path / "used").mkdir()
    (tmp_path / "used" / "manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="is not empty"):
        compose(tmp_path / "used", [first])


def test_compose_refuses_a_qualification_of_another_build(tmp_path):
    qualification, _ = _pair(tmp_path / "runs", "cohort", ["citry"])
    _, run = _pair(tmp_path / "runs", "other", ["citry"], build="/builds/elsewhere")
    with pytest.raises(ValueError, match="not made from the same prepared build"):
        compose(tmp_path / "report", [(qualification, run)])
