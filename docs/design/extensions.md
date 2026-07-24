# Design: the extension (plugin) system

**Status (2026-07-23): built, including the component caching short-circuit.** This
document is the design for citry's extension/hook system, adapted from
django-components and reshaped for citry's architecture (Citry-instance scoping,
the `CitryRender` struct pipeline, no Django). The system (`Extension`,
`Extension.Config`, `ExtensionManager`, `CitrySettings`, `ExtensionCommand`,
the `On*Context` types, the lifecycle/registration/render/template/slot/JS/CSS
hooks, the `emit` mechanism for extension-owned custom hooks,
`on_render_context_merge`/`on_serialize`, and `Extension.urls`) is
implemented; see the impl-log entries in
[`migration_djc.md`](migration_djc.md). The Cache extension's replay format
and `Component.Cache` path are specified in [`caching.md`](caching.md).

For the broader migration context see [`migration_djc.md`](migration_djc.md).
For the render model the render-hooks plug into see [`component_rendering.md`](component_rendering.md).
For operating rules see [`/CLAUDE.md`](../../CLAUDE.md).

Upstream references: django-components
[#829](https://github.com/django-components/django-components/issues/829)
(extensions architecture),
[#1144](https://github.com/django-components/django-components/issues/1144)
(media as an extension),
[#1213](https://github.com/django-components/django-components/issues/1213)
(extensions specify HTML attribute rules),
[#1230](https://github.com/django-components/django-components/issues/1230)
(scoped CSS),
[#1444](https://github.com/django-components/django-components/issues/1444)
(head-tag extension). Prior art:
[`extension.py`](../../packages/py/citry/_djc_reference/extension.py) (1555 lines).

---

## 1. Prior art (what was searched)

In `packages/py/citry/_djc_reference/`:

- **`extension.py`** is the whole system: `ComponentExtension` (base + hook
  methods), `ExtensionManager` (module-global singleton calling each hook on every extension),
  `ExtensionComponentConfig` (the `Component.View` nested-class mechanism),
  16 `On*Context` NamedTuples, plus `ComponentCommand` / `URLRoute` plumbing.
- **Scoping is a module global** (`extensions = ExtensionManager()`,
  `extension.py:1533`), initialized from Django `apps.ready()` via `_init_app`
  (`:1261`). The deferral machinery (`store_events`, `_initialized`, `_events`
  flush, `:1087`, `:1327`) exists **only** to survive Django's app-load order.
  The `_init_app` URL-resolver block (`:1269-1306`) is Django-specific.
- **`on_registry_created` / `on_registry_deleted` are fired by
  `component_registry.py` but implemented by no extension** (grep: only the
  base definition and the firing site exist). Confirms they can be dropped
  (section 6.3).
- **The `<name>_class` escape hatch** (`extension.py:1176`) mirrors the legacy
  `media_class` attribute (`component_media.py:575,640`). It exists for
  parity with that old API; with no such legacy in citry it can be dropped
  (section 5.3).
- **The two-job framing of `on_component_input`** (mutate inputs *and*
  short-circuit the render - that is, skip rendering it and return a substitute,
  such as a cached result) lives in its docstring (`extension.py:717-784`),
  with the memory-leak footgun the conflation causes. The maintainer's proposal
  to split it is **django-components#1141 "[v2] Ideas", item R6** ("Elevate
  component caching to first-class lifecycle hooks, instead of overloading
  `on_component_input`"): `on_component_input` regains a single responsibility
  (inspect/mutate inputs); a dedicated cache decision takes over
  "compute key / decide whether to render" (explicit short-circuit); and a
  hit notification lets *other* extensions observe the short-circuit. Citry's
  built-in Cache extension now owns the decision directly and emits only the
  notify-only `on_component_cache_hit` custom hook. Leak lineage:
  django-components#1607 (leak found) -> #1648 (fix: bind per-render state to the
  component lifetime) -> #1649 (docs warning). Section 7.1 carries R6 into
  citry's extension-owned-hooks model.

Places in citry where hooks will attach: `ComponentMeta.__new__`
([`component.py`](../../packages/py/citry/citry/component.py));
`Citry.register`/`unregister` ([`citry.py:82`](../../packages/py/citry/citry/citry.py));
`render_impl` ([`component_render.py:75`](../../packages/py/citry/citry/component_render.py));
`_get_compiled_template`/`_compile_template` (`:185`,`:206`);
the `_merge_dependencies` call (`:277`, already TODO-marked "replace this direct
call with an extension hook"); and `CitryContext.extra`, the tree-wide bag
reserved "for extensions."

---

## 2. Central decision: the manager is scoped to the `Citry` instance

DJC's manager is a module global. Citry's
[#1413](https://github.com/django-components/django-components/issues/1413) rule
is that **all engine state lives on the `Citry` instance**. So each `Citry`
**owns an `ExtensionManager`**; extensions are passed at construction:

```python
app = Citry(extensions=[MyExtension, "my_pkg.ext.OtherExtension"])
app.extensions                 # -> the ExtensionManager (not the raw list)
app.settings.extensions        # -> the immutable spec tuple (see 2.1)
```

Every instance (including the default module-level `citry`) also carries the
**built-in extensions**: a fixed set (`extension.py`'s `_builtin_extensions()`) the manager prepends
to the user's spec, with their names reserved. The built-ins are `cache`,
`dependencies`, and `events`. The `cache` extension owns key and invalidation
state plus the opt-in `Component.Cache` output-cache configuration;
`dependencies` is described in [`asset_loading.md`](asset_loading.md) section 7.
Beyond the built-ins, the
default instance has no extensions; a user who wants more constructs their own
`Citry(extensions=[...])` and assigns components to it
(`class C(Component): citry = app`). Same test-isolation model as the registry.

**This deletes DJC's deferral machinery entirely.** There is no `apps.ready()`
race in citry: a component class is bound to its `Citry` (and thus its
extensions) at definition time in the metaclass, so the extensions are always
present when a hook fires. `store_events`, `_initialized`, `_events`,
`_init_app`, and the replay loop are all dropped.

### 2.1 Where extensions live, and immutability

- **`Citry.extensions` is the `ExtensionManager`** (the thing that calls each
  hook on every extension). It is *not* the list of extensions. (An earlier draft
  conflated the two; corrected.)
- **The raw `extensions=` spec lives in the settings** (section 5.2's
  `CitrySettings`), stored as an **immutable tuple**. The `ExtensionManager`
  builds its instances from that tuple, and also holds the instantiated
  extensions as a tuple (not a mutable list).
- **No post-construction mutation.** Extensions are fixed at construction;
  mutating them afterward is undefined behavior. The tuple storage makes the
  intended-immutability explicit and blocks the obvious accidental `.append`.

---

## 3. Hook contexts: frozen dataclasses, minimal surface, `citry` + `component`

### 3.1 Frozen dataclasses

`@dataclass(frozen=True, slots=True)`, threaded across extensions with
`dataclasses.replace()`. Consistent with citry's metaclass (which already
converts inner `Kwargs`/`Slots` to dataclasses) and flagged per migration
principle #5. `frozen` blocks accidental field reassignment; where a hook is
*meant* to mutate inputs (adding a kwarg), it mutates the contained `dict`,
whose contents are not frozen.

### 3.2 Minimal surface: pass `citry` + `component`, derive the rest

Every context that concerns a specific render carries **`citry`** (the primary
handle extensions reach for: components, settings, caches) and, when a component
instance exists, **`component`**. Fields trivially derivable from those are
**dropped**:

- `component_class` is `type(component)`; `component_id` is `component.id`. Both
  dropped from the per-instance render hooks. (`component.id`, `component.kwargs`,
  etc. are all on the instance.)
- Component registration and lookup are available on `citry`, so no separate
  state object is passed (section 6.3).

Class-lifecycle hooks have no instance, so they carry **`citry`** +
**`component_class`** (full name; section 3.3).

`citry` itself is technically derivable (`component.citry`), but it is passed
explicitly because it is the handle extensions use most; making them write
`ctx.component.citry` everywhere is poor ergonomics. This is the one deliberate
redundancy.

### 3.3 `component_class`, not `component_cls`

Use the full word **`component_class`** on the contexts that carry a class.
(DJC marked `component_class` for deprecation in favor of `component_cls`;
citry keeps the readable full name.)

---

## 4. Naming

- **`Extension`** - the base users subclass. (`CitryExtension` was the
  considered alternative; `Extension`/`ExtensionManager`/`ExtensionCommand`/
  `Extension.Config` reads consistently.)
- **`Extension.Config`** - the per-component nested-config base (DJC:
  `ComponentConfig`). Shortened to `Config`: a user writes `class View:` and the
  manager rebuilds it as a subclass of `Extension.Config`.
- **`ExtensionManager`** - owned by `Citry`.
- **`ExtensionCommand`** - the CLI-command base (DJC: `ComponentCommand`). The
  CLI design that builds on it (the command runner, `Citry.commands`
  aggregation, and the `citry` executable) is
  [`extensions_commands.md`](extensions_commands.md).

---

## 5. The per-component config (`Extension.Config`)

The `Component.View` / `Component.Cache` mechanism: an extension named `"view"`
(`class_name == "View"`) lets a user define a nested `class View:` on a
component. Citry preserves the authored class, combines it with declarations
from the component's C3 MRO, then builds the effective class on the extension's
`Config` (with the component bound). That effective class is instantiated per
render and attached as `component.view`.

Nested declarations inherit automatically. The child does not repeat its
parent's nested class in the base list:

```python
class Parent(Component):
    class View:
        density = "comfortable"

        def label(self):
            return "parent"


class Child(Parent):
    class View:
        color = "blue"

        def label(self):
            return super().label() + ":child"
```

`Child.View` sees `color`, `density`, and both method implementations. For
multiple component bases, the nested declaration classes are bases in the same
C3 order as their component owners. A nearer declaration wins an attribute
conflict. An explicit `View = None` stops component-level inheritance at that
point while retaining the current Citry instance's global defaults and the
extension's factory defaults.

Each installed extension owns one valid Python `class_name`. Those names must
be unique, and extensions cannot claim the core schema names or the Events
extension's special `State` declaration. Engine construction rejects a
collision before any component can be defined.

Citry keeps the original nested class objects in the effective MRO. It does not
copy their namespaces, so descriptors, zero-argument `super()`, source paths,
and class identity continue to refer to the authored declarations.

An extension with a domain-specific merge can consume the source records
directly. The built-in Dependencies extension does this: its `extend` setting
walks and cuts individual component or reusable definition-base branches, so
it does not use the generic class composition rule for its JS/CSS entry lists.
Relative entries remain anchored to the class that authored that branch.

Captured nested declarations are immutable on a concrete component class.
Rebinding or deleting `Kwargs`, `State`, an extension config class, or another
recognized nested declaration after class creation raises `AttributeError`.
Define a new component subclass to change the declaration chain. This keeps
runtime schemas, extension metadata, and the preserved source records in one
consistent generation.

### 5.1 Component back-reference: keep the weakref + optional component

DJC stores a **weakref** to the component (`_component_ref = ref(component)`)
with a `.component` property - to avoid a component->config->component cycle, and
to support extensions that run **outside** the component lifecycle, where there
is no component (`component=None`).

An earlier draft of this doc proposed dropping both (strong ref, no `None`
case). **That was wrong:** citry will port DJC's extensions, including
**Storybook, which runs out-of-lifecycle** - so `component=None` is a real,
required case. The weakref + optional component **stay**.

The only cleanup is ergonomic: a tidier `__init__` and `.component` that
distinguishes the two `None` reasons with clear errors -

```python
def __init__(self, component: Component | None) -> None:
    self._component_ref = ref(component) if component is not None else None

@property
def component(self) -> Component:
    if self._component_ref is None:
        raise RuntimeError(f"{type(self).__name__} runs outside a component lifecycle (no component)")
    component = self._component_ref()
    if component is None:
        raise RuntimeError("Component has been garbage collected")
    return component
```

### 5.2 Three-level config defaults, on a real settings schema

Per the maintainer's call, citry gets a **real settings schema object now**
(not a plain `**settings` dict). Introduce a frozen `CitrySettings` dataclass as
the first concrete schema; it grows field-by-field as the engine does. Initial
fields relevant here:

```python
@dataclass(frozen=True, slots=True)
class CitrySettings:
    extensions: tuple[type[Extension] | Extension | str, ...] = ()
    extensions_defaults: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    # ... more fields added as subsystems land
```

`Citry(extensions=[...], extensions_defaults={...})` validates and freezes these
into `Citry.settings` (the `extensions` spec lives here as a tuple, section 2.1).
This replaces the placeholder `self._settings` dict.

The per-component config then merges all three layers:

1. **Factory defaults** - attributes on the extension's `Config` base.
2. **Global defaults** - `settings.extensions_defaults["view"]`.
3. **Component-level** - the user's nested `class View:` on the component.

Precedence: component-level > global defaults > factory. The effective base
order is the active authored `View` classes in component C3 order, followed by
`GlobalDefaults` and `Extension.Config`.

Field names at both user-facing levels (the component's nested class and the
global defaults) are validated at declaration time; see 5.4.

### 5.3 Escape hatch dropped

The `<name>_class` attribute override (DJC `extension.py:1176`) is dropped: it
only existed to mirror the legacy `media_class` API. The supported way to change
the base is the obvious one:

```python
class MyComp(Component):
    class View(SomeOtherBase):   # just subclass directly
        ...
```

### 5.4 Config field validation (`Extension.validate_config_fields`)

The config surface is deliberately permissive: a component's nested config
class and an `extensions_defaults` entry can carry practically any fields,
even methods. The cost is that, left alone, nothing catches a bad key (say
`_guardd`, a typo of the events extension's `_guard`) until it surfaces as a
confusing downstream error. A static allowed-keys set per extension is not
flexible enough to fix that: the events extension accepts any callable under
any unprefixed name (those are its event handlers), which no fixed set of
names can express.

So the base class carries an overridable method instead:

```python
class Extension:
    def validate_config_fields(self, fields, *, component=None) -> None: ...
```

`fields` maps each declared field name to its declared value. The framework
calls the method once per declaration, at declaration time:

- **At engine construction**, with the extension's entry in the
  `extensions_defaults` setting (`component=None`). A bad key in the setting
  fails at startup, with the error naming the extension and the setting.
- **At component class definition**, once per authored declaration for the
  receiving Citry instance, including declarations supplied by reusable
  definition bases (`component` is the concrete component class). This runs before
  `on_component_class_created` reaches any extension and before the nested
  class is rebuilt (5.2), and the error names the component and the nested
  class. Framework members are never presented as fields: the `Config` base's
  attributes and the classes the rebuild itself synthesizes (the rebuilt
  config class, the defaults holder) are excluded from the enumeration.

The base implementation accepts everything, which keeps the permissive
behavior for any extension that does not override it. An override raises
`ValueError` on a bad field, and because both declaration sites are checked,
every field name is known-valid by the time the config class is rebuilt and
instantiated.

The worked example is the events extension's two-tier rule:

- **Underscore names are configuration** and must be one of the recognized
  config attributes (`_guard`, `_context`, `_csrf`, `_methods`, `_debounce`,
  `_throttle`, `_topics`). An unknown underscore name fails with a "did you
  mean" hint (`'_guardd' is not a recognized Events config attribute; ...
  Did you mean '_guard'?`). On a component's `Events` class an underscore
  `def` is exempt: those are private helpers.
- **Unprefixed names are event handlers** and must be callable, so a
  non-callable value under a handler-looking name fails at class definition.
  In `extensions_defaults` unprefixed names are rejected outright: event
  handlers are defined on each component's nested `Events` class, and this
  design has no global default handler.

---

## 6. Hook firing: where, and the registry rethink

### 6.1 Class lifecycle

`ComponentMeta.__new__` snapshots the authored nested declarations and builds
the core schema classes, then fires `on_component_class_created`, runs the
extension config-class setup (`_init_component_class`), and registers. A
class-created hook reads the preserved source chain with
`ctx.nested_declarations(name)`; it never needs to infer authored declarations
from a config attribute that Citry later replaces. Deterministic
cleanup follows `on_component_unregistered`; garbage collection itself runs no
extension code because Python may invoke it while arbitrary application locks
are held. `Citry.clear()` remains a bulk engine teardown and does not emit
per-component unregistration hooks. Extension metadata that can refer back to
its component is stored on the component class itself, so clearing the registry
leaves only a collectible class-owned cycle rather than a weak-map value that
retains its own key.

### 6.2 Render

`render_impl`: after instance creation, run `_init_component_instance` (attach
`component.<name>` configs), then `on_component_input` (mutate) and the
short-circuit hook (section 7.1); after `template_data`, `on_component_data`;
after the body builds into a `CitryRender`, `on_component_rendered`.

### 6.3 Per-engine setup uses `on_extension_created`

A `Citry` owns exactly one component registration state. Setup an extension
needs for that engine is done in **`on_extension_created`**, whose context
carries **`citry`**. The extension uses engine-level methods such as
`ctx.citry.get()`, `ctx.citry.has()`, and `ctx.citry.components`.

`on_component_registered` / `on_component_unregistered` fire from
`Citry.register`/`unregister`, and their contexts carry **`citry`** + `name` +
`component_class`.

---

## 7. Render-hook divergences from DJC

### 7.1 `on_component_input` is mutate-only; Cache owns short-circuiting

DJC's `on_component_input` does two jobs (mutate inputs *and* short-circuit the
render), and the conflation causes the leak class of #1607/#1648/#1649. Citry
splits those responsibilities:

- `on_component_input(ctx) -> None` is **mutate-only** -
  inspect/mutate `ctx.kwargs` / `ctx.slots`, single responsibility, always runs.
  No short-circuit return. The mappings are authoritative raw inputs. After all
  hooks finish, Citry normalizes Slots and constructs the final typed inputs
  exactly once, before data methods or cache lookup.

- After input hooks and revalidation, core asks the built-in Cache extension
  directly for a bypass, miss plan, or replay candidate. This decision is not a
  public `emit()` hook: Cache owns its correctness, and first-result fanout
  would prevent later extensions from observing the decision consistently.

- After replay commits and current ownership settles, Cache emits the
  notify-only `on_component_cache_hit` custom hook. Return values are ignored,
  observer failures are isolated, and later observers still run.

A hit skips component data methods, `on_component_data`, `on_render`, template
nodes, and `on_component_rendered`. The separate hit notification is the honest
observation point for extensions that need metrics or diagnostics.

### 7.2 Post-render return type: `CitryRender | str | None`

`on_component_rendered` accepts **`CitryRender | str | None`**. A returned
`str` is convenience: it is wrapped as a single-part `CitryRender` (treated as
already-serialized HTML). Keeping the struct form available means deps stay
recoverable; the `str` form is the easy path. (DJC used `str` only, because its
render output was a string.)

### 7.3 `on_component_rendered` operates on the `CitryRender`

Receives `render: CitryRender | None` + `error`. Return a `CitryRender`/`str` to
replace output, raise to replace the error, return `None` to keep the original.
Threading semantics preserved from DJC.

### 7.4 `on_template_compiled` fires at the node list, not a Template object

Citry has no Django `Template`. The useful point is **after the body node list is
generated** (so extensions can mutate/replace nodes - e.g. scoped-CSS attribute
injection, #1230). Fire `on_template_compiled(ctx)` with `ctx.nodes` (the
generated body list) at body-build time, before the list is cached (in the
const-body cache, `_const_body`), so the transform is applied once per
cached body, not per render. May mutate in place or return a new list.

`on_template_loaded` still fires once per class with the template **string**
before parse.

### 7.5 JS/CSS data methods

`js_data()` / `css_data()` exist alongside `template_data()` (with typed
`JsData`/`CssData` schemas), and `on_component_data` carries `template_data`
+ `js_data` + `css_data`, plus the render's `CitryContext` (so extensions can
stash tree-wide state in `context.extra`). The dependencies extension
consumes the data as JS/CSS variables ([`dependencies.md`](dependencies.md)
section 5). (DJC's deprecated `context_data` is dropped outright.)

---

## 8. Smarter dispatch: call only extensions that implement a hook

DJC loops every extension for every hook, invoking empty base methods. Citry
builds a **dispatch map** at manager construction: for each hook name, the list
of extensions whose method is actually overridden
(`type(ext).on_x is not Extension.on_x`). Each `manager.on_x(...)` iterates only
that list. Empty-hook extensions cost nothing. This map is also what makes custom
hooks (section 9) tractable, since dispatch is already name-keyed.

---

## 9. An open hook system: custom hooks + the merge step

The most structural change. Two coupled ideas:

### 9.0 Convention: namespace `extra` by owner

`CitryContext.extra` is one bag shared by everything in the render tree, so
its top-level keys are **namespaced by owner** to avoid collisions: an
extension stashes its data under a key named after itself (the dependencies
extension uses `extra["dependencies"]`), and citry-core concepts that more
than one party may contribute to live under `extra["citry"]`
(`citry_context.EXTRA_CITRY_KEY`). The root-marker hook is the first such
core concept; the core wraps it in the internal
`CitryContext._add_root_markers` / `_get_root_markers` rather than exposing
the raw nested key, so the magic strings stay in one place (underscore-
prefixed for now: the built-in dependencies extension is the only writer, so
the contract can firm up before it is offered to third-party extensions).
The rule keeps two extensions (or an extension and the core) from clobbering
each other's `extra` entries.

### 9.1 The dependency-merge step becomes a hook

`_merge_dependencies(parent_ctx, child_ctx)`, the merge step fired when a child
`CitryRender` is consumed, is a core hook: **`on_render_context_merge(ctx)`**,
`ctx` carrying the parent and child `CitryContext`s, so each extension merges
*its own* slice of `extra` with its own policy (deps want ordered de-dup, not
last-writer-wins). The core no longer owns the merge semantics.

### 9.2 Extensions can define their own hooks

For a clean layering, **`on_dependencies` is not a core hook** - it belongs to
the `dependencies` extension. So the core lets an extension **declare and
fire its own hooks** that other extensions implement. Mechanism (registration is
duck-typed, leaning on section 8's name-keyed dispatch):

- `manager.emit(name, ctx, result=..., field=...)` dispatches `name` to every
  extension that defines a method `name`, combining their returns per `result`.
- Built-in policies: `none` (side-effecting, return `None`), `first` (return
  the first non-`None` return; short-circuit), `map` (thread `ctx.<field>`,
  each non-`None` return replacing it via `dataclasses.replace`, returning the
  final value).
- The core hooks are just well-known `emit` names with fixed policies; a custom
  hook (like `on_dependencies`) is fired by its owning extension via `emit`, and
  any extension implements it by defining a method of that name.

So the dependency extension owns `on_dependencies` (and fires it at serialize
time), uses `on_render_context_merge` to bubble deps up the tree, and stashes into
`CitryContext.extra` - all without the core knowing about JS/CSS.

The **cache hit notification** (section 7.1) follows the same extension-owned
custom-hook idea but uses isolated direct dispatch. The built-in Cache extension
owns lookup and publication, then notifies every `on_component_cache_hit`
observer after replay commits. One observer's failure cannot stop later
observers or roll back the committed hit.

The name-keyed dispatch + `emit` mechanism is built and the core hooks route
through it. Dependencies exercises generic custom-hook dispatch through
`on_dependencies`; Cache owns the isolated notification contract for
`on_component_cache_hit`.

---

## 10. DJC hook + surface tracking table

Status: **Skeleton** (build now) · **Deferred** (defined/planned, no hook wired
yet) · **Dropped** · **Renamed/Reshaped**.

| DJC hook | citry status | Divergence |
|---|---|---|
| `on_extension_created` | Skeleton | ctx gains `citry` (absorbs registry setup, section 6.3) |
| `on_component_class_created` | Skeleton | ctx: `citry, component_class` |
| `on_registry_created` | **Dropped** | one component scope per Citry; use `on_extension_created` + `citry` |
| `on_registry_deleted` | **Dropped** | same |
| `on_component_registered` | Skeleton | ctx: `citry, name, component_class` (no `registry`) |
| `on_component_unregistered` | Skeleton | ctx: `citry, name, component_class` |
| `on_component_input` | Skeleton (reshaped) | mutate-only, `-> None` (django-components#1141 R6, 7.1) |
| *(short-circuit)* | **Built (Cache-owned)** | direct built-in Cache lookup plus notify-only `on_component_cache_hit`; no public decision hook (7.1, 9.2) |
| `on_component_data` | Wired | ctx: `citry, component, context, template_data, js_data, css_data` (7.5) |
| `on_component_rendered` | Skeleton | operates on `CitryRender`; `-> CitryRender \| str \| None`; skipped on a cache hit (7.1) |
| `on_template_loaded` | Skeleton | ctx: `citry, component_class, content` |
| `on_template_compiled` | Skeleton (reshaped) | fires at the node list, not a Template (7.4) |
| *(new)* `on_template_reset` | Wired | fires after a class's loaded template and compiled form are reset; cache revision subscribers invalidate local keys |
| `on_css_loaded` | Skeleton | wired by the asset-loading subsystem ([`asset_loading.md`](asset_loading.md) section 6); ctx: `citry, component_class, content` |
| `on_js_loaded` | Skeleton | same as `on_css_loaded` |
| `on_slot_rendered` | Wired | fires at the `<c-slot>` site (docs/design/component_slots.md section 7) |
| *(new)* `on_attrs_resolved` | Wired | citry-only; fires per HTML element with dynamic attributes, after the attribute dict resolves and before formatting ([`template_html_attrs.md`](template_html_attrs.md) section 5.5); ctx: `citry, component, tag_name, attrs`, threaded on `attrs` |
| `on_dependencies` | **Reshaped (built)** | not core; the `dependencies` extension fires it via `emit` at serialize time ([`dependencies.md`](dependencies.md) section 7.2) |
| *(new)* `on_render_context_merge` | Wired | the generalized `_merge_dependencies` step (9.1); core fires it, extensions own their slice of the merge |
| *(new)* `on_serialize` | Wired | fires at the end of `serialize()` with the joined HTML, threaded; the dependencies extension's placement point ([`dependencies.md`](dependencies.md) section 7.2) |

| DJC non-hook surface | citry status | Note |
|---|---|---|
| `ComponentExtension` base | Renamed | `Extension` |
| `ExtensionComponentConfig` | Renamed | `Extension.Config`; weakref + optional component kept (5.1) |
| `ExtensionManager` (global) | Reshaped | per-`Citry`; no deferral; smart dispatch + `emit` |
| `ComponentCommand` | Renamed | `ExtensionCommand` (stub; no runner yet) |
| `commands` list | Skeleton | kept (framework-agnostic CLI) |
| `urls` / `URLRoute` / resolvers | Wired (reshaped) | framework-neutral `Extension.urls` + `Citry.urls` + contrib adapters (section 11) |
| `extensions_defaults` | Skeleton | built now as a field on the `CitrySettings` schema object (5.2) |
| `<name>_class` escape hatch | **Dropped** | legacy `media_class` mirror (5.3) |
| `store_events` / `_init_app` deferral | **Dropped** | no Django app-load race (section 2) |
| `ExtensionMeta` / `ExtensionClass` | **Dropped** | DJC backwards-compat only |
| `args`, `context_data`, `component_class` dup | **Dropped** | no positional args; deprecated fields |

---

## 11. URLs: extension routes (built)

Extensions provide HTTP endpoints through **`Extension.urls`**: a list (or
property) of framework-neutral `URLRoute`s (`citry/util/routing.py`). The
manager combines them into `Citry.urls`, which the web-integration adapters
(`citry.contrib.asgi`/`wsgi`/`fastapi`) mount into the host app; a user
extension's routes are namespaced under `ext/<name>/`, built-ins own their
paths directly. Route handlers reach engine state through `self.citry`, the
back-reference the manager sets on every extension instance. Full design in
[`dependencies.md`](dependencies.md) section 9; the dependencies extension's
script endpoints are the first user.

---

## 12. Open questions

- ~~Short-circuit ownership and hook behavior~~ settled (section 7.1): the
  built-in Cache extension owns lookup directly, emits notify-only
  `on_component_cache_hit` after replay commits, and does not run
  `on_component_rendered` on a hit.
- ~~Naming of the merge hook and the `emit` custom-hook API shape~~ settled
  (section 9): the hook is **`on_render_context_merge`** (it merges the
  `extra` bag between two `CitryContext`s), and `emit(name, ctx, result=...)`
  ships with the `none` / `first` / `map` policies, exercised by
  `on_dependencies` and `on_serialize`.
- Where `CitrySettings` is validated, and how settings compose with the existing
  per-class fields (5.2). (Decided: it is a real schema object, not a dict.)
- ~~`js_data` / `css_data` data-method signatures~~ settled (7.5):
  `js_data(kwargs, slots)` / `css_data(kwargs, slots)`, mirroring
  `template_data`, with optional `JsData` / `CssData` schemas.

---

## 13. Suggested phasing

1. **Skeleton - built.** `Extension`, `Extension.Config` (weakref +
   optional component), `ExtensionManager` (per-`Citry`, smart dispatch, `emit`),
   `CitrySettings` schema object,
   `ExtensionCommand`, the `On*Context` dataclasses (lean surface). The
   **Skeleton** rows of section 10 are wired at their hook points; core hooks
   route through `emit`. `extensions_defaults` as the first settings entry.
2. **Dependency extension, emission phase - built.** The first real
   `emit`-owned custom hook (`on_dependencies`), the `on_render_context_merge` and
   `on_serialize` core hooks, `Script`/`Style` types, `CitryContext.extra`
   population, serialize-time placement (#1144). Full design and remaining
   phases (client runtime, fragments, URLs) in
   [`dependencies.md`](dependencies.md).
3. **Caching / short-circuit - built.** The built-in Cache extension owns
   direct component and transparent `<c-cache>` lookup/publication, emits
   notify-only `on_component_cache_hit` after a committed replay, and publishes
   opt-in component introspection metadata ([`caching.md`](caching.md)).
4. **Slots - done.** `on_slot_rendered` fires at the `<c-slot>` site.
5. **CSS/JS - done.** The asset-loading subsystem
   ([`asset_loading.md`](asset_loading.md)) provides the `js`/`css` sources and
   fires `on_css_loaded`/`on_js_loaded`; the `js_data`/`css_data` data methods
   and their delivery are built (7.5, [`dependencies.md`](dependencies.md)).
6. **URLs - built** (section 11); the Django adapter
   (`citry.contrib.django`) and the django-components template-tag
   integration remain ([`dependencies.md`](dependencies.md) phase 5).
