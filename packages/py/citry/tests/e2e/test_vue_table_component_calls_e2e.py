"""Component calls inside table sections and rows, mounted and hydrated in a real browser."""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry._vue.serialization import hydration_admission

pytest.importorskip("playwright.sync_api")


@pytest.mark.e2e
@pytest.mark.parametrize("use_ssr", [False, True], ids=["mounted", "hydrated"])
def test_rows_and_cells_from_components_stay_inside_their_table(page: Any, serve_live: Any, use_ssr: bool) -> None:
    engine = Citry(secret="vue-table-calls-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    # Each row keeps browser state, so a click shows Vue runs the child.
    class Row(Component):
        citry = engine
        template = """
            <tr>
              <td>{{ name }}</td>
              <td>
                <button
                  type="button"
                  @click="picked = !picked"
                  v-text="picked ? 'picked' : 'pick'"
                ></button>
              </td>
            </tr>
        """
        js = """
            $component({ data() { return { picked: false }; } });
        """

        def template_data(self, kwargs, slots):
            return {"name": kwargs["name"]}

    class Cell(Component):
        citry = engine
        template = """
            <td>cell</td>
        """
        js = """
            $component({});
        """

    class Page(Component):
        citry = engine
        template = """
            <main>
              <table id="one">
                <tbody>
                  <c-row c-name="'Ada'" />
                </tbody>
              </table>
              <table id="many">
                <tbody>
                  <c-for each="name in names">
                    <c-row #c-key="name" c-name="name" />
                  </c-for>
                </tbody>
              </table>
              <table id="cells">
                <tbody>
                  <tr><c-cell /></tr>
                </tbody>
              </table>
            </main>
        """
        js = """
            $component({});
        """

        def template_data(self, kwargs, slots):
            return {"names": ["Bo", "Cy"]}

    rendered = Page().render()
    html = rendered.serialize(ssr=use_ssr)
    if use_ssr:
        admission = hydration_admission(rendered)
        assert admission is not None
        assert admission.declines == ()

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.add_init_script(
        """
        globalThis.__citryHydrationDiagnostics = true;
        window.__citryReadyApps = [];
        document.addEventListener('citry:ready', event => window.__citryReadyApps.push(event.detail.appId));
        """
    )
    page.goto(serve_live(engine, html, "") + "/")
    page.wait_for_function("window.__citryReadyApps?.length === 1")
    if use_ssr:
        page.wait_for_function("window.__citryHydrationReport !== undefined")
        report = page.evaluate("window.__citryHydrationReport")
        assert report["mountError"] is None, report
        assert report["mismatchCount"] == 0, report
        assert report["replacedElementCount"] == 0, report

    # Every row and cell sits in its own table's body, not before the table.
    names = "id => [...document.querySelectorAll(`#${id} > tbody > tr > td:first-child`)].map(td => td.textContent)"
    assert page.evaluate(f"({names})('one')") == ["Ada"]
    assert page.evaluate(f"({names})('many')") == ["Bo", "Cy"]
    assert page.evaluate(f"({names})('cells')") == ["cell"]
    assert page.evaluate("document.querySelectorAll('main > tr, main > td').length") == 0

    page.locator("#many button").nth(1).click()
    page.wait_for_function("document.querySelectorAll('#many button')[1].textContent === 'picked'")
    assert page.evaluate("[...document.querySelectorAll('#many button')].map(b => b.textContent)") == [
        "pick",
        "picked",
    ]
    assert faults == []
