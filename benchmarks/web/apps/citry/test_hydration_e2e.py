"""
Browser proof that the public board hydrates its server HTML and then behaves like a client mount.

Two uvicorn servers run ``hydration_test_server`` in subprocesses: one writes
every page for Vue to hydrate (threshold 0), the other serves the same board
with an empty Vue host for the browser to mount. The subprocesses keep the
board's Django configuration out of the pytest process. The test loads the
14-output board from both, checks that hydration kept every server element
without a mismatch, that both DOMs match, and that the same user actions,
including a server Render, give the same results.
"""

from __future__ import annotations

import importlib.util
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

pytest.importorskip("playwright.sync_api")
for _module in ("uvicorn", "django"):
    # Check only that the module exists, without importing it into the pytest process.
    if importlib.util.find_spec(_module) is None:
        pytest.skip(f"{_module} is not installed", allow_module_level=True)

pytestmark = pytest.mark.e2e

_APP_DIR = Path(__file__).parent
_OUTPUT_COUNT = 14
# Both servers keep their own in-memory model, so one session name gives
# both pages the same data and the same data-session attribute.
_SESSION = "hydration-e2e"

# Walk the Vue host in document order and describe what a user can observe.
# Two things differ by design and are left out: the shell marker
# (data-allow-mismatch, only on the hydrated side) and data-cid-* ids.
# Empty text nodes are skipped: a client mount marks where a list or fragment
# starts and ends with empty text nodes, while hydration keeps the server's
# comment nodes in those places.
_HOST_FACTS_JS = """() => {
  const host = document.querySelector('[id^="citry-vue-"]');
  const walker = document.createTreeWalker(host, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  const facts = [];
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (node.data !== '') facts.push({text: node.data});
      continue;
    }
    facts.push({
      tag: node.tagName.toLowerCase(),
      attrs: [...node.attributes]
        .filter(attr => attr.name !== 'data-allow-mismatch' && !attr.name.startsWith('data-cid-'))
        .map(attr => [attr.name, attr.value])
        .sort(([a], [b]) => a.localeCompare(b)),
      checked: 'checked' in node ? node.checked : null,
      value: 'value' in node && typeof node.value === 'string' ? node.value : null,
      display: getComputedStyle(node).display,
    });
  }
  return facts;
}"""

# Remember what the server wrote before the app starts, so the test can later
# prove hydration kept those exact nodes instead of building new ones.
_CAPTURE_SCRIPT = """<script>(() => {
  const host = document.querySelector('[id^="citry-vue-"]');
  window.__serverElements = [...host.querySelectorAll('*')];
  window.__serverHostHtml = host.innerHTML;
})();</script>"""


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _start_server(*, ssr: bool) -> tuple[subprocess.Popen[bytes], str]:
    """Start one board server and wait until its health route answers."""
    port = _free_port()
    # A file, not a pipe: nobody reads a pipe while the server runs, and a
    # full pipe would block the server on its next log line.
    log = tempfile.TemporaryFile()  # noqa: SIM115 - closed with the process below
    # Copy this process's environment without any CITRY_ setting or
    # DJANGO_SETTINGS_MODULE, so only the values below decide how the server renders.
    env = {key: value for key, value in os.environ.items() if not key.startswith("CITRY_")}
    env.pop("DJANGO_SETTINGS_MODULE", None)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(_APP_DIR), env.get("PYTHONPATH")]))
    env["BOARD_HYDRATION_TEST_SSR"] = "1" if ssr else "0"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "hydration_test_server:application",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=_APP_DIR,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    # The child keeps its own handle, so this process can drop its handle
    # once the server is known to be up.
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            log.seek(0)
            output = log.read().decode(errors="replace")
            log.close()
            pytest.fail(f"board server exited early ({process.returncode}):\n{output}")
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=1):  # noqa: S310 - local test server
                log.close()
                return process, url
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            time.sleep(0.1)
    process.terminate()
    process.wait(timeout=10)
    log.close()
    pytest.fail("board server did not answer /health within 30 seconds")


@pytest.fixture(scope="module")
def board_servers() -> Iterator[dict[str, str]]:
    """Yield base URLs of the hydrating server and the client-mount server."""
    processes: list[subprocess.Popen[bytes]] = []
    try:
        hydrate, hydrate_url = _start_server(ssr=True)
        processes.append(hydrate)
        client, client_url = _start_server(ssr=False)
        processes.append(client)
        yield {"hydrate": hydrate_url, "client": client_url}
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


@pytest.fixture
def board_context(browser: Any) -> Iterator[Any]:
    """Yield a fresh browser context that closes its pages even when the test fails."""
    context = browser.new_context()
    # A hydrating page then publishes window.__citryHydrationReport. The
    # client-mount page ignores the flag, which the test also checks.
    context.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    yield context
    context.close()


def _open_board(context: Any, base_url: str, *, capture: bool) -> tuple[Any, list[str], list[str], str]:
    """
    Load the board in a new page and wait for its app.

    Returns the page, its page errors, its console warnings and errors, and
    the HTML the server sent.
    """
    page = context.new_page()
    faults: list[str] = []
    console: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: console.append(message.text) if message.type in {"warning", "error"} else None)
    page.add_init_script(
        "window.__citryReadyApps = [];"
        "document.addEventListener('citry:ready', event => window.__citryReadyApps.push(event.detail.appId));"
    )
    served: dict[str, str] = {}
    url = f"{base_url}/?count={_OUTPUT_COUNT}&session={_SESSION}"

    def serve_document(route: Any) -> None:
        # Keep the server's bytes, adding only the capture script just before
        # the script tag that starts the app.
        response = route.fetch()
        html = response.text()
        served["html"] = html
        if capture:
            bootstrap_tag = html.index('<script type="application/json" data-citry-vue-document=')
            html = html[:bootstrap_tag] + _CAPTURE_SCRIPT + html[bootstrap_tag:]
        route.fulfill(response=response, body=html)

    page.route(url, serve_document)
    page.goto(url)
    page.wait_for_function("window.__citryReadyApps?.length === 1 && document.querySelector('#board')")
    return page, faults, console, served["html"]


