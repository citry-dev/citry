# Component.View usage audit, chunk 2 (app_project: panels, tabs, module and output forms)

Audit of real django-components `Component.View` usage in the maintainer's work
project (`baseapp`), against the citry Events design
(`docs/design/events.md`, sections 2, 3, 7.1). Nine files assigned; ten
component classes have a View (one inherited); three pure-display components in
the same files were skipped (`GoogleCalendarEventAutocompleteItem`,
`ProjectModulePanelInfoTab`, `ProjectPhasePanelInfoTab`).

How the schema fields were filled:

- **est_state_bytes** counts only what the citry Events design would sign into
  the state token: the ids and small flags a rebuild needs, never the fetched
  ORM data (section 7.1's id-plus-reload pattern). Sizes are the serialized
  JSON of that State.
- **rerenderable** is "yes" when a rebuild from State plus `request.user`
  could faithfully re-render the component. In every such case here, the
  existing GET View handler is itself the proof: it already rebuilds the full
  kwargs from the same ids.

## Summary table

| Component | Verbs | Actions | State fields | ~bytes | Rerenderable |
|---|---|---|---|---|---|
| ClientProject | GET | 1 (filter re-render) | org_id, active, author_type | 50 | yes |
| GoogleCalendarEventAutocomplete | GET (inherited) | 1 (search) | none (stateless) | 0 | n/a, returns JSON |
| ProjectModuleEvents | POST | 1 (save event links) | project_id, process_id | 40 | yes |
| ProjectModulePanel | GET | 1 x 3 tabs | project_id, phase_type, process_id, tab | 85 | yes |
| ProjectModuleTabs | GET | 1 (tab strip) | = kwargs | 100 | yes |
| ProjectModules | POST, PATCH | 3 (add, remove, reorder) | project_id, phase_type | 45 | yes |
| ProjectPanel | GET | 1 x 5 tabs | project_id, tab | 35 | yes |
| ProjectOutputForm | POST | 1 (save output) | project_id, phase_type, output_id, redirect_url | 110 | yes |
| ProjectPhasePanel | GET | 1 x 2 tabs | project_id, phase_type, tab | 60 | yes |
| ProjectPhaseTabs | GET | 1 (tab strip) | = kwargs | 60 | yes |

---

## 1. ClientProject

`app_project/components/client_project/client_project.py`

A dashboard card for one client organization: name, health, an AI/Human
summary toggle, a projects table. Kwargs carry a pre-fetched ORM bundle
(`data: ClientProjectsData`, a NamedTuple of `Organization`,
`OrganizationSummary | None`, `list[ProjectsTableData]`, `SummaryVote | None`,
defined in `app_home/operations/project.py:13`).

- **View**: `GET` only (`client_project.py:109`), with
  `@auth_requirements(auth_spec, mode="api")`. Query schema
  `{org_id, author_type, active}`. The handler 404s the org, refetches the
  whole bundle via `get_client_projects_data(user=request.user, ...)`, and
  `render_to_response`s the full card.
- **The client half is hand-rolled**: `get_template_data` builds
  `fragment_url = get_component_url(ClientProject, {org_id, active})`
  (`client_project.py:73`) and stamps it as `data-fragment-url` on the root
  div (`client_project.html:4`). The PillToggle's `js:onChange` walks up to
  the card, parses that URL, sets `author_type=<newValue>` as a query param,
  and `$swap`s the response over the card as outerHTML
  (`client_project.html:27-41`).
- **Events mapping**: this is exactly `@c-bind`-plus-`Events.render`. State is
  `{org_id: int, active: bool, author_type: str | None}` (~50 B); the toggle
  becomes a `$set` on `author_type`; `Events.render` reloads the bundle from
  `self.state` and `self.request` (the user). The auth decorator maps to the
  `guard` config.
- **Rerenderable**: yes. The GET handler is the rebuild recipe, verbatim.
- **State vs kwargs**: not trivial. Kwargs hold the ORM bundle; State holds
  the three scalars the bundle is derived from.

## 2. GoogleCalendarEventAutocomplete

`app_project/components/project_module_events/project_module_events.py:27`

A subclass of the shared `Autocomplete` base component. It defines only
`search_items`; the `View` is **inherited** from the base
(`components/autocomplete/autocomplete.py:91`), and
`get_component_url(self)` resolves per subclass, so each subclass gets its
own public search URL for free (`autocomplete.py:122-124`).

- **View**: `GET`, no auth decorator. Reads `?q=<term>`; below 3 chars
  returns `{items: []}`; otherwise calls the subclass `search_items` and
  returns JSON `{items: [{value, content, disabled}]}` capped at 20.
- **Response shape worth noting**: each item's `content` is **pre-rendered
  HTML** of a sibling display component
  (`GoogleCalendarEventAutocompleteItem.render(..., deps_strategy="ignore")`,
  `project_module_events.py:42-45`). Rich display travels as an HTML string
  inside a JSON payload, not as slots.
- **Events mapping**: a stateless, read-only JSON handler, i.e.
  `@event(methods=("GET",), state="none")` returning a dict (the design's
  "component carries its own mini-API" case, section 3.5's `word_count`
  example). No State, no token, 0 bytes.
- **Also validates**: handler inheritance through component subclassing
  (section 3.1), since the base class defines the endpoint and subclasses
  specialize it by overriding a helper method.
- **Rerenderable**: not applicable. The handler never re-renders the
  autocomplete; it returns JSON that happens to embed rendered HTML of a
  different component per item.

## 3. ProjectModuleEvents

`app_project/components/project_module_events/project_module_events.py:96`

The "Module Events" tab body: an autocomplete multi-select that links Google
Calendar events to a project module, auto-saving on every change.

- **View**: `POST` only (`project_module_events.py:136`), with
  `@auth_requirements`. Body `{event_ids: list[str]}` (ninja `Body`), query
  `{project_id, process_id}` (ninja `Query`). The handler 404s the module,
  validates all ids exist (else `HttpResponseBadRequest("One or more event
  IDs are invalid")`), then `project_module.events.set(found_events)` and
  returns nothing (an ack).
- **Client half**: `get_template_data` bakes
  `update_url = get_component_url(ProjectModuleEvents, query={project_id,
  process_id})` into the form (`project_module_events.py:108-111`); the JS
  component `$fetch`es it on every selection change and drives
  `isSaving` / `Saved!` / error refs by hand
  (`project_module_events.js:10-37`, `project_module_events.html:36-47`).
- **Events mapping**: one handler, `save(event_ids: list[str]) -> None`.
  State is `{project_id: int, process_id: int}` (~40 B); the changed
  selection is a **handler argument** (per-call data), not State. The invalid
  id case is `EventError`. The current URL-with-query-params is a hand-rolled
  unsigned state token.
- **Rerenderable**: yes. `selected_events` (ORM list) and `editable` are
  derivable from the two ids plus `request.user` (the panel's GET already
  does this via `prepare_project_module_data`). Today the client never
  re-renders after save; it trusts the widget's local state.
- **receives_slots**: no. It *fills* slots of the shared `Form` component in
  its own template, but takes none itself.

## 4. ProjectModulePanel

`app_project/components/project_module_panel/project_module_panel.py:44`

The module page's panel body. Renders one of three tab bodies (Info, Outputs,
Module Events) by dispatching on a `tab` kwarg and rendering a child
component to a string with `deps_strategy="ignore"`.

