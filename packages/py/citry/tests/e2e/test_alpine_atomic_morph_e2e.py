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
    canonical = json.dumps(unsigned, separators=(",", ":"), sort_keys=True).encode()
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
        template = '<div class="general-child"><input class="draft"><span>{{ label }}</span></div>'

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
          childRoot.querySelector("input").value = "draft";
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
            label: freshRoot.querySelector("span").textContent,
            callbackIdentity:
              window.__generalKeyed.length === 2 &&
              window.__generalKeyed[0].els === window.__generalKeyed[1].els &&
              window.__generalKeyed[0].scope === window.__generalKeyed[1].scope,
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
        "label": "two",
        "callbackIdentity": True,
    }
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
            <c-card>
              <button class="slot-fill" x-text="owner + ':' + count" @click="count += 1"></button>
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
        "fillText": "parent:2",
        "countText": "2",
        "version": "two",
        "owner": "parent",
        "count": 2,
        "routeChanged": True,
        "routeRevisionLive": True,
    }
    assert not [message for message in messages if message.startswith("error:")]
