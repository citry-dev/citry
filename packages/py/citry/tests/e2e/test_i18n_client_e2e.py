"""Browser acceptance for opt-in locale switching."""

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
from citry.ext.i18n.usage import CLIENT_CONTEXT_KEY, EXTRA_KEY

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.e2e


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


def _write_catalog(root: Path, *, include_lazy: bool = False) -> str:
    name = "browser_i18n_catalog_lazy" if include_lazy else "browser_i18n_catalog"
    package = root / name
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf8")
    (package / "citry-i18n.toml").write_text(
        'schema_version = 1\nowner = "browser-test"\nsource_locale = "en-US"\n',
        encoding="utf8",
    )
    for locale, message in (("en-US", "Account"), ("cs-CZ", "Účet")):
        locale_root = package / "locales" / locale
        locale_root.mkdir(parents=True)
        lazy = f"lazy-title = {'Loaded' if locale == 'en-US' else 'Načteno'}\n" if include_lazy else ""
        fragment = f"fragment-title = {'Fragment' if locale == 'en-US' else 'Fragment česky'}\n"
        count = (
            "# @param {int} $count\naccount-count = { $count ->\n    [one] One account\n   *[other] Many accounts\n}\n"
            if locale == "en-US"
            else "account-count = { $count ->\n    [one] Jeden účet\n   *[other] Více účtů\n}\n"
        )
        binding = (
            "# @param {str} $name\nbinding-title = Hello { $name }\n"
            if locale == "en-US"
            else "binding-title = Ahoj { $name }\n"
        )
        (locale_root / "common.ftl").write_text(
            f"account-title = {message}\n{lazy}{fragment}{count}{binding}",
            encoding="utf8",
        )
    return name


