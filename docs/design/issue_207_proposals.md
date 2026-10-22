# Issue #207: proposals that need your decision

The error-prevention benchmark writes the same developer mistakes in Citry and in other frameworks, and records when each framework first reports them. Issue #207 lists the mistakes Citry misses or reports only when the page runs. This document covers every part of that list that needs your approval before anyone builds it.

The simple rules (the "A batch": misspelled attributes and elements, `v-iff`, Vue expression syntax, `<div>` inside `<p>`, missing `alt`, ARIA names, duplicate ids, `disabled="false"`, `v-model` targets, and the server event checks that run when `citry check` loads the app) are being built separately. They are not repeated here.

An independent reviewer checked the research behind this document, including a separate prose pass. Its corrections are folded in.

## Words used in this document

- **Ids such as m19 and m52** are the benchmark's ids, one per mistake. "Issue comment 1" is a mistake raised in the first comment on #207.
- **A slip** is one typing mistake: two neighbouring letters swapped (`titel` for `title`), one letter doubled (`iff` for `if`), or one letter dropped (`clik` for `click`). The existing helper `_is_directive_typo` (`packages/py/citry/citry/analysis.py:1616`) tests for exactly these.
- **A notice** is a message from `citry check` and the editor that never fails the check. Discovery already uses notices for templates it cannot read.
- **citry-lsp** is Citry's editor language server.
- **The app worker** is the separate process citry-lsp starts to import the user's app, so the editor never runs project code in its own process.
- **The handler description** is the record citry sends to citry-lsp for each server event handler. It is built in `ext/events/_introspection.py:56-104` and also returned by `Citry.inspect_components`.
- **The TypeScript check file** is the JavaScript file citry-lsp generates from a template so that tsc can type-check its Vue expressions (`type_check_projections` in `citry_lsp/engine.py`).
- **The ty check file** is the Python file citry generates from a template so that ty can type-check its Python expressions (`_template_python.py`).
- **vize** is the Rust Vue compiler Citry uses to compile Vue templates when a page renders (`crates/citry_vue_compiler`).
- **The PyO3 surface** is the set of Rust functions and classes `citry_core` exposes to Python. Changing it needs a citry-core release and the written plan that CLAUDE.md requires (Mechanism 2).

## Decision summary

Ordered by value to a Citry user. A "plain fix" is a bug fix you can approve without a design.

| # | Proposal | Mistakes | Recommendation | Decision needed |
|---|---|---|---|---|
| 1 | Find components whose base class is in another module | issue comment 1 | Option 1 now, then 2 | Option 2: yes/no. Option 3: yes/no/defer |
| 2 | Run Vue's compiler over every template in `citry check` | m52, m19, m63, more | Option 1 (one shared converter) | Choose 1, 2 or 3 |
| 3 | Server event payload checks in the editor | m18, m32, m33 | Option 1 (new key in the handler description) | Add the key: yes/no. Name `extra_fields`: yes, or give another |
| 4 | Form field names against the event's data class | m44 | 4a Option 1 (doc fix); 4b Option 1 | 4a: choose 1, 2 or 3. 4b: choose 1, 2 or 3 |
| 5 | Typed slot data in the editor and `--types` | m36, m37 | Option 1 | yes/no |
| 6 | Links to routes and static files | m45, m61, m48 | Option 3 for files, Option 1 for routes | Option 3: yes/no. Option 1: yes/no |
| 7 | Type prop values written as expressions | m27 (beyond literals) | Option 1 for props; defer payloads | Option 1 for props: yes/no |
| 8 | Emit payload types and handler arguments | m30, m60 | Options 1 and 2 | yes/no |
| 9 | Exact error text for Vue syntax errors; exact prop-write check | m19, m28 | Option 2 (new PyO3 function, existing ones unchanged) | PyO3 addition in the next citry-core release: yes/no |
| 10 | Let the `v-iff` rule skip directives a component declares | m21 | Option 3 now, Option 1 with item 9 | Option 1 later: yes/no |
| 11 | Secrets and server-only values sent to the browser | m42 | Option 2 (a marker type) + docs | New public `citry.Secret`: yes/no. Option 1 off by default: yes/no |
| 12 | Clearer runtime errors and development-only checks | m51, m63, m14, m57 | Plain fixes for m51 and m63; Option 1 for m14; m57 your call | 12a, 12b, 12c: yes/no each. 12d: yes/no/defer |
| 13 | Misspelled CSS class | m16 | Defer | Off-by-default rule now, or defer |
| 14 | Side bugs found while tracing | - | See each | 14a, 14b: choose 1 or 2. 14c: yes/no |
| 15 | A shared value read under a key no ancestor provides | m50 | Option 2, falling back to Option 1 | Choose 1, 2 or 3; warning or error |

## 1. Components whose base class lives in another module

<details>
<summary>Details</summary>

**What the developer sees today.** A project puts a shared base class in its own module, and every component that inherits it loses its template checks with no message:

```python
# app/base.py
class AppComponent(Component): ...

# app/card.py
from app.base import AppComponent

class Card(AppComponent):
    template = """<p>{{ titel }}</p>"""  # nothing reported
```

`citry check --app` still reports template-variable mistakes, because it uses the loaded app's list of components. But the editor, `citry check --static` and the ty part of `citry check --types` find templates only by reading the source. They accept a class only when its base is `Component` or `LibraryComponent` imported from citry, or a component class in the same file (`analysis.py:4800`, and the fallback pattern at `analysis.py:4890`). One research agent found that `--types` loses its ty findings for such a template; the reviewer did not re-run that experiment.

**Options.**

1. **Report a notice.** When a class has a literal `template = """..."""` and a base class that cannot be traced, add a notice ("Card's base class comes from another module, so its template is not checked").
   - Cost: small.
   - Error mode: a class that is not a component but has a `template` attribute gets a notice it does not need. A notice does not fail `citry check`, so the cost is noise only.
2. **Use the loaded app's list of components.** When the app is loaded, read each component's `owner_file` and `owner_qualname` from the component records and accept those classes in that file.
   - Cost: small to medium. It fixes the editor and `--types`, not `--static`.
   - Error modes:
     - The app fails to import: fall back to Option 1's notice.
     - The file was edited since the app loaded: a new class is missed until the app reloads. A renamed class is skipped when its name is no longer found in the file.
