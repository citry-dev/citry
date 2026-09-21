import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledTextarea(Component):
    template = """
      <section
        class="forest-controlled"
      >
        <c-CField>
          <c-fill name="label">Patrol draft</c-fill>
          <c-fill name="default">
            <c-CTextarea
              name="patrol_draft"
              :value="controlled
                  ? draft
                  : undefined"
              @input="draft = $event.target.value"
            />
          </c-fill>
          <c-fill name="description">
            <span
              v-text="controlled
                ? 'Application controlled'
                : 'Browser controlled'"
            ></span>
          </c-fill>
        </c-CField>
        <div class="forest-controlled__actions">
          <c-CButton
            type="button"
            size="sm"
            @click="controlled = false"
          >
            Release
          </c-CButton>
          <c-CButton
            type="button"
            size="sm"
            variant="outline"
            @click="
              draft = 'Fresh tracks followed the creek north.';
              controlled = true;
            "
          >
            Replace draft
          </c-CButton>
        </div>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            controlled: true,
            draft: 'A tawny owl called from the eastern ridge.',
          };
        },
      });
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
