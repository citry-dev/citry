---
title: Tabs
url: https://citry.dev/v/0.4.0/ui-library/components/tabs/
description: "Organize keyboard-accessible views with Citry UI Tabs."
---
# Tabs

Switch between related views in place. `CTabs`, `CTab`, and `CTabPanel`
provide the ARIA structure, roving focus, activation modes, and controlled
selection.

## Tabs at a glance

Compare underline and pill treatments. Click a Tab or use the arrow keys. The
disabled **Crew** Tab shows the unavailable state.


### Tabs at a glance

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsAtAGlance(Component):
    template = """
      <section class="tabs-sampler">
        <article class="tabs-sampler__card tabs-sampler__card--cosmic">
          <header>
            <p class="tabs-sampler__eyebrow">Deep-space radio</p>
            <h2>Europa Relay</h2>
          </header>

          <c-CTabs
            default_value="signals"
            aria_label="Europa Relay channels"
          >
            <c-CTab value="broadcast">
              Broadcast
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>
            <c-CTab value="crew" disabled>
              Crew
            </c-CTab>

            <c-CTabPanel value="broadcast">
              <p>Now transmitting: a mixtape for whatever is out there.</p>
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              <div class="tabs-sampler__metric">
                <strong>A repeating pulse crossed 1,200 light-years</strong>
                <span>Three notes, a pause, then whale song.</span>
              </div>
            </c-CTabPanel>
            <c-CTabPanel value="crew">
              <p>This relay is delightfully uncrewed.</p>
            </c-CTabPanel>
          </c-CTabs>
        </article>

        <article class="tabs-sampler__card tabs-sampler__card--greenhouse">
          <header>
            <p class="tabs-sampler__eyebrow">Lunar greenhouse</p>
            <h2>Habitat Seven</h2>
          </header>

          <c-CTabs
            default_value="crops"
            aria_label="Lunar greenhouse readings"
            variant="pill"
            density="comfortable"
            grow
          >
            <c-CTab value="crops">
              Crops
            </c-CTab>
            <c-CTab value="climate">
              Climate
            </c-CTab>
            <c-CTab value="supplies">
              Supplies
            </c-CTab>

            <c-CTabPanel value="crops">
              <div class="tabs-sampler__metric">
                <strong>Leafy greens are thriving</strong>
                <span>The blue-spectrum lamps run for six more hours.</span>
              </div>
            </c-CTabPanel>
            <c-CTabPanel value="climate">
              <p>Humidity is holding at 62% during the daylight cycle.</p>
            </c-CTabPanel>
            <c-CTabPanel value="supplies">
              <p>The next seed-vault delivery arrives in three orbits.</p>
            </c-CTabPanel>
          </c-CTabs>
        </article>
      </section>
    """

    css = """
      :where(.tabs-sampler) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-sampler__card) {
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid;
        border-radius: 0.875rem;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.tabs-sampler__card--cosmic) {
        --cui-tabs-accent: light-dark(#5b21b6, #ddd6fe);
        --cui-tabs-focus-color: light-dark(#6d28d9, #c4b5fd);
        --cui-tabs-active-background: light-dark(#ffffffb8, #2e1065b8);
        border-color: light-dark(#c4b5fd, #6d28d9);
        background: Canvas;
      }

      :where(.tabs-sampler__card--greenhouse) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
        --cui-tabs-active-background: light-dark(#f0fdf4cc, #042f2ecc);
        border-color: light-dark(#5eead4, #0f766e);
        background: Canvas;
      }

      :where(.tabs-sampler__card header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-sampler__card h2, .tabs-sampler__card p) {
        margin-block: 0;
      }

      :where(.tabs-sampler__eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
      }

      :where(.tabs-sampler__metric) {
        display: grid;
        gap: 0.25rem;
      }

      :where(.tabs-sampler__metric span) {
        color: color-mix(in srgb, currentColor 72%, transparent);
      }
    """


preview = TabsAtAGlance()

preview  # noqa: B018
````


## Compose Tabs, Tab controls, and Panels

Compose one `CTabs` root from matching `CTab` and `CTabPanel` declarations.


### Night sky guide

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/night-sky-guide/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NightSkyGuide(Component):
    template = """
      <section
        class="night-sky-guide"
        x-data="{ selected: 'planets' }"
      >
        <header>
          <p class="night-sky-guide__eyebrow">Field guide</p>
          <h2>The night sky</h2>
          <p>
            Current topic:
            <output x-text="selected">planets</output>
          </p>
        </header>

        <c-CTabs
          default_value="planets"
          aria_label="Night sky topics"
          variant="pill"
          grow
          $c-props="{
            onValueChange: (value) => {
              selected = value;
            },
          }"
        >
          <c-CTab value="planets">
            Planets
          </c-CTab>
          <c-CTab value="nebulae">
            Nebulae
          </c-CTab>
          <c-CTab value="galaxies">
            Galaxies
          </c-CTab>

          <c-CTabPanel value="planets">
            <h3>Finding planets</h3>
            <p>Look for steady points of light. Planets usually twinkle less than stars.</p>
          </c-CTabPanel>
          <c-CTabPanel value="nebulae">
            <h3>Finding nebulae</h3>
            <p>Dark skies and a telescope reveal clouds of gas and dust.</p>
          </c-CTabPanel>
          <c-CTabPanel value="galaxies">
            <h3>Finding galaxies</h3>
            <p>From a dark site, the Andromeda Galaxy is visible without a telescope.</p>
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.night-sky-guide) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        --cui-tabs-active-background: light-dark(#eef2ff, #1e1b4b);
        max-width: 44rem;
        padding: 1.5rem;
        border: 1px solid light-dark(#a5b4fc, #4338ca);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
        box-shadow: 0 1rem 2.5rem rgb(15 23 42 / 12%);
      }

      :where(.night-sky-guide header) {
        margin-block-end: 1.25rem;
      }

      :where(.night-sky-guide h2, .night-sky-guide h3, .night-sky-guide p) {
        margin-block: 0 0.5rem;
      }

      :where(.night-sky-guide__eyebrow) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.night-sky-guide output) {
        font-weight: 700;
      }
    """


preview = NightSkyGuide()

preview  # noqa: B018
````



```citry-html
<c-CTabs
  default_value="planets"
  aria_label="Night sky topics"
>
  <c-CTab value="planets">
    Planets
  </c-CTab>
  <c-CTab value="nebulae">
    Nebulae
  </c-CTab>

  <c-CTabPanel value="planets">
    Worlds orbiting stars
  </c-CTabPanel>
  <c-CTabPanel value="nebulae">
    Clouds of gas and dust
  </c-CTabPanel>
</c-CTabs>
```


Each component has one job:

- `CTabs` owns selection and configuration, renders the root and the single
  accessibly named `role="tablist"`, and groups the generated controls.
- `CTab` declares one value and its native Tab Button content.
- `CTabPanel` declares the view paired with that value.

