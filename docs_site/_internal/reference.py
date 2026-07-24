"""
API reference: introspect the ``citry`` package with griffe and extract a
plain, render-ready structure for each public symbol.

This is the data layer. The ``ReferenceSymbol`` component
(``components/reference_symbol.py``) draws it, and the ``<c-docstring />``
directive resolves a dotted path to it. Only ``citry.*`` is documented (the
Rust ``citry_core`` plumbing is deliberately left out).
"""

from __future__ import annotations

import functools
import html
import importlib
import inspect
import re
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import griffe
import markdown
from markupsafe import Markup

from citry import citry as _default_citry
from citry.component_registry import NotRegistered
from docs_site._internal.annotation import render_annotation
from docs_site._internal.config import config
from docs_site._internal.crossrefs import make_type_resolver, resolve_crossrefs
from docs_site._internal.git_metadata import source_url_for

if TYPE_CHECKING:
    from collections.abc import Callable

# A small, self-contained markdown set for docstring prose (no snippet includes
# or repo-relative config, so it stays independent of the page pipeline).
_MD_EXTENSIONS = ["admonition", "attr_list", "def_list", "tables", "fenced_code"]
_ANCHOR_RE = re.compile(r"[^a-z0-9]+")

# Docstring sections that are rendered as their own structured fields, so the
# prose walk in _description skips them instead of repeating them.
_FIELD_SECTIONS = frozenset({"parameters", "returns", "raises", "attributes"})


@functools.cache
def _package() -> Any:
    """The griffe model of the citry package (loaded once)."""
    return griffe.load("citry", docstring_parser="google")


def resolve_symbol(dotted_path: str) -> Any | None:
    """Resolve ``citry.Component`` (or ``citry.Component.render``) to a griffe object."""
    parts = dotted_path.split(".")
    if not parts or parts[0] != "citry":
        return None
    obj: Any = _package()
    for part in parts[1:]:
        members = getattr(obj, "members", {})
        if part not in members:
            return None
        obj = members[part]
    return obj


def public_entrypoints() -> list[str]:
    """
    The dotted paths of citry's public import surfaces.

    The public API is three entrypoint shapes and nothing else: the root
    ``citry`` package, each ``citry.contrib.<name>`` module, and each
    ``citry.ext.<name>`` extension package (docs/design/events.md section
    3.4). Any deeper module is internal. The reference pages must cover
    everything these entrypoints export, which is what makes the API
    reference the enforcement of that rule; the docs-site test
    ``test_categories_cover_the_public_api`` checks it.
    """
    entrypoints = ["citry"]
    for namespace in ("citry.contrib", "citry.ext"):
        module = resolve_symbol(namespace)
        members = getattr(module, "members", {}) if module is not None else {}
        entrypoints.extend(
            f"{namespace}.{name}"
            for name, member in sorted(members.items())
            if member.kind.value == "module" and not name.startswith("_")
        )
    return entrypoints


def extract_symbol(dotted_path: str) -> SimpleNamespace | None:
    """Resolve and extract a symbol into a render-ready structure, or ``None``."""
    obj = resolve_symbol(dotted_path)
    return _extract(obj, dotted_path) if obj is not None else None


@functools.lru_cache(maxsize=1)
def reference_anchor_map() -> dict[str, str]:
    """
    The unique HTML anchor for every reference symbol and member, keyed by path.

    A reference page renders several top-level symbols, and Python names are
    case-sensitive while anchors are lowercased, so two of them (a ``Citry``
    class and the ``citry`` instance) can slugify to the same anchor. Anchors are
    assigned once here, deduped per category page (separate pages may reuse an
    anchor, one page may not): the first use keeps the base anchor and a later
    clash gets a numeric suffix. Both the rendered ids and the cross-reference
    links read from this map, so a symbol's anchor is the same in both places.
    """
    from docs_site._internal.reference_pages import CATEGORIES  # noqa: PLC0415 - lazy: avoids an import cycle

    mapping: dict[str, str] = {}
    for cat in CATEGORIES:
        if cat.source != "griffe":
            continue  # builtin tags are distinct and need no dedup
        seen: set[str] = set()
        for path in cat.symbols:
            obj = resolve_symbol(path)
            if obj is None:
                continue
            _assign_anchor(mapping, seen, path)
            # Members are walked in the same order and with the same filter as
            # _extract, so a member's anchor matches what its page renders.
            if obj.kind.value == "class":
                for name, member in obj.members.items():
                    if name.startswith("_") or member.kind.value not in ("function", "attribute"):
                        continue
                    _assign_anchor(mapping, seen, f"{path}.{name}")
    return mapping


def _assign_anchor(mapping: dict[str, str], seen: set[str], path: str) -> None:
    """Give ``path`` the next free anchor: the base slug, or a numeric suffix on a clash."""
    base = anchor(path)
    unique = base
    n = 2
    while unique in seen:
        unique = f"{base}-{n}"
        n += 1
    seen.add(unique)
    mapping[path] = unique


