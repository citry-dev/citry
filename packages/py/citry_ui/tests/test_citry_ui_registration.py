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
import citry_ui.components as citry_ui_components
import citry_ui.components.ccommand_palette as command_palette_family
import citry_ui.components.ccontext_menu as context_menu_family
import citry_ui.components.cimage as image_family
import citry_ui.components.cscroll_area as scroll_area_family
import citry_ui.components.csplitbutton as split_button_family
import citry_ui.components.ctags_input as tags_input_family
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
    CAccordion,
    CAccordionItem,
    CAlert,
    CAlertDialog,
    CBadge,
    CBreadcrumbs,
    CButton,
    CCard,
    CCarousel,
    CCarouselSlide,
    CCheckbox,
    CCombobox,
    CCommandPalette,
    CContainer,
    CContextMenu,
    CDataGrid,
    CDialog,
    CDisclosure,
    CDrawer,
    CDropTarget,
    CEditable,
    CField,
    CFileInput,
    CGrid,
    CGridItem,
    CGroup,
    CHoverCard,
    CIcon,
    CImage,
    CInput,
    CListbox,
    CListboxGroup,
    CListboxOption,
    CMenu,
    CMenuCheckboxItem,
    CMenuGroup,
    CMenuItem,
    CMenuRadioGroup,
    CMenuRadioItem,
    CMenuSeparator,
    CMenuSubmenu,
    CMultiSelect,
    CMultiSelectOption,
    CNativeSelect,
    CNativeSelectGroup,
    CNativeSelectOption,
    CNavigationMenu,
    CNavigationMenuItem,
    CNavigationMenuLink,
    CPopover,
    CProgress,
    CRadio,
    CRadioGroup,
    CScrollArea,
    CSelect,
    CSidebar,
    CSpinner,
    CSplitButton,
    CSplitter,
    CSplitterPanel,
    CStack,
    CStep,
    CStepper,
    CSwitch,
    CTable,
    CTagsInput,
    CTextarea,
    CTimeline,
    CTimelineItem,
    CToastRegion,
    CToolbar,
    CTooltip,
    CTour,
    CTourStep,
    CTransferList,
    CTransferListItem,
    CTree,
    CTreeItem,
    CVirtualList,
    CVirtualListItem,
    CVirtualWindow,
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
    assert result.stdout.strip() == "0.1.0"


