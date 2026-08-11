import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledTextarea(Component):
    template = """
      <section
        class="forest-controlled"
        x-data
        x-init="Alpine.store('forestTextareaDraft', {
          controlled: true,
          draft: 'A tawny owl called from the eastern ridge.',
        })"
      >
        <c-CField>
          <c-fill name="label">Patrol draft</c-fill>
          <c-fill name="default">
            <c-CTextarea
              name="patrol_draft"
              $c-props="{
                value: $store.forestTextareaDraft.controlled
                  ? $store.forestTextareaDraft.draft
                  : undefined,
              }"
              @input="$store.forestTextareaDraft.draft = $event.target.value"
            />
          </c-fill>
          <c-fill name="description">
            <span
              x-text="$store.forestTextareaDraft.controlled
                ? 'Application controlled'
                : 'Browser controlled'"
            ></span>
          </c-fill>
        </c-CField>
        <div class="forest-controlled__actions">
          <c-CButton
            type="button"
            size="sm"
            @click="$store.forestTextareaDraft.controlled = false"
          >
            Release
          </c-CButton>
          <c-CButton
            type="button"
            size="sm"
            variant="outline"
            @click="
              $store.forestTextareaDraft.draft = 'Fresh tracks followed the creek north.';
              $store.forestTextareaDraft.controlled = true;
            "
          >
            Replace draft
          </c-CButton>
        </div>
      </section>
    """

    css = """
      :where(.forest-controlled) {
        display: grid;
        gap: 1rem;
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-controlled__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = ControlledTextarea()

preview  # noqa: B018
