"""Run bounded diagnostic rendering profiles for Citry UI scaling."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict, dataclass
from functools import partial
from time import perf_counter
from typing import TYPE_CHECKING, cast

import citry_ui
from citry import Citry, Component

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True, slots=True)
class ScalingSample:
    """One diagnostic-only render measurement."""

    profile: str
    count: int
    median_ms: float
    output_bytes: int
    status: str = "diagnostic-only"


def _measure(render: Callable[[], str], *, samples: int) -> tuple[float, int]:
    durations: list[float] = []
    size = 0
    for _ in range(samples):
        start = perf_counter()
        output = render()
        durations.append((perf_counter() - start) * 1_000)
        size = len(output.encode())
    return statistics.median(durations), size


def _render_scaled(component: Callable[..., object], count: int) -> str:
    return str(component(count=count))


def scaling_report(*, counts: tuple[int, ...], samples: int = 3) -> dict[str, object]:
    """Measure Button instances and Table row counts without setting timing gates."""
    if samples < 1:
        msg = "samples must be at least 1"
        raise ValueError(msg)
    if not counts or any(isinstance(count, bool) or count < 1 for count in counts):
        msg = "counts must contain positive integers"
        raise ValueError(msg)

    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class ButtonScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"items": tuple(range(kwargs.count))}

        template = """
          <div>
            <c-for each="item in items">
              <c-CButton #c-key="item">
                Action {{ item }}
              </c-CButton>
            </c-for>
          </div>
        """

    class TableScale(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "columns": (
                    citry_ui.CTableColumn("id", "ID", row_header=True),
                    citry_ui.CTableColumn("value", "Value"),
                ),
                "rows": tuple(
                    citry_ui.CTableRow(str(index), {"id": index, "value": f"Row {index}"})
                    for index in range(kwargs.count)
                ),
            }

        template = """
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            density="compact"
          />
        """

    results: list[ScalingSample] = []
    # Mypy does not apply ComponentMeta.__call__ to concrete component classes,
    # while Pyright correctly sees the composition call. Use the metaclass's
    # real callable shape locally so this diagnostic can keep normal public
    # component composition without suppressing individual constructor calls.
    button_element = cast("Callable[..., object]", ButtonScale)
    table_element = cast("Callable[..., object]", TableScale)
    for count in counts:
        median_ms, output_bytes = _measure(partial(_render_scaled, button_element, count), samples=samples)
        results.append(ScalingSample("button-instances", count, round(median_ms, 3), output_bytes))
        median_ms, output_bytes = _measure(partial(_render_scaled, table_element, count), samples=samples)
        results.append(ScalingSample("table-rows", count, round(median_ms, 3), output_bytes))
    return {
        "schema": "citry-ui-scaling-report/v1",
        "samples_per_count": samples,
        "results": [asdict(result) for result in results],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure bounded Citry UI scaling profiles.")
    parser.add_argument("--counts", default="1,10,100,500,1000")
    parser.add_argument("--samples", type=int, default=3)
    args = parser.parse_args()
    try:
        counts = tuple(int(value) for value in args.counts.split(","))
        report = scaling_report(counts=counts, samples=args.samples)
    except ValueError as error:
        parser.exit(1, f"citry-ui scaling profile failed: {error}\n")
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
