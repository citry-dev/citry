# Cache replay writes the same HTML as a fresh render (#871)

- **Pull request:** [#871](https://github.com/citry-dev/citry/pull/871),
  merged 2026-11-24 (6baaaa6da)
- **Reviewer:** a separate reviewing agent (correctness, the claim that a
  removed branch never ran, the check for other differences, tests,
  versioning and prose), with a security pass for markers for Citry's
  browser code and a check against the maintainers' survey of security
  advisories published for other frameworks, as the pull request
  description states. `CLAUDE.md` calls the two security checks
  Mechanism 7 and Mechanism 8. The pull request holds no report,
  comment or review thread. This record is built from the description, the
  merged change and its tests.
- **Code:** `stage_events_cache` in
  `packages/py/citry/citry/ext/events/cache.py` and `capture_instance` in
  `packages/py/citry/citry/ext/events/emission.py`, with comment updates
  in `attrs.py` and `serialize.py` in the same package. Tests, all under
  `packages/py/citry/tests/`:
  `test_cache_replay_of_an_events_component_writes_the_live_html` in
  `test_ext_cache_typed_artifact.py`, `test_events_decimal_size.py`, and
  the end-to-end files `e2e/test_cache_replay_e2e.py` and
  `e2e/test_vue_events_default_e2e.py`

## Who controls the input

The change adds no input. It stops cache replay from writing one
attribute.

Citry's render cache stores the HTML of a rendered component, and cache
replay serves that stored HTML on a later render. Each render has a render
ID. When replay served a component with Events (Citry's server events
feature), Citry wrote `data-cid="<render id>"` on the component's root
element. A fresh render of the same component does not write it, so the
cached HTML differed from the fresh HTML. A page that mixed fresh and
cached copies of one component loaded that component's browser template
twice, in two forms.

- **Who writes the attribute.** Citry wrote it, with the render ID as its
  value. The description does not say where the render ID comes from.
- **What reads it.** The description says Citry's browser code does not:
  `_vue/client.js`, `dev_checks.js` and `packages/js/citry-client` do not
  mention `data-cid`. The browser code finds an Events instance by
  `occurrence.renderId` in the manifest (the list of components that the
  server sends with the page). The per-render `data-cid-<id>` markers are
  a different attribute and are unchanged.
- **Who could write one.** The name `data-cid` stays reserved. `c-bind`
  and Citry UI still refuse it, and `serialize.py` still drops a
  `data-cid="` marker that has a value when the page's output check for
  JavaScript (the `security_javascript` setting) is `"omit"` or
  `"forbid"`, as a safety net, though no first-party code writes one.

The contributor rules in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)
(Mechanism 7) keep a list of the places where a value can reach the
browser. The description names one of them: markers for Citry's browser
code.

## How it was checked

- **A security pass for markers for Citry's browser code.**
  The reviewer found no hole. The description gives the reason: data
  cannot write a `data-cid` that Citry's browser code trusts, because
  that code does not read it. The search covered the three places named
  above, not an app's own JavaScript.
- **The claim that the removed branch never ran.** `emission.py` had a
  second place that wrote `data-cid`, on a fresh render, when
  `direct_prepared_render_active()` was false. The description says every
  render enters `typed_render_scope(direct=True)`, so the branch never
  ran. The author made the branch log each run, and the whole
  non-end-to-end suite (15,834 tests) never reached it. The change removes
  the branch. The reviewer checked the claim. The description does not say
  how.
- **A check for other differences between a fresh render and a replay.**
  The description says a script compared both for Events components with
  each kind of State, `css_data`, `js_data`, translations, nested and
  multi-root components, shared roots, slot fills, `<c-element>` and
  `security_javascript="omit"`. After the change, all outputs are equal,
  apart from newly signed State tokens. Before it, all differed.
- **A new test.**
  `test_cache_replay_of_an_events_component_writes_the_live_html` covers
  the component cache and a `<c-cache>` fragment. With the same
  render IDs and Vue app ID, the replayed serialized page equals the fresh
  one byte for byte, and the component was built once. Both cases fail
  without the change.
- **Updated assertions.** Two existing assertions that checked the staged
  `data-cid` marker now check the render ID of the entry that Citry stages for
  the replay. They prove the stored State token was accepted.
- **A real browser.** `e2e/test_cache_replay_e2e.py` and
  `e2e/test_vue_events_default_e2e.py` (79 tests) passed in Chromium. The
  replay tests click cached Events components.
- **Other runs.** The non-end-to-end `citry` suite (15,870 passed),
  `ruff`, `ruff format --check`, mypy (host and `--platform linux`) and
  `scripts/validate.py`.
- **Other frameworks' advisories (Mechanism 8).** The reviewer ran the
  check and found no hole. The description does not name the kinds.
- **Versioning.** The render cache payload is unchanged, so no contract
  version moves. The description says an entry written by 1.2.0
  would replay under the new code without the attribute, and that 1.3.0
  starts with an empty cache anyway, because `_RENDER_CONTRACT` includes
  the Citry version. The
  versioning rules do not cover the exact attributes in rendered HTML, and
  `data-cid` stays reserved. The description targets 1.3.0 as a fix.

## Ruled out

- **Data writing a `data-cid` that the browser code trusts.** The
  browser code does not read the attribute, and `c-bind` and Citry UI
  refuse the name.
- **Cached and fresh HTML differing in another way.** The check found no
  other difference apart from newly signed State tokens, which differ by
  design.
- **A stale cached entry breaking replay.** The description says an entry
  from 1.2.0 would replay without the attribute, and 1.3.0 starts with an
  empty cache.

## Fixed during the review

Nothing recorded. The description says the reviewer's prose and docs
findings were applied, and does not list them.

## Not tested

- **Browsers other than Chromium.** The end-to-end tests ran in Chromium.
  The description names no version.

## Follow-ups

The description says older design docs (`docs/design/events.md` section 5.5,
`events_plan.md` and `dependencies.md`) describe the `data-cid` attribute
that replay used to write. They were already out of date before this change
and were left as they are. It names no issue for them.

The pull request closes
[#659](https://github.com/citry-dev/citry/issues/659).
