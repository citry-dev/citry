"""Publishing, packaging, and authoring checks for the Citry UI spike."""

from __future__ import annotations

import importlib.metadata
import importlib.resources
import inspect
import re
import subprocess
import sys
from dataclasses import fields
from types import ModuleType
from typing import get_type_hints

import pytest

import citry_ui
from citry import (
    AlreadyRegistered,
    Citry,
    CitryElement,
    Component,
    ComponentLibrary,
    Extension,
    LibraryComponent,
    LibraryComponentContextError,
    LibraryComponentInvocation,
    LibraryInstallationStale,
    LibraryNotInstalled,
)
from citry_ui import (
    CButton,
    CCombobox,
    CDialog,
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
    assert len(COMPONENTS) == 14
    assert all(issubclass(definition, LibraryComponent) for definition in COMPONENTS)
    assert all(not issubclass(definition, Component) for definition in COMPONENTS)
    assert tuple(definition.__name__ for definition in COMPONENTS) == (
        "CButton",
        "CCombobox",
        "CDialog",
        "CField",
        "CInput",
        "CForm",
        "CTable",
        "CTabs",
        "CTab",
        "CTabPanel",
        "CInternalTabsDeclarations",
        "CInternalTabs",
        "CInternalTab",
        "CInternalTabPanel",
    )


def test_library_publication_rejects_invalid_invocations_and_manifests():
    with pytest.raises(TypeError, match="abstract publishing base"):
        LibraryComponent()
    with pytest.raises(TypeError, match="slots must be a mapping"):
        CButton(slots=[])

    invocation = CButton(slots={"default": "Save"})
    assert invocation.identity == ("citry_ui.components.cbutton.cbutton", "CButton")
    with pytest.raises(TypeError, match="requires a Citry instance"):
        invocation.resolve(object())

    with pytest.raises(ValueError, match=r"ComponentLibrary\.name"):
        ComponentLibrary("Invalid Name", (CButton,))
    with pytest.raises(ValueError, match="at least one definition"):
        ComponentLibrary("empty", ())
    with pytest.raises(TypeError, match="definition classes"):
        ComponentLibrary("invalid", (object,))
    with pytest.raises(ValueError, match="more than once"):
        ComponentLibrary("duplicate", (CButton, CButton))
    with pytest.raises(ValueError, match="unique lowercase Python identifiers"):
        ComponentLibrary("requirements", (CButton,), required_extensions=("Events",))


def test_library_lookup_and_module_coercion_reject_unrelated_values():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)

    class COutside(LibraryComponent):
        template = "outside"

    with pytest.raises(KeyError, match="has no definition"):
        installed[COutside]

    empty_module = ModuleType("empty_component_library")
    with pytest.raises(TypeError, match="must expose a ComponentLibrary"):
        app.register_library(empty_module)
    with pytest.raises(TypeError, match="requires a ComponentLibrary"):
        app.register_library(object())


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
        "citry_ui.components.cbutton.cbutton",
        "citry_ui.components.ccombobox.ccombobox",
        "citry_ui.components.cdialog.cdialog",
        "citry_ui.components.cfield.cfield",
        "citry_ui.components.cform.cform",
        "citry_ui.components.ctable.ctable",
        "citry_ui.components.ctabs.ctabs",
    }
    assert [field.name for field in fields(CButton.Kwargs)] == [
        "type",
        "href",
        "disabled",
        "loading",
        "variant",
        "intent",
        "size",
        "block",
        "loading_pos",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CButton.Slots)] == ["default", "start", "end", "loading"]


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
    assert 'data-citry-ui-part="loading-indicator"' in html
    assert 'class="cui-button__spinner"' in html

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


def test_button_slots_receive_distinct_record_data():
    default_data = []
    start_data = []
    end_data = []
    loading_data = []

    def default_content(ctx):
        default_data.append(ctx.data)
        return "Save"

    def start_content(ctx):
        start_data.append(ctx.data)
        return "Start"

    def end_content(ctx):
        end_data.append(ctx.data)
        return "End"

    def loading_content(ctx):
        loading_data.append(ctx.data)
        return "Pending"

    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    button = CButton(
        loading=True,
        slots={
            "default": default_content,
            "start": start_content,
            "end": end_content,
            "loading": loading_content,
        },
    )

    html = str(button.render(citry=app))

    assert all(value in html for value in ("Save", "Start", "End", "Pending"))
    records = (default_data[0], start_data[0], end_data[0], loading_data[0])
    assert all(dict(record) == {} for record in records)
    assert all(record.__class__.__name__ == "SlotData" for record in records)


def test_inline_assets_and_introspection_are_stable():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)
    app.initialize()
    styled = installed[CButton]

    styled_info = app.inspect_component(styled, resolve_assets=True)

    assert styled_info.name == "c-button"
    assert styled_info.aliases == ("cbutton",)
    assert styled_info.assets.template.kind == "inline"
    assert styled_info.assets.js.kind == "inline"
    assert styled_info.assets.css.kind == "inline"
    assert "<c-element" in styled.get_template().source
    assert 'c-is="root_tag"' in styled.get_template().source
    assert styled.get_js() is not None
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
    assert ">=0.3.1" in citry_requirement
    assert "<0.4.0" in citry_requirement
    assert all(not requirement.startswith("typing-extensions") for requirement in requirements)
    assert resources.joinpath("py.typed").is_file()
    assert resources.joinpath("components/cbutton/cbutton.py").is_file()
    assert resources.joinpath("components/ccombobox/ccombobox.py").is_file()
    assert resources.joinpath("components/cdialog/cdialog.py").is_file()
    assert resources.joinpath("components/cfield/cfield.py").is_file()
    assert resources.joinpath("components/cform/cform.py").is_file()
    assert resources.joinpath("components/ctable/ctable.py").is_file()
    assert resources.joinpath("components/ctabs/ctabs.py").is_file()
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
    assert CField.__module__ == "citry_ui.components.cfield.cfield"
    assert CCombobox.__module__ == "citry_ui.components.ccombobox.ccombobox"
    assert CDialog.__module__ == "citry_ui.components.cdialog.cdialog"
    assert CInput.__module__ == "citry_ui.components.cfield.cfield"
    assert CTable.__module__ == "citry_ui.components.ctable.ctable"
