"""Check which handler hints, descriptors, instances and manifests the Events validators reject."""

from __future__ import annotations

from typing import Any

import pytest

from citry._protocol import events

_INSTANCE = {"renderId": "r1", "componentClassId": "app.Card", "stateToken": "tok", "publicState": {"n": 1}}
_DESCRIPTOR = {"componentClassId": "app.Card", "eventHandlers": {"save": {"httpMethod": "POST"}}}


def _manifest(**changes):
    manifest = {"protocol": "citry-events/1", "componentClasses": [_DESCRIPTOR], "componentInstances": [_INSTANCE]}
    manifest.update(changes)
    return manifest


@pytest.mark.parametrize(
    ("hints", "path", "category"),
    [
        pytest.param([], "", "type", id="not-a-mapping"),
        pytest.param({}, "/httpMethod", "required", id="no-method"),
        pytest.param({"httpMethod": 5}, "/httpMethod", "type", id="method-not-a-string"),
        pytest.param({"httpMethod": "post"}, "/httpMethod", "pattern", id="lowercase-method"),
        # Flags are written only at their non-default value, so the default is rejected.
        pytest.param({"httpMethod": "POST", "usesState": False}, "/usesState", "enum", id="uses-state-default"),
        pytest.param(
            {"httpMethod": "POST", "debounceMilliseconds": "5"}, "/debounceMilliseconds", "type", id="debounce-string"
        ),
        pytest.param(
            {"httpMethod": "POST", "throttleMilliseconds": True}, "/throttleMilliseconds", "type", id="throttle-bool"
        ),
        pytest.param(
            {"httpMethod": "POST", "debounceMilliseconds": 1.5},
            "/debounceMilliseconds",
            "type",
            id="debounce-fraction",
        ),
        pytest.param(
            {"httpMethod": "POST", "latestCallWins": False}, "/latestCallWins", "enum", id="latest-call-wins-default"
        ),
        pytest.param(
            {"httpMethod": "POST", "allowBatching": True}, "/allowBatching", "enum", id="allow-batching-default"
        ),
    ],
)
def test_handler_hints_report_the_first_problem(hints, path, category):
    issue = events.validate_handler_descriptor(hints)
    assert issue is not None
    assert (issue.path, issue.category) == (path, category)


def test_build_handler_descriptor_writes_only_the_hints_that_differ_from_the_defaults():
    assert events.build_handler_descriptor("POST") == {"httpMethod": "POST"}
    # Each flag is written at its non-default value, the reverse of the default.
    assert events.build_handler_descriptor(
        "POST",
        uses_state=True,
        debounce_milliseconds=10,
        throttle_milliseconds=20,
        latest_call_wins=True,
        allow_batching=False,
        detached=True,
    ) == {
        "httpMethod": "POST",
        "usesState": True,
        "debounceMilliseconds": 10,
        "throttleMilliseconds": 20,
        "latestCallWins": True,
        "allowBatching": False,
        "detached": True,
    }


def test_build_handler_descriptor_rejects_a_bad_method_with_the_issue_attached():
    with pytest.raises(events.ProtocolValueError) as error:
        events.build_handler_descriptor("post")
    assert error.value.issue.path == "/httpMethod"
    assert error.value.issue.category == "pattern"


@pytest.mark.parametrize(
    ("descriptor", "path", "category"),
    [
        pytest.param([], "", "type", id="not-a-mapping"),
        pytest.param({"eventHandlers": {}}, "/componentClassId", "required", id="no-class-id"),
        pytest.param({"componentClassId": "a"}, "/eventHandlers", "required", id="no-handlers"),
        pytest.param({**_DESCRIPTOR, "extra": 1}, "/extra", "unknown_field", id="unknown-field"),
        pytest.param({**_DESCRIPTOR, "componentClassId": 3}, "/componentClassId", "type", id="class-id-not-a-string"),
        pytest.param({**_DESCRIPTOR, "componentClassId": ""}, "/componentClassId", "range", id="empty-class-id"),
        pytest.param({**_DESCRIPTOR, "eventHandlers": []}, "/eventHandlers", "type", id="handlers-not-a-mapping"),
        pytest.param(
            {**_DESCRIPTOR, "eventHandlers": {"save": {}}},
            "/eventHandlers/save/httpMethod",
            "required",
            id="handler-without-method",
        ),
        pytest.param(
            {**_DESCRIPTOR, "writableStateFields": "name"}, "/writableStateFields", "type", id="fields-not-a-list"
        ),
        pytest.param(
            {**_DESCRIPTOR, "writableStateFields": [1]}, "/writableStateFields/0", "type", id="field-not-a-string"
        ),
        pytest.param(
            {**_DESCRIPTOR, "writableStateFields": [""]}, "/writableStateFields/0", "range", id="empty-field-name"
        ),
        pytest.param(
            {**_DESCRIPTOR, "writableStateFields": ["a", "a"]},
            "/writableStateFields",
            "semantic",
            id="duplicate-field",
        ),
    ],
)
def test_descriptors_report_the_first_problem(descriptor, path, category):
    issue = events.validate_descriptor(descriptor)
    assert issue is not None
    assert (issue.path, issue.category) == (path, category)


