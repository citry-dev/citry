# Plan: Citry v1 beta launch-readiness research

**Status (2026-07-23): approved research charter; Stages 0 and 1 complete;
Stage 2 bounded pilot complete and circuit breaker awaiting maintainer scope
decision; Stage 1 product decisions deferred to Stage 10.**

This document plans the investigation that will produce Citry's actual v1 beta
launch plan. It does not declare the repository release-ready, choose the final
release scope, prescribe the final review order, or authorize commits, version
changes, tags, publishing, GitHub issues, deployments, external contact or
posts, account/form/channel creation, analytics, or changes to repository,
organization, registry, domain, or other service settings.

The next phase starts only after the maintainer approves this research plan.
Its result will be an evidence-backed readiness report and an ordered review
backlog that the maintainer can accept, test in a live project, and sign off in
manageable batches before any release commit is made.

For repository operating rules, see [`/CLAUDE.md`](../../CLAUDE.md). For the
monorepo and release model, see [`/docs/codebase.md`](../codebase.md).

---

## 1. Decision and desired outcome

The launch work will use two distinct planning layers:

1. **Research plan, this document.** Define what must be investigated, what
   evidence will count, which outside projects and standards will be studied,
   and what artifacts the investigation must produce.
2. **Execution plan, produced after the investigation.** Define the actual
   release scope, dependency-aware review order, blocking fixes, live-project
   acceptance runs, commit batches, version changes, publishing rehearsal,
   launch work, and post-launch support.

This separation matters because the repository currently contains many months
of overlapping work. A filename, a test name, a design-doc status, and an open
issue can each describe a different point in the same feature's history. The
execution plan should follow verified current behavior and maintainer approval,
not the most confident piece of prose found first.

The desired research outcome is one coherent answer to five questions:

1. What product promise does "v1 beta" make to professional teams,
   professionals working alone, and hobbyists?
2. What is implemented, what is still being developed, and what is deliberately
   outside that promise?
3. In what order can the maintainer review and live-test the work without
   reviewing a consumer before its lower-level contract?
4. What code, packaging, documentation, infrastructure, security, community,
   and launch work remains?
5. What evidence must be green before the release is cut, and what evidence may
   follow during the beta?

## 2. Initial exploration baseline

These are routing signals from the 2026-07-23 initial exploration. They are not
the final readiness audit. Counts describe the tree before this document was
added.

### 2.1 Working tree and documentation shape

- The working tree had **673 dirty paths**: 173 modified, 5 deleted, and 495
  untracked. The tracked diff covered 178 files with about 29,485 additions and
  4,815 deletions; untracked file contents are not included in that diff count.
- The baseline commit was
  `53aec721b7b13309880919f0ff3979f08a6b2245`. Dirty-path counts used
  `git status --short -uall`; tracked diff totals used `git diff --stat`.
- The largest dirty areas were `packages/` (249 paths), `docs_site/` (211),
  `docs/` (146), and `crates/` (32). This is several product and infrastructure
  workstreams, not one review batch.
- [`docs/design/`](.) has 42 top-level Markdown design documents. Four evidence
  directories add more than 100 research and harness files:
  `alpinejs/`, `events_research/`, `ide_research/`, and `ui_research/`.
- `docs_site/content/` has 54 Markdown pages, while the docs builder, guards,
  examples, tests, static assets, and workflows are also substantially changed.
- Three large untracked reference archives total about 325 MB:
  `old-djc.zip`, `old-chk.zip`, and `old-vuetify.zip`. Their provenance,
  privacy, license, purpose, and source-control disposition need an explicit
  decision. They must not drift into a release commit by accident.

### 2.2 Preliminary package and contract map

"Preliminary state" below means only what the initial repository and registry
scan supports. It does not mean release-ready.

| Product or contract | Declared version | Distribution role | Preliminary state |
| --- | --- | --- | --- |
| `citry-monorepo` | `0.0.0` | Private root Python workspace and tooling coordinator | Active internal workspace; it is not a public distribution |
| `citry` | `0.2.0` | Public Python framework | Published as `0.2.0`; actively and extensively changed in the working tree |
| `citry-core` / `citry_core` | `1.3.0` | Public Python bindings with the Rust extension | Published as `1.3.0`; parser, binding stub, and tests have active working-tree changes |
| `pygments-citry` | `0.1.0` | Planned public Python Pygments plugin | Implemented locally and used by the docs; no PyPI project was visible in the initial scan |
| `citry-client` | `0.0.0`, private | TypeScript source for the generated Events browser runtime | Active internal build package, with generated output shipped inside `citry` |
| `citry-events/1` | protocol major 1 | Language-neutral Events wire contract | Active untracked normative schemas, test corpus, validator, and specification |
| `citry-client-graph/1` | protocol major 1 | Language-neutral browser ownership contract | Active untracked normative schema and specification |
| `citry_core_py` | `1.1.0` | Internal PyO3 binding crate for `citry-core` | Binding glue with active cross-language contract changes; not published on crates.io |
| `citry_html_transform` | `1.0.3` | Internal HTML transformation crate | Described as stable in agent guidance; current status still needs source/test verification |
| `citry_template_parser` | `1.0.0` | Internal parser/compiler crate | Active implementation frontier with extensive working-tree changes |
| `python_safe_eval` | `1.0.0` | Internal expression-evaluation crate | Described as stable in agent guidance; current status still needs source/test verification |
| `docs_site` | unversioned | Internal documentation application and static-site builder | Active replacement site with extensive source, content, test, and workflow changes |