Place the Tab declarations first, followed by their matching Panels. Tab
values are non-empty and unique, Panel values are non-empty and unique, and
both value sets must match. The initial value must identify an enabled Tab.
Provide either `aria_label` or `aria_labelledby` on `CTabs` to name the
generated Tab list.

`CTab` and `CTabPanel` are declarations, not standalone rendered components.
`CTabs` collects them before it renders the final Tab list and Panels. Using a
declaration outside `CTabs` fails. The default slot may contain formatting
whitespace, control flow, and transparent components, but no other rendered
HTML. This lets `CTabs` generate one correct semantic list without asking you
to maintain a structural-only list component.

## Try the configuration

Change accent, variant, density, orientation, alignment, growth, focus looping,
and disabled state. The controls use public CSS variables and `$c-props`.


### Configure Tabs

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/configuration/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsConfiguration(Component):
    template = """
      <section
        class="tabs-configurator"
        x-data="{
          selected: 'mercury',
          accent: 'violet',
          accents: {
            violet: 'light-dark(#6d28d9, #c4b5fd)',
            coral: 'light-dark(#c2410c, #fdba74)',
            teal: 'light-dark(#0f766e, #5eead4)',
            pink: 'light-dark(#be185d, #f9a8d4)',
          },
          variant: 'underline',
          density: 'default',
          orientation: 'horizontal',
          align: 'start',
          grow: false,
          loop: true,
          disabled: false,
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
        :style="{
          '--cui-tabs-accent': accents[accent],
          '--cui-tabs-focus-color': accents[accent],
        }"
      >
        <header>
          <p class="tabs-configurator__eyebrow">Pocket reference</p>
          <h2>Solar system field guide</h2>
        </header>

        <div class="tabs-configurator__stage">
          <p class="tabs-configurator__status" aria-live="polite">
            Current world:
            <strong x-text="selected">mercury</strong>
          </p>

          <c-CTabs
            default_value="mercury"
            aria_label="Solar system chapters"
            $c-props="{
              variant,
              density,
              orientation,
              align,
              grow,
              loop,
              disabled,
              onValueChange: (value) => {
                selected = value;
              },
            }"
          >
            <c-CTab value="mercury">
              Mercury
            </c-CTab>
            <c-CTab value="europa">
              Europa
            </c-CTab>
            <c-CTab value="titan">
              Titan
            </c-CTab>

            <c-CTabPanel value="mercury">
              <h3>Mercury</h3>
              <p>A cratered world with sharp swings between day and night.</p>
            </c-CTabPanel>
            <c-CTabPanel value="europa">
              <h3>Europa</h3>
              <p>An icy moon with evidence of a vast ocean beneath its surface.</p>
            </c-CTabPanel>
            <c-CTabPanel value="titan">
              <h3>Titan</h3>
              <p>A hazy moon with rivers and lakes of liquid methane.</p>
            </c-CTabPanel>
          </c-CTabs>
        </div>
      </section>
    """

    css = """
      :where(.tabs-configurator) {
        max-width: 64rem;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 54%, transparent);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.tabs-configurator > header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-configurator h2, .tabs-configurator h3, .tabs-configurator p) {
        margin-block: 0 0.5rem;
      }

      :where(.tabs-configurator__eyebrow) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.tabs-configurator__stage) {
        min-width: 0;
      }

      :where(.tabs-configurator__status) {
        color: color-mix(in srgb, currentColor 72%, transparent);
      }
    """


preview_controls = (
    {
        "name": "accent",
        "label": "Accent",
        "type": "select",
        "default": "violet",
        "options": (
            ("violet", "Violet"),
            ("coral", "Coral"),
            ("teal", "Teal"),
            ("pink", "Pink"),
        ),
    },
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "underline",
        "options": (("underline", "Underline"), ("pill", "Pill")),
    },
    {
        "name": "density",
        "label": "Density",
        "type": "select",
        "default": "default",
        "options": (
            ("default", "Default"),
            ("comfortable", "Comfortable"),
            ("compact", "Compact"),
        ),
    },
    {
        "name": "orientation",
        "label": "Orientation",
        "type": "select",
        "default": "horizontal",
        "options": (("horizontal", "Horizontal"), ("vertical", "Vertical")),
    },
    {
        "name": "align",
        "label": "Alignment",
        "type": "select",
        "default": "start",
        "options": (("start", "Start"), ("center", "Center"), ("end", "End")),
    },
    {
        "name": "grow",
        "label": "Grow to fill space",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "loop",
        "label": "Loop keyboard focus",
        "type": "checkbox",
        "default": True,
    },
    {
        "name": "disabled",
        "label": "Disable all Tabs",
        "type": "checkbox",
        "default": False,
    },
)

preview = TabsConfiguration()

preview  # noqa: B018
````


## Choose a variant

Use `underline` for low-emphasis navigation. Use `pill` when the choices need a
contained track and stronger selected state.


### Compare Tabs variants

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsVariants(Component):
    template = """
      <section class="tabs-variants">
        <article class="tabs-variants__card">
          <header>
            <p class="tabs-eyebrow">Low-emphasis navigation</p>
            <h2>Underline</h2>
          </header>

          <c-CTabs
            default_value="surface"
            aria_label="Underline Mars topics"
            variant="underline"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="weather">
              Weather
            </c-CTab>

            <c-CTabPanel value="orbit">
              Mars completes one orbit in roughly 687 Earth days.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Iron minerals give the surface its familiar red color.
            </c-CTabPanel>
            <c-CTabPanel value="weather">
              Thin clouds and planet-wide dust storms shape the sky.
            </c-CTabPanel>
          </c-CTabs>
        </article>

        <article class="tabs-variants__card tabs-variants__card--pill">
          <header>
            <p>Contained choices</p>
            <h2>Pill</h2>
          </header>

          <c-CTabs
            default_value="surface"
            aria_label="Pill Mars topics"
            variant="pill"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="weather">
              Weather
            </c-CTab>

            <c-CTabPanel value="orbit">
              Mars completes one orbit in roughly 687 Earth days.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Iron minerals give the surface its familiar red color.
            </c-CTabPanel>
            <c-CTabPanel value="weather">
              Thin clouds and planet-wide dust storms shape the sky.
            </c-CTabPanel>
          </c-CTabs>
        </article>
      </section>
    """

    css = """
      :where(.tabs-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-variants__card) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.tabs-variants__card--pill) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
        --cui-tabs-active-background: light-dark(#f0fdfa, #042f2e);
      }

      :where(.tabs-variants__card header) {
        margin-block-end: 0.75rem;
      }

      :where(.tabs-variants__card h2, .tabs-variants__card p) {
        margin-block: 0;
        margin-bottom: 0.5rem;
      }

      :where(.tabs-variants__card header p) {
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
    """


preview = TabsVariants()

preview  # noqa: B018
````


## Set density and available width

