# Component.View usage audit, chunk 1

Audit of real production `Component.View` usage in the maintainer's work
project (the `old-chk` snapshot, a Django + django-components + django-ninja
+ AlpineJS app), read against the citry Events design
(`docs/design/events.md`, sections 2, 3, 7.1). For each component the goal is
to answer: what would this look like under `Component.Events`, what State
would it need to round-trip, and could an event re-render it from State
alone.

## File coverage

| File (under `baseapp/`) | Components with View | Skipped |
|---|---|---|
| `app_attachments/pages/edit_attachment/edit_attachment.py` | EditAttachmentPage | |
| `app_ai_playground/pages/prompt_playground/prompt_playground.py` | PromptPlaygroundPage | |
| `app_hub/pages/hub/hub.py` | none | HubPage (pure display; filtering is URL navigation) |
| `app_integrations/pages/integrations/integrations.py` | IntegrationsPage | |
| `app_process/components/process_tree/process_tree.py` | ProcessTree | |
| `app_process/pages/process_create/process_create.py` | ProcessCreatePage | |
| `app_process/pages/process_step_edit/process_step_edit.py` | ProcessStepEditPage | |
| `app_process/pages/process_steps/process_steps.py` | ProcessStepsPage | |
| `app_project/components/ai_summary_vote/ai_summary_vote.py` | AiSummaryVote | |

Common infrastructure seen across all of them:

- Every View method carries its own
  `@auth_requirements(auth_spec, mode="api", is_method=True)` decorator.
  Auth is opt-in per method; nothing enforces it structurally.
- Most methods also wear `@json_view(name=..., standardized=False)`
  (`app/helpers/view.py`), a hand-rolled response envelope that dumps ORM
  models with `model_to_dict` and catches exceptions into
  `{"error": str(e), "data": None}` with status 400. The `standardized`
  flag exists because the envelope was retrofitted and not all views adopted
  it; every use in this chunk opts out of the standard shape.
- Instance identity always travels as URL query params minted at render
  time with `get_component_url(Comp, query={...})`. This is a hand-rolled
  version of what the Events design puts in the signed State token, minus
  the signing: the ids are user-editable URL text, and every handler
  re-authorizes with `get_object_or_404`.
- The client side is bespoke AlpineJS per page: a `$fetch` helper, manual
  loading/error refs, manual response parsing. No component ever receives
  new HTML back; every mutation ends in `window.location.reload()`, a
  client-side redirect, or a JSON value applied to Alpine state.

---

## EditAttachmentPage

`app_attachments/pages/edit_attachment/edit_attachment.py`, page component
(create/edit form for an attachment). Template `edit_attachment.html`, JS
`edit_attachment.js`.

- **Inputs**: `layout_data: LayoutData` (rich layout object built by the
  no-argument helper `get_layout_data()`), `attachment: AttachmentWithTags |
  None` (wrapper holding an ORM `Attachment` plus its tag list; `None`
  means create mode).
- **View verbs and actions**: classic verb-per-action CRUD on one URL.
  - `post`: create attachment from JSON body `{text, url, tags}`, then set
    tags. Returns `HttpResponse("OK")`.
  - `patch`: update attachment; id from `?attachment_id=` query, body same
    as create. Returns `"OK"`.
  - `delete`: clear tags and delete; id from `?attachment_id=`. Returns
    `"OK"`.
- **Render-time URL minting**: `get_template_data` bakes `save_url`,
  `save_method` (`"POST"` or `"PATCH"`), and `delete_url` into the page, so
  the client JS is told at render time which verb to use. Create vs edit
  mode is effectively state, encoded as a method name string in the HTML.
- **Client behavior**: `edit_attachment.js` collects the Alpine-held
  attachment fields, `$fetch`es to `save_url` with `save_method`, and on
  success sets `window.location.href = redirect_url` (back to the listing
  page). Errors go to `console.error` only.
- **Under Events**: three named handlers (`create`, `update`, `delete_`
  or one `save` switching on `state.attachment_id`), form fields as typed
  handler args, `fx.redirect(...)` replacing the client-side redirect.
  - **State**: `attachment_id: int | None` (derived from the ORM kwarg's
    pk via a `state_data` override). Roughly 25 bytes.
  - **Rerenderable**: yes. No slot fills; `layout_data` comes from a
    no-argument helper and the attachment reloads by id, so an
    `Events.render` reload recipe would be faithful. In practice the
    handlers never re-render today; they ack and the client navigates away.