3. **Follow the project's imports.** Resolve `from app.base import AppComponent` to the project file and read its class.
   - Cost: medium. It also helps `--static`.
   - Error modes:
     - An import loop or a deep chain: stop at a depth limit and fall back to the notice.
     - A third-party or dynamic import: treat as unknown, fall back to the notice.
     - A `src/` layout: needs the project's source folders, read from `pyproject.toml`; without them, fall back to the notice.

**Who owns it:** static discovery in `analysis.py`, shared by `citry check` and citry-lsp.

**Recommendation:** Option 1 now. It needs no approval, so it can join the A batch. Then Option 2. Option 3 only if `--static` users ask.

**Decision:** Option 2: yes/no. Option 3: yes/no/defer.

</details>

## 2. Run Vue's compiler over every template in `citry check`

<details>
<summary>Details</summary>

**What the developer sees today.** A template that Vue cannot compile passes `citry check` and fails when the page renders:

```citry-html
<table>
  <div>Row</div>
</table>
```

The page fails with a server error from vize, or the browser moves the element somewhere else. The same happens for a `<button>` inside a `<button>`, a `<form>` inside a `<form>`, and a `v-else` with no `v-if` before it. The A batch catches two mistakes that Vue also rejects with dedicated rules (m19, Vue expression syntax, and m52, `<div>` inside `<p>`), but not the rest.

**What exists.** Python can already call vize through `_rust.vue._compile_vue` (`crates/citry_core_py/src/vue.rs:11-38`), and it returns errors with positions. A throwaway prototype of about 90 lines turned each authored template into a Vue template:
- Python output (`{{ }}`) became placeholders;
- `c-*` attributes were dropped;
- `c-if` and `c-for` were unwrapped;
- component tags were renamed;
- `c-fill` became `<template v-slot>`.

The compiler then reported m19 and m52 at the right place, plus the cases above. It checked 4,547 templates in 3.5 s and made 9 false reports, all caused by the crude conversion.

**Options.**

1. **One shared converter.** Pull the code that builds the Vue template at render time (`_vue/direct_capture.py`) into a function that both the runtime and `citry check` call.
   - Cost: high. It changes runtime code, but needs no PyO3 change.
   - Benefit: the check and the runtime cannot drift apart.
2. **A separate converter for `citry check`,** plus a test that runs both converters on a fixed set of templates and compares the results.
   - Cost: medium.
   - Risk: a difference outside the test set goes unnoticed.
3. **Stop at the A rules.** No cost; the other compile failures stay runtime-only.

**Error modes for Options 1 and 2:**
- The converter cannot handle a template (an extension rewrote it, `c-element` with `c-bind`, a dynamic component): skip it and add a notice. Never report a guess.
- A compiler message has no position, such as `MODEL_HELPER_MISMATCH`: drop it and leave that mistake to its dedicated rule.
- The compiler's positions point into the converted template. Map them back to the authored template through the converter's position map, and drop any finding that cannot be mapped.
- The converter must turn `c-if` and `c-else` branches into `<template v-if>` and `<template v-else>`. Otherwise two branches that never render together look like duplicates.
- The converter must mark component calls as components. Otherwise `v-model` on a component is reported falsely.

**Who owns it:** the `citry check` analyzer, shared with citry-lsp. Proposed code: `citry.vue.template-invalid`, error, carrying the compiler's message.

**Recommendation:** Option 1. Once it exists, it is the single check for "Vue would reject this template", and the A rules for m19 and m52 keep their more specific messages.

**Decision:** choose 1, 2 or 3.

</details>

## 3. Server event payload checks in the editor

<details>
<summary>Details</summary>

**What the developer sees today.** A misspelled or missing payload field passes every check. The server rejects the call with a 422 result inside a successful (200) response, and the page silently does not update:

```citry-html
<button @c-click="save({amont: 1})">Add</button>
```

```python
class SaveIn:
    amount: int

class Events:
    def save(self, data: SaveIn): ...
```

The A batch adds these checks to `citry check` when it loads the app: unknown field (m18), literal of the wrong type (m32), and missing required field (m33). That part already has the real class (`EventHandler.data_schema`, `ext/events/extension.py:126`). The editor does not.

**Why the editor part needs your approval.**
- The editor gets each handler's fields from the handler description. It lists each field and whether it is required, but not whether the data class is a Pydantic model.
- A Pydantic model with default settings ignores unknown keys and turns `"1"` into `1` (`ext/events/schemas.py:311-327`), so the unknown-field and type rules must skip it.
- The handler description is a public contract: `docs/design/events.md` §9.1 says each handler object "always contains exactly these keys", and `Citry.inspect_components` returns it.
- `citry check --static` cannot run these rules at all, because it does not load the app.

**Options.**

1. **Add one key to the handler description,** for example `extra_fields: "reject" | "ignore"`. A plain class or dataclass gets `"reject"`. A Pydantic model gets `"reject"` only when its `model_config` sets `extra="forbid"`, otherwise `"ignore"`. The type rule also skips Pydantic models.
   - Cost: small to medium. It needs:
     - the `events.md` §9.1 update and the introspection tests;
     - citry-lsp reading `request_schema`, which no code in `citry_lsp` reads today;
     - handling an older citry in the user's app environment.
   - The contract stays at version 1, per the pre-1.0 rule in CLAUDE.md.
   - Error modes: a missing key (older citry) or an unknown value means the editor skips the unknown-field and type rules. It keeps the missing-required rule, which holds for Pydantic too.
2. **Reuse the existing `namespace_policy`** (`introspection.py:485`, set by `_schema_namespace_policy` at `_schema_introspection.py:165`). It already says whether a schema accepts extra names, but it labels a default Pydantic model "closed", which is wrong here. Fixing it changes every other user of that value.
3. **Keep these checks out of the editor.** No cost. Editor users see the mistake only when CI runs `citry check`.

**One rule for all options.** A template shared by several components reads the handlers of all of them (`_checker.py:791`). The rules report a field only when every owner's data class agrees, and skip the template otherwise.

**Who owns it:** the events extension (handler description) and citry-lsp.

**Recommendation:** Option 1.

**Decision:** add the key: yes/no. If yes, name it `extra_fields`, or give another name.

</details>

## 4. Form field names against the event's data class

<details>
<summary>Details</summary>

**What the developer sees today.** A form submits to a server event, and one control's `name` is misspelled. The server rejects the call with a 422 that the page does not show:

```citry-html
<form @c-submit.prevent="search">
  <input name="qeury" />
</form>
```

```python
class SearchIn:
    q: str
```

The rule itself is simple. Inside a `<form>` whose `@c-submit` call has no arguments, compare the static `name` of each `input`, `select` and `textarea` with the data class:
- An unknown name is always an error.
- A missing required field is reported only when the form is fully static: no `:name`, no component tags or slots, no `v-for`, and no `id` that a control outside the form could point at.
- Disabled controls and controls with `form="other"` are skipped.

`@c-submit="search()"` counts as "no arguments", because the browser collects the form's fields whenever the call has none (`_vue/client.js:3686-3696`).

**Two decisions block it.**

**Decision 4a: the CSRF hidden input.** `docs/design/security_csrf.md` §4.2 and §4.3 tell Django users to put `<input type="hidden" name="csrfmiddlewaretoken">` in the page, and say "the same hidden input can serve both native forms and the token function". If that input sits inside a form with `@c-submit`, the browser sends it as a field, and the server rejects the call as an unknown field, with or without JavaScript. That is a live bug today, separate from the new rule.

1. **Fix the docs:** tell users to place the hidden input outside any form that submits to a server event. The new rule then reports the input with a hint naming this fix.
   - Cost: a doc change (plain fix).
   - Error mode: none at runtime. Existing pages keep failing until they move the input, and the rule now tells them.
2. **The server ignores host CSRF field names** listed in a new setting (default: `csrfmiddlewaretoken`).
   - Cost: a new setting and a change to the events runtime.
   - Error mode: a data class that really declares a field with that name still receives it.
3. **The browser skips hidden inputs named in that setting** when it collects form fields.
   - Cost: the same, but in the browser code.
   - Error mode: a data class that really declares a field with that name never receives it from a form.

**Recommendation:** Option 1 now. Option 2 only if users ask to keep the input inside forms.

**Decision 4b: text values for number fields.** A form posted without JavaScript converts text to numbers and booleans (`FormCodec` in `ext/events/codecs.py` builds the args as `StringArgs`, defined in `schemas.py`). The same form submitted through Citry's browser code is checked as strict JSON (`schemas.py`). So a text input for an `int` field works without JavaScript and fails with it; only `type=number` and `type=range` inputs send numbers. `events.md` §5.1 promised that "the JS path and the no-JS path deliver the same call"; the 14b doc fix replaced that sentence with a description of the difference.

1. **The browser marks a payload it collected from a form,** and the server applies the form conversion rules to it.
   - Cost: a new flag in the events wire protocol (`citry-events/1`, changed in place before 1.0): its spec, schema, and JS and Python code under `packages/protocol/events/v1`.
   - Error mode: a missing flag (older browser code) keeps today's strict behaviour.
2. **Document the difference,** and have the form rule report a text input bound to an `int`, `float` or `bool` field.
   - Cost: small.
3. **Leave it.**

**Recommendation:** Option 1, because it keeps the promise in the design, and a form should not behave differently depending on whether JavaScript loaded.

**Decision:** 4a: choose 1, 2 or 3. 4b: choose 1, 2 or 3. The form rule can then join the A batch.

</details>

## 5. Typed slot data in the editor and `--types`

<details>
<summary>Details</summary>

**What the developer sees today.** A fill reads slot data under a wrong name, or uses it as the wrong type, and the page fails only when it renders:

```citry-html
<c-fill name="footer" data="card">
  Open {{ card.titel }}
</c-fill>
```

```python
class FooterData:
    title: str
    count: int

class Slots:
    footer: SlotInput[FooterData]
```

The parser checks field names only when the fill unpacks them (`data="{ title, count }"`). The ty check file declares a fill's name as `card: __citry_Any = None` (`_template_python.py:1164-1166`), so ty cannot report anything about it.

**Options.**

1. **Declare the name with a generated class.**
   - The app worker also sends each slot's `SlotInput[T]` fields.
   - `TemplatePythonControl` records which tag and slot introduced the name.
   - The ty check file declares `card` as a generated `Mapping[str, Any]` subclass carrying `T`'s fields.
   - This reuses the code that already types a child's `Kwargs` across files (`_wire_classes.py:104`, `engine.py:4925`).
   - One research agent's test with ty 0.0.89 reports `.titel` and `count + " tasks"`, and stays silent on `card["aria-label"]`, `len(card)` and `**card`. The full editor path is not proven, and the reviewer did not re-run the test.
   - Cost: small to medium. It changes the message between citry and citry-lsp (still version 1) and adds a public field to `citry.analysis.TemplatePythonControl`.
2. **Declare the name as `T` itself.** Simpler, but wrong: at runtime the fill receives `SlotData`, a mapping with attribute access (`slots.py:52`), so `card["x"]` and `**card` would be reported falsely.
3. **Leave it.** No cost.

**Error modes for Option 1:** in each of these cases the name stays `Any`, so nothing is reported:
- a dynamic slot name, or a fill inside `<c-component is=...>`;
- `T` cannot be resolved in the app worker;
- an older citry in the app environment sends no slot fields.

**Limits of Option 1:**
- It covers `--types` and the editor only. Plain `citry check` keeps missing m36, because it does not run ty.
- It trusts the child's declaration, because the runtime never checks what `<c-slot c-title=...>` passes against `T`.

**Who owns it:** the ty check file (citry) and the app worker message (citry and citry-lsp together).

**Recommendation:** Option 1.

**Decision:** yes/no.

</details>

## 6. Links to routes and static files

<details>
<summary>Details</summary>

**What the developer sees today.** A misspelled link, a wrong route parameter, or a misspelled file path shows up only as a 404 in the browser:

```citry-html
<a href="/abuot">About</a>
<a href="/projects/alpha">Project</a>  {# route needs a number #}
<img src="/static/avtar.svg" alt="" />
```

Citry has no list of the host app's routes and no static-folder setting. `Citry(dirs=...)` lists component folders. `URLRoute` (`util/routing.py:156`) covers only Citry's own endpoints. In the benchmark, both routes and static files are hand-written in `main.py`.

**Options.**

