"""Render complete standalone pages from ready Citry UI scenarios."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import citry_ui
from citry import Citry, Component, DepsStrategy
from citry_ui.components.caccordion.quality.scenario import accordion_states_component
from citry_ui.components.calert.quality.scenario import alert_states_component
from citry_ui.components.calert_dialog.quality.scenario import alert_dialog_states_component
from citry_ui.components.cavatar.quality.scenario import avatar_states_component
from citry_ui.components.cbadge.quality.scenario import badge_states_component
from citry_ui.components.cbreadcrumbs.quality.scenario import breadcrumbs_states_component
from citry_ui.components.cbutton.quality.scenario import button_states_component
from citry_ui.components.cbutton_group.quality.scenario import button_group_states_component
from citry_ui.components.ccalendar.quality.scenario import calendar_states_component
from citry_ui.components.ccard.quality.scenario import card_states_component
from citry_ui.components.ccarousel.quality.scenario import carousel_states_component
from citry_ui.components.ccascader.quality.scenario import cascader_states_component
from citry_ui.components.ccheckbox.quality.scenario import checkbox_states_component
from citry_ui.components.ccolor_picker.quality.scenario import color_picker_states_component
from citry_ui.components.ccombobox.quality.scenario import combobox_states_component
from citry_ui.components.ccommand_palette.quality.scenario import command_palette_states_component
from citry_ui.components.ccontext_menu.quality.scenario import context_menu_states_component
from citry_ui.components.cdata_grid.quality.scenario import data_grid_states_component
from citry_ui.components.cdate_input.quality.scenario import date_input_states_component
from citry_ui.components.cdate_picker.quality.scenario import date_picker_states_component
from citry_ui.components.cdate_range.quality.scenario import date_range_states_component
from citry_ui.components.cdialog.quality.scenario import dialog_states_component
from citry_ui.components.cdisclosure.quality.scenario import disclosure_states_component
from citry_ui.components.cdivider.quality.scenario import divider_states_component
from citry_ui.components.cdrawer.quality.scenario import drawer_states_component
from citry_ui.components.ceditable.quality.scenario import editable_states_component
from citry_ui.components.cfield.quality.scenario import field_input_states_component
from citry_ui.components.cfile_input.quality.scenario import file_input_states_component
from citry_ui.components.cflow.quality.scenario import flow_states_component
from citry_ui.components.cform.quality.scenario import form_states_component
from citry_ui.components.cform_collection.quality.scenario import form_collection_states_component
from citry_ui.components.cgrid.quality.scenario import grid_container_states_component
from citry_ui.components.chover_card.quality.scenario import hover_card_states_component
from citry_ui.components.cicon.quality.scenario import icon_states_component
from citry_ui.components.cimage.quality.scenario import image_states_component
from citry_ui.components.cinfinite_scroll.quality.scenario import infinite_scroll_states_component
from citry_ui.components.clist.quality.scenario import list_states_component
from citry_ui.components.clistbox.quality.scenario import listbox_states_component
from citry_ui.components.cmenu.quality.scenario import menu_states_component
from citry_ui.components.cmulti_select.quality.scenario import multi_select_states_component
from citry_ui.components.cnative_select.quality.scenario import native_select_states_component
from citry_ui.components.cnavigation_menu.quality.scenario import navigation_menu_states_component
from citry_ui.components.cnumber_input.quality.scenario import number_input_states_component
from citry_ui.components.cpagination.quality.scenario import pagination_states_component
from citry_ui.components.cpin_input.quality.scenario import pin_input_states_component
from citry_ui.components.cpopover.quality.scenario import popover_states_component
from citry_ui.components.cprogress.quality.scenario import progress_states_component
from citry_ui.components.cradio.quality.scenario import radio_states_component
from citry_ui.components.crating.quality.scenario import rating_states_component
from citry_ui.components.cscroll_area.quality.scenario import scroll_area_states_component
from citry_ui.components.cselect.quality.scenario import select_states_component
from citry_ui.components.csidebar.quality.scenario import sidebar_states_component
from citry_ui.components.cskeleton.quality.scenario import skeleton_states_component
from citry_ui.components.cslider.quality.scenario import slider_states_component
from citry_ui.components.csortable.quality.scenario import sortable_states_component
from citry_ui.components.cspinner.quality.scenario import spinner_states_component
from citry_ui.components.csplitbutton.quality.scenario import split_button_states_component
from citry_ui.components.csplitter.quality.scenario import splitter_states_component
from citry_ui.components.cstepper.quality.scenario import stepper_states_component
from citry_ui.components.cswitch.quality.scenario import switch_states_component
from citry_ui.components.ctable.quality.scenario import table_states_component
from citry_ui.components.ctabs.quality.scenario import tabs_overview_component
from citry_ui.components.ctag.quality.scenario import tag_states_component
from citry_ui.components.ctags_input.quality.scenario import tags_input_states_component
from citry_ui.components.ctextarea.quality.scenario import textarea_states_component
from citry_ui.components.ctime_picker.quality.scenario import time_states_component
from citry_ui.components.ctimeline.quality.scenario import timeline_states_component
from citry_ui.components.ctoast.quality.scenario import toast_states_component
from citry_ui.components.ctoggle.quality.scenario import toggle_states_component
from citry_ui.components.ctoolbar.quality.scenario import toolbar_states_component
from citry_ui.components.ctooltip.quality.scenario import tooltip_states_component
from citry_ui.components.ctour.quality.scenario import tour_states_component
from citry_ui.components.ctransfer_list.quality.scenario import transfer_list_states_component
from citry_ui.components.ctree.quality.scenario import tree_states_component
from citry_ui.components.ctree_grid.quality.scenario import tree_grid_states_component
from citry_ui.components.cvirtual_list.quality.scenario import virtual_list_states_component
from citry_ui.quality.compositions import (
    ledger_dashboard_component,
    orbit_access_component,
    repeatable_contacts_component,
)
from citry_ui.quality.scenarios import Scenario, ScenarioStatus, scenario_by_id

if TYPE_CHECKING:
    from collections.abc import Callable

_SCENARIO_FACTORIES = {
    "accordion.states": accordion_states_component,
    "disclosure.states": disclosure_states_component,
    "alert.states": alert_states_component,
    "button.states": button_states_component,
    "split-button.states": split_button_states_component,
    "avatar.states": avatar_states_component,
    "image.states": image_states_component,
    "badge.states": badge_states_component,
    "divider.states": divider_states_component,
    "field-input.states": field_input_states_component,
    "file-input.states": file_input_states_component,
    "progress.states": progress_states_component,
    "spinner.states": spinner_states_component,
    "splitter.states": splitter_states_component,
    "stepper.states": stepper_states_component,
    "sidebar.states": sidebar_states_component,
    "flow.states": flow_states_component,
    "grid-container.states": grid_container_states_component,
    "scroll-area.states": scroll_area_states_component,
    "radio.states": radio_states_component,
    "skeleton.states": skeleton_states_component,
    "switch.states": switch_states_component,
    "breadcrumbs.states": breadcrumbs_states_component,
    "form.states": form_states_component,
    "textarea.states": textarea_states_component,
    "native-select.states": native_select_states_component,
    "checkbox.states": checkbox_states_component,
    "tabs.overview": tabs_overview_component,
    "dialog.states": dialog_states_component,
    "alert-dialog.states": alert_dialog_states_component,
    "popover.states": popover_states_component,
    "drawer.states": drawer_states_component,
    "tour.states": tour_states_component,
    "tooltip.states": tooltip_states_component,
    "hover-card.states": hover_card_states_component,
    "menu.states": menu_states_component,
    "context-menu.states": context_menu_states_component,
    "navigation-menu.states": navigation_menu_states_component,
    "carousel.states": carousel_states_component,
    "toast.states": toast_states_component,
    "combobox.states": combobox_states_component,
    "command-palette.states": command_palette_states_component,
    "table.states": table_states_component,
    "icon.states": icon_states_component,
    "card.states": card_states_component,
    "button-group.states": button_group_states_component,
    "toggle.states": toggle_states_component,
    "pagination.states": pagination_states_component,
    "list.states": list_states_component,
    "data-grid.states": data_grid_states_component,
    "timeline.states": timeline_states_component,
    "transfer-list.states": transfer_list_states_component,
    "form-collection.states": form_collection_states_component,
    "sortable.states": sortable_states_component,
    "infinite-scroll.states": infinite_scroll_states_component,
    "cascader.states": cascader_states_component,
    "tree-grid.states": tree_grid_states_component,
    "color-picker.states": color_picker_states_component,
    "virtual-list.states": virtual_list_states_component,
    "tag.states": tag_states_component,
    "toolbar.states": toolbar_states_component,
    "listbox.states": listbox_states_component,
    "select.states": select_states_component,
    "multi-select.states": multi_select_states_component,
    "tags-input.states": tags_input_states_component,
    "number-input.states": number_input_states_component,
    "slider.states": slider_states_component,
    "rating.states": rating_states_component,
    "pin-input.states": pin_input_states_component,
    "date-input.states": date_input_states_component,
    "calendar.states": calendar_states_component,
    "date-picker.states": date_picker_states_component,
    "date-range.states": date_range_states_component,
    "time.states": time_states_component,
    "editable.states": editable_states_component,
    "tree.states": tree_states_component,
    "workflow.repeatable-contacts": repeatable_contacts_component,
    "composition.orbit-access": orbit_access_component,
    "composition.ledger-dashboard": ledger_dashboard_component,
}

# Standalone quality pages are also audited outside a mounted host. Keep the
# page self-contained so the browser does not probe the host root for a
# favicon during the Lighthouse run.
_PAGE_FAVICON_DATA_URI = (
    "data:image/svg+xml;base64,"
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxIDEiPjxwYXRoIGZpbGw9IiMwMDAiIGQ9Ik0wIDBoMXYxSDB6Ii8+PC9zdmc+"
)

_PAGE_CSS = """
  :where(html) {
    color-scheme: light dark;
    background: Canvas;
    color: CanvasText;
    font-family: ui-sans-serif, system-ui, sans-serif;
  }

  :where(body) {
    margin: 0;
  }

  :where(main) {
    box-sizing: border-box;
    inline-size: min(100%, 72rem);
    margin-inline: auto;
    padding: 2rem;
  }

  :where(.citry-ui-quality-stack) {
    display: grid;
    gap: 1rem;
  }

  :where(.citry-ui-quality-grid) {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
    gap: 1rem;
    align-items: start;
  }

  :where(.citry-ui-quality-grid > h1) {
    grid-column: 1 / -1;
  }
