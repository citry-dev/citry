import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourAtAGlance(Component):
    template = """
      <div>
        <button id="tour-save" type="button">Save project</button>
        <c-CTour>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Show tour</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CTourStep value="welcome">
              <c-fill name="title">Welcome to the workspace</c-fill>
              <c-fill name="default">This short tour explains the primary workflow.</c-fill>
            </c-CTourStep>
            <c-CTourStep value="save" target_id="tour-save" placement="bottom-end">
              <c-fill name="title">Save your work</c-fill>
              <c-fill name="default">Use this action when the project is ready.</c-fill>
            </c-CTourStep>
          </c-fill>
        </c-CTour>
      </div>
    """


preview = TourAtAGlance()
preview  # noqa: B018
