import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedAlertDialog(Component):
    template = """
      <c-CAlertDialog
        id="custom-archive"
        class_="archive-alert"
        c-style="{
          '--cui-alert-dialog-radius': '1.25rem',
          '--cui-alert-dialog-inline-size': '30rem',
          '--cui-alert-dialog-border-color': '#8b5cf6'
        }"
      >
        <c-fill name="activator" data="{activator_attrs}">
          <c-CButton c-attrs="activator_attrs" variant="outline">Archive workspace</c-CButton>
        </c-fill>
        <c-fill name="title">Archive this workspace?</c-fill>
        <c-fill name="description">Collaborators will lose active access.</c-fill>
        <c-fill name="cancel" data="{cancel_attrs}">
          <c-CButton c-attrs="cancel_attrs" variant="outline">Keep active</c-CButton>
        </c-fill>
        <c-fill name="action" data="{action_attrs}">
          <c-CButton c-attrs="action_attrs">Archive</c-CButton>
        </c-fill>
      </c-CAlertDialog>
    """


preview = CustomizedAlertDialog()
preview  # noqa: B018