---

## PromptPlaygroundPage

`app_ai_playground/pages/prompt_playground/prompt_playground.py`, page
component (internal LLM prompt testing tool). Template
`prompt_playground.html`, JS `prompt_playground.js`.

- **Inputs**: `layout_data: LayoutData`, `projects: list[Project]` (ORM
  queryset materialized into select options).
- **View verbs and actions**: two unrelated JSON RPCs, distinguished only
  by verb, on the same URL (`submit_url` and `project_summary_url` are both
  `get_component_url(PromptPlaygroundPage)` with no query):
  - `post`: run an OpenAI summary generation from body `{user_prompt,
    system_prompt, project_summary, status_update}`; returns
    `{"summary": ...}` JSON.
  - `patch`: **a read-only lookup** (fetch the stored latest summary for
    `{project_id}`), returning `{"summary": ...}`. PATCH carries no update
    semantics at all; it is simply the next free verb slot.
- **Client behavior**: Alpine refs for `loading` / `error` / `result`;
  responses update textareas. No HTML ever returned.
- **In-repo prior art**: lines 37 to 128 of this file are a commented-out
  sketch of a `Component.Ninja` extension: named endpoints per component
  (`def load_deps(...)` under a nested `class Ninja:`), registered via
  `on_component_class_created`, with a `get_ninja_url(self, "load_deps")`
  lookup. The maintainer hit the one-method-per-verb ceiling and designed
  named handlers plus URL lookup in situ; this is the direct ancestor of
  the Events design (`events.md` section 2 credits "the old
  Component.Ninja idea").
- **Under Events**: two named stateless handlers, `generate(...) -> dict`
  and `project_summary(project_id: int) -> dict`, both resolving the
  caller's promise with JSON. No State needed (all inputs are explicit
  args; nothing persists between calls).
  - **State**: none; handlers are stateless RPCs. 0 bytes.
  - **Rerenderable**: yes in principle (no slots; projects reload from the
    DB, layout from the helper), but moot: both handlers return JSON data
    and the page never re-renders.

---

## IntegrationsPage

`app_integrations/pages/integrations/integrations.py`, page component
(list of OAuth integrations with connect/disconnect). Template
`integrations.html`, no JS file.

- **Inputs**: `layout_data: LayoutData`, `user_accounts:
  list[SocialAccount]` (allauth ORM rows for the current user).
- **Request-scoped render input**: `get_template_data` requires
  `self.request` (raises without it) because `provider_login_url` needs the
  request and rows are scoped to `request.user`. This is exactly the
  `Events.globals` concern in `events.md` section 7.5: a faithful
  event-time re-render needs per-request values that kwargs do not carry.
- **View verbs and actions**: single action.
  - `delete`: disconnect an integration. Body `{provider_id}`; the row is
    looked up scoped to `request.user`, then deleted. Returns
    `HttpResponse("OK", status=204)`. (The handler also contains ~60 lines
    of commented-out Monday.com API experiments, including leftover
    `set_trace()` calls; the View method doubled as a scratchpad.)
- **Client behavior**: inline Alpine `onDelete(providerId)` posting the
  body, then `window.location.reload()` on success.
- **Under Events**: one handler `disconnect(provider_id: str)`; identity
  comes from the session user, not from state. Returning
  `self.rerender()` would replace the full-page reload, with the rebuild
  reloading accounts from `self.request` (via `Events.globals` or a
  request-reading `render` recipe).
  - **State**: none needed; the only identity is the session user. 0
    bytes.
  - **Rerenderable**: yes, with the caveat that the rebuild depends on the
    request (current user), not on State; the design's per-call globals
    hook covers it. No slots.

---

## ProcessTree

`app_process/components/process_tree/process_tree.py`, reusable component
(drag-and-drop step tree with a per-step context menu). Template
`process_tree.html`, JS `process_tree.js` (SortableJS integration).

- **Inputs**: `step_nodes: list` (rich `ProcessStepNode` objects: ORM step
  plus a `meta` dict of URLs), `editable: bool`, `attrs: dict | None`.
