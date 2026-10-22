"""
``<c-benchmark-text part="errors-hint" />`` prints one sentence the landing
page's benchmark cards share with the README.

The README carries the same two benchmark charts as the landing page, as
images with the cards' sentences around them (see
``docs_site/scripts/benchmark_readme.py``). Both places print each sentence
from the one function that builds it, so the landing page and the README
cannot say different things, and a new benchmark run updates the counts and
versions in both.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from citry import Component
from docs_site.scripts import benchmark_readme

if TYPE_CHECKING:
    from collections.abc import Callable

# Each part's sentence, built from the benchmark data the chart beside it draws.
PARTS: dict[str, Callable[[], str]] = {
    "errors-intro": lambda: benchmark_readme.errors_intro(benchmark_readme.load_data("errors")),
    "errors-hint": lambda: benchmark_readme.ERRORS_HINT,
    "errors-note": lambda: benchmark_readme.errors_note(benchmark_readme.load_data("errors")),
    "speed-intro": lambda: benchmark_readme.speed_intro(benchmark_readme.load_data("speed")),
    "speed-note": lambda: benchmark_readme.speed_note(benchmark_readme.load_data("speed")),
}


class BenchmarkText(Component):
    """``<c-benchmark-text part="errors-hint" />`` prints one shared benchmark sentence as plain text."""

    transparent = True

    class Kwargs:
        # Which sentence to print; PARTS lists them.
        part: Literal["errors-intro", "errors-hint", "errors-note", "speed-intro", "speed-note"]

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"text": PARTS[str(kwargs.part)]()}

    template = """
      {{ text }}
    """
