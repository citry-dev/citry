# Design: Citry user documentation content

**Status (2026-07-26): Stages 1 and 2 complete; Stage 3 pilot voice accepted;
the twelve-page Getting started journey is authored and its local, FastAPI,
Events, State, form, and fragment checks pass. Independent review is complete;
the browser-only slice still needs its final plain-Alpine activation gate.**

This document controls the research, information architecture, editorial
system, migration, and verification of Citry's user-oriented documentation.
It covers the reader-facing material under `docs_site/content/`, the runnable
material under `docs_site/examples/`, the included source under
`docs_site/snippets/`, and both generated and authored public Reference pages.

[`docs_site.md`](docs_site.md) remains the design and history of the site
builder. Its Phase 7 notes and content-related decision records are inputs to
this plan. When the two documents disagree about content work, this document
is authoritative. Repository-wide writing and component rules remain owned by
[`CLAUDE.md`](../../CLAUDE.md) and the
[component authoring guide](../best-practices/component-authoring.md).

This is the controlling plan. Completed research records and focused Stage 4
designs are linked below. Page rewrites, navigation changes, and broad
Reference docstring work still require their own review steps.

## Decisions at a glance

- Migrate the current corpus deliberately. Do not discard it wholesale and do
  not preserve it merely because it exists. Each page, example, and snippet
  gets evidence, a reader job, and an explicit disposition.
- Keep three distinct primary lenses: Docs explains and teaches, Examples
  provides code-first recipes, and Reference describes the public API.
- Treat `docs_site/snippets/` as an authoring mechanism, not a reader-facing
  information category. A snippet earns its place only when shared executable
  source prevents drift.
- Use one recognizable Citry voice with tones chosen for the reader's
  situation. Individual pages do not invent independent voices.
- Organize around reader jobs and journeys, then map product concepts and API
  symbols into that structure. The settled roles of Docs, Examples, Reference,
  and Community remain fixed; current page grouping and ordering are evidence,
  not immutable constraints.
- Verify claims against current behavior. Existing prose, design docs, and
  port-parity audits are leads until implementation and tests support them.
- Start with a bounded vertical pilot. Review its cost and results before an
  exhaustive repository sweep or parallel authoring pass.
- Keep the current site available while approved slices are prepared. Preserve
  useful content, tested examples, and public URLs until their successors and
  redirects are verified.

## Scope

### In scope

- the home page and evergreen Docs pages;
- the Examples index, future recipe pages, runnable demonstrations, and their
  tests;
- source included from `docs_site/snippets/`;
- generated API Reference prose and examples sourced from public docstrings,
  plus authored Reference pages for public surfaces without one Python owner;
- Community, About, migration, troubleshooting, security, and framework
  integration content;
- alignment with the root README, release notes, search descriptions, and
  Blog and future UI Kit boundaries;
- reader personas and jobs, information architecture, voice and tone, page
  archetypes, terminology, cross-linking, factual traceability, testing, and
  review workflow.

### Not part of this planning step

- rewriting or deleting any current page, example, snippet, or docstring;
- changing the navigation, templates, CSS, JavaScript, or build system;
- implementing the Citry UI catalog;
- deciding the final v1 beta product and support promises;
- publishing, deploying, or committing changes.

Later content work must not document a planned feature as current behavior.
Accepted future designs may inform the structure, but evergreen pages describe
what a reader can use in the supported product version.

The initial research boundary is current shipped public behavior: exported
Python APIs, commands, settings, host adapters, browser behavior, errors, and
generated artifacts that a user can encounter in the active working tree. This
boundary permits inventory and factual research without treating every shipped
capability as supported for the next release. Before the content map is frozen,
the maintainer must accept the relevant product and support scope or approve a
narrower explicit subset. Capabilities outside that accepted subset remain
recorded without becoming evergreen promises.

## Current baseline

The baseline must be refreshed when the content program begins because the
working tree is active. As observed on 2026-07-27, the current authoring corpus
contains:

- 69 Markdown pages under `docs_site/content/`;
- nine runnable example families under `docs_site/examples/`, each with a
  component, page, and regression test;
- five non-package Python modules under `docs_site/snippets/`;
- one HTML snippet that safely shows the otherwise nested `<c-raw>` syntax;
- four migration pages that include marked sections from four snippet modules;
  the fifth module verifies the migration snippets and is not directly shown;
- three other pages that use the snippet extension: the Built-in tags page and
  the repository's Code of Conduct and license.

All 69 pages have explicit title and description front matter and all 69 are
reachable through the authored or generated navigation. The current navigation
can regroup a page without changing its URL, so prefer a navigation-only move
when the public path remains meaningful. A physical source move that changes
the clean URL needs the redirect process described below.

