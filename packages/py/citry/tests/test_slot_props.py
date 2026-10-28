"""Reading Vue slot props: the outlets a component declares and the names a scoped fill reads."""

from __future__ import annotations

import pytest

from citry._slot_props import (
    SlotPatternKey,
    camelize,
    lint_unknown_slot_props,
    outlet_prop_names,
    outlets_for_slot,
    pattern_keys,
    scoped_fills,
    slot_outlets,
    slot_prop_name,
    unknown_slot_props_for,
)
from citry.nodes import _camelize
from citry_core.template_parser import parse_template


def _outlets(source: str):
    return slot_outlets(parse_template(source), parse_nested=parse_template)


def _fills(source: str):
    return scoped_fills(parse_template(source), parse_nested=parse_template)


def _text(source: str, start: int, end: int) -> str:
    # Spans are UTF-8 byte offsets, so slice the encoded source.
    return source.encode()[start:end].decode()


def _key_texts(pattern: str, start_index: int = 0) -> list[str]:
    keys = pattern_keys(pattern, start_index)
    assert keys is not None
    return [_text(" " * start_index + pattern, key.start_index, key.end_index) for key in keys]


class TestNames:
    def test_camelize_follows_vue(self):
        assert camelize("row") == "row"
        assert camelize("row-data") == "rowData"
        assert camelize("a-b-c") == "aBC"

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("row-data", "rowData"),
            # A leading dash and a doubled dash are the edge cases where a
            # second implementation would drift from the render path.
            ("-row", "Row"),
            ("a--b", "a-B"),
            ("a-1", "a1"),
        ],
    )
    def test_camelize_names_a_prop_as_the_render_path_does(self, name, expected):
        # The editor and `citry check` must name a prop as the page passes it,
        # so the two functions have to agree on every input.
        assert camelize(name) == _camelize(name)
        assert camelize(name) == expected

    @pytest.mark.parametrize(
        ("attribute", "expected"),
        [
            (":row", "row"),
            ("v-bind:row-data", "row-data"),
            # Spellings that do not pass one named prop.
            ("row", None),
            (":", None),
            (":[name]", None),
            (":row.prop", None),
            ("c-row", None),
        ],
    )
    def test_slot_prop_name_accepts_only_the_two_prop_spellings(self, attribute, expected):
        assert slot_prop_name(attribute) == expected


class TestSlotOutlets:
    def test_props_are_camelized_and_both_spellings_are_read(self):
        source = '<c-slot name="item" :row-data="a" v-bind:row="b" />'

        (outlet,) = _outlets(source)

        assert outlet.slot == "item"
        assert [(prop.name, prop.attribute, prop.source) for prop in outlet.props] == [
            ("rowData", ":row-data", "a"),
            ("row", "v-bind:row", "b"),
        ]
        assert outlet_prop_names((outlet,)) == frozenset({"rowData", "row"})

    def test_expression_spans_point_at_the_expression_text(self):
        source = '<c-slot name="item" :row-data="a" v-bind:row="b" />'

        (outlet,) = _outlets(source)

        assert [(prop.start_index, prop.end_index) for prop in outlet.props] == [(31, 32), (46, 47)]
        assert [_text(source, prop.start_index, prop.end_index) for prop in outlet.props] == ["a", "b"]
        # The outlet's own span is the tag name.
        assert (outlet.start_index, outlet.end_index) == (1, 7)
        assert _text(source, outlet.start_index, outlet.end_index) == "c-slot"

    def test_a_slot_without_a_name_serves_default(self):
        (outlet,) = _outlets("<c-slot />")

        assert outlet.slot == "default"
        assert outlet.props == ()

    def test_attributes_that_pass_no_prop_are_not_props(self):
        (outlet,) = _outlets('<c-slot name="item" c-row="row" />')

        assert outlet.slot == "item"
        assert outlet.props == ()

    @pytest.mark.parametrize("attribute", ['c-name="slot_name"', 'c-bind="attrs"'])
    def test_a_dynamic_name_gives_slot_none(self, attribute):
        (outlet,) = _outlets(f'<c-slot {attribute} :row="r" />')

        assert outlet.slot is None

    def test_outlets_are_found_in_source_order_inside_nested_tags(self):
        source = (
            '<c-slot name="a" :x="x" /><div><c-if cond="ok"><c-slot name="b" :y="y" /></c-if></div><c-slot name="c" />'
        )

        assert [(outlet.slot, [prop.name for prop in outlet.props]) for outlet in _outlets(source)] == [
            ("a", ["x"]),
            ("b", ["y"]),
            ("c", []),
        ]

    def test_an_outlet_inside_a_template_valued_attribute_is_found_with_template_offsets(self):
        source = "<c-card c-header=\"<><c-slot name='in' :row='row' /></>\" />"

        (outlet,) = _outlets(source)

        assert outlet.slot == "in"
        assert (outlet.start_index, outlet.end_index) == (21, 27)
        assert _text(source, outlet.start_index, outlet.end_index) == "c-slot"
        (prop,) = outlet.props
        assert (prop.start_index, prop.end_index) == (44, 47)
        assert _text(source, prop.start_index, prop.end_index) == "row"

    def test_offsets_are_bytes_after_non_ascii_text(self):
        source = "<p>é</p><c-card c-header=\"<><c-slot name='in' :row='row' /></>\" />"

        (outlet,) = _outlets(source)

        # The "é" takes two bytes, so the offsets are one larger than the
        # character index would be.
        assert (outlet.start_index, outlet.end_index) == (30, 36)
        (prop,) = outlet.props
        assert (prop.start_index, prop.end_index) == (53, 56)
        assert _text(source, prop.start_index, prop.end_index) == "row"