The Rust crates' version and edition metadata are not currently uniform. That
may be valid because they are internal, but the documentation makes broader
statements that the audit must reconcile.

Planned ecosystem products such as `citry-ui`, editor plugins, and other host
language bindings belong in the product roadmap. They do not become v1 beta
blockers merely because a design exists. The product charter must decide which,
if any, are part of the beta promise.

### 2.3 Conflicts already found

The deeper audit must resolve, rather than repeat, conflicts such as these:

- [`docs/codebase.md`](../codebase.md) labels most of itself unverified, describes
  both one and several Python packages, and contains both lockstep and
  independent versioning narratives.
- Design docs describe Events v1, Alpine integration, output caching,
  introspection, debug tools, hot reload, and much of the runtime as implemented.
  Several associated GitHub issues are still open, including the introspection
  and client-runtime issues.
- Resolved 2026-07-23: the docs-site caching guide, homepage, reference roster,
  and content audits now describe the shipped component and fragment output
  caches.
- The `citry` wheel package-data declaration and publish smoke test cover the
  dependency client JavaScript. Fresh wheel and source-distribution builds in
  the initial exploration omitted the new Events client runtime because it
  lives under a different package-data path. The current publish smoke does not
  detect that omission.
- Root guidance says Rust edition 2024, while two internal crate manifests still
  declare edition 2021. The root Rust version floor, nightly toolchain, and prose
  also need one verified explanation.

These examples justify a systematic audit. They do not settle which source is
correct.

### 2.4 Public release surface signals

Observed on 2026-07-23:

- PyPI served `citry 0.2.0` and `citry-core 1.3.0`. Their uploads used Trusted
  Publishing and carry provenance attestations. `pygments-citry` returned 404.
- The published `citry` project description contains older examples, including
  an obsolete browser callback name and an expression that conflicts with the
  documented no-builtins policy. Its repository-relative links and benchmark
  image also resolve to broken PyPI paths. The `citry-core` description contains
  obsolete API and layout guidance. Public package descriptions therefore need
  to be tested as released artifacts, not inferred from working-tree READMEs.
- `https://citry.dev/` returned a GitHub Pages 404. The latest `main` runs for
  the full Check, docs check, and docs deploy workflows were failing. The Python
  and Rust matrix workflows on the same commit passed. The working tree contains
  large CI and docs changes, so both the current public baseline and the proposed
  replacement need testing.
- The `main` branch had no branch protection or repository ruleset. GitHub
  Discussions were disabled even though the issue-template configuration links
  questions there. The organization did not require two-factor authentication.
- The public organization Projects page showed no projects. An owner-level API
  inventory could not be read with the current token because it lacks
  `read:project`. The research must confirm this with appropriate read-only
  access and decide whether a Project is useful.
- The organization profile was largely blank and had no public profile README.
  Public identity, maintainer visibility, recovery ownership, and contact routes
  therefore belong in the community audit.

### 2.5 What the quick checks do and do not prove

The initial exploration passed `git diff --check`,
`python scripts/validate.py`, `uv lock --check`, Cargo metadata loading, both
protocol validators, the private `citry-client` package check, and a strict
docs-site build check. The full Rust, Python, installed-artifact, and browser
matrices were not run. The four custom validators currently cover:

- Rust submodule registration against the Python binding stub;
- Cargo workspace membership;
- Dependabot entries for Python package directories; and
- one Rust toolchain pin comparison.

They do not prove that the full gate passes, packages contain every required
asset, published examples run, documentation claims match code, browser
protocols work in a live app, release workflows can publish the next versions,
or GitHub and PyPI are ready for a public beta.

## 3. Research outputs

The investigation will store all sanitized research artifacts in the dedicated
[`docs/design/v1_beta_research/`](v1_beta_research/) directory. This document
remains the research charter and index rather than accumulating the findings
itself. Security-sensitive evidence and private application data must not be
stored in that directory; section 4.6 defines their handling.

