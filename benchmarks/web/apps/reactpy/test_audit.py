"""Verify exact message retention and operation correlation without a browser."""

# These checks run in the isolated app environment without pytest.
# ruff: noqa: PT009

import asyncio
import hashlib
import json
import unittest
from typing import Any

from audit import ObserveTransport, accepted, preparations, records, report, retain_preparation


class AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        records.clear()
        accepted.clear()
        preparations.clear()

    def test_observer_preserves_protocol_bytes_and_pairs_the_operation(self) -> None:
        incoming = json.dumps({"type": "layout-event", "data": [{"target": {"elements": [{"value": "op-1"}]}}]})
        outgoing = json.dumps(
            {
                "type": "layout-update",
                "model": {
                    "tagName": "section",
                    "attributes": {"id": "board", "data-operation": "op-1", "data-revision": 1, "title": "Žlutý"},
                },
            },
            ensure_ascii=False,
        )
        sent = []

        async def application(_scope: dict, receive: Any, send: Any) -> None:
            await send({"type": "websocket.accept"})
            message = await receive()
            self.assertIs(message["text"], incoming)
            await send({"type": "websocket.send", "text": outgoing})

        async def receive() -> dict:
            return {"type": "websocket.receive", "text": incoming}

        async def send(message: dict) -> None:
            sent.append(message)

        asyncio.run(
            ObserveTransport(application)(
                {
                    "type": "websocket",
                    "query_string": b"session=test",
                    "scheme": "ws",
                    "headers": [(b"host", b"127.0.0.1:8913"), (b"origin", b"http://127.0.0.1:8913")],
                },
                receive,
                send,
            )
        )
        retain_preparation(next(iter(accepted["test"])), outgoing, 0.001)
        self.assertIs(sent[1]["text"], outgoing)
        self.assertNotIn("sha256", records["test"][0])
        result = report("test")["records"]
        self.assertEqual([item["operation"] for item in result], ["op-1", "op-1"])
        self.assertEqual(result[1]["revision"], 1)
        self.assertEqual(result[1]["bytes"], len(outgoing.encode("utf-8")))
        self.assertGreater(result[1]["bytes"], len(outgoing))
        self.assertEqual(result[1]["sha256"], hashlib.sha256(outgoing.encode("utf-8")).hexdigest())
        self.assertGreaterEqual(result[1]["server_ms"], 0)

    def test_preparations_correlate_by_connection_and_message_order(self) -> None:
        accepted["test"] = {"a": 100, "b": 100}
        first = '{"type":"layout-update","model":{"value":1}}'
        second = '{"type":"layout-update","model":{"value":2}}'
        retain_preparation("a", first, 0.001)
        retain_preparation("a", second, 0.002)
        retain_preparation("b", first, 0.003)
        records["test"] = [
            {"direction": "sent", "connection": "a", "index": 1, "text": first, "timestamp_ns": 200},
            {"direction": "sent", "connection": "b", "index": 1, "text": first, "timestamp_ns": 300},
            {"direction": "sent", "connection": "a", "index": 2, "text": second, "timestamp_ns": 400},
        ]
        audit = report("test")
        self.assertEqual([row["prepare_ms"] for row in audit["records"]], [1, 3, 2])
        self.assertEqual(audit["preparation_errors"], [])

    def test_mismatched_preparation_is_reported_without_a_duration(self) -> None:
        accepted["test"] = {"a": 100}
        retain_preparation("a", '{"expected":true}', 0.001)
        records["test"] = [
            {
                "direction": "sent",
                "connection": "a",
                "index": 1,
                "text": '{"type":"layout-update","actual":true}',
                "timestamp_ns": 200,
            }
        ]
        audit = report("test")
        self.assertNotIn("prepare_ms", audit["records"][0])
        self.assertEqual(len(audit["preparation_errors"]), 2)

    def test_equal_payloads_do_not_cross_session_boundaries(self) -> None:
        text = '{"type":"layout-update","model":{"value":1}}'
        for session, connection, duration in (("one", "a", 0.001), ("two", "b", 0.002)):
            accepted[session] = {connection: 100}
            retain_preparation(connection, text, duration)
            records[session] = [
                {"direction": "sent", "connection": connection, "index": 1, "text": text, "timestamp_ns": 200}
            ]
        self.assertEqual(report("one")["records"][0]["prepare_ms"], 1)
        self.assertEqual(report("two")["records"][0]["prepare_ms"], 2)

    def test_initial_timing_uses_its_own_connection_acceptance(self) -> None:
        accepted["test"] = {"a": 100, "b": 500}
        text = json.dumps(
            {
                "type": "layout-update",
                "model": {"attributes": {"id": "board", "data-operation": "initial", "data-revision": 0}},
            }
        )
        retain_preparation("a", text, 0.001)
        retain_preparation("b", text, 0.002)
        records["test"] = [
            {"direction": "sent", "connection": "a", "index": 1, "text": text, "timestamp_ns": 200},
            {"direction": "sent", "connection": "b", "index": 1, "text": text, "timestamp_ns": 800},
        ]
        result = report("test")["records"]
        self.assertEqual(result[0]["server_ms"], 0.0001)
        self.assertEqual(result[1]["server_ms"], 0.0003)

    def test_uncorrelated_message_does_not_get_a_fabricated_duration(self) -> None:
        records["test"] = [
            {
                "direction": "sent",
                "connection": "a",
                "index": 1,
                "text": '{"type":"layout-update","model":{"error":"failed"}}',
                "timestamp_ns": 200,
            }
        ]
        audit = report("test")
        result = audit["records"][0]
        self.assertIsNone(result["operation"])
        self.assertNotIn("server_ms", result)
        self.assertIn("has no preparation", audit["preparation_errors"][0])

    def test_missing_or_foreign_origin_is_rejected_before_the_backend(self) -> None:
        for origin in (None, b"http://other.example", b"https://127.0.0.1:8913"):
            sent = []

            async def application(_scope: dict, _receive: Any, _send: Any) -> None:
                self.fail("Rejected handshakes must not reach ReactPy")

            async def receive() -> dict:
                return {"type": "websocket.connect"}

            async def send(message: dict, target: list[dict] = sent) -> None:
                target.append(message)

            headers = [(b"host", b"127.0.0.1:8913")]
            if origin:
                headers.append((b"origin", origin))
            asyncio.run(
                ObserveTransport(application)({"type": "websocket", "scheme": "ws", "headers": headers}, receive, send)
            )
            self.assertEqual(sent[0]["type"], "websocket.close")
            self.assertEqual(sent[0]["code"], 1008)


if __name__ == "__main__":
    unittest.main()
