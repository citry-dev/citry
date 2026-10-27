"""
Vue slot props: `<c-slot :row="...">` passes browser data, which a fill reads with `v-slot`.

The parser checks the syntax (its own tests live in
`crates/citry_template_parser/tests/tag_parser_client_directives.rs`). These
tests check what Citry writes into the Vue templates it compiles, that the
Python slot data is unchanged beside the props, and the runtime guards that
keep Python data from choosing the Vue code the browser runs.
"""

from __future__ import annotations

import re

import pytest

import citry_ui
from citry import Citry, Component, Extension, InMemoryCache, Slot
from citry._vue.capture import UnsupportedPreparedView, render_prepared_direct
from citry._vue.compiler import NativeCompiler
from citry._vue.direct_capture import assemble_typed_render
from citry._vue.events import default_events_producer
from citry.ext.cache.artifact import (
    ArtifactDirectSlotPart,
    CacheArtifactError,
    _part_from_wire,
    _part_to_wire,
)


def _templates(page: Component, *, context_names: tuple[str, ...] = ()) -> dict[str, str]:
    assembly = assemble_typed_render(
        render_prepared_direct(page),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
        template_context_names=context_names,
    )
    return {
        item.type_key.rsplit("_", 1)[0]: assembly.compile_inputs[item.definition_id].template
        for item in assembly.view.occurrences
    }


def _list_and_page(registry: Citry, fill: str) -> type[Component]:
    class List(Component):
        citry = registry
        template = """
          <ul>
            <template v-for="row in rows" :key="row.id">
              <li><c-slot name="item" :row="row" v-bind:row-index="row.id" c-label="'L'" /></li>
            </template>
          </ul>
        """

        def js_data(self, kwargs, slots):
            return {"rows": [{"id": 1, "title": "A"}]}

    class Page(Component):
        citry = registry
        template = f"""
          <c-List>{fill}</c-List>
        """

    return Page


def _opening(template: str) -> str:
    [opening] = re.findall(r"<template v-slot:\['citrySlot[0-9a-f]+'\][^>]*>", template)
    return opening.split("]", 1)[1]


def test_the_outlet_passes_the_props_and_the_fill_function_reads_them() -> None:
    registry = Citry(autodiscover=False)
    page = _list_and_page(registry, '<c-fill name="item" v-slot="{ row }"><b v-text="row.title"></b></c-fill>')

    templates = _templates(page())

    # The props are written as authored, in the receiver's own template, so
    # they read its data; Vue camelizes `row-index` when it passes it on.
    assert re.search(
        r'<slot v-if="[^"]+" name="citrySlot[0-9a-f]+" :row="row" v-bind:row-index="row.id"></slot>', templates["List"]
    )
    assert _opening(templates["Page"]) == '="{ row }">'


@pytest.mark.parametrize(
    ("pattern", "expected"),
    [
        ("{ row }", '="{ $citryI18nBinding, $i18n, row }">'),
        # The key Vue passes for Citry's `v-if` around each slot is bound to
        # a reserved name before a rest or a props object can collect it.
        ("{ row: item, ...others }", '="{ $citryI18nBinding, $i18n, key: citrySlotKey, row: item, ...others }">'),
        ("{}", '="{ $citryI18nBinding, $i18n }">'),
        ("props", '="{ $citryI18nBinding, $i18n, key: citrySlotKey, ...props }">'),
        # A pattern holding a double quote is written between single quotes.
        ('{ row = "x" }', "='{ $citryI18nBinding, $i18n, row = \"x\" }'>"),
    ],
)
def test_the_fill_pattern_follows_the_context_names_extensions_pass(pattern: str, expected: str) -> None:
    registry = Citry(autodiscover=False)
    quote = "'" if '"' in pattern else '"'
    page = _list_and_page(registry, f'<c-fill name="item" v-slot={quote}{pattern}{quote}>x</c-fill>')

    templates = _templates(page(), context_names=("$citryI18nBinding", "$i18n"))

    assert _opening(templates["Page"]) == expected
    # The context names stay first on the outlet too.
    assert ':$citryI18nBinding="$citryI18nBinding" :$i18n="$i18n" :row="row"' in templates["List"]


def test_a_fill_without_a_pattern_keeps_the_context_only_slot_function() -> None:
    registry = Citry(autodiscover=False)
    page = _list_and_page(registry, '<c-fill name="item">x</c-fill>')

    assert _opening(_templates(page())["Page"]) == ">"
    assert _opening(_templates(page(), context_names=("$i18n",))["Page"]) == '="{ $i18n }">'