| Output | What it must contain | Completion gate |
| --- | --- | --- |
| Product and beta charter | Audiences, jobs, public promise, non-goals, support floors, compatibility promise, beta feedback model | Independently reviewed provisional charter exists; decisions are retained for Stage 10 rather than treated as approved promises |
| Working-tree change ledger | Every dirty path, purpose, originating design, dependency group, generated/source status, risk, tests, live scenario, and review decision | Every path is owned by exactly one review batch or explicit non-commit disposition |
| Design closure register | Every recursively discovered design artifact, current status, implementation proof, tests, docs, open questions, follow-ups, issue links, and maintainer decision | Every actual design is individually classified; evidence gaps and follow-ups are recorded and routed |
| Package and contract matrix | Public, private, internal, and protocol packages; versions; dependency graph; registry state; artifact contents; release workflow; support matrix | Every unit is individually classified and current build/inspect/install observations or untested gaps are recorded |
| Script and tooling register | First-party repository scripts, package commands, validators, docs utilities, workflow-called commands, their callers, safety, portability, tests, and documentation | Every in-scope executable entry point is inventoried; exclusions, defects, and unknowns are recorded and routed |
| Metadata and configuration register | First-party package, workspace, toolchain, lock, GitHub, community, legal, ignore, submodule, and release metadata plus cross-file invariants | Every in-scope file is inventoried and parsed where possible; exclusions, inconsistencies, and access limits are recorded |
| Technical readiness dossier | Code review findings, test coverage, CI, security, concurrency, compatibility, generated artifacts, and release risks | Each finding states its evidence level; failures and unknowns are reproducible or explicitly bounded and routed |
| Live-project acceptance matrix | Real application scenarios, proposed `demo/<host>/` reference apps, browsers, upgrade paths, expected behavior, evidence available now, and later maintainer sign-off | Every charter workflow has a proposed scenario; current evidence gaps and later execution/sign-off work are explicit |
| Documentation and public-surface audit | README, docs content, generated API reference, links, images, examples, site deployment, PyPI pages, releases, and search/SEO/accessibility checks | Each surface is observed or marked untested; every stale, broken, private, or unknown result is routed |
| Repository, organization, Project, and community audit | GitHub settings, Projects, issues, Discussions, security settings, governance, contribution path, support channels, and maintainer operations | Public facts, approved owner-only observations, unknowns, and recommended decisions are recorded without changing settings |
| Benchmark charter and current-evidence audit | Separate methodology, baselines, scenarios, variance, reproducibility, existing results, limits, and publication rules | Independent review accepts the method; missing measurements and later report work are routed separately |
| Ecosystem and outreach report | Comparable products, proposed user research, positioning, demo strategy, launch channels, feedback funnel, and post-launch support | Research protocol, candidate audiences, consent/privacy rules, success measures, and approval points are explicit |
| Actual v1 beta execution plan | Ordered review batches, blockers, deferred work, commit plan, release rehearsal, launch checklist, rollback, and post-launch monitoring | Maintainer approves it after reviewing the research |

## 4. Evidence and classification rules

### 4.1 Evidence levels

Every material conclusion will carry one of these labels:

- **Verified implementation:** walked from the live source through callers and
  tested in the current working tree.
- **Artifact verified:** confirmed in a built wheel, source distribution,
  generated client asset, static docs build, or deployed site.
- **Live-project verified:** exercised in the maintainer's representative
  project with the environment and expected result recorded.
- **Publicly observed:** inspected on PyPI, GitHub, `citry.dev`, or another
  external service on a stated date.
- **Document-claimed:** stated by a design or status document but not yet proved
  against current implementation.
- **Inference:** a reasoned conclusion that still needs a falsifying test or
  maintainer decision.

No launch decision may rely only on a document-claimed or inferred status.

### 4.2 Design-document statuses

Each actual design discovered by the recursive inventory receives exactly one
current status:

1. **Verified complete:** the in-scope behavior exists, its important cases are
   tested, public/internal docs are aligned, follow-ups are disposed, and the
   maintainer has accepted the result.
2. **Implemented, awaiting review:** implementation and tests exist, but the
   maintainer has not completed source review and live validation.
3. **Partially implemented:** some accepted scope is still absent or unproved.
4. **Active research or design:** the document is currently shaping a decision.
5. **Parked proposal:** a valid future idea with no current implementation
   commitment.
6. **Superseded or withdrawn:** replaced or deliberately abandoned; retained
   only when it still explains the current direction.
7. **Historical evidence:** retained to explain a decision or failed
   experiment, with no active work implied.
8. **Unclear:** conflicts or missing evidence prevent classification.

"Implemented" and "done" inside a design doc are evidence inputs, not the
final classification.

### 4.3 Package and contract statuses

Each distribution, crate, private package, protocol, application, and tooling
workspace receives these independent classifications:

- **Lifecycle:** published public, planned public, private/internal, proposed,
  superseded, or retired.
- **Implementation:** verified complete for its accepted scope, implemented
  awaiting review, partial, actively changing, proposed, or historical.
- **Maintainer acceptance:** unreviewed, source review in progress, source
  accepted, live validation pending, or live accepted.
- **Beta role:** one or more of launch-facing product, required dependency,
  optional companion, or outside the beta.
- **Delivery:** independently released, embedded in another artifact,
  internal-only, or deferred roadmap.
