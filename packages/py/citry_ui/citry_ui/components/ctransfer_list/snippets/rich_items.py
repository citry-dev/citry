import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListRichItems(Component):
    template = """
      <c-CTransferList name="owners" c-value="['platform']">
        <c-CTransferListItem value="platform" label="Platform team">
          <strong>Platform</strong><br /><small>Runtime and release infrastructure</small>
        </c-CTransferListItem>
        <c-CTransferListItem value="design" label="Design systems team">
          <strong>Design systems</strong><br /><small>Components, tokens, and accessibility</small>
        </c-CTransferListItem>
        <c-CTransferListItem value="security" label="Security team" c-disabled="True">
          <strong>Security</strong><br /><small>Managed by policy</small>
        </c-CTransferListItem>
      </c-CTransferList>
    """


preview = TransferListRichItems()
preview  # noqa: B018
