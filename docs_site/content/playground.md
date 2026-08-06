---
title: Try Citry
description: Edit and run a Citry component directly in your browser.
layout: playground
---

The starter already renders a welcome card. Change the `name` or `accent`
value in its final `WelcomeCard(...)` line, then see the updated page in
**Result**.

### Choose what appears in Result

The playground renders the value from the last Python expression. In the
starter, that expression creates `WelcomeCard(...)`. End your module with the
component or HTML string you want to preview.

Text written with `print()` appears in the Code diagnostics, not in Result.

### Call Python from Result

The starter's **Say hello from Python** button calls the `welcome` method in
`class Events`. That handler updates the component's `State` and dispatches the
new count back to the card. Try clicking it, then edit the handler or its
template binding and run the module again.

The displayed module stays active after it renders, so synchronous handlers
can return Data, update State, and Dispatch browser events. Starting another
run replaces that event environment. The playground does not imitate a web
server: event-driven component renders, redirects, history changes, downloads,
uploads, authentication, and sessions are unavailable here.

### Choose when your code runs

**Auto-run** is on by default: after you pause typing, the playground runs the
latest code and updates Result. Turn it off when you want to make several edits
before updating the page.

Use **Run** or press <kbd>Ctrl</kbd>+<kbd>Enter</kbd>
(<kbd>Cmd</kbd>+<kbd>Enter</kbd> on macOS) to run immediately. Use **Stop** to
cancel a run that is still in progress. After stopping, use **Run** to start a
fresh run.

### Adjust the workspace

Drag the divider to give Code or Result more room. Double-click it to restore
an even split. On narrow screens, use the **Code** and **Result** tabs to switch
panels.

### Keep your code or start over

- **Copy** puts the complete Python module on your clipboard.
- **Download** saves it as `citry_playground.py`.
- **Reset** discards your edits and restores the original starter. When
  Auto-run is enabled, the starter runs again.

### Fix a failed run

Python errors appear in Code. JavaScript errors from the rendered page appear
in Result. A failed run leaves the last successful page visible. If you see
**Showing last successful result**, Result does not match the current code and
its Python event handlers are inactive. Fix the code and run it successfully
to enable them again.

The first run can take a little longer because the browser downloads Python and
Citry. Later runs are usually faster while that runtime remains active.
