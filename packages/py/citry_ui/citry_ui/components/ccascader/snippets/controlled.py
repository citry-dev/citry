import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderControlled(Component):
    template = """
      <div x-data="{place:['earth','north'], last:''}">
        <c-CCascader $c-props="{value:place,onValueChange:(value)=>{place=value;last=value.join(' / ')}}">
          <c-CCascaderOption value="earth" label="Earth">
            <c-CCascaderOption value="north" label="Northern hemisphere" />
            <c-CCascaderOption value="south" label="Southern hemisphere" />
          </c-CCascaderOption>
        </c-CCascader>
        <output x-text="last"></output>
      </div>
    """


preview = CascaderControlled()
preview  # noqa: B018
