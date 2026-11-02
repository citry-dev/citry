"""Check the Events action, error, result and envelope builders and the validators behind them."""

from __future__ import annotations

import pytest

from citry._protocol import events

_RENDER = "render:r1"
_ACTION = {"action": "render", "target": _RENDER, "swap": "inner", "html": "<b>x</b>"}
_ERROR = {"status": 404, "code": "not_found", "message": "gone"}
_OK = {"ok": True, "actions": [_ACTION]}


def _first_issue(validator, value):
    issue = validator(value)
    assert issue is not None, value
    return issue.path, issue.category


@pytest.mark.parametrize(
    ("action", "path", "category"),
    [
        ([], "", "type"),
        ({}, "/action", "required"),
        ({"action": 3}, "/action", "type"),
        ({"action": "explode"}, "/action", "enum"),
        ({"action": "render", "target": _RENDER, "swap": "inner"}, "/html", "required"),
        ({**_ACTION, "extra": 1}, "/extra", "unknown_field"),
        ({**_ACTION, "target": 5}, "/target", "type"),
        ({**_ACTION, "target": ""}, "/target", "range"),
        ({**_ACTION, "target": "render:bad id"}, "/target", "pattern"),
        ({**_ACTION, "target": "nowhere"}, "/target", "pattern"),
        ({**_ACTION, "target": "mark:r1"}, "/target", "pattern"),
        ({**_ACTION, "target": "mark:r1:9bad"}, "/target", "pattern"),
        ({**_ACTION, "swap": 3}, "/swap", "type"),
        ({**_ACTION, "swap": "twirl"}, "/swap", "enum"),
        ({**_ACTION, "renderer": 3}, "/renderer", "type"),
        ({**_ACTION, "renderer": "other/1"}, "/renderer", "enum"),
        ({**_ACTION, "prepared": {}}, "/prepared", "semantic"),
        ({**_ACTION, "html": 3}, "/html", "type"),
        (
            {"action": "render", "target": _RENDER, "swap": "morph", "renderer": "vue-prepared/1"},
            "/prepared",
            "required",
        ),
        (
            {"action": "render", "target": _RENDER, "swap": "morph", "renderer": "vue-prepared/1", "prepared": []},
            "/prepared",
            "type",
        ),
        (
            {"action": "render", "target": _RENDER, "swap": "inner", "renderer": "vue-prepared/1", "prepared": {}},
            "/swap",
            "enum",
        ),
        (
            {
                "action": "render",
                "target": _RENDER,
                "swap": "morph",
                "renderer": "vue-prepared/1",
                "prepared": {},
                "html": "x",
            },
            "/html",
            "semantic",
        ),
        ({"action": "state", "targetRenderId": 1, "stateToken": "t", "publicState": {}}, "/targetRenderId", "type"),
        (
            {"action": "state", "targetRenderId": "bad id", "stateToken": "t", "publicState": {}},
            "/targetRenderId",
            "pattern",
        ),
        ({"action": "state", "targetRenderId": "r1", "stateToken": 1, "publicState": {}}, "/stateToken", "type"),
        ({"action": "state", "targetRenderId": "r1", "stateToken": "", "publicState": {}}, "/stateToken", "range"),
        ({"action": "state", "targetRenderId": "r1", "stateToken": "t", "publicState": []}, "/publicState", "type"),
        ({"action": "event", "eventName": 1}, "/eventName", "type"),
        ({"action": "event", "eventName": ""}, "/eventName", "range"),
        ({"action": "event", "eventName": "citry:internal"}, "/eventName", "pattern"),
        ({"action": "event", "eventName": "saved", "target": "mark:r1:name"}, "/target", "pattern"),
        ({"action": "redirect", "url": 1}, "/url", "type"),
        ({"action": "redirect", "url": ""}, "/url", "range"),
        ({"action": "url", "url": 1, "mode": "push"}, "/url", "type"),
        ({"action": "url", "url": "", "mode": "push"}, "/url", "range"),
        ({"action": "url", "url": "/a", "mode": 1}, "/mode", "type"),
        ({"action": "url", "url": "/a", "mode": "jump"}, "/mode", "enum"),
        ({**_ACTION, "delay": "1"}, "/delay", "type"),
        ({**_ACTION, "delay": True}, "/delay", "type"),
        ({**_ACTION, "delay": 10**400}, "/delay", "strict_json"),
        ({**_ACTION, "delay": -1}, "/delay", "range"),
        # Flags are written only at their non-default value, so the default is rejected.
        ({**_ACTION, "wait": True}, "/wait", "enum"),
    ],
    ids=[
        "not-a-mapping",
        "no-action",
        "action-not-a-string",
        "unknown-action",
        "render-without-html",
        "unknown-field",
        "target-not-a-string",
        "empty-target",
        "target-bad-render-id",
        "target-no-kind",
        "mark-without-name",
        "mark-bad-name",
        "swap-not-a-string",
        "unknown-swap",
        "renderer-not-a-string",
        "unknown-renderer",
        "prepared-without-renderer",
        "html-not-a-string",
        "morph-without-prepared",
        "prepared-not-a-mapping",
        "prepared-with-inner-swap",
        "prepared-with-html",
        "state-render-id-not-a-string",
        "state-render-id-bad-characters",
        "state-token-not-a-string",
        "state-empty-token",
        "state-public-state-not-a-mapping",
        "event-name-not-a-string",
        "event-empty-name",
        "event-reserved-name",
        "event-marker-target",
        "redirect-url-not-a-string",
        "redirect-empty-url",
        "url-not-a-string",
        "url-empty",
        "url-mode-not-a-string",
        "url-unknown-mode",
        "delay-string",
        "delay-bool",
        "delay-too-large",
        "delay-negative",
        "wait-default",
    ],
)
def test_actions_report_the_first_problem(action, path, category):
    assert _first_issue(events.validate_action, action) == (path, category)


