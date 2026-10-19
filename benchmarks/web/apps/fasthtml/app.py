"""Render the shared board with FastHTML FastTags and ordinary HTMX forms."""

# The captured scenario directory is shared data and assertions, not a renderer.
# ruff: noqa: E402

import os
import secrets
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

from fastcore.xml import FT
from fasthtml.common import (
    H1,
    H2,
    H3,
    H4,
    A,
    Article,
    Aside,
    Body,
    Button,
    Details,
    Div,
    FastHTML,
    Form,
    Head,
    Header,
    Html,
    Input,
    Label,
    Link,
    Meta,
    Nav,
    P,
    Script,
    Section,
    Span,
    Strong,
    Summary,
    Table,
    Tbody,
    Td,
    Textarea,
    Th,
    Title,
    Tr,
)
from starlette.datastructures import MutableHeaders
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

HERE = Path(__file__).parent
SCENARIO = HERE / "scenario"
if not SCENARIO.is_dir():
    SCENARIO = HERE.parents[1] / "scenarios" / "project_board"
sys.path.insert(0, str(SCENARIO))

import fasthtml.core
from model import ActionInput, apply, reset, snapshot
from render_timing import RenderTimingMiddleware, instrument, render_span, timed_render

app = FastHTML(
    debug=False,
    default_hdrs=False,
    canonical=False,
    secret_key="project-board-local-benchmark-only",  # noqa: S106 - isolated synthetic data
    middleware=[Middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])],
)


def render_snapshot(session: str) -> dict:
    state = snapshot(session)
    for phase in state["phase_groups"]:
        for row in phase["outputs"]:
            row["badge"] = (
                "Missing dependency"
                if any(not dependency["completed"] for dependency in row["dependencies"])
                else "Completed"
                if row["completed"]
                else "In progress"
            )
    return state


def form(state: dict, csrf: str, action: str, *children: Any, **attrs: Any) -> FT:
    return Form(
        Input(type="hidden", name="csrfmiddlewaretoken", value=csrf),
        Input(type="hidden", name="session", value=state["session"]),
        Input(type="hidden", name="action", value=action),
        Input(type="hidden", name="operation", value="manual"),
        *children,
        hx_post="/action",
        hx_target="#board",
        hx_swap="outerHTML",
        **attrs,
    )


def button(label: str, action: str) -> FT:
    return Button(label, type="submit", data_bench_action=action)


def attachments(row: dict) -> FT:
    items = [
        Article(
            A(item["name"], href=item["url"], cls="attachment-name"),
            Div(*[Span(tag, cls="attachment-tag", data_attachment_tag=tag) for tag in item["tags"]]),
            data_attachment_id=item["id"],
            data_attachment_name=item["name"],
        )
        for item in row["attachments"]
    ]
    return Section(H4("Attachments"), *(items or [P("No attachments")]), cls="attachments")


def dependencies(row: dict) -> FT:
    items = [
        Article(
            Span(item["title"], cls="dependency-title"),
            Strong("Missing") if not item["completed"] else None,
            data_dependency_id=item["id"],
            data_dependency_title=item["title"],
            data_dependency_completed="true" if item["completed"] else "false",
        )
        for item in row["dependencies"]
    ]
    return Section(H4("Dependencies"), *(items or [P("No dependencies")]), cls="dependencies")


def output(state: dict, csrf: str, row: dict) -> FT:
    return Article(
        Header(
            Span(row["title"], cls="row-title"),
            Span(row["status"], cls="row-status"),
            Span(row["badge"], data_output_badge=row["status"]),
        ),
        form(
            state,
            csrf,
            "select",
            Input(type="hidden", name="row_id", value=row["id"]),
            Label("Description", Textarea(row["description"], data_output_description=True)),
            Label(Input(type="checkbox", checked=row["completed"], data_output_completed=True), " Completed"),
            button("Select", row["select_action"]),
            cls="output-form",
        ),
        Button("Output details", type="button", **{"@click": "open = !open", ":aria-expanded": "open"}),
        Div(dependencies(row), attachments(row), cls="output-panel", x_show="open"),
        id=row["element_id"],
        data_row_id=row["id"],
        data_source_id=row["source_id"] if row["source_id"] is not None else None,
        data_selected="true" if row["id"] == state["selected"] else "false",
        data_output_expanded="true",
        x_data="{ open: true }",
    )


def phase_group(state: dict, csrf: str, phase: dict) -> FT:
    children = [output(state, csrf, row) for row in phase["outputs"]]
    return Section(
        Button(
            H3(phase["title"], cls="phase-title"),
            type="button",
            **{"@click": "open = !open", ":aria-expanded": "open"},
        ),
        Div(*(children or [P("No outputs")]), x_show="open"),
        id=f"phase-{phase['id']}",
        data_phase_id=phase["id"],
        data_phase_expanded="true",
        x_data="{ open: true }",
    )


