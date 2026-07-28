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
areas:
  - label: Docs
    items:
      - { title: Home, path: / }
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
changes.

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

Snapshots contain only `scope: versioned` pages and their content assets. They
omit site-scoped pages and root-owned search, crawl, runtime, static, feed, and
social-card outputs. A site-scoped root landing page is replaced in the
snapshot by a redirect to the first built versioned page, so `/v/<version>/`
remains a valid version-picker destination.

Snapshots share the current root Pagefind index, CSS, JavaScript, and Citry
runtime. Search from an old version can therefore return current Docs,
Community, or Blog pages, and shared asset changes must remain compatible with
published snapshot markup. Snapshots keep their baked page metadata; they do
not receive a per-version generated social-card set. Per-version search and
version-pinned shared assets remain deliberate deferrals.

Each new snapshot stores its accepted site-route patterns in
`_build_info.json`, so later scope changes do not reinterpret its intentional
root links. Reclassifying a published route is nevertheless a migration that
requires review of redirects, canonicals, content assets, and picker behavior.

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

Before the first real docs release, change that second behavior so the
versioned snapshot is built from the tag commit while the current root site is
assembled from `main`. The current main-based snapshot source is a release
blocker, not the model for editorial deploys.

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
