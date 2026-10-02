---
title: Events migration parity
description: Compare Component.View, django-unicorn, Tetra, and livecomponents capabilities with Citry Events delivery status.
---

# Events migration parity

You are porting a component from another server-component library and want
to know: does Citry Events cover what my component relies on, and if not,
what do I do instead? These tables answer that, one capability per row.

Clicks, forms, values kept between calls, and re-rendering part of the page
all map directly. The biggest differences are deliberate: Citry does not
re-render a component automatically after a call, does not keep the
component's original inputs on the server, and stores only plain JSON
between calls. File uploads, server push, and WebSockets are not built in.

For step-by-step ports, start from the guide for your library:

- [Component.View](/guides/migrate-from-component-view/)
- [django-unicorn](/guides/migrate-from-django-unicorn/)
- [Tetra](/guides/migrate-from-tetra/)
- [livecomponents](/guides/migrate-from-livecomponents/)

## Read the tables

Each row names a capability, how each library provides it, what to use in
Citry, and a delivery label:

| Label | Meaning |
|---|---|
| **v1** | Built into Citry Events today. |
| **v1.x** | Not built in. The Events design lists it as a smaller addition after v1. Use the workaround in the Citry column today. |
| **v2** | Not built in. It needs a larger design decision of its own, such as a new transport. Use the workaround in the Citry column, if any. |
| **Dropped** | Citry does this a different way on purpose, or leaves it to your code. The Citry column says how. |

The **v1.x** and **v2** labels describe how big the missing piece is, not a
release date. Plan your port around the workaround.

A dash in a library's column means that library has no built-in feature for
it.

A few Citry terms appear throughout:

- A **handler** is a public method in a component's nested `class Events`.
  Browser code can call it by name.
- **State** holds the values a handler needs on the next call. Citry sends
  them to the browser with the rendered component and gets them back with
  each call.
- A **per-event route** is the URL of one handler. Calls made from
  templates are usually bundled and sent to a shared **batch route** instead.

## Declare handlers

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry | Delivery |
|---|---|---|---|---|---|---|
| Callable declaration | HTTP-verb method | Most public methods | `@public` | `@command` | Public method in nested `Events` | **v1** |
| Explicit allowlist | Overridden verbs | Public by default, with exclusions | Decorator | Decorator | Being in `Events`; underscore methods stay private | **v1** |
| Several actions per component | Verb or query multiplexing | Named methods | Named methods | Named commands | One named handler per operation | **v1** |
| Typed input | Manual parsing | Coerced from type hints | JS arguments | Body kwargs | One strict `data` schema, with field errors | **v1** |
| JSON return to caller | Host response | Return value | Promise result | Execution-result model | `dict` or `actions.Data` resolves the caller's promise | **v1** |
| Raw host request | Django request | Django request | Django request | Django request | Framework-neutral `request`; `request.native` for the host object | **v1** |
| GET (read-only) handler | Verb method | POST only | POST only | POST only | `@event(methods=("GET",))`; you keep it read-only | **v1** |
| Async handler | Host-dependent | - | Async transport internals | - | Native under ASGI; rejected by sync hosts | **v1** |
| Web frameworks | Django | Django | Django | Django | Django, FastAPI/Starlette, Flask, plain ASGI and WSGI | **v1** |
| Per-operation URL | One class URL | - | - | Command URL tag | `events.url(name)` / `get_event_url(...)` | **v1** |
| Query and fragment in URLs | `get_component_url` | - | - | Query-built command URL | `query=` and `fragment=` on the URL builders | **v1** |
| Plain HTML form without JavaScript | Manual | Needs client runtime | Needs client runtime | Needs htmx | Post to the per-event URL; get HTML, a redirect, or JSON | **v1** |
| HTTP-verb handlers | Native model | - | - | - | `ViewEvents` for GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS | **v1** |
| TRACE handler | Supported | - | - | - | No compatibility handler | **Dropped** |
| Custom route pattern | Per component | Fixed message route | Fixed call route | Fixed command route | Fixed per-event, batch, and compatibility routes | **Dropped** |
| Reverse args for custom paths | Supported | - | - | - | Fixed event paths need no reverse args | **Dropped** |
| Load model from primary key automatically | - | Automatic | Object token in state | Stored model objects | Load by validated id and check access yourself | **Dropped** |
| OpenAPI document | - | - | - | - | Deterministic OpenAPI 3.1 from the CLI | **v1** |
| Served `openapi.json` | - | - | - | - | Not served; write it with the CLI and serve the file | **v1.x** |

