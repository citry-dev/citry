"""Validate documentation-content research records and fingerprints."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import re
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
RESEARCH_DIR = Path(__file__).resolve().parent
INVENTORY_FILE = RESEARCH_DIR / "content_inventory.tsv"
FINGERPRINT_FILE = RESEARCH_DIR / "baseline_fingerprints.tsv"
READER_EVIDENCE_FILE = RESEARCH_DIR / "reader_evidence.tsv"
READER_JOBS_FILE = RESEARCH_DIR / "reader_jobs.tsv"
FACT_LEDGER_FILE = RESEARCH_DIR / "fact_ledger.tsv"
BASELINE_ID = "DC1-20260726T101722Z-9d1a8636"
STAGE2_BASELINE_ID = "DC2-20260726T122608Z-6ad74ee1"
STAGE3_BASELINE_ID = "DC3-20260726T131933Z-6ad74ee1"

INVENTORY_COLUMNS = (
    "baseline",
    "artifact_id",
    "artifact_type",
    "source_locator",
    "public_locator",
    "nav_location",
    "title",
    "source_kind",
    "consumer_locators",
    "generated_outputs",
    "test_locators",
    "evidence_state",
    "inventory_state",
    "notes",
)
FINGERPRINT_COLUMNS = ("baseline", "scope", "source_path", "git_state", "byte_size", "sha256")
READER_EVIDENCE_COLUMNS = (
    "baseline",
    "evidence_id",
    "evidence_kind",
    "source_locator",
    "source_fingerprint",
    "observed_at",
    "observation",
    "evidence_level",
    "confidence",
    "privacy_state",
    "limitations",
    "supports_jobs",
)
READER_JOB_COLUMNS = (
    "baseline",
    "job_id",
    "segment",
    "situation",
    "journey_phase",
    "reader_context",
    "prerequisite",
    "job_statement",
    "successful_outcome",
    "failure_concern",
    "evidence_ids",
    "evidence_strength",
    "frequency",
    "impact",
    "risk",
    "product_priority",
    "priority_score",
    "priority_band",
    "confidence",
    "persona_status",
    "notes",
)
FACT_COLUMNS = (
    "baseline",
    "fact_id",
    "assertion",
    "reader_jobs",
    "surfaces",
    "applicability",
    "source_locators",
    "test_locators",
    "evidence_level",
    "confidence",
    "prerequisites",
    "supported_context",
    "security_implications",
    "successful_outcome",
    "failure_behavior",
    "canonical_owner",
    "supporting_links",
    "example_requirement",
    "status",
    "notes",
)

ARTIFACT_TYPES = {
    "content_page",
    "example_family",
    "snippet_module",
    "included_source",
    "reference_group",
    "readme_section",
    "release_surface",
    "generated_surface",
    "content_data",
    "static_asset",
}
SOURCE_KINDS = {"authored", "included", "generated", "projected"}
EVIDENCE_STATES = {
    "unverified",
    "guard-mapped",
    "test-mapped",
    "browser-test-mapped",
    "mixed-test-mapped",
    "observed-output",
}
INVENTORY_STATES = {"complete", "incomplete", "disputed"}
FINGERPRINT_SCOPES = {
    "content",
    "example",
    "snippet",
    "reference",
    "readme_release",
    "generated_surface",
    "asset_data",
    "test_guard",
    "workflow",
    "research_control",
    "toolchain",
    "external_input",
}
READER_EVIDENCE_KINDS = {
    "repository_behavior",
    "automated_test",
    "artifact_observation",
    "representative_application",
    "public_support",
    "maintainer_decision",
    "provisional_design",
    "current_docs",
    "unavailable_source",
}
READER_EVIDENCE_LEVELS = {
    "verified_implementation",
    "artifact_verified",
    "live_project_verified",
    "publicly_observed",
    "document_claimed",
    "inference",
}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
PRIVACY_STATES = {"repository_local", "public", "aggregate_only", "unavailable"}
READER_SEGMENTS = {
    "professional_team",
    "independent_developer",
    "learner",
    "component_tooling_author",
    "contributor_maintainer",
}
READER_SITUATIONS = {
    "evaluating",
    "learning",
    "building",
    "integrating",
    "debugging",
    "testing",
    "operating",
    "migrating",
    "looking_up_contract",
    "contributing",
}
JOURNEY_PHASES = {
    "evaluate",
    "first_success",
    "build",
    "integrate",
    "debug",
    "test",
    "deploy_operate",
    "migrate",
    "extend_reuse",
    "lookup",
    "contribute",
}
EVIDENCE_STRENGTHS = {"strong", "moderate", "limited", "unavailable"}
PRIORITY_BANDS = {"primary", "important", "supporting", "provisional"}
PERSONA_STATUSES = {"supported", "provisional", "secondary"}
FACT_SURFACES = {"docs", "examples", "reference", "research"}
FACT_APPLICABILITY = {"current", "experimental", "version_specific", "planned", "internal"}
EXAMPLE_REQUIREMENTS = {"required", "supporting", "none"}
FACT_STATUSES = {"disputed", "verified", "authored", "reviewed", "intentionally_omitted"}

BASELINE_RE = re.compile(r"^DC\d+-\d{8}T\d{6}Z-[0-9a-f]{8}$")
EVIDENCE_ID_RE = re.compile(r"^EV-\d{3}$")
JOB_ID_RE = re.compile(r"^JOB-\d{3}$")
FACT_ID_RE = re.compile(r"^FACT-\d{3}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HEADING_RE = re.compile(r"^(#{1,2})\s+(.+?)\s*$")
RELEASE_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
EXTERNAL_PYTHON_INVENTORY = "external:python-3.13-objects.inv"

REQUIRED_GENERATED_IDS = {
    "generated:404",
    "generated:markdown-companions",
    "generated:pagefind",
    "generated:sitemap",
    "generated:robots",
    "generated:indexing-manifest",
    "generated:llms-index",
    "generated:llms-full",
    "generated:objects-inventory",
    "generated:social-cards",
    "generated:versions",
    "generated:redirects",
    "generated:static-tree",
    "generated:client-runtime",
    "generated:blog-feed",
}


def _read_tsv(source_file: Path, expected_columns: tuple[str, ...]) -> tuple[list[dict[str, str]], list[str]]:
    """Read a TSV with an exact header, returning rows and validation errors."""
    errors: list[str] = []
    if not source_file.is_file():
        return [], [f"missing TSV: {source_file}"]

    with source_file.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        try:
            header = tuple(next(reader))
        except StopIteration:
            return [], [f"empty TSV: {source_file}"]
        if header != expected_columns:
            errors.append(f"{source_file}: header is {header!r}, expected {expected_columns!r}")

        rows: list[dict[str, str]] = []
        for line_number, values in enumerate(reader, start=2):
            if len(values) != len(expected_columns):
                errors.append(f"{source_file}:{line_number}: {len(values)} fields, expected {len(expected_columns)}")
                continue
            row = dict(zip(expected_columns, values, strict=True))
            row["_line"] = str(line_number)
            rows.append(row)
    return rows, errors


def _base_locator(locator: str) -> str:
    """Return the repository path portion of a source or test locator."""
    return locator.split("#", 1)[0].split("::", 1)[0]


def _locator_parts(value: str) -> list[str]:
    """Split a semicolon locator list while preserving explicit sentinel values."""
    return value.split(";")


def _check_local_locators(
    repo_root: Path,
    value: str,
    *,
    field: str,
    line_number: str,
    sentinels: set[str],
) -> list[str]:
    """Check repository-relative locators in one list field."""
    errors: list[str] = []
    for locator in _locator_parts(value):
        if locator != locator.strip():
            errors.append(f"inventory:{line_number}: {field} locator has surrounding whitespace: {locator!r}")
            continue
        if locator in sentinels or locator.startswith(("http://", "https://", "/")):
            continue
        source_name = _base_locator(locator)
        source_path = repo_root / source_name
        if not source_path.exists():
            errors.append(f"inventory:{line_number}: missing {field} locator: {source_name}")
            continue
        if field == "source" and "#" in locator and source_path.suffix.lower() == ".md":
            fragment = locator.split("#", 1)[1]
            if fragment not in _markdown_heading_slugs(source_path):
                errors.append(f"inventory:{line_number}: missing source heading {fragment!r} in {source_name}")
    return errors


def _github_slug(title: str) -> str:
    """Return the GitHub-style slug used by the current ASCII README headings."""
    cleaned = re.sub(r"[^\w\- ]", "", title.lower())
    return cleaned.replace(" ", "-").strip("-")


def _markdown_heading_slugs(source_file: Path) -> set[str]:
    """Return GitHub-style slugs for Markdown headings outside fenced code."""
    slugs: set[str] = set()
    seen: Counter[str] = Counter()
    in_fence = False
    fence_char = ""
    for line in source_file.read_text(encoding="utf-8").splitlines():
        fence = FENCE_RE.match(line)
        if fence:
            char = fence.group(1)[0]
            if not in_fence:
                in_fence, fence_char = True, char
            elif char == fence_char:
                in_fence = False
            continue
        if in_fence:
            continue
        heading = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not heading:
            continue
        base = _github_slug(heading.group(1))
        seen[base] += 1
        slug = base if seen[base] == 1 else f"{base}-{seen[base] - 1}"
        slugs.add(slug)
    return slugs


def _python_qualified_names(source_file: Path) -> set[str]:
    """Return top-level and class-qualified Python definitions."""
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    names: set[str] = set()

    def collect(body: list[ast.stmt], prefix: str = "") -> None:
        for node in body:
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            qualified = f"{prefix}.{node.name}" if prefix else node.name
            names.add(qualified)
            if isinstance(node, ast.ClassDef):
                collect(node.body, qualified)

    collect(tree.body)
    return names


def _readme_ids(repo_root: Path) -> set[str]:
    """Reader-visible level-one and level-two README heading IDs outside fences."""
    expected: set[str] = set()
    in_fence = False
    fence_char = ""
    for line in (repo_root / "README.md").read_text(encoding="utf-8").splitlines():
        fence = FENCE_RE.match(line)
        if fence:
            char = fence.group(1)[0]
            if not in_fence:
                in_fence, fence_char = True, char
            elif char == fence_char:
                in_fence = False
            continue
        if in_fence:
            continue
        heading = HEADING_RE.match(line)
        if heading:
            expected.add(f"readme:{_github_slug(heading.group(2))}")
    return expected


def _release_exclusions(repo_root: Path) -> set[str]:
    """Read the release generator's explicit excluded-heading tuple."""
    source_file = repo_root / "docs_site/_internal/release_notes.py"
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        if node.target.id == "EXCLUDED_RELEASES" and node.value is not None:
            return set(ast.literal_eval(node.value))
    return set()


