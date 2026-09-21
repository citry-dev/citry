"""Browser coverage for rendered HTML delivered through PreviewBridge."""

from __future__ import annotations

import json
import time
from base64 import b64encode
from typing import Any
from urllib.parse import urlsplit

import pytest

pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _client_active_tabs_page() -> tuple[str, list[dict[str, str]]]:
    app = Citry(
        autodiscover=False,
        secret="preview-bridge-regression-secret",  # noqa: S106 - test key
    )
    app.register_library(citry_ui)
    # The probe declares Events, and Vue serialization needs to know where their
    # routes live before it can build the app's call URLs.
    app.set_mounted_prefix("/__citry_playground__")

    class EventProbe(Component):
        citry = app

        class State:
            count: int = 7

        class Events:
            def ping(self) -> None:
                return None

        template = """
          <section id="event-probe">
            <output id="initial-state" v-text="$state.count"></output>
            <button type="button" @c-click="ping">Ping</button>
          </section>
        """

        js = """
          $component({
            onServerRender: ({component}) => {
              window.__initialState = component.$state.count;
            },
          })
        """

    class Demo(Component):
        citry = app
        js = """
          $component({
            data() {
              return {state: Citry.vue.reactive({selected: "account", changes: 0})};
            },
          })
        """

        template = """
          <main>
            <c-CTabs
              id="outer-tabs"
              default_value="account"
              aria_label="Outer sections"
              :value="state.selected"
              :onValueChange="(value, detail) => {
                state.selected = value;
                state.changes += 1;
                window.__outerChange = { value, source: detail.source, changes: state.changes };
              }"
            >
              <c-CTab value="account">Account</c-CTab>
              <c-CTab value="profile" disabled>Profile</c-CTab>
              <c-CTab value="security">Security</c-CTab>
              <c-CTabPanel value="account">
                <c-CTabs
                  id="inner-tabs"
                  default_value="inner-one"
                  aria_label="Inner sections"
                >
                  <c-CTab value="inner-one">Inner one</c-CTab>
                  <c-CTab value="inner-two">Inner two</c-CTab>
                  <c-CTabPanel value="inner-one">Inner panel one</c-CTabPanel>
                  <c-CTabPanel value="inner-two">Inner panel two</c-CTabPanel>
                </c-CTabs>
              </c-CTabPanel>
              <c-CTabPanel value="profile">Profile panel</c-CTabPanel>
              <c-CTabPanel value="security">Security panel</c-CTabPanel>
            </c-CTabs>
            <output id="selected-value" v-text="state.selected">account</output>
            <c-EventProbe />
          </main>
        """

    html = f"<!doctype html><html lang='en'><head></head><body>{Demo()}</body></html>"

    # PreviewBridge serves playground-owned assets through its callback rather
    # than exposing the application's Citry mount directly. Keep this fixture
    # on the same channel so the test exercises the real prepared Vue startup.
    from citry._vue.events import definition_bundle, style_asset
    from citry.ext.dependencies.emission import _runtime_js
    from docs_site._internal.static_deps import _prepared_owned_assets

    assets = [
        {
            "path": "/__citry_playground__/citry.js",
            "contentType": "text/javascript",
            "content": _runtime_js(),
        }
    ]
    for kind, digest in sorted(_prepared_owned_assets(html, app)):
        content = definition_bundle(app, digest) if kind == "js" else style_asset(app, digest)
        assert content is not None
        directory = "definitions" if kind == "js" else "assets"
        assets.append(
            {
                "path": f"/__citry_playground__/ext/events/{directory}/{digest}.{kind}",
                "contentType": "text/javascript" if kind == "js" else "text/css",
                "content": content.decode("utf-8"),
            }
        )
    return html, assets


