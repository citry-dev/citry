"""Vue directives written on a Citry component tag (`<c-child v-show="...">`, `v-if`, `v-model`, `v-focus`)."""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry._vue.capture import render_prepared_direct
from citry._vue.compiler import NativeCompiler
from citry._vue.direct_capture import assemble_typed_render
from citry._vue.events import native_compile_view
from citry._vue.serialization import hydration_admission
from citry.client_directives import (
    ComponentTagClientBindingKind,
    classify_component_tag_client_binding_key,
)

_SEVERAL = "its template has several top-level nodes, or a 'v-for', '<c-for>', or '<c-slot>' at the top level"
_PYTHON_HTML = "its template renders HTML from Python (such as '<c-raw>' or trusted markup) at the top level"


def _pages(child_template: str, page_template: str, data: dict[str, Any] | None = None) -> type[Component]:
    registry = Citry(autodiscover=False)

    class Leaf(Component):
        citry = registry
        template = """
            <i>leaf</i>
        """

    class Child(Component):
        citry = registry
        template = child_template

    class Page(Component):
        citry = registry
        template = page_template
        js = """
            $component({data(){return {visible:true,open:true};}});
        """

        def template_data(self, kwargs, slots):
            return dict(data or {})

    return Page


def _assemble(root: Component):
    return assemble_typed_render(
        render_prepared_direct(root),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )


class TestRejectedDirectives:
    @pytest.mark.parametrize(
        ("attribute", "hint"),
        [
            ('v-for="row in rows"', "Repeat the component with '<c-for>'"),
            ('v-html="markup"', "render it inside the child"),
            ('v-text="label"', "render it inside the child"),
            ('v-slot="data"', "Pass slot content with '<c-fill name=\"...\">'"),
            ('#header="data"', "Pass slot content with '<c-fill name=\"...\">'"),
            ('v-show.lazy="open"', "Write 'v-show' without an argument or modifiers."),
            ('v-if.once="open"', "Write 'v-if', 'v-else-if', and 'v-else' without an argument or modifiers."),
            ("v-else:x", "Write 'v-if', 'v-else-if', and 'v-else' without an argument or modifiers."),
            ("v-once", "Put the directive on an element inside the child's template."),
            ('v-citry-control="x"', "Citry reserves 'v-c-*' and 'v-citry-*' for its own browser runtime."),
            ('v-If="open"', "names are lowercase"),
            ('v-model:="q"', "Name the prop after 'v-model:'"),
            ('v-bind.prop="props"', "bind each prop as ':name=\"...\"'"),
            ('v-on="listeners"', "Write each listener as '@event=\"...\"'"),
            ('.value="text"', "Pass the value as a component prop with ':name=\"...\"'."),
            ('c-v-for="row in rows"', "Repeat the component with '<c-for>'"),
        ],
    )
    def test_directly_authored_directive_fails_to_compile(self, attribute, hint):
        page = _pages("<section>child</section>", f"<main><c-child {attribute} /></main>")
        name = attribute.split("=", 1)[0]

        with pytest.raises(SyntaxError) as caught:
            page().render()

        message = str(caught.value)
        assert f"Vue directive '{name}' is not supported on the component tag '<c-child>'. " in message
        assert hint in message

    @pytest.mark.parametrize("key", ["v-for", "v-html", "#header", "v-once"])
    def test_directive_from_a_python_spread_fails_at_render(self, key):
        page = _pages(
            "<section>child</section>",
            '<main><c-child c-bind="attrs" /></main>',
            {"attrs": {key: "open"}},
        )

        with pytest.raises(RuntimeError, match=rf"Vue directive '{key}' is not supported on the component tag"):
            page().render()

    @pytest.mark.parametrize(
        ("template", "key"),
        [
            ('<c-child c-v-show="expr" />', "v-show"),
            ('<c-child c-bind="attrs" />', "v-show"),
            ('<c-child c-v-if="expr" />', "v-if"),
            ('<c-child c-bind="model" />', "v-model"),
            ('<c-child c-bind="custom" />', "v-custom:arg.mod"),
        ],
    )
    def test_supported_directive_value_must_be_written_in_the_template(self, template, key):
        page = _pages(
            "<section>child</section>",
            f"<main>{template}</main>",
            {
                "expr": "open",
                "attrs": {"v-show": "open"},
                "model": {"v-model": "query"},
                "custom": {"v-custom:arg.mod": "open"},
            },
        )

        with pytest.raises(RuntimeError, match=rf"Executable Vue binding '{key}' on <c-child> must be authored"):
            page().render()

    @pytest.mark.parametrize(
        ("attribute", "name"),
        [
            ("v-show", "v-show"),
            ('v-show=""', "v-show"),
            ("v-if", "v-if"),
            ('v-else-if=" "', "v-else-if"),
            ("v-model", "v-model"),
            ("v-model:title.trim", "v-model:title.trim"),
        ],
    )
    def test_directive_needs_an_expression(self, attribute, name):
        page = _pages("<section>child</section>", f"<main><c-child {attribute} /></main>")

        with pytest.raises(SyntaxError, match=rf"'{name}' on the component tag '<c-child>' needs a Vue expression"):
            page().render()

    @pytest.mark.parametrize("attribute", ['v-model:key="q"', 'v-model:citry-id.trim="q"'])
    def test_model_cannot_target_citry_call_identity(self, attribute):
        page = _pages("<section>child</section>", f"<main><c-child {attribute} /></main>")

        with pytest.raises(RuntimeError, match=r"targets Citry-owned component identity"):
            page().render()

    def test_v_else_takes_no_value(self):
        page = _pages("<section>child</section>", '<main><c-child v-else="open" /></main>')

        with pytest.raises(SyntaxError, match=r"'v-else' on the component tag '<c-child>' takes no value"):
            page().render()

    @pytest.mark.parametrize(
        "page_template",
        [
            "<main><c-child v-else /></main>",
            '<main><c-child v-if="open" /><span>between</span><c-child v-else /></main>',
        ],
        ids=["no-v-if", "element-between"],
    )
    def test_v_else_needs_an_adjacent_v_if(self, page_template):
        # Vue's compiler reports a broken chain the same way it does for
        # elements.
        page = _pages("<section>child</section>", page_template)

        with pytest.raises(ValueError, match=r"VElseNoAdjacentIf"):
            page().render().serialize(ssr=False)

    def test_dynamic_element_keeps_every_directive(self):
        # `<c-element>` renders a plain HTML element, where these are native.
        page = _pages(
            "<section>child</section>",
            '<main><c-element is="p" v-if="open" v-text="\'x\'" /></main>',
        )

        page().render().serialize(ssr=False)

    @pytest.mark.parametrize(
        ("key", "kind"),
        [
            ("v-show", ComponentTagClientBindingKind.SHOW),
            ("v-if", ComponentTagClientBindingKind.CONDITION),
            ("v-else-if", ComponentTagClientBindingKind.CONDITION),
            ("v-else", ComponentTagClientBindingKind.CONDITION),
            ("v-model", ComponentTagClientBindingKind.MODEL),
            ("v-model:title.trim", ComponentTagClientBindingKind.MODEL),
            ("v-focus", ComponentTagClientBindingKind.DIRECTIVE),
            ("v-onboard:step", ComponentTagClientBindingKind.DIRECTIVE),
            ("v-bind", ComponentTagClientBindingKind.PROPS_OBJECT),
            ("v-on:select", ComponentTagClientBindingKind.EVENT),
        ],
    )
    def test_classifier_kinds(self, key, kind):
        assert classify_component_tag_client_binding_key(key, tag_name="c-child") is kind

    def test_classifier_reports_directives_only_on_a_component_boundary(self):
        assert classify_component_tag_client_binding_key("v-for", tag_name="c-element", component_boundary=False) is (
            None
        )
        assert classify_component_tag_client_binding_key(
            "v-focus", tag_name="c-element", component_boundary=False
        ) is (None)
        with pytest.raises(RuntimeError, match="Vue directive 'v-for'"):
            classify_component_tag_client_binding_key("v-for", tag_name="c-child")