def _release_ids(repo_root: Path) -> set[str]:
    """Release artifact IDs generated from current non-fenced changelog H2s."""
    excluded = _release_exclusions(repo_root)
    ids = {"release:index"}
    seen_slugs: Counter[str] = Counter()
    in_fence = False
    fence_char = ""
    for line in (repo_root / "CHANGELOG.md").read_text(encoding="utf-8").splitlines():
        fence = FENCE_RE.match(line)
        if fence:
            char = fence.group(1)[0]
            if not in_fence:
                in_fence, fence_char = True, char
            elif char == fence_char:
                in_fence = False
            continue
        if in_fence:
            continue
        heading = RELEASE_HEADING_RE.match(line)
        if not heading or heading.group(1) in excluded:
            continue
        slug = re.sub(r"[^a-z0-9.]+", "-", heading.group(1).lower()).strip("-") or "release"
        seen_slugs[slug] += 1
        if seen_slugs[slug] > 1:
            slug = f"{slug}-{seen_slugs[slug]}"
        ids.add(f"release:{slug}")
    return ids


def _expected_live_ids(repo_root: Path) -> dict[str, set[str]]:
    """Return artifact IDs mechanically implied by the current source tree."""
    content_dir = repo_root / "docs_site/content"
    pages = set()
    for source_file in content_dir.rglob("*.md"):
        relative = source_file.relative_to(content_dir)
        if relative.as_posix() == "index.md":
            name = "home"
        elif len(relative.parts) == 2 and relative.parts[0] == "blog" and relative.name != "index.md":
            slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", relative.stem)
            name = f"blog/{slug}"
        else:
            name = relative.with_suffix("").as_posix()
        pages.add(f"page:{name}")

    examples = {
        f"example:{item.name.replace('_', '-')}"
        for item in (repo_root / "docs_site/examples").iterdir()
        if item.is_dir() and item.name != "__pycache__"
    }
    snippets_root = repo_root / "docs_site/snippets"
    snippets = {
        "snippet:" + source_file.relative_to(snippets_root).with_suffix("").as_posix().lstrip("_").replace("_", "-")
        for source_file in snippets_root.rglob("*.py")
        if source_file.name != "__init__.py"
    }
    reference = {"reference:overview"}
    reference_source = yaml.safe_load((repo_root / "docs_site/reference.yml").read_text(encoding="utf-8"))
    reference.update(f"reference:{item['slug']}" for item in reference_source["categories"])
    assets = {
        f"asset:{source_file.name.replace('.', '-')}"
        for source_file in (repo_root / "docs_site/static/img").iterdir()
        if source_file.is_file()
    }
    return {
        "content_page": pages,
        "example_family": examples,
        "snippet_module": snippets,
        "included_source": {"include:code-of-conduct", "include:license"},
        "reference_group": reference,
        "readme_section": _readme_ids(repo_root),
        "release_surface": _release_ids(repo_root),
        "generated_surface": REQUIRED_GENERATED_IDS,
        "content_data": {"data:people"},
        "static_asset": assets,
    }


