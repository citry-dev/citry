from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for
from citry.util.html import Markup

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e


def test_opaque_html_updates_as_keyed_inert_static_ranges(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="opaque-html-e2e-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    bodies = (
        "",
        '<button id="opaque-a" @click="globalThis.__opaqueRan=true">{{ unsafe }}</button>',
        '<button id="opaque-a" @click="globalThis.__opaqueRan=true">{{ unsafe }}</button>',
        "",
        '<span id="opaque-a">A</span><!-- middle --><span id="opaque-b">B</span>',
        '<span id="opaque-b">B</span><span id="opaque-a">A</span>',
    )

    class Opaque(Component):
        citry = engine
        template = (
            '<main><button id="advance" @c-click="advance">advance</button><section id="zone">{{ bo'
            "dy }}</section></main>"
        )

        class State:
            stage: int = 0

        class Events:
            def advance(self, state: Opaque.State):
                state.stage += 1
                return Opaque(stage=state.stage)

        def template_data(self, kwargs, slots):
            return {
                # This test passes fixed trusted markup to exercise opaque HTML updates.
                "body": Markup(bodies[kwargs.get("stage", 0)])  # noqa: S704 -- trusted test fixture
            }

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    base = serve_live(engine, Opaque(stage=0).render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("CitryStable._apps.values().next().value.revision === 0")
    assert page.locator("#zone").inner_html() == ""

    page.locator("#advance").click()
    page.wait_for_selector("#opaque-a")
    assert page.locator("#opaque-a").text_content() == "{{ unsafe }}"
    page.locator("#opaque-a").click()
    assert page.evaluate("globalThis.__opaqueRan") is None
    page.evaluate("globalThis.__firstOpaque = document.querySelector('#opaque-a')")

    page.locator("#advance").click()
    page.wait_for_function("CitryStable._apps.values().next().value.revision === 2")
    assert page.evaluate("globalThis.__firstOpaque === document.querySelector('#opaque-a')")

    page.locator("#advance").click()
    page.wait_for_function("CitryStable._apps.values().next().value.revision === 3")
    assert page.locator("#zone").inner_html() == ""

    page.locator("#advance").click()
    page.wait_for_function("document.querySelector('#zone')?.textContent === 'AB'")
    assert page.locator("#zone > span").count() == 2
    page.locator("#advance").click()
    page.wait_for_function("document.querySelector('#zone')?.textContent === 'BA'")
    assert page.locator("#zone > span").all_inner_texts() == ["B", "A"]
    assert faults == []


def test_root_opaque_html_mounts_multiple_roots_without_a_wrapper(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class OpaqueRoot(Component):
        citry = engine
        template = "{{ body }}"
        js = "$component({data(){return {mounted: true};}});"
        css = ".opaque-root { color: var(--opaque-color); }"

        def template_data(self, kwargs, slots):
            return {
                "body": Markup(
                    '<span id="first-root" class="opaque-root">A</span>'
                    '<span id="second-root" class="opaque-root">B</span>'
                )
            }

        def css_data(self, kwargs, slots):
            return {"opaque-color": "rgb(0, 128, 0)"}

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_document(OpaqueRoot().render().serialize()))
    page.wait_for_selector("#first-root")
    assert page.locator('[id^="citry-vue-"] > span').count() == 2
    assert page.locator("#first-root").text_content() == "A"
    assert page.locator("#second-root").text_content() == "B"
    for selector in ("#first-root", "#second-root"):
        names = page.locator(selector).evaluate("node => node.getAttributeNames()")
        assert len([name for name in names if name.startswith("data-ccss-")]) == 1
        assert page.locator(selector).evaluate("node => getComputedStyle(node).color") == "rgb(0, 128, 0)"
    assert faults == []
