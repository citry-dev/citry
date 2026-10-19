---
title: Build CRUD pages
url: https://citry.dev/v/0.6.0/getting-started/build-crud-pages/
description: "Give each row of a list its own event handlers, errors, and status, and re-render the whole list from Python."
---
# Build CRUD pages

Admin pages often show a list of records where you can edit each row and
filter the whole list. CRUD stands for create, read, update, and delete;
this step covers editing and filtering. You build a task list that combines
the earlier steps:

- Each task row is its own component, with its own form, errors, and
  "Saved" message.
- Two filter buttons, above and below the list, ask Python for a filtered
  list and both show the current filter.

Replace `components.py` with this version. The task list takes the signup
form's place on the page; keep `citry_setup.py` and `app.py` as they are:

```citry
from dataclasses import dataclass

from citry_setup import citry_app

from citry import Component
from citry.ext.events import EventError, actions


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
        # Send the row a browser event so it can show a message.
        def save(self, data: RenameTaskIn, state: "TaskRow.State"):
            title = data.title.strip()
            if len(title) < 3:
                raise EventError(
                    "Give the task a longer title.",
                    fields={
                        "title": "Use at least three characters.",
                    },
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
        return {"task_id": kwargs.task_id, "title": kwargs.title}

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
            v-show="$error('save')"
            v-text="$error('save')?.fieldErrors?.title || ''"
          ></p>
          <output v-text="saveStatus"></output>
        </form>
      </li>
    """

    js = """
      // Display a message when this row's task title
      // is successfully saved.
      $component({
        data() {
          return { saveStatus: '' };
        },
        methods: {
          showSaved(detail) {
            this.saveStatus =
              `Saved task ${detail.taskId}: ${detail.title}`;
          },
        },
        onServerRender({ component, onEvent }) {
          // Citry removes this listener before onServerRender
          // runs again and when the component unmounts.
          onEvent('TaskRow:saved', (detail) => {
            component.showSaved(detail);
          });
        },
      });
    """


class TaskRows(Component):
    citry = citry_app

    class Kwargs:
        tasks: list[Task]

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
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


class TaskFilterToggle(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <button
        type="button"
        :disabled="loading"
        v-text="
          hideCompleted ? 'Show all tasks' : 'Hide completed tasks'
        "
        @click="$emit('select')"
      ></button>
    """

    js = """
      $component({
        props: {
          hideCompleted: { type: Boolean, required: true },
          loading: { type: Boolean, required: true },
        },
        emits: ['select'],
      });
    """


class FilterTasksIn:
    hide_completed: bool


class TaskList(Component):
    citry = citry_app

    class Kwargs:
        tasks: list[Task]
        hide_completed: bool = False

    class Slots:
        pass

    class Events:
        def filter_tasks(self, data: FilterTasksIn):
            visible_tasks = load_tasks(
                hide_completed=data.hide_completed,
            )
            task_list = TaskList(
                tasks=visible_tasks,
                hide_completed=data.hide_completed,
            )
            return actions.Render(task_list)

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"tasks": kwargs.tasks}

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"hideCompleted": kwargs.hide_completed}

    template = """
      <section class="task-list">
        <c-TaskFilterToggle
          :hideCompleted="hideCompleted"
          :loading="$loading('filter_tasks')"
          @select="$sendEvent('filter_tasks', {
            hide_completed: !hideCompleted,
          })"
        />

        <ul class="task-rows">
          <c-TaskRows c-tasks="tasks" />
        </ul>

        <c-TaskFilterToggle
          :hideCompleted="hideCompleted"
          :loading="$loading('filter_tasks')"
          @select="$sendEvent('filter_tasks', {
            hide_completed: !hideCompleted,
          })"
        />
      </section>
    """


class TutorialPage(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
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

Try a two-character title in one row, then save another row. The first row
keeps its error. Click either “Hide completed tasks” button: the server
returns two rows, and both buttons change to “Show all tasks.”

## One component per row


```citry-html
<c-for each="task in tasks">
  <c-TaskRow
    #c-key="task.id"
    c-task_id="task.id"
    c-title="task.title"
  />
