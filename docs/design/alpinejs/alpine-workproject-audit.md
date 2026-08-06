# Audit: how Alpine.js is installed, extended, and used in the maintainer's work app

Complement to `audit-context.md` (which covered the `$fetch` server-call pattern). Project audited: `/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/old-chk/baseapp` (django-components + django-ninja + Alpine.js + Tailwind). All paths below are relative to that base; all counts exclude `.venv`, `node_modules`, `__pycache__`.

## 1. Installation

**No bundler, no npm for the app itself.** Everything Alpine-related is loaded as CDN or static `<script>` tags through the `Media.js` of a single `Base` django-component (`app_home/components/base/base.py:18-40`), in this order:

1. `js/htmx.js` (local, marked `# TODO: Remove HTMX`, base.py:21-22; one leftover demo usage)
2. `js/alpine-swap.js`, `js/alpine-fetch.js`, `js/alpine-loaded.js` (local custom plugins, registered on `alpine:init`)
3. `//unpkg.com/@alpinejs/anchor` (unversioned CDN)
4. `https://cdn.jsdelivr.net/npm/alpine-reactivity@0.1.11/dist/cdn.min.js`
5. `https://cdn.jsdelivr.net/npm/alpine-composition@0.1.29/dist/cdn.min.js`
6. `<script src="//unpkg.com/alpinejs" defer></script>` wrapped in `mark_safe`, with the comment "defer is used so that AlpineJS is actually loaded only after all components are registered" (base.py:30-34)
7. `defineComponent.js`, `queryManager.js`, `base.js` (component-local global helpers)

- **Alpine version: unpinned** (`//unpkg.com/alpinejs` = latest v3 at load time). The only version reference in the repo is a comment pointing at `alpinejs@3.14.9` (`app/components_extensions/alpine.py:141`).
- **Official plugins: only `@alpinejs/anchor`.** No morph, persist, focus, collapse, intersect, or mask anywhere (grep over py/js/html returned nothing; the vendored alpine-swap even prints an error if `morph: true` is requested without `Alpine.morph`, `app_home/static/js/alpine-swap.js:143-150`).
- **Maintainer's own packages: 2 of 4 present.** `alpine-reactivity@0.1.11` (Vue-style `ref`/`computed`/`watch`) and `alpine-composition@0.1.29` (Vue-style `defineComponent` with `props`/`emits`/`setup`, plus the `x-props` directive) are load-bearing everywhere. `alpine-provide-inject` and `alpine-alpine` appear nowhere.
- **Initialization:** no manual `Alpine.start()`. The CSRF store is created on `alpine:init` inline in `app_home/components/base/base.html:26-30`. The two `package.json` files in the repo (`storybook/`, `tailwind_app/static_src/`) contain no Alpine dependencies.

## 2. Extension surface

### Custom magics (the complete list; no custom `Alpine.directive()` calls exist)

| Magic | File | Purpose |
|---|---|---|
| `$fetch` | `app_home/static/js/alpine-fetch.js` | fetch wrapper: URL or `HTMLFormElement` endpoint, `requestConfig` as object or transform function, `onSuccess`/`onError` callbacks, auto `X-CSRFToken` header from `Alpine.store('csrf')` (lines 57-68), auto `JSON.stringify` of plain-object bodies (lines 74-77). 47 call sites (see audit-context.md). |
| `$swap` | `app_home/static/js/alpine-swap.js` | vendored copy of james0r/alpine-swap (header comment lines 1-9): htmx-style HTML swapping with `swapMethod` (innerHTML/outerHTML/beforebegin/...), CSS `select` from response, settle classes, optional View Transitions, optional morph. Drives fragment swaps, e.g. `client_project.html:29-40` and the status-updates search. |
| `$loaded` | `app_home/static/js/alpine-loaded.js` | returns a reactive `{ value }` that flips true once every `x-data` under the element that references a *named* component has been registered (walks into `<template>` content, lines 40-63). Used with `x-if` so fragments do not evaluate before their component definitions arrive. |

### Store

Exactly one: `Alpine.store('csrf', { token })`, set inline in `app_home/components/base/base.html:26-30` from the Django `csrf_token`.

### Named components: 32, all via alpine-composition, zero direct `Alpine.data()` calls

