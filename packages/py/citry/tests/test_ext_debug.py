"""Tests for the opt-in visual Debug extension."""

from __future__ import annotations

import gc
import re
import weakref
from threading import Event, Thread

import pytest

from citry import Citry, CitryContext, CitryRender, Component, Markup
from citry.citry_render import Placeholder
from citry.ext.debug import Debug
from citry.extension import Extension


def _debug_app(*, components: bool = False, slots: bool = False) -> Citry:
    return Citry(
        extensions=[Debug],
        extensions_defaults={
            "debug": {
                "highlight_components": components,
                "highlight_slots": slots,
            },
        },
    )


class TestConfiguration:
    def test_extension_is_opt_in_and_defaults_off(self):
        plain = Citry()

        class PlainCard(Component):
            citry = plain
            template = """
                <article>plain</article>
            """

        configured = Citry(extensions=[Debug])

        class ConfiguredCard(Component):
            citry = configured
            template = """
                <article>configured</article>
            """

        assert "citry-debug" not in str(PlainCard())
        assert "citry-debug" not in str(ConfiguredCard())
        assert plain.extensions.get_extension("dependencies") is not None
        with pytest.raises(ValueError, match="Extension 'debug' not found"):
            plain.extensions.get_extension("debug")

    def test_component_config_overrides_engine_default(self):
        app = _debug_app(components=True)

        class Hidden(Component):
            citry = app
            template = """
                <p>hidden</p>
            """

            class Debug:
                highlight_components = False

        class Visible(Component):
            citry = app
            template = """
                <p>visible</p>
            """

        assert "citry-debug-component" not in str(Hidden())
        assert "citry-debug-component" in str(Visible())

    def test_component_config_can_enable_factory_default(self):
        app = Citry(extensions=[Debug])

        class Card(Component):
            citry = app
            template = """
                <article><c-slot name="body" /></article>
            """

            class Debug:
                highlight_components = True
                highlight_slots = True

        html = str(Card(slots={"body": "card"}))
        assert "citry-debug-component" in html
        assert "citry-debug-slot" in html

    @pytest.mark.parametrize("field", ["highlight_component", "color"])
    def test_unknown_engine_field_fails_at_engine_creation(self, field):
        with pytest.raises(ValueError, match=field):
            Citry(extensions=[Debug], extensions_defaults={"debug": {field: True}})

    @pytest.mark.parametrize("value", [1, 0, "yes", None])
    def test_non_boolean_engine_value_is_rejected(self, value):
        with pytest.raises(ValueError, match="must be a bool"):
            Citry(
                extensions=[Debug],
                extensions_defaults={"debug": {"highlight_components": value}},
            )

    def test_invalid_component_field_fails_at_class_definition(self):
        app = Citry(extensions=[Debug])

        with pytest.raises(ValueError, match="highlight_component"):

            class Card(Component):
                citry = app

                class Debug:
                    highlight_component = True

    def test_non_boolean_component_value_fails_at_class_definition(self):
        app = Citry(extensions=[Debug])

        with pytest.raises(ValueError, match="must be a bool"):

            class Card(Component):
                citry = app

                class Debug:
                    highlight_slots = 1