Examples now has one authored recipe page per runnable family. Each page owns
its title, description, prose, and one `<c-example>` card; `_nav.yml` owns the
reader-facing grouping and order. Runnable demos use
`/examples/<slug>/demo/`, leaving `/examples/<slug>/` for the recipe. The rich
browser card projects to component source, page source, and a live-result link
in Markdown companions and `llms-full.txt`. Structured metadata for framework,
prerequisites, audience, related pages, and test tier is still open if the
cookbook grows enough to need filtering beyond the navigation groups.

The earlier content-port audit is valuable provenance, but it answers whether
django-components material was represented. It does not prove that today's
Citry journeys are complete, that newer Events and migration material is
correct, or that the current grouping matches how readers look for help. Its
claim of complete port coverage must not be reused as a claim of complete user
documentation.

The Phase 7 notes also refer to roughly 29 pages, so their size and fan-out
assumptions are stale. A fresh inventory is the first execution stage.

## Outcomes and meaningful measures

The content program should make these statements true:

1. A reader can identify the right starting point from their situation and
   reach a useful result without understanding Citry internals.
2. A first-time user can install Citry, render a component, integrate it with a
   chosen host when needed, and diagnose common failures from verified material.
3. A working user can complete focused tasks from code-first recipes and follow
   links to the concept and API contract without encountering duplicated,
   contradictory instructions.
4. An evaluator can understand Citry's value, supported environments,
   limitations, security posture, and operational expectations without hype or
   roadmap claims presented as fact.
5. A maintainer can trace each material claim and copyable example to current
   evidence, repeat its verification, and know which reader surface owns it.
6. Changes to public behavior have an obvious documentation owner and a check
   that detects stale pages or examples where practical.

Measure task coverage, factual traceability, example execution, findability,
and reader success. Page count and word count are inventory facts, not quality
targets.

## Reader model

Personas are working hypotheses, not invented biographies. Record the reader's
context, prior knowledge, job, concern, and successful outcome. Separate three
dimensions that are often mixed together:

- **segment:** professional team, independent developer, learner, component or
  tooling author;
- **situation:** evaluating, learning, building, debugging, migrating,
  operating, or looking up a contract;
- **job:** the concrete outcome the reader needs now.

The [provisional beta charter](v1_beta_research/product_beta_charter.md)
provides useful audience and job evidence, but its decisions are still open.
The content research must validate them rather than silently turning them into
approved product policy.

### Provisional primary readers

| Reader situation | What they already know | Main questions and successful outcome |
| --- | --- | --- |
| Evaluating Python web engineer | Python, HTML, and at least one web framework | Understand what Citry does, where it fits, what it supports, and whether its tradeoffs suit the project. |
| First-time component author | Python and basic HTML, but not Citry's mental model | Install Citry, render a useful typed component, understand the two syntax rules, and know the next step. |
| Application builder | Core Citry component and template concepts | Complete a specific task involving composition, assets, Alpine, Events, forms, fragments, caching, testing, or deployment. |
| Integrator or migrator | An existing Python application or another server-side component model | Connect Citry to the host or translate an existing pattern without losing framework security and operational behavior. |
| Reusable component or extension author | Citry's core APIs and Python packaging | Design stable public inputs, slots, behavior, styling, scenarios, extensions, and packages. |

Contributors and maintainers are a secondary documentation audience. Their
build, review, release, and governance jobs primarily belong under Community
and in internal repository documentation. They should not make onboarding or
ordinary task pages heavier.

### Reader research to collect

Before freezing the personas or navigation, collect and classify:

- recurring questions and failure reports from issues, support channels, and
  maintainer experience;
- searches that return weak results or no result, if privacy-safe search data
  becomes available;
- points where a new user abandons or detours from the current getting-started
  path;
- tasks from representative Django, FastAPI/Starlette, Flask, ASGI, and WSGI
  applications;
- migration questions from Component.View, django-unicorn, Tetra,
  livecomponents, and django-components users;
- expectations set by comparable Python and frontend documentation;
- jobs in the provisional beta charter and the Citry UI product charter;
- direct maintainer decisions about audience priority and support scope.

Do not collect personal or private user data without an approved purpose,
retention rule, and storage location. When direct user evidence is unavailable,
label the resulting persona or priority as an inference and design a later test.

## Content surface contract

