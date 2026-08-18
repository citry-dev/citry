# Design: citry docs site (port of the django-components docs site)

This document plans the port of the django-components custom documentation
site into citry. It is the persistent reference for that multi-session
effort, in the same spirit as [`migration_djc.md`](migration_djc.md).

For operating rules see [`/CLAUDE.md`](../../CLAUDE.md). For the engine
migration see [`migration_djc.md`](migration_djc.md).

---

## Goal and why it is a good fit

django-components recently replaced its mkdocs/Material docs stack with a
custom builder that renders the documentation **with django-components
themselves** (live, interactive examples; component-driven page chrome). PR:
[django-components#1664](https://github.com/django-components/django-components/pull/1664).

Citry should have the same site, dogfooded on citry instead of Django. This
is a natural fit because citry is already the framework-agnostic engine such a
site needs:

- Component to HTML is built: `Component(...)` to `CitryElement` to `.render()`
  to `CitryRender` to `serialize()` to a string
  ([`component_render.py`](../../packages/py/citry/citry/component_render.py),
  [`serialize.py`](../../packages/py/citry/citry/serialize.py)).
- Serialize-time JS/CSS placement is built: `serialize(deps_strategy="document")`
  collects each component's CSS/JS and puts it in the page (CSS before
  `</head>`, JS before `</body>`, or into `<c-js>`/`<c-css>` placeholders), with
  `simple`/`fragment`/`ignore` variants. A full HTML page with working component
  assets comes out of one call, so interactive examples need no extra plumbing
  ([`ext/dependencies/`](../../packages/py/citry/citry/ext/dependencies/)).
- A framework-agnostic web layer is built:
  [`contrib/asgi.py`](../../packages/py/citry/citry/contrib/asgi.py) and
  [`contrib/fastapi.py`](../../packages/py/citry/citry/contrib/fastapi.py)
  mount a `Citry` instance's routes (component JS/CSS, the client runtime,
  extension endpoints) into FastAPI/Starlette/anything, over a real
  `URLRoute`/`RouteResponse` router
  ([`util/routing.py`](../../packages/py/citry/citry/util/routing.py)).
- No Django anywhere in `citry`, by invariant.

The win: the upstream site is already roughly 90% Django-independent. griffe
(API reference), python-markdown + pymdownx (markdown), Pagefind (search), and
the versioning / SEO / sitemap / social-card code are all plain Python. The
only genuinely Django-coupled pieces are the template pass that expands tags,
the component layer (page chrome and examples), and the project scaffolding
(settings, views, URLs, management commands, dev server). Each has a clean
citry / FastAPI replacement.

---

## Decisions taken (this session)

1. **Approach: port and adapt, do not reimplement.** Bring the entire
   upstream `docs_site/` into citry and adapt what exists to run on citry,
   rather than rebuilding the infrastructure from citry primitives.
2. **Scope: MVP first, full parity by the end of the work package.** The
   first iteration may temporarily switch off heavier features (Pagefind
   search, multi-version snapshots, SEO/sitemap, social cards) to get a
   working dogfood site fast. The work package is not done until those are
   back on and the site is at parity with the upstream one.
