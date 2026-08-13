"""Public CommandPalette evidence through its reusable quality scenario."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.ccommand_palette import CCommandPalette, CCommandPaletteCommand
from citry_ui.quality.routes import build_scenario, render_scenario

pytestmark = pytest.mark.e2e


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the CommandPalette quality test."
    raise RuntimeError(msg)


def _wait_for_all_ready(page: Any) -> None:
    page.wait_for_function(
        """() => {
          const roots = [...document.querySelectorAll('[data-citry-command-palette-host]')];
          const shadow = document.querySelector('#quality-command-palette-shadow-host')?.shadowRoot;
          const shadowRoots = shadow
            ? [...shadow.querySelectorAll('[data-citry-command-palette-host]')]
            : [];
          return roots.length > 0
            && roots.every(root => root.hasAttribute('data-citry-command-palette-initialized'))
            && shadowRoots.length === 1
            && shadowRoots.every(root => root.hasAttribute('data-citry-command-palette-initialized'));
        }""",
        timeout=10_000,
    )


def _axe_serious_or_critical(page: Any) -> list[dict[str, object]]:
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` before the CommandPalette quality axe test"
    page.add_script_tag(path=str(axe_path))
    return page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter((finding) => ['serious','critical'].includes(finding.impact))"""
    )


