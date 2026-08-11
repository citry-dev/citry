import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeAlertButtons(Component):
    template = """
      <c-CAlertDialog id="leave-editor">
        <c-fill name="activator" data="{activator_attrs, activator_type}">
          <button c-type="activator_type" c-bind="activator_attrs">Leave editor</button>
        </c-fill>
        <c-fill name="title">Leave the editor?</c-fill>
        <c-fill name="description">Changes since the last save will be lost.</c-fill>
        <c-fill name="cancel" data="{cancel_attrs, cancel_type}">
          <button c-type="cancel_type" c-bind="cancel_attrs">Stay</button>
        </c-fill>
        <c-fill name="action" data="{action_attrs, action_type}">
          <button c-type="action_type" c-bind="action_attrs">Leave</button>
        </c-fill>
      </c-CAlertDialog>
    """


preview = NativeAlertButtons()
preview  # noqa: B018
