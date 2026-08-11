import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertDialogGlance(Component):
    template = """
      <c-CAlertDialog id="glance-delete">
        <c-fill name="activator" data="{activator_attrs}">
          <c-CButton c-attrs="activator_attrs" intent="danger">Delete project</c-CButton>
        </c-fill>
        <c-fill name="title">Delete this project?</c-fill>
        <c-fill name="description">This permanently removes all project data.</c-fill>
        <c-fill name="cancel" data="{cancel_attrs}">
          <c-CButton c-attrs="cancel_attrs" variant="outline">Keep project</c-CButton>
        </c-fill>
        <c-fill name="action" data="{action_attrs}">
          <c-CButton c-attrs="action_attrs" intent="danger">Delete</c-CButton>
        </c-fill>
      </c-CAlertDialog>
    """


preview = AlertDialogGlance()
preview  # noqa: B018
