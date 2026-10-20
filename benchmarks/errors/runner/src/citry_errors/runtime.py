"""Run an app's development server, drive its page in a browser, and record what went wrong."""

from __future__ import annotations

import json
import os
import re
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING

from playwright.sync_api import sync_playwright

from .config import DEFAULT_JOURNEY, ConfigError
from .score import RuntimeResult
from .work import command_env, placeholder

if TYPE_CHECKING:
    from pathlib import Path

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
# it does for the user.
_SNAPSHOT = """() => {
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
    ]);
  }
  return {text: document.body ? document.body.innerText : '', elements};
}"""

# An HTTP status counts only where access logs print it: after the request
# line (`"GET / HTTP/1.1" 500`) or after the method and path (`POST /save 500`),
# so a response size such as `200 512` or a timing such as `250ms` is not
# read as a status.
_STATUS = re.compile(r'(?:HTTP/[\d.]+"? |\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) \S+ )([1-5]\d\d)\b')
# `\w*Error` also covers Python's and JavaScript's named errors, such as
# `TypeError:`, and `[500]` is how some dev servers tag a failed request.
_SERVER_ERROR = re.compile(
    r'Traceback|Exception|\bERROR\b|\b\w*Error\b|\[5\d\d\]|HTTP/[\d.]+"? 5\d\d\b'
    r"|\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) \S+ 5\d\d\b"
)
_SERVER_WARNING = re.compile(r"\bWARN(ING)?\b|\bwarn\b|Warning")
# Where each element's id and its aria-* pairs sit in a page record, in the
# order `_SNAPSHOT` writes them.
_ID, _ARIA = 8, 9
# 16 or more hex digits in a row in an id or any aria-* value are taken to be
# made up per render, such as the 32 random hex digits after `citry-vue-` on
# the element Citry mounts an interactive page into. A name a developer writes
# rarely has such a sequence; one that does is blanked too.
_GENERATED = re.compile(r"[0-9a-fA-F]{16,}")
# How long one step waits for its element before the journey counts as failed.
_STEP_TIMEOUT_MS = 5_000


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


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


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
        observation.snapshot_loaded = page.evaluate(_SNAPSHOT)
        _play(page, runtime.journeys[DEFAULT_JOURNEY], runtime.settle_ms)
    except Exception as error:  # noqa: BLE001 - a broken page is an observation, not a runner failure
        observation.failure = _describe(error)
    try:
        observation.snapshot = page.evaluate(_SNAPSHOT)
    except Exception as error:  # noqa: BLE001 - a page left mid-navigation is recorded, not raised
        observation.failure = observation.failure or f"record: {_describe(error)}"
    if not observation.failure:
        try:
            page.reload(wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(runtime.settle_ms)
            observation.snapshot_reloaded = page.evaluate(_SNAPSHOT)
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
        record.snapshot = page.evaluate(_SNAPSHOT)
    except Exception as error:  # noqa: BLE001 - a page left mid-navigation is recorded, not raised
        record.failure = record.failure or f"record: {_describe(error)}"
    page.context.close()
    return record


def observe(framework: Framework, env: Path, work: Path, log_path: Path) -> Observation:
    runtime = framework.runtime
    if runtime is None:
        raise ConfigError(f"{framework.key} has no [runtime] section")
    port = _free_port()
    argv = [placeholder(part, framework, env, work, port) for part in runtime.argv]
    url = f"http://127.0.0.1:{port}{runtime.page_path}"
    observation = Observation()
    with log_path.open("w") as log:
        process = subprocess.Popen(
            argv,
            cwd=work,
            env=command_env(framework, env, work, runtime.env, port),
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
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                _default_journey(browser, url, runtime, observation)
                for name, steps in runtime.journeys.items():
                    if name != DEFAULT_JOURNEY:
                        observation.journeys[name] = _journey(browser, url, steps, runtime.settle_ms, observation)
                browser.close()
        finally:
            _stop(process)
    observation.server_log = log_path.read_text(errors="replace").splitlines()
    return observation


def _normal(line: str, *, keep_status: bool) -> str:
    """Blank what differs between any two runs: ports, timestamps, counters.

    In a server log, HTTP status codes are kept, so a 500 in the access log
    does not look like the clean app's 200.
    """
    statuses = [match.group(1) for match in _STATUS.finditer(line)] if keep_status else []
    # Each case runs in a working folder named after it, which a dev server
    # may print, such as "Will watch for changes in .../work/m01-...".
    line = re.sub(r"\bwork/[^/\s'\"]+", "work/<case>", line)
    return " ".join(re.sub(r"\d+", "N", line).split()) + "".join(f" status={code}" for code in statuses)


def _response_key(line: str) -> str:
    # A failed response is recorded as `<status> <url>`; the status is kept so
    # a 500 on a URL does not look like the clean app's 404 on it.
    status, _, url = line.partition(" ")
    return f"{status} {_normal(url, keep_status=False)}"


def _added(
    baseline: list[str], mutated: list[str], *, keep_status: bool = False, responses: bool = False
) -> list[str]:
    """Return the case's lines that the clean app's run did not have."""

    def key(line: str) -> str:
        return _response_key(line) if responses else _normal(line, keep_status=keep_status)

    seen = {key(line) for line in baseline if line.strip()}
    return [line for line in mutated if line.strip() and key(line) not in seen]


def problems(observation: Observation) -> list[str]:
    """List what makes the clean app's run unusable as the comparison point."""
    found = []
    if not observation.started:
        found.append("did not start")
    if observation.failure:
        found.append(observation.failure)
    found += [f"journey {name}: {record.failure}" for name, record in observation.journeys.items() if record.failure]
    found += observation.console_errors[:3] + observation.bad_responses[:3]
    found += [line for line in observation.server_log if _SERVER_ERROR.search(line)][:3]
    return found


def compare(baseline: Observation, mutated: Observation) -> RuntimeResult:
    """Classify the case's runtime behavior against the clean app's."""
    result = RuntimeResult(started=mutated.started)
    errors = (
        _added(baseline.console_errors, mutated.console_errors)
        + _added(baseline.bad_responses, mutated.bad_responses, responses=True)
        + [
            line
            for line in _added(baseline.server_log, mutated.server_log, keep_status=True)
            if _SERVER_ERROR.search(line)
        ]
    )
    if mutated.failure and not baseline.failure:
        # The scripted clicks could not run, for example because a button is
        # missing. That is a visible difference, not an error message.
        result.output_differs = True
        result.evidence.append(f"interaction: {mutated.failure}")
    for name, record in mutated.journeys.items():
        clean = baseline.journeys.get(name)
        # The same rule for every other journey: a step the clean page could
        # take and the case's page could not is a visible difference.
        if record.failure and not (clean and clean.failure):
            result.output_differs = True
            result.evidence.append(f"interaction ({name}): {record.failure}")
    warnings = _added(baseline.console_warnings, mutated.console_warnings) + [
        line
        for line in _added(baseline.server_log, mutated.server_log, keep_status=True)
        if _SERVER_WARNING.search(line) and not _SERVER_ERROR.search(line)
    ]
    if not mutated.started:
        result.error = True
        result.evidence.append(mutated.failure)
    result.error = result.error or bool(errors)
    result.warning = bool(warnings)
    result.evidence += [f"error: {line}" for line in errors[:10]] + [f"warning: {line}" for line in warnings[:10]]
    if _pages(mutated) != _pages(baseline):
        result.output_differs = True
    return result


def _pages(observation: Observation) -> tuple:
    """Gather every page record of one run, in the form the comparison uses."""
    # A journey only one run has (a server that never started records none)
    # makes the two differ too.
    return (
        comparable(observation.snapshot_loaded),
        comparable(observation.snapshot),
        comparable(observation.snapshot_reloaded),
        {name: comparable(record.snapshot) for name, record in observation.journeys.items()},
    )


def comparable(snapshot: dict | None) -> dict | None:
    """
    Blank the parts of a page record that a framework generates anew on every render.

    Without this, two loads of the same clean page would never match, and
    every case of that framework would read as "silently wrong".
    """
    if snapshot is None:
        return None
    elements = []
    for element in snapshot["elements"]:
        row = list(element)
        row[_ID] = _blank_generated(row[_ID])
        # aria-controls and aria-labelledby name other elements by id.
        row[_ARIA] = [[name, _blank_generated(value)] for name, value in row[_ARIA]]
        elements.append(row)
    return {**snapshot, "elements": elements}


def _blank_generated(value: str | None) -> str | None:
    return None if value is None else _GENERATED.sub("<generated>", value)
