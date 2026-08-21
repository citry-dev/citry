"""Browser evidence for CCalendar's date grid, Form, control, and i18n contracts."""

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
              <title>Calendar browser contract</title>
              <script>window.__calendarEvents=[];window.__calendarSubmits=[];</script>
              <c-css />
            </head>
            <body>
              {provider_open}
              <section x-data="{{selected:'2026-08-19',visible:'2026-08-19',acceptValue:false,acceptVisible:false}}">
                <form id="booking" @submit.prevent="window.__calendarSubmits.push(Array.from(new FormData($event.target).entries()))">
                  <c-CField control_id="arrival" required>
                    <c-fill name="label">Arrival date</c-fill>
                    <c-fill name="description">Choose an available August day.</c-fill>
                    <c-fill name="default">
                      <c-CCalendar
                        id="arrival"
                        name="arrival"
                        value="2026-08-19"
                        min="2026-08-10"
                        max="2026-09-15"
                        c-unavailable_dates="('2026-08-20',)"
                        $c-props="{{onValueChange:(value,detail)=>window.__calendarEvents.push(['value',value,detail.source]),onVisibleDateChange:(value,detail)=>window.__calendarEvents.push(['visible',value,detail.source])}}"
                        @input="window.__calendarEvents.push(['input',$event.target.value])"
                        @change="window.__calendarEvents.push(['change',$event.target.value])"
                      />
                    </c-fill>
                    <c-fill name="error">Choose an arrival date.</c-fill>
                  </c-CField>
                  <button id="submit" type="submit">Submit</button>
                  <button id="reset" type="reset">Reset</button>
                </form>

                <c-CCalendar
                  id="controlled"
                  value="2026-08-19"
                  visible_date="2026-08-19"
                  label="Controlled calendar"
                  $c-props="{{value:selected,visibleDate:visible,onValueChange:(value,detail)=>{{window.__calendarEvents.push(['controlled-value',value,detail.controlled]);if(acceptValue)selected=value}},onVisibleDateChange:(value,detail)=>{{window.__calendarEvents.push(['controlled-visible',value,detail.controlled]);if(acceptVisible)visible=value}}}}"
                />
                <button id="accept-value" type="button" @click="acceptValue=true">Accept value</button>
                <button id="accept-visible" type="button" @click="acceptVisible=true">Accept page</button>
                <button id="set-controlled" type="button" @click="selected='2026-08-25';visible='2026-08-25'">Set controlled value</button>

                <form id="required-form">
                  <c-CField control_id="required-date" required>
                    <c-fill name="label">Required date</c-fill>
                    <c-fill name="default"><c-CCalendar id="required-date" name="required-date" /></c-fill>
                    <c-fill name="error">A date is required.</c-fill>
                  </c-CField>
                  <button id="required-submit" type="submit">Submit required date</button>
                </form>

                <c-CCalendar id="lower-boundary" visible_date="0001-01-01" label="Lower boundary" />
                <c-CCalendar id="upper-boundary" visible_date="9999-12-31" label="Upper boundary" />
                <button id="switch-cs" type="button" @click="$i18n.switchLocale('cs-CZ')">Čeština</button>
                <button id="switch-th" type="button" @click="$i18n.switchLocale('th-TH')">ไทย</button>
                <button id="switch-ar" type="button" @click="$i18n.switchLocale('ar-EG')">العربية</button>
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
    name = "citry_ui_calendar_browser_i18n"
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
citry-ui-calendar-label = Kalendář
citry-ui-calendar-previous-month = Předchozí měsíc
citry-ui-calendar-next-month = Další měsíc
citry-ui-calendar-unavailable = Vyberte dostupné datum.
""".lstrip(),
        encoding="utf8",
    )
    translations = {
        "th-TH": """
citry-ui-calendar-label = ปฏิทิน
citry-ui-calendar-previous-month = เดือนก่อนหน้า
citry-ui-calendar-next-month = เดือนถัดไป
citry-ui-calendar-unavailable = เลือกวันที่ว่าง
""".lstrip(),
        "ar-EG": """
citry-ui-calendar-label = التقويم
citry-ui-calendar-previous-month = الشهر السابق
citry-ui-calendar-next-month = الشهر التالي
citry-ui-calendar-unavailable = اختر تاريخًا متاحًا.
""".lstrip(),
    }
    for locale, content in translations.items():
        locale_root = package / "locales" / locale
        locale_root.mkdir(parents=True)
        (locale_root / "citry-ui.ftl").write_text(content, encoding="utf8")
    return name


def _open(page: Any, app: Citry, serve_citry_ui_live: Any, *, localized: bool = False) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(serve_citry_ui_live(app, _page(app, localized=localized)) + "/")
    page.wait_for_timeout(1_000)
    assert errors == []
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="calendar"]')]
          .every(root => root.hasAttribute('data-citry-calendar-initialized'))"""
    )
    return errors


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    return app