def _nav_paths(repo_root: Path) -> list[str]:
    """Extract the simple clean paths from the current navigation YAML."""
    source = (repo_root / "docs_site/content/_nav.yml").read_text(encoding="utf-8")
    paths = re.findall(r"\bpath:\s*([^\s},]+)", source)
    if re.search(r"(?m)^\s*source:\s*blog\s*$", source):
        paths.append("/blog/")
        blog_dir = repo_root / "docs_site/content/blog"
        for post in sorted(blog_dir.glob("*.md")):
            if post.name == "index.md":
                continue
            slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", post.stem)
            paths.append(f"/blog/{slug}/")
    return paths


def _priority_band(score: int) -> str:
    """Return the documented Stage 2 band for an ordinal priority sum."""
    if score >= 16:
        return "primary"
    if score >= 12:
        return "important"
    if score >= 8:
        return "supporting"
    return "provisional"


def validate_reader_records(
    repo_root: Path = REPO_ROOT,
    evidence_file: Path = READER_EVIDENCE_FILE,
    jobs_file: Path = READER_JOBS_FILE,
) -> list[str]:
    """Validate Stage 2 evidence, jobs, ranks, and their cross-references."""
    evidence_rows, errors = _read_tsv(evidence_file, READER_EVIDENCE_COLUMNS)
    job_rows, job_errors = _read_tsv(jobs_file, READER_JOB_COLUMNS)
    errors.extend(job_errors)

    evidence_by_id: dict[str, dict[str, str]] = {}
    jobs_by_id: dict[str, dict[str, str]] = {}

    for row in evidence_rows:
        line_number = row["_line"]
        for column in READER_EVIDENCE_COLUMNS:
            if not row[column]:
                errors.append(f"reader_evidence:{line_number}: empty required field {column}")

        evidence_id = row["evidence_id"]
        if not EVIDENCE_ID_RE.fullmatch(evidence_id):
            errors.append(f"reader_evidence:{line_number}: malformed evidence_id {evidence_id!r}")
        if evidence_id in evidence_by_id:
            errors.append(f"reader_evidence:{line_number}: duplicate evidence_id {evidence_id!r}")
        evidence_by_id[evidence_id] = row

        if not BASELINE_RE.fullmatch(row["baseline"]):
            errors.append(f"reader_evidence:{line_number}: malformed baseline {row['baseline']!r}")
        elif row["baseline"] != STAGE2_BASELINE_ID:
            errors.append(f"reader_evidence:{line_number}: unexpected baseline {row['baseline']!r}")
        if row["evidence_kind"] not in READER_EVIDENCE_KINDS:
            errors.append(f"reader_evidence:{line_number}: unknown evidence_kind {row['evidence_kind']!r}")
        if row["evidence_level"] not in READER_EVIDENCE_LEVELS:
            errors.append(f"reader_evidence:{line_number}: unknown evidence_level {row['evidence_level']!r}")
        if row["confidence"] not in CONFIDENCE_LEVELS:
            errors.append(f"reader_evidence:{line_number}: unknown confidence {row['confidence']!r}")
        if row["privacy_state"] not in PRIVACY_STATES:
            errors.append(f"reader_evidence:{line_number}: unknown privacy_state {row['privacy_state']!r}")
        try:
            date.fromisoformat(row["observed_at"])
        except ValueError:
            errors.append(f"reader_evidence:{line_number}: invalid observed_at {row['observed_at']!r}")

        locator = row["source_locator"]
        is_public = locator.startswith(("https://", "http://"))
        is_unavailable = locator.startswith("unavailable:")
        if row["evidence_kind"] == "representative_application" and row["evidence_level"] != "live_project_verified":
            errors.append(f"reader_evidence:{line_number}: representative application must be live_project_verified")
        if row["evidence_kind"] == "unavailable_source":
            if not is_unavailable:
                errors.append(f"reader_evidence:{line_number}: unavailable source needs unavailable: locator")
            if row["privacy_state"] != "unavailable":
                errors.append(f"reader_evidence:{line_number}: unavailable source needs unavailable privacy_state")
            if row["source_fingerprint"] != "n/a":
                errors.append(f"reader_evidence:{line_number}: unavailable source fingerprint must be n/a")
            if row["supports_jobs"] != "none":
                errors.append(f"reader_evidence:{line_number}: unavailable source cannot support jobs")
            if row["evidence_level"] != "inference":
                errors.append(f"reader_evidence:{line_number}: unavailable source must use inference evidence_level")
        elif is_public:
            if row["privacy_state"] not in {"public", "aggregate_only"}:
                errors.append(
                    f"reader_evidence:{line_number}: public URL needs public or aggregate_only privacy_state"
                )
            if row["source_fingerprint"] != "n/a":
                errors.append(f"reader_evidence:{line_number}: public source fingerprint must be n/a")
        elif is_unavailable:
            errors.append(f"reader_evidence:{line_number}: unavailable locator needs unavailable_source kind")
        else:
            if row["privacy_state"] != "repository_local":
                errors.append(
                    f"reader_evidence:{line_number}: repository locator needs repository_local privacy_state"
                )
            source_name = _base_locator(locator)
            source_path = repo_root / source_name
            if not source_path.is_file():
                errors.append(f"reader_evidence:{line_number}: missing source locator {source_name}")
            else:
                if "#" in locator and source_path.suffix.lower() == ".md":
                    fragment = locator.split("#", 1)[1].split("::", 1)[0]
                    if fragment not in _markdown_heading_slugs(source_path):
                        errors.append(
                            f"reader_evidence:{line_number}: missing source heading {fragment!r} in {source_name}"
                        )
                if "::" in locator and source_path.suffix.lower() == ".py":
                    qualified_name = locator.split("::", 1)[1].split("#", 1)[0]
                    if qualified_name not in _python_qualified_names(source_path):
                        errors.append(
                            f"reader_evidence:{line_number}: missing Python name {qualified_name!r} in {source_name}"
                        )
                if not SHA256_RE.fullmatch(row["source_fingerprint"]):
                    errors.append(f"reader_evidence:{line_number}: invalid repository source_fingerprint")
                elif hashlib.sha256(source_path.read_bytes()).hexdigest() != row["source_fingerprint"]:
                    errors.append(f"reader_evidence:{line_number}: stale source_fingerprint for {source_name}")

        if row["supports_jobs"] != "none":
            for job_id in row["supports_jobs"].split(";"):
                if job_id != job_id.strip() or not JOB_ID_RE.fullmatch(job_id):
                    errors.append(f"reader_evidence:{line_number}: malformed supports_jobs entry {job_id!r}")

    for row in job_rows:
        line_number = row["_line"]
        for column in READER_JOB_COLUMNS:
            if not row[column]:
                errors.append(f"reader_jobs:{line_number}: empty required field {column}")

        job_id = row["job_id"]
        if not JOB_ID_RE.fullmatch(job_id):
            errors.append(f"reader_jobs:{line_number}: malformed job_id {job_id!r}")
        if job_id in jobs_by_id:
            errors.append(f"reader_jobs:{line_number}: duplicate job_id {job_id!r}")
        jobs_by_id[job_id] = row

        if not BASELINE_RE.fullmatch(row["baseline"]):
            errors.append(f"reader_jobs:{line_number}: malformed baseline {row['baseline']!r}")
        elif row["baseline"] != STAGE2_BASELINE_ID:
            errors.append(f"reader_jobs:{line_number}: unexpected baseline {row['baseline']!r}")
        for field, allowed in (
            ("segment", READER_SEGMENTS),
            ("situation", READER_SITUATIONS),
            ("journey_phase", JOURNEY_PHASES),
            ("evidence_strength", EVIDENCE_STRENGTHS),
            ("priority_band", PRIORITY_BANDS),
            ("confidence", CONFIDENCE_LEVELS),
            ("persona_status", PERSONA_STATUSES),
        ):
            if row[field] not in allowed:
                errors.append(f"reader_jobs:{line_number}: unknown {field} {row[field]!r}")

        scores: list[int] = []
        for field in ("frequency", "impact", "risk", "product_priority"):
            try:
                value = int(row[field])
            except ValueError:
                errors.append(f"reader_jobs:{line_number}: invalid {field} {row[field]!r}")
                continue
            if value not in range(1, 6):
                errors.append(f"reader_jobs:{line_number}: {field} outside 1..5: {value}")
            scores.append(value)
        try:
            priority_score = int(row["priority_score"])
        except ValueError:
            errors.append(f"reader_jobs:{line_number}: invalid priority_score {row['priority_score']!r}")
        else:
            if len(scores) == 4 and priority_score != sum(scores):
                errors.append(f"reader_jobs:{line_number}: priority_score {priority_score} != {sum(scores)}")
            expected_band = _priority_band(priority_score)
            if row["priority_band"] != expected_band:
                errors.append(
                    f"reader_jobs:{line_number}: priority_band {row['priority_band']!r} != {expected_band!r}"
                )
        if row["priority_band"] == "primary" and row["evidence_strength"] not in {"strong", "moderate"}:
            errors.append(f"reader_jobs:{line_number}: primary job has {row['evidence_strength']} evidence")

        for evidence_id in row["evidence_ids"].split(";"):
            if evidence_id != evidence_id.strip() or not EVIDENCE_ID_RE.fullmatch(evidence_id):
                errors.append(f"reader_jobs:{line_number}: malformed evidence_ids entry {evidence_id!r}")

    for evidence_id, row in evidence_by_id.items():
        if row["supports_jobs"] == "none":
            continue
        for job_id in row["supports_jobs"].split(";"):
            job = jobs_by_id.get(job_id)
            if job is None:
                errors.append(f"reader_evidence:{row['_line']}: unknown supports_jobs ID {job_id!r}")
            elif evidence_id not in job["evidence_ids"].split(";"):
                errors.append(f"reader_evidence:{row['_line']}: {job_id!r} does not cite {evidence_id!r}")
    for job_id, row in jobs_by_id.items():
        for evidence_id in row["evidence_ids"].split(";"):
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None:
                errors.append(f"reader_jobs:{row['_line']}: unknown evidence_id {evidence_id!r}")
            elif job_id not in evidence["supports_jobs"].split(";"):
                errors.append(f"reader_jobs:{row['_line']}: {evidence_id!r} does not support {job_id!r}")
    return errors


