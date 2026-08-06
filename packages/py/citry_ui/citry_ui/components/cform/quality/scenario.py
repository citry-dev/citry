"""Shared Form scenario used by Phase 7.5 quality tools."""

from __future__ import annotations

from citry import Citry, Component


def form_states_component(app: Citry) -> type[Component]:
    """Create the reusable Form state catalog."""

    class CitryUiFormStates(Component):
        citry = app

        template = """
          <section
            class="citry-ui-quality-stack"
            aria-labelledby="form-states-title"
          >
            <h1 id="form-states-title">
              Form states
            </h1>
            <c-CForm
              id="quality-active-form"
              method="post"
              action="/quality/forms"
            >
              <c-CField required control_id="quality-form-name">
                <c-fill name="label">
                  Team name
                </c-fill>
                <c-fill name="error">
                  Enter a team name.
                </c-fill>
                <c-fill name="default">
                  <c-CInput
                    id="quality-form-name"
                    name="team_name"
                  />
                </c-fill>
              </c-CField>
              <div x-ref="optionalField">
                <c-CField control_id="quality-form-note">
                  <c-fill name="label">
                    Note
                  </c-fill>
                  <c-fill name="default">
                    <c-CInput
                      id="quality-form-note"
                      name="note"
                    />
                  </c-fill>
                </c-CField>
              </div>
              <c-CButton
                type="button"
                variant="outline"
                @click="$refs.optionalField.remove()"
              >
                Remove optional field
              </c-CButton>
              <c-CButton type="reset" variant="ghost">
                Reset
              </c-CButton>
              <c-CButton type="submit">
                Submit
              </c-CButton>
            </c-CForm>
            <label for="quality-allocation-code">
              External allocation code
            </label>
            <c-CInput
              id="quality-allocation-code"
              name="allocation_code"
              value="Q4-NORTH"
              c-attrs="{'form': 'quality-active-form'}"
            />
            <c-CForm id="quality-disabled-form" disabled>
              <c-CField control_id="quality-disabled-name">
                <c-fill name="label">
                  Disabled form
                </c-fill>
                <c-fill name="default">
                  <c-CInput
                    id="quality-disabled-name"
                    name="disabled_name"
                    value="Unavailable"
                  />
                </c-fill>
              </c-CField>
            </c-CForm>
            <c-CForm id="quality-readonly-form" readonly submitting>
              <c-CField control_id="quality-readonly-name">
                <c-fill name="label">
                  Submitting read-only form
                </c-fill>
                <c-fill name="default">
                  <c-CInput
                    id="quality-readonly-name"
                    name="readonly_name"
                    value="Saved value"
                  />
                </c-fill>
              </c-CField>
              <c-CButton type="submit">
                Saving
              </c-CButton>
            </c-CForm>
          </section>
        """

    return CitryUiFormStates
