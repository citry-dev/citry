from __future__ import annotations

import argparse
import os
import shutil
import signal
import socket
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .catalog import ExampleProject, select_projects

if TYPE_CHECKING:
    from collections.abc import Iterator

COPY_IGNORES = shutil.ignore_patterns(
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "_build",
    "*.pyc",
    "*.pyo",
)
TEST_SECRET = "qualification-only-citry-secret"  # noqa: S105 - fixed, test-only value


def project_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("VIRTUAL_ENV", None)
    environment.update(
        {
            "CITRY_SECRET": TEST_SECRET,
            "DJANGO_SECRET_KEY": TEST_SECRET,
            "PYTHONUNBUFFERED": "1",
        }
    )
    return environment


def copy_project(project: ExampleProject, root: Path) -> Path:
    destination = root / project.id
    shutil.copytree(project.source, destination, ignore=COPY_IGNORES)
    for required in ("README.md", "pyproject.toml", "uv.lock", "tests"):
        if not (destination / required).exists():
            raise RuntimeError(f"{project.id}: copied project is missing {required}")
    return destination


def run_checked(command: tuple[str, ...] | list[str], cwd: Path, environment: dict[str, str]) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode:
        rendered = " ".join(command)
        raise RuntimeError(f"Command failed in {cwd} ({result.returncode}): {rendered}\n{result.stdout}")


def install_project(
    project_dir: Path,
    environment: dict[str, str],
    python: str | None,
    editable_root: Path | None,
    wheels: list[Path],
) -> None:
    command = ["uv", "sync", "--frozen", "--dev"]
    if python:
        command.extend(("--python", python))
    run_checked(command, project_dir, environment)

    if editable_root is not None and wheels:
        raise ValueError("Use either --editable-root or --wheel, not both")
    if editable_root is not None:
        run_checked(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(project_dir / ".venv" / "bin" / "python"),
                "--reinstall",
                "--no-deps",
                "--editable",
                str(editable_root / "packages/py/citry_core"),
                "--editable",
                str(editable_root / "packages/py/citry"),
            ],
            project_dir,
            environment,
        )
    elif wheels:
        run_checked(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(project_dir / ".venv" / "bin" / "python"),
                "--reinstall",
                *map(str, wheels),
            ],
            project_dir,
            environment,
        )


def allocate_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def interpolate(command: tuple[str, ...], port: int) -> list[str]:
    return [part.replace("{port}", str(port)) for part in command]