**HTTP-verb handlers.** `ViewEvents` keeps the route that picks a handler by
HTTP method, so existing URLs keep working. The handler bodies still change:
they read typed `data` and the neutral `request`, and return Events values
instead of host responses. The method-only URL has no public URL builder;
`events.url("post")` builds the named `/post` route instead.

## Keep State across calls

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry | Delivery |
|---|---|---|---|---|---|---|
| State declaration | None | Public class attributes | Public/private attributes | Pydantic state model | Explicit dataclass-like `State`, separate from `Kwargs` | **v1** |
| Default storage | Your code | Client data, checksum, cached pickle | Encrypted pickle token | Redis pickle | Signed strict-JSON token (full HMAC) | **v1** |
| State kept on the server | Your code | Cached component | - | Default | `_storage = "server"` in `Citry.cache`, strict JSON | **v1** |
| Stateless handler | Natural | Full component state | Basic component variant | Special subclass | Omit `State`; no token is created | **v1** |
| Control what the browser reads | Your code | `javascript_exclude` | Public/private split | Server-held | `_public` limits what templates read; it does not hide values | **v1** |
| Client-writable fields | Your code | Public setters | Public attributes | Commands only | `_model` lists the writable public fields | **v1** |
| Per-component expiry | Your code | Cache policy | Token max age | Page-session TTL | `_max_age` on signed or server State | **v1** |
| Pluggable server store | Your code | Django cache | Token design | Store and serializer classes | Configure `Citry.cache`; State stays strict JSON | **v1** |
| Encrypted State token | Your code | - | Default | Server-held | Not built in; keep secret values in server State | **v1.x** |
| Rich Python values in State | Your code | Models, custom objects | Pickled component | Pickled/Pydantic values | Strict JSON only | **Dropped** |
| Undeclared attributes kept on the server | Natural | Yes | Private pickled attrs | Stored State | Only declared State fields survive the call | **Dropped** |
| Original kwargs during a call | Request code decides | Rehydrated object | Saved component | Stored State/context | Not available; pass every input to the returned component | **Dropped** |
| Original slot fills during a call | Request code decides | Template re-render | Saved component | Saved raw template | Pass fills again in the returned component | **Dropped** |
| Saved page context | Request code decides | Partial framework context | Saved component context | Selected context in store | Reload from the request, database, or State | **Dropped** |
| Re-render after every call | No | Yes | Yes, by default | Dirty components | Return a component or `Render`; `None` re-renders nothing | **Dropped** |

!!! warning "Signed State is readable by anyone"

    Signing lets Citry detect a changed token, but anyone can read the
    values in it. Put a value that must stay secret in server State
    (`_storage = "server"`), which keeps it out of the page.

## Bind events

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry | Delivery |
|---|---|---|---|---|---|---|
| Server event in markup | Handwritten JS/htmx | `unicorn:<event>` | Alpine listener calls method | `hx-post` command | `@c-<dom-event>` | **v1** |
| Browser-only event | Handwritten | Handwritten | Alpine | Alpine/htmx | Vue `@click` / `v-on:click` | **v1** |
| Event arguments | Request fields | Python-like call string | JS arguments | `hx-vals` | One Vue object expression, validated as `data` | **v1** |
| Bind an input to State | Handwritten | `unicorn:model` | Public Alpine attrs | Form/htmx | `:c-field` or `:c-field="handler"` | **v1** |
| Prevent and stop | Browser/htmx | Modifiers | Alpine modifiers | htmx/Alpine | `.prevent`, `.stop` | **v1** |
| Self, once, key filters | Browser/htmx | Partial | Alpine modifiers | Alpine modifiers | `.self`, `.once`, `.enter`, `.escape` | **v1** |
| Debounce and throttle | Handwritten | Debounce | Decorator chain | htmx modifiers | Binding modifiers and `@event` defaults | **v1** |
| Lazy or custom update event | Handwritten | `.lazy` | Alpine | htmx | `.lazy` and `.on:<event>` | **v1** |
| Deferred State write | Handwritten | `.defer` | Client state | htmx values | `$state` writes travel with the next call | **v1** |
| Loading indicator | Handwritten | Loading directives | Lifecycle/Alpine | htmx indicator | `$loading()` / `$loading(name)` and lifecycle events | **v1** |
| Error display | Host response | Error context/attrs | Method-error event | HTTP error | `$error()` / `$error(name)`, field errors, error event | **v1** |
| Polling | Handwritten | Poll object | Your code | htmx | `@c-poll.<time>="handler"`; pauses in hidden tabs | **v1** |
| Call from JavaScript | Fetch | `Unicorn.call` | Generated method | htmx request | `Citry.events.send`, `sendEvent`, `$sendEvent` | **v1** |
| Mistakes caught at template load | Limited | Mostly at runtime | Mostly at runtime | Mostly at runtime | Wrong literal event, State, and modifier names fail early | **v1** |
| Python call expression | - | Supported | - | - | Named handler plus object data | **Dropped** |
| Property-setter expression | - | Supported | Public Alpine write | - | Named handler, or a `$state` write | **Dropped** |
| Nested dotted binding path | Handwritten | Supported | Nested JS objects | Body values | Bind one top-level State field | **Dropped** |
| Discard pending writes | Handwritten | `.discard` | - | - | Your code decides which value to send | **Dropped** |
| Dirty-input indicator | Handwritten | `unicorn:dirty` | Alpine | htmx | Build from Vue state and lifecycle events | **Dropped** |
| Change poll interval from server | Handwritten | `PollUpdate` | Your code | htmx | Re-render with a different binding, or use your own code | **Dropped** |
| Run when scrolled into view | Handwritten | `unicorn:visible` | Alpine/plugin | htmx trigger | IntersectionObserver or a Vue integration | **Dropped** |

