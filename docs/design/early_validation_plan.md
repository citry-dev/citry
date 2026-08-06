# Research plan: early validation and fast feedback

**Status (2026-07-24): initial survey and adversarial review complete; research
plan awaiting maintainer review. No validation API is selected by this
document.**

This plan investigates how Citry can move failures earlier, from browser or
render time to template compilation, project checking, and editor feedback,
without claiming certainty that the framework does not possess. The first
targets are component template data, `CssData`, and `JsData`, but the work
starts with the full component data flow so the three channels do not acquire
incompatible rules.

The desired direction is:

```text
browser/runtime failure
        -> render preflight
        -> template or asset validation
        -> project check
        -> editor diagnostic
```

Moving a check left is useful only when the earlier result is sound enough,
fast enough, and points to the source that the author can change. Runtime
checks remain authoritative for dynamic paths.

---

## 1. Prior art

### 1.1 Current Citry implementation

The survey read the implementation and tests rather than inferring contracts
from existing design prose.

- Component class creation already recognizes `Kwargs`, `Slots`,
  `TemplateData`, `JsData`, and `CssData` as inherited schemas
  ([`component.py:93`](../../packages/py/citry/citry/component.py#L93),
  [`component.py:427`](../../packages/py/citry/citry/component.py#L427)). Plain
  field classes become composed slotted dataclasses
  ([`_nested_declarations.py:136`](../../packages/py/citry/citry/_nested_declarations.py#L136)).
- The base `Component.template_data()` already returns the effective `Kwargs`
  values ([`component.py:795`](../../packages/py/citry/citry/component.py#L795),
  [`component.py:807`](../../packages/py/citry/citry/component.py#L807)). In
  this plan, "no custom `template_data()`" means that the effective method is
  that base implementation, not that `hasattr()` returns false. Existing tests
  cover both untyped and typed kwargs passthrough
  ([`test_component.py:183`](../../packages/py/citry/tests/test_component.py#L183)).
- On a render-cache miss, Citry calls all three data methods and passes the
  results through `_normalize_data()`
  ([`component_render.py:1006`](../../packages/py/citry/citry/component_render.py#L1006),
  [`component_render.py:1533`](../../packages/py/citry/citry/component_render.py#L1533)).
  Schema construction currently applies the selected adapter's validation.
  Plain generated dataclasses and NamedTuples catch missing and unexpected
  fields, while adapters such as Pydantic follow their own extra-field and
  alias configuration. The constructed schema object is then discarded and
  the original mapping is returned. Defaults, coercions, aliases, and ignored
  extras therefore do not produce a canonical output mapping. Generated
  dataclass annotations do not enforce field value types.
- Engine template globals and per-render template globals are merged before
  component data, then extensions receive the mutable template, JS, and CSS
  dictionaries
  ([`component_render.py:1020`](../../packages/py/citry/citry/component_render.py#L1020),
  [`component_render.py:1033`](../../packages/py/citry/citry/component_render.py#L1033),
  [`extension.py:1436`](../../packages/py/citry/citry/extension.py#L1436)).
  Engine globals are intentionally mutable after construction
  ([`citry.py:174`](../../packages/py/citry/citry/citry.py#L174)), and callers
  may supply arbitrary per-render globals.
- Rust already computes free template-variable tokens after applying lexical
  `c-for` and `c-fill` bindings
  ([`parser.rs:208`](../../crates/citry_template_parser/src/parser.rs#L208),
  [`parser.rs:1912`](../../crates/citry_template_parser/src/parser.rs#L1912)).
  Each token retains its source span
  ([`ast.rs:17`](../../crates/citry_template_parser/src/ast.rs#L17)), and the
  template exposes the tokens to Python
  ([`ast.rs:934`](../../crates/citry_template_parser/src/ast.rs#L934)).
- Python currently loads and compiles a template lazily on its first render
  ([`component_render.py:1318`](../../packages/py/citry/citry/component_render.py#L1318),
  [`component_render.py:1380`](../../packages/py/citry/citry/component_render.py#L1380)).
  It stores only a `frozenset[str]` of used names after compilation, so source
  positions and duplicate uses are unavailable from the cached
  `CitryTemplate` later.
- There is no whole-template availability check. A missing name currently
  raises only when execution reaches its expression
  ([`nodes/__init__.py:479`](../../packages/py/citry/citry/nodes/__init__.py#L479),
  [`test_component.py:998`](../../packages/py/citry/tests/test_component.py#L998)).
  This makes present behavior branch-sensitive at render time.
- Slot data provides the closest working precedent. Python derives
  `slot_data_fields` from `SlotInput[T]`
  ([`tag_rules.py:54`](../../packages/py/citry/citry/tag_rules.py#L54),
  [`tag_rules.py:113`](../../packages/py/citry/citry/tag_rules.py#L113)), passes
  the finite field set into the parser
  ([`parser_context.rs:71`](../../crates/citry_template_parser/src/parser_context.rs#L71)),
  and Rust rejects statically invalid fill destructuring with a positioned
  diagnostic
  ([`parser.rs:3407`](../../crates/citry_template_parser/src/parser.rs#L3407)).
  Dynamic cases remain runtime-validated.
- Extension hook presence is not equivalent to a data effect. The built-in
  Dependencies and Events extensions implement `on_component_data`, but do
  not modify template data
  ([`ext/dependencies/extension.py:198`](../../packages/py/citry/citry/ext/dependencies/extension.py#L198),
  [`ext/events/extension.py:404`](../../packages/py/citry/citry/ext/events/extension.py#L404)).
  Other hooks can change input data, template source, post-parse nodes, JS
  source, or CSS source. In particular, the render pipeline already warns
  that `on_template_compiled` may add variable uses that are absent from the
  parser's recorded set
  ([`component_render.py:1112`](../../packages/py/citry/citry/component_render.py#L1112)).
- JS and CSS data are captured by the Dependencies extension. `$component(`
  is currently detected and rewritten with a regular expression
  ([`scripts.py:47`](../../packages/py/citry/citry/ext/dependencies/scripts.py#L47)),
  while CSS data keys are interpolated into generated custom-property
  declarations
  ([`scripts.py:281`](../../packages/py/citry/citry/ext/dependencies/scripts.py#L281)).
  Component-authored JS and CSS are not parsed or linted by Citry.
- Component introspection exposes schemas, but field types are currently
  normalized display strings rather than a structured, recursive portable
  type graph
  ([`_schema_introspection.py:59`](../../packages/py/citry/citry/_schema_introspection.py#L59),
  [`introspection.py:290`](../../packages/py/citry/citry/introspection.py#L290)).
  That is sufficient for documentation and completion, but not yet an
  established contract for TypeScript generation.

The main test corpus for this research is:

- [`test_component.py`](../../packages/py/citry/tests/test_component.py), for
  default template data, typed outputs, and missing variables;
- [`test_template_globals.py`](../../packages/py/citry/tests/test_template_globals.py),
  for mutable engine globals and per-render overlays;
- [`test_extension.py`](../../packages/py/citry/tests/test_extension.py), for
  data-hook ordering and mutation;
- [`test_tag_rules.py`](../../packages/py/citry/tests/test_tag_rules.py),
  [`test_slot_fills.py`](../../packages/py/citry/tests/test_slot_fills.py), and
  [`tag_parser_fills.rs`](../../crates/citry_template_parser/tests/tag_parser_fills.rs),
  for compile-time and runtime slot-data validation;
- [`test_js_css_data.py`](../../packages/py/citry/tests/test_js_css_data.py) and
  [`test_deps_vars.py`](../../packages/py/citry/tests/test_deps_vars.py), for
  schema shape checks, JSON transport, and CSS custom-property emission.

### 1.2 Existing Citry designs

This research extends, and must later reconcile with, the following plans:

- [`ide_integration.md`](ide_integration.md) already proposes `citry check`, a
  batch-first analyzer, virtual Python for expression typing, and an LSP. It
  deliberately defers type-aware template expressions and initially excludes
  embedded JS and CSS analyzers.
- [`ide_research/`](ide_research/) already surveys Vue/Volar, Svelte, templ,
  HEEx, Python template tooling, source mapping, and shadow-file approaches.
  The new work should reuse that evidence rather than repeat it.
- [`source_languages.md`](source_languages.md) anticipates language-service
  support for CSS data and `$component`, while
  [`asset_compiler.md`](asset_compiler.md) keeps type checking out of the
  render-time asset compiler. A later design must resolve the difference in
  scope and timing.
- [`extensions.md`](extensions.md) defines the mutable data and source hooks.
  [`extensions_roadmap.md`](extensions_roadmap.md) records scoped CSS as future
  work.
- [`component_slots.md`](component_slots.md) records the conservative `SlotInput[T]` source-field
  validation model and its runtime fallback.
- [`component_constness.md`](component_constness.md) is prior art for the limits of analyzing
  arbitrary `template_data()` code and for observing actual runtime outputs.

### 1.3 External research seeds

The external study will prefer language specifications, official framework
documentation, and implementation repositories. Community reports are useful
for identifying failure modes, but are not authoritative contracts.

| System | Question it helps answer |
|---|---|
| [Angular template type checking](https://angular.dev/tools/cli/template-typecheck) and [structural directive context guards](https://angular.dev/guide/directives/structural-directives#improving-template-type-checking-for-custom-directives) | Strictness tiers, generated checks, local escape hatches, and extension-declared context shapes |
| [Vue language-tools](https://github.com/vuejs/language-tools) and [Volar virtual code](https://volarjs.dev/reference/languages/) | Inspectable virtual source, source mappings, incremental language-service architecture |
| [Svelte check](https://svelte.dev/docs/cli/sv-check) and [Svelte language-tools](https://github.com/sveltejs/language-tools) | One checker spanning compiler, TypeScript, accessibility, and CSS diagnostics; dependency-aware checking |
| [Jinja meta analysis](https://jinja.palletsprojects.com/en/stable/api/#jinja2.meta.find_undeclared_variables) and `StrictUndefined` | Conservative undeclared-name extraction plus runtime authority |
| [Python typing specification](https://typing.python.org/) and [`dataclass_transform`](https://typing.python.org/en/latest/spec/dataclasses.html) | What ordinary Python type checkers can understand from generated schema classes |
| [Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/) and [FastAPI client generation](https://fastapi.tiangolo.com/advanced/generate-clients/) | One executable schema feeding runtime validation and cross-language code generation; validation shape versus serialization shape |
| [CSS Custom Properties Level 1](https://www.w3.org/TR/css-variables-1/) and [CSS Properties and Values API](https://www.w3.org/TR/css-properties-values-api-1/) | Cascade, inheritance, fallbacks, `@property`, typed custom properties, and why selector scoping is not variable isolation |
| [Stylelint custom-property checking](https://stylelint.io/user-guide/rules/no-unknown-custom-properties/) | Reference manifests, fallback handling, configurable open-world CSS checks |
| [TypeScript declaration files](https://www.typescriptlang.org/docs/handbook/2/type-declarations.html) and [Language Service API](https://github.com/microsoft/TypeScript/wiki/Using-the-Language-Service-API) | Generated `$component` context types, snapshots, change ranges, and reusable diagnostics |
| [LSP 3.17](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/) | Editor transport, kept separate from the analyzer's semantic model |

Avi Press's 2026 article,
[After 7 Years in Production, Scarf Has Reluctantly Moved Away from Haskell](https://avi.press/posts/2026-07-10-after-7-years-in-production-scarf-has-reluctantly-moved-away-from-haskell.html),
is a useful motivation for measuring the full edit-to-diagnostic cycle. The
article describes a cold build reaching roughly 15 minutes, not a substantiated
15 to 30 minute range. The corresponding
[Haskell community discussion](https://discourse.haskell.org/t/after-7-years-in-production-scarf-has-reluctantly-moved-away-from-haskell/14380)
provides counterexamples involving project structure, caching, and interactive
workflows. The research will treat both as prompts to measure Citry, not as
proof that either stronger checking or Python is inherently faster.

---

## 2. Objective and success criteria

The research must produce a coherent validation model for the template, slot,
JS-data, and CSS-data boundaries in scope:

1. kwargs and slots supplied to Python;
2. Python values exposed to a template;
3. extension-supplied or extension-mutated template values;
4. slot data exposed by an outlet to a fill;
5. Python values serialized into the `$component` browser context;
6. Python values serialized into CSS custom properties;
7. template globals, inherited browser context, global CSS tokens, and other
   intentionally ambient values.

For every boundary, the final design must state:

- who produces and consumes the value;
- which declaration, inference, or runtime observation describes it;
- whether the known shape is exact, additive, or open;
- which checks exist for field names, requiredness, value types,
  serialization, and use sites;
- the earliest sound validation stage;
- the invalidation dependencies for cached and editor results;
- the source location and wording of a diagnostic;
- the narrowest escape hatch for genuinely dynamic behavior;
- the runtime fallback when an earlier stage cannot prove correctness.

The work succeeds only if it improves the actual feedback loop. At minimum it
must demonstrate:

- a typo in a statically known template variable is diagnosed before render;
- the same semantic facts and rule definitions can be reused by a batch
  checker, a future LSP, and runtime fallback, while related stage-specific
  diagnostic codes remain possible when the actionable failure differs;
- an unknown extension, mutable global, dynamic data producer, or external CSS
  source degrades only the affected check, not all validation for the
  component;
- source positions remain accurate for inline and external assets when a
  trustworthy mapping exists, and diagnostics never claim an authored
  position when only transformed-source coordinates are known;
- cache invalidation is complete when a component schema, extension contract,
  global declaration, or source file changes;
- warm diagnostics fit an interactive budget, and cold project checking does
  not simply relocate long blocking work to imports or class creation;
- production does not pay for editor-only or project-wide type checking.

### Non-goals for this research plan

- It does not select syntax for `TemplateData`, `JsData`, `CssData`, or
  extension effects.
- It does not promise complete static interpretation of arbitrary Python.
- It does not make CSS a closed local namespace merely because selectors may
  later be scoped.
- It does not put TypeScript or CSS linting into the render path.
- It does not require a Rust parser contract change for the first template
  prototype. The existing positioned AST data must be tried first.

---

## 3. Name the feedback stages precisely

"Compile time" is too ambiguous for this work. Citry currently compiles most
component templates lazily during first render, while external frameworks use
the same term for build, import, generated-code, or editor checks. Reports and
benchmarks will name one of these stages:

| Stage | What it means in Citry research |
|---|---|
| Authoring or agent generation | The source has been produced but not necessarily saved or imported |
| Editor or lint | Source-only or partially resolved diagnostics while editing |
| Project check | An explicit `citry check`-style command that may discover or import the application under a documented mode |
| Import and component class creation | Python executes the component definition and constructs its effective nested schemas |
| Asset load | Template, JS, or CSS source is resolved and source-transforming hooks have run |
| Template parse and compile | Rust parses the final template source and Python creates executable nodes; today this is usually lazy |
| Render preflight | Final kwargs, globals, and extension data exist, but template expressions have not run |
| Expression or slot execution | A particular branch or fill actually requests a value |
| Serialization and browser | JS/CSS payloads are encoded, emitted, parsed, and consumed by the client |

The project will separately measure cold, warm, incremental, and cached cases.
An error is not "early" if a nominally earlier stage takes longer to reach than
the present runtime failure.

---

## 4. Initial data-flow and validation survey

### 4.1 Current normal template path

```text
component class body
  -> effective Kwargs / Slots / TemplateData / JsData / CssData schemas

composition inputs
  -> on_component_input
  -> typed kwargs and slots
  -> component-cache lookup
       -> hit: replay output and return before data methods or template compilation
       -> miss or bypass: continue
  -> template_data / js_data / css_data
  -> adapter-defined schema-constructor check, currently returning the original mappings
  -> engine globals + per-render globals + component template data
  -> on_component_data
  -> on_render
       -> replacement: return without loading or compiling the template
       -> normal path: continue
  -> load template source
  -> on_template_loaded source transforms
  -> parse and compile, recording positioned free-variable demand
  -> on_template_compiled node transforms, without recomputing recorded demand
  -> template expressions

js_data
  -> Dependencies capture and JSON serialization
  -> browser $component context

css_data
  -> Dependencies capture and JSON hashing
  -> generated --<key>: <value> declarations on component roots
  -> CSS cascade and inheritance
```

This diagram intentionally shows a logical JS/CSS flow. Current hook ordering
means the built-in Dependencies extension captures JS and CSS before later
user `on_component_data` hooks run. A user extension's template-data mutation
is visible through the shared context dictionary, while its later JS/CSS
mutation is not delivered to the browser. The intended ordering and canonical
post-hook validation point must be decided before extension effect metadata is
considered sound.

### 4.2 Current coverage matrix

| Concern | Runtime today | Template or asset validation today | Lint/editor today |
|---|---|---|---|
| Kwarg and slot field set | Typed input construction after input hooks | Static component-tag and fill checks where names are known | Proposed in `ide_integration.md` |
| Template-data field set | `TemplateData` construction before extensions; missing use raises only on an executed expression | No availability check against template demand | None |
| Template-data value types | Adapter-dependent; generated dataclasses do not enforce annotations | None | Ordinary Python annotations only where user code exposes them |
| Template globals | Actual mapping lookup | None; names may change after compilation or arrive per render | None |
| Extension data effects | Hook executes; no post-hook schema validation | No declared effect model | None |
| Slot-data source field | Positioned runtime error for dynamic cases | Positioned parser error for statically known cases | Available once the planned analyzer invokes the same parser rules |
| `JsData` field set | Schema construction before extensions | None | None for user component JS |
| JS wire type | JSON errors only when data is emitted; no match to annotation is guaranteed | None | None |
| `$component` usage | Registration shape is partly checked in the browser | Regex detection and rewrite, not syntax or type checking | None for user component JS |
| `CssData` field set | Schema construction before extensions | None | None |
| CSS value safety and type | Exact string keys, scalar type checks, CSS string escaping, and declaration containment during emission | None | None |
| CSS `var()` provenance | Browser cascade decides | None | None |

### 4.3 Immediate safety finding

The initial survey reproduced stylesheet injection through the CSS-data
emission implementation that existed at that time. Custom-property keys were
interpolated without validating that they were valid names, and string values
could escape their declaration because embedded quotes were not escaped
safely. This was a runtime safety and correctness issue, not merely a future
lint opportunity.

For example, a CSS-data key of `x; } body { color` was inserted into a
declaration as `--x; } body { color: red;`. The generated rule's final closing
brace completed the injected `body` rule. The affected paths remain
[`scripts.py`](../../packages/py/citry/citry/ext/dependencies/scripts.py) and
[`util/css.py`](../../packages/py/citry/citry/util/css.py), now with the
containment controls described below.

The resulting early security work package covers names, quotes, backslashes,
newlines, comments, braces, semicolons, functions, and raw CSS values. The fix
landed independently of the broader early-validation research.

**Resolution (2026-07-24): fixed.** CSS-data keys now accept only safe
custom-property identifier suffixes. Values accept strings, numbers, or
`None`; Citry escapes quoted CSS strings and rejects structurally incomplete
or declaration-breaking raw values before caching or emission. Regression
coverage includes the reproduced key and value payloads, quotes, controls,
blocks, comments, data URLs, HTML style end tags, non-scalar values, and cache
artifact reconstruction. This is a containment contract, not yet complete CSS
grammar or property-type validation. The broader audit reminder lives in
[`security-hardening.md`](security-hardening.md).

---

## 5. Soundness model to test

The research will keep three axes independent.

### 5.1 Data boundary

Template supply, template demand, slot supply, slot demand, JS serialization,
CSS serialization, and ambient values are different boundaries. Evidence that
closes one boundary must not silently close another.

### 5.2 Knowledge level

Each fact is classified as one of:

- **Exact declared:** a finite schema or manifest is the authoritative set.
- **Conservative inferred:** analysis can establish requirements but may
  include names from paths that do not execute.
- **Declared additive:** an extension or global contract adds a known set but
  may preserve an open remainder.
- **Trusted effect contract:** an extension declares which facts it changes.
  Development checks may audit the declaration, but a false declaration is
  still an extension bug.
- **Observed runtime:** only the actual rendered value is known.
- **Dynamic or unknown:** the checker must not infer absence from missing
  evidence.

The initial hypothesis is that certainty should be per channel and per effect,
not a binary "component has extensions" flag. An extension may observe JS,
modify template supply, transform CSS source, and leave template demand alone.

### 5.3 Feedback stage

A fact may be exact at render preflight and unknown in a source-only editor.
That is expected. The design should reuse diagnostic definitions while letting
each stage report the strongest conclusion supported by its evidence.

The intended behavior is graceful degradation:

```text
exact supply + exact demand       -> error for a missing name
exact supply + inferred demand    -> error or strict diagnostic, by policy
open supply + exact demand        -> completion for known names; no absence proof
dynamic source transform          -> disable only source-demand conclusions
dynamic data transform            -> disable only supply conclusions for that channel
```

---

## 6. Research questions

### 6.1 Template-data availability

1. Can Python validate the parser's positioned root free-variable tokens
   against effective component schemas without any Rust contract change?
2. Which template constructs make the current root set conservative or wrong
   for availability checking? Known probes include walrus assignment, nested
   template-valued attributes, repeated occurrences, Unicode identifiers,
   loops, fills, and extension-injected nodes.
3. When the effective method is the base `Component.template_data()`, can
   `Kwargs` be treated as the exact supply schema? How do open kwargs,
   inheritance resets, library-component materialization, defaults, and
   adapters affect that answer?
4. When a component overrides `template_data()`, which of `TemplateData`, a
   return annotation, a returned schema instance, or limited source inference
   is authoritative?
5. Should a whole-template preflight reject a missing name in a branch that is
   false on this render? If so, that is an intentional change from the current
   branch-lazy runtime contract and needs migration guidance.
6. How should `on_render()` replacements, fragment/component cache hits, hot
   reload, and dynamically reset templates interact with validation?
7. Can mutable engine globals and arbitrary per-render globals remain fully
   open while still giving useful diagnostics? Should Citry add optional
   declared global schemas, warning-only modes, or call-site-aware checks?

### 6.2 One source of truth for data

The work will compare, not assume, these authoring models:

1. An explicit nested schema plus a method returning an instance of that
   schema.
2. A schema class that is also the producer, so defaults and construction
   define the runtime output once.
3. Automatic `Kwargs` passthrough when no custom producer exists.
4. A return annotation such as a dataclass, Pydantic model, `TypedDict`, or
   another supported record shape.
5. Bounded Python AST inference for simple literal returns, with unknown as a
   normal result for branches, helper calls, mutations, or decorators.
6. A decorator or builder that declares fields and constructs the value once.

Each model will be scored against ordinary Python readability, inheritance,
runtime validation, defaults and coercion, mypy and Pyright behavior, editor
completion, introspection, JSON serialization, TypeScript generation, and the
ability to remain dynamic when needed.

Arbitrary return-value inference is not assumed feasible. The research must
measure how quickly representative real components become opaque and whether
limited inference reduces duplication without creating misleading certainty.

### 6.3 Extension effect declarations

The first proposal to test is a per-channel effect model with room for:

- no effect;
- observation only;
- adds a declared shape;
- removes or replaces a declared shape;
- arbitrary or dynamic effect.

The audited facts must include at least:

- kwarg and slot supply after `on_component_input`;
- template supply after `on_component_data`;
- JS and CSS data supply after `on_component_data`;
- template demand after `on_template_loaded` and `on_template_compiled`;
- JS demand/source after `on_js_loaded`;
- CSS demand/source after `on_css_loaded`.

The work will test whether development mode can compare declared effects with
before/after values. It must include nested mutation, removal, replacement,
ordering between built-ins and user extensions, and values captured before a
later hook mutates them. It must also cover effects selected by per-component
extension configuration and conditional runtime behavior, not only one fixed
effect per extension class. A declaration is a trusted optimization contract,
not a security boundary.

Source transformation is a separate effect dimension. `on_template_loaded`,
`on_js_loaded`, and `on_css_loaded` may insert or remove arbitrary text, but
their current return contract carries no mapping back to authored source.
Parser or language-service positions can therefore point into transformed
content that the author cannot edit directly. The study will compare:

- an explicit declaration that a transform preserves source positions;
- an extension-supplied source map;
- a diagnostic clearly labeled as referring to transformed source;
- degradation when no trustworthy mapping exists.

Chained transforms and insertions or deletions before an error are required
cases. This problem affects template, CSS, and JS diagnostics alike.

### 6.4 CSS data and custom properties

CSS research must distinguish two categories:

1. Citry-generated custom properties whose producer is `css_data()` and whose
   names may be generated or namespaced by Citry.
2. Arbitrary author-written `var(--name)` references that may resolve from the
   current rule, component data, an ancestor, a global theme, inline style,
   an external stylesheet, `@property`, CSSOM mutation, or the host page.

Selector-scoped CSS does not stop custom-property inheritance. Therefore
`Component.CSS.scoped` alone cannot make arbitrary `var()` references a closed
local namespace. The study will investigate:

- exact checks for compiler-owned generated properties;
- local declarations and `var()` fallbacks;
- optional app-wide theme or token manifests;
- `@property` syntax, initial values, and `inherits: false`;
- namespace and alias rules between Python field names and CSS names such as
  `row-color`;
- reference files similar to Stylelint;
- external dependencies, inline styles, shadow DOM, pseudo-elements, and
  runtime theme injection;
- unused `CssData` fields as a different, potentially more reliable diagnostic
  than unknown external references;
- a standards-grade CSS parser with positioned diagnostics and source maps.

The result may intentionally offer strict errors only for Citry-owned
properties, configurable warnings for manifest-backed author properties, and
no missing-source diagnostic for the remaining open world.

### 6.5 JS data and TypeScript

The JS study will determine whether `JsData` can drive the serialized `data`
member of a typed `$component` context. It must model browser-visible JSON, not
merely the Python validation annotation. Dates, decimals, enums, aliases,
custom serializers, large integers, non-string mapping keys, unions, tuples,
and nested records are required cases.

The prototype must cover at least:

```js
$component(({ data }) => { /* ... */ })
$component((ctx) => { /* ctx.data ... */ })
$component(handler)
$component({ init(ctx) { /* ... */ }, props: { /* ... */ } })
```

It will answer:

- whether a generated `.d.ts`, virtual TypeScript file, or both are needed;
- how inline Python strings and external `.js` or `.ts` files map diagnostics
  back to their source;
- when named handlers lose contextual typing;
- how extension-provided `$component` context fields compose without making
  `data` unknown;
- when the current regex rewrite must be replaced or preceded by real JS
  parsing;
- which rules belong in `citry check`, CI, and the future LSP, never render;
- whether Citry needs a structured portable type IR in introspection, or a
  purpose-specific serialization schema separate from display metadata.

### 6.6 Checker, editor, and diagnostic architecture

The leading architecture hypothesis is a reusable analyzer library.
`citry check`, a future LSP, class-creation checks, and development runtime
checks would adapt the same fact and rule definitions rather than implement
parallel validators. L1 will compare that hypothesis with separate
stage-specific implementations before the final design selects it.

Research will compare:

- a source-only mode that never imports user code;
- an import/discovery mode that observes actual registration, inheritance, and
  source hooks;
- a hybrid mode with static results upgraded by a long-lived discovered
  registry;
- generated virtual Python for expression typing;
- generated virtual TypeScript for component JS;
- standard CSS language-service delegation for component CSS.

The dependency graph must invalidate consumers after changes to component
schemas, bases, extension configuration, engine/global declarations, template
source, asset source, and registry identity. Checking only changed or staged
files is insufficient when a widely used contract changes.

### 6.7 Closed data-contract profile

An opt-in strict profile could trade some dynamic behavior for a genuinely
closed field set that earlier validation may trust. The leading hypothesis is
one ergonomic preset backed by independent capabilities:

- freeze the engine template-global name set from `Citry(...)` construction;
- reject per-render template globals for that engine;
- prevent extensions from adding, replacing, or removing top-level template
  data fields;
- apply the same top-level protection independently to JS data and CSS data.

These are distinct facts even if one public preset enables all of them. A user
may eventually want strict template supply while allowing a CSS-data
extension. The plan will avoid calling this deterministic mode: arbitrary data
methods may still read time, databases, randomness, or mutable nested values.
The strongest initial promise is a closed top-level data contract.

Questions to resolve include:

- construction-time freezing versus `Citry.initialize()` or a new explicit
  finalization lifecycle;
- configuration of the default Citry instance before imports complete;
- whether an explicitly empty per-render mapping is forbidden or allowed as
  an isolation operation;
- mixed-engine trees, because the current render-global `ContextVar` is not
  engine-keyed and a strict child can inherit globals from a non-strict outer
  render;
- read-only `Mapping` views for extension hooks versus before/after mutation
  auditing;
- the difference between top-level field-set stability and deep immutability
  of lists, dictionaries, models, or arbitrary objects;
- strict-policy identity in analyzer, compiled-template, and render-cache
  invalidation;
- future exact schemas for selected per-render globals without reopening the
  namespace arbitrarily.

Observer hooks must remain usable. The built-in Dependencies and Events hooks
read the three payloads while updating separate render metadata, so strict
mode should not ban `on_component_data` itself. Source-transforming extension
hooks remain a separate demand and source-mapping dimension even when supply
mappings are read-only.

### 6.8 Browser runtime error mapping through client-graph provenance

A development-only browser error overlay is the concrete feature that decides
whether the client ownership manifest should keep its source provenance. When
an Alpine expression or a `$component` script throws at runtime, the overlay
should show the authored template span that produced the failing element, the
way a Vite overlay shows the offending source line, rather than a bare stack
trace against generated markup.

The raw material already exists in the manifest. Here, a **component-tag
client binding** is a browser-side `$c-props`, `@click`, or `@c-poll.5s`
binding resolved from a nested `<c-*>` tag. The parent owns its expression or
handler, while the child supplies the component boundary where the browser
applies it. Every recorded nested component
tag, client binding, fill, and slot outlet carries an `origin`, a
byte range into its component's post-`on_template_loaded` template source, and
a `sourcePos` line and column. The browser receives these today and never reads
them (it only checks their shape). Two things are missing before they can drive
an overlay: the browser holds no copy of that template source, and a byte range
in the transformed source is not the authored position.

The decision, from the payload measurements in the client-graph package review,
is to make this provenance development-only:

- Production keeps `sourceLocations` empty and nulls its references. The
  omitted records are roughly half of the uncompressed manifest and about a
  quarter of the gzipped manifest, and production never reads them, so this
  honors the objective that production does not pay for editor-only features
  (section 2).
- Development keeps the provenance, and the build additionally ships the
  relevant template source (inline, fetched, or as a source map) so the overlay
  can resolve `origin` plus the byte range into a snippet. Line and column stay
  as a human-readable navigation aid.

Turning a transformed-source byte range back into an authored position is the
E3 problem below: these are post-hook coordinates, so the overlay must use a
trustworthy map when one exists and otherwise show the transformed snippet with
an explicit label, never silently claim an authored line. The overlay
correlates a failing DOM node to a graph record through its `data-cid`, then to
that record's call or client binding location.

Sub-questions for this feature:

- how development ships the template source without inflating production;
- how a browser runtime error is attributed to one graph record when several
  bindings share an element;
- whether component-JS errors are in scope, since those need JS source maps
  rather than template offsets.

**Falsifier:** if no common runtime failure can be attributed to a specific
authored span even with the provenance present, the provenance earns no place
in any payload and the offsets leave the manifest entirely.

---

## 7. Feasibility experiments

Each experiment produces a small harness, a written result, representative
diagnostic examples, and a falsifier result. Prototypes are disposable unless
the later design explicitly adopts them.

### R1: comparative tooling evidence matrix

Walk official documentation and, where behavior is load-bearing,
implementation code for Angular, Vue/Volar, Svelte, Jinja, TypeScript language
services, Stylelint, Pydantic/FastAPI, and the most relevant systems already
surveyed in `ide_research/`. Record, with versions and dates:

- strictness tiers and local escape hatches;
- supply and demand declarations;
- generated or virtual source and whether authors can inspect it;
- source mapping across transformed content;
- incremental dependency and invalidation models;
- CLI, editor, and runtime division of responsibility;
- diagnostic positioning, wording, related information, and error codes;
- known limitations and false-positive strategies.

**Falsifier for borrowing a pattern:** the pattern depends on a single-language
compiler or closed build graph that Citry's Python, template, JS, and CSS
boundaries cannot reproduce. Record the mismatch rather than copying the API
shape. R1 findings must be cited by the T1, C1, J2, and L1 reports where they
influence a decision.

### T1: positioned template-name validator

Use the existing Rust AST tokens in Python immediately after parsing. Compare
root free-variable demand with a supplied finite field set. Cover expressions,
component inputs, nested template attributes, loops, fills, Unicode names,
repeated uses, and source positions.

**Falsifier:** ordinary lexical constructs frequently report names that are
not context requirements. If so, first improve demand metadata and perform the
required parser and cross-binding design gate.

### T2: effective template-supply classifier

Classify components with:

- the base `template_data()` plus closed `Kwargs`;
- the base method plus open kwargs;
- a custom method plus `TemplateData`;
- a custom method without a schema;
- inherited methods and schema resets;
- dataclass, NamedTuple, Pydantic, and unknown adapters;
- Pydantic `extra="ignore"`, `extra="allow"`, and `extra="forbid"` policies,
  defaults, aliases, coercion, and preservation of the original mapping;
- `None`, mapping, and schema-instance outputs;
- library-component definitions and their materialized runtime classes.

**Falsifier:** the same supposedly closed class can produce different field
sets through an ordinary supported path without dynamic globals or extensions.

### T3: runtime preflight

After final component data and applicable extensions are available, compare
the actual context keys with positioned template demand before expression
execution. Exercise false branches, `on_render()` replacement, mutable and
per-render globals, cache hit and miss, extension addition and removal, hot
reload, and post-parse node injection.

**Falsifier:** preflight rejects documented valid renders in cases that are
not intentionally moved to a stricter contract.

### T4: expression-side bindings

Probe walrus assignment and any other expression construct that introduces a
name. Decide whether to reject assignment syntax, model cross-expression
bindings, or keep affected templates dynamic.

**Falsifier:** a local expression can introduce names in path-dependent ways
that make root-demand validation unreliable without a much larger data-flow
analysis.

### G1: global-data modes

Prototype exact declared engine globals, live open engine globals, declared
per-render globals, and arbitrary per-render mappings. Evaluate errors,
warnings, completion, invalidation, and call-site analysis.

**Falsifier for strict compilation:** a supported render can later provide a
name that an earlier unconditional check rejected.

### G2: closed data-contract lifecycle

Prototype a construction setting that freezes the engine global-name set and
forbids per-render globals, while keeping its guarantees as separately modeled
capabilities. Exercise explicit and lazy initialization, rendering before
initialization, attempted mutation, the default and explicit engines, hot
reload, concurrent access, nested renders, mixed strict/open engine trees, and
an explicitly empty per-render mapping.

**Falsifier:** no lifecycle boundary provides exact name knowledge without
making ordinary startup configuration impractical, or a strict component can
still inherit globals through a mixed-engine render. In that case prefer
declared global schemas, engine-keyed transport, or an explicit configuration
finalization API over a misleading strict flag.

### S1: normalization authority

Compare "validate only" with "construct and use canonical schema output" for
all five schema roles. Exercise defaults, factories, coercion, aliases,
validators, nested values, returned schema instances, and Pydantic's ignore,
allow, and forbid extra-field policies. Verify both the accepted constructor
input and the actual mapping delivered to each consumer.

**Falsifier for schema-as-guarantee:** an accepted runtime output can omit or
change a field that the static schema claims is available.

### S2: single-definition authoring lab

Implement the six authoring models from section 6.2 across a small corpus of
simple, inherited, conditional, and helper-heavy components. Run Python,
mypy, Pyright, introspection, and serialization probes.

**Falsifier for body inference:** common methods become unknown or yield
unstable field sets, making inference more surprising than an explicit schema.

### E1: extension effect matrix

Classify every public hook by the facts it can observe and change. Prototype
per-channel metadata, one additive shape, and an unknown fallback. Prove that
one dynamic effect degrades only the affected conclusion.

**Falsifier:** common useful extensions collapse to the dynamic category, or a
declared effect becomes unsound when selected by per-component configuration,
hook ordering, or conditional behavior. In either case the model is too coarse
to justify its authoring and cache-invalidation cost.

### E2: development effect auditor

Snapshot shallow and nested values around hooks and try to catch undeclared
additions, removals, replacements, and mutations. Include mutable custom
objects and intentional observer hooks.

**Falsifier:** auditing requires unsafe deep copies or cannot catch common
mutations at acceptable cost. In that case keep effect declarations trusted
and testable by extension authors, but not runtime-audited automatically.

### E3: transformed-source mapping

Apply one and several template, JS, and CSS source transforms that insert,
delete, and replace text before a known invalid reference. Compare
identity-preserving declarations, extension-supplied source maps, and
transformed-source-only diagnostics. Verify chained-map composition and expose
the transformed source for debugging.

**Falsifier:** an extension cannot provide or compose a trustworthy map for a
common transformation. The affected diagnostic must then degrade or point to
transformed source with explicit labeling, never silently claim an authored
position.

### E4: read-only extension payloads

Pass top-level read-only template, JS, and CSS data mappings through built-in
observer hooks and representative user extensions. Test assignment, update,
deletion, replacement, concrete-dict assumptions, nested mutation,
`context.extra`, root-marker updates, per-component extension configuration,
and cache hit/miss behavior.

**Falsifier:** common observer extensions require concrete mutable
dictionaries, or nested mutation is common enough that "closed payload" would
mislead users. If so, narrow the promise to field-set stability, use audited
effect declarations, or require canonical immutable payload values.

### C0: CSS emission safety

Before static CSS validation, define valid custom-property names and safe value
serialization. Test malicious and malformed keys/values, typed values, and a
deliberate raw-value API if one is needed.

**Falsifier:** string interpolation cannot support the desired CSS value model
safely. Adopt a parsed or typed declaration builder instead.

### C1: CSS provenance lab

Use a standards-grade parser to extract custom-property declarations,
`var()` references, fallbacks, and `@property` rules with source spans. Exercise
component roots, ancestors, global tokens, external dependencies, inline
styles, scoped selectors, shadow DOM, and runtime mutation in a browser.

**Falsifier for local closure:** a selector-scoped component validly consumes a
property from outside its local declarations. Standards indicate this will be
common.

### C2: CSS policy prototypes

Compare generated-name checking, Python-to-CSS aliases, component-local
declarations, namespace conventions, app token manifests, reference files,
fallback-aware warnings, and unused-field checks.

**Falsifier for an app-wide closed world:** ordinary host-page or dependency
CSS cannot be enumerated without restricting supported integration patterns.

### J1: serialized type model

Build a Python-schema to portable-JSON matrix, distinguishing validation and
serialization shapes. Include every type listed in section 6.5 and compare
actual `json.dumps` output with the proposed model.

**Falsifier:** supported adapters or serializers can change browser-visible
shape without exposing structured metadata. Such cases must degrade to
`unknown` or require an explicit serialization contract.

### J2: virtual TypeScript prototype

Generate a typed `$component` preamble or virtual file, run `tsc --noEmit`, and
map diagnostics back for all supported registration forms, inline source, and
external source. Test ordinary JavaScript through `allowJs`/`checkJs` and JSDoc
or contextual typing as well as TypeScript. Expose the generated file for
debugging.

**Falsifier:** source mapping is inaccurate or the supported forms require
rewriting that changes JavaScript semantics. Narrow the typed surface rather
than returning misleading errors.

### L1: analyzer mode comparison

Run the same template-name rule through source-only, import/discovery, class
creation, and runtime modes. Record which facts each mode knows and ensure the
same semantic rule and applicable source position are preserved. Record when
the actionable failure requires a related stage-specific diagnostic identity.

**Falsifier:** shared diagnostics conceal materially different semantics. If
so, keep a shared fact model but give stage-specific diagnostics explicit
identities.

### P1: feedback-loop benchmark

Measure time to first actionable diagnostic for:

- clean cold project analysis;
- warm no-change analysis;
- one template edit;
- one component schema edit;
- one widely used base-component edit;
- one extension configuration edit;
- one template-global declaration edit;
- one strict-policy or frozen-global-set edit;
- parallel isolated worktrees;
- cached versus clean diagnostic equivalence.

Record p50 and p95 wall time, work repeated, files invalidated, peak memory,
and whether user imports or side effects ran.

**Global falsifier:** if earlier validation only moves expensive work into
editor startup, imports, class creation, or first render without reducing
edit-to-diagnostic latency, it has failed its purpose.

---

## 8. Research phases and gates

### Phase 0: safety and vocabulary

**Work:** retain C0's landed regression suite and connect it to the broader
security-hardening audit; adopt the feedback-stage vocabulary from section 3;
freeze a representative component and extension corpus.

**Gate:** the reproduced CSS injection class remains closed across fresh
render, fragment, and cache-artifact paths, and every subsequent result names
its validation stage.

### Phase 1: baseline validation ledger

**Work:** complete R1's comparative industry evidence matrix and one local
ledger row per boundary using the fields from section 2. Add runtime harnesses
for schema defaults/coercion, hook ordering, cache behavior, walrus assignment,
and false branches.

**Gate:** each claim is tied to a test or explicitly marked unknown. The ledger
separates field-set, requiredness, value-type, serialization, and use-site
validation. The R1 matrix records versioned primary evidence, limitations, and
which later experiment consumes each relevant pattern.

### Phase 2: template name prototype

**Work:** T1 through T4, G1, and G2, using the existing Python-visible AST
first.

**Gate:** positioned diagnostics work for the closed subset, dynamic cases
degrade deliberately, and the branch-sensitivity decision is ready for
maintainer review.

### Phase 3: data authoring and normalization

**Work:** S1 and S2. Determine which declaration is authoritative for runtime,
static supply, introspection, and serialized output.

**Gate:** at least two viable authoring models have been implemented on the
same corpus; their duplication, typing, runtime, and tool behavior is measured.

### Phase 4: extension effects

**Work:** E1 through E4. Include every supply and source-transform hook,
built-ins, user extensions, per-component configuration, conditional effects,
ordering, source mapping, and cache invalidation.

**Gate:** one dynamic extension invalidates only affected facts, false effect
declarations have a documented failure and testing model, and transformed
sources either map accurately to authored files or identify themselves as
transformed-source diagnostics.

### Phase 5: CSS validation

**Work:** C1 and C2 after the C0 safety contract is understood. Coordinate with
the scoped-CSS design without assuming selector scoping isolates variables,
and consume E3's source-mapping result.

**Gate:** the design labels exact errors, configurable warnings, open-world
unknowns, and runtime safety separately. Browser tests support all inheritance
claims.

### Phase 6: JS and TypeScript validation

**Work:** J1 and J2. Reconcile with the source-language, asset-compiler, and IDE
plans, and consume E3's source-mapping result.

**Gate:** generated types describe actual serialized values, supported
`$component` forms type-check, diagnostic mapping is accurate, and TypeScript
does not enter the render path.

### Phase 7: checker and incremental feedback

**Work:** L1 and P1. Compare the reusable-analyzer hypothesis with
stage-specific implementations. If the evidence supports a shared core,
define its import/static modes, dependency graph, cache key, CLI surface, LSP
adapter boundary, and diagnostic identity model.

**Gate:** clean and cached results agree, transitive consumers invalidate, and
the accepted latency budgets are met on representative and parallel-worktree
cases.

### Phase 8: design closeout

**Outputs:**

- a maintainer-reviewed normative `early_validation.md` design;
- the R1 comparative tooling evidence matrix;
- a validation ledger covering every in-scope component data boundary;
- decisions for template supply, globals, extension effects, CSS policy, JS
  serialization types, and dynamic escape hatches;
- an implementation plan with alternatives and falsifiers;
- reconciled updates to `ide_integration.md`, `source_languages.md`,
  `asset_compiler.md`, `extensions.md`, and any affected schema documentation;
- an explicit cross-language and cross-binding audit if parser, AST,
  `LangImpl`, PyO3, or stubs must change;
- benchmark results and regression budgets.

**Gate:** no feature is called "compile-time validated" without specifying its
known subset, dynamic fallback, feedback stage, invalidation model, and measured
latency.

---

## 9. Decision principles

The research will use these principles to judge competing designs:

1. Prefer one executable declaration that can serve runtime and tooling, but
   do not hide arbitrary Python behind an unsound static claim.
2. Treat demand and supply as separate proofs. A declared field shape does not
   prove every runtime path supplies the field, just as `SlotInput[T]` does not
   prove every executed outlet passes every promised key.
3. Keep extension uncertainty narrow and explicit. Do not special-case
   built-in extension names when an effect contract can express the fact.
4. Describe serialized browser data, not Python validation inputs, when
   generating JS types.
5. Treat arbitrary CSS custom properties as open-world unless the application
   opts into a closed manifest. Selector scoping is not variable scoping.
6. Reuse one semantic fact and diagnostic model across batch, editor, import,
   compilation, and runtime adapters.
7. Preserve positioned runtime checks wherever static knowledge is incomplete.
8. Make generated or virtual source inspectable. Hidden code generation makes
   source-map failures hard to trust and debug.
9. Measure the full feedback cycle, including cold starts, transitive
   invalidation, and parallel worktrees.
10. Prefer a narrow local escape hatch over disabling a rule for an entire
    component or project.

---

## 10. Questions intentionally left open

This plan does not yet decide:

- whether `TemplateData` remains a separate declaration;
- whether schema construction should become the canonical runtime output;
- whether missing names in dead branches become early errors;
- whether template globals gain optional schemas or remain open by default;
- whether a closed data-contract preset exists, which independent capabilities
  it expands to, and where its configuration freezes;
- the syntax and trust model for extension effect declarations;
- whether CSS data names are generated, aliased, underscored, or explicitly
  mapped;
- whether a CSS token manifest is first-party, extension-owned, or left to
  Stylelint configuration;
- whether JS types come from a general introspection type IR, JSON Schema, or a
  purpose-built serialization graph;
- which `$component` registration forms receive full contextual typing;
- which checks run automatically at class creation and which require
  `citry check`;
- whether the existing parser metadata is sufficient after the walrus and
  post-parse-extension probes.

Those are the outputs of the research, not assumptions that should be baked
into its harnesses.
