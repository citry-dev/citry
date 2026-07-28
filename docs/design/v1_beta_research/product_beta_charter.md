# Citry product and beta charter

**Status (2026-07-23): independently reviewed provisional research charter.
Its decisions remain open until Stage 10.**

This charter defines what "Citry v1 beta" should mean before the repository is
triaged against it. It is a product and support contract, not a readiness
claim, feature-completion report, release authorization, or substitute for the
later design, package, implementation, live-project, documentation, benchmark,
and public-surface audits.

The local observations below are anchored to Stage 1 baseline
`B1-20260723T141813Z-cd177d74`. A later stage must re-check any source that
changes after that baseline before relying on it for a launch decision.

## Proposed decisions at a glance

| Topic | Provisional working decision | Why this is the default | Stage 10 status |
| --- | --- | --- | --- |
| Release identity | Publish the launch-facing `citry` distribution as `1.0.0b1` and describe the initiative as "Citry v1 beta" | The package version and public name say the same thing, while Python installers still treat it as an opt-in pre-release | Pending |
| Meaning of beta | A coherent, documented product for deliberate, rollback-capable production pilots, with known limitations and direct feedback; it is not yet a general production recommendation or the final v1 compatibility guarantee | This sets a higher bar than a preview while preserving room to correct APIs before `1.0.0` | Pending |
| Package scope | Launch `citry`; include a tested, bounded `citry-core` dependency; treat `pygments-citry` as an optional companion; keep `citry-ui` outside the v1 beta | This distinguishes the product from independently versioned implementation and ecosystem packages | Pending |
| Primary audience | Python teams and individuals building server-rendered websites and web applications who want reusable UI and selective interactivity without adopting a client-heavy application architecture | This matches the implemented Python-first direction and gives feature triage a concrete user | Pending |
| Python support | CPython 3.10 through 3.14 for the first beta; review 3.10 when upstream support ends; do not promise PyPy until it has a release-gating matrix | This matches current metadata and the main CI matrix without treating a classifier as test proof | Pending |
| Operating systems | Support Linux, Windows, and macOS on the published wheel targets; require full Linux and Windows CI plus macOS release smoke and artifact checks | This makes "supported" testable while allowing a cost-conscious macOS matrix | Pending |
| Browsers | Publish an exact per-beta matrix for the latest stable desktop Chrome, Edge, Firefox, and Safari available at release time; require branded smoke checks, backed by the locked Playwright Chromium/Firefox/WebKit regression suite | This gives users an actionable rolling policy without pretending engine snapshots alone prove branded compatibility | Pending |
| Web hosts | Make FastAPI/Starlette, Flask, Django, bare ASGI, and bare WSGI beta targets, but call a target supported only after its exact version floor and demo/live scenario pass | The adapters are public today, while their version floors are not consistently declared or tested | Pending |
| API stability | Permit breaking changes between beta releases only when justified, documented, and accompanied by migration guidance; freeze the accepted public surface at the first release candidate | This makes beta feedback useful without making upgrades arbitrary | Pending |
| Security support | Give the latest beta bug and security fixes; give the current 0.2 final line critical-security-only support through 30 days after `1.0.0`; keep private reporting and the current "within a few days" acknowledgement aim | This gives non-pre-release users a bounded bridge without promising multiple fully maintained lines | Pending |
| Feedback model | Initially use GitHub Issues, with distinct templates/labels for defects and questions/proposals; use Discord only for chat; consider Discussions later only after it is enabled and audited | This is operable with current public settings and keeps decisions durable | Pending |

## Product thesis

Citry should be the Python-first, HTML-first component framework for building
server-rendered UI that can grow from reusable markup into rich, progressively
interactive applications without forcing a separate client application or a
JavaScript build system.

The short promise is:

> Write reusable UI as Python components with familiar HTML templates. Compose,
> validate, render, style, and progressively activate those components across
> common Python web stacks, while Citry manages the browser and server plumbing.

This keeps the ambition in the user's launch brief while making the initial
v1 beta falsifiable. "Ultimate go-to solution" is a direction to earn through
reliability, ergonomics, documentation, interoperability, and community trust,
not a launch claim.

### Primary audiences and jobs

1. **Professional Python teams.** Build and maintain shared application UI with
   reviewable Python APIs, typed inputs, predictable rendering, test support,
   production deployment guidance, and a stable upgrade path.
