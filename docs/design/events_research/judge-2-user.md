# Judge 2 (end-user lens): Component.Events design comparison

Lens: a Python/web engineer choosing between citry Events, django-unicorn,
Tetra, livecomponents, htmx, or hand-written fetch handlers. The question is
not which document is best engineered; it is which shipped v1 that engineer
adopts, and which one they abandon after the first form.

Inputs: all three full designs read end to end; recon reports read
(ecosystem, js-runtime, citry-extensions in full; unicorn, tetra,
livecomponents, old-djc skimmed at section level). Load-bearing claims were
re-verified against source where the designs disagree; see "Source
verification" at the end.

Scores (1-10):

| Design | dx | citryFit | crossLanguage | migration | security | deliverability |
|---|---|---|---|---|---|---|
| A (dx-first) | 9 | 8 | 6 | 9 | 8 | 7 |
| B (contract-first) | 5 | 9 | 10 | 7 | 9.5 | 9 |
| C (supersede-first) | 8 | 8.5 | 7.5 | 9.5 | 9 | 7.5 |

---

## 1. The adversarial walkthroughs

I built the four briefed scenarios in each proposed API, on paper, counting
every line, import, concept, and trap the user meets. "v1" means what each
design actually ships first, not its roadmap.

### 1a. Counter

**A** (3 concepts: Events class, mutate kwargs, @click):

```python
class Counter(Component):
    class Kwargs:
        count: int = 0

    class Events:
        def increment(self):
            self.kwargs.count += 1
```

Template: `<button @click="increment">`. No imports, no return, no JS.
`self.kwargs.count += 1` is grounded: `Kwargs` is rebuilt as a non-frozen
`dataclass(slots=True)` (verified, `component.py:154-162`), and the implicit
None-means-re-render matches every tool the target user comes from.
Friction: zero beyond the two-line engine setup.

**B** (6 concepts: Events class, ctx, dict kwargs, Render import, explicit
return, hand-written JS):

```python
class Events:
    def increment(self, ctx: EventContext) -> Render:
        return Render(count=ctx.kwargs["count"] + 1)

js = """
$onComponent(({ els, send }) => {
  els[0].querySelector("button").onclick = () => send("increment");
});
"""
```

Three frictions, each real: (1) v1 has no declarative bindings at all, so
the entry-level demo requires component JS, which is precisely the work
unicorn/Tetra users adopted those tools to stop writing; (2)
`ctx.kwargs["count"]` is a stringly dict in a codebase whose whole identity
is typed Kwargs; a typo is a runtime KeyError, no IDE completion; (3)
forgetting `return Render()` yields a silent no-op success (B's explicit
choice), which for migrants from four re-render-by-default tools is a trap,
not a discipline.

**C** (4 concepts: Events class, `e` context, e.render, @click):

```python
class Events:
    def increment(self, e: Event, by: int = 1):
        return e.render(count=e.props.count + by)
```

Template: `<button @click="increment(by=1)">`. No imports (helpers ride on
`e`), typed attribute access (`e.props` is the rebuilt Kwargs dataclass),
declarative binding checked at class definition. One notch more ceremony
than A (the explicit `e.render(...)` and the `e: Event` parameter), still
clearly ahead of everything in the prior-art column.

Ranking: A > C >> B.

### 1b. Form with server-side validation errors

**A**: `@bind="name"`, `@bind="email"` batch field values with the submit;
handler raises `EventError(fields={"email": "..."})`; `@error="email"`
displays the message; on failure nothing re-renders so the user's input
stays put; `@loading.attr="disabled"` on the button. Zero JS, and the
failure path (keep input, show message) is the *default*. This is better
than unicorn's story (which needs `form_class` or manual plumbing) and is
the strongest single scenario in any of the three documents.

**B v1**: no bindings, no error-display channel. The user writes JS to
collect the fields, `await send("submit", {...})`, catch the rejection,
and paint `error.fields` into the DOM by hand. That is the "just write
fetch handlers" baseline with a nicer envelope. B's real counterweight is
its v1 no-JS mode: a plain `<form method="post" action="{{ url }}">`
against the per-event URL works via the urlencoded codec with a full-page
response or 303. Genuine progressive enhancement, but full-page-reload UX
is not what a unicorn refugee is shopping for. B's own falsifiability #2
concedes the form flow may force morph into v1.

**C**: args arrive via selector specials:
`@submit.prevent="save(name=$value('input[name=name]'), email=$value('input[name=email]'))"`.
Workable for two fields, ugly at five (CSS selectors inside one attribute
string, unvalidatable by the compile-time checker). There is no two-way
bind and, notably, no `@error` display attribute; field errors ride the
error op and `citry:events:error`, so displaying them is user JS until the
v2 `FormEvents` helper. Dropping model binding is also absent from C's
otherwise honest D1-D9 dropped-features list; the omission matters because
`unicorn:model` is unicorn's single most-used surface.

