---
title: Migrate from livecomponents
url: https://citry.dev/v/0.4.4/guides/migrate-from-livecomponents/
description: "Port livecomponents in two safe steps, first keeping server-held State, then choosing signed State component by component."
---
# Migrate from livecomponents

If a livecomponents page depends on Redis-held state and path-shaped component
ids, moving state and hierarchy at the same time creates unnecessary risk.
Citry supports a two-step port: first keep State on the server and reproduce
the current behavior, then choose signed browser-held State separately for
each component.

Both steps use strict JSON schemas and named handlers. Neither requires
pickling component instances, saving template source, or manually threading a
parent id through every child.

The Citry examples assume the configured `citry_app` from
[Server events](/v/0.4.4/events/#configure-a-signing-secret-before-using-state)
and these imports:


```python
from typing import Any

from citry import Component
from citry.ext.events import actions
```


## Step one: keep State on the server

A livecomponents counter declares a Pydantic state and mutates it through a
`CallContext`. The framework marks the component dirty and re-renders it:


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


Port the state fields directly, set `_storage = "server"`, and narrow
`_public` to the fields that may appear in the browser. The handler now returns
the fresh render explicitly:


```citry
class ServerCounter(Component):
    citry = citry_app

    class Kwargs:
        count: int = 0

    class State(Kwargs):
        _storage = "server"
        _public = ("count",)

    class Events:
        def increment(self, state):
            state.count += 1
            return ServerCounter(count=state.count)

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"count": kwargs.count}

    template = """
      <button @c-click="increment">
        Count: {{ count }}
      </button>
    """


```


The browser token contains an opaque reference while the strict JSON State
lives in `Citry.cache`. Public fields are still emitted separately for
templates and bindings, so `_storage = "server"` is not a visibility control.
Omit secrets and server-only facts from `_public`; the example exposes only
`count`. The default cache is in-process memory, which is useful for development
and one-process deployments. Configure a shared cache backend before running
several workers so every request can resolve the same State.

This first step changes the library boundary without forcing a storage-policy
change. Keep large values in the server store and server-only facts outside
`_public` while the component behavior settles.

## Step two: opt suitable components into signed State

When a component's State is small, non-secret strict JSON, remove the server
storage setting by using the default State declaration:


```citry
class SignedCounter(Component):
    citry = citry_app

    class Kwargs:
        count: int = 0

    class State(Kwargs):
        pass

    class Events:
        def increment(self, state):
            state.count += 1
            return SignedCounter(count=state.count)

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"count": kwargs.count}

    template = """
      <button @c-click="increment">
        Count: {{ count }}
      </button>
    """


```


The handler and template stay the same. State now travels in a full-HMAC
signed token, so the server store is not needed for that component.

Signed means tamper-evident, not encrypted. The values are visible in page
source and must be treated as client input. Components containing secrets or
large data can remain on `_storage = "server"` indefinitely, with `_public`
narrowed so secrets are not emitted separately. The migration is per
component, not an all-or-nothing application switch.

## Return every affected region explicitly

livecomponents commands accumulate execution results. A command can mark
itself, its parent, or another component dirty, and the response carries
several out-of-band fragments:


```python
@command
def save(self, call_context: CallContext[TaskState], task_id: int):
    save_task(task_id)
    return [
        ComponentDirty("task-summary"),
        TriggerEvents([Event(name="task-saved", detail={"taskId": task_id})]),
    ]
```


Citry returns the same intent as ordered actions. A selector names the region
to render, and a browser event handles client-owned follow-up behavior:


```citry
class TaskIn:
    task_id: int


class TaskSummary(Component):
    citry = citry_app

    class Kwargs:
        task_id: int

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"task_id": kwargs.task_id}

    template = """
      <p id="task-summary">Task {{ task_id }} saved</p>
    """


class TaskEditor(Component):
    citry = citry_app

    class Events:
        def save(self, data: TaskIn):
            save_task(data.task_id)
            return [
                actions.Render(
                    TaskSummary(task_id=data.task_id),
                    target="#task-summary",
                ),
                actions.Dispatch(
                    "TaskEditor:saved",
                    {"taskId": data.task_id},
                ),
            ]

    template = """
      <button @c-click="save({ task_id: 42 })">
        Save task
      </button>
      <p id="task-summary">Task 42 not saved</p>
    """


```


Use `actions.Render` for each independent component instance that must evolve
separately. If one selector matches several elements, Citry creates mirrored
placements of one logical instance: they share State and later self-renders
update all placements together.

Automatic `parent` and `find_one()` command routing is intentionally absent.
Use an explicit target when Python owns the update, or Dispatch an application
event when the receiving component owns the reaction. This keeps the
relationship visible at the call site and avoids path-encoded parent ids.

## Build every later render from explicit inputs

livecomponents can save component state, selected outer context, and raw
template source so it can reconstruct a later render. Citry handlers receive
no original kwargs or fills. A handler builds a fresh component tree from its
State, request context, and newly loaded records:


```python
class Events:
    def refresh(self, state, request):
        task = load_task_for_user(
            task_id=state.task_id,
            user=current_user(request),
        )
        return TaskEditor(task=task)
```


If the new tree needs slot content, supply the fills again in that returned
tree. This rule prevents stale request context or saved template text from
silently reappearing on a later call.

## Translate dynamic HTML attributes

Citry leaves ordinary HTML attribute values as literal strings. Django-style
interpolation inside an attribute therefore produces the wrong URL:


```html
<!-- Wrong in a Citry template: braces are sent to the browser. -->
<a href="{{ command_url }}">Run command</a>
```


Use `c-` for a dynamic HTML attribute:


```html
<!-- Right: command_url is evaluated during rendering. -->
<a c-href="command_url">Run command</a>
```


Apply the same rule to dynamic `action`, `src`, `class`, and other
attributes. Text interpolation continues to use `{{ expression }}`.

## Syntax mapping

| livecomponents | Citry Events |
|---|---|
| `LiveComponentsModel` | Dataclass-shaped `class State` |
| Redis/pickle State | First step: `_storage = "server"` with strict JSON in `Citry.cache` |
| Browser-independent migration step | Keep server storage for as long as the component needs it |
| Optional move away from Redis | Second step: default signed State, component by component |
| `@command` | Public method inside `class Events` |
| `CallContext.state` | `state` injectable |
| `CallContext.request` | framework-neutral `request` injectable |
| Body kwargs splatted into command | Typed `data` schema with coercion and 422 field errors |
| Implicit `ComponentDirty` | Return a fresh component or `actions.Render(...)` |
| `ParentDirty` / `ComponentDirty(id)` | Explicit `actions.Render(target=...)` |
| `TriggerEvents` | `actions.Dispatch(name, detail)` |
| `RedirectPage` | `actions.Redirect(url)` |
| `PushUrl` / `ReplaceUrl` | `actions.PushUrl(url)` / `actions.ReplaceUrl(url)` |
| `parent_id` and component path | No author-managed hierarchy id; use target or Dispatch |
| `{% call_command ... %}` / `hx-post` | `@c-*`, `$sendEvent`, or a per-event URL |
| htmx + json-enc + Alpine morph setup | Citry loads and coordinates its client runtimes automatically |
| Saved context and template source | Fresh tree with explicit kwargs and fills |

## Keep serialization and authorization explicit

Citry uses strict JSON for both storage modes. It does not pickle State,
component instances, Django forms, models, or template objects. Reload models
by validated id and treat a missing or unauthorized row as an ordinary event
error.

The session id is not authorization. Put authentication and authorization in
the host middleware, an Events guard, or the handler itself. Repeat the check
for every event even when the page that rendered the component was protected.

Staged uploads, batched download actions, and server push sit outside Events
v1. A dedicated `@event(bundle=False)` handler can return
`actions.Download(...)`; history updates use `actions.PushUrl(...)` or
`actions.ReplaceUrl(...)`. The
[Events migration parity matrix](/v/0.4.4/guides/events-migration-parity/) records
their delivery tags and the accepted replacement for deliberately excluded
behavior.

## Finish each migration step

For the server-held first step, check that:

- the State schema contains every value the next call truly needs;
- a shared cache is configured for multi-worker deployment;
- every handler returns the affected render, event, redirect, or data; and
- old parent-id and saved-context dependencies have explicit replacements.

Before switching one component to signed State, also check that:

- its serialized State is small strict JSON;
- none of its values are secret;
- every client-writable value is revalidated; and
- `_public` and `_model` expose only the intended fields.

Continue with [State](/v/0.4.4/events/state/) and [event actions](/v/0.4.4/events/actions/) for
fresh renders, and [Security](/v/0.4.4/security/) for cache, CSRF, and
client-input guidance.