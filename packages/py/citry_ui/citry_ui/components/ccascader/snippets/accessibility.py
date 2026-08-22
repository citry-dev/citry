# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderAccessibility(Component):
    template = """
      <label id="team-label">Owning team</label>
      <c-CCascader aria_labelledby="team-label" c-value="['product','experience','research']" size="lg" variant="soft" c-style="{'--cui-cascader-column-width': '14rem'}">
        <c-CCascaderOption value="product" label="Product">
          <c-CCascaderOption value="experience" label="Customer experience">
            <c-CCascaderOption value="research" label="Customer research" />
          </c-CCascaderOption>
        </c-CCascaderOption>
        <c-CCascaderOption value="operations" label="Operations">
          <c-CCascaderOption value="support" label="Customer support">
            <c-CCascaderOption value="priority" label="Priority support" />
          </c-CCascaderOption>
        </c-CCascaderOption>
      </c-CCascader>
    """


preview = CascaderAccessibility()
preview  # noqa: B018
