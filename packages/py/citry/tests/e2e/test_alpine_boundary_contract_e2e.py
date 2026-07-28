"""Browser acceptance for parent-owned component-tag client bindings."""

from __future__ import annotations

import json
import time
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

SIGNING_KEY = "a0-client-props-e2e"
READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"


SUPPLY_CASES = [
    pytest.param(
        ('$c-props="{ count: localCount }"', {}),
        id="direct",
    ),
    pytest.param(
        ('c-$c-props="props_expression"', {"props_expression": "{ count: localCount }"}),
        id="server-dynamic",
    ),
    pytest.param(
        ('c-bind="boundary_attrs"', {"boundary_attrs": {"$c-props": "{ count: localCount }"}}),
        id="spread",
    ),
    pytest.param(
        (
            '$c-props="{ count: 99 }" c-$c-props="props_expression"',
            {"props_expression": "{ count: localCount }"},
        ),
        id="direct-then-server-dynamic",
    ),
    pytest.param(
        ('c-$c-props="props_expression" $c-props="{ count: localCount }"', {"props_expression": "{ count: 99 }"}),
        id="server-dynamic-then-direct",
    ),
]


@pytest.fixture(params=SUPPLY_CASES)
def props_boundary_page(request: Any, page: Any, serve_live: Any) -> Any:
    """Boot one real page and wait until the current component callback ran."""
    supplied_attr, server_data = request.param
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class ChildState:
        marker: str = "child"

    class Child(Component):
        citry = c
        State = ChildState

        class Events:
            def noop(self, state):
                return None

        js = """
          $component({
            props: {
              count: { type: Number, default: 0 },
            },
            init: ({ props, els }) => {
              const apply = () => {
                els.forEach((el) => {
                  el.dataset.suppliedCount = String(props.count);
                });
              };
              apply();
              const stop = Alpine.effect(apply);
              return () => {
                if (typeof stop === "function") stop();
              };
            },
          });
        """
        template = """
          <section class="child">
            <output
              class="scope-owner"
              x-text="typeof localCount === 'undefined' ? 'isolated' : 'leaked'"
            ></output>
          </section>
        """

    class Page(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return dict(server_data)

    Page.template = f"""
      <html>
        <head><title>A0 props acceptance</title></head>
        <body>
          <main x-data="{{ localCount: 1 }}">
            <button class="increment" @click="localCount += 1">increment</button>
            <c-child {supplied_attr} />
          </main>
        </body>
      </html>
    """

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.child')?.hasAttribute('data-supplied-count') === true")
    return page


def test_props_supply_is_reactive_and_child_scope_stays_isolated(props_boundary_page: Any) -> None:
    page = props_boundary_page
    child = page.locator(".child")

    initial_count = child.get_attribute("data-supplied-count")
    assert initial_count == "1"
    assert page.locator(".scope-owner").inner_text() == "isolated"

    page.locator(".increment").click()
    page.wait_for_function("document.querySelector('.child')?.dataset.suppliedCount === '2'")
    assert child.get_attribute("data-supplied-count") == "2"


def test_props_supplier_dom_magics_use_real_source_element(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        js = """
          $component({
            props: {
              sourceId: { type: String, required: true },
              dispatched: { type: Boolean, required: true },
            },
            init: ({ props, effect }) => {
              effect(() => {
                window.__sourceProps = {
                  sourceId: props.sourceId,
                  dispatched: props.dispatched,
                };
              });
            },
          });
        """
        template = '<section class="source-magic-child">child</section>'

    class Parent(Component):
        citry = c
        template = """
          <main
            id="props-source"
            x-data="{ enabled: false }"
            @props-signal="window.__propsSignal = { source: $el.id, value: $event.detail.value }"
          >
            <button class="enable-source-props" @click="enabled = true">enable</button>
            <c-child
              $c-props="enabled
                ? { sourceId: $el.id, dispatched: $dispatch('props-signal', { value: 4 }) }
                : { sourceId: $el.id, dispatched: false }"
            />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__sourceProps?.sourceId === 'props-source'")
    assert page.evaluate("window.__sourceProps") == {"sourceId": "props-source", "dispatched": False}

    page.locator(".enable-source-props").click()
    page.wait_for_function("window.__sourceProps?.dispatched === true && window.__propsSignal")
    assert page.evaluate("window.__propsSignal") == {"source": "props-source", "value": 4}


def _capture_event_requests(page: Any) -> list[dict[str, Any]]:
    captured: list[dict[str, Any]] = []

    def record(request: Any) -> None:
        if "/ext/events/" not in request.url or request.url.endswith("/runtime.js"):
            return
        captured.append({"url": request.url, "body": json.loads(request.post_data or "null")})

    page.on("request", record)
    return captured


def _wait_requests(page: Any, captured: list[dict[str, Any]], count: int) -> None:
    deadline = time.monotonic() + 5
    while len(captured) < count:
        if time.monotonic() > deadline:
            msg = f"expected {count} event request(s), saw {len(captured)}"
            raise AssertionError(msg)
        page.wait_for_timeout(25)


def test_alpine_boundary_handler_uses_parent_lexical_and_child_physical_scope(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        template = """
          <section
            class="alpine-child"
            x-data="{ owner: 'child' }"
            x-ref="childRef"
            @physical-ping="window.__physicalPing = $el.className"
          >
            <button class="alpine-trigger">run</button>
          </section>
        """

    class Parent(Component):
        citry = c
        template = """
          <main id="source-root" x-data="{ owner: 'parent', hits: 0 }" x-ref="parentRef">
            <output class="parent-hits" x-text="hits"></output>
            <c-child
              @click="(window.__alpineClientBinding = {
                owner, ref: $refs.parentRef.id, root: $root.id, el: $el.className,
                target: $event.target.className, current: $event.currentTarget.className
              }, hits += 1, $dispatch('physical-ping'))"
            />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.locator(".alpine-trigger").click()
    page.wait_for_function("window.__alpineClientBinding && window.__physicalPing")

    assert page.evaluate("window.__alpineClientBinding") == {
        "owner": "parent",
        "ref": "source-root",
        "root": "source-root",
        "el": "alpine-child",
        "target": "alpine-trigger",
        "current": "alpine-child",
    }
    assert page.locator(".parent-hits").inner_text() == "1"
    assert page.evaluate("window.__physicalPing") == "alpine-child"


