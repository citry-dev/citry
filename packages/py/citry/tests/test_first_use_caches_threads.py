"""
Values Citry computes on first use stay one value when several threads need them at once.

A server's worker threads often make their first renders and first event
calls at the same moment. Citry runs the loading work, including the
extension hooks, with no lock held, and then keeps the first result that
finished. So two threads can both run a hook, and both get the same stored
value. A reset that arrives while a load runs makes that load run again, so
the old content is never kept.
"""

from __future__ import annotations

import contextlib
import threading
from typing import TYPE_CHECKING, Any

from citry import Citry, Component, Extension
from citry.ext.dependencies import scripts
from citry.ext.events import renderers, schemas

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

# Long enough for the second thread to reach a barrier when nothing holds it
# back.
_BARRIER_TIMEOUT = 5.0
# How long a test waits for its threads before it reports them stuck, so a
# deadlock fails the test instead of hanging the run.
_JOIN_TIMEOUT = 10.0


def _wait_for_the_other_thread(barrier: threading.Barrier) -> None:
    # Some tests only need the threads to overlap when they can; a broken
    # barrier there just means one thread went on alone.
    with contextlib.suppress(threading.BrokenBarrierError):
        barrier.wait()


def _run_together(target: Any, count: int = 2) -> list[Any]:
    results: list[Any] = []
    start = threading.Barrier(count, timeout=_BARRIER_TIMEOUT)

    def run() -> None:
        start.wait()
        results.append(target())

    threads = [threading.Thread(target=run, daemon=True) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=_JOIN_TIMEOUT)
    assert not any(thread.is_alive() for thread in threads), "a thread is stuck"
    assert len(results) == count
    return results


def _start(target: Any) -> threading.Thread:
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread


def _finish(*threads: threading.Thread) -> None:
    for thread in threads:
        thread.join(timeout=_JOIN_TIMEOUT)
    assert not any(thread.is_alive() for thread in threads), "a thread is stuck"


def test_on_one_thread_each_load_hook_runs_once_per_class() -> None:
    # Without other threads or resets, nothing makes a load run again.
    calls: list[str] = []

    class Counting(Extension):
        name = "counting"

        def on_template_loaded(self, ctx: Any) -> None:
            calls.append("template")

        def on_js_loaded(self, ctx: Any) -> None:
            calls.append("js")

        def on_css_loaded(self, ctx: Any) -> None:
            calls.append("css")

        def on_messages_loaded(self, ctx: Any) -> None:
            calls.append("messages")

    app = Citry(
        autodiscover=False,
        extensions=[Counting],
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )

    class Card(Component):
        citry = app
        template = """
            <p>Card</p>
        """
        js = """
            $component({});
        """
        css = """
            p { color: red; }
        """
        messages = """
            title = Card
        """

    app.initialize()
    revision = app._asset_revision
    for _ in range(3):
        Card().render().serialize()
        Card.get_messages()
    assert sorted(calls) == ["css", "js", "messages", "template"]
    assert app._asset_revision == revision


def test_defining_a_component_while_a_hook_runs_does_not_run_the_hook_again() -> None:
    # Registering a class clears Citry's standalone template cache, which
    # has its own counter, so a load in progress keeps its result.
    loading = threading.Event()
    release = threading.Event()
    calls: list[str] = []

    class SlowJs(Extension):
        name = "slow_js"

        def on_js_loaded(self, ctx: Any) -> None:
            calls.append(ctx.component_class.__name__)
            loading.set()
            release.wait(_JOIN_TIMEOUT)

    app = Citry(autodiscover=False, extensions=[SlowJs])

    class Card(Component):
        citry = app
        template = """
            <p>Card</p>
        """
        js = """
            $component({});
        """

    app.initialize()
    loader = _start(Card.get_js)
    assert loading.wait(_JOIN_TIMEOUT)

    def define() -> None:
        class Later(Component):
            citry = app
            template = """
                <p>Later</p>
            """

    _finish(_start(define))
    release.set()
    _finish(loader)
    assert calls == ["Card"]


