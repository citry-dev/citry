"""Shared Table scenario used by Phase 7.5 quality tools."""

from __future__ import annotations

import citry_ui
from citry import Citry, Component


def table_states_component(app: Citry) -> type[Component]:
    """Create the reusable Table state catalog."""

    class CitryUiTableStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack"
            aria-labelledby="table-states-title"
          >
            <h1 id="table-states-title">
              Table states
            </h1>
            <c-CTable
              id="quality-ready-table"
              c-columns="columns"
              c-rows="rows"
              variant="outline"
              density="compact"
              striped
              hover
              sticky_header
              column_borders
              layout="fixed"
              c-table_attrs="{'aria-label': 'Delivery work'}"
            >
              <c-fill name="caption">
                Current delivery work
              </c-fill>
              <c-fill
                name="header"
                data="{ column }"
              >
                {{ column.label }}
              </c-fill>
              <c-fill
                name="cell"
                data="{ cell, column }"
              >
                <c-if cond="column.key == 'health'">
                  <strong>
                    {{ cell.value }}
                  </strong>
                </c-if>
                <c-else>
                  {{ cell.value }}
                </c-else>
              </c-fill>
            </c-CTable>
            <c-CTable
              c-columns="columns"
              c-rows="()"
              c-table_attrs="{'aria-label': 'Empty delivery work'}"
            >
              <c-fill name="empty">
                No delivery work matches the filters.
              </c-fill>
            </c-CTable>
            <c-CTable
              c-columns="columns"
              c-rows="()"
              state="loading"
              c-table_attrs="{'aria-label': 'Loading delivery work'}"
            />
            <c-CTable
              c-columns="columns"
              c-rows="()"
              state="error"
              c-table_attrs="{'aria-label': 'Failed delivery work'}"
            />
            <c-CTable
              c-columns="columns"
              c-rows="large_rows"
              density="compact"
              overflow="auto"
              sticky_header
              style="max-block-size: 18rem"
              c-table_attrs="{'aria-label': 'Large delivery work'}"
            />
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            columns = (
                citry_ui.CTableColumn("project", "Project", row_header=True, footer="Total"),
                citry_ui.CTableColumn("owner", "Owner"),
                citry_ui.CTableColumn("stage", "Stage"),
                citry_ui.CTableColumn("health", "Health", align="end", footer="2 records"),
            )
            rows = (
                citry_ui.CTableRow(
                    "apollo",
                    {
                        "project": "Apollo",
                        "owner": "Ada Lovelace",
                        "stage": "Security review",
                        "health": "On track",
                    },
                ),
                citry_ui.CTableRow(
                    "mercury",
                    {
                        "project": "Mercury",
                        "owner": "Grace Hopper",
                        "stage": "Rollout",
                        "health": "Needs attention",
                    },
                ),
            )
            large_rows = tuple(
                citry_ui.CTableRow(
                    f"project-{index}",
                    {
                        "project": f"Project {index}",
                        "owner": "Delivery team",
                        "stage": "Implementation",
                        "health": "On track",
                    },
                )
                for index in range(1, 101)
            )
            return {"columns": columns, "rows": rows, "large_rows": large_rows}

    return CitryUiTableStates
