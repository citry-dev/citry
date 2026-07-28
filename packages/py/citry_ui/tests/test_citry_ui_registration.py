"""Publishing, packaging, and authoring checks for the Citry UI spike."""

from __future__ import annotations

import importlib.metadata
import importlib.resources
import inspect
import re
import subprocess
import sys
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import (
    AlreadyRegistered,
    Citry,
    CitryElement,
    Component,
    Extension,
    LibraryComponent,
    LibraryComponentContextError,
    LibraryComponentInvocation,
    LibraryInstallationStale,
    LibraryNotInstalled,
)
from citry_ui import (
    CButton,
    CButtonHeadless,
    CField,
    CInput,
    CTable,
)
from citry_ui.components import COMPONENTS


def test_import_is_inert_for_the_default_engine():
    script = """
from citry import citry
before = set(citry._registry._name_to_cls)
import citry_ui
after = set(citry._registry._name_to_cls)
assert before == after == set()
print(citry_ui.__version__)
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "0.0.1"


def test_package_exposes_one_explicit_ordered_component_library():
    manifest = citry_ui.__citry_library__

    assert manifest.name == "citry-ui"
    assert manifest.components == COMPONENTS
    assert len(COMPONENTS) == 16
    assert all(issubclass(definition, LibraryComponent) for definition in COMPONENTS)
    assert all(not issubclass(definition, Component) for definition in COMPONENTS)
    assert tuple(definition.__name__ for definition in COMPONENTS) == (
        "CButtonHeadless",
        "CButton",
        "CFieldHeadless",
        "CField",
        "CInputHeadless",
        "CInput",
        "CTableHeadless",
        "CTable",
        "CTabsHeadless",
        "CTabs",
        "CTabListHeadless",
        "CTabList",
        "CTabHeadless",
        "CTab",
        "CTabPanelHeadless",
        "CTabPanel",
    )


def test_repeated_registration_returns_the_same_installation_without_refiring_hooks():
    registrations = []

    class RecordRegistrations(Extension):
        name = "record_ui_registrations"

        def on_component_registered(self, ctx):
            if ctx.component_class.__module__.startswith("citry_ui."):
                registrations.append(ctx.component_class)

    app = Citry(extensions=[RecordRegistrations], autodiscover=False)
    first = app.register_library(citry_ui)
    first_events = tuple(registrations)
    second = app.register_library(citry_ui)

    assert second is first
    assert first.definitions == COMPONENTS
    assert first.classes == tuple(first[definition] for definition in COMPONENTS)
    assert tuple(registrations) == first_events
    assert len(first_events) == len(COMPONENTS)


def test_component_schemas_and_source_modules_are_separate_from_core_plumbing():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)

    assert {component.__module__ for component in installed.classes} == {
        "citry_ui.components.cbutton",
        "citry_ui.components.cfield",
        "citry_ui.components.ctable",
        "citry_ui.components.ctabs",
    }
    assert CButton.Kwargs is not CButtonHeadless.Kwargs
    assert CButton.Slots is not CButtonHeadless.Slots
    assert [field.name for field in fields(CButton.Kwargs)] == ["loading", "disabled", "type"]
    assert [field.name for field in fields(CButtonHeadless.Kwargs)] == ["loading", "disabled", "type"]
    assert [field.name for field in fields(CButton.Slots)] == ["default"]
    assert [field.name for field in fields(CButtonHeadless.Slots)] == ["default"]


def test_two_engines_receive_distinct_classes_with_matching_stable_ids():
    first_app = Citry(autodiscover=False)
    second_app = Citry(autodiscover=False)
    first = first_app.register_library(citry_ui)
    second = second_app.register_library(citry_ui)

    for definition in COMPONENTS:
        first_class = first[definition]
        second_class = second[definition]
        assert first_class is not second_class
        assert first_class.citry is first_app
        assert second_class.citry is second_app
        assert first_class.class_id == second_class.class_id
        assert first_class.definition_id != second_class.definition_id


def test_clear_retires_the_installation_and_reinstall_creates_fresh_classes():
    app = Citry(autodiscover=False)
    first = app.register_library(citry_ui)
    first_button = first[CButton]

    app.clear()

    assert first.is_active is False
    with pytest.raises(LibraryInstallationStale, match="no longer active"):
        first[CButton]

    second = app.register_library(citry_ui)
    assert second[CButton] is not first_button
    assert second[CButton].class_id == first_button.class_id


def test_registry_collision_is_rejected_before_any_library_class_is_created():
    app = Citry(autodiscover=False)

    class Occupied(Component):
        citry = app
        name = "CTable"

    with pytest.raises(AlreadyRegistered, match="ctable"):
        app.register_library(citry_ui)

    assert app.get("CTable") is Occupied
    assert app.has("CButton") is False
    assert app.has("CField") is False


def test_extension_failure_rolls_back_the_complete_library():
    class RejectTable(Extension):
        name = "reject_ui_table"

        def on_component_class_created(self, ctx):
            if ctx.component_class.__name__ == "CTable":
                raise RuntimeError("reject table")

    app = Citry(extensions=[RejectTable], autodiscover=False)

    with pytest.raises(RuntimeError, match="reject table"):
        app.register_library(citry_ui)

    assert all(app.has(definition.__name__) is False for definition in COMPONENTS)
    with pytest.raises(LibraryNotInstalled):
        app.get_library_installation("citry-ui")


def test_installed_classes_compose_directly_and_support_runtime_subclassing():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)
    element = installed[CButton](slots={"default": "Save"}, loading=True)

    assert isinstance(element, CitryElement)
    html = str(element)
    assert "Save" in html
    assert 'aria-busy="true"' in html
    assert "Loading" in html

    class BrandedButton(installed[CButton]):
        name = "BrandedButton"
        css = """
          .branded-button {
            color: rebeccapurple;
          }
        """

    assert BrandedButton.citry is app
    assert app.get("BrandedButton") is BrandedButton


def test_direct_template_tag_is_the_primary_styled_usage():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <main>
            <c-CButton type="submit">
              Save
            </c-CButton>
          </main>
        """

    html = str(Page())

    assert '<button class="cui-button" type="submit"' in html
    assert "Save" in html
    assert app.get("CButton") is installed[CButton]


