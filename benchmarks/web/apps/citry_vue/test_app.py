from __future__ import annotations

# ruff: noqa: I001, PT009

import json
import re
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

import app  # configure the benchmark Django application
from citry._protocol.events import build_call, build_call_envelope
from django.test import Client


class CitryVueServerTests(unittest.TestCase):
    def test_board_js_data_reuses_template_snapshot_revision(self) -> None:
        state = {"revision": 7, "phase_groups": []}
        component = app.Board._create_instance(kwargs={"session": "snapshot-reuse"}, slots={})
        with patch.object(app, "render_snapshot", return_value=state) as render_snapshot:
            template_data = component.template_data(component.kwargs, component.slots)
            js_data = component.js_data(component.kwargs, component.slots)

        self.assertEqual(render_snapshot.call_count, 1)
        self.assertIs(template_data["state"], state)
        self.assertEqual(js_data, {"server_revision": 7})

    @staticmethod
    def _configuration(client: Client, session: str) -> dict:
        page = client.get(f"/?session={session}&count=14")
        if page.status_code != 200:
            raise AssertionError(page.content.decode(errors="replace"))
        match = re.search(
            rb'<script type="application/json" data-citry-vue-document="[^"]*"[^>]*>(.*?)</script>', page.content
        )
        if match is None:
            raise AssertionError(page.content.decode(errors="replace"))
        return json.loads(match.group(1))

    def test_initial_prepared_payload_assets_and_csrf_floor(self) -> None:
        client = Client(enforce_csrf_checks=True)
        page = client.get("/?session=server-proof&count=14")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"data-citry-vue-document", page.content)
        configuration = self._configuration(client, "server-proof")
        manifest = configuration["manifest"]
        self.assertEqual(manifest["protocol"], "citry-vue-prepared/1")
        owner = next(item for item in manifest["occurrences"] if "eventContext" in item)
        self.assertEqual(
            set(owner["eventContext"]),
            {
                "serverRenderId",
                "stateToken",
                "publicState",
                "componentClassId",
                "descriptor",
            },
        )
        digest = manifest["definitions"][0]["sha256"]
        asset = client.get(f"/citry/ext/events/definitions/{digest}.js")
        self.assertEqual(asset.status_code, 200)
        self.assertIn(b"__citryRuntimeDefinitions", asset.content)
        rejected = client.post(
            "/citry/ext/events/call",
            data="{}",
            content_type="application/citry-events+json",
            HTTP_X_CITRY_EVENTS="1",
        )
        self.assertEqual(rejected.status_code, 403)

        context = owner["eventContext"]
        call = build_call(
            context["componentClassId"],
            "act",
            {"action": "probe", "operation": "manual"},
            caller_render_id=context["serverRenderId"],
            state_token=context["stateToken"],
            send_sequence=1,
        )
        envelope = build_call_envelope(
            "server-proof-1",
            [call],
            capabilities={
                "actions": ["render", "data", "state", "event", "redirect", "url"],
                "swaps": ["morph"],
                "renderers": ["vue-prepared/1"],
            },
        )
        accepted = client.post(
            "/citry/ext/events/call",
            data=json.dumps(envelope),
            content_type="application/citry-events+json",
            HTTP_X_CITRY_EVENTS="1",
            HTTP_X_CITRY_VUE_APP=manifest["appId"],
            HTTP_X_CITRY_VUE_OCCURRENCE=owner["id"],
            HTTP_X_CITRY_VUE_REVISION="0",
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        )
        self.assertEqual(accepted.status_code, 200)
        result = accepted.json()["results"][0]
        self.assertTrue(result["ok"])
        rendered = next(action for action in result["actions"] if action["action"] == "render")
        self.assertEqual(rendered["renderer"], "vue-prepared/1")
        self.assertEqual(rendered["prepared"]["baseRevision"], 0)

    def test_every_board_size_arrives_as_server_html_for_vue_to_hydrate(self) -> None:
        # The runner labels initial output and holds scripts from adapter.toml
        # alone. A hybrid adapter without hydration_min_count declares that
        # every initial page is server HTML, so each board size must hydrate
        # with Citry's default settings.
        declared = tomllib.loads((Path(__file__).with_name("adapter.toml")).read_text(encoding="utf-8"))["app"]
        self.assertEqual(declared["rendering"], "hybrid")
        self.assertNotIn("hydration_min_count", declared)
        client = Client()
        for count in (14, 140, 1400):
            page = client.get(f"/?session=hydration-{count}&count={count}")
            self.assertEqual(page.status_code, 200)
            self.assertIn(b'"hydrate":true', page.content, count)


if __name__ == "__main__":
    unittest.main()
