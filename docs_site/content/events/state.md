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
values must be JSON-serializable, or, for a
[Pydantic State](#pydantic-state), values Pydantic writes as JSON and
reads back unchanged. When the inputs hold larger objects, declare a
smaller State and fill it from the inputs with `state_data()`:

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
values that must survive a call. The server cannot read Vue `data()`, so a
panel hidden with `v-show` shows open until Vue starts. Moving the value from
`data()` to `js_data()` makes the page load closed, but each server render
then resets it, so a panel the user opened closes on the next re-render.
[Before Vue starts](/vue/server-rendering/#what-a-hydrated-page-shows-before-vue-starts)
covers the other bindings. See
[Where each value goes](/vue/#where-each-value-goes) for how Python and
browser code share a component.

!!! note "The browser gets State changes even without a re-render"

    When a handler changes State, the response always carries the new values
    of the fields the browser can read (see
    [`$state`](/reference/browser-apis/#state)). This holds when the handler
    returns `None`, returns data, or re-renders only part of the component.

## Pydantic State { #pydantic-state }

To have Pydantic check State, so a handler that sets a field to the wrong
type fails at once, write `State` as a Pydantic v2 or v1 model:

```citry
from pydantic import BaseModel


class Filters(Component):
    citry = citry_app

    class State(BaseModel):
        query: str = ""
        page: int = 1
        _public = ("query",)
```

A Pydantic v2 State (a model or a Pydantic dataclass) needs Pydantic
2.13.0 or newer. On an older Pydantic, defining the component raises
`RuntimeError`.

A plain `class State:` becomes a model too when you pass a Pydantic model
as [`Citry(model_base=...)`](/concepts/inputs-and-validation/#model-base).
A component from a library you install keeps the State its author wrote.
Settings such as `_public` and `_storage` work as on any State; other
underscore names are reserved for them.

A model State can also hold nested models, dates, and other values
Pydantic writes as JSON and reads back unchanged. Browser code reads them
as JSON, so a date is a string such as `"2026-01-02"`, and the next call
turns them back into dates and models.

Pydantic checks the values at three points, so your validators run at
each one:

- **When a call restores State.** If the values in the page no longer fit
  the model, for example because you changed a field's type and deployed,
  the call fails with `stale_state` (409) and Citry asks the user to reload
  the page ([details](/reference/browser-apis/#events-fired-around-each-call)).
- **When the browser writes a field.** The call fails with `invalid_args`
  (422) before the handler runs, with Pydantic's message for each bad
  field (for a list or dict, only its first bad item). A write with too
  many errors, too large or nested too deeply to check, or with field
  paths too long in total gets one message instead, under
  `fieldErrors._state`, the key for a message about the whole write
  rather than one field ([details](/security/#check-event-data)).
- **After a handler changes State.** If a new value does not fit, such as
  `state.page = "two"` or a wrong-typed item appended to a list, the call
  fails with `handler_error` (500), the page keeps its old State, and the
  server log names the component and the handler. Anything else the
  handler did, such as a database write, stays done.

With `validate_assignment=True`, a wrong assignment raises at that line in
the handler, and the call fails with `handler_error`.

A validator that raises an exception other than `ValueError` or
`AssertionError`, such as `RuntimeError`, is a bug in your validator.
When it happens while Citry checks a browser write, the call fails with a
422 and "The State could not be checked." under `fieldErrors._state`, and
Citry logs the error. This holds for a model State and for a Pydantic
dataclass State, with or without `validate_assignment`. A Pydantic v1
model also turns a `TypeError` into a message for its field.

Citry raises `ValueError` when the component class is defined if State,
or a model nested in it, uses one of these, because it could not store and
restore State with them:

- a frozen model (`frozen=True`, or `allow_mutation = False` in v1), or a
  frozen field;
- a field left out of the dump (`exclude=True` or `exclude_if`), or a
  serializer (`model_serializer`, `field_serializer`, `PlainSerializer`,
  `WrapSerializer`);
- a secret type such as `SecretStr`, which Pydantic writes masked;
- a field alias in a v1 model, unless the model sets
  `allow_population_by_field_name = True`.

Citry stores and restores State by field name, so a field alias only
affects input you pass the model yourself.

A Pydantic v2 State can't hold a `pydantic.v1` model or dataclass,
or check a field with a method of one, as in
`PlainValidator(Model.parse_obj)`. Defining the component raises
`ValueError`, naming the State and the v1 class. Make that class a
Pydantic v2 model. A State that is itself a `pydantic.v1` model still
works.

Pydantic decides what a browser write may hold. A field the browser may
write (`_model`) with a type such as `ImportString` would import whatever
module the browser names, so keep such types out of writable fields.

A request can carry several calls (up to 16), and the calls often carry
the same State. Citry can then restore those values once and give each
call its own copy. So a validator with a side effect can run fewer times
than there are calls, and a default that changes on each run, such as
`default_factory=uuid4` for a field that the saved State lacks (a field
you added in a deploy after the page loaded, for example), can give
several calls the same value.

### Pydantic dataclass State { #pydantic-dataclass-state }

A State can be a Pydantic dataclass too:

```citry
from pydantic import model_validator
from pydantic.dataclasses import dataclass


class Range(Component):
    citry = citry_app

    @dataclass
    class State:
        low: int = 0
        high: int = 10

        @model_validator(mode="after")
        def ordered(self):
            if self.low > self.high:
                msg = "low must not exceed high"
                raise ValueError(msg)
            return self
```

Pydantic checks nothing when code assigns a field of a dataclass, unless
the class sets `validate_assignment=True`, so Citry checks each browser
write itself, when it arrives. The writes one call carries are checked
together, as one batch: when the class refuses a value, the call fails
with `invalid_args` (422) and none of the batch's writes reach the State.
With the class above, a write that sets `low` to 30 fails with "Value
error, low must not exceed high" under `fieldErrors._state`.

Without `validate_assignment`, Citry first checks each written value
against its field, in the order the class declares its fields. A field
validator with an `info` parameter reads the fields declared before its
own in `info.data`, and that includes this call's writes to them, as
when Pydantic builds the class. Then, if the class has a model
validator, a `__post_init__`, a validator with an `info` parameter, or a
`default_factory` that takes the other fields, Citry builds the whole
State once, with the call's writes in it, so those run on the write too.
An error from a model validator or `__post_init__` lands under
`fieldErrors._state`.

Citry also builds the whole State when an `info` validator or a
`default_factory` that takes the other fields sits in a nested model. A
nested model's own model validator or `__post_init__` does not need it,
because checking that field already runs them.

With `validate_assignment=True`, Citry checks each assigned field, as
the class does.

Without `validate_assignment`, the State keeps each value as the
browser sent it, as the class itself does, until the next call restores
it: a field typed `tuple[int, ...]` written as `[1, 2]` holds the list
`[1, 2]` until then, and the tuple `(1, 2)` after.

!!! note "A large State makes each write slower"

    Each time Citry builds the whole State for a write, it takes longer
    the larger the State is. If your State is large, keep only an id in
    it and load the rest in the handler, or set `validate_assignment=True`.

### Fix a tree in State { #trees-in-state }

When State is a Pydantic model, defining the component raises
`ValueError` if the browser may write a field that holds a tree whose
nodes can be different classes, some of them holding more nodes. In this
filter, an `And` or `Or` holds more filters, and a `Cond` ends a branch:

```python
from typing import Annotated, Literal

from pydantic import BaseModel, Discriminator, Field, Tag


class Cond(BaseModel):
    field: str


class And(BaseModel):
    items: list["Node"]


class Or(BaseModel):
    any: list["Node"]


Node = And | Or | Cond


class State(BaseModel):
    filter: Node | None = None
```

The error says that `filter` "holds a union without a discriminator
inside a recursive type". The union is `Node`. A recursive type is a
type that contains itself: `And` holds a list of `Node`. A discriminator
is a field, or a function, that tells Pydantic which class in a union a
value is. The browser may write the fields in `_model`, or every public
field when you do not set `_model`. A plain `class State:`
that `Citry(model_base=BaseModel)` turns into a model gets the same
error.

Pick one fix. A discriminator on the State field alone does not reach
the unions inside the tree, so the first two fixes go on the recursive
type itself:

- Give each class a `Literal` tag field, and declare the discriminator
  on the recursive type:

    ```python
    class And(BaseModel):
        type: Literal["and"] = "and"
        items: list["Node"]


    # Or and Cond get a tag field of their own in the same way.
    Node = Annotated[And | Or | Cond, Field(discriminator="type")]
    ```

    Each node must then carry its tag: the browser's write of a node
    without it is refused, so update browser code that builds nodes. If
    the nodes had no tag field before, a page opened before the deploy
    with a tree in its State asks the visitor to reload once, on its
    next event call, because that State no longer fits the model.
- Use a callable `Discriminator` with a `Tag` on each class. When each
  class has a field the others lack, here `items` on `And`, `any` on
  `Or` and `field` on `Cond`, the function picks the class from those
  fields, so the browser writes the same data as before:

    ```python
    def pick(v):
        if isinstance(v, dict):
            if "any" in v:
                return "or"
            return "and" if "items" in v else "cond"
        return {And: "and", Or: "or", Cond: "cond"}.get(type(v))


    Node = Annotated[
        Annotated[And, Tag("and")]
        | Annotated[Or, Tag("or")]
        | Annotated[Cond, Tag("cond")],
        Discriminator(pick),
    ]
    ```

    When some types in the union are lists or tuples, such as
    `Node = list[Node] | tuple[Node, ...] | int`, a callable
    `Discriminator` is the only discriminator fix, because a list cannot
    carry a tag field.
- Set `_model` to the fields the browser may change, without the tree.
  The browser can then no longer write that field
  ([details](/security/#schemas-citry-refuses)).

A Pydantic dataclass State with such a tree is not refused. A browser
write to it that nests too deeply fails with one message under
`fieldErrors._state`. A deep tree that your own code puts in State, in
`state_data()` or a handler, restores on the next call as saved.

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
