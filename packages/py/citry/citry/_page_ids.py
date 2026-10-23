"""
Development check: the same ``id`` on two elements of one page.

The ``citry.template.duplicate-id`` rule finds an ``id`` written twice in one
template. It cannot see the same ``id`` coming from two components, or from
one component that renders twice, because that depends on the whole page.
With ``Citry(mode="development")``, serialization hands each component's own
HTML to this check, which counts every ``id`` across the page and warns when
one appears more than once. Production serialization never creates the
check, so it costs nothing there.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from citry._caller_warnings import warn_at_caller
from citry.util.html import LongReferenceSafeParser

# Elements whose start tag never has a matching end tag in the HTML.
_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
)

# Vue decides in the browser whether an element with one of these attributes
# exists, or how many times it repeats, so an id on it or inside it is not
# counted. A Citry `<c-if>` or `<c-for>` has already run when the HTML is
# written, so only the branches and rows that render are in it.
_BROWSER_DECIDED_ATTRIBUTES = frozenset({"v-if", "v-else-if", "v-else", "v-for"})

# Elements whose contents never become elements of the page: a <template>'s
# contents stay inert until a script uses them, and a browser that runs
# scripts reads <noscript> as text.
_INERT_CONTENT_TAGS = frozenset({"template", "noscript"})

# The attribute serialization writes on the <template> that stands in for a
# child component's HTML.
_CHILD_PLACEHOLDER_ATTRIBUTE = "c-render-id"


class _IdScanner(LongReferenceSafeParser):
    """Collect the ``id`` values a browser would register for one piece of HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        # Open elements as (tag, skipped). An element is skipped when it, or
        # an element around it, cannot be counted.
        self._open: list[tuple[str, bool]] = []
        self.ids: list[str] = []
        # Child placeholders that sit where the browser decides whether they
        # exist, such as inside a `v-if` branch; those children's ids are
        # not counted either.
        self.uncounted_children: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        names = {name for name, _ in attrs}
        decided = (bool(self._open) and self._open[-1][1]) or bool(names & _BROWSER_DECIDED_ATTRIBUTES)
        if tag == "template":
            child = next((value for name, value in attrs if name == _CHILD_PLACEHOLDER_ATTRIBUTE), None)
            if child and decided:
                self.uncounted_children.add(child)
        skipped = decided or tag in _INERT_CONTENT_TAGS
        if not skipped:
            for name, value in attrs:
                # An empty id is no id at all, so it cannot repeat.
                if name == "id" and value:
                    self.ids.append(value)
        if tag not in _VOID_TAGS:
            self._open.append((tag, skipped))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # `<svg><stop id="a"/></svg>` closes itself, so it must not stay open.
        self.handle_starttag(tag, attrs)
        if tag not in _VOID_TAGS and self._open and self._open[-1][0] == tag:
            self._open.pop()

    def handle_endtag(self, tag: str) -> None:
        # The browser closes elements whose end tag the HTML leaves out (a
        # `<p>` or `<li>`) when an outer element ends, so pop up to the match.
        for index in range(len(self._open) - 1, -1, -1):
            if self._open[index][0] == tag:
                del self._open[index:]
                return


@dataclass(slots=True)
class _Writer:
    """One component occurrence that wrote ids, and how many times each."""

    component: str
    origin: str | None
    counts: dict[str, int] = field(default_factory=dict)


class PageIdCheck:
    """Count the ids each component writes on one page and warn about repeats."""

    __slots__ = ("_writers",)

    def __init__(self) -> None:
        self._writers: list[_Writer] = []

    def add(self, html: str, component: str, origin: str | None) -> frozenset[str]:
        """
        Count the ids in one component's own HTML.

        ``html`` must hold only that component's output: serialization passes
        each component's HTML with its children's HTML replaced by
        ``<template c-render-id="...">`` placeholders, so each child counts
        its own ids.

        Returns:
            The ids of the child placeholders the browser may never show,
            such as one inside a ``v-if`` branch. The caller must not count
            those children, or anything inside them.

        """
        scanner = _IdScanner()
        try:
            scanner.feed(html)
            scanner.close()
        except Exception:  # noqa: BLE001 - a development check must never break a render
            return frozenset()
        uncounted = frozenset(scanner.uncounted_children)
        if not scanner.ids:
            return uncounted
        writer = _Writer(component, origin)
        for value in scanner.ids:
            writer.counts[value] = writer.counts.get(value, 0) + 1
        self._writers.append(writer)
        return uncounted

    def report(self) -> None:
        """Warn once, listing every id that appears more than once on the page."""
        totals: dict[str, int] = {}
        for writer in self._writers:
            for value, count in writer.counts.items():
                totals[value] = totals.get(value, 0) + count
        repeated = [value for value, total in totals.items() if total > 1]
        if not repeated:
            return
        lines = []
        # Sorted, so the same page always gives the same message and a
        # repeated warning is shown once.
        for value in sorted(repeated):
            # Name each component once, with how many elements its
            # occurrences wrote when that is more than one.
            by_component: dict[tuple[str, str | None], int] = {}
            for writer in self._writers:
                written = writer.counts.get(value, 0)
                if written:
                    key = (writer.component, writer.origin)
                    by_component[key] = by_component.get(key, 0) + written
            places = ", ".join(
                _describe_place(component, origin, total)
                for (component, origin), total in sorted(by_component.items(), key=lambda item: item[0][0])
            )
            lines.append(f'- id "{value}": {places}')
        body = "\n".join(lines)
        noun = "id" if len(repeated) == 1 else "ids"
        message = (
            f"Citry found {len(repeated)} {noun} used by more than one element on one page:\n{body}\n"
            "A browser uses only the first element with an id, so a label, a link, or a script that "
            "points at it reaches the wrong element. Give each element its own id: rename one, or, in "
            "a component used more than once, build the id from a value the component receives. "
            'Citry runs this check only with Citry(mode="development").'
        )
        # The author fixes this in a component, so point at their render or
        # serialize call, not at whichever Citry frame noticed it.
        warn_at_caller(message, RuntimeWarning)


def _describe_place(component: str, origin: str | None, count: int) -> str:
    """Name one component in the warning, with its element count and template when known."""
    details = [f"{count} elements"] if count > 1 else []
    if origin:
        details.append(origin)
    return f"{component} ({', '.join(details)})" if details else component