def test_two_threads_in_on_js_loaded_at_once_get_the_one_result_kept() -> None:
    # Both threads are inside the hook at the same time (the barrier would
    # time out otherwise), each returns different text, and Citry keeps one.
    inside = threading.Barrier(2, timeout=_BARRIER_TIMEOUT)
    calls: list[str] = []

    class Tagging(Extension):
        name = "tagging"

        def on_js_loaded(self, ctx: Any) -> str:
            inside.wait()
            calls.append(threading.current_thread().name)
            return f"{ctx.content} // {threading.current_thread().name}"

    app = Citry(autodiscover=False, extensions=[Tagging])

    class Card(Component):
        citry = app
        template = """
            <p>Card</p>
        """
        js = """
            $component({});
        """

    app.initialize()
    results = _run_together(Card.get_js)
    assert len(calls) == 2
    assert results[0] == results[1] == Card.get_js()


def test_two_threads_loading_a_template_at_once_share_one_template_record() -> None:
    inside = threading.Barrier(2, timeout=_BARRIER_TIMEOUT)

    class Waiting(Extension):
        name = "waiting"

        def on_template_loaded(self, ctx: Any) -> None:
            inside.wait()

    app = Citry(autodiscover=False, extensions=[Waiting])

    class Card(Component):
        citry = app
        template = """
            <p>Card</p>
        """

    app.initialize()
    templates = _run_together(Card.get_template)
    # The render pipeline fills in the compiled form on this one object.
    assert templates[0] is templates[1] is Card.get_template()


def test_an_asset_hook_may_load_another_components_assets() -> None:
    loaded: list[str | None] = []
    classes: dict[str, type[Component]] = {}

    class Reentering(Extension):
        name = "reentering"

        def on_js_loaded(self, ctx: Any) -> None:
            if ctx.component_class is classes["outer"]:
                loaded.append(classes["inner"].get_js())

    app = Citry(autodiscover=False, extensions=[Reentering])

    class Inner(Component):
        citry = app
        template = """
            <i>inner</i>
        """
        js = """
            $component({});
        """

    class Outer(Component):
        citry = app
        template = """
            <b>outer</b>
        """
        js = """
            $component({});
        """

    classes.update(inner=Inner, outer=Outer)
    app.initialize()
    _finish(_start(lambda: Outer().render().serialize()))
    assert loaded
    assert "$component" in (loaded[0] or "")


def test_hooks_that_read_another_kind_of_asset_do_not_wait_on_each_other() -> None:
    # A scoped-CSS extension reads a component's CSS while its template loads,
    # and its template while its CSS loads. Two threads doing the two first
    # loads at once must not each wait for the other.
    classes: dict[str, type[Component]] = {}
    inside = threading.Barrier(2, timeout=_BARRIER_TIMEOUT)
    # Each hook reads the other asset once, on its first call, so the two
    # hooks do not call each other without end on one thread.
    started: set[str] = set()

    class Scoped(Extension):
        name = "scoped"

        def on_template_loaded(self, ctx: Any) -> None:
            if ctx.component_class is classes["a"] and "template" not in started:
                started.add("template")
                inside.wait()
                classes["b"].get_css()

        def on_css_loaded(self, ctx: Any) -> None:
            if ctx.component_class is classes["b"] and "css" not in started:
                started.add("css")
                inside.wait()
                classes["a"].get_template()

    app = Citry(autodiscover=False, extensions=[Scoped])

    class First(Component):
        citry = app
        template = """
            <p>a</p>
        """

    class Second(Component):
        citry = app
        template = """
            <p>b</p>
        """
        css = """
            p { color: red; }
        """

    classes.update(a=First, b=Second)
    app.initialize()
    calls = iter([First.get_template, Second.get_css])
    lock = threading.Lock()

    def next_call() -> object:
        with lock:
            call = next(calls)
        return call()

    assert len(_run_together(next_call)) == 2


def test_a_reset_during_a_slow_on_js_loaded_is_not_undone(tmp_path: Path) -> None:
    # A reload edits js_file and resets the class while another thread is
    # still inside the hook with the old content. The reset does not wait
    # for the hook, and the load then runs again, so the new file is kept.
    script = tmp_path / "card.js"
    script.write_text("console.log('old');", encoding="utf-8")
    loading = threading.Event()
    release = threading.Event()
    seen: list[str] = []

    class SlowJs(Extension):
        name = "slow_js"

        def on_js_loaded(self, ctx: Any) -> None:
            seen.append(ctx.content)
            if not loading.is_set():
                loading.set()
                release.wait(_JOIN_TIMEOUT)

    app = Citry(autodiscover=False, extensions=[SlowJs])

    class Card(Component):
        citry = app
        template = """
            <p>Card</p>
        """
        js_file = str(script)

    app.initialize()
    loader = _start(Card.get_js)
    assert loading.wait(_JOIN_TIMEOUT)
    script.write_text("console.log('new');", encoding="utf-8")
    # The reset finishes while the hook still runs.
    _finish(_start(Card.reset_files))
    release.set()
    _finish(loader)
    assert "new" in (Card.get_js() or "")
    assert ["old" in text for text in seen] == [True, False]