"""


def renderable_scenario_ids() -> tuple[str, ...]:
    """Return scenario IDs that have a registered standalone renderer."""
    return tuple(_SCENARIO_FACTORIES)


@dataclass(frozen=True, slots=True)
class RenderedScenario:
    """One complete scenario document and the Citry instance that owns it."""

    scenario: Scenario
    app: Citry
    html: str


_PREPARED_BOOTSTRAP_RE = re.compile(r"CitryStable\.startPrepared\((\{.*\})\)\.catch", re.DOTALL)


# Keep standalone asset materialization local to the quality harness.
def _inline_prepared_assets(html: str, app: Citry) -> str:
    """Inline mounted Vue assets while retaining the host transport URLs."""
    match = _PREPARED_BOOTSTRAP_RE.search(html)
    if match is None:
        return html

    configuration = json.loads(match.group(1))
    manifest = configuration["manifest"]
    app_id = manifest["appId"]
    configuration["loadInitialAssets"] = False

    from citry._vue.events import definition_bundle, style_asset  # noqa: PLC0415
    from citry.ext.dependencies.emission import _runtime_js  # noqa: PLC0415
    from citry.ext.dependencies.types import Script, Style  # noqa: PLC0415

    runtime_url = app.build_url("citry.js")
    runtime_tag = str(Script(kind="core", content=_runtime_js(), wrap=False).render())
    expected_runtime_tag = f'<script src="{runtime_url}"></script>'
    if expected_runtime_tag not in html:
        raise RuntimeError("A mounted quality scenario did not emit its expected Citry runtime tag.")
    html = html.replace(expected_runtime_tag, runtime_tag, 1)

    scripts: list[str] = []
    emitted_script_sources: set[str] = set()
    for digest in dict.fromkeys(item["sha256"] for item in manifest["definitions"]):
        bundle = definition_bundle(app, digest)
        if bundle is None:
            raise RuntimeError("A prepared Vue definition bundle was not retained for standalone rendering.")
        scripts.append(str(Script(kind="core", content=bundle.decode()).render()))
    for asset in manifest["scripts"]:
        source = asset["source"]
        source_identity = json.dumps(source, allow_nan=False, separators=(",", ":"), sort_keys=True)
        if source_identity in emitted_script_sources:
            continue
        emitted_script_sources.add(source_identity)
        attrs = dict(source.get("attrs", {}))
        if source["kind"] == "owned":
            bundle = definition_bundle(app, source["sha256"])
            if bundle is None:
                raise RuntimeError("A prepared Vue script asset was not retained for standalone rendering.")
            scripts.append(str(Script(kind="core", content=bundle.decode(), attrs=attrs).render()))
        else:
            scripts.append(str(Script(kind="core", url=source["url"], attrs=attrs).render()))

    styles: list[str] = []
    emitted_style_sources: set[str] = set()
    for asset in manifest["styles"]:
        source = asset["source"]
        source_identity = json.dumps(source, allow_nan=False, separators=(",", ":"), sort_keys=True)
        if source_identity in emitted_style_sources:
            continue
        emitted_style_sources.add(source_identity)
        attrs = dict(source.get("attrs", {}))
        attrs["data-citry-css-url"] = source["url"]
        attrs["data-citry-vue-style-app"] = app_id
        if source["kind"] == "owned":
            body = style_asset(app, source["sha256"])
            if body is None:
                raise RuntimeError("A prepared Vue stylesheet was not retained for standalone rendering.")
            styles.append(str(Style(kind="core", content=body.decode(), attrs=attrs).render()))
        else:
            styles.append(str(Style(kind="core", url=source["url"], attrs=attrs).render()))

    html = html.replace("</head>", "".join(styles) + "</head>", 1)
    match = _PREPARED_BOOTSTRAP_RE.search(html)
    if match is None:  # pragma: no cover - the first match remains after tag insertion
        raise RuntimeError("A prepared quality scenario bootstrap disappeared during standalone rendering.")
    serialized = json.dumps(configuration, allow_nan=False, separators=(",", ":"), sort_keys=True).replace(
        "<", "\\u003c"
    )
    html = html[: match.start(1)] + serialized + html[match.end(1) :]
    bootstrap = "<script>(function() {\nCitryStable.startPrepared("
    bootstrap_index = html.find(bootstrap)
    if bootstrap_index < 0:  # pragma: no cover - every matched bootstrap has this framing
        raise RuntimeError("A prepared quality scenario bootstrap has an unexpected wrapper.")
    return html[:bootstrap_index] + "".join(scripts) + html[bootstrap_index:]


def build_scenario(
    scenario_id: str,
    *,
    configure_app: Callable[[Citry], None] | None = None,
    self_contained: bool = False,
    deps_strategy: DepsStrategy = "document",
) -> RenderedScenario:
    """
    Build a complete scenario after an optional host configures Citry.

    The app uses ``/citry`` when the host has not configured a prefix, keeping
    the default suitable for host routes and Lighthouse.  ``self_contained``
    inlines prepared browser assets for documents loaded without that host,
    while retaining the mounted Events transport URLs. ``deps_strategy`` can
    select the public static serializer for tests and no-JavaScript previews.
    """
    scenario = scenario_by_id(scenario_id)
    if scenario.status is not ScenarioStatus.READY:
        msg = f"Citry UI scenario {scenario_id!r} is {scenario.status.value}; no route is available yet."
        raise RuntimeError(msg)
    factory = _SCENARIO_FACTORIES.get(scenario_id)
    if factory is None:
        msg = f"No renderer is registered for ready scenario {scenario_id!r}."
        raise RuntimeError(msg)

    app = Citry(secret="citry-ui-quality-scenarios", autodiscover=False)  # noqa: S106
    app.register_library(citry_ui)
    if configure_app is not None:
        configure_app(app)
    if app.mounted_prefix is None:
        # Host-route and Lighthouse pages need a deterministic asset base when
        # no host has supplied one explicitly.
        app.set_mounted_prefix("/citry")
    scenario_component = factory(app)

    class ScenarioPage(Component):
        citry = app
        css = _PAGE_CSS

        class Kwargs:
            pass

        class Slots:
            pass

        template = f"""
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <meta name="color-scheme" content="light dark" />
              <link rel="icon" href="{_PAGE_FAVICON_DATA_URI}" />
              <title>{{{{ page_title }}}}</title>
              <c-css />
            </head>
            <body data-citry-ui-scenario="{scenario.id}">
              <main id="main-content">
                <c-{scenario_component.__name__} />
              </main>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"page_title": f"{scenario.purpose} | Citry UI quality"}

    page = ScenarioPage()
    html = page.render().serialize(deps_strategy=deps_strategy)
    if self_contained and deps_strategy == "document":
        html = _inline_prepared_assets(html, app)
    return RenderedScenario(scenario=scenario, app=app, html=html)


