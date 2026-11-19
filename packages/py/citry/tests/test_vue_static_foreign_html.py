"""
HTML that Citry did not compile, inside a Vue app.

A template with foreign spans (tags another engine renders, such as Django's
`{% %}` tags) compiles for static output, so its parts are plain strings.
Inside a Vue app the Vue writer joins those strings, and the parts beside
them that need no Vue, into one static block that the browser inserts
without compiling. These tests use a small foreign provider that replaces
each `{% name %}` span with fixed HTML, as Django would write it.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from citry import (
    Citry,
    Component,
    Extension,
    ForeignSpan,
    ForeignSpanSet,
    IncompleteStaticHtmlError,
    Markup,
    ScriptInStaticHtmlError,
    StaticHtmlError,
    StaticHtmlPlacementError,
    VueInsideStaticHtmlError,
    VueSyntaxInStaticHtmlError,
)
from citry._vue.capture import _validate_prepared_render, render_prepared_direct
from citry._vue.direct_capture import assemble_typed_render
from citry.citry_render import CitryRender
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for
from citry.ext.events.results import RenderEncodingContext, encode_actions
from citry.nodes import ForeignNode

# What each foreign span renders to: the HTML another engine would write.
_FOREIGN_HTML = {
    "{% word %}": "Hello &amp; bye",
    "{% bold %}": "<b>yes</b>",
    "{% open %}": "<div>",
    "{% script %}": "<script>globalThis.ran = true</script>",
    "{% noscript %}": "<noscript><img src=x></noscript>",
    # Vue syntax that data could carry: it must stay text and plain attributes.
    "{% vue %}": '{{ 7*7 }} <i v-html="evil" @click="alert(1)" :title="x" #default>t</i>',
}


class _Foreign(Extension):
    name = "test_static_foreign_html"

    def on_template_foreign_spans(self, ctx: Any) -> ForeignSpanSet:
        content = ctx.content.encode()
        return ForeignSpanSet(
            tuple(
                ForeignSpan(match.start(), match.end(), may_control_body=True)
                for match in re.finditer(rb"\{%.*?%\}", content)
            )
        )

    def on_template_foreign_compiled(self, ctx: Any) -> None:
        ctx.nodes[:] = [_FOREIGN_HTML[node.text] if isinstance(node, ForeignNode) else node for node in ctx.nodes]
        ctx.mark_resolved(*ctx.claims)


def _engine() -> Citry:
    engine = Citry(autodiscover=False, extensions=[_Foreign], secret="static-foreign-html-secret")  # noqa: S106
    engine.set_mounted_prefix("/citry")
    return engine


def _components(engine: Citry) -> dict[str, type[Component]]:
    class Modal(Component):
        citry = engine

        class Kwargs:
            title: str = ""

        class State(Kwargs):
            pass

        class Events:
            def close(self, state: Any) -> Any:
                return Modal(title="closed")

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"title": kwargs.title}

        template = """
<div class="modal"><h2>{{ title }}</h2><c-slot /><button @c-click="close">x</button></div>
"""

    class Badge(Component):
        citry = engine

        class Kwargs:
            color: str = "red"

        def css_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"badge-color": kwargs.color}

        template = """
<span class="badge">B</span>
"""
        css = """
.badge { color: var(--badge-color); }
"""

    class StaticLink(Component):
        citry = engine
        template = """
<a href="/home">{% word %}</a>
"""

    class Box(Component):
        citry = engine

        class Kwargs:
            n: int = 0

        class State(Kwargs):
            pass

        class Events:
            def inc(self, state: Any) -> Any:
                return Box(n=state.n + 1)

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"n": kwargs.n}

        template = """
