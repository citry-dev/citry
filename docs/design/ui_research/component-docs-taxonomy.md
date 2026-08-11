# Citry UI documentation taxonomy research

Status: applied to the docs catalog on 2026-08-10.

## Question

How should a growing component library group components so readers can find a
family by its job without turning the catalog into one long alphabetical list?

## Current library patterns

### Material UI

Source: <https://mui.com/material-ui/all-components/>, reviewed 2026-08-10.

Material UI uses a small task-oriented vocabulary: Inputs, Data display,
Feedback, Surface, Navigation, and Layout. It keeps framework utilities outside
the ordinary component groups. This is the clearest baseline for a catalog of
Citry UI's current size.

### PrimeVue

Source: <https://primevue.dev/components/>, reviewed 2026-08-10.

PrimeVue uses Form, Button, Data, Panel, Overlay, File, Menu, Messages, Media,
and Misc. Its useful contribution is separating overlays and menus from data
components. Its large Misc group is less useful as a destination and should not
be copied.

### Chakra UI

Source: <https://chakra-ui.com/docs/components/concepts/overview>, reviewed
2026-08-10.

Chakra's current overview is a searchable alphabetical catalog rather than a
small category tree. It works with strong search, but does not solve Citry UI's
sidebar length by itself. Chakra's component descriptions still reinforce the
same functional distinctions among layout, input, overlay, feedback, and data
display jobs.

### React Aria

Source: <https://react-aria.adobe.com/>, reviewed 2026-08-10.

React Aria emphasizes composition and application behavior more than a compact
sidebar taxonomy. Its model supports keeping composite widgets such as Tree and
Table with data-oriented components instead of classifying everything by DOM
shape.

## Decision

Citry UI uses seven functional groups:

1. Actions
2. Forms and inputs
3. Layout
4. Data display
5. Navigation
6. Feedback and status
7. Overlays and disclosure

This starts from Material UI's compact vocabulary, adds PrimeVue's useful
overlay distinction, and keeps Actions separate because Citry UI has several
families for persistent command controls. Tree belongs in Data display because
it presents and operates on hierarchical application data. Accordion belongs in
Overlays and disclosure because its primary job is controlled disclosure rather
than page navigation.

The grouping is metadata, not route structure. Existing component URLs remain
`/ui-library/components/<slug>/`. One catalog drives the sidebar, breadcrumbs,
overview sections, source ownership, and preview discovery. A component has one
primary group so navigation remains predictable; cross-links in guides can
serve secondary discovery jobs.

## Rejected directions

- One alphabetical group does not scale to the current catalog.
- A group for every visual shape creates too many tiny sections and makes
  semantics harder to predict.
- A general Misc group becomes a permanent dumping ground.
- Duplicating one component under several sidebar groups makes previous/next
  navigation and breadcrumbs ambiguous.
