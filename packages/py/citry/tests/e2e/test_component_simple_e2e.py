"""Simple templates preserve the browser relationships of their ordinary caller."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("dynamic", [False, True])
def test_simple_content_under_transparent_owner_initializes_in_browser(
    page: Any, serve_live: Any, dynamic: bool
) -> None:
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

    class Box(Component):
        citry = app
        simple = True
        template = """
            <div><c-receiver><b x-data="{label: 'hello'}" x-text="label"></b></c-receiver></div>
        """

    class Document(Component):
        citry = app
        transparent = True
        template = """
            <c-if cond="dynamic"><c-component c-is="target" /></c-if>
            <c-else><c-box /></c-else>
        """

    base = serve_live(app, Document(dynamic=dynamic, target=Box).render().serialize(), "")
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