def _render_through_preview_bridge(
    page: Any,
    base_url: str,
    html: str,
    *,
    assets: list[dict[str, str]] | None = None,
) -> None:
    if assets:
        by_path = {asset["path"]: asset for asset in assets}

        def fulfill_playground_asset(route: Any) -> None:
            path = urlsplit(route.request.url).path
            asset = by_path.get(path)
            if asset is None:
                route.continue_()
                return
            route.fulfill(
                status=200,
                content_type=asset["contentType"],
                headers={"Access-Control-Allow-Origin": "*"},
                body=asset["content"],
            )

        page.route("**/__citry_playground__/**", fulfill_playground_asset)
    page.goto(base_url + "/", wait_until="domcontentloaded")
    page.evaluate(
        """async ({ baseUrl, html, assets }) => {
          const { PreviewBridge } = await import(
            `${baseUrl}/docs_site/_internal/frontend/src/preview_bridge.js`
          );
          const iframe = document.createElement('iframe');
          iframe.id = 'preview';
          iframe.title = 'Rendered Citry result';
          iframe.src = `${baseUrl}/docs_site/static/playground/preview.html`;
          iframe.setAttribute('sandbox', 'allow-forms allow-scripts');
          document.body.append(iframe);
          window.__previewDiagnostics = [];
          window.__previewCommitted = false;
          window.__previewAssets = assets || [];
          window.__previewBridge = new PreviewBridge({
            iframe,
            onAssets: async paths => paths.map(path => {
              const asset = window.__previewAssets.find(candidate => candidate.path === path);
              if (!asset) throw new Error(`Missing test asset: ${path}`);
              return asset;
            }),
            onCommit: () => { window.__previewCommitted = true; },
            onDiagnostic: (kind, message) => {
              window.__previewDiagnostics.push({ kind, message });
            },
            onEvent: async () => ({}),
            onNavigation: () => {},
          });
          await window.__previewBridge.render(html, 1);
        }""",
        {"baseUrl": base_url, "html": html, "assets": assets},
    )


def _prepared_manifest(html: str) -> dict[str, Any]:
    marker = "CitryStable.startPrepared("
    start = html.index(marker) + len(marker)
    configuration, consumed = json.JSONDecoder().raw_decode(html[start:])
    assert html[start + consumed :].startswith(").catch")
    manifest = configuration["manifest"]
    assert manifest["protocol"] == "citry-vue-prepared/1"
    return manifest


def _inline_prepared_assets(html: str, assets: list[dict[str, str]]) -> str:
    """Inline prepared Vue assets so the sandbox does not resolve paths at ``blob:null``."""
    marker = "CitryStable.startPrepared("
    start = html.index(marker) + len(marker)
    configuration, consumed = json.JSONDecoder().raw_decode(html[start:])
    by_path = {asset["path"]: asset for asset in assets}

    def data_url(source: dict[str, Any]) -> str:
        path = source["url"]
        asset = by_path[path]
        encoded = b64encode(asset["content"].encode()).decode()
        return f"data:{asset['contentType']};base64,{encoded}"

    manifest = configuration["manifest"]
    for definition in manifest["definitions"]:
        definition["url"] = data_url(definition)
    for asset in [*manifest["scripts"], *manifest["styles"]]:
        asset["source"]["url"] = data_url(asset["source"])
    return html[:start] + json.dumps(configuration) + html[start + consumed :]


def test_preview_bridge_mounts_vue_before_committing_the_candidate(
    page: Any,
    workspace_static_url: str,
) -> None:
    html, assets = _client_active_tabs_page()
    html = _inline_prepared_assets(html, assets)
    expected_occurrences = len(_prepared_manifest(html)["occurrences"])
    _render_through_preview_bridge(page, workspace_static_url, html, assets=assets)
    preview = page.frame_locator("#preview")
    roots = preview.locator("[data-citry-tabs-root][data-citry-tabs-initialized]")
    expect(roots).to_have_count(2)
    expect(preview.locator("#initial-state")).to_have_text("7")
    initial_state = preview.locator("body").evaluate("body => body.ownerDocument.defaultView.__initialState")
    assert initial_state == 7

    inner_one = preview.get_by_role("tab", name="Inner one", exact=True)
    inner_one.focus()
    inner_one.press("ArrowRight")
    expect(preview.locator("#inner-tabs")).to_have_attribute("data-value", "inner-two")
    expect(preview.locator("#outer-tabs")).to_have_attribute("data-value", "account")

    preview.get_by_role("tab", name="Security", exact=True).click()
    expect(preview.locator("#outer-tabs")).to_have_attribute("data-value", "security")
    expect(preview.locator("#selected-value")).to_have_text("security")
    callback = preview.locator("body").evaluate("body => body.ownerDocument.defaultView.__outerChange")
    assert callback == {"value": "security", "source": "pointer", "changes": 1}

    account = preview.get_by_role("tab", name="Account", exact=True)
    account.click()
    account.focus()
    account.press("ArrowRight")
    expect(preview.get_by_role("tab", name="Security", exact=True)).to_be_focused()
    expect(preview.locator("#outer-tabs")).to_have_attribute("data-value", "security")
    keyboard_callback = preview.locator("body").evaluate("body => body.ownerDocument.defaultView.__outerChange")
    assert keyboard_callback == {"value": "security", "source": "keyboard", "changes": 3}

    runtime = preview.locator("body").evaluate(
        """body => {
          const doc = body.ownerDocument;
          const win = doc.defaultView;
          const apps = win.CitryStable ? [...win.CitryStable._apps.values()] : [];
          const app = apps[0];
          return {
            stable: typeof win.CitryStable?.startPrepared === 'function',
            apps: apps.length,
            revision: app?.revision ?? null,
            mounted: app?.mounted?.size ?? 0,
            terminal: app?.terminal ?? null,
            legacyManifests: doc.querySelectorAll(
              'script[data-citry-graph], script[data-citry-events], script[data-citry]'
            ).length,
            preparedBootstraps: [...doc.scripts].filter(script =>
              script.textContent.includes('CitryStable.startPrepared(')
            ).length,
          };
        }"""
    )
    assert runtime == {
        "stable": True,
        "apps": 1,
        "revision": 0,
        "mounted": expected_occurrences,
        "terminal": False,
        "legacyManifests": 0,
        "preparedBootstraps": 1,
    }
    assert page.evaluate("window.__previewCommitted") is True
    assert page.evaluate("window.__previewDiagnostics") == []


