---
title: Build CRUD pages
description: Give each row of a list its own event handlers, errors, and status, and re-render the whole list from Python.
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

<c-include-file path="docs_site/snippets/getting_started/components_step13.py" language="citry" />

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
in [Keep values between calls](/getting-started/state/). The handler reads it
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
[`onEvent`][onEvent] in [`onServerRender`][onServerRender], as the form did
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
[`$sendEvent`][$sendEvent] calls the list's Python `filter_tasks` handler
with the opposite filter.

## Re-render the list

The handler loads the matching tasks and returns a new `TaskList`:

```python
# TaskList.Events.filter_tasks
def filter_tasks(self, data: FilterTasksIn):
    visible_tasks = load_tasks(
        hide_completed=data.hide_completed,
    )
    return actions.Render(
        TaskList(
            tasks=visible_tasks,
            hide_completed=data.hide_completed,
        )
    )
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

You have finished the tutorial. The [Server events](/events/) guide covers
each part in more depth, and the [Examples](/examples/) show complete
recipes you can copy.
