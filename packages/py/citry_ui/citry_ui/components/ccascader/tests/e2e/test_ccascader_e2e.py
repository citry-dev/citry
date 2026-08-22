"""Browser evidence for Cascader path selection, forms, keyboard, and cleanup."""

# ruff: noqa: E501 - embedded templates and browser expressions remain readable

from __future__ import annotations

import importlib
import importlib.resources
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry import citry as default_citry

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root for Cascader browser tests.")


_SNIPPETS = _root() / "packages/py/citry_ui/citry_ui/components/ccascader/snippets"
_PREVIEW_NAMES = tuple(sorted(path.stem for path in _SNIPPETS.glob("*.py") if path.stem != "__init__"))


class CascaderPreviewDocument(Component):
    citry = default_citry

    class Kwargs:
        title: str
        content: object

    class Slots:
        pass

    template = """
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>{{ title }}</title>
          <c-css />
        </head>
        <body>
          <main>{{ content }}</main>
          <c-js />
        </body>
      </html>
    """

    def template_data(self, kwargs: Kwargs, _slots: Slots) -> dict[str, object]:
        return {"title": kwargs.title, "content": kwargs.content}


def _preview_document(name: str) -> str:
    module = importlib.import_module(f"citry_ui.components.ccascader.snippets.{name}")
    return CascaderPreviewDocument(title=name.replace("_", " ").title(), content=module.preview).render().serialize()


def _open_preview(page: Any, serve_citry_ui_live: Any, name: str) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    base = serve_citry_ui_live(default_citry, _preview_document(name))
    page.goto(base + "/", wait_until="networkidle")
    page.wait_for_selector("[data-citry-cascader-initialized]")
    return errors


def _write_catalog(root: Path) -> str:
    name = "citry_ui_cascader_browser_i18n"
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
citry-ui-cascader-placeholder = Vyberte možnost
citry-ui-cascader-empty = Žádné možnosti
citry-ui-cascader-selected = Vybráno: { $path }
""".lstrip(),
        encoding="utf8",
    )
    return name


def _localized_page(app: Citry) -> str:
    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en-US"><head><meta charset="utf-8"><title>Localized Cascader</title><c-css /></head>
          <body>
            <c-i18n tag="main" c-client="True">
              <section x-data="{selection:[]}">
                <c-CCascader id="localized-place" aria_label="Destination" $c-props="{value:selection,onValueChange:value=>selection=value}">
                  <c-CCascaderOption value="world" label="World">
                    <c-CCascaderOption value="europe" label="Europe"><c-CCascaderOption value="prague" label="Prague" /></c-CCascaderOption>
                  </c-CCascaderOption>
                </c-CCascader>
                <button id="clear-place" type="button" @click="selection=[]">Clear</button>
                <button id="switch-cs" type="button" @click="$i18n.switchLocale('cs-CZ')">Čeština</button>
                <button id="switch-en" type="button" @click="$i18n.switchLocale('en-US')">English</button>
              </section>
            </c-i18n>
            <c-js />
          </body></html>
        """

    context = app.extensions.get_extension("i18n").make_context(locale="en-US")
    return Page().render(provides={"citry_i18n": context}).serialize()


