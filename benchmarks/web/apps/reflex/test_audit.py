"""Verify protocol correlation and rejection of unrelated browser origins."""

# Stdlib tests keep adapter installation independent of test tooling.
# ruff: noqa: PT009
import asyncio
import unittest
from typing import Any

from audit import (
    ObserveTransport,
    accepted,
    decode,
    preparation_faults,
    preparations,
    records,
    report,
    retain_preparation,
    run_event_scope,
)
from render_timing import current_pending_preparation, pending_preparation


class AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        records.clear()
        accepted.clear()
        preparations.clear()
        preparation_faults.clear()

    def test_native_namespace_packet(self) -> None:
        self.assertEqual(decode('42/_event,["event",{"name":"handler"}]'), {"name": "handler"})
        self.assertEqual(decode("2"), {})

    def test_audit_binds_session_and_operation(self) -> None:
        packets = [
            (
                "received",
                '42/_event,["event",{"name":"reflex___state.hydrate","router_data":{"query":{"session":"one"}}}]',
            ),
            ("received", '42/_event,["event",{"payload":{"values":{"operation":"op1"}}}]'),
            (
                "sent",
                '42/_event,["event",{"delta":{"board_app":{"operation_rx_state_":"op1","revision_rx_state_":1}}}]',
            ),
        ]
        counters = {"received": 0, "sent": 0}
        rows = []
        for index, (direction, text) in enumerate(packets):
            counters[direction] += 1
            rows.append(
                {
                    "connection": "connection",
                    "direction": direction,
                    "text": text,
                    "index": counters[direction],
                    "timestamp_ns": (index + 1) * 1_000_000,
                }
            )
        records["manual"] = rows
        retain_preparation(
            "connection",
            '["event",{"delta":{"board_app":{"operation_rx_state_":"op1","revision_rx_state_":1}}}]',
            0.001,
        )
        result = report("one")["records"]
        self.assertEqual([row["operation"] for row in result], ["initial", "op1", "op1"])
        self.assertEqual(result[-1]["server_ms"], 1)
        self.assertEqual(report("different")["records"], [])

    def test_preparations_correlate_by_connection_and_socket_packet_order(self) -> None:
        first = '["event",{"delta":{"other":{"value":1}}}]'
        second = '["event",{"delta":{"other":{"value":2}}}]'
        accepted["one"] = {"a": 100, "b": 100}
        retain_preparation("a", first, 0.001)
        retain_preparation("a", second, 0.002)
        retain_preparation("b", first, 0.003)
        records["one"] = [
            {
                "direction": "received",
                "connection": "a",
                "index": 1,
                "text": '42/_event,["event",{"name":"state.hydrate","router_data":{"query":{"session":"one"}}}]',
                "timestamp_ns": 150,
            },
            {
                "direction": "received",
                "connection": "b",
                "index": 1,
                "text": '42/_event,["event",{"name":"state.hydrate","router_data":{"query":{"session":"one"}}}]',
                "timestamp_ns": 160,
            },
            {"direction": "sent", "connection": "a", "index": 1, "text": f"42/_event,{first}", "timestamp_ns": 200},
            {"direction": "sent", "connection": "b", "index": 1, "text": f"42/_event,{first}", "timestamp_ns": 300},
            {"direction": "sent", "connection": "a", "index": 2, "text": f"42/_event,{second}", "timestamp_ns": 400},
        ]
        audit = report("one")
        self.assertEqual([row["prepare_ms"] for row in audit["records"] if "prepare_ms" in row], [1, 3, 2])
        self.assertEqual(audit["preparation_errors"], [])

    def test_mismatched_preparation_is_reported_without_a_duration(self) -> None:
        accepted["one"] = {"a": 100}
        retain_preparation("a", '["event",{"expected":true}]', 0.001)
        records["one"] = [
            {
                "direction": "received",
                "connection": "a",
                "index": 1,
                "text": '42/_event,["event",{"name":"state.hydrate","router_data":{"query":{"session":"one"}}}]',
                "timestamp_ns": 150,
            },
            {
                "direction": "sent",
                "connection": "a",
                "index": 1,
                "text": '42/_event,["event",{"delta":{"other":{"actual":true}}}]',
                "timestamp_ns": 200,
            },
        ]
        audit = report("one")
        self.assertNotIn("prepare_ms", audit["records"][-1])
        self.assertEqual(len(audit["preparation_errors"]), 2)

    def test_multiple_serializer_outputs_are_reported_as_invalid(self) -> None:
        accepted["one"] = {"a": 100}
        records["one"] = [
            {
                "direction": "received",
                "connection": "a",
                "index": 1,
                "text": '42/_event,["event",{"name":"state.hydrate","router_data":{"query":{"session":"one"}}}]',
                "timestamp_ns": 150,
            }
        ]
        preparation_faults["a"] = ["Reflex emission produced 2 measured JSON payloads"]
        audit = report("one")
        self.assertEqual(audit["preparation_errors"], ["Reflex emission produced 2 measured JSON payloads"])

    def test_event_failure_discards_task_local_preparation(self) -> None:
        async def fail() -> None:
            pending_preparation()
            raise RuntimeError("event failed")

        async def check() -> None:
            with self.assertRaisesRegex(RuntimeError, "event failed"):  # noqa: PT027 - stdlib-only adapter test
                await run_event_scope(fail)
            self.assertIsNone(current_pending_preparation())

        asyncio.run(check())

    def test_equal_payloads_do_not_cross_session_boundaries(self) -> None:
        payload = '["event",{"delta":{"other":{"value":1}}}]'
        for session, connection, duration in (("one", "a", 0.001), ("two", "b", 0.002)):
            accepted[session] = {connection: 100}
            retain_preparation(connection, payload, duration)
            records[session] = [
                {
                    "direction": "received",
                    "connection": connection,
                    "index": 1,
                    "text": (
                        '42/_event,["event",{"name":"state.hydrate","router_data":{"query":{"session":"'
                        + session
                        + '"}}}]'
                    ),
                    "timestamp_ns": 150,
                },
                {
                    "direction": "sent",
                    "connection": connection,
                    "index": 1,
                    "text": f"42/_event,{payload}",
                    "timestamp_ns": 200,
                },
            ]
        self.assertEqual(next(row for row in report("one")["records"] if "prepare_ms" in row)["prepare_ms"], 1)
        self.assertEqual(next(row for row in report("two")["records"] if "prepare_ms" in row)["prepare_ms"], 2)


class OriginTests(unittest.IsolatedAsyncioTestCase):
    async def test_foreign_origin_never_reaches_framework(self) -> None:
        async def backend(*_args: Any) -> None:
            self.fail("Foreign browser origin reached Reflex")

        async def receive() -> dict:
            return {"type": "websocket.connect"}

        messages = []

        async def send(message: dict) -> None:
            messages.append(message)

        await ObserveTransport(backend)(
            {
                "type": "websocket",
                "scheme": "ws",
                "headers": [(b"host", b"127.0.0.1:8917"), (b"origin", b"https://other.example")],
            },
            receive,
            send,
        )
        self.assertEqual(messages[0]["code"], 1008)


if __name__ == "__main__":
    unittest.main()