- **Cross-component URL minting**: the per-step `move_url` / `delete_url`
  the tree consumes are minted by the **parent page**
  (`ProcessStepsPage.get_template_data` calls
  `get_component_url(ProcessTree, query={"step_id": ..., "process_id":
  ...})` for every step and stuffs them into `step_node.meta`). The
  component that owns the endpoint does not own the URLs; the parent
  threads them through data. Under Events the URL comes from the component
  class itself, which removes this coupling.
- **View verbs and actions**: verb-per-action, per-step identity in query
  params.
  - `post`: move a step; `?process_id=&step_id=` plus body `{index}`.
    Returns the ORM step as JSON.
  - `delete`: delete a step and clear its template attachments. Returns
    the deleted step as JSON.
- **Silent client/server drift**: the JS move payload sends
  `{parent_id, index}` but the server schema (`MoveProcessStepInput`)
  declares only `index`; ninja silently drops `parent_id`. Either dead
  payload or a lost feature; typed args with unknown-key rejection
  (`events.md` 7.3) would have surfaced it at the first call.
- **Client behavior**: after a successful move or delete,
  `location.reload()`. A drag-and-drop interaction that ends in a full
  page reload is the sharpest "missing client half" evidence in this
  chunk.
- **Under Events**: `move(step_id: int, index: int)` and
  `delete_step(step_id: int)` handlers with `process_id` in State;
  returning a fresh tree element (state holds the process id, render
  reloads the nodes) would morph instead of reloading.
  - **State**: `process_id: int`, `editable: bool`. Roughly 35 bytes.
  - **Rerenderable**: needs-subtargets as written. The component's inputs
    are non-JSON (rich node objects) and, worse, are enriched by the
    parent with URLs derived from the parent's own kwargs and
    `request.build_absolute_uri()` (redirect-back params). A faithful
    State-only rebuild requires moving that data loading and URL building
    into the component; short of that restructuring, events would patch
    regions or fall back to what it does today (reload).

---

## ProcessCreatePage

`app_process/pages/process_create/process_create.py`, page component
(create a "module", i.e. a Process). Template `process_create.html`, no JS
file (logic inline in the template via a `js:onSuccess` prop).

- **Inputs**: `layout_data: LayoutData`, `redirect: str | None`.
- **View verbs and actions**: single action.
  - `post`: create a Process from body `{name, instructions,
    is_default_module, phase_template}` (shared
    `CreateOrUpdateProcessInput` schema); duplicate-name check; returns the
    ORM Process as JSON via `json_view`.
- **The redirect placeholder hack**: because the server cannot redirect (the
  client owns navigation), `get_template_data` pre-renders the eventual
  process URL with a fake id (`{"process_id": "00000"}`), and the template's
  `onSuccess` JS replaces `"00000"` with `response.id` before setting
  `window.location.href`. Under Events the handler creates the process and
  calls `self.fx.redirect(url)` with the real id; the placeholder, the
  dataset attribute, and the JS all disappear.
- **Under Events**: one handler `create(name: str, instructions: str,
  ...)`, ending in `fx.redirect`.
  - **State**: `redirect: str | None` (the only JSON-safe kwarg; the
    override target for where to go after creation). Roughly 50 bytes with
    a URL in it.
  - **Rerenderable**: yes (trivially; no slots, layout from the no-arg
    helper), though the only action always navigates away.

---

## ProcessStepEditPage

`app_process/pages/process_step_edit/process_step_edit.py`, page component
(create/edit a process step, with Monday.com board sync). Template
`process_step_edit.html`, no JS file (submit logic inline in the template).

- **Inputs**: `layout_data: LayoutData`, `process_id: int`, `step:
  ProcessStep | None` (ORM; `None` means create), `submit_url: str`,
  `submit_method: str`, `submit_btn_text: str`, `redirect_url: str | None`,
  `templates: list[TemplateAttachment]` (ORM).
- **Mode as kwargs**: like EditAttachmentPage but more so: the calling view
  computes `submit_url` (with `?process_id=` or `?process_id=&step_id=`)
  and `submit_method` (`"POST"` or `"PATCH"`) and passes them as component
  kwargs; the template writes them into `data-` attributes; the inline JS
  reads them back to know what to call. Three layers ferry what is really
  one bit of state (`step_id` present or not).