Registration goes through a project wrapper `defineComponent()` (`app_home/components/base/defineComponent.js`): it calls `AlpineComposition.registerComponent(Alpine, component)`, records the component in a module-level `components` registry, and notifies `componentsListeners` (which is what `$loaded` hooks into). It guards both orders: registers immediately if `globalThis.Alpine` exists, else waits for `alpine:init` (lines 17-24).

Component shape is Vue-like, e.g. `components/vote/vote.js`: `{ name, props: { values: { type: Object, required: true }, ... }, emits: ["change"], setup(props, vm, { ref, watch }) { ... return bindings } }`. `vm` exposes `$el`, `$emit`, `$fetch`, `$dispatch`.

The 32 registered names, grouped:

- **Shared library widgets** (`components/`): `tabs`, `vote`, `autocomplete`, `pill_toggle`, `expansion_panel`, `multiselect`
- **App widgets**: `attachments`, `template_attachments`, `project_modules`, `project_modules_item`, `project_module_events`, `project_module_preview_actions`, `project_nav`, `project_output_dependency`, `project_output_form`, `project_users`, `process_tree`, `process_steps`, `bookmarks`, `bookmark`, `form`, `layout`
- **Page controllers** (one per edit/create page): `edit_attachment`, `edit_feedback`, `edit_risk`, `edit_status_update`, `edit_outcome`, `project_event_edit`, `prompt_playground`, `project_summary_create`, `org_summary_create`, `calendar_event_create`

### Django-side serialization filters (`app_home/templatetags/common.py`)

- `|json` (line 31): `json.dumps`, used as `{{ value|json|escape }}` inside `x-props`/`x-data` (13 files)
- `|alpine` (lines 39-49): `json.dumps` with `"` replaced by `'` so it can sit inside a double-quoted HTML attribute; carries a `NOTE: Maybe we could use HTML escaping to avoid the issue with double quotes?` and a `TODO - Replace with json or js filter`
- `|js` (lines 52-95): renders a dict as a raw JS object literal where every string value is treated as a JS *expression* (this is how `js:onChange="(vote) => ..."` callback strings become live code)

### The unregistered django-components AlpineExtension prototype

`app/components_extensions/alpine.py` defines `AlpineExtension(ComponentExtension)`: after render, if the HTML matches `x-data="<word>` (regex line 17), wrap the whole result in `<template x-if="$loaded.value">` (lines 169-180). It is **not enabled**: `COMPONENTS.extensions` in `app/settings/base.py:304-311` lists only `PydanticExtension` and `NinjaExtension`. Lines 20-164 are a long design-notes comment for a deeper Alpine integration: auto-injecting `x-data` on component roots, loading component JS as modules, mapping `get_js_data()` to props, erroring in Python when an Alpine-bound component has multiple roots, and "Fix scope when using slots, so we can get rid of the `js:passthrough` attribute" (line 164). This file is direct prior art for citry's Events design.

## 3. Usage shape and scale

- **`x-data` occurrences: 51 total.** 49 in `.html` templates plus 2 inside Python inline template strings (`app_project/components/project_users/project_users.py:78`, `app_project/pages/project_event_edit/project_event_edit.py:143`).
- **Distribution: 33 named-component references vs 18 inline object literals.** Named ones always pair with `x-props` (about 20 sites) to receive server data. Inline literals are small state bags (`dialog`, `menu`, `text_input`, per-row expand state in `projects_table.html:2-13`, `submitUrl` in `ai_summary_vote.html:1-4`) or page-local controllers (search + `$swap` in `project_status_updates_page.html:31-60`).
- **Directive counts across templates:** `x-show` 46, `x-cloak` 29, `x-text` 22, `x-ref` 11, `x-if` 8, `x-for` 6, `x-model` 4, `x-bind` 4, `x-html` 2. Zero `x-init`, `x-teleport`, `x-ignore`, `x-effect`, `x-transition` in templates. `x-anchor` never appears literally; the Menu component assembles the attribute name in Python: `all_list_attrs[f"x-anchor.{kwargs.anchor_dir}"] = kwargs.anchor` (`components/menu/menu.py:81-82`).
- **Shorthand (written directly in templates):** `@click=` 36, `@change=` 9, `@input=` 2, plus `:class=` 8, `:value=` 6 and a tail of `:name`/`:key`/`:id`/aria bindings. A comparable volume flows through `attrs:` kwargs (section 4).
- **Custom events via `$dispatch`, snake_case names:** `step_menu_toggle` (`process_node.html:38` listened via `attrs:@step_menu_toggle` at `process_tree.html:14`), `sidebar_toggle` (`app_home/components/navbar/navbar.html:10`), `click_outside` (`components/menu/menu.html:23`), `user_delete` (`project_users.py` template string).

