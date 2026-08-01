"""
Tests for the events HTTP layer (WP13): the payload codecs, the CSRF layers,
the three routes over a mounted FastAPI app, the compat / no-JS mode, the
``RouteResponse`` escape hatch, and the URL builders
(docs/design/events.md 3.8, 6.2, 7.4).

The Django parity half lives in test_events_django.py. Exact-output
assertions are authored observe-then-lock; the example-pinned wire messages
come from packages/protocol/events/v1/tests/.
"""

import asyncio
import json
from decimal import Decimal

import pytest

from citry import Citry, Component
from citry.ext.events import actions, event
from citry.ext.events.codecs import (
    EnvelopeCodec,
    FlatJsonCodec,
    FormCodec,
    decode_query_request,
    decode_request,
)
from citry.ext.events.csrf import build_csrf_check, enforce_floor
from citry.ext.events.dispatcher import EventsDispatcher, TransportContext
from citry.ext.events.errors import EventError
from citry.ext.events.routes import RUNTIME_PATH, events_config_url, get_event_url
from citry.ext.events.schemas import StringArgs
from citry.ext.events.tokens import mint_state_token
from citry.util.routing import RouteHeaders, RouteRequest, RouteResponse

SIGNING_KEY = "test-secret-key"
FIXED_NOW = 1_700_000_000.0

CSRF_FAILED_MESSAGE = "The call failed the CSRF check; reload the page and try again."
UNENCODABLE_RESULT_MESSAGE = (
    "The handler returned a value strict JSON cannot encode (for example, a Decimal or a non-finite number such as "
    "inf or nan)."
)


@pytest.fixture(autouse=True)
def _pinned_token_clock(monkeypatch):
    monkeypatch.setattr("citry.ext.events.tokens._now", lambda: FIXED_NOW)


def _citry(**kwargs):
    c = Citry(secret=SIGNING_KEY, **kwargs)
    c.set_mounted_prefix("/citry")
    return c


def _greeter(c):
    """A component exercising POST, GET, state, compat, and the escape hatch."""

    class GreetIn:
        text: str = ""

    class GreeterState:
        text: str = ""

        def render(self):
            return Greeter(text=self.text)

    class Greeter(Component):
        citry = c

        class Kwargs:
            text: str = ""

        State = GreeterState

        class Events:
            def save(self, data: GreetIn, state):
                state.text = data.text
                return state.render()

            def finish(self, data: GreetIn, state):
                from citry.ext.events.actions import Redirect

                state.text = data.text
                return Redirect("/done")

            def quiet(self, state):
                return None

            def history(self):
                return actions.PushUrl("?page=2")

            def codec_echo(self, data: GreetIn):
                return {"echo": data.text}

            @event(methods=("GET",))
            def echo(self, data: GreetIn):
                return {"echo": data.text}

            @event(methods=("GET",))
            def peek(self, state):
                return {"text": state.text}

            @event(bundle=False)
            def export(self):
                return RouteResponse(
                    content=b"csv,data",
                    content_type="text/csv",
                    headers=(("Content-Disposition", 'attachment; filename="x.csv"'),),
                )

            @event(bundle=False)
            def download(self):
                return actions.Download(
                    "name\nAda",
                    "přehled.csv",
                    content_type="text/csv; charset=utf-8",
                )

            @event(methods=("GET",), bundle=False)
            def download_get(self):
                return actions.Download(b"csv,data", "report.csv", content_type="text/csv")

            @event(methods=("GET",), bundle=False)
            def cached(self):
                return RouteResponse(
                    content="cached",
                    content_type="text/plain",
                    headers=(("cAcHe-CoNtRoL", "public, max-age=60"),),
                )

        def template_data(self, kwargs, slots):
            return {"text": kwargs.text}

        template = """
            <p>{{ text }}</p>
        """

    return Greeter


def _token(comp_cls, **state_kwargs):
    return mint_state_token(
        comp_cls.State(**state_kwargs),
        class_id=comp_cls.class_id,
        secret=SIGNING_KEY,
        max_age=None,
        max_bytes=8192,
    )


def _request(method="POST", content_type="application/json", headers=(), body=b"", query=None):
    all_headers = list(headers)
    if content_type:
        all_headers.append(("Content-Type", content_type))
    return RouteRequest(
        method=method,
        path="/citry/ext/events/call",
        query=query or {},
        headers=RouteHeaders(all_headers),
        body=body,
        content_type=content_type,
    )


################################################
# CODECS
################################################


class TestEnvelopeCodec:
    def test_claims_the_vendor_media_type(self):
        # The vendor type is what marks a body as an envelope (design 6.2);
        # classification never depends on body shape.
        assert EnvelopeCodec.content_type == "application/citry-events+json"

    def test_identity(self):
        envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": []}
        assert EnvelopeCodec().decode(json.dumps(envelope).encode(), _request()) == envelope

    def test_malformed_body_is_a_400(self):
        with pytest.raises(EventError) as excinfo:
            EnvelopeCodec().decode(b"{nope", _request())
        assert excinfo.value.status == 400

    def test_non_object_body_is_a_400(self):
        with pytest.raises(EventError) as excinfo:
            EnvelopeCodec().decode(b"[1, 2]", _request())
        assert excinfo.value.status == 400

    @pytest.mark.parametrize("literal", ["Infinity", "-Infinity", "NaN"])
    def test_non_standard_json_literals_are_a_400(self, literal):
        # Python's json.loads tolerates these, but they are not JSON: a
        # conforming client cannot send them, and the JSON result envelope
        # could not carry the values back.
        with pytest.raises(EventError) as excinfo:
            EnvelopeCodec().decode(f'{{"ratio": {literal}}}'.encode(), _request())
        assert excinfo.value.status == 400
        assert "not valid JSON" in excinfo.value.message

    @pytest.mark.parametrize("number", ["1e400", "-1e400"])
    def test_number_overflow_to_infinity_is_a_400(self, number):
        # Valid JSON grammar (RFC 8259 leaves out-of-range numbers
        # implementation-defined), but Python would read it as inf, which
        # the result envelope could not carry back; same 400 as the
        # non-standard literals.
        with pytest.raises(EventError) as excinfo:
            EnvelopeCodec().decode(f'{{"ratio": {number}}}'.encode(), _request())
        assert excinfo.value.status == 400
        assert "not valid JSON" in excinfo.value.message