def _no_javascript_fallback_html() -> str:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("command-palette-no-javascript", (CCommandPalette,)))

    class FallbackPage(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:
            return {"entries": (CCommandPaletteCommand(value="inspect", label="Inspect readable fallback"),)}

        template = """
          <main>
            <c-CCommandPalette
              id="quality-command-palette-no-js-closed"
              label="Closed fallback"
              c-entries="entries"
            />
            <c-CCommandPalette
              id="quality-command-palette-no-js-open"
              label="Open readable fallback"
              c-entries="entries"
              c-open="True"
            />
          </main>
        """

    return str(FallbackPage())


def test_command_palette_quality_search_control_action_form_ime_and_axe(page: Any) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(render_scenario("command-palette.states"), wait_until="load")
    _wait_for_all_ready(page)

    page.get_by_role("button", name="Open workspace commands").click()
    basic = page.locator("#quality-command-palette-basic")
    basic_input = basic.locator('[data-citry-ui-part="command-palette-input"]')
    assert basic.evaluate("element => element.open") is True
    assert basic_input.evaluate("element => element === document.activeElement") is True
    assert basic_input.get_attribute("role") == "combobox"
    assert basic.locator('[role="listbox"]').count() == 1
    assert basic.locator('[role="group"]').count() == 2
    assert basic.locator('[role="option"]').count() == 6
    basic_input.fill("create")
    page.wait_for_function(
        "document.querySelectorAll('#quality-command-palette-basic [role=option]:not([hidden])').length === 1"
    )
    basic_input.press("Enter")
    page.wait_for_function("!document.querySelector('#quality-command-palette-basic').open")
    assert page.locator("#quality-command-palette-basic-output").text_content().replace("\n", "").split() == [
        "closed|",
        "empty|",
        "create-project|",
        "0",
    ]

    page.get_by_role("button", name="Restore controlled open").click()
    controlled = page.locator("#quality-command-palette-controlled")
    controlled_input = controlled.locator('[data-citry-ui-part="command-palette-input"]')
    page.wait_for_function("document.querySelector('#quality-command-palette-controlled').open")
    controlled_input.fill("rejected")
    page.wait_for_function(
        "document.querySelector("
        "'#quality-command-palette-controlled [data-citry-ui-part=command-palette-input]'"
        ").value"
        " === 'open'"
    )
    controlled.locator('[data-citry-ui-part="command-palette-close"]').click()
    assert controlled.evaluate("element => element.open") is True
    page.evaluate(
        """() => {
          const owner = document.querySelector('#quality-command-palette-controlled').closest('article');
          Alpine.$data(owner).acceptClose = true;
        }"""
    )
    controlled.locator('[data-citry-ui-part="command-palette-close"]').click()
    page.wait_for_function("!document.querySelector('#quality-command-palette-controlled').open")

    page.get_by_role("button", name="Open profile commands").click()
    form_palette = page.locator("#quality-command-palette-form-palette")
    form_input = form_palette.locator('[data-citry-ui-part="command-palette-input"]')
    form_input.fill("no match")
    form_input.press("Enter")
    assert page.locator("#quality-command-palette-submit-output").text_content() == "0"
    page.evaluate(
        """() => {
          const input = document.querySelector(
            '#quality-command-palette-form-palette [data-citry-ui-part=command-palette-input]',
          );
          input.dispatchEvent(new CompositionEvent('compositionstart', {bubbles:true, data:'に'}));
          input.value = 'に';
          input.dispatchEvent(new InputEvent('input', {
            bubbles:true,
            data:'に',
            inputType:'insertCompositionText',
            isComposing:true,
          }));
          input.dispatchEvent(new KeyboardEvent('keydown', {
            bubbles:true,
            cancelable:true,
            key:'Enter',
            code:'Enter',
            isComposing:true,
            keyCode:229,
          }));
          input.dispatchEvent(new CompositionEvent('compositionend', {bubbles:true, data:'に'}));
          input.dispatchEvent(new InputEvent('input', {
            bubbles:true,
            data:null,
            inputType:'insertText',
          }));
        }"""
    )
    page.wait_for_timeout(50)
    assert page.locator("#quality-command-palette-submit-output").text_content() == "0"
    form_input.fill("copy project")
    form_input.press("Enter")
    page.wait_for_function("document.querySelector('#quality-command-palette-submit-output').textContent === '1'")
    form_palette.locator('[data-citry-ui-part="command-palette-close"]').click()
    page.wait_for_function("!document.querySelector('#quality-command-palette-form-palette').open")

    page.get_by_role("button", name="Open workspace commands").click()
    page.wait_for_function("document.querySelector('#quality-command-palette-basic').open")
    assert _axe_serious_or_critical(page) == []
    assert console_errors == []
    assert page_errors == []


def test_command_palette_signed_retained_changed_replacement_and_two_restore_cycles(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    rendered = build_scenario(
        "command-palette.states",
        configure_app=lambda app: app.set_mounted_prefix("/citry"),
    )
    base_url = serve_citry_ui_live(rendered.app, rendered.html)
    page.goto(base_url + "/", wait_until="load")
    _wait_for_all_ready(page)
    expected_roots = page.evaluate(
        """() => {
          const roots = [...document.querySelectorAll('[data-citry-command-palette-host]')];
          const shadow = document.querySelector('#quality-command-palette-shadow-host')?.shadowRoot;
          return roots.length + (shadow?.querySelectorAll('[data-citry-command-palette-host]').length ?? 0);
        }"""
    )
    baseline_modals = page.evaluate("globalThis[Symbol.for('citry-ui:dialog-controller-runtime')].counts().modals")

    page.get_by_role("button", name="Open lifecycle palette").click()
    lifecycle = page.locator("#quality-command-palette-lifecycle")
    page.wait_for_function("document.querySelector('#quality-command-palette-lifecycle').open")
    lifecycle_input = lifecycle.locator('[data-citry-ui-part="command-palette-input"]')
    lifecycle_input.focus()
    page.evaluate(
        """() => {
          const dialog = document.querySelector('#quality-command-palette-lifecycle');
          window.__commandPaletteLifecycle = {
            host: dialog.closest('[data-citry-command-palette-host]'),
            dialog,
            input: dialog.querySelector('[data-citry-ui-part=command-palette-input]'),
            listbox: dialog.querySelector('[data-citry-ui-part=command-palette-listbox]'),
          };
        }"""
    )
    assert (
        page.evaluate("globalThis[Symbol.for('citry-ui:dialog-controller-runtime')].counts().modals")
        == baseline_modals + 1
    )

    def refresh(step: int, roots: int) -> None:
        page.evaluate(
            """() => void Citry.events.send(
              document.querySelector('.command-palette-quality__lifecycle'),
              'refresh',
              {},
            )"""
        )
        try:
            page.wait_for_function(
                "step => Number(document.querySelector('[data-quality-morph-step]')?.textContent) === step",
                arg=step,
                timeout=10_000,
            )
            page.wait_for_function(
                """roots => {
                  const all = [...document.querySelectorAll('[data-citry-command-palette-host]')];
                  const shadow = document.querySelector('#quality-command-palette-shadow-host')?.shadowRoot;
                  if (shadow) all.push(...shadow.querySelectorAll('[data-citry-command-palette-host]'));
                  const ready = all.filter(
                    root => root.hasAttribute('data-citry-command-palette-initialized'),
                  );
                  return all.length === roots && ready.length === roots;
                }""",
                arg=roots,
                timeout=10_000,
            )
        except Exception as error:  # noqa: BLE001 - preserve browser diagnostics for a failed readiness gate
            diagnostic = page.evaluate(
                """() => {
                  const all = [...document.querySelectorAll('[data-citry-command-palette-host]')];
                  const shadow = document.querySelector('#quality-command-palette-shadow-host')?.shadowRoot;
                  if (shadow) all.push(...shadow.querySelectorAll('[data-citry-command-palette-host]'));
                  const lifecycle = document.querySelector('#quality-command-palette-lifecycle');
                  const prior = window.__commandPaletteLifecycle;
                  return {
                    roots: all.length,
                    ready: all.filter(
                      root => root.hasAttribute('data-citry-command-palette-initialized'),
                    ).length,
                    unready: all.filter(
                      root => !root.hasAttribute('data-citry-command-palette-initialized'),
                    ).map(root => ({
                      dialogId: root.querySelector('dialog')?.id ?? null,
                      states: root.closest('[data-quality-states]')?.dataset.qualityStates ?? null,
                      connected: root.isConnected,
                    })),
                    retained: lifecycle && prior ? {
                      host: lifecycle.closest('[data-citry-command-palette-host]') === prior.host,
                      dialog: lifecycle === prior.dialog,
                      input: lifecycle.querySelector('[data-citry-ui-part=command-palette-input]') === prior.input,
                      listbox:
                        lifecycle.querySelector('[data-citry-ui-part=command-palette-listbox]')
                        === prior.listbox,
                      open: lifecycle.open,
                    } : null,
                  };
                }"""
            )
            pytest.fail(
                f"CommandPalette roots did not settle after morph: {diagnostic}; "
                f"console={console_errors}; page={page_errors}; error={error}"
            )
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")

    refresh(1, expected_roots)
    retained = page.evaluate(
        """() => {
          const prior = window.__commandPaletteLifecycle;
          const dialog = document.querySelector('#quality-command-palette-lifecycle');
          return {
            host: dialog.closest('[data-citry-command-palette-host]') === prior.host,
            dialog: dialog === prior.dialog,
            input: dialog.querySelector('[data-citry-ui-part=command-palette-input]') === prior.input,
            listbox: dialog.querySelector('[data-citry-ui-part=command-palette-listbox]') === prior.listbox,
            open: dialog.open,
            focused: dialog.querySelector('[data-citry-ui-part=command-palette-input]')
              === document.activeElement,
          };
        }"""
    )
    assert retained == {
        "host": True,
        "dialog": True,
        "input": True,
        "listbox": True,
        "open": True,
        "focused": True,
    }

    refresh(2, expected_roots)
    changed = page.evaluate(
        """() => {
          const prior = window.__commandPaletteLifecycle;
          const dialog = document.querySelector('#quality-command-palette-lifecycle');
          return {
            host: dialog.closest('[data-citry-command-palette-host]') === prior.host,
            dialog: dialog === prior.dialog,
            input: dialog.querySelector('[data-citry-ui-part=command-palette-input]') === prior.input,
            listbox: dialog.querySelector('[data-citry-ui-part=command-palette-listbox]') === prior.listbox,
            open: dialog.open,
          };
        }"""
    )
    assert changed == {"host": True, "dialog": True, "input": True, "listbox": True, "open": True}

    refresh(3, expected_roots)
    replaced = page.evaluate(
        """() => {
          const prior = window.__commandPaletteLifecycle;
          const dialog = document.querySelector('#quality-command-palette-lifecycle');
          window.__commandPaletteReplacement = dialog.closest('[data-citry-command-palette-host]');
          return {
            hostChanged: window.__commandPaletteReplacement !== prior.host,
            dialogChanged: dialog !== prior.dialog,
            oldConnected: prior.host.isConnected,
            oldReady: prior.host.hasAttribute('data-citry-command-palette-initialized'),
          };
        }"""
    )
    assert replaced == {
        "hostChanged": True,
        "dialogChanged": True,
        "oldConnected": False,
        "oldReady": False,
    }

    refresh(4, expected_roots - 1)
    assert page.locator("#quality-command-palette-lifecycle").count() == 0
    remaining_modals = page.evaluate("globalThis[Symbol.for('citry-ui:dialog-controller-runtime')].counts().modals")
    assert remaining_modals == baseline_modals

    refresh(5, expected_roots)
    assert page.locator("#quality-command-palette-lifecycle").count() == 1
    assert (
        page.evaluate(
            "document.querySelector('#quality-command-palette-lifecycle')"
            ".closest('[data-citry-command-palette-host]') !== window.__commandPaletteReplacement"
        )
        is True
    )

    refresh(6, expected_roots - 1)
    assert page.locator("#quality-command-palette-lifecycle").count() == 0
    refresh(7, expected_roots)
    assert page.locator("#quality-command-palette-lifecycle").count() == 1
    assert console_errors == []
    assert page_errors == []


def test_command_palette_no_javascript_keeps_readable_inert_native_fallback(browser: Any) -> None:
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    try:
        page.set_content(_no_javascript_fallback_html(), wait_until="load")
        closed = page.locator("#quality-command-palette-no-js-closed")
        assert closed.get_attribute("open") is None
        open_fallback = page.locator("#quality-command-palette-no-js-open")
        assert open_fallback.get_attribute("open") == ""
        assert open_fallback.locator('[data-citry-ui-part="command-palette-input"]').is_disabled()
        assert open_fallback.locator('[role="option"]').count() > 0
    finally:
        context.close()
