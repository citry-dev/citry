# Citry UI component policy

**Status:** policy for Citry UI production and experimental components. Follow
the repository-wide
[`component authoring best practices`](../../../../docs/best-practices/component-authoring.md)
alongside this package-specific contract.

## Requalify one component family at a time

Tabs is the reference pass for the level of research, specification,
interaction, styling, examples, API reference, and testing expected from a
Citry UI family. Apply its method to each family, not its exact API or page
shape. Existing source is evidence to audit, not permission to skip design.

Use this order for a new family or an existing family being prepared for
release:

1. **Inventory the family.** Read its runtime, tests, quality scenarios,
   specification, maintainer notes, public guide, structured reference, and
   related composed pages. Classify each existing behavior as supported,
   provisional, contradicted, or untested.
2. **Catalog common jobs.** List what application authors use the family to
   accomplish, including common native-HTML, navigation, form, async,
   responsive, and composition cases that the existing component may omit.
   For every job, record the shortest intended template and Python expression
   and whether Citry solves it through direct API, native attributes, CSS or
   utility classes, composition, or a separate component.
3. **Refresh the research.** Start with the shared
   [`ui_research` index](../../../../docs/design/ui_research/README.md),
   [component taxonomy](../../../../docs/design/ui_research/component-taxonomy.md),
   [complaint register](../../../../docs/design/ui_research/complaint-register.md),
   and relevant ecosystem dossiers. Then inspect current component-specific
   standards, official documentation, implementation source, and material
   issue reports. Reuse current research; search again where coverage is
   missing, too broad, or stale.
4. **Record the evidence and decisions.** Section 2 of the family
   specification names every material source, its version or review date, the
   surface inspected, and the Citry UI decision it supports. Compare at least
   one mature styled suite, one accessibility or behavior-focused library,
   the closest native or standards pattern, and a Web Component implementation
   when one exists. Add other products because they expose a relevant design,
   not to meet a brand quota.
5. **Run the Vuetify disposition pass.** Treat current Vuetify as the primary
   styled-suite reference, with roughly 30 percent of the product-comparison
   decision weight. Distribute the remaining weight across the other relevant
   products instead of letting a large list dilute the strongest reference.
   Standards remain acceptance baselines, not votes. Walk every relevant
   Vuetify input, slot, event, method, state, and documented job and record how
   Citry supports it: direct API, native HTML or attributes, CSS or utility
   classes, composition, a separate component, or a deliberate omission with
   a reason. Matching the capability does not require copying the prop.
6. **Ratify the complete specification.** Resolve the 20-section
   [component specification template](../../../../docs/design/ui_components/_template.md),
   including unsupported cases and errors. Existing behavior changes when the
   evidence supports a better contract; the implementation does not decide the
   public API by default.
7. **Plan the public examples.** Before runtime edits, define the page theme,
   section order, example compositions, fixture copy, configurator controls,
   narrow and environmental cases, and contract coverage table under section
   19. Every visual or interactive contract maps to a planned rendered example
   or an explicit reason why prose and the API reference are sufficient.
8. **Review the design package.** Research, specification, and example catalog
   must be complete enough to evaluate together. Resolve every implementation
   blocker or mark it as an explicit deferral before changing runtime code.
9. **Implement and prove the contract.** Update runtime code, focused render
   and browser tests, reusable scenarios, host and lifecycle evidence, public
   guide, snippets, and `api.yml` from the ratified design. Keep these artifacts
   synchronized throughout the pass.
10. **Simplify and review.** Repeat the anatomy review, compare every public
   input, slot, callback, variable, selector, attribute, and interface across
   source and documentation, then inspect the complete page. Human visual
   polish, assistive-technology sessions, and live-device review remain named
   release evidence rather than silent assumptions.

Do not batch implementation across families. Finish the research and design
package for one family, implement it, learn from the result, and update this
policy before starting the next family when the pass exposes a reusable rule.

## Package layout and exports

