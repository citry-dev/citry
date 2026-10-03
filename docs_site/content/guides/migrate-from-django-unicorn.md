---
title: Migrate from django-unicorn
description: Move django-unicorn state, actions, validation, and browser calls to explicit Citry State and Events handlers.
---

# Migrate from django-unicorn

You have django-unicorn components with bound attributes, methods called
from the template, and validation, and you want them to behave the same in
Citry. This guide shows where each part of a `UnicornView` goes: its
attributes, its methods, its validation, and the JavaScript calls it makes.

Much of the template vocabulary carries over. `unicorn:click` becomes
`@c-click`, `unicorn:model` becomes a `:c-*` binding with matching debounce
and lazy modifiers, and loading states, errors, and polling all have direct
equivalents. An `@c-*` attribute calls a Python handler when a browser
event fires, and a `:c-*` attribute connects a form control to a State
field.

What changes most is where values live. django-unicorn sends every public
attribute back and forth and re-renders the component after each method
call. Citry splits a `UnicornView`'s job across three pieces:

- `Kwargs` are the inputs a component is rendered with. See
  [Inputs and validation](/concepts/inputs-and-validation/).
- [`State`][citry.Component.State] lists only the values a later call needs.
  Citry keeps them between calls, either on the server or in the page. See
  [Event state](/events/state/).
- A **handler** is a public method in the component's nested `class Events`.
  The browser calls it by name, and the handler returns the new render
  itself. See [Server events](/events/).

