# Design: render performance and optimization

**Status (2026-08-21): the optimized beta feature-set baseline is 38.65 ms for
a warm large-page render: 3.53x a bare Django template and 0.76x
django-components.** The June optimization passes and Rust-walk prototype
below remain useful historical analysis, but their ~13.7 ms / 1.29x baseline
predates the current ownership graph, client lifecycle, extension hooks,
security-aware serialization, and much larger emitted browser runtime. The
refresh also caught a new quadratic ownership scan: no-op render hooks walked
every ownership region accumulated so far, making the first current-tree run
take about 912 ms warm. The first guard reduced it to 87.31 ms; the indexed
ownership, exact-class asset, dormant i18n, and manifest work in section 10
first reduced the authoritative rerun to 62.60 ms; the Rust boundaries and
allocation work in section 10.5 then reached 48.67 ms; bounded traversal in
section 10.6 reached 45.78 ms; allocation, specialization, and pure-body work
in section 10.8 produced the latest table. See the 2026-08-21 entry in
[`benchmarking.md`](benchmarking.md) for the complete measurements and
methodology. This document records what changed, why, and which architectural
levers remain.

This doc is about **consciously making the render faster**. It is the
companion to two neighbours, and the split matters:

- [`benchmarking.md`](benchmarking.md) is about **measuring**: where the
  benchmark code lives, how the harness runs it, what the scenarios contain.
  It answers "how fast are we, relative to Django and django-components".
- This doc is about **optimizing**: where the time goes, what we changed to
  spend less of it, and what is left. It answers "why are we that fast, and
  how do we get faster".
- [`component_constness.md`](component_constness.md) is one specific optimization (marking inputs
  constant so template parts that depend only on them are computed once and
  reused). It predates this doc and stands on its own; section 4 here does not
  repeat it.