class TestFlatJsonCodec:
    def test_fields_become_args_and_reserved_fields_map(self):
        body = b'{"text": "Buy milk", "_citry_state_token": "cev1.abc", "_citry_caller_render_id": "c9Zk1q"}'
        envelope = FlatJsonCodec().decode(body, _request())
        assert envelope == {
            "protocol": "citry-events/1",
            "requestId": "flat",
            "calls": [
                {
                    "stateToken": "cev1.abc",
                    "callerRenderId": "c9Zk1q",
                    "args": {"text": "Buy milk"},
                }
            ],
        }

    def test_args_stay_a_plain_dict(self):
        # Flat JSON is still JSON: the args are never StringArgs, so the
        # strict binding rules of design 3.3 apply (no string-to-int).
        envelope = FlatJsonCodec().decode(b'{"count": "3"}', _request())
        args = envelope["calls"][0]["args"]
        assert type(args) is dict
        assert not isinstance(args, StringArgs)

    def test_malformed_body_is_a_400(self):
        with pytest.raises(EventError) as excinfo:
            FlatJsonCodec().decode(b"{nope", _request())
        assert excinfo.value.status == 400

    def test_non_object_body_is_a_400(self):
        with pytest.raises(EventError) as excinfo:
            FlatJsonCodec().decode(b"[1, 2]", _request())
        assert excinfo.value.status == 400
        assert "one key per field" in excinfo.value.message

    @pytest.mark.parametrize("literal", ["Infinity", "-Infinity", "NaN"])
    def test_non_standard_json_literals_are_a_400(self, literal):
        # Same strictness as the envelope codec: these literals are not
        # JSON, so they answer the malformed-body 400.
        with pytest.raises(EventError) as excinfo:
            FlatJsonCodec().decode(f'{{"ratio": {literal}}}'.encode(), _request())
        assert excinfo.value.status == 400
        assert "not valid JSON" in excinfo.value.message

    @pytest.mark.parametrize("number", ["1e400", "-1e400"])
    def test_number_overflow_to_infinity_is_a_400(self, number):
        # The parse_float guard is shared by both JSON codecs: a number
        # Python would overflow to inf answers the malformed-body 400.
        with pytest.raises(EventError) as excinfo:
            FlatJsonCodec().decode(f'{{"ratio": {number}}}'.encode(), _request())
        assert excinfo.value.status == 400
        assert "not valid JSON" in excinfo.value.message

    def test_ordinary_floats_still_parse(self):
        # The overflow guard must not touch in-range numbers (exponent
        # notation included).
        envelope = FlatJsonCodec().decode(b'{"ratio": 2.5, "n": 1e3}', _request())
        assert envelope["calls"][0]["args"] == {"ratio": 2.5, "n": 1000.0}


class TestFormCodec:
    def test_fields_become_args_and_reserved_fields_map(self):
        body = b"text=Buy+milk&_citry_state_token=cev1.abc&_citry_caller_render_id=c9Zk1q"
        envelope = FormCodec().decode(body, _request(content_type="application/x-www-form-urlencoded"))
        assert envelope == {
            "protocol": "citry-events/1",
            "requestId": "form",
            "calls": [
                {
                    "stateToken": "cev1.abc",
                    "callerRenderId": "c9Zk1q",
                    "args": {"text": "Buy milk"},
                }
            ],
        }

    def test_repeated_fields_become_lists(self):
        envelope = FormCodec().decode(b"tag=a&tag=b", _request())
        assert envelope["calls"][0]["args"] == {"tag": ["a", "b"]}

    def test_args_are_marked_as_string_transport(self):
        # The StringArgs marking is what turns on the source-aware binding
        # rule of design 3.3 in the schema layer.
        envelope = FormCodec().decode(b"count=3", _request())
        assert isinstance(envelope["calls"][0]["args"], StringArgs)


class TestQueryCodec:
    def test_args_from_query_and_token_only_when_state_declared(self):
        request = _request(
            method="GET",
            content_type="",
            query={"text": ("hi",), "_citry_state_token": ("cev1.abc",), "_citry_caller_render_id": ("i1",)},
        )
        with_state = decode_query_request(request, state_declared=True)
        assert with_state["calls"][0] == {"stateToken": "cev1.abc", "callerRenderId": "i1", "args": {"text": "hi"}}
        # A stateless handler's URL stays token-free: the parameter is not
        # part of the call at all.
        without_state = decode_query_request(request, state_declared=False)
        assert without_state["calls"][0] == {"callerRenderId": "i1", "args": {"text": "hi"}}

    def test_args_are_marked_as_string_transport(self):
        # Same marking as the form codec: query strings are a string
        # transport, so their args get the source-aware binding (design 3.3).
        request = _request(method="GET", content_type="", query={"count": ("3",)})
        envelope = decode_query_request(request, state_declared=False)
        assert isinstance(envelope["calls"][0]["args"], StringArgs)

    def test_browser_epoch_is_reserved_and_decoded_as_an_integer(self):
        request = _request(
            method="GET",
            content_type="",
            query={"text": ("hi",), "_citry_send_sequence": ("7",)},
        )
        envelope = decode_query_request(request, state_declared=False)
        assert envelope["calls"][0] == {"sendSequence": 7, "args": {"text": "hi"}}

    def test_browser_envelope_metadata_is_reserved_and_restored(self):
        capabilities = {"swaps": ["morph", "replace"], "actions": ["render", "data"]}
        request = _request(
            method="GET",
            content_type="",
            query={
                "text": ("hi",),
                "_citry_protocol": ("citry-events/1",),
                "_citry_request_id": ("r_browser",),
                "_citry_capabilities": (json.dumps(capabilities),),
            },
        )
        envelope = decode_query_request(request, state_declared=False)
        assert envelope == {
            "protocol": "citry-events/1",
            "requestId": "r_browser",
            "capabilities": capabilities,
            "calls": [{"args": {"text": "hi"}}],
        }


class TestDecodeRequest:
    def test_get_always_uses_the_query_codec(self):
        request = _request(method="GET", content_type="", query={"text": ("hi",)})
        decoded = decode_request(request)
        assert decoded.envelope["requestId"] == "query"
        assert decoded.form == {}

    def test_form_posts_carry_the_parsed_fields(self):
        request = _request(content_type="application/x-www-form-urlencoded", body=b"text=hi&_citry_state_token=t")
        decoded = decode_request(request)
        assert decoded.envelope["calls"][0]["args"] == {"text": "hi"}
        # request.form keeps every field, reserved ones included.
        assert decoded.form == {"text": "hi", "_citry_state_token": "t"}

    def test_content_type_parameters_are_ignored(self):
        envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": []}
        request = _request(
            content_type="application/citry-events+json; charset=utf-8",
            body=json.dumps(envelope).encode(),
        )
        assert decode_request(request).envelope == envelope

    def test_the_vendor_type_is_the_envelope_on_both_routes(self):
        envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": []}
        request = _request(content_type="application/citry-events+json", body=json.dumps(envelope).encode())
        assert decode_request(request).envelope == envelope
        assert decode_request(request, batch=True).envelope == envelope

    def test_plain_json_is_flat_on_the_per_event_route(self):
        request = _request(content_type="application/json", body=b'{"count": 3}')
        decoded = decode_request(request)
        assert decoded.envelope["requestId"] == "flat"
        assert decoded.envelope["calls"][0]["args"] == {"count": 3}
        assert decoded.form == {}

    def test_plain_json_is_the_envelope_on_the_batch_route(self):
        # A batch body has no flat reading, so the batch route takes the
        # envelope under plain application/json too (design 6.2).
        envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": [{"args": {}}]}
        request = _request(content_type="application/json", body=json.dumps(envelope).encode())
        assert decode_request(request, batch=True).envelope == envelope

    def test_batch_flat_shaped_json_gets_the_pointed_message(self):
        # An object with none of the envelope's identifying fields has no
        # envelope reading; the rejection names both the envelope and the
        # per-event flat alternative. (This picks between two error
        # messages only: the dispatcher would reject the object anyway.)
        request = _request(content_type="application/json", body=b'{"email": "a@b.c"}')
        with pytest.raises(EventError) as excinfo:
            decode_request(request, batch=True)
        assert excinfo.value.status == 400
        assert "takes the citry-events/1 call envelope" in excinfo.value.message
        assert "ext/events/e/{class_id}/{event}" in excinfo.value.message

    def test_batch_partial_envelope_is_not_intercepted(self):
        # Any identifying field means the body is a (broken) envelope; the
        # dispatcher's own validation answers it, not the pointed message.
        request = _request(content_type="application/json", body=b'{"calls": []}')
        assert decode_request(request, batch=True).envelope == {"calls": []}

    def test_batch_rejects_the_form_content_type(self):
        request = _request(content_type="application/x-www-form-urlencoded", body=b"a=1")
        with pytest.raises(EventError) as excinfo:
            decode_request(request, batch=True)
        assert excinfo.value.status == 400
        assert "batch endpoint" in excinfo.value.message

    def test_unclaimed_content_type_is_a_400(self):
        with pytest.raises(EventError) as excinfo:
            decode_request(_request(content_type="application/msgpack", body=b"x"))
        assert excinfo.value.status == 400
        assert "No payload codec claims" in excinfo.value.message

    def test_user_codecs_are_tried_first(self):
        class LoudJson:
            content_type = "application/json"

            def decode(self, body, request):
                return {"claimed": "by-user-codec"}

        request = _request(body=b"{}")
        assert decode_request(request, [LoudJson()]).envelope == {"claimed": "by-user-codec"}


