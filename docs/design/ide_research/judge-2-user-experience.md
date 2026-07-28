# Judge 2: user-experience verdict on the three IDE-integration drafts

**Date: 2026-07-07. Role:** adversarial judge over
[`design-A-ship-first.md`](design-A-ship-first.md),
[`design-B-platform-first.md`](design-B-platform-first.md), and
[`design-C-ecosystem-first.md`](design-C-ecosystem-first.md), judging from one
lens only: **the end user**, a Python/web engineer adopting citry, in the
editor they already use. Architecture elegance, maintainer economics, and
Rust doctrine matter here only insofar as they change what that user sees
and when.

Terms used throughout, defined once. **LSP** (Language Server Protocol) is
the editor-agnostic protocol a separate "language server" process speaks to
give an editor diagnostics, completion, hover, and go-to-definition. A
**TextMate grammar** is a regex-based highlighting grammar (the base format
in VS Code, also readable by JetBrains and Sublime); an **injection grammar**
splices such rules into another language's files, which is how strings inside
Python files get foreign coloring. **tree-sitter** is an error-tolerant
parser framework Neovim, Zed, and Helix use natively for highlighting.
**Pest** is the Rust parser generator citry's template grammar is written in;
it fails fast (one error, no partial tree). A **vsix** is VS Code's extension
package. **LSP4IJ** is Red Hat's free LSP client plugin for JetBrains IDEs.
**Pylance** is the closed language server behind VS Code's Python extension.

## What was read and verified for this judgment

- All three drafts in full, plus the five recon reports in this directory
  (`recon-citry-tooling-surface.md`, `recon-python-template-tooling.md`,
  `recon-lsp-architectures.md`, `recon-vue-tooling.md`,
  `recon-framework-tooling-field.md`) as the fact base.
- Repo spot-checks (2026-07-07): the Pygments package exists with both
  lexers (`packages/py/pygments_citry/pygments_citry/{citry_html.py,lexers.py}`);
  the `citry` console script is registered
  (`packages/py/citry/pyproject.toml`, `[project.scripts]`); pyo3 is an
  unconditional dependency of the parser crate
  (`crates/citry_template_parser/Cargo.toml:12`); `TagRules` is
  `#[pyclass]`-exposed (`crates/citry_template_parser/src/parser_context.rs:31`);
  the built-in tag list lives at
  `crates/citry_template_parser/src/constants.rs:55-56`; and the standing
  staged-build decision reads as all three drafts claim
  (`docs/design/source_languages.md`, sections 4.4-4.5).
- Fresh web checks (2026-07-07, all fetched live this pass):
  - pygls is at **v2.1.1, released 2026-03-25**, Python 3.9-3.14, multiple
    maintainers (PyPI). Design A's claim verified.
  - The **Python Developers Survey 2024** (PSF/JetBrains) puts main-editor
    share at **VS Code 48%, PyCharm 25%**, VS Code up 7 points year over
    year. Design C's load-bearing numbers verified.
  - The **LSP4IJ user-defined language server** doc confirms: servers can be
    declared without any plugin, mapped by file name pattern, and shared as
    importable templates. It does **not** confirm that a user-defined
    server's features surface inside `.py` files the IDE's Python plugin
    already owns; it even warns that custom file-type mappings can cost
    existing syntax features. The PyCharm attach question stays open for all
    three drafts.

Web access worked this pass; no training-knowledge claims are load-bearing
below.

## How this judgment scores

Six dimensions, weighted for the adopting user. Every score is
**discounted by when the thing ships and how likely it ships as designed**,
because a feature the user gets in month two and a feature promised for
month six are not the same feature to someone evaluating citry this quarter.
Where a draft's undiscounted end state would score differently, the text
says so.

| Dimension | Weight | The question |
|---|---|---|
| First-day experience | 0.20 | Install the extension: does highlighting just work in component template strings, and how soon does that day one exist? |
| Daily-driver features | 0.25 | Diagnostics as you type, completion of component names/kwargs/slots, go-to-component, hover; behavior mid-keystroke; what setup gates them |
| VS Code + Pylance | 0.15 | The 48% editor: coexistence, install shape, interpreter handling |
| PyCharm | 0.15 | The 25% editor: what actually reaches it, with how much friction |
| Degradation elsewhere | 0.05 | Neovim, Zed, Helix, Sublime, Emacs |
| Ladder ordering | 0.20 | Does the plan front-load what users feel, or what is architecturally interesting? |

