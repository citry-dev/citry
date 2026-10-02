---
title: Migrate from Tetra
description: Port Tetra public state, server methods, promise calls, and client callbacks to Citry State, Events, and actions.
---

# Migrate from Tetra

This guide is for Tetra users porting components to Citry. It shows where
each part of a Tetra component goes: its public attributes, its `@public`
methods, its JavaScript calls, and its client callbacks.

The core idea carries over: a template calls a Python method on the server,
and the page updates. Debounce settings, awaiting a method's return value
from JavaScript, and sending a browser event from Python all have direct
equivalents.

What changes most is what survives between calls. Tetra keeps the whole
component, pickled and encrypted, in a token. Citry keeps only the values
you declare, as JSON. The browser side also uses Vue instead of Alpine.js.
Three Citry terms come up throughout:

- [`State`][citry.Component.State] lists the values a later call needs.
  Citry sends them to the browser with the rendered component and gets them
  back with the next call. See [Event state](/events/state/).
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
from citry.ext.events import actions, event
```

## Syntax mapping

| Tetra | Citry |
|---|---|
| `count = public(0)` | `class State: count: int = 0` |
| Private component attribute | Reload it in the handler, or compute it during the render |
| `@public` method | Public method inside `class Events` |
| `@public.debounce(200)` | `@event(debounce=200)` |
| `@public.watch("query")` | `:c-query="refresh"`, or a Vue watcher that calls `this.$sendEvent(...)` |
| `@click="increment()"` | `@c-click="increment"` |
| `await this.method(...)` | `await this.$sendEvent(name, data)` |
| Method return value | Return `actions.Data(value)` or a `dict` |
| Automatic re-render | Return a new component or `actions.Render(...)` |
| `self.client._dispatch(...)` | `actions.Dispatch(name, detail)` |
| Other `self.client.*` callbacks | An action, or a dispatched event that browser code handles |
| History changes from Python | `actions.PushUrl(url)` / `actions.ReplaceUrl(url)` |
| Encrypted component token | Signed JSON State, or `_storage = "server"` |
| Alpine component script | Vue options in `$component({...})` |
| `x-data` / `x-model` | Vue `data()` / `v-model`; `$state` and `:c-*` reach Citry State |

The sections below show the common rows in context.

## Fix dynamic attributes

When you copy a template over, check its attributes first. An ordinary
attribute value in a Citry template is a literal string, so Django-style
braces inside it are not evaluated:

```citry-html
<!-- Wrong in a Citry template: braces appear in the final URL. -->
<a href="{{ task_url }}">Open task</a>
```

Prefix the attribute with `c-`, and Citry evaluates its value as a Python
expression:

```citry-html
<!-- Right: task_url is evaluated during rendering. -->
<a c-href="task_url">Open task</a>
```

The same applies to `action`, `src`, `class`, and any other attribute. Text
between tags still uses `{{ expression }}`. See
[Attributes](/syntax/dynamic-attributes/#c-dynamic-attributes).

## Port a component

A Tetra counter has a public attribute and a decorated server method, and
re-renders after the method runs:

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

In Citry, `count` becomes a State field and `increment` moves into
`Events`. The handler returns two things: a new `Counter` to re-render, and
a JSON value for JavaScript that awaits the call:

```citry
--8<-- "docs_site/snippets/migrate_tetra.py:counter"
```

The `data` parameter receives the call's arguments, here `{ amount: 1 }`,
checked against `StepIn`. `@event(debounce=200)` sets the default debounce
for every `@c-*` and `:c-*` binding that calls this handler. A binding can
override it with its own `.debounce.<time>` modifier. Debounce only spaces
out requests from the page; add rate limits on the server where you need
them.

By default, Citry signs State before sending it to the browser, so the
server can detect a changed value. Anyone can still read it in the page
source. Do not put model instances or secrets in State; reload records and
check permissions in each handler.

## Await a result in JS

Tetra generates a method on the browser object that returns a Promise:

```javascript
const value = await this.increment(1);
```

In Citry, call `this.$sendEvent(name, data)` from the component's
JavaScript, as `addOne` does in the `js` of the counter above. The Promise
resolves with the `actions.Data` value or `dict` the handler returns. Any
render in the same list still happens, in list order.

Two differences from Tetra:

- `$sendEvent` does not apply the `@event(debounce=...)` default. Debounce
  the call in JavaScript when it needs one.
- An `@c-*` attribute does not give you the return value. Use it when you
  only need the call to happen. When other browser code must react to it,
  return `actions.Dispatch(...)` instead.

## Replace client calls

Current Tetra uses `_dispatch` as its general callback; custom
`self.client.*` calls shown in older Tetra documentation are blocked by its
allowlist:

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

A Citry handler returns a list of actions instead. `actions.Dispatch` fires
a named browser event for browser code to handle, and `actions.Render`
re-renders the component:

```citry
--8<-- "docs_site/snippets/migrate_tetra.py:closed-actions"
```

In the component's JavaScript, listen with the `onEvent` function that
`onServerRender` receives, or with `addEventListener` on an element above
the component. With the Dispatch first, listeners from the current render
hear it. When a Render replaces a component that contains this one, the
Dispatch must come first; see
[Return several actions in order](/events/actions/#return-several-actions-in-order).

Every effect of a handler is visible in its return value.

## Move Alpine code to Vue

Tetra merges public state, server methods, and component JavaScript into
one Alpine.js object. In Citry, a component is also a Vue component, and
each kind of value has its own place:

- `State` belongs to the component and reaches Vue as `$state`.
- `$component({...})` in the component's `js` adds Vue `data()`, methods,
  computed values, and props. See
  [Client interactivity](/concepts/client-interactivity/).
- A Vue expression written on a child component's tag belongs to the parent.
  Pass values down with Vue props and listen to the child's events with
  Vue listeners such as `@select`.

The same holds for slots: content passed into a slot reads names from the
component that wrote it. A component with several top-level elements, or
none, is still one Vue component.

## Plan for differences

### Hide secret State

Citry does not pickle components, models, or forms into State. State holds
JSON values and is signed, not encrypted. To keep a value out of the page,
set `_storage = "server"` and leave the field out of `_public`. Server
storage keeps the values in the server cache, but fields listed in `_public`
(all fields by default) still reach the browser. See
[Treat State as client input](/security/#treat-state-as-client-input).

### Poll instead of push

Citry's server events run over HTTP, and the server cannot push updates to
the page. To refresh a part of the page on a timer, use `@c-poll`; see
[Call a handler on a timer](/events/bindings/#call-a-handler-on-a-timer).

### Accept file uploads

Citry does not read multipart file uploads by default. To accept files,
register a custom payload codec, a class that turns the request body into
handler input, and have it produce `UploadedFile` values. Downloads work
without extra setup: a handler marked `@event(bundle=False)` can return
`actions.Download(...)`; see
[Event actions](/events/actions/).

### Handle offline calls

Citry does not queue calls while offline, because replaying changes after a
deployment needs rules only your application knows. It also has no general
way for Python to call a browser function by path; use `actions.Dispatch`.

## Finish the port

Before shipping a migrated component, check that:

- every public Tetra attribute is now a render input (`Kwargs`), a State
  field, data for browser code (`js_data()`), or Vue `data()` (see
  [Event state](/events/state/) for how to choose);
- State holds only JSON values and no secrets;
- each handler returns a render, data, event, or redirect;
- client callbacks have become named `actions.Dispatch` events;
- database rows are reloaded and permissions checked on each call; and
- components that need server push, uploads, downloads, or history changes
  are checked against the parity matrix.

The [Events migration parity matrix](/guides/events-migration-parity/)
compares the rest of Tetra's features with Citry.
[Bind events in templates](/events/bindings/) and
[Event actions](/events/actions/) cover the full workflow.
