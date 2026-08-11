"""Three-browser A4 component lifecycle, scope, and init-DAG acceptance."""

from __future__ import annotations

import base64
import json
import re
import time
from typing import TYPE_CHECKING, Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

if TYPE_CHECKING:
    from collections.abc import Callable

pytestmark = pytest.mark.e2e

_DEPS_TAG = re.compile(r'(<script type="application/json" data-citry>)(.*?)(</script>)', re.DOTALL)


def _mutate_dependencies(html: str, mutate: Callable[[dict[str, Any]], None]) -> str:
    match = _DEPS_TAG.search(html)
    assert match is not None
    manifest = json.loads(match.group(2))
    mutate(manifest)
    replacement = f"{match.group(1)}{json.dumps(manifest)}{match.group(3)}"
    return f"{html[: match.start()]}{replacement}{html[match.end() :]}"


def test_nested_scopes_multi_root_shared_root_and_init_dag(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component(({ scope, els }) => {
            window.__a4Order.push("child");
            scope.value = "child";
            window.__a4ChildEls = els;
          });
        """
        template = """
          <span class="child-a" x-text="value"></span>
          <span class="child-b" x-text="value"></span>
        """

    class Rootless(Component):
        citry = c
        js = """
          $component(({ els, scope }) => {
            window.__a4Order.push("rootless");
            window.__a4NestedRootless = { count: els.length, scope };
          });
        """
        template = "rootless text"

    class Parent(Component):
        citry = c
        js = """
          $component(({ scope, els }) => {
            window.__a4Order.push("parent");
            scope.value = "parent";
            window.__a4ParentEls = els;
          });
        """
        template = """
          <section class="parent" x-data="{ value: 'user' }">
            <output class="same-root" x-text="value"></output>
            <c-child />
            <c-rootless />
          </section>
        """

    class SharedInner(Component):
        citry = c
        js = """
          $component(({ scope, els }) => {
            window.__a4Order.push("shared-inner");
            scope.owner = "inner";
            window.__a4SharedInnerEls = els;
          });
        """
        template = '<div class="shared-root" x-text="owner"></div>'

    class SharedOuter(Component):
        citry = c
        js = """
          $component(({ scope, els }) => {
            window.__a4Order.push("shared-outer");
            scope.owner = "outer";
            window.__a4SharedOuterEls = els;
          });
        """
        template = "<c-shared-inner />"

    class Independent(Component):
        citry = c
        js = '$component(() => { window.__a4Order.push("independent"); });'
        template = '<aside class="independent">independent</aside>'

    class Page(Component):
        citry = c
        template = """
          <html><body>
            <script>window.__a4Order = [];</script>
            <c-parent />
            <c-independent />
            <c-shared-outer />
          </body></html>
        """

    # The client must derive ancestry, not rely on dependency-manifest order.
    html = _mutate_dependencies(str(Page()), lambda manifest: manifest["calls"].reverse())
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_function(
        "window.__a4Order?.length === 6 && document.querySelector('.child-b')?.textContent === 'child'"
    )

    result = page.evaluate(
        """
        () => ({
          order: window.__a4Order,
          sameRoot: document.querySelector('.same-root').textContent,
          child: [...document.querySelectorAll('.child-a,.child-b')].map((el) => el.textContent),
          shared: document.querySelector('.shared-root').textContent,
          parentEls: window.__a4ParentEls.length,
          childEls: window.__a4ChildEls.length,
          sameSharedElement:
            window.__a4SharedInnerEls[0] === window.__a4SharedOuterEls[0],
          rootlessEls: window.__a4NestedRootless.count,
        })
        """
    )
    assert result["sameRoot"] == "user"
    assert result["child"] == ["child", "child"]
    assert result["shared"] == "inner"
    assert result["parentEls"] == 1
    assert result["childEls"] == 2
    assert result["sameSharedElement"] is True
    assert result["rootlessEls"] == 0
    assert result["order"].index("parent") < result["order"].index("child")
    assert result["order"].index("parent") < result["order"].index("rootless")
    assert result["order"].index("shared-outer") < result["order"].index("shared-inner")


def test_js_data_seeds_alpine_without_callback_and_clones_each_instance(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class SeedOnly(Component):
        citry = c
        template = """
          <article class="seed-only" x-init="nested.count += 1" x-text="label + ':' + nested.count"></article>
        """

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, object]:
            return {"label": "seed", "nested": {"count": 0}}

    class WithInit(Component):
        citry = c
        js = """
          $component(({ data, scope }) => {
            window.__seededInit.push({
              before: scope.label,
              sameNestedValue: scope.nested.count === data.nested.count,
              ownsProto: Object.prototype.hasOwnProperty.call(scope, "__proto__"),
              unpolluted: ({}).polluted === undefined,
            });
            data.nested.count += 10;
            scope.label = "callback";
          });
        """
        template = """<output class="with-init" x-text="label + ':' + nested.count"></output>"""

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, object]:
            return {
                "label": "server",
                "nested": {"count": 0},
                "__proto__": {"polluted": True},
            }

    class Page(Component):
        citry = c
        template = """
          <html><body>
            <script>window.__seededInit = [];</script>
            <c-seed-only /><c-seed-only />
            <c-with-init /><c-with-init />
          </body></html>
        """

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(
        "window.__seededInit?.length === 2 && "
        "[...document.querySelectorAll('.seed-only')].every((el) => el.textContent === 'seed:1')"
    )

    result = page.evaluate(
        """
        () => {
          const seedRoots = [...document.querySelectorAll('.seed-only')];
          return {
            seedText: seedRoots.map((el) => el.textContent),
            seedGraphsAreDistinct: Alpine.evaluate(seedRoots[0], 'nested') !== Alpine.evaluate(seedRoots[1], 'nested'),
            initText: [...document.querySelectorAll('.with-init')].map((el) => el.textContent),
            init: window.__seededInit,
            objectPrototypeSafe: ({}).polluted === undefined,
          };
        }
        """
    )
    assert result == {
        "seedText": ["seed:1", "seed:1"],
        "seedGraphsAreDistinct": True,
        "initText": ["callback:10", "callback:10"],
        "init": [
            {"before": "server", "sameNestedValue": True, "ownsProto": True, "unpolluted": True},
            {"before": "server", "sameNestedValue": True, "ownsProto": True, "unpolluted": True},
        ],
        "objectPrototypeSafe": True,
    }


def test_malformed_registered_js_data_cancels_without_partial_scope_seed(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class SeedOnly(Component):
        citry = c
        template = '<article class="malformed-seed" x-data="{}"></article>'

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, int]:
            return {"first": 1, "second": 2}

    html = str(SeedOnly())
    invalid = base64.b64encode(b'{"first":1,').decode()
    pattern = re.compile(
        rf'(Citry\.manager\.registerComponentData\("{re.escape(SeedOnly.class_id)}", "[^"]+", atob\(")[^"]+'
    )
    html, replacements = pattern.subn(rf"\g<1>{invalid}", html)
    assert replacements == 1

    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_function("window.Alpine && document.querySelector('.malformed-seed')?._x_dataStack")

    assert (
        page.evaluate(
            """
        () => {
          const el = document.querySelector('.malformed-seed');
          return Alpine.evaluate(el, "typeof first + ':' + typeof second");
        }
        """
        )
        == "undefined:undefined"
    )
    assert any("component data" in message and "call was cancelled" in message for message in messages)


def test_pre_boundary_phase_reads_parent_before_child_isolation(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          Citry.alpine._register({
            beforeBoundary: (el) => {
              window.__a4PreBoundaryCalls = (window.__a4PreBoundaryCalls || 0) + 1;
              if (el.matches?.(".pre-boundary-child")) {
                window.__a4PreBoundaryStacks = {
                  child: el._x_dataStack?.map((layer) => Object.keys(layer)),
                  parent: el.parentElement?._x_dataStack?.map((layer) => Object.keys(layer)),
                };
                window.__a4PreBoundaryValue = Alpine.evaluate(el, "sourceValue");
              }
            },
          });
          $component(({ scope }) => { scope.childValue = "child"; });
        """
        template = """
          <section class="pre-boundary-child">
            <output x-text="typeof sourceValue === 'undefined' ? childValue : 'leaked'"></output>
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html><body><main x-data="{ sourceValue: 'parent-source' }"><c-child /></main></body></html>
        """

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('.pre-boundary-child output')?.textContent === 'child'")
    assert page.evaluate(
        """() => ({
            value: window.__a4PreBoundaryValue,
            calls: window.__a4PreBoundaryCalls,
            stacks: window.__a4PreBoundaryStacks,
          })"""
    ) == {
        "value": "parent-source",
        # Page owns x-data and remains a lifecycle boundary, but its inherited
        # always-empty js_data hook needs no synthetic scope layer. Child still
        # reads the parent's x-data before its own boundary is installed.
        "calls": 2,
        "stacks": {"child": None, "parent": [["sourceValue"]]},
    }
    assert page.locator(".pre-boundary-child output").inner_text() == "child"


def test_rootless_caps_own_effect_and_cleanup_lifetime(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Rootless(Component):
        citry = c

        class Events:
            def ping(self) -> None:
                pass

        js = """
          $component(({ id, scope, els, effect, reactive }) => {
            window.__a4Rootless = { id, scope, els, reactive: reactive({ ok: true }) };
            window.__a4EffectRuns = 0;
            scope.tick = 0;
            effect(() => {
              scope.tick;
              window.__a4EffectRuns += 1;
            });
            return () => {
              window.__a4CleanupRuns = (window.__a4CleanupRuns || 0) + 1;
              window.__a4RunsAtCleanup = window.__a4EffectRuns;
            };
          });
        """
        template = "rootless"

    base = serve_live(c, str(Rootless()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a4Rootless && window.__a4EffectRuns === 1")
    assert page.evaluate("window.__a4Rootless.els.length") == 0
    assert page.evaluate("window.__a4Rootless.reactive.ok") is True
    assert page.evaluate("Citry.events._internal.getAnchor(window.__a4Rootless.id) !== null") is True

    page.evaluate("window.__a4Rootless.scope.tick = 1")
    page.wait_for_function("window.__a4EffectRuns === 2")
    page.evaluate(
        """
        () => {
          const id = window.__a4Rootless.id;
          const revision = Citry.manager.ownership.revisions()[0];
          const route = Citry.manager.ownership.forRender(revision, id);
          const graph = Citry.manager.ownership.get(revision);
          const physical = graph.registry.physicalRegions.get(route.instance.key);
          physical.start.remove();
          physical.end.remove();
        }
        """
    )
    page.wait_for_function("window.__a4CleanupRuns === 1")
    page.wait_for_function("Citry.events._internal.getAnchor(window.__a4Rootless.id) === null")
    runs = page.evaluate("window.__a4EffectRuns")
    page.evaluate("window.__a4Rootless.scope.tick = 2")
    page.wait_for_timeout(50)
    assert page.evaluate("window.__a4EffectRuns") == runs
    assert page.evaluate("window.__a4RunsAtCleanup") == runs
    assert page.evaluate("window.__a4CleanupRuns") == 1


def test_unsupported_async_parent_settles_descendant_and_independent_branch(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = '$component(() => { window.__a4AsyncOrder.push("child"); });'
        template = "<span>child</span>"

    class Parent(Component):
        citry = c
        js = """
          $component(() => {
            window.__a4AsyncOrder.push("parent");
            return Promise.reject(new Error("expected async rejection"));
          });
        """
        template = "<div><c-child /></div>"

    class Independent(Component):
        citry = c
        js = '$component(() => { window.__a4AsyncOrder.push("independent"); });'
        template = "<aside>independent</aside>"

    class Page(Component):
        citry = c
        template = """
          <html><body>
            <script>window.__a4AsyncOrder = [];</script>
            <c-parent />
            <c-independent />
          </body></html>
        """

    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    html = _mutate_dependencies(str(Page()), lambda manifest: manifest["calls"].reverse())
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_function("window.__a4AsyncOrder?.length === 3")

    order = page.evaluate("window.__a4AsyncOrder")
    assert order.index("parent") < order.index("child")
    assert "independent" in order
    assert any("Async component init is unsupported" in message for message in messages)
    page.wait_for_timeout(50)
    assert any("unsupported async component callback" in message for message in messages)
    assert any("expected async rejection" in message for message in messages)


def test_throwing_init_releases_managed_effect_and_settles_child(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = "$component(() => { window.__a4ThrowingChild = true; });"
        template = "<span>child</span>"

    class Parent(Component):
        citry = c
        js = """
          $component(({ scope, effect }) => {
            window.__a4ThrowingScope = scope;
            window.__a4ThrowingEffectRuns = 0;
            scope.value = 0;
            effect(() => {
              scope.value;
              window.__a4ThrowingEffectRuns += 1;
            });
            throw new Error("expected init failure");
          });
        """
        template = "<div><c-child /></div>"

    base = serve_live(c, str(Parent()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a4ThrowingChild === true")
    assert page.evaluate("window.__a4ThrowingEffectRuns") == 1
    page.evaluate("window.__a4ThrowingScope.value = 1")
    page.wait_for_timeout(50)
    assert page.evaluate("window.__a4ThrowingEffectRuns") == 1


def test_retired_waiting_parent_unblocks_its_live_child(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = "$component(() => { window.__a4UnblockedChild = true; });"
        template = '<span class="unblocked-child">child</span>'

    class Parent(Component):
        citry = c
        js = "$component(() => { window.__a4BlockedParent = true; });"
        template = "<section><c-child /></section>"

    def block_parent_data(manifest: dict[str, Any]) -> None:
        for call in manifest["calls"]:
            if base64.b64decode(call[0]).decode() == Parent.class_id:
                call[2] = base64.b64encode(b"missing-parent-data").decode()

    html = _mutate_dependencies(str(Parent()), block_parent_data)
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_function("Citry.manager.ownership.revisions().length === 1")
    page.wait_for_timeout(50)
    assert page.evaluate("window.__a4BlockedParent || false") is False
    assert page.evaluate("window.__a4UnblockedChild || false") is False

    page.evaluate(
        f"""
        () => {{
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const parent = graph.registry.renderIds.values().find(
            (instance) => instance.classId === {json.dumps(Parent.class_id)}
          );
          const physical = graph.registry.physicalRegions.get(parent.key);
          physical.start.remove();
          physical.end.remove();
        }}
        """
    )
    page.wait_for_function("window.__a4UnblockedChild === true")
    assert page.evaluate("window.__a4BlockedParent || false") is False


def test_same_class_replacement_keeps_scope_and_els_but_refires_fresh_render(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        js = """
          $component(({ id, data, scope, els }) => {
            const before = {
              label: scope.label,
              goneType: typeof scope.gone,
              added: scope.added ?? null,
              hadLocal: Boolean(scope.local),
            };
            scope.identity = scope.identity || Symbol("stable-scope");
            scope.local = scope.local || Symbol("callback-only");
            scope.label = "callback-" + data.label;
            window.__a4ReplacementInits.push({ id, data, scope, els, before });
            return () => window.__a4ReplacementCleanups.push(id);
          });
        """
        template = '<article class="card">card</article>'

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            if kwargs["label"] == "old":
                return {"label": "old", "gone": "remove"}
            return {"label": "fresh", "added": "new"}

    fragments = "".join(
        [
            Card(label="old").render().serialize(deps_strategy="fragment"),
            Card(label="fresh").render().serialize(deps_strategy="fragment"),
        ]
    )
    page_html = """
      <html><head><script src="/citry/citry.js"></script></head>
      <body>
        <script>window.__a4ReplacementInits = []; window.__a4ReplacementCleanups = [];</script>
        <div id="target"></div>
      </body></html>
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
    page.wait_for_function("window.__a4ReplacementInits.length === 2")
    page.evaluate(
        """
        () => {
          const revisions = Citry.manager.ownership.revisions();
          const routes = revisions.map((revision) => {
            const renderId = Citry.manager.ownership.get(revision).registry.renderIds.keys()[0];
            return Citry.manager.ownership.forRender(revision, renderId);
          });
          Citry.manager.ownership._replace([{
            fromRevision: revisions[0],
            fromRenderId: routes[0].instance.renderId,
            toRevision: revisions[1],
            toRenderId: routes[1].instance.renderId,
            preserveLogical: true,
          }]);
        }
        """
    )
    page.wait_for_function("window.__a4ReplacementInits.length === 3")

    result = page.evaluate(
        """
        () => {
          const before = window.__a4ReplacementInits.slice(0, 2);
          const oldInit = before.find((entry) => entry.data.label === 'old');
          const provisionalInit = before.find((entry) => entry.data.label === 'fresh');
          const freshInit = window.__a4ReplacementInits[2];
          return {
            freshId: freshInit.id === provisionalInit.id && freshInit.id !== oldInit.id,
            freshData: freshInit.data.label,
            stableScope: freshInit.scope === oldInit.scope,
            stableEls: freshInit.els === oldInit.els,
            pointsAtFreshRoot: freshInit.els[0] === document.querySelectorAll('.card')[1],
            resetServerFieldBeforeCallback: freshInit.before.label,
            removedOldSeed: freshInit.before.goneType,
            addedNewSeed: freshInit.before.added,
            preservedCallbackOnly: freshInit.before.hadLocal,
            callbackOverride: freshInit.scope.label,
            cleanupIds: window.__a4ReplacementCleanups.slice().sort(),
            oldId: oldInit.id,
            provisionalId: provisionalInit.id,
            runtime: Citry.alpine._debug().runtime,
          };
        }
        """
    )
    assert result["freshId"] is True
    assert result["freshData"] == "fresh"
    assert result["stableScope"] is True
    assert result["stableEls"] is True
    assert result["pointsAtFreshRoot"] is True
    assert result["resetServerFieldBeforeCallback"] == "fresh"
    assert result["removedOldSeed"] == "undefined"
    assert result["addedNewSeed"] == "new"
    assert result["preservedCallbackOnly"] is True
    assert result["callbackOverride"] == "callback-fresh"
    assert result["cleanupIds"] == sorted([result["oldId"], result["provisionalId"]])
    assert result["runtime"]["componentDataReferences"] == 1
    assert result["runtime"]["instanceDataOwners"] == 0

    page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions().find((candidate) => {
            const graph = Citry.manager.ownership.get(candidate);
            return graph.registry.renderIds.has(window.__a4ReplacementInits[2].id);
          });
          Citry.manager.ownership._replace([{
            fromRevision: revision,
            fromRenderId: window.__a4ReplacementInits[2].id,
          }]);
        }
        """
    )
    page.wait_for_function("Citry.alpine._debug().runtime.componentDataReferences === 0")
    assert page.evaluate("Citry.alpine._debug().runtime.instanceDataOwners") == 0


def test_class_replacement_and_plain_retirement_dispose_the_complete_lifecycle(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Source(Component):
        citry = c
        js = """
          $component(({ id, scope, els, effect }) => {
            scope.tick = 0;
            window.__a4Transitions.source = { id, scope, els, effectRuns: 0 };
            effect(() => {
              scope.tick;
              window.__a4Transitions.source.effectRuns += 1;
            });
            return () => window.__a4Transitions.userCleanups.push(id);
          });
        """
        template = '<article class="transition-source">source</article>'

    class Target(Component):
        citry = c
        js = """
          $component(({ id, scope, els, effect }) => {
            scope.tick = 0;
            window.__a4Transitions.target = { id, scope, els, effectRuns: 0 };
            effect(() => {
              scope.tick;
              window.__a4Transitions.target.effectRuns += 1;
            });
            return () => window.__a4Transitions.userCleanups.push(id);
          });
        """
        template = '<article class="transition-target">target</article>'

    fragments = "".join(
        [
            Source().render().serialize(deps_strategy="fragment"),
            Target().render().serialize(deps_strategy="fragment"),
        ]
    )
    page_html = """
      <html><head><script src="/citry/citry.js"></script></head>
      <body>
        <script>
          window.__a4Transitions = {
            source: null,
            target: null,
            userCleanups: [],
            resourceCleanups: [],
          };
          Citry.manager.decorateContext((ctx, control) => {
            control?.registerCleanup(() => window.__a4Transitions.resourceCleanups.push(ctx.id));
          });
        </script>
        <div id="target"></div>
      </body></html>
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
    page.wait_for_function("window.__a4Transitions.source && window.__a4Transitions.target")

    page.evaluate(
        """
        () => {
          const revisions = Citry.manager.ownership.revisions();
          const routes = revisions.map((revision) => {
            const renderId = Citry.manager.ownership.get(revision).registry.renderIds.keys()[0];
            return Citry.manager.ownership.forRender(revision, renderId);
          });
          const sourceId = document.querySelector('.transition-source').getAttribute('data-cid');
          const targetId = document.querySelector('.transition-target').getAttribute('data-cid');
          const source = routes.find((route) => route.instance.renderId === sourceId);
          const target = routes.find((route) => route.instance.renderId === targetId);
          window.__a4Transitions.routes = { source, target };
          Citry.manager.ownership._replace([{
            fromRevision: source.revision,
            fromRenderId: source.instance.renderId,
            toRevision: target.revision,
            toRenderId: target.instance.renderId,
            preserveLogical: false,
          }]);
        }
        """
    )
    page.wait_for_function("window.__a4Transitions.userCleanups.length === 1")
    after_class = page.evaluate(
        """
        () => {
          const state = window.__a4Transitions;
          const sourceRuns = state.source.effectRuns;
          state.source.scope.tick += 1;
          return {
            scopesDiffer: state.source.scope !== state.target.scope,
            sourceElsCleared: state.source.els.length === 0,
            targetElsKept: state.target.els[0] === document.querySelector('.transition-target'),
            sourceRuns,
            sourceId: state.source.id,
            targetId: state.target.id,
            userCleanups: state.userCleanups.slice(),
            resourceCleanups: state.resourceCleanups.slice(),
          };
        }
        """
    )
    page.wait_for_timeout(50)
    assert after_class["scopesDiffer"] is True
    assert after_class["sourceElsCleared"] is True
    assert after_class["targetElsKept"] is True
    assert after_class["userCleanups"] == [after_class["sourceId"]]
    assert after_class["resourceCleanups"] == [after_class["sourceId"]]
    assert page.evaluate("window.__a4Transitions.source.effectRuns") == after_class["sourceRuns"]

    page.evaluate(
        """
        () => {
          const route = window.__a4Transitions.routes.target;
          Citry.manager.ownership._replace([{
            fromRevision: route.revision,
            fromRenderId: route.instance.renderId,
            toRevision: null,
            toRenderId: null,
            preserveLogical: false,
          }]);
        }
        """
    )
    page.wait_for_function("window.__a4Transitions.userCleanups.length === 2")
    after_plain = page.evaluate(
        """
        () => {
          const state = window.__a4Transitions;
          const targetRuns = state.target.effectRuns;
          state.target.scope.tick += 1;
          return {
            targetElsCleared: state.target.els.length === 0,
            targetRuns,
            userCleanups: state.userCleanups.slice(),
            resourceCleanups: state.resourceCleanups.slice(),
          };
        }
        """
    )
    page.wait_for_timeout(50)
    assert after_plain["targetElsCleared"] is True
    assert after_plain["userCleanups"] == [after_class["sourceId"], after_class["targetId"]]
    assert after_plain["resourceCleanups"] == [after_class["sourceId"], after_class["targetId"]]
    assert page.evaluate("window.__a4Transitions.target.effectRuns") == after_plain["targetRuns"]


def test_after_start_fragment_holds_alpine_until_callback_scope_is_ready(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Fragment(Component):
        citry = c
        js = """
          $component(({ scope }) => {
            window.__a4DelayedCallback = true;
            scope.message = "ready-before-init";
          });
        """
        template = '<main class="delayed" x-init="window.__a4DelayedInit = message" x-text="message">early</main>'

    fragment = Fragment().render().serialize(deps_strategy="fragment")
    encoded = base64.b64encode(fragment.encode()).decode()
    page_html = f"""
      <html><head>
        <script src="/citry/citry.js"></script>
        <script src="/citry/ext/events/runtime.js"></script>
      </head><body>
        <div id="target"></div>
        <script>
          window.__insertA4Fragment = () => {{
            const template = document.createElement("template");
            template.innerHTML = atob("{encoded}");
            document.getElementById("target").append(template.content);
          }};
        </script>
      </body></html>
    """
    held: list[Any] = []
    page.route("**/citry/cache/*.js", lambda route: held.append(route))
    base = serve_live(c, page_html, "")
    page.goto(base + "/")
    page.wait_for_function("Citry.alpine._isStarted()")
    page.evaluate("window.__insertA4Fragment()")

    deadline = time.monotonic() + 5
    while not held:
        if time.monotonic() > deadline:
            raise AssertionError("the delayed Component.js request did not arrive")
        page.wait_for_timeout(25)
    assert page.evaluate("window.__a4DelayedInit") is None
    assert page.evaluate("document.querySelector('.delayed')._x_marker") is None

    held[0].continue_()
    page.wait_for_function("window.__a4DelayedInit === 'ready-before-init'")
    assert page.locator(".delayed").inner_text() == "ready-before-init"
    assert page.evaluate("window.__a4DelayedCallback") is True
