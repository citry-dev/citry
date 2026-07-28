# Judge 1: practicality and citry fit

Lens: does each design build on citry's real seams (Extension.urls, contrib
mounts, the JS runtime mount contract, on_serialize/on_dependencies, the
Kwargs contract), and can it actually ship and grow? All load-bearing claims
below were re-verified against source in this session, not taken from the
designs' own citations.

Ground truth established independently before judging:

- `RouteResponse` is content/content_type/status only; handlers are sync;
  the ASGI adapter calls `handler(scope, **params)` and never passes
  `receive`, so POST bodies are unreachable today
  (`packages/py/citry/citry/util/routing.py:42-53`, `contrib/asgi.py:94`).
  All three designs got this right and require the same v0 substrate.
- Route matching is definition order, first wins
  (`util/routing.py:128-141`, docstring says "define more specific patterns
  first").
- Bare `c-*` attributes are the dynamic Python-expression channel, and the
  `c-` prefix is stripped when the resolved attribute is emitted
  (`nodes/__init__.py:432-434` ExprHtmlAttr; `nodes/__init__.py:631,820,1190`
  `key.removeprefix("c-")`). So `c-arg:id="item.id"` really does render
  `arg:id="3"` (design A's mechanism, verified), and `c-on:click="add_item"`
  (design B's v1.1 spelling) would evaluate `add_item` as a Python
  expression, not pass through. `@click` parses as a plain attribute
  (`grammar.pest:228-255`); attribute values are atomic strings.
- `template_data(self, kwargs, slots=None)` is the real signature and
  returning None means no template variables (`component.py:494-513`).
- `get_component_by_class_id` reads `_classes_by_id`, populated only by
  `Citry.register` (`citry.py:206-210, 333-345`); autodiscovery
  auto-registers (`autodiscovery.py:92`). So registration is required for
  URL dispatch under all three designs equally (class_id for A/B, registry
  name for C); no design has an addressing advantage here.
- Root markers are attribute-name strings stamped on root elements
  (`serialize.py:104`, `citry_context.py:96-119`); today they are boolean
  markers (`data-cid-<id>`, `data-ccss-<hash>`). A valued `data-cev="..."`
  marker (design C) is a core serialization change, whereas an
  extension-owned inert manifest script tag (designs A and B) mirrors the
  dependencies pattern with zero core change.
- The `$onComponent` payload is exactly `{id, els, data}` built at
  `citry.js:150`; the runtime has no transport, no swap, no teardown, and
  fragment script execution order is not guaranteed (recon-js-runtime gaps
  1-3, 6). One callback invocation per manifest call entry.

Convergence note: all three designs independently landed on signed JSON
kwargs with full-length HMAC (no pickle, no rich revival), placement-as-
allowlist handler exposure, a fixed parametrized route (Django
snapshot-safe), self-addressed op/patch lists mixing HTML and JSON,
one-socket-per-page WS deferred with stateless dispatch making reconnect
trivial, `@poll` as the v1 push stopgap, vendored idiomorph, no
model-by-pk coercion, and OpenAPI from signature-derived argument models.
That convergence is strong evidence those pieces are simply correct; the
judging is about everything else.

---

## Design A (dx-first)

### What holds up under attack

- **Best verified reuse of real machinery.** Patches carry a complete
  `serialize(deps_strategy="fragment")` output as the `html` string, so
  asset loading and `$onComponent` re-fire ride the existing
  MutationObserver machinery unchanged. That is the single smartest
  citry-fit move in any design: the tested fragment path becomes the update
  vehicle. The props token riding inside the fragment's events manifest
  (not a separate response field) keeps fragments self-contained.
- **`c-arg:*` for dynamic per-item args is real.** Verified against the
  prefix-stripping behavior; it converts the "plain attribute values are
  static" constraint into a feature instead of fighting the grammar. Neither
  B nor C has an answer this clean for loop-item arguments (C's `$value`
  literals cover form fields, not loop ids).
- **A's examples run against the real API.** Alone among the three, every
  pitch example uses `template_data(self, kwargs, slots)` correctly. For a
  design whose thesis is DX, getting the copy-paste surface right matters,
  and it is evidence of actual ground-truth contact.
- **The slot-fill problem is confronted.** An interactive component that
  received slot fills errors loudly at first render with a named fix. B and
  C do not mention slots at all; their `Render()`/`e.render()` of a
  slot-filled instance silently re-renders with empty/default slots, which
  is exactly the livecomponents silent-wrong-render failure both cite as a
  lesson. This is a real practicality gap in B and C and a point to A.
- **`epoch` per-instance ordering.** The only design that handles
  out-of-order responses (two rapid `@bind.live` calls resolving in reverse)
  at the protocol level. This bug class shipped in unicorn and Livewire;
  A learned from it, B and C did not carry it.
- **id pinning for stable morph identity** uses the existing explicit `id=`
  argument (`component.py:447-456`), verified supported.
- **Honest DX-over-purity ledger (section 12) and a real falsifier list.**
  The morph spike gate (manifest re-fire, teardown, focus survival) is the
  correct first risk to retire.

### Where it bleeds

- **Django CSRF default is not safe-by-default.** Default `csrf="header"`
  plus Django's own CsrfViewMiddleware means a bare POST to a citry route
  under Django is rejected (or the view must be exempted) unless the user
  opts into `csrf="django"`. A acknowledges the interaction "depends on
  setup" but ships the wrong default for the most important migration host.
  B and C both autowire the host token by default (cookie -> header) and C
  makes "passes review without csrf_exempt" an explicit falsifier. A should
  adopt that default.
- **Protocol rigor is the thin spot.** No schema package, no golden
  fixtures, no conformance suite, and no capability negotiation. "Additive
  fields are minor and never gated" is a stale-cached-client hazard the
  moment a new patch `mode` ships. The envelope is also not self-describing
  over HTTP (component/event live only in the URL), so the WS frame adds
  fields and the batch envelope differs from the single-call envelope: three
  request shapes for one protocol.
- **The `@bind` writable-updates channel is the largest attack/complexity
  surface of any design**, and its allowlist rests on scanning the
  component's own template for `@bind` targets. The scan is server-side and
  cannot be widened by the client (good), but scan-at-"class creation"
  glosses over lazy template loading (`on_template_loaded` fires at first
  load, and file-based templates load later than class definition), and the
  scan's correctness across `c-if` branches and includes is unexamined.
  `model = (...)` explicit override exists, which contains the risk.
- **Teardown + payload extension modify the dependencies-owned runtime.**
  Adding cleanup-function support changes shared runtime behavior; it is
  coordinated, not forked, but it is core-adjacent work B avoids with its
  decorator seam. A also asserts its runtime is "self-contained and
  order-independent" without a mechanism; B actually mechanizes ordering
  with the inline bootstrap stub (recon gap 6 is real and verified).
- **v1 client scope is the largest**: morph, the whole `@` vocabulary,
  `@bind` batching plus re-apply-after-patch, `@error`, `@on:`, `@loading`,
  epoch handling, teardown. The staged exit criteria are good, but this is
  the design most likely to slip on the client half.
- Minor: `@on:cart-updated.window="refresh"` names a handler `refresh` that
  is presumably the built-in `$refresh`; the `fx` accumulator plus
  return-value algebra gives two ways to say several things (dispatch via
  return vs via fx) where B/C have one.

## Design B (contract-first)

### What holds up under attack

- **The cross-language machinery is real, not aspirational.** JSON Schema
  2020-12 for both envelopes, golden fixtures with declared-volatile JSON
  paths (the compiler-tests discipline applied to the protocol), a
  conformance rule that protocol changes land as fixture changes, and a
  host-opaque state token explicitly to avoid cross-language
  canonical-JSON signing. This is the only design a JS/PHP/Go binding could
  be built against without reverse-engineering the Python.
- **`caps` negotiation** is the only stale-client story that survives a
  deploy with a cached runtime, and it is what lets v1 ship `replace` and
  add `morph` additively. Genuinely good protocol engineering.
- **The dispatcher boundary is proven by the postMessage transport**: a
  complete client transport plus parent-page bridge with zero server
  change, feeding the Storybook/docs-preview need the roadmap actually
  lists. The GraphQL sketch is honest ten-line evidence, and falsifier 3
  ("any dispatcher signature change for WS/postMessage proves the
  abstraction fake") is the right test.
- **Route hygiene**: the `c/{class_id}/{event}` prefix deliberately
  disambiguates against the literal `call` and `runtime.js` routes under
  first-match routing. C's table gets this wrong (below); B is the only
  design that visibly thought about it.
- **The ordering fix is mechanized.** `decorateContext` plus a 15-line
  inline bootstrap queue in the manifest solves the verified
  script-execution-order gap; A asserts, B engineers.
- **Safest defaults**: CSRF autowired to the host token (passes Django
  review without exemption), guards inherit engine -> component -> handler
  (opt-out, not opt-in), cheapest-rejection-first dispatch, envelope and
  calls caps, `RouteResponse` escape confined to the per-event HTTP route.
- **PayloadCodec / ResultEncoder registries** are the only first-class
  answer to the brief's "pluggable formats" requirement; the urlencoded
  codec plus `Accept: text/html` compatibility mode yields a no-JS form
  story and htmx interop for free, which is itself a migration asset for
  livecomponents users who keep their `hx-post` attributes pointed at event
  URLs during transition.

### Where it bleeds

- **The v1.1 template-binding spelling is wrong, and knowably so.**
  `c-on:click="add_item"` collides with the verified `c-*`
  dynamic-expression channel; it would evaluate `add_item` as Python. B
  left this as "open question (a)" with a `data-on:*` fallback, but A and C
  both settled it against source in the same repo during the same exercise.
  For a contract-first design, leaving its own author-facing syntax
  unresolved when the answer is one grep away is a process failure, though
  contained (client-only sugar, fallback reserved).
- **Python-side ergonomics regress below citry's own bar.**
  `ctx.kwargs["items"]` is a plain dict where citry already builds a typed
  `Kwargs` dataclass; every handler takes an explicit `ctx` parameter;
  state changes are `Render(**overrides)` ceremony. B's flagship example is
  also broken against the real API: `TodoList` defines no `template_data`,
  so `{{ title }}` and `items` would render as nothing (base
  `template_data` returns None = no variables, verified). The contract got
  the attention; the binding got the leftovers.
- **v1 product risk is admitted but real**: no morph, no declarative
  bindings means every interaction needs hand-written component JS and
  swaps lose focus. Falsifier 2 concedes that if the form example fails,
  morph moves into v1, which is the likely outcome for the Livewire/unicorn
  audience; plan for it.
- **Slot fills unaddressed** (same silent-wrong-render exposure as C).
- **EventContext.request is the raw host object** while the route layer
  gains a neutral `RouteRequest`; handlers wanting neutral query/form access
  have no surface (A and C provide a neutral request with `.native`). The
  escape hatch exists; the neutral middle layer for handlers does not.
- Minor: state token on GET handlers unspecified (query length limits);
  GET csrf-exempt "read-only by contract" is unenforced.

## Design C (supersede-first)

### What holds up under attack

- **The parity matrix is the best migration artifact produced by any
  design.** It functions as an acceptance checklist per competitor, the
  D1-D9 dropped-features list argues each drop instead of hiding it, and
  the ~40-line `ViewEvents` verb shim is a genuinely valuable drop-in
  bridge nobody else offers (A hand-waves View migration into rewriting).
- **Compile-time binding validation is the strongest single DX idea across
  all three designs**: a typo'd handler name or bad arg literal failing at
  class-definition/template-load time with the template location is a
  differentiator no surveyed framework has, and it doubles as security
  (bindings must name declared handlers).
- **Seam citations are the most explicit and mostly correct**: the
  `on_js_loaded` rewrite point runs before the dependencies cache
  (documented seam 2 in the recon), `on_template_loaded` for the binding
  rewrite, `on_dependencies` for runtime injection, raw-class capture, the
  Alpine coexistence recognition rule (binding only if the value parses AND
  names a declared handler) is a thoughtful answer A lacks (A offers a
  configurable prefix instead).
- **Honest build-time verification points**: C flags the valued-root-marker
  question and the node-transform question itself rather than asserting.
- **OpenAPI CLI in v1.0** with docstrings as operation descriptions is the
  most complete delivery of the Component.Ninja promise, aligned with the
  house docstring rule.

### Where it bleeds

- **The route table as specified is buggy.** With first-match-in-definition-
  order routing (verified), the declared order (`{component}/{event}`, then
  `{component}`, then `runtime.js`, then `openapi.json`) makes
  `runtime.js` and `openapi.json` unreachable: a GET to
  `ext/events/runtime.js` matches `{component}` = "runtime.js" first (the
  View-shim single-segment route swallows every one-segment path). Trivial
  to fix (literals first), but a spec that ships its own 404 is exactly the
  kind of detail this lens exists to catch.
- **Body-authoritative routing subverts the per-event URL's value.** C
  states the server routes each call by the call's own `component`/`event`
  fields and a batched request posts to the first call's URL. Then host
  middleware, per-action rate limits, and access logs attached to
  `ext/events/{component}/{event}` can be bypassed or misled by a body
  naming a different component/event. A treats the URL as authoritative;
  B pre-binds class_id/event from the URL into the codec. C's choice
  quietly breaks the very middleware/OpenAPI story per-event URLs exist for.
- **The props envelope is structured wire data, not an opaque token.** The
  client registry parses `{v, c, p, t, sig}` (it reads the class from it),
  so the envelope's internals, including canonical-JSON HMAC input, become
  cross-language contract for every future server binding. B names this
  exact trap and dodges it by declaring the token host-opaque and shipping
  (instance, class, token) as separate manifest fields. C also puts the
  envelope in a GET query parameter, which meets URL length limits at
  ~2KB, and its "pasteable URL" claim conflicts with handlers whose
  re-render needs props (`e.render(show=show)` with `props=None` cannot
  reconstruct `project_id`).
- **Valued root markers are a core serialization change** where the
  extension-owned manifest tag pattern (A, B) needs none; C picked the one
  state-delivery path requiring core surgery and flags it only as a
  verification point under a v1 load-bearing feature.
- **Missing ASGI sync-handler offload** from the substrate list: C's
  handlers run synchronously inside the event loop under FastAPI, so a
  blocking ORM call stalls every request. Its own 2ms-dispatch falsifier
  measures the wrong thing. A (A3) and B (item 2) both include the offload.
- **Examples do not run against the real API**: `def template_data(self):`
  with `self.kwargs` does not match `template_data(self, kwargs, slots)`.
  Same class of sloppiness as B's example, and worth calling out in a
  design whose thesis is "users of prior art will read this and migrate".
- **v1 scope is the largest of the three** (bindings + compile-time checks
  + textual rewrite with known false-match class in `<c-raw>` + morph +
  multipart + OpenAPI + shim + two $-rewrites + registry). The textual
  template rewrite shipping in v1 with a known sharp edge, plus two
  unresolved verification points under it, makes the v1 date the least
  credible.
- **`$sendEvent` single-instance rule** will be a recurring support cost:
  list-rendered components are the norm, not the edge; C's own falsifier 5
  half-expects this. The instance-scoped `events` payload is the real API;
  the class-scoped magic is sugar that sours under `c-for`.

---

## Cross-design verdicts on the contested questions

1. **Binding prefix**: `@` (A, C) is correct; `c-*` (B v1.1) is verified
   unavailable. C's recognition rule (parse + declared-handler match) beats
   A's configurable prefix for Alpine coexistence.
2. **State access in handlers**: A's mutable typed kwargs wins the target
   audience; C's typed read-only `e.props` + `e.render(**overrides)` is the
   defensible middle; B's dict access is strictly worst.
3. **Token opacity**: B is right; A is fine in practice (single string) but
   should declare opacity; C's structured envelope is a cross-language
   liability.
4. **Morph in v1**: A and C are right for the audience; B's own falsifier
   effectively concedes it.
5. **URL vs body addressing**: A and B right (URL authoritative on the
   per-event route; batch is its own explicit endpoint); C wrong.
6. **CSRF default**: B and C right (autowire host token); A wrong default.
7. **Ordering/bootstrap**: B's inline bootstrap is the only mechanized
   answer to a verified gap; graft it regardless of base.
8. **Protocol evolution**: B's caps + fixtures is the only design that
   survives a stale cached client and a second language binding.
9. **Slot-filled components**: only A has an answer; graft its loud error
   everywhere.
10. **Requirements fidelity**: B's codec/encoder registries are the only
    real "pluggable formats"; C's `$sendEvent`/`$onEvent` hews closest to
    the requested magic names (requirement allows redesign, and the payload
    members are the safer primary surface).

## Scores (1-10)

| | dx | citryFit | crossLanguage | migration | security | deliverability |
|---|---|---|---|---|---|---|
| A (dx-first) | 9 | 9 | 6 | 9 | 8 | 7 |
| B (contract-first) | 6 | 8 | 10 | 7 | 9 | 8 |
| C (supersede-first) | 8 | 7 | 6 | 9 | 8 | 6 |

## Recommendation

Start from A's user-facing surface, client model, and staged delivery;
mount it on B's contract spine (protocol package, fixtures, caps,
dispatcher/TransportContext boundary, codec/encoder registries, opaque
token, CSRF default, bootstrap ordering fix); graft C's migration artifacts
(parity matrix as acceptance checklist, ViewEvents shim, compile-time
binding validation, OpenAPI CLI in v1.0). Reject: B's `c-on:*` spelling and
dict kwargs; C's valued root markers, body-authoritative routing, structured
props envelope, and route order as written; A's `csrf="header"`-only Django
default and ungated protocol additivity.