- **View**: `GET` only (`project_module_panel.py:145`), **no auth
  decorator**. Query `{project_id, phase_type, process_id, tab}`. The handler
  calls `prepare_project_module_data(...)` (`app_project/operations.py:518`),
  which 404s project/phase/process, derives `user_is_project_member`, and
  builds the tab-specific ORM bundle; then re-renders the panel with
  `deps_strategy="fragment"`.
- **Kwargs vs endpoint inputs diverge**: kwargs are `{process: Process (ORM),
  preview: bool, tab, tab_data: ModuleTabData}` where `ModuleTabData` is a
  three-variant union of ORM-heavy dataclasses (`operations.py:496-515`).
  The kwargs do not even contain `project_id` or `phase_type`; only the
  endpoint's query params do. A citry State here is a projection of the
  *endpoint's* identifiers, not of the kwargs, which is precisely what the
  `Events.state_data()` override is for (section 3.2), as a plain
  `State(Kwargs)` could not express it.
- **Events mapping**: State `{project_id, phase_type, process_id, tab}`
  (~85 B); the tab switch is one event (or `$set` on `tab` plus the render
  recipe). Multiplexing today is via the `?tab=` query param on a single GET.
- **Rerenderable**: yes; the View handler is the rebuild recipe.

## 5. ProjectModuleTabs

`app_project/components/project_module_tabs/project_module_tabs.py:102`

The module page's tab strip. Pure function of five JSON-safe scalars.

- **View**: `GET` only (`project_module_tabs.py:136`), no auth. Query
  mirrors the kwargs exactly; the handler just re-renders with them.
- **This is the `class State(Kwargs): pass` case**: kwargs
  `{project_id: int, phase_type: enum, process_id: int, tab: enum | None,
  preview: bool}` are already the minimal round-trip state (~100 B).
