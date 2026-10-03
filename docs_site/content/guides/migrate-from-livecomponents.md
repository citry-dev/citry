---
title: Migrate from livecomponents
description: Port livecomponents in two safe steps, first keeping server-held State, then choosing signed State component by component.
---

# Migrate from livecomponents

You have livecomponents components whose state lives in Redis, and you want
to move them to Citry without changing how they behave on day one. This
guide shows where each part of a `LiveComponent` goes: its state model, its
commands, and the results a command returns.

You can port in two steps. First, keep component state on the server, as
livecomponents does, and reproduce the current behavior. Later, decide for
each component whether its state can travel through the browser instead.

Commands, their call context, redirects, URL changes, and browser events all
have direct equivalents. What changes most is how the page updates. Citry
does not mark components dirty or find them through a parent id. Each
handler returns the renders it wants, and state holds JSON values, never
pickled objects. Three Citry terms come up throughout:

- [`State`][citry.Component.State] lists the values a later call needs.
  Citry keeps them between calls, either on the server or in the page. See
  [Event state](/events/state/).
- A **handler** is a public method in the component's nested `class Events`.
  The browser calls it by name. See [Server events](/events/).
- An **action** is a value a handler returns to tell the browser what to do
  next, such as `actions.Render` or `actions.Dispatch`. Returning a
  component re-renders it. See [Event actions](/events/actions/).