The Citry examples assume the `citry_app` instance configured in
[Server events](/events/#configure-a-signing-secret-before-using-state)
and these imports:

```python
from typing import Any

from citry import Component
from citry.ext.events import EventError, actions
```

## Syntax mapping

| django-unicorn | Citry |
|---|---|
| Public view attribute | A `State` field if a later call needs it; otherwise `Kwargs` |
| Method on `UnicornView` | Public method inside `class Events` |
| `unicorn:click="save"` | `@c-click="save"` |
| `unicorn:click="rate(5)"` | `@c-click="rate({ stars: 5 })"` with a typed `data` class |
| `unicorn:model="query"` | `:c-query` to show it, `:c-query="refresh"` to update and call |
| `.debounce-300` | `.debounce.300ms` |
| `.lazy`, `.prevent`, `.stop` | Same names |
| Automatic re-render | Return a new component from the handler |
| `ValidationError` | `raise EventError(..., fields=...)` |
| `unicorn.errors` | `$error("save").fieldErrors` |
| Loading attributes | `$loading()` or `$loading("save")` |
| `unicorn:poll` | `@c-poll.2s="refresh"` |
| `self.call("fn", ...)` | `actions.Dispatch(name, detail)` plus a browser listener |
| `Unicorn.call(...)` | `$sendEvent(name, args)` or `Citry.events.send(...)` |
| Component `key` | `#c-key` on repeated items |

The sections below show the common rows in context.

## Fix dynamic attributes

When you copy a template over, check its attributes first. Citry evaluates
Python in text between tags, but an ordinary HTML attribute value stays a
literal string:

```citry-html
<!-- Wrong in a Citry template: the browser receives
     {{ profile_url }}. -->
<a href="{{ profile_url }}">Profile</a>
```

Prefix the attribute with `c-`, and Citry evaluates its value as a Python
expression:

```citry-html
<!-- Right: profile_url is evaluated during rendering. -->
<a c-href="profile_url">Profile</a>
```

The same applies to `action`, `src`, `class`, and any other attribute. Text
between tags still uses `{{ expression }}`. See
[Attributes](/syntax/attributes/#c-dynamic-attributes).

## Bind values to State

A django-unicorn live search usually keeps the query on the view and
re-renders after the method call:

```python
class LiveSearchView(UnicornView):
    query = ""

    def refresh(self):
        self.results = find_products(self.query)
```

```html
<input unicorn:model.debounce-300="query">
<button unicorn:click="refresh">Search</button>
```

In Citry, `query` is both a render input and a value the next call needs, so
`State` inherits it from `Kwargs`. The binding names the handler to call when
the value changes:

```citry
--8<-- "docs_site/snippets/migrate_unicorn.py:live-search"
```

`:c-query.debounce.300ms="refresh"` waits until the user stops typing for
300 ms, writes the new text into `state.query`, and calls `refresh`. The
handler returns a new `LiveSearch` for that query. The input keeps its focus,
text, and cursor position through the update.

By default, Citry signs State before sending it to the browser, so the
server can detect a changed value. Anyone can still read it in the page
source. Keep State small, and keep secrets out of it.

## Pass call arguments

django-unicorn accepts Python-like call strings and property assignments in
the template:

```html
<button unicorn:click="rate(5)">Five stars</button>
<button unicorn:click="rating=0">Clear</button>
```

In Citry, a call passes one object. The handler's `data` parameter receives
it, checked against the class you annotate it with:

```citry
--8<-- "docs_site/snippets/migrate_unicorn.py:rating"
```

Every change to the component is now a named method with one input type.
When the input carries a database id, load the record inside the handler and
check the current user's permission there.

## Return field errors

In django-unicorn, a `ValidationError` fills the component's error collection
during the automatic re-render. In Citry, the handler raises `EventError` and
returns no render:

```citry
--8<-- "docs_site/snippets/migrate_unicorn.py:validation"
```

The browser receives a `422` response with the field messages.
`$error("save")` holds them for the `save` handler, and the form stays on the
page with everything the user typed. The next successful `save` call clears
that error. Errors from other handlers stay until their own next success.

Citry does not connect Django `Form` or `ModelForm` for you. Run the form in
the handler and pass its errors on:

```python
if not form.is_valid():
    raise EventError(
        "Please fix the errors.",
        fields={
            name: errors[0]
            for name, errors in form.errors.items()
        },
    )
```

[Handle and validate forms](/events/forms/) covers typed form data in full.

## Replace self.call

django-unicorn can ask the browser to run a named JavaScript function. With
`showToast` in Unicorn's `ALLOWED_JS_CALL_LIST`, a component might do this:

```python
def save(self):
    persist_preferences()
    self.call("showToast", "Preferences saved")
```

A Citry handler cannot name a JavaScript function to run. Instead, it returns
`actions.Dispatch`, which fires a named browser event, and JavaScript on the
page decides what to show:

```citry
--8<-- "docs_site/snippets/migrate_unicorn.py:browser-event"
```

In the component's JavaScript, listen with the `onEvent` function that
`onServerRender` receives (see
[Event actions](/events/actions/#notify-browser-code-that-something-happened)),
or with `addEventListener` on an element above it. Start the name with the component's name, as here. Names that start
with `citry:` are reserved, and `actions.Dispatch` rejects them.
[Event actions](/events/actions/) lists everything a handler can return.

## Change State locally

Citry components are also Vue components, so a change that needs no Python
can stay in the browser. `$state` is a Vue object that holds the component's
State:

```citry-html
<button @click="$state.expanded = !$state.expanded">
  Toggle
</button>
```

The click makes no request. The next server call from this component sends
the new value along, unless that call uses GET. See
[`$state` local changes](/events/bindings/#keep-rapid-local-changes-in-the-browser).

## Plan for differences

### Declare State fields

Citry has no public-by-default attributes, dotted property setters, or
Python call expressions in the template. It also does not turn an id into a
model instance for you. Declare State fields, named handlers, and typed
`data` classes, and load records inside the handler. To control which State
fields browser code may read or change, see
[`_public` and `_model`](/events/state/#limit-what-the-browser-can-read-and-change).

### Build dirty markers

There is no equivalent of `unicorn:dirty`. When a form needs one, build it
from Vue state and the
[events Citry fires around each call](/reference/browser-apis/#events-fired-around-each-call).

### Handle offline calls

Citry does not queue calls while the browser is offline. Replaying a change
after a deployment is rarely safe, so it is left to application code.

### Handle files

Citry does not read multipart file uploads by default. To accept files,
register a custom payload codec, a class that turns the request body into
handler input, and have it produce `UploadedFile` values. A handler marked
`@event(bundle=False)` can return `actions.Download(...)`; see
[Event actions](/events/actions/).
Check the [parity matrix](/guides/events-migration-parity/) before porting an
upload flow.

## Finish the port

Before shipping a migrated component, check that:

- State holds only values a later call needs;
- `_public` and `_model`, the State settings that limit which fields
  browser code can read and change, are set where the default (every
  field) is too broad;
- every handler returns the render or action that should happen;
- validation failures raise `EventError` and leave the form in place;
- every database id from State or `data` is checked against the current
  user; and
- repeated interactive items carry a stable `#c-key`.

The [Events migration parity matrix](/guides/events-migration-parity/)
compares the rest of django-unicorn's features with Citry.
[Event state](/events/state/), [Bind events in templates](/events/bindings/),
and [Event actions](/events/actions/) cover the full workflow.
