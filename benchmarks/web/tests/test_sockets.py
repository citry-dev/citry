"""Reject incomplete, miscorrelated or compressed persistent-message evidence."""

import hashlib
from copy import deepcopy

from citry_bench.sockets import collect_sockets, message_bytes


def evidence():
    request = '{"operation":"op"}'
    response = '{"operation":"op","revision":1,"text":"héllo"}'
    url = "ws://127.0.0.1:9000/socket"
    events = [
        {"event": "webSocketCreated", "value": {"requestId": "socket", "url": url}},
        {
            "event": "webSocketHandshakeResponseReceived",
            "value": {
                "requestId": "socket",
                "response": {"status": 101, "headers": {}},
            },
        },
    ]
    records = []
    for direction, event, text, revision in (
        ("received", "webSocketFrameSent", request, None),
        ("sent", "webSocketFrameReceived", response, 1),
    ):
        events.append(
            {
                "event": event,
                "value": {
                    "requestId": "socket",
                    "response": {"opcode": 1, "payloadData": text},
                },
            }
        )
        records.append(
            {
                "connection": "server-socket",
                "direction": direction,
                "index": 1,
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "bytes": len(text.encode()),
                "operation": "op",
                "revision": revision,
            }
        )
    transport = {"index": 0, "url": url, "sent": 1, "received": 1, "closed": None}
    ready = {"start": 10, "end": 21, "operation": "op", "revision": 1, "session": "session", "transport": [transport]}
    snapshot = {"transport": [{**transport, "sent": [11], "received": [20]}], "marks": [ready]}
    audit = {"session": "session", "compression": "identity", "records": records}
    return events, ready, snapshot, audit


def test_counts_identity_message_bytes_and_preserves_unknown_wire_size():
    result = collect_sockets(*evidence())
    assert result["errors"] == []
    assert result["decoded_response_bytes"] == len('{"operation":"op","revision":1,"text":"héllo"}'.encode())
    assert result["wire_bytes"] is None
    assert message_bytes({"opcode": 2, "payloadData": "AAEC"}) == b"\x00\x01\x02"


def test_output_preparation_duration_follows_the_correlated_incoming_message():
    events, ready, snapshot, audit = evidence()
    audit["records"][-1]["prepare_ms"] = 1.5
    result = collect_sockets(events, ready, snapshot, audit)
    assert result["messages"][-1]["prepare_ms"] == 1.5
    assert result["server_timings"][-1]["prepare_ms"] == 1.5


def test_preparation_instrumentation_faults_are_separate_from_protocol_errors():
    events, ready, snapshot, audit = evidence()
    audit["preparation_errors"] = ["multiple serializer calls"]
    result = collect_sockets(events, ready, snapshot, audit)
    assert result["errors"] == []
    assert result["preparation_errors"] == ["multiple serializer calls"]


def test_malformed_preparation_audit_is_an_instrumentation_fault():
    events, ready, snapshot, audit = evidence()
    audit["preparation_errors"] = "not a list"
    result = collect_sockets(events, ready, snapshot, audit)
    assert result["errors"] == []
    assert result["preparation_errors"] == ["server preparation audit is malformed"]


def test_late_second_message_cannot_hide_behind_first_acknowledgement():
    events, ready, snapshot, audit = evidence()
    events.append(deepcopy(events[-1]))
    snapshot["transport"][0]["received"].append(22)
    audit["records"].append({**audit["records"][-1], "index": 2})
    result = collect_sockets(events, ready, snapshot, audit)
    assert "after the ready boundary" in str(result["errors"])
    assert result["decoded_response_bytes"] is None


def test_mismatched_server_bytes_fail():
    events, ready, snapshot, audit = evidence()
    audit["records"][0]["bytes"] += 1
    assert "differs" in str(collect_sockets(events, ready, snapshot, audit)["errors"])


def test_compression_negotiation_is_rejected():
    events, ready, snapshot, audit = evidence()
    events[1]["value"]["response"]["headers"]["Sec-WebSocket-Extensions"] = "permessage-deflate"
    assert "no compression" in str(collect_sockets(events, ready, snapshot, audit)["errors"])


def test_disconnect_after_ready_is_retained_as_observed_failure():
    events, ready, snapshot, audit = evidence()
    snapshot["transport"][0]["closed"] = {"at": 22, "code": 1006}
    assert "interruption observed" in str(collect_sockets(events, ready, snapshot, audit)["errors"])


def test_message_in_interaction_gap_is_rejected():
    events, ready, snapshot, audit = evidence()
    snapshot["transport"][0]["sent"][0] = 9
    result = collect_sockets(events, ready, snapshot, audit)
    assert "outside its correlated operation" in str(result["errors"])


