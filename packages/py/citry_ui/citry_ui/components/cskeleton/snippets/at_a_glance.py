import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonGlance(Component):
    template = """
      <section class="skeleton-glance" aria-label="Loading field note" aria-busy="true">
        <c-CSkeleton height="8rem" animation="wave" />
        <c-CRow c-gap="'sm'">
          <c-CSkeleton kind="circle" width="2.75rem" />
          <c-CSkeleton kind="text" c-lines="3" />
        </c-CRow>
      </section>
    """
    css = """
      :where(.skeleton-glance) {
        display: grid;
        max-inline-size: 24rem;
        gap: 1rem;
        padding: 1rem;
        border: 1px solid light-dark(#b8cbb9, #425947);
        border-radius: 0.9rem;
      }
    """


preview = SkeletonGlance()
preview  # noqa: B018