def test_actions_accept_marker_targets_and_the_vue_prepared_renderer():
    marker = {**_ACTION, "target": "mark:r1:save-button", "delay": 1.5, "wait": False}
    assert events.validate_action(marker) is None
    prepared = {"action": "render", "target": _RENDER, "swap": "morph", "renderer": "vue-prepared/1", "prepared": {}}
    assert events.validate_action(prepared) is None


def test_action_builders_write_the_wire_shape_and_validate_it():
    assert events.build_render_action(_RENDER, "inner", "x", delay=2, wait=False) == {
        "action": "render",
        "target": _RENDER,
        "swap": "inner",
        "html": "x",
        "delay": 2,
        "wait": False,
    }
    assert events.build_prepared_render_action(_RENDER, "morph", "vue-prepared/1", {"a": 1}) == {
        "action": "render",
        "target": _RENDER,
        "swap": "morph",
        "renderer": "vue-prepared/1",
        "prepared": {"a": 1},
    }
    assert events.build_data_action({"k": [1]}, delay=1) == {"action": "data", "value": {"k": [1]}, "delay": 1}
    assert events.build_state_action("r1", "tok", {"n": 1}) == {
        "action": "state",
        "targetRenderId": "r1",
        "stateToken": "tok",
        "publicState": {"n": 1},
    }
    assert events.build_event_action("saved") == {"action": "event", "eventName": "saved"}
    # A detail of None is sent only when the caller asks for it, so null can be a real detail.
    assert events.build_event_action("saved", detail=None, include_detail=True, target=_RENDER) == {
        "action": "event",
        "eventName": "saved",
        "detail": None,
        "target": _RENDER,
    }
    assert events.build_redirect_action("/next", wait=False) == {"action": "redirect", "url": "/next", "wait": False}
    assert events.build_url_action("/a", "replace") == {"action": "url", "url": "/a", "mode": "replace"}


@pytest.mark.parametrize(
    "build",
    [
        lambda: events.build_render_action("nowhere", "inner", "x"),
        lambda: events.build_prepared_render_action(_RENDER, "inner", "vue-prepared/1", {}),
        lambda: events.build_data_action(1, delay=-1),
        lambda: events.build_state_action("r1", "", {}),
        lambda: events.build_event_action("citry:x"),
        lambda: events.build_redirect_action(""),
        lambda: events.build_url_action("/a", "jump"),
    ],
    ids=["render", "prepared-render", "data", "state", "event", "redirect", "url"],
)
def test_action_builders_refuse_an_invalid_action(build):
    with pytest.raises(events.ProtocolValueError):
        build()


