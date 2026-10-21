#!/usr/bin/env python
"""
Generate Citry's tables of HTML, ARIA, SVG, and DOM event names, and of HTML attribute values.

Citry's lint rules read these tables from the generated module. Most names
and keywords come from published standards or Vue's type declarations, so a
refresh picks up what those sources add or remove. The values this script
lists by hand, such as ``SUPPLEMENTS`` and ``SUPPLEMENTAL_EVENT_NAMES``,
change only when someone edits them. The rules and their tables:

- ``citry.template.invalid-attribute-value`` checks a static value such as
  ``draggable="treu"`` against ``ENUMERATED_VALUES``. It also reads
  ``BOOLEAN_ATTRIBUTES`` to report a value such as ``disabled="false"``, which
  still turns the attribute on. Both tables come from the WHATWG HTML
  Standard's attribute index, where the "Value" column lists the allowed
  keywords of an enumerated attribute, such as ``"true"; "false"``, or says
  "Boolean attribute".
- ``citry.template.misspelled-directive`` reads ``GLOBAL_ATTRIBUTES`` (which
  also holds the index's event handler attributes), ``ELEMENT_ATTRIBUTES``,
  and ``CUSTOM_ELEMENT_ATTRIBUTES``, so a ``c-*`` name that is an attribute
  of its element, such as ``c-id``, or ``c-form`` on ``<input>``, is not
  reported.
- ``citry.template.misspelled-attribute`` reads ``GLOBAL_ATTRIBUTES`` and
  ``ELEMENT_ATTRIBUTES`` to tell a typo such as ``titel`` from an attribute
  the element accepts.
- ``citry.template.unknown-aria-attribute`` reads ``ARIA_ATTRIBUTES``: every
  ``aria-*`` state and property that WAI-ARIA 1.2 (the W3C Recommendation) or
  the WAI-ARIA 1.3 editor's draft defines, deprecated ones included, because
  browsers and authors still use them.
- ``citry.template.misspelled-element`` reads ``HTML_ELEMENTS``,
  ``SVG_ELEMENTS``, and ``OBSOLETE_ELEMENTS``. It reads the SVG names because
  a component's template may start at an SVG element such as ``<path>``,
  with no ``<svg>`` around it in the same template, and the
  obsolete names because a tag such as ``<frame>`` is one slip from
  ``<iframe>`` yet is a real, if obsolete, element. The SVG names come from
  the element indexes of SVG 2 and SVG 1.1; SVG 1.1 is included because
  existing SVG files still use elements that SVG 2 dropped, such as
  ``altGlyph``. The obsolete names are the elements that the HTML
  Standard's "Non-conforming features" section (16.2) tells authors not to
  use, such as ``marquee``.
- ``citry.vue.misspelled-event`` reads ``DOM_EVENT_NAMES`` to tell a typo
  such as ``@clik`` from a real event, and
  ``citry.browser.undeclared-component-event`` reads it so that a lowercase
  native listener such as ``@click`` on a component tag is not reported as
  an event the component never declared. The names are the HTML Standard's
  event handler attributes without their ``on`` prefix, the events of Vue's
  ``Events`` type in the ``@vue/runtime-dom`` type declarations committed in
  this repository, and a few names added by hand below, each with its spec
  reference.

For enumerated values, only rows whose value cell is a closed list of keywords
are kept. A row that also allows open text, such as ``"any"`` or a number for
``step``, a custom command keyword, a MIME type, or a token list such as
``sandbox``, is left out, because a value outside the keywords may still be
valid there. A few closed sets that the index describes in words instead of
keywords are added by hand below, each with its spec reference.

Run it from the repository root to refresh the tables from the live standards:

    python scripts/generate_html_attribute_values.py

It downloads every page in ``SOURCES``. Pass ``--saved NAME=FILE`` to read a
saved copy of one of them instead, for example ``--saved aria=wai-aria.html``;
``--source FILE`` is short for ``--saved index=FILE``. Pass
``--vue-types FILE`` to read a different ``runtime-dom.d.ts``. Review the diff
of the generated module before committing it: a new keyword or name the
standards add becomes valid, and a removed one starts being reported.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "packages/py/citry/citry/_html_attribute_values.py"

# Every downloaded page: the name `--saved` uses for it, then a label for the
# generated module's header and the URL. The header names each source so a
# reader can tell which edition of each standard the tables follow.
SOURCES: dict[str, tuple[str, str]] = {
    "index": ("WHATWG HTML Standard, index", "https://html.spec.whatwg.org/multipage/indices.html"),
    "obsolete": (
        "WHATWG HTML Standard, obsolete features",
        "https://html.spec.whatwg.org/multipage/obsolete.html",
    ),
    "aria": ("WAI-ARIA 1.2, W3C Recommendation", "https://www.w3.org/TR/wai-aria-1.2/"),
    "aria-draft": ("WAI-ARIA 1.3, editor's draft", "https://w3c.github.io/aria/"),
    "svg2": ("SVG 2, element index", "https://www.w3.org/TR/SVG2/eltindex.html"),
    "svg11": ("SVG 1.1, element index", "https://www.w3.org/TR/SVG11/eltindex.html"),
}

# Vue's DOM type declarations, committed with the language server's bundled
# types. Their `Events` type lists the native events Vue gives a typed
# listener, such as `onDblclick`.
VUE_TYPES_PATH = ROOT / "packages/py/citry_lsp/citry_lsp/types/node_modules/@vue/runtime-dom/dist/runtime-dom.d.ts"

# Closed keyword sets the attribute index names only in words. Each comes from
# the spec section the index links to.
SUPPLEMENTS: dict[str, dict[str, tuple[str, ...]]] = {
    # "input type keyword": the keyword column of the table in the
    # `type` attribute section of the input element (4.10.5).
    "type": {
        "input": (
            "button",
            "checkbox",
            "color",
            "date",
            "datetime-local",
            "email",
            "file",
            "hidden",
            "image",
            "month",
            "number",
            "password",
            "radio",
            "range",
            "reset",
            "search",
            "submit",
            "tel",
            "text",
            "time",
            "url",
            "week",
        ),
        # `type` on `li` and `ul` is obsolete (16.2), but browsers still read
        # it to pick the list marker; the rendering section (15.3.8) lists
        # these values.
        "li": ("1", "a", "A", "i", "I", "none", "disc", "circle", "square"),
        "ul": ("none", "disc", "circle", "square"),
    },
    # `wrap="off"` is not in the standard, but every major browser supports
    # it to turn off soft wrapping, and no standard keyword does that.
    "wrap": {"textarea": ("soft", "hard", "off")},
    # "Referrer policy": the referrer policy keywords of the Referrer Policy
    # standard, which `referrerpolicy` attributes accept, including the empty string.
    "referrerpolicy": {
        element: (
            "",
            "no-referrer",
            "no-referrer-when-downgrade",
            "same-origin",
            "origin",
            "strict-origin",
            "origin-when-cross-origin",
            "strict-origin-when-cross-origin",
            "unsafe-url",
        )
        for element in ("a", "area", "iframe", "img", "link", "script")
    },
}

# The numbered and lettered list markers of `type` on `ol` and `li` tell "a"
# from "A", so they compare with letter case (4.4.5, 15.3.8). Every other
# keyword, including "disc" on `li`, ignores ASCII case.
CASE_SENSITIVE_KEYWORDS = {
    ("ol", "type"): ("1", "a", "A", "i", "I"),
    ("li", "type"): ("1", "a", "A", "i", "I"),
}

# Global attributes that another standard defines for every HTML element, so
# the HTML index does not list them. `role` comes from ARIA in HTML.
SUPPLEMENTAL_GLOBAL_ATTRIBUTES = ("role",)

# Attributes whose value is a "valid navigable target name or keyword": any
# name that does not start with "_", or one of these keywords (7.3.1.1).
NAVIGABLE_TARGET_KEYWORDS = ("_blank", "_self", "_parent", "_top")
NAVIGABLE_TARGET_ATTRIBUTES = {
    "target": ("a", "area", "base", "form"),
    "formtarget": ("button", "input"),
}
# The `name` of an `iframe` or `object` must be a "valid navigable target
# name" (4.8.5, 4.8.7), so no value there may start with "_".
FRAME_NAME_ELEMENTS = ("iframe", "object")

# Real event names that neither the HTML index nor Vue's `Events` type lists.
# Without them, the event rules would report a listener such as
# `@selectstart` as a typo.
SUPPLEMENTAL_EVENT_NAMES = (
    # Pointer Events Level 3, "The pointerrawupdate event", with its
    # `onpointerrawupdate` handler on GlobalEventHandlers.
    "pointerrawupdate",
    # Selection API, the `onselectstart` and `onselectionchange` handlers it
    # adds to GlobalEventHandlers.
    "selectionchange",
    "selectstart",
    # HTML Standard, "Page visibility" (6.2): the browser fires it at the
    # Document, so a listener on an element never runs, but the name is real
    # and the misspelling rule must not call it a typo.
    "visibilitychange",
    # WebGL 1.0, "WebGL context events" (5.15): fired at the <canvas>.
    "webglcontextcreationerror",
    "webglcontextlost",
    "webglcontextrestored",
    # CSS Containment Level 2, fired at an element with
    # `content-visibility: auto` when its contents start or stop being skipped.
    "contentvisibilityautostatechange",
    # CSS Scroll Snap Level 2, fired at a scroll container when its snap
    # target changes.
    "scrollsnapchange",
    "scrollsnapchanging",
)

# Names each table must hold. A guard that only rejects an empty table misses
# a page that the parser read only part of, such as a cut-off download or a
# moved anchor, so these names come from each source, including the ones only
# one source lists (`aria-braillelabel` from the ARIA 1.3 draft, `altGlyph`
# from SVG 1.1).
REQUIRED_NAMES: dict[str, tuple[str, ...]] = {
    "BOOLEAN_ATTRIBUTES": ("checked", "disabled", "inert"),
    "ARIA_ATTRIBUTES": ("aria-braillelabel", "aria-expanded", "aria-grabbed", "aria-hidden", "aria-label"),
    "SVG_ELEMENTS": ("altGlyph", "foreignObject", "path", "svg"),
    "OBSOLETE_ELEMENTS": ("applet", "frame", "marquee"),
    "DOM_EVENT_NAMES": ("afterprint", "click", "compositionstart", "pointerdown"),
}

# SVG names may use camelCase, such as `clipPath`, and hyphens, such as
# `font-face`.
_SVG_NAME = re.compile(r"[A-Za-z][A-Za-z0-9-]*")
# An HTML element name is lowercase letters and digits, such as `h1`.
_HTML_NAME = re.compile(r"[a-z][a-z0-9]*")


class _TableReader(HTMLParser):
    """Collect each table's rows as lists of cell text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: dict[str, list[list[str]]] = {}
        self.updated: str | None = None
        self._table: str | None = None
        self._unnamed = 0
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._in_pubdate = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        # The standard omits optional end tags, so a new cell or row closes the open one.
        if tag == "table":
            self._unnamed += 1
            self._table = values.get("id") or f"table-{self._unnamed}"
            self.tables[self._table] = []
        elif tag == "tr" and self._table is not None:
            self._close_row()
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._close_cell()
            self._cell = []
        elif tag == "span" and values.get("class") == "pubdate":
            self._in_pubdate = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"}:
            self._close_cell()
        elif tag == "tr":
            self._close_row()
        elif tag == "table":
            self._close_row()
            self._table = None
        elif tag == "span":
            self._in_pubdate = False

    def _close_cell(self) -> None:
        if self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
        self._cell = None

    def _close_row(self) -> None:
        self._close_cell()
        if self._table is not None and self._row is not None:
            self.tables[self._table].append(self._row)
        self._row = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)
        if self._in_pubdate:
            self.updated = (self.updated or "") + data