def test_a_reset_during_a_slow_on_template_loaded_is_not_undone(tmp_path: Path) -> None:
    source = tmp_path / "card.html"
    source.write_text("<p>old</p>", encoding="utf-8")
    loading = threading.Event()
    release = threading.Event()

    class SlowTemplate(Extension):
        name = "slow_template"

        def on_template_loaded(self, ctx: Any) -> None:
            if not loading.is_set():
                loading.set()
                release.wait(_JOIN_TIMEOUT)

    app = Citry(autodiscover=False, extensions=[SlowTemplate])

    class Card(Component):
        citry = app
        template_file = str(source)

    app.initialize()
    loader = _start(Card.get_template)
    assert loading.wait(_JOIN_TIMEOUT)
    source.write_text("<p>new</p>", encoding="utf-8")
    _finish(_start(Card.reset_template))
    release.set()
    _finish(loader)
    template = Card.get_template()
    assert template is not None
    assert "new" in template.source


def test_a_reset_during_a_slow_on_messages_loaded_leaves_the_catalog_on_the_new_text(tmp_path: Path) -> None:
    # The i18n extension installs each loaded source in its catalog from its
    # own on_messages_loaded hook. A load that read the old file before the
    # reset runs again after it, so the catalog ends on the new text too.
    source = tmp_path / "card.ftl"
    source.write_text("title = Old\n", encoding="utf-8")
    loading = threading.Event()
    release = threading.Event()

    class SlowMessages(Extension):
        name = "slow_messages"

        def on_messages_loaded(self, ctx: Any) -> None:
            if not loading.is_set():
                loading.set()
                release.wait(_JOIN_TIMEOUT)

    app = Citry(
        autodiscover=False,
        extensions=[SlowMessages],
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )

    class Card(Component):
        citry = app
        template = """
            <p>Card</p>
        """
        messages_file = str(source)

    app.initialize()
    loader = _start(Card.get_messages)
    assert loading.wait(_JOIN_TIMEOUT)
    source.write_text("title = New\n", encoding="utf-8")
    _finish(_start(Card.reset_files))
    release.set()
    _finish(loader)
    assert "New" in (Card.get_messages() or "")
    i18n = app.extensions.get_extension("i18n")
    assert "New" in i18n._catalogs[Card].content  # type: ignore[attr-defined]


def test_loads_stop_running_again_when_resets_keep_coming() -> None:
    # Every run of this hook resets the class, so every load sees a reset.
    # Citry runs the load three times and then keeps the last result, so a
    # stream of hot reloads cannot stall a render.
    runs: list[int] = []
    classes: dict[str, type[Component]] = {}

    class Resetting(Extension):
        name = "resetting"

        def on_js_loaded(self, ctx: Any) -> str:
            runs.append(len(runs))
            classes["card"].reset_files()
            return f"{ctx.content} // run {len(runs)}"

    app = Citry(autodiscover=False, extensions=[Resetting])

    class Card(Component):
        citry = app
        template = """
            <p>Card</p>
        """
        js = """
            $component({});
        """

    classes["card"] = Card
    app.initialize()
    result: list[str | None] = []
    _finish(_start(lambda: result.append(Card.get_js())))
    assert len(runs) == 3
    assert result == [Card.get_js()]
    assert "run 3" in (result[0] or "")


def test_a_reset_during_a_slow_dependencies_entry_is_not_undone() -> None:
    # A Dependencies entry may be a function, such as one that looks up a
    # build manifest. It runs with no lock held; a reset while it runs makes
    # the merge run again.
    urls = ["https://cdn.example/old.js"]
    entered = threading.Event()
    release = threading.Event()

    def current_url() -> str:
        url = urls[0]
        if not entered.is_set():
            entered.set()
            release.wait(_JOIN_TIMEOUT)
        return url

    app = Citry(autodiscover=False)

    class Card(Component):
        citry = app
        template = """
            <p>Card</p>
        """

        class Dependencies:
            js = current_url

    app.initialize()
    loader = _start(Card.get_dependencies)
    assert entered.wait(_JOIN_TIMEOUT)
    urls[0] = "https://cdn.example/new.js"
    _finish(_start(Card.reset_files))
    release.set()
    _finish(loader)
    assert Card.get_dependencies().js == ("https://cdn.example/new.js",)


