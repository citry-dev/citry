"""Research-only Citry components for the landing-page component field."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from itertools import count as counter
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

from citry import Citry, Component

Renderer = Literal["baseline", "dom", "canvas"]

SUPPORTED_COUNTS = (256, 512, 1024, 2048, 4096)
COORDINATE_SCALE = 1_000_000
FIELD_ASPECT_RATIO = 8 / 5
ARRIVAL_FRONT_MS = 1_600
CELL_SETTLE_MS = 350
RIPPLE_FRONT_MS = 550
MAX_CANVAS_PIXELS = 8_000_000
ASSET_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class CellDescriptor:
    """One server-created logical cell shared by both projection strategies."""

    cell_id: int
    x_ppm: int
    y_ppm: int
    phase_ms: int
    palette: int

    def compact(self) -> tuple[int, int, int, int, int]:
        """Return the stable numeric wire representation used by canvas."""
        return (self.cell_id, self.x_ppm, self.y_ppm, self.phase_ms, self.palette)


class LiteralCellData(TypedDict):
    cell_id: int
    style: dict[str, str]


class CanvasCellData(TypedDict):
    descriptor: str


@dataclass(slots=True)
class Scenario:
    """One isolated Citry registry and one deterministic research page."""

    renderer: Renderer
    count: int
    columns: int
    rows: int
    descriptor_sha256: str
    descriptors: tuple[CellDescriptor, ...]
    citry: Citry
    page_type: type[Component]
    tracker: dict[str, int]

    def render(self) -> tuple[str, int]:
        """Render one complete page and return HTML plus rendered cell count."""
        before = self.tracker["cell_renders"]
        html = self.page_type().render().serialize(deps_strategy="document")
        return html, self.tracker["cell_renders"] - before


def build_descriptors(count: int) -> tuple[tuple[CellDescriptor, ...], int, int]:
    """Build the deterministic centered grid used by DOM and canvas."""
    if count not in SUPPORTED_COUNTS:
        msg = f"cell count must be one of {SUPPORTED_COUNTS}, got {count}"
        raise ValueError(msg)

    columns = math.ceil(math.sqrt(count * FIELD_ASPECT_RATIO))
    rows = math.ceil(count / columns)
    final_row_count = count - (rows - 1) * columns
    descriptors: list[CellDescriptor] = []

    for cell_id in range(count):
        row, column = divmod(cell_id, columns)
        row_offset = (columns - final_row_count) / 2 if row == rows - 1 else 0
        x = (column + row_offset) / columns
        y = row / rows
        distance = math.hypot(x, y) / math.sqrt(2)
        descriptors.append(
            CellDescriptor(
                cell_id=cell_id,
                x_ppm=round(x * COORDINATE_SCALE),
                y_ppm=round(y * COORDINATE_SCALE),
                phase_ms=round(distance * ARRIVAL_FRONT_MS),
                palette=(row + column) % 4,
            )
        )

    return tuple(descriptors), columns, rows


def descriptor_sha256(descriptors: tuple[CellDescriptor, ...]) -> str:
    """Hash the exact ordered descriptor list for cross-renderer checks."""
    payload = json.dumps([descriptor.compact() for descriptor in descriptors], separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _literal_cells(descriptors: tuple[CellDescriptor, ...]) -> list[LiteralCellData]:
    return [
        {
            "cell_id": descriptor.cell_id,
            "style": {
                "--cell-x": f"{descriptor.x_ppm / COORDINATE_SCALE:.6f}",
                "--cell-y": f"{descriptor.y_ppm / COORDINATE_SCALE:.6f}",
                "--cell-phase": f"{descriptor.phase_ms}ms",
                "--cell-tone": str(descriptor.palette),
            },
        }
        for descriptor in descriptors
    ]


def _canvas_cells(descriptors: tuple[CellDescriptor, ...]) -> list[CanvasCellData]:
    cells: list[CanvasCellData] = []
    for index, descriptor in enumerate(descriptors):
        prefix = "," if index else ""
        wire = json.dumps(descriptor.compact(), separators=(",", ":"))
        cells.append({"descriptor": prefix + wire})
    return cells


def _field_template(renderer: Renderer, body: str) -> str:
    return f"""
      <section
        class="component-field"
        data-field-root
        data-renderer="{renderer}"
        c-data-cell-count="count"
        c-data-descriptor-sha256="descriptor_sha256"
        c-data-columns="columns"
        c-data-rows="rows"
      >
        <div class="component-field__surface" data-field-surface aria-hidden="true">
          {body}
        </div>
        <div class="component-field__copy">
          <p class="component-field__eyebrow">
            FREE AND OPEN SOURCE · MIT LICENSE · PYTHON
          </p>
          <h1>Build the frontend in Python.</h1>
          <p class="component-field__lede">
            Citry is an HTML-first frontend framework for Python web apps,
            built around reusable components.
          </p>
          <div class="component-field__actions">
            <a class="component-field__primary" href="#proof">
              Build your first component
            </a>
            <button type="button" data-field-trigger>Send a wave</button>
            <button type="button" data-field-pause aria-pressed="false">
              Pause motion
            </button>
          </div>
          <code>pip install citry</code>
          <p class="component-field__scope">
            Server-rendered HTML · Django, FastAPI, and Flask · No separate
            frontend build
          </p>
          <p class="component-field__status" data-field-status aria-live="polite">
            Component field ready.
          </p>
        </div>
      </section>
    """


def _page_template(field_name: str) -> str:
    return f"""
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>Citry component-field research</title>
          <script>
            window.__fieldVitals = {{
              cls: 0,
              lcp: null,
              paints: [],
              longTasks: [],
              events: [],
              droppedEntries: 0,
            }};
            for (const type of [
              "layout-shift",
              "largest-contentful-paint",
              "paint",
              "longtask",
              "event",
            ]) {{
              try {{
                const observer = new PerformanceObserver((list) => {{
                  const vitals = window.__fieldVitals;
                  for (const entry of list.getEntries()) {{
                    if (type === "layout-shift" && !entry.hadRecentInput) {{
                      vitals.cls += entry.value;
                    }} else if (type === "largest-contentful-paint") {{
                      vitals.lcp = entry.startTime;
                    }} else if (type === "paint") {{
                      vitals.paints.push({{ name: entry.name, startTime: entry.startTime }});
                    }} else if (type === "longtask") {{
                      vitals.longTasks.push({{ startTime: entry.startTime, duration: entry.duration }});
                    }} else if (type === "event") {{
                      vitals.events.push({{
                        name: entry.name,
                        startTime: entry.startTime,
                        duration: entry.duration,
                        interactionId: entry.interactionId,
                      }});
                    }}
                  }}
                }});
                observer.observe({{
                  type,
                  buffered: true,
                  durationThreshold: type === "event" ? 16 : undefined,
                }});
              }} catch (error) {{
                window.__fieldVitals[type + "Unsupported"] = String(error);
              }}
            }}
          </script>
          <noscript>
            <style>
              [data-field-trigger], [data-field-pause], [data-field-status] {{
                display: none !important;
              }}
            </style>
          </noscript>
          <c-css />
        </head>
        <body>
          <c-{field_name} />
          <main id="proof" class="research-proof">
            <h2>One component, a complete UI path</h2>
            <p>
              This fixed shell keeps representative landing-page copy and
              lower content in every renderer measurement.
            </p>
            <div class="research-proof__grid">
              <article><h3>Checked inputs</h3><p>Inputs fail at a named component boundary.</p></article>
              <article><h3>Owned behavior</h3><p>Browser behavior belongs to its Python component.</p></article>
              <article><h3>Server interaction</h3><p>Python handlers update ordinary HTML.</p></article>
            </div>
          </main>
          <c-js />
        </body>
      </html>
    """


def build_scenario(renderer: Renderer, count: int) -> Scenario:
    """Create one isolated renderer/count scenario with stable component IDs."""
    if renderer not in ("baseline", "dom", "canvas"):
        msg = f"unknown renderer {renderer!r}"
        raise ValueError(msg)

    descriptors, columns, rows = build_descriptors(count)
    digest = descriptor_sha256(descriptors)
    render_ids = counter(1)
    citry_instance = Citry(
        autodiscover=False,
        id_generator=lambda: f"r{next(render_ids):07x}",
    )
    citry_instance.set_mounted_prefix("/citry")
    tracker = {"cell_renders": 0}

    class LiteralCell(Component):
        citry = citry_instance
        name = "research-literal-cell"

        class Kwargs:
            cell_id: int
            style: dict[str, str]

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
            del slots
            tracker["cell_renders"] += 1
            return {"cell_id": kwargs.cell_id, "style": kwargs.style}

        template = """
          <i
            class="component-field__cell"
            data-field-cell
            c-data-cell-id="cell_id"
            c-style="style"
          ></i>
        """

    class CanvasCell(Component):
        citry = citry_instance
        name = "research-canvas-cell"
        transparent = True

        class Kwargs:
            descriptor: str

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, str]:
            del slots
            tracker["cell_renders"] += 1
            return {"descriptor": kwargs.descriptor}

        template = """
          {{ descriptor }}
        """

    class BaselineField(Component):
        citry = citry_instance
        name = "research-baseline-field"

        class Kwargs:
            pass

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, int | str]:
            del kwargs, slots
            return {
                "columns": columns,
                "count": 0,
                "descriptor_sha256": digest,
                "rows": rows,
            }

        template = _field_template(
            "baseline",
            '<div class="component-field__plane" data-field-plane></div>',
        )
        css_file = ASSET_DIR / "field.css"
        js_file = ASSET_DIR / "baseline_field.js"

    class LiteralField(Component):
        citry = citry_instance
        name = "research-literal-field"

        class Kwargs:
            pass

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
            del kwargs, slots
            return {
                "cells": _literal_cells(descriptors),
                "columns": columns,
                "count": count,
                "descriptor_sha256": digest,
                "rows": rows,
            }

        template = _field_template(
            "dom",
            """
              <div
                class="component-field__plane"
                data-field-plane
                c-style="{ '--columns': columns, '--rows': rows }"
              >
                <c-research-literal-cell
                  c-for="cell in cells"
                  c-cell_id="cell['cell_id']"
                  c-style="cell['style']"
                />
              </div>
            """,
        )
        css_file = ASSET_DIR / "field.css"
        js_file = ASSET_DIR / "dom_field.js"

    class CanvasField(Component):
        citry = citry_instance
        name = "research-canvas-field"

        class Kwargs:
            pass

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
            del kwargs, slots
            return {
                "cells": _canvas_cells(descriptors),
                "columns": columns,
                "count": count,
                "descriptor_sha256": digest,
                "rows": rows,
            }

        template = _field_template(
            "canvas",
            """
              <div
                class="component-field__plane component-field__plane--canvas"
                data-field-plane
                c-style="{ '--columns': columns, '--rows': rows }"
              >
                <canvas data-field-canvas></canvas>
                <script type="application/json" data-field-descriptors>
                  [<c-research-canvas-cell
                    c-for="cell in cells"
                    c-descriptor="cell['descriptor']"
                  />]
                </script>
              </div>
            """,
        )
        css_file = ASSET_DIR / "field.css"
        js_file = ASSET_DIR / "canvas_field.js"

    field_types: dict[Renderer, type[Component]] = {
        "baseline": BaselineField,
        "dom": LiteralField,
        "canvas": CanvasField,
    }
    field_type = field_types[renderer]
    field_name = cast("str", field_type.name)

    class ResearchPage(Component):
        citry = citry_instance
        name = f"research-{renderer}-page"

        class Kwargs:
            pass

        class Slots:
            pass

        template = _page_template(field_name)
        css_file = ASSET_DIR / "page.css"

    return Scenario(
        renderer=renderer,
        count=count,
        columns=columns,
        rows=rows,
        descriptor_sha256=digest,
        descriptors=descriptors,
        citry=citry_instance,
        page_type=ResearchPage,
        tracker=tracker,
    )


def parse_canvas_descriptors(html: str) -> list[list[int]]:
    """Parse the inert descriptor block from a rendered canvas page."""
    start_marker = '<script type="application/json" data-field-descriptors>'
    start = html.find(start_marker)
    if start < 0:
        msg = "rendered page has no canvas descriptor block"
        raise ValueError(msg)
    start += len(start_marker)
    end = html.find("</script>", start)
    if end < 0:
        msg = "canvas descriptor block has no closing script tag"
        raise ValueError(msg)
    value = json.loads(html[start:end])
    if not isinstance(value, list):
        msg = "canvas descriptor block must contain a list"
        raise TypeError(msg)
    return cast("list[list[int]]", value)


def component_asset_paths() -> tuple[Path, ...]:
    """Return every hand-authored asset that contributes to the proof."""
    return (
        Path(__file__).resolve(),
        ASSET_DIR / "baseline_field.js",
        ASSET_DIR / "canvas_field.js",
        ASSET_DIR / "dom_field.js",
        ASSET_DIR / "field.css",
        ASSET_DIR / "page.css",
    )


def component_fixture_sha256() -> str:
    """Hash the proof source so evidence identifies the exact fixture."""
    digest = hashlib.sha256()
    for path in component_asset_paths():
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()
