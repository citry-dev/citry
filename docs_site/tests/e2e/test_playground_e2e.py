"""Browser coverage for the shipped Pyodide playground path."""

from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

_CITRY_UI_TABS = (
    Path(__file__).parents[3] / "packages/py/citry_ui/citry_ui/components/ctabs/snippets/night_sky_guide.py"
)
_RUNTIME_PATH = Path(__file__).parents[2] / "static" / "playground" / "runtime.json"
_RUNTIME = json.loads(_RUNTIME_PATH.read_text(encoding="utf-8"))
_CITRY_VERSION = _RUNTIME["citry"]["version"]
_PUBLISHED_RUNTIME_LABEL = f"Citry {_CITRY_VERSION} · Citry UI {_RUNTIME['citry']['ui_version']}"
_LOCAL_RUNTIME_LABEL = f"Citry {_CITRY_VERSION} · Citry UI {version('citry-ui')}"


def _set_source(page: Any, source: str) -> None:
    page.evaluate("source => window.citryPlayground.setSource(source, false)", source)


def _run_and_wait(page: Any, *, timeout: int = 120_000) -> None:
    page.locator("#citry-playground-run").click()
    page.wait_for_function(
        "document.querySelector('#citry-playground-run').disabled === false",
        timeout=timeout,
    )


def _stall_preview_render(route: Any) -> None:
    route.fulfill(
        status=200,
        content_type="text/html",
        body="""<!doctype html><script>
          const ready = () => parent.postMessage({type: 'preview-ready', version: 1}, '*');
          addEventListener('message', (event) => {
            if (event.source !== parent) return;
            if (event.data?.type === 'preview-probe') ready();
            if (event.data?.type !== 'preview-connect' || event.ports.length !== 1) return;
            const port = event.ports[0];
            const session = event.data.session;
            port.onmessage = () => {};
            port.start();
            port.postMessage({type: 'preview-connected', version: 1, session});
            port.postMessage({type: 'preview-loaded', version: 1, session});
          });
          ready();
        </script>""",
    )


def _delay_preview_render(route: Any) -> None:
    route.fulfill(
        status=200,
        content_type="text/html",
        body="""<!doctype html><body><script>
          const ready = () => parent.postMessage({type: 'preview-ready', version: 1}, '*');
          addEventListener('message', (event) => {
            if (event.source !== parent) return;
            if (event.data?.type === 'preview-probe') ready();
            if (event.data?.type !== 'preview-connect' || event.ports.length !== 1) return;
            const port = event.ports[0];
            const session = event.data.session;
            port.onmessage = ({data}) => {
              if (data?.type !== 'render') return;
              const parsed = new DOMParser().parseFromString(data.html, 'text/html');
              document.body.replaceChildren(...parsed.body.childNodes);
              setTimeout(() => port.postMessage({
                type: 'preview-rendered', version: 1, session,
                runId: data.runId, nonce: data.nonce,
              }), 1000);
            };
            port.start();
            port.postMessage({type: 'preview-connected', version: 1, session});
            port.postMessage({type: 'preview-loaded', version: 1, session});
          });
          ready();
        </script></body>""",
    )


def test_playground_browser_ide_reports_completes_and_hovers(
    page: Any,
    docs_site_url: str,
) -> None:
    browser_messages: list[str] = []
    page.on("console", lambda message: browser_messages.append(f"{message.type}: {message.text}"))
    page.on("pageerror", lambda error: browser_messages.append(f"pageerror: {error}"))
    page.goto(docs_site_url + "/playground/", wait_until="domcontentloaded")
    page.wait_for_function("window.citryPlayground !== undefined")
    page.locator("#citry-playground-auto-run").uncheck()
    invalid = '''from citry import Component


class Card(Component):
    template = """
      <c-if>
    """


Card()
'''
    _set_source(page, invalid)
    try:
        page.wait_for_function("document.querySelectorAll('.cm-lintRange-error').length > 0", timeout=120_000)
    except PlaywrightTimeoutError:
        pytest.fail("Citry browser analysis did not report a diagnostic:\n" + "\n".join(browser_messages))

    incomplete = invalid.replace("<c-if>", "<c-i")
    _set_source(page, incomplete)
    cursor = incomplete.index("<c-i") + len("<c-i")
    assert page.evaluate("position => window.citryPlayground.setCursor(position)", cursor)
    page.keyboard.press("Control+Space")
    completion = page.locator(".cm-tooltip-autocomplete li", has_text="c-if")
    expect(completion).to_be_visible(timeout=120_000)
    page.keyboard.press("Escape")

    valid = invalid.replace("<c-if>", '<c-if cond="True"></c-if>')
    _set_source(page, valid)
    expect(page.locator(".cm-lintRange-error")).to_have_count(0, timeout=120_000)
    page.locator(".cm-citry-name", has_text="c-if").first.hover()
    expect(page.locator(".cm-citry-ide-hover")).to_contain_text("Conditional branch", timeout=120_000)

    registered = '''from citry import Component


class ProfileCard(Component):
    """Show one member profile."""

    class Kwargs:
        title: str

    template = "<p>{{ title }}</p>"


class Page(Component):
    template = """
      <main><c-ProfileCard title="Ada" /></main>
    """


Page()
'''
    _set_source(page, registered)
    _run_and_wait(page)
    page.locator(".cm-citry-name", has_text="c-ProfileCard").hover()
    component_hover = page.locator(".cm-citry-ide-hover")
    try:
        expect(component_hover).to_contain_text("ProfileCard", timeout=20_000)
    except AssertionError:
        pytest.fail("Registered component hover did not appear:\n" + "\n".join(browser_messages))
    expect(component_hover).to_contain_text("Inputs: title.")


