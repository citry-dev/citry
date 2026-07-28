# Component authoring best practices

These conventions apply to component implementations throughout the Citry
repository. Package-specific policy belongs in that package's own docs and
links back here.

## Keep each component family together

A component family should be readable in one source module. Keep its public
value types, schemas, behavior helpers, component definitions, templates,
JavaScript, and CSS together. Group declarations by component, then by its
variant. Do not place every kwargs class in one section and every slots class
in another.

Keep registration and package catalog plumbing out of component modules. A
component author should be able to change a component without navigating the
installation machinery.

## Nest component-owned schemas

Define `Kwargs` and `Slots` on the component that owns them. This keeps the
public surface compact and gives type annotations an obvious namespace:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from citry import LibraryComponent, SlotInput


class ActionSlotData:
    disabled: bool


class Action(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        disabled: bool = False

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[ActionSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        return {"slot_data": {"disabled": kwargs.disabled}}
```

Inside a method defined in the same component body, refer to sibling schemas as
`Kwargs` and `Slots`, as above. Use qualified names such as `Action.Kwargs` and
`Action.Slots` from outside the component or when qualification is needed to
disambiguate the type.

Define distinct schemas for distinct components, even when one schema simply
inherits another. Define empty `Kwargs` and `Slots` schemas when the component
has no fields so those names remain dependable. Do not define an empty
`State` merely for symmetry: state is behavior, and declaring it can opt a
component into event or state processing.

Citry converts plain nested data-schema classes to slotted dataclasses when it
creates a concrete component class. A deferred `LibraryComponent` definition
should use explicit `@dataclass(slots=True)` schemas when callers need to
construct or inspect those schemas before the library is registered.

Data methods receive the exact component-owned types. Do not give `slots` a
`None` default, rename an unused argument to `_slots`, cast an already typed
argument, or create a duplicate `typed_kwargs` variable. Citry supplies an
empty schema instance when a declared component has no slot values.

Schema class names and fields should be self-explanatory. Do not add class
docstrings that repeat them. Add field documentation when it carries actual
public contract information.

## Order component members from inputs to output

Readers should meet a component's public inputs and behavior before its
rendering implementation. Use this order inside a component class:

1. nested `Kwargs`, `Slots`, and `State` schemas;
2. event handlers, when present;
3. data methods such as `template_data()`, `js_data()`, and `css_data()`; and
4. `template`, `js`, and `css`.

Keep a helper or lifecycle method near the behavior it supports, but preserve
that overall direction. In particular, do not place a data method below the
template that reads its values.

## Use each language's naming style at the browser boundary

Keep Python names in `snake_case`. This includes template expressions, event
handler names, and payload keys written by Python. Use `camelCase` for
JavaScript variables, Alpine state, methods, and browser-side scope names.
Translate explicitly where a value crosses between them:

```citry-html
<section
  c-x-data="{
    'batchesLoaded': batches_loaded,
  }"
  @choice-picker:loaded="
    batchesLoaded = $event.detail.batches_loaded
  "
>
  {{ batches_loaded }}
</section>
```

Here, `batches_loaded` is a Python name and `batchesLoaded` is a browser name.
Name a value for the side that owns it, even when both names appear in the
same template. This makes the boundary visible and keeps code idiomatic on
both sides.

## Separate headless behavior from styled markup

A headless component owns behavior, state, relationships, and bindings. It
does not own the consumer's HTML. Expose the values a fill needs through slot
data so the consumer can apply them to custom markup.

Headless and styled variants are separate public components. They should have
separate `Kwargs`, `Slots`, and slot-data schema types, even when the styled
variant reuses every field from the headless variant.

## Format templates for review

Keep `<c-slot>` and its fallback text on separate lines:

```html
<c-slot name="empty">
  No data
</c-slot>
```

Whitespace is rendered content. A low-level transparent or dynamic built-in
may keep adjacent template tokens compact when line breaks would change its
output; document that exception beside the template.

Use multiline component templates. When a tag has more than two attributes,
or one long attribute, put each attribute on its own line and put the closing
`>` on its own line.

Order attributes by role:

1. identity, such as component name, slot name, or semantic key;
2. component and slot inputs;
3. ordinary HTML attributes;
4. other `data-*` attributes;
5. event handlers;
6. `c-bind` spreads.

Rightmost writes win, so place an attribute after a spread only when that
attribute must be protected from consumer overrides.

## Format CSS one declaration per line

Every declaration gets its own line, including short rules:

```css
:where(.tab[aria-selected="true"]) {
  border-color: #175cd3;
  color: #175cd3;
}
```

Component specifications must distinguish public variables, parts, and state
attributes from private implementation classes.

## Specify production components before implementation

Pressure components are useful for discovering framework constraints, but do
not promote one by incrementally polishing the spike. Begin production work
with a component-specific design document informed by research across relevant
React, Vue, Web Component, and native implementations.

At minimum, specify:

- scope, non-goals, and headless/styled relationships;
- prior art, recurring patterns, and material user complaints;
- kwargs, slots, slot data, events, methods, and returned values;
- semantic HTML, ARIA relationships, keyboard behavior, and focus movement;
- controlled, uncontrolled, server, and browser state;
- forms, async states, progressive enhancement, and failure handling;
- CSS variables, public parts, state attributes, layers, and override rules;
- right-to-left layout, reduced motion, forced colors, zoom, touch, and
  responsive behavior;
- server output, client behavior, morph behavior, cleanup, and dependency cost;
- security boundaries; and
- unit, render, browser, accessibility, visual, performance, and packaging
  acceptance tests.

Build broad production coverage after reusable scenarios and the planned
Storybook integration exist. The same scenarios should support visual
inspection, keyboard review, automated accessibility checks, screenshot
coverage, and standalone complete-page tests. Standalone pages are test
surfaces, not a second gallery product.
