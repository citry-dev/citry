---
title: v1.0.1
url: https://citry.dev/v/1.2.0/releases/v1.0.1/
description: "What changed in citry v1.0.1."
---
# v1.0.1

Citry 1.0.1 is a security release. It requires citry-core 2.1.1, which
installs with it. citry-ui 0.6.1 is released at the same time. Some of
the fixes refuse input or pages that 1.0.0 accepted, so read "Upgrading
from 1.0.0" before you deploy.

## Upgrading from 1.0.0

- On a page whose Citry script has no CSP nonce, a Vue fragment that
  Citry finds in the page no longer starts when it names a script Citry
  does not serve, such as a `Script(url=...)` dependency. Start such a
  fragment from your own script with `Citry.fragments.load()`, passing
  only data your own server wrote, or give the page a nonce-based CSP.
  Such a fragment also does not start when its data names Citry's files
  on another host or under a path other than your Citry prefix, as after
  a CDN rewrites those URLs. A CDN that serves only Citry's own script
  still works when it keeps your Citry prefix in the script's path, such
  as `/citry/citry.js`.
- On a page with a nonce-based CSP, a fragment or page data block whose
  nonce is only on its tag no longer starts. `serialize(csp_nonce=...)`
  already writes the nonce into the JSON as well; check any middleware
  that adds nonces by rewriting the HTML.
- Citry's browser code now resolves a relative URL of a script or
  stylesheet it adds against the page's address, not against a `<base>`
  tag. A `Script(url="static/app.js")` without a leading `/` on a page
  with a `<base>` tag now loads from the page's own folder. Write such a
  URL from the site root, such as `Script(url="/app/static/app.js")`, so
  it loads from the same place on every page.
- Each `css_data()` stylesheet gets a new URL, and a cached component
  render that includes one is rendered again the next time it is used. A
  page that a visitor opened before the upgrade shows the component
  without those values until it is reloaded.
- If you use a shared cache, such as Redis or memcached, delete the keys
  that earlier releases wrote for `css_data()` and `js_data()` once
  every worker runs this release. They are the keys that match
  `citry:*:css:*` or `citry:*:js:*` and do not contain `:component:`,
  and every key that starts with `citry:vue-style:`. Until you delete
  them, someone can still confirm a guessed value by timing its 404
  once. For a component class you renamed or removed since, this works
  on every request. Deleting them also removes stylesheets that this
  release wrote, so a page opened before then may show components
  without their `css_data()` values until it is reloaded. Clearing the
  whole cache also works, but it also drops the State that Citry keeps
  in the cache.
- Workers that share a cache must all set `secret`, or all leave it
  unset. While a deploy moves workers from 1.0.0, or from no `secret` to
  a `secret`, pages that the older workers render may show components
  without their `css_data()` values until the deploy ends.
- If a CDN or shared proxy sits in front of Citry, purge its copies of
  `/cache/` and `/ext/events/assets/`.
- If your app sets `cache` but not `secret`, set `secret` when
  `css_data()` returns values that differ between visitors. Citry logs a
  warning in that setup.
- To rotate `secret` while old and new workers run at the same time,
  deploy the new secret as the second entry first, and move it to the
  front in a later deploy. A worker that does not hold the new secret
  yet refuses the State and stylesheet URLs made with it.
- When a `<c-element>` gets `svg` or `math` from `c-is` or `c-bind`, its
  body may hold text, `{{ }}` values, nested `<c-element>` tags, and
  elements written in the template. Citry now raises `ValueError` for a
  `Markup` value that holds a tag, and for a `<c-raw>` block, a child
  component, a `<c-slot>`, or a `<script>` element in that body. Write
  the `<svg>` or `<math>` element directly in the template when it needs
  such content, for example in a `c-if` branch.
- A `<c-slot>` in such a body raises when a template fills it, even
  with plain text. A slot that the caller fills from Python with a
  plain `str` still renders, because Citry escapes it. So `<c-i18n>`
  with a `tag` of `svg`, and Citry UI layout components given
  `attrs={"is": "svg"}`, raise when their content is written in a
  template.