- **Two-region updates, hand-rolled**: each tab entry's attrs carry three
  URLs (`data-target-url` for the address bar, `data-fragment-url` for the
  panel, `data-tabs-fragment-url` for the strip itself,
  `project_module_tabs.py:66-93`) plus shared click JS that delegates to the
  `project_nav` component (`project_tabs.py:38-44`). One click fetches and
  swaps **both** the panel and the strip. In Events terms this is one
  handler answering with two render ops (`return` plus
  `fx.render(..., target=...)`) or a dispatch the second component listens
  to, plus `push_url`, i.e. the section 3.4 multi-component response,
  currently built by hand out of data attributes.
- **Rerenderable**: yes, trivially.

## 6. ProjectModules

`app_project/components/project_modules/project_modules.py:49`

The module picker: a sortable "selected" list and a static "available" list
of processes, with add/remove per item and drag-to-reorder.

- **View**: `POST` and `PATCH` (`project_modules.py:120`), both with
  `@auth_requirements` plus an explicit `user_is_project_member` check
  returning 403.
  - `POST` is **multiplexed through an `action` query param**:
    `{project_id, phase_type, process_id, action: "add" | "remove"}`
    (`project_modules.py:26-30`). Add also performs Monday.com side effects
    (external API calls to verify and create a board group,
    `project_modules.py:143-166`). Returns the Project as a
    `model_to_dict` JSON via `@json_view` (`app/helpers/view.py`), which the
    caller ignores.
  - `PATCH` reorders: body `{processes: list[str]}`, query
    `{project_id, phase_type}`; loops and saves positions; returns `"OK"`.
- **Who calls it**: the add/remove URLs are baked per item by the child
  `ProjectModulesItem` (`project_modules_item.py:28-45`); the reorder URL is
  baked by this component (`project_modules.py:98-104`) and PATCHed by the
  SortableJS `onMove` callback with the ids read from DOM order
  (`project_modules.js:48-72`).
- **Verb scarcity, demonstrated**: three logical actions had to fit two
  verbs, so add/remove share POST via `?action=` and reorder takes PATCH.
  Named events (`add_module(process_id)`, `remove_module(process_id)`,
  `reorder(process_ids: list[int])`) dissolve the multiplexing.
- **Stale UI after mutation**: after add/remove the item JS only flips a
  Saved! flag (`project_modules_item.js:19-59`); the module does not move
  between lists until a full page load. A citry handler returning
  `self.rerender()` fixes this class of bug structurally.
- **State**: `{project_id, phase_type}` (~45 B); the per-call `process_id`
  and the id ordering are handler args (the DOM is the source of truth for
  order, so args carry the data and State carries the scope).
- **Rerenderable**: yes; the process lists are derivable from the phase
  (`prepare_project_modules_for_phase`, `operations.py:230`), `editable`
  from the user. The slow Monday.com call also makes this a natural
  `@c-loading` consumer.

## 7. ProjectPanel

`app_project/components/project_panel/project_panel.py:39`

The project workbook page's panel body, same pattern as ProjectModulePanel
but with a five-variant tab union (Info, Outcomes, Feedbacks, Risks,
Outputs; `ProjectPanelTabData`, `operations.py:277-283`).

- **View**: `GET` only (`project_panel.py:177`), no auth decorator. Query
  `{project_id, tab}`; the handler rebuilds everything via
  `prepare_project_data(project_id, request.user, tab)` and re-renders with
  `deps_strategy="fragment"`.
- **Kwargs**: `{project: Project (ORM), phase_titles: dict, tab,
  tab_data: <5-way ORM union>}`, including lists of ORM rows and dicts keyed
  by int. None of it could ever be the round-trip token; this is the
  strongest example in the chunk that **State must be separate from
  Kwargs**, since the smallest faithful State is just
  `{project_id: int, tab: str | None}` (~35 B).
- **Rerenderable**: yes; one id plus the user rebuilds all five variants.

## 8. ProjectOutputForm

`app_project/components/project_output_form/project_output_form.py:65`

A per-output form: description textarea, completed checkbox, attachments
editor, Save button.

- **View**: `POST` only (`project_output_form.py:110`), with
  `@auth_requirements` plus a membership check that 403s
  (`project_output_form.py:169-183`). Query
  `{project_id, phase_type, output_id}`; body
  `{completed: bool, description: str, attachments: [{text, url, tags}]}`
  (ninja schema with a validating `UrlField`). The handler updates the
  output, writes activity-log rows, diffs and sets attachments, returns
  `"OK"`.
- **Client half**: the JS collects the native form, hand-converts the
  checkbox (the hidden-input trick at `project_output_form.html:62-70` plus
  `formData.completed.toLowerCase() === "on"` at
  `project_output_form.js:43`), merges in the attachments ref, `$fetch`es,
  then `location.reload()` or navigates to a `data-redirect-url`. Errors go
  to `console.error` only.
