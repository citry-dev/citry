---
title: Migrate from Tetra
url: https://citry.dev/v/0.4.1/guides/migrate-from-tetra/
description: "Port Tetra public state, server methods, promise calls, and client callbacks to Citry State, Events, and actions."
---
# Migrate from Tetra

If a Tetra component's encrypted state token, Alpine object, Python instance,
and template all feel like one object, deployment and authorization concerns
can become hard to separate. Citry keeps the convenient server-method call but
splits the contract into render inputs, strict JSON State, typed event data,
and a closed list of browser actions.

Alpine remains available and is bundled automatically. Citry owns the
component and slot graph, then attaches Alpine scopes to that graph. You still
use ordinary Alpine directives and expressions without making an Alpine
`x-data` object the source of component identity.

The Citry examples assume the configured `citry_app` from
[Server events](/v/0.4.1/events/#configure-a-signing-secret-before-using-state)
and these imports:


```python
from typing import Any

from citry import Component
from citry.ext.events import actions, event
```


## Move public attributes and methods to State and Events

A Tetra counter exposes a public attribute and a decorated server method. The
method automatically re-renders the component:


```citry
from tetra import Component, public


class Counter(Component):
    count = public(0)

    @public.debounce(200)
    def increment(self, amount=1):
        self.count += amount

    template = """
      <button
        {% ... attrs %}
        @click="increment(1)"
        x-text="count"
      ></button>
    """
```


In Citry, the browser-visible value is a State field and the callable method
lives in `Events`. The handler returns the fresh component render and a JSON
value for callers that await it:


```citry
class StepIn:
    amount: int = 1


class Counter(Component):
    citry = citry_app

    class Kwargs:
        count: int = 0

    class State(Kwargs):
        pass

    class Events:
        @event(debounce=200)
        def increment(self, data: StepIn, state):
            state.count += data.amount
            return [
                Counter(count=state.count),
                actions.Data({"count": state.count}),
            ]

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"count": kwargs.count}

    template = """
      <button @c-click="increment({ amount: 1 })">
        Count: {{ count }}
      </button>
    """

    js = """
      $component(({ scope, sendEvent }) => {
        scope.addOne = async () => {
          const result = await sendEvent("increment", { amount: 1 });
          return result.count;
        };
      });
    """


```


`@event(debounce=200)` supplies the handler's default client-side debounce
interval. A binding can override it with its own `.debounce.<time>` modifier.
Debouncing reduces request frequency but is not a server-side rate limit;
enforce authorization and rate limits on the server.
The decorator default applies to declarative `@c-*` and `:c-*` bindings.
Direct `sendEvent(...)` calls do not consult it, so debounce programmatic calls
in JavaScript when they need the same behavior.

State is signed strict JSON. It is visible in page source and treated as
client input. Reload records and authorization facts inside each handler; do
not put model instances or secrets in State.

## Await a server result from Component.js

Tetra generates promise-returning methods on its Alpine object:


```javascript
const value = await this.increment(1);
```


Citry supplies `sendEvent` to Component.js and `$sendEvent` to Alpine
expressions:


```javascript
$component(({ scope, sendEvent }) => {
  scope.addOne = async () => {
    const result = await sendEvent("increment", { amount: 1 });
    return result.count;
  };
});
```


Returning `actions.Data(value)`, or a plain dictionary, resolves that promise.
Render actions in the same result still apply in their listed order.

Inside a template, the equivalent is
`$sendEvent("increment", { amount: 1 })`. Prefer `@c-click="increment(...)"`
when the return value is not needed because the declarative binding also owns
loading and modifier behavior. A declarative `@c-*` binding does not expose
the Promise or its Data value. Return `actions.Dispatch(...)` when browser code
must observe a declarative call's result.

## Replace the callback proxy with closed actions

Current Tetra permits `_dispatch` as its generic callback path; custom
`self.client.*` paths shown in older documentation are blocked by its client
whitelist:


```python
@public
def complete(self, task_id):
    mark_complete(task_id)
    self.client._dispatch(
        "TaskEditor:completed",
        {"message": "Task complete"},
    )
    self.update_html()
```


Citry returns explicit effects. A browser event hands presentation to client
code, while a targeted render updates the server-owned region:


```citry
class TaskIn:
    task_id: int


class TaskSummary(Component):
    citry = citry_app

    class Kwargs:
        task_id: int
        status: str

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"task_id": kwargs.task_id, "status": kwargs.status}

    template = """
      <p id="task-summary">Task {{ task_id }}: {{ status }}</p>
    """


class TaskEditor(Component):
    citry = citry_app

    class Events:
        def complete(self, data: TaskIn):
            mark_complete(data.task_id)
            return [
                actions.Dispatch(
                    "TaskEditor:completed",
                    {"taskId": data.task_id},
                ),
                actions.Render(
                    TaskSummary(task_id=data.task_id, status="complete"),
                    target="#task-summary",
                ),
            ]

    template = """
      <button @c-click="complete({ task_id: 42 })">
        Complete task
      </button>
      <p id="task-summary">Task 42: pending</p>
    """


```


Listen for `TaskEditor:completed` with `$onEvent` or
`addEventListener`. Keep the dispatch before a render that could remove its
listener.

The closed action vocabulary prevents Python from traversing arbitrary client
objects. It also makes every possible response visible in the handler's
return value.

## Keep Alpine behavior local to the receiving component

Tetra merges public state, generated server methods, and component JavaScript
into one Alpine data object. Citry instead keeps three ownership rules:

- `State` belongs to the interactive Citry component instance.
- Component.js adds instance-local Alpine variables through its `scope`
  callback value.
- Alpine expressions authored on a child component tag use the parent's
  scope. Pass a callback through `$c-props` when the child should use it in
  the child's own scope.

This distinction matters for slots and multi-root components. Citry's graph
keeps the component and slot owner explicit even when their DOM ranges overlap
or have no element root.

## Translate dynamic HTML attributes

An ordinary Citry HTML attribute is a literal string, so Django-style braces
inside it are not evaluated:


```html
<!-- Wrong in a Citry template: braces appear in the final URL. -->
<a href="{{ task_url }}">Open task</a>
```


Use a `c-` dynamic attribute for a Python expression:


```html
<!-- Right: task_url is evaluated during rendering. -->
<a c-href="task_url">Open task</a>
```


Use the same rule for dynamic `action`, `src`, `class`, and other HTML
attributes. `{{ expression }}` remains the text-interpolation spelling.

## Syntax mapping

| Tetra | Citry Events |
|---|---|
| `count = public(0)` | `class State: count: int = 0` |
| Private pickled component attribute | Reload from the database or derive during the fresh render; use server-held strict JSON State only when it must persist |
| `@public` method | Public method inside `class Events` |
| `@public.debounce(200)` | `@event(debounce=200)` |
| `@public.watch("query")` | `:c-query="refresh"` or an Alpine watcher that calls `$sendEvent` |
| `@click="increment()"` | `@c-click="increment"` for a declarative server call |
| `await this.method(...)` | `await sendEvent(name, data)` or `$sendEvent(...)` |
| Public method return value | `actions.Data(value)` or a returned dictionary |
| Automatic re-render | Return a fresh component or `actions.Render(...)` |
| `self.client._dispatch(...)` | `actions.Dispatch(name, detail)` |
| Other `self.client.*` callbacks | A closed action, or a dispatched event handled by client code |
| Encrypted pickled component | Signed strict JSON State, or `_storage = "server"` for server-held strict JSON |
| Alpine component script export | Component.js `$component(({ scope, ... }) => {...})` callback |
| `x-data` / `x-model` | Ordinary Alpine remains available; `$state` and `:c-*` bridge Citry State |

## Choose explicit behavior for larger Tetra features

Citry v1 focuses on HTTP interactions. Reactive server push and WebSocket
topics are a separate later decision. Multipart uploads, batched download
actions, and optional State encryption also sit outside v1. A dedicated
`@event(bundle=False)` handler can return `actions.Download(...)`, while
history updates use `actions.PushUrl(...)` or `actions.ReplaceUrl(...)`.
The [Events migration parity matrix](/v/0.4.1/guides/events-migration-parity/) records
the delivery tag for each capability.

Citry does not carry Tetra's offline mutation queue or arbitrary
server-selected callback paths. Replaying calls across a deployment requires
application-specific conflict rules, and a closed action list is easier to
audit. Model and form objects are reloaded or validated in Python rather than
unpickled from the client token.

## Finish the port

Before shipping a migrated component, check that:

- every public Tetra attribute has been classified as `Kwargs`, State,
  `js_data`, or local Alpine data;
- State contains strict JSON values and no secret;
- each public method has an explicit render, data, event, or redirect result;
- server-selected client callbacks have become named Dispatch actions;
- database rows are reloaded and authorized per call; and
- components that require server push, uploads, batched downloads, or history
  changes have been checked against the parity matrix.

Continue with [event bindings](/v/0.4.1/events/bindings/) and [event
actions](/events/actions/) for the complete runtime workflow. See [Client
interactivity](/concepts/client-interactivity/) for
Component.js, `$c-props`, slots, and Alpine ownership.