################################################
# CSRF
################################################


class TestCsrfFloor:
    def test_json_post_without_the_header_is_rejected(self):
        with pytest.raises(EventError) as excinfo:
            enforce_floor(_request())
        assert excinfo.value.message == CSRF_FAILED_MESSAGE
        assert excinfo.value.status == 403

    def test_json_post_with_the_header_passes(self):
        enforce_floor(_request(headers=[("X-Citry-Events", "1")]))

    def test_vendor_type_post_without_the_header_is_rejected(self):
        # The envelope's own media type is JSON-bodied too; the header floor
        # covers it exactly like plain application/json (design 7.4).
        with pytest.raises(EventError) as excinfo:
            enforce_floor(_request(content_type="application/citry-events+json"))
        assert excinfo.value.message == CSRF_FAILED_MESSAGE
        assert excinfo.value.status == 403

    def test_vendor_type_post_with_the_header_passes(self):
        enforce_floor(
            _request(content_type="application/citry-events+json", headers=[("X-Citry-Events", "1")]),
        )

    def test_any_json_suffix_type_requires_the_header(self):
        # The floor keys on the +json suffix, so every JSON-bodied call is
        # covered, not just the two types the built-in codecs claim.
        with pytest.raises(EventError):
            enforce_floor(_request(content_type="application/hal+json"))

    def test_form_post_needs_no_header(self):
        # The compatibility path: a plain form cannot attach custom headers.
        enforce_floor(_request(content_type="application/x-www-form-urlencoded"))

    def test_origin_mismatch_is_rejected(self):
        request = _request(
            headers=[("X-Citry-Events", "1"), ("Origin", "https://evil.example"), ("Host", "good.example")],
        )
        with pytest.raises(EventError):
            enforce_floor(request)

    def test_matching_origin_passes(self):
        request = _request(
            headers=[("X-Citry-Events", "1"), ("Origin", "https://good.example"), ("Host", "good.example")],
        )
        enforce_floor(request)

    def test_null_origin_is_rejected(self):
        request = _request(headers=[("X-Citry-Events", "1"), ("Origin", "null"), ("Host", "good.example")])
        with pytest.raises(EventError):
            enforce_floor(request)

    @pytest.mark.parametrize(
        ("fetch_site", "passes"),
        [("same-origin", True), ("none", True), ("same-site", False), ("cross-site", False)],
    )
    def test_sec_fetch_site(self, fetch_site, passes):
        request = _request(headers=[("X-Citry-Events", "1"), ("Sec-Fetch-Site", fetch_site)])
        if passes:
            enforce_floor(request)
        else:
            with pytest.raises(EventError):
                enforce_floor(request)


class TestCsrfCheckThroughDispatch:
    """The per-handler policy layer, exercised where it runs: per call."""

    def _dispatch_with(self, c, comp_cls, event_name, request, **call_extra):
        call = {"componentClassId": comp_cls.class_id, "handlerName": event_name, "args": {}, **call_extra}
        envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": [call]}
        ctx = TransportContext(transport="http", citry=c, headers=request.headers)
        return EventsDispatcher().dispatch(envelope, ctx, csrf_check=build_csrf_check(request))

    def test_floor_failure_answers_the_fixture_wire_error(self):
        c = _citry()
        greeter = _greeter(c)
        result = self._dispatch_with(c, greeter, "quiet", _request(), stateToken=_token(greeter))
        error = result["results"][0]["error"]
        assert error == {"status": 403, "code": "csrf_failed", "message": CSRF_FAILED_MESSAGE}

    def test_get_calls_skip_csrf_entirely(self):
        c = _citry()
        greeter = _greeter(c)
        # A GET without the header and with a hostile Origin still passes:
        # GET handlers are read-only by contract and csrf-exempt.
        request = _request(method="GET", content_type="", headers=[("Origin", "https://evil.example")])
        result = self._dispatch_with(c, greeter, "echo", request, args={"text": "hi"})
        assert result["results"][0]["ok"] is True

    def test_callable_policy_replaces_the_token_check(self):
        seen = {}

        def policy(request):
            seen["request"] = request
            raise EventError("Bad token.", status=403)

        c = _citry()

        class Locked(Component):
            citry = c
            template = "<div>l</div>"

            class Events:
                @event(csrf=policy)
                def go(self):
                    return None

        request = _request(headers=[("X-Citry-Events", "1")])
        result = self._dispatch_with(c, Locked, "go", request)
        error = result["results"][0]["error"]
        # The policy's own message rides, under the csrf_failed code.
        assert error == {"status": 403, "code": "csrf_failed", "message": "Bad token."}
        assert seen["request"] is request

    def test_csrf_false_drops_only_the_token_layer(self):
        c = _citry()

        class Open(Component):
            citry = c
            template = "<div>o</div>"

            class Events:
                @event(csrf=False)
                def go(self):
                    return None

        # The floor never turns off: a JSON post without the header still fails.
        result = self._dispatch_with(c, Open, "go", _request())
        assert result["results"][0]["error"]["code"] == "csrf_failed"
        # With the floor satisfied, csrf=False adds no further check.
        result = self._dispatch_with(c, Open, "go", _request(headers=[("X-Citry-Events", "1")]))
        assert result["results"][0]["ok"] is True


################################################
# URL BUILDING
################################################


