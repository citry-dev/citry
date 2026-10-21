"""The error benchmark's reference page, written the way the Reflex docs write an app."""

import dataclasses
from typing import Any

import reflex as rx
from reflex.vars import ObjectVar

from board.card import card
from board.status import status


@dataclasses.dataclass
class Owner:
    name: str


@dataclasses.dataclass
class Project:
    title: str
    count: int
    # The page draws a featured project's card with the accent border.
    featured: bool = False


class BoardState(rx.State):
    """The board's server data, which Reflex sends to the browser as state."""

    owner: rx.Field[Owner] = rx.field(default_factory=lambda: Owner("Ada"))
    projects: rx.Field[list[Project]] = rx.field(
        default_factory=lambda: [Project("Alpha", 3, featured=True), Project("Beta", 5), Project("Gamma", 8)]
    )
    # The browser receives api_base; a name that starts with an underscore is a
    # backend-only var, which Reflex leaves out of the state it sends to the browser.
    api_base: rx.Field[str] = rx.field("/api")
    _secret_token: str = "s3cr3t"
    # The heading's color, which app.css reads as the CSS variable --accent.
    accent: rx.Field[str] = rx.field("rgb(0, 0, 255)")
    # Cards are hidden in this browser tab's state only; the project list stays the same.
    hidden: rx.Field[list[str]] = rx.field(default_factory=list)

    @rx.event
    def hide(self, title: str) -> None:
        self.hidden.append(title)

    @rx.var
    def visible_projects(self) -> list[Project]:
        return [project for project in self.projects if project.title not in self.hidden]


class CounterState(rx.State):
    count: rx.Field[int] = rx.field(0)

    @rx.event
    def save(self, amount: int) -> None:
        self.count += amount


class DetailsState(rx.State):
    open: rx.Field[bool] = rx.field(False)

    @rx.event
    def toggle(self) -> None:
        self.open = not self.open

    @rx.event
    def close(self) -> None:
        self.open = False


class SearchState(rx.State):
    # The text typed so far, which the line under the field repeats.
    query: rx.Field[str] = rx.field("")
    # The text the search form last submitted.
    searched: rx.Field[str] = rx.field("")

    @rx.event
    def set_query(self, value: str) -> None:
        self.query = value

    # Reflex hands a form's submit handler the form's fields by name.
    @rx.event
    def search(self, form_data: dict[str, Any]) -> None:
        self.searched = form_data["q"]


# ObjectVar lets pyright accept reading a project's fields in the loop.
def project_card(project: ObjectVar[Project]) -> rx.Component:
    return card(
        title=project.title,
        count=project.count,
        tone=rx.cond(project.featured, "accent", "plain"),
        # `.to(str)` gives pyright a string var, which has `lower()`.
        footer=lambda title, count: rx.link(f"Open {title} ({count})", href="#" + title.to(str).lower()),
        # The event already carries this card's title, so the card sends no value of its own.
        on_hide=BoardState.hide(project.title),
    )


def counter() -> rx.Component:
    return rx.box(
        rx.text("Saved: ", CounterState.count),
        rx.button("Add", type="button", on_click=CounterState.save(1)),
    )


def details() -> rx.Component:
    return rx.box(
        rx.button("Details", type="button", aria_expanded=DetailsState.open, on_click=DetailsState.toggle),
        rx.cond(DetailsState.open, rx.text("Details are visible")),
        status(open=DetailsState.open, on_close=DetailsState.close),
    )


def search() -> rx.Component:
    return rx.box(
        rx.form(
            rx.input(name="q", type="search", value=SearchState.query, on_change=SearchState.set_query),
            rx.button("Search", type="submit"),
            rx.text("Searching for: ", SearchState.query),
            role="search",
            on_submit=SearchState.search,
        ),
        rx.cond(SearchState.searched, rx.text("Searched: ", SearchState.searched)),
    )


def index() -> rx.Component:
    return rx.box(
        rx.heading("Projects", as_="h1"),
        rx.box(
            rx.text("Owned by ", BoardState.owner.name),
            rx.image(src="/avatar.svg", alt=BoardState.owner.name, width="32px", height="32px"),
            rx.text("Owner: ", BoardState.owner.name),
            rx.text("API: ", BoardState.api_base),
            rx.box(rx.foreach(BoardState.visible_projects, project_card)),
            counter(),
            details(),
            search(),
            rx.box(rx.link("About", href="/about"), " ", rx.link("Project 1", href="/projects/1")),
            class_name="board",
            title="Board",
        ),
        # The server sets the heading's color, which app.css reads.
        style={"--accent": BoardState.accent},
    )


def about() -> rx.Component:
    return rx.heading("About this board", as_="h1")


def project() -> rx.Component:
    # Reflex turns the route's `[project_id]` part into a state var of that
    # name, which its docs read as `rx.State.project_id`. pyright cannot see a
    # var Reflex adds when the page is registered.
    return rx.heading("Project ", rx.State.project_id, as_="h1")  # pyright: ignore[reportAttributeAccessIssue]


app = rx.App(stylesheets=["/app.css"])
app.add_page(index, title="Projects")
app.add_page(about, route="/about")
app.add_page(project, route="/projects/[project_id]")
