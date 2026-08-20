"""Browser evidence for Citry UI's catalog-owned translation destinations."""

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


def _write_catalog(root: Path) -> str:
    name = "citry_ui_browser_test_i18n"
    package = root / name
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf8")
    (package / "citry-i18n.toml").write_text(
        'schema_version = 1\nowner = "citry-ui"\nsource_locale = "en-US"\n',
        encoding="utf8",
    )
    source = importlib.resources.files("citry_ui_i18n")
    (package / "formats.json").write_text(
        source.joinpath("formats.json").read_text(encoding="utf8"),
        encoding="utf8",
    )
    english = package / "locales" / "en-US"
    english.mkdir(parents=True)
    (english / "citry-ui.ftl").write_text(
        source.joinpath("locales", "en-US", "citry-ui.ftl").read_text(encoding="utf8"),
        encoding="utf8",
    )
    translations = {
        "cs-CZ": """
citry-ui-breadcrumbs-label = Drobečková navigace
citry-ui-combobox-open = Zobrazit možnosti
citry-ui-combobox-close = Skrýt možnosti
citry-ui-pagination-label = Stránkování
citry-ui-pagination-page = Strana { $page }
citry-ui-pagination-previous = Předchozí strana
citry-ui-pagination-next = Další strana
citry-ui-tags-input-remove = Odebrat { $value }
citry-ui-toast-region = Oznámení
citry-ui-toast-dismiss = Zavřít { $title }
citry-ui-progress-value-text = { $label }: { $value } z { $max }
citry-ui-number-input-decrement = Snížit hodnotu
citry-ui-number-input-increment = Zvýšit hodnotu
citry-ui-number-input-required = Zadejte číslo.
citry-ui-number-input-invalid = Zadejte platné číslo.
citry-ui-number-input-minimum = Zadejte hodnotu alespoň { $min }.
citry-ui-number-input-maximum = Zadejte hodnotu nejvýše { $max }.
citry-ui-number-input-step = Zadejte hodnotu v krocích po { $step }.
citry-ui-range-slider-lower = Dolní hodnota
citry-ui-range-slider-upper = Horní hodnota
citry-ui-rating-value = { $value } z { $max }
""".lstrip(),
        "ar-EG": """
citry-ui-breadcrumbs-label = مسار التنقل
citry-ui-combobox-open = إظهار الخيارات
citry-ui-combobox-close = إخفاء الخيارات
citry-ui-pagination-label = ترقيم الصفحات
citry-ui-pagination-page = الصفحة { $page }
citry-ui-pagination-previous = الصفحة السابقة
citry-ui-pagination-next = الصفحة التالية
citry-ui-tags-input-remove = إزالة { $value }
citry-ui-toast-region = الإشعارات
citry-ui-toast-dismiss = إغلاق { $title }
citry-ui-progress-value-text = { $label }: { $value } من { $max }
citry-ui-number-input-decrement = خفض القيمة
citry-ui-number-input-increment = زيادة القيمة
citry-ui-number-input-required = أدخل رقمًا.
citry-ui-number-input-invalid = أدخل رقمًا صالحًا.
citry-ui-number-input-minimum = أدخل قيمة لا تقل عن { $min }.
citry-ui-number-input-maximum = أدخل قيمة لا تزيد عن { $max }.
citry-ui-number-input-step = أدخل قيمة بزيادات قدرها { $step }.
citry-ui-range-slider-lower = القيمة الدنيا
citry-ui-range-slider-upper = القيمة العليا
citry-ui-rating-value = { $value } من { $max }
""".lstrip(),
    }
    for locale, content in translations.items():
        locale_root = package / "locales" / locale
        locale_root.mkdir(parents=True)
        (locale_root / "citry-ui.ftl").write_text(content, encoding="utf8")
    return name


