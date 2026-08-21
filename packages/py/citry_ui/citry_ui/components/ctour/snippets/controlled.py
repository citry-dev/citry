import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourControlled(Component):
    template = """
      <section x-data="{open:false,active:0,last:'No request'}">
        <c-CButton @click="open=true">Open controlled tour</c-CButton>
        <output x-text="last">No request</output>
        <c-CTour
          $c-props="{
            open,
            active,
            onOpenChange:(next,detail)=>{last=`Open: ${detail.reason}`;open=next},
            onActiveChange:(next,detail)=>{last=`Step: ${detail.reason}`;active=next},
          }"
        >
          <c-CTourStep value="first">
            <c-fill name="title">First controlled step</c-fill>
            <c-fill name="default">The parent accepts each requested index.</c-fill>
          </c-CTourStep>
          <c-CTourStep value="second">
            <c-fill name="title">Second controlled step</c-fill>
            <c-fill name="default">Open and active ownership are independent.</c-fill>
          </c-CTourStep>
        </c-CTour>
      </section>
    """


preview = TourControlled()
preview  # noqa: B018