def test_python_slot_data_beside_the_props_is_unchanged() -> None:
    registry = Citry(autodiscover=False)
    seen: list[dict[str, object]] = []

    class Spy(Component):
        citry = registry
        template = """
          <c-slot name="item" :row="row" c-label="'L'" plain="p" />
        """

        def js_data(self, kwargs, slots):
            return {"row": 1}

    class Page(Component):
        citry = registry
        template = """
          <c-Spy><c-fill name="item" data="data">{{ record(data) }}</c-fill></c-Spy>
        """

        def template_data(self, kwargs, slots):
            return {"record": lambda data: seen.append(dict(data)) or ""}

    Page().render()

    # The Vue prop goes to the browser only, never into the Python data.
    assert seen == [{"label": "L", "plain": "p"}]


def test_a_fill_passed_on_by_a_group_forwards_the_whole_props_object() -> None:
    registry = Citry(autodiscover=False)
    registry.register_library(citry_ui)

    class Page(Component):
        citry = registry
        template = """
            <c-CTabs default_value="one" aria_label="Example">
              <c-CTab value="one"><c-fill name="default" v-slot="p"><span v-text="p.label">One</span></c-fill></c-CTab>
              <c-CTabPanel value="one"><p>Panel</p></c-CTabPanel>
            </c-CTabs>
        """

    templates = _templates(Page())

    # The author's slot function is written with its pattern; an intermediate
    # component that passes the fill on cannot know which props the pattern
    # reads, so it hands on the whole object.
    assert '="{ key: citrySlotKey, ...p }"><span v-text="p.label">' in templates["Page"]
    assert re.search(
        r'="citrySlotProps"><slot name="citrySlot[0-9a-f]+" v-bind="citrySlotProps"></slot>', templates["CTabs"]
    )


def test_a_transparent_receiver_refuses_slot_props_it_would_copy_in_place() -> None:
    registry = Citry(autodiscover=False)

    class Wrapper(Component):
        citry = registry
        transparent = True
        template = """
          <c-slot :row="1" />
        """

    class Page(Component):
        citry = registry
        template = """
          <section><c-Wrapper><b>x</b></c-Wrapper></section>
        """

        def js_data(self, kwargs, slots):
            return {"unused": 1}

    with pytest.raises(
        UnsupportedPreparedView,
        match=re.escape("Wrapper copies the content of slot 'default' into the template around it"),
    ):
        _templates(Page())


@pytest.mark.parametrize(
    ("receiver", "label"),
    [
        ('<c-provide key="k" value="v">{}</c-provide>', "<c-provide>"),
        ('<c-cache key="k">{}</c-cache>', "<c-cache>"),
        ('<c-element c-is="tag">{}</c-element>', "<c-element>"),
        ("<c-Wrapper>{}</c-Wrapper>", "Wrapper"),
    ],
)
def test_a_scoped_fill_into_a_receiver_that_copies_it_in_place_fails(receiver: str, label: str) -> None:
    registry = Citry(autodiscover=False)

    class Wrapper(Component):
        citry = registry
        transparent = True
        template = """
          <c-slot />
        """

    body = receiver.format('<c-fill name="default" v-slot="{ row }"><b v-text="row"></b></c-fill>')

    class Page(Component):
        citry = registry
        template = f"""
          <section>{body}</section>
        """

        def template_data(self, kwargs, slots):
            return {"tag": "div"}

    # The error names the receiver as the author wrote it.
    with pytest.raises(UnsupportedPreparedView, match=re.escape(f"{label} copies the content of slot 'default'")):
        _templates(Page())


@pytest.mark.parametrize(
    ("bind", "message"),
    [
        ({":row": "row"}, r"Vue directive ':row' is not supported on '<c-slot>' through 'c-bind'"),
        ({"v-bind:row": "row"}, r"Vue directive 'v-bind:row' is not supported on '<c-slot>' through 'c-bind'"),
    ],
)
def test_a_slot_prop_from_python_data_fails(bind: dict[str, str], message: str) -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = """
          <c-slot c-bind="attrs" />
        """

        def template_data(self, kwargs, slots):
            return {"attrs": bind}

    class Page(Component):
        citry = registry
        template = """
          <c-Child>x</c-Child>
        """

    with pytest.raises(RuntimeError, match=message):
        Page().render()