def validate_fact_ledger(
    repo_root: Path = REPO_ROOT,
    fact_file: Path = FACT_LEDGER_FILE,
    jobs_file: Path = READER_JOBS_FILE,
) -> list[str]:
    """Validate Stage 3 material facts and their evidence links."""
    rows, errors = _read_tsv(fact_file, FACT_COLUMNS)
    job_rows, job_errors = _read_tsv(jobs_file, READER_JOB_COLUMNS)
    errors.extend(job_errors)
    job_ids = {row["job_id"] for row in job_rows}
    seen_ids: set[str] = set()

    def check_locators(value: str, *, field: str, line_number: str, allow_none: bool) -> None:
        if value == "none" and allow_none:
            return
        for locator in value.split(";"):
            if locator != locator.strip():
                errors.append(f"facts:{line_number}: {field} locator has surrounding whitespace: {locator!r}")
                continue
            source_name = _base_locator(locator)
            source_path = repo_root / source_name
            if not source_path.is_file():
                errors.append(f"facts:{line_number}: missing {field} locator {source_name!r}")
                continue
            if "#" in locator and source_path.suffix.lower() == ".md":
                fragment = locator.split("#", 1)[1].split("::", 1)[0]
                if fragment not in _markdown_heading_slugs(source_path):
                    errors.append(f"facts:{line_number}: missing {field} heading {fragment!r} in {source_name}")
            if "::" in locator and source_path.suffix.lower() == ".py":
                qualified_name = locator.split("::", 1)[1].split("#", 1)[0]
                if qualified_name not in _python_qualified_names(source_path):
                    errors.append(
                        f"facts:{line_number}: missing {field} Python name {qualified_name!r} in {source_name}"
                    )

    for row in rows:
        line_number = row["_line"]
        for column in FACT_COLUMNS:
            if not row[column]:
                errors.append(f"facts:{line_number}: empty required field {column}")

        fact_id = row["fact_id"]
        if not FACT_ID_RE.fullmatch(fact_id):
            errors.append(f"facts:{line_number}: malformed fact_id {fact_id!r}")
        if fact_id in seen_ids:
            errors.append(f"facts:{line_number}: duplicate fact_id {fact_id!r}")
        seen_ids.add(fact_id)

        if not BASELINE_RE.fullmatch(row["baseline"]):
            errors.append(f"facts:{line_number}: malformed baseline {row['baseline']!r}")
        elif row["baseline"] != STAGE3_BASELINE_ID:
            errors.append(f"facts:{line_number}: unexpected baseline {row['baseline']!r}")
        for field, allowed in (
            ("applicability", FACT_APPLICABILITY),
            ("evidence_level", READER_EVIDENCE_LEVELS),
            ("confidence", CONFIDENCE_LEVELS),
            ("example_requirement", EXAMPLE_REQUIREMENTS),
            ("status", FACT_STATUSES),
        ):
            if row[field] not in allowed:
                errors.append(f"facts:{line_number}: unknown {field} {row[field]!r}")

        surfaces = row["surfaces"].split(";")
        if len(set(surfaces)) != len(surfaces):
            errors.append(f"facts:{line_number}: duplicate surface in {row['surfaces']!r}")
        for surface in surfaces:
            if surface != surface.strip() or surface not in FACT_SURFACES:
                errors.append(f"facts:{line_number}: unknown surface {surface!r}")

        for job_id in row["reader_jobs"].split(";"):
            if job_id != job_id.strip() or not JOB_ID_RE.fullmatch(job_id):
                errors.append(f"facts:{line_number}: malformed reader_jobs entry {job_id!r}")
            elif job_id not in job_ids:
                errors.append(f"facts:{line_number}: unknown reader job {job_id!r}")

        check_locators(row["source_locators"], field="source", line_number=line_number, allow_none=False)
        check_locators(row["test_locators"], field="test", line_number=line_number, allow_none=True)

        published = row["status"] in {"authored", "reviewed"}
        if published and row["applicability"] not in {"current", "version_specific"}:
            errors.append(f"facts:{line_number}: published fact cannot be {row['applicability']!r}")
        if published and row["evidence_level"] not in {
            "verified_implementation",
            "artifact_verified",
            "live_project_verified",
        }:
            errors.append(f"facts:{line_number}: published fact has weak evidence {row['evidence_level']!r}")
        if published and row["test_locators"] == "none":
            errors.append(f"facts:{line_number}: published fact has no test locator")
        if published and surfaces == ["research"]:
            errors.append(f"facts:{line_number}: published fact has no reader-facing surface")
        if row["example_requirement"] == "required" and "examples" not in surfaces:
            errors.append(f"facts:{line_number}: required example is not projected to Examples")
        if row["status"] == "disputed" and any(surface != "research" for surface in surfaces):
            errors.append(f"facts:{line_number}: disputed fact cannot be reader-facing")

    return errors


