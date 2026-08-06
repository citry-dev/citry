"""The executable citry-events/1 Python package and its embedded copy."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import UserDict
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry
from citry._protocol import events
from citry.ext.events import routes as event_routes
from citry.ext.events.dispatcher import EventsDispatcher, TransportContext

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from packages.protocol._tooling import apply_operations, load_cases, load_json_value  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

PROTOCOL_ROOT = ROOT / "packages" / "protocol" / "events" / "v1"
CASES = tuple(
    case for case in load_cases(PROTOCOL_ROOT / "tests" / "conformance-cases.json") if "python" in case.implementations
)
VALIDATORS: dict[str, Callable[[Any], events.ValidationIssue | None]] = {
    "call.schema.json": events.validate_call_envelope,
    "descriptor.schema.json": events.validate_descriptor,
    "manifest.schema.json": events.validate_manifest,
    "result.schema.json": events.validate_result_envelope,
}


def _mutated(case: Any) -> Any:
    seed = load_json_value(PROTOCOL_ROOT / "tests" / case.seed)
    return apply_operations(seed, case.operations)


@pytest.mark.parametrize("case", CASES, ids=[case.case_id for case in CASES])
def test_embedded_runtime_matches_each_shared_issue(case: Any) -> None:
    issue = VALIDATORS[case.schema](_mutated(case))
    assert issue is not None
    assert issue.path == case.expected.path
    assert issue.category == case.expected.category


@pytest.mark.parametrize(
    "case",
    [case for case in CASES if case.schema == "call.schema.json"],
    ids=lambda case: case.case_id,
)
def test_dispatcher_rejects_each_call_mutation_with_the_protocol_message(case: Any) -> None:
    envelope = _mutated(case)
    issue = events.validate_call_envelope(envelope)
    assert issue is not None
    outcome = EventsDispatcher().dispatch(envelope, TransportContext(transport="test", citry=Citry()))
    assert isinstance(outcome, dict)
    assert all(result["error"]["message"] == issue.message for result in outcome["results"])


def test_rejection_without_request_id_is_one_transport_edge_error() -> None:
    envelope = {
        "protocol": "citry-events/1",
        "requestId": None,
        "calls": [
            {"componentClassId": "X", "handlerName": "a", "args": {}, "sendSequence": 1},
            {"componentClassId": "X", "handlerName": "b", "args": {}, "sendSequence": 2},
        ],
    }
    outcome = EventsDispatcher().dispatch(envelope, TransportContext(transport="test", citry=Citry()))
    assert outcome == {
        "protocol": "citry-events/1",
        "requestId": None,
        "results": [
            {
                "ok": False,
                "error": {
                    "status": 400,
                    "code": "protocol_mismatch",
                    "message": "The envelope carries no 'requestId' string.",
                },
            }
        ],
    }
    assert events.validate_result_envelope(outcome) is None


def test_final_http_boundary_rejects_non_json_mapping_containers() -> None:
    envelope = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "results": [
            {
                "ok": False,
                "error": UserDict({"status": 500, "code": "handler_error", "message": "Broken."}),
            }
        ],
    }
    issue = events.validate_result_envelope(envelope)
    assert issue is not None
    assert issue.path == "/results/0/error"
    assert issue.category == "strict_json"
    with pytest.raises(events.ProtocolValueError) as raised:
        event_routes._encode_envelope(envelope)
    assert raised.value.issue == issue


def test_builders_normalize_declared_mapping_inputs() -> None:
    source = UserDict({"status": 500, "code": "handler_error", "message": "Reported."})
    result = events.build_error_result(source)
    source["message"] = "Mutated."
    assert result == {
        "ok": False,
        "error": {"status": 500, "code": "handler_error", "message": "Reported."},
    }
    assert type(result["error"]) is dict


def test_strict_json_parser_rejects_an_integer_a_browser_reads_as_infinity() -> None:
    with pytest.raises(ValueError, match="out of browser range"):
        events.loads_strict_json('{"value":' + "9" * 400 + "}")


def test_strict_json_validation_falls_back_for_values_deeper_than_python_recursion() -> None:
    value: list[Any] = []
    cursor = value
    for _ in range(1500):
        child: list[Any] = []
        cursor.append(child)
        cursor = child
    assert events.validate_strict_json(value) is None

    cursor.append(value)
    issue = events.validate_strict_json(value)
    assert issue is not None
    assert issue.category == "strict_json"
    assert issue.message == "The value contains a cycle."


@pytest.mark.parametrize(
    ("validator", "value", "expected_path"),
    [
        (
            events.validate_call,
            (call := {"componentClassId": "C", "handlerName": "save", "args": {}}),
            "/args/self",
        ),
        (events.validate_capabilities, (capabilities := {}), "/capabilities/actions"),
        (
            events.validate_call_envelope,
            (call_envelope := {"protocol": "citry-events/1", "requestId": "r1", "calls": []}),
            "/calls/0",
        ),
        (events.validate_handler_descriptor, (handler := {"httpMethod": "POST"}), "/self"),
        (
            events.validate_descriptor,
            (descriptor := {"componentClassId": "C", "eventHandlers": {}}),
            "/eventHandlers/loop",
        ),
        (
            events.validate_component_instance,
            (
                instance := {
                    "renderId": "c1",
                    "componentClassId": "C",
                    "stateToken": None,
                    "publicState": {},
                }
            ),
            "/publicState/self",
        ),
        (
            events.validate_manifest,
            (
                manifest := {
                    "protocol": "citry-events/1",
                    "clientGraphRevision": None,
                    "componentClasses": [],
                    "componentInstances": [],
                }
            ),
            "/componentClasses/0",
        ),
        (events.validate_action, (action := {"action": "data", "value": None}), "/value/self"),
        (
            events.validate_error,
            (error := {"status": 500, "code": "handler_error", "message": "broken"}),
            "/fieldErrors/self",
        ),
        (events.validate_result, (result := {"ok": True, "actions": []}), "/actions/0"),
        (
            events.validate_result_envelope,
            (result_envelope := {"protocol": "citry-events/1", "requestId": "r1", "results": []}),
            "/results/0",
        ),
    ],
)
def test_every_public_validator_checks_strict_json_before_record_shape(validator, value, expected_path) -> None:
    if validator is events.validate_call:
        value["args"] = {"self": value}
    elif validator is events.validate_capabilities:
        value["actions"] = value
    elif validator is events.validate_call_envelope:
        value["calls"].append(value)
    elif validator is events.validate_handler_descriptor:
        value["self"] = value
    elif validator is events.validate_descriptor:
        value["eventHandlers"]["loop"] = value
    elif validator is events.validate_component_instance:
        value["publicState"] = {"self": value}
    elif validator is events.validate_manifest:
        value["componentClasses"].append(value)
    elif validator is events.validate_action:
        value["value"] = {"self": value}
    elif validator is events.validate_error:
        value["fieldErrors"] = {"self": value}
    elif validator is events.validate_result:
        value["actions"].append(value)
    else:
        value["results"].append(value)

    issue = validator(value)
    assert issue is not None
    assert issue.path == expected_path
    assert issue.category == "strict_json"


def test_mathematically_integral_json_numbers_match_browser_integer_semantics() -> None:
    call = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "calls": [{"componentClassId": "C", "handlerName": "save", "args": {}, "sendSequence": 1.0}],
    }
    descriptor = {"httpMethod": "POST", "debounceMilliseconds": 1.0, "throttleMilliseconds": 2.0}
    result = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "results": [{"ok": True, "sendSequence": 1.0, "actions": []}],
    }
    error_result = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "results": [
            {
                "ok": False,
                "error": {"status": 500.0, "code": "handler_error", "message": "broken"},
            }
        ],
    }

    assert events.validate_call_envelope(call) is None
    assert events.call_send_sequence(call["calls"][0]) == 1
    assert events.validate_handler_descriptor(descriptor) is None
    assert events.validate_result_envelope(result) is None
    assert events.validate_result_envelope(error_result) is None


@pytest.mark.parametrize(
    ("validator", "value", "expected_path"),
    [
        (
            events.validate_call_envelope,
            {
                "protocol": "citry-events/1",
                "requestId": "r1",
                "calls": [
                    {"componentClassId": "Counter_1", "handlerName": "save", "args": {}, "sendSequence": 10**400}
                ],
            },
            "/calls/0/sendSequence",
        ),
        (
            events.validate_handler_descriptor,
            {"httpMethod": "POST", "debounceMilliseconds": 10**400},
            "/debounceMilliseconds",
        ),
        (
            events.validate_result_envelope,
            {
                "protocol": "citry-events/1",
                "requestId": "r1",
                "results": [{"ok": True, "sendSequence": 10**400, "actions": []}],
            },
            "/results/0/sendSequence",
        ),
        (
            events.validate_result_envelope,
            {
                "protocol": "citry-events/1",
                "requestId": "r1",
                "results": [
                    {
                        "ok": True,
                        "actions": [
                            {
                                "action": "render",
                                "target": "#result",
                                "swap": "replace",
                                "html": "ok",
                                "delay": 10**400,
                            }
                        ],
                    }
                ],
            },
            "/results/0/actions/0/delay",
        ),
    ],
)
def test_numeric_wire_fields_reject_integers_outside_browser_range(validator, value, expected_path) -> None:
    issue = validator(value)
    assert issue is not None
    assert issue.path == expected_path
    assert issue.category == "strict_json"


def test_structural_action_issue_precedes_the_data_count_relationship() -> None:
    envelope = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "results": [
            {
                "ok": True,
                "actions": [
                    {"action": "data", "value": 1},
                    {"action": "data", "value": 2},
                    {"action": "render", "target": "#result", "swap": "replace", "html": 3},
                ],
            }
        ],
    }
    issue = events.validate_result_envelope(envelope)
    assert issue is not None
    assert issue.path == "/results/0/actions/2/html"
    assert issue.category == "type"


def test_structural_manifest_issue_precedes_duplicate_class_relationship() -> None:
    manifest = load_json_value(PROTOCOL_ROOT / "tests" / "manifests" / "complete.valid.json")
    manifest["componentClasses"].append(json.loads(json.dumps(manifest["componentClasses"][0])))
    manifest["componentInstances"][0]["publicState"] = []
    issue = events.validate_manifest(manifest)
    assert issue is not None
    assert issue.path == "/componentInstances/0/publicState"
    assert issue.category == "type"


def test_builders_copy_open_application_json() -> None:
    args = {"items": [{"name": "before"}]}
    call = events.build_call("Counter_1", "save", args)
    args["items"][0]["name"] = "after"
    assert call["args"] == {"items": [{"name": "before"}]}


def test_validated_hook_mapping_may_preserve_an_explicit_zero_data_delay() -> None:
    action = {"action": "data", "value": {"saved": True}, "delay": 0}
    assert events.validate_action(action) is None
    built = events.build_data_action({"saved": True}, delay=0)
    assert "delay" not in built


def test_canonical_and_embedded_packages_are_byte_identical() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/sync_protocol_python.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_manifest_builder_escapes_only_at_the_html_transport_boundary() -> None:
    descriptor = events.build_descriptor("Notice_1", {})
    instance = events.build_component_instance("notice_1", "Notice_1", "token", {"text": "</script>"})
    manifest = events.build_manifest(None, [descriptor], [instance])
    text = json.dumps(manifest, separators=(",", ":"), sort_keys=True, allow_nan=False).replace("<", "\\u003c")
    assert "</script>" not in text
    assert json.loads(text) == manifest