def test_local_authoring_runtime_runs_workspace_citry_ui(page: Any, local_docs_site_url: str) -> None:
    console_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.goto(local_docs_site_url + "/playground/", wait_until="domcontentloaded")
    page.wait_for_function("window.citryPlayground !== undefined")
    _set_source(page, _CITRY_UI_TABS.read_text(encoding="utf-8"))

    _run_and_wait(page)
    _run_and_wait(page)
    expect(page.locator("#citry-playground-runtime")).to_have_text(_LOCAL_RUNTIME_LABEL)

    preview = page.frame_locator("#citry-playground-preview")
    tabs = preview.locator('[role="tab"]')
    expect(tabs).to_have_count(3, timeout=120_000)
    expect(tabs.nth(0)).to_have_attribute("aria-selected", "true")
    tabs.nth(1).click()
    expect(tabs.nth(1)).to_have_attribute("aria-selected", "true")
    expect(preview.locator('[role="tabpanel"]:not([hidden])')).to_contain_text("Finding nebulae")
    assert console_errors == []


def test_published_runtime_runs_citry_ui_twice(page: Any, docs_site_url: str) -> None:
    console_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.goto(docs_site_url + "/playground/", wait_until="domcontentloaded")
    page.wait_for_function("window.citryPlayground !== undefined")
    _set_source(page, _CITRY_UI_TABS.read_text(encoding="utf-8"))

    _run_and_wait(page)
    _run_and_wait(page)
    expect(page.locator("#citry-playground-runtime")).to_have_text(_PUBLISHED_RUNTIME_LABEL)

    preview = page.frame_locator("#citry-playground-preview")
    tabs = preview.locator('[role="tab"]')
    expect(tabs).to_have_count(3, timeout=120_000)
    tabs.nth(1).click()
    expect(tabs.nth(1)).to_have_attribute("aria-selected", "true")
    expect(preview.locator('[role="tabpanel"]:not([hidden])')).to_contain_text("Finding nebulae")
    assert console_errors == []


def test_published_runtime_resolves_a_direct_ui_component(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/playground/", wait_until="domcontentloaded")
    page.wait_for_function("window.citryPlayground !== undefined")
    _set_source(
        page,
        """from citry_ui import CButton

CButton(slots={"default": "Save changes"})
""",
    )

    _run_and_wait(page)
    _run_and_wait(page)

    preview = page.frame_locator("#citry-playground-preview")
    button = preview.locator("button", has_text="Save changes")
    expect(button).to_be_visible(timeout=120_000)
    expect(button).to_have_class("cui-button")


def test_published_runtime_activates_inline_citry_ui(page: Any, docs_site_url: str) -> None:
    console_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(f"{message.location}: {message.text}")
        if message.type == "error"
        else None,
    )
    page.goto(docs_site_url + "/ui-library/components/tabs/", wait_until="domcontentloaded")
    root = page.locator("[data-citry-ui-demo]").nth(1)
    built_preview = root.locator("[data-ui-preview-frame]")

    expect(built_preview).to_be_visible()
    expect(root.locator("[data-live-activate]")).to_be_visible()
    root.locator("[data-live-activate]").click()
    expect(root.locator(".cm-content")).to_be_attached(timeout=15_000)
    expect(root.locator("[data-live-fallback]")).to_have_value(_CITRY_UI_TABS.read_text(encoding="utf-8"))
    expect(built_preview).to_be_hidden()
    page.wait_for_function(
        """root => {
          const status = root.querySelector('[data-live-status]')?.textContent || '';
          return status.includes('Rendered in') || status === 'Runner unavailable';
        }""",
        arg=root.element_handle(),
        timeout=120_000,
    )
    if root.locator("[data-live-status]").text_content() == "Runner unavailable":
        summary = root.locator("[data-live-python-summary]").text_content()
        details = root.locator("[data-live-python-details]").text_content()
        pytest.fail(f"Published Citry UI runtime failed: {summary}\n{details}")

    run = root.locator("[data-live-run]")
    run.click()
    expect(run).to_be_disabled()
    expect(run).to_be_enabled(timeout=120_000)

    root.locator('[data-live-tab="result"]').click()
    preview = root.frame_locator(".citry-live-code__preview:not(.citry-playground__preview--candidate)")
    tabs = preview.locator('[role="tab"]')
    expect(tabs).to_have_count(3, timeout=120_000)
    tabs.nth(1).click()
    expect(tabs.nth(1)).to_have_attribute("aria-selected", "true")
    expect(preview.locator('[role="tabpanel"]:not([hidden])')).to_contain_text("Finding nebulae")
    root.locator("[data-live-close]").click()
    expect(built_preview).to_be_visible()
    expect(root.locator("[data-live-activate]")).to_be_focused()
    assert console_errors == []


