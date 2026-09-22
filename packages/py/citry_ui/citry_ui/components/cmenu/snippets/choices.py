import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuChoices(Component):
    template = """
      <section
        class="archive-choice-demo"
      >
        <c-CMenu c-close_on_select="False">
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Reading preferences</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuCheckboxItem
              value="glow"
              checked="mixed"
              v-bind="{
                checked: glow,
                onCheckedChange: (value) => glow = value,
              }"
            >
              Glow around enchanted passages
            </c-CMenuCheckboxItem>
            <c-CMenuSeparator />
            <c-CMenuRadioGroup
              value="elvish"
              v-bind="{
                value: script,
                onValueChange: (value) => script = value,
              }"
            >
              <c-fill name="label">Translation script</c-fill>
              <c-fill name="default">
                <c-CMenuRadioItem value="elvish">Elvish</c-CMenuRadioItem>
                <c-CMenuRadioItem value="draconic">Draconic</c-CMenuRadioItem>
                <c-CMenuRadioItem value="celestial">Celestial</c-CMenuRadioItem>
              </c-fill>
            </c-CMenuRadioGroup>
          </c-fill>
        </c-CMenu>
        <output
          v-text="`Glow: ${glow}; script: ${script}`"
        ></output>
      </section>
    """

    js = "$component({data(){return {glow:'mixed',script:'elvish'};}});"

    css = """
      :where(.archive-choice-demo) {
        display: grid;
        gap: 1rem;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = MenuChoices()

preview  # noqa: B018
