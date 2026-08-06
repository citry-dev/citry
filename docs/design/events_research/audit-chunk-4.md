# Component.View usage audit, chunk 4

Scope: 9 files from the maintainer's production Django app (`baseapp`), all
`app_project` page components plus the shared `Autocomplete` component. Every
file was read in full, along with its template (`.html`), component JS, and
the `json_view` helper the handlers use. Analysis is against the citry Events
design (`docs/design/events.md`, sections 2, 3, 7.1): for each component I
give the View surface as it exists today, then the minimal citry `State` an
Events port would round-trip.

A shared lifecycle dominates this chunk. Eight of nine components are full
pages following the same shape: a GET view function renders the page; the
page bakes one `get_component_url(...)` (often with ids in the query string)
into template data; client JS (`$fetch`, an in-house helper) sends
JSON to that URL with a verb chosen at render time; the handler mutates the
database and answers with `"OK"` text or a JSON dict; the client then does a
full `window.location` redirect. No mutation in this chunk updates HTML in
place; the only server-rendered update is the one GET fragment endpoint
(component 8).

---

## 1. ProjectEditStatusUpdatePage (page)

Path: `app_project/pages/edit_status_update/edit_status_update.py`

Create/edit form for a project status update. Two GET view functions (create
and edit routes) render the same page with `status_update=None` or a loaded
instance. `get_template_data` picks both the URL and the HTTP verb at render
time: `save_method` is `"POST"` for create, `"PATCH"` for edit, and the
target ids ride in query params baked into `save_url` / `delete_url`. The
companion JS (`edit_status_update.js`) receives `saveUrl`, `saveMethod`,
`redirectUrl`, `deleteUrl` as props and submits `{text, template_id}` from
the form.

- **Verbs**: `post`, `patch`, `delete` (all `public = True`, auth decorator
  plus a `user_is_project_member` check inside each handler).
- **Actions**: create status update; update status update; delete status
  update.
- **Multiplexing**: one component URL; the verb selects the action; target
  ids (`project_id`, `status_update_id`) ride in the query string chosen at
  render. Which verb means which action is template data, not a named
  contract.
- **Request data**: JSON body `{text, template_id}` (POST/PATCH) plus query
  ids; DELETE is query-only; `request.user` for authorization.
- **Response**: plain-text `"OK"` in all three; the client redirects to the
  status-updates list. Never re-renders.
- **Inputs**: `layout_data: ProjectLayoutData` (rich struct), `project`
  (ORM), `templates: list[ProjectStatusUpdateTemplate]` (ORM),
  `status_update` (ORM or None). Pydantic `Kwargs`. No slots received.
- **Citry State**: `project_id: int`, `status_update_id: int | None`
  (~45 B). Exactly what the handlers need; text and template id are handler
  args. `state_data` override required (kwargs are ORM objects, so
  `State(Kwargs)` does not apply).
- **Rerenderable**: yes. All kwargs derive from the two ids plus
  `request.user` (layout, templates list are re-queried). In practice the
  handlers would end in `fx.redirect`, so the re-render path is optional.
- **Notable**: the render-time verb choice (`save_method` prop) is the
  clearest example in this chunk of the verb being data. In Events the
  client would call `save` and `delete` by name and the create/edit split
  would be a `state.status_update_id is None` branch in one handler.

## 2. ProjectBookmarkEditPage (page)

Path: `app_project/pages/project_bookmark_edit/project_bookmark_edit.py`

Create/edit form for a project bookmark with tags. Same render-time URL and
verb wiring as component 1 (`submit_method` is `"POST"` or `"PATCH"`, ids in
the query string, verb read back from a `data-submit-method` attribute in an
inline Alpine handler).

- **Verbs**: `post`, `patch`, `delete`.
- **Actions**: create bookmark; update bookmark and reset its tags; delete
  bookmark and clear its tags.
- **Multiplexing**: one URL; verb selects the action; `project_id` /
  `bookmark_id` in query params baked at render.
- **Request data**: JSON body `{text, url, tags}` plus query ids. The
  `tags` field arrives as a single comma-joined string because the client
  serializes the form with `getFormData(form)`; a Pydantic
  `mode="before"` validator splits it back into a list.
