# Stage 1 internal contract evidence

**Status (2026-07-23): bounded read-only pass complete.**

This note records the highest-impact repository evidence used by the product
and beta charter. It does not declare implementation complete. Source and
manifest observations establish a current contract; configured tests and prose
still require execution or artifact/live-project verification in later stages.

## Product direction

- The root pitch describes a frontend framework for Python, broad Python web
  server compatibility, and UI/HTML/XML/SVG/text rendering (`README.md:10-13`,
  `README.md:68-85`).
- The public experience already spans plain-Python installation and rendering,
  component composition, typed inputs, templates, control flow, slots,
  JavaScript/CSS, fragments, framework adapters, Alpine behavior, Events,
  caches, extensions, introspection, debugging, hot reload, and CLI workflows.
- The primary technical user supported by this material is a Python web
  developer who knows HTML and wants server-rendered reusable UI with optional
  browser and server interactivity. "Professionals, teams, and hobbyists" are
  useful segments, but the repository does not establish a priority among them.

The audit boundary should therefore be the coherent end-to-end product already
presented to users, not every implemented experiment or every future-language
idea.

## Package roles supported by current evidence

| Unit | Current evidence | Charter implication |
| --- | --- | --- |
| `citry` 0.2.0 | Public Python framework (`packages/py/citry/pyproject.toml:5-38`) | Owns the v1 beta product label |
| `citry-core` 1.3.0 | Public required Rust-backed dependency with inherited version lineage (`packages/py/citry_core/pyproject.toml:5-33`, `packages/py/citry_core/CHANGELOG.md:3`) | Required, independently and monotonically versioned |
| `citry-client` 0.0.0 | Private package whose output is embedded in `citry` (`packages/js/citry-client/package.json:2-5`) | Internal delivery input, not an npm product promise |
| Events and client-graph v1 | Normative language-neutral specifications (`packages/protocol/events/v1/spec.md:1-16`, `packages/protocol/client_graph/v1/spec.md:1`) | Embedded compatibility contracts; third-party implementation support still needs a decision |
| `pygments-citry` 0.1.0 | Package and publish workflow exist; changelog remains Unreleased (`packages/py/pygments_citry/pyproject.toml:5-42`, `.github/workflows/py--pygments-citry--publish.yml:1-23`, `packages/py/pygments_citry/CHANGELOG.md:7`) | Optional companion, pending a separate publish decision |
| `citry-ui` 0.0.1 | Explicit non-public, Pre-Alpha packaging spike constrained to `citry<0.3.0` (`packages/py/citry_ui/README.md:1-4`, `packages/py/citry_ui/pyproject.toml:5-30`) | Outside the first beta unless scope is deliberately expanded |
| Rust crates | Workspace implementation crates not intended for crates.io (`Cargo.toml:1`, `docs/codebase.md:1008`) | Internal implementation |

The repository's tag convention already supports independent releases
(`CONTRIBUTING.md:63-69`). Numeric lockstep across the ecosystem is neither
necessary nor compatible with the existing core lineage.

## Configured support evidence

- All Python distributions declare `>=3.10,<4.0` and classifiers for 3.10
  through 3.14. The main workflow configures CPython 3.10 through 3.14 on Linux
  and Windows and a 3.10/3.14 macOS smoke pair
  (`.github/workflows/py--tests.yml:37-84`).
- `citry-core` advertises PyPy, but the main workflow does not configure PyPy
  (`packages/py/citry_core/pyproject.toml:20-30`,
  `.github/workflows/py--tests.yml:62-65`).
- Browser CI configures the full suite in Chromium on pull requests, focused
  Firefox/WebKit conformance, and a scheduled full Chromium/Firefox/WebKit run
  (`.github/workflows/py--tests.yml:86-169`,
  `.github/workflows/py--tests-cross-browser.yml:1-55`). No core policy defines
  precise browser versions, branded Edge/Safari coverage, or mobile support.
- Public documentation names FastAPI/Starlette, Flask, Django, bare ASGI, and
  bare WSGI (`README.md:514-522`,
  `docs_site/content/web-frameworks.md:53-64`). Current test dependencies declare
  FastAPI `>=0.110` and Django `>=5.2` only on Python 3.12 and newer, but no real
  Flask or direct Starlette floor (`packages/py/citry/pyproject.toml:54-67`).
