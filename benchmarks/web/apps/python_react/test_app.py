"""Check the shared backend's security and protocol using a real ASGI test client."""

# Run the shared API checks with the adapter's test environment.
# ruff: noqa: PT009
import math
import re
import unittest
from typing import Any

from app import application
from model import snapshot
from starlette.testclient import TestClient


class JsonApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(application)
        self.client.get("/?count=14&session=security-check")
        initial = self.client.get("/initial")
        self.assert_preparation(initial)
        self.token = initial.json()["csrf"]
        self.values = {"session": "security-check", "action": "probe", "operation": "test-probe"}

    def tearDown(self) -> None:
        self.client.close()

    def test_initial_and_action_correlate_server_state(self) -> None:
        response = self.client.post("/action", json=self.values, headers={"x-csrf-token": self.token})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["board"]["revision"], 1)
        self.assertEqual(response.headers["x-bench-operation"], "test-probe")
        self.assertEqual(response.headers["x-bench-revision"], "1")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assert_preparation(response)

    def assert_preparation(self, response: Any) -> None:
        match = re.search(r"(?:^|,)\s*prepare;dur=([^,;\s]+)", response.headers["server-timing"])
        self.assertIsNotNone(match)
        value = float(match.group(1))
        self.assertTrue(math.isfinite(value))
        self.assertGreaterEqual(value, 0)

    def test_missing_csrf_or_wrong_origin_rejects_before_mutation(self) -> None:
        for headers in (
            {},
            {"x-csrf-token": "wrong"},
            {"x-csrf-token": self.token, "origin": "https://other.example"},
        ):
            response = self.client.post("/action", json=self.values, headers=headers)
            self.assertEqual(response.status_code, 403)
            self.assertNotIn("prepare;dur", response.headers["server-timing"])
        self.assertEqual(snapshot("security-check")["revision"], 0)

    def test_foreign_session_rejected(self) -> None:
        response = self.client.post(
            "/action", json={**self.values, "session": "other"}, headers={"x-csrf-token": self.token}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(snapshot("security-check")["revision"], 0)

    def test_bad_values_and_unknown_fields_rejected(self) -> None:
        for extra in ({"query": None}, {"unknown": "field"}, {"action": "missing"}, {"operation": ""}):
            response = self.client.post("/action", json={**self.values, **extra}, headers={"x-csrf-token": self.token})
            self.assertEqual(response.status_code, 400)
        self.assertEqual(snapshot("security-check")["revision"], 0)

    def test_invalid_title_is_a_completed_business_response(self) -> None:
        response = self.client.post(
            "/action", json={**self.values, "action": "save", "title": ""}, headers={"x-csrf-token": self.token}
        )
        value = response.json()["board"]
        self.assertEqual(value["revision"], 1)
        self.assertEqual(value["title"], "Project Name")
        self.assertEqual(value["title_input"], "")
        self.assertTrue(value["error"])

    def test_bootstrap_requires_signed_session(self) -> None:
        self.client.cookies.clear()
        self.assertEqual(self.client.get("/initial").status_code, 403)


if __name__ == "__main__":
    unittest.main()
