#!/usr/bin/env python
"""
Generate Citry's tables of HTML attribute names and enumerated attribute values.

The rule ``citry.template.invalid-attribute-value`` checks a static attribute
value such as ``draggable="treu"`` against the value table. The table is read
from the WHATWG HTML Standard's attribute index, where the "Value" column lists
the allowed keywords of an enumerated attribute, such as ``"true"; "false"``.

The rule ``citry.template.misspelled-directive`` reads the attribute names from
the same index, plus its event handler attributes, so a ``c-*`` name that is a
real HTML attribute, such as ``c-id`` or ``c-form``, is never reported.

Only rows whose value cell is a closed list of keywords are kept. A row that
also allows open text, such as ``"any"`` or a number for ``step``, a custom
command keyword, a MIME type, or a token list such as ``sandbox``, is left out,
because a value outside the keywords may still be valid there. A few closed
sets that the index describes in words instead of keywords are added by hand
below, each with its spec reference.

Run it from the repository root to refresh the table from the live standard:

    python scripts/generate_html_attribute_values.py

Pass ``--source FILE`` to read a saved copy of
https://html.spec.whatwg.org/multipage/indices.html instead of downloading it.
Review the diff of the generated module before committing it: a new keyword
the standard adds becomes valid, and a removed one starts being reported.
"""

from __future__ import annotations

import argparse
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from pprint import pformat

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "packages/py/citry/citry/_html_attribute_values.py"
SOURCE_URL = "https://html.spec.whatwg.org/multipage/indices.html"

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
            if re.fullmatch(r"[a-z][a-z0-9]*", name.strip()):
                elements.add(name.strip())
    table: dict[str, dict[str, tuple[str, ...]]] = {}
    for row in attributes[1:]:
        if len(row) < 4:
            continue
        attribute, owners, _description, value = row[:4]
        keywords = _keywords(value)
        if keywords is None:
            continue
        # "HTML elements" marks a global attribute, stored under "*".
        targets = ["*"] if owners == "HTML elements" else [item.strip() for item in owners.split(";")]
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
    elements_table = reader.tables.get("table-1")
    if not attributes or not elements_table:
        msg = "the attribute or element index was not found; the page layout changed"
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
        attribute, owners = row[0], row[1]
        for raw_owner in owners.split(";"):
            owner = raw_owner.strip()
            if owner == "HTML elements":
                global_names.add(attribute)
            elif owner == "form-associated custom elements":
                custom_names.add(attribute)
            else:
                # An owner can carry a note, as in "source (in picture)", and
                # one row lists "video img" without a separator, so each word
                # outside the note that names an element counts.
                for word in re.sub(r"\([^)]*\)", " ", owner).split():
                    if word in known_elements:
                        by_element.setdefault(word, set()).add(attribute)
    return (
        tuple(sorted(global_names)),
        {element: tuple(sorted(by_element[element])) for element in sorted(by_element)},
        tuple(sorted(custom_names)),
    )


def render(page: str, *, retrieved: str) -> str:
    """Render the generated Python module for one copy of the attribute index."""
    table, elements, updated = build_table(page)
    global_names, element_names, custom_names = build_attribute_names(page)
    return (
        '"""\n'
        "HTML attribute names and the valid values of enumerated HTML attributes. Generated; do not edit.\n\n"
        "Run python scripts/generate_html_attribute_values.py to refresh it.\n"
        f"Source: {SOURCE_URL}\n"
        f"WHATWG HTML Standard, Last Updated {updated}; retrieved {retrieved}.\n"
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
        f"CUSTOM_ELEMENT_ATTRIBUTES: Final[tuple[str, ...]] = {pformat(custom_names, width=110, compact=True)}\n"
    )


def main() -> None:
    """Download or read the attribute index and write the generated module."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--source", type=Path, help="Read a saved copy of the attribute index page.")
    args = parser.parse_args()
    if args.source is not None:
        page = args.source.read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:  # noqa: S310 - fixed https URL
            page = response.read().decode("utf-8")
    retrieved = datetime.now(timezone.utc).date().isoformat()
    OUTPUT_PATH.write_text(render(page, retrieved=retrieved), encoding="utf-8")


if __name__ == "__main__":
    main()
