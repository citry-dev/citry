"""Tests for the Django contrib module: hot reload (``enable_hot_reload``) and the ``secret()`` helper."""

# ruff: noqa: ANN

import sys

import pytest

from citry import Citry, Component


def _loaded_template_component(tmp_path):
    """An engine + component whose template_file is loaded (so it is in the file index)."""
    file_path = tmp_path / "card.html"
    file_path.write_text("<p>v1</p>")
    engine = Citry(dirs=[tmp_path])

    class Card(Component):
        citry = engine
        template_file = "card.html"

    Card.get_template()
    return engine, Card, file_path


def test_invalid_mode_raises_without_django():
    # The mode check runs before Django is imported, so this needs no Django.
    from citry.contrib.django import enable_hot_reload

    with pytest.raises(ValueError, match="mode must be 'hot' or 'restart'"):
        enable_hot_reload(Citry(), mode="nope")  # type: ignore[arg-type]


@pytest.fixture
def hot_reload(monkeypatch):
    """
    Enable hot reload and drive Django's real reloader notification path.

    Yields ``(enable, restarts)``: ``enable(engine, mode)`` calls
    ``enable_hot_reload`` and returns the receiver, and ``restarts`` lists every
    path Django's ``trigger_reload`` was asked to restart for. The process exit
    is replaced with that recording so a test can check a restart without
    ending the test run.
    """
    pytest.importorskip("django")
    from django.dispatch import Signal
    from django.utils import autoreload

    from citry.contrib.django import enable_hot_reload

    # Fresh signals isolate each test: receivers connected here vanish with
    # them, and receivers other tests connected (such as Django's template
    # receivers, which need configured settings) do not run here.
    monkeypatch.setattr(autoreload, "file_changed", Signal())
    monkeypatch.setattr(autoreload, "autoreload_started", Signal())
    restarts = []
    monkeypatch.setattr(autoreload, "trigger_reload", restarts.append)

    def enable(engine, mode="hot"):
        return enable_hot_reload(engine, mode=mode)

    return enable, restarts


def _claim_template_dir(directory):
    """
    Connect a receiver that claims every non-Python file under ``directory``.

    This is what Django's own template receiver does for its template
    directories (``django.template.autoreload.template_changed`` returns True),
    without needing configured Django template settings in the test process.
    """
    from django.utils import autoreload

    def claim(sender, file_path, **kwargs):
        if file_path.suffix != ".py" and directory in file_path.parents:
            return True
        return None

    autoreload.file_changed.connect(claim, weak=False)


def _notify(file_path):
    """Report ``file_path`` as changed the way Django's reloader does."""
    from django.utils.autoreload import BaseReloader

    BaseReloader().notify_file_changed(file_path)


def test_hot_mode_invalidates_and_suppresses_restart(tmp_path, hot_reload):
    enable, restarts = hot_reload
    engine, card, file_path = _loaded_template_component(tmp_path)
    file_path.write_text("<p>v2</p>")

    enable(engine, mode="hot")
    _notify(file_path)

    # The cache is refreshed in place and the server keeps running.
    assert restarts == []
    assert card.get_template().source == "<p>v2</p>"


def test_restart_mode_restarts_on_component_file_change(tmp_path, hot_reload):
    # The usual case, with no other receiver connected. The test below covers
    # the case that used to skip the restart.
    enable, restarts = hot_reload
    engine, card, file_path = _loaded_template_component(tmp_path)
    file_path.write_text("<p>v2</p>")

    enable(engine, mode="restart")
    _notify(file_path)

    assert restarts == [file_path]
    assert card.get_template().source == "<p>v2</p>"


def test_restart_mode_restarts_when_django_template_receiver_claims_the_file(tmp_path, hot_reload):
    enable, restarts = hot_reload
    engine, _, file_path = _loaded_template_component(tmp_path)
    # The component file sits in a Django template directory, so Django's own
    # receiver reports it as handled, which alone would skip the restart.
    _claim_template_dir(tmp_path)
    enable(engine, mode="restart")
    _notify(file_path)

    assert restarts == [file_path]


def test_reloader_watches_engine_dirs(tmp_path, hot_reload):
    from django.utils import autoreload

    enable, _ = hot_reload
    engine, _, file_path = _loaded_template_component(tmp_path)
    nested = tmp_path / "nested" / "badge.css"
    nested.parent.mkdir()
    nested.write_text("b {}")

    enable(engine)
    # Django sends autoreload_started once runserver's reloader is ready.
    reloader = autoreload.BaseReloader()
    autoreload.autoreload_started.send(sender=reloader)
    watched = set(reloader.watched_files())

    # Files under the engine's dirs, at any depth, reach file_changed.
    assert file_path in watched
    assert nested in watched


