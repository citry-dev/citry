"""
Build the search index after the site is built.

Pagefind is a static search engine: once the HTML is on disk, it scans the
output directory and writes a compact, chunked index under a configured output
subdirectory (``<output>/pagefind/`` by default) that the browser queries
directly, with no server involved.

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


def run_pagefind(output_dir: Path, output_subdir: str = PAGEFIND_OUTPUT_SUBDIR) -> PagefindOutcome:
    """
    Build the search index over an already-built site directory.

    Returns a ``PagefindOutcome`` instead of raising, so a search-index failure
    is reported without discarding an otherwise successful build. The output
    subdirectory comes from the validated browser module path in ``settings.yml``.
    """
    if not output_dir.is_dir():
        return PagefindOutcome(ok=False, message=f"Site directory not found: {output_dir}")

    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pagefind",
                "--site",
                str(output_dir),
                "--output-subdir",
                output_subdir,
            ],
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

    bundle = output_dir / output_subdir
    if not bundle.is_dir():
        return PagefindOutcome(
            ok=False,
            message=f"pagefind reported success but no index was written to {bundle}",
            output=combined.strip(),
        )
    entrypoint = bundle / "pagefind.js"
    if not entrypoint.is_file():
        return PagefindOutcome(
            ok=False,
            message=f"pagefind reported success but no browser entrypoint was written to {entrypoint}",
            output=combined.strip(),
        )

    return PagefindOutcome(ok=True, message=f"Search index written to {bundle}", output=combined.strip())
