"""Render the canonical project page with Reflex state and component functions."""

import sys
from pathlib import Path
from typing import Any, TypedDict

import reflex as rx
from reflex_components_core.el.elements.sectioning import Section

HERE = Path(__file__).resolve().parent.parent
SCENARIO = HERE / "scenario"
if not SCENARIO.is_dir():
    SCENARIO = HERE.parents[1] / "scenarios/project_board"
sys.path.insert(0, str(SCENARIO))
from model import ActionInput, apply, reset, snapshot  # noqa: E402


class CommentData(TypedDict):
    id: int
    text: str
    author: str


class NoteData(TypedDict):
    id: int
    text: str
    comments: list[CommentData]


class NoteTabData(TypedDict):
    id: str
    title: str
    notes: list[NoteData]


class AttachmentData(TypedDict):
    id: int
    name: str
    url: str
    tags: list[str]


class DependencyData(TypedDict):
    id: int
    title: str
    completed: bool


class OutputData(TypedDict):
    id: int
    source_id: int | None
    title: str
    status: str
    completed: bool
    description: str
    phase_id: int
    attachments: list[AttachmentData]
    dependencies: list[DependencyData]
    element_id: str
    select_action: str
    selected: bool


class PhaseGroupData(TypedDict):
    id: int
    title: str
    outputs: list[OutputData]


class RoleData(TypedDict):
    id: int
    name: str
    user_name: str


class BookmarkData(TypedDict):
    id: int
    text: str
    url: str


class ProjectData(TypedDict):
    id: int
    name: str
    status: str
    start_date: str
    end_date: str
    organization: str


class Board(rx.State):
    session: str = ""
    revision: int = -1
    operation: str = "initial"
    title: str = "Project Name"
    title_input: str = "Project Name"
    query: str = ""
    selected: int = 0
    error: str = ""
    notice: str = ""
    visible_count: int = 0
    total_count: int = 0
    project: ProjectData = {}  # type: ignore[assignment]  # noqa: RUF012
    phase_groups: list[PhaseGroupData] = []  # noqa: RUF012
    note_tabs: list[NoteTabData] = []  # noqa: RUF012
    roles: list[RoleData] = []  # noqa: RUF012
    bookmarks: list[BookmarkData] = []  # noqa: RUF012
    contacts: list[dict[str, Any]] = []  # noqa: RUF012
    status_updates: list[dict[str, Any]] = []  # noqa: RUF012
    project_tags: list[dict[str, Any]] = []  # noqa: RUF012

    def _update_board(self, value: dict[str, Any]) -> None:
        for name in (
            "session",
            "revision",
            "operation",
            "title",
            "title_input",
            "query",
            "selected",
            "error",
            "notice",
            "visible_count",
            "total_count",
            "project",
            "phase_groups",
            "note_tabs",
            "roles",
            "bookmarks",
            "contacts",
            "status_updates",
            "project_tags",
        ):
            setattr(self, name, value[name])

    @rx.event
    def load(self) -> None:
        params = self.router.url.query_parameters
        session = str(params.get("session", "manual"))
        reset(session, int(params.get("count", "14")))
        self._update_board(snapshot(session))

    @rx.event
    def act(self, values: dict[str, Any]) -> None:
        if values.get("session") != self.session:
            raise ValueError("The submitted session must match the connected project")
        apply(
            self.session,
            ActionInput(
                **{
                    name: (values.get(name) if values.get(name) is not None else default)
                    for name, default in (
                        ("action", ""),
                        ("operation", ""),
                        ("row_id", "0"),
                        ("query", ""),
                        ("title", ""),
                    )
                }
            ),
        )
        self._update_board(snapshot(self.session))


class ObservedSection(Section):
    def add_imports(self) -> dict[str, list[str]]:
        return {"react": ["useEffect"]}

    def add_hooks(self) -> list[str]:
        return [
            f"""useEffect(() => {{
          if ({Board.revision!s} < 0 || !{rx.State.is_hydrated!s}) return;
          window.Alpine?.nextTick(() => {{
            const root = document.getElementById('board');
            window.__citryBench?.ready({{
              session: root.dataset.session, operation: root.dataset.operation,
              revision: Number(root.dataset.revision), pending: 0,
              phase: Number(root.dataset.revision) === 0 ? 'initial' : 'update',
            }});
          }});
        }}, [{Board.revision!s}, {rx.State.is_hydrated!s}]);"""
        ]


