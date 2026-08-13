# Citry documentation content research

**Status (2026-07-26): Stage 1 and Stage 2 complete; Stage 3 typed-card pilot
voice accepted; the Stage 4 twelve-page Getting started journey is authored.
The standalone client-prop page and every server step pass in Chromium.
Independent review is complete; the plain-Alpine-only example still needs its
final activation gate.**

This directory holds the evidence produced by
[`docs_content.md`](../docs_content.md). The design document controls the work;
these files record observations against named repository baselines.

Stage 2 adds reader-job evidence and prioritization. Stage 3 adds the first
fact ledger and a bounded Docs, Examples, and Reference content slice. The full
content map and subsystem fact sweep remain later approved stages.

The 2026-07-28 Blog implementation adds its index, conditional generated Atom
surface, navigation, consumers, outputs, tests, and source fingerprints to the
Stage 1 inventory. The original dummy post and its fingerprint were removed on
2026-08-13; no post is currently published. Those inventory columns are the
scoped Blog content map for this delivery. This is an addendum to an already
stale baseline, not a claim that the broader inventory has been reconciled. The
separate program-wide `content_map.tsv` and its schema remain deferred with the
rest of that later stage.

## Stage 1 artifacts

- [`baseline.md`](baseline.md): opening repository identity, scope fingerprint,
  counts, toolchain, exclusions, and refresh rules.
- `baseline_fingerprints.tsv`: per-file closing fingerprints for every source
  used directly by the inventory.
- `content_inventory.tsv`: every in-scope user-content artifact and its current
  URL, navigation, consumers, generated outputs, and mapped tests.
- [`evidence_log.md`](evidence_log.md): repeatable commands and observations,
  including the closing reconciliation and validation results.
- `validate.py`: dependency-free structural validation for the TSV records.
- `test_validate.py`: focused failure-path tests for the validator.

## Stage 2 artifacts

- [`stage2_baseline.md`](stage2_baseline.md): repository identity, approved
  privacy boundary, unavailable evidence, and invalidation rules for the reader
  research.
- `reader_evidence.tsv`: one traceable observation per source, including a
  content hash for repository-local sources.
- `reader_jobs.tsv`: ranked reader jobs with context, prerequisites, outcomes,
  supporting evidence, uncertainty, and the disclosed priority score.
- [`reader_jobs.md`](reader_jobs.md): synthesis, priority interpretation, and
  the journey map from evaluation through operation and migration.

## Stage 3 artifacts

- [`stage3_pilot.md`](stage3_pilot.md): opening scope, pilot decisions,
  conflicts, verification, review-size measures, and the provisional full-sweep
  estimate.
- `fact_ledger.tsv`: material current-behavior facts projected through the
  pilot tutorial, recipe, and Reference entries.

The validator checks Stage 1 through Stage 3 records together. Stage 3 does not
freeze the eventual navigation or authorize the full content rewrite.

## Stage 4 artifacts

- [`getting_started_journey.md`](getting_started_journey.md): verified
  prerequisite map, required FastAPI-backed beginner sequence from first render
  through Alpine, Events, State, forms, and a targeted rendered update,
  current-page dispositions, the plain-Alpine product prerequisite, page
  briefs, and acceptance checks.

The accepted Stage 4 journey now controls the authored Getting started wave.
Its page briefs and acceptance checks remain the source for final review.

Check the current records without changing them with:

```sh
uv run --no-sync python docs/design/docs_content_research/validate.py
```

After an intentional input change, preview the old-to-new fingerprint delta:

```sh
uv run --no-sync python docs/design/docs_content_research/validate.py --capture
```

When a fingerprint file already exists and differs, this command reports every
added, removed, or changed input and refuses to overwrite it. Identify the
affected observations first, record their reconciliation, and then explicitly
accept the reported change:

```sh
uv run --no-sync python docs/design/docs_content_research/validate.py \
  --capture \
  --accept-changes
```

An initial `--capture` writes the deterministic fingerprint file when none
exists. Both successful capture forms validate the inventory and live inputs
after writing.

## Inventory boundary

One inventory row represents one reader-facing or reader-content unit:

- every Markdown page under `docs_site/content/`;
- every runnable family under `docs_site/examples/`;
- every non-package Python module under `docs_site/snippets/`;
- every repository source included directly into a page;
- the Reference overview and every generated Reference category;
- every reader-visible level-one or level-two section of the root README;
- the release index and every release page currently generated from the
  changelog;
