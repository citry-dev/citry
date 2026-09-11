"""Browser edits retain authored positions after Python literal decoding."""

from __future__ import annotations

import ast

from lsprotocol import types

from citry import PythonTemplateSourceMap
from citry_lsp.engine import _browser_source_mappings
from citry_lsp.regions import StandaloneTemplateSourceMap


def _mappings(source: str):
    assignment = ast.parse(source).body[0]
    assert isinstance(assignment, ast.Assign)
    source_map = PythonTemplateSourceMap.from_ast(source, assignment.value)
    return source_map, _browser_source_mappings(source_map, 0, source_map.template_source, "// preamble\n")


def test_dedented_lines_keep_independent_source_columns_and_utf16_positions():
    source_map, mappings = _mappings('js = """\n    // 😀\n      data.a\n    """')
    assert source_map.template_source == "\n// 😀\n  data.a\n"
    member = next(mapping for mapping in mappings if mapping.virtual_range.start == types.Position(3, 0))
    assert member.virtual_range == types.Range(types.Position(3, 0), types.Position(3, 8))
    assert member.source_range == types.Range(types.Position(2, 4), types.Position(2, 12))
    comment = next(mapping for mapping in mappings if mapping.virtual_range.start == types.Position(2, 0))
    assert comment.virtual_range.end == types.Position(2, 5)
    assert comment.source_range.end == types.Position(1, 9)


def test_python_escape_is_a_separate_mapping_between_unchanged_runs():
    _, mappings = _mappings('js = "data.a\\nconsole.log(data.b)"')
    newline = next(mapping for mapping in mappings if mapping.virtual_range.start == types.Position(1, 6))
    assert newline.virtual_range.end == types.Position(2, 0)
    assert newline.source_range == types.Range(types.Position(0, 12), types.Position(0, 14))
    following = next(mapping for mapping in mappings if mapping.virtual_range.start == types.Position(2, 0))
    assert following.source_range.start == types.Position(0, 14)


def test_implicitly_concatenated_literals_decline_a_single_browser_edit_map():
    _, mappings = _mappings('js = "data." "a"')
    assert mappings == ()


def test_standalone_line_endings_have_only_valid_editor_boundaries():
    for newline in ("\r\n", "\r", "\n"):
        authored = f"one{newline}two"
        mappings = _browser_source_mappings(StandaloneTemplateSourceMap(authored), 0, authored, "// preamble\n")
        assert len(mappings) == 3
        assert mappings[1].source_range == types.Range(types.Position(0, 3), types.Position(1, 0))
        assert mappings[1].virtual_range == types.Range(types.Position(1, 3), types.Position(2, 0))
        assert mappings[2].source_range == types.Range(types.Position(1, 0), types.Position(1, 3))


def test_empty_literal_retains_a_completion_insertion_anchor():
    _, mappings = _mappings('js = ""')
    assert len(mappings) == 1
    assert mappings[0].source_range == types.Range(types.Position(0, 6), types.Position(0, 6))
    assert mappings[0].virtual_range == types.Range(types.Position(1, 0), types.Position(1, 0))
