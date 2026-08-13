# Design: Content Security Policy and JavaScript delivery

**Status (2026-08-12): complete through phase 11 and promoted.** Alpine core
and morph are upgraded to 3.16.1, and `@alpinejs/csp` is pinned at the same
version. Typed security settings, serialization overrides, and the immutable
`serialize_result()` contract are implemented. Structured scripts now produce
exact SHA-384 metadata, Citry-owned external scripts receive verified SRI, and
trusted tags are reconciled after string hooks. Request-scoped nonces now reach
every structured script, each inline structured style, and browser-created
fragment dependencies, with explicit conflicts rejected. The version-pinned
compatibility checker now feeds `citry check` and the LSP, and a committed CSP
Events runtime is built from the same TypeScript source as the standard
runtime. Warning serialization now reports reached-tree and settled-output
incompatibilities without changing the standard-runtime HTML. Strict
serialization selects the CSP runtime, rejects incompatible reached or final
output, and emits fragments for an already-installed matching manager without
an inline preloader. JavaScript inventory, managed-runtime omission, and
JavaScript-free enforcement now operate above every dependency strategy. The
Citry UI's public and registered internal production components are checked in
CI against the pinned Alpine CSP subset. Documentation snippets remain
teaching material rather than a product compatibility ledger. The landing page
now promotes that graduated path without claiming that Citry constructs the
host's complete header. The implemented Alpine ownership contract remains
[`alpinejs.md`](alpinejs.md). CSRF is a separate browser-request concern and
lives in [`security_csrf.md`](security_csrf.md).

For the wider security audit, see
[`security-hardening.md`](security-hardening.md). For dependency collection,
page serialization, and fragments, see
[`dependencies.md`](dependencies.md).

---

## 1. Decision

Citry should make CSP compatibility and JavaScript delivery first-class,
orthogonal policies.

- The host application owns the CSP response header, nonce generation,
  reporting endpoints, and the rest of the page.
- Citry owns the runtime variant it ships, the expressions it asks that
  runtime to evaluate, and every executable tag it generates.
- A request nonce is passed at final serialization, never stored on the
  long-lived `Citry` instance.
- Strict CSP uses Alpine's CSP build and rejects expressions that its pinned
  interpreter cannot execute.
- A warning mode runs the same compatibility analysis but keeps today's
  standard Alpine runtime and output.
- JavaScript-free rendering is not a stronger CSP mode. It is a separate
  delivery policy for server-rendered HTML.

The proposed public values are explicit strings, not a mix of booleans and
strings:

```python
citry = Citry(
    security_csp="strict",          # "off" | "warn" | "strict"
    security_javascript="allow",   # "allow" | "warn" | "omit" | "forbid"
)

html = component.render().serialize(
    csp_nonce=request.csp_nonce,
)
```

The compatibility-preserving defaults are `security_csp="off"` and
`security_javascript="allow"`. All new long-lived `Citry` security settings
use the `security_` prefix so they remain recognizable if security grows into
a larger settings family. The request-scoped `csp_nonce` serialization input
keeps its established CSP term because it is not an engine setting.

`no_js=False` and `no_js=True` read backwards and leave `True` ambiguous:
does it omit the runtime, reject an `x-data`, or sanitize all authored HTML?
`security_javascript="omit"` and `security_javascript="forbid"` make those two
intentions distinct. If the eventual API keeps the `no_js` spelling, it should
still use the exact string modes `"off"`, `"warn"`, `"omit"`, and `"strict"`;
booleans should not be accepted.

Engine settings are defaults. A serialization override should be available
for a static export, email, or route with a different policy. The nonce is
always serialization-scoped because it belongs to one response.

```python
preview_html = component.render().serialize(security_csp="warn")
email_html = component.render().serialize(security_javascript="omit")
```

## 2. What CSP does

Content Security Policy is an HTTP response policy interpreted by the browser.
Its directives constrain where scripts, styles, images, connections, frames,
and other resources may come from and which inline behavior may execute. It is
a mitigation for injection bugs, not a replacement for escaping,
authorization, or safe application code.

Three script controls matter directly to Citry:

1. Without an allowance, `script-src` blocks inline `<script>` elements,
   native event attributes such as `onclick`, and `javascript:` URLs.
2. A per-response nonce or a content hash can authorize a specific script
   element without enabling all inline script.
3. A nonce does not authorize `eval()`, `Function()`, or `AsyncFunction()`.
   Those string-compilation mechanisms require `unsafe-eval` unless the code
   is refactored.

An Alpine attribute is not a native inline handler. For example,
`@click="count++"` is an HTML attribute that Alpine reads as data; the browser
does not execute it as it would `onclick="count++"`. Standard Alpine still
needs `unsafe-eval` because Alpine compiles that string into a JavaScript
function. Alpine's CSP build removes that particular requirement by
interpreting a restricted expression language.

Style policy is related but separate. A nonce can authorize an inline
`<style>` element. It does not authorize a `style="..."` attribute. A first
Citry CSP release should make this scope explicit:

- `security_csp="strict"` guarantees that Citry's own script runtime and compatible
  Alpine expressions do not require `unsafe-eval` or `unsafe-inline` in
  `script-src`;
- Citry also propagates a supplied nonce to inline style elements it emits;
- it does not claim that arbitrary style attributes, fonts, images,
  connections, frames, or third-party assets satisfy the host's full policy.

The host should use `Content-Security-Policy-Report-Only` while introducing a
policy. That browser facility is complementary to `security_csp="warn"`: report-only
observes what the whole page actually does, while Citry's warning mode can
point to a component source location before deployment.

## 3. Current Citry state

Citry pins Alpine 3.16.1, `@alpinejs/morph` 3.16.1, and `@alpinejs/csp` 3.16.1.
Two committed Events artifacts are built from one TypeScript source. The
default artifact resolves `alpinejs/src/index`; the CSP artifact aliases that
exact entry to `@alpinejs/csp/src/index`. Both retain Citry's directive and
morph instrumentation. Off and warning serialization select the standard
artifact, whose evaluator creates an `AsyncFunction` from each expression
string. Strict serialization selects the CSP artifact and validates the
expressions it can reach before returning HTML.

