"""
Build the static site: render every markdown page to HTML on disk.

Walks the content directory, renders each ``*.md`` through the pipeline, and
writes the result to ``<output>/<slug>/index.html`` (clean URLs). Non-markdown
files (images, etc.) are copied across verbatim so relative references keep
working.

A page that fails to render is recorded on the outcome rather than aborting the
whole build, so one broken page does not hide the others. The post-build steps
the upstream site runs (search index, SEO files, social cards, minify,
versioning) are added later; this is the core that produces a browsable site.
"""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version
from pathlib import Path

from docs_site.config import DocsConfig
from docs_site.config import config as default_config
from docs_site.examples import get_example_registry
from docs_site.nav import load_nav
from docs_site.paths import md_to_html_path, md_to_url
from docs_site.pipeline import render_page


@dataclass
class BuildOutcome:
    """Result of a build: where it wrote, how many pages, and any failures."""

    output_dir: Path
    built: int = 0
    failed: int = 0
    examples: int = 0
    elapsed: float = 0.0
    # (page path relative to content dir, error message) for pages that raised.
    errors: list[tuple[str, str]] = field(default_factory=list)


def build_site(*, config: DocsConfig | None = None, output_dir: Path | None = None) -> BuildOutcome:
    """
    Build every page in ``config.content_dir`` into ``output_dir``.

    ``output_dir`` defaults to ``config.site_dir``. The target is cleared first,
    so it must not be the repo root, the content dir, or a filesystem root (that
    raises ``ValueError``).
    """
    config = config or default_config
    content_dir = config.content_dir
    output_dir = (output_dir or config.site_dir).resolve()

    if _is_unsafe_output(output_dir, content_dir, config):
        msg = f"Refusing to clear unsafe output dir: {output_dir}"
        raise ValueError(msg)

    site_base = config.site_url.rstrip("/")
    md_files = sorted(p for p in content_dir.rglob("*.md") if p.name != "_nav.yml")
    nav_tree = load_nav(content_dir / "_nav.yml")
    version = _citry_version()

    if output_dir.exists():
        shutil.rmtree(output_dir)

    outcome = BuildOutcome(output_dir=output_dir)
    start = time.monotonic()

    for md_path in md_files:
        rel = md_path.relative_to(content_dir)
        out_path = md_to_html_path(output_dir, rel)
        page_url = md_to_url(rel)
        canonical = f"{site_base}/{page_url}" if site_base else ""

        try:
            source = md_path.read_text(encoding="utf-8")
            result = render_page(
                source, config=config, canonical=canonical, nav_tree=nav_tree, current_path=page_url, version=version
            )
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(result.html, encoding="utf-8")
            outcome.built += 1
        except Exception as exc:  # noqa: BLE001 - one bad page must not abort the build
            outcome.failed += 1
            outcome.errors.append((str(rel), f"{type(exc).__name__}: {exc}"))

    _copy_non_markdown_assets(content_dir, output_dir)
    _copy_static_assets(config, output_dir)
    outcome.examples = _pre_render_examples(output_dir)

    outcome.elapsed = time.monotonic() - start
    return outcome


def _citry_version() -> str:
    """The installed citry version (shown in the footer), or ``""`` if unknown."""
    try:
        return get_version("citry")
    except PackageNotFoundError:
        return ""


def _is_unsafe_output(output_dir: Path, content_dir: Path, config: DocsConfig) -> bool:
    """The output dir is cleared, so refuse the repo root, content dir, or a filesystem root."""
    resolved = output_dir.resolve()
    unsafe = {config.repo_root.resolve(), content_dir.resolve(), Path(resolved.anchor)}
    return resolved in unsafe


def _copy_non_markdown_assets(content_dir: Path, output_dir: Path) -> None:
    """Copy images and other non-``.md`` content files into the output tree verbatim."""
    for asset in content_dir.rglob("*"):
        if asset.is_dir() or asset.suffix == ".md" or asset.name == "_nav.yml":
            continue
        dest = output_dir / asset.relative_to(content_dir)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset, dest)


def _copy_static_assets(config: DocsConfig, output_dir: Path) -> None:
    """Copy the site's static assets (CSS, JS, fonts, images) into ``<output>/static``."""
    static_dir = config.base_dir / "static"
    if static_dir.is_dir():
        shutil.copytree(static_dir, output_dir / "static", dirs_exist_ok=True)


def _pre_render_examples(output_dir: Path) -> int:
    """Render each example's standalone page to ``examples/<name>/index.html`` (the live-demo target)."""
    count = 0
    for name, info in get_example_registry().items():
        out_path = output_dir / "examples" / name / "index.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(str(info.page_cls()), encoding="utf-8")
        count += 1
    return count