- The same applies when data chooses the MathML tag `mglyph` or
  `malignmark`.
- In an interactive component (one with `js`) and in an Events `Render`,
  a `Markup` value that holds a `<noscript>` element now raises
  `ValueError`, also inside a `#c-ignore` or `v-pre` element.
- `c-bind`, and an extension's `on_attrs_resolved` hook, can no longer
  set `ref`, `ref_for` or `ref_key`; Citry raises `ValueError`.
- `c-ref="..."` now raises `ValueError`, whatever its value. Write
  `ref="name"` as plain text instead.
- The built-in `element` component raises when Python passes it a `ref`.
- A `<c-element>` with `c-is` or `c-bind` raises for `ref_for` and
  `ref_key` written in its template. A plain text `ref="name"` on it
  still works.
- Events now refuses a `Decimal` argument, State write or State value
  whose size, ignoring the sign, is 1e309 or more, or that has more than
  308 decimal places, with a 422 `invalid_args` error. This also applies
  to a State token that an earlier release signed, and to a State your
  own code filled with such a number. Keep such numbers out of State, or
  store them as text.
- With `security_javascript="forbid"`, a page that embeds a `data:`
  document whose type is not plain text, CSS, CSV, JSON, or a PNG, GIF,
  JPEG, BMP or ICO image now raises. This covers a PDF, a WebP image or
  an MP4 file opened by a frame, link, form, `<object>` or `<embed>`.
  Serve such a file from a URL instead.
- The output checks (`security_javascript` and `security_csp`) now also
  read a page with a `</form>` the way Chromium and WebKit read it
  inside a `<template>`, so a page that passed before can now raise.
  Close every element inside a form before its `</form>` to avoid this.
- With `security_javascript="forbid"`, an Events handler's answer to a
  plain form post, or to a link that opens a `GET` handler, now fails
  with a 500 error when the page it renders needs JavaScript, as a
  normal render does. Before, Citry served that page with a warning.
- `Citry(sandbox_expressions=...)` accepts only `True` or `False`. A
  value such as `1`, `"yes"` or `None` now raises `TypeError` when the
  app is built.

## Fixes

- Security: Citry now escapes rendered markup that a template writes
  into an HTML attribute in every case, such as `c-title="<>{{ value
  }}</>"` or a component input that holds such markup and is passed to
  `c-title`. Before, three kinds of render wrote it unescaped: a
  template that holds another template language's syntax through an
  extension that uses the experimental `on_template_foreign_spans` hook
  (for example, to use Django template tags); a slot rendered with
  `str(slot)` after the page render; and a slot rendered in a worker
  thread. A component inside such markup now raises in those renders, as
  it already did elsewhere.
- Security: Citry now escapes a Django `SafeString` (from `mark_safe` or
  `format_html`) that a template writes into an HTML attribute, as it
  already escaped `Markup`. Before, it was written unescaped by
  `c-<name>` attributes, `c-bind`, `<c-element>` and `format_attrs()`,
  and by `#c-key` in the three kinds of render listed above, so a `"` in
  it could end the attribute and add another one, such as `onmouseover`.
  A component with Vue bindings also no longer fails with a `TypeError`
  on such a value.
- Security: Citry now starts a Vue fragment or page data block only when
  both its tag and its JSON data carry the page's CSP nonce. A nonce on
  the tag used to be enough, and injected markup could take that
  attribute from the next tag that has one.
- Security: on a page whose Citry script has no nonce, a Vue fragment
  found in the page now starts only when every script it names is a file
  Citry serves from the page's own origin, it sends its server events
  and its requests for translated messages to Citry's own routes, and it
  mounts into the element Citry wrote for it. Injected markup could
  start a fragment that loaded any script the page's CSP allowed, which
  under a hash-based CSP with `'strict-dynamic'` meant a script from any
  site.
- Security: an injected `<base>` tag can no longer move the scripts and
  stylesheets that Citry's browser code adds to the page, or the Citry
  script that a fragment adds, to another site, even when the page's CSP
  has no `base-uri`.
