import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonMotion(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="skeleton-motion" aria-label="Loading archive shelves" aria-busy="true">
        <c-for each="motion in motions">
          <div><span>{{ motion }}</span><c-CSkeleton c-animation="motion" height="2.5rem" /></div>
        </c-for>
      </div>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"motions": ("pulse", "wave", "none")}

    css = """
      :where(.skeleton-motion) {
        display: grid;
        gap: 0.75rem;
      }

      :where(.skeleton-motion > div) {
        display: grid;
        grid-template-columns: 4rem 1fr;
        align-items: center;
        gap: 0.75rem;
        font: 0.75rem ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = SkeletonMotion()
preview  # noqa: B018
