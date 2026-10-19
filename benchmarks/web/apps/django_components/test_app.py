"""Check native component rendering, request protection and local dependencies."""

# Configure Django before constructing its test client.
# ruff: noqa: PT009

import hashlib
import json
import unittest
from unittest.mock import patch

import app
from django.test import Client


class ApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Client(enforce_csrf_checks=True)

    def test_native_page_and_fragment_lifecycle_and_dependency_metadata(self) -> None:
        with (
            patch.object(app.Page, "get_template_data", autospec=True, side_effect=app.Page.get_template_data) as page,
            patch.object(
                app.Board, "get_template_data", autospec=True, side_effect=app.Board.get_template_data
            ) as board,
        ):
            initial = self.client.get("/?count=14&session=lifecycle")
            self.assertEqual(initial.status_code, 200)
            self.assertEqual((page.call_count, board.call_count), (1, 1))
            self.assertIn(b"data-djc-id-", initial.content)
            self.assertIn(b"/static/django_components/django_components.min.js", initial.content)
            updated = self.client.post(
                "/action",
                {
                    "session": "lifecycle",
                    "action": "select",
                    "operation": "test-select",
                    "row_id": "1",
                    "csrfmiddlewaretoken": self.client.cookies["csrftoken"].value,
                },
            )
            self.assertEqual(updated.status_code, 200)
            self.assertEqual((page.call_count, board.call_count), (1, 2))
            self.assertIn(b'data-revision="1"', updated.content)
            self.assertIn(b'data-selected="true"', updated.content)
            self.assertIn(b"globalThis.DjangoComponents", updated.content)
            self.assertEqual(updated["X-Bench-Operation"], "test-select")

    def test_missing_csrf_and_foreign_origin_fail_without_mutation(self) -> None:
        self.client.get("/?count=14&session=protected")
        values = {"session": "protected", "action": "insert", "operation": "forbidden"}
        self.assertEqual(self.client.post("/action", values).status_code, 403)
        values["csrfmiddlewaretoken"] = self.client.cookies["csrftoken"].value
        response = self.client.post("/action", values, HTTP_ORIGIN="https://foreign.invalid")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(app.snapshot("protected")["revision"], 0)

    def test_invalid_protocol_and_unsupported_count_fail(self) -> None:
        self.assertEqual(self.client.get("/?count=11&session=invalid").status_code, 400)
        self.client.get("/?count=14&session=invalid")
        response = self.client.post(
            "/action",
            {
                "session": "invalid",
                "action": "unknown",
                "operation": "bad",
                "csrfmiddlewaretoken": self.client.cookies["csrftoken"].value,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(app.snapshot("invalid")["revision"], 0)

    def test_all_fixture_sizes_use_the_same_component(self) -> None:
        for count in (14, 140, 1400):
            with self.subTest(count=count):
                response = self.client.get(f"/?count={count}&session=size-{count}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content.count(b'data-row-id="'), count)

    def test_local_manager_and_pinned_assets(self) -> None:
        response = self.client.get("/static/django_components/django_components.min.js")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn("Content-Encoding", response)
        manager = json.loads((app.HERE / "provenance.json").read_text())["manager"]
        self.assertEqual(hashlib.sha256(response.content).hexdigest(), manager["sha256"])
        self.assertEqual(len(response.content), manager["bytes"])
        self.assertEqual(self.client.get("/static/../app.py").status_code, 404)
        self.assertEqual(self.client.get("/static/missing.js").status_code, 404)
        for name, metadata in json.loads((app.HERE / "assets/sources.json").read_text()).items():
            self.assertEqual(hashlib.sha256((app.HERE / "assets" / name).read_bytes()).hexdigest(), metadata["sha256"])


if __name__ == "__main__":
    unittest.main()
