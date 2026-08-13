"""
Cross-browser e2e for the client-side dependency manager, the browser runtime
shipped as ``citry/ext/dependencies/client/citry.js`` (design contract:
docs/design/dependencies.md section 8). The suite locks the runtime's whole
behavior surface:

- The public ``Citry.manager`` API, the load-once guard (a second load of
  the script keeps the existing manager and its state), and the runtime
  adding its manager to a pre-existing ``Citry`` global rather than
  replacing it.
- Loading scripts/stylesheets from ``{tag, attrs, content}`` descriptors:
  URL dedupe, the already-loaded bookkeeping (``markScriptLoaded`` /
  ``isScriptLoaded``), inline scripts running synchronously, URL-less inline
  scripts and styles never deduped, and how descriptor attributes render.
- Per-instance component calls: the payload shape (``{id, els, data}``),
  calls queueing until both the callback and the data have arrived (in any
  order), queue-order flushing, and a throwing callback not breaking the
  flush.
- Manifest tags (``<script type="application/json" data-citry>``, string
  fields base64): processed at startup when already in the document, picked
  up by the MutationObserver when inserted later (directly or nested inside
  an inserted subtree), processed exactly once, every manifest key optional,
  and a malformed manifest not breaking later ones.
- ``Citry.manager.decorateContext(fn)``: page scripts (e.g. extension
  runtimes) add members to the payload object that ``$component`` callbacks
  receive. Decorators run just before the callbacks, in registration order,
  mutate the payload in place (return values are ignored), are
  error-isolated, and can be unregistered.
- Teardown: a ``$component`` callback may return a cleanup function, which
  runs exactly once before the callbacks fire again for the same instance id.
  Cleanups are stored per instance: a call for a different instance of the
  same class leaves another instance's cleanup alone. Only a function return
  counts: any other value (e.g. the Promise an async callback implicitly
  returns) is ignored, never invoked as a cleanup.
- The instance lifecycle: an instance's cleanup also runs when its last
  ``data-cid-<id>`` element leaves the page, caught both for a real node
  removal and for an in-place ``data-cid`` swap; a class-level
  ``Component.css`` sheet (tagged ``data-citry-css-class``) is dropped when the
  class's last instance leaves, deferred so a same-class re-render in place
  keeps the sheet; and a callback that synchronously triggers a nested flush
  does not re-run the in-flight call.
- The full fragment pipeline: fresh data and elements after a re-render,
  per-instance calls for sibling instances, and the pre-loader bootstrapping
  the runtime on a page that never had it.

Uses the live-server harness like test_fragment_e2e.py. Tests that exercise a
later call for the same instance submit the dependency call independently of
the already-committed physical graph. The basic document/fragment strategies
themselves are covered by
test_document_e2e.py and test_fragment_e2e.py; this module targets the
runtime's own mechanics.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

# The initial page: load the runtime, run per-test setup JS (registering
# decorators and the shared log), and expose a helper that fetches the
# fragment and drops it into #target. Repeated calls replace the content,
# so the same instance id is "called" again by the fresh manifest.
_PAGE = """
<html>
  <head><script src="/citry/citry.js"></script></head>
  <body>
    <script>
      window.__log = [];
      // __SETUP__
      window.__insertFragment = () =>
        fetch('/fragment')
          .then((r) => r.text())
          .then((html) => { document.getElementById('target').innerHTML = html; });
      window.__refireFragmentCall = () => {
        const manifest = JSON.parse(document.querySelector('script[data-citry]').textContent);
        manifest.graph = null;
        for (const kind of ['js', 'css']) {
          manifest.fetch[kind] = manifest.fetch[kind].map((entry) => Array.isArray(entry) ? entry[0] : entry);
        }
        Citry.manager._loadComponentScripts(manifest);
      };
      window.__insertFreshCallManifest = () => {
        const manifest = JSON.parse(document.querySelector('script[data-citry]').textContent);
        manifest.graph = null;
        for (const kind of ['js', 'css']) {
          manifest.fetch[kind] = manifest.fetch[kind].map((entry) => Array.isArray(entry) ? entry[0] : entry);
        }
        const tag = document.createElement('script');
        tag.type = 'application/json';
        tag.dataset.citry = '';
        tag.textContent = JSON.stringify(manifest);
        document.body.append(tag);
      };
    </script>
    <div id="target"></div>
  </body>
</html>
"""


def _page(setup_js: str = "") -> str:
    return _PAGE.replace("// __SETUP__", setup_js)


def _b64(text: str) -> str:
    """Base64 of the UTF-8 bytes, the armor manifest string fields ride in."""
    return base64.b64encode(text.encode()).decode()


def _serve_runtime_page(serve_live: Any, setup_js: str = "") -> str:
    """Serve a page that loads only the runtime (no components), for direct manager API tests."""
    c = Citry()
    c.set_mounted_prefix("/citry")
    return serve_live(c, _page(setup_js), "")


def _serve_nonced_runtime_page(serve_live: Any, nonce: str) -> str:
    """Serve the manager from a script tag carrying one document CSP nonce."""
    c = Citry()
    c.set_mounted_prefix("/citry")
    html = _page().replace(
        '<script src="/citry/citry.js"></script>',
        f'<script nonce="{nonce}" src="/citry/citry.js"></script>',
    )
    return serve_live(c, html, "")


def _serve_fragment(serve_live: Any, component_js: str, setup_js: str = "") -> str:
    """Build a one-component engine and serve the page + its fragment; returns the base URL."""
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Frag(Component):
        citry = c
        template = """
          <div class="frag">frag</div>
        """
        js = component_js

    fragment_html = Frag().render().serialize(deps_strategy="fragment")
    return serve_live(c, _page(setup_js), fragment_html)


# ----- Public surface and the load-once guard -----


def test_manager_api_surface_is_locked(page: Any, serve_live: Any) -> None:
    # The exact members of `Citry.manager` are the contract page scripts and
    # extension runtimes program against; a member appearing or disappearing
    # must be a deliberate change.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    keys = page.evaluate("() => Object.keys(Citry.manager).sort()")
    assert keys == [
        "_loadComponentScripts",
        "_stageOwnershipManifest",
        "callComponent",
        "decorateContext",
        "isScriptLoaded",
        "loadCss",
        "loadJs",
        "markScriptLoaded",
        "ownership",
        "registerComponent",
        "registerComponentData",
    ]


def test_second_runtime_load_keeps_existing_manager_and_state(page: Any, serve_live: Any) -> None:
    # A page and a fragment may both include the runtime; the second
    # execution must return early, keeping the existing manager object and
    # everything registered on it (loaded URLs, callbacks).
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        async () => {
          const before = Citry.manager;
          Citry.manager.markScriptLoaded("js", "/kept.js");
          // Run the runtime source a second time, as a duplicate <script> would.
          const source = await fetch("/citry/citry.js").then((r) => r.text());
          eval(source);
          return {
            sameManager: Citry.manager === before,
            keptState: Citry.manager.isScriptLoaded("js", "/kept.js"),
          };
        }
        """
    )
    assert result == {"sameManager": True, "keptState": True}


