"""Browser evidence for TimeInput and TimePicker Forms, control, and i18n."""

# ruff: noqa: E501 - embedded templates and browser expressions remain readable

from __future__ import annotations

import importlib
import importlib.resources
from typing import TYPE_CHECKING, Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.e2e


def _page(app: Citry, *, localized: bool = False) -> str:
    provider_open = '<c-i18n tag="main" c-client="True">' if localized else "<main>"
    provider_close = "</c-i18n>" if localized else "</main>"

    class Page(Component):
        citry = app
        template = f"""
          <!doctype html>
          <html lang="en-US">
            <head>
              <meta charset="utf-8" />
              <title>Time browser contract</title>
              <script>window.__timeEvents=[];window.__timeSubmits=[];</script>
              <c-css />
            </head>
            <body>
              {provider_open}
              <section x-data="{{selected:'09:30',controlledOpen:false,acceptValue:false,acceptOpen:false}}">
                <form id="schedule" @submit.prevent="window.__timeSubmits.push(Array.from(new FormData($event.target).entries()))">
                  <c-CField control_id="arrival" required>
                    <c-fill name="label">Arrival time</c-fill>
                    <c-fill name="description">Choose an available morning time.</c-fill>
                    <c-fill name="default">
                      <c-CTimePicker
                        id="arrival"
                        name="arrival"
                        value="09:30"
                        min="09:00"
                        max="11:00"
                        c-step="1800"
                        $c-props="{{onValueChange:(value,detail)=>window.__timeEvents.push(['value',value,detail.source]),onOpenChange:(open,detail)=>window.__timeEvents.push(['open',open,detail.reason])}}"
                        @input="window.__timeEvents.push(['input',$event.target.value])"
                        @change="window.__timeEvents.push(['change',$event.target.value])"
                      />
                    </c-fill>
                    <c-fill name="error">Choose an arrival time.</c-fill>
                  </c-CField>
                  <label for="native-time">Native departure time</label>
                  <c-CTimeInput id="native-time" name="native-time" value="14:30" min="13:00" max="17:00" c-step="900" />
                  <button id="submit" type="submit">Submit</button>
                  <button id="reset" type="reset">Reset</button>
                </form>

                <c-CTimePicker
                  id="optional"
                  value="09:30"
                  min="09:00"
                  max="11:00"
                  c-step="1800"
                  $c-props="{{value:selected,onValueChange:(value,detail)=>{{window.__timeEvents.push(['controlled-value',value,detail.controlled]);if(acceptValue)selected=value}}}}"
                />
                <button id="accept-value" type="button" @click="acceptValue=true">Accept value</button>
                <button id="set-value" type="button" @click="selected='10:30'">Set value</button>

                <c-CTimePicker
                  id="controlled-open"
                  min="09:00"
                  max="11:00"
                  c-step="1800"
                  $c-props="{{open:controlledOpen,onOpenChange:(open,detail)=>{{window.__timeEvents.push(['controlled-open',open,detail.controlled]);if(acceptOpen)controlledOpen=open}}}}"
                />
                <button id="accept-open" type="button" @click="acceptOpen=true">Accept open</button>

                <form id="required-form">
                  <c-CField control_id="required-time" required>
                    <c-fill name="label">Required time</c-fill>
                    <c-fill name="default"><c-CTimePicker id="required-time" name="required-time" min="09:00" max="11:00" c-step="1800" /></c-fill>
                    <c-fill name="error">A time is required.</c-fill>
                  </c-CField>
                  <button id="required-submit" type="submit">Submit required time</button>
                </form>

                <button id="switch-cs" type="button" @click="$i18n.switchLocale('cs-CZ')">Čeština</button>
              </section>
              {provider_close}
              <c-js />
            </body>
          </html>
        """

    if localized:
        context = app.extensions.get_extension("i18n").make_context(locale="en-US")
        return Page().render(provides={"citry_i18n": context}).serialize()
    return str(Page())


def _write_catalog(root: Path) -> str:
    name = "citry_ui_time_browser_i18n"
    package = root / name
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf8")
    (package / "citry-i18n.toml").write_text(
        'schema_version = 1\nowner = "citry-ui"\nsource_locale = "en-US"\n',
        encoding="utf8",
    )
    source = importlib.resources.files("citry_ui_i18n")
    (package / "formats.json").write_text(source.joinpath("formats.json").read_text(encoding="utf8"), encoding="utf8")
    english = package / "locales" / "en-US"
    english.mkdir(parents=True)
    (english / "citry-ui.ftl").write_text(
        source.joinpath("locales", "en-US", "citry-ui.ftl").read_text(encoding="utf8"), encoding="utf8"
    )
    czech = package / "locales" / "cs-CZ"
    czech.mkdir(parents=True)
    (czech / "citry-ui.ftl").write_text(
        """
citry-ui-time-picker-placeholder = Vyberte čas
citry-ui-time-picker-label = Vybrat čas
citry-ui-time-picker-change = Změnit čas, { $time }
citry-ui-time-picker-clear = Vymazat čas
citry-ui-time-picker-unavailable = Vyberte dostupný čas.
""".lstrip(),
        encoding="utf8",
    )
    return name


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    return app


