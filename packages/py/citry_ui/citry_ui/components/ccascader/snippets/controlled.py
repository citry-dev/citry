import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderControlled(Component):
    template = """
      <div >
        <c-CCascader :value="place" :onValueChange="(value)=>{place=value;last=value.join(' / ')}">
          <c-CCascaderOption value="earth" label="Earth">
            <c-CCascaderOption value="north" label="Northern hemisphere" />
            <c-CCascaderOption value="south" label="Southern hemisphere" />
          </c-CCascaderOption>
        </c-CCascader>
        <output v-text="last"></output>
      </div>
    """
    js = """
      $component({
        data() {
          return {
            place:['earth','north'], last:''
          };
        },
      });
    """


preview = CascaderControlled()
preview  # noqa: B018