def test_runtime_preserves_a_preexisting_citry_namespace(page: Any, serve_live: Any) -> None:
    # A script that runs before the runtime (e.g. an extension runtime) may
    # have created `globalThis.Citry` already, without a manager; the runtime
    # must add its manager to that object, not replace the object and lose
    # the members already on it.
    page_html = """
    <html>
      <head>
        <script>globalThis.Citry = { probe: 1 };</script>
        <script src="/citry/citry.js"></script>
      </head>
      <body></body>
    </html>
    """
    c = Citry()
    c.set_mounted_prefix("/citry")
    base = serve_live(c, page_html, "")
    page.goto(base + "/")

    result = page.evaluate("() => ({ probe: Citry.probe, hasManager: !!Citry.manager })")
    assert result == {"probe": 1, "hasManager": True}


# ----- Script and style loading with URL dedupe -----


def test_manager_propagates_its_document_nonce_and_preflights_conflicting_batches(
    page: Any,
    serve_live: Any,
) -> None:
    nonce = "browserNonce123"
    base = _serve_nonced_runtime_page(serve_live, nonce)
    page.goto(base + "/")

    result = page.evaluate(
        """
        async (nonce) => {
          const m = Citry.manager;
          await m.loadJs({
            tag: "script",
            attrs: { "data-nonce-js": true },
            content: "window.__nonceScriptRan = true;",
          });
          await m.loadCss({
            tag: "style",
            attrs: { "data-nonce-style": true },
            content: ".nonce-probe { color: green; }",
          });
          await m.loadJs({
            tag: "script",
            attrs: { nonce: nonce, "data-matching-nonce": true },
            content: "window.__matchingNonceRan = true;",
          });

          const encode = (value) => btoa(JSON.stringify(value));
          const manifest = {
            fetch: {
              css: [encode({
                tag: "style",
                attrs: { "data-atomic-style": true },
                content: ".atomic { color: blue; }",
              })],
              js: [encode({
                tag: "script",
                attrs: { nonce: "conflictingNonce", "data-atomic-script": true },
                content: "window.__atomicScriptRan = true;",
              })],
            },
          };
          let conflict = null;
          try {
            m._loadComponentScripts(manifest);
          } catch (error) {
            conflict = String(error);
          }
          let nullConflict = null;
          try {
            await m.loadJs({
              tag: "script",
              attrs: { nonce: null, "data-null-nonce": true },
              content: "window.__nullNonceRan = true;",
            });
          } catch (error) {
            nullConflict = String(error);
          }

          const js = document.querySelector("script[data-nonce-js]");
          const style = document.querySelector("style[data-nonce-style]");
          const matching = document.querySelector("script[data-matching-nonce]");
          return {
            jsNonce: js && js.nonce,
            styleNonce: style && style.nonce,
            matchingNonce: matching && matching.nonce,
            ran: window.__nonceScriptRan === true && window.__matchingNonceRan === true,
            conflict,
            nullConflict,
            atomicStyleInserted: !!document.querySelector("style[data-atomic-style]"),
            atomicScriptInserted: !!document.querySelector("script[data-atomic-script]"),
            nullNonceInserted: !!document.querySelector("script[data-null-nonce]"),
          };
        }
        """,
        nonce,
    )

    assert result == {
        "jsNonce": nonce,
        "styleNonce": nonce,
        "matchingNonce": nonce,
        "ran": True,
        "conflict": "TypeError: [Citry] dependency descriptor nonce differs from the loaded document nonce.",
        "nullConflict": "TypeError: [Citry] dependency descriptor nonce differs from the loaded document nonce.",
        "atomicStyleInserted": False,
        "atomicScriptInserted": False,
        "nullNonceInserted": False,
    }


def test_load_js_appends_once_per_url_and_marks_loaded(page: Any, serve_live: Any) -> None:
    # loadJs appends a <script> to <body> and resolves once it has loaded;
    # the same URL is never fetched twice (even while the first request is
    # still in flight), and a URL marked as loaded up front is never fetched
    # at all. The runtime's own URL (with a query string) serves as a real,
    # executable script target.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        async () => {
          const m = Citry.manager;
          const url = (probe) => "/citry/citry.js?probe=" + probe;
          const count = (u) => document.body.querySelectorAll('script[src="' + u + '"]').length;

          await m.loadJs({ tag: "script", attrs: { src: url("a") } });
          const afterFirst = count(url("a"));
          await m.loadJs({ tag: "script", attrs: { src: url("a") } });
          const afterRepeat = count(url("a"));
          await m.loadJs({ tag: "script", attrs: { src: url("b") } });
          const afterOther = count(url("b"));

          m.markScriptLoaded("js", url("c"));
          await m.loadJs({ tag: "script", attrs: { src: url("c") } });
          const afterMarked = count(url("c"));

          // A URL is recorded as loaded when its request starts, not when it
          // finishes: two fragments inserted in the same batch may request the
          // same script, and the second request must not fetch (and so run) it
          // a second time. Nothing is awaited until both requests are made.
          const inFlight = m.loadJs({ tag: "script", attrs: { src: url("d") } });
          const markedWhileInFlight = m.isScriptLoaded("js", url("d"));
          const inFlightRepeat = m.loadJs({ tag: "script", attrs: { src: url("d") } });
          const sameInFlightPromise = inFlight === inFlightRepeat;
          await inFlight;
          await inFlightRepeat;
          const afterInFlight = count(url("d"));

          const failedUrl = url("failed-integrity");
          const failedDescriptor = {
            tag: "script",
            attrs: { src: failedUrl, integrity: "sha256-AAAA" },
          };
          await m.loadJs(failedDescriptor).catch(() => {});
          const markedAfterFailure = m.isScriptLoaded("js", failedUrl);
          await m.loadJs(failedDescriptor).catch(() => {});
          const failedAttempts = count(failedUrl);

          return {
            afterFirst,
            afterRepeat,
            afterOther,
            afterMarked,
            markedWhileInFlight,
            sameInFlightPromise,
            afterInFlight,
            markedAfterFailure,
            failedAttempts,
            loadedA: m.isScriptLoaded("js", url("a")),
            loadedB: m.isScriptLoaded("js", url("b")),
          };
        }
        """
    )
    assert result == {
        "afterFirst": 1,
        "afterRepeat": 1,
        "afterOther": 1,
        "afterMarked": 0,
        "markedWhileInFlight": True,
        "sameInFlightPromise": True,
        "afterInFlight": 1,
        "markedAfterFailure": False,
        "failedAttempts": 2,
        "loadedA": True,
        "loadedB": True,
    }


def test_load_css_waits_dedupes_and_retries_failures(page: Any, serve_live: Any) -> None:
    # The CSS counterpart: loadCss appends to <head>, resolves only after the
    # stylesheet loads, shares an in-flight promise, dedupes by href, clears a
    # failed URL so a later call can retry, honors a URL marked as loaded up
    # front, and appends href-less inline styles without dedupe.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        async () => {
          const m = Citry.manager;
          const url = (probe) =>
            "data:text/css,.citry-" + probe + "%7Bcolor%3Argb(1%2C2%2C3)%7D";
          const count = (u) =>
            Array.from(document.head.querySelectorAll("link[href]")).filter(
              (element) => element.getAttribute("href") === u,
            ).length;

          const first = m.loadCss({ tag: "link", attrs: { rel: "stylesheet", href: url("a") } });
          const repeatInFlight = m.loadCss({ tag: "link", attrs: { rel: "stylesheet", href: url("a") } });
          const sameInFlightPromise = first === repeatInFlight;
          await first;
          await repeatInFlight;
          const afterFirst = count(url("a"));
          await m.loadCss({ tag: "link", attrs: { rel: "stylesheet", href: url("a") } });
          const afterRepeat = count(url("a"));
          await m.loadCss({ tag: "link", attrs: { rel: "stylesheet", href: url("b") } });
          const afterOther = count(url("b"));

          m.markScriptLoaded("css", url("c"));
          await m.loadCss({ tag: "link", attrs: { rel: "stylesheet", href: url("c") } });
          const afterMarked = count(url("c"));

          const bad = "/citry/cache/does-not-exist.css";
          const loadBad = () =>
            m.loadCss({ tag: "link", attrs: { rel: "stylesheet", href: bad } })
              .then(() => "resolved", () => "rejected");
          const firstFailure = await loadBad();
          const retryFailure = await loadBad();

          // An inline <style> (no href) has no URL to dedupe on, so a
          // repeated load appends it again, mirroring inline scripts.
          const inline = () => ({
            tag: "style",
            attrs: { "data-inline-probe": true },
            content: ".probe { color: red; }",
          });
          await m.loadCss(inline());
          await m.loadCss(inline());
          const inlineStyles = document.head.querySelectorAll("style[data-inline-probe]").length;

          return {
            afterFirst,
            afterRepeat,
            afterOther,
            afterMarked,
            sameInFlightPromise,
            firstFailure,
            retryFailure,
            failedAttempts: count(bad),
            markedAfterFailure: m.isScriptLoaded("css", bad),
            inlineStyles,
            loadedA: m.isScriptLoaded("css", url("a")),
            // The js and css URL books are separate: a loaded stylesheet
            // does not mark the same URL as a loaded script.
            crossType: m.isScriptLoaded("js", url("a")),
            bodyUntouched: document.body.querySelectorAll("link").length === 0,
          };
        }
        """
    )
    assert result == {
        "afterFirst": 1,
        "afterRepeat": 1,
        "afterOther": 1,
        "afterMarked": 0,
        "sameInFlightPromise": True,
        "firstFailure": "rejected",
        "retryFailure": "rejected",
        "failedAttempts": 2,
        "markedAfterFailure": False,
        "inlineStyles": 2,
        "loadedA": True,
        "crossType": False,
        "bodyUntouched": True,
    }


