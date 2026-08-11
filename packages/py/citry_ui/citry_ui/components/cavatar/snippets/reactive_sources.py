import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarReactive(Component):
    template = """
      <div
        class="avatar-reactive"
        x-data="{source: null, status: 'fallback'}"
      >
        <c-CAvatar
          alt="Moonfen lookout"
          $c-props="{src: source, onStatusChange: detail => status = detail.status}"
        >ML</c-CAvatar>
        <p>Status: <strong x-text="status">fallback</strong></p>
        <div class="avatar-reactive__actions">
          <c-CButton size="sm" @click="source = '/missing-lookout-a.png'">Try missing image</c-CButton>
          <c-CButton size="sm" variant="outline" @click="source = null">Use fallback</c-CButton>
        </div>
      </div>
    """
    css = """
      :where(.avatar-reactive) {
        display: grid;
        justify-items: start;
        gap: 0.75rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-reactive p) {
        margin: 0;
        font-size: 0.8rem;
      }

      :where(.avatar-reactive__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
    """


preview = AvatarReactive()

preview  # noqa: B018
