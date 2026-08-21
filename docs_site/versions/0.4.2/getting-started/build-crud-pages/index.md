---
title: Build CRUD pages
url: https://citry.dev/v/0.4.2/getting-started/build-crud-pages/
description: "Keep repeated event-driven rows independent, then coordinate controls owned by their list."
---
# Build CRUD pages

Imagine a CRUD admin table view. Each row is one record, and each row has
buttons for editing or deleting the row. Each row also has its own loading,
errors, and success message. Meanwhile, the controls above and below the table
may need to move together.

You will build that shape in three layers:

- one `TaskRow` instance per task;
- one `onEvent` for each row's result;
- one `TaskList` that renders `TaskRow` and manages the list controls.

Continue from [Update page from
Python](/getting-started/server-rendered-updates/). Keep `citry_setup.py` and
`app.py` unchanged.

## Build the page

Replace `components.py` with this version:

```citry
from dataclasses import dataclass

from citry import Component
from citry.ext.events import EventError, actions

from citry_setup import citry_app


@dataclass
class Task:
    id: int
    title: str
    completed: bool = False


# This represents the "database" of tasks.
# In a real app, this would be stored in a database.
TASKS = [
    Task(id=1, title="Review the draft", completed=True),
    Task(id=2, title="Send the invitation"),
    Task(id=3, title="Publish the notes"),
]


def load_tasks(*, hide_completed: bool = False) -> list[Task]:
    if hide_completed:
        return [task for task in TASKS if not task.completed]
    return TASKS


class RenameTaskIn:
    title: str


class TaskRow(Component):
    citry = citry_app

    class Kwargs:
        task_id: int
        title: str

    class Slots:
        pass

    # Remember the task ID in State so we don't have
    # to send it with each event.
    class State:
        task_id: int

    class Events:
        # Update the task title in TASKS.
        # Return a message to display in the UI.
        def save(self, data: RenameTaskIn, state: "TaskRow.State"):
            title = data.title.strip()
            if len(title) < 3:
                raise EventError(
                    "Give the task a longer title.",
                    fields={"title": "Use at least three characters."},
                )

            # Perform a "database" update.
            for task in TASKS:
                if task.id == state.task_id:
                    task.title = title
                    break

            return actions.Dispatch(
                "TaskRow:saved",
                {"taskId": state.task_id, "title": title},
            )

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {
            "task_id": kwargs.task_id,
            "title": kwargs.title,
        }

    template = """
      <li class="task-row">
        <form @c-submit.prevent="save">
          <label>
            Task {{ task_id }}
            <input
              name="title"
              c-value="title"
              required
            />
          </label>
          <button
            type="submit"
            :disabled="$loading('save')"
          >
            Save
          </button>
          <p
            role="alert"
            x-show="$error('save')"
            x-text="$error('save')?.fieldErrors?.title || ''"
          ></p>
          <output x-text="saveStatus"></output>
        </form>
      </li>
    """

    js = """
      // Display a message when this row's task title
      // is successfully saved.
      $component(({ onEvent, scope }) => {
        scope.saveStatus = '';
        onEvent('TaskRow:saved', (detail) => {
          scope.saveStatus =
            `Saved task ${detail.taskId}: ${detail.title}`;
        });
      });
    """


class TaskRows(Component):
    citry = citry_app

    class Kwargs:
        tasks: list[Task]

    class Slots:
        pass

    def template_data(self, kwargs, slots):
        return {"tasks": kwargs.tasks}

    template = """
      <c-for each="task in tasks">
        <c-TaskRow
          #c-key="task.id"
          c-task_id="task.id"
          c-title="task.title"
        />
      </c-for>
    """


class FilterTasksIn:
    hide_completed: bool


class TaskFilterToggle(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <button
        type="button"
        :disabled="clientProps.loading"
        x-text="
          clientProps.hideCompleted
            ? 'Show all tasks'
            : 'Hide completed tasks'
        "
      ></button>
    """

    js = """
      $component({
        props: {
          hideCompleted: { type: Boolean, required: true },
          loading: { type: Boolean, required: true },
        },
        init: ({ props, scope }) => {
          scope.clientProps = props;
        },
      });
    """


class TaskList(Component):
    citry = citry_app

    class Kwargs:
        tasks: list[Task]

    class Slots:
        pass

    class Events:
        def filter_tasks(self, data: FilterTasksIn):
            visible_tasks = load_tasks(
                hide_completed=data.hide_completed,
            )
            return [
                actions.Dispatch(
                    "TaskList:filter-changed",
                    {"hideCompleted": data.hide_completed},
                ),
                actions.Render(
                    TaskRows(tasks=visible_tasks),
                    target="#task-rows",
                    swap="inner",
                ),
            ]

    def template_data(self, kwargs, slots):
        return {
            "tasks": kwargs.tasks,
        }

    template = """
      <section>
        <c-TaskFilterToggle
          $c-props="{
            hideCompleted,
            loading: $loading('filter_tasks'),
          }"
          @c-click="filter_tasks({
            hide_completed: !hideCompleted,
          })"
        />

        <ul id="task-rows">
          <c-TaskRows c-tasks="tasks" />
        </ul>

        <c-TaskFilterToggle
          $c-props="{
            hideCompleted,
            loading: $loading('filter_tasks'),
          }"
          @c-click="filter_tasks({
            hide_completed: !hideCompleted,
          })"
        />
      </section>
    """

    js = """
      $component(({ onEvent, scope }) => {
        scope.hideCompleted = false;
        onEvent(
          'TaskList:filter-changed',
          (detail) => {
            scope.hideCompleted = detail.hideCompleted;
          },
        );
      });
    """


class TutorialPage(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs, slots):
        return {"tasks": load_tasks()}

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Task list</title>
          <c-css />
        </head>
        <body>
          <main>
            <h1>Task list</h1>
            <c-TaskList c-tasks="tasks" />
          </main>
          <c-js />
        </body>
      </html>
    """

```

