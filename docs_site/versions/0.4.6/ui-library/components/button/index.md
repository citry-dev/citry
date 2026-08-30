---
title: Button
url: https://citry.dev/v/0.4.6/ui-library/components/button/
description: "Render styled native actions, links, and form submitters with Citry UI Button."
---
# Button

Use `CButton` for prominent actions and links. It renders a native `<button>`
by default and a native `<a>` when `href` is set. Both roots share styled
variants, semantic intents, three sizes, decoration slots, and a
focus-preserving loading state.

## Button at a glance

Solid, outline, and ghost variants set emphasis. Loading and disabled both
block activation, but only loading keeps the Button focusable in the browser.


### Button at a glance

[Open the rendered preview](/v/0.4.6/ui-library/components/button/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonAtAGlance(Component):
    template = """
      <section class="button-glance">
        <article class="button-glance__card">
          <header>
            <p>Woodland field guide</p>
            <h2>Follow the fern trail</h2>
          </header>

          <div class="button-glance__actions">
            <c-CButton intent="primary">
              <c-fill name="start">
                <span aria-hidden="true">✦</span>
              </c-fill>
              <c-fill name="default">
                Begin trail
              </c-fill>
            </c-CButton>
            <c-CButton variant="outline" intent="success">
              Log wildflower
            </c-CButton>
            <c-CButton variant="ghost" intent="neutral">
              Open field guide
            </c-CButton>
          </div>
        </article>

        <article class="button-glance__card">
          <header>
            <p>Trail conditions</p>
            <h2>Before you set out</h2>
          </header>

          <div class="button-glance__actions">
            <c-CButton loading intent="warn">
              Checking weather
            </c-CButton>
            <c-CButton disabled variant="outline" intent="neutral">
              North path closed
            </c-CButton>
          </div>
        </article>
      </section>
    """

    css = """
      :where(.button-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-glance__card) {
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid light-dark(#bbd6c5, #355e48);
        border-radius: 0.875rem;
        background: Canvas;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.button-glance__card header) {
        margin-block-end: 1rem;
      }

      :where(.button-glance__card h2, .button-glance__card p) {
        margin-block: 0;
      }

      :where(.button-glance__card header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-glance__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }
    """


preview = ButtonAtAGlance()

preview  # noqa: B018
````


## Create an action

`CButton` defaults to `type="button"`, so it does not accidentally submit a
surrounding form.


### Create Button actions

[Open the rendered preview](/v/0.4.6/ui-library/components/button/_previews/basic-actions/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonBasicActions(Component):
    template = """
      <section class="button-basic">
        <div>
          <p class="button-basic__eyebrow">Fern collection</p>
          <h2>One native action, optional decoration</h2>
        </div>

        <div class="button-basic__actions">
          <c-CButton>
            Record specimen
          </c-CButton>
          <c-CButton variant="outline">
            <c-fill name="start">
              <span aria-hidden="true">+</span>
            </c-fill>
            <c-fill name="default">
              Add observation
            </c-fill>
            <c-fill name="end">
              <span aria-hidden="true">→</span>
            </c-fill>
          </c-CButton>
        </div>
      </section>
    """

    css = """
      :where(.button-basic) {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 1rem;
        align-items: center;
        max-width: 58rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#cbd5d0, #40594b);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-basic h2, .button-basic p) {
        margin-block: 0;
      }

      :where(.button-basic__eyebrow) {
        margin-block-end: 0.35rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-basic__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = ButtonBasicActions()

preview  # noqa: B018
````



```citry-html
<c-CButton intent="primary">
  Record specimen
</c-CButton>
```


Compose the same Button in Python:


```python
from citry_ui import CButton

record_button = CButton(
    intent="primary",
    slots={"default": "Record specimen"},
)
```


## Navigate with a link

Set the server `href` input for navigation. `CButton` renders a native anchor,
so modifier clicks, context menus, link previews, and browser navigation remain
available.


### Use Button styling for links

[Open the rendered preview](/v/0.4.6/ui-library/components/button/_previews/navigation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonNavigation(Component):
    template = """
      <section class="button-navigation">
        <div>
          <p class="button-navigation__eyebrow">Trail library</p>
          <h2>Use link semantics for navigation</h2>
        </div>

        <div class="button-navigation__actions">
          <c-CButton href="https://example.com/field-guide/ferns/">
            Read the fern guide
          </c-CButton>
          <c-CButton
            href="https://example.com/herbarium"
            variant="outline"
            c-attrs="{'target': '_blank', 'rel': 'noreferrer'}"
          >
            <c-fill name="default">
              Visit the herbarium
            </c-fill>
            <c-fill name="end">
              <span aria-hidden="true">↗</span>
            </c-fill>
          </c-CButton>
        </div>
      </section>
    """

    css = """
      :where(.button-navigation) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        max-width: 58rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#cbd5d0, #40594b);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-navigation h2, .button-navigation p) {
        margin-block: 0;
      }

      :where(.button-navigation__eyebrow) {
        margin-block-end: 0.35rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-navigation__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = ButtonNavigation()

preview  # noqa: B018
````



```citry-html
<c-CButton
  href="https://example.com/field-guide/ferns/"
  c-attrs="{'target': '_blank', 'rel': 'noreferrer'}"
>
  Read the fern guide
</c-CButton>
```


The anchor keeps the same `inline-flex` layout as an action Button. Pass link
attributes such as `target`, `rel`, and `download` through `attrs`. `href` is
server-only because changing the native root after render would replace the
element and its browser state.

## Configure Button

Server inputs are passed in Python through `<c-CButton ... />` attributes or a
`CButton(...)` composition call. Client inputs are passed in the browser through
the `$c-props="{...}"` attribute.


### Configure Button

[Open the rendered preview](/v/0.4.6/ui-library/components/button/_previews/configuration/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonConfiguration(Component):
    template = """
      <section
        class="button-configurator"
        x-data="{
          variant: 'solid',
          intent: 'primary',
          size: 'md',
          loading_pos: 'center',
          loading: false,
          disabled: false,
          block: false,
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Specimen catalog</p>
          <h2>Configure the action</h2>
        </header>

        <div class="button-configurator__stage">
          <c-CButton
            $c-props="{
              variant,
              intent,
              size,
              loadingPosition: loading_pos,
              loading,
              disabled,
              block,
            }"
          >
            <c-fill name="start">
              <span aria-hidden="true">✿</span>
            </c-fill>
            <c-fill name="default">
              Catalog specimen
            </c-fill>
            <c-fill name="end">
              <span aria-hidden="true">→</span>
            </c-fill>
          </c-CButton>

          <p class="button-configurator__status" aria-live="polite">
            <span x-text="variant">solid</span>
            ·
            <span x-text="intent">primary</span>
            ·
            <span x-text="size">md</span>
          </p>
        </div>
      </section>
    """

    css = """
      :where(.button-configurator) {
        max-width: 58rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bbd6c5, #355e48);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.button-configurator header) {
        margin-block-end: 1rem;
      }

      :where(.button-configurator h2, .button-configurator p) {
        margin-block: 0;
      }

      :where(.button-configurator header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-configurator__stage) {
        display: grid;
        gap: 0.75rem;
        min-width: 0;
      }

      :where(
        .button-configurator__stage > [data-citry-ui-part="button"]
      ) {
        justify-self: start;
      }

      :where(
        .button-configurator__stage > [data-citry-ui-part="button"][data-block]
      ) {
        justify-self: stretch;
      }

      :where(.button-configurator__status) {
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "solid",
        "options": (("solid", "Solid"), ("outline", "Outline"), ("ghost", "Ghost")),
    },
    {
        "name": "intent",
        "label": "Intent",
        "type": "select",
        "default": "primary",
        "options": (
            ("primary", "Primary"),
            ("neutral", "Neutral"),
            ("success", "Success"),
            ("warn", "Warn"),
            ("danger", "Danger"),
        ),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "loading_pos",
        "label": "Loading position",
        "type": "select",
        "default": "center",
        "options": (("start", "Start"), ("center", "Center"), ("end", "End")),
    },
    {
        "name": "loading",
        "label": "Show loading state",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "disabled",
        "label": "Disable Button",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "block",
        "label": "Fill available width",
        "type": "checkbox",
        "default": False,
    },
)

preview = ButtonConfiguration()

preview  # noqa: B018
````


A supplied valid client input wins over its server input. Removing it restores
the server value. Invalid client values report one diagnostic per invalid
episode and use the server value for that field.


```citry-html
<c-CButton
  variant="outline"
  $c-props="{
    loading: scanning,
    disabled: !trailOpen,
    variant: preferredVariant,
  }"
>
  Begin survey
</c-CButton>
```


`type`, `href`, and `attrs` remain server-only because they define native
structure and browser behavior.

## Choose a variant

Use `solid` for the strongest action, `outline` for a visible alternative, and
`ghost` for a quiet action near stronger controls.


### Compare Button variants

[Open the rendered preview](/v/0.4.6/ui-library/components/button/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonVariants(Component):
    template = """
      <section class="button-variants">
        <article>
          <h2>Solid</h2>
          <p>Primary action in the current view.</p>
          <c-CButton variant="solid">
            Begin trail
          </c-CButton>
        </article>
        <article>
          <h2>Outline</h2>
          <p>Visible alternative with less emphasis.</p>
          <c-CButton variant="outline">
            Compare tracks
          </c-CButton>
        </article>
        <article>
          <h2>Ghost</h2>
          <p>Quiet action near stronger controls.</p>
          <c-CButton variant="ghost">
            Read field notes
          </c-CButton>
        </article>
      </section>
    """

    css = """
      :where(.button-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-variants article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        min-width: 0;
        padding: 1.1rem;
        border: 1px solid light-dark(#cbd5d0, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-variants h2, .button-variants p) {
        margin-block: 0;
      }

      :where(.button-variants p) {
        color: color-mix(in srgb, currentColor 68%, transparent);
      }

      :where(.button-variants [data-citry-ui-part="button"]) {
        justify-self: start;
      }
    """


preview = ButtonVariants()

preview  # noqa: B018
````


## Choose an intent

Intent communicates meaning without changing mechanics. Use `primary` for the
main action, `success` for a completed or beneficial outcome, `warn` for
caution, `danger` for a destructive outcome, and `neutral` when no semantic
color is needed.


### Compare Button intents

[Open the rendered preview](/v/0.4.6/ui-library/components/button/_previews/intents/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonIntents(Component):
    template = """
      <section class="button-intents">
        <article>
          <h2>Neutral</h2>
          <div>
            <c-CButton intent="neutral">View habitat</c-CButton>
            <c-CButton intent="neutral" variant="outline">View habitat</c-CButton>
          </div>
        </article>
        <article>
          <h2>Accent</h2>
          <div>
            <c-CButton intent="primary">Begin survey</c-CButton>
            <c-CButton intent="primary" variant="outline">Begin survey</c-CButton>
          </div>
        </article>
        <article>
          <h2>Positive</h2>
          <div>
            <c-CButton intent="success">Protect grove</c-CButton>
            <c-CButton intent="success" variant="outline">Protect grove</c-CButton>
          </div>
        </article>
        <article>
          <h2>Warning</h2>
          <div>
            <c-CButton intent="warn">Check conditions</c-CButton>
            <c-CButton intent="warn" variant="outline">Check conditions</c-CButton>
          </div>
        </article>
        <article>
          <h2>Negative</h2>
          <div>
            <c-CButton intent="danger">Remove invasive</c-CButton>
            <c-CButton intent="danger" variant="outline">Remove invasive</c-CButton>
          </div>
        </article>
      </section>
    """

    css = """
      :where(.button-intents) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 0.75rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-intents article) {
        display: grid;
        gap: 0.65rem;
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#d5ddd8, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-intents h2) {
        margin-block: 0;
        font-size: 0.875rem;
      }

      :where(.button-intents article div) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }
    """


preview = ButtonIntents()

preview  # noqa: B018
````


## Set size and available width

`sm`, `md`, and `lg` change target height, padding, and text size. Set
`block=True` to fill the available inline size. Labels wrap instead of forcing
horizontal page overflow.


### Compare Button sizes and layout

[Open the rendered preview](/v/0.4.6/ui-library/components/button/_previews/sizes-and-layout/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonSizesAndLayout(Component):
    template = """
      <section class="button-sizes">
        <div class="button-sizes__row">
          <c-CButton size="sm">
            Mark moss
          </c-CButton>
          <c-CButton size="md">
            Map meadow
          </c-CButton>
          <c-CButton size="lg">
            Explore canopy
          </c-CButton>
        </div>

        <article>
          <p>Field kit for a narrow trail</p>
          <c-CButton block variant="outline">
            Record the flowering plants along this shaded riverbank
          </c-CButton>
        </article>
      </section>
    """

    css = """
      :where(.button-sizes) {
        display: grid;
        gap: 1rem;
        max-width: 54rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-sizes__row) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        padding: 1rem;
        border: 1px solid light-dark(#d5ddd8, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-sizes article) {
        display: grid;
        gap: 0.75rem;
        inline-size: min(100%, 24rem);
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#d5ddd8, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-sizes article p) {
        margin-block: 0;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }
    """


preview = ButtonSizesAndLayout()

preview  # noqa: B018
````


## Add decoration

Use `start` and `end` for icons or other non-interactive decoration. Their
order follows text direction.


### Decorate Button content

[Open the rendered preview](/v/0.4.6/ui-library/components/button/_previews/decorations/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonDecorations(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="button-decorations">
        <article>
          <h2>Logical start and end</h2>
          <div class="button-decorations__actions">
            <c-CButton variant="outline">
              <c-fill name="start">
                <span aria-hidden="true">✿</span>
              </c-fill>
              <c-fill name="default">
                Identify bloom
              </c-fill>
            </c-CButton>
            <c-CButton variant="outline">
              <c-fill name="default">
                Continue upstream
              </c-fill>
              <c-fill name="end">
                <span aria-hidden="true">→</span>
              </c-fill>
            </c-CButton>
            <c-CButton>
              <c-fill name="start">
                <span aria-hidden="true">+</span>
              </c-fill>
              <c-fill name="default">
                Add sighting
              </c-fill>
              <c-fill name="end">
                <span aria-hidden="true">✓</span>
              </c-fill>
            </c-CButton>
          </div>
        </article>

        <article dir="rtl">
          <h2>Right-to-left flow</h2>
          <c-CButton variant="outline">
            <c-fill name="start">
              <span aria-hidden="true">✿</span>
            </c-fill>
            <c-fill name="default">
              فحص الزهرة
            </c-fill>
            <c-fill name="end">
              <span aria-hidden="true">←</span>
            </c-fill>
          </c-CButton>
        </article>

        <article class="button-decorations__icon-only">
          <h2>Icon-only content</h2>
          <p>The accessible name comes from <code>aria-label</code>.</p>
          <c-CButton c-attrs="icon_attrs" variant="outline">
            <span aria-hidden="true">★</span>
          </c-CButton>
        </article>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"icon_attrs": {"aria-label": "Mark specimen as notable"}}

    css = """
      :where(.button-decorations) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-decorations article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#d5ddd8, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-decorations h2, .button-decorations p) {
        margin-block: 0;
      }

      :where(.button-decorations p) {
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }

      :where(
        .button-decorations__icon-only > [data-citry-ui-part="button"]
      ) {
        justify-self: start;
      }

      :where(.button-decorations__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.button-decorations article[dir="rtl"] [data-citry-ui-part="button"]) {
        justify-self: start;
      }
    """


preview = ButtonDecorations()

preview  # noqa: B018
````



```citry-html
<c-CButton variant="outline">
  <c-fill name="start">
    <svg aria-hidden="true">...</svg>
  </c-fill>
  <c-fill name="default">
    Identify bloom
  </c-fill>
  <c-fill name="end">
    <svg aria-hidden="true">...</svg>
  </c-fill>
</c-CButton>
```


Do not place links, inputs, or other interactive content inside a Button. For
icon-only content, pass an accessible name through `attrs`, such as
`{"aria-label": "Inspect leaf"}`. `CButton` does not add square icon-Button
geometry.

## Show loading and disabled states

The server `loading` input sets the initial pending state. The client `loading`
input is passed through `$c-props` when browser code owns later changes.


### Compare Button loading states

[Open the rendered preview](/v/0.4.6/ui-library/components/button/_previews/loading-states/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonLoadingStates(Component):
    template = """
      <section
        class="button-loading"
        x-data="{ scanning: false }"
      >
        <article class="button-loading__interactive">
          <div>
            <p>Interactive pending state</p>
            <h2>Listen for woodland birds</h2>
          </div>
          <c-CButton
            $c-props="{ loading: scanning }"
            @click="scanning = true; setTimeout(() => { scanning = false }, 2400)"
          >
            Begin listening
          </c-CButton>
          <span aria-live="polite" x-text="scanning ? 'Listening…' : 'Ready'"></span>
        </article>

        <div class="button-loading__positions">
          <c-CButton loading loading_pos="start" variant="outline">
            <c-fill name="start">
              <span aria-hidden="true">✿</span>
            </c-fill>
            <c-fill name="default">
              Identifying spores
            </c-fill>
          </c-CButton>
          <c-CButton loading loading_pos="center">
            Mapping the trail
          </c-CButton>
          <c-CButton loading loading_pos="end" variant="outline">
            <c-fill name="default">
              Tracing migration
            </c-fill>
            <c-fill name="end">
              <span aria-hidden="true">→</span>
            </c-fill>
          </c-CButton>
          <c-CButton loading intent="success">
            <c-fill name="loading">
              <span aria-hidden="true">✺</span>
            </c-fill>
            <c-fill name="default">
              Pressing specimen
            </c-fill>
          </c-CButton>
          <c-CButton disabled intent="neutral" variant="outline">
            Trail unavailable
          </c-CButton>
        </div>
      </section>
    """

    css = """
      :where(.button-loading) {
        display: grid;
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-loading__interactive) {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 0.75rem 1rem;
        align-items: center;
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#bbd6c5, #355e48);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-loading__interactive h2, .button-loading__interactive p) {
        margin-block: 0;
      }

      :where(.button-loading__interactive p) {
        margin-block-end: 0.3rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-loading__interactive > span) {
        grid-column: 1 / -1;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }

      :where(.button-loading__positions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        padding: 1rem;
        border: 1px solid light-dark(#d5ddd8, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      @media (max-width: 34rem) {
        :where(.button-loading__interactive) {
          grid-template-columns: minmax(0, 1fr);
        }
      }
    """


preview = ButtonLoadingStates()

preview  # noqa: B018
````


Loading blocks click, keyboard, submit, reset, `.click()`, and
`requestSubmit(button)` activation. It keeps focus on the Button, exposes
`aria-busy="true"` and `aria-disabled="true"`, and preserves the accessible
name. The application still owns the operation and decides when loading begins
and ends.

Loading placement changes visual replacement:

| Position | Result |
|---|---|
| `start` | Replace the start decoration; keep the label and end visible. |
| `center` | Replace all ordinary visual content without changing intrinsic width. |
| `end` | Replace the end decoration; keep the start and label visible. |

If a start or end decoration is absent, loading reserves that position to avoid
overlapping the label. The optional `loading` slot replaces the built-in
spinner with a compact visual indicator; the root owns pending semantics.

`disabled=True` uses native `disabled` behavior on an action Button. On a link,
it removes `href`, removes the link from the focus order, and blocks scripted
clicks. A loading link also removes `href` but stays focusable. Both restore the
original destination when their unavailable state clears. Use loading for an
in-progress operation and disabled for an unavailable control.

A disabled enclosing `CForm` always wins over the Button's local value. Action
Buttons become natively disabled; Button links become inert. Both reflect the
effective state through `aria-disabled` and `data-disabled`.

## Use native forms

Set the server `type` input to `submit` or `reset` for native form behavior.
Native submitter attributes pass through the server `attrs` mapping.


### Use Button in a native form

[Open the rendered preview](/v/0.4.6/ui-library/components/button/_previews/native-forms/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonNativeForms(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section
        class="button-form"
        x-data="{ result: 'No sighting recorded yet.' }"
      >
        <header>
          <p>Field journal</p>
          <h2>Record a woodland sighting</h2>
        </header>

        <form
          @submit.prevent="result = `Recorded with ${$event.submitter.value}.`"
          @reset="result = 'Journal reset.'"
        >
          <label for="button-form-species">Species</label>
          <input
            id="button-form-species"
            name="species"
            value="Silver-washed fritillary"
          />
          <div>
            <c-CButton
              type="submit"
              intent="success"
              c-attrs="submit_attrs"
            >
              Record sighting
            </c-CButton>
            <c-CButton type="reset" variant="ghost" intent="neutral">
              Reset journal
            </c-CButton>
          </div>
        </form>

        <p class="button-form__result" aria-live="polite" x-text="result">
          No sighting recorded yet.
        </p>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "submit_attrs": {
                "name": "observation_action",
                "value": "field journal",
            }
        }

    css = """
      :where(.button-form) {
        max-width: 34rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bbd6c5, #355e48);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-form header) {
        margin-block-end: 1rem;
      }

      :where(.button-form h2, .button-form p) {
        margin-block: 0;
      }

      :where(.button-form header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-form form) {
        display: grid;
        gap: 0.65rem;
      }

      :where(.button-form label) {
        font-weight: 650;
      }

      :where(.button-form input) {
        box-sizing: border-box;
        inline-size: 100%;
        min-block-size: 2.5rem;
        padding: 0.55rem 0.7rem;
        border: 1px solid color-mix(in srgb, currentColor 32%, transparent);
        border-radius: 0.5rem;
        background: Field;
        color: FieldText;
        font: inherit;
      }

      :where(.button-form form > div) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.65rem;
        margin-block-start: 0.35rem;
      }

      :where(.button-form__result) {
        margin-block-start: 1rem;
        color: color-mix(in srgb, currentColor 72%, transparent);
      }
    """


preview = ButtonNativeForms()

preview  # noqa: B018
````


Supported native attributes include `name`, `value`, `form`, `formaction`,
`formenctype`, `formmethod`, `formnovalidate`, and `formtarget`. Listen to native
`click`, `submit`, and `reset` events with Alpine. `CButton` does not duplicate
them with component callbacks or custom DOM events.

Form attributes and `type="submit"` or `type="reset"` are incompatible with
`href`. Use a Button for form actions and a link for navigation.

Without JavaScript, server-disabled and server-loading Buttons both render with
native `disabled`. Submit and reset Buttons otherwise keep native behavior.

## Theme and customize Button

Button follows the surrounding `color-scheme`. Set documented
`--cui-button-*` variables on an ancestor or one root. Use public
`data-citry-ui-part` selectors for targeted element styling.


### Theme Button

[Open the rendered preview](/v/0.4.6/ui-library/components/button/_previews/theme-customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonThemeCustomization(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="button-theme">
        <article class="button-theme__card button-theme__card--day">
          <header>
            <p>Day garden</p>
            <h2>Herbarium walk</h2>
          </header>
          <c-CButton>
            Follow sunlit path
          </c-CButton>
          <c-CButton variant="outline" c-attrs="rounded_attrs">
            Open plant index
          </c-CButton>
        </article>

        <article class="button-theme__card button-theme__card--night">
          <header>
            <p>Night garden</p>
            <h2>After-dark blooms</h2>
          </header>
          <c-CButton>
            Watch moonflowers
          </c-CButton>
          <c-CButton variant="outline">
            Find fireflies
          </c-CButton>
        </article>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "rounded_attrs": {
                "style": "--cui-button-radius: 999px;",
            }
        }

    css = """
      :where(.button-theme) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-theme__card) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid;
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.button-theme__card header) {
        flex-basis: 100%;
        margin-block-end: 0.25rem;
      }

      :where(.button-theme__card h2, .button-theme__card p) {
        margin-block: 0;
      }

      :where(.button-theme__card header p) {
        margin-block-end: 0.35rem;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-theme__card--day) {
        --cui-button-background: #166534;
        --cui-button-foreground: #ffffff;
        --cui-button-border-color: #166534;
        --cui-button-hover-background: #14532d;
        --cui-button-active-background: #052e16;
        --cui-button-focus-color: #7c3aed;
        color-scheme: light;
        border-color: #bbd6c5;
      }

      :where(.button-theme__card--day header p) {
        color: #166534;
      }

      :where(.button-theme__card--night) {
        --cui-button-background: #a7f3d0;
        --cui-button-foreground: #052e16;
        --cui-button-border-color: #6ee7b7;
        --cui-button-hover-background: #6ee7b7;
        --cui-button-active-background: #34d399;
        --cui-button-focus-color: #f0abfc;
        color-scheme: dark;
        border-color: #355e48;
      }

      :where(.button-theme__card--night header p) {
        color: #6ee7b7;
      }

      :where(.button-theme__card--night [data-citry-ui-part="content"]) {
        letter-spacing: 0.025em;
      }
    """


preview = ButtonThemeCustomization()

preview  # noqa: B018
````



```css
.garden-actions {
  --cui-button-background: #166534;
  --cui-button-foreground: #ffffff;
  --cui-button-hover-background: #14532d;
  --cui-button-focus-color: #7c3aed;
}

.garden-actions [data-citry-ui-part="content"] {
  letter-spacing: 0.025em;
}
```


The documented variables, parts, and reflected attributes are public CSS API.
`.cui-*` classes and `--_cui-*` variables are private.

## Accessibility and keyboard behavior

The native Button supplies action and form semantics; the native anchor
supplies navigation and link semantics. Default content or consumer ARIA
attributes must provide an accessible name. Focus-visible and forced-colors
treatments remain visible.

Minimum heights are 2.25rem, 2.5rem, and 2.75rem for `sm`, `md`, and `lg`.
The surrounding layout remains responsible for additional target spacing
required by its context.

## API reference

### Inputs

#### CButton server inputs

Server inputs are passed in a template through `<c-CButton ... />` or in Python through
`CButton(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="button-input-cbutton-server-inputs-type"></span>`type` | `"button" | "submit" | "reset"` ([`CButtonType`](#button-interface-input-type-aliases-cbutton-type)) | `"button"` | Selects native action Button behavior. It must remain `button` when `href` is set. |
| <span id="button-input-cbutton-server-inputs-href"></span>`href` | `str | None` | `None` | Renders a native link when set. Omit it to render a native action Button. |
| <span id="button-input-cbutton-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables the action Button or makes the link inert and blocks activation; a disabled enclosing CForm always wins. |
| <span id="button-input-cbutton-server-inputs-loading"></span>`loading` | `bool` | `False` | Marks the action busy and blocks new activation while retaining focus after client activation. |
| <span id="button-input-cbutton-server-inputs-variant"></span>`variant` | `"solid" | "outline" | "ghost"` ([`CButtonVariant`](#button-interface-input-type-aliases-cbutton-variant)) | `"solid"` | Selects presentation strength. |
| <span id="button-input-cbutton-server-inputs-intent"></span>`intent` | `"primary" | "neutral" | "success" | "warn" | "danger"` ([`CButtonIntent`](#button-interface-input-type-aliases-cbutton-intent)) | `"primary"` | Selects the semantic color role. |
| <span id="button-input-cbutton-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CButtonSize`](#button-interface-input-type-aliases-cbutton-size)) | `"md"` | Sets height, spacing, and text size. |
| <span id="button-input-cbutton-server-inputs-block"></span>`block` | `bool` | `False` | Fills the available inline size. |
| <span id="button-input-cbutton-server-inputs-loading-pos"></span>`loading_pos` | `"start" | "center" | "end"` ([`CButtonLoadingPos`](#button-interface-input-type-aliases-cbutton-loading-pos)) | `"center"` | Replaces the matching visual position while loading. Center replaces all ordinary visual content. |
| <span id="button-input-cbutton-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#button-interface-input-type-aliases-class-value)) | `None` | Adds root classes from a string, conditional mapping, or nested sequence and merges them with `attrs`. |
| <span id="button-input-cbutton-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#button-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles from CSS text, a property mapping, or a nested sequence and merges them with `attrs`. |
| <span id="button-input-cbutton-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native root, ARIA, Alpine, and data attributes. It may also contribute class and style values; prefer the top-level inputs for those. Form attributes apply only without `href`; link attributes such as `target`, `rel`, and `download` apply with `href`. |

</div>

#### CButton client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CButton />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="button-input-cbutton-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls local disabled state for action Buttons and links; a disabled enclosing CForm always wins and updates native state, `aria-disabled`, activation, and `data-disabled`. |
| <span id="button-input-cbutton-client-inputs-loading"></span>`loading` | `boolean` | Uses the server input. | Controls busy semantics, visual replacement, indicator visibility, activation, and `data-loading`. |
| <span id="button-input-cbutton-client-inputs-variant"></span>`variant` | `"solid" | "outline" | "ghost"` ([`CButtonVariant`](#button-interface-input-type-aliases-cbutton-variant)) | Uses the server input. | Controls `data-variant` and presentation. |
| <span id="button-input-cbutton-client-inputs-intent"></span>`intent` | `"primary" | "neutral" | "success" | "warn" | "danger"` ([`CButtonIntent`](#button-interface-input-type-aliases-cbutton-intent)) | Uses the server input. | Controls `data-intent` and colors. |
| <span id="button-input-cbutton-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CButtonSize`](#button-interface-input-type-aliases-cbutton-size)) | Uses the server input. | Controls `data-size` and geometry. |
| <span id="button-input-cbutton-client-inputs-block"></span>`block` | `boolean` | Uses the server input. | Controls `data-block` and inline sizing. |
| <span id="button-input-cbutton-client-inputs-loading-position"></span>`loadingPosition` | `"start" | "center" | "end"` ([`CButtonLoadingPos`](#button-interface-input-type-aliases-cbutton-loading-pos)) | Uses the server input. | Controls `data-loading-position` and which ordinary visual content loading replaces. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CButton slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="button-slot-cbutton-slots-default"></span>`default` | yes | `{}` ([`CButtonDefaultSlotData`](#button-interface-cbutton-default-slot-data)) | none |
| <span id="button-slot-cbutton-slots-start"></span>`start` | no | `{}` ([`CButtonStartSlotData`](#button-interface-cbutton-start-slot-data)) | omitted |
| <span id="button-slot-cbutton-slots-end"></span>`end` | no | `{}` ([`CButtonEndSlotData`](#button-interface-cbutton-end-slot-data)) | omitted |
| <span id="button-slot-cbutton-slots-loading"></span>`loading` | no | `{}` ([`CButtonLoadingSlotData`](#button-interface-cbutton-loading-slot-data)) | Built-in compact CSS spinner. Supplied content is a compact visual indicator hidden from the accessibility tree. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CButton CSS variables

Apply these variables to `CButton` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="button-css-cbutton-css-variables-cui-button-background"></span>`--cui-button-background` | `color` | Resting background. | `Variant- and intent-derived color.` |
| <span id="button-css-cbutton-css-variables-cui-button-foreground"></span>`--cui-button-foreground` | `color` | Text and decoration. | `Derived contrast color.` |
| <span id="button-css-cbutton-css-variables-cui-button-border-color"></span>`--cui-button-border-color` | `color` | Resting border. | `Variant- and intent-derived color.` |
| <span id="button-css-cbutton-css-variables-cui-button-hover-background"></span>`--cui-button-hover-background` | `color` | Enabled hover background. | `Derived color mix.` |
| <span id="button-css-cbutton-css-variables-cui-button-active-background"></span>`--cui-button-active-background` | `color` | Enabled active background. | `Derived stronger color mix.` |
| <span id="button-css-cbutton-css-variables-cui-button-focus-color"></span>`--cui-button-focus-color` | `color` | Focus outline. | `Highlight` |
| <span id="button-css-cbutton-css-variables-cui-button-radius"></span>`--cui-button-radius` | `length` | Corner radius. | `0.5rem` |
| <span id="button-css-cbutton-css-variables-cui-button-font-weight"></span>`--cui-button-font-weight` | `number` | Label weight. | `600` |
| <span id="button-css-cbutton-css-variables-cui-button-gap"></span>`--cui-button-gap` | `length` | Gap between content parts. | `0.5rem` |
| <span id="button-css-cbutton-css-variables-cui-button-disabled-opacity"></span>`--cui-button-disabled-opacity` | `number` | Disabled presentation opacity. | `0.48` |
| <span id="button-css-cbutton-css-variables-cui-button-height"></span>`--cui-button-height` | `length` | Minimum target height. | `Size-derived length.` |
| <span id="button-css-cbutton-css-variables-cui-button-inline-padding"></span>`--cui-button-inline-padding` | `length` | Logical inline padding. | `Size-derived length.` |
| <span id="button-css-cbutton-css-variables-cui-button-block-padding"></span>`--cui-button-block-padding` | `length` | Logical block padding. | `Size-derived length.` |
| <span id="button-css-cbutton-css-variables-cui-button-font-size"></span>`--cui-button-font-size` | `length` | Label size. | `Size-derived length.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CButton attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="button-attribute-cbutton-attributes-data-loading"></span>`data-loading` | Native root | `present | absent` | Mirrors effective loading state. |
| <span id="button-attribute-cbutton-attributes-data-disabled"></span>`data-disabled` | Native root | `present | absent` | Mirrors effective disabled state. |
| <span id="button-attribute-cbutton-attributes-data-variant"></span>`data-variant` | Native root | `"solid" | "outline" | "ghost"` | Mirrors effective presentation variant. |
| <span id="button-attribute-cbutton-attributes-data-intent"></span>`data-intent` | Native root | `"primary" | "neutral" | "success" | "warn" | "danger"` | Mirrors effective semantic color role. |
| <span id="button-attribute-cbutton-attributes-data-size"></span>`data-size` | Native root | `"sm" | "md" | "lg"` | Mirrors effective size. |
| <span id="button-attribute-cbutton-attributes-data-block"></span>`data-block` | Native root | `present | absent` | Mirrors full-width layout. |
| <span id="button-attribute-cbutton-attributes-data-loading-position"></span>`data-loading-position` | Native root | `"start" | "center" | "end"` | Mirrors effective loading-content position. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CButton selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="button-selector-cbutton-selectors-data-citry-ui-part-button"></span>`[data-citry-ui-part="button"]` | Native root | Button or link root and `attrs` destination. |
| <span id="button-selector-cbutton-selectors-data-citry-ui-part-start"></span>`[data-citry-ui-part="start"]` | Leading wrapper | Leading content hook. |
| <span id="button-selector-cbutton-selectors-data-citry-ui-part-content"></span>`[data-citry-ui-part="content"]` | Content wrapper | Required label and content hook. |
| <span id="button-selector-cbutton-selectors-data-citry-ui-part-end"></span>`[data-citry-ui-part="end"]` | Trailing wrapper | Trailing content hook. |
| <span id="button-selector-cbutton-selectors-data-citry-ui-part-loading-indicator"></span>`[data-citry-ui-part="loading-indicator"]` | Loading wrapper | Stable loading-content hook. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="button-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="button-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="button-interface-input-type-aliases-cbutton-type"></span>`CButtonType` | `Literal["button", "submit", "reset"]` |
| <span id="button-interface-input-type-aliases-cbutton-variant"></span>`CButtonVariant` | `Literal["solid", "outline", "ghost"]` |
| <span id="button-interface-input-type-aliases-cbutton-intent"></span>`CButtonIntent` | `Literal["primary", "neutral", "success", "warn", "danger"]` |
| <span id="button-interface-input-type-aliases-cbutton-size"></span>`CButtonSize` | `Literal["sm", "md", "lg"]` |
| <span id="button-interface-input-type-aliases-cbutton-loading-pos"></span>`CButtonLoadingPos` | `Literal["start", "center", "end"]` |

</div>

<span id="button-interface-cbutton-default-slot-data"></span>

#### `CButtonDefaultSlotData`

Empty dataclass: `{}`.

<span id="button-interface-cbutton-start-slot-data"></span>

#### `CButtonStartSlotData`

Empty dataclass: `{}`.

<span id="button-interface-cbutton-end-slot-data"></span>

#### `CButtonEndSlotData`

Empty dataclass: `{}`.

<span id="button-interface-cbutton-loading-slot-data"></span>

#### `CButtonLoadingSlotData`

Empty dataclass: `{}`.

### Translation keys

-