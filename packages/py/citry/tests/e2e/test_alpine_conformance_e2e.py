"""A10 cross-browser protocol, deployment, and bounded-growth canaries."""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

SIGNING_KEY = "a10-conformance-secret"
READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"
_GRAPH_TAG = re.compile(r'<script type="application/json" data-citry-graph>(.*?)</script>', re.DOTALL)
_CAP = re.compile(r"<!--citry:g1:[0-9a-f]{64}:\d+:[ir]:\d+:[se]-->")


def _fragment(component: Component) -> str:
    return component.render().serialize(deps_strategy="fragment")


def _make_app() -> tuple[Citry, type[Component], type[Component], type[Component]]:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        _data_nonce = 0
        js = """
          $component({
            props: { count: { type: Number, required: true } },
            init: ({ data, props, scope, effect }) => {
              scope.seen = 0;
              scope.dataNonce = data.nonce;
              effect(() => { scope.seen = props.count; });
              return () => { window.__a10Cleanups = (window.__a10Cleanups || 0) + 1; };
            },
          });
        """
        template = """
          <button class="child-first" :data-nonce="dataNonce" x-text="seen"></button>
          <span class="child-second" x-text="seen"></span>
        """

        def js_data(self, kwargs: dict[str, object], slots: object) -> dict[str, object]:
            component_type = type(self)
            component_type._data_nonce += 1
            return {"nonce": component_type._data_nonce}

    class ParentState:
        count: int = 1

    class Parent(Component):
        citry = c
        State = ParentState
        js = """
          $component(({ scope, effect }) => {
            scope.parentRuns = 0;
            effect(() => { scope.parentRuns += 1; });
          });
        """

        class Events:
            def refresh(self, state):
                return None

        template = """
          <section class="parent" x-data="{ outer: 1 }">
            <input class="bound-control" :c-count="refresh" />
            <button class="local-event" @c-click="refresh">refresh</button>
            <c-child
              $c-props="{ count: outer }"
              @click="outer += 1"
              @c-probe="refresh({ count: outer })"
            />
          </section>
        """

    class Page(Component):
        citry = c
        template = "<html><head><title>A10</title></head><body><c-parent /></body></html>"

    return c, Child, Parent, Page


