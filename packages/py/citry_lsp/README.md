# Citry language server

`citry-lsp` provides parser diagnostics, component-aware completion and hover,
lexical template navigation, precise component navigation, document symbols,
and formatting for Citry templates. Component completion offers both
registered tag spellings and a valid class-name spelling such as `c-CButton`,
with the typed prefix deciding which form ranks first.

Even without an app, completion offers Citry's structural tags and
host-specific directive snippets. Parser-proven `c-for` and `c-fill` bindings
complete and hover inside their lexical scope, including shorthand loops,
destructured or aliased slot data, fallback names, and nested template values.
Hovering a structural tag, fixed Citry directive, or structural attribute also
shows concise first-party documentation with a link to the corresponding
`citry.dev` guide. This includes syntax such as `<c-slot>`, `required`,
`c-bind`, and `#c-key`, and does not depend on a registry or HTML provider.
Structural start-tag completion adds the primary syntax and places the cursor
in its value, for example `<c-for each="">` and `<c-if cond="">`; closing tags
remain bare names. These schema-free features do not claim that any user
component exists.

The server also exposes a version-bound HTML-provider projection used by the
VS Code client. It extracts the deepest parser-proven nested template from a
`c-*` attribute and maps its fragment back to the authored source. It also
projects a `<c-element>` start tag to its statically proven literal target, or
to a generic custom element when `c-is` or `c-bind` keeps the target dynamic.
This works in syntax-only mode. Invalid current syntax, non-contiguous or
non-linear Python literal text, stale versions, and unproven source ranges
return no projection.

Install it in the same Python environment as the Citry project for registry
knowledge. The first release requires Citry 0.4.0 or newer in the 0.4 series:

```console
python -m pip install citry-lsp
citry-lsp
```

The editor supplies an optional `module:attribute` registry target during LSP
initialization. The target may be a configured `Citry` instance or a
`ComponentLibrary`. A library target is useful while authoring a reusable
package without a host application:

```json
{
  "citry.app": "citry_ui:__citry_library__"
}
```

For a library target, the server creates an isolated registry containing
Citry's built-ins and that library. Host-application components,
configuration, and host-provided extensions are not included. If the library
requires one of those extensions, expose a configured `Citry` instance that
installs the library and select that instance instead.

With no target configured, the server runs in reported `syntax-only` mode. It
still validates definite inline component templates and documents explicitly
assigned the `citry-html` language, but it does not infer unknown components
or component contracts.

Registry mode also describes the data exposed by typed slots. Completion
inside a direct fill binding such as `data="{ row, ... }"` offers the remaining
fields, while slot and component hover show the complete known field set.
Inside a proven component template, expression completion also offers the
declared `TemplateData` roots, runtime globals, and lint-only variables from an
empty expression through partial typing. This applies to interpolations and
Python-valued attributes. Runtime globals receive conservative value-derived
types; lint annotations and descriptions remain available on hover. Hover and
go-to-definition on an exact component-data root link back to its annotated
Python field.
When `TemplateData` is absent, a conservative CPython-AST pass also recognizes
literal keys returned directly by `template_data()`, modelled local mapping
operations, and the inherited implementation that returns effective `Kwargs`.
Literal roots link to their exact dict-key source; kwargs-derived roots retain
their schema type and annotated-field target. Only a pristine direct `kwargs`
return or simple alias receives that treatment because typed `Kwargs` is not
modelled as a mutable dict. Open Python documents use their synchronized editor
text immediately, including unsaved key changes.

Declared `TemplateData` remains authoritative. If a physical template is
inherited or shared, the server exposes only roots proven for every registered
consumer and returns every distinct definition location where applicable.
Invalid source, ambiguous ownership, unmodelled mapping escapes, and
normalization-changing string keys produce no guess.

Registry-owned component CSS receives the corresponding cross-language data
assistance. Inside `var(--...)`, completion offers exact `CssData` field names,
hover shows their Python producer annotations and descriptions, and Definition
and Declaration navigate to the annotated field. References stay inside the
same physical CSS asset and add every exact Python origin when requested.
Without `CssData`, direct literal string keys inferred conservatively from
`css_data()` receive the same assistance, including hyphenated names such as
`--row-color`. Direct inline `css` literals and resolved `css_file` documents
are supported. Shared stylesheets retain only names supplied by every proven
consumer, and synchronized Python edits revalidate the schema and CSS asset
owner before a result is returned.

This is producer provenance, not a closed CSS namespace. Citry does not report
an unknown custom property or an unused `CssData` field because values may
come from or be consumed by the host page, ancestors, themes, JavaScript,
extensions, or external stylesheets. Ordinary CSS completion, hover, local
custom-property navigation, and validation continue to come from the editor's
CSS provider.