1. **Each framework integration registers a route checker.** The Flask and FastAPI integrations receive the host app in `mount()` (`contrib/flask.py:36`, `contrib/fastapi.py:33`); the Django one returns URL patterns (`contrib/django.py:132`), and Django's own lookups work without the app object. Each registers a function that `citry check` calls with every literal `href` and `src` path: Flask `url_map.bind().match`, Starlette route matching, Django `resolve()` and `finders.find()`.
   - Cost: medium; one adapter per framework. Off until the project turns it on.
   - Error modes:
     - A URL with a scheme, a leading `//`, or written as an expression: skipped.
     - The query string and fragment are removed before matching.
     - The adapter raises: drop the finding and add one notice naming the error.
     - `citry check` loads the app without running `mount()`, so no checker is registered: links are skipped and one notice says so.
     - A path served by a proxy, not the app: reported falsely, which is why this is an opt-in warning.
2. **A `url()` template helper that the integration resolves.** Route names and parameters are typed, like Next.js `typedRoutes`.
   - Cost: high; users must change how they write links.
   - Error mode: an unknown route name or parameter is an error at check time and at render.
3. **A declared static folder,** for example `Citry(static={"/static/": PROJECT_ROOT / "static"})`. `citry check` tests that each literal path under a prefix names an existing file.
   - Cost: small.
   - Error modes:
     - A folder that does not exist, or two overlapping prefixes: rejected when `Citry(...)` is built.
     - A path under a prefix that names no file, or that leaves the folder through `..`: an error.
     - Paths outside every prefix: skipped.
     - `--static` and an editor without the app loaded: the check does not run.

**Who owns it:** `citry check` with the app loaded (Options 1 and 3), plus the framework integrations (Option 1).

**Recommendation:** Option 3 for files (m48), as an error once declared. Option 1 for routes (m45, m61), as an opt-in warning. Each is a new public setting and needs a short design doc.

**Decision:** Option 3: yes/no. Option 1: yes/no.

</details>

## 7. Type prop values written as expressions

<details>
<summary>Details</summary>

**What the developer sees today.** A component prop declared as Boolean gets a string through an expression, and nothing reports it:

```citry-html
<c-Status :open="count > 0 ? 'open' : 'closed'" />
```

The A batch fixes two simpler cases: a Boolean prop that accepts any string (`_browser_expressions.py:491`), and a conditional whose two branches are literals. Any other expression is still unchecked, because the TypeScript check file writes a prop value on a component tag as `void (expr)` (`engine.py:2167-2169`), so the child's prop types never apply.

**Options.**

1. **Type each prop in the TypeScript check file** from the child's `$component({props})` source, the way the child's `emits` are already typed (`engine.py:2426`). A Boolean prop becomes `boolean | '' | '<prop-name>'`, matching how Vue converts strings.
   - Cost: medium. Runs only in `--types` and the editor.
   - Error modes: a prop with no readable type becomes `any`. A child whose source cannot be read leaves every prop `any`.
2. **Extend the Python checker** to more expression shapes, such as comparisons and arithmetic. Cheap per shape, but the list of shapes never ends.
3. **Leave it** after the A fixes.

The same question exists for server event payloads written as expressions (`save({amount: count})`). There, Option 1 needs a new converter from Python type annotations to TypeScript types, and TypeScript cannot tell `int` from `float`. I recommend deferring payload expressions until users report them.

**Who owns it:** the TypeScript check file in citry-lsp.

**Recommendation:** Option 1 for props; defer payload expressions.

**Decision:** Option 1 for props: yes/no.

</details>

## 8. Emit payload types and handler arguments

**What the developer sees today.** The parent's handler receives a number where it expected a title, or `reason` is `undefined`, and nothing reports either mistake:

```javascript
// child: sends the count where the parent expects a title
this.$emit('hide', count);

// parent: expects two arguments, but the child sends one
hideCard(title, reason) { ... }
```

With the array form `emits: ['hide']`, the payload type is `any[]` (`engine.py:9612`). With typed object emits, `--types` already reports the wrong payload (`ts2345`):

```javascript
emits: { hide: (/** @type {string} */ title) => true },
```

**Options.**

1. **Document typed emits** in the props-and-events guide, since they already work.
   - Cost: a docs change.
2. **Type a bare method handler on a component tag as a callback,** so tsc compares `hideCard`'s parameters with the emit's payload. Today only inline function handlers are typed.
   - Cost: medium.
   - Error modes: a method not found in the parent's source is skipped. A method without JSDoc has optional `any` parameters, so nothing is reported for it.
3. **Count arguments at the child's `$emit` calls.** Rejected: default parameters, `arguments`, and several emit sites make it wrong too often.

**Who owns it:** docs, and the TypeScript check file in citry-lsp.

**Recommendation:** Options 1 and 2.

**Decision:** yes/no.

## 9. Exact error text for Vue syntax errors, and an exact prop-write check

**What the developer sees today, once the A batch lands:**
- A Vue expression with a syntax error is underlined as a whole, with a generic message ("not valid JavaScript").
- A child that assigns a prop it received is found by reading the characters after the name, which is approximate.

Both limits exist because `analyze_browser_source` (`crates/citry_core_py/src/template_parser.rs:139`) returns only "valid or not" and a list of names. It does not return the parser's error text or position, and it does not say whether a name is written or only read.

**Options.**

1. **Change the return value** of `analyze_browser_source` to add the error and a write flag per name.
   - Cost: a PyO3 change, so a citry-core release, the `_rust.pyi` stub, and a matching `citry-core==` pin in citry.
   - Error mode: every caller must move at once.
2. **Add a new function,** for example `browser_source_diagnostics(source, mode)`, returning the error (message, start, end) and the written names. Existing callers stay as they are.
   - Cost: the same release coupling, but no change for existing callers.
   - Error mode: with an older citry-core that lacks the function, citry falls back to today's generic message and text-based check.
3. **Keep the generic message and the approximate check.** No cost.

**Who owns it:** the Rust browser analysis in `citry_template_parser` and the PyO3 glue in `citry_core_py`.

**Recommendation:** Option 2, in the next citry-core release, together with item 10.

**Decision:** PyO3 addition in the next citry-core release: yes/no.

## 10. Let the `v-iff` rule skip directives a component declares

**What the developer sees today, once the A batch lands:** `v-iff` is reported as a misspelled `v-if`. A component that really declares a directive named `iff` in `$component({directives: {iff}})` gets the same report, and has to turn the rule off.

No code reads `$component({directives})` today. The Rust analysis reads only props, methods, computed, inject, data and setup (`crates/citry_template_parser/src/browser.rs:591`). Directives registered through `Citry.vue.use(plugin)` are arbitrary JavaScript and cannot be seen at all.