@pytest.mark.parametrize(
    ("error", "path", "category"),
    [
        ([], "", "type"),
        ({"code": "not_found", "message": "m"}, "/status", "required"),
        ({**_ERROR, "extra": 1}, "/extra", "unknown_field"),
        ({**_ERROR, "status": "404"}, "/status", "type"),
        ({**_ERROR, "status": 404.5}, "/status", "type"),
        ({**_ERROR, "status": 200}, "/status", "range"),
        ({**_ERROR, "code": 1}, "/code", "type"),
        ({**_ERROR, "code": "mystery"}, "/code", "enum"),
        ({**_ERROR, "message": 1}, "/message", "type"),
        ({**_ERROR, "message": ""}, "/message", "range"),
        ({**_ERROR, "fieldErrors": []}, "/fieldErrors", "type"),
        ({**_ERROR, "fieldErrors": {"a": 1}}, "/fieldErrors/a", "type"),
        ({**_ERROR, "status": 500}, "/status", "semantic"),
    ],
    ids=[
        "not-a-mapping",
        "no-status",
        "unknown-field",
        "status-string",
        "status-fraction",
        "status-not-an-error",
        "code-not-a-string",
        "unknown-code",
        "message-not-a-string",
        "empty-message",
        "field-errors-not-a-mapping",
        "field-error-not-a-string",
        "status-code-mismatch",
    ],
)
def test_errors_report_the_first_problem(error, path, category):
    assert _first_issue(events.validate_error, error) == (path, category)


def test_error_builders_keep_field_errors_only_when_given():
    assert events.build_error(422, "invalid_args", "bad") == {"status": 422, "code": "invalid_args", "message": "bad"}
    built = events.build_error(422, "invalid_args", "bad", {"name": "required"})
    assert built["fieldErrors"] == {"name": "required"}
    # A generic `error` code has no fixed status, so any error status is allowed.
    assert events.build_error(503, "error", "down")["status"] == 503
    with pytest.raises(events.ProtocolValueError):
        events.build_error(500, "not_found", "x")
    assert events.build_error_result(_ERROR, 3) == {"ok": False, "sendSequence": 3, "error": _ERROR}
    assert events.build_error_result(_ERROR) == {"ok": False, "error": _ERROR}


@pytest.mark.parametrize(
    ("result", "path", "category"),
    [
        ([], "", "type"),
        ({}, "/ok", "required"),
        ({"ok": 1}, "/ok", "type"),
        ({"ok": True}, "/actions", "required"),
        ({"ok": False}, "/error", "required"),
        ({**_OK, "error": _ERROR}, "/error", "unknown_field"),
        ({**_OK, "sendSequence": "1"}, "/sendSequence", "type"),
        ({**_OK, "sendSequence": 10**400}, "/sendSequence", "strict_json"),
        ({**_OK, "sendSequence": 1.5}, "/sendSequence", "type"),
        ({**_OK, "sendSequence": -1}, "/sendSequence", "range"),
        ({"ok": False, "error": {**_ERROR, "code": "mystery"}}, "/error/code", "enum"),
        ({"ok": True, "actions": {}}, "/actions", "type"),
        ({"ok": True, "actions": [_ACTION, {"action": "redirect"}]}, "/actions/1/url", "required"),
        ({"ok": True, "actions": [{"action": "data", "value": 1}] * 2}, "/actions", "semantic"),
    ],
    ids=[
        "not-a-mapping",
        "no-ok",
        "ok-not-a-bool",
        "ok-without-actions",
        "failed-without-error",
        "ok-with-error",
        "send-sequence-string",
        "send-sequence-too-large",
        "send-sequence-fraction",
        "send-sequence-negative",
        "bad-error-code",
        "actions-not-a-list",
        "bad-second-action",
        "duplicate-data-actions",
    ],
)
def test_results_report_the_first_problem(result, path, category):
    assert _first_issue(events.validate_result, result) == (path, category)


def test_ok_result_builders_copy_actions_and_check_the_send_sequence():
    action = dict(_ACTION)
    built = events.build_ok_result([action], 2)
    assert built == {"ok": True, "sendSequence": 2, "actions": [_ACTION]}
    action["html"] = "changed"
    assert built["actions"][0]["html"] == "<b>x</b>"
    with pytest.raises(events.ProtocolValueError):
        events.build_ok_result([{"action": "nope"}])
    with pytest.raises(events.ProtocolValueError):
        events.build_ok_result([], -1)


def test_assemble_helpers_check_the_send_sequence_and_wrap_the_actions():
    assert events.assemble_validated_ok_result([_ACTION]) == {"ok": True, "actions": [_ACTION]}
    assert events.assemble_owned_ok_result([_ACTION], 0) == {"ok": True, "sendSequence": 0, "actions": [_ACTION]}
    for assemble in (events.assemble_validated_ok_result, events.assemble_owned_ok_result):
        with pytest.raises(events.ProtocolValueError) as error:
            assemble([], -5)
        assert error.value.issue.path == "/sendSequence"
    sent = events.assemble_validated_ok_result([_ACTION], 4)
    assert sent["sendSequence"] == 4


