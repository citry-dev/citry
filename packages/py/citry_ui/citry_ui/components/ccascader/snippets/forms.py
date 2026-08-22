# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderForms(Component):
    template = """
      <form>
        <c-CCascader name="category" c-value="['hardware','cameras','mirrorless']">
          <c-CCascaderOption value="hardware" label="Hardware"><c-CCascaderOption value="cameras" label="Cameras"><c-CCascaderOption value="mirrorless" label="Mirrorless" /></c-CCascaderOption></c-CCascaderOption>
        </c-CCascader>
        <button type="submit">Save category</button>
      </form>
    """


preview = CascaderForms()
preview  # noqa: B018
