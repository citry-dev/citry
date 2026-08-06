# Stage 1 evidence log

**Baseline:** `DC1-20260726T101722Z-9d1a8636`

**Status (2026-07-26): Stage 1 corpus inventory and closing reconciliation
complete.**

This log records repeatable observations for Stage 1 of
[`docs_content.md`](../docs_content.md). It inventories the current corpus. It
does not approve the prose, choose future reader journeys, or decide which
artifacts should survive the content redesign.

## Opening capture

The opening baseline was captured before this research directory was created.
See [`baseline.md`](baseline.md) for the full identity, source boundary, host,
and aggregate command.

| Observation | Opening value |
| --- | --- |
| Captured at | `2026-07-26T10:17:22Z` |
| HEAD | `9d1a8636230480cd9ae62b5e9d85b3ce77677360` |
| Branch | `main`, ahead 19 and behind 0 relative to `origin/main` |
| Porcelain entries | 316 |
| Tracked working-tree diff | 185 files, 35,447 additions, 8,214 deletions |
| Staged diff | 44 files, 8,281 additions |
| Opening docs-content scope | 235 files |
| Opening scope SHA-256 | `b839a5ba4e8896f4cc54a3bf9a321cfc03ec0cfda23564ca8b7fae839beece70` |

The existing modifications and untracked docs sources belong to the maintainer.
Stage 1 did not stage, commit, revert, or rewrite them.

## Inventory procedure

The inventory was assembled in three bounded passes and then reconciled against
the live tree:

1. Authored Markdown, front matter, clean URLs, navigation, README sections,
   and release surfaces.
2. Runnable example families, snippet modules and regions, direct consumers,
   generated standalone demos, and focused tests.
3. Reference categories and symbols, generated outputs, assets, workflows,
   package projections, and built-package behavior.

The closing validator performs the mechanical reconciliation:

```sh
uv run --no-sync python docs/design/docs_content_research/validate.py
```

It checks the exact TSV schema, stable IDs, enumerations, required fields,
source and test paths, current live artifact sets, navigation coverage and
uniqueness, explicit page titles and descriptions, and every source
fingerprint. A mismatch is reported and exits unsuccessfully.

The complete row-level result is in `content_inventory.tsv`. Its 123 artifact
records are distributed as follows:

| Artifact type | Records |
| --- | ---: |
| Authored content pages | 54 |
| Runnable example families | 9 |
| Snippet modules | 5 |
| Included repository sources | 2 |
| Reference overview and categories | 16 |
| Root README sections | 14 |
| Generated release surfaces | 5 |
| Generated output families | 14 |
| People data source | 1 |
| Reader-facing image assets | 3 |

Every inventory row is marked `complete`. This means the Stage 1 mapping is
complete, not that the artifact is correct or adequately tested.

## Authored pages, URLs, and navigation

The source tree contains 54 Markdown pages and 54 unique clean URLs. The
navigation contains 54 unique page entries. Comparing the three sets found no
orphaned content page, dead navigation path, or duplicate navigation path.
Every page currently has explicit `title` and `description` front matter; no
page overrides the current default indexing, search, or canonical behavior.

The rendered top-level order is `Docs`, `Examples`, `Reference`, `Community`.
It is controlled by `_TOP_NAV_SPECS` in
`docs_site/_internal/components/doc_page.py`, not solely by the order of
`docs_site/content/_nav.yml`. The generated Reference section is appended at
build time. The `Docs` tab opens `/getting-started/installation/`; `/` remains
the separately navigated Home page. Exact current area and sidebar ownership is
recorded for every page in `content_inventory.tsv`.

Five reader-visible titles differ between the page and its navigation label:
Home/Citry, Nested templates/Nested templates in attributes, Dynamic
components/Dynamic components and elements, Sharing components/Component
libraries, and Hot reload/Hot reload during development. These are inventory
facts for later routing and terminology work, not Stage 1 defects.

The content sources are untracked at this baseline. Git-derived authors,
updated dates, and sitemap `lastmod` values therefore cannot be observed for
them. Later findings must not infer publication history from the absent data.

## Examples and snippets

Nine example families are discovered from `docs_site/examples/`. Every family
has one component module, one page module, at least one focused regression test,
one standalone demo URL, and one embedded card on `/examples/`. The builder
emits ten standalone example HTML files because Fragments also emits a fragment
variant.

| Evidence boundary | Current observation |
| --- | --- |
| Server-render coverage | All nine families have focused tests. |
| Browser interaction coverage | Tabs and Fragments have behavior-specific Chromium checks. |
| Gallery browser coverage | The gallery card count is checked. |
| Other interactive behavior | Not checked end to end for Form submission or the remaining server-oriented examples. |
| Reverse discovery guard | No guard fails when a new example family is present but never consumed. |
| Theme behavior | No example-specific dark/light assertion exists. |

The Examples page expands the nine source families into one 155,008-byte
Markdown body before HTML rendering. Standalone demos are raw generated HTML,
not layout `PageRecord` objects, so they do not independently receive Markdown
companions, sitemap/index records, LLM entries, or social cards.

The four reader-snippet modules have exactly these consumers:

| Snippet module | Included by |
| --- | --- |
| `migrate_component_view.py` | `/guides/migrate-from-component-view/` |
| `migrate_unicorn.py` | `/guides/migrate-from-django-unicorn/` |
| `migrate_tetra.py` | `/guides/migrate-from-tetra/` |
| `migrate_livecomponents.py` | `/guides/migrate-from-livecomponents/` |

`_verify_events_migrations.py` is test infrastructure consumed only by
`test_events_migration_examples.py`. `CODE_OF_CONDUCT.md` and `LICENSE` are
also included through the snippet mechanism into their Community pages. The
migration test imports and exercises the full modules and verifies selected
region output. A selected region is not necessarily a standalone program
because some regions rely on setup elsewhere in their module.

## Reference, README, and releases