- generated output families such as the 404 page, search, sitemap, robots,
  Markdown companions, LLM indexes, social cards, and version manifest;
- user-facing data and image assets consumed by these surfaces.

Private builder modules, tests, workflows, renderer sources, the executed native
extension, and the docs maintainer README are evidence locators, not separate
user-content rows. Package markers, bytecode, ordinary build caches, and
generated local site output are excluded. The host-cached external Python
inventory is an exception because it changes Reference rendering; its bytes are
recorded under a stable external locator. Released version snapshots would be
inventoried individually when they exist; the current tree contains only the
versions manifest.

## Inventory schema

`content_inventory.tsv` uses exactly these columns:

| Column | Meaning |
| --- | --- |
| `baseline` | Baseline ID supporting the row. |
| `artifact_id` | Stable unique ID within this research program. |
| `artifact_type` | One of the types below. |
| `source_locator` | Repository source path, optionally with a heading or named section. |
| `public_locator` | Current clean site URL or external rendering location; `n/a` when the source is not directly addressable. |
| `nav_location` | Current top-level area and sidebar section; `n/a` when not navigated. |
| `title` | Current reader-visible title or concise generated-surface name. |
| `source_kind` | How the reader material is authored or derived. |
| `consumer_locators` | Semicolon-separated direct consumers, `direct-reader`, or `none`. |
| `generated_outputs` | Semicolon-separated outputs produced from the artifact, or `none`. |
| `test_locators` | Semicolon-separated existing tests or guards, or `none`. |
| `evidence_state` | Strongest mapped evidence class below. This records the current mapping, not a product-support decision. |
| `inventory_state` | Whether the Stage 1 row itself is complete, incomplete, or disputed. |
| `notes` | Concise limits, special generation behavior, or unresolved observation; `none` when there is nothing to add. |

Allowed `artifact_type` values are:

- `content_page`
- `example_family`
- `snippet_module`
- `included_source`
- `reference_group`
- `readme_section`
- `release_surface`
- `generated_surface`
- `content_data`
- `static_asset`

Allowed `source_kind` values are `authored`, `included`, `generated`, and
`projected`.

Allowed `evidence_state` values are:

- `unverified`
- `guard-mapped`
- `test-mapped`
- `browser-test-mapped`
- `mixed-test-mapped`
- `observed-output`

`test-mapped` means a relevant test exists. The evidence log separately records
whether it passed against this baseline. A browser-test mapping does not imply
that the browser suite ran during Stage 1.

Allowed `inventory_state` values are `complete`, `incomplete`, and `disputed`.

## Fingerprint schema

`baseline_fingerprints.tsv` uses exactly these columns:

| Column | Meaning |
| --- | --- |
| `baseline` | Baseline ID. |
| `scope` | Why Stage 1 read the file. |
| `source_path` | Unique repository-relative file path, or the declared stable external-input locator. |
| `git_state` | Two-character porcelain state, `clean`, `untracked`, or `n/a` for an external input. |
| `byte_size` | File size at the closing capture. |
| `sha256` | SHA-256 of the file bytes at the closing capture. |

Allowed `scope` values are `content`, `example`, `snippet`, `reference`,
`readme_release`, `generated_surface`, `asset_data`, `test_guard`, `workflow`,
`research_control`, `toolchain`, and `external_input`.

## Reader evidence schema

`reader_evidence.tsv` uses exactly these columns:

| Column | Meaning |
| --- | --- |
| `baseline` | Stage 2 baseline ID supporting the row. |
| `evidence_id` | Stable unique ID in the form `EV-001`. |
| `evidence_kind` | Kind of source or explicit absence, from the values below. |
| `source_locator` | One repository path with optional heading or test name, one public URL, or an `unavailable:` locator. |
| `source_fingerprint` | SHA-256 of the repository file, or `n/a` for a public or unavailable source. |
| `observed_at` | UTC calendar date in `YYYY-MM-DD` form. |
| `observation` | Concise observation, not a product promise inferred beyond the source. |
| `evidence_level` | Strength class from the content design's evidence ladder. |
| `confidence` | Confidence in this observation, separately from the source class. |
| `privacy_state` | Why the source is safe to retain in this repository. |
| `limitations` | Known scope or interpretation limit; `none` only when no material limit was found. |
| `supports_jobs` | Semicolon-separated job IDs, or `none` when an unavailable source supports no job. |

Allowed `evidence_kind` values are:

- `repository_behavior`
- `automated_test`
- `artifact_observation`
- `representative_application`
- `public_support`
- `maintainer_decision`
- `provisional_design`
- `current_docs`
- `unavailable_source`

Allowed `evidence_level` values are `verified_implementation`,
`artifact_verified`, `live_project_verified`, `publicly_observed`,
`document_claimed`, and `inference`. An inspected test is not automatically a
passing test. Use `verified_implementation` only when current source, callers,
and relevant focused tests have been traced; record command results in the
evidence log when execution is part of the observation.

Allowed `confidence` values are `high`, `medium`, and `low`. Allowed
`privacy_state` values are `repository_local`, `public`, `aggregate_only`, and
`unavailable`. Private user data, private support messages, credentials, and
security-sensitive reproductions are never valid locators.

One row names one source. When several sources support the same observation,
use separate evidence rows so each source and limitation stays inspectable.
Repository locators are invalid when the recorded SHA-256 no longer matches the
file. Public observations are time-bound to `observed_at` and must be refreshed
before a later decision depends on current external state.

## Reader jobs schema

`reader_jobs.tsv` uses exactly these columns:

| Column | Meaning |
| --- | --- |
| `baseline` | Stage 2 baseline ID supporting the row. |
| `job_id` | Stable unique ID in the form `JOB-001`. |
| `segment` | Provisional reader segment. |
| `situation` | Immediate situation that creates the job. |
| `journey_phase` | Where the job belongs in the end-to-end journey. |
| `reader_context` | Relevant prior knowledge or project state. |
| `prerequisite` | What must already be true, or `none`. |
| `job_statement` | Concrete outcome the reader needs now. |
| `successful_outcome` | Observable completion state. |
| `failure_concern` | Main failure, harm, or blocking uncertainty the docs must address. |
| `evidence_ids` | Semicolon-separated supporting evidence IDs. |
| `evidence_strength` | Overall support after considering source quality and agreement. |
| `frequency` | Ordinal frequency score from 1 to 5. |
| `impact` | Ordinal outcome impact score from 1 to 5. |
| `risk` | Ordinal harm or recovery-cost score from 1 to 5. |
| `product_priority` | Ordinal priority in accepted or provisional product evidence, from 1 to 5. |
| `priority_score` | Sum of the four ordinal scores, from 4 to 20. |
| `priority_band` | `primary`, `important`, `supporting`, or `provisional`. |
| `confidence` | Confidence in the job and rank. |
| `persona_status` | Whether the segment hypothesis is supported, provisional, or secondary. |
| `notes` | Important scope or ranking qualification; `none` only when unnecessary. |

Allowed `segment` values are `professional_team`, `independent_developer`,
`learner`, `component_tooling_author`, and `contributor_maintainer`. Allowed
`situation` values are `evaluating`, `learning`, `building`, `integrating`,
`debugging`, `testing`, `operating`, `migrating`, `looking_up_contract`, and
`contributing`. Allowed `journey_phase` values are `evaluate`, `first_success`,
`build`, `integrate`, `debug`, `test`, `deploy_operate`, `migrate`,
`extend_reuse`, `lookup`, and `contribute`.

`evidence_strength` is `strong` when verified behavior and at least one
independent source agree, `moderate` when repository evidence is coherent but
direct user or live-project evidence is absent, `limited` when the job rests on
documents, sparse public reports, or inference, and `unavailable` when the
needed evidence could not be collected. Allowed `persona_status` values are
`supported`, `provisional`, and `secondary`.

The four scores are ordinal review aids, not measured usage statistics:

| Score | Frequency | Impact | Risk | Product priority |
| ---: | --- | --- | --- | --- |
| 1 | Exceptional or speculative | Convenience only | Easy local recovery | Outside current product scope |
| 2 | Occasional or narrow | Small task delay | Bounded confusion or rework | Optional supporting capability |
| 3 | Recurring for a subset | Blocks a useful task | Material debugging or compatibility cost | Named supporting workflow |
| 4 | Common for a primary journey | Blocks a major journey | Operational, migration, or security-sensitive cost | Launch-critical workflow component |
| 5 | Universal or gateway task | Blocks product adoption or use | Severe security, data, deployment, or recovery consequence | Explicit launch-critical outcome |

