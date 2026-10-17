"""Serve the prebuilt Reflex frontend and native backend on the reserved origin."""

# Reflex reads configuration at import; set the owned environment first.
# ruff: noqa: E402

import os

from configuration import configure_environment, validate_configuration

# Production launch loads only the prepared Python app; frontend compilation is separate.
configure_environment(compile_frontend=False)

from audit import (
    ObserveTransport,
    install_preparation_timing,
    instrument_board_preparation,
    report,
    validate_preparation_application,
)

install_preparation_timing()

from board_app import board_app

instrument_board_preparation(board_app)
app = board_app.app
validate_preparation_application(app)
from reflex.config import get_config
from reflex.utils.path_ops import get_bun_path, get_node_path
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles


async def health(_request: Request) -> PlainTextResponse:
    return PlainTextResponse(os.environ.get("CITRY_BENCH_SERVER_NONCE", "ok"))


async def operations(request: Request) -> JSONResponse:
    return JSONResponse(report(request.query_params.get("session", "manual")))


def host(backend: Starlette) -> Starlette:
    # Static export is Reflex's documented self-hosting output. Identity encoding
    # is the current profile, so this host serves the original assets directly.
    backend.routes.insert(0, Route("/health", health))
    backend.routes.insert(0, Route("/__bench/operations", operations))
    backend.routes.append(Mount("/", StaticFiles(directory=".web/build/client", html=True)))
    return backend


validate_configuration(get_config(), get_node_path(), get_bun_path())
app.api_transformer = host
application = ObserveTransport(app())