The Reference surface has one overview plus 15 generated categories. The
category configuration currently selects 140 package symbols through Griffe
and seven built-in symbols. Focused tests cover category construction, public
entrypoints, annotations, cross-references, enrichers, source links, and output
guards. Generated Reference pages do not currently receive per-page Markdown
companions or Git metadata.

The root README has 14 reader-visible level-one or level-two sections outside
code fences. `packages/py/citry/README.md` projects the root README into the
package, and `packages/py/citry/pyproject.toml` selects it as package metadata.
A built sdist and wheel both contained the projected README in package
metadata. There is no dedicated executable README example corpus or guard that
checks the README and docs home for drift.

The release generator emits `/releases/` plus Unreleased, v0.3, v0.2, and v0.1
from `CHANGELOG.md`. The dated `2025-12-21` heading is explicitly excluded.
Generated release pages do not receive per-page Markdown companions or Git
metadata. The current public Unreleased body is 42,909 bytes. The package
metadata reports version `0.2.0` while a v0.3 release page is generated; Stage 1
records that mismatch without deciding release policy.

## Built and generated surfaces

A disposable production-style build was run without social-card rendering:

```sh
citry_docs_tmp=$(mktemp -d)
uv run --no-sync python -m docs_site build \
  --output "$citry_docs_tmp/site" \
  --no-social-cards
```

It completed with 54 authored pages, 16 Reference pages, five release pages,
ten standalone example outputs, 86 total HTML files, 54 Markdown companions,
and zero page failures. It emitted Pagefind, `sitemap.xml`, `robots.txt`,
`meta/indexing.json`, `llms.txt`, `llms-full.txt`, `objects.inv`, static assets,
and the Citry browser runtime.

| Generated observation | Value |
| --- | ---: |
| Sitemap URLs | 75 |
| Sitemap `lastmod` values | 0 |
| `llms.txt` links | 74 |
| `llms-full.txt` bytes | 1,348,690 |
| `objects.inv` bytes | 8,095 |
| Redirect stubs | 0 |
| Committed version snapshots | 0 |

The full-text LLM artifact is dominated by the expanded Examples page and
generated Reference content. Reference plus Examples account for about 65.2%
of its bytes, and some expanded components contribute browser-oriented HTML.
That is a current output characteristic for later product review, not a Stage 1
content-quality ruling.

A separate build with the available social-card browser and cache placed 75
cards. The source tree contains an empty `versions.json`; generating, committing,
and deploying the first real version snapshot remains operationally unproven.

Reference rendering consumed the pinned external inventory at
`https://docs.python.org/3.13/objects.inv`. The exact 149,862-byte cache input is
recorded as `external:python-3.13-objects.inv` with SHA-256
`060b0de08ce5c3d21a296427358abbf1c8dc5c2af6785f5c78bf5acda0cd79b5`;
it parsed to 18,423 external symbol targets. An adversarial build with the
external map forced empty still produced the same page counts but changed
`llms-full.txt` to 1,247,548 bytes and altered Reference HTML. The external
bytes are therefore a material input, not a disposable cache exclusion.

Before the closing verification, the installed workspace was checked against
the locks and requested docs extras:

```sh
uv sync --locked --all-packages --extra docs --extra social-cards --inexact
```

uv resolved 74 packages and checked 57 installed packages without changing the
environment. The closing fingerprints also include the root Python and Cargo
locks, toolchain declarations, relevant Citry Core Python and Rust sources, and
the executed Python 3.13 `_rust` extension. `--inexact` preserves the additive
browser-test package while the locked workspace and docs dependencies are
checked.

## Current tests and guards

The following closing checks were run from the repository root:

```sh
uv run --no-sync pytest docs/design/docs_content_research/test_validate.py -q
uv run --no-sync python docs/design/docs_content_research/validate.py
uv run --no-sync python -m docs_site build-check --strict
uv run --no-sync pytest docs_site/tests docs_site/examples -q
uv run --no-sync pytest docs_site/tests/e2e --browser chromium -q
python scripts/check.py --reporter agent
```

The changed-fingerprint workflow was also exercised. `--capture` reported the
old-to-new delta and refused to overwrite the existing file. Only after the
affected inputs and observations were reconciled was the same delta accepted
with `--capture --accept-changes`.

Final observed results:

| Check | Result |
| --- | --- |
| Research validator failure-path tests | 11 passed |
| Inventory and closing fingerprints | 123 records and 443 input fingerprints valid |
| Strict docs build guards | No findings |
| Docs unit, render, guard, and example suite | 331 passed, one Starlette deprecation warning |
| Chromium docs suite | 15 passed |
| Full repository gate | Earlier pass: all 10 phases passed; final repeat: seven passed and three failed on concurrent non-docs work |

The warning says Starlette's `TestClient` use of `httpx` is deprecated and
suggests `httpx2`. It did not fail the suite. Test mapping is recorded per
artifact. Stage 1 does not claim statement or branch coverage from passing test
counts.

The repository workflows in the closing evidence set are the six
`repo--docs-*.yml` files plus `py--citry--publish.yml`. `repo--docs-check.yml`
runs the docs build guards, docs/example suite, and a separate Chromium job.
The root `scripts/check.py` does not collect the dedicated docs suite, so both
the docs commands and the full repository gate are required.

The final repository repeat passed Cargo formatting, Clippy, Cargo tests, mypy,
Pyright, the Citry client check, and repository validators. Ruff check/format
failed on active changes in `test_alpine_conformance_e2e.py` and
`ownership_manifest.py`. Root pytest reported 4,147 passed, three failed, three
skipped, and one expected failure while retaining 93.69% coverage. The three
failures were in Alpine and ownership-manifest browser tests. Those files are
outside the authorized Stage 1 output, were changing concurrently, and were not
edited here. The exact opening docs scope remained unchanged, the research
validator remained valid, and the repeated docs-specific gates above passed.

## Independent review

Independent adversarial passes initially rejected the gate. They reproduced six
classes of issue, all repaired before closing:

- the fingerprint set now enforces completeness, exact baseline identity, live
  Git state, native renderer and toolchain inputs, and the external Python
  inventory;
