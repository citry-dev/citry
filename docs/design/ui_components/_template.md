# Citry UI component specification template

**Status:** reusable Phase 7 template. Copy this file for each production
component family and replace every instruction before implementation begins.
Delete sections that genuinely do not apply, but record why a high-risk
surface such as forms, overlays, collections, or async behavior is absent.

Follow the staged
[`Citry UI family workflow`](../../../packages/py/citry_ui/docs/component-authoring.md#requalify-one-component-family-at-a-time).
Complete the current-source record, all applicable sections, and the public
example catalog before changing production runtime code. Existing code may
supply evidence, but it does not settle an unresolved contract.

## 1. Purpose and product bar

State the user job, supported environments, and what makes the component
production-complete. Name the closest native HTML or WAI-ARIA pattern. Define
the styled out-of-the-box promise and any explicitly excluded specialist work.

List the common application jobs before designing the API. Do not limit this
to behavior already present in a prototype. For each job, show the shortest
intended template and Python-composition expression and classify its solution
as direct component API, native HTML or attributes, CSS or utility classes,
composition, a separate component, or unsupported. Use those examples to
check that high-frequency names and structure are concise without becoming
cryptic.

List non-goals. Record whether a headless API exists. Headless APIs remain
parked unless current application evidence justifies one.

## 2. Prior art and complaints

Start with the shared ecosystem dossiers, taxonomy, and complaint register.
Audit existing local runtime, tests, scenarios, docs, and composed usage. Then
refresh the component-specific evidence from current standards, official docs,
implementation source, and material issue reports.

Compare the official documentation and current implementation of relevant
React, Vue, Web Component, native, and Python counterparts. Include at least:

- public inputs and their defaults;
- controlled and uncontrolled state;
- children, named or scoped slots, render callbacks, and replaceable parts;
- callbacks, emitted events, methods, and their payloads;
- semantic HTML, ARIA, keyboard, focus, touch, and screen-reader behavior;
- form, async, collection, overlay, and responsive behavior when applicable;
- variants, sizes, density, intent, light/dark behavior, parts, and tokens; and
- material complaints, their affected versions, current status, and available
  workarounds.

Keep a source record so a later pass can tell what was actually checked:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Replace | Replace | Replace | Replace |

Conclude with the patterns Citry UI adopts, rejects, or must prove. Similar API
names are evidence, not a reason to copy unclear semantics.

Treat current Vuetify as the primary styled-suite reference with roughly 30
percent of the product-comparison decision weight. The number expresses
priority, not score arithmetic. Standards remain acceptance baselines. Add a
Vuetify disposition table covering every relevant input, slot, event, method,
state, and documented job:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| Replace | direct API, native HTML or attributes, CSS or utility classes, composition, separate component, or omitted | Replace | Replace |

Capability parity does not require prop parity. For example, a Vuetify
dimension prop may map to ordinary `attrs` classes or styles when that remains
easy, documented, and testable.

## 3. Public composition and anatomy

Show the smallest realistic template and Python-composition examples. Diagram
compound-component nesting when ownership or ordering matters.

Document:

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CExample` | Replace | Replace | Replace |

State which attributes consumers may pass, where they land, and which owned
attributes cannot be replaced. Document valid nesting, cardinality, generated
identity, and errors for missing, duplicate, misplaced, or unknown children.

After the first complete implementation, repeat the anatomy review. Identify
components that only group declarations or forward inputs, then test whether
their inputs can move to an existing owner without losing composition,
validation, semantics, customization, or extension points. Record each removed
or retained structural component and the scenarios that justify the decision.

Do not promise incidental wrapper elements. Mark only the elements and
relationships that consumers may rely on.

## 4. Server inputs and client inputs

For every Python input, classify it as structural server-only data, an initial
value, reactive configuration, or controlled browser state.

Every styled component exposes `class_` and `style` as optional top-level
server inputs on its documented root. They accept Citry's structured
class/style values and merge with any class/style contributions retained in a
general `attrs` mapping. Compound declaration components carry the values to
the concrete element they declare.

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| Replace | Replace | Replace | Replace | Replace |

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| Replace | Replace | Replace | Replace | Replace | Replace |

Define Python-versus-client precedence, first initialization, later updates,
prop removal, server rerender, and nested-instance isolation. A public DOM
mirror is observable styling state, not a writable configuration input.

## 5. State model

Enumerate every public state and transition. Cover controlled and uncontrolled
ownership, initial state, repeated same-value requests, disabled, read-only,
loading, pending, invalid, empty, and error behavior that applies.

For each transition, specify:

- its trigger and guard conditions;
- whether it requests or commits a change;
- native DOM, ARIA, focus, form, visual, and callback effects;
- behavior while controlled, disabled, loading, or being removed; and
- recovery from invalid external state.

Use a transition table or state diagram when the component has more than a
few interacting states.

## 6. Slots and slot data

Compare ordinary children, named and scoped slots, collection renderers, and
replaceable parts in the reference libraries.

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| Replace | Replace | Replace | Replace | Replace | Replace |

For each slot, define valid nesting, visible provided context, whether slot
data can change in the browser, and errors for unsupported composition.

For an unbounded data-driven surface, decide whether a dynamic namespace such
as `header.<key>` or `item.<key>` is needed. If it is, specify the name grammar,
valid keys and escaping, data shape, exact and generic fallback precedence,
collisions, typing, introspection, and invalid-name behavior. Dynamic slots
require proven parser and runtime support before implementation.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| Replace | Replace | Replace | Replace | Replace | Replace |

Component-authored notifications use optional callback inputs such as
`onValueChange` through `$c-props`. Alpine `@...` listeners remain the surface
for native browser events. Add a custom DOM event only for a separately
justified DOM interop or lifecycle requirement.

Document any public method such as `focus()`, `open()`, `close()`, `scrollTo()`,
or `validate()`, including preconditions, return value, failure behavior, and
effect during server replacement. Omit the method surface when ordinary state
and refs are sufficient.

## 8. Semantics, keyboard, focus, and assistive technology

Specify native elements, roles, names, descriptions, relationships, and every
exposed ARIA state. Include accessible-name requirements and errors.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| Replace | Replace | Replace | Replace | Replace |

Cover forward and reverse Tab order, pointer and touch, disabled-item rules,
focus entry and restoration, focus visibility, nested components, and the
screen-reader announcements needed to complete the user task.

## 9. Native forms and validation

When the component participates in a form, define its submitted name and
values, disabled and read-only behavior, required and constraint validation,
reset, Enter submission, multiple submitters, form ownership, autocomplete,
and no-JavaScript behavior. Cover Citry Events success, server validation,
transport failure, retry, cancellation, and preservation of edits and focus.

If the family is not a form participant, state that explicitly and identify
any native controls rendered inside consumer slots.

## 10. Styling and theme contract

Follow [`../ui_theme.md`](../ui_theme.md).

Document variants, sizes, densities, intents, and all supported combinations.
Separate stable public customization from implementation styling:

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| Replace | Replace | Replace | Replace |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| Replace | Replace | Replace | Replace |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| Replace | Replace | Replace |

Public variables are inherited inputs resolved through private effective
variables. Default rules live in the documented cascade layer and use low
specificity. Test ancestor and root variables, public element selectors, and
variant or density fallback precedence through computed styles.

## 11. Environmental behavior

Define and test:

- default light and dark color schemes;
- nested color-scheme scopes;
- right-to-left layout and logical properties;
- reduced motion and forced colors;
- 200% and 400% zoom, text spacing, and long content;
- narrow, wide, coarse-pointer, touch, and virtual-keyboard cases; and
- print behavior when the component has meaningful printable content.

Inventory every library-authored visible string even though locale selection
and translation remain separate follow-up work.

## 12. Overlay and layering behavior

For an overlay or a component that opens one, specify its host, physical and
Citry ownership, color-scheme inheritance, stacking category, anchor and
collision behavior, focus containment, outside interaction, Escape, scroll
locking, background inertness, nested overlays, restoration, and cleanup.

If the family never creates or controls an overlay, state that explicitly.

## 13. Collections, async data, and identity

For collection components, define key identity, ordering, selection, disabled
items, empty and error states, add/remove/reorder behavior, pagination or
virtualization boundaries, and dynamic slot resolution.

For async work, define loading ownership, cancellation, supersession,
out-of-order results, errors, retry, offline behavior, and what remains
interactive while a request is pending.

## 14. Server render, morph, and cleanup

Specify the useful no-JavaScript output, client activation, repeated
initialization, listener and observer cleanup, fragment insertion, and morphing
while each meaningful state is active. Cover focus, selection, edits,
composition, pending requests, open overlays, nested roots, teleports, and
component removal.

## 15. Security and content trust

Classify text, HTML, URLs, attributes, file metadata, and remote data as
escaped, validated, trusted-only, or rejected. Cover attempts to replace owned
identity or browser-expression attributes, generated-ID safety, cross-instance
async results, and any component-specific threat.

## 16. Assets and performance

List component CSS, JavaScript, icons, fonts, observers, listeners, and shared
dependencies. Record raw, gzip, and Brotli sizes plus the relevant repeated
instance and first-interaction budgets. State whether the component adds a
client asset when used statically.

## 17. Acceptance matrix

List the render, schema, typing, interaction, accessibility, visual, lifecycle,
security, performance, packaging, host, and browser evidence required for this
family. Reuse the Python-owned scenario catalog across docs live examples,
standalone routes, Playwright, screenshots, axe, Lighthouse, and manual tasks.

Separate automated evidence from manual keyboard, assistive-technology, and
visual-design sign-off. A component is not supported merely because its source
file or preview exists.

## 18. Compatibility classification

Classify every advertised surface:

1. **Stable public API:** component names, server-input and client-input names and
   meanings, behavior-affecting defaults, slots and slot data, callbacks,
   methods, public variables, selectors, reflected attributes, form output, and error
   behavior.
2. **Behavioral and structural contract:** semantics, keyboard and focus,
   controlled-state behavior, no-JavaScript output, and only the DOM elements
   or relationships documented as required.
3. **Evolvable design:** exact theme values, spacing, shadows, animation, and
   undocumented wrappers may improve while the public meaning and acceptance
   requirements remain intact. Record user-visible changes in release notes.
4. **Private implementation:** `.cui-*` classes, `--_cui-*` variables,
   behavior-only attributes, JavaScript organization, and incidental markup.

Changing a stable name, type, meaning, or behavior follows the library's
semantic-versioning and deprecation policy. Do not accidentally promote an
implementation detail by using it in public examples or tests.

## 19. Public documentation contract

The component-owned `api.md` is the reader-first guide. Its required sibling
`api.yml` is the exhaustive structured API reference. The docs builder
validates and combines them. Do not author an `## API reference` section in
Markdown.

Order the guide by likely use: valid composition first, common
configuration and controlled use next, then specialized composition,
interaction, environment, and edge cases.

Follow the shared
[`_preview.md`](./_preview.md) contract for result-first component previews,
source disclosure, live editing, example controls, and focused browser checks.
This component specification owns the concrete example catalog and maps every
visual or interactive contract to at least one public example.

Draft that catalog before implementation. For each planned example, record its
reader task, fixture theme and copy, visible states, controls, interaction,
environmental profiles, contract coverage, source-module name, and focused
browser evidence. A working preview is not required at the design gate, but
its composition and expected behavior must be specific enough to review.

Organize `api.yml` by Inputs, Slots, Events, Methods, CSS, Attributes,
Selectors, and Interfaces. Split every category by owning
component. Label inputs explicitly as server or client, and state whether the
reader passes them through component tags or Python composition, or through
browser `$c-props`. Put whole-pattern keyboard and focus behavior in the guide,
not under an arbitrary class.

Slot rows show exact inline data shapes and link named records to Interfaces.
Input rows expand public aliases inline and also link them to Interfaces, so a
reader never has to follow a link to interpret a row. Event rows treat callback
inputs such as `onValueChange` as component events and distinguish them from
native Alpine `@...` listeners. Attributes document reflected public
`data-*` output without using "state" as a category name. Selectors document
the exact `[data-citry-ui-part="..."]` contract rather than calling these
Shadow DOM parts. CSS variables are grouped under the component that reads
them. Interfaces define every referenced alias and record field.

Give every table and entry a stable kebab-case ID. The renderer derives public
anchors from those IDs, independent of heading IDs or the table renderer. Keep
released IDs stable. The selector-entry `anchor` override is reserved for
preserving an already published noncanonical anchor during migration.

Keep routine contract detail in table rows and move longer cross-component or
edge-case explanations into the guide or a concise admonition. Avoid trailing
prose below tables. Omit empty per-component subsections; when a top-level
category is empty for the whole family, write `-` without listing each
component that lacks it.

## 20. Open decisions and deferred work

List unresolved choices, the evidence that would settle them, the owner, and
whether they block implementation or release. Do not describe removed APIs as
future guidance.
