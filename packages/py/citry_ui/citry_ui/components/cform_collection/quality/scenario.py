"""Shared Form Collection scenario used by repository quality tools."""

# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from citry import Citry, Component


def form_collection_states_component(app: Citry) -> type[Component]:
    class CitryUiFormCollectionStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-form-collection-ready>
            <h1>Form Collection states</h1>
            <form>
              <c-CFormCollection label="Localized contacts" action_name="contact_action" c-min_items="1" c-attrs="quality_attrs">
                <c-CFormCollectionItem value="long" label="A very long contact label that wraps safely">
                  <label>Email <input name="contacts[long][email]" type="email" required /></label>
                </c-CFormCollectionItem>
                <c-CFormCollectionItem value="rtl" label="Arabic contact"><div dir="rtl"><label>البريد <input name="contacts[rtl][email]" /></label></div></c-CFormCollectionItem>
                <c-CFormCollectionItem value="fixed" label="Fixed contact" c-disabled="True"><label>Email <input name="contacts[fixed][email]" /></label></c-CFormCollectionItem>
              </c-CFormCollection>
            </form>
          </section>
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "quality_attrs": {
                    "data-quality-states": "form server-actions client-actions min-max disabled rtl long-content localized cleanup"
                }
            }

    return CitryUiFormCollectionStates


__all__ = ["form_collection_states_component"]
