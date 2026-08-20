---
title: Dialog
url: https://citry.dev/v/0.4.1/ui-library/components/dialog/
description: "Build accessible native modal workflows with Citry UI Dialog."
---
# Dialog

Use `CDialog` for a task or decision that temporarily blocks the page. It
renders a native `<dialog>`, enters the browser top layer, makes background
content inert, contains focus, restores focus, and locks page scrolling.

## Dialog at a glance

Use `sm` for one clear decision, `md` for ordinary tasks, `lg` for richer
content, and `full` when the task needs the viewport.


### Dialog at a glance

[Open the rendered preview](/v/0.4.1/ui-library/components/dialog/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DialogAtAGlance(Component):
    template = """
      <section class="dialog-glance">
        <article>
          <p class="dialog-glance__eyebrow">Lunar atlas</p>
          <h2>Mare Imbrium</h2>
          <p>A compact note for one clear decision.</p>
          <c-CDialog size="sm">
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton c-attrs="activator_attrs">
                Open field note
              </c-CButton>
            </c-fill>
            <c-fill name="title">
              Mare Imbrium
            </c-fill>
            <c-fill name="default">
              The basin spans more than 1,100 kilometres.
            </c-fill>
          </c-CDialog>
        </article>

        <article>
          <p class="dialog-glance__eyebrow">Deep-sky catalog</p>
          <h2>Orion Nebula</h2>
          <p>A generous surface for richer observations.</p>
          <c-CDialog size="lg">
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton variant="outline" c-attrs="activator_attrs">
                Inspect nebula
              </c-CButton>
            </c-fill>
            <c-fill name="title">
              Orion Nebula
            </c-fill>
            <c-fill name="description">
              A stellar nursery visible below Orion's belt.
            </c-fill>
            <c-fill name="default">
              New stars illuminate clouds of hydrogen, dust, and ionized gas.
            </c-fill>
          </c-CDialog>
        </article>
      </section>
    """

    css = """
      :where(.dialog-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.dialog-glance article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #6d28d9);
        border-radius: 0.875rem;
        background: Canvas;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.dialog-glance h2, .dialog-glance p) {
        margin: 0;
      }

      :where(.dialog-glance__eyebrow) {
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = DialogAtAGlance()

preview  # noqa: B018
````


## Build a Dialog

Provide a required title and body. Spread `activator_attrs` onto the control
that opens it. Spread `close_attrs` onto explicit completion or cancel actions.


### Open a field note

[Open the rendered preview](/v/0.4.1/ui-library/components/dialog/_previews/open-field-note/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class OpenFieldNote(Component):
    template = """
      <section class="field-note">
        <p>Tonight's observation</p>
        <h2>Aurora over the northern ridge</h2>
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Read field note
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Aurora over the northern ridge
          </c-fill>
          <c-fill name="description">
            Recorded at 01:42 under a clear sky.
          </c-fill>
          <c-fill name="default">
            <p>
              Green ribbons appeared low on the horizon, then climbed toward
              the zenith in three bright arcs.
            </p>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton variant="ghost" c-attrs="close_attrs">
              Close note
            </c-CButton>
            <c-CButton>
              Add to atlas
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.field-note) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0369a1);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.field-note h2, .field-note p) {
        margin: 0;
      }

      :where(.field-note > p) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = OpenFieldNote()

preview  # noqa: B018
````



```citry-html
<c-CDialog>
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">
      Read field note
    </c-CButton>
  </c-fill>
  <c-fill name="title">
    Aurora over the northern ridge
  </c-fill>
  <c-fill name="description">
    Recorded at 01:42 under a clear sky.
  </c-fill>
  <c-fill name="default">
    ...
  </c-fill>
  <c-fill name="actions" data="{ close_attrs }">
    <c-CButton c-attrs="close_attrs">
      Close note
    </c-CButton>
  </c-fill>
</c-CDialog>
```


Compose a Dialog in Python when its content is already available there:


```python
from citry_ui import CDialog

field_note = CDialog(
    slots={
        "title": "Aurora over the northern ridge",
        "default": note_content,
    },
)
```


The title becomes the accessible name. Use `description` for one concise
summary. Keep structured or lengthy content in the body so assistive technology
does not announce it as one uninterrupted description.

The activator is optional. A controlled owner may open the Dialog without one.

## Configure Dialog

Server inputs are passed in Python through `<c-CDialog ... />` attributes or a
`CDialog(...)` composition call. Client inputs are passed in the browser
through `$c-props="{...}"`.


### Configure Dialog