def _board_interactions(page: Any) -> dict[str, Any]:
    """Run the board's local and server actions and report what a user would see after each."""
    observed: dict[str, Any] = {}
    page.click("[data-bench-action=disclosure]")
    observed["disclosure"] = page.evaluate(
        """() => [document.querySelector('#disclosure-content').hidden,
          document.querySelector('[data-bench-action=disclosure]').getAttribute('aria-expanded')]"""
    )
    page.click("#outputs article button[type=button]")
    observed["row_details"] = page.evaluate(
        """() => [document.querySelector('#outputs article button[type=button]').getAttribute('aria-expanded'),
          getComputedStyle(document.querySelector('#outputs article > div')).display]"""
    )
    page.click("#outputs section > button")
    observed["phase"] = page.evaluate(
        """() => [document.querySelector('#outputs section > button').getAttribute('aria-expanded'),
          getComputedStyle(document.querySelector('#outputs section > div')).display]"""
    )
    page.click("[data-tab-target=notes-1]")
    observed["tab"] = page.evaluate(
        "() => [getComputedStyle(document.querySelector('#notes-1')).display,"
        " getComputedStyle(document.querySelector('#outputs')).display]"
    )
    page.click("[data-tab-target=outputs]")
    # Each button submits its form, which Board handles with @c-submit; the
    # server's Render then bumps the board's revision. The phase toggle above
    # hid the first phase's rows, so pick the first row button still visible.
    for action in ("insert", "select"):
        revision = page.evaluate("document.querySelector('#board').dataset.revision")
        page.locator(f"#board form [data-bench-action^={action}]:visible").first.click()
        page.wait_for_function(
            "revision => document.querySelector('#board').dataset.revision !== revision", arg=revision
        )
        observed[action] = page.evaluate(
            """() => [document.querySelector('#board').dataset.revision,
              document.querySelector('#board').dataset.operation,
              document.querySelectorAll('#outputs article[data-row-id]').length,
              [...document.querySelectorAll('#outputs article[data-selected=true]')].map(row => row.id)]"""
        )
    return observed


def test_public_board_hydrates_and_matches_client_mount(board_context: Any, board_servers: dict[str, str]) -> None:
    client, client_faults, client_console, client_html = _open_board(
        board_context, board_servers["client"], capture=False
    )
    assert '"hydrate":true' not in client_html
    assert client.evaluate("window.__citryHydrationReport") is None
    client_facts = client.evaluate(_HOST_FACTS_JS)

    hydrated, faults, console, hydrated_html = _open_board(board_context, board_servers["hydrate"], capture=True)
    assert '"hydrate":true' in hydrated_html
    # Every value on this board is known to the server, so nothing is left
    # for Vue to build in a shell. Check only the host's own HTML:
    # the inlined runtime source names the marker too.
    host_html = hydrated.evaluate("window.__serverHostHtml")
    assert host_html
    assert "data-allow-mismatch" not in host_html
    hydrated.wait_for_function("window.__citryHydrationReport !== undefined")
    adoption = hydrated.evaluate(
        """() => {
          const host = document.querySelector('[id^="citry-vue-"]');
          return {probe: window.__citryHydrationReport,
            serverElementCount: window.__serverElements.length,
            allAdopted: (() => {
              // Each server element must still be in the host and in the same order;
              // Vue may add elements between them only inside shells.
              const current = [...host.querySelectorAll('*')];
              const positions = window.__serverElements.map(element => current.indexOf(element));
              return positions.every((position, index) =>
                position >= 0 && (index === 0 || position > positions[index - 1]));
            })()};
        }"""
    )
    probe = adoption["probe"]
    assert probe["mountError"] is None, probe
    assert probe["mismatchCount"] == 0, probe
    assert probe["replacedElementCount"] == 0, probe
    # Every element the server wrote is the node Vue kept.
    assert adoption["allAdopted"] is True
    assert probe["reusedElementCount"] == probe["beforeElementCount"] == adoption["serverElementCount"] > 0, adoption
    assert hydrated.evaluate(_HOST_FACTS_JS) == client_facts

    client_observed = _board_interactions(client)
    hydrated_observed = _board_interactions(hydrated)
    assert hydrated_observed == client_observed
    # Lock what the client mount did, so a no-op action cannot pass as
    # "the same on both pages": the insert adds a row and the select marks one.
    assert client_observed == {
        "disclosure": [False, "true"],
        "row_details": ["false", "none"],
        "phase": ["false", "none"],
        "tab": ["block", "none"],
        "insert": ["1", "manual", _OUTPUT_COUNT + 1, []],
        "select": ["2", "manual", _OUTPUT_COUNT + 1, ["row-2"]],
    }
    assert hydrated.evaluate(_HOST_FACTS_JS) == client.evaluate(_HOST_FACTS_JS)

    assert faults == [], faults
    assert console == [], console
    assert client_faults == [], client_faults
    assert client_console == [], client_console
