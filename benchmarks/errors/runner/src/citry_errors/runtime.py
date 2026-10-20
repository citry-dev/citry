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

from .config import ConfigError
from .score import RuntimeResult
from .work import command_env, placeholder

if TYPE_CHECKING:
    from pathlib import Path

    from .config import Framework

# The visible state the comparison uses. It covers text, element kinds, the
# button type the browser settled on, tooltips and the computed color and
# display, so a missing style or a dropped attribute shows up, while
# framework-internal markup that never reaches the screen does not.
_SNAPSHOT = """() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'LINK', 'META', 'TEMPLATE', 'NOSCRIPT']);
  const elements = [];
  for (const el of document.querySelectorAll('body *')) {
    if (skip.has(el.tagName) || el.closest('nextjs-portal, nuxt-devtools-frame, #nuxt-devtools-container')) continue;
    const style = getComputedStyle(el);
    elements.push([
      el.tagName, el.getAttribute('title'), el.type ?? null, style.color, style.display, style.visibility,
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


@dataclass
class Observation:
    started: bool = True
    # The page right after it loads, and again after the scripted clicks. A
    # mistake can show in either: an ignored directive shows text too early.
    snapshot_loaded: dict | None = None
    snapshot: dict | None = None
    # After a reload, a value the response showed but the server never kept
    # (a write to a misspelled state field) is gone.
    snapshot_reloaded: dict | None = None
    console_errors: list[str] = field(default_factory=list)
    console_warnings: list[str] = field(default_factory=list)
    bad_responses: list[str] = field(default_factory=list)
    server_log: list[str] = field(default_factory=list)
    failure: str = ""

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
                page = browser.new_page()
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
                try:
                    page.goto(url, wait_until="networkidle", timeout=60_000)
                    page.wait_for_timeout(runtime.settle_ms)
                    observation.snapshot_loaded = page.evaluate(_SNAPSHOT)
                    for step in runtime.steps:
                        if step.action == "click":
                            page.locator(step.selector).first.click(timeout=5_000)
                        else:
                            page.wait_for_timeout(step.ms)
                    page.wait_for_load_state("networkidle", timeout=15_000)
                    page.wait_for_timeout(runtime.settle_ms)
                except Exception as error:  # noqa: BLE001 - a broken page is an observation, not a runner failure
                    observation.failure = f"{type(error).__name__}: {str(error).splitlines()[0]}"
                observation.snapshot = page.evaluate(_SNAPSHOT)
                if not observation.failure:
                    try:
                        page.reload(wait_until="networkidle", timeout=60_000)
                        page.wait_for_timeout(runtime.settle_ms)
                        observation.snapshot_reloaded = page.evaluate(_SNAPSHOT)
                    except Exception as error:  # noqa: BLE001 - same as above
                        observation.failure = f"reload: {type(error).__name__}: {str(error).splitlines()[0]}"
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
    if (
        mutated.snapshot != baseline.snapshot
        or mutated.snapshot_loaded != baseline.snapshot_loaded
        or mutated.snapshot_reloaded != baseline.snapshot_reloaded
    ):
        result.output_differs = True
    return result
