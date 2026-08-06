# Component.View audit, chunk 3: project tabs, project users, and the edit pages

Audit of real production `Component.View` usage in the maintainer's work
project (extracted tree under `old-chk/baseapp/`), against the citry Events
design (`docs/design/events.md`, sections 2, 3, 7.1). This chunk covers two
reusable components and seven full pages in `app_project/`, nine files total.

For every component the audit asks: what actions does the View expose, what
data do the handlers actually read, what would the citry Events design need
to round-trip as State, and could an event faithfully re-render the component
from that State alone.

## Method

For each file I read the component `.py`, and where the Python alone did not
show what an action does or how the client consumes it, the referenced
template (`.html`) and component JS (`.js`), plus the shared
`project_nav.js` that drives the tabs fragment. Components without a nested
`View` class are skipped from the schema but noted where they are part of an
action's plumbing.

## The shape of this chunk in one paragraph

Eight of the nine View-bearing components use `View` as a component-scoped
REST endpoint, not as a re-render endpoint: handlers mutate the database,
return a literal `HttpResponse("OK")`, and the client either reloads the
whole page (`window.location.reload()`) or navigates to a redirect URL that
the server computed at render time. Only one component (`ProjectTabs`) uses
its View to re-render itself as an HTML fragment. Actions are multiplexed by
HTTP verb (POST = create, PATCH = update, DELETE = delete) on the single
component URL, with the target record addressed by query params and per-row
action URLs precomputed at render time. Every handler re-fetches and
re-authorizes its models from ids, so the would-be citry State is tiny:
ids and at most one flag, 30 to 65 bytes serialized, on every component here.

This audit calls `$c-props`, an Alpine handler such as `@click`, or a Citry
handler such as `@c-save` or `@c-poll.5s` on a nested `<c-*>` tag a
**component-tag client binding**. The parent owns the expression or server
handler, while the child supplies the component boundary where the browser
applies it. Later references shorten this to “client binding.”

---

## 1. ProjectTabs (component)

File: `app_project/components/project_tabs/project_tabs.py` (View at
lines 120-130).

The row of tab headers on the project workbook page (Info, Client Outcomes,
Client Feedback, Contract Risks, Methodology Outputs). Renders the shared
`TabsStatic` component with precomputed hrefs and the active tab index.

| Field | Value |
|---|---|
| Kind | component |
| Verbs | `get` |
| Actions | Re-render the tab-headers fragment for a given project and active tab (`GET ?project_id&tab`) |
| Multiplexing | none (one verb, one action) |
| Request data | ninja `Query` schema `{project_id: int, tab: ProjectTab enum or None}`. No auth decorator, no `request.user` use (the only handler in this chunk without one). |
| Response | Re-renders itself via `render_to_response` (line 124). The client swaps the HTML into `#proj-tabs-extra-headers` with `$swap` (`project_nav.js:64-73`). |
| Inputs (Kwargs) | `project_id: int`, `tab: ProjectTab or None`. Fully JSON-safe (the enum is a str enum). |
| Receives slots | no |
| State fields | `project_id: int`, `tab: str or None` |
| State ~= Kwargs | yes, `class State(Kwargs): pass` would be exact |
| Est. state bytes | ~40 (`{"project_id":123,"tab":"outcomes"}`) |
| Re-renderable | yes. The GET endpoint already is a state-only rebuild; the query params are exactly the would-be State. |

Notes. This is the one true fragment endpoint in the chunk, and the clearest
"View as a hand-rolled `$refresh`" case. The wiring cost is striking: the
fragment URL for each tab is precomputed by `gen_tabs`
(`project_tabs.py:75-82`) via `get_component_url`, baked into `data-*`
attributes on entries rendered by a *different* component (the tabs), and
fetched by a *third* component's JS (`project_nav.js:40-74`), which also
swaps a second fragment and pushes browser history. Under Events this
collapses to State `{project_id, tab}` with tab switching as `$set` (or a
one-line `select_tab(tab)` handler), and no URL threading through data
attributes.

## 2. ProjectUsers (component)

File: `app_project/components/project_users/project_users.py` (View at
lines 194-248). Template `project_users.html`, JS `project_users.js`.

A section of the project page: a table of user-to-role assignments, an
add-user form, and a delete-confirmation dialog.

