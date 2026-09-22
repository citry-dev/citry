import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledCheckbox(Component):
    template = """
      <section
        class="checkbox-control-demo"
      >
        <c-CCheckbox
          :checked="controlled
              ? checked
              : undefined"
          @input="checked = $event.target.checked"
        >
          <c-fill name="default">Press this leaf in the field journal</c-fill>
          <c-fill name="description">
            <span
              v-text="controlled
                ? 'Application controlled'
                : 'Browser controlled'"
            ></span>
          </c-fill>
        </c-CCheckbox>
        <div class="checkbox-control-demo__actions">
          <c-CButton
            size="sm"
            @click="controlled = false"
          >
            Release
          </c-CButton>
          <c-CButton
            size="sm"
            variant="outline"
            @click="checked = true; controlled = true"
          >
            Check and reacquire
          </c-CButton>
          <c-CButton
            size="sm"
            variant="ghost"
            intent="neutral"
            @click="checked = false; controlled = true"
          >
            Clear and reacquire
          </c-CButton>
        </div>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            controlled: true, checked: false
          };
        },
      });
    """

    css = """
      :where(.checkbox-control-demo) {
        display: grid;
        gap: 1rem;
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-control-demo__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = ControlledCheckbox()

preview  # noqa: B018
