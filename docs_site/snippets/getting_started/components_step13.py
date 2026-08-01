from dataclasses import dataclass

from citry import Component
from citry.ext.events import EventError, actions

from citry_setup import citry_app


@dataclass
class Task:
    id: int
    title: str


# This represents the "database" of tasks.
# In a real app, this would be stored in a database.
TASKS = [
    Task(id=1, title="Review the draft"),
    Task(id=2, title="Send the invitation"),
    Task(id=3, title="Publish the notes"),
]


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


class CompactModeIn:
    compact: bool


class CompactToggle(Component):
    citry = citry_app

    template = """
      <button
        type="button"
        :disabled="clientProps.loading"
        x-text="
          clientProps.compact
            ? 'Use roomy rows'
            : 'Use compact rows'
        "
      ></button>
    """

    js = """
      $component({
        props: {
          compact: { type: Boolean, required: true },
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
        def set_compact(self, data: CompactModeIn):
            return actions.Dispatch(
                "TaskList:compact-changed",
                {"compact": data.compact},
            )

    def template_data(self, kwargs, slots):
        return {"tasks": kwargs.tasks}

    template = """
      <section :class="{ 'task-list--compact': compact }">
        <c-CompactToggle
          $c-props="{
            compact,
            loading: $loading('set_compact'),
          }"
          @c-click="set_compact({ compact: !compact })"
        />

        <ul>
          <c-for each="task in tasks">
            <c-TaskRow
              #c-key="task.id"
              c-task_id="task.id"
              c-title="task.title"
            />
          </c-for>
        </ul>

        <c-CompactToggle
          $c-props="{
            compact,
            loading: $loading('set_compact'),
          }"
          @c-click="set_compact({ compact: !compact })"
        />
      </section>
    """

    js = """
      $component(({ onEvent, scope }) => {
        scope.compact = false;
        onEvent(
          'TaskList:compact-changed',
          (detail) => {
            scope.compact = detail.compact;
          },
        );
      });
    """

    css = """
      .task-row {
        padding-block: 0.75rem;
      }

      .task-list--compact .task-row {
        padding-block: 0.25rem;
      }
    """


class TutorialPage(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs, slots):
        return {"tasks": TASKS}

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
