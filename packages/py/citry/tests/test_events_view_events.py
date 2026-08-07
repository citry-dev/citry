"""
Tests for the ViewEvents compatibility shim (WP14): the reserved verb
handler names and the verb-dispatch route ``ext/events/e/{class_id}``
(docs/design/events.md 10).

Wire-exact assertions are authored observe-then-lock over a mounted FastAPI
app, mirroring the routes suite (test_events_routes.py). Verb handlers
omit ``state``, so no tokens (and no pinned clock) are needed here.
"""

import json

import pytest

from citry import Citry, Component, Extension
from citry.ext.events import event
from citry.ext.events.view_events import (
    VERB_HANDLER_NAMES,
    VIEW_EVENT_PATH,
    ViewEvents,
    view_events_routes,
)

SIGNING_KEY = "test-secret-key"

RUNTIME_HEADERS = {"X-Citry-Events": "1"}
# What the runtime labels an envelope body (design 6.2); plain
# application/json on these routes is the flat handler-fields shape.
ENVELOPE_HEADERS = {"Content-Type": "application/citry-events+json", **RUNTIME_HEADERS}


def _citry(**kwargs):
    c = Citry(secret=SIGNING_KEY, **kwargs)
    c.set_mounted_prefix("/citry")
    return c


def _contact(c):
    """A verb-shaped component: the ported form-submission shape."""

    class SearchIn:
        q: str = ""

    class ContactIn:
        email: str = ""
        message: str = ""

    class ContactForm(Component):
        citry = c

        class Events(ViewEvents):
            def get(self, data: SearchIn):
                return {"echo": data.q}

            def post(self, data: ContactIn, request):
                return {"sent": data.email}

            def delete(self):
                return {"deleted": True}

            def notify(self, data: ContactIn):
                return {"notified": data.email}

        template = """
            <p>form</p>
        """

    return ContactForm


def _handlers(comp_cls):
    return comp_cls.citry.extensions.get_extension("events").resolve(comp_cls).handlers


################################################
# THE RESERVED VERB NAMES
################################################


class TestVerbReservation:
    def test_verb_handlers_answer_their_own_method(self):
        c = _citry()
        contact = _contact(c)
        handlers = _handlers(contact)
        assert handlers["get"].methods == ("GET",)
        assert handlers["post"].methods == ("POST",)
        assert handlers["delete"].methods == ("DELETE",)

    def test_named_handlers_ride_along_unchanged(self):
        # The shim only touches the seven verb names; a named event on the
        # same class keeps the plain Events defaults.
        c = _citry()
        contact = _contact(c)
        assert _handlers(contact)["notify"].methods == ("POST",)

    def test_explicit_event_methods_win_over_the_verb(self):
        c = _citry()

        class Odd(Component):
            citry = c

            class Events(ViewEvents):
                @event(methods=("POST",))
                def get(self):
                    return {"odd": True}

            template = """
                <p>odd</p>
            """

        assert _handlers(Odd)["get"].methods == ("POST",)

    def test_other_event_options_keep_the_stamped_verb(self):
        c = _citry()

        class Timed(Component):
            citry = c

            class Events(ViewEvents):
                @event(debounce=250)
                def post(self):
                    return {"ok": True}

            template = """
                <p>timed</p>
            """

        handler = _handlers(Timed)["post"]
        assert handler.methods == ("POST",)
        assert handler.debounce == 250

    def test_state_on_a_verb_handler_fails_at_class_definition(self):
        expected = (
            "Events.post declares 'state', but verb handlers omit it: they serve the token-optional"
            " verb compatibility route and do not expose State. Move stateful work into a named"
            " event handler (which can live on the same class)."
        )
        with pytest.raises(ValueError, match="verb handlers omit it") as exc_info:

            class Events(ViewEvents):
                def post(self, state):
                    return None

        assert str(exc_info.value) == expected

    def test_route_table_carries_the_verb_route(self):
        c = _citry()
        [route] = view_events_routes(c)
        assert route.path == VIEW_EVENT_PATH == "ext/events/e/{class_id}"
        assert route.methods == tuple(verb.upper() for verb in VERB_HANDLER_NAMES)
        assert route.handler_async is not None
        # The engine's combined table serves it (the extension mounts it
        # next to the per-event route).
        assert VIEW_EVENT_PATH in {r.path for r in c.urls}


################################################
# THE VERB ROUTE, END TO END OVER FASTAPI
################################################

fastapi = pytest.importorskip("fastapi", reason="the shim route tests need fastapi + httpx2")
pytest.importorskip("httpx2", reason="Starlette's TestClient needs httpx2")

from fastapi.testclient import TestClient  # noqa: E402


def _mounted(c):
    from citry.contrib.fastapi import mount

    app = fastapi.FastAPI()
    mount(app, c)
    return TestClient(app)


def _verb_url(comp_cls):
    return f"/citry/ext/events/e/{comp_cls.class_id}"


