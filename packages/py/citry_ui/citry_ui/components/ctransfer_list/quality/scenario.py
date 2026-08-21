"""Shared Transfer List scenario used by repository quality tools."""

from citry import Citry, Component


def transfer_list_states_component(app: Citry) -> type[Component]:
    class CitryUiTransferListStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-transfer-list-ready>
            <h1>Transfer List states</h1>
            <c-CTransferList
              id="quality-transfer-list"
              name="quality-items"
              c-required="True"
              c-value="['long','locked']"
              c-attrs="quality_attrs"
            >
              <c-CTransferListItem value="short" label="Short item" />
              <c-CTransferListItem value="rtl" label="Arabic localized content">
                <span dir="rtl">عنصر عربي طويل لاختبار الاتجاه</span>
              </c-CTransferListItem>
              <c-CTransferListItem value="long" label="A very long rich item that wraps safely">
                <strong>Long rich item</strong><br />A supporting description that wraps without widening the pane.
              </c-CTransferListItem>
              <c-CTransferListItem value="locked" label="Locked chosen item" c-disabled="True" />
            </c-CTransferList>
          </section>
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "quality_attrs": {
                    "data-quality-states": "native enhanced controlled form required disabled rtl narrow localized"
                }
            }

    return CitryUiTransferListStates


__all__ = ["transfer_list_states_component"]
