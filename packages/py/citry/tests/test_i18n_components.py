"""Server behavior for the built-in ``<c-i18n>`` and ``<c-trans>`` tags."""

import re

import pytest

from citry import Citry, Component
from citry.ext.i18n import I18n, I18nRuntimeUnavailableError


def configured_app() -> Citry:
    return Citry(
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ", "ar-EG"),
            }
        }
    )


def without_component_ids(rendered: str) -> str:
    return re.sub(r' data-cid-[^=]+=""', "", rendered)


def test_i18n_provider_changes_the_context_for_its_subtree() -> None:
    app = configured_app()

    class LocaleReporter(Component):
        citry = app
        template = "{{ locale }}:{{ direction }}"

        def template_data(self, kwargs, slots):
            i18n: I18n = self.i18n
            return {
                "locale": i18n.context.locale,
                "direction": i18n.context.direction,
            }

    class Page(Component):
        citry = app
        template = '<c-i18n locale="ar-EG" tag="section"><c-locale-reporter /></c-i18n>'

    assert without_component_ids(str(Page())) == '<section lang="ar-EG" dir="rtl">ar-EG:rtl</section>'


def test_i18n_provider_accepts_an_explicit_root_context() -> None:
    app = configured_app()

    class LocaleReporter(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return {"locale": self.i18n.context.locale}

        template = "{{ locale }}"

    class Page(Component):
        citry = app
        template = """\
<c-i18n tag="main"><c-locale-reporter /></c-i18n>\
"""

    context = app.extensions.get_extension("i18n").make_context(locale="cs-CZ")

    rendered = Page().render(provides={"citry_i18n": context})
    assert without_component_ids(str(rendered)) == '<main lang="cs-CZ" dir="ltr">cs-CZ</main>'


def test_nested_standalone_render_needs_its_own_explicit_context() -> None:
    app = configured_app()

    class LocaleReporter(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return {"locale": self.i18n.context.locale}

        template = """
            {{ locale }}
        """

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            context = self.i18n.context
            return {
                "page_locale": context.locale,
                "standalone_locale": str(LocaleReporter()).strip(),
                "explicit_locale": str(
                    LocaleReporter().render(
                        provides={"citry_i18n": context},
                    )
                ).strip(),
            }

        template = """
            {{ page_locale }}|{{ standalone_locale }}|{{ explicit_locale }}
        """

    context = app.extensions.get_extension("i18n").make_context(locale="cs-CZ")

    assert str(Page().render(provides={"citry_i18n": context})).strip() == "cs-CZ|en-US|cs-CZ"


def test_root_i18n_provide_rejects_the_wrong_value_type() -> None:
    app = configured_app()

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return {"locale": self.i18n.context.locale}

        template = """
            {{ locale }}
        """

    with pytest.raises(TypeError, match="must be an exact LocaleContext"):
        Page().render(provides={"citry_i18n": "cs-CZ"})


def test_i18n_provider_is_transparent_when_tag_is_omitted() -> None:
    app = configured_app()

    class LocaleReporter(Component):
        citry = app
        template = "{{ i18n_locale }}"

        def template_data(self, kwargs, slots):
            i18n: I18n = self.i18n
            return {"i18n_locale": i18n.context.locale}

    class Page(Component):
        citry = app
        template = '<p>before</p><c-i18n locale="cs-CZ"><c-locale-reporter /></c-i18n><p>after</p>'

    assert without_component_ids(str(Page())) == "<p>before</p>cs-CZ<p>after</p>"


def test_i18n_client_mode_fails_plainly_until_browser_switching_exists() -> None:
    app = configured_app()

    class Page(Component):
        citry = app
        template = '<c-i18n c-client="True">text</c-i18n>'

    with pytest.raises(ValueError, match="browser locale-switching stage"):
        Page().render()


def test_trans_repeats_one_application_fill_without_exposing_markers() -> None:
    app = configured_app()

    class Page(Component):
        citry = app
        messages = "# @param {Slot} $terms_link\nterms = Read { $terms_link }, then { $terms_link } again."
        template = """
            <c-trans message="terms" c-values="{}">
                <c-fill name="terms_link"><a href="/terms">terms</a></c-fill>
            </c-trans>
        """

    rendered = without_component_ids(str(Page())).strip()
    assert rendered == (
        'Read <bdi dir="auto"><a href="/terms">terms</a></bdi>, then '
        '<bdi dir="auto"><a href="/terms">terms</a></bdi> again.'
    )
    assert "CITRY" not in rendered


def test_trans_keeps_catalog_text_escaped_and_fill_markup_structural() -> None:
    app = configured_app()

    class Page(Component):
        citry = app
        messages = "# @param {Slot} $link\nsafe = <unsafe> { $link } & text"
        template = """
            <c-trans message="safe" c-values="{}">
                <c-fill name="link"><strong>owned</strong></c-fill>
            </c-trans>
        """

    rendered = without_component_ids(str(Page())).strip()
    assert rendered == '&lt;unsafe&gt; <bdi dir="auto"><strong>owned</strong></bdi> &amp; text'


def test_trans_rejects_a_missing_fill() -> None:
    app = configured_app()

    class Page(Component):
        citry = app
        messages = "# @param {Slot} $link\nterms = Read { $link }."
        template = '<c-trans message="terms" c-values="{}" />'

    with pytest.raises(ValueError, match="expected Slots"):
        Page().render()


def test_trans_rejects_a_cross_language_fallback_without_a_language_host() -> None:
    app = configured_app()

    class Page(Component):
        citry = app
        messages = "# @param {Slot} $link\nterms = Read { $link }."
        template = """
            <c-i18n locale="cs-CZ">
                <c-trans message="terms" c-values="{}">
                    <c-fill name="link"><a href="/terms">terms</a></c-fill>
                </c-trans>
            </c-i18n>
        """

    with pytest.raises(I18nRuntimeUnavailableError, match="cannot mark that fallback language"):
        Page().render()