def _page(app: Citry) -> str:
    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en-US">
            <head><meta charset="utf-8" /></head>
            <body>
              <c-i18n tag="main" c-client="True">
                <section x-data="{
                  progressLabel: 'Processed', progressValue: 25, currentPage: 2,
                  tags: ['alpha'],
                  notices: [{id: 'saved', title: 'Saved', durationMs: 0}],
                }">
                <c-CBreadcrumbs c-items="breadcrumbs" c-attrs="{'id': 'breadcrumbs'}" />
                <c-CBreadcrumbs
                  c-items="breadcrumbs"
                  label="Custom breadcrumbs"
                  c-attrs="{'id': 'breadcrumbs-override'}"
                />
                <c-CProgress
                  label="Processed"
                  c-value="25"
                  c-attrs="{'id': 'progress'}"
                  $c-props="{label: progressLabel, value: progressValue}"
                />
                <c-CNumberInput
                  id="number-input"
                  name="amount"
                  value="1234.5"
                  step="0.1"
                  c-input_attrs="{'aria-label':'Measurement'}"
                />
                <c-CRangeSlider
                  id="range"
                  c-value="('1234.5', '5678.5')"
                  min="0"
                  max="10000"
                  step="0.5"
                  show_value="always"
                />
                <c-CRating id="rating-i18n" label="Article rating" value="3.5" precision="0.5" />
                <c-CPagination
                  c-pages="5"
                  c-page="2"
                  c-attrs="{'id': 'pagination'}"
                  $c-props="{page: currentPage}"
                />
                <c-CCombobox id="combobox" c-options="options" c-input_attrs="combo_input_attrs" />
                <c-CTagsInput
                  id="tags"
                  c-value="initial_tags"
                  c-input_attrs="tags_input_attrs"
                  $c-props="{value: tags}"
                />
                <c-CToastRegion
                  id="toasts"
                  c-items="initial_notices"
                  c-duration_ms="0"
                  $c-props="{items: notices}"
                />
                <button id="change-values" type="button" @click="
                  progressLabel = 'Reviewed';
                  progressValue = 50;
                  currentPage = 3;
                  tags = ['alpha', 'beta'];
                  notices = [
                    {id: 'saved', title: 'Updated', durationMs: 0},
                    {id: 'queued', title: 'Queued', durationMs: 0},
                  ];
                ">Change values</button>
                <button id="switch-cs" type="button" @click="$i18n.switchLocale('cs-CZ')">Čeština</button>
                <button id="switch-ar" type="button" @click="$i18n.switchLocale('ar-EG')">العربية</button>
                </section>
              </c-i18n>
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "breadcrumbs": (
                    citry_ui.CBreadcrumbItem("Home", "/"),
                    citry_ui.CBreadcrumbItem("Current"),
                ),
                "options": (
                    citry_ui.CComboboxOption("alpha", "Alpha"),
                    citry_ui.CComboboxOption("beta", "Beta"),
                ),
                "combo_input_attrs": {"aria-label": "Choice"},
                "initial_tags": ("alpha",),
                "tags_input_attrs": {"aria-label": "Tags"},
                "initial_notices": (citry_ui.CToastMessage(id="saved", title="Saved", duration_ms=0),),
            }

    i18n = app.extensions.get_extension("i18n")
    context = i18n.make_context(locale="en-US")
    return Page().render(provides={"citry_i18n": context}).serialize()


def _plain(value: str | None) -> str | None:
    return None if value is None else value.replace("\u2068", "").replace("\u2069", "")


def _label(page: Any, selector: str) -> str | None:
    return _plain(page.locator(selector).get_attribute("aria-label"))


