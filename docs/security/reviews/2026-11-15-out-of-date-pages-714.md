# Out-of-date pages and the rolling-deploy check (#714)

- **Pull request:** [#714](https://github.com/citry-dev/citry/pull/714),
  merged 2026-11-15 (0cc86a3f8), part of the 1.0.0 work
  ([#624](https://github.com/citry-dev/citry/issues/624))
- **Reviewer:** several independent reviews, as the pull request
  description records: a first review (technical, security, advisory
  survey and prose), a later review of the production change, and a review
  of the rolling-deploy count check. The saved `docs-cold-reader` agent
  read the docs twice. This record is built from the pull request
  description, the merged change and its tests. The description gives the
  reviewers' conclusions and the routes they classified, not how each
  review worked.
- **Code:** `packages/js/citry-client/src/citry-events-vue.ts`
  (`reportFailure`, the host's `reportOutOfDate`) and
  `packages/js/citry-client/src/citry-fragments.ts` (`load`, `loadOnce`,
  the `citry:fragments:stale` event), with the built files
  `packages/py/citry/citry/_vue/events.js`, `fragments.js`, `runtime.js`
  and `client.js`; `scripts/rolling_deploy/check.py` and `scenario.py`;
  the `rolling-deploy` job in `.github/workflows/py--citry--publish.yml`;
  tests in `packages/js/citry-client/test/` (`vue-events.test.mjs`,
  `runtime-events.test.mjs`, `fragment-nonce.test.mjs`) and under
  `packages/py/citry/tests/` (`test_rolling_deploy_script.py`,
  `test_events_tokens.py`, `test_vue_dev_checks.py`,
  `test_ci_workflows.py`, `e2e/test_vue_component_context_e2e.py` and
  `e2e/test_vue_transparent_root_e2e.py`)

## Who controls the input

A page can be out of date in two ways. Its State token (the signed or
stored value that carries a component's State between requests) can have
expired, or a deploy can have put another Citry release behind it. A
rolling deploy replaces servers one at a time, so for a while a page
rendered by one release sends its requests to a server running another.

The browser may then get something it cannot read: a render from another
release, or a Vue fragment (a piece of HTML with Vue behavior that a page
loads after it has started) that declares another protocol (its format
name). The change makes the runtime fail these with the error code
`stale_state`. A failed event call goes through one report path in the
Events bridge (the runtime part that sends event calls and reports how
they ended): the cancelable `citry:events:stale` event, then Citry's own
once-per-page report, then `citry:events:error`. A refused fragment fires
the new `citry:fragments:stale` event and then Citry's own report.

Citry's own report is the part that does something in the browser:

- **In development mode** (`configuration.development === true`), it asks
  with the built-in `confirm("This page is out of date. Reload to
  continue?")`, once per page.
- **In production,** it asks nothing and reloads nothing. It writes one
  `console.warn` per page that names the cause and links the docs (a
  maintainer decision). Production is the page's own mode. On a page that
  started no Citry app, a fragment's own development flag decides.
- **A listener that cancels the event** replaces Citry's report in both
  modes.

The inputs, by who first supplies them:

- **The renders and fragments the browser cannot read.** The server of the
  app, running another Citry release, writes them. Request data does not
  choose them. A person who can inject HTML into a page can write a
  fragment block of their own, including its protocol field and its
  development flag.
- **The report texts and the reload.** Citry's runtime holds the question
  and the warning as constants. The only navigation is a reload of the same
  URL after the visitor agrees, and that happens only on a development
  page.
- **Listeners on `citry:events:stale` and `citry:fragments:stale`.** The
  app author's JavaScript supplies them. The docs warn against reloading
  from a listener, because a cached page with an expired token would loop.
- **A custom event transport and the public `Citry.events.applyActions`.**
  The app's code supplies them, so they are author-only by design.
- **The rolling-deploy check's inputs.** The previous published `citry`
  (installed from PyPI) and the candidate (a wheel or a checkout) are the
  inputs. The maintainers' release qualification runs it, never a pull
  request.

Of the places in the list of where values reach the browser (Mechanism 7 in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "JavaScript and JSON" (Events responses), "Navigation"
(`location.reload`), "Addresses and keys the browser code takes from the
server" (the Vue fragment data block), and "The CSP nonce".

## How it was checked

- **Routes the reviewer classified.**
  - Safe: the server's own answers (same-origin), and a fragment block
    under a nonce-based CSP. That block is refused before the new check,
    and a node test covers it.
  - Author-only by design: a custom transport or the public `applyActions`.
  - A nuisance, not a hole: on a page without a nonce-based CSP (a
    hash-based CSP or none), injected markup can raise the report (a console warning in production) and use
    up the once-per-page report. Without CSP, the same injection can
    already run script.
- **The production change.** Partway through the pull request, the
  maintainer decided that production pages would not ask. A later
  independent review of that change found no security hole and confirmed
  that production never asks. A refused fragment now follows the page's own
  mode, which comes from the first app that `startDocument` (the runtime
  function that starts a page's Vue apps) starts. So a fragment block
  injected into a production page without a nonce cannot make it ask the
  question.
- **Node tests** (`pnpm --dir packages/js/citry-client run check`, 334
  passed):
  - the bridge reports `stale_state` failures on every path: a waited
    action, a `wait: false` action, and public `applyActions` refused in
    preflight (the checks the runtime makes on a server answer before it
    applies the answer);
  - a fragment with another protocol, or a top-level field other than
    `vue`, fires `citry:fragments:stale` (on the block, or on `document`
    once the block is gone) and reports once: a question in development, a
    warning in production, nothing when a listener cancels it; a fragment
    refused for its nonce does not report;
  - an injected block on a production page, and on a development page;
  - `registerDefinition` treats another helper contract (the version of the
    render helper functions that a prepared Vue render names) as
    `stale_state`.
- **End-to-end, script, token and development-check tests:** 742 passed
  and 4 skipped (the author's private environment had no Django or
  uvicorn). The stale-token and helper-contract tests run in both modes.
  They check that a development page shows exactly one dialog, and that a
  production page shows none and writes one console warning that links the
  docs. A server test checks that the development flag reaches a
  fragment's `prepared` data, and the fragment end-to-end test fails if any
  dialog opens in production.
- **The rolling-deploy check.** `check.py` installs the previous published
  `citry` and the candidate in two environments. `scenario.py` runs the
  same app on both, in each direction (old page to new server, then new
  page to old server). It renders pages whose State is signed or stored in
  a shared `DiskCache` (a cache that keeps its entries in files), sends
  their event calls to the other release through the WSGI app, compares the
  runtime and definition files by SHA-256, and renders a cached component
  again. An answer must be a success or `stale_state`. The counters start
  at 41, away from State's default of 0, so a server that ignored the
  page's State would show another count. A successful call must render 42
  and the next call 43. `test_rolling_deploy_script.py` has 31 tests, which
  cover which version pairs are promised, the pick of the previous release
  from a synthetic PyPI payload, how answers are classified, the digest
  check and the exit rule.
- **A smoke run against 0.9.0.** The description pastes the output of
  `scripts/rolling_deploy/check.py --previous 0.9.0` on `2d220e15f`: 14
  checks, all OK, reported only, because 0.9.0 to 0.9.0 is not a 1.x
  deploy.
- **Other frameworks' advisories (Mechanism 8).** The reviewer read the
  maintainers' private survey of security bugs published for other
  frameworks (Mechanism 8 in `CLAUDE.md`) and checked these kinds:
  hydration (`hydration`), trusting the shape of data (`trusted-shape`),
  script loading (`script-load`), open redirects (`open-redirect`), script
  from URLs (`xss-url`), DOM clobbering (`dom-clobber`), `__proto__` keys
  (`proto`), CI workflows (`ci`) and cache keys (`cache-key`). The change
  introduces none of them.
- **Other runs.** `scripts/validate.py`, `test_ci_workflows.py` (the
  `--core-wheel` consumer count updated to 3), `ruff` and `mypy` (also
  with `--platform linux`) passed.

## Ruled out

- **A production page asking the visitor anything.** The question exists
  only in development mode. The first report decides for every app on the
  page and for fragments, because the once-per-page flag is shared. The
  production path writes a console warning and nothing else. The
  end-to-end tests check that production asks no question, and the
  fragment test fails if any dialog opens there. The one case the tests do
  not cover is a page with no Citry app of its own (see "Not tested").
- **Data choosing where the page goes.** The question and warning texts are
  constants, and the only navigation is a reload of the same URL after the
  visitor agrees.
- **A fragment block bypassing a nonce-based CSP.** On a page with a nonce
  CSP, a block without the page's nonce is refused before the out-of-date
  check, and a test shows it makes no report.
- **A failure path that skips the report.** The reporting path covers
  queued calls, `wait: false` actions and public `applyActions`,
  including its preflight.
- **The rolling-deploy check hiding a failure.** For a promised deploy (two
  releases of the same major version, 1 or later), a stage that crashes
  counts as a failure. Only a promised deploy can fail the run. For any
  other pair, every result is reported and the exit code is 0, except
  that the check fails when it cannot find the previous release on PyPI.
- **A success that proves nothing.** The counters start at 41, a call must
  render 42 and then 43, and a render with no count, another count or two
  counts fails.

## Fixed during the review

- Public `applyActions` gave no out-of-date report, because its preflight
  ran outside the reporting path. It is now reported, and the test makes
  the failure happen in preflight.
- Other preflight checks could fail a render from a newer release with a
  plain error first. The helper contract is now checked first.
- A refused fragment now follows the page's own mode, with node tests for
  an injected block on a production page and on a development page, and a
  server test that the development flag reaches a fragment's `prepared`
  data (fixed in `179611332`).
- The rolling-deploy check judged one direction. It now runs both.
- A crash failed even report-only runs. Stages that cannot run are now
  reported as failures and fail only a promised deploy.
- File checks looked only at HTTP 200. They now compare SHA-256, and a page
  with no definition file fails.
- The counters started at State's default of 0, so a server that ignored
  the page's State would also have shown 1. They now start at 41. The same
  review of the count check (`f047b934a`, fixed in `2d220e15f`) corrected
  the skip reason, which now says "left the page out of date" also when the
  page refused a render with other helpers, accepted a token refreshed by a
  protocol `state` action, and added tests for each of these.
- The cached-render result now says whether the other release's entry was
  reused or rendered again.
- Wording and docs fixes from the reviewers and the two `docs-cold-reader`
  passes: the error text and docs say "another Citry release" instead of "a
  newer one"; the changelog no longer says pages from the older release
  offer a reload; the spec no longer clashes with its own 409 pairing for
  `stale_state`; the docs say what a visitor who declines sees, list the
  causes of an out-of-date page (including dropped server-stored State and
  unknown token versions), and stop overstating the effect (only calls
  from that component fail); the example cancels the events; and docstrings,
  the upgrade guide and the Versioning page match the production behavior.

## Not tested

- **The `rolling-deploy` job in CI.** The description says it could not be
  timed or run there before the merge, because a qualify run needs a
  release candidate on `main`.
- **Renders that differ in a way other than the helper contract.** The
  check judges a render by its helper contract only. Another change to the
  render format is not detected, because running the old runtime's
  preflight on the new answer would need node or a browser in the job.
- **The second click across releases.** The token the serving release
  returns is not sent back to the rendering release. The second call goes to
  the same release.
- **A fragment on a page that started no Citry app.** There the fragment's
  own development flag counts. The description records tests for an injected
  block on a production page and on a development page, but none for a
  page without an app of its own.
- **Django and uvicorn.** The author's private environment had neither, so
  4 end-to-end tests were skipped.
- **The full repository gate.** The author did not run it, because its Rust
  phase needs a build that the author's environment did not allow.
- **Unrelated failures in the author's private environment.** The
  non-browser `pytest` run passed apart from failures caused by that
  environment: no `yaml` or `citry_ui`, pydantic 2.14.3 against the locked
  2.14.1, and no `tzdata`, all in unrelated files.

## Follow-ups

- [#720](https://github.com/citry-dev/citry/issues/720) (v1.1): found
  during this review and present before it. On a page whose CSP does not
  use nonces, injected markup can start a Vue fragment whose definition
  script URLs it chooses. The issue checks which URLs the fragment loader
  accepts.