</c-for>
```


`TaskRows` renders one `TaskRow` per task. Each `TaskRow` has its own State,
loading status, and errors, so one row's error does not affect another.

`#c-key` gives each row a key. When the list renders again, Vue uses the key
to tell which row is which. Use a database id or another value that stays
the same for the same record.

## Remember the record

The row keeps its task id in State, and the new title comes from the form:


```python
class State:
    task_id: int

class Events:
    def save(self, data: RenameTaskIn, state: "TaskRow.State"):
        ...
```


Citry fills `state.task_id` from the `task_id` input on the first render, as
in [Keep values between calls](/v/0.6.0/getting-started/state/). The handler reads it
to know which task to update.

!!! note "Sending the id from a hidden input"

    The row could instead send its id in a hidden `name="task_id"` input,
    with a matching field on `RenameTaskIn`. A user can edit a hidden
    input's value before submitting. State is signed, so Citry detects a
    changed `task_id`. Either way, keep sensitive values on the server and
    check in the handler that the user may edit that task.

## Show row messages


```citry-html
<p
  role="alert"
  v-show="$error('save')"
  v-text="$error('save')?.fieldErrors?.title || ''"
></p>
<output v-text="saveStatus"></output>
```


`$error('save')` reads only this row's error. After a successful save, Python
dispatches `TaskRow:saved` from that row. The row listens for it with
[`onEvent`](/v/0.6.0/reference/browser-apis/#on-server-render-on-event) in [`onServerRender`](/v/0.6.0/reference/browser-apis/#on-server-render), as the form did
in the earlier step:


```js
$component({
  data() {
    return { saveStatus: '' };
  },
  methods: {
    showSaved(detail) {
      this.saveStatus =
        `Saved task ${detail.taskId}: ${detail.title}`;
    },
  },
  onServerRender({ component, onEvent }) {
    // Citry removes this listener before onServerRender
    // runs again and when the component unmounts.
    onEvent('TaskRow:saved', (detail) => {
      component.showSaved(detail);
    });
  },
});
```


`onEvent` hears only events from this row's own Python handlers, so the
other rows do not show the message.

## Connect the filters

`TaskFilterToggle` is a button that receives two props and sends a `select`
event, as in [Connect components in the
browser](/getting-started/client-props-and-handlers/):


```js
$component({
  props: {
    hideCompleted: { type: Boolean, required: true },
    loading: { type: Boolean, required: true },
  },
  emits: ['select'],
});
```


`TaskList` uses it twice, with the same props and handler:


```citry-html
<c-TaskFilterToggle
  :hideCompleted="hideCompleted"
  :loading="$loading('filter_tasks')"
  @select="$sendEvent('filter_tasks', {
    hide_completed: !hideCompleted,
  })"
/>
```


`TaskList.js_data()` provides `hideCompleted`, and Vue passes the same value
to both buttons. When either button sends `select`,
[`$sendEvent`](/v/0.6.0/reference/browser-apis/#send-event) calls the list's Python `filter_tasks` handler
with the opposite filter.

## Re-render the list

The handler loads the matching tasks and returns a new `TaskList`:


```python
# TaskList.Events.filter_tasks
def filter_tasks(self, data: FilterTasksIn):
    visible_tasks = load_tasks(
        hide_completed=data.hide_completed,
    )
    task_list = TaskList(
        tasks=visible_tasks,
        hide_completed=data.hide_completed,
    )
    return actions.Render(task_list)
```


The new `TaskList` replaces the old one, because its handler ran. Passing
`hide_completed` lets the new list's `js_data()` start with the chosen
filter, so both buttons show it. The row keys let Vue keep the rows that are
still there, and remove or add the others.

## Split larger pages

On a larger page, split it into smaller components that each have their own
`Events`. A handler's `actions.Render` then replaces only its own component,
not the whole page.

## Next steps

You have finished the tutorial. The [Server events](/v/0.6.0/events/) guide covers
each part in more depth, and the [Examples](/v/0.6.0/examples/) show complete
recipes you can copy.