---
title: Native Select
url: https://citry.dev/v/0.4.2/ui-library/components/native-select/
description: "Choose one value with native keyboard, touch, forms, validation, and an optional controlled browser value."
---
# Native Select

Use `CNativeSelect` for one choice from a finite server-owned list. It renders
one native Select element, so keyboards, touch pickers, autofill, forms,
validation, and reset keep their browser behavior.

## Native Select at a glance


### Native Select at a glance

[Open the rendered preview](/v/0.4.2/ui-library/components/native-select/_previews/at-a-glance/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectGroup, CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectAtAGlance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "habitats": [
                CNativeSelectGroup(
                    "Coastal",
                    [
                        CNativeSelectOption("kelp", "Kelp forest"),
                        CNativeSelectOption("reef", "Coral reef"),
                        CNativeSelectOption("mangrove", "Mangrove nursery"),
                    ],
                ),
                CNativeSelectGroup(
                    "Open ocean",
                    [
                        CNativeSelectOption("pelagic", "Pelagic zone"),
                        CNativeSelectOption("abyss", "Abyssal plain"),
                    ],
                ),
            ],
        }

    template = """
      <section class="ocean-glance" aria-label="Ocean habitat survey">
        <c-CField required>
          <c-fill name="label">Primary habitat</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="habitat"
              c-options="habitats"
              placeholder="Choose a habitat"
              value="reef"
            />
          </c-fill>
          <c-fill name="description">Choose the habitat represented by this dive.</c-fill>
        </c-CField>

        <div class="ocean-glance__deep" style="color-scheme: dark">
          <c-CField invalid>
            <c-fill name="label">Unverified station</c-fill>
            <c-fill name="default">
              <c-CNativeSelect
                c-options="habitats"
                placeholder="Choose a station type"
                variant="filled"
              />
            </c-fill>
            <c-fill name="error">Match this station to a surveyed habitat.</c-fill>
          </c-CField>
        </div>
      </section>
    """

    css = """
      :where(.ocean-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 54rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-glance > *) {
        padding: 1rem;
        border: 1px solid light-dark(#9ccbd3, #315f6a);
        border-radius: 0.875rem;
        background: light-dark(#f1fbfc, #10272d);
      }

      :where(.ocean-glance__deep) {
        --cui-native-select-background: #142f36;
        --cui-native-select-border-color: #57828c;
        --cui-native-select-focus-color: #7ddbea;
      }
    """


preview = NativeSelectAtAGlance()

preview  # noqa: B018
````


## Compose a labelled Select

Put Native Select inside `CField` when it needs a label, description, error,
or composed state. Pass options as `CNativeSelectOption` and
`CNativeSelectGroup` records.


### Compose Native Select in templates and Python