| Field | Value |
|---|---|
| Kind | component |
| Verbs | `post`, `delete` |
| Actions | (1) Assign a user to a project role (`POST`, body `{user_id, role}` + `?project_id`); (2) remove a role assignment (`DELETE ?project_id&role_id`) |
| Multiplexing | verb per action on the single component URL; the row to delete is addressed by `?role_id`. One delete URL is precomputed per row (lines 62-65) and passed through row data into the `ProjectUserAction` child, which dispatches an Alpine event carrying it back up to the page-level dialog. |
| Request data | POST: JSON body `CreateProjectRoleInput {user_id: int, role: str}` (role checked by a pydantic `field_validator` against the role enum, then re-checked against assignable roles), query `{project_id}`. DELETE: query `{project_id, role_id}`. Both read `request.user` for authz (`user_can_edit_project`) and carry the `@auth_requirements(mode="api")` decorator. |
| Response | `HttpResponse("OK")` for both (lines 228, 248); the client then does `window.location.reload()` (`project_users.html:33, 63-66`). Never re-renders the fragment. |
| Inputs (Kwargs) | `project_id: int`, `roles_with_users: list[ProjectRole]` (ORM), `available_roles: list[str] or None`, `available_users: list[User] or None` (ORM), `editable: bool` |
| Receives slots | no (it fills the Table component's slots; nothing fills its own) |
| State fields | `project_id: int`, `editable: bool` (the role and user lists get re-derived from the database) |
| State ~= Kwargs | no; kwargs carry ORM lists, State is a reduced derivation |
| Est. state bytes | ~35 |
| Re-renderable | yes, via the id-plus-reload pattern. The POST handler itself already re-derives assignable roles from `project_id` (line 211), so an `Events.render` reload recipe exists in the codebase. |

Notes. "OK" plus full-page reload is this component's substitute for a
fragment re-render. Under Events: `add_user(user_id: int, role: Role)` and
`remove_role(role_id: int)` handlers ending in `self.rerender()`. The
per-row URL precomputation, the `ProjectUserAction` wrapper component whose
whole job is carrying that URL, and the Alpine event binding all exist because
the action cannot take arguments; typed handler args remove the lot.

Skipped in this file (no View): `ProjectUserAction` (line 55, the per-row
trash icon described above), `ProjectAddUserForm` (a Django form, not a
component).

---

## The edit-page family (sections 3 to 9)

Seven pages share one architecture, so it is described once here and each
page below records its specifics.

**Render path.** Each page is rendered by one or two separate
`@view_router.get` function views (create mode and edit mode) that fetch ORM
objects, build layout data, and call `Page.render_to_response`. The View
handlers never render anything; initial render and event handling are
already fully separated code paths.

**Action path.** The View exposes create/update/delete of one resource,
multiplexed by verb on the single component URL, with the record addressed
by query params. `get_template_data` bakes into the page: `save_url` (with
or without the record id), `save_method` (`"POST"` for create, `"PATCH"`
for edit), `delete_url`, and `redirect_url` (the project workbook page with
the right tab preselected). Client-side Alpine assembles the form into JSON,
`$fetch`es `save_url` with `save_method`, and on success sets
`window.location.href = redirectUrl`. Delete confirms in a dialog, sends
DELETE, then navigates the same way. Three pages do this in a dedicated
`.js` file; the note pages inline it in the template
(e.g. `edit_feedback_note.html:18-31, 55-67`).

**Handlers.** Every handler carries `@auth_requirements(mode="api")`,
re-fetches its models with `get_object_or_404` from the query-param ids,
checks `user_is_project_member(request.user, project_id)`, mutates, writes
an activity log entry attributed to `request.user`, and returns
`HttpResponse("OK")`.

**Events translation, common to all seven.** State is the id set from the
query params (30 to 65 bytes). The form content is not State: it lives
client-side until submit and would travel as typed handler args
(`save(text: str, attachments: list[AttachmentInput])`). The success path is
`self.fx.redirect(url)`, not a re-render; these pages are mechanically
re-renderable from State (ids reload everything; layout needs the request,
which handlers have per design section 3.3) but no handler ever wants that.
The three-verb multiplexing becomes three named handlers (`save` covering
create-or-update, or `create`/`update` split, plus `delete`), and the
render-time `save_method` switch disappears.

## 3. ProjectEditFeedbackPage

File: `app_project/pages/edit_feedback/edit_feedback.py` (View at
lines 184-318). Template `edit_feedback.html`, JS `edit_feedback.js`.

| Field | Value |
|---|---|
| Kind | page |
| Verbs | `post`, `patch`, `delete` |
| Actions | create feedback; update feedback; delete feedback |
| Multiplexing | verb per action; create vs update also encoded at render time as `save_method` + `?feedback_id` presence (lines 136-155) |
| Request data | POST/PATCH: query `{project_id, feedback_id?}`, JSON body `{text: str, attachments: [{text, url, tags[]}]}`; DELETE: query `{project_id, feedback_id}`; `request.user` for authz and activity log |
| Response | `HttpResponse("OK")` all three; client navigates to the precomputed `redirect_url` (`edit_feedback.js:53-67, 70-87`) |
| Inputs (Kwargs) | `layout_data: ProjectLayoutData` (rich layout struct), `project: Project` (ORM), `feedback_with_attachments: FeedbackWithAttachments or None` (ORM plus attachment join) |
| Receives slots | no |
| State fields | `project_id: int`, `feedback_id: int or None` |
| State ~= Kwargs | no |
| Est. state bytes | ~40 |
| Re-renderable | yes mechanically (id reload), but handlers only ever redirect; the Events translation is `fx.redirect`, never `rerender` |

Notes. The 97-line JS file exists to (a) hydrate an Alpine attachments array
from server JSON, (b) assemble `{text, attachments}` from the form, and
(c) fetch-then-redirect. Under Events, (b) and (c) are a handler call with
typed args plus `fx.redirect`; (a) remains a legitimate client concern (the
attachments editor is dynamic client state until submit).

## 4. ProjectEditFeedbackNotePage

File: `app_project/pages/edit_feedback_note/edit_feedback_note.py` (View at
lines 169-278). Template only, no JS file; save/delete wired inline with
Alpine (`edit_feedback_note.html`).

| Field | Value |
|---|---|
| Kind | page |
| Verbs | `post`, `patch`, `delete` |
| Actions | create note under a feedback; update note; delete note |
| Multiplexing | verb per action; `?feedback_note_id` presence distinguishes create from update |
| Request data | query `{project_id, feedback_id, feedback_note_id?}`, JSON body `{text: str}`; `request.user` (authz, `modified_by` attribution, activity log) |
| Response | `HttpResponse("OK")`; client navigates to precomputed `redirect_url` |
| Inputs (Kwargs) | `layout_data` (rich), `project` (ORM), `feedback` (ORM), `feedback_note` (ORM or None) |
| Receives slots | no |
| State fields | `project_id: int`, `feedback_id: int`, `feedback_note_id: int or None` |
| State ~= Kwargs | no |
| Est. state bytes | ~65 |
| Re-renderable | yes mechanically (id reload); handlers only redirect |

## 5. ProjectEditOutcomePage

File: `app_project/pages/edit_outcome/edit_outcome.py` (View at
lines 194-337). Same shape as the feedback page (section 3), for
`ProjectOutcome`, with attachments.

| Field | Value |
|---|---|
| Kind | page |
| Verbs | `post`, `patch`, `delete` |
| Actions | create outcome; update outcome; delete outcome |
| Multiplexing | verb per action; render-time `save_method` switch |
| Request data | query `{project_id, outcome_id?}`, JSON body `{text, attachments[]}`; `request.user` |
| Response | `HttpResponse("OK")`; client redirects to the outcomes tab |
| Inputs (Kwargs) | `layout_data`, `project` (ORM), `outcome_with_attachments` (ORM or None) |
| Receives slots | no |
| State fields | `project_id: int`, `outcome_id: int or None` |
| State ~= Kwargs | no |
| Est. state bytes | ~40 |
| Re-renderable | yes mechanically; handlers only redirect |

Notes. The PATCH handler renames the wire field to the model field
(`data["outcome"] = data.pop("text")`, lines 261-264), a small reminder that
these bodies are hand-maintained wire schemas; in Events the handler
signature is the schema and the mapping lives in one visible place.

## 6. ProjectEditOutcomeNotePage

File: `app_project/pages/edit_outcome_note/edit_outcome_note.py` (View at
lines 173-272). Same shape as the feedback-note page (section 4).

| Field | Value |
|---|---|
| Kind | page |
| Verbs | `post`, `patch`, `delete` |
| Actions | create note under an outcome; update note; delete note |
| Multiplexing | verb per action; `?outcome_note_id` presence distinguishes create from update |
| Request data | query `{project_id: int, outcome_id: int, outcome_note_id: int?}` (the only page whose query schema uses plain ints rather than `int | str` unions), JSON body `{text: str or None}`; `request.user` |
| Response | `HttpResponse("OK")`; client redirects |
| Inputs (Kwargs) | `layout_data`, `project` (ORM), `outcome` (ORM), `outcome_note` (ORM or None) |
| Receives slots | no |
| State fields | `project_id: int`, `outcome_id: int`, `outcome_note_id: int or None` |
| State ~= Kwargs | no |
| Est. state bytes | ~65 |
| Re-renderable | yes mechanically; handlers only redirect |

Notes. Rename shim again (`notes` vs `text`, lines 192-193 and 230-232).

## 7. ProjectEditPocsPage

File: `app_project/pages/edit_pocs/edit_pocs.py` (View at lines 300-340).
Template `edit_pocs.html`.

Manage a project's points of contact: a table of current POCs with remove
buttons, a search form over Hubspot contacts, and a results table with add
buttons.

| Field | Value |
|---|---|
| Kind | page |
| Verbs | `post`, `delete` |
| Actions | (1) add a Hubspot contact as a project POC (`POST ?project_id&hubspot_id`); (2) remove a POC (`DELETE ?project_id&hubspot_id`). Contact search is not a View action: it is a separate GET page route (`pocs_search_view`, lines 36-82) that re-renders the whole page with `?query=`, i.e. a full form-submit navigation. |
| Multiplexing | verb per action; the contact is addressed by `?hubspot_id`, with one URL precomputed per row inside the `PocAddButton` / `PocRemoveButton` child components |
| Request data | query `{project_id, hubspot_id}`; `request.user` for authz; no body |
| Response | `HttpResponse("OK")`; the row buttons fetch and then `window.location.reload()` (template strings at lines 139-162 and 218-241) |
| Inputs (Kwargs) | `layout_data`, `project` (ORM), `pocs: list[ProjectPoc]` (ORM), `hubspot_contacts: list[HubspotContact]` (ORM), `query: str or None` |
| Receives slots | no |
| State fields | `project_id: int`, `query: str or None` (POC and contact lists re-derived from the database) |
| State ~= Kwargs | no |
| Est. state bytes | ~45 |
| Re-renderable | yes, id-plus-query reload; today each row action costs a full page reload and each search a full navigation |

Notes. This page is the design doc's LiveSearch example (section 2) plus row
actions: `query` in State driven by `@c-bind.live`, `add_poc(hubspot_id)` /
`remove_poc(hubspot_id)` handlers ending in `self.rerender()`. The two
button wrapper components exist only to carry a precomputed URL and an
inline fetch-and-reload closure; with args on handlers they dissolve into
`@c-click` bindings. (Aside: `PocAddButton` at line 200 has no `@register`
decorator while the template renders `{% component "PocAddButton" %}`, so
registration presumably happens via some auto-discovery; not relevant to
Events, but it shows the wrapper was boilerplate enough to copy-paste
imperfectly.)

Skipped in this file (no View): `PocRemoveButton` (line 120),
`PocAddButton` (line 200), `PocSearchForm` (Django form).

## 8. ProjectEditRiskPage

File: `app_project/pages/edit_risk/edit_risk.py` (View at lines 192-332).
Same shape as the feedback page (section 3), for `ProjectContractRisk`,
with attachments and a JS file.

| Field | Value |
|---|---|
| Kind | page |
| Verbs | `post`, `patch`, `delete` |
| Actions | create risk; update risk; delete risk |
| Multiplexing | verb per action; render-time `save_method` switch |
| Request data | query `{project_id, risk_id?}`, JSON body `{text, attachments[]}`; `request.user` |
| Response | `HttpResponse("OK")`; client redirects to the risks tab |
| Inputs (Kwargs) | `layout_data`, `project` (ORM), `risk_with_attachments` (ORM or None) |
| Receives slots | no |
| State fields | `project_id: int`, `risk_id: int or None` |
| State ~= Kwargs | no |
| Est. state bytes | ~40 |
| Re-renderable | yes mechanically; handlers only redirect |

## 9. ProjectEditRiskNotePage

File: `app_project/pages/edit_risk_note/edit_risk_note.py` (View at
lines 170-277). Same shape as the feedback-note page (section 4).

| Field | Value |
|---|---|
| Kind | page |
| Verbs | `post`, `patch`, `delete` |
| Actions | create note under a risk; update note; delete note |
| Multiplexing | verb per action; `?risk_note_id` presence distinguishes create from update |
| Request data | query `{project_id, risk_id, risk_note_id?}`, JSON body `{text: str}`; `request.user` |
| Response | `HttpResponse("OK")`; client redirects |
| Inputs (Kwargs) | `layout_data`, `project` (ORM), `risk` (ORM), `risk_note` (ORM or None) |
| Receives slots | no |
| State fields | `project_id: int`, `risk_id: int`, `risk_note_id: int or None` |
| State ~= Kwargs | no |
| Est. state bytes | ~60 |
| Re-renderable | yes mechanically; handlers only redirect |

---

## Cross-cutting observations

1. **View is a REST endpoint here, not a re-render endpoint.** 8 of 9
   components never produce HTML from a handler: they return the literal
   string "OK" and rely on the client to reload or navigate. Only
   `ProjectTabs.get` re-renders its component. This validates the Events
   design's premise by absence: with no client half (transport, bindings,
   morph), even a component-oriented codebase falls back to full page
   reloads for every mutation. The `fx.redirect` effect and the
   `rerender()` path each have five-plus direct call sites waiting in this
   chunk alone.

