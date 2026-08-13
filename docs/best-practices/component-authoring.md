# Component authoring best practices

These conventions apply to component implementations throughout the Citry
repository. Package-specific policy belongs in that package's own docs and
links back here.

## Keep each component family together

A small component family should be readable in one runtime source module. Its
family directory may also own internal notes, public docs source, focused
fixtures, and tests. Keep public value types, schemas, behavior helpers,
component definitions, templates, JavaScript, and CSS together in the runtime
module until a concrete maintenance problem justifies another split. Group
declarations by component, then by its variant. Do not place every kwargs class
in one section and every slots class in another.

Keep registration and package catalog plumbing out of component modules. A
component author should be able to change a component without navigating the
installation machinery. Package builds must explicitly exclude family docs,
fixtures, reports, screenshots, and tests when those files live beside runtime
code.

Core built-in components live in `citry/components/`. A component that exists
only because an extension is installed lives with that extension, such as
`citry/ext/cache/components.py` or `citry/ext/i18n/components.py`. The central
built-in registry may create it, but its source and tests stay with the feature
that owns its behavior.

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
4. `template`, `js`, and `css`; and
5. `messages` or `messages_file`, as the final member of the component class.

When a component owns that final message asset, declare the language of its
defining source with `class I18n: messages_locale = "..."` near the nested
schemas. The asset activates engine-wide server source mode, so other
registered components may call its public keys without rendering the owner.
Do not add a parallel Python table of source strings.

Keep a helper or lifecycle method near the behavior it supports, but preserve
that overall direction. In particular, do not place a data method below the
template that reads its values, and do not place any member after the
component's source-message declaration.

## Declare inline assets directly

Assign multiline `template`, `js`, `css`, and `messages` assets directly to triple-quoted
class fields. Citry removes their common indentation when it loads them, so
the declarations can follow ordinary Python indentation without changing the
rendered HTML or the loaded JavaScript and CSS:

```python
class Notice(Component):
    template = """
      <aside>
        <c-slot />
      </aside>
    """
```

Do not wrap these literals in `dedent()`, `strip()`, or a package-specific
whitespace helper. Do not split one asset across implicitly concatenated string
literals. Direct assignments let the checker, formatter, language server, and
syntax highlighter recognize the embedded language. Use a file asset when
leading indentation itself is significant or the source should be kept
byte-for-byte.

## Compose extensions through public values

Citry's component rules also apply when two extensions meet:

- values do not leak between extensions;
- the handoff uses an existing public contract;
- missing required values fail clearly; and
- each extension keeps one small set of rules that works with every peer.

For example, Cache already lets a component return any stable value from
`Cache.vary()`. I18n already exposes the component's locale context. A localized
component combines them through those two ordinary APIs:

```python
class Cache:
    enabled = True

    def vary(self, kwargs, slots):
        return {
            "kwargs": kwargs,
            "locale_context": self.component.i18n.context.identity,
        }
```

Cache does not need a dependency flag for each peer extension, a peer-only
argument to `vary()`, or an import from the i18n extension. The same `vary()` rule works for
an authenticated user, a feature flag, a tenant, or any future extension.

Avoid these pair-specific bridges:

- adding one extension's field to another extension's nested config;
- changing a callback signature only when a named peer is installed;
- importing another extension's private class or reaching into its private
  state; and
- adding one branch per extension combination.

When every extension needs the same integration point, add one generic core
hook. For example, any extension may ask Cache to bypass a lookup through the
same render-cache hook. The hook must not name or special-case its callers.

## Pass provided values explicitly at render roots

Every direct `render()` call starts a new component tree. Pass the values that
tree may inject through the call itself:

```python
from citry.ext.i18n import make_context


context = make_context(
    app,
    locale="cs-CZ",
)
html = Page().render(
    provides={"citry_i18n": context},
)
```

The root and everything rendered below it may inject those values. Components,
expressions, and slot content rendered as part of that tree receive the values
through the normal render path.

