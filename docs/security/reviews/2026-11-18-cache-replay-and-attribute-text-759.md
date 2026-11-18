# Cache replay, stylesheet writes, class names and attribute text (#759)

- **Pull request:** [#759](https://github.com/citry-dev/citry/pull/759),
  merged 2026-11-18 (b4d027c77)
- **Reviewer:** a separate reviewing agent (technical and security), then
  a separate prose pass, as the pull request description states. The
  pull request holds no report, comment or review thread. This record is
  built from the description, the merged change and its tests.
- **Code:** in `packages/py/citry/citry/`: the check of staged text
  replacements in `ext/cache/replay.py` (it calls `is_binding_id`);
  `publish_css_data_stylesheets` in `ext/dependencies/emission.py`; the
  replayed `<textarea>` path in `_vue/leaf_program.py` and
  `_vue/serialization.py`; `_IdentityKey` in `_pure.py`; `_class_piece`
  and `_merge_class_mapping` in `attrs.py`; `escape_attribute_value` in
  `util/html.py` and its two callers in `_vue/leaf_program.py`; and the
  warning after `_server_contents_pass_policies` in
  `_vue/serialization.py`. Tests in `packages/py/citry/tests/`:
  `test_ext_cache_typed_artifact.py`, `test_ext_cache_component.py`,
  `test_css_data_stylesheet_names.py`, `test_component_pure.py`,
  `test_attrs.py`, `test_attribute_numeric_references.py`,
  `test_simple_vue_row_html.py` and `test_vue_hydration_regions.py`

## Who controls the input

Seven small changes, all in Python:

1. **Text replacements on render cache replay.** A payload extension (an
   extension that stores extra data with a cached render) may stage a
   text replacement that Citry writes into the stored HTML when it
   replays the render. The app author installs the extension. Citry now
   checks every binding ID (the internal names that tie translated text
   to its place in the page) in the old and new values, not only the
   ends of the marker, and the values must be exactly those IDs joined
   by single spaces. The built-in i18n extension already writes this
   shape. Anything else makes Citry render the component again instead
   of replaying it.
2. **The `css_data()` stylesheet with a configured cache.** The values
   come from the app's Python code. When the cache dropped the stylesheet
   after the render, the page linked a URL that answered 404. Citry now
   writes each linked stylesheet into the cache again when it writes the
   page. The browser applies it as CSS.
3. **A replayed `<textarea>`.** A cached component that writes a value
   into a `<textarea>` came back empty on replay. The serializer now gets
   the stored parts that mark the dynamic text.
4. **The memo for `pure = True` components.** It is keyed by the body
   object rather than its `id()`, so a later body at a reused address
   cannot match an earlier entry.
5. **`c-class` and `c-style` keys.** The template author or the app's
   Python code supplies them. A Django lazy translation now works as a
   class name, and a `Markup` class or style key is decoded once, so
   `&amp;` is not escaped twice.
6. **A carriage return in an attribute value.** The browser reads a raw
   carriage return in an attribute value as a line feed.
   `escape_attribute_value` now writes it as `&#13;`, and the two
   attribute writers in `_vue/leaf_program.py` call the same function.
   The value may come from request data. The browser reads it as
   attribute text.
7. **`security_csp` on a Vue page.** When the server HTML a Vue host
   would carry fails the CSP check, Citry sends the host empty, and the
   page's own check then finds nothing. Citry now warns with what its
   check of the server HTML found, in `"warn"` and `"strict"` mode
   alike. The render is not refused.

Of the places in the list of where values reach the browser (Mechanism 7
in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "Text and markup", "CSS", "Markers for Citry's
browser code", "Responses Citry serves" and "The opt-in output checks".

## How it was checked

- **Code read.** The reviewer read the change with a security brief for
  the places named above.
- **Each new test fails without its fix.** The author reverted each
  part of the change in turn and saw its test fail.
- **The `citry` test suite without the end-to-end tests:** 14,781
  passed, 9 skipped, 1 expected failure. Two failures and two collection
  errors also happen on `main` in the same environment. They come from
  an unpinned `tzdata` release, an unpinned `pydantic` release, and two
  files that import `citry_ui`, which was not installed.
- **Linters.** `ruff check`, `ruff format --check` and `mypy` on the
  touched files (also with `--platform linux`) were clean.
- **Versioning.** The reviewer agreed that the change fits a patch
  release: nothing a user passes in is refused, and no stored or wire
  format changes.

## Ruled out

- **Replay writing text that is not binding IDs into stored HTML.**
  Every ID is checked, and any other shape falls back to a fresh render.
  `stage_render_cache()` is experimental, and the render still succeeds.
- **A cache entry from one pure body served for another.** The memo key
  holds the body object itself.
- **A `Markup` key decoded twice or not at all.** It is decoded once,
  and the same fix covers style keys.
- **Two Python writers encoding a carriage return differently.** Both
  leaf-program writers call `escape_attribute_value`.

## Fixed during the review

- The double-escape fix was extended to `Markup` style keys.
- Updated line references in `docs/design/trust_boundaries.md`.
- A tighter assertion in the textarea test.
- The prose pass reworded the changelog entries, the warning text (it
  now says what to do), comments and docstrings.

## Not tested

- **Real browsers and the end-to-end tests.** They did not run.
- **The Vue server renderer.** The HTML it writes for a hydrated page
  still keeps a raw carriage return in an attribute value. Changing it
  needs a `citry-core` release.
- **The cost of item 2.** It adds one cache read for each linked
  `css_data()` stylesheet every time a page is written. The
  description records no measurement.

## Follow-ups

- [#768](https://github.com/citry-dev/citry/issues/768): encode a
  carriage return in attribute values in the Vue server renderer too.
- [#767](https://github.com/citry-dev/citry/issues/767): check what is
  left of the `class` and `style` whitespace follow-up from #610.
- [#766](https://github.com/citry-dev/citry/issues/766): cached and
  uncached renders treat `textContent` and `innerText` bindings
  differently.
- [#763](https://github.com/citry-dev/citry/issues/763): a development
  warning for `inject()` without `vary()` in a cached render, and a
  decision on a `<c-cache>` key that is not a literal.
- [#764](https://github.com/citry-dev/citry/issues/764): compare
  `str` subclass keys as plain strings in the expression sandbox.
- [#765](https://github.com/citry-dev/citry/issues/765): apply Citry's
  request `Decimal` limit before app Pydantic validators run.
- #764 and #768 are optional parts of the release batch in
  [#776](https://github.com/citry-dev/citry/issues/776).
