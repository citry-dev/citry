"""Tests for conservative region discovery and coordinate conversion."""

from __future__ import annotations

import pytest

from citry import LspPosition, LspRange
from citry_lsp.regions import discover_python_regions, parser_char_index, region_at_position, standalone_region


def test_valid_python_discovers_only_proven_component_literal():
    source = (
        "from citry import Component\n"
        "class Card(Component):\n"
        '    template = """é<c-panel />"""\n'
        "class Unrelated:\n"
        '    template = """<broken>"""\n'
    )

    discovery = discover_python_regions(source)

    assert discovery.valid_python is True
    assert len(discovery.regions) == 1
    assert discovery.regions[0].key == "Card"
    assert discovery.regions[0].source_map.template_source == "é<c-panel />"


def test_broken_python_recovers_exact_unfinished_triple_literal():
    source = 'from citry import Component\nclass Card(Component):\n    template = r"""<c-panel title="x"'

    discovery = discover_python_regions(source)

    assert discovery.valid_python is False
    assert len(discovery.regions) == 1
    assert discovery.regions[0].source_map.template_source == '<c-panel title="x"'


def test_broken_unrelated_python_is_not_claimed():
    source = 'class Card:\n    template = """<c-panel />'

    assert discover_python_regions(source).regions == ()


def test_standalone_map_uses_utf16_positions():
    region = standalone_region("😀<c-card />")
    start = len("😀".encode())
    end = start + len(b"<c-card />")

    assert region.source_map.map_range(start, end) == LspRange(
        LspPosition(0, 2),
        LspPosition(0, 12),
    )
    assert region.source_map.parser_index_at(LspPosition(0, 2)) == start


def test_coordinate_adapters_reject_non_boundaries_and_invalid_ranges():
    region = standalone_region("😀x")

    with pytest.raises(ValueError, match="precedes"):
        region.source_map.map_range(len("😀".encode()), 0)
    with pytest.raises(ValueError, match="splits a UTF-8"):
        region.source_map.map_range(1, len("😀".encode()))
    with pytest.raises(ValueError, match="outside the template"):
        parser_char_index("x", 2)
    with pytest.raises(ValueError, match="splits a UTF-8"):
        parser_char_index("😀", 1)


def test_position_lookup_skips_invalid_utf16_positions():
    region = standalone_region("😀x")

    assert region_at_position((region,), LspPosition(0, 1)) is None
    with pytest.raises(ValueError, match="outside the document"):
        region.source_map.parser_index_at(LspPosition(-1, 0))
    with pytest.raises(ValueError, match="outside the document line"):
        region.source_map.parser_index_at(LspPosition(0, 99))