def test_package_exposes_one_explicit_ordered_component_library():
    manifest = citry_ui.__citry_library__

    assert manifest.name == "citry-ui"
    assert manifest.components == COMPONENTS
    assert manifest.required_extensions == ()
    assert len(COMPONENTS) == 137
    assert all(issubclass(definition, LibraryComponent) for definition in COMPONENTS)
    assert all(not issubclass(definition, Component) for definition in COMPONENTS)
    assert tuple(definition.__name__ for definition in COMPONENTS) == (
        "CAccordion",
        "CAccordionItem",
        "CInternalAccordionItems",
        "CInternalAccordionPanelContent",
        "CDisclosure",
        "CInternalDisclosureTitleContent",
        "CInternalDisclosureActionsContent",
        "CInternalDisclosurePanelContent",
        "CAlert",
        "CAlertDialog",
        "CAvatar",
        "CImage",
        "CBreadcrumbs",
        "CBadge",
        "CButton",
        "CButtonGroup",
        "CSplitButton",
        "CCarousel",
        "CCarouselSlide",
        "CCombobox",
        "CCommandPalette",
        "CDialog",
        "CDrawer",
        "CDivider",
        "CEditable",
        "CHoverCard",
        "CField",
        "CInput",
        "CFileInput",
        "CDropTarget",
        "CTextarea",
        "CNativeSelect",
        "CCheckbox",
        "CForm",
        "CStack",
        "CGroup",
        "CContainer",
        "CGrid",
        "CGridItem",
        "CScrollArea",
        "CIcon",
        "CList",
        "CListItem",
        "CListbox",
        "CListboxOption",
        "CListboxGroup",
        "CNavigationMenu",
        "CNavigationMenuLink",
        "CNavigationMenuItem",
        "CSelect",
        "CMenu",
        "CMenuItem",
        "CMenuCheckboxItem",
        "CMenuRadioGroup",
        "CMenuRadioItem",
        "CMenuGroup",
        "CMenuSeparator",
        "CMenuSubmenu",
        "CInternalMenuCollection",
        "CInternalMenuContent",
        "CInternalMenuSurface",
        "CContextMenu",
        "CDataGrid",
        "CMultiSelect",
        "CTagsInput",
        "CNumberInput",
        "CSlider",
        "CRangeSlider",
        "CRating",
        "CPinInput",
        "CDateInput",
        "CDatePicker",
        "CDateRange",
        "CTimeInput",
        "CTimePicker",
        "CCalendar",
        "CProgress",
        "CPagination",
        "CPopover",
        "CTooltip",
        "CToastRegion",
        "CRadioGroup",
        "CRadio",
        "CSpinner",
        "CSidebar",
        "CSplitter",
        "CSplitterPanel",
        "CStepper",
        "CStep",
        "CTimeline",
        "CTimelineItem",
        "CTour",
        "CTourStep",
        "CTransferList",
        "CTransferListItem",
        "CVirtualList",
        "CVirtualListItem",
        "CVirtualWindow",
        "CSkeleton",
        "CSwitch",
        "CCard",
        "CTable",
        "CTabs",
        "CTab",
        "CTabPanel",
        "CTagGroup",
        "CTag",
        "CToggleGroup",
        "CToggle",
        "CToolbar",
        "CTree",
        "CTreeItem",
        "CInternalTabsDeclarations",
        "CInternalTabs",
        "CInternalTab",
        "CInternalTabPanel",
        "CInternalStepperDeclarations",
        "CInternalStepper",
        "CInternalStep",
        "CInternalTimelineDeclarations",
        "CInternalTimeline",
        "CInternalTimelineItem",
        "CInternalTourDeclarations",
        "CInternalTour",
        "CInternalTourStep",
        "CInternalTransferListDeclarations",
        "CInternalTransferList",
        "CInternalTransferListItem",
        "CInternalVirtualListDeclarations",
        "CInternalVirtualList",
        "CInternalVirtualListStatic",
        "CInternalVirtualListWindow",
        "CInternalVirtualListItem",
        "CInternalSplitterDeclarations",
        "CInternalSplitter",
        "CInternalSplitterPanel",
        "CInternalSplitterHandle",
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
        "citry_ui.components.caccordion.caccordion",
        "citry_ui.components.cdisclosure.cdisclosure",
        "citry_ui.components.calert.calert",
        "citry_ui.components.calert_dialog.calert_dialog",
        "citry_ui.components.cavatar.cavatar",
        "citry_ui.components.cimage.cimage",
        "citry_ui.components.cbadge.cbadge",
        "citry_ui.components.cbreadcrumbs.cbreadcrumbs",
        "citry_ui.components.cbutton.cbutton",
        "citry_ui.components.cbutton_group.cbutton_group",
        "citry_ui.components.ccalendar.ccalendar",
        "citry_ui.components.cdate_picker.cdate_picker",
        "citry_ui.components.cdate_range.cdate_range",
        "citry_ui.components.ctime_input.ctime_input",
        "citry_ui.components.ctime_picker.ctime_picker",
        "citry_ui.components.csplitbutton.csplitbutton",
        "citry_ui.components.ccarousel.ccarousel",
        "citry_ui.components.ccombobox.ccombobox",
        "citry_ui.components.ccommand_palette.ccommand_palette",
        "citry_ui.components.ccontext_menu.ccontext_menu",
        "citry_ui.components.cdata_grid.cdata_grid",
        "citry_ui.components.cdialog.cdialog",
        "citry_ui.components.cdrawer.cdrawer",
        "citry_ui.components.cdivider.cdivider",
        "citry_ui.components.ceditable.ceditable",
        "citry_ui.components.cfield.cfield",
        "citry_ui.components.cfile_input.cfile_input",
        "citry_ui.components.cflow.cflow",
        "citry_ui.components.cgrid.cgrid",
        "citry_ui.components.cscroll_area.cscroll_area",
        "citry_ui.components.chover_card.chover_card",
        "citry_ui.components.cform.cform",
        "citry_ui.components.cicon.cicon",
        "citry_ui.components.clist.clist",
        "citry_ui.components.clistbox.clistbox",
        "citry_ui.components.cselect.cselect",
        "citry_ui.components.cmulti_select.cmulti_select",
        "citry_ui.components.ctags_input.ctags_input",
        "citry_ui.components.cnavigation_menu.cnavigation_menu",
        "citry_ui.components.cnumber_input.cnumber_input",
        "citry_ui.components.cslider.cslider",
        "citry_ui.components.crating.crating",
        "citry_ui.components.cpin_input.cpin_input",
        "citry_ui.components.cdate_input.cdate_input",
        "citry_ui.components.cmenu.cmenu",
        "citry_ui.components.ccard.ccard",
        "citry_ui.components.ctable.ctable",
        "citry_ui.components.ctabs.ctabs",
        "citry_ui.components.ctag.ctag",
        "citry_ui.components.ctextarea.ctextarea",
        "citry_ui.components.cnative_select.cnative_select",
        "citry_ui.components.cprogress.cprogress",
        "citry_ui.components.cpagination.cpagination",
        "citry_ui.components.cpopover.cpopover",
        "citry_ui.components.ctooltip.ctooltip",
        "citry_ui.components.ctoast.ctoast",
        "citry_ui.components.cradio.cradio",
        "citry_ui.components.cspinner.cspinner",
        "citry_ui.components.csidebar.csidebar",
        "citry_ui.components.csplitter.csplitter",
        "citry_ui.components.cstepper.cstepper",
        "citry_ui.components.ctimeline.ctimeline",
        "citry_ui.components.ctour.ctour",
        "citry_ui.components.ctransfer_list.ctransfer_list",
        "citry_ui.components.cvirtual_list.cvirtual_list",
        "citry_ui.components.cskeleton.cskeleton",
        "citry_ui.components.cswitch.cswitch",
        "citry_ui.components.ctoggle.ctoggle",
        "citry_ui.components.ctoolbar.ctoolbar",
        "citry_ui.components.ctree.ctree",
        "citry_ui.components.ccheckbox.ccheckbox",
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


def test_primary_and_shared_assets_and_introspection_are_stable():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)
    app.initialize()
    styled = installed[CButton]

    styled_info = app.inspect_component(styled, resolve_assets=True)

    assert styled_info.name == "c-button"
    assert styled_info.aliases == ("cbutton",)
    assert styled_info.assets.template.kind == "inline"
    assert styled_info.assets.js.kind == "inline"
    assert styled_info.assets.css.kind == "none"
    assert "<c-element" in styled.get_template().source
    assert 'c-is="root_tag"' in styled.get_template().source
    assert styled.get_js() is not None
    assert styled.get_css() is None
    shared_css = tuple(
        entry.render_json()["content"] for entries in styled.get_dependencies().css.values() for entry in entries
    )
    assert any("@layer citry-ui.theme" in payload for payload in shared_css)
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
    assert ">=0.4.2" in citry_requirement
    assert "<0.5.0" in citry_requirement
    assert all(not requirement.startswith("typing-extensions") for requirement in requirements)
    assert resources.joinpath("py.typed").is_file()
    assert resources.joinpath("components/caccordion/caccordion.py").is_file()
    assert resources.joinpath("components/cdisclosure/cdisclosure.py").is_file()
    assert resources.joinpath("components/cbutton/cbutton.py").is_file()
    assert resources.joinpath("components/cimage/cimage.py").is_file()
    assert resources.joinpath("components/csplitbutton/csplitbutton.py").is_file()
    assert resources.joinpath("components/cbreadcrumbs/cbreadcrumbs.py").is_file()
    assert resources.joinpath("components/ccarousel/ccarousel.py").is_file()
    assert resources.joinpath("components/ccombobox/ccombobox.py").is_file()
    assert resources.joinpath("components/_active_descendant.py").is_file()
    assert resources.joinpath("components/_dialog_controller.py").is_file()
    assert resources.joinpath("components/ccommand_palette/ccommand_palette.py").is_file()
    assert resources.joinpath("components/cdialog/cdialog.py").is_file()
    assert resources.joinpath("components/calert_dialog/calert_dialog.py").is_file()
    assert resources.joinpath("components/cdrawer/cdrawer.py").is_file()
    assert resources.joinpath("components/ceditable/ceditable.py").is_file()
    assert resources.joinpath("components/cfield/cfield.py").is_file()
    assert resources.joinpath("components/cfile_input/cfile_input.py").is_file()
    assert resources.joinpath("components/cflow/cflow.py").is_file()
    assert resources.joinpath("components/cgrid/cgrid.py").is_file()
    assert resources.joinpath("components/_scroll_geometry.py").is_file()
    assert resources.joinpath("components/cscroll_area/cscroll_area.py").is_file()
    assert resources.joinpath("components/chover_card/chover_card.py").is_file()
    assert resources.joinpath("components/cform/cform.py").is_file()
    assert resources.joinpath("components/cicon/cicon.py").is_file()
    assert resources.joinpath("components/clistbox/clistbox.py").is_file()
    assert resources.joinpath("components/cselect/cselect.py").is_file()
    assert resources.joinpath("components/cmulti_select/cmulti_select.py").is_file()
    assert resources.joinpath("components/ctags_input/ctags_input.py").is_file()
    assert resources.joinpath("components/cnavigation_menu/cnavigation_menu.py").is_file()
    assert resources.joinpath("components/_anchored_layer.py").is_file()
    assert resources.joinpath("components/cmenu/cmenu.py").is_file()
    assert resources.joinpath("components/ccard/ccard.py").is_file()
    assert resources.joinpath("components/ctable/ctable.py").is_file()
    assert resources.joinpath("components/ctabs/ctabs.py").is_file()
    assert resources.joinpath("components/ctextarea/ctextarea.py").is_file()
    assert resources.joinpath("components/cnative_select/cnative_select.py").is_file()
    assert resources.joinpath("components/cprogress/cprogress.py").is_file()
    assert resources.joinpath("components/cradio/cradio.py").is_file()
    assert resources.joinpath("components/cspinner/cspinner.py").is_file()
    assert resources.joinpath("components/csidebar/csidebar.py").is_file()
    assert resources.joinpath("components/csplitter/csplitter.py").is_file()
    assert resources.joinpath("components/cstepper/cstepper.py").is_file()
    assert resources.joinpath("components/ctimeline/ctimeline.py").is_file()
    assert resources.joinpath("components/ctour/ctour.py").is_file()
    assert resources.joinpath("components/ctransfer_list/ctransfer_list.py").is_file()
    assert resources.joinpath("components/cswitch/cswitch.py").is_file()
    assert resources.joinpath("components/ccheckbox/ccheckbox.py").is_file()
    assert resources.joinpath("components/calert/calert.py").is_file()
    assert resources.joinpath("components/cpopover/cpopover.py").is_file()
    assert resources.joinpath("components/ccontext_menu/ccontext_menu.py").is_file()
    assert resources.joinpath("components/ctooltip/ctooltip.py").is_file()
    assert resources.joinpath("components/ctoast/ctoast.py").is_file()
    assert resources.joinpath("components/cbadge/cbadge.py").is_file()
    assert resources.joinpath("components/ctoolbar/ctoolbar.py").is_file()
    assert resources.joinpath("components/ctree/ctree.py").is_file()
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
    assert CAccordion.__module__ == "citry_ui.components.caccordion.caccordion"
    assert CAccordionItem.__module__ == "citry_ui.components.caccordion.caccordion"
    assert CDisclosure.__module__ == "citry_ui.components.cdisclosure.cdisclosure"
    assert CAlert.__module__ == "citry_ui.components.calert.calert"
    assert CAlertDialog.__module__ == "citry_ui.components.calert_dialog.calert_dialog"
    assert CBadge.__module__ == "citry_ui.components.cbadge.cbadge"
    assert CCarousel.__module__ == "citry_ui.components.ccarousel.ccarousel"
    assert CCarouselSlide.__module__ == "citry_ui.components.ccarousel.ccarousel"
    assert CBreadcrumbs.__module__ == "citry_ui.components.cbreadcrumbs.cbreadcrumbs"
    assert CField.__module__ == "citry_ui.components.cfield.cfield"
    assert CStack.__module__ == "citry_ui.components.cflow.cflow"
    assert CGroup.__module__ == "citry_ui.components.cflow.cflow"
    assert CContainer.__module__ == "citry_ui.components.cgrid.cgrid"
    assert CGrid.__module__ == "citry_ui.components.cgrid.cgrid"
    assert CGridItem.__module__ == "citry_ui.components.cgrid.cgrid"
    assert CScrollArea.__module__ == "citry_ui.components.cscroll_area.cscroll_area"
    assert CHoverCard.__module__ == "citry_ui.components.chover_card.chover_card"
    assert CCombobox.__module__ == "citry_ui.components.ccombobox.ccombobox"
    assert CCommandPalette.__module__ == "citry_ui.components.ccommand_palette.ccommand_palette"
    assert CContextMenu.__module__ == "citry_ui.components.ccontext_menu.ccontext_menu"
    assert CDataGrid.__module__ == "citry_ui.components.cdata_grid.cdata_grid"
    assert CDialog.__module__ == "citry_ui.components.cdialog.cdialog"
    assert CDrawer.__module__ == "citry_ui.components.cdrawer.cdrawer"
    assert CEditable.__module__ == "citry_ui.components.ceditable.ceditable"
    assert CInput.__module__ == "citry_ui.components.cfield.cfield"
    assert CFileInput.__module__ == "citry_ui.components.cfile_input.cfile_input"
    assert CDropTarget.__module__ == "citry_ui.components.cfile_input.cfile_input"
    assert CIcon.__module__ == "citry_ui.components.cicon.cicon"
    assert CImage.__module__ == "citry_ui.components.cimage.cimage"
    assert CListbox.__module__ == "citry_ui.components.clistbox.clistbox"
    assert CListboxOption.__module__ == "citry_ui.components.clistbox.clistbox"
    assert CListboxGroup.__module__ == "citry_ui.components.clistbox.clistbox"
    assert CSelect.__module__ == "citry_ui.components.cselect.cselect"
    assert CMultiSelect.__module__ == "citry_ui.components.cmulti_select.cmulti_select"
    assert CMultiSelectOption.__module__ == "citry_ui.components.cmulti_select.cmulti_select"
    assert CTagsInput.__module__ == "citry_ui.components.ctags_input.ctags_input"
    assert CNavigationMenu.__module__ == "citry_ui.components.cnavigation_menu.cnavigation_menu"
    assert CNavigationMenuLink.__module__ == "citry_ui.components.cnavigation_menu.cnavigation_menu"
    assert CNavigationMenuItem.__module__ == "citry_ui.components.cnavigation_menu.cnavigation_menu"
    assert CMenu.__module__ == "citry_ui.components.cmenu.cmenu"
    assert CMenuItem.__module__ == "citry_ui.components.cmenu.cmenu"
    assert CMenuCheckboxItem.__module__ == "citry_ui.components.cmenu.cmenu"
    assert CMenuRadioGroup.__module__ == "citry_ui.components.cmenu.cmenu"
    assert CMenuRadioItem.__module__ == "citry_ui.components.cmenu.cmenu"
    assert CMenuGroup.__module__ == "citry_ui.components.cmenu.cmenu"
    assert CMenuSeparator.__module__ == "citry_ui.components.cmenu.cmenu"
    assert CMenuSubmenu.__module__ == "citry_ui.components.cmenu.cmenu"
    assert CCard.__module__ == "citry_ui.components.ccard.ccard"
    assert CTable.__module__ == "citry_ui.components.ctable.ctable"
    assert CTextarea.__module__ == "citry_ui.components.ctextarea.ctextarea"
    assert CNativeSelect.__module__ == "citry_ui.components.cnative_select.cnative_select"
    assert CNativeSelectOption.__module__ == "citry_ui.components.cnative_select.cnative_select"
    assert CNativeSelectGroup.__module__ == "citry_ui.components.cnative_select.cnative_select"
    assert CProgress.__module__ == "citry_ui.components.cprogress.cprogress"
    assert CPopover.__module__ == "citry_ui.components.cpopover.cpopover"
    assert CTooltip.__module__ == "citry_ui.components.ctooltip.ctooltip"
    assert CToastRegion.__module__ == "citry_ui.components.ctoast.ctoast"
    assert CToolbar.__module__ == "citry_ui.components.ctoolbar.ctoolbar"
    assert CTree.__module__ == "citry_ui.components.ctree.ctree"
    assert CTreeItem.__module__ == "citry_ui.components.ctree.ctree"
    assert CRadioGroup.__module__ == "citry_ui.components.cradio.cradio"
    assert CRadio.__module__ == "citry_ui.components.cradio.cradio"
    assert CSpinner.__module__ == "citry_ui.components.cspinner.cspinner"
    assert CSidebar.__module__ == "citry_ui.components.csidebar.csidebar"
    assert CSplitButton.__module__ == "citry_ui.components.csplitbutton.csplitbutton"
    assert CSplitter.__module__ == "citry_ui.components.csplitter.csplitter"
    assert CSplitterPanel.__module__ == "citry_ui.components.csplitter.csplitter"
    assert CStepper.__module__ == "citry_ui.components.cstepper.cstepper"
    assert CStep.__module__ == "citry_ui.components.cstepper.cstepper"
    assert CTimeline.__module__ == "citry_ui.components.ctimeline.ctimeline"
    assert CTimelineItem.__module__ == "citry_ui.components.ctimeline.ctimeline"
    assert CTour.__module__ == "citry_ui.components.ctour.ctour"
    assert CTourStep.__module__ == "citry_ui.components.ctour.ctour"
    assert CTransferList.__module__ == "citry_ui.components.ctransfer_list.ctransfer_list"
    assert CTransferListItem.__module__ == "citry_ui.components.ctransfer_list.ctransfer_list"
    assert CVirtualList.__module__ == "citry_ui.components.cvirtual_list.cvirtual_list"
    assert CVirtualListItem.__module__ == "citry_ui.components.cvirtual_list.cvirtual_list"
    assert CVirtualWindow.__module__ == "citry_ui.components.cvirtual_list.cvirtual_list"
    assert CSwitch.__module__ == "citry_ui.components.cswitch.cswitch"
    assert CCheckbox.__module__ == "citry_ui.components.ccheckbox.ccheckbox"


