# Own-key i18n lookups, form member reads and cookie reading (#755)

- **Pull request:** [#755](https://github.com/citry-dev/citry/pull/755),
  merged 2026-11-18 (2304edcfb), closing issues
  [#701](https://github.com/citry-dev/citry/issues/701) and
  [#703](https://github.com/citry-dev/citry/issues/703)
- **Reviewer:** a separate reviewing agent (security, a check against the
  maintainers' private survey of security bugs published for other
  frameworks, and a prose pass), as the pull request description states.
  The pull request holds no report, comment or review thread. This record
  is built from the description, the merged change and its tests.
- **Code:** `ownValue` in
  `packages/js/citry-client/src/citry-i18n-core.ts` and its callers in
  `citry-i18n-runtime.ts` and `citry-i18n-vue.ts`; `readBuiltIn`,
  `callBuiltIn`, `nodeConnected`, `readCsrfCookie` and
  `editableValueProps` in `packages/py/citry/citry/_vue/client.js`;
  `memberOf` in `packages/py/citry/citry/_vue/dev_checks.js`; `readCookie`
  in `packages/js/citry-client/src/citry-events-vue.ts`. The built files
  `runtime.js`, `events.js`, `dev_checks.min.js` and
  `ext/i18n/client/vue-plugin.source.js` are rebuilt from these. Tests:
  `i18n-own-keys.test.mjs`, `client-helpers.test.mjs`,
  `vue-events.test.mjs`, `dev-checks.test.mjs`, `citry-listeners.test.mjs`
  and `page-dom.test.mjs` under `packages/js/citry-client/test/`, and
  `packages/py/citry/tests/e2e/test_vue_named_elements_e2e.py`

## Who controls the input

The change tightens four places where Citry's browser code reads a name
or value that the page supplies:

- **Names in the browser i18n runtime.** The runtime looks up format
  profiles (named number and date formats), number and percent parsers,
  message entries, the Fluent `NUMBER` profile and bundle directions by
  name. The template author writes most names. A message ID or a profile
  name can also come from the app's Python code, which may pass request
  data. The runtime now reads only the object's own entries (`ownValue`),
  so a name such as `constructor` or `__proto__` fails with the same error
  code as any other unknown name. The browser shows the formatted text.
- **A `__proto__` prop.** The copy of an editable element's props in
  `editableValueProps` leaves out a `__proto__` key.
- **Form members.** A form control whose `name` matches a member of the
  form, such as `contains`, hides that member on the form element. The
  template author or the app's Python code chooses control names, and
  request data may supply them. Citry's runtime now reads members such as
  `isConnected`, `contains`, `dispatchEvent` and `addEventListener` on a
  component root, host or focused element from the element's prototype,
  through `readBuiltIn`, `callBuiltIn` and `nodeConnected`. The
  development checks do the same through `memberOf`.
- **The CSRF cookie.** The browser code tightens how it reads the CSRF
  cookie. Both places that read it skip a value that is not valid
  percent-encoding and use the next cookie with the same name.

Of the places in the list of where values reach the browser (Mechanism 7
in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "Addresses and keys the browser code takes from the
server", "Element `id` and `name`" and "Translated messages".

## How it was checked

- **Code read.** The reviewer read the change with a security brief for
  the three places named above.
- **Node tests.** `pnpm --dir packages/js/citry-client run check` (the Vue
  types, `tsc`, `biome` and `node --test`): 370 passed. New tests:
  `i18n-own-keys.test.mjs` (7), `client-helpers.test.mjs` (3), one cookie
  test in `vue-events.test.mjs` and one form test in
  `dev-checks.test.mjs`. Each fails against the `main` sources.
- **A real browser.** A new end-to-end test renders a form root whose
  fields are named after five form members, re-renders it with a server
  `Render`, and sends an event from it. It fails with the `main` runtime.
  The full end-to-end suite in Chromium, without the benchmark file,
  passed: 609 passed, 3 skipped.
- **Python tests that read the built runtime files:** 101 passed.
- **Other frameworks' advisories (Mechanism 8).** The reviewer checked
  these kinds from the survey: prototype keys, DOM clobbering (page
  elements whose `id` or `name` hides a built-in property), CSRF handling,
  and crashes on bad input. It found no hole.

## Ruled out

- **A built-in object member read as an i18n entry.** Every lookup named
  above reads own entries only, and the new tests cover each error code.
- **A named control replacing a member Citry's runtime calls.** The
  runtime reads those members from the prototype, and the end-to-end test
  shows the event bindings keep working on a form with such names.

## Fixed during the review

- More development-check reads and the focus restore now go through the
  prototype helpers.
- A `__proto__` prop is dropped from the copy rather than kept as a key.
- A development-checks test was added.
- The `docs/design/trust_boundaries.md` row wording was narrowed.

## Not tested

- **The artifact merge check.** Its own-key lookup in `artifactsAgree` has
  no test of its own.
- **Other browsers.** The end-to-end suite ran in Chromium only.

## Follow-ups

- Vue's own code still reads form members directly, so a control named
  `addEventListener` stops the Vue app that renders the form. This limit
  is documented in [Check form field
  names](https://citry.dev/security/#check-form-field-names) and in the
  changelog entry for #703.
- No issue tracks a separate test for the `artifactsAgree` lookup.
