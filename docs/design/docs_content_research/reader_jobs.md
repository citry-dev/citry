# Citry reader jobs and journey map

**Status (2026-07-26): Stage 2 synthesis complete; closing evidence and limits
recorded.**

## Outcome

Stage 2 records 55 source observations and 23 reader jobs. Seventeen jobs fall
in the primary priority band, four are important, and two are supporting. This
is a content-research rank, not a promise that every current capability will
ship in the first beta or receive one standalone page.

The repository provides substantial evidence for component authoring, host
adapters, Events, caching, reload, diagnostics, tests, examples, and Citry-side
migration patterns. It does not provide direct-reader research, a sanitized
support corpus, search analytics, representative host applications, production
deployment, rollback, or upgrade rehearsals. Consequently:

- the jobs themselves can be prioritized from implementation, risk, and
  provisional product evidence;
- their frequency scores are ordinal hypotheses, not measured prevalence;
- all ordinary-reader segment assignments remain provisional;
- contributor and maintainer work remains a secondary audience;
- support, host-version, deployment, upgrade, and migration success claims
  need stronger evidence before evergreen prose presents them as complete.

The durable rows are in `reader_evidence.tsv` and `reader_jobs.tsv`. Their
schemas, scoring rubric, failure behavior, and source-hash rules are documented
in the research [`README.md`](README.md).

## What the evidence says

| Evidence class | Count | Interpretation |
| --- | ---: | --- |
| Verified implementation | 27 | Current source and focused passing tests establish mechanics and failure paths. |
| Artifact verified | 4 | Built or research artifacts were observed and their limits recorded. |
| Publicly observed | 9 | Current GitHub and public-service facts plus bounded predecessor signals are time-bound. |
| Document claimed | 10 | Current docs and provisional or accepted designs identify jobs and priority without proving reader success. |
| Inference or unavailable | 5 | The missing datasets are recorded as absences and support no job. |

The focused Stage 2 application pass produced 376 passing tests and two
optional-watcher skips. Eight selected application-shaped Chromium tests also
passed. The installed integrations were FastAPI 0.138.2, Starlette 1.3.1, and
Django 6.0.6; Flask was not installed. A separate isolated macOS arm64 check
built and installed the current Citry 0.2.0 wheel on Python 3.13 with released
citry-core 1.3.0, imported it, exercised CLI help, and found its packaged
client runtime. These results support current mechanics and one artifact, not
the future beta or a host and platform support matrix.

Public evidence changes the interpretation more than the implementation rank:

- the 21 current non-PR Citry Issues and all four comments are authored by the
  project maintainer, so they show maintainer intent rather than independent
  reader frequency;
- Discussions are disabled, while the Issue chooser still routes questions
  and ideas there;
- `citry.dev` and its intended Help URL returned GitHub Pages 404 at the stated
  observation time;
- Pagefind is local to the browser and no privacy-approved search-query or
  abandonment data was available;
- selected predecessor Issues support fragment, migration, low-boilerplate,
  machine-readable-docs, and asset jobs qualitatively, but do not measure
  current Citry demand.

## Priority method

Each job receives 1 through 5 for frequency, impact, risk, and product
priority. The sum determines its band: 16 through 20 is primary, 12 through 15
is important, 8 through 11 is supporting, and 4 through 7 is provisional.
Ties defer to product priority and then risk.

Frequency estimates how central and repeated the task is in current repository
and product evidence. It does not claim analytics. Impact asks what completing
the job unlocks. Risk asks about security, compatibility, operational harm, and
recovery cost. Product priority comes from current accepted or explicitly
provisional direction. Confidence and evidence strength stay separate from the
score so a high-risk evidence gap remains visible instead of being ranked away.

## Primary journey gate

Every proposed primary journey below names the Stage 2 gate fields. The
complete records add failure concerns, all evidence IDs, rank inputs, persona
status, and qualifications.