`priority_score` is the unweighted sum. Scores 16 through 20 are `primary`, 12
through 15 are `important`, 8 through 11 are `supporting`, and 4 through 7 are
`provisional`. Ties are reviewed by product priority, then risk, rather than by
inventing decimal precision. A primary job must have at least moderate evidence
and must name its reader context, prerequisite, successful outcome, and
failure concern. A job may be primary while its demographic segment remains
provisional; that distinction prevents repository behavior from being treated
as user-demographic research.

## Fact ledger schema

`fact_ledger.tsv` uses exactly these columns:

| Column | Meaning |
| --- | --- |
| `baseline` | Stage 3 baseline ID supporting the row. |
| `fact_id` | Stable unique ID in the form `FACT-001`. |
| `assertion` | One material current-behavior claim. |
| `reader_jobs` | Semicolon-separated Stage 2 job IDs served by the fact. |
| `surfaces` | Semicolon-separated projections from `docs`, `examples`, `reference`, and `research`. |
| `applicability` | `current`, `experimental`, `version_specific`, `planned`, or `internal`. |
| `source_locators` | Semicolon-separated implementation or authoritative-source locators. |
| `test_locators` | Semicolon-separated automated evidence locators, or `none`. |
| `evidence_level` | Strength class from the shared evidence ladder. |
| `confidence` | `high`, `medium`, or `low`. |
| `prerequisites` | Conditions that must hold before the assertion applies. |
| `supported_context` | Runtime, serialization, host, or version boundary actually verified. |
| `security_implications` | Relevant trust or safety boundary, or `none identified`. |
| `successful_outcome` | Observable evidence that the documented path worked. |
| `failure_behavior` | Observable error, fallback, or unsupported behavior. |
| `canonical_owner` | Reader surface that owns the detailed claim. |
| `supporting_links` | Deeper or adjacent reader links, or `none`. |
| `example_requirement` | Whether executable example coverage is `required`, `supporting`, or `none`. |
| `status` | `disputed`, `verified`, `authored`, `reviewed`, or `intentionally_omitted`. |
| `notes` | Important qualification, or `none`. |

`verified` means sufficient evidence was collected but no reader-facing prose
was authored. `authored` means the fact is projected into the pilot and its
automated checks pass; it does not claim maintainer acceptance. `reviewed` is
reserved for the maintainer's content gate. A disputed fact remains on the
research surface only and blocks definitive reader-facing prose.

Every authored or reviewed fact needs current or version-specific
applicability, implementation or artifact evidence, a test locator, and at
least one reader-facing surface. A fact whose example requirement is
`required` must be projected through Examples.

## Invalid records

All fields are required. Use `n/a`, `none`, `unknown`, or `pending` only where
the column definition permits the value. Empty fields never silently default.

The validator exits unsuccessfully for:

- a missing, extra, or reordered column;
- an empty required field;
- a duplicate artifact ID or fingerprint source path;
- an unknown enumerated value, malformed baseline ID, or record assigned to a
  different valid baseline;
- a missing local source, source heading, or test path;
- an undocumented extra artifact relative to the live content, example,
  snippet, image, README-section, or Reference-category sets;
- a live artifact missing from the inventory;
- an example or snippet without a known consumer, mapped test, or verified
  evidence state;
- an inventory row marked incomplete or disputed at the Stage 1 closing gate;
- a missing or extra fingerprint row relative to the declared closing evidence
  set;
- a fingerprint whose size, hash, or Git state no longer matches its source.
- a duplicate evidence or job ID, a broken evidence-to-job cross-reference, or
  a repository evidence locator whose fingerprint is stale;
- a priority score or band that does not match the disclosed rubric;
- a primary job without the Stage 2 gate fields or with limited or unavailable
  evidence;
- an unavailable evidence row that claims to support a job, or a public source
  represented as private or repository-local evidence.
- a duplicate or malformed fact ID, unknown fact enum, broken reader-job link,
  missing source or test locator, or invalid heading or Python symbol;
- a reader-facing disputed fact, an authored fact with weak evidence or no
  test, or a required example fact absent from Examples.

A stale source fingerprint invalidates only findings that depend on that file.
Refresh the baseline or record a delta before relying on those findings again.
Do not edit a stale hash until the changed input and affected observations are
identified.

## Delimiters and text rules

TSV fields contain no literal tabs or newlines. Semicolon-separated locator and
ID lists use no surrounding spaces. A source heading uses `#heading-slug`; a
test or symbol may use `::qualified_name`; a snippet region uses `:region-name`.
Notes remain plain text and must not contain private credentials, private user
data, or security-sensitive reproduction details.