`default`, `comfortable`, and `compact` change Tab height and padding. Enable
equal width when every Tab should share the available main-axis space.


### Compare density and growth

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/density-and-growth/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsDensityAndGrowth(Component):
    template = """
      <section
        class="tabs-density"
        x-data="{ grow: false }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <div class="tabs-density__row">
          <h2>Default</h2>
          <c-CTabs
            default_value="orbit"
            aria_label="Default-density telescope views"
            density="default"
            $c-props="{ grow }"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>

            <c-CTabPanel value="orbit">
              Track the object's path across the sky.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Compare reflected-light surface features.
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              Review the latest radio observations.
            </c-CTabPanel>
          </c-CTabs>
        </div>

        <div class="tabs-density__row">
          <h2>Comfortable</h2>
          <c-CTabs
            default_value="orbit"
            aria_label="Comfortable-density telescope views"
            density="comfortable"
            $c-props="{ grow }"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>

            <c-CTabPanel value="orbit">
              Track the object's path across the sky.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Compare reflected-light surface features.
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              Review the latest radio observations.
            </c-CTabPanel>
          </c-CTabs>
        </div>

        <div class="tabs-density__row">
          <h2>Compact</h2>
          <c-CTabs
            default_value="orbit"
            aria_label="Compact-density telescope views"
            density="compact"
            $c-props="{ grow }"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>

            <c-CTabPanel value="orbit">
              Track the object's path across the sky.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Compare reflected-light surface features.
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              Review the latest radio observations.
            </c-CTabPanel>
          </c-CTabs>
        </div>
      </section>
    """

    css = """
      :where(.tabs-density) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        display: grid;
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-density__row) {
        display: grid;
        grid-template-columns: 7rem minmax(0, 1fr);
        gap: 1rem;
        align-items: start;
        min-width: 0;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, currentColor 16%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.tabs-density__row h2) {
        margin-block: 0.65rem 0;
        color: color-mix(in srgb, currentColor 72%, transparent);
        font-size: 0.875rem;
      }

      @media (max-width: 34rem) {
        :where(.tabs-density__row) {
          grid-template-columns: minmax(0, 1fr);
        }

        :where(.tabs-density__row h2) {
          margin-block: 0;
        }
      }
    """


preview_controls = (
    {
        "name": "grow",
        "label": "Make Tabs equal width",
        "type": "checkbox",
        "default": False,
    },
)

preview = TabsDensityAndGrowth()

preview  # noqa: B018
````


## Align and orient Tabs

Alignment follows the main axis. Vertical orientation moves the Tab list beside
the active Panel and switches keyboard movement to Up and Down.


### Align and orient Tabs

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/alignment-and-orientation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsAlignmentAndOrientation(Component):
    template = """
      <section
        class="tabs-layout"
        x-data="{ align: 'start', orientation: 'horizontal' }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p class="tabs-eyebrow">Observatory catalog</p>
          <h2>Targets for tonight</h2>
        </header>

        <c-CTabs
          default_value="planets"
          aria_label="Observatory target categories"
          $c-props="{ align, orientation }"
        >
          <c-CTab value="stars">
            Stars
          </c-CTab>
          <c-CTab value="planets">
            Planets
          </c-CTab>
          <c-CTab value="nebulae">
            Nebulae
          </c-CTab>

          <c-CTabPanel value="stars">
            Compare color, brightness, and spectral class.
          </c-CTabPanel>
          <c-CTabPanel value="planets">
            Follow bright worlds as they move against the stars.
          </c-CTabPanel>
          <c-CTabPanel value="nebulae">
            Find emission and reflection clouds in dark skies.
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.tabs-layout) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
        max-width: 52rem;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-layout header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-layout h2, .tabs-layout p) {
        margin-block: 0;
      }

      :where(.tabs-layout header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
      }
    """


preview_controls = (
    {
        "name": "orientation",
        "label": "Orientation",
        "type": "select",
        "default": "horizontal",
        "options": (("horizontal", "Horizontal"), ("vertical", "Vertical")),
    },
    {
        "name": "align",
        "label": "Alignment",
        "type": "select",
        "default": "start",
        "options": (("start", "Start"), ("center", "Center"), ("end", "End")),
    },
)

preview = TabsAlignmentAndOrientation()

preview  # noqa: B018
````


## Control selection from JavaScript

Supplying client `value` makes selection controlled. A user request calls
`onValueChange`; the owner decides whether to commit the requested value.


### Control Tabs selection

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/controlled-selection/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsControlledSelection(Component):
    template = """
      <section
        class="tabs-controlled"
        x-data="{
          current: 'mercury',
          requested: 'none',
          requestSource: 'none',
          applyRequests: true,
        }"
      >
        <header>
          <p>Owner-controlled selection</p>
          <h2>Planetary briefing</h2>
        </header>

        <div
          class="tabs-controlled__owner-actions"
          role="group"
          aria-label="Select a briefing"
        >
          <button type="button" @click="current = 'mercury'">
            Show Mercury
          </button>
          <button type="button" @click="current = 'europa'">
            Show Europa
          </button>
          <button type="button" @click="current = 'titan'">
            Show Titan
          </button>
        </div>

        <label class="tabs-controlled__commit">
          <input type="checkbox" x-model="applyRequests" />
          <span>Apply requests from Tabs</span>
        </label>

        <dl class="tabs-controlled__status" aria-live="polite">
          <div>
            <dt>Selected</dt>
            <dd x-text="current">mercury</dd>
          </div>
          <div>
            <dt>Last request</dt>
            <dd>
              <span x-text="requested">none</span>
              <span x-show="requestSource !== 'none'">
                via <span x-text="requestSource"></span>
              </span>
            </dd>
          </div>
        </dl>

        <c-CTabs
          default_value="mercury"
          aria_label="Planetary briefing topics"
          $c-props="{
            value: current,
            onValueChange: (value, detail) => {
              requested = value;
              requestSource = detail.source;
              if (applyRequests) {
                current = value;
              }
            },
          }"
        >
          <c-CTab value="mercury">
            Mercury
          </c-CTab>
          <c-CTab value="europa">
            Europa
          </c-CTab>
          <c-CTab value="titan">
            Titan
          </c-CTab>

          <c-CTabPanel value="mercury">
            Mercury has the shortest year of any planet.
          </c-CTabPanel>
          <c-CTabPanel value="europa">
            Europa's fractured ice may cover a deep ocean.
          </c-CTabPanel>
          <c-CTabPanel value="titan">
            Titan has a dense atmosphere rich in nitrogen.
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.tabs-controlled) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        display: grid;
        gap: 1rem;
        max-width: 48rem;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-controlled h2, .tabs-controlled p) {
        margin-block: 0;
      }

      :where(.tabs-controlled header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-controlled__owner-actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }

      :where(.tabs-controlled__owner-actions button) {
        min-height: 2.25rem;
        padding-inline: 0.75rem;
        border: 1px solid color-mix(in srgb, currentColor 24%, transparent);
        border-radius: 0.375rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
        cursor: pointer;
      }

      :where(.tabs-controlled__owner-actions button:focus-visible) {
        outline: 0.1875rem solid var(--cui-tabs-focus-color);
        outline-offset: 0.125rem;
      }

      :where(.tabs-controlled__commit) {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        width: fit-content;
      }

      :where(.tabs-controlled__commit input) {
        inline-size: 1rem;
        block-size: 1rem;
        margin: 0;
      }

      :where(.tabs-controlled__status) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem 1.5rem;
        margin: 0;
        padding: 0.75rem;
        border-radius: 0.5rem;
        background: color-mix(in srgb, currentColor 7%, transparent);
      }

      :where(.tabs-controlled__status div) {
        display: flex;
        gap: 0.375rem;
      }

      :where(.tabs-controlled__status dt) {
        color: color-mix(in srgb, currentColor 68%, transparent);
      }

      :where(.tabs-controlled__status dd) {
        margin: 0;
        font-weight: 700;
      }
    """


