"""The error benchmark's reference page, written the way the ReactPy docs write an app."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reactpy import component, hooks, html, web
from reactpy.backend.starlette import Options, configure
from reactpy.types import VdomDict
from starlette.applications import Starlette

from card import Card
from status import Status

HERE = Path(__file__).parent

# The browser receives API_BASE; SECRET_TOKEN stays on the server.
API_BASE = "/api"
SECRET_TOKEN = "s3cr3t"


@dataclass
class Owner:
    name: str


@dataclass
class Project:
    title: str
    count: int
    # The page draws a featured project's card with the accent border.
    featured: bool = False


owner = Owner("Ada")
projects = [Project("Alpha", 3, featured=True), Project("Beta", 5), Project("Gamma", 8)]

# The API line is rendered by browser code, a ReactPy JavaScript component.
api_module = web.module_from_file("board-api", HERE / "api_line.js")
ApiLine = web.export(api_module, "ApiLine")


@component
def Counter() -> VdomDict:
    count, set_count = hooks.use_state(0)

    # ReactPy runs a click handler on the server, so `save` is a plain Python
    # function that the Add button calls with the amount to add.
    def save(amount: int) -> None:
        set_count(count + amount)

    return html.section(
        html.p(f"Saved: {count}"),
        html.button({"type": "button", "on_click": lambda event: save(amount=1)}, "Add"),
    )


@component
def Details() -> VdomDict:
    open, set_open = hooks.use_state(False)

    def toggle(event: dict[str, Any]) -> None:
        set_open(lambda value: not value)

    return html.section(
        html.button({"type": "button", "aria-expanded": open, "on_click": toggle}, "Details"),
        html.p("Details are visible") if open else None,
        Status(open=open, on_close=lambda: set_open(False)),
    )


@component
def Page() -> VdomDict:
    # Cards are hidden in this page's state only; the project list stays the same.
    hidden, set_hidden = hooks.use_state([])

    return html.div(
        html.h1("Projects"),
        html.div(
            {"class_name": "board", "title": "Board"},
            html.p(f"Owner: {owner.name}"),
            html.p(ApiLine({"api_base": API_BASE})),
            # ReactPy matches unkeyed children by position, so the cards get a
            # wrapper of their own: hiding one then cannot shift the counter and
            # the details panel to new positions, which would reset their state.
            html.div(
                {"class_name": "cards"},
                [
                    Card(
                        title=project.title,
                        count=project.count,
                        tone="accent" if project.featured else "plain",
                        footer=lambda title, count: html.a({"href": f"#{title.lower()}"}, f"Open {title} ({count})"),
                        on_hide=lambda title: set_hidden([*hidden, title]),
                        key=project.title,
                    )
                    for project in projects
                    if project.title not in hidden
                ],
            ),
            Counter(),
            Details(),
            html.form({"role": "search"}, html.button({"type": "submit"}, "Search")),
        ),
    )


# The page's stylesheet goes in the document head, where ReactPy's backend
# options put the page title too.
STYLES = """
.board { color: rgb(0, 128, 0); }
.card--accent { border: 2px solid rgb(0, 0, 255); }
"""

app = Starlette()
configure(app, Page, Options(head=(html.title("Projects"), html.style(STYLES))))
