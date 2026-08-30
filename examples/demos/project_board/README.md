# Citry Project Board demo

This demo shows how components, browser behavior, and Python handlers work
together in a larger Citry application. Search the board, add a task, move
cards between columns, mark work complete, and watch Citry update the page
without a full reload.

The demo uses fixed in-memory data. It does not need a database, an external
service, or a network connection after installation.

## What this demo shows

- FastAPI serves the page and mounts Citry under `/citry`.
- Typed inputs pass tasks between components. Slots compose the document,
  page heading, board columns, and cards.
- `ProjectBoard` provides one accent color. Each column and card injects that
  value so they use the same color.
- Each card uses `<c-component>` to choose its high- or standard-priority
  badge.
- Alpine opens the explanation and dismisses notices without calling Python.
- Dragging a card moves it to another column. Each card also has a labeled
  **Move to column** menu that works with a keyboard or touchscreen.
- Citry Events send searches, new tasks, card moves, and completion changes
  to typed Python handlers.
- Python validates the add-task form and leaves its entries in place when it
  finds an error.
- Successful changes replace the board and announce what changed.

## Requirements

- Python 3.10 through 3.14
- [uv](https://docs.astral.sh/uv/)

The project accepts Citry 0.4.6 or newer within the 0.4.x release line. Its
lockfile pins the version exercised by the tests.

## Run the project

On macOS or Linux:

```console
uv sync --dev
export CITRY_SECRET="$(
  uv run python -c 'import secrets; print(secrets.token_urlsafe(32))'
)"
uv run uvicorn app.main:web_app --host 127.0.0.1 --port 8000
```

In PowerShell:

```powershell
uv sync --dev
$env:CITRY_SECRET = uv run python -c `
  "import secrets; print(secrets.token_urlsafe(32))"
uv run uvicorn app.main:web_app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/>. You should see five active tasks across three
columns. Search for `keyboard` to leave one card. Clear the search, then drag a
card to another column or use its **Move to column** menu. Add a task, then
mark it complete to see those updates too.

The app reads `CITRY_SECRET` directly from the environment. `.env.example`
records the variable name, but the running demo does not load `.env` files.
The committed VS Code setup uses that example file only for Citry's isolated
editor discovery worker.

## Test the project

```console
uv run pytest
```

## Remove the environment and test cache

On macOS or Linux:

```console
rm -rf .venv .pytest_cache
```

In PowerShell:

```powershell
Remove-Item -Recurse -Force `
  -ErrorAction SilentlyContinue .venv, .pytest_cache
```

## Find the important code

| File | What it does |
|---|---|
| `app/main.py` | Starts FastAPI, initializes Citry, serves `/`, and mounts `/citry`. |
| `app/citry_app.py` | Creates the shared Citry instance and configures component autodiscovery. |
| `app/store.py` | Stores the sample tasks and adds, moves, or completes them after validation. |
| `app/components/app_shell.py` | Renders the document shell and shared page styles. |
| `app/components/board_page.py` | Composes the heading and project board. |
| `app/components/project_board.py` | Defines the form, filters, Events, and board-level state. |
| `app/components/lane.py` and `app/components/task_card.py` | Define the board columns and task cards. |
| `app/components/*_badge.py` and `app/components/badge_styles.py` | Define the priority badges and shared styles. |
| `tests/test_app.py` | Checks the page, task changes, and mounted Citry runtime. |

## Follow the data

| Step | What happens |
|---|---|
| FastAPI route to page | `home()` loads trusted `Task` records and passes them to `BoardPage`. |
| Parent to child | Typed inputs pass the records through the board, columns, and cards. |
| Component to template | `template_data()` exposes only the values each template renders. |
| Browser to Python | Signed `State` carries the search text and completed-task filter to an Event handler. |
| Card to board | A drag, a change in the **Move to column** menu, or the completion button tells the board which task changed. |
| Python to store | Typed handlers check each task ID and destination before changing the in-memory tasks. |
| Python to page | Each handler returns a new `ProjectBoard`, and Citry replaces the current board. |
| Python to browser | A dispatch action sends the success message shown in the notice. |

## Move cards by dragging or choosing a column

You can drag a card onto another column with a mouse or another pointing
device. The destination highlights while the card is over it. Every card also
has a **Move to column** menu that works with a keyboard or touchscreen.

Both interactions send the task ID and destination column to the board's
typed `move` Event. Python checks both values, changes the in-memory task, and
returns a new board. The browser sends the task ID, but Python looks up that
task and checks the destination before changing it.

## Keep data safe when adapting the demo

Python `Task` and `LaneView` objects stay on the server as component inputs.
Only the search text and completed-task filter travel through the browser as
`State`. Citry signs `State` against tampering, but the browser can read it.
Never put secrets in `State`.

All users connected to one process share the same in-memory task list, which
resets when the process restarts. Before adding private data or real write
operations:

- give every worker the same `CITRY_SECRET`;
- replace the in-memory list with a transactional database;
- reload each referenced task and check that the current user may change it;
- configure your host's CSRF token for authenticated writes;
- use a shared Citry cache when several workers render component updates; and
- add the process, proxy, logging, and health checks required by your
  deployment.

Read the [FastAPI guide](https://citry.dev/getting-started/fastapi/),
[Events guide](https://citry.dev/events/), and
[security guide](https://citry.dev/security/) before extending the demo.

## Where the demo came from

The demo adapts its page layout and component structure from
`packages/py/citry/tests/test_benchmark_citry.py`. That benchmark ports the
large django-components example from
[django-components PR #999](https://github.com/django-components/django-components/pull/999).
The demo owns its modules, data, interactions, and tests and does not affect
benchmark measurements.
