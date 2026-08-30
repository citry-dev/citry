from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.citry_app import citry_app
from app.components.project_page import ProjectPage
from app.data import find_projects
from citry.contrib.fastapi import mount


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    citry_app.initialize()
    yield


web_app = FastAPI(lifespan=lifespan)


@web_app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    html = str(ProjectPage(projects=find_projects()))
    return HTMLResponse(html)


mount(web_app, citry_app, prefix="/citry")
