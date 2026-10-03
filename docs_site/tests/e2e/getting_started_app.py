"""
Serve the getting-started tutorial to the browser tests, one step per server.

From the FastAPI step on, the tutorial has the reader keep `citry_setup.py`
and `app.py` and replace `components.py` at every step. Each server here does
the same: `CITRY_GETTING_STARTED_STEP` picks the `components_step<N>.py` file
that plays `components.py`, and the tutorial's own `app.py` serves it, so the
test runs the files the reader runs. Steps reuse component names and step 13
keeps its tasks in a module-level list, so every step gets its own process.

The earlier steps are browser-only examples that the docs run in the in-page
playground. `CITRY_GETTING_STARTED_STEP=live` serves those files from this
checkout instead, so they run against this checkout's Citry rather than the
release the playground pins.
"""

from __future__ import annotations

import importlib
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from citry import Citry
from citry.contrib.fastapi import mount

if TYPE_CHECKING:
    from citry.citry_element import CitryElement

_DOCS_SITE = Path(__file__).resolve().parents[2]
_SNIPPETS = _DOCS_SITE / "snippets" / "getting_started"
_LIVE_SNIPPETS = _DOCS_SITE / "live_snippets"

# Each browser-only example: its file, and the name of the value it renders.
LIVE_EXAMPLES = {
    "reading_list": "reading_list",
    "reading_panel": "page",
    "click_counters": "page",
    "connected_components": "page",
}


def _page_route(element: CitryElement) -> Callable[[], HTMLResponse]:
    # The file builds its element once; build a fresh one for every request
    # from the same class and inputs, as a playground reload does.
    def show() -> HTMLResponse:
        return HTMLResponse(str(element.comp_cls(**element.kwargs)))

    return show


def _live_app() -> FastAPI:
    engine = Citry(secret="docs-getting-started-live-secret", autodiscover=False)  # noqa: S106

    def run(name: str) -> dict[str, Any]:
        # The playground supplies the Citry instance, so the files declare none;
        # give every component class this server's instance before running it.
        source = (_LIVE_SNIPPETS / f"{name}.py").read_text(encoding="utf-8")
        source = re.sub(
            r"^class (\w+)\(Component\):$",
            r"class \1(Component):\n    citry = live_engine",
            source,
            flags=re.MULTILINE,
        )
        namespace: dict[str, Any] = {"live_engine": engine}
        exec(compile(source, f"docs_site/live_snippets/{name}.py", "exec"), namespace)  # noqa: S102
        return namespace

    app = FastAPI()
    welcome_card = run("welcome")["WelcomeCard"]

    @app.get("/welcome")
    def welcome() -> HTMLResponse:
        return HTMLResponse(str(welcome_card(name="ada lovelace", accent="#6f42c1")))

    for name, value in LIVE_EXAMPLES.items():
        app.get(f"/{name}")(_page_route(run(name)[value]))

    # Without a lifespan, set up the instance before the first request here.
    engine.initialize()
    mount(app, engine)
    return app


def _tutorial_app(step: str) -> FastAPI:
    # `app.py` imports `components` and `citry_setup` from its own folder.
    sys.path.insert(0, str(_SNIPPETS))
    sys.modules["components"] = importlib.import_module(f"components_step{step}")
    tutorial = importlib.import_module("app")
    return tutorial.app


_STEP = os.environ.get("CITRY_GETTING_STARTED_STEP", "13")
app = _live_app() if _STEP == "live" else _tutorial_app(_STEP)
