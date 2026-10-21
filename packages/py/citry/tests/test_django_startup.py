"""`citry --app` starts Django first when DJANGO_SETTINGS_MODULE is set, so a URL configuration can import models."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import types
from typing import TYPE_CHECKING

import pytest

from citry import _django_startup
from citry._app_selection import AppSelectionError, load_app

if TYPE_CHECKING:
    from pathlib import Path


def _write_django_project(root: Path) -> None:
    """Write a Django project whose URL configuration imports a model through its views, as most do."""
    (root / "proj_settings.py").write_text(
        "SECRET_KEY = 'test-only'\nROOT_URLCONF = 'proj_urls'\nINSTALLED_APPS = ['notes']\n",
        encoding="utf-8",
    )
    (root / "notes").mkdir()
    (root / "notes" / "__init__.py").write_text("", encoding="utf-8")
    (root / "notes" / "models.py").write_text(
        "from django.db import models\n\n\nclass Note(models.Model):\n    text = models.TextField()\n",
        encoding="utf-8",
    )
    (root / "notes" / "views.py").write_text(
        "from django.http import HttpResponse\n"
        "from notes.models import Note\n\n\n"
        "def home(request):\n"
        "    return HttpResponse(Note._meta.label)\n",
        encoding="utf-8",
    )
    (root / "proj_urls.py").write_text(
        textwrap.dedent(
            '''
            from django.urls import include, path
            from notes.views import home

            from citry import Citry, Component
            from citry.contrib.django import urlpatterns as citry_urlpatterns

            engine = Citry(autodiscover=False)


            class Page(Component):
                citry = engine
                template = """
                  <a href="/">Home</a>
                  <a href="/nope">Missing</a>
                """


            urlpatterns = [
                path("", home),
                path("citry/", include(citry_urlpatterns(engine, prefix="/citry"))),
            ]
            '''
        ),
        encoding="utf-8",
    )


def _run_check(root: Path, settings_module: str) -> subprocess.CompletedProcess[str]:
    """Run `citry --app proj_urls:engine check` in a fresh process, counting django.setup() calls."""
    # The count shows the CLI and the Django link checker share one startup.
    script = textwrap.dedent(
        """
        import sys

        import django

        calls = []
        original_setup = django.setup


        def counting_setup(*args, **kwargs):
            calls.append(1)
            return original_setup(*args, **kwargs)


        django.setup = counting_setup

        from citry.__main__ import main

        code = main(["--app", "proj_urls:engine", "check"])
        print(f"setup-calls={len(calls)}")
        sys.exit(code)
        """
    )
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=root,
        env={**os.environ, "DJANGO_SETTINGS_MODULE": settings_module, "PYTHONPATH": str(root)},
        capture_output=True,
        text=True,
        check=False,
    )


def test_check_starts_django_before_importing_a_urlconf_that_imports_models(tmp_path):
    pytest.importorskip("django", reason="the Django startup tests need django")
    _write_django_project(tmp_path)

    completed = _run_check(tmp_path, "proj_settings")

    assert "AppRegistryNotReady" not in completed.stderr
    assert "app unavailable" not in completed.stderr
    # The app loaded and Django answered for its links: only the missing page is reported.
    assert "'/nope'" in completed.stderr
    assert "were not checked" not in completed.stderr
    assert "setup-calls=1" in completed.stdout
    assert completed.returncode == 0, completed.stderr


def test_a_missing_settings_module_reports_djangos_error(tmp_path):
    pytest.importorskip("django", reason="the Django startup tests need django")
    _write_django_project(tmp_path)

    completed = _run_check(tmp_path, "no_such_settings")

    assert (
        "app unavailable: Django could not start with DJANGO_SETTINGS_MODULE='no_such_settings': "
        "ModuleNotFoundError: No module named 'no_such_settings'. Fix that error, "
        "or unset DJANGO_SETTINGS_MODULE if this is not a Django project."
    ) in completed.stderr
    assert "AppRegistryNotReady" not in completed.stderr
    assert completed.returncode == 2


def test_the_variable_without_django_installed_is_a_clear_app_error(monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "myproject.settings")
    # find_spec() returning None is what an environment without Django looks like.
    monkeypatch.setattr(_django_startup, "find_spec", lambda _name: None)

    # The check comes before the import, so the target module need not exist.
    with pytest.raises(AppSelectionError, match="Django is not installed") as raised:
        load_app("plain_app:engine")
    assert "'myproject.settings'" in str(raised.value)
    assert "unset DJANGO_SETTINGS_MODULE" in str(raised.value)


def test_a_settings_module_that_exits_is_reported_as_an_app_error(monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "myproject.settings")
    monkeypatch.setattr(_django_startup, "find_spec", lambda _name: object())

    def exiting_start() -> None:
        raise SystemExit(3)

    monkeypatch.setattr(_django_startup, "start_django", exiting_start)

    # A bare exit would otherwise end `citry --app ... list` with no message.
    with pytest.raises(AppSelectionError, match=r"Django could not start .*: SystemExit: 3\."):
        load_app("plain_app:engine")


def test_without_the_variable_django_is_not_started(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(tmp_path))
    (tmp_path / "plain_app_2.py").write_text("from citry import Citry\nengine = Citry()\n", encoding="utf-8")
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)

    def forbidden() -> None:
        pytest.fail("a project without DJANGO_SETTINGS_MODULE must not start Django")

    monkeypatch.setattr(_django_startup, "start_django", forbidden)

    try:
        assert load_app("plain_app_2:engine") is not None
    finally:
        # Drop the module so no later test finds this one by name.
        sys.modules.pop("plain_app_2", None)


@pytest.mark.parametrize(
    ("ready", "loading"),
    [
        (True, False),
        # Inside an app's ready() hook the models are registered but the apps
        # are not ready yet, and a second setup() would raise.
        (False, True),
    ],
)
def test_start_django_does_nothing_once_the_apps_are_loaded_or_loading(monkeypatch, ready, loading):
    django = pytest.importorskip("django", reason="the Django startup tests need django")
    from django.apps import apps

    def forbidden() -> None:
        pytest.fail("django.setup() must not run again once the apps are loaded")

    monkeypatch.setattr(apps, "ready", ready)
    monkeypatch.setattr(apps, "loading", loading)
    monkeypatch.setattr(django, "setup", forbidden)

    _django_startup.start_django()


def test_a_django_stub_without_a_spec_still_counts_as_installed(monkeypatch):
    # find_spec() raises ValueError for a sys.modules entry without __spec__;
    # the check must treat it as installed instead of failing on that error.
    stub = types.ModuleType("django")
    stub.__spec__ = None
    monkeypatch.setitem(sys.modules, "django", stub)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "myproject.settings")
    started = []
    monkeypatch.setattr(_django_startup, "start_django", lambda: started.append(True))

    _django_startup.start_django_from_environment()

    assert started == [True]
