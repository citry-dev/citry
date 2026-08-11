"""Shared Skeleton scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def skeleton_states_component(app: Citry) -> type[Component]:
    class CitryUiSkeletonStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack"
            aria-label="Loading archive"
            aria-busy="true"
            data-quality-skeleton-ready
          >
            <h1>Skeleton states</h1>
            <c-for each="animation in animations">
              <c-CSkeleton c-animation="animation" height="3rem" />
            </c-for>
            <c-CSkeleton kind="circle" width="3rem" />
            <c-CSkeleton kind="text" c-lines="4" last_line_width="42%" />
            <div dir="rtl"><c-CSkeleton kind="text" c-lines="2" /></div>
            <div style="color-scheme:dark"><c-CSkeleton height="2rem" /></div>
            <div class="skeleton-quality-brand"><c-CSkeleton animation="wave" height="4rem" /></div>
          </section>
        """

        def template_data(
            self,
            kwargs: Kwargs,  # noqa: ARG002
            slots: Slots,  # noqa: ARG002
        ) -> dict[str, object]:
            return {"animations": ("pulse", "wave", "none")}

        css = """
          :where(.skeleton-quality-brand) {
            --cui-skeleton-background: light-dark(#c9dfc8, #36513c);
            --cui-skeleton-highlight: light-dark(rgb(255 255 255 / 70%), rgb(190 239 200 / 28%));
          }
        """

    return CitryUiSkeletonStates
