"""Server behavior for the built-in ``<c-i18n>`` and ``<c-trans>`` tags."""

import json
import re
from typing import Any

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


def prepared_i18n_payload(component: Component) -> tuple[dict[str, Any], dict[str, Any]]:
    serialized = component.render().serialize()
    payload = serialized.split("CitryStable.startPrepared(", 1)[1].split(").catch", 1)[0]
    manifest = json.loads(payload)["manifest"]
    extension = manifest["extensions"]["i18n"]
    assert extension["schemaVersion"] == 1
    return manifest, extension["payload"]


def assert_provider_occurrence_identity(manifest: dict[str, Any], provider: dict[str, Any]) -> None:
    occurrences = {item["id"]: item for item in manifest["occurrences"]}
    assert provider["id"] in occurrences
    host = next(item for item in manifest["occurrences"] if item["renderId"] == provider["serverProviderId"])
    assert host["parentId"] == provider["id"]


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


def test_i18n_client_mode_requires_a_real_wrapper() -> None:
    app = configured_app()

    class Page(Component):
        citry = app
        template = '<c-i18n c-client="True">text</c-i18n>'

    with pytest.raises(ValueError, match="client provider requires a real 'tag' wrapper"):
        Page().render()


def test_i18n_client_mode_uses_the_native_prepared_provider_contract() -> None:
    app = configured_app()

    class Page(Component):
        citry = app
        template = '<c-i18n c-client="True" tag="section">text</c-i18n>'

    manifest, payload = prepared_i18n_payload(Page())
    providers = payload["providers"]
    assert len(providers) == 1
    provider = providers[0]
    assert provider["parent"] is None
    assert provider["context"]["locale"] == "en-US"
    assert provider["context"]["direction"] == "ltr"
    assert_provider_occurrence_identity(manifest, provider)
    assert payload["barriers"] == []
    assert payload["requirements"] == []


def test_nested_server_provider_is_an_explicit_client_barrier() -> None:
    app = configured_app()

    class Page(Component):
        citry = app
        template = """
            <c-i18n c-client="True" tag="main">
                <c-i18n tag="section">server-only subtree</c-i18n>
            </c-i18n>
        """

    manifest, payload = prepared_i18n_payload(Page())
    providers = payload["providers"]
    assert len(providers) == 1
    provider = providers[0]
    assert provider["parent"] is None
    assert_provider_occurrence_identity(manifest, provider)

    barriers = payload["barriers"]
    assert len(barriers) == 1
    barrier = barriers[0]
    occurrences = {item["id"]: item for item in manifest["occurrences"]}
    provider_host = next(item for item in manifest["occurrences"] if item["renderId"] == provider["serverProviderId"])
    assert occurrences[barrier]["parentId"] == provider_host["id"]
    assert barrier not in {item["id"] for item in providers}
    assert payload["requirements"] == []


def test_nested_server_provider_barrier_requires_a_real_wrapper() -> None:
    app = configured_app()

    class Page(Component):
        citry = app
        template = """
            <c-i18n c-client="True" tag="main">
                <c-i18n>server-only subtree</c-i18n>
            </c-i18n>
        """

    with pytest.raises(ValueError, match="client barrier requires a real 'tag' wrapper"):
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
