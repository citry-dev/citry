# Citry documentation site

This directory contains the source and build system for
[citry.dev](https://citry.dev/). The deployed site is static. Citry renders the
Markdown and components, then the build writes HTML, assets, search data, SEO
files, Markdown companions, LLM indexes, examples, generated API Reference
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
| `docs_versions.toml` | Version selection and publication policy |

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
`source: reference` fills its area from the public API category registry.
`source: blog` fills its area from the dated Markdown posts under
`content/blog/`, newest first, with **All posts** at the top.
Ordinary groups use the always-open section styling. Set `collapsible: true`
only when readers benefit from hiding a long or secondary list, as with
Release notes and the Examples groups. `section_style: true` keeps a
collapsible toggle visually aligned with the always-open section labels; it is
used by Release notes.
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
`/static/`, `/citry/`, and `/pagefind/` outputs also remain root-owned.
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
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/account_settings.py"
  title="Account settings tabs"
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

## Publish a Blog post

Blog sources live in `content/blog/`. Keep `index.md` as the only undated file
and name each post `YYYY-MM-DD-lowercase-kebab-slug.md`. The date prefix keeps
source files sortable, while the public URL omits it. For example,
`2026-07-27-language-agnostic-tools.md` is published at
`/blog/language-agnostic-tools/`.

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
Refresh the browser after changing Markdown. Uvicorn reloads when Python source
changes. Each server start or Python reload builds universal wheels from the
workspace `citry` and `citry-ui` packages for the browser playground. This
local-only runtime lets interactive snippets import `citry_ui` before the
package is published. `serve-built`, static builds, CI, and deployed docs keep
using the committed pinned runtime.

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
and `llms-full.txt`. It also minifies HTML.

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

The builder reads these variables when the Python process starts:

| Variable | Purpose | Default |
|---|---|---|
| `DOCS_SITE_URL` | Canonical, sitemap, Open Graph, and other public URLs | `https://citry.dev/` |
| `DOCS_BASE_PATH` | Root-relative prefix for project Pages or fork previews | empty |
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
outputs, then mounts the existing committed snapshots unchanged. It does not
create, modify, or regenerate a release snapshot. GitHub Pages replaces the
artifact atomically, so there is no separate partial-upload path to maintain.
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

Snapshots omit root-owned search, crawl, runtime, static, and social-card
outputs. They share those files from the assembled root site.

Pushing a `citry@X.Y.Z` tag triggers
[`repo--docs-release.yml`](../.github/workflows/repo--docs-release.yml). Review
that workflow's warning header before the first real release. This path has not
yet been proven with a real version snapshot, and two details need an explicit
maintainer decision:

- It attempts to commit the generated snapshot back to protected `main` with
  the default `GITHUB_TOKEN`, which may need replacement with an approved
  GitHub App token or PAT.
- It deliberately checks out `origin/main` before dependency installation and
  building, so the snapshot is internally consistent but a later `main` tip
  could differ from the commit carrying the tag.

A manual dispatch of the release workflow only assembles and redeploys the
existing version tree. Snapshot creation is conditional on a tag event.

`build-all` is for bootstrap or disaster recovery, not routine releases:

```bash
uv run --no-sync python -m docs_site build-all --dry-run
uv run --no-sync python -m docs_site build-all
uv run --no-sync python -m docs_site versions-check --strict
```

It walks selected release tags in temporary Git worktrees and modifies the
committed version tree. Tags that predate the docs builder are skipped. Selection
and the publication window are defined in `docs_versions.toml`.

## Maintenance workflows

| Job | Schedule | Manual operation |
|---|---|---|
| People data | Monthly | `GITHUB_TOKEN=... python docs_site/scripts/people.py` |
| External links | Mondays at 06:00 UTC | `gh workflow run repo--docs-external-links.yml` |
| Lighthouse | Relevant pull requests | `gh workflow run repo--docs-lighthouse.yml` |

The People script overwrites `docs_site/data/people.yml` and needs a token that
can read the public Citry and django-components repositories. Its workflow opens
a pull request when the generated data changes.

Internal links, anchors, assets, headings, snippets, and generated site structure
are checked by `build-check`. External links are intentionally checked on a
schedule because they can decay without a repository change. Lighthouse audits
performance, accessibility, best practices, and SEO; it is not currently a
required branch-protection check.
