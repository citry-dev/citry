import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledArchive(Component):
    template = """
      <section >
        <c-CAlertDialog
          id="archive-record"
          :open="open" :onOpenChange="(next, detail) => {
              if (detail.returnValue === 'action') {
                pending = true;
                result = 'Archiving...';
                window.setTimeout(() => {
                  pending = false;
                  open = false;
                  result = 'Record archived';
                }, 500);
              } else {
                open = next;
                if (!next) result = 'Archive cancelled';
              }
            }"
        >
          <c-fill name="activator" data="{activator_attrs}">
            <c-CButton c-attrs="activator_attrs">Archive record</c-CButton>
          </c-fill>
          <c-fill name="title">Archive this record?</c-fill>
          <c-fill name="description">It will leave the active workspace.</c-fill>
          <c-fill name="cancel" data="{cancel_attrs}">
            <c-CButton c-attrs="cancel_attrs" variant="outline" :disabled="pending">Cancel</c-CButton>
          </c-fill>
          <c-fill name="action" data="{action_attrs}">
            <c-CButton c-attrs="action_attrs" :loading="pending">Archive</c-CButton>
          </c-fill>
        </c-CAlertDialog>
        <p aria-live="polite" v-text="result"></p>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            open: false, pending: false, result: 'No decision yet'
          };
        },
      });
    """


preview = ControlledArchive()
preview  # noqa: B018
