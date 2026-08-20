---
title: Bind events in templates
url: https://citry.dev/v/0.4.1/events/bindings/
description: "Call Citry event handlers from HTML, bind controls to State, and show loading or error feedback with Alpine."
---
# Bind events in templates

Citry's `@c-*` attributes call handlers. Its `:c-*` attributes connect form
controls to [`State`](/v/0.4.1/reference/component/#citry-component-state). Both are compiled with the
component, so invalid handler names, State fields, and modifier combinations
fail when the template first compiles, normally on its first render.

## Call handlers from HTML

| Syntax | Result |
|---|---|
| `@c-click="save"` | Call `save` when this element receives `click`. Native and custom DOM event names work, including events that do not bubble. |
| `@c-click="rate({stars: 5})"` | Evaluate one Alpine object expression and validate it as the handler's `data`. |
| `@c-submit.prevent="submit"` | Collect named form controls and call `submit` without native navigation. |
| `@c-poll.30s="refresh"` | Call `refresh` every 30 seconds while the tab is visible. |

| Modifier | Use |
|---|---|
| `.prevent` | Call `preventDefault()` before sending. It takes effect when that event instance is cancelable. |
| `.stop` | Stop the DOM event from bubbling. |
| `.self` | Send only when the bound element itself was the event target. |
| `.once` | Send at most once during the binding's lifetime. |
| `.enter` / `.escape` | Require the concrete event's `key` to be `Enter` / `Escape`, regardless of the event name. |
| `.debounce[.300ms]` | Wait for a quiet period. The bare form uses 250 ms. |
| `.throttle[.1s]` | Send at most once per period. The bare form uses 250 ms. |

Debounce and throttle also apply to two-way State bindings. Polling accepts one
time segment. Invalid combinations fail when the component template compiles.

Citry listens on the element carrying the binding. A non-bubbling event works
on that element but does not reach a binding on an ancestor. Use a bubbling
counterpart such as `focusin` when an ancestor should react to descendant
events. Custom names are exact: Citry cannot tell a misspelling from an
intentional application event with that name. Citry also does not maintain a
tag/event compatibility table. Application code may dispatch a synthetic
event from any element, so even `<br @c-submit="save">` is valid and fires if
`submit` is dispatched on that element.

Modifiers follow the concrete event too. For example, a native `scroll` event
is not cancelable, but application code may dispatch a cancelable synthetic
event named `scroll`; `.prevent` cancels the latter. Likewise, `.enter` and
`.escape` inspect `event.key` rather than maintaining an event-name allowlist.
An ordinary event with no `key` simply does not match the filter, while an
arbitrarily named `KeyboardEvent` can.

Bindings inside an HTML `<template>` definition remain inert with the rest of
its `content`. When Alpine creates live `x-if` or `x-for` copies, Citry
activates the bindings on those inserted copies. A binding on the `<template>`
element itself is different: that element is live, so its binding activates
normally.

An `@c-*` attribute on a child component tag is a parent-owned listener. Its
handler name and optional argument expression use the parent's scope even
though the child's roots carry the physical DOM listener. If the child should
run a callback within its own scope, pass that callback as a `$c-props` value
and use it in the child's template. See
[Client interactivity](/v/0.4.1/concepts/client-interactivity/#send-events-up-from-a-component-tag)
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

A binding with no value is **one-way**: Citry writes the State field into the
control and never reads it back. A binding with a handler value is **two-way**:
the control writes to the field and calls the handler. Only a two-way binding
takes the timing modifiers above. Bare `.debounce` and `.throttle` use 250 ms,
and `.lazy` and `.on:<event>` cannot be combined.

State bindings belong on HTML controls inside the component that owns the
State. A `:c-*` binding on a child component tag is an error.

### Which elements you can bind

A binding reads a value out of a control and writes one back into it, so it
needs an element that holds an editable or displayable value.

| Element or input type | One-way | Two-way |
|---|---:|---:|
| `<input type="text">`, `search`, `tel`, `url`, `email`, `password`, `date`, `month`, `week`, `time`, `datetime-local`, `number`, `range`, `color`, `checkbox`, `radio` | Yes | Yes |
| `<input type="hidden">` | Yes | No: it has no user update event. |
| `<input type="file">` | No | No: files cannot live in JSON State; use an ordinary upload endpoint or custom transport. |
| `<input type="submit">`, `image`, `reset`, `button` | No | No: these are action controls, not editable values. |
| `<textarea>` | Yes | Yes |
| `<select>` | Yes | Yes. A single select binds a string; `multiple` binds a `list[str]`. |
| A custom element that exposes a value | Yes | Yes, with `.on:<event>`. |
| Any other element, such as `<div>` or `<span>` | No | No |

A missing, bare, or empty input `type` means `text`. Type matching is
case-insensitive but exact: `TEXT` works, while `" text "` or an unknown type
is an error. `.on:<event>` changes the event for a supported two-way binding;
it cannot make `hidden`, file/action inputs, or unknown native types bindable.

An element such as `<div>` holds no value, so a binding has nothing to read or
write. To react to what happens on one, use an `@c-*` event binding:


```citry-html
{# ❌ A <div> has no value to bind #}
<div :c-query.on:click="refresh"></div>

{# ✅ Listen for the event instead #}
<div @c-click="refresh"></div>
```


Citry rejects a known unbindable element when the template compiles. A binding
that a `c-bind` spread puts on an HTML element is checked the same way when it
resolves, including an element selected by `<c-element>`.

A `<select multiple>` reads all selected option values into a `list[str]`, in
the options' document order. Citry writes that list back by selecting every
option whose value occurs in it; an empty list or any non-list value clears the
selection. The live `multiple` property decides the value shape, so the same rule applies when
`multiple` or the `:c-*` binding comes from `c-bind`:


```citry-html
<select multiple :c-tags="save">
  <option value="new">New</option>
  <option value="sale">Sale</option>
</select>
```


Any non-list value, including `None`, clears every selection on the downward
path. A State binding reads selected disabled options too; ordinary form
submission keeps standard `FormData` behavior and omits disabled options.


```python
from dataclasses import field


class State:
    tags: list[str] = field(default_factory=list)
```


`<c-element>` binds whatever element its `is` attribute names, so
`<c-element is="input" :c-query="refresh" />` is an ordinary input binding.
When `is` is computed, Citry validates the State field and handler while the
template compiles, then validates the selected element and its final attributes
at render time. A result such as `input` works; a result such as `div`, an
unsupported input type, or a custom element without the required `.on:` event
fails before its HTML reaches the browser.

A custom element is bound by its `value` property. Citry writes the State value
to that property without HTML-control coercion, so strings, numbers, booleans,
lists, objects, and `None` arrive as their corresponding JavaScript values. A
two-way binding reads the property the same way; its value must therefore be
JSON-compatible and the Python field must accept the matching shape. If a
custom element returns `undefined`, throws while being read, or returns a
non-JSON value such as `Date` or `BigInt`, Citry leaves State unchanged and
does not send the binding's handler. It reports the invalid value in the
browser console, and a later valid update can recover normally.

The element may be defined before or after Citry starts. If its JavaScript
class has not loaded yet, Citry waits for the browser to upgrade that tag and
then applies the **current** State value to the live element. It does not create
a pre-upgrade `value` property or retain an element removed while waiting. The
class must expose `value` by the end of its synchronous upgrade. A missing
property, or a getter or setter that throws, produces a browser-console error
without aborting the other bindings on the page.

### Which event updates the field

A two-way binding listens for one DOM event. `.lazy` switches to the event that
fires when the value is committed, and `.on:<event>` replaces the choice
entirely. The listener belongs to the control itself, so `.on:<event>` also
works with a custom or non-bubbling event dispatched on that control.

| Control | Default event | With `.lazy` |
|---|---|---|
| `<input type="text">` and the other text-like types | `input` | `change` |
| `<input type="number">`, `<input type="range">` | `input` | `change` |
| `<input type="checkbox">`, `<input type="radio">` | `change` | Rejected: the value already commits on `change` |
| `<textarea>` | `input` | `change` |
| `<select>` | `change` | Rejected: the value already commits on `change` |
| A custom element | `.on:<event>` is required | Not applicable |

The `.enter` and `.escape` filters inspect the concrete update event's `key`.
Pair them with `.on:keyup` / `.on:keydown` for ordinary controls, or with any
custom update event that exposes a compatible `key` value.

Citry applies this matrix at every point where a type becomes known: template
load for a literal type, render time for Python-resolved `c-type` / `c-bind`,
and in the browser for Alpine `:type` / `x-bind:type`. A live invalid type
turns off State application, update listeners, draft preservation, and pending
timers. Citry reports it once and reactivates the binding if the type becomes
valid again. The browser checks the raw `type` attribute so an unknown keyword
cannot be silently normalized to `text`. Text-like changes such as a password
visibility toggle preserve an accepted draft; a value/event-shape change such
as text to checkbox cancels the stale draft before activating the new shape.

### What Python type the field receives

A two-way binding sends a JSON value, and the server checks it against the State
field's declared type **without converting it**. Declare the field to match the
control:

| Control | Value sent | Declare the field as |
|---|---|---|
| `<input type="checkbox">`, `<input type="radio">` | whether the control is checked | `bool` |
| `<input type="number">`, `<input type="range">` | a number | `int` or `float` |
| `<select multiple>` | all selected option values, in document order | `list[str]` |
| Supported string-valued two-way inputs, a single `<select>`, `<textarea>` | the value string | `str` |
| A custom element | whatever JSON-compatible value its `value` property holds | match that property |

An empty or half-typed `<input type="number">` holds no number, so it sends the
text instead. A field declared `int` rejects that value. Accept both spellings
and convert in the handler:


```python
class State:
    amount: int | str = ""


class Events:
    def save(self, state):
        amount = int(state.amount or 0)
```


### What Citry writes into the control

Citry applies the field to every bound control in the browser and re-applies it
after each update, so a one-way binding keeps showing the server's value:

| Control | Written as |
|---|---|
| `<input type="checkbox">`, `<input type="radio">` | checked when the value is truthy |
| `<select multiple>` | each option is selected when its value occurs in the list; an empty list or any non-list value (including `None`) clears all options |
| Every other input, `<textarea>`, a single `<select>` | the value as a string, with `None` becoming `""` |
| A custom element | the State value unchanged, including `None` as JavaScript `null` |

## Keep rapid local changes in the browser

Not every click needs Python. [`$state`](/v/0.4.1/reference/browser-apis/#state) is reactive, so a local button
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
| [`$state`](/v/0.4.1/reference/browser-apis/#state) | Read reactive public State or write a field allowed by `_model`. A write rides the next call from this component. |
| [`$loading()`](/v/0.4.1/reference/browser-apis/#loading) | Test whether any call from this component is queued or running. |
| [`$loading('save')`](/v/0.4.1/reference/browser-apis/#loading) | Test only the named handler. |
| [`$error()`](/v/0.4.1/reference/browser-apis/#error) | Read the newest retained error across this component's handlers, or `null`. |
| [`$error('save')`](/v/0.4.1/reference/browser-apis/#error) | Read only the named handler's retained error. |
| [`$sendEvent(name, args?)`](/v/0.4.1/reference/browser-apis/#send-event) | Send a named event from an Alpine expression. |
| [`$onEvent(name, callback)`](/v/0.4.1/reference/browser-apis/#on-event) | Listen for server-dispatched events and receive an unsubscribe function. |

The loading and error accessors are read-only. A successful call clears only
its handler's error. Retrying a failed handler leaves its error visible until
the new call succeeds or fails. Unknown handler names passed to `$loading` or
`$error` throw before a request is sent.

Component JavaScript receives the same State, loading, error, and event
helpers:


```javascript
$component(({ state, effect, loading, error, sendEvent, onEvent }) => {
  const stop = onEvent("FilterPanel:reset", () => {
    state.query = "";
    sendEvent("refresh");
  });

  effect(() => {
    const refreshError = error("refresh");
    showRefreshError(
      refreshError && !loading("refresh")
        ? refreshError.message
        : null,
    );
  });

  return stop;
});
```


Declarative `@c-*` bindings do not expose the handler's Promise or an
[`actions.Data`](/v/0.4.1/reference/events/#citry-ext-events-actions-data) value. Use `$sendEvent` or
`sendEvent` when browser code needs that one caller's value. Return
[`actions.Dispatch`](/v/0.4.1/reference/events/#citry-ext-events-actions-dispatch) when a declarative
call must notify browser listeners.

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