_EDGE = {"protocol": "citry-events/1", "requestId": None, "results": [{"ok": False, "error": _ERROR}]}
_ENVELOPE = {"protocol": "citry-events/1", "requestId": "q1", "results": [_OK]}


def _edge(error=None, **result_changes):
    result = {"ok": False, "error": error or {"status": 400, "code": "protocol_mismatch", "message": "m"}}
    result.update(result_changes)
    return {**_EDGE, "results": [result]}


@pytest.mark.parametrize(
    ("envelope", "path", "category"),
    [
        ([], "", "type"),
        ({"protocol": "citry-events/1", "requestId": "q"}, "/results", "required"),
        ({**_ENVELOPE, "extra": 1}, "/extra", "unknown_field"),
        ({**_ENVELOPE, "protocol": 1}, "/protocol", "type"),
        ({**_ENVELOPE, "protocol": "citry-events/9"}, "/protocol", "enum"),
        ({**_ENVELOPE, "requestId": 1}, "/requestId", "type"),
        ({**_ENVELOPE, "requestId": ""}, "/requestId", "range"),
        ({**_ENVELOPE, "results": {}}, "/results", "type"),
        ({**_ENVELOPE, "results": []}, "/results", "range"),
        ({**_ENVELOPE, "results": [{"ok": False}]}, "/results/0/error", "required"),
        (
            {**_EDGE, "results": [{"ok": False, "error": _ERROR}, {"ok": False, "error": _ERROR}]},
            "/results",
            "correlation",
        ),
        (_edge(sendSequence=1), "/results", "correlation"),
        ({**_EDGE, "results": [_OK]}, "/results", "correlation"),
        (_edge({"status": 404, "code": "not_found", "message": "m"}), "/results", "correlation"),
        (
            _edge({"status": 400, "code": "protocol_mismatch", "message": "m", "fieldErrors": {"a": "b"}}),
            "/results",
            "correlation",
        ),
    ],
    ids=[
        "not-a-mapping",
        "no-results",
        "unknown-field",
        "protocol-not-a-string",
        "unknown-protocol",
        "request-id-not-a-string",
        "empty-request-id",
        "results-not-a-list",
        "empty-results",
        "result-without-error",
        "two-edge-errors",
        "edge-error-with-send-sequence",
        "null-request-id-with-ok-result",
        "null-request-id-with-not-found",
        "null-request-id-with-field-errors",
    ],
)
def test_result_envelopes_report_the_first_problem(envelope, path, category):
    issue = events.validate_result_envelope(envelope)
    assert issue is not None
    assert (issue.path, issue.category) == (path, category)


@pytest.mark.parametrize("code", ["protocol_mismatch", "payload_too_large"])
def test_result_envelope_accepts_the_edge_error_with_a_null_request_id(code):
    # A null request ID is allowed only for one protocol_mismatch or payload_too_large error that has no sendSequence.
    error = {"status": 413 if code == "payload_too_large" else 400, "code": code, "message": "m"}
    assert events.validate_result_envelope(_edge(error)) is None


def test_envelope_builders_wrap_results_and_build_the_edge_error():
    built = events.build_result_envelope("q1", [_OK])
    assert built == _ENVELOPE
    assert events.finalize_owned_result_envelope("q1", [dict(_OK)]) == _ENVELOPE
    with pytest.raises(events.ProtocolValueError):
        events.finalize_owned_result_envelope("", [dict(_OK)])
    edge = events.build_edge_error_envelope(413, "payload_too_large", "too big")
    assert edge["requestId"] is None
    assert edge["results"][0]["error"]["code"] == "payload_too_large"
    with pytest.raises(events.ProtocolValueError):
        events.build_edge_error_envelope(400, "not_found", "x")


