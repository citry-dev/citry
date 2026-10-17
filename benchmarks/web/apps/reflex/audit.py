"""Retain WebSocket message references; calculate hashes after browser capture."""

# The copied scenario is resolved before importing its shared timing helper.
# ruff: noqa: E402, I001

import hashlib
import inspect
import json
import sys
import time
import uuid
from contextvars import ContextVar
from functools import wraps
from importlib.metadata import version
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
SCENARIO = HERE / "scenario"
if not SCENARIO.is_dir():
    SCENARIO = HERE.parents[1] / "scenarios" / "project_board"
sys.path.insert(0, str(SCENARIO))

from render_timing import (
    PreparationTimings,
    discard_pending_preparation,
    pending_preparation,
    preparation_scope,
    preparation_span,
    take_pending_preparation,
)
from reflex import state as state_module
from reflex.app import EventNamespace
from reflex.middleware.hydrate_middleware import HydrateMiddleware
from reflex.utils import format as format_module
from reflex_base.event.processor.base_state_processor import BaseStateEventProcessor
from socketio.async_manager import AsyncManager
from socketio.packet import Packet

records: dict[str, list[dict[str, Any]]] = {}
accepted: dict[str, dict[str, int]] = {}
preparations: dict[str, list[dict[str, Any]]] = {}
preparation_faults: dict[str, list[str]] = {}
CONNECTION_SCOPE_KEY = "citry_bench_connection"
_event_active: ContextVar[bool] = ContextVar("reflex_bench_event_active", default=False)
_hydrate_active: ContextVar[bool] = ContextVar("reflex_bench_hydrate_active", default=False)
_emission: ContextVar[dict[str, Any] | None] = ContextVar("reflex_bench_emission", default=None)
_installation = {"done": False}


def retain_preparation(connection: str, text: str, duration: float) -> None:
    """Retain serializer output by reference for post-readiness correlation."""
    preparations.setdefault(connection, []).append({"text": text, "prepare_ms": duration * 1000})


async def run_event_scope(function: Any, *args: Any, **kwargs: Any) -> Any:
    """Run one Reflex event execution and clear task-local work on every exit."""
    token = _event_active.set(True)
    try:
        return await function(*args, **kwargs)
    finally:
        _event_active.reset(token)
        discard_pending_preparation()


