# Design: component and fragment render caching

**Status (2026-07-23): Phases 1-5 and migration closeout complete;
`Component.Cache`, the transparent `<c-cache>` component, public documentation,
Cache introspection, and the applicable upstream test replacements are
available.** This document designs two
related output-cache features:

1. `Component.Cache`, which caches one component subtree by its effective
   inputs.
2. `<c-cache>`, which caches an explicitly named region inside a template.

Both features use the existing engine-owned [`CitryCache`](../../packages/py/citry/citry/cache.py)
backend. They differ in how an author names and varies an entry, but they share
one Cache extension, one key builder, and one replayable cache-entry format.

This is output caching. It does not replace Citry's compiled-template cache,
const-body cache, dependency-script cache, application data cache, response
cache, or the proposed expression cache.

The migration inventory is
[`migration_djc_tests.md`](migration_djc_tests.md). The applicable
`test_component_cache.py` and `test_django_cache_tag.py` behaviors now have
public Citry replacement coverage; named backend aliases remain deferred.

---

## 1. Decision summary

The design makes these decisions:

- The public template component is named `<c-cache>`. It is a transparent,
  reserved built-in component. No parser or grammar change is needed.
- Cache is a built-in extension, present on every `Citry` instance and disabled
  per component by default. It owns the nested `Component.Cache` config and the
  `<c-cache>` implementation.
- A cache entry is a versioned JSON `CachedRenderArtifact`. It is not final
  HTML, a pickled Python object, a live `CitryRender`, or a `CitryElement`.
- Replaying an artifact reuses the current cache-boundary component's already
  minted ID, preserves current-call boundary metadata, mints fresh IDs for
  archived descendants, and restores selected dependency, Events, and
  ownership contributions into the current render.
- Component lookup happens after all `on_component_input` hooks, but before
  `template_data()`, `js_data()`, `css_data()`, `on_render()`, and template
  rendering. Publication happens only after the complete subtree and every
  `on_component_rendered` hook succeed.
- Cache hits do not run the cached subtree's data, render, slot, attribute, or
  rendered hooks. `on_component_input` still runs for the cache boundary.
- Default component variation includes the complete effective typed kwargs,
  including defaults and factories. A supplied fill or typed Slot
  default/factory that produces content requires an explicit `Cache.vary()`
  method. Merely declaring an optional Slot whose effective value is `None`
  does not. Citry does not attempt to hash slot source or closures.
- `<c-cache>` requires a non-empty `key` and accepts one explicit `vary` value.
  The author must include every user, tenant, locale, provide value, global, or
  other input that can affect the body.
- `ttl=None` means no expiry, a positive finite number means that many seconds,
  and `ttl=0` bypasses caching for that render. Negative, non-finite, and boolean
  TTLs are errors.
- V1 uses the one cache backend owned by the `Citry` instance. Django-style
  named backend aliases are deferred.
- Concurrent misses may perform duplicate work. Citry publishes only complete
  successful artifacts, but does not hold a local or distributed lock while a
  component renders.
- Cache backend exceptions propagate, matching existing `CitryCache` use.
  Corrupt or unsupported render-cache entries are treated as misses and later
  overwritten by a successful render. They are not blindly deleted because a
  concurrent writer may already have replaced the bad value.
- Shared-worker render caching is explicit. The user supplies an application
  namespace and a deployment generation. Without both, keys include
  `Citry.engine_id` and are intentionally local to that engine lifetime.
- Exact-key deletion and version changes are supported. V1 does not maintain a
  distributed index of every variant of a fragment or component.

The most important prerequisite is the replay artifact. Neither public feature
should ship by caching strings or live render objects as a temporary shortcut.

---

## 2. Why this needs a new render representation

Citry already has three useful representations:

```text
Component(**kwargs)         -> CitryElement   describes work to do
CitryElement.render()       -> CitryRender    live result of one render
CitryRender.serialize()     -> str            final HTML
```

None of the three is a correct cross-request output-cache value.

### 2.1 Final HTML freezes render-local state

Serialization stamps every component root with its render ID. Dependencies,
Events, and client ownership also refer to those IDs. Reusing the same HTML in
two positions can therefore give two physical elements the same logical
instance identity.

