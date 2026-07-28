# Citry UI component policy

**Status:** policy for the experimental Citry UI pressure components. Follow
the repository-wide
[`component authoring best practices`](../../../../docs/best-practices/component-authoring.md)
alongside this package-specific contract.

## Package layout and exports

Each family owns one `citry_ui/components/c*.py` module containing its slot-data
schemas, supporting public types, helpers, and headless and styled
`LibraryComponent` definitions. `citry_ui/components/__init__.py` is the one
ordered public component catalog. The package root creates
`__citry_library__` from that catalog.

Do not add constructor factories, invocation facades, component specs,
registration callbacks, or per-component installation references. The public
`LibraryComponent` definition is also the Python composition entry point.

Do not set `name` when the registry name is the class name. Use an explicit
name only for an intentional public rename.

## Stable styled-component parts

`data-citry-ui-part` names a stable, documented element inside a styled
component. It is:

- a public selector for targeted theme and application overrides;
- a durable inspection hook for galleries and debugging; and
- a semantic test selector when the part itself is the contract.

It is not merely a test marker, and it does not encode component state or
instance identity. Use native ARIA state or a dedicated `data-state` attribute
for state. Citry owns render identity.

Part names become public API when a component is released and must appear in
that component's design document. Tests prefer roles, accessible names, and
native relationships unless the part marker itself is under test. A part
marker follows `c-bind` when consumers must not override it:

```html
<button
  class="cui-button"
  c-bind="data.attrs"
  data-citry-ui-part="button"
>
```

Styled components place default theme rules in the `citry-ui.theme` layer.

## Compound component boundaries

Compound components use `provide()` and `inject()` for ambient state. A child
that terminates the current compound scope calls `unprovide(key)` before it
renders user content. Descendants then observe the key as missing until a
nested root provides a fresh value.

Tabs apply this rule at Tab and TabPanel boundaries. This rejects `Tab > Tab`
and requires a fresh root, producing `Tabs > Tab > Tabs > Tab` at the compound
context level. In styled HTML, nested interactive Tabs belongs inside a
TabPanel because a native button cannot contain interactive descendants. A
Tabs root also hides an inherited TabList context before establishing its own.

## Production gate and deferred work

The Button, Field, Input, Table, and Tabs implementations are architecture
pressure cases, not released component specifications. They contain no
library-owned client interaction; current Tabs expresses server-selected
semantics only. Apply the global specification process before treating any of
them as production components.
Use the shared [`quality test strategy`](../../../../docs/design/ui_research/quality-test-strategy.md)
for accessibility, interaction, visual, performance, security, and packaging
coverage.

Define reusable Python scenarios and pass the two-adapter Storybook feasibility
gate before broad production implementation. Storybook is the planned
maintainer state browser. Standalone routes remain available for Lighthouse,
performance, direct browser tests, and manual work that requires a complete
page without Storybook chrome. Build a custom gallery only after a documented
Storybook shortcoming. Every documented state and meaningful combination needs
a scenario.

Disposable browser-readiness components and workflows stay outside the public
component catalog. They prove the framework before production specifications;
they do not become supported APIs by appearing in Storybook.

Before choosing the production relationship between styled and headless
variants, benchmark both designs:

- styled components rendering their headless component internally; and
- independent styled and headless implementations that share behavior but do
  not render through each other.

Measure server render time, component count, allocations, output size, and
client initialization across realistic trees. The pressure implementation's
`Headless > Styled` composition is not yet a performance commitment.

Localization remains separate follow-up work. Component specifications should
inventory every user-visible string and its purpose without freezing a locale
API before that inventory exposes the translation, formatting, direction, and
locale-selection requirements.