- **Release readiness:** unassessed, evidence incomplete, blocked with blocker
  references, ready for maintainer sign-off, or accepted for beta release.

"Published," "implemented," "reviewed," and "release-ready" are not
synonyms. A package is called done only when the matrix states which dimension
is done and supplies the corresponding evidence.

### 4.4 Follow-up handling

For each design, the closure register records:

- the exact follow-up and why it exists;
- whether it is in the accepted design scope, a beta blocker, a beta follow-up,
  or an unrelated roadmap idea;
- the current code/test/doc evidence;
- an existing GitHub issue, if one accurately tracks it;
- a candidate issue title and acceptance criteria when no issue exists; and
- the maintainer's decision.

Issues will not be created during the research without explicit approval. Once
approved, one actionable outcome gets one issue, and the design doc links it.
Vague possibilities remain design notes until they have a concrete user problem
and acceptance criteria.

### 4.5 Working-tree ownership

The change ledger must account for every dirty path without editing, moving, or
discarding it. Each entry records:

- source file, generated file, vendored evidence, local reference, binary
  archive, or deletion;
- feature or infrastructure workstream and originating design;
- prerequisite and consumers;
- public contract risk and migration impact;
- automated checks and live acceptance scenario;
- maintainer review state;
- intended commit batch or explicit local-only/archive disposition.

Generated files are reviewed together with their source and reproducible build
command. Large archives and screenshots receive provenance, privacy, license,
and necessity checks before any source-control decision.

### 4.6 Sensitive evidence and disclosure

Potential vulnerabilities receive a redacted public blocker entry and a private
record in a maintainer-approved location until coordinated remediation and
disclosure are complete. The design directory must never contain credentials,
tokens, owner-only settings exports, private vulnerability reproduction detail,
proprietary live-project data, or identifying cohort data.

Live-project and external-user evidence is sanitized to the minimum needed to
support a finding. Consent, retention, access, and deletion rules are approved
before any cohort contact, analytics, form, or recording. A missing safe storage
location blocks collection, not the rest of the read-only audit.

## 5. Research stages

The stages below define the investigation order. They do not preselect the
final implementation order.

### Stage 0: establish and refresh the evidence baseline

**Questions:** What commit, toolchain, and working-tree state does each finding
describe? Which files are source, generated output, references, or local-only
evidence? What changed while the research was in progress, and did it invalidate
an earlier observation? Are there overlapping edits whose provenance is unclear?

**Work:** Capture HEAD, submodule state, tool versions, complete dirty-file
inventory, diff statistics, untracked sizes, manifest list, workflow list,
recursive design-artifact list, exact inventory commands, and current
public-service snapshot as a timestamped baseline. This does not freeze the
repository or ask other feature work to stop. Refresh the baseline before each
research stage and review batch, classify newly changed paths, and rerun an
observation when its inputs changed. Record the baseline identifier, commands,
environment, UTC observation time, and sanitized outputs in the evidence log.
Classify sensitive findings before recording detail, and preserve all user
work.

**Output:** initial reproducible baseline, a timestamped change ledger with
subsequent baseline deltas, and a sanitized
`docs/design/v1_beta_research/evidence_log.md` recording commands and
observations. Sensitive evidence follows section 4.6 instead.

**Gate:** every finding names the baseline it describes, every observed delta is
reconciled, and no research action risks user work. Concurrent implementation
may continue; it creates a new baseline rather than making the research invalid
by definition.

### Complexity and approval circuit breaker

Stages 2 and 3 begin with a bounded pilot: one representative vertical slice
and a small sample of design/package records. The pilot must estimate the number
of work units, dependency fan-out, evidence depth, delegated tasks, token/tool
budget, and likely review cost before the full audit expands.

The default delegation cap across Stages 2 and 3 is three concurrent subagents
and six bounded delegated tasks in total. Nested delegation, follow-up turns,
and retried or re-scoped delegated tasks count toward that cap. If later
expansion reveals an unbounded or more-than-linear shape, more than twice the
pilot estimate, repeated new layers of dependencies, materially higher
token/tool cost than forecast, or a need to exceed that cap, stop and return to
the maintainer with:

1. the discovered scope and why it expanded;
2. what useful work is already complete;
3. options to narrow, sequence, sample, automate, or defer the remainder;
4. the estimated cost and confidence of each option; and
5. a recommended revised scope.

No bulk delegation or deeper expansion proceeds until the maintainer approves
the revised approach. A smaller complete interim checkpoint is preferable to a
large set of unfinished delegated threads; it does not replace the approved
research completion criteria.

### Stage 1: define the product and version promise

**Questions:** What makes v1 beta meaningfully different from the current
`0.x` releases? Does the release use a PEP 440 pre-release such as `1.0.0b1`, a
`0.x` beta milestone, or another explicit convention? Which public APIs are
stable during beta? Which Python, browser, operating-system, host-framework,
and deployment versions are supported? Which first-party packages are part of
the launch?

