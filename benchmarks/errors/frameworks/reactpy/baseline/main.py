"""The error benchmark's reference page, written the way the ReactPy docs write an app."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reactpy import component, hooks, html, web
from reactpy.backend.starlette import Options, configure
from reactpy.types import ComponentType, VdomDict
from reactpy_router import browser_router, link, route, use_params, use_search_params
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from card import BoardContext, Card
from status import Status

HERE = Path(__file__).parent

# The browser receives API_BASE; SECRET_TOKEN stays on the server.
API_BASE = "/api"
SECRET_TOKEN = "s3cr3t"
# The heading's color, which app.css reads as the CSS variable --accent.
ACCENT = "rgb(0, 0, 255)"


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
def Search() -> VdomDict:
    # The text typed so far, which the line under the field repeats.
    query, set_query = hooks.use_state("")

    # The form has no submit handler, so the browser submits it the ordinary
    # way: back to this page, with the text in the URL as `q`.
    return html.form(
        {"role": "search"},
        html.input(
            {
                "type": "search",
                "name": "q",
                "value": query,
                "on_change": lambda event: set_query(event["target"]["value"]),
            }
        ),
        html.button({"type": "submit"}, "Search"),
        html.p(f"Searching for: {query}"),
    )


@component
def Page() -> VdomDict:
    # Cards are hidden in this page's state only; the project list stays the same.
    hidden, set_hidden = hooks.use_state([])

    # Each card gets a hide handler of its own, built by a function, the way
    # ReactPy's docs build one handler per list item, so the handler knows
    # its card's title without the card passing it back.
    def make_hide(title: str) -> Callable[[], None]:
        def hide() -> None:
            set_hidden([*hidden, title])

        return hide

    # What the search form submitted, read from the page's URL.
    searched = use_search_params().get("q", [""])[0]

    return html.div(
        {"style": {"--accent": ACCENT}},
        html.h1("Projects"),
        html.div(
            {"class_name": "board", "id": "board", "title": "Board"},
            html.p(f"Owned by {owner.name}"),
            html.img({"src": "/static/avatar.svg", "alt": owner.name, "width": 32, "height": 32}),
            html.p(f"Owner: {owner.name}"),
            html.p(f"Projects: {len(projects)}"),
            html.p(ApiLine({"api_base": API_BASE})),
            # Every card inside reads the board's name from this context.
            BoardContext(
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
                            on_hide=make_hide(project.title),
                            # A key keeps each card matched to its project when an earlier one is hidden.
                            key=project.title,
                        )
                        for project in projects
                        if project.title not in hidden
                    ],
                ),
                value="Projects",
            ),
            Counter(),
            Details(),
            Search(),
            html.p(f"Searched: {searched}") if searched else None,
            # Links through the router change the page in the browser, without a new page load.
            html.nav(link({"to": "/about"}, "About"), " ", link({"to": "/projects/1"}, "Project 1")),
        ),
    )


@component
def ProjectPage() -> VdomDict:
    # The router turns the `{id:int}` part of the path into a number.
    project_id = use_params()["id"]
    return html.h1(f"Project {project_id}")


@component
def App() -> ComponentType:
    # ReactPy-Router, from the ReactPy project, picks the page that matches the
    # browser's URL; the last route catches every other URL.
    return browser_router(
        route("/", Page()),
        route("/about", html.h1("About this board")),
        route("/projects/{id:int}", ProjectPage()),
        route("{404:any}", html.h1("Page not found")),
    )


# The static files are mounted before ReactPy's routes, because ReactPy answers
# every other path with its page.
app = Starlette(routes=[Mount("/static", StaticFiles(directory=HERE / "static"))])
# The page's stylesheet and title go in the document head through the
# backend's options.
configure(
    app,
    App,
    Options(head=(html.title("Projects"), html.link({"rel": "stylesheet", "href": "/static/app.css"}))),
)
