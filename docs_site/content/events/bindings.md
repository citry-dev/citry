---
title: Bind events in templates
description: Call Citry event handlers from HTML, bind controls to State, and show loading or error feedback with Vue.
---

# Bind events in templates

This page covers the template attributes that connect your HTML to Python
handlers. Use `@c-*` to call a handler when something happens on an element,
such as a click or a keypress. Use `:c-*` to keep a form control in sync with
a [`State`][citry.Component.State] field. Vue helpers such as `$loading()` and
`$error()` show what a call is doing.

Citry checks these attributes when the template first compiles, which is
usually on the first render. A misspelled handler name, an unknown State
field, or modifiers that cannot be combined raise an error there.

## Call handlers from HTML

`@c-<event>="handler"` calls the handler when the element receives that DOM
event:

| Syntax | Result |
|---|---|
| `@c-click="save"` | Call `save` when the element is clicked. Any DOM event name works, including your own custom events. |
| `@c-click="rate({stars: 5})"` | Pass arguments as one object. The handler receives it as `data`. |
| `@c-submit.prevent="submit"` | Collect the form's named controls and call `submit` instead of submitting the page. |

Modifiers after the event name change when the call is sent:

| Modifier | Use |
|---|---|
| `.prevent` | Call `preventDefault()` on the event first. |
| `.stop` | Stop the event from bubbling to ancestors. |
| `.self` | Send only when the event happened on this element, not on a child. |
| `.once` | Send at most once. |
| `.enter` / `.escape` | Send only when the key pressed was Enter / Escape. |
| `.debounce` | Wait until events stop for a moment, then send once. |
| `.throttle` | Send at most once per interval. |

`.debounce` and `.throttle` wait 250 ms by default. Add a duration to change
it, as in `@c-input.debounce.300ms="search"` or `.throttle.1s`.

Citry listens on the element that has the attribute. An event that does not
bubble, such as `focus`, reaches only that element, so a binding on an
ancestor does not see it. Use a bubbling event such as `focusin` there
instead.