def test_load_js_rejects_when_the_script_fails_to_load(page: Any, serve_live: Any) -> None:
    # A script URL that cannot be fetched (a 404 here) rejects the returned
    # promise, so a caller awaiting the load sees the failure. A failed URL is
    # removed from both the loaded and in-flight indexes, allowing a later
    # caller to make a real retry rather than silently skipping the script.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        async () => {
          const m = Citry.manager;
          const bad = "/citry/cache/does-not-exist.js";
          const load = () =>
            m.loadJs({ tag: "script", attrs: { src: bad } }).then(() => "resolved", () => "rejected");
          const first = await load();
          const retry = await load();
          return {
            first,
            retry,
            stillMarked: m.isScriptLoaded("js", bad),
            tags: document.body.querySelectorAll('script[src="' + bad + '"]').length,
          };
        }
        """
    )
    assert result == {"first": "rejected", "retry": "rejected", "stillMarked": False, "tags": 2}


def test_load_js_inline_content_runs_synchronously_and_is_not_deduped(page: Any, serve_live: Any) -> None:
    # An inline descriptor (no src) runs the moment it is appended, so the
    # counter is read before each returned promise is awaited (reading only
    # after the await could not tell synchronous execution apart from
    # execution by resolution time); without a URL there is nothing to
    # dedupe on, so a repeated inline load runs again.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        async () => {
          const m = Citry.manager;
          const descriptor = () => ({
            tag: "script",
            attrs: {},
            content: "window.__inlineRuns = (window.__inlineRuns || 0) + 1;",
          });
          const first = m.loadJs(descriptor());
          const ranBeforeFirstAwait = window.__inlineRuns;
          await first;
          const second = m.loadJs(descriptor());
          const ranBeforeSecondAwait = window.__inlineRuns;
          await second;
          return { ranBeforeFirstAwait, ranBeforeSecondAwait };
        }
        """
    )
    assert result == {"ranBeforeFirstAwait": 1, "ranBeforeSecondAwait": 2}


def test_descriptor_attrs_render_semantics(page: Any, serve_live: Any) -> None:
    # How a descriptor's attrs land on the element: `true` becomes a bare
    # (empty-valued) attribute, `false` and `null` are omitted, everything
    # else is stringified; `content` becomes the element's text.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        async () => {
          await Citry.manager.loadJs({
            tag: "script",
            attrs: {
              "data-str": "x",
              "data-num": 5,
              "data-flag": true,
              "data-off": false,
              "data-nul": null,
            },
            content: "window.__attrProbe = true;",
          });
          const el = document.body.querySelector("script[data-str]");
          return {
            str: el.getAttribute("data-str"),
            num: el.getAttribute("data-num"),
            flag: el.getAttribute("data-flag"),
            hasOff: el.hasAttribute("data-off"),
            hasNul: el.hasAttribute("data-nul"),
            text: el.textContent,
            ran: window.__attrProbe,
          };
        }
        """
    )
    assert result == {
        "str": "x",
        "num": "5",
        "flag": "",
        "hasOff": False,
        "hasNul": False,
        "text": "window.__attrProbe = true;",
        "ran": True,
    }


# ----- The per-instance call queue -----


def test_call_payload_shape_and_els_in_document_order(page: Any, serve_live: Any) -> None:
    # The callback receives one payload object: the instance id, every
    # element carrying the instance's data-cid marker (in document order),
    # and the data registered under the call's classId:varsHash key.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          document.body.insertAdjacentHTML(
            "beforeend",
            '<div data-cid-c7a>first</div><section data-cid-c7a>second</section>'
          );
          let captured = null;
          m.registerComponent("shape_cls", (ctx) => { captured = ctx; });
          m.registerComponentData("shape_cls", "h7", { hello: "world" });
          m.callComponent("shape_cls", "c7a", "h7");
          return {
            keys: Object.keys(captured).sort(),
            id: captured.id,
            data: captured.data,
            els: captured.els.map((el) => el.outerHTML),
          };
        }
        """
    )
    assert result == {
        "keys": ["data", "els", "id"],
        "id": "c7a",
        "data": {"hello": "world"},
        "els": ['<div data-cid-c7a="">first</div>', '<section data-cid-c7a="">second</section>'],
    }


def test_call_is_fire_and_forget_and_numeric_return_is_ignored(page: Any, serve_live: Any) -> None:
    # Component init is synchronous and side-effect-only. A callback's one
    # meaningful return is a cleanup function; an ordinary value is ignored
    # and callComponent itself returns undefined rather than a Promise.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          let calls = 0;
          document.body.insertAdjacentHTML("beforeend", '<div data-cid-c7b></div>');
          m.registerComponent("return_cls", () => {
            calls += 1;
            return 123;
          });
          const returned = m.callComponent("return_cls", "c7b", null);
          return { calls, isUndefined: returned === undefined };
        }
        """
    )
    assert result == {"calls": 1, "isUndefined": True}


def test_call_waits_for_callback_registration(page: Any, serve_live: Any) -> None:
    # The manifest's call and the data can arrive before the component's JS:
    # the call stays queued and fires the moment the callback registers.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          const log = [];
          document.body.insertAdjacentHTML("beforeend", '<div data-cid-c8a></div>');
          m.registerComponentData("wait_cb_cls", "h8", { n: 8 });
          m.callComponent("wait_cb_cls", "c8a", "h8");
          const firedBefore = log.length;
          m.registerComponent("wait_cb_cls", (ctx) => { log.push(ctx.data.n); });
          return { firedBefore, log };
        }
        """
    )
    assert result == {"firedBefore": 0, "log": [8]}