class TestEventUrls:
    def test_get_event_url_builds_on_build_url_and_format_url(self):
        c = _citry()
        greeter = _greeter(c)
        url = get_event_url(greeter, "save", query={"q": "milk"}, fragment="top")
        assert url == f"/citry/ext/events/e/{greeter.class_id}/save?q=milk#top"

    def test_get_event_url_preserves_the_full_query_and_fragment_encoding_contract(self):
        c = _citry()
        greeter = _greeter(c)
        url = get_event_url(
            greeter,
            "save",
            query={"f'oo": "b ar&ba'z", "true_key": True, "false_key": False, "none_key": None},
            fragment='q u"x',
        )
        assert url == (f"/citry/ext/events/e/{greeter.class_id}/save?f%27oo=b+ar%26ba%27z&true_key#q%20u%22x")

    def test_unknown_event_fails_at_build_time(self):
        c = _citry()
        greeter = _greeter(c)
        with pytest.raises(ValueError, match="has no event 'svae'") as excinfo:
            get_event_url(greeter, "svae")
        assert "declared events:" in str(excinfo.value)

    def test_unmounted_engine_raises_the_standard_error(self):
        c = Citry(secret=SIGNING_KEY)
        greeter = _greeter(c)
        with pytest.raises(RuntimeError, match="no web integration is mounted"):
            get_event_url(greeter, "save")

    def test_component_events_url_during_render(self):
        c = _citry()

        class Form(Component):
            citry = c

            class Events:
                def submit(self):
                    return None

            def template_data(self, kwargs, slots):
                return {"action": self.events.url("submit")}

            template = """
                <form method="post">{{ action }}</form>
            """

        html = str(Form())
        assert f"/citry/ext/events/e/{Form.class_id}/submit" in html

    def test_the_woven_config_and_the_typing_base_share_url(self):
        # The url method rides the one class the weaving uses, which is also
        # the public typing base (citry.Events).
        import citry as citry_module

        assert citry_module.Events.url is events_config_url

    def test_typing_base_url_names_the_required_component_config(self):
        import citry as citry_module

        with pytest.raises(RuntimeError, match=r"call it as component\.events\.url"):
            citry_module.Events(None).url("save")


################################################
# END TO END OVER FASTAPI
################################################

fastapi = pytest.importorskip("fastapi", reason="the events route tests need fastapi + httpx")
pytest.importorskip("httpx", reason="Starlette's TestClient needs httpx")

from fastapi.testclient import TestClient  # noqa: E402

RUNTIME_HEADERS = {"X-Citry-Events": "1"}
ENVELOPE_CONTENT_TYPE = "application/citry-events+json"


def _mounted(c):
    from citry.contrib.fastapi import mount

    app = fastapi.FastAPI()
    mount(app, c)
    return TestClient(app)


def _event_url(comp_cls, name):
    return f"/citry/ext/events/e/{comp_cls.class_id}/{name}"


def _post_envelope(client, url, envelope, headers=None, **kwargs):
    """POST an envelope the way the runtime does: vendor media type plus the runtime header."""
    if "/ext/events/e/" in url:
        component_class_id, handler_name = url.rsplit("/", 2)[-2:]
        envelope = {
            **envelope,
            "calls": [
                {
                    "componentClassId": component_class_id,
                    "handlerName": handler_name,
                    **call,
                }
                if isinstance(call, dict)
                else call
                for call in envelope.get("calls", [])
            ],
        }
    all_headers = {"Content-Type": ENVELOPE_CONTENT_TYPE, **RUNTIME_HEADERS, **(headers or {})}
    return client.post(url, content=json.dumps(envelope), headers=all_headers, **kwargs)


def _post_call(client, comp_cls, name, call, headers=None, **kwargs):
    envelope = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "calls": [
            {
                "componentClassId": comp_cls.class_id,
                "handlerName": name,
                "args": {},
                **call,
            }
        ],
    }
    return _post_envelope(client, _event_url(comp_cls, name), envelope, headers=headers, **kwargs)


