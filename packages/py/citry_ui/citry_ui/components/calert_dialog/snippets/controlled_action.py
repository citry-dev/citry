import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledArchive(Component):
    template = """
      <section >
        <c-CAlertDialog
          id="archive-record"
          :open="open"
          :onOpenChange="applyArchiveDecision"
        >
          <c-fill name="activator" data="{activator_attrs}">
            <c-CButton c-attrs="activator_attrs">Archive record</c-CButton>
          </c-fill>
          <c-fill name="title">Archive this record?</c-fill>
          <c-fill name="description">It will leave the active workspace.</c-fill>
          <c-fill name="cancel" data="{cancel_attrs}">
            <c-CButton
              c-attrs="cancel_attrs"
              variant="outline"
              :disabled="pending"
            >Cancel</c-CButton>
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
        methods: {
          applyArchiveDecision(next, detail) {
            // When Archive is chosen, keep the dialog open while the work
            // runs and close it once the record is archived.
            if (detail.returnValue === 'action') {
              this.pending = true;
              this.result = 'Archiving...';
              window.setTimeout(() => {
                this.pending = false;
                this.open = false;
                this.result = 'Record archived';
              }, 500);
            } else {
              // Apply every other request as it comes, and note a cancel
              // when the dialog closes.
              this.open = next;
              if (!next) this.result = 'Archive cancelled';
            }
          },
        },
      });
    """


preview = ControlledArchive()
preview  # noqa: B018
