import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarShapes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="avatar-shapes">
        <c-for each="shape in shapes">
          <div>
            <c-CAvatar c-shape="shape" c-alt="f'{shape} spirit guide'" variant="soft">SG</c-CAvatar>
            <span>{{ shape }}</span>
          </div>
        </c-for>
      </div>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"shapes": ("circle", "rounded", "square")}

    css = """
      :where(.avatar-shapes) {
        display: flex;
        gap: 1rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-shapes > div) {
        display: grid;
        justify-items: center;
        gap: 0.35rem;
        font-size: 0.75rem;
        text-transform: capitalize;
      }
    """


preview = AvatarShapes()

preview  # noqa: B018
