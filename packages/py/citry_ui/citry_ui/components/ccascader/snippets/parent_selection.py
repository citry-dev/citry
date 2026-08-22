# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderParentSelection(Component):
    template = """
      <c-CCascader c-change_on_select="True">
        <c-CCascaderOption value="design" label="Design"><c-CCascaderOption value="research" label="Research" /><c-CCascaderOption value="systems" label="Design systems" /></c-CCascaderOption>
        <c-CCascaderOption value="engineering" label="Engineering"><c-CCascaderOption value="platform" label="Platform" /></c-CCascaderOption>
      </c-CCascader>
    """


preview = CascaderParentSelection()
preview  # noqa: B018
