"""
Load and query the primary-area tree from ``_nav.yml``.

The YAML hierarchy is the site hierarchy: every top-level area becomes a
header link, while its direct items and groups become that area's sidebar.
Generated navigation is declared in place with a ``source`` and hydrated by
the site loader, so Python code never promotes or reorders primary areas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


_AREA_SOURCES = frozenset({"blog", "reference"})
_GROUP_SOURCES = frozenset({"releases"})
_AREA_KEYS = frozenset({"label", "items", "groups", "source", "scope", "entry", "badge"})
_GROUP_KEYS = frozenset({"label", "items", "source", "scope", "entry", "collapsible", "section_style"})
_ITEM_KEYS = frozenset({"title", "path", "scope", "needs_review"})
_HOME_REQUIRED_KEYS = frozenset({"title", "path", "scope"})
SCOPE_VERSIONED = "versioned"
SCOPE_SITE = "site"
CONTENT_SCOPES = frozenset({SCOPE_SITE, SCOPE_VERSIONED})
_SOURCE_SCOPES = {"blog": SCOPE_SITE}


@dataclass
class NavItem:
    title: str
    path: str
    active: bool = False
    # Review state is presentation metadata, not part of the title. Keeping the
    # title clean preserves Overview detection, breadcrumbs, and page cards.
    needs_review: bool = False
    # Generated Blog entries carry an authored publication date. Ordinary
    # navigation items leave these empty and render exactly as before.
    date_iso: str = ""
    date_label: str = ""
    # Content scope is inherited from the owning group/area while parsing.
    # ``versioned`` is the compatibility default for programmatic/test items.
    scope: str = SCOPE_VERSIONED


@dataclass
class NavGroup:
    label: str
    items: list[NavItem] = field(default_factory=list)
    source: str = ""
    collapsible: bool = False
    section_style: bool = False
    expanded: bool = False
    scope: str = SCOPE_VERSIONED
    source_entry: NavItem | None = None

    @property
    def overview_path(self) -> str:
        """The explicit Overview item's path, when the group has one."""
        for item in self.items:
            if item.title.casefold() == "overview":
                return item.path
        return ""


@dataclass
class NavArea:
    label: str
    items: list[NavItem] = field(default_factory=list)
    groups: list[NavGroup] = field(default_factory=list)
    source: str = ""
    scope: str = SCOPE_VERSIONED
    badge: str = ""
    # A generated site-scoped area declares its stable root entry so snapshot
    # builds can keep the top-nav escape link without loading current content.
    source_entry: NavItem | None = None

    def flat_pages(self) -> list[NavItem]:
        """Every page in this area, in sidebar order."""
        pages = list(self.items)
        for group in self.groups:
            pages.extend(group.items)
        return pages

    @property
    def entry_path(self) -> str:
        """The page opened by this area's primary-navigation link."""
        pages = self.flat_pages()
        if pages:
            return pages[0].path
        return self.source_entry.path if self.source_entry is not None else ""

    @property
    def entry_item(self) -> NavItem | None:
        """The item represented by this area's primary-navigation link."""
        pages = self.flat_pages()
        if pages:
            return pages[0]
        return self.source_entry

    def contains(self, current_path: str) -> bool:
        """Whether ``current_path`` belongs to this area."""
        normalized = _norm(current_path)
        return any(_norm(item.path) == normalized for item in self.flat_pages())