def project_info(state: dict) -> FT:
    project = state["project"]
    roles = [
        Article(Span(role["name"], cls="role-name"), Span(role["user_name"], cls="user-name"), data_role_id=role["id"])
        for role in state["roles"]
    ]
    return Section(
        H2("Project Info"),
        Table(
            Tbody(
                Tr(Th("Organization"), Td(project["organization"])),
                Tr(Th("Status"), Td(project["status"])),
                Tr(Th("Duration"), Td(f"{project['start_date']} \N{EN DASH} {project['end_date']}")),
            )
        ),
        Section(
            H3("Tags"),
            *([Span(tag) for tag in state["project_tags"]] or [P("No project tags")]),
            data_project_tags=True,
        ),
        Section(
            H3("Status updates"),
            *([P(item) for item in state["status_updates"]] or [P("No status updates")]),
            data_project_status_updates=True,
        ),
        Section(H3("Team"), *roles, id="project-team"),
        Section(
            H3("Contacts"),
            *([P(item["name"]) for item in state["contacts"]] or [P("No contacts")]),
            data_project_contacts=True,
        ),
        id="project-info",
        data_tab_panel="project-info",
        x_show="activeTab === 'project-info'",
    )


def note_panel(tab: dict) -> FT:
    notes = []
    for note in tab["notes"]:
        comments = [
            Article(Span(c["author"], cls="comment-author"), P(c["text"], cls="comment-text"), data_comment_id=c["id"])
            for c in note["comments"]
        ]
        notes.append(
            Article(P(note["text"], cls="note-text"), Details(Summary("Comments"), *comments), data_note_id=note["id"])
        )
    panel_id = tab["id"]
    return Section(
        H2(tab["title"]), *notes, id=panel_id, data_tab_panel=panel_id, x_show=f"activeTab === '{panel_id}'"
    )


def project_tabs(state: dict, csrf: str) -> FT:
    labels = (
        ("project-info", "Project Info"),
        ("notes-1", "Notes 1"),
        ("notes-2", "Notes 2"),
        ("notes-3", "Notes 3"),
        ("outputs", "Outputs"),
    )
    controls = Div(
        *[
            Button(
                label,
                type="button",
                role="tab",
                data_tab_target=target,
                **{"@click": f"activeTab = '{target}'", ":aria-selected": f"activeTab === '{target}'"},
            )
            for target, label in labels
        ],
        role="tablist",
    )
    output_panel = Section(
        H2("Outputs"),
        *[phase_group(state, csrf, p) for p in state["phase_groups"]],
        id="outputs",
        data_tab_panel="outputs",
        x_show="activeTab === 'outputs'",
    )
    return Div(
        controls,
        project_info(state),
        *[note_panel(t) for t in state["note_tabs"]],
        output_panel,
        id="project-tabs",
        x_data="{ activeTab: 'outputs' }",
    )


@timed_render
def board(state: dict, csrf: str) -> FT:
    project = state["project"]
    phase_links = [A(phase["title"], href=f"#phase-{phase['id']}") for phase in state["phase_groups"]]
    return Section(
        Nav("Project workspace", id="project-navbar", aria_label="Project navigation"),
        Aside(
            H2("Phases"),
            Nav(*phase_links, aria_label="Project phases"),
            H2("Bookmarks"),
            *[
                A(
                    Span(bookmark["text"], cls="bookmark-name"),
                    href=bookmark["url"],
                    data_bookmark_id=bookmark["id"],
                    data_bookmark_name=bookmark["text"],
                )
                for bookmark in state["bookmarks"]
            ],
            id="project-sidebar",
        ),
        Header(
            P(project["organization"], id="project-organization"),
            H1(state["title"], id="board-title"),
            P(
                Span(project["start_date"], id="project-start-date"),
                " \N{EN DASH} ",
                Span(project["end_date"], id="project-end-date"),
                " · ",
                Span(project["status"], id="project-status"),
            ),
            id="project-header",
        ),
        Div(
            form(
                state,
                csrf,
                "filter",
                Label("Filter outputs", fr="query"),
                Input(id="query", name="query", value=state["query"]),
                button("Filter", "filter"),
            ),
            form(
                state,
                csrf,
                "save",
                Label("Project title", fr="title-input"),
                Input(id="title-input", name="title", value=state["title_input"]),
                button("Save", "save"),
                novalidate=True,
            ),
            cls="toolbar",
        ),
        P(state["error"], id="form-error", role="alert"),
        P(state["notice"], id="form-notice", role="status"),
        Div(
            *[
                form(state, csrf, action, button(label, action))
                for action, label in (
                    ("insert", "Insert output"),
                    ("reorder", "Reverse outputs"),
                    ("remove", "Remove inserted output"),
                    ("probe", "Check server"),
                )
            ],
            cls="toolbar",
        ),
        P(Span(state["visible_count"], id="visible-count"), " visible outputs"),
        project_tabs(state, csrf),
        id="board",
        data_project_id=project["id"],
        data_revision=state["revision"],
        data_session=state["session"],
        data_operation=state["operation"],
        data_visible_count=state["visible_count"],
        data_total_count=state["total_count"],
    )


