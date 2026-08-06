"""Targeted, source-preserving rewrites of actual HTML start tags."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True, slots=True)
class StartTag:
    """One parsed start tag and its exact span in the source document."""

    name: str
    attrs: tuple[tuple[str, str | None], ...]
    source: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class AttributeValue:
    """One exact attribute-value span inside a start tag."""

    name: str
    value: str
    start: int
    end: int


class _StartTagParser(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=False)
        self._line_offsets = [0]
        for line in source.splitlines(keepends=True):
            self._line_offsets.append(self._line_offsets[-1] + len(line))
        self.tags: list[StartTag] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)

    def _record(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        source = self.get_starttag_text()
        if source is None:
            return
        line, column = self.getpos()
        start = self._line_offsets[line - 1] + column
        self.tags.append(
            StartTag(
                name=tag,
                attrs=tuple(attrs),
                source=source,
                start=start,
                end=start + len(source),
            )
        )


def parse_start_tags(source: str) -> tuple[StartTag, ...]:
    """Parse real start tags while leaving script text and displayed code alone."""
    parser = _StartTagParser(source)
    parser.feed(source)
    parser.close()
    return tuple(parser.tags)


def rewrite_start_tags(source: str, transform: Callable[[StartTag], str]) -> str:
    """Rewrite selected start-tag spans without serializing the rest of the HTML."""
    rewritten = source
    for tag in reversed(parse_start_tags(source)):
        replacement = transform(tag)
        if replacement != tag.source:
            rewritten = rewritten[: tag.start] + replacement + rewritten[tag.end :]
    return rewritten


def rewrite_attribute_values(
    source: str,
    transform: Callable[[str, str], str],
) -> str:
    """Rewrite parsed attribute values in one start tag while preserving syntax."""
    rewritten = source
    for attribute in reversed(_attribute_values(source)):
        replacement = transform(attribute.name, attribute.value)
        if replacement != attribute.value:
            rewritten = rewritten[: attribute.start] + replacement + rewritten[attribute.end :]
    return rewritten


def append_attribute(tag_source: str, attribute: str) -> str:
    """Append a validated attribute declaration before a start tag's close."""
    closing = "/>" if tag_source.rstrip().endswith("/>") else ">"
    index = tag_source.rfind(closing)
    if index < 0:
        return tag_source
    return f"{tag_source[:index]} {attribute}{tag_source[index:]}"


def _attribute_values(source: str) -> tuple[AttributeValue, ...]:
    """Tokenize attribute value spans without matching text inside other values."""
    length = len(source)
    index = 1
    while index < length and source[index].isspace():
        index += 1
    while index < length and not source[index].isspace() and source[index] not in "/>":
        index += 1

    values: list[AttributeValue] = []
    while index < length:
        while index < length and source[index].isspace():
            index += 1
        if index >= length or source[index] == ">" or source.startswith("/>", index):
            break

        name_start = index
        while index < length and not source[index].isspace() and source[index] not in "=/>":
            index += 1
        name = source[name_start:index].casefold()
        if not name:
            index += 1
            continue
        while index < length and source[index].isspace():
            index += 1
        if index >= length or source[index] != "=":
            continue
        index += 1
        while index < length and source[index].isspace():
            index += 1
        if index >= length:
            break

        quote = source[index] if source[index] in {'"', "'"} else ""
        if quote:
            index += 1
            value_start = index
            while index < length and source[index] != quote:
                index += 1
            value_end = index
            if index < length:
                index += 1
        else:
            value_start = index
            while index < length and not source[index].isspace() and source[index] != ">":
                index += 1
            value_end = index
        values.append(
            AttributeValue(
                name=name,
                value=source[value_start:value_end],
                start=value_start,
                end=value_end,
            )
        )
    return tuple(values)