def validate_inventory(
    repo_root: Path = REPO_ROOT,
    source_file: Path = INVENTORY_FILE,
    *,
    check_live: bool = True,
) -> list[str]:
    """Validate the content inventory, optionally comparing it to the live tree."""
    rows, errors = _read_tsv(source_file, INVENTORY_COLUMNS)
    artifact_ids: set[str] = set()
    by_type: dict[str, set[str]] = {artifact_type: set() for artifact_type in ARTIFACT_TYPES}

    for row in rows:
        line_number = row["_line"]
        for column in INVENTORY_COLUMNS:
            if not row[column]:
                errors.append(f"inventory:{line_number}: empty required field {column}")
        if not BASELINE_RE.fullmatch(row["baseline"]):
            errors.append(f"inventory:{line_number}: malformed baseline {row['baseline']!r}")
        elif row["baseline"] != BASELINE_ID:
            errors.append(f"inventory:{line_number}: unexpected baseline {row['baseline']!r}")
        if row["artifact_type"] not in ARTIFACT_TYPES:
            errors.append(f"inventory:{line_number}: unknown artifact_type {row['artifact_type']!r}")
        if row["source_kind"] not in SOURCE_KINDS:
            errors.append(f"inventory:{line_number}: unknown source_kind {row['source_kind']!r}")
        if row["evidence_state"] not in EVIDENCE_STATES:
            errors.append(f"inventory:{line_number}: unknown evidence_state {row['evidence_state']!r}")
        if row["inventory_state"] not in INVENTORY_STATES:
            errors.append(f"inventory:{line_number}: unknown inventory_state {row['inventory_state']!r}")
        elif row["inventory_state"] != "complete":
            errors.append(f"inventory:{line_number}: row {row['artifact_id']!r} is {row['inventory_state']!r}")

        if row["artifact_type"] in {"example_family", "snippet_module"}:
            if row["consumer_locators"] in {"none", "n/a"}:
                errors.append(
                    f"inventory:{line_number}: {row['artifact_type']} {row['artifact_id']!r} has no known consumer"
                )
            if row["test_locators"] in {"none", "n/a"}:
                errors.append(
                    f"inventory:{line_number}: {row['artifact_type']} {row['artifact_id']!r} has no known test"
                )
            if row["evidence_state"] == "unverified":
                errors.append(f"inventory:{line_number}: {row['artifact_type']} {row['artifact_id']!r} is unverified")

        artifact_id = row["artifact_id"]
        if artifact_id in artifact_ids:
            errors.append(f"inventory:{line_number}: duplicate artifact_id {artifact_id!r}")
        artifact_ids.add(artifact_id)
        if row["artifact_type"] in by_type:
            by_type[row["artifact_type"]].add(artifact_id)

        errors.extend(
            _check_local_locators(
                repo_root,
                row["source_locator"],
                field="source",
                line_number=line_number,
                sentinels={"n/a", "none"},
            )
        )
        errors.extend(
            _check_local_locators(
                repo_root,
                row["test_locators"],
                field="test",
                line_number=line_number,
                sentinels={"n/a", "none"},
            )
        )
        errors.extend(
            _check_local_locators(
                repo_root,
                row["consumer_locators"],
                field="consumer",
                line_number=line_number,
                sentinels={"n/a", "none", "direct-reader", "site-build"},
            )
        )

    if check_live:
        for artifact_type, expected in _expected_live_ids(repo_root).items():
            actual = by_type[artifact_type]
            for missing in sorted(expected - actual):
                errors.append(f"inventory: live {artifact_type} missing row: {missing}")
            for extra in sorted(actual - expected):
                errors.append(f"inventory: extra {artifact_type} row: {extra}")

        content_urls = {row["public_locator"] for row in rows if row["artifact_type"] == "content_page"}
        nav_paths = _nav_paths(repo_root)
        duplicate_nav = sorted(item for item, count in Counter(nav_paths).items() if count > 1)
        if duplicate_nav:
            errors.append(f"navigation: duplicate paths: {duplicate_nav}")
        missing_nav = sorted(content_urls - set(nav_paths))
        dead_nav = sorted(set(nav_paths) - content_urls)
        if missing_nav:
            errors.append(f"navigation: content URLs absent from nav: {missing_nav}")
        if dead_nav:
            errors.append(f"navigation: nav paths without content: {dead_nav}")

        for row in rows:
            if row["artifact_type"] != "content_page":
                continue
            source = repo_root / _base_locator(row["source_locator"])
            if not source.is_file():
                # Locator validation above already reports the missing source.
                # Keep reconciling the rest of a stale inventory instead of
                # aborting on the first renamed or removed page.
                continue
            opening = source.read_text(encoding="utf-8").split("---", 2)
            if len(opening) < 3:
                errors.append(f"{source}: missing front matter")
                continue
            front = opening[1]
            for key in ("title", "description"):
                if not re.search(rf"(?m)^{key}:\s*\S", front):
                    errors.append(f"{source}: missing explicit {key}")
    return errors


