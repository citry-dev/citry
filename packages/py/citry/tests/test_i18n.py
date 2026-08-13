"""Server foundation tests for the built-in i18n extension."""

import gc
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from weakref import ref

import pytest

from citry import (
    Citry,
    Component,
    ComponentLibrary,
    Extension,
    I18nNotConfiguredError,
    I18nRuntimeUnavailableError,
    I18nService,
    InMemoryCache,
    LibraryComponent,
    LintSettings,
)
from citry.ext.i18n import make_context


class RecordingCache(InMemoryCache):
    def __init__(self):
        super().__init__()
        self.sets = 0

    def set(self, key, value, ttl=None):
        self.sets += 1
        super().set(key, value, ttl)


def configured_app(*, template_globals=None, **overrides):
    config = {
        "source_locale": "en-US",
        "locales": ("en-US", "cs-CZ", "ar-EG"),
        "fallbacks": {"ar-EG": ("cs-CZ",)},
    }
    config.update(overrides)
    return Citry(
        extensions_defaults={"i18n": config},
        template_globals=template_globals,
    )


class TestConfiguration:
    def test_builtin_is_dormant_by_default(self):
        i18n = Citry().extensions.get_extension("i18n")
        assert i18n.configured is False
        assert (i18n.render_cache_mode, i18n.render_cache_version) == ("stateless", 1)
        with pytest.raises(I18nNotConfiguredError, match="not configured"):
            _ = i18n.context

    def test_canonicalizes_topology_and_derives_default_context(self):
        app = Citry(
            extensions_defaults={
                "i18n": {
                    "source_locale": "EN-us",
                    "locales": ("EN-us", "iw-IL"),
                    "default_locale": "iw-IL",
                }
            }
        )
        i18n = app.extensions.get_extension("i18n")
        assert i18n.config.source_locale == "en-US"
        assert i18n.config.locales == ("en-US", "he-IL")
        assert i18n.context.locale == "he-IL"
        assert i18n.context.direction == "rtl"

    @pytest.mark.parametrize(
        ("config", "message"),
        [
            ({"source_locale": "en-US"}, "requires both"),
            (
                {"source_locale": "en-US", "locales": "en-US"},
                "sequence",
            ),
            (
                {"source_locale": "en-US", "locales": ("en-US", "EN-us")},
                "duplicate canonical locale",
            ),
            (
                {
                    "source_locale": "en-US",
                    "default_locale": "cs-CZ",
                    "locales": ("en-US",),
                },
                "default_locale must be present",
            ),
            (
                {
                    "source_locale": "en-US",
                    "locales": ("en-US", "cs-CZ"),
                    "fallbacks": {"en-US": ("cs-CZ",), "cs-CZ": ("en-US",)},
                },
                "cycle",
            ),
            (
                {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                    "catalogs": "my_app_i18n",
                },
                "sequence",
            ),
            (
                {
                    "source_locale": "en-US",
                    "locales": {"en-US", "cs-CZ"},
                },
                "sequence",
            ),
            (
                {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                    "catalogs": {"my_app_i18n", "citry_ui_i18n"},
                },
                "sequence",
            ),
            (
                {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                    "catalogs": ("my_app_i18n",),
                },
                "Could not import",
            ),
        ],
    )
    def test_rejects_invalid_engine_config(self, config, message):
        with pytest.raises(ValueError, match=message):
            Citry(extensions_defaults={"i18n": config})

    def test_source_locale_may_be_fallback_only_when_default_is_allowed(self):
        app = Citry(
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "default_locale": "cs-CZ",
                    "locales": ("cs-CZ",),
                }
            }
        )

        assert app.extensions.get_extension("i18n").context.locale == "cs-CZ"

    def test_rejects_template_global_collision_when_configured(self):
        with pytest.raises(ValueError, match="reserves template global"):
            configured_app(template_globals={"tr": object()})

    def test_configured_i18n_does_not_change_the_ordinary_cache_contract(self):
        backend = RecordingCache()
        app = Citry(
            cache=backend,
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )
        i18n = app.extensions.get_extension("i18n")
        assert (i18n.render_cache_mode, i18n.render_cache_version) == ("payload", 3)

        class Greeting(Component):
            citry = app

            messages = """
                my-app-greeting = Hello
            """
            template = '{{ tr("my-app-greeting") }}'

            class Cache:
                enabled = True

        assert str(Greeting()) == "Hello"
        assert str(Greeting()) == "Hello"
        assert backend.sets == 1

    def test_make_context_is_explicit_and_does_not_change_default_context(self):
        i18n = configured_app().extensions.get_extension("i18n")

        context = i18n.make_context(locale="ar-EG", time_zone="Asia/Riyadh")

        assert context.locale == "ar-EG"
        assert context.direction == "rtl"
        assert context.time_zone == "Asia/Riyadh"
        assert i18n.context.locale == "en-US"

    def test_public_make_context_helper_uses_the_given_application(self):
        app = configured_app(default_locale="cs-CZ")

        context = make_context(
            app,
            locale="ar-EG",
            time_zone="Asia/Riyadh",
        )

        assert context.locale == "ar-EG"
        assert context.direction == "rtl"
        assert context.time_zone == "Asia/Riyadh"
        assert app.extensions.get_extension("i18n").context.locale == "cs-CZ"

    def test_public_make_context_helper_preserves_configuration_errors(self):
        with pytest.raises(I18nNotConfiguredError, match="not configured"):
            make_context(Citry(), locale="en-US")

    def test_for_context_binds_the_complete_direct_use_service(self):
        app = configured_app()

        class Greeting(Component):
            citry = app

            messages = """
                my-app-greeting = Hello
            """

        i18n = app.extensions.get_extension("i18n")
        context = i18n.make_context(locale="cs-CZ")
        service = i18n.for_context(context)

        assert isinstance(service, I18nService)
        assert service.configured
        assert service.context is context
        assert service.tr("my-app-greeting") == "Hello"
        assert service.resolve("my-app-greeting").locale == "en-US"
        assert service.format is service.format
        assert service.parse is service.parse
        with pytest.raises(TypeError, match=r"for_context\(\).+LocaleContext"):
            i18n.for_context(object())


