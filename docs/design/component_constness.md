# Design: const-ness and render-body caching

**Status (2026-09-11): built, with ordinary component values and separate
const metadata.** `Const(value)` promises that one named value will remain the
same across renders. Citry uses that promise to compute eligible template work
once and cache the resulting body. This document calls that step
**precomputing**.

The current implementation has four parts:

- The public `Const` marker records a promise at the root of one named input or
  output. Citry removes that wrapper and recursively cleans supported builtin
  containers beneath it before component callbacks, hooks, schema user code,
  and template expressions receive the value. An ordinary container is not a
  cleanup root.
- Const provenance is the engine's record that a named value carries the
  promise. Renderer-owned mappings store that record beside ordinary values.
  The base `template_data` mapping, child input forwarding, template globals,
  and renderer-created scopes preserve provenance only when the engine can
  prove it still describes the same value.
- `ConstBodyCache` stores one precomputed body per component class, const
  signature, and visible-name set. It belongs to one `Citry` instance, uses a
  lock, and drops the least recently used entry when full.
- `precompute_const_parts` turns eligible expressions into escaped text,
  selects constant `<c-if>` branches, prepares live branch and slot interiors,
  and can unroll bounded text-only loops. A failed attempt leaves the node live
  so the normal render path reports any error.

Citry cannot infer which transformations in an arbitrary data callback are
constant. After `template_data` and data hooks finish, Citry restores input
provenance only when the final output has the same key and is the exact object
that component input normalization recorded. Renamed or replaced outputs need
an explicit promise:

```python
def template_data(self, kwargs, slots):
    return {
        "heading": Const(kwargs.label),
        "value": kwargs.value,
    }
```

Returning `kwargs` keeps each same-key input promise when the input schema
retained the recorded object. The base `template_data` method remains the
trusted engine mapping and keeps known input provenance without needing the
final comparison.

Sections 3-12 describe the current implementation. Section 13 keeps the first
performance measurements as historical evidence and qualifies where their
original callback model differs from the current contract. Section 14 records
the rejected const-slot design. Section 15 records later propagation
experiments. Section 16 describes the stronger `pure = True` promise.

For the broader migration context see
[`migration_djc.md`](migration_djc.md). For operating rules see
[`/CLAUDE.md`](../../CLAUDE.md).

