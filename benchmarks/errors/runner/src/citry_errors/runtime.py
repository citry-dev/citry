"""Run an app's development server, drive its page in a browser, and record what went wrong."""

from __future__ import annotations

import json
import os
import random
import re
import signal
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager, nullcontext
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING

from playwright.sync_api import sync_playwright

from .config import DEFAULT_JOURNEY, ConfigError
from .work import command_env, placeholder

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path
    from typing import IO

    from playwright.sync_api import Browser, Page

    from .config import Framework, Runtime, Step

# The visible state the comparison uses. It covers text, element kinds, the
# button type the browser settled on, tooltips and the computed color, border
# color (with the hover and focus the last click left) and display, so a
# missing style or a dropped attribute shows up, while
# framework-internal markup that never reaches the screen does not. It also
# keeps what screen readers read (`alt` and every `aria-*` attribute), the
# `id` that links and labels point to, and whether a control is disabled, so
# a mistake in one of those reads as a different page rather than the same one. `:disabled` is
# the state the browser applies, so `disabled="false"` counts as disabled, as
# it does for the user. For an image it records whether the image loaded, so
# a broken image reads as a different page even when the server answered
# its URL without an error status.
#
# Before it records anything it waits, at most `waitMs` (`_IMAGE_WAIT_MS` in a
# run), for every
# image that has not finished, so an image still loading when the page went
# quiet is not read as broken in one run and loaded in the other. An image
# the browser never requests, such as a lazy one far below the fold, uses up
# that wait and records as not loaded in every run.
_IMAGE_WAIT_MS = 2_000
_SNAPSHOT = """async (waitMs) => {
  const pending = [...document.images].filter((img) => !img.complete).map((img) => new Promise((done) => {
    img.addEventListener('load', done, {once: true});
    img.addEventListener('error', done, {once: true});
  }));
  await Promise.race([Promise.all(pending), new Promise((done) => setTimeout(done, waitMs))]);
  const skip = new Set(['SCRIPT', 'STYLE', 'LINK', 'META', 'TEMPLATE', 'NOSCRIPT']);
  const elements = [];
  for (const el of document.querySelectorAll('body *')) {
    if (skip.has(el.tagName) || el.closest('nextjs-portal, nuxt-devtools-frame, #nuxt-devtools-container')) continue;
    const style = getComputedStyle(el);
    const aria = el.getAttributeNames().filter((name) => name.startsWith('aria-')).sort()
      .map((name) => [name, el.getAttribute(name)]);
    elements.push([
      el.tagName, el.getAttribute('title'), el.type ?? null, style.color, style.display, style.visibility,
      style.borderColor, el.getAttribute('alt'), el.getAttribute('id'), aria, el.matches(':disabled'),
      el.tagName === 'IMG' ? el.complete && el.naturalWidth > 0 : null,
    ]);
  }
  return {text: document.body ? document.body.innerText : '', elements};
}"""

# Where each element's id, its aria-* pairs and, for an image, whether it
# loaded sit in a page record, in the order `_SNAPSHOT` writes them.
_ID, _ARIA, _LOADED = 8, 9, 11
# How long one step waits for its element before the journey counts as failed.
_STEP_TIMEOUT_MS = 5_000
# Dev servers listen on ports from this range. It sits below the range the
# operating system takes the local ends of outgoing connections from (49152
# and up on macOS, 32768 and up on Linux), so the browser's or another
# server's connections cannot take a port between its reservation here and
# the server's start. It also ends below 24678, where `nuxt dev` looks for a
# free hot-reload port (24678 to 24698) on its own, so it never finds one of
# these free and then loses it to the server it was reserved for.
_PORTS = range(20_000, 24_678)
# Ports handed to a server that is still running in this process. Several
# workers start servers at once, and checking that a port is free does not
# keep it free, so a second worker must not be given the same port.
_reserved_ports: set[int] = set()
_ports_lock = threading.Lock()
# How many ports a server gets in all: one, plus a new one each time it could
# not listen because another program took its port after it was checked.
_PORT_ATTEMPTS = 3
# Python and Node print the first two; Django's runserver prints the third,
# and Reflex the third with the port number in it (`Frontend port: 20001 is
# already in use.`).
_PORT_IN_USE = re.compile(r"address already in use|EADDRINUSE|port(?::? \d+)? is already in use", re.IGNORECASE)
# How long the server's log must stay unchanged before the record of its
# output ends, and the longest the runner waits for that.
_LOG_QUIET_S = 0.3
_LOG_QUIET_LIMIT_S = 5.0


@dataclass
class JourneyRecord:
    """The page at the end of one named journey, or why the journey stopped early."""

    snapshot: dict | None = None
    failure: str = ""