def render_scenario(
    scenario_id: str,
    *,
    embedded: bool = False,
    deps_strategy: DepsStrategy = "document",
) -> str:
    """Render a ready scenario as a component fragment or complete page."""
    if not embedded:
        return build_scenario(scenario_id, self_contained=True, deps_strategy=deps_strategy).html

    scenario = scenario_by_id(scenario_id)
    if scenario.status is not ScenarioStatus.READY:
        msg = f"Citry UI scenario {scenario_id!r} is {scenario.status.value}; no route is available yet."
        raise RuntimeError(msg)
    factory = _SCENARIO_FACTORIES.get(scenario_id)
    if factory is None:
        msg = f"No renderer is registered for ready scenario {scenario_id!r}."
        raise RuntimeError(msg)
    app = Citry(secret="citry-ui-quality-scenarios", autodiscover=False)  # noqa: S106
    app.register_library(citry_ui)
    app.set_mounted_prefix("/citry")
    return factory(app)().render().serialize(deps_strategy=deps_strategy)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a ready Citry UI quality scenario.")
    parser.add_argument("scenario_id")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--embedded", action="store_true")
    args = parser.parse_args()

    html = render_scenario(args.scenario_id, embedded=args.embedded)
    if args.output is None:
        sys.stdout.write(html + "\n")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(html, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
