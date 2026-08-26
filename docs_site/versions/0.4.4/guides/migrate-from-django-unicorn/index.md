---
title: Migrate from django-unicorn
url: https://citry.dev/v/0.4.4/guides/migrate-from-django-unicorn/
description: "Move django-unicorn state, actions, validation, and browser calls to explicit Citry State and Events handlers."
---
# Migrate from django-unicorn

If a component sends every public attribute on each interaction, it becomes
hard to tell which values are truly part of the client contract. In Citry,
render inputs live in `Kwargs`, round-trip values live in an explicit `State`,
and browser calls reach only methods declared in `Events`.

The template vocabulary remains familiar. The important shift is from an
implicit mutable view object to a small declared State plus a fresh component
tree returned by each handler that changes the page.

The Citry examples assume the configured `citry_app` from
[Server events](/v/0.4.4/events/#configure-a-signing-secret-before-using-state)
and these imports:


```python
from typing import Any

from citry import Component
from citry.ext.events import EventError, actions
```


## Move bound attributes into State

A django-unicorn search commonly puts the query directly on the view and lets
the framework re-render after the method call:


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


In Citry, `query` is both an initial render input and a value needed by later
calls, so `State` inherits it from `Kwargs`. The binding names the handler that
receives the updated value:


```citry
class LiveSearch(Component):
    citry = citry_app

    class Kwargs:
        query: str = ""

    class State(Kwargs):
        pass

    class Events:
        def refresh(self, state):
            return LiveSearch(query=state.query)

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        results = find_products(kwargs.query) if kwargs.query else []
        return {"results": results}

    template = """
      <div>
        <input
          type="search"
          :c-query.debounce.300ms="refresh"
        >
        <ul>
          <c-for each="item in results">
            <li>{{ item.name }}</li>
          </c-for>
        </ul>
      </div>
    """


```


`:c-query.debounce.300ms="refresh"` waits for 300 ms of quiet, sends the
declared field update alongside the current signed State token, and calls
`refresh`. The token contains the full declared State. The handler builds a new
`LiveSearch` explicitly. Focus, the input value, and the caret survive the
resulting morph.

If several handlers render the same component, add an author-defined helper
to the State class if it makes the repeated constructor clearer:


```python
class State(Kwargs):
    def render(self):
        return LiveSearch(query=self.query)
```


`render()` is ordinary application code, not a State method supplied by
Citry.

## Replace wire expressions with typed handlers

django-unicorn accepts Python-like call strings and direct property setters:


```html
<button unicorn:click="rate(5)">Five stars</button>
<button unicorn:click="rating=0">Clear</button>
```


Citry uses one Alpine object expression as event data, then validates it
against the handler's declared input:


```citry
class RatingIn:
    stars: int


class Rating(Component):
    citry = citry_app

    class Kwargs:
        value: int = 0

    class Events:
        def rate(self, data: RatingIn):
            save_rating(data.stars)
            return Rating(value=data.stars)

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"value": kwargs.value}

    template = """
      <button @c-click="rate({ stars: 5 })">Five stars</button>
      <button @c-click="rate({ stars: 0 })">Clear</button>
      <output>{{ value }}</output>
    """


```


This makes each mutation a greppable method with one schema. Load models from
validated ids inside the handler and repeat authorization there.

## Return field errors without replacing the form

In django-unicorn, form integration or a `ValidationError` populates the
component error collection during its automatic re-render. Citry makes the
failed-call behavior explicit: raise `EventError` and do not render.


```citry
class ContactIn:
    email: str = ""


class ContactForm(Component):
    citry = citry_app

    class Events:
        def submit(self, data: ContactIn):
            if "@" not in data.email:
                raise EventError(
                    "Please fix the errors.",
                    fields={"email": "Enter a valid email address."},
                )
            return ContactForm()

    template = """
      <form @c-submit.prevent="submit">
        <input name="email">
        <span x-text="$error('save')?.fieldErrors.email"></span>
        <button type="submit">Send</button>
      </form>
    """


```


The response carries status 422 and the field map. `$error("save")` exposes
that handler's map to Alpine, while the existing form stays in the DOM with
everything the user typed. A later successful `save` call clears that error
without clearing errors retained for other handlers.

Django `Form` and `ModelForm` convenience wiring is a later addition. Today,
run the form in the handler and translate `form.errors` yourself:


```python
if not form.is_valid():
    raise EventError(
        "Please fix the errors.",
        fields={name: errors[0] for name, errors in form.errors.items()},
    )
```


## Replace server-selected JavaScript calls with browser events

django-unicorn can queue a named JavaScript function from Python:

When `showToast` has been added to Unicorn's `ALLOWED_JS_CALL_LIST`, an
existing component may call it from Python:


```python
def save(self):
    persist_preferences()
    self.call("showToast", "Preferences saved")
```


Citry handlers return a closed set of actions. Dispatch a named browser event,
then let page JavaScript decide how it appears:


```citry
class Preferences(Component):
    citry = citry_app

    class Events:
        def save(self):
            save_preferences()
            return actions.Dispatch(
                "Preferences:saved",
                {"message": "Preferences saved"},
            )

    template = """
      <button @c-click="save">Save</button>
    """


```


Listen with `$onEvent("Preferences:saved", callback)` in Alpine or
Component.js, or with ordinary `addEventListener`. This keeps Python from
selecting and invoking arbitrary client functions.

Local-only interactions stay in Alpine. For example,
`@click="$state.expanded = !$state.expanded"` changes writable State locally,
and the next server call carries the queued update.

## Translate dynamic HTML attributes

Citry evaluates Python in text interpolation, but ordinary HTML attribute
values remain literal strings:


```html
<!-- Wrong in a Citry template: the browser receives {{ profile_url }}. -->
<a href="{{ profile_url }}">Profile</a>
```


Use the `c-` dynamic-attribute prefix:


```html
<!-- Right: profile_url is evaluated during rendering. -->
<a c-href="profile_url">Profile</a>
```


The same rule applies to dynamic `action`, `src`, `class`, and other HTML
attributes. Keep `{{ expression }}` for element text.

## Syntax mapping

| django-unicorn | Citry Events |
|---|---|
| Public view attribute | A declared `State` field if it must round-trip; otherwise `Kwargs` or derived template data |
| `unicorn:click="save"` | `@c-click="save"` |
| `unicorn:click="rate(5)"` | `@c-click="rate({ stars: 5 })"` with typed `data` |
| `unicorn:model="query"` | `:c-query` for display, or `:c-query="refresh"` for update plus call |
| `.debounce-300` | `.debounce.300ms` |
| `.lazy` | `.lazy` |
| `.prevent` / `.stop` | `.prevent` / `.stop` |
| Method on `UnicornView` | Public method inside `class Events` |
| Automatic re-render | Return a fresh component or `state.render()` helper you define |
| `ValidationError` / `unicorn.errors` | `EventError(..., fields=...)` / `$error("save").fieldErrors` |
| Loading attributes | `$loading()` or `$loading("save")` in an Alpine expression |
| `unicorn:poll` | `@c-poll.2s="refresh"` |
| `self.call("fn", ...)` | `actions.Dispatch(name, detail)` plus a browser listener |
| `Unicorn.call(...)` | `$sendEvent(name, args)` or `Citry.events.send(...)` |
| Component `key` | `#c-key` on reorderable or interactive children |

## Keep State explicit and small

Citry intentionally has no public-by-default attribute bag, dotted property
setter, ORM-primary-key revival, or Python call-expression parser on the wire.
Those features blur data, routing, and authorization into one input language.
The replacement is a short explicit list: State fields, named Events methods,
typed data, and record loading inside the handler.

Dirty-input styling can be built from Alpine state and lifecycle events when a
form needs it. Offline call queues are left to application-specific code
because replaying a mutation across a deployment is rarely safe. Multipart
uploads are not part of Events v1. A file-producing handler can use
`actions.Download(...)` when it is marked `@event(bundle=False)` and called
through its per-event route; check the
[parity matrix](/v/0.4.4/guides/events-migration-parity/) before porting upload flows.

## Finish the port

Before shipping a migrated component, check that:

- only values needed by a later call are in State;
- `_public` and `_model` narrow client access where the default is too broad;
- every handler returns the render or action that should happen;
- validation failures raise `EventError` without destroying the form;
- every database id from State or `data` is authorized again; and
- reorderable interactive children carry stable `#c-key` values.

Continue with [State](/v/0.4.4/events/state/), [event bindings](/v/0.4.4/events/bindings/), and
[event actions](/v/0.4.4/events/actions/) for the full Citry workflow. The
[Events migration parity matrix](/v/0.4.4/guides/events-migration-parity/) tracks
which broader django-unicorn capabilities are available now or planned later.