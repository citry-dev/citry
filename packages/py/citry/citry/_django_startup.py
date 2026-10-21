"""
Start Django before Citry imports a Django project's code.

A Django project's modules may import models, and importing a model before
Django has loaded its installed apps raises ``AppRegistryNotReady``. A running
server avoids that because ``manage.py`` or the WSGI entry point calls
``django.setup()`` first. ``citry check``, the other ``citry --app`` commands,
and the editor's app worker (the separate process that imports your app for
the editor) import the app module directly, so they call
``start_django_from_environment()`` first, the way ``manage.py`` would.

This module imports Django only inside its functions, so Citry still imports
without Django installed.
"""

from __future__ import annotations

import os
from importlib.util import find_spec

# The startup error ends with this way out, for a shell that still has the
# variable set from another project whose environment had Django installed.
_UNSET_HINT = "or unset DJANGO_SETTINGS_MODULE if this is not a Django project"


class DjangoStartupError(RuntimeError):
    """Django was asked for through ``DJANGO_SETTINGS_MODULE`` but could not start."""


def start_django() -> None:
    """
    Load Django's settings and installed apps once, as a running server has them.

    It returns at once when Django's apps are loaded or loading, so Django
    starts at most once per process, whichever caller needs it first.
    """
    # Imported here: Citry must import without Django installed.
    import django  # noqa: PLC0415
    from django.apps import apps  # noqa: PLC0415

    # django.setup() also reconfigures logging and the URL script prefix, so
    # calling it again would undo changes the project made after startup.
    # While Django runs the apps' ready() hooks, `loading` is set and the
    # models are registered; starting again there would raise "populate()
    # isn't reentrant".
    if apps.ready or apps.loading:
        return
    django.setup()


def start_django_from_environment() -> None:
    """
    Start Django when ``DJANGO_SETTINGS_MODULE`` names a settings module.

    Without the variable this does nothing: the project is not a Django
    project, or it configures Django in its own code with
    ``settings.configure()``. Such a project must leave the variable unset,
    because starting Django here reads the settings before its own code runs.
    With the variable set but Django not installed, this also does nothing.

    Raises:
        DjangoStartupError: When Django is installed but fails to start, for
            example because the settings module cannot be imported. The
            message carries Django's own error.

    """
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")
    if not settings_module:
        return
    try:
        django_installed = find_spec("django") is not None
    except ValueError:
        # A `django` entry in sys.modules without a spec, such as a test stub,
        # is still something to try to start.
        django_installed = True
    # Without Django the project cannot be a Django one, so the variable is
    # left over from another shell; failing here would break a project that
    # never needed Django.
    if not django_installed:
        return
    try:
        start_django()
    except (Exception, SystemExit) as exc:
        # Turn any startup failure, including a settings module that calls
        # sys.exit(), into one error that names the variable, so load_app()
        # and the editor report it as an app failure with Django's own
        # message, not a traceback or a silent exit.
        # Django's messages often end in a period; the sentence below adds one.
        detail = str(exc).rstrip(".")
        reason = f"{type(exc).__name__}: {detail}" if detail else type(exc).__name__
        msg = (
            f"Django could not start with DJANGO_SETTINGS_MODULE={settings_module!r}: {reason}. "
            f"Fix that error, {_UNSET_HINT}."
        )
        raise DjangoStartupError(msg) from exc


__all__: list[str] = []