<div><button @c-click="inc">{{ n }}</button><c-static-link /></div>
"""

    return {"Modal": Modal, "Badge": Badge, "StaticLink": StaticLink, "Box": Box}


def _configuration(html: str) -> dict[str, Any]:
    match = re.search(r'data-citry-vue-document="[^"]+">(.*?)</script>', html, re.DOTALL)
    assert match is not None, html
    return json.loads(match.group(1))


def _opaque_records(configuration: dict[str, Any]) -> list[str]:
    return [
        record["html"]
        for occurrence in configuration["manifest"]["occurrences"]
        for record in occurrence["preparedData"].get("opaqueHtml", {}).values()
    ]


def _host(html: str) -> str:
    start = html.index('<div id="citry-vue-')
    return html[start : html.index("<script", start)]


# An occurrence id in the shape the browser runtime generates.
_OCCURRENCE = "citryOccurrence" + "a" * 24


def _tag_for_type(type_key: str) -> str:
    return f"x-{type_key.lower().replace('_', '-')}"


class TestFills:
    """A fill written in a template with foreign spans, passed to an interactive component."""

    def test_value_tag_in_a_fill_becomes_a_text_value(self) -> None:
        engine = _engine()
        _components(engine)
        html = engine.render_template("<c-modal title='t'>{% word %}</c-modal>", {}).serialize()
        assert "Hello &amp; bye" in _host(html)
        # Text without tags needs no static block.
        assert _opaque_records(_configuration(html)) == []

    def test_block_output_in_a_fill_becomes_one_static_block(self) -> None:
        engine = _engine()
        _components(engine)
        html = engine.render_template("<c-modal title='t'>{% bold %} and <i>more</i></c-modal>", {}).serialize()
        assert _opaque_records(_configuration(html)) == ["<b>yes</b> and <i>more</i>"]
        assert "<b>yes</b> and <i>more</i>" in _host(html)

    def test_a_static_component_inside_the_fill_joins_the_block_with_its_markers_and_styles(self) -> None:
        engine = _engine()
        _components(engine)
        rendered = engine.render_template("<c-modal title='t'><ul><li><c-badge />{% word %}</li></ul></c-modal>", {})
        configuration = _configuration(rendered.serialize())
        [block] = _opaque_records(configuration)
        # The badge keeps the marker its css_data() stylesheet selects.
        assert re.fullmatch(
            r'<ul><li>\s*<span class="badge" data-ccss-[0-9a-f]+="">B</span>\s*Hello &amp; bye</li></ul>', block
        )
        occurrences = configuration["manifest"]["occurrences"]
        assert [item["typeKey"].split("_")[0] for item in occurrences] == ["TemplateRoot", "Modal"]
        # Both badge stylesheets load with the component whose template holds the block.
        root_id = configuration["manifest"]["rootId"]
        styles = configuration["manifest"]["styles"]
        assert len(styles) == 2
        assert all(style["owner"]["occurrenceIds"] == [root_id] for style in styles)

    def test_a_static_component_with_a_fill_inside_an_element_of_the_html_joins_the_block(self) -> None:
        engine = _engine()
        _components(engine)

        class Card(Component):
            citry = engine
            template = """
<div class="card"><c-slot /></div>
"""

        assert Card
        html = engine.render_template(
            "<c-modal title='t'><ul><li>{% word %}<c-card>{% bold %}</c-card></li></ul></c-modal>", {}
        ).serialize()
        assert _opaque_records(_configuration(html)) == [
            '<ul><li>Hello &amp; bye\n<div class="card"><b>yes</b></div>\n</li></ul>'
        ]

    def test_a_provide_inside_an_element_of_the_html_joins_the_block(self) -> None:
        engine = _engine()
        _components(engine)
        html = engine.render_template(
            "<c-modal title='t'><p>{% word %}<c-provide key='k' c-value='1'><b>x</b></c-provide></p></c-modal>", {}
        ).serialize()
        assert _opaque_records(_configuration(html)) == ["<p>Hello &amp; bye<b>x</b></p>"]

    def test_a_mark_keeps_its_vue_occurrence_so_a_render_can_find_it(self) -> None:
        engine = _engine()
        _components(engine)
        html = engine.render_template(
            "<c-modal title='t'>{% word %}<c-mark name='m'><b>x</b></c-mark></c-modal>", {}
        ).serialize()
        configuration = _configuration(html)
        assert [marker["name"] for marker in configuration["manifest"]["markers"]] == ["m"]
        with pytest.raises(
            VueInsideStaticHtmlError, match=r"The component Mark, which needs Vue, sits inside an element"
        ):
            engine.render_template(
                "<c-modal title='t'><p>{% word %}<c-mark name='m'><b>x</b></c-mark></p></c-modal>", {}
            ).serialize()

    def test_line_breaks_around_an_interactive_component_keep_the_page_hydrating(self) -> None:
        engine = _engine()
        _components(engine)
        rendered = engine.render_template("\n<c-modal title='t'>{% bold %}</c-modal>\n", {})
        html = rendered.serialize()
        assert '"hydrate":true' in html
        assert _opaque_records(_configuration(html)) == ["<b>yes</b>"]

    def test_an_interactive_component_beside_static_html_in_a_fill_stays_a_vue_component(self) -> None:
        engine = _engine()
        _components(engine)
        html = engine.render_template(
            "<c-modal title='outer'>{% bold %}<c-modal title='inner'>a</c-modal></c-modal>", {}
        ).serialize()
        configuration = _configuration(html)
        assert [item["typeKey"].split("_")[0] for item in configuration["manifest"]["occurrences"]] == [
            "TemplateRoot",
            "Modal",
            "Modal",
        ]
        assert _opaque_records(configuration) == ["<b>yes</b>"]

    def test_vue_syntax_in_the_html_stays_data_and_never_reaches_the_compiled_template(self) -> None:
        engine = _engine()
        components = _components(engine)

        class Page(Component):
            citry = engine
            template = """