| Job | Reader context | Prerequisite | Successful outcome | Evidence | Priority |
| --- | --- | --- | --- | --- | ---: |
| `JOB-001` Evaluate fit | Python web engineer with known host, browser, and deployment constraints | Python and HTML familiarity | Makes an adoption or rejection decision and names every unverified dependency | Moderate | 19 |
| `JOB-023` Clean install | New user with a clean environment | Supported Python and operating system plus promised package artifacts | Citry imports, CLI help runs, and packaged client assets exist | Moderate | 18 |
| `JOB-002` First component | Python and HTML user new to Citry | Installed compatible Citry environment | Renders expected HTML and recognizes a required-input failure | Strong | 18 |
| `JOB-003` Compose components | Author who understands first render | Working component and basic syntax | Typed composition and assets render, with useful missing-input, fill, and asset failures | Strong | 18 |
| `JOB-005` FastAPI or Starlette integration | Existing host application owner | Startup and mount control | Stable document, runtime, asset, fragment, and Events routes | Moderate | 19 |
| `JOB-006` Django integration | Django owner with middleware, URL, cache, and CSRF expectations | Startup and root URL control | Citry works while Django request and security behavior remains intact | Moderate | 19 |
| `JOB-007` Flask or WSGI integration | Synchronous host owner | Root WSGI callable that can be wrapped | Citry and host routes coexist, and async work receives the ASGI recovery direction | Moderate | 18 |
| `JOB-008` ASGI integration | ASGI 3 application owner | Host routing and lifespan control | Requests, bodies, disconnects, and failure statuses behave predictably | Moderate | 17 |
| `JOB-009` Progressive fragments and forms | Builder with a mounted host and target region | Browser runtime and working assets | Intended region updates with correct focus, assets, and fallback behavior | Strong | 18 |
| `JOB-010` Secure Events | Builder with an application security model | Mounted host and Events extension | Typed valid interactions succeed and invalid input, origin, token, or authorization fails at the right layer | Strong | 19 |
| `JOB-011` Diagnose a failure | Reader with a reproducible server or browser symptom | Server output and browser tools where relevant | Fixes the cause or produces a minimal actionable report | Moderate | 18 |
| `JOB-012` Test behavior | Team with working components or interactions | Matching render, host, or browser test environment | A proportional check detects the promised regression | Strong | 17 |
| `JOB-014` Cache output safely | Builder who knows every output-dependent dimension | Backend plus variation, expiry, and invalidation policy | Equivalent renders hit while distinct or corrupt cases separate or recover | Moderate | 16 |
| `JOB-015` Operate multiple workers | Operator using shared assets, cached output, or server-held State | Shared backend, deployment generation, health checks, and rollback plan | Workers remain compatible and rollback restores the prior generation | Moderate | 18 |
| `JOB-016` Upgrade safely | Current user with known source and target versions | Accurate release notes, compatibility boundaries, and restorable deployment | Target checks pass or the prior state is restored | Moderate | 17 |
| `JOB-017` Migrate another component model | Developer with reproducible source behavior | Mapped Citry target and coexistence or rollback plan | Citry matches the behavior checklist before the source path is retired | Moderate | 16 |
| `JOB-020` Get help or report safely | User with a question, defect, or vulnerability | Reachable route and appropriate reproduction evidence | Report reaches an enabled channel and sensitive details remain private | Moderate | 18 |

The primary band contains several low-frequency hypotheses because failure has
high adoption, security, migration, or operational cost. It does not mean all
17 should appear at the same level of navigation. Stage 4 will decide routing
after the pilot and later fact work.

## Journey map