def hidden(name: str, value: Any) -> rx.Component:
    return rx.el.input(type="hidden", name=name, default_value=value)


def action_form(action: str, label: str, *children: rx.Component, row_id: Any = None) -> rx.Component:
    return rx.el.form(
        hidden("session", Board.session),
        hidden("operation", "manual"),
        hidden("action", action),
        *([hidden("row_id", row_id)] if row_id is not None else []),
        *children,
        rx.el.button(
            label,
            type="submit",
            custom_attrs={"data-bench-action": action if row_id is None else "select-" + row_id.to(str)},
        ),
        on_submit=Board.act,
        reset_on_submit=False,
        no_validate=True,
        class_name="output-form" if row_id is not None else "",
    )


def project_navbar() -> rx.Component:
    return rx.el.nav(
        rx.el.a("Projects", href="#board"),
        rx.el.span(Board.project["name"], aria_current="page"),
        id="project-navbar",
        aria_label="Primary",
    )


def bookmark(item: rx.Var[BookmarkData]) -> rx.Component:
    return rx.el.a(
        rx.el.span(item["text"], class_name="bookmark-name"),
        href=item["url"],
        key=item["id"],
        custom_attrs={"data-bookmark-id": item["id"], "data-bookmark-name": item["text"]},
    )


def phase_link(item: rx.Var[PhaseGroupData]) -> rx.Component:
    return rx.el.li(rx.el.a(item["title"], href="#phase-" + item["id"].to(str)), key=item["id"])


def project_sidebar() -> rx.Component:
    return rx.el.aside(
        rx.el.section(
            rx.el.h2("Project Bookmarks", id="bookmark-heading"),
            rx.foreach(Board.bookmarks, bookmark),
            aria_labelledby="bookmark-heading",
        ),
        rx.el.nav(
            rx.el.h2("Phases"),
            rx.el.ul(rx.foreach(Board.phase_groups, phase_link)),
            aria_label="Project phases",
        ),
        id="project-sidebar",
    )


def project_header() -> rx.Component:
    return rx.el.header(
        rx.el.p(rx.el.a("Home", href="#project-navbar", aria_label="Projects home"), " / ", Board.project["name"]),
        rx.el.h1(Board.title, id="board-title"),
        rx.el.p(
            rx.el.span(Board.project["start_date"], id="project-start-date"),
            " - ",
            rx.el.span(Board.project["end_date"], id="project-end-date"),
        ),
        rx.el.p(
            "Status: ",
            rx.el.span(Board.project["status"], id="project-status"),
            "; organization: ",
            rx.el.span(Board.project["organization"], id="project-organization"),
        ),
        rx.el.p(rx.el.span(Board.visible_count, id="visible-count"), " visible outputs"),
        class_name="project-header",
    )


def project_actions() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            action_form(
                "filter",
                "Filter",
                rx.el.label("Filter outputs", html_for="query"),
                rx.el.input(id="query", name="query", default_value=Board.query, key=Board.revision.to(str)),
            ),
            action_form(
                "save",
                "Save",
                rx.el.label("Project name", html_for="title-input"),
                rx.el.input(
                    id="title-input",
                    name="title",
                    default_value=Board.title_input,
                    key=Board.revision.to(str),
                ),
            ),
            class_name="toolbar",
        ),
        rx.el.p(Board.error, id="form-error", role="alert"),
        rx.el.p(Board.notice, id="form-notice", role="status"),
        rx.el.div(
            action_form("insert", "Insert output"),
            action_form("reorder", "Reverse outputs"),
            action_form("remove", "Remove inserted output"),
            action_form("probe", "Check server"),
            class_name="toolbar",
        ),
        aria_label="Project actions",
    )


def role_row(item: rx.Var[RoleData]) -> rx.Component:
    return rx.el.tr(
        rx.el.td(item["user_name"], class_name="user-name"),
        rx.el.td(item["name"], class_name="role-name"),
        key=item["id"],
        custom_attrs={"data-role-id": item["id"]},
    )


