# Citry UI theme and color-scheme contract

**Status (2026-07-30): Phase 7 working contract.** This document fixes theme
ownership and acceptance requirements while leaving the final theme-provider
API and global token inventory open until several production families and the
Overlay slice provide enough evidence.

## 1. Vocabulary

- A **theme** is a coherent brand and design-token mapping: semantic colors,
  typography, spacing, radii, elevation, and motion.
- A **color scheme** is `light`, `dark`, or the user's system preference.
- A **component variant** changes a component's presentation, such as pill,
  underline, filled, or outlined.
- An **intent** communicates meaning such as neutral, accent, positive,
  warning, or negative.

These are separate public concepts. A dark color scheme is not a component
variant, and an accent intent is not a brand theme.

## 2. Ownership

Citry UI owns:

- usable and accessible default styling in light and dark schemes;
- semantic component colors that do not assume a white or black page;
- contrast, focus, disabled, selected, invalid, and loading differentiation in
  both schemes;
- reduced-motion and forced-colors behavior;
- nested color-scheme behavior; and
- preserving the originating theme and color scheme when a library-owned
  overlay renders outside its source DOM subtree.

The application owns:

- choosing light, dark, or system behavior;
- storing and restoring a user's explicit preference;
- applying brand token overrides;
- styling the surrounding application page; and
- any early document script or server cookie needed to prevent a flash when
  an explicit stored preference differs from the system preference.

An application must not need component-specific fixes merely to make the
official dark scheme readable or operable.

## 3. Phase 7 behavior

Every production component must pass its state and interaction matrix in light
and dark. Components use CSS inheritance, semantic system colors, and public
variables so a `color-scheme` set on an ancestor affects the component. The
component must not force one scheme locally unless that behavior is an
explicit public input.

The exact selector or provider used to select a named scheme is not frozen in
this increment. Ordinary CSS `color-scheme` and documented variables are the
current integration surface. Before release, the production slices must prove:

1. a system-preference default without requiring component JavaScript;
2. explicit light and dark scopes, including nested opposite schemes;
3. native controls and scrollbars receiving the effective `color-scheme`;
4. no cross-instance leakage between differently themed scopes;
5. theme continuity through Citry slots, morphs, and fragments; and
6. overlay continuity when physical DOM placement differs from Citry
   ownership.

The Overlay slice decides whether CSS inheritance plus copied scope markers is
sufficient or whether a public server and client ambient-context value is also
required. Citry's `provide`, `inject`, and `unprovide` APIs are available, but
the theme contract does not require a runtime provider before that need is
proven.

## 4. Customization tiers

Citry UI's styling order is:

1. library-wide semantic tokens once multiple families establish their roles;
2. component inputs such as variant, density, size, and intent;
3. documented component `--cui-*` variables;
4. documented `data-citry-ui-part` and public state selectors; and
5. consumer-owned markup through supported slots.

Public component variables are inherited inputs. A component resolves their
fallbacks through private effective variables and does not assign public
defaults on its root. Default rules live in the `citry-ui.theme` cascade layer
with low specificity.

The global semantic token set grows from repeated roles demonstrated by
production components and two distinct brand adaptations. Similar literal
values in one component are not sufficient evidence for a global token.

## 5. Compatibility

Public token and component-variable names, value types, meanings, inheritance,
and fallback precedence are stable API. Public part names and documented state
attributes are stable selectors.

Exact default colors, spacing, shadows, and motion belong to the evolvable
default theme. They may improve without a major release while preserving the
documented semantic role, accessibility floor, component dimensions promised
by behavior-affecting inputs, and override contract. User-visible theme changes
belong in release notes.

Private effective variables, implementation classes, and incidental markup
are not customization API.

## 6. Acceptance evidence

Each component provides browser-computed evidence for:

- system, explicit light, and explicit dark behavior;
- an opposite nested scheme;
- ancestor and component-root variable overrides;
- public part and state selectors;
- every supported variant, density, size, and intent in both schemes;
- forced colors, reduced motion, RTL, zoom, and long content; and
- two brand adaptations using only documented public surfaces.

The library-wide scenarios add complete-page screenshots, axe checks,
Lighthouse, CSS coexistence, server-render flash checks, and overlay or portal
continuity. Visual review remains required because computed values and
automated contrast checks do not prove coherent hierarchy or interaction
feedback.

## 7. Deferred theme API

After several production families and Overlay are implemented, revisit:

- the public theme or color-scheme scope component, if one is needed;
- named themes and application-wide component defaults;
- client-side selection and reactive updates;
- overlay-host propagation;
- token serialization and Python configuration;
- icon, typography, breakpoint, elevation, and motion configuration; and
- a no-flash server and browser initialization helper.

That work may extend this contract, but it must preserve the ownership and
acceptance requirements above.