**Work:** Draft audience and job statements; define launch-critical workflows,
compatibility and deprecation policy, beta support expectations, security
response, and explicit non-goals. Reconcile independent package versioning with
the phrase "Citry v1 beta."

**Output:** product and beta charter.

**Gate:** an independently reviewed provisional charter exists and its open
decisions are routed to Stage 10. Stages 2 through 9 may test its hypotheses and
alternatives, but may not perform irreversible feature triage or claim a public
beta promise from them.

### Stage 2: reconstruct the change graph

**Questions:** Which changes belong together? Which lower-level contracts feed
which runtime, browser, protocol, docs, and package consumers? Which files are
generated? Which changes are independent? Which experiments should remain
evidence rather than product code?

**Work:** Pilot the graph on one dependency-linked vertical slice, evaluate it
against the complexity circuit breaker, then trace each in-scope dirty file to
its design and tests. Build a dependency graph across grammar/AST/compiler,
Python bindings, runtime ownership and rendering, dependencies and browser
runtime, Events, caching, introspection/debug/CLI, protocols, docs, and release
infrastructure only after the pilot remains bounded or the maintainer approves
a revised approach.

**Output:** proposed review batches with prerequisites, risk, user value, and
estimated review burden. The likely pattern is lower-level contracts before
their consumers, but the graph must prove the exact order.

**Gate:** the pilot has a reviewed expansion estimate, the circuit breaker has
not triggered without maintainer resolution, and no batch asks the maintainer
to approve behavior whose prerequisite is still unreviewed.

### Stage 3: close the design and package inventories

**Questions:** What did each design commit to? What landed? What changed during
implementation? What follow-ups remain? Which GitHub issues are accurate,
stale, duplicated, or missing? Which products and internal contracts actually
exist?

**Work:** Pilot the closure register on a small representative set, evaluate it
against the complexity circuit breaker, then recursively inventory every
artifact under `docs/design/`, including this plan and nested alternative
designs. Classify each artifact as a governing design, alternative draft,
research evidence, harness/fixture, or historical support. Apply the individual
status and follow-up audit to every actual design; do not assign one status to a
mixed directory. Walk implementation and tests for completion claims. Build the
multidimensional package matrix for every Python distribution, Rust crate,
private TypeScript package, protocol contract, docs application, root tooling
workspace, and planned ecosystem package only while the work remains bounded or
after the maintainer approves a revised approach.

**Maintainer checkpoint (2026-07-24):** explicitly revisit the current
`docs/design/migration_djc.md` and verify whether every commitment is done.
The companion `docs/design/migration_djc_tests.md` is maintainer-reported as
done, but still receives the normal evidence check. The maintainer plans to
rename them to `migration_djc.md` and `migration_djc_tests.md`; when that occurs,
treat the old and new paths as the same two design records, reconcile inbound
references, and do not misclassify the rename as a removed design plus an
unrelated new design.

**Output:** design closure register, follow-up candidate list, issue
reconciliation report, and package/contract matrix.

**Gate:** the pilot has a reviewed expansion estimate, the circuit breaker has
not triggered without maintainer resolution, every completed design/package
record has an individual evidence-based status, and the approved scope accounts
for every remaining unknown or follow-up.

### Stage 4: audit implementation, metadata, tests, CI, and security

**Questions:** Are contracts synchronized across Rust, PyO3, stubs, Python,
TypeScript, generated assets, and protocol fixtures? Are manifests correct?
What is not covered by the current gate? Does CI test the same artifact users
install? Are failure, concurrency, malformed input, and security paths covered?

**Work:**

- review source in dependency order, including the full cross-binding audit for
  parser/compiler contract changes;
- create a script/tooling register covering `scripts/`, package entry points and
  package-manager commands, protocol validators, docs CLI/build utilities, and
  every command invoked by workflows; record callers, inputs/outputs,
  portability, idempotence and safety, tests, docs, and stale duplication;
- create a metadata/configuration register covering every `pyproject.toml`,
  `Cargo.toml`, `package.json`, workspace, lock, toolchain, package-data,
  classifier, dependency, license, URL, version, submodule, ignore, release,
  community, and `.github` configuration file, including `CODEOWNERS`, issue/PR
  templates, and Dependabot; parse them where possible and test cross-file
  invariants;
- bound both registers to first-party source-controlled files, dirty untracked
  files, and explicit release/integration metadata; classify vendored,
  generated, ignored, virtual-environment, dependency-install, and cache trees
  once, then inspect them only when they feed a shipped artifact or command;
- attempt the repository gate and focused suites, recording failures and
  environmental limits; identify and specify missing matrix, browser,
  packaging, protocol, fuzz/property, concurrency, and failure-injection tests
  without adding durable checks unless separately approved;
- audit GitHub Actions for triggers, permissions, action pinning, caches,
  required checks, release environments, artifact attestations, and failure
  handling;
- threat-model expression evaluation, Events calls and state, CSRF and signing,
  HTML/attribute output, asset routes, cache replay, file handling, and
  dependency loading;