**Options.**

1. **Read the `directives` option** in the Rust analysis and return the names through PyO3.
   - Cost: a PyO3 change (Mechanism 2), bundled with item 9.
   - Error mode: an option written in a form the analysis cannot read gives no names, so the rule reports as it does today.
2. **Find the names in Python with a text pattern.** Fragile, and it misses computed keys.
3. **Do not skip.** A component author sets `rule_misspelled_directive = "ignore"` in that component's `Lint` class. A declared directive one slip from a built-in name is rare.

**Recommendation:** Option 3 now; Option 1 when item 9 ships.

**Decision:** Option 1 later: yes/no.

## 11. Secrets and server-only values sent to the browser

**What the developer sees today.** A value returned from `js_data()` is sent to the browser, even if it is a secret, and nothing warns:

```python
def js_data(self, kwargs, slots):
    return {"apiBase": API_BASE, "secretToken": SECRET_TOKEN}
```

No framework in the benchmark catches this. Issue #207 also lists "sending a server-only value to the browser through `js_data()`" as a near-miss; it is the same mistake, and this item covers it. Reading such a value in Vue code without sending it is already caught (m12). Citry has no notion of a secret value: a search for secret, sensitive, redact and server-only found nothing.

**Options.**

1. **Warn on secret-looking names** in `js_data()` keys and values (secret, token, password, `api_key`).
   - Cost: small.
   - Error mode: many false reports. A CSRF token is meant for the browser, and names like `tokenCount` and `publicKey` look secret but are not. So it would have to be off by default.
2. **Add a marker type,** `citry.Secret[str]`.
   - The runtime refuses to send it to the browser, anywhere in the returned value, with a message naming the component and the key.
   - The static `js_data()` type check from the A batch (m41) reports it before the page runs, once `Secret` is added to that check's list of types that cannot be sent.
   - Rendering it as text in a template shows `***`.
   - Cost: a small new public API.
   - Error mode: a plain string secret is still missed. The developer has to opt in by wrapping it.
3. **Track values read from environment variables.** Not feasible: ty does not follow values through code.

**Who owns it:** the runtime JSON check for `js_data()`, plus the m41 static check.

**Recommendation:** Option 2, plus a docs section on keeping secrets out of `js_data()`.

**Decision:** new public `citry.Secret`: yes/no. Option 1 as an off-by-default rule: yes/no.

## 12. Clearer runtime errors and development-only checks

No check before the page runs can catch these mistakes in every case. The proposals improve what the developer sees when they happen.

### 12a. A repeated component without `#c-key` (m51)

**Today:** the render fails with `repeated component call requires an explicit #c-key` (`_vue/direct_capture.py:1646`), naming no component and no template. The A rule catches the case inside one component, but not a server-only component placed in a Vue page.

**Proposal:** add the component tag, the template file and line of the call, and the fix ("add `#c-key=\"...\"` to `<c-Card>`") to the message.

**Decision:** plain fix: yes/no.

### 12b. `v-model` on an element that holds no value (m63)

**Today:** the render fails with `MODEL_HELPER_MISMATCH`, "generated v-model helper calls do not match parsed runtime directives", with no position (`crates/citry_vue_compiler/src/lib.rs:579-587`). The A rule catches it before the page runs.

**Proposal:** report the position of the `v-model` attribute, with a message naming the allowed elements.

**Cost:** a Rust change in `citry_vue_compiler`, so it ships with the next citry-core release, but with no PyO3 change.

**Decision:** plain fix: yes/no.

### 12c. Server and browser render different content (m14)

**Today:** the browser silently replaces the server's HTML, with no warning:

```javascript
created() {
  this.open = window.matchMedia('(min-width: 60rem)').matches;
},
```

Vue normally hydrates the server's HTML: it adopts the existing elements instead of rebuilding them. But an element that passes values to a child component is never hydrated. The server renderer does not model those values (`crates/citry_vue_compiler/src/server_render.rs:3011-3014`), so the element is allowed to differ, and Vue rebuilds it. Whether the first browser render differs depends on the browser window, so no check before the page runs can prove it. The reviewer did not re-run this behaviour.

**Options.**

1. **A development-only browser check:** after Vue mounts such an element, compare its server HTML with Vue's first render and log a console warning naming the component.
   - Cost: medium.
   - Error modes: content meant to differ (a clock, a random id) also gets a warning. It runs only in development mode, so production is unaffected.
2. **A static warning** when `data`, `setup` or `created` reads `window`, `document`, `matchMedia` or `localStorage` and writes component state.
   - Cost: small.
   - Error mode: false reports for values that are never rendered, so it would be off by default.
3. **Leave it.**

**Recommendation:** Option 1.

**Decision:** Option 1: yes/no.

### 12d. The same id from two components (m57)

The A rule catches a duplicate id inside one template. The same id coming from two components, or from one component rendered twice, depends on the whole page.

**Proposal:** in development mode only, scan each rendered page for repeated `id` values and log a warning naming the id.
- Cost: one pass over the page's HTML per render in development.
- Error mode: an id that browser code adds after the render is not seen.

**Decision:** yes/no/defer.

## 13. Misspelled CSS class (m16)

**What the developer sees today:** `class="bord"` where the component's CSS styles `.board`. The element renders unstyled, and no framework in the benchmark catches this.

Component CSS is not scoped, so any stylesheet, script or test may use a class name.

**Options.**

1. **A narrow rule:** report a static class name that is one slip from a class selector in the component's own CSS and appears in no registered component's CSS.
   - Cost: small to medium; it needs a small scanner for CSS selectors.
   - Error mode: it misses typos of classes from site-wide stylesheets and Tailwind. It never reports correct uses of them either, because they are not one slip from the component's own selectors.
2. **Leave it.**

**Recommendation:** defer, or ship Option 1 off by default.

**Decision:** ship Option 1 off by default, or defer.

## 14. Side bugs found while tracing

### 14a. A `Literal` field on an event's data class always fails

**Today:** every call fails with "Unsupported annotation for event data" (`ext/events/schemas.py:347-359`), even with a valid value:

```python
class FilterIn:
    status: Literal["open", "closed"]
```

The module's documented conversion table does not list `Literal`, so the code matches the table. But it fails on every call instead of when the class is defined, and `Literal` works for component `Kwargs`.

