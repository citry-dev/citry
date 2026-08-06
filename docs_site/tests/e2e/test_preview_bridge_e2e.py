"""Browser coverage for rendered HTML delivered through PreviewBridge."""

from __future__ import annotations

import json
import re
import time
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e

_GRAPH_MANIFEST_RE = re.compile(
    r"<script\b(?=[^>]*\bdata-citry-graph\b)[^>]*>(.*?)</script>",
    re.DOTALL,
)


def _client_active_tabs_page() -> str:
    app = Citry(
        autodiscover=False,
        secret="preview-bridge-regression-secret",  # noqa: S106 - test key
    )
    app.register_library(citry_ui)

    class EventProbe(Component):
        citry = app

        class State:
            count: int = 7

        class Events:
            def ping(self) -> None:
                return None

        template = """
          <section id="event-probe" x-init="window.__initialState = $state.count">
            <output id="initial-state" x-text="$state.count"></output>
            <button type="button" @c-click="ping">Ping</button>
          </section>
        """

    class Demo(Component):
        citry = app
        template = """
          <main x-data="{ selected: 'account', changes: 0 }">
            <c-CTabs
              id="outer-tabs"
              default_value="account"
              aria_label="Outer sections"
              $c-props="{
                value: selected,
                onValueChange: (value, detail) => {
                  selected = value;
                  changes += 1;
                  window.__outerChange = { value, source: detail.source, changes };
                },
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
            <output id="selected-value" x-text="selected">account</output>
            <c-EventProbe />
          </main>
        """

    return f"<!doctype html><html lang='en'><head></head><body>{Demo()}</body></html>"


def _render_through_preview_bridge(
    page: Any,
    base_url: str,
    html: str,
    *,
    assets: list[dict[str, str]] | None = None,
) -> None:
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


def _ownership_instance_count(html: str) -> int:
    match = _GRAPH_MANIFEST_RE.search(html)
    assert match is not None
    manifest = json.loads(match.group(1))
    return sum(len(graph["componentInstances"]) for graph in manifest["graphs"])


def test_preview_bridge_waits_for_alpine_before_processing_citry_manifests(
    page: Any,
    workspace_static_url: str,
) -> None:
    html = _client_active_tabs_page()
    expected_lifecycles = _ownership_instance_count(html)
    _render_through_preview_bridge(page, workspace_static_url, html)
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
          const debug = doc.defaultView.Citry.alpine._debug();
          return {
            alpine: {
              installed: debug.installed,
              ready: debug.ready,
              started: debug.started,
            },
            hooks: debug.hooks,
            runtime: {
              ownershipRevisions: debug.runtime.ownershipRevisions,
              ownershipStates: debug.runtime.ownershipStates,
              dependencyClaims: debug.runtime.dependencyClaims,
              graphFailures: debug.runtime.graphFailures,
              pendingCalls: debug.runtime.pendingCalls,
              lifecycles: debug.runtime.lifecycles,
              propsEffects: debug.runtime.propsEffects,
            },
            manifests: {
              graphs: doc.querySelectorAll(
                'script[data-citry-graph][data-citry-graph-processed]'
              ).length,
              events: doc.querySelectorAll(
                'script[data-citry-events][data-citry-events-processed]'
              ).length,
              dependencies: doc.querySelectorAll(
                'script[data-citry][data-citry-processed]'
              ).length,
              eventsPairedWithGraph: doc.querySelector(
                'script[data-citry-events]'
              )?.previousElementSibling?.matches(
                'script[data-citry-graph]'
              ) === true,
            },
          };
        }"""
    )
    assert runtime["alpine"] == {"installed": True, "ready": True, "started": True}
    assert runtime["hooks"] == {"installs": 1, "roots": 1, "init": 1, "morph": 0, "starts": 1}
    assert runtime["runtime"] == {
        "ownershipRevisions": 1,
        "ownershipStates": 1,
        "dependencyClaims": 1,
        "graphFailures": 0,
        "pendingCalls": 0,
        "lifecycles": expected_lifecycles,
        "propsEffects": 1,
    }
    assert runtime["manifests"] == {
        "graphs": 1,
        "events": 1,
        "dependencies": 1,
        "eventsPairedWithGraph": True,
    }
    assert page.evaluate("window.__previewCommitted") is True
    assert page.evaluate("window.__previewDiagnostics") == []


def test_preview_bridge_waits_for_ordered_external_scripts_before_manifests(
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
            new MutationObserver(() => {
              if (document.querySelector('script[data-citry]')) {
                window.__activationOrder.push('manifest');
              }
            }).observe(document, { childList: true, subtree: true });
          </script>
          <script src="/__tests__/ordered-script.js"></script>
          <script type="application/json" data-citry>{}</script>
        </body>
      </html>
    """

    _render_through_preview_bridge(page, workspace_static_url, html)
    order = (
        page.frame_locator("#preview")
        .locator("body")
        .evaluate("body => body.ownerDocument.defaultView.__activationOrder")
    )

    assert order == ["external", "manifest"]
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