def test_catalog_defaults_follow_values_locales_and_rtl_but_overrides_stay_fixed(
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
                "locales": ("en-US", "cs-CZ", "ar-EG"),
                "catalogs": (catalog,),
            }
        },
    )
    app.register_library(citry_ui)
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.goto(serve_citry_ui_live(app, _page(app)) + "/")
    page.wait_for_timeout(1_000)
    assert errors == []
    page.wait_for_function(
        """() => document.querySelector('#progress')?.hasAttribute('data-citry-progress-initialized')
          && document.querySelector('#pagination')?.hasAttribute('data-citry-pagination-initialized')
          && document.querySelector('#number-input')?.closest('[data-citry-ui-part=number-input]')
            ?.hasAttribute('data-citry-number-input-initialized')
          && document.querySelector('#range-root')?.hasAttribute('data-citry-slider-initialized')
          && document.querySelector('#rating-i18n-root')?.hasAttribute('data-citry-rating-initialized')
          && document.querySelector('#combobox-root')?.hasAttribute('data-citry-combobox-initialized')
          && document.querySelector('#tags')?.closest('[data-citry-ui-part=tags-input]')
            ?.hasAttribute('data-citry-tags-input-initialized')
          && document.querySelector('#toasts')?.hasAttribute('data-citry-toast-initialized')"""
    )

    assert page.locator("#breadcrumbs").get_attribute("aria-label") == "Breadcrumbs"
    assert page.locator("#breadcrumbs-override").get_attribute("aria-label") == "Custom breadcrumbs"
    assert _plain(page.locator("#progress").text_content()) == "Processed: 25 of 100"
    assert page.locator("#number-input").input_value() == "1,234.5"
    assert page.locator("#number-input-transport").input_value() == "1234.5"
    assert page.locator("#range-lower-label").text_content() == "Lower value"
    assert page.locator("#range-upper-label").text_content() == "Upper value"
    assert page.locator('#range-root [role="slider"]').nth(0).get_attribute("aria-valuetext") == "1,234.5"
    rating_label = '#rating-i18n-root [data-value="3.5"] [data-citry-ui-part="choice-label"]'
    assert _plain(page.locator(rating_label).text_content()) == "3.5 out of 5"
    assert _label(page, '#pagination [data-kind="page"][data-page="2"]') == "Page 2"
    assert page.locator("#combobox-root [data-citry-combobox-trigger]").get_attribute("aria-label") == "Show options"
    assert _label(page, '.cui-tags-input:has(#tags) [data-citry-ui-part="remove"]') == "Remove alpha"
    assert _label(page, '#toasts [data-citry-toast-id="saved"] [data-citry-toast-dismiss]') == "Dismiss Saved"

    page.locator("#change-values").click()
    page.wait_for_function(
        """() => document.querySelector('#progress')?.textContent.includes('50')
          && document.querySelector('#pagination [aria-current=page]')?.dataset.page === '3'
          && document.querySelectorAll('.cui-tags-input:has(#tags) [data-citry-ui-part=remove]').length === 2
          && document.querySelectorAll('#toasts [data-citry-toast-id]').length === 2"""
    )
    assert _plain(page.locator("#progress").text_content()) == "Reviewed: 50 of 100"
    assert _label(page, '#pagination [data-kind="page"][data-page="3"]') == "Page 3"
    assert _label(page, '.cui-tags-input:has(#tags) [data-value="beta"][data-citry-ui-part="remove"]') == (
        "Remove beta"
    )
    assert _label(page, '#toasts [data-citry-toast-id="saved"] [data-citry-toast-dismiss]') == "Dismiss Updated"
    assert _label(page, '#toasts [data-citry-toast-id="queued"] [data-citry-toast-dismiss]') == "Dismiss Queued"

    page.locator("#combobox-root [data-citry-combobox-trigger]").click()
    assert page.locator("#combobox-root [data-citry-combobox-trigger]").get_attribute("aria-label") == "Hide options"
    page.evaluate("async () => Alpine.evaluate(document.querySelector('#switch-cs'), '$i18n').switchLocale('cs-CZ')")
    page.wait_for_function("document.querySelector('main')?.lang === 'cs-CZ'")
    assert page.locator("#breadcrumbs").get_attribute("aria-label") == "Drobečková navigace"
    assert page.locator("#breadcrumbs-override").get_attribute("aria-label") == "Custom breadcrumbs"
    assert _plain(page.locator("#progress").text_content()) == "Reviewed: 50 z 100"
    assert page.locator("#number-input").input_value().replace("\u00a0", " ") == "1 234,5"
    assert _label(page, '.cui-number-input:has(#number-input) [data-citry-ui-part="increment"]') == (
        "Zvýšit hodnotu"
    )
    assert page.locator("#range-lower-label").text_content() == "Dolní hodnota"
    assert page.locator("#range-upper-label").text_content() == "Horní hodnota"
    assert page.locator('#range-root [role="slider"]').nth(0).get_attribute("aria-valuetext").replace(
        "\u00a0", " "
    ) == "1 234,5"
    assert _plain(page.locator(rating_label).text_content()) == "3,5 z 5"
    assert _label(page, '#pagination [data-kind="page"][data-page="3"]') == "Strana 3"
    assert page.locator("#combobox-root [data-citry-combobox-trigger]").get_attribute("aria-label") == "Skrýt možnosti"
    assert _label(page, '.cui-tags-input:has(#tags) [data-value="beta"][data-citry-ui-part="remove"]') == (
        "Odebrat beta"
    )
    assert _label(page, '#toasts [data-citry-toast-id="saved"] [data-citry-toast-dismiss]') == "Zavřít Updated"
    page.locator("#number-input").press("ArrowUp")
    assert page.locator("#number-input-transport").input_value() == "1234.6"

    page.evaluate("async () => Alpine.evaluate(document.querySelector('#switch-ar'), '$i18n').switchLocale('ar-EG')")
    page.wait_for_function("document.querySelector('main')?.lang === 'ar-EG'")
    assert page.locator("main").get_attribute("dir") == "rtl"
    assert page.locator("#breadcrumbs").get_attribute("aria-label") == "مسار التنقل"
    assert page.locator("#number-input").input_value() == "\u0661\u066c\u0662\u0663\u0664\u066b\u0666"
    assert _label(page, '.cui-number-input:has(#number-input) [data-citry-ui-part="decrement"]') == "خفض القيمة"
    assert page.locator("#range-lower-label").text_content() == "القيمة الدنيا"
    assert page.locator("#range-upper-label").text_content() == "القيمة العليا"
    assert page.locator('#range-root [role="slider"]').nth(0).get_attribute("aria-valuetext") == "١٬٢٣٤٫٥"  # noqa: RUF001
    assert _plain(page.locator(rating_label).text_content()) == "٣٫٥ من ٥"  # noqa: RUF001
    assert _label(page, '#pagination [data-kind="page"][data-page="3"]') == "الصفحة ٣"
    assert errors == []
