"""Browser acceptance for component-tag range ignore and identity changes."""

from __future__ import annotations

import time
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

SIGNING_KEY = "component-ranges-e2e-secret"
READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"

_INSTALL_HELPERS = """
() => {
  const ownership = Citry.manager.ownership;
  const internal = Citry.events._internal;
  const componentId = (element) => element
    .getAttribute("data-cid")
    .trim()
    .split(/\\s+/)
    .at(-1);
  const nodesBetween = (physical) => {
    const nodes = [];
    for (let node = physical.start.nextSibling; node && node !== physical.end; node = node.nextSibling) {
      nodes.push(node);
    }
    return nodes;
  };
  const rangeForClass = (classId) => {
    for (const revision of ownership.revisions()) {
      const graph = ownership.get(revision);
      const instance = Array.from(graph.registry.renderIds.values()).find(
        (candidate) => candidate.classId === classId,
      );
      if (!instance) continue;
      const route = ownership.forRender(revision, instance.renderId);
      if (!route || !route.logicalInstance.active) continue;
      const physical = graph.registry.physicalPlacements.get(route.instance.key)?.[0];
      if (physical) return { revision, instance, route, physical };
    }
    throw new Error(`missing live range for ${classId}`);
  };
  const render = async (selector, html, swap = "morph") => {
    const root = document.querySelector(selector);
    const id = componentId(root);
    const anchor = internal.getAnchor(id);
    const sequence = anchor.epoch + 1;
    anchor.epoch = sequence;
    await internal.applyResult(
      {
        ok: true,
        sendSequence: sequence,
        actions: [{ action: "render", target: "render:" + id, swap, html }],
      },
      { anchor, instance: id, event: "refresh" },
    );
  };
  window.__componentRanges = { componentId, nodesBetween, rangeForClass, render };
}
"""


def _fragment(component: Component) -> str:
    return component.render().serialize(deps_strategy="fragment")


