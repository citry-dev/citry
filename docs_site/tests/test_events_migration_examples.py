"""Execute the Citry source used by the four Events migration guides."""

from __future__ import annotations

import html as html_module
import re
import subprocess
import sys
from pathlib import Path

import pytest

from docs_site._internal.config import config
from docs_site._internal.pipeline import _pass2_markdown

CONTENT = Path(__file__).resolve().parents[1] / "content" / "guides"
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PAGES = (
    "migrate-from-component-view.md",
    "migrate-from-django-unicorn.md",
    "migrate-from-tetra.md",
    "migrate-from-livecomponents.md",
)


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
    rendered_html, _toc = _pass2_markdown(source_path.read_text(encoding="utf-8"), config=config)
    text = html_module.unescape(re.sub(r"<[^>]+>", "", rendered_html))
    for fingerprint in fingerprints:
        assert fingerprint in text
    assert "--8<--" not in text