class _ElementReader(HTMLParser):
    """Collect the attributes and text of every element that ``match`` accepts."""

    def __init__(self, match: Callable[[str, dict[str, str | None]], bool]) -> None:
        super().__init__(convert_charrefs=True)
        self.found: list[tuple[dict[str, str | None], str]] = []
        self._match = match
        self._tag: str | None = None
        # The matched element can hold an element with the same tag, such as
        # a <span> inside the SVG index's name <span>, so only the end tag
        # that brings this count back to zero closes the match.
        self._depth = 0
        self._attrs: dict[str, str | None] = {}
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._tag is not None:
            if tag == self._tag:
                self._depth += 1
            return
        values = dict(attrs)
        if self._match(tag, values):
            self._tag, self._depth, self._attrs, self._text = tag, 1, values, []

    def handle_endtag(self, tag: str) -> None:
        if tag != self._tag:
            return
        self._depth -= 1
        if self._depth == 0:
            self.found.append((self._attrs, " ".join("".join(self._text).split())))
            self._tag = None

    def handle_data(self, data: str) -> None:
        if self._tag is not None:
            self._text.append(data)


class _DefinitionListReader(HTMLParser):
    """
    Collect the terms of the first ``<dl>`` whose id is ``anchor_id``, or that follows the element with that id.

    A page may mark a list either on the ``<dl>`` itself or on the heading
    before it, as the HTML Standard does for its non-conforming elements, so
    both count. A term is the text of one ``<dt>`` of that list, not of a list
    nested in one of its descriptions.
    """

    def __init__(self, anchor_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self.terms: list[str] = []
        self._anchor_id = anchor_id
        self._after_anchor = False
        self._done = False
        self._depth = 0
        self._term: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._done:
            return
        if dict(attrs).get("id") == self._anchor_id:
            self._after_anchor = True
        if tag == "dl" and (self._after_anchor or self._depth):
            self._depth += 1
        elif self._depth == 1 and tag in {"dt", "dd"}:
            # The HTML Standard omits optional end tags, so the next term or
            # description closes the open term.
            self._close_term()
            if tag == "dt":
                self._term = []

    def handle_endtag(self, tag: str) -> None:
        if self._done or not self._depth:
            return
        if tag == "dt" and self._depth == 1:
            self._close_term()
        elif tag == "dl":
            self._depth -= 1
            if self._depth == 0:
                self._close_term()
                self._done = True

    def handle_data(self, data: str) -> None:
        if self._term is not None:
            self._term.append(data)

    def _close_term(self) -> None:
        if self._term is not None:
            self.terms.append(" ".join("".join(self._term).split()))
        self._term = None


# A value cell that is only quoted keywords and "the empty string", separated
# by semicolons, describes a closed set. Anything else allows open text.
_KEYWORD = re.compile(r'"([^"]*)"|the empty string')
_CLOSED_CELL = re.compile(r'^(?:(?:"[^"]*"|the empty string)\s*;?\s*)+$')
# One row of the index can say "ASCII case-insensitive match for "UTF-8"".
_CASE_INSENSITIVE_MATCH = re.compile(r'^ASCII case-insensitive match for "([^"]+)"$')


def _keywords(cell: str) -> tuple[str, ...] | None:
    """Return the closed keyword set of one value cell, or ``None`` for an open one."""
    single = _CASE_INSENSITIVE_MATCH.match(cell)
    if single is not None:
        return (single.group(1),)
    if not _CLOSED_CELL.match(cell):
        return None
    return tuple(match.group(1) if match.group(1) is not None else "" for match in _KEYWORD.finditer(cell))


def _owners(cell: str, known_elements: set[str]) -> Iterator[str]:
    """
    Yield each owner that one "Element(s)" cell of the attribute index names.

    "HTML elements" marks a global attribute and comes out as "*", and
    "form-associated custom elements" comes out unchanged. Any other owner
    yields each element name it contains.
    """
    for raw_owner in cell.split(";"):
        owner = raw_owner.strip()
        if owner == "HTML elements":
            yield "*"
        elif owner == "form-associated custom elements":
            yield owner
        else:
            # An owner can carry a note, as in "source (in picture)", and
            # one row lists "video img" without a separator, so each word
            # outside the note that names an element counts.
            for word in re.sub(r"\([^)]*\)", " ", owner).split():
                if word in known_elements:
                    yield word


def build_table(page: str) -> tuple[dict[str, dict[str, tuple[str, ...]]], tuple[str, ...], str]:
    """Return the keyword table, the HTML element names, and the standard's update date."""
    reader = _TableReader()
    reader.feed(page)
    attributes = reader.tables.get("attributes-1")
    elements_table = reader.tables.get("table-1")
    if not attributes or not elements_table:
        msg = "the attribute or element index was not found; the page layout changed"
        raise SystemExit(msg)
    elements: set[str] = set()
    for row in elements_table[1:]:
        for name in row[0].split(","):
            # "SVG svg", "MathML math", and the custom-element row are not HTML elements.
            if _HTML_NAME.fullmatch(name.strip()):
                elements.add(name.strip())
    table: dict[str, dict[str, tuple[str, ...]]] = {}
    for row in attributes[1:]:
        if len(row) < 4:
            continue
        attribute, owners, _description, value = row[:4]
        keywords = _keywords(value)
        if keywords is None:
            continue
        # A global attribute is stored under "*". A value table cannot apply to
        # every custom element, so that owner is left out.
        targets = [owner for owner in _owners(owners, elements) if owner != "form-associated custom elements"]
        for element in targets:
            table.setdefault(attribute, {})[element] = keywords
    for attribute, by_element in SUPPLEMENTS.items():
        for element, keywords in by_element.items():
            table.setdefault(attribute, {})[element] = keywords
    ordered = {
        attribute: {element: table[attribute][element] for element in sorted(table[attribute])}
        for attribute in sorted(table)
    }
    return ordered, tuple(sorted(elements)), (reader.updated or "unknown").strip()


def build_attribute_names(
    page: str,
) -> tuple[tuple[str, ...], dict[str, tuple[str, ...]], tuple[str, ...]]:
    """
    Return the attribute names of the index: global, per element, and on custom elements.

    Global names are those the index lists for "HTML elements". The custom
    element names are those it lists for "form-associated custom elements";
    a template cannot tell whether a custom element is form-associated, so
    the rule accepts them on every custom element.
    """
    reader = _TableReader()
    reader.feed(page)
    attributes = reader.tables.get("attributes-1")
    if not attributes:
        msg = "the attribute index was not found; the page layout changed"
        raise SystemExit(msg)
    _table, elements, _updated = build_table(page)
    known_elements = set(elements)
    global_names: set[str] = set(SUPPLEMENTAL_GLOBAL_ATTRIBUTES)
    custom_names: set[str] = set()
    by_element: dict[str, set[str]] = {}
    # The event handler table has the same columns, and its handlers, such as
    # `onclick`, are attributes too.
    rows = [*attributes[1:], *reader.tables.get("ix-event-handlers", [])[1:]]
    for row in rows:
        if len(row) < 2:
            continue
        attribute = row[0]
        for owner in _owners(row[1], known_elements):
            if owner == "*":
                global_names.add(attribute)
            elif owner == "form-associated custom elements":
                custom_names.add(attribute)
            else:
                by_element.setdefault(owner, set()).add(attribute)
    return (
        tuple(sorted(global_names)),
        {element: tuple(sorted(by_element[element])) for element in sorted(by_element)},
        tuple(sorted(custom_names)),
    )


def build_boolean_attributes(page: str) -> dict[str, tuple[str, ...]]:
    """
    Return each boolean attribute and the elements that have it, "*" for every element.

    The index gives a boolean attribute the value "Boolean attribute", and one
    name can have several rows, such as ``disabled`` on form controls, on
    ``fieldset``, and on ``link``, so the rows are merged. A form-associated
    custom element is left out: a template cannot tell whether a custom
    element is one, so the rule does not check custom elements.
    """
    reader = _TableReader()
    reader.feed(page)
    attributes = reader.tables.get("attributes-1")
    if not attributes:
        msg = "the attribute index was not found; the page layout changed"
        raise SystemExit(msg)
    _table, elements, _updated = build_table(page)
    known_elements = set(elements)
    by_attribute: dict[str, set[str]] = {}
    for row in attributes[1:]:
        if len(row) < 4 or row[3] != "Boolean attribute":
            continue
        owners = {owner for owner in _owners(row[1], known_elements) if owner != "form-associated custom elements"}
        if owners:
            by_attribute.setdefault(row[0], set()).update(owners)
    if not by_attribute:
        msg = "no boolean attribute was found in the attribute index; the page layout changed"
        raise SystemExit(msg)
    return {attribute: tuple(sorted(by_attribute[attribute])) for attribute in sorted(by_attribute)}


def build_aria_attributes(*pages: str) -> tuple[str, ...]:
    """
    Return every ``aria-*`` state and property name the WAI-ARIA pages define.

    Each state or property has its own ``<section>`` whose id is its name and
    whose class says "state" or "property", deprecated ones included.
    """

    def is_definition(tag: str, attrs: dict[str, str | None]) -> bool:
        classes = set((attrs.get("class") or "").split())
        return (
            tag == "section" and (attrs.get("id") or "").startswith("aria-") and bool(classes & {"state", "property"})
        )

    names: set[str] = set()
    for page in pages:
        reader = _ElementReader(is_definition)
        reader.feed(page)
        found = {attrs["id"] or "" for attrs, _text in reader.found}
        # An empty result means the spec changed its markup, and an empty
        # table would make the rule report every ARIA attribute.
        if not found:
            msg = "no ARIA state or property section was found; the page layout changed"
            raise SystemExit(msg)
        names |= found
    return tuple(sorted(names))


def build_svg_elements(*pages: str) -> tuple[str, ...]:
    """
    Return the element names the SVG element index pages list, in their original case.

    Each index writes a name in quotes, as in ``'foreignObject'``, inside a
    ``<span class="element-name">``.
    """
    names: set[str] = set()
    for page in pages:
        reader = _ElementReader(lambda tag, attrs: tag == "span" and attrs.get("class") == "element-name")
        reader.feed(page)
        found = {text.strip("\u2018\u2019'\" ") for _attrs, text in reader.found}
        unexpected = sorted(name for name in found if not _SVG_NAME.fullmatch(name))
        if not found or unexpected:
            msg = f"the SVG element index listed {unexpected or 'no element names'}; the page layout changed"
            raise SystemExit(msg)
        names |= found
    return tuple(sorted(names))


def build_obsolete_elements(page: str) -> tuple[str, ...]:
    """
    Return the elements the HTML Standard's "Non-conforming features" section forbids.

    The section opens with "Elements in the following list are entirely
    obsolete", and that first definition list has one element name per term.
    """
    reader = _DefinitionListReader("non-conforming-features")
    reader.feed(page)
    # Every term must be one element name. Anything else means the list
    # changed shape, and silently dropping it could lose an element.
    unexpected = [term for term in reader.terms if not _HTML_NAME.fullmatch(term)]
    if not reader.terms or unexpected:
        msg = f"the non-conforming element list held {unexpected or 'no terms'}; the page layout changed"
        raise SystemExit(msg)
    return tuple(sorted(set(reader.terms)))


def build_event_names(page: str, vue_types: str) -> tuple[str, ...]:
    """
    Return the lowercase DOM event names a template listener such as ``@click`` may name.

    The names are the HTML index's event handler attributes without "on",
    the keys of Vue's ``Events`` type without "on", such as ``onDblclick``,
    which gives ``dblclick``,
    and ``SUPPLEMENTAL_EVENT_NAMES``.
    """
    reader = _TableReader()
    reader.feed(page)
    handlers = [row[0] for row in reader.tables.get("ix-event-handlers", [])[1:] if row and row[0].startswith("on")]
    events = re.search(r"^export interface Events \{\n(.*?)^\}", vue_types, re.DOTALL | re.MULTILINE)
    if not handlers or events is None:
        msg = "the event handler index or Vue's Events type was not found; the source changed"
        raise SystemExit(msg)
    vue_names = re.findall(r"^\s*on([A-Za-z]+)\??\s*:", events.group(1), re.MULTILINE)
    names = {name[2:] for name in handlers} | {name.lower() for name in vue_names} | set(SUPPLEMENTAL_EVENT_NAMES)
    return tuple(sorted(names))


def _vue_types_label(path: Path) -> str:
    """Name the Vue type declarations for the header, with the package version when it is known."""
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    manifest = path.parent.parent / "package.json"
    if manifest.is_file():
        package = json.loads(manifest.read_text(encoding="utf-8"))
        return f"{package.get('name', 'Vue')} {package.get('version', '(version unknown)')} types, {shown}"
    return f"Vue types, {shown}"


def render(pages: Mapping[str, str], vue_types: str, *, retrieved: str, vue_source: str) -> str:
    """Render the generated Python module from every source page and Vue's type declarations."""
    index = pages["index"]
    table, elements, updated = build_table(index)
    global_names, element_names, custom_names = build_attribute_names(index)
    boolean_attributes = build_boolean_attributes(index)
    aria = build_aria_attributes(pages["aria"], pages["aria-draft"])
    svg = build_svg_elements(pages["svg2"], pages["svg11"])
    obsolete = build_obsolete_elements(pages["obsolete"])
    events = build_event_names(index, vue_types)
    sources = "".join(f"- {label}: {url}\n" for label, url in SOURCES.values())
    return (
        '"""\n'
        "HTML, ARIA, SVG, and DOM event names and HTML attribute values. Generated; do not edit.\n\n"
        "Run python scripts/generate_html_attribute_values.py to refresh it.\n"
        f"WHATWG HTML Standard, Last Updated {updated}. Generated {retrieved} from these sources:\n"
        f"{sources}"
        f"- {vue_source}\n"
        '"""\n\n'
        "# ruff: noqa: E501, Q000\n"
        "# fmt: off\n\n"
        "from __future__ import annotations\n\n"
        "from typing import Final\n\n"
        "# HTML element names, so a custom element or a component tag is never checked.\n"
        f"HTML_ELEMENTS: Final[frozenset[str]] = frozenset({pformat(elements, width=110, compact=True)})\n\n"
        '# attribute -> element ("*" for every HTML element) -> allowed keywords.\n'
        '# "" means the empty string, or the attribute with no value, is allowed.\n'
        f"ENUMERATED_VALUES: Final[dict[str, dict[str, tuple[str, ...]]]] = {pformat(table, width=110)}\n\n"
        "# (element, attribute) -> the keywords that compare with letter case.\n"
        "CASE_SENSITIVE_KEYWORDS: Final[dict[tuple[str, str], tuple[str, ...]]] = "
        f"{pformat(CASE_SENSITIVE_KEYWORDS, width=110)}\n\n"
        '# Keywords for an attribute that otherwise takes any name not starting with "_".\n'
        f"NAVIGABLE_TARGET_KEYWORDS: Final[tuple[str, ...]] = {pformat(NAVIGABLE_TARGET_KEYWORDS)}\n"
        "NAVIGABLE_TARGET_ATTRIBUTES: Final[dict[str, tuple[str, ...]]] = "
        f"{pformat(NAVIGABLE_TARGET_ATTRIBUTES, width=110)}\n\n"
        '# Elements whose `name` may not start with "_" at all.\n'
        f"FRAME_NAME_ELEMENTS: Final[tuple[str, ...]] = {pformat(FRAME_NAME_ELEMENTS)}\n\n"
        "# Attribute names every HTML element accepts, including event handlers.\n"
        "# `data-*` and `aria-*` names are open families, not listed here.\n"
        f"GLOBAL_ATTRIBUTES: Final[frozenset[str]] = frozenset({pformat(global_names, width=110, compact=True)})\n\n"
        "# element -> the attribute names only that element accepts.\n"
        "ELEMENT_ATTRIBUTES: Final[dict[str, tuple[str, ...]]] = "
        f"{pformat(element_names, width=110, compact=True)}\n\n"
        "# Attribute names a form-associated custom element accepts.\n"
        f"CUSTOM_ELEMENT_ATTRIBUTES: Final[tuple[str, ...]] = {pformat(custom_names, width=110, compact=True)}\n\n"
        '# Boolean attribute -> the elements that have it ("*" for every HTML element).\n'
        '# Any value turns a boolean attribute on, even "false".\n'
        "BOOLEAN_ATTRIBUTES: Final[dict[str, tuple[str, ...]]] = "
        f"{pformat(boolean_attributes, width=110, compact=True)}\n\n"
        "# Every aria-* state and property of WAI-ARIA 1.2 and the 1.3 draft, deprecated ones included.\n"
        f"ARIA_ATTRIBUTES: Final[frozenset[str]] = frozenset({pformat(aria, width=110, compact=True)})\n\n"
        "# SVG 2 and SVG 1.1 element names, in their original case, such as foreignObject.\n"
        f"SVG_ELEMENTS: Final[frozenset[str]] = frozenset({pformat(svg, width=110, compact=True)})\n\n"
        "# Elements the HTML Standard tells authors not to use (16.2 Non-conforming features).\n"
        f"OBSOLETE_ELEMENTS: Final[frozenset[str]] = frozenset({pformat(obsolete, width=110, compact=True)})\n\n"
        "# Lowercase DOM event names a listener such as @click may name, without the on prefix.\n"
        f"DOM_EVENT_NAMES: Final[frozenset[str]] = frozenset({pformat(events, width=110, compact=True)})\n"
    )


def check_required_names(module: str) -> None:
    """
    Stop when the generated module lacks a name in ``REQUIRED_NAMES``.

    Running the module also proves it imports before it replaces the
    committed one.
    """
    namespace: dict[str, object] = {}
    exec(compile(module, str(OUTPUT_PATH), "exec"), namespace)  # noqa: S102 - our own generated source
    missing: dict[str, list[str]] = {}
    for table, names in REQUIRED_NAMES.items():
        # Every checked table is a frozenset of names or a dict keyed by name.
        values = namespace[table]
        if not isinstance(values, (frozenset, dict)):
            msg = f"{table} is a {type(values).__name__}, not a table of names"
            raise SystemExit(msg)
        absent = sorted(set(names) - set(values))
        if absent:
            missing[table] = absent
    if missing:
        msg = f"the generated tables lack names they always hold, so a source was read only in part: {missing}"
        raise SystemExit(msg)


def _download(url: str) -> str:
    """Fetch one source page as text."""
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 - fixed https URLs from SOURCES
        return response.read().decode("utf-8")


def main() -> None:
    """Download or read every source and write the generated module."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--source", type=Path, help="Read a saved copy of the HTML Standard's index page (same as --saved index=FILE)."
    )
    parser.add_argument(
        "--saved",
        action="append",
        default=[],
        metavar="NAME=FILE",
        help=f"Read a saved copy of one source page instead of downloading it. Names: {', '.join(SOURCES)}.",
    )
    parser.add_argument(
        "--vue-types",
        type=Path,
        default=VUE_TYPES_PATH,
        help="Read Vue's runtime-dom.d.ts from this path instead of the copy bundled with the language server.",
    )
    args = parser.parse_args()
    saved: dict[str, Path] = {}
    for item in args.saved:
        name, _, file = item.partition("=")
        # A typo in the name would otherwise download the page silently.
        if name not in SOURCES or not file:
            parser.error(f"--saved expects NAME=FILE with NAME one of {', '.join(SOURCES)}, got {item!r}")
        saved[name] = Path(file)
    if args.source is not None:
        # Two copies of the same page would leave it unclear which one was read.
        if "index" in saved:
            parser.error("pass --source or --saved index=FILE, not both")
        saved["index"] = args.source
    pages = {
        name: saved[name].read_text(encoding="utf-8") if name in saved else _download(url)
        for name, (_label, url) in SOURCES.items()
    }
    vue_types = args.vue_types.resolve()
    retrieved = datetime.now(timezone.utc).date().isoformat()
    module = render(
        pages,
        vue_types.read_text(encoding="utf-8"),
        retrieved=retrieved,
        vue_source=_vue_types_label(vue_types),
    )
    check_required_names(module)
    OUTPUT_PATH.write_text(module, encoding="utf-8")


if __name__ == "__main__":
    main()