def test_citry_boundary_handler_evaluates_only_args_and_dispatches_from_parent(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class ChildState:
        owner: str = "child-state"
        _public = ("owner",)

    class Child(Component):
        citry = c
        State = ChildState

        class SaveIn:
            selected: bool = False
            owner: str = ""
            ref: str = ""
            physical: str = ""

        class Events:
            def save_selection(self, data: SaveIn, state):  # noqa: F821
                return None

        template = """
          <article class="citry-child" x-data="{ selected: false }">
            <button class="citry-trigger">save</button>
          </article>
        """

    class ParentState:
        owner: str = "parent-state"
        _public = ("owner",)

    class Parent(Component):
        citry = c
        State = ParentState

        class SaveIn:
            selected: bool = False
            owner: str = ""
            ref: str = ""
            physical: str = ""

        class Events:
            def save_selection(self, data: SaveIn, state):  # noqa: F821
                return None

        template = """
          <main id="citry-source" x-data="{ selected: true }" x-ref="parentRef">
            <c-child
              @c-click="save_selection({
                selected, owner: $state.owner, ref: $refs.parentRef.id, physical: $el.className
              })"
            />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    captured = _capture_event_requests(page)
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.locator(".citry-trigger").click()
    _wait_requests(page, captured, 1)

    request = captured[0]
    assert f"/e/{Parent.class_id}/save_selection" in request["url"]
    assert f"/e/{Child.class_id}/save_selection" not in request["url"]
    assert request["body"]["calls"][0]["args"] == {
        "selected": True,
        "owner": "parent-state",
        "ref": "citry-source",
        "physical": "citry-child",
    }


def test_citry_boundary_submit_merges_form_fields_with_explicit_args(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        template = """
          <form class="boundary-submit-form">
            <input name="email" value="form@lose" />
            <input name="quantity" type="number" value="4" />
            <button class="boundary-submit" type="submit">save</button>
          </form>
        """

    class Parent(Component):
        citry = c

        class SaveIn:
            email: str = ""
            quantity: int = 0
            extra: str = ""

        class Events:
            def save(self, data: SaveIn):  # noqa: F821
                return None

        template = """
          <main>
            <c-child @c-submit.prevent="save({ email: 'expr@win', extra: 'from-expr' })" />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    captured = _capture_event_requests(page)
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.evaluate(
        "document.addEventListener('submit', "
        "(event) => { window.__boundarySubmitPrevented = event.defaultPrevented; })"
    )
    page.locator(".boundary-submit").click()
    _wait_requests(page, captured, 1)

    request = captured[0]
    assert f"/e/{Parent.class_id}/save" in request["url"]
    assert request["body"]["calls"][0]["args"] == {
        "email": "expr@win",
        "quantity": 4,
        "extra": "from-expr",
    }
    assert page.evaluate("window.__boundarySubmitPrevented") is True


def test_props_update_policy_readonly_defaults_diagnostics_and_recovery(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component({
            props: {
              required: { type: String, required: true },
              optional: { type: Number, default: 5 },
              tags: {
                type: Array,
                default: () => {
                  window.__factoryCalls = (window.__factoryCalls || 0) + 1;
                  return [];
                },
              },
            },
            init: ({ props, effect }) => {
              window.__propsView = props;
              window.__propSnapshots = [];
              window.__tagDefault = props.tags;
              try { props.optional = 99; }
              catch (error) { window.__readonlyError = error.message; }
              effect(() => {
                window.__propSnapshots.push({
                  required: props.required,
                  optional: props.optional,
                  tagsStable: props.tags === window.__tagDefault,
                });
              });
            },
          });
        """
        template = '<section class="policy-child">policy</section>'

    class Parent(Component):
        citry = c
        template = """
          <main x-data="{ stage: 0 }">
            <button class="next-stage" @click="stage += 1">next</button>
            <c-child
              $c-props="stage === 0
                ? { required: 'ok', optional: 1, unknown: 'ignored' }
                : stage === 1
                  ? { required: 9, optional: 2 }
                  : stage === 2
                    ? { required: 'recovered' }
                    : stage === 3
                      ? null
                      : stage === 4
                        ? { required: 'again' }
                        : { required: 9 }"
            />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    messages: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__propSnapshots?.length >= 1")

    assert page.evaluate("window.__propSnapshots.at(-1)") == {
        "required": "ok",
        "optional": 1,
        "tagsStable": True,
    }
    assert page.evaluate("window.__factoryCalls") == 1
    assert "props are read-only" in page.evaluate("window.__readonlyError")
    assert sum("ignored unknown supplied prop 'unknown'" in message for message in messages) == 1

    page.locator(".next-stage").click()
    page.wait_for_function("window.__propSnapshots.at(-1)?.optional === 2")
    invalid = page.evaluate("window.__propSnapshots.at(-1)")
    assert invalid == {"required": None, "optional": 2, "tagsStable": True}
    assert sum("prop 'required' expected String" in message for message in messages) == 1

    page.locator(".next-stage").click()
    page.wait_for_function("window.__propSnapshots.at(-1)?.required === 'recovered'")
    assert page.evaluate("window.__propSnapshots.at(-1)") == {
        "required": "recovered",
        "optional": 5,
        "tagsStable": True,
    }
    assert page.evaluate("window.__factoryCalls") == 1

    page.locator(".next-stage").click()
    page.wait_for_function("window.__propSnapshots.at(-1)?.tagsStable === false")
    failed_bag = page.evaluate("window.__propSnapshots.at(-1)")
    assert failed_bag == {"required": None, "optional": None, "tagsStable": False}

    page.locator(".next-stage").click()
    page.wait_for_function("window.__propSnapshots.at(-1)?.required === 'again'")
    assert page.evaluate("window.__factoryCalls") == 1

    page.locator(".next-stage").click()
    page.wait_for_function("window.__propSnapshots.at(-1)?.required === undefined")
    assert sum("prop 'required' expected String" in message for message in messages) == 2


@pytest.mark.parametrize(
    ("props_declaration", "expected_error"),
    [
        pytest.param("false", "props declaration must be an object", id="falsy-declaration"),
        pytest.param(
            "{ stamp: { default: new Date() } }",
            "object or array default; use a per-instance factory",
            id="non-plain-object-default",
        ),
    ],
)
def test_invalid_props_declarations_skip_init(
    page: Any,
    serve_live: Any,
    props_declaration: str,
    expected_error: str,
) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        js = f"""
          $component({{
            props: {props_declaration},
            init: () => {{ window.__invalidPropsInit = true; }},
          }});
        """
        template = '<section class="invalid-props-child">child</section>'

    class Page(Component):
        citry = c
        template = "<html><body><c-child /></body></html>"

    messages: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    deadline = time.monotonic() + 5
    while not any(expected_error in message for message in messages):
        if time.monotonic() > deadline:
            raise AssertionError(f"missing props diagnostic containing {expected_error!r}: {messages!r}")
        page.wait_for_timeout(25)

    assert page.evaluate("window.__invalidPropsInit || false") is False
    assert sum(expected_error in message for message in messages) == 1


def test_rejected_boundary_promises_are_observed_and_diagnosed(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class PropsChild(Component):
        citry = c
        js = """
          $component({
            props: { value: { type: Number, required: true } },
            init: () => { window.__promisePropsInit = true; },
          });
        """
        template = '<section class="promise-props-child">props</section>'

    class HandlerChild(Component):
        citry = c
        template = '<button class="promise-handler-child">handler</button>'

    class Parent(Component):
        citry = c
        template = """
          <main>
            <c-props-child $c-props="Promise.reject(new Error('props boom'))" />
            <c-handler-child @click="Promise.reject(new Error('client binding boom'))" />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    messages: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")

    deadline = time.monotonic() + 5
    while not any("supplier must synchronously return a plain object" in message for message in messages):
        if time.monotonic() > deadline:
            raise AssertionError(f"missing Promise supplier diagnostic: {messages!r}")
        page.wait_for_timeout(25)
    assert page.evaluate("window.__promisePropsInit || false") is False

    page.locator(".promise-handler-child").click()
    deadline = time.monotonic() + 5
    while not any("relocated Alpine handler '@click' failed" in message for message in messages):
        if time.monotonic() > deadline:
            raise AssertionError(f"missing rejected client-binding diagnostic: {messages!r}")
        page.wait_for_timeout(25)
    page.wait_for_timeout(50)
    assert page_errors == []


def test_rootless_props_init_and_poll_survive_dom_handler_diagnostics(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component({
            props: { value: { type: Number, required: true } },
            init: ({ props, els }) => {
              window.__rootless = { value: props.value, roots: els.length };
            },
          });
        """
        template = "rootless text"

    class Parent(Component):
        citry = c

        class PollIn:
            value: int = 0

        class Events:
            def save(self, data: PollIn):  # noqa: F821
                return None

            def poll(self, data: PollIn):  # noqa: F821
                return None

        template = """
          <main x-data="{ value: 7 }">
            <c-child
              $c-props="{ value }"
              @click="value += 1"
              @c-click="save({ value })"
              @c-poll.1s="poll({ value })"
            />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    messages: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    captured = _capture_event_requests(page)
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__rootless")

    assert page.evaluate("window.__rootless") == {"value": 7, "roots": 0}
    dom_errors = [message for message in messages if "rendered no HTML element root" in message]
    assert len(dom_errors) == 2
    assert any("@click" in message for message in dom_errors)
    assert any("@c-click" in message for message in dom_errors)

    _wait_requests(page, captured, 1)
    request = captured[0]
    assert f"/e/{Parent.class_id}/poll" in request["url"]
    assert request["body"]["calls"][0]["args"] == {"value": 7}


def test_top_level_nested_rootless_document_body_boundary_supplies_props_and_poll(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component({
            props: { value: { type: Number, required: true } },
            init: ({ props, els }) => {
              window.__documentBodyBoundary = { value: props.value, roots: els.length };
            },
          });
        """
        template = "rootless child"

    class Parent(Component):
        citry = c

        class PollIn:
            value: int = 0

        class Events:
            def poll(self, data: PollIn):  # noqa: F821
                return None

        template = '<c-child $c-props="{ value: 7 }" @c-poll.1s="poll({ value: 7 })" />'

    captured = _capture_event_requests(page)
    base = serve_live(c, str(Parent()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__documentBodyBoundary")

    assert page.evaluate("window.__documentBodyBoundary") == {"value": 7, "roots": 0}
    assert page.evaluate(
        f"""
        () => {{
          const graph = Citry.manager.ownership.get(Citry.manager.ownership.revisions()[0]);
          return [{json.dumps(Parent.class_id)}, {json.dumps(Child.class_id)}].map((classId) => {{
            const instance = graph.registry.renderIds.values().find((candidate) => candidate.classId === classId);
            return graph.registry.physicalRegions.get(instance.key).topology;
          }});
        }}
        """
    ) == ["document-body", "document-body"]

    _wait_requests(page, captured, 1)
    request = captured[0]
    assert f"/e/{Parent.class_id}/poll" in request["url"]
    assert request["body"]["calls"][0]["args"] == {"value": 7}


def test_multi_root_boundary_once_state_is_shared_across_roots(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        template = """
          <button class="group-root-one">one</button>
          <button class="group-root-two">two</button>
        """

    class Parent(Component):
        citry = c
        template = """
          <main x-data="{ hits: 0 }">
            <output class="group-hits" x-text="hits"></output>
            <c-child @click.once="hits += 1" />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.locator(".group-root-one").click()
    page.locator(".group-root-two").click()
    page.wait_for_timeout(50)

    assert page.locator(".group-hits").inner_text() == "1"


def test_shared_physical_root_still_uses_source_component_scope(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        template = '<button class="shared-root">shared</button>'

    class Parent(Component):
        citry = c
        js = """
          $component(({ scope, effect }) => {
            scope.hits = 0;
            effect(() => { window.__sharedHits = scope.hits; });
          });
        """
        template = '<c-child @click="hits += 1" />'

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__sharedHits === 0")
    root = page.locator(".shared-root")
    assert len((root.get_attribute("data-cid") or "").split()) >= 2

    root.click()
    page.wait_for_function("window.__sharedHits === 1")


def test_queued_citry_boundary_handler_keeps_source_owner_at_dequeue(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c

        class SaveIn:
            marker: str = ""

        class Events:
            def save(self, data: SaveIn):  # noqa: F821
                return None

        template = '<button class="queued-child">child</button>'

    class Parent(Component):
        citry = c

        class SaveIn:
            marker: str = ""

        class Events:
            def block(self):
                return None

            def save(self, data: SaveIn):  # noqa: F821
                return None

        template = """
          <main>
            <button class="queue-blocker" @c-click="block">block</button>
            <c-child @c-click="save({ marker: 'parent-owned' })" />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    captured = _capture_event_requests(page)
    held: list[Any] = []
    page.route(f"**/e/{Parent.class_id}/block", lambda route: held.append(route))
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    page.locator(".queue-blocker").click()
    deadline = time.monotonic() + 5
    while not held:
        if time.monotonic() > deadline:
            raise AssertionError("the blocking source request was not held")
        page.wait_for_timeout(25)

    page.locator(".queued-child").click()
    page.wait_for_timeout(100)
    assert len(captured) == 1
    held[0].continue_()
    _wait_requests(page, captured, 2)

    assert f"/e/{Parent.class_id}/save" in captured[1]["url"]
    assert f"/e/{Child.class_id}/save" not in captured[1]["url"]
    assert captured[1]["body"]["calls"][0]["args"] == {"marker": "parent-owned"}


def test_queued_rootless_poll_is_cancelled_when_target_is_removed(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        template = "rootless child"

    class Parent(Component):
        citry = c

        class Events:
            def block(self):
                return None

            def poll(self):
                return None

        template = """
          <main>
            <button class="rootless-queue-blocker" @c-click="block">block</button>
            <c-child @c-poll.1s="poll" />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    captured = _capture_event_requests(page)
    held: list[Any] = []
    page.route(f"**/e/{Parent.class_id}/block", lambda route: held.append(route))
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    page.locator(".rootless-queue-blocker").click()
    deadline = time.monotonic() + 5
    while not held:
        if time.monotonic() > deadline:
            raise AssertionError("the blocking source request was not held")
        page.wait_for_timeout(25)
    page.wait_for_function(
        "Citry.events._internal.queue.snapshot().some((node) => node.event === 'poll' && !node.dispatched)",
        timeout=5_000,
    )

    page.evaluate(
        f"""
        () => {{
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const child = graph.registry.renderIds.values().find(
            (instance) => instance.classId === {json.dumps(Child.class_id)}
          );
          const physical = graph.registry.physicalRegions.get(child.key);
          physical.start.remove();
          physical.end.remove();
        }}
        """
    )
    held[0].continue_()
    page.wait_for_function("Citry.events._internal.queue.snapshot().length === 0")
    page.wait_for_timeout(100)

    assert len(captured) == 1
    assert f"/e/{Parent.class_id}/block" in captured[0]["url"]
