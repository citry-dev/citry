---
title: Build CRUD pages
description: Keep repeated event-driven rows independent and rerender their owning list.
---

# Build CRUD pages

A CRUD page often has one event-driven component per record and shared
controls around the collection. This example gives each task row independent
loading, validation, and success state, while `TaskList` owns two synchronized
filter controls.

<c-include-file path="docs_site/snippets/getting_started/components_step13.py" language="citry" />

Try a two-character title in one row, then save another row. The first row's
error remains. Select either “Hide completed tasks” control: the server returns
two rows and both controls change to “Show all tasks.”

## Keep rows independent

```citry-html
<c-for each="task in tasks">
  <c-TaskRow
    #c-key="task.id"
    c-task_id="task.id"
    c-title="task.title"
  />
</c-for>
```

Each `TaskRow` is a separate instance with its own State, activity state, loading counters, and handler errors. `#c-key` gives Vue a stable application
identity for each row as the collection changes. Use a database key or another
stable domain identifier.

The task ID lives in signed State while the edited title comes from the named
form control:

```python
class State:
    task_id: int

class Events:
    def save(self, data: RenameTaskIn, state: "TaskRow.State"):
        ...
```

An alternative is a hidden `name="task_id"` control and a matching field on
`RenameTaskIn`. Keep sensitive or authoritative values on the server and check
permissions in the handler.

## Show row-local status

```citry-html
<p
  role="alert"
  v-show="$error('save')"
  v-text="$error('save')?.fieldErrors?.title || ''"
></p>
<output v-text="saveStatus"></output>
```

After a successful save, Python dispatches `task-row:saved` from that row. The
same row installs an instance listener in `onServerRender`:

```js
$component({
  data() {
    return { saveStatus: '' };
  },
  methods: {
    showSaved(detail) {
      this.saveStatus = `Saved task ${detail.taskId}: ${detail.title}`;
    },
  },
  onServerRender({ component }) {
    const receiveSaved = (event) => component.showSaved(event.detail);
    component.$el.addEventListener('task-row:saved', receiveSaved);
    return () => component.$el.removeEventListener('task-row:saved', receiveSaved);
  },
});
```

Because the event starts at the calling row, sibling rows do not receive it.

## Give the filter child props and an event

`TaskFilterToggle` declares its inputs and output:

```js
$component({
  props: {
    hideCompleted: { type: Boolean, required: true },
    loading: { type: Boolean, required: true },
  },
  emits: ['select'],
});
```

The button emits `select`. `TaskList` binds both copies to the same parent data
and handler:

```citry-html
<c-TaskFilterToggle
  :hideCompleted="hideCompleted"
  :loading="$loading('filter_tasks')"
  @select="$sendEvent('filter_tasks', { hide_completed: !hideCompleted })"
/>
```

`hideCompleted` is seeded by `TaskList.js_data()`. Vue updates both child props
from the same parent value. `$sendEvent` calls the parent component's Python
`filter_tasks` handler when either child emits `select`.

## Rerender the calling list

The handler loads the requested rows and returns a new `TaskList`:

```python
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

With no selector target, the Render action updates the calling `TaskList`.
Passing `hide_completed` seeds the replacement's browser state, so both filter
controls show the new mode. Stable row keys let the renderer match surviving
rows while removing or adding the others.

For larger pages, split ownership into smaller event components so a default
Render updates only the region that owns the handler.