class TestShownComponentCall:
    def test_v_show_becomes_a_declared_call_binding_and_not_a_kwarg(self):
        received: list[dict[str, Any]] = []
        registry = Citry(autodiscover=False)

        class Child(Component):
            citry = registry
            template = """
                <section>child</section>
            """

            def template_data(self, kwargs, slots):
                received.append(dict(self.raw_kwargs))
                return {}

        class Parent(Component):
            citry = registry
            template = """
                <main><c-child v-show="visible" :title="label" /></main>
            """

        assembly = _assemble(Parent())
        parent = next(item for item in assembly.view.occurrences if item.type_key == Parent.class_id)
        child = next(item for item in assembly.view.occurrences if item.type_key == Child.class_id)
        compile_input = assembly.compile_inputs[parent.definition_id]
        call = compile_input.local_calls[0]

        assert received == [{}]
        assert compile_input.template.strip() == (
            f'<main><x-{Child.class_id.lower().replace("_", "-")} v-show="visible" :title="label" '
            f':citry-id="$citryPrepared.calls.{call["localId"]}.id" '
            f':key="$citryPrepared.calls.{call["localId"]}.key"></x-{Child.class_id.lower().replace("_", "-")}></main>'
        )
        assert [(item["kind"], item["name"], item["value"]) for item in call["bindings"]] == [
            ("show", "v-show", "visible"),
            ("prop", ":title", "label"),
        ]
        source = compile_input.template.encode()
        first = call["bindings"][0]
        assert source[first["sourceStart"] : first["sourceEnd"]] == b'v-show="visible"'
        assert dict(assembly.root_directive_occurrences) == {child.id: ("Child", "c-child", "v-show")}

        compiled = native_compile_view(NativeCompiler())(assembly)
        parent_render = compiled[parent.definition_id]
        # The call keeps its Citry-owned key: no replacement key, and no entry
        # in the signature the browser compares across revisions.
        assert parent_render.directive_signature == ()
        assert parent_render.replacement_sites == ()
        assert "[_vShow, _ctx.visible]" in parent_render.javascript
        assert compiled[child.definition_id].root_shape == "element"

    @pytest.mark.parametrize(
        "child_template",
        [
            "<section>child</section>",
            "\n<!-- note -->\n<section>child</section>\n",
            '<p v-if="on">a</p><span v-else>b</span>',
            '<c-if cond="False"><p>hidden</p></c-if>',
            "<c-leaf />",
        ],
        ids=["element", "comment-and-element", "browser-condition", "empty", "component"],
    )
    def test_accepted_child_roots(self, child_template):
        page = _pages(child_template, '<main><c-child v-show="visible" /></main>')

        page().render().serialize(ssr=False)

    @pytest.mark.parametrize(
        ("child_template", "reason"),
        [
            ("<p>a</p><p>b</p>", _SEVERAL),
            ('<template v-if="on"><p>a</p><p>b</p></template>', _SEVERAL),
            ('<p v-for="x in [1, 2]" :key="x">a</p>', _SEVERAL),
            ("<c-slot />", _SEVERAL),
            ("just text", "its template renders only text"),
            ("<c-raw><p>a</p></c-raw>", _PYTHON_HTML),
        ],
        ids=["two-elements", "browser-condition-fragment", "browser-loop", "slot-outlet", "text", "python-html"],
    )
    def test_child_root_that_vue_would_skip_is_rejected(self, child_template, reason):
        page = _pages(child_template, '<main><c-child v-show="visible" /></main>')

        with pytest.raises(RuntimeError) as caught:
            page().render().serialize(ssr=False)

        assert str(caught.value) == (
            f"'v-show' on <c-child> needs component 'Child' to render one root element, but {reason}. "
            f"Vue would ignore 'v-show' there. Wrap the child's template in one element, or put 'v-show' on an "
            f"element around <c-child>."
        )

    def test_root_error_names_the_authored_dynamic_component_tag(self):
        page = _pages("<p>a</p><p>b</p>", '<main><c-component is="child" v-show="visible" /></main>')

        with pytest.raises(RuntimeError, match=r"^'v-show' on <c-component> needs component 'Child'"):
            page().render().serialize(ssr=False)

    @pytest.mark.parametrize(
        "call",
        [
            '<c-leaf v-show="visible" />',
            '<c-provide key="k" c-value="1" v-show="visible"><p>in</p></c-provide>',
            '<c-leaf :title="label" />',
        ],
    )
    def test_transparent_child_rejects_vue_bindings(self, call):
        registry = Citry(autodiscover=False)

        class Leaf(Component):
            citry = registry
            transparent = True
            template = """
                <i>leaf</i>
            """

        class Page(Component):
            citry = registry
            template = f"<main>{call}</main>"

        with pytest.raises(TypeError, match=r"cannot be used on the tag of the transparent component"):
            Page().render().serialize(ssr=False)

    def test_hydrated_page_leaves_the_shown_call_to_the_browser(self):
        registry = Citry(autodiscover=False)

        class Child(Component):
            citry = registry
            template = """
                <section>child</section>
            """

        class Page(Component):
            citry = registry
            template = """
                <main><p>before</p><c-child v-show="open" /></main>
            """

            def js_data(self, kwargs, slots):
                return {"open": False}

        rendered = Page().render()
        html = rendered.serialize(ssr=True)
        admission = hydration_admission(rendered)

        assert '"hydrate":true' in html
        # The shell shows what the server can write of its contents until the
        # runtime empties it; the call with `v-show` is left to Vue.
        assert '<main data-allow-mismatch="children"><p>before</p></main>' in html
        assert admission is not None
        assert [(item.code, item.outcome, item.shell_tag) for item in admission.declines] == [
            ("unsupported-directive", "shell", "main")
        ]