### Passing server data into Alpine: four mechanisms, no `json_script` anywhere

1. **`x-props` + `js_props` context var:** the component's Python merges caller-supplied `js:` kwargs with computed values (`components/vote/vote.py:31-36`) and the template renders `x-props="{ values: {{ js_props.values|json|escape }}, onChange: {{ js_props.onChange|escape }} }"` (`components/vote/vote.html:2-8`). Callback strings arrive raw, so they evaluate as JS.
2. **Inline `x-data` literal with `|json|escape`**, sometimes via `JSON.parse('{{ role|json|escape }}')` inside the attribute (`project_users.py:78-80`).
3. **`|alpine` filter** (single-quoted JSON) for per-row blobs, e.g. `step: {{ entry.step_data|alpine }}` (`process_node.html:9-11`).
4. **`data-*` attributes read via `$el.dataset`**, e.g. `data-fragment-url` (`client_project.html:4,29-31`, `project_status_updates_page.html:31-38`).

### Scale and the densest pages

373 `{% component %}` call sites overall; Alpine-rooted widget instantiation counts: Table 32, Form 25 (every `form` root is an Alpine component, `app_home/components/form/form.html:4`), ExpansionPanel 6, Tabs 6, Dialog 5, Menu 4.

Biggest candidates for the recalled 300-500-component page freeze:

1. **The overview/home page** (`app_home/pages/overview/overview.html:20-25`): loops `ClientProject` per client; each contains a `PillToggle` root + a `projects_table` inline `x-data` root + **2 Alpine roots per project row** (the `ai_summary_vote` inline wrapper plus the named `vote` component, `projects_table.html:33-40`) + an `x-show` detail row per project. Alpine roots scale as 2 x clients + 2 x projects, so a few dozen clients with a handful of projects each lands in the hundreds. This is the strongest candidate.
2. **The process steps page** (`app_process/pages/process_steps/process_steps.html`): `process_steps` + `process_tree` roots plus **one inline `x-data` root per step node** in an unbounded tree, each parsing a `|alpine` JSON blob (`process_node.html:8-13`), plus Menu and Dialog under `x-if` (`process_tree.html:17-30`).
3. **Project modules** (`project_modules.html:3,53` twice, plus `project_modules_item` per item).

Every root's `x-data`/`x-props` string is compiled with `new Function` at init, so the cost profile matches the recollection of a 0.15-0.3 s init freeze at 300-500 roots.

## 4. Interplay with django-components

