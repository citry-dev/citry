from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

from citry import Citry, Component
from citry._serialization_security import _browser_loader_descriptor
from citry.browser_render import (
    BrowserPluginDescriptor,
    BrowserRenderContribution,
    OnBrowserRenderPrepareContext,
    collect_browser_plugin_descriptors,
    prepare_browser_extensions,
)
from citry.ext.dependencies.types import Script, Style
from citry.extension import Extension


class _CustomDict(dict[str, object]):
    pass


def test_browser_loader_descriptor_preserves_external_integrity_and_rejects_nonce() -> None:
    sha384 = "sha384-" + "A" * 64
    sha512 = "sha512-" + "A" * 86 + "=="
    descriptor = _browser_loader_descriptor(
        Script(
            url="https://cdn.test/app.js",
            attrs={"integrity": f"{sha384} {sha512}", "crossorigin": "anonymous"},
        )
    )
    assert descriptor == {
        "kind": "external",
        "url": "https://cdn.test/app.js",
        "attrs": {"integrity": f"{sha384} {sha512}", "crossorigin": "anonymous"},
    }
    with pytest.raises(ValueError, match="cannot declare a revision nonce"):
        _browser_loader_descriptor(Style(url="https://cdn.test/app.css", attrs={"nonce": "changing"}))


@pytest.mark.parametrize(
    "attrs",
    [
        {"async": True},
        {"defer": True},
        {"nomodule": True},
        {"type": "module"},
        {"type": "application/json"},
    ],
)
def test_prepared_browser_scripts_require_synchronous_classic_execution(attrs: dict[str, str | bool]) -> None:
    with pytest.raises(ValueError, match=r"ordered classic|classic JavaScript MIME"):
        _browser_loader_descriptor(Script(content="register()", attrs=attrs))


def test_browser_plugin_descriptor_is_captured_once_before_contribution() -> None:
    calls = 0

    class BrowserProbeExtension(Extension):
        name = "browser_probe"

        def browser_plugin(self) -> BrowserPluginDescriptor:
            nonlocal calls
            calls += 1
            return BrowserPluginDescriptor(
                1,
                Script(content="register()"),
                template_context_names=("$probe",),
            )

        def prepare_browser_render(self, ctx: OnBrowserRenderPrepareContext) -> BrowserRenderContribution:
            return BrowserRenderContribution(1, {})

    app = Citry(extensions=[BrowserProbeExtension])
    registrations = collect_browser_plugin_descriptors(app)
    contributions = prepare_browser_extensions(
        citry=app,
        context=SimpleNamespace(extra={}, provides={}),  # type: ignore[arg-type]
        selected_render=object(),  # type: ignore[arg-type]
        view=object(),  # type: ignore[arg-type]
        render_to_occurrence={},
        app_id="app-1",
        revision=0,
        base_revision=None,
        registrations=registrations,
    )

    assert calls == 1
    registration = next(item for item in registrations if item.name == "browser_probe")
    assert contributions[0].plugin is registration.plugin
    assert contributions[0].plugin.template_context_names == ("$probe",)


def test_browser_plugin_descriptor_rejects_script_mutation_during_contribution() -> None:
    descriptor = BrowserPluginDescriptor(1, Script(content="register()", attrs={"type": "text/javascript"}))

    class BrowserProbeExtension(Extension):
        name = "browser_probe"

        def browser_plugin(self) -> BrowserPluginDescriptor:
            return descriptor

        def prepare_browser_render(self, ctx: OnBrowserRenderPrepareContext) -> BrowserRenderContribution:
            descriptor.script.attrs["type"] = "application/javascript"
            return BrowserRenderContribution(1, {})

    app = Citry(extensions=[BrowserProbeExtension])
    registrations = collect_browser_plugin_descriptors(app)
    with pytest.raises(RuntimeError, match="descriptor changed"):
        prepare_browser_extensions(
            citry=app,
            context=SimpleNamespace(extra={}, provides={}),  # type: ignore[arg-type]
            selected_render=object(),  # type: ignore[arg-type]
            view=object(),  # type: ignore[arg-type]
            render_to_occurrence={},
            app_id="app-1",
            revision=0,
            base_revision=None,
            registrations=registrations,
        )