def test_enabling_twice_keeps_one_setup_and_the_last_mode(tmp_path, hot_reload):
    from django.utils import autoreload

    enable, restarts = hot_reload
    engine, _, file_path = _loaded_template_component(tmp_path)

    enable(engine, mode="hot")
    enable(engine, mode="restart")
    started = autoreload.autoreload_started.send(sender=autoreload.BaseReloader())
    _notify(file_path)

    # One watch receiver per engine, and the second call's restart mode is the
    # one that handles the change.
    assert len(started) == 1
    assert restarts == [file_path]


@pytest.mark.parametrize("mode", ["hot", "restart"])
def test_unloaded_file_under_engine_dirs_keeps_server_running(tmp_path, hot_reload, mode):
    enable, restarts = hot_reload
    engine, _, _ = _loaded_template_component(tmp_path)
    # Neither file backs a loaded component: one is new, one is bytecode
    # Python writes next to imported modules.
    new_file = tmp_path / "not_rendered_yet.html"
    new_file.write_text("<p>new</p>")
    bytecode = tmp_path / "__pycache__" / "card.cpython-312.pyc"
    bytecode.parent.mkdir()
    bytecode.write_bytes(b"")

    enable(engine, mode=mode)
    _notify(new_file)
    _notify(bytecode)

    assert restarts == []


@pytest.mark.parametrize("mode", ["hot", "restart"])
def test_python_file_under_engine_dirs_restarts(tmp_path, hot_reload, mode):
    enable, restarts = hot_reload
    engine, _, _ = _loaded_template_component(tmp_path)
    module = tmp_path / "card.py"
    module.write_text("")

    enable(engine, mode=mode)
    _notify(module)

    assert restarts == [module]


def test_file_outside_engine_dirs_is_left_to_django(tmp_path, hot_reload):
    from django.utils import autoreload

    enable, _ = hot_reload
    engine_dir = tmp_path / "components"
    engine_dir.mkdir()
    engine, _, _ = _loaded_template_component(engine_dir)

    receiver = enable(engine)
    results = autoreload.file_changed.send(sender=None, file_path=tmp_path / "settings.toml")
    ours = [value for recv, value in results if recv is receiver]

    # A file no component loaded, outside the engine's dirs, returns None, so
    # Django's other receivers decide whether to restart.
    assert ours == [None]


def test_secret_reads_the_configured_settings_module(tmp_path, monkeypatch):
    pytest.importorskip("django")
    from django.conf import LazySettings

    from citry.contrib.django import secret

    settings_file = tmp_path / "citry_test_secret_settings.py"
    settings_file.write_text('SECRET_KEY = "key-from-settings-module"\n')
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, "citry_test_secret_settings", raising=False)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "citry_test_secret_settings")
    # A fresh LazySettings object (restored afterwards), so this test neither
    # depends on nor disturbs the process-global Django settings that other
    # tests may have configured.
    monkeypatch.setattr("django.conf.settings", LazySettings())

    assert secret() == "key-from-settings-module"


def test_secret_rides_the_citry_constructor(monkeypatch):
    pytest.importorskip("django")
    from django.conf import LazySettings

    from citry.contrib.django import secret

    fresh = LazySettings()
    fresh.configure(SECRET_KEY="configured-key")  # noqa: S106 - a dummy test secret, not a credential
    monkeypatch.setattr("django.conf.settings", fresh)

    engine = Citry(secret=secret())
    # A bare string normalizes to the one-element rotation form.
    assert engine.settings.secret == ["configured-key"]


def test_secret_error_when_django_is_not_configured(monkeypatch):
    pytest.importorskip("django")
    from django.conf import LazySettings

    from citry.contrib.django import secret

    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)
    monkeypatch.setattr("django.conf.settings", LazySettings())

    with pytest.raises(RuntimeError) as excinfo:
        secret()

    # The error says what failed and names each fix.
    message = str(excinfo.value)
    assert "SECRET_KEY" in message
    assert "DJANGO_SETTINGS_MODULE" in message
    assert "django.conf.settings.configure()" in message
    assert 'Citry(secret="...")' in message


def test_secret_reraises_when_secret_key_is_empty(monkeypatch):
    pytest.importorskip("django")
    from django.conf import LazySettings
    from django.core.exceptions import ImproperlyConfigured

    from citry.contrib.django import secret

    # Settings are configured, but the SECRET_KEY itself is unusable (empty).
    # secret() lets Django's own ImproperlyConfigured through rather than
    # masking it as the not-configured RuntimeError. Only the type is asserted;
    # Django owns the message wording.
    fresh = LazySettings()
    fresh.configure(SECRET_KEY="")
    monkeypatch.setattr("django.conf.settings", fresh)

    with pytest.raises(ImproperlyConfigured):
        secret()
