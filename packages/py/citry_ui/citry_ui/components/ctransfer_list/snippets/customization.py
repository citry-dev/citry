import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListCustomization(Component):
    template = """
      <c-CTransferList class_="brand-transfer" size="lg" c-value="['stable']">
        <c-CTransferListItem value="alpha" label="Alpha channel" />
        <c-CTransferListItem value="beta" label="Beta channel" />
        <c-CTransferListItem value="stable" label="Stable channel" />
      </c-CTransferList>
    """
    css = """
      .brand-transfer {
        --cui-transfer-list-selected: color-mix(in srgb, MediumPurple 25%, Canvas);
        --cui-transfer-list-focus: MediumPurple;
        --cui-transfer-list-radius: 1rem;
      }
    """


preview = TransferListCustomization()
preview  # noqa: B018
