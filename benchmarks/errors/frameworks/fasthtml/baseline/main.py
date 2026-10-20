"""The error benchmark's reference page, written the way the FastHTML docs write an app."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

# FastHTML apps import its whole namespace, which ruff's default rules
# flag at every use; a project that adds ruff silences that once here.
# ruff: noqa: F403, F405
from fasthtml.common import *

# fast_app() normally loads these from a CDN. The same files, at the same
# versions, are served from static/ so a run works offline and repeats exactly.
hdrs = (
    Meta(charset="utf-8"),
    Meta(name="viewport", content="width=device-width, initial-scale=1, viewport-fit=cover"),
    Script(src="/static/htmx.js"),
    Script(src="/static/fasthtml.js"),
    Script(src="/static/surreal.js"),
    Script(src="/static/css-scope-inline.js"),
    Link(rel="stylesheet", href="/static/pico.min.css"),
    # The page's own stylesheet, which makes the board text green.
    Link(rel="stylesheet", href="/static/app.css"),
)
app, rt = fast_app(default_hdrs=False, hdrs=hdrs)

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
count = 0


# This page's own card. It replaces the Pico `Card` that the star import brings in.
# The card hands its title and count to `footer`, which builds the footer link.
def Card(title: str, count: int, tone: Literal["plain", "accent"], footer: Callable[[str, int], FT]):
    return Article(
        H3(title),
        P(f"{title}: {count} tasks"),
        Footer(footer(title, count)),
        # The card only announces the click; the page decides what hiding means.
        Button("Hide", onclick="this.dispatchEvent(new CustomEvent('hide', {bubbles: true}))"),
        cls=f"card card--{tone}",
    )


# The search form submits back to this page with its text in `q`.
@rt("/")
def get(q: str = ""):
    return Title("Projects"), Div(
        H1("Projects"),
        P(f"Owned by {owner.name}"),
        Img(src="/static/avatar.svg", alt=owner.name, width="32", height="32"),
        P(f"Owner: {owner.name}"),
        P(id="api"),
        Script(f"document.getElementById('api').textContent = 'API: ' + {json.dumps(API_BASE)};"),
        *[
            Card(
                title=p.title,
                count=p.count,
                tone="accent" if p.featured else "plain",
                footer=lambda title, count: A(f"Open {title} ({count})", href=f"#{title.lower()}"),
            )
            for p in projects
        ],
        P(f"Saved: {count}", id="saved"),
        # FastHTML's type hints take hx_vals as a JSON string.
        Button("Add", hx_post="/save", hx_vals=json.dumps({"amount": 1}), hx_target="#saved"),
        Button("Details", onclick="toggleDetails()", id="details-button", aria_expanded="false"),
        P("Details are visible", id="details", hidden=True),
        Script("""
            let open = false;
            function toggleDetails() {
                open = !open;
                document.getElementById('details').hidden = !open;
                document.getElementById('details-button').setAttribute('aria-expanded', String(open));
            }
            // The card's hide event bubbles up to the page, which hides that card.
            document.addEventListener('hide', (event) => {
                event.target.closest('.card').hidden = true;
            });
        """),
        Form(
            Input(
                type="search",
                name="q",
                oninput="document.getElementById('query').textContent = this.value",
            ),
            Button("Search", type="submit"),
            P("Searching for: ", Span(id="query")),
            role="search",
        ),
        P(f"Searched: {q}") if q else None,
        Nav(A("About", href="/about"), A("Project 1", href="/projects/1")),
        cls="board",
        title="Board",
        style=f"--accent: {ACCENT}",
    )


@rt("/about")
def about():
    return Title("About"), H1("About this board")


@rt("/projects/{project_id}")
def project(project_id: int):
    return Title("Project"), H1(f"Project {project_id}")


@rt("/save")
def post(amount: int):
    global count
    count += amount
    return f"Saved: {count}"


serve()
