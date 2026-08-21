"""Browser evidence for CDatePicker composition, Forms, control, and i18n."""

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
              <title>DatePicker browser contract</title>
              <script>window.__datePickerEvents=[];window.__datePickerSubmits=[];</script>
              <c-css />
            </head>
            <body>
              {provider_open}
              <section x-data="{{selected:'2026-08-19',controlledOpen:false,acceptValue:false,acceptOpen:false}}">
                <form id="booking" @submit.prevent="window.__datePickerSubmits.push(Array.from(new FormData($event.target).entries()))">
                  <c-CField control_id="arrival" required>
                    <c-fill name="label">Arrival date</c-fill>
                    <c-fill name="description">Choose an available August day.</c-fill>
                    <c-fill name="default">
                      <c-CDatePicker
                        id="arrival"
                        name="arrival"
                        value="2026-08-19"
                        min="2026-08-10"
                        max="2026-09-15"
                        c-unavailable_dates="('2026-08-20',)"
                        $c-props="{{onValueChange:(value,detail)=>window.__datePickerEvents.push(['value',value,detail.source]),onOpenChange:(open,detail)=>window.__datePickerEvents.push(['open',open,detail.reason])}}"
                        @input="window.__datePickerEvents.push(['input',$event.target.value])"
                        @change="window.__datePickerEvents.push(['change',$event.target.value])"
                      />
                    </c-fill>
                    <c-fill name="error">Choose an arrival date.</c-fill>
                  </c-CField>
                  <button id="submit" type="submit">Submit</button>
                  <button id="reset" type="reset">Reset</button>
                </form>

                <c-CDatePicker
                  id="optional"
                  value="2026-08-19"
                  $c-props="{{value:selected,onValueChange:(value,detail)=>{{window.__datePickerEvents.push(['controlled-value',value,detail.controlled]);if(acceptValue)selected=value}}}}"
                />
                <button id="accept-value" type="button" @click="acceptValue=true">Accept value</button>
                <button id="set-value" type="button" @click="selected='2026-08-25'">Set value</button>

                <c-CDatePicker
                  id="controlled-open"
                  $c-props="{{open:controlledOpen,onOpenChange:(open,detail)=>{{window.__datePickerEvents.push(['controlled-open',open,detail.controlled]);if(acceptOpen)controlledOpen=open}}}}"
                />
                <button id="accept-open" type="button" @click="acceptOpen=true">Accept open</button>

                <form id="required-form">
                  <c-CField control_id="required-date" required>
                    <c-fill name="label">Required date</c-fill>
                    <c-fill name="default"><c-CDatePicker id="required-date" name="required-date" /></c-fill>
                    <c-fill name="error">A date is required.</c-fill>
                  </c-CField>
                  <button id="required-submit" type="submit">Submit required date</button>
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
    name = "citry_ui_date_picker_browser_i18n"
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
        source.joinpath("locales", "en-US", "citry-ui.ftl").read_text(encoding="utf8"),
        encoding="utf8",
    )
    czech = package / "locales" / "cs-CZ"
    czech.mkdir(parents=True)
    (czech / "citry-ui.ftl").write_text(
        """
citry-ui-date-picker-placeholder = Vyberte datum
citry-ui-date-picker-label = Vybrat datum
citry-ui-date-picker-change = Změnit datum, { $date }
citry-ui-date-picker-clear = Vymazat datum
citry-ui-date-picker-unavailable = Vyberte dostupné datum.
citry-ui-calendar-label = Kalendář
citry-ui-calendar-previous-month = Předchozí měsíc
citry-ui-calendar-next-month = Další měsíc
citry-ui-calendar-unavailable = Vyberte dostupné datum.
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
    assert errors == []
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="date-picker"]')]
          .every(root => root.hasAttribute('data-citry-date-picker-initialized'))"""
    )
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="calendar"]')]
          .every(root => root.hasAttribute('data-citry-calendar-initialized'))"""
    )
    assert errors == []
    return errors


def test_open_select_submit_and_reset_composed_route(page: Any, serve_citry_ui_live: Any) -> None:
    errors = _open(page, _app(), serve_citry_ui_live)
    trigger = page.locator("#arrival")
    native = page.locator("#arrival-native")
    assert native.input_value() == "2026-08-19"
    assert trigger.get_attribute("aria-expanded") == "false"
    trigger.click()
    page.wait_for_function("document.querySelector('#arrival').getAttribute('aria-expanded') === 'true'")
    page.wait_for_function("document.activeElement?.dataset.date === '2026-08-19'")
    calendar = page.locator("#arrival-calendar-calendar")
    assert calendar.locator('[data-citry-ui-part="heading"]').text_content() == "August 2026"
    assert page.evaluate("document.activeElement?.dataset.date") == "2026-08-19"
    calendar.locator('[data-date="2026-08-20"]').dispatch_event("click")
    assert native.input_value() == "2026-08-19"
    calendar.locator('[data-date="2026-08-21"]').click()
    page.wait_for_function("document.querySelector('#arrival-native').value === '2026-08-21'")
    page.wait_for_function("document.querySelector('#arrival').getAttribute('aria-expanded') === 'false'")
    assert page.evaluate("window.__datePickerEvents.slice(-4)") == [
        ["value", "2026-08-21", "calendar"],
        ["input", "2026-08-21"],
        ["change", "2026-08-21"],
        ["open", False, "selection"],
    ]
    page.locator("#submit").click()
    assert page.evaluate("window.__datePickerSubmits.at(-1)") == [["arrival", "2026-08-21"]]
    page.locator("#reset").click()
    page.wait_for_function("document.querySelector('#arrival-native').value === '2026-08-19'")
    page.wait_for_function("document.querySelector('#arrival').textContent.includes('August 19, 2026')")
    assert "August 19, 2026" in trigger.text_content()
    assert errors == []


def test_controlled_value_open_clear_and_required_invalid_focus(page: Any, serve_citry_ui_live: Any) -> None:
    errors = _open(page, _app(), serve_citry_ui_live)
    optional = page.locator("#optional")
    optional.click()
    page.locator('#optional-calendar-calendar [data-date="2026-08-21"]').click()
    assert page.locator("#optional-native").input_value() == "2026-08-19"
    assert page.evaluate("window.__datePickerEvents.at(-1)") == ["controlled-value", "2026-08-21", True]
    page.locator("#accept-value").click()
    optional.click()
    page.locator('#optional-calendar-calendar [data-date="2026-08-21"]').click()
    page.wait_for_function("document.querySelector('#optional-native').value === '2026-08-21'")
    page.locator('#optional-root [data-citry-ui-part="clear"]').click()
    page.wait_for_function("document.querySelector('#optional-native').value === ''")
    page.locator("#set-value").click()
    page.wait_for_function("document.querySelector('#optional-native').value === '2026-08-25'")

    controlled = page.locator("#controlled-open")
    controlled.click()
    assert controlled.get_attribute("aria-expanded") == "false"
    page.wait_for_function("window.__datePickerEvents.at(-1)?.[0] === 'controlled-open'")
    assert page.evaluate("window.__datePickerEvents.at(-1)") == ["controlled-open", True, True]
    page.locator("#accept-open").click()
    controlled.click()
    page.wait_for_function("document.querySelector('#controlled-open').getAttribute('aria-expanded') === 'true'")
    page.keyboard.press("Escape")
    page.wait_for_function("document.querySelector('#controlled-open').getAttribute('aria-expanded') === 'false'")

    page.locator("#required-submit").click()
    page.wait_for_function("document.querySelector('#required-date-root').dataset.invalid === ''")
    assert page.locator("#required-date").get_attribute("aria-expanded") == "true"
    page.wait_for_function("document.activeElement?.getAttribute('data-citry-ui-part') === 'day'")
    assert page.evaluate("document.activeElement?.getAttribute('data-citry-ui-part')") == "day"
    assert errors == []


def test_client_locale_switch_updates_display_trigger_title_clear_and_calendar(
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
    assert "August 19, 2026" in trigger.text_content()
    trigger.click()
    assert page.locator("#arrival-popover-title").text_content().strip() == "Choose date"
    page.evaluate("async () => Alpine.evaluate(document.querySelector('#switch-cs'), '$i18n').switchLocale('cs-CZ')")
    page.wait_for_function("document.querySelector('main')?.lang === 'cs-CZ'")
    page.wait_for_function("document.querySelector('#arrival').textContent.includes('19. srpna 2026')")
    assert trigger.get_attribute("aria-label") == "Změnit datum, \u206819. srpna 2026\u2069"
    assert page.locator("#arrival-popover-title").text_content().strip() == "Vybrat datum"
    assert page.locator('#optional-root [data-citry-ui-part="clear"]').get_attribute("aria-label") == "Vymazat datum"
    assert page.locator('#arrival-calendar-calendar [data-citry-ui-part="heading"]').text_content() == "srpen 2026"
    assert errors == []
