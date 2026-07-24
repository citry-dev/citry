"""
Shrink the built HTML as a final pass.

After every page is written, this walks the output tree and rewrites each
``*.html`` file in place with the whitespace and redundant markup removed.
GitHub Pages already gzips responses, so the transfer saving is small, but a
smaller document also parses faster in the browser.

The configuration is deliberately cautious: closing tags, the ``<html>`` /
``<head>`` opening tags, and comments are kept. Citry's client ownership graph
uses paired comments as physical range caps, so dropping comments breaks
component activation. Inline CSS is shrunk. Inline JavaScript is left untouched
on purpose, so ``<script type="application/ld+json">`` structured-data blocks
stay valid JSON. The minifier handles ``<pre>`` and other whitespace-sensitive
regions itself.

The ``minify-html`` import is loaded only when this runs and is guarded, so a
build on a machine without it simply skips this step instead of failing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# Options passed to minify_html.minify (v0.18+). The cautious defaults we want
# (doctype kept, attribute values left spec-compliant, spaces between attributes
# preserved, <pre> whitespace untouched) are the library's own defaults; we only
# opt into keeping comments and the closing / html+head opening tags, and
# shrinking inline CSS. Inline-JS minification stays off so the JSON-LD
# <script> blocks are not touched.
_MINIFY_CONFIG = {
    "minify_css": True,
    "keep_comments": True,
    "keep_closing_tags": True,
    "keep_html_and_head_opening_tags": True,
}


@dataclass
class MinifyOutcome:
    """How the minify pass went: counts, byte totals, and why it was skipped."""

    files: int = 0  # html files minified
    before: int = 0  # total bytes before
    after: int = 0  # total bytes after
    skipped_reason: str = ""  # set when minify-html is not available


def minify_site(output_dir: Path, *, log: Callable[[str], None] = lambda _msg: None) -> MinifyOutcome:
    """Shrink every ``*.html`` under ``output_dir`` in place. A no-op if minify-html is missing."""
    try:
        import minify_html  # noqa: PLC0415
    except ImportError:
        log("minify-html not installed; skipping HTML minification")
        return MinifyOutcome(skipped_reason="minify-html-missing")

    outcome = MinifyOutcome()
    for html_path in output_dir.rglob("*.html"):
        src = html_path.read_text(encoding="utf-8")
        out = minify_html.minify(src, **_MINIFY_CONFIG)
        html_path.write_text(out, encoding="utf-8")
        outcome.files += 1
        outcome.before += len(src)
        outcome.after += len(out)
    return outcome