Open `http://127.0.0.1:8000/`. Each row can save independently. Try a
two-character title in one row to keep its validation error visible, then
save another row. The first error stays in place.

`TaskList` renders the same `TaskFilterToggle` component above and below the
rows. Hide completed tasks with either control. The server sends back the two
unfinished tasks, and both controls change to "Show all tasks."

## Preserve browser state

The list renders the same component class several times:


```citry-html
<c-for each="task in tasks">
  <c-TaskRow
    #c-key="task.id"
    c-task_id="task.id"
    c-title="task.title"
  />
</c-for>
```


Each `<c-TaskRow>` is a separate component instance with its own
[`State`](/v/0.4.2/reference/component/#citry-component-state), call queue, loading counters, and handler
errors.

`#c-key="task.id"` tells Citry which row is which, so Citry can safely [morph them](https://alpinejs.dev/plugins/morph){: target="_blank" rel="noopener"}. Morphing means that when you re-fetch the list with changed order or items, any browser state of the old list keeps working (eg a text field keeps the end user's input). Without the key, rows are
matched by position.

!!! note

    Use a stable application identifier for the key. A database primary key,
    slug, or other domain ID is suitable. **DO NOT** use a Citry component ID, it changes with each render.

## Pass inputs to event handlers

The `save` handler needs the new title and the ID of the task to update. There
are three good ways to give it that ID.

### Keep the ID in State

This lesson keeps the ID in [`State`](/v/0.4.2/reference/component/#citry-component-state):


```citry
class RenameTaskIn:
    title: str

class TaskRow(Component):
    class State:
        task_id: int
```


In this component, Citry starts `state.task_id` from the matching
`Kwargs.task_id`, which the list passes with `c-task_id`. When the form is
submitted, `RenameTaskIn` carries the edited title, while `State` remembers
which task this row belongs to. The form does not need a hidden field for the
ID.

### Submit the ID as a form field

The second option is to send both values with the form:


```python
class RenameTaskIn:
    task_id: int
    title: str
```



```citry-html
<input
  type="hidden"
  name="task_id"
  c-value="task_id"
/>
```


The handler would then use `data.task_id`, and `TaskRow` would not need a
`State` class. This keeps everything `save` needs together in `data`, but every
form must now carry its own `task_id` field.

### Pass the ID from Alpine

The third option is to keep the ID in Alpine and add it when the form calls
`save`:


```citry-html
<form
  c-x-data="{ taskId: task_id }"
  @c-submit.prevent="save({ task_id: taskId })"
>
  <!-- The title input and submit button stay the same. -->
</form>
```


`@c-submit` combines the form's named controls with the object passed to
`save`, so `RenameTaskIn` receives both `title` and `task_id`. This version
also needs no `State` class or hidden input.

## Error and loading state

Each row is an isolated component environment:

- Own event handlers
- Own State
- Own Alpine data context

Inside the row, call [`$loading()`](/v/0.4.2/reference/browser-apis/#loading) and [`$error()`](/v/0.4.2/reference/browser-apis/#error) to get loading/error state
scoped to this row:


```citry-html
<button type="submit" :disabled="$loading('save')">
  Save
</button>
<p
  role="alert"
  x-show="$error('save')"
  x-text="$error('save')?.fieldErrors?.title || ''"
></p>
```


The handler name `'save'` picks errors specifically coming from the event handler named `save`. A success clears the error.

When one component contains several handlers, `$error()` returns its newest
retained error for a component-wide banner. `$error('save')` remains the
better choice beside one form.

`$error()` and `$loading()` are also accessible inside the component callback [`$component`](/v/0.4.2/reference/browser-apis/#component) as `error()` and `loading()`. Note, these functions return [Alpine reactive objects](https://alpinejs.dev/advanced/reactivity){: target="_blank" rel="noopener"}, and the accessing logic must be wrapped in `effect()`:


```js
$component(({ error, loading, effect }) => {
  // Same data as the ones in `x-data` and `:disabled`
  scope.text = '';
  scope.disabled = false;

  // Call the functions inside effect() so the changes propagate
  effect(() => {
    scope.text = error('save')?.fieldErrors?.title || '';
    scope.disabled = loading('save');
  });
});
```


## Event actions are isolated

Every row uses the same event handler `save`, and so returns the same event name:


```python
return actions.Dispatch(
    "TaskRow:saved",
    {"taskId": state.task_id, "title": title},
)
```


Despite this, the dispatched event `TaskRow:saved` **DOES NOT** leak across the rows.

When you use [`onEvent`](/v/0.4.2/reference/browser-apis/#on-event), Citry smartly passes that Dispatch action to the component instance whose handler
returned it. The row listens with its instance-scoped `onEvent` helper:


```js
$component(({ onEvent, scope }) => {
  scope.saveStatus = '';
  onEvent('TaskRow:saved', (detail) => {
    scope.saveStatus =
      `Saved task ${detail.taskId}: ${detail.title}`;
  });
});
```


## Bypass Dispatch event isolation

The recommended pattern is to use `onEvent` and keep the events coming from `Dispatch` isolated.

But if you need, you can use Alpine's
[`@event`](https://alpinejs.dev/directives/on){: target="_blank" rel="noopener"} listeners
or browser's [`addEventListener()`](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener){: target="_blank" rel="noopener"}
to listen for the events.

The browser events triggered by `Dispatch` are regular
browser events. For example,
`Dispatch("taskrow:saved", ...)` can be heard by
`@taskrow:saved="..."`.

Regular event bubbling rules apply - the listener hears the event on the dispatching root
or an ancestor, but not on a descendant or a sibling.

## Filter feature end-to-end

One task in the example is already complete. Filtering therefore needs a
server request: Python chooses which tasks still match, then rerenders the
list with two rows instead of three.

`TaskFilterToggle` owns the button markup. It reads the reactive values its
parent passes through `clientProps`:


```citry-html
<button
  type="button"
  :disabled="clientProps.loading"
  x-text="
    clientProps.hideCompleted
      ? 'Show all tasks'
      : 'Hide completed tasks'
  "
></button>
```


`TaskList` renders that component twice. Each copy receives the same list
filter and calls the same list-owned handler:


```citry-html
<c-TaskFilterToggle
  $c-props="{
    hideCompleted,
    loading: $loading('filter_tasks'),
  }"
  @c-click="filter_tasks({
    hide_completed: !hideCompleted,
  })"
/>

<!-- Task rows appear between the two controls. -->

<c-TaskFilterToggle
  $c-props="{
    hideCompleted,
    loading: $loading('filter_tasks'),
  }"
  @c-click="filter_tasks({
    hide_completed: !hideCompleted,
  })"
/>
```


The `$c-props` expressions run in `TaskList`, so both controls read its
`hideCompleted` value and loading state.

When `TaskFilterToggle` is clicked, this triggers the `@c-click` listener, which calls the server-side `filter_tasks`. The `@c-click` belongs
to `TaskList`. The browser listens for the click on the real button
rendered by `TaskFilterToggle`.

The `filter_tasks` event handler uses the requested filter to select tasks on the server. It then
returns two actions in order:


```python
# TaskList.Events.filter_tasks
def filter_tasks(self, data: FilterTasksIn)
    visible_tasks = load_tasks(
        hide_completed=data.hide_completed,
    )
    return [
        actions.Dispatch(
            "TaskList:filter-changed",
            {"hideCompleted": data.hide_completed},
        ),
        actions.Render(
            TaskRows(tasks=visible_tasks),
            target="#task-rows",
            swap="inner",
        ),
    ]
```


The [`Render`](/v/0.4.2/reference/events/#citry-ext-events-actions-render) action replaces the contents of `#task-rows` with a `TaskRows`
component containing only the matching rows. It leaves `TaskList` and both
filter controls in place. The [`Dispatch`](/v/0.4.2/reference/events/#citry-ext-events-actions-dispatch) action updates that existing list
scope and tells both controls whether the filter is now active.

`TaskList` registers an
instance-scoped listener in its `$component` callback:


```js
$component(({ onEvent, scope }) => {
  scope.hideCompleted = false;
  onEvent(
    'TaskList:filter-changed',
    (detail) => {
      scope.hideCompleted = detail.hideCompleted;
    },
  );
});
```


The callback updates `TaskList`'s `scope.hideCompleted` - this exposes `hideCompleted` as an Alpine template variable (for this instance only). This is the same `hideCompleted` that's passed down to `TaskFilterToggle`'s `$c-props`.

The reactive props
then update both `TaskFilterToggle` instances. If the next click comes from
the other control, it now sends `false` and asks the server for all three
tasks again. Citry removes the scoped subscription when the list instance
leaves the page.

This page has one `TaskList` and therefore one `#task-rows` update target. In a real-life application, you might want to update only individual rows instead of re-rendering entire list.

## Dispatch vs Data actions

The filter controls send the events to the server using `@c-click`. `@c-click` only declares what server event handler to send the event to, but it can't handle the server response.

That's why the server responds with a [`Dispatch`](/v/0.4.2/reference/events/#citry-ext-events-actions-dispatch) action - this works around the `@c-click`'s limitation:

1. `@c-click` triggers a server event.
2. Server-side handler receives and processes the event.
3. The server returns a `Dispatch` action
   to trigger a browser event `'TaskList:filter-changed'`.
4. In the browser, separate [`onEvent()`](/v/0.4.2/reference/browser-apis/#on-event) callback is registered in `TaskList` to listen for this event.
5. Inside the `onEvent()`, we can access the data sent with this event.

There is a simpler way: When you want to trigger a server event AND get data back from the server, you can instead use [`sendEvent()`](/v/0.4.2/reference/browser-apis/#send-event) together with [`actions.Data`](/v/0.4.2/reference/events/#citry-ext-events-actions-data).

`sendEvent()` returns a Promise that resolves to the data returned by
[`actions.Data`](/v/0.4.2/reference/events/#citry-ext-events-actions-data):


```js
const result = await sendEvent(
  'filter_tasks',
  { hide_completed: !hideCompleted },
);
// result === { hideCompleted: true }
```


And the Python action would have look like:


```python
actions.Data(
    {"hideCompleted": data.hide_completed},
)
```


In the browser, the code would look like this:

Replace `onEvent` in `TaskList`'s JavaScript with `sendEvent`:


```js
$component(({ sendEvent, scope }) => {
  scope.hideCompleted = false;

  scope.onFilterTasks = () => {
    const result = await sendEvent(
      'filter_tasks',
      { hide_completed: !scope.hideCompleted },
    );
    scope.hideCompleted = result.hideCompleted;
  };
});
```


And in the template, replace `@c-click` with regular `@click` on `TaskFilterToggle`:


```citry-html
<c-TaskFilterToggle
  $c-props="{
    hideCompleted,
    loading: $loading('filter_tasks'),
  }"
  @click="onFilterTasks"
/>
```


Bottom-line: Use Dispatch when `@c-*` starts the call and browser listeners must react. A
handler may return both when it supports both call styles.

## Keep building

Congratulations, you've reached the end of the tutorial.

You're now ready to get building! :)

You've now have the core patterns for editable tables, kanban columns, search
results, and other repeated interactive components:

From here:

- Use [Examples](/v/0.4.2/examples/) when you want working code for a specific task.
- Read [Docs](/v/0.4.2/getting-started/installation/) when you want a concept or guided
  workflow.
- Read [Reference](/v/0.4.2/reference/) when you need the exact API for a class, method, or return action.
- Install [Citry UI](/v/0.4.2/ui-library/), a library of reusable UI components.
- Install [Citry linter](/v/0.4.2/ide/vscode/) for your IDE, to get syntax highlight, diagnostics, and more.