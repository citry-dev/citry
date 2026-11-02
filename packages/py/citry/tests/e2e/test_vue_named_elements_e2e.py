"""
Browser e2e: an element `id` or `name` chosen by data does not stop Citry's runtime.

A browser makes an element with an `id` readable as a property of `window`,
and a `form`, `img`, `iframe`, `embed` or `object` with a `name` a property of
`document` that hides the document's own member of that name. A page whose
data picks such a value (a comment id used as an anchor, a field name) could
otherwise hand Citry's browser code an element in place of its own objects or
the document's methods, and Vue would never start or the Events call would
never go out. Each page here holds every such name at once, both as one form
per name and as all five element kinds sharing a name (which makes the
document property a collection), and must still start Vue and finish an
Events call.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

# Globals that Citry's scripts define on `window`. Taken as an element id, each
# is what a plain read of `window` returns until Citry's script defines its own value.
CITRY_GLOBALS = [
    "Citry",
    "__citryRuntime",
    "__citryRuntimeDefinitions",
    "CitryVueEvents",
    "CitryVueFragments",
    "CitryVueDevChecks",
    "Vue",
]
# Document members the runtime or Vue reads, plus Citry's globals, which reach
# `window` through a named `form` or `iframe` as well.
DOCUMENT_MEMBERS = [
    "currentScript",
    "cookie",
    "createElement",
    "createElementNS",
    "createTextNode",
    "createComment",
    "querySelector",
    "querySelectorAll",
    "addEventListener",
    "removeEventListener",
    "dispatchEvent",
    "head",
    "body",
    "documentElement",
    "activeElement",
    "baseURI",
    "hidden",
]
NAMES = DOCUMENT_MEMBERS + CITRY_GLOBALS

# The pages hide `document.querySelector` too, so the test reads them through the
# prototype, inside a function because the nonce page's CSP refuses a string to evaluate.
_FIND = "Document.prototype.querySelector.bind(document)"

# A form found as `window.<id>` hands out its named fields as properties. The
# definition table entry is named after the page's own definition id.
DEFINITION = object()
NESTED = [
    ("Citry", "vue"),
    ("Citry", "events"),
    ("Citry", "fragments"),
    ("__citryRuntime", "compilerRuntime"),
    ("__citryRuntimeDefinitions", DEFINITION),
    ("CitryVueEvents", "createVueEventsBridge"),
    ("CitryVueFragments", "installFragmentManager"),
]

NONCE = "cGFnZS1ub25jZQ"
CSP = f"script-src 'nonce-{NONCE}' 'strict-dynamic'; object-src 'none'"


def _named_values(*, all_kinds: bool, definition_id: str) -> dict[str, Any]:
    """The values data chooses: ids, names, and named inputs inside id-bearing forms."""
    return {
        "ids": CITRY_GLOBALS,
        "form_names": NAMES,
        "other_names": NAMES if all_kinds else [],
        # A form found as `window.<id>` hands out its named inputs as properties.
        "nested": [(form_id, definition_id if field == DEFINITION else field) for form_id, field in NESTED],
    }


def _named_markup(app: Citry, values: dict[str, Any]) -> str:
    """Render the named elements as plain server HTML, the way an app binds a comment id or a field name."""

    class NamedElements(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return values

        template = """
            <div
              c-for="name in ids"
              c-id="name"
            >
              clobber
            </div>
            <form
              c-for="name in form_names"
              c-name="name"
            ></form>
            <img
              c-for="name in other_names"
              c-name="name"
              src="data:,"
            >
            <iframe
              c-for="name in other_names"
              c-name="name"
            ></iframe>
            <embed
              c-for="name in other_names"
              c-name="name"
            >
            <object
              c-for="name in other_names"
              c-name="name"
            ></object>
            <form
              c-for="pair in nested"
              c-id="pair[0]"
            >
              <input c-name="pair[1]">
            </form>
        """

    return NamedElements().render().serialize()


def _counter(app: Citry) -> type[Component]:
    class NamedCounter(Component):
        citry = app

        class State:
            n: int = 0

        class Events:
            def inc(self, state: Any) -> None:
                state.n += 1

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"t": "vue-started"}

        template = """
            <main>
              <b id="probe-t" v-text="t"></b>
              <b id="probe-n" v-text="$state.n"></b>
              <button
                id="probe-btn"
                @c-click="inc"
              >
                inc
              </button>
            </main>
        """

    return NamedCounter


def _render(component: type[Component], named: str, variant: str) -> str:
    rendered = component().render()
    # The named elements come first, so they are in the page before the runtime's scripts run.
    if variant == "hydrated":
        return named + rendered.serialize()
    if variant == "prepend":
        return named + rendered.serialize(deps_position="prepend")
    return named + rendered.serialize(csp_nonce=NONCE)


def _definition_id(component: type[Component]) -> str:
    # The definition table entry the page's own manifest names, so a form can try to stand in for it.
    probe = component().render().serialize()
    return probe.split('"definitions":[{', 1)[1].split('"id":"', 1)[1].split('"', 1)[0]


def _check_page_works(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, app: Citry, html: str, variant: str
) -> None:
    """Load the page, wait for Vue to start, and finish one Events call."""
    base = serve_live(app, html, "")
    if variant == "nonce":
        # Serve the same page under a nonce CSP header, so only nonced scripts run.
        page.route(
            base + "/",
            lambda route: route.fulfill(
                status=200,
                headers={"Content-Type": "text/html; charset=utf-8", "Content-Security-Policy": CSP},
                body="<!doctype html>" + html
                if "<html" in html
                else f"<!doctype html><html><body>{html}</body></html>",
            ),
        )
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    # A runtime that cannot start never reports ready, so fail in seconds rather than the default 30.
    page.set_default_timeout(5000)
    page.goto(base + "/")
    try:
        wait_for_citry_ready()
        page.click("#probe-btn")
        page.wait_for_function(f"() => {_FIND}('#probe-n')?.textContent === '1'", timeout=5000)
    except Exception as error:  # noqa: BLE001 - report the page's errors with the timeout
        pytest.fail(f"the runtime did not start or the Events call did not finish: {error}; page errors: {errors}")
    assert errors == []
    # Citry's own globals are own properties of `window` holding Citry's objects.
    assert page.evaluate(
        """() => ['Citry', '__citryRuntime', 'CitryVueEvents', 'Vue'].every(name =>
            Object.prototype.hasOwnProperty.call(window, name) && !(window[name] instanceof Element))"""
    )


@pytest.mark.parametrize("all_kinds", [False, True], ids=["one-form-each", "five-kinds-each"])
@pytest.mark.parametrize("variant", ["hydrated", "prepend", "nonce"])
def test_data_chosen_ids_and_names_leave_the_runtime_working(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, *, all_kinds: bool, variant: str
) -> None:
    app = Citry(autodiscover=False, secret="s" * 40)
    app.set_mounted_prefix("/citry")
    component = _counter(app)
    values = _named_values(all_kinds=all_kinds, definition_id=_definition_id(component))
    html = _render(component, _named_markup(app, values), variant)
    _check_page_works(page, serve_live, wait_for_citry_ready, app, html, variant)


@pytest.mark.parametrize(
    ("form_id", "field"),
    NESTED,
    ids=[f"{form_id}-{'definition' if field is DEFINITION else field}" for form_id, field in NESTED],
)
def test_a_named_field_in_a_data_id_form_leaves_the_runtime_working(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, *, form_id: str, field: object
) -> None:
    # One form per page: with a second element of the same id, `window.<id>` is a
    # collection, which does not hand out the form's fields, so the route would go untested.
    app = Citry(autodiscover=False, secret="s" * 40)
    app.set_mounted_prefix("/citry")
    component = _counter(app)
    name = _definition_id(component) if field is DEFINITION else field
    values = {"ids": [], "form_names": [], "other_names": [], "nested": [(form_id, name)]}
    html = _render(component, _named_markup(app, values), "hydrated")
    _check_page_works(page, serve_live, wait_for_citry_ready, app, html, "hydrated")


# The page a fragment strategy targets: it has no Citry runtime of its own and
# runs the fragment's scripts when it inserts it, as htmx does.
_FRAGMENT_PAGE = """
<html>
  <head></head>
  <body>
    {named}
    <div id="target"></div>
    <script>
      fetch('/fragment')
        .then((r) => r.text())
        .then((html) => {{
          const range = document.createRange();
          document.getElementById('target').append(range.createContextualFragment(html));
        }});
    </script>
  </body>