@pytest.mark.parametrize("mutation", ["earlier_descriptor", "registry_order"])
def test_later_browser_hook_cannot_mutate_an_earlier_registration(mutation: str) -> None:
    descriptor = BrowserPluginDescriptor(1, Script(content="registerA()"))

    class A(Extension):
        name = "a"

        def browser_plugin(self):
            return descriptor

        def prepare_browser_render(self, ctx):
            return BrowserRenderContribution(1, {})

    class B(Extension):
        name = "b"

        def browser_plugin(self):
            return BrowserPluginDescriptor(1, Script(content="registerB()"))

        def prepare_browser_render(self, ctx):
            if mutation == "earlier_descriptor":
                descriptor.script.content = "changed"
            else:
                app.extensions._extensions = tuple(reversed(app.extensions._extensions))
            return BrowserRenderContribution(1, {})

    app = Citry(autodiscover=False, extensions=[A, B])
    registrations = collect_browser_plugin_descriptors(app)
    with pytest.raises(RuntimeError, match=r"descriptor changed|registry changed"):
        prepare_browser_extensions(
            citry=app,
            context=SimpleNamespace(extra={}, provides={}),  # type: ignore[arg-type]
            selected_render=object(),  # type: ignore[arg-type]
            view=object(),  # type: ignore[arg-type]
            render_to_occurrence={},
            app_id="app-1",
            revision=0,
            base_revision=None,
            registrations=registrations,
        )


def test_plugin_only_extension_gets_a_dormant_empty_wrapper() -> None:
    class PluginOnlyExtension(Extension):
        name = "plugin_only"

        def browser_plugin(self) -> BrowserPluginDescriptor:
            return BrowserPluginDescriptor(1, Script(content="register()"))

    app = Citry(extensions=[PluginOnlyExtension])
    registrations = collect_browser_plugin_descriptors(app)
    contributions = prepare_browser_extensions(
        citry=app,
        context=SimpleNamespace(extra={}, provides={}),  # type: ignore[arg-type]
        selected_render=object(),  # type: ignore[arg-type]
        view=object(),  # type: ignore[arg-type]
        render_to_occurrence={},
        app_id="app-1",
        revision=0,
        base_revision=None,
        registrations=registrations,
    )
    plugin_only = next(item for item in contributions if item.name == "plugin_only")
    assert plugin_only.payload == {}
    assert plugin_only.plugin.template_context_names == ()


def test_prepared_browser_extension_detaches_and_revalidates_contribution_assets() -> None:
    source_style = Style(content=".probe{}", attrs={"media": "screen"})

    class BrowserProbeExtension(Extension):
        name = "browser_probe"

        def browser_plugin(self) -> BrowserPluginDescriptor:
            return BrowserPluginDescriptor(1, Script(content="register()"))

        def prepare_browser_render(self, ctx: OnBrowserRenderPrepareContext) -> BrowserRenderContribution:
            return BrowserRenderContribution(1, {}, styles=(source_style,))

    app = Citry(extensions=[BrowserProbeExtension])
    contributions = prepare_browser_extensions(
        citry=app,
        context=SimpleNamespace(extra={}, provides={}),  # type: ignore[arg-type]
        selected_render=object(),  # type: ignore[arg-type]
        view=object(),  # type: ignore[arg-type]
        render_to_occurrence={},
        app_id="app-1",
        revision=0,
        base_revision=None,
    )
    prepared = contributions[0]
    assert prepared.styles[0] is not source_style
    source_style.attrs["media"] = "print"
    assert prepared.styles[0].attrs == {"media": "screen"}
    with pytest.raises(RuntimeError, match="contribution assets changed"):
        prepared.validate()