def test_a_fill_pattern_from_python_data_fails() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = """
          <c-slot name="item" />
        """

    class Page(Component):
        citry = registry
        template = """
          <c-Child><c-fill c-bind="attrs">x</c-fill></c-Child>
        """

        def template_data(self, kwargs, slots):
            return {"attrs": {"name": "item", "v-slot": "{ row }"}}

    with pytest.raises(RuntimeError, match="'c-bind' on <c-fill> got an unsupported key 'v-slot'"):
        Page().render()


def test_a_slot_printed_inside_a_scoped_outlet_fill_gets_none_of_its_props() -> None:
    registry = Citry(autodiscover=False)

    class Receiver(Component):
        citry = registry
        template = """
          <ul><li><c-slot name="item" :row="rows[0]" /></li></ul>
        """

        def js_data(self, kwargs, slots):
            return {"rows": [1]}

    class Middle(Component):
        citry = registry
        template = """
          <c-Receiver><c-fill name="item"><i>{{ header }}</i></c-fill></c-Receiver>
        """

        def template_data(self, kwargs, slots):
            return {"header": slots["header"]}

    class Page(Component):
        citry = registry
        template = """
          <c-Middle><c-fill name="header" v-slot="{ row }"><b v-text="row"></b></c-fill></c-Middle>
        """

    templates = _templates(Page())

    # Receiver's props read Receiver's data, so they stay on its own outlet.
    # The header outlet lands in Middle, where `rows` does not exist.
    assert ':row="rows[0]"' in templates["Receiver"]
    assert re.search(r'<i><slot name="citrySlot[0-9a-f]+"></slot></i>', templates["Middle"])


def test_a_scoped_fill_called_through_a_python_slot_at_a_props_outlet_fails() -> None:
    registry = Citry(autodiscover=False)

    class Inner(Component):
        citry = registry
        template = """
          <div><c-slot name="item" :row="1" /></div>
        """

        def js_data(self, kwargs, slots):
            return {"unused": 1}

    class Wrapper(Component):
        citry = registry
        template = """
          <div>{{ inner }}</div>
        """

        def template_data(self, kwargs, slots):
            fill = slots["item"]
            return {"inner": Inner(slots={"item": Slot(lambda ctx: fill(ctx.data))})}

    class Page(Component):
        citry = registry
        template = """
          <c-Wrapper><c-fill name="item" v-slot="{ row }"><b v-text="row"></b></c-fill></c-Wrapper>
        """

    # The Python Slot cannot pass `:row` on, so the fill would read nothing.
    with pytest.raises(
        RuntimeError, match=r"Inner's <c-slot name=\"item\"> passes Vue slot props, but it renders a Python Slot"
    ):
        _templates(Page())


def test_a_scoped_fill_at_a_nested_outlet_without_props_is_not_refused() -> None:
    registry = Citry(autodiscover=False)

    class Inner(Component):
        citry = registry
        template = """
          <div><c-slot name="item" :row="1" /></div>
        """

        def js_data(self, kwargs, slots):
            return {"unused": 1}

    class Plain(Component):
        citry = registry
        template = """
          <p><c-slot name="z" /></p>
        """

    class Wrapper(Component):
        citry = registry
        template = """
          <div>{{ inner }}</div>
        """

        def template_data(self, kwargs, slots):
            fill = slots["item"]
            plain = Slot(lambda _ctx: Plain(slots={"z": Slot(lambda ctx: fill(ctx.data))}))
            return {"inner": Inner(slots={"item": plain})}

    class Page(Component):
        citry = registry
        template = """
          <c-Wrapper><c-fill name="item" v-slot="{ row }"><b v-text="row"></b></c-fill></c-Wrapper>
        """

    # The fill renders at Plain's outlet, which passes no props, so Inner's
    # props were never meant for it.
    _templates(Page())


def test_c_bind_slot_data_with_a_slot_prop_name_fails() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = """
          <c-slot :row-data="1" c-bind="attrs" />
        """

        def template_data(self, kwargs, slots):
            return {"attrs": {"rowData": 5}}

    class Page(Component):
        citry = registry
        template = """
          <c-Child>x</c-Child>
        """

    # Vue passes `:row-data` to the fill as `rowData`, the same name.
    with pytest.raises(RuntimeError, match="also passes 'rowData' as a Vue slot prop"):
        Page().render()