@dataclass
class NavTree:
    # The project home is a route declaration, not a visible primary area.
    # Repositories without it retain the historical area-owned root behavior.
    home: NavItem | None = None
    areas: list[NavArea] = field(default_factory=list)

    def flat_pages(self) -> list[NavItem]:
        """All nav items in site order."""
        pages: list[NavItem] = []
        for area in self.areas:
            pages.extend(area.flat_pages())
        return pages

    def find_area(self, current_path: str) -> NavArea | None:
        """The primary area that owns ``current_path``."""
        for area in self.areas:
            if area.contains(current_path):
                return area
        return None

    def find_breadcrumbs(self, current_path: str) -> list[tuple[str, str]]:
        """Return the area/group/page trail for ``current_path``."""
        normalized = _norm(current_path)

        for area in self.areas:
            area_link = area.entry_path
            if _norm(area_link) == normalized:
                area_link = ""

            for item in area.items:
                if _norm(item.path) != normalized:
                    continue
                if not normalized:
                    return [(item.title, "")]
                if item.title.casefold() in {"all posts", "overview"}:
                    return [(area.label, "")]
                return [(area.label, area_link), (item.title, "")]

            for group in area.groups:
                for item in group.items:
                    if _norm(item.path) != normalized:
                        continue
                    area_crumb = (area.label, area_link)
                    if item.title.casefold() == "overview":
                        return [area_crumb, (group.label, "")]
                    return [
                        area_crumb,
                        (group.label, group.overview_path),
                        (item.title, ""),
                    ]
        return []

    def find_title(self, current_path: str) -> str:
        """The nav title for a path, or ``""`` when it is absent."""
        normalized = _norm(current_path)
        for item in self._route_items():
            if _norm(item.path) == normalized:
                return item.title
        return ""

    def scope_for_path(self, current_path: str) -> str:
        """Return a page's resolved content scope, defaulting to versioned."""
        normalized = _norm(current_path)
        for item in self._route_items():
            if _norm(item.path) == normalized:
                return item.scope
        return SCOPE_VERSIONED

    def scope_for_url(self, path: str) -> str:
        """Resolve a page or asset URL to its declared content scope."""
        normalized = _norm(path)
        route_items = self._route_items()
        for item in route_items:
            if _norm(item.path) == normalized:
                return item.scope

        namespace = _first_path_segment(path)
        if not namespace:
            return SCOPE_VERSIONED
        scopes = {item.scope for item in route_items if _first_path_segment(item.path) == namespace}
        if len(scopes) == 1:
            return scopes.pop()
        return SCOPE_VERSIONED

    def _route_items(self) -> list[NavItem]:
        items = self.flat_pages()
        if self.home is not None:
            items.append(self.home)
        items.extend(area.source_entry for area in self.areas if area.source_entry is not None)
        items.extend(
            group.source_entry for area in self.areas for group in area.groups if group.source_entry is not None
        )
        return items

    def project_path(self, path: str, version_prefix: str = "") -> str:
        """Project a logical root path into a version snapshot when required."""
        if not path or not version_prefix or self.scope_for_url(path) == SCOPE_SITE:
            return path
        return f"/{version_prefix.strip('/')}/{path.lstrip('/')}"

    def site_route_patterns(self) -> tuple[str, ...]:
        """Return stable exact/wildcard patterns for this build's site routes."""
        items = self._route_items()
        patterns = {item.path for item in items if item.scope == SCOPE_SITE}
        namespaces = {_first_path_segment(item.path) for item in items if _first_path_segment(item.path)}
        for namespace in namespaces:
            scopes = {item.scope for item in items if _first_path_segment(item.path) == namespace}
            if scopes == {SCOPE_SITE}:
                patterns.add(f"/{namespace}/*")
        return tuple(sorted(patterns))

    def scope_for_source(self, source: str) -> str:
        """Return the scope inherited by a generated navigation source."""
        for area in self.areas:
            if area.source == source:
                return area.scope
            for group in area.groups:
                if group.source == source:
                    return group.scope
        return SCOPE_VERSIONED

    def has_source(self, source: str) -> bool:
        """Return whether an area or group declares ``source``."""
        return any(
            area.source == source or any(group.source == source for group in area.groups) for area in self.areas
        )

    def fallback_items_for_source(self, source: str) -> list[NavItem] | None:
        """Return a generated owner's declared root item for a root-site escape."""
        for area in self.areas:
            if area.source == source:
                return [area.source_entry] if area.source_entry is not None else None
            for group in area.groups:
                if group.source == source:
                    return [group.source_entry] if group.source_entry is not None else None
        return None

    def scope_for_content_asset(self, relative_path: Path) -> str:
        """
        Resolve a content asset from its route namespace.

        Assets next to pages inherit the unanimous scope of that first URL
        segment. Unknown or mixed namespaces stay versioned, which preserves
        existing output instead of accidentally dropping a required asset.
        Site-global assets belong under ``static/`` and are shared by snapshots.
        """
        if not relative_path.parts:
            return SCOPE_VERSIONED
        return self.scope_for_url("/" + relative_path.as_posix())

    def find_prev_next(
        self,
        current_path: str,
    ) -> tuple[NavItem | None, NavItem | None]:
        """The adjacent pages within the current primary area."""
        area = self.find_area(current_path)
        if area is None:
            return None, None

        pages = area.flat_pages()
        normalized = _norm(current_path)
        for index, page in enumerate(pages):
            if _norm(page.path) != normalized:
                continue
            previous = pages[index - 1] if index > 0 else None
            following = pages[index + 1] if index + 1 < len(pages) else None
            return previous, following
        return None, None

    def set_active(self, current_path: str) -> None:
        """Mark the active page and expand the group that contains it."""
        normalized = _norm(current_path)

        for area in self.areas:
            for item in area.items:
                item.active = _norm(item.path) == normalized

            for group in area.groups:
                group.expanded = False
                for item in group.items:
                    item.active = _norm(item.path) == normalized
                    group.expanded = group.expanded or item.active


