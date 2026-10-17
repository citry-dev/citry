"""Exercise the real Unicorn protocol with Django's security middleware enabled."""

# Use stdlib unittest so the adapter needs no additional test dependencies.
# ruff: noqa: PT009
import json
import unittest
from time import time
from uuid import uuid4

import app  # noqa: F401 - configure Django before importing its client
from django.http import HttpResponse
from django.test import Client
from lxml import html
from model import snapshot


class UnicornSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Client(enforce_csrf_checks=True)
        self.session = uuid4().hex
        response = self.client.get(f"/?count=14&session={self.session}")
        root = html.fromstring(response.content).get_element_by_id("board")
        self.payload = {
            "id": root.attrib["unicorn:id"],
            "data": json.loads(root.attrib["unicorn:data"]),
            "meta": root.attrib["unicorn:meta"].split(":")[0] + f"::{int(time() * 1000)}",
            "actionQueue": [
                {"type": "syncInput", "payload": {"name": "operation", "value": "security-check"}},
                {"type": "callMethod", "payload": {"name": "act('probe')"}},
            ],
        }
        self.csrf = self.client.cookies["csrftoken"].value

    def post(self, **headers: str) -> HttpResponse:
        return self.client.post(
            "/unicorn/message/board", json.dumps(self.payload), content_type="application/json", **headers
        )

    def test_native_protocol_updates_and_correlates(self) -> None:
        response = self.post(HTTP_X_CSRFTOKEN=self.csrf)
        self.assertEqual(response.status_code, 200)
        self.assertIn("dom", response.json())
        self.assertEqual(response["X-Bench-Operation"], "security-check")
        self.assertEqual(response["X-Bench-Revision"], "1")
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_missing_csrf_rejects_before_mutation(self) -> None:
        self.assertEqual(self.post().status_code, 403)
        self.assertEqual(snapshot(self.session)["revision"], 0)

    def test_wrong_origin_rejects_before_mutation(self) -> None:
        response = self.post(HTTP_X_CSRFTOKEN=self.csrf, HTTP_ORIGIN="https://other.example")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(snapshot(self.session)["revision"], 0)

    def test_tampered_serialized_state_rejects_checksum(self) -> None:
        self.payload["data"]["query"] = "tampered"
        response = self.post(HTTP_X_CSRFTOKEN=self.csrf)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"error": "Checksum does not match"})
        self.assertEqual(snapshot(self.session)["revision"], 0)

    def test_component_from_another_signed_session_rejected(self) -> None:
        self.client.get(f"/?count=14&session={uuid4().hex}")
        response = self.post(HTTP_X_CSRFTOKEN=self.csrf)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(snapshot(self.session)["revision"], 0)


if __name__ == "__main__":
    unittest.main()
