"""Focused browser acceptance for standard and strict-CSP serialization."""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

_READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"
_SIGNING_KEY = "phase7-runtime-variant"


@pytest.mark.parametrize("runtime", ["standard", "csp"])
def test_runtime_variant_keeps_evaluators_ownership_morph_events_and_fragments(
    page: Any,
    serve_live: Any,
    runtime: str,
) -> None:
    """Run one CSP-compatible reached tree through both complete bundles."""
    nonce = "phase7RuntimeNonce"
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    calls: list[int] = []
    app = Citry(secret=_SIGNING_KEY, security_csp="strict" if runtime == "csp" else "off")
    app.set_mounted_prefix("/citry")

    class CounterState:
        count: int = 1
        _public = ("count",)

    class Counter(Component):
        citry = app
        State = CounterState
        js = """
          $component(({ els }) => {
            window.__variantCallbacks = (window.__variantCallbacks || 0) + 1;
            els[0].dataset.callbackReady = "true";
          });
        """
        template = """
          <section class="counter">
            <output class="value" x-text="$state.count">1</output>
            <button class="save" @c-click="save">save</button>
            <div x-data="{ localCount: 1 }">
              <button class="local" @click="localCount++">increment locally</button>
              <output class="local-value" x-text="localCount">1</output>
            </div>
          </section>
        """

        class Events:
            def save(self, state: CounterState) -> None:
                calls.append(state.count)

    class Page(Component):
        citry = app
        template = "<html><body><c-counter /></body></html>"

    initial = Page().render().serialize(csp_nonce=nonce)
    fresh = Counter(count=7).render().serialize(deps_strategy="fragment", csp_nonce=nonce)
    base = serve_live(app, initial, "")

    if runtime == "csp":
        page.add_init_script(
            """
            window.__cspViolations = [];
            document.addEventListener("securitypolicyviolation", (event) => {
              window.__cspViolations.push({
                blockedURI: event.blockedURI,
                effectiveDirective: event.effectiveDirective,
              });
            });
            """
        )

        def add_csp_header(route: Any) -> None:
            response = route.fetch()
            headers = dict(response.headers)
            headers["content-security-policy"] = (
                f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; connect-src 'self'"
            )
            route.fulfill(response=response, headers=headers)

        page.route(base + "/", add_csp_header)
    page.goto(base + "/")
    page.wait_for_function(_READY)
    page.wait_for_function("document.querySelector('.counter')?.dataset.callbackReady === 'true'")

    result = page.evaluate(
        """
        async (html) => {
          const root = document.querySelector(".counter");
          const oldId = root.getAttribute("data-cid");
          const internal = Citry.events._internal;
          const anchor = internal.getAnchor(oldId);
          const revision = Citry.manager.ownership.revisions().find(
            (candidate) => Citry.manager.ownership.forRender(candidate, oldId),
          );
          const oldOwned = !!Citry.manager.ownership.forRender(revision, oldId);
          const normalValue = Alpine.evaluate(root, "$state.count");
          const rawValue = Alpine.evaluateRaw(root, "$state.count");
          const evaluatorErrors = [];
          Alpine.setErrorHandler((error) => evaluatorErrors.push(String(error.message || error)));
          const normalArrowValue = Alpine.evaluate(root, "(() => 3)()");
          let rawArrow;
          try {
            rawArrow = { accepted: true, value: Alpine.evaluateRaw(root, "(() => 2)()") };
          } catch (error) {
            rawArrow = { accepted: false };
          }
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + oldId, swap: "morph", html }],
            },
            { anchor, instance: oldId, event: "save" },
          );
          const freshRoot = document.querySelector(".counter");
          const freshId = freshRoot.getAttribute("data-cid");
          const freshRevision = Citry.manager.ownership.revisions().find(
            (candidate) => Citry.manager.ownership.forRender(candidate, freshId),
          );
          return {
            normalValue,
            rawValue,
            normalArrow: { errors: evaluatorErrors.length, value: normalArrowValue },
            rawArrow,
            oldOwned,
            idChanged: freshId !== oldId,
            oldRetired: internal.getAnchor(oldId) === null,
            sameAnchor: internal.getAnchor(freshId) === anchor,
            freshOwned: !!Citry.manager.ownership.forRender(freshRevision, freshId),
            count: internal.getAnchor(freshId).values.count,
          };
        }
        """,
        fresh,
    )

    expected = {
        "normalValue": 1,
        "rawValue": 1,
        "normalArrow": {"errors": int(runtime == "csp"), "value": None},
        "rawArrow": {"accepted": runtime == "standard"},
        "oldOwned": True,
        "idChanged": True,
        "oldRetired": True,
        "sameAnchor": True,
        "freshOwned": True,
        "count": 7,
    }
    if runtime == "standard":
        expected["normalArrow"]["value"] = 3
        expected["rawArrow"]["value"] = 2
    assert result == expected
    page.wait_for_function("document.querySelector('.value')?.textContent === '7'")
    page.wait_for_function("window.__variantCallbacks === 2")
    page.click(".local")
    page.wait_for_function("document.querySelector('.local-value')?.textContent === '2'")
    with page.expect_response(lambda response: f"/e/{Counter.class_id}/save" in response.url):
        page.click(".save")
    assert calls == [7]
    if runtime == "csp":
        assert page.evaluate("window.__cspViolations") == []
    assert page_errors == []


def test_strict_fragment_is_rejected_by_a_standard_base_manager(page: Any, serve_live: Any) -> None:
    nonce = "phase8MismatchNonce"
    app = Citry(secret=_SIGNING_KEY)
    app.set_mounted_prefix("/citry")

    class Card(Component):
        citry = app
        template = """
            <div x-data="{}"></div>
        """

    initial = Card().render().serialize(csp_nonce=nonce)
    fragment = (
        Card()
        .render()
        .serialize(
            deps_strategy="fragment",
            csp_nonce=nonce,
            security_csp="strict",
        )
    )
    match = re.search(
        r'<script\b[^>]*\bdata-citry(?:=""|(?=\s|>))[^>]*>(.*?)</script>',
        fragment,
        re.DOTALL,
    )
    assert match is not None
    manifest = json.loads(match.group(1))
    base = serve_live(app, initial, "")

    page.goto(base + "/")
    page.wait_for_function(_READY)

    result = page.evaluate(
        """
        (manifest) => {
          try {
            Citry.manager.ownership._preflightDependency(manifest, manifest.graph);
            return null;
          } catch (error) {
            return String(error.message || error);
          }
        }
        """,
        manifest,
    )

    assert result == "[Citry] Alpine: the page requires the 'standard' runtime but received 'csp'."