def install_preparation_timing() -> None:
    """Wrap the pinned Reflex state builders and configured JSON serializer."""
    if _installation["done"]:
        raise RuntimeError("Reflex preparation timing is already installed")
    if (
        version("reflex") != "0.9.10.post2"
        or version("python-socketio") != "5.16.4"
        or version("starlette") != "1.6.0"
    ):
        raise RuntimeError(
            "Reflex preparation timing requires Reflex 0.9.10.post2, python-socketio 5.16.4 and Starlette 1.6.0"
        )

    original_execute = BaseStateEventProcessor._execute_event
    original_emit = EventNamespace.emit_update
    original_delta = state_module.BaseState.get_delta
    original_dict = state_module.BaseState.dict
    original_hydrate = HydrateMiddleware.preprocess
    original_dumps = format_module.json_dumps
    expected = (
        (
            original_execute,
            "reflex_base.event.processor.base_state_processor",
            "(self, *, entry: 'EventQueueEntry', registered_handler: 'RegisteredEventHandler') -> 'None'",
            True,
        ),
        (original_emit, "reflex.app", "(self, update: 'StateUpdate', token: 'str') -> 'None'", True),
        (original_delta, "reflex.state", "(self) -> 'Delta'", False),
        (
            original_dict,
            "reflex.state",
            "(self, include_computed: 'bool' = True, initial: 'bool' = False, **kwargs) -> 'builtins.dict[str, Any]'",
            False,
        ),
        (
            original_hydrate,
            "reflex.middleware.hydrate_middleware",
            "(self, app: 'App', state: 'BaseState', event: 'Event') -> 'StateUpdate | None'",
            True,
        ),
        (original_dumps, "reflex_base.utils.format", "(obj: 'Any', **kwargs) -> 'str'", False),
        (Packet.encode, "socketio.packet", "(self)", False),
        (
            AsyncManager.emit,
            "socketio.async_manager",
            "(self, event, data, namespace, room=None, skip_sid=None, callback=None, to=None, **kwargs)",
            True,
        ),
    )
    if any(
        function.__module__ != module
        or str(inspect.signature(function)) != signature
        or inspect.iscoroutinefunction(function) is not asynchronous
        for function, module, signature, asynchronous in expected
    ):
        raise RuntimeError("Reflex preparation timing hook signatures differ from the pinned releases")

    @wraps(original_execute)
    async def measured_execute(processor: Any, *, entry: Any, registered_handler: Any) -> None:
        await run_event_scope(
            original_execute,
            processor,
            entry=entry,
            registered_handler=registered_handler,
        )

    @wraps(original_delta)
    def measured_delta(state: Any) -> Any:
        if not _event_active.get():
            return original_delta(state)
        timing = pending_preparation()
        with preparation_scope(timing), preparation_span():
            return original_delta(state)

    @wraps(original_dict)
    def measured_dict(state: Any, *args: Any, **kwargs: Any) -> Any:
        if not _hydrate_active.get():
            return original_dict(state, *args, **kwargs)
        timing = pending_preparation()
        with preparation_scope(timing), preparation_span():
            return original_dict(state, *args, **kwargs)

    @wraps(original_hydrate)
    async def measured_hydrate(middleware: Any, app: Any, state: Any, event: Any) -> Any:
        token = _hydrate_active.set(_event_active.get())
        try:
            result = await original_hydrate(middleware, app, state, event)
        finally:
            _hydrate_active.reset(token)
        if result is None:
            discard_pending_preparation()
        return result

    @wraps(original_emit)
    async def measured_emit(namespace: Any, update: Any, token: str) -> None:
        timing = take_pending_preparation() or PreparationTimings()
        socket_record = namespace._token_manager.token_to_socket.get(token)
        connection = None
        if socket_record is not None and namespace.app.sio is not None:
            environ = namespace.app.sio.get_environ(socket_record.sid, namespace.namespace)
            if environ is not None:
                connection = environ.get("asgi.scope", {}).get(CONNECTION_SCOPE_KEY)
        emission = {"connection": connection, "timing": timing, "texts": []}
        emission_token = _emission.set(emission)
        try:
            await original_emit(namespace, update, token)
        finally:
            _emission.reset(emission_token)
            discard_pending_preparation()
        if not isinstance(connection, str):
            return
        texts = emission["texts"]
        if len(texts) == 1:
            retain_preparation(connection, texts[0], timing.duration)
        else:
            preparation_faults.setdefault(connection, []).append(
                f"Reflex emission produced {len(texts)} measured JSON payloads"
            )

    @wraps(original_dumps)
    def measured_dumps(value: Any, *args: Any, **kwargs: Any) -> str:
        emission = _emission.get()
        if emission is None:
            return original_dumps(value, *args, **kwargs)
        timing = emission["timing"]
        with preparation_scope(timing), preparation_span():
            text = original_dumps(value, *args, **kwargs)
        emission["texts"].append(text)
        return text

    BaseStateEventProcessor._execute_event = measured_execute
    EventNamespace.emit_update = measured_emit
    state_module.BaseState.get_delta = measured_delta
    state_module.BaseState.dict = measured_dict
    HydrateMiddleware.preprocess = measured_hydrate
    format_module.json_dumps = measured_dumps
    _installation["done"] = True


def instrument_board_preparation(board_module: Any) -> None:
    """Add the adapter's snapshot and state-projection work to the next delta."""
    original_snapshot = board_module.snapshot
    original_update = board_module.Board._update_board

    @wraps(original_snapshot)
    def measured_snapshot(session: str) -> Any:
        if not _event_active.get():
            return original_snapshot(session)
        timing = pending_preparation()
        with preparation_scope(timing), preparation_span():
            return original_snapshot(session)

    @wraps(original_update)
    def measured_update(state: Any, value: dict[str, Any]) -> None:
        if not _event_active.get():
            original_update(state, value)
            return
        timing = pending_preparation()
        with preparation_scope(timing), preparation_span():
            original_update(state, value)

    board_module.snapshot = measured_snapshot
    board_module.Board._update_board = measured_update


def validate_preparation_application(application: Any) -> None:
    """Fail if the active Socket.IO packet encoder did not capture our serializer."""
    socket_server = application.sio
    if socket_server is None:
        raise RuntimeError("Reflex preparation timing requires an active Socket.IO server")
    configured = socket_server.packet_class.json.dumps
    if isinstance(configured, staticmethod):
        configured = configured.__func__
    if configured is not format_module.json_dumps:
        raise RuntimeError("Reflex Socket.IO did not capture the measured JSON serializer")


def decode(text: str) -> dict[str, Any]:
    # Socket.IO event packets include the namespace before the JSON array.
    if text.startswith("42") and "[" in text:
        packet = json.loads(text[text.index("[") :])
        return packet[1] if len(packet) == 2 and isinstance(packet[1], dict) else {}
    return {}


def board_identity(value: Any) -> tuple[str, int] | None:
    for state in value.get("delta", {}).values():
        if "operation_rx_state_" in state and "revision_rx_state_" in state:
            return state["operation_rx_state_"], int(state["revision_rx_state_"])
    return None


def event_operation(value: dict[str, Any]) -> str | None:
    return value.get("payload", {}).get("values", {}).get("operation")