- capture now reports a delta and refuses silent replacement unless
  `--accept-changes` is explicit;
- missing focused content, Git-metadata, and browser-test mappings were added;
- release heading locators now use their actual Markdown anchors and the People
  data row names its direct component consumer;
- examples and snippets cannot validate without a known consumer, mapped test,
  and verified evidence state, and focused tests cover those failure paths plus
  missing fingerprints, stale Git state, baseline mismatch, and safe capture.
- GitHub-style README heading validation now preserves literal hyphens and
  verifies the actual `#citry---refreshingly-simple-ui` source and public
  locator.

The reviewer reran a disposable build and reproduced the recorded page and
generated-surface counts. The final repair review found no remaining Stage 1
gate blocker.

## Closing reconciliation

The closing capture was taken at `2026-07-26T11:28:59Z` on the same HEAD as the
opening capture. The repository was still active: the full porcelain status had
665 entries, the working-tree diff had 188 tracked files with 33,031 additions
and 5,182 deletions, and the index had 47 files with 8,904 additions. Seven
untracked entries are the Stage 1 research files. These global changes are not
attributed to this work.

After the first closing candidates, concurrent work changed
`citry/ownership_manifest.py` and the generated `citry.js` client source, both
of which are reachable from document rendering. Each safe capture reported the
exact source delta and refused automatic replacement. Stage 1 waited for stable
hashes, explicitly accepted the final bytes, repeated the strict build, all 331
docs/example tests, and all 15 Chromium tests, then confirmed the 443-input
fingerprint set was stable. No earlier observation was silently carried across
the changed renderer inputs.

Recomputing the exact 235-file opening scope produced the original
`b839a5ba4e8896f4cc54a3bf9a321cfc03ec0cfda23564ca8b7fae839beece70`
aggregate. No opening docs-content input moved. The wider 443-input closing set
has aggregate SHA-256
`4bbea7044d9776cd7f137e53146bef6f43b11683e933b735e1573c5cf7909a77`;
this hashes the sorted
`<file-sha256>  <source-path>` records, including the stable external locator.

The opening scope did not include the package implementation because the
initial boundary was authored docs and builder sources. Reference generation,
native rendering, and built-package verification made package source, toolchain,
metadata, native extension, and external inventory inputs direct evidence during
the sweep. The 443-input closing fingerprint set therefore deliberately expands
the opening boundary. This is a disclosed scope expansion, not evidence that the
opening aggregate remained unchanged.

## Stage 1 limits carried forward

- An existing test locator means a test is mapped, not that it proves every
  meaningful behavior or reader journey.
- The inventory records current navigation and direct consumers. Reader-job
  fit, proposed routes, canonical ownership, and dispositions begin in later
  stages.
- Current prose and design claims remain leads. Stage 1 does not promote them
  to verified product facts.
- Generated artifacts were observed in disposable output. No deployment,
  public-service behavior, or historical version snapshot is claimed here.
- A changed fingerprint invalidates only observations that depend on that file.
  Run the validator before relying on this log and reconcile any reported
  delta rather than overwriting it silently.

## Stage 2 reader and job evidence

Stage 2 opened at `DC2-20260726T122608Z-6ad74ee1`. Its privacy boundary,
unavailable inputs, and row-level invalidation rule are recorded in
[`stage2_baseline.md`](stage2_baseline.md). No private support material,
analytics export, representative private application, or identifying reader
data was inspected.

### Repository and application checks

The reader-job sweep traced the product charter and current implementation,
then ran this focused host, Events, cache, reload, debugging, migration, and
example suite:

```sh
uv run --no-sync pytest -q \
  packages/py/citry/tests/test_contrib_fastapi.py \
  packages/py/citry/tests/test_contrib_hosts.py \
  packages/py/citry/tests/test_contrib_request.py \
  packages/py/citry/tests/test_events_host_parity.py \
  packages/py/citry/tests/test_events_django.py \
  packages/py/citry/tests/test_reload.py \
  packages/py/citry/tests/test_ext_cache_component.py \
  packages/py/citry/tests/test_ext_cache_fragment.py \
  packages/py/citry/tests/test_ext_cache_artifact.py \
  packages/py/citry/tests/test_ext_debug.py \
  packages/py/citry/tests/test_error_trace.py \
  docs_site/tests/test_events_migration_examples.py \
  docs_site/examples/card/test_example_card.py \
  docs_site/examples/control_flow/test_example_control_flow.py \
  docs_site/examples/error_fallback/test_example_error_fallback.py \
  docs_site/examples/form_submission/test_example_form_submission.py \
  docs_site/examples/fragments/test_example_fragments.py \
  docs_site/examples/provide_inject/test_example_provide_inject.py \
  docs_site/examples/recursion/test_example_recursion.py \
  docs_site/examples/slots/test_example_slots.py \
  docs_site/examples/tabs/test_example_tabs.py
```

Result: 376 passed and two skipped. The skips exercise the real `watchfiles`
and `watchdog` integrations; neither optional dependency was installed.

Four selected application-shaped browser files were then run:

```sh
uv run --no-sync pytest -q \
  packages/py/citry/tests/e2e/test_cache_replay_e2e.py \
  packages/py/citry/tests/e2e/test_ext_debug_e2e.py \
  packages/py/citry/tests/e2e/test_events_form_submission_port_e2e.py \
  packages/py/citry/tests/e2e/test_events_fragments_port_e2e.py
```

Result: eight passed in Chromium. The installed integration versions were
FastAPI 0.138.2, Starlette 1.3.1, and Django 6.0.6. Flask was not installed.
The Flask-named focused test uses a small object with a `wsgi_app` attribute;
it verifies the wrapper contract, not a real Flask application or version.

The tree contains no `demo/<host>/` applications, production deployment
scenario, multi-process rehearsal, isolated upgrade rehearsal, or end-to-end
migration of an application from the four source component systems. Adapter
mechanics are extensively tested, but host support floors and production
promises remain unverified.

The current package's publish-workflow smoke was also repeated locally in an
isolated temporary directory:

```sh
uv build --package citry --out-dir "$task_install_dir/dist"
python3.13 -m venv "$task_install_dir/venv"
"$task_install_dir/venv/bin/python" -m pip install \
  "$task_install_dir"/dist/*.whl
"$task_install_dir/venv/bin/python" -c \
  'import citry; print("citry", citry.__file__)'
"$task_install_dir/venv/bin/citry" --help
```

The current Citry 0.2.0 wheel built and installed with released citry-core
1.3.0 on macOS arm64 and Python 3.13. Import, CLI help, and the packaged client
runtime passed. Setuptools emitted its known warning that the table form of
`project.license` is deprecated. This one local artifact check does not prove a
future v1 beta artifact or the full promised platform matrix.

### Public support and search checks

The public GitHub repository and its non-pull-request Issue corpus were queried
through the GitHub REST API on 2026-07-26. There were 21 Issues: 18 open and
three closed. Every Issue and all four comments were authored by the project
maintainer. Authenticated requests reported `MEMBER` association while
unauthenticated requests reported `COLLABORATOR`, so the durable record does
not rely on that viewer-dependent label. The corpus is therefore useful as
maintainer-intent evidence, not as reader-frequency evidence. Discussions were
disabled.

Exact public Issue searches for references to `citry-dev/citry`, its GitHub
URL, and `citry.dev` returned no external corpus. This does not cover private
repositories, chat, deleted material, unnamed use, or unindexed sources. No
privacy-approved support export or search-query analytics was available.
Pagefind operates in the browser, and the planned search-analytics work is
explicitly blocked on selecting an analytics target.

The current public service was observed with:

```sh
curl -sSIL --max-time 20 https://citry.dev/
curl -sSIL --max-time 20 https://citry.dev/community/help/
```

Both URLs returned GitHub Pages HTTP 404 with valid TLS at 2026-07-26 12:34
UTC. This is point-in-time availability evidence, not a claim about reader
frequency or a permanent deployment state.

The local Help page and provisional beta charter route questions and defects
to Issues while Discussions remain disabled. The Issue chooser instead routes
"Question or idea" to Discussions. This is a current support-route
contradiction and must be resolved before that journey is presented as working.

A bounded predecessor sample covered the 23 django-components Issues already
linked by Citry's migration records. Across 106 comments, eight distinct
non-member participants appeared in six Issues. This is selected historical
lineage evidence, not a random current-user sample. The clearest transferable
signals were full-page versus fragment rendering in Issue 897, migration
familiarity in Issue 1499, low-boilerplate component organization in Issue
1240, machine-readable documentation in Issue 1118, and component-owned asset
behavior in Issue 1444.

### Stage 2 interpretation limits

- Repository behavior supports the existence and impact of jobs, not the
  demographics or measured frequency of the people doing them.
- The rank's frequency numbers are disclosed ordinal hypotheses based on how
  central and repeated a workflow is in current product evidence. They are not
  analytics or market measurements.
- All ordinary-reader segment labels remain provisional. Contributor and
  maintainer work is a secondary audience for this content program.
- Public observations must be refreshed before a current support or deployment
  claim is authored.
- Passing focused tests do not establish released-artifact installation,
  representative-app success, documentation usability, or production support.

### Closing checks and adversarial repairs

The research control files passed Ruff check and format checks. Eighteen
validator failure-path tests passed, including stale row fingerprints, broken
evidence-to-job links, score and band mismatch, weak primary jobs, unavailable
sources that claim support, missing Markdown headings, missing Python qualified
names, and unverified representative-application labels.

After the two disclosed renderer inputs changed, the affected docs gates were
repeated before accepting any new baseline fingerprints:

| Check | Result |
| --- | --- |
| Strict docs build | No findings |
| Docs and example suite | 331 passed with one Starlette deprecation warning |
| Docs Chromium suite | 15 passed |

The first independent Stage 2 review rejected the gate. It found invented
qualified test names that a file-only check had missed, a Citry-side migration
harness mislabeled as a representative application, clean installation
combined with stronger first-render evidence, viewer-dependent GitHub
association wording, and a concurrent changelog fingerprint change. The
repairs were:

- validate Python `::qualified_name` locators through the source AST and test
  the failure path;
- replace invented names with current symbols or file-level test locators;
- classify the migration harness as repository behavior and require genuine
  representative-application evidence to be `live_project_verified`;
- split clean install into `JOB-023`, run the isolated current-wheel smoke, and
  keep future beta and platform evidence unavailable;
- describe the Issue corpus as maintainer-authored while recording the
  authenticated `MEMBER` and unauthenticated `COLLABORATOR` difference;
- re-read the changed Unreleased section, confirm it still contains 92
  top-level entries, and refresh only that row's source hash.

The repository-wide gate was also run:

```sh
python scripts/check.py --reporter agent
```

Cargo formatting, Clippy, Cargo tests, Ruff check and format, mypy, Pyright,
the Citry client check, and repository validators passed. The root pytest phase
failed in active work outside this research output: 37 Chromium failures in
`test_client_graph_corpus_e2e.py`, 4,113 other tests passed, three skipped, and
one expected failure. Total coverage was 92.92%, below the required 93.0%.
Stage 2 did not modify those graph fixtures, browser tests, or implementation
sources.

The closing sequence was intentionally ordered. After updating the evidence-log
hash in `reader_evidence.tsv` and validating the Stage 2 rows, safe capture
reported the four new Stage 2 artifacts, three research-control edits, the
changed changelog, and four concurrent renderer or content inputs. It refused
to overwrite the old fingerprints until `--accept-changes` was explicit. The
changed docs inputs were stable across the repeated docs checks above.

The accepted capture contains 447 input fingerprints. The complete validator
then passed twice with all 123 Stage 1 inventory rows, the 447 fingerprints, 55
Stage 2 evidence rows, and 23 ranked jobs valid. No later content or navigation
work is part of this close.

## Stage 4 Getting started journey evidence

### Reconciled research inputs

