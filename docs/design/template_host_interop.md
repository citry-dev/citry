# Design: host template interoperability

**Status (2026-08-22): implemented and release-qualified for Citry 0.4.3 and
Citry Core 1.6.0.** The generic host APIs are ready to release. The separate
Django adapter remains a proof of concept with the explicit compatibility
limits below. Formatter and checker support is deliberately host-agnostic, not
a plugin framework for Django formatting, highlighting, or hints.

This document records three decisions:

1. Add `Citry.render_template()` as an independent public feature.
2. Expose provider-owned foreign source spans with structured body,
   attribute-value, and start-tag representations.
3. Treat owner-dispatched foreign compilation, compiled-body rendering, fill
   collection, and provider analysis scopes as part of the supported integration
   surface. A serious adapter cannot safely rebuild those operations from
   private Citry internals.

Citry core remains unaware of Django, ERB, or any other foreign syntax. A Django
adapter remains a separate package. The migration outcome matters: a project
using Django templates or django-components should be able to opt into Citry,
keep its existing template syntax, and migrate individual regions over time.

For the extension system see [`extensions.md`](extensions.md). For template
loading and invalidation see [`asset_loading.md`](asset_loading.md). For render
objects and serialization see
[`component_rendering.md`](component_rendering.md). For the grammar contract see
[`template_grammar.md`](template_grammar.md).

---

## 1. Problem and intended outcome

A compatibility adapter needs to support both directions.

### 1.1 Django syntax inside a Citry component

```django
{% load wagtailimages_tags %}
<article class="{% if featured %}featured{% endif %}">
  {% for item in items %}
    <c-alert c-message="item.title" />
  {% endfor %}
</article>
```

Django must drive its block. Its `ForNode` binds `item`, then invokes a Citry
segment with that live context. Rendering the Citry body first would produce one
copy before `item` exists. Rendering Django to source and reparsing the result
would make data that happens to contain template delimiters executable.

### 1.2 Citry syntax inside a Django template

```django
{% extends "base.html" %}

{% block content %}
  {% for article in articles %}
    <c-article-card c-article="article" />
  {% endfor %}
{% endblock %}
```

Django owns the file, inheritance, loaders, libraries, context processors, and
loop. When Django reaches the component region it needs a public way to render
that Citry source with the current variables. The source is not itself a
declared component template, so the host should not have to invent and cache a
public component class.

### 1.3 Why this is part of Citry's migration story

The important first step is not a perfect mixed-language template. It is a
low-cost adoption path. Existing django-components templates already contain
Django filters, tags, includes, third-party libraries, and context-processor
values. Requiring those templates to be translated before their component
classes can move to Citry defeats gradual migration.

The mixed mode may remain a compatibility mode. New Citry code should still
prefer native constructs such as `c-class`, Python expressions, and Citry
control flow.

---

## 2. Prior art and repository constraints

### 2.1 Citry's current pipeline