def test_call_waits_for_component_data(page: Any, serve_live: Any) -> None:
    # Mirror case: the callback and the call are in, but the data script has
    # not arrived; the call stays queued until registerComponentData.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          const log = [];
          document.body.insertAdjacentHTML("beforeend", '<div data-cid-c8b></div>');
          m.registerComponent("wait_data_cls", (ctx) => { log.push(ctx.data.n); });
          m.callComponent("wait_data_cls", "c8b", "h8b");
          const firedBefore = log.length;
          m.registerComponentData("wait_data_cls", "h8b", { n: 9 });
          return { firedBefore, log };
        }
        """
    )
    assert result == {"firedBefore": 0, "log": [9]}


def test_call_with_null_vars_hash_passes_null_data(page: Any, serve_live: Any) -> None:
    # A component with no js_data() produces a call with a null hash: no
    # data registration is awaited and the callback receives data === null.
    # The identity check must run in the page, because Playwright serializes
    # JS null and undefined both to Python None.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          const log = [];
          document.body.insertAdjacentHTML("beforeend", '<div data-cid-c9></div>');
          m.registerComponent("null_hash_cls", (ctx) => { log.push(ctx.data === null); });
          m.callComponent("null_hash_cls", "c9", null);
          return log;
        }
        """
    )
    assert result == [True]


def test_pending_call_does_not_block_a_later_ready_call(page: Any, serve_live: Any) -> None:
    # Each queued call is checked on its own: an earlier call still waiting
    # for its callback must not hold up a later call that is ready.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          const log = [];
          document.body.insertAdjacentHTML(
            "beforeend",
            '<div data-cid-c10a></div><div data-cid-c10b></div>'
          );
          m.callComponent("blocked_cls", "c10a", null);
          m.registerComponent("ready_cls", () => { log.push("ready"); });
          m.callComponent("ready_cls", "c10b", null);
          const afterReady = log.slice();
          m.registerComponent("blocked_cls", () => { log.push("blocked"); });
          return { afterReady, log };
        }
        """
    )
    assert result == {"afterReady": ["ready"], "log": ["ready", "blocked"]}


def test_queued_calls_flush_in_order_on_the_single_registration(page: Any, serve_live: Any) -> None:
    # Queued calls flush in order when the class's one registration arrives,
    # and each queued call is consumed exactly once.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          const log = [];
          document.body.insertAdjacentHTML(
            "beforeend",
            '<div data-cid-c11a></div><div data-cid-c11b></div>'
          );
          m.callComponent("order_cls", "c11a", null);
          m.callComponent("order_cls", "c11b", null);
          m.registerComponent("order_cls", (ctx) => { log.push("cb:" + ctx.id); });
          return log;
        }
        """
    )
    assert result == ["cb:c11a", "cb:c11b"]


def test_second_registration_for_a_class_throws_a_pointed_error(page: Any, serve_live: Any) -> None:
    # A class has one component definition. A second registration is an
    # authoring error, and the error identifies both the class and the fix.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          const log = [];
          m.registerComponent("DuplicateClass", () => { log.push("first"); });
          let isError = false;
          let message = null;
          try {
            m.registerComponent("DuplicateClass", () => {});
          } catch (err) {
            isError = err instanceof Error;
            message = String(err.message);
          }
          m.callComponent("DuplicateClass", "duplicate-instance", null);
          return { isError, message, log };
        }
        """
    )
    assert result == {
        "isError": True,
        "message": (
            "[Citry] component 'DuplicateClass' is already defined; "
            "only one $component registration is allowed per class."
        ),
        "log": ["first"],
    }


def test_malformed_definition_is_rejected_before_the_class_is_registered(page: Any, serve_live: Any) -> None:
    # A definition is either a callback or a config object with callable
    # `init`. Rejecting any other shape must leave the class free for a valid
    # definition, including when a call is already waiting for it.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          const log = [];
          m.callComponent("MalformedClass", "malformed-instance", null);
          let isTypeError = false;
          let message = null;
          try {
            m.registerComponent("MalformedClass", { props: {} });
          } catch (err) {
            isTypeError = err instanceof TypeError;
            message = String(err.message);
          }
          m.registerComponent("MalformedClass", () => { log.push("valid"); });
          return { isTypeError, message, log };
        }
        """
    )
    assert result == {
        "isTypeError": True,
        "message": (
            "[Citry] component 'MalformedClass' definition must be a callback function "
            "or a config object with an init function."
        ),
        "log": ["valid"],
    }


def test_throwing_callback_does_not_break_later_classes(page: Any, serve_live: Any) -> None:
    # A throwing callback is logged and skipped; a later ready call for a
    # different class still flushes.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    with page.expect_console_message(
        lambda msg: msg.type == "error" and "[Citry] component callback for" in msg.text
    ) as console_info:
        log = page.evaluate(
            """
            () => {
              const m = Citry.manager;
              const log = [];
              document.body.insertAdjacentHTML("beforeend", '<div data-cid-c13></div>');
              m.registerComponent("boom_cls", () => { throw new Error("callback boom"); });
              m.registerComponent("survivor_cls", () => { log.push("survivor"); });
              m.callComponent("boom_cls", "c13", null);
              m.callComponent("survivor_cls", "c13", null);
              return log;
            }
            """
        )
    assert log == ["survivor"]
    assert "callback boom" in console_info.value.text


def test_callback_fires_with_empty_els_when_marker_absent(page: Any, serve_live: Any) -> None:
    # A call whose instance id matches nothing in the DOM still runs the
    # callback, with an empty els list; the runtime does not treat a missing
    # element as an error.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          const log = [];
          m.registerComponent("ghost_cls", (ctx) => { log.push(ctx.els.length); });
          m.callComponent("ghost_cls", "cghost", null);
          return log;
        }
        """
    )
    assert result == [0]


# ----- Manifest processing -----


def test_manifest_marks_urls_fetches_tags_and_runs_calls(page: Any, serve_live: Any) -> None:
    # One manifest object end to end, through the same base64 armor the
    # server emits (UTF-8 included): markLoaded URLs get registered, fetch
    # descriptors are loaded (CSS before JS within the manifest), and each
    # calls entry runs its instance's callback with the registered data.
    utf8_probe = "čučoriedka only-ascii-breaks-here 🫐"
    css_descriptor = {"tag": "style", "attrs": {"data-probe": True}, "content": ".probe { color: red; }"}
    js_descriptor = {
        "tag": "script",
        "attrs": {},
        "content": (
            f'window.__cssWasFirst = !!document.querySelector("style[data-probe]"); window.__utf8 = "{utf8_probe}";'
        ),
    }
    manifest = {
        "markLoaded": {"js": [_b64("/dép/já.js")], "css": [_b64("/dép/já.css")]},
        "fetch": {
            "js": [_b64(json.dumps(js_descriptor, ensure_ascii=False))],
            "css": [_b64(json.dumps(css_descriptor, ensure_ascii=False))],
        },
        "calls": [[_b64("manifest_cls"), _b64("cman"), _b64("hman"), "init"]],
    }

    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        (manifest) => {
          const m = Citry.manager;
          const log = [];
          document.body.insertAdjacentHTML("beforeend", '<div data-cid-cman></div>');
          m.registerComponent("manifest_cls", (ctx) => { log.push([ctx.id, ctx.data]); });
          m.registerComponentData("manifest_cls", "hman", { greeting: "hello" });
          m._loadComponentScripts(manifest);
          return {
            log,
            markedJs: m.isScriptLoaded("js", "/dép/já.js"),
            markedCss: m.isScriptLoaded("css", "/dép/já.css"),
            cssWasFirst: window.__cssWasFirst,
            utf8: window.__utf8,
            styleCount: document.head.querySelectorAll("style[data-probe]").length,
          };
        }
        """,
        manifest,
    )
    assert result == {
        "log": [["cman", {"greeting": "hello"}]],
        "markedJs": True,
        "markedCss": True,
        "cssWasFirst": True,
        "utf8": utf8_probe,
        "styleCount": 1,
    }