2. **Verb multiplexing is the action namespace, and it is full.** Every
   component maps POST/PATCH/DELETE to create/update/delete on its one URL.
   `ProjectUsers` and `ProjectEditPocsPage` have no free write verb left, so
   a second kind of write action would force a second component or query-param
   dispatch. Named handlers ("any number of named actions per component",
   design section 2) remove the cap. Create-vs-update is decided at render
   time by baking `save_method` into template data, an odd inversion that
   named handlers also erase.

3. **Per-row actions are precomputed URLs threaded through the tree.**
   Because a verb takes no arguments, the row identity must ride in the URL,
   so render time precomputes one `get_component_url(...)` per row and
   threads it via `data-*` attributes, Alpine props, or dedicated wrapper
   components (`ProjectUserAction`, `PocAddButton`, `PocRemoveButton`).
   Typed handler args (`remove_role(role_id: int)`) replace all of it.

4. **The id-plus-reload State pattern is already the practice.** Every
   handler starts from ids in query params, re-fetches with
   `get_object_or_404`, and re-authorizes with a membership check. That is
   exactly design sections 3.3 (handlers fetch and authorize their own
   models) and 7.1 (keep an id in State, reload the rest). Estimated States
   are 30 to 65 bytes, ids plus at most one flag; nothing within two orders
   of magnitude of the 8 KB cap, and no component would need the v1.x
   server-side store.