<c-modal title='t'>{% vue %}</c-modal>
"""

        assembly = assemble_typed_render(render_prepared_direct(Page()), revision=0, tag_for_type=_tag_for_type)
        templates = [item.template for item in assembly.compile_inputs.values()]
        assert all("7*7" not in template and "evil" not in template for template in templates)
        assert any("<citry-opaque-html" in template for template in templates)
        html = engine.render_template("<c-page />", {}).serialize()
        assert _opaque_records(_configuration(html)) == [_FOREIGN_HTML["{% vue %}"]]
        assert components["Modal"]


class TestRefusals:
    def test_unbalanced_html_is_refused(self) -> None:
        engine = _engine()
        _components(engine)
        with pytest.raises(
            IncompleteStaticHtmlError, match=r"did not compile .* is not a complete HTML fragment: '<div>x'"
        ):
            engine.render_template("<c-modal title='t'>{% open %}x</c-modal>", {}).serialize()

    def test_an_interactive_component_inside_an_element_of_the_html_is_refused(self) -> None:
        engine = _engine()
        _components(engine)
        with pytest.raises(
            VueInsideStaticHtmlError, match=r"The component Modal, which needs Vue, sits inside an element"
        ):
            engine.render_template(
                "<c-modal title='outer'><div>{% bold %}<c-modal title='inner'>a</c-modal></div></c-modal>", {}
            ).serialize()

    def test_unbalanced_html_after_an_interactive_component_is_named_as_unbalanced(self) -> None:
        engine = _engine()
        _components(engine)
        with pytest.raises(IncompleteStaticHtmlError, match=r"is not a complete HTML fragment: '<div>x'"):
            engine.render_template(
                "<c-modal title='t'><c-modal title='in'>a</c-modal>{% open %}x</c-modal>", {}
            ).serialize()

    @pytest.mark.parametrize("template", ['<a @click="go">{% word %}</a>', '<a :title="x">{% word %}</a>'])
    def test_vue_syntax_in_a_component_template_with_foreign_spans_is_refused(self, template: str) -> None:
        engine = _engine()
        components = _components(engine)

        class Linked(Component):
            citry = engine

        Linked.template = template

        class Holder(Component):
            citry = engine
            template = """
<div><button @click="1">b</button><c-linked /></div>
"""

        assert Holder
        assert components
        with pytest.raises(VueSyntaxInStaticHtmlError, match=r"Linked has Vue syntax \('(@click|:title)' on <a>\)"):
            engine.render_template("<c-holder />", {}).serialize()

    def test_vue_syntax_in_a_static_component_inside_the_html_is_refused(self) -> None:
        engine = _engine()
        _components(engine)

        class Linked(Component):
            citry = engine
            template = """
