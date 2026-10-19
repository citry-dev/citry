"""Serve the shared project board through ReactPy's supported Starlette backend."""

# Resolve the copied scenario before importing its deterministic model.
# ruff: noqa: E402, I001

import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from urllib.parse import parse_qs

# Set production options before ReactPy reads the parent process environment.
for option in (
    "REACTPY_DEBUG_MODE",
    "REACTPY_ASYNC_RENDERING",
    "REACTPY_CHECK_VDOM_SPEC",
    "REACTPY_CHECK_JSON_ATTRS",
):
    os.environ[option] = "false"
_module_directory = TemporaryDirectory(prefix="reactpy-modules-", dir=os.environ.get("CITRY_BENCH_RUNTIME_DIR"))
os.environ["REACTPY_WEB_MODULES_DIR"] = _module_directory.name

HERE = Path(__file__).parent
SCENARIO = HERE / "scenario"
if not SCENARIO.is_dir():
    SCENARIO = HERE.parents[1] / "scenarios" / "project_board"
sys.path.insert(0, str(SCENARIO))

from audit import ObserveTransport, accepted, install_preparation_timing, records, report
from reactpy import component, event, hooks, html, use_location, web
from reactpy.backend import starlette
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route

from model import ActionInput, apply, reset, snapshot

install_preparation_timing()

disclosure_module = web.module_from_file("board-disclosure", HERE / "assets" / "disclosure.js")
LocalDisclosure = web.export(disclosure_module, "LocalDisclosure")


@component
def action_form(
    act: Any,
    action: str,
    label: str,
    *children: Any,
    row_id: int = 0,
    input_name: str = "",
) -> Any:
    def submit(event_data: dict[str, Any]) -> None:
        act(action, row_id, input_name, event_data)

    return html.form(
        {
            "on_submit": event(submit, prevent_default=True),
            "no_validate": True,
            "class_name": "output-form" if row_id else "",
        },
        html.input({"type": "hidden", "name": "operation", "default_value": "manual"}),
        *children,
        html.button(
            {"type": "submit", "data-bench-action": f"select-{row_id}" if row_id else action},
            label,
        ),
    )


@component
def project_navbar(data: dict[str, Any]) -> Any:
    return html.nav(
        {"id": "project-navbar", "aria-label": "Primary"},
        html.a({"href": "#board"}, "Projects"),
        html.span({"aria-current": "page"}, data["project"]["name"]),
    )


@component
def project_sidebar(data: dict[str, Any]) -> Any:
    return html.aside(
        {"id": "project-sidebar"},
        html.section(
            {"aria-labelledby": "bookmark-heading"},
            html.h2({"id": "bookmark-heading"}, "Project Bookmarks"),
            *[
                html.a(
                    {
                        "key": bookmark["id"],
                        "data-bookmark-id": bookmark["id"],
                        "data-bookmark-name": bookmark["text"],
                        "href": bookmark["url"],
                    },
                    html.span({"class_name": "bookmark-name"}, bookmark["text"]),
                )
                for bookmark in data["bookmarks"]
            ],
        ),
        html.nav(
            {"aria-label": "Project phases"},
            html.h2("Phases"),
            html.ul(
                *[
                    html.li(
                        {"key": phase["id"]},
                        html.a({"href": f"#phase-{phase['id']}"}, phase["title"]),
                    )
                    for phase in data["phase_groups"]
                ]
            ),
        ),
    )


@component
def project_header(data: dict[str, Any]) -> Any:
    project = data["project"]
    return html.header(
        {"class_name": "project-header"},
        html.p(html.a({"href": "#project-navbar", "aria-label": "Projects home"}, "Home"), f" / {project['name']}"),
        html.h1({"id": "board-title"}, data["title"]),
        html.p(
            html.span({"id": "project-start-date"}, project["start_date"]),
            " - ",
            html.span({"id": "project-end-date"}, project["end_date"]),
        ),
        html.p(
            "Status: ",
            html.span({"id": "project-status"}, project["status"]),
            "; organization: ",
            html.span({"id": "project-organization"}, project["organization"]),
        ),
        html.p(html.span({"id": "visible-count"}, str(data["visible_count"])), " visible outputs"),
    )


