# Exploration: the client props passing side (WP23 stage one)

A maintainer-decision report settling how a parent supplies the prop values
a child client component declares (`events.md` 5.5 "props down, events up";
the open remainder recorded in 16.1). The declaration and consumption sides
are settled and landed (`$component`'s config-object form, WP17.1); this
report covers only the passing side, in the four stage-one items the plan
lists (`events_plan.md` WP23): the spelling, reactivity, validation timing,
and the identity rules. Analysis only; nothing here changes code.

Two terms recur. The **boundary entry** is the empty scope object the
events runtime pushes onto Alpine's scope stack at each instance root to
cut scope inheritance, so a nested instance never sees its parent's data
(the audited isolation mechanism). The **supply** is the evaluated result
of a parent's `x-props` expression for one element, the thing this report
designs the delivery of.

Run on 2026-07-17 against the working tree at commit `53aec72` plus the
uncommitted client-wave work. State of that tree as read: `packages/js/` is
entirely untracked; `citry-events.ts` contains the WP16.x applier and wire
layers, WP17.1's delegated listeners, `@c-poll` timers, and the
`$component` props resolution, plus the patch-time preservation guard and
post-patch re-apply machinery; the live two-way and one-way binding wiring
and form collection (WP17.2's build list) are not in the file yet, and no
named-client-component helper exists. A parallel stream may land WP17.2
edits after this read; stage two must re-read before building.

## Prior art (what was searched)

In this repo, verified against source:

- The settled design: `events.md` 5.5 (the composition block, the
  `$component` forms, the recorded lean and its evaluation-side reason,
  lines 3008-3081), 16.1 (the passing-side bullet with the binding
  requirements and the rejected alternatives, lines 4666-4688), 5.1 (the
  attribute channels and the `#c-*` reservation, lines 1758-1764 and
  1842-1888), and the WP23 section of `events_plan.md` (lines 2478-2528,
  the boundaries: no server changes, no ambient context).
- The landed resolution:
  `packages/js/citry-client/src/citry-events.ts:4052-4162`
  (`resolveDeclaredProps`: defaults, required, type matching, the
  `Alpine.reactive` bag), `:4166-4217` (the payload decoration setting
  `ctx.props = {}`), `:4316-4320` (the late-bound `_resolveProps` hook);
  `packages/py/citry/citry/ext/dependencies/client/citry.js:156-170` (the
  config-form registration), `:301-381` (`flushCalls`: decoration, per-entry
  props resolution at `:341-366`, skip-on-failure at `:360-363`).
- The scope machinery the binding must respect:
  `citry-events.ts:1013-1025` (the boundary entry and the isolation
  truncation), `:692-718` (`interceptInit` attach), `:679-681` (the root
  selector), `:4463-4479` (`Alpine.start()` waits for DOMContentLoaded;
  everything else registers at evaluation time), `:2560-2573` (the
  element-keyed timer dedupe, the lifecycle precedent for per-element
  bookkeeping).
- The template side, for where the attribute can physically sit:
  `crates/citry_template_parser/src/grammar.pest:219-269` (attribute names
  are permissive, so `x-props` parses anywhere),
  `packages/py/citry/citry/nodes/__init__.py:833-866` (every component-tag
  attribute becomes a kwarg under its literal name, `:852`; `c-bind` on a
  component tag spreads into kwargs, `:836-848`),
  `packages/py/citry/citry/component_render.py` (a `Kwargs` schema raises
  on unexpected fields, the `schema_cls(**data)` rule near `:1045`), and
  `docs/design/template_html_attrs.md` (the `c-bind` attribute spread on plain
  elements).
- The audited packages: `docs/design/alpinejs/alpine-vuetify-audit.md`,
  which contains the exact prior art. alpine-composition passes props "in
  HTML via an `x-props` attribute holding a JS object expression", read
  with `el.getAttribute('x-props')` and evaluated with
  `Alpine.evaluateLater(el.parentNode, expr)`, "deliberately against the
  PARENT element's scope" (audit lines 115-124, citing the snapshot's
  `component.ts:80-84`); the isolation is the data-stack truncation the
  landed runtime already uses (audit 132-157), and `x-props` is named there
  as the one sanctioned crossing of that boundary (audit 154-157). The
  audit's performance record: the production-patched bundle replaced one
  `watchEffect` per prop key with one watcher for the whole props
  expression, and that was "the big init multiplier" fix (audit 240-243).
- The pinned Alpine 3.15.12 source vendored in
  `packages/js/citry-client/node_modules/alpinejs/src/` (the bundle embeds
  exactly this version; every claim below cites it), plus
  `@alpinejs/morph` 3.15.12.

Searched for and absent: no `Alpine.directive` call exists anywhere in the
landed runtime (magics only, `citry-events.ts:3613-3675`); Alpine core
3.15.12 registers no `props` directive (`src/directives/` contains bind,
cloak, data, effect, for, html, id, if, ignore, init, model, modelable, on,
ref, show, teleport, text, transition); no third-party plugin in the
audited stack registers one (alpine-composition reads the attribute
directly, never registering a directive, audit 117-119).

## 1. The spelling: `x-props`, confirmed

**Recommendation: `x-props`, registered as a real Alpine directive.** The
maintainer's lean holds, and the mechanical survey strengthens it.

The recorded evaluation-side reason stands on its own: a props expression
is client-evaluated and must survive into the rendered HTML, which is
native `x-*` territory, while the `#c-*` channel is server-evaluated and
dissolves before the browser, so a `#c-props` spelling would put opposite
evaluation sides under one sigil (`events.md:3074-3079`). Three further
facts confirm the spelling:

1. **It is the maintainer's own production mechanism, verbatim.** The
   audited alpine-composition stack passed props through an `x-props`
   attribute holding one JS object expression, evaluated against the
   parent element's scope, at Vuetify scale (audit 115-124). WP23's header
   records that this is "a pattern the maintainer used commonly in
   production" (`events_plan.md:2480-2482`). The spelling carries years of
   field use.
2. **The name is unclaimed.** Alpine core 3.15.12 has no `props`
   directive (the directory listing above), and official Alpine plugins
   claim bare directive names the same way (`x-sort`, `x-mask`,
   `x-anchor`), so `x-props` follows the ecosystem convention rather than
   fighting it.
3. **An unregistered `x-*` attribute is silently inert, so the failure
   mode is safe.** Alpine matches any `x-`-prefixed attribute
   (`directives.js:181`) but looks its handler up in the registry and
   substitutes a noop when none exists (`directives.js:127-130`). A page
   whose events runtime is absent renders the attribute harmlessly; the
   loud surface for "props declared but runtime missing" already exists on
   the consumption side (`citry.js:349-356`).

**A registered directive, not attribute polling.** alpine-composition read
the attribute manually inside its component factory. The landed citry
architecture has no per-instance factory to hide that read in, and Alpine's
directive machinery buys exactly the lifecycle the binding needs, for free:

- A directive handler receives an element-bound `effect` whose reactive
  subscriptions are released when the attribute or the element goes away
  (`directives.js:105-134`, `reactivity.js:30-57`,
  `lifecycle.js:115-121`).
- A changed attribute value is processed as remove-then-add
  (`mutation.js:173-183`): the old expression's effect is cleaned up and
  the directive re-initializes with the new expression
  (`mutation.js:187-193`, `lifecycle.js:24-26`). Morph rewrites of the
  attribute therefore re-bind the supply with no citry-side bookkeeping.
- Custom directives run at DEFAULT priority, after `data`
  (`directives.js:206-228`), and `initTree` walks parents before children
  (`utils/walk.js:1-21`, `lifecycle.js:90-113`), so by the time the
  binding's handler runs, every scope it needs exists.

**Alternatives considered and rejected:**

| Spelling | Why not |
|---|---|
| `#c-props` | The recorded reason (opposite evaluation sides under one sigil); additionally the `#c-*` channel is "reserved for keying and morphing features only" (`events.md:1850-1852`), a props contract is neither, and the channel is a real parser channel (grammar, AST, compiler), so this spelling would also buy WP21-class Rust work for a purely client concern. |
| `:c-props` | `:c-*` names a public State field of the owning instance (`events.md` 5.1); props are not State fields, and the channel dissolves server-side into `data-cev-*` specs, which is the wrong evaluation side again. |
| `c-props="..."` (kwarg or expression attribute) | The `c-*` channel is server-evaluated; the supplied value must be a client expression over live client scope, which the server cannot evaluate and would have to smuggle as an escaped string. |
| `x-bind:props` / `:props` | Already-legal Alpine meaning "bind the HTML attribute named `props`"; overloading it would shadow real attribute binding. |
| Per-prop form `x-props:name="expr"` | Multiplies directive instances and effects per prop, exactly the per-prop-watcher shape the production perf work removed (audit 240-243); splits one contract across attributes. |
| `data-citry-props="<json>"` | An inert JSON channel (the audit's `data-x-init` shape): no expressions, no parent-scope access, not reactive. A different feature, not this one. |

**What the `#c-*` reservation sentence says afterwards: exactly what it
says today.** With `x-props` chosen, `events.md:1850-1852` stands
unchanged: the `#c-*` channel remains "reserved for keying and morphing
features only", and its member list remains exactly two (`#c-key`,
`#c-ignore`). The five-channel taxonomy sentence (`events.md:1758-1764`)
also stands unchanged: `x-props` is not a sixth citry channel but Alpine
vocabulary in the Alpine layer, alongside `x-data` and `x-text`, and the
stage-two design fold documents it in 5.5's composition block, not in
5.1's channel list. Had `#c-props` been chosen, the reservation sentence
would have needed a third clause; that the sentence survives untouched is
evidence the channel boundaries were drawn correctly.

**Where the attribute sits, per child kind.** The binding reads `x-props`
on the child component's own root element:

- A **plain-element Alpine child** (today: a subtree with the user's own
  `x-data`; later: a named client component once the runtime's component
  helper exists) carries the attribute directly, authored where the
  element is authored.
- A **citry child** renders its own root from its own template, so the
  parent's expression reaches that root through the existing attrs-dict
  spread: the parent passes an attrs mapping as a kwarg and the child
  spreads it onto its root with `c-bind`
  (`docs/design/template_html_attrs.md`; the production audit found exactly this
  spread pervasive for Alpine attributes, `events.md:1906-1910`). This
  respects WP23's "no server changes" boundary. Writing `x-props`
  directly on a `<c-*>` tag is not a channel today: the attribute parses
  (`grammar.pest:219-269`) and becomes a kwarg literally named `x-props`
  (`nodes/__init__.py:852`), which a `Kwargs` schema rejects loudly as an
  unexpected field (`component_render.py`, the `schema_cls(**data)` rule).
  A template-native forwarding (author it on the component tag, compiler
  moves it to the child's root) would be server-side work with a kwarg
  namespace question attached; it is recorded here as a possible later
  ergonomic, not part of WP23.

Worked example, the landed consumer (a citry child whose component JS
declares props):

```python
class Dashboard(Component):
    # The canonical local-first shape from events.md 5.5: theme toggles are
    # pure client writes, and the server sees the final value on save.
    class Kwargs:
        theme: str = "dark"

    class State(Kwargs):
        pass

    class Events:
        def save(self, state):
            persist_theme(state.theme)

    template = """
      <div>
        <button
          @click="$state.theme = $state.theme === 'dark' ? 'light' : 'dark'"
        >
          Switch theme
        </button>
        <button @c-click="save">Save</button>
        <c-chart-card
          c-attrs="{'x-props': '{theme: $state.theme}'}"
        />
      </div>
    """


class ChartCard(Component):
    class Kwargs:
        attrs: dict | None = None

    template = """
      <div c-bind="attrs">
        <canvas></canvas>
      </div>
    """

    js = """
      $component({
        props: {
          theme: { type: String, default: "light" },
        },
        init: (ctx) => {
          const chart = drawChart(ctx.els[0], ctx.props.theme);
          return () => chart.destroy();
        },
      });
    """
```

The rendered child root carries
`<div x-props="{theme: $state.theme}">`; the expression is evaluated
against the parent position, so `$state` resolves to the Dashboard
instance's State, and the resolved value arrives on `ctx.props.theme`
validated against the declaration. Clicking "Switch theme" is a pure
client write, and the supply follows it without a round trip (section 2
below carries the mechanism).

## 2. Reactivity of passed values

**Recommendation: passed values are reactive to parent-scope changes,
through plain Alpine reactivity and nothing else.** This confirms the
design prose that already calls props "one-way down and reactive"
(`events.md:3017-3018`) and the recorded requirement "plain Alpine
reactivity only" (`events.md:4682-4683`); what follows is the mechanism
that delivers it.

**One effect per carrying element, over the whole expression.** The
directive's handler builds one evaluator for the authored expression and
runs it inside one element-bound reactive effect. Every reactive value the
expression reads (the parent's `$state` fields, parent `x-data`
properties) is tracked by that effect; a parent-side write re-runs it, the
fresh object is validated and written key-by-key into the resolved props
bag, and Alpine's reactivity engine (`@vue/reactivity`,
`alpinejs/src/index.js:40-42`) makes same-value writes free, so no manual
diffing is needed. This is deliberately the production-patched shape, one
watcher for the whole props expression, never one per prop key (audit
240-243).

**The evaluation context is the parent position.** The evaluator is
created against `el.parentNode`, the audited alpine-composition semantics
(audit 115-124). Two properties follow from real Alpine mechanics:

- **Isolation is crossed exactly once, by the author.** The child root's
  own scope stack is the truncated boundary
  (`citry-events.ts:1013-1025`), so evaluating on the child would see
  nothing; evaluating on the parent node walks the ancestor chain
  (`scope.js:18-30`), which for a child nested inside another citry
  instance is itself truncated at that instance's boundary. The supplying
  expression therefore sees exactly what an inline Alpine expression
  written at the child's position in the parent's markup would see: the
  enclosing instance's magics and the user `x-data` scopes above the
  child, and nothing from further out. The maintainer's phrasing in 5.5,
  "the supplying expression sits exactly where the child sits", is
  literally the semantics.
- **The magics resolve to the enclosing instance.** `$state` inside the
  expression walks `closest("[data-cid]")` from the parent node, so it is
  the parent's State, never the child's, with no special casing.

One real limitation rides this rule, inherited from Alpine's `x-for`:
iteration scope is attached to the generated clone itself
(`x-for.js:119`), so an `x-props` on the clone's own root element,
evaluated against its parent, cannot see the iteration variable. The
working pattern is one wrapper element inside the `x-for` template, so the
component element's parent is the clone carrying the scope. This affects
only client-generated lists (a client `x-for` composes client components,
never citry components, `events.md:3091-3094`); server lists are `<c-for>`
and pass per-item data through kwargs server-side, where it belongs. The
audited production stack lived with the same rule. A cleverer capture (the
directive's inline phase runs before the element adds its own scope
layers, `directives.js:136-143`, so a pre-truncation snapshot is
mechanically possible) is recorded as the upgrade path if the wrapper
pattern proves annoying in the field, and deliberately not v1: it needs
two capture rules where the parent-node rule needs one.

**Timing inside Alpine.** An effect's first run is synchronous at
creation; re-runs are queued jobs flushed on a microtask
(`scheduler.js:29-36`), so a parent write propagates to the child's props
on the next flush, batched with every other Alpine update from the same
tick. The evaluator snapshots the scope chain when it is created
(`evaluator.js:48`); attribute rewrites re-create it (the remove-then-add
rule above), which is what keeps the chain current across morphs.

**What this means for effects reading props.** The resolved bag is already
`Alpine.reactive` (landed, `citry-events.ts:4161`, with the comment
promising exactly this future: "effects reading `props.<name>` re-run when
a future supplier writes", `:4101-4102`). Component JS consumes changes
with a plain effect, and deep values compose for free: passing a reactive
sub-object (`x-props="{filters: $state.filters}"`) hands the child a live
reference, so inner mutations in the parent are seen by child effects
without the supplier effect ever re-running, while replacing the object
re-runs the supplier and swaps the reference. One teaching note belongs in
the stage-two docs: destructuring reads once. The settled consumption
example (`init: ({ props: { name } }) => ...`) is fine for one-shot
setup, but a live read must go through the bag (`ctx.props.name`) inside
an effect, the same rule Vue teaches for its props.

**One-way down, enforced.** A child writing `ctx.props.name` today would
succeed silently and be clobbered whenever the parent next re-evaluates,
a delayed, nondeterministic surprise. Recommendation: hand the handler a
read-only view (a small proxy whose `get` passes through to the reactive
bag, so tracking still works, and whose `set` throws the pointed error
naming the prop and pointing at parent state or the child's own `x-data`).
This matches the `$state` clamp precedent (writes outside `_model` throw a
pointed error, `events.md` 5.5 magics table). It tightens the landed
WP17.1 surface, which returns the raw bag; stage two updates the runtime
and its tests together. The alternative, allowing the write and
documenting the clobber, was rejected precisely because the clobber
arrives only when the parent next changes, so the bug reproduces on the
parent's schedule, not where it was written. Deep writes through a passed object reference
(`ctx.props.filters.page = 2`) remain physically possible, as in Vue; the
one-way rule is enforced at the contract's own keys, and the docs say so.

**Excluded, per the recorded requirement:** the alpine-reactivity layer
(refs, computed, watch) stays out. The audit records its own gaps
(`shallowRef` is not shallow, `readonly` returns unstable identities,
audit 71-83); plain `Alpine.reactive` plus `Alpine.effect` is the whole
toolbox here, and it is sufficient.

Worked example:

```python
class SearchPage(Component):
    class State:
        query: str = ""

    class Events:
        def search(self, state): ...

    template = """
      <div>
        <input :c-query.debounce.300ms="search" />
        <c-result-meter
          c-attrs="{'x-props': '{query: $state.query}'}"
        />
      </div>
    """


class ResultMeter(Component):
    class Kwargs:
        attrs: dict | None = None

    template = """
      <div c-bind="attrs">
        <span class="meter"></span>
      </div>
    """

    js = """
      $component({
        props: {
          query: { type: String, required: true },
        },
        init: (ctx) => {
          // Reading through the bag inside an effect is what makes this
          // live; a destructured `query` would be a one-time snapshot.
          const stop = Alpine.effect(() => {
            ctx.els[0].querySelector(".meter").textContent =
              ctx.props.query.length + " chars";
          });
          return () => Alpine.release(stop);
        },
      });
    """
```

Typing into the parent's two-way bound input writes `$state.query`
(pending-update semantics unchanged); the supplier effect re-evaluates
`{query: $state.query}` on the next flush, writes the bag, and the child's
effect repaints. Round trips are not involved at any step.

## 3. Validation timing

**The settled init-time contract, restated.** 5.5 pins it: "Validation
runs when the instance initializes, before init: a missing required
prop or a type mismatch fails loudly, naming the component and the prop"
(`events.md:3062-3065`). Landed behavior on failure: the error is caught
in `flushCalls`, logged with the component named, and exactly that handler
is skipped (`citry.js:360-363`).

**The mechanical gap the passing side must close: the handler currently
fires before any supply can exist.** `$component` callbacks flush as
soon as class JS, data, and the call meet (`citry.js:301-381`), which on
initial page load happens during parse, while `Alpine.start()` waits for
DOMContentLoaded (`citry-events.ts:4463-4479`); and for a post-start
fragment, the dependency manager's observer was created before Alpine's,
so its manifest flush runs first in the batch. In every path, the first
evaluation of an `x-props` expression (which happens when Alpine
initializes the carrying element) comes after the moment the handler
would fire today.

**Recommendation: instance initialization completes when the declaration
meets the first supply.** Concretely:

- A props-declaring registration whose instance root carries no `x-props`
  resolves from defaults immediately and keeps today's timing and
  validation exactly (the landed WP17.1 behavior is the no-supply case).
- When the root carries `x-props` (a static attribute check at resolve
  time), the handler is deferred until the supplier's first evaluation
  lands. Then the merged values (supplied keys over declaration defaults)
  validate as one step, and the handler fires with the validated bag, or
  is skipped with the loud error, preserving 5.5's "before init"
  word for word. The wait is real but short: on initial load it is the
  parse-to-DOMContentLoaded gap that `Alpine.start()` already imposes on
  every expression on the page; for a fragment landed after start it is
  the same mutation batch, one observer later. The rejected alternative,
  firing the handler on defaults and streaming supplied values in
  afterwards, was rejected because it hands the handler a
  nondeterministic first view and moves required-prop failure past the
  handler's start, which contradicts the ratified sentence.
- The deferral needs a small contract extension between the two runtimes:
  `_resolveProps(classId, declarations)` must also receive the instance
  context (the `els` it already carries) and gain a deferred-invocation
  path, and a teardown that arrives while an invocation is still deferred
  must cancel it (the re-render teardown-then-re-fire cycle,
  `citry.js:199-220`). That is stage-two work in both files and must be
  coordinated with the WP17.2 stream editing the same territory.

**Re-validation on reactive updates: every supplier evaluation, per prop,
and nothing ever throws.** When the parent's scope changes and the
supplier effect re-runs:

- Each supplied key revalidates against its declaration (same type rules
  as init, `citry-events.ts:4059-4074`).
- An invalid value **keeps the prop's last valid value** and reports a
  pointed `console.error` naming the component, the prop, the expected
  type, and that the previous value was kept. Repeated identical
  rejections for one instance and prop are reported once until a valid
  value lands again, so a fast-typing parent cannot flood the console.
- A key absent from the new result: an optional prop falls back to its
  init-computed default (the default factory is called once per instance
  at init, and that value is reused, so object defaults keep their
  identity); a required prop's absence is an invalid update, last value
  kept, reported.
- A supplied key no declaration mentions is reported (`console.error`
  naming the declared props), the value ignored, the handler untouched;
  this is what catches a parent-side typo on an optional prop, which
  would otherwise fail silently. At init the same check runs with the
  same non-fatal surface: the declared contract is satisfied, so skipping
  the handler over an extra key would punish the child for the parent's
  spelling.

Throwing is off the table for a mechanical reason, not taste: effect
re-runs execute inside Alpine's scheduler flush, whose job loop has no
error isolation (`scheduler.js:39-51`), so one throwing validation would
abort every later queued effect on the page, and Alpine's own expression
errors are likewise logged and rethrown asynchronously rather than into
the write's stack (`utils/error.js:19-27`). For the same
channel-separation reason, `$error` stays untouched: it is the server
error envelope's box (`events.md` 5.5 magics table), and client-side
contract violations are developer errors that belong on the console.

**What surfaces where, in one table:**

| Moment | Check | On failure |
|---|---|---|
| Instance init (declaration meets first supply, or defaults when no `x-props`) | required, type, unknown keys | handler skipped; `console.error` naming component and prop (landed message shape, `citry-events.ts:4127-4133`, `:4146-4156`) |
| Supplier re-evaluation (parent change) | type per supplied key; required presence; unknown keys | prop keeps last valid value; deduplicated `console.error`; handler and page keep running |
| Expression itself fails (evaluation error) | Alpine's own handling | Alpine logs the expression error (`utils/error.js:24-26`); supply treated as absent for that run |
| Expression result is not a plain object | shape check in the supplier | supply treated as absent; pointed `console.error` naming the element and expression (the same rule 5.1 applies to argument expressions) |

Worked example of both moments:

```html
<!-- init: the parent supplies nothing, the child requires `query` -->
<div x-props="{}">...</div>
<!-- console: [Citry] component ResultMeter_9f2c41 prop 'query' is
     required, but no value was supplied and it declares no default.
     The handler is skipped; the page keeps running. -->

<!-- update: the parent later writes $state.query = 42 (a number) -->
<!-- console: [Citry] component ResultMeter_9f2c41 prop 'query':
     the value does not match the declared type; expected String, got a
     number. The previous value was kept. -->
```

(Class ids are the class name plus a short import-path hash,
`packages/py/citry/citry/component.py:98-114`; the ids above are
illustrative.)

The first message is the landed WP17.1 text; the second extends the landed
type-mismatch text (`citry-events.ts:4146-4156`) with the kept-value
sentence. Stage two locks both by observe-then-lock, and proves each test
bites.

## 4. The identity rules

**Recommendation: the attribute on the child's own root element is the
whole identity mechanism.** No registry, no names, no handshake, no
walking. The rules, each with its mechanical ground:

- **Per-sibling by construction.** Each element carries its own
  `x-props` and gets its own directive instance, its own effect, and its
  own resolved bag. Three `<c-meter>` siblings supplied from three
  different parent fields never share anything, and there are no keys to
  collide (the 16.1 requirement "per-sibling inputs with no shared keys;
  DOM containment is the identity").
- **DOM containment as the identity means containment at distance zero.**
  The supply an instance consumes is the attribute on its own root,
  period. A wrapper-element rule (nearest enclosing `x-props`) was
  considered and rejected: the moment two children sit in one wrapper,
  per-sibling identity is gone, and any distance rule is inheritance in
  disguise.
- **No inheritance across depth.** A child without the attribute resolves
  from defaults; nothing ever looks upward, so a grandchild can never
  absorb an ancestor's supply. Isolation stands doubly: the consumer
  never walks up, and the supplier expression itself evaluates under the
  enclosing instance's boundary truncation (section 2), so the whole
  mechanism cannot pierce what the audit's mechanism protects. Ambient
  values that should cross depth remain provide/inject's job, which is a
  different channel on purpose (`events.md:3083-3087`).
- **Multi-root instances: exactly one root may carry the attribute.** An
  instance's roots share one State and one bag; two roots carrying
  `x-props` would make the supply order-dependent, so the second is a
  pointed error naming the instance and both elements. Zero roots
  carrying it is the defaults-only case.
- **One element rooting two instances (the wrapper-and-only-child case,
  `events.md` 5.5) shares the one attribute.** Each props-declaring
  registration on that element resolves the same supplied object against
  its own declaration independently. The unknown-key report can fire for
  keys meant for the other instance; that noise is accepted in v1 and
  points at a real smell (two contracts sharing one supply surface).
- **A missing required prop fails loudly, naming the child and the
  prop.** At init: the landed pointed error and handler skip, quoted in
  section 3. On a later update that withdraws the key: the invalid-update
  rule, last value kept, reported. A prop can therefore never silently
  revert to `undefined` after a successful init.

Worked example, siblings and depth together:

```python
class OpsBoard(Component):
    class State:
        cpu: int = 0
        mem: int = 0

    class Events:
        def poll(self, state): ...

    template = """
      <div @c-poll.5s="poll">
        <c-meter
          c-attrs="{'x-props': '{value: $state.cpu}'}"
        />
        <c-meter
          c-attrs="{'x-props': '{value: $state.mem}'}"
        />
      </div>
    """


class Meter(Component):
    class Kwargs:
        attrs: dict | None = None

    # The nested <c-meter-label> declares its own props and carries no
    # x-props here, so it resolves from its own defaults: nothing from
    # OpsBoard, and nothing from Meter, is inherited.
    template = """
      <div c-bind="attrs">
        <c-meter-label />
      </div>
    """

    js = """
      $component({
        props: {
          value: { type: Number, required: true },
        },
        init: (ctx) => {
          const stop = Alpine.effect(() => {
            ctx.els[0].style.setProperty("--fill", ctx.props.value + "%");
          });
          return () => Alpine.release(stop);
        },
      });
    """
```

Each poll response updates `$state.cpu` and `$state.mem`; each sibling's
supplier effect re-evaluates only its own expression, and each meter
repaints from its own bag. Dropping one sibling's `c-attrs` removes that
sibling's supply and breaks exactly that sibling, at init, with its own
pointed error naming `value`.

## The runtime shape stage two builds

The consolidated mechanism, so the maintainer ratifies one picture (all of
it client-side, per the WP23 boundary):

1. `citry-events.ts` registers `Alpine.directive("props", ...)` at
   evaluation time, next to the magics. The handler builds an evaluator
   for the expression against `el.parentNode`, runs it inside the
   directive's element-bound `effect`, checks the result is a plain
   object, and writes it into a per-element **supply bag**: one
   `Alpine.reactive` record per carrying element, held in a WeakMap. The
   bag is the rendezvous between the supplier and consumers, because
   either side can exist first (registration at parse time, evaluation at
   start; or evaluation at insert time, registration at script load).
2. Props resolution (`resolveDeclaredProps`) gains the supply half: seed
   defaults, then merge and validate the element's supply, and keep a
   small merge effect alive that re-validates and re-writes the resolved
   bag when the supply changes. Merge effects are deduped per element and
   registration the way element timers already are
   (`citry-events.ts:2560-2573`), and released on teardown and element
   death.
3. The handler gate of section 3, with the `_resolveProps` contract
   extension and the cancel-on-teardown rule, coordinated with the
   WP17.2 stream.
4. The read-only view of section 2 replaces the raw bag on the payload.
5. Tests: unit coverage per rule above (each proven to bite), the e2e
   composition scenarios from the plan, and the canary extended if any
   new pinned-version Alpine surface is touched (none is expected: every
   API named here, `directive`, `evaluateLater`, `effect`, `release`,
   `reactive`, is public on the Alpine object, `alpine.js:25-76`; the
   two private isolation lines stay the ones already pinned).
6. The design fold: 5.5's "the passing side is the one open piece"
   paragraph becomes the settled `x-props` description, and 16.1's
   passing-side bullet moves to the resolved register. Both are
   stage-two edits to the read-only-for-this-WP design docs, made under
   ratification.
7. Wanted exports from `citry/ext/events/__init__.py`: none. The passing
   side adds no Python surface.

## Decision list for the maintainer

Each item is the recommendation above; ratify or redirect per item.

1. **Spelling `x-props`**, implemented as a registered Alpine directive.
   The `#c-*` reservation sentence and the five-channel taxonomy stand
   unchanged.
2. **Supply location**: the child's own root element; exactly one root of
   a multi-root instance may carry it; none means defaults-only. Citry
   children receive it through the attrs spread in v1; component-tag
   forwarding is recorded as possible later server-side work, not built.
3. **Evaluation context**: `el.parentNode`, the audited production
   semantics, with the `x-for` wrapper pattern documented; the
   inline-phase capture recorded as the upgrade if the pattern annoys.
4. **Reactivity**: yes, plain Alpine only; one supplier effect per
   carrying element over the whole expression; per-element supply bag;
   deep reactivity by shared reference.
5. **One-way enforcement**: child writes to declared prop keys throw the
   pointed error (a read-only view over the landed bag). This tightens
   the landed WP17.1 payload surface.
6. **Handler gating**: a props-declaring registration whose root carries
   `x-props` fires after the first supply evaluation, so validation stays
   truthfully "before init". Observable timing shifts by the
   Alpine-start gap on initial load.
7. **Update validation**: per evaluation, per prop; invalid updates keep
   the last valid value with a deduplicated `console.error`; absent
   optional keys fall back to the init-computed default; absent required
   keys are invalid updates; nothing throws inside effects; `$error`
   stays server-only.
8. **Unknown supplied keys**: reported loudly, never fatal, at init and
   on updates alike. (The stricter alternative, failing init on unknown
   keys, is defensible; the recommendation prefers not punishing the
   child for the parent's typo while still surfacing it.)

## Falsifiers

- **F1, the `x-for` rule.** If the dogfood port or e2e work shows
  client-list passing where the wrapper pattern is a recurring paper cut,
  the parent-node evaluation rule is falsified as the permanent answer
  and the inline-phase capture design comes forward.
- **F2, morph re-binding.** The claim that attribute rewrites re-bind the
  supply rests on Alpine's changed-attribute path
  (`mutation.js:173-183`) firing under the applier's morphs. If stage
  two's e2e shows a rewritten `x-props` whose old effect survives or
  whose new expression never binds, the directive needs an explicit
  post-patch supply refresh alongside the existing binding re-apply, and
  this report's "no citry-side bookkeeping" sentence is wrong.
- **F3, the handler gate's cost.** If gating measurably delays first
  interactivity on dense initial-load pages beyond the Alpine-start gap
  every expression already pays, the gate needs the early-evaluation
  refinement (evaluate supplies whose expressions resolve pre-start) and
  the uniform-timing claim is falsified.
- **F4, one-effect scaling.** If profiling at the audit's scale
  (hundreds of instances) shows supplier effects as a startup hotspot
  despite the one-effect-per-element shape, the audit's perf lesson was
  insufficiently applied and the supply layer needs the patched bundle's
  further tricks (measured, not assumed).
- **F5, one-way enforcement.** If dogfood surfaces a legitimate pattern
  that needs child-side writes to declared props (not deep writes, which
  stay possible), the read-only view is falsified and the silent-write
  semantics return with the clobber documented.
