import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonForms(Component):
    template = """
      <section
        class="split-button-forms"
        x-data="{result:'No Form action yet',owner:'accession-form'}"
      >
        <form
          id="accession-form"
          x-ref="accession"
          @submit.prevent="
            result = `Submitted ${new FormData($event.target, $event.submitter).get('action')}`
          "
          @reset="setTimeout(() => result = 'Reset accession', 0)"
        >
          <label>
            Accession name
            <input name="specimen" value="Alpine gentian" required />
          </label>
          <div class="split-button-forms__actions">
            <c-CSplitButton
              label="Commit accession actions"
              menu_label="More commit accession actions"
              type="submit"
              c-primary_attrs="{'name':'action','value':'commit'}"
            >
              <c-fill name="default">Commit accession</c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="export-draft">
                  Export draft
                </c-CMenuItem>
              </c-fill>
            </c-CSplitButton>
            <c-CSplitButton
              label="Reset accession actions"
              menu_label="More reset accession actions"
              type="reset"
              variant="outline"
            >
              <c-fill name="default">Reset accession</c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="restore-snapshot">
                  Restore saved snapshot
                </c-CMenuItem>
              </c-fill>
            </c-CSplitButton>
          </div>
        </form>

        <form
          id="secondary-accession-form"
          @submit.prevent="
            result = `Submitted to secondary Form with ${$event.submitter.value}`
          "
        >
          <label>
            Secondary accession
            <input name="secondary-specimen" value="Sea thrift" required />
          </label>
        </form>

        <label>
          External primary Form owner
          <select x-model="owner">
            <option value="accession-form">Main accession Form</option>
            <option value="secondary-accession-form">Secondary accession Form</option>
          </select>
        </label>

        <c-CSplitButton
          id="external-commit-actions"
          label="External commit actions"
          menu_label="More external commit actions"
          type="submit"
          size="sm"
          c-primary_attrs="{
            ':form':'owner',
            'name':'action',
            'value':'external-commit'
          }"
        >
          <c-fill name="default">Commit from outside</c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="download">Download draft</c-CMenuItem>
          </c-fill>
        </c-CSplitButton>

        <button
          type="button"
          @click="
            document.getElementById(owner).requestSubmit(
              document.getElementById('external-commit-actions-primary')
            )
          "
        >
          Request native submit
        </button>
        <output x-text="result">No Form action yet</output>
      </section>
    """

    css = """
      :where(.split-button-forms) {
        display: grid;
        gap: 1rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-forms form, .split-button-forms label) {
        display: grid;
        gap: 0.75rem;
      }

      :where(.split-button-forms__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = SplitButtonForms()

preview  # noqa: B018