def _page_render(page_template: str, *, child_js: str = "", page_js: str = "") -> tuple[Any, Any, Any, Any]:
    """Assemble and compile a page with a `Child` and an `Other` component."""
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = """
            <section>child</section>
        """
        js = child_js

    class Other(Component):
        citry = registry
        template = """
            <b>other</b>
        """

    class Page(Component):
        citry = registry
        template = page_template
        js = page_js

    assembly = _assemble(Page())
    parent = next(item for item in assembly.view.occurrences if item.type_key == Page.class_id)
    compiled = native_compile_view(NativeCompiler())(assembly)
    return assembly, parent, compiled, (Page, Child, Other)


def _call_bindings(assembly: Any, parent: Any) -> list[list[tuple[str, str, str]]]:
    return [
        [(item["kind"], item["name"], item["value"]) for item in call["bindings"]]
        for call in assembly.compile_inputs[parent.definition_id].local_calls
    ]


class TestConditionalCalls:
    """`v-if`, `v-else-if`, and `v-else` on a component tag, alone or mixed with elements."""

    def test_chain_across_calls_and_an_element_compiles_to_one_vue_condition(self):
        assembly, parent, compiled, (_, child, other) = _page_render(
            """
            <main>
              <c-child v-if="a" />
              <p v-else-if="b">b</p>
              <c-other v-else />
            </main>
            """,
            page_js="$component({data(){return {a:true,b:false};}});",
        )
        template = assembly.compile_inputs[parent.definition_id].template
        render = compiled[parent.definition_id]

        assert _call_bindings(assembly, parent) == [
            [("condition", "v-if", "a")],
            [("condition", "v-else", "")],
        ]
        # `v-else` keeps its bare authored form.
        assert " v-else :citry-id=" in template
        # The server renders both children, so each has a definition and data
        # whichever branch the browser picks.
        assert {child.class_id, other.class_id} <= {item.type_key for item in assembly.view.occurrences}
        assert "(_ctx.a)\n      ? (_openBlock(), _createBlock(_component_x_child" in render.javascript
        assert ': (_ctx.b)\n        ? (_openBlock(), _createElementBlock("p", { key: 1 }, "b"))' in render.javascript
        # Vue's own condition picks the branch; nothing joins the signature.
        assert render.directive_signature == ()
        assert render.replacement_sites == ()
        assert assembly.root_directive_occurrences == {}

    def test_chain_of_calls_only(self):
        assembly, parent, compiled, _ = _page_render(
            '<main><c-child v-if="a" /><c-other v-else-if="b" /><c-child v-else /></main>',
            page_js="$component({data(){return {a:true,b:false};}});",
        )

        assert _call_bindings(assembly, parent) == [
            [("condition", "v-if", "a")],
            [("condition", "v-else-if", "b")],
            [("condition", "v-else", "")],
        ]
        assert compiled[parent.definition_id].javascript.count("_createBlock(_component_x_") == 3