@dataclass
class Observation:
    started: bool = True
    # The page right after it loads, and again after the default journey's
    # steps. A mistake can show in either: an ignored directive shows text
    # too early.
    snapshot_loaded: dict | None = None
    snapshot: dict | None = None
    # After a reload, a value the response showed but the server never kept
    # (a write to a misspelled state field) is gone.
    snapshot_reloaded: dict | None = None
    # Why the first load, the default journey or the reload stopped early.
    failure: str = ""
    # Every other journey, by name, each run from a fresh load of the page.
    journeys: dict[str, JourneyRecord] = field(default_factory=dict)
    console_errors: list[str] = field(default_factory=list)
    console_warnings: list[str] = field(default_factory=list)
    bad_responses: list[str] = field(default_factory=list)
    server_log: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> Observation:
        """Read back what `to_json` wrote, as a stored browser check that a later run reuses."""
        data = json.loads(text)
        journeys = {name: JourneyRecord(**record) for name, record in data.pop("journeys").items()}
        return cls(**data, journeys=journeys)


def _port_is_free(port: int) -> bool:
    """Tell whether nothing on this machine listens on, or holds, the port right now."""
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


@contextmanager
def reserve_port() -> Iterator[int]:
    """
    Give a free port that no other server of this run gets until the block ends.

    The port is checked and recorded under one lock, so two workers asking
    at the same moment get different ports.
    """
    with _ports_lock:
        # A random order keeps two runs on one machine, each with its own
        # reservations, from trying the same ports in the same order.
        candidates = random.sample(_PORTS, k=len(_PORTS))
        port = next((port for port in candidates if port not in _reserved_ports and _port_is_free(port)), None)
        if port is None:
            raise RuntimeError(f"no free port between {_PORTS.start} and {_PORTS.stop - 1}")
        _reserved_ports.add(port)
    try:
        yield port
    finally:
        with _ports_lock:
            _reserved_ports.discard(port)


def _wait_ready(url: str, process: subprocess.Popen, timeout: int) -> bool:
    """Wait for any HTTP answer: an error page still means the server is up, and the browser records it."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            # The URL is always the local development server's http address.
            urllib.request.urlopen(url, timeout=5).close()  # noqa: S310
            return True
        except urllib.error.HTTPError:
            return True
        except OSError:
            time.sleep(0.5)
    return False


def _quiet_size(log: IO[str]) -> int:
    """Wait until the server's log stops growing, then give its size in bytes."""
    deadline = time.monotonic() + _LOG_QUIET_LIMIT_S
    size = os.fstat(log.fileno()).st_size
    while time.monotonic() < deadline:
        time.sleep(_LOG_QUIET_S)
        grown = os.fstat(log.fileno()).st_size
        if grown == size:
            break
        size = grown
    return size


def _stop(process: subprocess.Popen) -> None:
    """Stop the server's whole process group; a server that already exited at startup is fine."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=10)
    except ProcessLookupError:
        return
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=10)


def _describe(error: Exception) -> str:
    # An error with an empty message still needs a line, or the handler that
    # records it would raise in turn.
    return f"{type(error).__name__}: {(str(error).splitlines() or [''])[0]}"


def _open_page(browser: Browser, observation: Observation) -> Page:
    """
    Open a page in a new browser context, recording its console, errors and failed responses.

    A new context has no cookies or storage from an earlier journey, so each
    journey starts the way a first visit does. The server keeps whatever an
    earlier journey saved, the same in the clean app's run and the case's,
    apart from what the case's mistake changed.
    """
    page = browser.new_context().new_page()
    page.on(
        "console",
        lambda message: (
            observation.console_errors.append(message.text)
            if message.type == "error"
            else observation.console_warnings.append(message.text)
            if message.type in {"warning", "warn"}
            else None
        ),
    )
    page.on("pageerror", lambda error: observation.console_errors.append(f"pageerror: {error}"))
    page.on(
        "response",
        lambda response: (
            observation.bad_responses.append(f"{response.status} {response.url}")
            if response.status >= 400 and not response.url.endswith("favicon.ico")
            else None
        ),
    )
    return page


def _play(page: Page, steps: tuple[Step, ...], settle_ms: int) -> None:
    """Run a journey's steps, then wait for the requests they started and for the page to settle."""
    for step in steps:
        # `.first` keeps a selector that matches every card's button, such as
        # Hide, pointed at the first card, the same one in every framework.
        if step.action == "click":
            page.locator(step.selector).first.click(timeout=_STEP_TIMEOUT_MS)
        elif step.action == "fill":
            page.locator(step.selector).first.fill(step.text, timeout=_STEP_TIMEOUT_MS)
        elif step.action == "press" and step.selector:
            page.locator(step.selector).first.press(step.key, timeout=_STEP_TIMEOUT_MS)
        elif step.action == "press":
            # With no selector the key goes to whatever an earlier step focused.
            page.keyboard.press(step.key)
        elif step.action == "wait":
            page.wait_for_timeout(step.ms)
        else:
            # The loader accepts only the actions above, so this is an action
            # added to STEP_KEYS without a branch here.
            raise ConfigError(f"the browser check cannot run step action {step.action!r}")
    page.wait_for_load_state("networkidle", timeout=15_000)
    page.wait_for_timeout(settle_ms)


