"""
A parser that tracks which elements a browser keeps open, for Citry UI's checks of rendered output.

Several Citry UI components check the HTML they rendered, for example that
the fill of a CImage placeholder holds nothing focusable. Each check needs
to know which elements sit inside which, the way a browser builds the page.
Python's ``HTMLParser`` only reports tags. On its own it reads the content
of ``<style>`` and the other raw-text elements as text even inside SVG and
MathML, where a browser reads it as elements, and it reports end tags that
a browser ignores, such as ``</link>``. ``MarkupTreeParser`` follows the
browser's rules for these and tells the check when an element opens and
when it closes.

Citry keeps a copy of this parser in
``packages/py/citry/citry/util/_markup_tree.py`` for its own checks, because
``citry`` does not import ``citry_ui``. When you change how one copy reads
HTML, make the same change in the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

from citry.util.html import LongReferenceSafeParser
from citry_ui.components._validation import first_attribute_occurrences

Namespace = Literal["html", "svg", "math"]

T = TypeVar("T")

# Elements that never have content or an end tag. A browser ignores an end
# tag with one of these names, except ``</br>``, which it reads as ``<br>``.
VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "basefont",
        "bgsound",
        "br",
        "col",
        "embed",
        "frame",
        "hr",
        "img",
        "input",
        "keygen",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)

# Start tags that end SVG or MathML content: the browser closes the open SVG
# and MathML elements and creates an HTML element. From the HTML standard,
# "The rules for parsing tokens in foreign content".
_BREAKOUT_TAGS = frozenset(
    {
        "b",
        "big",
        "blockquote",
        "body",
        "br",
        "center",
        "code",
        "dd",
        "div",
        "dl",
        "dt",
        "em",
        "embed",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "head",
        "hr",
        "i",
        "img",
        "li",
        "listing",
        "menu",
        "meta",
        "nobr",
        "ol",
        "p",
        "pre",
        "ruby",
        "s",
        "small",
        "span",
        "strong",
        "strike",
        "sub",
        "sup",
        "table",
        "tt",
        "u",
        "ul",
        "var",
    }
)
# ``<font>`` ends SVG or MathML content only with one of these attributes.
_BREAKOUT_FONT_ATTRIBUTES = frozenset({"color", "face", "size"})

# MathML elements whose children are HTML, apart from these two MathML tags.
_MATHML_TEXT_ELEMENTS = frozenset({"mi", "mo", "mn", "ms", "mtext"})
_MATHML_TEXT_CHILDREN = frozenset({"mglyph", "malignmark"})
# SVG elements whose children are HTML. ``HTMLParser`` lowercases tag names,
# so ``foreignObject`` arrives as ``foreignobject``.
_SVG_HTML_CONTENT_ELEMENTS = frozenset({"foreignobject", "desc", "title"})
# The ``encoding`` values that make a MathML ``annotation-xml`` hold HTML.
_HTML_ANNOTATION_ENCODINGS = frozenset({"text/html", "application/xhtml+xml"})

# Elements that hide an open element below them from an end tag: the end tag
# is ignored when one of these sits between it and its match. From the HTML
# standard, "has an element in scope".
_HTML_SCOPE_LIMITS = frozenset({"applet", "caption", "html", "table", "td", "th", "marquee", "object", "template"})
_FOREIGN_SCOPE_LIMITS: frozenset[tuple[Namespace, str]] = frozenset(
    {("math", name) for name in (*_MATHML_TEXT_ELEMENTS, "annotation-xml")}
    | {("svg", name) for name in _SVG_HTML_CONTENT_ELEMENTS}
)

# The HTML standard's "special" elements. An end tag that matches no element
# above the nearest of these is ignored.
_SPECIAL_ELEMENTS = frozenset(
    {
        "address",
        "applet",
        "area",
        "article",
        "aside",
        "base",
        "basefont",
        "bgsound",
        "blockquote",
        "body",
        "br",
        "button",
        "caption",
        "center",
        "col",
        "colgroup",
        "dd",
        "details",
        "dir",
        "div",
        "dl",
        "dt",
        "embed",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "frame",
        "frameset",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "head",
        "header",
        "hgroup",
        "hr",
        "html",
        "iframe",
        "img",
        "input",
        "keygen",
        "li",
        "link",
        "listing",
        "main",
        "marquee",
        "menu",
        "meta",
        "nav",
        "noembed",
        "noframes",
        "noscript",
        "object",
        "ol",
        "p",
        "param",
        "plaintext",
        "pre",
        "script",
        "search",
        "section",
        "select",
        "source",
        "style",
        "summary",
        "table",
        "tbody",
        "td",
        "template",
        "textarea",
        "tfoot",
        "th",
        "thead",
        "title",
        "tr",
        "track",
        "ul",
        "wbr",
        "xmp",
    }
)

# End tags that close their element only when it is in scope, passing over
# special elements on the way. Every other end tag stops at the first
# special element.
_SCOPED_END_TAGS = frozenset(
    {
        "address",
        "applet",
        "article",
        "aside",
        "blockquote",
        "button",
        "center",
        "dd",
        "details",
        "dialog",
        "dir",
        "div",
        "dl",
        "dt",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "header",
        "hgroup",
        "listing",
        "main",
        "marquee",
        "menu",
        "nav",
        "object",
        "ol",
        "pre",
        "search",
        "section",
        "summary",
        "ul",
    }
)
_HEADINGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
# End tags a browser reads in the body without closing anything there.
_IGNORED_END_TAGS = frozenset({"body", "head", "html"})
# End tags of a table cell or caption and the table parts around it, which
# close a select opened inside the cell or caption.
_TABLE_END_TAGS = frozenset({"caption", "table", "tbody", "td", "tfoot", "th", "thead", "tr"})

# Start tags that first close an open ``<p>``, from the HTML standard's rules
# for start tags "in body".
_CLOSES_PARAGRAPH = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "center",
        "dd",
        "details",
        "dialog",
        "dir",
        "div",
        "dl",
        "dt",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "header",
        "hgroup",
        "hr",
        "li",
        "listing",
        "main",
        "menu",
        "nav",
        "ol",
        "p",
        "plaintext",
        "pre",
        "search",
        "section",
        "summary",
        "table",
        "ul",
        "xmp",
    }
    | _HEADINGS
)
# Elements after which an open ``<a>`` no longer counts for a new ``<a>``.
_FORMATTING_MARKERS = ("applet", "caption", "marquee", "object", "td", "template", "th")
# HTML elements whose content is text up to their end tag. ``HTMLParser``
# always treats ``<script>`` and ``<style>`` this way; Python releases before
# 2025 read these others as markup.
_HTML_RAW_TEXT = frozenset({"iframe", "noembed", "noframes", "textarea", "title", "xmp"})


@dataclass(slots=True)
class OpenElement(Generic[T]):
    """One element the browser has open, with what the check stored for it."""

    tag: str
    namespace: Namespace
    # Whether the element's children follow the HTML rules although the
    # element itself is SVG or MathML, as in ``<foreignObject>``.
    holds_html: bool
    value: T
    # The lookup lists this element is filed under, so closing it can take
    # it off each one.
    keys: tuple[str, ...] = ()
    # Set when ``</form>`` takes a form off the open elements while elements
    # inside it stay open; the entry stays in place until they close.
    removed: bool = False


class MarkupTreeParser(LongReferenceSafeParser, Generic[T]):
    """
    Report each element as the browser opens and closes it, for a check of rendered output.

    A subclass implements ``open_element``, which runs for every element the
    browser creates and returns the value the check keeps for it, and may
    implement ``close_element`` and ``unmatched_end_tag``. It must not
    define ``handle_starttag``, ``handle_startendtag`` or ``handle_endtag``.
    ``open_elements`` lists the open elements, outermost first; its last
    entry is always the element new content goes into.

    The parser follows the browser in these ways:

    - Inside SVG and MathML, ``<style>``, ``<script>``, ``<title>`` and the
      other elements ``HTMLParser`` reads as raw text hold elements, as in a
      browser. A tag such as ``<div>`` there closes the SVG or MathML
      elements first, and ``<![CDATA[`` starts a CDATA section only there;
      in HTML it is a comment that ends at the next ``>``.
    - An end tag closes the nearest open element with its name and every
      element opened inside it, and is ignored when the browser ignores it:
      for a void element such as ``</link>``, or when an element such as a
      table cell sits between the end tag and its match. ``</br>`` and a
      ``</p>`` with no open paragraph create an empty element, and
      ``</form>`` closes only the form, leaving the elements inside it open.
      Inside an open ``<select>``, ``</select>`` closes the select and
      everything opened inside it, ``</br>`` creates a ``<br>``, ``</p>``
      closes a paragraph opened inside the select or else creates an empty
      one, ``</template>`` and the end tag of the table cell or caption
      around the select (or of its row, section or table) close the select
      with it, and any other end tag closes only an element opened inside
      the select.
    - A start tag closes what the browser closes for it: an open ``<p>``
      before ``<div>`` and the other block elements, an open ``<li>``,
      ``<dd>``, ``<dt>``, ``<button>`` or heading before another of its
      kind, an open ``<a>`` before a new ``<a>``, and an open ``<select>``
      before ``<input>`` or before a nested ``<select>`` tag, which the
      browser then drops.
    - ``<span/>`` opens a span in HTML; the ``/`` closes an element only in
      SVG and MathML. ``<image>`` in HTML creates an ``<img>``.

    It does not close an ``<option>`` before another or before ``<hr>``.
    It does not model the elements a browser moves or opens again. A
    browser moves content placed before a ``<table>`` out in front of it,
    moves a block element out of a formatting element after an end tag
    such as ``</b>`` or a second ``<a>``, and opens a formatting element
    such as ``<b>`` again after ``</div>`` closed it. Outside a select, it
    also does not close a table cell before ``<td>`` or ``<tr>``, or for
    ``</td>``, ``</tr>`` or ``</table>`` while another element such as a
    ``<div>`` is open inside the cell. Here those elements stay where they
    were opened, which can hide an extra root element from a check that
    counts roots. ``<noscript>`` content is read as markup,
    as in a browser with scripting off; with scripting on it is text, so a
    check of a region should refuse ``<noscript>`` there.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)

    def reset(self) -> None:
        super().reset()
        self.open_elements: list[OpenElement[T]] = []
        # For each kind of element, the positions in ``open_elements`` of the
        # open elements of that kind, so each tag looks up its match without
        # walking the whole stack. Keys are "html:<tag>" and "any:<tag>",
        # "html", "special", "scope" and "li-stop".
        self._positions: dict[str, list[int]] = {}
        # Whether a ``<form>`` is open outside ``<template>``; the browser
        # ignores a second ``<form>`` start tag until ``</form>``.
        self._form_open = False
        # Whether the start tag being handled created an SVG or MathML
        # element, whose content ``HTMLParser`` must not read as raw text,
        # or an HTML element whose content must be raw text.
        self._opened_foreign = False
        self._opened_raw_text: str | None = None

    def open_element(self, tag: str, attrs: list[tuple[str, str | None]], namespace: Namespace) -> T:
        """Return the value to keep for an element the browser creates; ``open_elements`` holds its ancestors."""
        raise NotImplementedError

    def close_element(self, element: OpenElement[T]) -> None:
        """Run when the browser closes ``element``."""

    def unmatched_end_tag(self, tag: str) -> None:
        """
        Run for an end tag that matches no element this parser has open and nothing in the input stops it.

        In the full page it may close an element outside the HTML this
        parser read, so a check that reads only part of a page can refuse
        it. A void end tag such as ``</link>`` never comes here.
        """

    # ``HTMLParser`` calls these three; they turn its tags into elements.

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, self_closing=False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, self_closing=True)

    def handle_endtag(self, tag: str) -> None:
        current = self.open_elements[-1] if self.open_elements else None
        if current is None or current.namespace == "html":
            self._html_end(tag)
            return
        # Inside SVG or MathML. ``</br>`` and ``</p>`` close the SVG and
        # MathML elements and then act as in HTML.
        if tag in {"br", "p"}:
            self._close_foreign_content()
            self._html_end(tag)
            return
        # Any other end tag closes the nearest SVG or MathML element with its
        # name above the nearest HTML element; when there is none, the HTML
        # rules handle it.
        match = self._last(f"any:{tag}")
        nearest_html = self._last("html")
        if match > nearest_html:
            self._close_to(match)
        elif nearest_html >= 0:
            self._html_end(tag)
        else:
            self.unmatched_end_tag(tag)

    def parse_starttag(self, i: int) -> int:
        self._opened_foreign = False
        self._opened_raw_text = None
        end = super().parse_starttag(i)
        # ``HTMLParser`` switches to raw text after ``<style>`` and the other
        # raw-text elements, whatever namespace they are in; in SVG and
        # MathML a browser keeps reading tags there, so switch back.
        if self._opened_foreign and self.cdata_elem is not None:
            self.clear_cdata_mode()
        # Older Python releases read ``<textarea>`` and its kind as markup.
        elif self._opened_raw_text is not None and self.cdata_elem is None:
            self.set_cdata_mode(self._opened_raw_text)
        return end

    def parse_html_declaration(self, i: int) -> int:
        rawdata = self.rawdata
        if not rawdata.startswith("<![", i):
            return super().parse_html_declaration(i)
        current = self.open_elements[-1] if self.open_elements else None
        if current is None or current.namespace == "html" or not rawdata.startswith("<![CDATA[", i):
            # A browser reads ``<![CDATA[`` in HTML, and any other ``<![``, as
            # a comment that ends at the first ``>``, while Python releases
            # read some of them up to ``]]>``, which would hide the tags in
            # between.
            return self.parse_bogus_comment(i)
        # In SVG and MathML it is a CDATA section, read as text up to ``]]>``.
        close = rawdata.find("]]>", i + 9)
        if close < 0:
            return -1
        self.unknown_decl(rawdata[i + 3 : close])
        return close + 3

    def _start(self, tag: str, attrs: list[tuple[str, str | None]], *, self_closing: bool) -> None:
        namespace, holds_html = self._place(tag, attrs)
        if namespace == "html":
            if tag == "image":
                # A browser reads ``<image>`` in HTML as ``<img>``.
                tag = "img"
            in_template = self._last("html:template") >= 0
            if tag == "form" and self._form_open and not in_template:
                return
            # ``<input>`` and a nested ``<select>`` close an open select
            # first, and the browser drops the nested ``<select>`` tag, so
            # content after either one sits outside the select.
            if tag in {"input", "select"}:
                select = self._last("html:select")
                if select >= 0 and select >= self._last("scope"):
                    self._close_to(select)
                    if tag == "select":
                        return
            self._close_for_start_tag(tag)
            if tag == "form" and not in_template:
                self._form_open = True
            if tag in _HTML_RAW_TEXT and not self_closing:
                self._opened_raw_text = tag
        self._opened_foreign = namespace != "html"
        value = self.open_element(tag, attrs, namespace)
        self._push(OpenElement(tag, namespace, holds_html, value))
        # A void element has no content; in SVG and MathML the ``/`` of
        # ``<path/>`` closes the element too. In HTML the browser ignores
        # that ``/``, so ``<span/>`` stays open.
        if (namespace == "html" and tag in VOID_ELEMENTS) or (self_closing and namespace != "html"):
            self._close_to(len(self.open_elements) - 1)

    def _close_for_start_tag(self, tag: str) -> None:
        """Close the elements the browser closes before it creates the HTML element ``tag``."""
        if tag == "a":
            # An open ``<a>`` closes before a new one. When a block element
            # was opened inside it, the browser moves that block out instead,
            # which is not modeled, so the block stays open.
            match = self._last("html:a")
            if (
                match > max(self._last(f"html:{name}") for name in _FORMATTING_MARKERS)
                and self._last("special") < match
            ):
                self._close_to(match)
            return
        if tag in {"li", "dd", "dt"}:
            # The nearest open item of the same kind closes, unless a special
            # element other than ``<address>``, ``<div>`` or ``<p>`` sits
            # between.
            targets = ("li",) if tag == "li" else ("dd", "dt")
            match = max(self._last(f"html:{name}") for name in targets)
            if match >= 0 and match >= self._last("li-stop"):
                self._close_to(match)
        if tag in _CLOSES_PARAGRAPH:
            self._close_in_scope_paragraph()
        if tag in _HEADINGS and self.open_elements:
            current = self.open_elements[-1]
            if current.namespace == "html" and current.tag in _HEADINGS:
                self._close_to(len(self.open_elements) - 1)
        if tag == "button":
            open_button = self._in_scope({"button"}, extra_limits=())
            if open_button is not None and open_button >= 0:
                self._close_to(open_button)

    def _close_in_scope_paragraph(self) -> None:
        # A paragraph outside an open ``<select>`` stays open for content
        # placed inside the select.
        match = self._in_scope({"p"}, extra_limits=("button", "select"))
        if match is not None and match >= 0:
            self._close_to(match)

    def _place(self, tag: str, attrs: list[tuple[str, str | None]]) -> tuple[Namespace, bool]:
        """Return the namespace of a new element and whether its children are HTML, closing what the tag ends."""
        current = self.open_elements[-1] if self.open_elements else None
        if current is not None and current.namespace != "html" and not self._takes_html_child(current, tag):
            if tag == "svg" and current.namespace == "math" and current.tag == "annotation-xml":
                return "svg", False
            names = {name for name, _ in attrs}
            if tag not in _BREAKOUT_TAGS and not (tag == "font" and names & _BREAKOUT_FONT_ATTRIBUTES):
                return current.namespace, self._holds_html(current.namespace, tag, attrs)
            self._close_foreign_content()
        # HTML content: only ``<svg>`` and ``<math>`` start SVG or MathML.
        if tag == "svg":
            return "svg", False
        if tag == "math":
            return "math", False
        return "html", False

    @staticmethod
    def _takes_html_child(element: OpenElement[T], tag: str) -> bool:
        """Return whether a start tag inside the SVG or MathML ``element`` creates an HTML element."""
        if element.namespace == "math" and element.tag in _MATHML_TEXT_ELEMENTS:
            return tag not in _MATHML_TEXT_CHILDREN
        return element.holds_html

    @staticmethod
    def _holds_html(namespace: Namespace, tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        """Return whether a new SVG or MathML element's children follow the HTML rules."""
        if namespace == "svg":
            return tag in _SVG_HTML_CONTENT_ELEMENTS
        if tag == "annotation-xml":
            # The browser keeps the first ``encoding`` when the tag repeats it.
            encoding = dict(first_attribute_occurrences(attrs)).get("encoding") or ""
            return encoding.lower() in _HTML_ANNOTATION_ENCODINGS
        return False

    def _close_foreign_content(self) -> None:
        """Close SVG and MathML elements until an element whose children are HTML is current."""
        while self.open_elements:
            current = self.open_elements[-1]
            if (
                current.namespace == "html"
                or current.holds_html
                or (current.namespace == "math" and current.tag in _MATHML_TEXT_ELEMENTS)
            ):
                return
            self._close_to(len(self.open_elements) - 1)

    def _html_end(self, tag: str) -> None:
        """Apply the HTML rules for an end tag to the open elements."""
        # Inside an open ``<select>``, an end tag closes only an element
        # opened inside the select, so ``</div>`` whose ``<div>`` is outside
        # leaves the select and the elements around it open, apart from
        # ``</template>`` and the table end tags handled below.
        # ``</select>`` closes the select and everything opened inside it.
        select = self._last("html:select")
        if select >= 0 and select >= self._last("scope"):
            if tag == "select":
                self._close_to(select)
                return
            # ``</br>`` creates a ``<br>`` there too, and a ``</p>`` with no
            # paragraph opened inside the select creates an empty one inside
            # it, leaving a paragraph around the select open.
            if tag == "br":
                self._start("br", [], self_closing=False)
                return
            if tag == "p" and self._last("html:p") < select:
                self._start("p", [], self_closing=False)
                self._close_to(len(self.open_elements) - 1)
                return
            # ``</template>`` reaches the template rule below, which closes
            # the template around the select.
            if self._last(f"html:{tag}") < select and tag != "template":
                target = self._table_end_target(tag)
                if target is not None:
                    self._close_to(target)
                return
        if tag in VOID_ELEMENTS:
            # The browser ignores a void end tag, except that ``</br>`` creates
            # a ``<br>``.
            if tag == "br":
                self._start("br", [], self_closing=False)
            return
        if tag == "p":
            index = self._in_scope({"p"}, extra_limits=("button",))
            if index is not None and index >= 0:
                self._close_to(index)
            else:
                # With no paragraph to close, ``</p>`` creates an empty one.
                self._start("p", [], self_closing=False)
                self._close_to(len(self.open_elements) - 1)
            return
        if tag in _IGNORED_END_TAGS:
            return
        if tag == "template":
            # ``</template>`` closes the nearest open template, whatever is
            # open inside it.
            index = self._last("html:template")
            if index >= 0:
                self._close_to(index)
            else:
                self.unmatched_end_tag(tag)
            return
        if tag == "form" and self._last("html:template") < 0:
            self._end_form()
            return
        if tag in _SCOPED_END_TAGS or tag in _HEADINGS or tag == "li":
            targets = _HEADINGS if tag in _HEADINGS else {tag}
            index = self._in_scope(targets, extra_limits=("ol", "ul") if tag == "li" else ())
            if index is not None and index >= 0:
                self._close_to(index)
            elif index == -1:
                self.unmatched_end_tag(tag)
            return
        # Every other end tag closes the nearest HTML element with its name
        # unless a special element comes first. For a formatting element
        # such as ``</b>``, the browser then moves that special element out
        # rather than closing it, so ignoring the end tag keeps it open here
        # as it stays open in the browser.
        match = self._last(f"html:{tag}")
        special = self._last("special")
        if match >= 0 and match >= special:
            self._close_to(match)
        elif special < 0:
            self.unmatched_end_tag(tag)

    def _table_end_target(self, tag: str) -> int | None:
        """
        Return the position of the open element a table end tag closes from inside a cell or caption.

        A select inside a cell does not hide the cell from ``</td>``, so
        that end tag, and the end tag of the row, section or table around
        the cell, close the select along with the cell. ``None`` means the
        browser ignores the end tag.
        """
        if tag not in _TABLE_END_TAGS:
            return None
        cell = max(self._last("html:td"), self._last("html:th"), self._last("html:caption"))
        table = self._last("html:table")
        template = self._last("html:template")
        # The cell must belong to the nearest table, with no template
        # opened between them, or the browser is not reading a cell here.
        if cell < 0 or cell < table or cell < template:
            return None
        cell_tag = self.open_elements[cell].tag
        if tag == cell_tag:
            return cell
        if tag == "table":
            return table if table > template else None
        if cell_tag in {"td", "th"} and tag in {"tr", "tbody", "thead", "tfoot"}:
            # A row or section closes only when it sits inside the nearest
            # table. An implied ``<tbody>`` is not modeled; the browser then
            # stays inside the table until ``</table>``, which closes it here too.
            match = self._last(f"html:{tag}")
            return match if match > max(table, template) else None
        return None

    def _end_form(self) -> None:
        """Apply ``</form>`` outside a template: the browser removes only the form element."""
        self._form_open = False
        index = self._in_scope({"form"}, extra_limits=())
        if index == -1:
            self.unmatched_end_tag("form")
        if index is None or index < 0:
            return
        if index == len(self.open_elements) - 1:
            self._close_to(index)
            return
        # The elements opened inside the form stay open and stay inside it in
        # the page, so its entry stays as their ancestor, marked removed.
        element = self.open_elements[index]
        element.removed = True
        self.close_element(element)

    def _in_scope(self, targets: frozenset[str] | set[str], *, extra_limits: tuple[str, ...]) -> int | None:
        """
        Return the index of the nearest open HTML element named in ``targets``, if it is in scope.

        Return ``None`` when an element that limits the scope comes first,
        and ``-1`` when no open element matches and none limits the scope,
        so a match could only be outside the HTML this parser read.
        """
        match = max(self._last(f"html:{name}") for name in targets)
        limit = max([self._last("scope"), *(self._last(f"html:{name}") for name in extra_limits)])
        if match < 0:
            return None if limit >= 0 else -1
        # A target that limits the scope itself, such as ``<object>``, is
        # still found.
        return match if match >= limit else None

    def _last(self, key: str) -> int:
        """Return the position of the nearest open element filed under ``key``, or -1."""
        positions = self._positions.get(key)
        if not positions:
            return -1
        # A form that ``</form>`` removed stays in place but no longer counts.
        while positions and self.open_elements[positions[-1]].removed:
            positions.pop()
        return positions[-1] if positions else -1

    def _push(self, element: OpenElement[T]) -> None:
        keys = [f"any:{element.tag}"]
        if element.namespace == "html":
            keys += ["html", f"html:{element.tag}"]
            special = element.tag in _SPECIAL_ELEMENTS
            limits = element.tag in _HTML_SCOPE_LIMITS
        else:
            special = limits = (element.namespace, element.tag) in _FOREIGN_SCOPE_LIMITS
        if special:
            keys.append("special")
            if not (element.namespace == "html" and element.tag in {"address", "div", "p"}):
                keys.append("li-stop")
        if limits:
            keys.append("scope")
        element.keys = tuple(keys)
        position = len(self.open_elements)
        self.open_elements.append(element)
        for key in element.keys:
            self._positions.setdefault(key, []).append(position)

    def _close_to(self, index: int) -> None:
        """Close the element at ``index`` and every element opened inside it, innermost first."""
        while len(self.open_elements) > index:
            self._pop()
        # A form ``</form>`` removed leaves once nothing opened inside it is open.
        while self.open_elements and self.open_elements[-1].removed:
            self._pop()

    def _pop(self) -> None:
        element = self.open_elements.pop()
        position = len(self.open_elements)
        for key in element.keys:
            positions = self._positions[key]
            # ``_last`` may already have dropped a removed form's position.
            if positions and positions[-1] == position:
                positions.pop()
        if not element.removed:
            self.close_element(element)