The first Stage 4 slice added `getting_started_journey.md` and updated the
controlling content plan and research README to link it. The Stage 3 Card
tutorial also contains the maintainer-accepted final wording used as the new
beginner voice sample. No Getting started page was rewritten as part of the
Stage 4 journey design.

Safe fingerprint capture reported exactly these expected changes before it was
accepted:

- added `docs/design/docs_content_research/getting_started_journey.md`;
- changed `docs/design/docs_content.md`;
- changed `docs/design/docs_content_research/README.md`;
- changed `docs_site/content/getting-started/your-first-component.md`.

The new journey artifact was independently compared with all seven current
Getting started pages, the current navigation, the Stage 2 reader jobs, and
the relevant rendering, browser, host, and Events implementation.

### Capability and branch checks

The focused component, template, slot, asset, host, and Events checks were:

```sh
PYTHONPATH=. uv run --no-sync pytest -q \
  packages/py/citry/tests/test_component.py::TestTemplateData::test_typed_kwargs_resolve_in_template_without_template_data \
  packages/py/citry/tests/test_component.py::TestKwargsRenderValidation::test_missing_required_kwarg_raises \
  packages/py/citry/tests/test_tag_rules.py::TestKwargsValidation::test_unknown_attr_fails_at_parse \
  packages/py/citry/tests/test_slot_fills.py::TestImplicitDefaultSlot::test_body_content_fills_default_slot \
  packages/py/citry/tests/test_slots.py::TestSlotFieldDefaultFill::test_required_slot_uses_field_default_when_omitted \
  packages/py/citry/tests/test_deps_vars.py::TestComponentTransform::test_sugar_expands_to_register_component \
  packages/py/citry/tests/test_deps_vars.py::TestCssVars::test_distinct_css_data_gets_distinct_scoped_stylesheets \
  packages/py/citry/tests/test_deps_fragments.py::TestFragmentStrategy::test_fragment_carries_urls_not_content \
  packages/py/citry/tests/test_contrib_fastapi.py::TestMount::test_mount_records_the_prefix \
  packages/py/citry/tests/test_events.py::TestStateData::test_default_derivation_from_same_named_kwargs \
  packages/py/citry/tests/test_events.py::TestHandlerEnumeration::test_public_defs_are_handlers_in_definition_order \
  packages/py/citry/tests/test_events_bindings.py::TestStageOneEveryForm::test_locked_specs \
  packages/py/citry/tests/test_events_dispatch.py::TestHappyPaths::test_increment_renders_the_calling_instance
```

Result: 13 passed. FastAPI's compatibility import emitted one Starlette
deprecation warning about the installed `httpx` package.

Two representative browser checkpoints were then repeated:

```sh
PYTHONPATH=. uv run --no-sync pytest -q \
  packages/py/citry/tests/e2e/test_alpine_lifecycle_e2e.py::test_nested_scopes_multi_root_shared_root_and_init_dag \
  packages/py/citry/tests/e2e/test_events_pitch_e2e.py::test_counter_click_increments_through_the_server_and_morphs_the_button
```

Result: two passed in Chromium. These establish one `$component` and Alpine
path and one mounted Event round trip. They do not validate the future
tutorial examples, which still need their own executable and browser checks.

The initial Event design proposed a stateless first action, while the mounted
round trip above used State. A third focused browser check closed that boundary
before the page plan was kept:

```sh
PYTHONPATH=. uv run --no-sync pytest -q \
  packages/py/citry/tests/e2e/test_events_pitch_e2e.py::test_contact_form_shows_the_422_field_inline_and_a_corrected_submit_succeeds
```

Result: one passed in Chromium. Its `ContactForm.Events.submit(self, data)`
handler declares no State, returns a new `ContactForm`, and changes the visible
page through the mounted Events path without reloading it. This proves that a
stateless visible update is a valid tutorial boundary. The eventual beginner
action and prose remain unimplemented and require their own focused browser
test.

### Alpine activation contradiction

A direct render of a component whose template contained only `x-data`,
`@click`, and `x-text` produced the button and its Citry render attribute, but
no `data-citry-graph` marker and no Alpine or Events runtime. Adding a
component `js` block with
`$component(({ scope }) => { scope.count = 0; })` emitted the graph and inline
runtime; the focused Chromium lifecycle check above passed.

This contradicts the current Alpine runtime page's broad statement that Alpine
directives activate Citry's client graph. The Stage 4 journey therefore treats
`$component` as the verified beginner activation path and records the existing
claim for correction or a product behavior decision before the affected user
pages are reused.

### Focused research checks

The Stage 1 through Stage 3 validator failure-path tests and the Stage 3 pilot
content checks were repeated after the design edits:

```sh
uv run --no-sync pytest \
  docs/design/docs_content_research/test_validate.py \
  docs_site/tests/test_content_pilot.py \
  -q
```

Result: 26 passed.

The concurrent Events work advanced again during review. A repeated Django
Events run passed 12 tests, and the combined FastAPI/Django parity and route
run passed 130 tests. Repeating the full 402-test focused set then produced
399 passes and three failures: one ownership-manifest assertion still expected
the earlier `graph` field, and the existing counter and form Chromium journeys
did not send or complete a server action. This supersedes the intermediate
391-pass, 11-failure count as a later observation, while retaining it as
evidence that the inputs changed during the review.

The Events client bundle was then regenerated concurrently. The research
validator caught its changed size and hash during capture instead of accepting
the racing snapshot. A targeted post-generation run showed the counter journey
passing; the form journey sent its request but did not display the expected
field error, and the ownership-manifest assertion still expected the earlier
`graph` field. This is the latest focused browser observation before the
repository-wide gate.

The remaining failures are outside the documentation-only edits and confirm
that the continuous tutorial fixture must wait for a stable, green Events wire
and browser baseline. The host and route unit evidence is green at close; the
form browser path and one cross-manifest expectation are not. The counter path
is green after regeneration.

The required repository-wide gate was then started with:

```sh
python scripts/check.py --reporter agent
```

