"""A8 atomic graph, Events, dependency, and DOM adoption."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry._protocol.client_graph import canonical_json

pytestmark = pytest.mark.e2e

SIGNING_KEY = "a8-e2e-secret"
READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"

_GRAPH_TAG = re.compile(r'(<script type="application/json" data-citry-graph>)(.*?)(</script>)', re.DOTALL)
_EVENTS_TAG = re.compile(r'(<script type="application/json" data-citry-events>)(.*?)(</script>)', re.DOTALL)
_DEPS_TAG = re.compile(r'(<script type="application/json" data-citry>)(.*?)(</script>)', re.DOTALL)


def _fragment(component: Component) -> str:
    return component.render().serialize(deps_strategy="fragment")


def _goto(page: Any, serve_live: Any, citry: Citry, html: str) -> list[str]:
    messages: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    base = serve_live(citry, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    return messages


def _mutate_graph(html: str, mutate: Any) -> str:
    match = _GRAPH_TAG.search(html)
    assert match is not None
    manifest = json.loads(match.group(2))
    old_revision = manifest["revision"]
    mutate(manifest)
    unsigned = {key: value for key, value in manifest.items() if key != "revision"}
    canonical = canonical_json(unsigned).encode()
    manifest["revision"] = hashlib.sha256(canonical).hexdigest()
    replacement = f"{match.group(1)}{json.dumps(manifest)}{match.group(3)}"
    return f"{html[: match.start()]}{replacement}{html[match.end() :]}".replace(
        old_revision,
        manifest["revision"],
    )


def _mutate_events(html: str, mutate: Any) -> str:
    match = _EVENTS_TAG.search(html)
    assert match is not None
    manifest = json.loads(match.group(2))
    mutate(manifest)
    replacement = f"{match.group(1)}{json.dumps(manifest)}{match.group(3)}"
    return f"{html[: match.start()]}{replacement}{html[match.end() :]}"


def _mutate_dependencies(html: str, mutate: Any) -> str:
    match = _DEPS_TAG.search(html)
    assert match is not None
    manifest = json.loads(match.group(2))
    mutate(manifest)
    replacement = f"{match.group(1)}{json.dumps(manifest)}{match.group(3)}"
    return f"{html[: match.start()]}{replacement}{html[match.end() :]}"


def _mutate_class_descriptor(html: str, class_id: str, mutate: Any) -> str:
    def mutate_manifest(manifest: dict[str, Any]) -> None:
        descriptor = next(item for item in manifest["componentClasses"] if item["componentClassId"] == class_id)
        mutate(descriptor)

    return _mutate_events(html, mutate_manifest)


def _make_app() -> tuple[Citry, type[Component], type[Component]]:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class CardState:
        count: int = 0
        _public = ("count",)

    class Card(Component):
        citry = c
        State = CardState
        js = """
          $component(({ scope, els, graph }) => {
            window.__a8 = window.__a8 || { log: [], arrays: [] };
            window.__a8.probeModel = (state) => {
              try {
                state.count = 99;
                window.__a8.modelDuringMorph = "allowed";
              } catch (_error) {
                window.__a8.modelDuringMorph = "blocked";
              }
              return state.count;
            };
            window.__a8.log.push(`init:${graph.instance.renderId}:${els.length}`);
            window.__a8.arrays.push(els);
            scope.initCount = (scope.initCount || 0) + 1;
            return () => window.__a8.log.push(`cleanup:${graph.instance.renderId}`);
          });
        """

        class Events:
            def refresh(self, state):
                return None

        template = """
          <section class="card" x-data="{ local: 1 }">
            <input class="draft" x-model="local">
            <span
              class="server"
              x-text="window.__a8.armModelProbe === true ? window.__a8.probeModel($state) : $state.count"
            ></span>
            <span class="local" x-text="local"></span>
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>A8</title></head>
            <body><c-card c-count="1" /></body>
          </html>
        """

    return c, Card, Page


def test_same_class_self_render_adopts_graph_and_transfers_caps_atomically(page: Any, serve_live: Any) -> None:
    citry, Card, Page = _make_app()
    messages = _goto(page, serve_live, citry, str(Page()))
    fresh = _fragment(Card(count=2))

    def mutate_descriptor(descriptor: dict[str, Any]) -> None:
        descriptor["eventHandlers"]["refresh"]["httpMethod"] = "M-SEARCH"
        descriptor["writableStateFields"] = []

    fresh = _mutate_class_descriptor(
        fresh,
        Card.class_id,
        mutate_descriptor,
    )

    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const rootBefore = document.querySelector(".card");
          const oldId = rootBefore.getAttribute("data-cid");
          const oldRevision = ownership.revisions().find((revision) => ownership.forRender(revision, oldId));
          const oldRoute = ownership.forRender(oldRevision, oldId);
          const oldPhysical = ownership.get(oldRevision).registry.physicalRegions.get(oldRoute.instance.key);
          const oldStart = oldPhysical.start;
          const oldEnd = oldPhysical.end;
          const oldAnchor = oldRoute.anchor;
          const oldLogical = oldRoute.logicalInstance;
          const eventsAnchor = internal.getAnchor(oldId);
          const els = window.__a8.arrays[0];

          window.__a8.armModelProbe = true;
          rootBefore.querySelector(".draft").value = "17";
          rootBefore.querySelector(".draft").dispatchEvent(new Event("input", { bubbles: true }));
          eventsAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + oldId, swap: "morph", html }],
            },
            { anchor: eventsAnchor, instance: oldId, event: "refresh" },
          );

          const rootAfter = document.querySelector(".card");
          const newId = rootAfter.getAttribute("data-cid");
          const newRevision = ownership.revisions().find((revision) => ownership.forRender(revision, newId));
          const newRoute = ownership.forRender(newRevision, newId);
          const newPhysical = ownership.get(newRevision).registry.physicalRegions.get(newRoute.instance.key);
          return {
            idsChanged: newId !== oldId,
            revisionsChanged: newRevision !== oldRevision,
            oldRouteInactive: ownership.forRender(oldRevision, oldId) === null,
            anchorKept: newRoute.anchor === oldAnchor && internal.getAnchor(newId) === eventsAnchor,
            logicalKept: newRoute.logicalInstance === oldLogical,
            capsTransferred: newPhysical.start === oldStart && newPhysical.end === oldEnd,
            capRevisionChanged:
              newPhysical.start.data.includes(newRevision) && !newPhysical.start.data.includes(oldRevision),
            rootKept: rootAfter === rootBefore,
            elsKept: window.__a8.arrays[1] === els && els[0] === rootAfter,
            local: rootAfter.querySelector(".local").textContent,
            server: rootAfter.querySelector(".server").textContent,
            modelDuringMorph: window.__a8.modelDuringMorph,
            pending: Object.assign({}, eventsAnchor.pending),
            log: window.__a8.log,
          };
        }
        """,
        [fresh],
    )

    assert result["idsChanged"] is True
    assert result["revisionsChanged"] is True
    assert result["oldRouteInactive"] is True
    assert result["anchorKept"] is True
    assert result["logicalKept"] is True
    assert result["capsTransferred"] is True
    assert result["capRevisionChanged"] is True
    assert result["rootKept"] is True
    assert result["elsKept"] is True, result
    assert result["local"] == "17"
    assert result["server"] == "2"
    assert result["modelDuringMorph"] == "blocked"
    assert result["pending"] == {}
    assert result["log"][0].startswith("init:")
    assert result["log"][1].startswith("cleanup:")
    assert result["log"][2].startswith("init:")
    assert not [message for message in messages if message.startswith("error:")]


