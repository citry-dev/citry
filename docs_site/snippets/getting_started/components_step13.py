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