2. **Independent professionals and small teams.** Add component structure and
   selective interactivity to an existing Django, FastAPI, Starlette, Flask,
   ASGI, or WSGI application without creating a second application stack.
3. **Hobbyists and learners.** Start with plain Python and HTML, get useful
   errors and examples, and add framework mounting or browser behavior only
   when the project needs it.
4. **Component and tooling authors.** Build reusable Citry components,
   extensions, syntax tooling, and optional packages against documented public
   extension points.

The first three audiences are launch-critical. Ecosystem authors matter to the
v1 story, but ecosystem scale is not a prerequisite for the first beta.

### Core user jobs

- define a component in ordinary Python and render it without a web framework;
- compose components, pass validated inputs, fill slots, and share subtree
  context;
- attach scoped JavaScript, CSS, dependencies, and per-render browser data;
- mount the same component system into an accepted Python web host;
- add fragments, browser behavior, forms, and typed server events without
  losing host-framework security controls;
- diagnose template, render, browser, event, and deployment failures;
- test components and representative browser interactions;
- install, upgrade, deploy with multiple workers where promised, and roll back;
  and
- discover trustworthy documentation, examples, limitations, support routes,
  and release notes.

## The v1 beta promise

The proposed beta is meaningful only if a user can complete the launch-critical
workflows below from the released artifacts and published documentation. A
feature's presence in source, a design document, or the changelog is not enough.

### Candidate public capability set

The v1 beta candidate includes:

- Python component authoring, registration, initialization, composition, and
  rendering;
- Citry's template syntax, expressions, dynamic attributes, control flow,
  slots/fills, dynamic components/elements, and provide/inject behavior;
- declared input validation and documented component lifecycle behavior;
- component HTML, JavaScript, CSS, dependency, and asset delivery;
- document and fragment rendering, browser ownership, the pinned Alpine
  runtime, and supported extension hooks;
- typed server Events, forms, actions, state, transport, host integration, and
  documented security requirements;
- accepted cache behavior, including shared-cache requirements and deployment
  limits;
- debugging, introspection, hot reload, and the public command-line workflows;
- framework adapters accepted by the compatibility matrix; and
- testing guidance and a small set of runnable reference applications under
  `demo/`.

This list sets the audit boundary. Later stages may show that an item must be
repaired, narrowed, documented as experimental, or deferred. No item becomes a
launch claim until its required evidence and maintainer review are complete.

### Launch-critical workflows

| Workflow | Beta-level outcome | Evidence required before release |
| --- | --- | --- |
| Clean install | A new supported environment installs released artifacts without a repository checkout or local compiler when a promised wheel applies | Built-artifact inspection and isolated install test |
| First component | The installation guide produces rendered HTML and the documented CLI version | Installed-artifact test and docs example test |
| Composition | Inputs, nested components, slots/fills, dynamic attributes, control flow, JS/CSS, and dependencies behave as documented | Focused tests plus a demo scenario |
| Host setup | Each accepted host starts, initializes Citry safely, mounts routes, and serves a document | Versioned host matrix plus a runnable `demo/<host>/` app |
| Progressive behavior | Fragments, Alpine/client behavior, forms, and Events work together in accepted browsers and hosts | Browser tests plus representative demo/live-project validation |
| Failure diagnosis | Invalid templates, inputs, routing, events, cache state, and browser operations produce actionable diagnostics | Failure-path tests plus troubleshooting walk-through |
| Production operation | Documented production settings, assets, shared cache, multiple-worker behavior, deployment, and rollback match observed behavior | Deployment scenario and maintainer sign-off |
| Upgrade | A supported current public release can move to the beta using accurate release notes and migration guidance | Isolated upgrade rehearsal plus live-project sign-off |

### Explicit non-goals for the first beta

- a hosted service, deployment platform, database, authentication system, or
  general application framework;
- a client-only single-page application framework or replacement for every
  JavaScript ecosystem tool;
- final `1.0.0` API stability or long-term-support branches;
- official JavaScript/TypeScript, PHP, Go, or Rust language distributions;
- an official broad UI component library, including `citry-ui`, unless it
  separately clears its own product and quality gate;
- support for every Python web framework merely because bare ASGI or WSGI is
  available;
