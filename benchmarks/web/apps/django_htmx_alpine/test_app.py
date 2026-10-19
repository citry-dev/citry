"""Check that the page and fragment paths share one prepared model snapshot."""

from __future__ import annotations

# ruff: noqa: PT009
import unittest
from unittest.mock import patch

import app
from django.test import Client


class AppTests(unittest.TestCase):
    def test_initial_page_uses_one_snapshot_for_page_and_board(self) -> None:
        with patch.object(app, "snapshot", wraps=app.snapshot) as snapshot:
            response = Client().get("/?session=single-snapshot&count=14")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(snapshot.call_count, 1)
        self.assertEqual(response.content.count(b'data-row-id="'), 14)

    def test_action_fragment_still_uses_one_snapshot(self) -> None:
        client = Client(enforce_csrf_checks=True)
        page = client.get("/?session=single-snapshot-action&count=14")
        token = client.cookies["csrftoken"].value
        with patch.object(app, "snapshot", wraps=app.snapshot) as snapshot:
            response = client.post(
                "/action",
                {
                    "session": "single-snapshot-action",
                    "action": "probe",
                    "operation": "single-snapshot-action",
                    "csrfmiddlewaretoken": token,
                },
            )

        self.assertEqual(page.status_code, 200)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(snapshot.call_count, 1)


if __name__ == "__main__":
    unittest.main()
