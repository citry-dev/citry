import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BlockingError(Component):
    template = """
      <c-CAlertDialog id="sync-error" size="md">
        <c-fill name="activator" data="{activator_attrs}">
          <c-CButton c-attrs="activator_attrs" variant="outline">Show sync error</c-CButton>
        </c-fill>
        <c-fill name="title">Changes could not be synchronized</c-fill>
        <c-fill name="description">
          Reconnect before continuing so this draft is not overwritten.
        </c-fill>
        <c-fill name="default">
          Your local draft remains available in this browser.
        </c-fill>
        <c-fill name="cancel" data="{cancel_attrs}">
          <c-CButton c-attrs="cancel_attrs" variant="outline">Review draft</c-CButton>
        </c-fill>
        <c-fill name="action" data="{action_attrs}">
          <c-CButton c-attrs="action_attrs">Retry connection</c-CButton>
        </c-fill>
      </c-CAlertDialog>
    """


preview = BlockingError()
preview  # noqa: B018
