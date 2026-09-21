from dataclasses import dataclass

from citry_setup import citry_app

from citry import Component
from citry.ext.events import EventError, actions


@dataclass
class Task:
    id: int
    title: str
    completed: bool = False


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

    class State:
        task_id: int

    class Events:
        def save(self, data: RenameTaskIn, state: "TaskRow.State"):
            title = data.title.strip()
            if len(title) < 3:
                raise EventError(
                    "Give the task a longer title.",
                    fields={"title": "Use at least three characters."},
                )
            for task in TASKS:
                if task.id == state.task_id:
                    task.title = title
                    break
            return actions.Dispatch(
                "task-row:saved",
                {"taskId": state.task_id, "title": title},
            )

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"task_id": kwargs.task_id, "title": kwargs.title}

    template = """
      <li class="task-row">
        <form @c-submit.prevent="save">
          <label>
            Task {{ task_id }}
            <input name="title" c-value="title" required />
          </label>
          <button type="submit" :disabled="$loading('save')">Save</button>
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
        v-text="hideCompleted ? 'Show all tasks' : 'Hide completed tasks'"
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
            visible_tasks = load_tasks(hide_completed=data.hide_completed)
            return actions.Render(
                TaskList(
                    tasks=visible_tasks,
                    hide_completed=data.hide_completed,
                )
            )

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"tasks": kwargs.tasks}

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"hideCompleted": kwargs.hide_completed}

    template = """
      <section class="task-list">
        <c-TaskFilterToggle
          :hideCompleted="hideCompleted"
          :loading="$loading('filter_tasks')"
          @select="$sendEvent('filter_tasks', { hide_completed: !hideCompleted })"
        />

        <ul class="task-rows">
          <c-TaskRows c-tasks="tasks" />
        </ul>

        <c-TaskFilterToggle
          :hideCompleted="hideCompleted"
          :loading="$loading('filter_tasks')"
          @select="$sendEvent('filter_tasks', { hide_completed: !hideCompleted })"
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