- **View verbs and actions**: verb-per-mode.
  - `post`: create step. Query carries `process_id` plus optional
    `position` / `position_step_id` / `redirect` (insert-relative-to-step,
    forwarded from the page URL). Body is the step fields; then a
    Monday.com duplicate-name check across all linked project boards, step
    creation, optional move, attachment sync, and Monday task creation.
    Returns the ORM step as JSON.
  - `patch`: update step (`?process_id=&step_id=`); same body; Monday
    rename/update sync. Returns the ORM step as JSON.
- **Flat-form list encoding**: template attachments arrive as indexed form
  fields (`text_0`, `url_0`, `text_1`, ...) because the form posts flat
  key/value data. The ninja schema uses `extra="allow"` plus a pydantic
  `model_validator` that reaches into `request.POST` to reassemble the
  list (the docstring notes `__pydantic_extra__` was empty at runtime, so
  it grabs the raw request). Under Events the wire is structured JSON, so
  this is one typed arg: `attachments: list[AttachmentInput]`.
- **Client behavior**: inline Alpine `onSubmit` with `isSaving` / `error`
  refs; on success redirect to `redirect_url`; on error show the response
  text.
- **Under Events**: `create(...)` and `update(...)` handlers (or one
  `save`), with the create-position options living in State since they
  arrive with the page URL and persist across the interaction.
  - **State**: `process_id: int`, `step_id: int | None`, `position: str |
    None`, `position_step_id: int | None`, `redirect: str | None`. Roughly
    120 bytes.
  - **Rerenderable**: yes via id-plus-reload (step and attachments reload
    from `step_id`, the Django `ModelForm` rebuilds from the instance); no
    slots. Today both handlers end in a client-side redirect instead.

---

## ProcessStepsPage

`app_process/pages/process_steps/process_steps.py`, page component (view
one process: edit form, clone/delete buttons, and the ProcessTree).
Template `process_steps.html`, JS `process_steps.js`.

- **Inputs**: `layout_data: LayoutData`, `process: Process` (ORM),
  `step_nodes: list[Any]` (rich nodes), `editable: bool`,
  `redirect_on_action: str | None`, `redirect_on_delete: str | None`.
- **View verbs and actions**: the clearest case of verbs as arbitrary RPC
  slots. Three actions, and the verb-to-semantics mapping is scrambled
  because each action simply took the next free method:
  - `post`: **update** the process (body `CreateOrUpdateProcessInput`,
    `?process_id=`; Monday group rename sync). Returns ORM JSON.
  - `delete`: delete the process. Returns the deleted ORM row as JSON.
  - `patch`: **clone** the process. Returns the clone as JSON; the client
    replaces a `"000000"` placeholder in a pre-rendered URL with the
    clone's id and navigates to it (same hack as ProcessCreatePage).
- **Parent doing a child's plumbing**: `get_template_data` mints per-step
  `edit_url` / `delete_url` / `move_url` / `add_step_before_url` /
  `add_step_after_url` into each node's `meta` (the delete/move ones are
  ProcessTree's endpoints), using `self.request.build_absolute_uri()` for
  redirect-back params. Roughly half the method is URL plumbing for
  actions owned elsewhere.
- **Client behavior**: delete goes through a dialog then
  `window.location.href` or `reload()`; update reloads the page; clone
  redirects. No fragment updates anywhere.
- **Under Events**: `update(...)`, `delete_process()`, `clone()` as named
  handlers; clone ends in `fx.redirect` with the real URL; update returns
  `self.rerender()`.
  - **State**: `process_id: int`, `editable: bool`, `redirect_on_action:
    str | None`, `redirect_on_delete: str | None`. Roughly 150 bytes with
    two URLs.
  - **Rerenderable**: yes via id-plus-reload; the page's own calling view
    already demonstrates the recipe (`get_object_or_404(Process, ...)` +
    `get_process_steps_by_process(process_id)`), and the page receives no
    slot fills. The `request.build_absolute_uri()` dependency would move
    into per-call globals.

---

## AiSummaryVote

`app_project/components/ai_summary_vote/ai_summary_vote.py`, reusable leaf
component (thumbs up/down on an AI-generated summary). Template
`ai_summary_vote.html`, no JS file.

- **Inputs**: `owner_id: int` (project or organization id), `initial_vote:
  SummaryVoteValue | None`, `summary_type: SummaryVoteType` (enum),
  `summary_id: int`, `text: str | None`, `attrs: dict | None`. All
  JSON-safe scalars, enums, and a passthrough attrs dict.
