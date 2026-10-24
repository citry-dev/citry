"""Citry UI component sources, catalog packaging, and runtime tests."""

from __future__ import annotations

import ast
import importlib.resources
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from citry_ui_i18n._generate_catalog import render_component_catalog

import citry_ui
from citry import Citry, Component
from citry_ui import CBreadcrumbItem


def _configured_app(*, mode: str = "development") -> Citry:
    app = Citry(
        mode=mode,
        autodiscover=False,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
                "catalogs": ("citry_ui_i18n",),
            }
        },
    )
    app.register_library(citry_ui)
    return app


def test_catalog_resource_package_import_is_side_effect_free() -> None:
    script = """
import sys
assert "citry_ui" not in sys.modules
import citry_ui_i18n
assert "citry_ui" not in sys.modules
assert citry_ui_i18n.__all__ == ()
"""
    subprocess.run([sys.executable, "-c", script], check=True)


def _catalog_outputs() -> dict[str, dict[str, object]]:
    app = _configured_app()
    extension = app.extensions.get_extension("i18n")
    extension._load_project_sources()
    artifact = json.loads(extension._compiled_catalog.artifact_json())
    return {key: value for key, value in artifact["manifest"]["en-US"].items() if "." not in key}


def test_component_messages_generate_the_source_catalog() -> None:
    root = importlib.resources.files("citry_ui_i18n")
    component_catalog = root.joinpath("locales", "en-US", "citry-ui.ftl").read_text(encoding="utf-8")

    assert component_catalog == render_component_catalog(citry_ui.COMPONENTS)
    assert len(_catalog_outputs()) == 152


