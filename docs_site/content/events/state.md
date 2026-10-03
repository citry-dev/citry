---
title: Event state
description: Keep the values your Citry event handlers need between calls, and pass every input when a handler renders the component again.
---

# Event state

An event handler often needs values from the component it was called from:
which project it shows, which page of results, what the user typed. It does
not receive the component's original inputs. Keep those values in
[`State`][citry.Component.State]: Citry sends them to the browser with the
rendered component, and the browser sends them back with the next call.

Start with [Server events](/events/) if you have not called a Python handler
from a component yet.

## `State` and `state_data()` { #store-values-in-state }

When the component's inputs are already the values you need, make `State`
inherit from `Kwargs`:

```python
class Kwargs:
    count: int = 0

class State(Kwargs):
    pass
```

A handler receives them through its `state` parameter, and any change it makes
is kept for the next call.

Keep State small: ids, filters, page numbers, flags such as "editing". The
values must be JSON-serializable. When the inputs hold larger objects, declare
a smaller State and fill it from the inputs with `state_data()`:

```citry
class ProjectPanel(Component):
    citry = citry_app

    class Kwargs:
        project: Project
        show_archived: bool = False

    class State:
        project_id: int
        show_archived: bool = False

    def state_data(self, kwargs, slots):
        return {
            "project_id": kwargs.project.id,
            "show_archived": kwargs.show_archived,
        }
```

The handler then loads the project again from `project_id`, as the next
section shows.

## Pass every input { #pass-every-input-when-a-handler-renders-again }

When a handler returns a component, Citry renders it from scratch, using
only the inputs you pass. The original kwargs and slot fills are not kept.

The natural first attempt is to read the original inputs from `self`. That
fails, because `self` in a handler is not the rendered component:

```python
class Events:
    def refresh(self):
        # Wrong: self has no kwargs from the original render.
        return ProjectPanel(project=self.kwargs.project)
```

Instead, keep the id in State, load the record for the current user, and pass
every input explicitly:

```python
class Events:
    def refresh(self, state, request):
        project = load_project_for_user(
            project_id=state.project_id,
            user=current_user(request),
        )
        return ProjectPanel(
            project=project,
            show_archived=state.show_archived,
        )
```

The rule: if the new render needs a value, the handler must get it and pass
it in.

## `:c-<field>` on inputs

A `:c-<field>` attribute shows a State field in a form control. Give it a
handler name, and edits update the field and call the handler. This
live search sends the query 300 ms after the user stops typing:

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

    def template_data(self, kwargs, slots):
        if kwargs.query:
            results = find_products(kwargs.query)
        else:
            results = []
        return {"results": results}

    template = """
      <div>
        <input
          type="search"
          placeholder="Search..."
          :c-query.debounce.300ms="refresh"
        >
        <ul :class="{ searching: $loading() }">
          <c-for each="item in results">
            <li>{{ item.name }}</li>
          </c-for>
        </ul>
      </div>
    """
```

`refresh` renders a new `LiveSearch` for the updated query. Vue updates the
list in place, so the input keeps its focus and cursor position.

[Bind events in templates](/events/bindings/#bind-controls-to-state) lists
every control you can bind and the Python type each one sends.

## `_public` and `_model` { #limit-what-the-browser-can-read-and-change }

By default, browser code can read every State field and change it, through
the `$state` object in templates or a `:c-*` binding. Two settings narrow
that:

```python
class State:
    project_id: int
    page: int = 1
    can_delete: bool = False

    _public = ("page", "can_delete")
    _model = ("page",)
```

- `_public` lists the fields browser code can read.
- `_model` lists the public fields browser code can change.

The browser can only replace a whole field. Changing an item in place, such
as `$state.tags.push(tag)`, throws an error. Copy the value, change the copy,
and assign it back.

These settings limit what your templates can do. They do not hide anything.
The signed State is visible to anyone who opens the page, and a field the
browser can change may arrive with any value. Validate it in the handler like
any other user input. See [Security](/security/#treat-state-as-client-input).

## Choose where data lives

| Data | Put it in | How long it lives |
|---|---|---|
| Small values a later server call needs, or values bound with `:c-*` | `State` | Kept across calls. |
| Larger or computed values the browser code reads | `js_data()` | Recomputed on each render. |
| Browser-only UI state, such as whether a panel is open | Vue `data()` | Kept by the Vue component in the browser. |

Each server render replaces the `js_data()` values, so do not use them for
values that must survive a call. See
[Where each value goes](/vue/#where-each-value-goes) for how Python and
browser code share a component.

!!! note "The browser gets State changes even without a re-render"

    When a handler changes State, the response always carries the new values
    of the fields the browser can read (see
    [`$state`](/reference/browser-apis/#state)). This holds when the handler
    returns `None`, returns data, or re-renders only part of the component.

## Subclass State

A subclass uses its parent's `State` until it declares its own. To add
fields, name the parent's class as a base. The subclass keeps the
parent's fields and settings, such as `_public` and `_model`:

```python
class SortedProjectPanel(ProjectPanel):
    class State(ProjectPanel.State):
        sort: str = "name"
```

`ProjectPanel` is the component from
[`State` and `state_data()`](#store-values-in-state). Because the subclass
keeps any `_public` its parent sets, list a new field there too when
browser code should read it.

A plain `class State:` in the subclass replaces the parent's fields and
settings. It starts from the defaults: browser code can read and change
every field, the values are stored, signed, in the page, and the size
limit (`_max_bytes`) is the default. Citry warns when the class is
defined if the new State drops a parent field, or does not set a
`_public`, `_model`, or `_max_age` that the parent sets. `_max_age` is
how long the values stay valid.

If the parent's State keeps its values on the server with
`_storage = "server"` (see
[Security](/security/#treat-state-as-client-input)), a plain `class State:`
that does not set `_storage` raises `ValueError` when the class is
defined, because its values would be stored in the page, where anyone
who opens the page can read them. Name the parent's class, or set `_storage` yourself.

[Subclass components](/advanced/subclassing/) covers the same rule for
`Kwargs` and the other nested classes.