def test_split_button_family_exports_exact_public_schema_without_reexporting_aliases():
    names = {
        "CSplitButton",
        "CSplitButtonDefaultSlotData",
        "CSplitButtonStartSlotData",
        "CSplitButtonEndSlotData",
        "CSplitButtonLoadingSlotData",
        "CSplitButtonMenuSlotData",
    }

    assert set(split_button_family.__all__) == names
    for name in names:
        family_value = getattr(split_button_family, name)
        assert getattr(citry_ui_components, name) is family_value
        assert getattr(citry_ui, name) is family_value
    assert {
        "CButtonType",
        "CButtonVariant",
        "CButtonIntent",
        "CButtonSize",
        "CButtonLoadingPos",
        "CMenuPlacement",
    }.isdisjoint(split_button_family.__all__)


def test_tags_input_family_exports_exact_public_schema():
    names = {
        "CTagsInput",
        "CTagsInputMessages",
        "CTagsInputVariant",
        "CTagsInputSize",
        "CTagsInputChangeSource",
        "CTagsInputInvalidReason",
        "CTagsInputValueChangeDetail",
        "CTagsInputInputValueChangeDetail",
        "CTagsInputInvalidDetail",
    }

    assert set(tags_input_family.__all__) == names
    for name in names:
        family_value = getattr(tags_input_family, name)
        assert getattr(citry_ui_components, name) is family_value
        assert getattr(citry_ui, name) is family_value


