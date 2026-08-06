"""Rebuild and smoke-test both Storybook adapters with Chromium."""

from __future__ import annotations

import http.client
import json
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING

from playwright.sync_api import Browser, expect, sync_playwright

if TYPE_CHECKING:
    from collections.abc import Iterator

    from playwright.sync_api import FrameLocator, Page

_ROOT = Path(__file__).resolve().parent
_BACKEND_PORT = 8123
_ADAPTERS = (("Server/Webpack", 6206, "server"), ("HTML/Vite", 6207, "html"))
_STATIC_STORY_ID = "citry-ui-button-static--preview"
_REACTIVE_STORY_ID = "citry-ui-readiness-reactive-state--preview"
_PROXY_HEADERS = frozenset(
    (
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
    )
)


class _ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def _run(script: str) -> None:
    subprocess.run(["pnpm", "run", script], cwd=_ROOT, check=True)  # noqa: S607


def _stop(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


@contextmanager
def _running(command: list[str]) -> Iterator[subprocess.Popen[bytes]]:
    process = subprocess.Popen(
        command,
        cwd=_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        yield process
    finally:
        _stop(process)


def _wait_http(port: int, path: str = "/") -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            response.read()
            if response.status < 500:
                return
        except OSError:
            time.sleep(0.1)
        finally:
            connection.close()
    msg = f"Timed out waiting for http://127.0.0.1:{port}{path}."
    raise RuntimeError(msg)


@contextmanager
def _static_proxy(port: int, directory: Path) -> Iterator[ThreadingHTTPServer]:
    allowed_hosts = frozenset((f"127.0.0.1:{port}", f"localhost:{port}"))

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, message_format: str, *args: object) -> None:
            pass

        def reject_untrusted_host(self, *, include_body: bool) -> bool:
            if self.headers.get("Host") not in allowed_hosts:
                body = b"Untrusted Citry Storybook Host."
                self.send_response(403)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if include_body:
                    self.wfile.write(body)
                return True
            return False

        def do_GET(self) -> None:
            if self.reject_untrusted_host(include_body=True):
                return
            if self.path == "/citry" or self.path.startswith("/citry/"):
                self._proxy_to_citry()
                return
            super().do_GET()

        def do_HEAD(self) -> None:
            if self.reject_untrusted_host(include_body=False):
                return
            super().do_HEAD()

        def _proxy_to_citry(self) -> None:
            connection = http.client.HTTPConnection("127.0.0.1", _BACKEND_PORT, timeout=10)
            headers = dict(self.headers.items())
            headers["Host"] = f"127.0.0.1:{_BACKEND_PORT}"
            try:
                connection.request("GET", self.path, headers=headers)
                response = connection.getresponse()
                body = response.read()
            except OSError as error:
                body = f"Storybook proxy failed for {self.path}: {error}".encode()
                self.send_response(502)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            finally:
                connection.close()

            self.send_response(response.status)
            for name, value in response.getheaders():
                if name.lower() not in _PROXY_HEADERS and name.lower() != "content-length":
                    self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = _ReusableThreadingHTTPServer(
        ("127.0.0.1", port),
        partial(Handler, directory=str(directory)),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _check_static_adapter(browser: Browser, name: str, port: int) -> None:
    page = browser.new_page()
    browser_errors: list[str] = []
    page.on("pageerror", lambda error: browser_errors.append(str(error)))
    page.goto(f"http://127.0.0.1:{port}/?path=/story/{_STATIC_STORY_ID}&addonPanel=storybook/controls/panel")
    frame = page.frame_locator('iframe[title="storybook-preview-iframe"]')
    button = frame.locator('[data-citry-ui-part="button"]')
    expect(button).to_contain_text("Save changes")
    background = button.evaluate("element => getComputedStyle(element).backgroundColor")
    if background != "rgb(23, 92, 211)":
        msg = f"{name} did not activate the Citry UI Button CSS: {background!r}."
        raise RuntimeError(msg)

    changed_label = f"Changed through {name} Controls"
    page.locator("#control-label").fill(changed_label)
    expect(button).to_contain_text(changed_label)
    if browser_errors:
        msg = f"{name} reported browser errors: {browser_errors!r}."
        raise RuntimeError(msg)
    page.close()


def _readiness_audit(frame: FrameLocator) -> dict[str, object]:
    return frame.locator("body").evaluate("() => globalThis.__citryUiReadiness")


def _navigate_story(page: Page, story_id: str) -> None:
    page.evaluate(
        """storyId => {
          const url = `/?path=/story/${storyId}`;
          history.pushState({}, "", url);
          dispatchEvent(new PopStateEvent("popstate"));
        }""",
        story_id,
    )


def _render_count(port: int, audit_key: str) -> int:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
    try:
        connection.request("GET", "/citry/ext/storybook_scenarios/audit")
        response = connection.getresponse()
        body = response.read()
    finally:
        connection.close()
    if response.status != 200:
        raise RuntimeError(f"Storybook proxy on port {port} returned {response.status} for its render audit.")
    return int(json.loads(body)["renders"].get(audit_key, 0))


def _wait_for_render(port: int, audit_key: str, previous_count: int) -> None:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if _render_count(port, audit_key) > previous_count:
            return
        time.sleep(0.05)
    raise RuntimeError(f"Storybook proxy on port {port} never started render {audit_key!r}.")


def _check_interactive_adapter(browser: Browser, name: str, port: int) -> None:
    page = browser.new_page()
    browser_errors: list[str] = []
    page.on("pageerror", lambda error: browser_errors.append(str(error)))
    page.goto(f"http://127.0.0.1:{port}/?path=/story/{_REACTIVE_STORY_ID}&addonPanel=storybook/controls/panel")
    frame = page.frame_locator('iframe[title="storybook-preview-iframe"]')
    probe = frame.locator('.citry-ui-readiness-probe[data-ready="true"]')
    expect(probe).to_have_attribute("data-generation", "first", timeout=10_000)
    expect(probe).to_be_visible()
    expect(probe.locator("output")).to_have_text("0")
    background = probe.evaluate("element => getComputedStyle(element).backgroundColor")
    if background != "rgb(219, 234, 254)":
        msg = f"{name} did not activate the readiness CSS: {background!r}."
        raise RuntimeError(msg)
    audit = _readiness_audit(frame)
    if audit != {
        "active": 1,
        "cleanups": [],
        "clicks": [],
        "events": [],
        "inits": ["first"],
    }:
        msg = f"{name} started with an unexpected readiness audit: {audit!r}."
        raise RuntimeError(msg)

    probe.get_by_role("button", name="Increment").click()
    expect(probe.locator("output")).to_have_text("1")
    probe.get_by_role("button", name="Increment").evaluate("element => { globalThis.__citryUiOldButton = element; }")

    page.locator("#control-generation").select_option("delayed")
    delayed = frame.locator('.citry-ui-readiness-probe[data-generation="delayed"]')
    expect(delayed).to_have_attribute("data-ready", "loading")
    expect(delayed).to_be_hidden()
    expect(probe).to_be_visible()
    staging_audit = _readiness_audit(frame)
    if staging_audit["active"] != 1 or staging_audit["inits"][-1] != "delayed":
        raise RuntimeError(f"{name} activated delayed side effects before readiness: {staging_audit!r}.")
    expect(delayed).to_have_attribute("data-ready", "true", timeout=3_000)
    expect(delayed).to_be_visible()
    frame.locator("body").evaluate("() => globalThis.__citryUiOldButton.click()")
    if _readiness_audit(frame)["clicks"] != ["first"]:
        raise RuntimeError(f"{name} left the removed generation's click handler active.")
    audit = _readiness_audit(frame)
    if audit != {
        "active": 1,
        "cleanups": ["first"],
        "clicks": ["first"],
        "events": [],
        "inits": ["first", "delayed"],
    }:
        msg = f"{name} did not promote the delayed generation cleanly: {audit!r}."
        raise RuntimeError(msg)

    page.evaluate(
        """storyId => {
          const channel = globalThis.__STORYBOOK_ADDONS_CHANNEL__;
          const listener = payload => {
            if (payload.storyId === storyId) {
              globalThis.__citryUiStoryFinishedStatus = payload.status;
            }
          };
          globalThis.__citryUiStoryFinishedListener = listener;
          channel.on("storyFinished", listener);
        }""",
        _REACTIVE_STORY_ID,
    )
    page.locator("#control-generation").select_option("never")
    never = frame.locator('.citry-ui-readiness-probe[data-generation="never"]')
    expect(never).to_have_attribute("data-ready", "loading")
    expect(never).to_be_hidden()
    expect(delayed).to_be_visible()
    expect(frame.locator("body")).to_contain_text(
        "did not reach readiness selector",
        timeout=3_000,
    )
    page.wait_for_function(
        "() => globalThis.__citryUiStoryFinishedStatus === 'error'",
        timeout=3_000,
    )
    page.evaluate(
        """() => {
          const listener = globalThis.__citryUiStoryFinishedListener;
          if (listener) {
            globalThis.__STORYBOOK_ADDONS_CHANNEL__.off("storyFinished", listener);
          }
          delete globalThis.__citryUiStoryFinishedListener;
          delete globalThis.__citryUiStoryFinishedStatus;
        }""",
    )
    expect(delayed).to_be_attached()
    audit = _readiness_audit(frame)
    if audit != {
        "active": 1,
        "cleanups": ["first", "never"],
        "clicks": ["first"],
        "events": [],
        "inits": ["first", "delayed", "never"],
    }:
        msg = f"{name} did not preserve the last good generation after failure: {audit!r}."
        raise RuntimeError(msg)

    page.locator("#control-generation").select_option("second")
    probe = frame.locator('.citry-ui-readiness-probe[data-generation="second"]')
    expect(probe).to_have_attribute("data-ready", "true", timeout=3_000)
    expect(probe).to_be_visible()
    expect(probe.locator("output")).to_have_text("0")
    audit = _readiness_audit(frame)
    if audit != {
        "active": 1,
        "cleanups": ["first", "never", "delayed"],
        "clicks": ["first"],
        "events": [],
        "inits": ["first", "delayed", "never", "second"],
    }:
        msg = f"{name} did not recover from the failed generation cleanly: {audit!r}."
        raise RuntimeError(msg)

    frame.locator("body").evaluate("() => window.dispatchEvent(new Event('citry-ui-readiness-increment'))")
    expect(probe.locator("output")).to_have_text("1")
    if _readiness_audit(frame)["events"] != ["second"]:
        raise RuntimeError(f"{name} left more than one readiness window listener active.")

    audit_key = "readiness/reactive-state:slow"
    previous_slow_count = _render_count(port, audit_key)
    page.locator("#control-generation").select_option("slow")
    _wait_for_render(port, audit_key, previous_slow_count)
    page.locator("#control-generation").select_option("first")
    probe = frame.locator('.citry-ui-readiness-probe[data-generation="first"]')
    expect(probe).to_have_attribute("data-ready", "true", timeout=3_000)
    expect(probe).to_be_visible()
    audit = _readiness_audit(frame)
    if "slow" in audit["inits"] or audit["active"] != 1:
        raise RuntimeError(f"{name} activated a stale slow generation: {audit!r}.")

    _navigate_story(page, _STATIC_STORY_ID)
    expect(frame.locator('[data-citry-ui-part="button"]')).to_be_visible()
    audit = _readiness_audit(frame)
    if audit["active"] != 0 or audit["cleanups"][-1] != "first":
        raise RuntimeError(f"{name} did not clean up on story navigation: {audit!r}.")
    if browser_errors:
        msg = f"{name} reported browser errors: {browser_errors!r}."
        raise RuntimeError(msg)
    page.close()


def _check_standalone(browser: Browser) -> None:
    page = browser.new_page()
    page.goto(f"http://127.0.0.1:{_BACKEND_PORT}/citry/ext/storybook_scenarios/page/readiness/reactive-state")
    probe = page.locator('.citry-ui-readiness-probe[data-ready="true"]')
    expect(probe).to_have_attribute("data-generation", "first", timeout=10_000)
    probe.get_by_role("button", name="Increment").click()
    expect(probe.locator("output")).to_have_text("1")
    page.locator("main").evaluate("element => element.remove()")
    page.wait_for_function("globalThis.__citryUiReadiness?.active === 0")
    page.close()


def _check_backend_failure(browser: Browser, port: int) -> None:
    page = browser.new_page()
    page.goto(f"http://127.0.0.1:{port}/iframe.html?id={_STATIC_STORY_ID}&viewMode=story")
    expect(page.locator("body")).to_contain_text("The component failed to render properly", timeout=10_000)
    page.close()


def _check_proxy_host_policy(port: int) -> None:
    for method in ("GET", "HEAD"):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            connection.request(
                method,
                "/citry/ext/storybook_scenarios/catalog",
                headers={"Host": "attacker.example"},
            )
            response = connection.getresponse()
            response.read()
        finally:
            connection.close()
        if response.status != 403:
            msg = f"Storybook proxy on port {port} accepted an untrusted {method} Host."
            raise RuntimeError(msg)


def main() -> int:
    _run("test:dev-proxy")
    _run("generate")
    _run("build:server")
    _run("build:html")

    backend_command = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(_BACKEND_PORT),
    ]
    with (
        _running(backend_command) as backend,
        _static_proxy(6206, _ROOT / "storybook-static/server"),
        _static_proxy(6207, _ROOT / "storybook-static/html"),
        sync_playwright() as playwright,
    ):
        _wait_http(_BACKEND_PORT, "/citry/ext/storybook_scenarios/catalog")
        if backend.poll() is not None:
            raise RuntimeError("The Storybook scenario backend exited before the smoke began.")
        for _, port, _ in _ADAPTERS:
            _wait_http(port)
            _check_proxy_host_policy(port)

        browser = playwright.chromium.launch()
        try:
            _check_standalone(browser)
            for name, port, _ in _ADAPTERS:
                _check_static_adapter(browser, name, port)
                _check_interactive_adapter(browser, name, port)
            _stop(backend)
            for _, port, _ in _ADAPTERS:
                _check_backend_failure(browser, port)
        finally:
            browser.close()

    sys.stdout.write("Standalone and both Storybook adapters passed the interactive Chromium smoke.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
