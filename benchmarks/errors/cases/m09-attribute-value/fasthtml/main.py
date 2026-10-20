"""The error benchmark's reference page, written the way the FastHTML docs write an app."""

import json
from dataclasses import dataclass

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


@dataclass
class Owner:
    name: str


@dataclass
class Project:
    title: str
    count: int


owner = Owner("Ada")
projects = [Project("Alpha", 3), Project("Beta", 5), Project("Gamma", 8)]
count = 0


# This page's own card. It replaces the Pico `Card` that the star import brings in.
def Card(title: str, count: int, footer):
    return Article(
        H3(title),
        P(f"{title}: {count} tasks"),
        Footer(footer),
        # The card only announces the click; the page decides what hiding means.
        Button("Hide", onclick="this.dispatchEvent(new CustomEvent('hide', {bubbles: true}))"),
        cls="card",
    )


@rt("/")
def get():
    return Title("Projects"), Div(
        H1("Projects"),
        P(f"Owner: {owner.name}"),
        P(id="api"),
        Script(f"document.getElementById('api').textContent = 'API: ' + {json.dumps(API_BASE)};"),
        *[
            Card(title=p.title, count=p.count, footer=A(f"Open {p.title}", href=f"#{p.title.lower()}"))
            for p in projects
        ],
        P(f"Saved: {count}", id="saved"),
        # FastHTML's type hints take hx_vals as a JSON string.
        Button("Add", hx_post="/save", hx_vals=json.dumps({"amount": 1}), hx_target="#saved"),
        Button("Details", onclick="toggleDetails()"),
        P("Details are visible", id="details", hidden=True),
        Script("""
            let open = false;
            function toggleDetails() {
                open = !open;
                document.getElementById('details').hidden = !open;
            }
            // The card's hide event bubbles up to the page, which hides that card.
            document.addEventListener('hide', (event) => {
                event.target.closest('.card').hidden = true;
            });
        """),
        Form(Button("Search", type="sumbit"), role="search"),
        cls="board",
        title="Board",
    )


@rt("/save")
def post(amount: int):
    global count
    count += amount
    return f"Saved: {count}"


serve()
