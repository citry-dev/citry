---
title: Card
url: https://citry.dev/v/0.4.0/ui-library/components/card/
description: "Group related content, media, metadata, and actions in a flexible Citry UI surface."
---
# Card

Use `CCard` to present one subject as a contained visual unit. Its sections are
optional, so a Card can be a short note, a media object, or a complete summary
with header and footer actions.

## Card at a glance


### Card at a glance

[Open the rendered preview](/v/0.4.0/ui-library/components/card/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardAtAGlance(Component):
    template = """
      <section class="card-glance" aria-label="Rooms and furnishings">
        <c-CCard>
          <c-fill name="media">
            <div class="card-glance__scene card-glance__scene--sunroom" aria-hidden="true">
              <span></span>
            </div>
          </c-fill>
          <c-fill name="header">
            <p class="card-glance__eyebrow">Sunroom</p>
            <h2>Window reading chair</h2>
          </c-fill>
          <c-fill name="default">
            Oak arms, woven rush, and a linen cushion for slow afternoons.
          </c-fill>
          <c-fill name="footer">
            Natural oak · 76 cm wide
          </c-fill>
          <c-fill name="actions">
            <c-CButton size="sm">View chair</c-CButton>
          </c-fill>
        </c-CCard>

        <c-CCard variant="outline">
          <c-fill name="media">
            <div class="card-glance__scene card-glance__scene--studio" aria-hidden="true">
              <span></span>
            </div>
          </c-fill>
          <c-fill name="header">
            <p class="card-glance__eyebrow">Studio</p>
            <h2>Cloud pendant</h2>
          </c-fill>
          <c-fill name="header_actions">
            <c-CButton
              size="sm"
              variant="ghost"
              c-attrs="{'aria-label': 'Save Cloud pendant'}"
            >
              <c-CIcon name="heart" />
              <span class="card-glance__sr-only">Save</span>
            </c-CButton>
          </c-fill>
          <c-fill name="default">
            A softly diffused shade for desks, drawing tables, and late-night sketches.
          </c-fill>
        </c-CCard>

        <c-CCard variant="subtle">
          <c-fill name="header">
            <p class="card-glance__eyebrow">Library</p>
            <h2>Walnut wall shelf</h2>
          </c-fill>
          <c-fill name="default">
            Three slim shelves keep favorite books close without crowding the room.
          </c-fill>
          <c-fill name="actions">
            <c-CButton size="sm" variant="outline">See dimensions</c-CButton>
            <c-CButton size="sm" variant="ghost">Add to room</c-CButton>
          </c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        max-width: 68rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-glance [data-citry-ui-part="card"]) {
        align-self: start;
      }

      :where(.card-glance h2, .card-glance p) {
        margin: 0;
      }

      :where(.card-glance h2) {
        font-size: 1.05rem;
      }

      :where(.card-glance__eyebrow) {
        margin-block-end: 0.25rem;
        color: light-dark(#72531b, #e4bd70);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.card-glance__scene) {
        position: relative;
        block-size: 8.5rem;
        overflow: hidden;
      }

      :where(.card-glance__scene::before) {
        position: absolute;
        inset: 0;
        content: "";
      }

      :where(.card-glance__scene--sunroom::before) {
        background:
          linear-gradient(90deg, transparent 66%, rgb(255 255 255 / 46%) 66% 70%, transparent 70%),
          linear-gradient(160deg, #e9cfa0, #8aaa79);
      }

      :where(.card-glance__scene--studio::before) {
        background:
          radial-gradient(circle at 62% 38%, #fff1c7 0 13%, transparent 14%),
          linear-gradient(145deg, #8ba4bd, #3f5068);
      }

      :where(.card-glance__scene span) {
        position: absolute;
        inset-inline: 18%;
        inset-block-end: 16%;
        block-size: 30%;
        border-radius: 999px 999px 0.35rem 0.35rem;
        background: rgb(255 255 255 / 62%);
      }

      :where(.card-glance__sr-only) {
        position: absolute;
        inline-size: 1px;
        block-size: 1px;
        overflow: hidden;
        clip-path: inset(50%);
        white-space: nowrap;
      }
    """


preview = CardAtAGlance()

preview  # noqa: B018
````


The smallest Card needs only content:


```citry-html
<c-CCard>
  A quiet place to read beside the window.
</c-CCard>
```


Compose the same result in Python:


```python
from citry_ui import CCard

reading_note = CCard(slots={"default": "A quiet place to read beside the window."})
```


## Compose the sections you need

Every slot is optional, but a Card must supply at least one. Omitted sections
produce no empty wrapper.


### Compose optional Card sections

[Open the rendered preview](/v/0.4.0/ui-library/components/card/_previews/basic-card/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicCards(Component):
    template = """
      <section class="card-basics">
        <c-CCard>
          The south window gets soft light from breakfast until noon.
        </c-CCard>

        <c-CCard variant="outline">
          <c-fill name="header">
            <h2>Washed linen</h2>
            <p>Warm white · 140 g/m²</p>
          </c-fill>
        </c-CCard>

        <c-CCard variant="subtle">
          <c-fill name="footer">
            Hand-thrown stoneware · one of twelve
          </c-fill>
          <c-fill name="actions">
            <c-CButton size="sm" variant="ghost">Reserve vase</c-CButton>
          </c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-basics) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        max-width: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-basics h2, .card-basics p) {
        margin: 0;
      }

      :where(.card-basics h2) {
        font-size: 1rem;
      }

      :where(.card-basics p) {
        margin-block-start: 0.25rem;
        color: light-dark(#6b6257, #cfc5b8);
        font-size: 0.82rem;
      }
    """


preview = BasicCards()

preview  # noqa: B018
````


Use `header_actions` for controls beside a heading. Use `footer` for metadata
and `actions` for controls at the end. Card supplies the alignment; your slot
content supplies headings, landmarks, links, and accessible names.

## Choose visual emphasis

`elevated` lifts a Card with shadow, `outline` draws a boundary, and `subtle`
adds a quiet system-color tint.


### Compare Card variants

[Open the rendered preview](/v/0.4.0/ui-library/components/card/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardVariants(Component):
    template = """
      <section class="card-variants" aria-label="Card variants">
        <c-CCard variant="elevated">
          <c-fill name="header"><h2>Elevated</h2></c-fill>
          <c-fill name="default">A focal surface for the linen floor lamp.</c-fill>
        </c-CCard>
        <c-CCard variant="outline">
          <c-fill name="header"><h2>Outline</h2></c-fill>
          <c-fill name="default">A clear boundary for the oak side table.</c-fill>
        </c-CCard>
        <c-CCard variant="subtle">
          <c-fill name="header"><h2>Subtle</h2></c-fill>
          <c-fill name="default">A quiet grouping for woven storage baskets.</c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1.25rem;
        max-width: 62rem;
        padding: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-variants h2) {
        margin: 0;
        font-size: 1rem;
      }
    """


preview = CardVariants()

preview  # noqa: B018
````


Variants describe surface emphasis, not meaning. Use semantic HTML for
success, warning, or error feedback instead of assigning semantic color to
Card.

## Choose spacing

`sm`, `md`, and `lg` adjust section padding and action gaps. Typography remains
owned by your content.


### Compare Card sizes

[Open the rendered preview](/v/0.4.0/ui-library/components/card/_previews/sizes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardSizes(Component):
    template = """
      <section class="card-sizes" aria-label="Card sizes">
        <c-CCard size="sm" variant="outline">
          <c-fill name="header"><h2>Small</h2></c-fill>
          <c-fill name="default">Cedar drawer label and finish sample.</c-fill>
          <c-fill name="actions"><c-CButton size="sm" variant="ghost">Open</c-CButton></c-fill>
        </c-CCard>
        <c-CCard size="md" variant="outline">
          <c-fill name="header"><h2>Medium</h2></c-fill>
          <c-fill name="default">A balanced surface for a lamp, book, and cup.</c-fill>
          <c-fill name="actions"><c-CButton size="sm" variant="ghost">Open</c-CButton></c-fill>
        </c-CCard>
        <c-CCard size="lg" variant="outline">
          <c-fill name="header"><h2>Large</h2></c-fill>
          <c-fill name="default">Room for textile notes, dimensions, and a longer material story.</c-fill>
          <c-fill name="actions"><c-CButton size="sm" variant="ghost">Open</c-CButton></c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-sizes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1rem;
        align-items: start;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-sizes h2) {
        margin: 0;
        font-size: 1rem;
      }
    """


preview = CardSizes()

preview  # noqa: B018
````


## Add media

Media appears first and clips to the Card's top edge, or to every edge when it
is the only section. Card makes direct images, pictures, and videos block-level
and prevents intrinsic overflow. It does not choose an aspect ratio, crop, or
`object-fit`.


### Add consumer-owned media

[Open the rendered preview](/v/0.4.0/ui-library/components/card/_previews/media/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardMedia(Component):
    template = """
      <section class="card-media">
        <c-CCard variant="outline">
          <c-fill name="media">
            <svg
              class="card-media__illustration"
              viewBox="0 0 360 190"
              role="img"
              aria-label="A round table beside a sunlit arched window"
            >
              <rect width="360" height="190" fill="#d9c5a3" />
              <path d="M220 170V70a58 58 0 0 1 116 0v100" fill="#8da7a0" />
              <circle cx="278" cy="70" r="38" fill="#f7e7a7" opacity=".8" />
              <ellipse cx="105" cy="135" rx="72" ry="18" fill="#7a4e32" />
              <path d="M84 135v42M126 135v42" stroke="#513523" stroke-width="8" />
            </svg>
          </c-fill>
          <c-fill name="header"><h2>Breakfast nook</h2></c-fill>
          <c-fill name="default">
            Card preserves the illustration's own aspect ratio and accessible name.
          </c-fill>
        </c-CCard>

        <c-CCard>
          <c-fill name="media">
            <div class="card-media__swatches">
              <span class="card-media__clay">Clay</span>
              <span class="card-media__linen">Linen</span>
              <span class="card-media__moss">Moss</span>
              <span class="card-media__walnut">Walnut</span>
            </div>
          </c-fill>
          <c-fill name="header"><h2>Autumn materials</h2></c-fill>
          <c-fill name="default">
            Multiple consumer-owned nodes can define their own media layout.
          </c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-media) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-media h2) {
        margin: 0;
        font-size: 1rem;
      }

      :where(.card-media__illustration) {
        display: block;
        inline-size: 100%;
        block-size: auto;
      }

      :where(.card-media__swatches) {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        min-block-size: 10rem;
      }

      :where(.card-media__swatches span) {
        display: grid;
        place-items: end center;
        padding: 0.5rem 0.2rem;
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 700;
      }

      :where(.card-media__clay) {
        background: #a75f46;
      }

      :where(.card-media__linen) {
        background: #b8a98c;
        color: #241f18;
      }

      :where(.card-media__moss) {
        background: #66704a;
      }

      :where(.card-media__walnut) {
        background: #5d3a2a;
      }
    """


preview = CardMedia()

preview  # noqa: B018
````


Keep menus and popups outside `media`: clipping is intentional there. Place
escaping interactive content in the header, body, or footer.

## Align metadata and actions

Header and footer action slots keep direct controls together and wrap when
space runs out. The companion content stays in its own flexible column.


### Compose header and footer actions

[Open the rendered preview](/v/0.4.0/ui-library/components/card/_previews/actions/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardActions(Component):
    template = """
      <section class="card-actions">
        <c-CCard
          variant="outline"
          c-header_actions_attrs="{'role': 'group', 'aria-label': 'Shelf shortcuts'}"
          c-actions_attrs="{'role': 'group', 'aria-label': 'Shelf actions'}"
        >
          <c-fill name="header">
            <p class="card-actions__eyebrow">Library</p>
            <h2>Floating walnut shelf</h2>
          </c-fill>
          <c-fill name="header_actions">
            <c-CButton
              size="sm"
              variant="ghost"
              c-attrs="{'aria-label': 'Save floating walnut shelf'}"
            >
              <c-CIcon name="heart" />
              <span class="card-actions__sr-only">Save</span>
            </c-CButton>
          </c-fill>
          <c-fill name="default">
            Hidden steel brackets keep the profile light while supporting a row of hardbacks.
          </c-fill>
          <c-fill name="footer">
            90 by 18 cm · walnut veneer
          </c-fill>
          <c-fill name="actions">
            <c-CButton size="sm">Add to room</c-CButton>
            <c-CButton size="sm" variant="outline">Compare finishes</c-CButton>
            <c-CButton size="sm" variant="ghost">Dimensions</c-CButton>
          </c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-actions) {
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-actions h2, .card-actions p) {
        margin: 0;
      }

      :where(.card-actions h2) {
        font-size: 1.05rem;
      }

      :where(.card-actions__eyebrow) {
        margin-block-end: 0.25rem;
        color: light-dark(#7c4f28, #e2b581);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.card-actions__sr-only) {
        position: absolute;
        inline-size: 1px;
        block-size: 1px;
        overflow: hidden;
        clip-path: inset(50%);
        white-space: nowrap;
      }
    """


preview = CardActions()

preview  # noqa: B018
````


Pass `header_actions_attrs` or `actions_attrs` when the control cluster needs
group semantics, an accessible label, data, or a trusted Alpine binding. A
nonempty part mapping fails if its destination slot is absent.

## Put interactive content inside Card

Card has no client state and does not intercept nested controls. Its root,
header, body, and footer stay unclipped and create no stacking context.


### Use interactive content inside Card

[Open the rendered preview](/v/0.4.0/ui-library/components/card/_previews/nested-content/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardNestedContent(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "rooms": (
                citry_ui.CComboboxOption("sunroom", "Sunroom"),
                citry_ui.CComboboxOption("library", "Library"),
                citry_ui.CComboboxOption("studio", "Studio"),
            )
        }

    template = """
      <section class="card-nested">
        <c-CCard variant="outline">
          <c-fill name="header"><h2>Place the reading chair</h2></c-fill>
          <c-fill name="default">
            <c-CField>
              <c-fill name="label">Room</c-fill>
              <c-fill name="default">
                <c-CCombobox
                  c-options="rooms"
                  value="sunroom"
                  placeholder="Choose a room"
                />
              </c-fill>
            </c-CField>
          </c-fill>
          <c-fill name="actions">
            <c-CDialog>
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton variant="outline" c-attrs="activator_attrs">
                  Check dimensions
                </c-CButton>
              </c-fill>
              <c-fill name="title">Reading chair dimensions</c-fill>
              <c-fill name="description">
                Measure doorways and the chosen corner before delivery.
              </c-fill>
              <c-fill name="default">
                The chair is 76 cm wide, 84 cm deep, and 92 cm tall.
              </c-fill>
            </c-CDialog>
          </c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-nested) {
        max-width: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-nested h2) {
        margin: 0;
        font-size: 1.05rem;
      }
    """


preview = CardNestedContent()

preview  # noqa: B018
````


Card itself is not one large action. Use real links and Buttons inside it. A
whole-Card link needs its own focus, layering, and nested-control contract and
is not supported by `CCard`.

## Customize layout and theme

Override public variables on an ancestor or one Card. Stable part selectors
support responsive layouts without turning orientation into a server input.


### Customize Card with public CSS

[Open the rendered preview](/v/0.4.0/ui-library/components/card/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardCustomization(Component):
    template = """
      <section class="card-customization">
        <div class="card-customization__linen">
          <c-CCard class_="card-customization__horizontal">
            <c-fill name="media">
              <div class="card-customization__weave" aria-hidden="true"></div>
            </c-fill>
            <c-fill name="header"><h2>Linen house</h2></c-fill>
            <c-fill name="default">
              Soft edges and warm neutrals made entirely with public variables and parts.
            </c-fill>
            <c-fill name="footer">Natural flax · washed finish</c-fill>
          </c-CCard>
        </div>

        <div class="card-customization__studio" data-theme="dark">
          <c-CCard class_="card-customization__horizontal" variant="outline">
            <c-fill name="media">
              <div class="card-customization__grid" aria-hidden="true"></div>
            </c-fill>
            <c-fill name="header"><h2>Night studio</h2></c-fill>
            <c-fill name="default">
              Crisp geometry and cool contrast adapt through the same stable contract.
            </c-fill>
            <c-fill name="actions">
              <c-CButton size="sm" variant="outline">Open palette</c-CButton>
            </c-fill>
          </c-CCard>
        </div>
      </section>
    """

    css = """
      :where(.card-customization) {
        display: grid;
        gap: 1rem;
        max-width: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-customization > div) {
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.card-customization__linen) {
        --cui-card-background: #fffaf0;
        --cui-card-foreground: #3d3328;
        --cui-card-border-color: #d8c8ad;
        --cui-card-radius: 1.1rem;
        --cui-card-shadow: 0 0.8rem 2rem rgb(96 71 39 / 14%);
        background: #efe4d0;
      }

      :where(.card-customization__studio) {
        color-scheme: dark;
        --cui-card-background: #182235;
        --cui-card-foreground: #e7eefc;
        --cui-card-border-color: #607aa5;
        --cui-card-radius: 0.35rem;
        --cui-card-shadow: none;
        background: #0d1421;
      }

      :where(.card-customization__horizontal) {
        display: grid;
        grid-template-columns: minmax(8rem, 32%) 1fr;
      }

      :where(.card-customization__horizontal > [data-citry-ui-part="media"]) {
        grid-row: 1 / -1;
        border-start-start-radius: var(--cui-card-radius);
        border-start-end-radius: 0;
        border-end-start-radius: var(--cui-card-radius);
        border-end-end-radius: 0;
      }

      :where(.card-customization__horizontal > :not([data-citry-ui-part="media"])) {
        grid-column: 2;
      }

      :where(.card-customization h2) {
        margin: 0;
        font-size: 1.05rem;
      }

      :where(.card-customization__weave, .card-customization__grid) {
        min-block-size: 100%;
      }

      :where(.card-customization__weave) {
        background:
          repeating-linear-gradient(0deg, rgb(255 255 255 / 20%) 0 2px, transparent 2px 6px),
          #9f7950;
      }

      :where(.card-customization__grid) {
        background:
          linear-gradient(#5b78a8 1px, transparent 1px),
          linear-gradient(90deg, #5b78a8 1px, transparent 1px),
          #24324b;
        background-size: 1.5rem 1.5rem;
      }

      @media (max-width: 36rem) {
        :where(.card-customization__horizontal) {
          display: block;
        }

        :where(.card-customization__horizontal > [data-citry-ui-part="media"]) {
          border-start-start-radius: var(--cui-card-radius, 0.75rem);
          border-start-end-radius: var(--cui-card-radius, 0.75rem);
          border-end-start-radius: 0;
          border-end-end-radius: 0;
        }
      }
    """


preview = CardCustomization()

preview  # noqa: B018
````


The example shows two independent brand treatments and a horizontal layout
that returns to vertical at narrow width. `.cui-*` classes and `--_cui-*`
variables are private.

## Choose root semantics

The default `div` makes no document-structure claim. Choose `article` for an
independently reusable composition, `section` for a named document section, or
`li` inside a list.


### Choose native Card semantics

[Open the rendered preview](/v/0.4.0/ui-library/components/card/_previews/semantics/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardSemantics(Component):
    template = """
      <section class="card-semantics">
        <article>
          <h2>Neutral group</h2>
          <c-CCard>
            Decorative cushions can sit in an ordinary layout without becoming a document section.
          </c-CCard>
        </article>

        <article>
          <h2>Independent article</h2>
          <c-CCard tag="article" c-attrs="{'aria-labelledby': 'chair-title'}">
            <c-fill name="header"><h3 id="chair-title">The spindle chair returns</h3></c-fill>
            <c-fill name="default">A complete journal note with its own heading and subject.</c-fill>
          </c-CCard>
        </article>

        <section aria-labelledby="materials-title">
          <h2 id="materials-title">Named section</h2>
          <c-CCard tag="section" c-attrs="{'aria-labelledby': 'wool-title'}" variant="outline">
            <c-fill name="header"><h3 id="wool-title">Wool upholstery</h3></c-fill>
            <c-fill name="default">A subsection of the wider materials guide.</c-fill>
          </c-CCard>
        </section>

        <article>
          <h2>List item</h2>
          <ul>
            <c-CCard tag="li" variant="subtle">Oak side table</c-CCard>
            <c-CCard tag="li" variant="subtle">Linen floor lamp</c-CCard>
          </ul>
        </article>
      </section>
    """

    css = """
      :where(.card-semantics) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1.25rem;
        max-width: 68rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-semantics h2, .card-semantics h3) {
        margin-block-start: 0;
      }

      :where(.card-semantics h2) {
        font-size: 1rem;
      }

      :where(.card-semantics h3) {
        margin-block-end: 0;
        font-size: 0.95rem;
      }

      :where(.card-semantics ul) {
        display: grid;
        gap: 0.5rem;
        margin: 0;
        padding: 0;
        list-style: none;
      }
    """


preview = CardSemantics()

preview  # noqa: B018
````


`CCard` adds no role, focus stop, keyboard behavior, or accessible name. The
selected native root and your content own those semantics.

## Accessibility, trust, and server rendering

Card renders completely without JavaScript. Slot text uses ordinary Citry
escaping. Attribute maps accept native, ARIA, data, and trusted Alpine
attributes, but reserve Card's reflected fields, part markers, and Citry's
runtime ownership namespace.

Card follows nested `color-scheme`, keeps a visible forced-colors boundary,
removes decorative shadow in print, and uses logical layout for right-to-left
content.

## API reference

### Inputs

#### CCard server inputs

Server inputs are passed in a template through `<c-CCard ... />` or in Python through
`CCard(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="card-input-ccard-server-inputs-tag"></span>`tag` | `"div" | "article" | "section" | "li"` ([`CCardTag`](#card-interface-input-type-aliases-ccard-tag)) | `"div"` | Selects the native root. Use the neutral default unless the Card content satisfies stronger document semantics. |
| <span id="card-input-ccard-server-inputs-variant"></span>`variant` | `"elevated" | "outline" | "subtle"` ([`CCardVariant`](#card-interface-input-type-aliases-ccard-variant)) | `"elevated"` | Selects shadow, border, and background emphasis. |
| <span id="card-input-ccard-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CCardSize`](#card-interface-input-type-aliases-ccard-size)) | `"md"` | Sets section padding and action gaps without changing consumer typography. |
| <span id="card-input-ccard-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#card-interface-input-type-aliases-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="card-input-ccard-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#card-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="card-input-ccard-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted Alpine root attributes. It cannot replace the public part, variant, size, or Citry runtime ownership fields. |
| <span id="card-input-ccard-server-inputs-media-attrs"></span>`media_attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted Alpine attributes to the media wrapper. A nonempty mapping requires the media slot. |
| <span id="card-input-ccard-server-inputs-header-attrs"></span>`header_attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted Alpine attributes to the header row. A nonempty mapping requires header or header_actions. |
| <span id="card-input-ccard-server-inputs-header-actions-attrs"></span>`header_actions_attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted Alpine attributes to the header action group. A nonempty mapping requires header_actions. |
| <span id="card-input-ccard-server-inputs-body-attrs"></span>`body_attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted Alpine attributes to the body wrapper. A nonempty mapping requires the default slot. |
| <span id="card-input-ccard-server-inputs-footer-attrs"></span>`footer_attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted Alpine attributes to the footer row. A nonempty mapping requires footer or actions. |
| <span id="card-input-ccard-server-inputs-actions-attrs"></span>`actions_attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted Alpine attributes to the footer action group. A nonempty mapping requires actions. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CCard slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="card-slot-ccard-slots-media"></span>`media` | no | `{}` ([`CCardMediaSlotData`](#card-interface-ccard-media-slot-data)) | Wrapper omitted. |
| <span id="card-slot-ccard-slots-header"></span>`header` | no | `{}` ([`CCardHeaderSlotData`](#card-interface-ccard-header-slot-data)) | Content wrapper omitted. |
| <span id="card-slot-ccard-slots-header-actions"></span>`header_actions` | no | `{}` ([`CCardHeaderActionsSlotData`](#card-interface-ccard-header-actions-slot-data)) | Action wrapper omitted. |
| <span id="card-slot-ccard-slots-default"></span>`default` | no | `{}` ([`CCardDefaultSlotData`](#card-interface-ccard-default-slot-data)) | Body wrapper omitted. |
| <span id="card-slot-ccard-slots-footer"></span>`footer` | no | `{}` ([`CCardFooterSlotData`](#card-interface-ccard-footer-slot-data)) | Content wrapper omitted. |
| <span id="card-slot-ccard-slots-actions"></span>`actions` | no | `{}` ([`CCardActionsSlotData`](#card-interface-ccard-actions-slot-data)) | Action wrapper omitted. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CCard CSS variables

Apply these variables to `CCard` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="card-css-ccard-css-variables-cui-card-background"></span>`--cui-card-background` | `color` | Root background. | `Variant-derived Canvas or system-color mix.` |
| <span id="card-css-ccard-css-variables-cui-card-foreground"></span>`--cui-card-foreground` | `color` | Inherited content color. | `CanvasText` |
| <span id="card-css-ccard-css-variables-cui-card-border-color"></span>`--cui-card-border-color` | `color` | Root border color. | `Variant-derived transparent or system-color mix.` |
| <span id="card-css-ccard-css-variables-cui-card-shadow"></span>`--cui-card-shadow` | `shadow` | Root elevation shadow. | `Variant-derived shadow or none.` |
| <span id="card-css-ccard-css-variables-cui-card-radius"></span>`--cui-card-radius` | `length` | Root and media edge radius. | `0.75rem` |
| <span id="card-css-ccard-css-variables-cui-card-padding"></span>`--cui-card-padding` | `length` | Header, body, and footer row padding. | `Size-derived length.` |
| <span id="card-css-ccard-css-variables-cui-card-section-gap"></span>`--cui-card-section-gap` | `length` | Space between header or footer content and actions. | `Size-derived length.` |
| <span id="card-css-ccard-css-variables-cui-card-actions-gap"></span>`--cui-card-actions-gap` | `length` | Gap between controls in either action group. | `Size-derived length.` |
| <span id="card-css-ccard-css-variables-cui-card-actions-justify"></span>`--cui-card-actions-justify` | `justify-content` | Alignment inside action groups. | `flex-start` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CCard attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="card-attribute-ccard-attributes-data-variant"></span>`data-variant` | Root | `"elevated" | "outline" | "subtle"` | Reflects the server-selected surface treatment. |
| <span id="card-attribute-ccard-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Reflects the server-selected spacing preset. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CCard selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="card-selector-ccard-selectors-data-citry-ui-part-card"></span>`[data-citry-ui-part="card"]` | Native root | Stable Card root and `attrs` destination. |
| <span id="card-selector-ccard-selectors-data-citry-ui-part-media"></span>`[data-citry-ui-part="media"]` | Optional media wrapper | Clipped media edge and `media_attrs` destination. |
| <span id="card-selector-ccard-selectors-data-citry-ui-part-header"></span>`[data-citry-ui-part="header"]` | Optional header row | Header layout and `header_attrs` destination. |
| <span id="card-selector-ccard-selectors-data-citry-ui-part-header-actions"></span>`[data-citry-ui-part="header-actions"]` | Optional header action group | Direct-control layout and `header_actions_attrs` destination. |
| <span id="card-selector-ccard-selectors-data-citry-ui-part-body"></span>`[data-citry-ui-part="body"]` | Optional body wrapper | Main content and `body_attrs` destination. |
| <span id="card-selector-ccard-selectors-data-citry-ui-part-footer"></span>`[data-citry-ui-part="footer"]` | Optional footer row | Footer layout and `footer_attrs` destination. |
| <span id="card-selector-ccard-selectors-data-citry-ui-part-actions"></span>`[data-citry-ui-part="actions"]` | Optional footer action group | Direct-control layout and `actions_attrs` destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="card-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="card-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="card-interface-input-type-aliases-ccard-tag"></span>`CCardTag` | `Literal["div", "article", "section", "li"]` |
| <span id="card-interface-input-type-aliases-ccard-variant"></span>`CCardVariant` | `Literal["elevated", "outline", "subtle"]` |
| <span id="card-interface-input-type-aliases-ccard-size"></span>`CCardSize` | `Literal["sm", "md", "lg"]` |

</div>

<span id="card-interface-ccard-media-slot-data"></span>

#### `CCardMediaSlotData`

Empty dataclass: `{}`.

<span id="card-interface-ccard-header-slot-data"></span>

#### `CCardHeaderSlotData`

Empty dataclass: `{}`.

<span id="card-interface-ccard-header-actions-slot-data"></span>

#### `CCardHeaderActionsSlotData`

Empty dataclass: `{}`.

<span id="card-interface-ccard-default-slot-data"></span>

#### `CCardDefaultSlotData`

Empty dataclass: `{}`.

<span id="card-interface-ccard-footer-slot-data"></span>

#### `CCardFooterSlotData`

Empty dataclass: `{}`.

<span id="card-interface-ccard-actions-slot-data"></span>

#### `CCardActionsSlotData`

Empty dataclass: `{}`.

### Translation keys

-