"""Three-browser A2 ownership graph reconstruction and failure behavior."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from typing import TYPE_CHECKING, Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry._protocol.client_graph import canonical_json

if TYPE_CHECKING:
    from collections.abc import Callable

pytestmark = pytest.mark.e2e

_GRAPH_TAG = re.compile(r'(<script type="application/json" data-citry-graph>)(.*?)(</script>)', re.DOTALL)
_EVENTS_TAG = re.compile(r'(<script type="application/json" data-citry-events>)(.*?)(</script>)', re.DOTALL)
_DEPS_TAG = re.compile(r'(<script type="application/json" data-citry>)(.*?)(</script>)', re.DOTALL)


def _mutate_graph(html: str, mutate: Callable[[dict[str, Any]], None]) -> str:
    match = _GRAPH_TAG.search(html)
    assert match is not None
    manifest = json.loads(match.group(2))
    old_revision = manifest["revision"]
    mutate(manifest)
    unsigned = {key: value for key, value in manifest.items() if key != "revision"}
    canonical = canonical_json(unsigned).encode("utf8")
    manifest["revision"] = hashlib.sha256(canonical).hexdigest()
    replacement = f"{match.group(1)}{json.dumps(manifest)}{match.group(3)}"
    return f"{html[: match.start()]}{replacement}{html[match.end() :]}".replace(
        old_revision,
        manifest["revision"],
    )


def _mutate_events(html: str, mutate: Callable[[dict[str, Any]], None]) -> str:
    match = _EVENTS_TAG.search(html)
    assert match is not None
    manifest = json.loads(match.group(2))
    mutate(manifest)
    replacement = f"{match.group(1)}{json.dumps(manifest)}{match.group(3)}"
    return f"{html[: match.start()]}{replacement}{html[match.end() :]}"


def _mutate_dependencies(html: str, mutate: Callable[[dict[str, Any]], None]) -> str:
    match = _DEPS_TAG.search(html)
    assert match is not None
    manifest = json.loads(match.group(2))
    mutate(manifest)
    replacement = f"{match.group(1)}{json.dumps(manifest)}{match.group(3)}"
    return f"{html[: match.start()]}{replacement}{html[match.end() :]}"


def test_initial_document_commits_before_component_callback(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c
        js = """
          $component(({ els }) => {
            document.body.dataset.graphReadyAtInit = String(Citry.manager.ownership.revisions().length);
            document.body.dataset.rootCount = String(els.length);
          });
        """
        template = "rootless tail"

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("document.body.dataset.graphReadyAtInit === '1'")

    result = page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          return {
            revisions: Citry.manager.ownership.revisions().length,
            graphs: graph.graphs.length,
            componentInstances: graph.graphs[0].componentInstances.length,
            rootCount: document.body.dataset.rootCount,
          };
        }
        """
    )
    assert result == {"revisions": 1, "graphs": 1, "componentInstances": 1, "rootCount": "0"}