<a v-if="1">{% word %}</a>
"""

        assert Linked
        with pytest.raises(VueSyntaxInStaticHtmlError, match=r"Linked has Vue syntax \('v-if' on <a>\)"):
            engine.render_template("<c-modal title='t'><p>{% bold %}<c-linked /></p></c-modal>", {}).serialize()

    @pytest.mark.parametrize(
        "html",
        [
            "<script>1</script>",
            "<SCRIPT>1</SCRIPT>",
            "<svg><script>1</script></svg>",
            "<template><script>1</script></template>",
        ],
    )
    def test_each_spelling_of_a_script_is_refused(self, html: str) -> None:
        engine = _engine()
        _components(engine)
        _FOREIGN_HTML["{% spelled %}"] = html
        try:
            with pytest.raises(ScriptInStaticHtmlError, match=r"holds a <script> element"):
                engine.render_template("<c-modal title='t'>{% spelled %}</c-modal>", {}).serialize()
        finally:
            del _FOREIGN_HTML["{% spelled %}"]

    def test_a_script_is_refused(self) -> None:
        engine = _engine()
        _components(engine)
        with pytest.raises(ScriptInStaticHtmlError, match=r"holds a <script> element"):
            engine.render_template("<c-modal title='t'>{% script %}</c-modal>", {}).serialize()

    def test_a_noscript_is_refused(self) -> None:
        engine = _engine()
        _components(engine)
        with pytest.raises(ScriptInStaticHtmlError, match=r"holds a <noscript> element"):
            engine.render_template("<c-modal title='t'>{% noscript %}</c-modal>", {}).serialize()

    def test_html_inside_svg_is_refused(self) -> None:
        engine = _engine()

        class Picture(Component):
            citry = engine
            template = """
<svg @click="1"><c-slot /></svg>
"""

        assert Picture
        with pytest.raises(StaticHtmlPlacementError, match=r"cannot sit inside <svg> or <math>"):
            engine.render_template("<c-picture>{% bold %}</c-picture>", {}).serialize()

    @pytest.mark.parametrize(
        ("error", "built_in"),
        [
            (IncompleteStaticHtmlError, ValueError),
            (VueInsideStaticHtmlError, ValueError),
            (ScriptInStaticHtmlError, ValueError),
            (VueSyntaxInStaticHtmlError, TypeError),
            (StaticHtmlPlacementError, TypeError),
        ],
    )
    def test_each_refusal_keeps_the_built_in_type_it_had(self, error: type[Exception], built_in: type) -> None:
        # Code that caught the built-in type before these classes existed
        # still catches each refusal.
        assert issubclass(error, StaticHtmlError)
        assert issubclass(error, built_in)

    def test_a_refusal_names_its_component_and_tag(self) -> None:
        engine = _engine()
        _components(engine)
        with pytest.raises(VueInsideStaticHtmlError) as inside:
            engine.render_template(
                "<c-modal title='outer'><div>{% bold %}<c-modal title='inner'>a</c-modal></div></c-modal>", {}
            ).serialize()
        assert inside.value.component_name == "Modal"
        with pytest.raises(ScriptInStaticHtmlError) as script:
            engine.render_template("<c-modal title='t'>{% script %}</c-modal>", {}).serialize()
        assert script.value.tag == "script"

    def test_an_interactive_component_that_a_block_wraps_inside_an_element_is_named(self) -> None:
        # A block around the component, such as Django's `{% if %}` or a
        # `<c-for>` loop, hands it on inside a render that is not a component.
        engine = _engine()
        _components(engine)
        with pytest.raises(VueInsideStaticHtmlError) as caught:
            engine.render_template(
                "<c-modal title='o'><div>{% word %}<c-for each='x in [1]'><c-modal title='i'>a</c-modal></c-for>"
                "</div></c-modal>",
                {},
            ).serialize()
        assert caught.value.component_name == "Modal"
        assert str(caught.value).startswith(
            "The component Modal, which needs Vue, sits inside an element of HTML that Citry did not compile"
        )
        assert "inside a block that wraps it" in str(caught.value)
        assert "Move Modal out of the element" in str(caught.value)

    @pytest.mark.parametrize(
        "template",
        [
            # Vue syntax in the template passed to render_template() itself.
            "<c-modal title='t'>x</c-modal><a @click='go'>{% word %}</a>",
            # In a fill written there.
            "<c-modal title='t'><a @click='go'>{% word %}</a></c-modal>",
        ],
    )
    def test_vue_syntax_in_a_render_template_source_with_foreign_spans_is_refused(self, template: str) -> None:
        engine = _engine()
        _components(engine)
        with pytest.raises(
            VueSyntaxInStaticHtmlError, match=r"The template <render_template> has Vue syntax"
        ) as caught:
            engine.render_template(template, {}).serialize()
        assert caught.value.component_name is None
        assert caught.value.syntax == "'@click' on <a>"

    def test_vue_syntax_in_a_transparent_component_with_foreign_spans_is_refused(self) -> None:
        # A transparent component's body is written into its parent's
        # template, so its own template must be the one checked.
        engine = _engine()

        class Plain(Component):
            citry = engine
            transparent = True
            template = """
