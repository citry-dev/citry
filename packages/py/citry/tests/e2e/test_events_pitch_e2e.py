"""
Browser e2e for the three pitch examples of docs/design/events.md section 2,
run end to end through the real client runtime (WP17.2's honesty check: the
examples pass at, or under, their design-doc line counts).

- The counter: a click runs the server handler and the morphed button shows
  the incremented count.
- Live search: the two-way ``:c-query.debounce.300ms="refresh"`` binding
  debounces typing into one call carrying the update plus the handler, the
  result list renders under the input, and the focused input keeps its value
  and caret while the list changes under it (design section 2's trace, step
  10).
- The contact form: a failed submit answers the 422 ``fields`` map, the
  inline ``$error?.fieldErrors.email`` display shows it, nothing re-renders (the
  typed input survives), and a corrected submit renders the success branch.

The components are the design doc's code blocks verbatim; the one line added
to each is the ``citry = c`` registration the test harness needs (the doc
snippets assume an app-wide engine). The line-count test pins that honesty:
each fixture stays at or under its doc block's line count plus that one
line.

Uses the live-server harness (conftest ``serve_live``) like the sibling
suites. Locked strings were observed from the real runtime first, then
locked.
"""

from __future__ import annotations

import inspect
import json
import re
import time
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.events import EventError

pytestmark = pytest.mark.e2e

SIGNING_KEY = "e2e-secret"

READY = "window.Citry && Citry.events && Citry.events._internal && Citry.events._internal.alpineStarted === true"

c = Citry(secret=SIGNING_KEY)
c.set_mounted_prefix("/citry")


def find_products(query: str) -> list[Any]:
    """The pitch's stand-in product search: three deterministic hits per query."""
    return [type("Product", (), {"name": f"{query}-{n}"})() for n in range(3)]


SENT_EMAILS: list[tuple[str, str]] = []


def send_contact_email(name: str, email: str) -> None:
    """The pitch's stand-in mailer: record instead of sending."""
    SENT_EMAILS.append((name, email))


class Counter(Component):
    citry = c

    class Kwargs:
        count: int = 0

    class State(Kwargs):
        pass

    class Events:
        def increment(self, state):
            state.count += 1
            return Counter(count=state.count)

    def template_data(self, kwargs, slots):
        return {"count": kwargs.count}

    template = """
      <button @c-click="increment">
        Clicked {{ count }} times
      </button>
    """


class LiveSearch(Component):
    citry = c

    class Kwargs:
        query: str = ""

    class State(Kwargs):
        pass

    class Events:
        def refresh(self, state):
            return LiveSearch(query=state.query)

    def template_data(self, kwargs, slots):
        results = find_products(kwargs.query) if kwargs.query else []
        return {"results": results}

    template = """
      <div>
        <input
          type="search"
          placeholder="Search..."
          :c-query.debounce.300ms="refresh"
        >
        <ul :class="{ searching: $loading() }">
          <c-for each="item in results">
            <li>{{ item.name }}</li>
          </c-for>
        </ul>
      </div>
    """


class ContactIn:
    name: str = ""
    email: str = ""


class ContactForm(Component):
    citry = c

    class Kwargs:
        name: str = ""
        email: str = ""
        sent: bool = False

    class Events:
        def submit(self, data: ContactIn):
            if "@" not in data.email:
                raise EventError(
                    "Please fix the errors.",
                    fields={"email": "Enter a valid email address."},
                )
            send_contact_email(data.name, data.email)
            return ContactForm(name=data.name, email=data.email, sent=True)

    def template_data(self, kwargs, slots):
        return {"sent": kwargs.sent}

    template = """
      <c-if cond="sent">
        <p>Thanks, we'll be in touch!</p>
      </c-if>
      <c-else>
        <form @c-submit.prevent="submit">
          <input name="name">
          <input name="email">
          <span x-text="$error?.fieldErrors.email"></span>
          <button type="submit" :disabled="$loading()">Send</button>
        </form>
      </c-else>
    """


_PAGES: dict[str, type[Component]] = {}


def _page_for(body: str, title: str) -> str:
    """One full-page wrapper per body: a stable class per call site, since the registry refuses re-registration."""
    page_cls = _PAGES.get(body)
    if page_cls is None:
        page_cls = type(
            f"PitchPage{len(_PAGES)}",
            (Component,),
            {
                "citry": c,
                "template": f"""
                  <html>
                    <head><title>{title}</title></head>
                    <body>
                      {body}
                    </body>
                  </html>
                """,
            },
        )
        _PAGES[body] = page_cls
    return str(page_cls())


def _collect_console(page: Any) -> list[str]:
    messages: list[str] = []
    page.on("console", lambda msg: messages.append(f"{msg.type}:{msg.text}"))
    return messages


def _citry_errors(messages: list[str]) -> list[str]:
    # The browser logs its own console error for any non-2xx fetch, and the
    # per-event route mirrors a call's 422 onto HTTP by design (design 6.2),
    # so those resource lines are expected traffic, not runtime errors.
    return [m for m in messages if m.startswith("error:") and "Failed to load resource" not in m]


def _collect_event_requests(page: Any) -> list[dict]:
    captured: list[dict] = []

    def record(request: Any) -> None:
        if "/ext/events/" not in request.url or request.url.endswith("/runtime.js"):
            return
        body = None
        try:
            body = json.loads(request.post_data or "null")
        except ValueError:
            body = None
        captured.append({"url": request.url, "body": body})

    page.on("request", record)
    return captured