| Phase | Reader transition | Ranked jobs | Evidence and routing implication |
| --- | --- | --- | --- |
| Evaluate | Unknown product to informed fit decision | `JOB-001` | Current promise, limits, support state, versions, and public availability must be explicit before a quickstart. |
| First success | Fit decision to an installed artifact and visible standalone output | `JOB-023`, `JOB-002` | Verify the package boundary first, then keep the smallest typed render path independent of a web host and expose a useful failure and next choice. |
| Build the model | First component to composition and focused tasks | `JOB-003`, `JOB-004`, `JOB-009`, `JOB-010`, `JOB-013`, `JOB-014` | Docs owns concepts, Examples owns concise tested recipes, and Reference owns exact contracts. Security and cache prerequisites cannot be deferred. |
| Integrate | Standalone behavior to an existing host | `JOB-005` through `JOB-008` | Use one shared host journey with verified host-specific branches, while keeping unproved version and deployment claims visible. |
| Diagnose and verify | Working path to recoverable confidence | `JOB-011`, `JOB-012`, `JOB-020` | Troubleshooting, tests, search, and support form one recovery path. A dead or contradictory support route breaks the journey. |
| Deploy and operate | One process to a supported production topology | `JOB-015` | Shared-state and generation rules are primary because of risk, but successful production guidance is blocked on a representative rehearsal. |
| Upgrade or migrate | Current behavior to a changed version or model | `JOB-016`, `JOB-017` | State the source behavior, difference, verification, coexistence, and rollback. Executable Citry snippets alone do not prove migration success. |
| Look up and extend | Completed task to exact contract or reuse | `JOB-018`, `JOB-019` | Reference and machine-readable projections need later fact coverage. Reusable ecosystem authoring remains important but weakly user-validated. |
| Contribute | Product use to project maintenance | `JOB-021` | Keep repeatable maintainer workflows under Community and internal docs, away from ordinary onboarding. |
| Future UI catalog | Core Citry to ready-made UI | `JOB-022` | Preserve a future UI Kit and Examples projection without documenting unfinished Citry UI as current behavior. |

`JOB-004`, `JOB-013`, `JOB-018`, and `JOB-019` are important rather than
primary. `JOB-021` and `JOB-022` are supporting. No job lands in the
provisional score band, but 22 persona assignments remain provisional because
the segment evidence is unavailable.

## Persona findings

The repository supports situations and jobs more strongly than demographic
segments. Keep these as working contexts, not biographies:

- professional teams are a plausible context for integration, testing,
  operations, upgrade, and migration because those jobs require shared
  compatibility and recovery decisions;
- independent developers are a plausible context for first use, focused
  recipes, progressive behavior, debugging, and support;
- learners are plausible first-success readers, but there is no observed
  learner session or abandonment evidence;
- component and tooling authors are a plausible secondary growth context, but
  direct demand and the stable extension contract are incomplete;
- contributors and maintainers are a real repository audience, but their jobs
  remain secondary to user onboarding and ordinary application work.

No evidence supports invented age, employer size, industry, geography, or
similar biography. Future research should continue to recruit by situation and
job rather than by fictional profile.

## Evidence gaps that constrain later authoring

1. **Public availability:** the docs and Help URLs were 404. Re-observe after
   deployment before running public findability or task checks.
2. **Support path:** the Issue chooser points questions to disabled
   Discussions. Resolve and verify the route before describing it as usable.
3. **Host support:** build representative applications and an explicit version
   matrix. FastAPI and Django mechanics are strongest; Starlette, Flask, and
   branded ASGI or WSGI support need direct scenarios.
4. **Production operation:** run shared-cache, multi-worker, rolling-deploy,
   health, and rollback scenarios before writing definitive production steps.
5. **Upgrade and migration:** rehearse an isolated Citry upgrade and at least
   one real source-framework application migration, including rollback.
6. **Reader frequency and findability:** collect privacy-approved aggregate
   queries, zero-result terms, support classifications, and task outcomes after
   the site is live. Until then, treat frequency as a hypothesis.
7. **Reference and examples:** Stage 3 and later fact work must test whether a
   reader can move from tutorial to recipe to exact contract without duplicated
   or browser-only source.

These gaps block only the affected claims and completion assertions. They do
not erase the verified implementation evidence or prevent a bounded Stage 3
pilot.

## Later falsifying checks

- Ask representative readers to evaluate fit and reach first standalone
  success without navigation hints.
- Classify new public support requests by situation and job without retaining
  unnecessary identity data.
- After privacy approval, review aggregate search terms, zero-result queries,
  and result selections against this ranking.
- Exercise each proposed supported host at declared oldest and newest versions
  in a small application.
- Rehearse one multi-worker deploy and rollback with shared cache and server
  State.
- Rehearse one released-version upgrade and one source-framework migration.
- Compare observed detours and failures with `reader_jobs.tsv`; revise the
  personas, frequency scores, and journey order rather than defending the
  initial hypothesis.