<a @click="go">{% word %}</a>
"""

        class Holder(Component):
            citry = engine
            template = """
<div><button @click="1">b</button><c-plain /></div>
"""

        assert Plain
        assert Holder
        with pytest.raises(VueSyntaxInStaticHtmlError, match=r"Plain has Vue syntax \('@click' on <a>\)"):
            engine.render_template("<c-holder />", {}).serialize()

    def test_vue_syntax_in_a_template_with_foreign_spans_on_a_page_without_vue_is_kept(self) -> None:
        # Without a Vue app, the template's output is the page itself, and
        # nothing drops the attribute.
        engine = _engine()
        html = engine.render_template('<a @click="go">{% word %}</a>', {}).serialize()
        assert '<a @click="go">Hello &amp; bye</a>' in html

    def test_a_marker_attribute_written_by_the_html_stays_a_plain_attribute_of_the_block(self) -> None:
        engine = _engine()
        _FOREIGN_HTML["{% marker %}"] = '<p data-cid-x="">forged</p>'
        try:

            class Rooted(Component):
                citry = engine
                template = """
{% marker %}
"""

            class Holder(Component):
                citry = engine
                template = """
<button @click="1">b</button><c-rooted />
"""

            assert Rooted
            assert Holder
            html = engine.render_template("<c-holder />", {}).serialize()
        finally:
            del _FOREIGN_HTML["{% marker %}"]
        # Citry adds no marker to a component without root markers, so the
        # attribute stays a plain attribute of the static block.
        assert _opaque_records(_configuration(html)) == ['\n<p data-cid-x="">forged</p>\n']


class TestOutputChecks:
    """The opt-in output checks read the static block as they read a `Markup` value."""

    @staticmethod
    def _engine_with(**settings: Any) -> Citry:
        engine = Citry(
            autodiscover=False,
            extensions=[_Foreign],
            secret="static-foreign-html-secret",  # noqa: S106
            **settings,
        )
        engine.set_mounted_prefix("/citry")
        _components(engine)
        return engine

    def test_strict_csp_refuses_an_inline_handler_in_the_html(self) -> None:
        engine = self._engine_with(security_csp="strict")
        _FOREIGN_HTML["{% handler %}"] = '<img src="x" onerror="globalThis.ran = true">'
        try:
            rendered = engine.render_template("<c-modal title='t'>{% handler %}</c-modal>", {})
            with pytest.raises(ValueError, match=r"strict-CSP incompatibility(.|\n)*'onerror'"):
                rendered.serialize(csp_nonce="nonce-value")
        finally:
            del _FOREIGN_HTML["{% handler %}"]
        # The same page without the handler passes, so the handler is what the check refused.
        engine.render_template("<c-modal title='t'>{% bold %}</c-modal>", {}).serialize(csp_nonce="nonce-value")

    def test_javascript_warn_reports_an_inline_handler_in_the_html(self) -> None:
        engine = self._engine_with(security_javascript="warn")
        _FOREIGN_HTML["{% handler %}"] = '<img src="x" onerror="globalThis.ran = true">'
        try:
            with pytest.warns(Warning, match=r"onerror"):
                engine.render_template("<c-modal title='t'>{% handler %}</c-modal>", {}).serialize()
        finally:
            del _FOREIGN_HTML["{% handler %}"]


def _event_blocks(engine: Citry, component: type[Component], element: Any, handler: str) -> list[str]:
    """Encode an Events `Render` of `element` for `component`'s handler and return its static blocks."""
    dispatcher = dispatcher_for(engine)
    resolved = engine.extensions.get_extension("events").resolve(component).handlers[handler]
    context = RenderEncodingContext(
        engine,
        _OCCURRENCE,
        resolved,
        "http",
        "vue-prepared/1",
        headers={
            "x-citry-vue-app": "app",
            "x-citry-vue-occurrence": _OCCURRENCE,
            "x-citry-vue-revision": "3",
        },
    )
    [encoded] = encode_actions(
        [actions.Render(element)],
        instance_id="c9zk1q00",
        handler=handler,
        render_encoder=dispatcher._render_encoders["vue-prepared/1"],
        render_context=context,
    )
    return [
        record["html"]
        for occurrence in encoded["prepared"]["occurrences"]
        for record in occurrence["preparedData"].get("opaqueHtml", {}).values()
    ]