Each family owns one `citry_ui/components/c*/` directory. Its `c*.py` runtime
module contains slot-data schemas, supporting public types, helpers, and styled
`LibraryComponent` definitions. The directory also owns `README.md` for
maintainers, `api.md` for public documentation, and focused tests or fixtures.
Every family keeps its structured API data in a sibling `api.yml`.
Setuptools excludes those support files from the wheel. Phase 7 component
families contain their styled public definitions and any private renderers
needed to implement the documented structure.
`citry_ui/components/__init__.py` is the one
ordered public component catalog. The package root creates
`__citry_library__` from that catalog.

Do not add constructor factories, invocation facades, component specs,
registration callbacks, or per-component installation references. The public
`LibraryComponent` definition is also the Python composition entry point.

Do not set `name` when the registry name is the class name. Use an explicit
name only for an intentional public rename.

## Choose one owner for compound state

When a wrapper and its control could both expose the same state, choose one
authority for the composed case. Required markers, native properties, ARIA,
messages, CSS attributes, and form behavior must never resolve the same state
through independent precedence rules. Standalone controls may own inputs that
their enclosing relationship component owns when composed. Reject duplicated
server state and diagnose ignored client state instead of permitting a split
result.

Native ancestor behavior may be stronger than component configuration. For
example, a disabled native fieldset disables descendants even when a child
requests `disabled=False`; reflected component state must show the browser's
effective result.

## Protect native vocabulary on native roots

Audit every public input name against attributes and properties of the native
root. If Citry UI uses the same short name for a presentation job, document
how callers still reach the native meaning and prove both in one test. Prefer
short frequent inputs when the two destinations stay unambiguous. Input
`size="sm"` and `attrs={"size": 24}` are the reference distinction between
visual geometry and native character width.

## Enforce structural invariants across both renderers

Validate component-authored descendants during server rendering when they can
register with their enclosing family. Slot content can also contain a plain
HTML custom control, so carry a private marker in the slot bindings and verify
the settled DOM during client initialization. This two-stage check lets a
Field enforce exactly one control without making a private client context part
of the public custom-control API.

## Direct root class and style inputs

Every public styled component defines optional `class_` and `style` server
inputs on its documented root. Both accept Citry's structured class/style
values. Merge them with any class/style values retained in `attrs`; do not
force routine styling through `attrs`.

Use `class_` in both Python composition and component tags because component
input names are shared across those surfaces and `class` is a Python keyword.
Declaration components such as `CTab` and `CTabPanel` carry the inputs to the
native element produced by the family renderer. List both inputs in every
component's specification and structured server-input reference, and prove
their root destination with a render test.

## Stable styled-component parts

`data-citry-ui-part` names a stable, documented element inside a styled
component. It is:

- a public selector for targeted theme and application overrides;
- a durable inspection hook for galleries and debugging; and
- a semantic test selector when the part itself is the contract.

It is not merely a test marker, and it does not encode component state or
instance identity. Use native ARIA state or a dedicated `data-state` attribute
for state. Citry owns render identity.

Public reflected attributes mirror the component's current effective browser
configuration or interaction status so CSS, inspection tools, and consumer
selectors can observe it. They are not the component's source of truth or an
imperative configuration API. Client behavior reads its own resolved values,
then keeps the native DOM, ARIA, and public mirrors synchronized. Private
behavior hooks must be documented separately from this public contract.

Part names become public API when a component is released and must appear in
that component's design document. Treat changing or removing a released part
name as a semantic-versioned API change. For each part, the design document
records the HTML element, semantic purpose, supported state and configuration
selectors, and any stable parent or child relationship. Tests prefer roles,
accessible names, and native relationships unless the part marker itself is
under test. A part marker follows `c-bind` when consumers must not override it:

```html
<button
  class="cui-button"
  c-bind="data.attrs"
  data-citry-ui-part="button"
>
```

Styled components place default theme rules in the `citry-ui.theme` layer.
Public `--cui-*` variables are inherited inputs and are not assigned defaults
directly on the component root. Resolve each input through a private
`--_cui-*` variable with its fallback, and use the private variable in the
component's rules. This keeps ancestor and root overrides working while making
the public variable list explicit in the source. Private variables are not
customization API.

