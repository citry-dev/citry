import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormCollectionFieldGroups(Component):
    template = """
      <form>
        <c-CFormCollection
          label="Escalation contacts"
          description="Contacts are notified in shown order."
          c-allow_add="False"
          c-allow_remove="False"
          c-allow_reorder="False"
        >
          <c-CFormCollectionItem value="primary" label="Primary contact">
            <label>Name <input name="contacts[primary][name]" value="Ada Lovelace" /></label>
            <label>Email <input name="contacts[primary][email]" type="email" value="ada@example.com" /></label>
          </c-CFormCollectionItem>
          <c-CFormCollectionItem value="secondary" label="Secondary contact">
            <label>Name <input name="contacts[secondary][name]" value="Grace Hopper" /></label>
            <label>Email <input name="contacts[secondary][email]" type="email" value="grace@example.com" /></label>
          </c-CFormCollectionItem>
        </c-CFormCollection>
      </form>
    """


preview = FormCollectionFieldGroups()
preview  # noqa: B018
