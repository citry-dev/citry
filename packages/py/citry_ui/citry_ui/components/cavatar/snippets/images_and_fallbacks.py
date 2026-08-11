import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)

PORTRAIT = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 80'%3E"
    "%3Crect width='80' height='80' fill='%23365f50'/%3E"
    "%3Ccircle cx='40' cy='31' r='14' fill='%23f4d6b0'/%3E"
    "%3Cpath d='M13 80c4-22 15-32 27-32s23 10 27 32' fill='%238fc5a8'/%3E%3C/svg%3E"
)


class AvatarImages(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="avatar-image-grid">
        <div><c-CAvatar c-src="portrait" alt="Fen cartographer">FC</c-CAvatar><span>Loaded</span></div>
        <div>
          <c-CAvatar src="/missing-moonfen-portrait.png" alt="Marsh scout">MS</c-CAvatar>
          <span>Error fallback</span>
        </div>
        <div><c-CAvatar alt="Unassigned explorer" /><span>Generic fallback</span></div>
      </div>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"portrait": PORTRAIT}

    css = """
      :where(.avatar-image-grid) {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-image-grid > div) {
        display: grid;
        justify-items: center;
        gap: 0.35rem;
        color: light-dark(#315546, #b7ddc8);
        font-size: 0.75rem;
      }
    """


preview = AvatarImages()

preview  # noqa: B018
