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


def md_companion_path(output_dir: Path, rel: Path) -> Path:
    """
    Output ``.md`` companion path for a content markdown file (path relative to the content dir).

    The companion sits beside the page's ``index.html`` under the same clean-URL
    directory (``foo.md`` -> ``foo/index.md``), so the page at ``/foo/`` has its
    raw markdown at ``/foo/index.md``.
    """
    if rel.stem == "index":
        return output_dir / rel.parent / "index.md"
    return output_dir / rel.with_suffix("") / "index.md"


def clean_url_to_html_path(output_dir: Path, url_path: str) -> Path:
    """Output HTML path for a clean public URL, including generated routes."""
    clean = url_path.strip("/")
    return output_dir / clean / "index.html" if clean else output_dir / "index.html"


def clean_url_to_companion_path(output_dir: Path, url_path: str) -> Path:
    """Output Markdown-companion path for a clean public URL."""
    clean = url_path.strip("/")
    return output_dir / clean / "index.md" if clean else output_dir / "index.md"


def clean_url_to_companion_url(url_path: str) -> str:
    """Root-relative Markdown-companion URL for a clean public URL."""
    clean = url_path.strip("/")
    return f"/{clean}/index.md" if clean else "/index.md"


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