Registry-owned Alpine expressions and component JavaScript receive the same
cross-language assistance for browser data. Declared `JsData` fields, or
direct keys inferred conservatively from `js_data()`, complete as top-level
Alpine names with JSON-derived JavaScript types. Hover, Definition,
Declaration, and References link those names to the exact Python field or
returned dict key. In component JavaScript, the same contract types
the complete `$component` callback context. This includes `data`, `scope`,
read-only `props`, `state`, effects, dependency helpers, and event functions.
Direct synchronous writes to `scope.name`, `scope["name"]`, or a static
`Object.assign(scope, {...})` become typed names in the component's Alpine
subtree. A static `$component({ props, init })` declaration types `props`;
dynamic prop declarations remain unknown.

Free Alpine roots outside the proven component scope are errors by default.
The application or component lint policy can reduce this to a warning, ignore
it, or declare a typed analysis-only Alpine global. An `x-for` value, key, or
index binding receives its iterable-derived type, hover, Definition,
Declaration, and References inside its exact subtree.

Free names inside a proven `$component` callback or configuration `init`
function are also errors by default. This catches context values such as
`scope` when code uses them without destructuring them from the callback
argument. `rule_unknown_component_js_variable` configures the severity, and
`component_js_globals` declares typed globals genuinely supplied by the host
page. Citry browser magics and `$component` context bindings show concise
first-party hover help with links to the browser API reference.

Public Events `State` fields type `$state` in Alpine and both `$state` and the
callback `state` value in component JavaScript. A literal `sendEvent()` or
`$sendEvent()` name, a declarative `@c-*` handler, and a handler passed to
`$loading()` or `$error()` are checked against the component's effective
server-event handlers and navigate to the Python method. These literal
positions and declarative values also complete handler names. Dynamic event
names remain open, and
`onEvent()`/`$onEvent()` accept any browser event name.

A direct `$c-props="{...}"` object on a statically resolved child is checked
against that child's static `$component({props})` declaration. Unknown keys,
missing required props, and incompatible proven value types are errors;
hover and navigation on a key open the child JavaScript declaration. A spread
keeps its explicit keys checkable but suppresses a missing-required conclusion.
Dynamic component targets and `c-$c-props` values remain unproven. Shared
templates and JavaScript assets retain only facts proven for every owner.

The VS Code client maps each exact browser expression or component JavaScript
asset into a stable JavaScript document, so the installed JavaScript provider
can retain its analysis while the authored source changes. Only the
registry-backed provider handles such a region; the generic embedded fallback
is reserved for syntax-only documents. Citry keeps Python-backed names and
their navigation authoritative, and generated-document targets never escape
into authored navigation. A `JsData` field
whose annotation, or known literal value, cannot cross Citry's strict JSON
wire receives the warning `citry.js-data.unsupported-type` and is typed as
`unknown`; actual values still pass through runtime serialization.

Go to References lists every use of a proven root or exact `c-for`/`c-fill`
binding in the same physical template, including nested templates. Sibling
bindings with the same spelling remain separate. When the client requests
declarations, Citry adds the lexical introduction or every exact Python field
or inferred dict-key origin. Go to Declaration uses that same authored origin.

The server also runs its pinned Python analyzer for proven expression roots.
Member and call completion, hover, go to definition, signature help, and
diagnostics therefore use the real declared or inferred Python type inside
interpolations, Python-valued attributes, loop clauses, and nested templates.
Citry recreates `c-if` narrowing and `c-for` comprehension scope in an unsaved
Python document. For discoverability, member completion on a direct optional
root offers the non-`None` member surface through an analysis-only guard. Hover
and diagnostics still use the authored union, so dereferencing that root
without real template narrowing remains an error. The copied component source
uses synchronized editor text before each query. Because the pinned analyzer
still resolves an imported module from disk, Citry conservatively withholds
semantic results while another open Python file has unsaved changes instead of
returning stale types. A physical template shared by several components keeps
only member completion and signatures valid for every proven consumer and
return path.

Go to Type Definition follows a proven root or lexical value to its actual
Python class or standard-library type. It returns no result when any shared
consumer or inferred return path lacks a safe, source-mapped type target.
An untyped `c-fill` binding targets its current `Any` contract even if it is
unused. Synchronized edits to component inheritance or template declarations
are checked before a catalog consumer is trusted, so navigation does not keep
using a template that an unsaved Python edit has moved elsewhere.
That freshness proof accepts direct string literals and direct
`pathlib.Path("...")` declarations. Imported constants, factories, decorators,
metaclasses, and other dynamic asset selection remain usable from the loaded
registry, but registry-backed variable results are withheld while any Python
buffer is synchronized because their full dependency set cannot be proven.
References for Python-local names and members remain outside this first
Citry-owned navigation slice.