The checker reached its root pytest and coverage phase with Chromium active,
then remained asleep inside the browser run for about 19 minutes without
output or a checker-level timeout. Process inspection showed the checker,
pytest, Playwright driver, and Chromium all idle. The run was interrupted
cleanly rather than reported as a pass. It produced no phase summary. The
research-specific checks above remain green, but the repository-wide gate is
incomplete against this concurrent Events snapshot.

### Stage 4 close

The independent adversarial review first rejected the journey because page
jobs and prerequisites were implicit, the host and Event path appeared both
required and optional, and the stateless Event boundary lacked a browser
proof. It also found conflicting ownership for editor setup. The repaired
artifact now includes a page gate matrix, an explicit six-page shared path and
optional server branch, canonical navigation placement, the stateless browser
check above, and one explicitly open user-facing Editor setup owner. The final
adversarial pass reported no blockers.

Safe capture accepted 451 Stage 1 input fingerprints, including the new Stage
4 artifact and the four reconciled changes listed above. The complete content
research validator then passed twice.

The repository-wide gate was run after the final design review:

```sh
python scripts/check.py --reporter agent
```

Result: every phase passed. This included Cargo formatting, Clippy, Cargo
tests, Ruff check and formatting, mypy, Pyright, the Citry client checks, the
root pytest and coverage phase, and repository validators.

## Stage 4 maintainer revision: required server journey

The maintainer rejected the optional server branch. The revised Getting
started design now keeps all twelve pages under **Docs > Getting started** and
uses FastAPI as one explicit teaching host. The continuous path covers the
standalone component model, Alpine and `js_data()`, browser props and handlers,
FastAPI mounting, a stateless Event, signed State, a typed form, and a targeted
server-rendered update. **Docs > Guides > Web frameworks** remains the owner of
equivalent setup for other hosts.

Fragments stay near the end, where the reader can see Python-rendered HTML
replace a chosen region and then follow links to the full fragment contract
and other handler-return actions. This revision supersedes the six-page shared
path and optional server branch described in the earlier Stage 4 close. It
changes only research and design records, not the reader-facing Getting
started pages or product code.

### Plain Alpine runtime probe

The current source gate was traced through
`citry/ownership_manifest.py::ownership_manifest_required`,
`prepare_ownership_manifest`, and the Events dependency emission path. The
current graph triggers include `$component`, component-tag client bindings,
Events, State, client ambient-context magics, and Alpine directives in a
template-authored slot fill. Plain Alpine attributes in an ordinary component
template are not a trigger.

A focused Chromium probe serialized the same `AlpineOnly` component by itself
and beside an unrelated component whose JavaScript registered an empty
`$component` callback. It then read the button, clicked it, and read it again:

```text
plain_only graph=False runtime=False before=fallback after=fallback
with_unrelated_trigger graph=True runtime=True before=0 after=1
```

This proves the contextual failure: the plain Alpine component is inert by
itself and becomes interactive when an unrelated component causes the global
runtime to start. The result supports the maintainer's proposed product change.

An independent source audit found that the trigger must cover actual rendered
`x-*`, `@*`, and `:*` attributes, not only names beginning with `x-`. It also
found that template-source detection would miss dynamic `c-*` attributes,
`c-bind` mappings, selected control-flow output, slots, `on_render()`
replacements, fragments, and cache replay. The current string regex can also
match code text, comments, script strings, and ordinary attribute values, so
the implementation should use an actual settled start-tag attribute scan.

The revised design recommends making such output a full client-graph seed for
the owning component. A global-runtime-only path would make component
isolation depend on which unrelated feature loaded Alpine. This is a design
decision, not implemented behavior. Before code changes, it needs a separate
implementation plan and reconciliation with the client-graph protocol and
Alpine design, including detached slot content, nested boundaries, fragments,
cache replay, `simple` and `ignore` dependency strategies, users who currently
load Alpine separately, and payload cost.

### Concurrent Events baseline invalidation

Safe fingerprint preview also reported changes to eight Events implementation
inputs after the earlier 451-input Stage 4 close:

- `actions.py`;
- `codecs.py`;
- `dispatcher.py`;
- `emission.py`;
- `errors.py`;
- `openapi.py`;
- `results.py`;
- `routes.py`.

The current action, State, form, host, route, graph, and browser checks were
therefore repeated instead of carrying the earlier pass forward:

```sh
PYTHONPATH=. uv run --no-sync pytest -q \
  packages/py/citry/tests/test_ownership_manifest.py \
  packages/py/citry/tests/test_events_actions.py \
  packages/py/citry/tests/test_events_dispatch.py \
  packages/py/citry/tests/test_events_emission.py \
  packages/py/citry/tests/test_events_host_parity.py \
  packages/py/citry/tests/test_events_routes.py \
  packages/py/citry/tests/e2e/test_events_pitch_e2e.py::test_counter_click_increments_through_the_server_and_morphs_the_button \
  packages/py/citry/tests/e2e/test_events_pitch_e2e.py::test_contact_form_shows_the_422_field_inline_and_a_corrected_submit_succeeds
```

The focused run collected 402 tests: 391 passed and 11 failed. Failures showed tests and
fixtures still using earlier wire fields such as `stateToken`, `sendSequence`,
and `handlerName`, while the current implementation required fields such as
`componentClassId` and rejected the old shapes. The two selected Chromium
journeys did not send or complete their server calls under this mixed state.

These failures were not caused by the documentation-only revision, but they
invalidate the earlier green Events baseline for current-source authoring. The
journey remains a proposed design. No server-backed Getting started page may
claim an executable current path until the concurrent protocol work and its
tests agree, and the eventual continuous FastAPI fixture passes its own focused
and end-to-end checks.

### Revision review and research checks

A fresh independent adversarial review initially rejected three details: an
alternate-host rejoin contradicted the required FastAPI journey, the proposed
browser checkpoint used `$component` and could not detect missing plain-Alpine
activation, and detached Python slot content had no decided activation scope or
unmounted-fragment failure. The repaired design removes the host substitution,
requires a separate plain-Alpine-only browser regression, and defines the
component-authored, template-fill, and detached-content scope outcomes. It also
keeps the existing missing-route error for an unmounted fragment that now needs
the runtime.

