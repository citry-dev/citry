---
title: Events migration parity
url: https://citry.dev/v/0.4.2/guides/events-migration-parity/
description: "Compare Component.View, django-unicorn, Tetra, and livecomponents capabilities with Citry Events delivery status."
---
# Events migration parity

Use this matrix before porting a component that depends on more than basic
clicks, forms, State, and targeted renders. It distinguishes behavior that is
available in current Events code from later candidates and features Citry
intentionally leaves to explicit application code.

The source-specific walkthroughs are:

- [Component.View](/v/0.4.2/guides/migrate-from-component-view/)
- [django-unicorn](/v/0.4.2/guides/migrate-from-django-unicorn/)
- [Tetra](/v/0.4.2/guides/migrate-from-tetra/)
- [livecomponents](/v/0.4.2/guides/migrate-from-livecomponents/)

## Delivery labels

| Label | Meaning |
|---|---|
| **v1** | Shipped and supported now. |
| **v1.x** | A scoped follow-up release; the Citry answer column says whether it is shipped or planned. |
| **v2** | A separate design decision, not a compatibility promise. |
| **Dropped** | Intentionally represented another way or left to application code. |

A dash in a source-framework column means that framework does not supply the
capability as a first-class feature.

## Handlers, routes, and return values

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry answer | Delivery |
|---|---|---|---|---|---|---|
| Callable declaration | HTTP-verb method | Most public methods | `@public` | `@command` | Public method inside nested `Events` | **v1** |
| Explicit allowlist | Overridden verbs | Public by default with exclusions | Decorator | Decorator | Placement in `Events`; underscore methods are private | **v1** |
| Several actions per component | Verb or query multiplexing | Named methods | Named methods | Named commands | One named handler per operation | **v1** |
| HTTP-verb migration | Native model | - | - | - | `ViewEvents` for GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS | **v1** |
| TRACE compatibility | Supported by old view class | - | - | - | No compatibility handler | **Dropped** |
| Custom route pattern | Per component | Fixed message route | Fixed call route | Fixed command route | Fixed per-event, batch, and compatibility routes | **Dropped** |
| Per-operation URL | One class URL | - | - | Command URL tag | `events.url(name)` / `get_event_url(...)` | **v1** |
| Query and fragment URL building | `get_component_url` | - | - | Query-built command URL | `query=` and `fragment=` on the URL builders | **v1** |
| Reverse args for custom paths | Supported | - | - | - | Stable fixed event path needs no reverse args | **Dropped** |
| GET/read handler | Verb method | POST message route | POST call route | POST command route | `@event(methods=("GET",))`; author keeps it read-only | **v1** |
| Raw host request | Django request | Django request | Django request | Django request | Framework-neutral `request`, with `request.native` escape | **v1** |
| Async handler | Host-dependent | - | Async transport internals | - | Native under ASGI; rejected by sync hosts | **v1** |
| Host portability | Django | Django | Django | Django | Django, FastAPI/Starlette, Flask, plain ASGI and WSGI | **v1** |
| Typed input | Manual parsing | Hint-driven call coercion | JS arguments | Body kwargs | One strict `data` schema with field errors | **v1** |
| ORM-primary-key revival | - | Automatic | Object token state | Stored model objects | Load by validated id and authorize explicitly | **Dropped** |
| JSON return to caller | Host response | Return value | Promise result | Execution-result model | `dict` or `actions.Data` resolves the caller promise | **v1** |
| OpenAPI document | - | - | - | - | Deterministic OpenAPI 3.1 CLI output | **v1** |
| Served `openapi.json` | - | - | - | - | Planned HTTP document route | **v1.x** |
| Native form without JavaScript | Manual | Client runtime expected | Client runtime expected | htmx expected | Per-event URL with HTML, redirect, or JSON translation | **v1** |

`ViewEvents` preserves the method-selected route only. Its handler bodies still
move to typed `data`, the neutral request, and Events return values. The
method-only compatibility URL has no dedicated public builder;
`events.url("post")` builds the named `/post` route.

