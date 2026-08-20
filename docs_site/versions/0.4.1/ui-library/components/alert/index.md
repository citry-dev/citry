---
title: Alert
url: https://citry.dev/v/0.4.1/ui-library/components/alert/
description: "Present persistent feedback with clear intent, optional actions, and deliberate announcement urgency."
---
# Alert

Use `CAlert` for persistent feedback about a page, section, action, or system
condition. Alert owns presentation and optional announcement semantics. Your
application owns visibility, dismissal, focus recovery, and retry behavior.

## Alert at a glance

Intent changes both color and icon shape, so meaning never depends on color
alone.


### Alert at a glance

[Open the rendered preview](/v/0.4.1/ui-library/components/alert/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertAtAGlance(Component):
    template = """
      <section class="alert-glance" aria-label="Observatory alerts">
        <c-CAlert intent="info">
          <c-fill name="title">Meteor shower tonight</c-fill>
          <c-fill name="default">Peak activity begins near 23:10.</c-fill>
        </c-CAlert>
        <c-CAlert intent="success">
          <c-fill name="title">Telescope aligned</c-fill>
          <c-fill name="default">Tracking error is below 0.2 arcseconds.</c-fill>
        </c-CAlert>
        <c-CAlert intent="warn">
          <c-fill name="title">Cloud bank approaching</c-fill>
          <c-fill name="default">The western horizon may close after midnight.</c-fill>
        </c-CAlert>
        <c-CAlert intent="error">
          <c-fill name="title">Camera link lost</c-fill>
          <c-fill name="default">Reconnect before starting the next exposure.</c-fill>
        </c-CAlert>
      </section>
    """

    css = """
      :where(.alert-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 0.875rem;
        max-width: 72rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertAtAGlance()

preview  # noqa: B018
````


## Compose an Alert

Write a message in the default slot. Add `title` when a condition needs a
short summary.


### Compose Alert content

[Open the rendered preview](/v/0.4.1/ui-library/components/alert/_previews/basic-alert/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicAlerts(Component):
    template = """
      <section class="basic-alerts" aria-label="Basic Alert anatomy">
        <c-CAlert>
          Comet viewing begins at 22:40.
        </c-CAlert>
        <c-CAlert intent="success">
          <c-fill name="title">Calibration complete</c-fill>
          <c-fill name="default">
            The spectrograph is ready for the first target.
          </c-fill>
        </c-CAlert>
      </section>
    """

    css = """
      :where(.basic-alerts) {
        display: grid;
        gap: 0.875rem;
        max-width: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = BasicAlerts()

preview  # noqa: B018
````



```citry-html
<c-CAlert intent="warn">
  <c-fill name="title">
    Cloud cover approaching
  </c-fill>
  <c-fill name="default">
    The western ridge may disappear after midnight.
  </c-fill>
</c-CAlert>
```


Compose the same Alert in Python:


```python
from citry_ui import CAlert

forecast = CAlert(
    intent="warn",
    slots={
        "title": "Cloud cover approaching",
        "default": "The western ridge may disappear after midnight.",
    },
)
```


At least one of `title` or `default` is required. Alert does not choose a
heading rank; put the appropriate native heading in the title slot when the
Alert introduces a document section.

## Choose visual meaning

Use `info` for neutral context, `success` for completion, `warn` for a
condition that needs attention, and `error` for failure.


### Compare Alert intents

[Open the rendered preview](/v/0.4.1/ui-library/components/alert/_previews/intents/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertIntents(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="alert-intents" aria-label="Alert intents">
        <c-for each="item in alerts">
          <c-CAlert c-intent="item[0]">
            <c-fill name="title">{{ item[1] }}</c-fill>
            <c-fill name="default">{{ item[2] }}</c-fill>
          </c-CAlert>
        </c-for>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "alerts": (
                ("info", "Night plan ready", "Six targets fit the darkness window."),
                ("success", "Guide star acquired", "Tracking has settled on Vega."),
                ("warn", "Humidity rising", "Review the dome limit before continuing."),
                ("error", "Dome drive stopped", "Close the shutter manually."),
            )
        }

    css = """
      :where(.alert-intents) {
        display: grid;
        gap: 0.75rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertIntents()

preview  # noqa: B018
````


`intent` is visual meaning, not urgency. Configure announcements separately.

## Choose emphasis

`soft` is the quiet default. Use `solid` for stronger prominence and `outline`
when the surrounding surface should remain visible.


### Compare Alert variants

[Open the rendered preview](/v/0.4.1/ui-library/components/alert/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertVariants(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="alert-variants" aria-label="Alert variants">
        <c-for each="variant in variants">
          <c-CAlert intent="warn" c-variant="variant[0]">
            <c-fill name="title">{{ variant[1] }} warning</c-fill>
            <c-fill name="default">
              High cirrus may reduce contrast on faint galaxies.
            </c-fill>
          </c-CAlert>
        </c-for>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"variants": (("soft", "Soft"), ("solid", "Solid"), ("outline", "Outline"))}

    css = """
      :where(.alert-variants) {
        display: grid;
        gap: 0.75rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertVariants()

preview  # noqa: B018
````


## Choose size

`sm`, `md`, and `lg` change spacing, text scale, icon geometry, and action gap.


### Compare Alert sizes

[Open the rendered preview](/v/0.4.1/ui-library/components/alert/_previews/sizes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="alert-sizes" aria-label="Alert sizes">
        <c-for each="size in sizes">
          <c-CAlert c-size="size[0]">
            <c-fill name="title">{{ size[1] }} Alert</c-fill>
            <c-fill name="default">The northern camera is ready.</c-fill>
          </c-CAlert>
        </c-for>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"sizes": (("sm", "Small"), ("md", "Medium"), ("lg", "Large"))}

    css = """
      :where(.alert-sizes) {
        display: grid;
        gap: 0.75rem;
        max-width: 48rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertSizes()

preview  # noqa: B018
````


## Configure icons

The default icon follows intent. Set `icon=False` to hide it or pass a
registered `icon_name` for a fixed decorative glyph.


### Use automatic, hidden, and fixed icons

[Open the rendered preview](/v/0.4.1/ui-library/components/alert/_previews/icons/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertIcons(Component):
    template = """
      <section class="alert-icons" aria-label="Alert icons">
        <c-CAlert intent="success">
          Automatic success icon follows intent.
        </c-CAlert>
        <c-CAlert intent="warn" c-icon="False">
          Icon hidden; the message still carries the meaning.
        </c-CAlert>
        <c-CAlert icon_name="star" variant="outline">
          Fixed registered star icon stays constant when intent changes.
        </c-CAlert>
      </section>
    """

    css = """
      :where(.alert-icons) {
        display: grid;
        gap: 0.75rem;
        max-width: 50rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertIcons()

preview  # noqa: B018
````


Icons are hidden from the accessibility tree. Put essential meaning in the
title or message.

## Add actions

Use the `actions` slot for links, Buttons, menus, or other related controls.
`actions_label` gives the controls a named group without adding another layout
wrapper.


### Add actions and own dismissal

[Open the rendered preview](/v/0.4.1/ui-library/components/alert/_previews/actions/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertActions(Component):
    template = """
      <section
        class="alert-actions-demo"
        x-data
        x-init="Alpine.store('alertActions', {visible: true})"
      >
        <div
          x-show="$store.alertActions.visible"
          x-bind:inert="!$store.alertActions.visible"
        >
          <c-CAlert
            intent="warn"
            actions_label="Cloud-cover actions"
          >
            <c-fill name="title">Cloud cover approaching</c-fill>
            <c-fill name="default">
              The western ridge may disappear after midnight.
            </c-fill>
            <c-fill name="actions">
              <c-CButton
                href="#forecast"
                size="sm"
                variant="outline"
              >
                Open forecast
              </c-CButton>
              <c-CButton
                size="sm"
                intent="neutral"
                @click="$store.alertActions.visible = false;
                  Alpine.nextTick(() => document
                    .getElementById('restore-observatory-notice')
                    .focus())"
              >
                Dismiss
              </c-CButton>
            </c-fill>
          </c-CAlert>
        </div>
        <button
          id="restore-observatory-notice"
          x-show="!$store.alertActions.visible"
          type="button"
          @click="$store.alertActions.visible = true"
        >
          Restore observatory notice
        </button>
      </section>
    """

    css = """
      :where(.alert-actions-demo) {
        display: grid;
        gap: 0.75rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.alert-actions-demo > button) {
        justify-self: start;
        padding: 0.5rem 0.75rem;
        border: 1px solid light-dark(#8da1bb, #687b97);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
        cursor: pointer;
      }
    """


preview = AlertActions()

preview  # noqa: B018
````


Alert has no close input or callback. The state owner hides or removes it and
chooses where focus goes when a focused action disappears. The example retains
the Alert with `x-show`; use a server rerender when dismissal must remove it.

## Configure Alert in the browser

Server inputs are passed in Python through `<c-CAlert ... />` attributes or a
`CAlert(...)` composition call. Client inputs are passed in the browser through
`$c-props="{...}"`.


### Configure Alert

[Open the rendered preview](/v/0.4.1/ui-library/components/alert/_previews/configure/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConfigureAlert(Component):
    template = """
      <section
        class="alert-configurator"
        x-data="{
          intent: 'info',
          variant: 'soft',
          size: 'md',
          announce: 'off',
          icon: true,
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Live configuration</p>
          <h2>Observation status</h2>
        </header>
        <c-CAlert
          $c-props="{
            intent,
            variant,
            size,
            announce,
            icon,
          }"
        >
          <c-fill name="title">Tracking update</c-fill>
          <c-fill name="default">
            The guide camera is following the selected star.
          </c-fill>
        </c-CAlert>
      </section>
    """

    css = """
      :where(.alert-configurator) {
        display: grid;
        gap: 1.25rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.alert-configurator h2, .alert-configurator p) {
        margin: 0;
      }

      :where(.alert-configurator header p) {
        color: light-dark(#3758a6, #9db7ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview_controls = (
    {
        "name": "intent",
        "label": "Intent",
        "type": "select",
        "default": "info",
        "options": (
            ("info", "Info"),
            ("success", "Success"),
            ("warn", "Warn"),
            ("error", "Error"),
        ),
    },
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "soft",
        "options": (("soft", "Soft"), ("solid", "Solid"), ("outline", "Outline")),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "announce",
        "label": "Announcement",
        "type": "select",
        "default": "off",
        "options": (("off", "Off"), ("polite", "Polite"), ("assertive", "Assertive")),
    },
    {"name": "icon", "label": "Show icon", "type": "checkbox", "default": True},
)

preview = ConfigureAlert()

preview  # noqa: B018
````


Client `intent`, `variant`, `size`, `announce`, and `icon` values override the
server fallback. Omit a value to return to that fallback. Invalid values never
acquire ownership.

## Choose announcement urgency

The default `announce="off"` adds no live-region role. Use `polite` for a
nonblocking update and `assertive` only when attention is immediate.


### Compare announcement modes

[Open the rendered preview](/v/0.4.1/ui-library/components/alert/_previews/announcements/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertAnnouncements(Component):
    template = """
      <section class="alert-announcements" aria-label="Alert announcement modes">
        <c-CAlert announce="off">
          Static observing instructions use no live-region role.
        </c-CAlert>
        <c-CAlert announce="polite" intent="success">
          <c-fill name="title">Exposure saved</c-fill>
          <c-fill name="default">Use polite urgency for a nonblocking update.</c-fill>
        </c-CAlert>
        <c-CAlert announce="assertive" intent="error">
          <c-fill name="title">Shutter obstruction</c-fill>
          <c-fill name="default">Use assertive urgency only when attention is immediate.</c-fill>
        </c-CAlert>
      </section>
    """

    css = """
      :where(.alert-announcements) {
        display: grid;
        gap: 0.75rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertAnnouncements()

preview  # noqa: B018
````


Alert applies `status` or `alert` to the content wrapper, never the action
group. It does not guarantee that a populated Alert inserted in one operation
will be announced by every browser and assistive-technology pair. A queued,
reliable announcer needs a persistent owner.

## Customize the theme

Override public variables on an ancestor or one Alert. Use stable part
selectors for targeted rules.


### Theme observatory Alerts

[Open the rendered preview](/v/0.4.1/ui-library/components/alert/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertCustomization(Component):
    template = """
      <section class="alert-themes" aria-label="Alert theme customization">
        <article class="alert-themes__solar">
          <h2>Solar observatory</h2>
          <c-CAlert intent="warn">
            Coronal imaging pauses during the calibration sweep.
          </c-CAlert>
        </article>
        <article class="alert-themes__radio">
          <h2>Radio observatory</h2>
          <c-CAlert class_="radio-success" intent="success" variant="outline">
            The receiver array is synchronized.
          </c-CAlert>
        </article>
      </section>
    """

    css = """
      :where(.alert-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 60rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.alert-themes article) {
        display: grid;
        gap: 0.75rem;
      }

      :where(.alert-themes h2) {
        margin: 0;
        font-size: 1rem;
      }

      :where(.alert-themes__solar) {
        --cui-alert-background: light-dark(#fff8df, #30270b);
        --cui-alert-border-color: light-dark(#d99d13, #ffd166);
        --cui-alert-icon-color: light-dark(#9a6700, #ffd166);
      }

      :where(.radio-success[data-citry-ui-part="alert"]) {
        --cui-alert-border-color: light-dark(#6d28d9, #c4b5fd);
        --cui-alert-icon-color: light-dark(#6d28d9, #c4b5fd);
        --cui-alert-radius: 1.25rem;
      }
    """


preview = AlertCustomization()

preview  # noqa: B018
````


`class_`, `style`, and `attrs` target the root. `actions_attrs` targets the
optional action wrapper. Unlayered consumer CSS overrides Citry UI defaults;
named layers follow the site-wide layer-order contract.

## Accessibility and trust

Alert never moves focus, adds a Tab stop, traps keyboard input, or handles
Escape. Authored actions keep native DOM and Tab order. Visual intent changes
icon shape as well as color.

Title and message content use ordinary Citry escaping. `actions_label` is
converted to plain text before attribute rendering. Registered icon names use
the packaged allowlist. `attrs`, `actions_attrs`, `class_`, and `style` remain
trusted authoring surfaces for unowned values; Alert rejects attributes and
directives that could replace its children, semantics, focus ownership,
public mirrors, or runtime markers.

## API reference

### Inputs

#### CAlert server inputs

Server inputs are passed in a template through `<c-CAlert ... />` or in Python through
`CAlert(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 9rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="alert-input-calert-server-inputs-intent"></span>`intent` | `"info" | "success" | "warn" | "error"` ([`CAlertIntent`](#alert-interface-alert-intent)) | `"info"` | Selects visual meaning, colors, and the automatic icon without choosing announcement urgency. |
| <span id="alert-input-calert-server-inputs-variant"></span>`variant` | `"soft" | "solid" | "outline"` ([`CAlertVariant`](#alert-interface-alert-variant)) | `"soft"` | Selects quiet, strong, or transparent visual emphasis. |
| <span id="alert-input-calert-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CAlertSize`](#alert-interface-alert-size)) | `"md"` | Selects spacing, text scale, icon size, and action gap. |
| <span id="alert-input-calert-server-inputs-announce"></span>`announce` | `"off" | "polite" | "assertive"` ([`CAlertAnnounce`](#alert-interface-alert-announce)) | `"off"` | Applies no role, `status`, or `alert` to the content wrapper. It does not guarantee delivery by assistive technology. |
| <span id="alert-input-calert-server-inputs-icon"></span>`icon` | `bool` | `True` | Shows or hides the decorative automatic or fixed icon. |
| <span id="alert-input-calert-server-inputs-icon-name"></span>`icon_name` | `CIconName | None` ([`CIconName`](#alert-interface-alert-icon-name)) | `None` | Uses one registered fixed glyph. Omit it to let the icon follow intent. |
| <span id="alert-input-calert-server-inputs-actions-label"></span>`actions_label` | `non-whitespace str | None` | `None` | Names the optional action group and emits its owned `group` role; requires the actions slot. |
| <span id="alert-input-calert-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#alert-interface-alert-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="alert-input-calert-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#alert-interface-alert-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="alert-input-calert-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned root attributes. Alert semantics, children, structural Alpine directives, focus ownership, public mirrors, and runtime namespaces are reserved. |
| <span id="alert-input-calert-server-inputs-actions-attrs"></span>`actions_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned action-wrapper attributes. Group naming, focus, live-region, children, structural or initialization-suppressing directives, and runtime ownership are reserved; a nonempty mapping requires actions. |

</div>

#### CAlert client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CAlert />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 14rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="alert-input-calert-client-inputs-intent"></span>`intent` | `"info" | "success" | "warn" | "error"` ([`CAlertIntent`](#alert-interface-alert-intent)) | Uses the server input. | Controls visual meaning, colors, and the automatic icon. |
| <span id="alert-input-calert-client-inputs-variant"></span>`variant` | `"soft" | "solid" | "outline"` ([`CAlertVariant`](#alert-interface-alert-variant)) | Uses the server input. | Controls visual emphasis. |
| <span id="alert-input-calert-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CAlertSize`](#alert-interface-alert-size)) | Uses the server input. | Controls geometry and text scale. |
| <span id="alert-input-calert-client-inputs-announce"></span>`announce` | `"off" | "polite" | "assertive"` ([`CAlertAnnounce`](#alert-interface-alert-announce)) | Uses the server input. | Controls the content wrapper's announcement role. |
| <span id="alert-input-calert-client-inputs-icon"></span>`icon` | `boolean` | Uses the server input. | Controls decorative icon visibility. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CAlert slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="alert-slot-calert-slots-title"></span>`title` | no | `{}` ([`CAlertTitleSlotData`](#alert-interface-alert-title-slot-data)) | No title wrapper. At least title or default is required. |
| <span id="alert-slot-calert-slots-default"></span>`default` | no | `{}` ([`CAlertDefaultSlotData`](#alert-interface-alert-default-slot-data)) | No message wrapper. At least title or default is required. |
| <span id="alert-slot-calert-slots-actions"></span>`actions` | no | `{}` ([`CAlertActionsSlotData`](#alert-interface-alert-actions-slot-data)) | No action group. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CAlert CSS variables

Apply these variables to `CAlert` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="alert-css-calert-css-variables-cui-alert-background"></span>`--cui-alert-background` | `color` | Root background. | `Variant- and intent-derived color.` |
| <span id="alert-css-calert-css-variables-cui-alert-foreground"></span>`--cui-alert-foreground` | `color` | Title, message, and action foreground. | `Variant- and intent-derived color.` |
| <span id="alert-css-calert-css-variables-cui-alert-border-color"></span>`--cui-alert-border-color` | `color` | Root boundary color. | `Variant- and intent-derived color.` |
| <span id="alert-css-calert-css-variables-cui-alert-icon-color"></span>`--cui-alert-icon-color` | `color` | Automatic or fixed icon foreground. | `Intent color or solid foreground.` |
| <span id="alert-css-calert-css-variables-cui-alert-border-width"></span>`--cui-alert-border-width` | `length` | Root border width. | `1px` |
| <span id="alert-css-calert-css-variables-cui-alert-radius"></span>`--cui-alert-radius` | `length` | Root corner radius. | `0.75rem` |
| <span id="alert-css-calert-css-variables-cui-alert-padding"></span>`--cui-alert-padding` | `length` | Root block and inline padding. | `Size-derived spacing.` |
| <span id="alert-css-calert-css-variables-cui-alert-gap"></span>`--cui-alert-gap` | `length` | Gap between indicator, content, and actions. | `Size-derived spacing.` |
| <span id="alert-css-calert-css-variables-cui-alert-content-gap"></span>`--cui-alert-content-gap` | `length` | Space between title and message. | `Size-derived spacing.` |
| <span id="alert-css-calert-css-variables-cui-alert-actions-gap"></span>`--cui-alert-actions-gap` | `length` | Gap between direct action controls. | `Size-derived spacing.` |
| <span id="alert-css-calert-css-variables-cui-alert-title-font-weight"></span>`--cui-alert-title-font-weight` | `number` | Title emphasis without choosing heading semantics. | `650` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CAlert attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="alert-attribute-calert-attributes-data-intent"></span>`data-intent` | Root | `"info" | "success" | "warn" | "error"` | Mirrors effective visual intent. |
| <span id="alert-attribute-calert-attributes-data-variant"></span>`data-variant` | Root | `"soft" | "solid" | "outline"` | Mirrors effective visual emphasis. |
| <span id="alert-attribute-calert-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Mirrors effective geometry. |
| <span id="alert-attribute-calert-attributes-data-announce"></span>`data-announce` | Root | `"off" | "polite" | "assertive"` | Mirrors effective announcement configuration. |
| <span id="alert-attribute-calert-attributes-data-icon"></span>`data-icon` | Root | `present | absent` | Present while the decorative indicator is visible. |
| <span id="alert-attribute-calert-attributes-role"></span>`role` | Content wrapper | `absent | "status" | "alert"` | Native role derived from effective announcement configuration. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CAlert selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="alert-selector-calert-selectors-alert"></span>`[data-citry-ui-part="alert"]` | Root div | Stable Alert surface and `attrs` destination. |
| <span id="alert-selector-calert-selectors-indicator"></span>`[data-citry-ui-part="indicator"]` | Decorative indicator wrapper | Automatic or fixed registered icon container. |
| <span id="alert-selector-calert-selectors-content"></span>`[data-citry-ui-part="content"]` | Content wrapper | Title/message group and announcement-role destination. |
| <span id="alert-selector-calert-selectors-title"></span>`[data-citry-ui-part="title"]` | Optional title wrapper | Authored title content. |
| <span id="alert-selector-calert-selectors-message"></span>`[data-citry-ui-part="message"]` | Optional message wrapper | Authored default-slot content. |
| <span id="alert-selector-calert-selectors-actions"></span>`[data-citry-ui-part="actions"]` | Optional action wrapper | Action layout, group naming, and `actions_attrs` destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="alert-interface-alert-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="alert-interface-alert-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="alert-interface-alert-intent"></span>`CAlertIntent` | `Literal["info", "success", "warn", "error"]` |
| <span id="alert-interface-alert-variant"></span>`CAlertVariant` | `Literal["soft", "solid", "outline"]` |
| <span id="alert-interface-alert-size"></span>`CAlertSize` | `Literal["sm", "md", "lg"]` |
| <span id="alert-interface-alert-announce"></span>`CAlertAnnounce` | `Literal["off", "polite", "assertive"]` |
| <span id="alert-interface-alert-icon-name"></span>`CIconName` | `Literal["arrow-down", "arrow-left", "arrow-right", "arrow-up", "calendar", "check", "chevron-down", "chevron-left", "chevron-right", "chevron-up", "circle-check", "circle-help", "circle-info", "circle-x", "clock", "copy", "download", "edit", "external-link", "eye", "eye-off", "file", "folder", "heart", "home", "leaf", "link", "lock", "mail", "menu", "minus", "more-horizontal", "more-vertical", "plus", "refresh-cw", "search", "settings", "star", "trash", "triangle-alert", "unlock", "upload", "user", "x", "back", "forward", "prev", "next", "close", "clear", "success", "info", "warn", "danger", "expand", "collapse", "dropdown"]` |

</div>

<span id="alert-interface-alert-title-slot-data"></span>

#### `CAlertTitleSlotData`

Empty dataclass: `{}`.

<span id="alert-interface-alert-default-slot-data"></span>

#### `CAlertDefaultSlotData`

Empty dataclass: `{}`.

<span id="alert-interface-alert-actions-slot-data"></span>

#### `CAlertActionsSlotData`

Empty dataclass: `{}`.

### Translation keys

-