class TestVerbRoute:
    def test_form_post_reaches_the_post_handler(self):
        # The ported form-submission shape: a plain form post (no runtime
        # header) is served by method, and the data value answers as plain
        # JSON (the compat mode).
        c = _citry()
        contact = _contact(c)
        client = _mounted(c)
        response = client.post(_verb_url(contact), data={"email": "a@b.c", "message": "hi"})
        assert response.status_code == 200
        assert response.json() == {"sent": "a@b.c"}

    def test_classic_post_can_return_component_html_with_props_slots_and_escaping(self):
        observed_actions = []

        class ResultObserver(Extension):
            name = "result_observer"

            def on_event_result(self, ctx):
                observed_actions.extend(ctx.actions)
                return ctx.actions

        c = _citry(extensions=[ResultObserver])

        class ResultCard(Component):
            citry = c

            class Kwargs:
                name: str

            def template_data(self, kwargs, slots):
                return {"name": kwargs.name}

            template = """
                <section>
                    <p class="name">{{ name }}</p>
                    <p class="fallback"><c-slot name="fallback">Default greeting</c-slot></p>
                    <p class="message"><c-slot name="message" /></p>
                </section>
            """

        class ContactIn:
            name: str
            message: str

        class ContactForm(Component):
            citry = c

            class Events(ViewEvents):
                def post(self, data: ContactIn):
                    return ResultCard(name=data.name, slots={"message": data.message})

            template = """
                <form></form>
            """

        client = _mounted(c)
        response = client.post(
            _verb_url(ContactForm),
            data={"name": "<script>prop</script>", "message": "<script>slot</script>"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "Default greeting" in response.text
        assert "&lt;script&gt;prop&lt;/script&gt;" in response.text
        assert "&lt;script&gt;slot&lt;/script&gt;" in response.text
        assert "<script>" not in response.text
        [render_action] = observed_actions
        assert set(render_action) == {"action", "target", "swap", "html"}
        assert isinstance(render_action["target"], str)

    def test_envelope_post_round_trips(self):
        c = _citry()
        contact = _contact(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [
                {
                    "componentClassId": contact.class_id,
                    "handlerName": "post",
                    "args": {"email": "x@y.z"},
                }
            ],
        }
        response = client.post(_verb_url(contact), content=json.dumps(envelope), headers=ENVELOPE_HEADERS)
        assert response.status_code == 200
        assert response.json() == {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "results": [{"ok": True, "actions": [{"action": "data", "value": {"sent": "x@y.z"}}]}],
        }

    def test_get_reads_its_args_from_the_query(self):
        c = _citry()
        contact = _contact(c)
        client = _mounted(c)
        response = client.get(_verb_url(contact) + "?q=milk", headers=RUNTIME_HEADERS)
        assert response.status_code == 200
        assert response.json() == {
            "protocol": "citry-events/1",
            "requestId": "query",
            "results": [{"ok": True, "actions": [{"action": "data", "value": {"echo": "milk"}}]}],
        }

    def test_bodyless_delete_dispatches(self):
        # fetch(url, {method: "DELETE"}) sends no body and no content type;
        # the shim decodes it as an empty form post.
        c = _citry()
        contact = _contact(c)
        client = _mounted(c)
        response = client.request("DELETE", _verb_url(contact), headers=RUNTIME_HEADERS)
        assert response.status_code == 200
        assert response.json() == {
            "protocol": "citry-events/1",
            "requestId": "form",
            "results": [{"ok": True, "actions": [{"action": "data", "value": {"deleted": True}}]}],
        }

    def test_method_without_a_handler_answers_unknown_event(self):
        c = _citry()
        contact = _contact(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [{"componentClassId": contact.class_id, "handlerName": "put", "args": {}}],
        }
        response = client.put(_verb_url(contact), content=json.dumps(envelope), headers=ENVELOPE_HEADERS)
        assert response.status_code == 404
        error = response.json()["results"][0]["error"]
        assert error["code"] == "unknown_event"
        assert error["message"] == "Component 'ContactForm' has no event 'put'."

    def test_method_only_route_rejects_a_plain_events_class(self):
        c = _citry()

        class NamedOnly(Component):
            citry = c

            class Events:
                def post(self):
                    return {"unexpected": True}

            template = """
                <p>named only</p>
            """

        response = _mounted(c).post(_verb_url(NamedOnly), data={})
        assert response.status_code == 404
        assert response.text == "Not Found"

    def test_body_naming_a_different_event_is_rejected(self):
        # The URL (here: the method) stays authoritative, exactly like the
        # per-event route.
        c = _citry()
        contact = _contact(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [{"componentClassId": contact.class_id, "handlerName": "get", "args": {}}],
        }
        response = client.post(_verb_url(contact), content=json.dumps(envelope), headers=ENVELOPE_HEADERS)
        assert response.status_code == 400
        error = response.json()["results"][0]["error"]
        assert error["code"] == "protocol_mismatch"
        assert error["message"] == (
            "The call names event 'get', but the URL addresses 'post'; the URL is authoritative"
            " on the per-event route."
        )

    def test_form_post_redirect_becomes_303(self):
        # Post/redirect/get with JavaScript disabled: the browser-native
        # translation of a Redirect action.
        c = _citry()

        class Thanks(Component):
            citry = c

            class Events(ViewEvents):
                def post(self, request):
                    from citry.ext.events.actions import Redirect

                    return Redirect("/thanks")

            template = """
                <p>bye</p>
            """

        client = _mounted(c)
        response = client.post(_verb_url(Thanks), data={}, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/thanks"

    def test_the_per_event_route_still_serves_verbs_by_name(self):
        # The shim adds a route; it takes nothing away.
        c = _citry()
        contact = _contact(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [
                {
                    "componentClassId": contact.class_id,
                    "handlerName": "post",
                    "args": {"email": "n@m.o"},
                }
            ],
        }
        response = client.post(
            f"/citry/ext/events/e/{contact.class_id}/post",
            content=json.dumps(envelope),
            headers=ENVELOPE_HEADERS,
        )
        assert response.status_code == 200
        [result] = response.json()["results"]
        assert result["actions"] == [{"action": "data", "value": {"sent": "n@m.o"}}]
