"""
First renders on several threads work when the app never called ``initialize()``.

The first render of an engine finishes its one-time setup: it imports the
component modules (with autodiscovery on), creates Citry's built-in
components, and builds the rules that Citry checks templates against. One thread
does the setup and the others wait for it; each then builds the rules with
no lock held.
"""

from __future__ import annotations

import re
import sys
import threading
import uuid
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, CitryLifecycleInProgress, Component, Extension, lifecycle

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_THREADS = 8
_ROUNDS = 10
_JOIN_TIMEOUT = 20.0


def _render_together(render: Any, count: int = _THREADS) -> tuple[list[str], list[BaseException]]:
    pages: list[str] = []
    errors: list[BaseException] = []
    start = threading.Barrier(count, timeout=_JOIN_TIMEOUT)

    def run() -> None:
        start.wait()
        try:
            # Each render gets its own instance ids, so they are left out.
            pages.append(re.sub(r' data-cid-\w+=""', "", render()))
        except BaseException as error:  # noqa: BLE001 - every failure is reported below
            errors.append(error)

    threads = [threading.Thread(target=run, daemon=True) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=_JOIN_TIMEOUT)
    assert not any(thread.is_alive() for thread in threads), "a thread is stuck"
    return pages, errors


def _engine_without_discovery() -> tuple[Citry, type[Component]]:
    app = Citry(autodiscover=False)

    class Badge(Component):
        citry = app

        class Kwargs:
            label: str

        template = """
            <b>{{ label }}</b>
        """

    class Card(Component):
        citry = app
        template = """
            <p><c-Badge label="new" /></p>
        """

    return app, Card


@pytest.mark.parametrize("round_number", range(_ROUNDS))
def test_eight_first_renders_of_one_component_without_discovery(round_number: int) -> None:
    _app, card = _engine_without_discovery()
    pages, errors = _render_together(lambda: card().render().serialize())
    assert errors == []
    assert len(set(pages)) == 1
    assert "<b>new</b>" in pages[0]


@pytest.fixture
def discovered_engine(tmp_path: Path) -> Iterator[tuple[Citry, str]]:
    # Autodiscovery imports every module under `dirs`. The module reads the
    # engine from a helper module, so its components register on it.
    helper = f"citry_first_render_engine_{uuid.uuid4().hex}"
    package = f"citry_first_render_components_{uuid.uuid4().hex}"
    app = Citry(dirs=[tmp_path / package])
    holder = type(sys)(helper)
    holder.app = app  # type: ignore[attr-defined]
    sys.modules[helper] = holder
    (tmp_path / package).mkdir()
    (tmp_path / package / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / package / "cards.py").write_text(
        f'''
from citry import Component
from {helper} import app


class DiscoveredBadge(Component):
    citry = app

    class Kwargs:
        label: str

    template = """
        <b>{{{{ label }}}}</b>
    """


class DiscoveredCard(Component):
    citry = app
    template = """
        <p><c-DiscoveredBadge label="found" /></p>
    """
''',
        encoding="utf-8",
    )
    sys.path.insert(0, str(tmp_path))
    try:
        yield app, package
    finally:
        sys.path.remove(str(tmp_path))
        for name in [name for name in sys.modules if name.startswith(package)]:
            del sys.modules[name]
        del sys.modules[helper]


def test_eight_first_renders_of_one_component_with_discovery(discovered_engine: tuple[Citry, str]) -> None:
    app, _package = discovered_engine
    for _round in range(_ROUNDS):
        pages, errors = _render_together(lambda: str(app.render_template("<c-DiscoveredCard />")))
        assert errors == []
        assert len(set(pages)) == 1
        assert "<b>found</b>" in pages[0]


def test_two_components_rendered_for_the_first_time_on_two_threads() -> None:
    app = Citry(autodiscover=False)

    class First(Component):
        citry = app
        template = """
            <p>first</p>
        """

    class Second(Component):
        citry = app
        template = """
            <p>second</p>
        """

    calls = iter([First, Second])
    lock = threading.Lock()

    def render() -> str:
        with lock:
            component = next(calls)
        return component().render().serialize()

    pages, errors = _render_together(render, count=2)
    assert errors == []
    assert sorted("first" in page for page in pages) == [False, True]


def test_threads_waiting_for_a_failed_discovery_do_not_hang(tmp_path: Path) -> None:
    # The first thread's discovery fails on a broken module. The threads that
    # waited for it run the setup themselves and see the same error.
    package = f"citry_broken_components_{uuid.uuid4().hex}"
    (tmp_path / package).mkdir()
    (tmp_path / package / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / package / "broken.py").write_text("raise ImportError('broken component module')\n", encoding="utf-8")
    app = Citry(dirs=[tmp_path / package])
    sys.path.insert(0, str(tmp_path))
    try:
        pages, errors = _render_together(lambda: str(app.render_template("<p>x</p>")), count=4)
    finally:
        sys.path.remove(str(tmp_path))
        for name in [name for name in sys.modules if name.startswith(package)]:
            del sys.modules[name]
    assert pages == []
    assert len(errors) == 4
    assert all("broken component module" in str(error) for error in errors)


