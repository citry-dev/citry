# Who may supply each input that reaches the page

**Status (2026-11-15): written against `main` for the citry 1.0.0
release** (the `citry` package was at 0.9.0). Line numbers are from the
commit that adds this file. Every row names the function that does the
work; when that function changes, the row changes in the same pull request
(see [Keeping this doc accurate](#keeping-this-doc-accurate)).

Citry turns Python values, template source, and HTTP requests into HTML,
CSS, and JavaScript. For each value that ends up in the page, an app
developer needs one answer: can this come from a visitor's request, or must
only my own code or my template write it? Without this doc, that answer is
spread over the security page, docstrings, and the code, and each reviewer
of a security pass (Mechanism 7 in [`CLAUDE.md`](../../CLAUDE.md)) has to
work it out again. This doc collects it in one place, one table per area
of the API.

Section 2 of [`security-hardening.md`](security-hardening.md) lists who can
supply a value: the template author, the app developer, an extension
author, a visitor, the cache operator, and others. This doc says which of
them may supply each input.

## How to read a row

Each row answers four questions.

1. **Who may supply it.** Most rows use one of four answers:
   - **Request data OK**: Citry escapes or checks the value so that data from
     a visitor cannot run code, load a resource, or send the browser to an
     address of its choosing. The app
     may still need its own checks for meaning (for example, whether a
     redirect target is a site it trusts).
   - **App code**: the app's Python code chooses the value. Citry escapes it
     for the place it lands but does not check what it means, so request
     data must be checked by the app first (for example, a URL scheme).
   - **Author only**: only the person who writes the template or the
     component class may write it. The value is source code, or Citry
     inserts it without escaping. Code that acts as an author, such as an
     extension hook that returns template source, counts as an author.
   - **Undecided**: the trust level is not settled. The row links the issue
     that decides it. This doc does not guess, because a guess in a trust
     table reads as a promise.

   A row may split the answer by value type (a plain `str` and `Markup`
   often differ), or name another supplier, such as Citry itself, extension
   code, or whoever can write the cache store.
2. **What the browser does with it**: shows it as text, parses it as
   markup, applies it as CSS, runs it, navigates to it, or uses it as a key.
3. **What Citry does, and where**: the one function that escapes, checks,
   or passes the value through, as `file:line`, and the render paths that
   reach it.
4. **What the docs say**: the public page or docstring that states the
   rule. "Missing" means the code makes the input author only or app code
   but no public page says so yet.

Paths are repo-relative, with these short forms:

- `citry/` is `packages/py/citry/citry/`
- `ui/` is `packages/py/citry_ui/citry_ui/`
- `js/` is `packages/js/citry-client/src/`
- `tp/` is `crates/citry_template_parser/src/`
- `vc/` is `crates/citry_vue_compiler/src/`
- `docs/` is `docs_site/content/`

## The render paths every row refers to

A rule that holds on one render path but not another is a hole, so each row
says which paths it covers. These are the paths:

- **Capture.** Every ordinary render first records its output as a list of
  parts: text values, trusted HTML, and element start tags with their
  attributes (`citry/component_render.py:1069-1076`, `citry/_vue/capture.py`).
  The next two paths, static HTML and Vue, each turn that list into the
  page, so a check made while recording applies to both.
- **Static HTML.** A page or subtree without Vue. `citry/serialize.py`
  writes text values with `escape_to_str` (`citry/serialize.py:1351`) and
  trusted HTML as it is (`:1354`).
- **Vue.** A component with `js`, Vue syntax, or Events bindings. No Python
  value becomes Vue template source: the template gets a reference such as
  `$citryPrepared.citryText3`, and the value travels as JSON in the page's
  data block (`citry/_vue/direct_capture.py`; design rule in
  [`vue.md`](vue.md), "Do not compile rendered values as source"). The
  Rust server renderer writes, from that JSON, the HTML that Vue takes
  over in the browser (hydration, `vc/server_render.rs`).
- **Leaf programs.** `simple=True` components and component bodies with a
  fixed shape, which Citry compiles to functions that write the output
  directly (`citry/_simple_runtime.py`, `citry/_vue/leaf_program.py`). They
  repeat the attribute-name checks of capture.
- **Node path.** The older node classes in `citry/nodes/__init__.py`. Only
  templates that embed spans of another template language (the
  experimental host-template embedding, called foreign spans in the code)
  render this way (`citry/component_render.py:3053-3062`).
- **Events `Render`.** An event handler that returns
  `Render(element=...)` re-renders through the same capture and writers.
- **Cached render.** `citry/ext/cache/replay.py` replays a stored capture
  through the same writers. Text is stored raw and escaped when written.
  Trusted HTML is stored and replayed as it is, so whoever can write the
  cache store is trusted like the database (section 11).

The shared escaping functions live in `citry/util/html.py`:

- `escape` (`:81`) and `escape_to_str` (`:97`) escape HTML text
  (`& < > ' "` and ESC). A value with `__html__` passes through unchanged.
- `escape_attribute_value` (`:547`) escapes a double-quoted attribute value.
  A value with `__html__` is first decoded to the text a browser reads
  (`decode_attribute_entities`, `:531`) and then escaped, so a `Markup`
  value cannot end the attribute.
- `script_json` (`:580`) writes JSON for a `<script type="application/json">`
  block: pure ASCII, every `<` written as `\u003c`, so no `</script` or `<!--` can
  appear and the bytes read the same under any page encoding.

## 1. Text in the template

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| `{{ expr }}` result: `str`, number, or other ordinary object | Request data OK | Text | Escaped for HTML text on every path: capture keeps it as a text value (`citry/_vue/capture.py:946`); static HTML writes it with `escape_to_str` (`citry/serialize.py:1351`); Vue sends it as JSON and sets a text node (`citry/_vue/direct_capture.py:3035`, `:4347`), and the server renderer writes it with `escape_text` (`vc/server_render.rs:4376`); node path and leaf programs use `_render_value` (`citry/citry_render.py:888`). Inside an HTML comment `{{ }}` is not evaluated (`html_comment_content`, `tp/grammar.pest:75-82`); it stays author text. | `docs/syntax/expressions.md:135-148` |
| `{{ expr }}` result: `Markup` or any object with `__html__()` | App code (Citry inserts it unchanged) | Markup | Passed through: capture makes it trusted HTML (`citry/_vue/capture.py:962`); static HTML writes it raw (`citry/serialize.py:1354`); Vue sends it as an opaque HTML record the browser inserts with `createStaticVNode` (`citry/_vue/direct_capture.py:3067-3104`, `citry/_vue/client.js:903`) after `reject_cross_boundary_html` (`citry/_vue/opaque_html.py:36`) checks its shape. The shape check is not a sanitizer. | `docs/syntax/expressions.md:166-205` ("trusts the whole value") |
| `{{ expr }}` result: a component, `CitryElement`, `CitryRender`, or `Slot` | App code | Markup | A component renders with its own rules; a `CitryRender` is inlined as already-trusted HTML (`citry/citry_render.py:950-951`); a `Slot` follows section 4. | `docs/syntax/expressions.md:141-143` |
| `{{ expr }}` inside a `<script>` or `<style>` the template writes | App code (the author chooses the place). Never request data; app data only after the app escapes it for JavaScript or CSS itself | Runs / CSS | The grammar evaluates `{{ }}` there (`tp/grammar.pest:182-203`) but the value gets only the HTML escape, which is not a JavaScript or CSS escape. Data cannot write `</script>`, but it can leave a JavaScript string or add CSS rules. | `docs/advanced/js-and-css-dependencies.md:225-229` ("send data with `js_data()`") |
| Literal template text, static tags, HTML comments | Author only | Markup | Copied as written (`tp/compiler.rs:266-272`). | Author source |
| `<c-raw>` body | Author only | Markup | Copied as written, no template processing (`tp/compiler.rs:398-421`); on a Vue page it must be a complete fragment. | `docs/syntax/raw.md:25-30` |
| `Component.on_render()` return | `str`: request data OK. `Markup`, `CitryRender`, component: app code | Text / markup | `_text_or_html_part` (`citry/component_render.py:2877`) escapes a plain `str` and passes `__html__` through, for static, Vue, and Events `Render` paths. | `docs/advanced/hooks.md:63-95` |
| `<c-error-fallback fallback="...">` | `str`: request data OK. `Markup`: app code | Text / markup | Returned from `on_render`, so the same `_text_or_html_part` rule applies (`citry/components/error_fallback.py:83`). The exception object reaches the `fallback` fill as data and is escaped by `{{ }}`. | `docs/concepts/error-boundaries.md:48-50`, `:68-73` |

## 2. Attributes

### 2.1 Attribute values

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| Static attribute written in the template | Author only | As the attribute means | Copied as written (`tp/compiler.rs:690-700`); kept as source text in capture (`citry/_vue/capture.py:505-506`). | Author source |
| `c-<name>="expr"` value, and `c-bind` mapping values, on an HTML element | Request data OK as text. App code where the name loads, navigates, or runs the value (2.3) | Attribute text, or acted on by name | Escaped for a double-quoted value on every path, `Markup` included: `_format_resolved_attrs_to_str` (`citry/attrs.py:870`) calls `escape_attribute_value`. Callers: static HTML (`citry/_vue/capture.py:499`), Vue (`_vue_attribute_value`, `citry/_vue/json_data.py:246`; server renderer `escape_attribute`, `vc/server_render.rs:4391`), `<c-element>` (`citry/components/dynamic.py:433`), leaf programs, node path (`citry/nodes/__init__.py:1478`). No path checks what the value means. | `docs/syntax/attributes.md:56-59`; `docs/advanced/html-attributes.md:246-254` |
| `class`, `c-class` | Request data OK | Class names | `normalize_class` (`citry/attrs.py:499`), then the value escape. | `docs/syntax/attributes.md` |
| `style`, `c-style`, a `style` key in `c-bind` | App code | CSS | `normalize_style` (`citry/attrs.py:572`) writes `prop: value;` with no CSS check; only the attribute escape applies. Data can add declarations, such as a `background: url(...)` that loads a resource. | `docs/syntax/attributes.md` (`c-style`) |
| `c-<name>="<>...</>"` nested template on an HTML element | Author only (the markup); `{{ }}` values inside follow section 1 | Attribute text | Ordinary renders format the rendered result with `format_attrs`, so it is escaped as attribute text (test: `packages/py/citry/tests/test_nodes.py:215-231`). On the node path the mixed branch (`citry/nodes/__init__.py:1513-1518`) writes the render without an attribute escape. A `{{ }}` value inside is still HTML-escaped (a `"` becomes `&#34;`), so request data cannot end the attribute; only `Markup`, `<c-raw>`, or a component's own markup could, and those are app or author input. Not tested: [#702](https://github.com/citry-dev/citry/issues/702). | `docs/syntax/nested-templates.md` |

### 2.2 Attribute names

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| A name written in the template, including `c-on*` and `c-srcdoc` | Author only (the name). The value of `c-on*` and `c-srcdoc` is app code | `on*`: runs; `srcdoc`: a whole page | The grammar checks name syntax (`tp/grammar.pest:306`); an authored `on*` or `srcdoc` name is allowed on a plain element and its value only escaped. On a page with Vue, an authored `c-on*`, `c-innerHTML`, or `c-outerHTML` raises (`citry/_vue/direct_capture.py:3268-3279`, `:4284`; leaf programs `citry/_vue/leaf_program.py:3927`); `c-srcdoc` is allowed. | `docs/advanced/html-attributes.md:235-237` |
| `c-bind` keys on an HTML element | Request data OK for ordinary names. Undecided for Citry's marker names: [#699](https://github.com/citry-dev/citry/issues/699) | Attribute names; Vue may set a DOM property of that name | Every key, on capture, node path, leaf programs, and i18n elements: `validate_html_attr_name` (`citry/attrs.py:425`: no whitespace, control characters, quotes, `/ < = >`), `reject_vue_code_attr_name` (`citry/attrs.py:220`: `v-`, `:`, `@`, `#`, `.`, `^`, `$c-tr`), `reject_script_capable_attr_name` (`citry/attrs.py:269`: `on*`, `innerHTML`, `outerHTML`, `srcdoc`, any case), `_reject_reserved_events_attr` (`citry/nodes/__init__.py:155`: `data-cev-*` and two runtime names). Call sites: `citry/nodes/__init__.py:1416-1423`, `citry/_vue/leaf_program.py:4043-4045`, `citry/ext/i18n/bindings.py:355-360`. Names Citry reads as its own markers (`c-render-id`, `data-cid-*`, `data-citry-*`) are not refused yet. Undecided: [#699](https://github.com/citry-dev/citry/issues/699). | `docs/advanced/html-attributes.md:227-231`, `:259-264`; `docs/syntax/attributes.md:385-409` |
| `c-bind` keys that are Citry Events bindings (`@c-click`, `:c-query`) | App code (the key picks the server handler) | Calls a handler | Let through by `is_vue_code_attr_name` (`citry/attrs.py:139-142`, `_CITRY_OWNED_ATTR_PREFIXES`), handled by the Events extension. | `docs/syntax/attributes.md:405-409` ("never from request data") |
| `c-bind` keys on a component tag | Request data OK (they become keyword arguments, and are checked again where the component spreads them) | None directly | `ComponentNode` spread (`citry/nodes/__init__.py:2190-2240`): exact `str`, no Vue-code names, no State binding names, no `$c-tr`. | `docs/syntax/attributes.md:256-272` |
| Every name on `<c-element>` with `c-is` or `c-bind` | Request data OK for ordinary names; authored `on*` and `srcdoc` are refused too. Undecided for Citry's marker names: [#699](https://github.com/citry-dev/citry/issues/699) | Attribute names | `_resolve_element_attrs` (`citry/components/dynamic.py:377-379`) checks every name, written or spread. Vue-code names are refused earlier, at the component-tag spread (`citry/nodes/__init__.py:2223`), and by the Vue writer (`citry/_vue/direct_capture.py:3376`). | `docs/advanced/dynamic-components.md:223-229` |
| `format_attrs(mapping)` keys (a public Python helper) | App code | Attribute names | `format_attrs` (`citry/attrs.py:834`) runs `validate_html_attr_name` only. It does not refuse `on*`, `innerHTML`, `srcdoc`, or Vue-code names; those checks belong to the template callers. A template cannot place it inside a start tag, so this matters only to Python code that builds markup with it. | `docs/advanced/html-attributes.md` ("Format as HTML") and the `format_attrs` docstring. Whether the helper should refuse these names: [#700](https://github.com/citry-dev/citry/issues/700). |

### 2.3 URL attributes and embedded documents

Core Citry checks no URL scheme on any template attribute, on any render
path. Events `Redirect` (section 8), Citry UI (section 13), and the browser
runtime's script loader (section 14) check schemes. Whether core Citry
should check them is [#601](https://github.com/citry-dev/citry/issues/601);
until it decides, these inputs are app code. The opt-in output checks
report `javascript:` URLs in the HTML sent to the browser (section 12).

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| `c-href`, `c-src`, `c-action`, `c-formaction`, `c-srcset`, `c-xlink:href`, `c-poster`, `c-data`, `c-ping`, `c-cite`, and the same names from `c-bind` | App code (check the scheme first) | Navigates or loads; `javascript:` runs, `data:` can open a document | Attribute escape only (`citry/util/html.py:547`). Vue sets the same decoded text (`citry/_vue/json_data.py:283-286`). | `docs/security.md:206-226` ("does not check the scheme") |
| `c-content` on `<meta http-equiv="refresh">` | App code | Navigates after a delay | Attribute escape only. | `docs/security.md:216-219` |
| `c-to`, `c-from`, `c-by`, `c-values` on SVG `<set>` / `<animate>` | App code | Can change a link target | Attribute escape only; `attributeName` is not checked. | `docs/security.md:216-219` |
| `c-srcdoc` on `<iframe>` | App code (trusted markup) | Parses a whole page with its own scripts | Attribute escape only; the browser decodes it and runs what is inside. A data-chosen `srcdoc` name is refused (2.2). | `docs/advanced/html-attributes.md:246-254` |

## 3. Tags and dynamic components

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| `<c-element c-is="expr">` tag name | Request data OK | The tag decides how the browser parses the element | `_validate_tag_name` (`citry/components/dynamic.py:317`): name pattern, then refuses `applet base embed frame frameset iframe link meta noembed noframes noscript object plaintext script style template xmp` (`_REFUSED_DYNAMIC_ELEMENT_TAGS`, `citry/util/html.py:626`). Runs on every dynamic render; the Vue writer repeats it (`citry/_vue/direct_capture.py:3369`, `:3388`). A render is checked when it is stored in the cache (`citry/ext/cache/replay.py:925`); when it is read back, only the Vue writer checks again, and the static writer trusts the store (section 11). A data-chosen tag name also ends up in the public definitions bundle of a Vue component. A static `<c-element is="script">` is author source. | `docs/advanced/dynamic-components.md:174-208` |
| `<c-element>` body | As section 1 | Markup | Rendered like any body; only the default slot is accepted (`citry/components/dynamic.py:346`). | `docs/advanced/dynamic-components.md:220-236` |
| `<c-component c-is="expr">` (which component renders) | App code (map a request value through your own list) | That component's output | `_resolve_component` (`citry/components/dynamic.py:141`) accepts any registered name or `Component` class; any registered component can be chosen, including one that renders a `Markup` input. | `docs/advanced/dynamic-components.md` ("What `c-is` accepts") |
| `<c-i18n tag=...>` | Request data OK | Wrapper tag | Passed to `<c-element c-is>`, so the same `_validate_tag_name` applies (`citry/ext/i18n/components.py:52-57`). | `docs/reference/builtins.md:220-221` |

## 4. Slots and Citry's markers

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| `<c-fill>` body, the body between a component's tags, `<c-slot>` fallback | Author only (template source) | Markup | Compiled as template source, rendered at the callee's `SlotNode` (`citry/nodes/__init__.py:2995`). | `docs/concepts/slots.md:60-111` |
| `slots={"name": value}` and `Slot(value)` from Python | `str`, number: request data OK. `Markup`, component, `CitryRender`: app code | Text / markup | `Slot._resolve_content_func` (`citry/slots.py:360`) escapes a plain value; a callable's return goes through `_render_value` (`citry/slots.py:300`). | `docs/concepts/slots.md:231-234` |
| Slot data (`<c-slot c-user="user">`, `c-bind` on `<c-slot>`) and `c-name` | Request data OK | As the fill prints it | Passed to the fill's scope and escaped where the fill prints it. Vue slot props written on `<c-slot>` are author-only Vue code (`citry/nodes/__init__.py:644`). A `$c-tr` key from data is refused (`citry/nodes/__init__.py:171`). | `docs/concepts/slots.md:133-215`, `:342-375` |
| Render ids, `data-cid-<id>` root markers, `<template c-render-id>` child placeholders | Citry only | Read by Citry's server join step and browser code | Generated by `gen_id` (`citry/util/id.py:59`), checked by `validate_render_id`; markers added by `mark_html` (`crates/citry_html_transform/src/marker.rs:520`, from `citry/serialize.py:934`). Escaped text cannot write a tag, so it cannot write a placeholder. `Markup` and `<c-raw>` can (author or app input), and so can a `c-bind` key: [#699](https://github.com/citry-dev/citry/issues/699). | Internal |
| `<c-mark name="...">` | Author (name checked) | Events `Render` target key | `validate_mark_name` (`citry/components/mark.py:31`). | `docs/events/actions.md` |

## 5. Template source and the expression sandbox

Template source is code: the server runs its expressions and the browser
parses its markup. Every row here is author only. `docs/security.md:918-923`
and `docs/syntax/expressions.md:272-275` state the rule "never build a
template from request data".

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| `Component.template` | Author only | Markup; expressions run on the server | Loaded by `load_template` (`citry/assets.py:295`), compiled by `compile_template` / `compile_prepared_template` (`tp/compiler.rs:150`, `:161`). | Docstring `citry/component.py:724-729` |
| `Component.template_file` | Author only (a path from app code) | As above | Resolved next to the class, then `Citry(dirs=...)`; an absolute path is used as it is. | docstring `citry/component.py` |
| `Citry.render_template(source, ...)` | `source`: author only. Variables and slots: sections 1 and 4 | As above | Same parse and compile through a private root component (`citry/citry.py:388`). | Docstring `citry/citry.py:399` ("trusted standalone Citry template source") |
| `render_compiled_body`, `CompiledBody` (experimental host-template embedding) | Author only | As above | Checks the handle belongs to this engine (`citry/host_templates.py:79`). | Experimental; no page |
| Expression text in `{{ }}`, `c-*`, `c-for`, `c-if` | Author only | Server-side Python | `compile_expr(source, sandboxed=...)` (`packages/py/citry_core/citry_core/safe_eval/eval.py:253`); every call site passes the instance's `sandboxed` flag, so no path runs unsandboxed while the sandbox is on. | `docs/security.md:912-1069` |
| Values in the render context (`template_data()`, kwargs, `template_globals`, `provides`) | App code chooses the objects; their data may come from a request | What an expression can read and call | The sandbox blocks `_` names, unsafe builtins, `@unsafe` and `alters_data` callables (`.../safe_eval/sandbox.py:286`, `:335`, `:403`). It does not limit what public methods do. | `docs/security.md:924-929`, `:990-1019` |
| `Citry(sandbox_expressions=False)` | App code | Turns the sandbox off | `CitrySettings.sandbox_expressions` (`citry/settings.py:858`). | `docs/security.md:1050-1069` |

## 6. Component data and assets

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| `js_data()` values | Request data OK | JSON data | `_json_plain` (`citry/_vue/json_data.py:34`: exact JSON types, `Secret` refused), then `script_json` (`citry/util/html.py:580`). Same on Vue pages, Events `Render`, and cached renders. What the component's own Vue template then does with the value (`v-html`) is section 7. | `docs/vue/component-options.md:84-147` |
| `js_data()` top-level keys | Request data OK, within limits | Instance property names | `_check_js_data_keys` (`citry/component_render.py:3690`) refuses `$` and `_` prefixes (so `__proto__`) and `citryId`. | `docs/vue/component-options.md:137-146` |
| `css_data()` keys | Request data OK | Custom property names | `validate_css_var_name` (`citry/util/css.py:31`). | `docs/advanced/js-and-css-dependencies.md:192-195` |
| `css_data()` values | Request data OK for staying in one declaration. App code for a `url(...)` value | CSS; `url()` loads a resource | `serialize_css_var_value` (`citry/util/css.py:351`) refuses anything that could leave the declaration and writes every character outside printable ASCII as a CSS escape. Called for inline `<style>`, the served stylesheet, and again when a stored stylesheet is read from the cache (`citry/ext/dependencies/scripts.py:727`, `:828`). A raw `url(...)` passes, so data can choose an address the browser fetches. | `docs/advanced/js-and-css-dependencies.md` ("Send values to CSS") |
| `Component.js`, `Component.css`, `js_file`, `css_file` | Author only | Runs / CSS | `Dependency._check_validity` (`citry/ext/dependencies/types.py:171`) refuses inline content that contains `</script` or `</style`. Paths are not confined, which is fine for author paths. | `docs/advanced/js-and-css-dependencies.md:24-66` |
| `Dependencies.js` / `.css` URL entries | Author only | Loads and runs | No scheme check on the server. On a Vue page and in fragments the browser runtime refuses a script URL that is not `http:`, `https:`, or `blob:`, or `file:` on a `file:` page (`requireWebAssetUrl`, `citry/_vue/client.js:2882`); a static page writes `<script src>` without checking its scheme. | `docs/advanced/dependency-files.md` ("Add a library URL") |
| `Dependencies` entry with `__html__` (a ready-made tag) | App code | Markup | Inserted raw (`citry/ext/dependencies/emission.py:1113`); refused in fragments, on Vue pages, and with a nonce or Citry SRI. | `docs/advanced/dependency-files.md:266-276` |
| `Script(url=, content=, attrs=)`, `Style(...)` in `Dependencies`, `Component.on_dependencies()`, or the `on_dependencies` hook | App code | Runs / CSS | `content` checked by `_check_validity`; `attrs` names by `validate_html_attr_name`, values escaped. No scheme check; an `on*` key in `attrs` is allowed. | `docs/advanced/dependency-files.md` ("Customize the tag") and the `Script` / `Style` docstrings |
| `serialize(csp_nonce=)`, Events `_csp_nonce` | App code (syntax-checked, so a bad value cannot break out) | Lets scripts run under the CSP | `_validate_csp_nonce` (`citry/serialize.py:1151`, CSP base64 only), then added to every structured tag after the dependency hooks (`citry/_serialization_security.py:497`), the fragment loader, and the Vue data. Tags written in a template never get it. | `docs/security.md:1129-1295` |

## 7. Vue and translated text

### 7.1 Vue

Python values never become Vue template source (section "render paths").
The rows below are about what the template author writes around them.

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| Any Vue directive or binding written in the template (`v-if`, `@click`, `:x`, `v-model`) | Author only | Compiled and run as JavaScript | Compiled from template source (`crates/citry_core_py/src/vue.rs:13`). Python data cannot reach a directive: values are JSON references, Vue-code names from data are refused (2.2), and bindings on component tags must be plain authored text (`citry/nodes/__init__.py:2141-2153`). | `docs/vue/csp.md:80-82` |
| Value bound with `v-html`, `:innerHTML`, `:outerHTML`, or a `.prop` modifier | App code (never request data unless the app sanitized it) | Markup | Passed to Vue unchanged; the HTML the server writes does not contain the value, so the output checks never see it (`vc/server_render.rs:3509-3510`, `:4151`). | `docs/vue/slots.md:147-152`; added by this change: `docs/syntax/vue.md` |
| Value bound with `:srcdoc`, `:href`, `:src`, `:action`, `:formaction` | App code (check the scheme on the server) | Page / navigates / loads | Passed through; the server renderer writes it as escaped text, so the output checks read only the HTML sent to the browser, not a value Vue sets later. | `docs/vue/slots.md:147-152`; added by this change: `docs/syntax/vue.md` |
| Value bound with a lowercase `:onclick` (not `@click`) | Author only; never data | Runs | Vue writes a string as an inline handler; the server renderer leaves every `on*` name to the browser (`vc/server_render.rs:1576`). | `docs/syntax/vue.md` |
| Value bound with `:style` | App code | CSS | Vue applies a style object or string as it is, so a `url()` in it loads a resource. | `docs/syntax/vue.md` |
| Value bound to `<component :is>` | App code (map a request value through your own list) | A component, or a native element of that name | Passed to Vue unchecked; `is` picks the component (`vc/hydration.rs:1430`) and is not compared with the tags `<c-element>` refuses. A string that Vue cannot resolve as a component makes Vue create a native element of that name: the bundled `resolveDynamicComponent` returns the string itself when no component matches (`citry/_vue/vue.js`). Read from the source, not tested in a browser. | `docs/syntax/vue.md` |
| Object `v-bind="obj"` written by the author | Keys: app code. Values: as the key means | Sets attributes, DOM properties, listeners | Passed through; combining it with Python attributes on one element is refused (`citry/_vue/direct_capture.py:3301-3305`). | `docs/vue/slots.md:154-160` |
| Strings in the Vue page data | Request data OK | JSON data | `script_json` (`citry/util/html.py:580`); Rust-written rows use the same escapes (`crates/citry_native_render/src/json.rs:14`). | Internal |

### 7.2 Translated text

Citry treats message text as source code written by the team and its
translators. Placeholder values are typed data.

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| Message text (`messages`, `messages_file`, catalog `.ftl` files) | Author only | Text | Compiled by `crates/citry_i18n`; bidi controls refused; escaped where shown. | `docs/i18n/messages.md:72-76`, `docs/i18n/catalogs.md:73-76` |
| `tr()` result in a template | Message: author. Result: request data OK as text | Text | A plain `str` (`citry/ext/i18n/extension.py:2076`), so `{{ }}` and attribute escaping apply. A `tr()` result in a URL attribute is not scheme-checked (2.3). | `docs/i18n/index.md:65`; `docs/i18n/rich-messages.md:70-77`; `docs/i18n/rich-messages.md:93-101` |
| `I18nService.tr()` / `resolve()` and `I18nExtension.tr()` / `resolve()` in Python | Message: author | Whatever the caller does | Return unescaped text; the caller escapes it if it builds HTML in Python. | docstrings in `citry/ext/i18n/extension.py` |
| Placeholder values (`tr("id", name=value)`, `<c-trans c-values=...>`, `fmt.*`) | Request data OK | Text | `_tag_value` (`citry/ext/i18n/extension.py:2585`) accepts only exact `str`, `int`, finite `Decimal`, aware `datetime` (so not `Markup`). | `docs/i18n/messages.md:76-77` |
| `<c-trans>` text segments and fills | Segments: request data OK (escaped). Fills: author | Text / markup | `make_trans_component` (`citry/ext/i18n/components.py:266`) escapes each segment with `{{ }}` and places each fill as a slot. | `docs/i18n/rich-messages.md:79-91` |
| `I18nExtension.resolve_rich()` segments | The caller escapes | Whatever the caller does | Returns raw segments (`citry/ext/i18n/extension.py:2172`). | Docstring `:2190-2197` ("Nothing in them is escaped") |
| Locale (`make_context(locale=)`, `<c-i18n locale>`), `direction`, `time_zone` | Request data OK | `lang` / `dir` attributes; keys | `_canonical_allowed_locale` (`citry/ext/i18n/extension.py:2296`) allows only configured locales; `direction` is `ltr` or `rtl`; `load_time_zone` (`citry/ext/i18n/timezone.py:20`) reads only bundled tzdata. A cached render re-checks the locale and direction. | `docs/i18n/locale-context.md:73-80` |
| `$c-tr` binding name and values expression | Author only | Picks a message and an allowed attribute; the expression runs | `parse_i18n_binding_name` (`citry/_i18n_directives.py:58`) allows eight text attributes; data cannot add a binding (`citry/ext/i18n/bindings.py:359`); a cached render accepts only expressions a live template wrote (`citry/ext/cache/replay.py:1035`). | `docs/i18n/browser.md:156-158`, `:396-401` |
| Message ids and format profile names in the browser runtime | Author | Keys | Looked up by plain object index (`js/citry-i18n-runtime.ts:448-452`, `:894`, `:990`; `js/citry-i18n-core.ts:224`), so `__proto__` does not fail as an unknown name. Wrong output only, never markup or code: [#701](https://github.com/citry-dev/citry/issues/701). | `docs/i18n/formatting.md:266-267` |

## 8. Events actions

These are values an event handler returns. The fields marked request data
OK are checked by Citry on the server and again in the browser.

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| `Redirect(url=)` | Request data OK for the scheme and the header. App code for the destination (an open redirect is the app's check) | Navigates | `Redirect.__post_init__` (`citry/ext/events/actions.py:375`) refuses controls and any scheme other than `http`/`https`, read the way the WHATWG URL parser reads it (`redirect_url_scheme`, `:316`, which calls the one scheme reader every server-side check shares: `url_scheme` in `crates/citry_html_transform/src/url_scheme.rs`, through `citry/_urls.py`). The resolver for the no-JavaScript form path reads the scheme through the same reader (`_resolve_redirect_url`, `citry/ext/events/routes.py:661`). The browser checks the scheme again (`navigateToRedirect`, `citry/_vue/client.js:163`). Without JavaScript, `_encode_location` (`citry/ext/events/routes.py:783`) leaves only printable ASCII in the `Location` header. | `docs/events/actions.md:250-291`; `docs/security.md:160` |
| `PushUrl(url=)`, `ReplaceUrl(url=)` | Request data OK (the browser refuses another origin). App code for which same-origin path is shown | Changes the address bar | Server checks only a non-empty string (`citry/ext/events/actions.py:416`, `:445`). The browser resolves against the page address (`citry/_vue/client.js:150`) and the History API refuses another origin. Never applied without JavaScript. | `docs/events/actions.md:293-316` |
| `Render(element=, target=, swap=)` | `element`: section 1 rules. `target`, `swap`: request data OK | Markup | `Render.__post_init__` (`citry/ext/events/actions.py:171`) checks `target` with `validate_render_id` or `validate_mark_name` and `swap` against a fixed set; the browser checks again, for server results at `citry/_vue/client.js:3789-3794` and for `applyActions` at `:499-512`. | `docs/events/actions.md:27-125` |
| `Dispatch(name=, detail=)` | `name`: app code (pick it from your own list). `detail`: request data OK as JSON | DOM event fired at the component's first element; it bubbles | Non-empty, not `citry:` (`citry/ext/events/actions.py:296`); `detail` is strict JSON. The browser fires a `CustomEvent` with that name (`citry/_vue/client.js:4226`), so a name such as `click` or `submit` runs every listener for that event on the element and its ancestors, including `@c-*` bindings that call the server. Whether Citry should refuse such names: [#704](https://github.com/citry-dev/citry/issues/704). | `docs/events/actions.md:127-164` |
| `Data(value=)`, a returned `dict` | Request data OK | JSON | Strict JSON (`citry/ext/events/routes.py:467`). | `docs/events/actions.md:166-193` |
| `Download(content=, filename=, content_type=)` | `content`, `filename`: request data OK. `content_type`: app code | Saved as a file | `Download.__post_init__` (`citry/ext/events/actions.py:510`) refuses paths, controls, and bidi characters in `filename`, and anything outside printable ASCII in `content_type`; `_download_content_disposition` (`:543`) writes an `attachment` header. | `docs/events/actions.md:318-348` |
| `RouteResponse` from an `@event(bundle=False)` handler | App code | As its `content_type` says | Sent from the per-event route only (`citry/ext/events/dispatcher.py:1138`); the adapters add `nosniff` and a UTF-8 charset (`citry/util/routing.py:302`, `:318`) but do not check header values for line breaks. | `RouteResponse` docstring (`citry/util/routing.py`) |
| `on_event` hook return (Events extension) | Extension code | As the handler's result | A value other than `None` answers the call in place of the handler (`citry/ext/events/dispatcher.py:1039`) and goes through the same result encoding as a handler return. | Docstrings in `citry/ext/events/extension.py` |
| `on_event_error` hook return (Events extension) | Extension code | Error JSON | Used only when it is a valid error result (`_normalize_error_hook_result`, `citry/ext/events/dispatcher.py:1575`); anything else is ignored. | Docstrings in `citry/ext/events/extension.py` |
| `on_event_result` hook return (experimental) | Extension code | As the action kind | `_validate_hook_actions` (`citry/ext/events/dispatcher.py:1324`) checks the wire shape, not the `Redirect` scheme; the browser still checks the scheme, the no-JavaScript 303 does not. | Experimental |

## 9. Events requests

Requests are data from anyone. Nothing in this section is written to the
page by Citry itself; it is listed because it decides what a handler sees.

| Input | Who may supply it | What Citry does, and where | Docs |
|---|---|---|---|
| Handler name and component class id | Request data OK | Dict lookups only, never `getattr` (`citry/ext/events/routes.py:515`). | `docs/events/routes.md:14-23` |
| Event data, body size, form field count | Request data OK | `decode_request` (`citry/ext/events/codecs.py:293`), schema binding, size and field limits in `_prepare_dispatch` (`citry/ext/events/routes.py:339`). | `docs/security.md:409-472` |
| CSRF | Request data (any site can send one) | `build_csrf_check` (`citry/ext/events/csrf.py:114`). | `docs/security.md:242-407` |
| State token | Request data (opaque, signed) | `verify_state_token` (`citry/ext/events/tokens.py:627`): HMAC-SHA256 with a derived key, constant-time comparison, class binding, expiry. A cached render verifies and re-signs it (`citry/ext/events/cache.py:122-169`). | `docs/security.md:24-96` |
| `stateUpdates` (writes from `$state` and `:c-*`) | Request data OK | `apply_state_updates` (`citry/ext/events/tokens.py:885`): only `_model` fields, typed. | `docs/events/state.md:167-170` |
| Sub-path (ASGI `root_path`, WSGI `SCRIPT_NAME`) | App deployment only; it becomes request data when a proxy passes on a client's `X-Forwarded-Prefix` | `normalize_sub_path` (`citry/_sub_path.py:34`) uses the site root for a value that is not a path starting with one `/`, and percent-encodes the rest, so it stays a path on the same site either way. | `docs/advanced/web-frameworks.md:419-439` |
| `get_event_url(..., query=, fragment=)` | Query and fragment: request data OK | `format_url` (`citry/util/misc.py:175`) encodes them. | `docs/events/routes.md:25-62` |

## 10. Routes and responses

| Route or response | What it serves | Checks, and where | Docs |
|---|---|---|---|
| Every adapter | Any response | Adds `X-Content-Type-Options: nosniff` unless the response sets that header itself, and `charset=utf-8` to a `text/*` string body (`citry/util/routing.py:302`, `:318`). | `docs/advanced/extensions.md:400-404` |
| Events response body and errors | JSON, or `text/plain` without JavaScript | Strict JSON; error text that echoes request values is only sent as `text/plain` or JSON with `nosniff`. Exception text appears only when the `citry` logger is at `DEBUG` (`citry/ext/events/dispatcher.py:448`). A `GET` call answers with `Cache-Control: no-store` (`citry/ext/events/routes.py:810`); a `Download` always does (`citry/ext/events/dispatcher.py:1127`). | `docs/security.md:1104-1116` |
| Runtime files (`citry.<digest>.js`, `ext/events/definitions/<digest>.js`, `ext/events/assets/<digest>.css`, i18n runtime) | Citry's own files | Digest must be 64 hex characters; a shared-cache copy is served only if its hash matches (`citry/_hashed_runtime.py:54`, `:172`; `citry/_vue/events.py:414`). These, and their 404s, carry `Access-Control-Allow-Origin: *` (`citry/_owned_resource.py:19`); hashed files are sent as `immutable`. | `docs/security.md:1707-1745` |
| `cache/<class>.<hash>.{js,css}`, `asset/<file>` | Component files and the `css_data()` stylesheet | Class must be registered; type from a fixed table; content only from Citry's cache (`citry/ext/dependencies/routes.py:111`, `:159`). The `asset/` bytes are not re-hashed when served, so the cache operator is trusted. Successful responses carry `Access-Control-Allow-Origin: *` (`citry/_owned_resource.py:58`, `:66`, `:80`), so any site that has the URL can read a `css_data()` stylesheet; `css_data()` must not return secrets. 404s carry no CORS header. | `docs/security.md:1707-1745` |
| i18n messages route | Message JSON | 64 KiB, exact fields, allowed locales, known public message ids (`citry/ext/i18n/routes.py:79`). | `docs/i18n/browser.md:227-229` |
| Preview routes (experimental) | Component previews | Mounted only by the preview command, loopback `Host` and `Origin` only (`citry/ext/preview/host.py:57-89`). | `docs/advanced/previews.md:109-115` |

## 11. Extension hooks, cache, and debug output

An extension is Python code the app installs, so every hook return is
trusted code. The rows say what Citry still checks, which decides whether
a hook may pass request data through.

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| `on_component_rendered()`, `on_slot_rendered()` return | `str`: request data OK. `Markup`: app code | Text / markup | `_text_or_html_part` (`citry/component_render.py:2877`), the same rule as `{{ }}`, on static, Vue, and Events `Render` paths. Hooks do not run on a cache hit; the stored output replays. | `docs/advanced/extensions.md:115-147` |
| `on_attrs_resolved()` return: names | App code; may not add a code-capable name | Attribute names | `_reject_vue_code_from_attrs_hook` and `_reject_script_capable_from_attrs_hook` (`citry/extension.py:1511`, `:1530`) refuse an added `v-`/`:`/`@`/`on*`/`innerHTML`/`outerHTML`/`srcdoc` name; `validate_html_attr_name` runs on every name (`citry/nodes/__init__.py:1320`, reached from capture at `citry/_vue/capture.py:1079`). | `docs/advanced/extensions.md:165-167` |
| `on_attrs_resolved()` return: values | App code | Attribute text; URLs navigate; an existing `on*` value runs | Escaped; not scheme-checked. A hook may change the value of an `on*` attribute the template wrote. | `docs/advanced/extensions.md:169-173` |
| `on_serialize()` return (the whole page) | Extension's own text only | Markup | Used as it is after a type check (`citry/extension.py:2415`); on a Vue page `finalize` refuses a result that changes or removes the element Vue mounts on (`citry/_vue/serialization.py:626`). The output checks run after it. | `docs/advanced/extensions.md:145-147`; `docs/advanced/extensions.md:151-163` |
| `on_template_loaded()`, `on_template_compiled()`, `on_template_foreign_compiled()`, `on_template_foreign_spans()` return | Author only (the hook acts as the template author) | Markup | Parsed or used as authored template source; type checks only (`citry/extension.py:1461-1470`). | `docs/advanced/extensions.md:151-163`; added by this change: the compile hooks named there |
| `on_js_loaded()`, `on_css_loaded()`, `on_messages_loaded()` return | Author only | Runs / CSS / message text | Used as the component's own `js`, `css`, or messages. | `docs/advanced/extensions.md:151-163`; added by this change: `on_messages_loaded` named there |
| `on_dependencies` hook (`ctx.scripts`, `ctx.styles`) | App code | Runs / CSS | As `Script` / `Style` in section 6. | `docs/advanced/extensions.md` ("Add scripts and styles") |
| `on_component_input()`, `on_component_data()` changes | Request data OK to the same degree as the kwarg or variable it fills | As the template uses it | No hook-specific check; the template rules apply. | Docstrings `citry/extension.py:952-966` |
| `browser_plugin()`, `prepare_browser_render()` (experimental) | Script: app code. `payload`: request data OK as JSON | Runs / JSON | `_validate_plugin` and `_validate_json` (`citry/browser_render.py:280`, `:365`); the payload is written with `script_json`. | Experimental |
| `Extension.urls` route handlers | App code | As its content type says | The adapter adds `nosniff` and a charset; the body is the handler's choice. | `docs/advanced/extensions.md:400-404` |
| A stored render-cache entry | Whoever can write the cache store (trusted like the database) | Markup, scripts, CSS | Decoded strictly (`citry/ext/cache/artifact.py:334`, `:360`, `:423`); template text, raw blocks, Vue bindings, dynamic tags, render ids, and the CSS data are checked against this process's live templates on replay (`citry/ext/cache/replay.py:925`, `:1019-1039`). Trusted HTML parts and template-written attribute text replay as stored. | `docs/performance/caching.md:187-189` ("Protect the cache store like your database"); `docs/security.md:1098-1102` |
| Cache keys (`Component.Cache`, `<c-cache>`) | App code; may include request values | None directly; a wrong key serves one user's HTML to another | Hashed (`citry/ext/cache/keys.py:188`); `Secret` refused as a key part (`:404`). | `docs/performance/caching.md:175-189` |
| `export_render_cache()`, `stage_render_cache()`, `render_cache_bypass_reason()` | App code | Through the extension's own output | `render_cache_mode` defaults to `"deny"`, which skips caching for any render a hook touched (`citry/extension.py:1078`); a stored payload must be strict JSON (`citry/ext/cache/artifact.py:435`). | `docs/advanced/extensions.md:326-359` |
| Hooks whose return does not reach the page: `on_extension_created`, `on_component_class_created`, `on_component_registered`, `on_component_unregistered`, `on_citry_cleared`, `on_template_reset`, `on_render_context_merge`, `on_files_reset`, `on_component_cache_hit`, `validate_config_fields`, `inspect_component`, `inspect_template_namespace` | App code | Nothing from the return value | Return values are ignored or used only for metadata and analysis. Changes these hooks make (to `ctx.parent_context.extra`, or to a component class) reach the page only through the extension's other hooks or the class itself. | Docstrings in `citry/extension.py` |
| `citry.ext.debug.Debug` boxes | App code (config) | Text labels | Labels written as escaped text (`citry/ext/debug.py:47`); debug output is never cached. | `docs/guides/troubleshooting.md:291-311` |

## 12. Settings and the opt-in output checks

| Setting | Who may supply it | What Citry does, and where | Docs |
|---|---|---|---|
| `security_csp` (`off`, `warn`, `strict`) | App code | One Rust scan of the final page, after every hook: `check_output_html` (`crates/citry_html_transform/src/output_policy.rs:188`, via `citry/_output_policy.py:138`). Reports template-written `<script>` and `<style>`, `on*` handlers, and `javascript:` URLs, reading attribute values as the browser does. The scheme is read by the shared reader (`url_scheme_is`, `crates/citry_html_transform/src/url_scheme.rs`), which compares ASCII letters only, as the browser's URL parser does. Off by default, so it is a safety net, not the place a rule is enforced. It does not see what Vue builds in the browser. | `docs/security.md:1297-1396` |
| `security_javascript` (`allow`, `warn`, `omit`, `forbid`) | App code | The same scan with the JavaScript rules: handlers, `javascript:` URLs, embedded documents, encoding-dependent text, and parser differences (`output_policy.rs:323`, `:1407-1515`, `:1638`). Structured `Script` and `Style` dependencies are filtered first (`citry/_javascript_policy.py:91`), reading a `Markup` URL after decoding it as Citry writes it (`_written_attribute_text`, `:503`, from [#697](https://github.com/citry-dev/citry/pull/697)). `javascript:` and `data:` URLs are read by the shared scheme reader (`crates/citry_html_transform/src/url_scheme.rs`). | `docs/security.md:1397-1645` |
| `security_script_integrity` (`off`, `citry`) | App code | Under both values, the tags Citry writes for files it serves carry `integrity` (`citry/ext/dependencies/types.py:134`). `citry` also lists SHA-384 hashes of `Script` objects in `SerializedSecurity` and raises `TypeError` for a ready-made tag (`citry/settings.py:725-732`). | `docs/security.md:1646-1706` |

## 13. Citry UI

Every Citry UI check runs in Python in the component's `template_data()` or
`js_data()`, before the template renders, so static HTML, Vue pages,
Events `Render`, and cached renders all get it. Citry UI templates spread
attribute maps with core `c-bind`, so the core name checks of 2.2 apply on
top of the component's own. No Citry UI component inserts HTML with
`innerHTML`, `v-html`, or `<c-raw>`.

| Input | Who may supply it | Browser | What Citry UI does, and where | Docs |
|---|---|---|---|---|
| Link and form URLs: `CButton(href=)`, `CForm(action=)`, `formaction` in `CButton(attrs=)` and `CSplitButton(primary_attrs=)`, `CListItem`, `CMenuItem`, `CPagination` (the `{page}` template), `CBreadcrumbItem`, `CNavigationMenuLink` `href` | Request data OK | Navigates / submits | `check_link_url` (`ui/components/_url.py:59`) allows a relative URL or `http`, `https`, `mailto`, `sms`, `tel`, reading the scheme the way the WHATWG URL parser does, through the scheme reader every server-side check shares (`citry._urls.url_scheme`, which calls `url_scheme` in `crates/citry_html_transform/src/url_scheme.rs`). The URL name is refused inside the matching attribute map, so a map cannot get around it (for example `ui/components/cbutton/cbutton.py:121-140`). The check reads the text the page gets, after Citry decodes a `Markup` value's character references. | Each component's `api.yml` `href` / `action` row |
| Image URLs: `CAvatar(src=)`, `CImage(src=, srcset=, sources=)` | Request data OK | Loads an image | `check_image_url` (`ui/components/_url.py:95`) allows a relative URL, `http`, `https`, `blob`, and `data:image/`, reading the scheme through the shared reader (`citry._urls.url_scheme_and_rest`); every `srcset` candidate is checked (`ui/components/cimage/cimage.py:229-238`). The browser code repeats the rule for client props. | `ui/components/cavatar/api.yml:13`, `ui/components/cimage/api.md:130-135` |
| `attrs=` and every `*_attrs=` argument: names | App code | Attribute names | Three layers: the component refuses names it sets itself (`reject_owned_attrs`, `ui/components/_validation.py:47`), Vue directive names are refused (`reject_vue_directive_attrs`, `ui/components/_attrs.py:90`), and core `c-bind` refuses `on*`, `innerHTML`, `outerHTML`, `srcdoc` (2.2). A request-chosen name can still set `style`, `id`, `name`, `form`, `target`, or `ping` where the component does not own it. | `docs/ui-library/index.md` ("Pass request data safely") |
| `attrs=` values | Request data OK as text, except `style` and URL names | Attribute text | Escaped by core `format_attrs`. | As above |
| `style=` and `style` in an attribute map | App code | CSS | `merge_root_attrs` (`ui/components/_attrs.py:138`) hands it to core `merge_attrs` and `normalize_style`, with no CSS check. | `docs/ui-library/index.md` |
| Tag inputs: `CCard`, `CRow` and `CCol` (in `cflow.py`), `CContainer`, `CGrid`, `CGridItem`, `CSidebar` `tag=`, and `heading_level` (`h2` to `h6`) | Request data OK | Tag | A fixed list per component (for example `ui/components/ccard/ccard.py:121`, `ui/components/cflow/cflow.py:105`), then the core `<c-element>` check (section 3). No Citry UI component takes a free tag name. | Each `api.yml` `tag` row |
| Values Citry UI writes into CSS: `CColorPicker(value=)`, `CGrid(min_col=)`, `CImage(position=, fit=)`, numeric sizes | Request data OK | CSS | Checked before use: a hex color pattern (`ui/components/ccolor_picker/ccolor_picker.py:29`), one CSS length (`ui/components/cgrid/cgrid.py:59`), `position` without `; { } \` or controls (`ui/components/cimage/cimage.py:499-502`), numbers as `int` or `Decimal`. | Each `api.yml` row |
| Text inputs (labels, descriptions, option labels, table cells) | Request data OK as `str`. `Markup` or a component: app code | Text / markup | Printed with `{{ }}`. Many components copy a `Markup` value to a plain string first, so it prints as text; the others follow the core `Markup` rule (`ui/components/ctable/ctable.py:626`). | `ui/components/ctable/api.md:73-74` |
| `id=` and `name=` arguments | App code | Element `id` and form control `name` | `validate_html_id` refuses only whitespace; the value is escaped. A data-chosen control `name` can hide a form method that Citry's browser code calls ([#703](https://github.com/citry-dev/citry/issues/703)). | None |
| `CIcon(name=)` and icon names | Request data OK | Packaged SVG | Looked up in the packaged registry; `Markup` refused in every input (`ui/components/cicon/cicon.py:137`, `:160`). | `ui/components/cicon/api.md:139-142` |

## 14. Citry's browser runtime

Citry's browser code (`citry/_vue/client.js`, built in part from `js/`)
takes names and data from the server's JSON and from page code. The rule it
follows is that a name such as `__proto__` reaches only its own entry, and
that an element `id` or `name` chosen by data cannot replace what the code
reads from `window`, `document`, or a form.

| Input | Who may supply it | Browser | What Citry does, and where | Docs |
|---|---|---|---|---|
| App ids, render ids, component instance ids, mark names, State field names, extension names, transport names, locale names | Request data OK | Keys | Kept in `Map`s or in objects with no prototype, read through `own()` (`citry/_vue/client.js:186`, `:1434`, `:1601-1645`; `js/citry-i18n-runtime.ts:1107`). Targets from page code must match `/^[a-z0-9_-]+$/` or the mark-name pattern (`citry/_vue/client.js:420`, `:450`). The runtime never reads these names from the page's markup, so a marker name written by data does not change a lookup. The exception is the i18n runtime, which looks up format profile names and message ids by plain index, so `__proto__` gives wrong output instead of an error: [#701](https://github.com/citry-dev/citry/issues/701). | Internal |
| Definition ids and component type keys | Server JSON only | Keys | Plain objects (`window.__citryRuntimeDefinitions`, `componentTypes`), but filled only from Citry's own output; an id such as `constructor` fails when registered (`citry/_vue/client.js:1461`). | Internal |
| `window`, `document`, and form members | Element `id` and `name` in the page may be data | Reads | `ownGlobal`, `pageDocument`, and `callBuiltIn` (`citry/_vue/client.js:15`, `:32-37`, `:44-84`) read past named elements. A few calls on a form that is a component root or carries server-event listeners still read the member directly, so a control with a matching name breaks the binding (no code runs): [#703](https://github.com/citry-dev/citry/issues/703). | Internal |
| Document data block (`data-citry-vue-document`) | Server only | JSON that drives every script load | `startDocument` (`citry/_vue/client.js:5740`) needs exactly one block and, on a page with a nonce, the page's nonce (`:5720-5724`). | `docs/security.md:1289-1295` |
| Vue fragment data block (`data-citry-vue-fragment`) | Server only | Starts a Vue app when it enters the page | Refused without the page's nonce on a page with one (`js/citry-fragments.ts:112-135`); on a page without a nonce every block starts. | `docs/security.md:1274-1285` |
| Definition and asset scripts named in a manifest | Server only | Loaded as `<script>` | `requireWebAssetUrl` (`citry/_vue/client.js:2882`) allows `http`, `https`, `blob` (and `file` when the page itself is a `file:` page); Citry-served files carry SRI from their digest (`:2807`). Script URLs resolve against `document.baseURI`, so a `<base>` tag moves them. | `docs/security.md:1190-1217` |
| `Citry.events.applyActions(actions)` | Page code, with result data from the app's own server | Applies redirects, URL changes, events, State, and renders | Checked like a server result (`assertPublicActionList`, `citry/_vue/client.js:478-544`); a `render` action for a Vue component can name scripts that load with the page's nonce, so the actions must come from the app's own server. | `docs/reference/browser-apis.md` |
| `Citry.fragments.load(manifest)` called without a tag | Page code | Starts a Vue app | Skips the nonce check (`js/citry-fragments.ts:134`). Not documented as a public API. | None (not public) |
| An Events `Render` result sent as an HTML fragment (`html-fragment/1`) | Server | Not inserted by the runtime | The runtime refuses it (`citry/_vue/client.js:3789`); only the no-JavaScript response serves it, as `text/html`. | Internal |

## Open questions

Each row is a case where the code does not yet follow the rule "data must
not choose code or Citry's own markers" (Mechanism 7), or where the trust
level is not settled. None of them lets request data run script
as far as the review found.

| Question | Issue |
|---|---|
| A `c-bind` key can write Citry's marker names (`c-render-id`, `data-cid-*`, `data-ccss-*`, `data-citry-*`). A data-chosen `c-render-id` on an empty `<template>` makes the server copy another component's HTML there. | [#699](https://github.com/citry-dev/citry/issues/699) |
| `format_attrs()` checks name syntax only, so Python code that builds a tag with it must choose the names. Should it refuse the names `c-bind` refuses? | [#700](https://github.com/citry-dev/citry/issues/700) |
| The browser i18n runtime finds `__proto__` as a format profile or message id instead of failing. | [#701](https://github.com/citry-dev/citry/issues/701) |
| On the node path (foreign-span templates only), a nested-template attribute value may not be escaped as attribute text. Not proven either way. | [#702](https://github.com/citry-dev/citry/issues/702) |
| Core Citry checks no URL scheme. Should it? | [#601](https://github.com/citry-dev/citry/issues/601) |
| `Dispatch(name=)` fires a DOM event that bubbles, so a name such as `click` runs the page's own listeners. Should Citry refuse standard event names? | [#704](https://github.com/citry-dev/citry/issues/704) |
| A form control named after a DOM method (`addEventListener`, `contains`) can break a server-event binding on that form. | [#703](https://github.com/citry-dev/citry/issues/703) |
| Should Citry allow a template-written `onclick` on `<c-element>` with `c-is` or `c-bind`? It is refused. | [#605](https://github.com/citry-dev/citry/issues/605) |

## Keeping this doc accurate

- A pull request that adds or changes an input in these tables changes its
  row in the same pull request. The Mechanism 7 security pass checks that
  the row matches the code.
- **How a missing row is caught.** The validator
  [`scripts/validators/trust_boundary_rows.py`](../../scripts/validators/trust_boundary_rows.py)
  reads every public method of `Extension`, every hook an extension fires
  by name (the string passed to `.emit(...)` or `_extensions_with_hook(...)`
  in the `citry` package, such as `on_event`), every Events action in
  `citry.ext.events.actions.__all__`, and every `security_*` setting from
  the source, and fails when this doc does not name one in a code span. It
  runs in the `validators` phase of `scripts/check.py`, in both the fast
  and the full profile, and takes about half a second, because it parses
  the package's Python files without importing them. A name counts when
  it opens a code span, so the check proves the doc mentions each input,
  not that the row is right; the security pass checks that. It covers the inputs that are easiest to add without
  thinking of this doc; new template syntax and new keyword arguments are
  still caught only by the security pass. The check does not cover every
  public function that returns `Markup`: most such functions are already
  rows here, and that list would need hand-kept exceptions that cost more
  to keep current than they catch.
