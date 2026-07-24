"""
Build the search index after the site is built.

Pagefind is a static search engine: once the HTML is on disk, it scans the
output directory and writes a compact, chunked index under ``<output>/pagefind/``
that the browser queries directly, with no server involved.

What gets indexed is controlled by the page markup, not from here:

- ``data-pagefind-body`` on the article element limits indexing to the article
  text, so the header, sidebar, table of contents, and footer are left out.
- ``data-pagefind-weight`` on the same element applies a per-page ranking boost
  taken from the ``boost`` front-matter field.

The binary ships with the ``pagefind[bin]`` dependency and is run via
``python -m pagefind`` so it uses the same interpreter as the build.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# Pagefind writes its bundle to this subdirectory of the site by default.
PAGEFIND_OUTPUT_SUBDIR = "pagefind"


@dataclass
class PagefindOutcome:
    """Whether the index built, a human message, and the CLI output on failure."""

    ok: bool
    message: str
    # Combined stdout+stderr from the pagefind CLI, surfaced when it fails.
    output: str = ""


def run_pagefind(output_dir: Path) -> PagefindOutcome:
    """
    Build the search index over an already-built site directory.

    Returns a ``PagefindOutcome`` instead of raising, so a search-index failure
    is reported without discarding an otherwise successful build.
    """
    if not output_dir.is_dir():
        return PagefindOutcome(ok=False, message=f"Site directory not found: {output_dir}")

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pagefind", "--site", str(output_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        # The pagefind binary is missing: the docs dependencies are not installed.
        return PagefindOutcome(
            ok=False,
            message=(
                "pagefind binary not found; install the docs dependencies "
                "(the `docs` extra, which pulls pagefind[bin])."
            ),
        )

    combined = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return PagefindOutcome(
            ok=False, message=f"pagefind exited with code {proc.returncode}", output=combined.strip()
        )

    bundle = output_dir / PAGEFIND_OUTPUT_SUBDIR
    if not bundle.is_dir():
        return PagefindOutcome(
            ok=False,
            message=f"pagefind reported success but no index was written to {bundle}",
            output=combined.strip(),
        )

    return PagefindOutcome(ok=True, message=f"Search index written to {bundle}", output=combined.strip())