@pytest.mark.parametrize(
    "corruption",
    [
        "graph",
        "events",
        "events_options",
        "events_writable_state_fields",
        "dependency_calls",
        "dependency_mark_loaded",
        "dependency_css_instances",
        "dependency_asset",
    ],
)
def test_malformed_fragment_rolls_back_before_epoch_or_dom_mutation(
    page: Any,
    serve_live: Any,
    corruption: str,
) -> None:
    citry, Card, Page = _make_app()
    _goto(page, serve_live, citry, str(Page()))
    fresh = _fragment(Card(count=9))
    if corruption == "graph":
        fresh = _mutate_graph(fresh, lambda manifest: manifest["delimiters"].update(format="citry:g2"))
    elif corruption == "events":
        fresh = _mutate_events(fresh, lambda manifest: manifest["componentInstances"].append({"broken": True}))
    elif corruption == "events_options":
        fresh = _mutate_class_descriptor(
            fresh,
            Card.class_id,
            lambda descriptor: descriptor["eventHandlers"]["refresh"].update(httpMethod=7),
        )
    elif corruption == "events_writable_state_fields":
        fresh = _mutate_class_descriptor(
            fresh,
            Card.class_id,
            lambda descriptor: descriptor.update(writableStateFields=None),
        )
    elif corruption == "dependency_calls":
        fresh = _mutate_dependencies(fresh, lambda manifest: manifest["calls"].append(["broken"]))
    elif corruption == "dependency_mark_loaded":
        fresh = _mutate_dependencies(fresh, lambda manifest: manifest.update(markLoaded={"js": [123], "css": []}))
    elif corruption == "dependency_css_instances":
        fresh = _mutate_dependencies(fresh, lambda manifest: manifest["cssInstances"].append(["broken"]))
    else:
        invalid_descriptor = base64.b64encode(json.dumps({"tag": "bad tag"}).encode()).decode()
        fresh = _mutate_dependencies(fresh, lambda manifest: manifest["fetch"]["js"].append(invalid_descriptor))

    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const root = document.querySelector(".card");
          const id = root.getAttribute("data-cid");
          const anchor = internal.getAnchor(id);
          const fragment = new DOMParser().parseFromString(html, "text/html");
          const incomingRevision = JSON.parse(fragment.querySelector("script[data-citry-graph]").textContent).revision;
          const ready = ownership.whenReady(incomingRevision).then(
            () => "resolved",
            () => "rejected",
          );
          const before = {
            html: root.outerHTML,
            revisions: ownership.revisions().slice(),
            highestApplied: anchor.highestApplied,
            epochOwner: anchor.epochOwner,
            log: window.__a8.log.slice(),
          };
          anchor.epoch = 1;
          let rejected = false;
          try {
            await internal.applyResult(
              {
                ok: true,
                sendSequence: 1,
                actions: [{ action: "render", target: "render:" + id, swap: "morph", html }],
              },
              { anchor, instance: id, event: "refresh" },
            );
          } catch (_error) {
            rejected = true;
          }
          return {
            rejected,
            domUnchanged: root.isConnected && root.outerHTML === before.html,
            revisionsUnchanged: JSON.stringify(ownership.revisions()) === JSON.stringify(before.revisions),
            anchorUnchanged: internal.getAnchor(id) === anchor && anchor.componentId === id,
            epochUnchanged: anchor.highestApplied === before.highestApplied && anchor.epochOwner === before.epochOwner,
            callbacksUnchanged: JSON.stringify(window.__a8.log) === JSON.stringify(before.log),
            waiter: await ready,
          };
        }
        """,
        [fresh],
    )

    assert result == {
        "rejected": True,
        "domUnchanged": True,
        "revisionsUnchanged": True,
        "anchorUnchanged": True,
        "epochUnchanged": True,
        "callbacksUnchanged": True,
        "waiter": "rejected",
    }


def test_provisional_routes_stay_private_and_public_placement_arrays_are_frozen(
    page: Any,
    serve_live: Any,
) -> None:
    citry, Card, Page = _make_app()
    messages = _goto(page, serve_live, citry, str(Page()))
    fresh = _fragment(Card(count=3))
    result = page.evaluate(
        """
        ([html]) => {
          const ownership = Citry.manager.ownership;
          const currentRevision = ownership.revisions()[0];
          const currentGraph = ownership.get(currentRevision);
          const cardId = document.querySelector(".card").getAttribute("data-cid");
          const currentRoute = ownership.forRender(currentRevision, cardId);
          const placements = currentGraph.registry.physicalPlacements.get(currentRoute.instance.key);
          let placementMutationRejected = false;
          try {
            placements.pop();
          } catch (_error) {
            placementMutationRejected = true;
          }

          const template = document.createElement("template");
          template.innerHTML = html;
          const graphTag = template.content.querySelector("script[data-citry-graph]");
          const manifest = JSON.parse(graphTag.textContent);
          const transaction = ownership._prepareAdoption(manifest, template.content);
          const root = ownership._adoptionRoot(transaction);
          const publicRoute = ownership.forRender(manifest.revision, root.componentId);
          ownership._abortAdoption(transaction, new Error("test abort"));
          return {
            provisionalHidden: publicRoute === null && !ownership.revisions().includes(manifest.revision),
            placementMutationRejected,
            placementLength: currentGraph.registry.physicalPlacements.get(currentRoute.instance.key).length,
          };
        }
        """,
        [fresh],
    )

    assert result == {"provisionalHidden": True, "placementMutationRejected": True, "placementLength": 1}
    assert not [message for message in messages if message.startswith("error:")]


def test_post_morph_cap_failure_fails_closed_and_releases_adoption_hold(page: Any, serve_live: Any) -> None:
    # The incoming same-class descriptor temporarily replaces `refresh` with
    # `hijacked`. Its failed transaction must restore both the descriptor and
    # a retained `refresh` error on the sibling instance that stays live.
    citry, Card, Page = _make_app()
    del Page
    app = citry

    class TwoCards(Component):
        citry = app
        template = """
          <html>
            <head><title>A8 class rollback</title></head>
            <body><c-card c-count="1" /><c-card c-count="2" /></body>
          </html>
        """

    messages = _goto(page, serve_live, citry, str(TwoCards()))
    fresh = _fragment(Card(count=8))
    fresh = _mutate_class_descriptor(
        fresh,
        Card.class_id,
        lambda descriptor: descriptor.update(
            eventHandlers={"hijacked": {"httpMethod": "POST"}},
            writableStateFields=[],
        ),
    )
    result = page.evaluate(
        """
        async ([html, classId]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const [root, sibling] = Array.from(document.querySelectorAll(".card"));
          const id = root.getAttribute("data-cid");
          const siblingId = sibling.getAttribute("data-cid");
          const anchor = internal.getAnchor(id);
          const siblingAnchor = internal.getAnchor(siblingId);
          const originalClassDescriptor = internal.classes.get(classId);
          const originalRevision = ownership.revisions().find((revision) => ownership.forRender(revision, id));
          const originalRoute = ownership.forRender(originalRevision, id);
          const originalPhysical = ownership
            .get(originalRevision)
            .registry.physicalRegions.get(originalRoute.instance.key);
          const beforeRevisions = ownership.revisions().slice();
          const fragment = new DOMParser().parseFromString(html, "text/html");
          const incomingRevision = JSON.parse(fragment.querySelector("script[data-citry-graph]").textContent).revision;
          const ready = ownership.whenReady(incomingRevision).then(
            () => "resolved",
            () => "rejected",
          );
          internal.setTransport(async () => {
            throw { status: 422, code: "invalid", message: "retained sibling error" };
          });
          await Citry.events.send(siblingId, "refresh", {}).catch(() => {});
          anchor.epoch = 1;
          const commit = ownership._commitAdoption;
          ownership._commitAdoption = () => { throw new Error("injected post-morph commit failure"); };
          let rejected = false;
          try {
            await internal.applyResult(
              {
                ok: true,
                sendSequence: 1,
                actions: [{ action: "render", target: "render:" + id, swap: "morph", html }],
              },
              { anchor, instance: id, event: "refresh" },
            );
          } catch (_error) {
            rejected = true;
          } finally {
            ownership._commitAdoption = commit;
          }
          await new Promise((resolve) => setTimeout(resolve, 0));
          const siblingErrorAfterRollback = siblingAnchor.errorBox.handlers.refresh.current;
          internal.setTransport(async (call) => {
            window.__a8SiblingCall = call;
            return { ok: true };
          });
          siblingAnchor.stateProxy.count = 3;
          const siblingSend = await Citry.events.send(siblingId, "refresh", {}).then(
            () => "resolved",
            (error) => String(error && (error.message || error)),
          );
          return {
            rejected,
            targetRemoved: !root.isConnected,
            siblingStayed:
              sibling.isConnected &&
              internal.getAnchor(siblingId) === siblingAnchor &&
              document.querySelectorAll(".card").length === 1,
            classDescriptorRestored: internal.classes.get(classId) === originalClassDescriptor,
            siblingErrorAfterRollback,
            siblingSend,
            siblingEvent: window.__a8SiblingCall && window.__a8SiblingCall.handlerName,
            siblingUpdates: window.__a8SiblingCall && window.__a8SiblingCall.stateUpdates,
            incomingHidden:
              !ownership.revisions().includes(incomingRevision) && !ownership.has(incomingRevision),
            originalRevisionSet: beforeRevisions.every((revision) => ownership.revisions().includes(revision)),
            eventsRetired: anchor.componentId === null && internal.getAnchor(id) === null,
            capsRemoved: !originalPhysical.start.isConnected && !originalPhysical.end.isConnected,
            waiter: await ready,
            cleanupCount: window.__a8.log.filter((entry) => entry.startsWith("cleanup:")).length,
          };
        }
        """,
        [fresh, Card.class_id],
    )

    assert result == {
        "rejected": True,
        "targetRemoved": True,
        "siblingStayed": True,
        "classDescriptorRestored": True,
        "siblingErrorAfterRollback": {
            "status": 422,
            "code": "invalid",
            "message": "retained sibling error",
        },
        "siblingSend": "resolved",
        "siblingEvent": "refresh",
        "siblingUpdates": {"count": 3},
        "incomingHidden": True,
        "originalRevisionSet": True,
        "eventsRetired": True,
        "capsRemoved": True,
        "waiter": "rejected",
        "cleanupCount": 1,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_rootless_self_render_uses_caps_as_the_target_and_keeps_logical_lifecycle(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Rootless(Component):
        citry = c
        js = """
          $component(({ els, graph }) => {
            window.__rootlessA8 = window.__rootlessA8 || { arrays: [], log: [] };
            window.__rootlessA8.arrays.push(els);
            window.__rootlessA8.log.push(`init:${graph.instance.renderId}:${els.length}`);
            return () => window.__rootlessA8.log.push(`cleanup:${graph.instance.renderId}`);
          });
        """

        class Events:
            def refresh(self):
                return None

        template = "rootless={{ value }}"

        def template_data(self, kwargs, slots):
            return {"value": kwargs["value"]}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>A8 rootless</title></head>
            <body><div id="zone"><c-rootless c-value="'one'" /></div></body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Rootless(value="two"))
    newer = _fragment(Rootless(value="three"))
    result = page.evaluate(
        """
        async ([html, newerHtml, classId]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const oldRevision = ownership.revisions()[0];
          const oldGraph = ownership.get(oldRevision);
          const oldInstance = oldGraph.registry.renderIds.values().find((instance) => instance.classId === classId);
          const oldRoute = ownership.forRender(oldRevision, oldInstance.renderId);
          const oldPhysical = oldGraph.registry.physicalRegions.get(oldInstance.key);
          const oldStart = oldPhysical.start;
          const oldEnd = oldPhysical.end;
          const oldAnchor = oldRoute.anchor;
          const oldLogical = oldRoute.logicalInstance;
          const eventsAnchor = internal.getAnchor(oldInstance.renderId);
          const els = window.__rootlessA8.arrays[0];
          eventsAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + oldInstance.renderId, swap: "morph", html }],
            },
            { anchor: eventsAnchor, instance: oldInstance.renderId, event: "refresh" },
          );
          const middleId = eventsAnchor.componentId;
          eventsAnchor.epoch = 2;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 2,
              actions: [{ action: "render", target: "render:" + middleId, swap: "morph", html: newerHtml }],
            },
            { anchor: eventsAnchor, instance: middleId, event: "refresh" },
          );
          const newId = eventsAnchor.componentId;
          const newRevision = ownership.revisions().find((revision) => ownership.forRender(revision, newId));
          const route = ownership.forRender(newRevision, newId);
          const physical = ownership.get(newRevision).registry.physicalRegions.get(route.instance.key);
          return {
            text: Array.from(document.querySelector("#zone").childNodes)
              .filter((node) => node.nodeType === Node.TEXT_NODE)
              .map((node) => node.textContent)
              .join("")
              .trim(),
            capIdentity: physical.start === oldStart && physical.end === oldEnd,
            anchorIdentity: route.anchor === oldAnchor,
            logicalIdentity: route.logicalInstance === oldLogical,
            noRoots:
              window.__rootlessA8.arrays[1] === els &&
              window.__rootlessA8.arrays[2] === els &&
              els.length === 0,
            revisionCount: ownership.revisions().length,
            log: window.__rootlessA8.log,
          };
        }
        """,
        [fresh, newer, Rootless.class_id],
    )

    assert result["text"] == "rootless=three"
    assert result["capIdentity"] is True
    assert result["anchorIdentity"] is True
    assert result["logicalIdentity"] is True
    assert result["noRoots"] is True
    assert result["revisionCount"] == 2
    assert result["log"][1].startswith("cleanup:")
    assert result["log"][2].startswith("init:")
    assert result["log"][3].startswith("cleanup:")
    assert result["log"][4].startswith("init:")
    assert not [message for message in messages if message.startswith("error:")]


def test_keyed_child_without_events_uses_general_graph_correspondence(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component(({ els, scope }) => {
            window.__generalKeyed = window.__generalKeyed || [];
            window.__generalKeyed.push({ els, scope });
          });
        """
        template = """
          <div class="general-child">
            <input class="draft">
            <span>{{ label }}</span>
            <div class="scrollbox" style="height: 20px; overflow: auto"><div style="height: 200px"></div></div>
            <iframe class="frame" srcdoc="<p>inside</p>"></iframe>
          </div>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <section class="general-parent">
            <c-child #c-key="'stable'" c-label="label" />
          </section>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Page(Component):
        citry = c
        template = """
          <html><head><title>general keyed</title></head><body><c-parent c-label="'one'" /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(label="two"))
    result = page.evaluate(
        """
        async ([html, childClass]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const parentRoot = document.querySelector(".general-parent");
          const childRoot = document.querySelector(".general-child");
          const parentId = parentRoot.getAttribute("data-cid").trim().split(" ").at(-1);
          const childId = childRoot.getAttribute("data-cid").trim().split(" ").at(-1);
          const oldRevision = ownership.revisions().find((revision) => ownership.forRender(revision, childId));
          const oldRoute = ownership.forRender(oldRevision, childId);
          const parentAnchor = internal.getAnchor(parentId);
          const input = childRoot.querySelector("input");
          const scrollbox = childRoot.querySelector(".scrollbox");
          const frame = childRoot.querySelector(".frame");
          input.value = "draft";
          input.focus();
          input.setSelectionRange(2, 2);
          scrollbox.scrollTop = 41;
          frame.contentWindow.__citryStationary = "kept";
          const frameWindow = frame.contentWindow;
          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor: parentAnchor, instance: parentId, event: "refresh" },
          );
          const freshRoot = document.querySelector(".general-child");
          const freshId = freshRoot.getAttribute("data-cid").trim().split(" ").at(-1);
          const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, freshId));
          const route = ownership.forRender(revision, freshId);
          return {
            classKept: route.instance.classId === childClass,
            anchorKept: route.anchor === oldRoute.anchor,
            logicalKept: route.logicalInstance === oldRoute.logicalInstance,
            rootKept: freshRoot === childRoot,
            draftKept: freshRoot.querySelector("input").value,
            focusKept:
              document.activeElement === input && input.selectionStart === 2 && input.selectionEnd === 2,
            scrollKept: scrollbox.scrollTop === 41,
            iframeKept:
              freshRoot.querySelector(".frame") === frame &&
              frame.contentWindow === frameWindow &&
              frame.contentWindow.__citryStationary === "kept",
            label: freshRoot.querySelector("span").textContent,
            callbackIdentity:
              window.__generalKeyed.length === 2 &&
              window.__generalKeyed[0].els === window.__generalKeyed[1].els &&
              window.__generalKeyed[0].scope === window.__generalKeyed[1].scope,
            temporaryAdaptersRemoved:
              !document.querySelector(
                "template[data-citry-range-holder],template[data-citry-range-sentinel]",
              ),
          };
        }
        """,
        [fresh, Child.class_id],
    )

    assert result == {
        "classKept": True,
        "anchorKept": True,
        "logicalKept": True,
        "rootKept": True,
        "draftKept": "draft",
        "focusKept": True,
        "scrollKept": True,
        "iframeKept": True,
        "label": "two",
        "callbackIdentity": True,
        "temporaryAdaptersRemoved": True,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_keyed_supplied_slot_child_preserves_its_physical_range_during_parent_morph(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Leaf(Component):
        citry = c
        template = """
          <button class="slotted-leaf">
            <input class="draft" />
            <span class="slot-scroll" style="display:block;height:20px;overflow:auto">
              <span style="display:block;height:120px">scroll contents</span>
            </span>
            <iframe class="slot-frame" srcdoc="<p>frame</p>"></iframe>
            <span class="label">{{ label }}</span>
          </button>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Wrapper(Component):
        citry = c
        template = '<section class="slot-wrapper"><c-slot /></section>'

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="slotted-parent">
            <c-wrapper #c-key="'wrapper'">
              <c-leaf #c-key="'leaf'" c-label="label" />
            </c-wrapper>
          </main>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Page(Component):
        citry = c
        template = """
          <html><head><title>keyed supplied slot child</title></head><body><c-parent c-label="'old'" /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(label="fresh"))
    result = page.evaluate(
        """
        async ([html, wrapperClass, leafClass]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const parent = document.querySelector(".slotted-parent");
          const wrapper = document.querySelector(".slot-wrapper");
          const leaf = document.querySelector(".slotted-leaf");
          const parentId = parent.getAttribute("data-cid").trim().split(" ").at(-1);
          const parentAnchor = internal.getAnchor(parentId);
          const routeForClass = (classId) => {
            for (const revision of ownership.revisions()) {
              const graph = ownership.get(revision);
              const instance = Array.from(graph.registry.renderIds.values()).find(
                (candidate) => candidate.classId === classId,
              );
              const route = instance && ownership.forRender(revision, instance.renderId);
              if (route) return { revision, route };
            }
            throw new Error(`missing route for ${classId}`);
          };
          const before = {};
          for (const [name, classId, root] of [
            ["wrapper", wrapperClass, wrapper],
            ["leaf", leafClass, leaf],
          ]) {
            const { revision, route } = routeForClass(classId);
            const physical = ownership.get(revision).registry.physicalPlacements.get(route.instance.key)[0];
            before[name] = {
              root,
              anchor: route.anchor,
              logical: route.logicalInstance,
              start: physical.start,
              end: physical.end,
            };
          }
          const draft = leaf.querySelector(".draft");
          draft.value = "browser draft";
          draft.focus();
          draft.setSelectionRange(3, 3);
          const scrollbox = leaf.querySelector(".slot-scroll");
          scrollbox.scrollTop = 37;
          const frame = leaf.querySelector(".slot-frame");
          frame.contentWindow.__citrySlotted = "kept";
          const frameWindow = frame.contentWindow;
          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor: parentAnchor, instance: parentId, event: "refresh" },
          );
          const after = {};
          for (const [name, classId, selector] of [
            ["wrapper", wrapperClass, ".slot-wrapper"],
            ["leaf", leafClass, ".slotted-leaf"],
          ]) {
            const root = document.querySelector(selector);
            const { revision, route } = routeForClass(classId);
            const physical = ownership.get(revision).registry.physicalPlacements.get(route.instance.key)[0];
            after[name] = {
              root: root === before[name].root,
              anchor: route.anchor === before[name].anchor,
              logical: route.logicalInstance === before[name].logical,
              caps: physical.start === before[name].start && physical.end === before[name].end,
            };
          }
          return {
            after,
            draft: document.querySelector(".slotted-leaf .draft").value,
            focusKept:
              document.activeElement === draft && draft.selectionStart === 3 && draft.selectionEnd === 3,
            scrollKept: scrollbox.scrollTop === 37,
            iframeKept:
              document.querySelector(".slotted-leaf .slot-frame") === frame &&
              frame.contentWindow === frameWindow &&
              frame.contentWindow.__citrySlotted === "kept",
            label: document.querySelector(".slotted-leaf .label").textContent,
            temporaryAdaptersRemoved:
              !document.querySelector(
                "template[data-citry-range-holder],template[data-citry-range-sentinel]",
              ),
          };
        }
        """,
        [fresh, Wrapper.class_id, Leaf.class_id],
    )

    assert result == {
        "after": {
            "wrapper": {"root": True, "anchor": True, "logical": True, "caps": True},
            "leaf": {"root": True, "anchor": True, "logical": True, "caps": True},
        },
        "draft": "browser draft",
        "focusKept": True,
        "scrollKept": True,
        "iframeKept": True,
        "label": "fresh",
        "temporaryAdaptersRemoved": True,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_reordered_keyed_wrappers_preserve_their_nested_keyed_supplied_children(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Leaf(Component):
        citry = c
        template = """
          <article class="nested-slotted-leaf" c-data-ident="ident">
            <input class="draft" />
            <span class="label">{{ label }}</span>
          </article>
        """

        def template_data(self, kwargs, slots):
            return {"ident": kwargs["ident"], "label": kwargs["label"]}

    class Wrapper(Component):
        citry = c
        template = '<section class="nested-slot-wrapper" c-data-ident="ident"><c-slot /></section>'

        def template_data(self, kwargs, slots):
            return {"ident": kwargs["ident"]}

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="nested-slotted-parent">
            <c-if cond="variant == 'old'">
              <c-wrapper #c-key="'a'" c-ident="'a'">
                <c-leaf #c-key="'a'" c-ident="'a'" c-label="'A old'" />
              </c-wrapper>
              <c-wrapper #c-key="'b'" c-ident="'b'">
                <c-leaf #c-key="'b'" c-ident="'b'" c-label="'B old'" />
              </c-wrapper>
            </c-if>
            <c-else>
              <c-wrapper #c-key="'b'" c-ident="'b'">
                <c-leaf #c-key="'b'" c-ident="'b'" c-label="'B fresh'" />
              </c-wrapper>
              <c-wrapper #c-key="'a'" c-ident="'a'">
                <c-leaf #c-key="'a'" c-ident="'a'" c-label="'A fresh'" />
              </c-wrapper>
            </c-else>
          </main>
        """

        def template_data(self, kwargs, slots):
            return {"variant": kwargs["variant"]}

    class Page(Component):
        citry = c
        template = """
          <html><head><title>nested keyed supplied children</title></head>
          <body><c-parent c-variant="'old'" /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(variant="fresh"))
    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const parent = document.querySelector(".nested-slotted-parent");
          const parentId = parent.getAttribute("data-cid").trim().split(" ").at(-1);
          const parentAnchor = internal.getAnchor(parentId);
          const routeForRoot = (root) => {
            const id = root.getAttribute("data-cid").trim().split(" ").at(-1);
            for (const revision of ownership.revisions()) {
              const route = ownership.forRender(revision, id);
              if (route) return { revision, route };
            }
            throw new Error(`missing route for ${id}`);
          };
          const before = {};
          for (const ident of ["a", "b"]) {
            const wrapper = document.querySelector(`.nested-slot-wrapper[data-ident="${ident}"]`);
            const leaf = document.querySelector(`.nested-slotted-leaf[data-ident="${ident}"]`);
            const wrapperRoute = routeForRoot(wrapper);
            const leafRoute = routeForRoot(leaf);
            const wrapperPhysical = ownership
              .get(wrapperRoute.revision)
              .registry.physicalPlacements.get(wrapperRoute.route.instance.key)[0];
            const leafPhysical = ownership
              .get(leafRoute.revision)
              .registry.physicalPlacements.get(leafRoute.route.instance.key)[0];
            leaf.querySelector(".draft").value = `draft-${ident}`;
            before[ident] = {
              wrapper,
              wrapperAnchor: wrapperRoute.route.anchor,
              wrapperLogical: wrapperRoute.route.logicalInstance,
              wrapperStart: wrapperPhysical.start,
              wrapperEnd: wrapperPhysical.end,
              leaf,
              leafAnchor: leafRoute.route.anchor,
              leafLogical: leafRoute.route.logicalInstance,
              leafStart: leafPhysical.start,
              leafEnd: leafPhysical.end,
            };
          }
          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor: parentAnchor, instance: parentId, event: "refresh" },
          );
          const after = {};
          for (const ident of ["a", "b"]) {
            const wrapper = document.querySelector(`.nested-slot-wrapper[data-ident="${ident}"]`);
            const leaf = document.querySelector(`.nested-slotted-leaf[data-ident="${ident}"]`);
            const wrapperRoute = routeForRoot(wrapper);
            const leafRoute = routeForRoot(leaf);
            const wrapperPhysical = ownership
              .get(wrapperRoute.revision)
              .registry.physicalPlacements.get(wrapperRoute.route.instance.key)[0];
            const leafPhysical = ownership
              .get(leafRoute.revision)
              .registry.physicalPlacements.get(leafRoute.route.instance.key)[0];
            after[ident] = {
              wrapperRoot: wrapper === before[ident].wrapper,
              wrapperAnchor: wrapperRoute.route.anchor === before[ident].wrapperAnchor,
              wrapperLogical: wrapperRoute.route.logicalInstance === before[ident].wrapperLogical,
              wrapperCaps:
                wrapperPhysical.start === before[ident].wrapperStart &&
                wrapperPhysical.end === before[ident].wrapperEnd,
              leafRoot: leaf === before[ident].leaf,
              leafAnchor: leafRoute.route.anchor === before[ident].leafAnchor,
              leafLogical: leafRoute.route.logicalInstance === before[ident].leafLogical,
              leafCaps:
                leafPhysical.start === before[ident].leafStart && leafPhysical.end === before[ident].leafEnd,
              draft: leaf.querySelector(".draft").value,
              label: leaf.querySelector(".label").textContent,
            };
          }
          return {
            order: Array.from(document.querySelectorAll(".nested-slot-wrapper")).map(
              (root) => root.dataset.ident,
            ),
            after,
          };
        }
        """,
        [fresh],
    )

    assert result == {
        "order": ["b", "a"],
        "after": {
            "a": {
                "wrapperRoot": True,
                "wrapperAnchor": True,
                "wrapperLogical": True,
                "wrapperCaps": True,
                "leafRoot": True,
                "leafAnchor": True,
                "leafLogical": True,
                "leafCaps": True,
                "draft": "draft-a",
                "label": "A fresh",
            },
            "b": {
                "wrapperRoot": True,
                "wrapperAnchor": True,
                "wrapperLogical": True,
                "wrapperCaps": True,
                "leafRoot": True,
                "leafAnchor": True,
                "leafLogical": True,
                "leafCaps": True,
                "draft": "draft-b",
                "label": "B fresh",
            },
        },
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_keyed_child_survives_planned_morph_under_document_body_parent_range(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        template = """
          <article class="document-keyed-child">
            <input class="draft" />
            <span class="label">{{ label }}</span>
          </article>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="document-keyed-parent">
            <c-child #c-key="'stable'" c-label="label" />
          </main>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    messages = _goto(page, serve_live, c, str(Parent(label="old")))
    fresh = _fragment(Parent(label="fresh"))
    result = page.evaluate(
        """
        async ([html, parentClass, childClass]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const routeForClass = (classId, requiredAnchor = null) => {
            for (const revision of ownership.revisions()) {
              const graph = ownership.get(revision);
              const instance = Array.from(graph.registry.renderIds.values()).find(
                (candidate) => candidate.classId === classId,
              );
              const route = instance && ownership.forRender(revision, instance.renderId);
              if (route && (!requiredAnchor || route.anchor === requiredAnchor)) {
                return { revision, route };
              }
            }
            throw new Error(`missing route for ${classId}`);
          };
          const parentBefore = routeForClass(parentClass);
          const childBefore = routeForClass(childClass);
          const parentPhysical = ownership
            .get(parentBefore.revision)
            .registry.physicalPlacements.get(parentBefore.route.instance.key)[0];
          const childPhysical = ownership
            .get(childBefore.revision)
            .registry.physicalPlacements.get(childBefore.route.instance.key)[0];
          const childRoot = document.querySelector(".document-keyed-child");
          childRoot.querySelector(".draft").value = "document draft";
          const parentAnchor = internal.getAnchor(parentBefore.route.instance.renderId);
          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{
                action: "render",
                target: "render:" + parentBefore.route.instance.renderId,
                swap: "morph",
                html,
              }],
            },
            {
              anchor: parentAnchor,
              instance: parentBefore.route.instance.renderId,
              event: "refresh",
            },
          );
          const parentAfter = routeForClass(parentClass, parentBefore.route.anchor);
          const childAfter = routeForClass(childClass, childBefore.route.anchor);
          const parentPhysicalAfter = ownership
            .get(parentAfter.revision)
            .registry.physicalPlacements.get(parentAfter.route.instance.key)[0];
          const childPhysicalAfter = ownership
            .get(childAfter.revision)
            .registry.physicalPlacements.get(childAfter.route.instance.key)[0];
          const rootAfter = document.querySelector(".document-keyed-child");
          return {
            topology: parentPhysical.topology,
            parentAnchor: parentAfter.route.anchor === parentBefore.route.anchor,
            parentLogical: parentAfter.route.logicalInstance === parentBefore.route.logicalInstance,
            parentCaps:
              parentPhysicalAfter.start === parentPhysical.start &&
              parentPhysicalAfter.end === parentPhysical.end,
            childAnchor: childAfter.route.anchor === childBefore.route.anchor,
            childLogical: childAfter.route.logicalInstance === childBefore.route.logicalInstance,
            childCaps:
              childPhysicalAfter.start === childPhysical.start && childPhysicalAfter.end === childPhysical.end,
            childRoot: rootAfter === childRoot,
            draft: rootAfter.querySelector(".draft").value,
            label: rootAfter.querySelector(".label").textContent,
          };
        }
        """,
        [fresh, Parent.class_id, Child.class_id],
    )
    assert result == {
        "topology": "document-body",
        "parentAnchor": True,
        "parentLogical": True,
        "parentCaps": True,
        "childAnchor": True,
        "childLogical": True,
        "childCaps": True,
        "childRoot": True,
        "draft": "document draft",
        "label": "fresh",
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_keyed_transparent_document_root_preserves_its_split_slot_region(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <c-provide #c-key="'provider'" key="context" c-value="value">
            {{ prefix }}
            <main class="transparent-document-parent">
              <input class="transparent-document-input" #c-key="'input'" c-value="value" />
            </main>
          </c-provide>
        """

        def template_data(self, kwargs, slots):
            return {"prefix": kwargs["prefix"], "value": kwargs["value"]}

    messages = _goto(page, serve_live, c, str(Parent(prefix="", value="old")))
    fresh = _fragment(Parent(prefix="\N{NO-BREAK SPACE}", value="fresh"))
    result = page.evaluate(
        """
        async ([html, parentClass]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const current = ownership.get(ownership.revisions()[0]);
          const parentInstance = Array.from(current.registry.renderIds.values()).find(
            (candidate) => candidate.classId === parentClass,
          );
          const parentRoute = ownership.forRender(current.revision, parentInstance.renderId);
          const providerInvocation = Array.from(current.registry.nestedComponents.values()).find(
            (candidate) => candidate.morphKey === "provider",
          );
          const providerInstance = current.registry.renderIds.get(providerInvocation.targetRenderId);
          const region = Array.from(current.registry.slotRegions.values())[0];
          const providerPhysical = current.registry.physicalPlacements.get(providerInstance.key)[0];
          const regionPhysical = current.registry.physicalPlacements.get(region.key)[0];
          const input = document.querySelector(".transparent-document-input");
          input.value = "draft";
          const anchor = internal.getAnchor(parentInstance.renderId);
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentInstance.renderId, swap: "morph", html }],
            },
            { anchor, instance: parentInstance.renderId, event: "refresh" },
          );
          const next = ownership.revisions().map((revision) => ownership.get(revision)).find((candidate) => {
            const instance = Array.from(candidate.registry.renderIds.values()).find(
              (item) => item.classId === parentClass,
            );
            return instance &&
              ownership.forRender(candidate.revision, instance.renderId).anchor === parentRoute.anchor;
          });
          const nextProviderInvocation = Array.from(next.registry.nestedComponents.values()).find(
            (candidate) => candidate.morphKey === "provider",
          );
          const nextProvider = next.registry.renderIds.get(nextProviderInvocation.targetRenderId);
          const nextRegion = Array.from(next.registry.slotRegions.values())[0];
          const nextProviderPhysical = next.registry.physicalPlacements.get(nextProvider.key)[0];
          const nextRegionPhysical = next.registry.physicalPlacements.get(nextRegion.key)[0];
          const freshInput = document.querySelector(".transparent-document-input");
          const prefixNode = document.querySelector(".transparent-document-parent").previousSibling;
          return {
            providerTopology: providerPhysical.topology,
            regionTopology: regionPhysical.topology,
            providerCaps:
              nextProviderPhysical.start === providerPhysical.start &&
              nextProviderPhysical.end === providerPhysical.end,
            regionCaps:
              nextRegionPhysical.start === regionPhysical.start &&
              nextRegionPhysical.end === regionPhysical.end,
            inputKept: freshInput === input,
            prefixKept: prefixNode?.nodeType === Node.TEXT_NODE && prefixNode.nodeValue.includes("\u00a0"),
            value: freshInput.value,
            valueAttr: freshInput.getAttribute("value"),
          };
        }
        """,
        [fresh, Parent.class_id],
    )

    assert result == {
        "providerTopology": "document-body",
        "regionTopology": "document-body",
        "providerCaps": True,
        "regionCaps": True,
        "inputKept": True,
        "prefixKept": True,
        "value": "draft",
        "valueAttr": "fresh",
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_keyed_component_ranges_reorder_across_wrappers_and_receive_fresh_html(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        template = """
          <article class="range-child" c-data-ident="ident">
            <input class="draft" />
            <span class="label">{{ label }}</span>
          </article>
        """

        def template_data(self, kwargs, slots):
            return {"ident": kwargs["ident"], "label": kwargs["label"]}

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="range-parent">
            <c-if cond="variant == 'old'">
              <div class="old-a"><c-child #c-key="'a'" c-ident="'a'" c-label="'A old'" /></div>
              <div class="old-b"><c-child #c-key="'b'" c-ident="'b'" c-label="'B old'" /></div>
            </c-if>
            <c-else>
              <section class="new-b"><c-child #c-key="'b'" c-ident="'b'" c-label="'B fresh'" /></section>
              <aside class="new-a"><strong><c-child #c-key="'a'" c-ident="'a'" c-label="'A fresh'" /></strong></aside>
            </c-else>
          </main>
        """

        def template_data(self, kwargs, slots):
            return {"variant": kwargs["variant"]}

    class Page(Component):
        citry = c
        template = """
          <html><head><title>component ranges</title></head><body><c-parent c-variant="'old'" /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(variant="new"))
    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const parent = document.querySelector(".range-parent");
          const parentId = parent.getAttribute("data-cid").trim().split(" ").at(-1);
          const parentAnchor = internal.getAnchor(parentId);
          const old = {};
          for (const ident of ["a", "b"]) {
            const root = document.querySelector(`[data-ident="${ident}"]`);
            const id = root.getAttribute("data-cid").trim().split(" ").at(-1);
            const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, id));
            const route = ownership.forRender(revision, id);
            const physical = ownership.get(revision).registry.physicalPlacements.get(route.instance.key)[0];
            root.querySelector(".draft").value = `draft-${ident}`;
            old[ident] = {
              root,
              anchor: route.anchor,
              logical: route.logicalInstance,
              start: physical.start,
              end: physical.end,
            };
          }
          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor: parentAnchor, instance: parentId, event: "refresh" },
          );
          const after = {};
          for (const ident of ["a", "b"]) {
            const root = document.querySelector(`[data-ident="${ident}"]`);
            const id = root.getAttribute("data-cid").trim().split(" ").at(-1);
            const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, id));
            const route = ownership.forRender(revision, id);
            const physical = ownership.get(revision).registry.physicalPlacements.get(route.instance.key)[0];
            after[ident] = {
              root: root === old[ident].root,
              anchor: route.anchor === old[ident].anchor,
              logical: route.logicalInstance === old[ident].logical,
              caps: physical.start === old[ident].start && physical.end === old[ident].end,
              draft: root.querySelector(".draft").value,
              label: root.querySelector(".label").textContent,
            };
          }
          return {
            order: Array.from(document.querySelectorAll(".range-child")).map((root) => root.dataset.ident),
            wrappers: Boolean(document.querySelector(".new-b") && document.querySelector(".new-a strong")),
            after,
          };
        }
        """,
        [fresh],
    )

    assert result == {
        "order": ["b", "a"],
        "wrappers": True,
        "after": {
            "a": {
                "root": True,
                "anchor": True,
                "logical": True,
                "caps": True,
                "draft": "draft-a",
                "label": "A fresh",
            },
            "b": {
                "root": True,
                "anchor": True,
                "logical": True,
                "caps": True,
                "draft": "draft-b",
                "label": "B fresh",
            },
        },
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_nested_portable_ranges_survive_successive_mixed_reorder_and_removal(
    page: Any,
    serve_live: Any,
) -> None:
    """Detached portable parents keep nested operational cap pairs usable."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Leaf(Component):
        citry = c
        template = """
          <button class="mixed-range-leaf" c-data-ident="ident">
            <input class="mixed-range-draft" />
            <span>{{ label }}</span>
          </button>
        """

        def template_data(self, kwargs, slots):
            return {"ident": kwargs["ident"], "label": kwargs["label"]}

    class Relay(Component):
        citry = c
        transparent = True
        template = "<c-slot />"

    class Collection(Component):
        citry = c
        template = '<section class="mixed-range-collection"><c-relay><c-slot /></c-relay></section>'

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="mixed-range-parent">
            <c-collection #c-key="'collection'">
              <c-for each="item in primary">
                <c-leaf
                  #c-key="item['ident']"
                  c-ident="item['ident']"
                  c-label="item['label']"
                />
              </c-for>
              <c-relay>
                <c-for each="item in secondary">
                  <c-leaf
                    #c-key="item['ident']"
                    c-ident="item['ident']"
                    c-label="item['label']"
                  />
                </c-for>
              </c-relay>
              <c-if cond="show_nested">
                <c-collection #c-key="'nested'">
                  <c-for each="item in nested">
                    <c-leaf
                      #c-key="item['ident']"
                      c-ident="item['ident']"
                      c-label="item['label']"
                    />
                  </c-for>
                </c-collection>
              </c-if>
            </c-collection>
          </main>
        """

        def template_data(self, kwargs, slots):
            step = kwargs["step"]
            primary_order = ("a", "b", "c") if step == 0 else ("c", "a", "b") if step == 1 else ("c", "a")
            return {
                "primary": tuple({"ident": ident, "label": f"{ident}-{step}"} for ident in primary_order),
                "secondary": tuple(
                    {"ident": ident, "label": f"{ident}-{step}"} for ident in (("x", "y") if step < 2 else ("x",))
                ),
                "show_nested": step < 2,
                "nested": tuple(
                    {"ident": ident, "label": f"{ident}-{step}"}
                    for ident in (("n1", "n2") if step == 0 else ("n2", "n1"))
                ),
            }

    class Page(Component):
        citry = c
        template = """
          <html><head><title>nested portable ranges</title></head><body><c-parent c-step="0" /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fragments = [_fragment(Parent(step=1)), _fragment(Parent(step=2))]
    result = page.evaluate(
        """
        async ([fragments]) => {
          const internal = Citry.events._internal;
          const parent = document.querySelector('.mixed-range-parent');
          const parentId = parent.getAttribute('data-cid').trim().split(' ').at(-1);
          const anchor = internal.getAnchor(parentId);
          const retained = Object.fromEntries(['a', 'c', 'x'].map((ident) => [
            ident,
            document.querySelector(`[data-ident="${ident}"]`),
          ]));
          document.querySelector('[data-ident="a"] .mixed-range-draft').value = 'retained-draft';
          const snapshots = [];
          for (let index = 0; index < fragments.length; index += 1) {
            const currentId = anchor.componentId;
            anchor.epoch = index + 1;
            await internal.applyResult(
              {
                ok: true,
                sendSequence: index + 1,
                actions: [{
                  action: 'render',
                  target: `render:${currentId}`,
                  swap: 'morph',
                  html: fragments[index],
                }],
              },
              { anchor, instance: currentId, event: 'refresh' },
            );
            snapshots.push(Array.from(document.querySelectorAll('.mixed-range-leaf')).map(
              (element) => element.dataset.ident,
            ));
          }
          return {
            snapshots,
            retained: Object.fromEntries(Object.entries(retained).map(([ident, element]) => [
              ident,
              document.querySelector(`[data-ident="${ident}"]`) === element,
            ])),
            draft: document.querySelector('[data-ident="a"] .mixed-range-draft').value,
            temporaryAdapters: document.querySelectorAll(
              'template[data-citry-range-holder],template[data-citry-range-sentinel]',
            ).length,
          };
        }
        """,
        [fragments],
    )

    assert result == {
        "snapshots": [
            ["c", "a", "b", "x", "y", "n2", "n1"],
            ["c", "a", "x"],
        ],
        "retained": {"a": True, "c": True, "x": True},
        "draft": "retained-draft",
        "temporaryAdapters": 0,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_component_range_keys_and_root_element_keys_are_independent(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        template = """
          <article class="axis-child" #c-key="root_key" c-data-ident="ident">
            <input class="draft" />
            <span class="label">{{ label }}</span>
          </article>
        """

        def template_data(self, kwargs, slots):
            return {
                "ident": kwargs["ident"],
                "label": kwargs["label"],
                "root_key": kwargs["root-key"],
            }

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="axis-parent">
            <c-child
              #c-key="'stable-component'"
              c-ident="'stable'"
              c-root-key="stable_root_key"
              c-label="stable_label"
            />
            <c-child
              #c-key="reset_component_key"
              c-ident="'reset'"
              c-root-key="'inside'"
              c-label="reset_label"
            />
          </main>
        """

        def template_data(self, kwargs, slots):
            return dict(kwargs)

    old_props = {
        "stable_root_key": "old-root",
        "stable_label": "stable old",
        "reset_component_key": "old-component",
        "reset_label": "reset old",
    }
    new_props = {
        "stable_root_key": "new-root",
        "stable_label": "stable fresh",
        "reset_component_key": "new-component",
        "reset_label": "reset fresh",
    }

    class Page(Component):
        citry = c
        template = """
          <html><head><title>independent key axes</title></head><body><c-parent c-bind="props" /></body></html>
        """

        def template_data(self, kwargs, slots):
            return {"props": old_props}

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(**new_props))
    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const parent = document.querySelector(".axis-parent");
          const parentId = parent.getAttribute("data-cid").trim().split(" ").at(-1);
          const parentAnchor = internal.getAnchor(parentId);
          const before = {};
          for (const ident of ["stable", "reset"]) {
            const root = document.querySelector(`[data-ident="${ident}"]`);
            const id = root.getAttribute("data-cid").trim().split(" ").at(-1);
            const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, id));
            const route = ownership.forRender(revision, id);
            const physical = ownership.get(revision).registry.physicalPlacements.get(route.instance.key)[0];
            root.querySelector(".draft").value = `draft-${ident}`;
            before[ident] = {
              root,
              anchor: route.anchor,
              logical: route.logicalInstance,
              start: physical.start,
              end: physical.end,
            };
          }
          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor: parentAnchor, instance: parentId, event: "refresh" },
          );
          const after = {};
          for (const ident of ["stable", "reset"]) {
            const root = document.querySelector(`[data-ident="${ident}"]`);
            const id = root.getAttribute("data-cid").trim().split(" ").at(-1);
            const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, id));
            const route = ownership.forRender(revision, id);
            const physical = ownership.get(revision).registry.physicalPlacements.get(route.instance.key)[0];
            after[ident] = {
              rootKept: root === before[ident].root,
              anchorKept: route.anchor === before[ident].anchor,
              logicalKept: route.logicalInstance === before[ident].logical,
              capsKept: physical.start === before[ident].start && physical.end === before[ident].end,
              elementKey: root.getAttribute("data-citry-key"),
              draft: root.querySelector(".draft").value,
              label: root.querySelector(".label").textContent,
            };
          }
          return after;
        }
        """,
        [fresh],
    )

    assert result == {
        "stable": {
            "rootKept": False,
            "anchorKept": True,
            "logicalKept": True,
            "capsKept": True,
            "elementKey": ":new-root",
            "draft": "",
            "label": "stable fresh",
        },
        "reset": {
            "rootKept": False,
            "anchorKept": False,
            "logicalKept": False,
            "capsKept": False,
            "elementKey": ":inside",
            "draft": "",
            "label": "reset fresh",
        },
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_keyed_component_range_survives_multi_root_text_empty_and_element_shapes(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Shape(Component):
        citry = c
        template = """
          <c-if cond="kind == 'multi'">
            <i class="shape-a">{{ label }}</i><b class="shape-b">{{ label }}</b>
          </c-if>
          <c-elif cond="kind == 'text'">text={{ label }}</c-elif>
          <c-elif cond="kind == 'element'"><article class="shape-element">{{ label }}</article></c-elif>
          <c-else></c-else>
        """

        def template_data(self, kwargs, slots):
            return {"kind": kwargs["kind"], "label": kwargs["label"]}

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = (
            '<section class="shape-parent"><c-shape #c-key="\'stable\'" c-kind="kind" c-label="label" /></section>'
        )

        def template_data(self, kwargs, slots):
            return dict(kwargs)

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>keyed shapes</title></head>
            <body><c-parent c-kind="'multi'" c-label="'one'" /></body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fragments = [
        _fragment(Parent(kind="text", label="two")),
        _fragment(Parent(kind="empty", label="three")),
        _fragment(Parent(kind="element", label="four")),
    ]
    result = page.evaluate(
        """
        async ([fragments, shapeClass]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const parent = document.querySelector(".shape-parent");
          const parentId = parent.getAttribute("data-cid").trim().split(" ").at(-1);
          const parentAnchor = internal.getAnchor(parentId);
          const shapeInstance = (revision) => {
            const graph = ownership.get(revision);
            return Array.from(graph.registry.renderIds.values()).find((candidate) => candidate.classId === shapeClass);
          };
          const oldRevision = ownership.revisions().find((revision) => shapeInstance(revision));
          const oldInstance = shapeInstance(oldRevision);
          const oldRoute = ownership.forRender(oldRevision, oldInstance.renderId);
          const oldPhysical = ownership.get(oldRevision).registry.physicalPlacements.get(oldRoute.instance.key)[0];
          const states = [];
          for (let index = 0; index < fragments.length; index += 1) {
            const currentParentId = parentAnchor.componentId;
            parentAnchor.epoch = index + 1;
            await internal.applyResult(
              {
                ok: true,
                sendSequence: index + 1,
                actions: [{
                  action: "render",
                  target: "render:" + currentParentId,
                  swap: "morph",
                  html: fragments[index],
                }],
              },
              { anchor: parentAnchor, instance: currentParentId, event: "refresh" },
            );
            const revision = ownership.revisions().find((candidate) => {
              const instance = shapeInstance(candidate);
              return instance && ownership.forRender(candidate, instance.renderId)?.anchor === oldRoute.anchor;
            });
            const instance = shapeInstance(revision);
            const route = ownership.forRender(revision, instance.renderId);
            const physical = ownership.get(revision).registry.physicalPlacements.get(route.instance.key)[0];
            states.push({
              anchor: route.anchor === oldRoute.anchor,
              logical: route.logicalInstance === oldRoute.logicalInstance,
              caps: physical.start === oldPhysical.start && physical.end === oldPhysical.end,
              roots: Array.from(
                document.querySelectorAll(".shape-a, .shape-b, .shape-element"),
              ).map((el) => el.textContent),
              text: document.querySelector(".shape-parent").textContent.trim(),
            });
          }
          return states;
        }
        """,
        [fragments, Shape.class_id],
    )

    assert result == [
        {"anchor": True, "logical": True, "caps": True, "roots": [], "text": "text=two"},
        {"anchor": True, "logical": True, "caps": True, "roots": [], "text": ""},
        {"anchor": True, "logical": True, "caps": True, "roots": ["four"], "text": "four"},
    ]
    assert not [message for message in messages if message.startswith("error:")]


def test_replace_keeps_keyed_logical_state_but_replaces_the_complete_physical_range(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class ChildState:
        note: str = "server"
        _public = ("note",)

    class Child(Component):
        citry = c
        State = ChildState

        class Events:
            def save(self, state):
                return None

        template = """
          <article class="replace-child">
            <input class="bound" :c-note="save" />
            <input class="browser-only" />
            <span class="label">{{ label }}</span>
          </article>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = '<main class="replace-parent"><c-child #c-key="\'stable\'" c-label="label" /></main>'

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Page(Component):
        citry = c
        template = """
          <html><head><title>replace policy</title></head><body><c-parent c-label="'old'" /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(label="fresh"))
    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const parentRoot = document.querySelector(".replace-parent");
          const childRoot = document.querySelector(".replace-child");
          const parentId = parentRoot.getAttribute("data-cid").trim().split(" ").at(-1);
          const childId = childRoot.getAttribute("data-cid").trim().split(" ").at(-1);
          const parentAnchor = internal.getAnchor(parentId);
          const childEventsAnchor = internal.getAnchor(childId);
          const oldRevision = ownership.revisions().find((revision) => ownership.forRender(revision, childId));
          const oldRoute = ownership.forRender(oldRevision, childId);
          const oldPhysical = ownership.get(oldRevision).registry.physicalPlacements.get(oldRoute.instance.key)[0];
          childEventsAnchor.stateProxy.note = "draft";
          childRoot.querySelector(".browser-only").value = "browser draft";
          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "replace", html }],
            },
            { anchor: parentAnchor, instance: parentId, event: "refresh" },
          );
          const newParentRoot = document.querySelector(".replace-parent");
          const newChildRoot = document.querySelector(".replace-child");
          const newChildId = newChildRoot.getAttribute("data-cid").trim().split(" ").at(-1);
          const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, newChildId));
          const route = ownership.forRender(revision, newChildId);
          const physical = ownership.get(revision).registry.physicalPlacements.get(route.instance.key)[0];
          return {
            parentRootReplaced: newParentRoot !== parentRoot,
            childRootReplaced: newChildRoot !== childRoot,
            capsReplaced: physical.start !== oldPhysical.start && physical.end !== oldPhysical.end,
            generalAnchorKept: route.anchor === oldRoute.anchor,
            logicalKept: route.logicalInstance === oldRoute.logicalInstance,
            eventsAnchorKept: internal.getAnchor(newChildId) === childEventsAnchor,
            pendingKept: childEventsAnchor.pending.note === "draft",
            boundRestored: newChildRoot.querySelector(".bound").value,
            browserDraftReset: newChildRoot.querySelector(".browser-only").value,
            label: newChildRoot.querySelector(".label").textContent,
          };
        }
        """,
        [fresh],
    )

    assert result == {
        "parentRootReplaced": True,
        "childRootReplaced": True,
        "capsReplaced": True,
        "generalAnchorKept": True,
        "logicalKept": True,
        "eventsAnchorKept": True,
        "pendingKept": True,
        "boundRestored": "draft",
        "browserDraftReset": "",
        "label": "fresh",
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_component_key_nullability_and_class_scope_match_the_server_contract(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Item(Component):
        citry = c
        template = '<div class="semantic-item" c-data-ident="ident"><input /><span>{{ label }}</span></div>'

        def template_data(self, kwargs, slots):
            return {"ident": kwargs["ident"], "label": kwargs["label"]}

    class Other(Component):
        citry = c
        template = '<aside class="semantic-item" data-ident="other"><input /><span>{{ label }}</span></aside>'

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="semantic-parent">
            <c-item #c-key="''" c-ident="'empty'" c-label="label" />
            <c-item #c-key="False" c-ident="'false'" c-label="label" />
            <c-item #c-key="0" c-ident="'zero'" c-label="label" />
            <c-item #c-key="None" c-ident="'none'" c-label="label" />
            <c-other #c-key="0" c-label="label" />
            <c-item #c-key="'duplicate'" c-ident="duplicate_first" c-label="label" />
            <c-item #c-key="'duplicate'" c-ident="duplicate_second" c-label="label" />
          </main>
        """

        def template_data(self, kwargs, slots):
            return {
                "label": kwargs["label"],
                "duplicate_first": kwargs["duplicate-first"],
                "duplicate_second": kwargs["duplicate-second"],
            }

    class Page(Component):
        citry = c
        template = """
          <html><head><title>component key values</title></head><body>
            <c-parent c-label="'old'" c-duplicate-first="'duplicate-a'" c-duplicate-second="'duplicate-b'" />
          </body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(
        Parent(
            label="fresh",
            **{"duplicate-first": "duplicate-b", "duplicate-second": "duplicate-a"},
        )
    )
    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const parent = document.querySelector(".semantic-parent");
          const parentId = parent.getAttribute("data-cid").trim().split(" ").at(-1);
          const parentAnchor = internal.getAnchor(parentId);
          const duplicateRoots = Array.from(document.querySelectorAll('[data-ident^="duplicate-"]'));
          duplicateRoots[0].querySelector("input").value = "draft-first";
          duplicateRoots[1].querySelector("input").value = "draft-second";
          const before = {};
          for (const ident of ["empty", "false", "zero", "none", "other"]) {
            const root = document.querySelector(`[data-ident="${ident}"]`);
            const id = root.getAttribute("data-cid").trim().split(" ").at(-1);
            const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, id));
            const route = ownership.forRender(revision, id);
            const physical = ownership.get(revision).registry.physicalPlacements.get(route.instance.key)[0];
            root.querySelector("input").value = `draft-${ident}`;
            before[ident] = { root, anchor: route.anchor, logical: route.logicalInstance, start: physical.start };
          }
          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor: parentAnchor, instance: parentId, event: "refresh" },
          );
          const after = {};
          for (const ident of ["empty", "false", "zero", "none", "other"]) {
            const root = document.querySelector(`[data-ident="${ident}"]`);
            const id = root.getAttribute("data-cid").trim().split(" ").at(-1);
            const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, id));
            const route = ownership.forRender(revision, id);
            const physical = ownership.get(revision).registry.physicalPlacements.get(route.instance.key)[0];
            after[ident] = {
              kept:
                root === before[ident].root &&
                route.anchor === before[ident].anchor &&
                route.logicalInstance === before[ident].logical &&
                physical.start === before[ident].start,
              draft: root.querySelector("input").value,
              label: root.querySelector("span").textContent,
              noComponentDomKey: !root.hasAttribute("data-citry-key"),
            };
          }
          const duplicateAfter = Array.from(document.querySelectorAll('[data-ident^="duplicate-"]'));
          return {
            after,
            duplicates: duplicateAfter.map((root, index) => ({
              samePositionNode: root === duplicateRoots[index],
              ident: root.dataset.ident,
              draft: root.querySelector("input").value,
              label: root.querySelector("span").textContent,
            })),
          };
        }
        """,
        [fresh],
    )

    for ident in ("empty", "false", "zero", "other"):
        assert result["after"][ident] == {
            "kept": True,
            "draft": f"draft-{ident}",
            "label": "fresh",
            "noComponentDomKey": True,
        }
    # None means "no key". Positional unkeyed correspondence still preserves
    # a same-class child at the same direct-child position.
    assert result["after"]["none"] == {
        "kept": True,
        "draft": "draft-none",
        "label": "fresh",
        "noComponentDomKey": True,
    }
    assert result["duplicates"] == [
        {
            "samePositionNode": True,
            "ident": "duplicate-b",
            "draft": "draft-first",
            "label": "fresh",
        },
        {
            "samePositionNode": True,
            "ident": "duplicate-a",
            "draft": "draft-second",
            "label": "fresh",
        },
    ]
    duplicate_warnings = [message for message in messages if "duplicate component key" in message]
    assert len(duplicate_warnings) == 1
    assert "matched in invocation order" in duplicate_warnings[0]
    assert not [message for message in messages if message.startswith("error:")]


def test_fresh_child_queue_ancestry_rebinds_to_preserved_parent_logical_identity(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c

        class Events:
            def ping(self):
                return None

        template = '<button class="queue-child">child</button>'

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = '<section class="queue-parent"><c-child /><span>{{ version }}</span></section>'

        def template_data(self, kwargs, slots):
            return {"version": kwargs["version"]}

    class Page(Component):
        citry = c
        template = (
            "<html><head><title>queue ancestry</title></head><body><c-parent c-version=\"'one'\" /></body></html>"
        )

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(version="two"))
    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const parentRoot = document.querySelector(".queue-parent");
          const oldParentId = parentRoot.getAttribute("data-cid");
          const oldChildId = document.querySelector(".queue-child").getAttribute("data-cid");
          const parentAnchor = internal.getAnchor(oldParentId);
          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + oldParentId, swap: "morph", html }],
            },
            { anchor: parentAnchor, instance: oldParentId, event: "refresh" },
          );
          const childId = document.querySelector(".queue-child").getAttribute("data-cid");
          const childAnchor = internal.getAnchor(childId);
          const parentRelated = ownership._relatedEvents(parentAnchor.clientAnchor);
          const childRelated = ownership._relatedEvents(childAnchor.clientAnchor);
          return {
            childIsFresh: childId !== oldChildId,
            parentSeesChild: parentRelated.includes(childAnchor),
            childSeesParent: childRelated.includes(parentAnchor),
          };
        }
        """,
        [fresh],
    )

    assert result == {"childIsFresh": True, "parentSeesChild": True, "childSeesParent": True}
    assert not [message for message in messages if message.startswith("error:")]