@pytest.mark.parametrize("key", ["data", "fallback"])
def test_c_bind_fill_names_that_clash_with_the_pattern_fail(key: str) -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = """
          <c-slot name="item" />
        """

    class Page(Component):
        citry = registry
        template = """
          <c-Child><c-fill name="item" v-slot="{ row }" c-bind="attrs">x</c-fill></c-Child>
        """

        def template_data(self, kwargs, slots):
            return {"attrs": {key: "row"}}

    with pytest.raises(RuntimeError, match="names 'row' both in its Vue 'v-slot' and in its Python"):
        Page().render()


def _looped_list(registry: Citry) -> None:
    class Badge(Component):
        citry = registry
        template = """
          <span v-text="'badge'"></span>
        """

    class List(Component):
        citry = registry
        template = """
          <ul><li v-for="row in rows" :key="row"><c-slot name="item" :row="row" /></li></ul>
        """

        def js_data(self, kwargs, slots):
            return {"rows": ["a", "b"]}


def test_a_fill_with_a_component_at_an_outlet_in_a_vue_loop_fails() -> None:
    registry = Citry(autodiscover=False)
    _looped_list(registry)

    class Page(Component):
        citry = registry
        template = """
          <c-List><c-fill name="item" v-slot="{ row }"><c-Badge /></c-fill></c-List>
        """

    # Vue would mount the one Badge the server prepared once per row, which
    # fails in the browser; the outlet and the fill are in two templates.
    with pytest.raises(RuntimeError, match="component 'Page' passes a fill that holds Citry components"):
        Page().render().serialize()


def test_a_fill_passed_on_to_an_outlet_in_a_vue_loop_fails() -> None:
    registry = Citry(autodiscover=False)
    _looped_list(registry)

    class Middle(Component):
        citry = registry
        template = """
          <c-List><c-fill name="item"><c-slot name="cell" /></c-fill></c-List>
        """

    class Page(Component):
        citry = registry
        template = """
          <c-Middle><c-fill name="cell"><c-Badge /></c-fill></c-Middle>
        """

    # Middle's fill holds only its own outlet, which List repeats, so Page's
    # fill for that outlet repeats too.
    with pytest.raises(
        RuntimeError, match="to a <c-slot> of component 'Middle' that component 'List' repeats inside a Vue 'v-for'"
    ):
        Page().render().serialize()


