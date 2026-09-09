"""The browser accepts one boundary around a transparent caller's nested content."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e


def test_transparent_control_flow_and_fill_have_one_browser_boundary(page: Any, serve_live: Any) -> None:
    app = Citry()
    app.set_mounted_prefix("/citry")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    class Receiver(Component):
        citry = app
        template = """
            <section><c-slot /></section>
        """
        js = """
            $component(() => { window.receiverReady = true; });
        """

    class Document(Component):
        citry = app
        transparent = True
        template = """
            <c-if cond="visible">
                <div><c-receiver><b x-data="{label: 'hello'}" x-text="label"></b></c-receiver></div>
            </c-if>
        """

    base = serve_live(app, Document(visible=True).render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("window.receiverReady && document.querySelector('b').textContent === 'hello'")
    assert page.evaluate("Citry.manager.ownership.revisions().length") == 1
    assert (
        page.evaluate(
            """
        () => {
            const revision = Citry.manager.ownership.revisions()[0];
            return Citry.manager.ownership.get(revision).graphs[0].componentInstances.length;
        }
        """
        )
        == 2
    )
    assert errors == []