[Open the rendered preview](/v/0.4.1/ui-library/components/dialog/_previews/configuration/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConfigureDialog(Component):
    template = """
      <section
        class="dialog-config"
        x-data="{
          size: 'md',
          scroll: 'body',
          dismissible: true,
          close_on_escape: true,
          close_on_outside: true,
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <p>Observation archive</p>
        <h2>Configure the Dialog</h2>
        <c-CDialog
          $c-props="{
            size,
            scroll,
            dismissible,
            closeOnEscape: close_on_escape,
            closeOnOutside: close_on_outside,
          }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Preview configuration
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Observation archive
          </c-fill>
          <c-fill name="description">
            Test size, scrolling, and passive dismissal.
          </c-fill>
          <c-fill name="default">
            <p>The archive currently holds 384 lunar observations.</p>
            <p>Try Escape, the backdrop, and the explicit action.</p>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">
              Finish preview
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.dialog-config) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 52rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #6d28d9);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.dialog-config h2, .dialog-config p) {
        margin: 0;
      }

      :where(.dialog-config > p) {
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview_controls = (
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large"), ("full", "Full")),
    },
    {
        "name": "scroll",
        "label": "Scroll",
        "type": "select",
        "default": "body",
        "options": (("body", "Body only"), ("dialog", "Complete Dialog")),
    },
    {
        "name": "dismissible",
        "label": "Allow passive dismissal",
        "type": "checkbox",
        "default": True,
    },
    {
        "name": "close_on_escape",
        "label": "Close on Escape",
        "type": "checkbox",
        "default": True,
    },
    {
        "name": "close_on_outside",
        "label": "Close on backdrop press",
        "type": "checkbox",
        "default": True,
    },
)

preview = ConfigureDialog()

preview  # noqa: B018
````


A valid client input wins over its server value. Removing it restores the
server value, except `open`, which preserves the last committed state and
becomes uncontrolled. An invalid `open` value does the same after reporting a
diagnostic. Other invalid client values use their server fallback.


```citry-html
<c-CDialog
  size="md"
  scroll="body"
  $c-props="{
    size: preferredSize,
    scroll: preferredScroll,
    dismissible: allowPassiveClose,
  }"
>
  ...
</c-CDialog>
```


`id`, `close_label`, `class_`, `style`, and `attrs` are server-only because
they define rendered identity, text, and native structure.

## Control visibility

Pass a Boolean client `open` input to control visibility. `onOpenChange`
reports user requests; update `open` to accept one or keep it unchanged to
decline it.


### Control Dialog visibility

[Open the rendered preview](/v/0.4.1/ui-library/components/dialog/_previews/controlled-dialog/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledDialog(Component):
    template = """
      <section
        class="controlled-dialog"
        x-data="{ open: false, accept: false, lastReason: 'none' }"
      >
        <p>Mission control</p>
        <h2>Own every visibility change</h2>
        <label class="controlled-dialog__toggle">
          <input type="checkbox" x-model="accept" />
          Accept Dialog requests
        </label>
        <c-CDialog
          $c-props="{
            open,
            onOpenChange: (nextOpen, detail) => {
              lastReason = detail.reason;
              if (accept) open = nextOpen;
            },
          }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Request flight plan
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Flight plan
          </c-fill>
          <c-fill name="default">
            Controlled owners may accept or decline this close request.
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">
              Request close
            </c-CButton>
          </c-fill>
        </c-CDialog>
        <p class="controlled-dialog__status" aria-live="polite">
          Last request: <strong x-text="lastReason">none</strong>
        </p>
      </section>
    """

    css = """
      :where(.controlled-dialog) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0369a1);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.controlled-dialog h2, .controlled-dialog p) {
        margin: 0;
      }

      :where(.controlled-dialog > p:first-child) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.controlled-dialog__toggle) {
        display: flex;
        gap: 0.5rem;
        align-items: center;
      }

      :where(.controlled-dialog__status) {
        color: color-mix(in srgb, currentColor 72%, transparent);
        font-size: 0.875rem;
      }
    """


preview = ControlledDialog()

preview  # noqa: B018
````



```citry-html
<c-CDialog
  $c-props="{
    open,
    onOpenChange: (nextOpen, detail) => {
      if (mayApply(nextOpen, detail)) open = nextOpen;
    },
  }"
>
  ...
</c-CDialog>
```


The callback detail identifies the `trigger`, `close-button`, `action`,
`escape`, `outside`, or `native` reason. It also includes controlled ownership,
the browser source, and the Dialog return value. Owner commits do not notify
again.

When no client `open` input is supplied, CDialog commits requests itself and
then notifies. Passing `null` or removing the input releases control without
resetting the current state.

## Choose dismissal rules

`dismissible=True` shows the built-in close Button and permits passive
dismissal. `close_on_escape` and `close_on_outside` refine which passive paths
are allowed. All three have matching client inputs.


### Require an explicit decision

[Open the rendered preview](/v/0.4.1/ui-library/components/dialog/_previews/explicit-decision/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ExplicitDecision(Component):
    template = """
      <section class="explicit-dialog">
        <p>Telescope alignment</p>
        <h2>Require an explicit decision</h2>
        <c-CDialog c-dismissible="False">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton intent="warn" c-attrs="activator_attrs">
              Recalibrate telescope
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Recalibrate telescope?
          </c-fill>
          <c-fill name="description">
            Observation pauses for about two minutes.
          </c-fill>
          <c-fill name="default">
            Escape, backdrop presses, and the built-in close control are unavailable.
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton variant="outline" c-attrs="close_attrs">
              Keep current alignment
            </c-CButton>
            <c-CButton c-attrs="close_attrs">
              Begin recalibration
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.explicit-dialog) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 44rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#fde68a, #a16207);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.explicit-dialog h2, .explicit-dialog p) {
        margin: 0;
      }

      :where(.explicit-dialog > p) {
        color: light-dark(#a16207, #fde68a);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = ExplicitDecision()

preview  # noqa: B018
````


With `dismissible=False`, Escape, backdrop presses, and the built-in close
control are unavailable. Actions with `close_attrs` still work, so a deliberate
workflow can always complete.

Outside dismissal requires a press that starts and ends on this Dialog's
backdrop. Dragging from content to the backdrop does not close it.

## Place initial focus

The server `initial_focus` input and matching client `initialFocus` input accept
`auto` or `title`.


### Place initial focus

[Open the rendered preview](/v/0.4.1/ui-library/components/dialog/_previews/initial-focus/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DialogInitialFocus(Component):
    template = """
      <section class="dialog-focus-grid" x-data>
        <article>
          <p>Quick observation</p>
          <h2>Focus a control</h2>
          <c-CDialog initial_focus="auto">
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton
                c-attrs="activator_attrs"
                @click="$refs.cometName.setAttribute('autofocus', '')"
              >
                Name a comet
              </c-CButton>
            </c-fill>
            <c-fill name="title">
              Name a comet
            </c-fill>
            <c-fill name="default">
              <label for="comet-name">Catalog name</label>
              <input id="comet-name" x-ref="cometName" />
            </c-fill>
          </c-CDialog>
        </article>

        <article>
          <p>Long report</p>
          <h2>Focus the title</h2>
          <c-CDialog initial_focus="title">
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton variant="outline" c-attrs="activator_attrs">
                Read eclipse report
              </c-CButton>
            </c-fill>
            <c-fill name="title">
              Total eclipse report
            </c-fill>
            <c-fill name="default">
              <p>
                Focusing the title starts reading at the top without jumping
                past structured content.
              </p>
              <button type="button">Continue reading</button>
            </c-fill>
          </c-CDialog>
        </article>
      </section>
    """

    css = """
      :where(.dialog-focus-grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 60rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.dialog-focus-grid article) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #6d28d9);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.dialog-focus-grid h2, .dialog-focus-grid p) {
        margin: 0;
      }

      :where(.dialog-focus-grid article > p) {
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = DialogInitialFocus()

preview  # noqa: B018
````


- `auto` keeps native `[autofocus]` and browser Dialog focus steps. Put
  `autofocus` on the control that should receive focus first.
- `title` focuses the visible title. Use it for long or structured content so
  reading starts at the top without jumping to a later control.

Tab and Shift+Tab stay within the nearest open Dialog. Nested Dialog controls
do not enter a parent's focus loop. Closing returns focus to the element that
was active before opening when it remains available. A workflow that needs a
different destination can focus it after the close callback.

Do not add `tabindex` to the native Dialog. CDialog owns its focus contract and
rejects that attribute.

## Scroll long content

The server `scroll` input and matching client `scroll` input accept `body` or
`dialog`.


### Scroll long Dialog content

[Open the rendered preview](/v/0.4.1/ui-library/components/dialog/_previews/long-content/)

````citry
from dataclasses import dataclass

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


@dataclass(frozen=True, slots=True)
class ObservationEntry:
    title: str
    text: str


class DialogLongContent(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="dialog-scroll-demo">
        <p>Expedition archive</p>
        <h2>Choose what scrolls</h2>
        <c-CDialog scroll="body" size="lg">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Keep actions visible
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Seven nights at the ridge
          </c-fill>
          <c-fill name="description">
            Body scrolling keeps this header and the actions fixed.
          </c-fill>
          <c-fill name="default">
            <c-for each="entry in entries">
              <article class="dialog-scroll-demo__entry">
                <strong>{{ entry.title }}</strong>
                <span>{{ entry.text }}</span>
              </article>
            </c-for>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">
              Finish reading
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.dialog-scroll-demo) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 46rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0369a1);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.dialog-scroll-demo h2, .dialog-scroll-demo p) {
        margin: 0;
      }

      :where(.dialog-scroll-demo > p) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.dialog-scroll-demo__entry) {
        display: grid;
        gap: 0.25rem;
        padding-block: 0.75rem;
        border-block-end: 1px solid color-mix(in srgb, currentColor 16%, transparent);
      }

      :where(.dialog-scroll-demo__entry span) {
        color: color-mix(in srgb, currentColor 72%, transparent);
      }
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "entries": tuple(
                ObservationEntry(
                    title=f"Night {index}",
                    text="A clear horizon revealed Jupiter, four bright moons, and a faint silver arc.",
                )
                for index in range(1, 10)
            )
        }


preview = DialogLongContent()

preview  # noqa: B018
````


- `body` keeps the header and actions visible while the body scrolls.
- `dialog` scrolls the complete surface.

Both modes stay inside the dynamic viewport. `full` fills that viewport and
removes ordinary radius, border, and shadow. Long titles and actions wrap.

## Use a native Dialog Form

A native `<form method="dialog">` requests closure and sets the Dialog return
value to the accepted submitter's value.


### Use a native Dialog Form

[Open the rendered preview](/v/0.4.1/ui-library/components/dialog/_previews/dialog-form/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DialogForm(Component):
    template = """
      <section
        class="dialog-form-demo"
        x-data="{ result: 'No constellation selected' }"
      >
        <p>Star chart</p>
        <h2>Use a native Dialog Form</h2>
        <c-CDialog
          $c-props="{
            onOpenChange: (open, detail) => {
              if (!open && detail.returnValue) result = detail.returnValue;
            },
          }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Choose constellation
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Choose a constellation
          </c-fill>
          <c-fill name="description">
            Native submitter values become the Dialog return value.
          </c-fill>
          <c-fill name="default">
            <form method="dialog" class="dialog-form-demo__choices">
              <button value="Orion">Orion</button>
              <button value="Cassiopeia">Cassiopeia</button>
              <button value="Cygnus">Cygnus</button>
            </form>
          </c-fill>
        </c-CDialog>
        <p class="dialog-form-demo__result" aria-live="polite">
          Selected: <strong x-text="result">No constellation selected</strong>
        </p>
      </section>
    """

    css = """
      :where(.dialog-form-demo) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 44rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #6d28d9);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.dialog-form-demo h2, .dialog-form-demo p) {
        margin: 0;
      }

      :where(.dialog-form-demo > p:first-child) {
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.dialog-form-demo__choices) {
        display: grid;
        gap: 0.5rem;
      }

      :where(.dialog-form-demo__choices button) {
        padding: 0.75rem 1rem;
        border: 1px solid color-mix(in srgb, currentColor 24%, transparent);
        border-radius: 0.5rem;
        background: transparent;
        color: inherit;
        font: inherit;
        text-align: start;
        cursor: pointer;
      }

      :where(.dialog-form-demo__result) {
        color: color-mix(in srgb, currentColor 72%, transparent);
        font-size: 0.875rem;
      }
    """


preview = DialogForm()

preview  # noqa: B018
````



```citry-html
<c-CDialog
  $c-props="{
    onOpenChange: (open, detail) => {
      if (detail.reason === 'native') result = detail.returnValue;
    },
  }"
>
  <c-fill name="title">
    Choose a constellation
  </c-fill>
  <c-fill name="default">
    <form method="dialog">
      <button value="Orion">Orion</button>
      <button value="Cygnus">Cygnus</button>
    </form>
  </c-fill>
</c-CDialog>
```


In uncontrolled mode, the browser performs the native close. In controlled
mode, CDialog intercepts only that final close so the owner can accept or
decline it through `onOpenChange`. Validation, the submit event, reset,
`FormData`, and Citry Events remain native.

For asynchronous work, control `open`, show loading on the submit Button, keep
the Dialog open on validation or transport failure, and close after success.
Do not put `close_attrs` on a submit Button when closing before the result would
lose feedback.

## Nest Dialogs

Nest one `CDialog` inside another body when a focused subtask genuinely needs a
second modal layer.


### Nest Dialogs

[Open the rendered preview](/v/0.4.1/ui-library/components/dialog/_previews/nested-dialogs/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedDialogs(Component):
    template = """
      <section class="nested-dialog-demo">
        <p>Observatory archive</p>
        <h2>Open a chart inside a report</h2>
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Open transit report
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Europa transit report
          </c-fill>
          <c-fill name="default">
            <p>The moon crossed Jupiter's face shortly after midnight.</p>
            <c-CDialog size="sm">
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton variant="outline" c-attrs="activator_attrs">
                  Open transit chart
                </c-CButton>
              </c-fill>
              <c-fill name="title">
                Transit chart
              </c-fill>
              <c-fill name="default">
                Europa entered the western limb at 00:14 and cleared it at 02:37.
              </c-fill>
              <c-fill name="actions" data="{ close_attrs }">
                <c-CButton c-attrs="close_attrs">
                  Return to report
                </c-CButton>
              </c-fill>
            </c-CDialog>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">
              Close report
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.nested-dialog-demo) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 46rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0369a1);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.nested-dialog-demo h2, .nested-dialog-demo p) {
        margin: 0;
      }

      :where(.nested-dialog-demo > p) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = NestedDialogs()