| Surface | Reader question | Primary form | Ownership rule | Publication scope |
| --- | --- | --- | --- | --- |
| Home and root README | "What is Citry, can I use it, and where do I start?" | Proof-led overview and shortest path to first success | Keep the promise and first example aligned. The README must also render correctly outside the docs site. | The docs home is `versioned` today; `_nav.yml` can make a future project landing item `site`. The repository README is outside the site build. |
| Docs | "Teach me this journey or help me understand it." | Tutorials, explanations, integration guides, migrations, troubleshooting, and operational guidance | Own concepts, prerequisites, mental models, choices, and longer sequences. | `versioned` |
| Examples | "Show me code for doing this task." | Short, tested recipes with code first and only the explanation needed to use it | Own task-shaped, copyable implementations. Link to Docs for concepts and Reference for contracts. | `versioned` |
| Reference | "What exactly does this public API accept, do, return, or raise?" | Orderly API descriptions and compact usage examples | Follow the current public surface. Generate Python entries from public docstrings; author non-Python surfaces against an explicit entry registry. | `versioned` |
| Community | "How do I get help, participate, or maintain the project?" | Support, contribution, governance, people, policy, and maintainer workflows | Own contributor and community operations, not ordinary product usage. | `site` |
| Release notes | "What changed, and what must I do when upgrading?" | Versioned user-observable changes and migration links | Derive from the changelog and public release facts. Do not use it as evergreen explanation. | `versioned` |
| Blog | "What is the project thinking, learning, or announcing now?" | Dated, authored long-form posts | Own time-bound context and updates. Evergreen instructions must live elsewhere. | `site` |
| UI Kit, planned | "Which Citry UI component solves this need, and how do I use it?" | Component catalog projected from the accepted Python scenario source | Do not create a second hand-authored scenario catalog. The current docs rewrite must not wait for this unfinished surface. | Decide when the surface is designed. |
| Snippets | No direct reader question | Shared executable source included by another surface | Keep only when inclusion reduces drift and the source has known consumers and verification. | Inherit from the consuming page; snippets are not published routes. |

Content type follows the reader's question:

- a guided learning sequence belongs in a Docs tutorial;
- one concrete task belongs in Examples;
- the reason a behavior exists and how to think about it belongs in a Docs
  explanation;
- exact callable or type behavior belongs in Reference;
- a framework journey may have a Docs guide plus several focused Examples;
- a migration guide belongs in Docs and can link to recipes for individual
  translations;
- a time-bound update belongs in Blog or release notes;
- contributor and policy material belongs in Community.

A page may contain more than one mode when the reader's task needs it. It must
still have one primary job and one canonical owner for each detailed fact.

## Voice and tone

Citry should have one editorial voice:

- direct and concrete;
- warm without being chatty or patronizing;
- confident where behavior is verified and candid where limits remain;
- practical, with actions and observable results before mechanisms;
- respectful of the reader's time and existing Python or web knowledge;
- specific enough that a first-time visitor does not need hidden repository
  context.

The tone changes with the reader's situation:

| Content | Tone | Typical opening |
| --- | --- | --- |
| Home and evaluation | Confident, concise, proof-led | State the problem Citry solves, show a representative result, then name support and limits. |
| Tutorial | Encouraging, paced, explanatory | State what the reader will build, prerequisites, and the visible result. |
| Example recipe | Brisk, task-first, imperative | Show the working code and outcome, then explain the lines that matter. |
| Concept explanation | Curious, analytical, concrete | Start with when the concept matters and follow the data or control flow. |
| Reference | Neutral, exact, consistent | Summarize the public contract in one sentence, then parameters, results, failures, and a compact example where useful. |
| Migration | Candid, comparative, recovery-oriented | Name the familiar old task, the Citry model that performs it, behavior differences, and a safe sequence. |
| Troubleshooting and security | Calm, symptom-first, proportionate | Show what the reader observes, likely causes, how to confirm one, and the fix. |
| Community | Welcoming and procedurally precise | State who the process is for, what to do, and what response to expect. |
| Blog | Authored, dated, and more personal | Make the context and author clear; link durable instructions back to evergreen pages. |

Apply the repository house style in `CLAUDE.md`: plain words, action-led
sentences, explained project terms, descriptive headings, no private internals
or roadmap in user docs, and wrong/right examples when warning about a natural
mistake.

Use **insert** for template substitution: `{{ value }}` inserts a value where
the expression appears. Reserve **print** for an actual `print()` call, command
output, or another operation that writes text to a stream.

## Content principles

### Lead with the reader's job

Every page states who it helps, what they will accomplish, and any prerequisite
that changes the result. Begin with the shortest useful path. Explain the
mechanism when it helps the reader predict behavior or recover from failure.

### Teach beginner tutorials from the result backward

[`Your first component`](../../docs_site/content/getting-started/your-first-component.md)
is the accepted voice and pacing example for a beginner tutorial. It works
because it starts with something the reader wants to see, then introduces each
Citry term only when that term helps the reader change the result.

Apply these rules:

1. **Start with the visible result and why it is useful.** "Build a reusable
   card with a colored top border" gives the reader a picture and a reason to
   continue. "Build a typed component with one input and one slot" makes the
   reader decode the implementation before they know what they are making.
2. **Move from familiar material to unfamiliar material.** Start with the HTML
   in a component, then point out the one Citry tag. After the reader sees
   where `<c-slot />` sits, explain that Citry calls this replaceable area a
   slot.
3. **Define names through the action they enable.** For example: "`Kwargs`
   lists the `name=value` options you can choose when you use the Card." Do not
   start with schema, composition, ownership, or other implementation
   categories and leave the reader to reconstruct the action.
