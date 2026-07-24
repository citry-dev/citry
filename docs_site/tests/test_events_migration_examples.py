"""Execute the Citry source used by the four Events migration guides."""

from __future__ import annotations

import html as html_module
import re
import subprocess
import sys
from pathlib import Path

import pytest

from docs_site._internal.config import config
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


def _active_snippet_directives(source: str) -> list[str]:
    """Return real includes, excluding escaped ``;--8<--`` documentation."""
    return [line.strip() for line in source.splitlines() if line.lstrip().startswith("--8<-- ")]


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
        ("migrate-from-component-view.md", ("class ContactForm", "class FragmentLoader")),
        (
            "migrate-from-django-unicorn.md",
            ("class LiveSearch", "class Rating", "class Preferences"),
        ),
        ("migrate-from-tetra.md", ("class Counter", "class TaskEditor")),
        ("migrate-from-livecomponents.md", ("class ServerCounter", "class SignedCounter")),
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
    for directive in _active_snippet_directives(source):
        assert directive not in text
        assert directive not in result.markdown_body


def test_every_snippet_page_exports_self_contained_markdown() -> None:
    snippet_pages: list[tuple[Path, str, list[str]]] = []
    for path in sorted(CONTENT_ROOT.rglob("*.md")):
        source = path.read_text(encoding="utf-8")
        directives = _active_snippet_directives(source)
        if directives:
            snippet_pages.append((path, source, directives))

    assert snippet_pages
    for source_path, source, directives in snippet_pages:
        result = render_page(source, config=config, wrap_in_layout=False)
        for directive in directives:
            assert directive not in result.markdown_body, source_path