class TestComponentHighlighting:
    def test_nested_components_are_highlighted_and_authored_roots_keep_markers(self):
        app = _debug_app(components=True)

        class Child(Component):
            citry = app
            template = """
                <em>child</em>
            """

        class Page(Component):
            citry = app
            template = """
                <main><c-child /></main>
            """

        html = str(Page())
        assert html.count("citry-debug-component") == 2
        assert "Page (c1):" in html
        assert "Child (c2):" in html
        assert 'style="border: 1px solid blue"' in html
        assert 'style="font-weight: bold; color: #2f14bb"' in html
        assert re.search(r'<main data-cid-c1="">', html)
        assert re.search(r'<em data-cid-c2="">child</em>', html)
        assert not re.search(r"citry-debug-component[^>]*data-cid-", html)

    def test_sibling_instances_and_repeated_slots_have_independent_boundaries(self):
        app = _debug_app(components=True, slots=True)

        class Card(Component):
            citry = app
            template = """
                <article><c-slot /><c-slot /></article>
            """

        class Page(Component):
            citry = app
            template = """
                <main><c-card>one</c-card><c-card>two</c-card></main>
            """

            class Debug:
                highlight_components = False
                highlight_slots = False

        html = str(Page())
        assert html.count("citry-debug-component") == 2
        assert html.count("Card (") == 2
        assert html.count("citry-debug-slot") == 4
        assert html.count("Card - default:") == 4
        assert html.count("one</div>") == 2
        assert html.count("two</div>") == 2
        assert "c-render-id" not in html

    def test_child_as_only_root_keeps_both_parent_and_child_markers(self):
        app = _debug_app(components=True)

        class Child(Component):
            citry = app
            template = """
                <span>child</span>
            """

        class Parent(Component):
            citry = app
            template = """
                <c-child />
            """

        html = str(Parent())
        assert re.search(r'<span data-cid-c2="" data-cid-c1="">child</span>', html)
        assert not re.search(r"citry-debug-component[^>]*data-cid-", html)

    @pytest.mark.parametrize(
        ("template", "expected"),
        [
            (
                """
                    alpha<strong>beta</strong>
                """,
                "alpha<strong",
            ),
            (
                """
                    text only
                """,
                "text only",
            ),
            (
                """

                """,
                "",
            ),
        ],
    )
    def test_multi_root_text_and_empty_output(self, template, expected):
        app = _debug_app(components=True)

        class Example(Component):
            citry = app

        Example.template = template
        html = str(Example())
        assert html.count("citry-debug-component") == 1
        assert expected in html
        assert html.endswith("</div>")

    def test_label_text_is_html_escaped(self):
        app = _debug_app(components=True)

        class Card(Component):
            citry = app
            template = """
                <p>safe</p>
            """

        Card.__name__ = '<Card & "quoted">'
        html = str(Card())
        assert "&lt;Card &amp; &#34;quoted&#34;&gt; (c1):" in html
        assert '<Card & "quoted">' not in html

    def test_full_document_boundary_is_omitted_but_child_is_highlighted(self):
        app = _debug_app(components=True)

        class Child(Component):
            citry = app
            template = """
                <p>child</p>
            """

        class Page(Component):
            citry = app
            template = """
                <!-- page -->
                <!doctype html>
                <html><head></head><body><c-child /></body></html>
            """

        html = str(Page())
        assert html.lstrip().startswith("<!-- page -->")
        assert "Page (c1):" not in html
        assert "Child (c2):" in html
        assert html.count("citry-debug-component") == 1

    def test_transparent_component_and_its_slot_add_no_boundary(self):
        app = _debug_app(components=True, slots=True)
        provide = app.get("provide")
        assert "citry-debug" not in str(provide(key="ctx", slots={"default": "body"}))

    def test_document_slot_and_enclosing_component_boundaries_are_omitted(self):
        app = _debug_app(components=True, slots=True)

        class DocumentShell(Component):
            citry = app
            template = """
                <c-slot />
            """

        document = Markup("\ufeff<!DoCtYpE HTML><HTML><head></head><body>page</body></HTML>")
        html = str(DocumentShell(slots={"default": document}))
        assert "citry-debug" not in html
        assert html.lstrip().startswith("\ufeff<!DoCtYpE HTML>")
        assert '<HTML data-cid-c1="">' in html

    def test_failed_render_is_not_swallowed(self):
        app = _debug_app(components=True)

        class Broken(Component):
            citry = app

            def on_render(self):
                msg = "broken on purpose"
                raise RuntimeError(msg)

        with pytest.raises(RuntimeError, match="broken on purpose"):
            str(Broken())


class TestSlotHighlighting:
    def test_passed_and_fallback_slots_use_receiver_label(self):
        app = _debug_app(slots=True)

        class Card(Component):
            citry = app
            template = """
                <article><c-slot name="body">fallback</c-slot></article>
            """

        passed = str(Card(slots={"body": Markup("<span>passed</span>")}))
        fallback = str(Card())
        assert "Card - body:" in passed
        assert "<span>passed</span></div>" in passed
        assert 'style="border: 1px solid #e40c0c"' in passed
        assert 'style="font-weight: bold; color: #bb1414"' in passed
        assert "Card - body:" in fallback
        assert "fallback</div>" in fallback

    def test_repeated_slot_sites_get_distinct_complete_boundaries(self):
        app = _debug_app(slots=True)

        class Card(Component):
            citry = app
            template = """
                <div><c-slot name="body" /><c-slot name="body" /></div>
            """

        html = str(Card(slots={"body": "x"}))
        assert html.count("citry-debug-slot") == 2
        assert html.count("Card - body:") == 2
        assert "c-render-id" not in html

    def test_dynamic_slot_name_is_escaped(self):
        app = _debug_app(slots=True)
        slot_name = "slot <>&\"'"

        class Card(Component):
            citry = app
            template = """
                <div><c-slot c-name="slot_name" /></div>
            """

            def template_data(self, kwargs, slots):
                return {"slot_name": slot_name}

        html = str(Card(slots={slot_name: "safe"}))
        assert "Card - slot &lt;&gt;&amp;&#34;&#39;:" in html
        assert slot_name not in html

    def test_nested_component_inside_slot_keeps_nested_boundary_order(self):
        app = _debug_app(components=True, slots=True)

        class Leaf(Component):
            citry = app
            template = """
                <i>leaf</i>
            """

        class Card(Component):
            citry = app
            template = """
                <section><c-slot name="body" /></section>
            """

        class Page(Component):
            citry = app
            template = """
                <c-card><c-fill name="body"><c-leaf /></c-fill></c-card>
            """

        html = str(Page())
        slot_at = html.index("citry-debug-slot")
        leaf_at = html.index("Leaf (c3):")
        assert slot_at < leaf_at
        assert html.count("citry-debug-component") == 3
        assert html.count("citry-debug-slot") == 1