4. **Assume only the stated prerequisites.** A reader may use Python for
   research, design, medicine, data work, or teaching without thinking like a
   web-framework author. Do not say "the part you already know" when the page
   has not established that knowledge. "We'll unpack it one piece at a time"
   is both warmer and more accurate.
5. **Give complete physical instructions.** Name the file, show where it goes,
   provide the command to run, and say what the reader should see. Connect two
   forms explicitly: "The `slots` dictionary is the Python way to fill the
   same default slot."
6. **Keep generated internals out of the learning path.** Shorten generated
   HTML to the element, text, and styles that prove success. If Citry adds
   attributes the reader does not control, say only what they need to act:
   "The real HTML contains a few extra attributes that Citry uses. You do not
   need to write or remember them."
7. **Explain limitations at the moment they matter.** The Card first works,
   then the tutorial explains that ordinary CSS selectors can affect other
   matching elements. The warning is attached to a concrete class name and a
   simple action: choose a distinctive name.
8. **Pair a natural mistake with the repair.** Show the missing value, the
   resulting error, a plain explanation, and the corrected code. Avoid a list
   of exception contracts before the reader has completed the happy path.
9. **End with the reader's accomplishment.** Recap what their component can do
   in ordinary language, then link to the next goals. Do not close a beginner
   page with internal categories such as "input-shape failures" or
   "instance-scoped values."

The same fact can use different language on different surfaces. A tutorial
says "each Card keeps its own color." An Example points to the line that
changes the color. Reference can then name `css_data()`, its accepted values,
and its error behavior precisely. Precision belongs everywhere; API vocabulary
appears only where it helps that reader finish the job.

### Make a tutorial's progression visible

When a tutorial crosses Python, HTML, and browser JavaScript, follow the action
in the order the reader experiences it. Say where each part runs, what it sends
across the boundary, and which part receives it next. Do not make the reader
reconstruct that path from separate descriptions of each API.

When one lesson changes files from an earlier lesson, introduce the change
before showing the next complete version. Mark the new lines in that source,
then repeat the important new fragment below and explain it without the
unchanged code around it. A returning reader can spot the delta, while a reader
who entered on this page still receives a complete example.

At the first meaningful use of an API or syntax feature on each page, link to
the place that owns its full contract. Use Reference for an exact public API
and the canonical Docs page for a broader concept. Later repetitions on the
same page do not need the same link.

### Use progressive disclosure at three levels

1. **Across the site:** evaluation and first success lead to common tasks;
   advanced authoring, operations, and internals appear later.
2. **Within a page:** outcome and minimal working path come before variations,
   edge cases, and deeper explanation.
3. **Within an example:** show the complete relevant unit, highlight the lines
   that matter, and link to the broader contract.

Progressive disclosure must not hide a prerequisite, security requirement,
data-loss risk, compatibility limit, or other fact needed to use the common
path safely.

### Publish evidence, not inherited claims

Implementation and observable behavior are authoritative for what exists.
Tests and built artifacts show that behavior is repeatable. Public docstrings
describe the Reference presentation but still require implementation checks.
Accepted design docs can describe future intent only when the page is clearly
time-bound or marked as a proposal. Existing prose is candidate material to
verify.

When sources conflict, record the contradiction. Do not choose the most
convenient claim or make the prose vague enough to conceal it.

### Give each fact one canonical owner

Explain a concept fully in one place. Other surfaces summarize only what their
reader needs and link to the canonical detail. A recipe may repeat a signature
fragment needed to copy the code, but it must not maintain a second description
of every option or limitation.

### Make examples honest and copyable

Runnable examples are the default when readers are expected to copy or adapt
the code. Intentionally abbreviated code is allowed when unrelated setup would
obscure the lesson, but the omission must be obvious and the visible pattern
must remain valid. Never present illustrative pseudocode as a complete runnable
program.

All component examples follow the repository's component-authoring and
formatting conventions. `template`, `js`, and `css` use multiline strings;
nested schemas and data-method types are explicit where the example teaches a
production pattern; templates and CSS are formatted for review. A small
teaching excerpt may omit unrelated schemas or imports, but it must not teach a
conflicting pattern.

### Show expected results and failures

For a task, show the observable success when it is not obvious. For a common
mistake, show the natural attempt, the symptom, why it fails in plain language,
and the correction. Document meaningful exceptions, security boundaries, and
unsupported combinations near the action they constrain.

### Write pages that stand on their own

A tutorial sequence may build on an explicitly linked prerequisite. Other
pages define local terms and do not assume the reader has traversed the
sidebar. Headings must communicate the section's subject to skim readers,
screen-reader users, search, and generated Markdown consumers.

### Keep durable and time-bound material separate

Evergreen pages describe the supported current product. Release notes and Blog
may explain change over time. Internal plans and future language support do not
belong in ordinary user guidance.

### Design for every presentation mode

