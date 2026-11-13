# Design: serve the browser runtimes from content-hashed URLs

**Status (2026-11-13): proposed, waiting for maintainer review. Implement after
0.8.0 is released.** Tracking issue:
[#578](https://github.com/citry-dev/citry/issues/578).

## 1. What happens now and why it matters

Citry sends three JavaScript runtimes to the browser:

| URL | Bytes | Who links it |
|---|---|---|
| `{prefix}/citry.js` | `_vue/runtime.js` | Most pages and every fragment |
| `{prefix}/ext/events/runtime.js` | `_vue/runtime.js` (the same file) | A Vue page where the Dependencies extension did not already emit the runtime |
| `{prefix}/ext/i18n/runtime.js` | `ext/i18n/client/vue-plugin.source.js` | Pages that use browser translations |

`{prefix}` is the mount prefix the app chose, `/citry` by default.

None of these URLs changes when Citry is upgraded, and all three answer
`Cache-Control: no-store`. So the browser downloads the shared runtime (about
400 KB) and the i18n runtime again on every page load.

`no-store` is there for a reason. The page pairs itself with its runtime
only through the URL. If the browser reused a stored copy, a page rendered by
the new version could start with the old runtime. With
`security_script_integrity` on, that page fails its integrity check and never
starts. [#574](https://github.com/citry-dev/citry/pull/574) tried `no-cache`
with an `ETag`, and review found that the back and forward buttons may reuse a
stored script without asking the server, which brings the mismatch back.

This design puts a hash of the runtime's bytes into its URL. A page then names
the exact runtime it was rendered for, so the browser can keep that file for a
year, and a new deploy links a new URL that no stored copy can answer.

The Events plan decided the opposite: "the runtime keeps the stable
unversioned route `ext/events/runtime.js` and answers `Cache-Control:
no-store`. There is no runtime query-version compatibility protocol"
([`events_plan.md:1043-1045`](events_plan.md)). This design reverses that
amendment, and section 8 adds a dated amendment that records the change.

## 2. Prior art

The survey covered the three runtime routes, their emission paths, the hashed
definition and stylesheet routes, the asset store, the code that adds
`integrity` and nonces to Citry's script tags (`_serialization_security.py`),
the fragment loader, the browser loader, static export, the preview host, the
docs playground, the citry_ui quality harness (it renders UI scenarios without
a server and inlines the runtime), the Events spec, the design docs, the user
docs and the tests. Paths are relative to
`packages/py/citry/citry/` unless they start with another top-level folder.

**The runtime routes.**

- `ext/dependencies/routes.py:64` sets `RUNTIME_PATH = "citry.js"`. The route
  is registered at `:191`. The handler at `:156-167` adds `no-store`, and its
  comment gives the back/forward reason.
- `ext/dependencies/emission.py:727-735`: `_runtime_js()` reads
  `_vue/runtime.js` once per process.
- `ext/events/routes.py:90-103` sets `RUNTIME_PATH = "ext/events/runtime.js"`
  and `EVENTS_RUNTIME_SRC`. The route is at `:250`. `_runtime_resource`
  (`:274-281`) reads the file on every request and sets `no-store`.
- `ext/i18n/emission.py:33-58` sets `RUNTIME_PATH = "ext/i18n/runtime.js"`.
  `client_runtime_resource` reads the file once and sets `no-store`. The route
  is at `ext/i18n/routes.py:53`.
- `_owned_resource.py:125-141`: `.response()` adds
  `Access-Control-Allow-Origin: *`. `IMMUTABLE_CACHE_CONTROL` (`:67`) and
  `immutable_response()` already exist. `immutable_response()` appends its
  header after `self.headers`, so a resource that already carries `no-store`
  would send two `Cache-Control` headers.
- `util/routing.py:260-273`: every adapter adds
  `X-Content-Type-Options: nosniff`. `util/routing.py:379-398`: a `{name}`
  parameter matches any run of characters other than `/`, and a parameter
  listed in `dotless_params` also stops at `.`. So `citry.{digest}.js` is a
  valid route and does not match `citry.js`.

**The hashed routes that already work this way.**

- `ext/events/routes.py:94-95,251-262`: `ext/events/definitions/{digest}.js`
  and `ext/events/assets/{digest}.css`. The digest is the full SHA-256 of the
  bytes as 64 lowercase hex characters (`_vue/events.py:859-867`). A digest of
  the wrong shape gets `404` (`ext/events/routes.py:190-194,206-210`). That
  `404` sends no `Cache-Control`, unlike the Dependencies `404`s, which send
  `no-store` (`ext/dependencies/routes.py:61-62,127-130`).
- `_vue/events.py:55-63,173-216`: each process keeps the assets it compiled
  in memory, up to `vue_asset_max_bytes` without a shared cache, or up to 128
  entries with one. With `settings.cache` set, it also writes them to the
  shared cache under `citry:vue-{kind}:{digest}` with no expiry
  (`:168-170,383-410`). The write goes through `_store_if_missing`
  (`citry/cache.py`), which writes the key again when the backend has dropped
  it, checking at most once every `_STORED_KEY_RECHECK_SECONDS`. A read
  checks memory first, then the shared cache, and checks the SHA-256 again
  before serving (`:413-437`). This is what lets a worker answer for an asset another worker compiled.

**Where the runtime URL reaches the page.**

- Document pages: `ext/dependencies/emission.py:296-311,769-776` adds
  `_runtime_script()`, a `<script src>` for `citry.js` whose bytes Citry
  serves itself. With no mount prefix, the runtime is inlined instead.
- `_vue/serialization.py:1294-1297` builds a tag for `ext/events/runtime.js`.
  When the Vue serialization finishes (`finalize`, `:655-686`), it drops
  that tag when the Dependencies extension already emitted the runtime. The
  same block checks that a serialization hook did not remove the runtime tag, by looking for the exact `src="..."` text.
- Preload hint: `_vue/serialization.py:710-761` writes
  `<link rel="preload" as="script">` for the runtime with the same integrity,
  `crossorigin` and nonce.
- Start script: `_vue/serialization.py:1384-1393` writes the module script
  `__citryRuntime.startDocument(<app id>)`. A module script runs after the
  page is parsed and after the classic runtime script above it. Its comment
  says the text carries only the app id, so its CSP hash is short to compute.
  `_vue/client.js:5538` defines `global.__citryRuntime`, so it is an own
  property of `window`.
- Fragment loader: `ext/dependencies/emission.py:779-821` writes inline
  JavaScript that adds a `<script>` for `citry.js` when `window.Citry.fragments`
  is missing. It sets `integrity`, `crossOrigin` and `nonce`. It is omitted
  under strict CSP (`:944-945`). Events `Render` results carry this loader
  inside the result's HTML (`ext/events/results.py:108-115,400-403`).
- Integrity: `_serialization_security.py:361-385` computes a SHA-384 of the
  owned body on every render and sets `integrity` and
  `crossorigin="anonymous"`. `record_owned_dynamic` (`:256-275`) records the
  loader's URL.
- Render cache: `ext/cache/artifact.py:602,877` stores the parts of a render
  before serialization, and the runtime tag is added after replay. So no cached
  render holds the runtime URL.

**Browser code.**

- No TypeScript or `client.js` source names a runtime URL. `loadDefinition`
  (`_vue/client.js:2733-2758`) rejects when a definition fails to load and
  never retries or reloads. `promptReload` (`_vue/client.js:183-188`) shows a
  once-per-page `confirm()` and reloads, but only on a `stale_state` call
  failure.
- `HELPER_CONTRACT` (`_vue/compiler.py:526-540`, `_vue/client.js:117-122`)
  changes only when the definition format changes, not on every build.
- The i18n build ID (`packages/js/citry-client/build-support.mjs:110-121,187-191`,
  `src/citry-i18n-vue.ts:114-119,921`) stops a second, different i18n plugin
  build from registering on the same page. Python never reads it, and no URL
  contains it. The plugin registers through
  `__citryRuntime.registerBrowserPlugin` (`src/citry-i18n-vue.ts:190`), and
  `startPrepared` throws "missing or incompatible Citry browser plugin" when a
  plugin the page expects is absent (`_vue/client.js:3305-3310`).

**Hosts and tools that name the stable URLs.**

- Static export: `docs_site/_internal/static_deps.py:66-86` writes `citry.js`
  and `ext/events/runtime.js`, and does not export the i18n runtime.
- Preview host: `ext/preview/host.py:266` checks that the server is up by
  fetching `/citry.js`.
- Docs playground: `docs_site/static/playground/executor.py:55-65` allows only
  listed route names, and `preview.html:38,266` matches hashed paths with a
  regular expression. `runtime.json` pins the published `citry` wheel, so the
  playground must keep working with a wheel that predates this change.
- citry_ui quality harness: `packages/py/citry_ui/citry_ui/quality/routes.py:270-279,357-374`
  maps each runtime URL to its source.
- The starters and demos under `examples/` fetch `/citry/citry.js` and
  `/citry/ext/events/runtime.js` and check for `200`.

## 3. The design

### 3.1 URL shape

Each runtime gets a second route whose path contains the SHA-256 of the bytes
it serves, as 64 lowercase hex characters:

```text
GET <prefix>/citry.<sha256>.js
GET <prefix>/ext/events/runtime.<sha256>.js
GET <prefix>/ext/i18n/runtime.<sha256>.js
```

The digest has the same form as the definition and stylesheet digests, so one
check function validates all of them. The `{digest}` parameter is listed in
`dotless_params`, so the route can never match `citry.js` or a path with an
extra dot.

`citry.<sha256>.js` and `ext/events/runtime.<sha256>.js` serve the same bytes
and carry the same digest. Each emission path keeps linking the route it links
today, now in its hashed form. Section 6 asks whether to merge the two.

### 3.2 What the hashed route answers

The server computes each runtime's bytes, SHA-256 and SHA-384 once per
process and keeps them. The handler then:

1. Checks the digest's shape. A digest that is not 64 lowercase hex
   characters gets `404` with an empty body and `Cache-Control: no-store`.
2. Serves the current bytes when the digest matches them.
3. Otherwise, when `settings.cache` is set, reads `citry:runtime:<digest>`
   (for i18n, `citry:i18n-runtime:<digest>`) from the shared cache, checks its
   SHA-256 against the digest, and serves it. A mismatch deletes the entry.
4. Otherwise answers `404` with `no-store`.

A hit answers `200` with `Content-Type: text/javascript; charset=utf-8`,
`Cache-Control: public, max-age=31536000, immutable`,
`Access-Control-Allow-Origin: *` (the browser needs it to check integrity) and
`nosniff`. The resource is built without `no-store` in its own headers, so
`immutable_response()` sends exactly one `Cache-Control`.

When a process emits a hashed runtime URL and `settings.cache` is set, it
writes the runtime bytes to the shared cache under that key through
`_store_if_missing`, the function that stores Events definitions. So the
write happens before the response is sent, a backend that dropped the entry
gets it again on the first render after `_STORED_KEY_RECHECK_SECONDS` (60
seconds, `citry/cache.py:295`), and a cache backend error fails the render as
it does for definitions. The entry has no expiry, like definition entries, so
the backend drops it only when it needs the space. That costs one entry of
about 400 KB for each deployed version of the shared runtime, plus a smaller
one for i18n.

### 3.3 Where the page gets the hash

Every place that writes a runtime URL will call one helper per runtime.
Dependencies has one today (`runtime_url(citry)`); Events builds its URL inline
(`_vue/serialization.py:1295`, `ext/events/routes.py:277`) and gets a helper.
Those helpers return the hashed URL. So these all move together:

- the `<script src>` from `_runtime_script()`, `_vue/serialization.py`, and the
  i18n emission paths;
- the `<link rel="preload">` hint, which reads the same `Script` URL;
- the URL the fragment loader writes into its inline JavaScript, including the
  copy inside an Events `Render` result;
- the URL `record_owned_dynamic` records for the opt-in output checks;
- the check in `_vue/serialization.py:655-686` that a serialization hook kept
  the runtime tag, which compares against the same helper's value.

Integrity reads the stored SHA-384 instead of hashing the body on every
render. The value stays SHA-384, so the `integrity` attribute does not change.

Without a mount prefix, document pages still inline the runtime. The fragment
loader and the i18n resource keep the relative paths they use today, since no
route serves them. The hashed URL applies only when a prefix is mounted.

### 3.4 The stable URLs stay as aliases

`citry.js`, `ext/events/runtime.js` and `ext/i18n/runtime.js` keep serving the
current bytes with `no-store`. Pages that Citry renders link only the hashed
URLs. The stable URLs stay because:

- every page rendered by 0.8.0 or earlier links them, and those pages must keep
  working across the upgrade;
- the preview host's startup check, the starters, the demos and third-party
  tools fetch them;
- a host that loads the runtime by hand needs one URL that always works.

Section 6 asks whether to keep them past 1.0.

### 3.5 When a hashed runtime fails to load

A page can ask for a hash that no server holds (section 4). The page needs to
recover on its own, and it must never reload in a loop. The start script is
the right place for this, because it already runs on every document page,
carries the CSP nonce, and runs after the runtime script has loaded or failed.

The rule: **reload at most once per load, only when the browser can tell that
this load is not already a reload, and only when the server says the runtime
is gone.**

1. If `__citryRuntime` is an own property of `window`, the start script calls
   `startDocument` as today. Reading it as an own property matters, because an
   element with `id="__citryRuntime"` would otherwise answer the plain name.
2. Otherwise, if another start script on the page has already handled the
   failure (a flag on `window`), it stops. This keeps a page with several apps
   from logging or reloading more than once.
3. Otherwise it asks whether this load is already a reload. It reads the
   navigation entry (`performance.getEntriesByType("navigation")[0].type`),
   and falls back to the older `performance.navigation.type === 1` that
   Safari before 15 offers. If this load is a reload, or neither source
   exists, it writes a `console.error` and stops. A reload Citry started
   counts, and so does one the user started. This check needs no storage, so
   it holds when session storage is blocked or the page runs in a frame with
   no origin, such as the docs playground preview.
4. Otherwise, if session storage is readable and already holds this runtime
   URL, it writes a `console.error` and stops. This keeps a site whose whole
   pages are cached from reloading every page the user opens in that tab.
   When storage throws, step 3 still limits the page to one reload per load.
5. Otherwise it asks the server for the runtime with
   `fetch(url, {method: "HEAD", cache: "no-store"})`. The router already
   answers `HEAD` on `GET` routes (`util/routing.py:194`), so the probe does
   not download the runtime again. Only a `404` stores the URL in session
   storage (when it can) and calls `location.reload()`. A network error, a
   blocked request, a `200` or any other status writes a `console.error` and
   keeps the server HTML on screen. A reload would not help in any of these
   four cases: a page opened from history while offline, a runtime blocked by
   an extension or a proxy, a browser too old to run the runtime (the file
   loads but defines nothing), and a probe that the page's CSP `connect-src`
   blocks.

A sketch, with lines kept short. Storage access is wrapped in `try` in the
real script, and left out here:

```js
var w = window, own = Object.prototype.hasOwnProperty;
var url = "<runtime url>", key = "citry:runtime-reload";
var fail = function () {
  console.error("Citry could not load its runtime: " + url);
};
var reloaded = function () {
  var p = w.performance, nav = p.getEntriesByType
    ? p.getEntriesByType("navigation")[0] : null;
  if (nav) return nav.type === "reload";
  if (p.navigation) return p.navigation.type === 1;
  return true;  // cannot tell, so never reload
};
if (own.call(w, "__citryRuntime")) {
  w.__citryRuntime.startDocument("<app id>");
} else if (!own.call(w, "__citryRuntimeMissing")) {
  w.__citryRuntimeMissing = true;
  if (reloaded() || sessionStorage.getItem(key) === url) fail();
  else fetch(url, {method: "HEAD", cache: "no-store"})
    .then(function (r) {
      if (r.status !== 404) return fail();
      sessionStorage.setItem(key, url);
      location.reload();
    }, fail);
}
```

- The reload fetches fresh HTML, which links the hash the server holds now.
- After a failure, the server HTML stays on screen. Links and plain forms keep
  working. Events and Vue features do not start.
- The two values in the script are the app id it carries today and the
  runtime URL the server built. Both are written with `script_json`, and the
  URL is joined to the message with `+`, never pasted into a string.
- The start script's text now includes the runtime URL, so its CSP hash
  changes with each release. Serialization already reports the hash per
  render, so a host that sends hashes picks up the new one.

**Browser plugins.** The start script checks only `__citryRuntime`, not any
one extension's script. A plugin script, such as the i18n runtime, can also
fail to load while the runtime loads. Today the runtime then throws "missing
or incompatible Citry browser plugin" (`_vue/client.js:3307-3310`), from code
that both `startDocument` and the fragment code (`citry-fragments.ts:95`)
reach. The runtime handles it with the same rule, with three limits:

1. It applies the rule only when `startDocument` starts a full page. A
   fragment never reloads the page; it keeps today's error.
2. It applies the rule only when the plugin is not registered at all. A
   plugin that is registered but does not match (another schema version, or
   the i18n "different build already registered" error) would fail on every
   load, so it keeps today's error and never reloads.
3. It probes the plugin's script URL as step 5 does. So the page's entry for
   each extension in `manifest.extensions` (read at `_vue/client.js:3240`)
   also carries the URL of its plugin script. This is a change to the JSON the
   server writes for the runtime, made in place under version 1.

The rule lives once in the runtime for plugins and once in the start script
for the runtime itself, because the start script must work when the runtime
is missing. One browser test matrix covers both. This works the same for any
extension that registers a browser plugin.

**The fragment loader** does not reload the page. It adds an `error` listener
(a property set from JavaScript, so CSP allows it) that writes the same
`console.error`. A fragment is a small part of a page, and reloading the whole
page because of one fragment would lose the user's work. The fragment was
rendered a moment earlier by a current worker, so this miss happens only during
a rolling deploy.

## 4. Error modes

**An old page asks for a hash that is gone.** A page rendered before a deploy,
or reopened from history, asks for `runtime.<old>.js`.

1. The browser most likely has the file already, because it was stored as
   `immutable` for a year. The page starts without any request. This is the
   main gain over `no-store`: on a full page load, including the back and
   forward buttons, a page always runs with its own runtime.
2. If the browser does not have it and `settings.cache` is set, any worker
   serves it from the shared cache.
3. Otherwise the server answers `404` with `no-store`, and the page reloads
   once (section 3.5) and gets the new HTML.

**The page answered a form POST.** Many apps render a page directly in reply
to a POST. If that page reloads, the browser asks the user whether to send the
form again, and a user who agrees sends it twice. Browsers are expected to ask
first, so nothing is sent silently; a browser test in section 7 checks this
before the design relies on it. Section 6 asks whether to avoid the reload on
such pages.

**A host caches whole pages.** A CDN or a page cache in the app keeps HTML
that links an old hash after the deploy. Steps 1 and 2 above still apply. In
step 3 the reload returns the same cached HTML, the navigation-type check stops
a second reload, and the page stays as server HTML. The URL stored in session
storage stops the reload on the next pages the user opens in that tab. When
storage is blocked, each page the user opens reloads once, so every page load
costs two. The user docs tell app authors to purge cached pages on deploy or to
set `settings.cache`.

**Prerendering.** A page prerendered by speculation rules that calls
`location.reload()` is most likely thrown away by the browser, and the user
then gets a normal load. This is unproven; the browser tests in section 7
check it. A page restored from the back/forward cache does not run its scripts
again, so it never reaches the rule.

**Rolling deploys.** For a while, workers run different versions.

| Page rendered by | Runtime request reaches | Result |
|---|---|---|
| 0.8.0 or earlier | Any worker | Stable URL, `no-store`, same as today |
| Version N | A worker on N | Served from memory |
| Version N | A worker on M (both have this feature), shared cache set | Served from the shared cache, because N wrote it when it rendered the page |
| Version N | A worker on M, no shared cache | `404` with `no-store`, at most one reload |
| Version N | A worker on 0.8.0 or earlier | No such route, the adapter's `404`, at most one reload |

After the one reload, the new HTML may come from either version. If it comes
from a worker on 0.8.0 or earlier, it links the stable URL and works. If its
runtime request again reaches a worker that lacks the hash, the page stays as
server HTML until a later visit, because the second load is a reload. The user
docs recommend sticky sessions or a shared cache for rolling deploys. Citry
does not retry the request on another worker, because the browser cannot
choose one.

The adapter's `404` for an unmatched path under the prefix sends no
`Cache-Control` today (`contrib/asgi.py:175`, `contrib/wsgi.py:150`). This
change adds `no-store` to it. That fixes later deploys, but a worker on 0.8.0
or earlier still sends its old answer during the first deploy of this feature.

**A malformed or unknown hash.** Wrong length, upper case, or other characters:
`404`, empty body, `no-store`, the same answer as an unknown well-formed hash.
The handler checks the shape before it builds a cache key.

**A CDN in front of the app keeps `404` answers.** Every `404` from these routes
sends `no-store`, which mainstream CDNs honor by default. While touching this,
the Events definition and stylesheet `404`s gain the same `no-store` they lack
today, since CLAUDE.md Mechanism 3 asks for sibling bugs to be fixed in the
same pass. A CDN configured to cache `404`s for a fixed time ignores the
header. The user docs name that setting. The navigation-type check keeps such a
page from looping.

**The runtime file changes while the process runs.** Like `citry.js` today,
the Events and i18n routes read their file once per process, so an edited
file takes effect on restart. Editing the installed package is not a supported way to change the runtime.

**The shared cache holds wrong bytes.** The handler serves an entry only when
its SHA-256 equals the digest in the URL, and deletes it otherwise. So a broken
or tampered entry gets `404`, never wrong code under a trusted hash.

**Soft navigation.** A library that swaps the page body without a full load
(Turbo, `hx-boost`) keeps the runtime already in `window`. Section 8 lists this
under "Left out on purpose".

## 5. Alternatives considered

**`no-cache` with an `ETag`.** Tried in #574. The browser may reuse a stored
copy on back and forward navigation without asking, so a page can still meet
the wrong runtime. Rejected for the reason #574 gave.

**A query string on the stable URL** (`citry.js?v=<hash>`). The route would
either ignore the query and serve the current bytes under an old version's
URL, which an `immutable` cache would then keep, or check it, which is the
design above with a weaker URL. Some CDNs leave the query out of the cache key
by default. Rejected.

**Answer an unknown hash with the current bytes, or redirect to the stable
URL.** With integrity on, the browser rejects the bytes anyway. With integrity
off, the page runs the wrong runtime, which is the bug this design removes.
Rejected.

**Ship several past runtimes in the wheel.** The wheel would grow by about
400 KB per kept version and would still miss pages from versions it dropped.
The shared cache covers the same case for apps that need it. Rejected.

## 6. Open questions for the maintainer

1. **URL shape.** `citry.<sha256>.js` (the issue's shape, chosen here) or a
   folder such as `runtime/<sha256>.js`, like `definitions/<sha256>.js`.
2. **One URL or two for the shared runtime.** Today both `citry.<sha256>.js`
   and `ext/events/runtime.<sha256>.js` would exist for the same bytes. A page
   uses one of them, so the browser downloads the file once in the usual case.
   Merging them would make the Events serialization link the Dependencies
   route.
3. **How long the stable aliases stay.** This design keeps them while the
   package is below 1.0.0. They could stay for good, since they cost one route
   each.
4. **Reload on a page that answered a POST.** The browser asks before it sends
   the form again, so nothing happens silently, but a user can agree and send
   it twice. Options: accept this (chosen here); have the server leave out the
   reload when the host adapter knows the request was not a GET; or replace
   the reload with a `confirm()` message like `promptReload`.
5. **A public way to get the hashed URL.** Pages and tools that link
   `/citry/citry.js` by hand (`docs_site/examples/fragments/page.py:25`,
   `examples/demos/htmx/app/routes.py:83`, `guides/htmx.md:57`,
   `advanced/html-fragments.md:43`) keep working through the alias but stay on
   `no-store`. A public function such as `citry.runtime_url()` would let them
   cache the runtime too. It is a new public API, so this design leaves it out
   unless you want it.
6. **Shared-cache writes.** Writing about 400 KB per deployed version to
   `settings.cache` happens whenever a cache is set. It could be made opt-in.
7. **i18n in static export.** `static_deps.py` does not export the i18n
   runtime today. This design writes the hashed files only for the runtimes
   static export already writes. Exporting i18n is a separate change.

## 7. What would show this design is wrong

- **Repeat page loads still download the runtime.** A browser test loads two
  pages and counts requests for the hashed URL. More than one request, other
  than after a forced reload, means a header or a `crossorigin` mismatch
  between the preload hint and the script keeps the browser from reusing its
  copy.
- **The page reloads more than once.** A browser test serves a page whose
  runtime answers `404` and expects exactly one reload, then a
  `console.error`, then nothing more. It runs again with session storage
  blocked, inside a sandboxed frame with no origin, with a server that links a
  different missing hash on every load, and with the navigation entry stubbed
  out (no reload at all when neither navigation source exists).
- **A missing plugin reloads from the wrong place.** A browser test blocks
  the i18n runtime and expects one reload on a full page, none when a fragment
  needs the plugin, and none when the registered plugin does not match.
- **The POST and prerender claims in section 4 fail.** A browser test renders
  a page in reply to a form POST with a missing runtime and checks that the
  browser asks before sending the form again. Another prerenders a page with a
  missing runtime and checks that the user's later visit loads normally.
- **The page reloads when it should not.** A browser test makes the runtime
  request fail with a network error and expects no reload and the server HTML
  still on screen. The docs playground preview, on a current wheel, never
  reaches the reload branch.
- **A page meets the wrong runtime.** A browser test renders a page, swaps the
  runtime bytes (and so the hash), uses the back button, and checks that the
  page runs with the runtime its HTML names, with integrity on and off.
- **A hashed URL slips through a path.** A test renders a document, a
  fragment, an Events `Render` result and a cached render, and checks that each
  one names the hashed URL and never the stable one.

## 8. Everything that changes

The protocol string stays `citry-events/1`, and no contract version constant
moves (the package is below 1.0.0).

**Library code** (`packages/py/citry/citry/`):

- `ext/dependencies/routes.py`, `ext/events/routes.py`, `ext/i18n/routes.py`,
  `ext/i18n/emission.py`: the hashed routes, the per-process bytes and
  digests, the shared-cache read and write, `no-store` on every `404`
  (including the Events definition and stylesheet `404`s). The digest-shape
  check at `ext/events/routes.py:190,206` becomes one shared function.
- `contrib/asgi.py`, `contrib/wsgi.py`: `no-store` on the unmatched-path
  `404`.
- `ext/dependencies/emission.py`: `_runtime_script()`, the fragment loader URL
  and its `error` listener.
- `_vue/serialization.py`: the runtime tag, the preload hint, the hook check,
  the new start script, and the comment at `:1384-1389` that says the start
  script carries only the app id.
- `_vue/client.js`: the reload rule when a browser plugin is missing, on the
  `startDocument` path only. Then rebuild the committed `_vue/runtime.js`
  (`packages/js/citry-client/build.mjs`), and add JavaScript unit tests for
  the rule under `packages/js/citry-client/test/`.
- `_vue/serialization.py` and the extension plugin objects: each entry in
  `manifest.extensions` carries its plugin script URL.
- `_serialization_security.py`: use the stored SHA-384.
- `ext/i18n/extension.py`: `browser_plugin()` links the hashed URL.

**Hosts and tools:**

- `docs_site/_internal/static_deps.py`: also write the hashed files.
- `docs_site/_internal/assemble.py` and `docs/design/docs_site.md:466`:
  snapshot pages under `/v/<version>/` link root paths such as
  `/citry/citry.js` and `/citry/cache/...`. A snapshot that links a hashed
  runtime needs that file at the root, so `assemble.py` copies each
  snapshot's hashed runtime files into the site's root `/citry/` (hashed names
  never clash). Snapshots taken so far link `/citry/citry.js`, which the
  alias keeps working. The implementation checks a built site, because the
  existing snapshot links to `/citry/cache/...` and Events assets may already
  miss for the same reason; if they do, that is a separate fix.
- `docs_site/static/playground/executor.py` and `preview.html`: allow the
  hashed route names and paths, and keep the stable ones for older pinned
  wheels.
- `packages/py/citry_ui/citry_ui/quality/routes.py`: map the hashed URLs.
- `ext/preview/host.py`: no change (the startup check uses the alias).
- `packages/py/citry_ui/storybook/src/dev-proxy.js`: no change (it forwards
  everything under `/citry/`).

**Specs and design docs:**

- `packages/protocol/events/v1/spec.md:1128`: list
  `GET <prefix>/ext/events/runtime.<sha256>.js` with its caching, and the
  stable alias.
- `docs/design/events_plan.md`: a new dated amendment after `:1043-1045`
  that states the hashed URL, and the related sentences at `:1090-1092`,
  `:1239-1240` and `:2253-2255`.
- `docs/design/dependencies.md:626-670` (the start script), `:721`,
  `:738-743` and `:852-855`.
- `docs/design/events.md:1480,1937-1941`.
- `docs/design/security_csp.md:701-721`: the start script now carries the
  runtime URL and the reload rule, and its CSP hash changes with each release.
- `docs/design/public_api_0_6_0_audit.md` is a record of 0.6.0 and stays as
  it is.

**User docs and changelog:**

- `docs_site/content/advanced/web-frameworks.md:106,474,508-513`: the new
  caching, purging cached pages on deploy, sticky sessions or a shared cache,
  CDN `404` caching.
- `docs_site/content/security.md:1007`: the CORS list names all runtime routes.
- Pages that show `/citry/citry.js` as the loaded URL
  (`guides/troubleshooting.md:116`, `guides/htmx.md:57`,
  `examples/fragments.md:18`, `advanced/html-fragments.md:43,68`,
  `getting-started/fastapi.md:180`): say that pages link a hashed URL and the
  stable URL stays for manual use.
- `CHANGELOG.md`: one entry, along the lines of "The browser now keeps the
  Citry runtimes between page loads. Pages link them by a URL that changes
  with each release."

**Tests that expect the hashed URL.** Each takes the digest from the runtime
bytes, never from a copied literal:

- `packages/py/citry/tests/test_asset_cors.py:145-147,436-444,557-571`: the
  hashed routes are `immutable` with CORS, the aliases are `no-store`, every
  `404` is `no-store`.
- `test_events_routes.py:1416-1419`, `test_i18n_client.py:225-230,292`,
  `test_deps_fragments.py`, `test_vue_runtime_coverage_secondary.py:296-414`,
  `test_serialize_security.py:339-356,1112`, `test_vue_events.py:821,1168`,
  `test_check_app_rules.py:1855`.
- `e2e/test_fragment_e2e.py`, `e2e/test_fragment_nonce_e2e.py`,
  `e2e/test_vue_transparent_root_e2e.py`: pages now load the hashed URL.
- `docs_site/tests/test_static_deps.py`, `test_playground_executor.py`,
  `test_build.py:882-883`, `docs_site/tests/e2e/test_preview_bridge_e2e.py`.
- `packages/py/citry_ui/citry_ui/quality/tests/test_routes.py`.
- New: the shape check, the shared-cache read across two `Citry` instances,
  the mismatch delete, the adapter `404` header, and the browser tests in
  section 7.

**Tests that use the stable URL and keep passing through the alias:**
`test_events_host_parity.py:521-522,641-642`, `test_events_django.py`,
`test_deps_urls.py`, `test_path_checks.py`, `test_sub_path_urls.py`,
`test_contrib_fastapi.py`, `test_contrib_hosts.py`,
`test_events_body_limits.py`, `test_preview_host.py`,
`citry_ui/quality/tests/test_hosts.py`, `test_storybook_spike.py`,
`storybook/src/dev-proxy.test.js`, and the starter and demo tests under
`examples/`. Check each during implementation. A test that asserts on
rendered HTML, not on a direct request, moves to the hashed URL.

**Protocol examples.**
`packages/protocol/events/v1/tests/{happy_render,batch_two,baseline_swap}.result.json:13`
contain a loader with `/citry/citry.js`. They are examples checked against the
schema, not compared with live output, so they stay as they are.

**Left out on purpose:**

- A fragment rendered by a newer version and inserted into a page that
  already runs an older runtime. The fragment loader does not run in that
  case, and the older runtime reads the newer fragment. That is true today and
  this design does not change it.
- Soft navigation (Turbo, `hx-boost`), which keeps the runtime already in
  `window` across body swaps. The guarantee in section 4 covers full page
  loads.

## 9. Security pass routes

Every value this change adds comes from the server: the digest is computed from
package bytes, and no request or template data chooses a runtime URL. The one
new input from a request is the digest in the path. The places from the
CLAUDE.md list that this change touches, and the routes to check in the
review:

- **Responses Citry serves.** The hashed routes: `Content-Type`, `nosniff`,
  CORS, `immutable` only on bytes checked against their digest. Every `404`:
  empty body, `no-store`, the path never echoed.
- **Addresses the browser code takes from the server.** The runtime URL in
  `<script src>`, in the preload hint, in the fragment loader's JavaScript
  string (written with `json.dumps` and `<` escaped), inside an Events
  `Render` result, in the start script (written with `script_json`), and in
  each plugin's entry in `manifest.extensions`. The URL is the mount prefix,
  which the app author sets, plus a hex digest.
- **The probe request.** The start script and the runtime send a same-origin
  `HEAD` request to a URL the server chose, and read only its status.
- **The CSP nonce.** The runtime tag, the preload hint, the fragment loader's
  script, and the new start script all receive it, including fragments added
  after load. Under strict CSP the fragment loader is still omitted. The
  start script's CSP hash changes with each release and is reported per
  render.
- **Element `id` and `name`.** The start script reads `__citryRuntime` and its
  own flag as own properties of `window`. `location`, `performance`, `fetch`,
  `sessionStorage` and `console` are own properties of `window`, so markup
  cannot replace them.
- **Navigation.** The start script and the runtime only call
  `location.reload()`. Nothing chooses where the page goes.
- **The opt-in output checks.** `security_script_integrity`,
  `security_csp` and `security_javascript` must treat the hashed URL as the
  Citry-owned runtime, and the hook check must find it.
- **Cached renders.** The runtime tag is added after replay, so a cached render
  always gets the current URL. A page cached whole by the host links an old
  URL and follows section 4.
- **The shared cache.** An entry is served only when its SHA-256 matches the
  digest in the URL.

The implementation pull request changes library code, so its review also runs
the advisory survey check (CLAUDE.md Mechanism 8) and, after merge, writes a
record under `docs/security/reviews/` (Mechanism 7, step 7).
