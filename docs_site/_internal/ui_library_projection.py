"""Strict Citry UI catalog loading and public-route projection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from docs_site._internal.config_loading import (
    DocsConfigError,
    load_yaml,
    require_keys,
    require_list,
    require_mapping,
    require_relative_posix_path,
    require_str,
)
from docs_site._internal.frontmatter import parse_page
from docs_site._internal.nav import NavItem
from docs_site._internal.ui_library_reference import compose_ui_library_source

if TYPE_CHECKING:
    from pathlib import Path, PurePosixPath

_SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


@dataclass(frozen=True, slots=True)
class UiLibraryProjection:
    """One component-owned source and its public docs route."""

    family: str
    slug: str
    source: PurePosixPath
    nav_title: str = ""

    @property
    def public_path(self) -> str:
        return f"/ui-library/components/{self.slug}/"


@dataclass(frozen=True, slots=True)
class UiLibraryCatalog:
    projections: tuple[UiLibraryProjection, ...]


def load_ui_library_catalog(path: Path) -> UiLibraryCatalog:
    """Load the ordered Citry UI catalog and reject ambiguous projections."""
    root = require_mapping(load_yaml(path), str(path))
    require_keys(root, str(path), required={"components"})
    raw_items = require_list(root["components"], "ui_library.components")
    if not raw_items:
        raise DocsConfigError("ui_library.components must not be empty")

    projections: list[UiLibraryProjection] = []
    families: set[str] = set()
    slugs: set[str] = set()
    sources: set[PurePosixPath] = set()
    for index, raw in enumerate(raw_items):
        label = f"ui_library.components[{index}]"
        item = require_mapping(raw, label)
        require_keys(
            item,
            label,
            required={"family", "slug", "source"},
            optional={"nav_title"},
        )
        family = require_str(item["family"], f"{label}.family")
        slug = require_str(item["slug"], f"{label}.slug")
        if not _SLUG_RE.fullmatch(family) or not _SLUG_RE.fullmatch(slug):
            raise DocsConfigError(f"{label}.family and .slug must be lowercase kebab-case")
        source = require_relative_posix_path(item["source"], f"{label}.source", suffix=".md")
        if family in families:
            raise DocsConfigError(f"ui_library catalog contains duplicate family {family!r}")
        if slug in slugs:
            raise DocsConfigError(f"ui_library catalog contains duplicate slug {slug!r}")
        if source in sources:
            raise DocsConfigError(f"ui_library catalog contains duplicate source {source.as_posix()!r}")
        families.add(family)
        slugs.add(slug)
        sources.add(source)
        projections.append(
            UiLibraryProjection(
                family=family,
                slug=slug,
                source=source,
                nav_title=require_str(item.get("nav_title", ""), f"{label}.nav_title", allow_empty=True),
            )
        )
    return UiLibraryCatalog(projections=tuple(projections))


def ui_library_source_path(
    projection: UiLibraryProjection,
    *,
    repo_root: Path,
) -> Path:
    """Resolve one catalog source without allowing it to escape the repository."""
    source = repo_root.joinpath(*projection.source.parts)
    if not source.resolve().is_relative_to(repo_root.resolve()):
        raise DocsConfigError(f"Citry UI source escapes the repository: {projection.source}")
    return source


def ui_library_source_routes(
    catalog: UiLibraryCatalog,
    *,
    repo_root: Path,
) -> dict[Path, str]:
    """Map authoritative source paths to their clean public routes."""
    return {
        ui_library_source_path(projection, repo_root=repo_root).resolve(): projection.public_path
        for projection in catalog.projections
    }


def ui_library_projection_for_path(
    catalog: UiLibraryCatalog,
    public_path: str,
) -> UiLibraryProjection | None:
    """Return the catalog entry for one clean public route."""
    clean = f"/{public_path.strip('/')}/"
    return next((projection for projection in catalog.projections if projection.public_path == clean), None)


def validate_ui_library_sources(
    catalog: UiLibraryCatalog,
    *,
    repo_root: Path,
) -> None:
    """Validate every source and its required front matter before a build."""
    for projection in catalog.projections:
        source = ui_library_source_path(projection, repo_root=repo_root)
        if not source.is_file():
            raise FileNotFoundError(f"Citry UI API source does not exist: {projection.source}")
        meta = parse_page(source.read_text(encoding="utf-8"))
        if not meta.title or not meta.description:
            raise DocsConfigError(f"Citry UI source needs title and description front matter: {projection.source}")
        compose_ui_library_source(source, family=projection.family)


def ui_library_nav_items(
    catalog: UiLibraryCatalog,
    *,
    repo_root: Path,
) -> list[NavItem]:
    """Build sidebar items from catalog order and source front matter."""
    items: list[NavItem] = []
    for projection in catalog.projections:
        source = ui_library_source_path(projection, repo_root=repo_root)
        if not source.is_file():
            raise FileNotFoundError(f"Citry UI API source does not exist: {projection.source}")
        meta = parse_page(source.read_text(encoding="utf-8"))
        title = projection.nav_title or meta.title
        if not title:
            raise DocsConfigError(f"Citry UI source needs title front matter: {projection.source}")
        items.append(NavItem(title=title, path=projection.public_path, needs_review=True))
    return items


def ui_library_overview_items(
    catalog: UiLibraryCatalog,
    *,
    repo_root: Path,
) -> list[dict[str, str]]:
    """Build overview link data from the same source front matter as navigation."""
    result: list[dict[str, str]] = []
    for projection in catalog.projections:
        source = ui_library_source_path(projection, repo_root=repo_root)
        meta = parse_page(source.read_text(encoding="utf-8"))
        result.append(
            {
                "title": projection.nav_title or meta.title,
                "description": meta.description,
                "path": projection.public_path,
            }
        )
    return result
