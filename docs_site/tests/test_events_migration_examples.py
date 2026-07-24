"""Execute the Citry source used by the four Events migration guides."""

from __future__ import annotations

import html as html_module
import re
import subprocess
import sys
from pathlib import Path

import pytest

from docs_site._internal.config import config
from docs_site._internal.guards.snippet_path import iter_snippet_refs
from docs_site._internal.pipeline import render_page

CONTENT_ROOT = Path(__file__).resolve().parents[1] / "content"
CONTENT = CONTENT_ROOT / "guides"
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PAGES = (
    "migrate-from-component-view.md",
    "migrate-from-django-unicorn.md",
    "migrate-from-tetra.md",
    "migrate-from-livecomponents.md",
)


def _active_snippet_refs(source: str) -> list[str]:
    """Return inline and block include paths, excluding escaped documentation."""
    return [raw_path for _lineno, raw_path in iter_snippet_refs(source)]


def test_executable_migration_snippets() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "docs_site.snippets._verify_events_migrations"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_migration_page_carries_the_shared_authoring_contract() -> None:
    for page in MIGRATION_PAGES:
        source = (CONTENT / page).read_text(encoding="utf-8")
        assert 'href="{{ ' in source
        assert 'c-href="' in source
        assert "## Syntax mapping" in source
        assert "/guides/events-migration-parity/" in source


def test_parity_matrix_has_every_delivery_class_and_v1_acceptance() -> None:
    source = (CONTENT / "events-migration-parity.md").read_text(encoding="utf-8")
    for label in ("**v1**", "**v1.x**", "**v2**", "**Dropped**"):
        assert label in source
    assert "## Events v1 acceptance checklist" in source
    for page in MIGRATION_PAGES:
        route = page.removesuffix(".md")
        assert f"/guides/{route}/" in source


@pytest.mark.parametrize(
    ("page", "fingerprints"),
    [
        (
            "migrate-from-component-view.md",
            ("class ContactForm(Component)", "class NamedContactForm(Component)", "class FragmentLoader(Component)"),
        ),
        (
            "migrate-from-django-unicorn.md",
            (
                "class LiveSearch(Component)",
                "class Rating(Component)",
                "raise EventError(",
                "class Preferences(Component)",
            ),
        ),
        ("migrate-from-tetra.md", ("class Counter(Component)", "class TaskEditor(Component)")),
        (
            "migrate-from-livecomponents.md",
            ("class ServerCounter(Component)", "class SignedCounter(Component)", "class TaskEditor(Component)"),
        ),
    ],
)
def test_migration_pages_expand_their_executable_snippets(page: str, fingerprints: tuple[str, ...]) -> None:
    source_path = CONTENT / page
    source = source_path.read_text(encoding="utf-8")
    result = render_page(source, config=config, wrap_in_layout=False)
    text = html_module.unescape(re.sub(r"<[^>]+>", "", result.html))
    for fingerprint in fingerprints:
        assert fingerprint in text
        assert fingerprint in result.markdown_body
    assert list(iter_snippet_refs(result.markdown_body)) == []


def test_every_snippet_page_exports_self_contained_markdown() -> None:
    snippet_pages: list[tuple[Path, str]] = []
    for path in sorted(CONTENT_ROOT.rglob("*.md")):
        source = path.read_text(encoding="utf-8")
        if _active_snippet_refs(source):
            snippet_pages.append((path, source))

    assert snippet_pages
    for source_path, source in snippet_pages:
        result = render_page(source, config=config, wrap_in_layout=False)
        assert list(iter_snippet_refs(result.markdown_body)) == [], source_path

    by_path = {path.relative_to(CONTENT_ROOT).as_posix(): source for path, source in snippet_pages}
    assert (
        "# Contributor Covenant Code of Conduct"
        in render_page(by_path["community/code-of-conduct.md"], config=config, wrap_in_layout=False).markdown_body
    )
    assert (
        "Permission is hereby granted"
        in render_page(by_path["community/license.md"], config=config, wrap_in_layout=False).markdown_body
    )