The final independent pass reported no blockers. It also checked the revised
State lesson: the handler dispatches the visible value while Citry refreshes
the signed State token, so the design does not claim that a token-only response
updates public `$state` values.

The research validator failure-path tests and Stage 3 pilot content checks
remain green after the revision:

```sh
uv run --no-sync pytest -q \
  docs/design/docs_content_research/test_validate.py \
  docs_site/tests/test_content_pilot.py
```

Result: 26 passed.

## Getting started authoring: Install Citry

The first accepted Getting started slice rewrote
`docs_site/content/getting-started/installation.md` without changing its public
URL. Its page title and navigation label are now action-led: **Install Citry**.
The page teaches one path through a virtual environment, installs the `citry`
package with the selected interpreter, executes one complete component, and
hands the reader to **Your first component**.

The source audit verified that the current package and main CI matrix support
CPython 3.10 through 3.14, `citry` installs `citry-core` automatically, and a
plain component renders without a mounted web framework. The published PyPI
metadata reported Citry 0.2.0 with `requires-python` `>=3.10,<4.0` and
`citry-core>=1.3.0` on 2026-07-26.

Two isolated install probes checked the prerequisite and success path. The
first accidentally used the system's Python 3.9.6 and pip correctly reported
that no compatible Citry distribution was available. The repeated probe used
CPython 3.13, created a new virtual environment, installed the published
package, and rendered an HTML paragraph containing `Hello from Citry!`. This
supports stating the finite Python range before the install command.

The page intentionally removed generated component-ID mechanics,
`CitryElement` lifecycle detail, the `template_data()` lesson, CLI inventory,
and FastAPI mounting. Their owners are Rendering, Use data in a component,
Command line, and Serve the page with FastAPI. The inline proof remains on its
single consumer page rather than creating a one-use snippet.

The new `docs_site/tests/test_getting_started_content.py` extracts and executes
the exact `citry` fence, checks only meaningful output rather than the generated
attribute value, verifies the page's headings, navigation label, and links, and
guards against the displaced topics returning. The focused checks were:

```sh
uv run --no-sync pytest -q \
  docs_site/tests/test_getting_started_content.py \
  docs_site/tests/test_nav.py \
  docs_site/tests/test_pipeline.py::test_content_index_renders \
  docs_site/tests/test_guards.py
uv run --no-sync ruff check docs_site/tests/test_getting_started_content.py
uv run --no-sync ruff format --check docs_site/tests/test_getting_started_content.py
```

Result: 32 tests passed, and both Ruff checks passed. The strict docs build
also completed with all guards passing:

```sh
uv run --no-sync python -m docs_site build-check --strict
```

A normal build also produced the revised page at
`site/getting-started/installation/index.html`, its Markdown companion, its
navigation entries, and revised entries in `llms.txt` and `llms-full.txt`.
Inspection confirmed that all four reader projections use the new title,
description, proof, and handoff.

The full docs and examples suite was also attempted:

```sh
uv run --no-sync pytest -q docs_site/tests docs_site/examples
```

The first run produced 342 passes and one failure: the golden snapshot for
`getting-started/your-first-component.md` had not been regenerated after its
accepted CSS revision. The review-required prerequisite correction also
changed that page's rendered HTML. The one Card snapshot was regenerated from
the accepted source, reviewed as generated output, and the complete command
was repeated. Final result: 343 passed with one Starlette deprecation warning.

A fresh adversarial review caught stale generated projections, incomplete
research fingerprints, the misplaced evidence section, the bare `pip` command
on the next page, missing Windows launcher guidance, and two false-pass risks
in the page test. These findings were repaired before the slice closed.

The safe fingerprint preview showed the expected Install Citry design,
research, navigation, page, Card-prerequisite, and test changes. It also showed
concurrent changes to the three Events and migration pages, the
`migrate_unicorn.py` snippet, the Events cache, codecs, dispatcher, emission,
errors, results, and tokens modules, and the generated Events client. Reader
evidence separately saw the concurrent change to `test_events_host_parity.py`.
The preceding Events observations record the corresponding parity, route, and
browser reruns. The fingerprint updates accept these as the current shared
workspace baseline; they are not attributed to Install Citry.

The same independent reviewer checked the repaired slice again and reported
no remaining blocker. Its focused page tests, strict docs build, and research
validator all passed.

The required repository-wide gate then passed every phase:

```sh
python scripts/check.py --reporter agent
```

This included Cargo formatting, Clippy, Cargo tests, Ruff check and formatting,
mypy, Pyright, the Citry client checks, root pytest and coverage, and repository
validators.

## Getting started authoring: complete twelve-page wave

The maintainer narrowed Install Citry after its first slice. The current page
does not teach virtual environments or reassure readers about unrelated build
tools. It offers both `python -m pip install citry` and `uv add citry`, keeps one
render proof, and sends readers to the Card. This decision supersedes the
earlier Install Citry notes above where they describe a virtual-environment
lesson.

The rest of the accepted journey was authored in order:

- Use data in a component;
- Build a page from components;
- Add flexible content;
- Add browser behavior;
- Connect components in the browser;
- Serve the page with FastAPI;
- Call Python from a click;
- Events state;
- Handle and validate forms; and
- Replace part of the page from Python.

The first three pages were rendered from their complete copyable files. Their
observed results matched the stated list, parent-child composition, named-fill,
and fallback behavior. A first composition attempt used the HTML-style name
`empty-message`; the parser correctly rejected it because component fields use
their declared Python name. The authored file uses `empty_message` and passed.

The FastAPI half derives from seven executable files under
`docs_site/snippets/getting_started/`. Ruff check and formatting pass on every
file. Isolated imports rendered every step. FastAPI's `TestClient` returned 200
for both `/` and `/citry/citry.js`.