3. **Engine reference: full re-vendor to latest.** Refresh
   `_djc_reference` from current upstream rather than spot-updating. See
   [the reconciliation section](#_djc_reference-and-upstream-reconciliation)
   for the consequences and the follow-ups that re-vendor implies.
4. **No imported version history.** Citry is a new project with no prior
   documentation versions, so DJC's historical version snapshots are not
   carried over (the 1 GB `versions/` history is excluded from the vendor and
   the gh-pages import command is dropped). The multi-version *capability*
   still ports, but it starts at a single current version and grows as citry
   releases.
5. **Community channels: GitHub, PyPI, and Discord.** The docs-site header
   links to the project's GitHub (`citry-dev/citry`), PyPI (`citry`), and
   Discord (`https://discord.gg/NaQ8QPyHtD`, the same server as
   django-components). These are citry's canonical channels; the README carries
   the matching badges and the header renders them as social icons (workstream
   G, feature 5d.2). No other channels exist yet.

---

## Configuration ownership and command snapshot

Maintainer-owned product declarations live at the top of `docs_site/`, not in
the Python implementation. `settings.yml` owns site and repository identity,
links, Markdown profiles, search, Blog, git metadata, SEO, inventory, and
release-note policy. `reference.yml`, `ui_library.yml`, `redirects.yml`, and
`docs_versions.yml` own the build's ordered catalogs and workflow policy.
`people_sources.yml` separately owns the inputs used only by
`docs_site/scripts/people.py`. In particular, UI-family API heading contracts
belong to `ui_library.yml`; adding a family does not require a second Python
registry.

`_internal/config.py` is limited to runtime paths and environment overrides.
Each build, check, assemble, or server process loads its five runtime manifests
into one validated `DocsProject` and keeps that project active through nested
renderers, components, generated pages, and guards. The People generator loads
and validates `people_sources.yml` at its own command boundary. Mutating
commands validate the source files they will consume, generated Python symbols,
projection front matter, and route collisions before clearing or writing
output. The operational commands and edit locations are documented in
`docs_site/README.md`.

---

## Porting principle: read DJC first, adapt minimally, do not reinvent

When a docs-site feature needs building, the default is **not** to design it
from citry primitives. First find how the django-components site solved it, then
port that shape and change only the citry-specific parts. Reinvent only when
DJC's approach genuinely cannot apply to citry, and say why when you do.

Where to look: the vendored [`_djc_reference_docs_site/`](#_djc_reference-and-upstream-reconciliation),
and, for anything the snapshot dropped, the public
[django-components repo](https://github.com/django-components/django-components)
on `master` and the PR #1664 branch `jo-docs-mkdocs-migrate` (fetch a file with
`gh api repos/django-components/django-components/contents/<path>?ref=jo-docs-mkdocs-migrate`).

The failure mode to avoid: reaching for a larger, citry-specific mechanism when
DJC already solved the same problem more simply. Concrete example, the static
fragments demo: the instinct was to build a general "export every component's
dependency scripts to static files" subsystem for citry, but DJC's actual
solution ([`build/examples.py`](../../packages/py/citry/_djc_reference_docs_site/apps/docs/build/examples.py))
is only "pre-render each fragment variant to a static endpoint and rewrite the
URLs." Citry writes those endpoints below
`examples/<slug>/demo/<variant>/index.html`. Porting
that shape, the only genuinely citry-specific glue is writing the one fragment
component's two class-level dep files (citry's `fragment` strategy references
component JS/CSS by URL, where DJC served them through Django views), a handful
of lines rather than a subsystem.

---

## Upstream source and provenance

The upstream site lives in the django-components repo under `docs_site/`. It
was vendored into citry in Phase 0 from commit
`5d4d4f5d13dd06c80ba389f30fc63fdbb71cda75` (branch `jo-docs-mkdocs-migrate`,
the PR #1664 work, 2026-06-20), via
[`scripts/vendor_djc_reference.sh`](../../scripts/vendor_djc_reference.sh).

That single re-vendor produced two read-only, gitignored snapshots under
`packages/py/citry/`:

- `_djc_reference/` - the refreshed engine source (upstream
  `src/django_components/`), the migration reference cited across the design
  docs.
- `_djc_reference_docs_site/` - the docs-site tree to port from (upstream
  `docs_site/` minus the 1 GB `versions/` history, the generated
  `staticfiles/`, and the generated social-card cache; about 7 MB).

The vendoring script is the tracked provenance record: it pins the commit and
reproduces both snapshots, so the engine snapshot the design docs reference
stays reproducible even though the snapshot itself is not tracked. The commit
is on the public `django-components` repo (`origin/jo-docs-mkdocs-migrate`),
not on `master`, because PR #1664 is unmerged; re-pin the script to the merge
commit once it lands on `master`.

**Not everything upstream is inside the vendored `docs_site/` tree.** The
snapshot is only the upstream `docs_site/` directory, so repo-root scripts
(`scripts/people.py`, `scripts/supported_versions.py`, `scripts/validate_links.py`)
and the `.github/workflows/maint-docs-*.yml` maintenance workflows are absent
from it. They are all public in the django-components repo, on `master` and on
the PR #1664 branch `jo-docs-mkdocs-migrate`. When a feature needs one of these,
fetch and port it from there (for example with
`gh api repos/django-components/django-components/contents/<path>?ref=jo-docs-mkdocs-migrate`),
rather than reinventing it. Citry already ports `supported_versions.py`, and
`docs_site/scripts/people.py` (extended to merge the repositories declared in
`docs_site/people_sources.yml`) with its `repo--docs-people.yml` workflow.

---

## What the upstream site is, concretely

The heart is a **three-pass rendering pipeline** (from
`docs_site/apps/docs/build/pipeline.py`):

- **Pre-pass (fence protection).** Code blocks in the markdown are protected
  so the template engine does not execute template tags written *inside*
  documentation examples. Upstream wraps them in Django `{% verbatim %}`.
- **Pass 1 (template expansion).** The Django template engine expands all
  tags in the markdown source: the docs tags (`{% example %}`,
  `{% docstring %}`, `{% version %}`, `{% include_file %}`, `{% image %}`,
  `{% people %}`) plus `{% component %}`.
- **Pass 2 (markdown).** python-markdown + pymdownx converts the expanded
  markdown to HTML (syntax highlighting, admonitions, TOC, ...).
- **Pass 3 (page wrap).** The `DocPage` component wraps the content HTML in a
  full page layout (head metadata, CSS, header, sidebar, TOC, chrome).

Supporting build modules (`docs_site/apps/docs/build/`): `nav`, `toc`,
`frontmatter`, `links`, `redirects`, `seo`, `social_cards`, `pagefind`,
`minify`, `llms`, `site_index`, `versioning`, `base_path`, `git_metadata`,
`release_notes`, `paths`, `guard_runner`, and a `guards/` set (around 30
content/link/anchor/cross-version checks). API reference is a griffe-based
subsystem under `docs_site/apps/docs/reference/` plus
`docs_site/apps/docs/griffe_extensions/`.

The page chrome and widgets are django-components components under
`docs_site/apps/docs/components/`: `doc_page`, `example_card`,
`not_found_page`, `og_card`, `reference`, `search_modal`, `user_grid`,
`version_picker`.

Live examples live under `docs_site/examples/<name>/`, each a trio: a reusable
`component.py` (a django-components `Component`), a full-page `page.py`
(another `Component` whose template uses `{% component %}`), and a test. The
`{% example "tabs" %}` tag renders an `ExampleCard` showing component code,
page code, and a live demo.

Docs dependencies are a uv group (`[dependency-groups].docs`): `griffe`,
`pagefind[bin]` (bundled Rust binary, no Node), `minify-html` (Rust), `lxml`
(guard HTML parsing), `pymdown-extensions`, `markdown`.

---

## Disposition of the upstream tree

Three buckets. Directory-level, with the live upstream tree as the
file-level authority.

### A. Port with a config shim (Django-independent logic)

These are plain Python and only touch `django.conf.settings` for a few values
(`REPO_ROOT`, `SITE_URL`, `STATIC_ROOT`, base path, ...). Replace settings
with a plain citry-docs config object; otherwise port as-is.

- `build/`: `frontmatter`, `links`, `toc`, `nav`, `seo`, `social_cards`,
  `pagefind`, `minify`, `llms`, `redirects`, `site_index`, `versioning`,
  `base_path`, `git_metadata`, `release_notes`, `paths`, `guard_runner`,
  `guards/`.
- `reference/` (griffe API reference) and `griffe_extensions/`. griffe
  introspects Python and is framework-agnostic; only the parts that *render*
  through components move to bucket B.
- `_vendor/` (mike version-compat shims).
- `static/`, `content/images`, `examples/*/images`, `design/` notes.

### B. Adapt to citry (the real work)

These use Django templating, components, or views.

- **Pass 1 of the pipeline.** Swap the Django template `Engine` for citry.
  Since citry *is* a template engine, the dogfood path is to treat each
  markdown body (after frontmatter) as a citry template and render it with the
  docs components registered. The docs tags become citry components:
  `{% example %}` to `<c-example>`, `{% docstring %}` to `<c-docstring>`,
  `{% version %}` to `<c-version>`, `{% include_file %}` to
  `<c-include-file>`, `{% image %}` to `<c-image>`, `{% people %}` to
  `<c-people>`.
- **Pass 3 page wrap and all `components/`.** Re-author the page-chrome
  components (`doc_page`, `example_card`, `not_found_page`, `og_card`,
  `reference`, `search_modal`, `user_grid`, `version_picker`) as citry
  components. Templates move from `{% %}` syntax to citry `<c-*>` / `{{ }}`.
- **`build/fence_protection.py`.** Re-target from `{% verbatim %}` to citry's
  verbatim mechanism (`<c-raw>`), and protect citry's delimiters (`{{ }}`,
  `<c-*>`, `{# #}`) rather than Django's.
- **`build/builder.py`.** Replace the Django `render_to_string` /
  staticfiles-finder calls with citry render calls and a plain static-copy
  step.
- **`examples/*/`.** Port each example `component.py` and `page.py` to citry
  `Component`s: imports (`django_components` to `citry`), template syntax
  (`{% component %}` to `<c-*>`), and Django helpers (`django.utils.text`,
  `mark_safe`, `{% lorem %}`) to citry / stdlib equivalents. The dynamic
  `{% component %}` usage maps onto citry's built-in `<c-component>`.

### C. Replace (Django project scaffolding)

- `manage.py`, `docs_site/docs_site/{settings,urls,wsgi}.py`,
  `apps/docs/{apps,urls,views}.py` to a plain citry-docs config module plus a
  FastAPI app.
- `apps/docs/management/commands/*` to a CLI (see below).
- `apps/docs/templatetags/docs_extras.py` is split: its tag bodies become the
  `<c-*>` docs components (bucket B); the Django registration wrapper is
  dropped.

---

## Web server and CLI

The site's primary output is a **static build** for free hosting (GitHub
Pages), exactly as upstream. A web server is needed only for the dev/preview
and serve-built commands, so FastAPI / Starlette + uvicorn covers it.

CLI (subcommands mirror the upstream management commands; argparse or typer):

