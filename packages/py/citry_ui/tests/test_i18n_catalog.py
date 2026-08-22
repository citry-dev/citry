"""Citry UI component sources, catalog packaging, and runtime tests."""

from __future__ import annotations

import ast
import importlib.resources
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

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
    assert html.count("data-citry-i18n-binding=") == 1
    assert "citry-ui-breadcrumbs-label" in html
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
