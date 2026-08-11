# Cache and i18n contract

**Status:** The bounded Phase 0 exploration passed. The adapter is research
code. Citry's shipped Cache extension does not yet implement this i18n-aware
lookup path.

## What this settled

Citry can make localized output caching safe without putting the locale into
every cache key.

An i18n-dependent component receives a sealed `I18nCacheToken` from the
installed i18n extension before Cache reads its backend. The token records
every ambient value that can change settled output: locale, fallback chain,
direction, time zone, time-zone-data revision, catalog revision, and named-
format revision. Cache turns the token into one versioned canonical value.
Application inputs cannot mint it.

The proof used these rules:

- a dependent component or fragment may read the backend only after its final
  variation contains the exact token for the active i18n context;
- an omitted, stale, forged, cross-engine, or unbound token prevents the
  backend read;
- a failed proof also prevents publishing a cache entry;
- a declaration that is explicitly locale-independent may share one entry;
- parsed templates and compiled message structure stay locale-neutral; and
- dormant i18n declares `render_cache_mode = "stateless"` and replay version 1,
  so merely installing the built-in does not disable safe cache entries.

This is an input to the existing cache key, not a separate cache. Two distinct
`LocaleContext` objects with the same semantic values reused one entry. Arabic
did not replay English. Changing any one of the seven output-affecting fields
produced a distinct canonical token value.

The same pre-lookup rule worked for a component cache and `<c-cache>` fragment.
The fragment form injected the token internally. Authors did not put it in a
template expression.

## Failure checks

The harness proved that all of these fail before a backend read:

- a dependent declaration whose `vary()` result omits the supplied token;
- a dependent declaration rendered without an active locale context;
- a token minted for an older context;
- a token minted by another Citry engine; and
- an object made outside the extension, even if its visible fields copy a
  legitimate issuer and context.

The missing-token cases rendered normally but did not cache. Production
`citry check` should also report the unsafe declaration before deployment.

## Existing replay behavior

The current Cache replay tests already prove that settled component output,
client dependencies, ownership records, transparent descendants, and dynamic
`js_data()` records are captured and repaired on replay. The focused
transparent-dependency and variable-script repair tests still pass with this
design. That supports `stateless` version 1: compiled catalogs remain outside
the render artifact, while the normal Dependencies and ownership artifacts
carry browser-facing effects.

## Production work

The research adapter temporarily replaces private Cache lookup methods. The
production change should put the same steps in the public Cache extension:

1. tooling marks the component or fragment as dependent, independent, or
   unknown;
2. Cache asks i18n for the current sealed token before lookup;
3. Cache passes it to the typed `vary(..., *, i18n=token)` hook or adds it to a
   dependent fragment variation;
4. Cache validates and encodes the exact current token;
5. only then may it calculate the physical key and read the backend; and
6. replay still uses the existing dependency and ownership artifacts.

The production encoder needs a dedicated token case. Treating the token as an
ordinary dataclass or user mapping would lose its issuer and active-context
checks.

## Limits

- The dependency marker in this harness is a research class attribute. The
  proposed public names remain `Cache.i18n_dependent` and
  `Cache.i18n_independent`.
- The static checker that detects template `tr()` / `fmt()`, `<c-trans>`, and
  client message references was proved in earlier compiler slices, but is not
  wired to Cache in this harness.
- The harness proves key separation and the no-read rule with the in-memory
  backend. It does not benchmark a remote cache.
- This session did not have an independent agent reviewer. The evidence is
  executable and adversarial, but not independently reviewed.

The frozen results are in [`evidence.json`](evidence.json). Reproduction steps
are in [`prototype-environment.md`](prototype-environment.md).