def _wait_requests(page: Any, captured: list[dict], count: int, timeout_ms: int = 5000) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    while len(captured) < count:
        if time.monotonic() > deadline:
            msg = f"expected {count} captured request(s), saw {len(captured)}"
            raise AssertionError(msg)
        page.wait_for_timeout(25)


def _goto(page: Any, serve_live: Any, html: str) -> list[str]:
    messages = _collect_console(page)
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    return messages


def _source_lines(obj: Any) -> int:
    return len(inspect.getsource(obj).splitlines())


def _design_pitch_source(marker: str, fingerprint: str) -> str:
    design = (Path(__file__).resolve().parents[5] / "docs" / "design" / "events.md").read_text(encoding="utf8")
    for block in re.findall(r"```python\n(.*?)\n```", design, flags=re.DOTALL):
        if marker in block and fingerprint in block:
            return block[block.index(marker) :].strip()
    raise AssertionError(
        f"Could not find the {marker!r} pitch example containing {fingerprint!r} in docs/design/events.md"
    )


def _fixture_pitch_source(*objects: Any) -> str:
    # The docs assume app-wide registration; this suite adds only the local
    # harness registration and otherwise executes the published source.
    sources = [inspect.getsource(obj).replace("    citry = c\n\n", "").strip() for obj in objects]
    return "\n\n".join(sources)


def test_the_pitch_examples_hold_their_design_doc_line_counts() -> None:
    # Lock the executable classes to the published snippets, modulo the one
    # local registration line the e2e harness needs. This catches drift in
    # either direction; the size assertions keep the pitch's stated bounds.
    assert _fixture_pitch_source(Counter) == _design_pitch_source("class Counter", "Clicked {{ count }} times")
    assert _fixture_pitch_source(LiveSearch) == _design_pitch_source("class LiveSearch", 'placeholder="Search..."')
    assert _fixture_pitch_source(ContactIn, ContactForm) == _design_pitch_source(
        "class ContactIn", '<c-if cond="sent">'
    )
    assert _source_lines(Counter) <= 22
    assert _source_lines(LiveSearch) <= 32
    assert _source_lines(ContactIn) + _source_lines(ContactForm) <= 41


def test_counter_click_increments_through_the_server_and_morphs_the_button(page: Any, serve_live: Any) -> None:
    messages = _goto(page, serve_live, _page_for("<c-counter />", "pitch counter"))

    assert "Clicked 0 times" in page.inner_text("button")
    page.click("button")
    page.wait_for_function("document.querySelector('button').innerText.includes('Clicked 1 times')")
    page.click("button")
    page.wait_for_function("document.querySelector('button').innerText.includes('Clicked 2 times')")
    assert _citry_errors(messages) == []


def test_live_search_debounces_one_call_and_keeps_focus_and_caret_over_the_patch(page: Any, serve_live: Any) -> None:
    messages = _goto(page, serve_live, _page_for("<c-live-search />", "pitch live search"))
    captured = _collect_event_requests(page)

    search = page.locator("input[type=search]")
    search.press_sequentially("sho")
    _wait_requests(page, captured, 1)
    calls = (captured[0]["body"] or {}).get("calls", [])
    assert calls[0]["handlerName"] == "refresh"
    assert calls[0]["stateUpdates"] == {"query": "sho"}

    page.wait_for_function("document.querySelectorAll('li').length === 3")
    assert page.inner_text("li") == "sho-0"

    # The focused input keeps its value and caret while the morph changes
    # the list under it (section 2's trace, step 10).
    state = page.evaluate(
        """(() => {
          const el = document.querySelector('input[type=search]');
          return { focused: document.activeElement === el, value: el.value, at: el.selectionStart };
        })()"""
    )
    assert state == {"focused": True, "value": "sho", "at": 3}

    search.press_sequentially("es")
    page.wait_for_function("document.querySelector('li') && document.querySelector('li').innerText === 'shoes-0'")
    assert page.input_value("input[type=search]") == "shoes"
    assert _citry_errors(messages) == []


def test_contact_form_shows_the_422_field_inline_and_a_corrected_submit_succeeds(page: Any, serve_live: Any) -> None:
    SENT_EMAILS.clear()
    messages = _goto(page, serve_live, _page_for("<c-contact-form />", "pitch contact form"))
    captured = _collect_event_requests(page)

    page.fill("input[name=name]", "Ada")
    page.fill("input[name=email]", "not-an-email")
    page.click("button[type=submit]")
    _wait_requests(page, captured, 1)

    # The 422 fields map reaches the inline display; nothing re-rendered, so
    # the typed input survives untouched.
    page.wait_for_function("document.querySelector('span').innerText === 'Enter a valid email address.'")
    assert page.input_value("input[name=name]") == "Ada"
    assert page.input_value("input[name=email]") == "not-an-email"
    assert SENT_EMAILS == []

    page.fill("input[name=email]", "ada@lovelace.dev")
    page.click("button[type=submit]")
    page.wait_for_function('document.body.innerText.includes("Thanks, we\'ll be in touch!")')
    assert SENT_EMAILS == [("Ada", "ada@lovelace.dev")]
    assert _citry_errors(messages) == []