## State, serialization, and later renders

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry answer | Delivery |
|---|---|---|---|---|---|---|
| State declaration | None | Public class attributes | Public/private component attributes | Pydantic state model | Explicit dataclass-shaped `State`, separate from `Kwargs` | **v1** |
| Default storage | Application-owned | Client data plus checksum and cached pickle | Encrypted pickle token | Redis pickle | Full-HMAC signed strict JSON token | **v1** |
| Server-held State | Application-owned | Cached component | - | Default | `_storage = "server"` through `Citry.cache`, strict JSON | **v1** |
| Optional encrypted State | Application-owned | - | Default | Server-held | Optional encrypted token | **v1.x** |
| Browser visibility control | Application-owned | `javascript_exclude` | Public/private split | Server-held | `_public` controls projection, not secrecy; server storage keeps values out of the token | **v1** |
| Client-writable State | Application-owned | Rich public setters | Public attributes | Commands only | `_model` selects writable public fields | **v1** |
| Rich Python values in State | Application-owned | Models and custom objects | Pickled component graph | Pickled/Pydantic values | Strict JSON only | **Dropped** |
| Per-component expiry | Application-owned | Cache policy | Token max age | Page-session TTL | `_max_age` on signed or server State | **v1** |
| Original kwargs on a call | Request code decides | Rehydrated object | Saved component | Stored State/context | Handler receives none; rebuild the tree explicitly | **Dropped** |
| Original fills on a call | Request code decides | Re-rendered template | Saved component | Saved raw template | Supply fills again in the returned fresh tree | **Dropped** |
| Saved page context | Request code decides | Partial framework context | Saved component context | Selected context in store | Reload from request, database, or explicit State | **Dropped** |
| Implicit re-render | No | Yes | Yes by default | Dirty by default | Return a component or Render explicitly; `None` acknowledges | **Dropped** |
| Stateless handler | Natural | Full component state | Basic component variant | Special subclass | Omit `State`; no token is minted | **v1** |
| Mutable undeclared server bag | Natural | Yes | Private pickled attrs | Stored component State | Only declared State survives the call | **Dropped** |
| Pluggable server store | Application-owned | Django cache | Token design | Store and serializer classes | Configure `Citry.cache`; State remains strict JSON | **v1** |

Signed State is tamper-evident, not secret. State held on the server is the v1
choice when a value must not appear in the page token.