def test_protocol_caps_and_runtime_versions_survive_real_document_delivery(page: Any, serve_live: Any) -> None:
    citry, _Child, _Parent, Page = _make_app()
    html = str(Page())
    graph_match = _GRAPH_TAG.search(html)
    assert graph_match is not None
    manifest = json.loads(graph_match.group(1))
    assert manifest["protocol"] == "citry-client-graph/1"
    assert manifest["delimiters"] == {"format": "citry:g1"}

    base = serve_live(citry, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    result = page.evaluate(
        """
        ([revision]) => {
          const graph = Citry.manager.ownership.get(revision);
          const physicals = Array.from(graph.registry.physicalRegions.values());
          return {
            revisionActive: Citry.manager.ownership.revisions().includes(revision),
            capCount: physicals.length,
            capsConnected: physicals.every((range) => range.start.isConnected && range.end.isConnected),
            capsAreComments: physicals.every(
              (range) => range.start.nodeType === Node.COMMENT_NODE && range.end.nodeType === Node.COMMENT_NODE,
            ),
            capsCarryRevision: physicals.every(
              (range) => range.start.data.includes(revision) && range.end.data.includes(revision),
            ),
            hooks: Citry.alpine._debug().hooks,
          };
        }
        """,
        [manifest["revision"]],
    )

    assert result == {
        "revisionActive": True,
        "capCount": sum(len(graph["componentInstances"]) + len(graph["slotRegions"]) for graph in manifest["graphs"]),
        "capsConnected": True,
        "capsAreComments": True,
        "capsCarryRevision": True,
        "hooks": {"installs": 1, "roots": 1, "init": 1, "morph": 0, "starts": 1},
    }


def test_stripped_comment_caps_fail_before_graph_activation(page: Any, serve_live: Any) -> None:
    citry, _Child, _Parent, Page = _make_app()
    html = _CAP.sub("", str(Page()))

    base = serve_live(citry, html, "")
    with page.expect_console_message(
        lambda message: message.type == "error" and "missing physical cap" in message.text
    ) as cap_error:
        page.goto(base + "/")

    result = page.evaluate(
        """
        () => ({
          revisions: Citry.manager.ownership.revisions().length,
          anchors: Citry.manager.ownership.anchors().length,
          lifecycles: Citry.alpine._debug().runtime.lifecycles,
          eventsAnchors: Citry.events._internal.debug().anchors,
          childInitialized: document.querySelector('.child-second')?.textContent !== '',
        })
        """
    )
    assert result == {
        "revisions": 0,
        "anchors": 0,
        "lifecycles": 0,
        "eventsAnchors": 0,
        "childInitialized": False,
    }
    diagnostic = cap_error.value.text
    assert "Preserve Citry ownership comments beginning with citry:g1 through minification" in diagnostic


def test_unsafe_result_render_ids_are_rejected_before_selector_construction(page: Any, serve_live: Any) -> None:
    citry, _Child, _Parent, Page = _make_app()
    messages: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    page.on("pageerror", lambda error: page_errors.append(str(error)))

    base = serve_live(citry, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    result = page.evaluate(
        """
        async () => {
          const invalid = [
            { action: 'state', targetRenderId: 'MixedCase', stateToken: 'ignored' },
            { action: 'event', eventName: 'probe', target: 'render:MixedCase' },
            { action: 'render', target: 'render:MixedCase', swap: 'remove', html: '' },
          ];
          const rejected = [];
          for (const action of invalid) {
            try {
              await Citry.events.applyActions([action]);
              rejected.push(null);
            } catch (error) {
              rejected.push(String(error && (error.message || error)));
            }
          }
          return {
            connected: document.querySelector('.parent')?.isConnected === true,
            rejected,
          };
        }
        """
    )

    assert result["connected"] is True
    assert len(result["rejected"]) == 3
    assert all("invalid citry-events/1 action array" in message for message in result["rejected"])
    assert page_errors == []
    assert not [message for message in messages if "unsafe" in message and "render ID" in message]


def test_effect_listener_and_graph_counts_stay_bounded_through_morph_churn(page: Any, serve_live: Any) -> None:
    citry, Child, Parent, Page = _make_app()
    initial_html = str(Page())
    fragments = [_fragment(Parent()) for _ in range(25)]
    # The final graph is fresh, but its js_data hash repeats the first morph.
    # The content-addressed variables script must remain a page cache hit.
    Child._data_nonce = 1
    fragments[-1] = _fragment(Parent())
    messages: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    base = serve_live(citry, initial_html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.child-second')?.textContent === '1'")

    result = page.evaluate(
        """
        async ([htmls]) => {
          const ownership = Citry.manager.ownership;
          const events = Citry.events._internal;
          const parent = document.querySelector('.parent');
          const initialId = parent.getAttribute('data-cid');
          const anchor = events.getAnchor(initialId);
          const snapshots = [];
          const snapshot = () => ({
            alpine: Citry.alpine._debug(),
            events: events.debug(),
          });
          snapshots.push(snapshot());

          for (let index = 0; index < htmls.length; index += 1) {
            const currentId = anchor.componentId;
            anchor.epoch = index + 1;
            await events.applyResult(
              {
                ok: true,
                sendSequence: index + 1,
                actions: [{ action: 'render', target: 'render:' + currentId, swap: 'morph', html: htmls[index] }],
              },
              { anchor, instance: currentId, event: 'refresh' },
            );
            await new Promise((resolve) => setTimeout(resolve, 0));
            snapshots.push(snapshot());
          }
          return {
            snapshots,
            childText: document.querySelector('.child-second').textContent,
            cleanups: window.__a10Cleanups || 0,
          };
        }
        """,
        [fragments],
    )

    snapshots = result["snapshots"]
    baseline = snapshots[0]
    assert baseline["alpine"]["runtime"]["propsEffects"] == 1
    assert baseline["alpine"]["runtime"]["managedEffects"] == 2
    assert baseline["alpine"]["runtime"]["rootBindings"] >= 2
    assert baseline["alpine"]["runtime"]["nativeListenerTargets"] >= 4
    assert baseline["events"]["delegatedListenerTypes"] >= 2
    assert baseline["events"]["formEffects"] == 1
    assert baseline["events"]["queuedCalls"] == 0

    stable_alpine = [
        "registrations",
        "componentDataReferences",
        "instanceDataOwners",
        "lifecycles",
        "liveInstances",
        "browserAnchors",
        "componentBoundaries",
        "fillSources",
        "rootGroups",
        "rootBindings",
        "nativeListenerTargets",
        "propsEffects",
        "managedEffects",
        "managedResources",
        "ambientMagicFrames",
        "graphFailures",
        "pendingCalls",
    ]
    stable_events = [
        "anchors",
        "renderIds",
        "classes",
        "delegatedListenerTypes",
        "polledElements",
        "anchorIntervals",
        "elementIntervals",
        "boundControls",
        "formEffects",
        "pendingFlushes",
        "queuedCalls",
    ]
    churn_revision_count = snapshots[1]["alpine"]["runtime"]["ownershipRevisions"]
    assert churn_revision_count == 2
    for index, snapshot in enumerate(snapshots[1:], start=1):
        assert {key: snapshot["alpine"]["hooks"][key] for key in ("installs", "roots", "init", "starts")} == {
            key: baseline["alpine"]["hooks"][key] for key in ("installs", "roots", "init", "starts")
        }
        assert snapshot["alpine"]["hooks"]["morph"] == index
        assert snapshot["alpine"]["runtime"]["ownershipRevisions"] == churn_revision_count
        assert snapshot["alpine"]["runtime"]["ownershipStates"] == churn_revision_count
        assert snapshot["alpine"]["runtime"]["dependencyClaims"] == churn_revision_count
        assert snapshot["alpine"]["runtime"]["componentData"] == (
            baseline["alpine"]["runtime"]["componentData"] + min(index, len(fragments) - 1)
        )
        assert snapshot["alpine"]["runtime"]["replayRevisions"] == (
            baseline["alpine"]["runtime"]["replayRevisions"] + index
        )
        assert {key: snapshot["alpine"]["runtime"][key] for key in stable_alpine} == {
            key: baseline["alpine"]["runtime"][key] for key in stable_alpine
        }
        assert {key: snapshot["events"][key] for key in stable_events} == {
            key: baseline["events"][key] for key in stable_events
        }

    assert result["childText"] == "1"
    assert result["cleanups"] == len(fragments)
    assert not [message for message in messages if message.startswith("error:")]