def validate_fingerprints(
    repo_root: Path = REPO_ROOT,
    source_file: Path = FINGERPRINT_FILE,
    *,
    check_live: bool = True,
) -> list[str]:
    """Validate closing fingerprint rows against the current files."""
    rows, errors = _read_tsv(source_file, FINGERPRINT_COLUMNS)
    seen_sources: set[str] = set()
    for row in rows:
        line_number = row["_line"]
        for column in FINGERPRINT_COLUMNS:
            if not row[column]:
                errors.append(f"fingerprints:{line_number}: empty required field {column}")
        if not BASELINE_RE.fullmatch(row["baseline"]):
            errors.append(f"fingerprints:{line_number}: malformed baseline {row['baseline']!r}")
        elif row["baseline"] != BASELINE_ID:
            errors.append(f"fingerprints:{line_number}: unexpected baseline {row['baseline']!r}")
        if row["scope"] not in FINGERPRINT_SCOPES:
            errors.append(f"fingerprints:{line_number}: unknown scope {row['scope']!r}")

        source_name = row["source_path"]
        if source_name in seen_sources:
            errors.append(f"fingerprints:{line_number}: duplicate source_path {source_name!r}")
        seen_sources.add(source_name)
        if source_name == EXTERNAL_PYTHON_INVENTORY:
            local_file = _python_inventory_cache_path(repo_root)
        else:
            local_file = repo_root / source_name
        if not local_file.is_file():
            errors.append(f"fingerprints:{line_number}: missing source file {source_name}")
            continue
        try:
            expected_size = int(row["byte_size"])
        except ValueError:
            errors.append(f"fingerprints:{line_number}: invalid byte_size {row['byte_size']!r}")
            continue
        if expected_size != local_file.stat().st_size:
            errors.append(
                f"fingerprints:{line_number}: stale size for {source_name}: "
                f"{expected_size} != {local_file.stat().st_size}"
            )
        actual_hash = hashlib.sha256(local_file.read_bytes()).hexdigest()
        if row["sha256"] != actual_hash:
            errors.append(f"fingerprints:{line_number}: stale sha256 for {source_name}")
        if check_live:
            actual_git_state = (
                "n/a" if source_name == EXTERNAL_PYTHON_INVENTORY else _git_state(repo_root, source_name)
            )
            if row["git_state"] != actual_git_state:
                errors.append(
                    f"fingerprints:{line_number}: stale git_state for {source_name}: "
                    f"{row['git_state']!r} != {actual_git_state!r}"
                )

    if check_live:
        expected_sources = {
            source_file.relative_to(repo_root).as_posix() for source_file in _capture_source_files(repo_root)
        }
        expected_sources.add(EXTERNAL_PYTHON_INVENTORY)
        for missing in sorted(expected_sources - seen_sources):
            errors.append(f"fingerprints: live source missing row: {missing}")
        for extra in sorted(seen_sources - expected_sources):
            errors.append(f"fingerprints: extra source row: {extra}")
    return errors