def _server_only_localized_page(app: Citry) -> str:
    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="cs-CZ"><head><meta charset="utf-8"><title>Server-only Cascader</title><c-css /></head>
          <body>
            <c-CCascader id="server-only-place" aria_label="Cíl">
              <c-CCascaderOption value="world" label="Svět"><c-CCascaderOption value="prague" label="Praha" /></c-CCascaderOption>
            </c-CCascader>
            <c-js />
          </body></html>
        """

    context = app.extensions.get_extension("i18n").make_context(locale="cs-CZ")
    return Page().render(provides={"citry_i18n": context}).serialize()


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8"><title>Cascader evidence</title><c-css /></head>
          <body x-data>
            <form id="form"><label id="place-label">Destination</label><c-CCascader id="place" aria_labelledby="place-label" name="place" c-value="['world','europe','prague']"
              $c-props="{onValueChange:(value,detail)=>$store.cascade.changes.push([value,detail.source]),onOpenChange:(open)=>$store.cascade.opens.push(open)}">
              <c-CCascaderOption value="world" label="World">
                <c-CCascaderOption value="europe" label="Europe"><c-CCascaderOption value="prague" label="Prague" /><c-CCascaderOption value="berlin" label="Berlin" /></c-CCascaderOption>
                <c-CCascaderOption value="asia" label="Asia"><c-CCascaderOption value="tokyo" label="Tokyo" /></c-CCascaderOption>
              </c-CCascaderOption>
              <c-CCascaderOption value="offline" label="Offline" c-disabled="True" />
            </c-CCascader></form>
            <c-CCascader id="empty-place" aria_label="Empty destination" />
            <button id="after-empty" type="button">After empty Cascader</button>
            <c-CCascader id="controlled-place" aria_label="Controlled destination" c-value="['world','europe','prague']"
              $c-props="{open:$store.cascade.controlledOpen,value:$store.cascade.controlledValue,onOpenChange:open=>setTimeout(()=>$store.cascade.controlledOpen=open,40),onValueChange:value=>setTimeout(()=>$store.cascade.controlledValue=value,40)}">
              <c-CCascaderOption value="world" label="World">
                <c-CCascaderOption value="europe" label="Europe"><c-CCascaderOption value="prague" label="Prague" /></c-CCascaderOption>
                <c-CCascaderOption value="asia" label="Asia"><c-CCascaderOption value="tokyo" label="Tokyo" /></c-CCascaderOption>
              </c-CCascaderOption>
            </c-CCascader>
          </body></html>
        """
        js = "Alpine.store('cascade',{changes:[],opens:[],controlledOpen:false,controlledValue:['world','europe','prague']});"

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#place[data-citry-cascader-initialized]")
    page.wait_for_selector("#empty-place[data-citry-cascader-initialized]")
    page.wait_for_selector("#controlled-place[data-citry-cascader-initialized]")
    return errors