@component
def project_actions(data: dict[str, Any], act: Any) -> Any:
    return html.section(
        {"aria-label": "Project actions"},
        html.div(
            {"class_name": "toolbar"},
            action_form(
                act,
                "filter",
                "Filter",
                html.label({"html_for": "query"}, "Filter outputs"),
                html.input(
                    {"key": f"query-{data['revision']}", "id": "query", "name": "query", "value": data["query"]}
                ),
                input_name="query",
            ),
            action_form(
                act,
                "save",
                "Save",
                html.label({"html_for": "title-input"}, "Project name"),
                html.input(
                    {
                        "key": f"title-{data['revision']}",
                        "id": "title-input",
                        "name": "title",
                        "value": data["title_input"],
                    }
                ),
                input_name="title",
            ),
        ),
        html.p({"id": "form-error", "role": "alert"}, data["error"]),
        html.p({"id": "form-notice", "role": "status"}, data["notice"]),
        html.div(
            {"class_name": "toolbar"},
            action_form(act, "insert", "Insert output"),
            action_form(act, "reorder", "Reverse outputs"),
            action_form(act, "remove", "Remove inserted output"),
            action_form(act, "probe", "Check server"),
        ),
    )


@component
def project_info(data: dict[str, Any]) -> Any:
    project = data["project"]
    return html.section(
        {"class_name": "project-info"},
        html.h2("Project Info"),
        html.table(
            html.tbody(
                html.tr(html.th({"scope": "row"}, "Org"), html.td(project["organization"])),
                html.tr(
                    html.th({"scope": "row"}, "Duration"),
                    html.td(f"{project['start_date']} - {project['end_date']}"),
                ),
                html.tr(html.th({"scope": "row"}, "Status"), html.td(project["status"])),
                html.tr(
                    html.th({"scope": "row"}, "Tags"),
                    html.td({"data-project-tags": ""}, ", ".join(data["project_tags"]) or "No entries"),
                ),
            )
        ),
        html.section({"data-project-status-updates": ""}, html.h3("Status updates"), html.p("No entries")),
        html.section(
            html.h3("Team"),
            html.table(
                html.thead(html.tr(html.th("Name"), html.th("Role"))),
                html.tbody(
                    *[
                        html.tr(
                            {"key": role["id"], "data-role-id": role["id"]},
                            html.td({"class_name": "user-name"}, role["user_name"]),
                            html.td({"class_name": "role-name"}, role["name"]),
                        )
                        for role in data["roles"]
                    ]
                ),
            ),
        ),
        html.section({"data-project-contacts": ""}, html.h3("Contacts"), html.p("No entries")),
    )


@component
def project_notes(group: dict[str, Any]) -> Any:
    return html.section(
        {"class_name": "project-notes"},
        html.h2("Notes"),
        *[
            html.article(
                {"key": note["id"], "data-note-id": note["id"]},
                html.p({"class_name": "note-text"}, note["text"]),
                html.details(
                    html.summary("Comments"),
                    *[
                        html.article(
                            {"key": comment["id"], "data-comment-id": comment["id"]},
                            html.p({"class_name": "comment-text"}, comment["text"]),
                            html.small({"class_name": "comment-author"}, comment["author"]),
                        )
                        for comment in note["comments"]
                    ],
                ),
            )
            for note in group["notes"]
        ],
    )


@component
def output_badge(output: dict[str, Any]) -> Any:
    missing = any(not dependency["completed"] for dependency in output["dependencies"])
    label = "Missing dependency" if missing else "Completed" if output["completed"] else "In progress"
    return html.span(
        {"data-output-badge": "done" if output["completed"] else "open", "class_name": "output-badge"},
        label,
    )


