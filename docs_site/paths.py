"""
URL <-> content-file path mapping.

Shared by the build (markdown file -> output HTML path / URL) and the dev server
(incoming URL -> source markdown file), so both stay consistent. Ported from the
upstream docs site; the slug convention is unchanged:

    foo.md         -> /foo/   (output: foo/index.html)
    bar/index.md   -> /bar/   (output: bar/index.html)
    index.md       -> /       (output: index.html)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def md_to_html_path(output_dir: Path, rel: Path) -> Path:
    """Output HTML path for a content markdown file (path relative to the content dir)."""
    if rel.stem == "index":
        return output_dir / rel.parent / "index.html"
    return output_dir / rel.with_suffix("") / "index.html"


def md_to_url(rel: Path) -> str:
    """Clean URL path for a content markdown file (e.g. ``foo/`` or ``bar/baz/``)."""
    if rel.stem == "index":
        parent = str(rel.parent)
        return parent + "/" if parent != "." else ""
    return str(rel.with_suffix("")) + "/"


def url_to_md(content_dir: Path, url_path: str) -> Path | None:
    """
    Resolve an incoming URL path to a source markdown file, or ``None`` if none.

    Reverse of :func:`md_to_url`. Tries both the flat form (``foo`` -> ``foo.md``)
    and the directory-index form (``foo`` -> ``foo/index.md``), and rejects paths
    that escape the content directory (e.g. via ``..``).
    """
    clean = url_path.strip("/")
    candidates = ["index.md"] if not clean else [f"{clean}.md", f"{clean}/index.md"]

    base = content_dir.resolve()
    for rel in candidates:
        candidate = (base / rel).resolve()
        if not candidate.is_relative_to(base):
            continue
        if candidate.is_file():
            return candidate
    return None