def load_nav(nav_path: Path) -> NavTree:
    """Load and validate an authored ``_nav.yml`` area tree."""
    if not nav_path.is_file():
        return NavTree()

    with nav_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if not isinstance(raw, dict) or "areas" not in raw:
        raise ValueError("Navigation file must define a top-level 'areas' list")
    unknown = set(raw) - {"home", "areas"}
    if unknown:
        names = ", ".join(sorted(str(key) for key in unknown))
        raise ValueError(f"Navigation file has unknown top-level key(s): {names}")
    if not isinstance(raw["areas"], list):
        raise TypeError("Navigation 'areas' must be a list")
    if not raw["areas"]:
        raise ValueError("Navigation 'areas' must contain at least one area")

    home = _parse_home(raw["home"]) if "home" in raw else None
    tree = NavTree(home=home, areas=[_parse_area(area) for area in raw["areas"]])
    _validate_tree(tree, allow_unresolved=True)
    return tree


def resolve_nav_sources(
    tree: NavTree,
    sources: Mapping[str, list[NavItem] | None],
) -> NavTree:
    """Hydrate declared generated sources without changing YAML ordering."""
    for area in tree.areas:
        if area.source:
            area.items = _with_scope(_resolve_source(area.source, sources), area.scope)
            _validate_source_entry(area.source, area.items, area.source_entry)

        groups: list[NavGroup] = []
        for group in area.groups:
            if group.source:
                items = sources.get(group.source)
                if items is None:
                    continue
                group.items = _with_scope(items, group.scope)
                _validate_source_entry(group.source, group.items, group.source_entry)
            groups.append(group)
        area.groups = groups

    _validate_tree(tree, allow_unresolved=False)
    return tree


def _resolve_source(
    source: str,
    sources: Mapping[str, list[NavItem] | None],
) -> list[NavItem]:
    if source not in sources or sources[source] is None:
        msg = f"Navigation source {source!r} did not produce any pages"
        raise ValueError(msg)
    return list(sources[source] or [])


def _validate_source_entry(source: str, items: list[NavItem], entry: NavItem | None) -> None:
    if entry is None or not items:
        return
    first = items[0]
    if first.title == entry.title and _norm(first.path) == _norm(entry.path):
        return
    msg = (
        f"Navigation source {source!r} starts at {first.title!r} ({first.path}), "
        f"not its declared entry {entry.title!r} ({entry.path})"
    )
    raise ValueError(msg)