The Citry examples assume the `citry_app` instance configured in
[Server events](/events/#configure-a-signing-secret-before-using-state)
and these imports:

```python
from typing import Any

from citry import Component
from citry.ext.events import actions
```

## Syntax mapping

| livecomponents | Citry |
|---|---|
| `LiveComponentsModel` | `class State` with typed fields |
| State in Redis | First step: `_storage = "server"`; later, per component, the default signed State |
| `@command` | Public method inside `class Events` |
| `CallContext.state` | A `state` parameter |
| `CallContext.request` | A `request` parameter (`request.native` is the Django request) |
| Command keyword arguments | A `data` parameter with a typed class |
| Implicit `ComponentDirty` | Return a new component or `actions.Render(...)` |
| `ParentDirty` / `ComponentDirty(id)` | `actions.Render(..., target=...)` |
| `TriggerEvents` | `actions.Dispatch(name, detail)` |
| `RedirectPage` | `actions.Redirect(url)` |
| `PushUrl` / `ReplaceUrl` | `actions.PushUrl(url)` / `actions.ReplaceUrl(url)` |
| `parent_id` and component paths | Not needed; use a render target or Dispatch |
| `{% call_command %}` / `hx-post` | `@c-*` attributes, `$sendEvent`, or an event URL |
| htmx, json-enc, and Alpine morph setup | None: Citry loads its own browser code |
| Saved context and template source | Pass every input and slot again on each render |

The sections below show the common rows in context.

## Fix dynamic attributes

When you copy a template over, check its attributes first. Citry leaves an
ordinary attribute value as a literal string, so Django-style braces inside
it produce the wrong URL:

```citry-html
<!-- Wrong in a Citry template: braces are sent to the browser. -->
<a href="{{ command_url }}">Run command</a>
```

Prefix the attribute with `c-`, and Citry evaluates its value as a Python
expression:

```citry-html
<!-- Right: command_url is evaluated during rendering. -->
<a c-href="command_url">Run command</a>
```

The same applies to `action`, `src`, `class`, and any other attribute. Text
between tags still uses `{{ expression }}`. See
[Attributes](/syntax/attributes/#c-dynamic-attributes).

## Step 1: server State

A livecomponents counter declares a Pydantic state model and changes it
through a `CallContext`. The framework marks the component dirty and
re-renders it:

```python
class CounterState(LiveComponentsModel):
    count: int = 0


class Counter(LiveComponent[CounterState]):
    def init_state(self, context: InitStateContext) -> CounterState:
        return CounterState()

    @command
    def increment(self, call_context: CallContext[CounterState]):
        call_context.state.count += 1
```

Copy the state fields into `class State`, and set `_storage = "server"`. The
handler receives the state as its `state` parameter and returns the new
render itself:

```citry
--8<-- "docs_site/snippets/migrate_livecomponents.py:server-state"
```

With `_storage = "server"`, Citry keeps the State values in its cache and
sends the browser a reference instead of a token that holds them.

Two settings need attention in this step:

- **`_public` decides what browser code can read.** Fields listed in
  `_public` still reach the browser, for templates and bindings, even with
  server storage. By default `_public` lists every field, so set it: the
  example lists only `count`. Leave secrets and server-only values out of
  it.
- **The cache must be shared between workers.** The default cache lives in
  one process's memory, which suits development. With several workers,
  configure a shared backend such as Redis so every request finds the same
  State. See [Cache backends](/performance/cache-backends/).

## Step 2: signed State

When a component's State is small, contains no secrets, and holds only JSON
values, remove `_storage` to use the default:

```citry
--8<-- "docs_site/snippets/migrate_livecomponents.py:signed-state"
```

The handler and template stay the same. Citry now sends the State to the
browser with the rendered component, signed so the server can detect a
changed value, and the component no longer needs the cache. `_public` still
decides which fields browser code can read. This example drops it, so its
one field, `count`, stays readable.

Signing does not hide anything: anyone can read the values in the page
source, and you must check them like any other user input. A component with
secrets or large data can stay on `_storage = "server"` for good. You choose
per component, not for the whole application.

## Update several regions

A livecomponents command can mark itself, its parent, or another component
dirty, and the response carries several fragments:

```python
@command
def save(self, call_context: CallContext[TaskState], task_id: int):
    save_task(task_id)
    return [
        ComponentDirty("task-summary"),
        TriggerEvents(
            [Event(name="task-saved", detail={"taskId": task_id})],
        ),
    ]
```

A Citry handler returns the same intent as a list of actions, applied in
order. `actions.Render` with a target updates one named region, and
`actions.Dispatch` fires a browser event for browser code to handle:

```citry
--8<-- "docs_site/snippets/migrate_livecomponents.py:multi-component-result"
```

Mark a region in the template with `<c-mark name="...">`, and target it with
`mark:<name>`. Citry looks the name up in the template of the component whose
handler ran. Return one `actions.Render` per region that changes, next to
each other in the list. See
[Update part of the page](/events/actions/#update-one-part-of-the-page).

Citry has no `parent` or `find_one()` lookup. When Python owns the update,
return a Render with an explicit target. To render into another component,
use `target="render:<id>"`, where the render ID is the value of that
component's `id` in the browser. When another component should react in its
own way, dispatch an event and let that component listen for it.

## Rebuild each render

livecomponents can save a component's state, part of its outer context, and
its template source to rebuild a later render. A Citry handler receives none
of the original inputs or slot content. It builds a new component from its
State, the request, and freshly loaded records:

```python
class Events:
    def refresh(self, state, request):
        task = load_task_for_user(
            task_id=state.task_id,
            user=current_user(request),
        )
        return TaskEditor(task=task)
```

If the new render needs slot content, pass it again in the returned
component. Nothing from an earlier request reappears unless you pass it. See
[Pass every input](/events/state/#pass-every-input-when-a-handler-renders-again).

## Plan for differences

### Store JSON, not pickles

Both storage modes hold JSON values. Citry does not pickle State, component
instances, Django forms, models, or templates. Store a model's id, reload it
in the handler, and raise `EventError` when the row is missing or the user
may not see it.

### Authorize every event

A session id is not permission to act. Check the current user in the host
middleware, in a `_guard` method on `class Events` that runs before each
handler, or in the handler itself. Do it for every event, even when the page
that rendered the component was protected. See
[Authorize every event](/security/#authorize-every-event).

### Files and server push

Citry has no staged file uploads, and the server cannot push updates to the
page. A handler marked `@event(bundle=False)` can return
`actions.Download(...)`; see
[Event actions](/events/actions/).
The [Events migration parity matrix](/guides/events-migration-parity/) lists
what to use instead for each missing feature.

## Finish the port

For the first step, with State on the server, check that:

- State contains every value the next call needs;
- a shared cache is configured when you run several workers;
- every handler returns the render, event, redirect, or data it should; and
- each use of a parent id or saved context has an explicit replacement.

Before switching a component to signed State, also check that:

- its State is small and holds only JSON values;
- none of its values are secret;
- every value the browser can change is validated again in the handler; and
- `_public` lists only the fields browser code needs to read, and `_model`
  only the fields it may change.

[Event state](/events/state/) and [Event actions](/events/actions/) cover
renders in full, and [Security](/security/) covers caching, CSRF, and
checking client input.