class TestModelCalls:
    """`v-model` on a component tag becomes a Vue prop and an update listener."""

    def test_model_compiles_to_props_and_listeners_not_kwargs(self):
        received: list[dict[str, Any]] = []
        registry = Citry(autodiscover=False)

        class Child(Component):
            citry = registry
            template = """
                <section>child</section>
            """
            js = """
                $component({props: ["modelValue", "title", "titleModifiers"]});
            """

            def template_data(self, kwargs, slots):
                received.append(dict(self.raw_kwargs))
                return {}

        class Page(Component):
            citry = registry
            template = """
                <main><c-child v-model="q" v-model:title.trim.number="t" /></main>
            """
            js = """
                $component({data(){return {q:"",t:""};}});
            """

        assembly = _assemble(Page())
        parent = next(item for item in assembly.view.occurrences if item.type_key == Page.class_id)
        compiled = native_compile_view(NativeCompiler())(assembly)
        render = compiled[parent.definition_id]

        assert received == [{}]
        assert _call_bindings(assembly, parent) == [
            [("model", "v-model", "q"), ("model", "v-model:title.trim.number", "t")],
        ]
        for fragment in (
            "modelValue: _ctx.q,",
            '"onUpdate:modelValue": $event => ((_ctx.q) = $event),',
            "title: _ctx.t,",
            '"onUpdate:title": $event => ((_ctx.t) = $event),',
            "titleModifiers: { trim: true, number: true },",
        ):
            assert fragment in render.javascript
        # No runtime `vModel*` directive: the child applies the value itself.
        assert "_vModel" not in render.javascript
        assert "withDirectives" not in render.javascript
        assert render.directive_signature == ()


class TestCustomDirectiveCalls:
    """A custom directive on a component tag reaches the child's root element."""

    def test_custom_directive_is_a_declared_call_binding(self):
        assembly, parent, compiled, (_, child_class, _) = _page_render(
            '<main><c-child v-focus v-tip:top.delay="tip" /></main>',
            page_js="$component({data(){return {tip:'x'};}, directives:{focus:{}, tip:{}}});",
        )
        render = compiled[parent.definition_id]
        child = next(item for item in assembly.view.occurrences if item.type_key == child_class.class_id)

        assert _call_bindings(assembly, parent) == [
            [("directive", "v-focus", ""), ("directive", "v-tip:top.delay", "tip")],
        ]
        assert dict(assembly.root_directive_occurrences) == {child.id: ("Child", "c-child", "v-focus")}
        assert '[_directive_tip, _ctx.tip, "top", { "delay": true }]' in render.javascript
        assert "[_directive_focus]" in render.javascript
        # Like `v-show`, the call keeps its Citry-owned key and stays out of
        # the signature the browser compares across revisions.
        assert render.directive_signature == ()
        assert render.replacement_sites == ()

    def test_custom_directive_on_an_element_joins_the_signature(self):
        registry = Citry(autodiscover=False)

        class Page(Component):
            citry = registry
            template = """
                <main><p v-focus:x.a="1">text</p></main>
            """

        assembly = _assemble(Page())
        page = next(item for item in assembly.view.occurrences if item.type_key == Page.class_id)
        render = native_compile_view(NativeCompiler())(assembly)[page.definition_id]

        assert [(item.name, item.arg, item.modifiers) for item in render.directive_signature] == [
            ("v-focus", "x", ("a",))
        ]
        assert len(render.replacement_sites) == 1

    @pytest.mark.parametrize(
        ("child_template", "reason"),
        [
            ("<p>a</p><p>b</p>", _SEVERAL),
            ("just text", "its template renders only text"),
        ],
        ids=["two-elements", "text"],
    )
    def test_child_root_that_vue_would_skip_is_rejected(self, child_template, reason):
        page = _pages(child_template, '<main><c-child v-show="visible" v-focus /></main>')

        with pytest.raises(RuntimeError) as caught:
            page().render().serialize(ssr=False)

        # The first root directive on the tag names the error.
        assert str(caught.value) == (
            f"'v-show' on <c-child> needs component 'Child' to render one root element, but {reason}. "
            f"Vue would ignore 'v-show' there. Wrap the child's template in one element, or put 'v-show' on an "
            f"element around <c-child>."
        )

    def test_error_names_the_custom_directive(self):
        page = _pages("<p>a</p><p>b</p>", '<main><c-child v-focus:x="1" /></main>')

        with pytest.raises(RuntimeError, match=r"^'v-focus:x' on <c-child> needs component 'Child'"):
            page().render().serialize(ssr=False)