def test_pointer_path_updates_display_inputs_and_callbacks(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#place")
    assert root.locator('[data-citry-ui-part="popup"]').is_hidden()
    root.locator('[data-citry-ui-part="trigger"]').click()
    root.locator('[role="treeitem"][data-value="asia"]').click()
    root.locator('[role="treeitem"][data-value="tokyo"]').click()
    assert root.locator('[data-citry-ui-part="value"]').inner_text() == "World / Asia / Tokyo"
    assert root.locator('input[name="place"]').evaluate_all("els=>els.map(el=>el.value)") == ["world", "asia", "tokyo"]
    assert page.evaluate("Alpine.store('cascade').changes") == [[["world", "asia", "tokyo"], "pointer"]]
    assert page.evaluate("Alpine.store('cascade').opens") == [True, False]
    assert errors == []


def test_shipped_geographic_path_toggles_popup_and_each_active_branch(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "at_a_glance")
    root = page.locator('[data-citry-ui-part="cascader"]')
    trigger = root.locator('[data-citry-ui-part="trigger"]')
    popup = root.locator('[data-citry-ui-part="popup"]')
    europe = root.get_by_role("treeitem", name="Europe")
    czechia = root.get_by_role("treeitem", name="Czechia")
    germany = root.get_by_role("treeitem", name="Germany")
    prague = root.get_by_role("treeitem", name="Prague")
    berlin = root.get_by_role("treeitem", name="Berlin")

    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "true"
    assert europe.get_attribute("aria-expanded") == "true"
    assert czechia.get_attribute("aria-expanded") == "true"

    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "false"
    assert popup.is_hidden()
    assert popup.bounding_box() is None
    trigger.click()

    europe.click()
    assert europe.get_attribute("aria-expanded") == "false"
    assert czechia.is_hidden()
    assert germany.is_hidden()
    europe.click()
    assert europe.get_attribute("aria-expanded") == "true"
    assert czechia.is_visible()
    assert germany.is_visible()

    czechia.click()
    assert czechia.get_attribute("aria-expanded") == "true"
    assert prague.is_visible()
    czechia.click()
    assert czechia.get_attribute("aria-expanded") == "false"
    assert prague.is_hidden()

    germany.click()
    assert germany.get_attribute("aria-expanded") == "true"
    assert czechia.get_attribute("aria-expanded") == "false"
    assert berlin.is_visible()
    assert prague.is_hidden()
    germany.click()
    assert germany.get_attribute("aria-expanded") == "false"
    assert berlin.is_hidden()

    assert root.locator('[data-citry-ui-part="value"]').inner_text() == "Europe / Czechia / Prague"
    assert errors == []


def test_keyboard_environment_axe_and_cleanup(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#place")
    trigger = root.locator('[data-citry-ui-part="trigger"]')
    assert trigger.get_attribute("aria-labelledby") == "place-label"
    assert trigger.get_by_text("World / Europe / Prague").is_visible()
    trigger.focus()
    trigger.press("Enter")
    page.wait_for_function("document.activeElement?.dataset?.value === 'prague'")
    page.keyboard.press("ArrowLeft")
    page.wait_for_function("document.activeElement?.dataset?.value === 'europe'")
    assert root.get_by_role("treeitem", name="Europe").get_attribute("aria-expanded") == "false"
    page.keyboard.press("ArrowDown")
    page.wait_for_function("document.activeElement?.dataset?.value === 'asia'")
    page.keyboard.press("ArrowRight")
    page.wait_for_function("document.activeElement?.dataset?.value === 'tokyo'")
    page.keyboard.press("End")
    page.keyboard.press("Enter")
    assert page.evaluate("Alpine.store('cascade').changes.at(-1)[1]") == "keyboard"
    page.emulate_media(forced_colors="active", reduced_motion="reduce")
    page.add_script_tag(path=str(_root() / "node_modules" / "axe-core" / "axe.min.js"))
    violations = page.evaluate(
        """async()=> (await axe.run(document,{resultTypes:['violations']})).violations.filter(x=>['serious','critical'].includes(x.impact)).map(x=>x.id)"""
    )
    assert violations == []
    root.evaluate("element=>element.remove()")
    page.wait_for_timeout(30)
    assert errors == []


def test_empty_popup_escape_and_tab_close_from_the_trigger(page: Any) -> None:
    errors = _load(page)
    trigger = page.locator('#empty-place [data-citry-ui-part="trigger"]')
    trigger.focus()
    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "true"
    trigger.press("Escape")
    assert trigger.get_attribute("aria-expanded") == "false"
    assert page.evaluate("document.activeElement?.id") == trigger.get_attribute("id")

    trigger.click()
    trigger.press("Tab")
    assert trigger.get_attribute("aria-expanded") == "false"
    assert page.evaluate("document.activeElement?.id") != trigger.get_attribute("id")
    assert errors == []


def test_delayed_controlled_open_focuses_and_controlled_acceptance_announces(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#controlled-place")
    trigger = root.locator('[data-citry-ui-part="trigger"]')
    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "false"
    page.wait_for_function(
        "document.querySelector('#controlled-place [data-citry-ui-part=trigger]').getAttribute('aria-expanded') === 'true'"
    )
    page.wait_for_function("document.activeElement?.dataset?.value === 'prague'")

    trigger.click()
    assert page.evaluate("document.activeElement?.dataset?.citryUiPart") == "trigger"
    page.wait_for_function(
        "document.querySelector('#controlled-place [data-citry-ui-part=trigger]').getAttribute('aria-expanded') === 'false'"
    )
    assert page.evaluate("document.activeElement?.dataset?.citryUiPart") == "trigger"
    trigger.click()
    page.wait_for_function(
        "document.querySelector('#controlled-place [data-citry-ui-part=trigger]').getAttribute('aria-expanded') === 'true'"
    )

    root.get_by_role("treeitem", name="Asia").click()
    root.get_by_role("treeitem", name="Tokyo").click()
    assert root.locator('[data-citry-ui-part="value"]').inner_text() == "World / Europe / Prague"
    page.wait_for_function(
        "document.querySelector('#controlled-place [data-citry-ui-part=value]').textContent === 'World / Asia / Tokyo'"
    )
    announcement = (
        root.locator('[data-citry-ui-part="status"]').inner_text().replace("\u2068", "").replace("\u2069", "")
    )
    assert announcement == "Selected World / Asia / Tokyo"
    assert errors == []


def test_invalid_controlled_props_retain_the_last_valid_state_until_control_is_omitted(
    page: Any,
) -> None:
    errors = _load(page)
    root = page.locator("#controlled-place")
    page.evaluate(
        """() => {
          Alpine.store('cascade').controlledValue=['world','asia','tokyo'];
          Alpine.store('cascade').controlledOpen=true;
        }"""
    )
    page.wait_for_function(
        "document.querySelector('#controlled-place [data-citry-ui-part=value]').textContent === 'World / Asia / Tokyo'"
    )
    page.wait_for_function(
        "document.querySelector('#controlled-place [data-citry-ui-part=trigger]').getAttribute('aria-expanded') === 'true'"
    )
    announcement = root.locator('[data-citry-ui-part="status"]').inner_text()

    page.evaluate(
        """() => {
          Alpine.store('cascade').controlledValue=['world','missing'];
          Alpine.store('cascade').controlledOpen='yes';
        }"""
    )
    page.wait_for_timeout(50)
    assert root.locator('[data-citry-ui-part="value"]').inner_text() == "World / Asia / Tokyo"
    assert root.locator('[data-citry-ui-part="trigger"]').get_attribute("aria-expanded") == "true"
    assert root.locator('[data-value="asia"]').get_attribute("aria-expanded") == "true"
    assert root.get_by_role("treeitem", name="Tokyo").is_visible()
    assert root.locator('[data-citry-ui-part="status"]').inner_text() == announcement

    page.evaluate(
        """() => {
          Alpine.store('cascade').controlledValue=undefined;
          Alpine.store('cascade').controlledOpen=undefined;
        }"""
    )
    page.wait_for_function(
        "document.querySelector('#controlled-place [data-citry-ui-part=value]').textContent === 'World / Europe / Prague'"
    )
    assert root.locator('[data-citry-ui-part="trigger"]').get_attribute("aria-expanded") == "true"
    assert root.locator('[data-value="europe"]').get_attribute("aria-expanded") == "true"
    assert root.locator('[data-value="asia"]').get_attribute("aria-expanded") == "false"
    assert root.get_by_role("treeitem", name="Prague").is_visible()
    root.locator('[data-citry-ui-part="trigger"]').click()
    assert root.locator('[data-citry-ui-part="trigger"]').get_attribute("aria-expanded") == "false"
    assert root.locator('[data-citry-ui-part="popup"]').is_hidden()
    assert len(errors) == 2
    assert any("CCascader value received invalid client value" in error for error in errors)
    assert any("CCascader open received invalid client value" in error for error in errors)


def test_normal_flow_popup_is_clamped_without_document_overflow_in_ltr_and_rtl(page: Any) -> None:
    page.set_viewport_size({"width": 900, "height": 700})
    errors = _load(page)
    root = page.locator("#place")
    trigger = root.locator('[data-citry-ui-part="trigger"]')
    popup = root.locator('[data-citry-ui-part="popup"]')
    root.evaluate(
        "element => { element.style.display='grid'; element.style.marginLeft='auto'; element.style.marginRight='0'; }"
    )
    trigger.click()
    page.wait_for_timeout(0)
    ltr = popup.bounding_box()
    assert ltr is not None
    assert ltr["x"] >= 7
    assert ltr["x"] + ltr["width"] <= 893
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth") is True

    trigger.click()
    page.evaluate("document.documentElement.dir='rtl'")
    root.evaluate("element => { element.style.marginLeft='0'; element.style.marginRight='auto'; }")
    trigger.click()
    page.wait_for_timeout(0)
    rtl = popup.bounding_box()
    assert rtl is not None
    assert rtl["x"] >= 7
    assert rtl["x"] + rtl["width"] <= 893
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth") is True
    rtl_lefts = popup.locator(":scope > [data-citry-cascader-column]:not([hidden])").evaluate_all(
        "columns => columns.map(column => Math.round(column.getBoundingClientRect().left))"
    )
    assert rtl_lefts == sorted(rtl_lefts, reverse=True)
    indicator_scale = root.locator('[data-citry-ui-part="option-indicator"]').first.evaluate(
        "element => new DOMMatrix(getComputedStyle(element).transform).a"
    )
    assert indicator_scale == pytest.approx(-1)
    assert errors == []


def test_desktop_columns_are_siblings_without_nested_horizontal_scroll_or_reserved_height(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#place")
    root.locator('[data-citry-ui-part="trigger"]').click()
    geometry = root.locator('[data-citry-ui-part="popup"]').evaluate(
        """popup => {
          const columns = [...popup.querySelectorAll('[data-citry-cascader-column]')]
            .filter(column => !column.hidden);
          return {
            popupHeight: popup.getBoundingClientRect().height,
            columns: columns.map(column => {
              const box = column.getBoundingClientRect();
              return {
                left: box.left, right: box.right, top: box.top,
                scrollLeft: column.scrollLeft,
                scrollWidth: column.scrollWidth,
                clientWidth: column.clientWidth,
                itemsFit: [...column.children].every(item => {
                  const itemBox = item.getBoundingClientRect();
                  return itemBox.left >= box.left - 1 && itemBox.right <= box.right + 1;
                }),
              };
            }),
          };
        }"""
    )
    assert len(geometry["columns"]) == 3
    assert [column["left"] for column in geometry["columns"]] == sorted(
        column["left"] for column in geometry["columns"]
    )
    assert len({round(column["left"]) for column in geometry["columns"]}) == 3
    assert all(column["scrollLeft"] == 0 for column in geometry["columns"])
    assert all(column["scrollWidth"] <= column["clientWidth"] + 1 for column in geometry["columns"])
    assert all(column["itemsFit"] for column in geometry["columns"])
    assert geometry["popupHeight"] < 140
    assert root.get_by_role("treeitem", name="Europe").get_attribute("aria-owns")
    assert errors == []


def test_narrow_columns_stack_at_trigger_width_without_inline_scroll(page: Any) -> None:
    page.set_viewport_size({"width": 390, "height": 700})
    errors = _load(page)
    root = page.locator("#place")
    root.locator('[data-citry-ui-part="trigger"]').click()
    geometry = root.locator('[data-citry-ui-part="popup"]').evaluate(
        """popup => {
          const columns = [...popup.querySelectorAll('[data-citry-cascader-column]')]
            .filter(column => !column.hidden);
          const popupBox = popup.getBoundingClientRect();
          const triggerBox = popup.parentElement.querySelector('[data-citry-ui-part=trigger]').getBoundingClientRect();
          return {
            documentFits: document.documentElement.scrollWidth === document.documentElement.clientWidth,
            documentScrollWidth: document.documentElement.scrollWidth,
            documentClientWidth: document.documentElement.clientWidth,
            popupWidth: popupBox.width,
            triggerWidth: triggerBox.width,
            popupScrollWidth: popup.scrollWidth,
            popupClientWidth: popup.clientWidth,
            columns: columns.map(column => {
              const box = column.getBoundingClientRect();
              return {left:box.left,top:box.top,width:box.width,scrollWidth:column.scrollWidth,clientWidth:column.clientWidth};
            }),
          };
        }"""
    )
    assert len(geometry["columns"]) == 3
    assert root.locator('[data-citry-ui-part="popup"]').get_attribute("data-citry-cascader-stacked") == ""
    assert len({round(column["left"]) for column in geometry["columns"]}) == 1
    assert [column["top"] for column in geometry["columns"]] == sorted(column["top"] for column in geometry["columns"])
    assert len({round(column["top"]) for column in geometry["columns"]}) == 3
    assert geometry["popupWidth"] == pytest.approx(geometry["triggerWidth"], abs=1)
    assert geometry["popupScrollWidth"] <= geometry["popupClientWidth"] + 1
    assert all(column["scrollWidth"] <= column["clientWidth"] + 1 for column in geometry["columns"])
    assert geometry["documentFits"] is True, geometry
    root.locator('[data-citry-ui-part="trigger"]').click()
    assert root.locator('[data-citry-ui-part="popup"]').is_hidden()
    assert root.locator('[data-citry-ui-part="popup"]').bounding_box() is None
    assert errors == []


@pytest.mark.parametrize("preview_name", _PREVIEW_NAMES)
def test_shipped_previews_initialize_without_high_impact_axe_findings(
    page: Any,
    serve_citry_ui_live: Any,
    preview_name: str,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, preview_name)
    page.locator('[data-citry-ui-part="trigger"]').click()
    page.wait_for_timeout(50)
    page.add_script_tag(path=str(_root() / "node_modules" / "axe-core" / "axe.min.js"))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert errors == []


@pytest.mark.parametrize("preview_name", ["at_a_glance", "forms"])
def test_compact_shipped_paths_use_side_by_side_columns_when_they_fit(
    page: Any,
    serve_citry_ui_live: Any,
    preview_name: str,
) -> None:
    page.set_viewport_size({"width": 620, "height": 700})
    errors = _open_preview(page, serve_citry_ui_live, preview_name)
    root = page.locator('[data-citry-ui-part="cascader"]')
    root.locator('[data-citry-ui-part="trigger"]').click()
    popup = root.locator('[data-citry-ui-part="popup"]')
    popup_widths = popup.evaluate(
        "element => ({scrollWidth:element.scrollWidth,clientWidth:element.clientWidth,width:element.getBoundingClientRect().width,viewport:document.documentElement.clientWidth,stacked:element.hasAttribute('data-citry-cascader-stacked')})"
    )
    assert popup_widths["scrollWidth"] <= popup_widths["clientWidth"] + 1, popup_widths
    columns = popup.locator(":scope > [data-citry-cascader-column]:not([hidden])")
    assert columns.count() == 3
    lefts = columns.evaluate_all("columns => columns.map(column => Math.round(column.getBoundingClientRect().left))")
    assert len(set(lefts)) == 3
    assert popup.get_attribute("data-citry-cascader-stacked") is None
    for label in (
        ("Europe", "Czechia", "Prague") if preview_name == "at_a_glance" else ("Hardware", "Cameras", "Mirrorless")
    ):
        option = root.get_by_role("treeitem", name=label)
        assert option.is_visible()
        assert (
            option.evaluate(
                "element => { const column=element.closest('[data-citry-cascader-column]'); const a=element.getBoundingClientRect(); const b=column.getBoundingClientRect(); return a.left >= b.left - 1 && a.right <= b.right + 1; }"
            )
            is True
        )
    assert errors == []


def test_custom_wide_columns_demonstrate_fit_triggered_stacking(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    page.set_viewport_size({"width": 620, "height": 700})
    errors = _open_preview(page, serve_citry_ui_live, "accessibility")
    root = page.locator('[data-citry-ui-part="cascader"]')
    root.locator('[data-citry-ui-part="trigger"]').click()
    popup = root.locator('[data-citry-ui-part="popup"]')
    columns = popup.locator(":scope > [data-citry-cascader-column]:not([hidden])")
    assert columns.count() == 3
    geometry = columns.evaluate_all(
        "columns => columns.map(column => { const box=column.getBoundingClientRect(); return {left:Math.round(box.left),top:Math.round(box.top)}; })"
    )
    assert len({column["left"] for column in geometry}) == 1
    assert len({column["top"] for column in geometry}) == 3
    assert popup.get_attribute("data-citry-cascader-stacked") == ""
    assert errors == []


def test_locale_switch_updates_only_an_empty_placeholder_and_never_overwrites_a_selected_path(
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
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    base = serve_citry_ui_live(app, _localized_page(app))
    page.goto(base + "/", wait_until="networkidle")
    root = page.locator("#localized-place")
    page.wait_for_selector("#localized-place[data-citry-cascader-initialized]")
    value = root.locator('[data-citry-ui-part="value"]')
    assert value.inner_text() == "Choose an option"

    root.locator('[data-citry-ui-part="trigger"]').click()
    root.get_by_role("treeitem", name="World").click()
    root.get_by_role("treeitem", name="Europe").click()
    root.get_by_role("treeitem", name="Prague").click()
    assert value.inner_text() == "World / Europe / Prague"

    page.evaluate("async () => Alpine.evaluate(document.querySelector('#switch-cs'), '$i18n').switchLocale('cs-CZ')")
    page.wait_for_function("document.querySelector('main')?.lang === 'cs-CZ'")
    assert value.inner_text() == "World / Europe / Prague"

    page.locator("#clear-place").click()
    page.wait_for_function(
        "document.querySelector('#localized-place [data-citry-ui-part=value]').textContent === 'Vyberte možnost'"
    )
    page.evaluate("async () => Alpine.evaluate(document.querySelector('#switch-en'), '$i18n').switchLocale('en-US')")
    page.wait_for_function(
        "document.querySelector('#localized-place [data-citry-ui-part=value]').textContent === 'Choose an option'"
    )
    assert errors == []


def test_server_only_non_english_context_keeps_localized_selection_announcements(
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
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    base = serve_citry_ui_live(app, _server_only_localized_page(app))
    page.goto(base + "/", wait_until="networkidle")
    root = page.locator("#server-only-place")
    page.wait_for_selector("#server-only-place[data-citry-cascader-initialized]")
    root.locator('[data-citry-ui-part="trigger"]').click()
    root.get_by_role("treeitem", name="Svět").click()
    root.get_by_role("treeitem", name="Praha").click()
    announcement = (
        root.locator('[data-citry-ui-part="status"]').inner_text().replace("\u2068", "").replace("\u2069", "")
    )
    assert announcement == "Vybráno: Svět / Praha"
    assert errors == []