def report(session: str) -> dict[str, Any]:
    """Decode and hash retained messages only when the runner requests the audit."""
    connections = {
        raw["connection"]
        for group in records.values()
        for raw in group
        if decode(raw["text"]).get("router_data", {}).get("query", {}).get("session") == session
    }
    pending = {
        (connection, "initial"): stamp
        for group in accepted.values()
        for connection, stamp in group.items()
        if connection in connections
    }
    result = []
    preparation_errors = []
    expected = {connection: list(preparations.get(connection, [])) for connection in connections}
    for connection in connections:
        preparation_errors.extend(preparation_faults.get(connection, []))
    for raw in (row for group in records.values() for row in group if row["connection"] in connections):
        payload = decode(raw["text"])
        identity = board_identity(payload) if raw["direction"] == "sent" else None
        operation = identity[0] if identity else event_operation(payload)
        if operation is None and (
            raw["text"].startswith(("0{", "40"))
            or payload.get("name", "").endswith((".hydrate", ".on_load_internal"))
            or ("delta" in payload and all("board_app" not in key for key in payload["delta"]))
        ):
            operation = "initial"
        encoded = raw["text"].encode("utf-8")
        item = {
            **raw,
            "message_type": payload.get("name", "state" if "delta" in payload else "socket.io-control"),
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "bytes": len(encoded),
            "decoded_utf8_bytes": len(encoded),
            "encoded_identity_bytes": len(encoded),
            "operation": operation,
            "revision": identity[1] if identity else None,
        }
        if raw["direction"] == "sent" and ("delta" in payload or "events" in payload):
            queue = expected.get(raw["connection"], [])
            if queue and raw["text"].endswith(queue[0]["text"]):
                item["prepare_ms"] = queue.pop(0)["prepare_ms"]
            elif queue:
                preparation_errors.append(
                    f"Reflex preparation output differs at sent message {raw['index']} on {raw['connection']}"
                )
            else:
                preparation_errors.append(
                    f"Reflex sent message {raw['index']} on {raw['connection']} has no preparation"
                )
        key = (raw["connection"], operation)
        if raw["direction"] == "received" and operation:
            pending[key] = raw["timestamp_ns"]
        if raw["direction"] == "sent" and key in pending:
            item["server_ms"] = (raw["timestamp_ns"] - pending.pop(key)) / 1_000_000
        result.append(item)
    for connection, queue in expected.items():
        if queue:
            preparation_errors.append(f"Reflex retained {len(queue)} unmatched preparations on {connection}")
    return {
        "session": session,
        "records": result,
        "preparation_errors": preparation_errors,
        "compression": "identity",
        "wire_frame_overhead_included": False,
    }


class ObserveTransport:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "websocket":
            start = time.perf_counter_ns()

            async def http_send(message: dict) -> None:
                if message["type"] == "http.response.start":
                    message = {
                        **message,
                        "headers": [
                            *message.get("headers", []),
                            (b"cache-control", b"no-store"),
                            (
                                b"server-timing",
                                f"application;dur={(time.perf_counter_ns() - start) / 1_000_000:.3f}".encode(),
                            ),
                        ],
                    }
                await send(message)

            await self.app(scope, receive, http_send)
            return
        headers = dict(scope.get("headers", []))
        host = headers.get(b"host", b"").decode("latin1")
        origin = headers.get(b"origin", b"").decode("latin1")
        scheme = "https" if scope.get("scheme") == "wss" else "http"
        # Browser WebSockets need an origin check because CORS does not protect them.
        if urlsplit(f"//{host}").hostname not in ("127.0.0.1", "localhost") or origin != f"{scheme}://{host}":
            await send({"type": "websocket.close", "code": 1008, "reason": "A matching browser Origin is required."})
            return
        session = parse_qs(scope.get("query_string", b"").decode()).get("session", ["manual"])[0]
        connection = uuid.uuid4().hex
        scope[CONNECTION_SCOPE_KEY] = connection
        sequence = {"received": 0, "sent": 0}
        session_records = records.setdefault(session, [])

        def record(direction: str, message: dict, observed_ns: int) -> None:
            raw = message.get("text")
            if raw is None:
                return
            sequence[direction] += 1
            session_records.append(
                {
                    "connection": connection,
                    "direction": direction,
                    "index": sequence[direction],
                    "text": raw,
                    "timestamp_ns": observed_ns,
                }
            )

        async def observed_receive() -> dict:
            message = await receive()
            if message["type"] == "websocket.receive":
                record("received", message, time.perf_counter_ns())
            return message

        async def observed_send(message: dict) -> None:
            if message["type"] == "websocket.accept":
                await send(message)
                accepted.setdefault(session, {})[connection] = time.perf_counter_ns()
                return
            elif message["type"] == "websocket.send":
                record("sent", message, time.perf_counter_ns())
            await send(message)

        await self.app(scope, observed_receive, observed_send)
