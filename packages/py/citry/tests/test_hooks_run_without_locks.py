"""
Extension hooks, Dependencies entries, and Const functions run with no Citry lock held.

Each test starts two threads that used to wait on each other: one runs user
code that renders another component, the other resets a template or files
(as a hot reload does), or runs the same kind of user code. The threads are
daemon threads joined with a timeout, so a regression fails the test
instead of hanging the run.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from citry import Citry, Component, Const, Extension
from citry.constness import ConstBodyCache

# How long a test waits for its threads before it reports them stuck.
_JOIN_TIMEOUT = 10.0
# How long the user code below sleeps, long enough for the other thread to
# take any lock a reset takes.
_SLOW = 0.3


def _run(*targets: Any) -> None:
    threads = [threading.Thread(target=target, daemon=True) for target in targets]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=_JOIN_TIMEOUT)
    assert not any(thread.is_alive() for thread in threads), "the threads are stuck waiting on each other"


def test_an_on_js_loaded_hook_that_renders_a_cached_component_during_reset_files() -> None:
    entered = threading.Event()
    classes: dict[str, type[Component]] = {}

    class Inline(Extension):
        name = "inline_badge"

        def on_js_loaded(self, ctx: Any) -> None:
            if ctx.component_class is classes["card"]:
                entered.set()
                time.sleep(_SLOW)
                classes["badge"]().render().serialize()

    app = Citry(autodiscover=False, extensions=[Inline])

    class Badge(Component):
        citry = app
        template = """
            <span>badge</span>
        """

        class Cache:
            enabled = True

    class Card(Component):
        citry = app
        template = """
            <p>card</p>
        """
        js = """
            console.log("card");
        """

    class Other(Component):
        citry = app
        template = """
            <p>other</p>
        """

    classes.update(badge=Badge, card=Card)

    def reset() -> None:
        entered.wait(_JOIN_TIMEOUT)
        Other.reset_files()

    _run(Card.get_js, reset)


def test_an_on_template_loaded_hook_that_renders_a_cached_component_during_reset_template() -> None:
    entered = threading.Event()
    classes: dict[str, type[Component]] = {}

    class Inline(Extension):
        name = "inline_badge"

        def on_template_loaded(self, ctx: Any) -> None:
            if ctx.component_class is classes["card"]:
                entered.set()
                time.sleep(_SLOW)
                classes["badge"]().render().serialize()

    app = Citry(autodiscover=False, extensions=[Inline])

    class Badge(Component):
        citry = app
        template = """
            <span>badge</span>
        """

        class Cache:
            enabled = True

    class Card(Component):
        citry = app
        template = """
            <p>card</p>
        """

    class Other(Component):
        citry = app
        template = """
            <p>other</p>
        """

    classes.update(badge=Badge, card=Card)

    def reset() -> None:
        entered.wait(_JOIN_TIMEOUT)
        Other.reset_template()

    _run(Card.get_template, reset)


def test_components_on_two_engines_that_extend_each_others_dependencies() -> None:
    app_a = Citry(autodiscover=False)
    app_b = Citry(autodiscover=False)

    def slow(url: str) -> Any:
        def entry() -> str:
            time.sleep(_SLOW)
            return url

        return entry

    class BaseA(Component):
        citry = app_a
        template = """
            <p>a</p>
        """

        class Dependencies:
            js = "https://cdn.example/base-a.js"

    class BaseB(Component):
        citry = app_b
        template = """
            <p>b</p>
        """

        class Dependencies:
            js = "https://cdn.example/base-b.js"

    class CardA(Component):
        citry = app_a
        template = """
            <p>card a</p>
        """

        class Dependencies:
            js = slow("https://cdn.example/card-a.js")
            extend = [BaseB]

    class CardB(Component):
        citry = app_b
        template = """
            <p>card b</p>
        """

        class Dependencies:
            js = slow("https://cdn.example/card-b.js")
            extend = [BaseA]

    _run(CardA.get_dependencies, CardB.get_dependencies)
    assert CardA.get_dependencies().js == ("https://cdn.example/base-b.js", "https://cdn.example/card-a.js")
    assert CardB.get_dependencies().js == ("https://cdn.example/base-a.js", "https://cdn.example/card-b.js")


def _const_render_during_reset(*, leaf_loaded: bool) -> None:
    app = Citry(autodiscover=False)
    in_build = threading.Event()
    classes: dict[str, type[Component]] = {}

    def helper(value: str) -> str:
        in_build.set()
        time.sleep(_SLOW)
        return classes["leaf"](value=value).render().serialize()

    class Leaf(Component):
        citry = app
        template = """
            <b>{{ value }}</b>
        """

    class Page(Component):
        citry = app
        template = """
            <div>{{ helper(value) }}</div>
        """

    class Other(Component):
        citry = app
        template = """
            <p>other</p>
        """

    classes["leaf"] = Leaf
    if leaf_loaded:
        Leaf.get_template()
    rendered: list[str] = []

    def render() -> None:
        rendered.append(Page(value=Const("fixed"), helper=Const(helper)).render().serialize())

    def reset() -> None:
        in_build.wait(_JOIN_TIMEOUT)
        Other.reset_template()

    _run(render, reset)
    assert "fixed" in rendered[0]


def test_a_const_function_that_renders_a_component_for_the_first_time_during_reset_template() -> None:
    _const_render_during_reset(leaf_loaded=False)


def test_a_const_function_that_renders_a_loaded_component_during_reset_template() -> None:
    _const_render_during_reset(leaf_loaded=True)


def test_a_slow_on_template_loaded_hook_does_not_hold_up_renders_of_loaded_components() -> None:
    started = threading.Event()
    hook_seconds = 1.0
    classes: dict[str, type[Component]] = {}

    class SlowTemplate(Extension):
        name = "slow_template"

        def on_template_loaded(self, ctx: Any) -> None:
            if ctx.component_class is classes.get("slow"):
                started.set()
                time.sleep(hook_seconds)  # a template preprocessor

    app = Citry(autodiscover=False, extensions=[SlowTemplate])

    class Warm(Component):
        citry = app
        template = """
            <p>warm</p>
        """

    class Slow(Component):
        citry = app
        template = """
            <p>slow</p>
        """

    classes["slow"] = Slow
    Warm().render().serialize()
    loader = threading.Thread(target=Slow.get_template, daemon=True)
    loader.start()
    assert started.wait(_JOIN_TIMEOUT)
    began = time.perf_counter()
    Warm().render().serialize()
    elapsed = time.perf_counter() - began
    loader.join(timeout=_JOIN_TIMEOUT)
    assert not loader.is_alive()
    # Far below the hook's sleep: the render did not wait for it.
    assert elapsed < hook_seconds / 2


def test_two_compile_hooks_that_each_render_the_others_component_for_the_first_time() -> None:
    # Both threads are inside on_template_compiled at once (the barrier
    # would time out otherwise), and each hook then makes the other
    # component's first render.
    inside = threading.Barrier(2, timeout=_JOIN_TIMEOUT)
    started: set[str] = set()
    started_lock = threading.Lock()
    classes: dict[str, type[Component]] = {}

    class RendersTheOther(Extension):
        name = "renders_the_other"

        def on_template_compiled(self, ctx: Any) -> None:
            name = ctx.component_class.__name__
            if name not in {"First", "Second"}:
                return
            with started_lock:
                first_call = name not in started
                started.add(name)
            # Only each component's first compile renders the other, so the
            # two hooks do not call each other without end.
            if first_call:
                inside.wait()
                other = classes["second" if name == "First" else "first"]
                other().render().serialize()

    app = Citry(autodiscover=False, extensions=[RendersTheOther])

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

    classes.update(first=First, second=Second)
    app.initialize()
    pages: list[str] = []
    _run(
        lambda: pages.append(First().render().serialize()),
        lambda: pages.append(Second().render().serialize()),
    )
    assert sorted("first" in page for page in pages) == [False, True]


def test_a_reset_hook_may_render_a_component_on_its_own_thread() -> None:
    # Resets keep their locks while their hooks run. A thread that holds
    # one of these locks can take it again, so a hook that renders on the
    # resetting thread works.
    classes: dict[str, type[Component]] = {}
    rendered: list[str] = []

    class RendersOnReset(Extension):
        name = "renders_on_reset"

        def on_files_reset(self, ctx: Any) -> None:
            if ctx.component_class is classes["card"]:
                rendered.append(classes["fresh"]().render().serialize())

        def on_template_reset(self, ctx: Any) -> None:
            if ctx.component_class is classes["card"]:
                rendered.append(classes["fresh"]().render().serialize())

    app = Citry(autodiscover=False, extensions=[RendersOnReset])

    class Fresh(Component):
        citry = app
        template = """
            <p>fresh</p>
        """
        js = """
            console.log("fresh");
        """

    class Card(Component):
        citry = app
        template = """
            <p>card</p>
        """

    classes.update(card=Card, fresh=Fresh)
    _run(lambda: (Card.reset_files(), Card.reset_template()))
    assert len(rendered) == 2
    assert all("fresh" in page for page in rendered)


class Probe(Component):
    citry = Citry(autodiscover=False)
    template = """
        <p>probe</p>
    """


def test_a_const_body_built_during_an_eviction_is_built_again() -> None:
    cache = ConstBodyCache()
    signature: frozenset[tuple[str, Any]] = frozenset()
    builds: list[int] = []

    def build() -> list[Any]:
        builds.append(len(builds))
        if len(builds) == 1:
            # A reset arrives while this build runs.
            cache.evict_component(Probe)
        return [f"body {len(builds)}"]

    assert cache.get_or_build(Probe, signature, build) == ["body 2"]
    assert builds == [0, 1]
    assert cache.get_or_build(Probe, signature, build) == ["body 2"]


def test_const_bodies_stop_building_again_when_evictions_keep_coming() -> None:
    cache = ConstBodyCache()
    signature: frozenset[tuple[str, Any]] = frozenset()
    builds: list[int] = []

    def build() -> list[Any]:
        builds.append(len(builds))
        cache.evict_component(Probe)
        return [f"body {len(builds)}"]

    assert cache.get_or_build(Probe, signature, build) == ["body 3"]
    assert len(builds) == 3


def test_two_threads_building_one_const_body_get_the_body_kept() -> None:
    cache = ConstBodyCache()
    signature: frozenset[tuple[str, Any]] = frozenset()
    inside = threading.Barrier(2, timeout=_JOIN_TIMEOUT)
    bodies: list[list[Any]] = []

    def build() -> list[Any]:
        # Both threads are inside build() at once.
        inside.wait()
        return [threading.current_thread().name]

    _run(
        lambda: bodies.append(cache.get_or_build(Probe, signature, build)),
        lambda: bodies.append(cache.get_or_build(Probe, signature, build)),
    )
    assert bodies[0] is bodies[1]


def test_const_bodies_are_kept_per_loaded_template() -> None:
    # The body comes from the template the render loaded, so a body built
    # from one template is never returned for another.
    cache = ConstBodyCache()
    signature: frozenset[tuple[str, Any]] = frozenset()
    old = cache.get_or_build(Probe, signature, lambda: ["old"], template_id="first")
    new = cache.get_or_build(Probe, signature, lambda: ["new"], template_id="second")
    assert (old, new) == (["old"], ["new"])
    assert cache.get_or_build(Probe, signature, lambda: ["again"], template_id="first") == ["old"]


def test_a_reset_while_a_const_function_runs_shows_the_new_template_afterwards() -> None:
    # The render that started before the reset finishes with the template it
    # loaded; the next render uses the new one.
    app = Citry(autodiscover=False)
    in_build = threading.Event()
    release = threading.Event()

    def helper(value: str) -> str:
        if not in_build.is_set():
            in_build.set()
            release.wait(_JOIN_TIMEOUT)
        return value

    class Page(Component):
        citry = app
        template = """
            <div>OLD {{ helper(value) }}</div>
        """

    def render() -> str:
        return Page(value=Const("fixed"), helper=Const(helper)).render().serialize()

    first: list[str] = []
    renderer = threading.Thread(target=lambda: first.append(render()), daemon=True)
    renderer.start()
    assert in_build.wait(_JOIN_TIMEOUT)
    Page.template = """
            <div>NEW {{ helper(value) }}</div>
        """
    Page.reset_template()
    release.set()
    renderer.join(timeout=_JOIN_TIMEOUT)
    assert not renderer.is_alive()
    assert "OLD fixed" in first[0]
    assert "NEW fixed" in render()


def test_a_load_during_reset_hooks_runs_again_so_its_hook_state_survives() -> None:
    # A load that starts while a reset runs its hooks runs again after them,
    # so per-class state its hook sets is not lost to the reset hook.
    state: dict[type, str] = {}
    in_reset = threading.Event()
    loaded = threading.Event()
    classes: dict[str, type[Component]] = {}

    class Tracking(Extension):
        name = "tracking"

        def on_template_loaded(self, ctx: Any) -> None:
            state[ctx.component_class] = ctx.content
            loaded.set()

        def on_template_reset(self, ctx: Any) -> None:
            if ctx.component_class is classes["card"]:
                in_reset.set()
                # A load on another thread runs its hook now.
                loaded.wait(_JOIN_TIMEOUT)
                state.pop(ctx.component_class, None)

    app = Citry(autodiscover=False, extensions=[Tracking])

    class Card(Component):
        citry = app
        template = """
            <p>card</p>
        """

    classes["card"] = Card
    Card.get_template()
    loaded.clear()

    def load_during_reset() -> None:
        in_reset.wait(_JOIN_TIMEOUT)
        Card.get_template()

    _run(Card.reset_template, load_during_reset)
    assert Card in state


def test_the_component_base_class_has_empty_dependencies() -> None:
    assert Component.get_dependencies().js == ()