def test_client_switch_updates_only_client_owned_expressions(
    page: Any,
    serve_document: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _write_catalog(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    app = Citry(
        mode="development",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ", "ar-EG"),
                "catalogs": (catalog,),
                "formats": _formats(),
            }
        },
    )

    class EffectTitle(Component):
        citry = app
        js = """
            $component(({ effect, els, i18n }) => {
              effect(() => {
                els[0].textContent = i18n.tr("account-title");
              });
            });
        """
        template = '<output id="effect-title"></output>'

    class Page(Component):
        citry = app
        template = """
            <html>
              <body>
                <h1 id="server-title">{{ tr("account-title") }}</h1>
                <c-i18n c-client="True" tag="main">
                  <output id="alpine-title" x-text="$i18n.tr('account-title')"></output>
                  <output id="plural-title" x-text="$i18n.tr('account-count', { count: 2 })"></output>
                  <output
                    id="number-title"
                    x-text="$i18n.format.number('12345.50', { format: 'measurement' })"
                  ></output>
                  <output
                    id="percent-title"
                    x-text="$i18n.format.percent('0.125', { format: 'completion' })"
                  ></output>
                  <output
                    id="currency-title"
                    x-text="$i18n.format.currency('12.5', 'EUR', { format: 'money' })"
                  ></output>
                  <output
                    id="date-title"
                    x-text="$i18n.format.date({ year: 2026, month: 8, day: 11 }, { format: 'short-date' })"
                  ></output>
                  <output
                    id="time-title"
                    x-text="$i18n.format.time({ hour: 14, minute: 5 }, { format: 'short-time' })"
                  ></output>
                  <output
                    id="datetime-title"
                    x-text="$i18n.format.datetime(new Date('2026-08-11T14:05:00Z'), { format: 'short-datetime' })"
                  ></output>
                  <output
                    id="relative-title"
                    x-text="$i18n.format.relativeTime(-3, { unit: 'day', format: 'relative-day' })"
                  ></output>
                  <output
                    id="list-title"
                    x-text="$i18n.format.list(['Ada', 'Grace'], { format: 'choices' })"
                  ></output>
                  <output
                    id="unit-title"
                    x-text="$i18n.format.unit('12.5', 'kilometer', { format: 'distance' })"
                  ></output>
                  <output
                    id="parsed-number"
                    x-text="$i18n.parse.number(
                      $i18n.context.locale === 'cs-CZ' ? '12\u00a0345,50' : '12,345.50',
                      { format: 'measurement' },
                    ).value"
                  ></output>
                  <output
                    id="parsed-scientific"
                    x-text="$i18n.parse.number(
                      $i18n.context.locale === 'cs-CZ' ? '1,25e3' : '1.25e3',
                      { format: 'scientific-edit' },
                    ).value"
                  ></output>
                  <output
                    id="parsed-percent"
                    x-text="$i18n.parse.percent(
                      $i18n.context.locale === 'cs-CZ' ? '12,5\u00a0%' : '12.5%',
                      { format: 'completion' },
                    ).value"
                  ></output>
                  <c-effect-title />
                  <button id="switch" @click="$i18n.switchLocale('cs-CZ')">Switch</button>
                </c-i18n>
              </body>
            </html>
        """

    browser_errors: list[str] = []
    page.on("pageerror", lambda error: browser_errors.append(str(error)))
    page.on(
        "console",
        lambda message: browser_errors.append(message.text) if message.type == "error" else None,
    )
    i18n = app.extensions.get_extension("i18n")
    context = i18n.make_context(locale="en-US", time_zone="Europe/Prague")
    base = serve_document(Page().render(provides={"citry_i18n": context}).serialize())
    page.goto(base + "/")
    page.wait_for_timeout(1_000)
    assert page.locator("#alpine-title").inner_text() == "Account", "\n".join(browser_errors)
    assert page.locator("#plural-title").inner_text() == "Many accounts", "\n".join(browser_errors)
    assert page.locator("#effect-title").inner_text() == "Account", "\n".join(browser_errors)
    assert page.locator("#number-title").inner_text() == "12,345.50", "\n".join(browser_errors)
    assert page.locator("#percent-title").inner_text() == "12.5%", "\n".join(browser_errors)
    assert page.locator("#currency-title").inner_text() == "€12.50", "\n".join(browser_errors)
    assert page.locator("#date-title").inner_text() == "8/11/26", "\n".join(browser_errors)
    assert page.locator("#time-title").text_content() == "2:05:00 PM", "\n".join(browser_errors)
    assert page.locator("#datetime-title").text_content() == "8/11/26, 4:05:00 PM", "\n".join(browser_errors)
    assert page.locator("#relative-title").inner_text() == "3 days ago", "\n".join(browser_errors)
    assert page.locator("#list-title").text_content() == "\u2068Ada\u2069 and \u2068Grace\u2069", "\n".join(
        browser_errors
    )
    assert page.locator("#unit-title").inner_text() == "12.5 kilometers", "\n".join(browser_errors)
    assert page.locator("#parsed-number").inner_text() == "12345.50", "\n".join(browser_errors)
    assert page.locator("#parsed-scientific").inner_text() == "1250", "\n".join(browser_errors)
    assert page.locator("#parsed-percent").inner_text() == "0.125", "\n".join(browser_errors)

    plural_error = page.evaluate(
        """
        () => {
          const service = Alpine.evaluate(document.querySelector('#plural-title'), '$i18n');
          try {
            service.tr('account-count', { count: '9007199254740993' });
            return null;
          } catch (error) {
            return error.code;
          }
        }
        """
    )
    assert plural_error == "I18N_PLURAL_UNSUPPORTED"
    unit_error = page.evaluate(
        """
        () => {
          const service = Alpine.evaluate(document.querySelector('#unit-title'), '$i18n');
          try {
            service.format.unit('9007199254740993.25', 'meter', { format: 'distance' });
            return null;
          } catch (error) {
            return error.code;
          }
        }
        """
    )
    assert unit_error == "I18N_FORMAT_UNSUPPORTED"
    parse_states = page.evaluate(
        """
        () => {
          const service = Alpine.evaluate(document.querySelector('#parsed-number'), '$i18n');
          const incomplete = service.parse.number('1,', { format: 'measurement' });
          const invalid = service.parse.number('12x', { format: 'measurement' });
          const missingAffix = service.parse.percent('12.5', { format: 'completion' });
          return {
            frozen: Object.isFrozen(incomplete),
            incomplete: [incomplete.state, incomplete.error],
            invalid: [invalid.state, invalid.error],
            missingAffix: [missingAffix.state, missingAffix.error],
          };
        }
        """
    )
    assert parse_states == {
        "frozen": True,
        "incomplete": ["incomplete", "unfinished_group"],
        "invalid": ["invalid", "foreign_or_invalid_digit"],
        "missingAffix": ["incomplete", "missing_percent_affix"],
    }
    assert page.evaluate(
        """
        () => {
          const service = Alpine.evaluate(document.querySelector('#parsed-number'), '$i18n');
          return [
            typeof service.parse.date,
            typeof service.parse.time,
            typeof service.parse.datetime,
          ];
        }
        """
    ) == ["undefined", "undefined", "undefined"]

    page.locator("#switch").click()
    page.wait_for_function(
        "document.querySelector('#alpine-title')?.textContent === 'Účet' && "
        "document.querySelector('#effect-title')?.textContent === 'Účet'"
    )

    assert page.locator("#server-title").inner_text() == "Account"
    assert page.locator("#alpine-title").inner_text() == "Účet"
    assert page.locator("#effect-title").inner_text() == "Účet"
    assert page.locator("main").get_attribute("lang") == "cs-CZ"
    assert page.locator("#number-title").inner_text() == "12\N{NO-BREAK SPACE}345,50"
    assert page.locator("#percent-title").inner_text() == "12,5\N{NO-BREAK SPACE}%"
    assert page.locator("#currency-title").inner_text() == "12,50\N{NO-BREAK SPACE}€"
    assert page.locator("#date-title").inner_text() == "11. 8. 26"
    assert page.locator("#time-title").inner_text() == "14:05:00"
    assert page.locator("#datetime-title").inner_text() == "11. 8. 26 16:05:00"
    assert page.locator("#relative-title").inner_text() == "před 3 dny"
    assert page.locator("#list-title").text_content() == "\u2068Ada\u2069 a\N{NO-BREAK SPACE}\u2068Grace\u2069"
    assert page.locator("#unit-title").inner_text() == "12,5 kilometru"
    assert page.locator("#parsed-number").inner_text() == "12345.50"
    assert page.locator("#parsed-scientific").inner_text() == "1250"
    assert page.locator("#parsed-percent").inner_text() == "0.125"
    arabic_parse = page.evaluate(
        """
        async () => {
          const element = document.querySelector('#parsed-number');
          const service = Alpine.evaluate(element, '$i18n');
          await service.switchLocale('ar-EG');
          return {
            direction: service.context.direction,
            number: service.parse.number(
              '\u0661\u0662\u066c\u0663\u0664\u0665\u066b\u0665\u0660',
              { format: 'measurement' },
            ),
            percent: service.parse.percent('\u0661\u0662\u066b\u0665\u066a', { format: 'completion' }),
          };
        }
        """
    )
    assert arabic_parse == {
        "direction": "rtl",
        "number": {
            "error": None,
            "input": "\u0661\u0662\u066c\u0663\u0664\u0665\u066b\u0665\u0660",
            "state": "valid",
            "valid": True,
            "value": "12345.50",
        },
        "percent": {
            "error": None,
            "input": "\u0661\u0662\u066b\u0665\u066a",
            "state": "valid",
            "valid": True,
            "value": "0.125",
        },
    }
    assert page.locator("main").get_attribute("dir") == "rtl"
    overwrite_error = page.evaluate(
        """
        () => {
          try {
            Alpine.magic('i18n', () => null);
            return null;
          } catch (error) {
            return error.message;
          }
        }
        """
    )
    assert "$i18n is reserved by Citry" in overwrite_error