def test_manifest_with_all_keys_absent_is_a_safe_no_op(page: Any, serve_live: Any) -> None:
    # Every manifest key is optional: markLoaded, fetch, and calls (and their
    # js/css members) each default to empty. A hand-authored manifest with
    # the keys absent must be a no-op (nothing appended, no call fired, no
    # error logged), and the manager must keep working afterwards. A removed
    # default would throw out of the evaluate and fail the test.
    console_errors: list[str] = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          const log = [];
          document.body.insertAdjacentHTML("beforeend", '<div data-cid-c15></div>');
          m.registerComponent("optional_keys_cls", (ctx) => { log.push(ctx.id); });
          const countTags = () => document.querySelectorAll("script, style, link").length;
          const before = countTags();
          m._loadComponentScripts({});
          const appended = countTags() - before;
          const firedByEmpty = log.length;
          // The manager is untouched: a normal call still flushes.
          m.callComponent("optional_keys_cls", "c15", null);
          return { appended, firedByEmpty, log };
        }
        """
    )
    assert result == {"appended": 0, "firedByEmpty": 0, "log": ["c15"]}
    assert not [text for text in console_errors if "[Citry]" in text]


def test_manifest_present_before_runtime_is_processed_at_startup(page: Any, serve_live: Any) -> None:
    # A manifest tag that is already in the document when the runtime loads
    # (here: earlier in the HTML than the runtime's own script tag) is
    # processed at startup, without any DOM mutation to observe.
    manifest_json = json.dumps(
        {
            "markLoaded": {"js": [], "css": []},
            "fetch": {"js": [], "css": []},
            "calls": [[_b64("boot_cls"), _b64("cboot"), None, "init"]],
        }
    )
    page_html = f"""
    <html>
      <body>
        <script type="application/json" data-citry>{manifest_json}</script>
        <div data-cid-cboot></div>
        <script src="/citry/citry.js"></script>
        <script>
          window.__log = [];
          Citry.manager.registerComponent("boot_cls", (ctx) => {{ window.__log.push(ctx.id); }});
        </script>
      </body>
    </html>
    """
    c = Citry()
    c.set_mounted_prefix("/citry")
    base = serve_live(c, page_html, "")
    page.goto(base + "/")

    page.wait_for_function("window.__log && window.__log.length === 1")
    assert page.evaluate("window.__log") == ["cboot"]


def test_manifest_nested_in_inserted_subtree_is_processed(page: Any, serve_live: Any) -> None:
    # The MutationObserver also finds manifests that are descendants of an
    # inserted node (an HTMX-style swap wraps the fragment in a container),
    # not only manifests inserted as top-level nodes.
    js = """
      $component((ctx) => { window.__log.push(ctx.id); });
    """
    base = _serve_fragment(serve_live, js)
    page.goto(base + "/")

    page.evaluate(
        """
        () => fetch('/fragment')
          .then((r) => r.text())
          .then((html) => {
            document.getElementById('target').innerHTML = '<div class="wrapper">' + html + '</div>';
          })
        """
    )
    page.wait_for_function("window.__log.length === 1")
    assert page.evaluate("window.__log.length") == 1


def test_processed_manifest_is_not_reprocessed_when_reobserved(page: Any, serve_live: Any) -> None:
    # Moving an already-processed manifest tag makes the observer see it
    # again; non-cloneable node identity must keep it from running twice. The
    # data-citry-processed attribute remains a diagnostic selector only.
    js = """
      $component(() => { window.__log.push("call"); });
    """
    base = _serve_fragment(serve_live, js)
    page.goto(base + "/")

    page.evaluate("() => window.__insertFragment()")
    page.wait_for_function("window.__log.length === 1")

    # Re-append the processed manifest tag (a removal plus an insertion, so
    # the observer reports it as an added node again).
    page.evaluate(
        """
        () => {
          const tag = document.querySelector('script[data-citry][data-citry-processed]');
          document.body.appendChild(tag);
        }
        """
    )
    # The observer callback for the move runs as a microtask of the evaluate
    # above, so it has finished before this next evaluate task runs: had the
    # stamp been ignored, the duplicate "call" would already be in the log.
    assert page.evaluate("window.__log") == ["call"]

    # A fresh graph-independent call manifest still processes. Re-inserting
    # the same concrete graph fragment is rejected by A2 and has its own test.
    page.evaluate("() => window.__insertFreshCallManifest()")
    page.wait_for_function("window.__log.length === 2")
    assert page.evaluate("window.__log") == ["call", "call"]


def test_parser_created_manifest_waits_for_its_json_text(page: Any, serve_live: Any) -> None:
    # While a document is streaming, the HTML parser may yield a mutation
    # record for the script start tag before its JSON text node has landed.
    # The runtime must leave that transient empty element for the final
    # DOMContentLoaded drain instead of consuming it as invalid JSON.
    c = Citry()
    c.set_mounted_prefix("/citry")
    page_html = """
      <html>
        <head><script src="/citry/citry.js"></script></head>
        <body>
          <script type="application/json" data-citry>{}</script>
          <output id="after-parser">ready</output>
        </body>
      </html>
    """
    base = serve_live(c, page_html, "")
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )

    page.goto(base + "/", wait_until="networkidle")

    assert page.locator("#after-parser").text_content() == "ready"
    manifest = page.locator("script[data-citry]")
    assert manifest.get_attribute("data-citry-processed") == ""
    assert errors == []


def test_invalid_manifest_json_does_not_break_later_manifests(page: Any, serve_live: Any) -> None:
    # A malformed manifest is logged as an error and dropped; manifests
    # inserted afterwards still process normally.
    js = """
      $component(() => { window.__log.push("call"); });
    """
    base = _serve_fragment(serve_live, js)
    page.goto(base + "/")

    with page.expect_console_message(
        lambda msg: msg.type == "error" and "[Citry] failed to process dependency manifest" in msg.text
    ):
        page.evaluate(
            """
            () => {
              document.getElementById('target').innerHTML =
                '<script type="application/json" data-citry>not json</script>';
            }
            """
        )

    page.evaluate("() => window.__insertFragment()")
    page.wait_for_function("window.__log.length === 1")
    assert page.evaluate("window.__log") == ["call"]


# ----- The decorateContext hook -----


def test_decorator_adds_member_in_order_and_stops_after_unregister(page: Any, serve_live: Any) -> None:
    # Two decorators prove registration order ("a" then "+b"); unregistering
    # the second one stops its contribution on the next flush.
    setup = """
      Citry.manager.decorateContext((ctx) => { ctx.tag = "a"; });
      window.__unregB = Citry.manager.decorateContext((ctx) => { ctx.tag += "b"; });
    """
    js = """
      $component((ctx) => { window.__log.push("cb:" + ctx.tag); });
    """
    base = _serve_fragment(serve_live, js, setup)
    page.goto(base + "/")

    page.evaluate("() => window.__insertFragment()")
    page.wait_for_function("window.__log.length === 1")
    assert page.evaluate("window.__log") == ["cb:ab"]

    page.evaluate("() => window.__unregB()")
    # A second unregister call must be a no-op, not remove another decorator.
    page.evaluate("() => window.__unregB()")
    page.evaluate("() => window.__refireFragmentCall()")
    page.wait_for_function("window.__log.length === 2")
    assert page.evaluate("window.__log") == ["cb:ab", "cb:a"]


def test_decorator_unregistering_itself_during_flush_does_not_skip_next(page: Any, serve_live: Any) -> None:
    # A run-once decorator that unregisters itself while it runs must not
    # shift the registration list under the flush: the next decorator still
    # runs on the same payload, and only the unregistered one is gone on the
    # next flush.
    setup = """
      var unregA = Citry.manager.decorateContext((ctx) => {
        ctx.tag = "a";
        unregA();
      });
      Citry.manager.decorateContext((ctx) => { ctx.tag = (ctx.tag || "") + "b"; });
    """
    js = """
      $component((ctx) => { window.__log.push("cb:" + ctx.tag); });
    """
    base = _serve_fragment(serve_live, js, setup)
    page.goto(base + "/")

    page.evaluate("() => window.__insertFragment()")
    page.wait_for_function("window.__log.length === 1")
    assert page.evaluate("window.__log") == ["cb:ab"]

    page.evaluate("() => window.__refireFragmentCall()")
    page.wait_for_function("window.__log.length === 2")
    assert page.evaluate("window.__log") == ["cb:ab", "cb:b"]


def test_decorator_return_value_does_not_replace_payload(page: Any, serve_live: Any) -> None:
    # The contract is mutate-in-place: a decorator that returns a whole new
    # object changes nothing; callbacks still get the original payload
    # (correct id/els) plus the mutation, and none of the returned members.
    setup = """
      Citry.manager.decorateContext((ctx) => {
        ctx.added = "kept";
        return { id: "hijacked-id", els: [], data: null, hijacked: true };
      });
    """
    js = """
      $component((ctx) => {
        window.__log.push({
          added: ctx.added,
          hijackLeaked: "hijacked" in ctx,
          idMatchesEl: ctx.els.length === 1 && ctx.els[0].hasAttribute("data-cid-" + ctx.id),
        });
      });
    """
    base = _serve_fragment(serve_live, js, setup)
    page.goto(base + "/")

    page.evaluate("() => window.__insertFragment()")
    page.wait_for_function("window.__log.length === 1")
    assert page.evaluate("window.__log") == [{"added": "kept", "hijackLeaked": False, "idMatchesEl": True}]


def test_throwing_decorator_does_not_break_flush(page: Any, serve_live: Any) -> None:
    # The first decorator throws; the error is logged, the second decorator
    # and the callbacks still run.
    console_errors: list[str] = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    setup = """
      Citry.manager.decorateContext(() => { throw new Error("decorator boom"); });
      Citry.manager.decorateContext((ctx) => { ctx.after = "ran"; });
    """
    js = """
      $component((ctx) => { window.__log.push("cb:" + ctx.after); });
    """
    base = _serve_fragment(serve_live, js, setup)
    page.goto(base + "/")

    page.evaluate("() => window.__insertFragment()")
    page.wait_for_function("window.__log.length === 1")
    assert page.evaluate("window.__log") == ["cb:ran"]
    assert any("[Citry] context decorator failed" in text for text in console_errors)


# ----- Callback teardown -----


def test_callback_cleanup_runs_once_before_each_refire(page: Any, serve_live: Any) -> None:
    # A callback's returned cleanup runs exactly once, before the callback
    # fires again for the same instance id, and a fresh cleanup is stored on
    # every run (so the third insert tears down the second run's cleanup).
    js = """
      $component(() => {
        window.__log.push("call");
        return () => { window.__log.push("cleanup"); };
      });
    """
    base = _serve_fragment(serve_live, js)
    page.goto(base + "/")

    page.evaluate("() => window.__insertFragment()")
    page.wait_for_function("window.__log.length === 1")
    assert page.evaluate("window.__log") == ["call"]

    page.evaluate("() => window.__refireFragmentCall()")
    page.wait_for_function("window.__log.length === 3")
    assert page.evaluate("window.__log") == ["call", "cleanup", "call"]

    page.evaluate("() => window.__refireFragmentCall()")
    page.wait_for_function("window.__log.length === 5")
    assert page.evaluate("window.__log") == ["call", "cleanup", "call", "cleanup", "call"]


def test_callback_cleanup_is_scoped_per_instance_not_per_class(page: Any, serve_live: Any) -> None:
    # Cleanups are stored per instance id, not per class: with two instances
    # of one component on the page, calling c14b must not run c14a's cleanup
    # (a re-render of one sibling would otherwise tear down the live other),
    # and c14a's cleanup still runs exactly once before c14a's own re-fire.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          const log = [];
          document.body.insertAdjacentHTML(
            "beforeend",
            '<div data-cid-c14a></div><div data-cid-c14b></div>'
          );
          m.registerComponent("scoped_cls", (ctx) => {
            log.push("call:" + ctx.id);
            return () => { log.push("cleanup:" + ctx.id); };
          });
          m.callComponent("scoped_cls", "c14a", null);
          m.callComponent("scoped_cls", "c14b", null);
          m.callComponent("scoped_cls", "c14a", null);
          return log;
        }
        """
    )
    assert result == ["call:c14a", "call:c14b", "cleanup:c14a", "call:c14a"]


