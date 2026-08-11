"""Shared List scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def list_states_component(app: Citry) -> type[Component]:
    class CitryUiListStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-list-ready>
            <h1>List states</h1>
            <c-CList label="Navigation" variant="surface" c-divided="True">
              <c-CListItem href="/sky" c-current="True">Sky</c-CListItem>
              <c-CListItem href="/sessions">Sessions</c-CListItem>
              <c-CListItem href="/archive" c-disabled="True">Archive</c-CListItem>
            </c-CList>
            <c-CList c-ordered="True" marker="decimal" c-start="3">
              <c-CListItem>Align</c-CListItem>
              <c-CListItem>Calibrate</c-CListItem>
            </c-CList>
            <c-CList label="Anatomy" density="compact">
              <c-CListItem>
                <c-fill name="start"><c-CIcon name="star" /></c-fill>
                <c-fill name="default">Murchison meteorite</c-fill>
                <c-fill name="description">
                  Long unbroken text wrapswithoutcreatinghorizontaloverflowatnarrowwidths
                </c-fill>
                <c-fill name="end"><c-CBadge>Rare</c-CBadge></c-fill>
              </c-CListItem>
            </c-CList>
            <div dir="rtl">
              <c-CList marker="disc">
                <c-CListItem>RTL item</c-CListItem>
              </c-CList>
            </div>
            <div style="color-scheme:dark">
              <c-CList variant="surface">
                <c-CListItem c-action="True">Night action</c-CListItem>
              </c-CList>
            </div>
          </section>
        """

    return CitryUiListStates
