"""The preview CLI owns serving, selection, and aggregate failure status."""

import pytest

from citry import Citry, Component
from citry.command import run
from citry.ext.preview import PreviewExtension, commands, variant


def _app():
    app = Citry(extensions=[PreviewExtension])

    class Button(Component):
        citry = app
        template = """
            <button>Save</button>
        """

        class Preview:
            def variants(self):
                return [variant(slug="small", label="Small"), variant(slug="large", label="Large")]

    return app


class _Server:
    def __init__(self, app, routes, *, port=0):
        self.app = app
        self.base_url = f"http://127.0.0.1:{port or 8001}/citry"
        self.closed = False

    def __enter__(self):
        self.app.set_mounted_prefix("/citry")
        return self

    def __exit__(self, *args):
        self.closed = True

    def wait(self):
        raise KeyboardInterrupt


def test_serve_only_starts_host_and_stops_on_interrupt(monkeypatch, capsys):
    servers = []

    def server(*args, **kwargs):
        result = _Server(*args, **kwargs)
        servers.append(result)
        return result

    monkeypatch.setattr(commands, "PreviewServer", server)
    monkeypatch.setattr(commands, "capture", lambda *_args, **_kwargs: pytest.fail("serve started capture"))
    monkeypatch.setattr(commands, "preflight", lambda *_args, **_kwargs: pytest.fail("serve checked browser"))
    assert run(commands.ServeCommand, ["Button", "--variant", "small", "--port", "1234"], citry=_app()) == 0
    assert servers[0].closed
    assert "http://127.0.0.1:1234/citry/ext/preview/gallery" in capsys.readouterr().out


def test_capture_preflights_before_starting_owned_host(monkeypatch, tmp_path):
    events = []
    monkeypatch.setattr(commands, "preflight", lambda *_args, **_kwargs: events.append("preflight"))

    def server(*args, **kwargs):
        events.append("host")
        return _Server(*args, **kwargs)

    def capture(catalog, base_url, outdir, **kwargs):
        assert [v["slug"] for v in catalog["components"][0]["variants"]] == ["small"]
        events.append("capture")
        return {"captures": [1]}

    monkeypatch.setattr(commands, "PreviewServer", server)
    monkeypatch.setattr(commands, "capture", capture)
    assert run(commands.RenderCommand, ["Button", "--variant", "small", "-o", str(tmp_path)], citry=_app()) == 0
    assert events == ["preflight", "host", "capture"]


@pytest.mark.parametrize("args", [["Missing"], ["Button,,"], ["--variant", "missing"], ["--timeout", "nan"]])
def test_invalid_capture_selection_fails_before_host(monkeypatch, args):
    monkeypatch.setattr(commands, "PreviewServer", lambda *_args, **_kwargs: pytest.fail("started host"))
    with pytest.raises(SystemExit) as error:
        run(commands.RenderCommand, args, citry=_app())
    assert error.value.code == 1


def test_preflight_failure_never_starts_server(monkeypatch):
    def fail(*args, **kwargs):
        raise FileExistsError("existing image")

    monkeypatch.setattr(commands, "preflight", fail)
    monkeypatch.setattr(commands, "PreviewServer", lambda *_args, **_kwargs: pytest.fail("started host"))
    with pytest.raises(SystemExit) as error:
        run(commands.RenderCommand, [], citry=_app())
    assert error.value.code == 1


def test_remote_capture_does_not_mount_local_engine(monkeypatch):
    app = _app()
    renderer = commands._renderer(type("Command", (), {"citry": app})(), None, None, None)
    catalog = renderer.catalog(urls=False)
    for component in catalog["components"]:
        for value in component["variants"]:
            value["url"] = "/citry/ext/preview/render/example?variant=" + value["slug"]
    monkeypatch.setattr(commands, "preflight", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(commands, "fetch_catalog", lambda *_args: catalog)
    monkeypatch.setattr(commands, "capture", lambda *_args, **_kwargs: {"captures": [1, 2]})
    monkeypatch.setattr(commands, "PreviewServer", lambda *_args, **_kwargs: pytest.fail("started host"))
    assert run(commands.RenderCommand, ["--base-url", "http://localhost:8001/citry"], citry=app) == 0
    assert app.mounted_prefix is None


def test_empty_capture_needs_no_browser_or_server(monkeypatch, capsys):
    monkeypatch.setattr(commands, "preflight", lambda *_args, **_kwargs: pytest.fail("checked browser"))
    assert run(commands.RenderCommand, [], citry=Citry(extensions=[PreviewExtension])) == 0
    assert "No component previews" in capsys.readouterr().out