- attempt clean builds of every distribution in isolated locations, inspect
  successful artifacts and metadata, attempt clean installation and public
  entry points, and record rather than repair every failure.

**Output:** script/tooling register, metadata/configuration register, and
technical readiness dossier with reproducible findings.

**Gate:** every attempted check has an observed result, every unattempted check
has a reason, and each blocker, unknown, and missing durable test is supported
and routed to the execution plan.

### Stage 5: design representative live-project validation

**Questions:** Can a user start, build, debug, test, deploy, upgrade, and operate
a real Citry application? Do the new browser ownership, Events, fragment,
caching, hot-reload, dependency, and error behaviors survive a realistic host
application rather than isolated tests?

**Work:** Design a maintainer-run acceptance matrix for the real project plus
first-party reference applications under `demo/`. The candidate layout includes
`demo/django/` and `demo/fastapi/`; Stage 1's provisional host set supplies
candidates for Stage 5 evidence, while Stage 10 determines the final set.
Each demo should be a small runnable application with its own setup/run/test
instructions while sharing a documented acceptance-scenario contract from
`demo/README.md`. Cover the candidate host frameworks, document and fragment
rendering, forms and Events, Alpine/client behavior, slots, assets, cache
backends, reload, CLI, production settings, multiple workers where promised,
upgrade from the current PyPI release, clean install, and rollback. With
explicit maintainer approval, collect sanitized baseline observations from safe
scenarios; do not require proprietary data or change the live project as a
condition of completing research.

Each scenario records setup, expected observable result, diagnostics to retain,
automated coverage, manual checks, and maintainer sign-off.

**Output:** live-project acceptance matrix, proposed `demo/` structure and host
app manifests, available baseline evidence, and the later implementation and
sign-off work required for each scenario.

**Gate:** every charter workflow has a proposed scenario, evidence-collection
rule, and expected result; unrun scenarios and live sign-off are explicitly
routed to the execution plan.

### Stage 6: audit the GitHub repository, organization, and Project

**Questions:** Do repository and organization settings protect releases while
remaining welcoming to contributors? Is work planning visible and useful? Are
owner access, recovery, security response, and Pages deployment sustainable?

**Work:** Make a read-only inventory of default-branch and ruleset protection,
merge policy, Actions permissions and environments, Pages/domain configuration,
security features, Dependabot and advisories, topics, homepage, social preview,
enabled features, labels, milestones, templates, releases, and community health.
Audit organization profile, roles, base permissions, 2FA policy, backup/recovery
ownership, public identity, and domain/registry ownership. Inspect any GitHub
Project's visibility, access, fields, views, workflows, links, and maintenance
cost. Mark owner-only facts unknown until the maintainer grants suitable
read-only access; never export sensitive settings into the design directory.

**Output:** repository/organization/Project configuration inventory, public and
owner-only evidence ledger, unknowns, risk-ranked recommendations, and candidate
Project model if planning needs one.

**Gate:** every listed surface is observed or explicitly access-blocked, and
each finding is routed without changing external settings.

### Stage 7: audit documentation and public release surfaces

**Questions:** Does the README sell the current product honestly? Can a new user
reach a first success? Is the docs site complete and deployed? Do API pages,
examples, search, version navigation, links, images, social cards, metadata,
accessibility, and performance hold up? Do PyPI pages and GitHub releases render
the intended content and point to real destinations?

**Work:**

- map user documentation to tutorials, task guides, reference, and explanation;
- verify each public claim against implementation and each example by execution
  where practical;
- audit current pages against the accepted feature charter, not only a previous
  upstream site's content;
- build and inspect the site, run internal/external link, HTML, accessibility,
  Lighthouse, search, SEO, social-card, versioning, and custom-domain checks;
- inspect README rendering on GitHub and in each built/PyPI package, including
  relative links and images;
- inspect PyPI metadata, classifiers, project URLs, wheel/platform coverage,
  release descriptions, screenshots, file contents, and attestations;
- reconcile internal docs, agent docs, changelog, release notes, and issue
  status with the product that will ship.

**Output:** content inventory and public-surface audit with owner and acceptance
test for every gap.

**Gate:** every in-scope surface is observed or marked untested, and every
broken, stale, private, or unknown path is recorded with an acceptance test for
the later execution plan.

### Stage 8: run benchmarking as a separate investigation

**Questions:** Which performance jobs matter to users? What are the fair
baselines? How do cold start, parse/compile, first render, repeat render,
serialization, browser startup, Events round trips, DOM updates, payload size,
memory, cache behavior, concurrency, and scaling behave? Which claims reproduce
across machines and versions?

**Work:** Create a dedicated benchmark charter before changing benchmark code.
Audit scenario representativeness, pinned dependencies, optimized builds,
process isolation, warmup, sample size, variance, output equivalence, machine
metadata, and regression thresholds. Separate diagnostic microbenchmarks from
publishable product comparisons and user-perceived browser measurements.