def test_a_setup_hook_that_renders_on_the_setup_thread_fails_instead_of_waiting_on_itself() -> None:
    # An extension hook that runs during the one-time setup renders a
    # template on the same thread. The setup is not finished, so the render
    # raises, as it does on one thread without any other threads; it does
    # not wait for the setup it is part of.
    errors: list[BaseException] = []
    engines: list[Citry] = []

    class RendersDuringSetup(Extension):
        name = "renders_during_setup"

        def on_component_registered(self, ctx: Any) -> None:
            # The built-ins register during the setup; try once, from the
            # first of them.
            if ctx.component_class.__module__.startswith("citry.") and not errors:
                try:
                    str(engines[0].render_template("<p>inside</p>"))
                except Exception as error:  # noqa: BLE001 - the test checks the error below
                    errors.append(error)

    app = Citry(autodiscover=False, extensions=[RendersDuringSetup])
    engines.append(app)

    class Plain(Component):
        citry = app
        template = """
            <p>plain</p>
        """

    pages: list[str] = []
    thread = threading.Thread(target=lambda: pages.append(Plain().render().serialize()), daemon=True)
    thread.start()
    thread.join(timeout=_JOIN_TIMEOUT)
    assert not thread.is_alive(), "the setup waited on itself"
    assert len(errors) == 1
    assert "plain" in pages[0]


def test_a_kwargs_schema_is_checked_after_concurrent_first_renders() -> None:
    # The rules each thread builds are the real ones: a wrong input still
    # fails at parse time.
    app = Citry(autodiscover=False)

    class Strict(Component):
        citry = app

        class Kwargs:
            label: str

        template = """
            <b>{{ label }}</b>
        """

    class Uses(Component):
        citry = app
        template = """
            <c-Strict label="ok" />
        """

    _pages, errors = _render_together(lambda: Uses().render().serialize())
    assert errors == []
    with pytest.raises(SyntaxError, match="unknown"):
        str(app.render_template('<c-Strict label="ok" unknown="x" />'))


def _blocking_discovery(tmp_path: Path, body: str, extensions: list[Any] | None = None) -> tuple[Citry, str, str]:
    # A component module whose import runs `body`, with the engine and a
    # module of test hooks importable from it.
    helper = f"citry_first_render_hooks_{uuid.uuid4().hex}"
    package = f"citry_first_render_blocking_{uuid.uuid4().hex}"
    app = Citry(dirs=[tmp_path / package], extensions=extensions or [])
    holder = type(sys)(helper)
    holder.app = app  # type: ignore[attr-defined]
    sys.modules[helper] = holder
    (tmp_path / package).mkdir()
    (tmp_path / package / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / package / "blocking.py").write_text(f"from {helper} import app, hooks\n{body}\n", encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    return app, helper, package


def _forget(tmp_path: Path, helper: str, package: str) -> None:
    sys.path.remove(str(tmp_path))
    for name in [name for name in sys.modules if name.startswith(package)]:
        del sys.modules[name]
    del sys.modules[helper]


def test_a_discovered_module_that_joins_a_rendering_thread_fails_instead_of_hanging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The module starts a thread that looks a component up and waits for
    # it. That thread waits for the discovery, which waits for it, so the
    # wait gives up after its time limit and the lookup fails.
    monkeypatch.setattr(lifecycle, "_SETUP_WAIT_SECONDS", 0.5)
    app, helper, package = _blocking_discovery(tmp_path, "hooks.start_and_join()")
    errors: list[BaseException] = []

    def look_up() -> None:
        try:
            app.has("anything")
        except BaseException as error:  # noqa: BLE001 - the test checks the error below
            errors.append(error)

    def start_and_join() -> None:
        worker = threading.Thread(target=look_up, daemon=True)
        worker.start()
        worker.join(_JOIN_TIMEOUT)

    sys.modules[helper].hooks = type(sys)("hooks")  # type: ignore[attr-defined]
    sys.modules[helper].hooks.start_and_join = start_and_join  # type: ignore[attr-defined]
    try:
        pages, render_errors = _render_together(lambda: str(app.render_template("<p>x</p>")), count=1)
    finally:
        _forget(tmp_path, helper, package)
    assert render_errors == []
    assert pages == ["<p>x</p>"]
    assert len(errors) == 1
    assert isinstance(errors[0], CitryLifecycleInProgress)


def test_a_reset_hook_that_renders_during_another_threads_discovery_fails_at_once(tmp_path: Path) -> None:
    # A reset holds locks that the discovery may need, so a render from its
    # hook raises instead of waiting for the discovery.
    discovering = threading.Event()
    release = threading.Event()
    reset_errors: list[BaseException] = []
    engines: list[Citry] = []

    class RendersOnReset(Extension):
        name = "renders_on_reset"

        def on_files_reset(self, ctx: Any) -> None:
            try:
                str(engines[0].render_template("<p>reset</p>"))
            except BaseException as error:  # noqa: BLE001 - the test checks the error below
                reset_errors.append(error)

    app, helper, package = _blocking_discovery(tmp_path, "hooks.pause()", extensions=[RendersOnReset])
    engines.append(app)

    def pause() -> None:
        discovering.set()
        release.wait(_JOIN_TIMEOUT)

    sys.modules[helper].hooks = type(sys)("hooks")  # type: ignore[attr-defined]
    sys.modules[helper].hooks.pause = pause  # type: ignore[attr-defined]

    class Other(Component):
        citry = app
        template = """
            <p>other</p>
        """

    try:
        first = threading.Thread(target=lambda: str(app.render_template("<p>x</p>")), daemon=True)
        first.start()
        assert discovering.wait(_JOIN_TIMEOUT)
        resetter = threading.Thread(target=Other.reset_files, daemon=True)
        resetter.start()
        resetter.join(_JOIN_TIMEOUT)
        assert not resetter.is_alive(), "the reset waited for the discovery"
        release.set()
        first.join(_JOIN_TIMEOUT)
        assert not first.is_alive()
    finally:
        release.set()
        _forget(tmp_path, helper, package)
    assert len(reset_errors) == 1
    assert isinstance(reset_errors[0], CitryLifecycleInProgress)