django-components currently has this problem. Its component-aware Django cache
tag stores fully assembled HTML. Reusing one fragment twice can attach a client
handler repeatedly, and a persistent fragment can outlive process-local JS/CSS
variable data. The architectural report is
[django-components #1650](https://github.com/django-components/django-components/issues/1650).

Citry must not adopt that intermediate implementation.

### 2.2 A `CitryElement` still performs the expensive render

A `CitryElement` contains the component class, kwargs, and slots. Calling its
`render()` method correctly creates fresh IDs, but also runs the component and
its subtree again. Caching it is composition reuse, not output caching.

Template-created elements also carry ownership invocation records, and their
Slots may close over the writer's render context. Retaining one across requests
would retain render-local state even before it is invoked.

### 2.3 A live `CitryRender` retains one render

A `CitryRender` contains:

- the original component instances and their IDs;
- `CitryContext` objects, including variables, provides, and extension data;
- the original `OwnershipGraph` and physical slot regions;
- dependency records that intentionally retain exact component classes until
  serialization;
- nested render objects and serialize-time placeholders.

Serializing the same `CitryRender` twice preserves its IDs. Putting the same
rendered component ID in two positions is explicitly rejected by the serializer.
Serialization can also add ownership-manifest data to the render context, so a
live object is not a shareable immutable value.

Keeping live renders in an engine cache would recreate the class-lifetime leak
that Citry recently removed from its derived caches. It could also retain a
request, current user, provide payload, Slot closure, or custom extension state.

### 2.4 Corrected older design notes

[`component_rendering.md`](component_rendering.md), [`dependencies.md`](dependencies.md),
[`component_constness.md`](component_constness.md), [`extensions_roadmap.md`](extensions_roadmap.md),
and [`migration_djc.md`](migration_djc.md) previously used a live render
object as shorthand for structured cache data. Phase 0 corrected those
passages, the corresponding runtime module documentation, and the migration
ledger to use the detached replay artifact contract. A normal live
`CitryRender` remains a one-render value.

---

## 3. Prior art and lessons

### 3.1 django-components `Component.Cache`

django-components provides:

- `enabled`, `ttl`, `cache_name`, and `include_slots` config fields;
- a default key derived from the component class and stringified inputs;
- an overridable `hash()` method;
- a hit before component data and template rendering;
- publication after a successful render;
- an optional attempt to add slot contents to the key.

The implementation and tests are preserved locally in
[`_djc_reference/extensions/cache.py`](../../packages/py/citry/_djc_reference/extensions/cache.py)
and
the upstream
[`test_component_cache.py`](https://github.com/django-components/django-components/blob/5d4d4f5d13dd06c80ba389f30fc63fdbb71cda75/tests/test_component_cache.py).
The current user contract is documented in
[django-components component caching](https://django-components.github.io/django-components/latest/concepts/advanced/component_caching/).

Useful behavior to retain:

- opt-in component caching;
- an ordinary TTL;
- a customizable variation function;
- hit before expensive component methods;
- errors never publish an entry;
- no pending cache state on a process-global dictionary.

Behavior not to copy:

- Stringifying values with punctuation is not a canonical key format. It can
  collapse distinct types and delimiter-shaped inputs, and it can invoke an
  arbitrary object's `str()` implementation.
- `include_slots` does not see values captured by a template fill. The same
  fill source can render differently in different caller scopes. This is the
  unresolved part of
  [django-components #1164](https://github.com/django-components/django-components/issues/1164).
- Its documented `ttl=-1` "forever" value is passed through to Django, whose
  backends treat non-positive timeouts as immediate expiry. Citry already has
  the clearer `None` means forever contract.
- A stable class ID and input digest do not invalidate persistent entries after
  component code or templates change.
- The implementation stores finished output, so it inherits the identity and
  dependency problems in section 2.1.

Two upstream lifetime fixes directly shape this design:

- [django-components #1607](https://github.com/django-components/django-components/issues/1607)
  found that pending cache keys accumulated in a singleton extension mapping.
- [PR #1648](https://github.com/django-components/django-components/pull/1648)
  fixed the remaining short-circuit path by keeping pending state on the
  per-render component config.

Citry keeps a miss plan on its render-local finalize task. The Cache extension
does not own a render-ID-to-key dictionary.

### 3.2 Django template fragment caching

Django's `{% cache %}` tag has a small and successful public model:

- a required timeout and literal fragment name;
- ordered explicit variation values;
- `None` for no expiry;
- optional backend alias selection;
- `make_template_fragment_key()` for exact invalidation;
- get, render, then set on a miss.

See the
[Django fragment-cache documentation](https://docs.djangoproject.com/en/6.0/topics/cache/#template-fragment-caching)
and
[Django cache tag source](https://github.com/django/django/blob/stable/6.0.x/django/templatetags/cache.py).

Citry keeps the named fragment plus explicit variation model. It improves the
physical key format and replay value.

Django's key builder feeds `str(value)` plus separators into a digest. Citry
instead uses a typed canonical encoding. Django also leaves user, tenant,
locale, timezone, template version, and deploy version entirely to the author.
Citry cannot infer all of those either, but its documentation and generation
contract make the risk explicit.

### 3.3 Django cache backend lessons

Django distinguishes omitted timeout, `None`, and zero, supports prefixes and
versions, and exposes `add()` and `get_or_set()`. Its `get_or_set()` prevents a
late contender from overwriting a winner, but every contender may still run the
expensive factory. The history is captured in Django tickets
[#12982](https://code.djangoproject.com/ticket/12982) and
[#26332](https://code.djangoproject.com/ticket/26332).

Citry does not need to enlarge `CitryCache` for the first render-cache release.
The existing string protocol can store a JSON artifact. Duplicate miss work is
an explicit contract, not an accidental promise of single-flight behavior.

Other Django lessons included in this design:

- Local memory caches are per process. Shared workers need a shared backend.
- Physical keys should satisfy Memcached's short ASCII key restrictions.
- Prefixes and code/data versions prevent cross-application and cross-deploy
  collisions.
- Cache values are untrusted for availability but trusted as application
  output. A writable cache can inject HTML. Citry avoids pickle, which removes
  the additional arbitrary-code deserialization risk, but the backend still
  belongs inside the application's trust boundary.
- Fragment expiry can cause a stampede. Django ticket
  [#35524](https://code.djangoproject.com/ticket/35524) records the problem;
  this design defers renewal and distributed locking instead of pretending an
  atomic `add()` solves them.
- Enumerating every derived fragment variant is hard. Django ticket
  [#5815](https://code.djangoproject.com/ticket/5815) is why Citry starts with
  exact deletion and versioned invalidation, not a distributed variant index.

---

## 4. Public API

### 4.1 `Component.Cache`

Cache is a built-in extension named `"cache"`. Every component therefore has a
reserved nested `Cache` config surface, although output caching is disabled by
default.

The component-facing fields are:

```python
class ProductCard(Component):
    class Cache:
        enabled = True
        ttl = 300
        version = "v1"

    ...
```

| Field | Default | Meaning |
|---|---:|---|
| `enabled` | `False` | Whether this component boundary performs lookup and publication. |
| `ttl` | engine Cache default, initially `300` | Positive seconds, `None` for no expiry, or `0` to bypass. |
| `version` | `1` | Author-controlled component-output version included in the key. |

`cache_name` is not included. One `Citry` owns one cache backend, and the same
backend already stores dependency scripts and optional server-held Events
state. One backend avoids django-components' persistent-fragment versus
process-local-media mismatch. Applications that need storage separation can
gain a deliberate named-backend map in a later design.

`include_slots` is not included. Its apparently convenient behavior is unsafe
for template fills that close over caller variables.

#### Default variation

After every `on_component_input` hook has run, core revalidates the mutated raw
kwargs and Slots and builds the typed `component.kwargs` / `component.slots`
views. Typed construction is deferred until this point, so normal defaults,
factories, coercion, and validators run exactly once. The
default variation value is then a complete read-only snapshot of the effective
typed kwargs, not merely the author-supplied raw mapping. Dict key order does
not matter; sequence order does.

That revalidation closed the input-propagation item from
[`extensions.md`](extensions.md) in Phase 1. A cache key and the component's
data methods cannot observe two different input generations. An invalid
input-hook mutation raises before cache lookup, so a hit cannot hide an input
contract error.

The default variation describes the effective typed inputs. A component that
deliberately reads `raw_kwargs` or `raw_slots` in output-producing code must
define `Cache.vary()` and include every raw distinction that can affect output.
Typed validation may coerce values or remove a `Const` marker, so typed equality
does not prove raw equality.

The default variation path is valid only when the component has no effective
Slot input source. A supplied fill and a typed Slot default or factory that
produces content each count as a source and raise `CacheKeyError` with guidance
to define `Cache.vary()`. A declared optional Slot whose effective value is
`None` does not count. Fallback body content authored inside the component's
own template is internal output and can be cached. Citry does not silently
ignore a Slot and does not render one merely to build a key.

#### Custom variation

A component can return a smaller canonical value or turn complex inputs into
stable identifiers:

```python
class ProductCard(Component):
    class Cache:
        enabled = True
        ttl = 60
        version = "price-layout-v2"

        def vary(self, kwargs, slots):
            return {
                "product_id": kwargs["product"].pk,
                "currency": kwargs["currency"],
                "has_badge": "badge" in slots,
            }
```

`vary` is an instance config method. `self.component` is the current boundary
component, matching other extension-config methods. `kwargs` and `slots` are
read-only snapshots of the complete effective typed inputs after defaults,
factories, and input hooks. Defining the method is an explicit assertion that
its result covers every input that may affect the output, including any Slot
the method chooses not to describe. The method must not render a Slot and must
return a value accepted by the canonical encoder in section 6.2.

The method is named `vary`, not `hash`. It describes semantic variation and
returns structured data. Citry owns hashing and the physical key format.

#### Ambient data remains explicit

The default key cannot see future database reads, current time, randomness,
`template_globals`, `Component.inject()`, feature flags, or request state hidden
behind an object. A cache-enabled component that depends on one of these must do
at least one of the following:

- pass the relevant stable value as a kwarg;
- include it in `Cache.vary()`;
- increment `Cache.version` when it changes as one unit;
- leave caching disabled.

`Cache.vary()` may read an ambient value through `self.component`, including
`inject()`, but passing the stable dimension as an explicit kwarg is easier to
inspect, test, and reproduce. Ambient render globals are not passed as a second
implicit mapping.

Extensions follow the same rule. Cache does not add fields or callback arguments
for i18n, authentication, feature flags, or any other named extension. A
localized component can include the i18n context's plain immutable identity in
its normal variation:

```python
class Cache:
    enabled = True

    def vary(self, kwargs, slots):
        return {
            "kwargs": kwargs,
            "locale_context": self.component.i18n.context.identity,
        }
```

The identity covers locale, fallback locales, direction, time zone, tzdb
revision, catalog revision, and format revision. Cache treats it like any other
tuple of canonical values. If the component deliberately returns no locale
facts, ordinary Cache semantics apply and the entry may be shared across
locales. The author remains responsible for making that choice safe.

Caching never creates an authorization boundary. Omitting a user or tenant
dimension can serve one caller's rendered data to another caller.

### 4.2 `<c-cache>`

`<c-cache>` is a transparent built-in component. It adds no HTML wrapper and no
component root marker of its own. When its body contains client-active Slot
content, serialization may add invisible ownership-range comments around the
body. Those comments retain the transparent boundary needed by the client
ownership protocol without changing the rendered element structure.

```html
<c-cache
  key="product-sidebar"
  c-vary="[current_user.id, locale, catalog_revision]"
  c-ttl="300"
  version="v2"
>
  <c-product-links c-user="current_user" />
</c-cache>
```

Its inputs are:

| Input | Default | Meaning |
|---|---:|---|
| `key` | required | Non-empty static or computed string naming the fragment. |
| `vary` | empty tuple | One canonical value, commonly a list, tuple, or mapping. |
| `ttl` | engine Cache default | Positive seconds, `None`, or zero. |
| `version` | `1` | Author-controlled version for this fragment contract. |
| `enabled` | `True` | A computed boolean for conditional bypass. |

Static attributes are strings. Numeric, `None`, collection, and boolean values
normally use Citry's expression form, such as `c-ttl="300"`,
`c-ttl="None"`, and `c-enabled="feature_on"`.

Citry unwraps the runtime `Const` marker from all `<c-cache>` control inputs
before validating them. Thus a literal `key="sidebar"` and an expression that
evaluates to the same string have the same fragment-key meaning. Component
variation handles `Const` differently, as section 6.2 specifies, because
component code can observe whether an input was constant.

The body is the optional default Slot. Named fills are rejected by the
built-in's Slots schema. Empty output is a valid cache value and must be
distinguished from a miss.

The fragment key does not inspect the body. The explicit `key`, `vary`,
`version`, engine namespace, and deployment generation are the complete cache
identity. This matches the useful part of Django's fragment contract without
pretending Citry can discover every value read by arbitrary nested components.
Two call sites using the same identity therefore reuse the first stored body
even when their authored bodies differ. Replayed ownership binds to the current
lexical writer. A nested source span is rebound to an equivalent occurrence in
the current fill when possible; if no equivalent text exists, Citry preserves
the archived source span as provenance rather than rejecting the valid hit.

#### Nested fragments

On an outer miss, inner cache regions behave normally and their settled result
becomes part of the outer artifact. On an outer hit, the entire outer subtree is
replayed and inner caches are not consulted. The outer TTL and version therefore
dominate while the outer entry remains valid.

Authors who need independent refresh should not put the shorter-lived region
inside a longer-lived outer entry, or should include the inner content revision
in the outer `vary` value.

### 4.3 Engine-wide Cache defaults

The built-in extension reads these engine defaults:

```python
app = Citry(
    extensions_defaults={
        "cache": {
            "ttl": 300,
            "namespace": "storefront-production",
            "generation": release_sha,
            "max_entry_bytes": 1_000_000,
        },
    },
)
```

| Field | Default | Scope |
|---|---:|---|
| `ttl` | `300` | Inherited by component and fragment configs that omit a TTL. |
| `namespace` | `None` | Application/environment identity for shared keys. Engine-only. |
| `generation` | `None` | Deployment identity. Engine-only. Change on every output-affecting deploy. |
| `max_entry_bytes` | `1_000_000` | Oversized artifacts render normally but are not stored. Engine-only. |

`namespace`, `generation`, and `max_entry_bytes` are rejected when declared in
a component's nested `Cache` class. They describe storage and deployment, not
one component.

Configuration validation is exact and happens during class or engine
initialization:

| Surface | Accepted values |
|---|---|
| component `enabled` | Exact `bool`. There is no engine-wide `enabled`; component caching remains opt-in. |
| component/fragment/engine `ttl` | `None`, or an exact `int`/`float` excluding `bool`, at least zero and representable as finite seconds. Values normalize to `float`. |
| component/fragment `version` | Exact `int` excluding `bool`, or non-empty exact `str`. |
| component `vary` | The instance method described in section 4.1. Engine-level `vary` and `version` are rejected. |
| engine `namespace` | `None` or a non-empty exact `str`. |
| engine `generation` | `None` or a non-empty exact `str`. Supplying it without `namespace` is rejected. |
| engine `max_entry_bytes` | `None` or an exact positive `int` excluding `bool`. `None` removes the policy limit, not the artifact format's absolute safety cap. |
| fragment `key` | Non-empty exact `str` after `Const` unwrapping. |
| fragment `enabled` | Exact `bool` after `Const` unwrapping. |
| fragment `vary` | Any value accepted by section 6.2 after `Const` unwrapping at the control-input boundary. |

When either `namespace` or `generation` is absent, the effective scope includes
the process-lifetime `Citry.engine_id`. Such entries can still use Redis or
DiskCache, but another engine cannot hit them. When `generation` is supplied,
`namespace` is required. Two workers share render artifacts only when both
values match.

This opt-in prevents an application from accidentally reusing old output after
a deploy. It also avoids collisions when two applications share one Redis or
Memcached database. Backend-level prefixes, such as `RedisCache(prefix=...)`,
remain recommended defense in depth.

---

## 5. Render lifecycle

### 5.1 Lookup point

The component pipeline becomes:

```text
create Component instance and bind current ownership invocation
initialize per-component extension configs
run every on_component_input hook
revalidate raw input and rebuild typed kwargs / Slots
create the current boundary context and apply current-call metadata
ask the built-in Cache extension for a lookup decision
    hit  -> replay artifact into this render
    miss -> continue
run template_data / js_data / css_data
run on_component_data
run on_render and render the template subtree
settle children and generator work
run every on_component_rendered hook
commit a complete artifact for the miss
```

The lookup is after input hooks because they are allowed to mutate raw kwargs
and slots. A key computed before those mutations could describe different
inputs from the ones that render.

Revalidation is also before lookup. The same normalized values feed the cache
variation function and every component data/render method, and a cache hit does
not bypass typed input errors.

The lookup is before data methods because skipping those methods is a primary
benefit of component output caching.

A **component-tag client binding** is a browser-side `$c-props`, `@click`, or
`@c-poll.5s` binding resolved from a nested `<c-*>` tag. Its expression or
server handler stays parent-owned, while the child supplies the component
boundary where the browser applies it.

The current boundary exists before lookup. Its newly allocated render ID,
`#c-key`, component-tag client bindings, supplied fills, invocation record, and physical
containing region belong to this call. A `Component.Cache` hit binds the
artifact root to that boundary rather than restoring those values from the
first miss. A transparent `<c-cache>` has no component root of its own; it binds
the archived body to the current Slot writer, fill, invocation, and containing
region anchors described in section 7.2.

Lookup snapshots the engine-local cache revision. After backend fetch, decode,
and staging, core checks that the revision is unchanged before applying a hit.
If it changed, the staged hit is discarded without mutation and lookup restarts
under the new revision. Publication checks the same snapshot immediately before
`set()`. A revision change during a miss lets the current render complete but
skips storage of its now-old artifact.

### 5.2 Miss state belongs to the finalize task

Core asks the built-in Cache extension directly for one of:

- no plan, when caching is disabled or bypassed;
- a `CacheHit` carrying a validated artifact;
- a `CacheMissPlan` carrying the physical key, TTL, size limit, and information
  needed to publish later.

The core stores a `CacheMissPlan` on the render-local finalize task. It does not
store it on the extension singleton or in a dictionary keyed by render ID.

After replay succeeds and the current boundary's ownership has settled, the
Cache extension emits the notify-only custom `on_component_cache_hit` hook. It
exposes the cache kind, current live component, physical key digest, stored
artifact byte size, and frame count, but not raw variation values. Observer
return values are ignored. A failing observer is logged by extension name and
exception type, later observers still run, and the committed hit remains the
render result.

### 5.3 Publication point

An artifact is built and stored only after:

- the component template or replacement settled;
- every descendant settled;
- the component's `on_render` generator completed;
- every `on_component_rendered` extension hook completed;
- ownership retirement and selection completed;
- no error occurred anywhere in the cached subtree.

The last condition includes errors swallowed by `on_render`, an extension, or
`<c-error-fallback>`. A recovered error produces valid page output, but caching
that fallback can turn a transient failure into a long-lived result. The render
tracks an error-tainted bit and skips publication by default.

Publication uses one backend `set()` after the artifact is fully encoded and
validated. A render or encoding error cannot leave a partial cache value.

### 5.4 Hook behavior on a hit

For the cache boundary component:

- instance creation, ownership binding, config initialization, and
  `on_component_input` run;
- Cache lookup and `on_component_cache_hit` run;
- data methods, `on_component_data`, `on_render`, template nodes, Slot hooks,
  attribute hooks, and `on_component_rendered` do not run.

Nothing inside the cached subtree runs. Its extension contributions are restored
from the artifact instead.

This makes a hit a real short-circuit and keeps hook names truthful.
`on_component_rendered` means a component actually rendered during this call.
Extensions that need hit metrics use `on_component_cache_hit`.

Page-wide serialization still follows the normal pipeline, including extension
`on_serialize` hooks. Dependencies emission may also call a restored component
class's `Component.on_dependencies()` through its current registry identity.
The guarantee is that cached component render lifecycle code does not run; it
is not a guarantee that serialization executes no application Python at all.

### 5.5 Backend and artifact failures

Calls to the configured `CitryCache` preserve the existing strict behavior. A
backend exception propagates. Applications that want cache outages treated as
misses can supply an adapter that implements that policy and reports the
failure through their monitoring.

An entry with invalid JSON, an unknown artifact version, invalid field types,
an incompatible extension payload, or an impossible ownership reference is not
replayed. Citry records a diagnostic and continues as a miss. It does not delete
the entry because a concurrent writer may have replaced the value between
`get()` and diagnosis. A later successful render overwrites the physical key.

---

## 6. Keys and invalidation

### 6.1 Physical key shape

Physical keys are short ASCII strings suitable for Memcached:

```text
citry:render:v1:c:<64 lowercase SHA-256 hex characters>
citry:render:v1:f:<64 lowercase SHA-256 hex characters>
```

`c` means component and `f` means named fragment. Raw fragment names, user IDs,
tenant IDs, and other variation data never appear in the physical key or normal
logs.

The digest input contains a canonical record with:

- key-schema version;
- effective application namespace and deployment generation;
- engine-local render-cache revision;
- cache kind;
- stable component `class_id` or fragment `key`;
- component or fragment `version`;
- installed extension replay-format versions;
- canonical variation value.

Component and fragment entries cannot collide even when all author-supplied
values happen to match.

### 6.2 Canonical variation encoding

The key encoder accepts a deliberately small tree:

- exact `None`, `bool`, `int`, finite `float`, `str`, and `bytes` values;
- lists and tuples, preserving order and distinguishing the two types;
- exact built-in `dict` values with exact string keys, sorted by key;
- nested combinations of the above.

Every scalar carries a type tag. Integers use signed hexadecimal, floats use an
exact stable representation, and bytes use base64. Thus `1`, `True`, `1.0`, and
`"1"` are four different values.
Dict order does not change a key. List and tuple identity does.

For component variation, a runtime `Const` wrapper has its own type tag followed
by the canonical underlying value. This matters because component code can
observe `is_const(value)`, so constant and live expression inputs can produce
different output. `<c-cache>` control inputs are unwrapped before their own
validation and variation encoding as described in section 4.2.

The encoder rejects:

- NaN and infinities;
- cycles;
- sets and unordered custom collections;
- arbitrary `Mapping`, list, tuple, or dict subclasses;
- callables and Slots;
- arbitrary objects, dataclasses, models, and values relying on `repr()` or
  `str()`.

An error names the path to the unsupported value and suggests converting it in
`Cache.vary()` or `<c-cache c-vary="...">`.

Key input also has fixed denial-of-service limits: nesting depth 32, 10,000
nodes, and 64 KiB of canonical encoded data. These are format limits, not
backend settings. Cycles, recursion overflow, or crossing any limit raises
`CacheKeyError` before backend access.

### 6.3 Automatic local invalidation

The Cache extension owns an integer render-cache revision. It begins at zero
after registry initialization and increments when runtime state makes existing
artifacts suspect, including:

- template reset;
- file reset;
- component hot replacement;
- final unregistration;
- a completed `Citry.clear()` lifecycle.

The revision participates in every key. Incrementing it makes old entries
unreachable without enumerating them. They expire or are evicted normally.

Template reset, file reset, and `Citry.clear()` hold the revision guard across
all core and extension invalidation work. Concurrent key snapshots block until
that work finishes; the revision increments in the guard's `finally` path, so
even a partially mutating reset that raises cannot leave old keys reachable.
The new revision is therefore the reset commit point, not an early hook
notification.

Every lookup and publication carries the revision snapshot described in
section 5.1. This closes the race where a template reset happens after a value
is fetched but before it is replayed or republished.

The implemented template-reset extension notification parallels
`on_files_reset`. Initial class registration during startup does not increment
the revision differently across otherwise identical workers.

Hot reload remains process-local. A worker that resets files stops using its old
entries immediately, but it does not broadcast invalidation to other workers.
Production deploys use a new configured `generation`.

### 6.4 Public exact-key helpers

`citry.ext.cache` exposes deterministic helpers for callers that need targeted
invalidation:

```python
from citry.ext.cache import component_cache_key, fragment_cache_key

key = fragment_cache_key(
    app,
    "product-sidebar",
    vary=[user_id, locale, catalog_revision],
    version="v2",
)
app.cache.delete(key)

key = component_cache_key(
    ProductCard,
    vary={"product_id": product_id, "currency": currency},
    version="price-layout-v2",
)
app.cache.delete(key)
```

The component helper accepts the already-computed semantic `vary` value. It
does not construct a component or run input hooks merely to discover a key.

V1 does not expose "delete every variant of ProductCard" or "delete every
fragment named sidebar." Those operations require a durable secondary index
with its own concurrency, expiry, and cleanup rules. Change the component or
fragment `version`, or the deployment `generation`, instead.

---

## 7. `CachedRenderArtifact`

### 7.1 Required properties

`CachedRenderArtifact` is an internal immutable value with these properties:

- encoded as deterministic UTF-8 JSON accepted by the existing string-valued
  `CitryCache` protocol;
- versioned independently from the physical key format;
- strictly validated before replay;
- contains no Python import pickle, live class, Component, CitryContext,
  CitryElement, Slot, request, provide mapping, callback, weakref, lock, or
  original OwnershipGraph;
- contains no original random render IDs;
- represents empty output without using the cache-miss sentinel;
- safe to decode concurrently and replay more than once;
- bounded by `max_entry_bytes` before backend publication;
- bounded before JSON parsing and during structural validation.

JSON avoids arbitrary-code deserialization. It does not make a writable cache
untrusted: cached HTML is still trusted application output, so cache write
access can inject markup and scripts.

Artifact format v1 has an absolute 16 MiB UTF-8 read/write cap, a structural
depth cap of 128, and a combined 100,000 frame, part, relation, and extension
record cap. Every wire string, object key, and typed artifact string must be
strictly UTF-8 representable; lone Unicode surrogates are corrupt entries, not
oversized entries. The byte length is checked before JSON parsing. Recursion
and count limits are enforced by iterative validation. `max_entry_bytes=None`
disables only the lower operator policy limit; it cannot disable these format
caps.

Format v1 requires nullable `morph_key` and `morph_mode` on every archived
descendant component invocation. The morph mode accepts only `null` and
`"ignore"`. Malformed invocation records are rejected rather than replayed
with defaults, because either default could change browser identity or range
policy. The current call's boundary invocation key and morph mode remain
call-owned and are never restored from the artifact that
populated the cache.

### 7.2 Structural shape

The exact private schema belongs to implementation, but the current version needs these
logical sections:

```text
header
  artifact version
  Citry compatibility version
  extension payload versions
  creation metadata used only for diagnostics

frames and parts
  literal HTML/text chunks
  component-frame boundaries
  serialize-time placeholders
  local instance references instead of render IDs
  physical region references

ownership
  active instance records
  parent/child and invocation relations
  fill and physical-region relations
  client binding metadata required by the client manifest
  symbolic external anchors for current-call relations

extensions
  dependencies payload
  Events payload
  payloads from explicitly replay-compatible user extensions
```

Literal HTML is stored as structural chunks around local references, not as one
string later searched with regex replacements. Authored text that happens to
look like a token can never be mistaken for a framework reference.

The exporter starts from the settled cache boundary and includes only active
records reachable within its selected physical subtree. Retired or replaced
descendants and unrelated parent or sibling records are excluded. It never
copies a `CitryContext.extra` mapping wholesale. Each participating extension
exports only its own records after filtering them to the selected active render
IDs, and strips live references such as `DependencyRecord.component_class`.

References within the selected subtree use artifact-local indices. A relation
that legitimately crosses the boundary uses one of these symbolic anchors:

- the existing cache-boundary component, for `Component.Cache`;
- the current ownership invocation;
- the current lexical Slot writer;
- the current supplied fill records, keyed by validated Slot field and fill
  occurrence, including the default fill;
- the containing physical region.

Replay resolves each anchor from the new call. This is required for a
`<c-cache>` body, which is a Slot written by its surrounding component, and for
a component cache whose default Slot came from its caller. A reference to any
other external occurrence, an unavailable anchor, or a second ownership graph
makes the subtree uncacheable in v1. Citry does not capture the first writer's
context or guess how to merge foreign graphs.

### 7.3 Replay

Replay is transactional:

1. Validate the complete artifact, all limits, symbolic references, and
   extension compatibility without mutating the current render.
2. Bind the archived component root to the already-created current boundary.
   Its render ID, component-range `#c-key`, client bindings, supplied fills, invocation metadata,
   and containing region remain those of this call. A transparent `<c-cache>`
   has no marked root of its own.
3. Reserve a fresh render ID for every archived descendant occurrence. For
   `<c-cache>`, all archived component occurrences are descendants. The current
   `Citry.id_generator` remains the single source of IDs.
4. Build an immutable replay plan containing remapped ownership records,
   frames, physical regions, and resolved external anchors.
5. Ask each payload extension to validate and stage an immutable contribution.
   Import hooks cannot mutate `CitryContext.extra`, the ownership graph, or
   other live state.
6. Recheck the engine-local revision, then atomically apply the core replay plan
   and staged extension contributions. An unexpected apply failure rolls back
   every ownership and context contribution from this replay.
7. Return an ordinary settled render contribution that serialization can
   consume without special cache knowledge.

Two replays of one artifact in the same page therefore keep their own current
boundary IDs and have disjoint descendant IDs and physical ownership regions.
No staged failure can leave ghost frames, ownership records, or extension data.

### 7.4 Serializer/core prerequisite

The current serializer identifies a component frame through
`render.context.component`. A detached artifact has no live inner Component
instances. Core therefore adds a frozen `RenderFrame` descriptor to every
`CitryRender`. It contains the render ID, stable class ID, root status, and root
marker data needed by serialization and ownership consumers.

A normal live render has both its frame and its existing live
`context.component`. The root of a `Component.Cache` hit likewise keeps the
current boundary component. Replayed inner renders expose
`context.component is None` and carry identity through `render.frame`. This is
an observable traversal contract for callers that inspect a `CitryRender` tree;
code that requires a live component must handle replayed frames explicitly.
Core serializer, ownership, dependency selection, and diagnostic consumers move
identity-only reads to `RenderFrame`.

The ownership graph likewise needs a replay import path that accepts validated
records with local references. It must not create fake Component objects solely
to satisfy current internal APIs.

### 7.5 Extension replay contract

Every installed extension declares one explicit `render_cache_mode`:

- `"deny"` means a subtree in which the extension participates is not
  publishable. This is the conservative default for user extensions;
- `"stateless"` asserts that the extension needs no render-scoped payload and
  that normal serialization hooks are sufficient;
- `"payload"` requires artifact export plus staged replay import.

Both compatible modes require a positive `render_cache_version` included in
physical key compatibility. A payload exporter receives a read-only selected
subtree view and returns strict JSON with no live-object references. Its import
hook validates against the replay ID/anchor map and returns an immutable staged
contribution; core alone commits it.

The declarative mode/version fields and their ordered physical-key
compatibility tuple ship in Phase 1. Phase 2 adds enforcement during artifact
publication plus payload export and staged replay import.

An output-affecting or context-owning extension must not declare `"stateless"`
unless the settled structural render fully captures its effect. An extension in
`"deny"` mode makes the subtree uncacheable. Citry renders normally, skips
publication, and reports which extension prevented caching. It does not infer
safety from whether a hook happens to exist.

Changing an extension's payload or replay meaning requires incrementing
`render_cache_version`. Changing application behavior still requires a new
deployment `generation`.

One ownership cleanup remains: generic replay contribution and replay-error
types currently live under `citry.ext.cache`, so Events, Dependencies, and the
extension manager import Cache-owned modules while implementing the generic
contract above. Move those neutral types into a core render-cache protocol
module. Events and Dependencies should then depend on that protocol, not on
Cache's private implementation.

---

## 8. Built-in extension interactions

### 8.1 Dependencies

The artifact must carry enough dependency information to rebuild records with
fresh component IDs and to repair any missing content-addressed script values.
It cannot store only an old `js_vars_hash` or `css_vars_hash` and assume another
process still has the payload.

The Dependencies payload therefore records stable class IDs plus the canonical
JS/CSS variable data or equivalent validated script descriptors. Replay:

- assigns the new component IDs;
- recomputes or verifies content hashes;
- repopulates missing dependency-script cache values;
- restores root CSS-variable markers with the content hash, not a rewritten
  render ID;
- appends ordinary `DependencyRecord` equivalents to the current context.

Export selects records by the final active render-ID set described in section
7.2. A dependency from the writer, a parent, an earlier sibling, or a retired
replacement child is not copied merely because it shares a context mapping.
The serialized payload contains stable class IDs and data only, never the live
`DependencyRecord.component_class` reference.

Class-level assets resolve through the current registered class only after the
artifact generation and class identity are validated. No cache entry retains a
component class.

Using the same engine cache for render artifacts and dependency scripts removes
the backend disagreement that caused django-components' silent post-deploy
loss. Carrying replay data still matters because either kind of entry may be
evicted independently.

### 8.2 Events and client ownership

Cached markup with Events behavior must not reuse an old instance ID. Stateless
Events entries are rebuilt directly with the new ID and stable class ID.

For stateful Events components, the artifact stores the already-protected state
token and public values, not an arbitrary live State object. Replay validates
the token against the current class and secret configuration, recovers the
state through the normal Events codec, and mints a fresh token for the new
instance. An expired, missing server-held, or incompatible token makes the
artifact a miss.

Events export follows the same final active-ID selection. Records owned by
parents, Slot writers, siblings, and retired descendants stay outside the
artifact. Boundary component-tag client bindings and `#c-key` behavior are
rebuilt from the current call; they are not copied from the occurrence that
populated the entry. Archived descendant invocations carry their own required
nullable `morph_key` and `morph_mode`, because that metadata was authored
inside the cached subtree and is needed to reproduce its ownership graph
exactly.

The ownership payload restores active instances, invocations, fills, regions,
and init relations under fresh IDs. The client manifest generated from a replay
must be indistinguishable from one produced by a fresh render except that the
cached components' render lifecycle did not run. Page serialization and
dependency discovery can still execute the hooks called out in section 5.4.

No public cache feature ships for interactive subtrees until this path is
covered by browser-level tests. Silently dropping Events metadata is not an
acceptable reduced first release.

### 8.3 Debug

Debug highlighting includes render IDs in labels and inserts serialize-time
markers. It is a development transform, not cacheable application output.

When component or slot highlighting is active on any registered component, the
Cache extension conservatively bypasses lookup and publication for the engine.
This avoids hiding a highlighted descendant behind an outer hit, including for
dynamic component selection. Shared workers must still use homogeneous Debug
configuration and change the deployment generation when output-affecting
configuration changes. A future Debug toolbar can observe
`on_component_cache_hit` for hits; a complete hit and miss UI needs the future
runtime diagnostic collector.

### 8.4 Provide, template globals, and Slots

Values from `provide()`, `inject()`, template globals, render globals, and Slot
writer scope have already affected the artifact on a miss. They do not flow into
replayed content later. The author must vary the entry on every such value that
can change the result.

Replaying into a different parent or provide scope is valid only because the
cached subtree is a settled output contribution. Current outer provides still
apply to uncached siblings and descendants rendered after the cache boundary;
they do not retroactively change archived inner output.

A Slot writer is nevertheless part of structural ownership, not cached data.
Artifact export represents that relationship through the lexical-writer and
fill anchors. Replaying the same fragment under a second writer binds to that
writer and must not retain the first writer's render ID, context, provide
mapping, sibling metadata, or ownership graph.

### 8.5 Const and compiled-template caches

The compiled template and const-body caches remain independent. A miss can use
them while producing the artifact. A hit skips template generation entirely.

Render-cache invalidation does not need to delete compiled templates, and a
template reset must invalidate both layers through their respective revision or
eviction paths.

---

## 9. Concurrency and capacity

### 9.1 Concurrent misses

The v1 algorithm is:

```text
get key
if hit: validate and replay
if miss:
    render completely
    encode completely
    set key
    return the render
```

Two threads or workers can both miss, both render, and both store complete
artifacts. The later write wins. A correct cache contract requires both results
to be semantically valid for the same variation key.

Citry does not hold a lock across user component code. This avoids deadlocks
with nested caches, recursion, async-host bridges, and backends whose lock lease
expires while a slow render continues.

Cross-worker single-flight, stale-while-revalidate, proactive refresh, and cache
warming are later features. They require their own ownership, lease-expiry,
failure, and stale-data contracts.

### 9.2 Thread-safe local backend

The built-in `InMemoryCache` is thread-safe. Its get, set, delete, has, expiry,
and LRU updates use one internal lock. User rendering never happens while that
lock is held.

This is a prerequisite correction to the existing backend, not a new public
cache method.

### 9.3 Size and eviction

The artifact's UTF-8 byte length is checked before `set()`. An oversized entry
does not fail the render and is not split across keys. A diagnostic reports its
size and configured limit without logging variation values or HTML.

Every backend may evict an entry at any time. A cache miss is always safe and
re-renders. The default in-memory backend remains unbounded unless configured
with `max_entries`; production documentation should recommend an explicit
capacity or shared backend.

V1 intentionally shares one backend capacity among render artifacts,
dependency-script values, and optional server-held Events state. A cache-heavy
workload can therefore increase misses in the other tiers. Dependencies replay
can repopulate an independently evicted script value from the artifact. An
artifact that refers to missing server-held Events state is itself a miss and
fresh render. Operators must size the backend for all three tiers; separate
named backends remain deferred.

The Redis adapter applies central TTL validation and `math.ceil()`, so a
fractional TTL never expires earlier than requested.

---

## 10. Security and correctness rules

The user guide must give these rules a prominent place:

1. Include every caller-dependent value in the key. User, tenant, permission,
   locale, timezone, feature flag, experiment, CSRF value, CSP nonce, and
   provide data are common examples.
2. Cache only output that may be reused for every caller sharing that key.
3. Treat the cache backend as trusted application infrastructure. Write access
   can inject trusted HTML even though Citry never unpickles values.
4. Never use `repr()` or `str()` of an arbitrary object as a variation value.
   Convert it to a stable identifier.
5. Change the deployment generation whenever component code, templates,
   extensions, helpers, or global configuration can change rendered output.
6. Change a component or fragment version for targeted semantic invalidation.
7. Remember that a longer-lived outer cache suppresses all inner cache lookups.
8. Cache values are optimization data, never the authoritative home of
   application state.

Physical keys and ordinary diagnostics expose only digests. The artifact itself
contains rendered HTML and may contain protected Events state or dependency
data, so normal cache access controls and retention policies still apply.

---

## 11. Introspection and diagnostics

The Cache extension publishes component introspection metadata through the core
API designed in [`component_introspection.md`](component_introspection.md).
Its extension-owned `introspection_version = 1` object has this exact shape for
ordinary components:

```json
{
  "enabled": true,
  "ttl": 60.0,
  "version": {"kind": "string", "value": "card-v2"},
  "variation": "custom",
  "default_variation_slot_source": "not-applicable"
}
```

`ttl` is a normalized finite float or `null` for no expiry. Integer versions
use signed `hex()` text with `kind="integer"`; string versions retain their
exact text with `kind="string"`. The tagged representation preserves valid
integers beyond JSON's portable safe range and distinguishes integer `1` from
string `"1"`.

`variation` is `default` or `custom`. With default variation,
`default_variation_slot_source` is `none` for a closed-empty Slots schema and
`possible` for absent/open, opaque, or non-empty Slots schemas. With custom
variation it is `not-applicable`. This is declaration-level possibility, not a
claim about effective content in a future call, which could also come from a
supplied fill, default factory, or input hook.

Inspection does not execute `Cache.vary()` or factories, load assets, render,
or expose engine namespace, generation, capacity, physical keys, or variation
values. The exact transparent `<c-cache>` built-in publishes no Cache extension
entry because its core built-in fields and Kwargs schema already describe the
fragment surface; `Component.Cache.enabled` would be misleading there.

Runtime diagnostics should record:

- hit, miss, bypass, corrupt-entry, incompatible-entry, oversized-entry, and
  store outcomes;
- component class for component entries;
- physical key digest;
- artifact byte size and replay frame count;
- the reason an extension made a subtree uncacheable.

Fragment diagnostics use only the physical key digest, never the authored or
computed fragment name. Diagnostics must not record raw varied values, cached
HTML, Events tokens, or protected state.

Phase 3 records these outcomes on the `citry` logger at DEBUG level with safe
structured `LogRecord` fields. It keeps no engine-level history or counters.
The stable outcomes are `hit`, `miss`, `bypass`, `corrupt-entry`,
`incompatible-entry`, `oversized-entry`, `store`, `store-skipped`, and
`store-error`. Reasons are fixed codes such as `ttl-zero`, `debug-active`,
`error-tainted`, `revision-changed`, `extension-denied`, and
`backend-set-failed`; arbitrary exception messages are not included. The
notify-only hit context is public from `citry.ext.cache` as
`OnComponentCacheHitContext`.

---

## 12. Test migration and acceptance coverage

### 12.1 `test_component_cache.py`

| Upstream behavior | Citry disposition |
|---|---|
| enabled / disabled | Port. |
| TTL | Port with Citry's `None`, positive, and zero rules. |
| custom cache name | Defer; one engine-owned backend in v1. |
| cache by input | Port using canonical variation. |
| input hashing | Replace string hashing with type-safe collision tests. |
| override hash | Replace with `Cache.vary()`. |
| cached component inside include | Replace Django include specifics with nested Citry components and different parents. |
| cache fills and string Slots | Replace with explicit slot-variation coverage. |
| callable Slot error | Replace with the general "slots require explicit vary" rule. |
| render error does not cache | Port and extend to recovered errors. |
| short-circuit leak | Replace with finalize-plan and weak-lifetime tests. |

The old django-components global `provide_cache` lifetime tests parked beside
this family are not render-cache tests. Citry must not introduce a global
provide cache to satisfy them. Replace only their general lifetime lesson:
cached artifacts retain no provide payload or component class.

### 12.2 `test_django_cache_tag.py`

| Upstream behavior | Citry disposition |
|---|---|
| top-level miss and hit | Port to `<c-cache>`. |
| nested miss and hit | Port, including outer-hit dominance. |
| explicit `{% load cache %}` | Drop as Django-only. |
| Slot/component inside cached body | Port. |
| timeout expression and `None` | Port with `c-ttl`. |
| one and several variation values | Port through one structured `vary` input. |
| named backend | Defer. |
| frozen inner render ID | Reverse the assertion: every replay gets fresh IDs. |
| body error does not poison cache | Port. |

### 12.3 Citry-specific acceptance matrix

The public feature is not complete until tests cover:

**Key and config correctness**

- exact type distinctions: `1`, `True`, `1.0`, and `"1"`;
- delimiter-shaped strings and nested collection boundaries;
- dict order independence and sequence order dependence;
- unsupported objects, cycles, NaN, infinity, and callables;
- static `Const` inputs, including literal fragment keys and TTLs;
- component variation distinguishes a constant input from an equal live
  expression input;
- default kwargs variation uses typed defaults and factories after input-hook
  mutation and revalidation;
- supplied Slots and Slot defaults/factories that produce content are rejected
  without custom variation, while an optional `None` Slot is allowed;
- namespace, deployment generation, local revision, and author version;
- fragment and component key domains never collide;
- exact-key helper deletion.

**Replay identity**

- a component-cache hit retains the new call's boundary ID while every archived
  descendant gets a fresh ID;
- one artifact embedded twice on one page gets distinct boundary and descendant
  IDs as appropriate;
- nested and multi-root components preserve correct marker inheritance;
- a hit under a different parent connects to that parent ownership graph;
- the same component hit at two call sites uses each site's `#c-key`, boundary
  event client bindings, supplied fills, and invocation metadata;
- a `<c-cache>` Slot body replayed under two different lexical writers binds to
  the current writer and retains no first-writer IDs, provides, sibling records,
  or graph references;
- a literal `<c-slot>` inside that body follows the transitive supplied-Slot
  path to the caller's writer, including nested components in the caller fill;
- physical Slot/fill regions are distinct per replay;
- authored text resembling an internal reference stays literal;
- empty output is a hit, not a miss;
- concurrent replays of one decoded artifact do not mutate shared data;
- public `CitryRender` traversal sees a live current boundary component and
  `context.component is None` plus a complete `RenderFrame` for replayed inner
  frames.

**Extensions**

- class JS/CSS and Dependencies appear on hits;
- JS/CSS variables survive a simulated process-cache loss and are repopulated;
- content hashes stay content hashes while render IDs change;
- dependency and Events records belonging to parents, writers, siblings, or
  retired replacement children are excluded from the artifact;
- stateless and stateful Events entries receive fresh IDs and valid tokens;
- ownership and Events browser behavior work when one artifact appears twice;
- active Debug highlighting bypasses publication;
- an output-affecting extension without replay support makes the subtree
  uncacheable with a diagnostic;
- extension payload version changes cause a miss;
- failure while validating or staging each extension import leaves no ownership
  records, frames, physical regions, or `CitryContext.extra` contributions.

**Failure and lifetime**

- every render, child, generator, and extension error avoids publication;
- a recovered error result is not stored;
- corrupt and unsupported entries safely miss;
- a corrupt value replaced concurrently by a valid writer is never deleted;
- backend get/set failures follow the strict propagation contract;
- oversized entries render successfully and skip storage;
- unregister, hot replacement, reset, and `Citry.clear()` stop local reuse;
- a local revision change during fetch/staging abandons the hit and retries
  under the new revision, while a change before publication skips the old set;
- cached entries hold no strong reference to component classes, instances,
  requests, Slots, contexts, or provide data;
- a component class is collectable after unregister even if it previously
  produced cached output.

**Concurrency**

- the built-in memory backend is race-safe under concurrent get/set/expiry/LRU;
- concurrent misses may render more than once but publish only valid complete
  artifacts;
- nested same-key misses do not deadlock;
- no backend or lifecycle lock is held while user render code runs.

**Limits and shared capacity**

- key depth, node, and encoded-byte caps reject before backend access;
- oversized artifact strings reject before JSON parsing, and structural caps
  reject deeply nested or record-heavy payloads transactionally;
- malformed UTF-8 strings and keys are controlled corrupt misses, and a failed
  late replay removes any newly created repair key marked for rollback;
- dependency scripts are repopulated after their independent eviction;
- missing server-held Events state turns an otherwise valid artifact into a
  miss;
- render-artifact churn cannot make eviction in the shared backend incorrect.

The Events and ownership cases require end-to-end browser coverage, not only
HTML string assertions.

---

## 13. Implementation phases

### Phase 0: correct the design baseline (complete 2026-07-22)

- Update older docs that literally promise raw `CitryRender` or
  `CitryElement` caching.
- Update the migration ledger with the dispositions in section 12.
- Add a small invariant test proving that live `CitryRender` serialization
  preserves IDs and is not the cache replay API.

### Phase 1: key and backend prerequisites (complete 2026-07-22)

- Add strict TTL normalization shared by Cache config and `<c-cache>`.
- Complete post-`on_component_input` revalidation so raw and typed inputs agree.
- Add the typed canonical encoder and physical key builders.
- Add key and artifact safety caps enforced before recursive work or JSON
  parsing.
- Add an inert built-in Cache extension that owns engine defaults, effective
  local/shared scope, and the local revision. Its per-component config surface
  is enabled in Phase 3.
- Make `InMemoryCache` thread-safe.
- Fix Redis TTL conversion to round upward.
- Add ordered extension cache-compatibility declarations used by every key.
- Add public exact-key helpers.

### Phase 2: replay artifact and core checkpoint (complete 2026-07-23)

- Add `RenderFrame` to every `CitryRender`, migrate identity-only consumers, and
  document traversal of replayed inner frames.
- Add immutable artifact structs, deterministic JSON encoding, and strict decode
  validation.
- Add selected-active-subtree export, symbolic external anchors, and
  transactional ownership import with current-boundary/fresh-descendant replay.
- Add the post-input lookup and post-finalization commit points.
- Add revision snapshot checks before replay and publication.
- Track error-tainted subtrees.
- Enforce the Phase 1 extension deny/stateless/payload declarations and add
  immutable staged imports.
- Implement Dependencies and Events payload export/import.
- Complete replay, lifetime, corruption, concurrency, and browser tests before
  adding a public way to enable caching.

### Phase 3: `Component.Cache` (complete 2026-07-23)

- Enable the built-in Cache extension's nested Config validation and render
  behavior.
- Implement complete typed-default variation and instance `Cache.vary()`.
- Reject implicit variation for every effective Slot content source.
- Add hit notification and diagnostics.
- Port the applicable `test_component_cache.py` cases.

### Phase 4: `<c-cache>` (complete 2026-07-23)

- Add the per-engine reserved transparent component.
- Implement key, vary, TTL, version, enabled, and default-body behavior.
- Add nested-cache and outer-hit contracts.
- Port the applicable `test_django_cache_tag.py` cases.
- Delay extension-context merges for caller-owned Slot bodies until their
  deferred descendants settle, so fragment artifacts include complete
  Dependencies, Events, Debug, and user-extension state.
- Retain and physically cap transparent cache boundaries when client-active
  descendants refer to their Slot regions, and reject dangling parent-region
  references while building the ownership manifest.
- Carry each deferred occurrence's physical parent through rendering and
  finalization, including Python-composed render-hook replacements, so nested
  cache Slot regions preserve their physical ancestry on misses and replayed
  outer hits.

### Phase 5: public documentation and introspection (complete 2026-07-23)

- Replace the current user-guide statement that Citry has no per-component
  output caching.
- Document shared backend, namespace, generation, capacity, and security rules.
- Add Cache extension introspection metadata.
- Add examples for per-component, per-user fragment, locale variation, exact
  deletion, version invalidation, and intentionally uncached Slots.
- Keep the completed migration-family links aligned with the public guide and
  introspection examples.

---

## 14. Deferred work

These features are deliberately outside v1:

- named cache backends;
- distributed single-flight or locks;
- stale-while-revalidate and proactive refresh;
- cache warming and bulk APIs;
- sliding expiry through automatic `touch()`;
- a distributed index for deleting every variant;
- automatic source-code or template fingerprinting as a replacement for deploy
  generation;
- async cache methods before Citry has an async render pipeline;
- arbitrary-object key serializers;
- automatic slot-source or captured-context hashing;
- caching recovered error fallbacks;
- response and event-GET caching.

Each can be layered on the artifact and key contract later without changing
what a v1 hit means.

---

## 15. Alternatives rejected

### Cache final HTML

Rejected because it freezes IDs and render-local dependency metadata. This is
the known django-components failure mode.

### Cache a raw `CitryRender`

Rejected because it preserves IDs, retains live objects and contexts, mutates
during serialization, cannot use the string cache backend, and is unsafe for
concurrent replay.

### Cache a `CitryElement`

Rejected as output caching because it runs the expensive render again. Retaining
template-created elements also retains Slot and ownership state.

### Pickle a render object

Rejected because Slots and extension state are not generally serializable,
class identity is fragile across deploys, and cache write access would become
Python code-execution access.

### Ship local-only live-object caching first

Rejected. It would establish different hit semantics for local and shared
backends, preserve the lifetime and identity bugs, and make the later safe
artifact a breaking change.

### Automatically hash slot source

Rejected because source identity does not include captured caller values. It
would make an unsafe case look supported.

### Automatically fingerprint all Python behavior

Rejected as a correctness guarantee. A source hash cannot reliably capture
database state, helper modules, feature configuration, template globals,
extension behavior, dynamically defined classes, or external services. Explicit
deployment generation and semantic versions are honest and operationally
predictable.

### Copy Django's named backends now

Deferred. Citry currently has one engine-owned cache protocol and its dependency
system benefits from sharing the same store as render artifacts. A named map
needs a separate ownership, configuration, and shutdown contract.

### Lock every miss

Rejected for v1. The current backend protocol has no portable distributed lease,
and holding an engine lock across user rendering risks recursion and deadlock.
Duplicate work is the smaller, documented cost.

---

## 16. Final recommendation

Build the replay artifact and core checkpoint first, then expose
`Component.Cache`, then `<c-cache>`. Do not use a string or live-object shortcut
to make the migration tests pass early.

The resulting user model stays small:

- component authors enable `Component.Cache`, choose TTL/version, and describe
  nontrivial variation;
- template authors wrap a region in `<c-cache key=... c-vary=...>`;
- operators choose capacity and, for shared workers, set namespace plus deploy
  generation;
- Citry owns safe physical keys, complete publication, detached replay, fresh
  identities, and extension metadata restoration.

That provides the two requested caching surfaces while resolving the exact
identity, lifetime, slot, deploy, and dependency problems found upstream.
