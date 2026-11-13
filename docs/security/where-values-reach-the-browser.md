# Where a value reaches the browser

Citry turns Python values into HTML, CSS, JavaScript, and browser actions.
This page lists the places where a value can reach the visitor's browser.
It belongs to the security pass in
[`CLAUDE.md`](../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)
(Mechanism 7). When a change touches one of these places, check it with
steps 1 to 3 of that pass, and name the place in the security brief you
give the independent reviewer (step 4).

- **Text and markup.** `{{ }}` output, `Markup`, `<c-raw>`, slot content,
  `v-html` and Vue bindings that set a DOM property, and the HTML a Vue
  fragment or an Events `Render` action inserts after the page has
  loaded. HTML that Citry parses and writes again must mean the same
  after the rewrite.
- **Attribute names, not only values.** A `c-bind` spread or a Citry UI
  `attrs=` argument (and the other `*_attrs=` arguments) lets data choose
  the name. A data-chosen name can add an `on*` handler, set a DOM
  property such as `innerHTML`, or contain a form feed or other control
  character, which the browser reads as the end of the name.
- **URL attributes.** `href`, `src`, `action`, `formaction`, `srcset`,
  `xlink:href`, the URL in `<meta http-equiv="refresh">`, and the `to`,
  `from`, `by` or `values` of an SVG `<set>` or `<animate>` that changes a
  link. A `javascript:` URL runs code, and a `data:` URL can open a
  document that runs code.
- **Embedded documents.** An `iframe srcdoc` value, or a `data:` document
  opened in a frame, by a link or by a form, is a whole page with its own
  scripts and its own embedded documents.
- **Tag names.** `<c-element>` and the Citry UI components that take a
  tag. A data-chosen `script`, `style`, `plaintext` or `iframe` changes
  how the browser reads the element's content, and `base`, `meta` or
  `link` changes how the page loads.
- **CSS.** `css_data()` values, in the stylesheet Citry generates from
  them and in inline `<style>`, and `:style` bindings. Citry must write
  them so they read the same under any encoding the page declares.
- **JavaScript and JSON.** `js_data()`, the JSON Citry writes into
  `<script>` blocks (Events, i18n and Vue data), Events responses, and any
  value that ends up in a Vue or `$c-tr` expression the browser compiles.
- **Translated messages.** A translated message and the values put into
  it, through `tr()`, `<c-trans>` and the browser i18n runtime.
- **Markers for Citry's browser code.** Render ids, root markers and
  hydration markers. Data must not be able to write one.
- **Addresses and keys the browser code takes from the server.** Fragment
  and definition scripts, Events request URLs, and State and locale
  names, which the browser code must look up so that a name such as
  `__proto__` reaches only its own entry.
- **Navigation.** `Redirect`, `PushUrl` and `ReplaceUrl`, including the
  `Location` header on the no-JavaScript form path, which must not hold a
  control character.
- **Element `id` and `name`.** Citry's browser code must read `window`,
  `document` and form members so that a data-chosen `id` or `name` cannot
  change what it gets.
- **The CSP nonce.** Every path that gives the page's nonce to a script,
  including fragments inserted after the page has loaded.
- **The opt-in output checks** (the `security_csp` and
  `security_javascript` settings).
  They must read attribute values and URLs as the browser reads them. A
  check that reads a value differently lets code through or refuses
  harmless text.
- **Responses Citry serves.** `Content-Type` and its charset,
  `X-Content-Type-Options`, `Cache-Control`, `Content-Disposition` on a
  `Download`, the text of error bodies, and error output shown in the
  page, such as the error fallback.

When a review finds a new place, add it to this list in the same change,
or, for a hole in a released version, when its advisory is published.
