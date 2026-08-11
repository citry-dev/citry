import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuChoices(Component):
    template = """
      <section
        class="archive-choice-demo"
        x-data
        x-init="Alpine.store('archiveMenuChoices', {glow: 'mixed', script: 'elvish'})"
      >
        <c-CMenu c-close_on_select="False">
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Reading preferences</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuCheckboxItem
              value="glow"
              checked="mixed"
              $c-props="{
                checked: $store.archiveMenuChoices.glow,
                onCheckedChange: (value) => $store.archiveMenuChoices.glow = value,
              }"
            >
              Glow around enchanted passages
            </c-CMenuCheckboxItem>
            <c-CMenuSeparator />
            <c-CMenuRadioGroup
              value="elvish"
              $c-props="{
                value: $store.archiveMenuChoices.script,
                onValueChange: (value) => $store.archiveMenuChoices.script = value,
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
          x-text="`Glow: ${$store.archiveMenuChoices.glow}; script: ${$store.archiveMenuChoices.script}`"
        ></output>
      </section>
    """

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