## Update the page

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry | Delivery |
|---|---|---|---|---|---|---|
| Re-render the calling component | Manual response | Automatic | Automatic | Dirty component | Return the component, or `Render(target=None)` | **v1** |
| Update another part of the page | Manual fragment | Partial/parent controls | Client callback | Dirty result | `Render` with a component or marker as `target` | **v1** |
| Update several parts at once | Manual | Component instances | Component instances | Component ids | One `Render` per target, returned together | **v1** |
| Stable list-item identity | Manual ids | Component key | Component id | Path id | `#c-key` | **v1** |
| Keep focus and typed text | Handwritten | Depends on morph | Alpine morph rules | Alpine morph | Kept for reordered keyed rows and edited inputs | **v1** |
| Keep DOM a JS library manages | Manual | `unicorn:ignore` | Alpine morph controls | `no_morph` helper | `#c-ignore` on an HTML element | **v1** |
| Send a browser event from the server | Handwritten | Queued JS call | `_dispatch` | `TriggerEvents` | `actions.Dispatch` plus a listener | **v1** |
| Browser lifecycle events | Handwritten | Framework events | Tetra events | htmx events | before, after, error, swapped, and stale events | **v1** |
| Inserted HTML runs its JS and CSS | Your dependency setup | Framework runtime | Response bundle list | Manual client setup | Loads its assets and mounts its own Vue app | **v1** |
| Client libraries to install | Your choice | Unicorn JS | Tetra plus Alpine | htmx, json-enc, Alpine, morph, config | None; Citry loads its runtime with a pinned Vue | **v1** |
| Component root shape | Any | One element | One element | One element with root attrs | One element, several, text only, or empty | **v1** |
| Slot fills after an update | Your code | Template re-render | Saved component | Saved template | Pass fills in the returned component | **v1** |
| One target, several matches | Manual | Partials | - | OOB fragments | A target is one component or marker | **Dropped** |
| Call parent or ancestor | Request code | Parent controls | Child-state graph | `CallContext.parent/find_one` | `Render` with a target, or `Dispatch` plus a listener | **Dropped** |
| Server picks a JS function to run | Handwritten | Allowed call list | Callback path | htmx events | `Dispatch` data; browser code decides what to do | **Dropped** |
| Per-field Python lifecycle hooks | View hooks | Hydrate/update/call/render hooks | Component lifecycle | Command lifecycle | Events extension hooks | **Dropped** |
| Skip unchanged HTML (304) | Host code | Built in | - | - | Return `None` to acknowledge without rendering | **Dropped** |
| Merge duplicate re-renders | Host code | Partial logic | Self render | Ancestor dedup | The order of returned actions is what runs | **Dropped** |

**Update several parts at once.** Put the `Render` actions next to each
other in the returned list, one per target. Another action between them, a
`delay`, or `wait=False` makes the call fail.

**Keep focus and typed text.** When keyed rows are reordered, the focused
field keeps its focus, caret, and text. A text field keeps what the user
typed until the server sends a different value.

**Keep DOM a JS library manages.** An HTML element with `#c-ignore` keeps
its server-rendered contents through later renders. On a component tag,
`#c-ignore` raises an error.

**Slot fills after an update.** Each fill keeps the Vue scope of the
template that wrote it.

Each Citry component with browser behavior is a Vue component, so Vue
handles its slots, several root elements, and components that render no
element. State lives under `$state`, separate from the component's own Vue
data.