- **Events mapping**: one handler,
  `save(completed: bool, description: str, attachments: list[Attachment])`,
  where the form fields are handler args or `@c-bind` State fields, and the
  attachments list is a dataclass-typed arg (section 3.3's dataclass
  binding). State `{project_id, phase_type, output_id, redirect_url}`
  (~110 B with the URL; the URL is needed because success navigates, which
  becomes `self.fx.redirect(self.state.redirect_url)`). Validation failures
  would surface through `EventError.fields` and `@c-error` instead of a
  silent console.
- **Rerenderable**: yes; the output is refetchable by id and `editable`
  derives from the user, so a failed save could re-render with errors
  instead of reloading the page.

## 9. ProjectPhasePanel

`app_project/components/project_phase_panel/project_phase_panel.py:27`

The phase page's panel body: Description and Outputs tabs.

- **View**: `GET` only (`project_phase_panel.py:107`), no auth decorator.
  Query `{project_id, phase_type, tab}`; rebuilds via
  `prepare_project_phase_data` (`operations.py:448`) and re-renders with
  `deps_strategy="fragment"`.
- **Kwargs**: `{project: Project (ORM), phase: ProjectPhase (ORM), tab,
  tab_data: PhaseInfoTabData | PhaseOutputsTabData}`. State is
  `{project_id, phase_type, tab}` (~60 B).
- **Asset note**: declares `class Media: js = ["https://unpkg.com/sortablejs"]`
  (`project_phase_panel.py:28-29`), a third-party script that must ride the
  fragment dependency pipeline when the panel is swapped in. Any Events
  re-render of such a component leans on the same manifest machinery the
  design already commits to (section 2, fragment output).
- **Rerenderable**: yes.

## 10. ProjectPhaseTabs

`app_project/components/project_phase_tabs/project_phase_tabs.py:74`

The phase page's tab strip; the phase-level twin of ProjectModuleTabs.

- **View**: `GET` only (`project_phase_tabs.py:104`), no auth. Query mirrors
  kwargs `{project_id: int, phase_type: enum, tab: enum | None}`.
- **Trivial State(Kwargs)** (~60 B); same three-URLs-per-tab, two-region
  click JS as ProjectModuleTabs (`project_phase_tabs.py:52-67`).
- **Rerenderable**: yes.

---

## Cross-cutting findings for the Events design

1. **Two families cover everything.** Six of ten are GET self-re-render
   fragment endpoints whose handler is literally the design's
   `Events.render` recipe (refetch by ids plus `request.user`, render self).
   Three are POST/PATCH mutations that ack or return incidental JSON and
   never return HTML, leaving the client to fake or skip the update. One is
   a stateless JSON search endpoint.
2. **State is always tiny and never the rendered data.** Every endpoint
   rebuilds ORM bundles from 1 to 4 ids/enums/flags; observed States run
   35 to 110 bytes, orders of magnitude under the 8 KB cap. The
   id-plus-reload pattern the design prescribes (7.1) is already the
   universal practice here, unprompted.
3. **URL-as-unsigned-state-token.** `get_component_url(Cls, query={ids})` is
   called at render time and baked into templates and `data-*` attributes;
   the query string is a hand-rolled, unsigned State. Authorization is
   nonetheless re-checked per call on every mutating handler (membership
   403s), matching the design's "state carries scope, handlers authorize".
4. **Verb scarcity is real.** ProjectModules multiplexes add/remove through
   `?action=` and spends PATCH on reorder; every panel multiplexes N tabs
   through `?tab=`. Named events dissolve both shapes.
5. **The missing client half costs real UX.** Each component hand-rolls
   `$fetch`/`$swap` wiring, per-request `isSaving`/`error` refs, and URL
   data-attributes; two leave the page stale after a successful mutation
   (module add/remove, module events). Tab clicks update two regions via
   three data attributes and shared JS, which is the multi-op response
   (render plus `fx.render(target=...)` plus `push_url`) built by hand.
6. **Guards should default on.** Mutating Views consistently carry
   `@auth_requirements` plus explicit membership checks, but four GET
   fragment Views have no per-view auth at all. Per-endpoint auth is clearly
   deliberate on writes and ad hoc on reads, which supports the design's
   opt-out (inherited, default-on) guard model over per-method decorators.
7. **No slots anywhere.** None of the ten View-bearing components receive
   slot fills; rich per-item display is pre-rendered to HTML strings and
   passed as data (autocomplete items), and panels render children to
   strings inside `get_template_data`. In this codebase, the design's
   slots-vs-rerender restriction (7.6) would never fire.
8. **Handler inheritance is used in anger.** The Autocomplete base defines
   the View once; subclasses override one method and get their own URL. The
   Events design's "handlers inherit through normal subclassing" (3.1) has a
   direct production precedent.
