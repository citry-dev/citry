"""Strict Reference catalog loading and generated-page helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from docs_site._internal.config_loading import (
    DocsConfigError,
    load_yaml,
    require_keys,
    require_list,
    require_mapping,
    require_relative_posix_path,
    require_str,
    require_str_list,
)
from docs_site._internal.nav import NavItem

ReferenceKind = Literal["generated_python", "authored_api", "authored_builtins"]
_SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_BUILTIN_TAG_RE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
_INVENTORY_ROLES = frozenset({"js:data", "js:function", "py:obj", "std:label"})


@dataclass(frozen=True, slots=True)
class ReferenceEntry:
    """One linkable API name on an authored Reference page."""

    key: str
    anchor: str
    aliases: tuple[str, ...] = ()
    inventory_role: str = "std:label"


@dataclass(frozen=True, slots=True)
class Category:
    """One ordered page in the public Reference catalog."""

    kind: ReferenceKind
    slug: str
    title: str
    intro: str
    symbols: tuple[str, ...] = ()
    source_path: PurePosixPath | None = None
    entries: tuple[ReferenceEntry, ...] = ()

    @property
    def source(self) -> str:
        """Compatibility label used by the reference rendering machinery."""
        return {
            "generated_python": "griffe",
            "authored_api": "authored",
            "authored_builtins": "builtin",
        }[self.kind]

    @property
    def authored(self) -> bool:
        return self.kind != "generated_python"


@dataclass(frozen=True, slots=True)
class ReferenceCatalog:
    categories: tuple[Category, ...]
    description_overrides: tuple[tuple[str, str], ...] = ()

    def category(self, slug: str) -> Category | None:
        return next((item for item in self.categories if item.slug == slug), None)

    def description_override(self, symbol: str) -> str | None:
        return dict(self.description_overrides).get(symbol)


def load_reference_catalog(path: Path) -> ReferenceCatalog:
    """Load the ordered Reference catalog, rejecting ambiguity and unsafe paths."""
    root = require_mapping(load_yaml(path), str(path))
    require_keys(root, str(path), required={"categories"}, optional={"description_overrides"})
    raw_categories = require_list(root["categories"], "reference.categories")
    if not raw_categories:
        raise DocsConfigError("reference.categories must not be empty")

    categories: list[Category] = []
    slugs: set[str] = set()
    symbols: set[str] = set()
    crossref_keys: set[str] = set()
    for index, raw in enumerate(raw_categories):
        label = f"reference.categories[{index}]"
        item = require_mapping(raw, label)
        kind = require_str(item.get("kind"), f"{label}.kind")
        if kind not in {"generated_python", "authored_api", "authored_builtins"}:
            raise DocsConfigError(f"{label}.kind has unknown variant {kind!r}")
        slug = require_str(item.get("slug"), f"{label}.slug")
        if not _SLUG_RE.fullmatch(slug):
            raise DocsConfigError(f"{label}.slug must be a lowercase kebab-case URL segment")
        if slug in slugs:
            raise DocsConfigError(f"reference catalog contains duplicate slug {slug!r}")
        slugs.add(slug)

        common = {"kind", "slug", "title", "intro"}
        title = require_str(item.get("title"), f"{label}.title")
        intro = require_str(item.get("intro"), f"{label}.intro")
        if kind == "generated_python":
            require_keys(item, label, required=common | {"symbols"})
            category_symbols = require_str_list(item["symbols"], f"{label}.symbols")
            if not category_symbols:
                raise DocsConfigError(f"{label}.symbols must not be empty")
            duplicate_symbols = symbols.intersection(category_symbols)
            if duplicate_symbols:
                raise DocsConfigError(
                    f"reference Python symbols occur on multiple pages: {', '.join(sorted(duplicate_symbols))}"
                )
            symbols.update(category_symbols)
            categories.append(Category(kind, slug, title, intro, symbols=category_symbols))
            continue

        if kind == "authored_api":
            require_keys(item, label, required=common | {"source", "entries"})
            source_path = _authored_source(item["source"], f"{label}.source", slug)
            entries = tuple(
                _load_entry(raw_entry, f"{label}.entries[{entry_index}]")
                for entry_index, raw_entry in enumerate(require_list(item["entries"], f"{label}.entries"))
            )
            if not entries:
                raise DocsConfigError(f"{label}.entries must not be empty")
            _claim_entry_keys(entries, crossref_keys, label)
            categories.append(Category(kind, slug, title, intro, source_path=source_path, entries=entries))
            continue

        require_keys(item, label, required=common | {"source", "tags"})
        source_path = _authored_source(item["source"], f"{label}.source", slug)
        tags = require_str_list(item["tags"], f"{label}.tags")
        if not tags:
            raise DocsConfigError(f"{label}.tags must not be empty")
        for tag_index, tag in enumerate(tags):
            if not _BUILTIN_TAG_RE.fullmatch(tag):
                raise DocsConfigError(f"{label}.tags[{tag_index}] must be lowercase kebab-case")
        entries = tuple(
            ReferenceEntry(
                key=f"c-{tag}",
                anchor=f"c-{tag}",
                aliases=(tag,),
                inventory_role="py:obj",
            )
            for tag in tags
        )
        _claim_entry_keys(entries, crossref_keys, label)
        categories.append(Category(kind, slug, title, intro, symbols=tags, source_path=source_path, entries=entries))

    _validate_static_crossref_keys(categories)

    raw_overrides = require_mapping(root.get("description_overrides", {}), "reference.description_overrides")
    unknown_overrides = set(raw_overrides) - symbols
    if unknown_overrides:
        raise DocsConfigError(
            "reference.description_overrides names undocumented symbol(s): " + ", ".join(sorted(unknown_overrides))
        )
    overrides = tuple(
        (symbol, require_str(text, f"reference.description_overrides.{symbol}"))
        for symbol, text in raw_overrides.items()
    )
    return ReferenceCatalog(categories=tuple(categories), description_overrides=overrides)


def validate_authored_reference_sources(catalog: ReferenceCatalog, content_dir: Path) -> None:
    """Require every authored catalog page before a command can clear output."""
    for category in catalog.categories:
        if category.source_path is None:
            continue
        source = content_dir.joinpath(*category.source_path.parts)
        if not source.is_file():
            raise DocsConfigError(f"authored Reference source does not exist: {category.source_path}")


def _authored_source(value: Any, label: str, slug: str) -> PurePosixPath:
    path = require_relative_posix_path(value, label, suffix=".md")
    expected = PurePosixPath("reference") / f"{slug}.md"
    if path != expected:
        raise DocsConfigError(f"{label} must be {expected.as_posix()!r} for this public slug")
    return path


def _load_entry(value: Any, label: str) -> ReferenceEntry:
    item = require_mapping(value, label)
    require_keys(item, label, required={"key", "anchor", "role"}, optional={"aliases"})
    anchor = require_str(item["anchor"], f"{label}.anchor")
    if not _SLUG_RE.fullmatch(anchor):
        raise DocsConfigError(f"{label}.anchor must be lowercase kebab-case")
    role = require_str(item["role"], f"{label}.role")
    if role not in _INVENTORY_ROLES:
        supported = ", ".join(sorted(_INVENTORY_ROLES))
        raise DocsConfigError(f"{label}.role must be one of: {supported}")
    key = _inventory_key(item["key"], f"{label}.key")
    aliases = tuple(
        _inventory_key(alias, f"{label}.aliases[{index}]")
        for index, alias in enumerate(require_str_list(item.get("aliases", []), f"{label}.aliases"))
    )
    return ReferenceEntry(
        key=key,
        anchor=anchor,
        aliases=aliases,
        inventory_role=role,
    )


def _inventory_key(value: Any, label: str) -> str:
    key = require_str(value, label)
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in key):
        raise DocsConfigError(f"{label} must be a single-line inventory key without whitespace")
    return key


def _claim_entry_keys(entries: tuple[ReferenceEntry, ...], claimed: set[str], label: str) -> None:
    anchors: set[str] = set()
    for entry in entries:
        if entry.anchor in anchors:
            raise DocsConfigError(f"{label} contains duplicate anchor {entry.anchor!r}")
        anchors.add(entry.anchor)
        keys = {entry.key, *entry.aliases}
        if len(keys) != 1 + len(entry.aliases):
            raise DocsConfigError(f"{label} entry {entry.key!r} repeats its key as an alias")
        collisions = keys.intersection(claimed)
        if collisions:
            raise DocsConfigError(f"reference authored keys collide: {', '.join(sorted(collisions))}")
        claimed.update(keys)


def _validate_static_crossref_keys(categories: list[Category]) -> None:
    """Reject authored keys that could steal a generated symbol key."""
    generated: set[str] = set()
    authored: set[str] = set()
    for category in categories:
        if category.kind == "generated_python":
            for path in category.symbols:
                generated.update((path, path.rsplit(".", 1)[-1]))
            continue
        for entry in category.entries:
            authored.update((entry.key, *entry.aliases))
    _reject_surface_collisions(generated, authored)


def validate_reference_crossref_keys(catalog: ReferenceCatalog) -> None:
    """Reject collisions with public class-member keys after API introspection."""
    from docs_site._internal.reference import is_external_alias, resolve_symbol  # noqa: PLC0415

    generated: set[str] = set()
    authored: set[str] = set()
    for category in catalog.categories:
        if category.kind == "generated_python":
            for path in category.symbols:
                generated.update((path, path.rsplit(".", 1)[-1]))
        else:
            for entry in category.entries:
                authored.update((entry.key, *entry.aliases))

    for category in catalog.categories:
        if category.kind != "generated_python":
            continue
        for path in category.symbols:
            obj = resolve_symbol(path)
            if obj is None:
                raise DocsConfigError(f"reference generated Python symbol does not resolve: {path}")
            if getattr(obj, "kind", None) is None or obj.kind.value != "class" or is_external_alias(obj):
                continue
            leaf = path.rsplit(".", 1)[-1]
            for member_name, member in obj.members.items():
                if member_name.startswith("_") or member.kind.value not in {"attribute", "function"}:
                    continue
                owner = f"{path}.{member_name}"
                generated.update((f"{leaf}.{member_name}", owner))
    _reject_surface_collisions(generated, authored)


def _reject_surface_collisions(generated: set[str], authored: set[str]) -> None:
    collisions = generated.intersection(authored)
    if collisions:
        raise DocsConfigError(
            "reference authored keys collide with generated Python keys: " + ", ".join(sorted(collisions))
        )


def reference_page_markdown(cat: Category) -> str:
    """Markdown for one generated Python category page."""
    if cat.authored:
        source = cat.source_path.as_posix() if cat.source_path is not None else f"reference/{cat.slug}.md"
        raise ValueError(f"Reference category {cat.slug!r} is authored in content/{source}")
    lines = [f"# {cat.title}", "", cat.intro, ""]
    for symbol in cat.symbols:
        lines.extend((f'<c-docstring path="{symbol}" />', ""))
    return "\n".join(lines) + "\n"


def reference_index_markdown(catalog: ReferenceCatalog | None = None) -> str:
    """Markdown for the ``/reference/`` landing page."""
    catalog = catalog or _current_catalog()
    lines = ["# API reference", "", "The citry public API, by area.", ""]
    lines.extend(f"- [{cat.title}](/reference/{cat.slug}/) - {cat.intro}" for cat in catalog.categories)
    return "\n".join(lines) + "\n"


def reference_nav_items(catalog: ReferenceCatalog | None = None) -> list[NavItem]:
    """The pages supplied by ``source: reference`` in navigation."""
    catalog = catalog or _current_catalog()
    items = [NavItem(title="Overview", path="/reference/", needs_review=True)]
    items.extend(
        NavItem(title=cat.title, path=f"/reference/{cat.slug}/", needs_review=True) for cat in catalog.categories
    )
    return items


def category(slug: str) -> Category | None:
    """Look up a category in the active manifest-backed project."""
    return _current_catalog().category(slug)


def _current_catalog() -> ReferenceCatalog:
    # Local import avoids a cycle while project.py is assembling the catalog.
    from docs_site._internal.project import current_docs_project  # noqa: PLC0415

    return current_docs_project().reference
