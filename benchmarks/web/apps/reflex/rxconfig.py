"""Pin the compiled frontend to the reserved local adapter origin."""

import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin

config = rx.Config(
    app_name="board_app",
    api_url="http://127.0.0.1:8917",
    deploy_url="http://127.0.0.1:8917",
    backend_port=8917,
    telemetry_enabled=False,
    frozen_lockfile=True,
    transport="websocket",
    state_manager_mode="memory",
    cors_allowed_origins=["http://127.0.0.1:8917"],
    disable_plugins=[SitemapPlugin],
)
