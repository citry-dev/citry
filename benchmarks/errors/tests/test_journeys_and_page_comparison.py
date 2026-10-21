"""Journeys and page records decide if a missed mistake reads as "silently wrong" or "never", so both are tested."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest
import tomllib
from citry_errors import runtime
from citry_errors.compare import comparable, compare, problems
from citry_errors.config import (
    DEFAULT_JOURNEY,
    ConfigError,
    Runtime,
    Step,
    load_framework,
    load_frameworks,
    load_journeys,
)
from citry_errors.runtime import JourneyRecord, Observation
from citry_errors.score import RuntimeResult

if TYPE_CHECKING:
    from pathlib import Path

WHERE = "framework.toml [runtime.journeys]"


def _journeys(text: str) -> dict[str, tuple[Step, ...]]:
    return load_journeys(tomllib.loads(text), WHERE)


def test_journeys_read_every_step_kind_in_the_order_written() -> None:
    journeys = _journeys(
        """
        default = [{ action = "click", selector = "button:text-is('Add')" }, { action = "wait", ms = 500 }]
        search = [
          { action = "fill", selector = "input[name=q]", text = "alpha" },
          { action = "press", selector = "input[name=q]", key = "Enter" },
          { action = "press", key = "Tab" },
          { action = "fill", selector = "input[name=q]", text = "" },
        ]
        """
    )
    assert list(journeys) == [DEFAULT_JOURNEY, "search"]
    assert journeys["default"] == (Step("click", selector="button:text-is('Add')"), Step("wait", ms=500))
    assert journeys["search"] == (
        Step("fill", selector="input[name=q]", text="alpha"),
        Step("press", selector="input[name=q]", key="Enter"),
        # No selector: the key goes to whatever has focus.
        Step("press", key="Tab"),
        # Filling in empty text clears the field, which is a real step.
        Step("fill", selector="input[name=q]", text=""),
    )


@pytest.mark.parametrize(
    ("step", "message"),
    [
        ('{ action = "hover", selector = "a" }', "unknown action 'hover'"),
        ('{ selector = "a" }', "must be a table with an action"),
        ('{ action = "click" }', r"missing \['selector'\]"),
        ('{ action = "fill", selector = "input" }', r"missing \['text'\]"),
        ('{ action = "press" }', r"missing \['key'\]"),
        ('{ action = "wait" }', r"missing \['ms'\]"),
        # A key another action uses would otherwise be silently ignored.
        ('{ action = "click", selector = "a", ms = 500 }', r"unknown keys \['ms'\]"),
        ('{ action = "wait", ms = 500, selector = "a" }', r"unknown keys \['selector'\]"),
        ('{ action = "click", selector = "" }', "selector must be non-empty text"),
        ('{ action = "click", selector = 1 }', "selector must be non-empty text"),
        ('{ action = "press", key = "" }', "key must be non-empty text"),
        ('{ action = "fill", selector = "input", text = 1 }', "text must be text"),
        ('{ action = "wait", ms = 0 }', "ms must be a whole number"),
        ('{ action = "wait", ms = -5 }', "ms must be a whole number"),
        ('{ action = "wait", ms = 0.5 }', "ms must be a whole number"),
        ('{ action = "wait", ms = true }', "ms must be a whole number"),
        ('"click"', "must be a table with an action"),
    ],
)
def test_a_step_that_cannot_run_as_written_is_rejected_with_its_place(step: str, message: str) -> None:
    with pytest.raises(ConfigError, match=message) as caught:
        _journeys(f'default = [{{ action = "wait", ms = 1 }}]\nsearch = [{step}]')
    # The message names the journey and the step, so the typo can be found.
    assert "journey 'search' step 0" in str(caught.value)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('search = [{ action = "wait", ms = 1 }]', "needs a 'default' journey"),
        ("default = []", "journey 'default' must be a non-empty list"),
        ('default = { action = "wait", ms = 1 }', "journey 'default' must be a non-empty list"),
        ('default = [{ action = "wait", ms = 1 }]\nSearch = [{ action = "wait", ms = 1 }]', "journey name 'Search'"),
    ],
)
def test_a_journey_list_with_no_default_or_an_empty_or_misnamed_journey_is_rejected(text: str, message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        _journeys(text)


def test_journeys_must_be_a_table() -> None:
    with pytest.raises(ConfigError, match="must be a table of journey names"):
        load_journeys([{"action": "wait", "ms": 1}], WHERE)


def test_a_runtime_section_without_journeys_is_rejected_when_the_framework_loads(tmp_path: Path) -> None:
    root = tmp_path / "jinja"
    root.mkdir()
    (root / "framework.toml").write_text(
        'key = "jinja"\nname = "Jinja"\nstages = []\n'
        "[setup]\nmanifests = []\ncommand = []\n"
        '[runtime]\nargv = ["uvicorn"]\npage_path = "/"\n'
    )
    with pytest.raises(ConfigError, match=r"missing \['journeys'\]"):
        load_framework(root)


def test_every_framework_in_the_benchmark_has_a_default_journey() -> None:
    for framework in load_frameworks().values():
        assert framework.runtime is not None
        assert framework.runtime.journeys[DEFAULT_JOURNEY], framework.key


# One element as the page record stores it: tag, title, button type, color,
# display, visibility, border color, alt, id, aria-* pairs, disabled, and
# for an image whether it loaded.
BUTTON: list[Any] = [
    "BUTTON",
    None,
    "button",
    "rgb(0, 128, 0)",
    "inline-block",
    "visible",
    "rgb(0, 128, 0)",
    None,
    "details",
    [["aria-expanded", "false"]],
    False,
    None,
]


@pytest.mark.parametrize(
    ("index", "value"),
    [
        (6, "rgb(0, 0, 255)"),
        (7, "Ada"),
        (8, "board"),
        (9, [["aria-expandd", "false"]]),
        (9, [["aria-expanded", "yes"]]),
        (10, True),
    ],
    ids=["border-color", "alt", "id", "aria-name", "aria-value", "disabled"],
)
def test_a_page_that_differs_only_in_one_recorded_attribute_is_silently_wrong(index: int, value: Any) -> None:
    changed = list(BUTTON)
    changed[index] = value
    clean = Observation(snapshot={"text": "Details", "elements": [BUTTON]})
    case = Observation(snapshot={"text": "Details", "elements": [changed]})
    assert compare(clean, case).output_differs
    assert compare(clean, Observation(snapshot={"text": "Details", "elements": [list(BUTTON)]})) == RuntimeResult()


def test_an_image_that_did_not_load_makes_the_page_differ() -> None:
    # The avatar of the clean page loaded; the case's page answered its path with a page instead.
    image: list[Any] = [
        "IMG",
        None,
        None,
        "rgb(0, 0, 0)",
        "inline",
        "visible",
        "rgb(0, 0, 0)",
        "Ada",
        None,
        [],
        False,
        True,
    ]
    broken = [*image[:11], False]
    clean = Observation(snapshot={"text": "", "elements": [image]})
    assert compare(clean, Observation(snapshot={"text": "", "elements": [broken]})).output_differs


def test_an_image_the_browser_never_requests_ends_the_wait_at_its_limit() -> None:
    """A lazy image out of view never loads; the record still returns, with the image not loaded."""
    playwright_api = pytest.importorskip("playwright.sync_api")
    gif = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    html = f'<img alt="Ada" loading="lazy" style="display: none" src="{gif}">'
    with playwright_api.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except playwright_api.Error as error:
            pytest.skip(f"Chromium is not installed: {error}")
        page = browser.new_page()
        page.set_content(html)
        [image] = page.evaluate(runtime._SNAPSHOT, 50)["elements"]
        browser.close()
    assert image[runtime._LOADED] is False


def _with(index: int, value: Any) -> dict:
    row = list(BUTTON)
    row[index] = value
    return {"text": "Details", "elements": [row]}


def test_an_id_made_up_on_every_render_does_not_make_the_same_page_differ() -> None:
    # Citry mounts an interactive page into an element with a random id.
    first = Observation(snapshot=_with(8, "citry-vue-" + "0123456789abcdef" * 2))
    second = Observation(snapshot=_with(8, "citry-vue-" + "fedcba9876543210" * 2))
    assert compare(first, second) == RuntimeResult()
    pointing = Observation(snapshot=_with(9, [["aria-controls", "panel-" + "a1" * 8]]))
    assert (
        compare(pointing, Observation(snapshot=_with(9, [["aria-controls", "panel-" + "b2" * 8]]))) == RuntimeResult()
    )


@pytest.mark.parametrize(("clean", "case"), [("board", "bored"), ("card-beef", "card-cafe"), ("item-1", "item-2")])
def test_an_id_a_developer_writes_is_compared_as_written(clean: str, case: str) -> None:
    assert compare(Observation(snapshot=_with(8, clean)), Observation(snapshot=_with(8, case))).output_differs


def test_a_missing_page_record_stays_missing() -> None:
    assert comparable(None) is None


def _page(text: str) -> dict:
    return {"text": text, "elements": [BUTTON]}


def test_a_difference_at_the_end_of_another_journey_counts() -> None:
    clean = Observation(journeys={"search": JourneyRecord(snapshot=_page("Searched: alpha"))})
    same = Observation(journeys={"search": JourneyRecord(snapshot=_page("Searched: alpha"))})
    other = Observation(journeys={"search": JourneyRecord(snapshot=_page("Searched:"))})
    assert compare(clean, same) == RuntimeResult()
    assert compare(clean, other).output_differs


def test_a_journey_step_only_the_case_could_not_take_is_a_visible_difference() -> None:
    clean = Observation(journeys={"search": JourneyRecord(snapshot=_page(""))})
    stuck = Observation(journeys={"search": JourneyRecord(snapshot=_page(""), failure="TimeoutError: fill")})
    result = compare(clean, stuck)
    assert result.output_differs
    assert result.evidence == ["interaction (search): TimeoutError: fill"]
    # When the clean page fails the same way, the failure says nothing about the case.
    clean_stuck = Observation(journeys={"search": JourneyRecord(snapshot=_page(""), failure="TimeoutError: fill")})
    assert compare(clean_stuck, stuck) == RuntimeResult()


def test_a_journey_the_case_never_reached_differs() -> None:
    clean = Observation(journeys={"search": JourneyRecord(snapshot=_page(""))})
    assert compare(clean, Observation()).output_differs


def test_a_failing_journey_is_reported_as_a_clean_app_problem() -> None:
    clean = Observation(journeys={"about": JourneyRecord(failure="TimeoutError: click")})
    assert problems(clean) == ["journey about: TimeoutError: click"]


def test_journey_records_are_written_with_the_observation() -> None:
    observation = Observation(journeys={"search": JourneyRecord(snapshot=_page("x"), failure="")})
    assert json.loads(observation.to_json())["journeys"] == {"search": {"failure": "", "snapshot": _page("x")}}


class _FakePage:
    """Stands in for a Playwright page and writes down every call the browser check makes."""

    def __init__(self, calls: list[str], name: str) -> None:
        self.calls, self.name = calls, name
        self.keyboard = self
        self.context = self
        self.first = self

    def _log(self, call: str) -> None:
        self.calls.append(f"{self.name}: {call}")

    def on(self, event: str, _handler: object) -> None:
        self._log(f"on {event}")

    def goto(self, _url: str, **_options: object) -> None:
        self._log("goto")

    def reload(self, **_options: object) -> None:
        self._log("reload")

    def wait_for_timeout(self, ms: int) -> None:
        self._log(f"wait {ms}")

    def wait_for_load_state(self, state: str, **_options: object) -> None:
        self._log(state)

    def evaluate(self, _script: str, _argument: object = None) -> dict:
        self._log("record")
        return {"text": str(len(self.calls)), "elements": []}

    def locator(self, selector: str) -> _FakePage:
        self._log(f"locator {selector}")
        return self

    def click(self, **_options: object) -> None:
        self._log("click")

    def fill(self, text: str, **_options: object) -> None:
        self._log(f"fill {text}")

    def press(self, key: str, **_options: object) -> None:
        self._log(f"press {key}")

    def close(self) -> None:
        self._log("close")


class _FakeBrowser:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.pages = 0

    def new_context(self) -> _FakeBrowser:
        return self

    def new_page(self) -> _FakePage:
        self.pages += 1
        return _FakePage(self.calls, f"page {self.pages}")


def test_the_default_journey_records_the_page_at_the_same_points_and_other_journeys_start_fresh() -> None:
    steps = {
        DEFAULT_JOURNEY: (Step("click", selector="button:text-is('Add')"), Step("wait", ms=500)),
        "search": (Step("fill", selector="input", text="alpha"), Step("press", key="Enter")),
    }
    settings = Runtime(argv=(), page_path="/", ready_timeout=1, journeys=steps, settle_ms=800)
    browser = _FakeBrowser()
    observation = Observation()
    runtime._default_journey(browser, "http://x/", settings, observation)  # type: ignore[arg-type]
    observation.journeys["search"] = runtime._journey(browser, "http://x/", steps["search"], 800, observation)  # type: ignore[arg-type]
    listen = ["on console", "on pageerror", "on response"]
    # The default journey records the page after the load, after the steps
    # and after a reload, each time after the settle wait.
    assert browser.calls == [
        *(f"page 1: {call}" for call in listen),
        "page 1: goto",
        "page 1: wait 800",
        "page 1: record",
        "page 1: locator button:text-is('Add')",
        "page 1: click",
        "page 1: wait 500",
        "page 1: networkidle",
        "page 1: wait 800",
        "page 1: record",
        "page 1: reload",
        "page 1: wait 800",
        "page 1: record",
        "page 1: close",
        *(f"page 2: {call}" for call in listen),
        "page 2: goto",
        "page 2: wait 800",
        "page 2: locator input",
        "page 2: fill alpha",
        "page 2: press Enter",
        "page 2: networkidle",
        "page 2: wait 800",
        "page 2: record",
        "page 2: close",
    ]
    assert not observation.failure
    assert observation.journeys["search"].snapshot is not None


def test_the_page_record_holds_the_columns_the_comparison_reads() -> None:
    """Run the record script in Chromium, so the column order the comparison relies on is the real one."""
    playwright_api = pytest.importorskip("playwright.sync_api")
    html = """
      <div id="board" style="border: 1px solid rgb(0, 0, 255)">Board</div>
      <img alt="Ada" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7">
      <img alt="Missing" src="data:image/gif;base64,bm90IGFuIGltYWdl">
      <button aria-expanded="false" aria-controls="details" disabled="false">Search</button>
    """
    with playwright_api.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except playwright_api.Error as error:
            pytest.skip(f"Chromium is not installed: {error}")
        page = browser.new_page()
        page.set_content(html)
        board, image, broken, button = page.evaluate(runtime._SNAPSHOT, runtime._IMAGE_WAIT_MS)["elements"]
        browser.close()
    assert board[0] == "DIV"
    assert board[6] == "rgb(0, 0, 255)"
    assert board[runtime._ID] == "board"
    assert image[7] == "Ada"
    # aria-* pairs are sorted by name, so the order they are written in does not matter.
    assert button[runtime._ARIA] == [["aria-controls", "details"], ["aria-expanded", "false"]]
    # `disabled="false"` disables the button, as it does for the user.
    assert button[10] is True
    # An image records whether it loaded; a file the browser cannot decode
    # loads as a broken image, as a misspelled path that the server answers
    # with a page does. Other elements record nothing there.
    assert (image[runtime._LOADED], broken[runtime._LOADED], button[runtime._LOADED]) == (True, False, None)


def test_an_image_still_loading_is_waited_for_before_the_page_is_recorded(tmp_path: Path) -> None:
    """An image whose file arrives after the page went quiet still records as loaded, not as broken."""
    playwright_api = pytest.importorskip("playwright.sync_api")
    gif = bytes.fromhex("47494638396101000100800000000000ffffff21f90401000000002c000000000100010000020144003b")
    with playwright_api.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except playwright_api.Error as error:
            pytest.skip(f"Chromium is not installed: {error}")
        page = browser.new_page()
        # The image's response is held back for half a second, well inside the wait.
        page.route(
            "**/slow.gif",
            lambda route: (page.wait_for_timeout(500), route.fulfill(body=gif, content_type="image/gif")),
        )
        page.route(
            "**/page", lambda route: route.fulfill(body='<img alt="Ada" src="/slow.gif">', content_type="text/html")
        )
        page.goto("http://example.test/page", wait_until="domcontentloaded")
        [image] = page.evaluate(runtime._SNAPSHOT, runtime._IMAGE_WAIT_MS)["elements"]
        browser.close()
    assert image[runtime._LOADED] is True
