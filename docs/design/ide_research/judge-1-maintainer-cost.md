# Judge 1: practicality and maintainer cost

**Date: 2026-07-07. Role: adversarial judge** over the three competing IDE
integration drafts ([`design-A-ship-first.md`](design-A-ship-first.md),
[`design-B-platform-first.md`](design-B-platform-first.md),
[`design-C-ecosystem-first.md`](design-C-ecosystem-first.md)), feeding the
final [`../ide_integration.md`](../ide_integration.md).

**The lens:** citry is a solo-maintainer project whose core value is the
framework, not the tooling. Every tooling hour competes with framework hours.
Each draft is judged on time-to-first-user-visible-value, steady-state
maintenance burden, risk of abandoned half-built tooling (worse than none),
reuse of what already exists (the Rust parser, the shipped `citry_core`
bindings, the built `pygments_citry` package), and honesty of its effort
estimates. Each draft is also attacked: the hidden costs its author
underplayed are named.

Terms used throughout, defined once: **LSP** (Language Server Protocol) is
the editor-agnostic protocol a separate "language server" process speaks to
give an editor diagnostics, completion, hover, and navigation. A **TextMate
grammar** is a regex-based highlighting grammar (VS Code's base format, also
readable by JetBrains and Sublime). **tree-sitter** is an incremental,
error-tolerant parser framework Neovim, Zed, and Helix use natively for
highlighting. **pygls** is the standard Python library for writing language
servers. **TagRules** is the per-tag validation rule set citry's parser
accepts (allowed and required attributes and slots), defined in
`crates/citry_template_parser/src/parser_context.rs:31-62` and already
exposed to Python. A **vsix** is VS Code's extension package format.

## Method and verification

- All three drafts and all five recon reports in this directory were read in
  full. Draft claims were cross-checked against the recon corpus; where a
  draft's load-bearing claim rested on evidence the corpus does not support,
  it lost points, and the finding is recorded in the fact-check table below.
