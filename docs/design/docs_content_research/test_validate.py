"""Failure-path tests for the documentation-content research validator."""

# ruff: noqa: S101 - pytest assertions are the test contract

from __future__ import annotations

import csv
import hashlib
import importlib.util
from pathlib import Path
from unittest.mock import patch

_VALIDATOR_PATH = Path(__file__).with_name("validate.py")
_SPEC = importlib.util.spec_from_file_location("docs_content_research_validate", _VALIDATOR_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
validate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(validate)


def _valid_row() -> dict[str, str]:
    return {
        "baseline": "DC1-20260726T101722Z-9d1a8636",
        "artifact_id": "generated:test",
        "artifact_type": "generated_surface",
        "source_locator": "source.md",
        "public_locator": "/test/",
        "nav_location": "n/a",
        "title": "Test output",
        "source_kind": "generated",
        "consumer_locators": "direct-reader",
        "generated_outputs": "html",
        "test_locators": "none",
        "evidence_state": "unverified",
        "inventory_state": "complete",
        "notes": "none",
    }


def _write_inventory(destination: Path, rows: list[dict[str, str]]) -> None:
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=validate.INVENTORY_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _write_fingerprints(destination: Path, rows: list[dict[str, str]]) -> None:
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=validate.FINGERPRINT_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _fingerprint_row(source_path: str, body: bytes, *, git_state: str = "clean") -> dict[str, str]:
    return {
        "baseline": validate.BASELINE_ID,
        "scope": "content",
        "source_path": source_path,
        "git_state": git_state,
        "byte_size": str(len(body)),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def _reader_evidence_row(source_path: str, body: bytes) -> dict[str, str]:
    return {
        "baseline": validate.STAGE2_BASELINE_ID,
        "evidence_id": "EV-001",
        "evidence_kind": "repository_behavior",
        "source_locator": source_path,
        "source_fingerprint": hashlib.sha256(body).hexdigest(),
        "observed_at": "2026-07-26",
        "observation": "A reader can render a component.",
        "evidence_level": "verified_implementation",
        "confidence": "high",
        "privacy_state": "repository_local",
        "limitations": "Focused repository evidence only.",
        "supports_jobs": "JOB-001",
    }


def _reader_job_row() -> dict[str, str]:
    return {
        "baseline": validate.STAGE2_BASELINE_ID,
        "job_id": "JOB-001",
        "segment": "learner",
        "situation": "learning",
        "journey_phase": "first_success",
        "reader_context": "Knows Python and HTML.",
        "prerequisite": "A supported Python environment.",
        "job_statement": "Install Citry and render one component.",
        "successful_outcome": "The expected HTML is visible.",
        "failure_concern": "Installation or rendering fails without a recovery path.",
        "evidence_ids": "EV-001",
        "evidence_strength": "moderate",
        "frequency": "5",
        "impact": "5",
        "risk": "2",
        "product_priority": "5",
        "priority_score": "17",
        "priority_band": "primary",
        "confidence": "medium",
        "persona_status": "provisional",
        "notes": "Direct-user evidence is unavailable.",
    }


def _write_reader_records(
    evidence_file: Path,
    jobs_file: Path,
    evidence_rows: list[dict[str, str]],
    job_rows: list[dict[str, str]],
) -> None:
    with evidence_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=validate.READER_EVIDENCE_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(evidence_rows)
    with jobs_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=validate.READER_JOB_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(job_rows)


def _fact_row() -> dict[str, str]:
    return {
        "baseline": validate.STAGE3_BASELINE_ID,
        "fact_id": "FACT-001",
        "assertion": "A component renders its declared input.",
        "reader_jobs": "JOB-001",
        "surfaces": "docs;examples;reference",
        "applicability": "current",
        "source_locators": "source.py::Present",
        "test_locators": "test_source.py::test_present",
        "evidence_level": "verified_implementation",
        "confidence": "high",
        "prerequisites": "A concrete component class.",
        "supported_context": "Current local Python package.",
        "security_implications": "Plain text remains escaped.",
        "successful_outcome": "The expected value is visible.",
        "failure_behavior": "A missing required input raises TypeError during render.",
        "canonical_owner": "/getting-started/your-first-component/",
        "supporting_links": "/reference/component/",
        "example_requirement": "required",
        "status": "authored",
        "notes": "none",
    }


def _write_facts(destination: Path, rows: list[dict[str, str]]) -> None:
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=validate.FACT_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def test_validator_rejects_duplicate_ids_and_unknown_enum(tmp_path: Path) -> None:
    (tmp_path / "source.md").write_text("source", encoding="utf-8")
    first = _valid_row()
    second = _valid_row()
    second["source_kind"] = "mystery"
    inventory = tmp_path / "inventory.tsv"
    _write_inventory(inventory, [first, second])

    errors = validate.validate_inventory(tmp_path, inventory, check_live=False)

    assert any("duplicate artifact_id" in error for error in errors)
    assert any("unknown source_kind" in error for error in errors)


def test_validator_rejects_missing_source_and_incomplete_row(tmp_path: Path) -> None:
    row = _valid_row()
    row["source_locator"] = "missing.md"
    row["inventory_state"] = "incomplete"
    inventory = tmp_path / "inventory.tsv"
    _write_inventory(inventory, [row])

    errors = validate.validate_inventory(tmp_path, inventory, check_live=False)

    assert any("missing source locator" in error for error in errors)
    assert any("is 'incomplete'" in error for error in errors)


def test_reader_visible_headings_ignore_fenced_markdown(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Real title\n\n```md\n## Not a section\n```\n\n## Real section\n",
        encoding="utf-8",
    )

    assert validate._readme_ids(tmp_path) == {"readme:real-title", "readme:real-section"}


def test_live_inventory_includes_nested_snippet_modules(tmp_path: Path) -> None:
    (tmp_path / "docs_site" / "content").mkdir(parents=True)
    (tmp_path / "docs_site" / "content" / "index.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "docs_site" / "examples").mkdir()
    snippets = tmp_path / "docs_site" / "snippets"
    (snippets / "getting_started").mkdir(parents=True)
    (snippets / "root_snippet.py").write_text("ROOT = True\n", encoding="utf-8")
    (snippets / "getting_started" / "app.py").write_text("APP = True\n", encoding="utf-8")
    internal = tmp_path / "docs_site" / "_internal"
    internal.mkdir()
    (tmp_path / "docs_site" / "reference.yml").write_text("categories: []\n", encoding="utf-8")
    (internal / "release_notes.py").write_text("EXCLUDED_RELEASES = ()\n", encoding="utf-8")
    (tmp_path / "docs_site" / "static" / "img").mkdir(parents=True)
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changes\n", encoding="utf-8")

    expected = validate._expected_live_ids(tmp_path)

    assert expected["snippet_module"] == {
        "snippet:root-snippet",
        "snippet:getting-started/app",
    }


def test_github_slug_preserves_literal_hyphens_between_spaces() -> None:
    assert validate._github_slug("Citry - Refreshingly simple UI") == "citry---refreshingly-simple-ui"


def test_fingerprint_validator_rejects_stale_source(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("original", encoding="utf-8")
    fingerprints = tmp_path / "fingerprints.tsv"
    with fingerprints.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=validate.FINGERPRINT_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerow(
            {
                "baseline": "DC1-20260726T101722Z-9d1a8636",
                "scope": "content",
                "source_path": "source.md",
                "git_state": "untracked",
                "byte_size": str(source.stat().st_size),
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        )
    source.write_text("changed", encoding="utf-8")

    errors = validate.validate_fingerprints(tmp_path, fingerprints, check_live=False)

    assert any("stale size" in error for error in errors)
    assert any("stale sha256" in error for error in errors)


def test_inventory_validator_rejects_missing_markdown_heading(tmp_path: Path) -> None:
    (tmp_path / "source.md").write_text("# Present\n", encoding="utf-8")
    row = _valid_row()
    row["source_locator"] = "source.md#absent"
    inventory = tmp_path / "inventory.tsv"
    _write_inventory(inventory, [row])

    errors = validate.validate_inventory(tmp_path, inventory, check_live=False)

    assert any("missing source heading" in error for error in errors)


def test_validator_rejects_different_valid_baseline(tmp_path: Path) -> None:
    (tmp_path / "source.md").write_text("source", encoding="utf-8")
    row = _valid_row()
    row["baseline"] = "DC2-20260726T101722Z-9d1a8636"
    inventory = tmp_path / "inventory.tsv"
    _write_inventory(inventory, [row])

    errors = validate.validate_inventory(tmp_path, inventory, check_live=False)

    assert any("unexpected baseline" in error for error in errors)


def test_validator_enforces_example_consumers_and_tests(tmp_path: Path) -> None:
    (tmp_path / "source.md").write_text("source", encoding="utf-8")
    row = _valid_row()
    row["artifact_id"] = "example:test"
    row["artifact_type"] = "example_family"
    row["consumer_locators"] = "none"
    row["test_locators"] = "none"
    inventory = tmp_path / "inventory.tsv"
    _write_inventory(inventory, [row])

    errors = validate.validate_inventory(tmp_path, inventory, check_live=False)

    assert any("has no known consumer" in error for error in errors)
    assert any("has no known test" in error for error in errors)
    assert any("is unverified" in error for error in errors)


def test_fingerprint_validator_rejects_missing_live_row(tmp_path: Path) -> None:
    content = tmp_path / "docs_site" / "content"
    content.mkdir(parents=True)
    (content / "page.md").write_text("page", encoding="utf-8")
    fingerprints = tmp_path / "fingerprints.tsv"
    _write_fingerprints(fingerprints, [])

    errors = validate.validate_fingerprints(tmp_path, fingerprints)

    assert any("live source missing row: docs_site/content/page.md" in error for error in errors)


def test_fingerprint_validator_rejects_stale_git_state(tmp_path: Path) -> None:
    content = tmp_path / "docs_site" / "content"
    content.mkdir(parents=True)
    source = content / "page.md"
    source.write_text("page", encoding="utf-8")
    fingerprints = tmp_path / "fingerprints.tsv"
    _write_fingerprints(fingerprints, [_fingerprint_row("docs_site/content/page.md", source.read_bytes())])

    with patch.object(validate, "_git_state", return_value=" M"):
        errors = validate.validate_fingerprints(tmp_path, fingerprints)

    assert any("stale git_state" in error for error in errors)


def test_capture_refuses_to_replace_changed_fingerprints(tmp_path: Path) -> None:
    destination = tmp_path / "fingerprints.tsv"
    old = _fingerprint_row("source.md", b"old")
    new = _fingerprint_row("source.md", b"newer")
    _write_fingerprints(destination, [old])
    original = destination.read_text(encoding="utf-8")

    with patch.object(validate, "_fingerprint_rows", return_value=[new]):
        count, deltas, wrote = validate.capture_fingerprints(tmp_path, destination)

    assert count == 1
    assert deltas == ["changed source.md: byte_size,sha256"]
    assert not wrote
    assert destination.read_text(encoding="utf-8") == original


def test_reader_records_reject_stale_source_and_broken_cross_reference(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("original", encoding="utf-8")
    evidence = _reader_evidence_row("source.md", source.read_bytes())
    evidence["supports_jobs"] = "JOB-002"
    source.write_text("changed", encoding="utf-8")
    evidence_file = tmp_path / "reader_evidence.tsv"
    jobs_file = tmp_path / "reader_jobs.tsv"
    _write_reader_records(evidence_file, jobs_file, [evidence], [_reader_job_row()])

    errors = validate.validate_reader_records(tmp_path, evidence_file, jobs_file)

    assert any("stale source_fingerprint" in error for error in errors)
    assert any("unknown supports_jobs ID 'JOB-002'" in error for error in errors)
    assert any("does not support 'JOB-001'" in error for error in errors)


def test_reader_records_reject_priority_mismatch_and_weak_primary(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("source", encoding="utf-8")
    job = _reader_job_row()
    job["priority_score"] = "20"
    job["evidence_strength"] = "limited"
    evidence_file = tmp_path / "reader_evidence.tsv"
    jobs_file = tmp_path / "reader_jobs.tsv"
    _write_reader_records(
        evidence_file,
        jobs_file,
        [_reader_evidence_row("source.md", source.read_bytes())],
        [job],
    )

    errors = validate.validate_reader_records(tmp_path, evidence_file, jobs_file)

    assert any("priority_score 20 != 17" in error for error in errors)
    assert any("primary job has limited evidence" in error for error in errors)


def test_reader_records_reject_unavailable_source_that_supports_a_job(tmp_path: Path) -> None:
    evidence = _reader_evidence_row("unavailable:private-support", b"")
    evidence.update(
        {
            "evidence_kind": "unavailable_source",
            "source_fingerprint": "n/a",
            "evidence_level": "inference",
            "privacy_state": "unavailable",
        }
    )
    evidence_file = tmp_path / "reader_evidence.tsv"
    jobs_file = tmp_path / "reader_jobs.tsv"
    _write_reader_records(evidence_file, jobs_file, [evidence], [_reader_job_row()])

    errors = validate.validate_reader_records(tmp_path, evidence_file, jobs_file)

    assert any("unavailable source cannot support jobs" in error for error in errors)


def test_reader_records_reject_missing_markdown_evidence_heading(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("# Present\n", encoding="utf-8")
    evidence = _reader_evidence_row("source.md#absent", source.read_bytes())
    evidence_file = tmp_path / "reader_evidence.tsv"
    jobs_file = tmp_path / "reader_jobs.tsv"
    _write_reader_records(evidence_file, jobs_file, [evidence], [_reader_job_row()])

    errors = validate.validate_reader_records(tmp_path, evidence_file, jobs_file)

    assert any("missing source heading 'absent'" in error for error in errors)


def test_reader_records_reject_missing_python_qualified_name(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    source.write_text("class Present:\n    pass\n", encoding="utf-8")
    evidence = _reader_evidence_row("source.py::Absent", source.read_bytes())
    evidence_file = tmp_path / "reader_evidence.tsv"
    jobs_file = tmp_path / "reader_jobs.tsv"
    _write_reader_records(evidence_file, jobs_file, [evidence], [_reader_job_row()])

    errors = validate.validate_reader_records(tmp_path, evidence_file, jobs_file)

    assert any("missing Python name 'Absent'" in error for error in errors)


def test_reader_records_reject_unverified_representative_application(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("source", encoding="utf-8")
    evidence = _reader_evidence_row("source.md", source.read_bytes())
    evidence["evidence_kind"] = "representative_application"
    evidence_file = tmp_path / "reader_evidence.tsv"
    jobs_file = tmp_path / "reader_jobs.tsv"
    _write_reader_records(evidence_file, jobs_file, [evidence], [_reader_job_row()])

    errors = validate.validate_reader_records(tmp_path, evidence_file, jobs_file)

    assert any("representative application must be live_project_verified" in error for error in errors)


def test_live_project_row_still_validates_ordinary_repository_fields(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    source.write_text("def present():\n    pass\n", encoding="utf-8")
    evidence = _reader_evidence_row("source.py::absent", source.read_bytes())
    evidence.update(
        {
            "evidence_kind": "representative_application",
            "evidence_level": "live_project_verified",
            "source_fingerprint": "definitely-not-a-hash",
            "privacy_state": "public",
        }
    )
    evidence_file = tmp_path / "reader_evidence.tsv"
    jobs_file = tmp_path / "reader_jobs.tsv"
    _write_reader_records(evidence_file, jobs_file, [evidence], [_reader_job_row()])

    errors = validate.validate_reader_records(tmp_path, evidence_file, jobs_file)

    assert any("repository locator needs repository_local privacy_state" in error for error in errors)
    assert any("missing Python name 'absent'" in error for error in errors)
    assert any("invalid repository source_fingerprint" in error for error in errors)


def test_fact_ledger_rejects_duplicate_id_and_unknown_enums(tmp_path: Path) -> None:
    (tmp_path / "source.py").write_text("class Present:\n    pass\n", encoding="utf-8")
    (tmp_path / "test_source.py").write_text("def test_present():\n    pass\n", encoding="utf-8")
    evidence_file = tmp_path / "reader_evidence.tsv"
    jobs_file = tmp_path / "reader_jobs.tsv"
    _write_reader_records(
        evidence_file,
        jobs_file,
        [_reader_evidence_row("source.py", (tmp_path / "source.py").read_bytes())],
        [_reader_job_row()],
    )
    bad = _fact_row()
    bad["status"] = "published"
    bad["surfaces"] = "docs;unknown"
    fact_file = tmp_path / "facts.tsv"
    _write_facts(fact_file, [_fact_row(), bad])

    errors = validate.validate_fact_ledger(tmp_path, fact_file, jobs_file)

    assert any("duplicate fact_id" in error for error in errors)
    assert any("unknown status" in error for error in errors)
    assert any("unknown surface" in error for error in errors)


def test_fact_ledger_rejects_broken_locators_and_reader_job(tmp_path: Path) -> None:
    (tmp_path / "source.py").write_text("class Present:\n    pass\n", encoding="utf-8")
    (tmp_path / "test_source.py").write_text("def test_present():\n    pass\n", encoding="utf-8")
    evidence_file = tmp_path / "reader_evidence.tsv"
    jobs_file = tmp_path / "reader_jobs.tsv"
    _write_reader_records(
        evidence_file,
        jobs_file,
        [_reader_evidence_row("source.py", (tmp_path / "source.py").read_bytes())],
        [_reader_job_row()],
    )
    fact = _fact_row()
    fact["reader_jobs"] = "JOB-999"
    fact["source_locators"] = "missing.py::Absent"
    fact["test_locators"] = "test_source.py::test_absent"
    fact_file = tmp_path / "facts.tsv"
    _write_facts(fact_file, [fact])

    errors = validate.validate_fact_ledger(tmp_path, fact_file, jobs_file)

    assert any("unknown reader job 'JOB-999'" in error for error in errors)
    assert any("missing source locator 'missing.py'" in error for error in errors)
    assert any("missing test Python name 'test_absent'" in error for error in errors)


def test_fact_ledger_rejects_unsupported_published_fact(tmp_path: Path) -> None:
    (tmp_path / "source.py").write_text("class Present:\n    pass\n", encoding="utf-8")
    evidence_file = tmp_path / "reader_evidence.tsv"
    jobs_file = tmp_path / "reader_jobs.tsv"
    _write_reader_records(
        evidence_file,
        jobs_file,
        [_reader_evidence_row("source.py", (tmp_path / "source.py").read_bytes())],
        [_reader_job_row()],
    )
    fact = _fact_row()
    fact["applicability"] = "planned"
    fact["evidence_level"] = "document_claimed"
    fact["test_locators"] = "none"
    fact_file = tmp_path / "facts.tsv"
    _write_facts(fact_file, [fact])

    errors = validate.validate_fact_ledger(tmp_path, fact_file, jobs_file)

    assert any("published fact cannot be 'planned'" in error for error in errors)
    assert any("published fact has weak evidence" in error for error in errors)
    assert any("published fact has no test locator" in error for error in errors)


def test_fact_ledger_keeps_disputed_facts_out_of_reader_surfaces(tmp_path: Path) -> None:
    (tmp_path / "source.py").write_text("class Present:\n    pass\n", encoding="utf-8")
    evidence_file = tmp_path / "reader_evidence.tsv"
    jobs_file = tmp_path / "reader_jobs.tsv"
    _write_reader_records(
        evidence_file,
        jobs_file,
        [_reader_evidence_row("source.py", (tmp_path / "source.py").read_bytes())],
        [_reader_job_row()],
    )
    fact = _fact_row()
    fact["status"] = "disputed"
    fact["test_locators"] = "none"
    fact_file = tmp_path / "facts.tsv"
    _write_facts(fact_file, [fact])

    errors = validate.validate_fact_ledger(tmp_path, fact_file, jobs_file)

    assert any("disputed fact cannot be reader-facing" in error for error in errors)
