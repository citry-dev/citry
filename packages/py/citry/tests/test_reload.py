"""Tests for hot reload: the invalidate_file primitive, the watcher, and ``citry watch``."""

# ruff: noqa: ANN

import os
import threading
import time
from pathlib import Path

import pytest

from citry import Citry, Component
from citry.command import run
from citry.commands import build_cli
from citry.reload import (
    PollingWatcher,
    WatchdogWatcher,
    WatchfilesWatcher,
    default_watcher,
    watch,
)


def _engine_with_template_component(tmp_path, *, source="<p>v1</p>"):
    """A Citry with one component whose template_file is in tmp_path, already loaded."""
    file_path = tmp_path / "card.html"
    file_path.write_text(source)
    engine = Citry(dirs=[tmp_path])

    class Card(Component):
        citry = engine
        template_file = "card.html"

    # Resolve once so the file lands in the reverse index (it is populated lazily).
    Card.get_template()
    return engine, Card, file_path


class _FakeWatcher:
    """A FileWatcher that emits preset path batches then returns (deterministic, no threads of its own)."""

    def __init__(self, batches):
        self._batches = batches
        self.stopped = False

    def run(self, roots, on_change):
        for batch in self._batches:
            on_change(set(batch))

    def stop(self):
        self.stopped = True


class _BlockingWatcher:
    """A FileWatcher that blocks in run() until stopped, so start/stop is observable."""

    def __init__(self):
        self.run_started = threading.Event()
        self.stopped = threading.Event()

    def run(self, roots, on_change):
        self.run_started.set()
        self.stopped.wait()

    def stop(self):
        self.stopped.set()


def _assert_backend_reloads(tmp_path, watcher):
    """Run a real watcher backend: load a template, change the file, confirm the next read is fresh."""
    engine, card, file_path = _engine_with_template_component(tmp_path)
    reloaded = threading.Event()

    def on_reload(_changed, reset):
        if reset:
            reloaded.set()

    handle = watch(engine, roots=[tmp_path], watcher=watcher, on_reload=on_reload)
    try:
        time.sleep(0.4)  # let the native watcher establish its baseline
        file_path.write_text("<p>v2</p>")
        assert reloaded.wait(5.0), "watcher did not report the change in time"
    finally:
        handle.stop()
    assert card.get_template().source == "<p>v2</p>"


class TestInvalidateFile:
    def test_resets_loaded_component_and_returns_it(self, tmp_path):
        engine, card, file_path = _engine_with_template_component(tmp_path)
        assert engine.get_components_for_file(file_path) == [card]

        file_path.write_text("<p>v2</p>")
        # Until invalidation the cached template is the stale first read.
        assert card.get_template().source == "<p>v1</p>"

        reset = engine.invalidate_file(file_path)
        assert reset == [card]
        assert card.get_template().source == "<p>v2</p>"

    def test_unknown_file_returns_empty(self, tmp_path):
        engine, _, _ = _engine_with_template_component(tmp_path)
        assert engine.invalidate_file(tmp_path / "never-loaded.html") == []

    def test_accepts_a_string_path(self, tmp_path):
        engine, card, file_path = _engine_with_template_component(tmp_path)
        file_path.write_text("<p>v2</p>")
        assert engine.invalidate_file(str(file_path)) == [card]
        assert card.get_template().source == "<p>v2</p>"

    def test_resets_js_files_too(self, tmp_path):
        js_path = tmp_path / "card.js"
        js_path.write_text("console.log('v1');")
        engine = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = engine
            js_file = "card.js"

        assert Card.get_js() == "console.log('v1');"
        js_path.write_text("console.log('v2');")

        reset = engine.invalidate_file(js_path)
        assert reset == [Card]
        assert Card.get_js() == "console.log('v2');"


class TestWatch:
    def test_invalidates_changed_files(self, tmp_path):
        engine, card, file_path = _engine_with_template_component(tmp_path)
        file_path.write_text("<p>v2</p>")

        seen = {}

        def on_reload(changed, reset):
            seen["changed"] = changed
            seen["reset"] = reset

        handle = watch(engine, roots=[tmp_path], watcher=_FakeWatcher([[file_path]]), on_reload=on_reload)
        handle.wait()  # the fake watcher returns after emitting its one batch

        assert seen["changed"] == {file_path}
        assert seen["reset"] == [card]
        assert card.get_template().source == "<p>v2</p>"

    def test_requires_directories_to_watch(self, tmp_path):
        engine = Citry()  # no dirs configured, and none passed
        with pytest.raises(ValueError, match="no directories to watch"):
            watch(engine)

    def test_falls_back_to_engine_dirs(self, tmp_path):
        engine, card, file_path = _engine_with_template_component(tmp_path)
        file_path.write_text("<p>v2</p>")
        # roots omitted -> uses engine.settings.dirs (tmp_path).
        handle = watch(engine, watcher=_FakeWatcher([[file_path]]))
        handle.wait()
        assert card.get_template().source == "<p>v2</p>"

    def test_stop_signals_the_watcher(self, tmp_path):
        engine, _, _ = _engine_with_template_component(tmp_path)
        fake = _FakeWatcher([])
        handle = watch(engine, roots=[tmp_path], watcher=fake)
        handle.wait()
        handle.stop()
        assert fake.stopped is True