## Forms, files, URLs

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry | Delivery |
|---|---|---|---|---|---|---|
| Typed form fields | Manual | Model binding | Form components | Body kwargs | Named controls into typed `data` | **v1** |
| Field-error map | Manual | Built in | `form_errors` | Your code | Schema errors and `EventError.fields`, in `$error(name).fieldErrors` | **v1** |
| Redirect | Native response | Built in | Built in | `RedirectPage` | `actions.Redirect` | **v1** |
| Push or replace history | Host response | Redirect metadata | Built in | Built in | `actions.PushUrl` / `actions.ReplaceUrl` | **v1** |
| File download | Handwritten client | - | Built in | Header result | `actions.Download` from a per-event call | **v1** |
| Raw HTTP file response | Native response | - | `FileResponse` | Your response | `RouteResponse` from an `@event(bundle=False)` handler | **v1** |
| Django `form_class` shortcut | Manual | Built in | Form/ModelForm components | - | Not built in; validate the form and raise `EventError` | **v1.x** |
| File upload (multipart) | Raw request files | Limited | Built in | Built in | Not parsed by default; a custom codec can pass `UploadedFile` | **v1.x** |
| Upload across several requests | Your code | - | Temporary files | Upload flow | Not built in; keep it in your code | **Dropped** |
| Error attrs or template tag | Manual | Built in | Template state | Your code | Render from `$error(name)` | **Dropped** |

**File download.** `actions.Download` works only on a per-event call. A
batched call that returns it is rejected, so mark the handler
`@event(bundle=False)`.

**File upload.** Citry's built-in payload codecs do not read
`multipart/form-data`. To accept files now, register a custom payload codec
that turns the uploaded parts into `UploadedFile` values for the handler.

## Secure event calls

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry | Delivery |
|---|---|---|---|---|---|---|
| CSRF | Django middleware | Django middleware | Django middleware | Django header setup | Same-origin check, host middleware, token sent by the client, optional callable | **v1** |
| Authorization | Handler code | Endpoint plus handler code | Handler code | Opt-in decorator | Component or handler guard, plus checks in the handler | **v1** |

**Turning off the CSRF callable.** `csrf=False` turns off only Citry's
configurable token check. The same-origin check always runs, your host's
CSRF middleware still runs, and the browser still sends its token.

**Authorization.** A signed State token proves Citry created it, not that the
user may act on what it names. Load and check access for every record that
State or event data names.

## Send and queue calls

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry | Delivery |
|---|---|---|---|---|---|---|
| HTTP calls | Native view | Message POST | Call POST | Command POST | Fetch to the batch or per-event route | **v1** |
| Send pending writes with a call | Your code | Action queue | All public data | Command body | Pending State writes travel with the next call | **v1** |
| Call order | Host order | Optional serial cache | Client queue | One command at a time | One Vue app sends its calls one at a time, in order | **v1** |
| Ignore stale responses | Your code | Epoch | Old-value/focus checks | Session State | Epoch check, plus optional `latest_wins` | **v1** |
| Send one call on its own | Your code | - | - | - | `@event(bundle=False)` uses the per-event route | **v1** |
| Custom transport | Custom view | - | HTTP/WS internals | htmx | Register a transport | **v1** |
| Custom payload format | Host code | - | Framework protocol | JSON/form parsing | Register a payload codec | **v1** |
| Custom return handling | Host response | Framework return handling | Framework callbacks | Execution result classes | Register an event-result resolver | **v1** |
| postMessage bridge | Custom code | - | - | - | Not built in; register a transport that uses `postMessage` | **v1.x** |
| Combine calls from the same tick | Your code | Queue-specific | - | - | Not built in; each call is sent on its own | **v2** |
| WebSocket and server push | Custom code | - | Reactive components | - | Not built in | **v2** |
| Server-sent events | Custom code | - | - | - | Not built in | **v2** |
| Offline replay queue | Your code | - | Built in | - | Write your own retry and conflict rules | **Dropped** |

## Events v1 acceptance checklist

The Citry project treats Events v1 as complete only while all of these hold.
For a migrator, they are the guarantees you can build on:

- The protocol examples replay against the Python dispatcher and validate
  against the protocol schema, so the wire format matches its spec.
- The same event test suite passes under WSGI/Django and ASGI/FastAPI, so a
  handler behaves the same on either host.
- Host CSRF and per-event middleware run on event calls. You do not need to
  exempt the Events route.
- The counter, debounced live search, and validated form examples pass
  through the real browser runtime.
- The Component.View form and fragments ports pass through both plain HTML
  and the browser runtime, including the JavaScript, CSS, and Vue setup of
  inserted fragments.
- The guidance on State visibility, client input, guards, and CSRF is
  public in [Security](/security/).
- All four migration guides link to this page.

For the full API and authoring rules, continue with
[Server events](/events/) and [Security](/security/).