| Upstream command | citry-docs subcommand | Role |
|---|---|---|
| `build_docs` | `build` | Build the static site |
| `docs_serve` | `serve` | Dev server: render live, hot reload (uvicorn `--reload` + `watchfiles`) |
| `docs_serve_built` | `serve-built` | Serve the already-built static output |
| `docs_assemble` | `assemble` | Assemble the versioned deploy artifact |
| `docs_build_all` | `build-all` | Build every version |
| `docs_build_check` | `build-check` | Run the post-build guards |
| `docs_import_ghpages` | `import-ghpages` | Import historical versions |
| `docs_versions_check` | `versions-check` | Validate the version tree |

The dev server renders pages through citry on each request and mounts the
`Citry` instance's routes (component JS/CSS, runtime) via the existing
`contrib.fastapi.mount`. The static build runs the same render path ahead of
time and writes files.

---

## Content adaptation

The markdown under `content/` currently contains Django template syntax inline
(`{% example %}`, `{% component %}`, `{% version %}`, `{% lorem %}`, and
`{% verbatim %}` fences). Bringing the content over means a mechanical
transform of those tags to citry syntax (`<c-example name="..." />`,
`<c-component .../>`, `{{ version }}`, ...). The common tags are regular enough
to script the bulk conversion and hand-fix the remainder. Prose stays as-is.

---

## Phased plan

> **Status note (August 2026):** The slice log below records the order in which
> the port was implemented. Phrases such as "deferred" and "still open" inside
> a slice describe that historical checkpoint, not the current site. The
> configuration snapshot above, `docs_site/README.md`, the current code and
> tests, and the parity audit are authoritative for present behavior.

**Phase 0: vendor. (Done.)** Refreshed `_djc_reference` and vendored
`docs_site/` (minus history and generated output) as two gitignored snapshots,
reproducible via [`scripts/vendor_djc_reference.sh`](../../scripts/vendor_djc_reference.sh);
added the `docs` dependency group. The immediate follow-up before Phase 1 is
the citation re-check sweep described in the reconciliation section.

**Phase 1: MVP skeleton.** Config shim for the bucket-A `build/` modules.
Citry `DocPage` and the minimal page chrome. The three-pass pipeline running
on citry for a single page. Static `build` plus `serve` (dev). Parity features
(search, multi-version, SEO, social cards) switched off behind flags.

The working site lives at the repo-root `docs_site/` package (distinct from the
gitignored `_djc_reference_docs_site/` it ports from). Progress:

- *Slice 1 (done):* `config`, `frontmatter`, `pipeline.render_page` (markdown
  pass 2, ported verbatim, plus the `DocPage` layout wrap), and a minimal citry
  `DocPage`. One markdown page renders to a full HTML document.
- *Slice 2 (done):* `paths` (URL/file mapping), `build.build_site` (walk content
  to clean-URL HTML, copy assets, safe-output guard, per-page error capture),
  `serve` (a Starlette dev server: live render plus citry's `/citry` asset
  mount), and the `python -m docs_site` CLI (`build` / `serve`).
- *Slice 3 (done):* `nav` (the `NavTree` area hierarchy from `_nav.yml`),
  the static assets
  (`site.css`/`site.js`/fonts/pygments, reused verbatim), and the full `DocPage`
  chrome translated to citry (head, sticky header with theme picker, sidebar
  nav with per-page active state, breadcrumbs, content, prev/next, footer,
  right-rail TOC, back-to-top). Django filters and loop-position logic moved
  into `template_data`; the `djc-*` class hooks are kept so the vendored CSS/JS
  work unchanged. At that checkpoint, search, versioning, structured data, and
  mobile navigation remained for later slices.
- *Slice 4a (done):* the pass 0/1 directive pipeline. `fence_protection`
  protects code (fenced and inline) by wrapping it in `<c-raw>`;
  `pipeline.render_content` renders the page body as a citry template (a
  throwaway content component, unregistered after) so the custom `<c-*>` tags
  expand. Shipped tags: `<c-version />`
  and `<c-include-file path="..." />`. Wired into `render_page` ahead of the
  markdown pass.
- *Slice 4b (done):* the `<c-example name="..." />` live widget and its example
  infrastructure - `examples` (discovery + the tabbed card), example
  component/page pairs under `examples/<name>/`, build-time pre-render of each
  demo to `examples/<slug>/demo/index.html`, and a dev-server route for it. The
  authored recipe remains at `examples/<slug>/`. The card shows a live-demo
  iframe plus the Pygments-highlighted source. At that checkpoint,
  `<c-docstring />`, `<c-image />`, `<c-people />`, and example fragment
  variants remained for later slices.

  Notes:
  - The tabbed card is a citry component (`docs_site/_internal/components/example_card.py`). The
    per-card unique ids and the `<label for>` are dynamic, set with `c-id` and
    `c-bind="{'for': ...}"` (a regular `for` attribute coexists with the `c-for`
    loop; only its dynamic form needs `c-bind`, because `c-for` is the loop
    directive). The `<c-example />` directive renders it and flushes it left
    (`_lstrip_outside_pre`) so the markdown pass treats it as block HTML.
  - Current follow-through: the static build now exports `citry.js`, the Events
    runtime, and fragment JS/CSS under the same `/citry` mount used by the dev
    server. JavaScript examples therefore work from flat files as well as in
    live development. Unit and Chromium tests cover runtime export, fragment
    assets, and interactive example behavior.

The slices above were the execution unit and do not line up one-to-one with the
phase numbers below: slices 1-3 plus 4a are Phase 1, and **slice 4b is Phase 2**.

**Phase 2: live examples. (Done, delivered as slice 4b and later follow-ups.)**
`<c-example>` and the example card run on citry, with example component/page
pairs, build-time pre-rendering, JavaScript-interactive demos, fragment
variants, and the Examples cookbook/gallery.

**Phase 3: API reference.** Introspect citry with griffe and render symbols
through citry components, a page per category. The ordered catalog now lives in
`docs_site/reference.yml`; `_internal/reference_pages.py` strictly loads it and
owns generation mechanics.

The categories were re-derived from citry's public surface, not ported from
DJC's Django-shaped pages (`template_tags`, `management_command`,
`tag_formatters`, `signals`, and `template_variables`, which citry does not
have). The 17 ordered categories are **Component**, **Component
introspection**, **Component libraries**, **Citry instance and config**,
**Rendering**, **Slots**, **Nodes**, **Template analysis**, **Extensions**,
**Dependencies**, **Render cache keys**, **Events**, **Browser APIs**, **HTML
attributes**, **Web integration**, **Contrib integrations**, and **Built-in
tags**. `docs_site/reference.yml` is the authoritative list. Scope is
`citry.*` only, with no `citry_core` Rust internals.

- *Slice 3a (done):* `reference.py` (griffe introspection into a render-ready
  structure: signature, docstring sections, parameters/returns/raises/
  attributes, nested members), the recursive `ReferenceSymbol` citry component
  (a class renders its members by recursing into itself), and the
  `<c-docstring path="citry.X" />` directive.