def test_checked_bindings_react_to_values_locale_and_imperative_lifecycle(
    page: Any,
    serve_document: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _write_catalog(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    app = Citry(
        mode="development",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": (catalog,),
            }
        },
    )

    class Page(Component):
        citry = app
        template = """
            <html>
              <body>
                <c-i18n c-client="True" tag="main">
                  <section x-data="{ name: 'One' }">
                    <button
                      id="bound-attribute"
                      c-aria-label="tr('binding-title', name='One')"
                      $c-tr:binding-title[aria-label]="{ name: name }"
                      @click="name = 'Two'"
                    >Change value</button>
                  </section>
                  <span id="bound-text" $c-tr:account-title>{{ tr("account-title") }}</span>
                  <output id="imperative"></output>
                  <button id="switch" @click="$i18n.switchLocale('cs-CZ')">Switch</button>
                </c-i18n>
              </body>
            </html>
        """

    browser_errors: list[str] = []
    page.on("pageerror", lambda error: browser_errors.append(str(error)))
    page.on("console", lambda message: browser_errors.append(message.text) if message.type == "error" else None)
    base = serve_document(Page().render().serialize())
    page.goto(base + "/")
    page.wait_for_timeout(1_000)
    assert page.locator("#bound-attribute").get_attribute("aria-label") == "Hello \u2068One\u2069", "\n".join(
        browser_errors
    )
    assert page.locator("#bound-text").text_content() == "Account", "\n".join(browser_errors)
    page.wait_for_function(
        "document.querySelector('#bound-attribute')?.getAttribute('aria-label') === 'Hello \u2068One\u2069' && "
        "document.querySelector('#bound-text')?.textContent === 'Account'"
    )

    page.locator("#bound-attribute").click()
    page.wait_for_function(
        "document.querySelector('#bound-attribute')?.getAttribute('aria-label') === 'Hello \u2068Two\u2069'"
    )

    immediate = page.evaluate(
        """
        () => {
          const element = document.querySelector('#imperative');
          const service = Alpine.evaluate(element, '$i18n');
          const state = Alpine.reactive({ name: 'One' });
          let plain = 'One';
          const reactive = service.bind({
            message: 'binding-title',
            values: () => ({ name: state.name }),
            onChange(text) { element.textContent = text; },
          });
          const refreshed = service.bind({
            message: 'binding-title',
            values: () => ({ name: plain }),
            onChange(text) { element.dataset.refreshed = text; },
          });
          window.__citryBindingTest = { reactive, refreshed, state, setPlain(value) { plain = value; } };
          return { text: element.textContent, refreshed: element.dataset.refreshed };
        }
        """
    )
    assert immediate == {"text": "Hello \u2068One\u2069", "refreshed": "Hello \u2068One\u2069"}

    page.evaluate("window.__citryBindingTest.state.name = 'Three'")
    page.wait_for_function("document.querySelector('#imperative')?.textContent === 'Hello \u2068Three\u2069'")
    page.evaluate(
        """
        () => {
          window.__citryBindingTest.setPlain('Four');
          window.__citryBindingTest.refreshed.refresh();
        }
        """
    )
    assert page.locator("#imperative").get_attribute("data-refreshed") == "Hello \u2068Four\u2069"

    page.evaluate(
        """
        () => {
          const service = Alpine.evaluate(document.querySelector('#imperative'), '$i18n');
          window.__citrySubscriberCommits = 0;
          service.subscribe(context => {
            if (context.locale === 'cs-CZ') throw new Error('expected subscriber failure');
          });
          service.subscribe(() => { window.__citrySubscriberCommits += 1; });
          service.bind({
            message: 'account-title',
            onChange(_text, resolved) {
              if (resolved.locale === 'cs-CZ') throw new Error('expected binding callback failure');
            },
          });
        }
        """
    )
    page.locator("#switch").click()
    page.wait_for_function(
        "document.querySelector('#bound-attribute')?.getAttribute('aria-label') === 'Ahoj \u2068Two\u2069' && "
        "document.querySelector('#bound-text')?.textContent === 'Účet' && "
        "document.querySelector('#imperative')?.textContent === 'Ahoj \u2068Three\u2069'"
    )
    assert page.locator("#imperative").get_attribute("data-refreshed") == "Ahoj \u2068Four\u2069"
    assert page.evaluate("window.__citrySubscriberCommits") == 2

    page.evaluate("window.__citryBindingTest.reactive.dispose()")
    page.evaluate("window.__citryBindingTest.state.name = 'Five'")
    page.wait_for_timeout(100)
    assert page.locator("#imperative").inner_text() == "Ahoj \u2068Three\u2069"


