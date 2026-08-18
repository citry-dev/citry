---
title: Menu
url: https://citry.dev/v/0.4.0/ui-library/components/menu/
description: "Present commands, links, application choices, and nested command collections from one Button."
---
# Menu

Use `CMenu` for a temporary application-command collection. It supports native
links, grouped commands, check/radio choices, and nested submenus with direct
focus, typeahead, touch-safe activation, and logical placement.

Use `CPopover` for arbitrary controls, forms, or explanatory content. Menu
items accept text and decorative content, not nested interactive controls.

## Menu at a glance

Open the archive menu to see commands, navigation, a submenu, a separator, and
destructive emphasis together.


### Menu at a glance

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuAtAGlance(Component):
    template = """
      <section class="archive-menu-demo">
        <p>Enchanted archive</p>
        <c-CMenu>
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Open archive menu</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="rename">Rename folio</c-CMenuItem>
            <c-CMenuItem href="#moon-catalog">Open moon catalog</c-CMenuItem>
            <c-CMenuSubmenu value="send-to">
              <c-fill name="label">Send to collection</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="astronomy">Astronomy</c-CMenuItem>
                <c-CMenuItem value="mythology">Mythology</c-CMenuItem>
              </c-fill>
            </c-CMenuSubmenu>
            <c-CMenuSeparator />
            <c-CMenuItem value="banish" intent="danger">Banish folio</c-CMenuItem>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-menu-demo) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-menu-demo > p) {
        margin: 0;
        color: light-dark(#7a4b18, #e8bd76);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = MenuAtAGlance()

preview  # noqa: B018
````


## Compose a Menu

Provide exactly one native Button through `activator`. Put Menu-family
declarations directly in the default slot.


```citry-html
<c-CMenu>
  <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
    <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Open archive</c-CButton>
  </c-fill>
  <c-fill name="default">
    <c-CMenuItem value="rename">Rename folio</c-CMenuItem>
    <c-CMenuItem href="/catalog">Open catalog</c-CMenuItem>
    <c-CMenuSeparator />
    <c-CMenuItem value="delete" intent="danger">Delete folio</c-CMenuItem>
  </c-fill>
</c-CMenu>
```


Forward both activator fields. `activator_attrs` carries relationships and the
anchor; `activator_disabled` goes through CButton's `disabled` input. A native
`button` also sets `type="button"` directly.

For Python composition, supply one component whose output contains the direct
declarations. Transparent components may generate declarations when they add
no wrapper or other output.

`CMenuItem`, `CMenuCheckboxItem`, `CMenuRadioGroup`, `CMenuRadioItem`,
`CMenuGroup`, `CMenuSeparator`, and `CMenuSubmenu` are not standalone.

## Run commands and follow links

Give a command `value` when the root `onAction` callback should identify it.
Anonymous commands use native `@click`. Supplying `href` renders a real anchor
and preserves navigation, link context menus, and browser behavior.


### Commands and links

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/commands-and-links/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuCommandsAndLinks(Component):
    template = """
      <section
        class="archive-command-demo"
        x-data="{lastAction: 'none'}"
      >
        <c-CMenu
          $c-props="{
            onAction: (value) => lastAction = value,
          }"
        >
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Folio actions</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="duplicate">Duplicate folio</c-CMenuItem>
            <c-CMenuItem @click="lastAction = 'annotate'">Add annotation</c-CMenuItem>
            <c-CMenuItem href="#restricted-shelf">Visit restricted shelf</c-CMenuItem>
          </c-fill>
        </c-CMenu>
        <output x-text="`Last command: ${lastAction}`">Last command: none</output>
      </section>
    """

    css = """
      :where(.archive-command-demo) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 14rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-command-demo output) {
        color: light-dark(#66451f, #dec08f);
      }
    """


preview = MenuCommandsAndLinks()

preview  # noqa: B018
````


Links do not call `onAction`. Disabled links temporarily omit `href` and never
navigate.

## Add item content

Use `start`, default, `description`, and `end` for icons, the visible label,
supporting text, and shortcuts. Only the default label names the item; the
description is exposed separately.


### Item content

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/item-content/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuItemContent(Component):
    template = """
      <section class="archive-content-demo">
        <c-CMenu>
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Catalog tools</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="search">
              <c-fill name="start"><c-CIcon name="search" /></c-fill>
              <c-fill name="default">Search illuminated texts</c-fill>
              <c-fill name="description">Find titles, scribes, and sigils.</c-fill>
              <c-fill name="end"><kbd>⌘ K</kbd></c-fill>
            </c-CMenuItem>
            <c-CMenuItem value="bookmark">
              <c-fill name="start"><c-CIcon name="star" /></c-fill>
              <c-fill name="default">Mark this passage</c-fill>
              <c-fill name="end"><kbd>M</kbd></c-fill>
            </c-CMenuItem>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-content-demo) {
        min-block-size: 15rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-content-demo kbd) {
        padding: 0.1rem 0.35rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.3rem;
        font: inherit;
        font-size: 0.75rem;
      }
    """


preview = MenuItemContent()

preview  # noqa: B018
````


Keep every item region to noninteractive phrasing content. Set `text_value`
when the visible label does not produce concise typeahead text.

## Control visibility and configuration

Server inputs are passed in Python through `<c-CMenu ... />` attributes or a
`CMenu(...)` composition call. Client inputs are passed in the browser through
`$c-props="{...}"`.


### Control Menu visibility

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/controlled-open/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledMenu(Component):
    template = """
      <section
        class="archive-controlled-demo"
        x-data="{open: false, disabled: false, locked: false, size: 'md', lastReason: 'none'}"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <c-CButton size="sm" @click="open = !open">Toggle from owner</c-CButton>
        <c-CMenu
          $c-props="{
            open,
            disabled,
            size,
            onOpenChange: (nextOpen, detail) => {
              lastReason = detail.reason;
              if (!locked) open = nextOpen;
            },
          }"
        >
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Controlled grimoire</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="translate">Translate runes</c-CMenuItem>
            <c-CMenuItem value="restore">Restore missing page</c-CMenuItem>
          </c-fill>
        </c-CMenu>
        <output x-text="`Last request: ${lastReason}`">Last request: none</output>
      </section>
    """

    css = """
      :where(.archive-controlled-demo) {
        display: grid;
        gap: 1rem;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

    """


preview_controls = (
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "disabled",
        "label": "Disabled",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "locked",
        "label": "Decline visibility requests",
        "type": "checkbox",
        "default": False,
    },
)


preview = ControlledMenu()

preview  # noqa: B018
````


A Boolean client `open` owns visibility. Omit it or pass `null` to release
control from the current committed state. `onOpenChange` reports requests;
forced ancestor/modal/disabled closes cannot be rejected.

## Add application choices

Checkbox and radio items model application preferences, not native Form
controls. They contribute no `FormData` and emit no native input/change event.


### Menu choices

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/choices/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuChoices(Component):
    template = """
      <section
        class="archive-choice-demo"
        x-data
        x-init="Alpine.store('archiveMenuChoices', {glow: 'mixed', script: 'elvish'})"
      >
        <c-CMenu c-close_on_select="False">
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Reading preferences</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuCheckboxItem
              value="glow"
              checked="mixed"
              $c-props="{
                checked: $store.archiveMenuChoices.glow,
                onCheckedChange: (value) => $store.archiveMenuChoices.glow = value,
              }"
            >
              Glow around enchanted passages
            </c-CMenuCheckboxItem>
            <c-CMenuSeparator />
            <c-CMenuRadioGroup
              value="elvish"
              $c-props="{
                value: $store.archiveMenuChoices.script,
                onValueChange: (value) => $store.archiveMenuChoices.script = value,
              }"
            >
              <c-fill name="label">Translation script</c-fill>
              <c-fill name="default">
                <c-CMenuRadioItem value="elvish">Elvish</c-CMenuRadioItem>
                <c-CMenuRadioItem value="draconic">Draconic</c-CMenuRadioItem>
                <c-CMenuRadioItem value="celestial">Celestial</c-CMenuRadioItem>
              </c-fill>
            </c-CMenuRadioGroup>
          </c-fill>
        </c-CMenu>
        <output
          x-text="`Glow: ${$store.archiveMenuChoices.glow}; script: ${$store.archiveMenuChoices.script}`"
        ></output>
      </section>
    """

    css = """
      :where(.archive-choice-demo) {
        display: grid;
        gap: 1rem;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = MenuChoices()

preview  # noqa: B018
````


Checkboxes support `false`, `true`, and `"mixed"`; activating mixed requests
true. A radio group owns one value. Set `close_on_select=False` when readers
should make several choices before leaving the Menu.

## Group commands

`CMenuGroup` owns a visible accessible label. `CMenuSeparator` divides adjacent
command families. Radio groups have their own optional label.


### Groups and separators

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/groups-and-separators/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuGroups(Component):
    template = """
      <section class="archive-group-demo">
        <c-CMenu>
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Archive sections</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuGroup>
              <c-fill name="label">Public halls</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="maps">Star maps</c-CMenuItem>
                <c-CMenuItem value="herbals">Moonlit herbals</c-CMenuItem>
              </c-fill>
            </c-CMenuGroup>
            <c-CMenuSeparator />
            <c-CMenuGroup>
              <c-fill name="label">Restricted vaults</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="prophecies">Sealed prophecies</c-CMenuItem>
                <c-CMenuItem value="curses" disabled>Curses under glass</c-CMenuItem>
              </c-fill>
            </c-CMenuGroup>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-group-demo) {
        min-block-size: 18rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = MenuGroups()

preview  # noqa: B018
````


Do not put separators first, last, or consecutively. Generic groups cannot be
nested inside generic groups.

## Nest submenus

`CMenuSubmenu` is one item plus another Menu surface. Give it a stable `value`,
a `label` fill, and direct declarations in its default fill.


### Nested command menus

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/submenus/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedMenus(Component):
    template = """
      <section class="archive-submenu-demo">
        <c-CMenu>
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Choose a collection</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuSubmenu value="skies">
              <c-fill name="label">Celestial archives</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="constellations">Constellations</c-CMenuItem>
                <c-CMenuSubmenu value="moons">
                  <c-fill name="label">Moon records</c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="silver">Silver moon</c-CMenuItem>
                    <c-CMenuItem value="ember">Ember moon</c-CMenuItem>
                  </c-fill>
                </c-CMenuSubmenu>
              </c-fill>
            </c-CMenuSubmenu>
            <c-CMenuSubmenu value="seas">
              <c-fill name="label">Sunken archives</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="tides">Tide almanacs</c-CMenuItem>
                <c-CMenuItem value="leviathans">Leviathan sightings</c-CMenuItem>
              </c-fill>
            </c-CMenuSubmenu>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-submenu-demo) {
        display: grid;
        place-items: start center;
        min-block-size: 22rem;
        padding-inline: 5rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NestedMenus()

preview  # noqa: B018
````


Arrow direction follows text direction. Pointer intent uses the submenu's
actual collision-resolved geometry. Deep nesting works, but one level is
usually easier to scan and operate.

## Keyboard and typeahead

Arrow Down/Up moves direct focus, Home/End reaches the edges, and printable
characters perform buffered prefix matching. Repeating one character cycles
matching labels. `loop` controls wrapping.


### Keyboard and typeahead

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/keyboard-and-typeahead/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuKeyboard(Component):
    template = """
      <section
        class="archive-keyboard-demo"
        x-data="{loop: true, close: false}"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <c-CMenu
          c-close_on_select="False"
          $c-props="{loop, closeOnSelect: close}"
        >
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Browse spell index</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="aegis">Aegis</c-CMenuItem>
            <c-CMenuItem value="alchemy">Alchemy</c-CMenuItem>
            <c-CMenuItem value="astral">Astral projection</c-CMenuItem>
            <c-CMenuItem value="binding">Binding</c-CMenuItem>
            <c-CMenuItem value="blessing">Blessing</c-CMenuItem>
            <c-CMenuItem value="conjuring">Conjuring</c-CMenuItem>
            <c-CMenuItem value="divination">Divination</c-CMenuItem>
            <c-CMenuItem value="enchantment">Enchantment</c-CMenuItem>
            <c-CMenuItem value="illusion">Illusion</c-CMenuItem>
            <c-CMenuItem value="restoration">Restoration</c-CMenuItem>
            <c-CMenuItem value="warding">Warding</c-CMenuItem>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-keyboard-demo) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 20rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-keyboard-demo) {
        --cui-menu-max-block-size: 13rem;
      }
    """


preview_controls = (
    {
        "name": "loop",
        "label": "Loop navigation",
        "type": "checkbox",
        "default": True,
    },
    {
        "name": "close",
        "label": "Close on action",
        "type": "checkbox",
        "default": False,
    },
)


preview = MenuKeyboard()

preview  # noqa: B018
````


Escape closes one submenu or the root. Tab closes the whole tree and continues
normal page order. Disabled items remain discoverable by Menu navigation but
never activate.

## Disable Menu safely

Menu `disabled` and native disabled `fieldset` ancestry are authoritative.
Buttons inside the Menu always use `type=button`, so commands never submit an
enclosing Form.


### Disabled Menu and native Forms

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/disabled-and-forms/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuDisabledAndForms(Component):
    template = """
      <section
        class="archive-disabled-demo"
        x-data="{locked: true, submits: 0}"
      >
        <c-CButton size="sm" @click="locked = !locked">
          Toggle archive seal
        </c-CButton>
        <form @submit.prevent="submits += 1">
          <fieldset :disabled="locked">
            <legend>Archive desk</legend>
            <c-CMenu>
              <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Desk commands</c-CButton>
              </c-fill>
              <c-fill name="default">
                <c-CMenuItem value="catalog">Catalog folio</c-CMenuItem>
                <c-CMenuItem value="sealed" disabled>Break royal seal</c-CMenuItem>
              </c-fill>
            </c-CMenu>
            <button type="submit">Submit native form</button>
          </fieldset>
        </form>
        <output x-text="`Form submits: ${submits}`">Form submits: 0</output>
      </section>
    """

    css = """
      :where(.archive-disabled-demo) {
        display: grid;
        gap: 0.75rem;
        min-block-size: 18rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-disabled-demo fieldset) {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.75rem;
      }
    """


preview = MenuDisabledAndForms()

preview  # noqa: B018
````


## Place the surface

Choose one of six logical block placements. `match_width` follows the activator
only up to the viewport-safe maximum. Submenus prefer logical inline-end, flip
inline, then use a centered block fallback when neither side is usable.


### Placement, width, and RTL

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/placement-and-rtl/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuPlacement(Component):
    template = """
      <section
        class="archive-placement-demo"
        x-data="{placement: 'bottom-start', rtl: false, match: true}"
        :dir="rtl ? 'rtl' : 'ltr'"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <c-CMenu $c-props="{placement, matchWidth: match}">
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton
              class_="archive-placement-demo__wide"
              c-disabled="activator_disabled"
              c-attrs="activator_attrs"
            >
              A deliberately wide enchanted-volume trigger
            </c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="north">Northern shelf</c-CMenuItem>
            <c-CMenuItem value="south">Southern shelf</c-CMenuItem>
            <c-CMenuSubmenu value="hidden-wing">
              <c-fill name="label">Hidden wing</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="mirrors">Hall of mirrors</c-CMenuItem>
              </c-fill>
            </c-CMenuSubmenu>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-placement-demo) {
        display: grid;
        gap: 1rem;
        justify-items: center;
        min-block-size: 21rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-placement-demo__wide) {
        inline-size: min(34rem, 150dvi);
      }
    """


preview_controls = (
    {
        "name": "placement",
        "label": "Placement",
        "type": "select",
        "default": "bottom-start",
        "options": (
            ("bottom-start", "Bottom start"),
            ("bottom", "Bottom"),
            ("bottom-end", "Bottom end"),
            ("top-start", "Top start"),
            ("top", "Top"),
            ("top-end", "Top end"),
        ),
    },
    {
        "name": "match",
        "label": "Match activator width",
        "type": "checkbox",
        "default": True,
    },
    {
        "name": "rtl",
        "label": "Right-to-left",
        "type": "checkbox",
        "default": False,
    },
)


preview = MenuPlacement()

preview  # noqa: B018
````


## Choose a size

`sm`, `md`, and `lg` change the whole family’s item geometry.


### Menu sizes

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/sizes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuSizes(Component):
    template = """
      <section class="archive-size-demo">
        <c-CMenu size="sm">
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton size="sm" c-disabled="activator_disabled" c-attrs="activator_attrs">Small</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="index">Pocket index</c-CMenuItem>
            <c-CMenuItem value="notes">Margin notes</c-CMenuItem>
          </c-fill>
        </c-CMenu>
        <c-CMenu size="md">
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Medium</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="index">Reading index</c-CMenuItem>
            <c-CMenuItem value="notes">Scribe notes</c-CMenuItem>
          </c-fill>
        </c-CMenu>
        <c-CMenu size="lg">
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton size="lg" c-disabled="activator_disabled" c-attrs="activator_attrs">Large</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="index">Grand index</c-CMenuItem>
            <c-CMenuItem value="notes">Archivist notes</c-CMenuItem>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-size-demo) {
        display: flex;
        flex-wrap: wrap;
        align-items: start;
        gap: 1rem;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = MenuSizes()

preview  # noqa: B018
````


## Customize Menu

Override public variables on an ancestor or one wrapper. Stable part selectors
target the surface, item regions, groups, indicators, separators, and submenus.


### Theme archive menus

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedMenus(Component):
    template = """
      <section class="archive-theme-demo">
        <div class="archive-theme-demo__moon">
          <c-CMenu>
            <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
              <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Moon archive</c-CButton>
            </c-fill>
            <c-fill name="default">
              <c-CMenuItem value="phases">Moon phases</c-CMenuItem>
              <c-CMenuItem value="eclipses">Eclipse records</c-CMenuItem>
            </c-fill>
          </c-CMenu>
        </div>
        <div class="archive-theme-demo__ember">
          <c-CMenu>
            <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
              <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Ember archive</c-CButton>
            </c-fill>
            <c-fill name="default">
              <c-CMenuItem value="dragons">Dragon chronicles</c-CMenuItem>
              <c-CMenuItem value="ashes" intent="danger">Destroy ash record</c-CMenuItem>
            </c-fill>
          </c-CMenu>
        </div>
      </section>
    """

    css = """
      :where(.archive-theme-demo) {
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
        min-block-size: 18rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-theme-demo__moon) {
        --cui-menu-background: light-dark(#f4f2ff, #17142d);
        --cui-menu-border-color: light-dark(#8f83c7, #7065aa);
        --cui-menu-focus-background: light-dark(#4c3e92, #b6a9ff);
        --cui-menu-focus-foreground: light-dark(#ffffff, #17142d);
        --cui-menu-radius: 1rem;
      }

      :where(.archive-theme-demo__ember) {
        --cui-menu-background: light-dark(#fff7ed, #2a1710);
        --cui-menu-border-color: light-dark(#d97706, #f59e0b);
        --cui-menu-focus-background: light-dark(#9a3412, #fdba74);
        --cui-menu-focus-foreground: light-dark(#ffffff, #2a1710);
        --cui-menu-danger-color: light-dark(#991b1b, #fecaca);
        --cui-menu-radius: 0.35rem;
      }
    """


preview = CustomizedMenus()

preview  # noqa: B018
````


Every styled family member exposes top-level `class_` and `style` on its
documented root. Unlayered consumer CSS overrides Citry UI defaults; named
layers follow the site-wide layer-order contract.

## Compose with other overlays

Menu, Popover, Tooltip, and Dialog share one logical layer coordinator. Closing
an ancestor closes descendant submenus first. Opening an unrelated modal Dialog
suppresses outside anchored layers and gives the Dialog Escape/focus ownership.


### Overlay ownership and cleanup

[Open the rendered preview](/v/0.4.0/ui-library/components/menu/_previews/lifecycle/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuLifecycle(Component):
    template = """
      <section class="archive-lifecycle-demo" x-data>
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open reading room</c-CButton>
          </c-fill>
          <c-fill name="title">Reading room</c-fill>
          <c-fill name="default">
            <c-CMenu>
              <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Nested folio menu</c-CButton>
              </c-fill>
              <c-fill name="default">
                <c-CMenuItem value="inspect">Inspect binding</c-CMenuItem>
                <c-CMenuSubmenu value="editions">
                  <c-fill name="label">Other editions</c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="first">First edition</c-CMenuItem>
                  </c-fill>
                </c-CMenuSubmenu>
              </c-fill>
            </c-CMenu>
          </c-fill>
        </c-CPopover>
        <c-CButton @click="$refs.vault.showModal()">Open modal vault</c-CButton>
        <dialog x-ref="vault" aria-labelledby="vault-title">
          <h2 id="vault-title">Royal vault</h2>
          <p>Opening this modal closes unrelated anchored layers.</p>
          <button type="button" @click="$refs.vault.close()">Close vault</button>
        </dialog>
      </section>
    """

    css = """
      :where(.archive-lifecycle-demo) {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        min-block-size: 20rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-lifecycle-demo dialog) {
        max-inline-size: min(26rem, calc(100dvi - 2rem));
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, CanvasText 24%, transparent);
        border-radius: 0.85rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.archive-lifecycle-demo dialog::backdrop) {
        background: rgb(15 23 42 / 45%);
      }
    """


preview = MenuLifecycle()

preview  # noqa: B018
````


## Trust boundary

Text is escaped. Values are plain, nonempty canonical strings; generated IDs
do not expose raw values. `href` remains a trusted application URL boundary.
Attribute maps reject owned semantics, focus, visibility, anchoring, structural
Alpine directives, and Citry runtime namespaces. Use Popover when item content
needs links, Buttons, inputs, editing, or independent Tab stops.

## API reference

### Inputs

#### CMenu server inputs

Server inputs are passed in a template through `<c-CMenu ... />` or in Python through
`CMenu(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-server-inputs-id"></span>`id` | `str | None` | generated | Sets the Menu surface and activator relationship identity. |
| <span id="menu-input-cmenu-server-inputs-open"></span>`open` | `bool` | `False` | Sets initial visibility and the uncontrolled fallback. |
| <span id="menu-input-cmenu-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables the activator and force-closes the tree. Native disabled fieldset ancestry also applies. |
| <span id="menu-input-cmenu-server-inputs-loop"></span>`loop` | `bool` | `True` | Wraps arrow navigation and typeahead matching. |
| <span id="menu-input-cmenu-server-inputs-placement"></span>`placement` | `"top-start" | "top" | "top-end" | "bottom-start" | "bottom" | "bottom-end"` ([`CMenuPlacement`](#menu-interface-placement)) | `"bottom-start"` | Sets the preferred logical root placement. |
| <span id="menu-input-cmenu-server-inputs-match-width"></span>`match_width` | `bool` | `False` | Matches the activator width up to the viewport-safe maximum. |
| <span id="menu-input-cmenu-server-inputs-close-on-select"></span>`close_on_select` | `bool` | `True` | Sets the default command and choice close policy. |
| <span id="menu-input-cmenu-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CMenuSize`](#menu-interface-size)) | `"md"` | Sets item geometry for the whole tree. |
| <span id="menu-input-cmenu-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#menu-interface-class-value)) | `None` | Adds surface classes and merges with `attrs`. |
| <span id="menu-input-cmenu-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#menu-interface-style-value)) | `None` | Adds surface styles; private anchor ownership merges last. |
| <span id="menu-input-cmenu-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native, ARIA, Alpine, and data attributes to the Menu surface. |

</div>

#### CMenu client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CMenu />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-client-inputs-open"></span>`open` | `boolean | null` | Releases control from committed state. `null` has the same effect. | Controls root visibility while supplied as a Boolean. |
| <span id="menu-input-cmenu-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls local disabledness; native fieldset disabledness remains authoritative. |
| <span id="menu-input-cmenu-client-inputs-loop"></span>`loop` | `boolean` | Uses the server input. | Controls keyboard wrapping. |
| <span id="menu-input-cmenu-client-inputs-placement"></span>`placement` | `six logical placement strings` ([`CMenuPlacement`](#menu-interface-placement)) | Uses the server input. | Controls requested placement. |
| <span id="menu-input-cmenu-client-inputs-match-width"></span>`matchWidth` | `boolean` | Uses the server input. | Controls clamped activator-width matching. |
| <span id="menu-input-cmenu-client-inputs-close-on-select"></span>`closeOnSelect` | `boolean` | Uses the server input. | Controls the tree default close policy. |
| <span id="menu-input-cmenu-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CMenuSize`](#menu-interface-size)) | Uses the server input. | Controls tree geometry. |
| <span id="menu-input-cmenu-client-inputs-on-open-change"></span>`onOpenChange` | `function` | Does not notify a visibility callback. | Receives visibility requests and forced close notices. |
| <span id="menu-input-cmenu-client-inputs-on-action"></span>`onAction` | `function` | Does not notify a root action callback. | Receives valued command and choice activations. |

</div>

#### CMenuItem server inputs

Server inputs are passed in a template through `<c-CMenuItem ... />` or in Python through
`CMenuItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-item-server-inputs-value"></span>`value` | `str | None` | `None` | Supplies optional canonical command identity for root `onAction`; rejected with `href`. |
| <span id="menu-input-cmenu-item-server-inputs-href"></span>`href` | `str | None` | `None` | Renders a real anchor and preserves native navigation. |
| <span id="menu-input-cmenu-item-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Makes the item focusable but inactive. |
| <span id="menu-input-cmenu-item-server-inputs-close-on-select"></span>`close_on_select` | `bool | None` | `None` | Overrides the root close policy when supplied. |
| <span id="menu-input-cmenu-item-server-inputs-intent"></span>`intent` | `"default" | "danger"` ([`CMenuIntent`](#menu-interface-intent)) | `"default"` | Sets visual emphasis. |
| <span id="menu-input-cmenu-item-server-inputs-text-value"></span>`text_value` | `str | None` | `None` | Overrides label-derived typeahead text. |
| <span id="menu-input-cmenu-item-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#menu-interface-class-value)) | `None` | Adds semantic-root classes. |
| <span id="menu-input-cmenu-item-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#menu-interface-style-value)) | `None` | Adds semantic-root styles. |
| <span id="menu-input-cmenu-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed semantic-root attributes. |

</div>

#### CMenuItem client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CMenuItem />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-item-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls inactive behavior and `aria-disabled`. |
| <span id="menu-input-cmenu-item-client-inputs-close-on-select"></span>`closeOnSelect` | `boolean | null` | Inherits the root policy. `null` has the same effect. | Controls per-item close behavior. |
| <span id="menu-input-cmenu-item-client-inputs-intent"></span>`intent` | `"default" | "danger"` ([`CMenuIntent`](#menu-interface-intent)) | Uses the server input. | Controls emphasis and `data-intent`. |
| <span id="menu-input-cmenu-item-client-inputs-text-value"></span>`textValue` | `string | null` | Uses the server fallback. | Controls typeahead text; a null fallback may read current label text. |

</div>

#### CMenuCheckboxItem server inputs

Server inputs are passed in a template through `<c-CMenuCheckboxItem ... />` or in Python
through `CMenuCheckboxItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-checkbox-item-server-inputs-value"></span>`value` | `str` | required | Sets unique canonical choice identity. |
| <span id="menu-input-cmenu-checkbox-item-server-inputs-checked"></span>`checked` | `bool | "mixed"` ([`CMenuChecked`](#menu-interface-checked)) | `False` | Sets initial checked state. |
| <span id="menu-input-cmenu-checkbox-item-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Makes the item focusable but inactive. |
| <span id="menu-input-cmenu-checkbox-item-server-inputs-close-on-select"></span>`close_on_select` | `bool | None` | `None` | Overrides the root close policy. |
| <span id="menu-input-cmenu-checkbox-item-server-inputs-text-value"></span>`text_value` | `str | None` | `None` | Overrides label-derived typeahead text. |
| <span id="menu-input-cmenu-checkbox-item-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#menu-interface-class-value)) | `None` | Adds item classes. |
| <span id="menu-input-cmenu-checkbox-item-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#menu-interface-style-value)) | `None` | Adds item styles. |
| <span id="menu-input-cmenu-checkbox-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed item attributes. |

</div>

#### CMenuCheckboxItem client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CMenuCheckboxItem />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-checkbox-item-client-inputs-checked"></span>`checked` | `boolean | "mixed" | null` ([`CMenuChecked`](#menu-interface-checked)) | Releases control from committed state. `null` has the same effect. | Controls checked state. |
| <span id="menu-input-cmenu-checkbox-item-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls inactive behavior. |
| <span id="menu-input-cmenu-checkbox-item-client-inputs-close-on-select"></span>`closeOnSelect` | `boolean | null` | Inherits the root policy. | Controls per-item close behavior. |
| <span id="menu-input-cmenu-checkbox-item-client-inputs-text-value"></span>`textValue` | `string | null` | Uses the server fallback. | Controls typeahead text. |
| <span id="menu-input-cmenu-checkbox-item-client-inputs-on-checked-change"></span>`onCheckedChange` | `function` | Does not notify a checked callback. | Receives requested checked values. |

</div>

#### CMenuRadioGroup server inputs

Server inputs are passed in a template through `<c-CMenuRadioGroup ... />` or in Python
through `CMenuRadioGroup(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-radio-group-server-inputs-value"></span>`value` | `str` | required | Sets the required initial direct-radio selection. |
| <span id="menu-input-cmenu-radio-group-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#menu-interface-class-value)) | `None` | Adds group classes. |
| <span id="menu-input-cmenu-radio-group-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#menu-interface-style-value)) | `None` | Adds group styles. |
| <span id="menu-input-cmenu-radio-group-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed group attributes. |

</div>

#### CMenuRadioGroup client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CMenuRadioGroup />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-radio-group-client-inputs-value"></span>`value` | `string | null` | Releases control from committed state. `null` has the same effect. | Controls the selected radio value. |
| <span id="menu-input-cmenu-radio-group-client-inputs-on-value-change"></span>`onValueChange` | `function` | Does not notify a value callback. | Receives activation and structural-removal value requests. |

</div>

#### CMenuRadioItem server inputs

Server inputs are passed in a template through `<c-CMenuRadioItem ... />` or in Python
through `CMenuRadioItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-radio-item-server-inputs-value"></span>`value` | `str` | required | Sets canonical identity unique in the radio group. |
| <span id="menu-input-cmenu-radio-item-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Makes the item focusable but inactive. |
| <span id="menu-input-cmenu-radio-item-server-inputs-close-on-select"></span>`close_on_select` | `bool | None` | `None` | Overrides the root close policy. |
| <span id="menu-input-cmenu-radio-item-server-inputs-text-value"></span>`text_value` | `str | None` | `None` | Overrides label-derived typeahead text. |
| <span id="menu-input-cmenu-radio-item-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#menu-interface-class-value)) | `None` | Adds item classes. |
| <span id="menu-input-cmenu-radio-item-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#menu-interface-style-value)) | `None` | Adds item styles. |
| <span id="menu-input-cmenu-radio-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed item attributes. |

</div>

#### CMenuRadioItem client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CMenuRadioItem />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-radio-item-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls inactive behavior. |
| <span id="menu-input-cmenu-radio-item-client-inputs-close-on-select"></span>`closeOnSelect` | `boolean | null` | Inherits the root policy. | Controls per-item close behavior. |
| <span id="menu-input-cmenu-radio-item-client-inputs-text-value"></span>`textValue` | `string | null` | Uses the server fallback. | Controls typeahead text. |

</div>

#### CMenuGroup server inputs

Server inputs are passed in a template through `<c-CMenuGroup ... />` or in Python through
`CMenuGroup(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-group-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#menu-interface-class-value)) | `None` | Adds group classes. |
| <span id="menu-input-cmenu-group-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#menu-interface-style-value)) | `None` | Adds group styles. |
| <span id="menu-input-cmenu-group-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed group attributes. |

</div>

#### CMenuSeparator server inputs

Server inputs are passed in a template through `<c-CMenuSeparator ... />` or in Python
through `CMenuSeparator(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-separator-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#menu-interface-class-value)) | `None` | Adds separator classes. |
| <span id="menu-input-cmenu-separator-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#menu-interface-style-value)) | `None` | Adds separator styles. |
| <span id="menu-input-cmenu-separator-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed separator attributes. |

</div>

#### CMenuSubmenu server inputs

Server inputs are passed in a template through `<c-CMenuSubmenu ... />` or in Python through
`CMenuSubmenu(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-submenu-server-inputs-value"></span>`value` | `str` | required | Sets a canonical path segment unique at its menu level. |
| <span id="menu-input-cmenu-submenu-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Makes the trigger inactive and force-closes its child. |
| <span id="menu-input-cmenu-submenu-server-inputs-intent"></span>`intent` | `"default" | "danger"` ([`CMenuIntent`](#menu-interface-intent)) | `"default"` | Sets trigger emphasis. |
| <span id="menu-input-cmenu-submenu-server-inputs-text-value"></span>`text_value` | `str | None` | `None` | Overrides label-derived typeahead text. |
| <span id="menu-input-cmenu-submenu-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#menu-interface-class-value)) | `None` | Adds neutral-wrapper classes. |
| <span id="menu-input-cmenu-submenu-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#menu-interface-style-value)) | `None` | Adds neutral-wrapper styles inherited by the child surface. |
| <span id="menu-input-cmenu-submenu-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed neutral-wrapper attributes. |
| <span id="menu-input-cmenu-submenu-server-inputs-trigger-attrs"></span>`trigger_attrs` | `Mapping[str, object] | None` | `None` | Adds allowed submenu-trigger attributes. |
| <span id="menu-input-cmenu-submenu-server-inputs-menu-attrs"></span>`menu_attrs` | `Mapping[str, object] | None` | `None` | Adds allowed child Menu-surface attributes. |

</div>

#### CMenuSubmenu client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CMenuSubmenu />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="menu-input-cmenu-submenu-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls inactive behavior and child closure. |
| <span id="menu-input-cmenu-submenu-client-inputs-intent"></span>`intent` | `"default" | "danger"` ([`CMenuIntent`](#menu-interface-intent)) | Uses the server input. | Controls trigger emphasis. |
| <span id="menu-input-cmenu-submenu-client-inputs-text-value"></span>`textValue` | `string | null` | Uses the server fallback. | Controls typeahead text. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CMenu slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="menu-slot-cmenu-slots-activator"></span>`activator` | yes | `{activator_attrs: dict[str, object], activator_disabled: bool}` ([`CMenuActivatorSlotData`](#menu-interface-cmenu-activator-slot-data)) | none |
| <span id="menu-slot-cmenu-slots-default"></span>`default` | yes | `{}` ([`CMenuDefaultSlotData`](#menu-interface-cmenu-default-slot-data)) | none |

</div>

#### CMenuItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="menu-slot-cmenu-item-slots-start"></span>`start` | no | `{}` ([`CMenuItemStartSlotData`](#menu-interface-cmenu-item-start-slot-data)) | omitted |
| <span id="menu-slot-cmenu-item-slots-default"></span>`default` | yes | `{}` ([`CMenuItemDefaultSlotData`](#menu-interface-cmenu-item-default-slot-data)) | none |
| <span id="menu-slot-cmenu-item-slots-description"></span>`description` | no | `{}` ([`CMenuItemDescriptionSlotData`](#menu-interface-cmenu-item-description-slot-data)) | omitted |
| <span id="menu-slot-cmenu-item-slots-end"></span>`end` | no | `{}` ([`CMenuItemEndSlotData`](#menu-interface-cmenu-item-end-slot-data)) | omitted |

</div>

#### CMenuCheckboxItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="menu-slot-cmenu-checkbox-item-slots-start"></span>`start` | no | `{}` ([`CMenuItemStartSlotData`](#menu-interface-cmenu-item-start-slot-data)) | omitted |
| <span id="menu-slot-cmenu-checkbox-item-slots-default"></span>`default` | yes | `{}` ([`CMenuItemDefaultSlotData`](#menu-interface-cmenu-item-default-slot-data)) | none |
| <span id="menu-slot-cmenu-checkbox-item-slots-description"></span>`description` | no | `{}` ([`CMenuItemDescriptionSlotData`](#menu-interface-cmenu-item-description-slot-data)) | omitted |
| <span id="menu-slot-cmenu-checkbox-item-slots-end"></span>`end` | no | `{}` ([`CMenuItemEndSlotData`](#menu-interface-cmenu-item-end-slot-data)) | omitted |

</div>

#### CMenuRadioItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="menu-slot-cmenu-radio-item-slots-start"></span>`start` | no | `{}` ([`CMenuItemStartSlotData`](#menu-interface-cmenu-item-start-slot-data)) | omitted |
| <span id="menu-slot-cmenu-radio-item-slots-default"></span>`default` | yes | `{}` ([`CMenuItemDefaultSlotData`](#menu-interface-cmenu-item-default-slot-data)) | none |
| <span id="menu-slot-cmenu-radio-item-slots-description"></span>`description` | no | `{}` ([`CMenuItemDescriptionSlotData`](#menu-interface-cmenu-item-description-slot-data)) | omitted |
| <span id="menu-slot-cmenu-radio-item-slots-end"></span>`end` | no | `{}` ([`CMenuItemEndSlotData`](#menu-interface-cmenu-item-end-slot-data)) | omitted |

</div>

#### CMenuRadioGroup slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="menu-slot-cmenu-radio-group-slots-label"></span>`label` | no | `{}` ([`CMenuRadioGroupLabelSlotData`](#menu-interface-cmenu-radio-group-label-slot-data)) | omitted |
| <span id="menu-slot-cmenu-radio-group-slots-default"></span>`default` | yes | `{}` ([`CMenuRadioGroupDefaultSlotData`](#menu-interface-cmenu-radio-group-default-slot-data)) | none |

</div>

#### CMenuGroup slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="menu-slot-cmenu-group-slots-label"></span>`label` | yes | `{}` ([`CMenuGroupLabelSlotData`](#menu-interface-cmenu-group-label-slot-data)) | none |
| <span id="menu-slot-cmenu-group-slots-default"></span>`default` | yes | `{}` ([`CMenuGroupDefaultSlotData`](#menu-interface-cmenu-group-default-slot-data)) | none |

</div>

#### CMenuSubmenu slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="menu-slot-cmenu-submenu-slots-start"></span>`start` | no | `{}` ([`CMenuSubmenuStartSlotData`](#menu-interface-cmenu-submenu-start-slot-data)) | omitted |
| <span id="menu-slot-cmenu-submenu-slots-label"></span>`label` | yes | `{}` ([`CMenuSubmenuLabelSlotData`](#menu-interface-cmenu-submenu-label-slot-data)) | none |
| <span id="menu-slot-cmenu-submenu-slots-description"></span>`description` | no | `{}` ([`CMenuSubmenuDescriptionSlotData`](#menu-interface-cmenu-submenu-description-slot-data)) | omitted |
| <span id="menu-slot-cmenu-submenu-slots-end"></span>`end` | no | `{}` ([`CMenuSubmenuEndSlotData`](#menu-interface-cmenu-submenu-end-slot-data)) | Built-in direction-aware chevron. |
| <span id="menu-slot-cmenu-submenu-slots-default"></span>`default` | yes | `{}` ([`CMenuSubmenuDefaultSlotData`](#menu-interface-cmenu-submenu-default-slot-data)) | none |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CMenu events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="menu-event-cmenu-events-on-open-change"></span>`onOpenChange` | `(requestedOpen: boolean, detail: CMenuOpenChangeDetail) => void` ([`CMenuOpenChangeDetail`](#menu-interface-cmenu-open-change-detail)) | A visibility request occurs or a forced safety close changes effective open state. | `{reason, controlled, forced, source}` ([`CMenuOpenChangeDetail`](#menu-interface-cmenu-open-change-detail)) | Uncontrolled requests commit before notification; controlled requests wait except forced closes. |
| <span id="menu-event-cmenu-events-on-action"></span>`onAction` | `(value: string, detail: CMenuActionDetail) => void` ([`CMenuActionDetail`](#menu-interface-cmenu-action-detail)) | An enabled valued command or choice activates. | `{kind, item, event, path}` ([`CMenuActionDetail`](#menu-interface-cmenu-action-detail)) | Fires once after a choice-specific request and before the close request. Links and anonymous commands do not fire it. |

</div>

#### CMenuCheckboxItem events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="menu-event-cmenu-checkbox-item-events-on-checked-change"></span>`onCheckedChange` | `(requestedChecked: boolean, detail: CMenuCheckedChangeDetail) => void` ([`CMenuCheckedChangeDetail`](#menu-interface-cmenu-checked-change-detail)) | An enabled checkbox item activates. | `{checked, previousChecked, controlled, item, event, path}` ([`CMenuCheckedChangeDetail`](#menu-interface-cmenu-checked-change-detail)) | Controlled items wait for owner acceptance. |

</div>

#### CMenuRadioGroup events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="menu-event-cmenu-radio-group-events-on-value-change"></span>`onValueChange` | `(requestedValue: string, detail: CMenuRadioChangeDetail) => void` ([`CMenuRadioChangeDetail`](#menu-interface-cmenu-radio-change-detail)) | A different enabled radio activates or the selected radio is structurally removed in either ownership mode. | `{value, previousValue, reason, controlled, item, event, path}` ([`CMenuRadioChangeDetail`](#menu-interface-cmenu-radio-change-detail)) | Controlled groups wait for owner acceptance. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CMenu CSS variables

Apply these variables to `CMenu` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="menu-css-cmenu-css-variables-cui-menu-background"></span>`--cui-menu-background` | `color` | Menu surfaces. | `Canvas` |
| <span id="menu-css-cmenu-css-variables-cui-menu-foreground"></span>`--cui-menu-foreground` | `color` | Item text. | `CanvasText` |
| <span id="menu-css-cmenu-css-variables-cui-menu-muted-color"></span>`--cui-menu-muted-color` | `color` | Descriptions, labels, and shortcuts. | `color-mix(in srgb, current foreground 72%, transparent)` |
| <span id="menu-css-cmenu-css-variables-cui-menu-border-color"></span>`--cui-menu-border-color` | `color` | Surface and separator boundaries. | `color-mix(in srgb, CanvasText 18%, transparent)` |
| <span id="menu-css-cmenu-css-variables-cui-menu-border-width"></span>`--cui-menu-border-width` | `length` | Surface boundary width. | `1px` |
| <span id="menu-css-cmenu-css-variables-cui-menu-radius"></span>`--cui-menu-radius` | `length` | Surface corners. | `0.75rem` |
| <span id="menu-css-cmenu-css-variables-cui-menu-shadow"></span>`--cui-menu-shadow` | `shadow` | Root elevation. | `0 0.75rem 2rem rgb(15 23 42 / 18%)` |
| <span id="menu-css-cmenu-css-variables-cui-menu-submenu-shadow"></span>`--cui-menu-submenu-shadow` | `shadow` | Nested elevation. | `0 1rem 2.5rem rgb(15 23 42 / 22%)` |
| <span id="menu-css-cmenu-css-variables-cui-menu-inline-size"></span>`--cui-menu-inline-size` | `length` | Preferred width. | `14rem` |
| <span id="menu-css-cmenu-css-variables-cui-menu-min-inline-size"></span>`--cui-menu-min-inline-size` | `length` | Minimum useful inline submenu corridor. | `10rem` |
| <span id="menu-css-cmenu-css-variables-cui-menu-max-inline-size"></span>`--cui-menu-max-inline-size` | `length` | Viewport-safe width. | `calc(100dvi - 1rem)` |
| <span id="menu-css-cmenu-css-variables-cui-menu-max-block-size"></span>`--cui-menu-max-block-size` | `length` | Scroll limit. | `min(24rem, calc(100dvb - 1rem))` |
| <span id="menu-css-cmenu-css-variables-cui-menu-padding"></span>`--cui-menu-padding` | `length` | Surface edge spacing. | `0.375rem` |
| <span id="menu-css-cmenu-css-variables-cui-menu-item-block-size"></span>`--cui-menu-item-block-size` | `length` | Item minimum height. | `Size-derived.` |
| <span id="menu-css-cmenu-css-variables-cui-menu-item-padding-inline"></span>`--cui-menu-item-padding-inline` | `length` | Item inline spacing. | `Size-derived.` |
| <span id="menu-css-cmenu-css-variables-cui-menu-item-gap"></span>`--cui-menu-item-gap` | `length` | Item-region gap. | `0.625rem` |
| <span id="menu-css-cmenu-css-variables-cui-menu-item-radius"></span>`--cui-menu-item-radius` | `length` | Item corners. | `0.5rem` |
| <span id="menu-css-cmenu-css-variables-cui-menu-hover-background"></span>`--cui-menu-hover-background` | `color` | Pointer hover fill. | `color-mix(in srgb, CanvasText 8%, transparent)` |
| <span id="menu-css-cmenu-css-variables-cui-menu-focus-background"></span>`--cui-menu-focus-background` | `color` | Focused item fill. | `light-dark(#175cd3, #84adff)` |
| <span id="menu-css-cmenu-css-variables-cui-menu-focus-foreground"></span>`--cui-menu-focus-foreground` | `color` | Focused item content. | `light-dark(#ffffff, #101828)` |
| <span id="menu-css-cmenu-css-variables-cui-menu-focus-outline-color"></span>`--cui-menu-focus-outline-color` | `color` | Focus-visible outline. | `light-dark(#175cd3, #84adff)` |
| <span id="menu-css-cmenu-css-variables-cui-menu-danger-color"></span>`--cui-menu-danger-color` | `color` | Destructive item content. | `light-dark(#b42318, #fda29b)` |
| <span id="menu-css-cmenu-css-variables-cui-menu-disabled-opacity"></span>`--cui-menu-disabled-opacity` | `number` | Disabled content opacity. | `0.5` |
| <span id="menu-css-cmenu-css-variables-cui-menu-offset"></span>`--cui-menu-offset` | `length` | Root anchor gap. | `0.375rem` |
| <span id="menu-css-cmenu-css-variables-cui-menu-submenu-offset"></span>`--cui-menu-submenu-offset` | `length` | Nested anchor gap. | `0.25rem` |
| <span id="menu-css-cmenu-css-variables-cui-menu-duration"></span>`--cui-menu-duration` | `time` | Entry and exit duration. | `120ms` |
| <span id="menu-css-cmenu-css-variables-cui-menu-easing"></span>`--cui-menu-easing` | `easing` | Entry and exit easing. | `cubic-bezier(0.2, 0.8, 0.2, 1)` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CMenu attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="menu-attribute-cmenu-attributes-popover"></span>`popover` | Menu surface | `"manual"` | Native top-layer presence with Citry dismissal. |
| <span id="menu-attribute-cmenu-attributes-role"></span>`role` | Menu surface | `"menu"` | Application Menu composite. |
| <span id="menu-attribute-cmenu-attributes-aria-labelledby"></span>`aria-labelledby` | Menu surface | `activator IDREF` | Names the Menu from its Button. |
| <span id="menu-attribute-cmenu-attributes-data-open"></span>`data-open` | Menu surface | `present | absent` | Mirrors logical open ownership. |
| <span id="menu-attribute-cmenu-attributes-data-placement"></span>`data-placement` | Menu surface | `six requested placement strings` ([`CMenuPlacement`](#menu-interface-placement)) | Requested logical placement, not collision result. |
| <span id="menu-attribute-cmenu-attributes-data-match-width"></span>`data-match-width` | Menu surface | `present | absent` | Indicates clamped activator-width matching. |
| <span id="menu-attribute-cmenu-attributes-data-size"></span>`data-size` | Menu surface | `"sm" | "md" | "lg"` ([`CMenuSize`](#menu-interface-size)) | Effective item geometry. |
| <span id="menu-attribute-cmenu-attributes-aria-haspopup"></span>`aria-haspopup` | Activator Button | `"menu"` | Announces the controlled popup kind. |
| <span id="menu-attribute-cmenu-attributes-aria-controls"></span>`aria-controls` | Activator Button | `IDREF` | References the Menu surface. |
| <span id="menu-attribute-cmenu-attributes-aria-expanded"></span>`aria-expanded` | Activator Button | `"true" | "false"` | Mirrors logical open state. |

</div>

#### CMenuItem attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="menu-attribute-cmenu-item-attributes-role"></span>`role` | Item root | `"menuitem"` | Command or native-link semantics. |
| <span id="menu-attribute-cmenu-item-attributes-aria-labelledby"></span>`aria-labelledby` | Item root | `owned label IDREF` | Exact visible accessible name. |
| <span id="menu-attribute-cmenu-item-attributes-aria-describedby"></span>`aria-describedby` | Item root | `description IDREF | absent` | Optional separate description. |
| <span id="menu-attribute-cmenu-item-attributes-aria-disabled"></span>`aria-disabled` | Item root | `"true" | absent` | Focusable inactive item. |
| <span id="menu-attribute-cmenu-item-attributes-data-disabled"></span>`data-disabled` | Item root | `present | absent` | Disabled styling mirror. |
| <span id="menu-attribute-cmenu-item-attributes-data-intent"></span>`data-intent` | Item root | `"default" | "danger"` ([`CMenuIntent`](#menu-interface-intent)) | Visual emphasis. |

</div>

#### CMenuCheckboxItem attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="menu-attribute-cmenu-checkbox-item-attributes-role"></span>`role` | Item Button | `"menuitemcheckbox"` | Checkable command semantics. |
| <span id="menu-attribute-cmenu-checkbox-item-attributes-aria-checked"></span>`aria-checked` | Item Button | `"false" | "true" | "mixed"` | Effective checked value. |
| <span id="menu-attribute-cmenu-checkbox-item-attributes-data-checked"></span>`data-checked` | Item Button | `"false" | "true" | "mixed"` | Styling mirror. |

</div>

#### CMenuRadioItem attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="menu-attribute-cmenu-radio-item-attributes-role"></span>`role` | Item Button | `"menuitemradio"` | Exclusive choice semantics. |
| <span id="menu-attribute-cmenu-radio-item-attributes-aria-checked"></span>`aria-checked` | Item Button | `"false" | "true"` | Effective group selection. |
| <span id="menu-attribute-cmenu-radio-item-attributes-data-checked"></span>`data-checked` | Item Button | `"false" | "true"` | Styling mirror. |

</div>

#### CMenuGroup attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="menu-attribute-cmenu-group-attributes-role"></span>`role` | Group root | `"group"` | Owns grouped direct Menu items. |
| <span id="menu-attribute-cmenu-group-attributes-aria-labelledby"></span>`aria-labelledby` | Group root | `group-label IDREF` | Names the group from its visible label. |

</div>

#### CMenuRadioGroup attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="menu-attribute-cmenu-radio-group-attributes-role"></span>`role` | Radio-group root | `"group"` | Owns exclusive radio items. |
| <span id="menu-attribute-cmenu-radio-group-attributes-aria-labelledby"></span>`aria-labelledby` | Radio-group root | `label IDREF | absent` | Names the group when a label is supplied. |

</div>

#### CMenuSeparator attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="menu-attribute-cmenu-separator-attributes-role"></span>`role` | Horizontal rule | `"separator"` | Divides vertically stacked item families. |

</div>

#### CMenuSubmenu attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="menu-attribute-cmenu-submenu-attributes-role"></span>`role` | Wrapper / trigger / surface | `"none" / "menuitem" / "menu"` | Keeps the trigger and immediate sibling child Menu relationship. |
| <span id="menu-attribute-cmenu-submenu-attributes-aria-haspopup"></span>`aria-haspopup` | Submenu trigger | `"menu"` | Announces the child Menu. |
| <span id="menu-attribute-cmenu-submenu-attributes-aria-controls"></span>`aria-controls` | Submenu trigger | `child Menu IDREF` | References the child surface. |
| <span id="menu-attribute-cmenu-submenu-attributes-aria-expanded"></span>`aria-expanded` | Submenu trigger | `"true" | "false"` | Mirrors child open state. |
| <span id="menu-attribute-cmenu-submenu-attributes-data-open"></span>`data-open` | Wrapper / child surface | `present | absent` | Mirrors logical child open ownership. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CMenu selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="menu-selector-cmenu-selectors-menu"></span>`[data-citry-ui-part="menu"]` | Root or submenu surface | Popover presence and collection focus. |
| <span id="menu-selector-cmenu-selectors-menu-item"></span>`[data-citry-ui-part="menu-item"]` | Command/link/check/radio semantic root | Item styling. |
| <span id="menu-selector-cmenu-selectors-menu-item-start"></span>`[data-citry-ui-part="menu-item-start"]` | Decorative start wrapper | Start-region layout. |
| <span id="menu-selector-cmenu-selectors-menu-item-label"></span>`[data-citry-ui-part="menu-item-label"]` | Visible item label | Layout and exact accessible-name target. |
| <span id="menu-selector-cmenu-selectors-menu-item-description"></span>`[data-citry-ui-part="menu-item-description"]` | Optional description | Supporting text and accessible description. |
| <span id="menu-selector-cmenu-selectors-menu-item-end"></span>`[data-citry-ui-part="menu-item-end"]` | Decorative end wrapper | Shortcut/end-region layout. |
| <span id="menu-selector-cmenu-selectors-menu-choice-indicator"></span>`[data-citry-ui-part="menu-choice-indicator"]` | Decorative choice indicator | Checked/radio marker. |
| <span id="menu-selector-cmenu-selectors-menu-group"></span>`[data-citry-ui-part="menu-group"]` | Labelled group root | Group layout. |
| <span id="menu-selector-cmenu-selectors-menu-group-label"></span>`[data-citry-ui-part="menu-group-label"]` | Visible group label | Exact group name and layout. |
| <span id="menu-selector-cmenu-selectors-menu-radio-group"></span>`[data-citry-ui-part="menu-radio-group"]` | Radio-group root | Exclusive choice grouping. |
| <span id="menu-selector-cmenu-selectors-menu-separator"></span>`[data-citry-ui-part="menu-separator"]` | Horizontal separator | Collection division. |
| <span id="menu-selector-cmenu-selectors-menu-submenu"></span>`[data-citry-ui-part="menu-submenu"]` | Neutral submenu wrapper | Trigger/surface ownership and inherited customization. |
| <span id="menu-selector-cmenu-selectors-menu-submenu-trigger"></span>`[data-citry-ui-part="menu-submenu-trigger"]` | Submenu Button | Child Menu activation and placement anchor. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="menu-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="menu-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="menu-interface-placement"></span>`CMenuPlacement` | `Literal["top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end"]` |
| <span id="menu-interface-size"></span>`CMenuSize` | `Literal["sm", "md", "lg"]` |
| <span id="menu-interface-intent"></span>`CMenuIntent` | `Literal["default", "danger"]` |
| <span id="menu-interface-checked"></span>`CMenuChecked` | `bool | Literal["mixed"]` |

</div>

<span id="menu-interface-cmenu-activator-slot-data"></span>

#### `CMenuActivatorSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="menu-interface-cmenu-activator-slot-data-activator-attrs"></span>`activator_attrs` | `dict[str, object]` | - | Owned trigger marker, anchor identity, and synchronized ARIA relationships. |
| <span id="menu-interface-cmenu-activator-slot-data-activator-disabled"></span>`activator_disabled` | `bool` | - | Server-owned disabled value to forward through the activator component input. |

</div>

<span id="menu-interface-cmenu-default-slot-data"></span>

#### `CMenuDefaultSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-item-start-slot-data"></span>

#### `CMenuItemStartSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-item-default-slot-data"></span>

#### `CMenuItemDefaultSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-item-description-slot-data"></span>

#### `CMenuItemDescriptionSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-item-end-slot-data"></span>

#### `CMenuItemEndSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-group-label-slot-data"></span>

#### `CMenuGroupLabelSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-group-default-slot-data"></span>

#### `CMenuGroupDefaultSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-radio-group-label-slot-data"></span>

#### `CMenuRadioGroupLabelSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-radio-group-default-slot-data"></span>

#### `CMenuRadioGroupDefaultSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-submenu-start-slot-data"></span>

#### `CMenuSubmenuStartSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-submenu-label-slot-data"></span>

#### `CMenuSubmenuLabelSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-submenu-description-slot-data"></span>

#### `CMenuSubmenuDescriptionSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-submenu-end-slot-data"></span>

#### `CMenuSubmenuEndSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-submenu-default-slot-data"></span>

#### `CMenuSubmenuDefaultSlotData`

Empty dataclass: `{}`.

<span id="menu-interface-cmenu-open-change-detail"></span>

#### `CMenuOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="menu-interface-cmenu-open-change-detail-reason"></span>`reason` | `"trigger" | "escape" | "outside" | "focus-outside" | "tab" | "action" | "native" | "disabled" | "ancestor"` | - | Cause of the requested or forced visibility change. |
| <span id="menu-interface-cmenu-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client Boolean owns desired state. |
| <span id="menu-interface-cmenu-open-change-detail-forced"></span>`forced` | `boolean` | - | Whether native/structural safety overrides owner rejection. |
| <span id="menu-interface-cmenu-open-change-detail-source"></span>`source` | `Element | EventTarget | null` | - | Browser source associated with the change. |

</div>

<span id="menu-interface-cmenu-action-detail"></span>

#### `CMenuActionDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="menu-interface-cmenu-action-detail-kind"></span>`kind` | `"command" | "checkbox" | "radio"` | - | Activated semantic item kind. |
| <span id="menu-interface-cmenu-action-detail-item"></span>`item` | `Element` | - | Activated item root. |
| <span id="menu-interface-cmenu-action-detail-event"></span>`event` | `Event` | - | Native activation event. |
| <span id="menu-interface-cmenu-action-detail-path"></span>`path` | `list[str]` | - | Canonical ancestor-submenu path from the root. |

</div>

<span id="menu-interface-cmenu-checked-change-detail"></span>

#### `CMenuCheckedChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="menu-interface-cmenu-checked-change-detail-checked"></span>`checked` | `boolean` | - | Requested checked value; activation moves mixed to true and otherwise negates the prior state. |
| <span id="menu-interface-cmenu-checked-change-detail-previous-checked"></span>`previousChecked` | `boolean | "mixed"` ([`CMenuChecked`](#menu-interface-checked)) | - | Prior effective value. |
| <span id="menu-interface-cmenu-checked-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client value owns state. |
| <span id="menu-interface-cmenu-checked-change-detail-item"></span>`item` | `Element` | - | Activated checkbox item. |
| <span id="menu-interface-cmenu-checked-change-detail-event"></span>`event` | `Event` | - | Native activation event. |
| <span id="menu-interface-cmenu-checked-change-detail-path"></span>`path` | `list[str]` | - | Canonical ancestor-submenu path. |

</div>

<span id="menu-interface-cmenu-radio-change-detail"></span>

#### `CMenuRadioChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="menu-interface-cmenu-radio-change-detail-value"></span>`value` | `string` | - | Requested radio value. |
| <span id="menu-interface-cmenu-radio-change-detail-previous-value"></span>`previousValue` | `string` | - | Prior selected value. |
| <span id="menu-interface-cmenu-radio-change-detail-reason"></span>`reason` | `"activation" | "removal"` | - | Request source. |
| <span id="menu-interface-cmenu-radio-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client value owns state. |
| <span id="menu-interface-cmenu-radio-change-detail-item"></span>`item` | `Element | null` | - | Activated item or null for structural removal. |
| <span id="menu-interface-cmenu-radio-change-detail-event"></span>`event` | `Event | null` | - | Native activation event or null for removal. |
| <span id="menu-interface-cmenu-radio-change-detail-path"></span>`path` | `list[str]` | - | Canonical ancestor-submenu path. |

</div>

### Translation keys

-