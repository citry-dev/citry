import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonCard(Component):
    template = """
      <c-CCard c-attrs="{'aria-label': 'Loading moonfern field note', 'aria-busy': 'true'}">
        <c-fill name="media"><c-CSkeleton height="9rem" /></c-fill>
        <c-fill name="default">
          <c-CCol c-gap="'sm'">
            <c-CSkeleton kind="text" height="1.2rem" width="48%" />
            <c-CSkeleton kind="text" c-lines="3" />
          </c-CCol>
        </c-fill>
      </c-CCard>
    """


preview = SkeletonCard()
preview  # noqa: B018