def test_connected_provider_fetches_locale_and_dynamic_message_partitions(
    page: Any,
    serve_live: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _write_catalog(tmp_path, include_lazy=True)
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    app = Citry(
        mode="development",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": (catalog,),
            }
        },
    )
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = """
            <html>
              <body>
                <c-i18n c-client="True" tag="main">
                  <output id="title" x-text="$i18n.tr('account-title')"></output>
                  <button id="switch" @click="$i18n.switchLocale('cs-CZ')">Switch</button>
                  <section x-data="{ result: '', messageKey: 'lazy-title' }">
                    <output id="lazy" x-text="result"></output>
                      <button
                        id="load-lazy"
                        @click="$i18n.ensureMessages(messageKey).then(() => { result = $i18n.tr(messageKey) })"
                    >Load</button>
                  </section>
                </c-i18n>
              </body>
            </html>
        """

    browser_errors: list[str] = []
    page.on("pageerror", lambda error: browser_errors.append(str(error)))
    page.on(
        "console",
        lambda message: browser_errors.append(message.text) if message.type == "error" else None,
    )
    base = serve_live(app, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#title')?.textContent === 'Account'")

    page.route("**/citry/ext/i18n/messages", lambda route: route.fulfill(status=503, body="unavailable"))
    failed = page.evaluate(
        """
        async () => {
          const service = Alpine.evaluate(document.querySelector('#title'), '$i18n');
          try {
            await service.switchLocale('cs-CZ');
            return null;
          } catch (error) {
            return { message: String(error.message || error), phase: service.status.phase };
          }
        }
        """
    )
    assert failed == {
        "message": "[Citry] i18n: the cs-CZ message request failed with 503.",
        "phase": "error",
    }
    assert page.locator("main").get_attribute("lang") == "en-US"
    assert page.locator("#title").inner_text() == "Account"
    browser_errors.clear()
    page.unroute("**/citry/ext/i18n/messages")

    page.locator("#switch").click()
    page.wait_for_function("document.querySelector('#title')?.textContent === 'Účet'")
    page.locator("#load-lazy").click()
    page.wait_for_timeout(1_000)

    assert page.locator("#lazy").inner_text() == "Načteno", "\n".join(browser_errors)
    assert browser_errors == []


def test_nested_client_providers_inherit_or_pin_locale_and_server_provider_blocks_client_context(
    page: Any,
    serve_document: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _write_catalog(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    app = Citry(
        mode="development",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": (catalog,),
            }
        },
    )

    class Page(Component):
        citry = app
        template = """
            <html>
              <body>
                <c-i18n c-client="True" tag="main">
                  <output id="outer" x-text="$i18n.tr('account-title')"></output>
                  <c-i18n c-client="True" tag="section">
                    <output id="inherited" x-text="$i18n.tr('account-title')"></output>
                  </c-i18n>
                  <c-i18n c-client="True" locale="en-US" tag="section">
                    <output id="fixed" x-text="$i18n.tr('account-title')"></output>
                  </c-i18n>
                  <c-i18n tag="section">
                    <output
                      id="blocked"
                      x-text="$inject('citry_i18n', null) === null ? 'blocked' : 'leaked'"
                    ></output>
                  </c-i18n>
                  <button id="switch" @click="$i18n.switchLocale('cs-CZ')">Switch</button>
                </c-i18n>
              </body>
            </html>
        """

    base = serve_document(Page().render().serialize())
    page.goto(base + "/")
    page.wait_for_function(
        "document.querySelector('#outer')?.textContent === 'Account' && "
        "document.querySelector('#inherited')?.textContent === 'Account' && "
        "document.querySelector('#fixed')?.textContent === 'Account' && "
        "document.querySelector('#blocked')?.textContent === 'blocked'"
    )

    overlapping = page.evaluate(
        """
        async () => {
          const outer = Alpine.evaluate(document.querySelector('#outer'), '$i18n');
          const inherited = Alpine.evaluate(document.querySelector('#inherited'), '$i18n');
          const older = outer.switchLocale('cs-CZ');
          const newer = inherited.switchLocale('en-US');
          const [olderResult, newerResult] = await Promise.all([older, newer]);
          return {
            older: olderResult.status,
            newer: newerResult.status,
            outerStatus: outer.status.phase,
            inheritedStatus: inherited.status.phase,
          };
        }
        """
    )
    assert overlapping == {
        "older": "stale",
        "newer": "committed",
        "outerStatus": "ready",
        "inheritedStatus": "ready",
    }
    assert page.locator("#outer").inner_text() == "Účet"
    assert page.locator("#inherited").inner_text() == "Account"

    page.evaluate("Alpine.evaluate(document.querySelector('#outer'), '$i18n').switchLocale('en-US')")
    page.wait_for_function(
        "document.querySelector('#outer')?.textContent === 'Account' && "
        "document.querySelector('#inherited')?.textContent === 'Account'"
    )

    page.locator("#switch").click()
    page.wait_for_function(
        "document.querySelector('#outer')?.textContent === 'Účet' && "
        "document.querySelector('#inherited')?.textContent === 'Účet'"
    )

    assert page.locator("#fixed").inner_text() == "Account"
    assert page.locator("#blocked").inner_text() == "blocked"


def test_checked_bindings_keep_logical_provider_ownership_through_slots_and_teleports(
    page: Any,
    serve_document: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _write_catalog(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    app = Citry(
        mode="development",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": (catalog,),
            }
        },
    )

    class Card(Component):
        citry = app
        template = '<section class="card"><c-slot /></section>'

    class Page(Component):
        citry = app
        template = """
            <html>
              <body>
                <c-i18n c-client="True" tag="main">
                  <div id="teleport-destination"></div>
                  <c-Card>
                    <span id="slotted-title" $c-tr:account-title>{{ tr("account-title") }}</span>
                    <template x-teleport="#teleport-destination">
                      <span id="teleported-title" $c-tr:account-title>{{ tr("account-title") }}</span>
                    </template>
                  </c-Card>
                  <button id="switch" @click="$i18n.switchLocale('cs-CZ')">Switch</button>
                </c-i18n>
              </body>
            </html>
        """

    base = serve_document(Page().render().serialize())
    page.goto(base + "/")
    page.wait_for_function(
        "document.querySelector('#slotted-title')?.textContent === 'Account' && "
        "document.querySelector('#teleport-destination #teleported-title')?.textContent === 'Account'"
    )
    page.locator("#switch").click()
    page.wait_for_function(
        "document.querySelector('#slotted-title')?.textContent === 'Účet' && "
        "document.querySelector('#teleport-destination #teleported-title')?.textContent === 'Účet'"
    )


def test_one_hundred_message_switch_stays_atomic_and_within_the_commit_budget(
    page: Any,
    serve_document: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "browser_i18n_large_catalog"
    package = tmp_path / name
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf8")
    (package / "citry-i18n.toml").write_text(
        'schema_version = 1\nowner = "browser-performance"\nsource_locale = "en-US"\n',
        encoding="utf8",
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
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": (name,),
            }
        },
    )
    outputs = "\n".join(
        f'<output data-switch-message="{index}" x-text="$i18n.tr(\'switch-message-{index:03d}\')"></output>'
        for index in range(100)
    )

    class Page(Component):
        citry = app
        template = f"""
            <html>
              <body>
                <c-i18n c-client="True" tag="main">
                  {outputs}
                </c-i18n>
              </body>
            </html>
        """

    base = serve_document(Page().render().serialize())
    page.goto(base + "/")
    page.wait_for_function(
        "document.querySelectorAll('[data-switch-message]').length === 100 "
        "&& document.querySelector('[data-switch-message=\"99\"]')?.textContent === 'English 099'"
    )
    result = page.evaluate(
        """
        async () => {
          const host = document.querySelector('[data-switch-message]');
          const service = Alpine.evaluate(host, '$i18n');
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
        }
        """
    )

    assert result["samples"] == 30
    assert result["mixedFrames"] == 0
    assert result["p95"] <= 50


