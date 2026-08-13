"""Render-scoped i18n usage and cache replay metadata."""

from decimal import Decimal

from citry import Citry, Component, FormatRegistry, InMemoryCache, NumberFormat
from citry.ext.i18n.usage import (
    AMBIENT_CLIENT_OWNER,
    CLIENT_CONTEXT_KEY,
    EXTRA_KEY,
    MessageOutputUse,
    ProfileUse,
)


def configured_app(*, cache=None) -> Citry:
    return Citry(
        cache=cache,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
                "formats": FormatRegistry(number={"measurement": NumberFormat()}),
            }
        },
    )


def test_records_template_data_and_composite_template_calls_without_values() -> None:
    app = configured_app()

    class Greeting(Component):
        citry = app

        class Kwargs:
            name: str

        class I18n:
            client_messages = ("future-message",)

        def template_data(self, kwargs, slots):
            return {
                "name": kwargs.name,
                "prepared": self.i18n.tr("prepared-message", name=kwargs.name),
                "amount": self.i18n.format.number(Decimal("12.5"), format="measurement"),
                "parsed": self.i18n.parse.number("12.5", format="measurement").state,
            }

        template = """
            {{ prepared }}
            {{ "<" + tr("first-message") + ">" + tr("second-message") }}
            {{ amount }} {{ parsed }}
            <span x-text="$i18n.tr('browser-message')"></span>
        """
        js = """
            const i18n = unrelated;
            i18n.tr("not-a-component-call");
            $component(({ i18n: localeService }) => {
                localeService.tr("component-browser-message");
                localeService.bind({
                    message: "bound-browser-message",
                    output: "label",
                    onChange: applyMessage,
                });
            });
        """
        messages = """
            # @param {str} $name - User name.
            prepared-message = Hello, { $name }
            first-message = First
            second-message = Second
            browser-message = Browser
            component-browser-message = Component browser
            bound-browser-message = Bound browser
                .label = Bound label
            not-a-component-call = Not a component call
            future-message = Future
        """

    rendered = Greeting(name="Ada").render()
    record = next(iter(rendered.context.extra[EXTRA_KEY].values()))

    assert record.client_messages == ("future-message",)
    assert record.client_outputs == (
        MessageOutputUse("browser-message", None),
        MessageOutputUse("component-browser-message", None),
        MessageOutputUse("bound-browser-message", "label"),
    )
    assert record.server_usage.messages == (
        MessageOutputUse("prepared-message", None),
        MessageOutputUse("first-message", None),
        MessageOutputUse("second-message", None),
    )
    assert record.server_usage.formats == (ProfileUse("number", "measurement"),)
    assert record.server_usage.parsers == (ProfileUse("number", "measurement"),)
    assert "Ada" not in repr(record)
    assert "12.5" not in repr(record)


def test_nested_component_usage_merges_into_the_root_render() -> None:
    app = configured_app()

    class Child(Component):
        citry = app
        template = '{{ tr("child-message") }}'
        messages = "child-message = Child"

    class Page(Component):
        citry = app
        template = '<main>{{ tr("page-message") }}<c-Child /></main>'
        messages = "page-message = Page"

    rendered = Page().render()
    records = rendered.context.extra[EXTRA_KEY]

    assert [record.class_id for record in records.values()] == [Page.class_id, Child.class_id]
    assert [record.server_usage.messages for record in records.values()] == [
        (MessageOutputUse("page-message", None),),
        (MessageOutputUse("child-message", None),),
    ]


def test_explicit_service_calls_outside_a_component_do_not_enter_render_metadata() -> None:
    app = configured_app()

    class Page(Component):
        citry = app
        template = "Page"
        messages = "direct-message = Direct"

    i18n = app.extensions.get_extension("i18n")
    context = i18n.make_context(locale="en-US")
    assert i18n.for_context(context).tr("direct-message") == "Direct"

    rendered = Page().render(provides={"citry_i18n": context})
    record = next(iter(rendered.context.extra[EXTRA_KEY].values()))
    assert record.server_usage.empty


def test_render_cache_replays_usage_with_the_fresh_component_id() -> None:
    cache = InMemoryCache()
    app = configured_app(cache=cache)
    calls = 0

    class CachedGreeting(Component):
        citry = app

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return self.component.i18n.context.identity

        def template_data(self, kwargs, slots):
            nonlocal calls
            calls += 1
            return super().template_data(kwargs, slots)

        template = '{{ tr("cached-message") }}<span x-text="$i18n.tr(\'cached-client\')"></span>'
        messages = """
            cached-message = Cached
            cached-client = Cached client
        """

    first = CachedGreeting().render()
    second = CachedGreeting().render()
    first_record = next(iter(first.context.extra[EXTRA_KEY].values()))
    second_record = next(iter(second.context.extra[EXTRA_KEY].values()))

    assert calls == 1
    assert first_record.render_id != second_record.render_id
    assert first_record.server_usage.messages == (MessageOutputUse("cached-message", None),)
    assert second_record.server_usage.messages == first_record.server_usage.messages
    assert first_record.client_outputs == (MessageOutputUse("cached-client", None),)
    assert second_record.client_outputs == first_record.client_outputs


def test_render_cache_remaps_translation_binding_records_and_html_markers() -> None:
    cache = InMemoryCache()
    app = configured_app(cache=cache)
    calls = 0

    class CachedButton(Component):
        citry = app

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            nonlocal calls
            calls += 1
            return super().template_data(kwargs, slots)

        template = "<button c-title=\"tr('cached-message')\" $c-tr:cached-message[title]>Save</button>"
        messages = "cached-message = Cached"

    i18n = app.extensions.get_extension("i18n")
    provides = {
        "citry_i18n": i18n.make_context(locale="en-US"),
        CLIENT_CONTEXT_KEY: AMBIENT_CLIENT_OWNER,
    }
    first = CachedButton().render(provides=provides)
    second = CachedButton().render(provides=provides)
    first_record = next(iter(first.context.extra[EXTRA_KEY].values()))
    second_record = next(iter(second.context.extra[EXTRA_KEY].values()))
    first_binding = first_record.bindings.records[0]
    second_binding = second_record.bindings.records[0]

    assert calls == 1
    assert first_binding.id != second_binding.id
    assert first_binding.id in str(first)
    assert second_binding.id in str(second)
    assert first_binding.id not in str(second)
    assert second_binding.owner == AMBIENT_CLIENT_OWNER
