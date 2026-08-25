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
AXE_PATH = Path(__file__).resolve().parents[2] / "node_modules" / "axe-core" / "axe.min.js"

PAGE_SENTINELS = {
    "starter-web-v1": b"Project Explorer",
    "demo-project-board-v1": b"Launch workspace",
    "demo-htmx-v1": b"HTMX + Citry patterns",
}

STARTER_HOST_COPY = {
    "fastapi": ("FastAPI starter", "Citry FastAPI starter"),
    "django": ("Django starter", "Citry Django starter"),
    "flask": ("Flask starter", "Citry Flask starter"),
    "asgi": ("Bare ASGI starter", "Citry bare ASGI starter"),
    "wsgi": ("Bare WSGI starter", "Citry bare WSGI starter"),
}


def axe_high_impact_findings(page: Any) -> list[dict[str, object]]:
    if not AXE_PATH.is_file():
        raise RuntimeError("Run `pnpm install` before checking examples for accessibility problems.")
    if not page.evaluate("Boolean(window.axe)"):
        page.add_script_tag(path=str(AXE_PATH))
    return page.evaluate(
        """async () => {
          const result = await axe.run(document, {resultTypes: ["violations"]});
          return result.violations
            .filter(({impact}) => impact === "serious" || impact === "critical")
            .map(({id, impact, nodes}) => ({
              id,
              impact,
              targets: nodes.map(({target}) => target),
            }));
        }"""
    )