def test_grid_keyboard_unavailable_selection_formdata_and_reset(page: Any, serve_citry_ui_live: Any) -> None:
    errors = _open(page, _app(), serve_citry_ui_live)
    root = page.locator("#arrival-calendar")
    assert root.locator('[data-citry-ui-part="heading"]').text_content() == "August 2026"
    assert root.locator('[role="gridcell"][data-date]').count() == 42
    assert root.locator('[data-citry-ui-part="weekday"]').count() == 7
    assert root.locator('[role="gridcell"][tabindex="0"]').count() == 1
    assert root.locator('[data-date="2026-08-19"]').get_attribute("aria-selected") == "true"
    assert root.locator('[data-date="2026-08-20"]').get_attribute("aria-disabled") == "true"

    selected = root.locator('[data-date="2026-08-19"]')
    selected.focus()
    selected.press("ArrowRight")
    assert page.evaluate("document.activeElement?.dataset.date") == "2026-08-20"
    page.keyboard.press("Enter")
    assert page.locator("#arrival").input_value() == "2026-08-19"
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Enter")
    page.wait_for_function("document.querySelector('#arrival').value === '2026-08-21'")
    assert page.evaluate("window.__calendarEvents.slice(-3)") == [
        ["value", "2026-08-21", "keyboard"],
        ["input", "2026-08-21"],
        ["change", "2026-08-21"],
    ]
    page.locator("#submit").click()
    assert page.evaluate("window.__calendarSubmits.at(-1)") == [["arrival", "2026-08-21"]]
    page.locator("#reset").click()
    page.wait_for_function("document.querySelector('#arrival').value === '2026-08-19'")
    assert errors == []


def test_navigation_controlled_refusal_acceptance_and_reactive_value(page: Any, serve_citry_ui_live: Any) -> None:
    errors = _open(page, _app(), serve_citry_ui_live)
    root = page.locator("#controlled-calendar")
    root.locator('[data-date="2026-08-21"]').click()
    assert page.locator("#controlled").input_value() == "2026-08-19"
    assert page.evaluate("window.__calendarEvents.at(-1)") == ["controlled-value", "2026-08-21", True]
    page.locator("#accept-value").click()
    root.locator('[data-date="2026-08-21"]').click()
    page.wait_for_function("document.querySelector('#controlled').value === '2026-08-21'")

    root.locator('[data-citry-ui-part="next"]').click()
    assert root.locator('[data-citry-ui-part="heading"]').text_content() == "August 2026"
    assert page.evaluate("window.__calendarEvents.at(-1)[0]") == "controlled-visible"
    page.locator("#accept-visible").click()
    root.locator('[data-citry-ui-part="next"]').click()
    page.wait_for_function(
        "document.querySelector('#controlled-calendar [data-citry-ui-part=heading]').textContent === 'September 2026'"
    )

    page.locator("#set-controlled").click()
    page.wait_for_function("document.querySelector('#controlled').value === '2026-08-25'")
    page.wait_for_function(
        "document.querySelector('#controlled-calendar [data-citry-ui-part=heading]').textContent === 'August 2026'"
    )
    assert root.locator('[data-date="2026-08-25"]').get_attribute("aria-selected") == "true"
    assert errors == []


def test_required_invalid_focus_boundaries_and_cleanup_surface(page: Any, serve_citry_ui_live: Any) -> None:
    errors = _open(page, _app(), serve_citry_ui_live)
    page.locator("#required-submit").click()
    page.wait_for_function("document.querySelector('#required-date-calendar').dataset.invalid === ''")
    assert page.locator("#required-date-calendar").get_attribute("aria-errormessage") == "required-date-error"
    assert page.evaluate("document.activeElement?.getAttribute('data-citry-ui-part')") == "day"
    assert page.locator("#lower-boundary-calendar [data-citry-ui-part=previous]").is_disabled()
    assert page.locator("#upper-boundary-calendar [data-citry-ui-part=next]").is_disabled()
    assert page.locator("#lower-boundary-calendar [role=gridcell]").count() == 42
    assert page.locator("#upper-boundary-calendar [role=gridcell]").count() == 42
    assert errors == []


def test_client_locale_switch_updates_messages_calendar_fields_and_direction(
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
                "locales": ("en-US", "cs-CZ", "th-TH", "ar-EG"),
                "catalogs": (catalog,),
            }
        },
    )
    app.register_library(citry_ui)
    errors = _open(page, app, serve_citry_ui_live, localized=True)
    root = page.locator("#arrival-calendar")
    assert root.locator('[data-citry-ui-part="heading"]').text_content() == "August 2026"
    assert root.locator('[data-citry-ui-part="previous"]').get_attribute("aria-label") == "Previous month"
    english_label = root.locator('[data-date="2026-08-19"]').get_attribute("aria-label")

    page.evaluate("async () => Alpine.evaluate(document.querySelector('#switch-cs'), '$i18n').switchLocale('cs-CZ')")
    page.wait_for_function("document.querySelector('main')?.lang === 'cs-CZ'")
    page.wait_for_function(
        "document.querySelector('#arrival-calendar [data-citry-ui-part=previous]').getAttribute('aria-label') === 'Předchozí měsíc'"
    )
    assert root.get_attribute("aria-label") is None
    assert root.locator('[data-citry-ui-part="heading"]').text_content() == "srpen 2026"
    assert root.locator('[data-citry-ui-part="next"]').get_attribute("aria-label") == "Další měsíc"
    assert root.locator('[data-date="2026-08-19"]').get_attribute("aria-label") != english_label

    page.evaluate("async () => Alpine.evaluate(document.querySelector('#switch-th'), '$i18n').switchLocale('th-TH')")
    page.wait_for_function("document.querySelector('main')?.lang === 'th-TH'")
    assert "2569" in root.locator('[data-citry-ui-part="heading"]').text_content()
    assert root.locator('[data-date="2026-08-19"]').count() == 1

    page.evaluate("async () => Alpine.evaluate(document.querySelector('#switch-ar'), '$i18n').switchLocale('ar-EG')")
    page.wait_for_function("document.querySelector('main')?.dir === 'rtl'")
    day = root.locator('[data-date="2026-08-19"]')
    day.focus()
    day.press("ArrowLeft")
    assert page.evaluate("document.activeElement?.dataset.date") == "2026-08-20"
    assert errors == []