class TestExplicitContext:
    def test_make_context_loads_sources_before_catalog_revision_snapshot(self):
        app = configured_app()

        class Greeting(Component):
            citry = app

            template = """
                {{ tr("my-app-greeting") }}
            """

            messages = """
                my-app-greeting = Hello
            """

        i18n = app.extensions.get_extension("i18n")
        initial_revision = i18n.config.catalog_revision
        context = i18n.make_context()

        assert context.catalog_revision != initial_revision
        assert str(Greeting().render(provides={"citry_i18n": context})).strip() == "Hello"
        assert i18n.context.catalog_revision == context.catalog_revision

    def test_explicit_context_rejects_a_catalog_changed_by_hot_reload(self, tmp_path):
        source = tmp_path / "greeting.ftl"
        source.write_text("my-app-greeting = One", encoding="utf8")
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
        context = i18n.make_context()

        assert i18n.tr("my-app-greeting", context=context) == "One"
        source.write_text("my-app-greeting = Two", encoding="utf8")
        Greeting.reset_files()
        with pytest.raises(I18nRuntimeUnavailableError, match="catalog inventory changed"):
            i18n.tr("my-app-greeting", context=context)

    def test_concurrent_root_provides_do_not_leak(self):
        app = configured_app()
        i18n = app.extensions.get_extension("i18n")

        class Reporter(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"locale": self.i18n.context.locale}

            template = """
                {{ locale }}
            """

        def read(locale):
            context = i18n.make_context(locale=locale)
            return str(Reporter().render(provides={"citry_i18n": context})).strip()

        app.initialize()
        with ThreadPoolExecutor(max_workers=3) as pool:
            rendered = list(pool.map(read, ("en-US", "cs-CZ", "ar-EG")))
        assert rendered == ["en-US", "cs-CZ", "ar-EG"]
        assert i18n.context.locale == "en-US"

    def test_rejects_locale_outside_the_allowed_set(self):
        i18n = configured_app().extensions.get_extension("i18n")
        with pytest.raises(ValueError, match="not allowed"):
            i18n.make_context(locale="de-DE")

    def test_rejects_empty_locale_instead_of_using_default(self):
        i18n = configured_app().extensions.get_extension("i18n")
        with pytest.raises(ValueError, match="not be empty"):
            i18n.make_context(locale="")