preview = TabsControlledSelection()

preview  # noqa: B018
````



```citry-html
<c-CTabs
  default_value="planets"
  aria_label="Night sky topics"
  $c-props="{
    value: currentTopic,
    onValueChange: (value, detail) => {
      currentTopic = value;
      observationLog.record(detail);
    },
  }"
>
  ...
</c-CTabs>
```


Omit client `value` for immediate uncontrolled selection. Removing a controlled
value continues uncontrolled from the last valid selection. An invalid value
keeps the last valid selection, reports a diagnostic, and still reports eligible
user requests.

Other supplied client inputs override their server inputs. Removing one restores
the server value. `null` is valid only for `direction`, where it restores
inherited browser direction. Other invalid values report a diagnostic and use
their server value.

!!! note
    `onValueChange` runs only for a different enabled value. Initial selection
    and owner updates do not run it. Return values do not cancel the request.

    If client-owned DOM work removes the selected Tab, Tabs selects the next
    enabled Tab at that position, then the previous enabled Tab, then the first
    enabled Tab. If none remains, all Tabs and Panels become inactive and the
    event does not run.

## Disable selection

Disable one `CTab` to keep it visible but unavailable. Disable `CTabs` to block
the whole group without losing the selected value.


### Disable Tabs

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/disabled-states/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsDisabledStates(Component):
    template = """
      <section
        class="tabs-disabled"
        x-data="{ group_disabled: false }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p class="tabs-eyebrow">Launch windows</p>
          <h2>Inner-planet missions</h2>
        </header>

        <c-CTabs
          default_value="mercury"
          aria_label="Inner-planet mission windows"
          variant="pill"
          grow
          $c-props="{ disabled: group_disabled }"
        >
          <c-CTab value="mercury">
            Mercury
          </c-CTab>
          <c-CTab value="venus" disabled>
            Venus
          </c-CTab>
          <c-CTab value="mars">
            Mars
          </c-CTab>

          <c-CTabPanel value="mercury">
            The next transfer study opens in September.
          </c-CTabPanel>
          <c-CTabPanel value="venus">
            No launch window is available for this mission profile.
          </c-CTabPanel>
          <c-CTabPanel value="mars">
            The next transfer study opens in November.
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.tabs-disabled) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        --cui-tabs-active-background: light-dark(#eef2ff, #1e1b4b);
        max-width: 44rem;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-disabled header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-disabled h2, .tabs-disabled p) {
        margin-block: 0;
      }

      :where(.tabs-disabled header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
      }
    """


preview_controls = (
    {
        "name": "group_disabled",
        "label": "Disable the whole group",
        "type": "checkbox",
        "default": False,
    },
)

preview = TabsDisabledStates()

preview  # noqa: B018
````


## Choose keyboard activation

Automatic activation selects as focus moves. Manual activation moves focus
first, then waits for Enter or Space.


### Compare keyboard activation

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/keyboard-activation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsKeyboardActivation(Component):
    template = """
      <section
        class="tabs-activation"
        x-data="{ automaticValue: 'orbit', manualValue: 'orbit' }"
      >
        <article class="tabs-activation__card">
          <header>
            <p class="tabs-eyebrow">Arrow keys select immediately</p>
            <h2>Automatic</h2>
            <output x-text="automaticValue">orbit</output>
          </header>

          <c-CTabs
            default_value="orbit"
            aria_label="Automatic probe data"
            activation="automatic"
            $c-props="{
              onValueChange: (value) => {
                automaticValue = value;
              },
            }"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>

            <c-CTabPanel value="orbit">
              The probe is completing its 18th orbit.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Surface imaging resumes after local sunrise.
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              The high-gain antenna is locked on Earth.
            </c-CTabPanel>
          </c-CTabs>
        </article>

        <article class="tabs-activation__card tabs-activation__card--manual">
          <header>
            <p class="tabs-eyebrow">Arrow keys move focus; Enter or Space selects</p>
            <h2>Manual</h2>
            <output x-text="manualValue">orbit</output>
          </header>

          <c-CTabs
            default_value="orbit"
            aria_label="Manual probe data"
            activation="manual"
            $c-props="{
              onValueChange: (value) => {
                manualValue = value;
              },
            }"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>

            <c-CTabPanel value="orbit">
              The probe is completing its 18th orbit.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Surface imaging resumes after local sunrise.
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              The high-gain antenna is locked on Earth.
            </c-CTabPanel>
          </c-CTabs>
        </article>
      </section>
    """

    css = """
      :where(.tabs-activation) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-activation__card) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.tabs-activation__card--manual) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
      }

      :where(.tabs-activation__card header) {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 0.125rem 0.75rem;
        align-items: end;
        margin-block-end: 0.75rem;
      }

      :where(.tabs-activation__card h2, .tabs-activation__card p) {
        margin-block: 0;
      }

      :where(.tabs-activation__card header p) {
        grid-column: 1 / -1;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.75rem;
      }

      :where(.tabs-activation__card output) {
        color: var(--cui-tabs-accent);
        font-weight: 700;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
    """


preview = TabsKeyboardActivation()

preview  # noqa: B018
````


| Context | Key | Result |
|---|---|---|
| Horizontal LTR | Right / Left | Focus next / previous enabled Tab. |
| Horizontal RTL | Right / Left | Focus previous / next enabled Tab. |
| Vertical | Down / Up | Focus next / previous enabled Tab. |
| Either | Home / End | Focus first / last enabled Tab. |
| Manual activation | Enter / Space | Select the focused Tab. |
| Automatic activation | Arrow, Home, or End focus movement | Focus and select together. |

Horizontal Tabs do not consume Up or Down. Vertical Tabs do not consume Left
or Right. Disabled Tabs are skipped, and `loop=False` stops movement at either
end. Pointer activation selects and focuses the clicked enabled Tab.

