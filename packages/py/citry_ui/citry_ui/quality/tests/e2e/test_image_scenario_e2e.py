"""Public Image evidence through its reusable quality scenario."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest

pytest.importorskip("pytest_playwright")

from citry_ui.quality.routes import build_scenario, render_scenario

pytestmark = pytest.mark.e2e


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the Image quality test."
    raise RuntimeError(msg)


def _fixture_directory() -> Path:
    return _repository_root() / "docs_site" / "static" / "img" / "ui" / "image"


def _install_image_routes(page: Any, requests: list[dict[str, object]] | None = None) -> None:
    fixtures = _fixture_directory()
    files = {
        "horsehead-1280.jpg": ("image/jpeg", fixtures / "horsehead-nebula-1280.jpg"),
        "observatory-portrait-640.jpg": ("image/jpeg", fixtures / "observatory-portrait-640.jpg"),
        "observatory-1280.avif": ("image/avif", fixtures / "observatory-wide-1280.avif"),
        "observatory-1280.jpg": ("image/jpeg", fixtures / "observatory-wide-1280.jpg"),
        "orion-1280.jpg": ("image/jpeg", fixtures / "orion-nebula-1280.jpg"),
        "orion-640.jpg": ("image/jpeg", fixtures / "orion-nebula-640.jpg"),
    }

    def serve(route: Any) -> None:
        request = route.request
        if requests is not None:
            requests.append({"url": request.url, "headers": dict(request.headers)})
        name = Path(urlparse(request.url).path).name
        fixture = files.get(name)
        headers = {
            "access-control-allow-origin": "*",
            "cache-control": "public, max-age=3600",
        }
        if fixture is None:
            route.fulfill(status=200, content_type="image/png", body=b"not-an-image", headers=headers)
            return
        content_type, path = fixture
        route.fulfill(status=200, content_type=content_type, body=path.read_bytes(), headers=headers)

    page.route("https://images.citry.test/northstar/**", serve)
    page.route("https://cross-origin.citry.test/northstar/**", serve)
    page.route("https://blocked-images.citry.test/northstar/**", serve)


def _with_image_csp(html: str) -> str:
    policy = (
        '<meta http-equiv="Content-Security-Policy" '
        'content="img-src https://images.citry.test https://cross-origin.citry.test data: blob:">'
    )
    return html.replace("<head>", "<head>" + policy, 1)


def _wait_for_all_settled(page: Any) -> None:
    page.wait_for_function(
        """() => {
          const roots = [...document.querySelectorAll('[data-citry-ui-part="image-root"]')];
          return roots.length > 0
            && roots.every(root => root.hasAttribute('data-citry-image-initialized'))
            && roots.every(root => root.dataset.status === 'loaded' || root.dataset.status === 'error');
        }""",
        timeout=15_000,
    )


def _axe_serious_or_critical(page: Any) -> list[dict[str, object]]:
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` before the Image quality axe test"
    page.add_script_tag(path=str(axe_path))
    return page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter((finding) => ['serious','critical'].includes(finding.impact))"""
    )