@app.get("/")
def index(req: Request) -> FT | Response:
    try:
        session = req.query_params.get("session", "manual")
        reset(session, int(req.query_params.get("count", "14")))
        state = render_snapshot(session)
    except ValueError as error:
        return Response(str(error), status_code=400)
    req.session["csrf"] = secrets.token_urlsafe(32)
    req.session["board_session"] = session
    req.scope["bench_identity"] = (state["operation"], state["revision"])
    with render_span():
        return Html(
            Head(
                Meta(charset="utf-8"),
                Meta(name="viewport", content="width=device-width,initial-scale=1"),
                Title("Project board benchmark"),
                Link(rel="icon", href="data:,"),
                Link(rel="stylesheet", href="/assets/board.css"),
                Script(src="/assets/readiness.js"),
                Script(src="/assets/htmx.min.js", defer=True),
                Script(src="/assets/alpine.min.js", defer=True),
            ),
            Body(
                Aside(
                    Button(
                        "Local details",
                        type="button",
                        data_bench_action="disclosure",
                        **{"@click": "open = !open", ":aria-expanded": "open"},
                    ),
                    P(
                        "This disclosure needs no server request.",
                        id="disclosure-content",
                        x_show="open",
                        x_cloak=True,
                    ),
                    Label("Local draft", fr="preserved-input"),
                    Input(id="preserved-input", value="Unchanged draft"),
                    id="local-disclosure",
                    x_data="{ open: false }",
                ),
                board(state, req.session["csrf"]),
            ),
            lang="en",
        )


@app.post("/action")
async def action(req: Request) -> FT | Response:
    data = await req.form()
    token = data.get("csrfmiddlewaretoken", "")
    expected = req.session.get("csrf")
    origin = req.headers.get("origin")
    if (
        not isinstance(token, str)
        or not token.isascii()
        or not expected
        or not secrets.compare_digest(token, expected)
        or (origin is not None and origin != str(req.base_url).rstrip("/"))
    ):
        return Response("CSRF verification failed", status_code=403)
    session = data.get("session")
    if session != req.session.get("board_session"):
        return Response("Board session does not match the browser session", status_code=403)
    values = {key: data.get(key, "") for key in ActionInput.__dataclass_fields__}
    if not all(isinstance(value, str) for value in values.values()):
        return Response("Action fields must be text", status_code=400)
    try:
        apply(session, ActionInput(**values))
        state = render_snapshot(session)
    except (ValueError, KeyError, TypeError) as error:
        return Response(str(error), status_code=400)
    req.scope["bench_identity"] = (state["operation"], state["revision"])
    return board(state, expected)


@app.get("/health")
def health() -> Response:
    return Response(os.environ.get("CITRY_BENCH_SERVER_NONCE", "ok"), media_type="text/plain")


@app.get("/assets/{name}")
def asset(name: str) -> Response:
    directory = SCENARIO if name == "board.css" else HERE / "assets"
    path = directory / name
    if path.parent != directory or not path.is_file():
        return Response(status_code=404)
    return Response(path.read_bytes(), media_type="text/css" if name.endswith(".css") else "text/javascript")


class ResponseTiming:
    """Measure FastHTML's ASGI work through response start, before body transmission."""

    def __init__(self, application: ASGIApp) -> None:
        self.application = application

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.application(scope, receive, send)
            return
        start = perf_counter()

        async def timed_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Cache-Control"] = "no-store"
                headers["Server-Timing"] = f"application;dur={(perf_counter() - start) * 1000:.3f}"
                identity = scope.get("bench_identity")
                if identity:
                    headers["X-Bench-Operation"] = identity[0]
                    headers["X-Bench-Revision"] = str(identity[1])
            await send(message)

        await self.application(scope, receive, timed_send)


application = ResponseTiming(app)


instrument(fasthtml.core, "_xt_cts")

application = RenderTimingMiddleware(application)