## Cross-draft facts the reader should hold first

Three truths apply to all three drafts and none advertises them loudly:

1. **No draft ever colors templates inside `.py` files in PyCharm.** All
   three defer the JetBrains-native plugin that does real string injection
   (a PSI plugin, per `recon-python-template-tooling.md` section 5.2), and
   JetBrains' TextMate-bundle mechanism cannot touch a file type the Python
   plugin owns. Only design C states this plainly (its "Note A",
   `design-C-ecosystem-first.md:472-480`). A quarter of the surveyed audience
   gets, at best, LSP features without inline coloring under every plan on
   the table. The final design must say this to PyCharm users in C's honest
   register, and must carry the native-injection plugin as a named,
   triggered future rung rather than an implicit never.
2. **Mid-keystroke diagnostics are one squiggle at a time in all three.**
   Every draft keeps the Pest parser as the sole diagnostic authority, and
   Pest is fail-fast (`recon-citry-tooling-surface.md` section 3.2). B's and
   C's tree-sitter layer buys tolerant highlighting and completion context,
   not multi-error diagnostics. The daily "red squiggles while typing"
   experience differs less across drafts than their rhetoric suggests.
3. **The PyCharm attach question is unresolved everywhere.** Whether any
   second LSP client (native API or LSP4IJ) will surface features on `.py`
   documents PyCharm already owns is unverified in the corpus and in my own
   check. B flags it sharpest (falsifier 3) but schedules the spike months
   in; A assumes it with a falsifier; C does not flag it at all for its
   primary PyCharm route.

---

## Design A: ship-first

### What the adopting user gets, and when

Color in VS Code (inline strings and template files) about two weeks in, via
a universal vsix with no binaries and no configuration. A `citry check` CLI
about a month in, working in every editor's terminal. Inline diagnostics
from the real parser about two months in, then completion, hover, and
go-to-component shortly after, all served by a pygls server installed with
`pip install citry[lsp]` into the project's environment. Neovim/Zed/Helix
users get the server's features but no highlighting; PyCharm users get a
docs page.

### Scorecard

| Dimension | Score | Reasoning |
|---|---|---|
| First-day experience | 8.5 | The best in class where it counts: VS Code inline highlighting keyed on exact attribute names, ~2 weeks out, zero config, zero binaries. PyCharm's first day is empty. |
| Daily-driver features | 7.5 | Full retention set (diagnostics, completion, hover, go-to) at ~2 months, the earliest of the three by a wide margin, and the only v1 that can see dynamically registered components (registry mode). Docked for the per-project `pip install` gate and stale-tree completions mid-keystroke. |
| VS Code + Pylance | 8 | Proven second-server coexistence, the `@vscode/python-extension` interpreter API, simplest possible distribution. The pip-install step is the one visible seam, and A itself predicts it as the top support burden (`design-A-ship-first.md:340-343`). |
| PyCharm | 3.5 | The weak flank, with one claim that is wrong (below). Docs-only, manual, venv-dependent, no inline color. |
| Degradation elsewhere | 5 | LSP reach everywhere via PyPI, but tree-sitter editors get features over plain uncolored text, an odd half-experience. |
| Ladder ordering | 9.5 | The cleanest value ordering of the three: every rung is user-felt, each gates on dogfooding, and nothing user-invisible sits in front of color. |
| **Weighted total** | **7.45** | |

### Strongest element

The ladder itself. It is strictly ordered by what a user notices (color, then
CI-grade validation, then live diagnostics, then intelligence), first value
arrives inside two weeks, and the whole retention set exists while designs B
and C are still mid-build. For a framework whose users exist now and are
deciding now, that timing is the single most user-relevant property any
draft offers. The zero-binary distribution (universal vsix plus PyPI) also
makes rung 1 genuinely "install and it works".

### Weakest element

