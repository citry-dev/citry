import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListAccessibility(Component):
    template = """
      <c-CTransferList
        name="permissions"
        available_label="Available permissions"
        chosen_label="Granted permissions"
        c-value="['audit','read']"
      >
        <c-CTransferListItem value="read" label="Read records" />
        <c-CTransferListItem value="write" label="Write records" />
        <c-CTransferListItem value="audit" label="Audit access required by policy" c-disabled="True">
          <strong>Audit access</strong><br /><small>Required by policy; cannot be removed</small>
        </c-CTransferListItem>
      </c-CTransferList>
    """


preview = TransferListAccessibility()
preview  # noqa: B018