Upstream references: django-components
[#1083](https://github.com/django-components/django-components/issues/1083)
(`Const()` / ~50% perf), 
[#1473](https://github.com/django-components/django-components/issues/1473)
(expression caching),
[#1650](https://github.com/django-components/django-components/issues/1650)
(preserve structured render data for safe cache replay),
[#1326](https://github.com/django-components/django-components/issues/1326)
(avoid double-parsing). The variable-provenance notes in
[`TODO/v2_TODO.md`](../../TODO/v2_TODO.md) (the "Expression caching" section)
are closely related.

---

## 1. Goal

Let a template author mark inputs as constant across renders:

```python
MyCard(title="hi", cols=Const(3))
```

`Const(x)` is a promise: "this input does not change between renders of this
usage." The engine uses that promise to do work once instead of on every
render. Concretely, any part of the template whose value depends only on
const inputs is computed on the first render, precomputed into the body, and reused
on later renders. The non-const parts are re-evaluated every render as usual.

Component code still works with normal Python values. Behind the scenes the
engine recognizes a previously seen const signature and reuses the prepared
body.

This is the Citry form of django-components #1083.

---

## 2. Mental model

- Composition (`MyCard(...)`) produces an element describing what to render.
- Citry consumes a `Const` wrapper at each named component-input root and
  records the promise by input name. Supported builtin graphs under a marked
  root are cleaned recursively; ordinary roots are left untouched.
- Component methods, custom data callbacks, hooks, and expressions receive
  ordinary values for automatic and root markers. A marker manually nested in
  an ordinary container remains the caller's responsibility.
- The default kwargs-to-template mapping retains known promises. A custom
  template-data callback also retains a promise for a same-key output that is
  the exact input object. It must explicitly mark renamed or replaced stable
  outputs.
- The optimized body for a given const signature is built once and cached.
- On every render, the dynamic inputs are applied fresh; the const parts are
  already precomputed.

The cache key records which used template variables are const, their values,
and which names are visible. Dynamic values do not enter the key.

---

## 3. Architecture

### 3.1 Layering

Three layers, from most-shared to least:

1. **Class: the body-generating function.** Parsing + compiling + exec of the
   template, cached once per component class (this exists today, see
   `_get_compiled_template` in
   [`packages/py/citry/citry/component_render.py`](../../packages/py/citry/citry/component_render.py)).
   Calling it yields a fresh, unoptimized node list.
2. **Const cache: the prepared body.** Keyed by `(component class, const
   signature, visible-name set)`. The value is a specialized node list where
   all-const nodes have been precomputed and dead control-flow branches pruned.
   Scoped to the `Citry` instance and bounded (see 7.2).
3. **Per render: dynamic evaluation.** The non-const nodes in the optimized
   body evaluate against the live context each render.

### 3.2 What gets cached: the prepared body

The `CitryElement` also carries the per-call inputs. Two calls
with the same const signature but different dynamic inputs, for example
`MyCard(title="hi", cols=Const(3))` then `MyCard(title="bye", cols=Const(3))`,
must not share an element, or the stored `title` would be wrong for the second
call. What is genuinely invariant across those two calls is the **optimized
node list**, so that is what the cache stores. Each call still creates an
element with that call's inputs. The renderer finds the shared body at render
time.

### 3.3 Where the lookup happens

At render time, inside `render_impl` (not at composition). When resolving the
template to render, the engine determines which context values are const,
builds the const signature, and fetches (or builds and caches) the optimized
body. The body therefore lives in the const cache, keyed by signature, not on
the element. `render_impl` consults that per-signature cache on each render;
the element itself owns no specialized-body cache.

### 3.4 First render and cache hit

- **First render (cache miss):** start from the unoptimized node list (layer
  1). For each node, if all of the node's used variables are const in scope,
  evaluate it and replace it with text when that result is safe to share.
  Prune dead branches and store the specialized list in the const cache.
- **Cache hit:** render the already-precomputed list directly; do not re-precompute.

---

## 4. The `template_data` boundary

The body consumes the template variables returned by
`template_data(kwargs, slots)`. The base method returns `kwargs`, so component
inputs are available to templates without an override. Citry knows that this
specific mapping preserves names and values, and it carries known const
provenance to the template context.

A custom callback is arbitrary Python. A const kwarg does not prove that a
derived output is const:

```python
def template_data(self, kwargs, slots):
    return {
        "label": fetch_from_db(kwargs.title),
    }
```

For every marked component input, Citry records the ordinary object produced
by input normalization, before the input schema runs. A newer explicit promise
from a default, input hook, or input schema updates the candidate for that
name. After the output schema and data hooks finish, a final template variable
recovers the promise only when it has the same key and is the recorded
candidate object. This preserves direct pass-through from a new mapping or
`return kwargs` when the input schema kept that identity, without putting
proxies in component code.

A renamed or replaced output does not meet both conditions. The callback must
mark it when it promises the result is stable:

```python
def template_data(self, kwargs, slots):
    return {
        "label": Const(kwargs.title),
    }
```

Citry consumes that output marker while normalizing the returned mapping. The
template expression sees the underlying value, while the renderer retains the
promise by the `label` name.

The identity comparison follows Python exactly. Singletons, interned strings,
and other reused immutable objects can make a recomputed value identical to the
input object. When `is` succeeds for the same key, Citry intentionally restores
the promise.

### 4.1 Ordinary values and separate metadata

The public `Const` object is a proxy because the marker must be able to wrap
scalars, containers, and application objects without modifying them. It is a
short-lived transport at renderer boundaries. For each named mapping entry,
the renderer consumes an exact root marker and stores provenance separately in
`_ConstMapping`. If that root contains an exact builtin `dict`, `list`,
`tuple`, `set`, or `frozenset` graph, normalization recursively consumes
markers inside the graph. An ordinary container root is kept as-is, including
any manually nested marker. Entries produced by a `c-bind` mapping are
individual roots.

The following boundaries receive ordinary values for automatic markers and
values explicitly marked at their roots:

- raw and typed component kwargs;
- `template_data`, `js_data`, and `css_data` callbacks;
- component input and data extension hooks;
- component lifecycle hooks;
- template expression evaluators.

These boundaries may still observe a marker that application code manually
placed inside an ordinary container.

The mapping consumes an explicit root marker written by a callback or hook, so
the next callback receives its normal root value. A nested marker added to an
ordinary container remains visible. Assigning an ordinary value to a name
clears that name's provenance for the next hook. This makes extension order
predictable: a later hook observes the previous hook's root value without its
marker object. The final template-data reconciliation can restore an input
promise when the same key still holds the recorded input object.

Renderer-created scopes copy trusted provenance and treat new loop, fill, and
host-template bindings as dynamic. Merges use rightmost value semantics. An
ordinary override clears earlier provenance, including a const template global
overridden by component data.

Input schemas receive ordinary named constructor arguments for marked roots.
Citry-generated dataclasses normalize supported root-marked defaults and
factory results before user constructor hooks run, including `init=False`
fields and values delivered as `InitVar`. An ordinary container returned by a
factory is not searched for nested markers. When the generated constructor
only assigns fields, real output fields retain provenance from their explicitly
marked defaults. `InitVar` values are not output fields. Standard named tuples
are also rebuilt with ordinary root values.

A schema with validation, coercion, `__post_init__`, a custom constructor, or
another transformation does not inherit input provenance by field name alone.
A field keeps the promise when its final same-key value is the recorded input
object. Otherwise its final named field can establish new provenance by
producing `Const(value)` itself. Citry does not make a general promise about
factories that an arbitrary schema owns and executes internally.

### 4.2 A node uses only const variables

A component may mix const and dynamic inputs. The correct criterion is **"the
node uses only const variables,"** evaluated against the variables that node
actually reads. One dynamic variable keeps that node live without blocking
precomputing elsewhere in the body.

---

## 5. What a precomputed body contains

Precomputing does not collapse a subtree to a single string. A prepared body is
a list whose items are one of:

- `str`: static text, passes through unchanged.
- a live node that re-evaluates against the current context each render.

Component and slot nodes remain live. Precomputing may still descend into the
fill, default-content, and fallback bodies that those nodes own because those
bodies use the writer's scope.

### 5.1 Component boundaries remain live

A nested `<c-Inner>` with const inputs still cannot become frozen text,
because every time the outer component renders:

- `Inner` must mint a **fresh render ID** (the same element rendered twice
  yields two identities, per #1650), and
- `Inner`'s JS/CSS must be (re)registered for this render.

Citry therefore keeps the `ComponentNode` in the prepared parent body. Resolving
its direct attributes can preserve const metadata for the child's inputs, so
the child can use its own body cache while still running its per-render
component work.

---

## 6. The composition and render structs

Two distinct structs sit on either side of `.render()` (full design in
[`component_rendering.md`](component_rendering.md)):

- **`CitryElement`** (inspired by React's `ReactElement`) is what calling a
  component produces: the description of a component invocation (class plus
  kwargs/slots). `Component()` returns a `CitryElement`.
- **`CitryRender`** is what `.render()` produces: the render-phase output
  carrying the rendered parts plus collected metadata (JS/CSS deps).
  `CitryRender.serialize()` produces the HTML string.

The parent body keeps a live component node. That node produces a new element
and, later, a child `CitryRender` on each render.

---

## 7. Cache key and lifetime

### 7.1 Key construction

The key is built from const metadata on the normalized **`template_data`
output**, not by inspecting wrapper types in callback values. The trusted base
mapping carries metadata from kwargs. A custom callback keeps metadata through
same-key object identity or establishes it with an explicit output marker.

Key = `(weak reference to component class identity, frozenset of (const context
variable name, const value), visible variable names)`. The weak reference has
identity semantics while the class is alive but does not keep an unregistered
class alive by itself. Const entries are order-independent (frozenset). The
const VALUES participate, so differing const values miss; the const VARIABLE
SET participates, so a different set of const variables misses. Dynamic values
do not participate because they re-render each call. Visible variable names do
participate because a binder must reject an already-visible name even when the
template does not otherwise read it.

### 7.2 Hashing strategy

Const values must produce a stable key.

- Hashable values use their exact type and value, so `True` and `1` remain
  different inputs.
- Lists, tuples, dictionaries, sets, and frozensets freeze recursively into a
  form that records their container kind.
- An unhashable value outside those supported containers is treated as dynamic.

Unsupported unhashable values stay dynamic; Citry does not substitute
`repr(value)` or `id(value)` as their cache key.

### 7.3 Bounding and scoping

The cache is a bounded LRU scoped to the `Citry` instance (512 entries by
default) and is cleared by `Citry.clear()`. Its component-class key is weak;
an ordinary cache lookup, eviction, inspection, or length check prunes entries
whose class has been collected. The weak reference has no callback because
dropping a cached body during garbage collection could run destructors from an
arbitrary interrupted context. A successful final-alias unregister evicts that
class's current entries immediately. The cache remains bounded even if no
later operation performs lazy pruning. Together these rules keep transient
render work within the engine and component lifetimes while preserving
explicit hot-reload eviction.

`Const(user.id)` and similar high-cardinality "const per render" values are an
**anti-pattern**. Document this as guidance: `Const` is for values that are
stable across many renders (layout constants, fixed labels), not for values
that are merely fixed within a single render.

---

## 8. Constness analysis and scopes

Foldability is per node and per scope.

- A node is precomputable iff **all** of its used variables are const in the node's
  scope. One non-const variable poisons the node.
- **Scope and shadowing:** `<c-for each="x in items">` introduces `x`, and
  `<c-fill>` may introduce its `data`/`fallback` names. Reusing an already
  visible name is an error. A new binding is ordinary and cannot inherit an
  outer name's provenance. Dynamic `c-bind` fill names keep
  variable-dependent body expressions live.
- **Unrolled-loop guard:** an all-const loop may bake its text, but a lightweight
  `ForNode` remains and rechecks its target names against the live context. This
  covers both cache hits and a context mapping mutated earlier in the render.
- **Control-flow pruning:** `<c-if cond="cols > 2">` with `cols` const can be
  evaluated at precompute time and the dead branch dropped (a large part of the
  win). With `cols` non-const, keep both branches.

The inputs to this analysis (`used_variables`, `introduced_variables`) are
already tracked in the AST.

---

## 9. Invariants

- **Root markers do not reach user code.** Citry removes automatic and explicit
  root markers before callbacks or expressions run. Rebuilding marked
  containers may change identity as described in section 11. A marker manually
  nested in an ordinary root is not consumed.
- **Per-render state is never precomputed.** The render ID, component id, and any
  scoped CSS/JS hashes derived from it must be injected fresh on every render,
  never baked into the cached body. Const-body caching stores a recipe that
  still runs for each occurrence; cross-request output caching uses the
  detached replay artifact in [`caching.md`](caching.md).
- **`Const` is a user promise, not verified.** If a user marks a value const
  and then mutates it, output goes stale. That is acceptable and must be
  documented.
- **Precomputing assumes pure, deterministic expressions.** Citry expressions are
  sandboxed by default (see `safe_eval`), which mostly guarantees this, but
  precomputing does change when a const expression is evaluated (once, at first
  render). (Turning the sandbox off does not change this assumption: a template
  expression is still expected to be a pure function of its inputs.)
- **Custom transformations are explicit.** A callback may derive values from
  files, databases, clocks, or mutable state. Same-key pass-through of the
  recorded input object keeps its provenance. A renamed or replaced output
  receives provenance only through `Const`.

---

## 10. Interactions and non-goals

- **Expression caching (#1473) is a separate concern.** That is a per-value
  memo of expression results while inputs are unchanged. It is unrelated to
  const precomputing and must not be entangled with it. In particular, because
  precomputed bodies are shared across elements with the same const signature but
  different dynamic inputs, the non-const nodes in a shared body must be
  stateless re-evaluators; any expression cache is a separate, value-keyed
  layer that only applies to truly-unshared nodes.
- **Slot content precomputes inside; the slot boundary stays dynamic.** Precomputing
  descends into fill bodies, the implicit default-slot body, and slot
  fallback bodies: they render against the variables of the component whose
  template wrote them, so const expressions inside them are pre-computed
  like any other. The slot boundary itself (which fill a `<c-slot>` renders,
  the per-render fill collection) is per-render state and is excluded from
  the cache key. Crossing that boundary, so that a constant fill precomputes the
  child's `<c-slot>` away entirely, was designed, checked, and parked: see
  section 14 for the design and the reasons it lost.
- **Template literals are implicitly const.** A static attribute
  (`age="30"`, unquoted `age=30`, boolean `compact=""`) and a zero-variable
  expression attribute (`c-age="30"`, `c-items="[1, 2]"`) are written in the
  template, so they cannot change between renders. Citry evaluates the whole
  attribute before marking its result at the child-input root. In a call such
  as `c-total="add(1, 2)"`, the arguments are ordinary integers. Citry marks the
  evaluated result only when every referenced variable, including `add`, is
  known const. The child then receives the ordinary result plus renderer-owned
  provenance. A `c-bind` spread is arbitrary data and remains dynamic; each of
  its mapping entries becomes a separate input root.
- **Schemas preserve only proven field identity.** Inert generated dataclasses
  and standard named tuples keep named provenance. Pydantic and other custom
  or coercing schemas do not inherit it by field name, but final same-key
  identity with a recorded input can restore it. An explicit marker in a final
  named field can establish new provenance and is consumed before downstream
  code receives that field.
- **Defaults are const by explicit marking.** Auto-marking
  defaults was rejected: defaults can be **dynamic** (a `default_factory` may
  produce a fresh value each call, for example a random uuid), and the engine
  cannot tell a pure factory from `uuid4`, so a blanket rule would be
  unsound. Instead a default is made const the same way any value is, by
  marking it: `cols: int = Const(3)` on the typed `Kwargs`. Citry removes the
  marker before schema user code runs and records provenance for the omitted
  field. A passed kwarg uses the caller's marked or ordinary status.
- **Hooks can establish or clear provenance.** An input or data hook can assign
  `Const(value)` to mark that name. The hook manager consumes the marker before
  calling the next hook. Assigning a normal value clears the name's provenance
  for later hooks. Final same-key identity with a recorded input restores its
  input promise before template evaluation.
- **The base mapping is the trusted fast path.** The base `template_data`
  returns kwargs and retains their known provenance. An override that calls
  `super()`, returns `kwargs`, or builds a mapping with an unchanged same-key
  object also keeps that input's promise. Renamed and replaced stable outputs
  require explicit marking.
- **Simple components use the same rule.** Their default kwargs mapping
  retains provenance. A declared simple data callback receives ordinary root
  values and keeps same-key object pass-through; renamed or replaced stable
  outputs need explicit marking. Manually nested markers in ordinary roots are
  left in place.
- **Typing ergonomics (resolved).** `title=Const("hi")` type-checks against
  `title: str`: to checkers, `Const` is `def Const(x: T) -> T` (transparent
  to the checker, wraps at runtime). Annotating the class itself does not
  work, because wrapt ships no stubs (so the proxy base is `Any` to checkers)
  and mypy does not honor a `__new__` returning a bare TypeVar.
  `is_const` and `const_value` remain the public helpers for code that handles a
  marker before it reaches a renderer boundary.
- **Thread-safety.** The shared cache is read and written during render;
  concurrent renders need a lock or a concurrent map. First-render precomputing
  under a lock.
- **Hot reload / invalidation.** If a template changes (hot reload) the cached
  optimized bodies are stale. `reset_template()` and successful final-alias
  unregistration evict that class, while `Citry.clear()` evicts all classes.

---

## 11. Error modes and limits

- Only an exact root `Const` starts recursive normalization. Beneath that root,
  normalization follows exact builtin `dict`, `list`, `tuple`, `set`, and
  `frozenset` containers. It does not inspect attributes or contents owned by
  arbitrary application objects.
- Root markers supplied together in one normalization operation are converted
  as one graph, preserving aliases between them where possible and preserving
  mutable cycles. If a marked and an ordinary root share a graph that must be
  rebuilt, the marked root may receive a separate cleaned graph while the
  ordinary original stays unchanged.
- A cycle made from root or nested marker proxies beneath a marked root raises
  `ValueError`. Rebuilding a marked graph that crosses a cyclic tuple or
  frozenset also raises `ValueError`. Ordinary roots are not searched for
  these cycles.
- A known marked default combined with a custom dataclass constructor raises
  `TypeError` when Citry cannot normalize it before user code. If a custom
  input schema creates a marked read-only field that Citry cannot replace with
  its ordinary value, construction also raises `TypeError`. Citry handles
  supported named tuples by rebuilding them with plain fields.
- An already decorated dataclass with a marked `init=False` literal default is
  also rejected. Use an ordinary default or a Citry-generated declaration,
  which normalizes the value before user code runs.
- A marker manually nested inside an ordinary container stays in place and
  does not mark the containing name const. Application code must unwrap the
  nested marker where it uses the value. Mark the complete container when the
  complete value satisfies the promise and should be normalized recursively.
- If a const value cannot become a stable cache key, Citry treats that variable
  as dynamic and renders it normally.
- If an eligible expression, attribute region, condition, or loop fails while
  Citry tries to precompute it, Citry keeps the live node. The normal render
  path then reports the error at its usual point.
- A one-shot iterator is unsafe to mark const because precomputing may consume
  it. Use a stable list or tuple.

---

## 12. Landed phases and future work

The bounded body cache, node precomputing, literal and template-expression
forwarding, typed defaults, invalidation, and locking are built. Issue
[#107](https://github.com/citry-dev/citry/issues/107) establishes ordinary
component values while retaining these engine-controlled paths.

The callback boundary does not track arbitrary Python computations. It
recovers only same-key output that retains a recorded input object's identity;
renamed or replaced output remains explicit. Restoring transparent proxies
inside component methods depends on upstream support and is tracked only in
[#124](https://github.com/citry-dev/citry/issues/124). Cross-slot precomputing
remains parked for the reasons in section 14.

---

## 13. Measured results (2026-06-10, slot row 2026-06-11)

These numbers are historical evidence from the first proxy-based
implementation. They still show the possible value of body precomputing, but
they are not a current blanket performance claim. The present base
`template_data` path, same-key identity forwarding, and explicitly marked
custom outputs retain the optimization. A custom callback that relied on
broader input-marker propagation must mark renamed or replaced stable outputs
before this comparison applies.

Measured on an M-series Mac, CPython 3.13, **release** build of the Rust
extension (`maturin develop --release`; the default debug build skews any
benchmark that touches `transform_html` by ~12x). Each case compares the
same component called with `Const(...)`-marked inputs vs plain inputs, after
warmup (cache hits, not first-render precomputing). The current script reruns
these scenarios against the current implementation:

```bash
.venv/bin/python packages/py/citry/tests/benchmark_const.py            # rerun these scenarios
.venv/bin/python packages/py/citry/tests/benchmark_const.py --profile  # include the section 14.5 breakdown
```

| Template | Render only | Render + serialize |
|---|---|---|
| Expression-heavy (35 const exprs, 5 const ifs, 1 dynamic expr) | **2.38x** (27.5 -> 11.6 us) | **1.98x** (36.1 -> 18.3 us) |
| Small card (4 const exprs, 1 const if, 1 dynamic expr) | **1.48x** (8.7 -> 5.9 us) | **1.37x** (11.6 -> 8.5 us) |
| Nav with const 20-link loop, precompute v2 unroll (1 dynamic expr) | - | **2.83x** (44.1 -> 15.5 us) |
| Slot-heavy layout (layout + card, 4 slot sites, const fills precomputing inside) | **1.56x** (47.5 -> 30.5 us) | **1.64x** (68.8 -> 42.0 us) |

The render-phase number matches the ~50% upstream claim (django-components
#1083). Two findings from profiling:

- In that implementation, per-render signature freezing grew with the number
  of const variables. Memoizing the frozen key on each marker recovered
  roughly half the precomputing win in the 35-marker case. The current
  ordinary-value mapping does not expose root markers to callbacks.
- After precomputing, serialization (the marker pass) was the largest single
  remaining cost, ~37% of end-to-end; addressed in
  [#7](https://github.com/citry-dev/citry/issues/7) by `mark_html`, a
  single-pass root scan in `citry_html_transform`.

---

## 14. Const slots: precomputing across the slot boundary (considered, parked)

**Verdict (2026-06-11): parked.** The falsifier checks in 14.5 were carried
out and the design lost on all three counts; the measured results are
recorded there. The deciding argument is behavioral, not just numbers:
precomputing away `<c-slot>` tags makes core slot machinery (fill invocation,
the `on_slot_rendered` hook) conditional on an optimization, and an
extension implementing that hook (likely, possibly a built-in) would
disable the feature wholesale anyway. What slot-heavy pages actually
needed, precomputing INSIDE slot content, is built and unaffected (14.1).
The design below is kept as the record of what was considered and why it
was rejected.

Real pages are slot-heavy: a layout component exposes sidebar and main
slots, the main slot holds a card with title and body slots, the body holds
a button with a content slot. If the optimization stops at slot boundaries,
it misses most of such a page. This section designs the crossing.

### 14.1 What is already built

Precomputing descends INTO slot content (fill bodies, the implicit default-slot
body, slot fallback bodies), because that content renders against the
variables of the component whose template wrote it, and those are fixed per
cache entry. So a fill like `<c-fill name="title">{{ heading }}</c-fill>`
with `heading` const already precomputes to plain text inside the parent's cached
body. What does NOT yet happen: the child component still renders its
`<c-slot name="title">` dynamically on every render, looking up and
invoking the fill, even though the fill's output is a fixed string.

### 14.2 The key insight: a const slot is a fill that precomputed to pure text

There is no need for separate "is this slot const" reasoning (tracking the
fill's used variables, for example): after the parent's body is precomputed, a
constant fill is simply one whose body list contains nothing but strings.
That test is more precise than any static analysis (it benefits from
`<c-if>` pruning inside the fill) and the constant VALUE (the text) falls
out for free. A fill containing a nested component can never be const: the
child mints fresh render ids every render.

### 14.3 Design

1. **Detect at fill collection.** When `ComponentNode` collects fills, a
   fill whose (already-precomputed) body is all strings produces a `Slot` tagged
   with its constant text (e.g. a `const_text: str | None` field). The same
   tag applies to plain-string fills from the Python API
   (`slots={"title": "Hello"}`): a string fill is inherently constant, the
   slot counterpart of the template-literal rule of section 10.
2. **Let const slots into the child's cache key.** `_CompiledTemplate`
   additionally captures the template's statically declared slot names (the
   parsed AST already exposes `Template.slots`). The child's key then
   records, for each declared slot: the constant text when the fill is
   const, an explicit ABSENT marker when no fill was given, and NOTHING when
   the fill is dynamic.
3. **Why absent and dynamic must be distinct keys.** Precomputing the fallback
   body into place is only sound for renders that have NO fill for that
   slot. If "absent" and "dynamic fill" shared a cache entry, a render that
   passes a dynamic fill would be served the baked fallback. With distinct
   keys, the ABSENT entry can inline the (already precomputed) fallback, and
   dynamic-fill renders keep a live `<c-slot>`.
4. **Precompute the child's `<c-slot>`.** During the child's precompute, a slot node
   whose name is static and maps to a const-text entry is replaced by that
   text; one that maps to ABSENT is replaced by its precomputed fallback body.
   Slots with dynamic names (`c-name`) never precompute.
5. **Hook gate.** `on_slot_rendered` fires once per slot render today;
   precomputing the slot away would skip it. Only precompute slot nodes when no
   registered extension implements `on_slot_rendered` (the extension
   manager knows). This keeps the extension contract intact at the cost of
   the optimization, which is the right default.

In the layout scenario this would bake the card's title ("Dashboard"), a pure
static sidebar nav, and a button whose content slot is plain text. Any fill
containing a component or dynamic expression would stay live, along with
instances, fill collection, the render queue, and serialization.

### 14.4 Alternatives considered

- **Expose `used_vars` on `Slot` and reason from them.** Subsumed by 14.2:
  template fills already carry parser-computed used variables internally,
  but "try precomputing and check the result" is strictly more precise, and for
  Python-API slots there is no template scope for `used_vars` to refer to.
- **A generic `Const(slot)` wrapper as the user API.** Works as a promise
  for values whose output can be keyed (strings, which are auto-marked
  instead), but an arbitrary slot function's output cannot become a stable
  cache key without calling it, and function objects are typically
  recreated per render, so identity keying would never hit (the same
  reasoning that rejected `id()` keys in section 4.1). A
  const-promised slot *function* API is deferred until someone needs it.
- **Keying the child's cache on `Slot` object identity.** Rejected: fill
  collection builds fresh `Slot` closures every render, so identity is
  never stable.

### 14.5 The falsifier checks (carried out 2026-06-11; all three fired)

- **Fill-collection cost dominates.** Checked by profiling a representative
  layout page (layout + card, four slot sites, const sidebar links and
  title, dynamic body; reproducible with
  `packages/py/citry/tests/benchmark_const.py --profile`).
  `SlotNode` rendering was 32.7% of render time, but
  only two of the four slots would precompute, so the realistic ceiling was
  roughly 10-16%. Fill collection (~12%) is paid regardless: fills must be
  collected as long as any slot stays dynamic. The remaining per-render
  costs (instances, queue, serialize) require broader component-boundary work
  and are outside this design.
- **Low hit rate in real templates.** Worse than the raw rate suggests: the
  slots that CAN precompute are systematically the cheap ones (titles, labels,
  short static fills), while the expensive slots (main/body content) are
  exactly the ones that contain components and can never precompute. The win
  concentrates where there is least to win.
- **`on_slot_rendered` becomes ubiquitous.** Confirmed as likely: a built-in
  extension (the dependency extension is the natural candidate) is expected
  to implement the hook, which would trip the gate in 14.3 everywhere and
  leave the feature as dead complexity.

### 14.6 Open points

- Const slot texts live inside cache keys; a large static fill (a whole
  sidebar) makes a large key. The bounded cache contains the memory cost,
  but it is worth a note in the guidance.
- Cardinality guidance is the same as for const kwargs: a slot whose text
  differs on every render should not be const (and won't be detected as
  such unless its inputs are wrongly marked).
- A child using the same slot name in several `<c-slot>` tags bakes the
  text in each place; that is correct and needs no special handling.

## 15. Historical propagation experiments

The large benchmark attributed about 8% of a repeat render to expressions and
10% to element attributes. Most expressions read per-render loop data, so
broader const propagation had a low ceiling. Of 364 dynamic `c-*` attributes,
248 were bare variables, about 36 were literals, and only 8 computed over a
constant. None of its 47 `{{ }}` expressions computed over constants.

Two broader designs were assessed and left unbuilt:

1. **Deep const for literal collections.** This would track const provenance
   for individual values nested inside a container. It added no cache-key
   benefit because key freezing already walks complete const containers. Its
   only benefit was forwarding one nested value through another component, a
   pattern absent from the benchmark. The current normalizer consumes nested
   markers only beneath a marked root and does not infer per-item provenance.
   A manually nested marker under an ordinary root remains in place.
2. **Tracked computed values.** This would observe which const inputs arbitrary
   Python reads while deriving a result. It required callback-visible tracking
   objects and complex dependency rules, but the target workload mostly mixed
   const configuration with dynamic loop data. It did not justify the runtime
   or API complexity. It is historical exploration, not an active contract.

### 15.1 Template-expression forwarding

The narrow propagation rule that shipped applies only at a child component
input boundary. `_kwarg_is_const` checks whether every variable read by a
direct expression attribute has const provenance. If so, it attaches provenance
to the resolved child input. The literal case is the zero-variable form of the
same rule. A temporary marker transports that decision into child input
normalization and is consumed before child component code runs.

No access tracking is required because the compiler already records an
expression's inputs. Renderer-created loop and fill bindings are ordinary, so
expressions that read them do not inherit outer provenance.

The historical A/B measurements compared this rule with literal-only
forwarding:

| page shape | output identical | eval count off -> on | repeat render off -> on |
|---|---|---|---|
| large benchmark (data-heavy) | yes | 2577 -> 2577 (0%) | 12.28 -> 12.43 ms |
| config nav, rich child (6 const exprs x 200) | yes | 1601 -> 401 (**-75%**) | 2.55 -> 2.46 ms (**-3.8%**) |
| config nav, lean child (1 const expr x 200) | yes | 601 -> 401 (-33%) | 1.99 -> 2.23 ms (**+12%**) |

The rule reduced expression work on configuration-heavy pages but also added
cache-key work. The rich child improved while the lean child slowed down. The
data-heavy page did not reduce its expression count. These figures support a
conditional optimization, not a universal performance claim.

The child-input expression still evaluates on every parent render. If an
impure expression over promised-const inputs returns a different value, it
creates a different child cache signature. Output stays current, but the
bounded cache churns. Template expressions and marked inputs are expected to
be pure and stable.

## 16. Explicit pure-component body caching (2026-08-21)

`Const(value)` is a promise about one value and lets Citry specialize only the
nodes that depend on const inputs. `pure = True` is a stronger promise made by
one exact component class: its template body is a deterministic,
side-effect-free function of its template variables. Purity does not inherit;
a subclass receives `pure = False` unless it states the promise again. The same
rule applies to engine-neutral `LibraryComponent` definitions.

The implementation deliberately memoizes less than a complete component:

1. Every occurrence still creates a component instance and fresh render ID,
   runs input normalization, `template_data`, JS/CSS data, provides, lifecycle
   hooks, extension data hooks, finalization, and dependency merging.
2. A render-local `ContextVar` owns the memo. Nested components share it, but
   the complete dictionary is discarded when the root render ends. There is no
   cross-request state or invalidation problem.
3. The key contains the exact component class, compiled body identity, the
   complete visible-name set, and only parser-reported variables the template
   uses. Exact primitives and ordinary containers/dataclasses freeze by value;
   an unknown application object is reusable only when the exact same live
   object occurs again in that root render.
4. A miss walks the normal body one top-level item at a time and captures a
   small immutable plan. Safe items store their strings plus the shape of
   exact, same-context, transparent `CitryRender` wrappers created by control
   flow. A hit rebuilds those wrappers against the current context, so current
   IDs and frames remain current.
5. An item becomes a live hole when it changes ownership, captures i18n, or
   returns a child/deferred component, slot region, placeholder, foreign
   context, or component-root render. A hit executes that item normally while
   reusing safe siblings around it. Citry stores nothing when the body contains
   no reusable node result. This keeps the optimization fail-closed without
   rejecting a complete body merely because one item must remain live.

The explicit promise covers expression and element-hook behavior. A component
that mutates state, consumes a stream, reads ambient data absent from its
template variables, or depends on an element-level extension hook firing per
occurrence is not pure. Component-level data and lifecycle hooks remain live,
but putting the side effect there merely makes the declaration surprising and
is discouraged.

### 16.1 Why not reuse the output-cache artifact

The persistent Cache extension already has a detached replay format capable of
fresh IDs, ownership, dependencies, i18n, security validation, and backend
transport. It is the correct trust boundary for cross-request subtree caching,
but too expensive for a tiny render-local leaf memo. On the large benchmark,
replaying typed artifacts for the candidate leaves moved a roughly 41.8 ms
warm render to 58.6 ms. JSON was not the cause; validation and complete graph
replay were. The pure-body plan is intentionally not a second persistent cache.

### 16.2 Measured scope and outcome

The benchmark's 36 authored component classes were all force-enabled in the
original complete-body falsifier. Only two produced qualified repeated bodies:
`HeroIcon` stored 11 input shapes and hit 30 times; the no-child branch of
`ProjectOutputBadge` stored once and hit 10 times. Every other complete
occurrence was unique or carried children or ownership.

An interleaved 17-process A/B, with those two real declarations enabled only
on the candidate side, moved the warm median from 42.49 ms to 39.44 ms (means
42.96 to 39.12 ms). Deterministic fresh IDs produced byte-identical
980,643-byte output. This is a useful opt-in for repeated leaves, not the
architectural route back to the June 14 ms result; the much larger remaining
cost is live component, node, slot, and ownership work that purity correctly
refuses to erase.

The follow-up item plan keeps that live work as holes and reuses safe sibling
items. Focused tests prove that a stable expression runs once around two live
child executions, and likewise around two independently rendered slot fills.
Force-enabling additional benchmark classes still produced no clear end-to-end
win because freezing each input key cost about as much as the small sibling
expressions saved. The feature therefore expands where an application can gain
from an explicitly expensive pure expression; it is not a blanket reason to
mark container components pure.
