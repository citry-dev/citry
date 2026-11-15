---
title: Upgrade to Citry 1.0.0
description: Move a Citry 0.9.x project to 1.0.0, fix deprecation warnings, and handle State tokens that now expire after 24 hours.
---

# Upgrade to Citry 1.0.0

Use this guide to move a project to Citry 1.0.0, the first stable
release. Citry 0.9.0 was the last release with planned breaking changes,
so most projects upgrade without changing code. The change most projects
notice is that [State tokens now expire](#state-tokens-expire) after 24
hours.

Work from the top. The [checklist](#upgrade-checklist) at the end lists
every step.

## Upgrade to 0.9.x first { #upgrade-to-0-9-first }

If your project runs Citry 0.8.x or older, upgrade it to the newest 0.9.x
release before you move to 1.0.0:

1. Follow the "Upgrading from" notes of each release you skip, oldest
   first, in the [release notes](/releases/). For 0.8.x, that is
   [Upgrading from 0.8.x](/releases/v0.9.0/#upgrading-from-08x).
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

Run your tests on 0.9.x and fix every use the errors point to. Each
warning names the line in your code and what to use instead.
[Deprecations](/about/versioning/#deprecations) shows how to see the
warning in a running server too.

## Upgrade the packages { #upgrade-the-packages }

Upgrade Citry and the language server together:

```console
python -m pip install -U "citry>=1.0.0,<2" \
  "citry-lsp>=1.0.0,<2"
```

- Citry 1.0.0 installs the `citry-core` version it needs. Depend on
  `citry`, not on `citry-core`.
- If you use the [UI library](/ui-library/), add
  `"citry-ui>=0.6.0,<0.7"` to the same command. citry-ui 0.6.0 needs
  Citry 1.0.0 or later, and stays on 0.x, so pin one minor release.
- If you use the [VS Code extension](/ide/vscode/), update it to 1.0.0
  when you upgrade `citry-lsp`.

Then allow any 1.x release in your project's dependencies, as shown in
[Pin and upgrade](/about/versioning/#pin-citry).

## State tokens expire { #state-tokens-expire }

After the upgrade, a page left open for more than 24 hours can fail its
next event call: the call does not run its handler, it gets a
`stale_state` error, and Citry's browser code asks once whether to reload
the page. After the reload, the page works again.

This happens because of how Citry keeps State. Unless a component sets
`State._storage = "server"`, Citry sends its State to the page as a
signed string, the State token. In 0.9.x, a token worked until you
changed the signing secret. In 1.0.0, it stops working 24 hours after
Citry issues it, as server-stored State already did.

- Citry issues a new token when it renders the component and after a
  call that changes State. Only pages whose State has not changed for
  24 hours are affected.
- Tokens issued before the upgrade also expire 24 hours after Citry
  issued them.
- No setting turns expiry off. To keep tokens working for longer, set a
  longer `_max_age`:

    ```python
    from datetime import timedelta

    class State:
        _max_age = timedelta(days=7)
    ```

[State token lifetime](/about/versioning/#state-token-lifetime) has the
rule, and [Treat State as input](/security/#treat-state-as-client-input)
explains why tokens expire.

### Minimum `_max_age` { #max-age-minimum }

A `State._max_age` shorter than one second, including `timedelta(0)`,
now raises `ValueError` when the class is defined. Before, it made every
token expire as soon as Citry issued it. Remove the setting, or set one
second or more.

## Deploy the upgrade { #deploy-the-upgrade }

Follow [Deploy a Citry upgrade](/advanced/web-frameworks/#deploy-a-new-version):
clear whole-page caches, and give every server the same cache during a
rolling deploy.

Citry promises that open pages keep working during a rolling deploy
only between two 1.x releases (see
[Rolling deploys](/about/versioning/#rolling-deploys)). A page opened on
0.9.x before the deploy may need a reload.

## Experimental features { #check-experimental }

Citry 1.x keeps the documented API working, except for features marked
experimental, which may change in a minor release. Look through the
[list of experimental features](/about/versioning/#experimental). If your
code uses one, read the release notes before each minor upgrade.

One of them is running event calls from your own server code with
`EventsDispatcher` and `TransportContext`. The `citry-events/1` protocol
and custom browser transports are not experimental (see
[Events protocol](/about/versioning/#events-protocol)).

## Other changes in 1.0.0 { #other-changes }

These need no action in most projects:

- **An unknown State token version answers `stale_state`:** if a later
  Citry release changes the State token format, a page from the other
  release gets `stale_state` (HTTP 409) during a deploy, and Citry's
  browser code offers a reload. Before, it got `invalid_state` (HTTP
  403) and an error. If your monitoring or a custom transport treats
  `invalid_state` as the sign of an outdated page, check `stale_state`
  instead.
- **`javascript:` URLs written as `Markup` with character references are
  refused:** with `security_javascript="omit"`, Citry drops a `Script` or
  `Style` dependency whose URL is written this way, such as
  `Markup("java&#115;cript:x")`. In citry-ui, `CButton` `href`, `CForm`
  `action`, and a `formaction` in `CButton` `attrs` or `CSplitButton`
  `primary_attrs` raise `ValueError` for such a URL. Both already
  refused the same URL written as a plain string.

The [1.0.0 release notes](/releases/) list every change.

## Upgrade checklist { #upgrade-checklist }

1. Upgrade to the newest 0.9.x and follow its
   [upgrade notes](#upgrade-to-0-9-first).
2. Make `CitryDeprecationWarning` an error in your tests and
   [fix every warning](#fix-deprecation-warnings).
3. [Upgrade](#upgrade-the-packages) `citry`, `citry-lsp`, and, if you use
   them, `citry-ui` and the VS Code extension.
4. Set a longer `State._max_age` where a page must work after
   [24 hours](#state-tokens-expire), and keep every `_max_age` at one
   second or more.
5. [Deploy](#deploy-the-upgrade) with fresh whole-page caches.
6. Check whether your code uses an
   [experimental feature](#check-experimental).
