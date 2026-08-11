"""Run bounded diagnostic rendering profiles for Citry UI scaling."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict, dataclass
from functools import partial
from time import perf_counter
from typing import TYPE_CHECKING, cast

import citry_ui
from citry import Citry, Component

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True, slots=True)
class ScalingSample:
    """One diagnostic-only render measurement."""

    profile: str
    count: int
    median_ms: float
    output_bytes: int
    status: str = "diagnostic-only"


def _measure(render: Callable[[], str], *, samples: int) -> tuple[float, int]:
    durations: list[float] = []
    size = 0
    for _ in range(samples):
        start = perf_counter()
        output = render()
        durations.append((perf_counter() - start) * 1_000)
        size = len(output.encode())
    return statistics.median(durations), size


def _render_scaled(component: Callable[..., object], count: int) -> str:
    return str(component(count=count))


def scaling_report(*, counts: tuple[int, ...], samples: int = 3) -> dict[str, object]:
    """Measure representative component counts without setting timing gates."""
    if samples < 1:
        msg = "samples must be at least 1"
        raise ValueError(msg)
    if not counts or any(isinstance(count, bool) or count < 1 for count in counts):
        msg = "counts must contain positive integers"
        raise ValueError(msg)

    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class AccordionScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <c-CAccordion>
            <c-for each="item in items">
              <c-CAccordionItem c-value="f'item-{item}'">
                <c-fill name="title">Section {{ item }}</c-fill>
                <c-fill name="default">Panel {{ item }}</c-fill>
              </c-CAccordionItem>
            </c-for>
          </c-CAccordion>
        """

    class DisclosureScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CDisclosure #c-key="item" c-id="f'cui-scale-disclosure-{item}'">
                <c-fill name="title">Section {{ item }}</c-fill>
                <c-fill name="default">Panel {{ item }}</c-fill>
              </c-CDisclosure>
            </c-for>
          </div>
        """

    class AlertScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CAlert #c-key="item">
                Alert {{ item }}
              </c-CAlert>
            </c-for>
          </div>
        """

    class ButtonScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CButton #c-key="item">
                Action {{ item }}
              </c-CButton>
            </c-for>
          </div>
        """

    class AvatarScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CAvatar #c-key="item" c-alt="f'Guide {item}'">{{ item }}</c-CAvatar>
            </c-for>
          </div>
        """

    class BadgeScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CBadge #c-key="item">Label {{ item }}</c-CBadge>
            </c-for>
          </div>
        """

    class DividerScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CDivider #c-key="item" c-decorative="True" />
            </c-for>
          </div>
        """

    class ProgressScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CProgress
                #c-key="item"
                c-label="f'Task {item}'"
                c-value="item % 101"
              />
            </c-for>
          </div>
        """

    class SpinnerScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CSpinner #c-key="item" c-label="f'Task {item}'" />
            </c-for>
          </div>
        """

    class RadioScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <c-CRadioGroup name="scale-radio">
            <c-fill name="label">Scale choices</c-fill>
            <c-fill name="default">
              <c-for each="item in items">
                <c-CRadio #c-key="item" c-value="f'choice-{item}'">Choice {{ item }}</c-CRadio>
              </c-for>
            </c-fill>
          </c-CRadioGroup>
        """

    class SkeletonScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CSkeleton #c-key="item" kind="text" c-lines="3" />
            </c-for>
          </div>
        """

    class SwitchScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CSwitch #c-key="item" c-name="f'setting-{item}'">
                Setting {{ item }}
              </c-CSwitch>
            </c-for>
          </div>
        """

    class BreadcrumbsScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "items": tuple(
                    citry_ui.CBreadcrumbItem(f"Level {item}", f"/level/{item}")
                    if item < kwargs.count - 1
                    else citry_ui.CBreadcrumbItem(f"Level {item}")
                    for item in range(kwargs.count)
                )
            }

        template = '<c-CBreadcrumbs c-items="items" label="Scale location" />'

    class TableScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "columns": (
                    citry_ui.CTableColumn("id", "ID", row_header=True),
                    citry_ui.CTableColumn("value", "Value"),
                ),
                "rows": tuple(
                    citry_ui.CTableRow(str(index), {"id": index, "value": f"Row {index}"})
                    for index in range(kwargs.count)
                ),
            }

        template = """
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            density="compact"
          />
        """

    class IconScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CIcon #c-key="item" name="leaf" />
            </c-for>
          </div>
        """

    class CardScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CCard #c-key="item" variant="outline" size="sm">
                Card {{ item }}
              </c-CCard>
            </c-for>
          </div>
        """

    class TextareaScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CTextarea
                #c-key="item"
                c-id="f'cui-scale-textarea-{item}'"
                rows="2"
              />
            </c-for>
          </div>
        """

    class NativeSelectScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "items": tuple(range(kwargs.count)),
                "options": (
                    citry_ui.CNativeSelectOption("reef", "Coral reef"),
                    citry_ui.CNativeSelectOption("kelp", "Kelp forest"),
                    citry_ui.CNativeSelectOption("pelagic", "Pelagic zone"),
                ),
            }

        template = """
          <div>
            <c-for each="item in items">
              <c-CNativeSelect
                #c-key="item"
                c-id="f'cui-scale-native-select-{item}'"
                c-options="options"
              />
            </c-for>
          </div>
        """

    class CheckboxScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CCheckbox
                #c-key="item"
                c-id="f'cui-scale-checkbox-{item}'"
              >
                Choice {{ item }}
              </c-CCheckbox>
            </c-for>
          </div>
        """

    class FlowScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <c-CStack>
            <c-for each="item in items">
              <c-CGroup #c-key="item">
                <span>Label {{ item }}</span>
                <span>Value {{ item }}</span>
              </c-CGroup>
            </c-for>
          </c-CStack>
        """

    class GridScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CGrid #c-key="item" cols="3">
                <span>Quartz {{ item }}</span>
                <span>Calcite {{ item }}</span>
                <span>Olivine {{ item }}</span>
              </c-CGrid>
            </c-for>
          </div>
        """

    class ButtonGroupScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CButtonGroup #c-key="item" c-label="f'Actions {item}'">
                <c-CButton variant="outline">Previous</c-CButton>
                <c-CButton variant="outline">Next</c-CButton>
              </c-CButtonGroup>
            </c-for>
          </div>
        """

    class ToggleScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <c-CToggleGroup label="Scale Toggles">
            <c-for each="item in items">
              <c-CToggle #c-key="item" c-value="f'toggle-{item}'">
                Toggle {{ item }}
              </c-CToggle>
            </c-for>
          </c-CToggleGroup>
        """

    class PaginationScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CPagination
                #c-key="item"
                c-label="f'Pages {item}'"
                c-page="51"
                c-pages="100"
              />
            </c-for>
          </div>
        """

    class ListScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <c-CList label="Scale list">
            <c-for each="item in items">
              <c-CListItem #c-key="item">Item {{ item }}</c-CListItem>
            </c-for>
          </c-CList>
        """

    class PopoverScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CPopover
                #c-key="item"
                c-id="f'cui-scale-popover-{item}'"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">
                    Open {{ item }}
                  </c-CButton>
                </c-fill>
                <c-fill name="title">Popover {{ item }}</c-fill>
                <c-fill name="default">Body {{ item }}</c-fill>
              </c-CPopover>
            </c-for>
          </div>
        """

    class TooltipScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CTooltip
                #c-key="item"
                c-id="f'cui-scale-tooltip-{item}'"
                c-text="f'Description {item}'"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">
                    Target {{ item }}
                  </c-CButton>
                </c-fill>
              </c-CTooltip>
            </c-for>
          </div>
        """

    class DrawerScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CDrawer
                #c-key="item"
                c-id="f'cui-scale-drawer-{item}'"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open {{ item }}</c-CButton>
                </c-fill>
                <c-fill name="title">Drawer {{ item }}</c-fill>
                <c-fill name="default">Body {{ item }}</c-fill>
              </c-CDrawer>
            </c-for>
          </div>
        """

    class ToastScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "items": tuple(
                    citry_ui.CToastMessage(
                        id=f"cui-scale-toast-{item}",
                        title=f"Notification {item}",
                        description="Bounded queue scaling message.",
                    )
                    for item in range(kwargs.count)
                )
            }

        template = """
          <c-CToastRegion c-items="items" c-duration_ms="0" />
        """

    class MenuScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CMenu
                #c-key="item"
                c-id="f'cui-scale-menu-{item}'"
              >
                <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                  <c-CButton
                    c-disabled="activator_disabled"
                    c-attrs="activator_attrs"
                  >Open {{ item }}</c-CButton>
                </c-fill>
                <c-fill name="default">
                  <c-CMenuItem c-value="f'action-{item}'">Action {{ item }}</c-CMenuItem>
                </c-fill>
              </c-CMenu>
            </c-for>
          </div>
        """

    results: list[ScalingSample] = []
    # Mypy does not apply ComponentMeta.__call__ to concrete component classes,
    # while Pyright correctly sees the composition call. Use the metaclass's
    # real callable shape locally so this diagnostic can keep normal public
    # component composition without suppressing individual constructor calls.
    accordion_element = cast("Callable[..., object]", AccordionScale)
    disclosure_element = cast("Callable[..., object]", DisclosureScale)
    alert_element = cast("Callable[..., object]", AlertScale)
    button_element = cast("Callable[..., object]", ButtonScale)
    avatar_element = cast("Callable[..., object]", AvatarScale)
    badge_element = cast("Callable[..., object]", BadgeScale)
    divider_element = cast("Callable[..., object]", DividerScale)
    progress_element = cast("Callable[..., object]", ProgressScale)
    spinner_element = cast("Callable[..., object]", SpinnerScale)
    radio_element = cast("Callable[..., object]", RadioScale)
    skeleton_element = cast("Callable[..., object]", SkeletonScale)
    switch_element = cast("Callable[..., object]", SwitchScale)
    breadcrumbs_element = cast("Callable[..., object]", BreadcrumbsScale)
    table_element = cast("Callable[..., object]", TableScale)
    icon_element = cast("Callable[..., object]", IconScale)
    card_element = cast("Callable[..., object]", CardScale)
    textarea_element = cast("Callable[..., object]", TextareaScale)
    native_select_element = cast("Callable[..., object]", NativeSelectScale)
    checkbox_element = cast("Callable[..., object]", CheckboxScale)
    flow_element = cast("Callable[..., object]", FlowScale)
    grid_element = cast("Callable[..., object]", GridScale)
    button_group_element = cast("Callable[..., object]", ButtonGroupScale)
    toggle_element = cast("Callable[..., object]", ToggleScale)
    pagination_element = cast("Callable[..., object]", PaginationScale)
    list_element = cast("Callable[..., object]", ListScale)
    popover_element = cast("Callable[..., object]", PopoverScale)
    drawer_element = cast("Callable[..., object]", DrawerScale)
    toast_element = cast("Callable[..., object]", ToastScale)
    tooltip_element = cast("Callable[..., object]", TooltipScale)
    menu_element = cast("Callable[..., object]", MenuScale)
    for count in counts:
        median_ms, output_bytes = _measure(partial(_render_scaled, accordion_element, count), samples=samples)
        results.append(ScalingSample("accordion-items", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, disclosure_element, count), samples=samples)
        results.append(ScalingSample("disclosure-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, alert_element, count), samples=samples)
        results.append(ScalingSample("alert-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, button_element, count), samples=samples)
        results.append(ScalingSample("button-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, avatar_element, count), samples=samples)
        results.append(ScalingSample("avatar-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, badge_element, count), samples=samples)
        results.append(ScalingSample("badge-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, divider_element, count), samples=samples)
        results.append(ScalingSample("divider-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, progress_element, count), samples=samples)
        results.append(ScalingSample("progress-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, spinner_element, count), samples=samples)
        results.append(ScalingSample("spinner-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, radio_element, count), samples=samples)
        results.append(ScalingSample("radio-items", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, skeleton_element, count), samples=samples)
        results.append(ScalingSample("skeleton-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, switch_element, count), samples=samples)
        results.append(ScalingSample("switch-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, breadcrumbs_element, count), samples=samples)
        results.append(ScalingSample("breadcrumbs-items", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, table_element, count), samples=samples)
        results.append(ScalingSample("table-rows", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, icon_element, count), samples=samples)
        results.append(ScalingSample("icon-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, card_element, count), samples=samples)
        results.append(ScalingSample("card-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, textarea_element, count), samples=samples)
        results.append(ScalingSample("textarea-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, native_select_element, count), samples=samples)
        results.append(ScalingSample("native-select-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, checkbox_element, count), samples=samples)
        results.append(ScalingSample("checkbox-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, flow_element, count), samples=samples)
        results.append(ScalingSample("flow-groups", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, grid_element, count), samples=samples)
        results.append(ScalingSample("grid-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, button_group_element, count), samples=samples)
        results.append(ScalingSample("button-group-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, toggle_element, count), samples=samples)
        results.append(ScalingSample("toggle-items", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, pagination_element, count), samples=samples)
        results.append(ScalingSample("pagination-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, list_element, count), samples=samples)
        results.append(ScalingSample("list-items", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, popover_element, count), samples=samples)
        results.append(ScalingSample("popover-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, drawer_element, count), samples=samples)
        results.append(ScalingSample("drawer-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, toast_element, count), samples=samples)
        results.append(ScalingSample("toast-queued-items", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, tooltip_element, count), samples=samples)
        results.append(ScalingSample("tooltip-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, menu_element, count), samples=samples)
        results.append(ScalingSample("menu-instances", count, round(median_ms, 3), output_bytes))
    return {
        "schema": "citry-ui-scaling-report/v1",
        "samples_per_count": samples,
        "results": [asdict(result) for result in results],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure bounded Citry UI scaling profiles.")
    parser.add_argument("--counts", default="1,10,100,500,1000")
    parser.add_argument("--samples", type=int, default=3)
    args = parser.parse_args()
    try:
        counts = tuple(int(value) for value in args.counts.split(","))
        report = scaling_report(counts=counts, samples=args.samples)
    except ValueError as error:
        parser.exit(1, f"citry-ui scaling profile failed: {error}\n")
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