def test_headless_button_owns_no_html_and_exposes_bindings_as_slot_data():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <main>
            <c-CButtonHeadless loading type="submit">
              <c-fill name="default" data="data">
                <button
                  class="brand-action"
                  c-bind="data.attrs"
                >
                  Custom {{ data.loading }}
                </button>
              </c-fill>
            </c-CButtonHeadless>
          </main>
        """

    html = str(Page())

    assert '<button class="brand-action" type="submit" disabled aria-busy="true" data-loading>' in html
    assert "Custom True" in html
    assert html.count("<button") == 1
    assert "cui-button" not in html


def test_public_invocation_resolves_contextually_or_through_an_explicit_engine():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    button = CButton(loading=True, slots={"default": "Save"})

    assert isinstance(button, LibraryComponentInvocation)
    assert button.kwargs == {"loading": True}
    assert button.slots == {"default": "Save"}
    assert '<button class="cui-button" type="button"' in str(button.render(citry=app))
    with pytest.raises(LibraryComponentContextError, match="Pass citry=app"):
        button.render()
    with pytest.raises(LibraryComponentContextError, match="Pass citry=app"):
        str(button)

    class Page(Component):
        citry = app
        template = """
          <main>
            {{ button }}
          </main>
        """

        def template_data(self, kwargs, slots):
            return {"button": button}

    assert '<button class="cui-button" type="button"' in str(Page())


def test_invocation_resolution_never_uses_an_unrelated_name_collision():
    app = Citry(autodiscover=False)

    class Unrelated(Component):
        citry = app
        name = "CButton"
        template = "unrelated"

    button = CButton(slots={"default": "Save"})

    with pytest.raises(LibraryNotInstalled, match="register_library"):
        button.resolve(app)
    assert app.get("CButton") is Unrelated


def test_styled_and_headless_default_slots_receive_distinct_record_data():
    styled_data = []
    headless_data = []

    def styled_content(ctx):
        styled_data.append(ctx.data)
        return "Styled"

    def headless_content(ctx):
        headless_data.append(ctx.data)
        return "Headless"

    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    styled = CButton(slots={"default": styled_content})
    headless = CButtonHeadless(loading=True, slots={"default": headless_content})

    assert "Styled" in str(styled.render(citry=app))
    assert "Headless" in str(headless.render(citry=app))
    assert dict(styled_data[0]) == {}
    assert dict(headless_data[0]) == {
        "attrs": {
            "type": "button",
            "disabled": True,
            "aria-busy": "true",
            "data-loading": True,
        },
        "disabled": True,
        "loading": True,
    }
    assert styled_data[0].__class__.__name__ == "SlotData"
    assert headless_data[0].loading is True


def test_inline_assets_and_introspection_are_stable():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)
    app.initialize()
    styled = installed[CButton]
    headless = installed[CButtonHeadless]

    styled_info = app.inspect_component(styled, resolve_assets=True)
    headless_info = app.inspect_component(headless, resolve_assets=True)

    assert styled_info.name == "c-button"
    assert styled_info.aliases == ("cbutton",)
    assert styled_info.assets.template.kind == "inline"
    assert styled_info.assets.js.kind == "none"
    assert styled_info.assets.css.kind == "inline"
    assert headless_info.name == "c-button-headless"
    assert headless_info.aliases == ("cbuttonheadless",)
    assert headless_info.assets.css.kind == "none"
    assert "<c-CButtonHeadless" in styled.get_template().source
    assert styled.get_js() is None
    assert headless.get_js() is None
    assert "@layer citry-ui.theme" in styled.get_css()
    inspected_names = {item.name for item in app.inspect_components().components}
    assert inspected_names == {
        re.sub(r"(?<!^)(?=[A-Z])", "-", definition.__name__).lower() for definition in COMPONENTS
    }


def test_data_method_signatures_use_component_specific_input_types():
    for definition in COMPONENTS:
        method = definition.__dict__.get("template_data")
        if method is None:
            continue
        signature = inspect.signature(method)
        annotations = get_type_hints(method, localns=vars(definition))
        assert annotations["kwargs"] is definition.Kwargs
        assert annotations["slots"] is definition.Slots
        assert signature.parameters["slots"].default is inspect.Parameter.empty


def test_distribution_metadata_and_resources_use_only_the_citry_ui_namespace():
    requirements = importlib.metadata.requires("citry-ui")
    resources = importlib.resources.files("citry_ui")

    assert requirements is not None
    citry_requirement = next(requirement for requirement in requirements if requirement.startswith("citry"))
    assert ">=0.2.0" in citry_requirement
    assert "<0.3.0" in citry_requirement
    assert all(not requirement.startswith("typing-extensions") for requirement in requirements)
    assert resources.joinpath("py.typed").is_file()
    assert resources.joinpath("components/cbutton.py").is_file()
    assert resources.joinpath("components/cfield.py").is_file()
    assert resources.joinpath("components/ctable.py").is_file()
    assert resources.joinpath("components/ctabs.py").is_file()
    assert resources.joinpath("_definitions.py").is_file() is False
    assert resources.joinpath("_installation.py").is_file() is False
    assert resources.joinpath("_invocation.py").is_file() is False
    assert resources.joinpath("_registration.py").is_file() is False


def test_component_files_have_no_constructor_or_explicit_same_name_plumbing():
    for definition in COMPONENTS:
        source = inspect.getsource(sys.modules[definition.__module__])
        assert "def _construct_" not in source
        assert "name" not in definition.__dict__


def test_representative_component_definitions_remain_directly_importable():
    assert CField.__module__ == "citry_ui.components.cfield"
    assert CInput.__module__ == "citry_ui.components.cfield"
    assert CTable.__module__ == "citry_ui.components.ctable"
