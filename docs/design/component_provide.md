# Design: provide / inject and the `<c-provide>` component

**Status (2026-07-24): server and client contracts implemented.** The
`CitryContext.provides` plumbing, the hand-over at component and slot
boundaries, `Component.provide()`/`inject()`, the `<c-provide>` built-in with
the `transparent` flag, `Component.unprovide()` compound-scope boundaries,
lazy per-instance built-in registration, and the reserved-name guard. Tests in
[`tests/test_provide.py`](../../packages/py/citry/tests/test_provide.py).
Section 10 specifies the corresponding Alpine client API and graph routing.

This document specifies how a component passes data to components rendered
deep below it, without threading the data through every kwarg in between:
the provide/inject feature (React's `ContextProvider`, Vue's
`provide()`/`inject()`). It covers how the data travels, the
`Component.provide()` / `Component.inject()` APIs, the `<c-provide>` built-in
component, and how the data reaches slot content.

The server and client channels intentionally share descendant-only lookup,
nearest-provider replacement, slot-site visibility, and explicit blocking.
They do not share values automatically. The client model is summarized and
cross-linked from
[`alpinejs.md`](alpinejs.md#47-client-ambient-context).

It extends [`component_rendering.md`](component_rendering.md) (the three-phase pipeline and
`CitryContext`), [`component_rendering_defer.md`](component_rendering_defer.md) (children
render after their parents, which forces the snapshot rule in section 4.2
here), and [`component_slots.md`](component_slots.md) (whose section 6 defers provide/inject to
this design). Operating rules are in [`/CLAUDE.md`](../../CLAUDE.md).

Upstream references: the django-components implementation studied for this
design is [`_djc_reference/provide.py`](../../packages/py/citry/_djc_reference/provide.py)
(`ProvideNode`, `set_provided_context_var`, `get_injected_context_var`),
[`_djc_reference/perfutil/provide.py`](../../packages/py/citry/_djc_reference/perfutil/provide.py)
(the cache and reference-counting machinery), and
[`_djc_reference/context.py`](../../packages/py/citry/_djc_reference/context.py)
(the `_DJC_INJECT__` key pass-through). The behavioral contract is pinned by
the upstream DJC suite
[`test_templatetags_provide.py`](https://github.com/django-components/django-components/blob/5d4d4f5d13dd06c80ba389f30fc63fdbb71cda75/tests/test_templatetags_provide.py),
including the slot tests from django-components PRs #778 and #786.

---

## 1. Prior art

What already exists, verified on 2026-06-10:

- **The parser deliberately does not reserve `<c-provide>`.**
  [`constants.rs`](../../crates/citry_template_parser/src/constants.rs) notes
  (lines 19, 182, 196) that `c-provide`, `c-js`, and `c-css` do not influence
  the grammar and "can be implemented as regular user-side components". A
  `<c-provide>` tag therefore compiles to an ordinary
  `ComponentNode(name="provide")` today. **No grammar, AST, compiler,
  `LangImpl`, or PyO3 change is needed**; the whole feature is Python in
  `packages/py/citry/`.
- **The README pins the syntax** (line 74): the provider-name attribute is
  **`key`**, and every other attribute is the provided data:
  `<c-provide key="theme" mode="dark">...</c-provide>`.
- **[`migration_djc.md`](migration_djc.md)** plans `<c-provide>` as a
  built-in component in `citry/components/provide.py` (sections "Built-in
  components" and "Step 4").
- **The runtime pieces are in place**: `CitryContext`
  (variables/extra/component), the render queue where a child's inputs are
  read while the parent renders but the child itself renders later
  (`ComponentNode.render` -> `DeferredComponent` -> `_render_one`), the slot
  subsystem (`Slot`, `SlotContext`, `SlotNode`, fill collection), and
  `Component.parent`/`root` links. Nothing provide-related existed before
  this work;
  [`components/__init__.py`](../../packages/py/citry/citry/components/__init__.py)
  was empty.

---

## 2. The model in one paragraph

A component makes data available with `self.provide("user_data", user=user)`
(or a template wraps content in `<c-provide key="user_data" c-user="user">`),
and anything rendered inside that point can read it with
`self.inject("user_data")`. Content written elsewhere (`CitryElement`) that ends up
rendering inside the provider (as `CitryRender`) can inject too (section 3). The data travels on
`CitryContext.provides`, a small mapping that each render hands to the next:
a component hands it to its children, and a `<c-slot>` hands it into the slot
content it renders. The data never enters the template variables; components
opt in with `inject`. When two providers use the same key, the closer one
wins, and its payload replaces the outer one entirely (no field merging).

## 3. Who can inject the data: follow the rendered page, not the template files

Slot content is written in one place and rendered in another. That splits
"what surrounds this content?" into two possible answers, and provide/inject
has to pick one:

- the place the content is **written**: the parent's template, where the
  `<c-fill>` or component body sits;
- the place the content is **rendered**: the `<c-slot>` site inside the
  receiving component.

For template *variables*, citry picks "written": a fill renders with the
variables of the template that wrote it ([`component_slots.md`](component_slots.md) section 2).
For provide/inject, citry picks **rendered**. This example (the shape of the
DJC tests from PRs #778/#786) shows why:

```html
<!-- Provider's template: provides around its slot -->
<c-provide key="theme" mode="dark">
  <c-slot />
</c-provide>

<!-- Page's template: passes content into Provider -->
<c-provider>
  <c-themed-button />
</c-provider>
```

The button is written in Page's template, where no `theme` is provided. But
it ends up rendering inside Provider's `<c-provide>` block, and "the button
asks for the theme it is rendered under" is the entire point of the pattern.
So `inject` must see what is provided around the place the content lands,
not only around the place it was written.

Choosing "rendered" keeps the provider state from the "written" side unless a
component explicitly establishes a compound-scope boundary with
`unprovide()`. Normally, the content was picked up at the component call
(`<c-provider>` above), the receiving component inherits everything provided
around that call, and on the way to its `<c-slot>` it can only provide more.
So rendering slot content with the provides of the slot site keeps everything
that was provided where the content was written, plus whatever the receiving
component added. A deliberate block makes one key appear missing below that
component until a nearer provider restores it. When both provide the same key,
the rule from section 2 already answers it: the closer provider wins.

One more option that cannot work: walking up `Component.parent`. Those links
follow where content was *written* (a component inside slot content gets the
component that wrote it as its parent, see [`component_slots.md`](component_slots.md)), so
Provider above would never be on the button's parent chain.

## 4. How the data travels

### 4.1 `CitryContext.provides`

`CitryContext` gets a `provides` field next to `variables`/`extra`: a mapping
from key to frozen payload, plus private blocked markers that `inject()` treats
as absent. It is treated as read-only. A component that provides or blocks
builds a **new** mapping with its changes instead of changing the one it
received, so everyone already holding the old mapping is unaffected, and
handing the mapping around is just sharing a reference (no copies).
Every place that builds a derived context passes it along:
`ForNode.iter_bodies`, `_make_body_slot`, and `_render_one`.

### 4.2 From parent to child component

A child component renders *after* its parent has finished, through the
render queue, when the parent's context is already gone. So, exactly like
kwargs ([`component_rendering_defer.md`](component_rendering_defer.md) section 4.2), the
provides are read while the parent is still rendering: `ComponentNode.render`
stores the current `context.provides` on the `DeferredComponent` (a shared
reference, nothing is copied). When the queue renders the child, the child
instance keeps that mapping (this is what `inject` reads), and the child's
own context starts from it plus whatever the child itself provides in
`template_data`. A root render (`CitryElement.render()`) starts with nothing
provided.

### 4.3 From a `<c-slot>` into the slot content

When `<c-slot>` renders a fill, it passes its current provides into the
call: `slot(data, fallback=..., provides=...)`. `Slot.__call__` exposes them
on `SlotContext.provides` (`None` when the Slot is called directly, outside
any render, e.g. `str(slot)`). A template fill's body then renders with the
slot site's provides laid over the ones captured when the fill was collected;
per section 3 the slot site's entries win on a clash. Called with no slot
site, the body just keeps the captured ones. The slot's fallback body needs
no special handling: it renders against the context current at the slot
site, which already carries the right provides.

### 4.4 Elements rendered in the middle of a render

A `CitryElement` that gets rendered *during* another render inherits the
provides active at that point: `_render_value` passes them to `render_impl`.
This covers `{{ element }}` expressions (via `ExprNode`) and Python-supplied
slot content (a `Slot` wrapping an element, or a slot function returning
one), so `Provide(key="x", ..., slots={"default": Injectee()})` works. Only a
plain user call to `.render()` starts with nothing provided.

## 5. The Python API

### 5.1 `Component.provide(key, /, **data)`

Makes `data` available to this component's descendants. Call it from
`template_data` (or any hook that runs before the render context is built in
`_render_one`). `key` must be a non-empty string identifier (error
otherwise, matching DJC). `key` is positional-only, so a data field literally
named `key` can be provided. The data is frozen right away into a
`NamedTuple` named `Provided`: it cannot be changed afterwards, its fields
are read as attributes (`inject("user_data").user`), and every provided
field is always present. This is DJC's `DepInject` contract under a citry
name.

### 5.2 `Component.inject(key, default=MISSING)`

Returns the payload from the nearest provider above this component in the
rendered page, the given `default` when the key was never provided, or
raises `KeyError` (with the DJC-style explanation plus a difflib "did you
mean" hint over the available keys). Uses a `MISSING` sentinel rather than
DJC's `default=None` convention, so `inject(key, None)` can genuinely
default to `None` (a deliberate, strictly-wider divergence). `inject` sees
only what was provided *above* the component, never the component's own
`provide()` calls, and keeps working after the render finishes for as long
as the component instance is kept (the data sits on a plain attribute).

### 5.3 `Component.unprovide(key, /)`

Hides one inherited provide from this component's descendants. The current
component can still inject the inherited payload because its own outgoing
provide changes are never visible to itself. A nearer descendant can restore
the key normally with `provide()`.

Call this from `template_data` when a compound child ends the current ambient
scope. For example, a Tab blocks its Tabs context before rendering user
content. A nested Tab then fails until the user inserts a new Tabs root, whose
`provide()` replaces the internal blocked marker.

An empty payload cannot represent a block because `provide(key)` with no data
is deliberately injectable. The runtime therefore stores a private `BLOCKED`
marker in the outgoing provides mapping. `inject()` treats that marker exactly
like an absent key, including default handling and close-name suggestions.

### 5.4 Scoping rules (the DJC contract plus explicit boundaries)

- Provided data is **not** added to template variables; components opt in
  via `inject`. (`test_provide_does_not_expose_kwargs_to_context`)
- An inner provide under the same key **replaces the outer payload
  entirely**; fields of the outer payload do not merge in.
  (`test_provide_nested_in_provide_same_key`)
- Different keys are independent and compose.
- Siblings after the provider's closing tag do not see the data.
  (`test_provide_does_not_leak`)
- Providing with no data fields yields an empty payload, which is still
  injectable. (`test_provide_empty`)
- A blocked key appears missing below the blocking component until a nearer
  provider restores it.

## 6. The `<c-provide>` built-in component

A regular component in
[`components/provide.py`](../../packages/py/citry/citry/components/provide.py),
essentially:

```python
class Provide(Component):
    transparent = True
    template = "<c-slot />"

    def template_data(self, kwargs, slots):
        data = dict(kwargs)
        key = data.pop("key", None)   # missing/invalid key raises
        self.provide(key, **data)
        return {}
```

Everything else comes from existing machinery: static `key="theme"`, dynamic
`c-key="expr"`, `c-bind` spread (with `key` inside the mapping), data
attributes read against the live parent scope, self-closing
`<c-provide ... />` rendering empty, nesting, and per-iteration provides
inside `<c-for>`. The component declares no `Kwargs`/`Slots` classes, so the
parse-time tag rules correctly allow arbitrary data attributes and the
default fill. Its body reaches descendants through the slot hand-over
(section 4.3): the body is the default fill, rendered at the `<c-slot />`
site inside the component's own context, which carries the provided data.

### 6.1 Transparent components (no `data-cid` frame)

`<c-provide>` only wraps content: it owns no markup, no JS, no CSS. A new
class flag, `Component.transparent = False` by default, makes a component's
output count as part of the surrounding component for serialization: its
render is produced with `is_component_root=False`, so the serializer
([`serialize.py`](../../packages/py/citry/citry/serialize.py)) neither treats
it as a child component frame nor stamps a `data-cid-<id>` marker on its
content (the root-marker site also checks `is_component_root`, so a
transparent component serialized directly as the root is unmarked too). The
instance still gets a render id, hooks still fire, and dependency merging is
unchanged.

### 6.2 Per-instance registration and reserved names

A `Component` subclass binds to one `Citry` instance when the class is
defined, but the built-in must exist in every instance. Registering it
eagerly inside `Citry.__init__` cannot work for the default instance: that
instance is constructed while `citry/citry.py` is still importing, before
`component.py` can be imported at all. So built-ins are created **lazily** by
the private component registration state. On the engine's first component
lookup (`get`/`has`/`components`) it calls
`Citry._create_builtin_components`, whose function-local import is justified by
this concrete cycle, and creates the subclasses bound to that instance.
`clear()` resets the flag so a cleared engine re-creates them.

The names `provide`, `js`, and `css` are **reserved**
(`BUILTIN_COMPONENT_NAMES` in `component_registry.py`):
`Citry.register` rejects a user registration that would claim one of them (the
README promises all three as built-in tags), raising
`AlreadyRegistered` with a message naming the built-in. Without the guard, a
user class registered before the first lookup would silently take the
built-in's place.

## 7. What does NOT port from django-components

Each piece compensates for DJC machinery citry does not have:

- The entire [`perfutil/provide.py`](../../packages/py/citry/_djc_reference/perfutil/provide.py):
  `provide_cache`, `provide_references`, `component_provides`,
  `active_provides`, `managed_provide_cache`, the GC finalizers and all
  reference counting. DJC stores payloads in module-level globals (so its
  flat `Context` stays inspectable) and then has to track by hand when each
  entry can be deleted; citry keeps plain references on contexts and
  instances and lets Python's garbage collection do the work. The DJC tests'
  `_assert_clear_cache` assertions have no citry analog because there is no
  cache to leak.
- The `_DJC_INJECT__` context-key indirection and
  `make_isolated_context_copy`'s provide pass-through (citry has no context
  modes; the slot hand-over in 4.3 is the principled replacement).
- `ProvideNode`/`BaseNode` tag plumbing (the component IS the tag).
- The `var1:key=...` aggregate-dict kwarg syntax (a DJC expression-language
  feature; citry has `c-bind` and real dict expressions).
- `TemplateSyntaxError` types; citry raises its established
  `RuntimeError`/`KeyError`/`ValueError` styles.

Bonus: the three DJC tests skipped upstream over global-state cleanup
(provide inside forloops, django-components #1413) work in citry and are
ported as active tests.

## 8. Alternatives considered

- **Pass provides down the `Component.parent` chain.** Rejected: those links
  follow where content was written, so the provider in the section 3 example
  is never on the injecting component's chain.
- **Give slot content only the provides captured where it was written (no
  hand-over at the slot).** Rejected: breaks the section 3 example, which is
  the feature's main use, and the `<c-provide>` component could then never
  reach its own body (the body is slot content).
- **Store provides in `CitryContext.extra`.** Rejected: `extra` flows *up*
  (a child's entries are merged into its parent when the child finishes);
  provides flow only *down* and must never travel upward. One bag carrying
  both directions invites exactly the kind of leak the `extra` merge rules
  exist to prevent.
- **`<c-provide>` as a parser built-in / runtime node.** Rejected: the parser
  decision (prior art) is that it does not influence the grammar, and a node
  would need its own scope machinery that the component boundary already
  provides. The component approach also gives the Python-side
  `Component.provide()` API for free.
- **A plain mutable dict payload instead of a NamedTuple.** Rejected: DJC
  chose the NamedTuple so the injected object cannot be changed and always
  has all provided fields; both properties are part of the ported test
  contract (attribute access, `payload.field`).
- **Eager built-in registration in `Citry.__init__`.** Rejected for the
  import cycle described in 6.2.

What would falsify the section 3 choice: a real need for slot content that
must NOT see what is provided around the slot it renders in. Both DJC's
tests and the React/Vue context model treat that visibility as the feature
itself, so this is considered settled.

## 9. Phasing and test plan

1. **Core plumbing**: `CitryContext.provides` plus passing it through every
   derived-context construction site; `DeferredComponent.provides`; the
   `ComponentNode.render` snapshot; `_create_instance`/`__init__`;
   `citry/provide.py` (the `Provided` payload builder, the `MISSING`
   sentinel, key validation); `Component.provide()`/`inject()`.
2. **Slot hand-over**: the `Slot.__call__` provides argument,
   `SlotContext.provides`, the `_make_body_slot` overlay, `SlotNode`
   pass-through, and the `_render_value`/`render_impl` threading for
   elements rendered mid-render.
3. **The built-in**: `components/provide.py`, the `transparent` flag, lazy
   per-instance registration, and the reserved-name guard.
4. **Docs**: this document, the [`component_slots.md`](component_slots.md) section 6/12
   cross-references, README examples verified.

Tests (in `tests/test_provide.py`), ported from the DJC suite plus
citry-specific cases: basic provide+inject through the template and through
Python attribute access; payload immutability and full-field presence;
self-closing provide; scoping (sibling after close, no variable leak,
nested same-key replacement, nested different keys); dynamic `c-key`,
`c-bind` spread; missing/empty/non-identifier key errors; `inject` default
(including explicit `None`), missing-key `KeyError` with the did-you-mean
hint, inject-after-render with a kept instance; provide inside `<c-for>`
with per-iteration values; the slot trio (slot-in-provide, inject-in-fill,
inject-in-slot-in-fill); provides reaching Python-channel slot content and
`{{ element }}` expressions; deep nesting through the render queue;
transparent serialization (no `data-cid` for the provide, correct marker
stacking through it, transparent-as-root); the reserved-name guard; and the
README example verbatim.

## 10. Client provide, inject, and unprovide design

**Status: implemented on 2026-07-24.**
This section owns the public semantics. The client ownership architecture,
integration points, and abbreviated examples also appear in
[`alpinejs.md`](alpinejs.md#47-client-ambient-context). The two documents must
be changed together if this contract changes.

### 10.1 Decision

Citry should expose the same three operations through both client authoring
surfaces:

```js
$component(({ provide, inject, unprovide }) => {
  // Component-wide setup.
});
```

```html
<section x-init="$provide('theme', theme)">
  <span x-text="$inject('theme').name"></span>

  <div x-init="$unprovide('theme')">
    <!-- Descendants no longer see the outer theme. -->
  </div>
</section>
```

The public signatures are:

```ts
declare const contextValueType: unique symbol;
type InjectionKey<T> = symbol & { readonly [contextValueType]?: T };
type ContextKey<T = unknown> = string | InjectionKey<T>;

provide<T>(key: ContextKey<T>, value: T): void;
inject<T = unknown>(key: ContextKey<T>): T;
inject<T = unknown, D = unknown>(key: ContextKey<T>, defaultValue: D): T | D;
unprovide(key: ContextKey): void;
```

This is the intended TypeScript contract, following Vue's phantom generic
symbol pattern. The current browser runtime is shipped inside the Python
package and does not yet publish a JavaScript declaration package, so
`InjectionKey<T>` is not currently an importable public type. Runtime keys are
ordinary JavaScript strings and symbols. A future published client package
should export this declaration unchanged.

The Alpine spellings are `$provide`, `$inject`, and `$unprovide`. The
`$component` context spellings omit `$`, like its existing `effect`,
`reactive`, `sendEvent`, and `onEvent` helpers. Both surfaces call the same
ambient-context service. They are not parallel implementations.

The Python and JavaScript forms differ only where each language is most
ergonomic. Python's `<c-provide key="x" arg1="..." arg2="...">` tag passes
fields one by one, so `provide(key, arg1=value1, arg2=value2)` mirrors the tag
and reads more naturally than an explicit dictionary. JavaScript has native
object literals, reactive objects, functions, and primitives, so
`provide(key, value)` is the natural spelling there. Citry stores and returns
the exact JavaScript value without wrapping, cloning, freezing, merging, or
unwrapping it.

### 10.2 Prior art and what Citry should retain

The archived AlpinUI/Vuetify work contains
`alpine-provide-inject` 0.3.0. Its complete runtime is small:

- `$provide(key, value)` stores a value in an ad hoc `_provides` object on the
  current element;
- `$inject(key, defaultValue)` starts at `el.parentElement`, walks physical
  ancestors, and returns the first matching value;
- injection deliberately excludes the current element;
- the composition adapter forwards its `provide()` and `inject()` helpers to
  those magics;
- component code provides symbols and reactive refs or computed values, then
  injects them through Vuetify-style composables;
- a private `injectSelf()` helper reads the current instance's own provide
  object for one defaults-composition case.

Citry should retain the familiar callable names, ancestor-only lookup,
nearest-provider behavior, `string | symbol` keys, exact value identity, and
the component-setup forwarding pattern. Those choices worked well and match
Vue's component-authoring model.

Citry should not copy the old storage or traversal:

- `parentElement` expresses physical DOM ancestry, not Citry's rendered
  component and slot ancestry;
- an element property cannot represent a rootless component or one logical
  component with several roots;
- raw DOM walking loses the authored route under `x-teleport`, source-linked
  fills, shared physical roots, and mirrored placements;
- a plain object coerces numeric keys and makes the old TypeScript acceptance
  of numeric provide keys disagree with its inject signature;
- checking `defaultValue !== undefined` cannot distinguish an omitted default
  from an explicit `undefined` default;
- the old plugin has no `unprovide`, graph-revision ownership, morph
  transaction, or tests.

Alpine 3.15.12 does make the magic surface feasible. `Alpine.magic()` receives
the expression element, and its current implementation supplies memoized
element-bound utilities with cleanup tied to removal. Alpine's teleport
implementation also preserves a backlink to the authored template scope.
Those mechanisms are inputs to a Citry adapter, not permission to make DOM
ancestry authoritative. The cleanup utility passed to magic callbacks is
observed in pinned Alpine source but is not fully described by Alpine's public
magic documentation, so its use requires the private-API adapter and canaries
already required by [`alpinejs.md`](alpinejs.md#62-private-apis).

The primary upstream references are:

- [Alpine extension and magic documentation](https://alpinejs.dev/advanced/extending);
- [Alpine 3.15.12 magic source](https://github.com/alpinejs/alpine/blob/v3.15.12/packages/alpinejs/src/magics.js);
- [Alpine 3.15.12 scope source](https://github.com/alpinejs/alpine/blob/v3.15.12/packages/alpinejs/src/scope.js);
- [Alpine teleport documentation](https://alpinejs.dev/directives/teleport);
- [Alpine 3.15.12 teleport source](https://github.com/alpinejs/alpine/blob/v3.15.12/packages/alpinejs/src/directives/x-teleport.js);
- [Vue provide/inject documentation](https://vuejs.org/guide/components/provide-inject);
- [Vue runtime provide/inject source](https://github.com/vuejs/core/blob/v3.5.18/packages/runtime-core/src/apiInject.ts).

### 10.3 Core semantics

Client ambient context follows these rules:

1. A provide is visible below the component or HTML element where it was
   established. For supplied slot content, lookup follows the component's
   rendered `<c-slot>` position, while ordinary Alpine variables in the fill
   still come from the caller that authored the fill.
2. An inject never sees a provide or block established by the same context
   owner. An element owner starts at its incoming parent route. A shared hook
   owner starts independently at every live occurrence's incoming parent,
   then applies the consensus rule in section 10.4.
3. The nearest provided value for a key wins. Values are replaced as a whole;
   Citry never merges them.
4. Different keys compose independently.
5. An unprovide entry stops lookup for its key and makes the key appear missing
   below that point. A nearer descendant provide restores the key.
6. A provided `undefined` is present. `null` and every other JavaScript value
   are also valid.
7. A missing key with no default throws a context-rich error. An explicitly
   supplied default is returned, including an explicit `undefined`. The
   implementation must test `arguments.length`, not the default's value.
8. A key is either a non-empty string or a symbol. Numbers are rejected rather
   than silently coerced to strings.
9. `provide` and `unprovide` are synchronous initialization operations.
   `$component` callers use them in `init`; template callers normally use
   them in `x-init`. Calling either after the owning initialization window has
   closed throws. `inject` may be called later while its owner route remains
   live.
10. When one owner writes the same key more than once during initialization,
    the last call wins. A later `provide` replaces a block, and a later
    `unprovide` replaces a value.

The initialization restriction is intentional. Changing context topology
from a click handler or effect after descendants have initialized would make
setup-time injections order-dependent and would require implicit descendant
reinitialization. Dynamic data should instead be carried in one stable
reactive value that is provided during initialization.

Application code cannot change provider registration after initialization. If
a component provides an Alpine-reactive object, descendants receive that same
object and react normally when its properties change. Citry does invalidate a
live Alpine expression containing `$inject` when a provider declaration is
installed, replaced, or removed by runtime lifecycle work such as a morph;
the expression then resolves the current nearest value. This does not mutate
or wrap the value, and it does not retroactively change a value that component
setup captured in a plain variable. This matches the useful part of the
AlpinUI/Vue pattern: provide a stable reactive reference, and keep mutation
operations with the provider when practical.

`injectSelf` is not public API. A provider already has the value it provided.
A composition helper that needs both the inherited and replacement values
injects first, computes the new value, and then provides it. Because own
writes are invisible to own injection, source order does not change the
result.

### 10.4 Component hooks and template magics

The `$component` methods cover every root rendered by that component:

```js
const TabsKey = Symbol.for("citry-ui:tabs");

$component(({ reactive, provide }) => {
  const tabs = reactive({ active: null, items: [] });

  provide(TabsKey, tabs);
});
```

They work for single-root, multi-root, text-only, and empty components. A
component-wide provide is shared by the logical lifecycle and applies beneath
every live placement owned by that lifecycle.

The magic methods cover the browser HTML descendants of their expression
element. Supplied slot content is the exception to a plain `parentElement`
walk: it uses the receiver's rendered `<c-slot>` position, as section 10.5
defines.

```html
<section x-init="$provide('theme', theme)">
  <c-card />
</section>

<aside>
  <!-- This sibling is outside the provider. -->
</aside>
```

On a single element root, calling `provide()` in the hook has the same
descendant effect as calling `$provide()` in `x-init` on that root. On a
multi-root component, the hook is equivalent in coverage to placing the
magic on every root. The hook remains preferable for component-wide library
state because it runs once per logical callback invocation and also works
without any element root. The magic is preferable for a deliberately narrow
subtree.

The two forms differ in physical-copy ownership. A `$component` provide is
shared under Citry's logical mirror policy. A magic called in a mirrored or
structurally cloned element is placement-local, just like ordinary Alpine
`x-data` and directive cleanup. Each copy's descendants resolve through that
copy's ambient frame.

A shared component frame therefore has one occurrence per live placement.
All occurrences refer to the same provided value or blocked marker, but each
occurrence has its own incoming rendered route. This lets descendants at two
slot outlets see the shared component provide while preserving the different
outer providers at those outlets.

Hook `inject()` is singular even when its logical lifecycle has several
placements. Citry resolves the requested key independently at every live
occurrence. It returns a value only when every occurrence has the same lookup
outcome under `Object.is`. All occurrences being missing is one matching
outcome, after which the explicit default or missing-key error is applied.
Found `undefined` remains different from missing. If outcomes disagree, Citry
throws an ambiguous-context error that identifies the conflicting placements.
The author must move that lookup into a placement-local magic, arrange
equivalent outer context, or stop sharing that logical lifecycle. Citry must
not select the first physical placement as a hidden canonical route.

Hook initialization has to settle in ancestor order. A parent's synchronous
`provide()` or `unprovide()` calls are committed before a descendant hook may
call `inject()`. On a compatible render revision, old hook registrations are
removed and new registrations are installed as part of the same graph and DOM
adoption transaction. No descendant may observe the temporary gap. If hook
initialization fails, its ambient writes roll back before the branch is
retired or diagnosed.

The helpers handed to one hook invocation are bound to that invocation's live
occurrence set, including each occurrence's current incoming route. Captured
helpers fail as stale after invocation cleanup rather than silently resolving
through a replacement component revision.

Mixed hook and template initialization has the same guarantee. An ancestor
element's synchronous `$provide()` or `$unprovide()` call settles before a
descendant component hook runs, and an ancestor component hook settles before
a descendant element evaluates `$inject()`. The rule applies to initial
documents, inserted fragments, structural copies, teleport origins, and
reused compatible nodes. It also applies when Alpine's object-form `x-bind`
creates the provider directive. A provider call after the first asynchronous
pause is outside the synchronous initialization window and fails.

### 10.5 Slots require two different routes

A supplied fill already has two relevant locations:

- its lexical source, where its Alpine expressions were authored;
- its rendered site, where the receiver's `<c-slot>` places it.

Ambient context follows the rendered route, just like the server contract in
sections 3 and 4. Alpine variables, refs, IDs, and ordinary expression lookup
continue to follow the lexical source rules in
[`alpinejs.md`](alpinejs.md#65-fill-source-projection). These truths must not
be collapsed into one parent pointer.

For example:

```html
<!-- Receiver template -->
<section x-init="$provide('theme', receiverTheme)">
  <c-slot />
</section>

<!-- Caller template -->
<c-receiver>
  <button x-text="$inject('theme').buttonLabel"></button>
</c-receiver>
```

`receiverTheme` is evaluated in the receiver's Alpine scope. The button's
`x-text` expression is evaluated in the caller's lexical Alpine scope, but
its `$inject('theme')` lookup follows the rendered slot route and sees the
receiver's provided value.

The complete slot rules mirror the server:

- a supplied fill retains the caller-side ambient route captured at its
  invocation source;
- the route active at the rendered slot site is laid over that captured
  route;
- a slot-site provider or block wins when both routes contain the same key;
- fallback content uses the receiver's current rendered route directly;
- detached slot content has its ordinary empty lexical base but still receives
  ambient context from the rendered slot site;
- `$provide` or `$unprovide` authored inside a fill uses the caller's lexical
  scope to evaluate its arguments, then affects descendants at that fill's
  rendered position.

This route overlay is graph data, not a snapshot of JavaScript values in the
server manifest. The manifest records how runtime context positions relate;
all client values remain in browser memory.

### 10.6 The ambient-context graph

The old plugin's element walk must be replaced by a small graph overlay on
the landed ownership registry. The conceptual model is:

```text
rendered call-site route
        |
        v
component ambient frame       <- hook provide/unprovide
        |
        v
template element frame        <- magic provide/unprovide
        |
        v
child component or slot site
```

An ambient frame contains an owner token, one or more placement occurrences,
and a map from context keys to either a provided value or a private blocked
marker. Each occurrence has a route to its next outer frame. Lookup walks one
occurrence's route nearest to farthest and stops on the first value or block.
The exact storage may use persistent linked frames or an equivalent indexed
route; this design does not pin the internal representation.

There are two kinds of owners:

- a logical component callback invocation, represented even when `els` is
  empty;
- an Alpine expression element and physical placement, created lazily when a
  magic registers a value or block.

The ownership graph must expose a rendered ambient parent independently from
the existing lexical source and `Component.parent` relations. At component
invocations and slot outlets, that route follows the server hand-over rules.
At ordinary HTML nesting it follows browser `parentElement` ancestry. At a
teleport it follows Alpine's authored-origin backlink, not the destination's
`parentElement`. Shared roots use the graph's ordered ownership records.
Range caps preserve the route for multi-root and rootless components.
Several logical frames on one shared physical root remain independently
ordered graph records; an element property cannot collapse them. A mirrored
logical frame keeps one occurrence per placement as specified in section
10.4.

The implementation derives this route from the existing exact component,
fill, and physical-region records, together with ordinary HTML ancestry and
Alpine's teleport-origin backlink. No additional wire-manifest relation is
needed. Component and slot transitions still use Citry's recorded ranges and
fill placement; they never fall back to the nearest marked DOM element.

The graph also resolves the starting point:

- `$inject` on an element begins outside that element's own ambient frame;
- hook `inject` begins independently at every component-frame occurrence's
  incoming ambient parent, then applies the section 10.4 consensus rule;
- descendants begin through the current element or component frame and can
  therefore observe its provide or block.

This makes descendant-only visibility independent of Alpine directive order
on one element.

### 10.7 Lifecycle, teleport, morph, and cleanup

A magic frame belongs to one expression element and physical placement. Each
contribution to that frame is owned by the synchronous Alpine directive
invocation that called `$provide()` or `$unprovide()`. Repeated magic property
access during one invocation must not stack cleanup work. Several initializing
directives on one element contribute in Alpine's deterministic directive
order; the last completed write for a key wins. When one declaring directive
is removed or replaced, Citry removes all of that invocation's contributions
and recomputes the element frame from those that remain before the replacement
directive and descendant hooks run. Removing the element performs the same
cleanup through Alpine's element lifetime.

This is stricter than the old plugin and cannot be implemented with the
public `Alpine.magic()` callback alone: Alpine exposes the expression element
there, but not the exact directive attribute or its cleanup. At build time,
Citry narrowly instruments pinned Alpine's `getDirectiveHandler` execution
path. Every built-in and plugin directive therefore enters the context service
with its real `(element, originalAttributeName)` identity, independent of
expression text, attribute order, or plugin priority. The instrumentation
passes the directive's own `utilities.cleanup` registrar to the context
service. Cleanup therefore follows Alpine's exact directive lifetime for
literal attributes, object-form `x-bind`, and programmatic `Alpine.bind()`;
it is not inferred from later attribute text or element removal alone. Exact
source replacements and behavior tests are canaries for this pinned private
integration. Citry does not degrade to element-lifetime registrations.

An Alpine magic value follows Alpine's normal capture rule. Reading `$inject`
returns a helper bound to that expression element. If code stores the helper
in `x-data`, the stored function keeps that element's rendered route when it
is called later, including after `await`; it does not silently rebind to the
element whose later expression happened to call the stored function. Spell
`$inject(...)` directly in the later expression when that later element's
route is wanted. Writes differ deliberately: a stored `$provide` or
`$unprovide` helper can mutate context only during another directive's
synchronous initialization, and the exact executing directive owns that
registration and its cleanup.

Component-owned frames are tied to the `$component` callback invocation.
They are disposed with managed effects and the callback's returned cleanup.
The stable logical lifecycle may survive a same-class morph, but the previous
invocation's registrations do not.

The existing structural policies remain authoritative:

- ordinary `x-if` and `x-for` copies get copy-local magic frames and cleanup;
- component-active server nodes remain subject to the current structural
  rejection rules;
- `x-teleport` keeps ambient lookup at its authored origin while native event
  propagation remains physical;
- a complete logical range move preserves its component frame;
- removing one mirrored placement removes only placement-local magic frames;
- removing the final placement removes the shared component frame;
- a compatible atomic morph correlates ambient routes before descendants
  resume;
- a class replacement or retired source invalidates captured helpers and
  removes all owned frames exactly once.

For a preserved element under compatible morph:

- an unchanged declaring directive keeps its registration and receives the
  incoming rendered route atomically;
- changing the directive cleans the old registration, evaluates the new
  declaration once, and then releases descendants;
- removing the directive removes its registration;
- moving the element with an unchanged declaration keeps the registered value
  but retargets its outer route;
- changing a key or value through a newly evaluated declaration replaces the
  old invocation's complete registration set, so removed keys cannot linger.

While Alpine initializes a detached incoming morph counterpart, Citry maps
reads to the live element being cloned. Detached writes are rejected; the
declaration writes once it is installed on the live element. Provider
lifecycle changes invalidate existing Alpine `$inject` expressions so they
re-resolve after the live write or cleanup.

Moving an element or a complete component range under different HTML
ancestors also invalidates those expressions. The provider frame stays with
its declaring element or component invocation, while the next lookup uses the
new browser ancestry together with the same slot and teleport routing rules.

Server `Component.provide()` values are not automatically serialized into
the client graph. A component that needs the same conceptual service on both
sides explicitly transfers suitable data through `js_data()`, client props,
or another declared client channel, then calls client `provide()`. This avoids
accidental serialization of Python objects, functions, secrets, or mutable
state.

### 10.8 Diagnostics and supported context

The magics are installed through Citry's pre-start Alpine broker. They are
valid only when the expression element belongs to a live Citry ownership
graph. Calling one in unrelated standalone Alpine markup raises a pointed
error instead of silently switching to DOM-only semantics. A future generic
Alpine adapter can be designed separately if there is product demand.

The names `$provide`, `$inject`, and `$unprovide` are reserved by Citry on its
owned Alpine instance. The broker installs all three before running queued
plugin callbacks. Its extension registration API and its guarded
`Alpine.magic()` reject attempts to overwrite them. The error names the
reserved magic and leaves Citry's registrations unchanged. The archived
standalone plugin is therefore incompatible on the same Alpine instance and
must not be installed alongside Citry's implementation.

Diagnostics must distinguish:

- invalid key type or empty string;
- missing injection with no default;
- use outside a live Citry route;
- `provide` or `unprovide` after synchronous initialization;
- a captured helper used after its owner retired;
- malformed or missing ambient ancestry at a component, fill, teleport, or
  shared-root transition;
- duplicate runtime installation or a reserved-magic collision.

Errors name the key and the owner kind or component class when that information
is available, then give a concrete authoring fix. Symbol diagnostics use
`String(key)` and never treat two equal descriptions as equal symbols.

The dependency extension must arrange for the client runtime and ownership
manifest whenever these magics appear in a component template, even if the
component has no `js` body or Events handlers. Detection is an activation
signal only. It must not parse arbitrary expressions to infer context keys or
values.

### 10.9 Tabs and compound-component boundaries

The motivating Citry UI pattern is a compound component that consumes one
parent context but blocks accidental reuse below itself:

```js
const TabsKey = Symbol.for("citry-ui:tabs");

// CTabs
$component(({ reactive, provide }) => {
  const tabs = reactive({ active: null, tabs: [] });
  provide(TabsKey, tabs);
});

// CTab
$component(({ inject, unprovide }) => {
  const tabs = inject(TabsKey);
  unprovide(TabsKey);

  // Register this tab with `tabs`. Descendants now require a nested CTabs.
});
```

This permits `CTabs > CTab > CTabs > CTab` and rejects accidental
`CTabs > CTab > CTab`. The child can inject the inherited Tabs context because
its own block is outgoing only. A nested CTabs restores the key with its nearer
provide. The same rule applies when the inner content arrives through a slot.

### 10.10 Rejected alternatives

- **Copy the old `_provides` plus `parentElement` plugin.** Rejected because it
  cannot preserve Citry ownership and lifetime across the required root and
  slot shapes.
- **Use Alpine data scope as the context store.** Rejected because Citry
  deliberately isolates component data scopes, while ambient context is an
  explicit channel that must cross those boundaries. It would also conflate
  user variable shadowing with context-key replacement.
- **Resolve through lexical fill source.** Rejected because it contradicts the
  server slot contract and prevents a receiver from providing services to
  content rendered in its slot.
- **Resolve through physical DOM only.** Rejected by teleport, rootless
  components, logical mirrors, shared roots, and range-based morphing.
- **Expose only magics.** Rejected because a rootless component has no element
  carrier and multi-root component-wide setup would be duplicated.
- **Expose only hook methods.** Rejected because authors need a narrow provider
  or block at an arbitrary subtree, including inside slot content.
- **Add public `injectSelf`.** Rejected because own provided state is already
  locally available and descendant-only lookup is easier to reason about.
- **Automatically bridge server values.** Rejected because value eligibility,
  serialization, secrecy, identity, and reactivity all require explicit
  author intent.
- **Allow late provider topology changes.** Rejected for the first version
  because setup-time consumers would become order-dependent. Stable reactive
  provided values cover the legitimate dynamic-state case.

### 10.11 Implementation sequence and acceptance plan

The implementation was divided into independently reviewable stages:

1. Prove ambient-route representation against existing component, range,
   fill, shared-root, mirror, teleport, and graph-revision records. Decide
   whether the wire manifest needs one new relation. This proof includes
   per-placement frame occurrences and ambiguous hook injection.
2. Add the runtime frame registry, key validation, descendant-only lookup,
   blocking, defaults, stale-route protection, and lifecycle cleanup without
   exposing public APIs.
3. Add `$component` context methods and prove ancestor init ordering,
   rootless behavior, revision replacement, rollback, and cleanup.
4. Add the three Alpine magics through the permanent broker, including
   activation, directive-invocation cleanup, mixed hook/magic init ordering,
   reserved-name enforcement, and the pinned private-API canary.
5. Prove slot overlay and the separation of lexical expression source from
   rendered ambient route.
6. Close structural and transaction cases, then update public documentation
   and Citry UI components.

The completion matrix below remains required even though the core API and its
first browser coverage have landed. Cases not yet named in
`test_alpine_ambient_context_e2e.py` must not be treated as implicitly proven:

- string and symbol keys, provided `undefined`, omitted versus explicit
  `undefined` defaults, invalid keys, and missing-key diagnostics;
- nearest replacement, independent keys, sibling non-leakage, block,
  restoration, own-injection exclusion, duplicate writes, and failed-init
  rollback;
- method/magic parity on a single root, component-wide multi-root and rootless
  hooks, and narrow element subtrees;
- ancestor magic to descendant hook, ancestor hook to descendant magic,
  object-form `x-bind` provider creation, synchronous calls before an
  asynchronous pause, and rejected late calls;
- supplied fill, fallback fill, nested fills, detached content, a provider
  inside a fill, and caller lexical variables combined with receiver ambient
  context;
- ordinary user `x-data`, shared physical roots, transparent components,
  mirrors, structural clones, teleport, complete range moves across different
  providers, and final removal;
- mirrored occurrences with equal, missing, and conflicting outer outcomes,
  including found `undefined` versus missing, plus placement-local magic
  values;
- initial document activation, inserted fragments, compatible morph,
  incompatible replacement, stale callback helpers, and atomic graph
  rejection;
- preserved-element morph with an unchanged, changed, removed, or moved
  provider declaration, including removal of keys no longer declared;
- literal-attribute, object-form `x-bind`, and programmatic `Alpine.bind()`
  cleanup without stale registrations;
- attempted pre-start and late overwrite of each reserved magic name without
  partial installation;
- exact value identity and reactive-object updates without automatic
  provider-value wrapping;
- Chromium, Firefox, and WebKit behavior plus an Alpine 3.15.12 canary that
  fails when directive-invocation cleanup, magic utilities, or teleport
  ancestry changes.

The regression suite includes slot and teleport cases that fail if lookup is
reduced to `parentElement`, plus a rootless hook case that fails if component
frames are removed. These tests guard the architecture rather than only the
public spelling.
