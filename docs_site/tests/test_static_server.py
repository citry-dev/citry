"""Tests for the headers used by local/static docs previews."""

from __future__ import annotations

import functools
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from docs_site._internal.static_server import StaticSiteHandler, headers_for_static_path


def test_only_content_addressed_prepared_assets_allow_opaque_origins() -> None:
    header = ("Access-Control-Allow-Origin", "*")

    assert headers_for_static_path("/citry/ext/events/assets/" + "a" * 64 + ".css") == (header,)
    assert headers_for_static_path("/citry/ext/events/definitions/" + "b" * 64 + ".js") == (header,)
    assert headers_for_static_path("/citry/ext/events/call") == ()
    assert headers_for_static_path("/citry/citry.js") == ()
    assert headers_for_static_path("/citry/ext/events/assets/" + "a" * 64 + ".css?cache=1") == (header,)
    assert headers_for_static_path("/citry/ext/events/assets/../" + "a" * 64 + ".css") == ()


def test_static_site_handler_emits_cors_only_for_prepared_assets(tmp_path: Path) -> None:
    digest = "c" * 64
    asset = tmp_path / "citry" / "ext" / "events" / "assets" / f"{digest}.css"
    asset.parent.mkdir(parents=True)
    asset.write_text(".preview { color: red; }", encoding="utf-8")
    runtime = tmp_path / "citry" / "citry.js"
    runtime.write_text("runtime", encoding="utf-8")
    handler = functools.partial(StaticSiteHandler, directory=str(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urlopen(f"{base_url}/citry/ext/events/assets/{digest}.css", timeout=2) as response:  # noqa: S310
            assert response.headers["Access-Control-Allow-Origin"] == "*"
        with urlopen(f"{base_url}/citry/citry.js", timeout=2) as response:  # noqa: S310
            assert response.headers.get("Access-Control-Allow-Origin") is None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
