"""Conservative Citry template-region discovery and coordinate adapters."""

from __future__ import annotations

import ast
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from typing import Protocol

from citry import (
    LspPosition,
    LspRange,
    PythonComponentAssetKind,
    PythonTemplateSourceMap,
    discover_python_component_assets,
    discover_python_templates,
)


class TemplateSourceMap(Protocol):
    """Coordinate behavior consumed by diagnostics and editor features."""

    template_source: str

    def map_range(self, start_index: int, end_index: int) -> LspRange: ...

    def range_is_unambiguous(self, start_index: int, end_index: int) -> bool: ...

    def parser_index_at(self, position: LspPosition) -> int | None: ...


@dataclass(frozen=True, slots=True)
class TemplateRegion:
    """One definite authored template region in a host document."""

    key: str
    component_name: str | None
    source_map: TemplateSourceMap
    ast_proven: bool = True


@dataclass(frozen=True, slots=True)
class RegionDiscovery:
    """Current regions and whether Python parsed completely."""

    regions: tuple[TemplateRegion, ...]
    valid_python: bool


@dataclass(frozen=True, slots=True)
class CssRegion:
    """One registry-associated authored CSS source region."""

    key: str
    component_name: str | None
    source_map: TemplateSourceMap
    ast_proven: bool = True


@dataclass(frozen=True, slots=True)
class JsRegion:
    """One registry-associated authored JavaScript source region."""

    key: str
    component_name: str | None
    source_map: TemplateSourceMap
    ast_proven: bool = True


@dataclass(frozen=True, slots=True)
class MessagesRegion:
    """One direct component ``messages`` literal containing Fluent source."""

    key: str
    component_name: str
    source_map: TemplateSourceMap


class StandaloneTemplateSourceMap:
    """Map a complete `citry-html` document directly to LSP positions."""

    __slots__ = ("_byte_boundaries", "_line_starts", "template_source")

    def __init__(self, source: str) -> None:
        self.template_source = source
        boundaries = [0]
        for char in source:
            boundaries.append(boundaries[-1] + len(char.encode("utf-8")))
        self._byte_boundaries = tuple(boundaries)
        self._line_starts = _line_starts(source)

    def map_range(self, start_index: int, end_index: int) -> LspRange:
        start = _byte_boundary(self._byte_boundaries, start_index)
        end = _byte_boundary(self._byte_boundaries, end_index)
        if end < start:
            msg = "end_index precedes start_index"
            raise ValueError(msg)
        return LspRange(
            _offset_to_lsp(self.template_source, self._line_starts, start),
            _offset_to_lsp(self.template_source, self._line_starts, end),
        )

    def range_is_unambiguous(self, start_index: int, end_index: int) -> bool:
        """Validate a range and report that a standalone document is contiguous."""
        self.map_range(start_index, end_index)
        return True

    def parser_index_at(self, position: LspPosition) -> int | None:
        offset = _lsp_to_offset(self.template_source, self._line_starts, position)
        return self._byte_boundaries[offset]


def standalone_region(source: str) -> TemplateRegion:
    """Return the whole document as one explicit Citry template region."""
    return TemplateRegion("standalone", None, StandaloneTemplateSourceMap(source))


def discover_python_regions(source: str) -> RegionDiscovery:
    """Adapt Citry's shared conservative discovery for interactive editing."""
    discovery = discover_python_templates(source, recover_incomplete=True)
    return RegionDiscovery(
        tuple(
            TemplateRegion(
                region.component_name,
                region.component_name,
                region.source_map,
                ast_proven=discovery.valid_python,
            )
            for region in discovery.regions
        ),
        valid_python=discovery.valid_python,
    )


def discover_python_css_regions(source: str) -> tuple[CssRegion, ...]:
    """Return direct component ``css`` literals from valid Python source."""
    try:
        discovery = discover_python_component_assets(source)
    except (SyntaxError, TypeError, ValueError):
        return ()
    return tuple(
        CssRegion(
            f"css:{region.component_name}",
            region.component_name,
            region.source_map,
        )
        for region in discovery.regions
        if region.kind is PythonComponentAssetKind.CSS
    )


def discover_python_js_regions(source: str) -> tuple[JsRegion, ...]:
    """Return direct component ``js`` literals from valid Python source."""
    try:
        discovery = discover_python_component_assets(source)
    except (SyntaxError, TypeError, ValueError):
        return ()
    return tuple(
        JsRegion(
            f"js:{region.component_name}",
            region.component_name,
            region.source_map,
        )
        for region in discovery.regions
        if region.kind is PythonComponentAssetKind.JS
    )


def discover_python_messages_regions(source: str) -> tuple[MessagesRegion, ...]:
    """Return direct static ``messages`` literals from valid Python source."""
    try:
        module = ast.parse(source)
    except (SyntaxError, TypeError, ValueError):
        return ()
    regions: list[MessagesRegion] = []
    for node in ast.walk(module):
        if not isinstance(node, ast.ClassDef):
            continue
        declarations: list[ast.expr] = []
        for statement in node.body:
            matches = False
            value: ast.expr | None = None
            if isinstance(statement, ast.Assign):
                matches = any(isinstance(target, ast.Name) and target.id == "messages" for target in statement.targets)
                value = statement.value
            elif isinstance(statement, ast.AnnAssign):
                matches = isinstance(statement.target, ast.Name) and statement.target.id == "messages"
                value = statement.value
            if matches and value is not None:
                declarations.append(value)
        if not declarations:
            continue
        selected = declarations[-1]
        if not isinstance(selected, ast.Constant) or type(selected.value) is not str:
            continue
        try:
            source_map = PythonTemplateSourceMap.from_ast(source, selected)
        except (TypeError, ValueError):
            continue
        regions.append(MessagesRegion(f"messages:{node.name}", node.name, source_map))
    return tuple(regions)


