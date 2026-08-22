"""Shared Cascader scenario used by repository quality tools."""

# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from citry import Citry, Component


def cascader_states_component(app: Citry) -> type[Component]:
    class CitryUiCascaderStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-cascader-ready x-data="{path:['world','europe','prague'],open:true}">
            <h1>Cascader states</h1>
            <form>
              <c-CCascader id="quality-cascader" name="place" c-open="True" c-value="['world','europe','prague']" c-attrs="quality_attrs">
                <c-CCascaderOption value="world" label="A very long world category label">
                  <c-CCascaderOption value="europe" label="Europe"><c-CCascaderOption value="prague" label="Prague" /><c-CCascaderOption value="berlin" label="Berlin" /></c-CCascaderOption>
                  <c-CCascaderOption value="arabic" label="الشرق الأوسط"><c-CCascaderOption value="amman" label="عمّان" /></c-CCascaderOption>
                </c-CCascaderOption>
                <c-CCascaderOption value="offline" label="Unavailable path" c-disabled="True" />
              </c-CCascader>
            </form>
          </section>
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "quality_attrs": {
                    "data-quality-states": "server controlled keyboard pointer form disabled narrow rtl localized cleanup"
                }
            }

    return CitryUiCascaderStates


__all__ = ["cascader_states_component"]