def test_an_events_render_writes_the_same_props_and_pattern(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = Citry(autodiscover=False)
    page = _list_and_page(registry, '<c-fill name="item" v-slot="{ row }"><b v-text="row.title"></b></c-fill>')
    compiled: list[str] = []
    original = NativeCompiler.compile

    def record(self: NativeCompiler, template: str, **options: object) -> object:
        compiled.append(template)
        return original(self, template, **options)  # type: ignore[arg-type]

    monkeypatch.setattr(NativeCompiler, "compile", record)

    # The Events producer, which a server event's re-render uses, compiles
    # the same text as the first render.
    default_events_producer(registry).prepare_from_render(
        render_prepared_direct(page()), citry=registry, app_id="slot-props-events", revision=0
    )
    [receiver] = [text for text in compiled if "<slot " in text]
    [author] = [text for text in compiled if "v-slot:[" in text]

    assert re.search(r'name="citrySlot[0-9a-f]+" :row="row" v-bind:row-index="row.id"></slot>', receiver)
    assert _opening(author) == '="{ row }">'


def test_a_cached_slot_part_keeps_its_props_and_pattern() -> None:
    part = ArtifactDirectSlotPart(
        frame=0,
        execution=1,
        parent_execution=None,
        external_parent_execution=False,
        lexical_instance=0,
        lexical_parent_depth=None,
        receiver_instance=1,
        receiver_parent_depth=None,
        kind="named",
        public_name="item",
        fill_source='<c-fill name="item" v-slot="{ row }"></c-fill>',
        source='<c-slot name="item" :row="row" />',
        span=(0, 33),
        origin=None,
        vue_props=((":row", "row"),),
        fill_vue_pattern="{ row }",
    )

    wire = _part_to_wire(part)

    assert _part_from_wire(wire, "part") == part


@pytest.mark.parametrize(
    ("props", "pattern"),
    [
        (((":row", "row"), ("v-bind:row-index", "row.id")), "{ row, rowIndex = 0 }"),
        (((":label", "'a' + 'b'"),), "props"),
        (((":title", 'a + "b"'),), '{ title = "none" }'),
    ],
)
def test_a_cached_slot_part_the_parser_accepts_is_read_back(props: tuple[tuple[str, str], ...], pattern: str) -> None:
    part = ArtifactDirectSlotPart(
        frame=0,
        execution=1,
        parent_execution=None,
        external_parent_execution=False,
        lexical_instance=0,
        lexical_parent_depth=None,
        receiver_instance=1,
        receiver_parent_depth=None,
        kind="named",
        public_name="item",
        fill_source='<c-fill name="item" v-slot="{ row }"></c-fill>',
        source='<c-slot name="item" :row="row" />',
        span=(0, 33),
        origin=None,
        vue_props=props,
        fill_vue_pattern=pattern,
    )

    assert _part_from_wire(_part_to_wire(part), "part") == part


@pytest.mark.parametrize(
    ("index", "stored", "message"),
    [
        (15, [["@click", "steal()"]], "holds Vue slot props the template parser does not accept"),
        (15, [[':a="1" @click="steal()" :b', "row"]], "holds Vue slot props the template parser does not accept"),
        (15, [[":a><img", "row"]], "holds Vue slot props the template parser does not accept"),
        (15, [[":name", "row"]], "holds Vue slot props the template parser does not accept"),
        (15, [[":c-value", "row"]], "holds Vue slot props the template parser does not accept"),
        (15, [[":$i18n", "row"]], "holds Vue slot props the template parser does not accept"),
        (15, [[":[x]", "row"]], "holds Vue slot props the template parser does not accept"),
        (15, [[":row", "a"], [":row", "b"]], "holds Vue slot props the template parser does not accept"),
        (15, [[":row-data", "a"], [":rowData", "b"]], "holds Vue slot props the template parser does not accept"),
        (16, " { row }", "is not a 'v-slot' pattern the template parser accepts"),
        (16, "props ", "is not a 'v-slot' pattern the template parser accepts"),
        (15, [[":row", 'a + "\'"']], "is not a value the template parser accepts"),
        (15, [[":row", "{{ x }}"]], "is not a value the template parser accepts"),
        (16, "{ row", "is not a 'v-slot' pattern the template parser accepts"),
        (16, "{ row = steal() }", "is not a 'v-slot' pattern the template parser accepts"),
        (16, "{ row }, b", "is not a 'v-slot' pattern the template parser accepts"),
        (16, "a, b", "is not a 'v-slot' pattern the template parser accepts"),
        (16, "{ key }", "is not a 'v-slot' pattern the template parser accepts"),
        (16, "{ row } /* c */", "is not a 'v-slot' pattern the template parser accepts"),
    ],
)
def test_a_cached_slot_part_the_parser_could_not_write_is_unreadable(index: int, stored: object, message: str) -> None:
    part = ArtifactDirectSlotPart(
        frame=0,
        execution=1,
        parent_execution=None,
        external_parent_execution=False,
        lexical_instance=0,
        lexical_parent_depth=None,
        receiver_instance=1,
        receiver_parent_depth=None,
        kind="named",
        public_name="item",
        fill_source='<c-fill name="item" v-slot="{ row }"></c-fill>',
        source='<c-slot name="item" :row="row" />',
        span=(0, 33),
        origin=None,
        vue_props=((":row", "row"),),
        fill_vue_pattern="{ row }",
    )
    wire = _part_to_wire(part)
    wire[index] = stored

    # An unreadable entry is a cache miss, so the page renders afresh instead
    # of failing when Citry writes the outlet.
    with pytest.raises(CacheArtifactError, match=re.escape(message)):
        _part_from_wire(wire, "part")


def test_a_cache_hit_writes_the_same_slot_props_and_pattern() -> None:
    hits: list[str] = []

    class CacheProbe(Extension):
        name = "slot_props_cache_probe"
        render_cache_mode = "stateless"
        render_cache_version = 1

        def on_component_cache_hit(self, ctx):
            hits.append(type(ctx.component).__name__)

    registry = Citry(secret="slot-props-cache", cache=InMemoryCache(), extensions=[CacheProbe])  # noqa: S106

    class List(Component):
        citry = registry
        template = """
          <ul><li v-for="row in rows" :key="row"><c-slot name="item" :row="row" /></li></ul>
        """

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return "fixed"

        def js_data(self, kwargs, slots):
            return {"rows": ["a"]}

    class Page(Component):
        citry = registry
        template = """
          <c-List><c-fill name="item" v-slot="{ row }"><b v-text="row"></b></c-fill></c-List>
        """

    first = _templates(Page())
    second = _templates(Page())

    assert hits == ["List"]
    assert first == second
    assert ':row="row"' in second["List"]
    assert _opening(second["Page"]) == '="{ row }">'
