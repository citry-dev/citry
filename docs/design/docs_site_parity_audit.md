# Docs site parity audit: citry vs django-components

This is the feature-by-feature audit that checks what the citry docs site (`docs_site/`) has *actually* ported from the django-components (DJC) custom docs site, against the 228-row inventory in [`docs_site_feature_inventory.md`](docs_site_feature_inventory.md). It was produced on 2026-07-02 by reading citry's real code (not its status claims) for every inventory row and recording the true state with `file:line` evidence. Regenerate it the same way when the code moves on; the inventory doc is the stable checklist, this doc is the dated snapshot of where citry stands against it.

## Headline

Of **228** inventory rows, **61** do not apply to citry (the Django project scaffold, the docstring codemods on django-components' own source, the mkdocs migration steps, the Django-shaped discovery ADT, and features citry's architecture makes moot, such as anchor-alias deprecation). That leaves **167** rows that are genuine citry work. A second-pass re-review (2026-07-03) re-checked every row against current code and split out two buckets that were previously hidden inside the totals: `adapt` (a citry-native version of a DJC-shaped feature is worth building) and `deferred` (applies to citry, but deliberately deferred). Workstreams A, B, C, D, E, F, G, H, and I have landed; only J (search v2 / landing) and the content-quality track remain, so these counts are a moving snapshot:

| Status | Count | Share of applicable |
|---|---|---|
| Ported | 147 | 88% |
| Partial | 4 | 2% |
| Missing | 7 | 4% |
| Adapt | 1 | <1% |
| Deferred | 8 | 5% |
| (Not applicable) | 61 | - |

The site's infrastructure is in strong shape: the `<c-image>` / `<c-people>` directives, the `UserGrid` component, the seeded `data/people.yml`, the `docs_site/scripts/people.py` generator, the full nine-example gallery (including the fragments demo), and the git-metadata subsystem (per-page dates, authors, and the "edit on GitHub" link) all shipped. **Content coverage is now broad:** a per-file audit ([`docs_site_content_port_audit.md`](docs_site_content_port_audit.md)) found 18 of DJC's 52 content pages skipped; workstream A ported 17 of them as 16 new pages (community, dependencies, registration, subclassing, sharing, hooks, testing, troubleshooting, dev-server, compatibility, benchmarks) and dropped the 18th (`upgrading/v0`). **Phase 2 then enriched 12 partial pages** into 8 existing pages (typing, rendering, slots, provide/inject, extensions, the JS/CSS pages, and the home-page highlights). Cache Phase 5 subsequently ported `component_caching` into `advanced/caching.md`, so content coverage is now complete. The API-reference enrichers shipped too (workstream E: cross-linked signatures, base classes, per-symbol source links, external stdlib cross-refs, and the previously-dropped docstring example/note blocks). The other open gaps are the multi-version SEO plumbing and the polish/link workstreams (D, F through J below).

## What this corrects

Earlier session notes claimed "Phase 3b complete (25/25)" and "Phase 4 full parity." Both were overstated. The content-port row (3b.25) was only ~10% done when this audit was written; workstream A has since closed the skipped gap and enriched the 13 partial pages, so the content port is complete. Separately, several rows marked done in the inventory are **mechanism-only** in citry (the code path works but its data or its git-metadata input was never wired), and a handful of API-reference enrichers were never built. This audit replaces those claims with per-row evidence. The lesson that prompted it - features tested only in isolation shipped broken - is now guarded by a browser e2e suite ([`docs_site/tests/e2e/`](../../docs_site/tests/e2e/)) that builds the real site and drives it in Chromium, plus two features that had been dropped in the port and were restored: the table-of-contents fix ([`docs_site/_internal/toc.py`](../../docs_site/_internal/toc.py)), and whole-heading permalinks ([`docs_site/_internal/links.py`](../../docs_site/_internal/links.py) `linkify_headings`) so content and reference-symbol headings link to their own anchors (`.heading-anchor`; the CSS was already present).

## Remaining work, grouped (workstreams; the roadmap)

The missing and partial rows cluster into coherent workstreams, each with its inventory IDs. **A, B, C, D, E, F, G, H, and I are done; only J (search v2 / landing) and the content-quality track (Phases 7-9) remain.** Each open item is annotated so another session can pick it up cold. The per-file content-port enumeration (which DJC content pages were ported, adapted, dropped as Django-specific, or wrongly skipped) is in [`docs_site_content_port_audit.md`](docs_site_content_port_audit.md).

**How to resume a workstream.** Read the [porting principle](docs_site.md) in the design doc first, then the workstream's **Start here** (the DJC source that already solved it); port that shape and change only the citry-specific parts. Gate every change with `python -m docs_site build-check --strict`, `pytest docs_site/tests`, and the browser e2e (`pytest docs_site/tests/e2e --browser chromium`).

Each open workstream carries: **Effort** (S = up to a day, M = 1-3 days, L = more), **Depends** (any prerequisite), **Parallel** (whether it fans out into independent sub-items, and whether it is safe to run concurrently with other workstreams given the files it touches), and **Start here** (the DJC source to port from). See "Parallelization at a glance" after workstream J for the concurrency map.

### A. Content port (done)

The getting-started / template-syntax / core-concept scaffold shipped (27 pages), replacing the five earlier ones. Workstream A then closed every content gap in two passes (2026-07-03). **Phase 1** ported 17 of the 18 skipped DJC pages as 16 new citry pages (community: ai-bot-policy, code-of-conduct, contributing, development, help, license; advanced: hooks, testing, sharing components; concepts: registration/autodiscovery, subclassing; getting-started: adding dependencies; guides: troubleshooting, dev-server; about: compatibility, benchmarks); `upgrading/v0` was dropped. The code-of-conduct and license pages render the repo-root files inline via `--8<--`. **Phase 2** enriched the 12 real partial pages into 8 existing target pages (typing-and-validation, rendering, slots, provide-and-inject, extensions, adding-js-and-css, js-and-css-dependencies, index). Cache Phase 5 later ported `component_caching` into `advanced/caching.md`. Every addition was authored from its DJC source, verified against the real citry source, render-checked, and diffed against the pre-edit page so nothing existing was lost.

Rows: `3b.7` (community section, ported), `3b.25` (content sweep + all pages, done).
**Status:** done. The per-file record (what each page kept, added, or dropped) is in [`docs_site_content_port_audit.md`](docs_site_content_port_audit.md). Content quality (Diataxis rewrite, docstrings, a citry Pygments lexer) is tracked separately as the content-quality track below.

### B. Custom directives, generator, and examples (done)

The `<c-image>` and `<c-people>` tags (each in its own file under `docs_site/_internal/components/`, beside the component it renders), the `UserGrid` component, the seeded `data/people.yml`, and the `docs_site/scripts/people.py` generator (which merges Citry and django-components contributor counts) all shipped, and the Examples cookbook grew from one to nine Citry-native demos. Two needed special handling and got it: form submission simulates its server POST client-side, and the fragments demo pre-renders each variant below `examples/fragments/demo/<variant>/` and writes the fragment component's class-level dependency files. The fragments path is verified in a browser (`test_docs_e2e.py`). The release-notes generator (`3b.5`) shipped too (see below).

Rows: `1.15` (done), `3b.6` (done), `2.2` (done), `2.3` (done), `3b.5`.
**Done:** `3b.5` shipped. `docs_site/_internal/release_notes.py` parses CHANGELOG.md into a `/releases/` index plus one page per version (the per-version split mirrors DJC), wired into the build and dev server with a "Release notes" nav entry. Release prose *shows* citry syntax (e.g. `<c-raw>` in backticks), so the pages render with `render_page(..., run_citry_pass=False)` to display it rather than execute it. Covered by `docs_site/tests/test_release_notes.py`.

### C. Git-metadata subsystem (done)

`git_metadata.py` (ported from DJC) reads each source file's git history for its creation date, last-updated date, and recent authors, plus `edit_url_for`. `render_page` feeds the dates/authors/edit-link to `DocPage` (footer + TechArticle `datePublished`/`dateModified`), and `seo.write_sitemap` emits `<lastmod>`. The deploy workflow checks out with `fetch-depth: 0` so the dates are accurate. Browser-verified (`test_docs_e2e.py`).

Rows: `5c.1` (done), `5c.8` (done), `5c.16` (done)

### D. Multi-version SEO and build plumbing (done)

Done 2026-07-03. Old `/v/<version>/` snapshots are now kept out of search: robots.txt disallows every version outside the newest two + `latest` (`5c.2`), and an assemble-time pass sets `noindex,follow` + canonical-to-current on old-version pages (`1.26`/`1.27`/`6.12`, net-new since DJC deferred this half). Two version guards (`versions_manifest` + `cross_version_link`) plus a `versions-check` command cover manifest/filesystem integrity (`5b.13`/`5b.14`/`5b.15`). And the release plumbing landed: a git-free `build-all` core + git-worktree machinery (`5b.8`/`5b.9`), a `docs_versions.yml` config (`5b.12`), and a `repo--docs-release.yml` workflow (`5b.16`) that on a `citry@X.Y.Z` tag builds that version, runs `versions-check`, commits `versions/<v>/`, and deploys.