PyCharm. A's coverage matrix promises JetBrains semantics "via the native
LSP API or LSP4IJ" with a channel of "config docs"
(`design-A-ship-first.md:280`, `:249`), but the native LSP API is a plugin
API: an `LspServerDescriptor` lives in plugin code
(`recon-lsp-architectures.md:444-447`, A's own cited recon). No docs page can
reach it. The real docs-only route is LSP4IJ alone, which means the
second-largest audience's setup is: install a third-party plugin, define a
server by hand, and point it at a **venv-specific** command
(`.venv/bin/citry-lsp`), because A's server is not a binary on PATH but a
package inside each project's environment (`design-A-ship-first.md:303-306`).
Per-project, per-machine configuration for 25% of users, with no inline
color, indefinitely.

### Attacks: what the author glossed over

1. **The wrong native-API claim** above. Not fatal, but it inflates the
   PyCharm row of the coverage matrix, and the matrix is what a reader
   compares designs by.
2. **The venv-resident server multiplies configuration.** Every non-VS-Code
   editor config must name the interpreter-specific server path per project.
   Multi-root workspaces (several projects, several venvs, one window) need
   several server instances; the draft never mentions this.
3. **The semantic rungs are gated on the exact thing A predicts will be its
   top support burden.** "Install extension and it works" is true for
   rung 1 and false for rungs 3-4: the user must install `citry[lsp]` into
   each project and the extension must find the right interpreter. B and C
   bundle the binary; their diagnostics work on first open. A's honesty
   about the burden (falsifier 2, `design-A-ship-first.md:440-445`) does not
   reduce it.
4. **"Adjusted by text deltas" is unbudgeted work.** The last-good-tree
   pattern (`design-A-ship-first.md:204-211`) needs position adjustment
   logic to stay useful mid-edit; the effort estimate treats it as free.
5. **The priced-in rewrite is also a user-facing migration.** When the pygls
   server is rewritten in Rust (A section 7.3 accepts this), the install
   shape changes from venv package to binary, and every editor config snippet
   A shipped at rung 5 churns. Users pay a second onboarding.
6. **Tree-sitter deferral has a quality cost inside VS Code too.**
   `docs/design/source_languages.md:402-417` calls a tree-sitter grammar
   "the natural way to get correct highlighting boundaries"; A accepts
   documented brace-boundary mis-coloring as permanent low-grade issue
   traffic. Accepted knowingly, but it is the user who files those issues.

---

## Design B: platform-first

### What the adopting user gets, and when

Nothing user-visible for the first ~2 weeks (engine contract work), then
highlighting in VS Code, Neovim, and Helix at ~5-6 weeks (both grammar
families ship in M1), CI checking at ~7-9 weeks, then a 6-10 week silent
stretch while the Rust server is built, then the fullest feature set of any
draft (diagnostics, completion, hover, go-to-definition, find-references,
folding, semantic tokens, error tolerance) landing at roughly months 4-5.5,
followed by an editor rollout including the only one-click PyCharm install
of the three (a thin plugin with the binary bundled). An explicit pause
point after M2 can freeze everything beyond color-plus-CI if adoption
evidence is absent.

### Scorecard

| Dimension | Score | Reasoning |
|---|---|---|
| First-day experience | 7 | Same VS Code quality as A once shipped, plus Neovim/Helix, but ~3-4 weeks later than A for no user-facing reason (see attacks). PyCharm first-day: template files only. |
| Daily-driver features | 7 | Undiscounted this is a 9: the richest v1 set, tolerant completions, zero-setup static-first index, bundled binary. Discounted hard because it arrives after a 6-10 week trough, behind an adoption gate, at months 4-5.5 of focused solo time (calendar reality: longer). |
| VS Code + Pylance | 7.5 | The best end-state answer (binary in the vsix, works offline, no pip, no interpreter dance for the static tier). Same discount for arrival time. |
| PyCharm | 6.5 | The only draft whose PyCharm endgame is "install one thing from the marketplace". Contingent on the unverified attach question, spiked only at M4; web-types claim overstated (below). |
| Degradation elsewhere | 8.5 | Both grammar families plus a real rollout rung; Neovim/Helix get color at M1, earlier than anyone. |
| Ladder ordering | 4 | The weakest property: user-invisible work first, the longest trough in the middle, and an adoption gate placed before any retention feature exists. |
| **Weighted total** | **6.88** | |

### Strongest element

The end-state product definition. If citry's editor support is judged by
what a user experiences once everything ships, B wins: no per-project
install, no interpreter discovery for the default tier, the fullest feature
set, correct highlighting through broken mid-keystroke states, and the only
credible one-click PyCharm story. B is the best answer to "what should this
be in 2028"; the engine contract work in M0 (structured diagnostics, the
`python` cargo feature, the source-map slot) also benefits every alternative
future, including A's rewrite and issue #27.

