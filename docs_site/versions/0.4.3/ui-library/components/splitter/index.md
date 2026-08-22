---
title: Splitter
url: https://citry.dev/v/0.4.3/ui-library/components/splitter/
description: "Resize two or more adjacent application panels."
---
# Splitter

Use `CSplitter` when adjacent regions need user-adjustable space. Every
`CSplitterPanel` has stable identity, an accessible name, and percentage
constraints. Persist accepted sizes in application state through
`onResizeEnd` when a layout should survive navigation.

## Splitter at a glance


### Splitter at a glance

[Open the rendered preview](/v/0.4.3/ui-library/components/splitter/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitterAtAGlance(Component):
    template = """
      <c-CSplitter c-sizes="[30, 70]" variant="outline">
        <c-CSplitterPanel id="navigation" label="Navigation">
          <strong>Navigation</strong><p>Projects, files, and saved views.</p>
        </c-CSplitterPanel>
        <c-CSplitterPanel id="workspace" label="Workspace">
          <strong>Workspace</strong><p>Resize with the separator or its Arrow keys.</p>
        </c-CSplitterPanel>
      </c-CSplitter>
    """


preview = SplitterAtAGlance()
preview  # noqa: B018
````


## Resize multiple panels


### Resize three panels

[Open the rendered preview](/v/0.4.3/ui-library/components/splitter/_previews/multiple/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MultiplePanels(Component):
    template = """
      <c-CSplitter c-sizes="[20, 45, 35]" variant="soft">
        <c-CSplitterPanel id="outline" label="Document outline">Outline</c-CSplitterPanel>
        <c-CSplitterPanel id="editor" label="Document editor">Editor</c-CSplitterPanel>
        <c-CSplitterPanel id="preview" label="Document preview">Preview</c-CSplitterPanel>
      </c-CSplitter>
    """


preview = MultiplePanels()
preview  # noqa: B018
````


## Stack and nest Splitters


### Stack and nest Splitters

[Open the rendered preview](/v/0.4.3/ui-library/components/splitter/_previews/vertical-nested/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VerticalNested(Component):
    template = """
      <c-CSplitter orientation="vertical" c-sizes="[35, 65]" variant="outline">
        <c-CSplitterPanel id="header" label="Header preview">Header preview</c-CSplitterPanel>
        <c-CSplitterPanel id="workbench" label="Workbench">
          <c-CSplitter c-sizes="[40, 60]" size="sm">
            <c-CSplitterPanel id="source" label="Source">Source</c-CSplitterPanel>
            <c-CSplitterPanel id="result" label="Result">Result</c-CSplitterPanel>
          </c-CSplitter>
        </c-CSplitterPanel>
      </c-CSplitter>
    """


preview = VerticalNested()
preview  # noqa: B018
````


## Constrain keyboard resizing

Arrow keys move by `keyboard_step` percentage points, Shift uses four times
the step, and Home or End reaches the adjacent pair constraint.


### Constrain panel sizes

[Open the rendered preview](/v/0.4.3/ui-library/components/splitter/_previews/constraints-keyboard/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConstrainedSplitter(Component):
    template = """
      <c-CSplitter c-sizes="[35, 65]" c-keyboard_step="5" variant="outline">
        <c-CSplitterPanel id="tools" label="Tools" c-min_size="20" c-max_size="50">
          Focus the separator. Arrow keys move 5%; Shift moves 20%; Home and End use the limits.
        </c-CSplitterPanel>
        <c-CSplitterPanel id="canvas" label="Canvas" c-min_size="40">Canvas</c-CSplitterPanel>
      </c-CSplitter>
    """


preview = ConstrainedSplitter()
preview  # noqa: B018
````


## Control and persist sizes

Client `sizes` is controlled while supplied. The owner accepts resize
requests by updating the vector and can persist the final vector from
`onResizeEnd`.


### Control Splitter sizes

[Open the rendered preview](/v/0.4.3/ui-library/components/splitter/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledSplitter(Component):
    template = """
      <section x-data="{ sizes: [25, 75], saved: '' }">
        <c-CSplitter
          c-sizes="[25, 75]"
          $c-props="{
            sizes,
            onResize: (next) => sizes = next,
            onResizeEnd: (next) => saved = next.map(value => value.toFixed(0)).join(' / ')
          }"
        >
          <c-CSplitterPanel id="filters" label="Filters">Filters</c-CSplitterPanel>
          <c-CSplitterPanel id="results" label="Results">Results</c-CSplitterPanel>
        </c-CSplitter>
        <output x-text="saved ? `Saved: ${saved}` : 'Resize to save the layout'"></output>
      </section>
    """


preview = ControlledSplitter()
preview  # noqa: B018
````


## Disable resizing


### Disable Splitter

[Open the rendered preview](/v/0.4.3/ui-library/components/splitter/_previews/disabled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisabledSplitter(Component):
    template = """
      <fieldset disabled>
        <legend>Locked layout</legend>
        <c-CSplitter c-sizes="[40, 60]" variant="soft">
          <c-CSplitterPanel id="summary" label="Summary">Summary</c-CSplitterPanel>
          <c-CSplitterPanel id="details" label="Details">Details</c-CSplitterPanel>
        </c-CSplitter>
      </fieldset>
    """


preview = DisabledSplitter()
preview  # noqa: B018
````


## Customize Splitter


### Customize Splitter

[Open the rendered preview](/v/0.4.3/ui-library/components/splitter/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedSplitter(Component):
    template = """
      <div class="brand-splitter">
        <style>
          .brand-splitter {
            --cui-splitter-radius: 1.25rem;
            --cui-splitter-handle-active-color: rebeccapurple;
            --cui-splitter-background: color-mix(in srgb, rebeccapurple 7%, Canvas);
          }
          .brand-splitter [data-citry-ui-part="panel"] { overflow-wrap: anywhere; }
        </style>
        <c-CSplitter c-sizes="[38, 62]" variant="outline" size="lg">
          <c-CSplitterPanel id="index" label="Index">Branded index</c-CSplitterPanel>
          <c-CSplitterPanel id="article" label="Article">Branded article</c-CSplitterPanel>
        </c-CSplitter>
      </div>
    """


preview = CustomizedSplitter()
preview  # noqa: B018
````


## Accessibility and behavior

Each resize handle is a focusable ARIA separator with its current percentage,
allowed range, physical orientation, and the IDs of its adjacent panels.
Side-by-side layouts use Left and Right; stacked layouts use Up and Down.
Pointer and keyboard interaction change only the adjacent pair, preserving its
combined size. Controls inside panels retain their ordinary form behavior.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CSplitter server inputs

Server inputs are passed in a template through `<c-CSplitter ... />` or in Python through
`CSplitter(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="splitter-input-csplitter-server-inputs-sizes"></span>`sizes` | `Sequence[int | float] | None` | `None` | Sets initial percentage sizes totaling 100; omission divides space equally. |
| <span id="splitter-input-csplitter-server-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CSplitterOrientation`](#splitter-interface-csplitter-orientation)) | `"horizontal"` | Places panels side by side or stacked. |
| <span id="splitter-input-csplitter-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables every resize handle. |
| <span id="splitter-input-csplitter-server-inputs-keyboard-step"></span>`keyboard_step` | `float` | `2` | Sets Arrow-key movement in percentage points. |
| <span id="splitter-input-csplitter-server-inputs-variant"></span>`variant` | `"plain" | "soft" | "outline"` ([`CSplitterVariant`](#splitter-interface-csplitter-variant)) | `"plain"` | Selects surface treatment. |
| <span id="splitter-input-csplitter-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CSplitterSize`](#splitter-interface-csplitter-size)) | `"md"` | Selects handle geometry. |
| <span id="splitter-input-csplitter-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#splitter-interface-csplitter-class-value)) | `None` | Adds root classes. |
| <span id="splitter-input-csplitter-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#splitter-interface-csplitter-style-value)) | `None` | Adds root inline styles. |
| <span id="splitter-input-csplitter-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted root attributes without replacing owned structure state or runtime. |

</div>

#### CSplitter client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CSplitter />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="splitter-input-csplitter-client-inputs-sizes"></span>`sizes` | `number[] | null` | Uses uncontrolled committed sizes. | Controls percentages while supplied; null releases control. |
| <span id="splitter-input-csplitter-client-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CSplitterOrientation`](#splitter-interface-csplitter-orientation)) | Uses the server value. | Reactively changes layout and keyboard axis. |
| <span id="splitter-input-csplitter-client-inputs-disabled"></span>`disabled` | `bool` | Uses the server value. | Reactively disables resizing. |
| <span id="splitter-input-csplitter-client-inputs-keyboard-step"></span>`keyboardStep` | `number` | Uses the server value. | Reactively changes Arrow-key movement. |
| <span id="splitter-input-csplitter-client-inputs-variant"></span>`variant` | `"plain" | "soft" | "outline"` ([`CSplitterVariant`](#splitter-interface-csplitter-variant)) | Uses the server value. | Reactively changes surface treatment. |
| <span id="splitter-input-csplitter-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CSplitterSize`](#splitter-interface-csplitter-size)) | Uses the server value. | Reactively changes handle geometry. |
| <span id="splitter-input-csplitter-client-inputs-on-resize-start"></span>`onResizeStart` | `((detail: CSplitterResizeDetail) => void) | undefined` | No component callback runs. | Receives the beginning of a pointer or keyboard transaction. |
| <span id="splitter-input-csplitter-client-inputs-on-resize"></span>`onResize` | `((sizes: number[], detail: CSplitterResizeDetail) => void) | undefined` | No component callback runs. | Receives each valid adjacent-pair resize request. |
| <span id="splitter-input-csplitter-client-inputs-on-resize-end"></span>`onResizeEnd` | `((sizes: number[], detail: CSplitterResizeDetail) => void) | undefined` | No component callback runs. | Receives the settled end of a resize transaction. |

</div>

#### CSplitterPanel server inputs

Server inputs are passed in a template through `<c-CSplitterPanel ... />` or in Python
through `CSplitterPanel(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="splitter-input-csplitter-panel-server-inputs-id"></span>`id` | `str` | required | Supplies stable panel identity and relationship targets. |
| <span id="splitter-input-csplitter-panel-server-inputs-label"></span>`label` | `str` | required | Supplies the panel and adjacent separator accessible names. |
| <span id="splitter-input-csplitter-panel-server-inputs-min-size"></span>`min_size` | `float` | `10` | Sets the minimum percentage. |
| <span id="splitter-input-csplitter-panel-server-inputs-max-size"></span>`max_size` | `float` | `100` | Sets the maximum percentage. |
| <span id="splitter-input-csplitter-panel-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#splitter-interface-csplitter-class-value)) | `None` | Adds classes to the concrete panel. |
| <span id="splitter-input-csplitter-panel-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#splitter-interface-csplitter-style-value)) | `None` | Adds inline styles to the concrete panel. |
| <span id="splitter-input-csplitter-panel-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted panel attributes without replacing owned semantics identity or sizing. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CSplitter slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="splitter-slot-csplitter-slots-default"></span>`default` | yes | `{}` ([`CSplitterDefaultSlotData`](#splitter-interface-csplitter-default-slot-data)) | None. Requires two or more direct CSplitterPanel declarations. |

</div>

#### CSplitterPanel slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="splitter-slot-csplitter-panel-slots-default"></span>`default` | yes | `{id, index, size, is_first, is_last}` ([`CSplitterPanelDefaultSlotData`](#splitter-interface-csplitter-panel-default-slot-data)) | None. Supplies panel content. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CSplitter events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="splitter-event-csplitter-events-resize-start"></span>`onResizeStart` | `(detail: CSplitterResizeDetail) => void` ([`CSplitterResizeDetail`](#splitter-interface-csplitter-resize-detail)) | Pointerdown or an accepted keyboard resize. | `{sizes, previousSizes, handleIndex, controlled, source, sourceEvent}` ([`CSplitterResizeDetail`](#splitter-interface-csplitter-resize-detail)) | Begins a resize transaction. |
| <span id="splitter-event-csplitter-events-resize"></span>`onResize` | `(sizes: number[], detail: CSplitterResizeDetail) => void` ([`CSplitterResizeDetail`](#splitter-interface-csplitter-resize-detail)) | Each accepted pointer or keyboard resize request. | `{sizes, previousSizes, handleIndex, controlled, source, sourceEvent}` ([`CSplitterResizeDetail`](#splitter-interface-csplitter-resize-detail)) | Commits immediately when uncontrolled and waits for owner acceptance when controlled. |
| <span id="splitter-event-csplitter-events-resize-end"></span>`onResizeEnd` | `(sizes: number[], detail: CSplitterResizeDetail) => void` ([`CSplitterResizeDetail`](#splitter-interface-csplitter-resize-detail)) | Pointerup pointercancel disability or an accepted keyboard resize. | `{sizes, previousSizes, handleIndex, controlled, source, sourceEvent}` ([`CSplitterResizeDetail`](#splitter-interface-csplitter-resize-detail)) | Ends the transaction and is the persistence composition point. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CSplitter CSS variables

Apply these variables to `CSplitter` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="splitter-css-csplitter-css-variables-cui-splitter-min-block-size"></span>`--cui-splitter-min-block-size` | `length` | Minimum root block size. | `12rem` |
| <span id="splitter-css-csplitter-css-variables-cui-splitter-radius"></span>`--cui-splitter-radius` | `length` | Root corner radius. | `0.75rem` |
| <span id="splitter-css-csplitter-css-variables-cui-splitter-background"></span>`--cui-splitter-background` | `color` | Root background. | `plain and outline transparent; soft subtle CanvasText mix` |
| <span id="splitter-css-csplitter-css-variables-cui-splitter-border-color"></span>`--cui-splitter-border-color` | `color` | Outline root border. | `light #d0d5dd; dark #535862` |
| <span id="splitter-css-csplitter-css-variables-cui-splitter-handle-size"></span>`--cui-splitter-handle-size` | `length` | Handle hit-area thickness. | `sm 0.5rem; md 0.75rem; lg 1rem` |
| <span id="splitter-css-csplitter-css-variables-cui-splitter-handle-color"></span>`--cui-splitter-handle-color` | `color` | Inactive line and grip. | `light #98a2b3; dark #717680` |
| <span id="splitter-css-csplitter-css-variables-cui-splitter-handle-active-color"></span>`--cui-splitter-handle-active-color` | `color` | Hover and active grip. | `light #175cd3; dark #84adff` |
| <span id="splitter-css-csplitter-css-variables-cui-splitter-focus-color"></span>`--cui-splitter-focus-color` | `color` | Keyboard focus outline. | `Highlight` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CSplitter attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="splitter-attribute-csplitter-attributes-role"></span>`role` | Panel or separator div | `group | separator` | Gives panels and resize handles their owned semantics. |
| <span id="splitter-attribute-csplitter-attributes-tabindex"></span>`tabindex` | Separator div | `0 | -1` | Includes enabled handles in Tab order and removes disabled handles. |
| <span id="splitter-attribute-csplitter-attributes-aria-label"></span>`aria-label` | Panel or separator div | `string` | Names each panel and each adjacent-pair handle. |
| <span id="splitter-attribute-csplitter-attributes-aria-disabled"></span>`aria-disabled` | Separator div | `true | false` | Reflects effective resize availability. |
| <span id="splitter-attribute-csplitter-attributes-data-orientation"></span>`data-orientation` | Root div | `horizontal | vertical` | Mirrors effective layout. |
| <span id="splitter-attribute-csplitter-attributes-data-disabled"></span>`data-disabled` | Root or handle | `present-or-absent` | Reflects effective resizing unavailability. |
| <span id="splitter-attribute-csplitter-attributes-data-resizing"></span>`data-resizing` | Root div | `present-or-absent` | Present during pointer resizing. |
| <span id="splitter-attribute-csplitter-attributes-data-variant"></span>`data-variant` | Root div | `plain | soft | outline` | Mirrors effective surface treatment. |
| <span id="splitter-attribute-csplitter-attributes-data-size"></span>`data-size` | Root div | `sm | md | lg` | Mirrors effective geometry. |
| <span id="splitter-attribute-csplitter-attributes-data-panel-id"></span>`data-panel-id` | Panel div | `string` | Exposes canonical panel identity. |
| <span id="splitter-attribute-csplitter-attributes-data-index"></span>`data-index` | Panel div | `nonnegative-integer-string` | Exposes settled order. |
| <span id="splitter-attribute-csplitter-attributes-data-size-percent"></span>`data-size-percent` | Panel div | `number-string` | Mirrors effective percentage. |
| <span id="splitter-attribute-csplitter-attributes-data-min-size"></span>`data-min-size` | Panel div | `number-string` | Exposes minimum percentage. |
| <span id="splitter-attribute-csplitter-attributes-data-max-size"></span>`data-max-size` | Panel div | `number-string` | Exposes maximum percentage. |
| <span id="splitter-attribute-csplitter-attributes-data-handle-index"></span>`data-handle-index` | Separator div | `nonnegative-integer-string` | Identifies the adjacent pair. |
| <span id="splitter-attribute-csplitter-attributes-data-active"></span>`data-active` | Separator div | `present-or-absent` | Present during its pointer transaction. |
| <span id="splitter-attribute-csplitter-attributes-aria-controls"></span>`aria-controls` | Separator div | `IDREF-list` | Identifies both adjacent panels. |
| <span id="splitter-attribute-csplitter-attributes-aria-orientation"></span>`aria-orientation` | Separator div | `vertical | horizontal` | Exposes physical separator orientation. |
| <span id="splitter-attribute-csplitter-attributes-aria-valuemin"></span>`aria-valuemin` | Separator div | `number-string` | Exposes pair minimum. |
| <span id="splitter-attribute-csplitter-attributes-aria-valuemax"></span>`aria-valuemax` | Separator div | `number-string` | Exposes pair maximum. |
| <span id="splitter-attribute-csplitter-attributes-aria-valuenow"></span>`aria-valuenow` | Separator div | `number-string` | Exposes the preceding panel percentage. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CSplitter selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="splitter-selector-csplitter-selectors-part-splitter"></span>`[data-citry-ui-part="splitter"]` | Root div | Stable root and attrs destination. |
| <span id="splitter-selector-csplitter-selectors-part-panel"></span>`[data-citry-ui-part="panel"]` | Panel div | Stable content and panel attrs destination. |
| <span id="splitter-selector-csplitter-selectors-part-handle"></span>`[data-citry-ui-part="handle"]` | Separator div | Stable focusable resize control. |
| <span id="splitter-selector-csplitter-selectors-part-handle-line"></span>`[data-citry-ui-part="handle-line"]` | Decorative span | Stable separator line. |
| <span id="splitter-selector-csplitter-selectors-part-handle-grip"></span>`[data-citry-ui-part="handle-grip"]` | Decorative span | Stable resize affordance. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="splitter-interface-csplitter-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="splitter-interface-csplitter-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |
| <span id="splitter-interface-csplitter-orientation"></span>`CSplitterOrientation` | `Literal["horizontal", "vertical"]` |
| <span id="splitter-interface-csplitter-variant"></span>`CSplitterVariant` | `Literal["plain", "soft", "outline"]` |
| <span id="splitter-interface-csplitter-size"></span>`CSplitterSize` | `Literal["sm", "md", "lg"]` |
| <span id="splitter-interface-csplitter-resize-source"></span>`CSplitterResizeSource` | `Literal["pointer", "keyboard"]` |

</div>

<span id="splitter-interface-csplitter-default-slot-data"></span>

#### `CSplitterDefaultSlotData`

Empty dataclass: `{}`.

<span id="splitter-interface-csplitter-panel-default-slot-data"></span>

#### `CSplitterPanelDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="splitter-interface-csplitter-panel-default-slot-data-id"></span>`id` | `str` | - | Canonical panel identity. |
| <span id="splitter-interface-csplitter-panel-default-slot-data-index"></span>`index` | `int` | - | Zero-based settled panel index. |
| <span id="splitter-interface-csplitter-panel-default-slot-data-size"></span>`size` | `float` | - | Server-rendered percentage. |
| <span id="splitter-interface-csplitter-panel-default-slot-data-is-first"></span>`is_first` | `bool` | - | Whether this is the first panel. |
| <span id="splitter-interface-csplitter-panel-default-slot-data-is-last"></span>`is_last` | `bool` | - | Whether this is the last panel. |

</div>

<span id="splitter-interface-csplitter-resize-detail"></span>

#### `CSplitterResizeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="splitter-interface-csplitter-resize-detail-sizes"></span>`sizes` | `number[]` | - | Requested effective vector. |
| <span id="splitter-interface-csplitter-resize-detail-previous-sizes"></span>`previousSizes` | `number[]` | - | Vector before this transaction step. |
| <span id="splitter-interface-csplitter-resize-detail-handle-index"></span>`handleIndex` | `int` | - | Zero-based changed separator index. |
| <span id="splitter-interface-csplitter-resize-detail-controlled"></span>`controlled` | `bool` | - | Whether client sizes currently controls state. |
| <span id="splitter-interface-csplitter-resize-detail-source"></span>`source` | `"pointer" | "keyboard"` ([`CSplitterResizeSource`](#splitter-interface-csplitter-resize-source)) | - | Interaction source. |
| <span id="splitter-interface-csplitter-resize-detail-source-event"></span>`sourceEvent` | `Event` | - | Native PointerEvent or KeyboardEvent. |

</div>

### Translation keys

-