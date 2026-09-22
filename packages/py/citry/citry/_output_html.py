"""Browser-state-aware settled HTML facts with exact source byte spans."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict, cast

from citry_core.html_transform import scan_output_html as _scan_output_html


class _NativeTag(TypedDict):
    name: str
    start: int
    end: int
    name_start: int
    name_end: int
    element_end: int
    element_end_start: int
    attributes: list[tuple[str, str, int, int, int, int, bool]]


@dataclass(frozen=True, slots=True)
class OutputToken:
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class OutputText:
    content: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class OutputAttr:
    key: OutputText
    inner_value: OutputText | None


@dataclass(frozen=True, slots=True)
class OutputTag:
    token: OutputToken
    name: OutputText
    attrs: tuple[OutputAttr, ...] = ()


@dataclass(slots=True)
class OutputNode:
    start_tag: OutputTag
    body: OutputTemplate = field(default_factory=lambda: OutputTemplate())
    end_tag: OutputTag | None = None


@dataclass(slots=True)
class OutputTemplate:
    elements: list[OutputNode] = field(default_factory=list)


def scan_output_html(source: str) -> OutputTemplate:
    """Return flat source-token facts using HTML5 tree-builder tokenizer feedback."""
    template = OutputTemplate()
    for raw in cast("list[_NativeTag]", _scan_output_html(source)):
        attrs = tuple(
            OutputAttr(
                OutputText(name, name_start, name_end),
                OutputText(value, value_start, value_end) if has_value else None,
            )
            for name, value, name_start, name_end, value_start, value_end, has_value in raw["attributes"]
        )
        start_tag = OutputTag(
            OutputToken(raw["start"], raw["end"]),
            OutputText(raw["name"], raw["name_start"], raw["name_end"]),
            attrs,
        )
        end_tag = None
        if raw["element_end"] > raw["end"]:
            end_tag = OutputTag(OutputToken(raw["element_end_start"], raw["element_end"]), start_tag.name)
        template.elements.append(OutputNode(start_tag, end_tag=end_tag))
    return template


__all__ = ["OutputAttr", "OutputNode", "OutputTemplate", "scan_output_html"]