class TestHydratedCalls:
    """What the server writes for a hydrated page with these directives on a call."""

    @staticmethod
    def _hydrate(call: str) -> tuple[str, list[tuple[str, str, str | None]]]:
        registry = Citry(autodiscover=False)

        class Child(Component):
            citry = registry
            template = """
                <section>child</section>
            """

        class Other(Component):
            citry = registry
            template = """
                <b>other</b>
            """

        class Page(Component):
            citry = registry
            template = f"<main><p>before</p>{call}</main>"
            js = """
                $component({data(){return {local:true};}, directives:{focus:{}}});
            """

            def js_data(self, kwargs, slots):
                return {"open": True, "closed": False, "q": "x"}

        rendered = Page().render()
        html = rendered.serialize(ssr=True)
        admission = hydration_admission(rendered)
        assert admission is not None
        main = html[html.index("<main") : html.index("</main>") + len("</main>")]
        return main, [(item.code, item.outcome, item.shell_tag) for item in admission.declines]

    @pytest.mark.parametrize(
        ("call", "main"),
        [
            ('<c-child v-if="open" /><c-other v-else />', "<main><p>before</p><section>child</section></main>"),
            ('<c-child v-if="closed" /><c-other v-else />', "<main><p>before</p><b>other</b></main>"),
            ('<c-child v-if="closed" />', "<main><p>before</p><!--v-if--></main>"),
        ],
        ids=["true-branch", "else-branch", "false-placeholder"],
    )
    def test_server_known_condition_is_written(self, call, main):
        # A condition on `js_data` values is known on the server, so the
        # branch Vue picks is written, or Vue's `<!--v-if-->` placeholder.
        assert self._hydrate(call) == (main, [])

    @pytest.mark.parametrize(
        ("call", "code", "shown"),
        [
            ('<c-child v-if="local" />', "browser-condition", "<p>before</p><section>child</section>"),
            ('<c-child v-model="q" />', "component-attrs", "<p>before</p><section>child</section>"),
            ("<c-child v-focus />", "unsupported-directive", "<p>before</p>"),
        ],
    )
    def test_browser_decided_call_is_left_to_the_browser(self, call, code, shown):
        # Vue builds <main> in the browser, as for any prop, listener, or
        # directive on a call. Until the runtime empties the shell it shows
        # Citry's HTML: a condition only the browser can test shows its
        # branch, and a call with a custom directive is left out.
        expected = f'<main data-allow-mismatch="children">{shown}</main>'
        assert self._hydrate(call) == (expected, [(code, "shell", "main")])


class TestSlotDirectives:
    """`<c-slot>` attributes are Python slot data, so no Vue directive fits there."""

    _SLOT_DATA = "Its attributes other than 'name' and 'required' become Python slot data"

    @pytest.mark.parametrize(
        ("attribute", "hint"),
        [
            ('v-if="open"', "use '<c-if>' when Python decides"),
            ('v-show="open"', "Wrap the slot in an element that carries 'v-show'."),
            (':item="row"', "Vue slot props are not supported."),
            ('@click="go()"', "Put the listener on an element around the slot or inside the fill."),
            ("#header", "Name the slot with 'name=\"...\"'"),
            ('c-v-for="row in rows"', "Repeat the slot with '<c-for>'."),
        ],
    )
    def test_directly_authored_directive_fails_to_compile(self, attribute, hint):
        page = _pages(f"<section><c-slot {attribute} /></section>", "<main><c-child /></main>")
        name = attribute.split("=", 1)[0]

        with pytest.raises(SyntaxError) as caught:
            page().render()

        message = str(caught.value)
        assert f"Vue directive '{name}' is not supported on '<c-slot>'." in message
        assert self._SLOT_DATA in message
        assert hint in message

    @pytest.mark.parametrize("key", ["v-if", ":item", "@click", "#header", "v-custom:arg.mod"])
    def test_directive_from_a_python_spread_fails_at_render(self, key):
        registry = Citry(autodiscover=False)

        class Child(Component):
            citry = registry
            template = """
                <section><c-slot c-bind="attrs" /></section>
            """

            def template_data(self, kwargs, slots):
                return {"attrs": {key: "open"}}

        class Page(Component):
            citry = registry
            template = """
                <main><c-child>body</c-child></main>
            """

        with pytest.raises(RuntimeError, match=rf"Vue directive '{key}' is not supported on '<c-slot>'"):
            Page().render()

    def test_plain_slot_data_still_reaches_the_fill(self):
        registry = Citry(autodiscover=False)

        class Child(Component):
            citry = registry
            template = """
                <section><c-slot name="row" item="static" c-count="2" c-bind="extra" /></section>
            """

            def template_data(self, kwargs, slots):
                return {"extra": {"label": "spread"}}

        class Page(Component):
            citry = registry
            template = """
                <main>
                  <c-child>
                    <c-fill name="row" data="data">{{ data.item }}-{{ data.count }}-{{ data.label }}</c-fill>
                  </c-child>
                </main>
            """

        html = Page().render().serialize(ssr=False)

        assert "static-2-spread" in html
