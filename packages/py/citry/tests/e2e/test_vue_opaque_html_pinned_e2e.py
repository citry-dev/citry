"""
Browser tests for a pinned opaque HTML block.

An opaque HTML record carries HTML from Python that Vue inserts as one block.
A record with `pinned: true` keeps the nodes of its first render for the life
of the component that shows it, so page code (a chart library, say) can own
and change those nodes without Vue patching or replacing them on a later
render. These tests drive Citry's block component directly with real Vue,
which checks the browser side of that contract whatever the server sends.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component

pytest.importorskip("playwright.sync_api")

# Mounts Citry's opaque HTML block component in a separate Vue app so the test
# controls each record it renders, then records what happens to the DOM nodes.
_DRIVE_BLOCK = """
async ({first, second, hostId}) => {
  const citryApp = __citryRuntime._apps.values().next().value.vueApp;
  const Block = citryApp.component('citry-opaque-html');
  const record = Citry.vue.shallowRef(first);
  const host = document.createElement('div');
  host.id = hostId;
  document.body.append(host);
  Citry.vue.createApp({render: () => Citry.vue.h(Block, {record: record.value})}).mount(host);
  const node = host.querySelector('.block');
  // Page code changes the node it was handed, as a widget library would.
  node.dataset.widget = 'owned';
  node.append(document.createElement('canvas'));
  record.value = second;
  await Citry.vue.nextTick();
  const current = host.querySelector('.block');
  return {
    sameNode: current === node,
    html: host.innerHTML,
    widgetKept: current?.dataset.widget === 'owned' && current.querySelector('canvas') !== null,
  };
}
"""


def _open_citry_page(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class Shell(Component):
        citry = engine
        template = """
            <p id="shell">shell</p>
        """
        js = """
            $component({});
        """

    page.goto(serve_document(Shell().render().serialize()))
    page.wait_for_function("document.querySelector('#shell') && window.__citryRuntime?._apps.size === 1")


@pytest.mark.e2e
def test_a_pinned_block_keeps_its_first_nodes_across_renders(page: Any, serve_document: Any) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    _open_citry_page(page, serve_document)
    first = {"html": '<div class="block">one</div>', "nodeCount": 1, "pinned": True}
    # A later record, pinned or not, does not replace the block the first render made.
    second = {"html": '<div class="block">two</div>', "nodeCount": 1}
    outcome = page.evaluate(_DRIVE_BLOCK, {"first": first, "second": second, "hostId": "pinned"})
    assert outcome["sameNode"] is True
    assert outcome["widgetKept"] is True
    assert "one" in outcome["html"]
    assert "two" not in outcome["html"]
    assert errors == []


@pytest.mark.e2e
def test_an_unpinned_block_follows_new_html(page: Any, serve_document: Any) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    _open_citry_page(page, serve_document)
    first = {"html": '<div class="block">one</div>', "nodeCount": 1}
    second = {"html": '<div class="block">two</div>', "nodeCount": 1}
    outcome = page.evaluate(_DRIVE_BLOCK, {"first": first, "second": second, "hostId": "unpinned"})
    assert outcome["sameNode"] is False
    assert "two" in outcome["html"]
    assert errors == []


@pytest.mark.e2e
@pytest.mark.parametrize(
    "record",
    [
        {"html": "<b>x</b>", "nodeCount": 1, "pinned": False},
        {"html": "<b>x</b>", "nodeCount": 1, "pinned": "yes"},
        {"html": "<b>x</b>", "nodeCount": 1, "keep": True},
    ],
)
def test_a_pinned_key_other_than_true_is_rejected(page: Any, serve_document: Any, record: dict[str, Any]) -> None:
    _open_citry_page(page, serve_document)
    message = page.evaluate(
        """
        (record) => {
          const Block = __citryRuntime._apps.values().next().value.vueApp.component('citry-opaque-html');
          const app = Citry.vue.createApp({render: () => Citry.vue.h(Block, {record})});
          let caught = null;
          app.config.errorHandler = error => { caught = String(error); };
          app.mount(document.createElement('div'));
          return caught;
        }
        """,
        record,
    )
    assert message == "TypeError: invalid opaque HTML record"
