"""Browser port of django-components' form-submission example through Events."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import parse_qs

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.events import ViewEvents, actions

pytestmark = pytest.mark.e2e

READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"


def _form_port() -> tuple[Citry, str, type[Component]]:
    engine = Citry(secret="e2e-secret")  # noqa: S106 - deterministic test signing key
    engine.set_mounted_prefix("/citry")

    class ThankYouMessage(Component):
        citry = engine

        class Kwargs:
            name: str

        def template_data(self, kwargs, slots):
            return {"name": kwargs.name}

        template = """
          <p class="thanks">
            Thank you for your submission, {{ name }}!
          </p>
        """

    class ContactForm(Component):
        citry = engine

        class ContactIn:
            name: str = "stranger"

        class Events(ViewEvents):
            def post(self, data: ContactIn):  # noqa: F821
                return actions.Render(
                    ThankYouMessage(name=data.name),
                    target="#thank-you-container",
                    swap="inner",
                )

        def template_data(self, kwargs, slots):
            return {"submit_url": f"/citry/ext/events/e/{type(self).class_id}"}

        template = """
          <section>
            <form class="runtime-form" @c-submit.prevent="post">
              <label for="runtime-name">Name</label>
              <input type="text" name="name" id="runtime-name" />
              <button type="submit">Submit without htmx</button>
            </form>
            <form class="native-form" method="post" c-action="submit_url">
              <label for="name">Name</label>
              <input type="text" name="name" id="name" />
              <button type="submit">Submit through compatibility route</button>
            </form>
            <div id="thank-you-container"></div>
          </section>
        """

    class Page(Component):
        citry = engine
        template = """
          <html>
            <head><title>Events form-submission port</title></head>
            <body><c-contact-form /></body>
          </html>
        """

    return engine, str(Page()), ContactForm


def test_form_submission_port_targets_the_thank_you_fragment_without_htmx(page: Any, serve_live: Any) -> None:
    """The old HTMX target becomes a Citry Render target and keeps the form page."""
    engine, html, contact_form = _form_port()
    requests: list[Any] = []
    page.on("request", lambda request: requests.append(request) if "/ext/events/e/" in request.url else None)
    base = serve_live(engine, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.fill(".runtime-form input[name=name]", "John Doe")
    page.click(".runtime-form button[type=submit]")
    page.wait_for_function("document.querySelector('.thanks')?.innerText.includes('John Doe')")

    assert page.locator(".thanks").inner_text() == "Thank you for your submission, John Doe!"
    assert page.locator(".runtime-form").count() == 1
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert requests[0].url.endswith(f"/e/{contact_form.class_id}/post")
    assert json.loads(requests[0].post_data)["calls"][0]["args"] == {"name": "John Doe"}


def test_view_events_native_form_reaches_the_verb_compatibility_route(page: Any, serve_live: Any) -> None:
    """The initial verb-shaped migration remains available as a native form POST."""
    engine, html, contact_form = _form_port()

    requests: list[dict[str, Any]] = []

    def capture(request: Any) -> None:
        if "/ext/events/e/" not in request.url:
            return
        content_type = request.headers.get("content-type", "")
        body = (
            json.loads(request.post_data)
            if content_type.startswith("application/json")
            else parse_qs(request.post_data)
        )
        requests.append({"method": request.method, "url": request.url, "body": body})

    page.on("request", capture)
    base = serve_live(engine, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.fill(".native-form input[name=name]", "John Doe")
    with page.expect_navigation():
        page.click(".native-form button[type=submit]")
    page.wait_for_function("document.querySelector('.thanks')?.innerText.includes('John Doe')")

    assert page.locator(".thanks").inner_text() == "Thank you for your submission, John Doe!"
    assert len(requests) == 1
    assert requests[0]["method"] == "POST"
    assert requests[0]["url"].endswith(f"/e/{contact_form.class_id}")
    assert requests[0]["body"] == {"name": ["John Doe"]}