**Needs a real release to validate end-to-end** (the worktree build and the CI can't run locally): commit-back token/permissions, the `citry@` tag-prefix handling, and the committed-vs-artifact choice are called out in the workflow header.

Rows: `5c.2`, `6.12`, `1.26`, `1.27` (done), `5b.8`, `5b.9`, `5b.12`, `5b.13`, `5b.14`, `5b.15`, `5b.16` (done).

### E. API-reference enrichment (done)

Landed 2026-07-03. Signatures, parameters, returns, and attributes now cross-link their types: an internal type links to its reference page and a stdlib type links to docs.python.org (via `docs_site/_internal/inventory.py`, which parses Python's `objects.inv` and is offline-safe so a build never fails when the network is down). Every class shows its base classes (resolved from the runtime type, since griffe's static bases are empty for citry), every symbol carries a "View source" link into GitHub (`git_metadata.source_url_for`), and docstring `Examples:` and admonition sections that the text-only renderer used to drop now render. The implementation is in `docs_site/_internal/annotation.py`, `reference.py`, `crossrefs.py`, and `components/reference_symbol.py`, with observed-and-locked tests in `tests/test_reference_enrichers.py`.

Rows: `4.18` (done), `4.19` (done), `4.20` (done), `4.21` (done), `4.36` (done), `4.40` (done), `4.61` (done), plus the related `4.23` / `4.35` / `4.39` partials now closed. **`4.30`** (the extension-hook "Available data" table) was **deferred by decision**: citry already renders all 18 hook-context classes as first-class reference symbols on the Extensions page, so an inline per-hook table would duplicate them one screen away, and two contexts (`OnFilesReset`, `OnDependencies`) have no base-`Extension` hook to attach to. Build it only if hook-reading locality is wanted.

### F. Mechanisms present but data/entries empty (done)

Done 2026-07-03. The indexing manifest (`5c.11`) now lists every recorded doc page including noindex ones and records each page's real robots directive. The redirect emitter (`5c.17`) needs no data: citry is a fresh package with no moved URLs, so `REDIRECTS` stays empty by design until a real page rename happens (the emitter was already correct).

Rows: `5c.11` (done), `5c.17` (correctly empty).

### G. Chrome and SEO polish (done)

Done 2026-07-03. The 404 page (`5a.6`) now has a "Search the documentation" button (opening the shared search modal), four popular destinations, and an issue link; the header (`5d.2`) shows GitHub + PyPI + Discord social icons; google-site-verification (`5d.3`) is a config-driven meta tag; and a strict front-matter validator guard (`1.22`) is wired into build-check --strict.

Rows: `5a.6` (done), `5d.2` (done), `5d.3` (done), `1.22` (done).

### H. Link handling and external checks (done)

Done 2026-07-03. Internal `.md` link rewriting (`1.31`, new `links.py` wired into the pipeline) and per-page `.md` companion files (`1.28`, written from `markdown_body`) shipped as build code. The external-link (`5c.19`) and lighthouse (`5c.13`) checks are ported as `repo--docs-*` CI workflows; both need a first real Actions run to confirm before they gate anything (kept non-blocking / out of branch protection until then). The anchor-deprecation check (`5c.12`) is N/A: citry has no legacy anchor aliases to deprecate.

Rows: `1.31` (done), `1.28` (done), `5c.19` (done, CI unverified), `5c.13` (done, CI unverified), `5c.12` (n/a).

### I. Validation and test scaffolding (done)

Done 2026-07-03. A dependency-free content-HTML snapshot regression test (`3b.17`, golden files over 3 representative pages' content HTML) and the completed example-contract check (`2.7`, the per-example `test_example_*.py` requirement plus a test for each of the 9 examples; the nested-View check is N/A for citry). Test-only, so no runtime surface changed.

Rows: `3b.17` (done), `2.7` (done).

### J. Future phases (DJC itself may not have shipped these)

Search v2 (autocomplete, recent searches, scoping filters, typo recovery), search analytics, and a full hero/features/CTA landing page. Lowest priority; build when actually wanted.

Rows: `7.1`, `7.2`, `7.3`, `7.4`, `8.1`, `9.1`.
**Effort** L, lowest priority. **Parallel** independent (search v2 lives in `search.js` + the Pagefind config; the landing page is a new component). **Start here** no DJC parity source for most of these; build when actually wanted.

## Parallelization at a glance

**Run concurrently in separate sessions/branches** (they touch disjoint files, so little merge risk): **H** (a new `links.py` + new workflows), **I** (tests only), **J** (search/landing), and, from the content-quality track below, **Phase 9** (docstrings live in `packages/py/citry/`, a different package entirely) and **Phase 7** (only `content/*.md`). (**E**, the reference subsystem, was one of these and is now done.)

**Keep on one branch and sequence, or split carefully by function** (they share `seo.py` / `build.py` / `doc_page.py`): **D**, **F**, **G**, and H's `build.py` touch. Two agents editing the same module concurrently is the one real conflict risk here.

**Best workflow fan-outs** (one session, one subagent per sub-item): **G** (four polish items), **H** (five items), **Phase 7** (per page), **Phase 9** (per symbol/module). **D**, **F**, and **I** are small and cohesive, so a fan-out buys little.

With **E**, **F**, and **G** done, the remaining open workstreams are **H** (link handling + external checks) and **I** (validation/test scaffolding). **D** waits on versions; **J** waits on demand.

## Content-quality track (separate from the parity rows)

Beyond the parity rows above, the design doc [`docs_site.md`](docs_site.md) tracks three quality phases over content that is already ported and accurate, so they do not appear in the inventory:

- **Phase 7 - Diataxis content rewrite:** a deliberate writing pass over the ~29 pages (reader personas, per-page tone, progressive disclosure, short titles, the code-block formatting conventions). The biggest quality lever; fans out per page.
- **Phase 8 - citry Pygments lexer:** done. The `pygments-citry` package ships a `citry` Pygments lexer that highlights the HTML/JS/CSS embedded in `template`/`js`/`css` strings (and the `<c-*>` tags and `{{ }}` interpolation), not flat Python. The docs build loads it at startup, component code fences use ```` ```citry ````, and a `component_fence` guard keeps them from regressing. See [`pygments_citry.md`](pygments_citry.md).
- **Phase 9 - public API docstring pass:** rewrite the docstrings griffe renders into the reference pages in the Phase 7 spirit; fans out per symbol.

## Full per-feature status

Every inventory row with citry's real status. `n/a` = does not apply to citry (DJC-repo-specific); `adapt` = the DJC feature is Django-shaped, but citry has its own analog and a citry-adapted version is worth building. Evidence for each is in the audit run; the one-line note here is the summary.

The **Re-verified** column records a second-pass re-review (2026-07-03) that re-checked each row against the current code (the original evidence predates a refactor that split `directives.py` into `components/*.py`). `✓` marks a status confirmed this pass; `⟳ X→Y` marks a status change; a parenthetical flags a re-grounded evidence pointer or a corrected note. Every changed or promoted row was adversarially double-checked.

### Phase 0 (pre-work codemods) + Phase 1 (foundation: pipeline, DocPage MVP, directives)

<details>
<summary>Phase 0 + Phase 1 group</summary>

| ID | Status | Feature | Re-verified | Note |
|---|---|---|---|---|
| 0.1 | n/a | codemod-links (hand-typed link sweep `[X](api.md#...)` -> `[X][Key]`) | ✓ n/a confirmed | django-components source codemod (its own hand-typed links); citry has none to sweep. The bracket-ref adoption it implies for citry docstrings is tracked by 4.41. |
| 0.2 | n/a | codemod-google-sections (**Args:** -> Args:) | ✓ n/a confirmed | django-components source codemod; citry's own docstrings are already Google-shaped, so nothing to sweep. The convention itself is captured by 0.3/0.4. |
| 0.3 | done | docs-convention-community | ⟳ was adapt → done (built since) | Added a "Writing docstrings" section to `community/development.md`: Google-style sections (Args renders as Parameters, plus Returns/Raises/Attributes/Example) and the [`Text`][citry.Symbol] cross-ref form the griffe reference resolves, documented as the going-forward convention (source docstrings are not converted yet, which is 4.41). |
| 0.4 | done | docs-convention-claude | ⟳ was adapt → done (built since) | Added a terse "Public docstrings become the API reference" rule to CLAUDE.md (one-line summary, Google sections, [`Text`][citry.Symbol] cross-refs on a real `citry.*` path), pointing at the development.md section for the full how-to. |
| 1.0a | n/a | docs-old-rename (rename docs/ -> docs_old/, repoint mkdocs/config) | ✓ n/a (latent) | mkdocs migration scaffolding step; N/A to citry. |
| 1.1 | n/a | docs-site-django-project (Django project scaffold: settings, urls, wsgi, manage.py) | ✓ n/a confirmed | Django-specific scaffold; citry uses a plain config dataclass + CLI (cli.py) instead. |
| 1.2 | n/a | docs-app-scaffold (apps/docs/ with components/, templatetags/, management/commands/) | ✓ n/a confirmed | Django app scaffold; citry keeps the builder in `docs_site/_internal/`. The FUNCTIONAL equivalents exist and are audited under their own Phase 1 rows. |
| 1.3 | done | content-dir-structure (move user-facing pages -> content/) | ✓ done (note de-staled) | content/ is populated (getting-started/, concepts/, syntax/, advanced/, guides/) and built. |
| 1.4 | n/a | examples-dir-moved (move examples -> examples/) | ✓ n/a confirmed | Deferred to Phase 6 per the inventory; not a Phase 1 deliverable. |
| 1.5 | done | pygments-djc-loader (load the citry lexer at command startup) | ⟳ was MISSING → done (built since) | citry loads its own lexer: `import pygments_citry` at the top of `docs_site/_internal/pipeline.py` registers the `citry` fence lexer (the `pygments-citry` package) before any highlighting runs. Component code fences use ` ```citry `, which highlights the HTML/JS/CSS embedded in `template`/`js`/`css`. The `component_fence` guard warns if a component slips back into a ` ```python ` fence. See [`pygments_citry.md`](pygments_citry.md). |
| 1.6 | done | fence-protection-scanner (wrap code regions before the template pass) | ✓ | Equivalent role; wrapper changed from {% verbatim %} to <c-raw> because citry parses <c-*> tags, not {% %}. |
| 1.7 | done | markdown-pipeline-pass1 (template engine on markdown source) | ✓ | Ported: the engine is citry, not Django. Directive tags are citry Components (transparent), version/site_name are citry template globals. |
| 1.8 | done | markdown-pipeline-pass2 (python-markdown + pymdownx -> HTML) | ✓ | Copied verbatim from upstream; Django-independent. Deliberately repo-root-only snippet base_path (case-insensitive-FS guard). |
| 1.9 | done | markdown-pipeline-pass3 (wrap in DocPage layout) | ✓ | Ported as a citry Component render instead of a Django template include. |
| 1.10 | done | doc-page-component-mvp (minimal DocPage, full head block) | ✓ | Over-delivered: DocPage already has full chrome (the Phase 3a target), not just the Phase 1 stub. |
| 1.11 | done | slug-algorithm (Material-compatible heading slug = python-markdown DEFAULT toc slugify) | ✓ | Ported by matching the corrected default-slugify contract. |
| 1.12 | done | code-fence-info-string-parser (parse fence headers title=/hl_lines=) | ✓ | Provided by the pymdownx extension set copied verbatim; same behavior as reference. |
| 1.13 | done | include-file-tag ({% include_file %} template tag) | ✓ evidence → docs_site/_internal/components/include_file.py | Ported as a citry <c-include-file> directive. Minor lexer-name deviation vs reference (.sh -> 'sh' in citry vs 'bash' in reference; both valid Pygments aliases). |
| 1.14 | done | version-tag ({% version %} template tag) | ✓ stale 'test FAILS' caveat removed | Ported via the `{{ version }}` global, not a tag. test_pipeline.py::test_content_index_renders now passes (it runs configure_docs_globals first). |
| 1.15 | done | image-tag ({% image %} template tag, optional sugar) | ✓ evidence → docs_site/_internal/components/image.py | Ported as the `<c-image src alt width css_class />` directive, faithful to the upstream image() markup; tested in test_content_render.py. |
| 1.16 | done | pygments-light-stylesheet (light-mode Pygments theme CSS) | ✓ | Ported; linked unconditionally in the head. |
| 1.17 | done | pygments-dark-stylesheet (dark-mode Pygments theme CSS) | ✓ | Ported; linked unconditionally, theme-scoped via CSS. |
| 1.18 | done | uv-scripts-entrypoints (wire docs-serve / docs-build / docs-test) | ✓ | Ported as an argparse CLI (cli.py) with subcommands build / serve / build-check / serve-built / assemble, instead of uv-script/management-command entrypoints. |
| 1.19 | done | docs-serve-command (dev-loop runserver wrapper; live render of content/*.md) | ✓ | Ported; URL<->path mapping shared with the build in paths.py as in the reference. |
| 1.20 | done | docs-build-command-mvp (build current version to output, no manifest) | ✓ | Over-delivered relative to the Phase 1 no-manifest MVP; manifest/versioning (Phase 5b) is already present. |
| 1.21 | done | docs-test-command-mvp (post-build link validator) | ✓ | Ported as guards rather than a standalone command, matching the reference's later consolidation. |
| 1.22 | done | front-matter-schema (codified spec + validator) | ✓ done | Done (workstream G): `docs_site/_internal/guards/frontmatter.py` validates every content page against the `PageMeta` schema (derived via `get_type_hints` so it cannot drift) - an unknown key warns, a bad-typed `noindex`/`searchable`/`boost` errors - wired into build-check --strict. All 46 real pages pass. |
| 1.23 | done | docpage-head-block (unified head: title, description, canonical, viewport, favicon, robots, alternate...) | ✓ | Ported. rel=alternate points at /llms.txt; theme-color is not explicitly emitted (minor vs the inventory's field list). |
| 1.24 | done | page-titles (<Page Title> - Citry formatting) | ✓ | Ported; suffix is 'Citry' not 'Django-Components' (correct rebrand). |
| 1.25 | done | per-page-descriptions | ⟳ was partial → done (built since) | All three tiers shipped: front-matter description, else the first body paragraph (markdown-stripped, ~155-char cap, skipping admonitions/version notes) in `frontmatter.py`, else `config.default_description` applied at render. A page with no front-matter description now emits meta/OG/Twitter descriptions. Tests in `test_frontmatter.py`. |
| 1.26 | done | canonical-urls (versioned pages canonical to /latest/ counterpart) | ✓ done | Done (workstream D): an assemble-time pass rewrites old `/v/<ver>/` pages' `<link rel=canonical>` to the current (root) counterpart URL (or the site home when a page has no current counterpart). Net-new since DJC deferred this. |
| 1.27 | done | per-version-noindex (noindex,follow on non-current versions) | ✓ done | Done (workstream D): the same assemble-time pass sets `<meta name=robots>` to `noindex,follow` on every old-version page (versions outside the newest-2 + latest). |
| 1.28 | done | markdown-companion-urls (serve every page also at .../page.md raw markdown) | ✓ done | Done (workstream H): `build_site` writes a per-page `.md` companion (front matter + the expanded `markdown_body`) next to each content page's `index.html` at `.../index.md`, so the raw markdown is fetchable. Complements the aggregate llms.txt/llms-full.txt. |
| 1.29 | done | json-ld-breadcrumbs (BreadcrumbList JSON-LD on every page) | ✓ | Ported (and TechArticle too). Only emitted when canonical + title are set (home page correctly omitted). |
| 1.30 | done | placeholder-home-page (thin / placeholder) | ✓ | Ported; content/index.md is the home page. |
| 1.31 | done | internal-md-link-rewriting (rewrite [X](foo/bar.md) -> clean URL) | ✓ done | Done (workstream H): a new `docs_site/_internal/links.py` rewrites internal `[X](foo/bar.md)` links in the rendered HTML to clean relative URLs, run in the pipeline after the markdown pass. A no-op on today's content (which authors clean URLs; the only 3 `.md` links are external), but it enables the pattern. |

</details>

### Phase 2 (live-example feature) and Phase 3a (theme + core chrome)

<details>
<summary>Phase 2 group</summary>

| ID | Status | Feature | Re-verified | Note |
|---|---|---|---|---|
| 2.1 | done | example-autodiscovery | ✓ | Fully implemented and tested. Walks docs_site/examples/<name>/ for component.py + page.py, registers via importlib, finds the *Page class. Empty-dir case also tested (test_examples.py:63). |
| 2.2 | done | docs-example-convention (fragment-variant metadata) | ✓ | An example's component.py declares `FRAGMENTS = {variant: ComponentClass}` (examples.py ExampleInfo.fragments); the citry equivalent of DJC's `DocsExample.fragments`. Used by the fragments example. |
| 2.3 | done | fragment-pre-render | ⟳ was partial → done (built since) | Both paths work now. The static build pre-renders each variant to `examples/<slug>/demo/<variant>/index.html` and writes the dep files (`export_fragment_deps`); the dev server routes `/examples/<slug>/demo/<variant>/` (`serve.py` `serve_example_variant`) to the same fragment render, so `serve` supplies the fragment and the `/citry` mount supplies its JS/CSS. Browser-verified (`test_docs_e2e.py`) plus dev-server tests (`test_serve.py`). |
| 2.4 | done | example-card-component (tabbed code + render) | ✓ | CSS radio-button tabs driven by the shared `.tabbed-set` markup (`site.css`/`site.js`). The live-demo iframe points at `/examples/<slug>/demo/`. Distinct ids per card are tested. Citry uses an iframe `src`, not `srcdoc`; the standalone page owns its full document and assets. |
| 2.5 | done | example-tag (<c-example name>) | ✓ evidence → example_card.py:86 | The Django {% example 'name' %} simple_tag is ported to the citry <c-example name='...' /> directive. Unknown-example inline error handled (examples.py:100 example_not_found). |
| 2.6 | n/a | stable-example-ids-guardrail | ✓ n/a confirmed | DJC's guard failed a PR that renamed an examples/<name>/ dir, to freeze the example IDs; DJC dropped it as overly prescriptive. Not a citry gap: the example-contract guard (2.7) already flags a <c-example> that names a missing example. |
| 2.7 | done | example-contract-check | ✓ done | Done (workstream I): the guard now also requires each example dir to ship a `test_example_*.py`, and all 9 examples got one (each renders its page and locks an example-specific substring). The nested-View check is N/A (citry has no `Component.View`). CI collects the example tests via the docs-check workflow (not `testpaths`, so the packages gate is untouched). |
| 3a.1 | done | design-tokens-css (OKLCH tokens) | ✓ | Full OKLCH token file present and linked in the page head. |
| 3a.2 | done | light-theme-tokens | ✓ | Teal accent (Option A) as specced. |
| 3a.3 | done | dark-theme-tokens | ✓ | Both explicit data-theme=dark and the auto prefers-color-scheme fallback are present. |
| 3a.4 | done | theme-fouc-prevention | ✓ | Inline pre-paint theme script emitted in the head, keyed on djc-theme (same key as site.js). |
| 3a.5 | done | inter-font-link | ✓ | Self-hosted variable font, not CDN. |
| 3a.6 | done | prose-typography | ✓ | Body/heading/link prose styling present in site.css. |
| 3a.7 | done | inline-code-styling | ✓ | Accent-colored inline code pill via the accent/accent-dim tokens. |
| 3a.8 | done | code-block-component (lang label + copy button) | ✓ | JS-driven language label + copy button with checkmark feedback, matching the reference. |
| 3a.9 | defer | tabbed-code-component (unified CodeTabs) | ⟳ MISSING→defer | Unified CodeTabs is unbuilt in citry and in DJC (the inventory marks it pending). Tab switching already comes from pymdownx.tabbed and the ExampleCard widget, so build a dedicated component only when a multi-fence case needs it. |
| 3a.10 | done | blockquote-styling | ✓ | CSS-only, present. |
| 3a.11 | done | table-styling | ✓ | CSS-only, present. |
| 3a.12 | done | admonition-component | ✓ | CSS-only, multiple variants; verified rendering through the Pass 1 directive expansion. |
| 3a.13 | done | list-styling | ✓ | CSS-only, includes task-list styling. |
| 3a.14 | done | header-component (sticky header: logo, top-nav, search, version, theme, GitHub) | ✓ | Full sticky header. Version picker is a real <c-version-picker> component (`docs_site/_internal/components/version_picker.py`), shown only when a version is set (test_chrome.py:144). |
| 3a.15 | done | sidebar-component (nested nav, collapsible groups, active highlight, scroll-into-view) | ✓ | Primary areas, groups, and pages come from `_nav.yml`. Only the active area's sidebar renders. Group and scroll state are persisted with an area-scoped key, so identically named groups in Docs and Examples do not leak state. |
| 3a.16 | done | right-toc-component (H2/H3 scroll-spy) | ✓ | Right rail present with IntersectionObserver scroll-spy. The recently-added toc.py (merge_html_headings_into_toc) folds raw-HTML reference symbol headings into the rail with kind badges - previously-missing reference-page TOC now works a... |
| 3a.17 | done | doc-page-layout (3-column shell) | ✓ | 3-column shell present; responsive breakpoints handled in site.css. |
| 3a.18 | done | theme-toggle-button (3-mode auto/light/dark wired to localStorage) | ✓ | All three modes reachable and wired to localStorage. Implementation is a direct-select 3-button picker (light/auto/dark) rather than the reference's single cycling button; functionally equivalent (arguably better), the 'cycle' wording is... |
| 3a.19 | done | nav-yaml-loader (loads + validates _nav.yml) | ✓ | `_nav.yml` is the sole primary-navigation declaration. Its top-level areas drive the header and scoped sidebars. Explicit `reference` and `releases` sources hydrate generated pages in place without changing YAML order. The loader rejects empty labels and paths, duplicate ownership, invalid sources, and unresolved areas. |
| 3a.20 | done | breadcrumbs-component | ✓ | Visible and JSON-LD breadcrumbs both follow the declared area/group/page hierarchy; non-link group parents remain spans. |
| 3a.21 | done | page-nav-component (prev/next cards) | ✓ | Card-style prev/next at page bottom, derived from page order inside the active primary area. |
| 3a.22 | done | site-css (bundled prose + chrome stylesheet) | ✓ | Single bundled stylesheet for prose + chrome, as specced. |
| 3a.23 | done | site-js (bundled interactivity) | ✓ | All interactivity present, including the recently-verified resize handles, mobile drawer, and back-to-top. Search UI lives in the separate search.js (Phase 5a), matching the reference split. |

</details>

### Phase 3b  -  Mass content port + responsive + content-layer guardrails

<details>
<summary>Phase 3b group</summary>

| ID | Status | Feature | Re-verified | Note |
|---|---|---|---|---|
| 3b.1 | done | mobile-drawer | ✓ | Full-height off-canvas drawer with hamburger, overlay/Esc close, and background scroll-lock are all present in JS+CSS. Genuinely implemented. |
| 3b.2 | done | mobile-header-actions | ✓ | Kebab overflow menu with theme picker reusing the same data-theme-value hooks is present in the DocPage template as claimed. |
| 3b.3 | done | mobile-toc-details | ✓ | The <details> 'On this page' mobile TOC disclosure is present above the article, driven by the same toc_items as the right rail. |
| 3b.4 | done | responsive-breakpoints | ✓ | Breakpoint tiers and --page-gutter variable are wired flexbox-side per the spike. Implemented. |
| 3b.5 | done | release-notes-generator | ⟳ was MISSING → done (built since) | `docs_site/_internal/release_notes.py` parses CHANGELOG.md into a `/releases/` index + one page per version (per-version split mirrors DJC), wired into build + dev server with a "Release notes" nav entry; rendered with `run_citry_pass=False` so release prose that shows citry syntax is displayed, not executed. The sidebar entry is a collapsible "Release notes" section (closed by default, opens on a release page) with one item per version; version pages breadcrumb back to the index; `EXCLUDED_RELEASES` hides chosen entries (the initial-commit entry by default). Tests in `docs_site/tests/test_release_notes.py`. |
| 3b.6 | done | people-page-template | ✓ | Built: the `UserGrid` component (`docs_site/_internal/components/user_grid.py`) + the `<c-people group=... />` directive reading a seeded data/people.yml, plus docs_site/scripts/people.py (merges citry + django-components merged-PR counts) and the repo--docs-people.yml workflow. Tested in test_directives.py + test_people_generator.py. |
| 3b.7 | done | community-section | ⟳ MISSING→done (workstream A) | Whole community section now ported: ai-bot-policy, contributing, development, and help are full citry prose; code-of-conduct and license inline the repo-root files via pymdownx.snippets; people was already done. |
| 3b.8 | done | template-render-guard | ✓ | Per-page render-failure capture during Pass 1 is implemented in build_site as claimed. |
| 3b.9 | done | fence-validator | ✓ | scan_fences shared primitive and unclosed-fence ERROR present and tested. |
| 3b.10 | done | lexer-alias-check | ✓ | Fence info-string -> Pygments lexer resolution with allowlist is implemented. |
| 3b.11 | done | snippet-path-check | ✓ | Static pre-scan for both single and block --8<-- forms is implemented as claimed. |
| 3b.12 | done | internal-link-check | ✓ | Built-HTML internal link resolution via SiteIndex is implemented and tested. |
| 3b.13 | done | anchor-check | ✓ | #anchor -> id= mapping check is implemented against the site index. |
| 3b.14 | done | image-asset-check | ✓ | Local asset existence check is implemented against the site index. |
| 3b.15 | done | nav-yaml-validity-check | ✓ | Two-way nav/content drift check is implemented. Runs against the small 5-page nav, but the check logic is real. |
| 3b.16 | done | html-wellformedness-check | ✓ | lxml parse plus id-only duplicate detection via the site index is implemented per the documented deviation. |
| 3b.17 | done | snapshot-regression-test | ⟳ was MISSING → done (built since) | Done (workstream I): a dependency-free golden-file content-HTML snapshot test (`tests/test_content_snapshot.py` + `tests/snapshots/`) locks the rendered content HTML (via `wrap_in_layout=False`, so no dates/hashes/chrome) of 3 representative pages; deterministic (double-render byte-identical), with an `UPDATE_SNAPSHOTS=1` regen. No syrupy dependency (citry uses golden files). |
| 3b.18 | done | site-index | ✓ evidence → guards/site_index.py | Now at docs_site/_internal/guards/site_index.py. SiteIndex parses each built page once into a PageRecord (links, anchors, assets, images, headings, canonical, robots, redirect, JSON-LD, duplicate ids) and backs every post-build guard. |
| 3b.19 | done | guardrail-runner-harness | ✓ | Orchestrator with severity rules and dependency order is implemented and tested. |
| 3b.20 | done | single-h1-guardrail | ✓ | Exactly-one-h1 warning is implemented and tested. |
| 3b.21 | done | image-alt-text-guardrail | ✓ | Non-empty alt-text warning is implemented. |
| 3b.22 | done | structured-headings-guardrail | ✓ | No ##->#### heading-jump warning is implemented. |
| 3b.23 | done | code-block-language-tags-guardrail | ✓ | Missing-language-tag warning via source scan over scan_fences is implemented. |
| 3b.25 | done | content-port-sweep | ⟳ partial→done (content gap closed) | Workstream A closed the content-port gap: of DJC's 52 pages, 43 are ported (adapted to citry) and 9 dropped as inapplicable, with 0 partial and 0 skipped (docs_site_content_port_audit.md). Pipeline and full coverage shipped. |

</details>

### Phase 4 (API reference)  -  first half, rows 4.1-4.33

| ID | Status | Feature | Re-verified | Note |
|---|---|---|---|---|
| 4.1 | n/a | ReferencePage / ReferenceEntry types | ✓ n/a confirmed | Django-shaped discovery→rendering ADT. Citry re-derived categories from citry.__all__ and uses one renderer, so the typed page/entry ADT does not apply. The underlying capability (a render-ready per-symbol structure) is ported as referen... |
| 4.2 | n/a | Discovery orchestrator (Layer 1) | ✓ n/a confirmed | The Layer-1 discovery/rendering split is a DJC architecture. Citry's equivalent is static category config, not an orchestrator. |
| 4.3 | partial | Walk script: griffe force_inspection | ✓ partial confirmed | Loader is a cached one-line griffe.load (reference.py:45), simpler than DJC's configurable force_inspection walker. The base-class and source-link enrichers DJC attached to the loader are delivered by citry runtime code instead (4.18/4.19). |
| 4.4 | n/a | API page (kinds 1-5: components, fns, decorators, instances, NamedTuples) | ✓ n/a confirmed | The DJC kind taxonomy (kinds 1-5) does not exist in citry. The equivalent capability  -  rendering functions/classes/instances/NamedTuples as symbols  -  is ported generically via reference._extract + ReferenceSymbol, exercised by e.g. t... |
| 4.5 | n/a | Exceptions page (kind 6) | ✓ n/a confirmed | Django-shaped page. Citry folds exception classes into a normal category, rendered like any other class via ReferenceSymbol. |
| 4.6 | done | Components page (kind 7: predefined Component subclasses) | ⟳ n/a→done (built-ins page) | Citry has a dedicated authored Built-in tags Reference page at `/reference/builtins/`. Its seven component-backed entries use `<c-builtin>` and `extract_builtin`; the same page also documents all eight syntax-backed tags. Card quality is tracked separately by 4.24. |
| 4.7 | n/a | Settings page (kind 8: ComponentsSettings fields) | ✓ n/a confirmed (note de-staled) | CitrySettings renders all 8 fields as a per-field attributes list and member cards with linked types and anchors, not a bare class card. The DJC dedicated settings-page layout is not needed; the all-settings-with-defaults overview block is tracked by 4.25. |
| 4.8 | n/a | Tag formatters (kinds 9-10) | ✓ n/a confirmed | Per the audit brief: tag_formatters do not exist in citry (no {% %} tag formatting layer). N/A. |
| 4.9 | adapt | Management commands (kind 11) | ⟳ n/a→adapt (Commands page) | citry has a real CLI command tree (build_cli/run) plus extension commands (Extension.commands -> ExtensionCommand). Adapt: add a Commands section to the Reference that walks the tree and lists each command. |
| 4.10 | n/a | Template tags (kind 12) | ✓ n/a confirmed | Django `{% %}` template-tag discovery does not apply. Citry's own public template surface is documented instead: all 15 built-in `<c-*>` tags have stable entries on `/reference/builtins/`. |
| 4.11 | n/a | URL patterns (kind 13) | ✓ n/a confirmed | Django URLconf concept. Citry's route types are documented as ordinary classes, not as a URL-pattern layout. |
| 4.12 | n/a | Template vars (kind 14: ComponentVars) | ✓ n/a confirmed | Django template-context-variables concept. N/A for citry. |
| 4.13 | n/a | Testing API (kind 15) | ✓ n/a confirmed | No citry.testing public API is documented in the reference. Real absence, but tied to a DJC-shaped page; N/A as a DJC page, and citry ships no equivalent public testing API on the reference path. |
| 4.14 | partial | Extension hooks + contexts (kinds 16-17) | ✓ partial confirmed | Context objects render as class cards; hook methods render as generic members whose signatures link their context type. Gap: a high-level list of all hooks and their inputs in /advanced/extensions/, since finding hooks by browsing the reference is possible but unpleasant. |
| 4.15 | partial | Extension command API (kind 18) | ✓ partial confirmed | The extension command API classes (ExtensionCommand, CommandArg, CommandArgGroup, CommandSubcommand) render as generic class cards in the reference. There is no dedicated command-tree/argparse-style layout; that bespoke presentation is the 4.9 Commands-page work. |
| 4.16 | n/a | Extension URL API (kind 19) | ✓ n/a confirmed | Django extension-URL concept. N/A for citry. |
| 4.17 | n/a | Signals placeholder (kind 20) | ✓ n/a confirmed | Per the audit brief: signals do not exist in citry (no Django signals framework). N/A. |
| 4.18 | done | RuntimeBasesExtension ported | ✓ done confirmed (tested) | A class now shows its base classes, resolved from the runtime type (griffe's static `bases` is empty for citry) and cross-linked to their reference pages. `reference.py` `_bases` + the `doc-class-bases` line in `reference_symbol.py`. Done via a runtime-import walk rather than a griffe loader extension, but the deliverable (a bases line) is present. |
| 4.19 | done | SourceCodeExtension ported | ✓ done confirmed (tested) | Every reference symbol carries a "View source" link into GitHub, built by `git_metadata.source_url_for` from the griffe object's `filepath` + `lineno`. Unblocked 4.36. |
| 4.20 | done | Parse stdlib objects.inv → name→URL map | ✓ done confirmed (tested) | `inventory.py` parses Python's stdlib `objects.inv` into a name→URL map, offline-safe (empty map on any fetch failure, so a build never breaks). Django is dropped (citry is Django-free). Signature/annotation types now cross-link to docs.python.org. |
| 4.21 | done | Walk griffe Expr trees → resolve ExprName → emit signature links | ✓ done confirmed (tested) | `annotation.render_annotation` walks the griffe Expr tree and links each resolvable name via the internal symbol index then the external inventory. Signatures, parameters, returns, and attributes are all cross-linked now. |
| 4.22 | done | Emit site/objects.inv for external linkbacks | ✓ done confirmed | The emit half (unlike the parse half 4.20) is genuinely ported and tested. |
| 4.23 | done | ReferenceClass (workhorse renderer) | ✓ done confirmed (tested) | Now draws base classes (4.18), a "View source" link (4.19/4.36), and cross-linked signatures (4.21); the earlier degradations are closed. Members still render through the same recursive path, now with linked signatures. |
| 4.24 | MISSING | ReferenceComponentClass (kind 7) | ⟳ n/a→MISSING (no wired signature) | Built-in <c-*> component cards render prose only, with no input signature (extract_builtin sets signature='' and params=[], reference.py:165,169). Gap: render their inputs as a wired-up signature; citry's _params already cross-links param types, so populating params would wire it. |
| 4.25 | MISSING | ReferenceSetting (kinds 8, 14) | ⟳ n/a→MISSING (no field defaults) | citry renders CitrySettings fields with linked types and anchors but not their default values; DJC's ReferenceSetting shows each setting's default. The consolidated defaults overview block is tracked as 4.34. |
| 4.26 | n/a | ReferenceTagFormatter (kind 9) | ✓ n/a confirmed | tag_formatters do not exist in citry. N/A. |
| 4.27 | n/a | ReferenceManagementCommand (kind 11) | ✓ n/a confirmed (DJC renderer) | Django management-command renderer. N/A. |
| 4.28 | n/a | ReferenceTemplateTag (kind 12) | ✓ n/a confirmed | Django {% %} template-tag renderer. N/A. |
| 4.29 | n/a | ReferenceURLPattern (kind 13) | ✓ n/a confirmed | Django URL-pattern renderer. N/A. |
| 4.30 | defer | ReferenceExtensionHook (kind 16, Available-data table) | ⟳ partial→defer (by decision) | Deferred by decision (workstream E). citry already renders all 18 hook-context classes as first-class reference symbols on the Extensions page, so an inline per-hook Available-data table would duplicate them one screen away, and `OnFilesReset`/`OnDependencies` have no base-`Extension` hook to bind to. Feasible (algorithm in the E notes); build only if hook-reading locality is wanted. |
| 4.31 | n/a | ReferenceHookContext (kind 17, fields table) | ⟳ partial→n/a (generic lists sufficient) | Context fields render with per-field docstrings as generic member cards, which is sufficient. DJC's dedicated fields-table layout is a presentation citry does not need. |
| 4.32 | n/a | ReferenceSignal placeholder (kind 20) | ✓ n/a confirmed | No-op placeholder for a framework citry lacks. N/A. |
| 4.33 | n/a | AvailableInstancesList (kind 10) | ✓ n/a confirmed | Instance-list preface for tag-formatter instances, which citry does not have. N/A. |

### Phase 4 (API reference) - second half: features 4.34-4.67

| ID | Status | Feature | Re-verified | Note |
|---|---|---|---|---|
| 4.34 | MISSING | SettingsDefaultsPanel companion | ⟳ n/a→MISSING (settings-defaults block) | citry is missing DJC's SettingsDefaultsPanel: a single code block on the settings page listing every setting with its default value, for easy overview and copying. Per-field defaults are 4.25. |
| 4.35 | done | SignatureBlock (lang-aware fenced sig) | ✓ done confirmed (tested) | Signatures are cross-linked now: each annotation type links to its reference page or to docs.python.org, via `render_annotation` (4.21). |
| 4.36 | done | SourceCodeLink (repo file#L42 link) | ✓ done confirmed (tested) | Every reference entry has a "View source" link (`git_metadata.source_url_for`, format `/blob/<branch>/<path>#L<n>`), rendered by `reference_symbol.py`. |
| 4.37 | done | ParametersTable (name/type/desc rows) | ✓ done confirmed | Rendered as a bullet list (`<ul class=doc-list>`) rather than a `<table>`, but carries name+type+description; functionally equivalent. |
| 4.38 | done | DocstringBody (Google sections + md_in_html) | ✓ done confirmed | Google text + params/returns/raises/attributes render. See 4.39 for the admonition gap in the body. |
| 4.39 | done | AdmonitionsBlock (!!! note in docstrings) | ✓ done confirmed (tested) | Admonition sections now render (`_render_admonition`); the content loss is fixed. A catch-all `else` in `_description` also keeps every other section kind (yields/warns/receives/...) from being dropped, closing the whole class. |
| 4.40 | done | ExamplesBlock (fenced code from Examples:) | ✓ done confirmed (tested) | Docstring `Examples:` sections now render as a titled fenced block (`_render_examples`). The broader content-loss class is closed by the catch-all in `_description` (guards yields/warns/receives too), with a regression test. |
| 4.41 | done | CrossRef (bracket refs [X][] -> URL) | ✓ done (note de-staled) | Bracket cross-refs [text][key] resolve in docstrings and content (reference._md via resolve_crossrefs, reference.py:365), against the citry index and the external Python stdlib inventory; signature type annotations auto-cross-link separately (annotation.py). citry's own docstrings do not use bracket refs yet, pending the docstring rewrite. |
| 4.42 | done | SymbolTypeBadge (span class doc-symbol-X) | ✓ done confirmed | Symbol kind is shown in-page (as text) and as a colored badge in the rail. The in-page `doc-symbol-{kind}` badge span is emitted mainly to feed the TOC kind, matching toc.py:87-96. |
| 4.43 | done | API page layout | ✓ done confirmed | One generic category-page generator replaces DJC's per-kind page layouts; citry re-derived categories from citry.__all__ (docs_site.md:314-322). |
| 4.44 | n/a | Exceptions page layout (POC) | ✓ n/a confirmed | DJC-specific proof-of-concept page. citry's exception classes fold into a normal category; nothing exceptions-specific to build. |
| 4.45 | n/a | Components page layout | ✓ n/a confirmed (→ 4.6) | DJC renders predefined Component subclasses as per-class cards. Citry documents the seven component-backed tags as runtime-backed cards on its unified Built-in tags page, so this DJC-specific layout does not apply. |
| 4.46 | n/a | Settings page layout (entries + defaults panel) | ✓ n/a confirmed (→ 4.25) | DJC's bespoke settings layout pairs a defaults panel with per-field entries. citry renders settings through the generic category page (4.7, done); the defaults-panel analog is tracked as 4.25 (MISSING). |
| 4.47 | n/a | Tag formatters page (classes + instances) | ✓ n/a confirmed | Django-components-specific ({% component %} tag formatting). Does not apply to citry's <c-*> tag syntax. |
| 4.48 | n/a | Commands (command_tree layout) | ✓ n/a confirmed (→ 4.9) | DJC's command_tree layout walks an argparse parser depth-first. citry's CLI and extension commands are its analog, tracked as 4.9 (adapt); the Django management-command layout itself does not apply. |
| 4.49 | n/a | Template tags layout | ✓ n/a confirmed | The Django-template-tag layout is not reusable. Citry's authored Built-in tags page combines reader-written syntax entries with runtime-backed component entries and covers all 15 public tags. |
| 4.50 | n/a | URL patterns layout | ✓ n/a confirmed | DJC discovered Django URL patterns (kind 13). citry has no url dispatcher to introspect; only the route dataclasses, shown as class cards. |
| 4.51 | n/a | Template variables layout | ✓ n/a confirmed | Django-template-context-specific (ComponentVars fields). Not applicable to citry. |
| 4.52 | n/a | Testing API layout | ✓ n/a confirmed | DJC had a testing-API page (kind 15). citry has no equivalent public testing surface on the reference nav. |
| 4.53 | defer | Extension hooks + contexts (hooks_plus_objects) | ⟳ partial→defer (twin of 4.30) | Layout twin of 4.30, deferred by the same decision. citry already renders all 18 On*Context classes as Extensions-page symbols plus the 16 on_* Extension methods, so a Hooks/Objects split would duplicate them one screen away. |
| 4.54 | n/a | Extension commands layout | ✓ n/a confirmed | DJC-specific per-page layout. citry folds the command types into the Extensions class cards. |
| 4.55 | n/a | Extension URLs layout | ✓ n/a confirmed | Django-specific (kind 19). Not applicable to citry. |
| 4.56 | n/a | Signals placeholder layout | ✓ n/a confirmed | Django-signals-specific (kind 20). Explicitly out of scope for citry per the design doc. |
| 4.57 | done | docstring-tag {% docstring %} template tag | ✓ done confirmed | Ported to citry's <c-*> tag syntax. |
| 4.58 | n/a | Dual anchors: new #Component + legacy #django_components.Component | ✓ n/a confirmed | DJC's dual anchors preserved 397+578 inbound links to the old mkdocstrings ids. citry is a fresh package with no legacy inbound links, so a legacy alias would be meaningless. The site_index guard *supports* <a name=> aliases (site_index.... |
| 4.59 | n/a | @mark_extension_hook_api decorator detection | ✓ n/a confirmed | DJC discovery routed hook-context classes via the @mark_extension_hook_api runtime marker. citry's hand-curated category list makes the marker unnecessary. |
| 4.60 | done | Retire _extract_property_docstrings for griffe access | ✓ done confirmed | Effectively satisfied by construction: citry's reference layer is griffe-native from the start. |
| 4.61 | done | Snapshot tests for ReferencePage[] | ✓ done confirmed (tested) | Observed-and-locked tests added (`tests/test_reference_enrichers.py`): bases, source links, cross-linked signatures, the example/admonition blocks, the yields catch-all, and offline safety. citry's category+extract model has no discovery ADT to snapshot, so these lock the rendered HTML fragments instead. |
| 4.62 | done | api-symbol-forward-check ({% docstring %} refs must resolve) | ✓ done confirmed | Full forward check, error severity. |
| 4.63 | done | api-symbol-reverse-check (unreferenced public symbols = warning) | ✓ done confirmed | Warning severity as specified (design doc line 335 notes categories cover all of citry.__all__). |
| 4.64 | n/a | anchor-alias-coverage (renamed symbols have legacy aliases) | ✓ n/a confirmed | N/A for the same reason as 4.58: citry has no legacy/renamed-symbol anchor aliases to cover, so the coverage guard has nothing to check. |
| 4.65 | n/a | proof-exceptions-page (build exceptions.md end-to-end first) | ✓ n/a confirmed | DJC-specific proof-of-concept escalation step; not a citry buildable. |
| 4.66 | done | proof-component-page (build Component class entry second) | ✓ done confirmed | The Component reference page exists and works; the 'proof' framing is process, but the underlying deliverable is present. |
| 4.67 | done | toc-member-nav (collapsible per-member TOC, Option C) | ✓ done confirmed | Fully implemented, including scroll-spy auto-expand, a manual caret to pin one open, class/attr/meth/func/module badges, and the H1 unwrap. |

### Phase 5a (Search) and Phase 5b (Versioning)

| ID | Status | Feature | Note |
|---|---|---|---|
| 5a.1 | done | pagefind-integration | Inventory cites path `build/pagefind.py`; citry keeps it at `docs_site/_internal/pagefind.py`. Scoping is whitelist-based via `c-data-pagefind-body="searchable"` on the article (doc_page.py:261). Runs only on root build, not versi... |
| 5a.2 | done | search-overlay-component | Fully ported. Lazy import() of Pagefind on first open (search.js:169). Anchor-level sub-results rendered. Registered on DocPage via <c-search-modal> (doc_page.py:34). |
| 5a.3 | done | search-bar-component | Header trigger opens the shared modal. Static `/` hint replaced with per-platform label by JS. Icon+label+kbd markup present. |
| 5a.4 | done | search-states | All three states implemented. Error/dev-server path (no index) falls back to Google. Quick-link targets are real content URLs, so a moved target surfaces via the internal_link guard. |
| 5a.5 | done | search-v1-features | All listed sub-features present in search.js. The inventory says a committed Playwright E2E `test_search_e2e.py` drives all of this; citry's actual E2E is docs_site/tests/e2e/test_docs_e2e.py:61 which only asserts trigger->modal->results... |
| 5a.6 | done | custom-404-page | Done (workstream G): the 404 now renders a "Search the documentation" button that opens the shared search modal (the same `data-search-open` hook the header uses), four real popular destinations (installation, your-first-component, concepts/components, reference), and an "open an issue" link. Enriched in `build.py` `_build_not_found`; stays noindex. |
| 5b.1 | n/a | verspec-dep | Inventory marks done ('direct dep in the docs group'). In citry it is neither present nor needed - the vendored mike_versions.py handles ordering without verspec (5b.6 note). Not applicable to citry as built. |
| 5b.2 | done | mike-versions-vendor | Genuinely vendored and used. |
| 5b.3 | done | mike-redirect-vendor | Vendored and wired. |
| 5b.4 | done | versions-json-schema | Manifest read/write is in `docs_site/_internal/versioning.py` (the inventory cites `build/versioning.py`). |
| 5b.5 | done | build-info-stamp | Stamp is written, but the idempotency-check consumer it is meant to power (docs-build-all) does NOT exist in citry (see 5b.8), so the stamp is written but never read to skip work. |
| 5b.6 | done | version-sorter | Inventory also cites `bootstrap._lv` for tag bounds; bootstrap.py does NOT exist in citry (5b.8 missing), so that half of the claim is inapplicable. The manifest-ordering half is ported via the vendored model (no verspec). |
| 5b.7 | done | docs-build-cmd | Ported, though named differently: citry's command is `build --docs-version <v>` (cli.py:36), not a separate `docs-build`. --no-manifest-update surfaces as the build_site kwarg update_versions_manifest (build.py:119) but is NOT exposed as... |
| 5b.8 | done | docs-build-all-cmd | Done (workstream D): a `build-all` CLI command over a git-free `bootstrap.py` core (select_tags/needs_rebuild/bootstrap_versions), with `--dry-run`; idempotent via each version's `_build_info.json` source_sha. Unit-tested with injected git fakes; a successful worktree build needs doc-bearing tags to exercise end-to-end. |
| 5b.9 | done | worktree-orchestration | Done (workstream D): `build-all` builds each qualifying tag from a `git worktree add --detach` checkout (skipping checkouts that lack the docs builder), removing the worktree after. Skip + cleanup paths tested; a successful build needs a doc-bearing tag. |
| 5b.10 | done | alias-redirect-materializer | Ported and tested; relative href computed per nesting depth (versioning.py:156). |
| 5b.11 | done | version-picker-component | Fully ported including the 'Later' root-page fallback via data-versions-root (assemble.py) and <meta name=djc-base-path>. Switches to version home (no page-preservation), matching the note. Registered on DocPage (doc_page.py:35, 156). |
| 5b.12 | done | docs-versions-yaml | Done (workstream D): `docs_site/docs_versions.yml` (pattern/include/exclude/oldest/newest, aliases.latest, publish.window, indexing.keep_recent) is parsed by the strict YAML loader through `bootstrap.load_versions_config` and read by `build-all`; publication and indexing policy source from it. |
| 5b.13 | done | docs-build-check-cmd (manifest<->FS parity) | Done (workstream D): `docs_site/_internal/guards/versions_manifest.py` + a `versions-check` CLI command check manifest<->filesystem parity (orphans both directions, half-built dirs, alias resolution) as a SEPARATE guard suite (VERSION_GUARDS), not part of the per-build gate. |
| 5b.14 | done | versions-manifest-integrity-check | Done (workstream D): the `versions_manifest` guard checks orphans, half-built dirs (no index.html / no _build_info.json), stamp sanity (required fields + version-matches-dir-name), and alias resolution. It caught the live 0.2.0 orphan, which was reconciled (versions.json is now empty). |
| 5b.15 | done | cross-version-link-check | Done (workstream D): `docs_site/_internal/guards/cross_version_link.py` builds one SiteIndex over the whole versions/ tree and resolves cross-version `/v/<vA>/ -> /v/<vB>/` links, flagging broken ones; frozen imports skipped. |
| 5b.16 | done | ci-release-docs-workflow | Done (workstream D): `repo--docs-release.yml` ports DJC's release-docs flow to citry - on a `citry@X.Y.Z` tag it builds that version, runs versions-check, commits `versions/<v>/` + manifest, then assembles + deploys. (Earlier marked n/a on the wrong assumption that citry rejected the committed-versions model; citry does want it. See the workflow header for the human-review items before a first release.) |
| 5b.17 | partial | docs-build-check-command (CI gate) | The generic pre-commit gate (build + all non-version guards) IS ported and in PR CI. But the 5b-specific part the inventory claims - that CI also runs `docs_versions_check` (which does not exist, 5b.13) - is NOT present: repo--docs-check... |

### Phase 5c (SEO + AIO + social cards + chrome polish) and Phase 5d (feature-parity audit)

| ID | Status | Feature | Re-verified | Note |
|---|---|---|---|---|
| 5c.1 | done | sitemap-xml | ✓ | seo.write_sitemap now emits `<lastmod>` from git per source (git_metadata.get_page_git_meta via PageRecord.source_md); tested in test_seo.py. (Section-priority tuning for future guides/overview sections is cosmetic and left as-is.) |
| 5c.2 | done | robots-txt | ✓ done (multi-version) | Done (workstream D): `write_robots` now emits `Disallow: /v/<v>/` for every version outside the newest-2 + `latest` (read from the committed versions.json). Allow-all + AI bots + sitemap unchanged. |
| 5c.3 | done | og-image-generation | ✓ | Skips noindex + custom-og_image pages (_card_for social_cards.py:117-126). Matches the inventory description including graceful degradation. |
| 5c.4 | done | og-card-template | ✓ | Ported as a Citry Component (the reference was a Django template); functionally equivalent. |
| 5c.5 | done | social-card-generator | ✓ | Matches inventory. |
| 5c.6 | done | social-card-caching | ✓ | Deviation from a sidecar JSON to a content-addressed filename is intentional and equivalent, as the inventory states. |
| 5c.7 | done | og-twitter-cards | ✓ | Fully present in the DocPage head. |
| 5c.8 | done | json-ld-techarticle | ✓ | TechArticle now carries datePublished/dateModified from PageGitMeta.created/last_updated: render_page passes the git dates to DocPage's JSON-LD. Tested in test_git_metadata.py. |
| 5c.9 | done | json-ld-validity-guardrail | ✓ (guard registered) | json_ld.check is registered in GUARDS (`docs_site/_internal/guards/__init__.py`); it validates every JSON-LD block parses and has the required keys, with script-safe dumps in DocPage. |
| 5c.10 | done | llms-txt | ✓ | Both files present and wired. The alternate link is hardcoded /llms.txt (base_path.py rewrites it for subpath deploys). |
| 5c.11 | done | indexing-manifest | ✓ | Done (workstream F): `write_indexing_manifest` now lists every recorded doc page including `noindex` ones and records each page's real robots directive (`noindex,follow` / `index,follow`), matching what each page's `<meta robots>` declares. The generated 404 is written outside the record list, so it is not in the manifest (stated in the docstring). |
| 5c.12 | n/a | anchor-deprecation-timer | ✓ n/a confirmed | N/A for citry: there is no long-form `#django_components.X` anchor-alias scheme (citry is a fresh package with no legacy or renamed anchors to deprecate), so the timer guard has nothing to track. Same reasoning as 4.58 / 4.64. |
| 5c.13 | done | lighthouse-ci | ✓ | Done (workstream H): `repo--docs-lighthouse.yml` + `.github/lighthouserc.json` build the site and run Lighthouse CI (a11y/best-practices/SEO hard gates, performance warn), ported from DJC. Not yet run in real CI (thresholds were tuned on DJC's pages), so it is kept out of branch protection until a first run confirms - see the workflow's review notes. |
| 5c.14 | done | html-minifier | ✓ | Fully ported and wired. |
| 5c.15 | n/a | html-sanitizer | ✓ n/a confirmed | Correctly N/A - never a ported plugin; matches the inventory's 'won't-do' verdict. |
| 5c.16 | done | edit-on-github-url | ✓ | git_metadata.edit_url_for builds the source-file GitHub URL; render_page passes it to DocPage so content pages show an "Edit this page on GitHub" footer link (generated pages get none). Browser-verified in test_docs_e2e.py. |
| 5c.17 | done | redirect-file-emitter | ⟳ partial→done | The redirect emitter is fully ported, wired into the build, and tested on sample data (redirects.py, build.py:235). An empty REDIRECTS is the correct state for a fresh package with no moved URLs, not a gap; the first real page rename adds an entry. |
| 5c.18 | done | redirect-target-check | ✓ (guard registered) | Guard fully ported and registered in GUARDS (`docs_site/_internal/guards/__init__.py`); it flags any redirect stub whose target does not resolve. Dormant only because no stubs are emitted yet. |
| 5c.19 | done | external-link-check | ✓ | Done (workstream H): `repo--docs-external-links.yml` runs a weekly lychee check of outbound links on the built site (discord.gg and the not-yet-live citry.dev excluded, `GITHUB_TOKEN` for rate limits). Scheduled and non-blocking; ported from DJC, needs a first real run to confirm. |
| 5d.1 | done | back-to-top-button | ✓ | Fully ported (markup + JS + CSS). |
| 5d.2 | done | social-links-pypi-discord | ✓ | Done (workstream G): `djc-social-link` icon links for GitHub, PyPI, and Discord now sit in the header (SVGs ported byte-exact from DJC), with matching text links in the mobile overflow menu. citry's channels: github.com/citry-dev/citry, pypi.org/project/citry, discord.gg/NaQ8QPyHtD (the same Discord as django-components). |
| 5d.3 | done | google-site-verification | ✓ | Done (workstream G): `DocsConfig.google_site_verification` (env `DOCS_GOOGLE_SITE_VERIFICATION`, empty by default) threads into `DocPage`, which emits `<meta name="google-site-verification">` in the head only when set. |

### Phase 6 (cutover), Phase 7-9 (search v2/v3, landing), Phase 10+ (maintenance), Cross-cutting

| ID | Status | Feature | Re-verified | Note |
|---|---|---|---|---|
| 6.1 | n/a | materialize-redirects-script (latest/ symlink -> redirect HTML) | ✓ n/a confirmed | The underlying redirect-stub-not-symlink capability EXISTS in citry (materialize_alias, tested in test_versioning.py:47). The 'convert an existing latest/ symlink' task is N/A: there is no imported symlink tree to convert. |
| 6.2 | n/a | import-gh-pages-tree (one-time mirror of origin/gh-pages into versions/) | ✓ n/a confirmed | Deliberately dropped by design: citry has no historical mkdocs/mike versions to import. Reference command exists at _djc_reference_docs_site/.../docs_import_ghpages.py but was not ported. |
| 6.3 | n/a | docs-build-check-validation (validate imported tree before commit) | ✓ n/a confirmed | Its purpose (validate an imported tree) is moot with 6.2 N/A. The version-tree validation guards it folds into (versions_manifest) are themselves deferred by design. |
| 6.4 | done | ci-deploy-site-via-actions (build docs_site -> site/, deploy via GitHub Actions) | ✓ done confirmed | Ported and adapted: a standalone assemble CLI, the upload-pages-artifact plus deploy-pages model, and base path plus publish window. The Pages-source flip at real cutover is documented in the workflow. |
| 6.5 | n/a | gh-pages-branch-deletion (deferred 3-6 months) | ✓ n/a confirmed | Reference marks this pending/deferred cleanup; for citry it is inapplicable because there was never a gh-pages branch (fresh Pages-via-Actions deploy). |
| 6.6 | n/a | cutover-docs-cleanup (delete docs_old/ + mkdocs.yml; remove mkdocs/material/mike deps) | ✓ n/a confirmed | Cutover cleanup is N/A: citry never carried the old mkdocs site. pyproject.toml docs extra pulls only the survivor deps (pymdown-extensions, lxml, pagefind, minify-html, etc.). |
| 6.7 | n/a | content-move-to-content-dir (docs_old/ -> content/, assets -> static/) | ✓ n/a confirmed | N/A: citry's content was vendored directly into content/; there is no docs_old/ tree to migrate. |
| 6.8 | n/a | examples-move (docs_old/examples/ -> docs_site/examples/) | ✓ n/a confirmed | N/A as a 'move' task: examples are already in place. The example autodiscovery + card feature (Phase 2) is separately ported. |
| 6.9 | n/a | devguides-move (docs_old/community/devguides/ -> internal docs/devguides/) | ✓ n/a confirmed | N/A: DJC-specific artifact; no such devguides tree exists in citry to relocate. |
| 6.10 | n/a | devguides-relevance-review | ✓ n/a confirmed | N/A: nothing to review; the DJC devguides were not brought into citry. |
| 6.11 | MISSING | benchmark-report-relocation (asv report docs_old/benchmarks/ -> benchmarks/report/ + static passthrough) | ⟳ n/a→MISSING (blocked by benchmark site) | citry shows benchmarks as a content page but has no browsable benchmark report to serve, and the static-passthrough mechanism is not ported. Blocked on first standing up a benchmarking site; implement the passthrough once it exists. |
| 6.12 | done | canonical-latest-alignment (root canonical; old /v/ noindex via robots) | ✓ done (multi-version) | Done (workstream D): old `/v/<v>/` snapshots are now kept out of search - robots.txt disallows them (5c.2) and the assemble-time pass adds noindex + canonical-to-current (1.26/1.27). |
| 7.1 | defer | search-v2-autocomplete (inline autocomplete suggestions) | ✓ defer confirmed | Pending in the reference too, but for citry it is genuinely not built. Applies to citry (Pagefind search is present); a real future gap, not N/A. |
| 7.2 | defer | search-v2-recent-searches (local-stored history) | ✓ defer confirmed | Applies to citry; not built. Pending in reference as well. |
| 7.3 | defer | search-v2-filters (scoping filters, e.g. API only) | ✓ defer confirmed | Applies to citry; not built. Pending in reference. |
| 7.4 | defer | search-v2-typo-recovery (fallback scoring) | ✓ defer confirmed | Applies to citry; not built. Pending in reference. |
| 8.1 | defer | search-v3-analytics (search-result analytics) | ✓ defer confirmed | Blocked on choosing an analytics target in the reference; simply absent in citry. Applies to citry; a future gap, not N/A. |
| 9.1 | MISSING | landing-page-component (full hero/features/CTA landing page) | ✓ MISSING confirmed | Applies to citry; the real landing page (no sidebar/TOC, hero + features + CTAs) is not built. Pending in reference too, but genuinely a gap for citry. |
| 10.1 | n/a | selective-rebuild-policy (rebuild historical versions with new builder) | ✓ n/a (latent) | N/A until citry has multiple releases AND older-builder snapshots. Nothing to selectively rebuild today. |
| 10.2 | n/a | url-redirect-map-pre-0124 (manual redirects for pre-0.124 broken URLs) | ✓ n/a confirmed | N/A: these are django-components legacy URLs; citry has no pre-0.124 history. The redirect-stub emitter itself is present (redirects.py) but empty. |
| 10.3 | n/a | version-pruning-policy (move pre-0.110 versions to docs-archive branch) | ✓ n/a (latent) | N/A: DJC-specific version-history cleanup; citry starts at a single current version. |
| 10.4 | n/a | cve-bundle-audit (CVE audit on frozen Material/plugin bundles) | ✓ n/a (latent) | N/A: the audit targets frozen Material/mike/jQuery/asv bundles that citry never carried. The reference's residual risk (asv jQuery, /v/0.92 Material) does not exist here. |
| 10.5 | n/a | docs-versions-yaml-per-version-freeze-flag | ✓ n/a (latent) | N/A: the freeze flag exists to mark imported/frozen gh-pages versions, which citry has none of. Reference marks it 'Only if needed'. |
| 10.6 | n/a | sitemap-strategy (sitemap-index aggregating only latest/) | ✓ n/a (latent) | N/A / not needed: the single-sitemap current-version approach already lists only latest URLs. A multi-sitemap index becomes relevant only with many versions. Reference marks it 'Optional'. |
| 10.7 | MISSING | dev-deploy-ci-flow (whether dev/ commits or deploys separately) | ⟳ n/a→MISSING (dev docs version) | DJC deploys a /v/dev/ docs version built from the dev branch, robots-disallowed so it is not indexed, for previewing unreleased docs. citry has no dev docs version; implement it with the multi-version deploy. |
| legacy-anchor-alias-mechanism | n/a | Legacy anchor aliases (dual #Symbol + #django_components.Symbol anchors) | ✓ n/a confirmed | N/A: the dual-anchor mechanism (4.58) exists to preserve 397+578 inbound links to django_components.* anchors. citry is a fresh project with no such legacy inbound links, so the legacy-alias half was correctly not ported. |