class TestOutletsForSlot:
    def test_returns_the_outlets_that_serve_the_slot(self):
        outlets = _outlets('<c-slot name="a" :x="1" /><c-slot name="a" :y-z="2" /><c-slot name="b" />')

        serving = outlets_for_slot(outlets, "a")

        assert serving is not None
        assert [outlet.slot for outlet in serving] == ["a", "a"]
        # Two outlets of one slot merge their props.
        assert outlet_prop_names(serving) == frozenset({"x", "yZ"})

    def test_an_outlet_without_props_still_serves_its_slot(self):
        outlets = _outlets('<c-slot name="a" :x="1" /><c-slot name="b" />')

        serving = outlets_for_slot(outlets, "b")

        assert serving is not None
        assert outlet_prop_names(serving) == frozenset()

    def test_a_dynamic_outlet_makes_every_slot_unknown(self):
        outlets = _outlets('<c-slot name="a" :x="1" /><c-slot c-name="slot_name" />')

        assert outlets_for_slot(outlets, "a") is None
        assert outlets_for_slot(outlets, "other") is None

    def test_no_outlet_for_the_slot_gives_none(self):
        outlets = _outlets('<c-slot name="a" :x="1" />')

        assert outlets_for_slot(outlets, "missing") is None
        assert outlets_for_slot((), "default") is None


class TestScopedFills:
    def test_finds_the_owner_tag_through_control_flow(self):
        source = (
            "<c-Table>"
            '<c-if cond="ok"><c-for each="a in b">'
            '<c-fill name="item" v-slot="{ row }">x</c-fill>'
            "</c-for></c-if>"
            "</c-Table>"
        )

        (fill,) = _fills(source)

        assert (fill.tag, fill.slot, fill.pattern) == ("c-Table", "item", "{ row }")
        assert _text(source, fill.pattern_start_index, fill.pattern_end_index) == "{ row }"
        assert fill.keys is not None
        assert [(key.name, key.local) for key in fill.keys] == [("row", "row")]
        assert [_text(source, key.start_index, key.end_index) for key in fill.keys] == ["row"]

    def test_the_nearest_component_call_owns_the_fill(self):
        (fill,) = _fills('<c-Outer><c-Inner><c-fill name="a" v-slot="{ x }">y</c-fill></c-Inner></c-Outer>')

        assert fill.tag == "c-Inner"

    def test_a_fill_without_v_slot_is_not_scoped(self):
        assert _fills('<c-Table><c-fill name="item">x</c-fill></c-Table>') == ()

    def test_a_fill_named_by_c_name_is_skipped(self):
        assert _fills('<c-Table><c-fill c-name="n" v-slot="{ row }">x</c-fill></c-Table>') == ()

    def test_a_fill_whose_rightmost_name_is_c_bind_is_skipped(self):
        assert _fills('<c-Table><c-fill name="a" c-bind="attrs" v-slot="{ row }">x</c-fill></c-Table>') == ()

    def test_a_static_name_to_the_right_of_c_bind_wins(self):
        (fill,) = _fills('<c-Table><c-fill c-bind="attrs" name="a" v-slot="{ row }">x</c-fill></c-Table>')

        assert fill.slot == "a"

    def test_a_single_name_pattern_has_no_keys(self):
        (fill,) = _fills('<c-Table><c-fill name="item" v-slot="props">x</c-fill></c-Table>')

        assert fill.pattern == "props"
        assert fill.keys is None

    def test_key_spans_are_offset_into_the_template(self):
        source = '<p>é</p><c-Table><c-fill name="item" v-slot="{ row, extra }">x</c-fill></c-Table>'

        (fill,) = _fills(source)

        assert fill.keys is not None
        assert [_text(source, key.start_index, key.end_index) for key in fill.keys] == ["row", "extra"]


