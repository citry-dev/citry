from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from citry_setup import citry_app
from components import TutorialPage
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from citry.contrib.fastapi import mount


# New in this step: initialize Citry before serving requests.
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    citry_app.initialize()
    yield


app = FastAPI(lifespan=lifespan)


# New in this step: render a Citry page from a regular route.
@app.get("/")
def home() -> HTMLResponse:
    page = str(TutorialPage())
    return HTMLResponse(page)


# New in this step: add Citry's browser and event routes.
mount(app, citry_app)