[Open the rendered preview](/v/0.4.2/ui-library/components/native-select/_previews/compose-select/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelect, CNativeSelectOption

citry.register_library(citry_ui)


class ComposeNativeSelect(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        options = [
            CNativeSelectOption("north", "North transect"),
            CNativeSelectOption("central", "Central transect"),
            CNativeSelectOption("south", "South transect"),
        ]
        return {
            "options": options,
            "python_select": CNativeSelect(
                options=options,
                id="python-transect",
                name="python_transect",
                value="central",
            ),
        }

    template = """
      <section class="ocean-compose">
        <c-CField>
          <c-fill name="label">Template-composed transect</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="template_transect"
              c-options="options"
              value="north"
            />
          </c-fill>
        </c-CField>

        <div>
          <label class="ocean-compose__label" for="python-transect">
            Python-composed transect
          </label>
          {{ python_select }}
        </div>
      </section>
    """

    css = """
      :where(.ocean-compose) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-compose__label) {
        display: block;
        margin-block-end: 0.5rem;
        font-weight: 650;
      }
    """


preview = ComposeNativeSelect()

preview  # noqa: B018
````


Outside `CField`, provide a native label or accessible name yourself.
`CNativeSelect` has no slots or child content.

## Build options and groups

Option values are stable form and morph identities. They must be unique and
nonempty. Groups preserve order, cannot nest, and may disable all their
options.


### Use flat options, groups, and disabled choices

[Open the rendered preview](/v/0.4.2/ui-library/components/native-select/_previews/options-and-groups/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectGroup, CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectOptions(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "regions": [
                CNativeSelectOption("harbor", "Research harbor"),
                CNativeSelectGroup(
                    "Continental shelf",
                    [
                        CNativeSelectOption("bank", "Emerald Bank"),
                        CNativeSelectOption("canyon", "Bluefin Canyon"),
                        CNativeSelectOption("closure", "Seasonal closure", disabled=True),
                    ],
                ),
                CNativeSelectGroup(
                    "Weather hold",
                    [CNativeSelectOption("offshore", "Offshore station")],
                    disabled=True,
                ),
            ],
        }

    template = """
      <section class="ocean-options">
        <c-CField>
          <c-fill name="label">Expedition region</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="region"
              c-options="regions"
              value="bank"
            />
          </c-fill>
          <c-fill name="description">Closed choices remain visible but unavailable.</c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.ocean-options) {
        max-width: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NativeSelectOptions()

preview  # noqa: B018
````


Labels are plain text. Put rich rows or search in `CSelect`, `CMultiSelect`,
or `CListbox` rather than native options. Remote data and virtualization still
need application ownership or a later dedicated collection family.

## Prompt and require a choice

`placeholder` inserts the first empty-value option. It is also required for a
conforming required single Select.


### Compare optional and required destinations

[Open the rendered preview](/v/0.4.2/ui-library/components/native-select/_previews/placeholder-and-required/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectPlaceholder(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "destinations": [
                CNativeSelectOption("lagoon", "Lagoon station"),
                CNativeSelectOption("shelf", "Shelf station"),
                CNativeSelectOption("slope", "Continental slope"),
            ],
        }

    template = """
      <c-CForm class_="ocean-placeholders">
        <c-CField required>
          <c-fill name="label">Required destination</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="required_destination"
              c-options="destinations"
              placeholder="Choose a destination"
            />
          </c-fill>
          <c-fill name="error">Choose a destination before departure.</c-fill>
        </c-CField>

        <c-CField>
          <c-fill name="label">Optional backup</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="backup_destination"
              c-options="destinations"
              placeholder="No backup destination"
            />
          </c-fill>
        </c-CField>

        <div class="ocean-placeholders__actions">
          <c-CButton type="submit">Validate route</c-CButton>
          <c-CButton type="reset" variant="outline">Reset</c-CButton>
        </div>
      </c-CForm>
    """

    css = """
      :where(.ocean-placeholders) {
        display: grid;
        gap: 1rem;
        max-width: 36rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-placeholders__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = NativeSelectPlaceholder()

preview  # noqa: B018
````


An empty string selects an existing placeholder. Without a placeholder,
`None` leaves native initial selection to the first enabled option.

## Choose a variant

`outline`, `filled`, and `plain` change the closed-control treatment without
changing the native picker.


### Compare Native Select variants

[Open the rendered preview](/v/0.4.2/ui-library/components/native-select/_previews/variants/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectVariants(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "variants": ("outline", "filled", "plain"),
            "depths": [
                CNativeSelectOption("surface", "Surface"),
                CNativeSelectOption("twilight", "Twilight zone"),
                CNativeSelectOption("midnight", "Midnight zone"),
            ],
        }

    template = """
      <section class="ocean-variants">
        <c-for each="variant in variants">
          <c-CField>
            <c-fill name="label">{{ variant.title() }}</c-fill>
            <c-fill name="default">
              <c-CNativeSelect
                c-options="depths"
                c-variant="variant"
                value="twilight"
              />
            </c-fill>
          </c-CField>
        </c-for>
      </section>
    """

    css = """
      :where(.ocean-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NativeSelectVariants()

preview  # noqa: B018
````


## Choose a size

`sm`, `md`, and `lg` adjust visual padding and text size. This `size` is not
the native listbox-size attribute, which the component rejects.


### Compare Native Select sizes

[Open the rendered preview](/v/0.4.2/ui-library/components/native-select/_previews/sizes/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "sizes": ("sm", "md", "lg"),
            "vessels": [
                CNativeSelectOption("tern", "Tern"),
                CNativeSelectOption("albatross", "Albatross"),
                CNativeSelectOption(
                    "bathyscaphe",
                    "Bathyscaphe for the long continental-slope transect",
                ),
            ],
        }

    template = """
      <section class="ocean-sizes">
        <c-for each="size in sizes">
          <c-CField>
            <c-fill name="label">{{ size.upper() }} vessel control</c-fill>
            <c-fill name="default">
              <c-CNativeSelect
                c-options="vessels"
                c-size="size"
                value="bathyscaphe"
              />
            </c-fill>
          </c-CField>
        </c-for>
      </section>
    """

    css = """
      :where(.ocean-sizes) {
        display: grid;
        gap: 1rem;
        max-width: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NativeSelectSizes()

preview  # noqa: B018
````


## Use Field and Form states

Required, disabled, and invalid keep their native differences. Native Select
does not simulate read-only behavior: a Field requesting read-only rejects
this control instead of presenting an editable control as locked.


### Compare survey states

[Open the rendered preview](/v/0.4.2/ui-library/components/native-select/_previews/field-states/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "stations": [
                CNativeSelectOption("alpha", "Station Alpha"),
                CNativeSelectOption("beta", "Station Beta"),
                CNativeSelectOption("gamma", "Station Gamma"),
            ],
        }

    template = """
      <section class="ocean-states">
        <c-CField required>
          <c-fill name="label">Required station</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="station"
              c-options="stations"
              placeholder="Choose a station"
            />
          </c-fill>
        </c-CField>
        <c-CField disabled>
          <c-fill name="label">Closed station</c-fill>
          <c-fill name="default">
            <c-CNativeSelect c-options="stations" value="beta" />
          </c-fill>
        </c-CField>
        <c-CField invalid>
          <c-fill name="label">Unverified station</c-fill>
          <c-fill name="default">
            <c-CNativeSelect c-options="stations" value="gamma" />
          </c-fill>
          <c-fill name="error">Confirm the station with bridge control.</c-fill>
        </c-CField>
        <c-CForm disabled>
          <c-CField>
            <c-fill name="label">Survey locked by Form</c-fill>
            <c-fill name="default">
              <c-CNativeSelect c-options="stations" value="alpha" />
            </c-fill>
          </c-CField>
        </c-CForm>
      </section>
    """

    css = """
      :where(.ocean-states) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NativeSelectStates()

preview  # noqa: B018
````


## Control browser selection

Supply client `value` through `$c-props` to control current selection. Mirror
the native `input` event to accept user choices. Omit the prop to release
control without replacing a valid browser-owned selection.


### Control and release a vessel assignment

[Open the rendered preview](/v/0.4.2/ui-library/components/native-select/_previews/controlled-selection/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class ControlledNativeSelect(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "vessels": [
                CNativeSelectOption("calypso", "Calypso"),
                CNativeSelectOption("nautilus", "Nautilus"),
                CNativeSelectOption("aronnax", "Aronnax"),
            ],
        }

    template = """
      <section
        class="ocean-controlled"
        x-data
        x-init="Alpine.store('nativeSelectFleet', {
          controlled: true,
          vessel: 'nautilus',
        })"
      >
        <c-CField>
          <c-fill name="label">Survey vessel</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="vessel"
              c-options="vessels"
              placeholder="Unassigned"
              $c-props="{
                value: $store.nativeSelectFleet.controlled
                  ? $store.nativeSelectFleet.vessel
                  : undefined,
              }"
              @input="$store.nativeSelectFleet.vessel = $event.target.value"
            />
          </c-fill>
          <c-fill name="description">
            <span
              x-text="$store.nativeSelectFleet.controlled
                ? 'Application controlled'
                : 'Browser controlled'"
            ></span>
          </c-fill>
        </c-CField>

        <div class="ocean-controlled__actions">
          <c-CButton
            type="button"
            size="sm"
            @click="$store.nativeSelectFleet.controlled = false"
          >
            Release
          </c-CButton>
          <c-CButton
            type="button"
            size="sm"
            variant="outline"
            @click="
              $store.nativeSelectFleet.vessel = 'calypso';
              $store.nativeSelectFleet.controlled = true;
            "
          >
            Assign Calypso
          </c-CButton>
          <c-CButton
            type="button"
            size="sm"
            variant="ghost"
            @click="
              $store.nativeSelectFleet.vessel = null;
              $store.nativeSelectFleet.controlled = true;
            "
          >
            Clear
          </c-CButton>
        </div>
      </section>
    """

    css = """
      :where(.ocean-controlled) {
        display: grid;
        gap: 1rem;
        max-width: 36rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-controlled__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = ControlledNativeSelect()

preview  # noqa: B018
````


Client `null` selects the placeholder when present, otherwise it means no
selection. Invalid or disabled controlled values report once and follow the
documented fallback. Native Select adds no value-change callback or custom
DOM event.

## Keep the platform picker

Citry UI styles the closed root. The browser or operating system owns the
open picker, including its layout, scrolling, dismissal, touch behavior, and
assistive-technology presentation.


### Use native focus, events, and external Form ownership

[Open the rendered preview](/v/0.4.2/ui-library/components/native-select/_previews/native-picker/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativePickerBoundary(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "currents": [
                CNativeSelectOption("north", "North Equatorial Current"),
                CNativeSelectOption("counter", "Equatorial Countercurrent"),
                CNativeSelectOption("south", "South Equatorial Current"),
            ],
        }

    template = """
      <section class="ocean-picker" dir="rtl">
        <form id="current-survey"></form>
        <label for="current-select">تيار المحيط</label>
        <c-CNativeSelect
          id="current-select"
          name="current"
          c-options="currents"
          value="counter"
          c-attrs="{'form': 'current-survey', 'dir': 'rtl'}"
          @change="document.querySelector('#picker-value').textContent = $event.target.value"
        />
        <div class="ocean-picker__actions">
          <c-CButton
            type="button"
            size="sm"
            @click="
              const select = document.querySelector('#current-select');
              if (select.showPicker) select.showPicker();
              else select.focus();
            "
          >
            Open native picker
          </c-CButton>
          <output id="picker-value">counter</output>
        </div>
      </section>
    """

    css = """
      :where(.ocean-picker) {
        display: grid;
        gap: 0.75rem;
        max-width: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-picker__actions) {
        display: flex;
        align-items: center;
        gap: 1rem;
      }

      :where(.ocean-picker output) {
        font-family: ui-monospace, monospace;
      }
    """


preview = NativePickerBoundary()

preview  # noqa: B018
````


Listen to native `input`, `change`, focus, and invalid events directly.
Consumers may call native methods such as `focus()` and, where supported,
`showPicker()` on the root ref. The component does not promise the open
picker's DOM or styling.

## Customize the theme

Override public variables on an ancestor or one Select. Use the stable part
selector for targeted rules.


### Theme two expedition controls

[Open the rendered preview](/v/0.4.2/ui-library/components/native-select/_previews/theme-customization/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectThemes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "instruments": [
                CNativeSelectOption("ctd", "CTD profiler"),
                CNativeSelectOption("sonar", "Multibeam sonar"),
                CNativeSelectOption("rov", "Remotely operated vehicle"),
            ],
        }

    template = """
      <section class="ocean-themes">
        <div class="ocean-themes__lagoon">
          <c-CField>
            <c-fill name="label">Lagoon instrument</c-fill>
            <c-fill name="default">
              <c-CNativeSelect c-options="instruments" value="ctd" />
            </c-fill>
          </c-CField>
        </div>
        <div class="ocean-themes__trench" style="color-scheme: dark">
          <c-CField>
            <c-fill name="label">Trench instrument</c-fill>
            <c-fill name="default">
              <c-CNativeSelect
                c-options="instruments"
                value="rov"
                class_="ocean-themes__root"
              />
            </c-fill>
          </c-CField>
        </div>
      </section>
    """

    css = """
      :where(.ocean-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-themes > div) {
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.ocean-themes__lagoon) {
        --cui-native-select-background: #f3feff;
        --cui-native-select-foreground: #103f49;
        --cui-native-select-border-color: #5ca4b0;
        --cui-native-select-hover-border-color: #236b78;
        --cui-native-select-focus-color: #087e8b;
        --cui-native-select-placeholder-color: #52717a;
        --cui-native-select-radius: 1rem;
        --cui-native-select-indicator-size: 0.5rem;
        background: #dff4f6;
      }

      :where(.ocean-themes__trench) {
        --cui-native-select-background: #10262d;
        --cui-native-select-foreground: #e0f7fa;
        --cui-native-select-border-color: #527b86;
        --cui-native-select-hover-border-color: #83bbc6;
        --cui-native-select-focus-color: #76e4f7;
        --cui-native-select-placeholder-color: #a1bdc3;
        --cui-native-select-radius: 0.25rem;
        background: #08191e;
      }

      :where(.ocean-themes__root[data-citry-ui-part="native-select"]:focus-visible) {
        outline-style: double;
      }
    """


preview = NativeSelectThemes()

preview  # noqa: B018
````


`class_` and `style` target the native root. Unlayered consumer CSS overrides
the low-specificity defaults; named layers follow the site-wide Citry UI
layer ordering contract.

## Accessibility and trust

Keep a visible label even when placeholder text is present. Native Select
adds no role, focus proxy, or keyboard handler. Labels, values, names, IDs,
and autocomplete hints render as plain text, including trusted-string
subclasses. `attrs`, `class_`, `style`, and option/group `attrs` remain trusted
code surfaces for unowned native, ARIA, data, and Alpine attributes.

Use `attrs={"form": "survey"}` for an external native Form owner. That Form
element and ID must remain stable for one Select initialization; rerender the
Select when ownership changes. Dynamic `form` bindings and duplicate
case-insensitive spellings are rejected.

## API reference

### Inputs

#### CNativeSelect server inputs

Server inputs are passed in a template through `<c-CNativeSelect ... />` or in Python
through `CNativeSelect(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 11rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="native-select-input-cnative-select-server-inputs-options"></span>`options` | `Sequence[CNativeSelectItem]` ([`CNativeSelectItem`](#native-select-interface-native-select-item)) | required | Sets the finite ordered options and one-level groups; canonical option values must be unique. |
| <span id="native-select-input-cnative-select-server-inputs-name"></span>`name` | `non-empty str | None` | `None` | Sets the native submitted name; an unnamed Select contributes no `FormData` entry. |
| <span id="native-select-input-cnative-select-server-inputs-id"></span>`id` | `str | None` | generated | Uses the Field control ID when composed, otherwise sets or generates native identity. |
| <span id="native-select-input-cnative-select-server-inputs-value"></span>`value` | `str | None` | `None` | Sets initial and reset selection; `None` or `""` selects an existing placeholder, while `None` without one uses native first-option selection. |
| <span id="native-select-input-cnative-select-server-inputs-placeholder"></span>`placeholder` | `non-empty str | None` | `None` | Inserts the enabled first empty-value option and enables native required support. |
| <span id="native-select-input-cnative-select-server-inputs-required"></span>`required` | `bool | None` | `None` | Sets native required state when standalone and requires `placeholder`; omit it inside `CField`, which owns the state. |
| <span id="native-select-input-cnative-select-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Sets local disabled state when standalone; disabled `CForm` always wins. |
| <span id="native-select-input-cnative-select-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Sets application invalid state when standalone; omit it inside `CField`. |
| <span id="native-select-input-cnative-select-server-inputs-autocomplete"></span>`autocomplete` | `str | None` | `None` | Sets the native autofill hint. |
| <span id="native-select-input-cnative-select-server-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CNativeSelectVariant`](#native-select-interface-native-select-variant)) | `"outline"` | Selects presentation. |
| <span id="native-select-input-cnative-select-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CNativeSelectSize`](#native-select-interface-native-select-size)) | `"md"` | Selects visual padding and text size; this is not native Select `size`. |
| <span id="native-select-input-cnative-select-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#native-select-interface-native-select-class-value)) | `None` | Adds native-root classes and merges them with `attrs`. |
| <span id="native-select-input-cnative-select-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#native-select-interface-native-select-style-value)) | `None` | Adds native-root inline styles and merges them with `attrs`. |
| <span id="native-select-input-cnative-select-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds native Form ownership, ARIA, data, and trusted Alpine attributes not owned by explicit inputs. |

</div>

#### CNativeSelect client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CNativeSelect />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 15rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="native-select-input-cnative-select-client-inputs-value"></span>`value` | `string | null` | Releases control and preserves the semantic native selection. | Controls current selection; `null` selects the placeholder or no selection, and `""` selects an existing placeholder. |
| <span id="native-select-input-cnative-select-client-inputs-required"></span>`required` | `boolean` | Uses the server or Field value. | Controls required state when standalone; true requires a placeholder and `CField` owns the input when composed. |
| <span id="native-select-input-cnative-select-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server, Field, or Form value. | Controls local disabled state when standalone; disabled `CForm` always wins. |
| <span id="native-select-input-cnative-select-client-inputs-invalid"></span>`invalid` | `boolean` | Uses the server or Field value. | Controls application invalid state; native invalidity still combines with it. |
| <span id="native-select-input-cnative-select-client-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CNativeSelectVariant`](#native-select-interface-native-select-variant)) | Uses the server input. | Controls presentation. |
| <span id="native-select-input-cnative-select-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CNativeSelectSize`](#native-select-interface-native-select-size)) | Uses the server input. | Controls visual padding and text size. |

</div>

### Slots

-

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CNativeSelect CSS variables

Apply these variables to `CNativeSelect` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-background"></span>`--cui-native-select-background` | `color` | Native closed-control background. | `Canvas, variant adjusted` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-foreground"></span>`--cui-native-select-foreground` | `color` | Selected text and indicator. | `CanvasText` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-border-color"></span>`--cui-native-select-border-color` | `color` | Resting border. | `Subtle CanvasText mix, variant adjusted` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-hover-border-color"></span>`--cui-native-select-hover-border-color` | `color` | Hover border. | `Stronger CanvasText mix.` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-focus-color"></span>`--cui-native-select-focus-color` | `color` | Focus outline and border. | `Highlight` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-invalid-border-color"></span>`--cui-native-select-invalid-border-color` | `color` | Invalid border. | `Scheme-aware negative color.` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-disabled-background"></span>`--cui-native-select-disabled-background` | `color` | Disabled background. | `Subtle CanvasText/Canvas mix.` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-placeholder-color"></span>`--cui-native-select-placeholder-color` | `color` | Empty placeholder text and indicator. | `Muted CanvasText mix.` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-radius"></span>`--cui-native-select-radius` | `length` | Corner radius. | `0.5rem; 0 for plain` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-inline-padding"></span>`--cui-native-select-inline-padding` | `length` | Logical inline padding. | `Size-derived length.` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-block-padding"></span>`--cui-native-select-block-padding` | `length` | Logical block padding. | `Size-derived length.` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-font-size"></span>`--cui-native-select-font-size` | `length` | Closed-control text size. | `Size-derived length.` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-indicator-size"></span>`--cui-native-select-indicator-size` | `length` | Each indicator triangle and its reserved inline space. | `0.4rem` |
| <span id="native-select-css-cnative-select-css-variables-cui-native-select-indicator-gap"></span>`--cui-native-select-indicator-gap` | `length` | Logical gap between the indicator and root edge. | `0.75rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CNativeSelect attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="native-select-attribute-cnative-select-attributes-data-required"></span>`data-required` | Native Select | `present | absent` | Mirrors effective required state. |
| <span id="native-select-attribute-cnative-select-attributes-data-disabled"></span>`data-disabled` | Native Select | `present | absent` | Mirrors effective disabled state. |
| <span id="native-select-attribute-cnative-select-attributes-data-invalid"></span>`data-invalid` | Native Select | `present | absent` | Mirrors combined application and native invalid state. |
| <span id="native-select-attribute-cnative-select-attributes-data-empty"></span>`data-empty` | Native Select | `present | absent` | Marks a selected placeholder or semantic no-selection. |
| <span id="native-select-attribute-cnative-select-attributes-data-variant"></span>`data-variant` | Native Select | `"outline" | "filled" | "plain"` | Mirrors effective presentation variant. |
| <span id="native-select-attribute-cnative-select-attributes-data-size"></span>`data-size` | Native Select | `"sm" | "md" | "lg"` | Mirrors effective visual size. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CNativeSelect selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="native-select-selector-cnative-select-selectors-native-select"></span>`[data-citry-ui-part="native-select"]` | Native Select | Stable root, styling hook, and `attrs` destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="native-select-interface-native-select-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="native-select-interface-native-select-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="native-select-interface-native-select-variant"></span>`CNativeSelectVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="native-select-interface-native-select-size"></span>`CNativeSelectSize` | `Literal["sm", "md", "lg"]` |
| <span id="native-select-interface-native-select-item"></span>`CNativeSelectItem` | `CNativeSelectOption | CNativeSelectGroup` |

</div>

<span id="native-select-interface-cnative-select-option"></span>

#### `CNativeSelectOption`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="native-select-interface-cnative-select-option-value"></span>`value` | `str` | - | Unique nonempty canonical submitted value; CR and CRLF normalize to LF, and U+0000 is invalid. |
| <span id="native-select-interface-cnative-select-option-label"></span>`label` | `str` | - | Nonempty plain-text option label. |
| <span id="native-select-interface-cnative-select-option-disabled"></span>`disabled` | `bool` | False | Disables native selection. |
| <span id="native-select-interface-cnative-select-option-attrs"></span>`attrs` | `Mapping[str, object] | None` | None | Adds trusted unowned native option attributes. |

</div>

<span id="native-select-interface-cnative-select-group"></span>

#### `CNativeSelectGroup`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="native-select-interface-cnative-select-group-label"></span>`label` | `str` | - | Nonempty plain-text group label. |
| <span id="native-select-interface-cnative-select-group-options"></span>`options` | `Sequence[CNativeSelectOption]` | - | Ordered direct options; groups cannot nest. |
| <span id="native-select-interface-cnative-select-group-disabled"></span>`disabled` | `bool` | False | Disables every option in the native group. |
| <span id="native-select-interface-cnative-select-group-attrs"></span>`attrs` | `Mapping[str, object] | None` | None | Adds trusted unowned native optgroup attributes. |

</div>

### Translation keys

-