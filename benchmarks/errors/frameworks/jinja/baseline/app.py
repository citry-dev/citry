"""Serve the reference project board with Starlette, Jinja templates, HTMX and Alpine."""

from dataclasses import dataclass

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

# Server configuration. The API base is public and goes to the browser; the
# token is a server secret that no template is given.
API_BASE = "/api"
SECRET_TOKEN = "s3cr3t"
# The heading's color, which the stylesheet reads as the CSS variable --accent.
ACCENT = "rgb(0, 0, 255)"

templates = Jinja2Templates(directory="templates")


@dataclass
class Owner:
    name: str


@dataclass
class Project:
    title: str
    count: int
    # The page draws a featured project's card with the accent border.
    featured: bool


OWNER = Owner(name="Ada")
TASK_COUNTS = {"Alpha": 3, "Beta": 5, "Gamma": 8}


async def homepage(request: Request):
    projects = [
        Project(title=title, count=count, featured=title == "Alpha") for title, count in TASK_COUNTS.items()
    ]
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "owner": OWNER,
            "api_base": API_BASE,
            "accent": ACCENT,
            "projects": projects,
            "count": request.app.state.count,
            # The search form submits back to this page with its text in `q`.
            "searched": request.query_params.get("q", ""),
        },
    )


async def about(request: Request):
    return templates.TemplateResponse(request, "about.html")


async def project(request: Request):
    return templates.TemplateResponse(request, "project.html", {"project_id": request.path_params["project_id"]})


async def save(request: Request):
    # HTMX posts the button's hx-vals as form fields. A form field may also be
    # an uploaded file, so the type checker needs it read as text first.
    form = await request.form()
    request.app.state.count += int(str(form["amount"]))
    # Return only the counter, which HTMX swaps in place of the old one.
    return templates.TemplateResponse(request, "counter.html", {"count": request.app.state.count})


# Starlette's first docs example sets debug=True, which shows a traceback
# page instead of a bare 500 response.
app = Starlette(
    debug=True,
    routes=[
        Route("/", homepage),
        Route("/save", save, methods=["POST"]),
        Route("/about", about, name="about"),
        Route("/projects/{project_id:int}", project, name="project"),
        Mount("/static", app=StaticFiles(directory="static"), name="static"),
    ],
)
# The saved total lives on the application, so every visitor shares it until
# the server stops.
app.state.count = 0