- *Slice 3b (done):* `reference.yml` (the current ordered categories and public
  symbols) plus `reference_pages.py` (strict loading, page generation via
  `<c-docstring>` / `<c-builtin>`, and the `reference` navigation source),
  the `extract_builtin` runtime introspection plus the `<c-builtin>` directive for
  the dynamically created `<c-*>` tags, build/serve generation of the 17
  category pages plus the Reference index, and `reference.css` for the
  `.doc-*` classes. A guard test asserts every category symbol resolves and that
  the categories cover all of `citry.__all__`.
- *Slice 3d (done): unified built-in tag reference.*
  `/reference/builtins/` is now the authored **Built-in tags** page. It covers
  all 15 public tags, groups them by task, and gives each one a stable
  `#c-<name>` anchor. The seven component-backed entries still use
  `<c-builtin>` and their runtime class docstrings. The eight syntax-backed
  entries use reader-oriented Markdown because they do not have one-to-one
  public Python classes: `IfNode` and `ForNode` each implement several tags,
  and `<c-raw>` does not become a runtime node.

  The generated Reference index and sidebar still own the category entry, but
  the generated page pass skips this path so the authored HTML, companion,
  metadata, sitemap record, and LLM projection remain consistent. The dev
  server makes the same distinction. The `builtin_tags` guard compares the
  page with `BUILTIN_COMPONENT_NAMES | STRUCTURAL_TAG_NAMES`, checks all 15
  anchors, and verifies that every runtime-backed entry resolves. The same
  category list supplies cross-references and `objects.inv` entries for all 15
  tags.
- *Slice 3c (done):* `crossrefs.py` - `[text][symbol]` resolution wired into
  both the content pipeline and docstring rendering (`reference._md`), with
  absolute reference URLs, the `[text][]` shorthand, member anchors, fenced-code
  skipping, and degrade-to-text for unknown keys; plus the Sphinx v2
  `objects.inv` written into the build so other sites can link in. (citry's
  docstrings do not use bracket refs yet, but the feature is ready for when they
  do.)
- *Slice 3e (done): authored browser API reference.*
  `/reference/browser-apis/` is the canonical Reference page for
  `$component`, Citry's eight Alpine magics, `Citry.alpine.beforeStart`, and
  the five public `Citry.events` methods. These contracts span a Python source
  transform and two browser runtimes, so they use reader-authored Markdown
  instead of pretending to be Griffe symbols. `ReferenceEntry` declarations
  provide canonical cross-reference keys, stable anchors, aliases, and Sphinx
  inventory roles. The `authored_reference` guard checks the declared browser
  surface against the page without locking prose into tests.

**Phase 4: re-enable parity. (Done, in five slices.)** The deferred features
are back on; the build now produces a deploy-ready site. Slices:

- *Slice 4.1 (done):* the build finishing spine. `build.build_site` collects an
  in-memory `PageRecord` per layout page (url, canonical, title, description,
  noindex, expanded markdown) that the later steps read instead of re-parsing
  the output. Added `minify.py` (a final HTML-shrink pass, inline-JS minify left
  off so JSON-LD stays valid, the last step that writes content HTML), a custom
  `404.html`, and `static_deps.export_runtime` (sets the `/citry` mount prefix
  and writes the client runtime to `<site>/citry/citry.js`, so a component's JS
  loads from flat files). The plain `build` minifies by default (`--no-minify`
  to skip).
- *Slice 4.2 (done):* SEO and AI-readable index files, all built from the page
  records. `seo.py` writes `sitemap.xml`, `robots.txt` (allow-all plus named AI
  crawlers plus the sitemap), and `meta/indexing.json`; `llms.py` writes
  `llms.txt` (nav-ordered) and `llms-full.txt` (concatenated page text);
  `redirects.py` carries an empty moved-URL map ready for the first rename. The
  `DocPage` head gained BreadcrumbList and TechArticle JSON-LD (escaped for safe
  `<script>` embedding, base path stripped from the trail), a default Open Graph
  / Twitter card image (front-matter `og_image` overrides), and a `/llms.txt`
  alternate link.
- *Slice 4.3 (done):* Pagefind search. `pagefind.py` runs the bundled binary
  over the built HTML; a `SearchModal` citry component plus the header trigger,
  the `data-pagefind-body` / `data-pagefind-weight` article hooks, the
  `djc-base-path` meta, and front-matter `searchable` / `boost` complete the
  wiring. The vendored `search.css` / `search.js` drive it; the 404 opts out of
  the index. `--no-search` skips the index.
- *Slice 4.4 (done):* subpath deploys and the version picker. `base_path.py` is
  the truly-last pass: it prefixes root-absolute URLs with the deploy base path
  (from `DOCS_BASE_PATH`) and is a no-op at the domain root. The `VersionPicker`
  component renders the current version seeded into a native `<select>`; the
  vendored site.js only fetches a version manifest when one exists, so a
  single-version build shows the control and does nothing.
- *Slice 4.5 (done):* the post-build guard suite. `guards/` ports the harness
  (`base`, `site_index`, `run_guards`, `format_report`, `make_context`) and 13
  guards (fence_validator, lexer_alias, code_lang, snippet_path, nav,
  example_contract, internal_link, anchor, asset, html_wellformed, single_h1,
  alt_text, headings). The `build-check` CLI builds to a temp dir and runs them
  (exit nonzero on an error, or any warning under `--strict`); `serve-built`
  builds and serves the static site over plain HTTP. The guards immediately
  found real reference-rendering defects (heading-level jumps and duplicate
  anchor ids), which were fixed: `ReferenceSymbol` headings are now depth-aware
  (h2 at the top, deeper for members), and reference anchors come from a single
  per-category map (`reference.reference_anchor_map`) that both the rendered
  pages and the cross-reference links read, so each page's ids are unique (a
  `Citry` class and the `citry` instance no longer collide) and every link
  matches its target id.

The now-portable guards were added once the features they check existed:
`json_ld` (validates the structured data), `api_symbols` (every documented
symbol resolves and every public export is on a page), and `redirect_target`
(a redirect stub points at a real page; a no-op until the first page moves).
That brings the suite to 16 guards; the only one still deferred is
`anchor_alias`, which needs a legacy-anchor scheme citry has no use for yet (no
symbol has been renamed). The suite passes clean, including under `--strict`.

Social-card images are now generated too (`social_cards.py` + the `OgCard`
component): for each indexable page the card is rendered to standalone HTML,
screenshotted to a 1200x630 PNG by a headless browser, content-addressed in a
persistent cache, and the page's `og:image` / `twitter:image` is rewritten to it
before minify. The browser is the optional `social-cards` extra (Playwright plus
`playwright install chromium`); when it is absent the step skips cleanly and
every page keeps the valid default card image, so a plain `docs`-extra build is
still deployable. `--no-social-cards` turns it off.

Multi-version is now in place too. `versioning.py` (on a vendored copy of mike's
version model under `_vendor/`) reads and writes the `versions.json` manifest,
stamps each snapshot's `_build_info.json`, and materializes alias redirects
(`latest/`). `build --docs-version <v> [--alias latest]` builds a snapshot into
`versions/<v>/` (canonicaling to `/v/<v>/...`, leaving the site-wide crawl files
to the root build), and `assemble` builds the current version at the root, mounts
the committed snapshots under `/v/`, writes the served manifest, and marks the
picker-bearing root versioned pages so their JS fetches it. Site-scoped pages
do not render the picker. The site starts at a single
version and the manifest grows as citry releases.