def test_preview_bridge_waits_for_ordered_external_scripts_before_vue_bootstrap(
    page: Any,
    workspace_static_url: str,
) -> None:
    def fulfill_external_script(route: Any) -> None:
        time.sleep(0.2)
        route.fulfill(
            status=200,
            content_type="text/javascript",
            body="window.__activationOrder.push('external');",
        )

    page.route(
        "**/__tests__/ordered-script.js",
        fulfill_external_script,
    )
    html = """
      <!doctype html>
      <html lang="en">
        <head></head>
        <body>
          <script>
            window.__activationOrder = [];
          </script>
          <script src="/__tests__/ordered-script.js"></script>
          <script>
            // A prepared Vue bootstrap is activated only after the preceding
            // parser-style external script has settled.
            window.__activationOrder.push('vue-bootstrap');
          </script>
        </body>
      </html>
    """

    _render_through_preview_bridge(page, workspace_static_url, html)
    order = (
        page.frame_locator("#preview")
        .locator("body")
        .evaluate("body => body.ownerDocument.defaultView.__activationOrder")
    )

    assert order == ["external", "vue-bootstrap"]
    assert page.evaluate("window.__previewDiagnostics") == []


def test_preview_bridge_loads_internal_assets_before_committing_candidate(
    page: Any,
    workspace_static_url: str,
) -> None:
    script_path = "/__citry_playground__/cache/Test.abc123.js"
    style_path = "/__citry_playground__/cache/Test.abc123.css"
    html = f"""
      <!doctype html>
      <html lang="en">
        <head>
          <link rel="stylesheet" href="{style_path}">
        </head>
        <body>
          <output id="asset-status">waiting</output>
          <script src="{script_path}"></script>
        </body>
      </html>
    """
    assets = [
        {
            "path": script_path,
            "contentType": "text/javascript",
            "content": "document.querySelector('#asset-status').textContent = 'ready';",
        },
        {
            "path": style_path,
            "contentType": "text/css",
            "content": "#asset-status { color: rgb(12, 34, 56); }",
        },
    ]

    _render_through_preview_bridge(page, workspace_static_url, html, assets=assets)
    preview = page.frame_locator("#preview")

    expect(preview.locator("#asset-status")).to_have_text("ready")
    color = preview.locator("#asset-status").evaluate("element => getComputedStyle(element).color")
    assert color == "rgb(12, 34, 56)"
    assert page.evaluate("window.__previewCommitted") is True
    assert page.evaluate("window.__previewDiagnostics") == []


def test_preview_bridge_keeps_displayed_result_when_candidate_asset_fails(
    page: Any,
    workspace_static_url: str,
) -> None:
    _render_through_preview_bridge(
        page,
        workspace_static_url,
        "<!doctype html><html><body><output id='stable'>Last good result</output></body></html>",
    )
    failed_html = """
      <!doctype html>
      <html>
        <head>
          <script src="/__citry_playground__/cache/Missing.abc123.js"></script>
        </head>
        <body><output id="replacement">Broken candidate</output></body>
      </html>
    """

    message = page.evaluate(
        """async html => {
          try {
            await window.__previewBridge.render(html, 2);
            return "";
          } catch (error) {
            return String(error?.message || error);
          }
        }""",
        failed_html,
    )

    assert message == "Missing test asset: /__citry_playground__/cache/Missing.abc123.js"
    preview = page.frame_locator("#preview")
    expect(preview.locator("#stable")).to_have_text("Last good result")
    expect(preview.locator("#replacement")).to_have_count(0)
    expect(page.locator("iframe[id$='-candidate']")).to_have_count(0)