- Fresh web checks made for this judgment (accessed 2026-07-07): pygls on
  PyPI (v2.1.1, released 2026-03-25, Python 3.9-3.14, actively maintained;
  confirms design A's claim and supersedes the corpus's older v2.0.0
  snapshot), and the IntelliJ Platform web-types documentation (discovery is
  via `package.json` or an IDE plugin only; no documented path for a
  Python-only project; this convicts design B's M5 rung as written and
  confirms design C's pre-kill of the same idea).
- Repo spot-checks for the citations this judgment leans on: the `citry`
  console script exists (`packages/py/citry/pyproject.toml:48-49`); the
  parser crate's pyo3 dependency is unconditional
  (`crates/citry_template_parser/Cargo.toml:12`); parse errors flatten to
  strings at the Python boundary
  (`crates/citry_core_py/src/template_parser.rs:33-38`); `TagRules` is a
  `#[pyclass]` with the attribute and slot rule fields
  (`parser_context.rs:31-62`); `packages/py/pygments_citry/` is built and
  present in the tree.

## Scoring rubric

Five dimensions, weighted for this lens. Scores are 0-10.

| Dimension | Weight | What it measures |
|---|---|---|
| Time to first user-visible value | 25% | Calendar distance from "start" to something a citry user notices in their editor or CI |
| Steady-state maintenance burden | 25% | The permanent weekly cost once shipped: dependency churn, editor API churn, grammar mirrors, binary matrices, distribution channels |
| Abandoned-half-built risk | 20% | If the maintainer stops at any point, what is stranded, and does the stranded state hurt users or the project's reputation |
| Reuse of what exists | 15% | How much of the shipped parser, bindings, Pygments package, vendored scaffolds, and existing CI pipelines the plan stands on versus rebuilds |
| Honesty of effort estimates | 15% | Do the numbers survive arithmetic and adversarial reading; are the falsifiers real; did the author verify their own claims |

---

## Design A: ship-first

### Scores

| Dimension | Score | One-line basis |
|---|---|---|
| Time to first value | 9 | Rung 0 (publish the already-built `pygments-citry`) in 1-2 days; VS Code color in ~2 weeks; a parser-grade CI checker on the existing `citry` console script in ~3-4 weeks; inline diagnostics by ~week 7-8 |
| Steady-state burden | 7.5 | Smallest artifact inventory of the three: one grammar family, one universal vsix, one pure-Python wheel, zero binary matrix; the tail is interpreter discovery plus per-project version skew |
| Abandoned-half-built risk | 9 | Every rung ships standalone value and survives a stop; a stalled ladder leaves a published Pygments package, a working highlighting extension, and a CI linter, none of which rot fast |
| Reuse of what exists | 9 | Publishes the built Pygments package as-is, drives diagnostics through the shipped `citry_core` bindings and the existing `TagRules` hook, rides the existing console script; asks the engine for exactly two small additive changes |
| Estimate honesty | 7.5 | Mostly honest and the most self-critical cost section of the three, but the headline "roughly two months" is the low edge of its own arithmetic, and two real costs go unnamed (below) |

**Weighted total: 8.4**

### Reasoning

Design A is the only draft whose first month is spent almost entirely on
assets that already exist. Rung 0 is publishing a finished package. Rung 1
is a TextMate grammar whose region-detection logic is a transcription of the
already-tested Pygments lexer. Rung 2 puts the real parser and the existing
`TagRules` parameter behind a subcommand on a console script that already
ships. By the time any genuinely new architecture appears (the pygls server
at rung 3), the risky parts (component discovery, `TagRules` derivation,
diagnostics rendering) have already shipped twice and have users. That
sequencing is the best de-risking device in any of the three drafts, better
even than design B's pause point, because it front-loads value rather than
deferring it.

The distribution story is the structural win for this lens: because the
server is a pure-Python wheel living in the user's environment, there is no
per-platform binary matrix, no per-platform vsix pipeline, no GitHub
release archive automation, and no wasm packaging. Design A is the only
draft where "distribution" is one universal vsix plus PyPI, and that shape
is a consequence of the architecture, not an aspiration.

The honestly priced rewrite risk (section 7.3 of the draft) is handled
correctly: the thin-server discipline keeps the rewritable core small, and
the grammars, extension, CLI, tests, and docs all survive a rewrite. Under
this lens, a priced deferred cost beats a prepaid speculative one.

### Attacks: what the author underplayed

1. **Completion in broken buffers is the differentiating feature, and it
   fires exactly when the fail-fast parser has nothing.** Rung 4 sells "my
   editor knows my components", but the moment a user wants tag completion
   is mid-keystroke (`<c-Ca`), when the buffer does not parse. The
   last-good-tree pattern supplies the *data* (registry, variables) but not
   the *cursor context* ("am I inside a tag name? an attribute?"). Every
   server in this genre ends up with a small hand-rolled context scanner
   over the current text for that, and design A budgets zero lines for it.
   This makes falsifier 3 (fail-fast UX rejection) the most likely of its
   six to fire, and the draft does not connect its own rung 4 to that
   falsifier.
2. **Venv contamination and install friction.** `pip install citry[lsp]`
   puts pygls and its dependency tree (lsprotocol, cattrs, attrs) into the
   user's *project* environment, the same environment that may ship to
   production. Some teams will refuse; the sanctioned alternative
   (`uvx citry-lsp`) loses registry mode, the feature the whole design is
   built around. The predictable "extension cannot find citry-lsp in the
   selected interpreter" first-run support tail is adjacent to, but distinct
   from, the interpreter-discovery burden the draft does price.
3. **Version skew is inverted, not eliminated.** The draft claims lockstep
   releases, but the server ships in the user's venv, so the *user's pin*
   decides which server version runs. The extension must therefore stay
   compatible with every `citry-lsp` version users have installed across
   their projects, and issue reports will arrive from old servers against
   new extensions. Design B's polite-refusal skew diagnostic addresses
   exactly this and design A should adopt it.
4. **The arithmetic of "roughly two months".** Rungs 0-4 sum to 7.5-11.5
   focused weeks by the draft's own numbers; the midpoint is closer to two
   and a half months. Not dishonest, but the headline quotes the optimistic
   edge.
5. **Rung 5 support surface.** "Docs-only" editors still generate issues,
   and in Neovim/Zed/Helix design A's users get LSP features over
   completely unhighlighted files, an experience odd enough to produce
   "is this broken?" traffic. The draft acknowledges the gap but books no
   time for the resulting questions.

### Strongest and weakest element

- **Strongest:** the rung ordering. CLI before server, grammar before both,
  publishing a finished asset on day one. Each rung is a shipped product
  and a test bed for the next; nothing is scaffolding-only.
- **Weakest:** rung 4's completion story on a fail-fast parser. The design's
  headline semantic feature is the one place its architecture is weakest,
  and the mitigation (last-good-tree) is asserted rather than costed.

### Fact-check notes

pygls 2.1.1 (2026-03-25) verified on PyPI this pass. No claims contradicted
by the recon corpus were found. Notably, design A frames the Django
ecosystem's Python-to-Rust server story as a *priced risk* rather than a
settled verdict, which is the reading the corpus actually supports (see the
fact-check table).

---

## Design B: platform-first

### Scores

| Dimension | Score | One-line basis |
|---|---|---|
| Time to first value | 5 | Two weeks of user-invisible engine work first; first color at ~5-6 weeks; CI checking at 7-9 weeks; the headline editor semantics at 4-5.5 months |
| Steady-state burden | 5 | Best per-artifact endgame (one binary, static-first discovery, no rewrite ever) but the widest scheduled surface: two grammar families plus Pygments mirrors, per-platform vsix, a JetBrains plugin, and a typed-expression layer the draft itself calls a permanent line item |
| Abandoned-half-built risk | 5.5 | The pause point after M2 and the high salvage value of M0-M2 are real mitigations; the self-flagged 6-10 week M3 trough with no shippable increment is exactly the zone where solo tooling dies |
| Reuse of what exists | 6 | Direct crate linkage, vendored `ruff_server`/`ruff_python_parser`, the existing maturin matrix; but it bypasses the shipped Python bindings, requires new engine work before anything ships, and reserves compiler-contract space for a consumer (M6) that is gated and may never be built |
| Estimate honesty | 5.5 | The sharpest falsifier set of the three and admirable self-flagging of the M3 trough; but M0 is underpriced, the web-types rung is contradicted by the platform docs, and its strongest rhetorical claim overstates the corpus |

**Weighted total: 5.3**

### Reasoning

Design B is the best *product* plan and the worst *hour-economics* plan. Its
end state is genuinely superior: one binary that is both the LSP and the CI
checker, no interpreter discovery as a load-bearing mechanism, no rewrite
overhang, and engine contract fixes (structured diagnostics, the offset
entry, the whole-input-span fix) that improve citry's Python API for
everyone regardless of what happens to the tooling. The salvage value of
M0-M2 is the highest of any draft's early work, and the pause point after
M2 is a well-placed kill switch that the draft itself connects to the
decisive falsifier (no adoption evidence means stop).

But under this lens the plan's shape is the problem. The first two weeks
produce nothing a user can see. The headline feature sits behind a 6-10
week rung with no intermediate ship. The total commitment to M4 is
4-5.5 months of focused solo time, followed by scheduled rungs (JetBrains
plugin, web-types, typed expressions) that add 10-16 more weeks and two
permanent maintenance lines, all bet against adoption evidence the draft
concedes does not exist yet. The draft's own falsifier 5 is an honest
admission that the entire platform-first premise is unproven at the point
where it is cheapest to stop, which is another way of saying the premise
should not order the first six months of work.

### Attacks: what the author underplayed

1. **M0 is underpriced.** Four of its items touch surfaces CLAUDE.md marks
   high-risk (the pyo3 feature gate touches every `#[pyclass]` site in the
   AST, structured diagnostics change the PyO3 error contract, the offset
   entry changes the parser's public surface, the source-map slot changes
   the compiler output contract). Each requires a prior-art header, a plan,
   and the cross-binding audit across five `LangImpl` files, the PyO3
   registration, the `.pyi` stub, the Python wrapper, and both test suites.
   Calling that 1.5-2 weeks prices the diffs but not the process the repo
   itself mandates; 3 weeks is the honest floor.
2. **The source-map slot is speculative work on the highest-risk contract.**
   Reserving compiler-output space for M6, a rung that is doubly gated (on
   the Events typing work and on the pause review) and may never be built,
   is exactly the "prepaid speculative cost" this lens penalizes. If M6
   dies, the reservation was a contract change consumed by nothing.
3. **The web-types rung (M5) is contradicted by the evidence.** The draft
   claims web-types buys "PyCharm completion with zero plugin installed."
   The IntelliJ Platform docs (checked this pass) and design C's fresh
   verification both say discovery is keyed off `package.json` or bundled
   in an IDE plugin; a Python-only project has no documented path. The rung
   as written cannot work; at best web-types rides the M4 plugin, which is
   not "zero plugin". Design B's "verified 2026-07-07" diligence did not
   extend to this rung, and it shows.
4. **The anti-pygls argument overstates the corpus.** "The Django ecosystem
   already ran that experiment and abandoned that path" is the draft's
   strongest rhetorical weapon against design A. The corpus says djlsp
   (Python) shipped v1.2.2 in 2025-11 and remains active, while djls (Rust)
   is a different author's project, self-flagged early-stage with "most
   features incomplete" (recon-python-template-tooling, sections 2.1-2.2).
   The accurate reading is "a promising second-generation Rust server
   exists", not "the Python approach failed". Nothing was abandoned.
5. **Per-platform vsix is a new release pipeline, not a marginal one.** The
   wheel matrix exists, but building, embedding, signing, and publishing
   one vsix per OS/arch to two marketplaces on every release is its own CI
   surface with its own failure modes. "Marginal" undercounts it.
6. **Static-first component knowledge produces false positives until M5.**
   Deriving `TagRules` from static analysis means dynamically registered
   components are unknown to the server until the sidecar lands, so the M3
   server will squiggle valid `<c-*>` tags in exactly the projects that use
   citry's dynamic features. That is the Vetur trust failure the draft
   itself cites as disqualifying, and the ladder does not say how M3
   suppresses it (severity downgrade? unknown-tag diagnostics off until
   M5?). Unaddressed.

### Strongest and weakest element

- **Strongest:** the pause point plus the falsifier set. No other draft
  states as precisely what evidence kills it, schedules the risky spikes
  (JetBrains attach, parse latency) as early as possible, and places the
  stop decision at the cheapest point.
- **Weakest:** the overall committed shape. Roughly five months to the
  headline feature, with the differentiating value locked behind the
  longest single rung any draft proposes, justified by an end-state
  argument the draft's own falsifier 5 concedes is unproven.

---

## Design C: ecosystem-first

### Scores

| Dimension | Score | One-line basis |
|---|---|---|
| Time to first value | 4 | Invisible R0, then 3-5 weeks of tree-sitter work whose first visible value serves the smallest audience slice; VS Code color at 6-10 weeks; the CI checker is buried inside R4 at weeks 13-22 |
| Steady-state burden | 5.5 | Deliberately refuses the two permanent cost centers (typed layer, JetBrains-native plugin), which caps the tail; but carries the most channels and grammar mirrors of the three, and its own 2-6 hours/week estimate is the highest steady-state admission on the table |
| Abandoned-half-built risk | 5 | Rungs are nominally independent, but R1's standalone value is contingent on falsifier F1, the grammar's server payoff is stranded until R4, and six registries of half-alive glue is the diffuse-rot scenario |
| Reuse of what exists | 6.5 | Parser crate, vendored `ruff_python_parser` and server scaffolds, the issue #23/#26 designs; misses the free `pygments-citry` publication entirely |
| Estimate honesty | 8 | The only draft whose fresh verification *corrected* the corpus (Zed's repo+rev-only grammar fetch, the web-types kill, LSP4IJ mechanics); it pre-kills its own weakest rung and states the falsifier that breaks its own thesis; docked for a headline its own survey data undermines |

**Weighted total: 5.6**

### Reasoning

Design C's research hygiene is the best of the three. It is the only draft
that went and checked the distribution mechanics editor by editor, found
the web-types discovery dead end before proposing to build on it, and wrote
falsifier F1 (inline injection into Python strings may only work in Neovim)
against its own central artifact. Its two-tier project index (static scan
by default, opt-in `citry inspect --json` merging over it) is the cleanest
component-knowledge architecture in any draft, and the inspect command is
independently useful to scripts, CI, and issue #26's other consumers even
if every editor rung dies.

The problem is that the thesis and the ladder disagree. The thesis is
"maximize coverage per unit of maintainer effort", but both surveys the
draft cites agree VS Code plus PyCharm covers roughly three quarters or
more of the Python audience, and the artifact the ladder builds first
(tree-sitter, R1, 3-5 weeks) serves the Neovim/Zed/Helix tail, a slice of
perhaps 5-15%, with inline-template support unproven outside Neovim and
citry's documented house style being inline templates. The
highest-coverage single artifact by the draft's own numbers is the TextMate
grammar in the VS Code extension, which it schedules second. Meanwhile the
cheapest high-value artifact for a solo maintainer, the CI checker that
works in every editor at once (a point all three drafts and the field recon
agree on), does not exist until R4, months in. Design C's falsifiers F1 and
F2 are honest, but they point squarely back at its own ordering: if either
fires, the correct plan was a head-first design, and the distinctive early
spend was the waste.

The steady state deserves both credit and suspicion. Credit: refusing the
typed layer and the JetBrains-native plugin caps the two permanent cost
lines every failure story in the corpus runs through, and 2-6 hours/week is
probably the most accurate steady-state number any draft states. Suspicion:
the artifact inventory (tree-sitter grammar plus per-editor query variants,
mirror repo CI, TextMate grammar, server, VS Code extension, Zed extension,
Mason entry, Helix config, LSP4IJ template, Sublime package, taxonomy
validator) is the widest of the three, and every channel is a place for a
platform migration to land (the draft's own example: the nvim-treesitter
main-branch rewrite). Breadth is cheap per channel and expensive in
aggregate, and aggregate is what a solo maintainer pays.

### Attacks: what the author underplayed

1. **The ordering contradicts the survey data it leads with.** Five-plus
   weeks of R0+R1 before the largest editor sees anything, for a framework
   whose primary authoring mode (inline strings in `.py`) is the exact case
   tree-sitter injection may only handle in Neovim. The draft half-admits
   this in F1 and Note A but keeps the ladder anyway.
2. **"Six-plus editors with real support" overcounts PyCharm.** The
   second-largest audience gets: a hand-imported LSP4IJ JSON template, a
   third-party client plugin, no coloring at all for inline templates, and
   a documented-but-unshipped `# language=` workaround. F7 concedes the
   friction. That is coverage on paper, not in hand.
3. **The CI checker arrives last.** Design A ships `citry check` around
   week 3-4; design B at weeks 7-9; design C buries `check` inside the R4
   server rung at weeks 13-22, despite the field recon's finding that
   compile-time validation is where most perceived value concentrates. For
   a coverage-maximizing design, deferring the one artifact that covers
   every editor and CI at once is self-refuting.
4. **The mirror-repo machinery is infrastructure before product.** A
   CI-pushed generated mirror repository, per-editor query variants, and a
   registry entry exist by R1, months before the server gives those editors
   anything semantic. If the ladder stalls after R1, citry owns public
   grammar infrastructure serving highlighting for a tail audience, which
   is the closest any draft comes to the abandoned-half-built scenario this
   lens fears.
5. **Rung 0's free win is missing.** The built `pygments-citry` package is
   never published in this plan. One to two days for docs-wide rendering
   everywhere Pygments runs; no coverage-per-effort argument survives
   skipping it.

### Strongest and weakest element

- **Strongest:** verification honesty and the project index design. The
  fresh per-editor distribution facts (Zed repo+rev only, Helix `subpath`,
  nvim registry model, LSP4IJ user-defined servers, the web-types kill) are
  the most useful single block of research any draft contributed, and they
  survive whichever design wins.
- **Weakest:** the ladder ordering, which optimizes for the audience tail
  first and defers both the largest editor and the universal CI artifact,
  against the draft's own cited data.

---

## Cross-draft fact-check summary

Claims tested against the recon corpus, fresh web checks, and the repo.

| Claim | Draft | Verdict |
|---|---|---|
| pygls v2.1.1, 2026-03-25, active | A | **Confirmed** (PyPI, this pass); supersedes the corpus's v2.0.0 snapshot |
| web-types gives PyCharm completion "with zero plugin installed" | B (M5) | **Contradicted**: IntelliJ Platform docs (this pass) and C's fresh check both show discovery is `package.json`- or IDE-plugin-keyed; no Python-only path exists |
| The Django ecosystem "abandoned" the Python server path / djls is "lapping" djlsp | B | **Overstated**: djlsp is active (v1.2.2, 2025-11-14); djls is a different author's early-stage project, "most features are incomplete" (recon-python-template-tooling 2.1-2.2). Evidence supports "a second-generation Rust server exists", not "the Python approach failed" |
| Same story framed as a priced rewrite *risk* | A (7.3) | **Fair reading** of the same evidence |
| Zed fetches grammars by repository URL + revision only (forcing a mirror repo) | C | **Verified by C's own fresh check**; B's plan also needs the mirror and includes one |
| PyCharm cannot color inside `.py` strings without a native plugin (TextMate bundles cannot attach to natively-owned file types) | C (Note A) | **Consistent** with the corpus (recon-python-template-tooling 5.2, 7.2); A and B avoid claiming otherwise |
| JetBrains LSP clients attaching a second server to `.py` files is unproven | A (falsifier 4), B (falsifier 3), C (implicit via LSP4IJ file mappings) | **All three treat it honestly**; B schedules the earliest spike |
| maturin `bin` bindings package plain Rust binaries into wheels | B | **Accepted**: B re-verified against maturin docs; consistent with the djls precedent in the corpus |
| `TagRules` is the existing, Python-exposed diagnostics hook | all three | **Confirmed** (`parser_context.rs:31-62`, spot-read this pass) |
| Parse errors cross PyO3 as flattened strings | all three | **Confirmed** (`citry_core_py/src/template_parser.rs:33-38`, spot-read this pass) |

No draft misrepresented the repo's ground truth. The contradicted and
overstated items both belong to design B, and both sit under load-bearing
rungs (M5, and the case against the pygls path). Design C's fresh checks
were the only ones that corrected the corpus. These findings are reflected
in the honesty scores.

## Graft recommendations: what the winner should steal

Design A wins (verdict below), but it should absorb the following before it
becomes [`../ide_integration.md`](../ide_integration.md):

**From design B:**

1. **Measure parse latency during rung 1, not at rung 3 start.** B times
   the measurement before the server architecture is committed; A times it
   after the extension work is done and the server is next. B's timing is
   strictly better and costs nothing.
2. **Formalize the adoption pause review after rung 2.** A's ladder has
   gates ("ship it, use it, then start the next") but never states the
   evidence test. B's falsifier 5 (marketplace installs, issue traffic,
   PyPI numbers reviewed before the expensive rung) should be copied
   verbatim, placed between A's rungs 2 and 3.
3. **Bundle the whole-input-span fix into the structured-diagnostics pass.**
   B's M0 includes punch-list item 3 (`parser.rs:125-130` per the corpus);
   A defers it. It is the same surface, the same plan-mode pass, and the
   same cross-binding audit; doing it separately later pays the process
   cost twice.
4. **The version-skew polite-refusal diagnostic.** The server states, in
   one clear diagnostic, when the project's citry is newer than the
   server's understanding, instead of mis-parsing. A needs this *more* than
   B does, because A's server version is controlled by the user's venv pin
   (attack 3 on A above).
5. **The false-positive posture, stated up front:** unknown-component
   diagnostics only ever fire in registry mode, never from a static or
   degraded view. A's design already implies this (the static fallback
   parses without `TagRules`); it should say so as a hard rule, because it
   is the Vetur trust lesson turned into one sentence.