def test_inserted_fragment_contributes_messages_to_an_existing_provider(
    page: Any,
    serve_live: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _write_catalog(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    app = Citry(
        mode="development",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": (catalog,),
            }
        },
    )
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = """
            <html>
              <body>
                <c-i18n c-client="True" tag="main">
                  <div id="fragment-target"></div>
                  <button id="switch" @click="$i18n.switchLocale('cs-CZ')">Switch</button>
                </c-i18n>
              </body>
            </html>
        """

    class Fragment(Component):
        citry = app
        template = '<output id="fragment-title" x-text="$i18n.tr(\'fragment-title\')"></output>'

    rendered_page = Page().render()
    provider_records = [
        record for record in rendered_page.context.extra[EXTRA_KEY].values() if record.provider is not None
    ]
    assert len(provider_records) == 1
    provider_record = provider_records[0]
    fragment_html = (
        Fragment()
        .render(
            provides={
                "citry_i18n": provider_record.provider.context,
                CLIENT_CONTEXT_KEY: provider_record.render_id,
            }
        )
        .serialize(deps_strategy="fragment")
    )

    browser_errors: list[str] = []
    page.on("pageerror", lambda error: browser_errors.append(str(error)))
    page.on("console", lambda message: browser_errors.append(message.text) if message.type == "error" else None)
    base = serve_live(app, rendered_page.serialize(), "")
    page.goto(base + "/")
    page.evaluate(
        """
        async ([html]) => {
          await Citry.events.applyActions([
            { action: 'render', target: '#fragment-target', swap: 'inner', html },
          ]);
        }
        """,
        [fragment_html],
    )
    page.wait_for_function("document.querySelector('#fragment-title')?.textContent === 'Fragment'")

    page.locator("#switch").click()
    page.wait_for_function("document.querySelector('#fragment-title')?.textContent === 'Fragment česky'")