def test_image_quality_native_semantics_delivery_reactivity_lifecycle_guards_and_axe(page: Any) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    requests: list[dict[str, object]] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    _install_image_routes(page, requests)
    page.set_content(render_scenario("image.states"), wait_until="load")
    page.locator("#quality-image-lazy").scroll_into_view_if_needed()
    _wait_for_all_settled(page)

    basic_image = page.locator('#quality-image-basic [data-citry-ui-part="image"]')
    assert basic_image.get_attribute("alt") == "Orion Nebula, captured from Northstar Ridge"
    assert basic_image.get_attribute("width") == "1280"
    assert basic_image.get_attribute("height") == "720"
    assert basic_image.get_attribute("loading") == "eager"
    assert basic_image.get_attribute("fetchpriority") == "high"
    assert page.locator("#quality-image-basic").get_attribute("role") is None

    lazy_image = page.locator('#quality-image-lazy [data-citry-ui-part="image"]')
    assert lazy_image.get_attribute("loading") == "lazy"
    assert lazy_image.get_attribute("decoding") == "async"
    assert lazy_image.get_attribute("fetchpriority") == "auto"

    decorative = page.locator('#quality-image-decorative [data-citry-ui-part="image"]')
    assert decorative.get_attribute("alt") == ""
    assert page.locator("#quality-image-decorative").get_attribute("aria-label") is None

    responsive = page.locator("#quality-image-responsive")
    assert responsive.locator(":scope > picture > source").count() == 2
    assert responsive.locator(":scope > picture > img:last-child").count() == 1
    selected = responsive.locator("img").evaluate("image => new URL(image.currentSrc).pathname.split('/').pop()")
    assert selected in {
        "observatory-portrait-640.jpg",
        "observatory-1280.avif",
        "observatory-1280.jpg",
    }

    error = page.locator("#quality-image-error")
    assert error.get_attribute("data-status") == "error"
    assert error.locator('[data-citry-ui-part="placeholder"]').is_hidden()
    assert error.locator('[data-citry-ui-part="fallback"]').is_visible()
    assert error.locator('[data-citry-ui-part="fallback"]').get_attribute("aria-hidden") == "true"
    assert error.locator('[data-citry-ui-part="fallback"]').get_attribute("inert") == ""
    assert error.locator("img").get_attribute("aria-hidden") is None
    assert error.locator("img").get_attribute("alt") == "Unavailable Northstar archive plate"

    delivery_image = page.locator('#quality-image-delivery [data-citry-ui-part="image"]')
    assert delivery_image.get_attribute("crossorigin") == "anonymous"
    assert delivery_image.get_attribute("referrerpolicy") == "no-referrer"
    cross_request = next(
        request for request in requests if str(request["url"]).startswith("https://cross-origin.citry.test/")
    )
    assert dict(cross_request["headers"]).get("referer", "") == ""
    functional_link = page.get_by_role("link", name="Open the full Horsehead Nebula observation")
    functional_link.focus()
    assert functional_link.evaluate("element => element === document.activeElement") is True

    page.get_by_role("button", name="Broken", exact=True).click()
    page.wait_for_function("document.querySelector('#quality-image-reactive').dataset.status === 'error'")
    page.get_by_role("button", name="Rapid A then B", exact=True).click()
    page.wait_for_function(
        """() => document.querySelector('#quality-image-reactive').dataset.status === 'loaded'
          && document.querySelector('#quality-image-reactive-output').textContent
            .includes('orion-640.jpg')"""
    )
    reactive_output = page.locator("#quality-image-reactive-output").text_content()
    assert "https://" not in reactive_output
    assert "citry.test" not in reactive_output
    status, selected_name, callbacks, native_loads, native_errors = reactive_output.split("|")
    assert status == "loaded"
    assert selected_name == "orion-640.jpg"
    assert int(callbacks) >= 4
    assert int(native_loads) >= 2
    assert int(native_errors) >= 1

    assert _axe_serious_or_critical(page) == []

    page.evaluate(
        """() => {
          const root = document.querySelector('#quality-image-basic');
          const host = document.querySelector('#quality-image-shadow-host');
          host.attachShadow({mode:'open'}).append(root);
        }"""
    )
    page.wait_for_function(
        """() => document.querySelector('#quality-image-shadow-host').shadowRoot
          .querySelector('#quality-image-basic').hasAttribute('data-citry-image-initialized')"""
    )
    page.evaluate(
        """() => {
          const host = document.querySelector('#quality-image-shadow-host');
          host.before(host.shadowRoot.querySelector('#quality-image-basic'));
        }"""
    )
    page.wait_for_selector("#quality-image-basic[data-citry-image-initialized]")

    page.evaluate(
        """() => {
          const clone = document.querySelector('#quality-image-lifecycle').cloneNode(true);
          clone.id = 'quality-image-unowned-clone';
          document.querySelector('.image-quality').append(clone);
        }"""
    )
    page.wait_for_function(
        "!document.querySelector('#quality-image-unowned-clone').hasAttribute('data-citry-image-initialized')"
    )
    assert page.locator("#quality-image-unowned-clone").get_attribute("data-status") is None
    assert console_errors == []
    assert page_errors == []

    fit = page.locator("#quality-image-fit")
    fit.evaluate("element => element.setAttribute('data-status', 'forged')")
    page.wait_for_function(
        "!document.querySelector('#quality-image-fit').hasAttribute('data-citry-image-initialized')"
    )
    assert fit.get_attribute("data-status") is None
    assert len(console_errors) == 1
    assert console_errors[0].startswith("[citry-ui] CImage lost its owned native anatomy")
    assert "http" not in console_errors[0]
    assert page_errors == []


def test_image_quality_csp_remains_browser_owned_and_shows_the_visual_fallback(page: Any) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    requests: list[dict[str, object]] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    _install_image_routes(page, requests)

    page.set_content(_with_image_csp(render_scenario("image.states")), wait_until="load")
    page.locator("#quality-image-lazy").scroll_into_view_if_needed()
    _wait_for_all_settled(page)

    assert not any(str(request["url"]).startswith("https://blocked-images.citry.test/") for request in requests)
    csp_blocked = page.locator("#quality-image-csp")
    assert csp_blocked.get_attribute("data-status") == "error"
    assert csp_blocked.locator('[data-citry-ui-part="fallback"]').is_visible()
    assert all(
        "content security" in message.casefold() or "blocked-images.citry.test" in message
        for message in console_errors
    )
    assert page_errors == []