## Bindings, Alpine, and DOM updates

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry answer | Delivery |
|---|---|---|---|---|---|---|
| Server event in markup | Handwritten JS/htmx | `unicorn:<event>` | Alpine listener calling method | `hx-post` command | `@c-<dom-event>` | **v1** |
| Local browser event | Handwritten | Handwritten | Ordinary Alpine | Alpine/htmx | Ordinary `@click` / `x-on:*` stays Alpine | **v1** |
| Event arguments | Request fields | Python-like call string | JS arguments | `hx-vals` | One Alpine object expression validated as `data` | **v1** |
| Python call expression on wire | - | Supported | - | - | Named handler plus object data | **Dropped** |
| Property-setter expression | - | Supported | Public Alpine write | - | Named handler or local `$state` write | **Dropped** |
| State/model binding | Handwritten | `unicorn:model` | Public Alpine attrs | Form/htmx | `:c-field` or `:c-field="handler"` | **v1** |
| Nested dotted binding path | Handwritten | Supported | Nested JS objects | Body values | Bind one top-level declared State field | **Dropped** |
| Prevent and stop | Browser/htmx | Modifiers | Alpine modifiers | htmx/Alpine | `.prevent`, `.stop` | **v1** |
| Self, once, key filters | Browser/htmx | Partial | Alpine modifiers | Alpine modifiers | `.self`, `.once`, `.enter`, `.escape` | **v1** |
| Debounce and throttle | Handwritten | Debounce | Decorator chain | htmx modifiers | Binding modifiers and `@event` defaults | **v1** |
| Lazy/custom update event | Handwritten | `.lazy` | Alpine | htmx | `.lazy` and `.on:<event>` | **v1** |
| Deferred State write | Handwritten | `.defer` | Client state | htmx values | `$state` writes and pending two-way updates ride the next call | **v1** |
| Discard pending writes | Handwritten | `.discard` | - | - | Application decides which value to send | **Dropped** |
| Loading UI | Handwritten | Loading directives | Lifecycle/Alpine | htmx indicator | `$loading()` / `$loading(name)` and lifecycle events | **v1** |
| Error UI | Host response | Error context/attrs | Method-error event | HTTP error | `$error()` / `$error(name)`, field map, and error lifecycle event | **v1** |
| Dirty-input indicator | Handwritten | `unicorn:dirty` | Alpine | htmx | Build from Alpine and lifecycle events when needed | **Dropped** |
| Polling | Handwritten | Rich poll object | Application code | htmx | `@c-poll.<time>="handler"`, hidden-tab pause | **v1** |
| Dynamic poll retiming | Handwritten | `PollUpdate` | Application code | htmx | Re-render a different binding or use app code | **Dropped** |
| Viewport trigger | Handwritten | `unicorn:visible` | Alpine/plugin | htmx trigger | IntersectionObserver or Alpine integration | **Dropped** |
| Morph opt-out | Manual | `unicorn:ignore` | Alpine morph controls | `no_morph` helper | Bare `#c-ignore` on an inner plain element | **v1** |
| Stable item identity | Manual ids | Component key | Component id | Path id | `#c-key` within its sibling and depth window | **v1** |
| Single element root | Not required by core | Required | Required | Root attrs required | Supported | **v1** |
| Multi-root component | Supported by core | - | - | - | Logical root group | **v1** |
| Text-only or empty component | Supported by core | - | - | - | Logical rootless range with lifecycle support | **v1** |
| Focus/value/caret preservation | Handwritten | Morph-dependent | Alpine morph rules | Alpine morph | Compatible morph plus keyed identity and pending-write rules | **v1** |
| Self render | Manual response | Automatic full component | Automatic | Dirty component | Return component or `Render(target=None)` | **v1** |
| Target another region | Manual fragment | Partial/parent controls | Client callback | Dirty result | Ordered `Render(target=selector)` actions | **v1** |
| Several target matches | Manual | Partials | - | OOB fragments | One logical mirrored instance with shared State | **v1** |
| Independent target instances | Manual | Component instances | Component instances | Component ids | One Render action per target | **v1** |
| Parent/ancestor command API | Request code | Parent controls | Child-state graph | `CallContext.parent/find_one` | Explicit target Render or Dispatch plus listener | **Dropped** |
| Server-dispatched browser event | Handwritten | Queued JS call | `_dispatch` | `TriggerEvents` | `actions.Dispatch` and DOM/onEvent listener | **v1** |
| Arbitrary server-selected JS call | Handwritten | Allowed call list | Callback path | htmx events | Dispatch data; client-owned code chooses behavior | **Dropped** |
| Browser call outside markup | Fetch | `Unicorn.call` | Generated method | htmx request | `Citry.events.send`, `sendEvent`, `$sendEvent` | **v1** |
| Python lifecycle matrix | View hooks | Hydrate/update/call/render hooks | Component lifecycle | Command lifecycle | Events extension hooks, not per-field callback parity | **Dropped** |
| Browser lifecycle events | Handwritten | Framework events | Tetra events | htmx events | before, after, error, swapped, and stale Events lifecycle | **v1** |
| Fragment assets activate | Manual dependency strategy | Framework runtime | Response bundle list | Manual five-part client setup | Fragment carries dependency, graph, and Events manifests | **v1** |
| Client prerequisite | Application choice | Unicorn JS | Tetra plus Alpine | htmx, json-enc, Alpine, morph, config | Citry-managed runtimes with pinned stock Alpine and morph | **v1** |
| Template-load validation | Limited | Mostly runtime | Mostly runtime | Mostly runtime | Literal event, State, and modifier mistakes fail early | **v1** |
| Slot/fill scope after update | Application-owned | Template re-render | Saved component | Saved template | New fills in the returned tree; Citry graph owns client scope | **v1** |

Citry still uses Alpine. The difference is automatic bundling and a Citry-owned
logical component graph for scope, slots, multi-root groups, and rootless
ranges. State remains under `$state`; it is not flattened into user `x-data`.

