# Translated text in cached renders (#658)

- **Pull request:** [#658](https://github.com/citry-dev/citry/pull/658),
  merged 2026-11-14 (885e19085). It fixes
  [#631](https://github.com/citry-dev/citry/issues/631).
- **Reviewer:** an independent reviewer, with a separate security pass
- **Code:** `packages/py/citry/citry/ext/i18n/extension.py`
  (`_bindings_allocated_outside`, `_bindings_from_wire`,
  `export_render_cache`), `packages/py/citry/citry/ext/i18n/bindings.py`
  (`split_binding_id`, `is_binding_id`),
  `packages/py/citry/citry/ext/cache/replay.py`
  (`_browser_binding_operands`) and
  `OnRenderCacheExportContext.browser_binding_operands` in
  `packages/py/citry/citry/extension.py`. Tests in
  `packages/py/citry/tests/test_i18n_cache.py`,
  `packages/py/citry/tests/test_ext_cache_typed_artifact.py`,
  `packages/py/citry/tests/test_i18n_usage.py` and
  `packages/py/citry/tests/e2e/test_cache_replay_e2e.py`. The design text
  is in `docs/design/i18n.md` and `docs/design/caching.md`.

## Who controls the input

This change fixes a page that broke when translated text came out of the
render cache (the store of output from `<c-cache>` fragments and cached
components, which Citry reuses on later requests). The browser threw
`binding ... is not active` and the Vue app did not start.

A `$c-tr` attribute on an element marks it as text that the browser
translates again when the language changes. The browser finds each such
element by a binding ID, and the server sends the browser one definition
(the message and its values) for every ID the page names. Citry builds an
ID from the render ID (the fresh ID each component gets on every render)
of the component whose template holds the element. The binding belongs to
an owner, a client provider (the component that supplies the browser i18n
runtime to the ones below it). A stored output (an "entry") can include
elements from a component outside the stored part: a `<c-cache>` fragment
inside a page template, or slot content that a caller passes to a cached
component. The cache then kept the first render's ID and no definition for
it, so a render served from the cache named an ID the page never defined.

This change copies the bindings of components outside the stored part into
the stored entry. Writing the entry is "export". When a later request
reads it back ("replay"), every binding gets a fresh ID. The cache
boundary is the `<c-cache>` component, or the cached component, whose
output the entry holds. The inputs, and who first supplies them:

- **Binding IDs and the `data-citry-i18n-binding` markers** (the
  attribute values that list the IDs an element uses). Citry writes
  them. No template author or request supplies an ID. They do pass through
  the cache backend, which holds the stored entry between requests. Write
  access to the cache is already trusted: `docs/design/caching.md`
  (section 7.1) says cached HTML is trusted application output, so cache
  write access can inject markup and scripts.
- **The values expression of a `$c-tr` attribute.** This is JavaScript that
  the browser compiles to compute the values of a message. Only the
  template author writes it. `_apply_directive` in `bindings.py` takes it
  from the template text, and raises `TypeError` for a value that is
  neither a bare attribute nor written text.
- **Message values.** Values the app passes to `tr()` go into the stored
  binding, as they already did for bindings inside the entry. Bindings
  copied from components outside the entry are stored the same way.

The risk is that a stored or copied ID, marker or expression reaches the
browser in a form the server did not write: an ID the page never defines
(the page breaks), an ID or marker that data could choose, or an
expression the browser runs without a template author having written it.

## How it was checked

The pull request says an independent reviewer went through the change, with
a separate security pass, and a check against the maintainers' survey of
published advisories for other frameworks (the Mechanism 8 check in
`CLAUDE.md`). The security pass named three places from the Mechanism 7
list in `CLAUDE.md`: markers for Citry's browser code, JavaScript and JSON,
and translated messages. The reviewer found no security hole and no
confirmed bug. A separate prose review ran twice.

The checks in the repository:

- **Scenario tests.** `test_i18n_cache.py` (44 tests, by the pull
  request's count) renders each case more than once and checks that every
  binding ID named in the HTML has exactly one definition. The cases are a
  fragment with text and attribute bindings, a component cache with a
  caller's slot content, a fragment at the root of a child template, a
  provider inside the fragment, nested fragments, one fragment used twice,
  a fragment per loop item, a fragment inside slot content passed to
  another component, a boundary with its own binding plus a caller's, and
  an entry made under an outside provider and replayed without one. The
  pull request says the scenario tests fail on `main` before this change.
- **Each new check was removed in turn.** The pull request says it removed
  each new check once to confirm that a test fails.
- **Forged stored data.** Tests hand the replay code malformed IDs
  (no separator, no number, upper case, trailing letters, a space in the
  owner part, a number of thousands of digits, other digit scripts, a
  decimal number, and a value that is not a string) and a repeated ID.
  They also test the three export refusals below, and the skip for a
  provider the replaying render lacks.
- **A real browser.** `test_cache_replay_e2e.py` has a browser test with a
  page that holds a fragment and a component whose root is `<c-cache>`. The
  pull request calls it a Chromium test. It checks four fresh IDs on the
  second render, the texts, and that `$i18n.switchLocale('cs-CZ')`
  translates every element. The pull request says it fails with
  `binding ...~i18n-1 is not active` on `main` before this change.
- **One existing test changed.**
  `test_render_cache_remaps_translation_binding_records_and_html_markers`
  in `test_i18n_usage.py` gave a placeholder string as the client
  provider's owner. Replay drops a provided value that is not a
  render ID, so the new check skipped the entry. The test provides a
  valid ID.
- **Review findings.** The review's performance, robustness and test-gap
  findings were fixed and checked again (see "Fixed during the review").

## Ruled out

- **An ID the page does not define.** Export asks the render cache which
  binding IDs the stored HTML names, and copies the matching bindings and
  the markers that list them from the components that allocated them into
  the i18n record of the cache boundary (the entry's stored i18n data for
  that component). Replay renames them to fresh IDs, as it
  does for bindings written inside the entry. Each use of a cached
  fragment gets its own IDs, including repeated and nested uses.
- **A stored ID that Citry could not have written.** Replay accepts an ID
  only if it looks like `<render ID>~i18n-<number>` with an ASCII number of
  at most 9 digits (`split_binding_id`), and skips the entry when an ID is
  malformed or repeats in one record. A skipped entry renders again and is
  stored again. The 9-digit limit also keeps `int()` away from huge digit
  strings.
- **Export storing something it cannot rename.** Export refuses the entry
  (it stores nothing, and the part renders again on every request) when a
  stored part names an ID that no record holds, when one marker lists both
  IDs the stored parts use and IDs they do not, or when the boundary has no
  record to hold the outside bindings.
- **A client provider that the replaying render lacks.** When a stored
  binding belongs to a client provider outside the entry and the replaying
  render has none, replay skips the entry and the part renders again.
  Using the stored entry anyway (a cache hit) would fail the request
  later.
- **An expression the browser compiles without an author writing it.**
  This change does not alter the checks that already guard it. Replay
  restores a part's browser binding only if a live template in the process
  produced the same helper, target, attribute name and expression
  (`_require_produced_binding`), and a part's `$c-tr` values expression
  only if a template wrote the same text
  (`_require_authored_values_expression`, which uses
  `is_authored_values_expression`).
- **The expression stored in a binding's own record.** On replay it only
  has to be a non-empty string. The pull request calls this an
  inconsistency, not a way to run code: the browser stores it as metadata
  and does not run it. At the merged commit, `citry-i18n-runtime.ts` is the
  only file under `packages/js/citry-client/src` that reads the field, and
  it only checks the field and copies it into the binding object.
- **Entries from another Citry version.** The render contract that the
  cache checks includes the installed Citry version
  (`_RENDER_CONTRACT` in `ext/cache/artifact.py`, which the read path
  compares with the stored `render_contract`), so a worker on another
  version does not replay an entry written by this one. See "Not tested"
  for what this does not cover.

## Fixed during the review

- A stored ID with a very long number could make the ID check crash. The
  limit of 9 digits fixes it, with a test.
- The cost of export grew with the number of cached rows on the page. The
  collector keeps lookups by ID (`record_by_id`, `marker_by_id`), and
  export reads only the stored components' records.
- Other performance, robustness and test-gap findings, which the pull
  request does not itemize.

## Not tested

- **Replay does not check that every stored binding ID was renamed.** If a
  stored entry's parts and its i18n record disagree, it still replays as a
  cache hit, and the page can name IDs with no definition. Writing such an
  entry needs write access to the cache, which the design already trusts,
  and the code behaved the same way before this change. A reviewer
  reproduced it with a worker that lacked the fix writing entries that a
  worker with the fix then read, using two source trees with the same
  version string. The pull request has no test across a real version bump.
- A value passed in `render(provides=...)` for `citry_i18n_client` (the key
  that names the client provider) that is not shaped like a render ID.
  Every request then skips the entry and stores a new one, so the entry
  never hits. The page stays correct, and nothing in the package
  supplies the key this way.
- Whether `export_render_cache` can see an empty `instances` list (it reads
  `ctx.instances[0]` without a check). Nobody could build such a list.
- A stored binding whose owner is a component outside the entry,
  which the record names by its depth among the cache boundary's
  ancestors, replayed at a different depth, and components with
  `simple=True` (a component option that renders the component in its
  caller's HTML frame). Neither was proven either way.
- Browsers other than Chromium for the new browser test (the test file
  does not choose a browser itself, so this rests on the pull request).
- The pull request lists no separate check of the message values stored
  in bindings copied from components outside the entry.
- The pull request says the browser test files (the cache replay file and
  the four i18n files, 34 tests) passed before a rebase onto `main` and
  were not run again afterward, because the rebase did not touch them.
- The pull request says the full suite, `scripts/check.py` and the Rust
  checks were not run locally. Its focused subset had 20 failures that
  also occur without this change, because the local `citry_core` build was
  older than the source. CI with a fresh build is the real check.

## Follow-ups

- [#666](https://github.com/citry-dev/citry/issues/666): the three open
  checks above (check that replay renamed every ID, malformed provided
  value, unguarded `instances[0]`).
- [#663](https://github.com/citry-dev/citry/issues/663):
  `docs/design/caching.md` section 7.1 says cache artifacts hold no
  original render IDs, but the i18n payload keeps the original binding IDs
  as the names replay renames from. Correct the text or change the payload.
- The pull request also lists problems that exist without this change.
  Public issues with matching titles are
  [#659](https://github.com/citry-dev/citry/issues/659) (a replayed
  component with Events gets a `data-cid` that a live render skips),
  [#660](https://github.com/citry-dev/citry/issues/660) (an Events revision
  of a region with `<c-i18n c-client>` fails on a config key-order
  mismatch) and
  [#661](https://github.com/citry-dev/citry/issues/661) (`Cache` on a
  component returned from `on_render` raises on a hit). The list also
  names slow storing of a component cache entry with hundreds of its own
  `$c-tr` bindings, which the entry's size limit then refuses.
