---
title: Combobox
url: https://citry.dev/v/0.4.4/ui-library/components/combobox/
description: "Search a local or remote collection and submit one stable option value."
---
# Combobox

`CCombobox` is a searchable single select. The submitted value must match an
option. Use it when a plain Select would be too slow to scan. It does not accept
arbitrary text as a value.

## Combobox at a glance

Options may include supporting descriptions and disabled choices. Selection,
query text, popup visibility, loading, empty, and error state stay distinct.


### Combobox at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/combobox/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ComboboxAtAGlance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="combo-glance">
        <header>
          <p>Celestial catalog</p>
          <h2>Choose a destination</h2>
        </header>
        <div class="combo-glance__grid">
          <c-CField>
            <c-fill name="label">
              Planet
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                c-options="planets"
                value="saturn"
                placeholder="Search planets"
              />
            </c-fill>
          </c-CField>
          <c-CField>
            <c-fill name="label">
              Observation target
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                c-options="targets"
                variant="filled"
                auto_highlight
                placeholder="Search targets"
              />
            </c-fill>
            <c-fill name="description">
              Arrow keys skip unavailable targets.
            </c-fill>
          </c-CField>
          <c-CField disabled>
            <c-fill name="label">
              Launch window
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                c-options="windows"
                value="aurora"
                variant="plain"
              />
            </c-fill>
          </c-CField>
        </div>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "planets": (
                citry_ui.CComboboxOption("mars", "Mars", "Rocky planet with a thin atmosphere"),
                citry_ui.CComboboxOption("saturn", "Saturn", "Gas giant surrounded by bright rings"),
                citry_ui.CComboboxOption("neptune", "Neptune", "Windy blue world in the outer system"),
            ),
            "targets": (
                citry_ui.CComboboxOption("orion", "Orion Nebula", "A bright stellar nursery"),
                citry_ui.CComboboxOption("andromeda", "Andromeda Galaxy", "Nearest large spiral galaxy"),
                citry_ui.CComboboxOption("carina", "Carina Nebula", "Southern-sky emission nebula", disabled=True),
            ),
            "windows": (citry_ui.CComboboxOption("aurora", "Aurora window"),),
        }

    css = """
      :where(.combo-glance) {
        max-width: 62rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bfdbfe, #1e3a8a);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.combo-glance header) {
        margin-block-end: 1rem;
      }

      :where(.combo-glance h2, .combo-glance p) {
        margin: 0;
      }

      :where(.combo-glance header p) {
        margin-block-end: 0.3rem;
        color: light-dark(#1d4ed8, #93c5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.combo-glance__grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        align-items: start;
      }
    """


preview = ComboboxAtAGlance()

preview  # noqa: B018
````


## Build a searchable single select

Pass `CComboboxOption` values. Add `name` only when the canonical value should
join native FormData.


### Choose a moon

[Open the rendered preview](/v/0.4.4/ui-library/components/combobox/_previews/choose-a-moon/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ChooseAMoon(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="moon-picker">
        <c-CField required>
          <c-fill name="label">
            Moon
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              name="moon_id"
              c-options="moons"
              placeholder="Search moons"
            />
          </c-fill>
          <c-fill name="description">
            Search by name, then choose one destination.
          </c-fill>
          <c-fill name="error">
            Choose a destination from the catalog.
          </c-fill>
        </c-CField>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "moons": (
                citry_ui.CComboboxOption("europa", "Europa", "Icy moon of Jupiter"),
                citry_ui.CComboboxOption("titan", "Titan", "Moon with a dense atmosphere"),
                citry_ui.CComboboxOption("triton", "Triton", "Retrograde moon of Neptune"),
                citry_ui.CComboboxOption("enceladus", "Enceladus", "Bright moon with water plumes"),
            )
        }

    css = """
      :where(.moon-picker) {
        max-width: 28rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7d2fe, #3730a3);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = ChooseAMoon()

preview  # noqa: B018
````



```citry-html
<c-CCombobox
  name="moon_id"
  c-options="moons"
  placeholder="Search moons"
/>
```



```python
from citry_ui import CCombobox, CComboboxOption

moon_picker = CCombobox(
    name="moon_id",
    options=(
        CComboboxOption("europa", "Europa", "Icy moon of Jupiter"),
        CComboboxOption("titan", "Titan", "Moon with a dense atmosphere"),
    ),
)
```


`value` is the stable identity. `label` is visible and filterable text.
`description` adds optional supporting text. Duplicate labels are allowed;
values must be unique.

Opening a local Combobox whose text still mirrors its selection shows all
options, so the trigger can choose a replacement. Once the user edits the
text, it filters normally. An explicitly controlled `inputValue` is always a
search query.

Use `CField` for the accessible label, description, error, required state, and
shared Form state. Do not use `placeholder` as the only label.

## Configure Combobox

Server inputs are passed in Python through `<c-CCombobox ... />` attributes or
a `CCombobox(...)` composition call. Client inputs are passed in the browser
through `$c-props="{...}"`.


### Configure Combobox

[Open the rendered preview](/v/0.4.4/ui-library/components/combobox/_previews/configuration/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConfigureCombobox(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section
        class="combo-config"
        x-data
        x-init="Alpine.store('comboConfig', {
          variant: 'outline',
          size: 'md',
          filter: 'contains',
          clearable: true,
          open_on_focus: false,
          auto_highlight: false,
        })"
        @citry-ui-preview-controls.window="Object.assign($store.comboConfig, $event.detail)"
      >
        <p>Observatory controls</p>
        <h2>Configure the catalog</h2>
        <c-CField>
          <c-fill name="label">
            Deep-sky object
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              c-options="objects"
              placeholder="Search the catalog"
              $c-props="{
                variant: $store.comboConfig.variant,
                size: $store.comboConfig.size,
                filter: $store.comboConfig.filter,
                clearable: $store.comboConfig.clearable,
                openOnFocus: $store.comboConfig.open_on_focus,
                autoHighlight: $store.comboConfig.auto_highlight,
              }"
            />
          </c-fill>
        </c-CField>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "objects": (
                citry_ui.CComboboxOption("m31", "Andromeda Galaxy", "Spiral galaxy in Andromeda"),
                citry_ui.CComboboxOption("m42", "Orion Nebula", "Diffuse nebula in Orion"),
                citry_ui.CComboboxOption("m45", "Pleiades", "Open star cluster in Taurus"),
                citry_ui.CComboboxOption("ngc7000", "North America Nebula", "Emission nebula in Cygnus"),
            )
        }

    css = """
      :where(.combo-config) {
        display: grid;
        gap: 0.75rem;
        max-width: 38rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #075985);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.combo-config h2, .combo-config p) {
        margin: 0;
      }

      :where(.combo-config > p) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "outline",
        "options": (("outline", "Outline"), ("filled", "Filled"), ("plain", "Plain")),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "filter",
        "label": "Local filter",
        "type": "select",
        "default": "contains",
        "options": (("contains", "Contains"), ("starts_with", "Starts with"), ("none", "None")),
    },
    {"name": "clearable", "label": "Show clear action", "type": "checkbox", "default": True},
    {"name": "open_on_focus", "label": "Open on focus", "type": "checkbox", "default": False},
    {"name": "auto_highlight", "label": "Highlight first match", "type": "checkbox", "default": False},
)