A snapshot shares the root build's `/static`, client runtime, and search index
(assembly rewrites its search attribute to the root build's configured
`search.pagefind_path`), which keeps the committed tree small. One consequence:
searching from inside an old `/v/<version>/` page
queries the current version's index, since per-version search (a `pagefind_path`
the picker would point at the snapshot's own index) is not wired yet.

### Content scope and deployment

The multi-version builder separates content lifecycle from build target.
`content/_nav.yml` declares `scope: versioned` or `scope: site` on an area,
group, or item; children inherit their owner's scope and omitted scope defaults
to `versioned`. The root build is not a scope: it contains the current copy of
versioned content plus all site content. A release snapshot contains only
versioned content.

Current ownership is:

| Surface or output | Owner |
| --- | --- |
| Project landing page at `/` | Site content declared by `home` |
| Docs, Examples, Reference, release notes | Versioned content |
| Community, Blog index, posts, and feed | Site content |
| Pagefind, sitemap, robots, LLM files, redirects, static files, Citry runtime, generated social cards | Root build |
| `/v/<version>/` trees and aliases | Committed release snapshots |
| Deploy artifact | Fresh root build plus copied committed snapshots |

Generated site areas or groups declare a stable `entry` item. A snapshot uses that item
for the root-site header link without loading the current generator input. Blog
therefore remains visible as `/blog/` in snapshots produced by this builder,
but current post metadata cannot make a historical documentation build fail.
The generated source's first fully hydrated item must match the entry. Blog is
intrinsically site-scoped; an omitted or contradictory scope is rejected.

Logical nav paths stay root-relative. During a snapshot render, versioned
targets are projected under `/v/<version>/` and site targets remain at the root;
the final base-path pass then prefixes both for project Pages. The same resolver
controls authored-page discovery, generated outputs, content assets, picker
visibility, sidebar and breadcrumb links, clean Markdown links, and generated
HTML links. The site-scoped project home is declared separately from visible
primary areas with `home: {title, path, scope}`. Its path must be `/` and its
scope must be `site`; Docs therefore starts at `/docs/`. Each snapshot writes a
home redirect to its first successfully built versioned page.
This changes the snapshot output contract, so new snapshots carry docs builder
version `1.1.0`. Their `_build_info.json` also records the site-route patterns
used during that build. The cross-version guard reads that frozen scope
manifest instead of reinterpreting historical links through today's
navigation. Changing an established route's scope is still a public migration:
review redirects, canonicals, assets, and version-picker behavior explicitly.

An ordinary push to `main` that changes Blog, Community, a landing page, or any
other site-scoped source runs the existing Pages workflow. `assemble` rebuilds
the entire root and its root-owned indexes, then mounts the already committed
snapshots unchanged. The host receives one atomic artifact; no partial upload
and no snapshot regeneration are required. Only a Citry release creates a new
snapshot. Historical snapshot chrome remains historical and is not dynamically
replaced with the current global navigation.

Shared root infrastructure is a deliberate size tradeoff, not full snapshot
isolation. Search from an old version uses the current Pagefind index and may
lead to current Docs, Community, or Blog pages. Old HTML also runs against the
current root CSS, JavaScript, and Citry runtime, so those outputs require
backward compatibility. Snapshots retain baked social metadata and do not get a
per-version generated card set. Per-version search, version-pinned shared
assets, and dynamic historical chrome remain deferred.

Landed but still requiring first-release authorization review: the disaster-recovery
`build-all` (rebuild every
release tag via git worktrees), the two version-tree guards (`versions_manifest`,
`cross_version_link`) with a `versions-check` command, and the
`repo--docs-release.yml` workflow that on a `citry@X.Y.Z` tag builds that version
from the exact tag commit in a detached worktree, stages and registers it under
`versions/<v>/`, runs the guards, commits it from `main`, and then assembles the
current root from `main`. Each detached checkout gets a locked docs environment
with the tagged Citry and Citry UI packages selected explicitly. A manual
`release_tag=citry@X.Y.Z` dispatch provides the same immutable-tag path for
recovery without moving a published tag. Commit-back authorization for a protected default
branch remains the release blocker. Still deferred: the
ephemeral per-deploy `dev` snapshot, and per-version search (a `pagefind_path`
the picker would point at the snapshot's own index).

### Chrome parity: a correction to the "full parity" claim above

The Phase-4 "re-enable parity" framing measured parity by "the feature module
exists", not by rendering the full site, and it overstated the DocPage chrome. A
later audit against the reference site found that the vendored `site.js` /
`site.css` ship byte-identical to upstream, but the hand-re-authored DocPage had
silently dropped several of the markup hooks they bind to, so those behaviors
were inert. The guard suite did not catch this because the guards check content,
links, and anchors, not the presence of chrome elements. The following were
found missing and have since been restored:

- The **right-rail table of contents was empty on every reference page** (and on
  every content page without `##` sections). The reference symbols are injected
  as raw HTML, which python-markdown's `toc` extension never sees, so the rail's
  `toc_tokens` held only the page H1. The fix ports the upstream heading-merge
  pass as [`toc.py`](../../docs_site/_internal/toc.py) (`merge_html_headings_into_toc`
  re-parses the rendered HTML with lxml to recover those headings), called in
  `pipeline.render_page` after the markdown pass; and moves the anchor id onto
  the `ReferenceSymbol` heading (with a `doc-object-name` span and a
  `doc-symbol-<kind>` badge) so the merge can find and label it.
- The **right-panel drag-resize handle**, the **mobile "On this page"
  disclosure** (`djc-toc-mobile`), the **header overflow menu** (`djc-overflow`,
  which held the only theme/version controls below 768px), and the **sidebar
  drawer top-nav** (`djc-sidebar__topnav`) were all dropped markup. Each is
  re-added to the DocPage template, and `_flatten_toc` now carries the symbol
  `kind` and a `collapsible` flag so the TOC shows the type badges and the
  member-folding toggle the vendored CSS/JS already support.

The **prose content is now ported.** Rather than translate the upstream pages
(which document Django-specific django-components), citry's own docs were authored
from its real API: ~29 content pages across getting started, template syntax,
concepts, advanced, and the standalone CLI / web-frameworks / security pages,
replacing the five earlier pages (two of them stubs). Every page was grounded in
a verified per-subsystem fact sheet, and every code example was executed through
the live citry engine, so the shown code actually runs (this caught the
`{{ len(...) }}`-in-a-template pattern the README's own first example uses, which
raises `KeyError` because builtins are not available in expressions).

Workstream B is also built now: the **`<c-image>` and `<c-people>` tags** (each
in its own file under `docs_site/_internal/components/`, beside the component it renders) and the
**`UserGrid`** ship (with a
seeded `data/people.yml` and a `docs_site/scripts/people.py` generator), and the
**Examples cookbook** grew from one example to nine, each with its own authored
recipe and a Citry-native standalone demo verified against the live engine
(card, control flow, slots, provide/inject, tabs, error boundary, recursion,
form submission, and fragments). `_nav.yml` declares Examples as a primary
area, then groups and orders the recipes within it. Two
needed extra handling. The form submission simulates its server
POST client-side by intercepting the submit. The **fragments** demo needed the
smallest bit of new build support: citry's `fragment` strategy loads a
component's JS/CSS on demand by URL, but the static build only wrote the shared
runtime (`static_deps.export_runtime`), not the per-component fragment deps (the
default `document` strategy inlines them, so nothing else referenced them by URL).
Following the DJC shape (pre-render each variant to a static endpoint), Citry
places variants below `examples/<slug>/demo/<variant>/`. The only
citry-specific glue is
`static_deps.export_fragment_deps` writing the fragment component's two
class-level dep files, plus a `FRAGMENTS` declaration on the example; the whole
path is browser-verified in `test_docs_e2e.py`. The `people.yml` generator that
refreshes contributors from the GitHub API is built now too (see Phase 6).

That prose summary is backed by a full feature-by-feature audit. The
228-row upstream catalogue is copied verbatim to
[`docs_site_feature_inventory.md`](docs_site_feature_inventory.md), and
[`docs_site_parity_audit.md`](docs_site_parity_audit.md) records citry's real
status for every row as of 2026-07-02 (read from the code, with `file:line`
evidence): 99 ported, 25 partial, 33 missing, and 71 that do not apply to citry
(Django-repo-specific). Its "remaining work, grouped" section is the ordered
to-do list; workstreams A (content port) and B (directives and example gallery)
are now done, so the next gaps are the git-metadata subsystem and the
multi-version SEO plumbing (workstreams C and D).

To stop this class of "the module exists so it must work" gap from recurring,
the docs site now has a browser end-to-end suite
([`docs_site/tests/e2e/`](../../docs_site/tests/e2e/)): a session fixture builds
the real site (search index and all) and serves it, and the tests drive it in
Chromium to assert no broken assets, a populated reference table of contents,
both resize handles, working search, theme switching, active nav, and the mobile
overflow menu. Each one is a regression guard for a bug that shipped because it
was only ever checked in isolation.

**Phase 5: CI and deployment to GitHub Pages. (Done.)** Two workflows, named in
the repo's `repo--*` family (the docs live at the repo root, not under
`packages/py/`), both reusing the standard job preamble (checkout with
`submodules: recursive`, setup-uv, Python 3.13, the nightly Rust toolchain plus
`Swatinem/rust-cache`, then `uv sync --locked --all-packages`, because the docs
import `citry`, which the maturin backend builds during the sync):

