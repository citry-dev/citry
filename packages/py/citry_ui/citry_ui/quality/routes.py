"""Render complete standalone pages from ready Citry UI scenarios."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

import citry_ui
from citry import Citry, Component, DepsStrategy
from citry._vue.events import definition_bundle, style_asset
from citry.ext.dependencies.emission import _runtime_js
from citry.ext.dependencies.routes import RUNTIME_PATH
from citry.ext.dependencies.types import Script, Style
from citry.ext.events.routes import RUNTIME_PATH as EVENTS_RUNTIME_PATH
from citry.ext.i18n.emission import RUNTIME_PATH as I18N_RUNTIME_PATH
from citry.ext.i18n.emission import client_runtime_js
from citry.util.html import script_json
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

    from citry.citry_element import CitryElement

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


def _scenario_app() -> Citry:
    # Citry's default delivery writes each page's content into the served
    # HTML, so a scenario viewed without JavaScript still shows its fallback.
    app = Citry(secret="citry-ui-quality-scenarios", autodiscover=False)  # noqa: S106
    app.register_library(citry_ui)
    return app


# The serializer writes the browser configuration as one JSON data block that
# the start script reads by app id.
_DOCUMENT_CONFIGURATION_RE = re.compile(
    r'<script type="application/json" data-citry-vue-document="(?P<app>[^"]*)"[^>]*>(?P<json>.*?)</script>',
    re.DOTALL,
)
_SCRIPT_SRC_TAG_RE = re.compile(r'<script\b[^>]*\bsrc="(?P<src>[^"]*)"[^>]*></script>')
_LINK_TAG_RE = re.compile(r"<link\b[^>]*>")
_HREF_RE = re.compile(r'\bhref="(?P<href>[^"]*)"')


def _host_runtime_sources(app: Citry) -> dict[str, str]:
    """Map each runtime URL a mounted page may load to the text served there."""
    # Both runtime routes serve the same generated Vue runtime file, and the
    # i18n route serves its own plugin bundle.
    return {
        app.build_url(RUNTIME_PATH): _runtime_js(),
        app.build_url(EVENTS_RUNTIME_PATH): _runtime_js(),
        app.build_url(I18N_RUNTIME_PATH): client_runtime_js(),
    }


# Keep standalone asset materialization local to the quality harness.
def _inline_prepared_assets(html: str, app: Citry) -> str:
    """
    Write a mounted page's browser assets into the page itself.

    A mounted page loads its runtime, component definitions, and stylesheets
    from the host's `/citry/...` routes. A scenario file opened without that
    host would load none of them, so this replaces each of those tags with
    the same content inline and tells the runtime not to fetch them again.
    The Events transport URLs in the configuration stay pointed at the host.

    Raises:
        RuntimeError: A retained asset is missing, or the page still
            references a host asset that this function cannot inline.

    """
    match = _DOCUMENT_CONFIGURATION_RE.search(html)
    # A page without Vue components has no configuration and no host assets.
    if match is None:
        return html

    app_id = match.group("app")
    configuration = json.loads(match.group("json"))
    manifest = configuration["manifest"]
    # The definitions and stylesheets below are already in the page, so the
    # runtime adopts them instead of requesting them from the host.
    configuration["loadInitialAssets"] = False

    # The same order the standalone serializer uses: definitions first, then
    # the owned or external scripts the manifest lists.
    scripts: list[str] = []
    for digest in dict.fromkeys(item["sha256"] for item in manifest["definitions"]):
        bundle = definition_bundle(app, digest)
        if bundle is None:
            raise RuntimeError("A prepared Vue definition bundle was not retained for standalone rendering.")
        scripts.append(str(Script(kind="core", content=bundle.decode()).render()))
    emitted_script_sources: set[str] = set()
    for asset in manifest["scripts"]:
        source = asset["source"]
        # One source can back several manifest entries; write it only once.
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
        # The runtime finds an adopted stylesheet by these two attributes.
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

    prefix = app.build_url("")
    runtime_sources = _host_runtime_sources(app)
    i18n_runtime_url = app.build_url(I18N_RUNTIME_PATH)
    definitions_written = False

    def inline_runtime(tag: re.Match[str]) -> str:
        nonlocal definitions_written
        src = tag.group("src")
        # Scripts from other origins keep working without the host.
        if not src.startswith(prefix):
            return tag.group(0)
        content = runtime_sources.get(src)
        if content is None:
            msg = f"A mounted quality scenario loads {src!r}, which standalone rendering cannot inline."
            raise RuntimeError(msg)
        inline = str(Script(kind="core", content=content, wrap=False).render())
        # The definitions register with the runtime, so they go right after
        # the first runtime script, before any plugin or start script.
        if not definitions_written and src != i18n_runtime_url:
            definitions_written = True
            return inline + "".join(scripts)
        return inline

    def drop_host_link(tag: re.Match[str]) -> str:
        href = _HREF_RE.search(tag.group(0))
        # Preload hints and stylesheet links for host assets would request
        # routes that do not exist; the inline copies replace them.
        if href is not None and href.group("href").startswith(prefix):
            return ""
        return tag.group(0)

    # The configuration keeps its position; only the flag above changes.
    serialized = script_json(configuration, sort_keys=True)
    html = html[: match.start("json")] + serialized + html[match.end("json") :]
    html = _SCRIPT_SRC_TAG_RE.sub(inline_runtime, html)
    if not definitions_written:
        raise RuntimeError("A mounted quality scenario did not emit its Citry runtime script.")
    html = _LINK_TAG_RE.sub(drop_host_link, html)
    html = html.replace("</head>", "".join(styles) + "</head>", 1)
    # Fail here rather than ship a page that silently misses an asset.
    if re.search(rf'(?:src|href)="{re.escape(prefix)}', html) is not None:
        raise RuntimeError("A standalone quality scenario still references a host asset route.")
    return html


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
    the default suitable for host routes and Lighthouse.

    Args:
        scenario_id: The ready scenario to render.
        configure_app: A callback that configures the scenario's Citry
            instance before the page renders.
        self_contained: Write the prepared browser assets into the page, so
            a document opened without the host still runs. The Events
            transport URLs stay pointed at the host.
        deps_strategy: The serializer to use. Tests and no-JavaScript
            previews can select the public static serializer.

    """
    scenario = scenario_by_id(scenario_id)
    if scenario.status is not ScenarioStatus.READY:
        msg = f"Citry UI scenario {scenario_id!r} is {scenario.status.value}; no route is available yet."
        raise RuntimeError(msg)
    factory = _SCENARIO_FACTORIES.get(scenario_id)
    if factory is None:
        msg = f"No renderer is registered for ready scenario {scenario_id!r}."
        raise RuntimeError(msg)

    app = _scenario_app()
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

    page = cast("CitryElement", ScenarioPage())
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
    """
    Render a ready scenario as a component fragment or complete page.

    Args:
        scenario_id: The ready scenario to render.
        embedded: Return only the scenario component instead of a page.
        deps_strategy: The serializer to use for the rendered output.

    """
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
    app = _scenario_app()
    app.set_mounted_prefix("/citry")
    component = cast("CitryElement", factory(app)())
    return component.render().serialize(deps_strategy=deps_strategy)


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