def _extract(obj: Any, path: str, *, with_members: bool = True) -> SimpleNamespace:
    kind = obj.kind.value  # "class" | "function" | "attribute" | "module"
    sections = obj.docstring.parsed if obj.docstring else []

    members: list[SimpleNamespace] = []
    if with_members and kind == "class":
        for name, member in obj.members.items():
            if name.startswith("_") or member.kind.value not in ("function", "attribute"):
                continue
            members.append(_extract(member, f"{path}.{name}", with_members=False))

    return SimpleNamespace(
        name=obj.name,
        path=path,
        # The per-page-unique anchor (falls back to the raw slug for a symbol
        # rendered outside the category pages, e.g. a standalone <c-docstring>).
        anchor=reference_anchor_map().get(path, anchor(path)),
        kind=kind,
        signature=_signature(obj),
        description=_description(sections),
        bases=_bases(obj),
        source_url=source_url_for(config.repo_root, getattr(obj, "filepath", None), getattr(obj, "lineno", None)),
        params=_params(sections),
        returns=_returns(sections),
        raises=_raises(sections),
        attributes=_attributes(sections),
        members=members,
    )


def extract_builtin(tag: str) -> SimpleNamespace | None:
    """
    Extract a built-in ``<c-*>`` component from the default registry.

    The built-ins are created dynamically (factory functions), so they are
    introspected at runtime rather than through griffe: the registered class's
    docstring describes the tag.
    """
    try:
        cls = _default_citry.get(tag)
    except NotRegistered:
        return None
    return SimpleNamespace(
        name=f"<c-{tag}>",
        path=f"c-{tag}",
        anchor=anchor(f"c-{tag}"),
        kind="built-in component",
        signature="",
        description=Markup(_md(inspect.getdoc(cls) or "")),  # noqa: S704 - our own docstrings
        bases=[],
        source_url="",
        params=[],
        returns="",
        raises=[],
        attributes=[],
        members=[],
    )


def _signature(obj: Any) -> Markup:
    """A one-line, cross-linked signature: a call signature for functions, the type for attributes."""
    resolve = make_type_resolver()
    if obj.kind.value == "attribute":
        if obj.annotation is None:
            return Markup("")
        return Markup(f"{html.escape(obj.name)}: {render_annotation(obj.annotation, resolve)}")  # noqa: S704
    if obj.kind.value != "function":
        return Markup("")
    rendered = []
    for param in obj.parameters:
        if param.name in ("self", "cls"):
            continue
        text = _param_prefix(param) + html.escape(param.name)
        if param.annotation is not None:
            text += f": {render_annotation(param.annotation, resolve)}"
        if param.default is not None:
            text += f" = {html.escape(str(param.default))}"
        rendered.append(text)
    returns = f" -> {render_annotation(obj.returns, resolve)}" if obj.returns is not None else ""
    return Markup(f"{html.escape(obj.name)}({', '.join(rendered)}){returns}")  # noqa: S704 - escaped / linked HTML


def _param_prefix(param: Any) -> str:
    """The ``*`` / ``**`` marker for a var-positional or var-keyword parameter."""
    kind = getattr(param.kind, "name", "")
    if kind == "var_positional":
        return "*"
    if kind == "var_keyword":
        return "**"
    return ""


def _annotation_html(annotation: object, resolve: Callable[[str, str], str | None]) -> Markup:
    """One annotation rendered as linked-type HTML, or empty ``Markup`` when there is none."""
    if annotation is None:
        return Markup("")
    return Markup(render_annotation(annotation, resolve))  # noqa: S704 - render_annotation escapes its text


def _bases(obj: Any) -> list[Markup]:
    """
    A class's own base classes (excluding ``object``), each as a linked ``<code>``.

    griffe's static ``bases`` is empty for citry's classes, so we import the class at
    runtime and read ``__bases__``. Any import failure yields no bases rather than
    breaking the whole symbol.
    """
    if getattr(obj, "kind", None) is None or obj.kind.value != "class":
        return []
    try:
        module = importlib.import_module(obj.module.path)
        cls = getattr(module, obj.name)
        bases = [base for base in cls.__bases__ if base is not object]
    except Exception:  # noqa: BLE001 - a bad import must never break symbol extraction
        return []
    resolve = make_type_resolver()
    out: list[Markup] = []
    for base in bases:
        label = html.escape(base.__name__)
        url = resolve(base.__name__, f"{base.__module__}.{base.__qualname__}")
        inner = f'<a class="doc-type-link" href="{html.escape(url)}">{label}</a>' if url else label
        out.append(Markup(f"<code>{inner}</code>"))  # noqa: S704 - label and url are escaped
    return out


