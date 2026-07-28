# Actions semantics and public-API packaging: prior-art verification report

Research report for the citry Events design
(`/Users/mac/repos/citry/docs/design/events.md`, sections 3.4 and 4.3).
Each numbered section verifies one open question against current
framework docs and source (checked 2026-07-06) and ends with a
"Conclusion for citry" paragraph. Claims are tagged **documented**
(stated in official docs) or **source-observed** (read from the
framework's shipped source on GitHub); where docs are silent, that is
said explicitly.

Version note: `livewire.laravel.com/docs/<page>` (unversioned) now serves
Livewire 4 docs. Livewire 3 claims below cite the versioned
`/docs/3.x/...` pages where they were verified; where an unversioned URL
appears, the v4 page agrees with v3 on the cited point.

---

## 1. Target multiplicity: what a server-addressed CSS selector does when it matches several elements

### Turbo Streams

- `target` takes a DOM id and addresses exactly one element. Every stream
  action description in the reference reads like "appends ... to the
  container designated by the target dom id" (documented:
  <https://turbo.hotwired.dev/reference/streams>).
- `targets` (plural) takes a CSS selector and applies the action to **all
  matches**. The reference has a dedicated "Targeting Multiple Elements"
  section: "To target multiple elements with a single action, use the
  `targets` attribute with a CSS query selector instead of the `target`
  attribute." The handbook is explicit about plurality: content "will be
  added after the all elements that match 'inputs.invalid_field'"
  (documented: <https://turbo.hotwired.dev/handbook/streams>).
- Source confirms the mechanism: in `src/elements/stream_element.js`, the
  `targetElements` getter resolves `target` via
  `ownerDocument.getElementById(...)` (one element) and `targets` via
  `ownerDocument.querySelectorAll(...)` (all matches, empty list if none)
  (source-observed:
  <https://github.com/hotwired/turbo/blob/main/src/elements/stream_element.js>).
- Why the plural was added: PR #113 ("Allow a single stream response to
  update multiple elements", merged 2021-06-17). The motivating case was
  a page with two identical "Favorite Article" buttons that both need
  updating after one action; requiring one stream element per duplicate
  "adds a bit of friction since all the other code to render the elements
  is identical". DHH shaped the final API: keep `target` id-only and add
  a **separate plural attribute** rather than overloading one
  (<https://github.com/hotwired/turbo/pull/113>). Shipped in
  v7.0.0-beta.8
  (<https://github.com/hotwired/turbo/releases/tag/v7.0.0-beta.8>); the
  feature predates Turbo 7.1, whose release notes do not mention it.

### htmx

- `hx-target` resolves to exactly **one** element. Documented forms: a
  plain CSS selector ("A CSS query selector of the element to target",
  singular), `this`, `closest <sel>`, `find <sel>` ("the first child
  descendant element that matches"), `next`/`previous` (first match
  scanning forward/backward) (documented:
  <https://htmx.org/attributes/hx-target/>). The docs never state
  first-vs-all for a plain selector; the source settles it: `getTarget`
  calls `querySelectorExt`, which is literally
  `querySelectorAllExt(...)[0]`, so a plain selector is **first match
  only** (source-observed:
  <https://github.com/bigskysoftware/htmx/blob/master/src/htmx.js>).
- Out-of-band swaps (`hx-swap-oob`) match **by id** by default: "If not
  [given a selector], the element with an ID matching the new content
  will be swapped" (documented: <https://htmx.org/attributes/hx-swap-oob/>,
  <https://htmx.org/docs/#oob_swaps>).
- One OOB fragment CAN update multiple elements, and this is documented
  verbatim: the value form "any valid `hx-swap` value, followed by a
  colon, followed by a CSS selector" (e.g.
  `hx-swap-oob="beforeend:#table tbody"`), and "If a selector is given,
  **all elements matched by that selector will be swapped**"
  (<https://htmx.org/attributes/hx-swap-oob/>). Source agrees: `oobSwap`
  runs `querySelectorAllExt(...)` and iterates every match; even the
  default id path goes through an all-matches query and yields one
  element only because ids are unique in valid HTML (source-observed,
  `oobSwap` in `src/htmx.js`).
- So htmx is asymmetric: the request target (where the main response
  swaps, chosen client-side) is first-match-only; a **server-addressed**
  OOB fragment with a selector is all-matches.

### Datastar

- The `datastar-patch-elements` SSE event morphs by matching top-level
  fragment elements **by id** by default: "By default, Datastar morphs
  elements by matching top-level elements based on their ID" (documented:
  <https://data-star.dev/reference/sse_events>).
- An optional `selector` line "Selects the target element of the patch
  using a CSS selector". The docs use the singular and are silent on
  multiple matches; the source patches **all matches**:
  `document.querySelectorAll(selector)` then `applyToTargets(...)` over
  every element, with a console warning (`PatchElementsNoTargetsFound`)
  when the selector matches nothing (source-observed:
  <https://github.com/starfederation/datastar/blob/main/library/src/plugins/watchers/patchElements.ts>).

### Comma-union selectors

None of the three documents comma-separated selector lists; support falls
out of the underlying platform API in each case (source-observed):

- Turbo `targets` goes straight into `querySelectorAll`, which accepts
  selector lists natively, so `targets="#a, #b"` updates both.
- htmx's `querySelectorAllExt` splits on top-level commas and re-joins
  plain segments for a native `querySelectorAll`; in `hx-target` the
  union still collapses to `[0]`, in the OOB colon form it swaps all
  matches across the union. The OOB value parser splits on the first `:`
  only, so commas in the selector part are safe.
- Datastar's `selector` goes directly to `document.querySelectorAll`, so
  a comma union patches all matches.

### Summary

| Framework | Mechanism | Multiple matches |
|---|---|---|
| Turbo | `target` (id) | n/a, single via getElementById (documented) |
| Turbo | `targets` (CSS) | all matches via querySelectorAll (documented) |
| htmx | `hx-target` (plain CSS) | first match only (docs silent; source) |
| htmx | `hx-swap-oob` default | by id, effectively single (documented) |
| htmx | `hx-swap-oob` `style:selector` | all matches (documented verbatim) |
| Datastar | patch, no selector | per-fragment by id (documented) |
| Datastar | patch with `selector` | all matches (docs silent; source) |

### Conclusion for citry

The field's converged answer for a **server-addressed** selector is "all
matches": Turbo `targets`, htmx OOB-with-selector, and Datastar
`selector` all iterate `querySelectorAll`. The only first-match case
(htmx `hx-target`) is client-side request configuration, not a
server-pushed address, so it is not the analogous mechanism. For citry's
`css:<selector>` target on the `render` and `event` actions, the
defensible semantics are: apply to **all matches**, document that plainly
(do not leave it source-only the way htmx's hx-target and Datastar do),
and note that comma unions work because the selector is handed to
`querySelectorAll` unmodified. Zero matches should be observable
(Datastar logs a warning; a debug log line plus the `citry:events:*`
lifecycle event covers the same need). citry does not need Turbo's
two-attribute split: the multiplicity is already carried by the address
scheme (`cid:` is single-instance by construction, `css:` is plural),
which delivers the same "the contract says when it can be plural"
property Turbo bought with the separate `targets` attribute.

---

## 2. Redirect terminality and ordering

Version note for this section: Livewire claims verified against the 3.x
docs and the `livewire/livewire` `3.x` branch; htmx against master at
version 2.0.10; LiveView against hexdocs and the `phoenix_live_view`
main branch. All cited source files were read directly.

### Livewire 3

- A redirect is **not terminal in the payload**: `$this->redirect()`
  stores the URL and dehydrate adds it as one more effect
  (`$context->addEffect('redirect', $to)`,
  <https://github.com/livewire/livewire/blob/3.x/src/Features/SupportRedirects/SupportRedirects.php>
  lines 62-65). Dispatched events are added unconditionally as a sibling
  `dispatches` effect with no redirect check at all
  (<https://github.com/livewire/livewire/blob/3.x/src/Features/SupportEvents/SupportEvents.php>
  lines 53-55), and mutated properties still travel in the snapshot.
- **Re-render is skipped by default, and this is source-observed, not
  documented**: `redirect()` calls `skipRender()` unless the
  `render_on_redirect` config flag is set, and that flag is explained
  only in a config-file comment
  (<https://github.com/livewire/livewire/blob/3.x/src/Features/SupportRedirects/HandlesRedirects.php>
  lines 15-17,
  <https://github.com/livewire/livewire/blob/3.x/config/livewire.php>
  line 91). The user-facing pages
  <https://livewire.laravel.com/docs/3.x/redirecting> and
  <https://livewire.laravel.com/docs/3.x/events> say nothing about
  skipped rendering or about combining dispatch with redirect. (The
  redirecting page does document flash-message-then-redirect, but that
  is session state, not a browser event.)
- Client ordering has a subtlety: the redirect effect handler runs
  synchronously (`window.location.href = url`, or `Alpine.navigate` for
  wire:navigate), while dispatches defer through a triple
  `queueMicrotask` that deliberately lands after the morph
  (<https://github.com/livewire/livewire/blob/3.x/js/features/supportRedirects.js>,
  <https://github.com/livewire/livewire/blob/3.x/js/features/supportDispatches.js>
  lines 4-17,
  <https://github.com/livewire/livewire/blob/3.x/js/features/index.js>).
  Assigning `location.href` does not halt the running task, so the
  queued dispatches **do still fire, into the outgoing page** before the
  browser navigates. Practical consequence, confirmed by the community:
  a toast or modal raised by those events is destroyed by the
  navigation; the accepted workaround is session flash plus re-dispatch
  on the destination page
  (<https://github.com/livewire/livewire/discussions/6896>). No
  framework mechanism carries a dispatch across the navigation.

### htmx (2.0.10)

- Documented semantics: `HX-Redirect` does a full-page reload at the new
  location; `HX-Location` navigates "like following a hx-boost link"
  without a full reload (<https://htmx.org/headers/hx-redirect/>,
  <https://htmx.org/headers/hx-location/>,
  <https://htmx.org/reference/#response_headers>). `HX-Trigger` events
  fire "as soon as the response is received"
  (<https://htmx.org/headers/hx-trigger/>). **The docs are silent on the
  interaction**; the only adjacent note is that response headers are not
  processed at all on 3xx status codes.
- Source-observed order in `handleAjaxResponse`
  (<https://github.com/bigskysoftware/htmx/blob/master/src/htmx.js>,
  function starting near line 4804): `htmx:beforeOnLoad`, then
  **HX-Trigger first** (lines 4812-4814), then `HX-Location` (early
  return at line 4828), then `HX-Redirect` (early return at line 4837),
  then `HX-Refresh` (same pattern). Only when no redirect/refresh header
  is present: HX-Push-Url history handling, HX-Retarget/Reswap, the body
  swap, HX-Reselect, and `HX-Trigger-After-Swap` /
  `HX-Trigger-After-Settle` inside the swap callbacks.
- So in htmx the redirect **is terminal for everything except plain
  HX-Trigger**: the body is never swapped, HX-Push-Url and the
  retarget/reswap headers are ignored, and the After-Swap/After-Settle
  triggers never fire (they are only reachable through the swap). All
  silently; there is no `console.warn` in those early-return paths.

### Phoenix LiveView

- **The only framework that documents the combination as a contract**:
  "Events pushed during `push_navigate` (or any redirect) are sent to
  the client before the redirection happens"
  (<https://hexdocs.pm/phoenix_live_view/Phoenix.LiveView.html#push_event/3>;
  the sentence lives in
  <https://github.com/phoenixframework/phoenix_live_view/blob/main/lib/phoenix_live_view.ex>
  lines 832-833).
- Source confirms the mechanism in
  <https://github.com/phoenixframework/phoenix_live_view/blob/main/lib/phoenix_live_view/channel.ex>:
  `maybe_diff` is `socket.redirected || render_diff(...)` (lines
  1005-1007), so **no diff is rendered when a redirect was set** and
  assigns changed in the same `handle_event` never reach the DOM;
  `handle_redirect` then pushes a separate diff containing only the
  pending `push_event` payloads **before** the redirect message, for all
  three redirect kinds (`push_pending_events_on_redirect`, lines
  933-936), after which the LiveView process shuts down. `push_patch` is
  the exception: it stays in the same LiveView and renders a diff
  normally.

### Do any frameworks warn on effects-after-redirect?

No. None of the three logs, raises, or errors. Livewire silently skips
the render and silently fires dispatches into the dying page (users
discover it through lost toasts, discussion #6896 above); htmx silently
discards the body, URL headers, and after-swap triggers; LiveView does
not need to warn about `push_event` because delivery-before-redirect is
a documented guarantee, but changed assigns that never render are
dropped silently there too.

### Conclusion for citry

"Redirect drops everything else" is NOT the field norm, but neither is
"everything applies". The convergent pattern has three parts:
**redirect suppresses the DOM update** (Livewire skips `render()` by
default, htmx never swaps a redirecting response's body, LiveView skips
the diff); **plain events are delivered before navigation, not dropped**
(LiveView as a documented contract, htmx and Livewire by processing
order); and **everything dropped is dropped silently, undocumented
except by LiveView**. For citry's ordered-actions list this maps
directly: actions before a `Redirect` apply in order (a `Dispatch`
fires, a `Data` resolves the caller's promise) and the redirect
navigates last, which makes the design's
`[Dispatch("order-saved"), Redirect(...)]` example in 3.4 the field's
canonical pattern, and citry should write the guarantee down the way
LiveView does rather than leave it source-observed the way Livewire and
htmx do. Two lessons beyond the norm: first, delivery is not usefulness,
so the docs should carry LiveView-camp honesty that a `Dispatch` before
a `Redirect` fires into the outgoing page and any UI it raises dies with
the navigation (the durable pattern is state on the destination page,
Livewire's community workaround). Second, because citry's actions are an
explicit ordered list rather than a header bag, two mistakes the other
frameworks can only normalize silently become statically detectable:
actions after a `Redirect` (unreachable by every framework's behavior)
and a `Render` alongside a `Redirect` (work every framework suppresses).
A debug-mode hint for both, not an error since no framework errors, is
defensible and has no prior art against it. Keep the redirect itself an
ordinary action applied in order, never an early abort of the envelope.

---

## 3. URL history operations

### htmx

Both headers exist as documented siblings with identical value grammar
(a URL, or `false` to suppress the update), and each overrides the
matching client-side attribute:

- `HX-Push-Url`: "allows you to push a URL into the browser location
  history. This creates a new history entry", semantics "as per
  history.pushState()" (<https://htmx.org/headers/hx-push-url/>).
- `HX-Replace-Url`: "replace the current URL in the browser location
  history. This does not create a new history entry", semantics "as per
  history.replaceState()", same-origin required
  (<https://htmx.org/headers/hx-replace-url/>).
- Both are listed side by side in the response-header reference table
  (<https://htmx.org/reference/#response_headers>), mirrored by the
  attribute pair (<https://htmx.org/attributes/hx-push-url/>,
  <https://htmx.org/attributes/hx-replace-url/>).

### Turbo

No stream action manipulates the URL; the stream action list is append,
prepend, replace, update, remove, before, after, refresh (plus morph as
a variant) (<https://turbo.hotwired.dev/reference/streams>).
Push-vs-replace exists as the two **named visit actions**: "advance"
(default) "pushes a new entry onto the browser's history stack using
history.pushState", and "replace" "uses history.replaceState to discard
the topmost history entry", chosen via `data-turbo-action="replace"` or
`Turbo.visit(location, { action: "replace" })`
(<https://turbo.hotwired.dev/handbook/drive>). The server cannot say
"just change the URL" in Turbo; it can only annotate navigations.

### Livewire 3

URL sync is property-driven via `#[Url]`, and the push/replace
distinction is a **boolean flag**: "By default, Livewire uses
history.replaceState() to modify the URL instead of history.pushState()";
`#[Url(history: true)]` switches to push (documented:
<https://livewire.laravel.com/docs/3.x/url>). There is no general
server-issued "set the URL to X" action separate from `#[Url]` binding
and redirects.

### Phoenix LiveView

`push_patch/2` (navigation within the current LiveView) and
`push_navigate/2` (to another LiveView) each carry a `:replace` option:
"the flag to replace the current history or push a new state. Defaults
false", so push is the default
(<https://hexdocs.pm/phoenix_live_view/Phoenix.LiveView.html>). Again a
navigation verb with a boolean, not a standalone URL action.

### Conclusion for citry

All four frameworks expose both push and replace from the
server-controllable surface; the split is shape, not capability. Two
named sibling operations: htmx (HX-Push-Url / HX-Replace-Url) and Turbo
(advance / replace visit actions). One operation plus a boolean: Livewire
(`history: true`) and LiveView (`replace: true`), and notably those two
**disagree on which is the default** (Livewire defaults to replace,
LiveView to push), which is the trap a boolean invites. htmx is the
closest analogue to citry's channel (a server-pushed instruction
detached from navigation), and it chose siblings. citry's current design
already spans both camps cleanly: one `url` wire action with a `mode`
field (4.3) is the compact wire shape, and `PushUrl(url)` and
`ReplaceUrl(url)` as sibling Python constructors over it are the
explicit API shape. Sibling constructors also fit this repo's own
convention of positive names over boolean flags, and they avoid the
default-disagreement trap outright. Ship both as siblings; nothing in
the survey argues for treating replace as a fringe capability, and
htmx's `false` value has no citry analogue to port (it suppresses a
client-side attribute default that citry does not have).

---

## 4. Server-dispatched event naming and audience

### Livewire 3 `dispatch()`

- What lands in the browser is a real DOM **CustomEvent**:
  source-observed in `js/events.js`
  (<https://github.com/livewire/livewire>), which constructs
  `new CustomEvent(name, { bubbles, detail: params })` and dispatches it
  on the component's root element (bubbling to window); `dispatchSelf()`
  dispatches without bubbling and `dispatchGlobal()` targets `window`.
- The name is used **raw**, exactly as given (`post-created` dispatches
  literally `post-created`, no prefix). The `livewire:` prefix exists
  only on Livewire's own lifecycle events (`livewire:init`,
  <https://livewire.laravel.com/docs/3.x/javascript>).
- Interop is a documented goal: "Because it uses browser events under
  the hood, you can also use Livewire's event system to communicate with
  Alpine components or even plain, vanilla JavaScript", and the payload
  is documented on "the event's detail property"
  (<https://livewire.laravel.com/docs/3.x/events>).
- Precision on the documented consumers: the 3.x events page shows
  `Livewire.on('post-created', ...)` and Alpine
  `x-on:post-created="..."` as the JS/DOM consumers; a plain
  `window.addEventListener` example does not appear on that page. Plain
  `addEventListener` works in practice (the event is a bubbling
  CustomEvent, and Livewire's own `on()` is a window listener under the
  hood), but that mechanic is source-observed, not doc-stated.
- Scoping helpers (`dispatch()->self()`, `->to(Component::class)`)
  narrow delivery between components but do not rename events.

### htmx `HX-Trigger`

- Fires events with **exactly the given names**, no prefix, and the
  page's own consumption example is plain DOM:
  `document.body.addEventListener("myEvent", function(evt){...})`
  (documented: <https://htmx.org/headers/hx-trigger/>).
- JSON form supplies the detail payload:
  `HX-Trigger: {"showMessage": {...}}`, "Each property of the JSON
  object ... will be copied onto the details object for the event";
  multiple keys fire multiple events. Timing variants exist as sibling
  headers (`HX-Trigger-After-Settle`, `HX-Trigger-After-Swap`).
- Target and bubbling are documented: "This will trigger myEvent on the
  triggering element and will bubble up to the body." Source-observed:
  `makeEvent` returns
  `new CustomEvent(eventName, { bubbles: true, cancelable: true, composed: true, detail })`.
- Events as the interop surface is a stated design position: "The
  primary integration point between htmx and scripting solutions is the
  events that htmx sends and can respond to"
  (<https://htmx.org/docs/#3rd-party>). Note the contrast htmx itself
  maintains: its own lifecycle events are `htmx:`-prefixed; HX-Trigger
  user events are raw.

### Phoenix LiveView `push_event`

Two documented consumption paths
(<https://hexdocs.pm/phoenix_live_view/Phoenix.LiveView.html#push_event/3>,
<https://hexdocs.pm/phoenix_live_view/js-interop.html>):

1. **Framework-private**: `this.handleEvent("points", payload => ...)`
   inside a phx hook; the raw server-given name, but not a DOM event.
2. **Namespaced window events**: "They can be handled on window via
   addEventListener. A 'phx:' prefix will be added to the event name"
   (`window.addEventListener("phx:highlight", e => ... e.detail ...)`).

So hooks see raw names over a private channel; the DOM exposure exists
but is framework-prefixed. Raw-name DOM interop is not offered.

### Collision guidance

- **LiveView documents it explicitly**: "Events pushed from the server
  via push_event are global and will be dispatched to all active hooks
  on the client who are handling that event. If you need to scope events
  ... then this must be done by namespacing them", with the example
  `push_event("points-#{id}", points)`
  (<https://hexdocs.pm/phoenix_live_view/js-interop.html>).
- Livewire 3 and htmx publish no collision guidance for user event
  names. Their documented example names use hyphenated resource-verb
  style (`post-created`, `showMessage`); the colon form appears in these
  ecosystems only as the frameworks' own system prefixes (`phx:`,
  `htmx:`, `livewire:`). No framework doc formally recommends
  `namespace:event-name` style for user events.

### Conclusion for citry

The converged norm in the Livewire/htmx camp, which is citry's camp, is:
**developer-chosen raw names, dispatched as ordinary bubbling DOM
CustomEvents with the payload on `event.detail`, with the platform event
system as the documented interop surface** (both are literally
`new CustomEvent(name, ...)` in source). LiveView is the deliberate
outlier (private hook channel plus `phx:`-prefixed window events), and
its shape follows from its socket architecture, not from a safety
argument the others accepted. citry's `event` action (raw `name`,
`detail`, bubbling CustomEvent on the target instance's roots or
`document`, consumable by `onEvent` and plain `addEventListener`)
matches the majority design and needs no change; one nuance worth
copying from htmx and Livewire alike is to keep the framework's own
lifecycle events behind the `citry:` prefix (both reserve their prefix
for system events while user events stay raw) and to say so in the docs,
warning or refusing on user dispatch of `citry:*` names. On collisions,
LiveView is the only prior art with written guidance (namespace by
building scope into the name); citry recommending prefixed names like
`todo:added` in its docs goes slightly beyond what Livewire/htmx write
down, but it codifies the same practice LiveView documents and costs
nothing, since names remain raw strings on the wire.

---

## 5. File download / raw-response escape

### Livewire 3: the tunnel

- Downloads from an action are documented first-class: return
  `response()->download(...)` or `->streamDownload(...)` from the action
  and "Livewire will handle the response and trigger the download in the
  browser" (<https://livewire.laravel.com/docs/downloads>).
- How it travels is also documented: "the file's contents are Base64
  encoded, sent to the frontend, and decoded back into binary to be
  downloaded directly from the client" (same page), with the documented
  cost that `streamDownload` "isn't truly streamed".
- Source-observed mechanics: the server captures the returned
  file/streamed response, base64-encodes the contents into a `download`
  effect on the JSON envelope
  (<https://github.com/livewire/livewire/blob/main/src/Features/SupportFileDownloads/SupportFileDownloads.php>);
  the client rebuilds a Blob, creates an object URL, and clicks a hidden
  anchor
  (<https://github.com/livewire/livewire/blob/main/js/features/supportFileDownloads.js>).
  Costs: roughly a third more bytes on the wire and full buffering in
  memory; no true streaming.

### django-unicorn: unsupported, maintainer sketched an escape

Returning a `FileResponse` from an action crashes with "Type is not JSON
serializable: FileResponse"; the still-open issue's maintainer-sketched
fix is a two-step escape (stash the file server-side, return an id in
the JSON, fetch the file over a plain HTTP request)
(<https://github.com/django-commons/django-unicorn/issues/486>). The
practical documented answer today is a redirect to a normal Django
download view.

### Tetra: the escape, shipped

A public component method can return a Django `FileResponse`; per
Tetra's protocol spec the server "returns the file directly to the
browser" as a raw HTTP response with `Content-Disposition: attachment`,
which the client driver detects and hands to the browser
(<https://github.com/tetra-framework/tetra/blob/main/docs/files.md>,
<https://github.com/tetra-framework/tetra/blob/main/docs/development/protocol_specification.md>).

### htmx: downloads go around the ajax channel

htmx has no download support in the swap channel; a
`Content-Disposition` response to an htmx request gets swapped into the
DOM as text (<https://github.com/bigskysoftware/htmx/issues/474>,
<https://github.com/bigskysoftware/htmx/issues/2118>). Maintainer
guidance is a plain anchor, an `HX-Redirect` to a normal endpoint, or
rendering a download link
(<https://github.com/bigskysoftware/htmx/discussions/2741>).

### Other response-customization needs in these channels

- **Cookies**: work in Livewire only because the update call is itself a
  normal HTTP response that Laravel middleware decorates
  (<https://github.com/livewire/livewire/discussions/1787>); in htmx
  they work natively because every request is a real HTTP request. The
  recurring legitimate needs surfaced in issues/discussions: downloads,
  Set-Cookie (auth/session/consent), occasionally a custom status for
  middleware and logging.
- **Cache headers**: essentially absent as a request; event calls are
  POSTs and uncacheable in practice.
- **Custom statuses**: htmx documents status-code behavior on its real
  responses (e.g. 286 stops polling, <https://htmx.org/docs/#polling>);
  the envelope frameworks represent errors inside the JSON instead.
  htmx's HX-* response headers
  (<https://htmx.org/reference/#response_headers>) are themselves a
  header-level side channel that only exists because the response is a
  real HTTP response.

### Conclusion for citry

The field splits into tunnel vs escape, and the escape is the majority
and the better-aged shape: Livewire is the only tunneler (base64 into
the JSON envelope, paying memory and non-streaming for it, documented on
its own page), while Tetra shipped exactly a raw-response escape,
django-unicorn's maintainer independently designed toward one, and htmx
maintainers recommend routing around the ajax channel entirely. The
escape shape also subsumes the other legitimate needs (cookies, custom
statuses, any header) for free, because a real HTTP response carries
them natively. This confirms `RouteResponse(...)` as designed in 3.4: a
per-event-route raw-response escape hatch, HTTP transport only, rejected
with a clear error on the batch endpoint and non-HTTP transports, is
both right and sufficient; citry does not need a download action in the
envelope. One implementation note from the survey: when the event call
arrives over fetch/XHR, the client runtime must itself detect the raw
response (Content-Disposition or content type) and trigger the browser
download (blob plus anchor click, as both Tetra's driver and Livewire's
JS do), because a fetch response never triggers a native download on
its own.

---

## 6. File upload types

### Django Ninja `UploadedFile`

- Declared as `file: UploadedFile = File(...)`; the docs state
  "UploadedFile is an alias to Django's UploadFile" (meaning
  `django.core.files.uploadedfile.UploadedFile`)
  (<https://django-ninja.dev/guides/input/file-params/>). The source is
  slightly stronger than the docs: it is a subclass,
  `class UploadedFile(DjangoUploadedFile)`, adding only pydantic schema
  hooks
  (<https://github.com/vitalik/django-ninja/blob/master/ninja/files.py>).
- Importable from the package root: `from ninja import File,
  UploadedFile` (re-exported in
  <https://github.com/vitalik/django-ninja/blob/master/ninja/__init__.py>).
- Attributes per the docs page: `name`, `size`, `content_type`,
  `content_type_extra`, `charset`, plus sync `read()`,
  `multiple_chunks()`, `chunks()` (all inherited from Django).

### FastAPI `UploadFile`

- `from fastapi import UploadFile`; "FastAPI's UploadFile inherits
  directly from Starlette's UploadFile, but adds some necessary parts to
  make it compatible with Pydantic"
  (<https://fastapi.tiangolo.com/tutorial/request-files/>).
- Attributes per the API reference
  (<https://fastapi.tiangolo.com/reference/uploadfile/>):
  `filename: str | None`, `size: int | None`, `content_type`, `headers`,
  and `file` (the underlying sync file object, a
  `SpooledTemporaryFile`); async methods `read(size)`, `write(data)`,
  `seek(offset)`, `close()`, each run in a threadpool delegating to the
  underlying file. Starlette documents the same surface on its own
  `UploadFile` (<https://www.starlette.io/requests/>).

### Naming and shape comparison

Django core and Django Ninja both say **UploadedFile** (Ninja subclasses
Django's class and keeps the name); FastAPI says **UploadFile**
(Starlette's name). The attribute sets converge on one shape: an
original filename (`name` in Django/Ninja, `filename` in
FastAPI/Starlette), a byte `size`, a `content_type`, and file-like
reading (sync `read()` in Django/Ninja; async `read()` wrapping a sync
`.file` in FastAPI/Starlette).

### Conclusion for citry

Both anchors wrap the host framework's native upload object in a thin
class whose job is validation-system integration, exposed from the
package root under a one-word name. For citry's neutral type, the
`UploadedFile` spelling has the stronger claim in citry's context (it
matches Django core and Django Ninja, and citry's first-party adapters
include Django; FastAPI users will recognize it regardless), and the
minimal converged surface to guarantee across adapters is: a filename
attribute, `size`, `content_type`, and `read()`. The one real design
fork the prior art exposes is sync vs async `read()` (Django/Ninja sync,
FastAPI async); a neutral citry type that fronts either host object
should pin one calling convention explicitly rather than inherit
whichever adapter is underneath, and expose the raw host object (as
FastAPI exposes `.file`) as the escape for the rest.

---

## 7. Public API surface conventions in modern Python libraries

### FastAPI

`fastapi/__init__.py` has **no `__all__`** (a correction to the common
assumption): it marks the ~20 everyday names public via the redundant
alias convention (`from .applications import FastAPI as FastAPI`, etc.)
(<https://github.com/fastapi/fastapi/blob/master/fastapi/__init__.py>).
Implementation modules are plain-named (no underscores). Submodules such
as `fastapi.responses` are documented public import paths in the API
reference (<https://fastapi.tiangolo.com/reference/>,
<https://fastapi.tiangolo.com/reference/responses/>). Operational rule:
a small curated root surface plus documented convenience submodules;
publicness is defined by the reference docs, not underscores or
`__all__`.

### Django

Explicit written policy: "In general, everything covered in the
documentation - with the exception of anything in the internals area -
is considered stable", plus the underscore rule for methods
(<https://docs.djangoproject.com/en/stable/misc/api-stability/>). Public
API lives at deep documented paths, never re-exported to the root
(`django.forms.Form` at exactly that path,
<https://docs.djangoproject.com/en/stable/ref/forms/api/>). Django uses
both depths at once: core subsystems short (`django.forms`,
`django.db.models`), batteries-included add-ons namespaced
(`django.contrib.postgres` and its sub-paths,
<https://docs.djangoproject.com/en/stable/ref/contrib/postgres/>).
Operational rule: docs are the contract, in both directions (documented
means public; undocumented means private even without an underscore).

### Pydantic v2

Layout (<https://github.com/pydantic/pydantic/tree/main/pydantic>): one
underscore package `_internal/` for machinery; plain-named public
modules (`fields.py`, `networks.py`, `types.py`); plain-named lifecycle
packages (`deprecated/`, `experimental/`, `v1/`). The root
`pydantic/__init__.py` defines a large `__all__` (~140 names,
lazy-loaded via module `__getattr__`)
(<https://github.com/pydantic/pydantic/blob/main/pydantic/__init__.py>).
Public submodules are also documented at their deep paths
(`pydantic.fields` reference page,
<https://docs.pydantic.dev/latest/api/fields/>). Honest caveat: no
crisp policy sentence "everything in `pydantic._internal` is private"
exists in the docs; the version-policy page
(<https://docs.pydantic.dev/latest/version-policy/>) covers
compatibility tiers and the `experimental` contract, and the privateness
of `_internal` is carried by the underscore convention itself.

### httpx

The purest underscore form: **every** implementation module is
underscore-prefixed (`_client.py`, `_models.py`, `_transports/`), and
the whole public surface is the root package's `__all__` (75 names)
(<https://github.com/encode/httpx/tree/master/httpx>,
<https://github.com/encode/httpx/blob/master/httpx/__init__.py>). There
are no public submodule paths at all. Works because the API is small;
does not demonstrate how to scale to subsystems.

### SQLAlchemy 2

Root `__init__.py` re-exports a very large Core surface via
`import X as X` aliases, with **no `__all__`**
(<https://github.com/sqlalchemy/sqlalchemy/blob/main/lib/sqlalchemy/__init__.py>);
ORM names live at the documented `sqlalchemy.orm` path. `sqlalchemy.ext.*`
is the strongest extensions-namespace precedent: twelve documented ORM
extensions (<https://docs.sqlalchemy.org/en/20/orm/extensions/index.html>),
with fully production-grade members whose canonical documented imports
are the deep ones (`from sqlalchemy.ext.asyncio import
create_async_engine`,
<https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html>).
Internals stance: docs-as-contract plus targeted in-doc labels ("the
`sqlalchemy.sql.visitors` module is an internal API and is not fully
public", <https://docs.sqlalchemy.org/en/20/core/visitors.html>), and a
gradual retro-fit of underscores onto never-meant-public names recorded
in the 2.x/2.1 changelogs
(<https://docs.sqlalchemy.org/en/21/changelog/changelog_21.html>). That
retro-fit is evidence that skipping underscores early costs more later.

### attrs

Dual namespace: `src/attr` (implementation, with underscore machinery
modules `_make.py`, `_next_gen.py`, and plain public grouping submodules
`validators.py`, `converters.py`, `filters.py`, `setters.py`) plus
`src/attrs` as the modern re-export front door
(<https://github.com/python-attrs/attrs/tree/main/src>). The stance is
documented in prose ("On the core API names",
<https://www.attrs.org/en/stable/names.html>; API reference organized by
namespace, <https://www.attrs.org/en/stable/api.html>). Operational
rule: underscore modules for machinery, plain submodules as documented
public groupings, thin re-export namespace as the recommended entry.

### Short vs deep paths for built-in subsystems

Flask re-exports subsystem entry points as **root names** (`Blueprint`,
`Flask`, `request`), viable only because each subsystem is one or two
classes (<https://github.com/pallets/flask/blob/main/src/flask/__init__.py>).
Deep-namespaced-but-first-class is a well-worn, accepted pattern:
`django.contrib.postgres.search` and
`from sqlalchemy.ext.asyncio import ...` are the canonical imports in
each project's own docs, and no notable user complaints about the path
depth itself surfaced in the search (the recurring friction in both
ecosystems is behavioral, not import spelling). The consistent split
across the survey: short paths for subsystems most users touch
(`django.forms`, `pydantic.fields`), an extensions namespace for opt-in
batteries (`django.contrib.*`, `sqlalchemy.ext.*`); the namespace depth
signals "optional", not "second-class".

### Griffe / mkdocstrings behavior (constrains citry's choice)

- mkdocstrings-python's default `filters` value is `["!^_[^_]"]`: render
  everything except single-underscore members, keeping dunders. So
  underscore-prefixed modules and members disappear from the docs build
  with zero configuration
  (<https://mkdocstrings.github.io/python/usage/configuration/members/>).
- The same page documents `filters: public`: include only objects "added
  to the `__all__` attribute of modules, or not starting with a single
  underscore". So `__all__` is honored, but as a union with
  non-underscore names, and only in `public` mode. The loose claim
  "griffe follows `__all__` by default" is not accurate: by default only
  the underscore filter applies.
- Griffe's own guidance endorses using **both** conventions together
  (underscore prefixes for naming, `__all__` for declaring), and
  recognizes redundant aliases (`import X as X`) as a publicness signal
  while advising against relying on that alone
  (<https://mkdocstrings.github.io/griffe/guide/users/recommendations/public-apis/>).

### Conclusion for citry

Three defensible policies, in decreasing fit. **(A) httpx/pydantic
style**: underscore internals (a `citry/_internal/` package scales
better than per-file prefixes), curated `__all__` in `citry/__init__.py`,
each extension's public face in `citry/extensions/<name>/__init__.py`
with its own `__all__`. Griffe renders the contract mechanically with
zero curation; refactors inside `_internal` are provably safe; the cost
is one-time module renames. **(B) Django style, docs-as-contract with no
underscore renaming**: zero code churn and the strongest single
precedent, but it fights citry's toolchain, because griffe cannot read a
policy page, so hiding internals from the rendered reference becomes
hand-maintained per-module curation forever; Django affords this only
because its reference is hand-written prose. For a griffe-driven site
this is the weakest option. **(C, recommended) the hybrid pydantic and
attrs converged on, which is also what griffe's own guidance endorses**:
underscore names for internals, root `__all__` for the everyday surface,
and plain documented deep paths for subsystems, with
`citry.extensions.<name>` kept as the extensions' public import path on
the `sqlalchemy.ext.*` / `django.contrib.*` precedent (depth signals
opt-in, not second-class, and no evidence surfaced that users resent
those paths). Add the one Django-style policy paragraph to the docs:
public means importable from `citry` or from a documented `citry.*` path
with no leading underscore anywhere in the path. The remaining open
choice inside (C) is whether a core subsystem most users touch ever
earns a short path (`django.forms`-style) while extensions keep the deep
one; every surveyed library with both everyday and opt-in surfaces made
exactly that split, so promoting an extension to a short path later is
a well-trodden move, not a rupture.
