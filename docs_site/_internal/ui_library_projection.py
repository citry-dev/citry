"""Strict Citry UI catalog loading and public-route projection."""

from __future__ import annotations

import re
import shutil
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
from docs_site._internal.nav import NavGroup, NavItem
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
class UiLibraryGroup:
    """One functional group in the component catalog."""

    id: str
    label: str
    projections: tuple[UiLibraryProjection, ...]


@dataclass(frozen=True, slots=True)
class UiLibraryCatalog:
    projections: tuple[UiLibraryProjection, ...]
    groups: tuple[UiLibraryGroup, ...] = ()


def load_ui_library_catalog(path: Path) -> UiLibraryCatalog:
    """Load the ordered Citry UI catalog and reject ambiguous projections."""
    root = require_mapping(load_yaml(path), str(path))
    require_keys(root, str(path), optional={"components", "groups"})
    if ("components" in root) == ("groups" in root):
        raise DocsConfigError("ui_library.yml must define exactly one of components or groups")

    raw_groups: list[tuple[str, str, list[object]]]
    if "groups" in root:
        values = require_list(root["groups"], "ui_library.groups")
        if not values:
            raise DocsConfigError("ui_library.groups must not be empty")
        raw_groups = []
        group_ids: set[str] = set()
        group_labels: set[str] = set()
        for group_index, raw_group in enumerate(values):
            group_label = f"ui_library.groups[{group_index}]"
            group = require_mapping(raw_group, group_label)
            require_keys(group, group_label, required={"id", "label", "components"})
            group_id = require_str(group["id"], f"{group_label}.id")
            label = require_str(group["label"], f"{group_label}.label")
            if not _SLUG_RE.fullmatch(group_id):
                raise DocsConfigError(f"{group_label}.id must be lowercase kebab-case")
            if group_id in group_ids:
                raise DocsConfigError(f"ui_library catalog contains duplicate group id {group_id!r}")
            if label in group_labels:
                raise DocsConfigError(f"ui_library catalog contains duplicate group label {label!r}")
            components = require_list(group["components"], f"{group_label}.components")
            if not components:
                raise DocsConfigError(f"{group_label}.components must not be empty")
            group_ids.add(group_id)
            group_labels.add(label)
            raw_groups.append((group_id, label, components))
    else:
        raw_items = require_list(root["components"], "ui_library.components")
        if not raw_items:
            raise DocsConfigError("ui_library.components must not be empty")
        raw_groups = [("components", "Components", raw_items)]

    projections: list[UiLibraryProjection] = []
    groups: list[UiLibraryGroup] = []
    families: set[str] = set()
    slugs: set[str] = set()
    sources: set[PurePosixPath] = set()
    for group_id, group_title, raw_items in raw_groups:
        group_projections: list[UiLibraryProjection] = []
        for index, raw in enumerate(raw_items):
            label = f"ui_library.groups[{group_id!r}].components[{index}]"
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
            projection = UiLibraryProjection(
                family=family,
                slug=slug,
                source=source,
                nav_title=require_str(item.get("nav_title", ""), f"{label}.nav_title", allow_empty=True),
            )
            projections.append(projection)
            group_projections.append(projection)
        groups.append(UiLibraryGroup(id=group_id, label=group_title, projections=tuple(group_projections)))
    return UiLibraryCatalog(projections=tuple(projections), groups=tuple(groups))


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


def copy_ui_library_api_sources(
    catalog: UiLibraryCatalog,
    *,
    repo_root: Path,
    output_dir: Path,
) -> int:
    """Publish each structured ``api.yml`` beside its rendered component guide."""
    copied = 0
    for projection in catalog.projections:
        source = ui_library_source_path(projection, repo_root=repo_root).with_suffix(".yml")
        if not source.is_file():
            raise FileNotFoundError(f"Citry UI API data does not exist: {source.relative_to(repo_root)}")
        target = output_dir.joinpath(*projection.public_path.strip("/").split("/"), "api.yml")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied += 1
    return copied


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


def ui_library_nav_groups(
    catalog: UiLibraryCatalog,
    *,
    repo_root: Path,
) -> list[NavGroup]:
    """Build functional sidebar groups from the catalog."""
    groups = catalog.groups or (UiLibraryGroup("components", "Components", catalog.projections),)
    return [
        NavGroup(
            label=group.label,
            items=[
                item
                for projection in group.projections
                for item in ui_library_nav_items(
                    UiLibraryCatalog((projection,)),
                    repo_root=repo_root,
                )
            ],
            collapsible=True,
            section_style=True,
        )
        for group in groups
    ]


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


def ui_library_overview_groups(
    catalog: UiLibraryCatalog,
    *,
    repo_root: Path,
) -> list[dict[str, object]]:
    """Build grouped overview data from the catalog and source front matter."""
    groups = catalog.groups or (UiLibraryGroup("components", "Components", catalog.projections),)
    return [
        {
            "id": group.id,
            "label": group.label,
            "items": ui_library_overview_items(
                UiLibraryCatalog(group.projections),
                repo_root=repo_root,
            ),
        }
        for group in groups
    ]
