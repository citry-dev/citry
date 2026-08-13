"""Focused browser contracts for CImage."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cimage import CImage

pytestmark = pytest.mark.e2e

GREEN = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='40'%3E"
    "%3Crect width='80' height='40' fill='%23059669'/%3E%3C/svg%3E"
)
BLUE = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='30'%3E"
    "%3Crect width='60' height='30' fill='%232563eb'/%3E%3C/svg%3E"
)
GREEN_WIDE = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='90'%3E"
    "%3Crect width='160' height='90' fill='%23059669'/%3E%3C/svg%3E"
)
ZERO = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='0' height='0'%3E%3C/svg%3E"
SMALL_URL = "https://images.test/small.svg"
WIDE_URL = "https://images.test/wide.svg"


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-image-e2e", (CImage,)))
    return app


def _page() -> str:
    app = _app()

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <style>
                body { margin: 0; padding: 2rem; }
                .narrow { inline-size: 200px; }
              </style>
              <c-css />
            </head>
            <body
              x-data
              x-init="Alpine.store('imageTest', {
                source: document.querySelector('#basic-image').getAttribute('src'),
                alt: 'Reactive plate',
                height: 40,
                fit: 'contain',
                events: [],
                callbackEvents: [],
                callback: detail => {
                  const store = Alpine.store('imageTest');
                  store.callbackEvents.push(detail.status);
                  store.events.push({
                    status: detail.status,
                    src: detail.src,
                    current: detail.current_src,
                    width: detail.natural_width,
                    height: detail.natural_height
                  });
                }
              })"
            >
              <c-CImage
                c-src="green"
                alt="Green plate"
                c-width="80"
                c-height="40"
                c-attrs="{'id': 'basic'}"
                c-img_attrs="{'id': 'basic-image'}"
                $c-props="{
                  onStatusChange: detail => $store.imageTest.events.push({
                    status: detail.status,
                    src: detail.src,
                    current: detail.current_src,
                    width: detail.natural_width,
                    height: detail.natural_height
                  })
                }"
              >
                <c-fill name="placeholder">Loading</c-fill>
                <c-fill name="fallback">Unavailable</c-fill>
              </c-CImage>

              <c-CImage
                src="data:image/png;base64,AAAA"
                alt="Missing plate"
                c-width="80"
                c-height="40"
                c-attrs="{'id': 'missing'}"
              >
                <c-fill name="fallback">Missing fallback</c-fill>
              </c-CImage>

              <div class="narrow">
                <c-CImage
                  c-src="green_wide"
                  alt="Narrow plate"
                  c-width="1280"
                  c-height="720"
                  c-attrs="{'id': 'geometry'}"
                />
              </div>

              <c-CImage
                c-src="green"
                alt="Reactive plate"
                c-width="80"
                c-height="40"
                c-attrs="{'id': 'reactive'}"
                $c-props="{
                  src: $store.imageTest.source,
                  alt: $store.imageTest.alt,
                  height: $store.imageTest.height,
                  fit: $store.imageTest.fit,
                  onStatusChange: $store.imageTest.callback
                }"
              />
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {"green": GREEN, "green_wide": GREEN_WIDE}

    return str(Page())


def _zero_page() -> str:
    app = _app()

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /></head>
            <body x-data="{ events: [] }">
              <script>
                window.__imageDecodeCalls = 0;
                const nativeDecode = HTMLImageElement.prototype.decode;
                const nativeComplete = Object.getOwnPropertyDescriptor(
                  HTMLImageElement.prototype, 'complete'
                );
                const nativeCurrentSrc = Object.getOwnPropertyDescriptor(
                  HTMLImageElement.prototype, 'currentSrc'
                );
                const nativeNaturalWidth = Object.getOwnPropertyDescriptor(
                  HTMLImageElement.prototype, 'naturalWidth'
                );
                const nativeAddEventListener = HTMLImageElement.prototype.addEventListener;
                const isZeroProbe = image => image.alt === 'Zero dimension vector';
                Object.defineProperty(HTMLImageElement.prototype, 'complete', {
                  configurable: true,
                  get() {
                    if (isZeroProbe(this)) return true;
                    return nativeComplete.get.call(this);
                  }
                });
                Object.defineProperty(HTMLImageElement.prototype, 'currentSrc', {
                  configurable: true,
                  get() {
                    if (isZeroProbe(this)) return this.src;
                    return nativeCurrentSrc.get.call(this);
                  }
                });
                Object.defineProperty(HTMLImageElement.prototype, 'naturalWidth', {
                  configurable: true,
                  get() {
                    if (isZeroProbe(this)) return 0;
                    return nativeNaturalWidth.get.call(this);
                  }
                });
                HTMLImageElement.prototype.addEventListener = function (type, listener, options) {
                  if (type === 'load' && isZeroProbe(this)) return;
                  return nativeAddEventListener.call(this, type, listener, options);
                };
                HTMLImageElement.prototype.decode = function () {
                  window.__imageDecodeCalls += 1;
                  return nativeDecode.call(this);
                };
              </script>
              <c-CImage
                c-src="zero"
                alt="Zero dimension vector"
                c-width="20"
                c-height="10"
                c-attrs="{'id': 'zero'}"
                $c-props="{ onStatusChange: detail => events.push(detail.status) }"
              />
              <output id="zero-events" x-text="JSON.stringify(events)"></output>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {"zero": ZERO}

    return str(Page())


def _decode_race_page() -> str:
    app = _app()

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /></head>
            <body
              x-data
              x-init="Alpine.store('imageDecode', {
                source: document.querySelector('#decode-race img').getAttribute('src'),
                race: [], broken: []
              })"
            >
              <script>
                window.__decodeCalls = {race: 0, broken: 0};
                const nativeComplete = Object.getOwnPropertyDescriptor(
                  HTMLImageElement.prototype, 'complete'
                );
                const nativeCurrentSrc = Object.getOwnPropertyDescriptor(
                  HTMLImageElement.prototype, 'currentSrc'
                );
                const nativeNaturalWidth = Object.getOwnPropertyDescriptor(
                  HTMLImageElement.prototype, 'naturalWidth'
                );
                const nativeAddEventListener = HTMLImageElement.prototype.addEventListener;
                const isProbe = image => image.alt.endsWith('decode probe');
                Object.defineProperty(HTMLImageElement.prototype, 'complete', {
                  configurable: true,
                  get() { return isProbe(this) ? true : nativeComplete.get.call(this); }
                });
                Object.defineProperty(HTMLImageElement.prototype, 'currentSrc', {
                  configurable: true,
                  get() { return isProbe(this) ? this.src : nativeCurrentSrc.get.call(this); }
                });
                Object.defineProperty(HTMLImageElement.prototype, 'naturalWidth', {
                  configurable: true,
                  get() { return isProbe(this) ? 0 : nativeNaturalWidth.get.call(this); }
                });
                HTMLImageElement.prototype.addEventListener = function (type, listener, options) {
                  if (isProbe(this) && (type === 'load' || type === 'error')) return;
                  return nativeAddEventListener.call(this, type, listener, options);
                };
                HTMLImageElement.prototype.decode = function () {
                  if (this.alt === 'Broken decode probe') {
                    window.__decodeCalls.broken += 1;
                    return Promise.reject(new DOMException('fixture rejection'));
                  }
                  if (this.alt === 'Race decode probe') {
                    window.__decodeCalls.race += 1;
                    if (window.__decodeCalls.race === 1) return new Promise((resolve, reject) => {
                      window.__rejectOldDecode = reject;
                    });
                    return Promise.resolve();
                  }
                  return Promise.resolve();
                };
              </script>
              <c-CImage
                c-src="green"
                alt="Race decode probe"
                c-width="20"
                c-height="10"
                c-attrs="{'id': 'decode-race'}"
                $c-props="{
                  src: $store.imageDecode.source,
                  onStatusChange: detail => $store.imageDecode.race.push(detail.status)
                }"
              />
              <c-CImage
                src="data:image/png;base64,AAAA"
                alt="Broken decode probe"
                c-width="20"
                c-height="10"
                c-attrs="{'id': 'decode-broken'}"
                $c-props="{
                  onStatusChange: detail => $store.imageDecode.broken.push(detail.status)
                }"
              />
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {"green": GREEN}

    return str(Page())


def _invalid_decode_page(mode: str) -> str:
    app = _app()

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /></head>
            <body x-data="{ events: [] }">
              <script>
                const nativeComplete = Object.getOwnPropertyDescriptor(
                  HTMLImageElement.prototype, 'complete'
                );
                const nativeCurrentSrc = Object.getOwnPropertyDescriptor(
                  HTMLImageElement.prototype, 'currentSrc'
                );
                const nativeNaturalWidth = Object.getOwnPropertyDescriptor(
                  HTMLImageElement.prototype, 'naturalWidth'
                );
                Object.defineProperty(HTMLImageElement.prototype, 'complete', {
                  configurable: true, get() { return this.alt === 'Invalid decode probe'
                    ? true : nativeComplete.get.call(this); }
                });
                Object.defineProperty(HTMLImageElement.prototype, 'currentSrc', {
                  configurable: true, get() { return this.alt === 'Invalid decode probe'
                    ? this.src : nativeCurrentSrc.get.call(this); }
                });
                Object.defineProperty(HTMLImageElement.prototype, 'naturalWidth', {
                  configurable: true, get() { return this.alt === 'Invalid decode probe'
                    ? 0 : nativeNaturalWidth.get.call(this); }
                });
                HTMLImageElement.prototype.decode = function () {
                  if (this.alt !== 'Invalid decode probe') return Promise.resolve();
                  if (MODE === 'undefined') return undefined;
                  if (MODE === 'plain') return {};
                  if (MODE === 'getter') return Object.defineProperty({}, 'then', {
                    get() { throw new DOMException('fixture getter'); }
                  });
                  return { then() { throw new DOMException('fixture then'); } };
                };
              </script>
              <c-CImage
                c-src="zero"
                alt="Invalid decode probe"
                c-width="20"
                c-height="10"
                c-attrs="{'id': 'invalid-decode'}"
                $c-props="{onStatusChange: detail => events.push(detail.status)}"
              />
              <c-js />
            </body>
          </html>
        """.replace("MODE", repr(mode))

        def template_data(self, kwargs, slots):
            return {"zero": ZERO}

    return str(Page())