def test_plain_html_self_render_retires_graph_caps_and_both_identities(page: Any, serve_live: Any) -> None:
    citry, _Card, Page = _make_app()
    messages = _goto(page, serve_live, citry, str(Page()))
    result = page.evaluate(
        """
        async () => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const root = document.querySelector(".card");
          const id = root.getAttribute("data-cid");
          const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, id));
          const route = ownership.forRender(revision, id);
          const physical = ownership.get(revision).registry.physicalRegions.get(route.instance.key);
          const start = physical.start;
          const end = physical.end;
          const anchor = internal.getAnchor(id);
          const generalAnchor = route.anchor;
          const logical = route.logicalInstance;
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [
                { action: "render", target: "render:" + id, swap: "morph", html: '<p class="plain">done</p>' },
              ],
            },
            { anchor, instance: id, event: "refresh" },
          );
          return {
            plain: document.querySelector(".plain").textContent,
            eventsRetired: anchor.componentId === null,
            generalRetired: !generalAnchor.active && !logical.active && ownership.forRender(revision, id) === null,
            capsRemoved: !start.isConnected && !end.isConnected,
            cleanupCount: window.__a8.log.filter((entry) => entry.startsWith("cleanup:")).length,
          };
        }
        """
    )

    assert result == {
        "plain": "done",
        "eventsRetired": True,
        "generalRetired": True,
        "capsRemoved": True,
        "cleanupCount": 1,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_correlated_class_change_keeps_browser_anchor_but_mints_logical_identity(page: Any, serve_live: Any) -> None:
    citry, _Card, Page = _make_app()
    c = citry

    class Replacement(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = '<article class="replacement" x-data="{ fresh: 4 }" x-text="fresh"></article>'

    messages = _goto(page, serve_live, citry, str(Page()))
    fresh = _fragment(Replacement())
    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const root = document.querySelector(".card");
          const id = root.getAttribute("data-cid");
          const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, id));
          const route = ownership.forRender(revision, id);
          const physical = ownership.get(revision).registry.physicalRegions.get(route.instance.key);
          const anchor = internal.getAnchor(id);
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + id, swap: "morph", html }],
            },
            { anchor, instance: id, event: "refresh" },
          );
          const newId = anchor.componentId;
          const newRevision = ownership.revisions().find((candidate) => ownership.forRender(candidate, newId));
          const freshRoute = ownership.forRender(newRevision, newId);
          const freshPhysical = ownership.get(newRevision).registry.physicalRegions.get(freshRoute.instance.key);
          return {
            text: document.querySelector(".replacement").textContent,
            browserAnchorKept: freshRoute.anchor === route.anchor,
            logicalReplaced: freshRoute.logicalInstance !== route.logicalInstance && !route.logicalInstance.active,
            capsTransferred: freshPhysical.start === physical.start && freshPhysical.end === physical.end,
            cleanupCount: window.__a8.log.filter((entry) => entry.startsWith("cleanup:")).length,
          };
        }
        """,
        [fresh],
    )

    assert result == {
        "text": "4",
        "browserAnchorKept": True,
        "logicalReplaced": True,
        "capsTransferred": True,
        "cleanupCount": 1,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_class_change_to_component_without_events_keeps_only_general_browser_anchor(
    page: Any,
    serve_live: Any,
) -> None:
    citry, _Card, Page = _make_app()
    c = citry

    class StaticReplacement(Component):
        citry = c
        js = "$component(() => {});"
        template = '<article class="static-replacement" x-data="{}">static</article>'

    messages = _goto(page, serve_live, citry, str(Page()))
    fresh = _fragment(StaticReplacement())
    assert "data-citry-graph" in fresh
    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const root = document.querySelector(".card");
          const oldId = root.getAttribute("data-cid");
          const oldRevision = ownership.revisions().find((candidate) => ownership.forRender(candidate, oldId));
          const oldRoute = ownership.forRender(oldRevision, oldId);
          const eventsAnchor = internal.getAnchor(oldId);
          eventsAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + oldId, swap: "morph", html }],
            },
            { anchor: eventsAnchor, instance: oldId, event: "refresh" },
          );
          const freshRoot = document.querySelector(".static-replacement");
          const newId = freshRoot.getAttribute("data-cid");
          const newRevision = ownership.revisions().find((candidate) => ownership.forRender(candidate, newId));
          const freshRoute = ownership.forRender(newRevision, newId);
          return {
            text: freshRoot.textContent,
            browserAnchorKept: freshRoute.anchor === oldRoute.anchor,
            logicalReplaced:
              freshRoute.logicalInstance !== oldRoute.logicalInstance &&
              !oldRoute.logicalInstance.active,
            eventsRetired:
              eventsAnchor.componentId === null &&
              internal.getAnchor(oldId) === null &&
              internal.getAnchor(newId) === null,
          };
        }
        """,
        [fresh],
    )

    assert result == {
        "text": "static",
        "browserAnchorKept": True,
        "logicalReplaced": True,
        "eventsRetired": True,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_cap_death_retires_no_events_general_identity_and_prunes_fragment_revision(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Island(Component):
        citry = c
        js = """
          $component(() => {
            window.__islandCleanups = window.__islandCleanups || 0;
            return () => { window.__islandCleanups += 1; };
          });
        """
        template = '<aside class="island">island</aside>'

    class Page(Component):
        citry = c
        js = "$component(() => {});"
        template = '<html><head><title>retirement</title></head><body><div id="target"></div></body></html>'

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Island())
    result = page.evaluate(
        """
        async ([html, classId]) => {
          const ownership = Citry.manager.ownership;
          await Citry.events.applyActions([{ action: "render", target: "#target", swap: "inner", html }]);
          const root = document.querySelector(".island");
          const id = root.getAttribute("data-cid");
          const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, id));
          const route = ownership.forRender(revision, id);
          const anchor = route.anchor;
          const logical = route.logicalInstance;
          document.getElementById("target").replaceChildren();
          await new Promise((resolve) => setTimeout(resolve, 0));
          return {
            routeRetired: ownership.forRender(revision, id) === null,
            revisionPruned: !ownership.revisions().includes(revision),
            anchorRetired: !anchor.active && !ownership.anchors().includes(anchor),
            logicalRetired: !logical.active,
            cleanupCount: window.__islandCleanups,
            classId,
          };
        }
        """,
        [fresh, Island.class_id],
    )

    assert result == {
        "routeRetired": True,
        "revisionPruned": True,
        "anchorRetired": True,
        "logicalRetired": True,
        "cleanupCount": 1,
        "classId": Island.class_id,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_cross_revision_supplied_fill_adopts_new_source_route_before_alpine_morph(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = '<section class="slot-card" x-data="{ owner: \'child\' }"><c-slot /></section>'

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="slot-parent" x-data="{ owner: 'parent', count: 1 }">
            <output class="slot-count" x-text="count"></output>
            <c-card #c-key="'card'">
              <button
                class="slot-fill"
                #c-key="'fill-button'"
                x-text="owner + ':' + count"
                @click="count += 1"
              ></button>
            </c-card>
            <span class="slot-version">{{ version }}</span>
          </main>
        """

        def template_data(self, kwargs, slots):
            return {"version": kwargs["version"]}

    class Page(Component):
        citry = c
        template = """
          <html><head><title>fill adoption</title></head><body><c-parent c-version="'one'" /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(version="two"))
    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const root = document.querySelector(".slot-parent");
          const id = root.getAttribute("data-cid").trim().split(" ").at(-1);
          const anchor = internal.getAnchor(id);
          const fill = document.querySelector(".slot-fill");
          fill.click();
          const oldRoute = fill.getAttribute("x-citry-fill-source");
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + id, swap: "morph", html }],
            },
            { anchor, instance: id, event: "refresh" },
          );
          const freshFill = document.querySelector(".slot-fill");
          const freshRoute = freshFill.getAttribute("x-citry-fill-source");
          return {
            fillIdentity: freshFill === fill,
            fillText: freshFill.textContent,
            countText: document.querySelector(".slot-count").textContent,
            version: document.querySelector(".slot-version").textContent,
            owner: Alpine.evaluate(freshFill, "owner"),
            count: Alpine.evaluate(freshFill, "count"),
            routeChanged: oldRoute !== freshRoute,
            routeRevisionLive: ownership.revisions().some((revision) => freshRoute.startsWith(revision + ":")),
          };
        }
        """,
        [fresh],
    )

    assert result == {
        "fillIdentity": True,
        "fillText": "parent:2",
        "countText": "2",
        "version": "two",
        "owner": "parent",
        "count": 2,
        "routeChanged": True,
        "routeRevisionLive": True,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_supplied_slot_region_at_a_different_sibling_window_is_not_correlated(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Wrapper(Component):
        citry = c
        template = """
          <section class="moving-slot-wrapper">
            <c-if cond="side == 'before'">
              <c-slot /><span class="slot-divider">divider</span>
            </c-if>
            <c-else>
              <span class="slot-divider">divider</span><c-slot />
            </c-else>
          </section>
        """

        def template_data(self, kwargs, slots):
            return {"side": kwargs["side"]}

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="moving-slot-parent">
            <c-wrapper #c-key="'wrapper'" c-side="side">
              <input class="moving-slot-input" #c-key="'input'" c-value="value" />
            </c-wrapper>
          </main>
        """

        def template_data(self, kwargs, slots):
            return dict(kwargs)

    class Page(Component):
        citry = c
        template = """
          <html><head><title>moving slot outlet</title></head>
          <body><c-parent c-side="'before'" c-value="'old'" /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(side="after", value="fresh"))
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const parent = document.querySelector(".moving-slot-parent");
          const parentId = parent.getAttribute("data-cid").trim().split(" ").at(-1);
          const anchor = internal.getAnchor(parentId);
          const wrapper = document.querySelector(".moving-slot-wrapper");
          const input = document.querySelector(".moving-slot-input");
          input.value = "draft";
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor, instance: parentId, event: "refresh" },
          );
          const freshInput = document.querySelector(".moving-slot-input");
          return {
            wrapperKept: document.querySelector(".moving-slot-wrapper") === wrapper,
            inputKept: freshInput === input,
            value: freshInput.value,
            order: Array.from(document.querySelector(".moving-slot-wrapper").children).map(
              (element) => element.className,
            ),
          };
        }
        """,
        [fresh],
    )

    assert result == {
        "wrapperKept": True,
        "inputKept": False,
        "value": "fresh",
        "order": ["slot-divider", "moving-slot-input"],
    }
    assert not [message for message in messages if message.startswith("error:")]