def _open(page: Any, app: Citry, serve_citry_ui_live: Any, *, localized: bool = False) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(serve_citry_ui_live(app, _page(app, localized=localized)) + "/")
    page.wait_for_timeout(1_000)
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="time-picker"]')]
          .every(root => root.hasAttribute('data-citry-time-picker-initialized'))"""
    )
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="time-input"]')]
          .every(root => root.hasAttribute('data-citry-time-input-initialized'))"""
    )
    assert errors == []
    return errors


def test_select_submit_native_edit_and_reset(page: Any, serve_citry_ui_live: Any) -> None:
    errors = _open(page, _app(), serve_citry_ui_live)
    trigger = page.locator("#arrival")
    native = page.locator("#arrival-native")
    assert native.input_value() == "09:30"
    trigger.click()
    page.wait_for_function("document.querySelector('#arrival').getAttribute('aria-expanded') === 'true'")
    page.get_by_role("option", name="10:00 AM", exact=True).first.click()
    page.wait_for_function("document.querySelector('#arrival-native').value === '10:00'")
    assert page.evaluate("window.__timeEvents.slice(-4)") == [
        ["value", "10:00", "option"],
        ["input", "10:00"],
        ["change", "10:00"],
        ["open", False, "selection"],
    ]
    page.locator("#native-time").fill("15:45")
    page.locator("#submit").click()
    assert page.evaluate("window.__timeSubmits.at(-1)") == [["arrival", "10:00"], ["native-time", "15:45"]]
    page.locator("#reset").click()
    page.wait_for_function("document.querySelector('#arrival-native').value === '09:30'")
    assert page.locator("#native-time").input_value() == "14:30"
    assert errors == []


def test_controlled_value_open_clear_and_required_invalid_focus(page: Any, serve_citry_ui_live: Any) -> None:
    errors = _open(page, _app(), serve_citry_ui_live)
    optional = page.locator("#optional")
    optional.click()
    page.locator('#optional-root [data-value="10:00"]').click()
    assert page.locator("#optional-native").input_value() == "09:30"
    assert page.evaluate("window.__timeEvents.at(-1)") == ["controlled-value", "10:00", True]
    page.locator("#accept-value").click()
    optional.click()
    page.locator('#optional-root [data-value="10:00"]').click()
    page.wait_for_function("document.querySelector('#optional-native').value === '10:00'")
    page.locator('#optional-root [data-citry-ui-part="clear"]').click()
    page.wait_for_function("document.querySelector('#optional-native').value === ''")
    page.locator("#set-value").click()
    page.wait_for_function("document.querySelector('#optional-native').value === '10:30'")

    controlled = page.locator("#controlled-open")
    controlled.click()
    assert controlled.get_attribute("aria-expanded") == "false"
    page.wait_for_function("window.__timeEvents.at(-1)?.[0] === 'controlled-open'")
    assert page.evaluate("window.__timeEvents.at(-1)") == ["controlled-open", True, True]
    page.locator("#accept-open").click()
    controlled.click()
    page.wait_for_function("document.querySelector('#controlled-open').getAttribute('aria-expanded') === 'true'")
    page.keyboard.press("Escape")
    page.wait_for_function("document.querySelector('#controlled-open').getAttribute('aria-expanded') === 'false'")
    page.wait_for_function("document.activeElement?.id === 'controlled-open'")

    page.locator("#required-submit").click()
    page.wait_for_function("document.querySelector('#required-time-root').dataset.invalid === ''")
    assert page.locator("#required-time").get_attribute("aria-expanded") == "true"
    page.wait_for_function("document.activeElement?.getAttribute('role') === 'option'")
    assert page.evaluate("document.activeElement?.getAttribute('role')") == "option"
    assert errors == []


def test_client_locale_switch_updates_display_trigger_title_clear_and_options(
    page: Any,
    serve_citry_ui_live: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _write_catalog(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    app = Citry(
        mode="development",
        autodiscover=False,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": (catalog,),
            }
        },
    )
    app.register_library(citry_ui)
    errors = _open(page, app, serve_citry_ui_live, localized=True)
    trigger = page.locator("#arrival")
    assert "9:30:00 AM" in trigger.text_content()
    trigger.click()
    assert page.locator("#arrival-popover-title").text_content().strip() == "Choose time"
    page.evaluate("async () => Alpine.evaluate(document.querySelector('#switch-cs'), '$i18n').switchLocale('cs-CZ')")
    page.wait_for_function("document.querySelector('main')?.lang === 'cs-CZ'")
    page.wait_for_function("document.querySelector('#arrival').textContent.includes('9:30:00')")
    assert trigger.get_attribute("aria-label") == "Změnit čas, \u20689:30:00\u2069"
    assert page.locator("#arrival-popover-title").text_content().strip() == "Vybrat čas"
    assert page.locator('#optional-root [data-citry-ui-part="clear"]').get_attribute("aria-label") == "Vymazat čas"
    assert (
        page.locator('#arrival-root [data-value="10:00"] [data-citry-ui-part="listbox-option-label"]').text_content()
        == "10:00:00"
    )
    assert page.locator("#arrival-native").input_value() == "09:30"
    assert errors == []