### Weakest element

The ladder. M0 ships nothing a user can see. M1's grammars do not actually
need M0 (a TextMate grammar and a tree-sitter grammar consume no engine
contract), so first color is delayed weeks for sequencing hygiene that only
the server needs. M3 is a 6-10 week single-rung trough the draft itself
calls out (`design-B-platform-first.md:500-503`). Worst is the pause-point
paradox: falsifier 5 holds M3+ hostage to adoption evidence gathered while
the shipped artifacts are color and CI checking
(`design-B-platform-first.md:422-426`, `:586-593`), but the features that
generate adoption and retention are exactly the M3 features being gated. B
measures the harvest before planting.

### Attacks: what the author glossed over

1. **The web-types claim is contradicted by the corpus.** M5 promises
   "PyCharm completion with zero plugin installed"
   (`design-B-platform-first.md:417`, section 3.6). Design C verified
   against live JetBrains sources that web-types discovery is keyed off
   `package.json`, with no documented path for a Python-only project
   (`design-C-ecosystem-first.md:102-105`). B's own recon (the Vue report,
   lesson 8.1.4) recommended web-types without checking discovery. As
   written, M5's PyCharm dividend is unproven and probably dead; points
   lost for shipping a rung a sibling draft had already falsified on the
   same research date.
2. **"Being lapped" overstates the Django evidence.** B's thesis leans on
   "djlsp is being lapped by djls" (`design-B-platform-first.md:83-85`), but
   the recon says djls is "still flagged by its author as early stage
   ('most features are incomplete')" while the Python djlsp is the one with
   a shipped, used feature set (`recon-python-template-tooling.md:96-97`).
   The corpus also records that Vetur delivered years of user value before
   Volar existed (`recon-vue-tooling.md`, lesson 8.1.5 context). The field
   data supports "the interim generation gets rewritten", which A prices
   in; it does not support "the interim generation was a mistake to ship",
   which is B's actual bet. Users of the interim tools were served the
   whole time.
