# Design: component introspection

**Status (2026-07-22): proposed, revised after maintainer review; phases 0, 1,
2, and 3 are implemented.** This document defines
a core, per-engine API for inspecting registered component definitions. The
result is a versioned value snapshot for local tooling and extension-owned
metadata. It is not live component registration state.

The originating request is [issue #26](https://github.com/citry-dev/citry/issues/26).
The planned consumers are recorded in
[`extensions_roadmap.md`](extensions_roadmap.md),
[`ide_integration.md`](ide_integration.md),
[`events.md`](events.md), and [`asset_compiler.md`](asset_compiler.md).

---

## 1. Decision

Citry will expose a component catalog describing the component classes
registered with one `Citry` instance: their current names, stable class IDs,
Python locations, typed schemas, asset declarations, and explicitly requested
extension metadata.

The catalog is an immutable, canonically ordered snapshot. It contains values
only and does not retain component classes, component instances, render
contexts, slots, templates, or request data. `class_id` remains the stable
route identity, while `engine_id` and `definition_id` identify the exact
runtime owner and class generation described by the snapshot. A caller that
resolves a current class through `Citry.get_component_by_class_id()` must
compare both runtime identifiers before treating retained metadata as exact.

The first public API is:

```python
catalog = app.inspect_components(
    include_builtins=False,
    resolve_assets=False,
    include_default_values=False,
    include_extensions=(),
)

card = app.inspect_component(
    "card",
    resolve_assets=True,
    include_default_values=True,
    include_extensions=("events",),
)
```

The plural method returns a `ComponentCatalog`, not a bare list. The envelope
provides the schema version, Citry version, requested extension versions, and
deterministic JSON serialization. The singular method returns the same
`ComponentInfo` shape used inside the catalog.

This is core Python API. It requires no parser or Rust change.

## 2. Why the catalog exists

The repository already names these consumers:

| Consumer | Catalog data it needs |
|---|---|
| `citry inspect --json` | A scripting and CI friendly component inventory with a versioned JSON format. |
| `citry check` and the language server | Registered tag names, open or closed input and slot schemas, required fields, type text, documentation, and Python source paths. |
| Tailwind | Python files containing inline templates and resolved external template paths for its content scanner. |
| Storybook | Component identity, typed inputs and slots, source locations, portable default values when explicitly requested, and extension-owned Storybook metadata for stories and examples. |
| `Component.Docs` | The same class metadata plus docs-owned metadata for descriptions, prop documentation, examples, and preview configuration. |
| Events | Namespaced metadata for handlers and their public request and response schemas, replacing a second component inventory walk. |
| Cache | Effective component cache policy, normalized TTL, lossless version identity, variation mode, and static Slot-source possibility. |
| Asset and Vite-style tooling | Registered component entries and the declaration provenance of their primary assets. |

## 3. Public API

The implementation lives in `citry/introspection.py`. Its public records and
errors are re-exported from `citry`.

### 3.1 Engine-ownership prerequisite

Version 1 is published only after Citry enforces one ownership invariant:

> Every class registered with a `Citry` instance is owned by that same instance.

Today a component already renders through exactly one owner, `component_class.citry`,
but another engine may import that class into its registry under an alias. That
foreign registration skips the inspecting engine's class-created lifecycle and
then renders through the original engine's settings, extensions, caches, and
asset roots. Version 1 therefore describes registrations bound to one Citry instance only.

The prerequisite ownership round will:

- make `Citry.register()` reject a class whose `citry` is another instance;
- keep `Citry.register()` public for same-engine aliases and re-registration;
- keep `Citry.unregister()` public for alias removal, hot-swap, and plugin
  unload;
- keep the registry implementation owner-only and private, with registration
  and lookup flowing through the owning `Citry` instance;
- retain public engine-level reads and lifecycle operations such as `get()`,
  `has()`, `components`, `initialize()`, and `clear()`.

The owner is fixed when a concrete component class is defined. Assigning or
deleting its `citry` attribute later is an error. Component inheritance is
bound to one Citry instance too: a concrete component base and its subclass use the same
engine. The root `Component` base can still produce classes for any engine.
This prevents an extension config class built by one engine from entering
another engine through inheritance.

The private registry remains a separate implementation class to keep dependency
direction clear.

The same round can simplify the current implementation without changing the
remaining engine-level behavior:

- remove the weak owner reference and every standalone-versus-owned branch in
  registry mutation, initialization, and clearing;
- remove standalone built-in factories, lifecycle coordination, rollback
  paths, and their public tests;
- route registration hooks, class-ID indexing, tag-rule invalidation, and cache
  retirement through one `Citry` path;
- delete foreign-registry cache exceptions and foreign-extension inspection
  rules;
- keep per-engine built-in creation, discovery, lifecycle coordination, caches,
  and hot-reload indexes, since single ownership does not make those global.

Reusable component modules may define concrete classes through a plain
registration function when they do not need a public library manifest:

```python
def register_components(app: Citry):
    class Card(Component):
        citry = app
        # ...

    return Card
```

The caller runs this once for each receiving engine during startup, before
`app.initialize()`. A reusable distribution can use the richer
[`LibraryComponent` publishing contract](component_publishing.md), which adds
an explicit manifest, repeated-installation identity, atomic package rollback,
stable generated IDs, extension requirements, and a Citry-owned installation
record. Introspection sees the resulting concrete classes through the same
engine registry in either model.

### 3.2 `Citry.inspect_components`

```python
def inspect_components(
    self,
    *,
    include_builtins: bool = False,
    resolve_assets: bool = False,
    include_default_values: bool = False,
    include_extensions: Iterable[str] = (),
) -> ComponentCatalog: ...
```

Behavior:

- It reads one copied registry snapshot from `Citry.components`. Like that
  property, it completes lazy discovery and built-in initialization first.
- It groups aliases so one component class produces one `ComponentInfo`.
- It excludes Citry's built-in component classes by default. Tailwind,
  Storybook, and user-library documentation should not treat framework
  internals as user components. `include_builtins=True` exposes them with
  `builtin=True` for tools that need the complete registry.
- It inspects declarations only unless `resolve_assets=True` is given. Asset
  resolution may check the filesystem but never reads asset contents, compiles
  templates, runs asset hooks, fills caches, or updates the hot-reload index.
- It includes portable Python field defaults only when
  `include_default_values=True` is given. It never calls a default factory.
- It invokes only the installed Citry runtime extensions named by
  `include_extensions`. No extension inspector runs implicitly.
- It returns components in deterministic order by primary name, import path,
  then `class_id`. A missing import path sorts as an empty string.
- It does not cache the result. A later registration or unregistration appears
  in the next call without an invalidation protocol.

### 3.3 `Citry.inspect_component`

```python
def inspect_component(
    self,
    component: str | type[Component],
    *,
    resolve_assets: bool = False,
    include_default_values: bool = False,
    include_extensions: Iterable[str] = (),
) -> ComponentInfo: ...
```

A string uses the normal case-insensitive registry lookup. A class must be
registered with and owned by this `Citry` instance under at least one name. An
unregistered or foreign-owned class raises
`NotRegistered`; introspection does not revive it or describe every class ever
created. The method takes one copied name-to-class registry snapshot and uses
that copy for both lookup and alias grouping, so it cannot combine a lookup
from one registry state with aliases from another.

After the copy, another thread may unregister or replace the selected class
while metadata and requested extension entries are being built. The method
still returns the generation that was registered at snapshot time, identified
by `engine_id` and `definition_id`; it does not revalidate membership at the end
and combine two generations. A caller that needs current membership performs a
fresh lookup and compares the runtime identity as described in section 4.1.

Looking up an alias does not change the result's primary name. The primary name
is selected deterministically from all names currently registered for the
class:

1. the normalized explicit `Component.name`, when that name is still present;
2. otherwise the class's derived kebab-case name, when present;
3. otherwise the lexicographically first registered name.

All remaining names are sorted into `aliases`.

### 3.4 Catalog serialization

`ComponentCatalog.to_dict()` returns a fresh JSON-ready dictionary.
`ComponentCatalog.to_json(indent: int | None = None)` uses UTF-8 text,
`ensure_ascii=False`, `allow_nan=False`, recursively sorted object keys, and
compact separators when `indent` is `None`. Component, alias, field,
searched-path, and extension ordering is already canonical before
serialization.

The complete version 1 shape is:

```json
{
  "schema_version": 1,
  "citry_version": "...",
  "engine_id": "eng_9c2f...",
  "extension_versions": {"events": 1},
  "components": [
    {
      "class_id": "Card_a1b2c3",
      "engine_id": "eng_9c2f...",
      "definition_id": "def_7f3a...",
      "name": "card",
      "aliases": [],
      "class_name": "Card",
      "module": "shop.components.card",
      "qualname": "Card",
      "import_path": "shop.components.card.Card",
      "python_file": "/work/shop/components/card.py",
      "description": "A product card.",
      "transparent": false,
      "builtin": false,
      "schemas": {
        "kwargs": {
          "kind": "fields",
          "declared_on": "shop.components.card.Card",
          "import_path": "shop.components.card.Card.Kwargs",
          "fields": [
            {
              "name": "title",
              "required": true,
              "type_display": "str",
              "type_fidelity": "normalized",
              "default_kind": "missing",
              "default_value_state": "not-applicable",
              "default_value": null,
              "description": null,
              "source_module": "shop.components.card",
              "source_qualname": "Card.Kwargs",
              "source_file": "/work/shop/components/card.py"
            }
          ]
        },
        "slots": {
          "kind": "fields",
          "declared_on": "shop.components.card.Card",
          "import_path": "shop.components.card.Card.Slots",
          "fields": []
        },
        "template_data": {
          "kind": "absent",
          "declared_on": null,
          "import_path": null,
          "fields": []
        },
        "js_data": {
          "kind": "absent",
          "declared_on": null,
          "import_path": null,
          "fields": []
        },
        "css_data": {
          "kind": "opaque",
          "declared_on": "shop.components.card.Card",
          "import_path": "shop.types.CssPayload",
          "fields": []
        }
      },
      "assets": {
        "template": {
          "kind": "file",
          "declared_on": "shop.components.card.Card",
          "owner_file": "/work/shop/components/card.py",
          "declared_path": "card.html",
          "resolution": "resolved",
          "resolved_path": "/work/shop/components/card.html",
          "searched_paths": ["/work/shop/components/card.html"]
        },
        "messages": {
          "kind": "none",
          "declared_on": null,
          "owner_file": null,
          "declared_path": null,
          "resolution": "not-applicable",
          "resolved_path": null,
          "searched_paths": []
        },
        "js": {
          "kind": "none",
          "declared_on": null,
          "owner_file": null,
          "declared_path": null,
          "resolution": "not-applicable",
          "resolved_path": null,
          "searched_paths": []
        },
        "css": {
          "kind": "inline",
          "declared_on": "shop.components.card.Card",
          "owner_file": "/work/shop/components/card.py",
          "declared_path": null,
          "resolution": "not-applicable",
          "resolved_path": null,
          "searched_paths": []
        }
      },
      "extensions": {
        "events": {
          "introspection_version": 1,
          "data": {"handlers": []}
        }
      }
    }
  ]
}
```

Every optional core field is present with `null`; arrays and objects are never
replaced with null. `extension_versions` and per-component `extensions` are
JSON objects keyed by extension name, although their frozen Python
representation uses ordered tuples. Extension `data` is always a JSON object,
not an arbitrary scalar or array.

There is deliberately no generation timestamp. Serialization of one frozen
catalog is deterministic. Separate catalog calls serialize identically only
when registry declarations, requested options, filesystem state used by asset
resolution, and extension-inspector-visible state are all unchanged.

`engine_id` and `definition_id` are non-time-derived, process-lifetime tokens.
They intentionally change after process restart. `citry inspect --json` and CI
consumers use stable `class_id` for logical cross-run identity and use the two
runtime tokens only for same-process freshness and exact runtime joins. The
complete JSON document is therefore not byte-stable across separate process
invocations even when source declarations are unchanged.

In-process paths are absolute `Path` values. JSON serializes them as absolute
POSIX-style strings because the first consumers are local tools that need to
open those files. A catalog can expose the developer's filesystem layout and
must not be returned from an HTTP endpoint unchanged. A browser-facing
extension selects and rebases the fields it intentionally publishes.

The JSON format is a soft external contract. Version 1 readers ignore unknown
object fields and unrequested extension names. They reject an unsupported
`schema_version` by default rather than guessing, and an unknown enum string in
an otherwise version 1 field is invalid. Additive nullable fields may be
introduced within one schema version. Adding an enum value, renaming a field,
changing its meaning, or removing it requires a schema-version increment. Each
extension's introspection metadata has its own independent positive integer
version.

## 4. Data model

The examples below show the intended fields. Exact type aliases may use
`Literal` values or private enums, but their serialized strings are the
contract.

### 4.1 Catalog and component records

```python
@dataclass(frozen=True, slots=True)
class ComponentCatalog:
    schema_version: int
    citry_version: str
    engine_id: str
    extension_versions: tuple[ExtensionVersion, ...]
    components: tuple[ComponentInfo, ...]


@dataclass(frozen=True, slots=True)
class ComponentInfo:
    class_id: str
    engine_id: str
    definition_id: str
    name: str
    aliases: tuple[str, ...]
    class_name: str | None
    module: str | None
    qualname: str | None
    import_path: str | None
    python_file: Path | None
    description: str | None
    transparent: bool
    builtin: bool
    schemas: ComponentSchemas
    assets: ComponentAssets
    extensions: tuple[ComponentExtensionInfo, ...]


@dataclass(frozen=True, slots=True)
class ExtensionVersion:
    name: str
    introspection_version: int


@dataclass(frozen=True, slots=True)
class ComponentExtensionInfo:
    name: str
    introspection_version: int
    data: FrozenJsonObject
```

`class_id` is the stable cross-request lookup identity Citry already uses for
asset and Events routes. It is derived from import path, so a hot replacement
at the same path intentionally reuses it. `engine_id` is an opaque,
process-unique token assigned to one `Citry` instance. `definition_id` is an
opaque, process-unique token assigned to one component class object before its
class-created hooks run. Both tokens are non-time-derived. Re-registering the
same class preserves its definition token; defining a replacement class gets a
new value. Neither token survives a process restart.

All three identities are read-only after their owner is created, including
during class-created extension hooks. The human-readable `class_id` prefix is
restricted to ASCII letters, digits, hyphens, and underscores before it is
used in route paths or generated JavaScript; unusual names on dynamically
created Python classes are normalized without changing the import-path hash.

Consumers join retained catalogs, runtime records, and current classes by the
triple `(engine_id, class_id, definition_id)`. `Citry.get_component_by_class_id()`
still resolves the current route target by `class_id`; the caller then inspects
that class and compares both runtime tokens. A mismatch is a stale-owner or
stale-generation result, not permission to apply old schemas or assets to the
replacement. The Python fields are values, not a retained class. They are nullable so generated
classes, `exec`/REPL classes, and future template-only components can use the
same interchange shape.

`python_file` is taken only from the already-loaded class module and normalized
to an absolute path. Introspection does not import a missing module to discover
it. Generated, `exec`, and REPL classes may have no file.

`description` is the component class's own cleaned docstring. An undocumented
subclass does not inherit a base component's docstring into its catalog entry.
This own-only rule is specific to descriptive prose. Executable declarations,
including schemas, transparency, and asset pairs, follow their documented
effective inheritance rules. Richer user-library prose and examples belong to
`Component.Docs` extension metadata.

### 4.2 Typed schemas

All five component schema roles use one adapter and one representation:

```python
@dataclass(frozen=True, slots=True)
class ComponentSchemas:
    kwargs: SchemaInfo
    slots: SchemaInfo
    template_data: SchemaInfo
    js_data: SchemaInfo
    css_data: SchemaInfo


@dataclass(frozen=True, slots=True)
class SchemaInfo:
    kind: Literal["absent", "fields", "opaque"]
    declared_on: str | None
    import_path: str | None
    fields: tuple[FieldInfo, ...]


@dataclass(frozen=True, slots=True)
class FieldInfo:
    name: str
    required: bool
    type_display: str | None
    type_fidelity: Literal["normalized", "unavailable"]
    default_kind: Literal["missing", "value", "factory"]
    default_value_state: Literal[
        "not-applicable",
        "omitted",
        "available",
        "unsupported",
    ]
    default_value: FrozenJsonValue | None
    description: str | None
    source_module: str | None
    source_qualname: str | None
    source_file: Path | None
```

The schema `kind` is not cosmetic:

- `absent` means no schema was declared. For `Kwargs` and `Slots`, parsing is
  open and unknown names are accepted.
- `fields` means the schema was recognized. It is closed, including when the
  field tuple is empty.
- `opaque` means a schema class exists but the adapter does not understand its
  field protocol. Tooling must not present this as “accepts nothing”. Runtime
  parsing remains open because Citry cannot derive closed `TagRules` from it.

This preserves the existing difference between `Kwargs = None` and an empty
declared `class Kwargs`. Reusing the richer schema adapter from `get_fields()`
also keeps parser `TagRules` and the catalog from drifting apart.

Schema roles use Citry's preserved component C3 declaration chain:

- A subclass that omits `Kwargs`, `Slots`, or another schema role reuses a
  single inherited effective schema when no other branch contributes.
- A schema declared on the subclass automatically extends compatible schema
  declarations below it in C3 order. Nearer fields and methods take normal
  Python precedence; users do not need to spell `class Kwargs(Parent.Kwargs)`.
- An explicit `Kwargs = None` or `Slots = None` stops declarations below that
  point and reopens that input dimension. A nearer declaration above the reset
  starts a new chain.
- Multiple component bases contribute compatible declarations in C3 order.
  Plain field classes, unslotted dataclasses with one consistent frozen mode,
  and Pydantic models from the same generation can compose. Compatible frozen
  dataclasses produce a frozen effective schema. Multiple NamedTuple branches,
  multiple slotted dataclass layouts, mixed frozen modes, and incompatible
  adapter families fail at component definition with a targeted error rather
  than silently dropping fields.
- A single explicitly adapted schema keeps its native runtime behavior and
  options.

`declared_on` is the import path of the C3-MRO class whose own dictionary
contains the nearest contributing schema-role binding. It may name a base
component or an ordinary definition base when the role is inherited. An
explicit user `None` also has `declared_on`; only framework-default absence
leaves it null. `import_path` names the effective class assigned to the
receiving component, including a synthesized multi-branch schema, and is null
for an absent schema.

Schema builders enforce these combinations:

| `kind` | `declared_on` | `import_path` | `fields` |
|---|---|---|---|
| `absent` | The explicit `None` owner's component path, or `None` for framework-default absence. | `None` | Empty. |
| `fields` | The component path that supplied the effective schema binding. | The recognized schema class's import path. | Zero or more effective fields in declaration order. |
| `opaque` | The component path that supplied the effective schema binding. | The unrecognized schema class's import path. | Empty. |

`FieldInfo` also validates that `required=True` pairs only with
`default_kind="missing"`, that `type_display` is present exactly when
`type_fidelity="normalized"`, and that default value state follows the table
below. Field source module and qualified class name are either both present or
both absent; a source file requires both and is an absolute path. Public frozen
records reject contradictory constructor arguments in `__post_init__`;
internal private builders remain the normal construction path.

Field provenance names the authored class whose own annotation declares that
effective field. It is deliberately per-field: a composed C3 schema can contain
fields from several base declarations even though `SchemaInfo.import_path`
names one effective receiving schema. When Citry builds an effective dataclass,
it snapshots both each field annotation and its authored class before the
generated schema merges those annotations. Python 3.10 through 3.13 use
`inspect.get_annotations(..., eval_str=False)`. Python 3.14 uses
`annotationlib.Format.FORWARDREF`, which keeps an unavailable name as a
`ForwardRef` while retaining values available in the declaration's original
namespace. A previously materialized exact annotation mapping or Python 3.14
annotation cache is reused, so one schema build does not run a deferred
annotation function twice. The generated schema stores the owner snapshot as
private runtime metadata; this does not change catalog v1.

For an explicitly adapted schema without that snapshot, Citry uses the same
version-neutral reader while walking the already-created schema MRO. It skips
implementation-only synthesized declaration shells and reads only already-loaded
module paths. It does not import modules or scan source to invent provenance.
Dynamically produced or otherwise unprovable declarations may therefore leave
all three values absent. A local class can retain a module,
`<locals>` qualified name, and file while still lacking a stable source join;
`exec` and REPL classes commonly have no usable file. A tooling consumer may
conservatively join a non-local qualified class and field name to an exact
annotated assignment in `source_file`; ambiguity, unreadable source, or a
missing assignment yields no location. This v1 provenance has no source-content
fingerprint, so it cannot distinguish two valid source generations that retain
the same qualified class and field identity.

The recognized adapters remain the current ones: dataclasses, Pydantic v2,
Pydantic v1, and NamedTuple. Fields stay in declaration order. Runtime
inspection does not call `typing.get_type_hints()`, resolve forward references,
or evaluate stored annotation strings. Python 3.14 may run Python's generated
annotation function when no exact mapping has yet been materialized. An
unresolved name survives as a `ForwardRef`; another exception from that function
fails component schema construction or inspection rather than producing a
partial field list.

For dataclasses, the adapter describes constructor inputs: inherited fields and
`InitVar` entries with `init=True` are included, while `ClassVar` entries and
fields with `init=False` are excluded. This also keeps `TagRules` aligned with
what the generated dataclass constructor accepts.

The Pydantic adapters intentionally follow the same structural runtime
protocols as `get_fields()`: dynamic access to `model_fields` or `__fields__`,
and the documented v2 `is_required()` method. A custom duck-typed schema can
therefore execute descriptor or method code while being inspected. Such schema
protocol implementations are trusted component code. The adapter does not
promise a no-Python-execution sandbox; its narrower guarantees are that it does
not evaluate stored annotation strings, call default factories, or use arbitrary
default and annotation representations. Dataclass and NamedTuple adapters use
their standard runtime field metadata. Default and description extraction
follows the same trusted adapter boundary.

The initial Pydantic adapter exposes each model field's canonical Python name.
It does not yet expand `alias`, `validation_alias`, `AliasChoices`, or
model-level validate-by-name settings into accepted input spellings. That is a
separate validation-contract round; until then, Pydantic aliases can differ
from both this canonical metadata and `TagRules` acceptance.

Type text uses a deliberately small formatter. It never calls `repr()` or
`str()` on an arbitrary annotation object:

- A stored string annotation is copied without evaluation. Its fidelity is
  still `normalized`, because runtime cannot prove that the stored text is the
  exact source spelling.
- `None`, `Any`, built-in classes, and user classes become `None`, `Any`, their
  unqualified built-in name, or their import path.
- `ForwardRef` and `TypeVar` use their stored string name.
- Unions are flattened and formatted as `A | B` in argument order.
- Recognized generic aliases format as `Origin[A, B]` recursively. The initial
  recognized origins are `list`, `tuple`, `dict`, `set`, `frozenset`, `type`,
  `Sequence`, and `Mapping`. An ellipsis in a tuple is the literal `...`.
- Callables use exactly `Callable[[A, B], R]` or `Callable[..., R]`.
- `Literal` accepts only null, booleans, integers, finite floats, and strings.
  Strings use JSON escaping. A different literal value makes the annotation
  unavailable.
- `Annotated[T, ...]` formats as `T`; metadata is deliberately omitted rather
  than represented through user code.
- Any unrecognized origin, argument, or annotation makes the complete field
  type unavailable.

`type_display` and `type_fidelity` move together: a formatted type has fidelity
`normalized`; an unavailable type has `type_display=None` and fidelity
`unavailable`. Runtime reflection does not promise the exact spelling an author
typed. That richer source contract belongs to separate static tooling.

Default classification belongs to the core schema adapter so Storybook, Docs,
and other consumers do not independently reinterpret dataclass, Pydantic, and
NamedTuple protocols. Ordinary inspection records presence metadata only.
When the caller passes `include_default_values=True`, core additionally copies
portable literal values:

| `default_kind` | `default_value_state` | `default_value` |
|---|---|---|
| `missing` | `not-applicable` | `None` |
| `factory` | `not-applicable` | `None` |
| `value`, values not requested | `omitted` | `None` |
| `value`, requested and portable | `available` | The frozen JSON value, including a valid JSON null. |
| `value`, requested but unsupported | `unsupported` | `None` |

Portable values are `None` or values whose type is exactly `bool`, `str`, a
finite `float`, or an `int` in JavaScript's safe integer range
`[-(2**53 - 1), 2**53 - 1]`. Exact built-in `list`, `tuple`, and string-keyed
`dict` containers may recursively contain portable values.
Tuples serialize as JSON arrays. Larger integers, cycles, and every other object
are unsupported. The copier does not call user `repr()`, `str()`, iteration,
serialization, equality, or `deepcopy()` methods. It never executes a default
factory. This gives control-generating tools the component's real numeric,
string, boolean, null, list, and object defaults while keeping arbitrary Python
objects out of the value contract and preserving integers in browser consumers.

Default values can contain sensitive strings even when structurally portable.
That is why extraction is a caller option and why the default catalog omits
them. A Storybook integration may request the values and deliberately publish
the subset it needs through its own extension metadata. Deliberate story or
documentation examples remain extension-owned fields; they are not inferred
from factories or unsupported Python objects.

Field descriptions are optional and come from two exact runtime sources:
Pydantic's string field description, or a string stored under the
`"description"` key of `dataclasses.field(metadata=...)`. NamedTuple has no
runtime field-description source. This design does not introduce a required
field-documentation syntax.

### 4.3 Asset declarations

Each primary asset is described independently:

```python
@dataclass(frozen=True, slots=True)
class ComponentAssets:
    template: AssetInfo
    messages: AssetInfo
    js: AssetInfo
    css: AssetInfo


@dataclass(frozen=True, slots=True)
class AssetInfo:
    kind: Literal["none", "inline", "file"]
    declared_on: str | None
    owner_file: Path | None
    declared_path: str | None
    resolution: Literal[
        "not-applicable",
        "not-requested",
        "resolved",
        "missing",
        "unavailable",
    ]
    resolved_path: Path | None
    searched_paths: tuple[Path, ...]
```

The asset builder enforces this state table:

| `kind` | `resolution` | Required and forbidden fields |
|---|---|---|
| `none` | `not-applicable` | `declared_path` and `resolved_path` are null; `searched_paths` is empty. An explicit user `None` shadow has `declared_on` present and a nullable `owner_file`; both are null when only `Component`'s framework defaults ended the MRO walk. |
| `inline` | `not-applicable` | `declared_on` is present; `owner_file` may be null for a generated class; path fields are null and `searched_paths` is empty. |
| `file` | `not-requested` | `declared_on` and `declared_path` are present; `resolved_path` is null and `searched_paths` is empty. |
| `file` | `resolved` | `resolved_path` is absolute and exists at inspection time; `searched_paths` contains every absolute candidate checked, including the winning path. |
| `file` | `missing` | `resolved_path` is null and `searched_paths` contains every candidate that was checked. This includes a missing absolute declaration. |
| `file` | `unavailable` | The declaration is relative, its owner has no already-loaded module file, and the owning engine has no configured search root. No candidate can be formed, so both `resolved_path` and `searched_paths` are empty. |

Every other kind-and-resolution pair is invalid. Paths returned by the builder
are absolute. `AssetInfo.__post_init__` rejects contradictory public
construction just as the schema records do.

`resolution="not-requested"` means a file declaration exists, but the caller
used `resolve_assets=False`. Introspection did not form candidate paths or touch
the filesystem. It does not mean that resolution failed; `missing` and
`unavailable` represent those checked outcomes.

`declared_on` is the import path of the class that owns the winning
inline/file pair. This is essential for inheritance: a subclass that inherits
`template_file = "card.html"` keeps the declaring base class's module as its
resolution base.

The record does not include inline template, JavaScript, or CSS content. For an
inline declaration, `owner_file` tells scanners which Python file contains the
source. For a file declaration, `declared_path` is always present and
`resolved_path` is populated only when resolution was requested and succeeded.
A missing file is structured metadata rather than an exception that discards
the rest of the catalog; `searched_paths` supports a useful diagnostic.

Primary file declarations accept the documented string form and a concrete
`pathlib.Path`. The record stores a string declaration; a `Path` is converted
with `Path.as_posix()`. Arbitrary `PathLike` implementations are not invoked by
introspection. The builder checks that a resolved winner exists at inspection
time. The frozen record keeps that historical value even if the file is later
removed.

Asset inspection uses the same MRO ownership and search-order helpers as normal
loading, but it does not call `get_template()`, `get_messages()`, `get_js()`,
or `get_css()`.
Those accessors read content, run extension hooks, publish caches, and update
the hot-reload file index. A metadata query must not make a class look rendered
or loaded.

The implementation must not call the current `get_module_info()` helper for
this work because that helper imports a module missing from `sys.modules`.
Introspection reads class-owned metadata through `type`'s static descriptors,
uses `sys.modules.get()`, and reads `module.__file__` only when the module is
already loaded. It therefore neither imports additional code to discover a
path nor invokes custom component-metaclass `__getattribute__` hooks.

Secondary `Dependencies` entries are not reflected by core. Their declarations
may contain callables and globs, and resolving them can execute user code and
mutate extension caches. The dependencies extension can add a separately
approved metadata contract when a consumer needs that data.

The planned `template_lang`, `js_lang`, and `css_lang` declarations from
[`source_languages.md`](source_languages.md) are not implemented yet. When that
feature lands, `AssetInfo` can gain additive nullable language and provenance
fields. Component introspection does not pull that separate feature into its
first implementation.

## 5. Extension-owned metadata

Core must not know the schemas of Events, Storybook, Docs, Dependencies, or
future extensions. It also must not reflect arbitrary extension configuration:
those classes may contain callables, guards, secrets, private caches, and
objects with unstable representations.

An extension may implement one explicit introspection method:

```python
class EventsExtension(Extension):
    introspection_version = 1

    def inspect_component(self, ctx: ComponentIntrospectionContext):
        return {
            "handlers": [
                # Deliberately public, JSON-safe handler metadata.
            ]
        }
```

`Extension.inspect_component()` is a direct query method, not a render or
class-lifecycle hook. Its frozen context carries:

```python
@dataclass(frozen=True, slots=True)
class ComponentIntrospectionContext:
    citry: Citry
    component_class: type[Component]
    info: ComponentInfo
```

The fields are:

- the inspected `Citry` instance;
- the temporary live component class;
- the already-built `ComponentInfo` with `info.extensions` empty.

The shared method name is intentional: `Citry.inspect_component()` builds one
catalog record, while `Extension.inspect_component()` contributes that
extension's metadata during the build. `ComponentInfo.extensions` contains
frozen JSON metadata, not live extension instances.

Core holds the live class only for the duration of the inspector call and never
stores it in the result. An inspector is trusted extension code and can retain
its context or class elsewhere despite the contract; JSON validation cannot
prevent that independent side effect.

Extension metadata rules:

- A caller opts in by extension name, for example
  `include_extensions=("events",)`. Installation makes introspection
  capability available; it does not publish the extension's metadata in every
  catalog.
- The extension must be installed, implement `inspect_component()`, and declare
  a positive `introspection_version`. Otherwise the request raises a clear
  error. Version 1 has no wildcard selection.
- `None` means that component has no entry for the extension.
- Core namespaces the returned object under the extension's unique name and
  records its version in both the catalog envelope and serialized component
  entry.
- Core requires a top-level string-keyed object, then validates, defensively
  copies, and recursively freezes strict JSON values. Accepted values use exact
  built-in `None`, `bool`, `str`, finite `float`, safe-range `int`, `list`,
  `tuple`, and string-keyed `dict` types; tuples serialize as arrays. Container
  subclasses and every arbitrary object are rejected, so copying cannot invoke
  custom iteration methods. `to_dict()` returns fresh ordinary lists and
  dictionaries. A top-level scalar or list, class, callable, `Path`, component,
  slot, or arbitrary object is rejected.
- An inspector error raises `ComponentIntrospectionError` naming the extension
  and component. Citry does not silently publish partial or misleading
  metadata.
- Inspectors are observational and deterministic. They must not render a
  component, load asset content, mutate registration, or depend on request
  state.
- Inspectors must be reentrant and thread-safe. Citry uses no global inspector
  lock, so concurrent catalog calls may query the same extension instance.

Explicit selection prevents every installed extension from adding cost or
private metadata to every ordinary catalog query. It also lets each extension's
metadata evolve under its own introspection version. This supports the common
case where one application installs every production extension while an IDE,
Storybook process, or command requests only the metadata it consumes.

Requested extension names are deduplicated and sorted before inspectors run,
so caller ordering does not affect inspector order or serialized output.
Inspectors must not depend on another extension inspector having run first.

`extension_versions` contains every requested extension and its
`introspection_version`, even when that inspector returns `None` for every
component. A component's `extensions` object omits only that component's `None`
entries. Readers reject an unsupported introspection version. Within a known
version they ignore unknown object fields; adding an optional field is allowed,
while removing or renaming a field, changing its meaning, or adding a closed
enum value requires the extension to increment `introspection_version`.

A requested extension entry is a trusted, extension-owned publication surface. JSON shape
validation can reject classes and callables, but it cannot know whether an
ordinary returned string contains a secret. Core guarantees that it never
reflects extension config automatically. Each bundled inspector must separately
test and document its allowlisted public fields, and callers must review
third-party extension metadata before publishing it.

Events introspection version 1 is the first implementation of this contract.
It constructs an allowlisted public description from the existing
`EventsInfo`; it never serializes `EventsInfo` itself. Its exact schema,
ordering, absence semantics, and exclusions are normative in
[`events.md`](events.md) section 9.1. Storybook and `Component.Docs` follow the
same extension-owned pattern for their nested configuration.

Cache introspection version 1 is the second bundled implementation. It reads
the effective synthesized `Component.Cache` class statically, preserves
arbitrary-size integer versions as tagged hexadecimal text, and reports only
declaration-level Slot-source possibility. It does not execute `Cache.vary()`
or factories or expose backend scope configuration. Its exact shape is
normative in [`caching.md`](caching.md) section 11.

## 6. Lifecycle, concurrency, and lifetime

### 6.1 Discovery and initialization

Inspection follows the same readiness contract as `Citry.components`. Calling
it before explicit startup initialization performs normal lazy discovery.
Server applications should still call `app.initialize()` after startup-time
registration and before request workers begin, as defined in
[`component_initialization.md`](component_initialization.md).

If another thread owns component discovery, registration, clearing, or another
lifecycle operation, inspection raises the existing
`CitryLifecycleInProgress`. It does not add a second wait protocol.

### 6.2 Snapshot boundary

Citry holds its lifecycle read guard only long enough to copy the current
name-to-class registry. It does not hold that guard while formatting
annotations, checking asset paths, or invoking extension inspectors. Calling
arbitrary extension code while holding the lifecycle coordinator would make
recursive registration and deadlock behavior difficult to reason about.

The resulting catalog is a snapshot of the registry names and class generations
at copy time. A class may be unregistered immediately afterward; the catalog
stays useful as historical value data. A later live lookup by `class_id` may
fail, return the same generation, or return a hot replacement. Consumers compare
both runtime tokens to distinguish exact, foreign-owner, and replacement cases.
Filesystem resolution is not atomic with hot reload or file deletion and does
not claim to be.

### 6.3 No hidden retention

The implementation keeps no catalog cache in the engine. `ComponentInfo`,
`SchemaInfo`, `AssetInfo`, and extension entries contain copied value metadata,
not a class pointer. Temporary class references used while building a catalog
are released when the call returns.

This preserves unregister and plugin-unload behavior for core and compliant
extension records. In particular, a caller may retain a serialized catalog without
preventing a fully unregistered component class from being garbage-collected.
An extension inspector that attempts to return the class is rejected by JSON
validation. An inspector that independently stores its callback context violates
the inspector contract and can still retain the class on its own extension
instance.

## 7. Privacy and publication boundary

Core-owned catalog fields exclude by schema:

- raw kwargs and slots;
- slot contents or rendered slot HTML;
- template, JS, and CSS source bodies;
- `template_data`, `js_data`, `css_data`, State, and provide/inject values;
- requests, users, sessions, cookies, and headers;
- unsupported Python defaults and extension config objects;
- callables, tracebacks, and exception objects.

These omissions are part of the core API contract, not merely serializer
choices. Portable field default values are included only after the caller
passes `include_default_values=True`. Requested extension entries are trusted
publication surfaces as defined in section 5; their allowlisted data is outside
this categorical guarantee. Together, the core omissions and explicit
extension opt-in keep ordinary metadata
inspection from becoming an automatic data-exfiltration feature.

Absolute file paths are the one intentionally local field. They support
go-to-definition, Tailwind, compilers, and watch tools, but they can reveal
machine layout. `citry inspect --json` documentation must label its output as a
local tooling artifact. Storybook, Docs, and Events must not serve the catalog
wholesale.

## 8. Relationship to `citry inspect --json` and static analysis

This API and its version 1 JSON describe one successfully loaded `Citry`
instance only. They require runtime facts that an AST scan cannot prove:
registration, dynamic names and aliases, engine ownership, `class_id`, built-in
identity, inherited runtime schemas, and installed extension metadata.

[`ide_integration.md`](ide_integration.md) also proposes exact source spelling
and an AST fallback when a project cannot import. That is a separate tooling
contract. It needs its own partially known record, source-root discovery, and
confidence rules. The current `--app module:attribute` loader cannot recover an
engine's configured roots after the import that should produce the engine has
failed. A static scanner also must not claim registry completeness or emit
unknown-component diagnostics.

The static record therefore does not masquerade as `ComponentInfo`, and this
design does not specify or version it. A later IDE/tooling round may join source
records to a successful runtime catalog for richer editor data, or return
static records alone after an import failure. That round must define the join
key and ambiguity behavior before `citry inspect --json` promises one combined
format.

The `citry list` command calls with `include_builtins=True` and projects each
record's primary name and aliases back to one merged row per component. It
keeps the established `name`, `class`, and `path` columns, the familiar
lowercased-then-kebab automatic name pair, source-path behavior, and built-in
coverage. Catalog order makes component rows deterministic; additional manual
aliases use canonical order rather than registry insertion order. Neither row
order nor manual-alias order was part of the documented list contract.

`citry inspect --json` is the deliberately narrow runtime command. `--json` is
required, reserving bare `citry inspect` for a possible future human-readable
format. The command calls `inspect_components()` with its API defaults and
prints the compact canonical JSON followed by one newline. It therefore
excludes built-ins, does not resolve assets, does not include portable default
values, and invokes no extension inspector. Those choices can become explicit
CLI options only in a later command-contract round.

The selected app must import successfully and normal lazy discovery must
complete. There is no static scan or fallback after an import or discovery
failure. Runtime failures retain the command runner's existing exception
behavior. Citry also does not capture stdout written by application imports or
discovered modules, so application code used with machine-readable commands
must not write unrelated output there.

The JSON is a local tooling artifact. It contains absolute developer-machine
paths and must not be served wholesale from an HTTP endpoint.

## 9. Alternatives considered

### 9.1 Return live component classes

Rejected. `Citry.components` already serves callers that deliberately need
classes. Putting classes into portable descriptors makes snapshots mutable,
non-serializable, tied to Python, and capable of defeating hot unload. It also
encourages consumers to retain a stale class. Consumers should resolve the
current one by `class_id`.

### 9.2 One record per registry name

Rejected. A normal PascalCase component has lowercased and kebab-case names.
Duplicating all fields per alias would generate duplicate stories, docs pages,
compiler entries, and event operations. One class record with a primary name
and aliases preserves both identity and lookup spellings.

### 9.3 A bare `dict` or `TypedDict`

Rejected as the in-process API. Frozen records provide discoverable types,
clear nullability, and equality for tests. `to_dict()` remains the explicit
interchange boundary, with a schema version at the catalog root.

### 9.4 `Component.describe()` on each class

Rejected as the primary entry point. Registration names, aliases, built-in
status, installed extension metadata, and lifecycle readiness belong to one
`Citry` instance, not to the class in isolation. Extensions can still receive
the temporary class in their introspection context.

### 9.5 Eagerly load assets for accurate paths

Rejected. Loading reads files, runs transformation hooks, publishes caches,
and updates hot-reload state. Declaration inspection plus opt-in path checks is
sufficient for the planned scanners and keeps metadata queries observational.

### 9.6 Reflect every extension config automatically

Rejected. Config classes are extension-private and can hold callables, secrets,
and non-deterministic objects. An explicit versioned introspection method makes
each extension responsible for its public metadata.

### 9.7 Track every component class process-wide

Rejected. Citry deliberately scopes registration and extensions to a `Citry`
instance. A process-global tracker would leak components between apps and tests
and would reintroduce lifetime problems already avoided by the engine-owned
registry.

## 10. Implementation plan

### Phase 0: per-Citry registration

- Keep component registration state private to `Citry` and expose registration,
  lookup, lifecycle, and clearing through engine-level methods.
- Bind each concrete component class immutably to one engine.
- Reject registration and concrete component inheritance across engine owners
  before the receiving engine mutates state or runs hooks.
- Preserve same-engine aliases, same-class re-registration, discovery,
  built-ins, rollback, cache retirement, and lifecycle isolation.
- Document `register_components(app)` as the minimal factory pattern for
  reusable modules without a public manifest. Reusable distributions use the
  implemented `ComponentLibrary` publishing contract. Both produce ordinary
  concrete classes in the receiving engine's introspection catalog.

Implemented on 2026-07-22.

### Phase 1: value model and schema adapter

- Add the frozen public records and JSON serializer in
  `citry/introspection.py`.
- Assign non-time-derived, process-unique `engine_id` and `definition_id`
  tokens to each `Citry` instance and component class generation. Assign the
  definition token before class-created hooks, preserve it across same-class
  re-registration, make all identities immutable during hooks and afterwards,
  keep generated class IDs route-safe, and expose a comparison path for current
  lookups.
- Replace the current name-and-required-only internal derivation with one rich
  schema adapter. Keep `get_fields()` as a compatibility projection for
  `TagRules` until callers move directly to the rich record.
- Cover dataclasses, Pydantic v2, Pydantic v1, NamedTuple, absent schemas, and
  opaque schemas without evaluating annotations or default factories. Add
  binding provenance and the opt-in portable default-value copier.

Implemented on 2026-07-22.

### Phase 2: assets and catalog queries

- Add a declaration inspection helper beside the asset pair lookup.
- Add a path resolver that can return resolved, missing, and searched paths
  without reading content or mutating caches and indexes.
- Add `Citry.inspect_component()` and `Citry.inspect_components()`, alias
  grouping, built-in filtering, stable ordering, and public exports.

Implemented on 2026-07-22. This phase reserved the final
`include_extensions` parameter that Phase 3 now implements.

### Phase 3: extension metadata

- Add the inspector context, version declaration, manager dispatch, strict JSON
  validation, and contextual error type.
- Implement Events introspection version 1 as the first consumer. Do not
  serialize the existing `EventsInfo` object directly.

Implemented on 2026-07-22.

### Phase 4: first consumers

- Reimplement `citry list` as a small catalog projection after output parity is
  locked by tests.
- Add a runtime-only catalog output to tooling only after the command contract
  clearly distinguishes it from the separately designed static fallback.

Implemented on 2026-07-22. `citry inspect --json` is runtime-only and uses the
core API defaults; static analysis remains a separate future record and command
contract.

Tailwind, Storybook, `Component.Docs`, and any Dependencies metadata are
consumer rounds after the core contract is proven.

## 11. Acceptance matrix

The introspection implementation is complete only when tests establish these
properties:

| Area | Required tests |
|---|---|
| Registry | Foreign registration is rejected before introspection ships; aliases group into one record; primary-name selection and ordering are stable; built-ins are marked and filtered; discovery runs; an unregistered class disappears from a fresh catalog; same-path definitions in two engines share `class_id` but differ in runtime tokens; a hot replacement keeps `class_id`, changes `definition_id`, and cannot be mistaken for the retained generation; identities cannot be forged during class-created hooks; generated class names still produce route-safe IDs. |
| Lifetime | Retaining a core-only catalog or a catalog with bundled compliant extension metadata after final unregister does not keep the component class alive or file-indexed; closure-bearing Events and Dependencies declarations remain collectible after unregister and `Citry.clear()`. |
| Schemas | Absent, closed-empty, closed-with-fields, and opaque are distinct; component-schema omission, compatible C3 composition, reset/reopen ordering, and explicit-`None` shadowing match runtime behavior; adapter-incompatible branch combinations fail explicitly; inherited dataclass, Pydantic v1/v2, and NamedTuple order and requiredness match `TagRules`; synthesized paths name the receiving component's effective schema; eager and Python 3.14 deferred annotations preserve each composed field's authored owner; unresolved deferred names remain available as forward references; one schema build evaluates an annotation expression once; stored string annotations are not evaluated; default factories never run. |
| Defaults | Values are omitted by default; requested portable values are copied and frozen; JSON null remains distinguishable from omission; safe-integer boundaries are exact; larger integers, unsupported objects, and cycles are reported without the copier invoking custom methods; factories never run. |
| Types and docs | Every supported normalized type form has an exact expected string; unsupported or unsafe forms are unavailable without calling custom representations; own component docstrings do not inherit; Pydantic and dataclass descriptions use only the documented sources. |
| Assets | Inline, file, none, explicit-`None` shadowing, inherited owners, absolute paths, configured-directory resolution, missing files, and no-resolution mode are covered. Arbitrary `PathLike` implementations are rejected without calling `__fspath__`. Inspection does not read content, run load hooks, fill asset caches, compile templates, update the file index, or execute custom component-metaclass attribute hooks. |
| Extensions | Only requested extension inspectors run; inspectors may be called concurrently; namespaces and versions are stable; requested versions remain in the envelope when all component entries are `None`; unsupported versions and extensions, inspector failures, top-level scalars/lists, container subclasses, unsafe integers, and non-JSON nested values raise contextual errors; core performs no automatic config reflection; every bundled inspector allowlists and tests its public fields. |
| Serialization | Catalog and extension introspection versions are present; one snapshot serializes canonically; paths serialize consistently; no class, callable, unsupported default, or source body can enter core JSON. |
| Lifecycle | Inspection follows normal initialization, uses the existing fail-fast concurrent-lifecycle error, and does not hold the lifecycle guard while an inspector runs; concurrent unregister or replacement after the copied snapshot cannot mix lookup aliases or generation metadata. |

The normal repository gate remains `python scripts/check.py --reporter agent`.
