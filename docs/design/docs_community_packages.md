# Design: documentation for Community packages

**Status (2026-08-25): Implemented for manual curation. Automated discovery is
designed but not implemented.**

This document defines the package directories published by the Citry
documentation site, the checked-in catalog that owns them, and the human review
process around future automated discovery.

It builds on the site-scoped Community lifecycle in
[`docs_site.md`](docs_site.md#content-scope-and-deployment), the content roles in
[`docs_content.md`](docs_content.md#content-surface-contract), and the registry
threshold in [`ecosystem_roadmap.md`](ecosystem_roadmap.md#67-tooling-and-ecosystem).
The historical umbrella tracker is
[django-components#804](https://github.com/django-components/django-components/issues/804).
The package-directory proposals are
[django-components#805](https://github.com/django-components/django-components/issues/805)
and [django-components#1192](https://github.com/django-components/django-components/issues/1192).

## Decisions at a glance

- Publish **Community extensions** at `/community/extensions/`.
- Publish **Community UI libraries** at `/community/ui-libraries/`.
- Keep both as direct, site-scoped Community items. Do not add an Ecosystem
  primary-navigation area yet.
- Keep the versioned Advanced pages as the canonical authoring guides. The
  Community pages own current package discovery.
- Project both pages from one reviewed
  `docs_site/data/community_packages.yml` catalog.
- Allow one package to belong to both categories.
- Mark Citry-maintained and independently maintained projects explicitly.
- Mark whether the distribution is currently published on PyPI. Unpublished
  previews may be listed when their status is clear.
- Sort by display name. Do not rank by stars, downloads, or other popularity
  measures.
- Treat future automation as candidate discovery only. A maintainer must add or
  change every public listing through an ordinary pull request.
- Never install, import, build, or execute a candidate package during docs
  builds or discovery.

## Reader job and information architecture

The two pages answer different search questions:

- "Which package connects Citry to another framework or adds cross-cutting
  behavior?"
- "Which installable library gives me reusable Citry UI components?"

The Advanced [Extensions](../../docs_site/content/advanced/extensions.md) and
[Component libraries](../../docs_site/content/advanced/component-libraries.md)
pages answer how to author and install those package types. They are versioned
because their contracts follow a Citry release. The package directories are
site-scoped because maintainers, releases, availability, and compatibility can
change independently of Citry releases.

Community is the current placement because it already owns current people and
participation surfaces and can deploy without changing release snapshots. In
this context, "Community" describes the area, not package ownership. A badge on
each entry distinguishes Citry-maintained packages from independent projects.
If package discovery later grows into a larger catalog with several package
families, the project can reconsider a top-level Ecosystem area with navigation
and usage evidence.

## Catalog contract

`docs_site/data/community_packages.yml` is the only public-listing authority.
Its schema version remains `1` while Citry is below `1.0.0`, following the
repository rule for pre-1.0 contracts.

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

| Field | Contract |
| --- | --- |
| `distribution` | Required Python distribution name. Uniqueness uses standard normalized package names, so `a-b` and `a_b` collide. |
| `name` | Required one-line display name. |
| `categories` | Non-empty unique list containing `extension`, `ui_library`, or both. |
| `summary` | Required one-line plain-text description. |
| `ownership` | `official` for Citry-maintained work or `community` for independent work. |
| `published` | Whether the named distribution currently has a PyPI release. The renderer derives the canonical PyPI URL. |
| `citry_requirement` | Required PEP 440 specifier describing the package's declared Citry compatibility. |
| `source_url` | Required HTTPS source repository. |
| `docs_url` | Optional HTTPS or root-relative documentation URL. |
| `maintainer` | Required one-line maintainer or organization label. |
| `maintainer_url` | Optional HTTPS or root-relative identity URL. |
| `notice` | Optional one-line disclosure rendered in both HTML and Markdown. Use it for material maturity, licensing, or support facts. |

Unknown keys, unknown categories, unsafe URLs, invalid specifiers, duplicate
YAML keys, and duplicate normalized distributions fail validation. The catalog
may be empty so an honest empty state remains representable.

The initial entries are Citry UI, the first-party UI library, and Citry Django,
an independently maintained extension published on PyPI. Citry Django's
repository includes an MIT license. The directory identifies its independent
ownership and does not imply that Citry has audited it.

## Data flow and publication lifecycle

```text
community_packages.yml
          |
          v
 validate and normalize
          |
          v
CommunityPackageCatalog
       /          \
      v            v
extension page   UI-library page
      |              |
      +------v-------+
      HTML cards + Markdown/LLM projection
```

The root build loads the catalog only when one of the two package pages belongs
to that build. It validates the catalog before clearing output, then supplies
one immutable catalog through the page render. The development server reloads
it when either package route is requested, so YAML edits appear on refresh.

Snapshot builds filter out site-scoped Community pages before deciding whether
to load the catalog. They do not read or validate current package data. The
catalog therefore does not belong in `DocsProject`, whose declarations load
before the command knows its target scope.

`<c-community-packages category="..." />` renders accessible server-side cards.
HTTPS package, maintainer, source, and PyPI links open in a new tab with
`rel="noopener"`; root-relative Citry documentation links stay in the current
tab.
Marker comments identify the browser-only block. The Markdown companion and
`llms-full.txt` projection replaces that block with a concise Markdown list
derived from the same catalog. Pagefind indexes the cards because the directory
pages, rather than separate package detail pages, are the canonical search
results.

## Manual submission and review

A package author or contributor requests a listing by editing
`docs_site/data/community_packages.yml` in a pull request. A maintainer checks:

1. The source repository and maintainer identity are public and credible.
2. The package implements the claimed Citry category. A UI library exposes the
   component-library contract; an extension exposes Citry extension behavior.
3. The compatibility claim agrees with package metadata or the documented
   source-only installation.
4. The summary is factual and does not make unsupported quality, security, or
   compatibility claims.
5. Released packages have a working PyPI project. Preview packages are visibly
   unpublished and link to source.
6. License intent is declared. Missing license text, archived source, unresolved
   ownership, or a significant security concern must be resolved or disclosed
   before acceptance.
7. The package is useful to Citry users and is not typosquatting, advertising
   spam, or an unrelated project using the name.

The maintainer may ask the package owner to confirm the listing. A merge is the
approval action. No naming prefix, keyword, download count, star count, or
automated score grants inclusion.

The directory states that independent packages are not audited or supported by
Citry. A listing may be removed when a project disappears, becomes malicious,
misrepresents compatibility, loses a usable license, is archived without a
maintained successor, or repeatedly breaks against supported Citry releases.
Removal uses a normal pull request and does not erase repository history. A
package may be relisted when the problem is resolved.

## Future weekly candidate discovery

The first automated version should be a reporting workflow, tentatively
`repo--docs-community-packages.yml`, scheduled weekly and manually dispatchable.
It must not run in the docs build or block documentation deployment.

### Discovery sources

1. Fetch PyPI's JSON [Index API](https://docs.pypi.org/api/index-api/) at
   `/simple/`, normalize every project name, and select names beginning with
   `citry-`.
2. Fetch current Simple-project and
   [JSON API](https://docs.pypi.org/api/json/) metadata only for candidates and
   already approved PyPI distributions. Use ETags, caching, a descriptive user
   agent, bounded concurrency, and PyPI's published API policies.
3. Optionally search GitHub repositories with the `citry` topic through
   GitHub's documented repository search API. This remains a lead, not proof
   that a Python package exists.
4. Optionally query PyPI's public BigQuery distribution-metadata dataset for a
   `citry` dependency or keyword if prefix discovery proves insufficient.

PyPI Core Metadata has a free-form `Keywords` field, but PyPI has no supported
API for searching all current projects by keyword or `Requires-Dist`. The old
XML-RPC search is disabled. A workflow must not scrape the PyPI search UI or
claim that a keyword scan is complete. The BigQuery dataset also retains
deleted releases, so every result needs current-index revalidation.

### Report and human gate

The workflow compares candidates with the approved YAML catalog and a future
checked-in `community_package_discovery.yml` review-state file. That file is
human-maintained and changes only through pull requests. Each reviewed name
records its normalized identifier, canonical source identity, review outcome,
review date, optional expiry, and a SHA-256 fingerprint of canonical JSON made
from the observed version, source owner and repository, maintainers, license
expression, and archived state. The workflow writes escaped, length-limited
facts to a JSON artifact and the GitHub Actions job summary, grouped as:

- new candidates;
- changed metadata or ownership;
- approved packages missing from their current source;
- suspicious, quarantined, yanked, archived, or license-changed projects; and
- network or API errors.

When maintainers want active notification, the workflow may create or update
one tracking issue identified by a stable marker. It never edits the catalog or
opens an approval pull request. Triage has three outcomes:

- **accept:** a person opens the ordinary catalog pull request;
- **dismiss:** record the normalized identifier, reason, review date, observed
  fingerprint, and an expiry no later than 180 days so the same unchanged
  false positive does not reappear every week; or
- **defer:** leave the candidate in the report for later review.

A dismissed candidate resurfaces when its fingerprint changes, its source
identity changes, or its dismissal expires. An accepted package whose observed
fingerprint differs from the reviewed fingerprint stays in the changed group
until a person reviews and updates the state. A failed run never advances this
baseline.

Prefix matching uses the PEP 503-normalized project name and requires the
literal `citry-` prefix. GitHub topic matching uses the exact case-insensitive
topic `citry`. If optional BigQuery discovery is enabled, dependency matching
parses `Requires-Dist` and requires the normalized dependency name `citry`;
keyword matching tokenizes on commas and ASCII whitespace and requires the
exact case-insensitive token `citry`. These are candidate signals only.

Discovery metadata is hostile input. The implementation must cap text lengths,
escape issue and summary output, reject credentials and unsafe URL schemes,
and never download distributions. Network requests are restricted to
allowlisted PyPI JSON/Simple endpoints, GitHub API endpoints, and the configured
BigQuery dataset. The workflow never follows metadata-provided URLs. An outage
preserves the prior approved state; it is not evidence that a package
disappeared.

## Failure behavior

| Failure | Required behavior |
| --- | --- |
| Catalog missing or invalid in a root build | Fail before clearing the last successful output and report the source location. |
| Catalog missing or invalid in a snapshot build | Ignore it; current site-scoped package data is outside the snapshot. |
| Invalid catalog during live preview of a package page | Fail that request with the validation error; unrelated pages remain previewable. |
| Package page has a missing or wrong directive | Fail the registered source guard with the Markdown source and line. |
| External package link later breaks | Let the existing weekly external-link workflow report it. |
| Discovery API times out or rate-limits | Report an error, preserve prior state, and do not remove or change listings. |
| Candidate matches a prefix or keyword | Report it for review only; do not publish it. |
| Candidate metadata contains markup or unsafe URLs | Escape or reject it and flag the candidate. |

## Verification

Tests use synthetic catalogs to cover schema failures, normalized duplicates,
category projection, context restoration, empty states, card rendering,
Markdown projection, root-build inclusion, and snapshot isolation. They do not
assert the real package inventory or page prose. A source guard checks the real
catalog and page directives. The normal strict docs build supplies link,
heading, HTML, CSS, sitemap, search, and companion coverage. The existing
weekly external-link workflow checks public package links independently of
pull requests.
