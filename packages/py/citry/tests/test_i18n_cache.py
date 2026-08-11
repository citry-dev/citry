"""Composition between ordinary Cache variation and i18n context data."""

from citry import Citry, Component, InMemoryCache


class RecordingCache(InMemoryCache):
    def __init__(self) -> None:
        super().__init__()
        self.gets = 0
        self.sets = 0

    def get(self, key: str) -> str | None:
        self.gets += 1
        return super().get(key)

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        self.sets += 1
        super().set(key, value, ttl)


def configured_app(backend: RecordingCache) -> Citry:
    return Citry(
        cache=backend,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
            }
        },
    )


def test_component_explicitly_varies_by_plain_i18n_context_identity() -> None:
    backend = RecordingCache()
    app = configured_app(backend)
    renders: list[str] = []

    class LocaleCard(Component):
        citry = app

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return self.component.i18n.context.identity

        def template_data(self, kwargs, slots):
            locale = self.i18n.context.locale
            renders.append(locale)
            return {"locale": locale}

        template = "{{ locale }}"
        messages = "unused-message = present"

    i18n = app.extensions.get_extension("i18n")
    english = {"citry_i18n": i18n.make_context(locale="en-US")}
    czech = {"citry_i18n": i18n.make_context(locale="cs-CZ")}
    assert str(LocaleCard().render(provides=english)) == "en-US"
    assert str(LocaleCard().render(provides=english)) == "en-US"
    assert str(LocaleCard().render(provides=czech)) == "cs-CZ"
    assert str(LocaleCard().render(provides=czech)) == "cs-CZ"

    assert renders == ["en-US", "cs-CZ"]
    assert backend.sets == 2


def test_omitting_i18n_context_follows_the_normal_cache_rule_and_shares() -> None:
    backend = RecordingCache()
    app = configured_app(backend)
    renders = 0

    class Brand(Component):
        citry = app

        class Cache:
            enabled = True

        class Slots:
            pass

        def template_data(self, kwargs, slots):
            nonlocal renders
            renders += 1
            return super().template_data(kwargs, slots)

        template = "Citry"
        messages = "unused-message = present"

    i18n = app.extensions.get_extension("i18n")
    english = {"citry_i18n": i18n.make_context(locale="en-US")}
    czech = {"citry_i18n": i18n.make_context(locale="cs-CZ")}
    assert str(Brand().render(provides=english)) == "Citry"
    assert str(Brand().render(provides=czech)) == "Citry"

    assert renders == 1
    assert backend.sets == 1


def test_fragment_accepts_the_same_plain_context_identity_in_vary() -> None:
    backend = RecordingCache()
    app = configured_app(backend)

    class Page(Component):
        citry = app

        class Kwargs:
            locale: str

        def template_data(self, kwargs, slots):
            return {
                "locale": kwargs.locale,
                "locale_context": self.i18n.context,
            }

        template = """\
<c-cache key="copy" c-vary="locale_context.identity">{{ locale }}</c-cache>\
"""
        messages = "unused-message = present"

    i18n = app.extensions.get_extension("i18n")
    english = {"citry_i18n": i18n.make_context(locale="en-US")}
    czech = {"citry_i18n": i18n.make_context(locale="cs-CZ")}
    assert str(Page(locale="English").render(provides=english)) == "English"
    assert str(Page(locale="English").render(provides=english)) == "English"
    assert str(Page(locale="Czech").render(provides=czech)) == "Czech"
    assert str(Page(locale="Czech").render(provides=czech)) == "Czech"

    assert backend.sets == 2


def test_cache_vary_signature_stays_extension_neutral() -> None:
    backend = RecordingCache()
    app = configured_app(backend)
    calls = 0

    class Card(Component):
        citry = app

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return self.component.i18n.context.identity

        class Slots:
            pass

        template = "card"
        messages = "unused-message = present"

    assert str(Card()) == "card"
    assert str(Card()) == "card"
    assert calls == 2