- Security: someone who guesses a `css_data()` value can no longer
  confirm it by requesting the stylesheet URL that value would produce.
  Citry now builds that URL from the values and a key. An app that sets
  `cache` needs `secret` set as well for this.
- Security: Citry no longer serves a `js_data()` script that an earlier
  release left in a shared cache. With `secret` set, it also no longer
  serves a `css_data()` stylesheet left there.
- Security: a `<c-element>` whose tag comes from data can no longer
  place trusted HTML inside `<svg>` or `<math>`, where the browser reads
  elements such as `<style>` and `<noscript>` as markup. A `Markup`
  value that is harmless in HTML, such as sanitizer output, could run
  script there.
- Security: in an interactive component and in an Events `Render`, a
  `Markup` value that holds a `<noscript>` no longer runs its contents
  in Chromium and WebKit, the engine in Safari. Vue builds such a value
  inside a `<template>`, where those browsers read the `<noscript>`
  contents as markup. Citry now refuses the value on the server, and its
  browser code refuses it too.
- Security: a `ref`, `ref_for` or `ref_key` attribute name or `c-ref`
  value from data no longer reaches Vue. Vue stored the element in the
  component's own `setup()` value of that name, so data could replace a
  value that the component showed with `v-html`, and run script.
- Security: Citry now refuses, with the usual 422 `invalid_args` error,
  a `Decimal` event argument, State write or State value whose size,
  ignoring the sign, is 1e309 or more, or that has more than 308 decimal
  places. Such a short value could make one request use gigabytes of
  memory or hours of CPU time when a template formatted it with `.2f` or
  `%d`, or app code called `int()` on it.
- Security: with `security_javascript="forbid"`, an Events handler's
  answer to a plain form post, or to a link that opens a `GET` handler,
  now fails with a 500 error when it needs JavaScript, as a normal
  render does. Citry used to serve it with only a warning, including a
  `javascript:` link built from request data or an `onclick` written in
  the template.
- Security: the output checks (`security_javascript` and `security_csp`)
  now find a script hidden behind a `</form>` that Chromium or WebKit
  reads differently. Chromium differs inside a `<template>` written in
  the page, including a declarative shadow root, which the browser shows
  as soon as the page loads. When a script sets the HTML of a
  `<template>`, as the security docs recommend for inserting a fragment,
  WebKit differs, and so does Chromium for a `</form>` inside a
  `<noscript>`. A page that passed before can now raise.
- Security: `security_javascript` now counts a `data:` URL that a frame,
  link, form or refresh opens as running code unless its type is plain
  text, CSS, CSV, JSON, or a PNG, GIF, JPEG, BMP or ICO image. WebKit,
  the engine Safari uses, shows a `data:` document as HTML when it
  cannot display the type, such as a font, `application/octet-stream`,
  or a listed type written with a control character such as a form feed.
  The check also reads the `href` of a MathML element, which WebKit and
  Firefox open like a link's, and reads an HTML `data:` URL with its
  tabs and line breaks kept, as Chromium reads it, as well as without
  them. A download link (`<a download>`) still allows text, images,
  audio, video, fonts, PDF and `application/octet-stream`.
- Security: `Citry(...)` now raises `TypeError` when
  `sandbox_expressions` is not `True` or `False`. Such a value, like
  `None` from an unset environment variable, `""` or `0`, used to turn
  the expression sandbox off without an error.
- A malformed State token, or a malformed `cache/` or `asset/` URL, now
  gets a 403 or 404 instead of a server error when Citry's cache is a
  Django memcached backend.
- A `local_files = "serve"` file whose extension holds anything but
  ASCII letters, digits and `._~+-`, or is longer than 128 characters,
  is now written into the page, because a link to it would not load on
  every server and cache backend.
- Printing or logging `CitrySettings` no longer shows the `secret`.
- Citry's browser code now refuses the same tags for a `<c-element>` as
  the server does, such as `iframe` and `noscript`.

## Added

- You can now start a Vue fragment from your own script with
  `Citry.fragments.load()`. Citry does not check the data you pass, so
  pass only data your own server wrote.