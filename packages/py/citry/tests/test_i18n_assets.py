"""Tests for component ``messages`` and ``messages_file`` assets."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest

from citry import Citry, Component, Extension


def test_inline_messages_are_normalized_and_cached():
    app = Citry()

    class Card(Component):
        citry = app

        class I18n:
            messages_locale = "en-US"

        messages = """
            my-app-card-title = Card
        """

    assert Card.get_messages() == "\nmy-app-card-title = Card\n"
    assert Card.get_messages() is Card.get_messages()


def test_messages_file_is_lazy_watched_and_reset(tmp_path):
    path = tmp_path / "card.ftl"
    app = Citry(dirs=[tmp_path])

    class Card(Component):
        citry = app

        class I18n:
            messages_locale = "en-US"

        messages_file = "card.ftl"

    path.write_text("my-app-card-title = One", encoding="utf8")
    assert Card.get_messages() == "my-app-card-title = One"
    assert app.get_components_for_file(path) == [Card]
    path.write_text("my-app-card-title = Two", encoding="utf8")
    assert Card.get_messages() == "my-app-card-title = One"
    Card.reset_files()
    assert Card.get_messages() == "my-app-card-title = Two"


def test_invalid_reload_restores_last_valid_source_and_catalog(tmp_path):
    source = tmp_path / "greeting.ftl"
    source.write_text("greeting = One", encoding="utf8")
    app = Citry(
        dirs=[tmp_path],
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
            }
        },
    )

    class Greeting(Component):
        citry = app
        messages_file = "greeting.ftl"

    i18n = app.extensions.get_extension("i18n")
    assert i18n.tr("greeting") == "One"

    source.write_text("greeting = Broken, {", encoding="utf8")
    Greeting.reset_files()
    with pytest.raises(ValueError, match="Expected an inline expression"):
        Greeting.get_messages()

    assert Greeting.get_messages() == "greeting = One"
    assert i18n.tr("greeting") == "One"


def test_messages_pair_inherits_as_one_unit():
    app = Citry()

    class Parent(Component):
        citry = app

        class I18n:
            messages_locale = "en-US"

        messages = "parent = Parent"

    class Child(Parent):
        messages = "child = Child"

    assert Parent.get_messages() == "parent = Parent"
    assert Child.get_messages() == "child = Child"


def test_messages_and_messages_file_conflict_at_class_definition():
    app = Citry()
    with pytest.raises(ValueError, match="messages"):

        class Bad(Component):
            citry = app
            messages = "bad = Bad"
            messages_file = "bad.ftl"


def test_messages_loaded_hook_can_validate_or_replace_source():
    seen = []

    class Capture(Extension):
        name = "capture_messages"

        def on_messages_loaded(self, ctx):
            seen.append((ctx.component_class, ctx.content))
            return f"{ctx.content}\nextra = Added"

    app = Citry(extensions=[Capture])

    class Card(Component):
        citry = app

        class I18n:
            messages_locale = "en-US"

        messages = "card = Card"

    assert Card.get_messages() == "card = Card\nextra = Added"
    assert seen == [(Card, "card = Card")]


def test_configured_i18n_compiles_the_final_transformed_source():
    class Replace(Extension):
        name = "replace_messages"

        def on_messages_loaded(self, ctx):
            return ctx.content.replace("Original", "Changed")

    app = Citry(
        extensions=[Replace],
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
            }
        },
    )

    class Card(Component):
        citry = app
        template = '{{ tr("card") }}'
        messages = "card = Original"

    assert Card.get_messages() == "card = Changed"
    assert str(Card()) == "Changed"


def test_inherited_messages_are_transformed_once_per_source_unit():
    seen = []

    class Replace(Extension):
        name = "replace_messages_once"

        def on_messages_loaded(self, ctx):
            seen.append(ctx.component_class)
            return f"{ctx.content} from {ctx.component_class.__name__}"

    app = Citry(extensions=[Replace])

    class Parent(Component):
        citry = app

        class I18n:
            messages_locale = "en-US"

        messages = "card = Card"

    class Child(Parent):
        pass

    assert Child.get_messages() == "card = Card from Parent"
    assert Parent.get_messages() == "card = Card from Parent"
    assert seen == [Parent]


def test_concurrent_inherited_first_load_transforms_source_once():
    calls = []
    start = Barrier(2)

    class Capture(Extension):
        name = "capture_concurrent_messages"

        def on_messages_loaded(self, ctx):
            calls.append(ctx.component_class)

    app = Citry(extensions=[Capture])

    class Parent(Component):
        citry = app

        class I18n:
            messages_locale = "en-US"

        messages = "card = Card"

    class Child(Parent):
        pass

    def load(component):
        start.wait()
        return component.get_messages()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(load, (Parent, Child)))
    assert results == ["card = Card", "card = Card"]
    assert calls == [Parent]


def test_parent_reset_makes_owner_cache_authoritative_for_child(tmp_path):
    source = tmp_path / "shared.ftl"
    source.write_text("card = One", encoding="utf8")
    app = Citry(dirs=[tmp_path])

    class Parent(Component):
        citry = app

        class I18n:
            messages_locale = "en-US"

        messages_file = "shared.ftl"

    class Child(Parent):
        pass

    assert Parent.get_messages() == "card = One"
    assert Child.get_messages() == "card = One"
    source.write_text("card = Two", encoding="utf8")
    Parent.reset_files()
    assert Parent.get_messages() == "card = Two"
    assert Child.get_messages() == "card = Two"


def test_reset_and_concurrent_reload_publish_one_complete_source_state(tmp_path):
    reset_paused = Event()
    allow_reset = Event()
    reload_started = Event()

    class PauseReset(Extension):
        name = "pause_messages_reset"

        def on_files_reset(self, _ctx):
            reset_paused.set()
            assert allow_reset.wait(timeout=5)

    source = tmp_path / "greeting.ftl"
    source.write_text("greeting = One", encoding="utf8")
    app = Citry(
        dirs=[tmp_path],
        extensions=[PauseReset],
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
            }
        },
    )

    class Greeting(Component):
        citry = app
        messages_file = "greeting.ftl"

    i18n = app.extensions.get_extension("i18n")
    assert i18n.tr("greeting") == "One"
    source.write_text("greeting = Two", encoding="utf8")

    def reload():
        reload_started.set()
        return Greeting.get_messages()

    with ThreadPoolExecutor(max_workers=2) as pool:
        reset_future = pool.submit(Greeting.reset_files)
        assert reset_paused.wait(timeout=5)
        reload_future = pool.submit(reload)
        assert reload_started.wait(timeout=5)
        assert not reload_future.done()
        allow_reset.set()
        reset_future.result(timeout=5)
        assert reload_future.result(timeout=5) == "greeting = Two"

    assert i18n.tr("greeting") == "Two"


def test_messages_are_part_of_component_introspection():
    app = Citry()

    class Card(Component):
        citry = app
        messages = "card = Card"

    info = app.inspect_component(Card)
    assert info.assets.messages.kind == "inline"
    assert info.assets.messages.declared_on is not None
    assert info.assets.messages.declared_on.endswith(".Card")
