"""Component layouts preserve automatic Alpine data across their authored fills."""

import pytest

pytest.importorskip("pytest_playwright")
pytest.importorskip("uvicorn")

from citry import Citry, Component
from citry.ext.preview import Layout, PreviewExtension
from citry.ext.preview.host import PreviewServer
from citry.ext.preview.rendering import PreviewRenderer
from citry.ext.preview.routes import preview_routes

pytestmark = pytest.mark.e2e


def test_component_page_layout_preserves_automatic_js_data(page, browser_name):
    if browser_name != "chromium":
        pytest.skip("Preview captures use Chromium.")
    app = Citry(extensions=[PreviewExtension])

    class Shell(Component):
        citry = app
        template = """
            <!doctype html>
            <html><head></head><body>
                <header><c-slot name="header" /></header>
                <main><c-slot /></main>
            </body></html>
        """

    class Example(Component):
        citry = app
        template = """
            <section>
                <button @click="helpOpen = !helpOpen">Toggle help</button>
                <p x-show="helpOpen" x-text="notice"></p>
            </section>
        """

        def js_data(self, kwargs, slots):
            return {"helpOpen": False, "notice": "Automatic scope works"}

        class Preview:
            enabled = True
            page_layout = Layout(
                template="""
                    <c-shell>
                        <c-fill name="header"><h1>Example preview</h1></c-fill>
                        <c-fill name="default"><c-slot name="content" /></c-fill>
                    </c-shell>
                """
            )

    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    renderer = PreviewRenderer(app.extensions.get_extension("preview"))
    with PreviewServer(app, preview_routes(renderer)) as server:
        page.goto(f"{server.base_url}/ext/preview/render/{Example.class_id}?variant=default")
        page.wait_for_function(
            "document.querySelector('section')?._x_dataStack?.[0]?.notice === 'Automatic scope works'"
        )
        assert not page.locator("section p").is_visible()
        page.get_by_role("button", name="Toggle help").click()
        page.locator("section p").wait_for(state="visible")
        assert page.locator("section p").inner_text() == "Automatic scope works"
        assert not errors