def _parse_area(raw: dict) -> NavArea:
    _reject_unknown_keys(raw, _AREA_KEYS, owner="Navigation area")
    label = raw.get("label", "")
    source = raw.get("source", "")
    badge = raw.get("badge", "")
    if not isinstance(badge, str) or ("badge" in raw and not badge.strip()):
        raise ValueError(f"Nav area {label!r} badge must be a non-empty string")
    scope = _parse_scope(raw.get("scope", SCOPE_VERSIONED), owner=f"Nav area {label!r}")
    if source not in _AREA_SOURCES | {""}:
        msg = f"Unknown navigation area source {source!r}"
        raise ValueError(msg)
    if source in _SOURCE_SCOPES and scope != _SOURCE_SCOPES[source]:
        msg = f"Navigation source {source!r} must use scope {_SOURCE_SCOPES[source]!r}"
        raise ValueError(msg)
    if source and (raw.get("items") or raw.get("groups")):
        msg = f"Nav area {label!r} has a source and authored children"
        raise ValueError(msg)
    if raw.get("entry") and not source:
        msg = f"Nav area {label!r} has an entry without a source"
        raise ValueError(msg)

    items = [_parse_item(item, inherited_scope=scope) for item in raw.get("items", [])]
    groups = [_parse_group(group, inherited_scope=scope) for group in raw.get("groups", [])]
    source_entry = _parse_item(raw["entry"], inherited_scope=scope) if raw.get("entry") else None
    if source and scope == SCOPE_SITE and source_entry is None:
        msg = f"Site-scoped generated nav area {label!r} must declare an entry"
        raise ValueError(msg)
    return NavArea(
        label=label,
        items=items,
        groups=groups,
        source=source,
        scope=scope,
        badge=badge.strip(),
        source_entry=source_entry,
    )


def _parse_home(raw: dict) -> NavItem:
    """Parse the optional project home, which never becomes a header area."""
    if not isinstance(raw, dict):
        raise TypeError("Navigation home must be a mapping")
    missing = _HOME_REQUIRED_KEYS - set(raw)
    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"Navigation home is missing required key(s): {names}")
    home = _parse_item(raw, inherited_scope=SCOPE_SITE)
    if home.path != "/":
        raise ValueError("Navigation home path must be '/'")
    if home.scope != SCOPE_SITE:
        raise ValueError("Navigation home must use scope 'site'")
    return home


def _parse_group(raw: dict, *, inherited_scope: str) -> NavGroup:
    _reject_unknown_keys(raw, _GROUP_KEYS, owner="Navigation group")
    label = raw.get("label", "")
    source = raw.get("source", "")
    scope = _parse_scope(raw.get("scope", inherited_scope), owner=f"Nav group {label!r}")
    collapsible = bool(raw.get("collapsible", False))
    section_style = bool(raw.get("section_style", False))
    if source not in _GROUP_SOURCES | {""}:
        msg = f"Unknown navigation group source {source!r}"
        raise ValueError(msg)
    if source and raw.get("items"):
        msg = f"Nav group {label!r} has a source and authored items"
        raise ValueError(msg)
    if raw.get("entry") and not source:
        msg = f"Nav group {label!r} has an entry without a source"
        raise ValueError(msg)
    if section_style and not collapsible:
        msg = f"Nav group {label!r} uses section_style without being collapsible"
        raise ValueError(msg)
    source_entry = _parse_item(raw["entry"], inherited_scope=scope) if raw.get("entry") else None
    if source and scope == SCOPE_SITE and source_entry is None:
        msg = f"Site-scoped generated nav group {label!r} must declare an entry"
        raise ValueError(msg)
    return NavGroup(
        label=label,
        items=[_parse_item(item, inherited_scope=scope) for item in raw.get("items", [])],
        source=source,
        collapsible=collapsible,
        section_style=section_style,
        scope=scope,
        source_entry=source_entry,
    )