def _default_journey(browser: Browser, url: str, runtime: Runtime, observation: Observation) -> None:
    """Record the page after it loads, after the default journey's steps, and after a reload."""
    page = _open_page(browser, observation)
    try:
        page.goto(url, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(runtime.settle_ms)
        observation.snapshot_loaded = page.evaluate(_SNAPSHOT, _IMAGE_WAIT_MS)
        _play(page, runtime.journeys[DEFAULT_JOURNEY], runtime.settle_ms)
    except Exception as error:  # noqa: BLE001 - a broken page is an observation, not a runner failure
        observation.failure = _describe(error)
    try:
        observation.snapshot = page.evaluate(_SNAPSHOT, _IMAGE_WAIT_MS)
    except Exception as error:  # noqa: BLE001 - a page left mid-navigation is recorded, not raised
        observation.failure = observation.failure or f"record: {_describe(error)}"
    if not observation.failure:
        try:
            page.reload(wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(runtime.settle_ms)
            observation.snapshot_reloaded = page.evaluate(_SNAPSHOT, _IMAGE_WAIT_MS)
        except Exception as error:  # noqa: BLE001 - same as above
            observation.failure = f"reload: {_describe(error)}"
    # Closed before the next journey starts, so this page's timers and
    # requests cannot change the server or add messages while it runs.
    page.context.close()


def _journey(
    browser: Browser, url: str, steps: tuple[Step, ...], settle_ms: int, observation: Observation
) -> JourneyRecord:
    """Load the page fresh, run one named journey's steps, and record the page at the end."""
    record = JourneyRecord()
    page = _open_page(browser, observation)
    try:
        page.goto(url, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(settle_ms)
        _play(page, steps, settle_ms)
    except Exception as error:  # noqa: BLE001 - a broken page is an observation, not a runner failure
        record.failure = _describe(error)
    try:
        record.snapshot = page.evaluate(_SNAPSHOT, _IMAGE_WAIT_MS)
    except Exception as error:  # noqa: BLE001 - a page left mid-navigation is recorded, not raised
        record.failure = record.failure or f"record: {_describe(error)}"
    page.context.close()
    return record


def observe(framework: Framework, env: Path, work: Path, log_path: Path) -> Observation:
    """
    Start the app's development server on a free port, drive its page, and stop the server.

    A server that could not listen because another program took its port
    is started again on a new port, so the clash is not recorded as the
    case's server failing to start.
    """
    runtime = framework.runtime
    if runtime is None:
        raise ConfigError(f"{framework.key} has no [runtime] section")
    # A second port is reserved only for a server that names one, so a
    # server that needs one port takes only one.
    needs_backend_port = any("{backend_port}" in part for part in (*runtime.argv, *runtime.env.values()))
    for _attempt in range(_PORT_ATTEMPTS):
        with reserve_port() as port, reserve_port() if needs_backend_port else nullcontext(0) as backend_port:
            observation = _observe_on(framework, runtime, env, work, log_path, port, backend_port)
        # The log is read from the file: a server that never answered keeps an
        # empty `server_log` in its observation, as the comparison expects.
        if observation.started or not _PORT_IN_USE.search(log_path.read_text(errors="replace")):
            break
    return observation


def _observe_on(
    framework: Framework, runtime: Runtime, env: Path, work: Path, log_path: Path, port: int, backend_port: int
) -> Observation:
    argv = [placeholder(part, framework, env, work, port, backend_port) for part in runtime.argv]
    url = f"http://127.0.0.1:{port}{runtime.page_path}"
    observation = Observation()
    with log_path.open("w") as log:
        process = subprocess.Popen(
            argv,
            cwd=work,
            env=command_env(framework, env, work, runtime.env, port, backend_port),
            stdout=log,
            stderr=subprocess.STDOUT,
            # A new process group lets the whole dev server tree be stopped at once.
            start_new_session=True,
        )
        try:
            if not _wait_ready(url, process, runtime.ready_timeout):
                observation.started = False
                observation.failure = "the development server did not answer"
                return observation
            # Each call starts its own Playwright and browser: Playwright's
            # synchronous API must not be shared between threads, and a
            # browser that crashes then takes down only this case.
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                _default_journey(browser, url, runtime, observation)
                for name, steps in runtime.journeys.items():
                    if name != DEFAULT_JOURNEY:
                        observation.journeys[name] = _journey(browser, url, steps, runtime.settle_ms, observation)
                browser.close()
        finally:
            # What the server prints once it is told to stop says nothing
            # about the page, and some of it comes only in some runs, such as
            # granian's `Unexpected exit from worker-1` under `reflex run`; it
            # would make the clean app or a case report an error at random. So
            # the record ends where the browser check did, once the server has
            # finished printing what the last journey caused. The log file
            # keeps everything.
            recorded = _quiet_size(log)
            _stop(process)
    with log_path.open("rb") as file:
        observation.server_log = file.read(recorded).decode(errors="replace").splitlines()
    return observation