**From design C:**

6. **`citry inspect --json` as its own early rung.** A ships registry
   discovery inside `citry check`; C ships it as a standalone command that
   scripts, CI, and issue #26's other consumers (docs tooling, Storybook)
   can use with no editor anywhere. Splitting it out costs days and creates
   an independently useful artifact plus the natural first consumer of the
   component introspection API.
7. **Claim every name now.** C's list (Open VSX, Marketplace, Package
   Control, crates.io) is cheap insurance A only partially takes (Open VSX
   at rung 1). Do all of it in rung 0's week.
8. **File C's verified distribution mechanics as the tree-sitter reopening
   appendix.** Zed's repo+rev-only fetch, Helix's `subpath`, the
   nvim-treesitter registry model, and the mirror-repo pattern are exactly
   what A will need if its reopening trigger for tree-sitter ever fires;
   they are verified today and will be stale by then, but the shape of the
   problem will not be. Point at C's section 3.1 and its sources from the
   final doc.
9. **Adopt C's F1 spike protocol as the tree-sitter gate.** If tree-sitter
   is ever pulled forward (A's falsifier 3 firing), the first week must be
   C's injection spike (prove Python-string injection per editor) before
   any grammar work, because C established that the grammar's coverage
   dividend hinges on it.
10. **Keep web-types dead.** A defers it; C proved it. The final doc should
    record C's verification (discovery is `package.json`-keyed, no
    Python-only path) as the standing reason, with the reopening condition
    being a JetBrains-documented non-npm discovery path, not merely
    "JetBrains plugin work starts".