def project_info() -> rx.Component:
    return rx.el.section(
        rx.el.h2("Project Info"),
        rx.el.table(
            rx.el.tbody(
                rx.el.tr(rx.el.th("Org", scope="row"), rx.el.td(Board.project["organization"])),
                rx.el.tr(
                    rx.el.th("Duration", scope="row"),
                    rx.el.td(Board.project["start_date"], " - ", Board.project["end_date"]),
                ),
                rx.el.tr(rx.el.th("Status", scope="row"), rx.el.td(Board.project["status"])),
                rx.el.tr(
                    rx.el.th("Tags", scope="row"),
                    rx.el.td("No entries", custom_attrs={"data-project-tags": ""}),
                ),
            )
        ),
        rx.el.section(
            rx.el.h3("Status updates"),
            rx.el.p("No entries"),
            custom_attrs={"data-project-status-updates": ""},
        ),
        rx.el.section(
            rx.el.h3("Team"),
            rx.el.table(
                rx.el.thead(rx.el.tr(rx.el.th("Name"), rx.el.th("Role"))),
                rx.el.tbody(rx.foreach(Board.roles, role_row)),
            ),
        ),
        rx.el.section(rx.el.h3("Contacts"), rx.el.p("No entries"), custom_attrs={"data-project-contacts": ""}),
        class_name="project-info",
    )


def comment(item: rx.Var[CommentData]) -> rx.Component:
    return rx.el.article(
        rx.el.p(item["text"], class_name="comment-text"),
        rx.el.small(item["author"], class_name="comment-author"),
        key=item["id"],
        custom_attrs={"data-comment-id": item["id"]},
    )


def note(item: rx.Var[NoteData]) -> rx.Component:
    return rx.el.article(
        rx.el.p(item["text"], class_name="note-text"),
        rx.el.details(rx.el.summary("Comments"), rx.foreach(item["comments"], comment)),
        key=item["id"],
        custom_attrs={"data-note-id": item["id"]},
    )


def project_notes(group: rx.Var[NoteTabData]) -> rx.Component:
    return rx.el.section(rx.el.h2("Notes"), rx.foreach(group["notes"], note), class_name="project-notes")


def attachment_tag(value: rx.Var[str]) -> rx.Component:
    return rx.el.li(value, custom_attrs={"data-attachment-tag": value})


def attachment(item: rx.Var[AttachmentData]) -> rx.Component:
    return rx.el.article(
        rx.el.a(item["name"], href=item["url"], class_name="attachment-name"),
        rx.el.ul(rx.foreach(item["tags"], attachment_tag)),
        key=item["id"],
        custom_attrs={"data-attachment-id": item["id"], "data-attachment-name": item["name"]},
    )


def dependency(item: rx.Var[DependencyData]) -> rx.Component:
    return rx.el.article(
        rx.el.span(rx.cond(item["completed"], "✓", "⚠"), aria_hidden="true"),
        rx.el.span(item["title"], class_name="dependency-title"),
        key=item["id"],
        custom_attrs={
            "data-dependency-id": item["id"],
            "data-dependency-title": item["title"],
            "data-dependency-completed": rx.cond(item["completed"], "true", "false"),
        },
    )


def output_form(item: rx.Var[OutputData]) -> rx.Component:
    return action_form(
        "select",
        "Select",
        rx.el.label("Description", html_for="description-" + item["id"].to(str)),
        rx.el.textarea(
            default_value=item["description"],
            id="description-" + item["id"].to(str),
            custom_attrs={"data-output-description": ""},
        ),
        rx.el.label(
            rx.el.input(
                type="checkbox",
                default_checked=item["completed"],
                custom_attrs={"data-output-completed": ""},
            ),
            " Completed",
        ),
        row_id=item["id"],
    )


def output_attachments(item: rx.Var[OutputData]) -> rx.Component:
    return rx.el.section(
        rx.el.h4("Attachments"),
        rx.cond(
            item["attachments"].length() > 0,
            rx.foreach(item["attachments"], attachment),
            rx.el.p("No attachments"),
        ),
        class_name="output-attachments",
        aria_label="Attachments",
    )


