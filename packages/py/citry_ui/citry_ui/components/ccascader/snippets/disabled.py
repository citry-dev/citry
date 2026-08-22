# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderDisabled(Component):
    template = """
      <c-CCascader>
        <c-CCascaderOption value="available" label="Available"><c-CCascaderOption value="one" label="Warehouse one" /></c-CCascaderOption>
        <c-CCascaderOption value="maintenance" label="Under maintenance" c-disabled="True"><c-CCascaderOption value="two" label="Warehouse two" /></c-CCascaderOption>
      </c-CCascader>
    """


preview = CascaderDisabled()
preview  # noqa: B018
