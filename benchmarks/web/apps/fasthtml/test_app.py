"""Check FastHTML response rendering and CSRF/session rejection through ASGI."""

# Keep these checks runnable with the application environment alone.
# ruff: noqa: PT009
import re
import unittest
from typing import Any

from app import application
from starlette.testclient import TestClient


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(application)
        self.page = self.client.get("/?session=test&count=14")
        self.token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', self.page.text).group(1)

    def tearDown(self) -> None:
        self.client.close()

    def post(self, **updates: str) -> Any:
        data = {"csrfmiddlewaretoken": self.token, "session": "test", "action": "probe", "operation": "one"}
        data.update(updates)
        return self.client.post("/action", data=data, headers={"HX-Request": "true"})

    def test_renders_full_page_and_fragment_with_correlated_revision(self) -> None:
        self.assertEqual(self.page.status_code, 200)
        self.assertTrue(self.page.text.startswith("<!doctype html>"))
        self.assertEqual(self.page.text.count("data-row-id="), 14)
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-bench-operation"], "one")
        self.assertEqual(response.headers["x-bench-revision"], "1")
        self.assertNotIn("<html", response.text)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_missing_invalid_and_non_ascii_csrf_tokens_fail(self) -> None:
        for token in ("", "incorrect", "é"):
            with self.subTest(token=token):
                self.assertEqual(self.post(csrfmiddlewaretoken=token).status_code, 403)

    def test_wrong_session_and_origin_fail(self) -> None:
        self.assertEqual(self.post(session="other").status_code, 403)
        response = self.client.post(
            "/action",
            data={
                "csrfmiddlewaretoken": self.token,
                "session": "test",
                "action": "probe",
                "operation": "one",
            },
            headers={"Origin": "https://other.example", "HX-Request": "true"},
        )
        self.assertEqual(response.status_code, 403)

    def test_validation_errors_keep_attempted_title(self) -> None:
        response = self.post(action="save", title="")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Use between 3 and 80 characters.", response.text)
        self.assertIn('name="title" value=""', response.text)
        self.assertIn("Project Name", response.text)

    def test_host_and_method_restrictions(self) -> None:
        self.assertEqual(self.client.get("/action").status_code, 405)
        self.assertEqual(self.client.get("/", headers={"host": "other.example"}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
