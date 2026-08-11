import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonText(Component):
    template = """
      <div class="skeleton-text" aria-label="Loading fern description" aria-busy="true">
        <c-CSkeleton kind="text" height="1.15rem" width="55%" />
        <c-CSkeleton kind="text" c-lines="4" last_line_width="38%" />
      </div>
    """
    css = """
      :where(.skeleton-text) {
        display: grid;
        max-inline-size: 30rem;
        gap: 1rem;
      }
    """


preview = SkeletonText()
preview  # noqa: B018