def standalone_css_region(source: str) -> CssRegion:
    """Treat one registry-owned CSS file as its own authored region."""
    return CssRegion("css:standalone", None, StandaloneTemplateSourceMap(source))


def standalone_js_region(source: str) -> JsRegion:
    """Treat one registry-owned JavaScript file as its authored region."""
    return JsRegion("js:standalone", None, StandaloneTemplateSourceMap(source))


def python_messages_source_map(source: str, component_name: str) -> PythonTemplateSourceMap | None:
    """Map one direct inline ``messages`` literal named by a compiled origin."""
    try:
        module = ast.parse(source)
    except (SyntaxError, TypeError, ValueError):
        return None
    candidates: list[ast.Constant] = []
    for node in ast.walk(module):
        if not isinstance(node, ast.ClassDef) or node.name != component_name:
            continue
        declarations: list[ast.expr] = []
        for statement in node.body:
            if isinstance(statement, ast.Assign):
                matches = any(isinstance(target, ast.Name) and target.id == "messages" for target in statement.targets)
            elif isinstance(statement, ast.AnnAssign):
                matches = isinstance(statement.target, ast.Name) and statement.target.id == "messages"
            else:
                continue
            if matches and statement.value is not None:
                declarations.append(statement.value)
        if declarations:
            selected = declarations[-1]
            if isinstance(selected, ast.Constant) and type(selected.value) is str:
                candidates.append(selected)
    if len(candidates) != 1:
        return None
    try:
        return PythonTemplateSourceMap.from_ast(source, candidates[0])
    except (TypeError, ValueError):
        return None


def css_region_at_position(regions: tuple[CssRegion, ...], position: LspPosition) -> CssRegion | None:
    """Return the authored CSS region containing an LSP position."""
    for region in regions:
        try:
            if region.source_map.parser_index_at(position) is not None:
                return region
        except ValueError:
            continue
    return None


def js_region_at_position(regions: tuple[JsRegion, ...], position: LspPosition) -> JsRegion | None:
    """Return the authored JavaScript region containing an LSP position."""
    for region in regions:
        try:
            if region.source_map.parser_index_at(position) is not None:
                return region
        except ValueError:
            continue
    return None


def region_at_position(regions: tuple[TemplateRegion, ...], position: LspPosition) -> TemplateRegion | None:
    """Return the authored template region containing an LSP position."""
    for region in regions:
        try:
            if region.source_map.parser_index_at(position) is not None:
                return region
        except ValueError:
            continue
    return None


def parser_char_index(source: str, byte_index: int) -> int:
    """Convert a UTF-8 parser boundary into a Python character index."""
    encoded = source.encode("utf-8")
    if byte_index < 0 or byte_index > len(encoded):
        msg = "parser byte index is outside the template"
        raise ValueError(msg)
    try:
        return len(encoded[:byte_index].decode("utf-8"))
    except UnicodeDecodeError as exc:
        msg = "parser byte index splits a UTF-8 code point"
        raise ValueError(msg) from exc


def document_offset_at(source: str, position: LspPosition) -> int:
    """Convert one UTF-16 LSP position to a Python string offset."""
    return _lsp_to_offset(source, _line_starts(source), position)


def document_range_for_offsets(source: str, start: int, end: int) -> LspRange:
    """Convert one half-open Python string-offset range to LSP coordinates."""
    if start < 0 or end < start or end > len(source):
        msg = "document offsets form an invalid range"
        raise ValueError(msg)
    starts = _line_starts(source)
    return LspRange(
        _offset_to_lsp(source, starts, start),
        _offset_to_lsp(source, starts, end),
    )


def _line_starts(source: str) -> tuple[int, ...]:
    starts = [0]
    for index, char in enumerate(source):
        if char == "\n":
            starts.append(index + 1)
    return tuple(starts)


def _byte_boundary(boundaries: tuple[int, ...], byte_index: int) -> int:
    index = bisect_left(boundaries, byte_index)
    if index == len(boundaries) or boundaries[index] != byte_index:
        msg = "parser byte index is outside the template or splits a UTF-8 code point"
        raise ValueError(msg)
    return index


def _offset_to_lsp(source: str, line_starts: tuple[int, ...], offset: int) -> LspPosition:
    line = bisect_right(line_starts, offset) - 1
    prefix = source[line_starts[line] : offset]
    return LspPosition(line, len(prefix.encode("utf-16-le")) // 2)


def _lsp_to_offset(source: str, line_starts: tuple[int, ...], position: LspPosition) -> int:
    if position.line < 0 or position.character < 0 or position.line >= len(line_starts):
        msg = "LSP position is outside the document"
        raise ValueError(msg)
    start = line_starts[position.line]
    end = line_starts[position.line + 1] if position.line + 1 < len(line_starts) else len(source)
    units = 0
    for offset in range(start, end):
        if units == position.character:
            return offset
        units += 2 if ord(source[offset]) > 0xFFFF else 1
        if units > position.character:
            msg = "LSP position splits a UTF-16 surrogate pair"
            raise ValueError(msg)
    if units == position.character:
        return end
    msg = "LSP position is outside the document line"
    raise ValueError(msg)


__all__ = [
    "CssRegion",
    "JsRegion",
    "RegionDiscovery",
    "StandaloneTemplateSourceMap",
    "TemplateRegion",
    "TemplateSourceMap",
    "css_region_at_position",
    "discover_python_css_regions",
    "discover_python_js_regions",
    "discover_python_regions",
    "document_offset_at",
    "document_range_for_offsets",
    "js_region_at_position",
    "parser_char_index",
    "region_at_position",
    "standalone_css_region",
    "standalone_js_region",
    "standalone_region",
]