Add browser coverage that reads computed styles after an ancestor variable
override and a public part-selector override. Presence assertions alone do not
prove the cascade contract. When a variant or density changes a fallback, test
both its fallback and a public override that must still win.

## Slot contracts

Follow the repository-wide slot research and specification rules. Every Citry
UI component design compares the relevant libraries' children, named or
scoped slots, collection renderers, and replaceable parts. It then documents
each chosen slot, its data, fallback, nesting, and errors.

Dynamic keyed slot families are appropriate for an unbounded data-driven
surface, such as per-column table headers or cells. They require a documented
namespace and proven Citry typing, introspection, parser, and runtime behavior
before a component adopts them. Finite component anatomy uses explicit named
slots.

Start every production family from the repository's
[`component specification template`](../../../../docs/design/ui_components/_template.md).
Apply the shared
[`theme and color-scheme contract`](../../../../docs/design/ui_theme.md) to all
styled components. A component is not ready for implementation until the
template's public inputs, state, composition, semantics, styling, lifecycle,
security, and acceptance sections are resolved or explicitly deferred.

## Compound component boundaries

Compound components use `provide()` and `inject()` for ambient state. A child
that terminates the current compound scope calls `unprovide(key)` before it
renders user content. Descendants then observe the key as missing until a
nested root provides a fresh value.

Tabs apply this rule at Tab and TabPanel boundaries. `CTab` and `CTabPanel`
first register lazy declaration data with their enclosing `CTabs`, then private
renderers invoke their content with the parent context unprovided. This rejects
`Tab > Tab` and requires a fresh root, producing `Tabs > Tab > Tabs > Tab` at
the compound context level. In styled HTML, nested interactive Tabs belongs
inside a TabPanel because a native button cannot contain interactive
descendants. A Tabs root also rejects an inherited Tabs context before
establishing its own.

Declaration-only children must fail when used outside their family root and
must not expose themselves from the public catalog as standalone rendered
components. Keep their captured Slots lazy so fill variables, render-site
provides, dependencies, and ownership are resolved at the final outlet. A
private renderer may be registered in the library manifest without being
re-exported as public API.

## Keep runtime, specification, and public reference synchronized

Treat each production family as three views of one contract:

1. the component module implements behavior and declares public CSS variables,
   selector markers, and reflected attributes;
2. `docs/design/ui_components/*.md` records the complete 20-section product,
   lifecycle, security, environment, compatibility, and acceptance decision;
3. the family-owned public documentation teaches common use and exhaustively
   lists Inputs, Slots, Events, Methods, CSS, Attributes, Selectors, and
   Interfaces. Keep the guide in `api.md` and the fixed API data in `api.yml`.

The public guide puts whole-pattern keyboard, focus, form, and lifecycle
guidance in `api.md`. The guide does not declare
`## API reference`; the docs builder validates `api.yml` and appends the eight
fixed categories. Omit empty per-component tables. Expand aliases and slot-data
shapes inline, link their named Interfaces, and give every input, slot, event,
attribute, selector, variable, record field, and interface entry a stable ID.
CSS-variable entries include the accepted value kind, purpose, and current
default or default derivation.

Generated tables use category-specific column widths by default. A table may
override them with `column_widths`, which must contain one value per column.
Use `fit` for a compact content-width column, `auto` for a column that consumes
remaining space, or a constrained `ch`, `rem`, or percentage width such as
`12rem`. Keep identifiers compact, keep type and default columns relatively
thin, and leave explanatory prose as the flexible column.

Table and entry IDs generate stable public anchors. Keep them after release.
The optional selector-entry `anchor` field exists only to retain a previously
published noncanonical anchor during migration; do not use it for new rows.

After a family works end to end, repeat its anatomy review. Remove structural
components that only group declarations or forward inputs when an existing
owner can preserve all semantics and customization. Then compare the runtime's
exact `--cui-*`, `data-citry-ui-part`, and reflected `data-*` surface against
both documents. `tests/test_component_contracts.py` automates this inventory,
the complete specification headings, public-variable fallback pattern, and the
ordering that keeps an owned part marker after a consumer `c-bind` spread.
Extend that table when a family deliberately adds or removes a reflected
attribute.

