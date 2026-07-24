"""
Golden-file snapshot regression test for the content-HTML render pipeline.

Parity row 3b.17: django-components ships a syrupy content-HTML snapshot; this is
the citry-native, dependency-free equivalent. It renders a few representative
content pages to their *content HTML* and locks the output into golden files
under ``snapshots/``. Any later change that alters the render output for these
pages fails this test, surfacing the diff for review.

Why content HTML only: ``render_page(..., wrap_in_layout=False)`` returns just
the content HTML, before the ``DocPage`` layout is applied. The layout is where
the non-deterministic bits live (git-derived dates, social-card hashes), so
excluding it keeps the snapshot byte-stable across machines and runs. The one
per-render id source in the content path (``<c-example>``'s radio ids) is avoided
by page choice, and ``test_render_is_deterministic`` proves nothing else leaks.

Why these pages: each renders deterministically while exercising the pipeline
broadly:

- ``getting-started/your-first-component``: prose, ``[X][symbol]`` cross-refs,
  and python/html code fences (fence protection plus Pygments highlighting).
- ``syntax/control-flow``: many code fences that *show* ``<c-*>`` tags as literal
  code, the strongest check that fence protection escapes them (``&lt;c-if&gt;``)
  rather than executing them.
- ``about/benchmarks``: expands a real custom tag (``<c-image>``) and renders a
  markdown table.

Regenerating the goldens: set ``UPDATE_SNAPSHOTS=1`` to rewrite the golden files
from the current render instead of asserting against them::

    UPDATE_SNAPSHOTS=1 .venv/bin/python -m pytest docs_site/tests/test_content_snapshot.py

Review the resulting diff before committing; an unexpected change there is the
signal this test exists to catch.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from docs_site._internal.config import config as default_config
from docs_site._internal.paths import md_to_url
from docs_site._internal.pipeline import render_page

# The committed golden files live here, one per page in ``_PAGES`` below.
_SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

# When set, rewrite the goldens from the current render instead of asserting
# against them (see the module docstring for the observe-then-lock workflow).
_UPDATE_SNAPSHOTS = os.environ.get("UPDATE_SNAPSHOTS") == "1"

# (content-relative source page, golden file stem). Chosen for deterministic
# output plus broad pipeline coverage; see the module docstring.
_PAGES = [
    ("getting-started/your-first-component.md", "getting-started_your-first-component"),
    ("syntax/control-flow.md", "syntax_control-flow"),
    ("about/benchmarks.md", "about_benchmarks"),
]
_PAGE_RELS = [page_rel for page_rel, _ in _PAGES]


def _render_content_html(page_rel: str) -> str:
    """
    Render one content page to its content HTML only (no surrounding chrome).

    ``wrap_in_layout=False`` returns the content HTML before the ``DocPage``
    layout, which is where the non-deterministic values (git dates, social-card
    hashes) live. ``source_path`` is passed to mirror the real build so the
    internal-link rewrite runs; for these pages every link is already a clean or
    external URL, so it is a no-op and the output stays deterministic.
    """
    source_path = default_config.content_dir / page_rel
    source = source_path.read_text(encoding="utf-8")
    result = render_page(
        source,
        config=default_config,
        current_path=md_to_url(Path(page_rel)),
        source_path=source_path,
        wrap_in_layout=False,
    )
    return result.html


@pytest.mark.parametrize(("page_rel", "golden_stem"), _PAGES)
def test_content_html_matches_golden(page_rel: str, golden_stem: str) -> None:
    """Each page's content HTML must byte-match its committed golden file."""
    rendered = _render_content_html(page_rel)
    golden_path = _SNAPSHOT_DIR / f"{golden_stem}.content.html"

    if _UPDATE_SNAPSHOTS:
        _SNAPSHOT_DIR.mkdir(exist_ok=True)
        golden_path.write_text(rendered, encoding="utf-8")
        pytest.skip(f"UPDATE_SNAPSHOTS=1: rewrote {golden_path.name}")

    assert golden_path.is_file(), (
        f"Missing golden {golden_path}. Generate it once with UPDATE_SNAPSHOTS=1 (see this module's docstring)."
    )
    expected = golden_path.read_text(encoding="utf-8")
    assert rendered == expected, (
        f"Content HTML for {page_rel} no longer matches {golden_path.name}. If the "
        f"change is intended, regenerate with UPDATE_SNAPSHOTS=1 and review the diff."
    )


@pytest.mark.parametrize("page_rel", _PAGE_RELS)
def test_render_is_deterministic(page_rel: str) -> None:
    """
    Two renders of the same page in one process must be byte-identical.

    ``render_content`` gives each render a fresh component name from a
    module-level counter, so if that counter (or any per-render id) leaked into
    the output, the second render would differ from the first. Byte-identity
    proves nothing per-render leaks, which is what makes the golden stable.
    """
    first = _render_content_html(page_rel)
    second = _render_content_html(page_rel)
    assert first == second