def test_callback_non_function_return_is_not_treated_as_cleanup(page: Any, serve_live: Any) -> None:
    # Only a function return is stored as a cleanup. An async callback is the
    # natural way to return something else: it implicitly returns a Promise,
    # which the runtime must ignore. If the runtime stored it, the re-insert
    # would invoke it as a cleanup and log a "[Citry] component cleanup"
    # error, so the test asserts both re-fires happen and no such error
    # appears.
    console_errors: list[str] = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    js = """
      $component(async () => {
        window.__log.push("call");
      });
    """
    base = _serve_fragment(serve_live, js)
    page.goto(base + "/")

    page.evaluate("() => window.__insertFragment()")
    page.wait_for_function("window.__log.length === 1")
    page.evaluate("() => window.__refireFragmentCall()")
    page.wait_for_function("window.__log.length === 2")

    assert page.evaluate("window.__log") == ["call", "call"]
    assert not [text for text in console_errors if "[Citry] component cleanup for" in text]


def test_throwing_cleanup_does_not_break_flush(page: Any, serve_live: Any) -> None:
    # A cleanup that throws on re-fire is logged, and the class's single
    # callback still runs again.
    console_errors: list[str] = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    js = """
      $component(() => {
        window.__log.push("call");
        return () => { throw new Error("cleanup boom"); };
      });
    """
    base = _serve_fragment(serve_live, js)
    page.goto(base + "/")

    page.evaluate("() => window.__insertFragment()")
    page.wait_for_function("window.__log.length === 1")
    assert page.evaluate("window.__log") == ["call"]

    page.evaluate("() => window.__refireFragmentCall()")
    page.wait_for_function("window.__log.length === 2")
    assert page.evaluate("window.__log") == ["call", "call"]
    assert any("[Citry] component cleanup for" in text for text in console_errors)