def test_image_signed_retained_resource_replacement_and_two_restore_cycles(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    _install_image_routes(page)

    rendered = build_scenario(
        "image.states",
        configure_app=lambda app: app.set_mounted_prefix("/citry"),
    )
    base_url = serve_citry_ui_live(rendered.app, rendered.html)
    page.goto(base_url + "/", wait_until="load")
    page.locator("#quality-image-lazy").scroll_into_view_if_needed()
    _wait_for_all_settled(page)
    expected_roots = page.locator('[data-citry-ui-part="image-root"]').count()
    page.evaluate(
        """() => {
          const root = document.querySelector('#quality-image-lifecycle');
          window.__imageLifecycle = {
            root,
            image: root.querySelector('[data-citry-ui-part="image"]'),
            current: root.querySelector('[data-citry-ui-part="image"]').currentSrc,
          };
        }"""
    )
    callback_baseline = int(page.locator("#quality-image-lifecycle-output").text_content().split("|")[-1])

    def refresh(step: int, roots: int) -> None:
        page.evaluate(
            """() => void Citry.events.send(
              document.querySelector('.image-quality'),
              'refresh',
              {},
            )"""
        )
        page.wait_for_function(
            "step => Number(document.querySelector('[data-quality-morph-step]')?.textContent) === step",
            arg=step,
            timeout=10_000,
        )
        page.wait_for_function(
            """roots => {
              const all = [...document.querySelectorAll('[data-citry-ui-part="image-root"]')];
              const ready = all.filter(root => root.hasAttribute('data-citry-image-initialized'));
              return all.length === roots && ready.length === roots;
            }""",
            arg=roots,
            timeout=10_000,
        )
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")

    refresh(1, expected_roots)
    page.wait_for_function("document.querySelector('#quality-image-lifecycle').dataset.status === 'loaded'")
    retained = page.evaluate(
        """() => {
          const prior = window.__imageLifecycle;
          const root = document.querySelector('#quality-image-lifecycle');
          const image = root.querySelector('[data-citry-ui-part="image"]');
          return {
            root: root === prior.root,
            image: image === prior.image,
            current: image.currentSrc === prior.current,
          };
        }"""
    )
    assert retained == {"root": True, "image": True, "current": True}
    assert int(page.locator("#quality-image-lifecycle-output").text_content().split("|")[-1]) == callback_baseline

    refresh(2, expected_roots)
    page.wait_for_function(
        """() => {
          const root = document.querySelector('#quality-image-lifecycle');
          const image = root?.querySelector('[data-citry-ui-part="image"]');
          return root?.dataset.status === 'loaded' && image?.currentSrc.includes('orion-1280.jpg');
        }"""
    )
    resource_changed = page.evaluate(
        """() => {
          const prior = window.__imageLifecycle;
          const root = document.querySelector('#quality-image-lifecycle');
          return {
            root: root === prior.root,
            image: root.querySelector('[data-citry-ui-part="image"]') === prior.image,
          };
        }"""
    )
    assert resource_changed == {"root": True, "image": True}

    refresh(3, expected_roots)
    page.wait_for_function("document.querySelector('#quality-image-lifecycle').dataset.status === 'loaded'")
    replaced = page.evaluate(
        """() => {
          const prior = window.__imageLifecycle;
          const root = document.querySelector('#quality-image-lifecycle');
          window.__imageReplacement = root;
          return {
            rootChanged: root !== prior.root,
            imageChanged: root.querySelector('[data-citry-ui-part="image"]') !== prior.image,
            oldConnected: prior.root.isConnected,
            oldReady: prior.root.hasAttribute('data-citry-image-initialized'),
          };
        }"""
    )
    assert replaced == {
        "rootChanged": True,
        "imageChanged": True,
        "oldConnected": False,
        "oldReady": False,
    }

    refresh(4, expected_roots - 1)
    assert page.locator("#quality-image-lifecycle").count() == 0

    refresh(5, expected_roots)
    page.wait_for_function("document.querySelector('#quality-image-lifecycle').dataset.status === 'loaded'")
    assert page.evaluate("document.querySelector('#quality-image-lifecycle') !== window.__imageReplacement") is True

    refresh(6, expected_roots - 1)
    assert page.locator("#quality-image-lifecycle").count() == 0

    refresh(7, expected_roots)
    page.wait_for_function("document.querySelector('#quality-image-lifecycle').dataset.status === 'loaded'")
    assert console_errors == []
    assert page_errors == []


def test_image_quality_no_javascript_keeps_native_alt_geometry_and_sources(browser: Any) -> None:
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    try:
        _install_image_routes(page)
        page.set_content(render_scenario("image.states"), wait_until="load")
        basic = page.locator('#quality-image-basic [data-citry-ui-part="image"]')
        assert basic.get_attribute("alt") == "Orion Nebula, captured from Northstar Ridge"
        assert basic.get_attribute("width") == "1280"
        assert basic.get_attribute("height") == "720"
        assert page.locator("#quality-image-responsive picture > source").count() == 2
        assert page.locator("#quality-image-responsive picture > img:last-child").count() == 1
        assert page.locator('#quality-image-error [data-citry-ui-part="fallback"]').is_hidden()
        assert page.locator('#quality-image-error [data-citry-ui-part="image"]').get_attribute("alt") == (
            "Unavailable Northstar archive plate"
        )
        assert page.locator("[data-citry-image-initialized]").count() == 0
    finally:
        context.close()