@component
def output_attachments(output: dict[str, Any]) -> Any:
    return html.section(
        {"class_name": "output-attachments", "aria-label": "Attachments"},
        html.h4("Attachments"),
        *(
            [
                html.article(
                    {
                        "key": attachment["id"],
                        "data-attachment-id": attachment["id"],
                        "data-attachment-name": attachment["name"],
                    },
                    html.a(
                        {"href": attachment["url"], "class_name": "attachment-name"},
                        attachment["name"],
                    ),
                    html.ul(*[html.li({"key": tag, "data-attachment-tag": tag}, tag) for tag in attachment["tags"]]),
                )
                for attachment in output["attachments"]
            ]
            if output["attachments"]
            else [html.p("No attachments")]
        ),
    )


@component
def output_dependency(dependency: dict[str, Any]) -> Any:
    return html.article(
        {
            "data-dependency-id": dependency["id"],
            "data-dependency-title": dependency["title"],
            "data-dependency-completed": "true" if dependency["completed"] else "false",
        },
        html.span({"aria-hidden": "true"}, "✓" if dependency["completed"] else "⚠"),
        html.span({"class_name": "dependency-title"}, dependency["title"]),
    )


@component
def output_form(act: Any, output: dict[str, Any]) -> Any:
    return action_form(
        act,
        "select",
        "Select",
        html.label({"html_for": f"description-{output['id']}"}, "Description"),
        html.textarea(
            {"id": f"description-{output['id']}", "data-output-description": "", "value": output["description"]}
        ),
        html.label(
            html.input({"type": "checkbox", "data-output-completed": "", "checked": output["completed"]}),
            " Completed",
        ),
        row_id=output["id"],
    )


@component
def project_output(data: dict[str, Any], act: Any, output: dict[str, Any]) -> Any:
    return html.article(
        {
            "key": output["id"],
            "id": output["element_id"],
            "data-row-id": output["id"],
            "data-output-expanded": "true",
            **({"data-source-id": output["source_id"]} if output["source_id"] is not None else {}),
            "data-selected": "true" if output["id"] == data["selected"] else "false",
        },
        html.header(
            html.span({"class_name": "row-title"}, output["title"]),
            html.span({"class_name": "row-status"}, output["status"]),
            output_badge(output),
        ),
        output_form(act, output),
        html.details(
            {"open": True},
            html.summary("Output details"),
            html.section(
                {"aria-label": "Dependencies"},
                html.h4("Dependencies"),
                *(
                    [output_dependency(dependency) for dependency in output["dependencies"]]
                    if output["dependencies"]
                    else [html.p("No dependencies")]
                ),
            ),
            output_attachments(output),
        ),
    )


@component
def phase_group(data: dict[str, Any], act: Any, phase: dict[str, Any]) -> Any:
    return html.section(
        {
            "key": phase["id"],
            "id": f"phase-{phase['id']}",
            "data-phase-id": phase["id"],
            "data-phase-expanded": "true",
        },
        html.details(
            {"open": True},
            html.summary(html.h3({"class_name": "phase-title"}, phase["title"])),
            html.div(*[project_output(data, act, output) for output in phase["outputs"]]),
        ),
    )


@component
def project_outputs(data: dict[str, Any], act: Any) -> Any:
    return html.section(
        {"id": "rows", "class_name": "project-outputs"},
        html.h2("Outputs"),
        *[phase_group(data, act, phase) for phase in data["phase_groups"]],
    )


