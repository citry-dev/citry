from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.citry_app import citry_app
from app.components.about_page import AboutPage
from app.components.board_page import BoardPage
from app.components.project_page import ProjectPage
from app.data import OWNER, PROJECTS
from citry.contrib.fastapi import mount

STATIC_DIR = Path(__file__).resolve().parent / "static"


# Uvicorn runs the lifespan before it serves a request, so initialize() has
# found every component in app/components/ before the first page renders.
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    citry_app.initialize()
    yield


web_app = FastAPI(lifespan=lifespan)


@web_app.get("/", response_class=HTMLResponse)
def board() -> HTMLResponse:
    return HTMLResponse(str(BoardPage(owner=OWNER, projects=PROJECTS)))


@web_app.get("/about", response_class=HTMLResponse)
def about() -> HTMLResponse:
    return HTMLResponse(str(AboutPage()))


# The project route takes the project's number, so FastAPI answers a link
# such as /projects/alpha with an error response instead of a page.
@web_app.get("/projects/{project_id}", response_class=HTMLResponse)
def project(project_id: int) -> HTMLResponse:
    return HTMLResponse(str(ProjectPage(project_id=project_id)))


# Serve app/static/, which holds the images the pages link to, such as the
# owner's avatar.
web_app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# The pages load Citry's browser code from /citry, and server events are sent there.
mount(web_app, citry_app, prefix="/citry")