Ranking: A >> C > B.

### 1c. Live search with debounce

**A**: `<input @bind.live.debounce.300ms="query">` plus `template_data`
computing results. Zero handlers, zero JS, morph protects the focused
input. Ten out of ten; this is the pitch demo that converts people.

**B v1**: hand-rolled debounce in component JS, then `send`. Worse: the
handler re-renders the whole component and the v1 swap is `replace`, which
clobbers the focused input on every response. The escape is restructuring
into a css-targeted `Render` of a separate results region. So the naive
build of the most common LiveWire-class demo is broken-feeling in B v1 by
design, acknowledged in its own falsifiability list.

**C**: `<input @input.debounce-300="set_query(query=$value)">` plus a
one-line handler returning `e.render(query=query)`. One small handler more
than A (C has no bind built-in, so a set-field handler is user code), morph
in v1 preserves focus. Very close to A.

Ranking: A > C >> B.

### 1d. Chat page with server push

All three defer push. What the user can ship meanwhile, and when push
lands:

- **A**: v1 `@poll.5s` declarative, tab-aware; push in v2 (WS or SSE, one
  socket per page, signed channels via `Events.channels()`, pushed payload
  = the same response envelope).
- **B**: v1 has no poll attribute; "poll a GET handler" means the user
  writes their own setInterval loop in JS. WS is v2 and push is **v3**,
  the furthest of the three.
- **C**: v1 `@poll-5000="refresh()"` declarative; push in v2 with the most
  concrete design of the three (declared topic templates
  `Events.topics = ("project:{project_id}",)` formatted from props and
  signed at render; `push(topic, *ops)` callable from a task queue).

Ranking: C >= A >> B.

### Scenario summary

A wins three of four scenarios outright and ties the fourth. C is a close
second everywhere and ahead on push design. B loses every scenario in v1,
on purpose; its bet is that plumbing correctness now buys ergonomics
later. From the adoption lens that ordering is backwards: users evaluate
the counter and the form on day one, and B's v1 loses those evaluations to
django-unicorn, a tool it is supposed to supersede.

---

## 2. Per-design critique

### Design A (dx-first): the product, with the weakest contract

Strengths beyond the scenarios:

- Only design that confronts the two silent-wrong-render holes of the
  stateless model: slot-filled interactive components fail loudly at first
  render (6.5), and request-scoped `template_globals` get a per-call
  `Events.globals()` recompute plus a dev warning (6.4). B and C do not
  mention either (verified by grep); both would reproduce livecomponents'
  known wrong-render bug the first time a user puts a button in a Card
  that takes slot fills. For a real app this is not an edge case.
