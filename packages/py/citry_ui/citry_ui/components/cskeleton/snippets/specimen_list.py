import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonList(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="skeleton-list" aria-label="Loading specimen index" aria-busy="true">
        <c-for each="item in items">
          <c-CRow #c-key="item" c-gap="'sm'" c-align="'center'">
            <c-CSkeleton kind="circle" width="2.5rem" />
            <c-CSkeleton kind="text" c-lines="2" c-last_line_width="f'{45 + item * 8}%'" />
            <c-CSkeleton width="3.5rem" height="1.5rem" />
          </c-CRow>
        </c-for>
      </div>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"items": (0, 1, 2)}

    css = """
      :where(.skeleton-list) {
        display: grid;
        max-inline-size: 30rem;
        gap: 1rem;
      }

      :where(.skeleton-list [data-citry-ui-part="row"] > :nth-child(2)) {
        flex: 1 1 auto;
      }
    """


preview = SkeletonList()
preview  # noqa: B018
