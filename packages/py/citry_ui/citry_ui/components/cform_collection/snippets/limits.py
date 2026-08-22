import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormCollectionLimits(Component):
    template = """
      <c-CFormCollection label="Approvers" c-min_items="1" c-max_items="2">
        <c-CFormCollectionItem value="owner" label="Account owner" c-removable="False" c-movable="False">
          <label>Email <input name="approvers[owner]" value="owner@example.com" /></label>
        </c-CFormCollectionItem>
        <c-CFormCollectionItem value="security" label="Security reviewer" c-disabled="True">
          <label>Email <input name="approvers[security]" value="security@example.com" /></label>
        </c-CFormCollectionItem>
      </c-CFormCollection>
    """


preview = FormCollectionLimits()
preview  # noqa: B018
