import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonCustomization(Component):
    template = """
      <div class="skeleton-lichen" aria-label="Loading lichen plates" aria-busy="true">
        <c-CSkeleton height="5rem" animation="wave" />
        <c-CSkeleton kind="text" c-lines="3" />
      </div>
    """
    css = """
      :where(.skeleton-lichen) {
        --cui-skeleton-background: light-dark(#c9dfc8, #36513c);
        --cui-skeleton-highlight: light-dark(rgb(255 255 255 / 70%), rgb(190 239 200 / 28%));
        --cui-skeleton-radius: 1rem;
        display: grid;
        max-inline-size: 24rem;
        gap: 1rem;
      }
    """


preview = SkeletonCustomization()
preview  # noqa: B018