@pytest.mark.parametrize(
    ("old_mode", "new_mode", "expected_class", "expected_value"),
    [
        ("fallback", "supplied", "semantic-supplied", "supplied"),
        ("supplied", "fallback", "semantic-fallback", "fallback"),
    ],
)
def test_fallback_and_supplied_slot_regions_do_not_correlate(
    page: Any,
    serve_live: Any,
    old_mode: str,
    new_mode: str,
    expected_class: str,
    expected_value: str,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Wrapper(Component):
        citry = c
        template = """
          <section class="semantic-slot-wrapper">
            <c-slot>
              <input class="semantic-fallback" #c-key="'same-key'" value="fallback" />
            </c-slot>
          </section>
        """

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="semantic-slot-parent">
            <c-if cond="mode == 'fallback'">
              <c-wrapper #c-key="'wrapper'" />
            </c-if>
            <c-else>
              <c-wrapper #c-key="'wrapper'">
                <input class="semantic-supplied" #c-key="'same-key'" value="supplied" />
              </c-wrapper>
            </c-else>
          </main>
        """

        def template_data(self, kwargs, slots):
            return {"mode": kwargs["mode"]}

    class Page(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return {"old_mode": old_mode}

        template = """
          <html><head><title>slot semantics</title></head>
          <body><c-parent c-mode="old_mode" /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(mode=new_mode))
    result = page.evaluate(
        """
        async ([html, expectedClass]) => {
          const internal = Citry.events._internal;
          const parent = document.querySelector(".semantic-slot-parent");
          const parentId = parent.getAttribute("data-cid").trim().split(" ").at(-1);
          const anchor = internal.getAnchor(parentId);
          const wrapper = document.querySelector(".semantic-slot-wrapper");
          const input = wrapper.querySelector("input");
          input.value = "draft";
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor, instance: parentId, event: "refresh" },
          );
          const freshInput = document.querySelector("." + expectedClass);
          return {
            wrapperKept: document.querySelector(".semantic-slot-wrapper") === wrapper,
            inputKept: freshInput === input,
            value: freshInput.value,
          };
        }
        """,
        [fresh, expected_class],
    )

    assert result == {
        "wrapperKept": True,
        "inputKept": False,
        "value": expected_value,
    }
    assert not [message for message in messages if message.startswith("error:")]


