from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

pytestmark = pytest.mark.e2e


def test_keyed_transparent_wrappers_move_descendants_and_keep_runtime_events(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-transparent-key-move-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    rows_render_id = ""
    ping_calls = 0

    class Row(Component):
        citry = engine
        template = (
            '<label><input class="local-input" v-model="local">'
            '<output class="instance-id" v-text="instanceId"></output></label>'
        )
        js = """$component({data(){
          const instanceId = (globalThis.__rowInstanceCount = (globalThis.__rowInstanceCount || 0) + 1);
          return {local: this.value, instanceId};
        }});"""

        def js_data(self, kwargs, slots):
            return {"value": kwargs["value"]}

    class Rows(Component):
        citry = engine
        template = """
            <section id="rows">
                <c-for each="value in values">
                    <c-provide key="theme" c-data="{}" #c-key="value">
                        <section class="keyed-row" c-data-row="value">
                            <c-Row c-value="value" />
                            <button class="runtime-event" c-bind="runtimeAttrs">ping</button>
                        </section>
                    </c-provide>
                </c-for>
            </section>
        """

        class Events:
            def ping(self):
                nonlocal ping_calls
                ping_calls += 1

        def template_data(self, kwargs, slots):
            nonlocal rows_render_id
            rows_render_id = self.id
            return {**kwargs, "runtimeAttrs": {"@c-click": "ping"}}

    class Controller(Component):
        citry = engine
        template = '<button id="reorder" @c-click="reorder">reorder</button>'

        class Events:
            def reorder(self):
                return actions.Render(Rows(values=["b", "a"]), target=f"render:{rows_render_id}")

    class Page(Component):
        citry = engine
        template = "<main>{{ controller }}{{ rows }}</main>"

        def template_data(self, kwargs, slots):
            return {"controller": Controller(), "rows": Rows(values=["a", "b"])}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")
    page.wait_for_function("document.querySelectorAll('.keyed-row').length === 2")

    for key in ("a", "b"):
        page.locator(f'.keyed-row[data-row="{key}"] .local-input').fill(f"local-{key}")

    page.evaluate(
        """() => {
          globalThis.__transparentRows = Object.fromEntries(
            [...document.querySelectorAll('.keyed-row')].map(row => {
              const input = row.querySelector('.local-input');
              return [row.dataset.row, {
                row,
                input,
                component: input.__vueParentComponent,
                instanceId: row.querySelector('.instance-id').textContent,
              }];
            }),
          );
        }"""
    )

    page.locator("#reorder").click()
    page.wait_for_function(
        "() => [...document.querySelectorAll('.keyed-row')].map(row => row.dataset.row).join(',') === 'b,a'"
    )

    assert [page.locator(".keyed-row").nth(index).get_attribute("data-row") for index in range(2)] == ["b", "a"]
    assert [page.locator(f'.keyed-row[data-row="{key}"] .local-input').input_value() for key in ("a", "b")] == [
        "local-a",
        "local-b",
    ]
    assert (
        page.evaluate(
            """() => ['a', 'b'].every(key => {
              const row = document.querySelector(`.keyed-row[data-row="${key}"]`);
              const input = row.querySelector('.local-input');
              const before = globalThis.__transparentRows[key];
              return row === before.row
                && input === before.input
                && input.__vueParentComponent === before.component
                && row.querySelector('.instance-id').textContent === before.instanceId;
            })"""
        )
        is True
    )

    with page.expect_response("**/ext/events/call") as event_response:
        page.locator('.keyed-row[data-row="b"] .runtime-event').click()
    response = event_response.value
    event_call = response.request.post_data_json["calls"][0]
    assert response.ok
    assert event_call["handlerName"] == "ping"
    assert ping_calls == 1
    assert faults == []
