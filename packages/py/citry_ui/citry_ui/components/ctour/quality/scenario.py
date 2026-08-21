"""Shared Tour scenario used by repository quality tools."""

from citry import Citry, Component


def tour_states_component(app: Citry) -> type[Component]:
    class CitryUiTourStates(Component):
        citry = app
        template = """
          <section
            class="citry-ui-quality-stack tour-quality"
            data-quality-tour-ready
            x-data="{open:true,active:0,last:'No request'}"
          >
            <h1>Tour states</h1>
            <div class="tour-quality__workspace">
              <button id="quality-tour-target" type="button">Target action</button>
              <p>Page content remains visible behind the modal spotlight.</p>
            </div>
            <c-CTour
              id="quality-tour"
              c-open="True"
              c-attrs="quality_attrs"
              $c-props="{
                open,
                active,
                onOpenChange:(next,detail)=>{last=detail.reason;open=next},
                onActiveChange:(next,detail)=>{last=detail.reason;active=next},
              }"
            >
              <c-CTourStep value="intro" c-describe="True">
                <c-fill name="title">Welcome to Tour quality</c-fill>
                <c-fill name="default">
                  This centered step exercises modal naming, progress, actions, and focus.
                </c-fill>
              </c-CTourStep>
              <c-CTourStep value="target" target_id="quality-tour-target" placement="bottom-end">
                <c-fill name="title">A target-aware step</c-fill>
                <c-fill name="default">
                  The target remains inert while geometry follows viewport changes and very long content wraps safely.
                </c-fill>
              </c-CTourStep>
              <c-CTourStep value="missing" target_id="quality-tour-missing">
                <c-fill name="title">Missing target</c-fill>
                <c-fill name="default">Skip policy advances past this unavailable target.</c-fill>
              </c-CTourStep>
              <c-CTourStep value="finish">
                <c-fill name="title">Finish</c-fill>
                <c-fill name="default"><span dir="rtl">اكتملت الجولة</span></c-fill>
              </c-CTourStep>
            </c-CTour>
            <output x-text="last">No request</output>
          </section>
        """
        css = """
          :where(.tour-quality__workspace){min-block-size:24rem;padding:2rem;background:light-dark(#f8fafc,#172033)}
          :where(.tour-quality__workspace button){margin-inline-start:60%;min-block-size:2.75rem}
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "quality_attrs": {
                    "data-quality-states": (
                        "centered targeted modal controlled missing-target rtl long-content localized"
                    )
                }
            }

    return CitryUiTourStates


__all__ = ["tour_states_component"]