preview = ConfigureCombobox()

preview  # noqa: B018
````


`variant`, `size`, `filter`, `clearable`, `open_on_focus`, and
`auto_highlight` have matching client inputs. A valid client input wins. Remove
it to return configuration to the server value.

`value`, `inputValue`, and `open` behave differently: each is independently
controlled while supplied. Removing query or popup control preserves its last
committed state. `value=null` is an intentional controlled empty selection.

`auto_highlight` only moves the active option. It does not select on blur or
Tab. `min_chars` applies to popup visibility and remote loading, including
trigger and keyboard opening.

## Search remote options

Pass `loadOptions` through client props. It receives the committed query, an
AbortSignal, and a request ID. Return one complete valid item array.


### Search a star catalog

[Open the rendered preview](/v/0.4.4/ui-library/components/combobox/_previews/remote-catalog/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RemoteStarCatalog(Component):
    template = """
      <section
        class="remote-stars"
        x-data
        x-init="Alpine.store('remoteStars', {
          async loadStars({ query, signal }) {
            await new Promise((resolve, reject) => {
              const timer = setTimeout(resolve, 350);
              signal.addEventListener('abort', () => {
                clearTimeout(timer);
                reject(new DOMException('Aborted', 'AbortError'));
              }, { once: true });
            });
            if (query.toLowerCase() === 'offline') {
              throw new Error('Catalog unavailable');
            }
            const stars = [
              { value: 'vega', label: 'Vega', description: 'Blue-white star in Lyra' },
              { value: 'rigel', label: 'Rigel', description: 'Blue supergiant in Orion' },
              { value: 'sirius', label: 'Sirius', description: 'Brightest star in the night sky' },
              { value: 'betelgeuse', label: 'Betelgeuse', description: 'Red supergiant in Orion' },
            ];
            const needle = query.toLowerCase();
            return stars.filter((star) => star.label.toLowerCase().includes(needle));
          },
        })"
      >
        <c-CField>
          <c-fill name="label">
            Star catalog
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              c-min_chars="2"
              c-debounce_ms="150"
              placeholder="Type at least two letters"
              $c-props="{ loadOptions: $store.remoteStars.loadStars }"
            >
              <c-fill name="loading">
                Reading the catalog...
              </c-fill>
              <c-fill name="empty">
                No catalog match.
              </c-fill>
              <c-fill name="error">
                The catalog could not be read.
              </c-fill>
            </c-CCombobox>
          </c-fill>
          <c-fill name="description">
            Try Vega, Rigel, Sirius, or Betelgeuse. Type offline to preview recovery.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.remote-stars) {
        max-width: 30rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#a5b4fc, #4338ca);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = RemoteStarCatalog()

preview  # noqa: B018
````



```citry-html
<c-CCombobox
  c-min_chars="2"
  c-debounce_ms="250"
  $c-props="{
    loadOptions: async ({ query, signal, requestId }) => {
      const response = await fetch(`/stars?q=${encodeURIComponent(query)}`, {
        signal,
      });
      return await response.json();
    },
  }"
/>
```


A new qualifying query aborts the previous request. Request identity still
rejects stale results when a loader ignores abort. Closing, reset, disabled or
read-only state, replacement, and cleanup also abort work.

Replacing `loadOptions` aborts its current request. A valid replacement loads
the current qualifying query when the popup is open; `null` returns to local
filtering.

Use the `loading`, `empty`, and `error` slots to match surrounding language.
Errors never render exception text. A later valid query can recover.

Remote mode bypasses local filtering. For local data, choose `contains`,
`starts_with`, or `none`. Matching is plain case-insensitive text matching, not
locale-aware or fuzzy search.

## Control browser state

Control selection, query, and popup independently. Every callback reports the
affected axis, reason, ownership, and browser source.


### Control a mission target

[Open the rendered preview](/v/0.4.4/ui-library/components/combobox/_previews/controlled-state/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledMissionTarget(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section
        class="controlled-target"
        x-data
        x-init="Alpine.store('missionTarget', {
          value: null,
          query: '',
          open: false,
          lastReason: 'none',
        })"
      >
        <c-CField>
          <c-fill name="label">
            Mission target
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              c-options="targets"
              $c-props="{
                value: $store.missionTarget.value,
                inputValue: $store.missionTarget.query,
                open: $store.missionTarget.open,
                onValueChange: (next, detail) => {
                  $store.missionTarget.value = next;
                  $store.missionTarget.lastReason = `value: ${detail.reason}`;
                },
                onInputValueChange: (next, detail) => {
                  $store.missionTarget.query = next;
                  $store.missionTarget.lastReason = `query: ${detail.reason}`;
                },
                onOpenChange: (next, detail) => {
                  $store.missionTarget.open = next;
                  $store.missionTarget.lastReason = `popup: ${detail.reason}`;
                },
              }"
            />
          </c-fill>
        </c-CField>
        <dl aria-live="polite">
          <div>
            <dt>Value</dt>
            <dd x-text="$store.missionTarget.value ?? 'none'">none</dd>
          </div>
          <div>
            <dt>Query</dt>
            <dd x-text="$store.missionTarget.query || 'empty'">empty</dd>
          </div>
          <div>
            <dt>Last request</dt>
            <dd x-text="$store.missionTarget.lastReason">none</dd>
          </div>
        </dl>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "targets": (
                citry_ui.CComboboxOption("ceres", "Ceres", "Dwarf planet in the asteroid belt"),
                citry_ui.CComboboxOption("vesta", "Vesta", "Large rocky asteroid"),
                citry_ui.CComboboxOption("psyche", "16 Psyche", "Metal-rich asteroid"),
            )
        }

    css = """
      :where(.controlled-target) {
        display: grid;
        gap: 1rem;
        max-width: 34rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#ddd6fe, #5b21b6);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.controlled-target dl) {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0;
      }

      :where(.controlled-target dl > div) {
        min-width: 0;
        padding: 0.625rem;
        border-radius: 0.5rem;
        background: color-mix(in srgb, CanvasText 6%, Canvas);
      }

      :where(.controlled-target dt) {
        color: color-mix(in srgb, currentColor 65%, transparent);
        font-size: 0.75rem;
      }

      :where(.controlled-target dd) {
        margin: 0.2rem 0 0;
        overflow-wrap: anywhere;
        font-size: 0.875rem;
        font-weight: 650;
      }
    """


preview = ControlledMissionTarget()

preview  # noqa: B018
````



```citry-html
<c-CCombobox
  $c-props="{
    value: targetId,
    inputValue: targetQuery,
    open: targetOpen,
    onValueChange: (value, detail) => targetId = value,
    onInputValueChange: (query, detail) => targetQuery = query,
    onOpenChange: (open, detail) => targetOpen = open,
  }"
/>
```


An uncontrolled axis commits before its callback. A controlled callback is a
request; update the matching client input to accept it. Owner commits do not
notify again. Selecting an option requests value, label query, then close in
that order, but controlling one axis never takes ownership of another.

If a selected value temporarily has no item, its canonical value and last
known label survive. A later matching item rehydrates the label without a
callback. This supports options that arrive after selection.

## Use native Forms and validation

`name` adds a hidden canonical input. The visible text input owns native
validation but never submits its label.


### Submit a launch destination

[Open the rendered preview](/v/0.4.4/ui-library/components/combobox/_previews/form-destination/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LaunchDestinationForm(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section
        class="launch-form"
        x-data="{ result: 'No route submitted.' }"
      >
        <header>
          <p>Flight plan</p>
          <h2>Choose a launch destination</h2>
        </header>
        <c-CForm
          @submit.prevent="result = `Route: ${new FormData($el).get('destination_id')}`"
          @reset="result = 'Flight plan reset.'"
        >
          <c-CField required>
            <c-fill name="label">
              Destination
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                name="destination_id"
                c-options="destinations"
                value="luna"
              />
            </c-fill>
            <c-fill name="error">
              Choose a destination from the route catalog.
            </c-fill>
          </c-CField>
          <div class="launch-form__actions">
            <c-CButton type="submit">
              Submit route
            </c-CButton>
            <c-CButton
              type="reset"
              variant="ghost"
              intent="neutral"
            >
              Reset
            </c-CButton>
          </div>
        </c-CForm>
        <p
          class="launch-form__result"
          aria-live="polite"
          x-text="result"
        >
          No route submitted.
        </p>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "destinations": (
                citry_ui.CComboboxOption("luna", "Lunar orbit", "Three-day transfer"),
                citry_ui.CComboboxOption("mars", "Mars transfer", "Hohmann transfer window"),
                citry_ui.CComboboxOption("europa", "Europa flyby", "Outer-system gravity assists"),
            )
        }

    css = """
      :where(.launch-form) {
        max-width: 36rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0c4a6e);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.launch-form header) {
        margin-block-end: 1rem;
      }

      :where(.launch-form h2, .launch-form p) {
        margin: 0;
      }

      :where(.launch-form header p) {
        margin-block-end: 0.3rem;
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.launch-form__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
        margin-block-start: 1rem;
      }

      :where(.launch-form__result) {
        margin-block-start: 1rem;
        color: color-mix(in srgb, currentColor 70%, transparent);
        font-size: 0.875rem;
      }
    """


preview = LaunchDestinationForm()

preview  # noqa: B018
````


Required validity needs a selected option, not merely typed text. Disabled
Comboboxes are omitted from FormData. Read-only Comboboxes keep their value but
cannot edit, open, select, or clear.

An uncanceled native reset restores uncontrolled server values. Controlled
axes reassert their browser values after the reset turn. A canceled reset does
nothing.

Before browser activation, the visible input is read-only. If scripts fail,
the displayed label cannot change while an old hidden key is submitted. The
server must still verify that every submitted key is allowed.

Browser autofill is treated as text input. It clears an old canonical value and
never guesses identity from a label, including duplicate labels.

## Use the keyboard


### Navigate constellations

[Open the rendered preview](/v/0.4.4/ui-library/components/combobox/_previews/keyboard-navigation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConstellationKeyboardPicker(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="constellation-keys">
        <header>
          <p>Keyboard chart</p>
          <h2>Navigate constellations</h2>
        </header>
        <c-CField>
          <c-fill name="label">
            Constellation
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              c-options="constellations"
              open_on_focus
              auto_highlight
              placeholder="Search constellations"
            />
          </c-fill>
          <c-fill name="description">
            Try Arrow keys, Home, End, Enter, Escape, and Tab.
          </c-fill>
        </c-CField>
        <p class="constellation-keys__note">
          Cetus is unavailable and is skipped by keyboard navigation.
        </p>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "constellations": (
                citry_ui.CComboboxOption("andromeda", "Andromeda", "Northern constellation"),
                citry_ui.CComboboxOption("cetus", "Cetus", "Sea-monster constellation", disabled=True),
                citry_ui.CComboboxOption("cygnus", "Cygnus", "Northern Cross"),
                citry_ui.CComboboxOption("lyra", "Lyra", "Home of Vega"),
                citry_ui.CComboboxOption("orion", "Orion", "Prominent winter constellation"),
            )
        }

    css = """
      :where(.constellation-keys) {
        max-width: 32rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #5b21b6);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.constellation-keys header) {
        margin-block-end: 1rem;
      }

      :where(.constellation-keys h2, .constellation-keys p) {
        margin: 0;
      }

      :where(.constellation-keys header p) {
        margin-block-end: 0.3rem;
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.constellation-keys__note) {
        margin-block-start: 1rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }
    """


preview = ConstellationKeyboardPicker()

preview  # noqa: B018
````


- ArrowDown and ArrowUp open and move across enabled options with wrap.
- Home and End move to the first or last enabled option while open.
- Enter selects the highlighted option.
- Escape closes without selecting.
- Tab closes and continues native focus order without selecting.
- Printable keys, IME, editing shortcuts, and horizontal arrows remain native.

DOM focus stays on the input. `aria-activedescendant` exposes the highlighted
option. Pointer selection keeps input focus through the commit. The trigger and
clear actions are outside sequential Tab order so the composite uses one Tab
stop.

## Theme and customize Combobox

Use `class_`, `style`, public CSS variables, or documented selectors. Do not
target private `.cui-*` classes.


### Theme a deep-sky picker

[Open the rendered preview](/v/0.4.4/ui-library/components/combobox/_previews/theme-customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DeepSkyTheme(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="deep-sky-theme">
        <header>
          <p>Deep-sky palette</p>
          <h2>Search the Messier catalog</h2>
        </header>
        <c-CField>
          <c-fill name="label">
            Messier object
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              c-options="objects"
              value="m51"
              class_="deep-sky-theme__picker"
            />
          </c-fill>
        </c-CField>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "objects": (
                citry_ui.CComboboxOption("m1", "Crab Nebula", "Supernova remnant in Taurus"),
                citry_ui.CComboboxOption("m42", "Orion Nebula", "Stellar nursery in Orion"),
                citry_ui.CComboboxOption("m51", "Whirlpool Galaxy", "Interacting spiral galaxies"),
                citry_ui.CComboboxOption("m104", "Sombrero Galaxy", "Galaxy with a bright central bulge"),
            )
        }

    css = """
      :where(.deep-sky-theme) {
        --cui-combobox-background: #11142b;
        --cui-combobox-foreground: #f5f3ff;
        --cui-combobox-border-color: #6d5bd0;
        --cui-combobox-focus-color: #f0abfc;
        --cui-combobox-popup-background: #171a35;
        --cui-combobox-popup-border-color: #8171d8;
        --cui-combobox-highlighted-background: #312e81;
        --cui-combobox-selected-background: #4c1d95;
        --cui-combobox-option-description-color: #c4b5fd;

        max-width: 34rem;
        padding: 1.25rem;
        border: 1px solid #5145a6;
        border-radius: 0.875rem;
        background: #0b1024;
        color: #f5f3ff;
        color-scheme: dark;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.deep-sky-theme header) {
        margin-block-end: 1rem;
      }

      :where(.deep-sky-theme h2, .deep-sky-theme p) {
        margin: 0;
      }

      :where(.deep-sky-theme header p) {
        margin-block-end: 0.3rem;
        color: #f0abfc;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.deep-sky-theme__picker) {
        --cui-combobox-radius: 0.75rem;
        --cui-combobox-popup-shadow: 0 1rem 3rem rgb(0 0 0 / 45%);
      }
    """


preview = DeepSkyTheme()

preview  # noqa: B018
````


Variables inherit, so a container can theme several Comboboxes. Set one on the
root for an isolated override. Public selectors such as
`[data-citry-ui-part="option-description"]` target stable elements. Reflected
attributes such as `data-open`, `data-loading`, `data-selected`, and
`data-highlighted` expose current styling state.

The popup stays under the component and inherits its theme. It does not use the
browser top layer yet, so an ancestor with clipped overflow may clip it.

## Support narrow, translated, and directional content


### Explore long celestial names

[Open the rendered preview](/v/0.4.4/ui-library/components/combobox/_previews/environment/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CelestialNamesEnvironment(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="celestial-environment">
        <div
          dir="rtl"
          style="color-scheme: dark"
        >
          <c-CField>
            <c-fill name="label">
              جرم سماوي
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                c-options="arabic_objects"
                value="thurayya"
                size="sm"
              />
            </c-fill>
          </c-CField>
        </div>
        <div
          class="celestial-environment__narrow"
          style="color-scheme: light"
        >
          <c-CField>
            <c-fill name="label">
              Long catalog name
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                c-options="long_names"
                open_on_focus
                placeholder="Search long names"
              />
            </c-fill>
          </c-CField>
        </div>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "arabic_objects": (
                citry_ui.CComboboxOption("thurayya", "الثريا", "عنقود نجمي مفتوح"),
                citry_ui.CComboboxOption("jauza", "الجوزاء", "كوكبة بارزة في سماء الشتاء"),
            ),
            "long_names": (
                citry_ui.CComboboxOption(
                    "andromeda-satellite",
                    "Andromeda Galaxy satellite candidate in the outer stellar halo",
                    "A deliberately long label that wraps instead of covering the action controls",
                ),
                citry_ui.CComboboxOption(
                    "magellanic-stream",
                    "Magellanic Stream high-velocity cloud observation",
                    "Supporting text also wraps inside a narrow popup",
                ),
            ),
        }

    css = """
      :where(.celestial-environment) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
        gap: 1rem;
        align-items: start;
        max-width: 48rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bfdbfe, #1e40af);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.celestial-environment__narrow) {
        max-width: 17rem;
      }
    """


preview = CelestialNamesEnvironment()

preview  # noqa: B018
````


Logical properties support RTL. Labels and descriptions wrap inside the
scrollable popup. Default colors support light and dark schemes and retain
boundaries and highlight in forced colors.

Version 1 targets ordinary collections up to 1,000 items. Grouping,
virtualization, infinite loading, multiple selection, free values, create-new,
and arbitrary option rendering remain separate later work.

## API reference

### Inputs

#### CCombobox server inputs

Server inputs are passed in a template through `<c-CCombobox ... />` or in Python through
`CCombobox(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 9rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="combobox-input-ccombobox-server-inputs-options"></span>`options` | `Sequence[CComboboxOption]` | `"()"` | Supplies the initial strict-selection collection. |
| <span id="combobox-input-ccombobox-server-inputs-name"></span>`name` | `str | None` | `None` | Adds the optional hidden native submitted name. Omit it when the control does not participate in a Form. |
| <span id="combobox-input-ccombobox-server-inputs-id"></span>`id` | `str | None` | Uses the Field ID or a generated ID. | Sets visible-input, listbox, and option identity. |
| <span id="combobox-input-ccombobox-server-inputs-value"></span>`value` | `str | None` | `None` | Sets initial canonical selection. A value may arrive before its matching item. |
| <span id="combobox-input-ccombobox-server-inputs-input-value"></span>`input_value` | `str | None` | Uses the selected label or an empty string. | Sets initial editable query text. |
| <span id="combobox-input-ccombobox-server-inputs-open"></span>`open` | `bool` | `False` | Sets initial popup visibility when interaction and the query threshold allow it. |
| <span id="combobox-input-ccombobox-server-inputs-required"></span>`required` | `bool | None` | `None` | Requires canonical selection when standalone; `CField` owns this state when composed. |
| <span id="combobox-input-ccombobox-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Disables interaction and Form participation when standalone; disabled `CForm` always wins and `CField` owns this state when composed. |
| <span id="combobox-input-ccombobox-server-inputs-readonly"></span>`readonly` | `bool | None` | Inherits CForm when standalone. | Preserves Form participation but blocks editing, opening, clearing, and selection; `CField` owns this state when composed. |
| <span id="combobox-input-ccombobox-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Sets application invalid presentation when standalone; `CField` owns this state when composed. |
| <span id="combobox-input-ccombobox-server-inputs-loading"></span>`loading` | `bool` | `False` | Adds external loading presentation to internal remote loading. |
| <span id="combobox-input-ccombobox-server-inputs-clearable"></span>`clearable` | `bool` | `True` | Shows the clear action when selection or query text exists. |
| <span id="combobox-input-ccombobox-server-inputs-open-on-focus"></span>`open_on_focus` | `bool` | `False` | Opens on input focus when the query meets `min_chars`. |
| <span id="combobox-input-ccombobox-server-inputs-auto-highlight"></span>`auto_highlight` | `bool` | `False` | Highlights the first enabled match after filtering or loading without selecting it on blur or Tab. |
| <span id="combobox-input-ccombobox-server-inputs-filter"></span>`filter` | `"contains" | "starts_with" | "none"` ([`CComboboxFilter`](#combobox-interface-input-type-aliases-ccombobox-filter)) | `"contains"` | Selects plain case-insensitive local matching. Remote mode bypasses it. |
| <span id="combobox-input-ccombobox-server-inputs-min-chars"></span>`min_chars` | `non-negative int` | `0` | Sets the minimum Unicode-code-point query length for popup visibility and remote loading. |
| <span id="combobox-input-ccombobox-server-inputs-debounce-ms"></span>`debounce_ms` | `non-negative int` | `200` | Sets remote request delay in milliseconds. |
| <span id="combobox-input-ccombobox-server-inputs-placeholder"></span>`placeholder` | `str | None` | `None` | Sets the visible native-input placeholder. |
| <span id="combobox-input-ccombobox-server-inputs-autocomplete"></span>`autocomplete` | `non-empty str` | `"off"` | Sets the visible native-input autocomplete hint. Browser heuristics may still override it. |
| <span id="combobox-input-ccombobox-server-inputs-inputmode"></span>`inputmode` | `str | None` | `None` | Sets the visible native-input virtual-keyboard hint. |
| <span id="combobox-input-ccombobox-server-inputs-required-message"></span>`required_message` | `non-empty str` | `"Select an option."` | Sets native custom-validity text for a missing required selection. |
| <span id="combobox-input-ccombobox-server-inputs-clear-label"></span>`clear_label` | `non-empty str` | `"Clear selection"` | Names the clear Button. |
| <span id="combobox-input-ccombobox-server-inputs-open-label"></span>`open_label` | `non-empty str` | `"Show options"` | Names the closed popup trigger. |
| <span id="combobox-input-ccombobox-server-inputs-close-label"></span>`close_label` | `non-empty str` | `"Hide options"` | Names the open popup trigger. |
| <span id="combobox-input-ccombobox-server-inputs-loading-label"></span>`loading_label` | `non-empty str` | `"Loading options..."` | Sets fallback loading status text. |
| <span id="combobox-input-ccombobox-server-inputs-empty-label"></span>`empty_label` | `non-empty str` | `"No options found."` | Sets fallback empty status text. |
| <span id="combobox-input-ccombobox-server-inputs-error-label"></span>`error_label` | `non-empty str` | `"Options could not be loaded."` | Sets fallback remote-error status text. |
| <span id="combobox-input-ccombobox-server-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CComboboxVariant`](#combobox-interface-input-type-aliases-ccombobox-variant)) | `"outline"` | Selects control presentation. |
| <span id="combobox-input-ccombobox-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CComboboxSize`](#combobox-interface-input-type-aliases-ccombobox-size)) | `"md"` | Selects control geometry. |
| <span id="combobox-input-ccombobox-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#combobox-interface-input-type-aliases-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="combobox-input-ccombobox-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#combobox-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="combobox-input-ccombobox-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native, ARIA, Alpine, and data attributes to the root. Prefer the top-level class and style inputs. |
| <span id="combobox-input-ccombobox-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds allowed attributes to the visible input. `form` is rejected so validation and submitted value cannot have different owners. |

</div>

#### CCombobox client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CCombobox />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="combobox-input-ccombobox-client-inputs-items"></span>`items` | `CComboboxItem[]` ([`CComboboxItem`](#combobox-interface-ccombobox-item)) | Keeps the current collection. | Replaces the current collection while valid. `null`, malformed entries, and duplicate values retain the prior collection and report once per invalid episode. |
| <span id="combobox-input-ccombobox-client-inputs-value"></span>`value` | `non-empty string | null` | Continues uncontrolled from the current selection. | Controls canonical selection while supplied. `null` is an intentional empty controlled value; empty strings and other invalid values release control from current state. |
| <span id="combobox-input-ccombobox-client-inputs-input-value"></span>`inputValue` | `string | null` | Continues uncontrolled from the current query. `null` has the same effect. | Controls editable query text while supplied as a string. Invalid values report and release control. |
| <span id="combobox-input-ccombobox-client-inputs-open"></span>`open` | `boolean | null` | Continues uncontrolled from current visibility. `null` has the same effect. | Controls requested popup visibility; disabled, read-only, and query-threshold rules still determine effective visibility. |
| <span id="combobox-input-ccombobox-client-inputs-required"></span>`required` | `boolean` | Uses the server value. | Controls required state only when standalone. `CField` owns it when composed. |
| <span id="combobox-input-ccombobox-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server value. | Controls local disabled state only when standalone. Disabled `CForm` always wins and `CField` owns it when composed. |
| <span id="combobox-input-ccombobox-client-inputs-readonly"></span>`readonly` | `boolean` | Uses the server or reactive CForm value. | Controls read-only state only when standalone. `CField` owns it when composed. |
| <span id="combobox-input-ccombobox-client-inputs-invalid"></span>`invalid` | `boolean` | Uses the server value. | Controls application invalid state only when standalone. `CField` owns it when composed. |
| <span id="combobox-input-ccombobox-client-inputs-loading"></span>`loading` | `boolean` | Uses the server input. | Adds external loading presentation. |
| <span id="combobox-input-ccombobox-client-inputs-clearable"></span>`clearable` | `boolean` | Uses the server input. | Controls clear-action visibility. |
| <span id="combobox-input-ccombobox-client-inputs-open-on-focus"></span>`openOnFocus` | `boolean` | Uses the server input. | Controls focus-triggered opening. |
| <span id="combobox-input-ccombobox-client-inputs-auto-highlight"></span>`autoHighlight` | `boolean` | Uses the server input. | Controls first-match highlight after filtering or loading. |
| <span id="combobox-input-ccombobox-client-inputs-filter"></span>`filter` | `"contains" | "starts_with" | "none"` ([`CComboboxFilter`](#combobox-interface-input-type-aliases-ccombobox-filter)) | Uses the server input. | Controls local matching. |
| <span id="combobox-input-ccombobox-client-inputs-min-chars"></span>`minChars` | `non-negative integer` | Uses the server input. | Controls the Unicode-code-point popup and remote-query threshold. |
| <span id="combobox-input-ccombobox-client-inputs-debounce-ms"></span>`debounceMs` | `non-negative integer` | Uses the server input. | Controls remote delay. |
| <span id="combobox-input-ccombobox-client-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CComboboxVariant`](#combobox-interface-input-type-aliases-ccombobox-variant)) | Uses the server input. | Controls presentation. |
| <span id="combobox-input-ccombobox-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CComboboxSize`](#combobox-interface-input-type-aliases-ccombobox-size)) | Uses the server input. | Controls geometry. |
| <span id="combobox-input-ccombobox-client-inputs-load-options"></span>`loadOptions` | `(request: CComboboxLoadRequest) => Promise<CComboboxItem[]> | CComboboxItem[]` ([`CComboboxLoadRequest`](#combobox-interface-ccombobox-load-request), [`CComboboxItem`](#combobox-interface-ccombobox-item)) | Uses local filtering. | Loads one complete replacement collection for the committed query. `null` disables remote mode. Replacing or removing the function aborts current work; a valid replacement reloads a qualifying open query. |
| <span id="combobox-input-ccombobox-client-inputs-on-value-change"></span>`onValueChange` | `function` | Does not notify a selection callback. | Receives user and reset selection requests. |
| <span id="combobox-input-ccombobox-client-inputs-on-input-value-change"></span>`onInputValueChange` | `function` | Does not notify a query callback. | Receives user and reset query requests. |
| <span id="combobox-input-ccombobox-client-inputs-on-open-change"></span>`onOpenChange` | `function` | Does not notify a visibility callback. | Receives user-authored popup requests and query-threshold closure. |
| <span id="combobox-input-ccombobox-client-inputs-on-load-error"></span>`onLoadError` | `function` | Does not notify a loading-error callback. | Receives current non-abort remote failures after safe error presentation. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CCombobox slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="combobox-slot-ccombobox-slots-loading"></span>`loading` | no | `{}` ([`CComboboxLoadingSlotData`](#combobox-interface-ccombobox-loading-slot-data)) | `loading_label` |
| <span id="combobox-slot-ccombobox-slots-empty"></span>`empty` | no | `{}` ([`CComboboxEmptySlotData`](#combobox-interface-ccombobox-empty-slot-data)) | `empty_label` |
| <span id="combobox-slot-ccombobox-slots-error"></span>`error` | no | `{}` ([`CComboboxErrorSlotData`](#combobox-interface-ccombobox-error-slot-data)) | `error_label` |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CCombobox events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="combobox-event-ccombobox-events-on-value-change"></span>`onValueChange` | `(value: string | null, detail: CComboboxValueChangeDetail) => void` ([`CComboboxValueChangeDetail`](#combobox-interface-ccombobox-value-change-detail)) | Option selection, clear, text invalidation, or uncanceled reset requests a different canonical value. | `{reason: "option" | "clear" | "input" | "reset", option: CComboboxItem | null, query: string, controlled: boolean, source: EventTarget | null}` ([`CComboboxValueChangeDetail`](#combobox-interface-ccombobox-value-change-detail), [`CComboboxItem`](#combobox-interface-ccombobox-item)) | Uncontrolled value and Form state commit before notification. Controlled requests wait for the owner. Owner commits and repeated values do not notify. |
| <span id="combobox-event-ccombobox-events-on-input-value-change"></span>`onInputValueChange` | `(query: string, detail: CComboboxInputValueChangeDetail) => void` ([`CComboboxInputValueChangeDetail`](#combobox-interface-ccombobox-input-value-change-detail)) | Input, option, clear, blur reconciliation, or uncanceled reset requests different query text. | `{reason: "input" | "option" | "clear" | "blur" | "reset", controlled: boolean, source: EventTarget | null}` ([`CComboboxInputValueChangeDetail`](#combobox-interface-ccombobox-input-value-change-detail)) | Uncontrolled visible text commits before notification. Controlled requests wait for the owner. Owner commits do not notify. |
| <span id="combobox-event-ccombobox-events-on-open-change"></span>`onOpenChange` | `(open: boolean, detail: CComboboxOpenChangeDetail) => void` ([`CComboboxOpenChangeDetail`](#combobox-interface-ccombobox-open-change-detail)) | Input, focus, trigger, keyboard, selection, Escape, outside press, blur, reset, or threshold requests different visibility. | `{reason: "input" | "focus" | "trigger" | "keyboard" | "selection" | "escape" | "outside" | "blur" | "reset" | "minimum-characters", controlled: boolean, source: EventTarget | null}` ([`CComboboxOpenChangeDetail`](#combobox-interface-ccombobox-open-change-detail)) | Uncontrolled visibility and ARIA commit before notification. Controlled requests wait for the owner. Owner commits do not notify. |
| <span id="combobox-event-ccombobox-events-on-load-error"></span>`onLoadError` | `(error: unknown, detail: CComboboxLoadErrorDetail) => void` ([`CComboboxLoadErrorDetail`](#combobox-interface-ccombobox-load-error-detail)) | The current remote loader throws, rejects, or returns an invalid collection for a reason other than abort. | `{query: string, requestId: number}` ([`CComboboxLoadErrorDetail`](#combobox-interface-ccombobox-load-error-detail)) | Error presentation appears before notification. Abort and stale requests do not notify. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CCombobox CSS variables

Apply these variables to `CCombobox` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-background"></span>`--cui-combobox-background` | `color` | Control background. | `Canvas` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-foreground"></span>`--cui-combobox-foreground` | `color` | Control and popup text. | `CanvasText` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-border-color"></span>`--cui-combobox-border-color` | `color` | Resting control border. | `Subtle CanvasText mix.` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-focus-color"></span>`--cui-combobox-focus-color` | `color` | Focus ring and border. | `Highlight` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-invalid-color"></span>`--cui-combobox-invalid-color` | `color` | Invalid border. | `Scheme-aware error color.` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-radius"></span>`--cui-combobox-radius` | `length` | Control, popup, and option radius basis. | `0.5rem` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-height"></span>`--cui-combobox-height` | `length` | Minimum control height. | `Size-derived.` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-inline-padding"></span>`--cui-combobox-inline-padding` | `length` | Input logical inline padding. | `Size-derived.` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-icon-size"></span>`--cui-combobox-icon-size` | `length` | Clear and trigger Button size. | `2.25rem` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-popup-background"></span>`--cui-combobox-popup-background` | `color` | Popup surface. | `Canvas` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-popup-border-color"></span>`--cui-combobox-popup-border-color` | `color` | Popup border. | `Subtle CanvasText mix.` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-popup-shadow"></span>`--cui-combobox-popup-shadow` | `shadow` | Popup elevation. | `0 0.75rem 2rem rgb(15 23 42 / 18%)` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-popup-max-height"></span>`--cui-combobox-popup-max-height` | `length` | Scrollable list height. | `18rem` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-option-padding"></span>`--cui-combobox-option-padding` | `length` | Option padding. | `0.625rem 0.75rem` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-option-gap"></span>`--cui-combobox-option-gap` | `length` | Gap between option label and description. | `0.125rem` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-option-description-color"></span>`--cui-combobox-option-description-color` | `color` | Supporting option text. | `Muted current color.` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-highlighted-background"></span>`--cui-combobox-highlighted-background` | `color` | Keyboard or pointer highlight. | `Subtle Highlight/Canvas mix.` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-selected-background"></span>`--cui-combobox-selected-background` | `color` | Committed selected-option background. | `Stronger Highlight/Canvas mix.` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-disabled-opacity"></span>`--cui-combobox-disabled-opacity` | `number` | Disabled control and option opacity. | `0.55` |
| <span id="combobox-css-ccombobox-css-variables-cui-combobox-error-color"></span>`--cui-combobox-error-color` | `color` | Remote error text. | `Scheme-aware error color.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CCombobox attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="combobox-attribute-ccombobox-root-attributes-data-open"></span>`data-open` | Root | `present | absent` | Mirrors effective popup visibility. |
| <span id="combobox-attribute-ccombobox-root-attributes-data-loading"></span>`data-loading` | Root | `present | absent` | Mirrors external or current remote loading. |
| <span id="combobox-attribute-ccombobox-root-attributes-data-empty"></span>`data-empty` | Root | `present | absent` | Mirrors visible open empty state. |
| <span id="combobox-attribute-ccombobox-root-attributes-data-error"></span>`data-error` | Root | `present | absent` | Mirrors current remote-error state. |
| <span id="combobox-attribute-ccombobox-root-attributes-data-required"></span>`data-required` | Root | `present | absent` | Mirrors effective required state. |
| <span id="combobox-attribute-ccombobox-root-attributes-data-disabled"></span>`data-disabled` | Root | `present | absent` | Mirrors effective disabled state. |
| <span id="combobox-attribute-ccombobox-root-attributes-data-readonly"></span>`data-readonly` | Root | `present | absent` | Mirrors effective read-only state. |
| <span id="combobox-attribute-ccombobox-root-attributes-data-invalid"></span>`data-invalid` | Root | `present | absent` | Mirrors application or native invalid state. |
| <span id="combobox-attribute-ccombobox-root-attributes-data-variant"></span>`data-variant` | Root | `"outline" | "filled" | "plain"` | Mirrors effective variant. |
| <span id="combobox-attribute-ccombobox-root-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Mirrors effective size. |

</div>

#### CCombobox attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="combobox-attribute-ccombobox-option-attributes-data-value"></span>`data-value` | Option | `string` | Canonical option identity. |
| <span id="combobox-attribute-ccombobox-option-attributes-data-selected"></span>`data-selected` | Option | `present | absent` | Mirrors committed selection. |
| <span id="combobox-attribute-ccombobox-option-attributes-data-highlighted"></span>`data-highlighted` | Option | `present | absent` | Mirrors transient keyboard or pointer highlight. |
| <span id="combobox-attribute-ccombobox-option-attributes-data-disabled"></span>`data-disabled` | Option | `present | absent` | Mirrors disabled state. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CCombobox selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="combobox-selector-ccombobox-selectors-root"></span>`[data-citry-ui-part="root"]` | Root | Combobox root and `attrs` destination. |
| <span id="combobox-selector-ccombobox-selectors-control"></span>`[data-citry-ui-part="control"]` | Control | Visible input and action layout. |
| <span id="combobox-selector-ccombobox-selectors-input"></span>`[data-citry-ui-part="input"]` | Native text input | Editable query, validation owner, and `input_attrs` destination. |
| <span id="combobox-selector-ccombobox-selectors-clear"></span>`[data-citry-ui-part="clear"]` | Clear Button | Clear action. |
| <span id="combobox-selector-ccombobox-selectors-trigger"></span>`[data-citry-ui-part="trigger"]` | Trigger Button | Popup toggle. |
| <span id="combobox-selector-ccombobox-selectors-popup"></span>`[data-citry-ui-part="popup"]` | Popup | Inline popup surface. |
| <span id="combobox-selector-ccombobox-selectors-listbox"></span>`[data-citry-ui-part="listbox"]` | Listbox | ARIA listbox and scrolling collection. |
| <span id="combobox-selector-ccombobox-selectors-option"></span>`[data-citry-ui-part="option"]` | Option | Selectable plain-text item. |
| <span id="combobox-selector-ccombobox-selectors-option-label"></span>`[data-citry-ui-part="option-label"]` | Option label | Primary visible text. |
| <span id="combobox-selector-ccombobox-selectors-option-description"></span>`[data-citry-ui-part="option-description"]` | Option description | Optional supporting visible text. |
| <span id="combobox-selector-ccombobox-selectors-loading"></span>`[data-citry-ui-part="loading"]` | Loading status | Remote or external loading feedback. |
| <span id="combobox-selector-ccombobox-selectors-empty"></span>`[data-citry-ui-part="empty"]` | Empty status | Open empty-result feedback. |
| <span id="combobox-selector-ccombobox-selectors-error"></span>`[data-citry-ui-part="error"]` | Error status | Safe remote-failure feedback. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="combobox-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="combobox-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="combobox-interface-input-type-aliases-ccombobox-filter"></span>`CComboboxFilter` | `Literal["contains", "starts_with", "none"]` |
| <span id="combobox-interface-input-type-aliases-ccombobox-variant"></span>`CComboboxVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="combobox-interface-input-type-aliases-ccombobox-size"></span>`CComboboxSize` | `Literal["sm", "md", "lg"]` |

</div>

<span id="combobox-interface-ccombobox-option"></span>

#### `CComboboxOption`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="combobox-interface-ccombobox-option-value"></span>`value` | `non-empty str` | - | Stable identity and optional submitted value. |
| <span id="combobox-interface-ccombobox-option-label"></span>`label` | `non-empty str` | - | Primary escaped visible text and local filter text. |
| <span id="combobox-interface-ccombobox-option-description"></span>`description` | `str | None` | None | Optional escaped supporting text. |
| <span id="combobox-interface-ccombobox-option-disabled"></span>`disabled` | `bool` | False | Excludes the option from selection and highlight. |

</div>

<span id="combobox-interface-ccombobox-item"></span>

#### `CComboboxItem`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="combobox-interface-ccombobox-item-value"></span>`value` | `non-empty string` | - | Stable unique identity and canonical value. |
| <span id="combobox-interface-ccombobox-item-label"></span>`label` | `non-empty string` | - | Primary plain text and local filter text. |
| <span id="combobox-interface-ccombobox-item-description"></span>`description` | `string | null` | null | Optional supporting plain text. |
| <span id="combobox-interface-ccombobox-item-disabled"></span>`disabled` | `boolean` | false | Excludes the item from selection and highlight. |

</div>

<span id="combobox-interface-ccombobox-load-request"></span>

#### `CComboboxLoadRequest`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="combobox-interface-ccombobox-load-request-query"></span>`query` | `string` | - | Committed query that qualified for loading. |
| <span id="combobox-interface-ccombobox-load-request-signal"></span>`signal` | `AbortSignal` | - | Aborts when superseded, closed, reset, blocked, replaced, or removed. |
| <span id="combobox-interface-ccombobox-load-request-request-id"></span>`requestId` | `number` | - | Monotonic identity used to reject stale results even if abort is ignored. |

</div>

<span id="combobox-interface-ccombobox-loading-slot-data"></span>

#### `CComboboxLoadingSlotData`

Empty dataclass: `{}`.

<span id="combobox-interface-ccombobox-empty-slot-data"></span>

#### `CComboboxEmptySlotData`

Empty dataclass: `{}`.

<span id="combobox-interface-ccombobox-error-slot-data"></span>

#### `CComboboxErrorSlotData`

Empty dataclass: `{}`.

<span id="combobox-interface-ccombobox-value-change-detail"></span>

#### `CComboboxValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="combobox-interface-ccombobox-value-change-detail-reason"></span>`reason` | `"option" | "clear" | "input" | "reset"` | - | Canonical-value request source. |
| <span id="combobox-interface-ccombobox-value-change-detail-option"></span>`option` | `CComboboxItem | null` | - | Associated option when one caused the request. |
| <span id="combobox-interface-ccombobox-value-change-detail-query"></span>`query` | `string` | - | Query before dependent query reconciliation. |
| <span id="combobox-interface-ccombobox-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client `value` currently owns selection. |
| <span id="combobox-interface-ccombobox-value-change-detail-source"></span>`source` | `EventTarget | null` | - | Browser source associated with the request. |

</div>

<span id="combobox-interface-ccombobox-input-value-change-detail"></span>

#### `CComboboxInputValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="combobox-interface-ccombobox-input-value-change-detail-reason"></span>`reason` | `"input" | "option" | "clear" | "blur" | "reset"` | - | Query request source. |
| <span id="combobox-interface-ccombobox-input-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client `inputValue` currently owns query text. |
| <span id="combobox-interface-ccombobox-input-value-change-detail-source"></span>`source` | `EventTarget | null` | - | Browser source associated with the request. |

</div>

<span id="combobox-interface-ccombobox-open-change-detail"></span>

#### `CComboboxOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="combobox-interface-ccombobox-open-change-detail-reason"></span>`reason` | `"input" | "focus" | "trigger" | "keyboard" | "selection" | "escape" | "outside" | "blur" | "reset" | "minimum-characters"` | - | Popup request source. |
| <span id="combobox-interface-ccombobox-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client `open` currently owns requested visibility. |
| <span id="combobox-interface-ccombobox-open-change-detail-source"></span>`source` | `EventTarget | null` | - | Browser source associated with the request. |

</div>

<span id="combobox-interface-ccombobox-load-error-detail"></span>

#### `CComboboxLoadErrorDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="combobox-interface-ccombobox-load-error-detail-query"></span>`query` | `string` | - | Query associated with the failed current request. |
| <span id="combobox-interface-ccombobox-load-error-detail-request-id"></span>`requestId` | `number` | - | Failed request identity. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CCombobox translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="combobox-translation-ccombobox-translations-required"></span>`citry-ui-combobox-required` | Supplies native required-selection validity text. | `None` | `required_message` input | `i18n.bind()` updates the native validation message. |
| <span id="combobox-translation-ccombobox-translations-clear"></span>`citry-ui-combobox-clear` | Names the clear-selection control. | `None` | `clear_label` input | $c-tr updates `aria-label`. |
| <span id="combobox-translation-ccombobox-translations-open"></span>`citry-ui-combobox-open` | Names the trigger while the popup is closed. | `None` | `open_label` input | `i18n.bind()` updates the stateful `aria-label`. |
| <span id="combobox-translation-ccombobox-translations-close"></span>`citry-ui-combobox-close` | Names the trigger while the popup is open. | `None` | `close_label` input | `i18n.bind()` updates the stateful `aria-label`. |
| <span id="combobox-translation-ccombobox-translations-loading"></span>`citry-ui-combobox-loading` | Reports asynchronous option loading. | `None` | `loading_label` input or `loading` slot | $c-tr updates fallback text. |
| <span id="combobox-translation-ccombobox-translations-empty"></span>`citry-ui-combobox-empty` | Reports an empty option result. | `None` | `empty_label` input or `empty` slot | $c-tr updates fallback text. |
| <span id="combobox-translation-ccombobox-translations-error"></span>`citry-ui-combobox-error` | Reports option-loading failure. | `None` | `error_label` input or `error` slot | $c-tr updates fallback text. |

</div>