- support for untested Python implementations, operating systems, CPU targets,
  browser versions, cache backends, or deployment topologies;
- a supported third-party implementation contract for the v1 wire protocols;
  the first beta validates those protocols as first-party embedded contracts;
- performance leadership claims until the separate benchmark work is accepted;
  or
- feature completeness relative to Vue, React, Livewire, Django, Jinja, or any
  other comparison project.

## Release and package identity

### Proposed version convention

The launch-facing package should move from `0.x` to `1.0.0b1`.

- `1.0.0b1` is a PEP 440 beta pre-release. Normal Python dependency resolution
  does not generally select a pre-release unless the user opts in or no final
  release satisfies the requirement.
- Package metadata should add `Development Status :: 4 - Beta`. Installation and
  upgrade instructions must use an exact pin such as
  `pip install citry==1.0.0b1` or an explicit pre-release opt-in such as
  `pip install --pre citry`; the current plain `pip install citry` remains a
  latest-final instruction and would not normally select the beta.
- The Git tag should follow the repository's independent-package convention,
  `citry@1.0.0b1`, and the GitHub release should be marked as a pre-release.
- Before the tag is used, the docs-release tag filter must accept PEP 440 beta
  suffixes and the package workflow must create or update the GitHub release as
  a pre-release. The current final-only tag filter and unqualified
  `gh release create` command do not satisfy this contract.
- This proposal absorbs the reviewed, accepted work currently recorded under
  the changelog's `v0.3.0` and Unreleased sections. It does not publish an
  intervening public `0.3.0` first. If the intended v1 contract remains
  materially open after this review, the fallback is to publish `0.3.0` and
  call it "Citry beta" or "pre-v1 beta," not "v1 beta."
- Documentation, support forms, telemetry-free diagnostics, and release notes
  should display the exact package version, not only "v1 beta."
- Later betas increment `bN`; the first release candidate is `1.0.0rc1`; the
  final release is `1.0.0`. Post and development releases are not the normal
  public beta cadence.

The alternatives are weaker:

- A `0.x` release marketed as "v1 beta" makes dependency specifications,
  screenshots, bug reports, and support conversations ambiguous.
- `1.0.0rc1` implies the feature and compatibility contract is substantially
  frozen, which is premature before maintainer source review and live-project
  validation.
- `1.0.0` would overstate the current evidence and remove the deliberate beta
  correction period.

### Proposed package roles

| Unit | Role in the v1 beta | Version treatment | Release rule |
| --- | --- | --- | --- |
| `citry` | Launch-facing product | `1.0.0b1` | Must clear every beta release gate |
| `citry-core` | Required implementation dependency | Independent version; exact compatible range decided from the package/contract and artifact audit | Publish only if the accepted `citry` beta needs unreleased core changes; always test the released pair |
| `pygments-citry` | Optional ecosystem companion for syntax highlighting | Independent version | May ship alongside the beta after its own artifact/docs checks, but does not block the runtime beta unless the final docs depend on it |
| `citry-ui` | Experimental UI-library work outside the first beta | Keep unpublished, pre-alpha, and independently versioned | Keep it in the development workspace; update its internal Citry constraint to accept the beta, regenerate the workspace, and require its tests to pass; do not publish, market, or bundle it as part of Citry v1 beta |
| `citry-client` and protocol packages | Internal or embedded runtime contracts, subject to Stage 3 classification | Do not present their workspace versions as the product version | Validate and deliver them through the owning released artifact unless Stage 3 proves a public distribution is needed |
| Rust crates, docs app, root tooling | Implementation and project infrastructure | No Citry product-version promise | Audit and version only according to their actual delivery role |

The `citry` requirement on `citry-core` must be bounded by a documented
compatibility policy. The exact lower and upper bounds are deliberately a
Stage 3 and Stage 4 evidence decision because the current `>=1.3.0` lower bound
does not state what future core releases may break. The beta cannot publish
until that range is explicit and the selected pair has passed artifact tests.

Deferring `citry-ui` does not mean leaving the workspace unresolvable. The
chosen disposition is to keep the unpublished spike in the development
workspace, change its internal dependency from `citry<0.3.0` to a bounded range
of `citry>=1.0.0b1,<2.0.0`, regenerate the workspace, and require its runtime
and typing tests to pass against the accepted beta. If it cannot pass without
broad UI work, the charter must be amended before execution; it must not
silently expand the core beta or publish an incompatible `citry-ui` artifact.

