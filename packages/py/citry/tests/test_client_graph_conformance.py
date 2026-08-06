"""
Replay every valid `citry-client-graph/1` golden fixture through the Python producer.

Each scenario below is the canonical component setup for one golden fixture in
``packages/protocol/client_graph/v1/tests/``. The test renders the scenario
with every environment-dependent input pinned and compares the emitted
manifest to the frozen fixture, so the Python producer cannot drift from the
published protocol package silently.

Three inputs normally vary per machine or process, and the harness pins all
of them so the manifest (including its SHA-256 revision) is reproducible:

- render ids come from a process-global randomized counter; the harness
  installs a per-render ``Citry.id_generator`` counting ``c1``, ``c2``, ...
- class ids embed an md5 of the class's import path; the harness patches the
  import-path lookup to the fixed ``citry_fixture.<ClassName>``.
- template origins embed the defining module's file path; the harness patches
  the inline-template origin to the fixed ``fixture://<ClassName>``.

Regenerating fixtures after a deliberate producer or format change:

    .venv/bin/python packages/py/citry/tests/test_client_graph_conformance.py --freeze

then rerun the protocol package checks and commit the fixture diffs together
with the change that caused them.
"""

from __future__ import annotations

import itertools
import json
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

import citry.assets as citry_assets
import citry.component as citry_component
from citry import Citry, Component, Extension
from citry.nodes import ComponentNode

_ROOT = Path(__file__).resolve().parents[4]
_FIXTURES = _ROOT / "packages" / "protocol" / "client_graph" / "v1" / "tests"
_GRAPH_RE = re.compile(r'<script type="application/json" data-citry-graph>(.*?)</script>', re.DOTALL)


@contextmanager
def _pinned_identity() -> Iterator[None]:
    """Make class ids and template origins machine-independent while active."""
    original_import_path = citry_component.get_import_path
    original_inline_origin = citry_assets._inline_origin

    def fixture_import_path(cls_or_fn: object) -> str:
        name = getattr(cls_or_fn, "__name__", None)
        if name:
            return f"citry_fixture.{name}"
        return original_import_path(cls_or_fn)

    citry_component.get_import_path = fixture_import_path
    citry_assets._inline_origin = lambda cls: f"fixture://{cls.__name__}"
    try:
        yield
    finally:
        citry_component.get_import_path = original_import_path
        citry_assets._inline_origin = original_inline_origin


def _render_html(engine: Citry, root_factory: Callable[[], Component]) -> str:
    """Render the scenario with pinned render ids into a self-contained page."""
    counter = itertools.count(1)
    engine.id_generator = lambda: f"c{next(counter)}"
    return root_factory().render().serialize()


def manifest_from_html(html: str) -> dict:
    """Return the decoded graph manifest embedded in a rendered page."""
    match = _GRAPH_RE.search(html)
    assert match is not None, "the scenario render emitted no graph manifest"
    return json.loads(match.group(1))


def scenario_minimal() -> str:
    """The smallest client-active render: one class, one root instance."""
    with _pinned_identity():
        engine = Citry(mode="development")

        class Host(Component):
            citry = engine
            js = """
              $component(() => {});
            """
            template = """
              <p>host</p>
            """

        return _render_html(engine, Host)


def scenario_component_tag_client_bindings() -> str:
    """One nested component carrying all four component-tag client binding payloads."""
    with _pinned_identity():

        class AddRangeIgnore(Extension):
            name = "fixture_range_ignore"

            def on_template_compiled(self, ctx):
                if ctx.component_class is not Page:
                    return
                index, node = next(
                    (index, node) for index, node in enumerate(ctx.nodes) if isinstance(node, ComponentNode)
                )
                assert node.metadata is not None
                assert node.metadata[0] == "range"
                ctx.nodes[index] = ComponentNode(
                    node.source,
                    node.position,
                    node.attrs,
                    node.body,
                    node.used_vars,
                    node.name,
                    node.contains_fills,
                    (*node.metadata, ("morph", "ignore")),
                )

        engine = Citry(mode="development", extensions=[AddRangeIgnore])

        class Child(Component):
            citry = engine
            js = """
              $component(() => {});
            """
            template = """
              <section>child</section>
            """

        class Page(Component):
            citry = engine

            class Events:
                def save(self):
                    return None

                def tick(self):
                    return None

            # The pollchange handler locks the poll-versus-DOM-event rule: only
            # the exact event segment "poll" is a poll, so a custom DOM event
            # whose name merely starts with "poll" stays a DOM event.
            template = """
              <c-child
                #c-key="graph_key"
                $c-props="{n: 1}"
                @click="open = true"
                @c-click.prevent="save({x: 1})"
                @c-keyup.enter.debounce.300ms="save({y: 2})"
                @c-pollchange="save({z: 3})"
                @c-poll.5s="tick()"
              />
            """

            def template_data(self, kwargs, slots):
                return {"graph_key": '</script><x>&"π'}

        return _render_html(engine, Page)


