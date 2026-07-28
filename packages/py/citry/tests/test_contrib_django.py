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


def test_hot_mode_invalidates_and_suppresses_restart(tmp_path):
    pytest.importorskip("django")
    from django.utils.autoreload import file_changed

    from citry.contrib.django import enable_hot_reload

    engine, card, file_path = _loaded_template_component(tmp_path)
    file_path.write_text("<p>v2</p>")

    receiver = enable_hot_reload(engine, mode="hot")
    try:
        results = file_changed.send_robust(sender=None, file_path=file_path)
        ours = [value for recv, value in results if recv is receiver]
    finally:
        file_changed.disconnect(receiver)

    # hot mode returns True, which tells Django's autoreloader the change was
    # handled (no process restart), and the cache is refreshed in place.
    assert ours == [True]
    assert card.get_template().source == "<p>v2</p>"


def test_restart_mode_invalidates_but_lets_django_restart(tmp_path):
    pytest.importorskip("django")
    from django.utils.autoreload import file_changed

    from citry.contrib.django import enable_hot_reload

    engine, card, file_path = _loaded_template_component(tmp_path)
    file_path.write_text("<p>v2</p>")

    receiver = enable_hot_reload(engine, mode="restart")
    try:
        results = file_changed.send_robust(sender=None, file_path=file_path)
        ours = [value for recv, value in results if recv is receiver]
    finally:
        file_changed.disconnect(receiver)

    # restart mode returns None so Django falls through to its own restart, but
    # the caches are still cleared first.
    assert ours == [None]
    assert card.get_template().source == "<p>v2</p>"


def test_unknown_file_is_left_to_django(tmp_path):
    pytest.importorskip("django")
    from django.utils.autoreload import file_changed

    from citry.contrib.django import enable_hot_reload

    engine, _, _ = _loaded_template_component(tmp_path)

    receiver = enable_hot_reload(engine, mode="hot")
    try:
        results = file_changed.send_robust(sender=None, file_path=tmp_path / "unrelated.py")
        ours = [value for recv, value in results if recv is receiver]
    finally:
        file_changed.disconnect(receiver)

    # A file no component loaded returns None, so Django decides what to do.
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
