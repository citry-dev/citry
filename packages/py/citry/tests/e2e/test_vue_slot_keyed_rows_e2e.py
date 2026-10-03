"""Browser proof that keyed rows inside a supplied slot keep their Vue instances."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

pytestmark = pytest.mark.e2e

# Each server event re-renders the board with the next list. The rows sit in a
# fill the board supplies to a panel, so the slot name the panel exposes must
# stay the same across renders for Vue to patch the rows instead of recreating
# them.
_STEPS = (
    ("reorder", ["c", "a", "b"]),
    ("insert", ["c", "x", "a", "b"]),
    ("remove", ["c", "x", "b"]),
)


def test_keyed_rows_in_a_supplied_slot_survive_reorder_insert_and_remove(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-slot-keyed-rows-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    board_render_id = ""
    step_index = 0

    class Row(Component):
        citry = engine
        template = """
            <label class="row" c-data-row="value">
              <input class="local-input" v-model="local">
              <output class="instance-id" v-text="instanceId"></output>
            </label>
        """
        js = """
            $component({data(){
              const instanceId = (globalThis.__slotRowCount = (globalThis.__slotRowCount || 0) + 1);
              return {local: 'fresh', instanceId};
            }});
        """

        def template_data(self, kwargs, slots):
            return {"value": kwargs["value"]}

    class Panel(Component):
        citry = engine
        template = """
            <section class="panel"><c-slot /></section>
        """

    class Board(Component):
        citry = engine
        template = """
            <c-panel>
              <c-for each="value in values">
                <c-row #c-key="value" c-value="value" />
              </c-for>
            </c-panel>
        """

        def template_data(self, kwargs, slots):
            nonlocal board_render_id
            board_render_id = self.id
            return {"values": kwargs["values"]}

    class Controller(Component):
        citry = engine
        template = """
            <button id="next" @c-click="advance">next</button>
        """

        class Events:
            def advance(self):
                nonlocal step_index
                _, values = _STEPS[step_index]
                step_index += 1
                return actions.Render(Board(values=values), target=f"render:{board_render_id}")

    class Page(Component):
        citry = engine
        template = """
            <main>{{ controller }}{{ board }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"controller": Controller(), "board": Board(values=["a", "b", "c"])}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")
    page.wait_for_function("document.querySelectorAll('.row').length === 3")

    def rows() -> list[str]:
        return page.eval_on_selector_all(".row", "rows => rows.map(row => row.dataset.row)")

    def remember() -> None:
        # Store each row's element, input and Vue instance number so the next
        # step can prove it is the same object, not an equal copy.
        page.evaluate(
            """() => {
              globalThis.__slotRows = Object.fromEntries(
                [...document.querySelectorAll('.row')].map(row => {
                  const input = row.querySelector('.local-input');
                  return [row.dataset.row, {
                    row,
                    input,
                    instanceId: row.querySelector('.instance-id').textContent,
                  }];
                }),
              );
            }"""
        )

    for key in rows():
        page.locator(f'.row[data-row="{key}"] .local-input').fill(f"local-{key}")
    remember()

    for name, values in _STEPS:
        before = rows()
        page.locator("#next").click()
        page.wait_for_function(
            "expected => [...document.querySelectorAll('.row')].map(row => row.dataset.row).join(',') === expected",
            arg=",".join(values),
        )
        kept = [key for key in values if key in before]
        # A surviving row keeps its DOM nodes, its Vue instance and the text
        # typed into it. Losing any of these means Vue recreated the row.
        survivors = page.evaluate(
            """keys => keys.map(key => {
              const row = document.querySelector(`.row[data-row="${key}"]`);
              const input = row.querySelector('.local-input');
              const saved = globalThis.__slotRows[key];
              return {
                key,
                sameRow: row === saved.row,
                sameInput: input === saved.input,
                sameInstance: row.querySelector('.instance-id').textContent === saved.instanceId,
                value: input.value,
              };
            })""",
            kept,
        )
        assert survivors == [
            {
                "key": key,
                "sameRow": True,
                "sameInput": True,
                "sameInstance": True,
                "value": f"local-{key}",
            }
            for key in kept
        ], name
        added = [key for key in values if key not in before]
        for key in added:
            # A new row starts from its own initial state.
            assert page.locator(f'.row[data-row="{key}"] .local-input').input_value() == "fresh", name
            page.locator(f'.row[data-row="{key}"] .local-input').fill(f"local-{key}")
        remember()

    assert page.locator(".panel").count() == 1
    assert faults == []


def test_component_inside_a_transparent_wrapper_in_a_fill_mounts(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class Box(Component):
        citry = engine
        name = "box"
        template = """
            <section class="box"><c-slot /></section>
        """

    class Group(Component):
        citry = engine
        name = "group"
        transparent = True
        template = """
            <c-slot />
        """

    class Page(Component):
        citry = engine
        # The inner box call sits in Page's fill for the outer box, wrapped by
        # a transparent component. Its call and fill must stay in Page's
        # definition for Vue to find them.
        template = """
            <!doctype html>
            <html><head></head><body>
              <c-box #c-key="'outer'">
                <b id="outer">outer</b>
                <c-group><c-box #c-key="'inner'"><i id="inner">inner</i></c-box></c-group>
              </c-box>
              <c-js />
            </body></html>
        """
        js = """
            $component({data(){return {}}});
        """

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_document(Page().render().serialize(deps_strategy="document")))
    page.wait_for_function("document.querySelectorAll('.box').length === 2")

    assert page.locator(".box #outer").inner_text() == "outer"
    assert page.locator(".box .box #inner").inner_text() == "inner"
    assert faults == []
