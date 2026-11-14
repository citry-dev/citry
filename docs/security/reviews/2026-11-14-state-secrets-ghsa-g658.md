# Empty secrets and State token storage (GHSA-g658)

- **Advisory:**
  [GHSA-g658-7whm-p526](https://github.com/citry-dev/citry/security/advisories/GHSA-g658-7whm-p526),
  published 2026-11-14, severity medium (CVSS 3.1 score 6.5)
- **Affected and fixed versions:** `citry >= 0.3.0, < 0.8.0`; fixed in
  `citry` 0.8.0
- **Fix:** `210bff486`. `Citry(secret=...)` raises an error for a secret, or
  a list entry, that is empty, only whitespace, or not a plain `str`, and
  each component checks a State token by the storage mode it declares.
- **Reviewer:** a separate reviewing agent
- **Code:** `packages/py/citry/citry/settings.py` (`is_usable_secret`,
  `_validate_secret`, called from `CitrySettings.__post_init__`);
  `packages/py/citry/citry/ext/events/tokens.py` (`verify_state_token`,
  `_refuse_other_form`, `_verify_signed`, `_normalize_secrets`);
  `packages/py/citry/citry/ext/events/dispatcher.py` and
  `packages/py/citry/citry/ext/events/cache.py` (the two callers of
  `verify_state_token`); `packages/py/citry/citry/contrib/django.py`
  (`secret`). Tests: `packages/py/citry/tests/test_citry.py`,
  `packages/py/citry/tests/test_events_tokens.py`
  (`TestStorageAndUnusableKeys`),
  `packages/py/citry/tests/test_events_routes.py`
  (`test_state_token_must_match_the_component_storage`) and
  `packages/py/citry/tests/test_contrib_django.py`.

## Who controls the input

A State token is the string that stands for a component's State (the data a
component keeps between calls) between event calls. The browser holds it
and sends it back with each call. (Events is Citry's extension for browser
calls to Python event handlers.) A component stores its State in one of two
ways. With signed storage, the token holds the State and an HMAC (a keyed
checksum) made with the app's secret. With server storage
(`State._storage = "server"`), the token is only a random key, and the
State sits in Citry's cache.

The problem: `Citry(secret=...)` accepted a secret that is empty or only
whitespace (a weak key), alone or as an entry of a list. Citry
accepts a token signed with any entry of the list, so it accepted one
signed with a weak key. A request could then carry a forged token and run
an event handler on State of the sender's choosing. Server-storage
components also accepted a signed token in place of their cache entry,
because Citry chose how to check the token from its prefix (its first
characters), not from the component.

Two parties supply input here:

- **The app's Python code** supplies the secret, for example from an
  environment variable that is unset and so reads as an empty string. Only
  an app with such a secret was affected.
- **Anyone who can send a request to an Events URL** supplies the token. At
  risk is what the handler does with the State it is given: the browser
  never runs or shows the token, so this is a server-side trust problem, not
  a page-content problem.

## How it was checked

The reviewer wrote probe tests and ran them against the fixed code, using
the test client that the Events route tests use. The probes covered:

- **Settings.** Sixteen cases of a secret that should be refused: an empty
  string, a space, a tab, an ideographic space, empty `bytes`, a list or
  tuple with an empty, whitespace-only, `bytes` or `None` entry, a `str`
  subclass that overrides `strip()`, a list-like object, a `dict`, and a
  generator. Each raised `ValueError` or `TypeError`. A copy of the settings
  made with `dataclasses.replace` is checked again.
- **Five request routes**, each sent a token signed with an empty,
  whitespace-only or tab key: the per-event JSON call, a GET query, a form
  post, a flat JSON body (one object of fields) and the batch envelope
  (several calls in one request). This ran for both storage
  modes. To test the token check alone, the probes also wrote a weak key into
  the settings object after the settings check, and swapped in a whole
  settings object that held one. In every case the handler did not run.
- **The two storage forms against each other.** A token signed with the real
  key, sent to a server-storage component; and a server-storage token, sent
  to a signed component. Neither ran the handler.
