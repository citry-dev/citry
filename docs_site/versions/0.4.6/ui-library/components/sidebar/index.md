---
title: Sidebar
url: https://citry.dev/v/0.4.6/ui-library/components/sidebar/
description: "Build persistent, rail, and collapsible application sidebars with Citry UI."
---
# Sidebar

Use `CSidebar` for persistent application navigation or complementary tools.
It gives header and footer content fixed positions around one scrollable region
and supports rail or off-canvas collapse.

When a header is present, it shares the first Row with the collapse toggle.
Only the rail width transition clips horizontal overflow while the fixed-width
inner panel moves behind it, so labels do not flash as one-character columns.
At rest, the collapsed panel uses the actual rail width, preserving complete
icon boxes instead of clipping expanded boxes at the rail edge. Arbitrary slot
text stays on one clipped line in the steady rail instead of wrapping into a
tall one-character column; mark content with
`data-citry-sidebar-expanded-only` when it should disappear entirely.

## Sidebar at a glance


### Sidebar at a glance

[Open the rendered preview](/v/0.4.6/ui-library/components/sidebar/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarAtAGlance(Component):
    template = """
      <div class="sidebar-layout">
        <c-CSidebar id="workspace" tag="nav" label="Workspace navigation">
          <c-fill name="header"><strong>Northstar</strong></c-fill>
          <c-fill name="default">
            <c-CList variant="surface">
              <c-CListItem href="#overview" c-current="True">
                <c-fill name="start"><c-CIcon name="home" /></c-fill>
                <c-fill name="default">Overview</c-fill>
              </c-CListItem>
              <c-CListItem href="#projects">
                <c-fill name="start"><c-CIcon name="folder" /></c-fill>
                <c-fill name="default">Projects</c-fill>
              </c-CListItem>
              <c-CListItem href="#reports">
                <c-fill name="start"><c-CIcon name="file" /></c-fill>
                <c-fill name="default">Reports</c-fill>
              </c-CListItem>
            </c-CList>
          </c-fill>
          <c-fill name="footer"><small>ada@example.com</small></c-fill>
        </c-CSidebar>
        <main><h2 id="overview">Overview</h2><p>The primary page remains ordinary application layout.</p></main>
      </div>
    """
    css = """
      :where(.sidebar-layout) {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        gap: 1.5rem;
        min-block-size: 24rem;
      }
      :where(.sidebar-layout main) { padding: 1rem; }
    """


preview = SidebarAtAGlance()
preview  # noqa: B018
````


## Compose navigation from List

Sidebar does not invent a second navigation-item API. Compose `CList` for
links, `CDisclosure` for expandable sections, and `CMenu` for command popovers.
When rail-collapsed, List text stays visually clipped but remains the accessible
name of each link.


### Compose Sidebar navigation

[Open the rendered preview](/v/0.4.6/ui-library/components/sidebar/_previews/navigation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarNavigation(Component):
    template = """
      <c-CSidebar tag="nav" label="Project navigation" c-collapsed="True">
        <c-fill name="header"><span data-citry-sidebar-expanded-only><strong>Atlas</strong></span></c-fill>
        <c-fill name="default">
          <c-CList>
            <c-CListItem href="#activity" c-current="True">
              <c-fill name="start"><c-CIcon name="clock" /></c-fill>
              <c-fill name="default">Activity</c-fill>
            </c-CListItem>
            <c-CListItem href="#members">
              <c-fill name="start"><c-CIcon name="user" /></c-fill>
              <c-fill name="default">Members</c-fill>
            </c-CListItem>
            <c-CListItem href="#settings">
              <c-fill name="start"><c-CIcon name="settings" /></c-fill>
              <c-fill name="default">Settings</c-fill>
            </c-CListItem>
          </c-CList>
        </c-fill>
      </c-CSidebar>
    """


preview = SidebarNavigation()
preview  # noqa: B018
````


## Choose a collapse mode

`collapsible="rail"` keeps an icon-width navigation rail. `offcanvas` hides
the panel while retaining the native toggle. `none` renders a permanent region
and rejects `collapsed=True`.


### Compare Sidebar collapse modes

[Open the rendered preview](/v/0.4.6/ui-library/components/sidebar/_previews/collapse-modes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarCollapseModes(Component):
    template = """
      <div class="sidebar-modes">
        <c-CSidebar label="Rail example" c-collapsed="True" collapsible="rail" size="sm">
          <strong>Rail content remains available.</strong>
        </c-CSidebar>
        <c-CSidebar label="Offcanvas example" c-collapsed="True" collapsible="offcanvas" size="sm">
          <strong>The panel starts hidden.</strong>
        </c-CSidebar>
        <c-CSidebar label="Permanent example" collapsible="none" size="sm">
          <strong>No toggle is rendered.</strong>
        </c-CSidebar>
      </div>
    """
    css = ":where(.sidebar-modes){display:flex;align-items:flex-start;gap:1rem;min-block-size:14rem}"


preview = SidebarCollapseModes()
preview  # noqa: B018
````


## Control collapse state

Supply `collapsed` through `$c-props` to control it. The callback is a request;
keep or change your value to reject or accept it.


### Control Sidebar collapse

[Open the rendered preview](/v/0.4.6/ui-library/components/sidebar/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarControlled(Component):
    template = """
      <section x-data="{
        collapsed:false,
        last:'No request yet',
        change(next){this.last=`Requested ${next ? 'collapse' : 'expand'}`;this.collapsed=next},
      }">
        <p><output x-text="last">No request yet</output></p>
        <c-CSidebar
          label="Controlled navigation"
          $c-props="{collapsed,onCollapsedChange:change}"
        >
          <strong>Controlled Sidebar content</strong>
        </c-CSidebar>
      </section>
    """


preview = SidebarControlled()
preview  # noqa: B018
````


## Build sticky and floating Sidebars

Sticky Sidebars use `--cui-sidebar-sticky-offset` to leave room for an
application header. `variant="floating"` adds a contained border, radius, and
elevation without registering page-layout insets. Sticky positioning applies
an offset and a viewport-sized maximum; it does not force a fixed height, so a
preview iframe cannot enter a self-expanding height loop.


### Choose Sidebar presentation

[Open the rendered preview](/v/0.4.6/ui-library/components/sidebar/_previews/presentation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarPresentation(Component):
    template = """
      <c-CSidebar
        label="Sticky tools"
        variant="floating"
        size="lg"
        c-sticky="True"
        c-style="{'--cui-sidebar-sticky-offset':'1rem'}"
      >
        <c-fill name="header"><strong>Inspector</strong></c-fill>
        <c-fill name="default">
          <p>Long tool content scrolls independently between fixed regions.</p>
          <p>Keep adding contextual controls here.</p>
        </c-fill>
        <c-fill name="footer"><c-CButton size="sm">Apply</c-CButton></c-fill>
      </c-CSidebar>
    """


preview = SidebarPresentation()
preview  # noqa: B018
````


## Customize Sidebar


### Customize Sidebar

[Open the rendered preview](/v/0.4.6/ui-library/components/sidebar/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarCustomization(Component):
    template = """
      <c-CSidebar label="Custom navigation" variant="floating" side="inline-end" c-class_="['ocean-sidebar']">
        <c-fill name="toggle"><c-CIcon name="menu" /></c-fill>
        <c-fill name="header"><strong>Ocean lab</strong></c-fill>
        <c-fill name="default"><p>Public variables and parts customize the stable landmark.</p></c-fill>
      </c-CSidebar>
    """
    css = """
      :where(.ocean-sidebar) {
        --cui-sidebar-background: light-dark(#eff8ff, #102a43);
        --cui-sidebar-border-color: light-dark(#84caff, #2e90fa);
        --cui-sidebar-width: 18rem;
      }
    """


preview = SidebarCustomization()
preview  # noqa: B018
````


## Persistent Sidebar or mobile Drawer?

Sidebar remains in document layout and never traps focus, adds a scrim, or
locks page scrolling. For modal mobile navigation, render the same application
navigation component inside `CDrawer placement="inline-start"`. A future
AppShell can choose the responsive policy without changing either component.

## Accessibility and localization

Choose `tag="nav"` when the content is navigation and `aside` for complementary
tools. `label` is required. The native toggle owns `aria-controls` and
`aria-expanded`; Enter and Space work without a custom keyboard model. If an
off-canvas collapse would hide current focus, focus moves to the toggle first.

The Expand and Collapse labels are Citry UI catalog messages. Override them
with `expand_label` and `collapse_label`; overrides stay fixed while catalog
defaults react to a client locale switch.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CSidebar server inputs

Server inputs are passed in a template through `<c-CSidebar ... />` or in Python through
`CSidebar(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="sidebar-input-csidebar-server-inputs-id"></span>`id` | `str | None` | generated | Sets the landmark ID and bases the controlled panel ID. |
| <span id="sidebar-input-csidebar-server-inputs-label"></span>`label` | `str` | required | Names the complementary or navigation landmark. |
| <span id="sidebar-input-csidebar-server-inputs-tag"></span>`tag` | `CSidebarTag` ([`CSidebarTag`](#sidebar-interface-tag)) | `"aside"` | Selects complementary aside or navigation nav semantics. |
| <span id="sidebar-input-csidebar-server-inputs-collapsed"></span>`collapsed` | `bool` | `False` | Sets initial expanded or collapsed state. |
| <span id="sidebar-input-csidebar-server-inputs-collapsible"></span>`collapsible` | `CSidebarCollapsible` ([`CSidebarCollapsible`](#sidebar-interface-collapsible)) | `"rail"` | Selects rail offcanvas or permanent behavior. |
| <span id="sidebar-input-csidebar-server-inputs-side"></span>`side` | `CSidebarSide` ([`CSidebarSide`](#sidebar-interface-side)) | `"inline-start"` | Selects the logical page edge and border/toggle placement. |
| <span id="sidebar-input-csidebar-server-inputs-variant"></span>`variant` | `CSidebarVariant` ([`CSidebarVariant`](#sidebar-interface-variant)) | `"plain"` | Selects flush or floating surface treatment. |
| <span id="sidebar-input-csidebar-server-inputs-size"></span>`size` | `CSidebarSize` ([`CSidebarSize`](#sidebar-interface-size)) | `"md"` | Selects the default expanded width. |
| <span id="sidebar-input-csidebar-server-inputs-sticky"></span>`sticky` | `bool` | `False` | Sticks the Sidebar at the public block offset within its scroll container. |
| <span id="sidebar-input-csidebar-server-inputs-expand-label"></span>`expand_label` | `str` | `"Expand sidebar"` | Overrides the localized expanded-state action name. |
| <span id="sidebar-input-csidebar-server-inputs-collapse-label"></span>`collapse_label` | `str` | `"Collapse sidebar"` | Overrides the localized collapsed-state action name. |
| <span id="sidebar-input-csidebar-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#sidebar-interface-class-value)) | `None` | Adds classes to the native landmark. |
| <span id="sidebar-input-csidebar-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#sidebar-interface-style-value)) | `None` | Adds styles to the native landmark. |
| <span id="sidebar-input-csidebar-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed landmark attributes without replacing owned semantics state or identity. |

</div>

#### CSidebar client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CSidebar />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="sidebar-input-csidebar-client-inputs-collapsed"></span>`collapsed` | `boolean | null` | Releases control to the committed value. | Controls expanded or collapsed state. |
| <span id="sidebar-input-csidebar-client-inputs-collapsible"></span>`collapsible` | `CSidebarCollapsible` ([`CSidebarCollapsible`](#sidebar-interface-collapsible)) | Uses the server value. | Controls rail offcanvas or permanent behavior. |
| <span id="sidebar-input-csidebar-client-inputs-side"></span>`side` | `CSidebarSide` ([`CSidebarSide`](#sidebar-interface-side)) | Uses the server value. | Controls logical placement. |
| <span id="sidebar-input-csidebar-client-inputs-variant"></span>`variant` | `CSidebarVariant` ([`CSidebarVariant`](#sidebar-interface-variant)) | Uses the server value. | Controls surface treatment. |
| <span id="sidebar-input-csidebar-client-inputs-size"></span>`size` | `CSidebarSize` ([`CSidebarSize`](#sidebar-interface-size)) | Uses the server value. | Controls width profile. |
| <span id="sidebar-input-csidebar-client-inputs-sticky"></span>`sticky` | `boolean` | Uses the server value. | Controls sticky positioning. |
| <span id="sidebar-input-csidebar-client-inputs-on-collapsed-change"></span>`onCollapsedChange` | `function` | No semantic collapse callback. | Receives native toggle requests. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CSidebar slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="sidebar-slot-csidebar-slots-default"></span>`default` | yes | `{}` ([`CSidebarDefaultSlotData`](#sidebar-interface-csidebar-default-slot-data)) | None. |
| <span id="sidebar-slot-csidebar-slots-header"></span>`header` | no | `{}` ([`CSidebarHeaderSlotData`](#sidebar-interface-csidebar-header-slot-data)) | Omitted. |
| <span id="sidebar-slot-csidebar-slots-footer"></span>`footer` | no | `{}` ([`CSidebarFooterSlotData`](#sidebar-interface-csidebar-footer-slot-data)) | Omitted. |
| <span id="sidebar-slot-csidebar-slots-toggle"></span>`toggle` | no | `{collapsed}` ([`CSidebarToggleSlotData`](#sidebar-interface-csidebar-toggle-slot-data)) | Decorative neutral panel glyph. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CSidebar events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="sidebar-event-csidebar-events-on-collapsed-change"></span>`onCollapsedChange` | `(collapsed: boolean, detail: CSidebarCollapsedChangeDetail) => void` ([`CSidebarCollapsedChangeDetail`](#sidebar-interface-csidebar-collapsed-change-detail)) | Native toggle activation requests a different state. | `{collapsed, previousCollapsed, controlled, source, sourceEvent}` ([`CSidebarCollapsedChangeDetail`](#sidebar-interface-csidebar-collapsed-change-detail)) | Uncontrolled state commits before notification; controlled state is request-only. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CSidebar CSS variables

Apply these variables to `CSidebar` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="sidebar-css-csidebar-css-variables-width"></span>`--cui-sidebar-width` | `length` | Expanded inline size overriding the selected profile. | `sm 14rem; md 16rem; lg 20rem` |
| <span id="sidebar-css-csidebar-css-variables-rail-width"></span>`--cui-sidebar-rail-width` | `length` | Collapsed rail inline size. | `4rem` |
| <span id="sidebar-css-csidebar-css-variables-background"></span>`--cui-sidebar-background` | `color` | Landmark and toggle surface. | `Adaptive neutral` |
| <span id="sidebar-css-csidebar-css-variables-foreground"></span>`--cui-sidebar-foreground` | `color` | Sidebar text and icon color. | `CanvasText` |
| <span id="sidebar-css-csidebar-css-variables-border-color"></span>`--cui-sidebar-border-color` | `color` | Logical edge and floating border. | `Adaptive neutral` |
| <span id="sidebar-css-csidebar-css-variables-shadow"></span>`--cui-sidebar-shadow` | `shadow` | Floating surface elevation. | `Soft elevation` |
| <span id="sidebar-css-csidebar-css-variables-radius"></span>`--cui-sidebar-radius` | `length` | Floating surface and toggle corner input. | `0.85rem` |
| <span id="sidebar-css-csidebar-css-variables-padding"></span>`--cui-sidebar-padding` | `length` | Internal panel spacing. | `0.75rem` |
| <span id="sidebar-css-csidebar-css-variables-gap"></span>`--cui-sidebar-gap` | `length` | Header content footer and offcanvas-trigger spacing. | `0.75rem` |
| <span id="sidebar-css-csidebar-css-variables-toggle-size"></span>`--cui-sidebar-toggle-size` | `length` | Native toggle target size. | `2.75rem` |
| <span id="sidebar-css-csidebar-css-variables-focus-color"></span>`--cui-sidebar-focus-color` | `color` | Toggle focus outline. | `Highlight` |
| <span id="sidebar-css-csidebar-css-variables-sticky-offset"></span>`--cui-sidebar-sticky-offset` | `length` | Block offset reserved above a sticky Sidebar. | `0px` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CSidebar attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="sidebar-attribute-csidebar-attributes-aria-label"></span>`aria-label` | Root landmark | `string` | Names the complementary or navigation region. |
| <span id="sidebar-attribute-csidebar-attributes-data-collapsed"></span>`data-collapsed` | Root landmark | `present | absent` | Marks effective collapsed state. |
| <span id="sidebar-attribute-csidebar-attributes-data-collapsible"></span>`data-collapsible` | Root landmark | `CSidebarCollapsible` ([`CSidebarCollapsible`](#sidebar-interface-collapsible)) | Mirrors collapse behavior. |
| <span id="sidebar-attribute-csidebar-attributes-data-side"></span>`data-side` | Root landmark | `CSidebarSide` ([`CSidebarSide`](#sidebar-interface-side)) | Mirrors logical placement. |
| <span id="sidebar-attribute-csidebar-attributes-data-variant"></span>`data-variant` | Root landmark | `CSidebarVariant` ([`CSidebarVariant`](#sidebar-interface-variant)) | Mirrors surface treatment. |
| <span id="sidebar-attribute-csidebar-attributes-data-size"></span>`data-size` | Root landmark | `CSidebarSize` ([`CSidebarSize`](#sidebar-interface-size)) | Mirrors width profile. |
| <span id="sidebar-attribute-csidebar-attributes-data-sticky"></span>`data-sticky` | Root landmark | `present | absent` | Marks sticky positioning. |
| <span id="sidebar-attribute-csidebar-attributes-data-has-header"></span>`data-has-header` | Root landmark | `present | absent` | Marks header anatomy so the header and toggle share the first Row. |
| <span id="sidebar-attribute-csidebar-attributes-aria-controls"></span>`aria-controls` | Toggle Button | `IDREF` | Refers to the owned panel. |
| <span id="sidebar-attribute-csidebar-attributes-aria-expanded"></span>`aria-expanded` | Toggle Button | `boolean-string` | Reflects expanded state. |
| <span id="sidebar-attribute-csidebar-attributes-data-citry-sidebar-expanded-only"></span>`data-citry-sidebar-expanded-only` | Authored descendant | `present | absent` | Hides authored content in rail mode. |
| <span id="sidebar-attribute-csidebar-attributes-data-citry-sidebar-rail-only"></span>`data-citry-sidebar-rail-only` | Authored descendant | `present | absent` | Shows authored accessible replacement only in rail mode. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CSidebar selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="sidebar-selector-csidebar-selectors-sidebar"></span>`[data-citry-ui-part="sidebar"]` | Native aside or nav root | State reflections and customization destination. |
| <span id="sidebar-selector-csidebar-selectors-toggle"></span>`[data-citry-ui-part="toggle"]` | Native Button | Collapse control. |
| <span id="sidebar-selector-csidebar-selectors-toggle-icon"></span>`[data-citry-ui-part="toggle-icon"]` | Decorative span | Custom or fallback visual. |
| <span id="sidebar-selector-csidebar-selectors-toggle-label"></span>`[data-citry-ui-part="toggle-label"]` | Visually hidden span | Localized state-dependent accessible name. |
| <span id="sidebar-selector-csidebar-selectors-panel"></span>`[data-citry-ui-part="panel"]` | Owned div | Full-width clipped transition and fixed/scroll region owner. |
| <span id="sidebar-selector-csidebar-selectors-header"></span>`[data-citry-ui-part="header"]` | Optional header | Fixed branding and controls. |
| <span id="sidebar-selector-csidebar-selectors-content"></span>`[data-citry-ui-part="content"]` | Scrollable div | Primary authored Sidebar content. |
| <span id="sidebar-selector-csidebar-selectors-footer"></span>`[data-citry-ui-part="footer"]` | Optional footer | Fixed account status or actions. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="sidebar-interface-tag"></span>`CSidebarTag` | `Literal["aside", "nav"]` |
| <span id="sidebar-interface-collapsible"></span>`CSidebarCollapsible` | `Literal["rail", "offcanvas", "none"]` |
| <span id="sidebar-interface-side"></span>`CSidebarSide` | `Literal["inline-start", "inline-end"]` |
| <span id="sidebar-interface-variant"></span>`CSidebarVariant` | `Literal["plain", "floating"]` |
| <span id="sidebar-interface-size"></span>`CSidebarSize` | `Literal["sm", "md", "lg"]` |
| <span id="sidebar-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="sidebar-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="sidebar-interface-csidebar-default-slot-data"></span>

#### `CSidebarDefaultSlotData`

Empty dataclass: `{}`.

<span id="sidebar-interface-csidebar-header-slot-data"></span>

#### `CSidebarHeaderSlotData`

Empty dataclass: `{}`.

<span id="sidebar-interface-csidebar-footer-slot-data"></span>

#### `CSidebarFooterSlotData`

Empty dataclass: `{}`.

<span id="sidebar-interface-csidebar-toggle-slot-data"></span>

#### `CSidebarToggleSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="sidebar-interface-csidebar-toggle-slot-data-collapsed"></span>`collapsed` | `bool` | - | Server-rendered initial collapsed state. |

</div>

<span id="sidebar-interface-csidebar-collapsed-change-detail"></span>

#### `CSidebarCollapsedChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="sidebar-interface-csidebar-collapsed-change-detail-collapsed"></span>`collapsed` | `bool` | - | Requested collapsed state. |
| <span id="sidebar-interface-csidebar-collapsed-change-detail-previous-collapsed"></span>`previousCollapsed` | `bool` | - | Effective state before the request. |
| <span id="sidebar-interface-csidebar-collapsed-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client state currently controls collapse. |
| <span id="sidebar-interface-csidebar-collapsed-change-detail-source"></span>`source` | `activation` | - | Native toggle activation source. |
| <span id="sidebar-interface-csidebar-collapsed-change-detail-source-event"></span>`sourceEvent` | `Event` | - | Native click event. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CSidebar translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="sidebar-translation-csidebar-translations-expand"></span>`citry-ui-sidebar-expand` | Names the action that expands a collapsed Sidebar. | `None.` | `expand_label` | Stable `$c-tr` text binding follows client locale changes. |
| <span id="sidebar-translation-csidebar-translations-collapse"></span>`citry-ui-sidebar-collapse` | Names the action that collapses an expanded Sidebar. | `None.` | `collapse_label` | Stable `$c-tr` text binding follows client locale changes. |

</div>