## Compatibility and support proposal

"Supported" means that Citry documents the combination, exercises an
appropriate release gate, accepts actionable bug reports for it, and either
fixes beta regressions or publicly narrows the next beta's matrix. A broad
metadata classifier, adapter import, or passing unit test alone is not a
support promise.

### Python and operating systems

- **Python:** support CPython 3.10, 3.11, 3.12, 3.13, and 3.14 for `1.0.0b1`.
  Revisit 3.10 when upstream maintenance ends rather than promising it for all
  of Citry 1.x. Adding a new CPython release requires a passing matrix and
  released wheels before public support.
- **Python implementations:** PyPy and other implementations are best-effort
  until they have a declared build, install, and test matrix. A current PyPy
  classifier on `citry-core` must be verified or removed before release.
- **Linux and Windows:** run the Python suite across every supported version,
  inspect the promised wheel families, and install representative artifacts.
- **macOS:** support Intel and Apple Silicon wheel families if release artifacts
  pass inspection and install smoke tests. The continuous suite may retain an
  oldest/newest Python smoke pair, provided release checks cover the actual
  artifacts and the limitation is documented internally.
- **Other operating systems and source builds:** document them as best-effort.
  Source installation may require Rust; it is not equivalent to a promised
  prebuilt wheel.

The current compatibility page says Citry should run on any operating system
that supports Python. That is an aspiration, not a beta support commitment, and
should be rewritten to distinguish tested, artifact-supported, and best-effort
targets.

### Browser runtime

- This policy concerns testing Citry's shipped JavaScript runtime and publishing
  the tested browser versions in the compatibility documentation and beta
  release notes. It does not create browser-specific Python wheels; Citry's
  Python wheel is the same regardless of which browser visits the application.
- The public beta contract covers the latest stable desktop Chrome, Edge,
  Firefox, and Safari versions available at each beta cutoff. The release notes
  and compatibility page must record the exact major versions actually checked;
  support does not float silently between releases.
- Branded smoke checks on those exact versions are the public support evidence.
  The Chromium, Firefox, and WebKit revisions supplied by the lockfile's exact
  Playwright version remain the repeatable regression contract and must also be
  recorded in release evidence. They are not described as interchangeable with
  every branded browser build.
- Every browser-runtime change must run a compact contract in all three
  engines. The full browser suite must pass in all three before a beta release.
- Internet Explorer, legacy EdgeHTML, unsupported Safari/WebView versions, and
  mobile browsers are outside the first-beta promise. User-supplied replacements
  for Citry's pinned Alpine runtime are also unsupported.

### Web hosts and deployment

The public product surface currently names six candidate beta targets: FastAPI
and Starlette as separate host commitments that share one adapter, plus Flask,
Django, bare ASGI, and bare WSGI. The recommended acceptance structure is:

| Target | Candidate floor | What must prove support |
| --- | --- | --- |
| FastAPI | `>=0.110` | Direct adapter tests, a pinned oldest/newest matrix, and `demo/fastapi/` |
| Starlette | Floor to be derived from the direct API used, not only FastAPI's transitive dependency | Direct adapter tests and either the FastAPI demo or a focused bare Starlette scenario |
| Django | `>=5.2` | Direct adapter tests across accepted Django/Python pairs and `demo/django/` |
| Flask | `>=3.0` as the proposed starting floor | Direct adapter tests across accepted Flask/Python pairs and `demo/flask/`, or explicit deferral from launch support |
| Bare ASGI | ASGI 3 callable contract used by the adapter | Protocol tests plus a runnable deployment scenario |
| Bare WSGI | WSGI 1.0 callable contract used by the adapter | Protocol tests plus a runnable deployment scenario |

The FastAPI and Django candidates have current dependency evidence. The
Starlette, Flask, ASGI, and WSGI floors need Stage 4 verification; `Flask>=3.0`
is a proposed policy floor rather than a current manifest fact. If that work is
not accepted or does not pass, the honest beta promise is to keep the adapter
available but label it experimental, not supported.