class TestPollingWatcher:
    def test_diff_detects_modified_file(self, tmp_path):
        file_path = tmp_path / "a.html"
        file_path.write_text("1")
        poller = PollingWatcher()

        before = poller._snapshot([tmp_path])
        assert file_path in before

        # Force a later mtime rather than relying on filesystem timing.
        os.utime(file_path, (before[file_path] + 10, before[file_path] + 10))
        after = poller._snapshot([tmp_path])
        assert poller._diff(before, after) == {file_path}

    def test_diff_detects_added_and_removed(self, tmp_path):
        poller = PollingWatcher()
        first = tmp_path / "a.html"
        first.write_text("1")
        before = poller._snapshot([tmp_path])

        second = tmp_path / "b.html"
        second.write_text("2")
        after_add = poller._snapshot([tmp_path])
        assert second in poller._diff(before, after_add)

        first.unlink()
        after_remove = poller._snapshot([tmp_path])
        assert first in poller._diff(after_add, after_remove)


class TestDefaultWatcher:
    def test_returns_a_usable_watcher(self):
        # watchfiles/watchdog may or may not be installed; either way the result
        # is a FileWatcher with the run/stop pair the protocol promises.
        chosen = default_watcher()
        assert callable(chosen.run)
        assert callable(chosen.stop)

    def test_prefers_watchfiles_then_watchdog_then_polling(self, monkeypatch):
        from citry import reload as reload_mod

        available: set[str] = set()
        monkeypatch.setattr(reload_mod, "_module_installed", lambda name: name in available)

        available = {"watchfiles", "watchdog"}
        assert isinstance(reload_mod.default_watcher(), WatchfilesWatcher)
        available = {"watchdog"}
        assert isinstance(reload_mod.default_watcher(), WatchdogWatcher)
        available = set()
        assert isinstance(reload_mod.default_watcher(), PollingWatcher)


class TestWatchCommand:
    def test_no_directories_exits_with_message(self, capsys):
        engine = Citry()
        with pytest.raises(SystemExit):
            run(build_cli(engine), ["watch"], citry=engine)
        assert "no directories to watch" in capsys.readouterr().out

    def test_runs_watcher_and_stops(self, monkeypatch, tmp_path, capsys):
        calls = {}

        class FakeHandle:
            def wait(self):
                calls["waited"] = True

            def stop(self):
                calls["stopped"] = True

        def fake_watch(engine, *, roots=None, on_reload=None):
            calls["engine"] = engine
            calls["roots"] = roots
            # Simulate one reload so the command's reporting path runs.
            if on_reload is not None:
                on_reload({Path("card.html")}, [])
            return FakeHandle()

        monkeypatch.setattr("citry.commands.watch.watch", fake_watch)
        engine = Citry(dirs=[tmp_path])

        code = run(build_cli(engine), ["watch", "--path", str(tmp_path)], citry=engine)

        assert code == 0
        assert calls["engine"] is engine
        assert calls["roots"] == [tmp_path]
        assert calls["waited"] is True
        assert calls["stopped"] is True
        out = capsys.readouterr().out
        assert "watching" in out
        assert "reloaded card.html" in out


class TestInvalidateAll:
    def test_resets_every_loaded_component(self, tmp_path):
        (tmp_path / "a.html").write_text("<p>a1</p>")
        (tmp_path / "b.html").write_text("<p>b1</p>")
        engine = Citry(dirs=[tmp_path])

        class A(Component):
            citry = engine
            template_file = "a.html"

        class B(Component):
            citry = engine
            template_file = "b.html"

        A.get_template()
        B.get_template()
        (tmp_path / "a.html").write_text("<p>a2</p>")
        (tmp_path / "b.html").write_text("<p>b2</p>")

        reset = engine.invalidate_all()
        assert set(reset) == {A, B}
        assert A.get_template().source == "<p>a2</p>"
        assert B.get_template().source == "<p>b2</p>"

    def test_empty_when_nothing_loaded(self):
        assert Citry().invalidate_all() == []


class TestReloadLifespan:
    def test_starts_on_startup_stops_on_shutdown(self, tmp_path):
        fastapi = pytest.importorskip("fastapi")
        pytest.importorskip("httpx")
        from fastapi.testclient import TestClient

        from citry.contrib.asgi import reload_lifespan

        engine, _, _ = _engine_with_template_component(tmp_path)
        watcher = _BlockingWatcher()
        app = fastapi.FastAPI(lifespan=reload_lifespan(engine, roots=[tmp_path], watcher=watcher))

        assert not watcher.run_started.is_set()
        with TestClient(app):
            assert watcher.run_started.wait(2.0)  # startup started the watcher
            assert not watcher.stopped.is_set()
        assert watcher.stopped.is_set()  # shutdown stopped it


class TestNativeBackends:
    """Integration tests against the real watcher libraries; skipped when they are absent."""

    def test_watchfiles_backend_reloads(self, tmp_path):
        pytest.importorskip("watchfiles")
        _assert_backend_reloads(tmp_path, WatchfilesWatcher())

    def test_watchdog_backend_reloads(self, tmp_path):
        pytest.importorskip("watchdog")
        _assert_backend_reloads(tmp_path, WatchdogWatcher())