Variable hover uses the same Python-highlighted declaration shape as ordinary
Python tooling, for example `(variable) method: str | None`, followed by the
Citry provenance that explains whether the name came from `TemplateData`,
`template_data()`, `Kwargs`, a loop, or a fill. Real template conditions narrow
the displayed type. Shared templates retain every proven consumer type, while
an unavailable or incomplete analyzer answer falls back to the declared type
and Citry provenance instead of showing a partial result.

Citry conservatively withholds semantic results for assignment-expression flow
that the Python shadow cannot reproduce exactly, including walruses in loop
hosts. Parser diagnostics and Citry-owned root intelligence remain available.

`citry-lsp` installs the supported analyzer automatically. It resolves the
executable from the selected Python environment rather than `PATH`, and passes
that interpreter's prefix to the analyzer for matching third-party module
resolution. If the process is missing, has the wrong version, exits, or times
out, the server shows one degradation notice and keeps parser diagnostics,
root completion, root hover, and root navigation active. Private members and definitely
receiver-proven sandbox restrictions, including `str.format`, type `mro`, and
generator or coroutine frame/code access, are not offered.

Registry mode diagnoses a parser-proven free root that is unavailable in the
component namespace. The policy comes from `LintSettings` on the selected
`Citry` instance and defaults to error. Runtime globals, lint-only declarations,
and extension contributions count as known. Explicitly extra-preserving
schemas cap unknown names at warning; unknown or absent schemas stay strict by
default. Warning-only reports do not fail `citry check`, and syntax-only
documents do not guess a component namespace. The stable diagnostic code is
`citry.template.unknown-variable`.

Component definitions use the catalog's loaded Python file and qualified class
name to select an unambiguous class definition. Component input attributes and
static fill slot names use per-field authoring provenance to select an exact
annotated field. Inferred return keys use private worker provenance for the
full class-to-method-owner chain and revalidate it against current source. A
generated, local, duplicate, unreadable, invalid, or otherwise ambiguous
declaration produces no definition target. Open Python files are joined
against synchronized editor text; closed files are joined against the current
on-disk AST. Component-tag navigation keeps its existing safe file fallback.

The server imports the configured app or library in a bounded worker
subprocess. Project output, `SystemExit`, hangs, and crashes cannot corrupt the
LSP stdio transport. Each workspace folder needs its own server process so its
Python interpreter and registry target remain independent.

The console command also accepts pygls transport options such as `--tcp` for
development. With no transport flag it uses stdio, which is the production
editor integration mode.

## Formatting

Protocol v1 dynamically registers standard document formatting only for the
`citry-html` language beneath that server's workspace root. This keeps
independent servers correctly routed in a multi-root editor, including a
workspace opened through a symlink. Python keeps its selected Python formatter
and uses the versioned `citry/formatTemplates` request for either every definite
inline template or the template containing one cursor position. Both routes
format the current synchronized text, reject stale document versions, and
return no edit when formatting is refused.

Custom document-scope requests also accept an `html` document when the loaded
registry proves that its URI is a resolved `template_file`. Unrelated HTML
remains ineligible, and standard formatting is still registered only for
`citry-html`.

Clients that need to own formatter routing can set the protocol v1
`standardFormatting` initialization option to `false` and use the custom
request. The option defaults to `true`; diagnostics and other language features
are unchanged when it is disabled.

The formatter applies the shared structural Citry/HTML policy, the built-in
Python expression and `c-for` provider, and Citry's `c-fill data` layout. The
active Python provider identity is included in additive project status; the
protocol remains version 1.

Clients may additionally advertise this protocol-v1 initialization option:

```json
{
  "embeddedFormatting": {
    "version": 1,
    "languages": ["javascript", "css"],
    "providerSelection": "vscode-first-result"
  }
}
```

The `citry/formatComponentAssets` request uses the same document or position
scope as `citry/formatTemplates`, but includes proven direct `js` and `css`
literals. During that request, the server sends immutable virtual documents
through `citry/formatEmbedded`. It accepts results only when the document
version, plan, region identities, cardinality, delimiter constraints, and final
Citry or Python parse all remain valid. A stale or malformed response produces
no edit.

`vscode-first-result` names the public editor selection mechanism. It does not
identify the formatter extension that supplied a result. Project status and
format responses therefore leave provider identity and version unset unless a
future client can prove them. Clients without this capability still receive
Citry structure and Python-expression formatting; JavaScript and CSS remain
unchanged and are returned as explicit notices.

For an isolated syntax-only process that cannot import the project registry:

```console
uvx --from citry-lsp citry-lsp
```
