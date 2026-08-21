import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListControlled(Component):
    template = """
      <section x-data="{chosen:['grace'],last:'No request'}">
        <c-CTransferList
          $c-props="{
            value:chosen,
            onValueChange:(next,detail)=>{chosen=next;last=`${detail.source}: ${next.join(', ') || 'none'}`},
          }"
        >
          <c-CTransferListItem value="ada" label="Ada" />
          <c-CTransferListItem value="grace" label="Grace" />
          <c-CTransferListItem value="katherine" label="Katherine" />
        </c-CTransferList>
        <output x-text="last">No request</output>
      </section>
    """


preview = TransferListControlled()
preview  # noqa: B018