For deployment, beta support includes documented single-worker operation and
multiple workers only with the shared-cache and version-coordination rules
required by the chosen feature set. It excludes an unconditional promise for
every server, proxy, cache, container platform, or zero-downtime deployment
strategy. Client-active pages currently require Alpine's standard evaluator and
`unsafe-eval`; the unsupported CSP build is an explicit beta limitation unless
later work changes and verifies that constraint.

## Public API and compatibility policy

### What counts as public

The beta audit should presume the following are public until Stage 3 classifies
them more narrowly:

- documented imports, classes, functions, methods, decorators, exceptions,
  protocols, and type shapes under released packages;
- component subclass hooks and data passed to those hooks;
- template syntax, built-in tags, dynamic attributes, validation rules, and
  rendered behavior;
- documented configuration, extension hooks, cache interfaces, adapter entry
  points, and CLI commands/options/output contracts;
- browser globals and hooks documented for application or extension code;
- URL behavior, Events requests/responses, actions, tokens, protocol schemas,
  and shipped client/server compatibility; and
- package names, extras, entry points, supported version ranges, and documented
  artifact contents.

Private names are not automatically safe to change if generated artifacts,
protocol fixtures, third-party extensions, or public examples depend on them.
The Stage 3 package and contract matrix must identify those cases.

### During beta

- Breaking changes are allowed only when they materially improve correctness,
  safety, maintainability, or the eventual v1 contract.
- Each breaking change must be called out in release notes with affected APIs,
  replacement or migration steps, and the earliest release in which the old
  behavior disappears.
- Use a runtime or documentation deprecation period when practical. A beta may
  remove an unsafe or unusable contract immediately, but the reason and
  migration must still be explicit.
- Wire and browser contracts must carry an explicit compatibility/versioning
  rule whenever separately cached or deployed client and server artifacts can
  overlap.
- Silent breaking changes are release blockers.

### From release candidate to final

`1.0.0rc1` freezes the intended public v1 API and compatibility contract.
After that point, only release blockers, security fixes, documentation fixes,
and changes that restore the accepted contract should land. Any necessary new
breaking change returns the release to another beta unless the maintainer
explicitly accepts a new release-candidate cycle.

The final `1.0.0` policy should promise compatibility within the 1.x line and a
documented deprecation path for intentional breaking changes. Exact support
windows and deprecation lengths remain a pre-RC decision because they must
match sustainable maintainer capacity.

## Beta feedback, support, and security

### Feedback routes

- **Defects:** GitHub Issues using a template that captures `citry`,
  `citry-core`, Python, operating-system, browser, host, and minimal reproduction
  details where relevant.
- **Questions and proposals:** GitHub Issues with a distinct question/proposal
  template and labels. This is the first-beta default because Issues is enabled
  and Discussions is not. Discussions may replace this route only after it is
  enabled, audited, and accepted through a later explicit decision.
- **Chat:** Discord may provide rapid community help, but decisions and known
  defects must be summarized into durable public records.
- **Security:** GitHub private vulnerability reporting only, following
  `SECURITY.md`; never route suspected vulnerabilities through public issues or
  chat.

Every beta should publish release notes, upgrade steps, known limitations, the
supported matrix, and a structured request for feedback. Reports should be
triaged into release blocker, accepted beta defect, documentation gap,
enhancement, or unsupported combination. No response-time promise should be
made beyond what the maintainer can repeatedly sustain.

### Security support

The latest released `citry` beta and its exact supported `citry-core` line
receive bug and security fixes. Because ordinary installers will continue to
select the latest final release, the current 0.2 line receives critical security
backports, but not ordinary bug fixes, through 30 days after `1.0.0` publishes.
If a safe backport is impossible, the advisory must say so and identify the
fixed upgrade. Confirmed vulnerabilities should receive coordinated fixes and
releases. The current aim to acknowledge reports "within a few days" is
reasonable for the first beta; a stricter service-level objective should not be
published without a staffing and availability decision.

## Beta entry and exit criteria

### Entry to `1.0.0b1`

The first beta may publish only when later research and execution work shows:

- every release-facing package and internal contract has an accepted role and
  tested artifact path;
- every dirty path is reviewed, grouped, tested, and either committed or given
  an explicit non-commit disposition;
- launch-critical designs and follow-ups are classified and resolved or
  transparently deferred;
- the repository gate, release CI, artifact checks, accepted browser/host
  matrices, docs build/deploy, and representative demos pass;
- the maintainer has reviewed the source batches and signed off the real-project
  acceptance scenarios;
