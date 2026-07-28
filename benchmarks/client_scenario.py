"""Reusable production-shaped client graph workload for benchmarks and budgets."""

from __future__ import annotations

import gzip
import re
from dataclasses import dataclass
from itertools import count as counter

from citry import Citry, Component

_GRAPH_RE = re.compile(r'<script type="application/json" data-citry-graph>(.*?)</script>', re.DOTALL)
_BENCHMARK_CLASS_MODULE = "citry_benchmarks.client_scenario"


@dataclass(frozen=True)
class ClientPayloadSizes:
    graph_raw: int
    graph_gzip: int
    document_raw: int
    document_gzip: int


@dataclass(frozen=True)
class ClientScenario:
    """One Citry registry and its document, shell, and fresh-fragment builders."""

    citry: Citry
    page_type: type[Component]
    morph_page_type: type[Component]
    morph_document_type: type[Component]
    shell_type: type[Component]
    count: int

    def document(self) -> str:
        return self.page_type().render().serialize()

    def shell(self) -> str:
        return self.shell_type().render().serialize()

    def fragment(self) -> str:
        self.citry.set_mounted_prefix("/citry")
        return self.page_type().render().serialize(deps_strategy="fragment")

    def morph_document(self) -> str:
        return self.morph_document_type().render().serialize()

    def morph_fragment(self) -> str:
        self.citry.set_mounted_prefix("/citry")
        return self.morph_page_type().render().serialize(deps_strategy="fragment")


def build_client_scenario(count: int, *, managed_effects: bool = True) -> ClientScenario:
    """Build N children with component-tag client bindings through server ancestry."""
    if count < 1:
        msg = "client benchmark count must be positive"
        raise ValueError(msg)

    # A fixed-width, HTML-case-safe sequence makes both raw and compressed
    # payload measurements repeatable across processes. A benchmark workload
    # stays far below the seven hexadecimal digits available here.
    render_ids = counter(1)
    c = Citry(id_generator=lambda: f"b{next(render_ids):07x}")
    item_js = (
        """
          $component({
            props: { index: { type: Number, required: true } },
            init: ({ props, scope, effect }) => {
              window.__citryBenchInits = (window.__citryBenchInits || 0) + 1;
              effect(() => { scope.index = props.index; });
              return () => {
                window.__citryBenchCleanups = (window.__citryBenchCleanups || 0) + 1;
              };
            },
          });
        """
        if managed_effects
        else None
    )

    class Item(Component):
        citry = c
        js = item_js
        template = '<button class="bench-item"><c-slot /></button>'

    class MorphItem(Component):
        citry = c
        js = item_js
        template = '<button class="bench-item" x-text="index"></button>'

    def items_data() -> dict[str, object]:
        return {
            "items": [
                {
                    "index": index,
                    "label": f"row-{index}",
                    "props": f"{{ index: {index} }}",
                    "handlers": {
                        "@click": "selected = true",
                        "@c-click": "choose",
                    },
                }
                for index in range(count)
            ]
        }

    class Page(Component):
        citry = c

        class Events:
            def choose(self) -> None:
                return None

        template = """
          <ul class="bench-list" x-data="{ selected: false }">
            <c-for each="item in items">
              <li>
                <c-item
                  #c-key="item['index']"
                  c-$c-props="item['props']"
                  c-bind="item['handlers']"
                >{{ item['label'] }}</c-item>
              </li>
            </c-for>
          </ul>
        """

        def template_data(self, _kwargs: dict[str, object], _slots: object) -> dict[str, object]:
            return items_data()

    class MorphPage(Component):
        citry = c

        class Events:
            def choose(self) -> None:
                return None

        template = """
          <section class="bench-list" x-data="{ selected: false }">
            <c-for each="item in items">
              <c-morph-item
                #c-key="item['index']"
                c-$c-props="item['props']"
                c-bind="item['handlers']"
              />
            </c-for>
          </section>
        """

        def template_data(self, _kwargs: dict[str, object], _slots: object) -> dict[str, object]:
            return items_data()

    class MorphDocument(Component):
        citry = c
        template = '<main class="bench-morph-document"><c-morph-page /></main>'

    class Shell(Component):
        citry = c

        class Events:
            def warm(self) -> None:
                return None

        template = """
          <html>
            <head><title>Citry client benchmark shell</title></head>
            <body><div id="fragment-target"></div></body>
          </html>
        """

    # A single benchmark command may build several counts in one Python
    # process. Give each workload distinct component classes and asset-cache
    # identities so one count cannot reuse another count's server registry.
    item_name = f"client-bench-item-{count}"
    morph_item_name = f"client-bench-morph-item-{count}"
    page_name = f"client-bench-page-{count}"
    morph_page_name = f"client-bench-morph-page-{count}"
    item_variant = type(
        f"ClientBenchItem{count}",
        (Item,),
        {"__module__": _BENCHMARK_CLASS_MODULE, "name": item_name},
    )
    morph_item_variant = type(
        f"ClientBenchMorphItem{count}",
        (MorphItem,),
        {"__module__": _BENCHMARK_CLASS_MODULE, "name": morph_item_name},
    )
    page_variant = type(
        f"ClientBenchPage{count}",
        (Page,),
        {
            "__module__": _BENCHMARK_CLASS_MODULE,
            "name": page_name,
            "template": Page.template.replace("<c-item", f"<c-{item_name}").replace("</c-item>", f"</c-{item_name}>"),
        },
    )
    morph_page_variant = type(
        f"ClientBenchMorphPage{count}",
        (MorphPage,),
        {
            "__module__": _BENCHMARK_CLASS_MODULE,
            "name": morph_page_name,
            "template": MorphPage.template.replace("<c-morph-item", f"<c-{morph_item_name}"),
        },
    )
    morph_document_variant = type(
        f"ClientBenchMorphDocument{count}",
        (MorphDocument,),
        {
            "__module__": _BENCHMARK_CLASS_MODULE,
            "name": f"client-bench-morph-document-{count}",
            "template": f'<main class="bench-morph-document"><c-{morph_page_name} /></main>',
        },
    )
    shell_variant = type(
        f"ClientBenchShell{count}",
        (Shell,),
        {"__module__": _BENCHMARK_CLASS_MODULE, "name": f"client-bench-shell-{count}"},
    )
    del item_variant, morph_item_variant

    return ClientScenario(
        citry=c,
        page_type=page_variant,
        morph_page_type=morph_page_variant,
        morph_document_type=morph_document_variant,
        shell_type=shell_variant,
        count=count,
    )


def payload_sizes(html: str) -> ClientPayloadSizes:
    """Return deterministic raw and gzip byte counts for graph JSON and response."""
    match = _GRAPH_RE.search(html)
    if match is None:
        msg = "client benchmark document contains no ownership graph"
        raise ValueError(msg)
    graph = match.group(1).encode("utf8")
    document = html.encode("utf8")
    return ClientPayloadSizes(
        graph_raw=len(graph),
        graph_gzip=len(gzip.compress(graph, mtime=0)),
        document_raw=len(document),
        document_gzip=len(gzip.compress(document, mtime=0)),
    )
