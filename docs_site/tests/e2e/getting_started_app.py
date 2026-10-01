"""Local ASGI app for the finished getting-started tutorial browser test."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from citry import Citry
from citry.contrib.fastapi import mount

_SNIPPETS = Path(__file__).resolve().parents[2] / "snippets" / "getting_started"
sys.path.insert(0, str(_SNIPPETS))
import components_step13 as tutorial  # noqa: E402


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    tutorial.citry_app.initialize()
    welcome_engine.initialize()
    yield


app = FastAPI(lifespan=lifespan)

welcome_engine = Citry(secret="docs-welcome-browser-test-secret", autodiscover=False)  # noqa: S106
welcome_engine.set_mounted_prefix("/welcome-citry")
welcome_source = (
    (Path(__file__).resolve().parents[2] / "live_snippets" / "welcome.py")
    .read_text(encoding="utf-8")
    .replace("class WelcomeCard(Component):", "class WelcomeCard(Component):\n    citry = welcome_engine", 1)
)
welcome_namespace = {"welcome_engine": welcome_engine}
exec(compile(welcome_source, "docs_site/live_snippets/welcome.py", "exec"), welcome_namespace)  # noqa: S102
MountedWelcomeCard = welcome_namespace["WelcomeCard"]


@app.get("/")
def home() -> HTMLResponse:
    return HTMLResponse(str(tutorial.TutorialPage()))


@app.get("/welcome")
def welcome() -> HTMLResponse:
    return HTMLResponse(str(MountedWelcomeCard(name="ada lovelace", accent="#6f42c1")))


mount(app, tutorial.citry_app)
mount(app, welcome_engine, prefix="/welcome-citry")