</html>
"""


def test_fragment_preloader_ignores_data_chosen_ids_and_names(page: Any, serve_live: Any) -> None:
    app = Citry(autodiscover=False, secret="s" * 40)
    app.set_mounted_prefix("/citry")

    class Frag(Component):
        citry = app
        template = '<b id="frag-t" v-text="t"></b>'

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"t": "fragment-started"}

    fragment_html = Frag().render().serialize(deps_strategy="fragment")
    # The script that loads the runtime reads `Citry`, `document.createElement`,
    # `document.head` and `document.currentScript`, and the fragment manager reads
    # `document.querySelectorAll` and `document.body`; data names each of them.
    named = (
        '<form id="Citry"><input name="fragments"></form>'
        '<form name="createElement"></form><form name="head"></form><form name="currentScript"></form>'
        # The fragment manager reads these two when it mounts the fragment.
        '<form name="querySelectorAll"></form><form name="body"></form>'
    )
    base = serve_live(app, _FRAGMENT_PAGE.format(named=named), fragment_html)
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base + "/")
    try:
        page.wait_for_function(f"() => {_FIND}('#frag-t')?.textContent === 'fragment-started'", timeout=5000)
    except Exception as error:  # noqa: BLE001 - report the page's errors with the timeout
        pytest.fail(f"the fragment did not start: {error}; page errors: {errors}")
    assert errors == []
