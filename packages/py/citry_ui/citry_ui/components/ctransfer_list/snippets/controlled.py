# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListControlled(Component):
    template = """
      <section >
        <c-CTransferList
          :value="chosen" :onValueChange="(next,detail)=>{chosen=next;last=`${detail.source}: ${next.join(', ') || 'none'}`}"
        >
          <c-CTransferListItem value="ada" label="Ada" />
          <c-CTransferListItem value="grace" label="Grace" />
          <c-CTransferListItem value="katherine" label="Katherine" />
        </c-CTransferList>
        <output v-text="last">No request</output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            chosen:['grace'],last:'No request'
          };
        },
      });
    """


preview = TransferListControlled()
preview  # noqa: B018