A component rendered directly inside `template_data()` is different. That call
starts another root, so it receives nothing from the caller's tree unless the
call passes the value again:

```python
def template_data(self, kwargs, slots):
    locale_context = self.i18n.context
    card_html = AccountCard().render(
        provides={"citry_i18n": locale_context},
    )
    return {"card_html": card_html}
```

This small amount of repetition keeps the provided-value dependency
predictable. Another page, task, test, or thread cannot silently change the
nested component's locale merely by changing its own provided context.

A page may accept a context through a Kwarg and call `provide()` itself when
that makes its public dependency clearer. The root `provides` argument is the
shorter form when the request handler already owns the value. Both use the same
provide/inject channel, and neither puts the value into template variables.

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
>
  {{ batches_loaded }}
  <button
    type="button"
    @click="batchesLoaded += 1"
  >
    Load another batch
  </button>
</section>
```

Here, `batches_loaded` is a Python name and `batchesLoaded` is a browser name.
Name a value for the side that owns it, even when both names appear in the
same template. This makes the boundary visible and keeps code idiomatic on
both sides.

## Optimize frequent APIs for legible brevity

Start a component design by listing the concrete jobs users will perform with
it. Include the ordinary cases that are easy to overlook when research starts
from an existing implementation. For an action control, that includes native
form actions, pending work, destructive actions, navigation with action-like
styling, compact toolbar use, decorations, and width changes. For every job,
record the shortest supported expression and whether the job belongs to this
component, native HTML or attributes, CSS or utility classes, composition, or
a separate component.

Components appear repeatedly in application code. Treat names and required
structure as a writing budget:

- keep the smallest common use free of administrative wrappers and redundant
  inputs;
- prefer short, established vocabulary such as `sm`, `md`, and `lg` when its
  meaning is conventional across UI libraries;
- abbreviate only when the result remains immediately legible in isolation;
- keep one spelling for one concept across the suite; and
- spend longer names on uncommon options or distinctions where the extra word
  prevents ambiguity.

Do not optimize character count alone. A private abbreviation, overloaded
boolean, or implicit semantic switch costs more to learn than it saves to
type. Review the smallest template and Python-composition examples together,
then audit repeated realistic use before freezing names.

## Keep root class and style inputs direct

Every reusable styled component exposes optional top-level `class_` and
`style` server inputs for its documented root element. Do not make routine
styling pass through a general `attrs` mapping. `class_` uses the trailing
underscore because `class` is a Python keyword and Citry component inputs keep
the same name in Python composition and component tags.

Accept Citry's structured class and style values, not strings alone:

```python
CButton(
    class_=["toolbar-action", {"is-current": current}],
    style={"inline-size": "100%"},
    slots={"default": "Open"},
)
```

```citry-html
<c-CButton
  c-class_="['toolbar-action', {'is-current': current}]"
  c-style="{'inline-size': '100%'}"
>
  Open