def add_control_message(events, snapshot, audit, *, direction, text, at):
    browser_direction, server_direction, event_name = {
        "sent": ("sent", "received", "webSocketFrameSent"),
        "received": ("received", "sent", "webSocketFrameReceived"),
    }[direction]
    events.append(
        {
            "event": event_name,
            "value": {
                "requestId": "socket",
                "response": {"opcode": 1, "payloadData": text},
            },
        }
    )
    snapshot["transport"][0][browser_direction].append(at)
    audit["records"].append(
        {
            "connection": "server-socket",
            "direction": server_direction,
            "index": len(snapshot["transport"][0][browser_direction]),
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "bytes": len(text.encode()),
            "message_type": "socket.io-control",
            "operation": None,
            "revision": None,
        }
    )


def test_engine_io_heartbeat_is_accounted_without_becoming_an_application_message():
    events, ready, snapshot, audit = evidence()
    add_control_message(events, snapshot, audit, direction="sent", text="3", at=12)
    add_control_message(events, snapshot, audit, direction="received", text="2", at=19)
    ready["transport"][0].update(sent=2, received=2)

    result = collect_sockets(events, ready, snapshot, audit)

    assert result["errors"] == []
    assert result["control_request_bytes"] == 1
    assert result["control_response_bytes"] == 1
    assert len(result["control_messages"]) == 2
    assert result["request_body_bytes"] == len(b'{"operation":"op"}')


def test_engine_io_heartbeat_after_ready_is_retained_without_invalidating_readiness():
    events, ready, snapshot, audit = evidence()
    add_control_message(events, snapshot, audit, direction="received", text="2", at=22)

    result = collect_sockets(events, ready, snapshot, audit)

    assert result["errors"] == []
    assert result["control_response_bytes"] == 0
    assert result["control_messages"][-1]["in_observation_window"] is False


def test_unowned_or_misclassified_socket_frames_remain_errors():
    events, ready, snapshot, audit = evidence()
    add_control_message(events, snapshot, audit, direction="received", text="unknown", at=22)
    result = collect_sockets(events, ready, snapshot, audit)
    assert "application messages arrived after" in str(result["errors"])

    events, ready, snapshot, audit = evidence()
    add_control_message(events, snapshot, audit, direction="received", text="2", at=22)
    events[-1]["value"]["response"] = {"opcode": 2, "payloadData": "Mg=="}
    result = collect_sockets(events, ready, snapshot, audit)
    assert "application messages arrived after" in str(result["errors"])

    events, ready, snapshot, audit = evidence()
    add_control_message(events, snapshot, audit, direction="received", text="2", at=22)
    audit["records"][-1]["message_type"] = "state"
    result = collect_sockets(events, ready, snapshot, audit)
    assert "application messages arrived after" in str(result["errors"])


def add_late_heartbeat(events, audit, *, text, server_direction, cdp=True):
    # The page's message log was copied before this heartbeat arrived, so only
    # the later evidence (the CDP frames, the server audit) can contain it.
    if cdp:
        event_name = "webSocketFrameReceived" if server_direction == "sent" else "webSocketFrameSent"
        events.append(
            {"event": event_name, "value": {"requestId": "socket", "response": {"opcode": 1, "payloadData": text}}}
        )
    audit["records"].append(
        {
            "connection": "server-socket",
            "direction": server_direction,
            "index": 2,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "bytes": len(text.encode()),
            "message_type": "socket.io-control",
            "operation": None,
            "revision": None,
        }
    )


def test_heartbeat_arriving_while_evidence_is_collected_is_set_aside():
    # Reflex pings every 25 seconds. A ping and its pong that land after the
    # page's log was copied must not fail an otherwise complete action.
    events, ready, snapshot, audit = evidence()
    add_late_heartbeat(events, audit, text="2", server_direction="sent")
    add_late_heartbeat(events, audit, text="3", server_direction="received", cdp=False)

    result = collect_sockets(events, ready, snapshot, audit)

    assert result["errors"] == []
    assert result["late_control_messages"] == 2
    assert result["decoded_response_bytes"] == len('{"operation":"op","revision":1,"text":"héllo"}'.encode())


def test_late_application_message_outside_the_page_log_still_fails():
    events, ready, snapshot, audit = evidence()
    add_late_heartbeat(events, audit, text="2", server_direction="sent")
    audit["records"][-1]["message_type"] = "state"

    result = collect_sockets(events, ready, snapshot, audit)

    assert "Browser/CDP/server received message counts differ (1/2/2)" in result["errors"]
    assert result["decoded_response_bytes"] is None
