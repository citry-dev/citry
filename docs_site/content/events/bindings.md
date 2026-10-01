---
title: Bind events in templates
description: Call Citry event handlers from HTML, bind controls to State, and show loading or error feedback with Vue.
---

# Bind events in templates

Citry's `@c-*` attributes call handlers. Its `:c-*` attributes connect form
controls to [`State`][citry.Component.State]. Both are compiled with the
component, so invalid handler names, State fields, and modifier combinations
fail when the template first compiles, normally on its first render.

## Call handlers from HTML

| Syntax | Result |
|---|---|
| `@c-click="save"` | Call `save` when this element receives `click`. Native and custom DOM event names work, including events that do not bubble. |
| `@c-click="rate({stars: 5})"` | Evaluate one Vue object expression and validate it as the handler's `data`. |
| `@c-submit.prevent="submit"` | Collect named form controls and call `submit` without native navigation. |

| Modifier | Use |
|---|---|
| `.prevent` | Call `preventDefault()` before sending. It takes effect when that event instance is cancelable. |
| `.stop` | Stop the DOM event from bubbling. |
| `.self` | Send only when the bound element itself was the event target. |
| `.once` | Send at most once during the binding's lifetime. |
| `.enter` / `.escape` | Require the concrete event's `key` to be `Enter` / `Escape`, regardless of the event name. |

On HTML elements, `.once` follows Vue's native listener behavior: the first
event consumes the listener even if `.enter` or `.self` prevents the handler
from running. For example, with `@c-keydown.enter.once`, pressing another key
first leaves no listener for a later Enter press.

Ordinary-element `@c-*` bindings support `.debounce` and `.throttle`. Each may
take an optional whole-number duration in milliseconds or seconds immediately
after the modifier, as in `@c-input.debounce.300ms="search"`; a bare modifier
uses 250 ms. Two-way `:c-*` State control bindings support the same modifiers.

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
its `content`. When Vue creates live `v-if` or `v-for` copies, Citry
activates the bindings on those inserted copies. A binding on the `<template>`
element itself is different: that element is live, so its binding activates
normally.

An `@c-*` attribute on a child component tag is a parent-owned listener. Its
handler name and optional argument expression use the parent's Vue instance even
though the child receives the event. If the child should run a callback from
its own template, declare a native Vue function prop and pass the callback
through that prop. See
[Client interactivity](/concepts/client-interactivity/#listen-to-child-events)
for component-boundary isolation. Debounce and throttle are currently supported
only on `@c-*` bindings attached to HTML elements; a timed binding on a child
component is rejected rather than sharing timing state between child placements.

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
and in the browser for Vue `:type`. A live invalid type
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
        <span v-text="$state.count">{{ count }}</span>
        <button @c-click="save">Save</button>
      </div>
    """
```

The first button is ordinary Vue and makes no request. The Save button sends
the queued State update with the `save` call.

## Read call state from Vue

These magics are available in Vue expressions inside an interactive Citry
component:

| Magic | Use |
|---|---|
| [`$state`][$state] | Read reactive public State or replace a field allowed by `_model`. A write rides the next non-GET browser call from this component. |
| [`$loading()`][$loading] | Test whether any call from this component is queued or running. |
| [`$loading('save')`][$loading] | Test only the named handler. |
| [`$error()`][$error] | Read the newest retained error across this component's handlers, or `null`. |
| [`$error('save')`][$error] | Read only the named handler's retained error. |
| [`$sendEvent(name, args?)`][$sendEvent] | Send a named event from a Vue expression. |

The loading and error accessors are read-only. A successful call clears only
its handler's error. Retrying a failed handler leaves its error visible until
the new call succeeds or fails. Unknown handler names passed to `$loading` or
`$error` throw before a request is sent.

Component JavaScript uses the same public-instance helpers through `this`:

```javascript
$component({
  methods: {
    async refresh() {
      const result = await this.$sendEvent("refresh");
      this.result = result;
    },
  },
  data() {
    return { result: null };
  },
});
```

Declarative `@c-*` bindings do not expose the handler's Promise or an
[`actions.Data`][citry.ext.events.actions.Data] value. Use `$sendEvent` when browser code needs that one caller's value. Return
[`actions.Dispatch`][citry.ext.events.actions.Dispatch] when a declarative
call must notify browser listeners.

A well-formed server `ok: false` result, including `invalid_args`, is recorded
for `$error(...)` and consumed by a declarative `@c-*` binding. A native Vue
listener that calls `$sendEvent`, such as `@select="$sendEvent('save')"`, owns
a Promise instead; handle its rejection with `await` and `try`/`catch` or with
`.catch(...)`. Client-side argument expressions that cannot be encoded as JSON,
malformed Events protocol responses, and render or lifecycle failures still
surface as runtime errors.

## Polling status

Use `@c-poll.<seconds>s` on an ordinary DOM element to call a server handler at
a fixed cadence. The first call starts after one complete interval:

```citry-html
<output @c-poll.30s="refresh({projectId})">Waiting for an update</output>
```

Each live element owns its polling lifetime. Citry skips a tick while that
element's previous polling request is queued or running. Removing the element
or accepting a server revision that replaces that binding stops its old
lifetime and starts a fresh complete interval. A revision in an unrelated
subtree does not reset the timer. A hidden page pauses polling; returning to it
starts a fresh complete interval, without catch-up calls.

Polling currently requires a literal binding on an ordinary DOM element.
Component-boundary `@c-poll` and polling introduced through `c-bind` are not
supported by the Vue runtime.