def _capture_source_files(repo_root: Path) -> list[Path]:
    """Return the deterministic closing source set for Stage 1."""
    sources: set[Path] = set()

    def add_tree(tree_root: Path) -> None:
        if not tree_root.exists():
            return
        for candidate in tree_root.rglob("*"):
            if not candidate.is_file():
                continue
            if (
                candidate.name == ".DS_Store"
                or candidate.suffix in {".dylib", ".pyc", ".pyd", ".so"}
                or "__pycache__" in candidate.parts
                or ".cache" in candidate.parts
            ):
                continue
            sources.add(candidate)

    add_tree(repo_root / "docs_site")
    add_tree(repo_root / "packages/py/citry/citry")
    add_tree(repo_root / "packages/py/citry_core/citry_core")
    native_prefix = f"_rust.cpython-{sys.version_info.major}{sys.version_info.minor}-"
    sources.update(
        candidate
        for candidate in (repo_root / "packages/py/citry_core/citry_core").glob(f"{native_prefix}*")
        if candidate.is_file()
    )
    add_tree(repo_root / "docs/design/docs_content_research")
    for crate in ("citry_core_py", "citry_html_transform", "citry_template_parser", "python_safe_eval"):
        add_tree(repo_root / "crates" / crate)

    for relative in (
        "README.md",
        "CHANGELOG.md",
        "CODE_OF_CONDUCT.md",
        "LICENSE",
        "docs/design/docs_content.md",
        "docs/design/docs_site.md",
        "packages/py/citry/README.md",
        "packages/py/citry/pyproject.toml",
        "packages/py/citry_core/pyproject.toml",
        "packages/py/citry_core/uv.lock",
        ".python-version",
        "Cargo.lock",
        "Cargo.toml",
        "pyproject.toml",
        "rust-toolchain.toml",
        "uv.lock",
    ):
        candidate = repo_root / relative
        if candidate.is_file():
            sources.add(candidate)

    for pattern in ("repo--docs-*.yml", "py--citry--publish.yml"):
        sources.update((repo_root / ".github/workflows").glob(pattern))

    sources.discard(FINGERPRINT_FILE)
    sources.discard(RESEARCH_DIR / "evidence_log.md")
    return sorted(sources, key=lambda item: item.relative_to(repo_root).as_posix())


def _fingerprint_scope(relative: str) -> str:
    """Classify why a captured file is part of the Stage 1 evidence set."""
    if relative.startswith("docs_site/content/"):
        return "content"
    if relative.startswith("docs_site/examples/"):
        return "example"
    if relative.startswith("docs_site/snippets/") or relative in {"CODE_OF_CONDUCT.md", "LICENSE"}:
        return "snippet"
    if relative.startswith("packages/py/citry/citry/") or "reference" in relative or "crossref" in relative:
        return "reference"
    if relative.startswith(("packages/py/citry_core/", "crates/")) or relative in {
        ".python-version",
        "Cargo.lock",
        "Cargo.toml",
        "pyproject.toml",
        "rust-toolchain.toml",
        "uv.lock",
    }:
        return "toolchain"
    if relative in {"README.md", "CHANGELOG.md", "packages/py/citry/README.md", "packages/py/citry/pyproject.toml"}:
        return "readme_release"
    if relative.startswith("docs_site/tests/"):
        return "test_guard"
    if relative.startswith(".github/workflows/"):
        return "workflow"
    if relative.startswith("docs/design/"):
        return "research_control"
    if relative.startswith(("docs_site/static/", "docs_site/data/", "docs_site/scripts/")):
        return "asset_data"
    return "generated_surface"


