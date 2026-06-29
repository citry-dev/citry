"""
Load the navigation tree from ``_nav.yml``.

Produces a typed tree the page chrome consumes: the sidebar, breadcrumbs, and
prev/next links. A section has EITHER a ``path`` (a standalone link), ``items``
(one level), OR ``groups`` (two levels). Ported from the upstream docs site.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class NavItem:
    title: str
    path: str
    active: bool = False


@dataclass
class NavGroup:
    label: str
    items: list[NavItem] = field(default_factory=list)
    expanded: bool = False


@dataclass
class NavSection:
    label: str
    path: str = ""
    items: list[NavItem] = field(default_factory=list)
    groups: list[NavGroup] = field(default_factory=list)


@dataclass
class NavTree:
    sections: list[NavSection] = field(default_factory=list)

    def flat_pages(self) -> list[NavItem]:
        """All nav items in document order (used for prev/next navigation)."""
        pages: list[NavItem] = []
        for section in self.sections:
            if section.path:
                pages.append(NavItem(title=section.label, path=section.path))
            pages.extend(section.items)
            for group in section.groups:
                pages.extend(group.items)
        return pages

    def find_breadcrumbs(self, current_path: str) -> list[tuple[str, str]]:
        """
        Breadcrumb trail for ``current_path`` as ``(label, path)`` pairs.

        The last entry is the current page, with ``path=""`` to mark it as the
        non-link tail.
        """
        normalized = current_path.strip("/")

        for section in self.sections:
            if section.path and section.path.strip("/") == normalized:
                return [(section.label, "")]

            for item in section.items:
                if item.path.strip("/") == normalized:
                    return [(section.label, section.path or ""), (item.title, "")]

            for group in section.groups:
                for item in group.items:
                    if item.path.strip("/") == normalized:
                        return [
                            (section.label, section.path or ""),
                            (group.label, ""),
                            (item.title, ""),
                        ]
        return []

    def find_title(self, current_path: str) -> str:
        """The nav title for a path, or ``""`` if the page is not in the nav."""
        normalized = current_path.strip("/")
        for section in self.sections:
            if section.path and section.path.strip("/") == normalized:
                return section.label
            for item in section.items:
                if item.path.strip("/") == normalized:
                    return item.title
            for group in section.groups:
                for item in group.items:
                    if item.path.strip("/") == normalized:
                        return item.title
        return ""

    def find_prev_next(self, current_path: str) -> tuple[NavItem | None, NavItem | None]:
        """The ``(prev, next)`` nav items around ``current_path``."""
        pages = self.flat_pages()
        normalized = current_path.strip("/")

        for i, page in enumerate(pages):
            if page.path.strip("/") == normalized:
                prev_item = pages[i - 1] if i > 0 else None
                next_item = pages[i + 1] if i < len(pages) - 1 else None
                return prev_item, next_item
        return None, None

    def set_active(self, current_path: str) -> None:
        """Mark the active item and expand the group that contains it."""
        normalized = current_path.strip("/")

        for section in self.sections:
            for item in section.items:
                item.active = item.path.strip("/") == normalized

            for group in section.groups:
                group_has_active = False
                for item in group.items:
                    item.active = item.path.strip("/") == normalized
                    group_has_active = group_has_active or item.active
                group.expanded = group_has_active


def load_nav(nav_path: Path) -> NavTree:
    """Load and validate a ``_nav.yml`` file into a :class:`NavTree`."""
    if not nav_path.is_file():
        return NavTree()

    with nav_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if not raw or "sections" not in raw:
        return NavTree()

    return NavTree(sections=[_parse_section(section) for section in raw["sections"]])


def _parse_section(raw: dict) -> NavSection:
    label = raw.get("label", "")

    if "items" in raw and "groups" in raw:
        msg = f"Nav section {label!r} has both 'items' and 'groups'; pick one"
        raise ValueError(msg)

    items = [NavItem(title=i["title"], path=i["path"]) for i in raw.get("items", [])]
    groups = [
        NavGroup(
            label=group["label"],
            items=[NavItem(title=i["title"], path=i["path"]) for i in group.get("items", [])],
        )
        for group in raw.get("groups", [])
    ]
    return NavSection(label=label, path=raw.get("path", ""), items=items, groups=groups)