- [`repo--docs-check.yml`](../../.github/workflows/repo--docs-check.yml): the
  docs gate. On pushes/PRs that touch the docs or the API they document, it
  installs the `docs` extra, runs `python -m docs_site build-check` (fails on a
  render failure or a guard error), then the docs-site test suite. A second job
  (`docs-e2e`) additionally installs the `e2e` group and a Chromium binary and
  runs the browser suite in [`docs_site/tests/e2e/`](../../docs_site/tests/e2e/).
  These are not covered by the main gate (`scripts/check.py`) or the package test
  workflows, so this is their dedicated CI.
- [`repo--docs-deploy.yml`](../../.github/workflows/repo--docs-deploy.yml): the
  Pages deploy (the `upload-pages-artifact` + `deploy-pages` model, not a
  `gh-pages` branch push). On pushes to `main` (or on demand) a build job
  installs the `docs` + `social-cards` extras, runs
  `playwright install --with-deps chromium`, caches the content-addressed cards,
  runs `python -m docs_site assemble` into `site/` (current version at the root,
  committed `versions/` snapshots under `/v/`, newest `publish_window` of them),
  and uploads the artifact; a deploy job with the `github-pages` environment and
  `pages: write` / `id-token: write` publishes it, under a `pages` concurrency
  group. Social cards render here because this is the one path that installs the
  browser; every other build keeps the default card.

  This same path handles editorial-only site updates. It rebuilds root content
  and root-owned generated files, remounts committed `/v/` snapshots without
  regenerating them, and publishes one atomic artifact.

The public URL and subpath are env-driven (`DOCS_SITE_URL`, `DOCS_BASE_PATH`), set
in the deploy workflow: the default targets the `citry.dev` custom domain at the
root, with a documented switch to project Pages (`/citry` base path). One-time
operational setup: repo Settings -> Pages source = GitHub Actions (and the custom
domain, if used). The gate and the deploy are separate workflows, mirroring the
repo convention that publishing is not gated on the test workflow; a branch-
protection rule requiring `repo--docs-check` keeps a guard-failing site off
`main`.

**Phase 6: docs maintenance automation. (Pending, not started.)** Scheduled and
change-time checks that run against the deployed site, ported from
django-components' `maint-docs-*` workflows. All follow Phase 5 (they need the
deployed site). These sit alongside checks citry already has: deployment is
Phase 5, and build-time internal-link and anchor validation shipped in Phase 4
slice 4.5 (the `internal_link` and `anchor` post-build guards), so neither is
repeated here.

- *Lighthouse CI.* A `.github/lighthouserc.json` plus a workflow that audits a
  handful of key pages for performance, accessibility, best practices, and SEO
  on docs changes, failing under set thresholds. Catches perf and accessibility
  regressions the post-build guards do not. (Upstream:
  `.github/workflows/maint-docs-lighthouse.yml`.)
- *External-link health.* A scheduled job (e.g. lychee) that walks the built
  site for broken *external* URLs (link rot). Distinct from the existing
  `internal_link` / `anchor` guards, which validate on-site links and anchors
  only. (Upstream: `maint-docs-external-links.yml` plus `scripts/validate_links.py`.)
- *Contributor-recognition data. (Done.)* [`docs_site/scripts/people.py`](../../docs_site/scripts/people.py),
  ported from the upstream script, counts merged PRs across **both** citry and
  django-components and merges the totals (citry continues django-components, so
  a contributor to either is credited), writing `docs_site/data/people.yml` that
  the `<c-people />` component renders. Repository order, featured people, and
  ignored bots are declared in `docs_site/people_sources.yml`. The
  [`repo--docs-people.yml`](../../.github/workflows/repo--docs-people.yml)
  workflow runs it monthly and opens a PR when the data changes. Built now rather
  than deferred, because the django-components merge means there is already a real
  contributor set to recognize.

**Phase 7: proper content authoring (Diataxis rewrite). (Pending, not started.)**
The controlling research and execution plan for this phase now lives in
[`docs_content.md`](docs_content.md). It also controls the public-docstring work
previously tracked as Phase 9. The notes below are a dated historical record,
including stale page counts and status language. Use the dedicated content plan
for current scope, evidence, reader, migration, and verification rules.

The Phase 3b content port stood up citry's own docs (~29 pages) grounded in a
verified fact sheet per subsystem, with every code example executed through the
live engine. That reached accurate, complete coverage, but it was not a writing
pass: the pages were drafted from API facts, not shaped around who is reading and
why. This phase is the deliberate authoring pass. Approach:

- **Diataxis across the three surfaces.** Use all four modes without forcing
  them back into one Docs tree: tutorials and explanations belong primarily in
  Docs, code-first how-to material belongs primarily in Examples, and public
  API lookup belongs in Reference. A page may combine modes where the reader's
  task requires it, but the content-authoring pass must preserve the distinct
  roles in the 2026-07-25 decision record below rather than rebuilding one flat
  "concepts" pile.
