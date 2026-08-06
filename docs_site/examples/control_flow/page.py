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