def _responsive_page(*, small_url: str = SMALL_URL) -> str:
    app = _app()

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /></head>
            <body x-data="{ events: [] }">
              <c-CImage
                c-src="wide"
                alt="Responsive plate"
                c-width="60"
                c-height="30"
                c-sources="sources"
                c-attrs="{'id': 'responsive'}"
                $c-props="{
                  onStatusChange: detail => events.push({
                    status: detail.status,
                    current: detail.current_src
                  })
                }"
              />
              <output id="responsive-events" x-text="JSON.stringify(events)"></output>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            from citry_ui.components.cimage import CImageSource

            return {
                "wide": WIDE_URL,
                "sources": (CImageSource(small_url, media="(max-width: 600px)", width=80, height=40),),
            }

    return str(Page())


def _auto_sizes_page() -> str:
    app = _app()

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /></head>
            <body x-data="{ imageLoading: 'lazy', imageSizes: 'auto, 100vw' }">
              <c-CImage
                c-src="wide"
                c-srcset="wide_set"
                sizes="auto, 100vw"
                alt="Auto sizes plate"
                c-width="80"
                c-height="40"
                loading="lazy"
                c-sources="sources"
                c-attrs="{'id': 'auto-sizes'}"
                $c-props="{loading: imageLoading, sizes: imageSizes}"
              />
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            from citry_ui.components.cimage import CImageSource

            return {
                "wide": WIDE_URL,
                "wide_set": f"{WIDE_URL} 80w",
                "sources": (
                    CImageSource(
                        f"{SMALL_URL} 80w",
                        media="(max-width: 600px)",
                        sizes="auto, 100vw",
                        width=80,
                        height=40,
                    ),
                ),
            }

    return str(Page())


