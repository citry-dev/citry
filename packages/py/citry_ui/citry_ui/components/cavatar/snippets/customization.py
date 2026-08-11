import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarCustomization(Component):
    template = """
      <div class="avatar-moonlit">
        <c-CAvatar alt="Moonlit ranger" size="lg">MR</c-CAvatar>
        <c-CAvatar alt="Reed oracle" size="lg" variant="outline">RO</c-CAvatar>
      </div>
    """
    css = """
      :where(.avatar-moonlit) {
        --cui-avatar-background: light-dark(#d9f1e4, #234738);
        --cui-avatar-foreground: light-dark(#174b35, #c9f4dd);
        --cui-avatar-border-color: light-dark(#4b8a69, #83c9a3);
        --cui-avatar-radius: 35% 65% 58% 42%;
        display: flex;
        gap: 0.75rem;
      }

      :where(.avatar-moonlit [data-citry-ui-part="fallback"]) {
        letter-spacing: 0.06em;
      }
    """


preview = AvatarCustomization()

preview  # noqa: B018