</c-CButton>
```

Keep `attrs` for other native, ARIA, Alpine, and `data-*` attributes. Existing
class/style values in `attrs` remain valid and merge with the direct inputs
through Citry's ordinary HTML attribute rules. A compound declaration
component carries these inputs to the concrete element it declares.

## Separate component callbacks from native browser events

Expose a component-authored browser notification as an optional callback input
through `$c-props`, such as `onValueChange`. Use Alpine `@click`,
`@keydown`, `@input`, `@change`, and similar listeners for the native events
already emitted by the component's HTML. Do not dispatch a second custom DOM
event that duplicates a component callback or a native event.

A custom DOM event is an exception, not the default Citry UI notification
surface. Add one only when a specification identifies a concrete DOM-level
interop or lifecycle requirement that a callback and the rendered element's
native events cannot satisfy. Specify its target, bubbling, composition,
cancellation, ordering, payload, nested-component behavior, and relationship
to callbacks before implementation.

For every production component, research the official APIs and implementations
of relevant React, Vue, Web Component, and native counterparts before freezing
its callbacks. Record:

- which callbacks or events exist and which interaction or lifecycle causes
  each one;
- whether controlled-property updates, programmatic changes, initialization,
  or repeated same-value interactions notify;
- whether the notification represents a request or an already committed
  change;
- ordering relative to focus movement, DOM synchronization, and other
  callbacks;
- cancellation behavior; and
- the exact payload, including old and new values, source information, and
  native event objects where applicable.

The component specification must then state Citry UI's chosen callback names,
conditions, timing, and payload. Similar names across other libraries are
evidence, not a reason to copy ambiguous semantics.

## Research composition and slots before freezing them

For every production component, compare how relevant React, Vue, Web
Component, and native counterparts let consumers replace or extend content.
The comparison includes ordinary children, named and scoped slots, render
callbacks, replaceable internal parts, and collection renderers. Record which
capability each library exposes and the data it passes to consumer content.

The component specification must define every chosen slot's:

- name, purpose, and owning component;
- required or optional status, cardinality, and fallback content;
- slot-data fields and whether each field can change in the browser;
- valid nesting and the component context visible inside the fill; and
- error behavior for missing, duplicate, misplaced, or unknown fills.

Use explicit named slots for a finite component anatomy. For data-driven
components with an unbounded set of keys, also evaluate a dynamic slot family
such as `header.<key>` or `item.<key>`. A dynamic family advances only when its
specification defines the name grammar, valid keys and escaping, the slot-data
shape, exact-match and generic fallback precedence, collision handling,
introspection and typing behavior, and errors for unsupported names. It also
needs proven framework and compiler support. Do not hide an unproven dynamic
lookup inside one component implementation.

Similar slot names across other libraries are research evidence. Citry UI
chooses the smallest composition surface that covers its supported scenarios
and records why broader internal replacement points were omitted.

## Revisit compound anatomy after implementation

Once a component family works end to end, review its public anatomy again
before treating the first shape as final. Implementation exposes which
components own behavior and which exist only to group declarations or forward
inputs. Remove a structural component when its inputs can move to an existing
owner and the same composition, validation, semantics, customization, and
extension points remain available.

Do not optimize for the fewest tags by itself. Compare the before and after
APIs against every supported scenario, including Python composition, dynamic
declarations, slots, nesting, accessibility, attributes, selectors, and future
extension needs. Record why each remaining public component earns its place.
Tabs are the reference example: collecting `CTab` and `CTabPanel` declarations
lets `CTabs` generate the one semantic TabList internally, so a public
list-wrapper component adds ceremony without adding expressivity.

## Design server inputs and client overrides together

A Python kwarg is a server-render input. A value returned by `js_data()` is an
inert snapshot for that render. A declared `$component` prop is a separate,
reactive browser input. Do not assume that defining one automatically creates
the others, and do not expose every Python kwarg as a client prop.

For every public input, decide whether it is:

- structural and server-only, such as slot topology, generated identity, or an
  attribute map;
- an initial value whose browser-local state may later diverge;
- a configuration value with an optional reactive client override; or
- a controlled browser value or callback.

When an optional client prop should fall back to the server value, declare no
JavaScript default. Citry uses `undefined` for an omitted optional prop, so the
component can resolve a configuration value as "valid prop when supplied,
otherwise `js_data()` fallback." `null`, `false`, `0`, and `""` are supplied
values and require explicit component semantics or validation. The complete
props omission and recovery contract lives in
[`alpinejs.md`](../design/alpinejs.md#43-prop-declaration-and-updates).

Citry skips a component's first client initialization when its prop declaration
rejects the initial supply. If a component promises that an invalid individual
prop falls back while the rest stays interactive, do not rely on a constructor
declaration for that field: accept it into the props view and validate it in
the initializer before resolving the effective value. Otherwise document and
test the first-supply failure as part of the component contract. A malformed
supplier bag is still a boundary failure owned by Citry.

Do not apply that stateless fallback rule blindly to controlled/uncontrolled
state. Specify what happens when control is added or removed. For example, a
selection component may preserve its last controlled selection when its
`value` prop becomes omitted instead of resetting to the original server
default.

Resolve each input through one client path, then synchronize every surface
that depends on it: native DOM properties, ARIA, focus and roving `tabindex`,
visibility, keyboard and pointer behavior, event guards, and documented state
or configuration attributes. Native and ARIA attributes remain the semantic
truth. A public `data-*` state or configuration attribute is a read-only DOM
mirror for CSS, inspection, and selectors; mutating that mirror must not
reconfigure the component.

Each production component specification must inventory the server-only and
client-reactive inputs, their precedence and removal rules, accepted `null`
semantics, downstream surfaces, invalid-value recovery, and nested-component
isolation. Add browser tests that change reactive inputs after initialization;
an initial server-render assertion does not prove the client contract.

## Specify headless APIs independently when a product supports them

A headless component owns behavior, state, relationships, and bindings. It
does not own the consumer's HTML. Expose the values a fill needs through slot
data so the consumer can apply them to custom markup.

Do not assume every styled family must ship a headless counterpart. That is a
product and support decision backed by actual application needs. When both are
supported, treat them as separate public components with separate `Kwargs`,
`Slots`, and slot-data schema types, even when one schema inherits every field
from another. Do not make a production styled component render through a
headless component unless representative-page measurements and lifecycle tests
justify the additional component boundary.

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

Component specifications must distinguish public variables, element selectors,
and reflected attributes from private implementation classes. A stable
`data-citry-ui-part` marker is a semantic-versioned customization API, not just
a test selector. Public documentation lists its exact attribute selector under
**Selectors** rather than implying the Shadow DOM `::part()` API. Document the
element it identifies, its purpose, its supported conditions, and any DOM
relationship consumers may rely on. List supported reflected `data-*` output
under **Attributes**, not "state attributes", so the wording cannot be confused
with Citry's server event-handler State.

Treat public component variables as inherited inputs. Resolve their fallback
values into private effective variables on the component root, then use those
private variables in implementation rules. Assigning the public variable's
default on the root prevents a value set on an ancestor from winning. Private
effective variables are implementation details and may change without notice.

Render tests prove that variables and public selectors are present. Browser tests
must also inspect computed styles after overriding variables from an ancestor,
from the component root, and through a documented element selector. Cover each
fallback whose value changes with a component variant or density.

## Specify production components before implementation

Pressure components are useful for discovering framework constraints, but do
not promote one by incrementally polishing the spike. Begin production work
with a component-specific design document informed by research across relevant
React, Vue, Web Component, and native implementations.

Citry UI production families start from the reusable
[`component specification template`](../design/ui_components/_template.md) and
follow the shared
[`theme and color-scheme contract`](../design/ui_theme.md).

At minimum, specify:

- scope, non-goals, and headless/styled relationships;
- prior art, recurring patterns, and material user complaints;
- kwargs, static and dynamic slots, slot data, fallback and collision rules,
  callbacks, exceptional custom events, methods, and returned values;
- semantic HTML, ARIA relationships, keyboard behavior, and focus movement;
- controlled, uncontrolled, server, and browser state;
- forms, async states, progressive enhancement, and failure handling;
- CSS variables, public selectors, reflected attributes, layers, and override rules;
- right-to-left layout, reduced motion, forced colors, zoom, touch, and
  responsive behavior;
- server output, client behavior, morph behavior, cleanup, and dependency cost;
- security boundaries; and
- unit, render, browser, accessibility, visual, performance, and packaging
  acceptance tests.

Build broad production coverage after reusable scenarios and docs live
examples exist. The same scenarios should support visual inspection, keyboard
review, automated accessibility checks, screenshot coverage, and standalone
complete-page tests. Standalone pages are quality surfaces, not a separate
public gallery product. Optional preview extensions do not gate component
implementation.