def _events_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-image-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(ComponentLibrary("citry-ui-image-events-e2e", (CImage,)))

    class EventsImage(Component):
        citry = app

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return EventsImage(step=state.step)

        template = """
          <section data-events-image>
            <button class="advance-image" type="button" @c-click="advance">Advance</button>
            <output id="image-step">{{ step }}</output>
            <c-CImage
              #c-key="'events-image'"
              c-src="image_src"
              c-alt="image_alt"
              c-width="80"
              c-height="40"
              c-sources="sources"
              c-attrs="{'id': 'events-image'}"
              $c-props="{
                onStatusChange: detail => $store.imageMorph.events.push({
                  status: detail.status,
                  current: detail.current_src,
                })
              }"
            />
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            from citry_ui.components.cimage import CImageSource

            return {
                "step": kwargs.step,
                "image_src": GREEN if kwargs.step < 2 else BLUE,
                "image_alt": f"Morph plate {kwargs.step}",
                "sources": () if kwargs.step < 3 else (CImageSource(GREEN, type="image/svg+xml"),),
            }

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body x-data x-init="Alpine.store('imageMorph', {events: []})">
              <c-events-image />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def test_basic_cached_error_slots_geometry_and_native_semantics(page: Any) -> None:
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#basic[data-citry-image-initialized]")
    page.wait_for_function("document.querySelector('#basic').dataset.status === 'loaded'")
    page.wait_for_function("document.querySelector('#missing').dataset.status === 'error'")

    assert page.locator("#basic-image").get_attribute("alt") == "Green plate"
    assert page.locator("#basic").get_attribute("role") is None
    assert page.locator("#basic [data-citry-ui-part='placeholder']").is_hidden()
    assert page.locator("#basic [data-citry-ui-part='fallback']").is_hidden()
    assert page.locator("#missing [data-citry-ui-part='fallback']").is_visible()
    assert page.locator("#missing [data-citry-ui-part='image']").get_attribute("aria-hidden") is None
    box = page.locator("#geometry [data-citry-ui-part='image']").bounding_box()
    assert box is not None
    assert box["width"] == pytest.approx(200, abs=0.5)
    assert box["height"] == pytest.approx(112.5, abs=0.5)
    statuses = page.evaluate("Alpine.store('imageTest').events.map(event => event.status)")
    assert statuses.count("loading") == 2
    assert statuses.count("loaded") == 2


def test_reactive_request_generation_and_non_request_changes(page: Any) -> None:
    page.set_content(_page(), wait_until="load")
    page.wait_for_function("document.querySelector('#reactive').dataset.status === 'loaded'")
    baseline = page.evaluate("Alpine.store('imageTest').events.length")

    page.evaluate("Object.assign(Alpine.store('imageTest'), {alt: 'Updated plate', height: 60, fit: 'cover'})")
    page.wait_for_timeout(50)
    assert page.evaluate("Alpine.store('imageTest').events.length") == baseline
    assert page.locator("#reactive [data-citry-ui-part='image']").get_attribute("alt") == "Updated plate"
    assert page.locator("#reactive").get_attribute("data-fit") == "cover"

    page.evaluate("Alpine.store('imageTest').source = '/broken-reactive.png'")
    page.wait_for_function("document.querySelector('#reactive').dataset.status === 'error'")
    page.evaluate(f"Alpine.store('imageTest').source = {BLUE!r}")
    page.wait_for_function("document.querySelector('#reactive').dataset.status === 'loaded'")
    assert page.evaluate("Alpine.store('imageTest').events.slice(-4).map(event => event.status)") == [
        "loading",
        "error",
        "loading",
        "loaded",
    ]


def test_cached_valid_zero_dimension_image_uses_decode_probe(page: Any) -> None:
    page.set_content(_zero_page(), wait_until="load")
    page.wait_for_function("document.querySelector('#zero').hasAttribute('data-citry-image-initialized')")
    page.wait_for_function("document.querySelector('#zero').dataset.status === 'loaded'")
    assert page.evaluate("window.__imageDecodeCalls") == 1
    assert page.evaluate("JSON.parse(document.querySelector('#zero-events').textContent)") == ["loading", "loaded"]


def test_cached_decode_rejection_and_superseded_probe_are_generation_guarded(page: Any) -> None:
    page.set_content(_decode_race_page(), wait_until="load")
    page.wait_for_function("window.__decodeCalls.race === 1 && window.__decodeCalls.broken === 1")
    page.wait_for_function("document.querySelector('#decode-broken').dataset.status === 'error'")
    assert page.evaluate("Alpine.store('imageDecode').broken") == ["loading", "error"]

    page.evaluate(f"Alpine.store('imageDecode').source = {BLUE!r}")
    page.wait_for_function("window.__decodeCalls.race === 2")
    page.wait_for_function("document.querySelector('#decode-race').dataset.status === 'loaded'")
    page.evaluate("window.__rejectOldDecode(new DOMException('superseded fixture rejection'))")
    page.wait_for_timeout(50)
    assert page.evaluate("Alpine.store('imageDecode').race") == ["loading", "loading", "loaded"]
    assert page.locator("#decode-race").get_attribute("data-status") == "loaded"


@pytest.mark.parametrize("mode", ["undefined", "plain", "getter", "then"])
def test_invalid_decode_capability_fails_closed_without_pageerror(page: Any, mode: str) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_invalid_decode_page(mode), wait_until="load")
    page.wait_for_function("!document.querySelector('#invalid-decode').hasAttribute('data-citry-image-initialized')")
    assert page.locator("#invalid-decode").get_attribute("data-status") is None
    assert (
        page.evaluate("Boolean(document.querySelector('#invalid-decode')[Symbol.for('citry-ui:image-owner')])")
        is False
    )
    assert errors == []


def test_picture_media_change_notifies_without_new_loading_episode(page: Any) -> None:
    def serve_image(route: Any) -> None:
        color = "#059669" if route.request.url == SMALL_URL else "#2563eb"
        route.fulfill(
            status=200,
            content_type="image/svg+xml",
            body=(
                '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40">'
                f'<rect width="80" height="40" fill="{color}"/></svg>'
            ),
        )

    page.route("https://images.test/*.svg", serve_image)
    page.set_viewport_size({"width": 1000, "height": 700})
    page.set_content(_responsive_page(), wait_until="load")
    page.wait_for_function("document.querySelector('#responsive').dataset.status === 'loaded'")
    before = page.locator("#responsive [data-citry-ui-part='image']").evaluate("image => image.currentSrc")
    page.set_viewport_size({"width": 500, "height": 700})
    page.wait_for_function(
        "previous => document.querySelector('#responsive [data-citry-ui-part=\"image\"]').currentSrc !== previous",
        arg=before,
    )
    page.wait_for_timeout(50)
    events = page.evaluate("JSON.parse(document.querySelector('#responsive-events').textContent)")
    assert [event["status"] for event in events] == ["loading", "loaded", "loaded"]
    assert events[-1]["current"] != events[-2]["current"]


def test_reactive_auto_sizes_tuple_retains_last_valid_configuration_atomically(page: Any) -> None:
    page.route(
        "https://images.test/*.svg",
        lambda route: route.fulfill(
            status=200,
            content_type="image/svg+xml",
            body='<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40"/>',
        ),
    )
    page.set_content(_auto_sizes_page(), wait_until="load")
    page.wait_for_selector("#auto-sizes[data-citry-image-initialized]")
    image = page.locator("#auto-sizes img")
    source = page.locator("#auto-sizes source")

    page.evaluate("Alpine.$data(document.body).imageLoading = 'eager'")
    page.wait_for_timeout(50)
    assert image.get_attribute("loading") == "lazy"
    assert image.get_attribute("sizes") == "auto, 100vw"
    assert source.get_attribute("sizes") == "auto, 100vw"

    page.evaluate("Alpine.$data(document.body).imageLoading = 'lazy'")
    page.evaluate("Alpine.$data(document.body).imageSizes = '100vw'")
    page.wait_for_timeout(50)
    assert image.get_attribute("loading") == "lazy"
    assert image.get_attribute("sizes") == "auto, 100vw"
    assert source.get_attribute("sizes") == "auto, 100vw"


def test_picture_candidate_failure_follows_native_event_truth(page: Any, browser_name: str) -> None:
    broken_small = "data:image/png;base64,AAAA"

    def serve_image(route: Any) -> None:
        route.fulfill(
            status=200,
            content_type="image/svg+xml",
            body=(
                '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40">'
                '<rect width="80" height="40" fill="#2563eb"/></svg>'
            ),
        )

    page.route("https://images.test/*.svg", serve_image)
    page.set_viewport_size({"width": 1000, "height": 700})
    page.set_content(_responsive_page(small_url=broken_small), wait_until="load")
    page.wait_for_function("document.querySelector('#responsive').dataset.status === 'loaded'")
    page.evaluate(
        "window.__nativeResponsive=[];document.querySelector('#responsive img')"
        ".addEventListener('error',event=>window.__nativeResponsive.push({"
        "trusted:event.isTrusted,current:event.currentTarget.currentSrc}))"
    )
    page.set_viewport_size({"width": 500, "height": 700})
    page.wait_for_timeout(750)
    state = page.evaluate(
        "({status:document.querySelector('#responsive').dataset.status,"
        "current:document.querySelector('#responsive img').currentSrc,"
        "complete:document.querySelector('#responsive img').complete,"
        "native:window.__nativeResponsive})"
    )
    if browser_name == "chromium":
        assert state == {
            "status": "loaded",
            "current": broken_small,
            "complete": True,
            "native": [],
        }
    else:
        assert state["status"] == "error", state
        assert state["current"] == broken_small
        assert state["native"] == [{"trusted": True, "current": broken_small}]
    page.set_viewport_size({"width": 1000, "height": 700})
    page.wait_for_function(
        "expected => document.querySelector('#responsive img').currentSrc === expected",
        arg=WIDE_URL,
    )
    page.wait_for_timeout(100)
    events = page.evaluate("JSON.parse(document.querySelector('#responsive-events').textContent)")
    statuses = [event["status"] for event in events]
    if browser_name == "chromium":
        assert statuses == ["loading", "loaded"]
    else:
        assert statuses == ["loading", "loaded", "error", "loaded"]


def test_untrusted_native_events_do_not_settle(page: Any) -> None:
    page.set_content(_page(), wait_until="load")
    page.wait_for_function("document.querySelector('#basic').dataset.status === 'loaded'")
    page.evaluate("document.querySelector('#basic img').dispatchEvent(new Event('error'));")
    page.wait_for_timeout(20)
    assert page.locator("#basic").get_attribute("data-status") == "loaded"


def test_trusted_load_with_empty_current_src_never_settles_loaded(page: Any) -> None:
    page.set_content(_page(), wait_until="load")
    page.wait_for_function("document.querySelector('#reactive').dataset.status === 'loaded'")
    page.evaluate(
        "const image=document.querySelector('#reactive img');"
        "window.__emptyCurrentLoads=0;"
        "image.addEventListener('load',event=>{if(event.isTrusted)window.__emptyCurrentLoads+=1});"
        "Object.defineProperty(image,'currentSrc',{configurable:true,get:()=>''});"
        f"Alpine.store('imageTest').source={BLUE!r}"
    )
    page.wait_for_function("document.querySelector('#reactive').dataset.status === 'loading'")
    page.wait_for_timeout(250)
    assert page.locator("#reactive").get_attribute("data-status") == "loading"
    assert page.evaluate("Alpine.store('imageTest').callbackEvents.at(-1)") == "loading"


def test_invalid_client_diagnostics_do_not_stringify_or_disclose_values(page: Any) -> None:
    page.set_content(_page(), wait_until="load")
    page.wait_for_function("document.querySelector('#reactive').dataset.status === 'loaded'")
    page.evaluate(
        "window.__imageStringified=0;window.__imageDiagnostics=[];"
        "const original=console.error;console.error=(...args)=>{"
        "window.__imageDiagnostics.push(args);original(...args)};"
        "Alpine.store('imageTest').source={toString(){"
        "window.__imageStringified+=1;return 'https://secret.invalid/image?token=SENTINEL'}}"
    )
    page.wait_for_function("window.__imageDiagnostics.length === 1")
    assert page.evaluate("window.__imageStringified") == 0
    diagnostic = page.evaluate(
        "({length:window.__imageDiagnostics[0].length,"
        "types:window.__imageDiagnostics[0].map(value=>typeof value),"
        "text:String(window.__imageDiagnostics[0][0])})"
    )
    assert diagnostic == {
        "length": 1,
        "types": ["string"],
        "text": ("[citry-ui] CImage src received an invalid object; retaining the last valid value."),
    }
    assert "SENTINEL" not in diagnostic["text"]


def test_invalid_callback_retains_last_valid_until_explicit_clear_or_replacement(page: Any) -> None:
    page.set_content(_page(), wait_until="load")
    page.wait_for_function("document.querySelector('#reactive').dataset.status === 'loaded'")
    assert page.evaluate("Alpine.store('imageTest').callbackEvents") == ["loading", "loaded"]

    page.evaluate(
        "Alpine.store('imageTest').callback='invalid';Alpine.store('imageTest').source='/broken-callback.png'"
    )
    page.wait_for_function("document.querySelector('#reactive').dataset.status === 'error'")
    assert page.evaluate("Alpine.store('imageTest').callbackEvents") == [
        "loading",
        "loaded",
        "loading",
        "error",
    ]

    page.evaluate(f"Alpine.store('imageTest').callback=null;Alpine.store('imageTest').source={BLUE!r}")
    page.wait_for_function("document.querySelector('#reactive').dataset.status === 'loaded'")
    assert page.evaluate("Alpine.store('imageTest').callbackEvents") == [
        "loading",
        "loaded",
        "loading",
        "error",
    ]

    page.evaluate(
        "Alpine.store('imageTest').callback=detail=>"
        "Alpine.store('imageTest').callbackEvents.push(`next:${detail.status}`);"
        f"Alpine.store('imageTest').source={GREEN!r}"
    )
    page.wait_for_function("Alpine.store('imageTest').callbackEvents.at(-1) === 'next:loaded'")
    assert page.evaluate("Alpine.store('imageTest').callbackEvents.slice(-2)") == [
        "next:loading",
        "next:loaded",
    ]


def test_reserved_semantics_and_runtime_marker_mutations_fail_closed(page: Any) -> None:
    page.set_content(_page(), wait_until="load")
    page.wait_for_function(
        "[...document.querySelectorAll('[data-citry-ui-part=\"image-root\"]')]"
        ".every(root=>root.hasAttribute('data-citry-image-initialized'))"
    )

    page.evaluate("document.querySelector('#basic').setAttribute('aria-description','hostile')")
    page.evaluate("document.querySelector('#missing').setAttribute('data-cid-hostile','changed')")
    page.evaluate("document.querySelector('#reactive img').setAttribute('aria-label','hostile')")
    page.evaluate("document.querySelector('#geometry').setAttribute('x-citry-fill-source','hostile')")
    page.evaluate("document.querySelector('#basic img').setAttribute('data-has-alpine-state','true')")
    page.wait_for_function(
        "['basic','missing','reactive','geometry'].every(id=>"
        "!document.getElementById(id).hasAttribute('data-citry-image-initialized'))"
    )
    for root_id in ("basic", "missing", "reactive", "geometry"):
        assert page.locator(f"#{root_id}").get_attribute("data-status") is None


def test_citry_events_marker_on_owned_anatomy_fails_closed(page: Any) -> None:
    page.set_content(_page(), wait_until="load")
    page.wait_for_function("document.querySelector('#geometry').dataset.status === 'loaded'")
    page.evaluate("document.querySelector('#geometry img').setAttribute('data-cev-on','forged')")
    page.wait_for_function("!document.querySelector('#geometry').hasAttribute('data-citry-image-initialized')")
    assert page.locator("#geometry").get_attribute("data-status") is None


def test_correlated_morph_preserves_equal_request_and_restarts_changed_or_replaced_request(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    app, html = _events_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#events-image')?.dataset.status === 'loaded'")
    page.evaluate(
        "window.__eventsImageRoot=document.querySelector('#events-image');"
        "window.__eventsImageNode=document.querySelector('#events-image img')"
    )
    baseline = page.evaluate("Alpine.store('imageMorph').events.length")

    page.evaluate("()=>Citry.events.send(document.querySelector('.advance-image'),'advance',{})")
    page.wait_for_function("document.querySelector('#image-step').textContent.trim() === '1'")
    page.wait_for_function("document.querySelector('#events-image')?.dataset.status === 'loaded'")
    assert page.evaluate("document.querySelector('#events-image')===window.__eventsImageRoot") is True
    assert page.evaluate("document.querySelector('#events-image img')===window.__eventsImageNode") is True
    assert page.evaluate("Alpine.store('imageMorph').events.length") == baseline

    page.evaluate("()=>Citry.events.send(document.querySelector('.advance-image'),'advance',{})")
    page.wait_for_function("document.querySelector('#image-step').textContent.trim() === '2'")
    page.wait_for_function("document.querySelector('#events-image')?.dataset.status === 'loaded'")
    assert page.evaluate("document.querySelector('#events-image')===window.__eventsImageRoot") is True
    assert page.evaluate("document.querySelector('#events-image img')===window.__eventsImageNode") is True
    assert page.evaluate("Alpine.store('imageMorph').events.slice(-2).map(event=>event.status)") == [
        "loading",
        "loaded",
    ]

    page.evaluate("window.__eventsImageNode=document.querySelector('#events-image img')")
    page.evaluate("()=>Citry.events.send(document.querySelector('.advance-image'),'advance',{})")
    page.wait_for_function("document.querySelector('#image-step').textContent.trim() === '3'")
    page.wait_for_function("document.querySelector('#events-image')?.dataset.status === 'loaded'")
    assert page.evaluate("document.querySelector('#events-image')===window.__eventsImageRoot") is True
    assert page.evaluate("document.querySelector('#events-image img')!==window.__eventsImageNode") is True
    assert page.locator("#events-image > picture > source").count() == 1
    assert page.evaluate("Alpine.store('imageMorph').events.slice(-2).map(event=>event.status)") == [
        "loading",
        "loaded",
    ]
    assert errors == []


def test_clone_hostile_anatomy_shadow_move_and_cleanup_are_owner_guarded(page: Any) -> None:
    errors: list[str] = []
    console_errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console",
        lambda message: console_errors.append(message.text)
        if message.type == "error" and "lost its owned native anatomy" in message.text
        else None,
    )
    page.set_content(_page(), wait_until="load")
    page.wait_for_function("document.querySelector('#basic').dataset.status === 'loaded'")

    page.evaluate(
        "const source=document.querySelector('#basic');"
        "const clone=source.cloneNode(true);clone.id='copied';document.body.append(clone);"
    )
    page.wait_for_function("!document.querySelector('#copied').hasAttribute('data-citry-image-initialized')")
    assert page.locator("#copied").get_attribute("data-status") is None

    page.locator("#basic [data-citry-ui-part='image']").evaluate(
        "image => image.setAttribute('title', 'Allowed consumer title')"
    )
    page.wait_for_timeout(20)
    assert page.locator("#basic").get_attribute("data-citry-image-initialized") == ""

    baseline_events = page.evaluate("Alpine.store('imageTest').events.length")
    page.locator("#basic").evaluate("root => root.setAttribute('style', 'color: red')")
    page.wait_for_function(
        "getComputedStyle(document.querySelector('#basic')).color === 'rgb(255, 0, 0)'"
        " && document.querySelector('#basic').style.getPropertyValue('--_cui-image-input-fit') === 'contain'"
        " && document.querySelector('#basic').style.getPropertyValue('--_cui-image-input-position') === '50% 50%'"
    )
    assert page.locator("#basic").get_attribute("data-citry-image-initialized") == ""
    assert page.locator("#basic").get_attribute("data-status") == "loaded"
    assert page.evaluate("Alpine.store('imageTest').events.length") == baseline_events

    page.locator("#missing [data-citry-ui-part='fallback']").evaluate(
        "visual => visual.insertAdjacentHTML('beforeend', '<img src=\"data:image/png;base64,AAAA\" alt=\"forged\">')"
    )
    page.wait_for_function("!document.querySelector('#missing').hasAttribute('data-citry-image-initialized')")
    assert page.locator("#missing img").count() == 2

    page.locator("#basic [data-citry-ui-part='placeholder']").evaluate("visual => { visual.hidden = false }")
    page.wait_for_function("!document.querySelector('#basic').hasAttribute('data-citry-image-initialized')")
    assert page.locator("#basic [data-citry-ui-part='placeholder']").is_hidden()

    page.locator("#reactive [data-citry-ui-part='image']").evaluate(
        "image => image.setAttribute('src', '/hostile-replacement.png')"
    )
    page.wait_for_function("!document.querySelector('#reactive').hasAttribute('data-citry-image-initialized')")
    assert page.locator("#reactive").get_attribute("data-status") is None

    page.evaluate(
        "const host=document.createElement('div');host.id='shadow-host';document.body.append(host);"
        "host.attachShadow({mode:'open'}).append(document.querySelector('#geometry'));"
    )
    page.wait_for_function(
        "document.querySelector('#shadow-host').shadowRoot.querySelector('#geometry')"
        ".hasAttribute('data-citry-image-initialized')"
    )
    assert (
        page.evaluate("document.querySelector('#shadow-host').shadowRoot.querySelector('#geometry').dataset.status")
        == "loaded"
    )
    page.evaluate(
        "const root=document.querySelector('#shadow-host').shadowRoot.querySelector('#geometry');"
        "document.body.append(root)"
    )
    page.wait_for_function("document.querySelector('#geometry').hasAttribute('data-citry-image-initialized')")

    removed = page.evaluate(
        "()=>{const root=document.querySelector('#geometry');root.remove();window.__removedImageRoot=root;return true}"
    )
    assert removed is True
    page.wait_for_function("!window.__removedImageRoot.hasAttribute('data-citry-image-initialized')")
    assert page.evaluate("window.__removedImageRoot.dataset.status ?? null") is None
    assert page.evaluate("Boolean(window.__removedImageRoot[Symbol.for('citry-ui:image-owner')])") is False
    assert errors == []
    assert console_errors == [
        "[citry-ui] CImage lost its owned native anatomy; component behavior was removed.",
        "[citry-ui] CImage lost its owned native anatomy; component behavior was removed.",
        "[citry-ui] CImage lost its owned native anatomy; component behavior was removed.",
    ]