def output(item: rx.Var[OutputData]) -> rx.Component:
    return rx.el.article(
        rx.el.header(
            rx.el.span(item["title"], class_name="row-title"),
            rx.el.span(item["status"], class_name="row-status"),
            rx.el.span(
                rx.cond(
                    item["dependencies"].length() > 0,
                    "Missing dependency",
                    rx.cond(item["completed"], "Completed", "In progress"),
                ),
                class_name="output-badge",
                custom_attrs={"data-output-badge": item["status"]},
            ),
        ),
        output_form(item),
        rx.el.details(
            rx.el.summary("Output details"),
            rx.el.section(
                rx.el.h4("Dependencies"),
                rx.cond(
                    item["dependencies"].length() > 0,
                    rx.foreach(item["dependencies"], dependency),
                    rx.el.p("No dependencies"),
                ),
                aria_label="Dependencies",
            ),
            output_attachments(item),
            open=True,
        ),
        key=item["id"],
        id=item["element_id"],
        custom_attrs={
            "data-row-id": item["id"],
            "data-output-expanded": "true",
            "data-source-id": item["source_id"],
            "data-selected": rx.cond(item["selected"], "true", "false"),
        },
    )


def phase_group(item: rx.Var[PhaseGroupData]) -> rx.Component:
    return rx.el.section(
        rx.el.details(
            rx.el.summary(rx.el.h3(item["title"], class_name="phase-title")),
            rx.el.div(rx.foreach(item["outputs"], output)),
            open=True,
        ),
        key=item["id"],
        id="phase-" + item["id"].to(str),
        custom_attrs={"data-phase-id": item["id"], "data-phase-expanded": "true"},
    )


def project_outputs() -> rx.Component:
    return rx.el.section(
        rx.el.h2("Outputs"),
        rx.foreach(Board.phase_groups, phase_group),
        id="rows",
        class_name="project-outputs",
    )


def tab_button(panel_id: Any, label: Any) -> rx.Component:
    return rx.el.button(
        label,
        type="button",
        role="tab",
        aria_controls=panel_id,
        aria_selected=panel_id == "outputs",
        custom_attrs={"data-tab-target": panel_id},
    )


def note_tab_button(group: rx.Var[NoteTabData]) -> rx.Component:
    return tab_button(group["id"], group["title"])


def note_tab_panel(group: rx.Var[NoteTabData]) -> rx.Component:
    return rx.el.div(
        project_notes(group),
        id=group["id"],
        role="tabpanel",
        hidden=True,
        custom_attrs={"data-tab-panel": group["id"]},
    )


def project_tabs() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            tab_button("project-info", "Project Info"),
            rx.foreach(Board.note_tabs, note_tab_button),
            tab_button("outputs", "Outputs"),
            role="tablist",
        ),
        rx.el.div(
            project_info(),
            id="project-info",
            role="tabpanel",
            hidden=True,
            custom_attrs={"data-tab-panel": "project-info"},
        ),
        rx.foreach(Board.note_tabs, note_tab_panel),
        rx.el.div(project_outputs(), id="outputs", role="tabpanel", custom_attrs={"data-tab-panel": "outputs"}),
        id="project-tabs",
    )


def index() -> rx.Component:
    return rx.el.main(
        rx.html("""<aside x-data="{ open: false }" id="local-disclosure">
<button type="button" data-bench-action="disclosure" @click="open = !open" :aria-expanded="open">Local details</button>
<p x-show="open" x-cloak id="disclosure-content">This disclosure needs no server request.</p>
<label for="preserved-input">Local draft</label><input id="preserved-input" value="Unchanged draft"></aside>"""),
        ObservedSection.create(
            project_navbar(),
            project_sidebar(),
            rx.el.main(project_header(), project_actions(), project_tabs()),
            id="board",
            custom_attrs={
                "data-hydrated": rx.State.is_hydrated,
                "data-project-id": Board.project["id"],
                "data-session": Board.session,
                "data-operation": Board.operation,
                "data-revision": Board.revision,
                "data-visible-count": Board.visible_count,
                "data-total-count": Board.total_count,
            },
        ),
    )


app = rx.App(
    stylesheets=["/board.css", "/reflex-board-defaults.css"],
    theme=None,
    head_components=[rx.el.script(src="/alpine.min.js", defer=True), rx.el.script(src="/tabs.js", defer=True)],
)
app.add_page(index, on_load=Board.load, title="Project board benchmark")