def scenario_dynamic_spread_loop() -> str:
    """Spread and server-dynamic component-tag client bindings from a loop."""
    with _pinned_identity():
        engine = Citry(mode="development")

        class Item(Component):
            citry = engine
            js = """
              $component(() => {});
            """
            template = """
              <button><c-slot /></button>
            """

        class Page(Component):
            citry = engine

            class Events:
                def choose(self):
                    return None

            template = """
              <ul>
                <c-for each="item in items">
                  <li>
                    <c-item
                      c-$c-props="item['props']"
                      c-bind="item['handlers']"
                    >{{ item['label'] }}</c-item>
                  </li>
                </c-for>
              </ul>
            """

            def template_data(self, kwargs, slots):
                return {
                    "items": [
                        {
                            "label": f"row-{index}",
                            "props": f"{{index: {index}}}",
                            "handlers": {"@click": "selected = true", "@c-click": "choose"},
                        }
                        for index in range(2)
                    ]
                }

        return _render_html(engine, Page)


def scenario_supplied_fills() -> str:
    """A named template fill whose one slot renders through two outlets."""
    with _pinned_identity():
        engine = Citry(mode="development")

        class Card(Component):
            citry = engine
            template = """
              <article>
                <header><c-slot name="title" /></header>
                <aside><c-slot name="title" /></aside>
              </article>
            """

        class Page(Component):
            citry = engine
            template = """
              <c-card>
                <c-fill name="title"><b x-text="title"></b></c-fill>
              </c-card>
            """

        return _render_html(engine, Page)


def scenario_fallback_fill() -> str:
    """An unsupplied slot rendering its own client-active fallback."""
    with _pinned_identity():
        engine = Citry(mode="development")

        class Card(Component):
            citry = engine
            template = """
              <section><c-slot><i x-text="label">fallback</i></c-slot></section>
            """

        class Page(Component):
            citry = engine
            template = """
              <c-card />
            """

        return _render_html(engine, Page)


def scenario_detached_fills() -> str:
    """A Python-supplied slot plus an unsupplied typed default on one receiver."""
    with _pinned_identity():
        engine = Citry(mode="development")

        class Card(Component):
            citry = engine

            class Events:
                def noop(self):
                    return None

            class Slots:
                default: str
                header: str = "typed default header"

            template = """
              <div>
                <header><c-slot name="header" /></header>
                <main><c-slot /></main>
              </div>
            """

        return _render_html(engine, lambda: Card(slots={"default": "python content"}))


def scenario_nested_slot_regions() -> str:
    """Nested cache boundaries: region ancestry, transitions, transparency."""
    with _pinned_identity():
        engine = Citry(mode="development")

        class Active(Component):
            citry = engine
            js = """
              $component(() => {});
            """
            template = """
              <p>active</p>
            """

        class Page(Component):
            citry = engine
            template = """
              <c-cache key="outer">
                <c-cache key="inner">
                  <c-active />
                </c-cache>
              </c-cache>
            """

        return _render_html(engine, Page)


def scenario_multi_graph() -> str:
    """A page embedding a separately rendered component: two graphs, one manifest."""
    with _pinned_identity():
        engine = Citry(mode="development")

        class Foreign(Component):
            citry = engine
            js = """
              $component(() => {});
            """
            template = """
              <div>foreign</div>
            """

        class Page(Component):
            citry = engine

            class Events:
                def save(self):
                    return None

            template = """
              <main>{{ foreign }}</main>
            """

            def template_data(self, kwargs, slots):
                return {"foreign": foreign_renders.pop()}

        # The foreign component renders before (and outside of) the page
        # render; embedding the finished result is what creates the second
        # graph. Rendering it inside template_data would join the page graph.
        foreign_renders: list = []

        def build_root() -> Component:
            foreign_renders.append(Foreign().render())
            return Page()

        return _render_html(engine, build_root)


def scenario_utf8_offsets() -> str:
    """Count UTF-8 bytes before a component-tag client binding."""
    with _pinned_identity():
        engine = Citry(mode="development")

        class Child(Component):
            citry = engine
            template = """
              <span>x</span>
            """

        class Page(Component):
            citry = engine

            class Events:
                def save(self):
                    return None

            template = """π<c-child @c-click="save()" />"""

        return _render_html(engine, Page)


SCENARIOS: dict[str, Callable[[], str]] = {
    "minimal": scenario_minimal,
    "component_tag_client_bindings": scenario_component_tag_client_bindings,
    "dynamic_spread_loop": scenario_dynamic_spread_loop,
    "supplied_fills": scenario_supplied_fills,
    "fallback_fill": scenario_fallback_fill,
    "detached_fills": scenario_detached_fills,
    "nested_slot_regions": scenario_nested_slot_regions,
    "multi_graph": scenario_multi_graph,
    "utf8_offsets": scenario_utf8_offsets,
}


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_producer_matches_golden_fixture(name: str) -> None:
    produced = manifest_from_html(SCENARIOS[name]())
    frozen = json.loads((_FIXTURES / f"{name}.manifest.json").read_text(encoding="utf8"))
    assert produced == frozen


def test_pinned_scenarios_are_deterministic() -> None:
    for name, scenario in SCENARIOS.items():
        first = json.dumps(manifest_from_html(scenario()), sort_keys=True)
        second = json.dumps(manifest_from_html(scenario()), sort_keys=True)
        assert first == second, f"scenario {name} is not deterministic under the pinned harness"


def main() -> int:
    if "--freeze" not in sys.argv[1:]:
        print(__doc__)  # noqa: T201 - standalone regeneration CLI
        return 1
    for name, scenario in SCENARIOS.items():
        path = _FIXTURES / f"{name}.manifest.json"
        manifest = manifest_from_html(scenario())
        path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf8")
        print(f"froze {path.name}")  # noqa: T201 - standalone regeneration CLI
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
