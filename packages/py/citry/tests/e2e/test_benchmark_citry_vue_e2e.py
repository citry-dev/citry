"""Browser proof for the Vue-only large benchmark fixture."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")


_FIXTURE_PATH = Path(__file__).parents[1] / "test_benchmark_citry.py"
_SPEC = importlib.util.spec_from_file_location("citry_benchmark_vue_fixture", _FIXTURE_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_FIXTURE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _FIXTURE
_SPEC.loader.exec_module(_FIXTURE)

pytestmark = pytest.mark.e2e


def test_large_benchmark_mounts_and_switches_server_rendered_tabs(page: Any, serve_live: Any) -> None:
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))

    # The page hydrates by default, and Vue marks only a client-mounted host
    # with data-v-app, so wait for Citry's own ready event instead.
    page.add_init_script(
        "window.__citryReady = false;document.addEventListener('citry:ready', () => { window.__citryReady = true; });"
    )
    page.goto(serve_live(_FIXTURE.app, _FIXTURE.render(_FIXTURE.gen_render_data()), "") + "/")
    page.wait_for_function("window.__citryReady === true")
    assert page_errors == []

    headers = page.locator("[data-tab-header]")
    panels = page.locator("[data-tab-panel]")
    assert headers.count() >= 2
    assert panels.count() >= 2
    assert panels.nth(0).is_visible()

    headers.nth(1).click()

    assert panels.nth(0).is_hidden()
    assert panels.nth(1).is_visible()

    bookmark_menu = page.locator("[data-benchmark-bookmark-menu]").first
    bookmark_menu.click()
    assert page.locator("[data-benchmark-bookmark-context]").count() == 1

    assert page_errors == []


def test_benchmark_attachment_rows_follow_parent_state(page: Any, serve_live: Any) -> None:
    attachments = [
        _FIXTURE.RenderedAttachment(url="/first", text="First", tags=["Tag 9"]),
        _FIXTURE.RenderedAttachment(url="/second", text="Second", tags=["Tag 10"]),
    ]

    class AttachmentHarness(_FIXTURE.Component):
        citry = _FIXTURE.app
        name = "BenchmarkAttachmentHarness"

        js = """
                $component({
                    methods: {
                        removeAttachment(index) { this.attachments.splice(index, 1); },
                    setAttachmentTags(index, tags) { this.attachments[index].tags = tags; },
                    updateAttachmentData(index, data) { Object.assign(this.attachments[index], data); },
                    toggleAttachment(index) {
                        this.attachments[index].isPreview = !this.attachments[index].isPreview;
                    },
                },
            });
        """

        def js_data(self, kwargs, slots):
            return {"attachments": [{**attachment._asdict(), "isPreview": True} for attachment in attachments]}

        def template_data(self, kwargs, slots):
            return {
                "attachments": attachments,
                "attachment_props": {
                    "attachments": "attachments",
                    "onRemoveAttachment": "removeAttachment",
                    "onSetAttachmentTags": "setAttachmentTags",
                    "onUpdateAttachmentData": "updateAttachmentData",
                    "onToggleAttachment": "toggleAttachment",
                },
            }

        template = """
            <main>
                    <c-ProjectOutputAttachments
                    c-has_attachments="True"
                    c-editable="True"
                    c-attachments="attachments"
                    c-js_props="attachment_props"
                    :attachments="attachments"
                    @remove-attachment="removeAttachment"
                    @set-attachment-tags="setAttachmentTags"
                    @update-attachment-data="updateAttachmentData"
                    @toggle-attachment="toggleAttachment" />
                <output id="attachment-state" v-text="JSON.stringify(attachments)"></output>
            </main>
        """

    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(serve_live(_FIXTURE.app, AttachmentHarness().render().serialize(), "") + "/")
    rows = page.locator("[data-benchmark-initial-attachment]")
    assert rows.count() == 2
    rows.nth(1).get_by_role("button", name="Edit").click()
    second_text = rows.nth(1).locator("input[name='text']")
    second_text.fill("Updated second")
    second_text.press("Tab")
    assert '"text":"Updated second"' in page.locator("#attachment-state").inner_text()
    rows.first.get_by_role("button", name="Remove").first.click()
    assert rows.count() == 1
    assert rows.first.locator("input[name='text']").input_value() == "Updated second"
    tag_select = rows.first.locator("[data-benchmark-tags] select")
    tag_select.select_option("Tag 11")
    assert '"tags":["Tag 11"]' in page.locator("#attachment-state").inner_text()
    assert page_errors == []


def test_benchmark_dialog_uses_controlled_native_model_and_escape(page: Any, serve_live: Any) -> None:
    class DialogHarness(_FIXTURE.Component):
        citry = _FIXTURE.app
        name = "BenchmarkDialogHarness"
        js = "$component({ data() { return { open: false }; } });"
        template = """
            <main>
                <button id="open-dialog" @click="open = true">Open</button>
                <c-Dialog :model_value="open" @update:model_value="open = $event">
                    <c-fill name="content"><p id="dialog-content">Controlled dialog</p></c-fill>
                </c-Dialog>
            </main>
        """

    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(serve_live(_FIXTURE.app, DialogHarness().render().serialize(), "") + "/")
    content = page.locator("#dialog-content")
    assert content.is_hidden()
    page.locator("#open-dialog").click()
    assert content.is_visible()
    page.keyboard.press("Escape")
    assert content.is_hidden()
    assert page_errors == []