@pytest.mark.parametrize("mode", ["development", "production"])
def test_slot_region_provenance_correlates_the_same_in_development_and_production(
    page: Any,
    serve_live: Any,
    mode: str,
) -> None:
    c = Citry(secret=SIGNING_KEY, mode=mode)
    c.set_mounted_prefix("/citry")

    class ShiftWrapper(Component):
        citry = c
        template = '<c-if cond="show"><c-slot /></c-if>'

        def template_data(self, kwargs, slots):
            return {"show": kwargs["show"]}

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="provenance-parent">
            <c-shift-wrapper c-show="show"><span>shifted capture</span></c-shift-wrapper>
            <c-provide #c-key="'provider'" key="context" c-value="value">
              <input class="provenance-input" #c-key="'input'" c-value="value" />
            </c-provide>
          </main>
        """

        def template_data(self, kwargs, slots):
            return dict(kwargs)

    class Page(Component):
        citry = c
        template = """
          <html><head><title>slot provenance parity</title></head>
          <body><c-parent c-show="False" c-value="'old'" /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(show=True, value="fresh"))
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const parent = document.querySelector(".provenance-parent");
          const parentId = parent.getAttribute("data-cid").trim().split(" ").at(-1);
          const anchor = internal.getAnchor(parentId);
          const input = document.querySelector(".provenance-input");
          input.value = "draft";
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor, instance: parentId, event: "refresh" },
          );
          const freshInput = document.querySelector(".provenance-input");
          return {
            inputKept: freshInput === input,
            value: freshInput.value,
            valueAttr: freshInput.getAttribute("value"),
            shifted: document.querySelector(".provenance-parent span").textContent,
          };
        }
        """,
        [fresh],
    )

    assert result == {
        "inputKept": True,
        "value": "draft",
        "valueAttr": "fresh",
        "shifted": "shifted capture",
    }
    assert not [message for message in messages if message.startswith("error:")]


@pytest.mark.parametrize("mode", ["development", "production"])
def test_slot_region_identity_does_not_depend_on_authored_source_location(
    page: Any,
    serve_live: Any,
    mode: str,
) -> None:
    c = Citry(secret=SIGNING_KEY, mode=mode)
    c.set_mounted_prefix("/citry")

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="authored-location-parent">
            <c-if cond="branch == 'first'">
              <c-provide #c-key="'provider'" key="context" c-value="value">
                <input class="authored-location-input" #c-key="'input'" c-value="value" />
              </c-provide>
            </c-if>
            <c-else>
              <c-provide #c-key="'provider'" key="context" c-value="value">
                <input class="authored-location-input" #c-key="'input'" c-value="value" />
              </c-provide>
            </c-else>
          </main>
        """

        def template_data(self, kwargs, slots):
            return dict(kwargs)

    class Page(Component):
        citry = c
        template = """
          <html><head><title>authored slot location parity</title></head>
          <body><c-parent c-branch="'first'" c-value="'old'" /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Parent(branch="second", value="fresh"))
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const parent = document.querySelector(".authored-location-parent");
          const parentId = parent.getAttribute("data-cid").trim().split(" ").at(-1);
          const anchor = internal.getAnchor(parentId);
          const input = document.querySelector(".authored-location-input");
          input.value = "draft";
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor, instance: parentId, event: "refresh" },
          );
          const freshInput = document.querySelector(".authored-location-input");
          return {
            inputKept: freshInput === input,
            value: freshInput.value,
            valueAttr: freshInput.getAttribute("value"),
          };
        }
        """,
        [fresh],
    )

    assert result == {
        "inputKept": True,
        "value": "draft",
        "valueAttr": "fresh",
    }
    assert not [message for message in messages if message.startswith("error:")]