- **Personas and tone.** Define the reader personas (the Python/web engineer
  evaluating citry, the developer mid-build looking one thing up, the
  contributor). Pick a tone per page/section for its audience; several tones
  across the site is correct, not inconsistent. Personas give a concrete frame of
  reference for who each page is written to.
- **Component reuse pages.** The Advanced authoring pass separates two reader
  jobs: `Component libraries` covers packaging and publishing reusable
  components, while `Custom component values` explains the `ComponentLike`
  integration contract. Both keep implementation detail behind the task it
  helps the reader complete.
- **Intent-driven and concise.** Every reader arrives with a reason. Lead them to
  it and respect their time. Avoid jargon. Cut anything that does not serve the
  reader's goal on that page.
- **Progressive disclosure.** Surface the common path first; tuck depth, edge
  cases, and internals behind later sections or dedicated pages.
- **No meta-talk, internal leaks, or empty statements.** Two concrete bad
  examples from the Phase 3b home page: "The engine is a single Rust core with
  Python bindings today, and JavaScript, PHP, Go, and Rust to follow" (a
  first-time visitor came for a Python frontend framework; the other-language
  roadmap belongs in community/contributing docs, not the welcome page), and
  "This very page is rendered by Citry (version X): the docs site dogfoods the
  engine it documents" (irrelevant to the reader's goal on a high-traffic page;
  fine as a fun fact somewhere low-traffic, not on the landing page).
- **Fact extraction, file by file.** Before rewriting, sweep the whole codebase
  (and the existing docs) file by file, and where needed line by line: for every
  docstring, inline comment, markdown line, and code line/block, decide whether it
  is internal or something a user should know, and capture each user-facing item
  as a "fact" to document. Assemble the facts across all files first, then revisit
  the site's concepts and pages and build them out of the fact set. This is the
  Phase 3b fact-sheet discipline applied exhaustively and used to drive structure,
  not only accuracy.
- **Section titles: short and direct.** Flowery titles overflow the right-rail
  table of contents (observed). Prefer the shortest title that names the thing:
  "The each clause is a real comprehension" becomes "`each` clause"; "The loop
  variable is only what you name" becomes "loop variables".
- **Code-block formatting conventions** (apply to every example):
  - One blank line between sections of a small example, not two. The standard
    two-blank-line separation wastes vertical space in a focused block, and the
    blocks are already tightly scoped.
  - Inside a component's inlined `template` / `js` / `css` string, indent the
    contents two spaces and use two-space indentation throughout the string body
    (the surrounding Python keeps four-space). This separates the embedded
    HTML/JS/CSS from the Python around it.
  - Construct components with one keyword argument per line, not all on one line.
  - Write nested HTML tags on their own indented lines, not run together.
  - Keep inline code comments to roughly 55 to 60 characters per line so they do
    not force horizontal scrolling.
  - When a component declares a nested `Kwargs` class, annotate the data method's
    parameter with it (`def template_data(self, kwargs: Kwargs, slots): ...`).
    Python then infers each field's type, so `kwargs.title` is known to be `str`
    inside the method: the examples type-check, and the field types are visible
    inline without a separate lookup.
- **Specific content fixes to fold in:**
  - `/advanced/dynamic-components/`: drop the `Citry` instance `c` that the
    examples create and assign but never meaningfully use. Include an engine
    instance only when it is relevant to what the example teaches.
  - `/advanced/extensions/` "Hooks": it opens with "Each hook takes one frozen
    dataclass context" before the reader knows what a hook is or why to care.
    Motivate first (what hooks are for, why you would reach for one), then the
    mechanics.
  - Extensions: add the per-component extension config pattern. The page shows
    reading config (`self.view.title()`) but not setting it for one component: a
    component can define a nested class (e.g. `Page.View`) to override an
    extension's config for just that component.
  - CLI/terminal invocations (e.g. `citry ext run greeter greet`) belong in
    fenced code blocks, not inline code spans.
  - Navigation grouping has since landed: `Web frameworks` is under Guides,
    `Command line` is under Advanced, and `Security` is under About.
- **Open questions to settle here:** whether reference-page ToC members
  (attributes/methods) should be sorted alphabetically or keep source order
  (check what comparable frameworks do), and whether to reorder the reference
  categories in the nav.

### Future information architecture and editorial roles (decision record, 2026-07-25)

**Status:** The role of Examples is decided. Blog is implemented according to
[`docs_blog.md`](docs_blog.md). The placement/name of the Citry UI catalog
remains open. The Examples theme problem is a confirmed bug.

#### Keep Examples as the code-first cookbook

The Examples surface is permanent. Citry UI may make individual low-level
examples such as Card or Tabs less valuable in their current form, but it does
not make the Examples *role* redundant. Reassess, replace, or move individual
recipes when Citry UI lands rather than removing the Examples area.

The three documentation lenses have distinct jobs:

- **Docs** are for onboarding, concepts, user journeys, and long-form narrative
  explanations. They should explain why and when a feature matters before
  teaching all its mechanics.
- **Reference** is the orderly description of Citry's public API. Its structure
  follows the product/API rather than a user's journey.
- **Examples** are the cookbook and quick how-to reference. They lead with code:
  "here is how to do X", followed by links to the relevant Docs and Reference
  material for the complete explanation.

Grow Examples beyond the current component demos. Candidate families include:

- one group for **Web frameworks**, with dedicated Django, FastAPI/Starlette,
  Flask, ASGI, WSGI, and other integration recipes;
- one group for **Alpine**, with a focused page for each supported Alpine magic
  or integration pattern;
- cross-cutting recipes for passing JavaScript/CSS data, events, fragments,
  dependencies, state, and other common tasks; and