Citry represents collected dependencies as structured `Script` and `Style`
objects, and dependency hooks may add a nonce to the entries they receive.
That is useful low-level control but not complete CSP support:

- the core dependency manager and framework manifests are added after the
  application-wide dependency hook;
- zero-configuration rendering may inline the manager;
- off and warning fragment serialization emit an inline preloader, while
  strict fragments require an existing matching manager;
- browser-created dependency elements need the nonce of the already-loaded
  document; and
- the standard Alpine evaluator still needs `unsafe-eval` even when every
  script tag has a nonce.

The upstream django-components report that motivated this work was
[`django-components` issue #932](https://github.com/django-components/django-components/issues/932).
Component JavaScript was blocked by a policy that rejected inline scripts,
while the available customization had to be repeated per component and could
not see the request-scoped nonce. Later dependency hooks made tags mutable,
but users still needed shared extension state or a base component to move the
request nonce into final tags. Citry should solve this once at serialization,
not ask each component to solve it.

The strict implementation and the component-by-component UI and documentation
ratification have landed. A nonce hook alone would have solved only one of the
boundaries above; the promoted contract also includes early expression checks,
the matching evaluator, settled-output validation, and explicit example status.

## 4. How Alpine's CSP build works

The standard and CSP packages expose the same Alpine directive and lifecycle
model. Their evaluator is different.

The standard evaluator:

- wraps an expression in `with (scope)`;
- constructs an `AsyncFunction` from the string; and
- caches that generated function by expression.

The CSP package calls `Alpine.setEvaluator()` and
`Alpine.setRawEvaluator()` during bootstrap. Its evaluator tokenizes the
attribute string, parses a small AST, and interprets that AST against Alpine's
merged data and magic scope. It never turns that string into browser code.
Actual JavaScript function values still use Alpine's ordinary function
evaluation path.

For Citry, `alpinejs`, `@alpinejs/morph`, and `@alpinejs/csp` are pinned to
exactly the same version. Phase 1 confirmed 3.16.1 as the latest stable release
on 2026-08-12, upgraded the standard and morph bundles, added the CSP package,
and ran the private-API and focused browser canaries. The three pins must move
together in future upgrades.

### 4.1 Currently audited expression shape

The previously audited 3.15.12 CSP interpreter supports the useful core of
Alpine expressions:

- strings, numbers, booleans, `null`, and `undefined`;
- array and object literals;
- identifiers, property reads, and computed property reads;
- function and method calls;
- arithmetic, comparisons, logical operators, and ternaries;
- simple assignment; and
- prefix and postfix increment or decrement.

That is not full JavaScript. Among the unsupported or prohibited constructs
are:

- arrow functions, destructuring, spreads, and template literals;
- optional chaining, compound assignments such as `+=`, multiple statements,
  declarations, `if`, and `await`;
- browser globals such as `window`, `document`, `console`, `Math`, `JSON`, and
  `parseInt` when referenced from an expression;
- evaluation on `<script>` and `<iframe>` elements;
- prototype-related properties and dangerous DOM mutation methods; and
- `x-html`, which the CSP package replaces with an erroring directive.

Component JavaScript is different. An authorized `Component.js`, `js_file`,
or external dependency is ordinary JavaScript and may use globals, arrow
functions, and the rest of the language. It still must not call `eval()` or a
function constructor when the host's policy excludes `unsafe-eval`.

Upstream's CSP guide currently contradicts itself about nested property
assignment: it shows `x-model="user.name"` as supported while an older
unsupported list still includes `user.name = ...`. The audited 3.15.12 source
does implement non-DOM member assignment. Citry must therefore maintain a
version-pinned executable compatibility corpus rather than copy a prose list
from upstream and assume it is exact. This inventory must be regenerated and
verified against the Alpine version selected by the upgrade in this work
package before it becomes the strict-mode contract.

### 4.2 Impact on current Citry authoring

Common Citry expressions such as `count++`, `count = 0`, method names, object
literals, `$state.count++`, and calls to Citry magics fit the interpreter.
Other current examples do not:

```html
<!-- optional chaining -->
<span x-show="$error('save')?.fieldErrors?.email"></span>

<!-- await and a compound statement -->
<button @click="result = await $sendEvent('preview', { page: 2 })"></button>

<!-- arrow callback and a global -->
<button @click="setTimeout(() => open = true, 200)"></button>
```

Citry UI and the docs also contain `x-html`, global access, arrow functions,
compound assignments, and multi-statement handlers. Strict mode cannot ship
until the compatibility checker covers the real catalog and the supported
components either refactor those expressions or declare that they do not
support strict mode.

The preferred refactor is to move complex logic into authorized component
JavaScript and expose a method or getter on the component scope:

```html
<button @click="openLater">Open</button>
```

This keeps the inline expression small and testable without weakening CSP.

### 4.3 Compatibility checker contract

The compatibility spike is the first, bounded part of the checker phase. It is
not the production checker. Its job is to establish the exact contract before
Citry implements that contract in its portable analysis layer.

The spike runs a checked-in expression corpus against the parser and evaluator
from the exact pinned `@alpinejs/csp` version. Directive-only restrictions,
such as the CSP build rejecting `x-html` even when its expression parses, use a
small browser canary. The corpus covers:

- representative Alpine expressions authored in Citry's UI, documentation,
  and focused test fixtures, with full component-by-component ratification
  remaining phase 10;
- the supported and rejected boundaries of the pinned tokenizer, parser, and
  evaluator, including assignments, updates, calls, object and array literals,
  operators, multiple statements, optional chaining, arrow functions, and
  blocked property access;
- the expression contexts Citry extracts, including value expressions, event
  statements, normal Alpine evaluation, `$c-props`, and `@c-*` arguments.
  Native-element `@c-*` arguments use Alpine's normal evaluator, while
  component-boundary handlers, props, and `@c-*` arguments use its raw
  evaluator. The corpus also covers the synthesized `x-model` and
  `x-modelable` setter and the iterable side of `x-for`;
- representative scope and magic values needed to distinguish parser success
  from evaluator failure.

Each case records the Alpine version, directive or attribute, exact source,
scope fixture when needed, expected compatibility, and expected failure class.
The development runner may be disposable, but the versioned corpus remains as
a release conformance fixture. A dependency upgrade must rerun it and reconcile
every changed result before the compatibility version is advanced. The spike is
deliberately finite: it samples the real Citry catalog and checks targeted
grammar boundaries, not an open-ended fuzzing or benchmarking exercise.

The production checker then implements the proven classification in Citry's
portable browser-analysis layer. A fail-closed recursive-descent parser mirrors
the small pinned Alpine CSP grammar and preserves UTF-8 ranges; existing OXC
analysis remains responsible for free-name discovery. Normal `citry check` and
IDE operation do not start Node, load a browser, or evaluate application code.
One version constant ties the classifier, corpus, CSP client bundle, and Alpine
pin together. Conformance tests run every corpus case against the real pinned
evaluator and against Citry's static expectation. `"compatible"` means
source-compatible, not that runtime values were proven safe. Corpus cases that
deliberately inject a known browser-global value are marked
`"runtime-dependent"`; other value-dependent enforcement remains with the
browser evaluator.

For one template, the analysis flow is:

1. the Citry parser identifies exact Alpine and Citry expression hosts;
2. the portable host record supplies the browser-canonical element tag and
   directive name, expression mode, UTF-8 source range, lexical bindings, and
   whether Alpine uses its normal or raw evaluator path. Phase 6 extends
   `BrowserExpression` with that context and normalizes HTML tag and attribute
   names using ASCII case folding so
   spellings such as `X-HTML` cannot bypass the checker;
3. the pinned classifier checks directive support, grammar, and statically
   identifiable evaluator restrictions;
4. one structured Citry finding is mapped back to the authored range;
5. `citry check` and the LSP render that same finding, and editor clients merely
   display the LSP diagnostic.

A finding should point at the smallest unsupported token or directive that
Citry's classifier can prove, and otherwise at the exact expression or
attribute range. Alpine's parser does not consistently retain source spans, so
token-level ranges are a Citry classifier requirement rather than an assumed
upstream feature. Every finding names both the pinned Alpine version and an
actionable refactor. For example:

```text
citry.csp.incompatible-browser-code
Alpine CSP 3.16.1 cannot evaluate arrow functions here. Move the logic to
Component.js and call a scope method, for example @click="openLater".
```

The central diagnostic catalog owns the stable code, message variants, help
URL, and examples. A physical source range and rule are reported once even
when several component registrations consume the same template.

The selected Citry application supplies its configured engine-default mode to
project tooling:

- `"off"` produces no CSP compatibility findings;
- `"warn"` produces warning diagnostics while the standard Alpine runtime
  remains selected;
- `"strict"` produces error diagnostics;
- syntax-only checking without a selected application does not guess a CSP
  policy.

The LSP discovery snapshot therefore needs to carry the selected engine's
configured `security_csp` value. A per-serialization override is intentionally
not predicted by project tooling; reached-tree serialization enforces it. VS
Code, PyCharm, and other LSP clients require no editor-specific checker. A
browser playground may call the same portable classifier only when the example
explicitly selects a CSP analysis mode and its worker protocol preserves the
diagnostic severity.

Static acceptance cannot prove facts that depend on runtime values, such as a
scope method returning a browser global or an otherwise ordinary object being
a DOM object. The CSP evaluator remains the enforcement boundary for those
cases. Later settled-output validation also covers dynamically produced
attributes and extension output. The checker guarantees parity for its
versioned, source-classifiable contract; it must not claim that every possible
runtime value was statically proven safe.

## 5. CSP modes

The proposed modes have deliberately different runtime behavior.

| Mode | Runtime | Diagnostics | Output claim |
|---|---|---|---|
| `"off"` | Standard Alpine | No CSP-compatibility diagnostics | Current behavior. It does not disable a host CSP header. |
| `"warn"` | Standard Alpine | Warn for everything that would fail strict mode | Migration aid only. Output still needs `unsafe-eval` when it evaluates Alpine expressions. |
| `"strict"` | Version-matched Alpine CSP build | Unsupported behavior is an error | Citry-owned script execution can run without `unsafe-eval` or `unsafe-inline` when the host supplies the matching policy and nonce. |

Warning mode must not switch to the CSP evaluator and then continue after a
warning. An unsupported expression would stop working in the browser. It must
leave output behavior unchanged and report that strict mode is not ready.

Diagnostics should be structured Citry findings, rendered by `citry check`,
the IDE, or the development terminal. They should be deduplicated by source
location and rule when that identity survives rendering. When an arbitrary
string hook makes the source site unknowable, render-time validation keeps
instances separate rather than hiding a potentially distinct conditional
site. Dynamic attributes and extension-added tags still need a final
render-time check.
Project checking may report every discoverable component; strict
serialization fails only for behavior reached by that rendered tree and its
emitted dependencies.

## 6. Nonce and serialization contract

The host generates a fresh, unpredictable nonce for one response and places
the matching nonce source in its CSP header. The application passes the raw
nonce value once:

```python
html = page.render().serialize(csp_nonce=request.csp_nonce)
```

Citry then:

1. validates that the value is a non-empty CSP base64 value, while leaving
   entropy and freshness to the host;
2. applies it after extensions have contributed dependencies;
3. adds it to every structured Citry dependency script and inline style
   element, including core and extension output;
4. records it in the document manager for later dependency creation; and
5. rejects a dependency that already carries a different nonce.

An identical explicit dependency nonce is accepted. Silently replacing a
different nonce could conceal stale request state, so it is an error. Without
a response nonce, explicit dependency nonces remain untouched.

The same value may be placed on script and style elements. The host decides
whether `script-src`, `style-src`, or both include it. Inert
`type="application/json"` data blocks do not execute, but consistently
annotating all Citry-owned script elements avoids special cases in final tag
processing.

A full-page cache must not reuse nonce-bearing HTML with a newly generated
header. The HTML and header must be produced under the same request nonce.
In strict mode, document or simple serialization requires a nonce whenever it
would emit an executable script or inline style. A fully static result may omit
it. Supplying a nonce in off or warning mode is still useful during a staged
host-policy rollout.

### 6.1 Final output validation

Structured dependencies are not the whole document. Strict mode needs a final
HTML pass that can identify:

- raw `<script>` elements, including inert-looking data and manifest blocks;
- any ASCII-case-insensitive `on*` attribute, conservatively treating the
  browser event-handler namespace as executable;
- `javascript:` URLs;
- Alpine attributes and their expression source;
- inline `<style>` elements; and
- framework and extension manifests.

That pass is a compatibility validator and nonce applicator, not a general
HTML sanitizer. It rejects native inline JavaScript that a nonce cannot
authorize, but it does not claim that trusted component JavaScript, third-party
packages, host markup outside the Citry render, or every CSP directive is safe.

Raw `<script>` and `<style>` elements authored directly in template HTML are
not automatically nonced. Automatically blessing every final tag would turn a
raw-HTML injection into trusted code. Strict mode rejects those raw elements
and points the author to `Component.js`, `Component.css`, or a structured
`Dependencies` entry. Those APIs are explicit trusted-code surfaces and are
the only elements Citry nonces automatically. A host layout outside the Citry
render remains the host's responsibility.

All raw script elements are rejected, not only executable MIME types. Citry's
manager consumes inert JSON manifests, so trusting a raw manifest by tag shape
would let unstructured markup enter a security-sensitive protocol. Structured
Citry manifests are distinguished by a per-serialization private marker that
is verified after every string hook and removed before HTML is returned.

Warning mode runs the same reached-tree and settled-output checks, emits one
Python `RuntimeWarning` containing findings deduplicated by rendered instance,
location, and rule, and preserves the standard-runtime HTML. When arbitrary
string hooks make source identity unknowable, Citry keeps separate rendered
instances rather than hiding a potentially distinct conditional source site.
It also remembers raw active tags before dependency insertion, so a later
identical structured tag cannot authenticate authored raw markup; this can
conservatively warn even when a later hook removes that original raw tag.
Static `citry check` and LSP diagnostics remain the structured source-facing
path for normal development.

### 6.2 Fragments

A nonce belongs to the loaded document's policy. A later fragment response
cannot generate a new nonce and expect that value to be accepted inside the
existing document.

In strict mode:

- the base document installs the CSP-compatible Citry runtime and records its
  nonce;
- a fragment carries inert manifests and markup, not today's inline preloader;
- the existing manager creates any needed script or style elements with the
  document nonce; and
- ordinary CSP-compatible Alpine attributes initialize through the existing
  Alpine mutation lifecycle.

A strict fragment therefore requires a Citry-managed base document. A present
manager rejects a runtime-variant or nonce mismatch before dependency adoption.
If the base page did not install the manager, an inert fragment cannot observe
that fact or execute an error without reintroducing a bootstrap script; it
therefore remains inert. Hosts that insert strict fragments must treat the
matching base manager as a precondition. Registration needed by a fragment
must occur before Alpine adopts its markup.

Phase 5 implements the nonce transport used by the strict contract.
The document manager captures the nonce from its own authorizing script tag.
It validates a whole dependency batch before insertion, rejects a descriptor
that carries a different nonce, and supplies the recorded value to dynamically
created `<script>` and `<style>` elements that omit it. A fragment serialized
with `csp_nonce` also stamps the same value onto its structured top-level tags
and descriptors. Off and warning fragment preloaders receive the nonce and
forward it to a dynamically loaded standard manager. Phase 8 removes that
preloader in strict mode and records the required CSP runtime variant in the
inert fragment manifest instead.

### 6.3 Optional script hashes and Subresource Integrity

Citry should also explore an opt-in mode that hashes scripts and adds
Subresource Integrity metadata. CSP hashes and the HTML `integrity` attribute
use similar digest strings but enforce different boundaries:

- a CSP hash source in `script-src`, such as
  `'sha384-<base64-digest>'`, authorizes that exact script content under the
  document's execution policy; and
- an external `<script src="..." integrity="sha384-...">` makes the browser
  verify that the fetched bytes match before executing them, even if the URL's
  server or delivery path returns different content.

For an external script to be authorized by a CSP hash, the script element must
also carry matching `integrity` metadata. Every valid digest in that attribute
must be present in the CSP source list. An inline script instead uses the hash
of its exact emitted text in the CSP header; `integrity` is not its mechanism.
Whitespace, wrapping, and minification therefore affect the digest.

This gives Citry two related opt-in capabilities to explore:

1. **SRI metadata only.** Hash immutable external Citry assets and add
   `integrity`. The host may continue authorizing them through a nonce,
   `'self'`, or another CSP source. This still protects against changed fetched
   bytes.
2. **Hash-based CSP output.** In addition to `integrity`, expose the exact CSP
   hash sources the host must add to `script-src`. This can replace per-request
   script nonces for fully deterministic output and is especially attractive
   for static pages and aggressively cached HTML.

The first public setting remains separate from `security_csp="strict"` because
a strict policy may use nonces, hashes, or both:

```python
citry = Citry(
    security_csp="strict",
    security_script_integrity="citry",  # "off" | "citry"
)
```

`security_script_integrity="citry"` asks Citry to collect SHA-384 digests for
structured scripts. Inline digests are returned as CSP metadata. External
Citry-owned digests are also emitted in matching `integrity` attributes. An
explicit integrity value on a Citry-owned resource is verified against the
owned bytes; a mismatch is an error. An explicit value on a third-party URL is
shape-checked and preserved, but reported as unverified because Citry does not
fetch that resource. With the setting off, existing explicit attributes are
still preserved, but Citry does not calculate or promise security metadata.

The trust and byte-ownership rules are:

- Citry may compute digests for its pinned runtime, generated content-addressed
  assets, component scripts it serves itself, and other resources whose exact
  response bytes it owns.
- An inline digest is calculated after inline wrapping; an external digest is
  calculated from the exact bytes the route serves after build transforms.
  Citry must not assume those two representations are identical or hash the
  component's source string.
- A third-party URL is never fetched by Citry merely to manufacture a digest.
  Its author supplies explicit `integrity` metadata, and Citry preserves and
  validates its shape while the browser verifies the resource.
- Cross-origin SRI resources also need the appropriate CORS request and
  response configuration. Citry must not add `crossorigin` blindly.
- Fragment descriptors carry `integrity` and any explicit `crossorigin` value
  into dynamically created script elements before the request begins.
- Changing any script bytes changes its digest and the CSP header value.
  Release tooling and caches must invalidate both atomically.

Hashing does not make a script trustworthy, remove Alpine's `unsafe-eval`
problem, or validate what the JavaScript does. It proves byte identity and,
when the digest is in CSP, authorizes only that exact content. Alpine's CSP
build is still required for strict expression evaluation.

### 6.4 Structured serialization result

The recommended API is a new result-producing method, not a changed return
type for `serialize()`:

```python
serialized = page.render().serialize_result(
    security_csp="strict",
    security_script_integrity="citry",
    csp_nonce=request.csp_nonce,
)

html = serialized.html
script_hashes = serialized.security.csp_script_hashes
# ("'sha384-abc...'", "'sha384-def...'", ...)
```

The conceptual public types are:

```python
@dataclass(frozen=True, slots=True)
class SerializedRender:
    html: str
    security: SerializedSecurity


@dataclass(frozen=True, slots=True)
class SerializedSecurity:
    scripts: tuple[SerializedScriptSecurity, ...]
    csp_script_hashes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SerializedScriptSecurity:
    location: Literal["inline", "external"]
    url: str | None
    digests: tuple[str, ...]  # unquoted SRI form: "sha384-..."
    provenance: Literal[
        "citry-computed",
        "declared-verified",
        "declared-unverified",
    ]
    origin_class_id: str | None
```

`csp_script_hashes` is the deduplicated, document-order list of quoted hash
sources ready to add to `script-src`. The per-script records retain enough
provenance to explain which tag produced a hash and whether Citry verified its
bytes. The exact module and property names may change during implementation,
but these semantics should not.

`serialize_result()` becomes the canonical implementation. Existing behavior
stays compatible:

```python
def serialize(...) -> str:
    return self.serialize_result(...).html
```

`str(render)`, `bytes(render)`, templates, and host integrations therefore
continue receiving a string. Hash-aware integrations opt into the richer
result. With security features disabled the result carries empty security
metadata and does not do digest work.

The host uses the result after body construction and before sending the
response:

```python
serialized = page.render().serialize_result(security_script_integrity="citry")
hash_sources = " ".join(serialized.security.csp_script_hashes)
policy = f"default-src 'self'; script-src 'self' {hash_sources}"
return HTMLResponse(
    serialized.html,
    headers={"Content-Security-Policy": policy},
)
```

This is intentionally a contribution to the host policy, not a complete CSP
header. Citry cannot know about scripts in a host layout, analytics, images,
connections, frames, or application-specific origins.

The host must not rewrite executable script text after serialization. HTML
pretty-printers, minifiers, template filters, or middleware that change inline
whitespace invalidate its CSP hash. Middleware may compress a response, but it
must not change the decoded external resource bytes covered by SRI.

Rejected alternatives:

- Changing `serialize()` to return a tuple or result object would break its
  string contract and the existing `str(render)` and `bytes(render)` paths.
- A caller-provided list, set, callback, or context variable would make an
  otherwise pure return value depend on a mutable side channel and would be
  easy to miss in framework adapters.
- Parsing the completed HTML only to discover scripts loses dependency
  provenance and cannot obtain the bytes behind external URLs.
- Returning a complete CSP header would incorrectly make Citry the authority
  for resources outside the Citry render.

### 6.5 Where hashes are obtained

Hash collection belongs to one serialization session. It must not be stored in
`CitryContext.extra`, which contains render artifacts and can outlive or be
replayed into a later serialization.

The mutable session is also not exposed on the public `OnSerializeContext`.
Phase 4 gives the structured dependency layer a narrow internal recording
capability instead of letting string-level extension hooks mutate or retain the
collector that becomes trusted host metadata. The public `OnSerializeContext`
does not carry this capability.

The serialization pipeline should become:

1. `serialize_result()` creates a private serialization session and performs
   the existing top-down and bottom-up render passes.
2. The dependencies extension resolves component assets and runs every
   `on_dependencies` hook as it does today.
3. Core runtime and manifest entries are appended. At this point the script
   list is complete.
4. Each structured `Script` is materialized once through `_render()` into an
   immutable internal emitted-tag record. Rendering, hashing, and fragment
   descriptor generation all consume that same record, so a wrapper or custom
   `Script` subclass cannot produce two different representations. The session
   records its final attributes and content, its component origin, and any
   Citry-owned external response bytes. A private, unpredictable
   per-serialization identifier temporarily marks the resulting tag.
5. The existing string-threading `on_serialize` hooks finish.
6. Core removes any unfilled framework placeholders, then a non-hookable
   finalizer reconciles the private identifiers with the final HTML, verifies
   that a later string hook did not alter or duplicate a tag after nonce and
   integrity attributes were applied, removes the private identifiers, and
   performs the strict raw-markup checks.
7. The session freezes into `SerializedSecurity`, and `SerializedRender` is
   returned.

A hook that needs to add, remove, or edit an executable dependency must use
the structured `on_dependencies` list. In strict or integrity mode, changing a
trusted script later as an HTML string is an error with guidance to use that
hook. This preserves extension flexibility without silently blessing text
that appeared after the trusted-code boundary.

Opaque pre-rendered tags and dependency objects that produce a script without
the structured `Script` contract cannot receive computed integrity. Strict or
integrity mode rejects them with guidance to return a `Script` object; off mode
keeps today's trusted raw-output behavior.

The digest inputs are exact:

- For an inline classic script, hash the UTF-8 bytes of the content returned by
  `Script._render()`. That includes Citry's optional IIFE wrapper but excludes
  the `<script>` tags and attributes.
- For an inline module or other CSP-controlled script type, hash its exact
  rendered text without adding the classic-script wrapper.
- Inert Citry JSON manifests are recorded for nonce propagation and validation
  but do not add executable-script hash sources.
- For an external Citry script, hash the exact `RouteResponse.body` bytes that
  the mounted adapter serves, then add the unquoted digest to `integrity` and
  expose its quoted form as a CSP source.

Citry uses a small internal owned-resource record shared by
dependency resolution and route serving. It associates an emitted URL with
the authoritative body bytes and content type. The security code receives
that record directly; it must not infer ownership from a URL that merely looks
like a Citry route. Runtime, component, variables, and locally served
dependency scripts all use this path.

The existing truncated MD5 values in asset URLs are cache fingerprints with
`usedforsecurity=False`. They remain valid for addressing, but they are not
security digests and must never appear in CSP or `integrity`. SHA-384 is
computed independently from the authoritative bytes.

For third-party URLs, Citry never downloads a resource during serialization.
If the author supplies several valid integrity values, all of them are
preserved and exposed as CSP sources because CSP requires every valid digest
on the element to appear in `script-src`. Cross-origin CORS remains the host
and resource server's responsibility. The first implementation accepts
SHA-256, SHA-384, and SHA-512 metadata without option suffixes; unsupported
metadata options fail validation instead of being interpreted loosely.

### 6.6 Documents, fragments, and timing

Hash-based document policies work naturally because Citry already builds the
complete body before the host sends the response header. Per-request inline
data may produce per-request hashes, while static output produces stable
hashes.

A fragment is different. Its serialization result can describe its scripts
and carry SRI metadata, but the fragment response cannot add hash sources to
the CSP header of a document that is already loaded. The first implementation
must therefore use the base document's nonce and existing manager for strict
dynamic fragments, as specified in section 6.2. Fragment hash metadata is
useful for diagnostics and for a future build-time catalog of every permitted
asset, but it is not a real-time authorization mechanism for an already-loaded
page.

`'strict-dynamic'` could later let trust flow from a nonce- or hash-authorized
Citry loader to scripts it creates. That changes the host policy's trust model,
so Citry may document and test it as an integration option but must not insert
it into the host header or silently require it. SRI remains useful in either
case because it verifies the fetched fragment dependency's bytes.

Fragment script metadata has a stable wire and activation order: the inline
preloader, the manager resource it may fetch, top-level framework manifests,
dependency descriptors in manifest order, and the inert outer manifest. The
descriptor records describe elements created after insertion rather than tags
already present in the fragment HTML.

## 7. JavaScript delivery modes

"NoJS" is not a browser security standard. It usually means that a page's
essential content and actions remain usable when JavaScript is unavailable or
intentionally omitted. A page may be NoJS-capable while having no CSP at all;
a strict-CSP page may run a large JavaScript application.

Citry models JavaScript delivery separately:

| Mode | Output behavior | Intended use |
|---|---|---|
| `"allow"` | Current output | Interactive application pages |
| `"warn"` | Current output plus findings for client requirements | Inventory before a static or progressive-enhancement pass |
| `"omit"` | Omit Citry-managed executable JS, Alpine, Events browser code, component JS, JS dependencies, preloaders, and runtime manifests; keep server HTML and CSS | Deliberate static fallback or export |
| `"forbid"` | Raise if the rendered Citry subtree requires or contains executable client behavior | CI-enforced JavaScript-free components and pages |

`"omit"` is the useful lax mode from the proposal. Authored Alpine attributes
may remain in the HTML but are inert. This is sometimes desirable because the
same component can provide meaningful server HTML with optional enhancement.
Citry warns about `x-cloak`, client-only visibility, and controls whose
only action is a browser handler because those fallbacks are likely unusable.

`"omit"` is not a security guarantee and should not silently rewrite arbitrary
raw HTML. If a template contains its own executable `<script>`, native event
attribute, or `javascript:` URL, Citry reports it and leaves the author to
choose `"forbid"` or change the source. The mode promises that Citry's
dependency system emits no JavaScript, not that a host layout or opaque markup
outside Citry contains none.

`"forbid"` is the strict guarantee for the rendered Citry subtree. It rejects:

- any Alpine directive or shorthand that needs the runtime, including
  `x-data`, `x-show`, `x-bind`, `x-on`, `@`, `:`, structural directives, and
  `x-cloak`;
- `Component.js`, `js_file`, JavaScript `Dependencies`, `$component`
  registration, and active `js_data()` scope seeding;
- Events, State bindings, actions, client props, and browser i18n when they are
  active in the rendered tree;
- executable raw `<script>` elements, native event attributes, and
  `javascript:` URLs;
- executable embedded HTML in `iframe srcdoc` and HTML data-document
  contexts; and
- extension output or a fragment strategy that requires a browser manager.

Detection must operate on the settled render and final extension output, not
only on class declarations. A class may declare an Event that the rendered
tree never binds, while a dynamic attribute or extension can introduce a
client requirement only at render time.

CSS remains allowed in every JavaScript mode. Exact structured inert data
scripts are retained, while Citry-owned manifests are omitted when there is no
runtime to consume them. Opaque dependency renderers cannot prove what tag
they create: warn reports them conservatively, omit removes them, and forbid
rejects them with guidance to return an exact `Script` or `Style`. Omit strips
executable attributes from exact structured styles and inert data scripts
instead of discarding their safe CSS or data payload.

The current `deps_strategy="simple"` is not a NoJS guarantee: it omits the
dependency manager but still emits component and dependency script tags.
`deps_strategy="ignore"` drops collected tags but does not inspect raw scripts
or Alpine attributes. The new policy therefore sits above dependency strategy
rather than aliasing either value.

### 7.1 Combining JavaScript, CSP, and dependency modes

JavaScript delivery is applied before CSP runtime selection:

| Effective JavaScript mode | Effect of CSP mode |
|---|---|
| `"allow"` | `off` and `warn` use standard Alpine; `strict` uses the CSP build. |
| `"warn"` | Same runtime choice as `allow`, plus the JavaScript-requirement inventory. |
| `"omit"` | No Citry Alpine or executable dependency runtime is emitted, so Alpine expression compatibility is not checked for inert attributes. Strict CSP still validates raw executable markup and applies nonces to structured styles. |
| `"forbid"` | Client requirements fail before runtime emission. If the subtree passes, no Alpine runtime exists for CSP to select; strict CSP still validates remaining raw executable markup and applies nonces to structured styles. |

The JavaScript policy is a restrictive ceiling over `deps_strategy`:

- with `allow` or `warn`, all existing dependency strategies keep their
  current meaning;
- with `omit`, `document`, `simple`, and `fragment` may emit CSS but strip
  every Citry-managed executable dependency and runtime manifest;
- with `forbid`, a JavaScript dependency or client-active subtree is an error
  under every dependency strategy; and
- `deps_strategy="ignore"` may still suppress CSS and collected tags, but it
  cannot hide a JavaScript requirement from `forbid`.

An omit fragment emits retained styles directly. It has no preloader,
dependency manifest, mount requirement, or existing-manager requirement.
Inventory under `ignore` does not invoke dependency hooks that the strategy
historically skipped; it examines reached bindings, collected declarations,
and final string-hook output instead.

This precedence makes combinations such as `security_csp="strict"` with
`security_javascript="omit"` coherent: the result has no Citry JavaScript,
while the strict final-output checks still protect the boundaries that remain.

## 8. Expression IDs and precompiled functions

Replacing inline Alpine expressions with stable IDs is directionally sound,
but it should be a second phase, not the first strict-CSP implementation.

Citry should not walk the live DOM and reimplement Alpine directive execution.
Alpine already owns directive ordering, effects, cleanup, `x-if`, `x-for`,
teleport, mutation observation, and morph integration. A second walker would
fork those semantics and create difficult fragment races.

Two integration shapes are plausible:

1. Rewrite a complex expression to a small CSP-supported registry call, with
   a precompiled function registered before Alpine initializes the node.
2. Install a Citry evaluator through Alpine's `setEvaluator()` and
   `setRawEvaluator()` hooks, resolving expression IDs to precompiled
   functions.

The second hook is real and used by Alpine's own CSP package, but it is global,
has no getter for wrapping the previous evaluator, and would bind Citry more
tightly to Alpine internals. Either design must preserve Alpine scope, magics,
`$event`, reads and writes that drive reactivity, async behavior, error source
locations, cleanup, and fragment registration order. Browser code must never
fall back to `new Function()`.

The first release should instead use Alpine's CSP interpreter, diagnose its
subset early, and make moving complex logic into component scope methods easy.
Expression IDs become justified only if real Citry applications cannot be
made practical under that model.

## 9. Ownership matrix

| Concern | Host | Citry | Component or extension author |
|---|---|---|---|
| CSP header and directives | Owns | Documents requirements | Does not construct globally |
| Nonce generation and freshness | Owns | Validates shape and propagates | Does not cache or invent |
| Runtime evaluator | Chooses Citry mode | Owns matching bundle | Uses the supported surface |
| Alpine expression compatibility | May select strict mode | Checks and fails early | Refactors unsupported expressions |
| Component and extension JS | Authorizes source policy | Emits with nonce or URL | Keeps code free of blocked dynamic evaluation |
| Third-party resources | Allow-lists or proxies | Preserves declared dependency data | Chooses trustworthy dependencies |
| Report-only rollout | Owns header and reports | Supplies source diagnostics | Resolves findings |
| JavaScript-free usability | Owns complete page | Controls the Citry subtree | Provides native links/forms and meaningful HTML |

## 10. Implementation sequence

1. **Complete (2026-08-12).** Confirm the latest stable Alpine release, then upgrade and pin `alpinejs`,
   `@alpinejs/morph`, and `@alpinejs/csp` to that exact shared version. Run the
   focused private-API, ownership, and morph canaries before building on it.
2. **Complete (2026-08-12).** Add typed `security_csp`, `security_javascript`, and
   `security_script_integrity` settings plus serialization overrides with the
   exact mode semantics above.
3. **Complete (2026-08-12).** Make `serialize_result()` the canonical serializer, add the private
   serialization session and structured security result, and keep
   `serialize()` as the HTML-only compatibility wrapper.
4. **Complete (2026-08-12).** Add authoritative owned-resource bytes, SHA-384
   collection, optional SRI, and final trusted-tag reconciliation for documents
   and fragment descriptors. The owned set includes the dependency manager,
   component and variables scripts, served local JavaScript, and the Events and
   i18n runtimes. Fragment preloaders pin the manager bytes they load.
5. **Complete (2026-08-12).** Add central request-scoped nonce propagation
   after all extension contributions, including structured scripts, inline
   styles, fragment-created elements, browser-manager inheritance, and
   explicit-nonce conflict handling before dependency insertion.
6. **Complete (2026-08-12).** Build the version-pinned CSP compatibility
   checker in two bounded parts:
   1. run the development-only executable spike against the real Alpine 3.16.1
      parser, evaluator, and the few directive-level browser canaries, then
      retain its reconciled corpus as release conformance data;
   2. implement the production portable classifier, add its stable diagnostic
      to the central catalog, carry the selected engine's configured CSP mode
      through LSP discovery, and expose identical findings through `citry
      check` and the existing LSP/IDE pipeline.
7. **Complete (2026-08-12).** Build a CSP runtime variant from the same pinned
   Alpine version and run a focused Citry ownership, morph, Events, and
   fragment canary against both variants. The CSP build aliases the one
   standard Alpine entry import, while both artifacts retain the same Citry
   TypeScript source and build instrumentation. Build-graph and output
   canaries prove that the CSP artifact installs both CSP evaluator paths,
   excludes the standard Alpine entry, and contains no `AsyncFunction` or
   `new Function` path. The browser canary distinguishes both active evaluator
   paths after full startup and runs the CSP artifact under an enforcing policy
   without `unsafe-eval`.
8. **Complete (2026-08-12).** Add reached-tree and settled-output CSP
   validation for dynamic attributes and extension output using the same
   versioned classifier from phase 6. Warning mode emits a deduplicated warning
   without changing standard-runtime output. Strict mode selects the CSP
   runtime, rejects incompatible final output, requires a nonce when structured
   executable scripts or inline styles need one, and replaces the fragment
   preloader with the existing-manager contract. A present manager rejects
   runtime-variant and nonce mismatches before adoption; without a manager the
   inert fragment remains inactive.
9. **Complete (2026-08-12).** Add call-local JavaScript inventory on reached
   component bindings, final structured dependency lists, and settled HTML.
   Warning mode preserves the legacy bytes, omit mode removes Citry-managed
   executable dependencies and browser manifests while retaining HTML and
   CSS, and forbid mode rejects recognized activation paths above every
   dependency strategy. Omit fragments emit CSS directly without a manager;
   opaque dependency renderers are removed or rejected conservatively. Exact
   structured CSS and inert data tags are sanitized without losing their safe
   payload, while embedded HTML execution contexts and manager manifests are
   included in forbid-mode validation.
10. **Complete (revised 2026-08-13).** Check every Citry UI production
    component definition against the pinned Alpine 3.16.1 subset in CI. The
    check discovers every public and private `LibraryComponent` in production
    modules, requires each one to belong to the installed library manifest,
    and runs the same compatibility analysis used by `citry check` over that
    complete registry. Documentation snippets are intentionally outside this
    guarantee because examples may teach syntax for the standard Alpine
    evaluator; they are not a product compatibility ledger.
11. **Complete (2026-08-12).** Add the CSP progression to "Grow without a
    rewrite." The entry starts with warning-mode migration, shows strict mode
    and Citry-owned SRI, and keeps nonce generation plus the complete CSP
    response header with the host.

Phases 2 and 3 establish the stable configuration and result contracts. Phase 4
implements `security_script_integrity="citry"`, and phase 5 implements the
request-scoped `csp_nonce` transport. Phase 6.1 retained the executable Alpine
3.16.1 corpus, and phase 6.2 added the production checker, stable diagnostic,
and configured-mode transport through `citry check` and the LSP. Phase 6 can
report the selected future policy
through check and IDE tooling, but it does not by itself make strict runtime
output safe. Phase 7 provides the matching runtime artifact, phase 8 owns
production selection and final dynamic validation, and phase 9 owns the
orthogonal JavaScript-delivery ceiling. CSP and JavaScript modes are now
enabled. The compatibility defaults keep the old emission path and empty
metadata, and per-call overrides remain serialization-local.

## 11. Acceptance criteria

Strict CSP support is ready when focused conformance proves:

- Citry's core runtime starts under an enforcing policy without
  `unsafe-eval` or `unsafe-inline` in `script-src`;
- unsupported Alpine syntax fails before browser interaction and names the
  component, attribute, and source range;
- the pinned compatibility corpus agrees with the actual CSP evaluator;
- all structured Citry document scripts, styles, extension contributions, and
  dynamically created fragment dependencies receive the correct document
  nonce, while raw template tags are never automatically trusted;
- nonce conflicts fail without partially adopting a fragment;
- opt-in integrity values match the exact fetched bytes, survive fragment
  creation, and are invalidated with their assets;
- a hash-based CSP result exposes every required source without asking Citry
  to construct the host's complete header;
- host integration conformance proves the returned HTML succeeds unchanged
  and a post-serialization script-text rewrite invalidates its hash;
- warning mode leaves runtime behavior unchanged and deduplicates findings;
- omit mode emits no Citry-managed JavaScript while preserving server HTML and
  CSS; and
- forbid mode rejects every recognized client activation path listed in
  section 7.

This is a conformance matrix, not a broad performance program. It should stay
focused on the policy boundaries.

## 12. Primary references

- [Alpine CSP guide](https://alpinejs.dev/advanced/csp)
- [Alpine 3.15.12 standard evaluator](https://github.com/alpinejs/alpine/blob/v3.15.12/packages/alpinejs/src/evaluator.js)
- [Alpine 3.15.12 CSP bootstrap](https://github.com/alpinejs/alpine/blob/v3.15.12/packages/csp/src/index.js)
- [Alpine 3.15.12 CSP evaluator](https://github.com/alpinejs/alpine/blob/v3.15.12/packages/csp/src/evaluator.js)
- [Alpine 3.15.12 CSP parser and interpreter](https://github.com/alpinejs/alpine/blob/v3.15.12/packages/csp/src/parser.js)
- [Alpine 3.16.1 release](https://github.com/alpinejs/alpine/releases/tag/v3.16.1)
- [MDN CSP guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)
- [MDN `script-src`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src)
- [MDN `style-src-attr`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/style-src-attr)
- [MDN Subresource Integrity](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity)
- [CSP Level 3: allowing external JavaScript via hashes](https://www.w3.org/TR/CSP/#external-hash)
- [Django CSP and nonce guide](https://docs.djangoproject.com/en/dev/howto/csp/)
- [Alpine fragment/CSP discussion #4478](https://github.com/alpinejs/alpine/discussions/4478)