def fetch(url: str, timeout: float = 2) -> tuple[int, str, bytes]:
    request = Request(  # noqa: S310 - the caller supplies a loopback or local test URL
        url,
        headers={"User-Agent": "citry-example-qualification"},
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - loopback/test URLs only
        return response.status, response.headers.get("Content-Type", ""), response.read()


@contextmanager
def running_server(
    project: ExampleProject,
    project_dir: Path,
    environment: dict[str, str],
    timeout: float,
) -> Iterator[str]:
    if project.serve is None:
        raise ValueError(f"{project.id}: no server command is configured")
    port = allocate_port()
    command = interpolate(project.serve, port)
    log = tempfile.TemporaryFile(mode="w+", encoding="utf-8")  # noqa: SIM115 - closed after yielded server
    process = subprocess.Popen(
        command,
        cwd=project_dir,
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    page_path = project.page_path or "/"
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    ready = False
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            try:
                status, content_type, body = fetch(base_url + page_path)
                if status == 200:
                    if "text/html" not in content_type:
                        raise RuntimeError(f"{project.id}: page returned unexpected content type {content_type!r}")
                    if b"Project Explorer" not in body and b"Launch workspace" not in body:
                        raise RuntimeError(f"{project.id}: page sentinel is missing")
                    ready = True
                    break
            except (OSError, HTTPError, URLError) as error:
                last_error = error
                time.sleep(0.05)
        if not ready:
            log.seek(0)
            output = log.read()
            raise RuntimeError(
                f"{project.id}: server did not become ready; last error={last_error!r}\n"
                f"command={' '.join(command)}\n{output}"
            )

        prefix = project.citry_prefix or "/citry"
        status, content_type, _body = fetch(base_url + prefix + "/citry.js")
        if status != 200 or "javascript" not in content_type:
            raise RuntimeError(f"{project.id}: runtime returned {status} {content_type!r}")
        yield base_url
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        log.close()


def _browser_problems(page: Any) -> tuple[list[str], list[str], list[str]]:
    console_errors: list[str] = []
    page_errors: list[str] = []
    failed_requests: list[str] = []

    def on_console(message: Any) -> None:
        if message.type == "error" and "Failed to load resource" not in message.text:
            console_errors.append(message.text)

    page.on("console", on_console)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on("requestfailed", lambda request: failed_requests.append(request.url))
    return console_errors, page_errors, failed_requests


def browser_starter(base_url: str, browser_name: str) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = getattr(playwright, browser_name).launch()
        page = browser.new_page()
        console_errors, page_errors, failed_requests = _browser_problems(page)
        event_requests = []
        page.on(
            "request",
            lambda request: event_requests.append(request.url)
            if request.method == "POST" and "/ext/events/" in request.url
            else None,
        )
        page.goto(base_url + "/", wait_until="networkidle")
        page.wait_for_function("window.Alpine && window.Citry && Citry.events")

        page.get_by_role("button", name="Show how it works").click()
        page.get_by_text("Two kinds of interaction share this component.").wait_for()
        if event_requests:
            raise AssertionError("The local Alpine help interaction sent an Event request")

        search = page.get_by_role("searchbox", name="Filter projects")
        search.fill("incident")
        page.get_by_text("1 matching projects").wait_for()
        page.get_by_role("heading", name="Beacon").wait_for()
        if search.input_value() != "incident" or not search.evaluate("element => element === document.activeElement"):
            raise AssertionError("The Events morph did not preserve search value and focus")
        if len(event_requests) != 1:
            raise AssertionError(f"Expected one debounced Event request, saw {event_requests}")
        if console_errors or page_errors or failed_requests:
            raise AssertionError(
                f"Browser errors: console={console_errors}, page={page_errors}, requests={failed_requests}"
            )
        browser.close()


def browser_demo(base_url: str, browser_name: str) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = getattr(playwright, browser_name).launch()
        page = browser.new_page()
        console_errors, page_errors, failed_requests = _browser_problems(page)
        page.goto(base_url + "/", wait_until="networkidle")
        page.wait_for_function("window.Alpine && window.Citry && Citry.events")

        page.get_by_role("button", name="How this works").click()
        page.get_by_text("Filters call Python because they change server data.").wait_for()

        search = page.get_by_role("searchbox", name="Search board")
        search.fill("keyboard")
        page.get_by_role("heading", name="Review keyboard navigation").wait_for()
        search.fill("")
        page.get_by_role("heading", name="Map the onboarding journey").wait_for()

        title = page.get_by_role("textbox", name="Task title")
        title.fill("x")
        page.get_by_role("button", name="Add task").click()
        page.get_by_text("Use at least four characters.").wait_for()
        if title.input_value() != "x":
            raise AssertionError("Validation failure did not preserve the typed title")

        title.fill("Plan release notes")
        page.get_by_label("Lane").select_option("review")
        page.get_by_label("Priority").select_option("high")
        page.get_by_role("button", name="Add task").click()
        card = page.locator("article.task-card", has_text="Plan release notes")
        card.wait_for()
        page.get_by_text("Added “Plan release notes”.").wait_for()
        card.get_by_role("button", name="Mark complete").click()
        card.wait_for(state="detached")

        if console_errors or page_errors or failed_requests:
            raise AssertionError(
                f"Browser errors: console={console_errors}, page={page_errors}, requests={failed_requests}"
            )
        browser.close()


def browser_standalone(project_dir: Path, browser_name: str) -> None:
    from playwright.sync_api import sync_playwright

    document = project_dir / "_build" / "index.html"
    if not document.is_file():
        raise RuntimeError("Standalone build did not create _build/index.html")
    with sync_playwright() as playwright:
        browser = getattr(playwright, browser_name).launch()
        page = browser.new_page()
        console_errors, page_errors, failed_requests = _browser_problems(page)
        network_requests = []
        page.on(
            "request",
            lambda request: network_requests.append(request.url)
            if request.url.startswith(("http://", "https://"))
            else None,
        )
        page.goto(document.resolve().as_uri())
        page.wait_for_function("window.Alpine")
        page.get_by_role("button", name="Show how it works").click()
        page.get_by_text("This toggle stays in the browser.").wait_for()
        if network_requests or console_errors or page_errors or failed_requests:
            raise AssertionError(
                "Standalone browser problems: "
                f"network={network_requests}, console={console_errors}, "
                f"page={page_errors}, requests={failed_requests}"
            )
        browser.close()


def qualify_project(
    project: ExampleProject,
    project_dir: Path,
    environment: dict[str, str],
    browser: str | None,
    timeout: float,
) -> None:
    run_checked(project.test, project_dir, environment)
    if project.build is not None:
        run_checked(project.build, project_dir, environment)
        if browser:
            browser_standalone(project_dir, browser)
        return
    with running_server(project, project_dir, environment, timeout) as base_url:
        if browser:
            if project.kind == "demo":
                browser_demo(base_url, browser)
            else:
                browser_starter(base_url, browser)


def main() -> None:
    parser = argparse.ArgumentParser(description="Qualify copied Citry example projects")
    parser.add_argument("--project", action="append", dest="projects")
    parser.add_argument("--python", help="Python request passed to uv sync")
    parser.add_argument("--editable-root", type=Path)
    parser.add_argument("--wheel", action="append", default=[], type=Path)
    parser.add_argument("--browser", choices=("chromium", "firefox", "webkit"))
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args()

    environment = project_environment()
    with tempfile.TemporaryDirectory(prefix="citry-examples-") as temp:
        root = Path(temp)
        for project in select_projects(args.projects):
            print(f"Qualifying {project.id}")
            project_dir = copy_project(project, root)
            install_project(
                project_dir,
                environment,
                args.python,
                args.editable_root.resolve() if args.editable_root else None,
                [wheel.resolve() for wheel in args.wheel],
            )
            qualify_project(
                project,
                project_dir,
                environment,
                args.browser,
                args.timeout,
            )
            print(f"Passed {project.id}")


if __name__ == "__main__":
    main()
