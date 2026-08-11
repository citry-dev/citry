import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarVariants(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="avatar-variants">
        <c-for each="variant in variants">
          <div>
            <strong>{{ variant }}</strong>
            <c-for each="size in sizes">
              <c-CAvatar c-variant="variant" c-size="size" c-alt="f'{variant} {size} guide'">MF</c-CAvatar>
            </c-for>
          </div>
        </c-for>
      </div>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"variants": ("soft", "solid", "outline"), "sizes": ("sm", "md", "lg")}

    css = """
      :where(.avatar-variants) {
        display: grid;
        gap: 0.8rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-variants > div) {
        display: flex;
        align-items: center;
        gap: 0.65rem;
      }

      :where(.avatar-variants strong) {
        inline-size: 4.5rem;
        color: light-dark(#315546, #b7ddc8);
        font-size: 0.75rem;
        text-transform: capitalize;
      }
    """


preview = AvatarVariants()

preview  # noqa: B018
