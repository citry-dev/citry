"""Shared Field and Input scenario used by Phase 7.5 quality tools."""

from __future__ import annotations

from citry import Citry, Component


def field_input_states_component(app: Citry) -> type[Component]:
    """Create the reusable Field and Input state catalog."""

    class CitryUiFieldInputStates(Component):
        citry = app

        template = """
          <section
            class="citry-ui-quality-stack"
            aria-labelledby="field-input-states-title"
            x-data
            x-init="Alpine.store('fieldInputQuality', {
              controlled: true,
              value: 'Ochre sea star',
              invalid: false,
              formDisabled: false,
            })"
          >
            <h1 id="field-input-states-title">
              Field and Input states
            </h1>
            <c-CForm
              id="quality-field-form"
              $c-props="{ disabled: $store.fieldInputQuality.formDisabled }"
            >
              <c-CField required control_id="quality-required">
                <c-fill name="label">
                  Observation site
                </c-fill>
                <c-fill name="description">
                  Use the name on the tidepool marker.
                </c-fill>
                <c-fill name="default">
                  <c-CInput
                    id="quality-required"
                    name="site"
                    autocomplete="off"
                    placeholder="North shelf"
                  />
                </c-fill>
              </c-CField>
              <c-CField
                control_id="quality-controlled"
                $c-props="{ invalid: $store.fieldInputQuality.invalid }"
              >
                <c-fill name="label">
                  Controlled species note
                </c-fill>
                <c-fill name="error">
                  Enter at least three characters.
                </c-fill>
                <c-fill name="default">
                  <c-CInput
                    id="quality-controlled"
                    name="species"
                    $c-props="{
                      value: $store.fieldInputQuality.controlled
                        ? $store.fieldInputQuality.value
                        : undefined,
                    }"
                    @input="
                      $store.fieldInputQuality.value = $event.target.value;
                      $store.fieldInputQuality.invalid = $event.target.value.length < 3;
                    "
                  />
                </c-fill>
              </c-CField>
              <c-CField readonly control_id="quality-readonly">
                <c-fill name="label">
                  Survey permit
                </c-fill>
                <c-fill name="default">
                  <c-CInput
                    id="quality-readonly"
                    name="permit"
                    value="SHORE-204"
                  />
                </c-fill>
              </c-CField>
              <c-CField disabled control_id="quality-disabled">
                <c-fill name="label">
                  Closed trail
                </c-fill>
                <c-fill name="default">
                  <c-CInput
                    id="quality-disabled"
                    name="trail"
                    value="Cliff descent"
                  />
                </c-fill>
              </c-CField>
              <button
                id="quality-release-control"
                type="button"
                @click="$store.fieldInputQuality.controlled = false"
              >
                Release controlled value
              </button>
              <button
                id="quality-restore-control"
                type="button"
                @click="
                  $store.fieldInputQuality.value = 'Giant green anemone';
                  $store.fieldInputQuality.invalid = false;
                  $store.fieldInputQuality.controlled = true;
                "
              >
                Restore controlled value
              </button>
              <button id="quality-reset-field-form" type="reset">
                Reset survey
              </button>
            </c-CForm>
            <button
              id="quality-toggle-form-disabled"
              type="button"
              @click="$store.fieldInputQuality.formDisabled = !$store.fieldInputQuality.formDisabled"
            >
              Toggle form disabled
            </button>
          </section>
        """

    return CitryUiFieldInputStates
