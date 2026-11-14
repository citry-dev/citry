# Hash check on served scripts and stylesheets (GHSA-x6rm)

- **Advisory:**
  [GHSA-x6rm-5x8c-wr5c](https://github.com/citry-dev/citry/security/advisories/GHSA-x6rm-5x8c-wr5c),
  published 2026-11-14, severity medium (CVSS 3.1 base score 4.7)
- **Affected and fixed versions:** `citry` before 0.8.0; fixed in 0.8.0
- **Fix:**
  [`d4e2cca39`](https://github.com/citry-dev/citry/commit/d4e2cca39a3384edadd26e7889c593ebb6e03022):
  the script and stylesheet tags Citry writes for files it serves carry
  `integrity` (a hash the browser checks) and `crossorigin="anonymous"`
  (so the browser may read the file to check it) under every value of
  `security_script_integrity` (the setting that adds hashes to scripts)
- **Reviewer:** a separate reviewing agent
- **Code:** `packages/py/citry/citry/ext/dependencies/types.py`
  (`Dependency._owned_resource`, `Dependency._owned_fetch_attrs`, and
  `_render()` in `Script` and `Style`; `Dependency` is the object for one
  script or stylesheet tag);
  `packages/py/citry/citry/_owned_resource.py`
  (`_OwnedResource.integrity` and `fetch_attrs`);
  `packages/py/citry/citry/ext/dependencies/emission.py` (`_owned_style`,
  `_cached_css_resource`, `_variables_style`, `_preloader_script`);
  `packages/py/citry/citry/_serialization_security.py`; tests in
  `packages/py/citry/tests/test_owned_file_integrity.py` and
  `packages/py/citry/tests/e2e/test_base_element_e2e.py`; the security
  guide in `docs_site/content/security.md`

## Who controls the input

Citry writes root-relative URLs, such as `/citry/citry.js`, for the script
and stylesheet files it serves. At the default setting these tags had no
`integrity` attribute (Subresource Integrity: a hash that makes the browser
use a file only when its bytes match). A `<base href>` element, which tells
the browser to resolve relative URLs against another address, could
therefore make the browser load such a file from another site and run or
apply it. The attack needs a separate HTML injection in the app. Someone
who can inject HTML that keeps a `<base>` element supplies the other
address. The fix does not remove that injection.

Three inputs matter:

- **The other site's address.** It comes from whoever injects the
  `<base>` element: request data or stored data that reaches the page
  as markup. The browser requests the file there and then runs it
  (script) or applies it (stylesheet).
- **The bytes Citry serves.** They come from Citry itself (its runtime
  files, a component's `js` and `css`, the stylesheet built from
  `css_data()` values) or from files a template author lists with
  `local_files = "serve"`. The hash is computed from these same bytes.
- **URLs an author writes.** An app's own `Script(url=...)`, a URL in a
  `Dependencies` class and a tag written in a template come from the
  template author or the app's Python code. Citry never reads those
  files, so it cannot hash them.

The browser checks a hash only on a response it may read. That is why the
fix adds `crossorigin="anonymous"` to these tags and why Citry's file
routes answer with a CORS header (the response header that lets another
page read a file).

The main risk is a page that sends a nonce-based Content Security Policy
(CSP) without `base-uri`. A CSP is a response header that limits what a page
may load, and a nonce is a one-time value that marks a tag as trusted.
Citry puts the nonce on these tags, so the policy allowed the other
site's file although it would have stopped an injected script tag.

The places in the Mechanism 7 list (the list in `CLAUDE.md` of places where
a value reaches the browser) that the fix touches are the addresses the
browser code takes from the server (fragment and definition scripts), the
CSP nonce, and the responses Citry serves (the CORS header).

## How it was checked

**Real browsers, old code against the fix.** The fix author used Chromium
156.0.8078.4 and Firefox 157.0 through Playwright (a tool that drives real
browsers from a script). One local server stood in for the app. A second
stood in for the other site: it answered every script with a harmless mark
on the page and every stylesheet with a harmless style rule, and it sent
CORS headers, so only the `integrity` check could stop the file. The
`<base>` element was added to the page markup. The same 22 page setups ran
in both browsers on the old code and on the fix:

- the runtime tag of an interactive page, at default settings, under six
  CSP forms (a nonce alone, a nonce with `'strict-dynamic'`, a nonce with
  `'self'`, a nonce with `base-uri 'self'`, `base-uri 'self'` alone and
  `base-uri 'none'` alone; the last two have no `script-src`), and with
  `security_script_integrity="citry"`;
- the i18n (translation) runtime;
- files served with `local_files = "serve"`, on static and interactive
  pages;
- interactive and static fragments, which a host page inserts after it has
  loaded;
- an author's root-relative `Script` and `Style`, and a hand-written
  runtime tag like the one in the fragments guide;
- a control with no `<base>` element.

On the old code the runtime from the other site ran under no CSP and under
the nonce policies that had no `base-uri`, so Citry's own runtime never
loaded. Each of the three policies with `base-uri` stopped it. The control
sent nothing to the other site. On the fix, every Citry-served file that a
`<base>` element moved on these routes reached the other site as a request
and the browser refused the answer, so no mark appeared and no style from
the other site applied. The reviewer then ran its own browser script in the
same two browsers, on the old code and on the fix, with a control, the
nonce policies and a stylesheet that the cache had dropped. The probes ran
before Citry named its runtime files by content hash, so they use the
earlier `/citry/citry.js` name. The browser test at commit `45e44a7a3` uses
the hashed name.

**Older releases.** The fix author rendered a page with citry 0.1.0 and
with citry 0.4.0. The runtime tag had no `integrity` in either. With 0.1.0
the file from the other site ran in both browsers. With 0.4.0 it ran under
two nonce policies, and a policy of `script-src 'self'` with no nonce
stopped it.

**Every URL against its route.** A test script of the reviewer's, with
no browser, wrote pages and fragments under many render settings: the
default and the `"citry"` integrity mode, a configured cache backend,
four ways of emitting dependencies (`deps_strategy` set to `"document"`,
`"simple"`, `"fragment"` and `"ignore"`), three script positions, head
placeholders, and per-call `security_javascript`, `security_csp` and nonce
values, each on static and on interactive components. Ten of those
renders raised their own error (per-call overrides on interactive pages,
and `security_javascript="forbid"`) and gave no URLs. For each of the 1,009
script and stylesheet tags, preload tags, loader scripts and entries in
the JSON file list that the browser runtime reads, each naming a file Citry
serves, it asked Citry's real WSGI app (the standard Python web interface)
for the URL and compared the `integrity` value with the bytes that came
back. All 1,009 had the attribute and matched. This run and the first
browser runs used the fix before the two corrections under "Fixed during
the review". Later runs covered those corrections only, so the full URL
comparison was not repeated on the merged commit.

**Edge cases, old code against the fix, no browser.** The reviewer
checked an app mounted below a sub-path such as `/shop`, copies of a
`Dependency` that holds a file (`copy`, `deepcopy` and `pickle` keep the
hash), and ways an `on_dependencies` hook (the extension hook that edits
the dependency list) can edit or rebuild a tag.

- A hook that moves a served file to another URL leaves both attributes
  off.
- A hook that builds a new object for the same URL, or rebuilds the tag
  from its JSON form with `from_json(to_json)`, also gets no hash. This is
  the documented limit.
- An `integrity` or `crossorigin` value the hook sets stays as written.
- With `"citry"` mode, a changed script URL or an empty `integrity` raises
  an error.

**What the fix may break, in browsers.** The reviewer tried a page in an
iframe sandboxed without `allow-same-origin` (so the page has no origin of
its own), a proxy that strips the CORS header, a page opened from disk, and
a page cached across an upgrade. With the header kept, the sandboxed page
worked. A page opened from disk worked, and a saved copy of a page that
names its files with `crossorigin` had files refused. A proxy that strips
the header breaks the sandboxed page, because a page with no origin of its
own needs CORS to read any file, but not a same-origin page. A cached page
that names an old hash fails when the file at that URL changed. The
security guide and the changelog describe each, under "Keep the CORS
header" and "Keep files unchanged".

**Tests added.** `test_owned_file_integrity.py` renders each route to
the page and compares the hash with the route's body. It covers documents,
fragments, hooks and `Dependency` objects. `test_base_element_e2e.py`
drives a browser with a `<base>` element, with and without a nonce policy,
and checks that the other site's script does not run.

## Ruled out

- **A Citry-served file running or applying from another site.** On
  every route tested the browser refused the other site's answer in both
  browsers. That includes the nonce case, which was the main risk. The
  claim covers files Citry serves, not the files and tags under "Files
  Citry cannot hash".
- **A hash that does not match the route.** All 1,009 values matched the
  bytes the route sent, in the runs made before the two corrections below.
  One function, `_OwnedResource.integrity`, computes every hash, and the
  `_render()` methods of `Script` and `Style` add it, so documents,
  fragments and the asset list the runtime reads share one step.
- **A Citry-added hash counted as the author's.**
  `_serialization_security.py` keeps a hash Citry added apart from one the
  author wrote, so the dependency output does not report Citry's own hash
  as one the author declared and verified.
- **A doubled attribute.** `fetch_attrs` compares names without regard to
  case, so an author's `CrossOrigin` is kept and Citry adds no second
  spelling.
- **Files Citry cannot hash, by design.** An author's own URLs, a tag
  written by hand, and a tag an extension moves or rebuilds as a new
  object get no hash. The browser run covered an author's URLs and the
  hand-written tag, and those files still load from the other site, as the
  advisory says. The security guide lists these cases and recommends
  `base-uri 'self'`, or `'none'` when a page has no `<base>` element.
- **The injection itself.** The fix does not stop HTML injection. The
  guide and the advisory say so.

## Fixed during the review

- A `Dependency` copied with `dataclasses.replace` lost its file's bytes,
  and so its hash, without any message. The field is now a keyword-only
  init field, which `replace` keeps. `test_replace_keeps_the_file` and
  `test_hook_that_rebuilds_a_tag_keeps_the_hash` cover it.
- A `css_data()` stylesheet (the stylesheet built from a component's
  `css_data()` values) that the cache had dropped before a fragment was
  written lost its hash. `_variables_style` now reads the
  stylesheet bytes the render itself produced first.
  `test_stylesheet_the_store_dropped_keeps_its_hash` covers it.

## Not tested

- WebKit and Safari. Only Chromium and Firefox ran.
- Browser runs of releases other than 0.1.0 and 0.4.0.
- Real proxies and CDNs. A local server that strips CORS stood in for
  them.
- A shared cache such as Redis. The test scripts used an in-memory
  stand-in.
- The full URL comparison on the merged commit, as explained above.
- A rolling deploy that serves pages and files from two versions at once.
  The guide describes the symptom, and no run reproduced it.
- A tag an extension moves or rebuilds, in a browser. The advisory states
  that such tags are not covered, and the checks of them ran by script
  only.
- `X-Forwarded-Prefix` in a browser.
- Races between a hot reload and a render.
- Interactive pages with a per-call `security_csp` or
  `security_javascript` setting, in a browser.
- The browser test `test_base_element_e2e.py` on the final commit. It
  passed in Chromium and Firefox on an earlier commit, and the probes
  cover the runtime tag of the final one.

## Follow-ups

None open. The files the fix does not cover are a documented limit, in
[the security guide](https://github.com/citry-dev/citry/blob/d4e2cca39a3384edadd26e7889c593ebb6e03022/docs_site/content/security.md)
under "Limit the `<base>` tag". The same `<base>` element also moved the
addresses of Citry's event calls and message requests. That is covered
by [GHSA-xmx5-6846-xq2r](https://github.com/citry-dev/citry/security/advisories/GHSA-xmx5-6846-xq2r),
and its record sits beside this one.
