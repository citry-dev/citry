import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisclosureActionsAndDisabled(Component):
    template = """
      <section
        class="disclosure-actions-demo"
        x-data="{disabled:false, fieldsetDisabled:false}"
      >
        <c-CDisclosure
          actions_label="Release note actions"
          c-actions_attrs="{'data-demo-actions':'release'}"
        >
          <c-fill name="title">Release notes</c-fill>
          <c-fill name="actions">
            <c-CButton size="sm" variant="ghost">Copy link</c-CButton>
          </c-fill>
          <c-fill name="default">Review migration notes before deploying version 4.</c-fill>
        </c-CDisclosure>
        <c-CDisclosure open $c-props="{disabled}">
          <c-fill name="title">Managed policy</c-fill>
          <c-fill name="default">Your organization keeps this guidance visible.</c-fill>
        </c-CDisclosure>
        <label><input type="checkbox" x-model="disabled" /> Disable managed policy</label>
        <c-CDisclosure disabled>
          <c-fill name="title">Unavailable audit appendix</c-fill>
          <c-fill name="default">This closed section cannot be activated.</c-fill>
        </c-CDisclosure>
        <fieldset :disabled="fieldsetDisabled">
          <legend>
            <label><input type="checkbox" x-model="fieldsetDisabled" /> Disable native fieldset</label>
          </legend>
          <c-CDisclosure>
            <c-fill name="title">Fieldset-owned policy</c-fill>
            <c-fill name="default">Native fieldset ownership disables this trigger.</c-fill>
          </c-CDisclosure>
        </fieldset>
      </section>
    """

    css = """
      :where(.disclosure-actions-demo) { display: grid; gap: 1rem; }
      :where(.disclosure-actions-demo fieldset) {
        min-inline-size: 0;
        padding: 0.75rem;
        border: 1px solid color-mix(in srgb, currentColor 24%, transparent);
        border-radius: 0.75rem;
      }
    """


preview = DisclosureActionsAndDisabled()
preview  # noqa: B018
