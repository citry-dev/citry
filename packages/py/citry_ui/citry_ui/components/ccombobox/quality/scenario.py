"""Shared Combobox scenario used by Phase 7.5 quality tools."""

from __future__ import annotations

import citry_ui
from citry import Citry, Component


def combobox_states_component(app: Citry) -> type[Component]:
    """Create the reusable Combobox state catalog."""

    class CitryUiComboboxStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack"
            aria-labelledby="combobox-states-title"
            x-data
            x-init="Alpine.store('qualityCombobox', {
              controlledValue: 'vega',
              controlledQuery: 'Vega',
              remoteFailure: false,
              objects: [
                { value: 'vega', label: 'Vega', disabled: false },
                { value: 'rigel', label: 'Rigel', disabled: false },
                { value: 'sirius', label: 'Sirius', disabled: false },
              ],
              async loadOptions({ query, signal }) {
                await new Promise((resolve, reject) => {
                  const timer = setTimeout(resolve, 20);
                  signal.addEventListener('abort', () => {
                    clearTimeout(timer);
                    reject(new DOMException('Aborted', 'AbortError'));
                  });
                });
                const store = Alpine.store('qualityCombobox');
                if (store.remoteFailure) {
                  throw new Error('Representative failure');
                }
                return store.objects.filter((object) =>
                  object.label.toLowerCase().includes(query.toLowerCase())
                );
              },
            })"
          >
            <h1 id="combobox-states-title">
              Combobox states
            </h1>
            <c-CField required control_id="quality-local-combobox">
              <c-fill name="label">
                Local destination
              </c-fill>
              <c-fill name="default">
                <c-CCombobox
                  id="quality-local-combobox"
                  name="destination"
                  c-options="objects"
                  value="vega"
                />
              </c-fill>
            </c-CField>
            <c-CField control_id="quality-controlled-combobox">
              <c-fill name="label">
                Controlled destination
              </c-fill>
              <c-fill name="default">
                <c-CCombobox
                  id="quality-controlled-combobox"
                  name="controlled_destination"
                  c-options="objects"
                  $c-props="{
                    value: $store.qualityCombobox.controlledValue,
                    inputValue: $store.qualityCombobox.controlledQuery,
                    onValueChange: (value, detail) => {
                      $store.qualityCombobox.controlledValue = value;
                      $store.qualityCombobox.controlledQuery = detail.option?.label || '';
                    },
                    onInputValueChange: (value) => {
                      $store.qualityCombobox.controlledQuery = value;
                    },
                  }"
                />
              </c-fill>
            </c-CField>
            <c-CField control_id="quality-remote-combobox">
              <c-fill name="label">
                Remote catalog
              </c-fill>
              <c-fill name="default">
                <c-CCombobox
                  id="quality-remote-combobox"
                  name="remote_destination"
                  c-min_chars="1"
                  c-debounce_ms="0"
                  $c-props="{
                    loadOptions: $store.qualityCombobox.loadOptions,
                    onLoadError: () => window.__qualityComboboxFailed = true,
                  }"
                >
                  <c-fill name="loading">
                    Reading the catalog...
                  </c-fill>
                  <c-fill name="empty">
                    No matching objects.
                  </c-fill>
                  <c-fill name="error">
                    Catalog search failed.
                  </c-fill>
                </c-CCombobox>
              </c-fill>
            </c-CField>
            <c-CCombobox
              name="empty_destination"
              c-options="()"
              open
              placeholder="No options"
              c-input_attrs="{'aria-label': 'Empty destination'}"
            />
            <c-CCombobox
              name="loading_destination"
              loading
              placeholder="Loading"
              c-input_attrs="{'aria-label': 'Loading destination'}"
            />
            <c-CCombobox
              name="disabled_destination"
              c-options="objects"
              disabled
              value="rigel"
              c-input_attrs="{'aria-label': 'Disabled destination'}"
            />
            <c-CCombobox
              name="readonly_destination"
              c-options="objects"
              readonly
              value="sirius"
              c-input_attrs="{'aria-label': 'Read-only destination'}"
            />
            <c-CCombobox
              name="invalid_destination"
              c-options="objects"
              invalid
              required
              c-input_attrs="{'aria-label': 'Invalid destination'}"
            />
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "objects": (
                    citry_ui.CComboboxOption("vega", "Vega", "Blue-white star in Lyra"),
                    citry_ui.CComboboxOption("rigel", "Rigel", "Blue supergiant in Orion"),
                    citry_ui.CComboboxOption("sirius", "Sirius", "Brightest star in the night sky"),
                    citry_ui.CComboboxOption("blocked", "Unavailable target", disabled=True),
                ),
            }

    return CitryUiComboboxStates
