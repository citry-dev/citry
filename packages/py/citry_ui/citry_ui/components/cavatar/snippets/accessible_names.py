import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarNames(Component):
    template = """
      <div class="avatar-name-list">
        <div><c-CAvatar alt="Mira Vale">MV</c-CAvatar><span>Named identity</span></div>
        <div><c-CAvatar><span aria-hidden="true">MF</span></c-CAvatar><span>Decorative companion</span></div>
      </div>
    """
    css = """
      :where(.avatar-name-list) {
        display: grid;
        gap: 0.75rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-name-list > div) {
        display: flex;
        align-items: center;
        gap: 0.75rem;
      }
    """


preview = AvatarNames()

preview  # noqa: B018