def test_rejected_call_envelope_answers_every_call_slot_when_the_request_id_is_usable():
    raw = {"requestId": "q9", "calls": [{"sendSequence": 0}, {"sendSequence": 1}, "junk"]}
    built = events.build_rejected_call_envelope(raw, status=400, code="protocol_mismatch", message="no")
    assert built["requestId"] == "q9"
    assert [result.get("sendSequence") for result in built["results"]] == [0, 1, None]
    assert all(result["ok"] is False for result in built["results"])
    assert events.validate_result_envelope(built) is None
    # With no calls to correlate, one result still answers the request.
    single = events.build_rejected_call_envelope(
        {"requestId": "q9", "calls": []}, status=400, code="protocol_mismatch", message="no"
    )
    assert len(single["results"]) == 1
    assert events.validate_result_envelope(single) is None


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param({"calls": []}, id="no-request-id"),
        pytest.param({"requestId": ""}, id="empty-request-id"),
        pytest.param({"requestId": 5}, id="request-id-not-a-string"),
        pytest.param("text", id="text"),
        pytest.param(None, id="none"),
    ],
)
def test_rejected_call_envelope_without_a_usable_request_id_is_an_edge_error(raw):
    built = events.build_rejected_call_envelope(raw, status=413, code="payload_too_large", message="big")
    assert built["requestId"] is None
    assert len(built["results"]) == 1
    assert events.validate_result_envelope(built) is None


def test_rejected_call_envelope_for_a_non_mapping_is_one_edge_error():
    built = events.build_rejected_call_envelope([1], status=400, code="protocol_mismatch", message="no")
    assert built["requestId"] is None


def _call_envelope(**changes):
    envelope = {"protocol": "citry-events/1", "requestId": "q1", "calls": [{"sendSequence": 7}]}
    envelope.update(changes)
    return envelope


def test_exchange_accepts_a_matching_result():
    result = {"protocol": "citry-events/1", "requestId": "q1", "results": [{**_OK, "sendSequence": 7}]}
    assert events.validate_exchange(_call_envelope(), result) is None


def _exchange_issue(call_envelope, result_envelope):
    issue = events.validate_exchange(call_envelope, result_envelope)
    assert issue is not None
    return issue.path, issue.category


def test_exchange_rejects_a_mismatched_correlation():
    ok = {**_OK, "sendSequence": 7}
    result = {"protocol": "citry-events/1", "requestId": "q1", "results": [ok]}
    assert _exchange_issue(_call_envelope(), {**result, "requestId": "q2"}) == ("/requestId", "correlation")
    assert _exchange_issue(_call_envelope(calls=[{}, {}]), result) == ("/results", "correlation")
    # The result must echo the call's sendSequence, and must not add one.
    assert _exchange_issue(_call_envelope(), {**result, "results": [_OK]}) == (
        "/results/0/sendSequence",
        "correlation",
    )
    assert _exchange_issue(_call_envelope(calls=[{}]), result) == ("/results/0/sendSequence", "correlation")
    # A result that is not itself a valid envelope is reported before correlation.
    assert _exchange_issue(_call_envelope(), {"protocol": "citry-events/1"}) == ("/requestId", "required")


def test_exchange_rejects_actions_the_caller_did_not_advertise():
    def result_with(action):
        return {
            "protocol": "citry-events/1",
            "requestId": "q1",
            "results": [{"ok": True, "sendSequence": 7, "actions": [action]}],
        }

    narrow = _call_envelope(capabilities={"swaps": ["inner"], "actions": ["render"], "renderers": ["html-fragment/1"]})
    assert events.validate_exchange(narrow, result_with(_ACTION)) is None
    redirect = {"action": "redirect", "url": "/x"}
    assert _exchange_issue(narrow, result_with(redirect)) == ("/results/0/actions/0/action", "capability")
    assert _exchange_issue(narrow, result_with({**_ACTION, "swap": "append"})) == (
        "/results/0/actions/0/swap",
        "capability",
    )
    prepared = {"action": "render", "target": _RENDER, "swap": "morph", "renderer": "vue-prepared/1", "prepared": {}}
    wide = _call_envelope(capabilities={"swaps": ["morph"], "actions": ["render"], "renderers": ["html-fragment/1"]})
    assert _exchange_issue(wide, result_with(prepared)) == ("/results/0/actions/0/renderer", "capability")
    # Without advertised capabilities the baseline applies, and it excludes morph.
    assert _exchange_issue(_call_envelope(), result_with({**_ACTION, "swap": "morph"})) == (
        "/results/0/actions/0/swap",
        "capability",
    )


def test_exchange_skips_capability_checks_for_failed_results():
    failed = {
        "protocol": "citry-events/1",
        "requestId": "q1",
        "results": [{"ok": False, "sendSequence": 7, "error": _ERROR}],
    }
    assert events.validate_exchange(_call_envelope(capabilities={}), failed) is None
