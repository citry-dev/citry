---
title: Upgrade to Citry 1.0.0
description: Move a Citry project to 1.0.0, prepare for deprecation warnings, and handle State tokens that now expire after 24 hours.
---

# Upgrade to Citry 1.0.0

How to move a project to Citry 1.0.0, the first stable release. Citry
0.9.0 made the last large set of breaking changes, so most projects need
no code changes. The one change most projects notice:
[State tokens](#state-tokens-expire) (the signed strings that carry a
component's [State](/events/state/) to the page) expire after 24 hours.

## Upgrade steps { #upgrade-checklist }

1. Upgrade to the newest 0.9.x and follow its
   [upgrade notes](#upgrade-to-0-9-first).
2. Make `CitryDeprecationWarning` (Citry's warning for a feature that
   is going away) an error in your [tests](#fix-deprecation-warnings).
3. [Upgrade the packages](#upgrade-the-packages) and pin
   `citry>=1.0.0,<2`.
4. Set a longer `State._max_age` where a page must work
   [after 24 hours](#state-tokens-expire) or sits in a whole-page cache
   for longer than that. Keep
   every `_max_age` at one second or more.
5. [Add a listener for out-of-date pages](#out-of-date-listener), so
   visitors see a message when a call fails with `stale_state`.
6. Run your tests on 1.0.0.
7. [Deploy](#deploy-the-upgrade) with fresh whole-page caches.
8. Check whether your code uses an
   [experimental feature](#check-experimental), and read the
   [other changes](#other-changes).

Skip steps 4 and 5 if no component uses server events.

## Upgrade to 0.9.x first { #upgrade-to-0-9-first }

Move to the newest 0.9.x. Already on 0.9.x: do only step 2 of this
list. On an older release:

1. Follow the "Upgrading from" notes of each release you skip, oldest
   first, in the [release notes](/releases/). From 0.8.x:
   [Upgrading from 0.8.x](/releases/v0.9.0/#upgrading-from-08x).
2. Run your tests and your app on 0.9.x, and fix what fails.

One release line at a time keeps each failure next to the notes that
explain it.

## Fix deprecation warnings { #fix-deprecation-warnings }

Make `CitryDeprecationWarning` an error in your tests:

```toml
# pyproject.toml
[tool.pytest.ini_options]
filterwarnings = [
    "error::citry.CitryDeprecationWarning",
]
```

- Citry 0.9.x deprecates nothing, so expect no failures today.
- Why add it anyway: a 1.x minor release may deprecate a feature, and
  Python hides the warning in most programs. The setting turns each use
  into a failing test.
- To see the warning in a running server:
  [Deprecations](/about/versioning/#deprecations).

## Upgrade the packages { #upgrade-the-packages }

```console
python -m pip install -U "citry>=1.0.0,<2"
```

Add the packages you use to the same command:

- `"citry-lsp>=1.0.0,<2"`: the language server behind editor support.
  If you use the [VS Code extension](/ide/vscode/), update it to 1.0.0
  at the same time.
- `"pygments-citry>=1.0.0,<2"`: Citry syntax highlighting for Pygments.
- `"citry-ui>=0.6.0,<0.7"`: the [UI library](/ui-library/).
    - 0.6.0 needs Citry 1.0.0 or later.
    - Still 0.x, so pin one minor release.

Then:

- Change the Citry entry in `pyproject.toml` or your requirements file
  to `citry>=1.0.0,<2`, so later installs stay on 1.x (see
  [Pin and upgrade](/about/versioning/#pin-citry)).
- Depend on `citry`, not `citry-core`. Citry installs the `citry-core`
  version it needs.

## Handle State expiry { #state-tokens-expire }

If a component's `State` sets no `_max_age` and its page's State has
not changed for 24 hours:

- the next event call fails with `stale_state`, without running its
  handler;
- in production Citry shows the visitor nothing and writes a console
  warning; only a page rendered in development mode asks whether to
  reload;
- until the visitor reloads, every call from that component fails the
  same way.

Fix: set a longer `_max_age` in the `State` class inside the component.
No setting turns expiry off.

```python
from datetime import timedelta

class State:
    _max_age = timedelta(days=7)
```

Details:

- **New tokens:** Citry issues a new token on every render of the
  component and after every call that changes State.
- **A longer `_max_age`** applies to tokens Citry issues after the
  upgrade.
- **Tokens issued before the upgrade:** expire 24 hours after Citry
  issued them, whatever `_max_age` says.
- **Whole-page caches** (in your CDN or web framework): a cached page
  carries the token it was rendered with. If the cache keeps pages
  longer than 24 hours, set `_max_age` at least that long. Otherwise
  visitors get an expired token from the cache, and reloading does not
  help.
- **[Render cache](/performance/caching/):** an entry whose token has
  expired is rendered again, so a `ttl` over 24 hours needs a matching
  `_max_age` to save any work.

Why: unless a component sets `State._storage = "server"`, Citry sends
its State to the page as a signed string, the State token. In 0.9.x, a
token from a component with no `_max_age` worked until you changed the
secret Citry signs it with. Now it expires after 24 hours, like
server-stored State. See
[State token lifetime](/about/versioning/#state-token-lifetime) and
[Treat State as input](/security/#treat-state-as-client-input).

### Set a valid `_max_age` { #max-age-minimum }

- Minimum: one second.
- A shorter value, `timedelta(0)` included, raises `ValueError` when
  Python imports the component.
- In 0.9.x, a shorter value made every token expire as soon as Citry
  issued it.

## Tell visitors about out-of-date pages { #out-of-date-listener }

In 1.0.0, Citry shows a production visitor nothing when an event call
fails with `stale_state`. That covers an expired token, but also State
the server dropped, a changed secret, and a deploy. Calls from that
component keep failing until the visitor reloads the page. So in every
app that uses server events, add a listener that tells visitors the
page is out of date, as
[Handle out-of-date pages](/reference/browser-apis/#out-of-date-pages)
shows.

## Deploy the upgrade { #deploy-the-upgrade }

Follow [Deploy a Citry upgrade](/advanced/web-frameworks/#deploy-a-new-version):

- clear cached copies of whole pages (in your CDN or web framework);
- give every server one shared cache while you upgrade servers one at
  a time (a rolling deploy).

Open pages keep working during a rolling deploy only between two
1.x releases (see [Rolling deploys](/about/versioning/#rolling-deploys)).
A page opened on 0.9.x may show components that do not start until the
visitor reloads it.

## Check experimental APIs { #check-experimental }

Experimental features may change in a minor release.

- The list: [Experimental features](/about/versioning/#experimental).
- Example: calling event handlers from your own server code with
  `EventsDispatcher` and `TransportContext`.
- Not experimental: the `citry-events/1` protocol and the transports
  you register in the browser (see
  [Events protocol](/about/versioning/#events-protocol)).
- If your code uses one, read the release notes before each minor
  upgrade.

## Other changes in 1.0.0 { #other-changes }

No action needed in most projects:

- **`javascript:` URLs written with character references:**
    - with `security_javascript="omit"`, Citry removes a `Script` or
      `Style` dependency whose URL is, for example,
      `Markup("java&#115;cript:x")`, and removes such a URL from a
      dependency's attributes;
    - before, Citry reported it but left it on the page;
    - citry-ui 0.6.0: `CButton` `href`, `CForm` `action`, and a
      `formaction` in `CButton` `attrs` or `CSplitButton`
      `primary_attrs` raise `ValueError` for it;
    - Citry and citry-ui already refused the same URL written as a
      plain string.
- **Unknown State token version:** nothing changes today. If a later
  1.x release changes the token format, a server that does not know the
  new version answers `stale_state` (HTTP 409) instead of
  `invalid_state` (HTTP 403), and Citry fires `citry:events:stale`.

Every change: the [1.0.0 release notes](/releases/v1.0.0/).