- Plain rendering requires no host. Client-active fragments need mounted routes,
  and multiple-worker fragment delivery needs shared cache behavior
  (`docs_site/content/getting-started/installation.md:103-115`,
  `docs_site/content/web-frameworks.md:194-223`).
- Client-active pages currently use Alpine's standard evaluator and require
  `unsafe-eval`; the CSP build is not supported
  (`docs_site/content/advanced/alpine-runtime.md:35-47`). This is a deployment
  limitation, not a detail to omit from the beta contract.

These are configuration and document observations. They do not replace current
workflow results, built-artifact inspection, or live validation.

## Contract contradictions and release risks

1. `docs/codebase.md:731-745` describes lockstep versioning, while
   `docs/codebase.md:795-831` describes intentionally independent package
   versions. The manifests prove the latter model.
2. The runtime manifest remains 0.2.0, while `CHANGELOG.md` contains a v0.3.0
   section and a much larger Unreleased section (`CHANGELOG.md:3`,
   `CHANGELOG.md:530`). The proposed beta must explicitly absorb, precede, or
   follow that intended release.
3. The dated project status and contributing guide still describe two Python
   packages, while the workspace now contains four
   (`TODO/project_status_june_2026.md:168-187`, `CONTRIBUTING.md:26`,
   `pyproject.toml:53`, `pyproject.toml:245`).
4. `citry.__init__` says only root `__all__` names are stable and all submodules
   are internal, while `citry.contrib` and public docs explicitly expose
   `contrib` and `ext` submodules (`packages/py/citry/citry/__init__.py:9`,
   `packages/py/citry/citry/contrib/__init__.py:20`,
   `docs_site/content/security.md:71`). The public API cannot be defined by
   `__all__` alone.
5. The core README describes a nonexistent `src` layout and an obsolete
   `parse_tag` API, while the live wrapper exports `parse_template` and
   `compile_template` (`packages/py/citry_core/README.md:40-80`,
   `packages/py/citry_core/citry_core/template_parser/__init__.py:33`).
6. Supported-version automation reads only `citry` and `citry-core`, despite
   the two additional Python distributions (`scripts/supported_versions.py:43`,
   `packages/py/citry_ui/pyproject.toml:18-26`,
   `packages/py/pygments_citry/pyproject.toml:20-27`).
7. The `citry` package-data declaration names dependency client JavaScript but
   not the Events bundle, and the current publish smoke test checks only the
   dependency bundle (`packages/py/citry/pyproject.toml:92-96`,
   `.github/workflows/py--citry--publish.yml:64-88`). Events cannot be called
   artifact-verified until the built wheel is inspected.
8. `docs/codebase.md:53` marks much of the file unverified and later contains a
   future package split that has already happened (`docs/codebase.md:650`). It is
   useful context but not an authoritative release promise until reconciled.

## Current security and community contract

- `SECURITY.md` supports only the latest `citry` and `citry-core` releases, uses
  private vulnerability reporting, and aims to acknowledge reports within a few
  days (`SECURITY.md:3-35`).
- The template sandbox is a defensive evaluator, not a formally complete jail,
  and Event authorization remains application-owned
  (`docs_site/content/security.md:8-16`, `docs_site/content/security.md:266-272`).
- Public help is issue-driven and the repository is solo-maintained
  (`docs_site/content/community/help.md:25-50`, `.github/CODEOWNERS:1`).
- Documentation and issue configuration intend GitHub Discussions as a question
  route, but Stage 0 publicly observed that Discussions was disabled. The beta
  cannot promise that route until the mismatch is resolved.

The defensible beta default is latest-release-only security support, best-effort
ordinary support, a durable public feedback route, and no stronger service-level
commitment without a capacity decision.

## Decisions the repository cannot make for the maintainer

- whether current `0.3.0` work is absorbed into `1.0.0b1` or released first;
- the exact protected public API and minimum beta deprecation window;
- precise host and branded-browser version floors;
- whether PyPy is supported or its classifier is removed;
- whether `pygments-citry` ships alongside the beta;
- whether the beta is for deliberate production pilots, general production use,
  or evaluation only;
- whether the v1 protocol specifications support third-party implementations in
  the first beta; and
- the ordinary support and security response capacity.

The clearest internal default is a Python-first `citry` 1.0 beta with an
independently versioned `citry-core`, embedded private browser runtime and v1
protocols, optional Pygments companion, and `citry-ui` outside launch scope.