# ----- The full fragment pipeline -----


def test_rerender_delivers_fresh_data_and_new_instance_id(page: Any, serve_live: Any) -> None:
    # Re-rendering a component (not re-inserting the same HTML) produces a
    # new instance id and, when js_data changed, a new variables script; the
    # callback for the new instance receives the fresh values and the fresh
    # element, not anything cached from the previous render.
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Frag(Component):
        citry = c
        template = """
          <div class="frag">frag</div>
        """
        js = """
          $component(({ id, els, data }) => {
            window.__log.push({
              id,
              n: data.n,
              connected: els[0].isConnected,
              marked: els[0].hasAttribute("data-cid-" + id),
            });
          });
        """
        current_n = 0

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, int]:
            return {"n": type(self).current_n}

    Frag.current_n = 1
    html1 = Frag().render().serialize(deps_strategy="fragment")
    Frag.current_n = 2
    html2 = Frag().render().serialize(deps_strategy="fragment")

    base = serve_live(c, _page(), html1)
    page.goto(base + "/")

    insert = "(html) => { document.getElementById('target').innerHTML = html; }"
    page.evaluate(insert, html1)
    page.wait_for_function("window.__log.length === 1")
    page.evaluate(insert, html2)
    page.wait_for_function("window.__log.length === 2")

    log = page.evaluate("window.__log")
    assert [entry["n"] for entry in log] == [1, 2]
    assert log[0]["id"] != log[1]["id"]
    assert all(entry["connected"] and entry["marked"] for entry in log)


def test_sibling_instances_get_one_call_each_in_document_order(page: Any, serve_live: Any) -> None:
    # Two instances of one component in a single fragment: identical js_data
    # collapses to one variables script, but each instance still gets its own
    # call, with its own elements, in document order.
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Item(Component):
        citry = c
        template = """
          <div class="item">item</div>
        """
        js = """
          $component(({ id, els, data }) => {
            window.__log.push({
              id,
              n: data.n,
              pos: Array.prototype.indexOf.call(document.querySelectorAll(".item"), els[0]),
            });
          });
        """

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, int]:
            return {"n": 7}

    class Pair(Component):
        citry = c
        template = """
          <c-item />
          <c-item />
        """

    fragment_html = Pair().render().serialize(deps_strategy="fragment")
    base = serve_live(c, _page(), fragment_html)
    page.goto(base + "/")

    page.evaluate("() => window.__insertFragment()")
    page.wait_for_function("window.__log.length === 2")

    log = page.evaluate("window.__log")
    assert [entry["n"] for entry in log] == [7, 7]
    assert [entry["pos"] for entry in log] == [0, 1]
    assert log[0]["id"] != log[1]["id"]


def test_fragment_bootstraps_runtime_on_page_without_it(page: Any, serve_live: Any) -> None:
    # A fragment inserted into a page that never loaded the runtime: once the
    # fragment's script tags execute (as an HTMX-style swapper does; plain
    # innerHTML never runs scripts), the pre-loader injects the runtime, and
    # the runtime's startup pass processes the manifest that is already in
    # the document, fetches the component's scripts, and runs its callback.
    bare_page = """
    <html>
      <head></head>
      <body>
        <div id="target"></div>
        <script>
          window.__insertFragmentAndRunScripts = () =>
            fetch('/fragment')
              .then((r) => r.text())
              .then((html) => {
                const target = document.getElementById('target');
                target.innerHTML = html;
                target.querySelectorAll('script').forEach((old) => {
                  const fresh = document.createElement('script');
                  for (const attr of old.attributes) fresh.setAttribute(attr.name, attr.value);
                  fresh.textContent = old.textContent;
                  old.replaceWith(fresh);
                });
              });
        </script>
      </body>
    </html>
    """
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Frag(Component):
        citry = c
        template = """
          <div class="frag">frag</div>
        """
        js = """
          $component(({ els, data }) => { els[0].setAttribute('data-n', String(data.n)); });
        """

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, int]:
            return {"n": 42}

    fragment_html = Frag().render().serialize(deps_strategy="fragment")
    base = serve_live(c, bare_page, fragment_html)
    page.goto(base + "/")

    assert page.evaluate("() => window.Citry === undefined")
    page.evaluate("() => window.__insertFragmentAndRunScripts()")
    page.wait_for_function("document.querySelector('.frag')?.dataset.n === '42'")
    assert page.evaluate("() => !!window.Citry.manager")


# ----- Instance lifecycle: teardown on removal and Component.css cleanup -----


def test_cleanup_runs_when_instance_element_is_removed(page: Any, serve_live: Any) -> None:
    # An instance whose callback returned a cleanup has that cleanup run when
    # its last data-cid element leaves the DOM, even though no new call for the
    # id ever arrives (the case a re-render under a fresh id creates: the old
    # id's call never recurs). The removal sweep runs on the microtask after
    # the DOM mutation, so the log is read after that has settled.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    page.evaluate(
        """
        () => {
          const m = Citry.manager;
          document.body.insertAdjacentHTML("beforeend", '<div id="rm" data-cid-RM1></div>');
          m.registerComponent("removal_cls", (ctx) => {
            window.__log.push("call:" + ctx.id);
            return () => { window.__log.push("cleanup:" + ctx.id); };
          });
          m.callComponent("removal_cls", "RM1", null);
        }
        """
    )
    assert page.evaluate("window.__log") == ["call:RM1"]

    # Remove the instance's only element; the sweep retires the id and runs its
    # cleanup exactly once.
    page.evaluate("() => document.getElementById('rm').remove()")
    page.wait_for_function("window.__log.length === 2")
    assert page.evaluate("window.__log") == ["call:RM1", "cleanup:RM1"]

    # A later sweep (from an unrelated mutation) must not run the cleanup a
    # second time: the id was retired and forgotten.
    page.evaluate("() => document.body.insertAdjacentHTML('beforeend', '<div data-cid-UNREL></div>')")
    page.evaluate("() => new Promise((r) => setTimeout(r, 0))")
    assert page.evaluate("window.__log") == ["call:RM1", "cleanup:RM1"]


def test_cleanup_runs_when_instance_id_is_swapped_in_place(page: Any, serve_live: Any) -> None:
    # A persisting node whose data-cid-<id> is swapped for a new id (what an
    # in-place morph patch does) retires the OLD id exactly once via its
    # cleanup. No node is removed and no new call is fired, so the only signal
    # that the old id left is the attribute change: the sweep must watch
    # attributes, not only node removals.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    page.evaluate(
        """
        () => {
          const m = Citry.manager;
          document.body.insertAdjacentHTML("beforeend", '<div id="sw" data-cid-SW1></div>');
          m.registerComponent("swap_cls", (ctx) => {
            window.__log.push("call:" + ctx.id);
            return () => { window.__log.push("cleanup:" + ctx.id); };
          });
          m.callComponent("swap_cls", "SW1", null);
        }
        """
    )
    assert page.evaluate("window.__log") == ["call:SW1"]

    page.evaluate(
        """
        () => {
          const node = document.getElementById("sw");
          node.removeAttribute("data-cid-SW1");
          node.setAttribute("data-cid-SW2", "");
        }
        """
    )
    page.wait_for_function("window.__log.length === 2")
    assert page.evaluate("window.__log") == ["call:SW1", "cleanup:SW1"]