Code, diagrams, examples, navigation labels, and callouts must remain readable
with light, dark, and automatic themes, at narrow and wide viewports, with a
keyboard and screen reader, and in generated Markdown where the site provides
it. Color cannot be the only carrier of meaning.

## Information collection plan

Research should produce evidence that can be reviewed and reused, not a pile of
notes that only its author understands. The minimum planned records live under
a future `docs/design/docs_content_research/` directory:

| Record | Purpose |
| --- | --- |
| `baseline.md` | Commit, working-tree fingerprint, content counts, commands, date, and changes that invalidate observations. |
| `reader_jobs.md` | Evidence for segments, situations, jobs, concerns, priority, and successful outcomes. |
| `content_inventory.tsv` | Every current page, example, snippet, generated Reference group, root README section, and release surface. |
| `fact_ledger.tsv` | User-facing claims and behavior with evidence, confidence, applicability, failure modes, and candidate owner. |
| `content_map.tsv` | Current artifact to proposed reader job, surface, URL, disposition, canonical owner, dependencies, and review wave. |
| `terminology.md` | Accepted public terms, first-use explanations, casing, and terms that still need a product decision. |
| `evidence_log.md` | Repeatable commands and concise observations that support or falsify ledger entries. |

If the pilot shows that two records are small or duplicate one another, combine
them. The records exist to make decisions reviewable, not to satisfy a fixed
file count.

### Evidence levels

Reuse the evidence discipline from the v1 beta research:

1. **Verified implementation:** traced through current source, callers, and
   focused tests.
2. **Artifact verified:** observed in a built package, generated site, or other
   shipped artifact.
3. **Live-project verified:** completed in a representative application with
   environment and outcome recorded.
4. **Publicly observed:** inspected on a public service on a stated date.
5. **Document-claimed:** stated in prose or a design but not confirmed.
6. **Inference:** a reasoned hypothesis with a named falsifying check.

No evergreen product claim should rely only on document-claimed or inferred
evidence.

### Fact ledger fields

Each material fact should record:

- a stable fact ID and concise assertion;
- the reader job and surface that need it;
- current, experimental, version-specific, planned, or internal applicability;
- implementation symbol or file, focused test, command, artifact, or public
  observation that supports it;
- evidence level, observation date, baseline ID, and confidence;
- prerequisites, supported hosts or versions, and security implications;
- observable success, failure behavior, and important edge cases;
- canonical content owner, supporting cross-links, and example requirement;
- disputed, verified, authored, reviewed, or intentionally omitted status.

Record evidence at the stable symbol, test, or command level where possible.
Line numbers may help a review but should not be the only locator because they
drift during active implementation.

### Record validation and failure behavior

The pilot must define required columns, enumerated values, and uniqueness rules
in the research directory's README before a record becomes a stage-gate input.
Apply these rules:

- a missing required field keeps the row explicitly incomplete and prevents it
  from satisfying a stage gate;
- a duplicate stable ID, unknown enumerated value, malformed baseline ID, or
  undocumented extra column is a validation error;
- two rows that claim canonical ownership of the same fact are a content-map
  conflict and prevent the map from freezing;
- a missing or stale source locator lowers the evidence to document-claimed or
  inference until the source is found and observed again;
- a blank optional field means not applicable only when the schema says so;
  otherwise use an explicit `unknown` or `pending` value;
- schema changes update the README and validator before existing rows are
  migrated. A checker must report wrong values and exit unsuccessfully rather
  than silently defaulting them.

Draft rows may remain incomplete during research. They cannot support authored
claims until their required fields validate and their evidence reaches the
level required by this plan.

### Collection order

1. Capture the active baseline without changing or discarding user work.
2. Inventory the existing surfaces, URLs, navigation, inbound links, examples,
   snippet consumers, Reference groups, tests, and generated outputs.
3. Gather reader-job evidence and rank jobs by frequency, impact, risk, and
   product priority.
4. Pilot the fact schema on one representative vertical journey.
5. Adjust the schema and estimate the full research cost from the pilot.
6. Sweep public behavior subsystem by subsystem: public API and CLI contracts,
   host adapters, errors, tests, built artifacts, then implementation details
   needed to explain observable behavior.
7. Reconcile current prose, README claims, examples, snippets, changelog, and
   accepted designs against that evidence.
8. Build a provisional content map after enough facts and reader evidence exist
   to justify an initial ownership and grouping proposal. Freeze it only after
   the subsystem deep dives reconcile the full accepted scope.

An exhaustive line-by-line sweep of every private implementation file is not
the default. Start from public behavior and reader jobs, then follow the call
paths needed to verify them. Inspect private code when it determines observable
behavior, a limitation, or an error, without exposing private names in the
published explanation.

## Current-artifact disposition

Every current artifact receives one of these decisions:

| Disposition | Meaning |
| --- | --- |
| Retain | The reader job, placement, facts, and presentation remain sound after verification. |
| Revise | The artifact has the right owner and job but needs factual, structural, or editorial work. |
| Split | One artifact serves distinct jobs that need separate destinations. |
| Merge | Several artifacts duplicate one job and should have one canonical owner. |
| Move | The material is useful but belongs on another surface or at another URL. |
| Rebuild | Preserve the job and verified facts, but replace the presentation or executable source. |
| Project | Generate the reader presentation from another accepted source, such as a Citry UI scenario or public docstring. |
| Retire | No current reader job or supported behavior justifies keeping it. |

No artifact is removed until its useful facts and inbound links have an
approved destination. A URL move needs a redirect, updated internal links, and
a check of public inbound references where practical.

### Snippet policy

For every snippet, record all consuming pages, the sections they include, and
the test or command that verifies it. Keep a shared snippet when at least one of
these is true:

- multiple pages must display the same executable source;
- a long file has several tested sections that readers need independently;
- the snippet is generated or exercised as a coherent program and including it
  prevents prose from drifting from the test.

Inline short code when indirection makes the page harder to review and shared
execution provides no benefit. Split a snippet whose consumers need materially
different prerequisites or behavior. A verification helper is not itself a
reader snippet and should be classified as test infrastructure.

### Examples policy

The Examples surface is permanent and grows into a cookbook. Not every recipe
must use the current live iframe card. Choose the smallest truthful form:

- an embedded live demo for visual or interactive component behavior;
- an executable focused recipe for a code task;
- a complete small project for a host integration or operational journey;
- a projection from an accepted scenario source when that source exists.

Each recipe states prerequisites, expected result, supported hosts or versions,
and the next Docs and Reference links. It has an execution check proportional
to the promise: import or render test for a focused snippet, integration test
for a host recipe, and browser plus accessibility checks for interactive UI.

The accepted [Citry UI scenario catalog](ui_research/scenario-catalog.md) will
eventually feed UI Kit pages and relevant examples. Its runner and docs
projection are unfinished, so the core content program must provide a verified
current source and a recorded future projection decision rather than wait or
duplicate scenarios.

The browser widget and the textual recipe are projections of one authored
example, not separate copies. Generated per-page Markdown and LLM indexes must
receive readable code and prose, not expanded tab controls, iframe markup, or
syntax-highlighter HTML.

## Page archetypes to design in the pilot

| Archetype | Minimum structure |
| --- | --- |
| Evaluation page | Reader problem, representative result, current support and limits, evidence links, next action. |
| Tutorial | Outcome, prerequisites, complete starting state, ordered steps with visible checkpoints, recap, next journey. |
| Explanation | When the concept matters, action or data flow, mental model, tradeoffs, boundaries, related tasks and Reference. |
| Example recipe | Task and prerequisites, code and expected result first, explanation of relevant lines, variations and failures, deeper links. |
| Framework guide | Supported versions, installation and initialization, minimal document, routes and assets, host security behavior, testing, production notes, troubleshooting. |
| Migration guide | Source concept, Citry mapping, behavior differences, staged procedure, verification, rollback or recovery concerns. |
| Troubleshooting entry | Observable symptom, fast checks, likely causes in order, confirmation, fix, prevention, escalation evidence. |
| Reference entry | One-sentence contract, signature, parameters or fields, result, exceptions and state effects, compact example, related symbols. |
| Operations guide | Supported topology, prerequisites, configuration, deploy and rollback steps, health checks, failure recovery, and limits. |
| Security guide | Threat or protected asset, required user action, safe default, verification, failure impact, and reporting route. |
| Community procedure | Audience, prerequisites, ordered action, expected response or ownership, conduct and escalation route. |
| Release note | User-observable change, affected versions, required action, migration link, and compatibility impact. |
| Blog post | Date, author, time-bound context, evidence or examples, and links to canonical evergreen guidance. |

The pilot should turn the tutorial, explanation, recipe, and Reference outlines
into small approved templates and examples of the voice. Stage 4 should finish
the remaining archetypes before their authoring wave. Do not force every page
into identical headings when a heading does not serve its job.

## Execution stages and review gates

### Stage 0: approve the content contract

Review this plan, its scope, provisional personas, evidence rules, surface
boundaries, and proposed pilot. Resolve only decisions that materially change
the research. Editorial preferences can remain open until the pilot produces
real samples.

**Gate:** the maintainer accepts the research scope and first pilot, or records
specific changes in this document.

### Stage 1: capture the baseline and current corpus

Create the research directory and inventory every current page, example,
snippet, Reference group, root README section, generated release surface, URL,
navigation entry, direct consumer, and existing test. Record the active commit
and fingerprints for uncommitted sources so concurrent changes can be detected.

Build and observe the current site only as needed to understand those artifacts.
Do not judge prose quality yet beyond obvious factual or rendering blockers.

**Gate:** every artifact has a row, every snippet and example has known
consumers and tests, and changed inputs are identified before later findings
rely on them.

### Stage 2: validate readers and jobs