def test_a_messages_hook_that_reads_js_does_not_wait_on_a_reset() -> None:
    # A messages hook that reads the component's JS while another thread
    # resets the component: neither may get stuck.
    inside = threading.Barrier(2, timeout=_BARRIER_TIMEOUT)
    classes: dict[str, type[Component]] = {}

    class ReadsJs(Extension):
        name = "reads_js"

        def on_messages_loaded(self, ctx: Any) -> None:
            _wait_for_the_other_thread(inside)
            classes["card"].get_js()

    app = Citry(
        autodiscover=False,
        extensions=[ReadsJs],
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )

    class Card(Component):
        citry = app
        template = """
            <p>Card</p>
        """
        js = """
            $component({});
        """
        messages = """
            title = Card
        """

    classes["card"] = Card
    app.initialize()
    calls = iter([Card.get_messages, lambda: (_wait_for_the_other_thread(inside), Card.reset_files())])
    lock = threading.Lock()

    def next_call() -> object:
        with lock:
            call = next(calls)
        return call()

    assert len(_run_together(next_call)) == 2


def test_a_reset_while_the_browser_script_is_built_is_not_undone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Citry builds the script it sends the browser from get_js() and stores
    # it on the class. A reset between the read and the store makes the
    # build run again, so the old script is not kept.
    script = tmp_path / "card.js"
    script.write_text("$component({}); // old", encoding="utf-8")
    app = Citry(autodiscover=False)

    class Card(Component):
        citry = app
        template = """
            <p>Card</p>
        """
        js_file = str(script)

    app.initialize()
    building = threading.Event()
    release = threading.Event()
    spans = scripts._component_call_spans

    def slow_spans(content: str) -> Any:
        if "old" in content and not building.is_set():
            building.set()
            release.wait(_JOIN_TIMEOUT)
        return spans(content)

    monkeypatch.setattr(scripts, "_component_call_spans", slow_spans)
    builder = _start(lambda: scripts.uses_component(Card))
    assert building.wait(_JOIN_TIMEOUT)
    script.write_text("$component({}); // new", encoding="utf-8")
    _finish(_start(Card.reset_files))
    release.set()
    _finish(builder)
    stored = scripts._component_script_capture("js", Card).script
    assert stored is not None
    assert "new" in stored.content


def test_a_schema_converts_to_one_class_across_threads(monkeypatch: pytest.MonkeyPatch) -> None:
    class Payload:
        title: str

    inside = threading.Barrier(2, timeout=_BARRIER_TIMEOUT)
    convert = schemas.convert_state_class

    def wait_then_convert(name: str, cls: type) -> type:
        inside.wait()
        return convert(name, cls)

    monkeypatch.setattr(schemas, "convert_state_class", wait_then_convert)
    converted = _run_together(lambda: schemas.convert_schema_class(Payload))
    # Nested schema instances rely on one stable class per schema.
    assert converted[0] is converted[1] is schemas.convert_schema_class(Payload)

    # The field specs, with both threads inside their computation at once.
    inside_hints = threading.Barrier(2, timeout=_BARRIER_TIMEOUT)
    hints = schemas.get_type_hints

    def wait_then_hints(cls: type) -> dict[str, Any]:
        inside_hints.wait()
        return hints(cls)

    monkeypatch.setattr(schemas, "get_type_hints", wait_then_hints)
    infos = _run_together(lambda: schemas._schema_info(Payload))
    assert infos[0] is infos[1]
    assert infos[0][0] is converted[0]


def test_the_events_dispatcher_is_one_object_across_threads(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Citry(autodiscover=False)
    inside = threading.Barrier(2, timeout=_BARRIER_TIMEOUT)
    build = renderers.EventsDispatcher

    def wait_then_build(*args: Any, **kwargs: Any) -> Any:
        inside.wait()
        return build(*args, **kwargs)

    monkeypatch.setattr(renderers, "EventsDispatcher", wait_then_build)
    dispatchers = _run_together(lambda: renderers.dispatcher_for(app))
    assert dispatchers[0] is dispatchers[1] is renderers.dispatcher_for(app)
