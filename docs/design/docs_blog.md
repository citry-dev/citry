# Design: Citry documentation blog

**Status (2026-07-28): Implemented.** This document defines the Blog content
model and the docs-site behavior that now implements it.

The Blog is a dated, authored part of the documentation site for project news,
design stories, lessons learned, and other context that should remain true to a
point in time. It is not another home for evergreen instructions or release
notes.

This design builds on the Blog decision in
[`docs_site.md`](docs_site.md#add-blog-as-a-top-level-area) and the content
surface contract in [`docs_content.md`](docs_content.md#content-surface-contract).
It also accounts for the later top-navigation proposal in
[`docs_playground.md`](docs_playground.md#navigation-and-page-generation).
The site builder and authoring commands remain documented in
[`docs_site/README.md`](../../docs_site/README.md).

## Decisions at a glance

- Add **Blog** as the last, rightmost primary-navigation item, after Community.
- Keep the index and post sources under `docs_site/content/blog/`.
- Name posts `YYYY-MM-DD-slug.md`; publish them at the stable `/blog/slug/`
  URL.
- Require a title, description, publication timestamp, and author. The
  description is also the visible subtitle and index excerpt.
- Allow an update timestamp, author URL, tags, and custom Open Graph image.
- Generate the Blog sidebar, index cards, and Atom feed from one
  validated post catalog.
- Sort the index and left sidebar in reverse chronological order, newest first.
- Keep the existing right-rail table of contents for headings on the current
  post.
- Publish Blog only at the site root. Frozen `/v/<version>/` documentation does
  not copy Blog pages.
- Keep drafts in branches and pull requests. The initial design has no draft or
  scheduled-publication flag.
- Do not add comments, reactions, social-share widgets, analytics, a newsletter,
  or author profile pages.

## Prior art and constraints

The existing site already provides most of the page machinery Blog needs:

- [`docs_site/content/_nav.yml`](../../docs_site/content/_nav.yml) owns primary
  navigation order. Named sources already generate Reference and release-note
  entries in place.
- [`nav.py`](../../docs_site/_internal/nav.py) scopes the sidebar, breadcrumbs,
  and previous/next links to the active primary area.
- [`pipeline.py`](../../docs_site/_internal/pipeline.py) turns Markdown headings
  into the right-rail and mobile tables of contents.
- [`frontmatter.py`](../../docs_site/_internal/frontmatter.py) parses a small set
  of scalar front-matter fields. Blog can extend that scalar model without
  replacing it with a second Markdown format.
- [`git_metadata.py`](../../docs_site/_internal/git_metadata.py) reports page
  edit history. A post's publication date and byline have different meaning, so
  Blog must use explicit authored metadata for those fields.
- [`build.py`](../../docs_site/_internal/build.py) records every page once, then
  uses those records for search, sitemap, social cards, Markdown companions,
  and LLM indexes.
- [`DocPage`](../../docs_site/_internal/components/doc_page.py) already emits
  canonical, Open Graph, Twitter, breadcrumb, and article metadata.
- The current docs design explicitly requires another narrow-desktop and mobile
  navigation check when Blog is added.

The older feature inventory marked Blog, comments, and tags as skipped because
the ported django-components site did not use them. The later information-
architecture decision in `docs_site.md` is authoritative for this new surface.

## Reader job and top-level placement

Blog primarily serves two reader situations:

- an existing user or contributor wants the context behind an announcement,
  experiment, or direction;
- an evaluator wants evidence of how the project makes decisions and what it
  has learned over time.

Success means the reader understands the dated context, can inspect the
supporting evidence, and can reach the current durable guidance without
mistaking the post for that guidance.

The repository has no direct-reader or search evidence for a Blog entry yet.
Its top-level placement is a maintainer product decision, made explicit in this
task, rather than an analytics finding. The placement should be revisited if
the area receives no sustained content, readers consistently reach posts only
through search and external links, or the full primary navigation cannot remain
clear at supported widths. Blog must not displace the higher-priority
evaluation, onboarding, troubleshooting, upgrade, or support paths.

## What belongs in Blog

Blog answers: "What is the project thinking, learning, or announcing now?"

Good Blog material includes:

- a project update with the context behind it;
- a release announcement that tells the larger story and links to the exact
  release notes;
- a design decision or experiment whose date and assumptions matter;
- a benchmark, migration story, or engineering lesson with reproducible
  evidence;
- a community announcement or contributor story.

Blog does not own the durable contract:

- supported current behavior belongs in Docs;
- a copyable task belongs in Examples;
- exact API behavior belongs in Reference;
- upgrade facts and required actions belong in release notes;
- contribution procedures belong in Community.

A post may summarize any of those subjects, but it links to the canonical page
for instructions readers should continue to follow. When a post discusses
planned behavior, it labels the proposal and date clearly. A later product
change does not require rewriting the historical post, but a material factual
error receives a visible correction and an `updated` timestamp.

## Information architecture

### Primary navigation

The `_nav.yml` declaration becomes:

```yaml
  - label: Community
    scope: site
    items:
      # Existing Community pages.

  - label: Blog
    scope: site
    source: blog
    entry: { title: All posts, path: /blog/ }
```

`source: blog` resolves to the Blog index followed by every post. Keeping the
source declaration in YAML preserves `_nav.yml` as the primary-navigation
owner while avoiding a second hand-maintained list of post titles and paths.
`scope: site` applies the shared site-wide lifecycle described in
[`docs_site.md`](docs_site.md#content-scope-and-deployment). `entry` supplies the
stable root link that a snapshot can render without loading current Blog
metadata; full source hydration must start with the same item.

The header order is:

1. Docs
2. Examples
3. Reference
4. Community
5. Blog

The separate playground design proposes **Try it**, and Citry UI is expected to
add another area near Examples. Blog remains the rightmost item in that likely
seven-link topology. Responsive acceptance therefore covers both the five-link
header that lands now and the full planned topology, not the older six-link
estimate in `docs_site.md`.

The Blog area is active on the index and post pages.

### URLs and files

| Source or generated artifact | Public URL |
| --- | --- |
| `content/blog/index.md` | `/blog/` |
| `content/blog/2026-07-27-language-agnostic-tools.md` | `/blog/language-agnostic-tools/` |
| Generated Atom feed | `/blog/feed.xml` |

The catalog strips the leading date when it creates the public post slug. The
filename keeps filesystem order, while the URL stays stable if an editorial
date needs correction. A published slug is stable. If it must change, the same
change adds an entry to the site's redirect map.

`index.md` is the only non-post Markdown file in `content/blog/`. Nested post
directories and undated post filenames are not part of the first version.

### Left sidebar

The left sidebar contains:

1. **All posts**, linked to `/blog/`;
2. every post, newest first.

Each entry shows the post title and a compact machine-rendered date. The source
files remain naturally sortable by their leading date, while catalog sorting
uses the full publication timestamp and a filename tie-breaker. This makes the
order deterministic when two posts share a day.

The Blog index lists the same catalog as cards, newest first. It shows the
title, description, publication date, author, computed reading time, and tags.
The first version lists all posts without pagination. A year-grouped archive or
pagination becomes necessary when the sidebar or index becomes hard to scan;
50 posts is the review threshold, not a silent behavior switch.

Breadcrumbs follow the generated area ownership rather than source filenames:

- the index shows **Blog** as the current crumb;
- a post shows **Blog** linked to `/blog/`, then its title as the current crumb.

The Blog navigation source supplies these trails explicitly because its index
sidebar label is **All posts** and its dated sources do not match their public
URLs under the generic exact-path breadcrumb lookup.

### Right table of contents

Post bodies use ordinary Markdown `##` and `###` headings. The current TOC
pipeline supplies the desktop right rail, mobile "On this page" disclosure,
heading links, and scroll tracking without Blog-specific JavaScript.

A short post with no `h2` intentionally omits both TOC presentations. An `h2`
is recommended when a post has distinct sections, but is not required merely
to fill the right rail. `h4` and deeper headings may appear in the article but
remain absent from the current two-level TOC; authors do not skip heading
levels.

The Blog layout supplies the only `h1`. Authors begin the Markdown body with an
opening paragraph or an `h2`. This keeps one page title and prevents the byline
from being separated from a duplicate body heading.

### Previous and next posts

Post footers use **Newer post** and **Older post** labels, based on the same
reverse-chronological catalog. The Blog index is not treated as a neighboring
post. A separate **All posts** link returns to `/blog/`.

## Authoring contract

### Filename

A post filename must match:

```text
YYYY-MM-DD-lowercase-kebab-slug.md
```

The prefix must be a real calendar date. The part after the date becomes the
public slug and uses lowercase ASCII letters, digits, and single hyphens. The
prefix must equal the calendar-date portion of the authored `date` value.

### Front matter

Example:

```yaml
---
title: Why language-agnostic tools matter
description: One implementation can give several language communities the same reliable behavior.
date: 2026-07-28T09:00:00+02:00
author: Juro Oravec
author_url: https://github.com/jurooravec
updated: 2026-08-02T16:30:00+02:00
tags: Project updates, Architecture
og_image: /static/img/blog/language-agnostic-tools.png
---
```

| Field | Requirement | Meaning |
| --- | --- | --- |
| `title` | Required | Page title, sidebar label, feed title, and social-card title. |
| `description` | Required | Visible subtitle, index excerpt, search description, feed summary, and default social description. |
| `date` | Required | First publication time as an ISO 8601 timestamp with an explicit timezone. |
| `author` | Required | One human-readable byline for the first version. |
| `author_url` | Optional | An HTTPS or root-relative link for the author name. |
| `updated` | Optional | Time of a material correction or revision, using the same timestamp format. |
| `tags` | Optional | Comma-separated display labels for cards, post metadata, social metadata, and the feed. A tag itself cannot contain a comma. |
| `og_image` | Optional | Existing per-page social-card override. |
| `noindex`, `searchable`, `boost` | Optional | Existing page controls, used only for an intentional exceptional case. |

There is no separate `subtitle` or `summary` field. `description` fills both
roles, which prevents the visible excerpt, feed summary, and search metadata
from drifting apart.

Blog posts do not accept a `canonical` override. Their local stable public URL
is the canonical URL and Atom entry identity. This prevents an editorial SEO
override from changing a feed entry's identity.

Tag display casing and punctuation are preserved. For duplicate detection,
the catalog trims and collapses whitespace and applies Unicode case-folding.
The initial release does not link tags or generate tag archive pages. Tags
still provide visible context and feed/Open Graph categories; a browse taxonomy
waits for enough posts to justify stable tag URLs.

The first version supports one author. A post can credit other contributors in
its prose. Multiple structured authors should be added only with an author
identity model and a real post that needs it.

### Post body

A post starts with the context the reader needs now, then presents evidence,
examples, or the story in a useful order. It should include:

- the time-bound context or question;
- evidence and runnable examples when claims depend on behavior;
- limitations, failed approaches, or uncertainty that changes the conclusion;
- links to the canonical Docs, Examples, Reference, release notes, issue, or
  design record where readers can continue.

Code and component examples follow the same formatting and execution rules as
the rest of the user documentation. A post is allowed a more personal authorial
tone, but still follows the repository's plain-language and heading rules.

### Publication workflow

A branch or pull request is the draft. Merging a valid post to the deployed
branch publishes it. This keeps the public catalog equal to the repository
contents and avoids a hidden `draft: false` mistake.

Scheduled publishing is not supported. A future publication timestamp fails
every catalog load, including the development server and `assemble`. An author
who needs a timed release uses the intended publication timestamp only when
merging or dispatching the deployment. The validator accepts an injected clock
for deterministic tests, not a production bypass.

## Catalog and data flow

A new `docs_site._internal.blog` module discovers the post files once and
creates an immutable `BlogCatalog`:

```text
Markdown file + filename
          |
          v
  validate and normalize
          |
          v
      BlogCatalog
       /   |   |   \
      v    v   v    v
 sidebar  index  post  Atom/SEO/LLM
```

`BlogPost` carries the source path, public URL, title, description, publication
and update times, author fields, normalized tags, reading time, and the ordinary
page metadata. `BlogCatalog` exposes posts newest first, lookup by URL, and tag
groups.

The static build creates the catalog before clearing the output directory. A
metadata error therefore leaves the last successful local build intact. The
dev server rebuilds the small catalog per request, matching its current
live-authoring behavior.

Dated post files are excluded from the ordinary `content/**/*.md` output loop.
The Blog catalog renders each one only at its stable `/blog/<slug>/` URL, so the
build cannot also leak a date-prefixed alias. The development server's
URL-to-source lookup resolves post routes through the same catalog. `index.md`
continues through the ordinary Markdown pipeline, with the catalog injected
for its Blog-list component.

Internal Markdown-link rewriting uses the catalog's source-to-public-URL map
before the generic `md_to_url` fallback. A relative link to a dated Blog source
therefore resolves to `/blog/<slug>/`, not to a missing date-prefixed URL. The
same resolver is shared by build, development server, link guard, Markdown
companions, and redirect checks.

Reading time is computed, not authored. It uses the visible prose word count at
200 words per minute, rounded up to at least one minute. Fenced code and raw
markup are excluded so generated HTML and syntax tokens do not inflate it. The
label remains explicitly approximate, such as "About 4 min read."

## Rendering

### Blog index

`content/blog/index.md` owns the introductory prose and includes one
`<c-blog-list />` directive. A Blog component family renders the index cards
from `BlogCatalog`. As with the example-card projection, the pipeline produces
a concise Markdown list for per-page companions and `llms-full.txt` rather
than exporting the browser card markup. Pagefind ignores the repeated card
list on the Blog index so searches lead to the post itself.

### Post header

`DocPage` receives an optional Blog-post view. Inside the page's `<article>`, it
renders:

- the title as `h1`;
- the description as a visible subtitle;
- `By <author>`;
- a semantic `<time datetime="...">` publication date;
- an updated date only when provided;
- approximate reading time;
- tag labels.

The generic git-derived "Last updated by" footer is suppressed for posts. It
describes repository edit history, not editorial publication. The existing
"Edit this page on GitHub" action remains.

### Themes and responsive layout

Blog adds only CSS to the shared token system. The header, cards, byline, tags,
and feed link must work in explicit light, explicit dark, and automatic themes.
Dates use text as well as placement or color. Links remain underlined or
otherwise distinguishable without color alone.

The added primary-navigation item must pass the existing overlap checks at
769, 800, 900, and 1024 pixels, plus the mobile drawer check. If it does not
fit, the header's collapse or overflow behavior changes for all areas; labels
must not overlap the search, version, theme, or social controls.

## Feed and discovery

The root build writes an Atom 1.0 feed at `/blog/feed.xml`. Atom is chosen
because it has a precise standard for stable entry IDs, authors, updates,
categories, and self links. The feed contains the 20 newest posts, with:

- `Citry blog` as its title, the absolute canonical feed URL as its stable ID,
  a self link, a `/blog/` alternate link, and the maximum effective-update
  timestamp among its entries as the feed update time;
- the canonical post URL as its link and stable entry ID;
- title and plain-text description;
- publication timestamp and an Atom update timestamp equal to `updated` when
  present, otherwise `date`;
- author name and optional URL;
- tags as Atom categories.

The feed publishes summaries and links to the canonical pages. It does not copy
the full rendered HTML, which avoids rewriting internal asset URLs and embedded
interactive examples for feed readers.

Every current root page includes an autodiscovery link:

```html
<link
  rel="alternate"
  type="application/atom+xml"
  title="Citry blog"
  href="/blog/feed.xml"
>
```

The Blog index also has a visible **Subscribe via Atom** link. With no posts,
the index renders an honest empty state and the build omits the feed and its
links. A production feed requires an absolute `DOCS_SITE_URL`. With posts, the
development server renders `/blog/feed.xml` on demand through the same
serializer, using the local request origin and configured base path for preview
URLs. This keeps route and XML behavior aligned without treating a development
origin as the published identity.

The feed follows [RFC 4287](https://www.rfc-editor.org/rfc/rfc4287). Post pages
use [`BlogPosting`](https://schema.org/BlogPosting) structured data and the
current [Google article metadata guidance](https://developers.google.com/search/docs/appearance/structured-data/article)
for visible authors, dates, headlines, and representative images.

## Search, SEO, social cards, and generated text

Blog posts participate in the existing systems as first-class page records:

- Pagefind indexes the post title, description, headings, and body.
- The sitemap uses `updated` when present and `date` otherwise, rather than a
  git commit date.
- Each post emits `BlogPosting` JSON-LD with `headline`, `description`,
  `datePublished`, `dateModified` (using `updated` or falling back to `date`),
  `author`, `publisher`, canonical URL, and the final social image.
- Open Graph metadata adds `article:published_time`, optional
  `article:modified_time`, `article:author`, and one `article:tag` per tag.
- Existing generated social cards use Blog as their section label and keep the
  post title and description.
- Markdown companions retain the date, updated date, author, author URL, and
  tags as front matter.
- `llms.txt` gains a Blog section in navigation order. `llms-full.txt` includes
  each post once, newest first.

The JSON-LD guard learns the required `BlogPosting` fields. Feed generation has
an XML well-formedness and required-element check.

## Documentation versions

Blog uses the docs site's declarative `site` scope rather than a Blog-only build
exception. It is project-wide, not Citry-version-specific:

- the current root build writes `/blog/`, post pages, and the feed;
- a `build --docs-version ...` snapshot skips `content/blog/` and Blog-generated
  artifacts;
- Blog links in versioned page chrome point to the root `/blog/`;
- Blog pages hide the documentation version picker, whose choices do not map
  to Blog URLs;
- old committed snapshots stay immutable, including their historical header.

This avoids copying the same time-bound posts into every release snapshot and
prevents a picker from constructing missing `/v/<version>/blog/...` URLs. For a
version build, the resolved Blog navigation area is therefore a root-owned
header and mobile-drawer link, not a snapshot page collection. It has no
versioned sidebar entries and is never active inside the snapshot.

The same scope resolver drives authored-page inclusion, generated-source
hydration, content assets, picker visibility, navigation URLs, Markdown links,
and version-tree validation. Versioned destinations are projected to
`/v/<version>/...`; Blog and other site destinations stay at the root. The
cross-version guard permits root-absolute page links only when `_nav.yml`
declares their route namespace site-scoped, and checks `/v/...` targets against
the committed snapshot tree. It does not assume that every root-absolute link
is valid.

Assembly does not rewrite historical headers. Only snapshots built by the
current builder contain the declared Blog escape link; older committed HTML
keeps the navigation it was built with.

## Validation and failure behavior

Blog metadata is validated as a catalog before rendering. Errors name the
Markdown path and source line where possible.

| Invalid or unexpected input | Result |
| --- | --- |
| Missing index page | Build error: Blog has no header destination. |
| Duplicate key, malformed front-matter line, or unknown post key | Build error at the offending source line. |
| Missing or whitespace-only title, description, date, or author | Build error on that source file. |
| Filename does not match the required dated slug | Build error. |
| Filename date and `date` disagree | Build error. |
| Timestamp is invalid or lacks a timezone | Build error. |
| Publication time is in the future | Catalog error in build, checks, and development serving; scheduled publishing is unsupported. |
| `updated` is earlier than `date` | Build error. |
| `updated` is in the future | Catalog error using the same injected clock as `date`. |
| Post declares `canonical` | Build error; Blog post identities are local and stable. |
| Invalid author URL | Build error. Only HTTPS and root-relative links are accepted. |
| Empty tag or duplicate normalized tag | Build error. |
| Duplicate public post URL | Build error before output is cleared. |
| Empty post body | Build error. |
| Blog index has zero or multiple `<c-blog-list />` directives | Build error; the index owns exactly one generated list. |
| No posts | Valid empty index; no feed file or feed link. |
| One post body fails to render | Recorded page failure; `build-check` fails and deployment is blocked. |
| Empty or invalid production site URL | Feed/structured-data error in the strict build. |
| A published post path changes without a redirect | Pull-request review error; the final tree alone cannot prove prior publication. A declared redirect is then checked by the existing redirect and link guards. |

Ordinary non-Blog pages keep their current permissive front-matter behavior.
The stricter contract applies only to dated post files.

## Accessibility and semantics

- Each post has exactly one `h1`; body headings descend without skipped levels.
- The post and every index card use `<article>` semantics where appropriate.
- Dates use `<time>` with a machine-readable timestamp and visible text.
- The author URL has the author name as its accessible text.
- Tags are a labelled list of plain display values, not an unlabeled row of
  pills. The first version has no tag archive links.
- The right TOC, mobile disclosure, breadcrumbs, keyboard behavior, focus
  appearance, contrast, reduced-motion behavior, and zoom support remain part
  of the shared page chrome acceptance checks.
- Feed and tag links have descriptive accessible names.

No client JavaScript is required for core Blog reading or navigation.

## Implementation surface

| Area | Expected change |
| --- | --- |
| Content | Add `content/blog/index.md` and dated post files. |
| Catalog | Add `_internal/blog.py` for discovery, validation, ordering, tags, reading time, and feed data. |
| Navigation | Add the `blog` area source, place it last in `_nav.yml`, generate Blog breadcrumbs, and teach the nav guard about generated entries. |
| Rendering | Add the Blog component family, post-header data, and text projection. |
| Build and serve | Share one catalog across root-build consumers and internal-link rewriting; route dated post sources only to stable slugs; add the feed output/route; use the common site scope to omit Blog from docs-version builds without reading current metadata. |
| Metadata | Extend post parsing, page records, companions, sitemap dates, Open Graph, and JSON-LD. |
| Styling | Add token-based Blog header, card, metadata, tag, and feed styles. |
| Guards | Add Blog metadata/feed checks and extend nav, JSON-LD, link, and generated-artifact coverage. |
| Documentation | Add Blog authoring instructions to `docs_site/README.md` and update the Blog status in `docs_site.md` and `docs_content.md` after landing. |
| Content research | Add the index, post family, feed, URLs, navigation, consumers, outputs, tests, and refreshed source fingerprints to the Stage 1 inventory. Its mapping columns are the scoped Blog content map; the separate program-wide map remains part of the later content-research stage. |

Keep the Blog components in one component-family module, following the
repository's component-authoring guide. Keep catalog, validation, and feed
generation outside the components so rendering remains a projection of one
accepted data model.

## Test plan

Use synthetic temporary posts for machinery tests. Do not lock a real post's
wording, title, or tags into pytest assertions.

### Unit and build tests

- valid discovery and all metadata fields;
- each filename, timestamp, URL, tag, and author validation error;
- deterministic newest-first ordering and same-day tie-breaking;
- reading-time calculation;
- generated navigation, active Blog area, sidebar dates, breadcrumbs, and
  Blog-specific newer/older links;
- one rendered `h1`, visible subtitle/byline/times/tags, and a right TOC from
  body headings;
- index cards, empty state, and their text projections;
- Atom structure, entry order, stable IDs, categories, XML escaping, and the
  effective update fallback, feed metadata, and 20-entry limit;
- `BlogPosting` JSON-LD, Open Graph article fields, social-card selection,
  sitemap dates, Markdown companions, and LLM order;
- current root build inclusion and docs-version build exclusion;
- build/dev-server parity for index, post, and feed routes;
- nav and Blog guards reporting source paths and lines;
- relative links between Blog posts resolving to stable slugs in rendered HTML,
  link checks, and Markdown companions.

### Browser and accessibility tests

- Blog is the rightmost desktop and mobile primary-navigation item and becomes
  active on index and post pages;
- the five-link header and a synthetic seven-link future header do not overlap
  controls across the existing narrow-desktop range;
- mobile drawer, left sidebar, right TOC, and heading scroll tracking work on a
  post;
- explicit light, explicit dark, and automatic themes keep cards and metadata
  readable;
- keyboard focus, semantic landmarks, accessible names, and contrast pass;
- the visible Atom link downloads a valid feed and no Blog asset returns 4xx or
  5xx.

### Delivery checks

Run the dedicated docs checks before the repository-wide gate:

```sh
uv run --no-sync python -m docs_site build-check --strict
uv run --no-sync pytest docs_site/tests docs_site/examples
uv run --no-sync pytest docs_site/tests/e2e --browser chromium
python scripts/check.py
```

## Rollout

1. Add the catalog, strict metadata validation, synthetic tests, and Blog nav
   source.
2. Add the index, post header, sidebar ordering, and styles.
3. Add Atom, structured data, sitemap/companion/LLM integration, and version-
   build exclusion.
4. Add one editorially reviewed launch post and run the production-equivalent
   build plus browser and accessibility checks.
5. Update the controlling docs-site and content design records from planned to
   implemented only after the full path is verified.

Each stage should leave the strict docs build green. The first public deploy
should contain at least one post so feed discovery and real post metadata are
observed in the production artifact.

## Alternatives considered

### Hand-author every post in `_nav.yml`

This duplicates title, path, and order beside the Markdown source. It allows
the sidebar, index, and feed to disagree, so one generated source owns all
three projections.

### Put Blog in a peer `docs_site/blog/` tree

Posts use the same trusted Markdown, components, links, search, SEO, and build
pipeline as other reader pages. Keeping them under `content/blog/` preserves
one content boundary; a separate source tree adds routing without a distinct
security or rendering need.

### Derive publication metadata from Git

The first and latest commits describe repository history. They do not reliably
describe editorial publication, corrections, or the byline. Explicit post
metadata supplies those meanings and remains stable across rebases or imports.

### Keep the date in public URLs

A dated URL can use the ordinary Markdown path mapping directly, but it couples
the public identity to editorial date metadata. The catalog already needs
Blog-specific discovery for navigation, tags, feeds, and validation, so it also
owns stable `/blog/slug/` path lookup in the build and dev server.

### Add comments or reactions

They require identity, moderation, abuse handling, privacy policy, storage,
notifications, and an operational service on an otherwise static site. They do
not serve the first Blog release.

## Falsifiers and later decisions

Revisit this design when evidence shows one of these conditions:

- more than 50 posts makes the flat sidebar or all-post index hard to scan;
- a real post needs multiple structured authors or an internal author profile;
- publication must happen automatically at a scheduled time;
- readers need full-content feeds rather than summaries;
- tags are too sparse to justify archive pages or rich enough to need a formal
  taxonomy;
- a Blog post genuinely needs to be frozen separately for every Citry version;
- stable slug mapping causes repeated authoring or routing mistakes that the
  dated source URL would avoid.

Until then, the smaller contract above keeps authoring explicit and every
public projection derived from one source.
