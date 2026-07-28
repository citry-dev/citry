# Stage 1 external norms

**Status (2026-07-23): bounded read-only research complete.**

This note records the standards and comparison mechanisms used to shape the
product and beta charter. It is intentionally narrower than the later ecosystem,
positioning, benchmarking, and outreach research. Versions and support tables
are time-sensitive and must be checked again before release.

## Packaging and version semantics

- PyPA's version specifier specification uses `1.0.0b1` as the canonical beta
  spelling. It orders before `1.0.0`. Installers normally exclude pre-releases
  unless a user opts in, an appropriate pre-release is already installed, or no
  final release satisfies the requirement. See [Version
  specifiers](https://packaging.python.org/en/latest/specifications/version-specifiers/).
- `0.3.0` is a final release to Python packaging tools even if the package has
  the `Development Status :: 4 - Beta` classifier. Classifiers support project
  discovery; they do not change resolver behavior. See [Writing
  `pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/).
- `Requires-Python` constrains installation. Python-version classifiers describe
  intended or tested support but do not enforce it. See [Core
  metadata](https://packaging.python.org/en/latest/specifications/core-metadata/).
- Semantic Versioning treats `0.y.z` as initial development and `1.0.0` as the
  definition of the public API, while allowing an explicitly marked 1.0
  pre-release to remain unstable. Citry uses PEP 440 spelling for Python
  packages, but this lifecycle distinction remains useful. See [Semantic
  Versioning](https://semver.org/).
- Standard PyPI project links include Documentation, Source, Issues, Changelog,
  Release Notes, and Funding. See [Well-known project
  URLs](https://packaging.python.org/en/latest/specifications/well-known-project-urls/).
- PyPI attestations and Trusted Publishing can associate uploaded artifacts with
  their repository and publishing identity. They complement release review and
  artifact inspection rather than replacing them. See [PyPI
  attestations](https://docs.pypi.org/attestations/).

## Public package observations

Observed on 2026-07-23:

- PyPI listed `citry` 0.2.0, uploaded 2026-07-02, with
  `Requires-Python >=3.10,<4` and no Development Status classifier.
- PyPI listed `citry-core` 1.3.0, uploaded 2026-06-30, with the same Python range
  and no Development Status classifier.
- PyPI did not return a project under the name `pygments-citry`.
- The local `citry-ui` manifest was 0.0.1, Pre-Alpha, and constrained to
  `citry>=0.2.0,<0.3.0`.

The `citry-core` version must remain monotonic. It cannot be reset to match an
umbrella Citry version.

## Transferable comparison mechanisms

The comparison is about release and support mechanisms, not feature parity or
market positioning.

### django-components

This is the closest package-versioning analogue because its [source
manifest](https://github.com/django-components/django-components/blob/master/pyproject.toml)
shows wrapper version 0.151.1 depending on `djc-core>=1.3.1`.

- It publishes exact Python and Django compatibility and distinguishes tested
  operating systems from systems expected to work. See its [compatibility
  policy](https://django-components.github.io/django-components/latest/overview/compatibility/).
- It names Chromium, Firefox, and WebKit as its tested engines. See the [project
  overview](https://django-components.github.io/django-components/latest/overview/welcome/).
- It derives Python and Django support from active upstream support and revisits
  the matrix. See its [development
  process](https://django-components.github.io/django-components/latest/community/development/).
- Deprecations identify intended removal versions. See the [v0.140.0 release
  notes](https://django-components.github.io/django-components/latest/releases/v0.140.0/).
- Its [source
  manifest](https://github.com/django-components/django-components/blob/master/pyproject.toml)
  selects a compatible core floor instead of forcing numeric alignment. The
  current observed wrapper release was [0.151.1 on
  2026-06-25](https://github.com/django-components/django-components/releases/tag/0.151.1).

Transfer: keep Citry package versions independent, but publish the exact tested
combination and a concrete compatibility matrix.

### Laravel Livewire

- The quickstart gives concrete Laravel and PHP floors. See the [Livewire 4
  quickstart](https://livewire.laravel.com/docs/4.x/quickstart).
- A dedicated [major-version upgrade
  guide](https://livewire.laravel.com/docs/4.x/upgrading) identifies signature,
  configuration, and behavior changes.
- Browser-dependent behavior documents its fallback or limitation. See
  [transition compatibility](https://livewire.laravel.com/docs/4.x/wire-transition).
- Security reports have a [private reporting
  route](https://github.com/livewire/livewire/security).

Transfer: state host floors and give migrations a first-class public home.
Livewire's inspected material did not provide a detailed supported-version
window, so Citry should not copy that omission.

### Phoenix LiveView

- The [security
  policy](https://github.com/phoenixframework/phoenix_live_view/blob/main/SECURITY.md)
  names the lines receiving security fixes and limits ordinary fixes to the
  latest minor.
- The [repository
  documentation](https://github.com/phoenixframework/phoenix_live_view) names
  current Chrome, Safari, Firefox, and Edge rather than only saying "modern
  browsers."
- The [changelog](https://hexdocs.pm/phoenix_live_view/changelog.html) includes
  concrete migration actions.

Transfer: use a short, explicit support table that matches maintainer capacity.

### Django

- Deprecations normally remain with warnings for at least two feature releases,
  and patch releases preserve compatibility except where security or data-loss
  risk requires otherwise. See the [release
  process](https://docs.djangoproject.com/en/dev/internals/release-process/).
- Django separates feature freeze, beta stabilization, and release-candidate
  behavior. See the [6.1
  roadmap](https://www.djangoproject.com/download/6.1/roadmap/).
- Supported Python versions are explicit. See the [Django 6.0 release
  notes](https://docs.djangoproject.com/en/6.0/releases/6.0/).
- Security reporting is private and applies to supported versions. See the
  [security policy](https://docs.djangoproject.com/en/dev/internals/security/).

Transfer: use the lifecycle structure, but do not copy Django's response or
deprecation timeframes without capacity to sustain them.

### NiceGUI and Reflex

- NiceGUI uses deprecation warnings and migration guidance for major changes,
  names browser floors for features that need them, and supports only the latest
  version for security fixes. See its [3.0.0
  release](https://github.com/zauberzeug/nicegui/releases/tag/v3.0.0), [deployment
  configuration](https://nicegui.io/documentation/section_configuration_deployment),
  and [security
  policy](https://github.com/zauberzeug/nicegui/blob/main/SECURITY.md).
- Reflex publishes normal `0.x` releases while using a Beta classifier, provides
  migration guides for breaking pre-1.0 changes, and enumerates independently
  versioned first-party packages in releases. See its [PyPI
  project](https://pypi.org/project/reflex/), [0.8 to 0.9 migration
  guide](https://reflex.dev/blog/upgrading-reflex-0-8-to-0-9/), [0.9.7 release
  bill of materials](https://github.com/reflex-dev/reflex/releases/tag/v0.9.7),
  and [security
  policy](https://github.com/reflex-dev/reflex/blob/main/SECURITY.md).

Transfer: a `0.x` beta is viable if the intended v1 contract remains too open,
but it should not be marketed as a version that package metadata does not encode.

## Python and browser policy inputs

The [Python version status
table](https://devguide.python.org/versions/) placed Python 3.10 in
security-fix-only status through October 2026 on the observation date. Citry can
retain it for the first beta if CI, wheels, dependencies, and representative use
pass, but should publish a review point rather than promise 3.10 for all 1.x.

A defensible compatibility table distinguishes:

- tested and supported combinations;
- expected but not continuously tested combinations;
- unsupported combinations; and
- progressive enhancements whose absence does not remove the core workflow.

The browser policy should name engines and either exact floors or a rolling
window. Host adapters and deployment models need their own rows because one
working adapter or server cannot establish support for all of them.

## Version alternatives

### Alternative 1: umbrella v1 pre-release

Publish `citry==1.0.0b1`, keep core and companions independently versioned, and
publish the exact tested bill of materials. This is the recommended alternative
if the intended v1 public contract can now be named.

### Alternative 2: ecosystem compatibility train

Publish `citry==1.0.0b1` and designate several independently versioned packages
as one supported train. This increases release, documentation, security, and
maintenance scope. It should require explicit scope-expansion approval.

### Alternative 3: pre-v1 `0.x` beta

Publish an ordinary final such as `citry==0.3.0`, apply the Beta classifier, and
call it "Citry beta" or "pre-v1 beta." This is more honest if the intended v1
API and support contract cannot yet be named, but it does not encode a v1 beta
and it will be selected without pre-release opt-in.

## Resulting recommendation

Use Alternative 1 if the maintainer accepts a concise intended v1 public API,
launch-critical workflows, compatibility floors, package scope, beta change
rules, and support capacity. Use Alternative 3 if any of those remain materially
open after charter review. Keep Alternative 2 as an explicit later expansion,
not the default.