5. **Auth maps to `guard`.** Every mutating handler wears the same
   `@auth_requirements(auth_spec, mode="api", is_method=True)` decorator
   plus an in-handler project-membership check. A component-level
   `Events.guard` covers the decorator half; the resource-level check stays
   in handlers by design. The one handler without auth (`ProjectTabs.get`,
   a public read-only fragment) matches the
   `@event(methods=("GET",), state="none")`-style escape hatch.

6. **Wire schemas are hand-maintained and stringly.** ninja `Query`/`Body`
   schemas full of `int | str` unions with manual `int(...)` casts (query
   params arrive as strings), pydantic validators for enum membership, and
   field-rename shims (`text` to `outcome`, `text` to `notes`). The Events
   arg-binding layer (str-to-int coercion, Enum annotations, dataclass args;
   design section 3.3) makes the handler signature the schema and deletes
   this layer.

7. **Initial render and event handling are already separate code paths.**
   Pages are rendered by standalone GET function views that build rich ORM
   kwargs; View handlers never see those kwargs. The Kwargs/State split
   formalizes a separation this codebase already lives with, rather than
   imposing a new one.

8. **The family is copy-paste evidence of missing abstraction.** The same
   ~300-line CRUD page appears five times (feedback, outcome, risk, and
   their notes) differing only in model and field names, each with its own
   fetch-then-redirect client code. Under Events the client code disappears
   into `@c-*` bindings plus `fx.redirect`, and the residual handler bodies
   become small enough that a shared base component could parametrize the
   rest.

9. **Exposure is already opt-in.** Every View sets `public = True` (required
   for `get_component_url`). The Events rule "in the class means exposed"
   keeps that property while dropping the flag.