def test_fragment_binding_prepares_the_provider_current_locale_before_activation(
    page: Any,
    serve_live: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _write_catalog(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    app = Citry(
        mode="development",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": (catalog,),
            }
        },
    )
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = """
            <html>
              <body>
                <c-i18n c-client="True" tag="main">
                  <div id="fragment-target"></div>
                  <button id="switch" @click="$i18n.switchLocale('cs-CZ')">Switch</button>
                </c-i18n>
              </body>
            </html>
        """

    class Fragment(Component):
        citry = app
        js = """
            $component(({ els }) => {
              window.__fragmentTextAtActivation = els[0].querySelector('#fragment-title').textContent;
              window.__fragmentTemplateTextAtActivation = els[0]
                .querySelector('#fragment-template')
                .content.querySelector('#fragment-template-title').textContent;
            });
        """
        template = """
            <c-i18n c-client="True" tag="section">
              <output id="fragment-title" $c-tr:fragment-title>{{ tr("fragment-title") }}</output>
              <template id="fragment-template">
                <output id="fragment-template-title" $c-tr:fragment-title>{{ tr("fragment-title") }}</output>
              </template>
            </c-i18n>
        """

    rendered_page = Page().render()
    (provider_record,) = [
        record for record in rendered_page.context.extra[EXTRA_KEY].values() if record.provider is not None
    ]

    def render_fragment() -> str:
        return (
            Fragment()
            .render(
                provides={
                    "citry_i18n": provider_record.provider.context,
                    CLIENT_CONTEXT_KEY: provider_record.render_id,
                }
            )
            .serialize(deps_strategy="fragment")
        )

    fragment_html = render_fragment()
    morph_fragment_html = render_fragment()

    browser_errors: list[str] = []
    page.on("pageerror", lambda error: browser_errors.append(str(error)))
    page.on("console", lambda message: browser_errors.append(message.text) if message.type == "error" else None)
    base = serve_live(app, rendered_page.serialize(), "")
    page.goto(base + "/")
    page.locator("#switch").click()
    page.wait_for_function("document.querySelector('main')?.lang === 'cs-CZ'")
    page.evaluate(
        """
        async ([html]) => {
          await Citry.events.applyActions([
            { action: 'render', target: '#fragment-target', swap: 'inner', html },
          ]);
        }
        """,
        [fragment_html],
    )
    page.wait_for_function("document.querySelector('#fragment-title')?.textContent === 'Fragment česky'")
    assert page.evaluate("window.__fragmentTextAtActivation") == "Fragment česky", repr(browser_errors)
    assert page.evaluate("window.__fragmentTemplateTextAtActivation") == "Fragment česky", repr(browser_errors)
    assert page.locator("#fragment-title").text_content() == "Fragment česky"
    assert page.locator("#fragment-title").evaluate("element => element.closest('section').lang") == "cs-CZ"

    page.evaluate("window.__removedFragment = document.querySelector('#fragment-title')")
    page.evaluate(
        """
        async () => {
          await Citry.events.applyActions([
            { action: 'render', target: '#fragment-target', swap: 'inner', html: '<span id="replacement"></span>' },
          ]);
        }
        """
    )
    page.wait_for_function("document.querySelector('#replacement') !== null")
    page.evaluate("Alpine.evaluate(document.querySelector('#switch'), '$i18n').switchLocale('en-US')")
    page.wait_for_function("document.querySelector('main')?.lang === 'en-US'")
    assert page.evaluate("window.__removedFragment.textContent") == "Fragment česky"

    page.locator("#switch").click()
    page.wait_for_function("document.querySelector('main')?.lang === 'cs-CZ'")
    page.evaluate(
        """
        async ([html]) => {
          await Citry.events.applyActions([
            { action: 'render', target: '#replacement', swap: 'morph', html },
          ]);
        }
        """,
        [morph_fragment_html],
    )
    page.wait_for_function(
        "document.querySelector('#fragment-title')?.textContent === 'Fragment česky' && "
        "window.__fragmentTextAtActivation === 'Fragment česky' && "
        "window.__fragmentTemplateTextAtActivation === 'Fragment česky'"
    )
    assert browser_errors == []


