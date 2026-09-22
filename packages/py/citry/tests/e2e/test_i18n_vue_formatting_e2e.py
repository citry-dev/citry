"""Browser coverage for Vue i18n formatting and localized parsing."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import (
    Citry,
    Component,
    CurrencyFormat,
    DateFormat,
    DateTimeFormat,
    FormatRegistry,
    ListFormat,
    NumberFormat,
    NumberInput,
    PercentFormat,
    RelativeTimeFormat,
    TimeFormat,
    UnitFormat,
)

pytestmark = pytest.mark.e2e

if TYPE_CHECKING:
    from pathlib import Path


def _formats() -> FormatRegistry:
    return FormatRegistry(
        number={
            "measurement": NumberFormat(),
            "scientific-edit": NumberFormat(input=NumberInput(notation="decimal_or_scientific")),
        },
        percent={"completion": PercentFormat()},
        currency={"money": CurrencyFormat()},
        date={"short-date": DateFormat(length="short")},
        datetime={"short-datetime": DateTimeFormat(length="short")},
        time={"short-time": TimeFormat(length="short")},
        relative_time={"relative-day": RelativeTimeFormat()},
        list={"choices": ListFormat(kind="and", length="wide")},
        unit={"distance": UnitFormat(width="long")},
    )


def test_vue_i18n_large_catalog_switch_stays_atomic(
    page: Any,
    serve_document: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_name = "browser_i18n_large_catalog_vue"
    package = tmp_path / package_name
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf8")
    (package / "citry-i18n.toml").write_text(
        'schema_version = 1\nowner = "browser-performance"\nsource_locale = "en-US"\n', encoding="utf8"
    )
    for locale, prefix in (("en-US", "English"), ("cs-CZ", "Czech")):
        locale_root = package / "locales" / locale
        locale_root.mkdir(parents=True)
        source = "\n".join(f"switch-message-{index:03d} = {prefix} {index:03d}" for index in range(100))
        (locale_root / "messages.ftl").write_text(source, encoding="utf8")
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()

    app = Citry(
        mode="development",
        autodiscover=False,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": (package_name,),
            }
        },
    )
    outputs = "\n".join(
        f'<output data-switch-message="{index}" v-text="$i18n.tr(\'switch-message-{index:03d}\')"></output>'
        for index in range(100)
    )

    class I18nProbe(Component):
        citry = app
        template = '<output id="i18n-probe" v-text="$i18n.tr(\'switch-message-000\')"></output>'
        js = """$component({onServerRender({component}){
          globalThis.__i18nService = component.$i18n;
        }});"""

    class Page(Component):
        citry = app
        template = f"""
            <html><body><c-i18n c-client="True" tag="main">
              {outputs}
              <c-i18n-probe />
            </c-i18n></body></html>
        """

    page.goto(serve_document(Page().render().serialize()) + "/")
    page.wait_for_function(
        "document.querySelectorAll('[data-switch-message]').length === 100 "
        "&& document.querySelector('[data-switch-message=\"99\"]')?.textContent === 'English 099' "
        "&& globalThis.__i18nService"
    )
    result = page.evaluate(
        """async () => {
          const service = globalThis.__i18nService;
          const durations = [];
          let running = true;
          let mixedFrames = 0;
          const sample = () => {
            const values = Array.from(document.querySelectorAll('[data-switch-message]'))
              .map(element => element.textContent.startsWith('English') ? 'en' : 'cs');
            if (new Set(values).size > 1) mixedFrames += 1;
            if (running) requestAnimationFrame(sample);
          };
          requestAnimationFrame(sample);
          for (let index = 0; index < 30; index += 1) {
            const locale = index % 2 === 0 ? 'cs-CZ' : 'en-US';
            const started = performance.now();
            await service.switchLocale(locale);
            durations.push(performance.now() - started);
            await new Promise(resolve => requestAnimationFrame(resolve));
          }
          running = false;
          durations.sort((left, right) => left - right);
          return {
            mixedFrames,
            p95: durations[Math.ceil(durations.length * 0.95) - 1],
            samples: durations.length,
          };
        }"""
    )
    assert result["samples"] == 30
    assert result["mixedFrames"] == 0
    assert result["p95"] <= 50


def test_vue_i18n_formats_and_parsers_follow_locale(page: Any, serve_document: Any) -> None:
    app = Citry(
        autodiscover=False,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "formats": _formats(),
            }
        },
    )

    class Page(Component):
        citry = app
        template = """
            <html><body>
              <c-i18n c-client="True" tag="main">
                <output id="number" v-text="$i18n.format.number('12345.50', { format: 'measurement' })"></output>
                <output id="percent" v-text="$i18n.format.percent('0.125', { format: 'completion' })"></output>
                <output id="currency" v-text="$i18n.format.currency('12.5', 'EUR', { format: 'money' })"></output>
                <output id="date"
                  v-text="$i18n.format.date({ year: 2026, month: 8, day: 11 }, { format: 'short-date' })">
                </output>
                <output id="time"
                  v-text="$i18n.format.time({ hour: 14, minute: 5 }, { format: 'short-time' })">
                </output>
                <output id="relative"
                  v-text="$i18n.format.relativeTime(-3, { unit: 'day', format: 'relative-day' })">
                </output>
                <output id="list" v-text="$i18n.format.list(['Ada', 'Grace'], { format: 'choices' })"></output>
                <output id="unit" v-text="$i18n.format.unit('12.5', 'kilometer', { format: 'distance' })"></output>
                <output id="parsed-number"
                  v-text="$i18n.parse.number(
                    $i18n.context.locale === 'cs-CZ' ? '12\\u00a0345,50' : '12,345.50',
                    { format: 'measurement' },
                  ).value">
                </output>
                <output id="parsed-percent"
                  v-text="$i18n.parse.percent(
                    $i18n.context.locale === 'cs-CZ' ? '12,5\\u00a0%' : '12.5%',
                    { format: 'completion' },
                  ).value">
                </output>
                <button id="switch" @click="$i18n.switchLocale('cs-CZ')">Switch</button>
              </c-i18n>
            </body></html>
        """

    i18n = app.extensions.get_extension("i18n")
    context = i18n.make_context(locale="en-US", time_zone="Europe/Prague")
    page.goto(serve_document(Page().render(provides={"citry_i18n": context}).serialize()) + "/")
    page.wait_for_function("document.querySelector('#number')?.textContent === '12,345.50'")

    assert page.locator("#percent").text_content() == "12.5%"
    assert page.locator("#currency").text_content() == "€12.50"
    assert page.locator("#date").text_content() == "8/11/26"
    assert page.locator("#time").text_content() == "2:05:00 PM"
    assert page.locator("#relative").text_content() == "3 days ago"
    assert page.locator("#list").text_content() == "\u2068Ada\u2069 and \u2068Grace\u2069"
    assert page.locator("#unit").text_content() == "12.5 kilometers"
    assert page.locator("#parsed-number").text_content() == "12345.50"
    assert page.locator("#parsed-percent").text_content() == "0.125"

    parse_states = page.evaluate(
        """() => {
          const service = [...CitryStable._apps.values()]
            .flatMap(app => [...app.mounted.values()])
            .map(value => value.component.$i18n).find(Boolean);
          const incomplete = service.parse.number('1,', {format: 'measurement'});
          const invalid = service.parse.number('12x', {format: 'measurement'});
          return {
            incomplete: [incomplete.state, incomplete.error],
            invalid: [invalid.state, invalid.error],
          };
        }"""
    )
    assert parse_states == {
        "incomplete": ["incomplete", "unfinished_group"],
        "invalid": ["invalid", "foreign_or_invalid_digit"],
    }

    page.locator("#switch").click()
    page.wait_for_function("document.querySelector('#number')?.textContent === '12\\u00a0345,50'")
    assert page.locator("#percent").text_content() == "12,5\u00a0%"
    assert page.locator("#currency").text_content() == "12,50\u00a0€"
    assert page.locator("#date").text_content() == "11. 8. 26"
    assert page.locator("#time").text_content() == "14:05:00"
    assert page.locator("#relative").text_content() == "před 3 dny"
    assert page.locator("#list").text_content() == "\u2068Ada\u2069 a\u00a0\u2068Grace\u2069"
    assert page.locator("#unit").text_content() == "12,5 kilometru"
    assert page.locator("#parsed-number").text_content() == "12345.50"
    assert page.locator("#parsed-percent").text_content() == "0.125"