## Queueing, transport, and stale responses

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry answer | Delivery |
|---|---|---|---|---|---|---|
| HTTP calls | Native view | Message POST | Call POST | Command POST | Fetch over batch or per-event route | **v1** |
| Pending updates plus calls | Application code | Action queue | Full public data | Command body | Queue batches co-eligible calls and pending State writes | **v1** |
| Opt out of bundling | Application code | - | - | - | `@event(bundle=False)` | **v1** |
| Same-tick global coalescing | Application code | Queue-specific | - | - | Separate later queue optimization | **v2** |
| Stale-response defense | Application code | Epoch | Old-value/focus checks | Session State | Epoch plus optional `latest_wins` | **v1** |
| Call ordering | Host order | Optional serial cache | Client queue | One command, several dirty results | Same-instance order, containment dependencies, sibling parallelism | **v1** |
| Offline replay queue | Application code | - | Shipped | - | Application-specific retry and conflict policy | **Dropped** |
| Custom transport | Custom view | - | HTTP/WS internals | htmx | Public transport registration | **v1** |
| postMessage bridge | Custom code | - | - | - | No built bridge yet; an explicit bridge is planned | **v1.x** |
| WebSocket and server push | Custom code | - | Reactive components | - | Signed-topic WebSocket design decision | **v2** |
| Server-sent events | Custom code | - | - | - | Evaluated with the push decision | **v2** |

## Security, forms, files, and navigation

| Capability | Component.View | django-unicorn | Tetra | livecomponents | Citry answer | Delivery |
|---|---|---|---|---|---|---|
| CSRF | Django middleware | Django middleware | Django middleware | Django header setup | Same-origin floor, host middleware, client token wiring, optional callable | **v1** |
| Authorization hook | Handler code | Endpoint plus handler code | Handler code | Opt-in decorator | Component or handler guard plus handler checks | **v1** |
| Custom payload codec | Host code | - | Framework protocol | JSON/form parsing | Registered payload codec | **v1** |
| Custom return resolver | Host response | Framework return handling | Framework callbacks | Execution result classes | Registered event-result resolver | **v1** |
| Typed form collection | Manual | Model binding | Form components | Body kwargs | Named controls into typed `data` | **v1** |
| Django `form_class` sugar | Manual | Shipped | Form/ModelForm components | - | Convenience integration | **v1.x** |
| Field-error map | Manual | Shipped | `form_errors` | Application code | Schema errors and `EventError.fields` in `$error(name).fieldErrors` | **v1** |
| Error attrs/template tag | Manual | Shipped | Template state | Application code | Render from `$error(name)` explicitly | **Dropped** |
| Multipart upload | Raw request files | Limited | Shipped | Shipped | Built-in multipart to `UploadedFile` | **v1.x** |
| Staged multi-request upload | Application code | - | Temporary files | Upload flow | Single-request multipart is the planned scope | **Dropped** |
| HTTP file response | Native response | - | `FileResponse` | Application response | `RouteResponse` from `@event(bundle=False)` on a per-event HTTP call | **v1** |
| File download action | Handwritten client | - | Shipped | Header result | Shipped per-event `actions.Download` response; batches are rejected | **v1.x** |
| Redirect | Native response | Shipped | Shipped | `RedirectPage` | `actions.Redirect` | **v1** |
| Push/replace history | Host response | Redirect metadata | Shipped | Shipped | Shipped `PushUrl` / `ReplaceUrl` actions | **v1.x** |
| Automatic unchanged-HTML 304 | Host code | Shipped | - | - | Explicit no-action acknowledgement | **Dropped** |
| Automatic dirty-tree deduplication | Host code | Partial logic | Self render | Ancestor dirty-set dedup | Explicit action order is authoritative | **Dropped** |

Setting `csrf=False` disables only Citry's configurable callable token check.
It does not disable the always-on cross-site request floor or independently
configured host middleware, and it does not change which token the browser
runtime sends. State signatures also do not replace authorization: reload and
authorize every record named by State or event data.

## Events v1 acceptance checklist

The migration target is considered v1-complete when all of these remain true:

- protocol examples replay against the Python dispatcher and validate against
  the protocol schema;
- the same event suite passes under WSGI/Django and ASGI/FastAPI hosts;
- host CSRF and per-event middleware are exercised without exempting the
  Events route;
- the counter, debounced live search, and validated form pass through the real
  browser runtime;
- the Component.View form and fragments ports pass through native and runtime
  paths, including fragment JavaScript, CSS, and Alpine activation;
- State visibility, client-input, guard, and CSRF guidance is public; and
- all four migration guides point to this maintained matrix.

For the API and authoring rules, continue with
[Server events](/v/0.4.2/events/) and [Security](/v/0.4.2/security/).