Collect repository, maintainer, support, search, and representative-application
evidence available within the approved privacy boundary. Rank jobs, record
uncertainty, and produce a journey map from evaluation through operation and
migration.

**Gate:** each proposed primary journey names a reader context, prerequisite,
successful outcome, evidence strength, and priority. Unsupported personas stay
explicitly provisional.

### Stage 3: run one vertical pilot

Recommended pilot: define and render a typed component with one input, one
slot, and component-owned CSS with a per-render CSS value, then trace the same
journey across a tutorial section, a code-first recipe, and the relevant API
Reference entries. It is a common first
success, touches the three primary lenses, exercises component formatting, and
has observable output and failure cases without depending on an unstable host.

Use the pilot to test the fact ledger, content routing, page templates,
cross-links, code execution, review size, and tone samples. Record the number
of facts, dependencies, conflicts, and review time before expanding.

**Gate:** the maintainer can review the pilot as one coherent slice; every
published claim is traceable; the example runs; and the pilot yields a credible
estimate for the full sweep. If the scope is more than twice the estimate or
reveals unbounded dependency paths, stop and revise the plan.

### Stage 4: establish the provisional content map and editorial kit

Turn the validated jobs and pilot results into a proposed navigation and
content map. Approve terminology, page archetypes, voice samples, metadata,
cross-link rules, code-example classes, and disposition criteria. Keep
editorial metadata in the research ledger first: the current page front matter
accepts only title, description, canonical URL, indexing and search controls,
Open Graph image, and search boost. Adding audience, content type, prerequisite,
or framework fields to pages requires a separate schema and builder decision.

The first focused Stage 4 slice is the
[`Getting started journey design`](docs_content_research/getting_started_journey.md).
It maps the current pages to one required end-to-end path. The first five pages
teach rendering and composition, the next two add Alpine and browser component
boundaries, and FastAPI then carries the same application through Events,
State, a typed form, and a targeted server-rendered update. Other hosts remain
owned by **Docs > Guides > Web frameworks**.

The journey also records a verified product prerequisite. Plain rendered
Alpine directives are currently inert when no unrelated feature loads Citry's
client runtime. Citry should activate the owning client graph for settled
`x-*`, `@*`, and `:*` attributes before the browser-interaction page is
authored. That behavior change needs its own implementation plan and protocol,
compatibility, fragment, cache, browser, and payload checks. It is not yet a
reader-facing current-behavior claim.

**Gate:** each proposed page has one primary job, persona or situation, surface,
candidate canonical facts, URL plan, dependencies, and acceptance check.
Duplicate ownership and orphaned current URLs are resolved or explicitly open.
The map is approved as a research hypothesis, not frozen against later evidence.

### Stage 5: perform subsystem deep dives

Sweep the current shipped public research boundary in bounded groups such as
core components and rendering, template syntax, assets and browser behavior,
Events, hosts, caching and operations, extension and library authoring, and
tooling. Classify each capability against the maintainer-accepted product and
support scope before it becomes an evergreen promise. Update the fact ledger
and provisional content map before writing pages.

Independent groups may be researched in parallel after the pilot establishes
the schema. Cross-cutting concepts, terminology, and public-contract conflicts
remain centrally reviewed.

**Gate:** every capability and prioritized job in the accepted scope has a
verified fact set, an intentional content owner, or an explicit unsupported or
deferred decision. The maintainer accepts the scope and the reconciled content
map is then frozen for the first authoring waves. Later evidence can still
change it through a recorded decision.

### Stage 6: author in review-sized waves

Suggested order:

1. home, evaluation, installation, and first success;
2. core component, template, composition, and data-flow journeys;
3. hosts, assets, Alpine, fragments, forms, and Events;
4. testing, troubleshooting, security, performance, caching, and operations;
5. migrations, reusable component and extension authoring, About, and
   Community;
6. Examples expansion and any remaining consolidation.

Each wave includes its examples, snippets, cross-links, redirects, tests, and
content-map updates. Keep content and unrelated builder changes in separate
review batches. The maintainer's commits remain the approval gate.

**Gate:** the wave passes its technical and editorial checks, has independent
factual review, preserves approved URLs, and is accepted before the next large
wave depends on it.

### Stage 7: align Reference and public docstrings

After terminology and public concepts stabilize, rewrite public docstrings by
module or symbol family. Verify signatures, fields, returns, exceptions,
examples, and cross-references in the generated site.

This work can overlap later content waves only when the owning concept and
terminology are already accepted. It is not an independent bulk rewrite.

**Gate:** every in-scope public symbol has an intentional Reference disposition,
the generated entry matches current behavior, and examples and links render.

### Stage 8: verify the complete journey and cut over

Run structural, executable, browser, accessibility, search, SEO, and production
preview checks. Conduct task-based reading or usability sessions for the
highest-priority journeys. Compare the final content map with the baseline so
no useful fact, example behavior, snippet consumer, or public URL disappeared
silently.

