---
title: Keep State between calls
description: Choose the small values a Citry component carries through the browser and rebuild each event render from explicit inputs.
---

# Keep State between calls

An event handler often needs values from the component it was called from:
which project it shows, which page of results, what the user typed. It does
not receive the component's original inputs. Keep those values in
[`State`][citry.Component.State]: Citry sends them to the browser with the
rendered component, and the browser sends them back with the next call.

Start with [Server events](/events/) if you have not called a Python handler
from a component yet.

## Store the values the next call needs

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

## Build every event render from explicit inputs

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

## Connect an input to State

A `:c-<field>` attribute shows a State field in a form control. Give it a
handler name, and each edit updates the field and calls the handler. This
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

## Limit what the browser can read and change

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

The browser can only replace a whole field. To change one item inside a list
or object field, copy the value, change the copy, and assign it back.

These settings limit what your templates can do. They do not hide anything.
The signed State is visible to anyone who opens the page, and a field the
browser can change may arrive with any value. Validate it in the handler like
any other user input. See [Security](/security/#treat-state-as-client-input).

## Choose between State, js_data, and Vue data

| Data | Put it in | How long it lives |
|---|---|---|
| Small values a later server call needs, or values bound with `:c-*` | `State` | Kept across calls. |
| Larger or computed values the browser code reads | `js_data()` | Recomputed on each render. |
| Browser-only UI state, such as whether a panel is open | Vue `data()` | Kept by the Vue component in the browser. |

Each server render replaces the `js_data()` values, so do not use them for
values that must survive a call. See
[Client interactivity](/concepts/client-interactivity/) for how Python and
browser code share a component.

!!! note "The browser gets State changes even without a re-render"

    When a handler changes State, the response always carries the new values
    of the fields the browser can read (see
    [`$state`](/reference/browser-apis/#state)). This holds when the handler
    returns `None`, returns data, or re-renders only part of the component.
