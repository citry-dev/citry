"""Browser evidence for CDateRange draft, Forms, control, and i18n."""

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
              <title>DateRange browser contract</title>
              <script>window.__rangeEvents=[];window.__rangeSubmits=[];</script>
              <c-css />
            </head>
            <body>
              {provider_open}
              <section x-data="{{value:{{start:'2026-08-19',end:'2026-08-24'}},controlledOpen:false,acceptValue:false,acceptOpen:false}}">
                <form id="booking" @submit.prevent="window.__rangeSubmits.push(Array.from(new FormData($event.target).entries()))">
                  <fieldset>
                    <legend>Stay dates</legend>
                    <c-CDateRange
                      id="stay"
                      start_name="arrival"
                      end_name="departure"
                      start="2026-08-19"
                      end="2026-08-24"
                      min="2026-08-10"
                      max="2026-09-15"
                      required
                      $c-props="{{onValueChange:(value,detail)=>window.__rangeEvents.push(['value',value,detail.source]),onOpenChange:(open,detail)=>window.__rangeEvents.push(['open',open,detail.reason])}}"
                      @input="window.__rangeEvents.push(['input',$event.target.dataset.citryUiPart,$event.target.value])"
                      @change="window.__rangeEvents.push(['change',$event.target.dataset.citryUiPart,$event.target.value])"
                    />
                  </fieldset>
                  <button id="submit" type="submit">Submit</button>
                  <button id="reset" type="reset">Reset</button>
                </form>

                <c-CDateRange
                  id="optional"
                  start="2026-08-19"
                  end="2026-08-24"
                  min="2026-08-10"
                  max="2026-09-15"
                  $c-props="{{value,onValueChange:(next,detail)=>{{window.__rangeEvents.push(['controlled-value',next,detail.controlled]);if(acceptValue)value=next}}}}"
                />
                <button id="accept-value" type="button" @click="acceptValue=true">Accept value</button>
                <button id="set-value" type="button" @click="value={{start:'2026-08-25',end:'2026-08-27'}}">Set value</button>

                <c-CDateRange
                  id="controlled-open"
                  min="2026-08-10"
                  max="2026-09-15"
                  $c-props="{{open:controlledOpen,onOpenChange:(open,detail)=>{{window.__rangeEvents.push(['controlled-open',open,detail.controlled]);if(acceptOpen)controlledOpen=open}}}}"
                />
                <button id="accept-open" type="button" @click="acceptOpen=true">Accept open</button>

                <c-CDateRange id="blocked" min="2026-08-10" max="2026-09-15" c-unavailable_dates="('2026-08-21',)" />

                <form id="required-form">
                  <c-CDateRange id="required-range" start_name="start" end_name="end" min="2026-08-10" max="2026-09-15" required />
                  <button id="required-submit" type="submit">Submit required range</button>
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
    name = "citry_ui_date_range_browser_i18n"
    package = root / name
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf8")
    (package / "citry-i18n.toml").write_text(
        'schema_version = 1\nowner = "citry-ui"\nsource_locale = "en-US"\n', encoding="utf8"
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
citry-ui-date-range-placeholder = Vyberte data
citry-ui-date-range-label = Vybrat rozsah dat
citry-ui-date-range-change = Změnit rozsah dat, { $start } až { $end }
citry-ui-date-range-start-label = Počáteční datum
citry-ui-date-range-end-label = Koncové datum
citry-ui-date-range-clear = Vymazat rozsah dat
citry-ui-date-range-unavailable = Vyberte dostupný rozsah dat.
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
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="date-range"]')]
          .every(root => root.hasAttribute('data-citry-date-range-initialized'))"""
    )
    page.wait_for_function(
        """() => [...document.querySelectorAll('.cui-date-range__calendar')]
          .every(root => root.hasAttribute('data-citry-calendar-initialized'))"""
    )
    assert errors == []
    return errors


def test_draft_preview_commit_submit_and_reset(page: Any, serve_citry_ui_live: Any) -> None:
    errors = _open(page, _app(), serve_citry_ui_live)
    trigger = page.locator("#stay")
    trigger.click()
    page.wait_for_function("document.querySelector('#stay').getAttribute('aria-expanded') === 'true'")
    calendar = page.locator("#stay-calendar-calendar")
    calendar.locator('[data-date="2026-08-20"]').click()
    assert page.locator("#stay-start").input_value() == "2026-08-19"
    assert calendar.locator('[data-date="2026-08-20"]').get_attribute("data-range-start") == ""
    calendar.locator('[data-date="2026-08-23"]').hover()
    assert calendar.locator('[data-date="2026-08-22"]').get_attribute("data-range-preview") == ""
    calendar.locator('[data-date="2026-08-23"]').click()
    page.wait_for_function("document.querySelector('#stay-start').value === '2026-08-20'")
    page.wait_for_function("document.querySelector('#stay-end').value === '2026-08-23'")
    page.wait_for_function("document.querySelector('#stay').getAttribute('aria-expanded') === 'false'")
    assert page.evaluate("window.__rangeEvents.slice(-6)") == [
        ["value", {"start": "2026-08-20", "end": "2026-08-23"}, "calendar"],
        ["input", "start-input", "2026-08-20"],
        ["change", "start-input", "2026-08-20"],
        ["input", "end-input", "2026-08-23"],
        ["change", "end-input", "2026-08-23"],
        ["open", False, "selection"],
    ]
    page.locator("#submit").click()
    assert page.evaluate("window.__rangeSubmits.at(-1)") == [["arrival", "2026-08-20"], ["departure", "2026-08-23"]]
    page.locator("#reset").click()
    page.wait_for_function("document.querySelector('#stay-start').value === '2026-08-19'")
    assert page.locator("#stay-end").input_value() == "2026-08-24"
    assert errors == []


def test_blocked_range_same_day_controlled_clear_open_and_invalid_focus(page: Any, serve_citry_ui_live: Any) -> None:
    errors = _open(page, _app(), serve_citry_ui_live)
    blocked = page.locator("#blocked")
    blocked.click()
    blocked_calendar = page.locator("#blocked-calendar-calendar")
    blocked_calendar.locator('[data-date="2026-08-20"]').click()
    blocked_calendar.locator('[data-date="2026-08-22"]').click()
    assert page.locator("#blocked-start").input_value() == ""
    assert blocked.get_attribute("aria-expanded") == "true"
    page.keyboard.press("Escape")

    optional = page.locator("#optional")
    optional.click()
    calendar = page.locator("#optional-calendar-calendar")
    calendar.locator('[data-date="2026-08-25"]').click()
    calendar.locator('[data-date="2026-08-25"]').click()
    assert page.locator("#optional-start").input_value() == "2026-08-19"
    assert page.evaluate("window.__rangeEvents.at(-1)") == [
        "controlled-value",
        {"start": "2026-08-25", "end": "2026-08-25"},
        True,
    ]
    page.locator("#accept-value").click()
    optional.click()
    calendar.locator('[data-date="2026-08-25"]').click()
    calendar.locator('[data-date="2026-08-26"]').click()
    page.wait_for_function("document.querySelector('#optional-end').value === '2026-08-26'")
    page.locator('#optional-root [data-citry-ui-part="clear"]').click()
    page.wait_for_function("document.querySelector('#optional-start').value === ''")
    page.locator("#set-value").click()
    page.wait_for_function("document.querySelector('#optional-end').value === '2026-08-27'")

    controlled = page.locator("#controlled-open")
    controlled.click()
    assert controlled.get_attribute("aria-expanded") == "false"
    page.wait_for_function("window.__rangeEvents.at(-1)?.[0] === 'controlled-open'")
    assert page.evaluate("window.__rangeEvents.at(-1)") == ["controlled-open", True, True]
    page.locator("#accept-open").click()
    controlled.click()
    page.wait_for_function("document.querySelector('#controlled-open').getAttribute('aria-expanded') === 'true'")
    page.keyboard.press("Escape")
    page.wait_for_function("document.querySelector('#controlled-open').getAttribute('aria-expanded') === 'false'")
    page.wait_for_function("document.activeElement?.id === 'controlled-open'")

    page.locator("#required-submit").click()
    page.wait_for_function("document.querySelector('#required-range-root').dataset.invalid === ''")
    assert page.locator("#required-range").get_attribute("aria-expanded") == "true"
    page.wait_for_function("document.activeElement?.getAttribute('data-citry-ui-part') === 'day'")
    assert errors == []


def test_client_locale_switch_updates_summary_labels_title_clear_and_endpoints(
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
            "i18n": {"source_locale": "en-US", "locales": ("en-US", "cs-CZ"), "catalogs": (catalog,)}
        },
    )
    app.register_library(citry_ui)
    errors = _open(page, app, serve_citry_ui_live, localized=True)
    trigger = page.locator("#stay")
    assert "August 19, 2026" in trigger.text_content()
    trigger.click()
    assert page.locator("#stay-popover-title").text_content().strip() == "Choose date range"
    page.evaluate("async () => Alpine.evaluate(document.querySelector('#switch-cs'), '$i18n').switchLocale('cs-CZ')")
    page.wait_for_function("document.querySelector('main')?.lang === 'cs-CZ'")
    page.wait_for_function("document.querySelector('#stay').textContent.includes('19. srpna 2026')")
    assert (
        trigger.get_attribute("aria-label")
        == "Změnit rozsah dat, \u206819. srpna 2026\u2069 až \u206824. srpna 2026\u2069"
    )
    assert page.locator("#stay-popover-title").text_content().strip() == "Vybrat rozsah dat"
    assert (
        page.locator('#optional-root [data-citry-ui-part="clear"]').get_attribute("aria-label") == "Vymazat rozsah dat"
    )
    assert page.locator("#stay-start").input_value() == "2026-08-19"
    assert page.locator("#stay-end").input_value() == "2026-08-24"
    page.wait_for_function(
        "document.querySelector('#stay-calendar-calendar')?.getAttribute('aria-label') === 'Vybrat rozsah dat'"
    )
    assert page.locator("#stay-calendar-calendar").get_attribute("aria-label") == "Vybrat rozsah dat"
    assert errors == []