class TestSerialization:
    @pytest.mark.parametrize("strategy", ["ignore", "simple", "document", "fragment"])
    def test_every_dependency_strategy_resolves_boundaries(self, strategy):
        app = _debug_app(components=True)

        class Card(Component):
            citry = app
            template = """
                <p>card</p>
            """

        html = Card().render().serialize(deps_strategy=strategy)
        assert "citry-debug-component" in html
        assert "c-render-id" not in html

    def test_repeated_serialization_is_stable_and_dependencies_stay_present(self):
        app = _debug_app(components=True)

        class Card(Component):
            citry = app
            template = """
                <article>card</article>
            """
            css = """
                article { color: purple; }
            """

        rendered = Card().render()
        first = rendered.serialize(deps_strategy="simple")
        second = rendered.serialize(deps_strategy="simple")
        assert first == second
        assert "article { color: purple; }" in first
        assert "citry-debug-component" in first

    def test_same_render_can_use_different_dependency_strategies(self):
        app = _debug_app(components=True)

        class Card(Component):
            citry = app
            template = """
                <article>card</article>
            """

        rendered = Card().render()
        outputs = [
            rendered.serialize(deps_strategy=strategy) for strategy in ("ignore", "simple", "document", "fragment")
        ]
        assert all(output.count("citry-debug-component") == 1 for output in outputs)
        assert all("c-render-id" not in output for output in outputs)

    def test_debug_preserves_dependency_event_key_and_ownership_markers(self):
        app = _debug_app(components=True)

        class Widget(Component):
            citry = app
            template = """
                <section class="widget">widget</section>
            """
            css = """
                .widget { color: var(--tone); }
            """

            class Events:
                def save(self):
                    return None

            def css_data(self, kwargs, slots):
                return {"tone": "purple"}

        class Page(Component):
            citry = app
            template = """
                <main><c-widget #c-key="'stable'" /></main>
            """

            class Debug:
                highlight_components = False

        html = Page().render().serialize(deps_strategy="document")
        section = re.search(r"<section[^>]*>", html)
        assert section is not None
        assert 'data-cid-c2=""' in section.group()
        assert 'data-cid="c2"' in section.group()
        assert "data-ccss-" in section.group()
        assert "data-citry-key" not in section.group()
        assert '"morphKey":"stable"' in html
        assert not re.search(r"citry-debug-component[^>]*data-(?:cid|ccss|citry-key)", html)
        assert '<script type="application/json" data-citry-graph>' in html
        assert '<script type="application/json" data-citry-events>' in html
        assert ".widget { color: var(--tone); }" in html

    @pytest.mark.parametrize("side", ["open", "close"])
    def test_extension_after_debug_can_drop_one_side_without_leaking_marker(self, side):
        class DropBoundary(Extension):
            name = "drop_boundary"

            def on_component_rendered(self, ctx):
                if not isinstance(ctx.render, CitryRender):
                    return None
                if not ctx.render.parts or not isinstance(ctx.render.parts[0], Placeholder):
                    return None
                parts = ctx.render.parts[1:] if side == "open" else ctx.render.parts[:-1]
                return CitryRender(parts=parts, context=ctx.render.context)

        app = Citry(
            extensions=[Debug, DropBoundary],
            extensions_defaults={"debug": {"highlight_components": True}},
        )

        class Card(Component):
            citry = app
            template = """
                <p>card</p>
            """

        html = str(Card())
        assert "card" in html
        assert "citry-debug" not in html
        assert "c-render-id" not in html

    def test_debug_highlights_output_replaced_by_an_earlier_extension(self):
        class ReplaceOutput(Extension):
            name = "replace_output"

            def on_component_rendered(self, ctx):
                return "<strong>replacement</strong>"

        app = Citry(
            extensions=[ReplaceOutput, Debug],
            extensions_defaults={"debug": {"highlight_components": True}},
        )

        class Card(Component):
            citry = app
            template = """
                <p>original</p>
            """

        html = str(Card())
        assert "citry-debug-component" in html
        assert '<strong data-cid-c1="">replacement</strong>' in html
        assert "original" not in html

    def test_recovery_before_debug_is_highlighted(self):
        class Recover(Extension):
            name = "recover"

            def on_component_rendered(self, ctx):
                if ctx.error is not None:
                    return "<strong>recovered</strong>"
                return None

        app = Citry(
            extensions=[Recover, Debug],
            extensions_defaults={"debug": {"highlight_components": True}},
        )

        class Broken(Component):
            citry = app

            def on_render(self):
                msg = "recover me"
                raise RuntimeError(msg)

        class Host(Component):
            citry = app
            template = """
                <main><c-broken /></main>
            """

        html = str(Host())
        assert "citry-debug-component" in html
        assert '<strong data-cid-c1="">recovered</strong>' in html

    def test_recovery_after_debug_is_not_highlighted(self):
        class Recover(Extension):
            name = "recover"

            def on_component_rendered(self, ctx):
                if ctx.error is not None:
                    return "<strong>recovered</strong>"
                return None

        app = Citry(
            extensions=[Debug, Recover],
            extensions_defaults={"debug": {"highlight_components": True}},
        )

        class Broken(Component):
            citry = app

            def on_render(self):
                msg = "recover me"
                raise RuntimeError(msg)

        class Host(Component):
            citry = app
            template = """
                <main><c-broken /></main>
            """

        html = str(Host())
        assert "citry-debug" not in html
        assert '<strong data-cid-c1="">recovered</strong>' in html

    def test_unresolved_placeholder_is_empty_for_component_root(self):
        app = Citry()

        class PlaceholderComponent(Component):
            citry = app

            def on_render(self):
                return CitryRender(parts=[Placeholder("unowned")], context=CitryContext())

        assert str(PlaceholderComponent()) == ""

    def test_unresolved_placeholder_is_empty_for_componentless_root(self):
        rendered = CitryRender(parts=["left", Placeholder("unowned"), "right"], context=CitryContext())
        assert rendered.serialize(deps_strategy="ignore") == "leftright"