For operating rules see [`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. How to measure (reproducing the profile)

Two tools, used together. Neither is wired into CI; both run on demand against
the large benchmark scenario
([`packages/py/citry/tests/test_benchmark_citry.py`](../../packages/py/citry/tests/test_benchmark_citry.py)),
which is the biggest real template citry renders.

**1. cProfile, for "where does the time go".** Load the scenario module, warm
it once (so templates are compiled and caches are filled), then profile a
batch of renders and sort by `tottime` (time inside a function itself) and
`cumtime` (time including everything it calls):

```python
import cProfile, pstats, importlib.util, sys
spec = importlib.util.spec_from_file_location("bc", "tests/test_benchmark_citry.py")
m = importlib.util.module_from_spec(spec); sys.modules["bc"] = m; spec.loader.exec_module(m)
data = m.gen_render_data(); m.render(data)            # warm up
pr = cProfile.Profile(); pr.enable()
for _ in range(10): m.render(data)
pr.disable()
pstats.Stats(pr).sort_stats("tottime").print_stats(20)
```

cProfile inflates absolute time (per-call instrumentation overhead), so read
it for **relative** weight and call counts, never as a wall-clock number. Its
two most useful follow-ups are `print_callers(name)` (who calls this hot
function) and watching a call count fall after a change.

**2. In-process A/B timing, for "did this change actually help".** cProfile's
overhead hides small wins, so confirm each change with a plain timer that
renders the warm page many times and keeps the best run (the least
noise-affected). Measure the same change both ways: swap the new code for the
old in-process (a monkeypatch on the hot method is enough) so the only
variable is the code under test, not process startup or GC timing.

The authoritative cross-engine numbers still come from
`benchmarks/compare.py` (fresh subprocess per cell, median of 5); the two
tools above are for finding and sizing a change before it reaches that table.

Treat that split as a rule, not a preference: the in-process A/B sizes a change
and points it in a direction, but the keep-or-drop decision needs the
fresh-process median. Keeping the best warm run cannot see a first-render or
one-time compile cost, and it samples out steady per-render overhead the change
adds; if you also A/B the new path against the old with both carrying the new
machinery, you hide that machinery's own cost. A change to how a component body
is rendered, once measured this way as a few-percent win, turned out on
`benchmarks/compare.py` to be a large first-render regression for a flat warm
render (section 6.10).

## 2. The render-path cost model

A repeat (warm) render runs almost entirely in Python: parsing happens once at
compile time in the Rust core, and the compiled template is a tree of Python
node objects that execute on every render. So a warm render's cost is the cost
of walking that tree and turning values into HTML.

The work splits into two kinds, and the split is the whole strategy:

**Optimizable overhead** (Python doing more work than it needs to):

- **Attribute resolution and formatting.** For every element with dynamic
  attributes, citry resolves each attribute, merges the contributions
  (`class`/`style` accumulate), and formats the result. The structured
  `class`/`style` values (the React/Vue-style lists and dicts, see
  [`template_html_attrs.md`](template_html_attrs.md)) are normalized here with a chain of type
  checks.
- **HTML escaping.** Every dynamic value and attribute value is escaped before
  it reaches the output. The escaping itself is C-accelerated (markupsafe),
  but each result is wrapped in a `Markup` object (a trusted-HTML string
  subclass), and those wrappers add up.
- **Expression evaluation.** Each `{{ expr }}` and `c-*` attribute runs a
  compiled function through safe_eval. The compilation is cached; the
  per-call wrapper that adds error context is not free.
- **Type dispatch.** The render path is full of `isinstance` checks (to tell a
  rendered subtree from a raw value, a const-marked value from a plain one,
  and so on). Individually tiny, collectively the single most-called built-in.

**Irreducible component machinery** (work a bare Django template does not do
at all, which is the reason citry is a component engine):

- **The marking pass.** At serialize time citry walks the render tree and
  inserts a `data-cid-<id>` attribute on each component's root element, so CSS
  and JS can scope to an instance. Django emits flat HTML with none of this.
- **Dependency collection.** Each component reports the JS/CSS it needs; those
  reports are gathered and turned into `<script>`/`<style>` tags or a manifest
  (see [`dependencies.md`](dependencies.md)).
- **Per-component construction and slots.** Each instance is constructed,
  given an id, linked to its parent, and has its slots/fills resolved across a
  context boundary.

The optimizable overhead is where Python-level fixes pay off (section 4). The
irreducible machinery is the floor: it can be made cheaper but not removed
without dropping the feature, and getting *below* a bare template means moving
some of it into Rust (section 6).

## 3. The ceiling, and what actually sets it

On the 2026-06-22 feature set, after the passes in section 4, Citry's repeat
render was about 1.29x a bare Django template and about 3.4x faster than
django-components. Those numbers are historical: the current beta-feature
baseline is 3.53x bare Django and 0.76x django-components on a materially richer
and larger render. The cost-model work below explains the June profile; future
optimization decisions must be re-profiled against the current baseline
recorded in [`benchmarking.md`](benchmarking.md).

It is tempting to call the rest "the structural cost of Python components," and
an earlier version of this doc did. Measurement (section 6.5) shows that is
wrong. The genuinely unavoidable Python work, the data callbacks
(`template_data`) and expression evaluation, is only ~10% of the render. The
other ~85% is **render-walk machinery** (tree traversal, type dispatch,
attribute formatting, string assembly, per-component construction and hooks):
mechanical work that merely happens to run in a tree of Python objects. So the
gap to Django is largely reducible, and matching or beating a bare template is
reachable, but not by trimming Python further. It means running the walk itself
in Rust, which moves the compiler-output contract (the compiler emits Python
node classes today, see [`component_rendering.md`](component_rendering.md)). Section 6 scopes that
move and the prototype that de-risks it.

## 4. Optimizations done (2026-06-22 pass)

Each change below was verified to leave the rendered HTML byte-identical (the
output is the contract; only the work behind it changed) and sized with the
A/B timer. They are listed biggest win first. The cross-engine table is in
[`benchmarking.md`](benchmarking.md) section 11; the per-change deltas here are
from the in-process A/B timer on this machine and are directional.

### 4.1 Dependency collection: O(n*depth) to O(n)

The largest win (~3.2 ms). Each component reports a dependency record, and
those records bubble up to every ancestor as nested renders merge into their
parents. The merge copied the child's whole record list into the parent, so a
record at depth *d* was re-copied at each level above it. On the 325-instance
page this built **469,583 record copies**, and the final de-duplication ran
over **154,120 entries** to recover the 71 distinct records.

The fix holds each render context's records as an **insertion-ordered set** (a
`dict` used for its keys) instead of a list. The merge becomes a set union, so
it de-duplicates on insert and is idempotent: a record that has already
bubbled through is not copied again. The accumulation can no longer multiply,
and emission reads the 71 distinct records directly.

An earlier fix (a prior session) had de-duplicated the records *before* the
expensive per-record script lookup, which removed the wasted lookups but left
the list itself blowing up. This change removes the blow-up at its source.
Code: [`citry/extensions/dependencies/__init__.py`](../../packages/py/citry/citry/extensions/dependencies/__init__.py)
(`on_component_data`, `on_render_context_merge`).

### 4.2 Element attributes format in one pass

The element renderer formatted attributes one at a time: it called
`format_attrs({key: value})` once per attribute, and each call escaped, joined
a single piece, allocated a `Markup`, and was concatenated with a leading
space. For an element with three attributes that is three of everything.

It now formats the whole resolved attribute dict in a single `format_attrs`
call for the common case (no attribute value is a nested-template render),
falling back to the per-attribute path only when a nested template is present
(those keep their parts so components inside them stay deferred). One escape
pass, one join, one allocation per element. Code:
[`citry/nodes/__init__.py`](../../packages/py/citry/citry/nodes/__init__.py)
(`ElementAttrsNode._format`).

### 4.3 Escape to a plain string, not a Markup, in format_attrs

`format_attrs` escapes each attribute key and value into an f-string and wraps
the whole joined result as one `Markup` at the end. The individual
`escape()` calls therefore allocated a `Markup` per key and per value only to
have it immediately turned back into a plain string by the f-string: pure
allocation.

A new helper, `escape_to_str`
([`citry/util/html.py`](../../packages/py/citry/citry/util/html.py)), runs the
same escaping but returns a plain `str`. It uses markupsafe's own inner
escaper (the routine `escape` calls before wrapping the result), with a
fallback to the public `escape` if a future markupsafe removes the name, so
the escaping stays exactly markupsafe's. Use it only where the escaped text is
concatenated into a larger string that is marked safe as a whole, so the
unmarked piece is never re-escaped; for a value that becomes output on its
own, `escape` is still correct. `Markup` allocations across the render dropped
about 78%.

### 4.4 Cheaper component ids

Each component instance gets a short random id for its `data-cid` marker. This
used nanoid, which makes a `urandom` syscall and recomputes its
rejection-sampling math on every call, about 342 times per render. These ids
scope DOM and CSS to an instance; they are not secrets. `gen_id` then switched to
`random.choices` over the same alphabet, which is uniform, has the same id
space (so the same collision odds), and is about 4x faster with no syscall.
(A later pass replaced `random.choices` with a counter off a random base, faster
again and the current scheme; see section 8 and
[`util/id.py`](../../packages/py/citry/citry/util/id.py).)

### 4.5 Port side: hoisting render-invariant constructions

Not an engine change, but the idiomatic thing a citry user would do: a value
that is the same on every render of a component does not belong in
`template_data`. In the benchmark port the breadcrumb home icon (a fixed
`Icon`) is now built once at module load. A sweep of the port found it was the
only pure-literal *component* construction; the other invariants are the
literal attribute dicts, which the Const variant already marks (see
[`benchmarking.md`](benchmarking.md) section 6.4). Rendering a component
instance does not mutate it, so a single shared instance is safe to reuse.

### 4.6 Tried and reverted: fusing the attribute merge

`ElementAttrsNode._resolve` builds a one-key dict per attribute and then
merges them. Fusing the merge into the resolve loop to skip those dicts was
implemented, measured as perf-neutral, and reverted. The reason is in the
profile: `_resolve`'s time is in its callees (resolving each attribute through
safe_eval), not in building the small dicts, so removing the dicts changed
nothing and only added public surface. Recorded here so it is not re-attempted
blind.

### 4.7 Per-component fixed-overhead trims (second pass)

A second pass chased the per-component fixed cost (the work a bare Django
template does not do, paid once per component, ~342 times on the large page).
Together these took the repeat render from ~14.5 ms to ~13.7 ms.

- **Lazy extension-hook contexts.** Each per-component hook dispatcher
  (`on_component_rendered`, `on_slot_rendered`) built its context dataclass and
  fired the event even when no installed extension implements the hook. With
  only the dependencies extension installed, those fire for nobody. They now
  check `has_hook` first and return early, skipping the build
  ([`citry/extension.py`](../../packages/py/citry/citry/extension.py)).
- **Cached strategy validation.** `serialize_render` validated its
  `deps_strategy`/`deps_position` against `get_args(<Literal>)` on every call;
  the allowed values are computed once into module constants
  ([`citry/serialize.py`](../../packages/py/citry/citry/serialize.py)).
- **Memoized class-level dependency resolution.** `_resolve_records` rebuilt
  each *class's* `Dependencies` entries and JS/CSS for every *instance* (the
  serialize was ~57% this one function). The class-level part is now resolved
  once per class within the call and reused across its instances
  ([`citry/extensions/dependencies/emission.py`](../../packages/py/citry/citry/extensions/dependencies/emission.py)),
  cutting ~0.24 ms.
- **Tried and reverted: a cross-render version of that cache.** Persisting the
  class resolution across renders (keyed per Citry, invalidated on file reset)
  measured neutral against the within-call memo: once duplicates are collapsed
  within a render, the remaining first-sight resolution is cheap (most classes
  have no dependencies, so it is trivially empty), so caching it across renders
  saved nothing and added a weak-keyed store plus invalidation. Reverted.

## 5. Further Python-level opportunities (explored 2026-06-22)

The leads from the first pass were chased down. The finding is that the
Python-level wins are now **at or below the full-render noise floor** (about
+/- 0.2 ms on a 13.5 ms render): the big structural costs are gone, and what is
left is spread thinly across many already-tight call sites. One small cleanup
landed; the rest were measured and either rejected or judged not worth the
churn. This is the evidence that section 6 (moving work to Rust), not more
Python micro-tuning, is the next real lever.

What was investigated:

- **safe_eval per-call wrapper (landed, sub-noise).** The `error_context`
  decorator wraps every intercepted operation of every expression (variable,
  attribute, subscript, call; ~27,700 calls per render). It used to extract the
  source string and token positions from the arguments on every call, but those
  are only used to build a message when the operation raises. Moving that
  extraction into the `except` branch leaves the success path bare. Measured at
  ~7 ns per call, ~0.19 ms per render: real and strictly less work, but below
  what the full-render timer can resolve. Kept as a cleanup
  ([`citry_core/.../safe_eval/error.py`](../../packages/py/citry_core/citry_core/safe_eval/error.py)),
  not because the render got visibly faster.
- **Type-dispatch in the value-to-output path (tried, reverted).** Adding a
  "plain string, just escape it" fast path to `citry_render._render_value`
  looked obvious but was reverted: instrumenting it showed **none** of its calls
  on the real page are a plain `str`. The function exists for *composed* values
  (a `Slot`, an unrendered `CitryElement`, an already-rendered `CitryRender`);
  plain interpolated text is escaped on a different, already-direct path. The
  fast path was dead code. A good reminder to count the branch before adding it.
- **`isinstance` overall (no change).** It is the most-called built-in, but its
  weight is spread across paths that are already tight: `_render_body` checks
  `str` first and moves on; the render-tree `walk` does two checks per part that
  are inherent to telling a deferred child from a nested render; `const_value` /
  `is_const` are a single check each and exist to support the `Const` feature.
  No single reordering moved the full-render timer.
- **Attribute-merge and kwargs allocation (not pursued).** The same per-key
  allocation pattern as section 4.6 (which was measured neutral and reverted):
  `_resolve`'s and `_resolve_kwargs`'s time is in resolving each value through
  safe_eval, not in building the small dicts, so removing the dicts is expected
  to be neutral for the same reason. Left alone unless a profile says otherwise.

## 6. Candidates for moving to Rust (analysed 2026-06-22)

**Finding: the obvious string-processing paths are already in Rust, and the
per-call boundary cost rules out the remaining fine-grained moves (one would
make escaping 2x slower). The single borderline candidate is attribute
formatting, about 7% of the render, and even it is marginal. The real lever is
architectural (running the render loop itself in Rust), not a piecewise port.**

The selection rule a path must clear to be worth moving:

- **It is genuinely hot.** High call count and real `tottime` share in the
  warm-render profile, not just "feels low-level".
- **Its work is CPU on plain data, not Python-object choreography.** Moving a
  loop that mostly calls back into Python objects (user `template_data`, Python
  expressions, component instances) buys little and costs a boundary crossing
  each call. Good candidates take simple inputs (strings, the compiled node
  data) and return simple outputs.
- **Its interface is stable and narrow.** The Rust/Python boundary is a
  contract (see the high-risk areas in [`/CLAUDE.md`](../../CLAUDE.md)); a path
  still changing shape is not ready to freeze across the binding.
- **The win survives the boundary cost** (the one that does most of the work
  below).

### 6.1 What is already across the boundary

Four Rust crates back `citry_core`: `citry_template_parser` (parse and
compile), `citry_html_transform` (the marking scan), `python_safe_eval`
(expression transformation), and `citry_core_py` (the PyO3 glue). The Python
runtime imports from Rust: `template_parser.compile_template` / `parse_template`,
`html_transform.mark_html`, and `safe_eval.safe_eval`. So Rust already owns the
mechanical string work: turning a template into a node tree, scanning a
component's rendered HTML to splice in its `data-cid` markers, and turning an
expression string into safe code. What is left in Python is the **runtime**:
walking the compiled node tree and turning values into HTML.

### 6.2 The decisive constraint: the per-call boundary cost

A minimal PyO3 round-trip, measured here by calling `mark_html` on a 7-character
string, is about **177 ns** on this machine. That is the floor every crossing
pays before any useful work, so a path called N times per render starts at
177ns x N just in crossings. This is what rejects the fine-grained candidates,
and it refutes this section's own earlier guess that escaping was a starting
point:

- **HTML escaping is already C and must not move.** `escape_to_str` is about
  **87 ns end to end** (markupsafe's C escaper). A Rust escape would pay ~177 ns
  just to cross, before escaping one character: roughly **2x slower**. Escaping
  is called tens of thousands of times per render, so this is decisive.

### 6.3 Candidate verdicts

- **Already C or Rust (no win, some would regress):** HTML escaping and `Markup`
  construction (markupsafe C), the `mark_html` scan, and parsing/compilation.
  Re-porting these to Rust gains nothing and, for escaping, loses.
- **Python-object choreography (cannot move piecewise):** the render-tree walk
  (`_render_one` / `_render_body` / `walk`), expression **evaluation** (the
  compiled functions run Python against Python context data), and
  kwargs/slot/provide resolution. Each step calls back into Python objects, so
  a Rust version would cross the boundary per node, and the 177 ns floor turns
  that into a loss. These move only if the objects they walk move too (6.5).
- **Borderline, the only real piecewise candidate:** attribute formatting (6.4).

### 6.4 The one borderline candidate: attribute formatting

`format_attrs` plus the `class`/`style` normalizers are about **6.9%** of the
warm render (cProfile), at ~591 `format_attrs` calls per render. It is the most
string-like of the Python hot paths, so it is the natural thing to weigh. It
still does not clearly pay:

- Part of its cost is escaping, already C: no Rust win there.
- The `class`/`style` values are structured Python (lists and dicts of class
  names, dicts of style properties). Passing them to Rust means converting
  nested Python into Rust on every call, which costs more than the 177 ns base
  crossing.
- ~591 crossings per render is already a ~0.1 ms floor, before that conversion.

So of a roughly 1 ms prize, perhaps 0.3 to 0.5 ms would survive, in exchange for
a new function frozen into the cross-language contract. The clean shape (format
an element's *already-normalized*, strings-only attributes in Rust) needs the
normalization done in Python first, and the normalization is the Python-heavy
part, so little is left to move. Verdict: defer unless a future profile makes it
clearly worth a new contract surface.

### 6.5 Where the render time actually goes (and why "structural" was wrong)

Measuring the ~13.7 ms render by callback (not by cProfile bucket) corrects an
earlier claim in this doc. The unavoidable Python work is small:

- **Expression evaluation** (the compiled safe_eval functions running): ~0.8 ms
  (~6%), over ~2,580 evaluations. Python, on Python data, so it stays.
- **`template_data`** (and `js_data`/`css_data`), the user data methods: ~0.5 ms
  (~4%). User Python, so it stays.
- **Serialize / marking**: ~0.7 ms (~5%). `mark_html` is already Rust; the rest
  is Python orchestration, and its deps half was trimmed this pass (4.7).

That is only ~15%. The other **~85% (~11 ms) is render-walk machinery**: walking
the compiled node tree, the per-node type dispatch, resolving and formatting
attributes, assembling and joining strings, and the per-component work
(construction, context setup, id, slots, the extension-hook dispatch). None of
that is an unavoidable Python callback; it is mechanical work that merely runs
in a tree of Python objects. So the gap to Django is **not** "the structural
cost of Python components" (an earlier conclusion here, now retracted) - it is
walk machinery, and some of it is Rust-able. But "~85% Rust-able" overstated it:
the prototype (6.7) found that much of that 85% is woven through the
irreducibly-Python component model (the user component classes, `template_data`,
the per-component hooks) and cannot leave Python, so the genuinely movable part
is the string assembly and traversal, ~20-30%, not 85%. The lever is real but
smaller than this section first claimed.

### 6.6 The render walk in Rust: the architecture

Running the *walk* in Rust removes the interleaving that defeated the
fine-grained moves: the traversal and string assembly stay on the Rust side, and
the boundary is crossed only for the ~15% that is genuinely Python.

Today the compiler emits Python node classes (see [`component_rendering.md`](component_rendering.md))
that the Python runtime walks. The change is to emit a **render plan the Rust
core executes**: Rust walks the plan, assembles static text, formats attributes,
escapes, and joins, and calls back into Python only for `template_data` (once
per component) and expression evaluation (once per expression). Crossings drop
from tens of thousands of fine-grained string ops to a few hundred coarse
callbacks (~342 components + ~2,580 expressions ~= 0.5 ms of crossing for the
whole page at the 177 ns floor).

The hard part is not the string work; it is the **component machinery** the walk
drives: per-component construction, the context boundary, slots/fills,
provide/inject, and the extension-hook dispatch (the deps collection's
`on_component_data` fires per component). These are Python objects and a Python
extension system. For each, the Rust walk can either keep it Python (a crossing
per component, which the math above affords) or move it too (much larger); the
first is the pragmatic start. This moves the compiler-output format, a high-risk
contract ([`/CLAUDE.md`](../../CLAUDE.md)), and a chunk of the runtime, so it is
a project, not a patch, and needs a prototype before commitment.

### 6.7 The prototype, and what it found

Built (`crates/citry_core_py/src/prototype.rs`, a throwaway `RenderPlan` class,
since removed): a Rust walk of a body expressed as static segments interleaved
with `{{ expr }}` interpolations, calling back into Python for each compiled
expression, measured against the equivalent Python walk. Both call the same
compiled expressions, so the comparison isolates the walk itself; the plan
(segments and expressions) is held on each side and only the context crosses per
render, as a compiled template would be.

It answered the one question it could (interpolation; attributes and the
component machinery were left for a later prototype) and the answer reshapes the
verdict:

- **The per-expression crossing is affordable.** Even paying a Rust-to-Python
  crossing per expression, the Rust walk beat the Python walk on every body. The
  crossing was the headline risk, and it is cleared.
- **But the win is bounded and sub-threshold.** Output byte-identical; the Rust
  walk saved **10% on an expression-heavy body, up to 25% on a static-heavy one**
  (1.10x to 1.33x). The reason: the expression evaluations are the bulk of the
  dynamic work (~80% of the expression-heavy body, 3.7 of 4.6 us over 9 evals),
  and they are Python on Python data, so they stay. Rust cut the walk machinery
  itself ~1.8x net of the crossings, but the eval floor caps the overall win.
- **So the "30% net -> go" threshold was not met** on the part that could be
  tested, and the part that could not (the component machinery: construction,
  context, slots, the per-component hooks) is the *irreducibly-Python* component
  model, not movable string work. The realistic Rust-walk ceiling is the string
  assembly and traversal, ~20-30% of the render, which would reach roughly
  Django parity, not beat it, in exchange for moving the compiler-output
  contract and a chunk of the runtime.

**Verdict: not yet.** The architectural move is a large, high-risk project for a
bounded (~parity) gain, and the prototype showed the dominant cost is the
expression eval, which the Rust walk does not remove.

That eval is worth attacking, but **not** the way an earlier draft of this
section claimed. The claim was that a literal key's sandbox check is invariant
to the runtime value, so the compiler could resolve it once and emit direct
access. That is wrong, and reading `safe_eval/sandbox.py` shows why:
`is_safe_attribute(obj, attr)` calls `_is_internal_attribute`, which blocks
*every* attribute on a `CodeType`/`TracebackType`/`FrameType` (and special
attributes on functions, generators, and so on) purely from `obj`'s runtime
type. `is_safe_attribute(frame, "name")` is False while `is_safe_attribute(dict,
"name")` is True, for the same key. A compile-time fast path would emit direct
access not knowing `obj` is not a frame, which is a sandbox hole. The check is
genuinely value-dependent.

What is real: the check is ~62% of a subscript eval (272 of 436 ns), and for the
built-in container/scalar types none of `_is_internal_attribute`'s dangerous
branches can match, so its result there reduces to `not attr.startswith("_")`.
So a **runtime** fast path - a guard like `if type(obj) in
_SAFE_CONTAINER_TYPES: return not attr.startswith("_")` (exact types only;
subclasses and custom objects fall through to the full check) - is provably
equivalent and skips the isinstance chain. But it is a security-sensitive change
to the sandbox, covers only exact common types, and is worth ~2-3% of the render
(the eval is ~6% of the page and this trims part of it), not the ~1 ms an
earlier draft implied.

So no lever short of the Rust-walk project reaches parity: that project gets to
~parity (and is the only route to parallelism, 6.8); the runtime sandbox fast
path is ~2-3% and security-sensitive; the remaining Python micro-opts are low
single digits. The honest decision is binary: commit to the Rust-walk
architecture, or accept ~1.3x as where a Python component engine lands. (That
decision was taken and settled - the engine was built out, measured, and
archived; see 6.9.)

### 6.8 Parallelism is the same lever, not a separate one

Can node sub-trees render in parallel? Not in current Python: the GIL serializes
CPU-bound threads, so threads buy nothing, and the render holds shared mutable
state (the deps collection, the parent/child context linkage) that would need
real locking even under free-threaded Python (experimental, with C-extension
caveats). `multiprocessing` and subinterpreters cannot share the render tree. So
parallelism is reachable only *through* the Rust walk (no GIL, `rayon` over
independent sub-trees) - it is the same project, which is a further reason to
prioritize the prototype above over more piecewise Python tuning.

### 6.9 Postscript: the full engine was built, measured, and archived (2026-06-25)

The binary decision in 6.7 was taken: the prototype was built out into a full
production body engine and measured, to settle "roughly parity, not a beat" with a
real implementation rather than the isolated-walk estimate.

What was built: a Rust `BodyEngine` (with a `FoldedPlan` that lowers a const-precomputed
body once and caches it) that walks the body in Rust - static text, simple
attribute regions, and scalar `{{ expr }}` interpolation - emitting the real
`list[RenderPart]` and delegating every other node (components, slots, control
flow, non-scalar values) back to Python. It crosses to Python only for expression
eval and the in-walk hooks, and was gated behind a default-off flag.

What it measured (byte-identical everywhere - 823 rendering tests plus the 203 KB
benchmark):

- **~parity on a real, construction-bound page** (the large benchmark: 12.5 ->
  12.7 ms, 0.98-1.0x). The first cut, walking the Python body item-by-item, was
  ~3-6% *slower* (the per-item `get_item`/`isinstance` crossings cost more than the
  string work saved); pre-lowering the body into the Rust-side `FoldedPlan` removed
  that and brought it to parity.
- **~1.06x on a markup-heavy page** (40 components x 24 attributes + 12
  interpolations: 1.13 -> 1.06 ms), the regime where string work dominates -
  exactly where the prototype's isolated 1.8x came from, attenuated by the
  unavoidable per-component crossings.

So the production measurement confirmed the prediction: the body walk reaches
parity on a real page and wins only modestly where string work dominates. Not a
beat; the page stays construction-bound (section 8), and the expression-eval floor
stays in Python.

**It was removed from the live code but preserved in git history**, so a future
portability or multi-language port (the real reason to want a host-agnostic Rust
walk - see the section 6 opening) can pick it up:

- The full implementation, its design doc (`render_plan_rust.md`, with the complete
  contract, callback ABI, and measurements), and the prototype harness live in
  commit **`b7b2f4e`** ("refactor: Rust renderer proof of concept (rejected)").
- It was taken back out of the tree in **`60e1980`** ("revert: remove the Rust
  render engine from the live code").
- To bring it forward again: `git revert 60e1980`, or cherry-pick from `b7b2f4e`.

### 6.10 Explored and reverted: rendering a body by running a generated function

A cross-engine comparison surfaced a third option section 6.7 missed, between
the Python walk and the Rust walk: generate a Python function from each
component's body, the way Jinja2 turns a template into straight-line Python, and
run that function instead of walking the body's node list every render. It was
built out, proven byte-identical (a battery of constructs rendered both ways,
plus the 203 KB benchmark page modulo random ids), measured, and taken back out.
The implementation is preserved in git (commit `ec5faaf`); to bring it forward,
cherry-pick from there.

It is a net loss on a real page, for the reason section 8 gives: the warm render
is construction-bound. Generating a function removes the body walk, but that
walk is a minority of the render; the work it cannot remove (expression
evaluation, attribute resolve and escape, the per-component construction)
dominates.

- **First render: about +33%** on the large benchmark page (about 38 to 50 ms).
  Generating a function for every component body, and for the sub-bodies of
  slots, fills, and nested templates, is real work that all lands on the first
  render. It is the same one-time compile cost Jinja2 pays
  ([`benchmarking.md`](benchmarking.md) section 11), but here with no warm-render
  payoff to earn it back.
- **Warm render: flat** (about 14.7 ms generated versus about 14.6 ms walking,
  inside the run-to-run noise). The per-component bookkeeping that selects and
  caches the right generated function costs about what running it instead of
  walking saves, so they cancel.
- **The body work alone is 1.15x to 1.24x faster** on static- and loop-heavy
  bodies (an attribute-heavy body is 1.01x, no gain, since the evaluate, merge,
  and escape work is intrinsic). The win is real but small, and it falls on the
  slice of the render a construction-bound page spends the least time in, so it
  does not reach the whole-page number.

This lands where the archived Rust walk did (section 6.9) and for the same
reason: the leaf work dominates, so a faster walk, in Rust or as generated
Python, reaches roughly parity, not a beat. The levers that move the whole-page
number are per-component construction (section 8) and the per-expression sandbox
(section 6.7), neither of which this touches.

It nearly shipped on a misleading measurement; that story, and the rule it
sharpened, are in section 1 and [`RATIONALE.md`](../agent/RATIONALE.md).

## 7. Working rules for optimization

- **Output is the contract; prove it byte-identical.** A render optimization
  that changes the HTML is a bug, not a speedup. Diff the rendered page (modulo
  the random per-render ids) before and after, and lean on the suite's exact
  attribute/element assertions.
- **Measure, then keep.** Size every change with the A/B timer in section 1. A
  change that is within noise does not go in, however clean it looks (4.6).
- **Read the profile before guessing.** A "this looks slow" hunch is worth one
  cProfile run to confirm; the biggest win in section 4 (the dependency
  blow-up) was invisible in `tottime` and only showed up as a call count.
- **Fix the cause, not the symptom.** The dependency fix removed the
  accumulation; it did not add a bigger cache or a faster de-duplication over
  the already-exploded list.

## 8. Per-component construction cost (and the Python trims)

Section 6.5 found that a page of many small components is **construction-bound**:
most of the per-component cost is Python work (creating the instance and running
`template_data`) that no Rust walk can speed up. So the question this section
answers is: what does that construction actually do, and can it be made cheaper *in
Python*?

### 8.1 What was trimmed (low-risk wins, landed)

Four low-risk reductions landed. Measured together (cProfile of one component's
construction, then a component-render harness):

- **Component-id generator** -> a per-process random base plus a counter,
  using an HTML-attribute-safe lowercase alphabet (`gen_id` in
  [`util/id.py`](../../packages/py/citry/citry/util/id.py)).
  This replaces the `random.choices` scheme that section 4.4 describes.
- **`has_hook` short-circuit** on `on_component_input` / `on_component_data`
  ([`extension.py`](../../packages/py/citry/citry/extension.py)).
- **Skip slot normalization** for the no-slots case
  ([`component.py`](../../packages/py/citry/citry/component.py)).
- **Lazy `_provides_own`** ([`component.py`](../../packages/py/citry/citry/component.py)).

Result: construction (the `_create_instance` + `template_data` path) got about
**34% cheaper** (the six PRNG draws of `random.choices` are gone, and the
`on_component_input` context dataclass is no longer built when nothing subscribes),
which showed up as about a **19% faster** render on a page of many tiny components
(less on richer pages where the body walk dominates). The later A10 browser
scaling gate changed the id alphabet to `c[0-9a-z]{8}`: HTML attribute names
are case-insensitive, so mixed-case ids could collapse onto the same
`data-cid-*` marker. Ids remain non-deterministic and the counter mechanism is
unchanged.

### 8.2 What construction costs (the baseline)

Profiling one simple component's construction (`_create_instance` + `template_data`
+ context; the wall-clock is ~3.5 us per component) breaks the cost, *before the
trims above*, into four areas:

1. **Component-id generation, ~20% of construction.** The old `gen_id` was
   `"".join(random.choices(_ID_ALPHABET, k=6))`. `random.choices` is not one cheap
   call: it does `floor(random() * 62)` per character, so one id is six
   Mersenne-Twister draws plus six `math.floor` calls plus a list and a join - the
   single largest contributor in the profile. (Now: a counter off a random base;
   see 8.1.)
2. **Extension per-component touchpoints, ~15%.** Every component runs
   `_init_component_instance`, which per extension allocates a config object (with a
   `weakref`) and `setattr`s it onto the component, and then `on_component_input`,
   which **built a frozen context dataclass for every component even when no
   extension subscribed**. The three hot hooks already guarded with `has_hook`;
   `on_component_input` / `on_component_data` did not (now they do; see 8.1).
3. **`Component.__init__` core, the rest of the spine.** A defensive copy of the
   kwargs dict, slot normalization that ran even with no slots, the typed
   `Kwargs`/`Slots` dataclass instantiation, and two empty-dict allocations for
   `provides`.
4. **Normalization helpers.** `to_dict` runs ~3 times per component, and
   `_normalize_data` normalizes the `template_data`/`js_data`/`css_data` outputs.

The recurring pattern: the work is unconditional but only needed for a subset of
components. Most components are leaf markup with no slots, no provides, no
extension-config access, and a `template_data` that just reads the plain kwargs
dict, so almost all of it is paid for nothing.

### 8.3 The reductions, ranked

**1. Component id: a counter or a hybrid (the standout, landed).** The id only
scopes a component's CSS/JS (the `data-cid-<id>` marker) and is a DOM lookup key; it
is never a dict key, never persisted, and not a secret, and it only has to be unique
within one serialized page. So the random id was over-provisioned. Measured (200k
iterations):

| scheme | per id | vs old |
|---|---|---|
| old (`random.choices`, 6 draws) | 0.299 us | 1.0x |
| per-render **counter** (`c1`, `c2`, ...) | 0.056 us | **5.3x** |
| **hybrid**: one random base per render + counter | 0.061 us | **4.9x** |
| single `getrandbits(36)` + 6-char assembly | 0.399 us | 0.75x (slower) |

The last row is a useful negative: one `getrandbits` plus a Python assembly loop is
*slower* than `random.choices`, because the per-character shift-and-index in Python
costs more than `random.choices`' C internals. Only a counter avoids the per-char
work. The **hybrid** (random base + counter) was chosen: ~5x faster and keeps
cross-render uniqueness because different bases pick different starting
points. A10 later moved its suffix to eight lowercase base-36 characters after the `c` prefix so
the marker name cannot collide under HTML's case folding. See
[`util/id.py`](../../packages/py/citry/citry/util/id.py).

**2. Guard `on_component_input`/`on_component_data` with `has_hook` (landed).**
Return early when nothing subscribes, exactly as the three hot hooks already do, so
the per-component context dataclass is never built. In the default Citry nothing
implements `on_component_input`, so it is a pure win; these are fire-and-forget
hooks, so there is no observable change.

**3. Skip slot normalization when there are no slots (landed).** The render path
sets `element.slots = slots or {}` (a falsy empty dict), so a `slots is not None`
guard did not short-circuit and `normalize_slot_fills({})` ran a call frame to build
an empty dict. A truthiness check returns `{}` directly for the common no-slots
component.

**4. Trim the `Component.__init__` allocations.** Lazy `_provides_own` landed
(initialize to `None`, let `provide()` create it on first use). Two medium-risk
follow-ups remain: a **lazy typed `Kwargs`/`Slots` view** (build from the raw dict
on first access, saving the dataclass instantiation for the common case where
`template_data` reads the plain dict; medium risk because a required-field `Kwargs`
would then raise at first access rather than at construction), and **avoiding the
defensive kwargs copy** when no input-mutating extension is active (gate on
`has_hook("on_component_input")`; medium risk because a wrong gate would leak one
render's mutation into the next).

**5. `_init_component_instance` plan cache (medium, not done).** Cache, per
component class, the resolved `(name, config_cls)` tuple so the per-component path is
just `setattr(component, name, config_cls(component))`. Making the config object
itself lazy would remove the `weakref` + object + `setattr` for components that never
read their extension config, but it is the riskiest (timing of when
`component.<ext.name>` exists), so it should follow the cheaper wins.

### 8.4 Honest assessment

Stacking the low-risk wins trims construction by perhaps 20-30%, about 1 us off a
~3.5 us construction. At the render level that is a few percent for a page of many
small components, and less for a page of rich components where the body walk and
attributes dominate. The medium-risk changes roughly double that ceiling but carry
correctness questions worth a careful pass each.

So: real, low-risk, worth doing as an incremental Python pass, with the id generator
the clear first move - but it does not change the strategic picture any more than the
Rust port did (section 6). A Python component engine that creates an instance, runs
the user data methods, and walks a node tree per component lands around 1.3x a bare
Django template; construction is a meaningful slice of that, but trimming it yields
single-digit percentages, not a different order. The constructs are sound; the wins
are in making the conditional work conditional and deferring the speculative work,
not in replacing the model.

## 9. Citry Core release-wheel profile and ABI decision (2026-08-18)

Citry Core's release pipeline needed fewer artifacts and shorter qualification
runs, but neither is allowed to silently tax application performance. Two
independent changes were therefore measured as a four-way matrix rather than
only comparing the old wheel with a candidate that changed both variables:

| Build | Python API | Cargo optimization |
|---|---|---|
| Baseline | CPython 3.14 version-specific API | fat LTO, one codegen unit |
| LTO candidate | CPython 3.14 version-specific API | thin LTO, 16 codegen units |
| ABI candidate | `abi3-py310` limited API | fat LTO, one codegen unit |
| Combined candidate | `abi3-py310` limited API | thin LTO, 16 codegen units |

### 9.1 Method

The controlled release-toolchain run used an Apple M4 (`arm64-apple-darwin`),
Rust 1.95.0, Maturin 1.14.1, and CPython 3.14.3. The ABI3 artifacts were built
against the Python 3.10 stable ABI and installed into the same CPython 3.14.3
used for the version-specific artifacts. Each cold build had an empty,
independent `CARGO_TARGET_DIR`; only the Cargo registry/download cache was
shared. Maturin stripped all four wheels. These local wall times are a relative
profile comparison, not a prediction of a particular GitHub runner.

Each wheel was installed into its own virtual environment outside the checkout.
Runtime cases were warmed once, then timed with nine `timeit.repeat` samples and
case-specific iteration counts. The complete four-variant order was interleaved
over three fresh processes; the table reports the median sample within each
process and then the median across those processes. Cases exercised the PyO3
boundary and each major current primitive: locale canonicalization, safe-eval
compilation, template parsing and formatting, small and 60 KB HTML transforms,
and catalog compilation/format/resolution. The 2 MB transform separately reused
`benchmark_html_transform.generate_large_html(11_000)` and took the median of
11 samples of 20 transforms. The ordinary iteration counts were 200,000 locale
calls; 20,000 safe-eval compilations; 10,000 small parses, formats, and HTML
transforms; 200 transforms of a 60 KB input; 2,000 catalog compilations; 50,000
catalog formats; and 30,000 catalog resolutions. Every callable was exercised
once before timing, all variants used identical inputs, and the normal package
tests plus isolated release-wheel smokes supplied the correctness gate.

### 9.2 Build and size result

| Variant | Cold build | Wheel | Native extension |
|---|---:|---:|---:|
| Fat LTO, version-specific API | 125.1 s | 5.25 MiB | 13.16 MiB |
| Thin LTO, version-specific API | 60.3 s | 5.62 MiB | 14.74 MiB |
| Fat LTO, ABI3 | 126.5 s | 5.25 MiB | 13.16 MiB |
| Thin LTO, ABI3 | 59.6 s | 5.62 MiB | 14.74 MiB |

The candidate profile halved this cold build but made the compressed wheel
about 7% larger and the unpacked extension about 12% larger. ABI3 itself was
effectively size- and build-neutral. Its release benefit is multiplicative:
one standard CPython wheel per OS/architecture replaces five version-specific
3.10-3.14 wheels, while free-threaded CPython 3.14 and PyPy retain their own
Linux wheels.

### 9.3 Runtime result

Representative version-specific-API medians isolate the Cargo profile change:

| Operation | Fat LTO | Thin candidate | Delta |
|---|---:|---:|---:|
| Locale canonicalization | 88 ns | 102 ns | +15.9% |
| Safe-eval compilation | 1.97 us | 2.03 us | +2.7% |
| Small template parse | 5.96 us | 7.65 us | +28.3% |
| Small template format | 55.8 us | 66.0 us | +18.3% |
| Small HTML transform | 0.765 us | 0.774 us | +1.1% |
| 60 KB HTML transform | 0.415 ms | 0.420 ms | +1.2% |
| 2 MB HTML transform | 3.51 ms | 3.70 ms | +5.6% |
| Catalog compile | 18.1 us | 18.6 us | +2.9% |
| Catalog format | 0.532 us | 0.567 us | +6.5% |
| Catalog resolve | 0.719 us | 0.748 us | +4.0% |

The percentages on the smallest calls are large relative to nanosecond and
microsecond absolute costs, but they are repeatable and the profile is not
performance-neutral. This comparison is deliberately named the *profile*
result: changing both LTO mode and codegen-unit count means it does not claim
which compiler knob owns each regression.

Holding fat LTO constant isolates ABI3. On CPython 3.14 the ordinary primitive
cases ranged from -0.3% to +2.2%; the 2 MB transform was +0.6%. Catalog compile,
format, and resolve were +1.6%, -0.7%, and +3.6% respectively, with the largest
absolute difference about 26 ns per call. No material ABI3 regression was
observed for Citry's current surface. A separate oldest-interpreter check on
CPython 3.10, using the same two fat-LTO variants with the repository's
development nightly, ranged from -0.9% to +2.1%. Future bindings that require a
newer limited API must requalify the decision.

### 9.4 Decision

- **Keep `abi3-py310`.** It removes most duplicate CPython builds with no
  material measured runtime or per-artifact size cost. The release still emits
  version-specific free-threaded CPython 3.14 and PyPy wheels, and installs the
  ABI3 artifact on every supported GIL-enabled CPython during qualification.
- **Keep fat LTO and one codegen unit for published bytes.** Build-once
  qualification, ABI3, parallel PyEmscripten reproducibility builds, caching,
  and build-owned smoke tests address release latency without spending user
  runtime. The `release-wheel` profile differs from the profiler-oriented
  `release` profile only by omitting debug information from the stripped
  distribution build.
- **Do not infer that ABI3 is always free.** CPython's limited API can replace
  version-specific macros/inlining with stable calls, and PyO3 cannot use every
  exact-interpreter optimization. Re-run this four-way method when the binding
  surface, minimum Python version, PyO3 version, or a performance-sensitive
  boundary changes.

## 10. Beta feature-set regression audit (2026-08-20)

The refreshed cross-engine benchmark made the performance regression visible,
then a bounded same-machine comparison separated new output from inefficient
runtime work. The comparison used the unchanged large scenario at historical
commit `86f162b1` and at the pre-optimization checkout, with both running under CPython
3.14.3 and the same release-built Citry Core 1.5.0. The historical checkout
produced 204,782 bytes and a 14.43 ms steady render, closely reproducing its
published 14.52 ms result. The pre-optimization checkout produced 986,021 bytes
and took 85.30 ms steady; its fresh-process table recorded 87.31 ms for the
second render.

| Phase | June runtime | Pre-optimization runtime | Added time |
|---|---:|---:|---:|
| Component-tree render, including nested hook serialization | 14.00 ms | 70.75 ms | 56.75 ms |
| Root serialization | 0.43 ms | 14.26 ms | 13.83 ms |
| Total | 14.43 ms | 85.30 ms | 70.87 ms |

The same five-render cProfile comparison counted 0.99 million calls in the
June runtime and 8.30 million now. cProfile inflates absolute times, so the
wall-clock probes below instrumented the current runtime without using its
timings as the cross-engine result.

### 10.1 What the added time is doing

**Ownership capture and replacement are the largest target.** Distinct
instrumented operations accounted for roughly 29 ms per render: slot-region
capture (9.0 ms), seven `selected_region_ids()` calls (7.9 ms), one
`retire_component_output()` pass (5.3 ms), and source-location, instance, and
invocation recording (6.9 ms combined). This is a lower bound because it omits
several smaller ownership operations. The remaining selection calls still
walk the complete accumulated physical-region result set, and replacement
retirement repeatedly scans graph collections to find a closure. Those are
data-structure/algorithm costs, not the unavoidable price of retaining keyed
identity.

**Static dependency work is repeated per instance.** The page made 103 static
component-JavaScript scans and 164 class-script preparation/cache checks per
render. The source is class-level and unchanged between instances. A controlled
in-process cache of the derived class asset reduced the median by about 5-7 ms
without changing the output size. The durable fix needs exact-class caching,
file-reset/unregistration invalidation, and one shared-cache repair check per
class/render rather than per instance.

**The client manifest has a real cost, with avoidable work inside it.**
`prepare_ownership_manifest()` took about 8.4 ms, including about 2.7 ms in
canonical JSON/revision serialization. A diagnostic run that suppressed the
client manifest reduced the total by about 12 ms, but also removed required
client output and is not a valid product optimization. The useful targets are
fewer graph walks and avoiding serializing the same canonical structure once
for its revision and again for emission.

**Dormant extensions are not free enough.** Every component eagerly receives
Cache, Dependencies, Events, and I18n config objects. Even though this scenario
uses no translations, the i18n data hook still checks component/project
messages on all 342 instances, and generic `c-bind` destinations retain the
dynamic `$c-tr` capture path. Timed in isolation, the dormant i18n hook cost
about 1.6 ms, i18n config construction about 0.9 ms, and the conservative
attribute-binding wrapper about 3 ms. Other config construction, Events
touchpoints, and cache lookups add smaller amounts. These paths need a true
unconfigured fast path while preserving zero-configuration component-owned
messages and dynamic binding correctness.

### 10.2 What does not explain it

The larger response is not the main server-time cause. Setting a mounted prefix
changed the current response from 986,021 bytes of inline output to 232,638
bytes of URL-based output, but the median remained about 85.3 ms and the
render/serialize split remained about 71.7 / 14.5 ms. The same scenario also
renders the same 342 component instances on the historical and current
checkouts. The regression is therefore in runtime work per node/component and
in graph-wide passes, not a sixfold increase in scenario size.

### 10.3 Implemented optimization order

1. Ownership selection memoizes overlapping region subtrees, no-op generator
   checkpoints skip selection, ancestor closure uses queues, and replacement
   retirement builds region/fill/receiver indexes once per pass.
2. Exact component classes cache their derived JS/CSS object, serialized bytes,
   hash, and `$component` fact. File reset invalidates that state; serialization
   still repairs missing or stale shared-cache entries, but ordinary instances
   no longer repeat the work.
3. Dormant i18n configs allocate usage and binding collectors lazily, a current
   empty catalog exits before component source checks, and ordinary `c-bind`
   nodes use the normal attribute renderer while still rejecting an unconsumed
   dynamic `$c-tr` key.
4. Manifest assembly hashes and retains one canonical unsigned traversal,
   while a C-backed mutation guard preserves precise fail-closed revalidation
   for externally changed artifact dictionaries. Required/preparation analysis
   also shares serialization-scoped Alpine scan results.
5. The remaining node walk was re-profiled only after these changes, then the
   complete fresh-process comparison was rerun.

### 10.4 Outcome

The bounded five-process checkpoints moved the large repeat median as follows:

| Kept change | Repeat median |
|---|---:|
| Refreshed beta baseline | 87.31 ms |
| Memoized ownership selection and no-op generator guard | 77.88 ms |
| Exact-class asset derivation | 70.83 ms |
| Dormant i18n lifecycle | 69.23 ms |
| Single-pass manifest signing/serialization | 67.31 ms |
| Dormant ordinary-spread renderer | 64.93 ms |
| Indexed replacement retirement | 61.84 ms |

A separate 11-process check put serialization-scoped Alpine reuse at 61.12 ms.
The final authoritative cross-engine rerun, measured independently across all
cells, recorded 62.60 ms. That is 28% below 87.31 ms, with byte-identical
986,021-byte output. First render improved from 122.27 ms to 98.20 ms. Against
django-components, the large repeat ratio moved from 1.76x to 1.21x; the small
repeat result moved from 258.8 us to 216.8 us, effectively even with
django-components' 211.6 us in that run.

The final five-render cProfile counted 4.13 million calls instead of the
pre-optimization 8.30 million. Its remaining inclusive hotspots are the
ordinary attribute resolve/format walk, source and slot ownership capture,
direct-Alpine detection for client-active frames, and the one unavoidable
canonical traversal used to sign the ownership manifest. Those are the next
places to investigate; this pass does not weaken their validation or remove
client output to improve a number.

### 10.5 Rust boundaries and allocation pass

The next pass kept the mutable render/ownership graph in Python but moved two
closed, value-oriented operations across the existing native boundary:

1. `scan_alpine_html()` lexes multiple fragments in Rust and recognizes real
   `x-*`, `@*`, and `:*` attributes rather than matching attribute-shaped text.
   Region candidates cross the boundary as one batch and share the existing
   serialization-scoped cache.
2. The strict client-graph encoder and SHA-256 revision run in Rust. It retains
   the wire contract's UTF-16 key order, decoded-integer rules, lone-surrogate
   behavior, safe-integer bounds, and rejection of non-JSON Python containers.
3. Ownership source spans cache their UTF-8-to-Python offsets, immutable record
   transitions use record-specific constructors instead of generic
   `dataclasses.replace()`, and each component instance snapshots its stable
   class ID once.
4. Compiler-validated element attributes use a flat item merge. Static regions
   skip dynamic key validation and unused extension dispatch, while `c-bind`
   retains runtime name, Events, i18n, class/style, and duplicate-key checks
   without allocating one temporary mapping per contribution.

The ownership graph itself did **not** move to Rust. Its hot operations mutate
Python render objects, extension contexts, slots, and component instances; a
native owner would require frequent object crossings or a second graph that
must remain synchronized. The closed canonicalization and HTML-scanning
boundaries avoid that synchronization cost. A future compiler-owned Alpine
semantic bit could eliminate even the fallback scan, but after batching the
measured scan was about 0.55 ms per large render, so it is no longer a leading
target.

Correctness was checked three ways: the Rust and reference Python canonical
encoders produced identical JSON and revisions for the protocol corpus and
Unicode edge cases; one settled tree serialized through both paths produced
exactly the same bytes; and the large scenario remained exactly 986,021 bytes.
The final `benchmarks/compare.py --size lg --rounds 5` run used fresh processes
for every cell and measured 82.76 ms first render and 48.67 ms warm, down from
98.20 / 62.60 ms. In that run Citry's warm result was about 4% faster than
django-components (48.67 vs 50.64 ms).

The final five-render cProfile counted 2.81 million calls. Its inclusive
groups are shown below only as a priority map: parent and child rows overlap,
and profiling inflates the absolute values, so the times must not be added or
compared with the wall-clock benchmark.

| Inclusive group (five profiled renders) | Calls | cProfile time |
|---|---:|---:|
| settle complete render tree | 10/5 | 640 ms |
| render one component | 1,710/1,700 | 500 ms |
| render component bodies | 5,110/1,690 | 382 ms |
| ordinary element-attribute node | 2,825 | 177 ms |
| dormant i18n attribute wrapper (includes ordinary node) | 2,160 | 140 ms |
| slot node and call/capture chain | 1,370/1,245 | 114 / 83 / 76 ms |
| invocation-region settlement | 1,715 | 106 ms |
| component-node render/input resolution | 1,695 | 82 / 38 ms |
| attribute resolve/format | 2,825 | 78 / 73 ms |
| dynamic-spread resolution | 2,160 | 56 ms |
| root serialization | 30 internal calls | 55 ms |
| ownership selected-region traversal | 10 | 35 ms |

The next meaningful server-side work is therefore structural: reduce the
number of Python node/hook/slot calls or precompile larger static regions. More
micro-optimizing manifest scans is unlikely to move the total materially.

### 10.6 Repeated-object and traversal follow-up (2026-08-21)

The next profile tested whether the remaining high `isinstance()` count meant
the runtime kept classifying the same objects. In the final five-render rerun,
59.7% of instrumented calls repeated the same call-site/object pair, but only
3.0% of object/type pairs crossed render boundaries. A general cache was the
wrong shape: direct `isinstance()` measured about 30.7 ns, a type-keyed LRU about
37.4 ns, and an object/type dictionary about 83.5 ns. The retained changes
therefore cache or skip only operations with stronger, domain-specific reuse:

1. Exact built-in `str` HTML attribute names use a bounded 512-entry validity
   cache. String subclasses stay on the uncached path, so user-defined hashing
   and equality never enter shared state and contextual errors remain fresh.
2. Render replacement computes selected render IDs, object identities, and
   physical-region IDs once, then reuses them for both retirement decisions.
3. `ElementAttrsNode` records whether a spread, raw Events binding, or compiled
   State binding can require the built-in Events runtime hook. Proven-inert
   elements skip only that built-in subscriber; third-party
   `on_attrs_resolved` hooks still receive every dynamic element.
4. Manifest detection and preparation share a lazy, serialization-epoch tree
   index. Detection retains its early exit and preparation resumes the same
   traversal. Serializations that cannot emit or inspect ownership metadata do
   not build the index. An eager prototype was rejected: completing the full
   index before the query moved the warm median to 52.22 ms.
5. Safe-eval attribute policy bypasses internal-frame/callable classification
   for exact ordinary built-in values after the underscore check. Subclasses
   and Python's function, method, type, code, traceback, frame, generator,
   coroutine, and async-generator objects retain the full policy.
6. The two transparent physical-region wrapper classes share one internal
   marker base. Unwrapping, serialization, ownership, slot, node, and cache
   traversals now perform one marker check instead of dispatching over a tuple
   of the two concrete classes. The wrappers, mutable `.part` contract, and
   emitted ownership-boundary comments remain unchanged.

The five-render profile fell from about 2.80 million calls before this batch to
2.41 million. Root serialization fell from 52 ms to 46 ms of overlapping
cProfile time, while ordinary attribute-node work fell from 171 ms to 145 ms.
The marker-base change did not reduce calls, but moved `isinstance()` self time
from 26 to 24 ms and physical unwrapping cumulative time from 9 to 7 ms across
five profiled renders. An 11-process Citry-only check measured 77.93 / 45.82 ms
versus the preceding nine-process 78.93 / 46.11 ms, a modest 0.6% warm change.
The complete cross-engine rerun landed at 77.88 ms first render and 45.78 ms
warm. Its larger difference from the preceding 81.66 / 48.07 ms table includes
fresh-process run variance and is not attributed to the marker change alone.
Output size stayed 986,021 bytes, and the complete non-E2E suite passed: 7,680
passed, 5 skipped, 1 expected failure, and 1,171 deselected.

### 10.7 Readable ownership-comment aliases (2026-08-21)

Ownership comments now carry the first eight hexadecimal characters of the
manifest revision. The complete 64-character SHA remains in the manifest,
Events and dependency links, public browser API, replay ledger, and internal
graph maps. The browser maps the short alias to one complete live or
provisional revision. A second complete revision with the same active alias is
rejected before publication; abort, discard, and inactive-revision pruning
release the reservation.

This is a readability decision, not a performance optimization. The exact
large benchmark response is now 980,643 raw bytes, 172,980 gzip bytes, and
138,052 Brotli bytes. Expanding its 148 `citry:g1` markers back to full
revisions while keeping the same runtime produces 988,931 raw, 173,240 gzip,
and 138,152 Brotli bytes. The aliases therefore remove 8,288 raw bytes, 260
gzip bytes, and 100 Brotli bytes from that otherwise identical response. The
alias lookup and collision guard add browser-runtime code, which is why this
controlled marker comparison is more useful than attributing the difference
from the earlier 986,021-byte response entirely to shorter comments.

The producer/parser unit tests lock the exact eight-character grammar, the
browser corpus uses two valid revisions with the same `5ddad84c` prefix to
prove atomic collision rejection and release after abort, and the range plus
Events suites prove canonical and mirrored placement markers continue to
preserve nested-island identity. The raw response used for inspection was
generated with the large Citry benchmark scenario's
`render(gen_render_data())` entrypoint.

### 10.8 Render allocation, specialization, and pure-body pass (2026-08-21)

The next pass attacked work below the graph-wide algorithms rather than
weakening ownership output:

1. Recursive local walker closures in deferred scanning and serialization
   became module-level stack helpers. Template slot content now weakly refers
   to its `Slot`, physical-region results are weak values, and slot-object fill
   lookup uses weak keys. This removed the retained closure/slot/render cycles
   from the ordinary path. Physical-region selection roots stay strong until
   the outer render settles, then clear; a root component computes
   `root is self` without storing a self-reference. A representative render
   fell from 20,766 to 277 cyclic objects collected, with no render,
   component, ownership, slot, or region objects among the remainder.
2. `ConstBodyCache` lets weakref callbacks set one cheap dirty bit and prunes
   dead component classes on the next ordinary cache operation. It does not
   release arbitrary objects from a garbage-collector callback.
3. Compiler-created `ComponentNode` instances record whether their inputs are
   only fixed ordinary kwargs. In this scenario 324 of 339 nodes take the
   direct resolver rather than constructing pending spread/binding maps and
   closures. Dynamic, client-bound, spread, and `<c-element>` calls retain the
   generic path.
4. Ordinary attribute spreads no longer invoke the built-in Events resolver
   merely because a spread exists; the resolved runtime keys decide whether it
   is an Events candidate. `$c-props` is not rescanned and applied twice when
   no extension transformed the attributes. Third-party hooks still receive
   every element they subscribe to.
5. The built-in i18n completion hook now exits before allocating a hook context
   when that component never activated i18n bindings. Recursive body walkers,
   weak ownership maps, direct component inputs, and these attr/hook gates
   brought the five-render cProfile from 2.41 million calls to 2.15 million.
6. Explicit `pure = True` adds the bounded render-local body plan described in
   [`component_constness.md`](component_constness.md#16-explicit-pure-component-body-caching-2026-08-21).
   The benchmark marks its repeated `HeroIcon` and `ProjectOutputBadge`
   classes pure; their qualified occurrences save roughly 0.4-0.8 ms while
   preserving byte-identical output and fresh IDs.

The final 11-process Citry-only check measured 76.53 ms first render and
39.38 ms warm, compared with the preceding 77.88 / 45.78 ms table. The warm
result is about 14% lower. A complete five-process cross-engine rerun measured
Citry at 76.59 / 38.65 ms versus django-components at 68.39 / 50.65 ms. Output
remained exactly 980,643 bytes. The new 39 ms level is substantial progress but
still far above June's 14 ms: the profile is now dominated by live body-node,
element-attribute, slot-region, and component transaction work, not one hidden
graph-wide scan.

### 10.9 Remaining transaction cost and native-boundary probes (2026-08-21)

A fresh five-render cProfile after section 10.8 counted 2,150,202 calls
(2,079,667 primitive). Its absolute 531 ms is profiler-inflated, but the call
shape is useful: each real render executes 342 components, 339 component nodes,
274 slot nodes, 505 element-attribute nodes, about 942 body walks over 3,863
items, and about 2,441 expression evaluations. Of those body items, 2,264 are
strings and 1,599 are live node objects. The remaining cost is therefore spread
across thousands of small Python transactions rather than one new dominant
function.

An unprofiled 300-render phase probe on the same checkout measured a 40.84 ms
median total in that process: 37.43 ms settling the tree (including the nested
serializations selected by component hooks) and 3.42 ms for the final root
serialization. This is a diagnostic split, not a replacement for the
fresh-process 38.65 ms result above. It says that another serializer rewrite
cannot recover the missing ~25 ms by itself.

#### Ownership is large, but moving the current object graph verbatim is not the answer

One settled benchmark render captured 3,182 records:

| Record family | Captured | Survives selected output |
|---|---:|---:|
| Source locations | 1,081 | not state-bearing |
| Component invocations | 339 | 43 |
| Logical instances | 342 | 46 |
| Logical fills | 468 | 57 |
| Physical regions | 274 | 30 |
| Init ancestry | 339 | 43 |
| Render queue | 339 | 43 settled |

Those 1,081 source records refer to only 115 distinct compiled sites, a 9.4x
occurrence-to-site ratio. `tracemalloc`, while retaining the settled render,
attributed about 840 KiB and 11,828 live allocation blocks to `ownership.py`
out of 1.49 MiB traced in total. Most state-bearing records are later retired
because hooks select or flatten another result. The first design target should
therefore be less materialization, not a line-for-line Rust translation of
frozen Python dataclasses.

A useful ownership transaction design has three layers:

1. The compiled component body interns immutable source-site metadata once.
   Runtime events carry a small site integer instead of rebuilding a source
   record and its strings for every occurrence.
2. Each component output owns an append-only journal segment. Committing the
   ordinary result keeps the segment; selecting an unrelated replacement can
   discard a whole segment or mark one range dead. Only the uncommon
   replacement that preserves selected descendants needs the current closure
   analysis.
3. After that contract is proven in Python, a native arena can store compact
   record structs, indexes, state bits, and adjacency lists. Python wrappers
   retain only numeric render/region handles. One native query receives the
   selected handles and performs ancestor closure or retirement; one final
   export produces the manifest data. The native owner must never retain a
   parallel mirror of mutable `CitryRender`, `Slot`, component, or extension
   objects.

A throwaway C-extension probe tested whether per-event calls make that boundary
impractical. Appending 3,182 five-integer events into a native vector took
0.137 ms; a Python tuple journal took 0.174 ms, Python structure-of-arrays took
0.199 ms, and constructing a slotted frozen dataclass plus an index took
0.886 ms. This synthetic result does not predict the graph's total saving: it
shows that a compact integer boundary is affordable and that replacing record
construction alone is worth less than a millisecond. Site interning,
transactional discard, and native relation processing are what can make the
larger difference.

#### A native attribute fast path is real but deliberately small

The same render sent 535 resolved attribute maps to the final formatter. Of
1,490 values, 1,485 were exact `str`, `bool`, `int`, `float`, or `None`; only
five used the general proxy/object path. A temporary 50 KiB C extension walked
the real maps, retained current escaping and boolean rules, and fell back on
unsupported values. It verified exact formatted strings for 530 qualifying
maps.

| Formatter probe | Median per render's qualifying maps |
|---|---:|
| Current Python loop with MarkupSafe's C escaper | 0.609 ms |
| Native loop, plain string result | 0.200 ms |
| Native loop plus `Markup` result | 0.278 ms |

Interleaving the formatter in the complete render moved the median from 38.47
to 37.83 ms and the mean from 38.64 to 38.09 ms. This supports a production
exact-builtins fast path with a Python fallback, but caps its expected gain at
roughly 0.5-0.7 ms on this page. The production implementation should live in
the existing Rust/PyO3 `citry-core` extension and be measured in its release
`abi3` build; a separate C module would duplicate native build, PyPy, and
PyEmscripten work for no architectural benefit.

For this particular closed loop, the Stable ABI was not a material penalty in
the probe. Recompiling the same module with `Py_LIMITED_API=0x030A0000` and
using only the available call API moved a 500-map batch from 0.210 to 0.212 ms
(about 0.9%). That result applies only to this dictionary/Unicode loop; it does
not overturn the separate release-wheel ABI benchmarks or remove the need to
test the eventual PyO3 implementation.

#### The larger route is a compiled render plan

The benchmark has 342 instances across 37 classes, but only 121 distinct
class/template-data shapes in one render. There are 221 repeated shapes:
`Button` alone has 114 occurrences over 16 shapes, while several form, tag,
attachment, and icon classes repeat heavily. The initial pure-body memo can use
only 40 safe hits because it deliberately refuses child, slot, and ownership
effects.

The next architectural prototype should compile the post-extension node tree
into a render plan with larger operations:

- merge adjacent static output and prebind node functions, resolved attribute
  identities, extension subscribers, component targets, and ownership site IDs;
- evaluate a run of ordinary expressions in generated Python code instead of
  entering one node method and error wrapper per expression;
- represent child components, slots, and ownership effects as explicit holes
  or transactions that still create fresh instances, IDs, hooks, and records;
- for an explicitly pure class, memoize the immutable plan result around those
  live holes, rather than rejecting the complete occurrence merely because it
  contains a child;
- send only closed scalar batches (attributes, escaping, static text assembly,
  compact ownership relations) to Rust. Arbitrary Python expressions and
  lifecycle hooks remain in Python.

An opcode interpreter written in Python is unlikely to help: it replaces node
method dispatch with another Python dispatch loop. Generated Python for dynamic
expressions plus native execution of closed batches is the boundary to test.
The acceptance sequence is: byte/graph equivalence corpus, a count of removed
node and ownership transactions, in-process A/B, fresh-process first/warm
medians, then an `abi3` versus version-specific native profile. Do not infer a
win from fewer source lines or from a microbenchmark alone.

Compiling the current modules wholesale with Cython or mypyc is a weaker first
experiment. Their hot paths are dominated by dynamic component subclasses,
metaclasses, arbitrary mappings, generators, extension callbacks, and calls
between modules—the exact places where ahead-of-time Python compilers retain
boxed operations or require semantic restrictions. A small typed transaction
kernel could be a useful mypyc comparison, but Rust already owns Citry's native
distribution and supports the browser wheel. Keep the Python implementation as
the reference/fallback and move only a closed, measured contract.

### 10.10 Highest-value follow-up results (2026-08-21)

The section 10.9 proposals were tested as bounded prototypes before choosing
production code. Three changes survived that test.

First, each `OwnershipGraph` now shares immutable source-site metadata across
executions of the same compiled span. The 1,081 occurrence records still have
fresh IDs, owners, order, and mapping positions, but point at 115 site objects
for origin, source, spans, line, and column. An alternating 30-pair in-process
A/B measured a 0.539 ms median saving from avoiding repeated UTF-8 span
conversion. A shallow object-size model measured about 95,864 fewer retained
bytes from the smaller occurrence records and shared character-span tuples.
That is not a complete heap measurement, but it establishes both the direction
and the approximate scale.

Second, ownership retirement uses capture-order ranges for records created by
one hook attempt. Replacing component output also builds relation indexes
lazily, only when replacement asks for ancestor or descendant closure. Removing
those indexes was the falsifier: `retire_component_output` rose from about 1 ms
to about 6 ms per render under cProfile, and an 11-process warm median rose to
45.65 ms. Restoring them returned the warm median to 38.75 ms. Building all
indexes costs about 0.6 profiler-ms per render and avoids repeated whole-journal
fixed-point scans.

Third, a pure-body plan now keeps child, slot, ownership, and i18n work as live
holes. Safe expression or element results around those holes can still be
reused. Focused tests execute the stable sibling expression once while proving
that two child components or two slot fills execute independently. Force-marking
additional classes in the large page did not produce a clear aggregate win:
key freezing offset the small sibling expressions available there. The feature
is retained for components with measurably expensive safe work, not enabled on
container classes by default.

The following prototypes did not survive:

- Generating one unrolled Python function per current body saved about 0.21 ms
  in an interleaved run, within noise and far below its added compiler surface.
- A production-shaped PyO3 attribute formatter reduced the 500 eligible maps
  from about 0.345 ms to 0.247 ms. Its roughly 0.10 ms ceiling is much smaller
  than the earlier raw C probe, and complete renders were neutral or slower.
- Eagerly indexing every physical render object made the render slower because
  recording roughly 1,289 objects cost more than the one late scan it removed.
- A preflight for render trees owned by a different ownership graph did not
  fire in the benchmark: hook replacement selects from the active graph.

The final five-render profile counted 2,176,007 calls (2,105,437 primitive) in
0.502 profiler-seconds:

| Operation | Calls in five renders | Self / cumulative profiler time |
|---|---:|---:|
| `isinstance` | 421,665 | 22 / 32 ms |
| render one component | 1,710 | 15 / 386 ms |
| walk a body | 4,635 | 10 / 267 ms |
| physical-region containment | 23,005 | 9 / 17 ms |
| capture a source occurrence | 5,405 | 8 / 15 ms |
| retire replaced component output | 5 | 5 / 15 ms |
| build replacement relation indexes | 5 | 2 / 3 ms |
| freeze pure-body keys | 5,550 | 3 / 6 ms |

An 11-process Citry-only check measured 76.97 ms first and 38.75 ms warm,
with the same 980,643-byte output. This is effectively the section 10.8
76.59 / 38.65 level, while using less source-location memory and allowing
safe pure work around live children and slots. The simple compiled-plan and
native-scalar routes do not explain the remaining gap to June. Future native
ownership work is justified only as one compact journal plus closure/export
queries, not as a translation of the current Python object graph.

### 10.11 Ideas to take upstream to Python (2026-08-21)

This list concerns CPython and Python's standard APIs. It is separate from
adding more native code to Citry. The profile is useful as a large framework
workload, but one project is not enough evidence for a language change.

#### `isinstance` needs a workload contribution, not a new general proposal

The raw count first suggested specializing repeated type checks. Current
CPython already emits a dedicated `CALL_ISINSTANCE` specialization, visible in
the generated [opcode metadata](https://github.com/python/cpython/blob/main/Lib/_opcode_metadata.py).
The useful upstream step is to run Citry on a specialization-stats build and
classify misses: exact type, tuple of types, abstract base class, or custom
metaclass. If one common stable case repeatedly deoptimizes, a focused
interpreter PR plus a `pyperformance`-style benchmark is appropriate. A new
PEP or a Python-level type-test memo is not.

#### Make the Unicode writer usable from stable extension ABIs

Python 3.14 added the public [`PyUnicodeWriter`](https://docs.python.org/3.14/c-api/unicode.html#pyunicodewriter)
API, but its entries are not marked as part of the Stable ABI. Extension
authors targeting `abi3` therefore still fall back to lists, joins, or repeated
public calls for incremental string assembly. A concrete C API proposal would
make an opaque writer available through a future Limited/Stable ABI, with a
fallback for older runtimes. The draft [PEP 809 interface mechanism](https://peps.python.org/pep-0809/)
is one possible delivery path. This starts as a C API working-group issue and
benchmarked reference patch, not necessarily a language PEP.

Citry's actual attribute loop is evidence about ergonomics rather than a large
speed claim: its production-shaped native ceiling was only about 0.10 ms per
render. A useful upstream case should add serializers, template engines, and
protocol builders that assemble much larger strings.

#### Add a scoped bulk update for context variables

Python 3.14 lets one [`ContextVar` token act as a context manager](https://docs.python.org/3/library/contextvars.html#contextvars.Token),
but setting several framework variables still creates and unwinds one token
per variable or uses nested generator-based context managers. Five profiled
renders made 8,815 `ContextVar.set`/`reset` pairs and entered 10,560 generated
context managers. A possible standard API is a scoped bulk update that accepts
`ContextVar`/value pairs, restores them in reverse order, and rolls back a
partial enter if allocation fails.

A pure Python convenience helper would not remove token and frame overhead.
The performance case needs a C implementation, async/task-switching tests, and
evidence from tracing, logging, web, and dependency-injection frameworks. This
is likely a `contextvars` API discussion followed by a CPython PR; it becomes a
PEP only if atomicity or cross-implementation semantics require a new language
contract.

#### Expose a safe mutation guard to stable-ABI extensions

[PEP 509](https://peps.python.org/pep-0509/) deliberately kept dictionary
versions private, and Python 3.14's
[`PyDict_AddWatcher`](https://docs.python.org/3.14/c-api/dict.html#c.PyDict_AddWatcher)
family is public but not marked as Stable ABI. Version-based caches in an
`abi3` extension must either repeat lookups, use callbacks tied to CPython's
full API, or make an unsafe assumption about a live mapping. A narrow opaque
mutation-token or watcher interface for exact dictionaries could let an
extension validate a cached lookup without exposing object layout or a Python
`dict.__version__` property. Free-threaded callback lifetime and synchronization
are the hard part, so this belongs with the C API and free-threading groups.

#### Follow immutable-container work instead of proposing deep freeze again

Python 3.15 already accepted [`frozendict`](https://peps.python.org/pep-0814/),
and draft [PEP 841](https://peps.python.org/pep-0841/) proposes syntax that can
constant-fold frozen mappings and sets in Python 3.16. These can reduce setup
for shallow immutable configuration and cache inputs. They do not solve
Citry's recursive cache key, whose values may contain lists, dataclasses,
application objects, or cycles.

A general deep-freeze or universal cache-key protocol is not a good fresh PEP
from this evidence. [PEP 351](https://peps.python.org/pep-0351/) already shows
the semantic difficulty and was rejected. Citry should first collect repeated
implementations and compatible semantics across libraries; until then, a
project-local fail-closed freezer is more honest than standardizing one answer.