- richer showcase applications such as games, public-data dashboards,
  visualizations, spreadsheets, and creative tools. The candidate portfolio,
  data/asset requirements, and landing-page selection contract live in the
  [landing-page design](docs_landing_page.md#example-showcase-backlog).

The final taxonomy and the relationship between gallery cards, recipe pages,
and standalone live demos remain implementation questions. Every recipe should
still be runnable/tested and should point readers toward the deeper Docs and API
Reference pages instead of duplicating them.

Examples owns each showcase's runnable code, canonical page, showcase manifest,
and generated preview. The project landing page selects example IDs and order
for a small accepted subset, but it must link back to Examples rather than
becoming a second source for the title, demo, attribution, or explanation. The
manifest and landing selection contract are defined in the
[landing-page design](docs_landing_page.md#landing-page-selection-contract).

#### Add Blog as a top-level area

**Implemented 2026-07-28.** **Blog** is the rightmost primary-navigation item,
immediately to the right of Community. Its purpose is long-form project updates
that do not belong in the evergreen Docs narrative.

Blog content lives at `docs_site/content/blog/`, consistent with the rule that
user-facing pages live under `docs_site/content/`. Its index, stable URL/date
scheme, author metadata, tags, Atom feed, generation, and version-isolation
rules are defined in [`docs_blog.md`](docs_blog.md).

Adding the Citry UI catalog would grow the now five-link primary navigation to
six links. Re-run the narrow-desktop overlap range covered by
[`test_desktop_primary_navigation_does_not_overlap_actions`](../../docs_site/tests/e2e/test_docs_e2e.py)
and the mobile drawer checks when either link lands. Adjust the collapse
breakpoint or overflow behavior rather than allowing the header links and
actions to compete for space.

#### Add the Citry UI catalog near Examples

When `citry-ui` is introduced to the site, give its component catalog a
top-level navigation link adjacent to Examples. Whether it sits immediately to
the left or right of Examples remains open. **UI Kit** is a candidate label
because it is shorter and more user-oriented than **Components**, following the
naming used by [Django Cotton](https://django-cotton.com/ui); choose the final
label when the catalog is designed.

The catalog sidebar can take organizational inspiration from
[Vuetify's components catalog](https://vuetifyjs.com/en/components/all/). This
is an information-architecture reference, not a requirement to copy Vuetify's
visual design. Define how UI Kit pages and general Examples cross-link before
deciding whether current Card/Tabs recipes move, narrow their focus, or stay as
framework-level examples.

The public catalog should consume Citry UI's accepted
[Python scenario catalog](ui_research/scenario-catalog.md) and canonical
component examples rather than creating a competing scenario format or
duplicating hand-authored snippets. The docs site's live-component host is the
first-party public preview surface. Standalone routes remain quality and
debugging surfaces, as defined in the [Citry UI plan](ui_library_plan.md).
Storybook is a separate optional contributor extension tracked in
[`extensions_storybook.md`](extensions_storybook.md).

#### Fix Examples theme compatibility

The current Examples code presentation is unreadable in some dark-theme states
because dark text is rendered on a dark background. Audit the gallery/card code
panes and source tabs first, then confirm whether standalone iframe demo pages
share the problem. The fix should cover explicit light, explicit dark, and
automatic system themes, use shared theme tokens, and gain a browser regression
check for readable foreground/background colors.

### Cleanup notes (TODO)

- `/advanced/extensions/` - List all Extension here for a high-level overview, because going through them in the reference page is not easy.

- re docstrings - preferably, most of public API symbols should include usage examples in their docstrings, so that the usage examples show up in the reference too.

- The primary navigation is declared entirely by the top-level `areas` in
  `_nav.yml`: Docs, Reference, Examples, Try it, Citry UI, IDE, Community, and
  Blog. Header order, active area, scoped sidebar, breadcrumbs, and prev/next
  navigation all use that tree. Reference and Release notes use explicit
  generated sources in the same declaration. Blog uses the generated `blog`
  source. Item review state and area badges remain structured navigation
  metadata so page titles stay clean for every other consumer.

- Keep About. It contains Compatibility, Benchmarks, and Security. Command line
  lives under Advanced.

- Add a new "Commands" section to "Reference"

- Within Docs, "Web frameworks" should become a section (not a single page).
  This is distinct from the code-first Web frameworks group proposed for Examples.
  - One overview page for how Citry integrates with web frameworks / what it is.
  - Then per-integration pages (Django, FastAPI/Starlette, Flask, WSGI, ASGI, etc...)

- Re "Maintainers" on people page - swap maintainers - put Juro first.

- Re order of attributes/methods in refernce APIs (eg class' methods and attrs) - the order seems random - is the order taken as is from the codebase? Should we sort by kind (attrs first, then methods), and within kinds sort alphabetically? (that's how djc did it).

- Fix `127.0.0.1:59951 - "GET /pagefind/pagefind.js HTTP/1.1" 404 Not Found`

- Merge `docs_site_content_port_audit.md` into `docs_site_parity_audit.md`

- Set up `DOCS_GOOGLE_SITE_VERIFICATION`

**Phase 8: citry syntax highlighting (Pygments lexer). (Pending, not started.)**
Port django-components' Pygments integration so docs (and any Pygments user) can
write ```` ```citry ```` fenced blocks. A `citry` lexer highlights the Python
component as Python, and additionally highlights the HTML, JS, and CSS embedded in
the `template` / `js` / `css` strings (and the `<c-*>` tag syntax), instead of
rendering those strings as flat Python string literals. Upstream shipped this as
the `pygments_djc` plugin lexer loaded at command startup (inventory feature 1.5,
marked N/A for citry until this lexer exists). Wiring: register the lexer as a
Pygments plugin, load it in the docs build, and switch the ```` ```python ````
component examples to ```` ```citry ```` where the embedded markup benefits.

**Phase 9: public API docstring pass. (Pending, not started.)** Rewrite every
public API docstring (the ones griffe renders into the reference pages) in the
same spirit as Phase 7: intent-driven, concise, no jargon, no internal leaks,
written for the reader who meets the symbol in the reference. Apply the same
file-by-file fact-extraction discipline: a docstring is user-facing surface, so
decide what the reader needs and cut what is internal. This covers the generated
reference layer that the Phase 7 prose pages link into.

The controlling scope, order, evidence rules, and review gate for this work are
now in [`docs_content.md`](docs_content.md), especially Stage 7. This paragraph
is retained only as the historical phase record.

Phase order is guided by dependency and is flexible; each phase ships
something runnable.

---

## Open risks and dependencies

- **Content carries Django-isms.** The inline-tag transform is mechanical, but
  example pages use Django-only constructs (`{% lorem %}`, kwarg syntax like
  `attrs:class=...`, `types.django_html`) that need citry equivalents or
  removal.
- **New dev-only dependencies.** griffe, python-markdown + pymdownx, Pagefind,
  minify-html, lxml. All optional/dev (the `docs` group), none shipped in the
  `citry` wheel.

---

## `_djc_reference` and upstream reconciliation

`_djc_reference` is a snapshot of the django-components *package source*
(`django_components/*.py`) that the design docs reference as the migration
source. It is a different tree from the docs site, which was never vendored
here before Phase 0.

Phase 0 settled the open questions: the snapshot is **gitignored** (which stops
the `git status` nag), with provenance and reproducibility held in the tracked
[`scripts/vendor_djc_reference.sh`](../../scripts/vendor_djc_reference.sh), and
it was **fully re-vendored** to the current upstream commit.

The re-vendor changed 10 of the 75 engine files (none added or removed):
`app_settings`, `cache_tag`, `component`, `component_registry`, `extension`,
`node`, `provide`, `slots`, `templatetags/component_tags`, and
`util/django_monkeypatch`. The design docs reference these by file name (and
sometimes a line *count*), not by line *anchor*, so the drift surface was
narrow. A verified sweep (run before Phase 1) closed it:

- **Line counts corrected** in [`migration_djc.md`](migration_djc.md): 12
  updates across the changed files (for example `component.py` 3657 to 3620,
  `slots.py` 1698 to 1688).
- **Per-file verdicts confirmed intact.** All 10 changed files differ from the
  old snapshot only cosmetically (docstring link-syntax, doc-path pointers in
  comments, one import reorder, one deleted TODO comment); no structural or
  behavioral change. An adversarial verification pass flagged zero stale
  claims, so every June 2026 verdict still holds.

The other 65 files are byte-identical to what the docs were written against, so
their references need no change.

For the docs-site port specifically, `docs_site/` is vendored as its own
read-only reference (`_djc_reference_docs_site/`) next to `_djc_reference`, so
the engine snapshot and the docs-site snapshot stay separable.
