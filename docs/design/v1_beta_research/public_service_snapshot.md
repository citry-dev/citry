# Stage 0 public-service snapshot

**Observation window:** 2026-07-23T13:21:41Z to 2026-07-23T13:25:56Z.

**Evidence level:** publicly observed unless a section explicitly says
owner-readable. This is a read-only snapshot, not a release-readiness verdict.

## GitHub repository

- [`citry-dev/citry`](https://github.com/citry-dev/citry) is public, uses the
  MIT license, and has `main` as its default branch. The repository homepage is
  `https://citry.dev`.
- The latest public `main` commit was
  [`53aec721`](https://github.com/citry-dev/citry/commit/53aec721b7b13309880919f0ff3979f08a6b2245),
  committed on 2026-07-08. It matched the local Stage 0 HEAD.
- GitHub exposed 16 active committed workflows. The working tree contained 19
  workflow files, so public `main` and the local implementation must be tracked
  separately.
- The latest relevant public runs included:
  - [Check: failed](https://github.com/citry-dev/citry/actions/runs/28972667566)
  - [Docs check: failed](https://github.com/citry-dev/citry/actions/runs/28972667580)
  - [Deploy docs: failed](https://github.com/citry-dev/citry/actions/runs/28972667495)
  - [Python tests: passed](https://github.com/citry-dev/citry/actions/runs/28972667523)
  - [Rust tests: passed](https://github.com/citry-dev/citry/actions/runs/28972667551)
  - [Cross-browser tests: passed](https://github.com/citry-dev/citry/actions/runs/29726975085)
  - [Supported-Python check: passed](https://github.com/citry-dev/citry/actions/runs/29729220312)
- The repository had 18 open issues and 6 open pull requests. All six pull
  requests were Dependabot updates. No milestones were visible.
- Issues, repository Projects, Wiki, and Pages were enabled. Discussions were
  disabled.
- Public releases were `citry@0.1.0`, `citry@0.2.0`, and
  `citry-core@1.3.0`. They were public, non-draft, and not marked as
  pre-releases.

## GitHub organization and settings

Public observations:

- The [`citry-dev`](https://github.com/citry-dev) organization profile had no
  public name, description, website, location, email, social handle, profile
  README, or public members.
- The public organization Projects page reported no open or closed projects.
  Non-public Project V2 state remains unknown because suitable read-only
  Project access was unavailable.

Non-sensitive owner-readable observations:

- The repository rulesets endpoint returned no rulesets, and `main` was not
  branch protected.
- Pages used a workflow build with `citry.dev` as its custom domain and HTTPS
  enforcement enabled.
- Dependabot security updates, automated security fixes, secret scanning, and
  push protection were reported disabled.
- Auto-merge, update-branch, and automatic head-branch deletion were disabled.
  Merge commits, squash merges, and rebase merges were all allowed.
- The organization did not require two-factor authentication. Default
  repository permission was read.

These are summarized configuration facts, not raw settings exports. Private
membership, audit logs, secrets, billing, recovery material, and private
Project state were not inspected.

## Python Package Index

- [`citry`](https://pypi.org/project/citry/) returned 200. Latest was `0.2.0`,
  with one universal wheel and one source distribution, both unyanked. The
  files exposed GitHub publishing provenance.
- [`citry-core`](https://pypi.org/project/citry-core/) returned 200. Latest and
  only release was `1.3.0`, with 90 wheels and one source distribution, all
  unyanked. The files exposed GitHub publishing provenance.
- The official JSON endpoint for `pygments-citry` returned 404, so no published
  project or release was observable.
- Both published projects declared Python `>=3.10,<4.0`. Neither published
  metadata contained a Development Status classifier, a license expression, or
  a License classifier.

An empty vulnerability list in PyPI JSON is not proof that no vulnerability
exists.

## Documentation domain

- [`https://citry.dev/`](https://citry.dev/) returned HTTP 404 with valid TLS
  and a GitHub Pages response.
- `http://citry.dev/` redirected to HTTPS and then returned 404.
- `https://citry-dev.github.io/citry/` redirected to `https://citry.dev/` and
  then returned 404.
- `https://www.citry.dev/` failed TLS hostname verification. The HTTP `www`
  address redirected to the apex HTTPS address.
- Apex DNS used GitHub Pages addresses; `www` was a CNAME to
  `citry-dev.github.io`.

## Reproduction protocol

Public GitHub facts came from official REST endpoints rooted at:

```text
https://api.github.com/repos/citry-dev/citry
https://api.github.com/repos/citry-dev/citry/commits/main
https://api.github.com/repos/citry-dev/citry/actions/workflows
https://api.github.com/repos/citry-dev/citry/releases
https://api.github.com/search/issues
https://api.github.com/orgs/citry-dev
```

Non-sensitive owner-readable checks used read-only `gh api` requests for the
repository, rulesets, branch protection, Pages, and organization endpoints.
The Project query was attempted read-only and remained access-blocked.

PyPI checks used the official JSON and Simple API endpoints:

```text
https://pypi.org/pypi/citry/json
https://pypi.org/pypi/citry-core/json
https://pypi.org/pypi/pygments-citry/json
https://pypi.org/simple/{project}/
```

Domain checks used `curl -I`, redirect-following `curl`, and `dig` for the apex,
`www`, and GitHub Pages addresses. No credential, token, secret name/value, or
private content was retained.