3. **The PyCharm inline color gap is never stated.** B's matrix row for
   PyCharm lists "TextMate bundle in the plugin"
   (`design-B-platform-first.md:388`) without saying the bundle cannot color
   inside `.py` files (C's Note A). B flags the semantics attach risk and
   stays silent on the color gap; a PyCharm-heavy reader would over-read
   that row.
4. **The attach spike is scheduled backwards.** The single question that
   decides whether 25% of the audience gets B's headline feature inline is
   tested "in week one of M4" (`design-B-platform-first.md:416`), months
   in, after the server exists. The spike costs days against a stub server
   and would re-rank the whole editor strategy if it fails. It belongs in
   week one of the project.
5. **Calendar honesty.** "4-5.5 months of focused solo work" is the
   best-case; this maintainer is also building the framework. The user-lens
   translation: a citry adopter in 2026 Q4 likely experiences B as "nice
   highlighting, check runs in CI, nothing in my editor yet".

---

## Design C: ecosystem-first

### What the adopting user gets, and when

Highlighting for Neovim (and file templates in Zed/Helix) at weeks ~4-7,
VS Code color at weeks ~6-10, a registry-dump CLI at ~8-12, and then a
single 6-10 week rung (R4) that delivers the server, all editor glue, and
packaging at once, putting diagnostics and completion in front of users at
cumulative weeks 13-22. The v1 feature set is deliberately reduced:
diagnostics, name completion, go-to-component, document symbols; **no
hover**, no semantic tokens. PyCharm gets a documented LSP4IJ template
(install plugin, import JSON, install binary) with no inline color, honestly
flagged.

### Scorecard

| Dimension | Score | Reasoning |
|---|---|---|
| First-day experience | 6 | VS Code, the 48% editor, waits 6-10 weeks for color that A ships in 2; the first-served editor holds 4% main-editor share. Quality once shipped is fine (bundled binary later, exact injection). |
| Daily-driver features | 5.5 | The trio arrives last of the three designs (months 4-6), minus hover, minus semantic tokens. Error tolerance and static-first index are real quality wins, but the retention set is thinnest and latest. |
| VS Code + Pylance | 6.5 | Same coexistence posture and bundled-binary shape as B, slightly thinner features, materially later. |
| PyCharm | 5.5 | The cheapest real route any draft found (LSP4IJ user-defined template, verified mechanism, zero plugin code) and the most honest color story (Note A). Docked for three-step onboarding friction on the 25% editor and for not flagging the attach uncertainty at all (below). |
| Degradation elsewhere | 9.5 | The whole thesis, and it delivers: Neovim/Zed/Helix/Sublime/Emacs all get a real story, most of them first. |
| Ladder ordering | 4 | Ordered by artifact canonicality, not by user-felt value: the canonical grammar serves the smallest audiences first, and everything users retain on is bundled into the final rung. |
| **Weighted total** | **5.99** | |

### Strongest element

Evidence discipline. C is the only draft that re-derived its audience
weighting from fresh survey data (verified this pass: VS Code 48%, PyCharm
25% main-editor share), the only one that killed a rival's rung with a
verification (web-types discovery is `package.json`-keyed, gating what B
ships blind), and the one whose per-editor distribution mechanics (Zed's
repo+rev-only grammars, Helix `subpath`, the nvim registry, the LSP4IJ
template) are checked rather than assumed. Its falsifier F1 honestly
concedes the case in which its own core bet collapses. The LSP4IJ
user-defined-server template is a genuine find every other design should
steal.

### Weakest element

The value ordering contradicts the draft's own data. C's verified numbers
say 73% of the audience lives in two editors; C ships to those two editors
last (VS Code color at R2, semantics at R4's very end) and least (no hover),
while spending its first 3-5 focused weeks on a grammar whose inline-string
dividend, by C's own falsifier F1
(`design-C-ecosystem-first.md:672-681`), may reach only Neovim, in a
project whose house style makes inline strings the primary authoring mode
(CLAUDE.md, "Component `template` / `js` / `css` are multiline strings").
Coverage-per-artifact is the maintainer's metric; hours-to-my-editor is the
user's, and C optimizes the former.

### Attacks: what the author glossed over

1. **No hover in v1 is a real daily-driver cut, unjustified.** Hover on
   `<c-Card>` showing the component's docs and inputs is how users read a
   component without leaving the call site; the data is already in C's own
   index (docstrings from `Kwargs`), both rivals ship it in v1, and the
   draft drops it in one line (`design-C-ecosystem-first.md:329-332`) with
   no cost argument. This looks like scope discipline for its own sake.
2. **The PyCharm attach uncertainty is presented as solved.** The coverage
   matrix says "Full v1 server via LSP4IJ template"
   (`design-C-ecosystem-first.md:464`). What C verified is that user-defined
   servers exist and are importable; whether their features surface inside
   `.py` files PyCharm's Python plugin owns is exactly the question B
   flags as its falsifier 3, and my own check of the LSP4IJ doc found no
   promise (and a hint of file-type conflicts). C's F7 covers setup
   friction, not attach capability. The matrix row for the second-largest
   editor rests on an unflagged assumption.
3. **"Every rung ships user-visible value" strains.** R0 is invisible; R3
   (`citry inspect --json`) is invisible to editor users; between R2 and
   the end of R4, the dominant editors receive nothing new for roughly a
   quarter. The claim is true for Neovim and false for most users.
4. **R4 is a kitchen-sink rung.** Server, document store, index, check
   subcommand, PyPI wheels, release archives, VS Code wiring, Mason, Zed,
   LSP4IJ template, Helix and Neovim snippets, all inside 6-10 weeks. B
   budgets 6-10 weeks for the server alone and 2-3 more for rollout; C's
   estimate for strictly more scope is thinner than its own field
   calibration suggests.
5. **The grammar-mirror tax lands before the syntax frontier calms.** C
   itself names four-going-on-five hand-synced taxonomy mirrors as "the
   single most concerning line" and falsifier F4 admits grammar churn kills
   the ordering, yet the ladder still puts both grammar artifacts in the
   first three rungs of an actively-moving V3 syntax.

---

## Graft recommendations: what the final design should steal

Regardless of which skeleton wins, the composite is stronger than any
single draft:

**From A (take the spine):**

- The rung order: publish `pygments-citry` now; VS Code extension with the
  injection grammar next; `citry check` before any server; live server
  before intelligence; long-tail editors by documentation. It is the only
  ladder ordered by what users feel.
- The universal-first distribution posture at the grammar rung (no
  binaries, no platform matrix, until a server exists to need one).
- Registry-mode `TagRules` derivation shared between the CLI and the
  server, with the static fallback, exercised in batch (CI) before it runs
  live.

**From B (take the destination and two safeguards):**

- The engine contract items as an early, parallel workstream: structured
  diagnostics across PyO3 (any server needs it), and the cheap source-map
  slot reservation in the compiler output contract before more consumers
  exist. The `python` cargo feature can wait for the rung that needs a
  binary.
- **The PyCharm attach spike, moved to week one of the whole program.**
  Days of work against a stub server (native API and LSP4IJ, on `.py`
  documents), and it re-prices the second-largest audience for every
  design. No draft should ship its coverage matrix before this answer
  exists.
- The bundled-binary vsix and thin JetBrains plugin as the named endgame
  that resolves A's venv friction when (not if) the server outgrows pygls;
  B's M3-M4 design is the executable plan for A's priced-in rewrite.

**From C (take the evidence and the PyCharm glue):**

- The survey-weighted audience model as the ladder's ordering function,
  and the practice of verifying a rung's distribution mechanism before
  scheduling it (the web-types kill is the model).
- The LSP4IJ user-defined-server template, shipped as an importable JSON on
  the docs site the same week the server first runs. It is the cheapest
  real PyCharm route for every design, including A's pygls server (the
  template's command field can point at a venv path, with the caveat
  documented).
- Note A's honest framing of the PyCharm inline-color gap, verbatim, in
  user-facing docs.
- Claiming the `citry` name on Open VSX, Marketplace, Package Control, and
  crates.io immediately (all three drafts agree; C states it most
  operationally).
- The tree-sitter grammar as the tolerant-parser asset when a server needs
  error tolerance or Neovim demand materializes, with C's F1 spike run
  first so the inline-injection dividend is measured before the 3-5 weeks
  are spent.

## Final verdict

| Rank | Draft | Weighted score | One-line judgment |
|---|---|---|---|
| 1 | **A: ship-first** | **7.45** | The only plan ordered by what users feel, and the only one whose retention features exist while the adoption window is open; its PyCharm story and venv-resident server are real flaws, both repairable by grafts. |
| 2 | **B: platform-first** | **6.88** | The best end state and the best PyCharm endgame, wrapped in the worst ladder: user-invisible work first, a quarter-long trough, and an adoption gate placed before the features that create adoption. |
| 3 | **C: ecosystem-first** | **5.99** | The best-verified draft and the best long-tail story, but it ships last and least to the 73% of users its own data says matter most, and drops hover for no stated reason. |

Stated honestly: on **undiscounted end-state quality** the order is B, then
A, then C. This judgment ranks A first because the lens is a user adopting
citry now, and the expected experience over the first year favors the design
whose diagnostics, completion, and go-to-component exist at month two rather
than month five, behind no pause gate. B's falsifier 5 concedes the point
from the other side: it agrees the expensive rungs should wait for adoption
evidence, and A is the design that generates that evidence fastest, while
building nothing (grammars, CLI, discovery code, LSP feature tests, docs,
marketplace presence) that a later B-shaped server does not reuse. The
losing move would be to average the drafts; the winning move is A's ladder,
B's destination and week-one PyCharm spike, and C's evidence discipline and
LSP4IJ glue, as itemized above.

## Sources

The fact base is in-repo: the three drafts and the five recon reports in
this directory (all dated 2026-07-07), read in full, plus the repo
spot-checks cited with `file:line` in "What was read and verified for this
judgment" above. The fresh web checks from that section (accessed
2026-07-07):

- pygls on PyPI (v2.1.1, released 2026-03-25, Python 3.9-3.14):
  <https://pypi.org/project/pygls/>
- Python Developers Survey 2024, PSF/JetBrains (main editor: VS Code 48%,
  PyCharm 25%): <https://lp.jetbrains.com/python-developers-survey-2024/>
- LSP4IJ user-defined language server documentation (servers declared
  without plugin code, file-name mappings, importable templates, the
  warning that custom file-type mappings can cost existing syntax
  features):
  <https://github.com/redhat-developer/lsp4ij/blob/main/docs/UserDefinedLanguageServer.md>