def test_reentrant_flush_does_not_double_run_the_in_flight_call(page: Any, serve_live: Any) -> None:
    # A callback that synchronously triggers another flush (here by registering
    # a second component) must not make the in-flight call run again: its
    # callback and its cleanup each run exactly once, and the nested flush does
    # not recurse. The queue is snapshotted and cleared before iterating, so the
    # nested flush sees a fresh queue, never the call still in flight.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        () => {
          const m = Citry.manager;
          const log = [];
          let fires = 0;
          document.body.insertAdjacentHTML("beforeend", '<div data-cid-RE1></div>');
          m.registerComponent("reentry_cls", () => {
            fires += 1;
            log.push("cb");
            if (fires === 1) {
              // Trigger a nested flush while this call is still in flight.
              // Registering a different class adds no call; it just runs
              // flushCalls again.
              m.registerComponent("nudge_cls", () => {});
            }
            return () => { log.push("cleanup"); };
          });
          m.callComponent("reentry_cls", "RE1", null);
          const afterCall = log.slice();
          // Re-fire RE1 to flush whatever cleanup(s) were stored for it.
          m.callComponent("reentry_cls", "RE1", null);
          return { afterCall, afterRefire: log.slice() };
        }
        """
    )
    assert result == {"afterCall": ["cb"], "afterRefire": ["cb", "cleanup", "cb"]}


def test_component_css_dropped_only_when_last_instance_of_class_leaves(page: Any, serve_live: Any) -> None:
    # Two instances of one class share its data-citry-css-class sheet. Removing
    # one leaves the sheet (a live instance still needs it); removing the last
    # drops it, on the deferred collection tick. A second class's sheet, still
    # in use, is never touched. The test hand-builds the tagged sheets WP10 will
    # emit.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    page.evaluate(
        """
        () => {
          const m = Citry.manager;
          document.head.insertAdjacentHTML(
            "beforeend",
            '<style data-citry-css-class="GcCls">.gc{}</style>' +
            '<style data-citry-css-class="KeepCls">.keep{}</style>'
          );
          document.body.insertAdjacentHTML(
            "beforeend",
            '<div id="g1" data-cid-G1></div><div id="g2" data-cid-G2></div>' +
            '<div id="k1" data-cid-K1></div>'
          );
          m.registerComponent("GcCls", () => {});
          m.registerComponent("KeepCls", () => {});
          m.callComponent("GcCls", "G1", null);
          m.callComponent("GcCls", "G2", null);
          m.callComponent("KeepCls", "K1", null);
        }
        """
    )
    present = "(cls) => !!document.querySelector('[data-citry-css-class=' + cls + ']')"
    assert page.evaluate(present, "GcCls") is True
    assert page.evaluate(present, "KeepCls") is True

    # Remove one of the two GcCls instances: the class still has G2 live, so its
    # sheet stays, past the deferred tick as well.
    page.evaluate("() => document.getElementById('g1').remove()")
    page.evaluate("() => new Promise((r) => setTimeout(r, 0))")
    assert page.evaluate(present, "GcCls") is True

    # Remove the last GcCls instance: the deferred collection drops its sheet,
    # while KeepCls (still live via K1) keeps its own.
    page.evaluate("() => document.getElementById('g2').remove()")
    page.wait_for_function("!document.querySelector('[data-citry-css-class=GcCls]')")
    assert page.evaluate(present, "GcCls") is False
    assert page.evaluate(present, "KeepCls") is True


def test_collected_component_css_url_can_be_loaded_again(page: Any, serve_live: Any) -> None:
    # Class CSS collection removes both the link and its loaded-URL marker.
    # A later instance of the same class can therefore fetch and apply the
    # stylesheet again instead of being left permanently unstyled.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        async () => {
          const m = Citry.manager;
          const url = "data:text/css,.citry-reload%7Bcolor%3Argb(7%2C8%2C9)%7D";
          const descriptor = {
            tag: "link",
            attrs: {
              rel: "stylesheet",
              href: url,
              "data-citry-css-class": "Reloadable",
            },
          };
          const count = () =>
            Array.from(document.head.querySelectorAll("link[href]")).filter(
              (element) => element.getAttribute("href") === url,
            ).length;

          await m.loadCss(descriptor);
          document.body.insertAdjacentHTML(
            "beforeend",
            '<div id="reload-one" class="citry-reload" data-cid-RL1>one</div>',
          );
          m.registerComponent("Reloadable", () => {});
          m.callComponent("Reloadable", "RL1", null);
          const firstColor = getComputedStyle(document.getElementById("reload-one")).color;
          document.getElementById("reload-one").remove();
          await new Promise((resolve) => setTimeout(resolve, 0));
          await new Promise((resolve) => setTimeout(resolve, 0));
          const afterCollection = {
            links: count(),
            loaded: m.isScriptLoaded("css", url),
          };

          await m.loadCss(descriptor);
          document.body.insertAdjacentHTML(
            "beforeend",
            '<div id="reload-two" class="citry-reload" data-cid-RL2>two</div>',
          );
          m.callComponent("Reloadable", "RL2", null);
          return {
            firstColor,
            afterCollection,
            reloadedLinks: count(),
            reloaded: m.isScriptLoaded("css", url),
            secondColor: getComputedStyle(document.getElementById("reload-two")).color,
          };
        }
        """
    )
    assert result == {
        "firstColor": "rgb(7, 8, 9)",
        "afterCollection": {"links": 0, "loaded": False},
        "reloadedLinks": 1,
        "reloaded": True,
        "secondColor": "rgb(7, 8, 9)",
    }


def test_component_css_survives_a_same_class_rerender_in_place(page: Any, serve_live: Any) -> None:
    # THE deferred-collection test (spike finding F-CI-4). A solo instance of a
    # class re-renders in place: its old id retires (the class momentarily looks
    # empty) and only then does the fresh same-class id register. The collection
    # must be deferred and re-checked so the fresh arrival cancels it; an inline
    # collection would drop the sheet the instant the old id retired, and a URL
    # sheet would then never come back.
    base = _serve_runtime_page(serve_live)
    page.goto(base + "/")

    result = page.evaluate(
        """
        async () => {
          const m = Citry.manager;
          const present = () => !!document.querySelector('[data-citry-css-class=Solo]');
          document.head.insertAdjacentHTML("beforeend", '<style data-citry-css-class="Solo">.s{}</style>');
          document.body.insertAdjacentHTML("beforeend", '<div id="solo" data-cid-S1></div>');
          m.registerComponent("Solo", () => {});
          m.callComponent("Solo", "S1", null);          // S1 live, class count 1

          const node = document.getElementById("solo");
          // Re-render in place: retire the old id first...
          node.removeAttribute("data-cid-S1");
          node.setAttribute("data-cid-S2", "");
          // ...let the removal sweep run now, while the fresh id is NOT yet
          // registered, so the class looks empty here. An INLINE collection
          // would drop the sheet at this point.
          await Promise.resolve();
          const afterSweep = present();
          // ...then the fresh same-class id registers, in the same tick, before
          // the deferred collection fires: this must cancel it.
          m.callComponent("Solo", "S2", null);          // S2 live, class count 1
          // Let the deferred collection task run and re-check the count.
          await new Promise((r) => setTimeout(r, 0));
          await new Promise((r) => setTimeout(r, 0));
          const afterDefer = present();
          return { afterSweep, afterDefer };
        }
        """
    )
    assert result == {"afterSweep": True, "afterDefer": True}