@pytest.mark.parametrize(
    "names",
    [
        ("probe",),
        ("$_probe",),
        ("$bad-name",),
        ("$slots",),
        ("$state",),
        ("$b", "$a"),
        ("$a", "$a"),
    ],
)
def test_browser_plugin_descriptor_rejects_invalid_template_context_names(names: tuple[str, ...]) -> None:
    class InvalidBrowserExtension(Extension):
        name = "invalid_browser"

        def browser_plugin(self) -> BrowserPluginDescriptor:
            return BrowserPluginDescriptor(1, Script(content="register()"), template_context_names=names)

        def prepare_browser_render(self, ctx: OnBrowserRenderPrepareContext) -> None:
            return None

    with pytest.raises((TypeError, ValueError), match="template context names"):
        collect_browser_plugin_descriptors(Citry(extensions=[InvalidBrowserExtension]))


def test_browser_plugin_descriptors_reject_context_name_claimed_by_two_extensions() -> None:
    class FirstExtension(Extension):
        name = "first"

        def browser_plugin(self) -> BrowserPluginDescriptor:
            return BrowserPluginDescriptor(1, Script(content="first()"), template_context_names=("$shared",))

        def prepare_browser_render(self, ctx: OnBrowserRenderPrepareContext) -> None:
            return None

    class SecondExtension(Extension):
        name = "second"

        def browser_plugin(self) -> BrowserPluginDescriptor:
            return BrowserPluginDescriptor(1, Script(content="second()"), template_context_names=("$shared",))

        def prepare_browser_render(self, ctx: OnBrowserRenderPrepareContext) -> None:
            return None

    with pytest.raises(ValueError, match="claimed by both"):
        collect_browser_plugin_descriptors(Citry(extensions=[FirstExtension, SecondExtension]))


def test_browser_render_extension_receives_detached_occurrence_mapping() -> None:
    observed: dict[str, str] = {}

    class BrowserProbeExtension(Extension):
        name = "browser_probe"

        def browser_plugin(self) -> BrowserPluginDescriptor:
            return BrowserPluginDescriptor(1, Script(content="register()"), allows_late_component_assets=True)

        def prepare_browser_render(
            self,
            ctx: OnBrowserRenderPrepareContext,
        ) -> BrowserRenderContribution:
            observed.update(ctx.render_to_occurrence)
            with pytest.raises(TypeError):
                ctx.render_to_occurrence["other"] = "occurrence-2"  # type: ignore[index]
            return BrowserRenderContribution(1, {"owner": ctx.render_to_occurrence["render-1"]})

    app = Citry(extensions=[BrowserProbeExtension])
    mapping = {"render-1": "occurrence-1"}
    context = SimpleNamespace(extra={}, provides={})
    contributions = prepare_browser_extensions(
        citry=app,
        context=context,  # type: ignore[arg-type]
        selected_render=object(),  # type: ignore[arg-type]
        view=object(),  # type: ignore[arg-type]
        render_to_occurrence=mapping,
        app_id="app-1",
        revision=0,
        base_revision=None,
    )

    mapping["render-1"] = "changed-after-call"
    assert observed == {"render-1": "occurrence-1"}
    assert contributions[0].payload == {"owner": "occurrence-1"}
    assert contributions[0].plugin.allows_late_component_assets is True


@pytest.mark.parametrize(
    ("invalid", "message"),
    [
        (object(), "exact JSON type"),
        ({1: "value"}, "non-string"),
        ({"nested": {"value": float("inf")}}, "non-finite"),
        (_CustomDict(value="custom"), "exact JSON type"),
    ],
)
def test_browser_render_extension_rejects_non_json_payload(invalid: object, message: str) -> None:
    class InvalidBrowserExtension(Extension):
        name = "invalid_browser"

        def browser_plugin(self) -> BrowserPluginDescriptor:
            return BrowserPluginDescriptor(1, Script(content="register()"))

        def prepare_browser_render(self, ctx: OnBrowserRenderPrepareContext) -> BrowserRenderContribution:
            return BrowserRenderContribution(1, {"invalid": invalid})

    app = Citry(extensions=[InvalidBrowserExtension])
    context = SimpleNamespace(extra={}, provides={})
    with pytest.raises(TypeError, match=message):
        prepare_browser_extensions(
            citry=app,
            context=context,  # type: ignore[arg-type]
            selected_render=object(),  # type: ignore[arg-type]
            view=object(),  # type: ignore[arg-type]
            render_to_occurrence={},
            app_id="app-1",
            revision=0,
            base_revision=None,
        )


