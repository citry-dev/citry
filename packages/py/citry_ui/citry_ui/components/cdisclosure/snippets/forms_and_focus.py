import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisclosureFormsAndFocus(Component):
    template = """
      <form
        class="disclosure-form"
        x-data="{notificationOpen:true, escalationOpen:false, invalidTarget:null}"
        @invalid.capture="
          if ($event.target.name === 'notification-email') {
            $event.preventDefault();
            notificationOpen = true;
          } else if ($event.target.name === 'escalation-contact') {
            $event.preventDefault();
            escalationOpen = true;
          } else {
            return;
          }
          if (invalidTarget === null) {
            invalidTarget = $event.target;
            $nextTick(() => {
              invalidTarget?.focus();
              invalidTarget = null;
            });
          }
        "
      >
        <c-CDisclosure
          open
          $c-props="{
            open: notificationOpen,
            onOpenChange: (next) => notificationOpen = next,
          }"
        >
          <c-fill name="title">Notification settings</c-fill>
          <c-fill name="default">
            <c-CStack gap="sm">
              <c-CField>
                <c-fill name="label">Notification email</c-fill>
                <c-fill name="default">
                  <c-CInput name="notification-email" type="email" value="ops@example.com" />
                </c-fill>
                <c-fill name="description">Edits survive closing and reopening.</c-fill>
              </c-CField>
              <c-CCheckbox name="weekly-summary">Send a weekly summary</c-CCheckbox>
            </c-CStack>
          </c-fill>
        </c-CDisclosure>
        <c-CDisclosure
          $c-props="{
            open: escalationOpen,
            onOpenChange: (next) => escalationOpen = next,
          }"
        >
          <c-fill name="title">Required escalation contact</c-fill>
          <c-fill name="default">
            <label>Contact <input name="escalation-contact" required /></label>
          </c-fill>
        </c-CDisclosure>
        <c-CButton type="submit">Save settings</c-CButton>
        <c-CButton type="reset" variant="outline">Reset form</c-CButton>
      </form>
    """

    css = """
      :where(.disclosure-form) { display: grid; gap: 1rem; max-inline-size: 42rem; }
    """


preview = DisclosureFormsAndFocus()
preview  # noqa: B018