def test_failed_fragment_locale_preparation_keeps_the_live_region_unchanged(
    page: Any,
    serve_live: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = _write_catalog(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    app = Citry(
        mode="development",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": (catalog,),
            }
        },
    )
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = """
            <html>
              <body>
                <c-i18n c-client="True" tag="main">
                  <div id="fragment-target"><span id="original">Original</span></div>
                  <button id="switch" @click="$i18n.switchLocale('cs-CZ')">Switch</button>
                </c-i18n>
              </body>
            </html>
        """

    class Fragment(Component):
        citry = app
        template = '<output id="failed-fragment" $c-tr:fragment-title>{{ tr("fragment-title") }}</output>'

    rendered_page = Page().render()
    (provider_record,) = [
        record for record in rendered_page.context.extra[EXTRA_KEY].values() if record.provider is not None
    ]
    fragment_html = (
        Fragment()
        .render(
            provides={
                "citry_i18n": provider_record.provider.context,
                CLIENT_CONTEXT_KEY: provider_record.render_id,
            }
        )
        .serialize(deps_strategy="fragment")
    )

    base = serve_live(app, rendered_page.serialize(), "")
    page.goto(base + "/")
    page.locator("#switch").click()
    page.wait_for_function("document.querySelector('main')?.lang === 'cs-CZ'")
    page.route("**/citry/ext/i18n/messages", lambda route: route.fulfill(status=503, body="unavailable"))
    error = page.evaluate(
        """
        async ([html]) => {
          try {
            await Citry.events.applyActions([
              { action: 'render', target: '#fragment-target', swap: 'inner', html },
            ]);
            return null;
          } catch (failure) {
            return String(failure.message || failure);
          }
        }
        """,
        [fragment_html],
    )

    assert "message request failed with 503" in error
    assert page.locator("#fragment-target").count() == 1
    assert page.locator("#original").inner_text() == "Original"
    assert page.locator("#failed-fragment").count() == 0
    assert page.locator("main").get_attribute("lang") == "cs-CZ"
