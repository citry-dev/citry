from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.citry_app import citry_app
from app.routes import router
from citry.contrib.fastapi import mount

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

STATIC_DIR = Path(__file__).with_name("static")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    citry_app.initialize()
    yield


web_app = FastAPI(lifespan=lifespan)
web_app.include_router(router)
web_app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
mount(web_app, citry_app, prefix="/citry")
