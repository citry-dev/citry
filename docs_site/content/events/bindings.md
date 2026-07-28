---
title: Bind events in templates
description: Call Citry event handlers from HTML, bind controls to State, and show loading or error feedback with Alpine.
---

# Bind events in templates

Citry's `@c-*` attributes call handlers. Its `:c-*` attributes connect form
controls to [`State`][citry.Component.State]. Both are compiled with the
component, so invalid handler names, State fields, and modifier combinations
fail when the template loads.

## Call handlers from HTML

| Syntax | Result |
|---|---|
| `@c-click="save"` | Call `save` for a click. Any DOM event name works. |
| `@c-click="rate({stars: 5})"` | Evaluate one Alpine object expression and validate it as the handler's `data`. |
| `@c-submit.prevent="submit"` | Collect named form controls and call `submit` without native navigation. |
| `@c-poll.30s="refresh"` | Call `refresh` every 30 seconds while the tab is visible. |

| Modifier | Use |
|---|---|
| `.prevent` | Call `preventDefault()` before sending an event. |
| `.stop` | Stop the DOM event from bubbling. |
| `.self` | Send only when the bound element itself was the event target. |
| `.once` | Send at most once during the binding's lifetime. |
| `.enter` / `.escape` | Filter a keyboard event to one key. |
| `.debounce[.300ms]` | Wait for a quiet period. The bare form uses 250 ms. |
| `.throttle[.1s]` | Send at most once per period. The bare form uses 250 ms. |

Debounce and throttle also apply to two-way State bindings. Polling accepts one
time segment. Invalid combinations fail when the component template loads.

An `@c-*` attribute on a child component tag is a parent-owned listener. Its
handler name and optional argument expression use the parent's scope even
though the child's roots carry the physical DOM listener. If the child should
run a callback within its own scope, pass that callback as a `$c-props` value
and use it in the child's template. See
[Client interactivity](/concepts/client-interactivity/#send-events-up-from-a-component-tag)
for component-boundary isolation.

## Bind controls to State

| Syntax | Result |
|---|---|
| `:c-query` | Display the public `query` State field in this control. |
| `:c-query="refresh"` | Update `query` and call `refresh` on the control's normal update event. |
| `:c-query.lazy="refresh"` | Wait for the committed-value event. |
| `:c-query.debounce.300ms="refresh"` | Wait for 300 ms of quiet before one update and call. |
| `:c-query.throttle.1s="refresh"` | Send at most one update per second. |
| `:c-query.on:keyup.enter="refresh"` | Use `keyup` as the update event and accept only Enter. |

Text inputs, textareas, and ranges use `input` by default and `change` with
`.lazy`. Selects, checkboxes, and radios use `change`. A custom element must
name its event with `.on:<event>`. File inputs are event arguments, not State.
Bare `.debounce` and `.throttle` use 250 ms. `.lazy` and `.on:<event>` cannot be
combined.

State bindings belong on HTML controls inside the component that owns the
State. A `:c-*` binding on a child component tag is an error.

## Keep rapid local changes in the browser

Not every click needs Python. [`$state`][$state] is reactive, so a local button
can update it immediately and a later server event can persist the latest
value:

```citry
class SavedCounter(Component):
    citry = citry_app

    class Kwargs:
        count: int = 0

    class State(Kwargs):
        pass

    class Events:
        def save(self, state):
            persist_count(state.count)

    def template_data(self, kwargs, slots):
        return {"count": kwargs.count}

    template = """
      <div>
        <button @click="$state.count++">+1</button>
        <span x-text="$state.count">{{ count }}</span>
        <button @c-click="save">Save</button>
      </div>
    """
```

The first button is ordinary Alpine and makes no request. The Save button sends
the queued State update with the `save` call.

## Read call state from Alpine

These magics are available in Alpine expressions inside an interactive Citry
component:

| Magic | Use |
|---|---|
| [`$state`][$state] | Read reactive public State or write a field allowed by `_model`. A write rides the next call from this component. |
| [`$loading()`][$loading] | Test whether any call from this component is queued or running. |
| [`$loading('save')`][$loading] | Test only the named handler. |
| [`$error`][$error] | Read the last failed call as `{status, code, message, fieldErrors?}`, or `null`. |
| [`$sendEvent(name, args?)`][$sendEvent] | Send a named event from an Alpine expression. |
| [`$onEvent(name, callback)`][$onEvent] | Listen for server-dispatched events and receive an unsubscribe function. |

`$loading` and `$error` are read-only. A successful call clears `$error`.

Component JavaScript receives the same State and event helpers:

```javascript
$component(({ state, sendEvent, onEvent }) => {
  const stop = onEvent("FilterPanel:reset", () => {
    state.query = "";
    sendEvent("refresh");
  });

  return stop;
});
```

## Refresh a dashboard on an interval

`@c-poll` calls one handler repeatedly and pauses while the tab is hidden:

```citry
class JobStatus(Component):
    citry = citry_app

    class Kwargs:
        job_id: int

    class State(Kwargs):
        pass

    class Events:
        def refresh(self, state):
            return JobStatus(job_id=state.job_id)

    def template_data(self, kwargs, slots):
        return {"status": job_status(kwargs.job_id)}

    template = """
      <div @c-poll.30s="refresh">
        Job is {{ status }}
      </div>
    """
```

Use exactly one time segment, such as `.30s`.