class TestPatternKeys:
    def test_shorthand_keys(self):
        assert pattern_keys("{ row, index }") == (
            SlotPatternKey("row", 2, 5, "row"),
            SlotPatternKey("index", 7, 12, "index"),
        )

    def test_a_rename_reports_the_key_and_binds_the_local_name(self):
        assert pattern_keys("{ row: item }") == (SlotPatternKey("row", 2, 5, "item"),)

    def test_a_default_binds_the_key_name(self):
        assert pattern_keys("{ row = 1 }") == (SlotPatternKey("row", 2, 5, "row"),)

    def test_a_rename_with_a_default_binds_the_renamed_name(self):
        assert pattern_keys("{ row: item = 1 }") == (SlotPatternKey("row", 2, 5, "item"),)

    def test_a_nested_value_binds_no_single_local_name(self):
        pattern = "{ row: { title }, index }"

        assert pattern_keys(pattern) == (
            SlotPatternKey("row", 2, 5, None),
            SlotPatternKey("index", 18, 23, "index"),
        )
        assert _key_texts(pattern) == ["row", "index"]

    def test_an_array_value_binds_no_single_local_name(self):
        keys = pattern_keys("{ a: [x, y], b }")

        assert keys is not None
        assert [(key.name, key.local) for key in keys] == [("a", None), ("b", "b")]

    def test_commas_inside_a_default_do_not_start_a_key(self):
        keys = pattern_keys("{ a = f(1, 2), b }")

        assert keys is not None
        assert [key.name for key in keys] == ["a", "b"]

    def test_a_quoted_key_spans_its_quotes_and_names_its_value(self):
        pattern = "{ 'row-data': r }"

        (key,) = pattern_keys(pattern) or ()

        assert (key.name, key.local) == ("row-data", "r")
        assert (key.start_index, key.end_index) == (2, 12)
        assert _text(pattern, key.start_index, key.end_index) == "'row-data'"

    def test_a_double_quoted_key(self):
        assert pattern_keys('{ "a": b }') == (SlotPatternKey("a", 2, 5, "b"),)

    def test_a_rest_element_reads_no_prop_by_name(self):
        assert pattern_keys("{ row, ...rest }") == (SlotPatternKey("row", 2, 5, "row"),)

    def test_an_empty_pattern_has_no_keys(self):
        assert pattern_keys("{}") == ()

    @pytest.mark.parametrize(
        "pattern",
        [
            # A computed key cannot be named statically.
            "{ [k]: v }",
            # A numeric key is not an identifier or a string.
            "{ 1: a }",
            # A `/` may start a regular expression, which the tokenizer cannot split safely.
            "{ a = /x/ }",
            "{ a = 1 / 2 }",
            # A template literal may hide commas and braces.
            "{ a = `t` }",
            # Not an object pattern at all.
            "props",
            "[a, b]",
            "",
        ],
    )
    def test_a_pattern_that_cannot_be_split_safely_gives_none(self, pattern):
        assert pattern_keys(pattern) is None

    def test_spans_are_offset_by_start_index(self):
        assert pattern_keys("{ row }", 10) == (SlotPatternKey("row", 12, 15, "row"),)

    def test_spans_are_byte_offsets_after_non_ascii_text(self):
        # "ñ" takes two bytes, so `row` starts at byte 6 although it is the fifth character.
        assert pattern_keys("{ ñ, row }") == (
            SlotPatternKey("ñ", 2, 4, "ñ"),
            SlotPatternKey("row", 6, 9, "row"),
        )
        assert _key_texts("{ ñ, row }") == ["ñ", "row"]

    def test_a_non_ascii_quoted_key_spans_its_bytes_and_start_index_adds_on(self):
        assert pattern_keys("{ 'é': x, ñ }") == (
            SlotPatternKey("é", 2, 6, "x"),
            SlotPatternKey("ñ", 11, 13, "ñ"),
        )
        assert _key_texts("{ ñ, row }", 5) == ["ñ", "row"]


