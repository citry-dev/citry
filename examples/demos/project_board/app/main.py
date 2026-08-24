from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from citry.contrib.fastapi import mount

from .citry_app import citry_app
from .components import BoardPage
from .store import board_snapshot


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    citry_app.initialize()
    yield


web_app = FastAPI(lifespan=lifespan)


@web_app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return HTMLResponse(str(BoardPage(lanes=board_snapshot())))


mount(web_app, citry_app, prefix="/citry")