def test_playground_runs_edits_reports_errors_and_recovers(
    page: Any,
    docs_site_url: str,
) -> None:
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(docs_site_url + "/playground/", wait_until="domcontentloaded")
    page.wait_for_function("window.citryPlayground !== undefined")

    assert page.locator(".cm-editor").count() == 1
    assert page.locator(".cm-citry-interpolation").count() >= 1
    assert page.locator(".cm-citry-function").count() >= 2
    assert page.locator("#citry-playground-auto-run").is_checked()
    assert set(page.locator("#citry-playground-preview").get_attribute("sandbox").split()) == {
        "allow-forms",
        "allow-scripts",
    }
    stop = page.locator("#citry-playground-stop")
    assert stop.is_visible()

    for control, label in (
        ("run", "Run Python"),
        ("stop", "Stop Python"),
        ("copy-code", "Copy code"),
        ("download-code", "Download code"),
        ("reset", "Reset code"),
        ("help", "Playground help"),
        ("copy-python-error", "Copy Python diagnostic"),
        ("dismiss-python", "Close Python diagnostic"),
        ("copy-preview-error", "Copy Result diagnostic"),
        ("dismiss-preview", "Close Result diagnostic"),
    ):
        button = page.locator(f"#citry-playground-{control}")
        assert button.get_attribute("aria-label") == label
        assert button.inner_text().strip() == ""

    help_dialog = page.locator("#citry-playground-help-dialog")
    help_content = help_dialog.locator("article.prose")
    page.locator("#citry-playground-help").click()
    assert help_dialog.evaluate("dialog => dialog.open")
    assert help_content.is_visible()
    assert help_content.evaluate("content => getComputedStyle(content).fontSize") == page.locator("body").evaluate(
        "body => getComputedStyle(body).fontSize"
    )
    help_content.click(position={"x": 8, "y": 8})
    assert help_dialog.evaluate("dialog => dialog.open")
    dialog_box = help_dialog.bounding_box()
    assert dialog_box is not None
    page.mouse.click(max(1, dialog_box["x"] - 10), dialog_box["y"] + dialog_box["height"] / 2)
    page.wait_for_function("!document.querySelector('#citry-playground-help-dialog').open")

    page.locator("#citry-playground-help").click()
    page.locator("#citry-playground-close-help").click()
    assert not help_dialog.evaluate("dialog => dialog.open")
    page.locator("#citry-playground-help").click()
    page.locator("#citry-playground-close-help-footer").click()
    assert not help_dialog.evaluate("dialog => dialog.open")
    page.locator("#citry-playground-help").click()
    page.keyboard.press("Escape")
    assert not help_dialog.evaluate("dialog => dialog.open")

    editor_colors = {}
    for theme in ("light", "dark"):
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        editor_colors[theme] = page.evaluate(
            """() => {
              const color = (selector) => getComputedStyle(document.querySelector(selector)).color;
              const canvas = document.createElement('canvas');
              canvas.width = canvas.height = 1;
              const context = canvas.getContext('2d');
              const rgb = (value) => {
                context.clearRect(0, 0, 1, 1);
                context.fillStyle = value;
                context.fillRect(0, 0, 1, 1);
                return [...context.getImageData(0, 0, 1, 1).data].slice(0, 3).map(x => x / 255);
              };
              const luminance = (value) => {
                const channels = rgb(value).map(x => x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4);
                return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2];
              };
              const background = luminance(getComputedStyle(document.querySelector('.cm-editor')).backgroundColor);
              const contrast = (selector) => {
                const foreground = luminance(color(selector));
                return (Math.max(foreground, background) + .05) / (Math.min(foreground, background) + .05);
              };
              const tokenContrasts = [...document.querySelectorAll('.cm-line span')]
                .filter(token => token.textContent.trim())
                .map(token => {
                  const foreground = luminance(getComputedStyle(token).color);
                  return {
                    contrast: (Math.max(foreground, background) + .05) / (Math.min(foreground, background) + .05),
                    text: token.textContent,
                  };
                });
              const lowestToken = tokenContrasts.reduce(
                (lowest, token) => token.contrast < lowest.contrast ? token : lowest,
                {contrast: Number.POSITIVE_INFINITY, text: ''},
              );
              return {
                base: color('.cm-content'),
                function: color('.cm-citry-function'),
                functionContrast: contrast('.cm-citry-function'),
                interpolation: color('.cm-citry-interpolation'),
                interpolationContrast: contrast('.cm-citry-interpolation'),
                keyword: color('.cm-citry-keyword'),
                lowestToken,
                staleContrast: contrast('#citry-playground-stale'),
                string: color('.cm-citry-string'),
                tagContrast: contrast('.cm-citry-tag'),
              };
            }"""
        )
        token_colors = {value for value in editor_colors[theme].values() if isinstance(value, str)}
        assert len(token_colors) >= 3
        assert editor_colors[theme]["function"] != editor_colors[theme]["base"]
        assert editor_colors[theme]["functionContrast"] >= 4.5
        assert editor_colors[theme]["interpolation"] != editor_colors[theme]["base"]
        assert editor_colors[theme]["interpolationContrast"] >= 4.5
        assert editor_colors[theme]["lowestToken"]["contrast"] >= 4.5, editor_colors[theme]["lowestToken"]
        assert editor_colors[theme]["staleContrast"] >= 4.5
        assert editor_colors[theme]["tagContrast"] >= 4.5
    assert editor_colors["light"] != editor_colors["dark"]

    card = page.frame_locator("#citry-playground-preview").locator(".welcome-card")
    card.wait_for(timeout=120_000)
    page.wait_for_function("document.querySelector('#citry-playground-run').disabled === false")
    assert stop.is_disabled()
    assert "Welcome, Ada Lovelace." in card.inner_text()
    card.locator("button").click()
    try:
        expect(card.locator("output")).to_have_text("1", timeout=10_000)
    except AssertionError as error:
        summary = page.locator("#citry-playground-preview-summary").inner_text()
        details = page.locator("#citry-playground-preview-details").inner_text()
        pytest.fail(f"Welcome event did not update State: {summary}\n{details}\n{error}")
    assert "Replies from Python:" in card.inner_text()
    page.wait_for_timeout(100)
    assert page.locator("#citry-playground-preview-diagnostic").is_hidden()

    _set_source(
        page,
        '''html = """
<script>
globalThis.originalDataBlocks = [
  document.querySelector('#data-block'),
  document.querySelector('#legacy-data-block'),
]
</script>
<script id="data-block" type="   ">visitor data</script>
<script id="legacy-data-block" language="javascript ">legacy visitor data</script>
<script>
document.body.dataset.dataBlockPreserved = String(
  globalThis.originalDataBlocks[0] === document.querySelector('#data-block')
)
document.body.dataset.legacyDataBlockPreserved = String(
  globalThis.originalDataBlocks[1] === document.querySelector('#legacy-data-block')
)
</script>
"""
html''',
    )
    _run_and_wait(page)
    data_block_body = page.frame_locator("#citry-playground-preview").locator("body")
    expect(data_block_body).to_have_attribute("data-data-block-preserved", "true")
    expect(data_block_body).to_have_attribute("data-legacy-data-block-preserved", "true")

    _set_source(
        page,
        """from citry import Component


class DataProbe(Component):
    class Kwargs:
        value: str

    class State(Kwargs):
        pass

    class Events:
        def changed(self, state):
            from citry.ext.events import actions

            return actions.Dispatch("data-probe:changed", {"state": state.value})

        def inspect(self, state, request, event):
            return {
                "method": request.method,
                "state": state.value,
                "transport": event.transport,
            }

    template = '''
      <div id="data-probe-root" @data-probe:changed="$el.dataset.state = $event.detail.state">
        <input id="state-input" :c-value="changed">
        <button
          id="data-probe"
          @click="$sendEvent('inspect').then(value => {
            $el.dataset.method = value.method;
            $el.dataset.state = value.state;
            $el.dataset.transport = value.transport;
          })"
        >
          Inspect transport
        </button>
      </div>
    '''


DataProbe(value="start")
""",
    )
    _run_and_wait(page)
    data_probe = page.frame_locator("#citry-playground-preview").locator("#data-probe")
    data_probe_root = page.frame_locator("#citry-playground-preview").locator("#data-probe-root")
    page.frame_locator("#citry-playground-preview").locator("#state-input").fill("edited")
    expect(data_probe_root).to_have_attribute("data-state", "edited", timeout=10_000)
    data_probe.click()
    expect(data_probe).to_have_attribute("data-method", "POST", timeout=10_000)
    expect(data_probe).to_have_attribute("data-state", "edited", timeout=10_000)
    expect(data_probe).to_have_attribute("data-transport", "playground", timeout=10_000)

    _set_source(
        page,
        '''from citry import Component
from citry.ext.events import actions


class NestedEditor(Component):
    class State:
        value: str = "start"

    class Events:
        def changed(self, state):
            return actions.Dispatch("nested:changed", {"value": state.value})

    template = """
      <div id="nested-editor" @nested:changed="$el.dataset.value = $event.detail.value">
        <input id="nested-input" :c-value="changed" />
        <output id="nested-output" x-text="$state.value">start</output>
      </div>
    """


class PropChild(Component):
    template = """
      <output id="prop-output" x-text="clientProps.label"></output>
    """

    js = """
      $component({
        props: {
          label: { type: String, required: true },
        },
        init: ({ props, scope }) => {
          scope.clientProps = props;
        },
      });
    """


class Placeholder(Component):
    template = "<span>Cleared</span>"


class CssOnly(Component):
    template = '<div id="css-only" class="css-only">CSS lifecycle</div>'

    css = """
      .css-only {
        color: rgb(14, 73, 122);
      }
    """


class CssDataProbe(Component):
    class Kwargs:
        accent: str

    def css_data(self, kwargs, slots):
        return {"accent": kwargs.accent}

    template = '<div id="css-data-probe" class="css-data-probe">CSS data</div>'

    css = """
      .css-data-probe {
        color: var(--accent);
      }
    """


class LoadedFragment(Component):
    class Kwargs:
        kind: str
        accent: str

    class Events:
        def ping(self):
            return actions.Dispatch("fragment:ping", {"kind": "nested"})

    def js_data(self, kwargs, slots):
        return {"kind": kwargs.kind}

    def css_data(self, kwargs, slots):
        return {"accent": kwargs.accent}

    template = """
      <section
        id="loaded-fragment"
        class="loaded-fragment"
        x-data="{ label: 'before' }"
        @fragment:ping="$el.dataset.ping = $event.detail.kind"
      >
        <button id="fragment-ping" type="button" @c-click="ping">Ping</button>
        <button id="prop-update" type="button" @click="label = 'after'">Update prop</button>
        <c-PropChild $c-props="{ label }" />
        <c-NestedEditor />
      </section>
    """

    js = """
      window.__fragmentAssetLoads = (window.__fragmentAssetLoads || 0) + 1;
      $component(({ els, data }) => {
        els[0].setAttribute("data-component-js", data.kind);
      });
    """

    css = """
      .loaded-fragment {
        border: 3px solid var(--accent);
        background-color: rgb(231, 241, 255);
      }
    """


class FragmentLoader(Component):
    class Events:
        def load(self):
            return actions.Render(
                LoadedFragment(kind="rendered", accent="rgb(45, 67, 89)"),
                target="#fragment-target",
                swap="inner",
            )

        def load_css(self):
            return actions.Render(CssOnly(), target="#css-target", swap="inner")

        def load_css_data(self):
            return actions.Render(
                CssDataProbe(accent="rgb(122, 51, 19)"),
                target="#css-data-target",
                swap="inner",
            )

        def clear_css(self):
            return [
                actions.Render(Placeholder(), target="#css-initial", swap="inner"),
                actions.Render(Placeholder(), target="#css-target", swap="inner"),
            ]

    template = """
      <main>
        <div id="initial-fragment">
          <c-LoadedFragment kind="initial" accent="rgb(90, 90, 90)" />
        </div>
        <button id="load-fragment" type="button" @c-click="load">Load</button>
        <div id="fragment-target"></div>
        <div id="css-initial"><c-CssOnly /></div>
        <button id="load-css" type="button" @c-click="load_css">Load CSS probe</button>
        <button id="clear-css" type="button" @c-click="clear_css">Clear CSS probe</button>
        <div id="css-target"></div>
        <div id="css-data-initial"><c-CssDataProbe accent="rgb(122, 51, 19)" /></div>
        <button id="load-css-data" type="button" @c-click="load_css_data">Load CSS data probe</button>
        <div id="css-data-target"></div>
      </main>
    """


FragmentLoader()
''',
    )
    _run_and_wait(page)
    render_preview = page.frame_locator("#citry-playground-preview")
    load_fragment = render_preview.locator("#load-fragment")
    load_fragment.click()
    loaded_fragment = render_preview.locator("#fragment-target #loaded-fragment")
    expect(loaded_fragment).to_have_attribute("data-component-js", "rendered", timeout=10_000)
    expect(loaded_fragment).to_have_css("background-color", "rgb(231, 241, 255)")
    expect(loaded_fragment).to_have_css("border-top-color", "rgb(45, 67, 89)")
    loaded_fragment.locator("#fragment-ping").click()
    expect(loaded_fragment).to_have_attribute("data-ping", "nested", timeout=10_000)
    expect(loaded_fragment.locator("#prop-output")).to_have_text("before", timeout=10_000)
    loaded_fragment.locator("#prop-update").click()
    expect(loaded_fragment.locator("#prop-output")).to_have_text("after", timeout=10_000)
    loaded_fragment.locator("#nested-input").fill("edited")
    expect(loaded_fragment.locator("#nested-output")).to_have_text("edited", timeout=10_000)
    expect(loaded_fragment.locator("#nested-editor")).to_have_attribute("data-value", "edited", timeout=10_000)

    asset_loads = render_preview.locator("body").evaluate(
        "body => body.ownerDocument.defaultView.__fragmentAssetLoads"
    )
    assert asset_loads == 1

    render_preview.locator("#load-css").click()
    css_probe = render_preview.locator("#css-target #css-only")
    expect(css_probe).to_have_css("color", "rgb(14, 73, 122)", timeout=10_000)
    class_style_sheets = render_preview.locator("[data-citry-css-class]")
    expect(class_style_sheets).to_have_count(3)
    render_preview.locator("#clear-css").click()
    expect(render_preview.locator("#css-only")).to_have_count(0, timeout=10_000)
    expect(class_style_sheets).to_have_count(2, timeout=10_000)
    render_preview.locator("#load-css").click()
    css_probe_again = render_preview.locator("#css-target #css-only")
    expect(css_probe_again).to_have_css("color", "rgb(14, 73, 122)", timeout=10_000)
    expect(class_style_sheets).to_have_count(3, timeout=10_000)

    stylesheet_count = render_preview.locator('style, link[rel~="stylesheet"]').count()
    render_preview.locator("#load-css-data").click()
    css_data_probe = render_preview.locator("#css-data-target #css-data-probe")
    expect(css_data_probe).to_have_css("color", "rgb(122, 51, 19)", timeout=10_000)
    expect(render_preview.locator('style, link[rel~="stylesheet"]')).to_have_count(stylesheet_count)
    if not page.locator("#citry-playground-preview-diagnostic").is_hidden():
        summary = page.locator("#citry-playground-preview-summary").inner_text()
        details = page.locator("#citry-playground-preview-details").inner_text()
        pytest.fail(f"Render lifecycle reported a client diagnostic: {summary}\n{details}")

    _set_source(
        page,
        '''from citry import Component
from citry.ext.events import EventError, actions


class SignupIn:
    email: str


class SignupForm(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    class Events:
        def submit(self, data: SignupIn):
            email = data.email.strip()
            if not email.endswith("@example.com"):
                raise EventError(
                    "Please fix the email address.",
                    fields={"email": "Use an @example.com address."},
                )
            return actions.Dispatch("signup:sent", {"email": email})

    template = """
      <section x-data="{ acceptedEmail: '' }" @signup:sent="acceptedEmail = $event.detail.email">
        <form @c-submit.prevent="submit">
          <input name="email" type="email" required />
          <span
            id="signup-error"
            x-show="(typeof $error === 'function' ? $error('submit') : $error)?.fieldErrors?.email"
            x-text="(typeof $error === 'function' ? $error('submit') : $error)?.fieldErrors?.email || ''"
          ></span>
          <button type="submit">Send request</button>
        </form>
        <output id="accepted-email" x-show="acceptedEmail" x-text="acceptedEmail"></output>
      </section>
    """


class TutorialPage(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Join the reading room</title>
        </head>
        <body>
          <main>
            <h1>Join the reading room</h1>
            <c-SignupForm />
          </main>
        </body>
      </html>
    """


TutorialPage()
''',
    )
    _run_and_wait(page)
    signup = page.frame_locator("#citry-playground-preview")
    signup.locator('input[name="email"]').wait_for(timeout=10_000)
    signup.locator('input[name="email"]').fill("reader@other.test")
    signup.locator('button[type="submit"]').click()
    expect(signup.locator("#signup-error")).to_have_text("Use an @example.com address.", timeout=10_000)
    page.wait_for_function(
        "document.querySelector('#citry-playground-preview-summary').textContent.includes('event error')"
    )
    assert "Please fix the email address." in page.locator("#citry-playground-preview-details").inner_text()
    page.locator("#citry-playground-dismiss-preview").click()
    signup.locator('input[name="email"]').fill("reader@example.com")
    signup.locator('button[type="submit"]').click()
    expect(signup.locator("#accepted-email")).to_have_text("reader@example.com", timeout=10_000)
    assert page.locator("#citry-playground-python-diagnostic").is_hidden()
    assert page.locator("#citry-playground-preview-diagnostic").is_hidden()

    page.locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+a")
    selection_alpha = page.locator(".cm-selectionBackground").first.evaluate(
        """element => {
          const canvas = document.createElement('canvas');
          canvas.width = canvas.height = 1;
          const context = canvas.getContext('2d');
          context.clearRect(0, 0, 1, 1);
          context.fillStyle = getComputedStyle(element).backgroundColor;
          context.fillRect(0, 0, 1, 1);
          return context.getImageData(0, 0, 1, 1).data[3] / 255;
        }"""
    )
    assert 0 < selection_alpha < 0.3

    _set_source(page, "html = '<main id=changed>Changed</main>'\nhtml")
    _run_and_wait(page)
    assert page.frame_locator("#citry-playground-preview").locator("#changed").inner_text() == "Changed"

    _set_source(
        page,
        """html = \"\"\"<p id='state-one'>First realm</p>
<script>setInterval(() => { window.__citryRunOne = (window.__citryRunOne || 0) + 1; }, 10)</script>\"\"\"
html""",
    )
    _run_and_wait(page)
    page.wait_for_timeout(100)
    _set_source(
        page,
        """html = \"\"\"<p id='state-two'>Fresh realm</p>
<button id='retained-error' onclick=\"setTimeout(() => { throw new Error('retained boom'); })\">Error</button>
<script>
document.body.dataset.oldRun = typeof window.__citryRunOne;
setTimeout(() => { document.body.dataset.oldRunLater = typeof window.__citryRunOne; }, 100);
</script>\"\"\"
html""",
    )
    _run_and_wait(page)
    preview_body = page.frame_locator("#citry-playground-preview").locator("body")
    assert preview_body.get_attribute("data-old-run") == "undefined"
    page.wait_for_timeout(150)
    assert preview_body.get_attribute("data-old-run-later") == "undefined"

    stalled_preview = "**/static/playground/preview.html?citry-preview=*"
    page.route(stalled_preview, _stall_preview_render)
    _set_source(page, "html = '<p id=never-swapped>Never swapped</p>'\nhtml")
    _run_and_wait(page)
    assert page.locator("#citry-playground-status").inner_text() == "Preview unavailable"
    assert page.frame_locator("#citry-playground-preview").locator("#state-two").inner_text() == "Fresh realm"
    assert page.frame_locator("#citry-playground-preview").locator("#never-swapped").count() == 0
    page.frame_locator("#citry-playground-preview").locator("#retained-error").click()
    page.wait_for_function(
        "document.querySelector('#citry-playground-preview-summary').textContent.includes('Client error')"
    )
    page.unroute(stalled_preview, _stall_preview_render)

    delayed_preview = "**/static/playground/preview.html?citry-preview=*"
    page.route(delayed_preview, _delay_preview_render)
    _set_source(page, "html = '<p id=accepted>Accepted candidate</p>'\nhtml")
    page.locator("#citry-playground-run").click()
    page.wait_for_function(
        "document.querySelector('#citry-playground-status').textContent === 'Updating rendered result'"
    )
    page.wait_for_function(
        "document.querySelector('#citry-playground-announcer').textContent === 'Updating rendered result'"
    )
    page.frame_locator("#citry-playground-preview").locator("#retained-error").click()
    page.wait_for_function(
        "document.querySelector('#citry-playground-preview-summary').textContent.includes('Client error')"
    )
    page.wait_for_function("document.querySelector('#citry-playground-run').disabled === false")
    assert page.frame_locator("#citry-playground-preview").locator("#accepted").inner_text() == "Accepted candidate"
    assert page.locator("#citry-playground-preview-diagnostic").is_hidden()
    page.unroute(delayed_preview, _delay_preview_render)

    page.route(delayed_preview, _delay_preview_render)
    _set_source(page, "html = '<p id=stopped-candidate>Stopped candidate</p>'\nhtml")
    page.locator("#citry-playground-run").click()
    page.wait_for_function(
        "document.querySelector('#citry-playground-status').textContent === 'Updating rendered result'"
    )
    page.locator("#citry-playground-stop").click()
    page.wait_for_function("document.querySelector('#citry-playground-status').textContent === 'Stopped'")
    assert page.locator("#citry-playground-stop").is_disabled()
    assert page.locator("#citry-playground-stale").is_visible()
    assert page.frame_locator("#citry-playground-preview").locator("#accepted").inner_text() == "Accepted candidate"
    assert page.frame_locator("#citry-playground-preview").locator("#stopped-candidate").count() == 0
    page.unroute(delayed_preview, _delay_preview_render)

    _set_source(page, "raise ValueError('visitor boom')")
    _run_and_wait(page)
    assert "visitor boom" in page.locator("#citry-playground-python-summary").inner_text()
    assert page.locator("#citry-playground-stale").is_visible()
    assert page.frame_locator("#citry-playground-preview").locator("#accepted").inner_text() == "Accepted candidate"
    page.locator("#citry-playground-copy-python-error").click()
    page.wait_for_function(
        "document.querySelector('#citry-playground-announcer').textContent === 'Python diagnostic copied'"
    )
    page.locator("#citry-playground-dismiss-python").click()
    assert page.locator("#citry-playground-python-diagnostic").is_hidden()

    _set_source(
        page,
        "html = \"<p id='client'>Client</p><script>throw new Error('client boom')</script>\"\nhtml",
    )
    _run_and_wait(page)
    page.wait_for_function(
        "document.querySelector('#citry-playground-preview-summary').textContent.includes('Client error')"
    )
    # WebKit redacts some opaque-origin script messages to "Script error.";
    # the diagnostic still belongs to the Result panel and remains actionable.
    assert page.locator("#citry-playground-preview-details").inner_text()
    page.locator("#citry-playground-copy-preview-error").click()
    page.wait_for_function(
        "document.querySelector('#citry-playground-announcer').textContent === 'Result diagnostic copied'"
    )
    page.locator("#citry-playground-dismiss-preview").click()
    assert page.locator("#citry-playground-preview-diagnostic").is_hidden()

    _set_source(
        page,
        """from citry import Component


class BrokenEvent(Component):
    class Events:
        def fail(self):
            raise ValueError("event boom")

    template = '<button id="broken-event" @c-click="fail">Fail</button>'


BrokenEvent()
""",
    )
    _run_and_wait(page)
    page.frame_locator("#citry-playground-preview").locator("#broken-event").click()
    page.wait_for_function(
        "document.querySelector('#citry-playground-preview-summary').textContent.includes('event error')"
    )
    assert "event boom" in page.locator("#citry-playground-preview-details").inner_text()

    assert page.locator("#citry-playground-auto-run").is_checked()
    _set_source(page, "import time\ntime.sleep(1)\nhtml = '<p id=older>Older</p>'\nhtml")
    page.locator("#citry-playground-run").click()
    page.wait_for_function("document.querySelector('#citry-playground-stop').disabled === false")
    _set_source(page, "html = '<p id=newest>Newest</p>'\nhtml")
    page.frame_locator("#citry-playground-preview").locator("#newest").wait_for(timeout=120_000)
    assert page.frame_locator("#citry-playground-preview").locator("#older").count() == 0

    page.locator("#citry-playground-auto-run").uncheck()
    _set_source(page, "while True:\n    pass\n'<p>never</p>'")
    page.locator("#citry-playground-run").click()
    page.wait_for_function("document.querySelector('#citry-playground-stop').disabled === false")
    page.wait_for_timeout(100)
    page.locator("#citry-playground-stop").click()
    page.wait_for_function("document.querySelector('#citry-playground-status').textContent === 'Stopped'")

    _set_source(page, "html = '<p id=reset-race>Do not commit this result</p>'\nhtml")
    page.evaluate(
        """() => {
          window.__citryResetRaceDone = false;
          const status = document.querySelector('#citry-playground-status');
          const observer = new MutationObserver(() => {
            if (status.textContent !== 'Updating rendered result') return;
            observer.disconnect();
            document.querySelector('#citry-playground-reset').click();
            window.__citryResetRaceDone = true;
          });
          observer.observe(status, { childList: true, subtree: true });
        }"""
    )
    page.locator("#citry-playground-run").click()
    page.wait_for_function("window.__citryResetRaceDone === true", timeout=120_000)
    assert "class WelcomeCard" in page.evaluate("window.citryPlayground.getSource()")
    page.wait_for_timeout(250)
    assert page.locator("#citry-playground-status").inner_text() == "Starter restored"
    assert not page.locator("#citry-playground-run").is_disabled()
    _run_and_wait(page)
    assert "Ada Lovelace" in card.inner_text()

    divider = page.locator("#citry-playground-divider")
    assert divider.get_attribute("aria-valuemin") == "30"
    assert divider.get_attribute("aria-valuemax") == "70"
    divider.focus()
    page.keyboard.press("Shift+ArrowRight")
    assert divider.get_attribute("aria-valuenow") == "60"
    root_width = page.locator(".citry-playground").bounding_box()["width"]
    code_width = page.locator("#citry-playground-code-panel").bounding_box()["width"]
    assert code_width / root_width == pytest.approx(0.6, abs=0.01)

    page.set_viewport_size({"width": 880, "height": 800})
    page.locator("#citry-playground-result-tab").click()
    assert page.locator("#citry-playground-result-panel").is_visible()
    assert page.locator("#citry-playground-code-panel").is_hidden()

    page.reload(wait_until="domcontentloaded")
    page.wait_for_function("window.citryPlayground !== undefined")
    page.wait_for_timeout(700)
    assert not page.locator("#citry-playground-auto-run").is_checked()
    assert page.locator("#citry-playground-status").inner_text() == "Ready to run"
    assert page.locator("#citry-playground-stop").is_visible()
    assert page.locator("#citry-playground-stop").is_disabled()
    empty_state = page.locator("#citry-playground-empty")
    assert empty_state.get_attribute("hidden") is None
    page.locator("#citry-playground-result-tab").click()
    assert empty_state.is_visible()
