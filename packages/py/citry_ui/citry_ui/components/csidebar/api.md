---
title: Sidebar
description: Build persistent, rail, and collapsible application sidebars with Citry UI.
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

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csidebar/snippets/at_a_glance.py" title="Sidebar at a glance" />

## Compose navigation from List

Sidebar does not invent a second navigation-item API. Compose `CList` for
links, `CDisclosure` for expandable sections, and `CMenu` for command popovers.
When rail-collapsed, List text stays visually clipped but remains the accessible
name of each link.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csidebar/snippets/navigation.py" title="Compose Sidebar navigation" />

## Choose a collapse mode

`collapsible="rail"` keeps an icon-width navigation rail. `offcanvas` hides
the panel while retaining the native toggle. `none` renders a permanent region
and rejects `collapsed=True`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csidebar/snippets/collapse_modes.py" title="Compare Sidebar collapse modes" />

## Control collapse state

Supply `collapsed` through `$c-props` to control it. The callback is a request;
keep or change your value to reject or accept it.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csidebar/snippets/controlled.py" title="Control Sidebar collapse" />

## Build sticky and floating Sidebars

Sticky Sidebars use `--cui-sidebar-sticky-offset` to leave room for an
application header. `variant="floating"` adds a contained border, radius, and
elevation without registering page-layout insets. Sticky positioning applies
an offset and a viewport-sized maximum; it does not force a fixed height, so a
preview iframe cannot enter a self-expanding height loop.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csidebar/snippets/presentation.py" title="Choose Sidebar presentation" />

## Customize Sidebar

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csidebar/snippets/customization.py" title="Customize Sidebar" />

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