**Gate:** acceptance coverage is reported by reader job and public capability,
remaining gaps are explicit, the deployed site is observed, and the maintainer
accepts the content release.

## Verification and coverage model

### Automated checks

- strict site build, front matter, headings, links, anchors, navigation,
  snippets, HTML, assets, and generated-site guards;
- runnable example and snippet tests, with host and browser tests where their
  claims require them;
- generated Reference discovery, signatures, cross-references, and docstring
  rendering;
- light, dark, and automatic-theme checks for code and interactive examples;
- concise, self-contained per-page Markdown and LLM output that does not expose
  expanded browser-widget implementation;
- keyboard, semantic HTML, screen-reader, reduced-motion, contrast, and narrow
  viewport checks for reader interactions;
- production-equivalent build and deployment workflows where the change
  affects their output.

### Human checks

- technical review against the fact ledger and observed behavior;
- editorial review against the reader job, voice, progressive disclosure, and
  canonical ownership;
- independent adversarial review for misleading claims, omitted failure modes,
  and examples that work only in the author's environment;
- task-based checks that ask a reader to find and complete an outcome without
  hints about the intended navigation path.

### Coverage to report

- **reader-job coverage:** prioritized jobs with a verified successful path;
- **public-capability coverage:** in-scope public behavior with a canonical
  page, Reference entry, or intentional omission;
- **claim coverage:** material claims linked to sufficient evidence;
- **example coverage:** copyable examples with the promised execution layer;
- **failure coverage:** high-impact errors, security requirements, and
  unsupported combinations with actionable guidance;
- **navigation and search coverage:** priority jobs findable by browsing and
  representative search terms;
- **migration coverage:** useful current facts and public URLs retained, moved
  with redirects, or intentionally retired;
- **presentation coverage:** priority pages readable across themes, viewports,
  keyboard, assistive technology, and generated Markdown.

Coverage reports must name exclusions and evidence levels. A high count of
pages or passing syntax checks does not prove that readers can finish a job.

## Failure modes and responses

| Failure mode | Response |
| --- | --- |
| Source, tests, and prose disagree | Mark the fact disputed, identify the owning implementation decision, and do not publish a definitive evergreen claim until resolved. |
| A design describes behavior that has not landed | Keep it in a design or dated update. Do not teach it as current product behavior. |
| Concurrent implementation changes invalidate research | Record a new baseline delta and rerun only observations whose inputs changed. |
| The pilot exposes much larger scope or dependency fan-out | Stop expansion, report the estimate and options, and obtain maintainer approval for a narrower or staged plan. |
| A runnable example cannot be made repeatable | Fix the product or test setup, narrow the promise, or classify the code clearly as illustrative. Do not silently remove the check. |
| Abbreviated code looks complete or teaches a conflicting pattern | Add the missing context, mark the omission clearly, or replace it with a tested focused example. |
| A snippet has no consumer or no independent value | Inline useful code or retire the asset after verifying no generated or external consumer depends on it. |
| One snippet's consumers require incompatible variants | Split the executable sources and give each a clear owner and test. |
| A rich browser example overwhelms Markdown, search, or LLM output | Generate a concise textual projection from the same authored example and test both projections. |
| Moving or merging a page breaks an established URL | Add a redirect and update inbound links before removing the old source. |
| A reader job spans several pages but has no clear path | Add a journey entry point and explicit next actions; do not duplicate every detail on the entry page. |
| Reader testing contradicts the proposed navigation | Revise the journey and labels. Do not compensate only by adding more prose. |
| External feedback or analytics are unavailable | Continue with repository and maintainer evidence, label priorities as inferred, and schedule a later falsifying check. |
| A security-sensitive fact cannot be published safely | Publish only the safe user action and route sensitive details through the approved private process. |

An unresolved fact should block the affected claim or page, not unrelated
inventory and research work.

## Decisions still needed

These do not block the initial baseline and inventory unless noted:

- approve or adjust the provisional primary reader priorities as direct-reader
  evidence becomes available;
- review the revised Getting started page sequence and the exact continuous
  tutorial application before its authoring wave;
- decide which support, issue, search, or live-project evidence may be used and
  under what privacy boundary;
- settle the public support and version promise before Stage 5 freezes the map
  and before authoring compatibility, deployment, and beta-specific guidance;
- decide how much existing URL stability to promise beyond preserving known
  inbound links by default;
- choose final UI Kit placement when that surface enters implementation; Blog
  metadata is defined in [`docs_blog.md`](docs_blog.md);
- decide whether Reference members use source order or a documented grouped
  order during the Reference content pass.

## Immediate next step after approval

Review and commit the completed **Install Citry** slice as its own gate. The
accepted Card remains the second page. After that, author **Use data in a
component** as the next review-sized slice from the
[`Getting started journey design`](docs_content_research/getting_started_journey.md).
Alpine activation belongs to separate runtime work. This content pass does not
publish the new behavior until the implementation is available to its
executable browser example.
