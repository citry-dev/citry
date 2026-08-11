import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarAtAGlance(Component):
    template = """
      <section class="avatar-guide" aria-labelledby="avatar-guide-title">
        <p class="avatar-guide__eyebrow">Moonfen field guide</p>
        <h2 id="avatar-guide-title">Night expedition</h2>
        <div class="avatar-guide__row">
          <div><c-CAvatar alt="Mira Vale">MV</c-CAvatar><span>Mira</span></div>
          <div><c-CAvatar alt="Orrin Moss" variant="solid">OM</c-CAvatar><span>Orrin</span></div>
          <div><c-CAvatar alt="Unknown guide" variant="outline" /><span>Guide</span></div>
        </div>
      </section>
    """
    css = """
      :where(.avatar-guide) {
        max-inline-size: 28rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#a8c7b5, #426151);
        border-radius: 0.9rem;
        background: light-dark(#f4fbf6, #15241c);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-guide h2, .avatar-guide p) {
        margin: 0;
      }

      :where(.avatar-guide h2) {
        margin-block: 0.2rem 1rem;
        font-size: 1.1rem;
      }

      :where(.avatar-guide__eyebrow) {
        color: light-dark(#35624b, #a9d7bc);
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.avatar-guide__row) {
        display: flex;
        gap: 1rem;
      }

      :where(.avatar-guide__row > div) {
        display: grid;
        justify-items: center;
        gap: 0.35rem;
        font-size: 0.8rem;
      }
    """


preview = AvatarAtAGlance()

preview  # noqa: B018