**From design B, conditionally:** the engine punch-list items A does not
need now (the pyo3 feature gate, the offset-aware entry) should stay
sequenced exactly where B's falsifiers would pull them in, and the final
doc should copy B's framing of them as prerequisites of the *fallback*
architecture, so that if A's falsifiers 1-3 fire, the pivot plan is already
written.

## Final ranked verdict

**1. Design A: ship-first (8.4).** On this lens it is not close. Design A
is the only draft that ships user-visible value from existing assets in its
first two weeks, the only one with no binary distribution matrix, the only
one whose every stopping point leaves shipped low-maintenance products
rather than infrastructure, and the one that asks the engine for the least
speculative work (two small additive changes versus a cross-cutting feature
gate plus a contract reservation). Its known overhang, the possible
Rust rewrite, is deferred, priced, and survivable; design B's costs are
prepaid and partly speculative. Its two real underplays (completion in
broken buffers, venv install friction) are absorbable with the grafts
above and do not change the shape of the plan.

**2. Design C: ecosystem-first (5.6).** Second by a small margin, and for a
specific reason: its *total commitment is capped*. C refuses the two
permanent cost centers (the typed-expression transform and a
JetBrains-native codebase) that every blowup story in the corpus runs
through, its steady-state estimate is the most credible number any draft
states, and its claims survived fact-checking best, including checks that
killed its own rungs. It loses to A because its ladder spends the scarcest
early weeks on the audience tail, defers the universal CI artifact to
last, and rests its distinctive spend on a falsifier (F1) it rates as
genuinely open.