- [`assets.py:271`](../../packages/py/citry/citry/assets.py#L271) loads a
  component template, runs `on_template_loaded`, and caches one `CitryTemplate`
  on the component class.
- [`component_render.py:1510`](../../packages/py/citry/citry/component_render.py#L1510)
  lazily compiles that template on first render.
- [`component_render.py:1572`](../../packages/py/citry/citry/component_render.py#L1572)
  owns the Rust parse, Rust compile, and Python `exec` pipeline.
- [`component_render.py:1185`](../../packages/py/citry/citry/component_render.py#L1185)
  generates a fresh body, runs `on_template_compiled`, precomputes constants,
  and stores the result in the const-body cache.
- [`component_render.py:1655`](../../packages/py/citry/citry/component_render.py#L1655)
  renders an already-compiled body against a `CitryContext`. This function is
  private today.
- [`assets.py:432`](../../packages/py/citry/citry/assets.py#L432) defines template
  reset and cache eviction.

### 2.2 Parser and compiler facts that constrain the design

- [`parser.rs:92`](../../crates/citry_template_parser/src/parser.rs#L92) accepts
  source, expression language, and tag rules. There is no parser-options object.
- [`ast.rs:75`](../../crates/citry_template_parser/src/ast.rs#L75) stores Pest
  offsets as UTF-8 byte indices.
- [`ast.rs:850`](../../crates/citry_template_parser/src/ast.rs#L850) defines the
  body union as `Node | Expr | Text`.
- [`grammar.pest:371`](../../crates/citry_template_parser/src/grammar.pest#L371)
  makes quoted attribute values atomic. They do not contain body-level template
  elements.
- [`ast.rs:354`](../../crates/citry_template_parser/src/ast.rs#L354) stores an
  attribute as one key token and one optional value token.
- [`compiler.rs:469`](../../crates/citry_template_parser/src/compiler.rs#L469)
  flattens an ordinary HTML element into ordered output items.
- [`compiler.rs:496`](../../crates/citry_template_parser/src/compiler.rs#L496)
  groups a start tag's attributes into one `ElementAttrsNode` when any attribute
  is dynamic.
- [`compiler.rs:955`](../../crates/citry_template_parser/src/compiler.rs#L955)
  keeps component attributes inside one `ComponentNode`; they are not body
  items.
- [`component_render.py:1629`](../../packages/py/citry/citry/component_render.py#L1629)
  has private prior art for compiling a template-valued attribute. It runs the
  compiled hook, but it does not carry a root parse envelope or foreign span set.

These facts mean a body-only `TemplateElement::Foreign(Text)` does not, by
itself, explain foreign syntax inside attribute values or between attributes.

### 2.3 Extension, cache, and tooling constraints

- The load and compiled hooks are declared at
  [`extension.py:840`](../../packages/py/citry/citry/extension.py#L840) and
  [`extension.py:858`](../../packages/py/citry/citry/extension.py#L858), with
  manager entry points at
  [`extension.py:1844`](../../packages/py/citry/citry/extension.py#L1844) and
  [`extension.py:1881`](../../packages/py/citry/citry/extension.py#L1881).
- An extension implementing template hooks participates in render-cache deny
  mode at [`extension.py:793`](../../packages/py/citry/citry/extension.py#L793).
  The new hook must join that list.
- Unknown extension node types remain live during const precomputation at
  [`constness.py:489`](../../packages/py/citry/citry/constness.py#L489), which is
  the safe behavior for host-owned runtime nodes.
- The checker calls the low-level parser directly at
  [`_checker.py:413`](../../packages/py/citry/citry/_checker.py#L413).
- Structural formatting calls the formatter without an engine or extensions at
  [`_formatter.py:527`](../../packages/py/citry/citry/_formatter.py#L527).
- The PyO3 parse signature and handwritten type surface live at
  [`template_parser.rs:59`](../../crates/citry_core_py/src/template_parser.rs#L59)
  and [`_rust.pyi:454`](../../packages/py/citry_core/citry_core/_rust.pyi#L454).

Successful runtime rendering alone is not enough. Check, formatter, analysis,
LSP, PyO3, and the public AST all need an explicit outcome.

### 2.4 The public Django proof of concept

The external reference is
[`joeyjurjens/citry-django-poc` at `0e00e168`](https://github.com/joeyjurjens/citry-django-poc/tree/0e00e1685434282ff5c3ac6dff5de42f6c5492e0).
Its code and fixtures demonstrate a sound intended control direction: Django
compiles its own tags plus synthetic Citry segment nodes, then calls the
selected Citry segments with its live context.

The exact Citry patch is not public. The repository expects an ignored local
`citry-src/` checkout, as shown in its
[`pyproject.toml`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/pyproject.toml#L4-L6)
and
[`README`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/README.md#L84-L94).
The public commit therefore cannot reproduce the claimed Citry parser suite or
adapter suite, and its hardest parser behavior cannot be inspected.

---

## 3. Design principles

1. **Citry does not learn foreign delimiters.** The provider tokenizes its own
   language and submits validated source ranges.
2. **Source and data never trade places.** Citry output passed back to a host is
   a rendered value, never new host template source.
3. **Each engine drives its own control flow.** A host loop decides how many
   times a Citry segment renders. A Citry loop decides how many times a host node
   renders.
4. **The parser owns exclusions.** A source rewrite may change content. A
   foreign span tells the parser which authored bytes it must not interpret.
5. **Ownership is explicit.** Two installed providers must not consume each
   other's foreign nodes.
6. **Offsets use one unit.** Citry parser, AST, diagnostics, and foreign spans use
   half-open UTF-8 byte ranges.
7. **Unsupported crossings fail loudly.** A block that crosses a Citry component,
   slot, or branch body is an error, not plausible output.
8. **Standalone source is a real render root, but not a public component.** It
   uses the normal render pipeline without polluting the component registry.

---

## 4. Alternatives considered

### 4.1 Keep only `on_template_loaded()`

A rewrite into `<c-foreign>` works in body position and fails inside:

```html
<div class="{% if active %}on{% endif %}">x</div>
```

Replacing host syntax with text markers keeps the source parseable, but current
attributes are atomic and component attributes are nested inside runtime nodes.
Recovering exact ordered nodes after compilation requires re-deriving the
structure and positions that the parser already knew. Adding a sidecar source
map and ordered claims would be a foreign-span design under another name.

**Rejected for the full migration goal.** The existing hook remains useful for
ordinary source transformations.

### 4.2 Add explicit `<c-host>` and `{% citry %}` constructs

This is small, predictable, and suitable for a conservative official adapter.
It does not preserve existing Django templates, cannot appear in an attribute
value, and cannot support a host block that lazily re-renders Citry segments.

**Kept as a possible simple adapter mode, rejected as the gradual-migration
mechanism.**

### 4.3 Render Django fully, then Citry

This preserves Django's page structure, but Citry components inside a Django
loop arrive only as rendered text or as source that must be parsed later. The
first loses live Citry rendering and the second creates source/data injection
risk. Citry identity and dependency records are also flattened.

**Rejected.**

### 4.4 Render Citry fully, then Django

Django cannot re-render a Citry segment per loop iteration after Citry has
flattened it. It also lets foreign tags affect output after Citry validated a
different HTML shape.

**Rejected.**

### 4.5 Teach Citry Django or ERB delimiters

This couples the Rust grammar to one host and still reimplements host lexer
rules such as Django `verbatim`, quoting, loaded libraries, and third-party tag
parsers.

**Rejected.**

### 4.6 Call a Python tokenizer from the Rust parser

This puts arbitrary Python, GIL, and exception behavior inside a language-neutral
parser. Other bindings could not use the same contract, and parser caching would
depend on host callbacks.

**Rejected.** Precomputed owned spans are the smaller boundary.

### 4.7 Parse two complete trees and merge them

The trees are not required to agree. This is legal Django output:

```django
{% if active %}<div>{% endif %}</div>
```

The integration only needs ordered callbacks, not one combined structural tree.
Tree merging adds restrictions without solving cross-engine render control.

**Rejected.**

### 4.8 Conclusion on necessity

For live, two-way, zero-rewrite migration, parser-owned source partitioning is
the best current candidate. A source-partition or token-stream API might provide
the same semantic capability without exposing literal ranges as the final
parser representation. The exact POC representation is not established. In
particular, a grammar marker plus only one body AST variant is not yet proven
sufficient.

---

## 5. Public standalone rendering API

Use `render_template`, not `render_fragment`. In Citry, “fragment” already
describes HTML/dependency serialization modes.

```python
django_compile_context = django_extension.compile_context(
    engine=django_engine,
    libraries=loaded_libraries,  # Preserved in Django load order.
)

render = app.render_template(
    source,
    variables,
    slots=slots,
    template_globals={"request": request},
    provides={"django": django_context},
    foreign_compile_contexts=[django_compile_context],
    origin="templates/card.html:citry-region-2",
)
```

Proposed signature:

```python
class ForeignCompileContext(Protocol):
    provider: str
    cache_fingerprint: bytes | str


class Citry:
    def render_template(
        self,
        source: str,
        variables: Mapping[str, Any] | None = None,
        *,
        slots: Mapping[str, Any] | None = None,
        template_globals: Mapping[str, Any] | None = None,
        provides: Mapping[str, Any] | None = None,
        foreign_compile_contexts: Sequence[ForeignCompileContext] = (),
        origin: str = "<render_template>",
    ) -> CitryRender: ...
```

### 5.1 Semantics

- `source` is trusted template code. Runtime values are never compiled.
- `variables`, `slots`, `template_globals`, and `provides` are copied at the
  public boundary.
- `foreign_compile_contexts` is an optional adapter-to-provider channel.
  Ordinary callers do not pass it. Each item is a typed, immutable value created
  by the target provider, not a raw mapping assembled by the caller. It carries
  compile-time host state that is neither a template variable nor a runtime
  provide, such as the selected Django engine and the ordered `{% load %}`
  libraries surrounding an extracted Citry region. The value identifies its
  provider and exposes a deterministic fingerprint before span discovery, so
  core can check the standalone-template cache without rerunning Django's lexer.
- Precedence remains engine template globals, render template globals, then
  `variables`, matching the component pipeline.
- The returned value is a normal `CitryRender`. The caller chooses how and when
  to serialize it.
- The synthetic root is transparent. Actual components inside the source retain
  normal identity, ownership, dependencies, and extension behavior.
- Root `<c-slot />` uses `slots` when supplied, otherwise it renders its fallback
  or empty output under the existing slot rules.
- Variable names such as `self` and `slots` are not silently dropped. The
  implementation passes a mapping into a render element directly instead of
  expanding the mapping as component constructor keywords.
- Parse, compile, and render errors name `origin`.

Every cached source has an immutable `template_id` distinct from the synthetic
root class and from `origin`. Template load, foreign-span, compiled, reset, and
eviction contexts carry that ID plus origin and template kind. Extensions key
template-specific state by this ID. Reusing one internal root class must not let
loaded libraries, compiled metadata, or reset events collide across sources.

### 5.2 Implementation model

Do not create ordinary public component classes per source. Every normal
`Component` subclass auto-registers at
[`component.py:476`](../../packages/py/citry/citry/component.py#L476), while the
current private-class authority is restricted to built-in initialization at
[`component_registry.py:187`](../../packages/py/citry/citry/component_registry.py#L187).
A generated-class LRU built on that path would pollute registry names, tag rules,
class IDs, and lifecycle hooks even after LRU eviction.

Preferred implementation:

1. Add one core-owned transparent template-root class or an equivalent internal
   render-root object per `Citry` instance.
2. Store the selected compiled `CitryTemplate` on the render work item, not on a
   public registry entry.
3. Let the normal input, data, ownership, dependency, child-render, error, and
   serialize pipeline run.
4. Let the compile path accept a `CitryTemplate` override rather than always
   loading one from `type(component)`.
5. Carry the active template origin in render context so runtime node errors do
   not consult a synthetic class's unrelated template.

This requires extending existing template hooks, which identify a template
primarily through `component_class`, with the immutable template identity. Cache
eviction fires a template-evicted lifecycle event so extensions can discard
state even when the shared root class remains alive.

If a private class per cached source proves materially simpler, core must add an
unforgeable anonymous-class path, keep those classes out of every public
registry, and define eviction lifecycle. Ordinary metaclass registration is not
acceptable.

### 5.3 Cache contract

- The cache is bounded and owned by one `Citry` instance.
- The key contains the complete source or a digest plus an equality-checked
  source record. A digest alone is not identity.
- Compilation context includes the owning `Citry`, parser options, installed
  extensions, tag-rule revision, and any security mode that changes compilation.
- The key contains installed foreign-provider revisions and the ordered
  `(provider, cache_fingerprint)` values from supplied
  `ForeignCompileContext`s. These cover external state such as the selected
  Django engine, builtins, ordered libraries, and policy settings before core
  decides whether span discovery is needed. If no per-call context exists, the
  provider's immutable configuration or invalidation revision supplies its
  identity.
- `origin` is either part of the key or render-local metadata. Reusing one cached
  record must never report another caller's origin.
- Registration changes that alter parse-time component rules invalidate or
  revision the cache.
- `Citry.clear()` clears it.
- First compilation is thread-safe. A concurrency test must begin from a cold
  cache.

---

## 6. Provider-owned foreign spans

### 6.1 Low-level parser input

Introduce parser options instead of appending positional arguments forever:

```rust
pub struct ParseOptions {
    pub foreign_spans: Vec<OwnedForeignSpan>,
}

pub struct OwnedForeignSpan {
    pub start_byte: usize,
    pub end_byte: usize,
    pub provider: String,
    pub ordinal: usize,
}
```

The existing Rust `parse_template()` stays as a compatibility wrapper using
default options. PyO3 exposes a typed `ForeignSpan` and a keyword-only parser
option. A low-level caller may set the provider explicitly. At the extension
layer core assigns it.

### 6.2 Extension hook

```python
@dataclass(frozen=True, slots=True)
class ForeignSpan:
    start_byte: int
    end_byte: int
    may_control_body: bool = False


@dataclass(frozen=True, slots=True)
class ForeignSpanSet:
    spans: tuple[ForeignSpan, ...]
    provider_metadata: object | None = None


class Extension:
    def on_template_foreign_spans(
        self,
        ctx: OnTemplateForeignSpansContext,
    ) -> ForeignSpanSet | None: ...
```

The hook name describes its output and capability: it declares foreign source
spans. `ForeignSpanSet` may also carry binding-side provider state produced by
the same host lexing pass. Calling this a “plan” was accurate but less
self-explanatory at the extension boundary.

`foreign_compile_contexts` and `provider_metadata` travel in opposite
directions. The former are optional typed inputs from the embedding adapter to
their providers. The latter is output from the provider's span-discovery pass,
retained so `on_template_foreign_compiled` can reuse tokenization or host
compilation state without storing it on a component class or repeating the
work.

The context contains:

- `citry`
- `component_class`, including the core-owned standalone-template root
- post-`on_template_loaded` `content`
- `origin`
- immutable `template_id`
- template kind: `primary` or `standalone`

The manager attaches `extension.name` and an ordinal to every returned span.
Providers cannot claim another provider's identity. Runtime foreign nodes retain
that identity. The adapter's owned compilation context receives only parts with
its identity and protected handles for other content. Existing general-purpose
compiled hooks are trusted extension code, so provider identity prevents
accidental consumption rather than acting as a security boundary.

Only validated spans, provider IDs, ordinals, and structural flags cross the
Rust parser boundary. `provider_metadata` remains binding-side and is recovered
by `template_id` for the owner-dispatched compilation hook. Other bindings
provide the equivalent host-side storage instead of adding Python objects to the
language-neutral AST.

The hook runs once on a compilation-cache miss after `on_template_loaded` and
before the root parser call, including for a `render_template()` source. Cache
identity is already known from source, parser and registry revisions, installed
provider revisions, and the typed compile-context fingerprints. Arbitrary
`provider_metadata` never participates in identity.

Nested template-valued attributes require special handling. Citry recursively
parses them inside Rust at
[`parser.rs:582`](../../crates/citry_template_parser/src/parser.rs#L582), before
Python can invoke another extension hook. `ParserContext` must filter root spans
to the nested token, rebase them for that child parse, and preserve their root
coordinates. The compiler currently discards the validated child AST and emits
only its source at
[`compiler.rs:1432`](../../crates/citry_template_parser/src/compiler.rs#L1432),
then Python reparses that source lazily at
[`nodes/__init__.py:784`](../../packages/py/citry/citry/nodes/__init__.py#L784).
The prototype must either carry the projected spans and provider metadata into
that lazy parse or eliminate the second parse by retaining a compiled child.
Calling the Python hook again on an isolated substring is not equivalent because
it has lost the root provider context.

### 6.3 Validation

Given `source_bytes = content.encode("utf-8")`, core requires:

```text
0 <= start_byte < end_byte <= len(source_bytes)
```

It also requires both endpoints to be UTF-8 character boundaries.

Core then:

- rejects booleans and non-integer offsets;
- requires a non-empty core-assigned provider ID;
- sorts by start, end, provider installation order, and ordinal;
- preserves adjacent spans as separate spans;
- rejects duplicate, overlapping, and nested spans;
- names both providers in a cross-provider conflict;
- does not silently merge or trim spans.

Raw `(int, int)` tuples are too easy to misuse across Python character indices,
JavaScript UTF-16 units, and Rust byte indices. Bindings should also provide
tested helpers for converting host-native positions to Citry byte spans.

### 6.4 Runtime and AST ownership

Use `Foreign` for the public concept. It communicates that another installed
provider owns compilation and rendering of the source part. “Opaque” describes
only the narrower parser implementation detail: Citry's grammar does not inspect
the claimed bytes. A foreign part may compile to active host control flow,
rendered output, explicit literal passthrough, or an error; it is not inherently
inert.

At body level the AST gains an owned foreign element:

```rust
TemplateElement::Foreign(ForeignSourcePart)
```

The compiled Python runtime gains `ForeignNode(source, position, provider,
ordinal, text)`. An extension-owned node fails compilation if its owner does not
explicitly consume it or mark it as literal passthrough. This fail-closed rule
prevents a broken adapter from leaking template source as plausible output. The
low-level parser and formatter can still round-trip a foreign part without a
runtime policy. `collect_fills()` retains the base error behavior unless the
owning provider supplies collection behavior; it must never silently drop a
fill group.

Provider identity is part of equality, representation, PyO3, stubs, formatter
projection, and compiler fixtures.

### 6.5 Structured source parts beyond body text

Foreign spans are not only body elements. The parser must record source parts in
the structures that currently own their bytes:

- body text: `TemplateElement::Foreign`;
- an attribute value: ordered literal and foreign value parts;
- a plain HTML start tag between attributes: ordered attributes and foreign
  start-tag parts;
- raw text containers and comments: body parts split by the sidecar spans;
- nested template-valued attributes: their own rebased spans and owner IDs.

Keep existing `HtmlAttr.value` and `inner_value` accessors for compatibility,
but add a foreign-aware source-parts representation. The compiler uses that
representation rather than scanning generated Python strings for magic marker
text.

For a static attribute:

```html
class="{% if active %}on{% endif %}"
```

the compiler must produce the equivalent of:

```text
attribute value body = [
    Foreign("{% if active %}"),
    "on",
    Foreign("{% endif %}"),
]
```

For a plain HTML start tag:

```django
<div {% html_attrs attrs %} class="card">
```

the compiler must preserve this order:

```text
"<div " + Foreign("{% html_attrs attrs %}") + " class=\"card\">"
```

This is required for django-components migration. Its templates commonly place
attribute-producing tags between the tag name and ordinary attributes.

For v1, a foreign part between ordinary HTML attributes compiles as an ordered
raw start-tag program. Literal source, provider-rendered contributions, and the
closing delimiter render in authored order. Provider output may contain
attribute names, quotes, `/`, or `>`; Citry cannot merge or validate it as an
attribute mapping without reparsing rendered host output. The raw program
therefore bypasses Citry's empty-attribute normalization and duplicate,
`class`, `style`, and `c-bind` merge behavior.

A foreign part inside a quoted ordinary attribute value remains a structured
attribute contribution instead. The provider resolves its ordered value parts,
then Citry performs its existing key validation, class/style merge, boolean and
empty-value normalization, and escaping. Unquoted foreign attribute values are
rejected in v1 because masking their delimiters and internal whitespace cannot
preserve one unambiguous HTML attribute token.

To keep that bypass explicit, v1 rejects a raw foreign start tag that also uses
Citry or extension-owned dynamic attribute semantics on the same element. This
includes `c-bind`, `c-class`, `c-style`, expression-valued `c-*` attributes, and
dynamic event/binding attributes. A later design may define ordered merge
semantics, but the initial prototype must not imply that unknown host output can
participate in `ElementAttrsNode` safely.

Component inputs are separate:

- a plain input such as `title="prefix {{ django_name }}"` may resolve its
  ordered parts through the host and pass the resulting string plus the host's
  safe-string metadata as the kwarg, so later Citry output does not double
  escape it;
- an expression input such as `c-title="..."` remains wholly Citry syntax and
  rejects a foreign part;
- a nested template-valued input may contain foreign parts in its nested Citry
  body, using the projected-span rules above.

These cases need distinct AST and generated-code fixtures. A generic
“foreign-containing attribute” node is not a sufficient semantic contract.

### 6.6 Supported position matrix

| Source position | v1 result | Reason |
|---|---|---|
| Body text | Supported | Direct ordered runtime part |
| Whole `{{ ... }}` expression | Supported | Provider owns the complete delimiter range |
| Quoted ordinary HTML attribute value | Supported as ordered structured value parts | Required for existing Django templates while retaining Citry's attribute escaping and merge locus |
| Unquoted ordinary HTML attribute value | Rejected in v1 | Host delimiters and whitespace cannot remain one unambiguous unquoted value |
| Between attributes on a plain HTML start tag | Supported through a raw ordered start-tag program | Required for tags such as `html_attrs` |
| Foreign plus Citry dynamic attrs on one plain start tag | Rejected in v1 | Unknown host output cannot participate in `ElementAttrsNode` merge rules |
| HTML comment or text-container body | Supported | Django still tokenizes its syntax there |
| Provider verbatim range containing Citry-looking markup | Supported | The whole range is foreign and parser-opaque before Citry parses it |
| Plain Citry component input value | Supported as a host-rendered string kwarg | Required for incremental mixed use |
| `c-*` expression input containing a foreign part | Rejected in v1 | The value must have one expression language |
| Nested template-valued component input | Supported | Uses projected root spans and provider metadata |
| Between component inputs | Rejected in v1 | Runtime host output cannot safely create or remove schema-validated kwargs |
| Citry expression interior | Rejected | Partial ownership would change expression grammar |
| Tag name, end-tag name, attribute name | Rejected | These define Citry structure |
| Span crossing a Citry component, slot, fill, or control-flow body | Rejected by the host adapter | Pairing across independently compiled bodies is ambiguous |

The parser reports a `FOREIGN_SPAN_UNSUPPORTED_POSITION` diagnostic for a
claimed span in a rejected position. It does not treat it as text by accident.

### 6.7 Host control flow, fills, and variable scopes

A provider's foreign span set marks which claims may control whether surrounding
Citry segments materialize. A Django block tag is controlling; a Django variable
token is not. This is trusted provider metadata, not syntax inferred by Citry.

Static fill validation must account for that control. Citry currently recognizes
only its own branches when deciding whether fills are conditional, checking
duplicates and cardinality at
[`parser.rs:3331`](../../crates/citry_template_parser/src/parser.rs#L3331) and
required fills at
[`parser.rs:3425`](../../crates/citry_template_parser/src/parser.rs#L3425).
When a controlling foreign part occurs in a component's fill body, the parser:

1. still validates statically knowable fill names and structurally invalid Citry
   syntax;
2. defers duplicate, required, and maximum-cardinality decisions that depend on
   host branch selection;
3. requires the owning provider's runtime node to implement fill collection;
4. validates the selected fill set against the component schema after the host
   has chosen its branches.

A non-controlling foreign output next to `<c-fill>` remains an error. The parser
must not broadly disable fill-only validation merely because any provider span
is present.

Host bindings also need a tooling representation. In:

```django
{% for item in items %}<c-alert c-message="item.title" />{% endfor %}
```

`item` is not a Citry free variable. The provider's owned compilation and
analysis service must annotate each Citry segment with host-introduced bindings
and their source scope. Rendering overlays the live values; checker and
engine-aware analysis consume the same scope metadata. If a provider cannot
analyze scopes, tooling reports host analysis as unavailable for that segment
instead of emitting a false unresolved-name diagnostic.

V1 permits at most one body-controlling provider in one independently compiled
body list. Disjoint non-controlling providers may coexist. Supporting nested
control by different host engines requires a separately specified composition
order and is not implied by non-overlapping byte spans.

### 6.8 Masking

Masking is an internal parser technique, not the public contract and not the
source of truth. The sidecar owned spans are authoritative.

A correct mask preserves:

- UTF-8 byte length;
- UTF-8 validity;
- `\r`, `\n`, and CRLF placement;
- either the number of Unicode scalar values on each line or enough source-map
  information to calculate columns from the unmasked source;
- lexical inertness in every supported position;
- distinct adjacent spans.

“Same byte length” alone is not sufficient. Replacing a multibyte scalar with
several ASCII bytes changes Pest-derived columns unless columns are recomputed
from the original source. Replacing newlines with filler changes line numbers.
One candidate implementation replaces each non-newline scalar with an inert
scalar of the same UTF-8 width and preserves line breaks exactly, then recovers
all authored contents from the original source and sidecar spans. Another uses
context-specific ASCII masks and never derives line or column information from
the mask.

The structured-source prototype must prove that the chosen neutral characters
remain inert in every supported grammar position. If that cannot be proven, v1
must narrow the supported-position table.

### 6.9 Default handling is authority, not zero risk

An untransformed extension-owned `ForeignNode` fails closed. A provider may
explicitly choose literal passthrough for text-like syntax, but that still
changes what Citry analyzes: used variables, slots, structural validation,
formatter layout, and lint no longer inspect the claimed bytes.

That is the authority the installed provider requested. Documentation should
not call the hook zero risk.

---

## 7. Stable compiled-body integration API

Foreign compilation should not be implemented by asking every generic
`on_template_compiled` hook to walk and mutate the full tree. Add an
owner-dispatched hook and structured body partition:

```python
class Extension:
    def on_template_foreign_compiled(
        self,
        ctx: OnTemplateForeignCompiledContext,
    ) -> None: ...
```

The context carries the matching `template_id`, provider metadata, and only the
owner's foreign claims. For a controlling body, core presents an ordered
partition of owned source parts and protected handles for each run of other
Citry content. The provider may compile its source and embed those segment
handles, but it cannot silently discard or claim another provider's part. For a
non-controlling claim it returns one runtime contribution or explicit literal
passthrough. Core verifies that every claim has an outcome before invoking the
existing general compiled hooks.

General compiled hooks remain trusted and can still rewrite arbitrary nodes.
The owner-dispatched path is a correctness boundary for this feature, not a
sandbox against malicious extension code.

### 7.1 Hook order

The order is fixed:

1. All `on_template_loaded` mapping hooks finish, producing the source Citry
   will actually parse.
2. `on_template_foreign_spans` runs for each provider against that final source.
3. Core validates and combines the span sets, then Rust parses and compiles the
   template into its body generator.
4. On each generated body-list build, `on_template_foreign_compiled` runs first,
   owner-dispatched, and must account for every foreign part.
5. Core verifies that every foreign part was consumed or explicitly converted
   to literal passthrough.
6. Existing `on_template_compiled` mapping hooks run on the resolved provider
   nodes and ordinary Citry nodes.
7. For body types that already participate in the Const cache, const
   precomputation runs and the resulting body is cached.

Therefore `on_template_foreign_compiled` runs immediately before
`on_template_compiled`, not after it. Existing compiled hooks see the provider's
finished runtime nodes and can transform them like any other extension node.
If a provider captures an ordinary Citry run with `ctx.compiled_body(nodes)`,
core applies the existing compiled hooks to that captured run before sealing
the handle. This prevents a provider wrapper from hiding ordinary Citry nodes
from built-in or third-party compiled transformations. The provider's outer
replacement nodes then pass through the normal compiled hook in step 6.
Neither compiled hook is a per-render hook: it runs when a generated body is
built for its compilation/Const cache entry, matching the current order at
[`component_render.py:1222`](../../packages/py/citry/citry/component_render.py#L1222).
The relative owner-hook/general-hook order also applies to nested template
bodies. The current nested path invokes `on_template_compiled` but does not run
const precomputation at
[`component_render.py:1629`](../../packages/py/citry/citry/component_render.py#L1629).
This proposal does not silently change that behavior. Any later unification of
the two paths needs its own tests and benchmark evidence.

### 7.2 Rendering host-selected Citry segments

The proof of concept needs to render already-compiled Citry segments after the
host has selected a branch and added variables. It currently imports private
`_render_body`, `_settle_render`, and `serialize_render` functions from Citry.
That makes the claim that an adapter needs only two public additions incomplete.

Add an extension-facing operation along these lines:

```python
render = render_compiled_body(
    body,
    context,
    variables_overlay=host_context,
    finalize_root=False,
)
```

The exact public home may be an `OnTemplateCompiledContext` service rather than a
module function. Its contract must:

- preserve the original component, provides, ownership graph, and extension
  data;
- overlay live variables without mutating the parent context;
- settle deferred children correctly;
- return a `CitryRender`, not an already serialized string;
- support a fill-collection mode so a host conditional can select Citry
  `<c-fill>` nodes instead of dropping them.

The Django adapter retains each returned render behind a collision-resistant
marker while Django selects, orders, and repeats its nodelist. When the marker
stream returns, the adapter reconstructs one `CitryRender` containing Django
text and the retained nested renders. The enclosing Citry serializer therefore
runs once with the complete ownership tree, dependency placeholders, and CSP
state. A marker that Django transforms, duplicates, or discards fails loudly.
Standard HTML escaping is an intentional flattening boundary: the adapter
serializes that occurrence with dependencies ignored and escapes the resulting
inert text, preserving tags such as a Wagtail `CharBlock` that deliberately
consume rendered HTML as a value.

---

## 8. Reference Django adapter flow

This section describes expected use of the core features. It is not a promise
that Citry core ships Django support.

### 8.1 Citry component containing Django syntax

1. `on_template_loaded` produces the final Citry source.
2. The Django extension tokenizes it with Django's `DebugLexer`.
3. The extension converts Django character offsets into UTF-8 byte spans and
   returns them with template-scoped provider metadata from
   `on_template_foreign_spans`.
4. Citry parses its own structure and returns provider-owned foreign parts in
   source order.
5. Core invokes the Django extension's owner-dispatched foreign compilation hook
   with its source parts, provider metadata, and protected Citry segment handles.
6. It operates per compiled Citry body list through the structured body
   partition protocol.
7. It builds one Django template from Django source parts and an internal marker
   for each run of Citry content.
8. Django's own parser decides tag pairing.
9. During render, Django drives the selected nodelist. Each internal segment
   callback renders its compiled Citry body with the live Django context overlay.
10. Segment callbacks retain structured renders and return inert markers.
    After Django finishes, intact markers become nested Citry render parts so
    the enclosing component is serialized once.

Top-level Django inheritance remains a feature of a Django-owned template, not
of a Citry component body. A mixed adapter may support local tags such as
`load`, `include`, and block control flow inside one Citry body, but it should
reject `extends` there unless it defines and tests component-fragment semantics
for it.

For fill collection, the same Django nodelist runs in collection mode. Its
segment callbacks call Citry's body fill collector and return empty host text.

### 8.2 Django template containing Citry syntax

1. Django's lexer protects Django tokens while a tolerant Citry region scanner
   locates outermost `<c-*>` regions.
2. The scanner must not require unrelated surrounding Django output to be one
   valid Citry HTML document. Django templates and inherited blocks may emit
   partial or conditionally balanced markup.
3. Django compiles a private collision-resistant node for each region.
4. At render time that node calls `Citry.render_template()` with the live Django
   variables, request as a template global, host state as a provide, real source
   origin, outer source map, and extension compile context containing the
   selected Django engine and surrounding library loads.
5. The Citry render is serialized as one independent Django contribution. A CSP
   nonce is read from `csp_nonce`, `CSP_NONCE`, or `request.csp_nonce`.
   Projects that need dependency deduplication across several independent
   regions use the adapter's Sekizai integration.

Rendered HTML crossing either boundary is a value, never template source. The
adapter must preserve Django's autoescape decision and mark only already-rendered
Citry or Django HTML as safe for the receiving engine. Ordinary context values
remain subject to that engine's normal escaping rules.

### 8.3 Expression ownership is adapter policy

`{{ ... }}` is genuinely ambiguous. A live Django filter registry, dotted-path
rule, or Python parse can provide a useful migration heuristic, but every rule
has collisions:

- `a | length` can be a Django filter or Python bitwise OR;
- Django dotted lookup may index mappings and automatically call methods;
- Citry sandbox rules do not apply to an expression delegated to Django;
- selectively loaded filters differ from every filter present in a library.

Core should expose exact spans and leave this policy to the adapter. A mature
adapter should offer at least a documented migration policy, diagnostics for
ambiguous expressions, and an explicit override.

### 8.4 POC migration and upstream handoff

The final integration exercise uses the public POC rather than a new throwaway
adapter:

1. Fork `joeyjurjens/citry-django-poc`, clone the fork outside the Citry
   worktree, add Joey's repository as `upstream`, and preserve an unmodified
   baseline branch at the audited commit or then-current upstream main.
2. On a migration branch, point the POC's existing ignored `citry-src/` source
   entry at the local Citry checkout containing the new APIs. Run `uv sync`,
   then verify `citry.__file__` and `citry_core.__file__` both resolve through
   that local source so an installed wheel cannot mask the implementation under
   test.
3. Replace POC-only Citry patches, character/byte assumptions, global Django
   engine selection, and imports of private runtime functions with the public
   foreign-span, compile-context, `render_template`, compiled-body, and interior
   serialization APIs from this design. Keep its Django-facing architecture
   unless a failing test demonstrates that it must change.
4. Add the Unicode, fills, loaders, multiple engines, relative origins, missing
   variables, selective loads, unmatched `verbatim`, partial-HTML, exact-once
   assets, and cold-concurrency regressions in section 13.6.
5. Run the complete suite and package checks from the fork:

   ```bash
   uv run pytest
   uv run --with ruff ruff check .
   uv run --with ruff ruff format --check .
   uv build --package citry-django
   uv build --package citry-django-sekizai
   ```

6. Compare the fork's output and performance against plain Django, equivalent
   plain Citry work, and the preserved POC baseline wherever that baseline can
   be made runnable.
7. Prepare the upstream branch and draft PR while the Citry release is pending,
   but do not claim PyPI installability. If CI needs it, the draft may
   temporarily pin the exact Citry Git revision.
8. Publish `citry-core` before `citry`, because `citry` exactly pins its core
   package. After both packages are public, remove the POC's local source
   override, set its Citry dependency floor to the actual release, regenerate
   `uv.lock`, and rerun every check from a fresh clone with no `citry-src/`.
9. Open or update the draft PR against Joey's upstream with links to the Citry
   implementation and release plus the supported-crossing matrix. Mark it ready
   only after the fresh-clone, published-package run passes.

This external qualification is complete on the migration branch: the adapter
uses public APIs and its 208 tests pass against the sibling checkout. A final
fresh-clone run against published wheels remains a gate for making the adapter
PR ready, not for publishing the Citry APIs it has already qualified.

---

## 9. Error and diagnostic contract

### 9.1 Core span errors

Core raises deterministic diagnostics for:

- invalid span type;
- empty or reversed range;
- out-of-bounds range;
- endpoint not on a UTF-8 boundary;
- duplicate or overlapping ownership;
- unsupported source position;
- an adapter attempting to claim a foreign part with another provider's ID;
- an unhandled foreign node in a fill group.

Messages include provider, origin, byte range, and both owners for conflicts.

### 9.2 Source positions and mapping

Every AST and runtime foreign part carries its root processed-source byte range.
The internal mask is never shown in diagnostics. Nested attribute positions are
rebased to that root through `ParserContext`.

Citry already documents byte ranges at
[`parse.py:4`](../../packages/py/citry_core/citry_core/template_parser/parse.py#L4),
but the Python formatter builds character indices at
[`error.py:33`](../../packages/py/citry_core/citry_core/safe_eval/error.py#L33),
and template errors pass Rust positions to it directly at
[`exception.py:156`](../../packages/py/citry/citry/util/exception.py#L156).
Byte offsets must be converted before Python string slicing. This is a
prerequisite for claiming non-ASCII-safe foreign-span diagnostics.

Foreign spans index the final string returned by `on_template_loaded`. The
existing hook returns only a string, so a length-changing load transformation
has no map back to the originally loaded file. Exact authored-source diagnostics
therefore require either an offset-preserving transformation or a future loaded
source object that carries a composable source map. Without one, diagnostics
must explicitly describe positions as post-load source positions.

### 9.3 Host errors

A provider that compiles synthetic host source must retain a source map from
synthetic tokens and segment markers back to original Citry byte ranges. A
Django exception should name the component template origin and its authored
line, not `<citry-django>` or a generated hex payload.

An unmatched host block fails through the host parser. A host block that pairs
only by crossing a Citry body boundary fails loudly and includes the Citry
component trace.

---

## 10. Caching, lifecycle, and concurrency

### 10.1 Foreign-span computation

Foreign-span hooks run only on compilation-cache misses, not every render. Their
spans and analysis metadata must be deterministic for the keyed context or the
provider must invalidate the template. External lexer/library state that affects
ownership or host compilation is represented before the lookup by an installed
provider revision or typed `ForeignCompileContext.cache_fingerprint`.

Span ownership joins parser and formatter cache keys. A cache created without
foreign spans cannot serve a parse with them.

### 10.2 Template reset

`reset_template()` removes:

- loaded source;
- compiled AST/body generator;
- const-precomputed bodies;
- provider span/token metadata tied to that immutable template ID.

Providers must not store current template loads or lexer state only on a
component class. Reset and standalone-cache eviction identify the exact template
record and trigger provider cleanup for that ID.

### 10.3 Runtime node caching

A provider may lazily compile its host nodelist once per transformed runtime
node. Cold compilation must be thread-safe. Cached host templates contain only
immutable compilation state; live context stays render-local.

### 10.4 Render cache

`on_template_foreign_spans` is included in extension render-cache participation.
A provider that wants component output caching must either export and restore
the necessary contribution or explicitly bypass it with a stable reason.

---

## 11. Tooling and cross-binding work

### 11.1 Rust and compiler

Audit and update:

- `grammar.pest`, if the prototype proves a grammar marker is needed;
- `ast.rs` body and structured-source parts;
- `parser.rs` and `parser_context.rs` options, validation, masking, rebasing, and
  metadata walkers;
- `compiler.rs` body, attribute, control-flow, fill, and source-order lowering;
- compiler runtime constants and generated-code fixtures;
- every exhaustive `TemplateElement` match;
- all language generators:
  `src/lang/python.rs`, `src/lang/js.rs`, `src/lang/php.rs`,
  `src/lang/go.rs`, and `src/lang/rust.rs`.

The four non-Python code generators are currently unfinished, but parsing in
all five language modes still exposes the same AST and must receive coverage.

### 11.2 Formatter

The low-level formatter accepts `ParseOptions`, preserves foreign-span bytes
exactly, and treats their contents as unknown. It may format Citry-owned source
around a claim, rebases claims internally after each edit, reparses with the
rebased options, and verifies byte idempotence. It never reindents or normalizes
inside an owned span. The Python entry point is
`citry_core.template_formatter.format_template(source, options=options)`.

A host-aware formatter still needs a provider that can obtain the spans. The
core formatter cannot infer Django libraries or run arbitrary Python extensions
by itself.

### 11.3 PyO3 and Python

Update:

- PyO3 span/options and AST types;
- registration and exports in `crates/citry_core_py/src/lib.rs`;
- `_rust.pyi` signatures and variant unions;
- Python parser wrappers and re-exports;
- extension context, base hook, dispatch manager, and cache participation;
- runtime foreign body and attribute nodes;
- compile namespace and dummy compiler runtimes in tests;
- template reset and standalone-template cache;
- public API documentation.

### 11.4 Check, analysis, and LSP

App-aware `citry --app module:engine check` asks installed extensions for spans
against each authored template and parses with those options. Shared consumers
must agree on the claim set. Claimed contents receive no Citry diagnostics. If
any claim may control a body, the checker suppresses the unresolved-name lint
for that mixed template because the host may introduce names;
the remaining Citry validation still runs.

This is intentionally smaller than a provider analysis framework. The checker
does not inspect Django syntax or publish host binding scopes. `citry check
--static`, `citry format`, and the LSP do not import an application, so they
cannot discover extension claims and remain Citry-only. A host adapter or editor
integration that already has spans may call the low-level formatter with
`ParseOptions`; Citry supplies no host-specific formatting, highlighting, or
hints.

---

## 12. Audit of the public POC

The POC's code and fixtures target useful behavior, including lazy Django
blocks, live loop and `with` variables, several Wagtail and third-party tags,
body-consuming tags, normal slots, and inert user data. Because its Citry fork
is absent, those fixtures do not independently verify the claimed upstream
behavior or prove general Django compatibility.

The following findings are design inputs.

| Finding | Evidence | Required resolution |
|---|---|---|
| Core fork and claimed suite are not reproducible | [`docs/citry-upstream.md`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/docs/citry-upstream.md#L69-L78) lists missing upstream work; `citry-src/` and a locked `wagtail-block-components` dependency are absent | Publish an exact patch/fork revision and locked green run |
| Unicode corrupts spans in both directions | [`extension.py:205-243`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/extension.py#L205-L243) forwards Django character offsets as bytes; [`rewrite.py:55-63`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/rewrite.py#L55-L63) slices Python text with Citry byte offsets | Typed byte spans and tested conversion helpers |
| Attribute mechanism is under-specified | The upstream note lists only `TemplateElement::Foreign(Text)` while current attrs are atomic | Publish structured AST and generated-code examples |
| Multiple providers cannot coexist | [`extension.py:266-350`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/extension.py#L266-L350) consumes every core foreign node | Core-attached provider identity and overlap errors |
| Conditional fills can disappear | [`extension.py:142-143`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/extension.py#L142-L143) makes `collect_fills()` a no-op | Host-driven collection mode; default errors instead of dropping |
| Missing variables diverge from Django | [`nodes.py:34-39`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/nodes.py#L34-L39) ignores `ignore_failures` and raises | Match Django resolution for `if`, `firstof`, `with`, and `for` |
| Unclosed `verbatim` is not delegated | [`extension.py:220-243`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/extension.py#L220-L243) drops the unmatched opener from claimed spans | Preserve the opener so Django raises its normal error |
| Whole-file region scanning rejects legal partial HTML | [`rewrite.py:123-135`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/rewrite.py#L123-L135) parses the entire masked Django file as Citry | Use tolerant region discovery or explicitly narrow scope |
| Custom Django loaders are skipped | [`backend.py:46-55`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/backend.py#L46-L55) wraps only default loaders | Loader decorator/configuration for arbitrary loaders |
| Multiple Django engines are ambiguous | [`extension.py:62-86`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/extension.py#L62-L86) prefers alias `django` or first engine | Explicit engine alias/object per adapter instance |
| Relative include/extends lose origin | [`extension.py:110-120`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/extension.py#L110-L120) uses synthetic origin | Carry real template origin and source map |
| Django render state resets at crossings | [`extension.py:124-140`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/extension.py#L124-L140) constructs a fresh context | Preserve or explicitly bridge `render_context`, autoescape, localization, and active template state |
| Selective filter loads are misclassified | [`extension.py:254-263`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/extension.py#L254-L263) records the whole library; [`expressions.py:76-86`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/expressions.py#L76-L86) caches all filters | Track selected names and invalidate live registry caches |
| Expression heuristic changes sandbox behavior | [`expressions.py:39-47`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/expressions.py#L39-L47) delegates every dotted path | Document policy, warn on ambiguity, provide override |
| Internal marker tags can collide | [`templatetags/citry.py:18-28`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/templatetags/citry.py#L18-L28) installs a normal builtin name | Collision-resistant private registration and provenance checks |
| Diagnostics point at generated source | [`rewrite.py:55-63`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/rewrite.py#L55-L63) replaces regions with hex payloads | `origin` plus bidirectional source mapping |
| Assets and serializers can run per region or iteration | [`nodes.py:105-114`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/nodes.py#L105-L114) serializes each root; segment rendering also serializes eagerly; the Sekizai bridge sorts paths alphabetically | Page-wide accumulation, interior serialization, and dependency-preserving first-seen order |
| Adapter depends on private Citry internals | [`extension.py:149-182`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/extension.py#L149-L182) imports private render functions and rebuilds context internals | Stable compiled-body API and structured owned-body partition |
| Template load state can survive hot reload | [`extension.py:209-250`](https://github.com/joeyjurjens/citry-django-poc/blob/0e00e1685434282ff5c3ac6dff5de42f6c5492e0/packages/citry-django/src/citry_django/extension.py#L209-L250) sets class state only when loads exist | Template-scoped metadata and reset handling |

The POC also acknowledges one visible normalization difference: Citry removes
an empty `class` in the attribute test where plain Django keeps `class=""`.
Interop should promise defined semantics, not byte-identical output.

The repository should be treated as an architectural experiment, not a
compatibility release. Its declared `citry>=0.3.2` does not supply the required
unreleased APIs, it has no committed CI or ERB proof, and its concurrency test
warms the compiled path before starting threads. The README claim that segments
never become strings also disagrees with the eager serialization in
`render_segment()`. These do not invalidate the control-flow idea, but they do
limit what the current evidence establishes.

---

## 13. Required proof matrix

### 13.1 Core spans

- Empty, reversed, adjacent, duplicate, overlapping, nested, and out-of-range
  spans.
- Endpoints inside a UTF-8 scalar.
- ASCII and non-ASCII before, inside, and after a span.
- Multiline, `\n`, `\r`, and CRLF spans, with diagnostics before and after.
- Two providers, disjoint ranges, exact conflicts, and partial overlaps.
- Deterministic rejection of two body-controlling providers in one body list.
- Identical source/spans with different compile-context fingerprints do not share
  compiled output.
- Provider reset and cache invalidation.

### 13.2 Source positions

- Body text and whole `{{ ... }}`.
- Ordinary quoted and unquoted attribute values.
- Provider tags between plain HTML attributes.
- Plain, expression, and nested-template component input values.
- Deterministic rejection of foreign plus Citry dynamic attributes on one plain
  start tag.
- HTML comments, script, style, textarea, title, Citry comments, and raw blocks.
- Nested template attributes with root-absolute positions.
- Unsupported tag-name, attribute-name, and partial-expression claims.

### 13.3 Structure and fills

- Citry `if`/`elif`/`else` and `for`/`empty` grouping with foreign parts nearby.
- Host blocks that cross ordinary HTML boundaries.
- Host blocks wholly inside a component, slot, fill, or Citry branch.
- Host blocks crossing those body boundaries, with deterministic errors.
- Host conditionals and loops around named and default `<c-fill>` nodes.
- Deferred duplicate, required, and maximum-fill validation after host branch
  selection.
- Unknown provider nodes in fill groups fail rather than disappear.

### 13.4 `render_template()`

- Variable and template-global precedence.
- Foreign compile context is private to its named provider and changes cache
  identity through its precomputed fingerprint.
- Mapping keys named `self` and `slots`.
- Provides in nested components.
- Root fallback and supplied slots.
- Nested component identity, dependencies, ownership, error fallback, and hooks.
- Source origin at parse, compile, and render time.
- Distinct immutable template IDs across different cached source records and
  hook cleanup on eviction.
- Cold concurrent compilation.
- Bounded eviction, registry revision, reset, and `Citry.clear()`.
- Source is compiled and variables remain inert data.

### 13.5 Tooling and bindings

- Rust parser/compiler fixtures and Python wrapper/runtime tests.
- Five expression-language parse modes.
- PyO3 registration/conversion failures and `_rust.pyi` parity.
- Formatter exact foreign-span preservation and idempotence.
- Checker and engine-aware analysis use the same spans as render.
- Host-introduced bindings have exact segment scopes; unavailable provider
  analysis does not become false unresolved-name errors.
- LSP behavior is documented and tested.

### 13.6 Django adapter qualification

- Django 4.2 through every declared supported release.
- Missing variables in `if`, `firstof`, `with`, and `for`.
- Active `autoescape`, localization, `cycle`, `ifchanged`, and render context
  across every supported crossing.
- Selective library loads and registry invalidation.
- Custom loaders, multiple engines, relative includes, and real origins.
- Partial surrounding HTML and inherited blocks.
- Wagtail and third-party node-list inspection.
- Multiple Citry regions and Django-loop repetition with exactly-once assets.
- Custom `on_serialize`, cache, CSP, and security extensions.
- Unicode template source in both directions.
- Cold concurrent host compilation.

### 13.7 Performance qualification

Capture the baseline before implementing parser or runtime changes, then rerun
the same commands after the internal prototype, the cross-language core change,
and the POC migration. A debug `citry_core` build invalidates all timing results;
the release-build requirement is documented at
[`codebase.md:188`](../codebase.md#L188) and the existing runner procedure is in
[`benchmarks/README.md`](../../benchmarks/README.md).

#### Existing Citry workloads

Build once in release mode, run once to warm the newly built native library and
discard that result, then retain matched runs from the same machine, Python,
dependencies, power state, and checkout state:

```bash
cd packages/py/citry_core
../../../.venv/bin/maturin develop --release
cd ../../..

.venv/bin/python benchmarks/compare.py --size sm --rounds 5
.venv/bin/python benchmarks/compare.py --size lg --rounds 5
.venv/bin/python packages/py/citry/tests/benchmark_const.py
```

Record `startup`, `first`, and `subsequent` for plain Citry. The no-provider
path must keep a fast-path check: it must not allocate hook contexts, span sets,
source maps, or runtime nodes. First run the unchanged base commit against itself
to measure A/A noise. Before implementation, set the regression threshold to
the larger of 3% or twice the observed A/A variation. A result beyond that
threshold requires investigation and explicit justification before merge; the
budget is not revised after seeing the implementation result.

#### Parser/compiler micro-benchmark

Add a release-mode template parser benchmark covering:

- parse and compile with no foreign providers or spans;
- 1, 10, and 100 foreign spans in body text;
- spans in quoted attributes, raw start tags, and nested template-valued inputs;
- ASCII, multibyte Unicode, LF, and CRLF source;
- span validation and provider-conflict failures;
- cold compilation and cached body generation separately.

Report median and p95 time, allocations or peak memory where the harness can
measure them, source bytes, span count, and generated-node count. The zero-span
case is the regression guard for every existing Citry user; the nonzero cases
show the scaling law rather than one favorable template.

#### Python/runtime micro-benchmark

Add a focused script benchmark, verifying rendered output before timing, for:

- an ordinary component with no foreign provider installed;
- a provider installed but returning no spans;
- cold and warm `render_template()` cache paths;
- cold concurrent compilation of the same source;
- Django controlling 100 Citry segment renders;
- Citry controlling repeated Django nodes;
- one final page serialization, with no per-segment invocation of page-wide
  serialization hooks.

The first two cases guard existing users and the provider-installed fast path.
The remaining cases establish absolute mixed-mode costs and scaling. Mixed mode
has no honest pre-feature baseline, so compare it with equivalent ordinary
Citry/Django work and the runnable POC; do not invent a regression percentage.

#### Migrated POC workload

The POC fork adds matched scenarios for:

- a Django template with no Citry syntax;
- a Citry component with no Django syntax while the provider is installed;
- a Django loop invoking a Citry segment many times;
- Django conditionals in body and attribute positions;
- several Citry regions on one page with page-wide assets;
- cold compilation and warm rendering as separate measurements.

Compare the migrated adapter to plain Django and, when the preserved baseline is
runnable, to the original POC on the same commits and dependency versions. Store
the commands, raw samples, medians, environment, and Git revisions with the POC
draft PR. Functional equivalence is checked before timing so a faster wrong
render cannot qualify.

---

## 14. Implementation phases

### Phase 1: publish and reduce the proof

1. Obtain the exact POC Citry patch or reconstruct it as a minimal branch.
2. Add focused failing fixtures for Unicode, attributes, conditional fills,
   multiple providers, diagnostics, and cold concurrency.
3. Record the current generated Rust AST, generated Python code, and runtime
   body for every supported position.
4. Capture the section 13.7 no-provider and parser/compiler performance baseline
   before changing parser or runtime code.

### Phase 2: `render_template()`

1. Add the internal transparent render root and compiled-template override.
2. Add immutable template identity, hook contexts, eviction, the bounded
   per-engine cache, and origin handling.
3. Add public API, typing, documentation, and focused lifecycle tests.
4. Land this independently. It is useful without foreign spans.

### Phase 3: one internal vertical prototype

1. Add non-public parser options, provider identity, and source parts on an
   experiment branch.
2. Run one Django-driven example end to end for body text, a raw ordinary start
   tag, a nested template-valued input, a host-controlled fill, Unicode source,
   and a live host-bound variable.
3. Resolve masking, recursive child parsing, attribute safety, fill validation,
   analysis scopes, and interior serialization before freezing the AST.
4. Record generated AST, host-independent IR, Python code, runtime bodies, and
   failure output for the vertical examples.
5. Run the parser micro-benchmark and existing Citry workloads against the
   prototype without treating exploratory numbers as a release result.

### Phase 4: freeze the cross-language core contract

1. Add the typed foreign span set and compile contexts, provider revisions,
   validation, byte conversion helpers, template identity, and owner-dispatched
   compilation API.
2. Implement the proven body, attribute, nested-template, and fill
   representations.
3. Add compiled-body rendering, interior serialization, and provider analysis
   scopes.
4. Complete AST, all five language generators, PyO3 registration, stubs,
   wrappers, formatter, Rust tests, and Python tests as one contract change.
5. Rerun and record the matched no-provider and foreign-span benchmarks before
   merging the core change.

### Phase 5: adapter and tooling qualification

1. Fork the audited POC, retain its baseline branch, and port its adapter to the
   local Citry implementation using only public APIs.
2. Build or correct the tolerant Django region scanner, loader integration,
   context bridge, and page-wide dependency collector in that fork.
3. Route the app-aware checker through installed span providers; keep static
   checking, the generic formatter command, and LSP explicitly Citry-only.
4. Qualify the fork against sections 13.6 and 13.7, including matched functional
   output and performance evidence.
5. Once the Citry release version is assigned, prepare the draft upstream POC PR
   with the future minimum dependency. After publication, replace local sources
   with the released packages and require the clean-checkout run to pass before
   marking the PR ready.

---

## 15. Falsifiers and remaining decisions

The recommendation changes if any of these is demonstrated:

- A source-mapped `on_template_loaded` implementation preserves ordered body
  and attribute contributions, diagnostics, ownership, live variables, and
  failure boundaries with materially less core complexity. Such an
  implementation will probably have recreated owned spans internally.
- The actual migration scope excludes foreign syntax in attributes and excludes
  live back-and-forth blocks. In that smaller scope explicit host components or
  sequential rendering are sufficient.
- The unpublished POC patch contains a sound structured-attribute design and
  passes section 13. It may replace the internal representation proposed here.
- Providers need nested or overlapping ownership. Flat non-overlapping spans
  cannot express that; the design would need a tokenizer ownership graph.
- A lexically inert, byte- and column-preserving mask cannot be built for the
  supported position matrix. The matrix must then be narrowed.
- A transparent standalone render root cannot preserve normal ownership,
  dependency, extension, and cache behavior without synthetic registry state.
  `render_template()` must then use a first-class non-component render root.

Open product decisions after the first release:

1. Whether Citry ships a minimal official Django adapter in addition to the
   third-party mixed adapter.
2. Whether a future editor integration should load an application. The current
   formatter command and LSP intentionally do not.
3. Whether expression-ownership ambiguity uses warnings, explicit delimiters,
   or a configured precedence mode.
4. Whether `foreign_compile_contexts` remains a public `render_template()`
   keyword or moves into a lower-level typed template-source object used by
   adapters. A hidden context variable or source-prefix rewrite is not an
   acceptable replacement.

---

## 16. Implementation log

### 2026-08-22: pre-implementation baseline

Baseline commit: `f400050a` on the dirty `review` worktree, using CPython
3.14.3, Rust nightly 1.98.0, and a release build of `citry_core`. The first
post-build quick run was discarded. Each recorded value below is the median of
the three five-round series, and A/A spread is `(maximum - minimum) / median`.

| Scenario | Citry phase | Baseline | A/A spread | Regression threshold |
|---|---|---:|---:|---:|
| Small | startup | 117.42 ms | 3.55% | 7.10% |
| Small | import | 110.06 ms | 0.88% | 3.00% |
| Small | first | 8.89 ms | 0.34% | 3.00% |
| Small | subsequent | 249.7 us | 1.84% | 3.68% |
| Large | startup | 129.34 ms | 0.59% | 3.00% |
| Large | import | 108.97 ms | 0.66% | 3.00% |
| Large | first | 85.22 ms | 1.21% | 3.00% |
| Large | subsequent | 42.22 ms | 2.23% | 4.46% |

The existing const benchmark recorded 163.5/73.1 us for the expression-heavy
serialized path, 101.7/34.6 us for render-only, 77.5/58.1 us for the small-card
serialized path, and 37.4/24.9 us for its render-only path. The final
qualification must repeat the same release-build commands and add the focused
foreign-span and mixed-runtime benchmarks from section 13.7.

### 2026-08-22: vertical implementation and qualification

The implementation uses `ForeignSpan` and `ParseOptions` at the Rust boundary.
Every claim carries its provider and ordinal through `TemplateElement::Foreign`,
quoted attribute source parts, and start-tag source parts. Claims are validated
as root-source UTF-8 byte ranges and masked only for grammar parsing. Public
tokens and diagnostics are reconstructed from the immutable original source.

The Python runtime adds `on_template_foreign_spans` followed by
`on_template_foreign_compiled`, then the existing `on_template_compiled`. The
owner hook runs bottom-up for every independent component, slot, fill, branch,
and nested-template body. It must explicitly resolve every provider-owned claim.
Core snapshots every other provider's claim partition around an owner call, so
one provider cannot consume or erase another provider's claim. Captured Citry
runs receive the normal compiled-hook transformations before becoming handles.
Unresolved body and component-input nodes fail closed. A controlling provider
may select Citry fills at runtime; non-controlling foreign output remains
invalid beside a fill group, and statically knowable fill names and data sources
remain parser-validated.

`Citry.render_template()` uses one private transparent root and a bounded
per-engine source cache. It preserves variables named `self` and `slots`, uses
normal component rendering for nested components, serializes through the normal
`CitryRender` API, invalidates on registry changes and `Citry.clear()`, and
compiles a cold source only once across concurrent callers. Host callbacks use
opaque `CompiledBody` values through `render_compiled_body` and
`collect_compiled_body_fills`, so the migrated adapter imports no private render
functions. Handles are tuple-backed and bound to the exact engine and active
template record. Nested templates retain root-source byte coordinates and the
authored origin. Primary and nested cold compilation paths use reentrant locks,
and concurrent primary first loads publish one canonical `CitryTemplate`
record.

The structured attribute prototype proved a useful distinction. A foreign part
inside a quoted ordinary attribute becomes a structured `ForeignHtmlAttr`
contribution and retains Citry's class/style normalization and escaping locus.
A provider claim between attributes has no attribute key, so it remains an
ordered start-tag contribution. The parser rejects combinations with Citry
dynamic or metadata attributes where raw start-tag contribution order would be
ambiguous. When both claim kinds occur in one start tag, the compiler composes
all parts in source order. A span that masks an authored tag name is rejected
against the original source rather than being misclassified as body text.

The public `citry-django-poc` was ported on branch
`codex/citry-foreign-spans-api` against the sibling Citry checkout. Its adapter
now uses the public hooks, `render_template`, and compiled-body APIs. The port
also fixes both directions of the prototype's Python-character versus UTF-8
byte-offset bug, removes stale class-level load-library state, implements
host-selected fill collection, and adds its previously undeclared
`wagtail-block-components` test dependency. Region discovery is now tolerant of
host-controlled partial HTML, ignores Citry-looking text in raw-text and
attribute loci, and preserves dependent Citry control-flow sibling chains. The
adapter carries real origins into both engines and locks cold host compilation.
Host-selected segments now remain structured until the enclosing serialization,
preserving client ownership graphs, event manifests, dependency placeholder
position, and single-pass serialization. Standard Django HTML escaping remains
an explicit flattening boundary. Standalone Django regions pass CSP nonces from
the host context or request. All 208 tests and Ruff checks pass. The adapter's
source-level mypy check also passes when missing third-party imports are ignored;
the POC does not install Django stubs or publish Citry typing metadata.

### 2026-08-22: post-implementation performance

The matched release-build no-provider benchmark remains within every
predeclared threshold:

| Scenario | Citry phase | Baseline | Implementation | Change | Threshold |
|---|---|---:|---:|---:|---:|
| Small | startup | 117.42 ms | 116.42 ms | -0.85% | 7.10% |
| Small | import | 110.06 ms | 112.02 ms | +1.78% | 3.00% |
| Small | first | 8.89 ms | 8.93 ms | +0.45% | 3.00% |
| Small | subsequent | 249.7 us | 251.6 us | +0.76% | 3.68% |
| Large | startup | 129.34 ms | 131.03 ms | +1.31% | 3.00% |
| Large | import | 108.97 ms | 109.73 ms | +0.70% | 3.00% |
| Large | first | 85.22 ms | 87.72 ms | +2.93% | 3.00% |
| Large | subsequent | 42.22 ms | 42.82 ms | +1.42% | 4.46% |

The focused release parser plus compiler benchmark recorded:

| Claims | Source bytes | Median | p95 | Same-size no-claim median |
|---:|---:|---:|---:|---:|
| 0 | 22 | 6.5 us | 6.6 us | 6.5 us |
| 1 | 58 | 11.7 us | 12.1 us | 10.7 us |
| 10 | 382 | 68.1 us | 69.2 us | 55.5 us |
| 100 | 3,802 | 2.280 ms | 2.296 ms | 1.991 ms |

The existing parser is itself nonlinear on the repeated-element workload at
100 elements. Foreign ownership adds about 0.29 ms to that 3.8 KB case. Span
lookups now enter through binary search over the validated sorted list, so an
individual token does not scan claims that ended earlier in the source.

The focused Python runtime benchmark recorded 56.7 us median for an ordinary
component with no provider, 55.9 us with an installed provider returning no
spans, 54.0 us for a warm `render_template`, 47.2 us for a warm one-claim
standalone source, and 88.0 us for a cold unique standalone source. The host
span and compiled hooks each ran once across 2,020 warm renders of the same
source.

### Qualification limits retained after the vertical implementation

- Host-introduced binding scopes have no public analysis result. The app-aware
  checker therefore suppresses unresolved-name findings for a mixed
  template when a provider marks any claim as body-controlling. This is
  intentionally conservative; other Citry validation still runs.
- The generic formatter command, static checker, and LSP do not load an app.
  They remain Citry-only. Callers that already have provider spans can pass
  them to the low-level formatter, which preserves the claimed bytes as
  unknown source.
- Provider compile policy is assumed immutable for the lifetime of a compiled
  template record. A provider whose policy mutates must clear the relevant
  template cache; a revision key may be added if a real mutable provider needs
  it.
- Synthetic Django parser errors do not yet map every internal `citryseg`
  marker back to the authored Citry byte range.
- Foreign-span parser failures still share coarse generic diagnostic codes, and
  some validation failures do not carry the provider-specific claimed range.
  Dedicated foreign diagnostic codes and exact root-source ranges are accepted
  follow-up improvements rather than blockers for the first release.