class TestComponentSurface:
    def test_clear_drops_catalogs_and_a_replacement_can_reuse_the_id(self):
        app = configured_app()

        class First(Component):
            citry = app
            messages = "my-app-greeting = First"
            template = '{{ tr("my-app-greeting") }}'

        i18n = app.extensions.get_extension("i18n")
        assert str(First()) == "First"
        app.clear()
        with pytest.raises(ValueError, match="Unknown i18n message ID"):
            i18n.tr("my-app-greeting")

        class Replacement(Component):
            citry = app
            messages = "my-app-greeting = Replacement"
            template = '{{ tr("my-app-greeting") }}'

        assert str(Replacement()) == "Replacement"

    def test_reregistering_a_class_reactivates_its_cached_messages(self):
        app = configured_app()

        class Greeting(Component):
            citry = app
            messages = "my-app-greeting = Hello"

        i18n = app.extensions.get_extension("i18n")
        assert i18n.tr("my-app-greeting") == "Hello"
        app.unregister(Greeting)
        with pytest.raises(ValueError, match="Unknown i18n message ID"):
            i18n.tr("my-app-greeting")
        app.register(Greeting)
        assert i18n.tr("my-app-greeting") == "Hello"

    def test_component_receives_i18n_config_and_template_facades(self):
        app = configured_app()

        class Greeting(Component):
            citry = app
            template = "{{ configured }}"

            def template_data(self, kwargs, slots):
                assert self.i18n.context.locale == "en-US"
                return {"configured": self.i18n.configured}

        assert str(Greeting()) == "True"
        assert Greeting.I18n.client_messages == ()

    def test_component_config_accepts_messages_locale_and_client_messages(self):
        app = configured_app()

        with pytest.raises(ValueError, match="unknown component I18n"):

            class Bad(Component):
                citry = app

                class I18n:
                    source_locale = "en-US"

        with pytest.raises(ValueError, match="must be a tuple"):

            class BadMessages(Component):
                citry = app

                class I18n:
                    client_messages = ["my-app-message"]

        with pytest.raises(ValueError, match="messages_locale"):

            class BadLocale(Component):
                citry = app

                class I18n:
                    messages_locale = "not_a_locale"


