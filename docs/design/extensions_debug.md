# Design: the Debug extension

**Status (2026-07-21): implemented, with the cross-engine serialization rule
folded in after adversarial review.** This document defines
Citry's opt-in visual debugging extension. The extension draws blue boundaries
around component output and red boundaries around slot output, with labels that
identify each boundary.

For the extension framework see [`extensions.md`](extensions.md). For the
broader extension backlog see [`extensions_roadmap.md`](extensions_roadmap.md).
For operating rules see [`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. Prior art and scope

The first Citry record is the June 12 migration audit in
[`migration_djc.md`](migration_djc.md#extensionsdebug_highlightpy-142-lines).
It classifies django-components' DebugHighlight extension as portable and maps
its behavior to Citry's `on_component_rendered` and `on_slot_rendered` hooks.
It also places the two settings on the extension's own configuration rather
than on the core `CitrySettings` schema.

The later [`extensions_roadmap.md`](extensions_roadmap.md#2-build-now)
consolidates the Citry API under the name `Debug`. The upstream behavior and
test matrix came from upstream
[`test_component_highlight.py`](https://github.com/django-components/django-components/blob/5d4d4f5d13dd06c80ba389f30fc63fdbb71cda75/tests/test_component_highlight.py):
blue component boundaries, red slot boundaries, labels, engine-wide defaults,
component overrides, nested components, and repeated slots.

This extension is the small visual boundary tool. The future debug-toolbar
panel is a separate extension with request-level render details, timings, slot
fills, and dependency inspection. Its runtime record is explored in
[`component_tracing.md`](component_tracing.md).

## 2. Public API and configuration

`Debug` is bundled with Citry but opt-in. It is imported from
`citry.ext.debug` and passed to a `Citry` instance:

```python
from citry import Citry
from citry.ext.debug import Debug

app = Citry(
    extensions=[Debug],
    extensions_defaults={
        "debug": {
            "highlight_components": True,
            "highlight_slots": True,
        },
    },
)
```

The extension is not part of `_builtin_extensions()`. A `Citry` instance pays
its render-hook cost only when the application installs it.

The extension name is `"debug"`, so a component's nested configuration class
is `Debug` and its render-time configuration is available as
`component.debug`:

```python
from citry import Component


class Card(Component):
    citry = app
    template = """
        <article>
            <c-slot name="body" />
        </article>
    """

    class Debug:
        highlight_components = True
        highlight_slots = False
```

`Debug.Config` defines two fields, both defaulting to `False`:

| Field | Meaning |
|---|---|
| `highlight_components` | Draw and label the boundary around this component's output. |
| `highlight_slots` | Draw and label the boundaries around slots rendered by this component. |

Both declaration sites use strict validation:

- an unknown field raises during `Citry` construction or component class
  definition;
- each value must be an actual `bool`;
- normal extension precedence applies: factory default, then
  `extensions_defaults["debug"]`, then the component's nested `Debug` class.

The extension does not expose color configuration in its first version.
Components use the established blue palette and slots use the established red
palette.

## 3. Rendering contract

### 3.1 Labels and wrappers

An enabled component boundary contains the component class name and render ID.
An enabled slot boundary contains the receiving component class name and the
resolved slot name. Labels are HTML-escaped text rendered in a dedicated label
element. Names and IDs are never interpolated into CSS source.

The wrapper elements carry stable Citry Debug classes for inspection, while
their border and label colors follow the fixed component and slot palettes.
The original rendered output remains in source order inside the wrapper.

### 3.2 Root identity stays on authored elements

Debug wrappers are inserted after Citry marks component roots. Attributes such
as `data-cid-*`, `data-cid`, `data-citry-key`, and component CSS-variable
markers therefore stay on the elements authored by the component:

```html
<div class="citry-debug citry-debug-component">
  <section data-cid-c1="">...</section>
</div>
```

The wrapper itself is not a component root. This preserves the elements seen
by `$component(...).els`, Events, keyed morphing, dependency cleanup, and the
ownership manifest.

### 3.3 Errors, transparent components, and documents

Debug does not change error handling. When `on_component_rendered` receives an
error or no render, it returns `None`, so the error continues through the
normal pipeline.

Transparent components and their slots do not receive boundaries. Their
explicit contract is that they add no markup of their own, and a visual wrapper
would change that behavior. This includes structural built-ins such as
`<c-provide>`, dynamic dispatch wrappers, and the JS/CSS placeholder
components.

A component or slot boundary is also omitted when its final region begins with
an optional UTF-8 byte-order mark followed by `<!doctype>` or `<html>`.
Wrapping a full document in a `<div>` would invalidate the document. Omitting
the inner slot boundary also lets an enclosing component recognize that its
whole output is a document. Descendant components and ordinary slots inside
the document remain highlighted.

### 3.4 Development-only DOM changes

Debug boundaries are real wrapper elements. They can affect flex and grid
children, direct-child selectors, exact element identity, and HTML contexts
with restricted children such as tables and selects. No single bordered HTML
element is valid around every possible fragment.

The extension is therefore for development inspection, not production output
or layout-sensitive behavioral verification. The future debug-toolbar panel
can provide non-wrapping inspection through the separate
[`component tracing`](component_tracing.md) design.

## 4. Serialize-time boundary insertion

[`Placeholder`](../../packages/py/citry/citry/citry_render.py) already
represents a position whose final HTML is supplied during serialization. Debug
uses a paired placeholder around each enabled result:

```python
CitryRender(
    parts=[Placeholder(open_key), original_result, Placeholder(close_key)],
    context=result_context,
)
```

For an existing `CitryRender`, the interior wrapper reuses its context. This
keeps nested dependency and ownership metadata attached to the rendered
subtree. A string slot result uses a component-less interior `CitryContext`;
the slot's physical ownership wrapper remains authoritative.

Placeholder keys carry encoded string-only boundary metadata: the boundary
kind, a render-tree-unique pairing token, and the label input. A component
boundary's token includes its render ID; a slot boundary's token includes its
receiving component's render ID and that slot occurrence's counter. Every
variable field uses lowercase hexadecimal UTF-8 bytes, so the key contains no
quote, angle bracket, equals sign, or whitespace when the serializer places it
in the `c-render-id` attribute. The serializer appends a random private
identity on every serialization, so an authored `c-render-id` lookalike cannot
be mistaken for a generated placeholder during replacement or cleanup. The
decoded label is HTML-escaped when the final wrapper is built. The extension
does not keep a side table keyed by components or render IDs, so it retains no
component class, component instance, or rendered tree after a render finishes.

Component root marking occurs before every serialize hook. The dependencies
extension's serialize hook runs before `Debug.on_serialize` because built-ins
are prepended to the extension list. Events has already contributed its
render-time root markers by this point. Debug then uses the serializer's exact
placeholder texts to:

1. pair each opening and closing boundary;
2. process nested boundaries without changing their order;
3. omit full-document component and slot boundaries;
4. replace complete pairs with the final wrapper HTML;
5. remove a surviving half when an earlier extension discarded the other
   half.

The same `CitryRender` may be serialized more than once. Replacement operates
on each serialization's HTML string and does not mutate the render object.
All dependency strategies (`ignore`, `simple`, `document`, and `fragment`)
use the same boundary replacement.

### 4.1 Embedded renders from another Citry instance

A pre-rendered `CitryRender` may be embedded in output owned by another
`Citry` instance when the render does not require a client ownership manifest.
Only the root component's extension manager receives `on_serialize`.

Debug placeholder keys therefore use one stable format understood by every
`Debug` instance. When the root instance also installs Debug, its serialize
hook resolves boundaries contributed by the embedded render. When the root
instance does not install Debug, the embedded content remains and its visual
boundaries are omitted.

After all serialize hooks run, the core Python serializer removes every exact
placeholder occurrence that remains unresolved. This is the fallback already
defined by `Placeholder`: a position that no extension fills serializes to an
empty string. It also makes extension handoff safe generally, including a root
render with no component and therefore no extension manager.

## 5. Extension ordering

Render replacements are threaded in configured extension order. Applications
should place `Debug` after extensions whose final component or slot output they
want to inspect:

```python
app = Citry(extensions=[MyOutputExtension, Debug])
```

An extension that runs after `Debug` may deliberately replace output and drop
the Debug placeholders. Serialization removes any unmatched half rather than
emitting malformed wrapper HTML.

Root marking is complete before `on_serialize`, and the built-in dependencies
extension runs its serialize hook before user extensions. Debug therefore sees
the marked component roots and the dependency extension's final HTML.

## 6. Implementation record

### Round 1: extension and configuration

- Added `packages/py/citry/citry/ext/debug.py` with the public `Debug` class,
  `Debug.Config`, strict field validation, fixed palettes, label formatting,
  and boundary helpers.
- Exported the `debug` module from `citry.ext` while keeping `Debug` out of the
  core `citry` namespace.
- Kept `_builtin_extensions()` unchanged.

### Round 2: render and serialization hooks

- Implemented `on_component_rendered`, including error, transparent-component,
  and configuration handling.
- Implemented `on_slot_rendered` for string and `CitryRender` results, including
  transparent receivers and repeated slot occurrences.
- Implemented paired `Placeholder` replacement in `on_serialize` with escaping,
  nesting, full-document detection, unmatched-half cleanup, and
  repeated-serialization safety.
- Made the core Python serializer remove exact unresolved placeholder
  occurrences after all serialize hooks, fulfilling `Placeholder`'s empty
  fallback contract for roots with and without an extension manager.
- Stored only encoded strings and slot counters scoped to one component config
  instance. Included the component render ID in every pairing token so tokens
  remain unique across instances. Added no extension-owned component or class
  cache.

### Round 3: focused and integration tests

`packages/py/citry/tests/test_ext_debug.py` and
`packages/py/citry/tests/e2e/test_ext_debug_e2e.py` cover:

- opt-in behavior and default-off output;
- factory, engine-wide, and component-level precedence;
- unknown fields and non-boolean values;
- nested, repeated, multi-root, text-only, and empty component output;
- passed fills, fallback slots, repeated slots, string results, and nested
  components inside slots;
- combined component and slot highlighting;
- transparent components and full-document output;
- escaped labels, failed renders, extension ordering, and unmatched pairs;
- repeated serialization and all four dependency strategies;
- pre-rendered cross-`Citry` embedding when the root instance installs Debug
  and when it does not;
- unresolved placeholder cleanup on a component root and a component-less
  root;
- authored-root `data-cid`, Events, key, CSS-variable, dependency, and
  ownership-manifest behavior;
- browser proof that `$component(...).els` still contains the authored roots;
- component-class collection after final unregister, proving that Debug adds
  no lifetime retention.

All seven methods in the vendored django-components highlight file are
accounted for individually in
[`migration_djc_tests.md`](migration_djc_tests.md#test_component_highlightpy-7-tests):
three are ported, two direct-helper tests are replaced by assertions through
the public extension, and two legacy core-setting tests are dropped. The Citry
suite also adds serializer, ownership, dependency, browser, and lifetime cases.

### Round 4: documentation and status records

- Added installation, component-level configuration, colors, and the
  development-only warning to
  `docs_site/content/guides/troubleshooting.md`.
- Added the bundled opt-in extension to
  `docs_site/content/advanced/extensions.md` and API-reference routing.
- Updated `extensions_roadmap.md`, `migration_djc.md`,
  `migration_djc_tests.md`, and the docs-site content audit for the landed
  feature.
- Added a user-facing `CHANGELOG.md` entry for the new public extension.

### Round 5: verification

Focused Python, browser, docs, lint, and type checks passed during
implementation. The full repository gate also passed:

```text
python scripts/check.py --reporter agent
```

## 7. Boundaries

This work is Python-side. It adds the generic unresolved-placeholder cleanup to
the Python serializer but introduces no core lifecycle hook. It requires no
changes to the Rust parser, grammar, AST, compiler, host-language
implementations, PyO3 bindings, or `citry_core` type stubs. The existing
component-rendered, slot-rendered, and serialize hooks provide the extension
behavior.
