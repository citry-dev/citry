# Audit: maintainer's work Django app as context for citry Component.Events

Project audited: `/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/old-chk/baseapp` (django-components + django-ninja + Alpine.js + Tailwind, the maintainer's production app). All counts exclude `.venv`, `node_modules`, `__pycache__`, and test files unless noted.

## Headline numbers

| Metric | Value |
|---|---|
| View-bearing registered components | 38 (24 pages, 14 widgets; +3 Autocomplete subclasses inheriting View) |
| `get_component_url` references (non-test .py) | 116 |
| Alpine `$fetch({...})` call sites (html+js) | 47 |
| Raw `fetch(` call sites against component URLs | 1 (autocomplete.js) |
| htmx attributes | 1 file (a leftover demo hitting `/api/test`, not a component URL) |
| `<form>` tags total / with `action=` | 4 / 1 |
| ninja `Query` schemas for these Views | 52; field count median 2, max 5 |
| Views re-rendering the component in the handler (fragment pattern) | 8 / 38 |
| Views touching `request.user` or `request.session` | 25 / 38 (66%) |
| View-bearing components receiving `{% fill %}` at call sites | 0 |

## 1. Client patterns: how the frontend invokes component View endpoints

One dominant pattern, used near-universally: **the server computes the endpoint URL with `get_component_url(...)` inside `get_template_data()`, injects it into the template (or `js_props`), and the client fires it from Alpine.js via a custom `$fetch` magic helper**. The helper (`app_home/static/js/alpine-fetch.js`) wraps `fetch()` and injects the CSRF token from an Alpine store; JSON bodies, `onSuccess`/`onError` callbacks. htmx is effectively absent (one leftover demo in `app_home/templates/app_home/pages/index.html:11`), and classic form posts are absent (1 `action=` form, a GET search in `app_project/pages/edit_pocs/edit_pocs.html:9`).

Identity travels in **URL query params, not the body**: `get_component_url(Comp, query={"project_id": ..., "role_id": ...})` bakes the ids into the URL at render time; the body carries only the user's input (vote value, note text, form fields).

Representative snippets:

1. Vote widget, server-baked URL + Alpine `$fetch` POST (`app_project/components/ai_summary_vote/ai_summary_vote.html:1-29`):

```html
<div x-data="{ submitUrl: {{ submit_url|json|escape }} }" ...>
  {% component "Vote"
    initial_vote=initial_vote
    js:onChange="(vote) => {
      $fetch({
        endpoint: submitUrl,
        requestConfig: { method: 'POST', body: { vote } },
        ...
      });
    }"
  / %}
```

2. Tree drag-and-drop, per-node URLs embedded in the rendered data (`app_process/components/process_tree/process_tree.js:75-83`; the URLs are attached server-side in `app_process/pages/process_steps/process_steps.py:143-147` as `step_node.meta["move_url"] = get_component_url(...)`):

```js
const payload = { parent_id: parentId, index: adjustedIndex };
vm.$fetch({
  endpoint: step.move_url,
  requestConfig: { method: 'POST', body: JSON.stringify(payload) },
  onSuccess: () => location.reload(),
});
```

3. Autocomplete, raw GET fetch with a query param (`components/autocomplete/autocomplete.js:66-75`; `endpointUrl` comes from `get_component_url(self)` at `components/autocomplete/autocomplete.py:122-124`):

```js
const url = new URL(urlStr);
url.searchParams.set(props.queryParamName, term);
...
const response = await fetch(url);
```

A secondary pattern worth noting for Events: **tab fragments**. `ProjectModuleTabs` bakes both a page URL and a `data-fragment-url` (`get_component_url(ProjectModulePanel, query={...5 ids/flags})`) into each tab (`app_project/components/project_module_tabs/project_module_tabs.py:76-93`); clicking swaps the fragment via fetch and updates the address bar. This is a GET that re-renders a component purely from ids + flags, i.e. exactly the citry State round trip.

## 2. Payload sizing: what a signed State token would carry vs what gets rendered

All 52 ninja `Query` schemas across the 38 Views carry only ids, short enums, and booleans. Field count distribution: 17 schemas with 1 field, 18 with 2, 14 with 3, 2 with 4, 1 with 5 (median 2, max 5, the max being `ProjectModuleTabsGetQuery` at `app_project/components/project_module_tabs/project_module_tabs.py:26-31`).

Token estimate method: JSON state payload, plus component id (~40-60 B FQN), timestamp, and an HMAC-SHA256 signature, base64-encoded (roughly `1.34 x len(json) + ~110 B` overhead). Five components:

| Component | State the token would carry | Est. JSON | Est. signed token | What the component actually renders (template_data scale) |
|---|---|---|---|---|
| Autocomplete (`components/autocomplete/autocomplete.py`) | nothing beyond component id (search term is a per-request query param; config is class constants) | ~20 B | **~150 B** | input + up to `MAX_RESULTS = 20` dropdown items, `js_props` with URLs, ~1-3 KB HTML |
| AiSummaryVote (`app_project/components/ai_summary_vote/ai_summary_vote.py:44-51`) | `owner_id`, `summary_id`, `summary_type` (exactly what `get_component_url` embeds today) | ~85 B | **~230 B** | tiny widget, ~0.5 KB HTML |
| ProcessTree (`app_process/components/process_tree/process_tree.py:17-20,97-128`) | per-action `process_id` + `step_id` (+ `editable` flag) | ~60 B | **~200 B** | the **whole step tree** (`step_nodes` kwarg, unbounded, each node carrying menu items and 4 per-step URLs), easily tens of KB |
| ProjectModuleTabs (fragment re-render; `project_module_tabs.py:26-31,139-149`) | `project_id`, `phase_type`, `process_id`, `tab`, `preview` (the 5-field worst case) | ~115 B | **~270 B** | 3 tabs x 3 URLs each, ~1-2 KB HTML |
| ProjectEditFeedbackNotePage (form page; `app_project/pages/edit_feedback_note/edit_feedback_note.py:28-38`) | `project_id`, `feedback_id`, `feedback_note_id` | ~75 B | **~215 B** | full page: `layout_data` (nav, breadcrumbs), `Project`, `ProjectClientFeedback` models, form, redirect/save/delete URLs, tens of KB |
| ProjectUsers (list + add/delete; `app_project/components/project_users/project_users.py:27-33`) | `project_id` (+ `role_id` per row action) | ~40 B | **~180 B** | roles table + add-user form including **all** available user choices |

**Verdict: yes, real tokens stay far under budget.** Worst case observed is 5 scalar fields; every realistic token lands at 150-300 B, roughly 7x under the 2 KB median target and 25x under the 8 KB cap. The margin is 1-2 orders of magnitude, so even doubling for nesting context or per-slot metadata is safe.

The load-bearing condition: state must stay ids + flags, never the render inputs. The gap between the two is huge here (60 B of ids vs a whole step tree or a user list), and this codebase already lives by the id + re-fetch discipline: every single handler starts from `get_object_or_404` on the id fields and re-queries the DB (`process_tree.py:109`, `project_users.py:206,239-240`, `edit_feedback_note.py:183-184`). A design that let `Kwargs` leak into the token (ProcessTree's `step_nodes`, ProjectUsers' `roles_with_users` + `available_users`, the page's `layout_data`) would blow the 8 KB cap immediately and would also be unserializable (Django model instances). The cap is therefore a useful guardrail, not a constraint users will fight.

## 3. Shape: widgets vs pages, slot fills, and request/user access

**Split: 24 of 38 are full pages, 14 are widgets** (63% / 37%). Pages are the `*Page` classes under `app_*/pages/` (edit/create forms like `ProjectEditFeedbackNotePage`, `ProcessStepsPage`, `IntegrationsPage`); their Views are the REST backend for the page's own form. Widgets live under `components/` and `app_*/components/`: 1 shared library widget (Autocomplete, plus 3 subclasses inheriting its View), and 13 domain widgets (vote, tree, tabs x3, panels x3, users, modules, output form, events, client_project). So View-bearing components skew toward pages, but the widget population is where the high-frequency interactions are (vote, autocomplete, drag-and-drop, tab fragments).

**Slot fills at call sites: zero.** Verified programmatically over every `{% component "<ViewBearer>" %}` occurrence in html and py templates: all call sites are self-closing (`/ %}`), including the Autocomplete subclasses. The codebase uses fills heavily (138 `{% fill %}` occurrences), but they all flow *into* generic UI components (Table, Dialog, Form, Tabs, ExpansionPanel) from inside the View-bearers' own templates, e.g. `process_tree.html:55,70` filling a delete Dialog. Implication for citry: a State token that cannot reconstruct arbitrary caller slot fills matches real usage; View/Events-bearing components are self-contained subtrees, and fills are an intra-component composition tool one level down.

**request.user / session: needed by two thirds of handlers.** 25 of 38 View classes reference `request.user` or `request.session` inside the View body. Three recurring uses: permission checks (`user_can_edit_project(request.user, project_id)` at `project_users.py:208`, `user_is_project_member` at `edit_feedback_note.py:186`), audit logging (`user_id=request.user.pk` in `log_project_activity`, `edit_feedback_note.py:203`), and per-user API clients (`get_monday_client(request.user)` at `process_steps.py:234`). The remaining 13 still run behind `@auth_requirements(auth_spec, ...)` decorators, so authentication context wraps 100% of handlers even when the body does not read the user. The Events.globals case (handler access to request/user/session) is a hard requirement, not an edge case.

**Fragment re-render is an established pattern**: 8 of 38 Views call `Component.render_to_response(...)` in their GET handler, rebuilding the component purely from the 1-5 ids/flags in the query string (tabs and panels). This is the closest existing analogue to the citry Events state-token round trip and confirms the "ids in, HTML out" contract works at production scale.