preview  # noqa: B018
````


Each Dialog owns only its nearest activators, close actions, focus loop, and
scroll-lock claim. Closing the nested Dialog leaves its parent open and returns
focus to the nested trigger. Closing a parent also closes its open descendants,
so an invisible nested modal cannot retain page inertness. Escape affects the
top Dialog.

Avoid deep modal stacks. A page, expansion, or inline disclosure is usually
easier to understand after one nested task.

## Theme and customize Dialog

Dialog follows the surrounding `color-scheme` even in the browser top layer.
Set documented `--cui-dialog-*` variables on an ancestor or the Dialog root.
Use public `data-citry-ui-part` selectors for targeted region styling.


### Theme Dialog

[Open the rendered preview](/v/0.4.1/ui-library/components/dialog/_previews/theme-customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DialogThemeCustomization(Component):
    template = """
      <section class="moonlit-dialog">
        <p>Moonlit observatory</p>
        <h2>Customize tokens and parts</h2>
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Open moon map
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Moon map
          </c-fill>
          <c-fill name="description">
            Public variables tune the surface; public selectors tune regions.
          </c-fill>
          <c-fill name="close">
            <span aria-hidden="true">✦</span>
          </c-fill>
          <c-fill name="default">
            The terminator currently crosses the eastern rim of Copernicus.
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.moonlit-dialog) {
        --cui-dialog-backdrop: rgb(15 23 42 / 78%);
        --cui-dialog-background: light-dark(#f5f3ff, #172033);
        --cui-dialog-foreground: light-dark(#2e1065, #e0e7ff);
        --cui-dialog-border-color: light-dark(#a78bfa, #818cf8);
        --cui-dialog-radius: 1.25rem;
        --cui-dialog-shadow: 0 1.75rem 5rem rgb(49 46 129 / 36%);

        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 44rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #6d28d9);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.moonlit-dialog h2, .moonlit-dialog p) {
        margin: 0;
      }

      :where(.moonlit-dialog > p) {
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.moonlit-dialog [data-citry-ui-part="title"]) {
        letter-spacing: 0.03em;
      }

      :where(.moonlit-dialog [data-citry-ui-part="close"]) {
        color: light-dark(#6d28d9, #c4b5fd);
      }
    """


preview = DialogThemeCustomization()

preview  # noqa: B018
````



```css
.moonlit-observatory {
  --cui-dialog-backdrop: rgb(15 23 42 / 78%);
  --cui-dialog-background: #172033;
  --cui-dialog-foreground: #e0e7ff;
  --cui-dialog-border-color: #818cf8;
  --cui-dialog-radius: 1.25rem;
}

.moonlit-observatory [data-citry-ui-part="title"] {
  letter-spacing: 0.03em;
}
```


The optional `close` slot replaces only the icon inside the built-in accessible
Button. Keep its content non-interactive. CDialog retains its label, behavior,
and public `close` selector.

The documented variables, selectors, and reflected attributes are public CSS
API. `.cui-*` classes, `--_cui-*` variables, and behavior markers are private.

## Support narrow viewports and zoom


### Use a full Dialog

[Open the rendered preview](/v/0.4.1/ui-library/components/dialog/_previews/narrow-dialog/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NarrowDialog(Component):
    template = """
      <section class="narrow-dialog-demo">
        <p>Mobile star atlas</p>
        <h2>Fill a narrow viewport</h2>
        <c-CDialog size="full">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Open full atlas
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            The complete guide to circumpolar constellations
          </c-fill>
          <c-fill name="description">
            Full size uses the dynamic viewport and keeps actions reachable.
          </c-fill>
          <c-fill name="default">
            <p>
              Ursa Major, Ursa Minor, Cassiopeia, Cepheus, and Draco remain
              above the horizon throughout the year at northern latitudes.
            </p>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton variant="outline" c-attrs="close_attrs">
              Return to chart
            </c-CButton>
            <c-CButton>
              Mark visible stars
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.narrow-dialog-demo) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 40rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0369a1);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.narrow-dialog-demo h2, .narrow-dialog-demo p) {
        margin: 0;
      }

      :where(.narrow-dialog-demo > p) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = NarrowDialog()

preview  # noqa: B018
````


Dialog uses logical properties, wraps actions, and constrains ordinary sizes
to the dynamic viewport. It supports nested light and dark scopes, RTL content,
forced colors, text spacing, and high zoom without requiring motion.

The built-in close Button is at least 2.5rem square and always has an accessible
name. A non-dismissible Dialog must provide an explicit action or another clear
completion path.

Without JavaScript, `open=False` keeps content in a closed native Dialog.
`open=True` shows non-modal content because only browser `showModal()` enters
the top layer. Client activation upgrades it immediately.

## API reference

### Inputs

#### CDialog server inputs

Server inputs are passed in a template through `<c-CDialog ... />` or in Python through
`CDialog(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="dialog-input-cdialog-server-inputs-id"></span>`id` | `str | None` | generated | Sets native identity and title, description, and activator relationships. |
| <span id="dialog-input-cdialog-server-inputs-open"></span>`open` | `bool` | `False` | Sets the server-visible initial open state. A valid client `open` input controls later state. |
| <span id="dialog-input-cdialog-server-inputs-dismissible"></span>`dismissible` | `bool` | `True` | Shows the built-in close control and permits passive dismissal. Explicit action bindings remain available when false. |
| <span id="dialog-input-cdialog-server-inputs-close-on-escape"></span>`close_on_escape` | `bool` | `True` | Permits Escape and equivalent platform cancel requests when dismissible. |
| <span id="dialog-input-cdialog-server-inputs-close-on-outside"></span>`close_on_outside` | `bool` | `True` | Permits a press that begins and ends on this Dialog's backdrop when dismissible. |
| <span id="dialog-input-cdialog-server-inputs-initial-focus"></span>`initial_focus` | `"auto" | "title"` ([`CDialogInitialFocus`](#dialog-interface-input-type-aliases-cdialog-initial-focus)) | `"auto"` | Preserves native autofocus and Dialog focus steps, or focuses the fixed title after opening. |
| <span id="dialog-input-cdialog-server-inputs-size"></span>`size` | `"sm" | "md" | "lg" | "full"` ([`CDialogSize`](#dialog-interface-input-type-aliases-cdialog-size)) | `"md"` | Sets the responsive surface size. |
| <span id="dialog-input-cdialog-server-inputs-scroll"></span>`scroll` | `"body" | "dialog"` ([`CDialogScroll`](#dialog-interface-input-type-aliases-cdialog-scroll)) | `"body"` | Scrolls only body content or the complete Dialog surface. |
| <span id="dialog-input-cdialog-server-inputs-close-label"></span>`close_label` | `non-empty str` | `"Close"` | Sets the built-in close Button's accessible name. |
| <span id="dialog-input-cdialog-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#dialog-interface-input-type-aliases-class-value)) | `None` | Adds native Dialog classes from a string, conditional mapping, or nested sequence and merges them with `attrs`. |
| <span id="dialog-input-cdialog-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#dialog-interface-input-type-aliases-style-value)) | `None` | Adds native Dialog inline styles from CSS text, a property mapping, or nested sequence and merges them with `attrs`. |
| <span id="dialog-input-cdialog-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native Dialog, ARIA, Alpine, and data attributes. It may also contribute class and style values; prefer the top-level inputs for those. |

</div>

#### CDialog client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CDialog />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="dialog-input-cdialog-client-inputs-open"></span>`open` | `boolean | null` | Continues uncontrolled from the current committed state. `null` has the same effect. | Controls visible open state while supplied as a Boolean. An invalid value reports once and releases control from the current state. |
| <span id="dialog-input-cdialog-client-inputs-dismissible"></span>`dismissible` | `boolean` | Uses the server input. | Controls built-in close visibility and passive dismissal. |
| <span id="dialog-input-cdialog-client-inputs-close-on-escape"></span>`closeOnEscape` | `boolean` | Uses the server input. | Controls Escape and platform cancel dismissal. |
| <span id="dialog-input-cdialog-client-inputs-close-on-outside"></span>`closeOnOutside` | `boolean` | Uses the server input. | Controls backdrop-press dismissal. |
| <span id="dialog-input-cdialog-client-inputs-initial-focus"></span>`initialFocus` | `"auto" | "title"` ([`CDialogInitialFocus`](#dialog-interface-input-type-aliases-cdialog-initial-focus)) | Uses the server input. | Controls focus placement on the next opening. |
| <span id="dialog-input-cdialog-client-inputs-size"></span>`size` | `"sm" | "md" | "lg" | "full"` ([`CDialogSize`](#dialog-interface-input-type-aliases-cdialog-size)) | Uses the server input. | Controls `data-size` and responsive geometry. |
| <span id="dialog-input-cdialog-client-inputs-scroll"></span>`scroll` | `"body" | "dialog"` ([`CDialogScroll`](#dialog-interface-input-type-aliases-cdialog-scroll)) | Uses the server input. | Controls `data-scroll` and overflow behavior. |
| <span id="dialog-input-cdialog-client-inputs-on-open-change"></span>`onOpenChange` | `function` | Does not notify a component callback. | Receives user-authored open requests and unavoidable native close reconciliation. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CDialog slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="dialog-slot-cdialog-slots-activator"></span>`activator` | no | `{activator_attrs: dict[str, object]}` ([`CDialogActivatorSlotData`](#dialog-interface-cdialog-activator-slot-data)) | No activator. |
| <span id="dialog-slot-cdialog-slots-title"></span>`title` | yes | `{}` ([`CDialogTitleSlotData`](#dialog-interface-cdialog-title-slot-data)) | none |
| <span id="dialog-slot-cdialog-slots-description"></span>`description` | no | `{}` ([`CDialogDescriptionSlotData`](#dialog-interface-cdialog-description-slot-data)) | Omitted, with no `aria-describedby`. |
| <span id="dialog-slot-cdialog-slots-default"></span>`default` | yes | `{}` ([`CDialogDefaultSlotData`](#dialog-interface-cdialog-default-slot-data)) | none |
| <span id="dialog-slot-cdialog-slots-actions"></span>`actions` | no | `{close_attrs: dict[str, object]}` ([`CDialogActionsSlotData`](#dialog-interface-cdialog-actions-slot-data)) | omitted |
| <span id="dialog-slot-cdialog-slots-close"></span>`close` | no | `{}` ([`CDialogCloseSlotData`](#dialog-interface-cdialog-close-slot-data)) | Built-in multiplication-sign icon inside the accessible close Button. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CDialog events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="dialog-event-cdialog-events-on-open-change"></span>`onOpenChange` | `(requestedOpen: boolean, detail: CDialogOpenChangeDetail) => void` ([`CDialogOpenChangeDetail`](#dialog-interface-cdialog-open-change-detail)) | An owned trigger, built-in close, explicit action, Escape, outside press, or native close requests a different open state. | `{reason: "trigger" | "close-button" | "action" | "escape" | "outside" | "native", controlled: boolean, source: Element | EventTarget | null, returnValue: string}` ([`CDialogOpenChangeDetail`](#dialog-interface-cdialog-open-change-detail)) | Uncontrolled requests commit before notification. Controlled requests, including successful Dialog Form submission, wait for the owner. An external native close is reconciled immediately and a stale true input cannot reopen it. Owner commits do not notify. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CDialog CSS variables

Apply these variables to `CDialog` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="dialog-css-cdialog-css-variables-cui-dialog-backdrop"></span>`--cui-dialog-backdrop` | `color` | Top-layer backdrop color. | `rgb(15 23 42 / 58%)` |
| <span id="dialog-css-cdialog-css-variables-cui-dialog-background"></span>`--cui-dialog-background` | `color` | Surface background. | `Canvas` |
| <span id="dialog-css-cdialog-css-variables-cui-dialog-foreground"></span>`--cui-dialog-foreground` | `color` | Surface text. | `CanvasText` |
| <span id="dialog-css-cdialog-css-variables-cui-dialog-border-color"></span>`--cui-dialog-border-color` | `color` | Surface boundary. | `Subtle CanvasText mix.` |
| <span id="dialog-css-cdialog-css-variables-cui-dialog-radius"></span>`--cui-dialog-radius` | `length` | Surface corner radius. | `0.875rem` |
| <span id="dialog-css-cdialog-css-variables-cui-dialog-shadow"></span>`--cui-dialog-shadow` | `shadow` | Surface elevation. | `0 1.5rem 4rem rgb(15 23 42 / 28%)` |
| <span id="dialog-css-cdialog-css-variables-cui-dialog-inline-size"></span>`--cui-dialog-inline-size` | `length` | Responsive preferred width. | ``Size-derived; 36rem at `md`.`` |
| <span id="dialog-css-cdialog-css-variables-cui-dialog-max-block-size"></span>`--cui-dialog-max-block-size` | `length` | Maximum non-full height. | `calc(100dvb - 2rem)` |
| <span id="dialog-css-cdialog-css-variables-cui-dialog-padding"></span>`--cui-dialog-padding` | `length` | Surface region padding. | `1.25rem` |
| <span id="dialog-css-cdialog-css-variables-cui-dialog-gap"></span>`--cui-dialog-gap` | `length` | Gap between Dialog regions. | `1rem` |
| <span id="dialog-css-cdialog-css-variables-cui-dialog-close-size"></span>`--cui-dialog-close-size` | `length` | Built-in close Button target size. | `2.5rem` |
| <span id="dialog-css-cdialog-css-variables-cui-dialog-close-radius"></span>`--cui-dialog-close-radius` | `length` | Built-in close Button radius. | `0.5rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CDialog attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="dialog-attribute-cdialog-attributes-data-open"></span>`data-open` | Native Dialog | `present | absent` | Mirrors effective native open state. |
| <span id="dialog-attribute-cdialog-attributes-data-size"></span>`data-size` | Native Dialog | `"sm" | "md" | "lg" | "full"` | Mirrors effective responsive size. |
| <span id="dialog-attribute-cdialog-attributes-data-scroll"></span>`data-scroll` | Native Dialog | `"body" | "dialog"` | Mirrors effective overflow mode. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CDialog selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="dialog-selector-cdialog-selectors-data-citry-ui-part-dialog"></span>`[data-citry-ui-part="dialog"]` | Native Dialog | Modal root and `attrs` destination. |
| <span id="dialog-selector-cdialog-selectors-data-citry-ui-part-surface"></span>`[data-citry-ui-part="surface"]` | Surface | Visual Dialog surface. |
| <span id="dialog-selector-cdialog-selectors-data-citry-ui-part-header"></span>`[data-citry-ui-part="header"]` | Header | Title and built-in close layout. |
| <span id="dialog-selector-cdialog-selectors-data-citry-ui-part-title"></span>`[data-citry-ui-part="title"]` | Title | Required accessible visible title. |
| <span id="dialog-selector-cdialog-selectors-data-citry-ui-part-description"></span>`[data-citry-ui-part="description"]` | Description | Optional concise described-by content. |
| <span id="dialog-selector-cdialog-selectors-data-citry-ui-part-close"></span>`[data-citry-ui-part="close"]` | Close Button | Built-in accessible dismissal control. |
| <span id="dialog-selector-cdialog-selectors-data-citry-ui-part-body"></span>`[data-citry-ui-part="body"]` | Body | Required default content region. |
| <span id="dialog-selector-cdialog-selectors-data-citry-ui-part-actions"></span>`[data-citry-ui-part="actions"]` | Actions | Optional explicit-action region. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="dialog-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="dialog-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="dialog-interface-input-type-aliases-cdialog-initial-focus"></span>`CDialogInitialFocus` | `Literal["auto", "title"]` |
| <span id="dialog-interface-input-type-aliases-cdialog-size"></span>`CDialogSize` | `Literal["sm", "md", "lg", "full"]` |
| <span id="dialog-interface-input-type-aliases-cdialog-scroll"></span>`CDialogScroll` | `Literal["body", "dialog"]` |

</div>

<span id="dialog-interface-cdialog-activator-slot-data"></span>

#### `CDialogActivatorSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="dialog-interface-cdialog-activator-slot-data-activator-attrs"></span>`activator_attrs` | `dict[str, object]` | - | Owned trigger marker plus `aria-haspopup`, `aria-controls`, and synchronized `aria-expanded`. |

</div>

<span id="dialog-interface-cdialog-title-slot-data"></span>

#### `CDialogTitleSlotData`

Empty dataclass: `{}`.

<span id="dialog-interface-cdialog-description-slot-data"></span>

#### `CDialogDescriptionSlotData`

Empty dataclass: `{}`.

<span id="dialog-interface-cdialog-default-slot-data"></span>

#### `CDialogDefaultSlotData`

Empty dataclass: `{}`.

<span id="dialog-interface-cdialog-actions-slot-data"></span>

#### `CDialogActionsSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="dialog-interface-cdialog-actions-slot-data-close-attrs"></span>`close_attrs` | `dict[str, object]` | - | Explicit-close marker for an action control. A Button value becomes the requested return value. |

</div>

<span id="dialog-interface-cdialog-close-slot-data"></span>

#### `CDialogCloseSlotData`

Empty dataclass: `{}`.

<span id="dialog-interface-cdialog-open-change-detail"></span>

#### `CDialogOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="dialog-interface-cdialog-open-change-detail-reason"></span>`reason` | `"trigger" | "close-button" | "action" | "escape" | "outside" | "native"` | - | Source of the open or close request. |
| <span id="dialog-interface-cdialog-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client `open` value currently owns state. |
| <span id="dialog-interface-cdialog-open-change-detail-source"></span>`source` | `Element | EventTarget | null` | - | Browser source associated with the request. |
| <span id="dialog-interface-cdialog-open-change-detail-return-value"></span>`returnValue` | `string` | - | Explicit action value or native Dialog Form return value; empty for other requests. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CDialog translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="dialog-translation-cdialog-translations-close"></span>`citry-ui-dialog-close` | Names the generated close control. | `None` | `close_label` input or `close` slot | $c-tr updates `aria-label`. |

</div>