- **View verbs and actions**: single action.
  - `post`: record a vote. Identity (`owner_id`, `summary_id`,
    `summary_type`) rides in query params baked into `submit_url` at
    render; the vote value is the body; the user comes from the session.
    The handler re-validates that the owner and summary exist, creates a
    `SummaryVote` row, returns `"OK"`.
- **Client behavior**: the inner `Vote` component updates its own UI
  optimistically; the fetch success/error callbacks are empty. Fire and
  forget.
- **Under Events**: this is the design's Counter-shaped case, one to one:
  `class State(Kwargs)` minus presentation fields, a single
  `vote(value: str | None)` handler reading `self.state`. The
  hand-assembled query-param identity is precisely what the signed token
  carries, with tamper protection the query string version lacks (here
  mitigated by per-call existence checks).
  - **State**: `owner_id: int`, `summary_id: int`, `summary_type: str`.
    Roughly 70 bytes.
  - **Rerenderable**: yes; every kwarg is JSON-safe, no slots, so even a
    full `State(Kwargs)` mirror rebuild would be faithful (about 120
    bytes). Today the handler acks and the client keeps its optimistic
    UI.

---

## Cross-cutting observations

1. **Verb multiplexing degrades into arbitrary RPC slots.** With one method
   per HTTP verb, actions land on whatever verb is free:
   `ProcessStepsPage` uses POST=update, PATCH=clone, DELETE=delete;
   `PromptPlaygroundPage` uses PATCH for a read-only lookup. Verb
   semantics are gone by the second action. Named handlers are the fix the
   codebase is already straining toward.
2. **The maintainer already designed named handlers once.**
   `prompt_playground.py` carries a full commented-out `Component.Ninja`
   extension sketch (named endpoints, class-creation hook, URL lookup by
   handler name), in-repo prior art for `events.md`.
3. **Identity is a hand-rolled, unsigned state token.** Every stateful
   endpoint bakes ids into its URL at render time
   (`get_component_url(query={...})`), then re-authorizes per call. The
   Events State token is this exact pattern with signing, typing, and a
   single home. Observed "state" sizes: 0 to ~150 bytes, all ids, flags,
   and redirect URLs; nothing approaches the 8 KB cap, and every component
   already follows (or trivially maps to) id-plus-reload.
4. **No action ever returns HTML.** Responses are bare `"OK"` or
   `model_to_dict` JSON; success handling is `window.location.reload()`
   (IntegrationsPage, ProcessTree, ProcessStepsPage) or a client redirect
   (the form pages). Even drag-and-drop reorder ends in a full page
   reload. The fragment/morph half of Events addresses a real, universal
   gap, not an edge case.
5. **Server-computed redirects are faked client-side.** Twice
   (ProcessCreatePage, ProcessStepsPage clone), a URL is pre-rendered with
   a placeholder id (`"00000"`) that JS string-replaces from the JSON
   response. `fx.redirect` deletes the hack.
6. **Per-method decorator auth is 100 percent boilerplate.** Every View
   method individually repeats `@auth_requirements(..., is_method=True)`;
   nothing catches a forgotten one. Supports the design's inherit-by-default
   guards (7.4).
7. **Unvalidated extras drift silently.** ProcessTree's client sends
   `parent_id`; the server schema never declared it; ninja drops it without
   error. Strict arg binding (7.3) turns this class of bug into a loud 422.
8. **Request-scoped render inputs are real.** IntegrationsPage cannot
   render without `self.request` (login URLs, current user);
   ProcessStepsPage embeds `request.build_absolute_uri()`. The
   `Events.globals` hook (7.5) is needed for faithful event-time renders
   of exactly these pages.
9. **Structured args beat flat forms.** The `text_0`/`url_0` indexed-field
   reassembly in ProcessStepEditPage (a pydantic validator groping through
   `request.POST`) exists only because the wire is flat form data; JSON
   args make it a typed `list` parameter.
10. **Every page re-implements the same fetch scaffolding.** Loading and
    error refs, `$fetch` config, response parsing, error text extraction:
    30 to 90 lines of Alpine per page for what `@c-*` bindings plus
    promise-resolving handlers provide declaratively.
