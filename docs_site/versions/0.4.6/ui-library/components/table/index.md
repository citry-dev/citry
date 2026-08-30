---
title: Table
url: https://citry.dev/v/0.4.6/ui-library/components/table/
description: "Present finite server-owned records in a styled native Table."
---
# Table

`CTable` renders finite, read-only tabular data with native HTML semantics. It
owns structure and presentation, not sorting, selection, editing, pagination,
or remote queries.

## Table at a glance

Line and outline variants, three densities, stripes, hover, column borders,
sticky headers, and explicit loading, empty, and error output share one native
Table model.


### Table at a glance

[Open the rendered preview](/v/0.4.6/ui-library/components/table/_previews/at-a-glance/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class TableAtAGlance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="table-glance">
        <article>
          <h2>Inner planets</h2>
          <c-CTable
            c-columns="columns"
            c-rows="inner_rows"
            density="compact"
            striped
          >
            <c-fill name="caption">
              Distance from the Sun
            </c-fill>
          </c-CTable>
        </article>
        <article>
          <h2>Outer planets</h2>
          <c-CTable
            c-columns="columns"
            c-rows="outer_rows"
            variant="outline"
            density="compact"
            hover
          >
            <c-fill name="caption">
              Distance from the Sun
            </c-fill>
          </c-CTable>
        </article>
        <article>
          <h2>Survey pending</h2>
          <c-CTable
            c-columns="columns"
            c-rows="()"
            state="loading"
            density="compact"
            loading_label="Loading orbital survey..."
          />
        </article>
        <article>
          <h2>No matching worlds</h2>
          <c-CTable
            c-columns="columns"
            c-rows="()"
            variant="outline"
            density="compact"
            empty_label="No planets match this orbit."
          />
        </article>
      </section>
    """

    css = """
      :where(.table-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 72rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.table-glance article) {
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#bfdbfe, #1e3a8a);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.table-glance h2) {
        margin: 0 0 0.75rem;
        color: light-dark(#1d4ed8, #93c5fd);
        font-size: 1rem;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("planet", "Planet", row_header=True),
                CTableColumn("distance", "Mean distance", align="end"),
            ),
            "inner_rows": (
                CTableRow("mercury", {"planet": "Mercury", "distance": "57.9 million km"}),
                CTableRow("venus", {"planet": "Venus", "distance": "108.2 million km"}),
                CTableRow("earth", {"planet": "Earth", "distance": "149.6 million km"}),
            ),
            "outer_rows": (
                CTableRow("jupiter", {"planet": "Jupiter", "distance": "778.5 million km"}),
                CTableRow("saturn", {"planet": "Saturn", "distance": "1.43 billion km"}),
                CTableRow("uranus", {"planet": "Uranus", "distance": "2.87 billion km"}),
            ),
        }


preview = TableAtAGlance()

preview  # noqa: B018
````


`CTable` has no component JavaScript or client inputs. Every Table input is a
server input passed through `<c-CTable ... />` or `CTable(...)`. Controls
inside cells keep their own client props and native events.

## Build a Table

Declare columns once, then give every keyed row exactly one value per column.


### List the moons of Jupiter

[Open the rendered preview](/v/0.4.6/ui-library/components/table/_previews/moons-of-jupiter/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class MoonsOfJupiter(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="moon-table">
        <c-CTable
          c-columns="columns"
          c-rows="rows"
          striped
          hover
        >
          <c-fill name="caption">
            Galilean moons
          </c-fill>
        </c-CTable>
      </section>
    """

    css = """
      :where(.moon-table) {
        max-width: 48rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.moon-table [data-column-key="diameter"]) {
        font-variant-numeric: tabular-nums;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("moon", "Moon", row_header=True),
                CTableColumn("discoverer", "Discoverer"),
                CTableColumn("diameter", "Diameter", align="end"),
            ),
            "rows": (
                CTableRow("io", {"moon": "Io", "discoverer": "Galileo", "diameter": "3,643 km"}),
                CTableRow("europa", {"moon": "Europa", "discoverer": "Galileo", "diameter": "3,122 km"}),
                CTableRow("ganymede", {"moon": "Ganymede", "discoverer": "Galileo", "diameter": "5,268 km"}),
                CTableRow("callisto", {"moon": "Callisto", "discoverer": "Galileo", "diameter": "4,821 km"}),
            ),
        }


preview = MoonsOfJupiter()

preview  # noqa: B018
````



```citry-html
<c-CTable
  c-columns="columns"
  c-rows="rows"
  striped
>
  <c-fill name="caption">
    Galilean moons
  </c-fill>
</c-CTable>
```



```python
from citry_ui import CTable, CTableColumn, CTableRow

moon_table = CTable(
    columns=(
        CTableColumn("moon", "Moon", row_header=True),
        CTableColumn("diameter", "Diameter", align="end"),
    ),
    rows=(
        CTableRow("europa", {"moon": "Europa", "diameter": "3,122 km"}),
    ),
    slots={"caption": "Galilean moons"},
)
```


Keys are stable application identity, not display text or array positions.
They must be unique and non-empty. Row and column keys are exposed in escaped
`data-*` attributes, so do not put secrets in them.

Use one `row_header=True` column for the entity or category that identifies
each row. `align="end"` follows text direction and suits numeric values. Add
tabular numerals through `cell_attrs`, a class, or the public cell selector.

## Present rich cells

Raw values are escaped. A `CTableCell` adds attributes to one position, and a
component-like value renders directly. Use the generic `cell` fill when output
depends on the current row and column.


### Build an observation catalog

[Open the rendered preview](/v/0.4.6/ui-library/components/table/_previews/rich-cells/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableCell, CTableColumn, CTableRow

citry.register_library(citry_ui)


class ObservationCatalog(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="observation-catalog">
        <c-CTable
          c-columns="columns"
          c-rows="rows"
          variant="outline"
          hover
        >
          <c-fill name="caption">
            Tonight's observation catalog
          </c-fill>
          <c-fill name="cell" data="{ row, column, cell }">
            <c-if cond="column.key == 'visibility'">
              <span c-class="['visibility', 'visibility--' + cell.value]">
                {{ cell.value }}
              </span>
            </c-if>
            <c-elif cond="column.key == 'action'">
              <c-CButton size="sm" variant="outline">
                View {{ row.key }}
              </c-CButton>
            </c-elif>
            <c-else>
              {{ cell.value }}
            </c-else>
          </c-fill>
        </c-CTable>
      </section>
    """

    css = """
      :where(.observation-catalog) {
        max-width: 58rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.visibility) {
        display: inline-flex;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: capitalize;
      }

      :where(.visibility--excellent) {
        color: light-dark(#166534, #bbf7d0);
        background: light-dark(#dcfce7, #14532d);
      }

      :where(.visibility--limited) {
        color: light-dark(#9a3412, #fed7aa);
        background: light-dark(#ffedd5, #7c2d12);
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("target", "Target", row_header=True),
                CTableColumn("type", "Type"),
                CTableColumn("visibility", "Visibility"),
                CTableColumn("action", "Actions"),
            ),
            "rows": (
                CTableRow(
                    "orion-nebula",
                    {"target": "Orion Nebula", "type": "Nebula", "visibility": "excellent", "action": None},
                ),
                CTableRow(
                    "andromeda",
                    {
                        "target": CTableCell("Andromeda Galaxy", attrs={"class": "featured-target"}),
                        "type": "Galaxy",
                        "visibility": "limited",
                        "action": None,
                    },
                ),
            ),
        }


preview = ObservationCatalog()

preview  # noqa: B018
````



```citry-html
<c-fill name="cell" data="{ row, column, cell }">
  <c-if cond="column.key == 'action'">
    <c-CButton size="sm">
      View {{ row.key }}
    </c-CButton>
  </c-if>
  <c-else>
    {{ cell.value }}
  </c-else>
</c-fill>
```


`header_attrs` targets one column header. `cell_attrs` supplies defaults to
every body cell in that column. `CTableCell.attrs` wins for ordinary duplicate
attributes while class and style contributions merge. Structural values such
as scopes and spans remain Table-owned.

Sorting links, row actions, checkboxes, Inputs, and Comboboxes may live in
cells, but their behavior belongs to those controls. Hover never makes a row
selectable or clickable.

## Add totals and summaries

Set one or more column `footer` values to render a native one-row `tfoot`.
Footer content may be plain text or another component. `footer_attrs` targets
that column's footer cell.


### Summarize telescope time

[Open the rendered preview](/v/0.4.6/ui-library/components/table/_previews/survey-totals/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class SurveyTotals(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="survey-totals">
        <c-CTable
          c-columns="columns"
          c-rows="rows"
          variant="outline"
        >
          <c-fill name="caption">
            Telescope survey time
          </c-fill>
          <c-fill name="footer" data="{ column, value }">
            <c-if cond="column.key == 'hours'">
              <strong>{{ value }}</strong>
            </c-if>
            <c-else>
              {{ value }}
            </c-else>
          </c-fill>
        </c-CTable>
      </section>
    """

    css = """
      :where(.survey-totals) {
        max-width: 44rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.survey-totals [data-citry-ui-part="footer-cell"]) {
        color: light-dark(#1e3a8a, #bfdbfe);
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("program", "Program", row_header=True, footer="Total"),
                CTableColumn("instrument", "Instrument", footer="3 programs"),
                CTableColumn(
                    "hours",
                    "Hours",
                    align="end",
                    cell_attrs={"style": {"font-variant-numeric": "tabular-nums"}},
                    footer="84.5",
                ),
            ),
            "rows": (
                CTableRow("aurora", {"program": "Aurora survey", "instrument": "Spectrograph", "hours": "36.0"}),
                CTableRow("rings", {"program": "Ring survey", "instrument": "Wide-field camera", "hours": "28.5"}),
                CTableRow("comets", {"program": "Comet survey", "instrument": "Infrared camera", "hours": "20.0"}),
            ),
        }


preview = SurveyTotals()

preview  # noqa: B018
````


The `footer` fill receives `{column, value, column_index}` once per footer
cell. Its fallback is the matching column value. The row-header column remains
a row header in the footer.

Version 1 owns one summary row. Multiple footer rows, grouped headers,
`rowspan`, `colspan`, and `colgroup` need a future logical-grid schema.

## Choose appearance


### Compare Table appearance

[Open the rendered preview](/v/0.4.6/ui-library/components/table/_previews/appearance/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class TableAppearance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="table-appearance">
        <article>
          <h2>Line · comfortable</h2>
          <c-CTable c-columns="columns" c-rows="rows" />
        </article>
        <article>
          <h2>Outline · compact</h2>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            variant="outline"
            density="compact"
            column_borders
          />
        </article>
        <article>
          <h2>Striped · default</h2>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            density="default"
            striped
          />
        </article>
        <article>
          <h2>Hover · bottom caption</h2>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            hover
            caption_side="bottom"
          >
            <c-fill name="caption">
              Hover highlights, but never selects, a row.
            </c-fill>
          </c-CTable>
        </article>
      </section>
    """

    css = """
      :where(.table-appearance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
        gap: 1rem;
        max-width: 72rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.table-appearance article) {
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#dbeafe, #1e3a8a);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.table-appearance h2) {
        margin: 0 0 0.75rem;
        font-size: 0.875rem;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("planet", "Planet", row_header=True),
                CTableColumn("gravity", "Gravity", align="end"),
            ),
            "rows": (
                CTableRow("mars", {"planet": "Mars", "gravity": "3.71 m/s²"}),
                CTableRow("neptune", {"planet": "Neptune", "gravity": "11.15 m/s²"}),
            ),
        }


preview = TableAppearance()

preview  # noqa: B018
````


- `variant="line"` separates rows; `outline` also frames the root.
- `density` accepts `default`, `comfortable`, or `compact`.
- `striped` alternates ready-row surfaces.
- `hover` adds pointer feedback without behavior.
- `column_borders` adds vertical separators.
- `caption_side` places a native caption at the top or bottom.
- `layout="fixed"` uses native fixed table layout; set widths through column
  attribute styles, classes, or public selectors.

These are server inputs. Side-by-side examples show their output without
pretending that Table owns browser-reactive configuration.

## Show loading, empty, and error output


### Show survey states

[Open the rendered preview](/v/0.4.6/ui-library/components/table/_previews/states/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn

citry.register_library(citry_ui)


class TableStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="table-states">
        <article>
          <h2>Loading</h2>
          <c-CTable
            c-columns="columns"
            c-rows="()"
            state="loading"
            loading_label="Receiving deep-space survey..."
          >
            <c-fill name="loading">
              Receiving deep-space survey...
            </c-fill>
          </c-CTable>
        </article>
        <article>
          <h2>Empty</h2>
          <c-CTable
            c-columns="columns"
            c-rows="()"
            empty_label="No signals match this wavelength."
          />
        </article>
        <article>
          <h2>Error</h2>
          <c-CTable
            c-columns="columns"
            c-rows="()"
            state="error"
            error_label="The telescope feed is unavailable."
          />
        </article>
      </section>
    """

    css = """
      :where(.table-states) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 68rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.table-states article) {
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#c7d2fe, #3730a3);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.table-states h2) {
        margin: 0 0 0.75rem;
        font-size: 0.875rem;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("signal", "Signal", row_header=True),
                CTableColumn("strength", "Strength", align="end"),
            ),
        }


preview = TableStates()

preview  # noqa: B018
````


The header stays visible. Loading, empty, and error replace body rows with one
native cell spanning every column. Loading sets `aria-busy` on the Table.
Configured footers appear only in ready output, including ready-empty output.

The `loading`, `empty`, and `error` slots change visible content. Their matching
label inputs also feed a persistent polite live region outside the busy Table.
Keep each label consistent with its custom slot.

Entering a state removes stale ready rows. Returning to ready renders the next
complete keyed collection.

## Keep wide and long Tables usable

`overflow="auto"` is the default. It preserves native row and column
relationships and lets two-dimensional data scroll horizontally at narrow
widths or high zoom.


### Keep headers visible

[Open the rendered preview](/v/0.4.6/ui-library/components/table/_previews/sticky-overflow/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class StickyOverflowTable(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="sticky-tables">
        <article>
          <h2>Bounded catalog</h2>
          <p>Scroll this region in either direction.</p>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            sticky_header
            layout="fixed"
            style="max-block-size: 16rem; --cui-table-min-width: 54rem"
          >
            <c-fill name="caption">
              Confirmed exoplanets
            </c-fill>
          </c-CTable>
        </article>
        <article>
          <h2>Page-sticky mode</h2>
          <p>The header follows page scroll instead of an inner scroller.</p>
          <c-CTable
                c-columns="columns"
            c-rows="rows"
            sticky_header
            overflow="visible"
          >
            <c-fill name="caption">
              Nearby exoplanets
            </c-fill>
          </c-CTable>
        </article>
      </section>
    """

    css = """
      :where(.sticky-tables) {
        display: grid;
        gap: 1.25rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.sticky-tables article) {
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#bae6fd, #075985);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.sticky-tables h2, .sticky-tables p) {
        margin: 0;
      }

      :where(.sticky-tables p) {
        margin-block: 0.25rem 0.75rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        columns = (
            CTableColumn("planet", "Planet", row_header=True, cell_attrs={"style": {"width": "12rem"}}),
            CTableColumn("system", "System", cell_attrs={"style": {"width": "14rem"}}),
            CTableColumn("distance", "Distance", align="end", cell_attrs={"style": {"width": "10rem"}}),
            CTableColumn("period", "Orbital period", align="end", cell_attrs={"style": {"width": "10rem"}}),
        )
        rows = tuple(
            CTableRow(
                key,
                {"planet": planet, "system": system, "distance": distance, "period": period},
            )
            for key, planet, system, distance, period in (
                ("proxima-b", "Proxima Centauri b", "Proxima Centauri", "4.2 ly", "11.2 days"),
                ("barnard-b", "Barnard's Star b", "Barnard's Star", "6.0 ly", "233 days"),
                ("ross-128-b", "Ross 128 b", "Ross 128", "11.0 ly", "9.9 days"),
                ("tau-ceti-e", "Tau Ceti e", "Tau Ceti", "11.9 ly", "163 days"),
                ("gj-1061-d", "GJ 1061 d", "GJ 1061", "12.0 ly", "13.0 days"),
                ("teegarden-b", "Teegarden's Star b", "Teegarden's Star", "12.5 ly", "4.9 days"),
                ("wolf-1061-c", "Wolf 1061 c", "Wolf 1061", "14.1 ly", "17.9 days"),
                ("gliese-667-cc", "Gliese 667 Cc", "Gliese 667 C", "23.6 ly", "28.1 days"),
            )
        )
        return {"columns": columns, "rows": rows}


preview = StickyOverflowTable()

preview  # noqa: B018
````


For a bounded scroller, combine `sticky_header=True` with a block-size limit:


```citry-html
<c-CTable
  c-columns="columns"
  c-rows="rows"
  sticky_header
  style="max-block-size: 24rem"
/>
```


For a header that follows page scroll, use `sticky_header=True` with
`overflow="visible"`. The two modes have different scroll ancestors.

Auto overflow always adds one keyboard focus stop because a zero-JavaScript
component cannot measure overflow before deciding. A caption names that region.
Without a caption, set `scroll_label` or name the native Table with
`table_attrs={"aria-label": ...}`. The focus ring stays visible.

An auto-overflow wrapper can clip inline menus, listboxes, and other overlays.
Use a top-layer or portaled overlay when available, or choose visible overflow
when the page can contain the Table.

## Preserve native semantics and focus

Column headers use `<th scope="col">`. The optional row-header column uses
`<th scope="row">`; other cells use `<td>`. A caption supplies the Table's
native accessible name. Use `table_attrs` for `aria-label`, `aria-labelledby`,
or `aria-describedby` when visible caption text is not appropriate.

Table does not use `role="grid"`, move focus with arrow keys, or select rows.
Tab order contains the auto-overflow wrapper and focusable content supplied in
cells. Native table navigation remains available to assistive technology.

Ready rows use private Citry morph keys. Reordering preserves a surviving row
subtree and its control state where Citry can preserve the control. Removing a
row removes its complete subtree. Table does not guess a new focus target.

Sorting, filtering, pagination, and selection belong to controls composed
around the Table. Those controls update server state and render the next
complete `columns` and `rows`; they are not Table callbacks.

## Theme and customize Table

Use `class_`, `style`, public CSS variables, or documented selectors. Do not
target private `.cui-*` classes or `--_cui-*` variables.


### Theme observatory Tables

[Open the rendered preview](/v/0.4.6/ui-library/components/table/_previews/theme-customization/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class ObservatoryTables(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="observatory-tables">
        <article class="observatory-tables__night">
          <h2>Night observation</h2>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            variant="outline"
            striped
          >
            <c-fill name="caption">
              Winter sky
            </c-fill>
          </c-CTable>
        </article>
        <article class="observatory-tables__day">
          <h2>Solar observation</h2>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            variant="outline"
            style="--cui-table-header-background: light-dark(#fef3c7, #78350f)"
          >
            <c-fill name="caption">
              Daylight calibration
            </c-fill>
          </c-CTable>
        </article>
      </section>
    """

    css = """
      :where(.observatory-tables) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
        gap: 1rem;
        max-width: 70rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.observatory-tables article) {
        min-width: 0;
        padding: 1rem;
        border-radius: 0.875rem;
      }

      :where(.observatory-tables h2) {
        margin: 0 0 0.75rem;
        font-size: 1rem;
      }

      :where(.observatory-tables__night) {
        color-scheme: dark;
        color: #e0f2fe;
        background: #0c1b33;
        --cui-table-background: #102a43;
        --cui-table-foreground: #e0f2fe;
        --cui-table-border-color: #486581;
        --cui-table-header-background: #243b53;
        --cui-table-striped-background: #173a5e;
      }

      :where(.observatory-tables__day) {
        color-scheme: light;
        color: #422006;
        background: #fffbeb;
        --cui-table-border-color: #f59e0b;
      }

      :where(.observatory-tables [data-citry-ui-part="footer-cell"]) {
        letter-spacing: 0.02em;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("star", "Star", row_header=True, footer="Brightest"),
                CTableColumn("magnitude", "Magnitude", align="end", footer="-1.46"),
            ),
            "rows": (
                CTableRow("sirius", {"star": "Sirius", "magnitude": "-1.46"}),
                CTableRow("canopus", {"star": "Canopus", "magnitude": "-0.74"}),
                CTableRow("arcturus", {"star": "Arcturus", "magnitude": "-0.05"}),
            ),
        }


preview = ObservatoryTables()

preview  # noqa: B018
````


Variables inherit, so one ancestor can theme several Tables. Set a variable on
one root for an isolated override. Public selectors such as
`[data-citry-ui-part="footer-cell"]` target stable elements. Reflected
attributes expose the selected visual configuration for CSS and inspection.

Nested Tables resolve their own density and variant rules. Structural styles
from an outer Table do not stripe, hover, border, or resize an inner Table.
Public color variables may intentionally inherit unless the nested root
overrides them.

## Support direction, long content, and print


### Read translated star names

[Open the rendered preview](/v/0.4.6/ui-library/components/table/_previews/environment/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTable, CTableColumn, CTableRow

citry.register_library(citry_ui)


class TableEnvironment(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="table-environment" dir="rtl">
        <h2>أسماء النجوم</h2>
        <c-CTable
          c-columns="columns"
          c-rows="rows"
          variant="outline"
          striped
          style="--cui-table-min-width: 42rem"
        >
          <c-fill name="caption">
            أسماء عربية وتقليدية للنجوم
          </c-fill>
        </c-CTable>
      </section>
    """

    css = """
      :where(.table-environment) {
        max-width: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.table-environment h2) {
        margin: 0 0 0.75rem;
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 1rem;
      }

      :where(.table-environment [data-column-key="notes"]) {
        min-width: 18rem;
        white-space: normal;
        overflow-wrap: anywhere;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        nested = CTable(
            columns=(CTableColumn("planet", "الكوكب"),),
            rows=(CTableRow("earth", {"planet": "الأرض"}),),
            density="compact",
            overflow="visible",
            slots={"caption": "نظام نجمي"},
        )
        return {
            "columns": (
                CTableColumn("name", "الاسم", row_header=True),
                CTableColumn("meaning", "المعنى"),
                CTableColumn("notes", "ملاحظات"),
            ),
            "rows": (
                CTableRow(
                    "betelgeuse",
                    {
                        "name": "منكب الجوزاء",
                        "meaning": "كتف الجبار",
                        "notes": "نجم أحمر فائق الضخامة في كوكبة الجبار، واسمه التقليدي طويل عند نقله بين اللغات.",
                    },
                ),
                CTableRow(
                    "nested",
                    {"name": "الشمس", "meaning": "نجمنا", "notes": nested},
                ),
            ),
        }


preview = TableEnvironment()

preview  # noqa: B018
````


Logical alignment follows LTR and RTL. Long text wraps by default; use fixed
layout and explicit widths only when truncation or stable columns improve the
task. At narrow widths and 400% zoom, surrounding content still reflows while
the Table may scroll as a two-dimensional exception.

Default colors support light and dark scopes. Forced colors retains text,
focus, and borders without using stripes or hover as the only signal. Print
removes overflow clipping and sticky positioning.

`CTable` targets ordinary finite collections. The repository's diagnostic
scaling harness records server rendering at 10, 100, and 1,000 rows; hosted
results remain release evidence, not a performance guarantee. Virtualization,
grouped headers, interactive grid navigation, editing, and remote collection
ownership belong to a future DataTable/DataGrid.

## API reference

### Inputs

#### CTable server inputs

Server inputs are passed in a template through `<c-CTable ... />` or in Python through
`CTable(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 9rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="table-input-ctable-server-inputs-columns"></span>`columns` | `Sequence[CTableColumn]` | required | Defines the structural column schema. |
| <span id="table-input-ctable-server-inputs-rows"></span>`rows` | `Sequence[CTableRow]` | required | Defines the keyed server-owned collection. |
| <span id="table-input-ctable-server-inputs-state"></span>`state` | `"ready" | "loading" | "error"` ([`CTableState`](#table-interface-input-type-aliases-ctable-state)) | `"ready"` | Selects body output. Ready with no rows selects empty output. |
| <span id="table-input-ctable-server-inputs-id"></span>`id` | `str | None` | generated | Sets wrapper and caption identity. |
| <span id="table-input-ctable-server-inputs-variant"></span>`variant` | `"line" | "outline"` ([`CTableVariant`](#table-interface-input-type-aliases-ctable-variant)) | `"line"` | Selects border presentation. |
| <span id="table-input-ctable-server-inputs-density"></span>`density` | `"default" | "comfortable" | "compact"` ([`CTableDensity`](#table-interface-input-type-aliases-ctable-density)) | `"comfortable"` | Selects cell sizing. |
| <span id="table-input-ctable-server-inputs-striped"></span>`striped` | `bool` | `False` | Adds alternating ready-row backgrounds. |
| <span id="table-input-ctable-server-inputs-hover"></span>`hover` | `bool` | `False` | Adds pointer hover feedback without adding row behavior. |
| <span id="table-input-ctable-server-inputs-sticky-header"></span>`sticky_header` | `bool` | `False` | Sticks header cells within the scroll ancestor. |
| <span id="table-input-ctable-server-inputs-column-borders"></span>`column_borders` | `bool` | `False` | Adds vertical separators. |
| <span id="table-input-ctable-server-inputs-layout"></span>`layout` | `"auto" | "fixed"` ([`CTableLayout`](#table-interface-input-type-aliases-ctable-layout)) | `"auto"` | Selects native `table-layout`. |
| <span id="table-input-ctable-server-inputs-overflow"></span>`overflow` | `"auto" | "visible"` ([`CTableOverflow`](#table-interface-input-type-aliases-ctable-overflow)) | `"auto"` | Selects horizontal wrapper behavior. |
| <span id="table-input-ctable-server-inputs-caption-side"></span>`caption_side` | `"top" | "bottom"` ([`CTableCaptionSide`](#table-interface-input-type-aliases-ctable-caption-side)) | `"top"` | Places the native caption. |
| <span id="table-input-ctable-server-inputs-scroll-label"></span>`scroll_label` | `non-empty str | None` | Uses the caption or native Table ARIA name when available. | Names the `overflow="auto"` focusable region. |
| <span id="table-input-ctable-server-inputs-loading-label"></span>`loading_label` | `non-empty str` | `"Loading data..."` | Sets the loading fallback and persistent polite announcement text. |
| <span id="table-input-ctable-server-inputs-empty-label"></span>`empty_label` | `non-empty str` | `"No data."` | Sets the empty fallback and persistent polite announcement text. |
| <span id="table-input-ctable-server-inputs-error-label"></span>`error_label` | `non-empty str` | `"Unable to load data."` | Sets the error fallback and persistent polite announcement text. |
| <span id="table-input-ctable-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#table-interface-input-type-aliases-class-value)) | `None` | Adds wrapper classes from a string, conditional mapping, or nested sequence and merges them with `attrs`. |
| <span id="table-input-ctable-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#table-interface-input-type-aliases-style-value)) | `None` | Adds wrapper inline styles from CSS text, a property mapping, or a nested sequence and merges them with `attrs`. |
| <span id="table-input-ctable-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed wrapper attributes; prefer the top-level inputs for class and style. |
| <span id="table-input-ctable-server-inputs-table-attrs"></span>`table_attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native table and ARIA attributes. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CTable slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="table-slot-ctable-slots-caption"></span>`caption` | no | `{}` ([`CTableCaptionSlotData`](#table-interface-ctable-caption-slot-data)) | No caption. |
| <span id="table-slot-ctable-slots-header"></span>`header` | no | `{column: CTableColumn, column_index: int}` ([`CTableHeaderSlotData`](#table-interface-ctable-header-slot-data)) | Escaped column label. |
| <span id="table-slot-ctable-slots-cell"></span>`cell` | no | `{row: CTableRow, column: CTableColumn, cell: CTableCell, row_index: int, column_index: int}` ([`CTableCellSlotData`](#table-interface-ctable-cell-slot-data)) | Escaped or component-like cell value. |
| <span id="table-slot-ctable-slots-footer"></span>`footer` | no | `{column: CTableColumn, value: object | None, column_index: int}` ([`CTableFooterSlotData`](#table-interface-ctable-footer-slot-data)) | Escaped or component-like column footer value. |
| <span id="table-slot-ctable-slots-empty"></span>`empty` | no | `{}` ([`CTableEmptySlotData`](#table-interface-ctable-empty-slot-data)) | `empty_label` |
| <span id="table-slot-ctable-slots-loading"></span>`loading` | no | `{}` ([`CTableLoadingSlotData`](#table-interface-ctable-loading-slot-data)) | `loading_label` |
| <span id="table-slot-ctable-slots-error"></span>`error` | no | `{}` ([`CTableErrorSlotData`](#table-interface-ctable-error-slot-data)) | `error_label` |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTable CSS variables

Apply these variables to `CTable` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="table-css-ctable-css-variables-cui-table-background"></span>`--cui-table-background` | `color` | Table surface. | `Canvas` |
| <span id="table-css-ctable-css-variables-cui-table-foreground"></span>`--cui-table-foreground` | `color` | Primary text. | `CanvasText` |
| <span id="table-css-ctable-css-variables-cui-table-muted-foreground"></span>`--cui-table-muted-foreground` | `color` | Caption and subdued status text. | `Muted CanvasText mix.` |
| <span id="table-css-ctable-css-variables-cui-table-border-color"></span>`--cui-table-border-color` | `color` | Row, outline, footer, and optional column borders. | `Subtle CanvasText mix.` |
| <span id="table-css-ctable-css-variables-cui-table-header-background"></span>`--cui-table-header-background` | `color` | Header surface, including sticky headers. | `Subtle CanvasText/Canvas mix.` |
| <span id="table-css-ctable-css-variables-cui-table-footer-background"></span>`--cui-table-footer-background` | `color` | Footer surface. | `Subtle CanvasText/Canvas mix.` |
| <span id="table-css-ctable-css-variables-cui-table-striped-background"></span>`--cui-table-striped-background` | `color` | Alternating ready-row surface. | `Subtle CanvasText/Canvas mix.` |
| <span id="table-css-ctable-css-variables-cui-table-hover-background"></span>`--cui-table-hover-background` | `color` | Ready-row pointer hover surface. | `Subtle Highlight/Canvas mix.` |
| <span id="table-css-ctable-css-variables-cui-table-error-foreground"></span>`--cui-table-error-foreground` | `color` | Error status text. | `Scheme-aware negative color.` |
| <span id="table-css-ctable-css-variables-cui-table-focus-color"></span>`--cui-table-focus-color` | `color` | Overflow-region focus ring. | `Highlight` |
| <span id="table-css-ctable-css-variables-cui-table-radius"></span>`--cui-table-radius` | `length` | Outline and wrapper radius. | `0.625rem` |
| <span id="table-css-ctable-css-variables-cui-table-cell-block-padding"></span>`--cui-table-cell-block-padding` | `length` | Logical block cell padding. | `Density-derived length.` |
| <span id="table-css-ctable-css-variables-cui-table-cell-inline-padding"></span>`--cui-table-cell-inline-padding` | `length` | Logical inline cell padding. | `Density-derived length.` |
| <span id="table-css-ctable-css-variables-cui-table-caption-padding"></span>`--cui-table-caption-padding` | `CSS padding shorthand` | Caption spacing. | `0.75rem 1rem` |
| <span id="table-css-ctable-css-variables-cui-table-min-width"></span>`--cui-table-min-width` | `length` | Minimum width before horizontal overflow. | `32rem` |
| <span id="table-css-ctable-css-variables-cui-table-sticky-offset"></span>`--cui-table-sticky-offset` | `length` | Sticky header block offset. | `0px` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTable attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="table-attribute-root-data-state"></span>`data-state` | Root | `"ready" | "loading" | "error"` | Mirrors effective body-output state. |
| <span id="table-attribute-root-data-variant"></span>`data-variant` | Root | `"line" | "outline"` | Mirrors effective border presentation. |
| <span id="table-attribute-root-data-density"></span>`data-density` | Root | `"default" | "comfortable" | "compact"` | Mirrors effective cell density. |
| <span id="table-attribute-root-data-striped"></span>`data-striped` | Root | `present | absent` | Mirrors striped-row presentation. |
| <span id="table-attribute-root-data-hover"></span>`data-hover` | Root | `present | absent` | Mirrors pointer-hover presentation. |
| <span id="table-attribute-root-data-sticky-header"></span>`data-sticky-header` | Root | `present | absent` | Mirrors sticky-header configuration. |
| <span id="table-attribute-root-data-column-borders"></span>`data-column-borders` | Root | `present | absent` | Mirrors column-border presentation. |
| <span id="table-attribute-root-data-layout"></span>`data-layout` | Root | `"auto" | "fixed"` | Mirrors effective native table layout. |
| <span id="table-attribute-root-data-overflow"></span>`data-overflow` | Root | `"auto" | "visible"` | Mirrors horizontal overflow behavior. |
| <span id="table-attribute-root-data-caption-side"></span>`data-caption-side` | Root | `"top" | "bottom"` | Mirrors effective caption placement. |

</div>

#### CTable attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="table-attribute-row-data-row-key"></span>`data-row-key` | Ready row | `string` | Canonical row identity. |

</div>

#### CTable attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="table-attribute-cell-data-column-key"></span>`data-column-key` | Header, body, or footer cell | `string` | Canonical column identity. |
| <span id="table-attribute-cell-data-align"></span>`data-align` | Header, body, or footer cell | `"start" | "center" | "end"` | Logical cell alignment. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTable selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="table-selector-root"></span>`[data-citry-ui-part="root"]` | Root | Wrapper, scroll container, and `attrs` destination. |
| <span id="table-selector-table"></span>`[data-citry-ui-part="table"]` | Native Table | Table and `table_attrs` destination. |
| <span id="table-selector-caption"></span>`[data-citry-ui-part="caption"]` | Native caption | Optional caption hook. |
| <span id="table-selector-header"></span>`[data-citry-ui-part="header"]` | Header group | Native header group. |
| <span id="table-selector-header-row"></span>`[data-citry-ui-part="header-row"]` | Header row | Native header row. |
| <span id="table-selector-header-cell"></span>`[data-citry-ui-part="header-cell"]` | Header cell | Column-header hook. |
| <span id="table-selector-body"></span>`[data-citry-ui-part="body"]` | Body group | Native body group. |
| <span id="table-selector-row"></span>`[data-citry-ui-part="row"]` | Ready row | Keyed row hook. |
| <span id="table-selector-cell"></span>`[data-citry-ui-part="cell"]` | Body cell | Ready data-cell or row-header hook. |
| <span id="table-selector-state-row"></span>`[data-citry-ui-part="state-row"]` | State row | Loading, empty, or error row. |
| <span id="table-selector-state-cell"></span>`[data-citry-ui-part="state-cell"]` | State cell | Cell spanning every column. |
| <span id="table-selector-loading"></span>`[data-citry-ui-part="loading"]` | Loading region | Loading status content. |
| <span id="table-selector-empty"></span>`[data-citry-ui-part="empty"]` | Empty region | Empty status content. |
| <span id="table-selector-error"></span>`[data-citry-ui-part="error"]` | Error region | Error status content. |
| <span id="table-selector-footer"></span>`[data-citry-ui-part="footer"]` | Native footer group | Optional summary group. |
| <span id="table-selector-footer-row"></span>`[data-citry-ui-part="footer-row"]` | Native footer row | One summary row. |
| <span id="table-selector-footer-cell"></span>`[data-citry-ui-part="footer-cell"]` | Footer cell | Per-column summary cell. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="table-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="table-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="table-interface-input-type-aliases-ctable-state"></span>`CTableState` | `Literal["ready", "loading", "error"]` |
| <span id="table-interface-input-type-aliases-ctable-variant"></span>`CTableVariant` | `Literal["line", "outline"]` |
| <span id="table-interface-input-type-aliases-ctable-density"></span>`CTableDensity` | `Literal["default", "comfortable", "compact"]` |
| <span id="table-interface-input-type-aliases-ctable-align"></span>`CTableAlign` | `Literal["start", "center", "end"]` |
| <span id="table-interface-input-type-aliases-ctable-layout"></span>`CTableLayout` | `Literal["auto", "fixed"]` |
| <span id="table-interface-input-type-aliases-ctable-overflow"></span>`CTableOverflow` | `Literal["auto", "visible"]` |
| <span id="table-interface-input-type-aliases-ctable-caption-side"></span>`CTableCaptionSide` | `Literal["top", "bottom"]` |

</div>

<span id="table-interface-ctable-column"></span>

#### `CTableColumn`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="table-interface-ctable-column-key"></span>`key` | `non-empty str` | required | Unique column identity. |
| <span id="table-interface-ctable-column-label"></span>`label` | `non-empty str` | required | Default escaped header content. |
| <span id="table-interface-ctable-column-row-header"></span>`row_header` | `bool` | False | Renders body cells in this column as `<th scope="row">`. |
| <span id="table-interface-ctable-column-align"></span>`align` | `"start" | "center" | "end"` ([`CTableAlign`](#table-interface-input-type-aliases-ctable-align)) | "start" | Sets logical header and cell alignment. |
| <span id="table-interface-ctable-column-header-attrs"></span>`header_attrs` | `Mapping[str, object] | None` | None | Adds allowed native attributes to the column header. |
| <span id="table-interface-ctable-column-cell-attrs"></span>`cell_attrs` | `Mapping[str, object] | None` | None | Adds defaults to every body cell in the column; a specific `CTableCell.attrs` value wins while class and style merge. |
| <span id="table-interface-ctable-column-footer"></span>`footer` | `object | None` | None | Supplies fallback content for the optional footer cell. Any non-None value enables the footer. |
| <span id="table-interface-ctable-column-footer-attrs"></span>`footer_attrs` | `Mapping[str, object] | None` | None | Adds allowed native attributes to the footer cell. |

</div>

<span id="table-interface-ctable-row"></span>

#### `CTableRow`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="table-interface-ctable-row-key"></span>`key` | `non-empty str` | required | Unique row and morph identity. |
| <span id="table-interface-ctable-row-cells"></span>`cells` | `Mapping[str, object | CTableCell]` | required | Supplies exactly one value for every declared column key. |
| <span id="table-interface-ctable-row-attrs"></span>`attrs` | `Mapping[str, object] | None` | None | Adds allowed native attributes to the row. |

</div>

<span id="table-interface-ctable-cell"></span>

#### `CTableCell`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="table-interface-ctable-cell-value"></span>`value` | `object` | required | Default escaped or component-like cell content. |
| <span id="table-interface-ctable-cell-attrs"></span>`attrs` | `Mapping[str, object] | None` | None | Adds allowed native cell attributes. |

</div>

<span id="table-interface-ctable-caption-slot-data"></span>

#### `CTableCaptionSlotData`

Empty dataclass: `{}`.

<span id="table-interface-ctable-header-slot-data"></span>

#### `CTableHeaderSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="table-interface-ctable-header-slot-data-column"></span>`column` | `CTableColumn` | - | Current column declaration. |
| <span id="table-interface-ctable-header-slot-data-column-index"></span>`column_index` | `int` | - | Zero-based column position. |

</div>

<span id="table-interface-ctable-cell-slot-data"></span>

#### `CTableCellSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="table-interface-ctable-cell-slot-data-row"></span>`row` | `CTableRow` | - | Current row declaration. |
| <span id="table-interface-ctable-cell-slot-data-column"></span>`column` | `CTableColumn` | - | Current column declaration. |
| <span id="table-interface-ctable-cell-slot-data-cell"></span>`cell` | `CTableCell` | - | Normalized cell declaration. |
| <span id="table-interface-ctable-cell-slot-data-row-index"></span>`row_index` | `int` | - | Zero-based row position. |
| <span id="table-interface-ctable-cell-slot-data-column-index"></span>`column_index` | `int` | - | Zero-based column position. |

</div>

<span id="table-interface-ctable-footer-slot-data"></span>

#### `CTableFooterSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="table-interface-ctable-footer-slot-data-column"></span>`column` | `CTableColumn` | - | Current column declaration. |
| <span id="table-interface-ctable-footer-slot-data-value"></span>`value` | `object | None` | - | Current column footer value. |
| <span id="table-interface-ctable-footer-slot-data-column-index"></span>`column_index` | `int` | - | Zero-based column position. |

</div>

<span id="table-interface-ctable-empty-slot-data"></span>

#### `CTableEmptySlotData`

Empty dataclass: `{}`.

<span id="table-interface-ctable-loading-slot-data"></span>

#### `CTableLoadingSlotData`

Empty dataclass: `{}`.

<span id="table-interface-ctable-error-slot-data"></span>

#### `CTableErrorSlotData`

Empty dataclass: `{}`.

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CTable translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="table-translation-ctable-translations-loading"></span>`citry-ui-table-loading` | Labels and announces the loading state. | `None` | `loading_label` input or `loading` slot | $c-tr updates component fallback text and the announcer. |
| <span id="table-translation-ctable-translations-empty"></span>`citry-ui-table-empty` | Labels and announces an empty ready state. | `None` | `empty_label` input or `empty` slot | $c-tr updates component fallback text and the announcer. |
| <span id="table-translation-ctable-translations-error"></span>`citry-ui-table-error` | Labels and announces the error state. | `None` | `error_label` input or `error` slot | $c-tr updates component fallback text and the announcer. |

</div>