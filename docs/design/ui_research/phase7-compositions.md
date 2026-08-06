# Phase 7 representative Citry UI compositions

**Status (2026-07-30): accepted composition and brand fixture.** These pages
test the production slice as a small product, not as disconnected component
demos. They are acceptance fixtures and possible future docs examples, not
new public components.

## 1. Required compositions

### Public-site access form

The first composition is a light-scheme product access form with name, work
email, and plan fields plus a primary submit action. It uses `CForm`, `CField`,
`CInput`, `CCombobox`, and `CButton`. The copy, labels, native autocomplete,
required constraints, canonical plan value, and narrow viewport behavior are
part of the fixture.

### Application dashboard

The second composition is a dark-scheme project dashboard with `CTabs`, a
semantic `CTable`, action Buttons, and a `CDialog` for creating a report. It
proves compound navigation, dense data, overlay theme continuity, and
cross-family visual consistency in one realistic application surface.

The base markup adds no application stylesheet. Component defaults must
therefore produce legible, usable controls and relationships on their own.
Normal browser flow between sections is acceptable because a future layout
primitive is outside this Phase 7 slice.

## 2. Brand adaptations

The `Orbit` and `Ledger` brands deliberately differ in palette, radius,
density, and emphasis. Their CSS may use only:

- a consumer-owned scope class;
- the inherited `color-scheme` property;
- the scope's ordinary background and foreground using system colors;
- documented component `--cui-*` variables; and
- documented `[data-citry-ui-part="..."]` selectors.

The adaptations must contain no package class selector, private data marker,
private `--_cui-*` variable, internal DOM query, or `!important`. The fixture
asserts both the authored CSS restrictions and representative computed styles.
This does not freeze every chosen color value. It freezes that ordinary
branding is possible through the public customization contract.

## 3. Interaction and environment checks

Direct browser evidence covers:

1. both branded scopes render with their selected light or dark scheme;
2. the same Button family resolves distinct inherited brand variables;
3. public part overrides reach their intended elements;
4. the public form preserves labels, required validation, keyboard access,
   canonical Combobox output, and native submission behavior;
5. dashboard Tabs switch panels and retain correct semantics;
6. the Table remains horizontally focusable at a narrow viewport;
7. the report Dialog opens into the browser top layer while retaining Ledger
   variables, initial focus, and focus restoration; and
8. no component reads public mirror attributes as imperative configuration.

Cross-browser behavior runs in Chromium, Firefox, and WebKit. Screenshot,
forced-colors, 200 and 400 percent zoom, mobile viewport, Nu HTML, Lighthouse,
and representative screen-reader tasks remain separate quality-tool and manual
profiles against the same standalone composition.

## 4. Product findings

The composition can require a future layout, typography, navigation, card, or
feedback family without turning ad hoc page CSS into Citry UI API. Such gaps
are recorded for the Phase 8 inventory. They do not justify selectors into
private component markup.

If either brand cannot reach a coherent result without a private selector or
`!important`, the affected component's token or part contract must expand
before the production surface grows. A custom provider or global token tier is
selected only after these concrete overrides show repeated inputs that should
be shared across families.