def project_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("VIRTUAL_ENV", None)
    environment.update(
        {
            "CITRY_SECRET": TEST_SECRET,
            "DJANGO_SECRET_KEY": TEST_SECRET,
            "PYTHONUNBUFFERED": "1",
            # install_project() may replace the locked Citry package with
            # editable sources or candidate wheels. UV_NO_SYNC keeps later
            # `uv run` commands from restoring the lock.
            "UV_NO_SYNC": "1",
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
                    sentinel = PAGE_SENTINELS.get(project.profile)
                    if sentinel is None:
                        raise RuntimeError(f"{project.id}: no readiness sentinel for profile {project.profile!r}")
                    if sentinel not in body:
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


def assert_starter_visual_contract(page: Any) -> None:
    styles = page.evaluate(
        """() => {
          const root = getComputedStyle(document.documentElement);
          return {
            colorScheme: root.colorScheme,
            pageColor: root.getPropertyValue("--color-page").trim(),
            backgroundImage: getComputedStyle(document.body).backgroundImage,
            headerPosition: getComputedStyle(document.querySelector(".site-header")).position,
            headingFont: getComputedStyle(document.querySelector("h1")).fontFamily,
            cardShadow: getComputedStyle(document.querySelector(".project-card")).boxShadow,
          };
        }"""
    )
    expected = {
        "colorScheme": "light",
        "pageColor": "oklch(96.5% 0.005 250)",
        "backgroundImage": "none",
        "headerPosition": "fixed",
        "cardShadow": "none",
    }
    differences = {key: styles[key] for key, value in expected.items() if styles[key] != value}
    if differences:
        raise AssertionError(f"The starter does not match Citry's visual contract: {differences!r}")
    if "system-ui" not in styles["headingFont"]:
        raise AssertionError(
            f"The starter heading does not use the Citry system font stack: {styles['headingFont']!r}"
        )

    page.set_viewport_size({"width": 390, "height": 844})
    viewport = page.evaluate(
        """() => ({
          clientWidth: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
        })"""
    )
    if viewport["scrollWidth"] > viewport["clientWidth"]:
        raise AssertionError(f"The starter overflows its mobile viewport: {viewport!r}")


def browser_starter(project: ExampleProject, base_url: str, browser_name: str) -> None:
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
        expected_mode, expected_eyebrow = STARTER_HOST_COPY[project.host]
        if page.locator(".mode-label").text_content() != expected_mode:
            raise AssertionError(f"{project.id}: the header does not name its host")
        if page.locator(".eyebrow").inner_text() != expected_eyebrow:
            raise AssertionError(f"{project.id}: the page introduction does not name its host")
        accessibility_findings = axe_high_impact_findings(page)
        if accessibility_findings:
            raise AssertionError(
                f"Axe found serious or critical accessibility problems on the starter page: {accessibility_findings}"
            )

        page.get_by_role("button", name="How this page works").click()
        page.get_by_text("The help button and search take different paths.").wait_for()
        if event_requests:
            raise AssertionError("Opening the help panel sent a request to the Events endpoint")

        search = page.get_by_role("searchbox", name="Filter projects")
        search.fill("incident")
        page.get_by_text("1 matching project", exact=True).wait_for()
        page.get_by_role("heading", name="Beacon").wait_for()
        if search.input_value() != "incident" or not search.evaluate("element => element === document.activeElement"):
            raise AssertionError("Updating the search results changed the query or moved keyboard focus")
        if len(event_requests) != 1:
            raise AssertionError(f"Expected search to send one Event request, saw {event_requests}")

        # Remove every ProjectCard so the manager drops its class stylesheet.
        # Clearing the search must then fetch that stylesheet before showing
        # cards again.
        search.fill("no-project-can-match-this-query")
        page.get_by_text("0 matching projects", exact=True).wait_for()
        page.wait_for_function("!document.querySelector('[data-citry-css-class^=ProjectCard_]')")
        search.fill("")
        page.get_by_text("6 matching projects", exact=True).wait_for()
        page.locator(".project-card").first.wait_for()
        page.wait_for_function(
            """() => {
              const card = document.querySelector('.project-card');
              return card && getComputedStyle(card).display === 'grid';
            }"""
        )
        restored_card_style = page.locator(".project-card").first.evaluate(
            "element => ({ display: getComputedStyle(element).display, padding: getComputedStyle(element).padding })"
        )
        if restored_card_style["display"] != "grid" or restored_card_style["padding"] == "0px":
            raise AssertionError(
                "ProjectCard styling was not restored after the empty result removed its class CSS: "
                f"{restored_card_style!r}"
            )
        if len(event_requests) != 3:
            raise AssertionError(f"Expected three search Event requests, saw {event_requests}")

        page.reload(wait_until="networkidle")
        page.wait_for_function("window.Alpine && window.Citry && Citry.events")
        page.get_by_text("6 matching projects", exact=True).wait_for()
        if page.get_by_role("searchbox", name="Filter projects").input_value():
            raise AssertionError("Reload did not restore the empty initial query")
        if page.locator(".project-card").count() != 6:
            raise AssertionError("Reload did not restore the deterministic initial project list")
        if page.locator("#explorer-help").is_visible():
            raise AssertionError("Reload did not restore the closed help panel")
        if page.get_by_text("Searching…", exact=True).is_visible():
            raise AssertionError("Reload left the starter in its loading state")
        if len(event_requests) != 3:
            raise AssertionError(f"Reload unexpectedly sent another Event request: {event_requests}")
        if console_errors or page_errors or failed_requests:
            raise AssertionError(
                f"Browser errors: console={console_errors}, page={page_errors}, requests={failed_requests}"
            )
        assert_starter_visual_contract(page)
        browser.close()


def browser_project_board(base_url: str, browser_name: str) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = getattr(playwright, browser_name).launch()
        page = browser.new_page()
        console_errors, page_errors, failed_requests = _browser_problems(page)
        page.goto(base_url + "/", wait_until="networkidle")
        page.wait_for_function("window.Alpine && window.Citry && Citry.events")
        accessibility_findings = axe_high_impact_findings(page)
        if accessibility_findings:
            raise AssertionError(
                f"Axe found serious or critical accessibility problems on the Project Board: {accessibility_findings}"
            )

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


def browser_htmx(base_url: str, browser_name: str) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = getattr(playwright, browser_name).launch()
        page = browser.new_page()
        console_errors, page_errors, failed_requests = _browser_problems(page)
        fragment_requests: list[str] = []
        event_requests: list[str] = []

        def record_request(request: Any) -> None:
            if "/fragments/" in request.url:
                fragment_requests.append(request.url)
            if request.method == "POST" and "/ext/events/" in request.url:
                event_requests.append(request.url)

        page.on("request", record_request)
        page.goto(base_url + "/", wait_until="networkidle")
        page.wait_for_function("window.htmx && window.Citry")
        results = page.locator("#search-results")
        results.locator(".contact-results[data-citry-activated='all']").wait_for()
        initial_accessibility_findings = axe_high_impact_findings(page)
        if initial_accessibility_findings:
            raise AssertionError(
                "Axe found serious or critical accessibility problems on the initial HTMX page: "
                f"{initial_accessibility_findings}"
            )

        search = page.get_by_role("searchbox", name="Search by name, email, or team")
        with page.expect_request(lambda request: "/fragments/search?q=ada" in request.url.lower()):
            search.fill("ada")
        with page.expect_request(lambda request: "/fragments/search?q=grace" in request.url.lower()):
            search.fill("grace")
        results.get_by_text("Grace Hopper", exact=True).wait_for()
        results.locator(".contact-results[data-citry-activated='grace']").wait_for()
        if results.get_by_text("Ada Lovelace", exact=True).count():
            raise AssertionError("The slower Ada search overwrote the newer Grace result")
        page.wait_for_function(
            """() => {
                const element = document.querySelector('#search-results .contact-results');
                if (!element) return false;
                const styles = getComputedStyle(element);
                return styles.borderLeftStyle === 'solid' && Number.parseFloat(styles.borderLeftWidth) > 0;
            }"""
        )
        border = results.locator(".contact-results").evaluate(
            """element => {
                const styles = getComputedStyle(element);
                return {
                    style: styles.borderLeftStyle,
                    width: Number.parseFloat(styles.borderLeftWidth),
                };
            }"""
        )
        if border["style"] != "solid" or border["width"] <= 0:
            raise AssertionError(
                f"Expected a visible search-results border after Citry loaded its CSS, got {border!r}"
            )
        canceled_searches = [url for url in failed_requests if "/fragments/search?q=ada" in url.lower()]
        if not canceled_searches:
            raise AssertionError("HTMX did not cancel the slower Ada search")
        failed_requests[:] = [url for url in failed_requests if url not in canceled_searches]
        expected_abort_prefixes = ("htmx:afterRequest,", "htmx:sendAbort,")
        if not all(
            any(message.startswith(prefix) for message in console_errors) for prefix in expected_abort_prefixes
        ):
            raise AssertionError(f"HTMX did not report that it canceled the Ada search: {console_errors}")
        console_errors[:] = [message for message in console_errors if not message.startswith(expected_abort_prefixes)]

        with page.expect_request(lambda request: "/fragments/search?q=" in request.url.lower()):
            search.fill("")
        results.get_by_text("Ada Lovelace", exact=True).wait_for()
        results.locator(".contact-results[data-citry-activated='all']").wait_for()
        editor = results.locator("#contact-row-1")
        grace = results.locator("#contact-row-2")
        edit_button = editor.get_by_role("button", name="Edit Ada Lovelace")
        page.keyboard.press("Tab")
        if not edit_button.evaluate("element => element === document.activeElement"):
            raise AssertionError("Tab did not move from search to the first Edit button")
        page.keyboard.press("Enter")
        editor.get_by_role("heading", name="Edit Ada Lovelace").wait_for()
        grace.get_by_role("heading", name="Grace Hopper").wait_for()
        page.wait_for_function(
            "document.activeElement?.name === 'name' && document.activeElement.closest('#contact-row-1')"
        )
        form_style = page.locator("link[rel='stylesheet'][href*='ContactForm_']")
        form_style.wait_for(state="attached")
        page.wait_for_function(
            "getComputedStyle(document.querySelector('#contact-row-1 .contact-form')).display === 'grid'"
        )
        active_form_accessibility_findings = axe_high_impact_findings(page)
        if active_form_accessibility_findings:
            raise AssertionError(
                "Axe found serious or critical accessibility problems while the contact form was open: "
                f"{active_form_accessibility_findings}"
            )
        keyboard_targets = (
            (editor.get_by_label("Email"), "Email field"),
            (editor.get_by_label("Team"), "Team field"),
            (editor.get_by_role("button", name="Save contact"), "Save button"),
            (editor.get_by_role("button", name="Cancel"), "Cancel button"),
        )
        for target, label in keyboard_targets:
            page.keyboard.press("Tab")
            if not target.evaluate("element => element === document.activeElement"):
                raise AssertionError(f"Tab did not move focus to the {label}")
        page.keyboard.press("Enter")
        editor.get_by_role("heading", name="Ada Lovelace").wait_for()
        grace.get_by_role("heading", name="Grace Hopper").wait_for()
        form_style.wait_for(state="detached")

        editor.get_by_role("button", name="Edit Ada Lovelace").click()
        editor.get_by_role("heading", name="Edit Ada Lovelace").wait_for()
        form_style.wait_for(state="attached")
        page.wait_for_function(
            "document.activeElement?.name === 'name' && document.activeElement.closest('#contact-row-1')"
        )
        form_display = editor.locator(".contact-form").evaluate("element => getComputedStyle(element).display")
        if form_display != "grid":
            raise AssertionError(f"Expected the contact form to use display: grid, got {form_display!r}")
        name = editor.get_by_label("Name")
        email = editor.get_by_label("Email")
        name.fill("A")
        email.fill("broken")
        editor.get_by_role("button", name="Save contact").click()
        editor.get_by_text("Enter a name between 2 and 80 characters.").wait_for()
        editor.get_by_text("Enter a valid email address.").wait_for()
        invalid_form_accessibility_findings = axe_high_impact_findings(page)
        if invalid_form_accessibility_findings:
            raise AssertionError(
                "Axe found serious or critical accessibility problems after the form showed validation errors: "
                f"{invalid_form_accessibility_findings}"
            )

        editor.get_by_label("Name").fill("Ada Byron")
        editor.get_by_label("Email").fill("ada.byron@example.test")
        team_field = editor.get_by_label("Team")
        team_field.select_option("4")
        team_field.focus()
        page.keyboard.press("Tab")
        save_button = editor.get_by_role("button", name="Save contact")
        if not save_button.evaluate("element => element === document.activeElement"):
            raise AssertionError("Tab did not move from the team field to the Save button")
        page.keyboard.press("Enter")
        editor.get_by_role("heading", name="Ada Byron").wait_for()
        editor.get_by_text("Saved Ada Byron.").wait_for()
        editor.locator(".contact-detail[data-citry-contact='1']").wait_for()
        form_style.wait_for(state="detached")

        department = page.get_by_label("Department")
        team = page.get_by_label("Team", exact=True)
        team.wait_for()
        control_tops = page.locator("#department-choice, #team-choice").evaluate_all(
            "elements => elements.map(element => element.getBoundingClientRect().top)"
        )
        if abs(control_tops[0] - control_tops[1]) > 1:
            raise AssertionError(f"The department and team selects are not aligned: {control_tops!r}")
        if team.locator("option").all_text_contents() != [
            "Platform",
            "Developer Experience",
            "Infrastructure",
            "Security",
        ]:
            raise AssertionError("The initial Engineering team list is incomplete")
        if page.locator("#team-picker [role='status']").text_content() != "4 teams available":
            raise AssertionError("The Engineering team count is not visible")

        department.select_option("design")
        team.get_by_role("option", name="Product Design").wait_for(state="attached")
        if team.locator("option").all_text_contents() != ["Product Design", "Research"]:
            raise AssertionError("The team list did not update after choosing Design")
        if page.locator("#team-picker [role='status']").text_content() != "2 teams available":
            raise AssertionError("The Design team count did not update")

        department.select_option("operations")
        team.get_by_role("option", name="Customer Operations").wait_for(state="attached")
        if team.locator("option").all_text_contents() != ["Customer Operations"]:
            raise AssertionError("The team list did not update after choosing Operations")
        if page.locator("#team-picker [role='status']").text_content() != "1 team available":
            raise AssertionError("The Operations team count did not update")

        required_paths = ("/fragments/search", "/edit", "/fragments/contacts/1", "/fragments/team-picker")
        missing_paths = [path for path in required_paths if not any(path in url for url in fragment_requests)]
        if missing_paths:
            raise AssertionError(f"The browser did not send these HTMX requests: {missing_paths}")
        if event_requests:
            raise AssertionError(f"The browser sent Citry Events requests during the HTMX demo: {event_requests}")
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
        accessibility_findings = axe_high_impact_findings(page)
        if accessibility_findings:
            raise AssertionError(
                "Axe found serious or critical accessibility problems on the standalone starter page: "
                f"{accessibility_findings}"
            )
        page.get_by_role("button", name="How this page works").click()
        page.get_by_text("Opening this panel does not call Python.").wait_for()
        if network_requests or console_errors or page_errors or failed_requests:
            raise AssertionError(
                "Standalone browser problems: "
                f"network={network_requests}, console={console_errors}, "
                f"page={page_errors}, requests={failed_requests}"
            )
        assert_starter_visual_contract(page)
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
            if project.profile == "demo-project-board-v1":
                browser_project_board(base_url, browser)
            elif project.profile == "demo-htmx-v1":
                browser_htmx(base_url, browser)
            elif project.kind == "starter":
                browser_starter(project, base_url, browser)
            else:
                raise RuntimeError(f"{project.id}: no browser journey for profile {project.profile!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Qualify copied Citry example projects")
    parser.add_argument("--project", action="append", dest="projects")
    parser.add_argument("--python", help="Python version or interpreter passed to `uv sync --python`")
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