A real Uvicorn server and Chromium then exercised the completed application.
Two clicks reached Python and displayed State values one and two; reloading the
page reset the value to zero. Submitting `ada@elsewhere.test` produced the
expected HTTP 422 and field message while preserving the input. Submitting
`ada@example.com` replaced only `#signup-result`; the form remained, the
confirmation JavaScript changed its status, and its fragment-delivered CSS
produced the expected green border. This flow now has permanent coverage in
`docs_site/tests/e2e/test_getting_started_journey_e2e.py`.

The old Adding JS and CSS and Adding dependencies pages left the required
journey. Their useful editor, asset, dependency, execution, and inheritance
material moved to the accepted Advanced owners, and internal links use the
canonical destinations.

Focused verification after the content cutover was:

```sh
uv run --no-sync python -m docs_site build-check --strict
uv run pytest -q \
  docs_site/tests/test_redirects.py \
  docs_site/tests/test_getting_started_content.py \
  docs_site/tests/test_content_snapshot.py \
  docs_site/tests/test_guards.py
uv run pytest -q docs_site/tests/e2e/test_getting_started_journey_e2e.py
```

The strict build reported no findings. The focused non-browser group passed 44
tests, and the completed server journey passed its Chromium test.

The browser-only pages are not yet closed. The concurrent Alpine activation
work has added settled-output detection to the shared tree, but a component
whose own template contains only ordinary `x-*`, `@*`, or `:*` attributes still
serialized without the Citry runtime at this observation point. Add browser
behavior must not be accepted until its exact plain-Alpine example works in a
browser without an unrelated `$component`, Events, or State trigger.

## Getting started adversarial review and intermediate coverage

An independent review of all twelve pages found four material gaps. The `uv`
command assumed a project that the page had not named, the page-composition
check assumed pytest without installing it, the FastAPI step dropped the
browser component from the preceding lesson, and permanent coverage exercised
only the completed server app rather than each intermediate source file.

The repaired journey now qualifies `uv add` as an existing-project command and
uses a plain Python assertion for the early render check. The choice button and
picker continue into FastAPI and remain on the page while Events, State, the
form, and the fragment update are introduced. Short prerequisite links make
each later server page usable as a direct search landing. Server results use
live-region semantics, the disclosure creates a unique panel ID for every
render and uses `x-cloak`, and the first form success message stays hidden
until there is a complete result to announce.

Every server source from step 8 through the completed app now receives an
isolated FastAPI `TestClient` check for the page and Citry runtime. Chromium
coverage separately proves the standalone page-7 client prop and relocated
handler, the page-8 browser interaction over HTTP, the page-9 stateless
Dispatch, the page-10 two-call State path and reload reset, the page-11 error
and corrected success Dispatch, and the page-12 targeted fragment update.

The focused results after repair were:

```text
docs content, redirects, and pilot: 28 passed
standalone plus intermediate and completed Chromium journey: 3 passed
```

The reviewer reported no further blocker beyond the already-recorded plain
Alpine activation defect. That one gate remains owned by the concurrent
runtime implementation and is not hidden by any other tutorial behavior.

The subsequent strict build reported no findings, and the complete docs and
examples test run passed 366 tests. The closing authoring build contained 59
authored content pages, 80 indexed and sitemap pages, 79 links in `llms.txt`,
and 80 expanded bodies totaling 1,252,135 bytes in `llms-full.txt`.

The required repository-wide gate then passed every phase:

```sh
python scripts/check.py --reporter agent
```

Cargo formatting, Clippy, Cargo tests, Ruff check and formatting, mypy,
Pyright, the Citry client checks, root pytest with coverage, and the repository
validators all passed. A final execution of the exact disclosure source still
produced neither a client graph nor the Citry runtime. This confirms that the
remaining browser gate depends on the separate Alpine activation branch, not
on an untested or hidden trigger in the authored page.

## Verification policy reconciliation (2026-07-27)

The page-specific pytest commands above record how the authored wave was
checked at that time. They are not the ongoing contributor contract. The
adopted policy is for tests to cover reusable docs-site machinery with
synthetic inputs, while requirements for user-facing Markdown belong in
registered build guards that report the source page and line. Existing
content-coupled tests still need a separate migration to that policy.

The redirect statements above also predate publication. The moved-page
redirect map is empty, and the generic emitter and redirect guard remain ready
for the first published URL that moves.

`test_getting_started_content.py` contains only page-coupled assertions. It can
be removed after deciding whether executable examples remain mandatory. If
they do, the replacement is an opt-in executable-example guard rather than
another test tied to named pages or expected prose.

## Blog implementation addendum (2026-07-28)

The Blog implementation added two authored content sources and one generated
Atom surface to the inventory. A no-search, no-social-card, unminified
observation build reported 77 authored pages and produced 97 DocPage records,
96 `llms.txt` links, and 97 `llms-full.txt` bodies totaling 1,304,527 bytes.
Blog posts use their editorial date or update timestamp for sitemap `lastmod`,
so that metadata does not depend on a git history entry for a new source.

The focused implementation checks passed:

```text
strict docs build and guards: no findings
docs tests and examples: 457 passed
Chromium docs suite: 20 passed
content research validator unit tests: 23 passed
independent final Blog review: no material findings
```

The full content-research validator still reports the broader pre-existing
reconciliation as stale. It has 21 live page IDs without rows, four removed
page IDs, removed test locators, and many changed fingerprints from the active
content and runtime work. Before this addendum it also aborted at the first
removed page; it now reports that missing locator and continues through the
complete discrepancy list. The Blog-specific inventory rows, generated-surface
requirement, navigation expansion, and source fingerprints are recorded here
without silently accepting or recapturing unrelated baseline changes.

The repository gate passed Rust, typing, JavaScript, root pytest, and repository
validators. Its Ruff phases remain blocked by the unrelated untracked
`docs/design/docs_playground_research/runtime_proof/public_api_smoke.py` file,
which has 27 lint findings and is outside the Blog scope. All Blog-touched files
pass focused Ruff checking and formatting.