**Output:** benchmark charter, current-evidence audit, and separately scoped
execution backlog. A reproducible benchmark report follows only after that
charter is approved. Existing [`benchmarking.md`](benchmarking.md) and
[`performance.md`](performance.md) are inputs, not automatic approval of future
claims.

**Gate:** an independent reviewer accepts the proposed method and publication
rules; missing measurements and unapproved claims are routed to the dedicated
benchmark backlog.

### Stage 9: research the market, community, and launch

**Questions:** Who has the strongest need for Citry? What category do they place
it in? What does Citry do distinctly well today? What proof, demos, migrations,
and comparisons help them evaluate it? Where do those users already gather?
What support load can the maintainer sustain?

**Work:** Analyze comparable products and draft a small-beta-cohort research
protocol with candidate audiences, recruitment criteria, consent, privacy,
retention, and success measures. No person is contacted and no post, account,
form, channel, analytics property, or mailing list is created without separate
maintainer approval. Test positioning against repository and already-public
evidence; define a flagship demo and smaller copyable examples; draft launch
notes, release notes, migration content, feedback routing, issue triage,
response expectations, measurable launch/feedback outcomes, and a targeted
outreach calendar. Prefer useful technical content and direct feedback requests
to broad untargeted promotion.

**Output:** draft positioning with an evidence-needs register, launch assets
list, approved-research protocol, channel plan, feedback funnel, and post-launch
support plan.

**Gate:** each proposed public promise, research contact, launch channel, and
support route has an evidence need, approval point, owner/capacity assumption,
privacy rule, and measurable outcome. External execution remains deferred.

### Stage 10: synthesize the actual v1 beta plan

**Work:** Return first to the open Stage 1 decision register and resolve it
against the completed evidence. Then combine all findings into one
dependency-aware backlog. Classify work as beta blocker, beta quality target,
documented beta limitation, or later roadmap. Attach evidence, owner, review
batch, acceptance checks, live scenario, and rollback to each blocker. Propose
commit boundaries only after the maintainer has reviewed their contents.

**Output:** the actual v1 beta execution plan and release runbook.

**Gate:** the maintainer resolves the product/version decision register and
reviews the resulting execution plan, followed by an independent adversarial
review. Only then does implementation/review execution begin.

## 6. Human review and live sign-off workflow

The research will design review batches around dependency and risk rather than
raw file count. Every proposed batch will contain:

1. the user-visible outcome and why it belongs in the beta;
2. linked design decisions and unresolved questions;
3. complete file list, including generated outputs and deletions;
4. prerequisite and downstream batches;
5. public API, migration, security, and compatibility risks;
6. concise diff walkthrough and points requiring maintainer judgment;
7. automated evidence with commands, environment, and results;
8. a live-project script with expected observable outcomes;
9. documentation, changelog, issue, and release implications;
10. explicit maintainer states: needs changes, source reviewed, live verified,
    accepted for commit.

No batch is called accepted until the maintainer has reviewed it and completed
its launch-critical live checks. No commit, version update, tag, registry
upload, external issue or post, user contact, deployment, account/form/channel
creation, analytics setup, or external-service setting change follows
automatically from research approval.

## 7. External research corpus

The deeper investigation will use current primary sources and date every
observation. Comparable projects are selected by architecture and user job, not
as popularity votes.

### 7.1 Direct architecture and product comparisons