class TestSourceModeAndRemainingComponentSurface:
    def test_component_messages_activate_template_and_python_translation_without_settings(self):
        app = Citry(autodiscover=False)

        class SourceMessages(Component):
            citry = app

            class I18n:
                messages_locale = "EN-us"

            messages = "my-app-greeting = Hello"

        class Consumer(Component):
            citry = app
            template = '{{ python_text }} / {{ tr("my-app-greeting") }}'

            def template_data(self, kwargs, slots):
                return {"python_text": self.i18n.tr("my-app-greeting")}

        i18n = app.extensions.get_extension("i18n")
        assert i18n.configured is False
        assert i18n.available is True
        assert i18n.context.locale == "en-US"
        assert str(Consumer()) == "Hello / Hello"
        assert SourceMessages._resolved_messages == "my-app-greeting = Hello"

    def test_cross_component_source_lookup_tracks_the_complete_registered_inventory(self):
        app = Citry(autodiscover=False)

        class SourceMessages(Component):
            citry = app

            class I18n:
                messages_locale = "en-US"

            messages = "my-app-open = Open"

        class Consumer(Component):
            citry = app
            template = '{{ tr("my-app-open") }}'

        i18n = app.extensions.get_extension("i18n")
        assert str(Consumer()) == "Open"
        app.unregister(SourceMessages)
        with pytest.raises(I18nNotConfiguredError, match="no component messages"):
            i18n.tr("my-app-open")

    def test_source_mode_requires_each_message_declaration_to_name_its_locale(self):
        app = Citry(autodiscover=False)

        class MissingLocale(Component):
            citry = app
            messages = "my-app-copy = Copy"

        with pytest.raises(ValueError, match=r"I18n\.messages_locale"):
            MissingLocale.get_messages()

    def test_inherited_messages_keep_the_declaration_owners_locale(self):
        app = Citry(autodiscover=False)

        class Parent(Component):
            citry = app

            class I18n:
                messages_locale = "en-US"

            messages = "my-app-shared = Shared"

        class Child(Parent):
            class I18n:
                messages_locale = "it-IT"

            template = '{{ tr("my-app-shared") }}'

        assert str(Child()) == "Shared"
        assert app.extensions.get_extension("i18n").context.locale == "en-US"

    def test_application_source_locale_selects_the_default_over_a_library_locale(self):
        app = Citry(autodiscover=False)

        class LibraryCopy(LibraryComponent):
            class I18n:
                messages_locale = "en-US"

            messages = "demo-library-copy = Library copy"

        app.register_library(ComponentLibrary("demo-source-mode", (LibraryCopy,)))

        class ApplicationCopy(Component):
            citry = app

            class I18n:
                messages_locale = "it-IT"

            messages = "my-app-copy = Copia"

        i18n = app.extensions.get_extension("i18n")
        assert i18n.context.locale == "it-IT"
        assert i18n.tr("my-app-copy") == "Copia"
        library = i18n.resolve("demo-library-copy")
        assert (library.text, library.locale, library.used_fallback) == ("Library copy", "en-US", True)

    def test_multiple_application_source_locales_require_explicit_engine_settings(self):
        app = Citry(autodiscover=False)

        class English(Component):
            citry = app

            class I18n:
                messages_locale = "en-US"

            messages = "my-app-english = English"

        class Italian(Component):
            citry = app

            class I18n:
                messages_locale = "it-IT"

            messages = "my-app-italian = Italiano"

        with pytest.raises(ValueError, match="multiple locales"):
            app.extensions.get_extension("i18n").make_context()

    def test_multiple_library_source_locales_require_explicit_engine_settings(self):
        app = Citry(autodiscover=False)

        class EnglishLibraryCopy(LibraryComponent):
            class I18n:
                messages_locale = "en-US"

            messages = "demo-english = English"

        class ItalianLibraryCopy(LibraryComponent):
            class I18n:
                messages_locale = "it-IT"

            messages = "demo-italian = Italiano"

        app.register_library(ComponentLibrary("demo-english", (EnglishLibraryCopy,)))
        app.register_library(ComponentLibrary("demo-italian", (ItalianLibraryCopy,)))

        with pytest.raises(ValueError, match="library messages authored in multiple locales"):
            app.extensions.get_extension("i18n").make_context()

    def test_text_only_tr_and_resolve_use_the_rust_fluent_runtime(self):
        app = configured_app()

        class Greeting(Component):
            citry = app
            messages = """
                my-app-greeting = Hello
                    .aria-label = Friendly greeting
            """
            template = "<p c-aria-label=\"tr('my-app-greeting', attr='aria-label')\">{{ tr(\"my-app-greeting\") }}</p>"

        rendered = str(Greeting())
        assert 'aria-label="Friendly greeting"' in rendered
        assert rendered.endswith(">Hello</p>")
        i18n = app.extensions.get_extension("i18n")
        resolved = i18n.resolve("my-app-greeting")
        assert (resolved.text, resolved.locale, resolved.direction, resolved.used_fallback) == (
            "Hello",
            "en-US",
            "ltr",
            False,
        )

    def test_attribute_only_message_is_a_public_output(self):
        app = configured_app()

        class CloseButton(Component):
            citry = app
            messages = "my-app-close =\n    .aria-label = Close"
            template = "<button c-aria-label=\"tr('my-app-close', attr='aria-label')\"></button>"

        assert 'aria-label="Close"' in str(CloseButton())

    def test_tr_rejects_arguments_absent_from_the_source_contract(self):
        app = configured_app()

        class Greeting(Component):
            citry = app
            messages = "my-app-greeting = Hello"
            template = '{{ tr("my-app-greeting", name="Ada") }}'

        with pytest.raises(ValueError, match="expected args"):
            Greeting().render()

    def test_message_variable_without_param_type_uses_safe_scalar_runtime_contract(self):
        app = configured_app()

        class Greeting(Component):
            citry = app
            messages = "my-app-greeting = Hello, { $name }."

        assert app.extensions.get_extension("i18n").tr("my-app-greeting", name="Ada") == ("Hello, \u2068Ada\u2069.")

    def test_missing_param_type_can_be_promoted_to_an_error(self):
        app = Citry(
            lint=LintSettings(rule_i18n_missing_param_type="error"),
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Greeting(Component):
            citry = app
            messages = "my-app-greeting = Hello, { $name }."

        with pytest.raises(ValueError, match="without an @param declaration"):
            Greeting.get_messages()

    def test_component_can_ignore_missing_param_type_warning(self):
        app = configured_app()

        class Greeting(Component):
            citry = app
            messages = "my-app-greeting = Hello, { $name }."

            class Lint:
                rule_i18n_missing_param_type = "ignore"

        Greeting.get_messages()
        i18n = app.extensions.get_extension("i18n")
        i18n._load_project_sources()
        artifact = json.loads(i18n._compiled_catalog.artifact_json())
        assert artifact["diagnostics"] == []

    def test_typed_message_arguments_render_through_the_compiled_runtime(self):
        app = configured_app()

        class Greeting(Component):
            citry = app
            messages = "# @param {str} $name - User name.\nmy-app-greeting = Hello, { $name }."
            template = '{{ tr("my-app-greeting", name=name) }}'

            class Kwargs:
                name: str

        assert str(Greeting(name="<Ada>")) == "Hello, \u2068&lt;Ada&gt;\u2069."

    def test_cross_component_literal_key_uses_the_project_index(self):
        app = configured_app()

        class CommonMessages(Component):
            citry = app
            messages = "my-app-common-open = Open"

        class Button(Component):
            citry = app
            template = '{{ tr("my-app-common-open") }}'

        assert str(Button()) == "Open"

    def test_duplicate_message_ids_point_to_both_sources(self):
        app = configured_app()

        class First(Component):
            citry = app
            messages = "my-app-duplicate = First"

        class Second(Component):
            citry = app
            messages = "my-app-duplicate = Second"

        First.get_messages()
        with pytest.raises(ValueError, match="defined more than once"):
            Second.get_messages()

    def test_inherited_message_declaration_is_one_source_unit(self):
        app = configured_app()

        class Parent(Component):
            citry = app
            messages = "my-app-shared = Shared"
            template = '{{ tr("my-app-shared") }}'

        class Child(Parent):
            pass

        i18n = app.extensions.get_extension("i18n")
        context = i18n.make_context()
        provides = {"citry_i18n": context}

        assert str(Parent().render(provides=provides)) == "Shared"
        assert str(Child().render(provides=provides)) == "Shared"
        assert i18n.context.catalog_revision == context.catalog_revision

    def test_render_checks_unloaded_components_for_duplicate_ids(self):
        app = configured_app()

        class First(Component):
            citry = app
            messages = "my-app-duplicate = First"
            template = '{{ tr("my-app-duplicate") }}'

        class Second(Component):
            citry = app
            messages = "my-app-duplicate = Second"

        with pytest.raises(ValueError, match="defined more than once"):
            First().render()

    def test_registration_during_inventory_is_checked_before_resolve_returns(self):
        source_paused = Event()
        allow_source = Event()
        app = Citry(
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class First(Component):
            citry = app
            messages = "my-app-raced = First"

            @classmethod
            def get_messages(cls):
                content = super().get_messages()
                if not source_paused.is_set():
                    source_paused.set()
                    assert allow_source.wait(timeout=5)
                return content

        i18n = app.extensions.get_extension("i18n")
        with ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(i18n.tr, "my-app-raced")
            assert source_paused.wait(timeout=5)

            class Second(Component):
                citry = app
                messages = "my-app-raced = Second"

            allow_source.set()
            with pytest.raises(ValueError, match="defined more than once"):
                result.result(timeout=5)

    def test_unregistered_message_id_can_be_reused_without_an_intermediate_lookup(self):
        app = configured_app()

        class First(Component):
            citry = app
            messages = "my-app-reused = First"
            template = '{{ tr("my-app-reused") }}'

        assert str(First()) == "First"
        app.unregister(First)

        class Replacement(Component):
            citry = app
            messages = "my-app-reused = Replacement"
            template = '{{ tr("my-app-reused") }}'

        assert str(Replacement()) == "Replacement"

    def test_unregistered_catalog_owner_is_collected_without_another_i18n_call(self):
        app = configured_app()

        class Temporary(Component):
            citry = app
            messages = "my-app-temporary = Temporary"

        i18n = app.extensions.get_extension("i18n")
        assert i18n.tr("my-app-temporary") == "Temporary"
        class_reference = ref(Temporary)
        catalog_reference = ref(i18n._catalogs[Temporary])

        app.unregister(Temporary)
        del Temporary
        gc.collect()

        assert class_reference() is None
        assert catalog_reference() is None
        assert not i18n._catalogs

    def test_rejected_unregister_does_not_erase_active_catalog_ownership(self):
        class RejectUnregister(Extension):
            name = "reject_i18n_unregister"

            def on_component_unregistered(self, ctx):
                raise RuntimeError(f"keep {ctx.component_class.__name__}")

        app = Citry(
            extensions=[RejectUnregister],
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class First(Component):
            citry = app
            messages = "my-app-owned = First"

        i18n = app.extensions.get_extension("i18n")
        assert i18n.tr("my-app-owned") == "First"
        with pytest.raises(RuntimeError, match="keep First"):
            app.unregister(First)

        class Second(Component):
            citry = app
            messages = "my-app-owned = Second"

        with pytest.raises(ValueError, match="defined more than once"):
            Second.get_messages()

    def test_rejected_reregistration_does_not_leave_a_ghost_catalog(self):
        class RejectRegister(Extension):
            name = "reject_i18n_register"
            reject = False

            def on_component_registered(self, ctx):
                if self.reject and ctx.component_class.__name__ == "Ghost":
                    raise RuntimeError("reject Ghost")

        reject = RejectRegister()
        app = Citry(
            extensions=[reject],
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Ghost(Component):
            citry = app
            messages = "my-app-ghost = Ghost"

        i18n = app.extensions.get_extension("i18n")
        assert i18n.tr("my-app-ghost") == "Ghost"
        app.unregister(Ghost)
        with pytest.raises(ValueError, match="Unknown i18n message ID"):
            i18n.tr("my-app-ghost")

        reject.reject = True
        with pytest.raises(RuntimeError, match="reject Ghost"):
            app.register(Ghost)
        with pytest.raises(ValueError, match="Unknown i18n message ID"):
            i18n.tr("my-app-ghost")

    def test_non_source_locale_uses_the_defining_owner_source_fallback(self):
        app = configured_app()

        class Greeting(Component):
            citry = app
            messages = "my-app-greeting = Hello"
            template = '{{ tr("my-app-greeting") }}'

        i18n = app.extensions.get_extension("i18n")
        context = i18n.make_context(locale="cs-CZ")

        assert str(Greeting().render(provides={"citry_i18n": context})) == "Hello"
        resolved = i18n.resolve("my-app-greeting", context=context)
        assert (resolved.locale, resolved.direction, resolved.used_fallback) == ("en-US", "ltr", True)

    def test_cross_direction_fallback_isolates_each_bidi_paragraph(self):
        app = configured_app()

        class Notice(Component):
            citry = app
            messages = "my-app-notice = First\u2029Second"

        i18n = app.extensions.get_extension("i18n")
        context = i18n.make_context(locale="ar-EG")

        assert i18n.tr("my-app-notice", context=context) == "\u2066First\u2069\u2029\u2066Second\u2069"

    def test_reserved_template_data_name_fails(self):
        app = configured_app()

        class Bad(Component):
            citry = app
            template = "{{ tr }}"

            def template_data(self, kwargs, slots):
                return {"tr": "not the translator"}

        with pytest.raises(ValueError, match="reserved i18n template"):
            Bad().render()

    @pytest.mark.parametrize("name", ["tr", "fmt"])
    def test_user_extension_cannot_overwrite_reserved_template_facade(self, name):
        class Override(Extension):
            name = "override_i18n_facade"

            def on_component_data(self, ctx):
                ctx.template_data[name] = lambda *_args, **_kwargs: "OVERRIDE"

        app = Citry(
            extensions=[Override],
            extensions_defaults={
                "i18n": {
                    "source_locale": "en-US",
                    "locales": ("en-US",),
                }
            },
        )

        class Bad(Component):
            citry = app
            template = "plain"

        with pytest.raises(ValueError, match="reserved i18n template"):
            Bad().render()