def _goto(page: Any, serve_live: Any, citry: Citry, html: str) -> list[str]:
    messages: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    base = serve_live(citry, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.evaluate(_INSTALL_HELPERS)
    return messages


def _assert_no_errors(messages: list[str]) -> None:
    assert not [message for message in messages if message.startswith("error:")]


def _wait_for_requests(page: Any, requests: list[Any], count: int) -> None:
    deadline = time.monotonic() + 5
    while len(requests) < count:
        if time.monotonic() > deadline:
            raise AssertionError(f"expected {count} request(s), got {len(requests)}")
        page.wait_for_timeout(25)


@pytest.mark.parametrize("shape", ["single", "multi", "text", "empty", "transparent"])
def test_range_ignore_freezes_every_output_shape(page: Any, serve_live: Any, shape: str) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Single(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

        template = """
          <article class="shape-single">
            <input class="shape-draft" />
            <span>{{ label }}</span>
          </article>
        """

    class Multi(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

        template = """
          <i class="shape-multi-a">{{ label }}-a</i><b class="shape-multi-b">{{ label }}-b</b>
        """

    class TextOnly(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

        template = """
          text={{ label }}
        """

    class EmptyShape(Component):
        citry = c

        # The continuation keeps this fixture exactly empty, without a
        # whitespace text node between its ownership comments.
        template = """\
"""

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"], "shape": kwargs["shape"]}

        template = """
          <main class="shape-parent">
            <c-if cond="shape == 'single'">
              <c-single #c-ignore c-label="label" />
            </c-if>
            <c-elif cond="shape == 'multi'">
              <c-multi #c-ignore c-label="label" />
            </c-elif>
            <c-elif cond="shape == 'text'">
              <c-text-only #c-ignore c-label="label" />
            </c-elif>
            <c-elif cond="shape == 'empty'">
              <c-empty-shape #c-ignore />
            </c-elif>
            <c-else>
              <c-provide
                #c-ignore
                key="shape_theme"
                c-data="{'label': label}"
              >
                <span class="shape-transparent">{{ label }}</span>
              </c-provide>
            </c-else>
          </main>
        """

    class Page(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return {"shape": shape}

        template = """
          <html>
            <head><title>ignored range shapes</title></head>
            <body><c-parent c-shape="shape" c-label="'old'" /></body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    class_ids = {
        "single": Single.class_id,
        "multi": Multi.class_id,
        "text": TextOnly.class_id,
        "empty": EmptyShape.class_id,
        "transparent": c.get("provide").class_id,
    }
    result = page.evaluate(
        """
        async ([html, classIds, shape]) => {
          const helpers = window.__componentRanges;
          const current = helpers.rangeForClass(classIds[shape]);
          const before = {
            anchor: current.route.anchor,
            logical: current.route.logicalInstance,
            start: current.physical.start,
            end: current.physical.end,
            nodes: helpers.nodesBetween(current.physical),
          };
          const draft = document.querySelector(".shape-draft");
          if (draft) draft.value = "client-draft";
          const transparent = document.querySelector(".shape-transparent");
          if (transparent) transparent.setAttribute("data-client", "kept");

          await helpers.render(".shape-parent", html);

          const after = helpers.rangeForClass(classIds[shape]);
          const nodes = helpers.nodesBetween(after.physical);
          const elementRoot = document.querySelector(
            ".shape-single, .shape-multi-a, .shape-multi-b, .shape-transparent",
          );
          return {
            kept: {
              anchor: after.route.anchor === before.anchor,
              logical: after.route.logicalInstance === before.logical,
              caps: after.physical.start === before.start && after.physical.end === before.end,
              nodes:
                nodes.length === before.nodes.length &&
                nodes.every((node, index) => node === before.nodes[index]),
              elementCount: nodes.filter((node) => node.nodeType === Node.ELEMENT_NODE).length,
              text: nodes
                .filter((node) => node.nodeType !== Node.COMMENT_NODE)
                .map((node) => node.textContent)
                .join("")
                .trim(),
            },
            singleDraft: document.querySelector(".shape-draft")?.value ?? null,
            transparentClient: document.querySelector(".shape-transparent")?.getAttribute("data-client") ?? null,
            noRootMarker: !elementRoot?.hasAttribute("data-citry-morph"),
          };
        }
        """,
        [_fragment(Parent(shape=shape, label="new")), class_ids, shape],
    )

    expected = {
        "single": {"elementCount": 1, "text": "old"},
        "multi": {"elementCount": 2, "text": "old-aold-b"},
        "text": {"elementCount": 0, "text": "text=old"},
        "empty": {"elementCount": 0, "text": ""},
        "transparent": {"elementCount": 1, "text": "old"},
    }[shape]
    assert result["singleDraft"] == ("client-draft" if shape == "single" else None)
    assert result["transparentClient"] == ("kept" if shape == "transparent" else None)
    assert result["noRootMarker"] is True
    assert result["kept"] == {"anchor": True, "logical": True, "caps": True, "nodes": True, **expected}
    _assert_no_errors(messages)


def test_old_ignore_is_sticky_and_incoming_ignore_starts_on_the_next_morph(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class PolicyChild(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"], "ident": kwargs["ident"]}

        template = """
          <article class="policy-child" c-data-ident="ident">{{ label }}</article>
        """

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        def template_data(self, kwargs, slots):
            return {
                "sticky": kwargs["sticky"],
                "adding": kwargs["adding"],
                "sticky_ignore": kwargs["sticky-ignore"],
                "adding_ignore": kwargs["adding-ignore"],
            }

        template = """
          <main class="policy-parent">
            <c-if cond="sticky_ignore">
              <c-policy-child
                #c-key="'sticky'"
                #c-ignore
                ident="sticky"
                c-label="sticky"
              />
            </c-if>
            <c-else>
              <c-policy-child #c-key="'sticky'" ident="sticky" c-label="sticky" />
            </c-else>
            <c-if cond="adding_ignore">
              <c-policy-child
                #c-key="'adding'"
                #c-ignore
                ident="adding"
                c-label="adding"
              />
            </c-if>
            <c-else>
              <c-policy-child #c-key="'adding'" ident="adding" c-label="adding" />
            </c-else>
          </main>
        """

    class Page(Component):
        citry = c

        template = """
          <html>
            <head><title>range ignore policy</title></head>
            <body>
              <c-parent
                sticky="sticky-old"
                adding="adding-one"
                c-sticky-ignore="True"
                c-adding-ignore="False"
              />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    first = Parent(
        sticky="sticky-fresh",
        adding="adding-two",
        **{"sticky-ignore": False, "adding-ignore": True},
    )
    second = Parent(
        sticky="sticky-newer",
        adding="adding-three",
        **{"sticky-ignore": False, "adding-ignore": False},
    )
    result = page.evaluate(
        """
        async ([first, second]) => {
          const helpers = window.__componentRanges;
          const sticky = document.querySelector('[data-ident="sticky"]');
          const adding = document.querySelector('[data-ident="adding"]');
          await helpers.render(".policy-parent", first);
          const afterFirst = {
            sticky: document.querySelector('[data-ident="sticky"]').textContent,
            adding: document.querySelector('[data-ident="adding"]').textContent,
            stickyNode: document.querySelector('[data-ident="sticky"]') === sticky,
            addingNode: document.querySelector('[data-ident="adding"]') === adding,
          };
          await helpers.render(".policy-parent", second);
          return {
            afterFirst,
            afterSecond: {
              sticky: document.querySelector('[data-ident="sticky"]').textContent,
              adding: document.querySelector('[data-ident="adding"]').textContent,
              stickyNode: document.querySelector('[data-ident="sticky"]') === sticky,
              addingNode: document.querySelector('[data-ident="adding"]') === adding,
            },
            noDomMarkers: Array.from(document.querySelectorAll(".policy-child")).every(
              (node) => !node.hasAttribute("data-citry-morph"),
            ),
          };
        }
        """,
        [_fragment(first), _fragment(second)],
    )

    assert result == {
        "afterFirst": {
            "sticky": "sticky-old",
            "adding": "adding-two",
            "stickyNode": True,
            "addingNode": True,
        },
        "afterSecond": {
            "sticky": "sticky-old",
            "adding": "adding-two",
            "stickyNode": True,
            "addingNode": True,
        },
        "noDomMarkers": True,
    }
    _assert_no_errors(messages)


@pytest.mark.parametrize("change", ["key", "class", "removal", "ancestor"])
def test_identity_or_ancestor_change_removes_an_ignored_range(page: Any, serve_live: Any, change: str) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class IdentityChild(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

        template = """
          <article class="identity-child">{{ label }}</article>
        """

    class IdentityOther(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

        template = """
          <aside class="identity-other">{{ label }}</aside>
        """

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        def template_data(self, kwargs, slots):
            return {"change": kwargs["change"]}

        template = """
          <main class="identity-parent">
            <c-if cond="change == 'old'">
              <div class="identity-wrapper" #c-key="'wrapper'">
                <c-identity-child #c-key="'stable'" #c-ignore c-label="'old'" />
              </div>
            </c-if>
            <c-elif cond="change == 'key'">
              <div class="identity-wrapper" #c-key="'wrapper'">
                <c-identity-child #c-key="'fresh-key'" c-label="'fresh-key'" />
              </div>
            </c-elif>
            <c-elif cond="change == 'class'">
              <div class="identity-wrapper" #c-key="'wrapper'">
                <c-identity-other #c-key="'stable'" c-label="'fresh-class'" />
              </div>
            </c-elif>
            <c-elif cond="change == 'removal'">
              <div class="identity-wrapper" #c-key="'wrapper'">
                <p class="identity-removed">removed</p>
              </div>
            </c-elif>
            <c-else>
              <section class="identity-wrapper-new" #c-key="'wrapper-new'">
                <c-identity-child #c-key="'stable'" c-label="'fresh-ancestor'" />
              </section>
            </c-else>
          </main>
        """

    class Page(Component):
        citry = c

        template = """
          <html>
            <head><title>ignored range identity</title></head>
            <body><c-parent change="old" /></body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    result = page.evaluate(
        """
        async ([html, change]) => {
          const helpers = window.__componentRanges;
          const oldRoot = document.querySelector(".identity-child");
          const oldWrapper = document.querySelector(".identity-wrapper");
          oldRoot.setAttribute("data-client", "old");
          await helpers.render(".identity-parent", html);
          const selector = change === "class"
            ? ".identity-other"
            : change === "removal"
              ? ".identity-removed"
              : ".identity-child";
          const incoming = document.querySelector(selector);
          return {
            oldRootConnected: oldRoot.isConnected,
            oldWrapperConnected: oldWrapper.isConnected,
            incomingText: incoming.textContent,
            incomingIsOld: incoming === oldRoot,
            clientMarker: incoming.getAttribute("data-client"),
          };
        }
        """,
        [_fragment(Parent(change=change)), change],
    )

    expected_text = {
        "key": "fresh-key",
        "class": "fresh-class",
        "removal": "removed",
        "ancestor": "fresh-ancestor",
    }[change]
    assert result == {
        "oldRootConnected": False,
        "oldWrapperConnected": change != "ancestor",
        "incomingText": expected_text,
        "incomingIsOld": False,
        "clientMarker": None,
    }
    _assert_no_errors(messages)


def test_replace_bypasses_and_can_remove_sticky_range_ignore(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class ReplaceChild(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

        template = """
          <article class="replace-child">{{ label }}</article>
        """

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        def template_data(self, kwargs, slots):
            return {"frozen": kwargs["frozen"], "label": kwargs["label"]}

        template = """
          <main class="replace-parent">
            <c-if cond="frozen">
              <c-replace-child #c-key="'stable'" #c-ignore c-label="label" />
            </c-if>
            <c-else>
              <c-replace-child #c-key="'stable'" c-label="label" />
            </c-else>
          </main>
        """

    class Page(Component):
        citry = c

        template = """
          <html>
            <head><title>replace ignored range</title></head>
            <body><c-parent c-frozen="True" label="old" /></body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = Parent(frozen=False, label="fresh")
    newer = Parent(frozen=False, label="newer")
    result = page.evaluate(
        """
        async ([fresh, newer]) => {
          const helpers = window.__componentRanges;
          const parent = document.querySelector(".replace-parent");
          const child = document.querySelector(".replace-child");
          await helpers.render(".replace-parent", fresh, "replace");
          const afterReplaceParent = document.querySelector(".replace-parent");
          const afterReplaceChild = document.querySelector(".replace-child");
          const afterReplace = {
            parentReplaced: afterReplaceParent !== parent,
            childReplaced: afterReplaceChild !== child,
            text: afterReplaceChild.textContent,
          };
          await helpers.render(".replace-parent", newer);
          return {
            afterReplace,
            afterMorph: {
              childKept: document.querySelector(".replace-child") === afterReplaceChild,
              text: document.querySelector(".replace-child").textContent,
            },
          };
        }
        """,
        [_fragment(fresh), _fragment(newer)],
    )

    assert result == {
        "afterReplace": {"parentReplaced": True, "childReplaced": True, "text": "fresh"},
        "afterMorph": {"childKept": True, "text": "newer"},
    }
    _assert_no_errors(messages)


def test_parent_authored_ignore_skips_child_self_render_and_clears_busy(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class IgnoredSelf(Component):
        citry = c

        class Events:
            def refresh(self):
                return IgnoredSelf(label="fresh")

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

        template = """
          <button class="ignored-self" @c-click="refresh">{{ label }}</button>
        """

    class Page(Component):
        citry = c

        template = """
          <html>
            <head><title>ignored self render</title></head>
            <body><c-ignored-self #c-ignore label="old" /></body>
          </html>
        """

    held: list[Any] = []
    page.route("**/ext/events/e/**", lambda route: held.append(route))
    messages = _goto(page, serve_live, c, str(Page()))
    page.evaluate(
        """
        () => {
          const helpers = window.__componentRanges;
          const root = document.querySelector(".ignored-self");
          window.__ignoredSelfBefore = {
            root,
            id: helpers.componentId(root),
            anchor: Citry.events._internal.getAnchor(helpers.componentId(root)),
          };
          window.__ignoredSelfSend = { settled: false, error: null };
          Citry.events.send(root, "refresh").then(
            () => { window.__ignoredSelfSend.settled = true; },
            (error) => {
              window.__ignoredSelfSend.settled = true;
              window.__ignoredSelfSend.error = String(error?.message || error);
            },
          );
        }
        """
    )

    page.wait_for_timeout(100)
    send_debug = page.evaluate(
        """
        () => ({
          anchor: Boolean(window.__ignoredSelfBefore.anchor),
          settled: window.__ignoredSelfSend.settled,
          error: window.__ignoredSelfSend.error,
        })
        """
    )
    assert send_debug == {"anchor": True, "settled": False, "error": None}
    _wait_for_requests(page, held, 1)
    pending = page.evaluate(
        """
        () => ({
          loading: window.__ignoredSelfBefore.anchor.loading.any,
          rootBusy: window.__ignoredSelfBefore.root.hasAttribute("data-citry-busy"),
        })
        """
    )
    assert pending == {"loading": 1, "rootBusy": True}

    held[0].continue_()
    page.wait_for_function(
        "window.__ignoredSelfSend.settled === true && window.__ignoredSelfBefore.anchor.loading.any === 0"
    )
    result = page.evaluate(
        """
        () => {
          const helpers = window.__componentRanges;
          const root = document.querySelector(".ignored-self");
          const before = window.__ignoredSelfBefore;
          return {
            rootKept: root === before.root,
            idKept: helpers.componentId(root) === before.id,
            anchorKept: Citry.events._internal.getAnchor(before.id) === before.anchor,
            text: root.textContent,
            loading: before.anchor.loading.any,
            busyCleared: !root.hasAttribute("data-citry-busy"),
            error: window.__ignoredSelfSend.error,
          };
        }
        """
    )
    assert result == {
        "rootKept": True,
        "idKept": True,
        "anchorKept": True,
        "text": "old",
        "loading": 0,
        "busyCleared": True,
        "error": None,
    }
    _assert_no_errors(messages)


def test_ordinary_ignore_on_one_root_does_not_freeze_sibling_roots(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class SplitChild(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

        template = """
          <section class="split-frozen" #c-ignore>
            <input class="split-draft" />
            <span class="split-frozen-label">{{ label }}</span>
          </section>
          <p class="split-live">{{ label }}</p>
        """

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

        template = """
          <main class="split-parent"><c-split-child c-label="label" /></main>
        """

    class Page(Component):
        citry = c

        template = """
          <html>
            <head><title>partial ordinary ignore</title></head>
            <body><c-parent c-label="'old'" /></body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    result = page.evaluate(
        """
        async ([html]) => {
          const helpers = window.__componentRanges;
          const frozen = document.querySelector(".split-frozen");
          const live = document.querySelector(".split-live");
          frozen.setAttribute("data-client", "kept");
          frozen.querySelector(".split-draft").value = "client-draft";
          frozen.querySelector(".split-frozen-label").textContent = "client-owned";
          await helpers.render(".split-parent", html);
          const frozenAfter = document.querySelector(".split-frozen");
          const liveAfter = document.querySelector(".split-live");
          return {
            frozenKept: frozenAfter === frozen,
            liveKept: liveAfter === live,
            clientMarker: frozenAfter.getAttribute("data-client"),
            draft: frozenAfter.querySelector(".split-draft").value,
            frozenText: frozenAfter.querySelector(".split-frozen-label").textContent,
            liveText: liveAfter.textContent,
          };
        }
        """,
        [_fragment(Parent(label="fresh"))],
    )

    assert result == {
        "frozenKept": True,
        "liveKept": True,
        "clientMarker": "kept",
        "draft": "client-draft",
        "frozenText": "client-owned",
        "liveText": "fresh",
    }
    _assert_no_errors(messages)
