# Design: asset loading (template, JS, and CSS files)

**Status (2026-06-12): design agreed and built.** This
document specifies how a component's assets, the HTML template and the
component-colocated JS and CSS, are declared on the Component class, resolved to
files on disk, loaded, cached, and invalidated. It covers the three inline/file
field pairs (`template`/`template_file`, `js`/`js_file`, `css`/`css_file`), the
`CitryTemplate` struct, the path lookup chain, the secondary-asset
`Dependencies` class (owned by a built-in extension), the loading hooks, and the
hot-reload seam.

For the broader migration context see
[`citry_migration.md`](citry_migration.md). For the render model that consumes
the loaded template see [`rendering.md`](rendering.md); for the hook system the
loaders fire into see [`extensions.md`](extensions.md). For operating rules see
[`/CLAUDE.md`](../../CLAUDE.md).

Upstream references: django-components
[#1144](https://github.com/django-components/django-components/issues/1144)
(media becomes an extension),
[#1240](https://github.com/django-components/django-components/issues/1240)
(template-only components),
[#1326](https://github.com/django-components/django-components/issues/1326)
(avoid double-parsing),
[#901](https://github.com/django-components/django-components/issues/901)
(template loading via Django loaders, which citry drops),
[#1074](https://github.com/django-components/django-components/issues/1074)
(explicit utf8 encoding on Windows).

---

## 1. Prior art (what was searched)

In `packages/py/citry/_djc_reference/`:

- **`component_media.py`** (1288 lines) is the whole loading subsystem:
  the `ComponentMedia` holder + `UNSET` sentinel, `ComponentMediaMeta` with
  per-attribute `InterceptDescriptor`s for lazy resolution (`:359-444`), the
  MRO walk with pair-level override (`:451-495`), relative-path resolution
  (`:867-989`), content loading via `_get_asset` (`:1060-1211`), the `Media`
  normalization (`:714-864`), the Django `Media` merge with `extend`
  (`:502-599`), and the file-to-component reverse index for hot reload
  (`:1218-1288`).
- **`template.py`**: `load_component_template` + the `Origin` association
  machinery and the `loading_components` stack, all needed because Django's
  `Template.__init__` is a global chokepoint. Its `TODO_v3` (`template.py:350`)
  says to drop Django loaders and read files directly; citry does exactly that.
- **`util/loader.py`**: `get_component_dirs()` (driven by Django settings),
  `resolve_file()`, and the autodiscovery glob walk. The dir-based file
  resolution concept ports here (asset loading); the autodiscovery glob walk
  ports separately to `citry/autodiscovery.py`; finders and template_loader
  stay in django-components.
- **The laziness rationale** (`component_media.py:348-358`): DJC resolves
  lazily because Django settings are unavailable at class-definition time.
  Citry has no such race: a component binds to its `Citry` (whose frozen
  `CitrySettings` exists) at class definition. The *mechanism* (descriptors,
  holder object, sentinel) is therefore not ported; the *semantics*
  (pair-unit inheritance, explicit-None override, resolve-once caching) are.

In `packages/py/citry/citry/`:

- `component_render.py` `_get_template_string` was the placeholder this design
  replaces (it raised `NotImplementedError` for `template_file`), with a TODO
  saying the loaded template should become a Template object, not a string.
- `_get_compiled_template` already fires `on_template_loaded` and caches the
  compiled body generator per class in the class `__dict__`; the loaders follow
  the same resolve-once-per-class pattern.
- `extension.py` has `on_template_loaded` / `on_template_compiled` wired;
  `on_js_loaded` / `on_css_loaded` were catalogued in
  [`extensions.md`](extensions.md) section 10 as deferred "pending CSS/JS
  subsystem". This subsystem is that prerequisite, so this design wires them.
- `settings.py` `CitrySettings` is the frozen settings schema; the component
  search dirs become its next field.

---

## 2. Scope and the decisions that shaped it

Decisions made with the maintainer:

1. **`CitryTemplate` struct.** The loaded template is a struct, not a bare
   string: source + origin + filepath, plus the compiled form filled in lazily
   on first render, all one object (section 4).
2. **Scope: primary assets AND the secondary-asset class.** All three field
   pairs plus the secondary-asset class land now (sections 3 and 7).
3. **Path lookup: py-file dir, then Citry dirs** (section 5). No staticfiles
   tier, no comp-dir-relative path rewriting; resolve to an absolute path and
   read the file directly.
4. **Hot reload: reset methods, per-class cache eviction, AND the
   file-to-component reverse index** (section 8). The watcher itself is later
   work.
5. **The secondary-asset class is named `Dependencies` (not DJC's `Media`),
   and it is owned by a built-in extension from day one.** `Scripts` was
   considered and rejected (CSS is not a script, and it collides with the
   planned `Script`/`Style` entry objects). `Dependencies` matches the
   vocabulary the rest of the design already uses (the dependency flow in
   [`rendering.md`](rendering.md) section 6, the dependency extension in
   [`extensions.md`](extensions.md)). Implementing it as a built-in extension
   realizes DJC #1144 directly instead of deferring it: the extension named
   `dependencies` derives the nested config class name `Dependencies` through
   the extension system's own naming rule, so the loading half (this doc) and
   the later emission half live in the same extension and users never see a
   migration. Section 7 specifies the mechanism.

Naming cascade from decision 5: the nested class is `Dependencies`, the merged
struct is `CitryDependencies`, the accessor is `get_dependencies()`, the core
loading module is `citry/assets.py` (it loads templates too, so `media.py` was
a misnomer), and the built-in extension lives in
`citry/extensions/dependencies.py` (a new `extensions/` package for built-in
extensions, mirroring `components/` for built-in components).

---

## 3. The declaration model: three pairs, fields stay raw

The Component class gains the full DJC-style asset surface:

```python
class Card(Component):
    template_file = "card.html"   # or: template = "<div>...</div>"
    js_file = "card.js"           # or: js = "console.log('hi')"
    css_file = "card.css"         # or: css = ".card { ... }"

    class Dependencies:           # secondary assets, section 7
        js = ["vendor/chart.js"]
        css = {"all": "theme.css", "print": "print.css"}
```

### 3.1 Fields are declarations; classmethods are the accessors

A deliberate divergence from DJC: the class fields are **never rewritten**.
DJC's descriptors make `MyComp.js` return the loaded file content; citry keeps
`MyComp.js` as whatever the user wrote (`None` when `js_file` was used) and
exposes the resolved values through classmethods on `Component`, so no imports
are needed:

```python
Card.get_template()       # -> CitryTemplate | None    (section 4)
Card.get_js()             # -> str | None              (loaded primary JS content)
Card.get_css()            # -> str | None              (loaded primary CSS content)
Card.get_dependencies()   # -> CitryDependencies       (merged secondary assets, section 7)
```

The classmethods are thin delegates: the loading machinery lives in
`citry/assets.py` (so it stays independently testable and `component.py` stays
small), and `get_dependencies` delegates through `cls.citry.extensions` to the
built-in `dependencies` extension (acceptable coupling, since built-ins are
guaranteed present, and a uniform accessor surface beats making one of the four
require an import). The resets follow the same logic:
`Card.reset_template()` / `Card.reset_files()` (section 8.2).

Two notes on this surface:

- These accessors are **not override points**. DJC had `get_template` /
  `get_template_name` as deprecated *instance* hooks for supplying a template
  dynamically; citry's `get_template` is a cached accessor with a different
  return type. Overriding it is unsupported in the first version (a dynamic
  template source, if ever needed, would be its own designed feature).
- Nothing asset-related is exported at the `citry` package top level except
  the structs (`CitryTemplate`, `CitryDependencies`); the former top-level
  `get_*` / `reset_*` function exports are dropped.

Why not descriptors: that machinery was DJC's workaround for the Django
settings race, it makes `__setattr__` on the metaclass necessary, and it blurs
"what the user declared" with "what the engine resolved". Explicit classmethods
are mypy-friendly, keep the metaclass small, and make the caching story
inspectable.

### 3.2 Pair rules

For each pair (`template`/`template_file`, `js`/`js_file`, `css`/`css_file`):

- **Mutual exclusivity, checked at class definition.** Setting both members
  non-`None` on the same class raises `ValueError` immediately (DJC checks the
  same in `ComponentMedia.__post_init__`). Setting both to `None` is allowed
  (it means "explicitly no asset", see below).
- **The pair is one inheritance unit.** Resolution walks the MRO and stops at
  the first class whose own `__dict__` contains *either* member of the pair.
  That class's declaration wins for the whole pair. So a child that sets only
  `template_file` fully shadows a parent's inline `template`; the parent's
  value cannot leak through plain attribute lookup. (This fixes a latent bug:
  the previous `_get_template_string` read `comp_cls.template` via attribute
  lookup, which would have seen the parent's inline template alongside the
  child's `template_file`.)
- **Explicit `None` overrides; absence inherits.** `template = None` on a
  subclass makes it template-less even if a parent declared one. Not
  mentioning the pair at all walks on to the parent. There is no `UNSET`
  sentinel: presence in the class `__dict__` *is* the sentinel. (DJC needed
  `UNSET` only because it copied attrs into a holder dataclass where absence
  could not be represented.)
- The base `Component` class declares all six fields as `None` defaults, so
  the MRO walk terminates there with "no asset", which is the correct empty
  case.

### 3.3 Resolution is lazy, cached per class

Each primary accessor resolves on first call and caches the result in the
asking class's own `__dict__`: `_citry_template` (the `CitryTemplate`, which
also carries its compiled form once first rendered, section 4), `_resolved_js`,
and `_resolved_css`. The merged `Dependencies` result is cached differently: on the
built-in extension instance, in a weak-keyed per-class map (section 7.3), since
extension state belongs to the extension, not to user classes. No filesystem
I/O happens at import time, and a class is never resolved twice.

One consequence to know about: a subclass that inherits its parent's
declaration caches its *own* copy of the resolved content. Both classes
register against the same file in the reverse index (section 8), so file-driven
invalidation reaches both; only a direct `reset_template(Parent)` call does not
clear children. Acceptable for the skeleton; revisit if it bites.

---

## 4. `CitryTemplate`: the loaded template struct

`citry/citry_template.py`, completing the `CitryElement`/`CitryRender`/
`CitryContext` family:

```python
@dataclass(slots=True)
class CitryTemplate:
    source: str           # the template string, after on_template_loaded hooks
    origin: str           # display string: the absolute file path, or "pkg.mod::ClassName" for inline
    filepath: Path | None # the resolved file, or None when inline

    # The compiled form, filled in lazily by the render pipeline on first
    # render (None until then). Internal: the fields exist on this struct so
    # the loaded and compiled halves share one cache and one invalidation.
    generate: Callable[[], list[BodyItem]] | None
    used_vars: ...        # whatever _CompiledTemplate carries today
```

- One struct, one cache, one invalidation: the compiled form is derived purely
  from `source`, the compile site (`_get_compiled_template`) is the only
  consumer of the loaded template, and a reset must always drop both, so
  keeping them as two per-class cache attributes was two things to keep in
  sync for no benefit. The merged struct is cached on the class under a single
  attribute (`_citry_template`); `Card.get_template()` returns it whether or
  not it has been compiled yet.
- The compile *code* stays in `component_render.py` (it needs the runtime node
  classes for the exec namespace); it fills the struct's compiled fields
  instead of writing a second cache. The struct is therefore not frozen; the
  compiled fields are documented as internal.
- `origin` follows DJC's inline convention (`module_filepath::ClassName`) so
  error messages and debugging tools can always name where a template came
  from. **Wiring `origin` into error messages is part of this work package**,
  using the established error-context idiom in `citry/util/exception.py`
  (rewrite `err.args` on the same exception object, re-raise with
  `from None`):
  - **Parse/compile time**: `_get_compiled_template` catches errors from
    `parse_template` / `compile_template` and prefixes the message with the
    origin, so a syntax error names the file (or `module::Class` for inline)
    instead of arriving bare from the Rust layer.
  - **Render time**: `set_template_position_error_message`'s header line
    (currently `In template of 'Page':`) gains the origin, e.g.
    `In template of 'Page' (/path/card.html):`.
- `source` is post-hook: `on_template_loaded` fires inside the loader (for both
  inline and file content, matching DJC), and the hooked content is what gets
  cached and compiled. The firing moved out of `_get_compiled_template` into the
  loader so there is exactly one place content enters the engine.
- The struct's role in #1240 template-only components is recorded with that
  feature in [`citry_migration.md`](citry_migration.md) (planned-features
  table).

---

## 5. Path resolution

### 5.1 `CitrySettings.dirs`

The component search directories live on the settings schema:

```python
app = Citry(dirs=["/proj/components"])
```

- `CitrySettings.dirs: tuple[Path, ...]`, frozen like the rest of the schema.
- Entries must be absolute paths; `Citry.__init__` validates and raises
  `ValueError` otherwise (same contract as DJC's `COMPONENTS.dirs`).
- The default instance has no dirs; relative-to-py-file resolution (below)
  works without any configuration.

### 5.2 The lookup chain

For a `*_file` value (and for `Dependencies` file entries, section 7.4):

1. **Absolute path**: used as-is (must exist).
2. **Relative to the component's module directory**: the directory of the
   `.py` file where the class is defined (via `__module__` ->
   `sys.modules[...].__file__`). This is the colocated single-dir component
   layout (`card.py` + `card.html` side by side), DJC's most-used pattern.
   Components without a module file (REPL, exec) skip this tier.
3. **Relative to each entry of `comp_cls.citry.settings.dirs`**, in order.

First existing file wins, resolved to an **absolute** `Path`. There is no
staticfiles tier and no rewriting of the user's path into a comp-dir-relative
form: DJC only did that because Django's `Media`/staticfiles/template-loader
machinery consumed comp-dir-relative names, and citry reads the file directly
(the `TODO_v3` in DJC's own `template.py`).

For the primary `*_file` fields, failure to resolve raises `FileNotFoundError`
naming every location searched. (Media entries differ; section 7.3.)

Files are read with `encoding="utf8"` explicitly (Windows, DJC #1074).

### 5.3 What is dropped from DJC

Django staticfiles finders, Django template loaders and the
`loading_components` stack, `Origin` monkeypatching, `get_template_name` /
`get_template` / `get_template_string` (already deprecated upstream), the
`template_name` alias, and `cached_template`.

---

## 6. Loading hooks

All primary-asset loading funnels through `assets.py`, which fires the
extension hooks:

- **`on_template_loaded`** - fires once per class with the template string
  (inline or file) before parse. Already existed; the firing site moves from
  `_get_compiled_template` into the template loader.
- **`on_js_loaded`** / **`on_css_loaded`** - new, fire once per class with the
  JS/CSS content (inline or file). Contexts carry `citry`, `component_class`,
  `content`; threaded with `result="map"` like `on_template_loaded`. These were
  the "deferred pending CSS/JS subsystem" rows in
  [`extensions.md`](extensions.md) section 10; this subsystem lands them.

Because resolution is cached per class, each hook fires once per class, and the
post-hook content is what gets cached. A reset (section 8) re-fires on the next
access, which is the desired hot-reload behavior.

`get_js_data` / `get_css_data` (per-render variables for the assets) remain a
TODO tracked in [`extensions.md`](extensions.md) section 7.5; they are consumers
of this subsystem, not part of it.

---

## 7. Secondary assets: the `Dependencies` built-in extension

This is citry's realization of DJC #1144 ("media becomes an extension"),
implemented as such from the start rather than migrated later. A built-in
extension named `dependencies` owns the whole secondary-asset concern: the
user-facing nested `Dependencies` class, the normalize/resolve/merge logic, the
merged-result cache, and emission into the rendered output (built later, see
[`dependencies.md`](dependencies.md)).

### 7.1 The user surface

The nested `Dependencies` class accepts the DJC `Media` shapes:

```python
class Card(Component):
    class Dependencies:
        js = "a.js"                              # str | Path | callable | list of those
        css = {"all": ["x.css"], "print": "p.css"}   # also: single entry or list
        extend = True                            # bool | list[type[Component]]
```

An entry may be:

- a `str` or `Path` - a file path (globs allowed, section 7.4) or a URL,
- a callable returning one of those - evaluated lazily at resolution time,
- an object with `__html__` (e.g. `SafeString`) - a pre-rendered tag, passed
  through untouched.

Divergences from DJC, flagged per migration principle 5: `bytes` entries are
dropped (a Django-era convenience); callables are invoked lazily at first
resolution rather than at class definition (DJC's `_normalize_media` runs them
in the metaclass); and the user's `Dependencies` class is **not mutated** - DJC
normalizes the shapes in place at class creation, citry normalizes into the
separate `CitryDependencies` result and leaves the declaration as written.

### 7.2 The built-in extension mechanism

Two pieces are new to the extension system:

- **Built-in extensions.** `ExtensionManager._build` prepends a fixed
  fixed built-in set (`extension.py`'s `_builtin_extensions()`) to the user's `extensions=` spec, so every `Citry`
  instance has them (including the default instance). This mirrors the
  registry's built-in components factory (`<c-provide>` and friends). Built-in
  names are reserved: a user extension named `dependencies` is a name-conflict
  error, same as any duplicate. Built-ins cannot be disabled or replaced in
  the first version (decided; revisit only if a real need appears).
- **The nested class rides the existing `Extension.Config` mechanism.** The
  extension's `name = "dependencies"` derives `class_name == "Dependencies"`,
  so the manager's per-component config rebuild gives every component a
  `Dependencies` config class (user declaration > global defaults > the
  extension's `Config` base, which declares `js = None`, `css = None`,
  `extend = True`), and every component instance gets `component.dependencies`.

One interaction needs care: the config rebuild **replaces** the nested class on
the component (and `getattr` walks the MRO, so a child with no own declaration
would see its parent's rebuilt config baked into its own). That erases "what
did *this* class declare", which four parts of the merge semantics consume:

- **Own-entry detection.** The merge is own entries plus inherited ones; if a
  child's rebuilt config inherits the parent's `js` through the class chain,
  the parent's entries arrive twice (attribute inheritance plus the explicit
  `extend` walk).
- **Path anchoring.** An entry resolves relative to the module dir of the
  class that *declared* it (section 7.4); an entry leaking through config
  inheritance would wrongly anchor to the child's module dir.
- **`extend = False` / `extend = [...]`.** Skipping bases in the walk is not
  enough when inherited attributes still surface parent entries.
- **`Dependencies = None`.** The rebuild replaces `None` with a synthesized
  config class, erasing the "no entries, no inheritance" signal.

So the extension captures the raw declaration early, in its
`on_component_class_created` hook, which fires before the config rebuild: at
that moment `cls.__dict__.get("Dependencies")` is still exactly what the user
wrote (a class, `None`, or absent). The extension stores that in a weak-keyed
per-class map and the merge walk reads only these captured declarations. The
rebuilt config class remains the runtime access point
(`component.dependencies`); the captured declaration is the merge input.

### 7.3 `CitryDependencies`: the merged result

```python
@dataclass(frozen=True)
class CitryDependencies:
    js: tuple[str, ...] = ()
    css: Mapping[str, tuple[str, ...]] = ...   # media type -> paths
```

- `Card.get_dependencies()` (a classmethod delegating through
  `cls.citry.extensions` to the built-in extension instance, section 3.1;
  the implementation lives in `citry/extensions/dependencies.py`) resolves
  the class's own captured declaration
  (normalize shapes, invoke callables, resolve paths and globs relative to
  *that class's* module dir, then the Citry dirs) and merges ancestors per
  `extend`: `True` inherits from `__bases__`, `False` inherits nothing, a list
  of component classes inherits from exactly those. A captured `Dependencies =
  None` means no own entries and no inheritance.
- Merge order is **bases first, own entries last** (bases in their declaration
  order, then the class's own), de-duplicated preserving first-seen order (the
  repo-wide determinism rule: never let set iteration order into output). The
  rationale: list order becomes document order at emission, and CSS breaks
  equal-specificity ties by document order, so the more specialized class's
  styles must come later to win. JS follows the same rule (a base's vendored
  lib loads before subclass code that may use it). This matches Django's own
  forms `Media` (`base + own`); DJC inverted it to own-first
  (`component_media.py:577-594`) with no recorded rationale, and citry
  deliberately restores the cascade-friendly order. Flagged divergence from
  DJC per migration principle 5.
- Resolution is recursive over the inheritance graph, cached per class in a
  weak-keyed map held by the extension instance (state belongs to the
  extension, and the `Citry`-scoping rule #1413 is satisfied because the
  extension itself is per-`Citry`).

### 7.4 Dependencies path semantics

Each non-`__html__` entry:

- URLs (`http://`, `https://`, `://`, `/` prefixes) pass through unresolved.
- Globs (`*?[`) expand relative to the module dir, then relative to the Citry
  dirs; matches become absolute paths.
- Plain paths resolve through the section 5.2 chain (the extension reuses
  `assets.py`'s resolution helpers); a path that resolves to an existing file
  becomes absolute and is registered in the reverse index.
- A path that matches nothing is **kept as-is** (it may be meaningful to the
  consumer, e.g. a server-side static route), unlike the primary `*_file`
  fields which raise. This mirrors DJC.

### 7.5 Loading and emission, same extension

What `Dependencies` entries *mean* in output (inline the file content? emit a
`<script src>`? fingerprint and copy to a static dir?) is the **emission**
half. It lives in this same extension (built later, see
[`dependencies.md`](dependencies.md)), together with stashing collected
assets into `CitryContext.extra` and the serialize-time placement. Because the
loading half already lived in the extension, emission only added hooks and
methods to it; nothing moved, and no user-facing surface changed.
The core render pipeline never reads `Dependencies`.

The primary assets stay core: the render pipeline itself needs the template,
and the 1:1 colocated `js`/`css` pairs are component definition surface, not
extension config. The boundary is: **pairs in core `assets.py`, the
`Dependencies` class in the built-in extension.**

---

## 8. Hot reload: the reverse index and resets

### 8.1 File-to-component reverse index

Per DJC #1413 (all state on the `Citry` instance), the index lives on `Citry`,
not at module level:

- `Citry._register_component_file(path, comp_cls)` - called by the loaders for
  every file a class resolves (template, js, css, Dependencies entries).
  Stores weakrefs.
- `Citry.get_components_for_file(path)` - returns the live classes using that
  file, pruning dead refs. This is the API a future watcher (or test helper)
  drives invalidation through.
- `Citry.clear()` empties it.

### 8.2 Resets

Classmethods on `Component` (thin delegates into `assets.py`, same as the
accessors in 3.1):

- `Card.reset_template()` - drops the class's cached `CitryTemplate` (one
  object carrying source and compiled form, section 4) and evicts the class's
  entries from the `Citry` const-body cache
  (`Citry._evict_component_cache(comp_cls)`, since that cache previously only
  supported global `clear()`). The next render re-resolves, re-reads, re-fires
  `on_template_loaded`, and re-compiles.
- `Card.reset_files()` - drops the cached primary JS/CSS content, then fires
  the `on_files_reset` hook so extensions evict their own per-class state. The `dependencies` built-in implements it to drop its merged
  `CitryDependencies` cache; the future emission phase evicts its script cache
  the same way (DJC's `reset_files` evicts the script cache directly, but in
  citry the core must not reach into a specific extension). This is the first
  concrete consumer of the custom-hook dispatch
  ([`extensions.md`](extensions.md) section 9).

The watcher that calls these on file change is deferred (likely an extension,
using `get_components_for_file`).

---

## 9. DJC surface tracking

| DJC surface | citry status | Note |
|---|---|---|
| `template` / `template_file` pair | Ported | loaded via `get_template` -> `CitryTemplate` |
| `js`/`js_file`, `css`/`css_file` pairs | Ported | loaded via `get_js` / `get_css` |
| `template_name` alias + descriptor | Dropped | deprecated upstream |
| `get_template_name`/`get_template`/`get_template_string` | Dropped | deprecated upstream |
| Lazy descriptors / `ComponentMedia` holder / `UNSET` | Dropped (mechanism) | semantics kept via `__dict__`-walk; no settings race in citry |
| Pair-unit MRO override, explicit-`None` | Ported | section 3.2 |
| Relative-to-py-file resolution | Ported | resolves to absolute path, no rewriting |
| `COMPONENTS.dirs` | Ported | `CitrySettings.dirs`, absolute-only |
| Staticfiles finder tier | Dropped | no Django |
| Django template loaders + `loading_components` | Dropped | files read directly (DJC's own TODO_v3) |
| `Media` class (str/list/dict, globs, `extend`) | Ported, renamed + reshaped | `class Dependencies`, owned by the built-in `dependencies` extension (#1144 realized now, section 7) |
| `bytes` media entries | Dropped | flagged divergence |
| Callables in `Media` | Ported (lazier) | invoked at resolution, not class definition |
| `Script`/`Style` entry objects | Done | accepted as `Dependencies` entries ([`dependencies.md`](dependencies.md)) |
| `media_class` override | Dropped | legacy hook, same call as extensions.md 5.3 |
| Django `Media` merge | Replaced | `CitryDependencies` merge, first-seen-order dedup; bases-first order (restores Django forms' `base + own`, which DJC had inverted) |
| `on_template_loaded` | Moved | fires in the loader, inline + file |
| `on_js_loaded` / `on_css_loaded` | Wired now | were deferred in extensions.md section 10 |
| File-to-component reverse index | Ported | on the `Citry` instance, weakrefs |
| `reset_template` / `reset_files` | Ported | plus per-class const-body eviction |
| Hot-reload watcher | Deferred | future extension over `get_components_for_file` |
| Autodiscovery | citry owns it | `citry/autodiscovery.py`, run from `Citry.autodiscover()` / the `autodiscover` setting; separate from asset loading, which only reads files |
| finders / template_loader | Stays in DJC | per the migration classification |

---

## 10. Interactions

- **The `dependencies` extension exists from day one** (section 7), carrying
  the loading half. Its emission half (built later, see
  [`dependencies.md`](dependencies.md)) stashes collected assets into
  `CitryContext.extra` and places them at serialize time (rendering.md
  section 6), consuming `get_js`, `get_css`, and its own `get_dependencies`.
- **Built-in extensions are a new extension-system capability** (section 7.2):
  a fixed built-in set prepended by the manager (`_builtin_extensions()`), reserved names. Noted
  in [`extensions.md`](extensions.md) section 2.
- **Const-body cache**: gains per-class eviction (`_evict_component_cache`),
  used by `reset_template`. Folding (constness.md) is unaffected; a template
  reload simply invalidates all signatures for that class.
- **Body generator cache** (#1326): unchanged mechanism; `reset_template`
  clears it together with the template.
- **Template-only components** (#1240): `CitryTemplate` is the synthesis seat;
  not built.
- **Deferred rendering / slots**: untouched; loading happens before the body
  generator exists, upstream of the render queue.

---

## 11. Open questions

- Subclass caches are independent (section 3.3): a direct reset on a parent
  does not clear children; file-driven invalidation does. Accepted for now
  (the hot-reload workflow is not yet known); revisit if direct resets become
  a user-facing API.
- Whether `get_dependencies` should also surface the *loaded content* of local
  files, or only paths, depends on the extension's emission design.

---

## 12. Layout

The subsystem as built:

- `citry/citry_template.py`: `CitryTemplate` (loaded source + origin +
  lazily-filled compiled form, one object, one per-class cache).
- `citry/assets.py` (core): the loading machinery behind the pair accessors
  (template/js/css resolution chain, content loading + hooks, reverse-index
  registration, the reset implementations + the reset hook).
- `citry/extensions/dependencies.py` (built-in extension): the
  `DependenciesExtension` (`name = "dependencies"`), declaration capture,
  normalization, glob/path resolution of entries, `CitryDependencies` + merge,
  the weak-keyed merged cache.
- `citry/component.py`: `js`, `js_file`, `css`, `css_file` fields; the
  accessor/reset classmethods (`get_template`, `get_js`, `get_css`,
  `get_dependencies`, `reset_template`, `reset_files`), thin delegates into
  `assets.py` and the built-in extension; metaclass pair-exclusivity
  validation. (No `Dependencies` field on `Component`: the nested class is
  extension config, declared per component and rebuilt by the extension
  manager.)
- `citry/settings.py`: `dirs` field; `citry/citry.py`: dirs validation, the
  reverse index, `get_components_for_file`, `_evict_component_cache`.
- `citry/extension.py`: `OnJsLoadedContext`, `OnCssLoadedContext`,
  `on_js_loaded`, `on_css_loaded`; the `_builtin_extensions()` prepend.
- `citry/component_render.py`: the compile step fills `CitryTemplate`'s
  compiled fields and wraps parse/compile errors with the template origin;
  `set_template_position_error_message`'s header gains the origin (section 4).
- `citry/util/misc.py`: `get_module_info`, `is_glob`.
- Package top level exports the structs only (`CitryTemplate`,
  `CitryDependencies`); no `get_*` / `reset_*` function exports.
- Tests: `tests/test_assets.py`, `tests/test_ext_dependencies.py`.