class TestLintUnknownSlotProps:
    SOURCE = '<c-Table><c-fill name="item" v-slot="{ row, missing }">x</c-fill></c-Table>'

    def test_the_default_message_lists_what_the_slot_passes(self):
        findings = lint_unknown_slot_props(_fills(self.SOURCE), lambda _tag, _slot: frozenset({"row", "index"}))

        (finding,) = findings
        assert finding.name == "missing"
        assert finding.code == "citry.vue.unknown-slot-prop"
        assert finding.severity == "warning"
        assert finding.message == (
            "Slot 'item' on <c-Table> passes no Vue prop named 'missing', so it is undefined in this fill. "
            "The slot passes: index, row."
        )

    def test_the_none_message_is_used_when_the_slot_passes_no_props(self):
        findings = lint_unknown_slot_props(_fills(self.SOURCE), lambda _tag, _slot: frozenset())

        assert [(finding.name, finding.message) for finding in findings] == [
            (
                "row",
                "Slot 'item' on <c-Table> passes no Vue props, so 'row' is undefined in this fill. "
                "If the slot passes Python data, read it with data= instead. Otherwise add it to its "
                '<c-slot> as a Vue prop, such as :row="row".',
            ),
            (
                "missing",
                "Slot 'item' on <c-Table> passes no Vue props, so 'missing' is undefined in this fill. "
                "If the slot passes Python data, read it with data= instead. Otherwise add it to its "
                '<c-slot> as a Vue prop, such as :row="row".',
            ),
        ]

    def test_the_finding_span_covers_the_key(self):
        (finding,) = lint_unknown_slot_props(_fills(self.SOURCE), lambda _tag, _slot: frozenset({"row"}))

        assert (finding.start_index, finding.end_index) == (44, 51)
        assert _text(self.SOURCE, finding.start_index, finding.end_index) == "missing"

    def test_no_finding_when_the_props_are_not_known(self):
        assert lint_unknown_slot_props(_fills(self.SOURCE), lambda _tag, _slot: None) == ()

    def test_no_finding_when_every_key_is_passed(self):
        assert lint_unknown_slot_props(_fills(self.SOURCE), lambda _tag, _slot: frozenset({"row", "missing"})) == ()

    def test_a_renamed_key_is_checked_by_its_key_not_its_local_name(self):
        source = '<c-Table><c-fill name="item" v-slot="{ row: item, extra: other }">x</c-fill></c-Table>'

        # `item` is only the local name, so passing `item` would not make `row` known.
        findings = lint_unknown_slot_props(_fills(source), lambda _tag, _slot: frozenset({"item", "other", "extra"}))

        (finding,) = findings
        assert finding.name == "row"
        assert _text(source, finding.start_index, finding.end_index) == "row"
        # Passing the key silences the finding whatever the local name is.
        assert lint_unknown_slot_props(_fills(source), lambda _tag, _slot: frozenset({"row", "extra"})) == ()

    def test_a_single_name_or_unreadable_pattern_gets_no_finding(self):
        source = (
            '<c-Table><c-fill name="a" v-slot="props">x</c-fill>'
            '<c-fill name="b" v-slot="{ a = `t` }">y</c-fill></c-Table>'
        )

        assert lint_unknown_slot_props(_fills(source), lambda _tag, _slot: frozenset()) == ()

    def test_props_for_receives_the_tag_as_written_and_the_slot(self):
        calls: list[tuple[str, str]] = []

        def props_for(tag: str, slot: str) -> frozenset[str] | None:
            calls.append((tag, slot))
            return None

        lint_unknown_slot_props(_fills(self.SOURCE), props_for)

        assert calls == [("c-Table", "item")]


class TestUnknownSlotPropsFor:
    OUTLETS = _outlets('<c-slot name="a" :x="1" /><c-slot name="a" :y-z="2" /><c-slot name="b" />')

    def test_looks_up_the_tag_case_insensitively_and_merges_the_slot_props(self):
        props_for = unknown_slot_props_for({"c-table": self.OUTLETS})

        assert props_for("c-Table", "a") == frozenset({"x", "yZ"})
        assert props_for("C-TABLE", "b") == frozenset()

    def test_unknown_when_the_tag_is_not_registered_or_its_template_is_unknown(self):
        props_for = unknown_slot_props_for({"c-table": self.OUTLETS, "c-broken": None})

        assert props_for("c-other", "a") is None
        assert props_for("c-broken", "a") is None

    def test_unknown_when_no_outlet_serves_the_slot(self):
        assert unknown_slot_props_for({"c-table": self.OUTLETS})("c-table", "missing") is None

    def test_unknown_when_the_template_has_a_dynamic_outlet(self):
        dynamic = _outlets('<c-slot name="a" :x="1" /><c-slot c-name="slot_name" />')

        assert unknown_slot_props_for({"c-table": dynamic})("c-table", "a") is None