def test_scroll_area_family_exports_exact_public_schema():
    names = {
        "CScrollArea",
        "CScrollAreaAxis",
        "CScrollAreaScrollbarWidth",
        "CScrollAreaScrollbarGutter",
        "CScrollAreaOverscroll",
        "CScrollAreaScrollDetail",
    }

    assert set(scroll_area_family.__all__) == names
    for name in names:
        family_value = getattr(scroll_area_family, name)
        assert getattr(citry_ui_components, name) is family_value
        assert getattr(citry_ui, name) is family_value


def test_context_menu_family_exports_exact_public_schema_without_private_renderer():
    names = {
        "CContextMenu",
        "CContextMenuTargetSlotData",
        "CContextMenuMenuSlotData",
        "CContextMenuOpenChangeDetail",
    }

    assert set(context_menu_family.__all__) == names
    for name in names:
        family_value = getattr(context_menu_family, name)
        assert getattr(citry_ui_components, name) is family_value
        assert getattr(citry_ui, name) is family_value
    assert "CInternalMenuSurface" not in citry_ui_components.__all__
    assert "CInternalMenuSurface" not in citry_ui.__all__


def test_command_palette_family_exports_exact_public_schema_without_record_registration():
    names = {
        "CCommandPalette",
        "CCommandPaletteCommand",
        "CCommandPaletteGroup",
        "CCommandPaletteSeparator",
        "CCommandPaletteEntry",
        "CCommandPaletteIntent",
        "CCommandPaletteSize",
        "CCommandPaletteActionSource",
        "CCommandPaletteActionDetail",
        "CCommandPaletteOpenReason",
        "CCommandPaletteOpenChangeDetail",
        "CCommandPaletteQueryReason",
        "CCommandPaletteQueryChangeDetail",
        "CCommandPaletteItemSlotData",
    }

    assert set(command_palette_family.__all__) == names
    for name in names:
        family_value = getattr(command_palette_family, name)
        assert getattr(citry_ui_components, name) is family_value
        assert getattr(citry_ui, name) is family_value
    assert tuple(
        definition
        for definition in COMPONENTS
        if definition.__module__.startswith("citry_ui.components.ccommand_palette")
    ) == (CCommandPalette,)


def test_image_family_exports_exact_public_schema_without_record_registration():
    names = {
        "CImage",
        "CImageCrossOrigin",
        "CImageDecoding",
        "CImageFetchPriority",
        "CImageFit",
        "CImageLoading",
        "CImageReferrerPolicy",
        "CImageSource",
        "CImageStatus",
        "CImageStatusChangeDetail",
    }

    assert set(image_family.__all__) == names
    for name in names:
        family_value = getattr(image_family, name)
        assert getattr(citry_ui_components, name) is family_value
        assert getattr(citry_ui, name) is family_value
    assert tuple(
        definition for definition in COMPONENTS if definition.__module__.startswith("citry_ui.components.cimage")
    ) == (CImage,)
