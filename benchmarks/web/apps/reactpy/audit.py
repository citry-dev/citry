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
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
SCENARIO = HERE / "scenario"
if not SCENARIO.is_dir():
    SCENARIO = HERE.parents[1] / "scenarios" / "project_board"
sys.path.insert(0, str(SCENARIO))

from render_timing import (
    current_pending_preparation,
    discard_pending_preparation,
    pending_preparation,
    preparation_scope,
    preparation_span,
    take_pending_preparation,
)
from reactpy.backend import starlette as backend
from reactpy.config import REACTPY_ASYNC_RENDERING
from reactpy.core.layout import Layout

records: dict[str, list[dict[str, Any]]] = {}
accepted: dict[str, dict[str, int]] = {}
preparations: dict[str, list[dict[str, Any]]] = {}
CONNECTION_SCOPE_KEY = "citry_bench_connection"
_connection: ContextVar[str | None] = ContextVar("reactpy_bench_connection", default=None)
_serialized: ContextVar[list[str] | None] = ContextVar("reactpy_bench_serialized", default=None)
_installation = {"done": False}


def retain_preparation(connection: str, text: str, duration: float) -> None:
    """Retain serializer output by reference for post-readiness correlation."""
    preparations.setdefault(connection, []).append({"text": text, "prepare_ms": duration * 1000})


def install_preparation_timing() -> None:
    """Wrap the pinned active layout builder and its existing JSON serializer."""
    if _installation["done"]:
        raise RuntimeError("ReactPy preparation timing is already installed")
    if version("reactpy") != "1.1.0" or version("starlette") != "0.52.1":
        raise RuntimeError("ReactPy preparation timing requires ReactPy 1.1.0 and Starlette 0.52.1")

    if REACTPY_ASYNC_RENDERING.current:
        raise RuntimeError("ReactPy preparation timing requires serial rendering")
    original_create = Layout._create_layout_update
    original_callbacks = backend._make_send_recv_callbacks
    if (
        original_create.__module__ != "reactpy.core.layout"
        or str(inspect.signature(original_create)) != "(self, old_state: '_ModelState') -> 'LayoutUpdateMessage'"
        or not inspect.iscoroutinefunction(original_create)
        or original_callbacks.__module__ != "reactpy.backend.starlette"
        or str(inspect.signature(original_callbacks))
        != "(socket: 'WebSocket') -> 'tuple[SendCoroutine, RecvCoroutine]'"
        or backend.json is not json
    ):
        raise RuntimeError("ReactPy preparation timing hook signatures differ from the pinned release")

    @wraps(original_create)
    async def measured_create(layout: Any, old_state: Any) -> Any:
        if take_pending_preparation() is not None:
            raise RuntimeError("ReactPy started a second layout update before serializing the first")
        timing = pending_preparation()
        try:
            with preparation_scope(timing), preparation_span():
                return await original_create(layout, old_state)
        except BaseException:
            discard_pending_preparation()
            raise

    @wraps(original_callbacks)
    def measured_callbacks(socket: Any) -> Any:
        send, receive = original_callbacks(socket)
        connection = socket.scope.get(CONNECTION_SCOPE_KEY)
        if not isinstance(connection, str):
            raise TypeError("ReactPy WebSocket is missing its benchmark connection identity")

        @wraps(send)
        async def measured_send(value: Any) -> None:
            token = _connection.set(connection)
            texts: list[str] = []
            serialized_token = _serialized.set(texts)
            try:
                await send(value)
                timing = take_pending_preparation()
                if timing is None or len(texts) != 1:
                    raise RuntimeError("ReactPy layout send did not serialize one measured payload")
                retain_preparation(connection, texts[0], timing.duration)
            finally:
                _serialized.reset(serialized_token)
                _connection.reset(token)
                discard_pending_preparation()

        return measured_send, receive

    original_json = backend.json
    original_dumps = original_json.dumps

    def measured_dumps(value: Any, *args: Any, **kwargs: Any) -> str:
        connection = _connection.get()
        if connection is None:
            return original_dumps(value, *args, **kwargs)
        timing = current_pending_preparation()
        if timing is None:
            raise RuntimeError("ReactPy serialized a layout update without measured construction")
        with preparation_scope(timing), preparation_span():
            text = original_dumps(value, *args, **kwargs)
        texts = _serialized.get()
        if texts is None:
            raise RuntimeError("ReactPy serializer ran outside its socket send scope")
        texts.append(text)
        return text

    Layout._create_layout_update = measured_create
    backend._make_send_recv_callbacks = measured_callbacks
    backend.json = SimpleNamespace(dumps=measured_dumps, loads=original_json.loads)
    _installation["done"] = True


def board_identity(value: Any) -> tuple[str, int] | None:
    if isinstance(value, dict):
        attrs = value.get("attributes", {})
        if attrs.get("id") == "board":
            return attrs["data-operation"], int(attrs["data-revision"])
        for child in value.values():
            found = board_identity(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = board_identity(child)
            if found:
                return found
    return None


def event_operation(value: dict[str, Any]) -> str | None:
    if value.get("type") != "layout-event":
        return None
    try:
        return value["data"][0]["target"]["elements"][0]["value"]
    except (KeyError, IndexError, TypeError):
        return None


def report(session: str) -> dict[str, Any]:
    """Decode and hash retained messages only when the runner requests the audit."""
    pending = {(connection, "initial"): stamp for connection, stamp in accepted.get(session, {}).items()}
    result = []
    preparation_errors = []
    expected = {connection: list(preparations.get(connection, [])) for connection in accepted.get(session, {})}
    for raw in records.get(session, []):
        payload = json.loads(raw["text"])
        identity = board_identity(payload) if raw["direction"] == "sent" else None
        operation = identity[0] if identity else event_operation(payload)
        encoded = raw["text"].encode("utf-8")
        item = {
            **raw,
            "message_type": payload.get("type"),
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "bytes": len(encoded),
            "decoded_utf8_bytes": len(encoded),
            "encoded_identity_bytes": len(encoded),
            "operation": operation,
            "revision": identity[1] if identity else None,
        }
        if raw["direction"] == "sent" and payload.get("type") == "layout-update":
            queue = expected.get(raw["connection"], [])
            if queue and queue[0]["text"] == raw["text"]:
                item["prepare_ms"] = queue.pop(0)["prepare_ms"]
            elif queue:
                preparation_errors.append(
                    f"ReactPy preparation output differs at sent message {raw['index']} on {raw['connection']}"
                )
            else:
                preparation_errors.append(
                    f"ReactPy sent message {raw['index']} on {raw['connection']} has no preparation"
                )
        key = (raw["connection"], operation)
        if raw["direction"] == "received" and operation:
            pending[key] = raw["timestamp_ns"]
        if raw["direction"] == "sent" and key in pending:
            item["server_ms"] = (raw["timestamp_ns"] - pending.pop(key)) / 1_000_000
        result.append(item)
    for connection, queue in expected.items():
        if queue:
            preparation_errors.append(f"ReactPy retained {len(queue)} unmatched preparations on {connection}")
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