def _parse_item(raw: dict, *, inherited_scope: str) -> NavItem:
    _reject_unknown_keys(raw, _ITEM_KEYS, owner="Navigation item")
    title = raw["title"]
    path = raw["path"]
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Navigation item titles may not be empty")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Navigation item paths may not be empty")
    if "🚧" in title:
        raise ValueError("Navigation item titles must use needs_review: true instead of the 🚧 marker")
    if not path.startswith("/") or not path.endswith("/"):
        msg = f"Navigation path {path!r} must start and end with '/'"
        raise ValueError(msg)
    needs_review = raw.get("needs_review", False)
    if not isinstance(needs_review, bool):
        raise TypeError(f"Nav item {title!r} needs_review must be true or false")
    scope = _parse_scope(raw.get("scope", inherited_scope), owner=f"Nav item {title!r}")
    return NavItem(title=title, path=path, needs_review=needs_review, scope=scope)


def _parse_scope(raw: object, *, owner: str) -> str:
    if not isinstance(raw, str) or raw not in CONTENT_SCOPES:
        choices = ", ".join(sorted(CONTENT_SCOPES))
        msg = f"{owner} has invalid scope {raw!r}; expected one of: {choices}"
        raise ValueError(msg)
    return raw


def _with_scope(items: list[NavItem], scope: str) -> list[NavItem]:
    """Assign a generated source's inherited scope to all of its pages."""
    resolved = list(items)
    for item in resolved:
        item.scope = scope
    return resolved


def _reject_unknown_keys(raw: object, allowed: frozenset[str], *, owner: str) -> None:
    if not isinstance(raw, dict):
        raise TypeError(f"{owner} must be a mapping")
    unknown = set(raw) - allowed
    if unknown:
        names = ", ".join(sorted(str(key) for key in unknown))
        raise ValueError(f"{owner} has unknown key(s): {names}")


def _validate_tree(tree: NavTree, *, allow_unresolved: bool) -> None:
    area_labels: set[str] = set()
    source_owners: dict[str, str] = {}
    for area in tree.areas:
        if not area.label:
            raise ValueError("Navigation area labels may not be empty")
        if area.label in area_labels:
            msg = f"Duplicate navigation area label {area.label!r}"
            raise ValueError(msg)
        area_labels.add(area.label)
        if area.source:
            _claim_source(source_owners, area.source, area.label)

        group_labels: set[str] = set()
        for group in area.groups:
            if not group.label:
                raise ValueError("Navigation group labels may not be empty")
            if group.label in group_labels:
                msg = f"Duplicate navigation group label {group.label!r} in area {area.label!r}"
                raise ValueError(msg)
            group_labels.add(group.label)
            if group.source:
                _claim_source(
                    source_owners,
                    group.source,
                    f"{area.label} / {group.label}",
                )
            if not group.items and not (allow_unresolved and group.source):
                msg = f"Navigation group {group.label!r} has no pages"
                raise ValueError(msg)

        if not area.flat_pages() and not (
            allow_unresolved and (area.source or any(group.source for group in area.groups))
        ):
            msg = f"Navigation area {area.label!r} has no pages"
            raise ValueError(msg)

    owners: dict[str, str] = {}
    if tree.home is not None:
        owners[_norm(tree.home.path)] = "home"
    for area in tree.areas:
        for item in area.flat_pages():
            normalized = _norm(item.path)
            if normalized in owners:
                msg = f"Navigation path {item.path!r} belongs to both {owners[normalized]!r} and {area.label!r}"
                raise ValueError(msg)
            owners[normalized] = area.label


def _claim_source(
    owners: dict[str, str],
    source: str,
    owner: str,
) -> None:
    if source in owners:
        msg = f"Navigation source {source!r} is declared by both {owners[source]!r} and {owner!r}"
        raise ValueError(msg)
    owners[source] = owner


def _norm(path: str) -> str:
    return path.strip("/")


def _first_path_segment(path: str) -> str:
    normalized = _norm(path)
    return normalized.split("/", 1)[0] if normalized else ""
