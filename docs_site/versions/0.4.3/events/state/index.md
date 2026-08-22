---
title: Keep State between calls
url: https://citry.dev/v/0.4.3/events/state/
description: "Choose the small values a Citry component carries through the browser and rebuild each event render from explicit inputs."
---
# Keep State between calls

[`State`](/v/0.4.3/reference/component/#citry-component-state) holds the small values that a later server
call needs. Citry restores those values for the next handler and keeps the
browser's public State in sync.

Start with [Server events](/v/0.4.3/events/) if you have not called a Python handler
from a component yet.

## Add live search with one State binding

Use `:c-query` to connect a control to a public State field. Giving the
attribute a handler name makes it two-way: the edit and the named call travel
together, so the handler receives the latest State.


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
        results = find_products(kwargs.query) if kwargs.query else []
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


The data flow is explicit:

1. `query` starts as a component input.
2. `class State(Kwargs)` makes that field part of the round trip.
3. `:c-query` displays the State value in the input.
4. `.debounce.300ms="refresh"` waits for 300 ms of quiet, then sends the
   pending value and calls `refresh` once.
5. `refresh` builds a new `LiveSearch` from the updated State.
6. `template_data` performs the search for that new render.
7. The morph updates the result list while preserving the focused input and
   its caret.

## Choose what survives in State

`Kwargs` describes one render. `State` describes only the small,
JSON-serializable values needed by later calls. Keep database ids, short
filters, page numbers, and editing flags there. Reload records and permission
facts in the handler.

For a leaf component whose inputs are already the right State, inherit the
schema:


```python
class State(Kwargs):
    pass
```


For richer inputs, declare a smaller State and derive it at render time:


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


All State fields are public and writable by default. Narrow the client surface
only when needed:


```python
class State:
    project_id: int
    page: int = 1
    can_delete: bool = False

    _public = ("page", "can_delete")
    _model = ("page",)
```


`_public` selects which fields client expressions may read. `_model` selects
which public fields they may write through `$state` or a two-way binding.
These lists are capability controls, not secrecy controls. Signed State travels
through the browser and must be treated as client input. Server-held State
keeps its values out of the token, but client-writable fields are still client
input. See [Security](/v/0.4.3/security/#treat-state-as-client-input).

## Build every event render from explicit inputs

A handler's render is a fresh component tree. It does not retain the original
component's kwargs or slot fills.

The natural first attempt fails because `self` is the per-call Events object,
not the rendered component:


```python
class Events:
    def refresh(self):
        # Wrong: the original component inputs do not exist here.
        return ProjectPanel(project=self.kwargs.project)
```


Carry the durable id in State, reload the authorized object, and pass every
input explicitly:


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


This is the golden rule for Events rendering: if a later render needs a value,
the handler must obtain it and pass it to the new tree.

## Put data in State, js_data, or x-data deliberately

| Data kind | Put it in | Lifetime |
|---|---|---|
| Small values a later server call needs, or values used by `:c-*` | `State` | Survives calls and self-renders; signed storage travels through the browser. |
| Large or derived browser values | `js_data()` | Recomputed for each render; transport is deduplicated, but each instance gets a fresh nested graph. |
| Client-only UI state such as an open accordion | `x-data` | Owned by Alpine in the current client region. |

`js_data()` is not persistent Events State. Citry seeds its top-level keys into
the instance's reactive Alpine scope, but a server rerender refreshes those
server-owned keys. Put ongoing browser-only changes and functions on `scope`,
and put values needed by later server calls in Events `State`. See [Client
interactivity](/concepts/client-interactivity/) for the complete component
boundary and Component.js contract.