def test_component_source_messages_are_the_final_class_member() -> None:
    component_root = Path(__file__).parents[1] / "citry_ui" / "components"

    for path in sorted(component_root.glob("c*/*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            source_declarations = [
                statement
                for statement in class_node.body
                if (
                    isinstance(statement, ast.Assign)
                    and any(
                        isinstance(target, ast.Name) and target.id in {"messages", "messages_file"}
                        for target in statement.targets
                    )
                )
                or (
                    isinstance(statement, ast.AnnAssign)
                    and isinstance(statement.target, ast.Name)
                    and statement.target.id in {"messages", "messages_file"}
                )
            ]
            if not source_declarations:
                continue

            assert len(source_declarations) == 1, f"{path}:{class_node.lineno} declares source messages more than once"
            assert class_node.body[-1] is source_declarations[0], (
                f"{path}:{source_declarations[0].lineno} must be the final member of {class_node.name}"
            )
            declaration = source_declarations[0]
            names = (
                [target.id for target in declaration.targets if isinstance(target, ast.Name)]
                if isinstance(declaration, ast.Assign)
                else [declaration.target.id]
                if isinstance(declaration.target, ast.Name)
                else []
            )
            if "messages" in names:
                assert declaration.end_lineno is not None
                assert declaration.end_lineno > declaration.lineno, (
                    f"{path}:{declaration.lineno} must declare {class_node.name}.messages as a multiline block"
                )


def test_every_message_owner_declares_english_source_locale() -> None:
    owners = [component for component in citry_ui.COMPONENTS if component.__dict__.get("messages") is not None]
    assert owners
    assert all(component.I18n.messages_locale == "en-US" for component in owners)


def test_every_catalog_message_has_one_structured_component_api_entry() -> None:
    component_root = Path(__file__).parents[1] / "citry_ui" / "components"
    documented = [
        entry["key"]
        for path in sorted(component_root.glob("c*/api.yml"))
        for table in yaml.safe_load(path.read_text(encoding="utf-8"))["translations"]
        for entry in table["entries"]
    ]

    assert len(documented) == len(set(documented))
    assert set(documented) == set(_catalog_outputs())


def test_every_catalog_message_resolves_through_the_configured_package() -> None:
    app = _configured_app()
    extension = app.extensions.get_extension("i18n")
    sample_values = {
        "action_label": "Undo",
        "date": "August 19, 2026",
        "label": "Upload",
        "item": "Design review",
        "max": "8",
        "min": "1",
        "page": "3",
        "path": "World / Europe / Prague",
        "position": "2",
        "row": "Design review",
        "start": "August 19, 2026",
        "step": "0.5",
        "end": "August 24, 2026",
        "time": "9:30 AM",
        "title": "Saved",
        "value": "alpha",
        "current": 1,
        "total": 2,
        "selected": 1,
        "count": 2,
        "column": "Name",
        "color": "#7f56d9",
    }

    for message_id, entry in _catalog_outputs().items():
        values = {
            name: str(sample_values[name]) if contract["type_name"] == "str" else sample_values[name]
            for name, contract in entry["interface"].items()
        }
        assert extension.tr(message_id, **values)


def test_zero_configuration_citry_ui_uses_component_source_messages() -> None:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    items = (CBreadcrumbItem("Home", "/"), CBreadcrumbItem("Current"))

    class Page(Component):
        citry = app
        template = '<c-CBreadcrumbs c-items="items" />'

        def template_data(self, kwargs, slots):
            return {"items": items}

    extension = app.extensions.get_extension("i18n")
    html = str(Page())
    assert extension.configured is False
    assert extension.available is True
    assert extension.context.locale == "en-US"
    assert 'aria-label="Breadcrumbs"' in html
    assert "data-citry-i18n-binding" not in html


def test_configured_catalog_renders_defaults_but_preserves_explicit_component_text() -> None:
    app = _configured_app()
    items = (CBreadcrumbItem("Home", "/"), CBreadcrumbItem("Current"))

    class Page(Component):
        citry = app
        template = """
          <c-CBreadcrumbs c-items="items" />
          <c-CBreadcrumbs c-items="items" label="Page location" />
        """

        def template_data(self, kwargs, slots):
            return {"items": items}

    html = str(Page())
    assert html.count('aria-label="Breadcrumbs"') == 1
    assert html.count('aria-label="Page location"') == 1


def test_client_provider_emits_only_the_default_catalog_binding() -> None:
    app = _configured_app()
    items = (CBreadcrumbItem("Home", "/"), CBreadcrumbItem("Current"))

    class Page(Component):
        citry = app
        template = """
          <c-i18n tag="section" c-client="True">
            <c-CBreadcrumbs c-items="items" />
            <c-CBreadcrumbs c-items="items" label="Page location" />
          </c-i18n>
        """

        def template_data(self, kwargs, slots):
            return {"items": items}

    html = str(Page())
    match = re.search(
        r'<script type="application/json" data-citry-vue-document="[^"]*"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    manifest = json.loads(match.group(1))["manifest"]
    bindings = [
        attrs["data-citry-i18n-binding"]
        for occurrence in manifest["occurrences"]
        for key, attrs in occurrence["preparedData"].items()
        if key.startswith("citryAttrs") and "data-citry-i18n-binding" in attrs
    ]
    assert len(bindings) == 1
    payload = manifest["extensions"]["i18n"]["payload"]
    assert any(
        binding["message"] == "citry-ui-breadcrumbs-label"
        for requirement in payload["requirements"]
        for binding in requirement["bindings"]
    )
    assert "$c-tr" not in html


def test_package_format_profiles_load_from_source_and_compiled_artifacts() -> None:
    for mode in ("development", "production"):
        app = _configured_app(mode=mode)
        extension = app.extensions.get_extension("i18n")
        formatter = extension.for_context(extension.make_context(locale="en-US")).format

        assert formatter.number(Decimal("1234.5"), format="citry-ui-number-input") == "1,234.5"
        assert formatter.number(Decimal("1234.5"), format="citry-ui-pagination-page") == "1,234.5"
        assert formatter.number(Decimal("1234.5"), format="citry-ui-slider") == "1,234.5"
        assert formatter.number(Decimal("3.5"), format="citry-ui-rating") == "3.5"
        assert formatter.number(Decimal(8), format="citry-ui-tags-input-maximum") == "8"


def _null_form_render(markup: str) -> tuple[str, dict[str, str | None], dict[str, bool]]:
    """Render under a client provider; return the HTML, each binding's values expression, and the catalog flags."""
    app = _configured_app()

    class Page(Component):
        citry = app
        template = f'<c-i18n tag="section" c-client="True">{markup}</c-i18n>'

    html = str(Page())
    match = re.search(
        r'<script type="application/json" data-citry-vue-document="[^"]*"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    manifest = json.loads(match.group(1))["manifest"]
    expressions = {
        binding["message"]: binding.get("values_expression")
        for requirement in manifest["extensions"]["i18n"]["payload"]["requirements"]
        for binding in requirement["bindings"]
    }
    # The js_data flags each `$c-tr` expression reads to choose between
    # translating and keeping the caller's own label.
    flags = {
        key: value
        for occurrence in manifest["occurrences"]
        for key, value in occurrence["serverData"].items()
        if key.startswith("catalog") and type(value) is bool
    }
    return html, expressions, flags


def _assert_null_form(default: str, override: str, message: str, flag: str, caller_text: str) -> None:
    _html, expressions, flags = _null_form_render(default)
    assert expressions[message] == f"{flag} ? {{}} : null"
    assert flags[flag] is True
    html, expressions, flags = _null_form_render(override)
    # The binding stays, but its flag is false, so the browser keeps the caller's text.
    assert expressions[message] == f"{flag} ? {{}} : null"
    assert flags[flag] is False
    assert caller_text in html


def test_null_form_infinite_scroll_keeps_a_caller_label() -> None:
    _assert_null_form(
        "<c-CInfiniteScroll />",
        '<c-CInfiniteScroll loading_label="Fetching rows" />',
        "citry-ui-infinite-scroll-loading",
        "catalogLoading",
        ">Fetching rows</span>",
    )


def test_null_form_number_input_keeps_a_caller_label() -> None:
    _assert_null_form(
        "<c-CNumberInput />",
        '<c-CNumberInput increment_label="Add one" />',
        "citry-ui-number-input-increment",
        "catalogIncrementLabel",
        'aria-label="Add one"',
    )


def test_null_form_sidebar_keeps_a_caller_label() -> None:
    _assert_null_form(
        '<c-CSidebar label="Site">x</c-CSidebar>',
        '<c-CSidebar label="Site" expand_label="Open menu">x</c-CSidebar>',
        "citry-ui-sidebar-expand",
        "catalogExpandLabel",
        ">Open menu</span>",
    )


def test_null_form_tag_keeps_a_caller_label() -> None:
    _assert_null_form(
        '<c-CTagGroup label="Tags" removable><c-CTag value="a">A</c-CTag></c-CTagGroup>',
        '<c-CTagGroup label="Tags" removable remove_label="Drop"><c-CTag value="a">A</c-CTag></c-CTagGroup>',
        "citry-ui-tag-remove",
        "catalogRemoveLabel",
        ">Drop</span>",
    )


def test_null_form_time_picker_keeps_a_caller_label() -> None:
    _assert_null_form(
        "<c-CTimePicker />",
        '<c-CTimePicker clear_label="Wipe time" />',
        "citry-ui-time-picker-clear",
        "catalogClearLabel",
        'aria-label="Wipe time"',
    )


def test_null_form_range_slider_keeps_a_caller_label() -> None:
    _assert_null_form(
        "<c-CRangeSlider />",
        '<c-CRangeSlider lower_label="Minimum price" />',
        "citry-ui-range-slider-lower",
        "catalogLowerLabel",
        ">Minimum price</span>",
    )


def _null_form_manifest(template: str, kwargs: dict[str, object]) -> tuple[str, dict[str, object]]:
    app = _configured_app()

    class Page(Component):
        citry = app

        def template_data(self, _kwargs, slots):
            return {"kw": kwargs}

    Page.template = f'<c-i18n tag="section" c-client="True">{template}</c-i18n>'
    html = str(Page())
    match = re.search(
        r'<script type="application/json" data-citry-vue-document="[^"]*"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    return html, json.loads(match.group(1))["manifest"]


def _null_form_flag(manifest: dict[str, object], path: str) -> object:
    # The flag lives in the browser data of the occurrence that owns it.
    for occurrence in manifest["occurrences"]:
        value: object = occurrence["serverData"]
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                break
            value = value[part]
        else:
            return value
    raise AssertionError(f"no occurrence sends {path!r}")


@pytest.mark.parametrize(
    ("template", "base", "message", "flag", "override"),
    [
        (
            '<c-CCalendar c-bind="kw" />',
            {},
            "citry-ui-calendar-previous-month",
            "catalogPreviousLabel",
            {"previous_label": "Mine"},
        ),
        (
            '<c-CColorPicker label="Brand color" c-bind="kw" />',
            {},
            "citry-ui-color-picker-hue",
            "serverDefaults.catalog.hue",
            {"hue_label": "Mine"},
        ),
        (
            '<c-CCommandPalette label="Commands" c-bind="kw" />',
            {"entries": (citry_ui.CCommandPaletteCommand(value="open", label="Open"),)},
            "citry-ui-command-palette-close",
            "catalogCloseLabel",
            {"close_label": "Mine"},
        ),
        (
            '<c-CDatePicker name="arrival" c-bind="kw" />',
            {},
            "citry-ui-date-picker-clear",
            "catalog.clear_label",
            {"clear_label": "Mine"},
        ),
        (
            '<c-CDateRange start_name="start" end_name="end" c-bind="kw" />',
            {},
            "citry-ui-date-range-label",
            "catalogRangeLabel",
            {"range_label": "Mine"},
        ),
        (
            '<c-CDialog c-bind="kw"><c-fill name="title">T</c-fill><c-fill name="default">B</c-fill></c-CDialog>',
            {},
            "citry-ui-dialog-close",
            "catalogCloseLabel",
            {"close_label": "Mine"},
        ),
        (
            '<c-CDrawer c-bind="kw"><c-fill name="title">T</c-fill><c-fill name="default">B</c-fill></c-CDrawer>',
            {},
            "citry-ui-drawer-close",
            "catalogCloseLabel",
            {"close_label": "Mine"},
        ),
        (
            '<c-CEditable value="Atlas" name="title" c-bind="kw" />',
            {},
            "citry-ui-editable-edit",
            "catalogEditLabel",
            {"edit_label": "Mine"},
        ),
    ],
)
def test_null_form_binding_follows_the_catalog_flag_in_browser_data(
    template: str, base: dict[str, object], message: str, flag: str, override: dict[str, object]
) -> None:
    for extra, uses_catalog in (({}, True), (override, False)):
        html, manifest = _null_form_manifest(template, {**base, **extra})
        bindings = [
            binding
            for requirement in manifest["extensions"]["i18n"]["payload"]["requirements"]
            for binding in requirement["bindings"]
            if binding["message"] == message
        ]
        # The binding is written in the template, so it exists in both
        # branches; the browser data decides whether it translates.
        assert bindings, html
        assert all(binding["values_expression"] == f"{flag} ? {{}} : null" for binding in bindings)
        assert _null_form_flag(manifest, flag) is uses_catalog
        if not uses_catalog:
            # The caller's own label is what the server renders and what
            # `null` keeps in the browser.
            assert "Mine" in html


def _bindings_for(manifest: dict[str, object], message: str) -> list[dict[str, object]]:
    payload = manifest["extensions"]["i18n"]["payload"]  # type: ignore[index]
    return [
        binding
        for requirement in payload["requirements"]
        for binding in requirement["bindings"]
        if binding["message"] == message
    ]


@pytest.mark.parametrize(
    ("template", "kwargs", "message", "attribute"),
    [
        # Another element names the calendar, so it renders no aria-label.
        (
            '<c-CCalendar c-bind="kw" />',
            {"attrs": {"aria-labelledby": "heading"}},
            "citry-ui-calendar-label",
            "aria-label",
        ),
        (
            '<c-CDateRange start_name="start" end_name="end" c-bind="kw" />',
            {"attrs": {"aria-labelledby": "heading"}},
            "citry-ui-date-range-label",
            "aria-label",
        ),
        # `None` removes the role description.
        (
            '<c-CCarousel label="Obs" c-bind="kw">'
            '<c-CCarouselSlide value="a" label="A">a</c-CCarouselSlide>'
            "</c-CCarousel>",
            {"role_description": None},
            "citry-ui-carousel-role",
            "aria-roledescription",
        ),
    ],
)
def test_null_form_binding_on_an_attribute_the_component_left_out_is_dropped(
    template: str, kwargs: dict[str, object], message: str, attribute: str
) -> None:
    html, manifest = _null_form_manifest(template, kwargs)
    # The render succeeds, and nothing is left to translate on that attribute.
    assert not [
        binding
        for binding in _bindings_for(manifest, message)
        if binding["target"] == {"kind": "attribute", "name": attribute}
    ], html


_TOUR = (
    '<c-CTour c-open="True" c-bind="kw"><c-fill name="default">'
    '<c-CTourStep value="a"><c-fill name="title">T1</c-fill><c-fill name="default">D1</c-fill></c-CTourStep>'
    "</c-fill></c-CTour>"
)


@pytest.mark.parametrize(
    ("template", "base", "message", "values", "override", "caller_text"),
    [
        (
            '<c-CTable c-rows="()" state="loading" c-bind="kw" />',
            {"columns": (citry_ui.CTableColumn("name", "Name"),)},
            "citry-ui-table-loading",
            {},
            {"loading_label": "Fetching"},
            ">Fetching</span>",
        ),
        (
            '<c-CBreadcrumbs c-bind="kw" />',
            {"items": (CBreadcrumbItem("Home", "/"), CBreadcrumbItem("Here"))},
            "citry-ui-breadcrumbs-label",
            {},
            {"label": "Page location"},
            'aria-label="Page location"',
        ),
        (_TOUR, {}, "citry-ui-tour-close", {}, {"close_label": "Quit"}, 'aria-label="Quit"'),
        (
            '<c-CToastRegion c-duration_ms="0" c-bind="kw" />',
            {"items": (citry_ui.CToastMessage(id="a", title="Saved"),)},
            "citry-ui-toast-dismiss",
            {"title": {"type": "str", "value": "Saved"}},
            {"messages": citry_ui.CToastMessages(dismiss_label="Close {title}")},
            'aria-label="Close Saved"',
        ),
        (
            '<c-CTagsInput name="t" c-bind="kw" />',
            {"value": ("red",), "input_attrs": {"aria-label": "Tags"}},
            "citry-ui-tags-input-remove",
            {"value": {"type": "str", "value": "red"}},
            {"messages": citry_ui.CTagsInputMessages(remove_label="Drop {value}")},
            'aria-label="Drop red"',
        ),
    ],
)
def test_bare_binding_renders_only_on_the_catalog_branch(
    template: str,
    base: dict[str, object],
    message: str,
    values: dict[str, object],
    override: dict[str, object],
    caller_text: str,
) -> None:
    html, manifest = _null_form_manifest(template, base)
    bindings = _bindings_for(manifest, message)
    # The catalog branch's binding has no browser expression: the browser
    # translates again with the values the server passed to tr().
    assert bindings, html
    assert all("values_expression" not in binding for binding in bindings)
    assert bindings[0]["values"] == values
    html, manifest = _null_form_manifest(template, {**base, **override})
    # The caller's own label renders the branch without a binding.
    assert _bindings_for(manifest, message) == []
    assert caller_text in html


_TRANSFER = '<c-CTransferList name="r" c-bind="kw"><c-CTransferListItem value="a" label="Ada" /></c-CTransferList>'


@pytest.mark.parametrize(
    ("template", "base", "message", "flag", "override", "caller_text"),
    [
        (_TRANSFER, {}, "citry-ui-transfer-list-add", "catalog.add", {"add_label": "Move in"}, ">Move in</button>"),
        (
            '<c-CDataGrid c-rows="()" label="Grid" c-bind="kw" />',
            {"columns": (citry_ui.CDataGridColumn("name", "Name"),)},
            "citry-ui-data-grid-empty",
            "serverDefaults.catalog.empty",
            {"empty_label": "Nothing yet"},
            ">Nothing yet</span>",
        ),
        (
            '<c-CToastRegion c-items="()" c-bind="kw" />',
            {},
            "citry-ui-toast-region",
            "catalogLabel",
            {"label": "Alerts"},
            'aria-label="Alerts"',
        ),
    ],
)
def test_null_form_binding_keeps_a_caller_label_in_more_families(
    template: str,
    base: dict[str, object],
    message: str,
    flag: str,
    override: dict[str, object],
    caller_text: str,
) -> None:
    for extra, uses_catalog in (({}, True), (override, False)):
        html, manifest = _null_form_manifest(template, {**base, **extra})
        bindings = _bindings_for(manifest, message)
        assert bindings, html
        assert all(binding["values_expression"] == f"{flag} ? {{}} : null" for binding in bindings)
        assert _null_form_flag(manifest, flag) is uses_catalog
        if not uses_catalog:
            assert caller_text in html
