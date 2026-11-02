"""Browser evidence that Image examples show what `onStatusChange` reports."""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest

pytest.importorskip("pytest_playwright")

from playwright.sync_api import expect

from citry import Component
from citry import citry as default_citry

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root for Image browser tests.")


_FIXTURES = _root() / "docs_site" / "static" / "img" / "ui" / "image"


class ImagePreviewDocument(Component):
    citry = default_citry

    class Kwargs:
        title: str
        content: object

    class Slots:
        pass

    template = """
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>{{ title }}</title>
          <c-css />
        </head>
        <body>
          <main>{{ content }}</main>
          <c-js />
        </body>
      </html>
    """

    def template_data(self, kwargs: Kwargs, _slots: Slots) -> dict[str, object]:
        return {"title": kwargs.title, "content": kwargs.content}


def _serve_fixture_images(page: Any) -> None:
    # The examples load docs-site image paths, which the test server does not
    # serve, so the browser gets the same files from the docs static folder.
    # An unknown name answers 404, which is how the "Broken" frame fails.
    def serve(route: Any) -> None:
        path = _FIXTURES / Path(urlparse(route.request.url).path).name
        if not path.is_file():
            route.fulfill(status=404, body=b"")
            return
        content_type = "image/avif" if path.suffix == ".avif" else "image/jpeg"
        route.fulfill(status=200, content_type=content_type, body=path.read_bytes())

    page.route("**/static/img/ui/image/**", serve)


def _open_example(page: Any, serve_citry_ui_live: Any, name: str) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    _serve_fixture_images(page)
    # Each test renders the shipped example module directly, so it does not
    # depend on where the docs page places that example.
    module = importlib.import_module(f"citry_ui.components.cimage.snippets.{name}")
    html = ImagePreviewDocument(title=name, content=module.preview).render().serialize()
    base = serve_citry_ui_live(default_citry, html)
    page.goto(base + "/", wait_until="networkidle")
    page.wait_for_selector("[data-citry-image-initialized]")
    return errors


def _reactive_counts(page: Any) -> dict[str, object]:
    # The example writes one sentence; split it back into the values its
    # status handler set.
    text = " ".join(page.locator(".image-reactive output").text_content().split())
    match = re.fullmatch(
        r"Status (\w+); selected (\S+); callbacks (\d+); native load/error (\d+)/(\d+)",
        text,
    )
    assert match is not None, text
    status, selected, callbacks, loads, errors = match.groups()
    return {
        "status": status,
        "selected": selected,
        "callbacks": int(callbacks),
        "loads": int(loads),
        "errors": int(errors),
    }


def test_reactive_image_example_counts_and_redacts_each_status_change(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "reactive_image")
    page.wait_for_function("document.querySelector('.image-reactive output').textContent.includes('Status loaded')")
    before = _reactive_counts(page)
    assert before["selected"] == "horsehead-nebula-1280.jpg"

    page.get_by_role("button", name="Frame B", exact=True).click()
    page.wait_for_function(
        """() => {
          const text = document.querySelector('.image-reactive output').textContent;
          return text.includes('Status loaded') && text.includes('orion-nebula-1280.jpg');
        }"""
    )
    frame_b = _reactive_counts(page)
    assert frame_b["callbacks"] > before["callbacks"]
    assert frame_b["loads"] == before["loads"] + 1
    assert frame_b["errors"] == before["errors"]

    page.get_by_role("button", name="Broken", exact=True).click()
    page.wait_for_function("document.querySelector('.image-reactive output').textContent.includes('Status error')")
    broken = _reactive_counts(page)
    # The output shows the filename only, never the path or the query.
    assert broken["selected"] == "missing-live-frame.jpg"
    assert broken["callbacks"] > frame_b["callbacks"]
    assert broken["loads"] == frame_b["loads"]
    assert broken["errors"] == frame_b["errors"] + 1
    # The broken frame is a deliberate 404; nothing else may log an error.
    assert [error for error in errors if "404" not in error] == []


def test_image_lifecycle_example_shows_status_and_filename_for_each_resource(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "image_lifecycle")
    output = page.locator(".image-lifecycle > output")
    expect(output).to_have_text("Status loaded; selected horsehead-nebula-1280.jpg")

    # The server sends a new source, and the handler shows the new filename
    # without the `?plate=` query.
    page.get_by_role("button", name="Change the resource").click()
    expect(output).to_have_text("Status loaded; selected orion-nebula-1280.jpg")
    assert errors == []


def test_responsive_sources_example_shows_the_candidate_the_browser_chose(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    page.set_viewport_size({"width": 1280, "height": 900})
    errors = _open_example(page, serve_citry_ui_live, "responsive_sources")
    output = page.locator(".image-responsive output")
    expect(output).to_have_text("Selected local fixture: observatory-wide-1280.avif")

    # Below 48rem the portrait source matches, and the browser reports the
    # new candidate through the same handler.
    page.set_viewport_size({"width": 400, "height": 900})
    expect(output).to_have_text("Selected local fixture: observatory-portrait-640.jpg")
    assert errors == []


_QUALITY_FILES = {
    "horsehead-1280.jpg": "horsehead-nebula-1280.jpg",
    "observatory-portrait-640.jpg": "observatory-portrait-640.jpg",
    "observatory-1280.avif": "observatory-wide-1280.avif",
    "observatory-1280.jpg": "observatory-wide-1280.jpg",
    "orion-1280.jpg": "orion-nebula-1280.jpg",
    "orion-640.jpg": "orion-nebula-640.jpg",
}


def _serve_quality_images(page: Any) -> None:
    # The quality scenario names remote hosts, so the browser gets local
    # fixture files instead; an unknown name fails as a broken image.
    def serve(route: Any) -> None:
        name = _QUALITY_FILES.get(Path(urlparse(route.request.url).path).name)
        headers = {"access-control-allow-origin": "*"}
        if name is None:
            route.fulfill(status=200, content_type="image/png", body=b"not-an-image", headers=headers)
            return
        content_type = "image/avif" if name.endswith(".avif") else "image/jpeg"
        route.fulfill(status=200, content_type=content_type, body=(_FIXTURES / name).read_bytes(), headers=headers)

    for host in ("images", "cross-origin", "blocked-images"):
        page.route(f"https://{host}.citry.test/northstar/**", serve)


def test_image_quality_lifecycle_handler_runs_only_when_the_image_changes(page: Any, open_scenario: Any) -> None:
    _serve_quality_images(page)
    open_scenario("image.states")
    lifecycle = page.locator("#quality-image-lifecycle")
    output = page.locator("#quality-image-lifecycle-output")
    lifecycle.scroll_into_view_if_needed()
    page.wait_for_function("document.querySelector('#quality-image-lifecycle').dataset.status === 'loaded'")
    expect(output).to_contain_text("loaded|")
    baseline = int(output.text_content().split("|")[-1])
    advance = page.get_by_role("button", name="Advance signed image lifecycle")

    # Step 1 re-renders the same image, so the handler must not run again.
    advance.click()
    expect(page.locator("[data-quality-morph-step]")).to_have_text("1")
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
    assert output.text_content().split() == [f"loaded|{baseline}"]

    # Step 2 changes the resource, so the new load reaches the handler.
    advance.click()
    expect(page.locator("[data-quality-morph-step]")).to_have_text("2")
    page.wait_for_function(
        """baseline => {
          const [status, count] = document.querySelector('#quality-image-lifecycle-output')
            .textContent.trim().split('|');
          return status === 'loaded' && Number(count) > baseline;
        }""",
        arg=baseline,
    )
