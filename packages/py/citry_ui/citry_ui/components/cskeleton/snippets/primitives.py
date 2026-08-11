import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonPrimitives(Component):
    template = """
      <div class="skeleton-primitives" aria-label="Loading archive specimens" aria-busy="true">
        <c-CSkeleton width="10rem" height="5rem" />
        <c-CSkeleton kind="circle" width="3rem" />
        <c-CSkeleton kind="text" width="12rem" />
      </div>
    """
    css = """
      :where(.skeleton-primitives) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
      }
    """


preview = SkeletonPrimitives()
preview  # noqa: B018
