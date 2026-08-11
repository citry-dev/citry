import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarComposition(Component):
    template = """
      <div class="avatar-party">
        <div class="avatar-party__member">
          <c-CAvatar alt="Mira Vale">MV</c-CAvatar>
          <c-CBadge intent="success" shape="pill">Ready</c-CBadge>
        </div>
        <div class="avatar-party__group" aria-label="Moonfen expedition party">
          <c-CAvatar alt="Orrin Moss">OM</c-CAvatar>
          <c-CAvatar alt="Sable Reed" variant="solid">SR</c-CAvatar>
          <c-CAvatar alt="Tarin Wisp" variant="outline">TW</c-CAvatar>
        </div>
      </div>
    """
    css = """
      :where(.avatar-party) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1.5rem;
      }

      :where(.avatar-party__member) {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      :where(.avatar-party__group) {
        display: flex;
        padding-inline-start: 0.5rem;
      }

      :where(.avatar-party__group [data-citry-ui-part="avatar"]) {
        margin-inline-start: -0.5rem;
        border-color: Canvas;
        border-width: 2px;
      }
    """


preview = AvatarComposition()

preview  # noqa: B018