- [Laravel Livewire](https://livewire.laravel.com/docs):
  server-owned components, events, forms, DOM updates, testing, deployment,
  documentation, and product messaging. Use the current stable release; retain
  version 3 material only where it explains a still-relevant Citry comparison.
- [Phoenix LiveView](https://hexdocs.pm/phoenix_live_view/): stateful server UI,
  lifecycle, recovery, deployment, JavaScript interoperability, testing, and
  security boundaries.
- [Hotwire](https://hotwired.dev/) and [htmx](https://htmx.org/):
  HTML-over-the-wire adoption, progressive enhancement, deployment, and the
  boundary between server and browser behavior.
- [django-components](https://django-components.github.io/django-components/):
  component authoring, typing, slots, dependencies, extensions, packaging,
  documentation, and the upstream relationship.
- [Django Unicorn](https://www.django-unicorn.com/), Tetra, and
  django-livecomponents: Python/Django server-interactive APIs, deployment
  assumptions, community friction, and migration opportunities.
- Vue, Svelte, and Alpine official documentation: component composition,
  reactivity, ownership, developer tools, accessibility, and ecosystem
  expectations that Python web developers may bring to Citry.

### 7.2 Adjacent Python UI products

Study [NiceGUI](https://nicegui.io/documentation/), Reflex, Solara, Flet,
Streamlit, and comparable maintained projects for onboarding time, deployment,
component breadth, escape hatches, typing, testing, docs, demos, packaging,
community, and the difference between professional web-app and dashboard or
desktop-oriented promises.

The comparison will not ask which framework is "best." It will identify user
jobs, trust signals, adoption barriers, and mechanisms that transfer to Citry's
HTML-first, host-framework-compatible model.

### 7.3 Release, documentation, security, and community standards

- The [Python Packaging User Guide on `pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/),
  binary-extension packaging, PyPI-friendly READMEs, Trusted Publishing, and
  TestPyPI for metadata, wheels, license fields, links, pre-releases, and release
  rehearsal.
- [PEP 440](https://peps.python.org/pep-0440/) for the v1 beta version and
  dependency semantics.
- [GitHub's healthy-contribution guidance](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions),
  Projects guidance, Discussions guidance, rulesets, environments, security,
  releases, organization settings, and community profiles.
- [OpenSSF Scorecard](https://github.com/ossf/scorecard) and the
  [OpenSSF Best Practices Badge](https://www.bestpractices.dev/en) as audit
  inputs for branch protection, token permissions, dependency updates, security
  policy, code review, packaging, static analysis, and vulnerability handling.
- [Diataxis](https://diataxis.fr/) for separating learning tutorials, task
  guides, technical reference, and explanation without forcing those labels
  into the site's navigation.
- W3C Web Accessibility Initiative guidance, WCAG, MDN compatibility/testing
  guidance, and browser accessibility tools for docs, demos, and client-active
  UI.
- [Open Source Guides on finding users](https://opensource.guide/finding-users/),
  [building community](https://opensource.guide/building-community/), and
  governance for positioning, targeted outreach, contributor experience, and
  sustainable maintenance.

### 7.4 Evidence protocol for comparisons

For each project, record version, observation date, official docs, release and
package state, architecture, supported workflows, deployment model, test and
security guidance, community routes, and Citry relevance. User complaints are
versioned evidence, not votes: record the exact report, affected version,
maintainer response, reproduction or current contract, recurrence, and whether
the concern is current, fixed, intentional, or unverified.

Stop expanding a comparison stratum when two consecutive candidates add no new
launch requirement, architecture, user job, or recurring failure mode.

## 8. Expected findings and falsification

The plan starts with hypotheses, not conclusions:

- The dirty tree probably decomposes into a small number of dependency-linked
  feature programs. The complete change graph can falsify this if files have
  inseparable cross-cutting edits.
- Lower-level contracts probably need review before runtime and documentation
  consumers. A proven independent vertical slice may justify a different order.
- Several designs probably contain implemented work plus later follow-ups.
  Walking code, tests, and issues may show some are partial or historical.
- Documentation, public package pages, and repository settings probably contain
  real launch blockers even when code is correct. The public audit may show that
  some are already fixed by the working tree.
- Not every open issue or planned ecosystem package belongs in the beta. The
  product charter and user evidence may elevate or defer each one.
- Existing benchmark results may remain directionally useful, but new browser
  and Events capabilities may require different scenarios and claims.

Any conclusion that survives only by ignoring a conflicting code path,
artifact, supported environment, public page, or realistic user workflow is not
ready for the execution plan.

## 9. Research-phase completion criteria

The investigation is complete when:

- every dirty path is classified and routed;
- every recursively discovered design artifact is classified by role, and each
  actual design has an individual evidence-based current status;
- every design follow-up has a blocker/defer/close decision and issue status;
- every current and planned package, crate, protocol, application, and tooling
  workspace has lifecycle, implementation, acceptance, beta role, delivery, and
  release-readiness states plus an owner, versioning policy, dependency graph,
  and registry state;
- every in-scope executable entry point and repository metadata/configuration
  file is in its register, with excluded tree classes, consistency findings,
  and unknowns recorded;
- code, tests, CI, security, docs, public registries, approved GitHub settings,
  and live-project scenarios have observed findings or explicit evidence gaps;
- benchmarking has a separately reviewed proposed methodology and backlog;
- positioning and outreach research has candidate users, evidence needs,
  consent/privacy rules, channels, feedback measures, approval points, and
  support-capacity assumptions;
- the actual execution backlog explains ordering and blocker rationale; and
- the maintainer and an independent reviewer have reviewed the result.

Research completion does not mean the beta is ready to publish. It means the
maintainer has a trustworthy map for getting there. Failures and unrun release
checks are valid research results when their scope and remediation work are
recorded; green launch evidence belongs to execution and final release gates.

## 10. Decisions reserved for maintainer review

The research will bring evidence and recommendations for these decisions
without assuming the answer now:

- the exact meaning and version spelling of "v1 beta";
- the beta's required user workflows and acceptable documented limitations;
- whether package versions remain independent and which packages launch
  together;
- the supported Python, browser, operating-system, host-framework, and
  deployment matrix;
- the representative live project and beta cohort;
- the boundary between GitHub Issues, Discussions, Discord, and private
  security reporting;
- the GitHub Project structure and repository/organization hardening choices;
- the benchmark claims suitable for public use;
- the launch message, flagship demo, outreach channels, and support promise;
- the final review batches, commit boundaries, release date, and go/no-go call.