class TestPerEventRoute:
    def test_full_pipeline_renders_and_mirrors_200(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = _post_call(
            client,
            greeter,
            "save",
            {"callerRenderId": "i1", "args": {"text": "Hello"}, "stateToken": _token(greeter), "sendSequence": 2},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        envelope = response.json()
        assert envelope["protocol"] == "citry-events/1"
        [item] = envelope["results"]
        assert item["ok"] is True
        assert item["sendSequence"] == 2
        [action] = item["actions"]
        assert action["action"] == "render"
        # The fragment's root carries the instance markers.
        assert ">Hello</p>" in action["html"]
        assert "data-cid" in action["html"]

    def test_error_statuses_mirror_onto_http(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)

        # unknown event -> 404
        response = _post_envelope(
            client,
            _event_url(greeter, "nope"),
            {"protocol": "citry-events/1", "requestId": "r1", "calls": [{"args": {}}]},
        )
        assert response.status_code == 404
        assert response.json()["results"][0]["error"]["code"] == "unknown_event"

        # missing token on a state handler -> 403
        response = _post_call(client, greeter, "quiet", {"args": {}})
        assert response.status_code == 403
        assert response.json()["results"][0]["error"]["code"] == "invalid_state"

    def test_url_vs_body_mismatch_is_rejected(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = _post_call(client, greeter, "save", {"handlerName": "quiet", "args": {}})
        assert response.status_code == 400
        assert "the URL is authoritative" in response.json()["results"][0]["error"]["message"]

    def test_non_standard_json_literal_in_the_envelope_is_rejected(self):
        # Python's json.loads tolerates Infinity, but it is not JSON: the
        # body is rejected at decode, before it can bind a float the JSON
        # result envelope could not carry back to the client.
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        body = '{"protocol": "citry-events/1", "requestId": "r1", "calls": [{"args": {"ratio": Infinity}}]}'
        response = client.post(
            _event_url(greeter, "quiet"),
            content=body.encode(),
            headers={"Content-Type": ENVELOPE_CONTENT_TYPE, **RUNTIME_HEADERS},
        )
        assert response.status_code == 400
        error = response.json()["results"][0]["error"]
        assert error["code"] == "protocol_mismatch"
        assert error["message"] == (
            "The request body is not valid JSON; the events endpoints take a citry-events/1 call envelope."
        )

    def test_method_allowlist_is_a_plain_405(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = _post_call(client, greeter, "echo", {"args": {}})
        assert response.status_code == 405
        assert response.headers["allow"] == "GET"

    def test_multi_call_envelope_is_rejected_on_the_per_event_route(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [
                {"args": {}, "sendSequence": 4},
                "not-an-object",
                {"args": {}, "sendSequence": True},
                {"args": {}, "sendSequence": -1},
                {"args": {}, "sendSequence": "7"},
                {"args": {}, "sendSequence": 0},
            ],
        }
        response = _post_envelope(client, _event_url(greeter, "quiet"), envelope)
        assert response.status_code == 400
        body = response.json()
        assert body["requestId"] == "r1"
        assert [result.get("sendSequence") for result in body["results"]] == [4, None, None, None, None, 0]
        assert len(body["results"]) == len(envelope["calls"])
        assert all("takes a single call" in result["error"]["message"] for result in body["results"])

    def test_compat_multi_call_envelope_is_a_plain_text_400(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r_compat_batch",
            "calls": [{"args": {}}, {"args": {}}],
        }
        response = _post_envelope(
            client,
            _event_url(greeter, "quiet"),
            envelope,
            headers={"Accept": "text/html"},
        )
        assert response.status_code == 400
        assert response.headers["content-type"].startswith("text/plain")
        assert response.text == (
            "The per-event route takes a single call; this envelope carries 2. Use ext/events/call for batches."
        )

    def test_missing_runtime_header_is_csrf_failed(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [
                {
                    "componentClassId": greeter.class_id,
                    "handlerName": "quiet",
                    "args": {},
                    "stateToken": _token(greeter),
                }
            ],
        }
        # The envelope's vendor media type without the header: the floor
        # covers every JSON-bodied call (design 7.4).
        response = client.post(
            _event_url(greeter, "quiet"),
            content=json.dumps(envelope),
            headers={"Content-Type": ENVELOPE_CONTENT_TYPE},
        )
        assert response.status_code == 403
        assert response.json()["results"][0]["error"]["code"] == "csrf_failed"

    def test_cross_origin_is_rejected(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = _post_call(
            client,
            greeter,
            "quiet",
            {"args": {}, "stateToken": _token(greeter)},
            headers={"Origin": "https://evil.example"},
        )
        assert response.status_code == 403
        assert response.json()["results"][0]["error"]["code"] == "csrf_failed"

    def test_same_origin_passes(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = _post_call(
            client,
            greeter,
            "quiet",
            {"args": {}, "stateToken": _token(greeter)},
            headers={"Origin": "http://testserver"},
        )
        assert response.status_code == 200

    def test_envelope_size_cap_is_configured_per_engine(self):
        # The byte cap rides extensions_defaults["events"] (design 3.5);
        # routes.MAX_ENVELOPE_BYTES is only the unconfigured default.
        c = _citry(extensions_defaults={"events": {"_max_envelope_bytes": 64}})
        greeter = _greeter(c)
        client = _mounted(c)
        big = {"protocol": "citry-events/1", "requestId": "r1", "calls": [{"args": {"text": "x" * 200}}]}
        response = _post_envelope(client, _event_url(greeter, "quiet"), big)
        assert response.status_code == 413
        error = response.json()["results"][0]["error"]
        assert error["code"] == "payload_too_large"
        assert "the cap is 64" in error["message"]


class TestGetHandlers:
    def test_pasteable_get_is_tokenless_and_no_store(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = client.get(_event_url(greeter, "echo"), params={"text": "hi"})
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        [item] = response.json()["results"]
        assert item == {"ok": True, "actions": [{"action": "data", "value": {"echo": "hi"}}]}

    def test_state_declaring_get_reads_the_token_parameter(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        token = _token(greeter, text="stored")
        response = client.get(_event_url(greeter, "peek"), params={"_citry_state_token": token})
        assert response.status_code == 200
        assert response.json()["results"][0]["actions"][0]["value"] == {"text": "stored"}

        # Without the token the call cannot rebuild state: 403 invalid_state.
        response = client.get(_event_url(greeter, "peek"))
        assert response.status_code == 403
        assert response.json()["results"][0]["error"]["code"] == "invalid_state"

    def test_browser_get_preserves_protocol_mismatch_and_correlation(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = client.get(
            _event_url(greeter, "echo"),
            params={
                "text": "hi",
                "_citry_protocol": "citry-events/2",
                "_citry_request_id": "r_get_skew",
                "_citry_capabilities": json.dumps({"swaps": ["morph"]}),
            },
        )
        assert response.status_code == 400
        payload = response.json()
        assert payload["protocol"] == "citry-events/1"
        assert payload["requestId"] == "r_get_skew"
        assert payload["results"][0]["error"]["code"] == "protocol_mismatch"

    @pytest.mark.parametrize(
        ("query_key", "query_values"),
        [
            pytest.param("_citry_send_sequence", ["not-an-integer"], id="non-integer-epoch"),
            pytest.param("_citry_send_sequence", ["1", "2"], id="repeated-epoch"),
            pytest.param(
                "_citry_capabilities",
                [json.dumps({"actions": ["data"]}), json.dumps({"actions": ["render"]})],
                id="repeated-capabilities",
            ),
        ],
    )
    def test_browser_get_rejects_malformed_reserved_metadata(self, query_key, query_values):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        params = [("text", "hi"), *((query_key, value) for value in query_values)]
        response = client.get(_event_url(greeter, "echo"), params=params)
        assert response.status_code == 400
        [result] = response.json()["results"]
        assert result["ok"] is False
        assert result["error"]["code"] == "protocol_mismatch"

    def test_explicit_cache_control_on_raw_get_response_is_preserved(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = client.get(_event_url(greeter, "cached"), headers=RUNTIME_HEADERS)
        cache_headers = [value for name, value in response.headers.raw if name.lower() == b"cache-control"]
        assert response.status_code == 200
        assert response.text == "cached"
        assert cache_headers == [b"public, max-age=60"]


class TestBatchRoute:
    def test_batch_always_answers_200_with_statuses_inside(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [
                {"componentClassId": greeter.class_id, "handlerName": "echo", "args": {"text": "one"}},
                {"componentClassId": greeter.class_id, "handlerName": "nope", "args": {}},
            ],
        }
        # Posted as plain application/json on purpose: the batch route takes
        # the envelope under either media type (design 6.2).
        response = client.post("/citry/ext/events/call", json=envelope, headers=RUNTIME_HEADERS)
        assert response.status_code == 200
        first, second = response.json()["results"]
        assert first["ok"] is True
        assert second["error"]["status"] == 404

    def test_batch_accepts_the_envelope_under_the_vendor_type(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [{"componentClassId": greeter.class_id, "handlerName": "echo", "args": {"text": "one"}}],
        }
        response = _post_envelope(client, "/citry/ext/events/call", envelope)
        assert response.status_code == 200
        assert response.json()["results"][0]["ok"] is True

    def test_flat_shaped_json_answers_the_pointed_mismatch(self):
        # Flat handler fields belong on the per-event route; on the batch
        # route the rejection names the envelope and that alternative.
        c = _citry()
        client = _mounted(c)
        response = client.post("/citry/ext/events/call", json={"email": "a@b.c"}, headers=RUNTIME_HEADERS)
        assert response.status_code == 200  # batch always answers 200
        [item] = response.json()["results"]
        error = item["error"]
        assert error["status"] == 400
        assert error["code"] == "protocol_mismatch"
        assert "takes the citry-events/1 call envelope" in error["message"]
        assert "ext/events/e/{class_id}/{event}" in error["message"]

    def test_form_posts_are_not_a_batch_shape(self):
        c = _citry()
        client = _mounted(c)
        response = client.post("/citry/ext/events/call", data={"text": "hi"}, headers=RUNTIME_HEADERS)
        assert response.status_code == 200  # batch always answers 200
        error = response.json()["results"][0]["error"]
        assert error["code"] == "protocol_mismatch"
        assert "batch endpoint" in error["message"]

    def test_get_on_the_batch_route_is_405(self):
        c = _citry()
        client = _mounted(c)
        assert client.get("/citry/ext/events/call").status_code == 405


class TestFlatJsonRoute:
    """
    The per-event route's plain-JSON shape (design 6.2): one flat object of
    handler fields, for API clients that do not speak the protocol. The
    envelope rides its own vendor media type, so the two shapes never
    collide and nothing sniffs the body.
    """

    def test_registered_codecs_are_scanned_in_order_before_built_ins(self):
        class UnclaimedCodec:
            content_type = "application/msgpack"

            def decode(self, body, request):
                pytest.fail("an unclaimed codec must not run")

        class ClaimedJsonCodec:
            content_type = "application/json"

            def decode(self, body, request):
                assert body == b"deliberately not JSON"
                return {
                    "protocol": "citry-events/1",
                    "requestId": "custom-codec",
                    "calls": [{"args": {"text": "decoded by user codec"}}],
                }

        c = _citry(event_payload_codecs=[UnclaimedCodec(), ClaimedJsonCodec()])
        greeter = _greeter(c)
        client = _mounted(c)
        response = client.post(
            _event_url(greeter, "codec_echo"),
            content=b"deliberately not JSON",
            headers={"Content-Type": "application/json", **RUNTIME_HEADERS},
        )
        assert response.status_code == 200
        assert response.json() == {
            "protocol": "citry-events/1",
            "requestId": "custom-codec",
            "results": [
                {"ok": True, "actions": [{"action": "data", "value": {"echo": "decoded by user codec"}}]},
            ],
        }

    def _tally(self, c):
        class CountIn:
            count: int

        class Tally(Component):
            citry = c
            template = "<div>t</div>"

            class Events:
                def add(self, data: CountIn):
                    return {"total": data.count + 1}

        return Tally

    def test_flat_fields_dispatch_the_handler(self):
        c = _citry()
        tally = self._tally(c)
        client = _mounted(c)
        response = client.post(_event_url(tally, "add"), json={"count": 3}, headers=RUNTIME_HEADERS)
        assert response.status_code == 200
        envelope = response.json()
        assert envelope["requestId"] == "flat"
        assert envelope["results"][0]["actions"] == [{"action": "data", "value": {"total": 4}}]

    def test_flat_fields_bind_per_the_strict_json_rules(self):
        # Flat JSON is still JSON: a string where the schema declares int is
        # the strict 422 (design 3.3), never the string-transport binding.
        c = _citry()
        tally = self._tally(c)
        client = _mounted(c)
        response = client.post(_event_url(tally, "add"), json={"count": "3"}, headers=RUNTIME_HEADERS)
        assert response.status_code == 422
        error = response.json()["results"][0]["error"]
        assert error["code"] == "invalid_args"
        assert error["fieldErrors"] == {"count": "Expected int, got str."}

    def test_non_standard_json_literals_are_rejected(self):
        # Python's json.loads tolerates Infinity, but it is not JSON: the
        # body is rejected at decode, so the result envelope stays JSON a
        # conforming client can parse.
        c = _citry()
        tally = self._tally(c)
        client = _mounted(c)
        response = client.post(
            _event_url(tally, "add"),
            content=b'{"ratio": Infinity}',
            headers={"Content-Type": "application/json", **RUNTIME_HEADERS},
        )
        assert response.status_code == 400
        error = response.json()["results"][0]["error"]
        assert error["code"] == "protocol_mismatch"
        assert error["message"] == (
            "The request body is not valid JSON; the per-event route takes the handler's fields as one object."
        )

    def test_number_overflow_to_infinity_is_rejected(self):
        # 1e400 is valid JSON grammar that Python would read as inf; it
        # answers the same 400 as the non-standard literals, so a non-finite
        # float can never enter through a JSON body.
        c = _citry()
        tally = self._tally(c)
        client = _mounted(c)
        response = client.post(
            _event_url(tally, "add"),
            content=b'{"ratio": 1e400}',
            headers={"Content-Type": "application/json", **RUNTIME_HEADERS},
        )
        assert response.status_code == 400
        error = response.json()["results"][0]["error"]
        assert error["code"] == "protocol_mismatch"
        assert error["message"] == (
            "The request body is not valid JSON; the per-event route takes the handler's fields as one object."
        )

    def test_reserved_keys_map_like_the_form_codecs(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = client.post(
            _event_url(greeter, "save"),
            json={"text": "Hi", "_citry_state_token": _token(greeter), "_citry_caller_render_id": "i1"},
            headers=RUNTIME_HEADERS,
        )
        assert response.status_code == 200
        [action] = response.json()["results"][0]["actions"]
        assert action["action"] == "render"
        assert ">Hi</p>" in action["html"]

    def test_envelope_shaped_body_still_binds_as_flat_fields(self):
        # Classification never depends on body shape: under plain
        # application/json even an envelope-shaped object is handler fields
        # (a schema could legitimately declare a field named "calls").
        c = _citry()
        tally = self._tally(c)
        client = _mounted(c)
        envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": [{"args": {"count": 3}}]}
        response = client.post(_event_url(tally, "add"), json=envelope, headers=RUNTIME_HEADERS)
        assert response.status_code == 422
        error = response.json()["results"][0]["error"]
        assert error["code"] == "invalid_args"
        assert error["fieldErrors"] == {
            "calls": "Unexpected field: not declared on the schema.",
            "count": "This field is required.",
            "requestId": "Unexpected field: not declared on the schema.",
            "protocol": "Unexpected field: not declared on the schema.",
        }

    def test_flat_json_without_the_header_is_csrf_failed(self):
        # The one static header an API client must send (design 7.4).
        c = _citry()
        tally = self._tally(c)
        client = _mounted(c)
        response = client.post(_event_url(tally, "add"), json={"count": 3})
        assert response.status_code == 403
        assert response.json()["results"][0]["error"]["code"] == "csrf_failed"


class TestAsyncEventHandlersUnderAsgi:
    """
    Design 6.2 under the ASGI adapter: the dispatch routes run through
    ``EventsDispatcher.dispatch_async``, so ``async def`` event handlers are
    awaited natively on the event loop while plain handlers stay off it.
    """

    def _mixed(self, c):
        """A component with one async and one sync handler, recording where each ran."""
        seen = {}

        class Mixed(Component):
            citry = c

            class Events:
                async def afetch(self):
                    await asyncio.sleep(0)
                    # A running loop is only observable from a native await;
                    # a worker thread has none.
                    seen["async_loop"] = asyncio.get_running_loop()
                    return {"kind": "async"}

                def sfetch(self):
                    try:
                        asyncio.get_running_loop()
                    except RuntimeError:
                        seen["sync_on_loop"] = False
                    else:
                        seen["sync_on_loop"] = True
                    return {"kind": "sync"}

            template = """
                <div>m</div>
            """

        return Mixed, seen

    def test_async_handler_round_trips_on_the_per_event_route(self):
        c = _citry()
        mixed, seen = self._mixed(c)
        client = _mounted(c)
        response = _post_call(client, mixed, "afetch", {"args": {}})
        assert response.status_code == 200
        [item] = response.json()["results"]
        assert item["ok"] is True
        assert item["actions"][0]["value"] == {"kind": "async"}
        assert seen["async_loop"] is not None

    def test_sync_handler_still_works_and_stays_off_the_loop(self):
        c = _citry()
        mixed, seen = self._mixed(c)
        client = _mounted(c)
        response = _post_call(client, mixed, "sfetch", {"args": {}})
        assert response.status_code == 200
        assert response.json()["results"][0]["actions"][0]["value"] == {"kind": "sync"}
        assert seen["sync_on_loop"] is False

    def test_async_and_sync_handlers_through_the_batch_route(self):
        c = _citry()
        mixed, _seen = self._mixed(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [
                {"componentClassId": mixed.class_id, "handlerName": "afetch", "args": {}},
                {"componentClassId": mixed.class_id, "handlerName": "sfetch", "args": {}},
            ],
        }
        response = client.post("/citry/ext/events/call", json=envelope, headers=RUNTIME_HEADERS)
        assert response.status_code == 200
        values = [item["actions"][0]["value"] for item in response.json()["results"]]
        assert values == [{"kind": "async"}, {"kind": "sync"}]


class TestRuntimeRoute:
    def test_serves_the_built_runtime_bundle_and_matches_the_emitted_path(self):
        from citry.ext.events.emission import RUNTIME_PATH as EMITTED_PATH

        assert RUNTIME_PATH == EMITTED_PATH
        c = _citry()
        client = _mounted(c)
        response = client.get("/citry/ext/events/runtime.js")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/javascript")
        # The bundle's generated-file banner is its identifying marker
        # (observed from the built file; the versions behind it may move).
        assert "Citry events client runtime. GENERATED FILE" in response.text

    def test_the_emitted_script_url_is_servable(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        page = type("Page", (Component,), {"citry": c, "template": "<main><c-greeter /></main>"})
        html = str(page())
        assert '"/citry/ext/events/runtime.js"' in html or "/citry/ext/events/runtime.js" in html
        assert client.get("/citry/ext/events/runtime.js").status_code == 200
        del greeter


class TestCompatMode:
    def test_form_post_round_trip_renders_html(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = client.post(
            _event_url(greeter, "save"),
            data={"text": "No JS", "_citry_state_token": _token(greeter), "_citry_caller_render_id": "i1"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert ">No JS</p>" in response.text

    def test_redirect_becomes_a_303(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = client.post(
            _event_url(greeter, "finish"),
            data={"text": "done", "_citry_state_token": _token(greeter)},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/done"

    def test_acknowledged_call_is_a_204(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = client.post(_event_url(greeter, "quiet"), data={"_citry_state_token": _token(greeter)})
        assert response.status_code == 204

    def test_history_only_call_is_a_204_without_a_redirect_location(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = client.post(_event_url(greeter, "history"), data={"_citry_caller_render_id": "i1"})
        assert response.status_code == 204
        assert "location" not in response.headers

    def test_errors_carry_their_status_as_text(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        # A form post without the token: the state handler cannot run.
        response = client.post(_event_url(greeter, "quiet"), data={"x": "1"})
        assert response.status_code == 403
        assert response.headers["content-type"].startswith("text/plain")
        assert "state token" in response.text

    def test_pasted_get_url_answers_the_data_value(self):
        # A GET URL opened in a browser (Accept: text/html) still shows the
        # handler's data instead of an envelope.
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = client.get(
            _event_url(greeter, "echo"),
            params={"text": "hi"},
            headers={"Accept": "text/html"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert response.json() == {"echo": "hi"}

    def test_accept_html_selects_compat_for_runtime_shaped_requests(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [{"callerRenderId": "i1", "args": {"text": "Hi"}, "stateToken": _token(greeter)}],
        }
        response = _post_envelope(
            client,
            _event_url(greeter, "save"),
            envelope,
            headers={"Accept": "text/html"},
        )
        assert response.status_code == 200
        assert ">Hi</p>" in response.text


class TestRouteResponseEscape:
    def test_served_as_is_on_the_per_event_route(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = _post_envelope(
            client,
            _event_url(greeter, "export"),
            {"protocol": "citry-events/1", "requestId": "r1", "calls": [{"args": {}}]},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert response.headers["content-disposition"] == 'attachment; filename="x.csv"'
        assert response.content == b"csv,data"

    def test_batch_rejects_it_loudly(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [{"componentClassId": greeter.class_id, "handlerName": "export", "args": {}}],
        }
        response = client.post("/citry/ext/events/call", json=envelope, headers=RUNTIME_HEADERS)
        assert response.status_code == 200
        assert response.json()["results"][0]["error"]["code"] == "handler_error"


class TestDownloadResponse:
    def test_serves_unicode_filename_and_body_on_the_per_event_route(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = _post_envelope(
            client,
            _event_url(greeter, "download"),
            {"protocol": "citry-events/1", "requestId": "r1", "calls": [{"args": {}}]},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv; charset=utf-8")
        assert response.headers["content-disposition"] == (
            "attachment; filename=\"prehled.csv\"; filename*=UTF-8''p%C5%99ehled.csv"
        )
        assert response.headers["cache-control"] == "no-store"
        assert response.content == b"name\nAda"

    def test_batch_rejects_download(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [{"componentClassId": greeter.class_id, "handlerName": "download", "args": {}}],
        }
        response = client.post("/citry/ext/events/call", json=envelope, headers=RUNTIME_HEADERS)
        assert response.status_code == 200
        assert response.json()["results"][0]["error"]["code"] == "handler_error"

    def test_get_download_is_raw_and_has_exactly_one_no_store_header(self):
        c = _citry()
        greeter = _greeter(c)
        client = _mounted(c)
        response = client.get(_event_url(greeter, "download_get"), headers=RUNTIME_HEADERS)
        cache_headers = [value for name, value in response.headers.raw if name.lower() == b"cache-control"]
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert response.headers["content-disposition"] == (
            "attachment; filename=\"report.csv\"; filename*=UTF-8''report.csv"
        )
        assert cache_headers == [b"no-store"]
        assert response.content == b"csv,data"


def _strict_json(text):
    """Parse like a conforming client: any Infinity/NaN literal in the body fails the test."""

    def _reject(literal):
        msg = f"non-JSON literal {literal} in the response body"
        raise AssertionError(msg)

    return json.loads(text, parse_constant=_reject)


class TestNonFiniteResultValues:
    """
    The egress twin of the codecs' non-finite rejection: json.dumps would
    emit the non-JSON literals Infinity / NaN for a non-finite float a
    handler returned, and a conforming client could not parse the response
    (spec section 2: all envelopes are JSON). The dispatcher validates its
    completed result with allow_nan=False and replaces the failing call with
    the pointed handler_error before either response mode serializes it.
    """

    def _meter(self, c):
        class Meter(Component):
            citry = c
            template = "<div>m</div>"

            class Events:
                def blow_up(self):
                    return {"ratio": float("inf")}

                def fine(self):
                    return {"n": 1}

                def decimal(self):
                    return {"amount": Decimal("1.25")}

                def decimal_inf(self):
                    return {"amount": Decimal("Infinity")}

                @event(methods=("GET",))
                def peek_inf(self):
                    return {"ratio": float("nan")}

                @event(methods=("GET",))
                def peek_decimal(self):
                    return {"amount": Decimal("1.25")}

        return Meter

    def test_per_event_result_becomes_the_pointed_handler_error(self):
        c = _citry()
        meter = self._meter(c)
        client = _mounted(c)
        response = client.post(_event_url(meter, "blow_up"), json={}, headers=RUNTIME_HEADERS)
        assert response.status_code == 500
        [result] = _strict_json(response.text)["results"]
        assert result == {
            "ok": False,
            "error": {"status": 500, "code": "handler_error", "message": UNENCODABLE_RESULT_MESSAGE},
        }

    def test_batch_keeps_the_other_results_and_stays_strict_json(self):
        # Only the failing call's result is replaced; the batch contract
        # (HTTP 200, per-call statuses inside) and the epoch echo survive.
        c = _citry()
        meter = self._meter(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [
                {"componentClassId": meter.class_id, "handlerName": "fine", "args": {}, "sendSequence": 4},
                {"componentClassId": meter.class_id, "handlerName": "blow_up", "args": {}, "sendSequence": 7},
            ],
        }
        response = client.post("/citry/ext/events/call", json=envelope, headers=RUNTIME_HEADERS)
        assert response.status_code == 200
        good, bad = _strict_json(response.text)["results"]
        assert good == {"ok": True, "sendSequence": 4, "actions": [{"action": "data", "value": {"n": 1}}]}
        assert bad == {
            "ok": False,
            "sendSequence": 7,
            "error": {"status": 500, "code": "handler_error", "message": UNENCODABLE_RESULT_MESSAGE},
        }

    @pytest.mark.parametrize("event_name", ["decimal", "decimal_inf"])
    def test_decimal_result_becomes_the_pointed_handler_error(self, event_name):
        c = _citry()
        meter = self._meter(c)
        client = _mounted(c)
        response = client.post(_event_url(meter, event_name), json={}, headers=RUNTIME_HEADERS)
        assert response.status_code == 500
        assert _strict_json(response.text)["results"] == [
            {
                "ok": False,
                "error": {"status": 500, "code": "handler_error", "message": UNENCODABLE_RESULT_MESSAGE},
            }
        ]

    def test_decimal_result_repair_isolated_to_its_batch_slot(self):
        c = _citry()
        meter = self._meter(c)
        client = _mounted(c)
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [
                {"componentClassId": meter.class_id, "handlerName": "decimal", "args": {}, "sendSequence": 2},
                {"componentClassId": meter.class_id, "handlerName": "fine", "args": {}, "sendSequence": 3},
            ],
        }
        response = client.post("/citry/ext/events/call", json=envelope, headers=RUNTIME_HEADERS)
        first, second = _strict_json(response.text)["results"]
        assert first["sendSequence"] == 2
        assert first["error"]["code"] == "handler_error"
        assert second == {"ok": True, "sendSequence": 3, "actions": [{"action": "data", "value": {"n": 1}}]}

    @pytest.mark.parametrize("event_name", ["peek_inf", "peek_decimal"])
    def test_compat_data_value_answers_plain_text_500(self, event_name):
        # The compat / no-JS mode has no envelope to repair; like any compat
        # error, the failure carries its status as plain text.
        c = _citry()
        meter = self._meter(c)
        client = _mounted(c)
        response = client.get(_event_url(meter, event_name), headers={"Accept": "text/html"})
        assert response.status_code == 500
        assert response.headers["content-type"].startswith("text/plain")
        assert response.text == UNENCODABLE_RESULT_MESSAGE


################################################
# TYPED FIELDS THROUGH THE FORM AND QUERY CODECS
################################################


class TestFormAndQueryTypedFields:
    """
    Form posts and GET query strings deliver every value as a string, and
    the binding is source-aware (design 3.3): the form and query codecs mark
    their payloads as ``StringArgs``, so on those paths strings bind to
    declared ``int`` / ``float`` / ``bool`` fields. A JSON payload stays
    strict (a string where the schema declares ``int`` is a 422 there): JSON
    expresses those types natively, so a mistyped field is a client bug
    worth surfacing. The full binding matrix lives in
    test_events_schemas.py; these tests prove the rule end to end over
    the HTTP routes.
    """

    def _tally(self, c):
        class CountIn:
            count: int

        class Tally(Component):
            citry = c
            template = "<div>t</div>"

            class Events:
                def add(self, data: CountIn):
                    return {"total": data.count + 1}

                @event(methods=("GET",))
                def peek(self, data: CountIn):
                    return {"total": data.count + 1}

        return Tally

    def test_form_post_binds_an_int_field(self):
        c = _citry()
        tally = self._tally(c)
        client = _mounted(c)

        # A plain form post (compat mode) sends count as the string "3"; the
        # form codec's StringArgs marking makes it bind to the int field.
        response = client.post(_event_url(tally, "add"), data={"count": "3"})
        assert response.status_code == 200
        assert response.json() == {"total": 4}

        # A string the int grammar cannot read is still the per-field 422.
        response = client.post(_event_url(tally, "add"), data={"count": "x"})
        assert response.status_code == 422
        assert response.headers["content-type"].startswith("text/plain")
        assert response.text == (
            "The args for event 'add' on component 'Tally' did not validate.\ncount: Not a valid int: 'x'."
        )

    def test_json_payloads_stay_strict(self):
        c = _citry()
        tally = self._tally(c)
        client = _mounted(c)

        # From JSON, 3 arrives as a real int and binds.
        envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": [{"args": {"count": 3}}]}
        response = _post_envelope(client, _event_url(tally, "add"), envelope)
        assert response.status_code == 200
        assert response.json()["results"][0]["actions"] == [{"action": "data", "value": {"total": 4}}]

        # The string "3" in a JSON payload is the strict 422, not a binding.
        envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": [{"args": {"count": "3"}}]}
        response = _post_envelope(client, _event_url(tally, "add"), envelope)
        assert response.status_code == 422
        error = response.json()["results"][0]["error"]
        assert error["code"] == "invalid_args"
        assert error["fieldErrors"] == {"count": "Expected int, got str."}

    def test_pasted_get_url_binds_an_int_field(self):
        c = _citry()
        tally = self._tally(c)
        client = _mounted(c)
        response = client.get(_event_url(tally, "peek"), params={"count": "3"})
        assert response.status_code == 200
        assert response.json()["results"][0]["actions"] == [{"action": "data", "value": {"total": 4}}]

        response = client.get(_event_url(tally, "peek"), params={"count": "abc"})
        assert response.status_code == 422
        error = response.json()["results"][0]["error"]
        assert error["code"] == "invalid_args"
        assert error["fieldErrors"] == {"count": "Not a valid int: 'abc'."}

    def test_design_3_5_get_example_binds_end_to_end(self):
        # The design 3.5 example: a read-only GET handler whose int arg
        # arrives as a query-string value and binds source-aware.
        c = _citry()

        class WordCountIn:
            doc_id: int

        def count_words(doc_id):
            return len(("one two three " * doc_id).split())

        class Document(Component):
            citry = c
            template = "<div>d</div>"

            class Events:
                @event(methods=("GET",))
                def word_count(self, data: WordCountIn) -> dict:
                    return {"words": count_words(data.doc_id)}

        client = _mounted(c)
        response = client.get(_event_url(Document, "word_count"), params={"doc_id": "2"})
        assert response.status_code == 200
        assert response.json()["results"][0]["actions"] == [{"action": "data", "value": {"words": 6}}]


################################################
# THE ENVELOPE CAP CONFIG NAME
################################################


class TestEnvelopeCapConfig:
    """
    ``_max_envelope_bytes`` is engine-wide: the cap guards the transport
    before any component resolves, so only ``extensions_defaults["events"]``
    may set it (the HTTP effect is covered by
    ``TestPerEventRoute.test_envelope_size_cap_is_configured_per_engine``).
    """

    def test_component_level_declaration_fails_at_class_definition(self):
        c = _citry()
        with pytest.raises(ValueError, match="engine-wide") as err:

            class Capped(Component):
                citry = c
                template = "<div>c</div>"

                class Events:
                    _max_envelope_bytes = 64

                    def go(self):
                        return None

        assert (
            "'_max_envelope_bytes' is engine-wide configuration; set it in"
            " extensions_defaults['events'], not on a component's Events class." in str(err.value)
        )

    def test_bad_value_fails_at_engine_construction(self):
        with pytest.raises(ValueError, match="_max_envelope_bytes") as err:
            _citry(extensions_defaults={"events": {"_max_envelope_bytes": "big"}})
        assert "'_max_envelope_bytes' must be a positive int (a byte count); got 'big'." in str(err.value)