def _panel(engine: Citry, note_template: str) -> type[Component]:
    """An interactive panel holding a static component with `note_template`, which prints `{{ note }}`."""

    class Note(Component):
        citry = engine

        class Kwargs:
            note: Any = ""

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"note": kwargs.note}

    Note.template = note_template

    class Panel(Component):
        citry = engine

        class Kwargs:
            note: Any = ""

        class State(Kwargs):
            pass

        class Events:
            def bump(self, state: Any) -> Any:
                return Panel(note=state.note)

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"note": kwargs.note}

        template = """
<div><button @c-click="bump">+</button><c-note c-note="note" /></div>
"""

    assert Note
    return Panel


class TestEventsRerender:
    def test_a_component_with_a_static_foreign_child_renders_through_an_events_render(self) -> None:
        engine = _engine()
        components = _components(engine)
        box = components["Box"]
        assert _event_blocks(engine, box, box(n=2), "inc") == ['\n<a href="/home">Hello &amp; bye</a>\n']

    def test_a_value_printed_in_a_template_with_foreign_spans_renders_as_on_the_page(self) -> None:
        # A template compiled for static output writes each `{{ }}` as a
        # `Markup` part, which the page always accepted and an event refused.
        engine = _engine()
        panel = _panel(engine, '{% word %}<p class="note">{{ note }}</p>{% word %}')
        page_blocks = _opaque_records(_configuration(engine.render_template("<c-panel note='a&b' />", {}).serialize()))
        event_blocks = _event_blocks(engine, panel, panel(note="a&b"), "bump")
        assert event_blocks == page_blocks == ['Hello &amp; bye<p class="note">a&amp;b</p>Hello &amp; bye']

    def test_an_event_refuses_a_value_the_page_refuses(self) -> None:
        # Accepting the `Markup` part must not skip the checks the page
        # applies to the block that holds it.
        engine = _engine()
        panel = _panel(engine, "{% word %}<p>{{ note }}</p>")
        value = Markup("<noscript><img src=x></noscript>")
        with pytest.raises(ScriptInStaticHtmlError, match=r"holds a <noscript> element"):
            engine.render_template("<c-panel c-note='value' />", {"value": value}).serialize()
        with pytest.raises(ScriptInStaticHtmlError, match=r"holds a <noscript> element"):
            _event_blocks(engine, panel, panel(note=value), "bump")

    def test_an_event_still_refuses_raw_output_the_writer_does_not_know(self) -> None:
        engine = _engine()
        components = _components(engine)

        class Text(str):
            __slots__ = ()

        rendered = render_prepared_direct(components["StaticLink"]())
        # A `str` subclass is not HTML a template compiled for static output
        # wrote, so neither the page writer nor an event accepts it.
        with pytest.raises(TypeError, match=r"unsupported raw output: Text"):
            _validate_prepared_render(
                CitryRender([*rendered.parts, Text("x")], rendered.context, render_target="prepared")
            )

    def test_vue_syntax_in_a_template_with_foreign_spans_is_refused_in_an_event(self) -> None:
        engine = _engine()
        panel = _panel(engine, '{% word %}<p @click="go">{{ note }}</p>')
        with pytest.raises(VueSyntaxInStaticHtmlError, match=r"Note has Vue syntax \('@click' on <p>\)"):
            _event_blocks(engine, panel, panel(note="a"), "bump")
