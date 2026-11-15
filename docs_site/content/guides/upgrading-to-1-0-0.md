---
title: Upgrade to Citry 1.0.0
description: Move a Citry project to 1.0.0, prepare for deprecation warnings, and handle State tokens that now expire after 24 hours.
---

# Upgrade to Citry 1.0.0

Use this guide to move a project to Citry 1.0.0, the first stable
release. Citry 0.9.0 made the last large set of breaking changes, and
most projects need no code changes for 1.0.0. The one change most
projects notice is that
[Citry's State tokens now expire](#state-tokens-expire): the signed
strings that carry a component's [State](/events/state/) to the page
stop working after 24 hours.

Work from the top. Skip the State sections if no component uses server
events; everyone follows [Deploy the upgrade](#deploy-the-upgrade). The
[checklist](#upgrade-checklist) at the end lists every step.

## Upgrade to 0.9.x first { #upgrade-to-0-9-first }

Move to the newest 0.9.x release before 1.0.0. If you are on 0.9.x
already, skip to step 2. If you are on an older release:

1. Follow the "Upgrading from" notes of each release you skip, oldest
   first, in the [release notes](/releases/). For a project on 0.8.x,
   that is [Upgrading from 0.8.x](/releases/v0.9.0/#upgrading-from-08x).
2. Run your tests and your app on 0.9.x, and fix what fails.

Going one release line at a time keeps each failure tied to the notes
that explain it.

## Fix deprecation warnings { #fix-deprecation-warnings }

Citry warns with `CitryDeprecationWarning` when your code uses a feature
that is going away. Python hides this warning in most programs, so make
it an error in your tests:

```toml
# pyproject.toml
[tool.pytest.ini_options]
filterwarnings = [
    "error::citry.CitryDeprecationWarning",
]
```

Citry 0.9.x deprecates nothing, so your tests should show no warnings
today. Add the setting anyway: a 1.x minor release may deprecate a
feature, and this makes each use fail a test instead of going unnoticed.
[Deprecations](/about/versioning/#deprecations) shows how to see the
warning in a running server too.

## Upgrade the packages { #upgrade-the-packages }

Upgrade Citry:

```console
python -m pip install -U "citry>=1.0.0,<2"
```

Add the packages you use to the same command:

- `"citry-lsp>=1.0.0,<2"`, the language server behind editor support.
  If you use the [VS Code extension](/ide/vscode/), update it to 1.0.0
  at the same time.
- `"pygments-citry>=1.0.0,<2"`, the Citry syntax highlighter for
  Pygments.
- `"citry-ui>=0.6.0,<0.7"`, the [UI library](/ui-library/). citry-ui
  0.6.0 needs Citry 1.0.0 or later, and stays on 0.x, so pin one minor
  release.

Citry 1.0.0 installs the `citry-core` version it needs. Depend on
`citry`, not on `citry-core`.

Then change the Citry entry in `pyproject.toml` or your requirements
file to `citry>=1.0.0,<2`, so later installs stay on 1.x (see
[Pin and upgrade](/about/versioning/#pin-citry)).

## Handle State expiry { #state-tokens-expire }

After the upgrade, a component whose `State` sets no `_max_age` can fail
its next event call: the call fails with a `stale_state` error without
running its handler, and Citry's browser code asks the visitor once per
page whether to reload. Until the visitor reloads, every call from that
component fails the same way.

Unless a component sets `State._storage = "server"`, Citry sends its
State to the page as a signed string, the State token. In 0.9.x, the
token of a component with no `_max_age` worked until you changed the
secret Citry signs it with. In 1.0.0, it stops working 24 hours after
Citry issues it, as server-stored State already did.

- Citry issues a new token when it renders the component and after a
  call that changes State. Only pages whose State has not changed for
  24 hours are affected.
- To keep tokens working for longer, set a longer `_max_age` in the
  `State` class inside the component. No setting turns expiry off.

    ```python
    from datetime import timedelta

    class State:
        _max_age = timedelta(days=7)
    ```

- A longer `_max_age` applies to tokens Citry issues after the upgrade.
  Tokens issued before the upgrade expire 24 hours after Citry issued
  them, whatever `_max_age` says.
- A cached page carries the token it was rendered with. If your CDN or
  web framework keeps whole pages for more than 24 hours, set
  `_max_age` at least that long. Otherwise a visitor gets an expired
  token straight from the cache, and reloading does not help.
- The [render cache](/performance/caching/) renders an entry again once
  its token has expired, so a `ttl` over 24 hours needs a matching
  `_max_age` to save any work.

[State token lifetime](/about/versioning/#state-token-lifetime) has the
rule, and [Treat State as input](/security/#treat-state-as-client-input)
explains why tokens expire.

### Set a valid `_max_age` { #max-age-minimum }

Set `_max_age` to at least one second. A shorter value, including
`timedelta(0)`, now raises `ValueError` when Python imports the
component. In 0.9.x it made every token expire the moment Citry issued
it.

## Deploy the upgrade { #deploy-the-upgrade }

Follow [Deploy a Citry upgrade](/advanced/web-frameworks/#deploy-a-new-version):
clear the cached copies of whole pages (in your CDN or web framework),
and give every server one shared cache while you upgrade servers one at
a time.

Open pages keep working during such a rolling deploy only when both
releases are 1.x (see [Rolling deploys](/about/versioning/#rolling-deploys)).
A page opened on 0.9.x may show components that do not start until the
visitor reloads it.

## Check experimental APIs { #check-experimental }

Citry 1.x keeps the documented API working, except for features marked
experimental, which may change in a minor release. Look through the
[list of experimental features](/about/versioning/#experimental). If your
code uses one, read the release notes before each minor upgrade.

If you call event handlers from your own server code with
`EventsDispatcher` and `TransportContext`, you use an experimental
feature. The `citry-events/1` protocol and the transports you register
in the browser are not experimental (see
[Events protocol](/about/versioning/#events-protocol)).

## Other changes in 1.0.0 { #other-changes }

These need no action in most projects:

- **A `javascript:` URL written with character references is
  dropped:** with `security_javascript="omit"`, Citry removes a
  `Script` or `Style` dependency whose URL is, for example,
  `Markup("java&#115;cript:x")`, and removes such a URL from a
  dependency's attributes. Before, Citry reported it but left it on the
  page. It already did this for the same URL written as a plain string.
- **citry-ui 0.6.0 refuses the same URL:** `CButton` `href`, `CForm`
  `action`, and a `formaction` in `CButton` `attrs` or `CSplitButton`
  `primary_attrs` raise `ValueError` for it.
- **An unknown State token version answers `stale_state`:** nothing
  changes today. If a later 1.x release changes the token format, a
  server that does not know the new version answers `stale_state`
  (HTTP 409) instead of `invalid_state` (HTTP 403), and Citry's browser
  code offers a reload.

The [1.0.0 release notes](/releases/) list every change.

## Upgrade checklist { #upgrade-checklist }

1. Upgrade to the newest 0.9.x and follow its
   [upgrade notes](#upgrade-to-0-9-first).
2. Make `CitryDeprecationWarning` an error in your
   [tests](#fix-deprecation-warnings).
3. [Upgrade](#upgrade-the-packages) `citry`, and the `citry-lsp`,
   `pygments-citry`, `citry-ui` and VS Code extension you use. Pin
   `citry>=1.0.0,<2`.
4. Set a longer `State._max_age` where a page must work after
   [24 hours](#state-tokens-expire) or stays cached longer, and keep
   every `_max_age` at one second or more.
5. Run your tests on 1.0.0.
6. [Deploy](#deploy-the-upgrade) with fresh whole-page caches.
7. Check whether your code uses an
   [experimental feature](#check-experimental), and read the
   [other changes](#other-changes).
