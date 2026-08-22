import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertDialogSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CRow gap="md" wrap>
        <c-for each="size in sizes">
          <c-CAlertDialog c-size="size">
            <c-fill name="activator" data="{activator_attrs}">
              <c-CButton c-attrs="activator_attrs" variant="outline">Open {{ size }}</c-CButton>
            </c-fill>
            <c-fill name="title">{{ size }} decision surface</c-fill>
            <c-fill name="description">Compare the responsive width for this size.</c-fill>
            <c-fill name="cancel" data="{cancel_attrs}">
              <c-CButton c-attrs="cancel_attrs" variant="outline">Cancel</c-CButton>
            </c-fill>
            <c-fill name="action" data="{action_attrs}">
              <c-CButton c-attrs="action_attrs">Continue</c-CButton>
            </c-fill>
          </c-CAlertDialog>
        </c-for>
      </c-CRow>
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {"sizes": ("sm", "md", "lg")}


preview = AlertDialogSizes()
preview  # noqa: B018
