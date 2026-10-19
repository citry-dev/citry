"""Account for uncompressed WebSocket messages using browser and server evidence."""

import base64
import hashlib
from collections import defaultdict


def message_bytes(frame: dict) -> bytes:
    if frame["opcode"] == 1:
        return frame["payloadData"].encode("utf-8")
    if frame["opcode"] == 2:
        return base64.b64decode(frame["payloadData"], validate=True)
    raise ValueError(f"Unsupported WebSocket opcode: {frame['opcode']}")


def is_control_frame(frame: dict) -> bool:
    """Return whether a CDP frame is an Engine.IO heartbeat ("2" ping or "3" pong)."""
    return frame.get("opcode") == 1 and frame.get("payloadData") in ("2", "3")


def is_control_record(record: dict) -> bool:
    """Return whether a server audit record is an Engine.IO heartbeat."""
    return (
        record.get("message_type") == "socket.io-control"
        and record.get("operation") is None
        and record.get("revision") is None
    )


def collect_sockets(events: list[dict], ready: dict, snapshot: dict, audit: dict) -> dict:
    """Require matching message order, hashes, operation IDs and ready boundaries.

    The current profile permits one socket and no negotiated extensions. Browser
    observer times share the ready mark's clock. CDP timestamps are retained as
    evidence but never subtracted from those browser times.
    """
    errors = []
    created = [entry["value"] for entry in events if entry["event"] == "webSocketCreated"]
    if len(created) != 1 or len(ready.get("transport", [])) != 1 or len(snapshot.get("transport", [])) != 1:
        raise ValueError("The qualified socket profile requires exactly one browser connection")
    connection = created[0]["requestId"]
    browser = snapshot["transport"][0]
    boundary = ready["transport"][0]
    if browser["url"] != created[0]["url"] or boundary["url"] != browser["url"]:
        errors.append("Browser and CDP socket URLs differ")
    if boundary["closed"]:
        errors.append("Socket closed before readiness")
    if browser["closed"] or any(entry["event"] in ("webSocketClosed", "webSocketFrameError") for entry in events):
        errors.append("Socket interruption observed before evidence collection completed")
    handshakes = [
        entry["value"]
        for entry in events
        if entry["event"] == "webSocketHandshakeResponseReceived" and entry["value"]["requestId"] == connection
    ]
    if len(handshakes) != 1:
        errors.append("Missing or ambiguous WebSocket handshake")
    else:
        response = handshakes[0]["response"]
        headers = {key.lower(): value for key, value in response["headers"].items()}
        if response["status"] != 101 or headers.get("sec-websocket-extensions"):
            errors.append("Socket requires an accepted handshake with no compression/extensions")
    if audit.get("session") != ready["session"] or audit.get("compression") != "identity":
        errors.append("Audit session or compression differs from the selected profile")
    ledger = defaultdict(list)
    for entry in audit.get("records", []):
        ledger[entry["direction"]].append(entry)
    if len({entry["connection"] for entry in audit.get("records", [])}) != 1:
        errors.append("Audit must describe exactly one server connection")
    selected = []
    control_messages = []
    late_control_messages = 0
    for browser_direction, server_direction, event_name in (
        ("sent", "received", "webSocketFrameSent"),
        ("received", "sent", "webSocketFrameReceived"),
    ):
        frames = [
            entry["value"]["response"]
            for entry in events
            if entry["event"] == event_name and entry["value"]["requestId"] == connection
        ]
        times = browser[browser_direction]
        server = ledger[server_direction]
        count = boundary[browser_direction]
        # The page's message log is copied first, then the server audit is
        # fetched and the CDP frames are read. The server keeps sending its
        # timed heartbeat meanwhile (Reflex every 25 seconds), so a ping and
        # its pong can reach the later two records only. Set those aside when
        # every extra entry is a heartbeat; any other extra message still fails.
        captured = len(times)
        late_frames, late_server = frames[captured:], server[captured:]
        if (late_frames or late_server) and (
            all(is_control_frame(frame) for frame in late_frames)
            and all(is_control_record(record) for record in late_server)
        ):
            frames, server = frames[:captured], server[:captured]
            late_control_messages += max(len(late_frames), len(late_server))
        if len(frames) != len(times) or len(server) != len(frames) or count > len(times):
            errors.append(
                f"Browser/CDP/server {browser_direction} message counts differ "
                f"({len(times)}/{len(frames)}/{len(server)})"
            )
            continue
        for index, (frame, at, observed) in enumerate(zip(frames, times, server, strict=True), 1):
            try:
                body = message_bytes(frame)
            except (KeyError, ValueError) as error:
                errors.append(str(error))
                continue
            if (
                observed["index"] != index
                or observed["sha256"] != hashlib.sha256(body).hexdigest()
                or observed["bytes"] != len(body)
            ):
                errors.append(f"Server/CDP {browser_direction} message {index} differs")
            control = frame["opcode"] == 1 and body in (b"2", b"3") and is_control_record(observed)
            if control:
                control_messages.append(
                    {
                        "direction": browser_direction,
                        "index": index,
                        "at": at,
                        "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "in_observation_window": ready["start"] <= at <= ready["end"],
                    }
                )
                continue
            if index > count:
                errors.append("Socket application messages arrived after the ready boundary")
            elif at > ready["end"]:
                errors.append("Readiness counted a later socket application message")
            if index > count and at <= ready["end"]:
                errors.append("Readiness omitted an already-observed socket application message")
            owners = [mark for mark in snapshot.get("marks", [ready]) if mark["start"] <= at <= mark["end"]]
            if len(owners) != 1 or owners[0]["operation"] != observed["operation"]:
                errors.append("Socket message falls outside its correlated operation window")
            if ready["start"] <= at <= ready["end"]:
                if observed["operation"] != ready["operation"]:
                    errors.append("Socket window contains an uncorrelated application message")
                selected.append(
                    {
                        "direction": browser_direction,
                        "index": index,
                        "at": at,
                        "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "operation": observed["operation"],
                        "revision": observed["revision"],
                        "server_ms": observed.get("server_ms"),
                        "prepare_ms": observed.get("prepare_ms"),
                    }
                )
    incoming = [entry for entry in selected if entry["direction"] == "received"]
    outgoing = [entry for entry in selected if entry["direction"] == "sent"]
    observed_controls = [entry for entry in control_messages if entry["in_observation_window"]]
    if not any(entry["revision"] == ready["revision"] for entry in incoming):
        errors.append("No received socket message acknowledges the ready revision")
    if ready["operation"] != "initial" and not outgoing:
        errors.append("Server action sent no socket message")
    complete = not errors
    preparation_errors = audit.get("preparation_errors", [])
    if not isinstance(preparation_errors, list) or any(not isinstance(error, str) for error in preparation_errors):
        preparation_errors = ["server preparation audit is malformed"]
    return {
        "errors": errors,
        "preparation_errors": preparation_errors,
        "messages": selected,
        "control_messages": control_messages,
        # Heartbeats that arrived after the page's message log was copied.
        "late_control_messages": late_control_messages,
        "control_request_bytes": sum(entry["bytes"] for entry in observed_controls if entry["direction"] == "sent"),
        "control_response_bytes": sum(
            entry["bytes"] for entry in observed_controls if entry["direction"] == "received"
        ),
        "sent_messages": len(outgoing),
        "received_messages": len(incoming),
        "request_body_bytes": sum(entry["bytes"] for entry in outgoing) if complete else None,
        "decoded_response_bytes": sum(entry["bytes"] for entry in incoming) if complete else None,
        "encoded_response_body_bytes": sum(entry["bytes"] for entry in incoming) if complete else None,
        "byte_method": (
            "CDP UTF-8/binary application messages matched to server hashes; "
            "audited Engine.IO heartbeat bytes are retained separately; handshake has no extensions"
        ),
        "wire_bytes": None,
        "server_timings": [
            entry for entry in incoming if entry["server_ms"] is not None or entry["prepare_ms"] is not None
        ],
    }