On a child component tag, `@c-select="save"` calls the parent's `save`
handler when the child emits `select` through Vue. To let the child call
something from its own template, pass a callback through a Vue prop instead.
See [Client interactivity](/concepts/client-interactivity/#listen-to-child-events).

## Bind controls to State

`:c-<field>` connects a form control to the State field of the same name:

| Syntax | Result |
|---|---|
| `:c-query` | Show the `query` field in this control. |
| `:c-query="refresh"` | Also write each edit to `query` and call `refresh`. |
| `:c-query.lazy="refresh"` | Send when the user finishes editing (on `change`), not on every keystroke. |
| `:c-query.debounce.300ms="refresh"` | Send once, after 300 ms without edits. |
| `:c-query.throttle.1s="refresh"` | Send at most once per second. |
| `:c-query.on:keyup.enter="refresh"` | Send on `keyup`, only for the Enter key. |

A binding without a handler is **one-way**: Citry shows the field's value in
the control but never reads the control back. A binding with a handler is
**two-way**: each edit updates the field and calls the handler with the new
State. Only two-way bindings take the timing modifiers. `.lazy` and
`.on:<event>` cannot be combined.

Put the binding on a control inside the component that owns the State. A
`:c-*` binding on a child component tag is an error.

### What Python type the field receives

The browser sends the control's value as JSON, and the server checks it
against the field's type **without converting it**. Declare the field to
match the control:

| Control | Value sent | Declare the field as |
|---|---|---|
| Checkbox, radio | whether it is checked | `bool` |
| `<input type="number">`, `<input type="range">` | a number | `int` or `float` |
| `<select multiple>` | the selected option values, in page order | `list[str]` |
| Other text-like inputs, a single `<select>`, `<textarea>` | the text | `str` |
| A custom element | its `value` property, which must be JSON | the matching type |

An empty or half-typed number input has no number, so it sends its text. A
field declared `int` rejects that. Accept both and convert in the handler:

```python
class State:
    amount: int | str = ""


class Events:
    def save(self, state):
        amount = int(state.amount or 0)
```

For `<select multiple>`, give the field an empty list as its default:

```python
from dataclasses import field


class State:
    tags: list[str] = field(default_factory=list)
```

### Which elements you can bind

A binding reads and writes a control's value, so the element must have one:

| Element or input type | One-way | Two-way |
|---|---:|---:|
| `<input>` of type `text`, `search`, `tel`, `url`, `email`, `password`, `date`, `month`, `week`, `time`, `datetime-local`, `number`, `range`, `color`, `checkbox`, `radio` | Yes | Yes |
| `<input type="hidden">` | Yes | No: the user cannot edit it. |
| `<input type="file">` | No | No: files cannot go into State. Use an upload endpoint. |
| `<input>` of type `submit`, `image`, `reset`, `button` | No | No: these are buttons, not values. |
| `<textarea>`, `<select>` | Yes | Yes |
| A custom element with a `value` property | Yes | Yes, with `.on:<event>` |
| Any other element, such as `<div>` or `<span>` | No | No |

An `<input>` without a `type` counts as `text`. To react to something
happening on an element without a value, use an `@c-*` event binding:

```citry-html
{# ❌ A <div> has no value to bind #}
<div :c-query.on:click="refresh"></div>

{# ✅ Listen for the event instead #}
<div @c-click="refresh"></div>
```

### Which event updates the field

A two-way binding sends on one DOM event. `.lazy` switches to the event that
fires when the user finishes editing, and `.on:<event>` names the event
yourself:

| Control | Default event | With `.lazy` |
|---|---|---|
| Text-like inputs, number, range, `<textarea>` | `input` | `change` |
| Checkbox, radio, `<select>` | `change` | Not allowed: these already send on `change` |
| A custom element | You must set `.on:<event>` | Not allowed |

`.enter` and `.escape` need a keyboard event, so pair them with
`.on:keyup` or `.on:keydown`.

### What Citry writes into the control

Citry writes the field into every bound control, and again after each
response that changes State. This is how a one-way binding shows the
server's value:

| Control | Written as |
|---|---|
| Checkbox, radio | checked when the value is truthy |
| `<select multiple>` | options whose value is in the list are selected; anything that is not a list clears the selection |
| Other inputs, `<textarea>`, a single `<select>` | the value as text; `None` becomes empty |
| A custom element | the value as is; `None` becomes `null` |

## Keep rapid local changes in the browser

Not every click needs Python. [`$state`][$state] is a Vue object holding the
component's State. A plain Vue click handler can change it without a request,
and the next server call sends the latest value along:

```citry-html
<button @click="$state.count++">+1</button>
<span v-text="$state.count">{{ count }}</span>
<button @c-click="save">Save</button>
```

The `+1` button is ordinary Vue and makes no request. Save calls the `save`
handler, which receives the updated `count` in `state`.

## Read call state from Vue

These helpers work in the template and, through `this`, in the component's
JavaScript:

| Helper | Use |
|---|---|
| [`$state`][$state] | Read State, or replace a field the browser may change. The change is sent with the next non-GET call from this component. |
| [`$loading()`][$loading] | True while any call from this component is waiting or running. |
| [`$loading('save')`][$loading] | The same, for the `save` handler only. |
| [`$error()`][$error] | The newest error from any of this component's handlers, or `null`. |
| [`$error('save')`][$error] | The last error from `save`, or `null`. |
| [`$sendEvent(name, args?)`][$sendEvent] | Call a handler and get a Promise for its result. |

A successful call clears its handler's error. A retry keeps showing the old
error until the new call finishes. Passing an unknown handler name to
`$loading` or `$error` raises an error.

Use `$sendEvent` when your JavaScript needs the handler's return value. An
`@c-*` attribute does not give you one:

```javascript
$component({
  data() {
    return { result: null };
  },
  methods: {
    async refresh() {
      this.result = await this.$sendEvent("refresh");
    },
  },
});
```

When a call made with `$sendEvent` fails, its Promise rejects. Catch it with
`try`/`catch` or `.catch(...)`. An `@c-*` attribute handles failures for you:
the error goes to `$error()`.

## Call a handler on a timer

`@c-poll.<seconds>s` calls a handler repeatedly, for example to refresh a
status. The first call happens after one full interval:

```citry-html
<output @c-poll.30s="refresh({projectId})">
  Waiting for an update
</output>
```

Citry skips a tick while the previous poll is still waiting or running. Polls
stop while the browser tab is hidden. When the tab is shown again, the timer
starts a new full interval, without making up for missed calls. The timer
also stops when the element is removed, and starts over when a re-render
replaces it.

## When a binding does not behave as expected

!!! note "Debounce, throttle, and polling need an HTML element"

    `.debounce`, `.throttle`, and `@c-poll` work only on HTML elements. On a
    child component tag they raise `TypeError` when the page renders. A
    `c-bind` spread can add `@c-poll` to an element, but only with a plain
    handler name such as `"refresh"`, without arguments.

!!! note "`.once` is used up by the first event"

    `.once` removes the listener after the first event, even when another
    modifier stops that event from sending. With `@c-keydown.enter.once`,
    pressing any other key first means a later Enter sends nothing.

!!! note "Modifiers check the actual event"

    `.prevent` has an effect only when the event can be cancelled.
    `.enter` and `.escape` read the event's `key` property, whatever the
    event's name. An event without a `key` never matches.

!!! note "Bindings that Citry checks during the render"

    When `<c-element>`, a `c-bind` spread, or a Python-computed `c-type`
    decides the element or its input type, Citry checks the binding while
    rendering, before the HTML reaches the browser. When Vue changes `:type`
    in the browser to a type that cannot be bound, the binding stops
    working and Citry reports it in the browser console. It starts working
    again if the type changes back.

!!! note "Binding a custom element"

    Citry reads and writes a custom element's `value` property as is, so
    numbers, lists, and objects arrive unchanged. If reading `value` throws,
    returns `undefined`, or returns something that is not JSON, Citry
    leaves State unchanged, sends nothing, and reports the problem in the
    browser console. The element may be defined after Citry starts: Citry
    waits for it and then applies the current State value.
