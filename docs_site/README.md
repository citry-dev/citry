# Citry documentation site

This directory contains the source and build system for
[citry.dev](https://citry.dev/). The deployed site is static. Citry renders the
Markdown and components, then the build writes HTML, assets, search data, SEO
files, Markdown companions, LLM navigation, examples, generated API Reference
pages, and authored Reference pages for non-Python public APIs.

Run every command in this README from the repository root.

## Where to make changes

| Path | Purpose |
|---|---|
| `content/` | User-facing Markdown pages and `_nav.yml` navigation |
| `examples/` | Runnable source, standalone demo pages, and example tests |
| `live_snippets/` | Complete browser-runnable modules used by opt-in live code blocks |
| `snippets/` | Source included in Markdown with `--8<--` |
| `static/` | Site-owned CSS, JavaScript, fonts, and images |
| `data/` | Content data such as the generated People listing |
| `scripts/` | Docs-specific maintenance scripts |
| `versions/` | Committed, generated snapshots of released documentation |
| `tests/` | Build, render, guard, and browser tests |
| `_internal/` | The site builder and its private components |
| `settings.yml` | Site identity, links, Markdown profiles, and product policy |
| `reference.yml` | Ordered Reference pages, Python symbols, and authored API anchors |
| `ui_library.yml` | Functionally grouped Citry UI source pages and public routes |
| `redirects.yml` | Published clean-URL redirects |
| `people_sources.yml` | People-generator repositories, featured people, and ignored bots |
| `data/community_packages.yml` | Reviewed packages shown on the Community extension and UI-library pages |
| `docs_versions.yml` | Version selection and publication policy |

Most content work belongs in `content/`, `examples/`, `snippets/`, `static/`,
or `data/`. Changes under `_internal/` change the documentation product or
build system. Components should follow the repository's
[component-authoring conventions](../docs/best-practices/component-authoring.md).

## Edit navigation

`content/_nav.yml` is the single source of truth for site navigation. Each
top-level entry under `areas` becomes a header link, in YAML order. Its direct
`items` and nested `groups` become that area's sidebar. The first resolved page
is the header link's destination.

Docs and Examples combine direct overview items with grouped pages. Community
uses direct items. Generated entries stay explicit through named sources:

```yaml
home:
  title: Citry
  path: /
  scope: site

areas:
  - label: Docs
    scope: versioned
    items:
      - { title: Overview, path: /docs/, needs_review: true }
    groups:
      - label: Release notes
        source: releases
        collapsible: true
        section_style: true

  - label: Reference
    scope: versioned
    source: reference

  - label: Community
    scope: site
    items:
      - { title: People, path: /community/people/ }

  - label: Citry UI
    badge: alpha
    items:
      - { title: Overview, path: /ui-library/ }

  - label: Blog
    scope: site
    source: blog
    entry: { title: All posts, path: /blog/ }
```

`source: releases` fills its group from `CHANGELOG.md`.
`source: reference` fills its area from `reference.yml`.
`source: ui_library` replaces the Citry UI Components placeholder with the
functional groups from `ui_library.yml`; each component page's front matter
supplies its title and description.
`source: blog` fills its area from the dated Markdown posts under
`content/blog/`, newest first, with **All posts** at the top.
Groups in the Docs area set both `collapsible: true` and
`section_style: true`. They start closed on the Docs overview so the growing
category list stays easy to scan. The group containing the current page opens
automatically, and readers can open or close the others without hiding the
active link. Their choices persist in local storage. Groups in other areas may
stay open or opt into either presentation as their navigation requires.
Adding an ordinary top-level area needs no Python or template change: add the
area and its pages to `_nav.yml`.

Set `needs_review: true` on an item that has not completed final human review.
The sidebar adds the `🚧` marker and an accessible explanation while keeping
the plain `title` for breadcrumbs and previous/next links. Do not put the
marker in `title`. An area can carry a short plain-text `badge`, such as the
Citry UI `alpha` label; the header, mobile drawer, and active sidebar render it
consistently.

The optional top-level `home` declaration owns `/` without creating a visible
header area. It must declare the root path and `scope: site`. This keeps the
project landing page current while the Docs header item can point to the first
versioned documentation page. Repositories that omit `home` retain the older
area-owned root behavior.

### Choose a content scope

Navigation also declares publication scope. `scope: versioned` means the page
is part of each documentation release; `scope: site` means there is one current
copy at the site root. Omitted scope defaults to `versioned`. Areas pass their
scope to groups and items, which can override it for a mixed area. This lets a
future project landing page remain current while the documentation below it is
frozen per release.

The current policy is:

| Content | Scope |
|---|---|
| Project landing page | `site` |
| Docs, Examples, Reference, and release notes | `versioned` |
| Community and Blog | `site` |

Blog is intrinsically site-scoped. Its generated area declares `entry` so a
snapshot can render the root `/blog/` header link without reading or validating
current posts. A generated source's first resolved item must match its declared
entry. Unknown navigation keys and unknown scope values fail the build, so a
scope typo cannot silently publish content into snapshots.

A root build is not the same thing as site scope. It contains the current copy
of versioned content plus all site-scoped content. A snapshot contains only
versioned content. In snapshot HTML, links to versioned pages are projected
under `/v/<version>/`; links to site pages remain at the root. Shared
`/static/`, `/citry/`, and the configured Pagefind output also remain
root-owned. During assembly, mounted snapshot pages are rewritten to load that
root Pagefind bundle, so changing its configured directory does not strand
historical versions on an old asset URL.
Content assets inherit the unanimous scope of their first route segment. Keep a
content-asset directory within one scope; put site-global assets under
`static/`. An unknown or mixed asset namespace defaults to `versioned` so the
builder does not silently drop an existing file.

### Edit the project landing page

The project landing page lives in `content/index.md` and uses
`layout: landing`. Its distinctive field, page styling, and small interactions
belong to `_internal/components/landing.py`, so the page demonstrates the same
component-owned HTML, CSS, and JavaScript model it describes. The ordinary
documentation overview lives in `content/docs.md` at `/docs/`.

The landing layout keeps the shared header, search, SEO metadata, Markdown
companion, and LLM output. It deliberately omits the documentation sidebar,
breadcrumbs, page table of contents, and previous/next navigation. Keep all
meaningful copy in `content/index.md`; JavaScript may enhance it but must not be
required to read it or follow its primary actions.

### Add an inline live example

Reference one complete Python module anywhere in the repository. Keep reusable
reader-facing examples under `docs_site/live_snippets/` by convention, then
reference the canonical file from Markdown:

```html
<c-live-code
  path="docs_site/live_snippets/welcome.py"
  title="Welcome card with State and Events"
/>
```

Add the value-less `full_height` kwarg when the static code block should show
the complete file without its default 32rem height cap:

```html
<c-live-code
  path="docs_site/live_snippets/welcome.py"
  title="Welcome card with State and Events"
  full_height
/>
```

Readers initially receive a normal highlighted code block. **Try live** loads
the editor and browser runtime only when selected. Markdown companions, search,
and LLM exports retain the source without the controls. Released version pages
remain static even when their source contains this tag.

Component-library pages may also project a repository-owned snippet from
`packages/py/citry_ui/citry_ui/components/<family>/snippets/<name>.py`. Add the
value-less `static` kwarg while that source depends on a package unavailable in
the browser runtime:

```html
<c-live-code
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/night_sky_guide.py"
  title="Night sky guide"
  static
/>
```

This keeps the canonical source beside the component and uses the same
highlighting and text projection without offering a broken activation control.
The live authoring server builds the workspace `citry` and `citry-ui` wheels
and automatically enables these component snippets in the browser. Keep
`static` in committed content until `citry-ui` is part of the published
playground runtime. Static builds and `build-check` intentionally use that
published package set.

The path may name any Python file in the repository, including after resolving
symlinks. The module must be UTF-8 with LF line endings and no larger than 64
KiB. Keep imports within Python's standard library or the active browser
runtime's package allowlist. `build-check` validates the directive and source
before rendering and reports the Markdown line for an invalid tag. It permits
a module without a final preview value so readers can activate an incomplete
example and edit it into a renderable one. Running that source reports the
missing value in the live editor until the reader adds one. Do not duplicate
the module in a Markdown fence.

When the same file should also print its result as a normal script, keep one
value for both environments:

```python
example = ExamplePage()

if __name__ == "__main__":
    print(example)

example
```

Python prints the value through the `__main__` block. The final expression is
otherwise harmless, and it gives the browser executor the value to preview.

### Add a Citry UI component preview

Citry UI component pages use a result-first preview when the reader needs to
see and operate a component before opening its source. Keep the canonical
module beside its component and reference it from that family's `api.md`:

```html
<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/night_sky_guide.py"
  title="Night sky guide"
/>
```

The path must stay under the same component directory as the declaring
`api.md`. The module exposes a component-like value as `preview` and ends with
that expression:

```python
preview = NightSkyGuide()

preview
```

The preview value must use Citry's default instance, matching the browser
snippet runtime and the standalone preview document that the builder owns.

Add host-owned controls with an optional `preview_controls` tuple:

```python
preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "underline",
        "options": (("underline", "Underline"), ("pill", "Pill")),
    },
    {
        "name": "disabled",
        "label": "Disable all Tabs",
        "type": "checkbox",
        "default": False,
    },
)
```

The builder validates control names, labels, defaults, and options. It renders
the controls in an open, collapsible section between the demo header and
preview. They are documentation tooling, not rendered component content.

The host sends current values to the sandboxed preview. Handle them on the
preview root:

```citry-html
<section
  x-data="{ variant: 'underline', disabled: false }"
  @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
>
  ...
</section>
```

Controls must map to documented component inputs or CSS variables. The current
schema supports `select` with `(value, label)` options and `checkbox` with a
Boolean default.

The docs builder derives
`/ui-library/components/<slug>/_previews/<module-name>/` from the catalog and
filename. It renders that private document ahead of deployment and places it
before a collapsed, highlighted source disclosure. Private preview documents
are excluded from navigation, search, sitemap and LLM page records, while the
owning page's Markdown companion and LLM projection retain the canonical source
and a link to the rendered result.

Rendered content uses a slightly smaller type scale and the same light/dark
surface as docs code blocks. The parent page sends only the resolved theme name
to the sandboxed preview; the iframe does not gain same-origin access.

Do not add a second route declaration or a copy under `docs_site/content/`.
The local authoring server adds **Try live** and loads this exact source into
the shared inline editor only after activation. Deployed docs omit the action
until a published `citry-ui` wheel is pinned in the browser runtime; the built
preview and source remain fully usable without it.

## List a Community package

The manually reviewed package catalog lives in
`data/community_packages.yml`. One entry may use either or both supported
categories:

```yaml
schema_version: 1
packages:
  - distribution: example-citry-package
    name: Example package
    categories:
      - extension
      - ui_library
    summary: One plain-text sentence explaining the package's job.
    ownership: community
    published: true
    citry_requirement: ">=0.4.0,<0.5.0"
    source_url: https://github.com/example/example-citry-package
    docs_url: https://example.test/docs/
    maintainer: "@example"
    maintainer_url: https://github.com/example
    notice: Optional plain-text maturity, licensing, or support disclosure.
```

Use `ownership: official` only for Citry-maintained packages. Set
`published: false` for a source-only preview; the page then omits the PyPI link
and installation command. `docs_url`, `maintainer_url`, and `notice` are
optional. Use `notice` when a material maturity, licensing, or support fact
must stay visible on both the rendered card and its Markdown projection. All
other fields are required.

Open a pull request for every addition, change, or removal. Maintainers verify
the package category, ownership, public source, declared Citry compatibility,
publication state, license intent, and factual summary. A `citry-` name or
package keyword may help discovery but never grants inclusion. The complete
governance rules and the future reporting-only automation design live in
[`docs_community_packages.md`](../docs/design/docs_community_packages.md).

The two authored pages contain one directive each:

```html
<c-community-packages category="extension" />
<c-community-packages category="ui_library" />
```

The catalog is current site content. Root builds validate it before replacing
output, while version snapshots neither read it nor copy the Community pages.

## Publish a Blog post

Blog sources live in `content/blog/`. Keep `index.md` as the only undated file
and name each post `YYYY-MM-DD-lowercase-kebab-slug.md`. The date prefix keeps
source files sortable, while the public URL omits it. For example,
`2026-07-27-project-update.md` is published at `/blog/project-update/`.

Every post starts with strict front matter:

```yaml
---
title: A clear post title
description: The visible subtitle and feed summary.
date: 2026-07-27T09:00:00+02:00
author: Author name
author_url: https://github.com/example
updated: 2026-07-29T14:30:00+02:00
tags: Project updates, Architecture
---
```

`title`, `description`, `date`, and `author` are required. `updated`,
`author_url`, `tags`, `og_image`, `noindex`, `searchable`, and `boost` are
optional. Timestamps must be ISO 8601 values with an explicit timezone. The
publication date must match the filename and neither timestamp may be in the
future. Keep drafts on branches; there is no draft or scheduled-publication
flag.

Do not add an `h1` to the post body because the Blog layout supplies it. Start
with the opening paragraph or an `h2`. Link durable instructions to their
current Docs, Examples, or Reference owner. A root build publishes the index,
stable post routes, Markdown companions, search and LLM entries, sitemap data,
social metadata, and `/blog/feed.xml`. Documentation snapshots produced by the
current builder keep a root `/blog/` header link but do not copy Blog content.
Older committed snapshots keep their historical header unchanged.

## Set up the environment

The docs require Python 3.10 or newer, [uv](https://docs.astral.sh/uv/), the
repository's pinned nightly Rust toolchain, and the recursive Git submodules.
CI currently uses Python 3.13.

```bash
git submodule update --init --recursive
uv sync --locked --all-packages --extra docs
```

The sync builds the Rust-backed `citry_core`, installs all workspace packages,
and adds the docs-only dependencies. Node and pnpm are not needed for ordinary
docs work, but they are needed by the complete repository gate.

## Work locally

### Live authoring server

```bash
uv run --no-sync python -m docs_site serve
```

Open <http://127.0.0.1:8000/>. The server reads content and navigation on each
request, renders through Citry, and serves component assets and examples.
Refresh the browser after changing Markdown. Uvicorn reloads when Python or
YAML docs configuration changes. Each server start or reload builds a universal
wheel from the workspace `citry-ui` package and combines it with the browser
playground's pinned Citry release. This local-only runtime lets interactive
snippets import `citry_ui` before that package is published, when its Citry
requirement accepts the pinned release. `serve-built`, static builds, CI, and
deployed docs use the committed pinned runtime unchanged.

Example recipes live at `/examples/<slug>/`. Their bare runnable pages live at
`/examples/<slug>/demo/`, so opening a recipe and opening its iframe directly
exercise different routes.

Useful options include:

```bash
uv run --no-sync python -m docs_site serve --port 8080
uv run --no-sync python -m docs_site serve --host 0.0.0.0
uv run --no-sync python -m docs_site serve --no-reload
```

This mode does not generate Pagefind search, minified HTML, crawl files, social
cards, or the assembled version tree. Use a static preview when testing those.

### Static current-version build

```bash
uv run --no-sync python -m docs_site build
```

The default output is the gitignored `site/` directory. A build clears its
output directory before writing, so treat a custom `--output` directory as
disposable. The builder refuses obvious unsafe targets such as the repository
root, content directory, and filesystem root.

For a faster content iteration build:

```bash
uv run --no-sync python -m docs_site build \
  --no-search \
  --no-social-cards \
  --no-minify
```

To choose another output directory:

```bash
uv run --no-sync python -m docs_site build --output path/to/output
```

The normal root build writes current versioned documentation and all site-scoped
pages, plus API reference, release notes, examples, static assets, Citry client
assets, Pagefind index, sitemap, robots file, Markdown companions, `llms.txt`,
and a nonstandard `llms-full.txt` bulk export. It also minifies HTML.

The v2 `llms.txt` file points directly to each page's `index.md` companion.
Rendered pages advertise that companion with `rel="alternate"` and advertise
the covering `llms.txt` with `rel="describedby"`. Keep `llms-full.txt` for
existing bulk-download users, but do not link it as part of the v2 proposal.

Social-card generation is optional. Without the `social-cards` extra and a
Chromium binary, it skips cleanly and pages retain the default Open Graph image.
A plain `build` reports a Pagefind failure without making that failure the
command's exit status, so use `build-check` when validating a change.

### Static preview

To rebuild and serve the current version's static output:

```bash
uv run --no-sync python -m docs_site serve-built
```

This is useful for Pagefind, minification, and flat-file asset behavior. It does
not mount committed `/v/` snapshots, so it is not the complete production
artifact.

### Production-equivalent preview

Production installs Playwright, renders social cards, and assembles the current
site together with committed version snapshots:

```bash
uv sync --locked --all-packages --extra docs --extra social-cards
uv run --no-sync playwright install chromium
uv run --no-sync python -m docs_site assemble
uv run --no-sync python -m http.server 8000 --directory site
```

Open <http://127.0.0.1:8000/>. On Linux, use `playwright install --with-deps
chromium`, as the deployment workflow does.

`assemble` is the local analogue of the GitHub Pages artifact: the current site
lives at the root and the published subset of `versions/` is mounted under
`/v/`. Avoid `assemble --no-build` for a normal preview because it intentionally
reuses an existing root build, which may be stale.

## Validate changes

Run the strict build and guard suite:

```bash
uv run --no-sync python -m docs_site build-check --strict
```

Run the docs unit, render, and example tests using the same explicit roots as
CI:

```bash
uv run --no-sync pytest docs_site/tests docs_site/examples
```

Do not replace those roots with `pytest docs_site`; the latter can choose an
import root that makes the example packages unable to import `docs_site`.

For browser tests:

```bash
uv sync --locked --all-packages --extra docs
uv sync --locked --package citry --group e2e --inexact
uv run --no-sync playwright install chromium
uv run --no-sync pytest docs_site/tests/e2e --browser chromium
```

The second sync selects the `e2e` group from its owning `citry` workspace
package. `--inexact` keeps the root project's docs dependencies installed.

The complete repository gate is:

```bash
pnpm install --frozen-lockfile  # first-time Node workspace setup
python scripts/check.py
```

Root pytest intentionally collects the published packages rather than the docs
suite, so a successful repository gate does not replace the dedicated docs
commands above. See [the monorepo development guide](../docs/codebase.md) for
the gate's full Rust, Python, and Node prerequisites.

## Configuration

`settings.yml` is the main maintainer-facing declaration. It owns the site and
repository identity, social destinations, search shortcuts, the `pages` and
`docstrings` Markdown profiles, Blog policy, git-footer policy, sitemap and
crawler policy, external inventory endpoints, and release-note exclusions.
The builder loads it together with `reference.yml`, `ui_library.yml`,
`redirects.yml`, and `docs_versions.yml` once at each command boundary and
validates all of them before a build clears or writes output.

Every manifest contains comments beside its editable declarations. Unknown
fields and duplicate YAML keys fail validation. The exact settings schema is
implemented by [`SiteSettings`](./_internal/settings.py) and its nested
dataclasses; version defaults and validation live in
[`VersionsConfig`](./_internal/bootstrap.py).

### Site settings fields

All fields in `settings.yml` are required. Lists described as unique reject
duplicate values.

| Field | Accepted value | Used for |
|---|---|---|
| `site.name` | Non-empty string | Page titles and site chrome |
| `site.public_url` | Absolute HTTP(S) URL ending in `/` | Canonicals, sitemap, feeds, and social metadata |
| `site.language` | Non-empty string | HTML `lang` value |
| `site.default_description` | Non-empty string | Fallback page description |
| `repository.owner` | GitHub owner name | Repository identity and generated links |
| `repository.name` | GitHub repository name | Repository identity and generated links |
| `repository.url` | `https://github.com/<owner>/<name>` URL, with an optional trailing slash | Source, edit, and social links |
| `repository.edit_branch` | Safe Git branch name | Edit-page links |
| `repository.issues_url` | `repository.url` plus `/issues` | Issue and 404 links |
| `repository.sponsors_url` | Absolute HTTP(S) URL | Sponsor links |
| `links.pypi` | Absolute HTTP(S) URL | Package links |
| `links.discord` | Absolute HTTP(S) URL | Community links |
| `search.pagefind_path` | Safe root-relative path ending in `/pagefind.js`; parent segments start with a letter or digit and then use only letters, digits, `_`, and `-`; the non-colliding root is outside `static`, `citry`, `meta`, `og`, and `v` | Search module and generated bundle location |
| `search.quick_links` | Ordered list of `{label, path}` mappings with unique paths | Search shortcuts |
| `markdown.pages.extensions` | Unique list of Python-Markdown extension names | Markdown page rendering |
| `markdown.pages.extension_configs` | Mapping from enabled extension name to option mapping | Markdown page extension options |
| `markdown.docstrings.extensions` | Unique list of Python-Markdown extension names | API docstring rendering |
| `markdown.docstrings.extension_configs` | Mapping from enabled extension name to option mapping | Docstring extension options |
| `blog.feed_path` | Root-relative `.xml` path under `/blog/` that does not overlap authored/generated routes, redirects, copied assets, or Pagefind output | Atom feed output |
| `blog.feed_limit` | Integer at least 1 | Maximum posts in the feed |
| `blog.words_per_minute` | Integer at least 1 | Reading-time estimates |
| `git.exclude_patterns` | Unique list of non-empty path-pattern strings | Pages omitted from author footers |
| `git.max_authors` | Integer at least 1 | Maximum displayed page authors |
| `seo.priorities` | Ordered list of unique `{prefix, priority}` mappings; priority is from 0 through 1 | Sitemap priority overrides |
| `inventory.python_docs_url` | Absolute HTTP(S) URL ending in `/` | Python intersphinx inventory |
| `release_notes.exclude` | Unique list of exact, non-empty changelog heading strings | Releases omitted from docs |

Extension option values may recursively contain strings, finite numbers,
booleans, `null`, lists, or mappings with string keys, to a maximum depth of
100 levels. A profile may configure only extensions enabled in that profile.
All configured HTTP(S) URLs reject credentials, query strings, fragments,
control characters, unsafe markup characters, and invalid ports.
Safe maintainer URL paths are literal paths: percent escapes, drive separators,
query strings, fragments, backslashes, whitespace, and dot segments are
rejected.

### Version policy fields

Every mapping and field in `docs_versions.yml` is optional. Omitted values use
the defaults shown below, but the manifest file itself is required.

| Field | Accepted value | Default |
|---|---|---|
| `versions.pattern` | Non-empty Python regular-expression matched after removing Citry's `citry@` tag prefix | Full three-part versions, with optional `v` prefix |
| `versions.include` | Unique list of normalized single-segment tag identifiers that start/end with a letter or digit and use `.`, `_`, or `-` internally; bypasses pattern and version bounds | `[]` |
| `versions.exclude` | Unique list of normalized single-segment tag identifiers with the same character policy | `[]` |
| `versions.oldest` | Empty string or full `major.minor.patch` version | `""` |
| `versions.newest` | Empty string or full `major.minor.patch` version | `""` |
| `aliases.latest` | Empty string or full `major.minor.patch` version | `""`, meaning newest built version |
| `publish.window` | Non-negative integer; `0` publishes all versions | `0` |
| `indexing.keep_recent` | Non-negative integer; `0` indexes all versions; `dev` and the `latest` target are always retained | `2` |

A tag cannot appear in both include and exclude. When both version bounds are
set, `oldest` cannot be newer than `newest`.

Markdown extension ordering and ordinary extension options belong in the named
profiles. Snippet base paths and the custom capture and table extensions remain
implementation-owned because they depend on the active checkout and precise
pipeline ordering.

To change Reference order or symbol ownership, edit `reference.yml`. Authored
Reference entries declare their Markdown source and stable anchors there. To
add, group, or reorder Citry UI pages, edit `ui_library.yml`. A component-owned
`api.md` supplies the guide, and its sibling `api.yml` supplies a structured API
reference. Both files are required. The builder validates and combines them at
the catalog route, and publishes the YAML beside the rendered guide so authored
`api.yml` links remain valid. The same functional groups drive the collapsible sidebar and
the grouped UI overview; there is no synchronized copy under
`docs_site/content`.
Add a published redirect to `redirects.yml`; redirect chains and unsafe paths
are rejected.

The builder reads these variables when the Python process starts:

| Variable | Purpose | Default |
|---|---|---|
| `DOCS_SITE_URL` | Override canonical, sitemap, Open Graph, and other public URLs | `settings.yml` |
| `DOCS_BASE_PATH` | Empty or a root-relative prefix such as `/citry`, never `/` and without a trailing slash | empty |
| `DOCS_GOOGLE_SITE_VERIFICATION` | Optional Google Search Console token | empty |

For a custom domain, `DOCS_SITE_URL` must match the Pages custom-domain setting.
For project Pages, set both the full project URL and its base path, for example
`DOCS_SITE_URL=https://owner.github.io/citry/` and
`DOCS_BASE_PATH=/citry`.

Google verification is supported by the builder but is not currently set in
the deployment workflows.

## Deploy the current site

Deployment uses GitHub Pages artifacts, not a `gh-pages` branch. Relevant
pushes to `main` trigger
[`repo--docs-deploy.yml`](../.github/workflows/repo--docs-deploy.yml), or a
maintainer can dispatch it manually:

```bash
gh workflow run repo--docs-deploy.yml
```

The workflow installs the locked workspace, docs and social-card dependencies,
and Chromium; runs `python -m docs_site assemble`; uploads `site/`; and deploys
through the `github-pages` environment.

An editorial-only merge, such as a Blog post, Community update, landing-page
change, or another `scope: site` page, uses this same workflow. It rebuilds the
root site and root-owned Pagefind, sitemap, LLM, feed, redirect, and social-card
outputs, then mounts copies of the existing committed snapshots. Assembly may
adjust those deployed copies for canonical/robots policy, the configured
Pagefind path, and a deployment base path; it never modifies or regenerates the
committed source snapshots. GitHub Pages replaces the artifact atomically, so
there is no separate partial-upload path to maintain.
Any future site-scoped source outside `docs_site/**` must be added to both the
docs-check and docs-deploy workflow path filters.

The repository needs this one-time GitHub configuration:

1. Set **Settings → Pages → Source** to **GitHub Actions**.
2. Configure `citry.dev` as the Pages custom domain.
3. Keep the workflow's `DOCS_SITE_URL` and `DOCS_BASE_PATH` aligned with the
   Pages configuration.

The deployment workflow does not depend directly on the docs-check workflow.
Branch protection should require **Docs check** so a failing docs build cannot
reach `main` and trigger deployment.

## Release version snapshots

A normal snapshot build writes tracked files under `docs_site/versions/` and
updates its manifest:

```bash
uv run --no-sync python -m docs_site build \
  --docs-version X.Y.Z \
  --alias latest
uv run --no-sync python -m docs_site versions-check --strict
```

For a detached snapshot at a custom path, add `-o <path>` and
`--no-update-versions-manifest`; detached builds require `--docs-version` and
cannot materialize an alias.

Snapshots contain only `scope: versioned` pages and their content assets. They
omit site-scoped pages and root-owned search, crawl, runtime, static, feed, and
social-card outputs. A site-scoped root landing page is replaced in the
snapshot by a redirect to the first built versioned page, so `/v/<version>/`
remains a valid version-picker destination.

Snapshots share the current root Pagefind index, CSS, JavaScript, and Citry
runtime. Search from an old version can therefore return current Docs,
Community, or Blog pages, and shared asset changes must remain compatible with
published snapshot markup. Snapshots keep their baked page metadata, including
the discovery relations emitted by their historical builder; only new
snapshots receive the current Markdown `alternate` and `llms.txt`
`describedby` contract. They do not receive a per-version generated social-card
set. Per-version search and version-pinned shared assets remain deliberate
deferrals.

Each new snapshot stores its accepted site-route patterns in
`_build_info.json`, so later scope changes do not reinterpret its intentional
root links. Reclassifying a published route is nevertheless a migration that
requires review of redirects, canonicals, content assets, and picker behavior.

Pushing a `citry@X.Y.Z` tag triggers
[`repo--docs-release.yml`](../.github/workflows/repo--docs-release.yml). The
workflow checks out `main` for commit-back and current-root assembly, while
`build-tag` creates the released snapshot in a detached worktree at the exact
tag commit. That worktree receives its own locked docs environment, including
the tagged Citry and Citry UI workspace packages, before the snapshot build:

```bash
uv run --no-sync python -m docs_site build-tag citry@X.Y.Z
uv run --no-sync python -m docs_site versions-check --strict
```

The snapshot is staged and replaces an existing version only after the tagged
builder exits successfully and writes its build stamp. One authorization detail
still needs an explicit maintainer decision before the first real snapshot:

- It attempts to commit the generated snapshot back to protected `main` with
  the default `GITHUB_TOKEN`, which may need replacement with an approved
  GitHub App token or PAT.

A manual dispatch without inputs only assembles and redeploys the existing
version tree. For recovery after a tag-triggered build failure, dispatch from
`main` with `release_tag=citry@X.Y.Z`; it rebuilds from that immutable tag,
commits the snapshot to `main`, and deploys it without moving the tag.

`build-all` is for bootstrap or disaster recovery, not routine releases:

```bash
uv run --no-sync python -m docs_site build-all --dry-run
uv run --no-sync python -m docs_site build-all
uv run --no-sync python -m docs_site versions-check --strict
```

It walks selected release tags in temporary Git worktrees and modifies the
committed version tree. Tags that predate the docs builder are skipped. Selection
and the publication window are defined in `docs_versions.yml`.

## Maintenance workflows

| Job | Schedule | Manual operation |
|---|---|---|
| People data | Monthly | `GITHUB_TOKEN=... uv run --no-sync python -m docs_site.scripts.people` |
| External links | Mondays at 06:00 UTC | `gh workflow run repo--docs-external-links.yml` |
| Lighthouse | Relevant pull requests | `gh workflow run repo--docs-lighthouse.yml` |

The People script reads `people_sources.yml`, resolves its `site` repository
entry from the `repository` mapping in `settings.yml`, and overwrites
`docs_site/data/people.yml`, and needs a token that can read every configured
repository. Repository order controls tie order and which later profile data
wins. The `maintainers` and `special_thanks` list order is the display order.
The workflow opens a pull request when generated data changes.

Internal links, anchors, assets, headings, snippets, and generated site structure
are checked by `build-check`. External links are intentionally checked on a
schedule because they can decay without a repository change. Lighthouse audits
performance, accessibility, best practices, and SEO; it is not currently a
required branch-protection check.
