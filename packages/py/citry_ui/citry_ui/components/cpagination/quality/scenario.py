"""Shared Pagination scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def pagination_states_component(app: Citry) -> type[Component]:
    class CitryUiPaginationStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-pagination-ready>
            <h1>Pagination states</h1>
            <c-CPagination c-pages="100" c-page="50" href="?page={page}" c-show_edges="True" />
            <c-CPagination c-pages="12" c-page="1" variant="outline" size="sm" />
            <c-CPagination c-pages="12" c-page="12" variant="plain" size="lg" />
            <c-CPagination c-pages="8" c-page="4" c-disabled="True" />
            <div dir="rtl"><c-CPagination c-pages="20" c-page="8" /></div>
            <div style="color-scheme:dark"><c-CPagination c-pages="9" c-page="3" /></div>
          </section>
        """

    return CitryUiPaginationStates