- **Response**: `"OK"`; client redirects to the project page.
- **Inputs**: `layout_data` (rich), `project` (ORM), `tags: list[str]`,
  `bookmark` (ORM or None). No slots received.
- **Citry State**: `project_id: int`, `bookmark_id: int | None` (~40 B).
- **Rerenderable**: yes (kwargs re-derivable from ids; tags re-queried via
  `get_tags`).
- **Notable**: the comma-joined-tags idiom exists only because the wire is
  flattened form data. The Events envelope sends a structured `args` object,
  so a `tags: list[str]` handler parameter would arrive as a real array and
  the before-validator disappears. The same idiom repeats in components 3
  and 4 (shared `_TagsInput`).

## 3. ProjectCreatePage (page)

Path: `app_project/pages/project_create/project_create.py`

Project creation form, including optional Monday.com board creation or
linking. Single action, but the heaviest handler in the chunk: it verifies
board groups and columns via the Monday API, creates the org on the fly,
creates the project, sets tags, then creates or links the board. All
synchronous, several third-party round trips.

- **Verbs**: `post` only.
- **Actions**: create project (plus Monday board create/link side effects).
- **Multiplexing**: none.
- **Request data**: JSON body `{name, org_name, start_date, end_date, tags,
  monday_board_id?, monday_board_new?}` with cross-field date validation;
  `request.user` (per-user Monday client, project owner).
- **Response**: JSON of the created project via `@json_view` (errors become
  `{error, data}` 400s). The client then rewrites a redirect URL by
  replacing a `"00000"` placeholder with the returned id and navigates.
- **Inputs**: `layout_data` (rich), `org` (ORM or None, preselected client),
  `org_options: list[InputOption]`. No slots received.
- **Citry State**: none strictly required (pure create; args carry
  everything, so handlers could be stateless per design 3.2). If server-side
  validation-error re-render is wanted (the ContactForm pattern),
  `org_id: int | None` (~15 B) rebuilds the page.
- **Rerenderable**: yes (org options re-queried, layout from request).
- **Notable**: the placeholder-URL rewrite exists because the redirect
  target needs the new id, which only the server knows after the insert.
  `self.fx.redirect(f"/projects/{project.pk}/...")` computes it where the id
  is born and deletes the client-side string surgery. Also a data point for
  Events being synchronous-friendly: this handler blocks on a third-party
  API and the page hand-rolls an `isSaving` flag, which `@c-loading` covers.

## 4. ProjectEditPage (page)

Path: `app_project/pages/project_edit/project_edit.py`

Project settings page: edit form, a "Migrate to Monday.com" button, a
delete dialog, plus per-phase module pickers (separate `ProjectModules`
components with their own endpoints, out of this chunk).

- **Verbs**: `patch` (migrate), `post` (update), `delete`.
- **Actions**: update project incl. Monday board relink/unlink; migrate
  project to Monday (a distinct business action); delete project with
  manual cascade cleanup of tags across five resource types.
- **Multiplexing**: one URL with `?project_id=`; three unrelated actions
  distinguished only by verb. PATCH is repurposed as "migrate" because the
  View offers exactly one method per verb and update already took POST.