**Options.**

1. **Support it:** accept a value equal to one of the literal values with the same exact type, so `True` does not match `1`, as component `Kwargs` already do.
   - Cost: small, plus a line in the documented table.
2. **Reject it when the handler is defined,** with a message that names the field.
   - Cost: small.
   - Error mode: a handler that was never called but has a `Literal` field now fails at import.

**Recommendation:** Option 1.

**Decision:** choose 1 or 2.

### 14b. `events.md` §5.1 describes a form merge the runtime does not do

`docs/design/events.md:2363-2367` says a form's fields are sent together with the arguments written in `@c-submit`, with the written arguments winning on a name clash. The browser sends only the written arguments when there are any (`_vue/client.js:3686-3696`). The same paragraph says the JS and no-JS paths deliver the same call, which 4b shows is not true for number fields.

**Options.**

1. **Fix the doc to match the code.** Plain fix.
2. **Change the runtime to merge,** which is more useful: `@c-submit="search({page: 1})"` would also send the form fields. It is a behaviour change.

**Decision:** choose 1 or 2.

### 14c. CLAUDE.md lists too few PyO3 submodules

CLAUDE.md says the PyO3 surface is `template_parser`, `safe_eval` and `html_transform`. `crates/citry_core_py/src/lib.rs` also registers `vue`, `i18n` and `template_formatter`.

**Decision:** plain doc fix in CLAUDE.md, which you make or approve: yes/no.

### Already handled elsewhere

- **A Boolean prop accepts any string** (`_browser_expressions.py:491`): fixed in the A batch (m27).
- **The CSRF hidden input is rejected:** decision 4a.
- **Form text values for number fields:** decision 4b.

## 15. A shared value read under a key no ancestor provides (m50)

**What the developer sees today.** The page provides the board's name under `board`, and the card reads it under `bord`:

```citry-html
<c-provide key="board" name="Projects">
  <c-Card c-for="project in projects" ... />
</c-provide>
```

```python
class Card(Component):
    def template_data(self, kwargs, slots):
        board = self.inject("bord")
```

The render fails with a `KeyError` that names the component and the key and suggests the near key ("Did you mean 'board'?", `inject_value` in `provide.py:87`). No check reports it before the page renders, because no rule reads `inject()` calls.

**What exists.**
- A value is provided in three ways: `<c-provide key="...">` in a template, `self.provide("...")` in a component's Python code, and `render(provides={...})` at a render root.
- `Citry.inspect_component_graph()` (`docs/design/component_graph.md`) lists, for each registered component, the registered components whose templates write its tag. It records who wrote the tag: a card written inside a `<c-fill>` is listed under the component that wrote the fill, not under the component whose slot renders it.
- The runtime looks the key up along the render path, which includes the component whose slot renders the card (`Component.inject` docstring).

**Options.** Each one reads only an `inject()` call whose key is a string literal and that passes no default, since a default means the key may be missing on purpose.

1. **The key is provided nowhere.** With the app loaded, collect every literal key the app provides: the `key` of each `<c-provide>` in any registered template, and the first argument of each literal `provide("...")` call in any registered component's source. Report an `inject("bord")` whose key is not in that set, with a "did you mean" hint.
   - Cost: small.
   - It catches m50, because a misspelled key is rarely provided anywhere.
   - It misses a key that one page provides and the page that renders the card does not.
   - Error modes:
     - A key provided only through `render(provides={...})` in application code, or through a key written as an expression (`<c-provide c-key="...">`, `provide(name)`), is invisible, so the rule reports it falsely. The rule could also collect literal keys from `render(provides={...})` calls in the project's Python files, but a dictionary built elsewhere stays invisible. This is why it should be a warning, and a component can turn it off in its `Lint` class.
     - A component whose source cannot be read is skipped as a provider, so its keys count as missing; skip the rule entirely when any registered component's source cannot be read.