Each Tab is a native `button type="button"` with `role="tab"`,
`aria-controls`, `aria-selected`, and roving `tabindex`. Each Panel has
`role="tabpanel"`, `aria-labelledby`, and `tabindex="0"`. Panels remain mounted;
inactive Panels receive `hidden`.

Without JavaScript, the server-selected Panel remains visible and all ARIA
relationships are valid, but the Tab Buttons do not switch Panels.

## Use long Tab lists

Long horizontal lists scroll inside the Tab-list surface. Pointer and keyboard
selection bring the active Tab into view. Overflow arrows and menus are not part
of the current component.


### Scroll a long Tab list

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/long-list/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsLongList(Component):
    template = """
      <section class="tabs-overflow">
        <header>
          <p class="tabs-eyebrow">Seven survey programs</p>
          <h2>Planetary observation queue</h2>
        </header>

        <p class="tabs-overflow__hint">Scroll the Tab row to reach every survey.</p>

        <c-CTabs
          default_value="mercury"
          aria_label="Planetary observation programs"
          density="compact"
        >
          <c-CTab value="mercury">
            Mercury geology
          </c-CTab>
          <c-CTab value="venus">
            Venus cloud layers
          </c-CTab>
          <c-CTab value="earth">
            Earth magnetosphere
          </c-CTab>
          <c-CTab value="mars">
            Mars surface weather
          </c-CTab>
          <c-CTab value="jupiter">
            Jupiter storm systems
          </c-CTab>
          <c-CTab value="saturn">
            Saturn ring survey
          </c-CTab>
          <c-CTab value="outer-system">
            Outer-system objects
          </c-CTab>

          <c-CTabPanel value="mercury">
            Map fresh impact craters near Mercury's equator.
          </c-CTabPanel>
          <c-CTabPanel value="venus">
            Compare ultraviolet images of Venusian clouds.
          </c-CTabPanel>
          <c-CTabPanel value="earth">
            Follow changes in Earth's magnetic environment.
          </c-CTabPanel>
          <c-CTabPanel value="mars">
            Track dust and frost across the Martian surface.
          </c-CTabPanel>
          <c-CTabPanel value="jupiter">
            Measure wind patterns around Jupiter's largest storms.
          </c-CTabPanel>
          <c-CTabPanel value="saturn">
            Resolve fine structure within Saturn's rings.
          </c-CTabPanel>
          <c-CTabPanel value="outer-system">
            Search for faint objects beyond Neptune.
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.tabs-overflow) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        width: min(100%, 28rem);
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-overflow header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-overflow h2, .tabs-overflow p) {
        margin-block: 0;
      }

      :where(.tabs-overflow header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-overflow__hint) {
        margin-block: 0 0.5rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
    """


preview = TabsLongList()

preview  # noqa: B018
````


## Nest Tabs

Place nested Tabs inside a `CTabPanel`. Each root keeps independent selection,
focus, configuration, and callbacks.


### Nest Tabs

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/nested-tabs/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsNested(Component):
    template = """
      <section class="tabs-nested">
        <header>
          <p class="tabs-eyebrow">Outer and inner selection</p>
          <h2>Giant planets</h2>
        </header>

        <c-CTabs
          default_value="jupiter"
          aria_label="Giant planets"
        >
          <c-CTab value="jupiter">
            Jupiter
          </c-CTab>
          <c-CTab value="saturn">
            Saturn
          </c-CTab>

          <c-CTabPanel value="jupiter">
            <div class="tabs-nested__inner">
              <c-CTabs
                default_value="moons"
                aria_label="Jupiter topics"
                variant="pill"
                density="compact"
              >
                <c-CTab value="moons">
                  Moons
                </c-CTab>
                <c-CTab value="atmosphere">
                  Atmosphere
                </c-CTab>
                <c-CTab value="rings">
                  Rings
                </c-CTab>

                <c-CTabPanel value="moons">
                  Io, Europa, Ganymede, and Callisto are the largest moons.
                </c-CTabPanel>
                <c-CTabPanel value="atmosphere">
                  Bands of clouds circle a deep hydrogen-rich atmosphere.
                </c-CTabPanel>
                <c-CTabPanel value="rings">
                  Jupiter has a faint ring system made mostly of dust.
                </c-CTabPanel>
              </c-CTabs>
            </div>
          </c-CTabPanel>
          <c-CTabPanel value="saturn">
            Saturn's bright rings contain countless pieces of ice and rock.
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.tabs-nested) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        max-width: 52rem;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-nested > header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-nested h2, .tabs-nested p) {
        margin-block: 0;
      }

      :where(.tabs-nested > header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-nested__inner) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
        --cui-tabs-active-background: light-dark(#f0fdfa, #042f2e);
        padding: 0.75rem;
        border: 1px solid color-mix(in srgb, currentColor 14%, transparent);
        border-radius: 0.625rem;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
    """


preview = TabsNested()

preview  # noqa: B018
````



```citry-html
<c-CTabPanel value="jupiter">
  <c-CTabs
    default_value="moons"
    aria_label="Jupiter topics"
  >
    ...
  </c-CTabs>
</c-CTabPanel>
```


A Tab and Panel block access to their parent's Tabs context. Rendering Tabs
inside a Tab fails because native Buttons cannot contain interactive content. A
nested root also cannot sit directly among another root's declarations.

## Support text direction

Horizontal arrow keys follow visual direction. In RTL, Right moves toward the
previous declared Tab and Left moves toward the next. Vertical movement is
unchanged.


### Compare LTR and RTL Tabs

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/direction/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsDirection(Component):
    template = """
      <section class="tabs-direction">
        <article class="tabs-direction__card" dir="ltr" lang="en">
          <header>
            <p class="tabs-eyebrow">Left to right</p>
            <h2>Inner planets</h2>
          </header>

          <c-CTabs
            default_value="mercury"
            aria_label="Inner planets in English"
            direction="ltr"
          >
            <c-CTab value="mercury">
              Mercury
            </c-CTab>
            <c-CTab value="venus">
              Venus
            </c-CTab>
            <c-CTab value="earth">
              Earth
            </c-CTab>

            <c-CTabPanel value="mercury">
              The closest planet to the Sun.
            </c-CTabPanel>
            <c-CTabPanel value="venus">
              The second planet from the Sun.
            </c-CTabPanel>
            <c-CTabPanel value="earth">
              Our home in the solar system.
            </c-CTabPanel>
          </c-CTabs>
        </article>

        <article class="tabs-direction__card tabs-direction__card--rtl" dir="rtl" lang="ar">
          <header>
            <p class="tabs-eyebrow">من اليمين إلى اليسار</p>
            <h2>الكواكب الداخلية</h2>
          </header>

          <c-CTabs
            default_value="mercury"
            aria_label="الكواكب الداخلية بالعربية"
            direction="rtl"
            c-attrs="{'lang': 'ar'}"
          >
            <c-CTab value="mercury">
              عطارد
            </c-CTab>
            <c-CTab value="venus">
              الزهرة
            </c-CTab>
            <c-CTab value="earth">
              الأرض
            </c-CTab>

            <c-CTabPanel value="mercury">
              الكوكب الأقرب إلى الشمس.
            </c-CTabPanel>
            <c-CTabPanel value="venus">
              ثاني كوكب من الشمس.
            </c-CTabPanel>
            <c-CTabPanel value="earth">
              موطننا في النظام الشمسي.
            </c-CTabPanel>
          </c-CTabs>
        </article>
      </section>
    """

    css = """
      :where(.tabs-direction) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-direction__card) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.tabs-direction__card--rtl) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
      }

      :where(.tabs-direction__card header) {
        margin-block-end: 0.75rem;
      }

      :where(.tabs-direction__card h2, .tabs-direction__card p) {
        margin-block: 0;
      }

      :where(.tabs-direction__card header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
    """