- **Verb drift, observed**: the Python registers migrate under PATCH, but
  the template's migrate button sends `method: 'POST'`
  (`project_edit.html`, the `onClick` handler around lines 175-190), which
  is the update handler's verb, with no body. Nothing in
  `__tests__/test_project.py` pins the migrate verb (no "migrate" hits). I
  cannot run the app to confirm the runtime failure mode, but the two sides
  plainly disagree, and no grep can catch it because the action has no name
  on the wire; the verb is the name, and it appears in two files as
  unrelated string literals. This is the single strongest argument in this
  chunk for named events (`@c-click="migrate"` fails loudly at template
  load if `migrate` does not exist; the design's section 5.1 validation).
- **Request data**: query `{project_id}` on all three; POST adds
  `UpdateProjectInput` (name, org_name, dates, status enum-validated, tags
  comma-hack, Monday fields); `request.user` for edit permission and the
  Monday client. Delete-authorization nuance: the UI shows the delete
  button only to superusers, but the handler checks
  `user_can_edit_project`, a weaker condition. UI gating and handler
  guards are maintained separately; the Events `guard` config would not
  automatically fix this, but one named `delete` handler with its own
  `@event(guard=...)` puts the check next to the action.
- **Response**: JSON project (PATCH/POST via `@json_view`); `"OK"`
  (DELETE); client redirects or reloads.
- **Inputs**: `layout_data` (rich), `project` (ORM), `monday_board` (ORM or
  None), `tags: list[str]`, `phase_entries: list[PhaseEntry]` (NamedTuple
  holding ORM `Process` lists), `editable: bool | None`, `org_options`. No
  slots received.
- **Citry State**: `project_id: int` (~20 B). Everything else (tags,
  phases, org options, editability) re-derives from it plus
  `request.user`.
- **Rerenderable**: yes, from `project_id` alone; the page proves the
  id-plus-reload pattern scales to a large page (seven kwargs, one id).

## 5. ProjectEventEditPage (page)

Path: `app_project/pages/project_event_edit/project_event_edit.py`

Create/edit form for a Google Calendar event tied to a project. Older
component style: `get_context_data` with keyword parameters (no `Kwargs`
class), inline `template` string.

- **Verbs**: `post`, `patch`, `delete`.
- **Actions**: create event (writes to Google Calendar, saves a DB mirror,
  then round-trips again to append an app link to the description); update
  event (both stores); archive event (deletes from GCal, soft-deletes in
  DB).
- **Multiplexing**: one URL; verb selects the action; unlike siblings, the
  target ids (`project_id`, `event_id`) ride in the JSON body, sourced from
  hidden form inputs and JS props. Even DELETE carries a JSON body. Each
  page invented its own addressing channel (query string here, body there);
  there is no framework-level convention.
- **Request data**: JSON body carrying both args and identity: create
  `{project_id, name, description, start_date}`; update adds `event_id`;
  delete `{project_id, event_id}`. Pydantic `extra="forbid"`.
- **Response**: `model_to_dict(db_event)` JSON (create/update); `None`
  (delete); client redirects to the events list.
- **Inputs**: `layout_data` (rich), `project` (ORM), `event`
  (`GoogleCalendarEvent` ORM or None). No slots received.
- **Citry State**: `project_id: int`, `event_id: str | None` (GCal ids are
  ~26-char strings) (~60 B).
- **Rerenderable**: yes (event reloadable by pk).
- **Notable**: the hidden inputs are an unsigned, user-editable state
  channel: the page renders `project_id`/`event_id` into the form and
  trusts them back (the handlers do re-fetch and scope by both ids, which
  is the mitigation). This is exactly the channel the signed State token
  formalizes (design 7.1): same bytes, but tamper-evident and captured
  declaratively instead of via `<input type="hidden">`.

## 6. ProjectModuleCreatePage (page)

Path: `app_project/pages/project_module_create/project_module_create.py`

Create form for a project module (a `Process`), rendered with a Django
`ModelForm` (`{{ form.as_p }}`) including a martor markdown editor pulled in
through `Media.extend`.

- **Verbs**: `post` only.
- **Actions**: create module (Process) under a phase.
- **Multiplexing**: none.
- **Request data**: JSON body `{name, instructions, is_default_module}` plus
  query `{project_id, phase_type}`; membership check via a helper returning
  a `(response, project, phase)` tuple, the manual guard idiom.
- **Response**: `JsonResponse(model_to_dict(process))`; client substitutes
  the id into a `"00000"` placeholder URL and navigates (same idiom as
  component 3).
- **Inputs**: `layout_data` (rich), `project` (ORM), `phase` (ORM),
  `phase_titles: dict`. The rendered Django form object is template data,
  not a kwarg. No slots received.
- **Citry State**: `project_id: int`, `phase_type: str` (~45 B). Today
  these ride in the query string of the baked URL; they are per-instance
  render facts, so in Events they are State, not handler args.
- **Rerenderable**: yes (form object and breadcrumbs rebuild from the two
  State fields).

## 7. ProjectPhaseEditPage (page)

Path: `app_project/pages/project_phase_edit/project_phase_edit.py`

Edit form for a phase template (name plus markdown description). Smallest
mutating page in the chunk.

- **Verbs**: `post` only.
- **Actions**: update phase template.
- **Multiplexing**: none. Note the verb semantics are loose across the
  codebase: this update is a POST, while sibling pages use PATCH for
  updates. With named events the verb stops carrying meaning at all.
- **Request data**: query `{phase_type}` plus JSON body
  `{name, description}`; `user_is_admin` check inside the handler (403).
- **Response**: `"OK"`; client redirects to the phases list.
- **Inputs**: `layout_data` (rich), `phase_template` (ORM),
  `editable: bool | None`. No slots received.
- **Citry State**: `phase_type: str` (~25 B); `editable` re-derives from
  `request.user` at event time (safer than trusting the rendered flag).
- **Rerenderable**: yes.

## 8. ProjectStatusUpdatesPage (page)

Path: `app_project/pages/project_status_updates_page/project_status_updates_page.py`

The one fragment endpoint in the chunk, and the closest real-world match to
the design's LiveSearch example. The page shows a list of status updates
with a search box; Alpine code hand-rolls a 200 ms debounce and calls
`$swap` to replace an inner container's innerHTML with the fetched fragment.

- **Verbs**: `get` only.
- **Actions**: search status updates, returning a rendered HTML fragment of
  the inner list.
- **Multiplexing**: none on the request side; the response shape
  multiplexes: HTML of a different component when there are results, the
  plain string `"No status updates found"` when not. The client swaps
  either into the container blindly.
- **Request data**: GET query `{project_id, editable, q?}`. `editable` is
  client-supplied: the page bakes `is_project_member` into the fragment
  URL as a query param, and the handler passes `query.editable` straight
  into the child render. A user can flip `editable=true` in the URL and
  receive the fragment with edit controls. Not a privilege escalation
  (the mutation endpoints in component 1 re-check membership), but the
  UI-permission flag is client-controlled. Under Events this flag would be
  a State field captured server-side and signed, closing the channel by
  construction (design 7.1).
- **Response**: `ProjectStatusUpdates.render_to_response(...)`, a
  different component. The page class serves purely as the URL anchor for
  its inner region's fragment.
- **Inputs**: `layout_data` (rich), `project` (ORM), `status_updates`
  (ORM list), `is_project_member: bool`, `breadcrumbs` (ORM list or None).
  No slots received.
- **Citry State**: on the component that would own the events, the inner
  `ProjectStatusUpdates`: `project_id: int`, `editable: bool`, `q: str`
  (~45 B, `q` being the `@c-bind.live` field).
- **Rerenderable**: renders-other. The handler responds with a different
  component's HTML. The natural Events port moves State plus
  `Events.render` onto the inner list component
  (`@c-bind.live.debounce.200ms="q"` replaces all the Alpine debounce and
  `$swap` code), leaving the page static; alternatively a page-level
  handler returns the child element, which the design's return contract
  explicitly allows.

## 9. Autocomplete (component)

Path: `components/autocomplete/autocomplete.py`

The one reusable (non-page) View in the chunk: a base autocomplete whose
subclasses override `classmethod search_items(request, term)`. The nested
`View(ComponentView)` resolves the concrete class via `self.component_cls`,
so every registered subclass inherits the endpoint and gets its own URL
(`get_component_url(self)` is the default `endpoint_url` kwarg). Server
enforces `QUERY_MIN_LENGTH` and caps at `MAX_RESULTS`; the 8 KB client JS
handles debounce, keyboard navigation, chips, and fetches
`?q=<term>&<extraParams>` as the user types.

- **Verbs**: `get` only.
- **Actions**: autocomplete search returning JSON items.
- **Multiplexing**: none.
- **Request data**: GET query: the term under a configurable param name
  (default `q`) plus arbitrary `extraParams` merged in by client JS (e.g.
  `project_id` for the Monday board field); `request.user` available to
  `search_items`.
- **Response**: `JsonResponse({"items": AutocompleteItem[]})`; a subclass
  may also return a raw `HttpResponse` that is passed through.
- **Inputs**: all JSON-safe or stringly: `name`, `editable`, `multiple`,
  `placeholder`, `max_width`, `endpoint_url`, `query_param_name`,
  `query_min_length`, `debounce_ms`, `selected_items:
  list[AutocompleteItem]` (TypedDict), `attrs: dict`, `js: dict` (carries
  JS function source strings such as `onChange`). No slots received.
- **Citry State**: none; this is the stateless typed-JSON-handler shape,
  near-verbatim the design's `@event(methods=("GET",), state="none")`
  `word_count` example (section 3.5), including per-subclass handler
  inheritance (section 3.1). 0 B.
- **Rerenderable**: moot; the only handler returns data, never HTML, and
  the dropdown is client-rendered. A State-only rebuild would be possible
  (kwargs are JSON-safe) but no re-render path exists or is wanted.
- **Notable**: config constants (`DEBOUNCE_MS`, `QUERY_MIN_LENGTH`) live on
  the Python class and are shipped to JS as props, showing demand for
  server-declared client behavior, which is what the `@c-*` modifier
  vocabulary and `@event(debounce=...)` encode. The response cap and
  min-length check are server-side guards Events handlers would keep in
  the handler body.

---

## Cross-cutting patterns in this chunk

1. **Mutate-then-redirect is the universal page lifecycle.** 7 of 9
   components never consume HTML from their View; every mutation ends in a
   client-side `window.location` change. An Events port of this chunk is
   mostly `fx.redirect(...)` handlers; the morph/re-render machinery is
   exercised only by the fragment search (8) and hypothetical
   validation-error re-renders. Two pages (3, 6) do the redirect by
   client-side substitution of the created id into a `"00000"` placeholder
   URL, which server-side `fx.redirect` deletes outright.
2. **The ad-hoc state channel already exists, unsigned.** Every page
   round-trips 15-60 bytes of render facts: ids baked into URL query
   strings at render (1, 2, 4, 6, 7, 8), or hidden form inputs echoed back
   in the body (5), and in one case a permission-ish flag (`editable`, 8)
   rides as a client-tamperable query param. This is exactly the channel
   the signed State token formalizes. Observed state sizes are two orders
   of magnitude under the 8 KB cap.
3. **Verb multiplexing degrades at three actions and has no names to
   check.** ProjectEditPage repurposes PATCH as "migrate to Monday", and
   its template's migrate button sends POST; nothing ties the two sides
   together, and no test pins it. Verb semantics also drift across pages
   (update is PATCH in 1, 2, 5 but POST in 4, 7). Named handlers plus
   template-load validation remove the whole class.
4. **`State(Kwargs)` fits zero components here.** Every page State is
   derived ids (the id-plus-reload pattern of design 7.1); the
   `state_data` override with `kwargs.<obj>.pk` would be the norm for page
   components, matching the design's `doc_id` example. The one-line
   spelling is for leaf components, and this chunk's only leaf (9) is
   stateless.
5. **Flattened form data forced server-side workarounds.** The
   comma-joined `tags` before-validator (2, 3, 4) exists only because the
   wire is `FormData`; a structured `args` object makes list-typed handler
   parameters just work.
6. **Auth is per-call, decorator plus in-body checks.** All 18 handlers
   re-authenticate (`@auth_requirements(auth_spec, mode="api")`) and most
   re-authorize against the DB (member/admin/can-edit). Maps directly to
   the Events `guard` config for the repeated decorator plus handler-body
   checks for resource-level rules; note UI gating and handler guards can
   still disagree (4's delete: superuser-only button, can-edit-level
   check).
7. **Responses are five ad-hoc shapes** ("OK" text, bare `JsonResponse`,
   `model_to_dict`, `json_view`-wrapped model-or-error, child-component
   HTML, plus a plain-text empty-result message). The ops envelope
   normalizes all of them into data / render / redirect ops.