class TestCrossCitryEmbedding:
    def _foreign_render(self):
        foreign_app = _debug_app(components=True)

        class Foreign(Component):
            citry = foreign_app
            template = """
                <aside>foreign</aside>
            """

        return Foreign().render()

    def test_root_debug_resolves_embedded_debug_boundaries(self):
        foreign = self._foreign_render()
        root_app = _debug_app(components=True)

        class Host(Component):
            citry = root_app
            template = """
                <main>{{ foreign }}</main>
            """

            def template_data(self, kwargs, slots):
                return {"foreign": foreign}

        html = Host().render().serialize(deps_strategy="ignore")
        assert "Host (c2):" in html
        assert "Foreign (c1):" in html
        assert html.count("citry-debug-component") == 2

    def test_root_without_debug_omits_embedded_boundary_but_keeps_content(self):
        foreign = self._foreign_render()
        root_app = Citry()

        class Host(Component):
            citry = root_app
            template = """
                <main>{{ foreign }}</main>
            """

            def template_data(self, kwargs, slots):
                return {"foreign": foreign}

        html = Host().render().serialize(deps_strategy="ignore")
        assert "foreign" in html
        assert "citry-debug" not in html
        assert "c-render-id" not in html


class TestLifetime:
    def test_cache_bypass_index_serializes_lookup_and_unregistration(self):
        app = _debug_app(components=True)

        class Card(Component):
            citry = app

        extension = app.extensions.get_extension("debug")

        def assert_waits_for_index_lock(operation):
            started = Event()
            completed = Event()

            def run():
                started.set()
                operation()
                completed.set()

            worker = Thread(target=run)
            with extension._registered_components_lock:
                worker.start()
                assert started.wait(timeout=1)
                assert not completed.wait(timeout=0.01)
            assert completed.wait(timeout=1)
            worker.join()

        assert_waits_for_index_lock(extension.render_cache_bypass_reason)
        assert_waits_for_index_lock(lambda: app.unregister(Card))

    def test_debug_does_not_retain_unregistered_rendered_component_class(self):
        app = _debug_app(components=True, slots=True)

        def render_and_unregister():
            class Ephemeral(Component):
                citry = app
                template = """
                    <div><c-slot>body</c-slot></div>
                """

            class_ref = weakref.ref(Ephemeral)
            str(Ephemeral())
            app.unregister(Ephemeral)
            return class_ref

        class_ref = render_and_unregister()
        gc.collect()
        assert class_ref() is None
