"""Shared Avatar scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def avatar_states_component(app: Citry) -> type[Component]:
    """Create the reusable Avatar state and environment scenario."""

    class CitryUiAvatarStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack"
            aria-labelledby="avatar-states-title"
            data-quality-avatar-ready
          >
            <h1 id="avatar-states-title">Avatar states</h1>
            <c-for each="variant in variants">
              <div class="avatar-quality-row">
                <c-for each="size in sizes">
                  <c-CAvatar c-variant="variant" c-size="size" c-alt="f'{variant} {size} guide'">MF</c-CAvatar>
                </c-for>
              </div>
            </c-for>
            <div class="avatar-quality-row">
              <c-for each="shape in shapes">
                <c-CAvatar c-shape="shape" c-alt="f'{shape} guide'">SG</c-CAvatar>
              </c-for>
            </div>
            <c-CAvatar alt="Generic fallback" />
            <c-CAvatar c-attrs="{'data-quality-avatar-decorative': True}">DF</c-CAvatar>
            <div dir="rtl"><c-CAvatar alt="RTL guide">RG</c-CAvatar></div>
            <div style="color-scheme:dark"><c-CAvatar alt="Dark guide">DG</c-CAvatar></div>
            <div class="avatar-quality-brand avatar-quality-brand--fen">
              <c-CAvatar alt="Fen brand" variant="solid">FB</c-CAvatar>
            </div>
            <div class="avatar-quality-brand avatar-quality-brand--moon">
              <c-CAvatar alt="Moon brand" variant="outline">MB</c-CAvatar>
            </div>
          </section>
        """

        def template_data(
            self,
            kwargs: Kwargs,  # noqa: ARG002
            slots: Slots,  # noqa: ARG002
        ) -> dict[str, object]:
            return {
                "variants": ("soft", "solid", "outline"),
                "sizes": ("sm", "md", "lg"),
                "shapes": ("circle", "rounded", "square"),
            }

        css = """
          :where(.avatar-quality-row) {
            display: flex;
            align-items: center;
            gap: 0.75rem;
          }

          :where(.avatar-quality-brand) {
            padding: 1rem;
          }

          :where(.avatar-quality-brand--fen) {
            --cui-avatar-background: light-dark(#d9f1e4, #234738);
            --cui-avatar-foreground: light-dark(#174b35, #c9f4dd);
            background: light-dark(#f3faf6, #13271e);
          }

          :where(.avatar-quality-brand--moon) {
            --cui-avatar-border-color: light-dark(#6852a3, #c8b8ff);
            --cui-avatar-foreground: light-dark(#4b347f, #ddd3ff);
            background: light-dark(#f5f1ff, #211a32);
          }
        """

    return CitryUiAvatarStates