def test_build_descriptor_copies_handler_hints_and_validates_the_result():
    hints = {"httpMethod": "POST"}
    built = events.build_descriptor("app.Card", {"save": hints}, writable_state_fields=["name"])
    assert built == {
        "componentClassId": "app.Card",
        "eventHandlers": {"save": {"httpMethod": "POST"}},
        "writableStateFields": ["name"],
    }
    # Changing the caller's hints later must not change the built descriptor.
    hints["httpMethod"] = "GET"
    assert built["eventHandlers"]["save"]["httpMethod"] == "POST"
    with pytest.raises(events.ProtocolValueError):
        events.build_descriptor("", {})


@pytest.mark.parametrize(
    ("instance", "path", "category"),
    [
        pytest.param([], "", "type", id="not-a-mapping"),
        pytest.param(
            {k: v for k, v in _INSTANCE.items() if k != "stateToken"}, "/stateToken", "required", id="no-state-token"
        ),
        pytest.param({**_INSTANCE, "extra": 1}, "/extra", "unknown_field", id="unknown-field"),
        pytest.param({**_INSTANCE, "renderId": 1}, "/renderId", "type", id="render-id-not-a-string"),
        pytest.param({**_INSTANCE, "renderId": "bad id!"}, "/renderId", "pattern", id="render-id-bad-characters"),
        pytest.param({**_INSTANCE, "componentClassId": 1}, "/componentClassId", "type", id="class-id-not-a-string"),
        pytest.param({**_INSTANCE, "componentClassId": ""}, "/componentClassId", "range", id="empty-class-id"),
        pytest.param({**_INSTANCE, "stateToken": 1}, "/stateToken", "type", id="token-not-a-string"),
        pytest.param({**_INSTANCE, "stateToken": ""}, "/stateToken", "range", id="empty-token"),
        pytest.param({**_INSTANCE, "publicState": []}, "/publicState", "type", id="state-not-a-mapping"),
    ],
)
def test_component_instances_report_the_first_problem(instance, path, category):
    issue = events.validate_component_instance(instance)
    assert issue is not None
    assert (issue.path, issue.category) == (path, category)


def test_build_component_instance_copies_public_state_and_validates():
    state = {"n": 1}
    built = events.build_component_instance("r1", "app.Card", "tok", state)
    state["n"] = 2
    assert built["publicState"] == {"n": 1}
    with pytest.raises(events.ProtocolValueError):
        events.build_component_instance("r1", "app.Card", "", {})


@pytest.mark.parametrize(
    ("manifest", "path", "category"),
    [
        pytest.param([], "", "type", id="not-a-mapping"),
        pytest.param({"protocol": "citry-events/1"}, "/componentClasses", "required", id="no-classes"),
        pytest.param(_manifest(extra=1), "/extra", "unknown_field", id="unknown-field"),
        pytest.param(_manifest(protocol=1), "/protocol", "type", id="protocol-not-a-string"),
        pytest.param(_manifest(protocol="citry-events/2"), "/protocol", "enum", id="unknown-protocol"),
        pytest.param(_manifest(componentClasses={}), "/componentClasses", "type", id="classes-not-a-list"),
        pytest.param(_manifest(componentClasses=[[]]), "/componentClasses/0", "type", id="class-not-a-mapping"),
        pytest.param(_manifest(componentInstances={}), "/componentInstances", "type", id="instances-not-a-list"),
        pytest.param(_manifest(componentInstances=[[]]), "/componentInstances/0", "type", id="instance-not-a-mapping"),
        pytest.param(
            _manifest(componentClasses=[_DESCRIPTOR, _DESCRIPTOR]),
            "/componentClasses/1",
            "semantic",
            id="duplicate-class",
        ),
        pytest.param(
            _manifest(componentInstances=[_INSTANCE, _INSTANCE]),
            "/componentInstances/1",
            "semantic",
            id="duplicate-instance",
        ),
        pytest.param(
            _manifest(componentInstances=[{**_INSTANCE, "componentClassId": "app.Other"}]),
            "/componentInstances/0/componentClassId",
            "semantic",
            id="instance-of-unlisted-class",
        ),
        # A null stateToken makes the instance stateless, so its public State must be empty.
        pytest.param(
            _manifest(componentInstances=[{**_INSTANCE, "stateToken": None}]),
            "/componentInstances/0/publicState",
            "semantic",
            id="stateless-instance-with-state",
        ),
    ],
)
def test_manifests_report_the_first_problem(manifest, path, category):
    issue = events.validate_manifest(manifest)
    assert issue is not None
    assert (issue.path, issue.category) == (path, category)


def test_build_manifest_accepts_a_consistent_manifest_and_rejects_an_inconsistent_one():
    built = events.build_manifest([_DESCRIPTOR], [_INSTANCE])
    assert built == _manifest()
    # Changing the caller's descriptor later must not change the built manifest.
    descriptor: dict[str, Any] = {"componentClassId": "app.Card", "eventHandlers": {"save": {"httpMethod": "POST"}}}
    copied = events.build_manifest([descriptor], [])
    descriptor["eventHandlers"]["save"]["httpMethod"] = "GET"
    assert copied["componentClasses"][0]["eventHandlers"]["save"]["httpMethod"] == "POST"
    with pytest.raises(events.ProtocolValueError) as error:
        events.build_manifest([], [_INSTANCE])
    assert error.value.issue.category == "semantic"