- README, docs site, package pages, release notes, security/support routes, and
  GitHub release surfaces agree with this charter;
- benchmark claims are separately accepted or removed;
- known limitations and rollback instructions are public; and
- no unresolved security, data-loss, installation, upgrade, or release-pipeline
  blocker remains.

### Exit from beta to release candidate

The first release candidate requires:

- the accepted public API inventory and support matrix are frozen;
- representative users can complete the launch-critical workflows from public
  artifacts and documentation;
- beta feedback shows no unresolved pattern of critical installation,
  correctness, security, operability, or documentation failures;
- upgrade and rollback rehearsals have passed;
- release and support operations have been exercised at least once; and
- remaining limitations are compatible with the final v1 promise.

Download, star, benchmark, or social metrics can inform outreach, but they do
not replace these quality gates.

## Current evidence and contradictions

The proposed charter deliberately narrows or qualifies several current claims:

- The root README calls Citry a fast, simple, and smart frontend framework,
  claims broad framework compatibility, and exposes a substantial component,
  asset, fragment, CLI, and integration surface (`README.md:10-13`,
  `README.md:68-85`, `README.md:492-566`). These are candidate promises, not yet
  installed-artifact or live-project proof.
- The runtime manifest is version `0.2.0`, supports Python `>=3.10,<4.0`, and
  depends on unbounded `citry-core>=1.3.0`
  (`packages/py/citry/pyproject.toml:5-38`). The beta version and core
  compatibility bound therefore require explicit release changes later.
- The changelog already has a `v0.3.0` section plus a much larger Unreleased
  section while the manifest remains 0.2.0 (`CHANGELOG.md:3`,
  `CHANGELOG.md:530`). The proposed `1.0.0b1` absorbs accepted work from both;
  publishing `0.3.0` first is an explicit alternative, not an accidental step.
- The root README currently teaches plain `pip install citry`, the docs-release
  workflow accepts only final `X.Y.Z` tags, and the package workflow creates an
  unqualified GitHub release (`README.md:82-86`,
  `.github/workflows/repo--docs-release.yml:25-32`,
  `.github/workflows/py--citry--publish.yml:124-137`). Exact beta install
  guidance, beta tag handling, and `--prerelease` release state are explicit
  execution blockers, not behavior inferred from the proposed version.
- Current test dependencies name Django `>=5.2` only on Python 3.12 and newer
  and FastAPI `>=0.110`; no Flask or direct Starlette floor appears there
  (`packages/py/citry/pyproject.toml:54-67`). Public host claims are broader than
  the declared floor evidence.
- The compatibility page claims Python 3.10 through 3.14, Linux/Windows testing,
  macOS support, broad wheels, and Chromium/Firefox/WebKit coverage
  (`docs_site/content/about/compatibility.md:8-48`). The Python workflow does
  exercise Linux and Windows across that range and macOS at the endpoints, with
  focused cross-browser PR jobs and a scheduled full engine sweep
  (`.github/workflows/py--tests.yml:37-49`,
  `.github/workflows/py--tests.yml:86-169`,
  `.github/workflows/py--tests-cross-browser.yml:1-55`). Later stages must still
  inspect actual release artifacts and observed workflow results.
- The public adapter documentation names FastAPI/Starlette, Flask, Django, bare
  ASGI, and bare WSGI and documents multi-worker shared-cache constraints
  (`docs_site/content/web-frameworks.md:53-73`,
  `docs_site/content/web-frameworks.md:194-223`). Exact support floors and
  realistic deployments remain unproved.
- Releases are independently tagged per package, so "Citry v1 beta" cannot
  imply that every first-party package shares a major version
  (`CONTRIBUTING.md:63-69`).
- The security policy supports only each package's latest release, uses private
  GitHub advisories, and aims to acknowledge reports within a few days
  (`SECURITY.md:3-35`). This charter retains latest-beta support and adds a
  bounded critical-security bridge for users whom normal resolution leaves on
  the current final release.
- `citry-ui` declares itself a Phase 6 packaging spike and pre-alpha package,
  while `pygments-citry` is an independently versioned lexer package
  (`packages/py/citry_ui/pyproject.toml:5-30`,
  `packages/py/pygments_citry/pyproject.toml:5-42`). Neither should silently
  become part of the core beta promise.
