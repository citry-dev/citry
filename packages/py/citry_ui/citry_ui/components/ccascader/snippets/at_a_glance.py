import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderAtAGlance(Component):
    template = """
      <c-CCascader c-value="['europe','czechia','prague']">
        <c-CCascaderOption value="europe" label="Europe">
          <c-CCascaderOption value="czechia" label="Czechia">
            <c-CCascaderOption value="prague" label="Prague" />
          </c-CCascaderOption>
          <c-CCascaderOption value="germany" label="Germany">
            <c-CCascaderOption value="berlin" label="Berlin" />
          </c-CCascaderOption>
        </c-CCascaderOption>
      </c-CCascader>
    """


preview = CascaderAtAGlance()
preview  # noqa: B018
