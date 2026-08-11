import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledArchive(Component):
    template = """
      <section x-data="{open: false, pending: false, result: 'No decision yet'}">
        <c-CAlertDialog
          id="archive-record"
          $c-props="{
            open,
            onOpenChange: (next, detail) => {
              if (detail.returnValue === 'action') {
                pending = true;
                result = 'Archiving...';
                setTimeout(() => {
                  pending = false;
                  open = false;
                  result = 'Record archived';
                }, 500);
              } else {
                open = next;
                if (!next) result = 'Archive cancelled';
              }
            }
          }"
        >
          <c-fill name="activator" data="{activator_attrs}">
            <c-CButton c-attrs="activator_attrs">Archive record</c-CButton>
          </c-fill>
          <c-fill name="title">Archive this record?</c-fill>
          <c-fill name="description">It will leave the active workspace.</c-fill>
          <c-fill name="cancel" data="{cancel_attrs}">
            <c-CButton c-attrs="cancel_attrs" variant="outline" $c-props="{disabled: pending}">Cancel</c-CButton>
          </c-fill>
          <c-fill name="action" data="{action_attrs}">
            <c-CButton c-attrs="action_attrs" $c-props="{loading: pending}">Archive</c-CButton>
          </c-fill>
        </c-CAlertDialog>
        <p aria-live="polite" x-text="result"></p>
      </section>
    """


preview = ControlledArchive()
preview  # noqa: B018
