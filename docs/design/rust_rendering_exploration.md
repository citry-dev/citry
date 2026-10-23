# Moving server rendering to Rust: where the time goes and what to try first

> **This is the research record, not the description of what ships.** It
> keeps the measurements, reasoning and rejected options from the research
> that led to Citry's native render path (October 2026). What ships, when
> Citry uses it and how it fails is in
> [`native_render.md`](native_render.md). The research code was never
> merged, and its raw timing data was not kept, so this note is the only
> record of what was built and measured.
>
> Words this note uses for that later work:
> - *Production* means the five pull requests that rebuilt the research
>   levels for release: level A shipped in
>   [#265](https://github.com/citry-dev/citry/pull/265), and B1, C1, C2
>   and B2 are in #266-#269. Each level's own timing, measured again on
>   release wheels, is in its pull request and in its row of the decision
>   ledger in
>   [`performance_architecture_experiments.md`](performance_architecture_experiments.md#decision-ledger)
>   (the table of kept and rejected performance changes; the B1-B2 rows
>   land with their pull requests). The *production
>   plan* and *production review* are the plan and the independent
>   reviews of those pull requests.
> - *The written Stage 2 plan* (or "the design" in the Stage 2 sections)
>   is the research's own plan for Stage 2. It was not kept; the bars it
>   set are quoted here.
> - *Today* in a section means the `origin/main` commit that section
>   names, and file and line references point at that commit.

This research note asks one question. Suppose Citry moved most of its
server-side rendering from Python to Rust, while user code (callbacks,
`template_data()`, values Rust cannot read as plain data) stayed in Python.
Would the server time of the project-board benchmark page (called "the board"
below) fall to roughly one third? That is the hypothesis in
[issue #144](https://github.com/citry-dev/citry/issues/144), item "Native Rust
rendering architecture". The note is not an implementation plan. Sections 1
to 4 were first written from source reading and earlier recorded
measurements. The Stage 0 measurements in the "Stage 0 results" section
were taken afterwards, on 2026-10-20, and replace the paper estimates where
they disagree.

## Short answer

This answer reflects the Stage 0, Stage 1 and Stage 2 measurements. Section 4 describes three
architectures. **A** is a Rust producer for the board's repeated rows,
**B** adds a Rust serializer for the finished page, and **C** is a native
scheduler that calls Python only for user code. "Warm" means a server process
that has already rendered the page once, so templates are compiled.

- **One third is not reached on present evidence, even with C.**
  - 21% of warm server time at 1,400 rows stays put, out of 110.5 ms:
    - user code and schemas (6.9 ms) stay in Python;
    - about half of row setup (5.1 ms) stays in Python: id minting, the
      admission check (the test that lets a row skip creating a component
      instance) and the callback order;
    - the hydration HTML writer (11.1 ms) is already Rust.
  - For the row evaluation it measured, Rust took 7.4% of the time Citry's
    Python takes, reading the row through the CPython C API: 1.2 ms against
    16.4 ms for 1,400 rows, with byte-identical output. That is far better
    than the 56-85% the paper estimate borrowed from other engines.
  - That ratio covers about 19 ms of the work. With one stated rule set for
    the rest (section "Projections from the measurements"), C saves 36-60 ms
    (33-54%), leaving 51-74 ms. That is 46-67% of today's warm time. Stage 1
    supports the middle of that range at best: the ratio implied by the
    integrated prototype puts C near the less favorable end (see "What
    Stage 1 says about the hypothesis").
  - Reaching one third would also need Rust to remove about 14 ms of work
    that CPython already does in C (placement digests, `json.dumps`, a JSON
    round trip), or fewer Python objects to remove a similar share of the
    17 ms of garbage-collection pauses. Stage 1 measured part of the second:
    its rows made full collections rarer, cutting about 6-9 ms per render on
    average.
- **With every Stage 2 level added, warm time is about 0.50 of
  `origin/main`'s** (0.54 with collector pauses taken out). Stage 2
  (section "Stage 2 results") measured on `origin/main` at `92e1cf5a9`,
  each step against the one below: the Python cuts 8.2%, A 27.5%, B1 in
  Rust 11.8%, C1 3.6%, C2 6.5% and B2 4.5%. C1's Rust arm is no faster
  than its Python arm, so C1 stays in Python. Whether B1 stays in Rust or
  in Python depends on the figure used (section "Stage 2 results"); the
  maintainer kept it in Rust. First load at 1,400 rows
  falls to 0.67 and second load to 0.48. These ratios count the Python
  cuts as part of the stack. Production measured the same stack against a
  base that already has the cuts and got about 0.55 (0.72 first load,
  0.53 second load), which matches this research once the base is the
  same (55.1 / 100.4 = 0.55).
- **Architecture A measured a 21-26% cut on top of the Python-only cuts.**
  The Stage 1 prototype took warm render plus serialize at 1,400 rows from
  103.7 to 77.2 ms (its second version), with byte-identical output in every
  output kind tested. The projection was 21-31 ms, and the measured saving
  is 26 ms. The Python-only cuts save 8.6% against `origin/main` on their
  own, so together warm time falls to about 0.68-0.72 of today's (ratios
  measured under different load). One third is still out of reach.
- **First load needs a second change.** The first request pays 42-47 ms of
  one-time work: compilation, first renders and memory warm-up, which
  rendering in Rust does not remove. With C alone, first-load prepare would
  land at about 62-77% of today (projected). A alone measured 14% off first
  load at 1,400 rows, against the cleaned-up Python. Adding compilation of the registered templates at
  startup (the "first-request warm-up" item in #144) would bring it to about
  38-58% (estimate).
- **The 0.6.0 release first-load step does not reproduce reliably.**
  Both release-harness runs that evening show about 196-199 ms of first-load
  server prepare at 1,400 rows. The same released wheels, served with plain
  HTTP requests in fresh processes, give 153.5-163.1 ms. That matches the Sep
  27 figure of 157.7 ms, so the code did not get slower. A recheck through
  the same harness gave 165.3 ms in its latency run (no step) and 207.9 ms in
  its qualification run, which was slow throughout. Each harness cell is a
  single page load, so the harness cannot tell the step from noise. Whether
  to rerun the 0.6.0 cohort is open (section 7).
- **Python-only changes are worth about 15-17% warm, with no Rust.**
  Freezing long-lived startup objects out of garbage collection
  (`gc.freeze()`) saved 8.6 ms, measured. A sweep of the render path for
  avoidable Python work found cuts that change no output; they measured
  -8.6% (about 12 ms) at 1,400 rows under load. These overlap with the Rust
  savings, because both remove the same Python work, so they do not add up.

Paths are relative to the repository root at `origin/main` (`c6bbc2413` when
the note was first written, `695bd3168` for the Stage 0 measurements,
`92e1cf5a9` for Stage 2). The raw timing data, the harness scripts and the
earlier benchmark runs that sections 1 to 4 cite lived only on the
maintainer's machine and were not kept. Where this note names a benchmark
run, the name only identifies which run a figure came from. "Unproven"
marks anything inferred rather than read or measured.

## Terms used in this note

- **Hydrate:** the browser's Vue attaches to HTML the server already wrote,
  instead of building the page itself. The board hydrates by default.
- **Occurrence:** one placement of a component in the rendered page. Each of
  the 1,400 board rows is one occurrence.
- **Manifest:** the JSON document the server sends with the page. It lists
  every occurrence with the values Vue needs to render and hydrate it.
- **Instance-free row:** an occurrence of a component declared with
  `simple = "vue"`. It renders without creating a Python component object,
  and keeps only its Vue state.
- **Plain data:** values whose types are exactly `dict`, `list`, `str`,
  `int`, `float`, `bool` or `None`. The scalar part of that set is read live on
  every row (`packages/py/citry/citry/_vue/leaf_program.py:2092`, `:2104-2120`).
  Registering a type with the `ComponentLike` ABC removes it from the set.
- **GIL and C API:** the GIL is CPython's global interpreter lock. A thread
  must hold it to touch Python objects. The C API is the set of functions
  CPython gives native code for reading Python objects.
- **Effect:** a call into user or extension code whose order or count is part
  of Citry's contract.
- **Admission check:** the per-row check that a class may still render
  without a Python instance, given the current extensions and settings.
- **Leaf program:** one Python object that evaluates a whole template body
  containing no component calls.
- **Placement digest:** a SHA-256 hash of a row's position and key, which
  gives the row its stable id in the manifest.
- **s, r and T:** s is the share of warm server time that cannot move
  (Python user code, or already Rust). r is what Rust spends on moved work,
  as a fraction of the Python time it replaces. T = s + r × (1 − s) is the
  warm time after the change, as a fraction of today's. Section 1 explains
  the formula.
- **Rusty Templates:** `django-rusty-templates`, a Rust implementation of the
  Django template language. The benchmark runs it on the same board.
- **Level:** one step of the native render work, built and timed on its own
  against the step below. Stage 1 built two versions of architecture A,
  called Level 1 and Level 2. From Stage 2 on, "A" means Stage 1's Level 2,
  and B1, C1, C2 and B2 are the steps built on it (see "Stage 2 results").
- **Arm:** one of the variants a timing comparison runs, such as Rust rows
  on or off.
- **Call run:** the components one `<c-for>` loop places at one call site.

## How the research measured

Anyone timing a new level can reuse this method. The timings of the
production levels used it too.

**The in-process harness.** A script imports the board app from
`benchmarks/web/apps/citry` exactly as the benchmark server does, so the
engine, extensions and settings match the published app. It times
`Page(...).render()` and `.serialize()` and runs in one of three modes, one
mode per fresh process:
- *total*: no wrappers, the control figure;
- *attr*: about 40 functions wrapped with counters that record each
  function's *exclusive* time (the time of wrapped functions it calls is
  left out), so every millisecond is counted once;
- *cold*: the same attribution for the first render of a fresh process.

Garbage-collection pauses are timed through `gc.callbacks`. Citry imports
its helpers by name, so the attr mode rebinds every module-level alias of
a wrapped function in the `citry` modules and in `app`, and times calls
into Rust through a proxy on `citry_core._rust`. Closures such as the
nested `transform_component` cannot be wrapped from outside, so the
research branch added timing counters inside `assemble_typed_render` that
do nothing unless the harness turns them on. Time a whole loop of rows as
one unit where possible: a wrapper that runs 1,400 times per page adds its
own cost to the per-row figures. The wrappers added about 5.6 ms per page
in Stage 0 and about 1.4 ms with level A on.

**Pairs of fresh processes.** Each comparison runs the two variants (the
two *arms*) in alternating fresh processes, 5 or 10 pairs, so slow drift on
the machine hits both arms. Each process renders 2 warm-up pages, then 11
timed ones, under normal garbage collection. Citry-core is always a
release build; the benchmark refuses a debug build of the Rust extension.
The research used editable release builds (`maturin develop --release`,
cp312) on `PYTHONPATH`; the production levels used installed release
wheels. So compare figures only within one of the two.

**Which figure decides.** Stages 0 and 1 reported the median of each
process's median. That figure jumps by about 12 ms depending on whether
the middle render of a process happens to include a full collection,
which costs 13-19 ms. In Stage 1, every process with Rust rows on had a
full collection in 6 of 11 renders, and every process with them off in 10
of 11. So a level worth 1-3 ms cannot be read from it.

Stage 2 decided with the *collection-free median*: for each process, the
median over the renders that ran no full collection, compared as a paired
difference within each pair. It leaves out the collector pauses a level
avoids, so it is the cautious figure. The mean over all renders is
reported beside it, because collector pauses are real server time.
- The collection-free median spreads 4.8 ms between processes at 1,400
  rows (sd 2.2 ms), but the paired difference has an sd of about 1.0 ms,
  because machine state moves both arms of a pair together. At 140 rows
  the sd is 0.25 ms between processes and 0.23 ms for the paired
  difference.
- A threshold is at least three standard errors of the median paired
  difference (about 1.25 × sd / √n): about 2 ms with 5 pairs, 1.5 ms with
  10. The 1.0 ms sd itself came from 5 pairs, so its 95% range is about
  0.6-2.9 ms. Estimate it again at the first timing step of a new level,
  and raise the thresholds if it is larger.
- A level is kept when the bytes match, the median paired difference
  reaches its threshold, and 5 of 5 or at least 8 of 10 pairs favor it.
  For a level whose true gain equals the threshold, each pair favors it
  about 93% of the time, so 10 of 10 happens only about half the time
  (0.93^10 ≈ 0.48), while 8 of 10 happens about 97% of the time. Stage
  1's rule, "every process with the change beats every process without
  it", fails even a real 3 ms gain, because the 4.8 ms spread between
  processes is larger.
- When an arm has fewer than 3 collection-free renders in a process,
  adding renders is impractical: an arm that collects on 10 of 11 renders
  would need about 33 renders per process for 3 clean ones. Rerun that
  comparison with the collector off in both arms; the normal run still
  gives the mean and the collection count. At 1,400 rows `origin/main`
  and the Python-cuts arm had only one such render per process. Their
  reruns were never done, so the mean decides those Stage 2 rows ("too
  few renders").

**Choosing between a Rust arm and its Python control.** B1 and C1 (the
levels described in "Stage 2 results") each had a Python arm that did the
same restructuring with no Rust. With 3 ms as the level's threshold and
2 ms as the smallest gain 5 pairs can see:
1. keep Rust when it reaches 3 ms against the level below and leads the
   Python arm by at least 2 ms over 10 pairs;
2. otherwise keep the Python arm when it reaches 2 ms;
3. otherwise keep Rust when it alone reaches 3 ms;
4. otherwise keep neither.

So Rust saving 3.5 ms and Python 2 ms keeps Python: 1.5 ms is too little to
justify the Rust code.

**Counting collections and objects.**
- Detect a full collection by `info["generation"] == 2` in the callback.
  Stage 1 used a pause above 8 ms as a stand-in; the generation is exact.
- Estimate allocations of objects the collector tracks as the total
  number of collections of every generation times `gc.get_threshold()[0]`,
  plus the change in `gc.get_count()[0]`: every collection starts when the
  generation-0 count passes that threshold, and resets it.
  Counting generation 0 alone read about 9% low, because a collection that
  also takes older generations is counted under the oldest one it takes.
- Count live objects in a separate, untimed mode, because
  `len(gc.get_objects())` is slow. That mode calls `gc.collect()`, which
  resets the collection counters, so estimate allocations in a different
  run.
- CPython 3.12 runs a full collection only when enough young collections
  have run and the long-lived objects waiting for one exceed 25% of all
  long-lived objects. Level A removed about half the tracked allocations,
  which halved collections per render (123 to 67), and full collections
  also fell, from 10 of 11 renders to 6 of 11. So removing short-lived
  objects can make full collections rarer too.
- Credit a level with a collection saving only when the measured count or
  pause time falls. Bound it with three runs of the same arm: normal,
  after `gc.freeze()`, and with the collector off. "Normal minus freeze"
  caps the credit from fewer full collections (8.6 ms in Stage 0, about
  6.5 ms with A on), and "freeze minus off" caps the credit from fewer
  young ones (8.2 ms in Stage 0, about 3.9 ms with A on).
- CPython 3.14 collects incrementally, so collection figures need measuring
  again there before any claim reaches users.

**First and second load through the server.** The board app runs under
uvicorn in a fresh process per sample, and plain HTTP requests fetch the
page twice. Read the `prepare` span of the `Server-Timing` header; the
`application` span measures a different interval. Single loads have
outliers: in one Stage 1 run, one process of 5 with the change read
167.7 ms against 131.5-136.0 ms for the others, and the processes without
it had an sd of 2.0 ms on first load and 4.1 ms on second load. Each
process gives one first load, so use 10 processes per cell.

**Equivalence before timing.** No timing counts until every arm writes the
same bytes. The harness pins render ids, the Vue app id, the Events token
clock and the CSP nonce, and replaces the Django CSRF token, then compares:
- full HTML and manifest bytes for each output kind (hydrated, `ssr=False`,
  static, fragment, CSP, hydration declined, serialized twice);
- Events action responses;
- fault cases: the same exception, message, `__cause__` and `__context__`
  chain, innermost traceback frame, component path and callback counts;
- the order log of every user callback and hook, the trace log, and for
  the C levels, the execution frame each callback sees, the registry and
  admission counts, and whether the scope and value context were reset.

A case with two threads must start both at a barrier with a short
`sys.setswitchinterval`, or the two renders never overlap. The production
tests do the same through `render_both` and `tests/test_call_run_order.py`
(see `native_render.md`).

**Pitfalls the research hit.**
- Each child process must clear the environment variables that turn on
  the other arms, and a child that prints a Python warning should fail the
  run: a warning usually means the arm silently took another path.
- Record hook calls for the order check with `sys.setprofile`, as
  `tests/test_call_run_order.py` does: replacing a built-in hook method
  turns hydration off (see "Traps found while building the levels"). If a
  hook must be patched, patch it on the class that defines it. Patching it
  on the `Extension` base makes every extension look as if it defines the
  hook, and patching the instance changes what `vars(extension)` shows.
- In a case with two threads, registry counts depend on which thread fills
  a shared cache first, so compare bytes only.
- A release build uses every core for minutes and disturbs other timing
  runs on the machine: build between runs, or with `CARGO_BUILD_JOBS=2`.
- A `CARGO_TARGET_DIR` shared between worktrees once made a release build
  reuse another worktree's compiled crate, and the build failed because
  the new source file's exports were missing. Touching the crate's
  sources forced the rebuild.
- Other sessions loaded the machine during several runs, so absolute
  times differ between tables. Compare within one run of pairs, never
  across runs. Nothing pinned CPU cores or controlled the temperature;
  the method relies on fresh processes, alternating which arm goes
  first, paired differences and a quiet machine.

**Repeating a comparison.** The harness scripts were not kept, but the
method needs little code. The production levels were timed this way:
1. Build one install per side (the base commit and the change), each in
   its own Python 3.12 environment, because the board app requires 3.12.
   For a base checkout, run `git submodule update --init --recursive`
   first. Then run `maturin build --profile release-wheel` in
   `packages/py/citry_core` and `uv build --wheel packages/py/citry`, and
   `uv pip install --reinstall` both wheels plus the board's dependencies.
   `--reinstall` matters, because uv keeps an install with the same
   version number. Install the second side with `-c` pointing at the
   first side's `uv pip freeze --exclude citry --exclude citry-core`, so
   both get the same other packages; without the two excludes the freeze
   pins citry to the first side's wheel. Leave `CARGO_TARGET_DIR` unset,
   and check each side with
   `python -I -c "import citry_core._rust as r; print(r.BUILD_PROFILE)"`,
   which must print `release`.
2. Write a timing script that puts `benchmarks/web/apps/citry` on
   `sys.path`, imports `app`, and registers a `gc.callbacks` hook that
   records the pause time and generation of each collection. For each of
   13 renders, call `app.reset(f"s{i}", rows)` outside the timed span,
   then time `app.Page(session=f"s{i}").render()` and `.serialize()`
   separately. For the fragment page call
   `.serialize(deps_strategy="fragment")`; for the strict-CSP page, set
   `app.engine.settings = dataclasses.replace(app.engine.settings,
   security_csp="strict")` once (the board uses Events), then call
   `.serialize(security_csp="strict", csp_nonce=...)`. Drop the first 2
   renders. Print the mean of all renders and the median of the renders
   with no generation-2 collection.
3. Run the script in fresh processes, alternating the sides (odd pairs
   start with the base), 5 or 10 pairs, at 1,400 and 140 rows, and apply
   the keep rule above to the median over processes and the median paired
   difference. To compare the Rust and Python paths in one install, set
   `CITRY_NATIVE_RENDER=0` on one side.
4. For loads, start a fresh server per sample with
   `python -m uvicorn app:application` in `benchmarks/web/apps/citry`,
   wait for `/health`, request `/?count=1400&session=s1` and then
   `/?count=1400&session=s2`, and read `prepare;dur=` from each
   response's `Server-Timing` header. Use 10 servers per side.

For reference, `origin/main` `736071308` on release wheels and Python 3.12
rendered and serialized the hydrated board in 99.3 ms at 1,400 rows and
14.1 ms at 140 rows (the median over processes of each process's mean),
and served the 1,400-row page in 155.3 ms on first load and 103.1 ms on
second load (the median of 10 servers).

## Stage 0 results (measured 2026-10-20)

**Setup.** All runs used one machine and one source tree: a checkout of
`origin/main` `695bd3168`, CPython 3.12.13, and citry-core built in release
mode. The section "How the research measured" describes the harness. The
only source change is a timing hook on two nested functions in
`packages/py/citry/citry/_vue/direct_capture.py`, which does nothing unless
the harness turns it on. Before the runs, two desktop apps that had each held
a full CPU core for weeks were closed. A macOS storage indexer still ran.

### Warm time at 1,400 rows, and where it goes

These are medians of 33 samples: 3 fresh processes, each with 2 warm-ups
and 11 timed renders, under normal garbage collection.

| Measure | 140 rows | 1,400 rows |
|---|---:|---:|
| Render + serialize, no wrappers | 6.6 + 8.3 = 14.9 ms | 58.2 + 52.3 = 110.5 ms |
| Garbage-collection pauses inside that | 0.6 ms | 16.9 ms (124 collections) |

To attribute the time, a second set of processes wraps about 40 functions.
Each wrapper records its *exclusive* time, which leaves out the time of other
wrapped functions it calls, so every millisecond is counted once. The table
gives the median of each function's exclusive time, summed per group. These
sums come to 103.8 ms at 1,400 rows, against the plain median of 110.5 ms.
The 6.7 ms gap is mostly garbage-collection spikes: the median of a sum is
larger than the sum of medians when a few samples carry long collections.
Wrapping also adds about 5.6 ms of overhead inside the wrapped functions,
mostly per-row ones, so the per-row groups are slightly overstated. Shares are
of the plain 110.5 ms.

| Group | 140 rows (ms) | 1,400 rows (ms) | Share at 1,400 |
|---|---:|---:|---:|
| Stays in Python: user code (board snapshot, data methods) and schemas | 0.8 | 6.9 | 6% |
| Already Rust: the hydration HTML writer | 1.3 | 11.1 | 10% |
| Mostly C inside CPython: placement digests and manifest `json.dumps` | 1.4 | 10.6 | 10% |
| A can move it: row setup, row check, evaluation | 2.4 | 23.4 | 21% |
| B can move it: serialize Python (per-occurrence assembly, manifest building, document) | 5.9 | 31.8 | 29% |
| Only C can move it: scheduler, ordinary components, loops, NotePanel and ProjectInfo leaves | 3.5 | 19.9 | 18% |
| Not owned by one function | about 0 | 6.7 | 6% |

(Each wrapped function is placed in one group. These groups follow the code's
render and serialize split. The projection below assigns the per-row part of
serialize to A, because A writes the row's manifest entry: per-occurrence
assembly, digests and the round trip. So A moves 44 ms there, not 23.4.
Row setup includes render-id minting and the admission check, which A keeps
in Python.)

Largest single items at 1,400 rows (exclusive ms):

| Item | ms | Calls |
|---|---:|---:|
| Row check plus generated evaluator (`render_static_instance_free`) | 13.2 | 1,400 |
| Per-occurrence assembly (`transform_component`) | 11.6 | 1,416 |
| Rust hydration HTML (`_render_for_hydration`) | 11.1 | 1 |
| Row setup (`_render_simple_vue_leaf`: admission check, ids, records) | 10.3 | 1,415 |
| NotePanel and ProjectInfo leaf programs | 6.0 | 4 |
| Copying recorded row values (`attach_leaf_data`) | 5.5 | 1,404 |
| Placement digests (`_digest`) | 5.3 | 2,852 |
| Manifest encoding (`_script_json`) | 5.3 | 2 |
| Parent loop per row (`ComponentNode.render`) | 4.9 | 1,415 |
| Board snapshot (user code) | 3.9 | 1 |
| Server data round trip (`PreparedOccurrence._from_assembly`) | 3.2 | 1,416 |
| Row `template_data` (user code) | 0.3 | 1,400 |

How this compares with the paper estimate in section 1:
- The row check and evaluator (13.2 ms) fall inside the estimated 9-14 ms.
  The estimate left out row setup (10.3 ms).
- User code is smaller (6.9 ms, against an estimated 10-13 ms).
- The per-row part of serialize is large: `transform_component`,
  `attach_leaf_data`, `_from_assembly` and the digests come to about 26 ms.

**Garbage collection.** The same warm render with collection policies
changed, 3 processes each:

| Policy | Render + serialize at 1,400 rows |
|---|---:|
| Normal | 109.1 ms |
| `gc.freeze()` after startup | 100.5 ms |
| Collection off | 92.3 ms |

`gc.freeze()` moves every object alive at that point out of the collector's
reach. It saves 8.6 ms at no cost to the output, but it is a process-wide
choice. It belongs in deployment guidance, not in the framework. Turning
collection off saves 16.8 ms, which bounds the collector pauses that any
reduction in Python object counts can remove. The measurement froze the
objects before the warm-up renders, in process. A frozen object that later
becomes garbage as part of a reference cycle is never freed, so the setting
suits a server that freezes once after startup. The tip now ships in the
user docs' performance page (`docs_site/content/performance/index.md`).

### What Rust costs for the row work (Stage 0b)

A standalone research module, outside `citry_core_py`, does one board row
per call. It checks types against the live plain-scalar set, evaluates every
row expression including the nested loops, and writes the row's values as
sorted, ASCII-escaped JSON. Its output is byte-identical to a Python
reference on all 1,400 rows, and the reference's values equal what Citry's
own evaluator records for every row. It was also checked on 491 edge rows,
200,038 floats against `repr()` (it calls CPython's formatter), and 27 fault
cases. Timings are medians of 11 samples for 1,400 rows. The variants run in
rotation, one round each per sample, so drift affects them all equally.
They use the abi3 build that citry-core ships, which is compiled against
CPython's stable ABI so one wheel serves every CPython version:

| Variant | ms per 1,400 rows | r (against Citry's evaluator plus leaf-data copy and per-row JSON, 16.4 ms) |
|---|---:|---:|
| Rust reads the row through the C API | 1.22 | **0.074** |
| `json.dumps` per row, then Rust parses | 4.74, plus Python's type check 1.34 | 0.37 |
| Citry's generated evaluator alone | 9.59 | |
| A plain Python reference doing the same work | 7.42 | |

(The default, non-abi3 build gave 1.15 ms and r = 0.073.)

**Reading Python objects through the C API is cheap: about 0.9 µs per row,**
including every check and the JSON writing. The archived Rust body walker
(see Prior art) lost, probably because it went back to Python for each body
item (inferred). Here a whole row is read and written in one call. The JSON
route loses, because encoding in Python costs more than everything Rust
does.

What this does not cover:
- integration costs, such as the Python record per row and handing data over
  to the hydration writer;
- C's page-level passes and scheduler work;
- the free-threaded CPython 3.14 and PyPy builds;
- rows with many attachments or non-ASCII text. The board data has 200
  dependencies, 100 attachments, no tags and only ASCII text.

The module also skips three checks Citry makes, listed in its README:
`c-bind` name validation and `style` normalization, lone-surrogate strings,
and `_ConstMapping` roots. None occurs on the board.

### Projections from the measurements

A short script computed the projection from the exclusive-time medians at
1,400 rows. One rule set applies to every
item:

| Kind of work | Ratio r used | Items at 1,400 rows (ms) |
|---|---|---|
| Measured by Stage 0b | 0.074 at both ends | row check and evaluator 13.2, leaf-data copy 5.5 |
| Python work Stage 0b did not measure | 0.074 (optimistic) to 0.5 (pessimistic) | per-occurrence assembly 11.6, half of row setup 5.1, page-level serialize passes 11.5, scheduler, loops, ordinary components and leaf programs about 20 |
| Work CPython already does in C | 1, so no saving | placement digests 5.3, manifest `json.dumps` 5.3, server-data round trip 3.2 |
| Stays | not moved | user code and schemas 6.9, Rust hydration HTML 11.1, the other half of row setup (ids, admission, callback order) |

- Integration costs 2 ms at the optimistic end and 5 ms at the pessimistic
  end, charged once (unmeasured).
- The 6.7 ms that no single function owns (garbage-collection spikes and
  wrapper overhead) is not credited.

| Architecture | Moved work | Warm saving | Warm time | T |
|---|---:|---:|---:|---:|
| A: Rust row producer | 44 ms | 21-31 ms (19-28%) | 80-90 ms | 0.72-0.81 |
| A + B: plus the Rust serializer | 61 ms | 26-41 ms (24-38%) | 69-84 ms | 0.62-0.76 |
| C: native scheduler | 81 ms | 36-60 ms (33-54%) | 51-74 ms | 0.46-0.67 |

**What this says about one third.**
- For C, s = 0.21: user code, schemas, the half of row setup that stays, and
  the Rust writer. So the ratio that would reach one third is
  r* = (1/3 - s)/(1 - s) = 0.16. The measured r = 0.074 is well below r*.
  What holds the projection above one third is the work CPython already does
  in C, kept at r = 1.
- **Projected T for C is 0.46-0.67.** Both ends are above one third and both
  savings are at least 25%. By the section 5 decision table, one third is
  ruled out for this page on present evidence. Stage 1 was worth running for
  the smaller goal, and it ran with the maintainer's agreement.
- Two unmeasured effects could narrow the gap:
  - Rust could remove outright the work CPython already does in C, up to
    about 14 ms;
  - fewer Python objects could cut garbage collection, up to 16.8 ms.

  Either one alone could bring C's optimistic end to about one third
  (unproven). For example, removing the 13.9 ms of C work gives T = 0.33.
- For A + B, the scheduler, loops and ordinary components stay as well, so
  s is about 0.39 and one third is out of reach.

First load and request to layout use the 2026-09-27 run's totals:
Server-Timing `prepare` 157.7 / 110.3 ms, and request to layout 359.2 / 304.1
ms. "Startup compilation" assumes it removes 30-38 ms of the first request's
one-time work (unproven).

| Case | First-load prepare (ms) | Second-load request to layout (ms) | First-load request to layout (ms) |
|---|---:|---:|---:|
| Today | 157.7 | 304.1 | 359.2 |
| A | 127-137 | 273-283 | 328-338 |
| A + B | 116-131 | 263-278 | 318-333 |
| C | 98-121 | 244-268 | 299-323 |
| C plus startup compilation | 60-91 | 244-268 | 261-293 |
| Others in the same run: Rusty / Jinja / Nuxt | 11.0 / 17.5 / 81.4 (their spans) | 293.9 / 295.1 / 211.3 | 313.3 / 315.2 / 269.8 |

The first load pays a one-time cost of about 42-47 ms. In process it
splits roughly as follows:
- about 30-38 ms of compilation and first-render setup: template parse and
  compile, Vue definitions, row evaluator code generation, expression
  rewriting, and building each component's body on its first render. About
  7 ms of that is already Rust.
- about 5-10 ms of first-touch memory and interpreter warm-up. The row
  evaluator alone runs 9.2 ms slower on its first page (likely page faults,
  unproven).

Compiling the registered templates and building their bodies at startup
would remove most of the first part, independently of Rust.

The largest one-time items, from the cold-process attribution (first
render minus a warm render, exclusive ms at 1,400 rows):

| One-time work | ms |
|---|---:|
| First renders of the ordinary components and the `simple = "vue"` admission check | 11.3 |
| The row evaluator's first render of the page, likely memory the process has not touched yet (unproven) | 9.2 |
| Python's checks on the Vue compiler's response | 6.9 |
| Template load and compile, Python side | 5.9 |
| Generating and `exec`-ing the row evaluator and its read-set check | 4.1 |
| Rust Vue compile, and Rust template parse and compile | 4.0 and 3.1 |

Collector pauses on the first render were 14.1-14.6 ms over about 140
collections, no more than on a warm render, so they do not explain the
slow first load. Logging `resource.getrusage(RUSAGE_SELF).ru_minflt`
before and after the first two requests would size the page-fault
explanation; it was not run.

**Not measured in Stage 0, deferred to Stage 1 or later:**
- the C API reads on the free-threaded CPython 3.14 build. Stage 0b skipped
  it because the research venv is CPython 3.12, and building citry for 3.14t
  was out of the Stage 0 budget;
- the C API reads on PyPy;
- the Rust producer inside the real render path (measured in Stage 1).

### The 0.6.0 first-load step

The 0.6.0 release benchmark report shows
Citry's first-load prepare at 1,400 rows at 199.4 ms, against 120.3 ms on the
second load. The qualification run from the same evening,
`20261019T210740Z-2b5cd077`, shows 196.2 ms, and the 2026-10-16
qualification run shows 169.3 ms. The step appears only at 1,400 rows: the
first-load gap at 14 and 140 rows is about 46-48 ms, as before.

Served through the real uvicorn server with plain HTTP requests, in 5 fresh
processes per build:

| Build | First load (min-max) | Second load |
|---|---:|---:|
| Local release build of `695bd3168` | 155.6-161.5 ms | 109.1-112.6 ms |
| PyPI `citry==0.6.0`, `citry-core==1.8.0` (abi3 wheel) | 153.5-163.1 ms | 107.4-110.0 ms |

A source comparison against the Sep 27 build found no new first-request
work. So the step comes from something in the release harness run that this
setup lacks. The candidates are the concurrent browser, memory pressure
from the apps that ran before Citry, and the harness's build environment.
Memory pressure is a weak fit: with the profile's fixed seed, Citry runs
13th of 14 apps at every size, and the 14- and 140-row cells show no step.
It is not CPU load alone, because that would have hit every size. The cause is not
isolated. Until it is, the release report's Citry first-load figure at
1,400 rows should not be read as a code regression.

**Recheck through the real harness, 2026-10-20.** Citry alone ran through the
same harness (profile `release-0.6.0-citry`, identical to `release-0.6.0`
except for the app list) with the other sessions' tests stopped. Each cell of
this profile is one page load, so each figure below is a single observation:

| Run | 1,400 rows, first load | Second load | First minus second | Same gap at 140 rows |
|---|---:|---:|---:|---:|
| Release qualification, 2026-10-19 | 196.2 ms | 117.8 ms | 78.4 ms | 46.4 ms |
| Release latency run, 2026-10-19 | 199.4 ms | 120.3 ms | 79.1 ms | 46.5 ms |
| Recheck qualification | 207.9 ms | 146.1 ms | 61.8 ms | 44.1 ms |
| Recheck latency run | 165.3 ms | 115.2 ms | 50.1 ms | 45.5 ms |

The recheck latency run, the like-for-like comparison with the release
cell, shows no step. Its first load is just above the plain-HTTP range
(153.5-163.1 ms), and its first-minus-second gap is close to the 44-47 ms
seen at 140 rows. The recheck qualification run was slow on both loads at
1,400 rows, and its 14-row first load was 85.9 ms against about 55 ms
elsewhere, while its 140-row cell was normal. Its gap is about 18 ms above
its own 140-row gap. Whether that is machine noise or a smaller step is
unproven. Other sessions were idle, but this session's own review agent was
running.

So the step does not reproduce reliably. With one sample per cell, a rerun
of the whole cohort under the same profile would replace one single sample
per cell with another. A rerun with more blocks (each block starts a fresh
server process, so it adds cold first loads) would settle it, but that
changes the method for every framework. Either rerun takes about 90 minutes
or more, because only Citry was built in the recheck checkout. The decision
is in section 7.

### Python-only cuts found by the sweep

These were ranked estimates when the sweep made them. The cuts that change no
output were then built and measured together: -8.6% at 1,400 rows (see
"Stage 1 results"). Most of them shipped in
[#262](https://github.com/citry-dev/citry/pull/262) (the decision ledger lists which), and the
`on_dependencies` fix in the last row shipped on its own in
[#260](https://github.com/citry-dev/citry/pull/260).

| Change | Estimated saving at 1,400 rows | Contract touched |
|---|---:|---|
| `gc.freeze()` after startup (deployment guidance) | 8.6 ms, measured | none |
| Placement digests: hash the constant prefix once, copy the hasher per row, share one JSON encoder | about 2.5 ms | none (ids stay byte-identical) |
| Registry lookups under the lifecycle lock, about 4 per row: make the context managers small classes | 1.5-2 ms | none |
| Per-row schema and mapping copies, function-level imports in per-row code, per-occurrence work that depends only on the definition | 1-2 ms each | none |
| Dependency records resolved twice in `ext/dependencies/emission.py:224` | up to 1 ms | yes: the user's `on_dependencies` hook runs twice today, against its documented once-per-instance contract. That is a bug to fix with a changelog entry. |

The cuts that touch no output total about 8-12 ms, so about 17-21 ms
(15-19%) with `gc.freeze()`. Two candidates overlap with rejected ledger entries (the
`json.loads(json.dumps(...))` round trip and the per-row leaf-data copy), so
neither should ship on its own.

The shipped cuts are listed in the decision ledger. Parts of three sweep
items did not ship with them and remain open Python-only work:
- *Per-row schema copies* (1-2 ms estimated): cache one schema plan per
  class, and skip the two empty `_ConstMapping` objects built for a missing
  `js_data` and `css_data`. The missing-argument `TypeError`, the timing of
  `default_factory` and `Const` unwrapping must stay, and
  `_normalize_data` must still run whenever a schema is declared. A
  similar ledger entry ("closed-engine orchestration cut") was flat, so
  expect little from the empty objects alone.
- *Repeated passes* (part of 1-1.5 ms): `analyze_vue_serialization` makes
  about six passes over every part, and `events.py` loops over all
  occurrences several more times. (#262 already removed an unused set built
  in `record_region` and the style table built for a page with no
  styles.)
- *String copies while the document is finished* (under 1 ms): the page is
  copied whole about five times and the 1.28 MB configuration script (the
  script that carries the page's manifest) about six. Joining the CSS, JS and preloads once, after `on_serialize`, needs a
  byte-parity test and the constraints listed under B4 in "Levels dropped,
  and alternatives rejected". (#262 already made two scans cheaper: it
  checks for `"</"` before lower-casing the script, and tests with `in`
  where it used `count`.)

## Stage 1 results (measured 2026-10-20)

**What was built** (on a research branch that was never merged): a
Rust row producer for instance-free rows, behind the
`CITRY_RESEARCH_RUST_ROWS` switch. It lives in a new crate,
`citry_leaf_rows`, and a `leaf_rows` submodule in `citry_core_py`. It came
in two versions, each measured against the switch off:
- **Level 1.** Each row's data methods still run in Python, in today's
  order. Then one Rust call reads the row and either writes the row's
  manifest entry or hands the row back to today's Python evaluator. Every
  other output gets the values back through the existing Python evaluator.
- **Level 2** adds two things on top of Level 1:
  - Rust computes each row's two placement ids (the hashed ids that say
    where an occurrence sits under its parent) in one call. It hashes the
    shared prefix of a call run (the rows one loop places at one call site)
    once. The ids match Python's byte for byte. A row key with no UTF-8
    form, such as a lone surrogate, falls back to Python.
  - A shortcut past assembly, the per-occurrence step that records each
    occurrence's definition, ids and lookup maps. A Rust-produced row with
    no `js_data` and no root markers (the hydration markers a component
    writes on its root element) skips `transform_component` and goes
    through a short loop that writes the same records and maps. Events
    updates keep the Level 1 path.

**Equivalence.** With the switch on, the output is byte-identical to the
switch off, at both levels:
- 24 output cases (hydrated, `ssr=False`, static, fragment, CSP, hydration
  declined, serialized twice) at 14, 140 and 1,400 rows;
- 10 Events action responses;
- 20 fault cases. Each gives the same exception, component path and
  callback counts. The 20th, added for Level 2, puts a lone surrogate in one
  row key, so Python and Rust ids mix within one run.

Rust produces all 1,400 board rows, and the hydrated path rebuilds no Python
row objects. Independent reviewers fuzzed about 220,000 rows across 13
synthetic templates (Level 1) and 180,000 keys through the Rust ids
(Level 2), and compared 215 real assemblies against the Level 1 code. They
found no mismatch.

**How the numbers are taken.** Every comparison below alternates the two
variants across 5 fresh-process pairs. Each process renders 2 warm-up pages
and then 11 timed ones, under normal garbage collection. A process's value is
the median of its 11 render plus serialize times, and the table shows the
median of the 5 process values. Other sessions were loading the machine
during the Python-cuts and Level 1 runs, and less so during the Level 2
run, so absolute times differ between tables. Compare within a table, not
across tables.

**The baseline includes the Python-only cuts.** They were merged into the
research branch first, so the Rust comparison is against the cleaned-up
Python. The cuts on their own:

| Rows | `origin/main` | With the Python-only cuts | Change |
|---:|---:|---:|---:|
| 140 | 16.4 ms | 15.8 ms | -4.1% |
| 1,400 | 142.5 ms | 130.1 ms | -8.6% |

At 1,400 rows every process with the cuts was faster than every process
without them. At 140 rows the ranges overlap.

**The Rust row producer against the cleaned-up Python:**

| Level | Rows | Switch off | Switch on | Change |
|---|---:|---:|---:|---:|
| 1 | 140 | 15.5 ms | 12.7 ms | -2.8 ms (-17.8%) |
| 1 | 1,400 | 124.4 ms | 98.1 ms | -26.3 ms (-21.1%) |
| 2 | 140 | 13.8 ms | 11.2 ms | -2.5 ms (-18.5%) |
| 2 | 1,400 | 103.7 ms | 77.2 ms | -26.5 ms (-25.5%) |

In all four rows, every switch-on process was faster than every switch-off
process. The medians are a little conservative for the switch on: there, a
full garbage collection runs on about every other render, and with 11
samples the median lands on a render that includes one. Means give -23.8%
(Level 1) and -27.3% (Level 2) at 1,400 rows.

**Level 2's own share is about 5-8 ms, not measured directly.** No run put
Level 1 and Level 2 side by side, and the two ran under different load. Two
indirect readings disagree:
- On renders without a full collection, `transform_component` drops from
  14.6 ms (Level 1) to 6.1 ms (Level 2). Allowing for the load difference,
  that is about 7.5 ms. The in-process check of the Rust ids (2.5 → 1.1 ms
  per 1,400 rows) adds about 1.4 ms, and row setup grew by about 1.2 ms, so
  the net is 7.5 + 1.4 - 1.2 = 7.7 ms.
- The whole-page ratios (0.789 for Level 1, 0.745 for Level 2) give about
  4.6 ms.

The Stage 1 design estimated 4-6 ms.

**Garbage collection.** Fewer Python row objects made full collections
rarer. At 1,400 rows, a collection pause above 8 ms came on 50 of 55 renders
with the switch off and on 30 of 55 with it on, at both levels. Average
collection time per render fell from 16.5 to 10.2 ms (Level 2). Each pause
stays about 17 ms long; only fewer of them happen. ("Full" is inferred from
the pause length; the harness does not record the generation.)

A full collection lands wherever the allocation that triggers it happens,
which skews per-function figures. With the switch on it often landed inside
`PreparedOccurrence._from_assembly`, so that function's median read 13 ms.
On renders without a full collection it cost 1.1 ms, down from 3.3 ms with
the switch off. Read per-function times from renders without one.

**Where the remaining per-row time sits**, from exclusive time with the
switch on at 1,400 rows, on renders without a full collection:
- The Python evaluator (15.0 ms) is gone. Most of the per-row copying and
  encoding is gone too: leaf-data copy 5.9 → 2.3 ms, manifest encoding 5.7
  → 1.0 ms, server-data round trip 3.5 → 1.2 ms.
- Assembly (`transform_component`) took 14.6 ms with Level 1 and 6.1 ms
  with Level 2. What is left belongs to the board's other components.
- Python row setup still takes about 7 µs per row (10.1 ms). That covers the
  admission check, id minting and data-method dispatch, and the Rust read
  (about 1 µs, inferred) is included in it. It is above the 5 µs the plan
  named as a warning line. Only the order-preserving batched-run variant
  addresses it, which belongs to the C direction.

**What Stage 1 says about the hypothesis.** Architecture A alone cuts warm
time at 1,400 rows by 21-26% against the cleaned-up Python. The projection
was 21-31 ms, and the measured saving is 26 ms at both levels. With the
Python-only cuts, warm time is about 28-32% below `origin/main`: T ≈
0.68-0.72. That range is the product of ratios measured separately under
different load (0.914 × 0.745 = 0.68, 0.914 × 0.789 = 0.72). C's projection (T 0.46-0.67) assumed no Python cuts, so the two are not
directly comparable. C plus the cuts would project somewhat lower, but the
cuts overlap with C's savings.

The "Decisions after Stage 1" table in section 5 asks for C's projection to
be redone with the ratio measured in the integrated prototype. Stage 1 did
not measure that ratio directly. A rough reading: A saved 26 ms out of
about 40-44 ms of Python work it moved, which implies a ratio of about
0.35-0.4 rather than Stage 0b's 0.074 (unproven, because the moved work is
estimated from the attribution). With that ratio C lands near the less
favorable end of its range: T about 0.6, a saving of about 35%. Either way,
the third row applies: projected T for C stays above one third and the
projected saving is at least 25%. One third is ruled out for this page, and a production design for
the smaller goal is the maintainer's call.

**First and second load through the real server.** The board app ran under
uvicorn in fresh processes, with plain HTTP requests, alternating switch
off and on across 5 process pairs. The figure is the server's own
`prepare` time from the `Server-Timing` header, median of 5 (range in
brackets). The page bytes were identical.

| Rows | Load | Switch off | Switch on (Level 2) | Change |
|---:|---|---:|---:|---:|
| 140 | first | 60.3 ms [59.2-98.7] | 57.5 ms [57.4-77.9] | -4.6% |
| 140 | second | 14.9 ms [14.2-15.3] | 11.9 ms [11.7-19.2] | -20% |
| 1,400 | first | 156.9 ms [155.3-160.3] | 134.5 ms [131.5-167.7] | -14% |
| 1,400 | second | 106.3 ms [102.9-112.9] | 67.5 ms [66.7-90.3] | -37% |

The first load gains 22 ms at 1,400 rows, less than the warm 26 ms, so the
Rust path adds some one-time cost on the first request (building its row
plans, among others; not attributed). The second load gains more than the
warm measurement does. A second request in a fresh process still collects
much of the startup garbage, and Rust rows leave less to collect, but that
explanation is unproven. Each process gives one first load, so these are 5
samples per cell.

**Not run in Stage 1:**
- the browser-harness run of the prototype (request to layout). Its
  single-sample cells would add little to the table above;
- Python object counts;
- the variant that removes the parent loop's per-row objects.

**Risks recorded for a production version:**
- Rows written directly in the *root* component's template are evaluated
  twice on hydrated and `ssr=False` pages. Reproduced with a 50-row page:
  with the switch on, 50 rows are rebuilt in Python when the rows sit in
  the root template, and 0 when they sit in a child component. The bytes
  match the switch off in all four cases. The cause:
  - The serializer always builds the root component's own HTML, because
    the document shell (doctype, `<head>`, everything outside the part Vue
    mounts) comes from it.
  - It skips child components that Vue will render, but the rows in the
    root template are part of the root's HTML, so it writes their HTML too
    (`serialize.py:1014`). To do that it rebuilds each Rust row's Python
    values.
  - The page then drops that HTML: the hydrated body comes from
    `_render_for_hydration`, and the `ssr=False` body is empty.

  The same HTML is written and dropped on `origin/main` too, so this is
  also a Python-only waste; the Rust path only makes it more expensive. The
  fix belongs in the serializer: do not write row HTML that the output will
  drop. The board is unaffected because its rows sit in a child component.
  That fix shipped in [#261](https://github.com/citry-dev/citry/pull/261)
  (`_can_skip_vue_document_body` in `serialize.py`), and Stage 2 ran with
  the same code merged in. In development mode the page still builds its
  whole body, because the check for repeated `id`s needs every id. The
  timing runs in production mode, so this does not change the figures.
  Production level A goes further: in development mode it does not read
  rows in Rust at all (see `native_render.md`, section 2).
- The assembly shortcut looks up the registry and the tag callback once per
  class per assembly. A registration on another thread during assembly, or
  a tag callback whose answer changes between calls, would not be seen. The
  only callback the shortcut accepts is the built-in one, which caches its
  answers.
- The shortcut repeats the start of `transform_component`. A check added
  there later must also go into the shortcut, or Rust rows would skip it.

## Stage 2 results (measured 2026-10-22)

Stage 2 builds B and C on top of A, one level at a time. B1 and C1 each
come with a pure-Python control arm: the same restructuring with no Rust,
because batching alone removes Python work. Every level must beat the
level below it by its threshold. B1 and C1 must also lead their Python arm
by 2 ms, or the Python arm is kept. Four levels are built and measured here. C1b and C3, the optional levels,
are not built: the maintainer stopped Stage 2 at half of `origin/main`'s
warm time, since neither would reach one third.

- **B1**: with A alone, each Rust row still gets its own Python record
  during serialize. B1 makes one Rust object per loop for those rows. It
  holds the rows' ids, the map entries assembly needs and the rows'
  manifest JSON. On the board that takes the per-row records from 1,416
  to 16.
- **C1**: today each row of a loop is its own task on the render queue. C1
  makes one queue task per loop, which runs each row's setup and data
  methods in the same order as today.
- **C2**: before the rows run, Python's `<c-for>` walks the loop and reads
  each row's inputs. C2 does that walk in Rust for loops over plain data,
  and hands the loop back to Python for anything else (tracing on, values
  that are not plain data, a key it cannot read).
- **B2**: Rust writes the JSON for the other components' data, which
  Python used to convert and copy. Anything Rust cannot write the way
  Python would goes to Python's own conversion. A page can reach only two
  such values: a lone surrogate in text, and an int past Python's digit
  limit in an attribute (found by the production review). Leaf programs
  turn their data into text, ints and bools before B2 sees it (a `citry.Secret`
  becomes its masked text, and a `Markup` value makes the component skip
  the leaf data that B2 writes). Tests called Rust directly to check the
  refusals no page can reach, a `Secret` among them.

Before measuring, the branches were brought up to date with `origin/main`
at `92e1cf5a9`. Since the Stage 1 measurements, main checks component
input types on every row (#208), so the earlier figures were measured
again. Every arm wrote the same bytes, and the order log of every user
callback and hook was identical across arms. The board app runs in
production mode.

### Warm time at 1,400 rows

Each row of the table below is its own run of alternating fresh-process
pairs, 5 pairs, or 10 for the B1 and C1 Rust-against-Python rows and for
C2 and B2. Each process renders 11 times. Its "before" figure was measured
in that run, so it can differ slightly from the "after" of the row above.
Two figures are given per row:

- **Mean**: the median over processes of each process's mean over all
  renders, collector pauses included. This is what a server pays on
  average.
- **No full collection**: the metric chosen to decide with (see "How the
  research measured", "Which figure decides"). It is the paired difference of each process's median over
  the renders that ran no full garbage collection. It leaves out the
  collector pauses a level avoids, so it is the more cautious figure.
  Every Stage 2 arm had 5 to 8 such renders out of 11, enough to use it.
  Only the `origin/main` and Python-cuts arms had too few (one each).

| Step | Mean, before -> after (ms) | Change | Saving, no full collection (ms) | Pairs favoring the "after" arm |
|---|---|---:|---:|---:|
| `origin/main` -> Python cuts | 109.3 -> 100.4 | -8.2% | too few renders | 5 of 5 |
| Python cuts -> A | 100.1 -> 72.6 | -27.5% | too few renders | 5 of 5 |
| A -> B1 in Rust | 72.7 -> 64.1 | -11.8% | 4.55 | 5 of 5 |
| A -> B1 in Python | 72.7 -> 66.8 | -8.1% | 3.15 | 5 of 5 |
| B1 in Python -> B1 in Rust | 67.1 -> 64.3 | -4.1% | 1.65 | 10 of 10 |
| A -> C1 in Python | 73.1 -> 66.8 | -8.6% | 2.29 | 5 of 5 |
| A -> C1 in Rust | 73.0 -> 67.2 | -8.0% | 1.57 | 5 of 5 |
| B1 in Rust -> B1 + C1 in Python | 63.7 -> 61.4 | -3.6% | 0.82 | 5 of 5 |
| C1 in Python -> C1 in Rust (with B1) | 61.0 -> 61.0 | +0.1% | -0.62 | 5 of 10 |
| B1 + C1 -> B1 + C1 + C2 | 61.6 -> 57.7 | -6.5% | 4.09 | 10 of 10 |
| B1 + C1 + C2 -> + B2 | 57.7 -> 55.1 | -4.5% | 2.04 | 10 of 10 |

With collector pauses taken out of each render's time, A cuts 25.9%, B1 in
Rust 8.6%, C2 7.3% and B2 2.4%. At 140 rows every step is smaller: cuts
-7.2%, A -16.0%, B1 in Rust -3.5%, C1 on A -0.6% (Python) and -1.3%
(Rust), C2 -2.3%, B2 -2.2%.

What the table decides, and where the two figures disagree:

- **C2 and B2 are kept** on both figures. C2 saves about 4.1 ms per render
  (threshold 3 ms) and B2 2.0-2.65 ms (threshold 1.5 ms), in every pair.
  About half of B2's mean saving is fewer collector pauses. Neither has a
  Python arm, because the design did not ask for one. A Python walk over
  the same pre-read paths, or a Python writer that skips the copy, might
  take part of the gain, as B1's and C1's Python arms did. That is
  untested.
- **C1 stays in Python.** Its Rust arm is no faster, on A alone or with
  B1. The gain comes from running a loop as one queue task, not from Rust.
  On A alone C1 passes on both figures. On top of B1 it saves 2.3 ms on
  the mean but only 0.8 ms on the cautious figure, below C1's 3 ms
  threshold. So the keep is clear on A and marginal on B1.
- **B1 is kept in Rust, by the maintainer's decision.** On the mean, B1
  in Rust leads its Python arm by 2.7 ms in 10 of 10 pairs. On the
  cautious figure the lead is 1.65 ms, under the 2 ms the rule asks for,
  which alone would keep the Python arm. Rust's extra lead comes from
  fewer full collections, which the mean counts and the cautious figure
  leaves out by design. Collector pauses are real server time, and the
  Rust arm is small: about 700 lines of Rust in place of the Python
  arm's 275 lines. The Python changes around it serve both arms.
- **The full stack** (A, B1 in Rust, C1 in Python, C2, B2) takes about
  **0.50** of `origin/main`'s warm time at 1,400 rows on the mean (0.54
  with collector pauses taken out). The steps above multiply to 0.505,
  and the direct ratio of the last run's 55.1 ms to `origin/main`'s
  109.3 ms is 0.504. Each run's "before" figure lies within 0.6% of the
  previous run's "after", so multiplying across runs holds. With B1 in
  Python the stack would be about 0.53, if the later levels save the same
  on top of it (not measured). Stage 1 left it at 0.68-0.72. One
  third is not reached with the levels built; the next subsection shows
  what remains.
- **Per level, research against production.** Production timed each
  level again on release wheels, each against the level below, starting
  from `origin/main` `736071308`, which already has the Python cuts. A, B1, C2 and B2 agree
  with the research within the noise: A -27.5% in the research and -28.1%
  in production; B1 4.55 ms and 4.8 ms collection-free; C2 4.09 and
  4.2 ms; B2 2.04 and 2.6 ms. C1 on top of B1 measured about half the
  research figure: -1.7% against -3.6%. Production also timed what the
  research did not: fragments (-25.7% for the whole stack at 1,400 rows),
  the strict-CSP page (-3.8%), and C1 with the native path off, as PyPy
  runs it. There C1 is 0.17 ms (1.2%) slower than B1 at 140 rows and 0.9%
  slower than `origin/main`, which misses the production plan's "not
  slower" bar; it was kept as the base C2 needs.

### First and second load through the server

The server's own `prepare` time, from its Server-Timing header, at 1,400
rows: the median of 5 fresh servers per arm, as a fraction of
`origin/main`. The design asked for 10 servers per arm, because single
loads have outliers. These runs used 5, so treat the third digit as
noise.

| Stack | First load | Second load |
|---|---:|---:|
| `origin/main` | 167.5 ms (1.00) | 114.0 ms (1.00) |
| Python cuts | 0.93 | 0.89 |
| A | 0.78 | 0.58 |
| A + B1 | 0.76 | 0.54 |
| A + B1 + C1 | 0.70 | 0.54 |
| A + B1 + C1 + C2 | 0.68 | 0.51 |
| A + B1 + C1 + C2 + B2 | 0.67 | 0.48 |

The C2 and B2 rows come from later runs of 5 servers per arm. Each run
measured `origin/main` and the stack below again alongside: `origin/main`
first load was 165.7 and 166.7 ms. At 140 rows first load stays at
0.91-0.95, because one-time work dominates it. Second load at 140 rows
reaches about 0.69 with every level on.

### Garbage collection, and the B1 gate

With A on, collector pauses take about 10 ms of the 73 ms. Freezing startup
objects (`gc.freeze()`) brings the render to 66.8 ms, and turning the
collector off brings it to 62.9 ms, so no level can earn more than about
10 ms from fewer collections.

Before B1 was built, a profiling run (B0) timed the serialize loop that B1
replaces, with A on. The design asked for at least 2.5 ms before building
B1 without the maintainer's agreement. The median over all renders read
16.3 ms, but that figure has the skew Stage 1 found: a full collection
often lands inside the loop, and its pause is counted there. On renders without one the loop
took 3.26-3.33 ms in each of the 3 processes, against a projection of
3.1-4.1 ms. That still clears the 2.5 ms bar, so the decision to build B1
stands on the right figure too.

Object counts for B1, measured: the `PreparedOccurrence` objects on the
board fell from 1,416 to 16, and dicts alive at the manifest write from
16,586 to 13,786. Per row, 3 fewer tracked objects (objects the garbage collector tracks)
are alive at that point
with the Rust arm and 2 fewer with the Python arm, which keeps one small
object per row (the design had estimated about 8, but empty dicts are not
tracked and some objects die when assembly returns). Net tracked
allocations during serialize fall by 9.0 per row with the Rust arm and 7.5
with the Python arm. That difference fits the Rust arm's extra lead on the
mean, which comes from fewer full collections (inferred).

### Where the remaining time goes

With every level on, 3 profiling processes at 1,400 rows give a median of
54.3 ms per render plus serialize. Each millisecond is counted under one
function; the counts add up to 53.9 ms, and the wrappers add a little
time:

| Work | ms | Already in Rust? |
|---|---:|---|
| The hydration HTML writer | 10.9 | yes |
| Per-row setup in Python: id minting, the admission check, kwargs, calling the data methods, finishing the record | 11.4 | no |
| User code and its schemas (the app's data function and the input checks) | 6.1 | stays in Python |
| The board's other components' Python leaf programs | 5.8 | no; C3 (Rust leaves for these components, not built) targets it |
| Serialize: the finished plan, the other components' records, the run objects, the leaf JSON, assets, the document shell, dependencies | 14.7 | partly |
| Render bookkeeping: body walks, the loop walk, the queue | 4.5 | partly |
| Other, each under 0.3 ms | 0.4 | |

One third of `origin/main`'s warm time is about 36 ms, so about 19 ms more
would have to go. Outside user code and the hydration writer, about 37 ms
of Python work remains, so reaching one third means removing about half
of it. C3 was projected at 3.5-4.9 ms against A, and part of that overlaps
what B2 already saved. C1's Rust arm moved the loop around the per-row
setup and saved nothing, because each row still calls the same Python
functions; porting those functions to Rust was not tried. The rest is
spread over many small steps. So the levels in the design do not reach
one third on this page.

### Not built: C3, and what it would need

C3 would move the board's two other leaf components, NotePanel and
ProjectInfo, onto A's Rust path. Their Python leaf programs cost 5.8 ms at
1,400 rows with every level on (table above).

What blocks it is a contract question, not code. Both components have
attributes worked out at render time, and the Events extension registers
an `on_attrs_resolved` hook, which runs after a component's attributes
are resolved and may change them. Citry cannot prove what a hook does,
so a component with resolved attributes and such a hook takes the
general Python evaluator: the leaf program drops its generated evaluator
when any `on_attrs_resolved` hook is registered and the template has
dynamic attributes (`_vue/leaf_program.py`, in the leaf program's
render). A's Rust plan, and even the faster generated Python evaluator,
apply only when no hook can change the opening tag.

There is a precedent. `simple = "vue"` rows already accept the built-in
Events hook and only that one (`_simple_vue_spread_hooks_supported` in
the same file), because the reserved keys it acts on are rejected there
first. C3 would extend that reasoning to ordinary leaf components.

To build C3, the maintainer would first rule that the built-in Events
hook is an observer: it is still called, in the same order, but its
result cannot change these components' opening tags. That is the
"observer" class of the effect contract sketched in `rust_rendering.md`.
The ruling then needs a test that the hook's return value for these
components equals its input. With the ruling in place:

- the Python step comes first: let the generated evaluator run these
  components under the same ruling, projected at 2-3 ms (unproven);
- then C3 itself, projected at 3.5-4.9 ms against A, part of which
  overlaps what B2 already saves;
- a third-party extension with its own `on_attrs_resolved` hook keeps
  the general evaluator, because only the built-in hook is ruled on.

The bar the design set for C3: at least 2.5 ms against the level below
with 5 pairs, and at least 1.5 ms more than the Python step above with
10 pairs, so the Rust part has to earn its place over the Python one. In
a stack with C3, B2's saving must not be counted again, because C3 turns
the same leaves into Rust rows. With C3, the design projected the stack
at 0.42-0.58 of `origin/main`'s warm time, still above one third.

Neither step brings the board near one third, which is why Stage 2
stopped before them.

### Stage 2 projections compared with the results

Before building anything, the written Stage 2 plan projected each level
from the Stage 1 attribution, on renders without a full collection.
Comparing the projections with what was measured shows where this kind of
estimate goes wrong:

| Level | Projected saving | Measured, no full collection |
|---|---:|---:|
| B1 in Rust | 3-6 ms | 4.55 ms |
| B1 in Python | 1-2.5 ms | 3.15 ms |
| C1 in Rust | 4-7 ms | 1.57 ms on A; -0.62 ms on top of B1 |
| C1 in Python | 1.5-3 ms | 2.29 ms |
| C2 | 4-6 ms | 4.09 ms |
| B2 | 1-1.8 ms, perhaps too small to see | 2.04 ms |
| The full stack, warm, as a fraction of `origin/main` | 0.44-0.61, including up to 6 ms of credit for fewer collections | 0.50 (mean) |
| The full stack, first load | 0.69-0.80 | 0.67 |
| The full stack, second load | 0.37-0.50 | 0.48 |

Every level landed near its projection except C1 in Rust. Its projection
assumed that running the row loop in Rust would shrink the Python work
around each row's callbacks from 11.1 ms (A's Rust read included) to
about 4.6 ms: A's read 1.0 ms, the registry 0.4, the render id 0.4, the
checks and scope 0.5, normalizing the data and merging the template
globals 1.0, building the two records 1.0, and the Rust loop itself 0.3.
It did not shrink, because each row still called the same Python
functions (next subsection). That breakdown is the starting map for anyone
who moves those functions to Rust. The Python arms of B1 and C1 did better
than projected: batching alone removes more Python work than the
attribution suggested.

The effort estimate grew too. The core of Stage 2 was first put at 11.5
agent-days. The first plan review raised it to about 15.5, and the second
to about 20 by adding about 15% for unexpected findings (2.6 days), the
re-measured base and the reruns with the collector off; the Rust half of
C1 alone grew from 1.75 to 2.5 days. With C1b and C3 it was about 24. The
production plan for the five pull requests estimated 22.5 agent-days, or
about 26 with the same allowance.

### Levels dropped, and alternatives rejected

These are the options someone extending the levels is most likely to
propose again, with the reason each was not built.

- **C1 in Rust.** A Rust loop over a call run's rows, running each row's
  setup and data methods in today's order, was built and measured. It was
  no faster than the Python arm, and slightly slower on top of B1. Each
  row still calls the same Python functions. Rust looks each one up by
  name in `component_render`'s module globals on every call, about 25-30
  dict lookups per row, because Python resolves a global at each call and
  a test that patches the function must see the patch. The admission check
  is itself a Python call per row (`_simple_vue_admission_key`), because
  rebuilding its six reads in Rust would copy a Python rule. The gain
  comes from running a loop as one queue task, which the Python arm does
  too, so production C1 is Python only. A side benefit: it uses no Rust,
  so it runs on every interpreter. Moving the called functions themselves
  to Rust was not tried.
- **C1b, one run record instead of a record per row.** It would touch
  about 44 places across 9 files that check a record's type: the kind of
  spread that got a 3.8% gain rejected before (the "fused prepared-leaf
  occurrence ticket" in the decision ledger). Projected at 1-2 ms plus a
  collector effect, it was to be built only if C1's object counts showed
  the per-row records drive full collections. Those counts were never
  taken, and C1b was not built. C2 was also never timed on top of the Rust
  C1 arm, only on the Python one.
- **B3, feeding the hydration writer from Rust rows.** The writer parses
  the manifest JSON (about 2.4 ms). Projected at 0.5-1.2 ms, below the
  2 ms that 5 pairs can see. It also carries a quiet correctness risk:
  converting the values to `serde_json::Value` loses the float text that
  Python's `repr()` produced unless `arbitrary_precision` is on, and a
  mismatch shows up as a hydration mismatch in the browser, not as a
  server error. If the parse ever matters, the better route is a parse
  that reads the manifest text in place without converting it to
  `serde_json::Value`, so the writer keeps reading exactly the JSON the
  browser receives.
- **B4, joining the document in Rust.** It would replace `finalize`'s text
  searches with offsets recorded while writing. With A on, the document
  steps cost 6.1 ms (`finalize` 3.1, `typed_document_shell` 1.1,
  `emit_dependencies` 1.1). B4's gain beyond recording the same offsets in
  Python was projected at 0.5-1.5 ms, too small to see, and a Rust join
  would have to reproduce `_insert_default`'s text search exactly. A Python
  version must keep the 64 KB head scan limit (`_PRELOAD_HEAD_SCAN_LIMIT`,
  counted from the end of the inserted CSS) and every copy made before
  `on_serialize`, because that hook may replace the HTML.
- **The document shell in Rust.** `typed_document_shell` walks the Python
  render tree, so moving it means reading that tree from Rust. It stays in
  Python.
- **The full native scheduler** (ordinary components, slots,
  `provide`/`inject`, `on_render` generators, hook dispatch in Rust).
  After C2 the board's 16 ordinary components cost about 2-3 ms:
  `_render_one` 0.6 ms, their bodies about 1 ms, the rest of the queue
  about 0.5 ms, plus the hooks inside `_render_one`. So it saves 1.5-2.5 ms
  at best, for the largest contract change in section 6. The archived
  walker gained only 1.03x on a tree of small components, because building
  Python components dominates and that stays in Python. Not worth building
  for this page; a page with hundreds of ordinary components would need
  its own assessment.
- **Rust reads the whole finished render tree** (architecture B as first
  sketched in section 4). Tens of thousands of C API reads, and a copy of
  about 2,500 lines of `transform_component` rules, for 2-3 ms of
  ordinary-component assembly. B1 and B2 took the per-row and per-leaf
  parts instead.
- **Rust returns Python dicts or manifest dicts.** The same Python objects
  remain, so nothing is saved.
- **A lazy `dict` subclass for row values.** The C JSON encoder reads dict
  internals directly, and Citry checks `type(x) is dict` in many places.
- **Rust writes Citry's own row HTML** for static, fragment and declined
  outputs. It would copy Python's HTML rules for outputs that were not
  being measured; production rebuilds those rows in Python.
- **The parent loop runs each row's callbacks during its walk.** Rejected
  by the maintainer, because it changes the order in which user code runs.
- **Rust calls `_render_simple_vue_leaf` per row.** It saves only the queue
  work, about 1-2 ms, which the Python C1 already takes.
- **One nested render for a whole run.** It changes the shape of the parts
  list that assembly and serialize read, so the list keeps one entry per
  row.
- **One shared run object at every row position.** The research C1 did
  this. The production review showed that it renders different rows, or
  rows in a different order, when an `on_slot_rendered` hook reorders or
  drops the rows not yet placed, or when a template that holds the rows
  is printed a second time after some rows were placed. Production C1
  puts one small object at each row position, which the queue finds by
  identity, the same way it finds a component whose render waits for a
  later queue step.
- **Rust mints render ids.** About 0.5 ms, and a user `id_generator` may
  run, so ids stay in Python.

The production plan also rejected these ways of shipping the levels:
- an opt-in switch, off by default: users would not get the gain, and the
  suite would test the Rust path only when someone set it;
- one pull request for every level: about 10,000 changed lines and no
  point to bisect between levels;
- one switch per level: 32 combinations, of which one would be tested;
- Rust on PyPy and free-threaded builds: PyPy reads objects through a slow
  layer, and a free-threaded build needs locking around every container
  Rust reads;
- running C1 only when the Rust path is on: it would leave two schedulers
  to test;
- running the Python-path suite inside the local full profile: it would
  roughly double the longest local phase, so one CI cell runs it instead.

Each design also named the results that would show it was wrong, so a
later level can reuse the same checks:
- Stage 1: a byte difference that can be fixed only by copying a Python
  rule into Rust; a Python leaf built on the hydrated or `ssr=False` path;
  a call-count difference in a fault case; Rust costing more than 3 µs per
  row; Python's remaining per-row cost above 5 µs (this one fired, at
  about 7 µs); under 15% saved after Level 2; an Events update more than
  a few ms slower.
- B: the same byte rule; B1 saving under 3 ms, or costing more than
  1.5 µs per row in Rust; the Python control kept under the arm rule; any
  per-row `PreparedOccurrence` left on a hydrated page; a consumer that
  needs an exact `PreparedOccurrence` type; full collections not falling
  while object counts do.
- C: any difference in the order log, trace log, callback counts,
  exception, message or component path; a nested render that fails or
  panics; the Python arm kept under the arm rule (this one fired for C1);
  C1 saving under 3 ms; C2 needing any expression beyond names and
  constant subscripts to pay off; first load more than 4 ms slower. That
  4 ms comes from the plan's budget for building Rust plans on the first
  request: 1-3 ms for the B levels and 2-5 ms for B and C together.
- Production: a level's gain on current `origin/main` missing its
  threshold by more than a third; development mode becoming noticeably
  slower in a way that cannot simply be excluded; the coverage floor
  holding only if the Python-path cell's coverage is counted; the
  Pyodide wheel growing enough to slow the playground; the whole stack
  above 0.6 of `origin/main`'s warm time; the
  Python-path CI cell finding failures that the both-paths tests missed,
  more than once; the new tests costing much more than 30 s of worker
  time; the Python path with C1 slower than `origin/main` (it was, by
  0.9% at 140 rows); a bug in the first release that only the Rust path
  has and users cannot work around.

### Risks the research recorded, and how production handled them

The prototype recorded several risks without fixing them. Production
resolved each one as follows (details in `native_render.md` and in the
pull requests of each level):

- *Rows in the root template were evaluated twice* on hydrated and
  `ssr=False` pages. Fixed in the serializer before Stage 2
  ([#261](https://github.com/citry-dev/citry/pull/261)).
- *The assembly shortcut looked up the registry and the tag callback once
  per class per assembly.* Production level A checks every row against
  the registry, as the per-row path always has, and looks up only the
  component tag once per class per assembly. That is listed as an
  accepted difference: the path accepts only the built-in tag callback,
  which gives the same answer for every row. With B1
  ([#266](https://github.com/citry-dev/citry/pull/266)) the registry check
  runs once per call run, and B1 lists its own accepted difference for a
  class replaced on another thread during serialize.
- *The shortcut repeated the start of `transform_component`,* so a check
  added there later could miss Rust rows. Production makes both paths
  begin with one shared function, `start_occurrence` in
  `_vue/direct_capture.py`.
- *A lone surrogate in a call-run key.* The research fell back to Python
  for that row's ids; production does the same, inside a run whose other
  ids come from Rust.
- *Development mode.* The research still read rows in Rust there and then
  rebuilt them for the duplicate-`id` check. Production level A does not
  read rows in Rust in development mode at all. That choice was made by
  reasoning, not timed.
- *Test coverage.* The research ran only 45 of the 212 Python test files
  with Rust rows on, and excused 6 failing tests (3 assertions about which
  internal Python path ran). A change outside its test list broke 3 tests
  in `test_vue_migration_coverage.py`. Production runs every test on the
  Rust path, runs the row tests on both paths (`render_both`), marks the
  cache tests for the Python path, and moves one CI cell to run the whole
  suite on the Python path, because no CI job runs on PyPy, Pyodide or
  free-threaded builds, which always take it.
- *C1's shared run object at every row position* (see "One shared run
  object at every row position" above). Production C1 uses one object per
  row position.

### Traps found while building the levels

Reviews of the prototype and of the production pull requests found these.
Each one is easy to reintroduce in a new level, and most are invisible on
the board's own data.

- **A dict lookup can run user code.** Looking a key up in a dict calls
  `__eq__` on a stored key whose hash matches. So Rust reading plain data
  can still run Python code. A decline that repeats the reads repeats
  those calls. Python looks each scope name up once per path that reads
  it; level A looks each name up once and lists the lower `__eq__` count
  as an accepted difference (`native_render.md`, section 4), so a new
  level must either match Python or add itself to that list. The counts
  depend on the hash seed, so the research repeated that check 12 times.
- **Read order and read count are observable.** The C1 review found reads
  done in a different order from Python's (a flag that marks a dynamic
  component selector, read before the key; `class_id` before the method
  lookup; an extra truth test of `js_data`). Reads of class attributes and
  of Citry's own frozen records can keep their order and still differ in
  count; a user metaclass with a read hook would see that.
- **Call `Citry.get` for each row of a walked loop, not once per loop.**
  Today that per-row call raises `CitryLifecycleInProgress` when another
  thread changes the registry; one call per loop would hide it. (This is
  the walk's per-row lookup of the row's component, not the assembly
  registry check that B1 makes once per run.)
- **Registration order reaches the manifest bytes.** Registering a run's
  component definition before the run is known to succeed puts that
  definition earlier in the manifest than the per-row path would, or adds
  one the per-row path never registers (a row with `js_data`). Check every
  registry and map the run reads before registering anything.
- **Events updates need insertion order.** The page update after an
  Events action copies the data and encodes it with an unsorted
  `json.dumps`, so sorted JSON written by Rust cannot be spliced into it.
  That is why every level rebuilds rows for Events updates.
- **A lone surrogate in a template literal.** `#c-key="row['\ud800']"`
  made the C2 prototype raise `UnicodeEncodeError` on every render: a
  Rust `String` cannot hold it, and the error escaped the plan builder.
  Python's `ast` also kept U+D800 while the sandbox's expression rewriter
  turned the escape into U+FFFD, so the two paths would have read
  different keys anyway. The C2 review found that the split was wider: the
  expression sandbox read `'\ud800'` as U+FFFD wherever it ran, while the
  fast generated evaluator (`_simple_json_expr_from_ast` in
  `_vue/leaf_program.py`) and the unsandboxed path kept U+D800, so even an
  ordinary component's key depended on which evaluator its template got.
  The fix for [#280](https://github.com/citry-dev/citry/issues/280) went
  into the sandbox's rewriter: it writes such a literal from its source
  text, and C2 now turns each expression into a path from Python's parse
  alone. C2 and level A still refuse the key, because no Rust string can
  hold it.
- **Cache keys that compare equal but encode differently.**
  - `True == 1` in Python while their JSON differs, so a cache keyed on
    `DefinitionCompileInput` must not rely on `==` alone.
  - A component tag cache must leave a class with a custom metaclass
    uncached, and must keep a lookup that passes a class separate from
    one that does not.
  - A registry lookup can be deduplicated only per `(class_id, class)`
    pair, because a `Citry` subclass may override the lookup.
  - The lookup in `_render_simple_vue_leaf` must stay per row, because
    registration can change between rows.
- **The collector does not see a PyO3 class without `__traverse__`.** PyO3
  0.27 turns on garbage-collector support only for a class that defines
  it. That is safe for a class holding only strings and plain values; a
  class that holds Python callables or containers needs it, or a reference
  cycle through it is never freed.
- **Rust code that calls user code.** Hold no borrow across a Python call,
  keep per-run state local and the plan unchanging, because a callback
  may start a nested render that reaches the same plan. When Rust adds the
  component path to a row's error, it must make the row's error the
  exception being handled, so `__context__` chains match Python's, and
  restore it with a drop guard. A panic must still reach the reset of the
  execution scope, and an error from that reset must keep the row's error
  as its context. A `BaseException` that is not an `Exception` (such as
  `KeyboardInterrupt`) must pass unchanged, with no path, as Python's
  `except Exception` leaves it.
- **A Python constant copied into Rust makes a test compare Rust with
  Rust.** The prototype hard-coded the 32-entry spread layout cache; a
  test that set Python's limit to 0 then still passed. Pass such values in
  from Python.
- **A new kind of deferred part must make `_contains_deferred` true,** or
  a slot fill rendered by another component merges dependency records
  before its rows exist.
- **Replacing a built-in hook method turns hydration off,** because
  serialize checks the hooks' identity. That is why
  `tests/test_call_run_order.py` records hook calls with `sys.setprofile`
  instead of wrapping the hooks.
- **The Vue render parity recorder follows the manifest writer.**
  `scripts/vue_render_parity/collect.py` reads the manifest data and the
  definition ids that serialize writes. A level that changes how the
  manifest is written must update it too, or the parity check records
  pages without their data and reports no error.
- **Coverage does not count the Python-path CI cell.** Lines that only
  the Python render path runs need a `render_both` or
  `python_render_path` test to count toward coverage.
- **Build plans whenever the native path is supported, not only when it
  is on.** Plans are cached on template nodes, so a node first rendered
  while the native path is off (as when tests switch paths in one
  process) would otherwise cache "no plan" and keep later Rust-path
  renders on Python. That is why `native_render.py` has
  two flags: plans follow `SUPPORTED`, and each call site reads `ACTIVE`.
- **Data passed from render to serialize goes in `_PreparedResult`
  fields,** not in `context.extra`: serialize clears its note keys there
  (`SERIALIZATION_NOTE_KEYS`) on every call, so such data would not
  survive a second serialize.

## Prior art

These are the files, tests and records searched, and what already exists.

**Design records**

- [`rust_rendering.md`](rust_rendering.md) records the target boundary.
  - Rust would own scheduling, per-render storage and output, and call Python
    only for effects (`:13-15`).
  - It names two conditions for this: "batching data must not reorder
    effects" and "Native ownership must be real, rather than two live object
    graphs" (`:15`).
  - It also requires that no fallback replay a callback after partial native
    execution (`:17`).
- [`performance_architecture_experiments.md`](performance_architecture_experiments.md)
  holds the measured experiments in its decision ledger table. Six rejected or
  deferred entries are close to steps this note discusses:
  - A Python writer that turned leaf data straight into JSON was 3.3% slower
    (`:198`).
  - Direct emission of finished occurrences was deferred because "a general
    final-occurrence writer needs a separate contract" (`:199`).
  - Letting assembly adopt `server_data` removed one
    `json.loads(json.dumps(...))` round trip and was flat (`:178`).
  - Three other experiments that each removed one Python step (`:173`,
    `:175`, `:179`) were flat or slower.

  The pattern is that removing one copy or object at a time in Python gains
  little. That is evidence about how much "removing work" is worth.
- The archived design (`git show b7b2f4e:docs/design/render_plan_rust.md`)
  covers two things this note needs. Lines 191-217 list every call a native
  scheduler must make back into Python. Lines 44-51 give the speed of an
  isolated Rust walk over Python's: about 1.3x for interpolation and control
  flow, 1.8x for attributes, and 1.03x for a tree of small components.
- [`vue_optimization_rollout.md`](vue_optimization_rollout.md) holds the
  current performance checkpoint (`:58-83`) and the row writer measurements
  (`:131-190`).

**The archived Rust body walker.** It is called `BodyEngine` with a
`FoldedPlan`. It landed in commit `b7b2f4e66` and was removed in `60e19804f`,
both on `origin/main`. It walked a component body in Rust and reached only
parity on a real page, 12.5 to 12.7 ms.
- Its first version read the Python body list item by item from Rust. It
  was 3-6% slower: "the per-item `get_item`/`isinstance` crossings cost more
  than the string work saved" (`docs/design/performance.md:550-555`).
- On a tree of small components it gained 1.03x, and on the real page it
  reached 0.98-1.0x (`performance.md:550-551`). The board's 1,400 rows are
  small components.
- The fix was to convert the body into Rust-owned data once, so the walk no
  longer read Python objects.

Row data changes on every request and cannot be converted once. **So any
design where Rust reads row data from Python objects reuses the mechanism that
lost.** Whether it loses again depends on how much Python work each read
replaces. That is the first thing to measure. A Python-to-Rust call costs
about 177 ns (`performance.md:358-363`, timed with one `mark_html` call).

**Rust that already runs on every hydrated request.**
- `crates/citry_vue_compiler/src/server_render.rs` turns each compiled Vue
  render function into a program, once per definition (`read_program`, `:303`).
  Once per page, `render_for_hydration` (`:2102`) parses the manifest JSON that
  Python built (`:2103`). It then writes every row's HTML with no calls back
  into Python (`Writer::list` `:2618`, `Writer::component` `:2989`).
- The PyO3 wrapper releases the GIL while this runs
  (`crates/citry_core_py/src/vue.rs:120-129`). Python calls it once
  (`packages/py/citry/citry/_vue/serialization.py:436`).
- At 1,400 rows the call takes 10.0-10.6 ms: about 2.4 ms to parse the
  manifest, 6.5 ms to write HTML and 1 ms to check the tokens
  (`docs/design/vue_board_hydration_plan.md:330-332`).

**Other Rust on the path.**
- The template compiler (`crates/citry_template_parser/src/compiler.rs`)
  produces Python source once per template. Python runs it with `exec` and
  caches the result (`packages/py/citry/citry/component_render.py:2590-2679`).
- The board renders in the compiler's *prepared* mode, whose output keeps
  each element as typed data for the Vue path instead of an HTML string. That
  form comes from `compile_prepared_template` (`compiler.rs:141-159`), which
  calls the private `compile_template_body_with_mode` (`:203`) and supports
  Python only. The public language-neutral `compile_template_body` (`:199`) is
  the HTML-mode form. A Rust render plan would need the prepared form in the
  language-neutral output first.
- `python_safe_eval` rewrites each expression once, on first use, and the
  result is cached on the node
  (`packages/py/citry/citry/nodes/__init__.py:693-694`). Every later evaluation
  is plain Python with sandbox checks
  (`packages/py/citry_core/citry_core/safe_eval/eval.py:176-231`).
- `mark_html` runs once, for the root frame
  (`packages/py/citry/citry/serialize.py:696`).

**What Rust does not have.** No Rust structure on `main` holds a scheduler
for Citry templates or a plan for running one. The nearest structures are the
per-definition Vue programs and the per-call occurrence table in
`server_render.rs` (`:86`, `:959-978`). The `citry_ownership` crate held a
component relationship table keyed by integer ids, until the Vue migration
(`ff78430ac`) replaced that design. It is evidence that a table independent
of the host language can work. A new crate would start from today's `main`.

**The PyO3 surface** (`crates/citry_core_py/src/lib.rs:49-211`, mirrored by
hand in `packages/py/citry_core/citry_core/_rust.pyi`). It exposes the
`template_parser`, `vue`, `html_transform`, `i18n`, `safe_eval` and
`template_formatter` submodules. Only one function takes page data and returns
rendered output: `_render_for_hydration`, which takes a JSON string.

**Interpreters citry-core ships for.** It ships CPython wheels for the
stable ABI, a free-threaded CPython 3.14 wheel (`cp314t`) and a PyPy 3.11
wheel (`.github/workflows/py--citry-core--publish.yml:98-172`), plus a Pyodide
build for the browser playground (`:423-430`). A design that reads Python
objects from Rust must work on all of them.
- On `cp314t`, `lib.rs` declared the module with a bare `#[pymodule]` and no
  `gil_used = false` (`crates/citry_core_py/src/lib.rs:49`). Under PyO3's
  default, the free-threaded interpreter then turns the GIL back on when the
  module loads. That was not checked at runtime. A design that wants parallel
  requests there must opt out and lock shared Python objects itself.
  (Production level A declares `#[pymodule(gil_used = true)]` and keeps the
  native path off on free-threaded builds; see `native_render.md`.)
- On PyPy, every C API call goes through an emulation layer, `cpyext`, which
  is far slower.

## 1. Where server time goes today

### The page

The board app (`benchmarks/web/apps/citry/app.py`) has 16 ordinary
components and N `ProjectOutput` rows, where N is 14, 140 or 1,400. Only the
row is instance-free (`app.py:113-134`). Rows come from one loop per phase, in
`benchmarks/web/apps/citry/phase_group.html:7`:

```citry-html
<c-ProjectOutput
  c-for="row in phase['outputs']"
  #c-key="row['id']"
  c-row="row"
/>
```

A typical row has about 22 elements and 11 top-level server expressions:
dictionary lookups on the row, one attribute spread of `row_attrs`, and two
`c-if` tests. Rows with dependencies or attachments add three nested `c-for`
loops, each with 4-7 more expressions, and one conditional expression. A row
also has 3 browser bindings (`@click`, `:aria-expanded` and `v-show`). Its
only user code is a static `template_data` that builds a 3- or 4-key
attribute dictionary (`app.py:122-131`). The engine uses default settings and
no user extensions.

### The recorded totals at 1,400 rows

All in ms. "Prepare" is the `Server-Timing` span around
`render().serialize()` (`benchmarks/web/apps/citry/app.py:279-280`).

| Measure | First load | Second load | Source |
|---|---:|---:|---|
| Server prepare | 157.7 | 110.3 | benchmark run `20260927T232351Z-6a10df61` (2026-09-27) |
| Server prepare, 0.6.0 wheels | 169.3 | 117.7 | run `20261016T141751Z-7ed90531`, n=1 (a qualification run, which checks every app's output before a measured run) |
| Browser time after the response | 173.4 | 165.9 | run `6a10df61` |
| Request to layout | 359.2 | 304.1 | run `6a10df61` |

Warm figures, measured outside the load sequence:

| Measure | ms | Source |
|---|---:|---|
| Render + serialize, in process | 52.4 + 60.6 | `vue_optimization_rollout.md:181` |
| Prepare through the real server | 105.6 (min 94.2, max 109.4) | an earlier islands research run |

The projections below use the 2026-09-27 run, because it is the one cited in
#144. Stage 0 could not reproduce the 0.6.0 release run's slower first load
outside the release harness (see "The 0.6.0 first-load step"), so this note
keeps the Sep 27 base.

What the totals show:

- **The server is where Citry trails.** In the same run, Nuxt's browser time
  after the response is 169.0 / 157.9 ms, close to Citry's. Nuxt's whole
  server request is 81.4 / 21.8 ms against Citry's 157.7 / 110.3. Making the
  server faster is the right lever for request to layout.
- **The first load costs 42-47 ms more than the second** at 140 and 1,400
  rows in run `6a10df61`, and 51.6 ms at 1,400 rows with the 0.6.0 wheels. At
  14 rows the gap is 83-85 ms. That comes from qualification run
  `20261016T141751Z-7ed90531` (0.6.0 wheels) and from run
  `20261019T203419Z-3ebc8934`, which was still in progress and is not
  confirmed to use the 0.6.0 wheels. The extra is
  inferred to be the first
  request compiling templates and Vue definitions, generating and `exec`-ing
  the row evaluator, creating classes, and importing modules lazily. The
  issue's "45-65 ms" figure appears in no recorded file. At 140 rows about
  42 ms of the 57.8 ms first load is this one-time cost. So one third is out of
  reach there on first load, whatever happens to rendering.
- **Hydration adds about 12-16 ms of server time** at 1,400 rows, and saves
  about 34 ms of browser work plus 59 ms of layout
  (`vue_optimization_rollout.md:79-81`).

### The render path, step by step

The entry point is `Page(session=...).render().serialize()`
(`benchmarks/web/apps/citry/app.py:280`).

**Render, about 52 ms warm.** `render_impl`
(`packages/py/citry/citry/component_render.py:789`) runs a last-in,
first-out work queue (`_settle_render`, `:941`).

1. **Ordinary components, 16 per page.** `_render_one` (`:1690-2184`) does
   the following for each one:
   - creates the instance;
   - builds the `Kwargs` and `Slots` objects and a `CitryContext`;
   - calls `template_data`, `js_data` and `css_data`;
   - runs `on_component_data` with 3 built-in hooks, and later
     `on_render_context_merge` (`packages/py/citry/citry/extension.py:2083`,
     `:2114`). The Events hook signs the Board's state token here, at render
     time (`packages/py/citry/citry/ext/events/emission.py:37-58`);
   - walks the compiled body node by node (`_render_body`, `:2750-2807`).

   `Board.template_data` calls the model's `snapshot()`, a full
   `dataclasses.asdict` of the board. That is user code and costs an estimated
   5 ms. NotePanel and ProjectInfo render as leaf programs (one Python object
   that evaluates a whole template body containing no component calls) over
   about 1,200 notes and comments. The Events attribute hook keeps them off the
   fast generated evaluator (`_vue/leaf_program.py:2397-2405`). They cost an
   estimated 8 ms, from 4 calls and about 23 ms under cProfile, which inflates
   times about 2.9x.
2. **The parent loop, once per row.** `PhaseGroup`'s `c-for`
   (`packages/py/citry/citry/nodes/__init__.py:2176-2233`) does the following
   for each row:
   - copies the variable mapping and builds a new context;
   - evaluates `row['id']` through the sandbox for the key;
   - leaves one `DeferredComponent` (`nodes/__init__.py:1575-1682`).

   That comes to about 11 Python objects and 2 registry-lock round trips per row
   (unproven).
3. **The row, 1,400 times.** The queue pops one task per row, in source order
   (`component_render.py:1182-1243`). `_render_simple_vue_leaf` (`:535-697`)
   does the following for each row:
   - re-checks that the class may still render without an instance (a 6-part
     key, `:190-220`);
   - mints a render id;
   - builds the `Kwargs` object;
   - calls the user's `template_data`, then `js_data` and `css_data`, in that
     order (`:613`);
   - merges the template globals into the variables (`:630-638`).

   Then `LeafProgramNode.render_static_instance_free` (called at `:642`;
   `_vue/leaf_program.py:2336-2376`) runs two functions that were generated
   once per template. The first checks that every value the template reads is
   plain data. If not, it raises `TypeError`, and no other path runs (`:2353-2355`;
   test `packages/py/citry/tests/test_simple_vue_mode.py:558-576`). The second
   records each text, attribute, chosen branch and loop item. No extension
   hook runs per row.

The closest recorded breakdown of render time is from 2026-09-25, before two
later changes:
- hydration was turned on;
- row HTML moved out of render into a writer that a hydrated page never calls,
  which saved about 11 ms (`vue_optimization_rollout.md:186-187`).

In that run, `_render_simple_vue_leaf` took 32.8 ms inclusive across 1,415
calls. The check, the evaluator and the attribute spread inside it took
19.7 ms together, and `Kwargs` construction took 2.9 ms
(an attribution run from the Vue architecture experiments).
Inclusive times overlap and must not be added. Everything outside the row
call took 18.6-21.3 ms. The 19.7 ms still included writing each row's HTML
(the profile shows 1,400 calls of the `_row_*` HTML helpers), which today's
hydrated page skips. So today's check, recording and spread are likely about
9-14 ms (unproven).

**Serialize, about 61 ms warm.** `serialize_render_result`
(`packages/py/citry/citry/serialize.py:507`) runs these steps:

1. **Assembly, once per occurrence.** `assemble_typed_render`
   (`_vue/direct_capture.py:361`) runs a nested `transform_component` 1,416
   times (`:678`). For each row it:
   - copies the recorded values;
   - computes 2 placement digests (SHA-256 hashes of a `json.dumps`, `:1568-1570`
     and `_digest` at `:2766`). These give the row its ids in the manifest:
     about 2,800 per page, all with distinct inputs, costing about 5.8 ms on an
     older path (an earlier digest profile).

   `PreparedOccurrence._from_assembly` then round-trips each occurrence's
   server data through `json.loads(json.dumps(...))`
   (`_vue/prepared.py:240-251`).
2. **Vue definitions, per request.** `NativeCompiler.compile`
   (`_vue/compiler.py:~460-505`) rebuilds its cache key for about 11
   definitions on every request. This costs under 1 ms. Rust compiles only on
   a cache miss.
3. **The manifest.** `_prepare_holding_assets`
   (`_vue/events.py:590-1078`):
   - builds one dictionary per occurrence (`_vue/protocol.py:158-170`);
   - loops over all occurrences about 4 times;
   - resolves the 1,400 dependency records;
   - publishes assets to the cache backend.

   `_script_json` then encodes the manifest with the standard library's
   `json.dumps` (`_vue/serialization.py:1128`; `util/html.py:166`). Encoding the
   whole 1,400-row page data costs about 3.1 ms
   (an earlier islands research estimate).
4. **The hydration HTML.** The one Rust call described above: 10.0-10.6 ms.
5. **Document assembly.** `typed_document_shell` (`_vue/document.py:25`)
   walks the tree again. `emit_dependencies`
   (`ext/dependencies/emission.py:150-274`) walks it once more and resolves
   dependency records a second time. `vue_plan.finalize`
   (`_vue/serialization.py:597-735`) lower-cases the configuration script for
   a validity check (`ext/dependencies/types.py:179-185`) and copies the full
   document twice. Serialize also runs the extension hooks
   `prepare_browser_render`, `browser_plugin`, `on_dependencies` and
   `on_serialize`. `on_serialize` receives the finished HTML and may replace it
   (`packages/py/citry/citry/extension.py:543-561`, `:999-1020`).

About 10.5 ms of serialize is Rust, about 3 ms is `json.dumps`, and about
6 ms is digests. Before Stage 0, the other roughly 40 ms of Python had
never been broken down. Stage 0 now breaks it down.

### Warm budget at 1,400 rows

This table assembles figures from different runs, so it maps where work
happens. It is not one measurement. The columns ask which architecture in
section 4 could move each item.

| Work | ms (approx.) | A + B can move it | Only C can move it | Stays |
|---|---:|:--:|:--:|:--:|
| User code: board snapshot, row and other `template_data` | 7-9 | | | ✓ |
| `Kwargs`/`Slots` schema construction | 3-4 | | | ✓ |
| Rust hydration HTML | 10-10.6 | | | ✓ (already Rust) |
| Row check, recording, attribute spread | 9-14 (unproven) | ✓ | | |
| NotePanel and ProjectInfo leaf evaluation | about 8 (unproven) | | ✓ | |
| Parent loop and ordinary component setup and hooks | 6-10 (unproven) | | ✓ | |
| Assembly, digests, manifest building and encoding | 30-35 (unproven) | ✓ | | |
| Asset publishing, document assembly, copies | 8-12 (unproven) | mostly | | some |

The listed rows sum to about 81-103 ms. The rest of the roughly 110 ms is
unattributed, and this note counts it as movable, which favors the
hypothesis.
- **What stays:** the "stays" rows total 20-24 ms, and with part of the last
  row about 22-27 ms. That is s ≈ 0.20-0.25 of 110 ms.
- **With A and B alone:** the "only C" rows (14-18 ms) stay as well, so about
  36-45 ms remains in Python, s ≈ 0.33-0.41.

Garbage collection adds
uncertainty. An older version of this path spent 11-17% of a 1,400-row render
in garbage collection (`performance_architecture_experiments.md:197`).
Moving work to Rust also removes Python objects. Before Stage 0, the current
path had no garbage-collection measurement. Stage 0 now measures it.

### What this means for the one-third hypothesis

This subsection is the estimate made before Stage 0. Stage 0 measured
r = 0.074 for the row work, far below the ratios borrowed here from other
engines. The projections in "Stage 0 results" replace the ones below, which
stay as the record of the reasoning.

Two numbers decide the outcome. One is **s**, the share of warm time that
stays in Python or is already Rust. The other is **r**, what Rust spends on
the moved work as a fraction of the Python time it replaces. The warm time
after the change, as a fraction of today's, is:

```text
T = s + r × (1 − s)
```

Evidence for r:

| Comparison | r | What it models |
|---|---:|---|
| Rusty Templates against Django templates, render span, same board | 0.21-0.24 | Rust against an *interpreted* Python engine (run `6a10df61`) |
| Rusty Templates against Jinja2, same board, same span, warm loads | 0.84-0.85 | Rust against *compiled* Python templates. Citry's row evaluator is generated Python, so this is the closer match. The first-load figure (0.63) includes Jinja2's own compilation. |
| Citry's archived Rust body walk against the Python walk, isolated | 0.56-0.77 | Citry's own templates: interpolation, attributes, control flow (`render_plan_rust.md:44-51` at `b7b2f4e`) |
| The same walker on a tree of small components, and on a real page | about 0.97-1.0 | Python still built every component (`performance.md:550-551`) |
| Work that is already C inside CPython (`json.dumps`, SHA-256, string copies) | about 1.0 | Rust cannot make C much faster. Only removing the work helps. |

(Rusty Templates is `django-rusty-templates`, a Rust implementation of the
Django template language. The benchmark runs it with the same template and the
same measurement span as the Django and Jinja2 apps.)

Removing work outright, such as intermediate records, repeated tree walks and
copies, could push r below these speed-up figures. Nothing measured shows
this, though: the decision ledger shows Python-side removals one at a time
were mostly flat. How much Rust ownership removes at once is unknown, which is
why r must be measured. Part of the moved work is already C inside CPython,
with r ≈ 1 unless it is removed. So a single r for all moved work flatters
the result. Stage 0a splits the two.

Projected warm time, with today's warm base at about 110 ms:

| Architecture | s | r = 0.25 (no evidence) | r = 0.56 | r = 0.85 |
|---|---:|---:|---:|---:|
| A + B | 0.33-0.41 | 50-56% | 71-74% | 90-91% |
| C | 0.20-0.25 | 40-44% | 65-67% | 88-89% |

One third needs s below 1/3 and r ≤ (1/3 − s)/(1 − s). With C, that is
r ≤ 0.11-0.17. With A + B it needs r ≤ 0.01 or is impossible, because s may
already be above 1/3. **No comparable measurement reaches r = 0.17.** With the
evidence-supported range r = 0.56-0.85, the warm time lands at 65-89% of
today's with C (an 11-35% cut, about 12-39 ms), and at 71-91% with A + B
(a 9-29% cut). Both are upper estimates, because they apply r even to work
that is already C. They are unproven.

The same savings applied to the benchmark's totals (C, 12-39 ms):

- **Second load, request to layout:** 304.1 → about 265-292 ms. On the same
  load Rusty is 293.9, Jinja 295.1 and Nuxt 211.3.
- **First load:** the one-time cost stays, so the same saving applies.
  359.2 → about 320-347 ms, against Rusty 313.3, Jinja 315.2 and Nuxt 269.8.
- **The #144 projection:** 265/252 ms at 1,400 rows, "possibly 245/232", from
  the maintainer's handoff notes of 2026-09-28. They record no
  derivation. Subtracting 65% of the recorded server time
  reproduces only the 232 ms second-load alternative
  (304.1 − 0.65 × 110.3 = 232.4).

**The board is the friendliest case.** Its rows carry plain data, with no
slots, no hooks and no Python instance. A page built from many ordinary
components spends its time building Python component objects and running
hooks. The archived walker could not remove that cost. Only architecture C
addresses it.

## 2. Two consequences of what Rust already does

- **Python encodes the browser data, and Rust then parses it back.**
  Python builds the manifest as dictionaries and encodes it to JSON. Rust
  parses that text again to write the HTML. A Rust producer could keep the
  values in Rust and skip the parse, but only about 2.4 ms of the 10.5 ms call
  is parsing. The JSON must still be written for the browser.
- **The Rust HTML writer follows Vue's rules, not Citry's.** It is checked
  against Vue's own `renderToString` (`scripts/vue_render_parity/check.py`).
  Static and fragment output, and pages where hydration declines, use Citry's
  own row HTML format, which Python writes today (for the decline fallback,
  `packages/py/citry/citry/serialize.py:775-786`). A Rust producer
  that serves every output kind needs both formats, or must hand the values
  back to Python's writer.

Side findings, not fixed here:
- `_rust.pyi` declares five i18n `format_*` methods inside
  `class template_parser`, where they do not exist (still true at
  `88d7e4869`).
- `crates/citry_vue_compiler` has no `AGENTS.md`.

## 3. What must stay in Python, and how Rust can receive the data

| Stays in Python | Why |
|---|---|
| `template_data`, `js_data`, `css_data`, `on_render`, Events handlers | User code. Call order and call count are part of the contract. |
| `Kwargs`/`Slots`/data schema construction | Schemas may carry factories and validators that run user code (`packages/py/citry/citry/constness.py:752`). |
| Expressions over values that are not plain data | They may call `__getitem__`, `__html__` or properties on user objects. The sandbox checks live types. |
| Extension hooks | Python contracts. A third-party extension that overrides a per-component hook already forces rows off the instance-free path (`component_render.py:481-509`). |
| Slots and `provide`/`inject` | Slot content renders lazily inside the receiver (`nodes/__init__.py:452-480`), and `inject` reads values set by Python calls. |
| i18n | Lookups go through the active catalog and locale. The Rust formatter is already called per message. |
| Output caching (`Cache` extension) | Keys and storage backends are Python objects. |
| Error messages | They must carry the same component path and source position as today (`component_render.py:691-697`). |
| Events state signing (render time), asset publishing (serialize time), id generation | Signing uses the engine secret, and publishing writes to the Python cache backend. A user `id_generator` may run, so ids are minted in Python, in order. |

**How Rust can receive row data.** There are two ways:

1. **One Rust call per row, at the point where Python runs its plain-data
   check today.** That is after `template_data`, `js_data`, `css_data` and the
   template-globals merge (`component_render.py:613-642`). Rust reads the
   merged variables through the C API, checks types, and copies the values it
   needs into Rust-owned storage. The call order and the error path match
   today's. Copying at that point also means a later row's user code cannot
   change an earlier row's output.
   - *Cost:* 1,400 calls at about 177 ns each is about 0.25 ms. The C API reads
     are the unknown, because this is the mechanism the archived walker lost
     with. Each read is a C function call, expected to cost tens of
     nanoseconds on CPython (unproven). At about 30 reads for a row without
     nested lists, that is roughly 1-2 ms per page. Rows with dependencies and
     attachments need more.
   - *Other interpreters:* if the module opts out of the GIL on `cp314t`, the
     reads need per-object locking (`PyDict_GetItemRef` or critical sections).
     On PyPy they go through `cpyext` and are likely too slow, so PyPy should
     keep today's Python evaluator, chosen once at startup.
2. **Python encodes, Rust parses.** Python's C-coded `json.dumps` encodes each
   row's checked values, and Rust parses the text. This avoids per-field C API
   reads and works the same on every interpreter. Encoding the whole page's data
   costs about 3.1 ms, so this is a credible alternative. Which option is
   cheaper is exactly what Stage 0 measures.

Batching rows into one call per loop looks cheaper, but it changes behavior.
All of a loop's `template_data` calls would run before any row is checked. So
a bad row would surface after more user calls than today, and a reused
dictionary could change earlier rows. It also needs the queue to look ahead
over row tasks. The per-row call avoids all of this, for about 0.25 ms.
(C1 later batched a loop's rows differently: one queue task that still
runs each row's callbacks and checks in today's order, so none of these
problems arise. See "Stage 2 results" and the callback-order decision in
section 7.)

**The ordering rule.** Rust may run ahead only over plain data. When the next
step needs an effect, Rust either returns control to Python in that order or
never takes the row. A row is never partly written by Rust and then re-run in
Python, because that would call user code twice (`rust_rendering.md:17`).

## 4. Candidate architectures

There are three, from smallest to largest. Savings are estimates from
section 1, and none is measured.

### A. A Rust row producer for plain-data instance-free rows

**What moves.** For each instance-free row, Rust takes over where Python
runs its plain-data check today, after the row's data methods and the
globals merge:
- the plain-data check, using the live scalar set Python passes in;
- the template's lookups;
- the row's manifest entry, written as JSON text, including its placement
  digests;
- the values, kept for the hydration writer.

Python still runs the scheduler, ordinary components, the parent loop, id
generation and `template_data`.

**What crosses the boundary, and how often.** One call per row (1,400 per
page), with a Python record per row holding a handle to the Rust data. Each
row's dictionary is read through the C API, or passed as JSON (option 2 in
section 3).

**Expected saving (paper estimate, before Stage 0; see Stage 0 results for
the projection from measurements).** The row work (9-14 ms) and the row share of assembly
and manifest building (an estimated 15-20 ms), so 24-34 ms is moved. At
r = 0.56-0.85, that is a net saving of about 4-15 ms, or 3-14%.

**What gets harder.**
- **Two object graphs.** The Python graph stays: a `CitryElement`,
  `DeferredComponent` and record per row, beside Rust records with their own
  lifetime. That is what `rust_rendering.md:13-15` says to avoid. A is
  therefore a stepping stone and a measurement, not the target design. Shipping
  it would be an explicit exception that needs the maintainer's decision.
- **New record kind.** Every consumer must handle the Rust-backed record:
  - assembly, the manifest and the hydration writer;
  - the hydration decline fallback, which rebuilds row HTML in Python
    (`serialize.py:775-786`);
  - documents with CSP, a JavaScript policy, script integrity, or
    `deps_position` other than `"smart"`, where Python writes row HTML
    (`_vue/serialization.py:1129-1141`);
  - `ssr=False`, static and fragment output;
  - the page update the server sends after an Events action, built by
    `DirectVueEventsProducer.prepare_from_render` (`_vue/events.py:543`);
    every board action re-renders the whole Board;
  - output caching and serializing one render twice.

  A 3.8% gain was rejected for this cost before: a new record type spread
  across seven files (`performance_architecture_experiments.md:193`).
- **Byte-identical output.** Rust's JSON must match Python's: sorted keys,
  ASCII escaping, the `<` escape and float `repr`. It must also follow Vue's
  attribute value rules (`_vue/json_data.py:62-118`):
  - integers beyond ±(2^53 − 1) become strings;
  - the integer digit limit applies;
  - floats, lists and dicts become their Python `str` text;
  - `__html__` values are decoded.

**Error modes.**
- *Not plain data, or a missing key, or a non-finite float.* Today all three
  raise the same `TypeError` ("template data is not safe for the context-free
  evaluator"), with the component path, after exactly one call each of
  `template_data`, `js_data` and `css_data`.
  Rust must return a code so Python raises that same error. A fallback to the
  general evaluator would be a new behavior and a contract change.
  (Production level A declines such a row, and the same generated Python
  evaluator then runs and raises its own error.)
- *The live scalar set changed.* For example, `ComponentLike.register(str)`.
  Python passes the set, or the `abc.get_cache_token()` value it is keyed on,
  with every call, so Rust never uses a stale list. A test locks this
  behavior (`packages/py/citry/tests/test_simple_vue_row_caches.py:442-476`).
- *A string with a lone surrogate.* It cannot be borrowed as UTF-8.
  Stage 1 measured that on both paths serialize raises
  `UnicodeEncodeError`, and the Stage 2 B2 review found that this holds
  for every output that writes HTML, so only `ssr=False` gets through. Rust declines such a row, so Python raises
  that same error.
- *Engine state changed since the plan was built,* such as the extension set
  or the cache revision. Today a change to the 6-part key rebuilds the
  class's record of whether it may render without an instance
  (`component_render.py:223-230`). A new hook or configured i18n then sends
  the row to the ordinary path before any callback runs (`:596-599`). Only an
  unsupported class shape raises (`:580-582`). The Rust row plan must be keyed
  on the same 6-part key, or it goes stale when Python rebuilds that record.
- *Rust panics.* PyO3 raises `PanicException`, which derives from
  `BaseException`, so Citry's `except Exception` error attribution would miss
  it. The wrapper must convert it to an ordinary exception with the component
  path, and return no partial output.
- *Free-threaded CPython or PyPy.* See section 3. The interpreter choice is
  made once, before any rendering.

### B. A Rust serializer over the finished render tree

**What moves.** Everything after render that does not run hooks:
- assembly;
- digests;
- building and encoding the manifest;
- the hydration HTML (already Rust);
- the document shell.

Python render is unchanged.

**What crosses the boundary, and how often.** Two calls per page. Rust reads
the Python render tree through the C API: 1,416 occurrence records and their
recorded values. That is tens of thousands of reads (unproven count, it
depends on the nested lists). This is the read pattern that lost before, and
it is unproven here. `prepare_browser_render` needs the assembly's map from
renders to occurrences (`_vue/events.py:688-696`), so the order is:

1. Python decides whether Rust can handle the page, from facts known before
   any hook runs: record kinds, policy mode and the installed hook set. A
   decline here means the Python serializer runs, and no hook runs twice.
2. Rust assembles the occurrences and returns the map from renders to
   occurrences.
3. `prepare_browser_render` and `browser_plugin` run in Python.
4. Rust builds the manifest, including their contributions, and writes the
   output.
5. `on_dependencies` and `on_serialize` run on Rust's output in Python. Asset
   publishing stays in Python.
6. `finalize` runs.

On a hydrated page these browser hooks are already limited to built-in,
unconfigured i18n (`_vue/serialization.py:367-379`), so on the board they do
nothing.

**Expected saving (paper estimate, before Stage 0; see Stage 0 results for
the projection from measurements).** The Python assembly and manifest work (30-35 ms) plus
part of document assembly, so 35-43 ms is moved. About a third of that is
already C code, where r ≈ 1. Applying r = 0.56-0.85 to the remaining 23-29 ms
gives a net saving of about 4-13 ms, or 3-12%.

**What gets harder.** The Rust walker depends on the private layout of
Python's render records, so every change to a record becomes a cross-language
change. Serialize has three output kinds (document, static and fragment), and
policy checks that scan the HTML. Each needs a Rust version or a decline.

**Error modes.**
- *A record kind Rust does not know,* such as one from an extension, a
  `<c-raw>` block or an output-cache replay. Python declines in step 1,
  before any hook runs.
- *A policy mode that needs a full HTML scan.* Run Rust's existing
  `scan_output_html` on the output, or decline.
- *Free-threaded CPython and PyPy,* as for A.

### C. A native scheduler that calls Python for effects

This is the target in `rust_rendering.md`.

**What moves.** Rust keeps the compiled render plan and owns:
- the work queue;
- loop and branch selection;
- slot relationships;
- occurrence identity;
- per-render storage;
- HTML and manifest output.

Python is called for effects only: user callbacks, schema construction,
expressions over values that are not plain data, and hooks.

**What crosses the boundary, and how often.** At least one Python call per
row, if one helper runs `template_data`, the `Kwargs` construction and
render-id minting together. Otherwise two to three per row, about
2,800-4,200 per page. The 16 ordinary
components add about 100-130 calls for their data methods, schemas,
`on_render` and hook dispatches, before slots and `inject`. Values that are not
plain data stay Python handles.

**Expected saving (paper estimate, before Stage 0; see Stage 0 results for
the projection from measurements).** Everything in A and B, plus the parent loop, the NotePanel
and ProjectInfo leaves (which need the Events attribute hook classified), and
part of ordinary component setup. At r = 0.56-0.85, the net saving is about
12-39 ms, or 11-35%. This is the only option that could approach one third,
and only with r ≤ 0.11-0.17. It is also a step toward the planned JS, PHP and Go
bindings ([issue #27](https://github.com/citry-dev/citry/issues/27)).

**What gets harder.** Nearly everything in section 6:
- hook dispatch order;
- `on_render` generators that pause and resume;
- lazy slot rendering inside the receiver;
- `provide` and `inject`;
- output caching and its replay;
- error attribution.

Extensions would also need a declared kind for each hook (`rust_rendering.md:17`):
- observer hooks, which cannot change output;
- hooks that change only named fields;
- hooks that may replace anything.

Pages that use a hook of unknown kind need the Python scheduler, so Citry
would maintain two schedulers.

**Error modes.**
- *A hook of unknown kind.* The component takes the Python path, decided
  before any of its user code runs.
- *A callback raises.* Rust stops, drops the per-render storage, and re-raises
  with the component path.
- *A callback starts a nested render.* It re-enters Python rendering, which
  needs a re-entry guard or the existing rule that a nested `render()` starts a
  new tree.
- *Threads.* Rust may keep Python references while it releases the GIL, but it
  cannot touch them, so effect calls run one at a time under the GIL, as
  today. If the module opts out of the GIL on `cp314t`, calls can run in
  parallel and shared values need locking.
- *Pyodide.* The browser build has no threads. Whether the native scheduler
  behaves the same there is unproven.

### Python-only cleanup, as the comparison baseline

Some Python serialize work could be made cheaper in Python alone:
- the second dependency-resolution pass;
- repeated tree walks;
- full-document copies;
- the lower-casing of the configuration script.

The digests produce ids the browser protocol uses, so they can be made cheaper
(one hash per row, or a cheaper encoding of their inputs) but not dropped
without changing the id scheme. Given the flat single-cut results in the
decision ledger, 5-10 ms looks plausible (unproven). Any Rust result should be
compared against this cleaned-up Python, or reported as an upper bound that
includes removable Python work.

## 5. Recommended first step

**Status:** Stage 0a and Stage 0b ran on 2026-10-20. The results and the
decision they give are in "Stage 0 results" near the top of this note. One
third is ruled out on present evidence, and the projected saving for C is
above 25%, so Stage 1 ran for the smaller goal with the maintainer's
agreement. Its results are in "Stage 1 results".

The first step has three stages. The first two are cheap and can rule out one
third before any integration work. The one-third thresholds (s ≥ 1/3 and
r > r*) come from the formula in section 1. The 15% and 25% saving bands are
policy choices, picked because the decision ledger's retained changes were
mostly 3-10% and a cross-language contract change needs a clearly larger
gain. They are open to change.

### Stage 0a: measure s, how much must stay in Python

**Method.** Instrument `origin/main` in process, at 140 and 1,400 rows,
with citry-core built in release mode, because the benchmark refuses debug
builds of the Rust extension.
- Start from the profiling harness of the earlier Vue architecture
  experiments, importing the board app from `benchmarks/web/apps/citry`
  exactly as the benchmark server does.
- Remove its `gc.collect()` before each sample, so garbage collection runs
  normally.
- On that research branch, add timing counters inside `assemble_typed_render`
  for the nested `transform_component` and `attach_leaf_data`, because these
  closures cannot be wrapped from outside.
- Wrap these functions with low-overhead counters:
  - `ProjectOutput.template_data` (rewrapped with `staticmethod(...)`, or the
    class is rejected) and `Board.template_data`;
  - `_construct_data_schema`, `_render_one` and `_render_simple_vue_leaf`;
  - `render_static_instance_free` and the four `LeafProgramNode.render` calls;
  - `ComponentNode.render`, `ForNode` and `_render_body`;
  - `_prepare_holding_assets`, `_script_json` and `_render_for_hydration`;
  - `typed_document_shell`, `emit_dependencies` and `vue_plan.finalize`.
- Record garbage-collection pauses with `gc.callbacks`.

**Budget.** 3 fresh processes per size, 2 warm-ups and 11 timed samples each.
That is under 5 minutes of machine time, plus about half a day to set up.

**Output.**
- Each timed function sorted into four groups: stays, A + B can move it,
  only C can move it, and already C inside CPython.
- s for A + B and for C, and the r needed for one third:
  r* = (1/3 − s)/(1 − s).

The sorting is a judgment layered on the timings, so the person running
Stage 0a records the sorting next to the numbers for review.

### Stage 0b: measure r on the row work

**Method.** A standalone research extension module, built outside
`citry_core_py` so no shipped PyO3 surface changes. It does the row work for
the board's 1,400 real row dictionaries, including the nested dependency,
attachment and tag loops, in two variants:
- C API reads (option 1 in section 3);
- `json.dumps` followed by a Rust parse (option 2).

Each variant checks types, evaluates every row expression and writes the
row's manifest JSON. Compare both with today's Python check, evaluator and
that row's assembly work on the same rows. Run on CPython 3.12. Also run the C
API variant on `cp314t` with the GIL off.

**Budget.** About 1-1.5 days of work and under 2 minutes of machine time.
The result is optimistic for row work, because it leaves out integration
costs. So a bad r here is conclusive for A's row work, and a good r is only a
reason to continue. It does not measure C's whole-pass removals (the parent
loop, repeated tree walks, document copies). For those, the "already C" group
uses r = 1 and the rest uses the Stage 0b r, until Stage 1 measures them.

### Decisions after Stage 0

Read the table from the top. The first row that matches applies. "Projected
saving" is 1 − T for architecture C, using s from Stage 0a and, for each work
group, its r: the Stage 0b r for Python-interpreted work, and 1 for work
already in C.

| Result | Decision |
|---|---|
| s for C is at least 1/3 | One third is impossible on this page. Restate the goal before writing more Rust. |
| Projected saving is under 15% | Stop the Rust route for speed on this page. Do the Python cleanup. |
| Projected saving is 15-25% | The maintainer decides. The recommendation is the Python cleanup first, then re-measure. |
| Projected T is above 1/3, and the projected saving is at least 25% | One third is ruled out for this page. Stage 1 is still worth running for the smaller goal, if the maintainer agrees. |
| Projected T is at most 1/3 | Go to Stage 1. |

### Stage 1: a research prototype of architecture A, only if Stage 0 says go

**Scope.** A branch from `origin/main`, never merged. Behind a private switch,
it admits only the board's `ProjectOutput` template. CLAUDE.md requires a
written plan for any new PyO3-exposed function, even on a research branch, so
Stage 1 starts with that plan or with the maintainer's explicit waiver.

**Data flow.**
1. Python runs as today through each row's data methods and the globals
   merge.
2. Where `render_static_instance_free` is called today
   (`component_render.py:642`), Python makes one Rust call per row, with
   option 1 or 2, whichever won in Stage 0b.
3. Rust holds the row data and writes the row's manifest JSON. A Rust
   encoder splices it into the manifest.
4. `_render_for_hydration` runs unchanged.
5. For outputs that need Citry's own row HTML (static, fragment, the decline
   fallback), Rust hands the recorded values back to Python's existing writer.

**A second measured variant** (an "arm" of the comparison) also skips the
parent loop's per-row Python objects. It shows how much of the gap between A
and C the loop accounts for.

**Control.** The same commit with the switch off, in the same release build,
with the variants interleaved across fresh processes. If the Python cleanup is
ready, add it as a third arm.

**Equivalence checks.** All of these must pass before any timing counts:
- *Output bytes:* full HTML bytes, and manifest bytes with a fixed id
  generator, clock and secret. Also the recorded child-call groups (call
  runs), Vue definitions, dependency assets and Events tokens.
- *User call order:* `template_data`, `js_data` and `css_data` call counts
  and order.
- *Faults:*
  - row k has a missing key, a `dict` subclass value, a `Markup` value or a
    non-finite float: the same `TypeError` and component path, and exactly k
    calls each of `template_data`, `js_data` and `css_data`;
  - `ComponentLike.register(str)` makes the row reject (measured in
    Stage 1: it breaks the page before any row, on both paths, with the
    same error);
  - one dictionary reused across rows gives identical output.
- *Output kinds:* one Events action round trip (the page update the server
  sends after an action),
  `ssr=False`, static, fragment, CSP on, and a forced hydration decline.
- *Sizes:* 14, 140 and 1,400 rows.

**Measurement.**
- Warm render + serialize in process: 3 interleaved processes per arm, 11
  samples, normal garbage collection.
- Per page, record the Rust calls, the time spent reading Python data, and the
  Python object counts.
- One run through the real harness with the `citry-local-wheels` profile,
  which installs Citry from locally built wheels
  (`benchmarks/web/README.md:200-242`). The switch is set by an environment
  variable read at server start.

**Budget.** About 5 minutes in process, plus about 4-5 minutes for the
harness run: about 30 s to prepare and 2 minutes to qualify
(`benchmarks/web/README.md:172-173`), then the run. That exceeds the 5-minute
guideline because the harness run is the only way to see first- and
second-load `prepare` and request to layout. It needs the maintainer's
go-ahead. (The maintainer agreed. Stage 1 measured first and second load
through the real server with plain HTTP instead, with 5 samples per cell;
the browser-harness run was not done, as "Stage 1 results" records.)

**Decisions after Stage 1.** Read the table from the top, and the first
matching row applies. "Projected saving" is 1 − T for architecture C. It uses
the r measured in the integrated prototype for Python-interpreted work and
r = 1 for work already in C. B's share counts only work that A does not
already move.

| Result | Decision |
|---|---|
| Projected saving is under 15% | Stop the Rust route for speed. Keep the Python cleanup. |
| Projected saving is 15-25% | The maintainer decides, weighing it against the contract cost in section 6. |
| Projected T is above 1/3, and the projected saving is at least 25% | The one-third hypothesis is ruled out. A production design for the smaller goal is the maintainer's call. |
| Projected T is at most 1/3 | The hypothesis survives. Write a production design for C, with a plan as CLAUDE.md requires. |

**Cost.** About 5-7 working days. Most of it goes to:
- the Rust row writer;
- the manifest encoder that matches Python byte for byte, including float
  `repr` and the digest inputs;
- the hand-back path to Python's writer;
- the parent-loop variant, which needs scheduler changes;
- the parity harness.

No step adds to routine CI.

## 6. Code and docs a full migration would change

This is the cross-binding list that CLAUDE.md requires (Mechanism 4). Stage 0
and Stage 1 change none of it: they are research branches. A production
version of A, B or C would touch the items below.

Legend:
- **real:** substantive work;
- **stub:** a signature or registration update;
- **check:** review it, though it may not change;
- **none:** not affected.

**Rust crates**

| Item | A | B | C |
|---|---|---|---|
| New crate for the render plan, per-render storage and output, with root `Cargo.toml` members and `[workspace.dependencies]` entries | real | real | real |
| `crates/citry_template_parser/src/compiler.rs`: expose the prepared form; update the module contract (`:1-79`) | real | check | real |
| `src/lang/lang.rs` `LangImpl`: a new method needs a plan | check | check | real |
| `src/lang/python.rs`: expression ids must line up with the plan | real | check | real |
| `src/lang/js.rs`, `php.rs`, `go.rs`, `rust.rs`: return "not yet implemented" | stub | none | stub |
| `src/constants.rs`: the `Prepared*` node names are string literals in `compiler.rs` today | stub | none | real |
| `crates/citry_vue_compiler/src/server_render.rs`: may read Rust-held values instead of JSON | check | real | real |
| `crates/citry_core_py/src/vue.rs`: the `_render_for_hydration` signature changes if it reads Rust-held values | check | real | real |
| `crates/citry_html_transform`: `mark_html` may move into the writer | check | real | real |
| `crates/citry_i18n`: message formatting as a native effect | none | check | check |
| `crates/python_safe_eval`: expressions stay Python | check | none | check |
| `crates/citry_core_py/src/lib.rs` plus a new `render.rs`: registration, calls back into Python, handle tables | real | real | real |
| `crates/citry_core_py/Cargo.toml` | stub | stub | stub |
| Rust tests: `citry_template_parser/tests/tag_compiler*.rs`, inline tests in `server_render.rs:3656` and `hydration.rs:1453`, `citry_html_transform/tests/` | real | real | real |

**Python packages and protocol**

`packages/py/citry_core/`:
- `citry_core/_rust.pyi`: real. Also remove the stray `format_*` lines in
  `class template_parser`.
- A new `citry_core/render/` wrapper module: real.
- The tests, check or real: `tests/test_template_parser.py`,
  `test_distribution_artifacts.py` and `test_build_profile.py`.

`packages/py/citry/citry/`:
- Real for all three architectures:
  - `component_render.py`, `nodes/__init__.py`, `citry_render.py`;
  - `serialize.py`;
  - `_vue/leaf_program.py`, `_vue/direct_capture.py`, `_vue/prepared.py`,
    `_vue/protocol.py`, `_vue/events.py`, `_vue/serialization.py`,
    `_vue/compiler.py`, `_vue/document.py`;
  - `ext/dependencies/emission.py`.
- Real for C:
  - `component.py`, `citry_context.py`, `citry_element.py`;
  - `slots.py`, `provide.py`, `extension.py`, `constness.py`;
  - `cache.py`, `lifecycle.py`, `browser_render.py`;
  - `ext/events/*` and `ext/i18n/*`.
- Check or real for all: `_csp_validation.py`, `_javascript_policy.py` and
  `_output_html.py`.

The protocol and the browser runtime:
- `packages/protocol/events/v1/` (`spec.md`, `manifest.schema.json`,
  `validate.py`, and its tests): check for A, real for B and C if the Events
  manifest builder (`_vue/events.py:1012`) moves.
- `_vue/client.js` and `runtime.js`: check, or real if the manifest format
  changes.

Python tests, real or check:
- `test_simple_vue_*.py`, `test_render*.py`, `test_nodes.py`,
  `test_component_node.py`;
- `test_slot_node.py`, `test_deferred_render.py`, `test_on_render.py`;
- `test_serialize_security.py`, `test_vue_hydration_regions.py`,
  `test_vue_prepared*.py`, `test_vue_markers.py`;
- `test_vue_metadata_contracts.py`, `test_events_host_parity.py`,
  `test_vue_events*.py`;
- the e2e suites, and `benchmarks/web/apps/citry/test_hydration_e2e.py`.

`scripts/vue_render_parity/check.py`, the Vue `renderToString` parity check:
real.

**Distribution**

- `scripts/verify_citry_core_distribution.py` and
  `.github/workflows/py--citry-core--publish.yml`: real. The new code must
  pass the `cp314t` and PyPy smoke tests.
- The Pyodide build (`packages/py/citry_core/pyodide-build.json`,
  `scripts/build_citry_core_pyodide_wheel.py`,
  `scripts/update_playground_runtime.py`): check. The playground runtime
  must still build and work.
- `packages/py/citry/pyproject.toml:41-43` pinned `citry-core==1.8.0` exactly
  when this was written (1.9.0 at `88d7e4869`), so citry and citry-core
  release together. citry-core was at 1.8.0, so a new
  public function is a minor bump and a changed one a major bump. citry is at
  0.6.0, below 1.0.0, so its manifest, protocol and render-cache versions stay
  at 1, with corrections made in place.

**Docs and records**

- `docs/design/rust_rendering.md` and `performance_architecture_experiments.md`:
  real. Record the decision, and add a ledger row for each measured attempt.
- `docs/design/performance.md` section 6.9: real.
- These design docs, real or check: `vue_optimization_rollout.md`,
  `vue_board_hydration_plan.md`, `vue_ssr_selected_tree_plan.md`,
  `component_rendering.md`, `component_rendering_defer.md` and `vue.md`.
- `docs/agent/INDEX.md`, in its pipeline and open plans: real.
- `crates/citry_template_parser/AGENTS.md` and its `docs/agent/INDEX.md`:
  real if the compiler output changes.
- `crates/citry_core_py/AGENTS.md`: stub.
- New `AGENTS.md` files for `crates/citry_vue_compiler` and any new crate:
  real.
- `docs/codebase.md`: stub, for the new crate and the release coupling.

**Changelogs**

- The root `CHANGELOG.md` gets one user-visible speed entry.
- `packages/py/citry_core/CHANGELOG.md` gets an entry for any public citry-core
  API.

**Published benchmarks**

- `benchmarks/web/apps/citry/`: check. Its timing hooks must stay identical
  across measured arms (`docs/design/framework_interaction_benchmarks.md:316-319`).
- `benchmarks/native_build.py`: check. It is the guard against debug builds.
- `docs_site/data/benchmark_time_to_interactive.json`,
  `docs_site/content/about/benchmarks.md` and
  `docs_site/scripts/benchmark_data.py`: real once results are published. The
  landing-page claim waits for a confirmed result, as #144 says.

## 7. Decisions and open questions

Decided by the maintainer (2026-10-20):
- **The goal covers both warm time and first-load time.** First load needs
  startup compilation alongside any Rust work.
- **Internal formats may change where needed.** That includes the internal
  manifest layout. The public API should not change in any major way; minor
  parts and edge cases are open to discussion.
- **Architectures A, B and C should all be explored,** together with
  Python-side inefficiencies, even though one third may not be reachable.
- **Pyodide and PyPy keep the Python path.** The native path switches off on
  those builds (and on free-threaded CPython until it is measured there), and
  the user docs must say so clearly.
- **User callback order must not change.** A variant that skips the parent
  loop's per-row Python objects has to keep today's order. The candidate:
  - The loop still evaluates each row's kwargs and key during the parent's
    template walk, as today.
  - It records them in one compact list and pushes a single queue task for
    the whole run of rows, at the queue position the per-row tasks hold
    today.
  - That task runs the rows in order.

  Nothing else runs between consecutive instance-free row tasks today, so the
  callback order, render-id order and dependency-record order stay the same.
  The error path (row k raises, later rows never run) needs a test proving
  the same exception and component path. This variant runs only if Stage 1
  points toward architecture C.
- **The Python-only cuts land before Stage 1 is measured,** so the Rust
  comparison is against the cleaned-up Python.
- **The `on_dependencies` double call is fixed as an ordinary bug,** outside
  this research. It shipped in
  [#260](https://github.com/citry-dev/citry/pull/260).
- **The public benchmark is re-checked on a quiet machine.**
  - First, Citry runs alone through the release harness.
  - If the 1,400-row first-load step goes away, the whole cohort is rerun with
    the same method and published, noting why it was rerun.
  - If the step stays, it is investigated.
  - Result: the latency recheck shows no step, so by the agreed trigger the
    cohort rerun is due. The qualification recheck shows a smaller step,
    about 18 ms, in a run that was slow throughout (see "The 0.6.0 first-load
    step"). This note recommends a change of plan, in open question 3; the
    maintainer decides.
- **`gc.freeze()` is documented as an optional deployment tip, not a
  feature.** The tip is on the user docs' performance page
  (`docs_site/content/performance/index.md`).

Still open:
1. **Does reuse by other host languages count toward C?** C would put the
   scheduler and output writer in Rust once, so a future JS, PHP or Go
   binding ([issue #27](https://github.com/citry-dev/citry/issues/27)) would
   supply only its callbacks. Should that weigh in C's favor, beyond its
   speed?
2. **Should the benchmark app call `gc.freeze()`?** It is a process-wide
   setting, so every framework in the benchmark would have to get the same
   treatment, or none of them.
3. **What to do about the 0.6.0 first-load figure?** The recommendation is
   to keep the published data and add a note to the 0.6.0 Citry 1,400-row
   first-load cell: it is a single observation, and two rechecks through the
   same harness measured 165.3 ms and 207.9 ms. The agreed plan was to rerun
   the cohort with the same method if the step went away. That rerun would
   produce another single sample per cell, with the same weakness, so this
   note recommends against it. For the next release, the profile could take 3 or more
   cold-process first loads per cell, so one slow draw cannot set a
   published figure. That means more `blocks`, since each block starts a
   fresh server process. More `sessions` would not help, because later
   sessions reuse the warm process. That changes the method for every framework, so it
   belongs in the next release, not in a 0.6.0 republish. A 0.6.0 rerun with
   more blocks is the alternative, at about 90 minutes or more.

   **Decided:** the cohort is rerun after these optimizations are merged.
   Other benchmarks are using the machine until then, so the published 0.6.0
   data stays as it is for now.
4. **What has not been timed yet?** Neither the research nor the
   production timing covered an Events update step (the production
   plan's bar was "no more than 2 ms slower"), speed on PyPy, Pyodide and
   free-threaded CPython (all take the Python path, which C1 changes), or
   wheel size per level. No CI job runs the test suite on those
   interpreters either
   ([#264](https://github.com/citry-dev/citry/issues/264)).
5. **Which follow-ups should a production version take next?** The
   written Stage 2 plan named three: one internal record and occurrence
   format for rows and ordinary components; a lowered loop form from the
   template compiler, which C2's walk could read instead of re-reading
   Python's parse; and a parse of the manifest text in place in
   `server_render.rs`, if the 2.4 ms parse ever matters. A fourth, a
   Python batched run, became production C1
   ([#267](https://github.com/citry-dev/citry/pull/267)).
6. **How much does the native module add to the Pyodide wheel?** Nobody
   has measured it. The module ships there unused. The production plan
   keeps one build everywhere unless that wheel grows by more than about
   100 KB compressed; then the module is left out of the `emscripten`
   target with `#[cfg]`. The check in `native_render.py` that picks the
   path already handles a missing module, but the release smoke script
   (`scripts/smoke_citry_core.py`) calls `_rust.native_render` on every
   wheel and would need a platform guard too.
7. **Will the maintainer rule on the built-in Events hook?** C3 waits on
   the ruling that the built-in `on_attrs_resolved` hook is an observer
   for these components (see "Not built: C3, and what it would need").
   The research switch for C3 stayed off for lack of it.