**3. Design B: platform-first (5.3).** Third by a nose, and the ranking
needs its caveat stated: B has the best end state, the best falsifier
discipline, and the highest-salvage early work. It loses on exactly what
this lens weighs: five months to the headline feature, two weeks of
invisible work before anything ships, an underpriced M0, a scheduled tail
(JetBrains plugin, typed layer) containing the two permanent cost lines C
refuses, and the only two claims in the contest that the evidence
contradicts or overstates (web-types M5, the "abandoned" pygls narrative).
The B-versus-C margin is inside the noise of this rubric; B ranks below C
because C's overclaims are ordering mistakes while B's are factual, and
because B's plan, as written, schedules the permanent costs rather than
gating them out.

**Flip conditions**, stated so the final doc can revisit:

- If real adoption evidence already existed (marketplace installs, editor
  feature requests from actual users), B's pause-point logic inverts and B
  rises to second, possibly first: prepaying the platform is rational once
  the audience is proven.
- If A's falsifier 3 fires (fail-fast UX makes the server feel broken while
  typing), the tree-sitter grammar becomes load-bearing and the correct
  plan becomes A's rungs 0-2 followed by B's M1/M3 architecture; that
  hybrid, not C, is the successor plan.
- If F2's audience data shows citry users meaningfully spread beyond
  VS Code plus PyCharm, C's breadth rungs stop being tail-chasing and its
  ordering critique softens (though its CI-checker deferral does not).

The composite this judge would hand the final doc: **design A's ladder as
the spine, with grafts 1-10 applied, and design B's M0/M3 architecture
documented as the pre-written pivot** for the day A's falsifiers demand it.

## Sources

The three drafts and five recon reports in this directory (all dated
2026-07-07), read in full. Repo spot-checks this pass:
`packages/py/citry/pyproject.toml:48-49`,
`crates/citry_template_parser/Cargo.toml:12`,
`crates/citry_template_parser/src/parser_context.rs:31-62`,
`crates/citry_core_py/src/template_parser.rs:33-38`,
`packages/py/pygments_citry/` (directory listing). Fresh web checks this
pass (accessed 2026-07-07):

- pygls on PyPI (v2.1.1, 2026-03-25, Python 3.9-3.14):
  <https://pypi.org/project/pygls/>
- IntelliJ Platform web-types documentation (discovery via `package.json`
  or IDE plugin only; no Python-only registration path):
  <https://plugins.jetbrains.com/docs/intellij/polysymbols-web-types.html>