def test_interactive_serialization_places_plugin_before_bootstrap() -> None:
    class BrowserProbeExtension(Extension):
        name = "browser_probe"

        def browser_plugin(self) -> BrowserPluginDescriptor:
            return BrowserPluginDescriptor(1, Script(content="window.probePluginLoaded = true"))

        def prepare_browser_render(
            self,
            ctx: OnBrowserRenderPrepareContext,
        ) -> BrowserRenderContribution:
            return BrowserRenderContribution(
                1,
                {"revision": ctx.revision},
                scripts=(Script(content="window.probeContributionLoaded = true"),),
                styles=(Style(content=".probe-extension { color: green; }"),),
            )

    app = Citry(extensions=[BrowserProbeExtension])

    class Page(Component):
        citry = app
        template = """
<html><body><div>ready</div></body></html>
"""
        js = """
$component({});
"""

    html = Page().render().serialize()

    assert (
        '"extensions":{"browser_probe":{"payload":{"revision":0},"schemaVersion":1,"templateContextNames":[]}}' in html
    )
    assert html.index("window.probePluginLoaded = true") < html.index("CitryStable.startPrepared")
    assert html.index(".probe-extension { color: green; }") < html.index("CitryStable.startPrepared")
    assert html.index("window.probeContributionLoaded = true") < html.index("CitryStable.startPrepared")
    assert '"owner":{"extensionName":"browser_probe","kind":"extension"}' in html
    assert 'data-citry-css-url="/assets/' in html
    assert 'data-citry-vue-style-app="' in html


@pytest.mark.parametrize("mutation", ["component", "descriptor", "registry"])
def test_interactive_serialization_revalidates_metadata_after_serialize_hooks(mutation: str) -> None:
    descriptor = BrowserPluginDescriptor(1, Script(content="window.probePluginLoaded = true"))

    class BrowserProbeExtension(Extension):
        name = "browser_probe"

        def browser_plugin(self) -> BrowserPluginDescriptor:
            return descriptor

        def prepare_browser_render(self, ctx: OnBrowserRenderPrepareContext) -> BrowserRenderContribution:
            return BrowserRenderContribution(1, {})

        def on_serialize(self, ctx):
            if mutation == "component":
                Page.__name__ = "ChangedPage"
            elif mutation == "descriptor":
                descriptor.script.content = "window.changed = true"
            else:
                self.name = "changed_registry_name"

    app = Citry(autodiscover=False, extensions=[BrowserProbeExtension])

    class Page(Component):
        citry = app
        template = "<html><body><main :data-ready='true'>ready</main></body></html>"

    original_name = Page.__name__
    extension = app.extensions.get_extension("browser_probe")
    try:
        with pytest.raises((RuntimeError, ValueError), match=r"changed during|registry metadata changed"):
            Page().render().serialize()
    finally:
        Page.__name__ = original_name
        descriptor.script.content = "window.probePluginLoaded = true"
        extension.name = "browser_probe"


def test_initial_component_styles_have_exact_app_and_manifest_url_ownership() -> None:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = "<html><head></head><body><main :data-ready='true'>ready</main></body></html>"
        css = "main { color: green; }"

    html = str(Page().render().serialize())
    app_id = re.search(r'"appId":"([0-9a-f]{32})"', html)
    style_url = re.search(r'"styles":\[\{.*?"url":"([^"]+)"', html)
    assert app_id is not None
    assert style_url is not None
    assert f'data-citry-vue-style-app="{app_id.group(1)}"' not in html
    assert f'data-citry-css-url="{style_url.group(1)}"' not in html
    assert '"loadInitialAssets":true' in html


def test_configured_dormant_i18n_plugin_has_a_minimal_payload() -> None:
    app = Citry(
        autodiscover=False,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )

    class Page(Component):
        citry = app
        template = "<html><body><p>ready</p></body></html>"
        js = "$component({});"

    html = Page().render().serialize()
    assert (
        '"i18n":{"payload":{"barriers":[],"providers":[],"requirements":[]},"schemaVersion":1,'
        '"templateContextNames":["$citryI18nBinding","$i18n"]}' in html
    )
    assert '"payload":{"parsers"' not in html
