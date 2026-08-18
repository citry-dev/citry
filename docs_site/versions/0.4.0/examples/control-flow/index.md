---
title: Control flow
url: https://citry.dev/v/0.4.0/examples/control-flow/
description: "Render conditions, loops, and empty states in a Citry template."
---
# Control flow

Loops, conditionals, and an empty state with `<c-for>`, `<c-if>`, and
`<c-empty>`.



### Component

````citry
"""A task list that shows off c-for, c-if, and c-empty control flow."""

from typing import Any, TypedDict

from citry import Component


class Task(TypedDict):
    text: str
    done: bool


class TaskList(Component):
    """Renders a list of {text, done} tasks.

    Done tasks are struck through with a check mark; pending tasks get a
    hollow bullet. When there are no tasks, the c-empty branch is shown.
    """

    class Kwargs:
        tasks: list[Task]
        title: str = "Tasks"

    class Slots:
        pass

    template = """
      <section class="tasklist">
        <h3 class="tasklist__title">{{ title }}</h3>
        <ul class="tasklist__items">
          <c-for each="task in tasks">
            <li class="tasklist__item">
              <span c-if="task['done']" class="tasklist__mark tasklist__mark--done">&#10003;</span>
              <span c-else class="tasklist__mark tasklist__mark--todo">&#9675;</span>
              <span c-if="task['done']" class="tasklist__text tasklist__text--done">{{ task['text'] }}</span>
              <span c-else class="tasklist__text">{{ task['text'] }}</span>
            </li>
          </c-for>
          <c-empty>
            <li class="tasklist__item tasklist__item--empty">Nothing to do yet.</li>
          </c-empty>
        </ul>
      </section>
    """

    css = """
      .tasklist {
        max-width: 24rem;
        margin: 0 0 1.25rem;
        padding: 1rem 1.25rem;
        border: 1px solid #d0d7de;
        border-radius: 8px;
        font-family: system-ui, sans-serif;
      }
      .tasklist__title {
        margin: 0 0 0.5rem;
        font-size: 1.05rem;
      }
      .tasklist__items {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .tasklist__item {
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
        padding: 0.25rem 0;
      }
      .tasklist__mark--done {
        color: #1a7f37;
      }
      .tasklist__mark--todo {
        color: #8c959f;
      }
      .tasklist__text--done {
        color: #8c959f;
        text-decoration: line-through;
      }
      .tasklist__item--empty {
        color: #8c959f;
        font-style: italic;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        return {"tasks": kwargs.tasks, "title": kwargs.title}
````

### Page

````citry
"""Standalone page that renders the TaskList control-flow example."""

from citry import Component


class ControlFlowPage(Component):
    """A full page showing a populated TaskList and an empty one."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Control flow example</title>
          <c-css />
        </head>
        <body
          style="margin: 0; padding: 1.5rem; font-family: system-ui, sans-serif;"
        >
          <c-TaskList
            title="Today"
            c-tasks="[
              {'text': 'Write the docs example', 'done': True},
              {'text': 'Review the pull request', 'done': False},
              {'text': 'Ship the release', 'done': False},
            ]"
          />
          <c-TaskList
            title="Someday"
            c-tasks="[]"
          />
          <c-js />
        </body>
      </html>
    """
````

[Open the live result](/v/0.4.0/examples/control-flow/demo/)