@component
def project_tabs(data: dict[str, Any], act: Any) -> Any:
    tabs = [
        ("project-info", "Project Info", project_info(data)),
        *[(group["id"], group["title"], project_notes(group)) for group in data["note_tabs"]],
        ("outputs", "Outputs", project_outputs(data, act)),
    ]
    return html.section(
        {"id": "project-tabs"},
        html.div(
            {"role": "tablist"},
            *[
                html.button(
                    {
                        "key": panel_id,
                        "type": "button",
                        "role": "tab",
                        "data-tab-target": panel_id,
                        "aria-controls": panel_id,
                        "aria-selected": panel_id == "outputs",
                    },
                    label,
                )
                for panel_id, label, _content in tabs
            ],
        ),
        *[
            html.div(
                {
                    "key": panel_id,
                    "id": panel_id,
                    "role": "tabpanel",
                    "data-tab-panel": panel_id,
                    "hidden": panel_id != "outputs",
                },
                content,
            )
            for panel_id, _label, content in tabs
        ],
    )


@component
def project_page(data: dict[str, Any], act: Any) -> Any:
    return html.div(
        {"class_name": "project-shell"},
        project_navbar(data),
        project_sidebar(data),
        html.main(project_header(data), project_actions(data, act), project_tabs(data, act)),
    )


@component
def board_app() -> Any:
    session = parse_qs(use_location().search.lstrip("?")).get("session", ["manual"])[0]
    revision, set_revision = hooks.use_state(0)
    data = snapshot(session)

    def act(action: str, row_id: int, input_name: str, event_data: dict[str, Any]) -> None:
        controls = event_data["target"]["elements"]
        value = controls[1].get("value", "") if input_name else ""
        apply(
            session,
            ActionInput(
                action=action,
                operation=controls[0].get("value", ""),
                row_id=str(row_id),
                query=value if input_name == "query" else "",
                title=value if input_name == "title" else "",
            ),
        )
        set_revision(lambda previous: previous + 1)

    board = html.section(
        {
            "id": "board",
            "data-project-id": data["project"]["id"],
            "data-session": session,
            "data-operation": data["operation"],
            "data-revision": data["revision"],
            "data-visible-count": data["visible_count"],
            "data-total-count": data["total_count"],
        },
        project_page(data, act),
    )
    identity = {
        "session": session,
        "operation": data["operation"],
        "revision": data["revision"],
        "phase": "initial" if revision == 0 else "update",
    }
    return html.div(
        LocalDisclosure(),
        board,
        html.script(
            {"key": f"commit-{revision}"}, f"window.__reactpyBoardObserver.committed({json.dumps(identity)});"
        ),
    )


async def index(request: Request) -> Response:
    try:
        session = request.query_params.get("session", "manual")
        reset(session, int(request.query_params.get("count", "14")))
    except ValueError as exc:
        return Response(str(exc), status_code=400)
    records.pop(session, None)
    accepted.pop(session, None)
    return HTMLResponse(INDEX_HTML)


async def health(_request: Request) -> Response:
    return Response(os.environ.get("CITRY_BENCH_SERVER_NONCE", "ok"), media_type="text/plain")


async def audit(request: Request) -> Response:
    return JSONResponse(report(request.query_params.get("session", "manual")))


async def asset(request: Request) -> Response:
    name = request.path_params["name"]
    if name == "board.css":
        return Response((SCENARIO / name).read_bytes(), media_type="text/css")
    if name in ("readiness.js", "tabs.js"):
        return Response((HERE / "assets" / name).read_bytes(), media_type="text/javascript")
    return Response(status_code=404)


app = Starlette(
    debug=False,
    routes=[
        Route("/", index),
        Route("/health", health),
        Route("/__bench/operations", audit),
        Route("/assets/{name}", asset),
    ],
)
options = starlette.Options(
    serve_index_route=False,
    head=[
        html.title("Project board benchmark"),
        html.link({"rel": "icon", "href": "data:,"}),
        html.link({"rel": "stylesheet", "href": "/assets/board.css"}),
        html.script({"src": "/assets/readiness.js"}),
        html.script({"src": "/assets/tabs.js", "defer": True}),
    ],
)
starlette.configure(app, board_app, options)
# Use the exact installed client's shell, adding only the documented head option.
INDEX_HTML = starlette.read_client_index_html(options)
application = ObserveTransport(app)