def _description(sections: list) -> Markup:
    """
    A docstring's prose in source order, keeping example and note blocks.

    Parameter, return, raise, and attribute sections are pulled into their own
    structured fields, so here we render only the free-text, example, and admonition
    sections, each in the order the author wrote them.
    """
    parts: list[str] = []
    for section in sections:
        kind = section.kind.value
        if kind == "text":
            parts.append(_md(section.value))
        elif kind == "examples":
            parts.append(_render_examples(section.value))
        elif kind == "admonition":
            parts.append(_render_admonition(section))
        elif kind in _FIELD_SECTIONS:
            continue  # shown as their own Parameters/Returns/Raises/Attributes fields
        else:
            # Any other section (yields, warns, receives, ...) still shows,
            # instead of silently vanishing from the reference page.
            parts.append(_render_other_section(section))
    return Markup("\n".join(part for part in parts if part))  # noqa: S704 - each part is escaped HTML


def _render_examples(rows: list) -> str:
    """Render a docstring ``Examples:`` section (usually fenced code) as a titled block."""
    # Each row is a (kind, content) pair whose content is already markdown.
    blocks = [_md(row[1] if isinstance(row, tuple) else str(row)) for row in rows]
    return f'<div class="doc-examples"><p class="doc-section-title">Example</p>{"".join(blocks)}</div>'


def _render_admonition(section: Any) -> str:
    """Render a docstring admonition (a ``Note:`` / ``Example:`` block) as a callout."""
    title = html.escape(str(getattr(section, "title", "") or "Note"))
    value = getattr(section, "value", "")
    body = value.contents if hasattr(value, "contents") else str(value)
    return f'<blockquote class="doc-admonition"><p class="doc-admonition-title">{title}</p>{_md(body)}</blockquote>'


def _render_other_section(section: Any) -> str:
    """
    Render a docstring section citry has no dedicated field for.

    Yields, warns, receives, and similar sections would otherwise be dropped;
    this keeps their content visible under a heading. The structured sections
    (parameters, returns, raises, attributes) are rendered as their own fields
    and never reach here.
    """
    label = html.escape((getattr(section, "title", None) or section.kind.value.replace("_", " ")).title())
    value = section.value
    if isinstance(value, str):
        return f'<p class="doc-section">{label}</p>{_md(value)}'
    if not isinstance(value, (list, tuple)):
        return f'<p class="doc-section">{label}</p>{_md(str(value))}'
    # List-valued sections (yields, warns, receives, ...): one row per item,
    # showing its type (when present) and description.
    resolve = make_type_resolver()
    items: list[str] = []
    for item in value:
        annotation = getattr(item, "annotation", None)
        type_html = render_annotation(annotation, resolve) if annotation is not None else ""
        desc = html.escape(getattr(item, "description", "").strip())
        if not type_html and not desc:
            continue
        sep = " - " if type_html and desc else ""
        items.append(f"<li>{type_html}{sep}{desc}</li>")
    if not items:
        return ""
    return f'<p class="doc-section">{label}</p><ul class="doc-list">{"".join(items)}</ul>'


def _params(sections: list) -> list[SimpleNamespace]:
    resolve = make_type_resolver()
    for section in sections:
        if section.kind.value == "parameters":
            return [
                SimpleNamespace(
                    name=p.name,
                    annotation=_annotation_html(p.annotation, resolve),
                    description=p.description.strip(),
                )
                for p in section.value
            ]
    return []


def _returns(sections: list) -> Markup:
    resolve = make_type_resolver()
    for section in sections:
        if section.kind.value == "returns" and section.value:
            item = section.value[0]
            type_html = render_annotation(item.annotation, resolve) if item.annotation is not None else ""
            desc = html.escape(item.description.strip())
            sep = ": " if type_html and desc else ""
            return Markup(f"{type_html}{sep}{desc}")  # noqa: S704 - escaped / linked HTML
    return Markup("")


def _raises(sections: list) -> list[SimpleNamespace]:
    for section in sections:
        if section.kind.value == "raises":
            return [SimpleNamespace(name=str(r.annotation), description=r.description.strip()) for r in section.value]
    return []


def _attributes(sections: list) -> list[SimpleNamespace]:
    resolve = make_type_resolver()
    for section in sections:
        if section.kind.value == "attributes":
            return [
                SimpleNamespace(
                    name=a.name,
                    annotation=_annotation_html(a.annotation, resolve),
                    description=a.description.strip(),
                )
                for a in section.value
            ]
    return []


def _md(text: str) -> str:
    if not text:
        return ""
    # Resolve [text][symbol] cross-refs to reference links before HTML conversion.
    resolved, _unresolved = resolve_crossrefs(text, degrade_unresolved=True)
    return markdown.markdown(resolved, extensions=_MD_EXTENSIONS)


def anchor(path: str) -> str:
    """The HTML anchor id for a symbol path (must match what the reference pages render)."""
    return _ANCHOR_RE.sub("-", path.lower()).strip("-")
