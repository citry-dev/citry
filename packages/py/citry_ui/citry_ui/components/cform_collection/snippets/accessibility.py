import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormCollectionAccessibility(Component):
    template = """
      <form>
        <c-CFormCollection
          label="Shipping addresses"
          description="The first address is used by default."
          c-allow_add="False"
          c-allow_remove="False"
          c-allow_reorder="False"
        >
          <c-CFormCollectionItem value="home" label="Home address">
            <label>Street <input name="addresses[home][street]" autocomplete="street-address" /></label>
            <label>City <input name="addresses[home][city]" autocomplete="address-level2" /></label>
          </c-CFormCollectionItem>
          <c-CFormCollectionItem value="office" label="Office address">
            <label>Street <input name="addresses[office][street]" /></label>
            <label>City <input name="addresses[office][city]" /></label>
          </c-CFormCollectionItem>
        </c-CFormCollection>
      </form>
    """


preview = FormCollectionAccessibility()
preview  # noqa: B018