def test_fragment_inserted_while_parser_runs_commits_before_alpine_start(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Fragment(Component):
        citry = c
        js = "$component(() => { window.__prestartFragmentCallback = true; })"
        template = """
          <main
            x-data="{ local: 'kept' }"
            x-init="
              window.__graphCountAtInit = Citry.manager.ownership.revisions().length;
              window.__eventsReadyAtInit =
                !!Citry.events._internal.getAnchor($el.getAttribute('data-cid')) &&
                local === 'kept' && typeof $state === 'object'
            "
          >fragment</main>
        """

        class Events:
            def save(self) -> None:
                pass

    fragment = Fragment().render().serialize(deps_strategy="fragment")
    encoded = base64.b64encode(fragment.encode()).decode()
    page_html = f"""
      <html>
        <head>
          <script src="/citry/citry.js"></script>
          <script src="/citry/ext/events/runtime.js"></script>
        </head>
        <body>
          <div id="target"></div>
          <script>
            window.__fragmentInsertReadyState = document.readyState;
            const template = document.createElement("template");
            template.innerHTML = atob("{encoded}");
            document.getElementById("target").append(template.content);
          </script>
        </body>
      </html>
    """
    base = serve_live(c, page_html, "")
    page.goto(base + "/")
    page.wait_for_function(
        "window.__prestartFragmentCallback && window.__graphCountAtInit !== undefined && "
        "window.__eventsReadyAtInit === true"
    )

    result = page.evaluate(
        """
        () => ({
          insertedWhileLoading: window.__fragmentInsertReadyState === "loading",
          graphCountAtInit: window.__graphCountAtInit,
          eventsReadyAtInit: window.__eventsReadyAtInit,
          committedGraphs: Citry.manager.ownership.revisions().length,
          starts: Citry.alpine._debug().hooks.starts,
        })
        """
    )
    assert result == {
        "insertedWhileLoading": True,
        "graphCountAtInit": 1,
        "eventsReadyAtInit": True,
        "committedGraphs": 1,
        "starts": 1,
    }


def test_general_alpine_broker_and_typed_route_work_without_events(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c
        js = """
          Citry.alpine.beforeStart((Alpine) => {
            Alpine.magic("a3Probe", () => "broker-ready");
          });
          $component(({ graph }) => {
            window.__a3Route = graph;
          });
        """
        template = '<main x-data x-text="$a3Probe">waiting</main>'

    html = Page().render().serialize()
    assert "data-citry-events" not in html
    assert 'data-citry-root=""' in html
    assert '<script src="/citry/ext/events/runtime.js"></script>' in html

    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_function("window.__a3Route && document.querySelector('main').textContent === 'broker-ready'")

    result = page.evaluate(
        """
        () => {
          const revision = window.__a3Route.revision;
          const committed = Citry.manager.ownership.get(revision);
          const instance = committed.registry.renderIds.get(window.__a3Route.instance.renderId);
          let lateError = "";
          try {
            Citry.alpine.beforeStart(() => {});
          } catch (error) {
            lateError = String(error.message || error);
          }
          return {
            sameInstance: instance === window.__a3Route.instance,
            sameAnchor: instance.anchor === window.__a3Route.anchor,
            sameLogical: instance.logicalInstance === window.__a3Route.logicalInstance,
            indexes: {
              graphs: committed.registry.graphs.size,
              componentInstances: committed.registry.componentInstances.size,
              sourceLocations: committed.registry.sourceLocations.size,
              anchors: committed.registry.anchors.size,
            },
            broker: Citry.alpine._debug(),
            lateError,
          };
        }
        """
    )
    assert result["sameInstance"] is True
    assert result["sameAnchor"] is True
    assert result["sameLogical"] is True
    assert result["indexes"] == {
        "graphs": 1,
        "componentInstances": 1,
        "sourceLocations": 0,
        "anchors": 1,
    }
    assert result["broker"]["started"] is True
    assert result["broker"]["hooks"] == {"installs": 1, "roots": 1, "init": 1, "morph": 0, "starts": 1}
    assert "beforeStart(callback) was called after Citry-owned startup" in result["lateError"]


def test_unmounted_document_inlines_alpine_and_runs_graph_callback(page: Any, serve_live: Any) -> None:
    c = Citry()

    class Page(Component):
        citry = c
        js = "$component(() => { window.__inlineA3Callback = true; })"
        template = "<main x-data=\"{ ready: true }\" x-text=\"ready ? 'inline-ready' : 'waiting'\"></main>"

    html = Page().render().serialize()
    assert '<script src="/citry/ext/events/runtime.js"' not in html
    assert "Citry events client runtime. GENERATED FILE" in html

    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_function("window.__inlineA3Callback && Citry.alpine._isStarted()")
    assert page.locator("main").inner_text() == "inline-ready"


def test_events_anchor_is_a_sidecar_of_the_general_anchor(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c
        template = "<button>save</button>"

        class Events:
            def save(self):
                return None

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("Citry.events && Citry.events._internal.anchors.size === 1")

    result = page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const id = document.querySelector("button").getAttribute("data-cid");
          const route = Citry.manager.ownership.forRender(revision, id);
          const events = Citry.events._internal.getAnchor(id);
          return {
            routeExists: !!route,
            generalPointsToEvents: route.anchor.events === events,
            eventsPointsToGeneral: events.clientAnchor === route.anchor,
          };
        }
        """
    )
    assert result == {
        "routeExists": True,
        "generalPointsToEvents": True,
        "eventsPointsToGeneral": True,
    }


def test_runtime_dynamic_target_commits_without_a_wrapper_identity(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Target(Component):
        citry = c
        js = """
          $component(() => {});
        """
        template = """
          <button>target</button>
        """

    class Page(Component):
        citry = c
        js = """
          $component(() => {
            const revision = Citry.manager.ownership.revisions()[0];
            const graph = Citry.manager.ownership.get(revision).graphs[0];
            document.body.dataset.instanceCount = String(graph.componentInstances.length);
            document.body.dataset.hasTransparent = String(
              graph.componentInstances.some((item) => item.transparent),
            );
          });
        """
        template = """
          <c-component c-is="target" $c-props="{value: 1}" />
        """

        def template_data(self, kwargs, slots):
            return {"target": Target}

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("document.body.dataset.instanceCount === '2'")

    assert page.locator("button").inner_text() == "target"
    assert page.evaluate("document.body.dataset.hasTransparent") == "false"


def test_parser_document_waits_for_a_trailing_outer_cap(page: Any, serve_live: Any) -> None:
    c = Citry()

    class Page(Component):
        citry = c
        js = """
          $component(() => {
            document.body.dataset.trailingCapReady = String(Citry.manager.ownership.revisions().length);
          });
        """
        template = "<html><head></head><body><main>page</main><c-js /></body></html>"

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("document.body.dataset.trailingCapReady === '1'")

    assert page.locator("main").inner_text() == "page"


def test_malformed_manifest_commits_nothing_and_keeps_prior_revision(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c
        js = "$component(() => { window.__pageRuns = (window.__pageRuns || 0) + 1; })"
        template = "<main>ok</main>"

    base = serve_live(c, Page().render().serialize(), "")
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    page.goto(base + "/")
    page.wait_for_function("Citry.manager.ownership.revisions().length === 1")

    result = page.evaluate(
        """
        async () => {
          const prior = Citry.manager.ownership.revisions()[0];
          const original = document.querySelector('[data-citry-graph]');
          const broken = JSON.parse(original.textContent);
          broken.revision = "0".repeat(64);
          const waiting = Citry.manager.ownership.whenReady(broken.revision).then(
            () => false,
            () => true,
          );
          const dependency = JSON.parse(document.querySelector('script[data-citry]').textContent);
          dependency.graph = broken.revision;
          const dependencyTag = document.createElement("script");
          dependencyTag.type = "application/json";
          dependencyTag.dataset.citry = "";
          dependencyTag.textContent = JSON.stringify(dependency);
          document.body.append(dependencyTag);
          const tag = document.createElement("script");
          tag.type = "application/json";
          tag.dataset.citryGraph = "";
          tag.textContent = JSON.stringify(broken);
          document.body.append(tag);
          const waiterRejected = await waiting;
          await new Promise((resolve) => setTimeout(resolve, 20));
          return {
            priorStillPresent: Citry.manager.ownership.has(prior),
            brokenAbsent: !Citry.manager.ownership.has(broken.revision),
            revisions: Citry.manager.ownership.revisions().length,
            waiterRejected,
            pageRuns: window.__pageRuns,
          };
        }
        """
    )
    assert result == {
        "priorStillPresent": True,
        "brokenAbsent": True,
        "revisions": 1,
        "waiterRejected": True,
        "pageRuns": 1,
    }
    assert any("failed to process ownership graph manifest" in message for message in messages)


def test_resigned_instance_invocation_mismatch_is_rejected_before_callback(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        template = "<span>child</span>"

    class Page(Component):
        citry = c
        js = "$component(() => { window.__relationshipRuns = (window.__relationshipRuns || 0) + 1; })"
        template = "<c-child />"

    def corrupt(manifest: dict[str, Any]) -> None:
        graph = manifest["graphs"][0]
        invocation_id = graph["nestedComponents"][0]["invocationId"]
        graph["componentInstances"][0]["invocationId"] = invocation_id
        graph["componentInstances"][1]["invocationId"] = None

    html = _mutate_graph(Page().render().serialize(), corrupt)
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_timeout(100)

    assert page.evaluate("Citry.manager.ownership.revisions().length") == 0
    assert page.evaluate("window.__relationshipRuns || 0") == 0
    assert any("failed to process ownership graph manifest" in message for message in messages)


def test_resigned_region_cycle_is_rejected_before_callback(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Shell(Component):
        citry = c
        template = "<section><c-slot /></section>"

    class Page(Component):
        citry = c
        js = "$component(() => { window.__regionRuns = (window.__regionRuns || 0) + 1; })"
        template = "<c-shell><span>fill</span></c-shell>"

    def corrupt(manifest: dict[str, Any]) -> None:
        region = manifest["graphs"][0]["slotRegions"][0]
        region["parentRegionId"] = region["regionId"]

    html = _mutate_graph(Page().render().serialize(), corrupt)
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_timeout(100)

    assert page.evaluate("Citry.manager.ownership.revisions().length") == 0
    assert page.evaluate("window.__regionRuns || 0") == 0
    assert any("failed to process ownership graph manifest" in message for message in messages)


def test_resigned_logical_parent_cycle_is_rejected_before_callback(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        template = "<span>child</span>"

    class Page(Component):
        citry = c
        js = "$component(() => { window.__logicalCycleRuns = (window.__logicalCycleRuns || 0) + 1; })"
        template = "<c-child />"

    def corrupt(manifest: dict[str, Any]) -> None:
        child = manifest["graphs"][0]["componentInstances"][-1]
        child["parentRenderId"] = child["renderId"]

    html = _mutate_graph(Page().render().serialize(), corrupt)
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_timeout(100)

    assert page.evaluate("Citry.manager.ownership.revisions().length") == 0
    assert page.evaluate("window.__logicalCycleRuns || 0") == 0
    assert any("failed to process ownership graph manifest" in message for message in messages)


def test_malformed_later_events_instance_is_atomic_and_blocks_callbacks(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = "$component(() => { window.__childEventRuns = (window.__childEventRuns || 0) + 1; })"
        template = "<span>child</span>"

        class Events:
            def child_event(self):
                return None

    class Page(Component):
        citry = c
        js = "$component(() => { window.__pageEventRuns = (window.__pageEventRuns || 0) + 1; })"
        template = "<c-child />"

        class Events:
            def page_event(self):
                return None

    def corrupt(manifest: dict[str, Any]) -> None:
        manifest["componentInstances"][1]["publicState"] = []

    html = _mutate_events(Page().render().serialize(), corrupt)
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_timeout(150)

    assert page.evaluate("Citry.manager.ownership.revisions().length") == 1
    assert page.evaluate("window.__pageEventRuns || 0") == 0
    assert page.evaluate("window.__childEventRuns || 0") == 0
    assert page.evaluate("Citry.events._internal.anchors.size") == 0
    assert any("failed to process events manifest" in message for message in messages)
    assert any("discarded graph-linked dependency manifest" in message for message in messages)


def test_events_class_mismatch_rejects_before_any_anchor_or_callback(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c
        js = "$component(() => { window.__mismatchedEventsRuns = (window.__mismatchedEventsRuns || 0) + 1; })"
        template = "<button>page</button>"

        class Events:
            def save(self):
                return None

    html = _mutate_events(
        Page().render().serialize(),
        lambda manifest: manifest["componentInstances"][0].update(componentClassId="WrongClass"),
    )
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_timeout(150)

    assert page.evaluate("window.__mismatchedEventsRuns || 0") == 0
    assert page.evaluate("Citry.events._internal.anchors.size") == 0
    assert page.evaluate("Citry.events._internal.classes.size") == 0
    assert any("failed to process events manifest" in message for message in messages)


@pytest.mark.parametrize(
    "bad_revision",
    [
        pytest.param(None, id="missing-link"),
        pytest.param("not-a-revision", id="invalid-link"),
        pytest.param("f" * 64, id="mismatched-link"),
    ],
)
def test_bad_events_graph_link_blocks_callbacks_and_registry_mutation(
    page: Any,
    serve_live: Any,
    bad_revision: str | None,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c
        js = "$component(() => { window.__badEventsLinkRuns = (window.__badEventsLinkRuns || 0) + 1; })"
        template = "<main>page</main>"

        class Events:
            def save(self):
                return None

    html = _mutate_events(
        Page().render().serialize(),
        lambda manifest: manifest.update(clientGraphRevision=bad_revision),
    )
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_timeout(150)

    assert page.evaluate("window.__badEventsLinkRuns || 0") == 0
    assert page.evaluate("Citry.events._internal.anchors.size") == 0
    assert page.evaluate("Citry.events._internal.classes.size") == 0
    assert any("failed to process events manifest" in message for message in messages)


def test_graph_linked_callback_class_mismatch_is_atomic(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c
        js = "$component(() => { window.__mismatchedCallbackRuns = (window.__mismatchedCallbackRuns || 0) + 1; })"
        template = "<main>page</main>"

    html = _mutate_dependencies(
        Page().render().serialize(),
        lambda manifest: manifest["calls"][0].__setitem__(0, base64.b64encode(b"WrongClass").decode()),
    )
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_timeout(150)

    assert page.evaluate("window.__mismatchedCallbackRuns || 0") == 0
    assert any("discarded graph-linked dependency manifest" in message for message in messages)


def test_cloned_processed_graph_tag_reaches_duplicate_revision_rejection(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c
        js = "$component(() => { window.__cloneRuns = (window.__cloneRuns || 0) + 1; })"
        template = "<main>page</main>"

    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("window.__cloneRuns === 1")

    page.evaluate("document.body.append(document.querySelector('[data-citry-graph]').cloneNode(true))")
    page.wait_for_timeout(50)

    assert page.evaluate("Citry.manager.ownership.revisions().length") == 1
    assert page.evaluate("window.__cloneRuns") == 1
    assert any("failed to process ownership graph manifest" in message for message in messages)


def test_duplicate_alpine_bundle_preserves_identity_and_permanent_hook_counts(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c
        js = "$component(() => { window.__a3DuplicateReady = true; })"
        template = "<main x-data>page</main>"

    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a3DuplicateReady && Citry.alpine._isStarted()")

    result = page.evaluate(
        """
        async () => {
          const beforeAlpine = window.Alpine;
          const before = Citry.alpine._debug();
          const source = await fetch("/citry/ext/events/runtime.js").then((response) => response.text());
          eval(source);
          const after = Citry.alpine._debug();
          return {
            sameAlpine: window.Alpine === beforeAlpine,
            before: before,
            after: after,
          };
        }
        """
    )
    assert result["sameAlpine"] is True
    assert result["after"] == result["before"]
    assert any("a second Citry Alpine bundle was evaluated" in message for message in messages)


def test_explicit_revision_replacement_preserves_replaces_and_retires_identity(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        js = "$component(() => {})"
        template = "<article>card</article>"

    class Panel(Component):
        citry = c
        js = "$component(() => {})"
        template = "<section>panel</section>"

    fragments = "".join(
        [
            Card().render().serialize(deps_strategy="fragment"),
            Card().render().serialize(deps_strategy="fragment"),
            Panel().render().serialize(deps_strategy="fragment"),
        ]
    )
    page_html = """
      <html><head><script src="/citry/citry.js"></script></head>
      <body><div id="target"></div></body></html>
    """
    base = serve_live(c, page_html, fragments)
    page.goto(base + "/")
    page.evaluate(
        """
        async () => {
          const html = await fetch('/fragment').then((response) => response.text());
          document.getElementById('target').innerHTML = html;
        }
        """
    )
    page.wait_for_function("Citry.manager.ownership.revisions().length === 3")

    result = page.evaluate(
        """
        () => {
          const revisions = Citry.manager.ownership.revisions();
          const routes = revisions.map((revision) => {
            const renderId = Citry.manager.ownership.get(revision).registry.renderIds.keys()[0];
            return Citry.manager.ownership.forRender(revision, renderId);
          });
          const firstAnchor = routes[0].anchor;
          const firstLogical = routes[0].logicalInstance;
          const secondProvisionalAnchor = routes[1].anchor;
          const secondProvisionalLogical = routes[1].logicalInstance;

          let selfMapRolledBack = false;
          try {
            Citry.manager.ownership._replace([{
              fromRevision: revisions[0],
              fromRenderId: routes[0].instance.renderId,
              toRevision: revisions[0],
              toRenderId: routes[0].instance.renderId,
              preserveLogical: true,
            }]);
          } catch (_err) {
            selfMapRolledBack = routes.every((route) => route.instance.active);
          }

          let overlapRolledBack = false;
          try {
            Citry.manager.ownership._replace([{
              fromRevision: revisions[0],
              fromRenderId: routes[0].instance.renderId,
              toRevision: revisions[1],
              toRenderId: routes[1].instance.renderId,
              preserveLogical: false,
            }, {
              fromRevision: revisions[1],
              fromRenderId: routes[1].instance.renderId,
              toRevision: revisions[2],
              toRenderId: routes[2].instance.renderId,
              preserveLogical: false,
            }]);
          } catch (_err) {
            overlapRolledBack = routes.every((route) => route.instance.active);
          }

          let invalidRolledBack = false;
          try {
            Citry.manager.ownership._replace([{
              fromRevision: revisions[0],
              fromRenderId: routes[0].instance.renderId,
              toRevision: revisions[2],
              toRenderId: routes[2].instance.renderId,
              preserveLogical: true,
            }]);
          } catch (_err) {
            invalidRolledBack = routes[0].instance.active && routes[2].instance.active;
          }

          Citry.manager.ownership._replace([{
            fromRevision: revisions[0],
            fromRenderId: routes[0].instance.renderId,
            toRevision: revisions[1],
            toRenderId: routes[1].instance.renderId,
            preserveLogical: true,
          }]);
          const sameClass = Citry.manager.ownership.forRender(revisions[1], routes[1].instance.renderId);
          const sameClassResult = {
            oldInactive: !routes[0].instance.active,
            keptAnchor: sameClass.anchor === firstAnchor,
            keptLogical: sameClass.logicalInstance === firstLogical,
            provisionalRetired: !secondProvisionalAnchor.active,
            logicalRegistryRekeyed:
              Citry.manager.ownership.get(revisions[1]).registry.logicalInstances.get(firstLogical.id) ===
                firstLogical &&
              !Citry.manager.ownership
                .get(revisions[1])
                .registry.logicalInstances.has(secondProvisionalLogical.id),
          };

          Citry.manager.ownership._replace([{
            fromRevision: revisions[1],
            fromRenderId: routes[1].instance.renderId,
            toRevision: revisions[2],
            toRenderId: routes[2].instance.renderId,
            preserveLogical: false,
          }]);
          const classReplacement = Citry.manager.ownership.forRender(revisions[2], routes[2].instance.renderId);
          const classResult = {
            keptAnchor: classReplacement.anchor === firstAnchor,
            replacedLogical: classReplacement.logicalInstance !== firstLogical,
            oldLogicalRetired: !firstLogical.active,
          };

          Citry.manager.ownership._replace([{
            fromRevision: revisions[2],
            fromRenderId: routes[2].instance.renderId,
            toRevision: null,
            toRenderId: null,
            preserveLogical: false,
          }]);
          return {
            selfMapRolledBack,
            overlapRolledBack,
            invalidRolledBack,
            sameClass: sameClassResult,
            classReplacement: classResult,
            retired: !classReplacement.instance.active && !firstAnchor.active,
          };
        }
        """
    )
    assert result == {
        "selfMapRolledBack": True,
        "overlapRolledBack": True,
        "invalidRolledBack": True,
        "sameClass": {
            "oldInactive": True,
            "keptAnchor": True,
            "keptLogical": True,
            "provisionalRetired": True,
            "logicalRegistryRekeyed": True,
        },
        "classReplacement": {
            "keptAnchor": True,
            "replacedLogical": True,
            "oldLogicalRetired": True,
        },
        "retired": True,
    }


def test_fragment_insertion_commits_once_and_rejects_a_clone(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Frag(Component):
        citry = c
        js = "$component(() => { window.__fragmentRuns = (window.__fragmentRuns || 0) + 1; })"
        template = "<span class='fragment'>fragment</span>"

        class Events:
            def select(self):
                return None

    page_html = """
      <html><head><script src="/citry/citry.js"></script></head>
      <body><div id="target"></div></body></html>
    """
    fragment = Frag().render().serialize(deps_strategy="fragment")
    base = serve_live(c, page_html, fragment)
    page.goto(base + "/")

    page.evaluate(
        """
        async () => {
          const html = await fetch('/fragment').then((response) => response.text());
          document.getElementById('target').innerHTML = html;
        }
        """
    )
    page.wait_for_function("window.__fragmentRuns === 1")
    assert page.evaluate("Citry.manager.ownership.revisions().length") == 1

    with page.expect_console_message(lambda message: "[Citry] failed to process events manifest:" in message.text):
        page.evaluate(
            """
            async () => {
              const html = await fetch('/fragment').then((response) => response.text());
              document.getElementById('target').insertAdjacentHTML('beforeend', html);
            }
            """
        )
    assert page.evaluate("window.__fragmentRuns") == 1
    assert page.evaluate("Citry.manager.ownership.revisions().length") == 1


def test_table_context_fragment_keeps_caps_reconstructable(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Row(Component):
        citry = c
        js = "$component(() => { window.__rowReady = true; })"
        template = "<tr><td>row</td></tr>"

    page_html = """
      <html><head><script src="/citry/citry.js"></script></head>
      <body><table><tbody id="target"></tbody></table></body></html>
    """
    fragment = Row().render().serialize(deps_strategy="fragment")
    base = serve_live(c, page_html, fragment)
    page.goto(base + "/")

    page.evaluate(
        """
        async () => {
          const html = await fetch('/fragment').then((response) => response.text());
          const target = document.getElementById('target');
          const range = document.createRange();
          range.selectNodeContents(target);
          target.append(range.createContextualFragment(html));
        }
        """
    )
    page.wait_for_function("window.__rowReady === true")
    assert page.locator("#target tr td").inner_text() == "row"
    assert page.evaluate("Citry.manager.ownership.revisions().length") == 1


@pytest.mark.parametrize(
    ("container", "template", "selector"),
    [
        ('<select id="target"></select>', '<option value="x">choice</option>', '#target option[value="x"]'),
        (
            '<svg id="target" xmlns="http://www.w3.org/2000/svg"></svg>',
            '<circle id="dot" cx="5" cy="5" r="4" />',
            "#target #dot",
        ),
    ],
)
def test_select_and_svg_context_fragments_keep_caps_reconstructable(
    page: Any,
    serve_live: Any,
    container: str,
    template: str,
    selector: str,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Contextual(Component):
        citry = c
        js = "$component(() => { window.__contextReady = true; })"

    Contextual.template = template
    page_html = f'<html><head><script src="/citry/citry.js"></script></head><body>{container}</body></html>'
    fragment = Contextual().render().serialize(deps_strategy="fragment")
    base = serve_live(c, page_html, fragment)
    page.goto(base + "/")

    page.evaluate(
        """
        async () => {
          const html = await fetch('/fragment').then((response) => response.text());
          const target = document.getElementById('target');
          const range = document.createRange();
          range.selectNodeContents(target);
          target.append(range.createContextualFragment(html));
        }
        """
    )
    page.wait_for_function("window.__contextReady === true")
    assert page.locator(selector).count() == 1
    assert page.evaluate("Citry.manager.ownership.revisions().length") == 1