## Keep semantic collections smaller than interactive grids

Start data-display families from the closest native model. A native Table can
own captions, headers, keyed rows, simple footers, responsive overflow, and
presentation without owning selection, sorting, editing, virtualization, or
grid keyboard behavior. When advanced interaction changes roles, focus,
collection ownership, or async state, specify a separate DataTable or DataGrid
instead of adding flags to the semantic component.

For record-driven native output:

- list the simplest supported logical shape and reject spans, groups, or
  associations that the component cannot validate as a complete structure;
- copy and validate every caller-owned attribute mapping before template
  binding, including mappings nested in frozen records, so later mutation
  cannot bypass validation;
- provide concise column- or item-wide attribute defaults when repeating the
  same class, style, width, or native hint per record would dominate call
  sites;
- scope structural CSS through direct-child relationships so outer collection
  variants, density, stripes, hover, and borders do not restyle a nested
  instance; inherited public theme variables may still flow intentionally;
- separate bounded-container sticky behavior from page-scroll sticky behavior
  and document the scroll ancestor required by each;
- document when overflow can clip inline overlays and identify the visible,
  top-layer, or portal escape path; and
- keep live announcements outside a subtree marked `aria-busy`, preserve the
  live-region node across server morphs, and treat exact assistive-technology
  timing as manual evidence.

Server-only components do not need a documentation configurator. Use
side-by-side previews when a control would merely mutate server inputs in the
browser or swap hidden prerendered output.

## Production gate and deferred work

Button, Field/Input, Form, Tabs, Dialog, Combobox, and Table have Phase 7
production specifications and direct styled implementations. They remain
pre-release until the complete acceptance and release matrices pass. Apply the
global specification process before adding or promoting another family.
Use the shared [`quality test strategy`](../../../../docs/design/ui_research/quality-test-strategy.md)
for accessibility, interaction, visual, performance, security, and packaging
coverage.

Define reusable Python scenarios, docs live examples, and standalone routes
before broad production implementation. Standalone routes support Lighthouse,
performance, direct browser tests, and manual work that requires a complete
page. Use the smallest pairwise and boundary sample that can protect a release
decision; the specification inventories the complete contract without forcing
every state into every tool. Storybook is optional extension work tracked
in [`extensions_storybook.md`](../../../../docs/design/extensions_storybook.md),
not a production gate.

Disposable browser-readiness components and workflows stay outside the public
component catalog. They prove the framework before production specifications;
they do not become supported APIs by appearing in a preview tool.

Headless component APIs are parked. Revisit them only after the styled library
has broader component coverage and an actual application supplies concrete
authoring needs and representative pages. Those pages should then drive API
design and measure server render time, component count, allocations, output
size, and client initialization. The pressure implementation's
`Headless > Styled` composition is not a production commitment.

Localization remains separate follow-up work. Component specifications should
inventory every user-visible string and its purpose without freezing a locale
API before that inventory exposes the translation, formatting, direction, and
locale-selection requirements.

## Server inputs and reactive client overrides

Follow the repository-wide
[`server input and client override rules`](../../../../docs/best-practices/component-authoring.md#design-server-inputs-and-client-overrides-together).
Every Citry UI component specification must classify each Python input instead
of automatically exposing every kwarg as a prop. For each chosen reactive
override, test its Python fallback, initial client precedence, later updates,
removal, invalid and `null` values, every affected semantic and visual surface,
and isolation from nested component roots.

## Browser notification surfaces

Follow the repository-wide
[`component callback and native event rules`](../../../../docs/best-practices/component-authoring.md#separate-component-callbacks-from-native-browser-events).
Citry UI components expose their own semantic notifications as optional
callback inputs such as `onValueChange` supplied through `$c-props`. Consumer
templates use Alpine `@...` listeners for native events from the rendered HTML.
Do not add a custom DOM event as a second spelling of either surface.

Each component design must compare relevant libraries' notification APIs and
then define the chosen callback's trigger conditions, controlled-state
semantics, ordering, cancellation behavior, and exact arguments. A custom DOM
event requires a separately documented DOM interop or lifecycle need.