- The root package's claim that only `citry.__all__` is stable and all submodules
  are internal conflicts with documented public `citry.contrib` and `citry.ext`
  imports (`packages/py/citry/citry/__init__.py:9`,
  `packages/py/citry/citry/contrib/__init__.py:20`,
  `docs_site/content/security.md:71`). Stage 3 must inventory the actual public
  API before the beta compatibility policy can be applied.
- Client-active use currently requires Alpine's standard evaluator and
  `unsafe-eval`; the CSP build is unsupported
  (`docs_site/content/advanced/alpine-runtime.md:35-47`). This must remain a
  visible deployment limitation unless later evidence changes it.
- Stage 0 observed that GitHub Discussions was disabled while Issues was enabled
  (`docs/design/v1_beta_research/public_service_snapshot.md:27-30`). The proposed
  first-beta feedback route therefore uses Issues for both defects and labeled
  questions/proposals rather than depending on a setting that is currently off.

These are document and source observations, not completion findings. Stage 2
and later retain responsibility for proving the implementation and deciding
the affected work.

## External policy basis

The external evidence pass is deliberately limited to rules that shape the
charter. Full notes and sources are in
[`stage1_external_norms.md`](stage1_external_norms.md); they do not attempt the
later ecosystem, positioning, or outreach research.

- PyPA's [version specifier
  specification](https://packaging.python.org/en/latest/specifications/version-specifiers/)
  establishes the `1.0.0b1` spelling, ordering, and installer pre-release
  behavior. A `0.3.0` Beta classifier does not create equivalent resolver
  semantics.
- The [Python version status table](https://devguide.python.org/versions/)
  placed Python 3.10 in security-fix-only status through October 2026 on the
  observation date. The proposed first-beta support therefore has an explicit
  review point.
- [django-components compatibility
  policy](https://django-components.github.io/django-components/latest/overview/compatibility/)
  and [source
  manifest](https://github.com/django-components/django-components/blob/master/pyproject.toml)
  make it the closest package analogue: wrapper 0.151.1 selects
  `djc-core>=1.3.1`, alongside an explicit compatibility matrix, tested browser
  engines, and versioned deprecations.
- Django's [release
  process](https://docs.djangoproject.com/en/dev/internals/release-process/)
  illustrates a staged freeze and long deprecation window. Phoenix LiveView's
  [security
  policy](https://github.com/phoenixframework/phoenix_live_view/blob/main/SECURITY.md)
  illustrates explicit supported lines. These are precedents, not proof that a
  solo-maintained Citry can sustain the same promises.
- Reflex demonstrates the viable alternative of ordinary `0.x` releases with a
  Beta classifier and migration discipline. That supports the fallback path,
  but not calling a resolver-stable `0.3.0` package "v1 beta." See the [Reflex
  PyPI project](https://pypi.org/project/reflex/).

## Stage 10 decision register

These items intentionally remain open while active development and the deeper
research continue. Stages 2 through 9 may use the proposed defaults as
hypotheses for gathering evidence, identifying conflicts, and comparing
alternatives. They must not treat them as approved promises, use them to discard
work irreversibly, or require the maintainer to commit to the beta contract.

Stage 10 will return to the complete evidence and ask the maintainer to accept,
change, defer, or reject each material decision before the actual execution plan
is approved.

- [ ] Product thesis, primary audiences, and launch-critical jobs
- [ ] `citry==1.0.0b1` as the release identity
- [ ] Absorb the current `v0.3.0`/Unreleased work rather than publish 0.3.0 first
- [ ] Package roles, especially deferring `citry-ui`
- [ ] Candidate public capability set and explicit non-goals
- [ ] CPython and operating-system support proposal
- [ ] Browser support wording
- [ ] Host list and candidate version floors
- [ ] First-party-only protocol support during the first beta
- [ ] Beta breaking-change policy and RC freeze
- [ ] Latest-beta support, the 0.2 critical-security bridge, and acknowledgement wording
- [ ] Issues-first feedback routes and maintainer support expectations
- [ ] Beta entry and RC exit criteria

The independently reviewed Stage 1 draft is sufficient for later research to
evaluate the repository against these hypotheses. It does not authorize code
changes, package publication, GitHub settings changes, issue creation, outreach,
release activity, or any public compatibility commitment.
