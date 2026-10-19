"""Check startup, session protection and local asset delivery without a browser."""

# Django must be configured before constructing its test client.
# ruff: noqa: PT009

import unittest

import app  # noqa: F401
from django.test import Client


class ApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Client(enforce_csrf_checks=True)

    def test_page_uses_encrypted_component_and_local_assets(self) -> None:
        response = self.client.get("/?count=14&session=app-test")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('tetra-component="board_app__default__board"', html)
        self.assertIn('data-revision="0"', html)
        self.assertIn("/static/tetra/js/alpinejs.cdn.js", html)
        self.assertNotIn('src="https://', html)
        self.assertIn("csrftoken", response.cookies)
        self.assertIn("sessionid", response.cookies)

    def test_missing_csrf_rejects_native_method_request(self) -> None:
        self.client.get("/?count=14&session=csrf-test")
        response = self.client.post(
            "/__tetra__/board_app/default/board/act",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_invalid_fixture_is_rejected(self) -> None:
        response = self.client.get("/?count=11&session=invalid")
        self.assertEqual(response.status_code, 400)

    def test_static_asset_is_local_and_uncached(self) -> None:
        response = self.client.get("/static/tetra/js/alpinejs.cdn.min.js")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertGreater(len(response.content), 1000)
        self.assertEqual(self.client.get("/static/missing.js").status_code, 404)


if __name__ == "__main__":
    unittest.main()