2. **The key is provided on a path above the component.** Start from the templates that render the component (the graph's reverse references) and walk up: a key counts when a `<c-provide>` around the tag provides it, when the writing component calls `provide()` with it, or when any component further up does. When the tag sits inside a `<c-fill>`, the component whose slot renders the fill, and the `<c-provide>` elements around its `<c-slot>`, count too. Report when no path provides the key.
   - Cost: medium to high. It needs a walk over the graph and the slot owners, which no code does today.
   - It catches m50, and also a key that only another page provides.
   - Error modes:
     - No registered template renders the component (it is rendered only from Python, or only through `<c-component is=...>` with a dynamic name): fall back to Option 1.
     - A fill whose slot owner cannot be resolved (a dynamic component, a slot passed through several components): treat that path as providing every key, so nothing is reported for it.
     - `render(provides={...})` at the root: as in Option 1.
     - A component rendered on two paths where only one provides the key: not reported, because the rule cannot tell whether the other path is ever rendered. The runtime error still catches it.
3. **Leave the runtime error.** It already names the component and the near key. No cost.

Browser-side `inject` in `$component({inject: [...]})` is a separate mechanism (Vue's own provide and inject) and is not covered by any of these options.

**Who owns it:** `citry check` with the app loaded (`_registry_lint.py`, next to the other rules that read every registered component), and the editor when it has loaded the app. Suggested names: `rule_unknown_inject_key`, `citry.template.unknown-inject-key`, a warning.

**Recommendation:** Option 2, which compares each literal `inject()` key with the `<c-provide>` keys in the templates that render the component, as you suggested, built on Option 1's collection of keys: Option 1 is the fallback whenever a path cannot be resolved. Ship it as a warning, because `render(provides={...})` keys can always be invisible.

**Decision:** choose 1, 2 or 3. If 1 or 2: warning or error by default.

## Decisions recorded

The maintainer's answers, as of 2026-10-21:

| # | Proposal | Decision |
|---|---|---|
| 1 | Components whose base class lives in another module | Options 1 and 2; Option 3 deferred. **Done:** Option 1 (the `citry.check.template-not-checked` notice) and Option 2 (the editor and `citry check --types` accept the classes the loaded app registers) |
| 2 | Run Vue's compiler over every template in `citry check` | Option 1, one converter shared with the runtime. **Done** as `citry.vue.compile-error` (`rule_vue_compile_error`, error by default), in `citry check`, `--static`, and the editor. A render writes its Vue template from what it rendered, so no single function can serve both: `citry/_vue/static_template.py` walks the nodes the template compiler produces (the same objects a render uses) and writes each element, component call, fill, slot outlet, text value, and `<c-if>`/`<c-for>` wrapper with the functions a render uses to write them (`_vue/direct_capture.py`, `_vue/capture.py`, `_vue/leaf_program.py`). `tests/test_vue_static_template.py` renders components and checks that both produce the same Vue template. Differences from this proposal: a `<c-if>` branch is wrapped in `<template v-if>` only where a render does, which is for a body it compiles once and reuses (a leaf program); otherwise each branch is written unwrapped, as a render writes the branch it picks, because the compiler checks a `<template>`'s contents on their own, not against the element around it. A compiler error that points only at text Citry generated, such as a component's own tag, is dropped, except a component inside a Vue `v-for`, which is reported on the component's tag and only by `citry check` with the app loaded (a `transparent` or `simple` component may sit there). The compiler reports a `v-else` with no `v-if` right before it (an orphan `v-else`) without a position, so the rule takes groups of `v-else`s out of their chains, recompiles, and halves each group that held an orphan until it finds which ones the compiler counted. A template the writer cannot convert, such as one using an extension's template syntax, is skipped without a notice. An expression error or a block inside `<p>` stays with its own rule even when that rule is off; to find every tag a block inside `<p>` breaks, the rule recompiles with that `<p>` renamed to `<q>`. Known gap: the check decides whether a render compiles the body as a leaf program as it would for an ordinary component, before constants are folded and without extension hooks, so a `simple`, `pure` or `transparent` component, an app with a non-Events attribute hook, or a `<c-if>` with a constant condition can render a branch differently. On this repository it checks 1,009 Python templates in about 0.6 s and 384 documentation examples, with no false findings. It found that the landing page's editor demo (`docs_site/snippets/landing/editor_invite_panel.py`) puts a component inside a Vue `v-for`, which fails when it renders; fixing the demo is left to the maintainer |
| 3 | Server event payload checks in the editor | Option 1, an `extra_fields` key in the handler description. **Done**, with a second key, `validated_by: "citry" \| "pydantic"`: `extra_fields` alone cannot tell the editor that a Pydantic model with `extra="forbid"` converts values and reads fields under aliases, so the editor skips a handler unless `validated_by` is `"citry"` |
| 4a | CSRF hidden input in a form | Option 2: the server drops known CSRF field names (default `csrfmiddlewaretoken`) before checking the data class, so the token can stay inside the form and both the JavaScript and the no-JavaScript paths work. **Done:** `extensions_defaults["events"]["_csrf_field_names"]`, engine-wide like `_max_envelope_bytes` |
| 4b | Text values for number fields | Option 1: the browser marks payloads it collected from a form, and the server converts them by the same rules as a form posted without JavaScript. **Done:** the call field `argsSource: "form"`; the browser now sends number and range inputs as text too, so both paths deliver the same values. The form-field rule (section 4) is done as `citry.browser.unknown-form-field` and `citry.browser.missing-form-field` |
| 5 | Typed slot data in the editor and `--types` | Option 1. **Done:** the app worker sends `slot_data_classes`, `TemplatePythonControl.slot_target` names the fill's component and slot, and the ty check file declares the name as a `Mapping[str, Any]` subclass with the slot's fields |
| 6 | Links to routes and static files | Ask each framework integration through `mount()` / `urlpatterns()`. No `static=` setting. The rule is `rule_unknown_url` in `LintSettings`, a warning by default. It runs only when an integration has registered a checker, and a project or a component can turn it off. **Done** as `citry.template.unknown-url`, with the notes `citry.check.url-checker-missing` and `citry.check.url-checker-failed`. The integration must run while `citry check` loads the app, so `--app` names the module that mounts Citry. The error-prevention benchmark's Citry app serves its pages from hand-written ASGI code, so m45, m48 and m61 stay unreported there |
| 7 | Prop values written as expressions | Option 1, for props only; payload expressions deferred. **Done** in the TypeScript check file |
| 8 | Emit payload types and handler arguments | Options 1 and 2. **Done:** the props and events guide shows typed emits (`emits: { hide: (/** @type {string} */ title) => true }`), which report a wrong payload at the child's `$emit` (m30). In the TypeScript check file, a listener whose value is only the name of a method the parent's `methods` declares (`@hide="hideCard"`) is passed to a generated function typed from the child's payload, so tsc reports a method that needs more values than the child sends on the method name (m60, `ts2345`). Nothing is reported for an untyped method, array-form `emits`, or a name that is not in `methods`. Because the check runs with `strict` off, a parameter type narrower than the payload is not reported. The benchmark's own app uses `emits: ['hide']` and an untyped `hideCard`, so m30 and m60 stay unreported there |
| 9 | Exact error text for Vue syntax errors; exact prop-write check | Not decided yet |
| 10 | Let the `v-iff` rule skip directives a component declares | Not decided yet |
| 11 | Secrets sent to the browser | Option 2; Option 1 not built. **Done:** the public `citry.Secret` (`Secret[str]`, read with `get_secret_value()`, shown as `***` wherever Python turns it into text). Rendering fails with an error naming the component and the key path when `js_data()`, `css_data()` or State holds one; `citry.js-data.unsupported-type` reports one in a `JsData` annotation, a module-level value that `js_data()` puts in its result (also inside a dict or list literal, unpacked with `*`, in either branch of a conditional expression, inside `Const(...)`, or read as an attribute such as `config.API_TOKEN`, where `config` is a module or a plain class), and a value ty types as `Secret`. A plain string secret is still not detected. A cached component cannot take a `Secret` input unless its `Cache.vary()` leaves it out: the cache key would otherwise hold the secret, so building it raises `CacheKeyError`. A `Secret` in an action a handler returns is refused only by the events protocol's generic JSON check, which does not name the key. The benchmark's app keeps `SECRET_TOKEN` a plain string, so m42 stays unreported there |
| 12a | Repeated component without `#c-key` | Plain fix. #230 added the tag, template and line. **Done:** the line is right for template files, slot fills and template-valued attributes, the duplicate-key message names the repeated value and explains nested loops, and the element-key conflict uses the parser's wording |
| 12b | `v-model` on an element that holds no value | Plain fix. **Done in Python, with no Rust change:** when the Vue compiler reports `MODEL_HELPER_MISMATCH`, the render runs the `rule_invalid_model_target` check over the authored templates the Vue template came from and names each element, its template and line. When it finds none, the error names the component and keeps the compiler's text. A template-valued attribute written without the `<>...</>` wrapper, such as `c-body="<b>Hi</b> <div v-model='q'></div>"`, still renders as a template, but the search and `rule_invalid_model_target` read only a wrapped value, so a bad `v-model` there gets that generic message |
| 12c | Server and browser render different content | Option 1. **Done**, in development mode only: a hydrating page whose shells carry served contents inlines `_vue/dev_checks.js`, and after `mount()` the runtime compares each element Vue rebuilds (marked `data-allow-mismatch="children"`) with the HTML the server sent, and logs one `console.warn` per element naming the component, the element, the first difference, and the `data-allow-mismatch` value that silences it. The comparison is one-sided: it reports only a text or attribute value the server wrote that Vue shows differently, because the server leaves out what it cannot compute. Content meant to differ (a clock, a random id) also warns; move it to `mounted()` or add `data-allow-mismatch`. Elements Vue adopts normally, state changed in `mounted()` or after an `await`, and elements only one side has are not compared. m14 warns on a 1280px window (`aria-expanded`), not at 600px or in production. A production page does not load the check: it carries no flag and no script, and the runtime keeps only the short call that looks for the script. Known limits: a list that `created()` filters can go unreported, and a browser-only `v-if` next to a browser-only `v-for` of the same tag can still warn |
| 12d | The same id from two components | Yes, in development mode only. **Done** on the server, because only the server can name every component, including those without browser code: serialization passes each component's own HTML to `_page_ids.py`, which issues one `RuntimeWarning` per page listing each repeated id with the components and template files that wrote it. Ids set by Vue bindings or scripts, ids in `<template>`, `<noscript>` or a `v-if`/`v-else`/`v-for` element, and fragments a server event renders again (checked on their own) are not compared. Known limits: a `v-if` written on a component's own tag still warns, and a `simple` component's ids are named under its caller |
| 13 | Misspelled CSS class | Option 1, a warning, on by default. **Done** as `citry.css.misspelled-class` (`rule_misspelled_css_class`), in `citry check` with the app loaded (not the editor, like `citry.css.misspelled-variable`). A slip that moves, doubles or drops a digit, a missing final `s` after a letter other than `s`, one of the listed short words `close`, `collapse`, `disable`, `enable`, `fade`, `mute`, `show`, `slide` and `toggle` next to its longer form, and one letter typed twice or left out in a first hyphen part of one or two characters are not reported, because they usually name another class of the same family (`col-1`/`col-12`, `tab`/`tabs`, `disable`/`disabled`, `navbar-toggle`/`navbar-toggler`, `p-4`/`px-4`). Any other cut-short word (`heade`/`header`) and two letters swapped in a short first part (`iu-button`/`ui-button`) are reported. Pairs where both forms are real classes outside that list, such as Tailwind's `tracking-wide`/`tracking-wider`, are still reported. A class one slip from the component's own selectors is reported even when a stylesheet Citry does not read styles it. No findings on this repository's apps, citry_ui, or the docs site |
| 13+ | Every undeclared CSS class and variable | Two more rules, off by default (`"ignore"`, which the diagnostics schema now allows for a configurable rule). **Done** as `citry.css.undeclared-class` (`rule_undeclared_css_class`): a static class that no CSS Citry reads declares; and `citry.css.undeclared-variable` (`rule_undeclared_css_variable`): a `var(--x)` without a fallback in a component's CSS that nothing Citry reads sets. Citry reads each registered component's `css` or `css_file`, its inline or local-file `Dependencies` stylesheets, its template's `<style>` elements, and, for variables, every `css_data()` key and `--x` strings in templates, component JavaScript and Python modules. It does not read stylesheets linked by URL, so Tailwind utilities and site stylesheets are reported, which is why both are off |
| 14a | `Literal` field on an event's data class | Option 1; already done on main (`ext/events/schemas.py`) |
| 14b | `events.md` §5.1 form merge | Option 1; §5.1 was already fixed on main. **Done:** the component-tag section (relocated `@c-submit`) still described the merge and now matches the code |
| 14c | CLAUDE.md lists too few PyO3 submodules | **Done:** CLAUDE.md and `docs/agent/INDEX.md` list `template_parser`, `vue`, `html_transform`, `i18n`, `safe_eval` and `template_formatter` |
| 15 | A shared value read under a key no ancestor provides | Option 2, with Option 1 as the fallback, a warning. **Done** as `citry.template.unknown-inject-key` (`rule_unknown_inject_key`), in `citry check` with the app loaded and in the editor once it has loaded the app. `citry/_provide_keys.py` reads every registered template once and works out the keys that reach each component: from each template that writes its tag, the `<c-provide>` keys around the tag, the `provide()` keys of the writing component, and, for slot content, the keys the component whose `<c-slot>` shows it provides around that slot (also through a slot passed on to another component), plus the keys that reach the writing component, repeated until nothing changes. The literal keys of `render(provides={...})` and `provides=dict(...)` calls in the project's Python files (under the check's folder, skipping virtual environments, plus the modules that define registered components) count everywhere. A component no template writes, including one only a dynamic `<c-component>` picks, falls back to every literal key the app provides. Differences from this section: a dynamic `<c-component>` also counts as a place that may render every component, so its surroundings count too; a `provide()` key written as a module-level string constant counts as that string; and a `<c-provide c-key>`, a `provide()` key written as an expression, or markup in a component attribute on a path makes that path provide every key (the fallback still ignores them, as Option 1 says). A component whose source cannot be read counts as providing every key, so the fallback reports nothing while one exists; any registered template that cannot be read or parsed turns the rule off. Only `self.inject()` with one string literal and no default, in a component class or a component base class, is read; an `inject()` on a base class is reported once, when no registered subclass gets the key. Built-in templates' own dynamic `<c-component>` (the `<c-i18n>` host) counts as passing its slot through. The editor receives the keys from the app worker (`inject_keys`) and reads the calls from the open buffer. The benchmark's m50 is reported with "Did you mean 'board'?"; no findings on the examples, citry_ui, the docs site with its examples, or the benchmark baseline app |
| m53 | `<img>` without `alt` | Warning by default; a project can raise it to an error |
| m62 | Boolean attributes | Follow the HTML standard: any value other than empty or the attribute's own name is reported, including `"true"` |
