import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListAtAGlance(Component):
    template = """
      <c-CTransferList name="reviewers" c-value="['grace']">
        <c-CTransferListItem value="ada" label="Ada Lovelace" />
        <c-CTransferListItem value="grace" label="Grace Hopper" />
        <c-CTransferListItem value="katherine" label="Katherine Johnson" />
        <c-CTransferListItem value="margaret" label="Margaret Hamilton" />
      </c-CTransferList>
    """


preview = TransferListAtAGlance()
preview  # noqa: B018