def _git_state(repo_root: Path, relative: str) -> str:
    """Return the exact two-character porcelain state or a readable sentinel."""
    result = subprocess.run(
        [  # noqa: S607 - the repository's Git executable is intentionally resolved from PATH
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            relative,
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    if not result.stdout:
        return "clean"
    state = result.stdout[:2]
    return "untracked" if state == "??" else state


def _python_inventory_cache_path(repo_root: Path) -> Path:
    """Resolve the host-cached external inventory used by Reference rendering."""
    source = (repo_root / "docs_site/_internal/inventory.py").read_text(encoding="utf-8")
    match = re.search(r'^_PYTHON_DOCS\s*=\s*"([^"]+)"', source, flags=re.MULTILINE)
    if match is None:
        msg = "Cannot resolve _PYTHON_DOCS from docs_site/_internal/inventory.py"
        raise ValueError(msg)
    url = match.group(1).rstrip("/") + "/objects.inv"
    cache_name = hashlib.sha256(url.encode()).hexdigest()[:16] + ".inv"
    return Path(tempfile.gettempdir()) / "citry-docs-inventories" / cache_name


def _fingerprint_rows(repo_root: Path) -> list[dict[str, str]]:
    """Build deterministic rows for repository and external evidence inputs."""
    rows: list[dict[str, str]] = []
    for source_file in _capture_source_files(repo_root):
        relative = source_file.relative_to(repo_root).as_posix()
        body = source_file.read_bytes()
        rows.append(
            {
                "baseline": BASELINE_ID,
                "scope": _fingerprint_scope(relative),
                "source_path": relative,
                "git_state": _git_state(repo_root, relative),
                "byte_size": str(len(body)),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        )

    external_file = _python_inventory_cache_path(repo_root)
    if not external_file.is_file():
        msg = f"External Python inventory cache is missing: {external_file}"
        raise FileNotFoundError(msg)
    external_body = external_file.read_bytes()
    rows.append(
        {
            "baseline": BASELINE_ID,
            "scope": "external_input",
            "source_path": EXTERNAL_PYTHON_INVENTORY,
            "git_state": "n/a",
            "byte_size": str(len(external_body)),
            "sha256": hashlib.sha256(external_body).hexdigest(),
        }
    )
    return sorted(rows, key=lambda row: row["source_path"])


def _serialize_fingerprints(rows: list[dict[str, str]]) -> str:
    """Serialize fingerprint rows with stable TSV formatting."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FINGERPRINT_COLUMNS, delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _fingerprint_deltas(destination: Path, rows: list[dict[str, str]]) -> list[str]:
    """Describe old-to-new row changes without modifying the destination."""
    if not destination.is_file():
        return []
    old_rows, errors = _read_tsv(destination, FINGERPRINT_COLUMNS)
    if errors:
        return [f"existing fingerprint file is invalid: {error}" for error in errors]
    old = {row["source_path"]: {column: row[column] for column in FINGERPRINT_COLUMNS} for row in old_rows}
    new = {row["source_path"]: row for row in rows}
    deltas = [f"removed {source_name}" for source_name in sorted(old.keys() - new.keys())]
    deltas.extend(f"added {source_name}" for source_name in sorted(new.keys() - old.keys()))
    for source_name in sorted(old.keys() & new.keys()):
        changed = [column for column in FINGERPRINT_COLUMNS if old[source_name][column] != new[source_name][column]]
        if changed:
            deltas.append(f"changed {source_name}: {','.join(changed)}")
    return deltas


def capture_fingerprints(
    repo_root: Path = REPO_ROOT,
    destination: Path = FINGERPRINT_FILE,
    *,
    accept_changes: bool = False,
) -> tuple[int, list[str], bool]:
    """Capture fingerprints, refusing to replace a changed baseline silently."""
    rows = _fingerprint_rows(repo_root)
    deltas = _fingerprint_deltas(destination, rows)
    if destination.is_file() and deltas and not accept_changes:
        return len(rows), deltas, False
    destination.write_text(_serialize_fingerprints(rows), encoding="utf-8")
    return len(rows), deltas, True


def main(argv: list[str] | None = None) -> int:
    """Validate Stage 1 through Stage 3 research artifacts and report every error."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture",
        action="store_true",
        help="capture fingerprints; refuse changed rows unless --accept-changes is also given",
    )
    parser.add_argument(
        "--accept-changes",
        action="store_true",
        help="with --capture, replace fingerprints after reporting the old-to-new delta",
    )
    args = parser.parse_args(argv)
    if args.accept_changes and not args.capture:
        parser.error("--accept-changes requires --capture")
    if args.capture:
        try:
            count, deltas, wrote = capture_fingerprints(accept_changes=args.accept_changes)
        except (FileNotFoundError, ValueError) as exc:
            print(f"ERROR {exc}")  # noqa: T201 - CLI validation report
            return 1
        for delta in deltas:
            print(f"DELTA {delta}")  # noqa: T201 - explicit baseline change report
        if not wrote:
            print("ERROR Refusing to replace changed fingerprints without --accept-changes")  # noqa: T201
            return 1
        print(f"Captured {count} Stage 1 source fingerprints")  # noqa: T201 - CLI status output
    errors = validate_inventory() + validate_fingerprints() + validate_reader_records() + validate_fact_ledger()
    if errors:
        for error in errors:
            print(f"ERROR {error}")  # noqa: T201 - CLI validation report
        return 1
    print("PASS docs content Stage 1 inventory/fingerprints, Stage 2 reader records, and Stage 3 facts")  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
