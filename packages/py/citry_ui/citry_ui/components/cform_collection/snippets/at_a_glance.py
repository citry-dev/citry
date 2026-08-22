import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormCollectionAtAGlance(Component):
    template = """
      <form>
        <c-CFormCollection
          label="Email addresses"
          c-allow_add="False"
          c-allow_remove="False"
          c-allow_reorder="False"
        >
          <c-CFormCollectionItem value="primary" label="Primary email">
            <label>Email <input name="emails[primary]" type="email" value="ada@example.com" /></label>
          </c-CFormCollectionItem>
          <c-CFormCollectionItem value="backup" label="Backup email">
            <label>Email <input name="emails[backup]" type="email" /></label>
          </c-CFormCollectionItem>
        </c-CFormCollection>
      </form>
    """


preview = FormCollectionAtAGlance()
preview  # noqa: B018
