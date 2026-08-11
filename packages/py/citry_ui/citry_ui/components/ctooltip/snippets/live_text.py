import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LiveTooltipText(Component):
    template = """
      <section class="live-tooltip" x-data="{ unit: 'kilometres' }">
        <c-CTooltip
          text="Europa is 3,122 kilometres wide"
          $c-props="{
            text: unit === 'kilometres'
              ? 'Europa is 3,122 kilometres wide'
              : 'Europa is 1,940 miles wide',
          }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Europa diameter</c-CButton>
          </c-fill>
        </c-CTooltip>
        <label>
          Units
          <select x-model="unit">
            <option value="kilometres">Kilometres</option>
            <option value="miles">Miles</option>
          </select>
        </label>
      </section>
    """

    css = """
      :where(.live-tooltip) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 11rem;
        padding-block: 2rem;
      }

      :where(.live-tooltip label) {
        display: grid;
        gap: 0.25rem;
        font-size: 0.875rem;
      }
    """


preview = LiveTooltipText()

preview  # noqa: B018