preview = TabsDirection()

preview  # noqa: B018
````


Set server `direction` to `ltr` or `rtl`, or leave it unset to inherit computed
browser direction. Client `direction: null` explicitly restores inheritance.

## Theme and customize Tabs

Tabs follow the surrounding `color-scheme`. Set documented `--cui-tabs-*`
variables on an ancestor or one Tabs root to customize color and geometry.


### Theme Tabs

[Open the rendered preview](/v/0.4.0/ui-library/components/tabs/_previews/theme-customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsThemeCustomization(Component):
    template = """
      <section class="tabs-theme">
        <article class="tabs-theme__card tabs-theme__card--light">
          <header>
            <p class="tabs-eyebrow">Light surface</p>
            <h2>Lunar atlas</h2>
          </header>

          <c-CTabs
            default_value="maria"
            aria_label="Light lunar atlas"
            variant="pill"
          >
            <c-CTab value="maria">
              Maria
            </c-CTab>
            <c-CTab value="craters">
              Craters
            </c-CTab>
            <c-CTab value="highlands">
              Highlands
            </c-CTab>

            <c-CTabPanel value="maria">
              Dark plains formed by ancient volcanic flows.
            </c-CTabPanel>
            <c-CTabPanel value="craters">
              Impact basins record billions of years of history.
            </c-CTabPanel>
            <c-CTabPanel value="highlands">
              Bright, heavily cratered terrain covers much of the Moon.
            </c-CTabPanel>
          </c-CTabs>
        </article>

        <article class="tabs-theme__card tabs-theme__card--dark">
          <header>
            <p class="tabs-eyebrow">Dark surface</p>
            <h2>Lunar atlas</h2>
          </header>

          <c-CTabs
            default_value="maria"
            aria_label="Dark lunar atlas"
            variant="pill"
          >
            <c-CTab value="maria">
              Maria
            </c-CTab>
            <c-CTab value="craters">
              Craters
            </c-CTab>
            <c-CTab value="highlands">
              Highlands
            </c-CTab>

            <c-CTabPanel value="maria">
              Dark plains formed by ancient volcanic flows.
            </c-CTabPanel>
            <c-CTabPanel value="craters">
              Impact basins record billions of years of history.
            </c-CTabPanel>
            <c-CTabPanel value="highlands">
              Bright, heavily cratered terrain covers much of the Moon.
            </c-CTabPanel>
          </c-CTabs>
        </article>
      </section>
    """

    css = """
      :where(.tabs-theme) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-theme__card) {
        --cui-tabs-accent: #1d4ed8;
        --cui-tabs-border-color: #bfdbfe;
        --cui-tabs-muted-color: #475569;
        --cui-tabs-list-background: #eff6ff;
        --cui-tabs-active-background: #ffffff;
        --cui-tabs-hover-background: #dbeafe;
        --cui-tabs-focus-color: #7c3aed;
        --cui-tabs-radius: 0.75rem;
        --cui-tabs-gap: 0.75rem;
        --cui-tabs-panel-padding: 1rem 0.25rem 0.25rem;
        color-scheme: light;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid #bfdbfe;
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.tabs-theme__card--dark) {
        --cui-tabs-accent: #67e8f9;
        --cui-tabs-border-color: #155e75;
        --cui-tabs-muted-color: #cbd5e1;
        --cui-tabs-list-background: #083344;
        --cui-tabs-active-background: #164e63;
        --cui-tabs-hover-background: #0e7490;
        --cui-tabs-focus-color: #f0abfc;
        color-scheme: dark;
        border-color: #155e75;
      }

      :where(.tabs-theme__card header) {
        margin-block-end: 0.75rem;
      }

      :where(.tabs-theme__card h2, .tabs-theme__card p) {
        margin-block: 0;
      }

      :where(.tabs-theme__card header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
    """


preview = TabsThemeCustomization()

preview  # noqa: B018
````


The two surfaces use the same component markup. Their explicit light and dark
schemes and public CSS variables supply every visual difference.

## API reference

### Inputs

#### CTabs server inputs

Server inputs are passed in a template through `<c-CTabs ... />` or in Python through
`CTabs(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tabs-input-ctabs-server-default-value"></span>`default_value` | `non-empty str` | required | Sets uncontrolled initial selection and the server fallback. |
| <span id="tabs-input-ctabs-server-value"></span>`value` | `str | None` | `None` | Selects the server-controlled value for this render and wins over `default_value`. |
| <span id="tabs-input-ctabs-server-activation"></span>`activation` | `"automatic" | "manual"` ([`CTabsActivation`](#tabs-interface-ctabs-activation)) | `"automatic"` | Selects keyboard activation behavior. |
| <span id="tabs-input-ctabs-server-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CTabsOrientation`](#tabs-interface-ctabs-orientation)) | `"horizontal"` | Sets layout, ARIA orientation, and keyboard axis. |
| <span id="tabs-input-ctabs-server-direction"></span>`direction` | `"ltr" | "rtl" | None` ([`CTabsDirection`](#tabs-interface-ctabs-direction)) | `None` | Sets explicit direction or inherits computed browser direction. |
| <span id="tabs-input-ctabs-server-loop"></span>`loop` | `bool` | `True` | Controls arrow-key wrapping. |
| <span id="tabs-input-ctabs-server-disabled"></span>`disabled` | `bool` | `False` | Disables every Tab without losing selected state. |
| <span id="tabs-input-ctabs-server-variant"></span>`variant` | `"underline" | "pill"` ([`CTabsVariant`](#tabs-interface-ctabs-variant)) | `"underline"` | Selects the active treatment. |
| <span id="tabs-input-ctabs-server-density"></span>`density` | `"default" | "comfortable" | "compact"` ([`CTabsDensity`](#tabs-interface-ctabs-density)) | `"default"` | Selects Tab padding and minimum height. |
| <span id="tabs-input-ctabs-server-align"></span>`align` | `"start" | "center" | "end"` ([`CTabsAlign`](#tabs-interface-ctabs-align)) | `"start"` | Aligns Tabs on the list's main axis. |
| <span id="tabs-input-ctabs-server-grow"></span>`grow` | `bool` | `False` | Makes Tabs share the available main-axis size. |
| <span id="tabs-input-ctabs-server-id"></span>`id` | `str | None` | generated | Sets the root and relationship prefix. Explicit values cannot be blank or contain ASCII whitespace. |
| <span id="tabs-input-ctabs-server-aria-label"></span>`aria_label` | `str | None` | `None` | Directly names the generated Tab list. Required unless `aria_labelledby` is supplied. |
| <span id="tabs-input-ctabs-server-aria-labelledby"></span>`aria_labelledby` | `str | None` | `None` | Names the generated Tab list through another element's ID. Required unless `aria_label` is supplied. |
| <span id="tabs-input-ctabs-server-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#tabs-interface-input-type-aliases-class-value)) | `None` | Adds Tabs-root classes from a string, conditional mapping, or nested sequence and merges them with `attrs`. |
| <span id="tabs-input-ctabs-server-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#tabs-interface-input-type-aliases-style-value)) | `None` | Adds Tabs-root inline styles from CSS text, a property mapping, or a nested sequence and merges them with `attrs`. |
| <span id="tabs-input-ctabs-server-attrs"></span>`attrs` | `dict[str, object] | None` | `None` | Adds allowed attributes to the Tabs root; prefer the top-level inputs for class and style. |
| <span id="tabs-input-ctabs-server-tab-list-attrs"></span>`tab_list_attrs` | `dict[str, object] | None` | `None` | Adds allowed attributes to the generated `role="tablist"` element. |

</div>

#### CTabs client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTabs />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="tabs-input-ctabs-client-value"></span>`value` | `string` | Continues uncontrolled from the current selection. | Controls selection while supplied. |
| <span id="tabs-input-ctabs-client-activation"></span>`activation` | `"automatic" | "manual"` ([`CTabsActivation`](#tabs-interface-ctabs-activation)) | Uses the server input. | Reactively controls keyboard activation. |
| <span id="tabs-input-ctabs-client-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CTabsOrientation`](#tabs-interface-ctabs-orientation)) | Uses the server input. | Reactively controls layout, ARIA, and keyboard axis. |
| <span id="tabs-input-ctabs-client-direction"></span>`direction` | `"ltr" | "rtl" | null` ([`CTabsDirection`](#tabs-interface-ctabs-direction)) | Uses the server input. | Sets direction; `null` explicitly restores inherited browser direction. |
| <span id="tabs-input-ctabs-client-loop"></span>`loop` | `boolean` | Uses the server input. | Reactively controls wrapping. |
| <span id="tabs-input-ctabs-client-disabled"></span>`disabled` | `boolean` | Uses the server input. | Reactively controls root disabled state. |
| <span id="tabs-input-ctabs-client-variant"></span>`variant` | `"underline" | "pill"` ([`CTabsVariant`](#tabs-interface-ctabs-variant)) | Uses the server input. | Reactively controls presentation. |
| <span id="tabs-input-ctabs-client-density"></span>`density` | `"default" | "comfortable" | "compact"` ([`CTabsDensity`](#tabs-interface-ctabs-density)) | Uses the server input. | Reactively controls geometry. |
| <span id="tabs-input-ctabs-client-align"></span>`align` | `"start" | "center" | "end"` ([`CTabsAlign`](#tabs-interface-ctabs-align)) | Uses the server input. | Reactively controls alignment. |
| <span id="tabs-input-ctabs-client-grow"></span>`grow` | `boolean` | Uses the server input. | Reactively controls equal growth. |

</div>

#### CTab server inputs

Server inputs are passed in a template through `<c-CTab ... />` or in Python through
`CTab(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tabs-input-ctab-server-value"></span>`value` | `non-empty str` | required | Pairs this Tab with one Panel. |
| <span id="tabs-input-ctab-server-disabled"></span>`disabled` | `bool` | `False` | Natively disables this Tab and removes it from selection and focus movement. |
| <span id="tabs-input-ctab-server-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#tabs-interface-input-type-aliases-class-value)) | `None` | Adds native Tab classes from a string, conditional mapping, or nested sequence and merges them with `attrs`. |
| <span id="tabs-input-ctab-server-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#tabs-interface-input-type-aliases-style-value)) | `None` | Adds native Tab inline styles from CSS text, a property mapping, or a nested sequence and merges them with `attrs`. |
| <span id="tabs-input-ctab-server-attrs"></span>`attrs` | `dict[str, object] | None` | `None` | Adds allowed attributes to the native Tab Button; prefer the top-level inputs for class and style. |

</div>

#### CTabPanel server inputs

Server inputs are passed in a template through `<c-CTabPanel ... />` or in Python through
`CTabPanel(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tabs-input-ctabpanel-server-value"></span>`value` | `non-empty str` | required | Pairs this Panel with one Tab. |
| <span id="tabs-input-ctabpanel-server-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#tabs-interface-input-type-aliases-class-value)) | `None` | Adds Panel classes from a string, conditional mapping, or nested sequence and merges them with `attrs`. |
| <span id="tabs-input-ctabpanel-server-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#tabs-interface-input-type-aliases-style-value)) | `None` | Adds Panel inline styles from CSS text, a property mapping, or a nested sequence and merges them with `attrs`. |
| <span id="tabs-input-ctabpanel-server-attrs"></span>`attrs` | `dict[str, object] | None` | `None` | Adds allowed attributes to the Panel; prefer the top-level inputs for class and style. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CTabs slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="tabs-slot-ctabs-default"></span>`default` | yes | `{}` ([`CTabsDefaultSlotData`](#tabs-interface-ctabs-default-slot-data)) | none |

</div>

#### CTab slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="tabs-slot-ctab-default"></span>`default` | yes | `{value: str, is_selected: bool, is_disabled: bool}` ([`CTabDefaultSlotData`](#tabs-interface-ctab-default-slot-data)) | none |

</div>

#### CTabPanel slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="tabs-slot-ctabpanel-default"></span>`default` | yes | `{value: str, is_selected: bool}` ([`CTabPanelDefaultSlotData`](#tabs-interface-ctabpanel-default-slot-data)) | none |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CTabs events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="tabs-event-ctabs-on-value-change"></span>`onValueChange` | `(value: string, detail: object) => void` | A different enabled value is requested by pointer, keyboard, or removal. Runs before an uncontrolled commit; initial and owner updates are excluded. | `{value: string, previousValue: string, source: "pointer" | "keyboard" | "removal"}` | Controlled Tabs wait for `value` to update. Return values do not cancel the request. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTabs CSS variables

Apply these variables to `CTabs` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="tabs-css-ctabs-accent"></span>`--cui-tabs-accent` | `color` | Selected indicator and text. | `` `LinkText` `` |
| <span id="tabs-css-ctabs-border-color"></span>`--cui-tabs-border-color` | `color` | TabList divider. | `` 22% `currentColor` `` |
| <span id="tabs-css-ctabs-muted-color"></span>`--cui-tabs-muted-color` | `color` | Inactive Tab text. | `` 68% `currentColor` `` |
| <span id="tabs-css-ctabs-list-background"></span>`--cui-tabs-list-background` | `color` | TabList or pill track. | `transparent; pill derives a 12% accent mix` |
| <span id="tabs-css-ctabs-active-background"></span>`--cui-tabs-active-background` | `color` | Selected pill background. | `` `Canvas` `` |
| <span id="tabs-css-ctabs-hover-background"></span>`--cui-tabs-hover-background` | `color` | Enabled Tab hover background. | `` 8% `currentColor` `` |
| <span id="tabs-css-ctabs-focus-color"></span>`--cui-tabs-focus-color` | `color` | Tab and Panel focus-visible outline. | `` `Highlight` `` |
| <span id="tabs-css-ctabs-radius"></span>`--cui-tabs-radius` | `length` | Pill list and Tab radius basis. | `` `0.5rem` `` |
| <span id="tabs-css-ctabs-gap"></span>`--cui-tabs-gap` | `length` | Gap between TabList and Panels. | `` `1rem` `` |
| <span id="tabs-css-ctabs-tab-inline-padding"></span>`--cui-tabs-tab-inline-padding` | `length` | Tab logical inline padding. | `density-derived` |
| <span id="tabs-css-ctabs-tab-block-padding"></span>`--cui-tabs-tab-block-padding` | `length` | Tab logical block padding. | `density-derived` |
| <span id="tabs-css-ctabs-panel-padding"></span>`--cui-tabs-panel-padding` | `length` | Panel padding. | `` `1rem` `` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTabs attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tabs-attribute-ctabs-data-value"></span>`data-value` | Tabs root | `non-empty string or absent` | Effective selected value. |
| <span id="tabs-attribute-ctabs-data-activation"></span>`data-activation` | Tabs root | `automatic | manual` | Effective activation behavior. |
| <span id="tabs-attribute-ctabs-data-orientation"></span>`data-orientation` | Tabs root | `horizontal | vertical` | Effective layout and keyboard axis. |
| <span id="tabs-attribute-ctabs-data-direction"></span>`data-direction` | Tabs root | `ltr | rtl or absent` | Explicit effective direction. Absence means direction is inherited. |
| <span id="tabs-attribute-ctabs-data-loop"></span>`data-loop` | Tabs root | `boolean attribute` | Whether focus movement wraps. |
| <span id="tabs-attribute-ctabs-data-density"></span>`data-density` | Tabs root | `default | comfortable | compact` | Effective density. |
| <span id="tabs-attribute-ctabs-data-variant"></span>`data-variant` | Tabs root | `underline | pill` | Effective visual variant. |
| <span id="tabs-attribute-ctabs-data-align"></span>`data-align` | Tabs root | `start | center | end` | Effective Tab alignment. |
| <span id="tabs-attribute-ctabs-data-grow"></span>`data-grow` | Tabs root | `boolean attribute` | Whether Tabs share available space. |
| <span id="tabs-attribute-ctabs-data-disabled"></span>`data-disabled` | Tabs root | `boolean attribute` | Whether the whole group is disabled. |
| <span id="tabs-attribute-ctabs-list-data-orientation"></span>`data-orientation` | Generated Tab list | `horizontal | vertical` | Effective list orientation. |

</div>

#### CTab attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tabs-attribute-ctab-data-state"></span>`data-state` | Tab Button | `active | inactive` | Whether this Tab is selected. |
| <span id="tabs-attribute-ctab-data-value"></span>`data-value` | Tab Button | `non-empty string` | Immutable server-rendered Tab-to-Panel pairing identity. |
| <span id="tabs-attribute-ctab-data-disabled"></span>`data-disabled` | Tab Button | `boolean attribute` | Effective per-Tab or root disabled state. |

</div>

#### CTabPanel attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tabs-attribute-ctabpanel-data-state"></span>`data-state` | Tab Panel | `active | inactive` | Whether this Panel is selected. |
| <span id="tabs-attribute-ctabpanel-data-value"></span>`data-value` | Tab Panel | `non-empty string` | Immutable server-rendered Panel-to-Tab pairing identity. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTabs selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="tabs-selector-ctabs-tabs"></span>`[data-citry-ui-part="tabs"]` | Root `<div>` | Owns effective configuration and selected-value attributes. |
| <span id="tabs-selector-ctabs-tab-list"></span>`[data-citry-ui-part="tab-list"]` | Generated `<div role="tablist">` | Groups, names, and arranges the Tab controls. |

</div>

#### CTab selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="tabs-selector-ctab-tab"></span>`[data-citry-ui-part="tab"]` | Native `<button role="tab">` | Tab activation, focus, selected, hover, and disabled styling. |

</div>

#### CTabPanel selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="tabs-selector-ctabpanel-tab-panel"></span>`[data-citry-ui-part="tab-panel"]` | `<div role="tabpanel">` | Contains one mounted Panel's content. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="tabs-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="tabs-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="tabs-interface-ctabs-activation"></span>`CTabsActivation` | `Literal["automatic", "manual"]` |
| <span id="tabs-interface-ctabs-orientation"></span>`CTabsOrientation` | `Literal["horizontal", "vertical"]` |
| <span id="tabs-interface-ctabs-direction"></span>`CTabsDirection` | `Literal["ltr", "rtl"]` |
| <span id="tabs-interface-ctabs-variant"></span>`CTabsVariant` | `Literal["underline", "pill"]` |
| <span id="tabs-interface-ctabs-density"></span>`CTabsDensity` | `Literal["default", "comfortable", "compact"]` |
| <span id="tabs-interface-ctabs-align"></span>`CTabsAlign` | `Literal["start", "center", "end"]` |

</div>

<span id="tabs-interface-ctabs-default-slot-data"></span>

#### `CTabsDefaultSlotData`

Empty dataclass: `{}`.

<span id="tabs-interface-ctab-default-slot-data"></span>

#### `CTabDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tabs-interface-ctab-default-slot-data-value"></span>`value` | `str` | - | This Tab's pairing value. |
| <span id="tabs-interface-ctab-default-slot-data-is-selected"></span>`is_selected` | `bool` | - | Whether this Tab is selected in the server render. |
| <span id="tabs-interface-ctab-default-slot-data-is-disabled"></span>`is_disabled` | `bool` | - | Effective disabled state in the server render. |

</div>

<span id="tabs-interface-ctabpanel-default-slot-data"></span>

#### `CTabPanelDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tabs-interface-ctabpanel-default-slot-data-value"></span>`value` | `str` | - | This Panel's pairing value. |
| <span id="tabs-interface-ctabpanel-default-slot-data-is-selected"></span>`is_selected` | `bool` | - | Whether this Panel is selected in the server render. |

</div>

### Translation keys

-