- **Real tokens.** Tokens minted the normal way, in both storage modes, were
  accepted on all five routes.
- **Direct calls** of `verify_state_token` with odd secret lists (an empty
  entry, `bytes`, `None`, an empty list, no list) and with storage values
  that are not `"signed"` or `"server"`. Each was refused. `mint_state_token`
  (which makes a token) refused unusable entries.
- **Before the fix.** The reviewer also wrote probes for the code from before
  the fix, with a bare empty secret, a whitespace-only secret and a list with
  one weak entry, in the storage modes that each case applies to.

The fix itself added tests for each rule at the place that owns it:
`test_an_empty_secret_entry_is_refused` and
`test_a_secret_that_is_not_text_is_refused` in `test_citry.py` (message text
and entry position included), `TestStorageAndUnusableKeys` in
`test_events_tokens.py` (both storage mismatches, an unknown storage value,
a weak key passed directly, and `mint_state_token` with a weak entry),
`test_state_token_must_match_the_component_storage` in
`test_events_routes.py` (a 409 `stale_state` error, the Events error code
and its HTTP status, and no handler run, both ways), and a whitespace-only
fallback case in `test_contrib_django.py`.

## Ruled out

- **A weak key reaching the token check.** The settings check runs when
  `Citry(...)` is built and applies one rule, `is_usable_secret`, to every
  entry. The token check applies the same rule again and skips any entry
  that fails it, so a weak key is never tried even when the settings check
  was bypassed.
- **Choosing the check from the token.** `verify_state_token` now takes the
  component's declared storage and ignores the token's prefix when deciding
  how to read it. A server-storage component reads State only from the
  cache, which a visitor cannot write. A token of the other form gets
  `stale_state` (409), so a page rendered before the app changed `_storage`
  offers a reload. An unknown storage value gets `invalid_state` (403).
- **The render cache replay.** The code that replays a cached render
  (`ext/events/cache.py`) also passes the component's storage to
  `verify_state_token`, so it follows the same rule.
- **Secret shapes that hide a weak key.** Only a `str`, a list or a tuple is
  read, and each entry must be a plain `str`. `bytes`, `None`, numbers,
  generators, mappings and `str` subclasses are refused, not iterated.
- **Django.** `citry.contrib.django.secret()` skips empty and
  whitespace-only entries of `SECRET_KEY_FALLBACKS` with the same rule, and
  `test_secret_skips_empty_fallbacks_and_reaches_the_citry_settings` covers
  it. A whitespace-only `SECRET_KEY` is returned as is, and `Citry(...)`
  then refuses it.

## Fixed during the review

The review changed the fix before it merged:

- **A token of the other storage form.** The review changed the answer
  to `stale_state` (409), so a page rendered before the app changed
  `_storage` offers a reload.
  `test_state_token_must_match_the_component_storage` checks the status and
  that no handler runs.
- **Secret error messages.** The messages for a bare string secret and for
  a list entry were reworded to say what to change. `test_citry.py`
  checks the start of the text, which names the entry position.
- **The changelog entry.** It was widened to say that a bare empty or
  whitespace-only secret is refused too, not only a list entry.

## Not tested

- **A real browser.** The review is server-side: it checks what the server
  does with a token string. Nothing in the change writes a value into the
  page.
- **A short or guessable secret that is not empty.** The rule requires a
  plain `str` with at least one character that is not whitespace. It sets
  no minimum length, and the probes accepted a one-character secret in a
  tuple. `None` and an empty list are accepted by design: they mean no
  secret, and a component with signed State then fails at its first token.
  The docs and the error message tell app authors to use a long random
  string.
- **Each released version.** The probes ran against the code from before the
  fix and against the fix, not against every release from 0.3.0 to 0.7.0.
- **Free-threaded Python.** No run used it.
- **A second review of the changes under "Fixed during the review".** No
  second agent read them.
- **Other cache backends.** Server storage was tested with the cache of the
  test setup, not with a shared backend such as Redis or memcached.
- **A whitespace-only Django `SECRET_KEY`.** No test sets one; the refusal
  comes from the general rule in `CitrySettings`.

## Follow-ups

None.