- The honest DX-over-purity ledger (section 12) and the morph-spike gate
  (falsifiability #1) show the risk is understood, not hidden.
- `c-arg:*` for dynamic per-item args is verified to work today with zero
  parser changes (`c-` prefix strips on render, `nodes/__init__.py:631`).

Weaknesses:

- **Cross-language is the afterthought.** No schema package, no fixtures,
  no conformance story; the envelope carries positional `args` (a Python
  calling-convention leak the brief explicitly warned about). A JS or Go
  server binding would be reverse-engineered from the Python one.
- **Biggest v1 client runtime of the three**: morph + two-way bind with
  value re-application + focus protection + error channel + poll + loading
  + delegated modifiers + teardown in `citry.js`, all in the first
  release. unicorn's issue tracker is a catalog of exactly these
  morph/bind edge cases accumulated over years. Deliverability 7 reflects
  slip risk, not feasibility.
- CSRF default is header+Origin, with Django token integration opt-in
  (`csrf="django"`). For the Django-heavy migration audience the default
  posture is wrong (B and C both default to host-token integration), and A
  itself admits a bare POST under Django is "rejected or unprotected
  depending on setup".
- Alpine coexistence is prefix-configuration only; C's recognition rule
  (a binding must parse AND name a declared handler) is strictly better
  and A should adopt it.

### Design B (contract-first): the best plumbing, the worst v1 product

Strengths:

- The protocol package (`packages/protocol/events/v1`: JSON Schemas,
  golden fixtures, declared-volatile paths) is the single most valuable
  artifact in any of the three documents for a multi-language project. It
  mirrors the repo's observe-then-lock culture, and its postMessage
  transport actually proves the transport seam (envelope crosses two
  transports unchanged, enabling sandboxed Storybook/docs previews with
  zero server work). No other design proves its abstraction.
- Security is the most rigorous: schema-cap on calls, additionalProperties
  false, verify-state-before-args ordering, full-length HMAC with key
  rotation (only B has rotation), guards that inherit engine to component
  to handler, host CSRF by default, tracebacks never on the wire.
- The htmx/no-JS compatibility mode (Accept: text/html + urlencoded codec
  on per-event URLs) is a real adoption wedge nobody else ships in v1:
  htmx users can consume Events endpoints without adopting the citry
  client.
- The `decorateContext` seam plus inline bootstrap stub is the most
  carefully engineered client-integration ordering story.

Weaknesses:

- Everything in section 1 above: v1 without bindings, bind, morph, poll,
  or an error channel does not convert a single unicorn/Tetra user, and
  the migration "afters" are visibly more ceremony than the "befores".
- `ctx.kwargs: dict[str, Any]` discards citry's typed-Kwargs identity in
  the one place users touch state on every call. Ironic for the
  contract-first design; C shows the typed rebuild costs nothing.
- Its deferred declarative-binding spelling `c-on:click` contradicts
  verified source: bare `c-*` attributes are the dynamic Python-expression
  channel (`ExprHtmlAttr`, `nodes/__init__.py:430-441`), so
  `c-on:input="search"` would evaluate `search` as a template expression
  at render time. B flagged the pre-check and reserved `data-on:*`, so it
  is not fatal, but the design as printed (including its unicorn migration
  example) is wrong, and `data-on:*` is the ugliest spelling on the table.
- `None` returning an empty ack is the worst beginner trap of the three:
  a migrant writes a mutating handler with no return and the UI silently
  does nothing.

### Design C (supersede-first): the migration document, nearly the product

Strengths:

- The parity matrix plus D1-D9 dropped-features-with-acceptance list IS
  the migration sales document; the ViewEvents verb shim (~40 lines) gives
  Component.View users a drop-in bridge nobody else offers; the
  execution-results-to-ops table does the same for livecomponents.
- Compile-time binding validation (typo in `@click="filte(...)"` fails at
  class definition with the template location) is the one capability no
  prior art has, and C is the only design shipping it in v1.
- Typed `e.props` (Kwargs rebuilt), keyword-only args matching the Kwargs
  culture, helpers on the context so handlers need no imports.
- The Alpine recognition rule (grammar-match AND declared-handler) is the
  best answer to the shared `@` prefix.
- The most concrete push design (signed topic templates from props).

Weaknesses:

- **The structured props envelope is a wire bug waiting to happen.** C
  sends `props` as a parsed JSON object (`{v, c, p, t, sig}`) inside the
  call, with `sig` over canonical JSON. The client JSON-parses and
  re-serializes the envelope, and JS normalizes values (1.0 becomes 1,
  unicode escapes differ), so server-side re-canonicalization can fail the
  signature on untampered state, surfacing as spurious 409 stale errors.
  A and B both echo an opaque base64 string verbatim, which eliminates the
  class; B additionally argues opacity keeps the token format out of the
  cross-language contract. C should adopt the opaque token unchanged.
- No two-way bind and no declarative error display (section 1b); the
  `$value('selector')` idiom does not scale to real forms.
- URLs address components by registered name, so events silently require
  `citry.register` for every interactive component; A and B use class_id,
  which always exists. Hidden preconditions are exactly the migration
  friction this design is supposed to remove.
- Two flagged delivery unknowns sit under its headline features: the
  textual `@` rewrite at template load (same false-match class as the
  shipped `$onComponent` rewrite, admittedly precedented) and
  class-definition-time template validation, which quietly forces eager
  template loading for file-based templates (not called out in its
  build-time checks).
- `$sendEvent`'s single-instance rule is a designed-in support question
  (its own falsifiability #5); A and B's rejection of new source rewrites
  matches the recon's documented sharp edges.

---

## 3. Recommended graft

Start from **A's user surface and state model**; it is the only v1 that
wins the four scenarios against the tools users would otherwise pick, and
the only design that closes the slot-fill and template-globals correctness
holes. Then graft:

From B (the contract layer, wholesale):

1. `packages/protocol/events/v1` with JSON Schemas, golden fixtures, and
   declared-volatile paths, merged before server code; make A's envelope
   carry `calls[]` as an array from day one (B and C both fixed batching
   in the schema now; A's separate later batch endpoint is the weaker
   shape).
2. Caps negotiation for swap/op evolution, opaque host-minted state token
   framing (exempt from conformance), and secret rotation (list-valued
   secret).
3. The dispatcher + TransportContext split with PayloadCodec /
   ResultEncoder registries, the urlencoded codec, and the
   Accept: text/html compatibility mode in v1 (htmx interop plus no-JS
   forms is a real wedge A deferred to v1.x for no strong reason).
4. `decorateContext` plus the inline bootstrap stub for airtight client
   ordering, and the postMessage transport as the seam-proving example.
5. Host-token CSRF as the default under Django (keep A's header+Origin as
   the universal floor).

From C (the migration and correctness details):

6. Compile-time binding validation and the recognition rule (parse-match
   AND declared handler) layered on A's `@` vocabulary; fall back to
   first-load validation where templates load lazily.
7. Keyword-only args on the wire (drop A's positional list; `rate(5)`
   sugar can stay client-side but encode named).
8. The ViewEvents verb shim, the parity matrix, and the D1-D9
   dropped-features list as the skeleton of the migration docs.
9. Typed context access stays (A already rebuilds Kwargs; never regress to
   B's dict).
10. C's push design (signed topic templates formatted from props) as the
    committed v2 shape.

Keep from A unchanged: None-re-renders and return-and-render semantics,
the full `@bind`/`@error`/`@loading`/`@poll` v1 vocabulary, mutable typed
kwargs, loud slot/globals failures, and the morph-spike gate as the first
milestone. If the spike or the schedule falsifies the v1 client scope,
shed morph to v1.1 behind B's caps mechanism rather than shedding the
binding vocabulary; the vocabulary is what converts users, morph quality
can follow one minor version behind.

---

## 4. Adjudicated disagreements

1. **Binding prefix and timing.** A/C ship `@` bindings in v1; B defers to
   v1.1 spelled `c-on:*`. A/C are right, and B's spelling is broken as
   printed: verified in source that bare `c-*` attributes are the
   evaluated-expression channel and the `c-` prefix strips on render.
   B flagged the pre-check, but its printed examples would not work.
2. **`None` return.** A/C: re-render (matches unicorn, Tetra, Livewire,
   livecomponents). B: empty ack. A/C right for this audience; B's choice
   converts the most common handler shape into a silent no-op.
3. **Value return.** A: resolve promise AND re-render (Livewire/Tetra
   behavior). B/C: resolve only. A is right for migrants; B/C reintroduce
   the documented "my update stopped when I added a return" bug class.
4. **State token format.** A/B: opaque string echoed verbatim. C:
   structured JSON with in-protocol signature. A/B right; C's shape
   invites JSON re-serialization signature failures and drags the token
   format into the cross-language contract.
5. **Handler state surface.** A: mutable typed kwargs (grounded in the
   non-frozen dataclass). C: typed functional `e.props` + `e.render`.
   B: plain dict. A best for DX, C acceptable, B's dict should not
   survive the merge.
6. **Event URL identity.** A/B: class_id (always exists). C: registered
   name (adds a hidden registration requirement). A/B right.
7. **CSRF default.** B/C: host token by default under Django. A: custom
   header default. B/C right for the audience.
8. **`$sendEvent`/`$onEvent` as source rewrites.** C ships them with a
   single-instance rule; A/B reject rewrites for context members. A/B
   right: the recon documents the rewrite's substring sharp edges, and
   C's own falsifiability #5 predicts the support burden.
9. **Slot fills and template globals on re-render.** Only A addresses
   them. A is right that both must fail loudly; silence here is the
   livecomponents wrong-render bug reproduced in v1.

---

## 5. Source verification notes

Claims re-checked against the repo during judging:

- `Kwargs` nested classes become non-frozen `dataclass(slots=True)`
  (`packages/py/citry/citry/component.py:154-162`): A's mutation model and
  C's `Kwargs(**p)` rebuild are both grounded.
- Bare `c-*` attributes are dynamic expression attributes
  (`packages/py/citry/citry/nodes/__init__.py:430-441`) and the prefix is
  stripped on render (`:631`, `removeprefix("c-")`): confirms A's
  `c-arg:*` mechanism, confirms C's argument against `c-on:*`, falsifies
  B's printed v1.1 spelling.
- `html_attribute_name` accepts `@click`, dotted modifiers, and `:`-forms
  (`crates/citry_template_parser/src/grammar.pest:228-255`): the `@`
  vocabulary passes the parser as plain attributes for all three designs.
- The `$onComponent` payload is exactly `{id, els, data}` built at
  `citry.js:150`, with no transport, no morph, no teardown in the runtime
  (recon-js-runtime, spot-checked): all three designs' client-gap lists
  are accurate; the payload-extension route (A/B/C all use it) is the
  designed extension point.
- Neither B nor C mentions slot fills or template globals in the
  re-render path (grep over both documents).
