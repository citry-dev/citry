"""Server delivery contract for opt-in browser i18n."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component, InMemoryCache
from citry._vue.capture import render_prepared_direct
from citry._vue.events import default_events_producer
from citry.ext.i18n.usage import CLIENT_CONTEXT_KEY, EXTRA_KEY
from citry.util.routing import RouteHeaders, RouteRequest, match_route

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry_element import CitryElement
    from citry.citry_render import CitryRender


def _app() -> Citry:
    return Citry(
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
            }
        }
    )


def _prepared_manifest(
    component: CitryElement,
    *,
    provides: Mapping[str, object] | None = None,
) -> tuple[CitryRender, dict[str, object]]:
    """Prepare a manifest from the same producer used by Vue serialization."""
    app = component.comp_cls.citry
    rendered = render_prepared_direct(component, provides=provides)
    manifest = default_events_producer(app).prepare_from_render(
        rendered,
        citry=app,
        app_id="i18n-unit",
        revision=0,
    )

    return rendered, manifest


def _prepared_i18n(
    component: CitryElement,
    *,
    provides: Mapping[str, object] | None = None,
) -> tuple[CitryRender, dict[str, object]]:
    """Read the extension payload from the same prepared producer used by Vue."""
    rendered, manifest = _prepared_manifest(component, provides=provides)
    extensions = manifest["extensions"]
    assert type(extensions) is dict
    extension = extensions["i18n"]
    assert type(extension) is dict
    assert extension["schemaVersion"] == 1
    payload = extension["payload"]
    assert type(payload) is dict
    return rendered, payload


def test_plain_server_translation_does_not_ship_the_browser_runtime() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = '<h1>{{ tr("title") }}</h1>'
        messages = "title = Server title"

    html = Page().render().serialize()

    assert ">Server title</h1>" in html
    assert "data-citry-i18n" not in html
    assert "Citry's opt-in browser i18n runtime" not in html


def test_javascript_delivery_policy_sees_client_i18n_and_can_omit_it() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = (
            '<c-i18n c-client="True" tag="main"><output v-text="$i18n.tr(\'title\')">Static fallback</output></c-i18n>'
        )
        messages = "title = Client title"

    rendered = Page().render()
    with pytest.raises(ValueError, match="browser activation attribute 'v-text' requires JavaScript"):
        rendered.serialize(deps_strategy="ignore", security_javascript="forbid")

    with pytest.warns(RuntimeWarning, match="static fallback"):
        omitted = rendered.serialize(security_javascript="omit")
    assert "data-citry-i18n" not in omitted
    assert "opt-in browser i18n runtime" not in omitted
    assert "v-text" in omitted
    assert ">Static fallback</output>" in omitted


def test_client_provider_emits_only_literal_client_roots() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """
            <c-i18n c-client="True" tag="main">
                <h1>{{ tr("server-only") }}</h1>
                <output v-text="$i18n.tr('client-title')"></output>
            </c-i18n>
        """
        messages = """
            server-only = Server only
            client-title = Client title
        """

    _rendered, manifest = _prepared_i18n(Page())
    assert set(manifest["parsers"]) == {"en-US", "cs-CZ"}
    assert manifest["parsers"]["en-US"]["schema_version"] == 1
    assert manifest["parsers"]["en-US"]["number"] == {}
    assert manifest["parsers"]["en-US"]["percent"] == {}
    requirements = manifest["requirements"]
    assert isinstance(requirements, list)
    assert len(requirements) == 1
    requirement = requirements[0]
    assert requirement["outputs"] == []
    assert requirement["messages"] == ["client-title"]
    assert set(requirement["artifacts"]) == {"en-US", "cs-CZ"}
    assert "server-only" not in requirement["artifacts"]["en-US"]["messages"]


def test_large_catalog_browser_payload_contains_only_the_requested_roots() -> None:
    """A large server catalog must not turn into a large browser payload."""
    app = _app()
    all_messages = "\n".join(f"catalog-message-{index:04d} = Catalog message {index:04d}" for index in range(2_000))

    class Page(Component):
        citry = app
        template = """
            <c-i18n c-client="True" tag="main">
                <output v-text="$i18n.tr('catalog-message-0000')"></output>
                <output v-text="$i18n.tr('catalog-message-0999')"></output>
                <output v-text="$i18n.tr('catalog-message-1999')"></output>
            </c-i18n>
        """
        messages = all_messages

    _rendered, manifest = _prepared_i18n(Page())
    requirement = manifest["requirements"][0]
    assert requirement["messages"] == [
        "catalog-message-0000",
        "catalog-message-0999",
        "catalog-message-1999",
    ]
    for artifact in requirement["artifacts"].values():
        assert set(artifact["messages"]) == {
            "catalog-message-0000",
            "catalog-message-0999",
            "catalog-message-1999",
        }
        assert "Catalog message 0001" not in json.dumps(artifact)

    # Both selectable locales, the complete small profile registry, parser
    # records, and the three exact message roots stay comfortably bounded.
    payload = json.dumps(manifest, ensure_ascii=False, separators=(",", ":")).encode()
    assert len(gzip.compress(payload, mtime=0)) <= 3_500


def test_one_hundred_message_partition_stays_within_the_release_budget() -> None:
    app = _app()
    source_messages = "\n".join(f"payload-message-{index:03d} = Message {index:03d}" for index in range(100))

    class Catalog(Component):
        citry = app
        template = "Catalog"
        messages = source_messages

    Catalog().render()
    i18n = app.extensions.get_extension("i18n")
    artifact = i18n.browser_artifact(
        locale="en-US",
        outputs=tuple(f"payload-message-{index:03d}" for index in range(100)),
        messages=(),
    )
    payload = json.dumps(artifact, ensure_ascii=False, separators=(",", ":")).encode()

    assert len(gzip.compress(payload, mtime=0)) <= 15 * 1024
    runtime = Path(__file__).parents[1] / "citry/ext/i18n/client/vue-plugin.source.js"
    combined = runtime.read_bytes() + b"\n" + payload
    assert len(gzip.compress(combined, mtime=0)) <= 35 * 1024


def test_mounted_i18n_runtime_integrity_matches_route_body() -> None:
    app = Citry(
        security_script_integrity="citry",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
            }
        },
    )
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = """
            <c-i18n c-client="True" tag="main">
                <output v-text="$i18n.tr('client-title')"></output>
            </c-i18n>
        """
        messages = "client-title = Client title"

    result = Page().render().serialize_result()
    url = "/citry/ext/i18n/runtime.js"
    matched = match_route(app.urls, "ext/i18n/runtime.js")
    assert matched is not None
    response = matched.route.handler(None, **matched.params)
    digest = f"sha384-{base64.b64encode(hashlib.sha384(response.body).digest()).decode('ascii')}"

    record = next(script for script in result.security.scripts if script.url == url)
    assert record.digests == (digest,)
    assert f'src="{url}" integrity="{digest}"' in result.html


def test_literal_client_root_includes_all_message_attributes() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """
            <c-i18n c-client="True" tag="main">
                <output v-text="$i18n.tr('client-title', {}, { attr: 'aria-label' })"></output>
            </c-i18n>
        """
        messages = """
            client-title = Client title
                .aria-label = Accessible client title
        """

    _rendered, manifest = _prepared_i18n(Page())
    requirement = manifest["requirements"][0]
    messages = requirement["artifacts"]["en-US"]["messages"]

    assert set(messages) == {"client-title", "client-title.aria-label"}


def test_unknown_literal_client_root_fails_before_html_is_emitted() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """
            <c-i18n c-client="True" tag="main">
                <output v-text="$i18n.tr('missing-title')"></output>
            </c-i18n>
        """

    with pytest.raises(ValueError, match="missing-title"):
        Page().render().serialize()


def test_mounted_document_inlines_only_the_current_locale_partition() -> None:
    app = _app()
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = """
            <c-i18n c-client="True" tag="main">
                <output v-text="$i18n.tr('client-title')"></output>
            </c-i18n>
        """
        messages = "client-title = Client title"

    html = Page().render().serialize()
    _rendered, manifest = _prepared_i18n(Page())
    requirement = manifest["requirements"][0]

    assert set(requirement["artifacts"]) == {"en-US"}
    assert manifest["messages_url"] == "/citry/ext/i18n/messages"
    assert '<script src="/citry/ext/i18n/runtime.js"></script>' in html


def test_fragment_attaches_literal_client_roots_to_its_external_provider() -> None:
    app = _app()
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = '<c-i18n c-client="True" tag="main"></c-i18n>'

    class Fragment(Component):
        citry = app
        template = "<output v-text=\"$i18n.tr('fragment-title')\"></output>"
        messages = "fragment-title = Fragment title"

    rendered_page = Page().render()
    provider_records = [
        record for record in rendered_page.context.extra[EXTRA_KEY].values() if record.provider is not None
    ]
    assert len(provider_records) == 1
    provider_record = provider_records[0]

    _fragment, prepared = _prepared_manifest(
        Fragment(),
        provides={
            "citry_i18n": provider_record.provider.context,
            CLIENT_CONTEXT_KEY: provider_record.render_id,
        },
    )
    extension = prepared["extensions"]["i18n"]
    manifest = extension["payload"]

    assert manifest["providers"] == []
    assert manifest["requirements"][0]["provider"] == {"serverProviderId": provider_record.render_id}
    assert manifest["requirements"][0]["owner"] == prepared["rootId"]
    assert manifest["requirements"][0]["messages"] == ["fragment-title"]


def test_browser_requirements_remain_partitioned_by_logical_render_owner() -> None:
    app = _app()

    class First(Component):
        citry = app
        template = "<output v-text=\"$i18n.tr('first-title')\"></output>"
        messages = "first-title = First"

    class Second(Component):
        citry = app
        template = "<output v-text=\"$i18n.tr('second-title')\"></output>"
        messages = "second-title = Second"

    class Page(Component):
        citry = app
        template = '<c-i18n c-client="True" tag="main"><c-First /><c-Second /></c-i18n>'

    _rendered, manifest = _prepared_i18n(Page())
    requirements = manifest["requirements"]

    assert len(requirements) == 2
    assert len({requirement["owner"] for requirement in requirements}) == 2
    assert {tuple(requirement["messages"]) for requirement in requirements} == {
        ("first-title",),
        ("second-title",),
    }
    assert len({requirement["provider"] for requirement in requirements}) == 1


def test_fragment_server_only_barrier_does_not_leak_client_roots_to_external_provider() -> None:
    app = _app()
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = '<c-i18n c-client="True" tag="main"></c-i18n>'

    class ClientCopy(Component):
        citry = app
        template = "<output v-text=\"$i18n.tr('blocked-title')\"></output>"
        messages = "blocked-title = Blocked title"

    class Fragment(Component):
        citry = app
        template = '<c-i18n tag="section"><c-client-copy /></c-i18n>'

    rendered_page = Page().render()
    provider_record = next(
        record for record in rendered_page.context.extra[EXTRA_KEY].values() if record.provider is not None
    )
    _fragment, manifest = _prepared_i18n(
        Fragment(),
        provides={
            "citry_i18n": provider_record.provider.context,
            CLIENT_CONTEXT_KEY: provider_record.render_id,
        },
    )

    assert manifest["barriers"]
    assert all("blocked-title" not in json.dumps(requirement) for requirement in manifest["requirements"])


def test_cached_fragment_rebuilds_prepared_provider_barrier_ancestry() -> None:
    app = Citry(
        cache=InMemoryCache(),
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US", "cs-CZ")}},
    )
    renders = 0

    class Page(Component):
        citry = app
        template = '<c-i18n c-client="True" tag="main"></c-i18n>'

    class ClientCopy(Component):
        citry = app
        template = "<output v-text=\"$i18n.tr('blocked-title')\"></output>"
        messages = "blocked-title = Blocked title"

    class Fragment(Component):
        citry = app
        template = '<c-i18n tag="section"><c-client-copy /></c-i18n>'

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            nonlocal renders
            renders += 1
            return {}

    rendered_page = Page().render()
    provider_record = next(
        record for record in rendered_page.context.extra[EXTRA_KEY].values() if record.provider is not None
    )
    provides = {
        "citry_i18n": provider_record.provider.context,
        CLIENT_CONTEXT_KEY: provider_record.render_id,
    }

    manifests = [_prepared_i18n(Fragment(), provides=provides)[1] for _ in range(2)]

    assert renders == 1
    assert all(manifest["barriers"] for manifest in manifests)
    assert all(
        "blocked-title" not in json.dumps(requirement)
        for manifest in manifests
        for requirement in manifest["requirements"]
    )


def test_message_route_returns_an_exact_partition_and_rejects_stale_requests() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = "Page"
        messages = "client-title = Client title"

    Page().render()
    i18n = app.extensions.get_extension("i18n")
    matched = match_route(app.urls, "ext/i18n/messages")
    assert matched is not None

    def request(revision: str) -> RouteRequest:
        body = json.dumps(
            {
                "catalog_revision": revision,
                "locale": "en-US",
                "messages": [],
                "outputs": ["client-title"],
                "schema_version": 1,
            }
        ).encode()
        return RouteRequest(
            method="POST",
            body=body,
            content_type="application/json",
            headers=RouteHeaders((("Content-Type", "application/json"),)),
        )

    response = matched.route.handler(request(i18n.catalog_revision))
    assert response.status == 200
    artifact = json.loads(response.content)
    assert list(artifact["messages"]) == ["client-title"]
    assert artifact["requested_locale"] == "en-US"

    stale = matched.route.handler(request("stale"))
    assert stale.status == 400
    assert json.loads(stale.content)["error"]["code"] == "I18N_BROWSER_REQUEST_INVALID"