- **Alpine attributes travel as component kwargs, not static markup.** The `attrs:` prefix forwards them through Python into `{% html_attrs %}` merging: `attrs:@click=` 27, `attrs:@click.prevent=` 18, `attrs:@submit.prevent=` 16, `attrs:@click.stop=` 6, `attrs:x-text=` 5, `attrs:x-ref=` 4, `attrs::class=` 3, plus `attrs:x-bind:class`, `attrs:x-on:click.stop`, `attrs::disabled`, and listener attrs for custom events (`attrs:@step_menu_toggle`, `attrs:@user_delete`, `attrs:@sidebar_toggle`, `attrs:@click_outside`). Roughly 90 Alpine attributes exist only after render-time dict merging.
- **Django template syntax inside Alpine expressions** is routine: dynamic state names `'{{ model }}': false` and `@keydown.escape="{{ model }} = false"` (`components/dialog/dialog.html:8-17`, `components/menu/menu.html:7-30`), interpolated ids `toggleExpanded('{{ data.item.alpine_id }}')` (`projects_table.html:71`), and Alpine expressions passed as Django kwargs the other way (`model="contextStep.value"`, `anchor="contextMenuRef.value"` at `process_tree.html:19-26`).
- **`js:passthrough` (20 uses):** hands parent-scope Alpine bindings to a child component so the child's rendered markup can call them (e.g. `edit_attachment.html:23-25`, `process_edit_form.html:41-43`). Exists because django-components slot rendering breaks Alpine's scope inheritance expectations; removing it is goal 5 of the AlpineExtension notes (`alpine.py:164`).
- **No `x-teleport`, no slot-related Alpine tricks.** Dialogs render in place with z-index. The only "slot-adjacent" trick is `$loaded` + `x-if` wrapping.
- **Collision surface for citry's `@c-*` / `:c-*` to `data-cev-*` rewriting:**
  - Zero occurrences of `@c-`, `:c-`, or `data-cev` today, and the common shorthands (`@click`, `@change`, `:class`) do not match a literal `c-` prefix, so a prefix-scoped rewriter would not touch any existing Alpine attribute. No naming collision.
  - The real hazard is **when** rewriting happens: in this codebase a large share of Alpine attributes never appear as literal template text. They are built as Python dict keys (`menu.py:81-82`), forwarded through `attrs:` kwargs and emitted by `{% html_attrs %}`, or live inside Python string templates (`project_users.py:78-90`). A compile-time attribute rewriter sees none of these; citry needs defined semantics for dynamically merged/spread attributes or an explicit rule that `@c-*`/`:c-*` are only recognized as literal template attributes.
  - Event names here are snake_case DOM CustomEvents (`step_menu_toggle`); any citry event-name normalization (case, hyphens) should keep such names working since HTML attributes lowercase silently.

## 5. Pain points visible in the code

1. **Load-order fragility, defended in three places:** the `defer` hack with an explanatory comment (`base.py:30-34`), the dual-path registration guard in `defineComponent.js:17-24` (`if (globalThis.Alpine) ... else alpine:init`), and the whole `$loaded` magic plus the unshipped AlpineExtension, both existing solely so markup does not evaluate before its component definition is registered (the fragment-injection problem).
2. **Alpine `x-for` DOM desync worked around by hand:** "NOTE: For unknown reason, AlpineJS removes the attachment from for-loop only on second click. So we do so ourselves" followed by manual `querySelectorAll(...)[index].remove()` (`app_project/components/template_attachments/template_attachments.js:34-39`).
3. **Hybrid server/client rendering reconciliation:** because Django renders the initial rows but Alpine adds/removes them client-side, three components re-populate Alpine-generated HTML after `nextTick` ("When attachments are added or removed, we add/remove HTML by AlpineJS ... then populate the generated HTML"): `template_attachments.js:69-80`, `app_attachments/components/attachments/attachments.js:55`, `components/multiselect/multiselect.js:77`. A whole class of code exists just to reconcile the two render sources.
4. **Cross-component access by DOM query:** `Alpine.$data(document.querySelector('[x-data="attachments"]')).addAttachment()` and variants in 8 files (`app_attachments/pages/edit_attachment/edit_attachment.js:33-40`, `app_project/components/project_tabs/project_tabs.py:38-44`, plus `process_tree.js`, `project_output_form.js`, `edit_risk.js`, `edit_feedback.js`, `edit_outcome.js`, `calendar_event_create.js`). There is no inter-component channel; components find each other by `x-data` attribute selectors. Notably, the maintainer's own `alpine-provide-inject` package (built for exactly this) is not used here.
5. **`x-cloak` everywhere content flashes:** 29 uses across 8 files (dialogs, edit forms, module panels) backed by `[x-cloak] { display: none !important; }` (`tailwind_app/static_src/src/styles.css:38-40`).
6. **Escaping gymnastics for attribute-embedded data:** the `|alpine` quote-swapping filter with its own doubting NOTE (`common.py:45-48`), and `JSON.parse('{{ role|json|escape }}')` inside an attribute value (`project_users.py:78-80`).
7. **Hand-rolled URL state sync:** `queryManager.js` (177 lines) implements query-param watch/set/replaceState with its own callback registry because there is no router; loaded globally via `base.js:4-7`.
8. **Dead htmx still shipped:** `htmx.js` loaded on every page and a CSRF hook kept alive, both tagged `TODO: Remove HTMX` (`base.py:21-22`, `base.html:17-23`).
