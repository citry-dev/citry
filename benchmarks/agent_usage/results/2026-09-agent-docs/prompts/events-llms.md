Implement the task below in /workspace using the installed Citry package.
This directory is an application project. Python, Node, Git, curl, ripgrep,
pytest, and Python Playwright with Chromium are available. Use Playwright
through its Python API (`playwright.sync_api` or `playwright.async_api`).

Keep the installed dependency versions. Put the application and any tests you
write in /workspace. You may use public documentation and inspect installed
package source. Do not clone the upstream repository or search for evaluation
solutions. Use the available terminal and browser libraries to check your work.
Complete the task autonomously within the time limit. In your final response,
state what works, what you tested, and any remaining problems.

Time limit: 900 seconds.

Use https://citry.dev/llms.txt.

# Choose a subscription plan through server events

Implement `app.py` with a FastAPI ASGI application exported as `app`, using
the installed `citry==0.4.6` public API and Citry Events. The evaluator starts
`python -m uvicorn app:app --host 127.0.0.1 --port PORT` in the workspace.

At `GET /`, show a plan chooser built from a Citry component. The starter
contains the server's plan catalog. Initially select `starter`. Provide these
visible controls and outputs:

- `button[data-plan="starter"]`, `button[data-plan="team"]`, and
  `button[data-plan="scale"]` select the corresponding plan;
- `#selected-plan` shows `Starter`, `Team`, or `Scale`;
- `#selected-price` shows `$12 / month`, `$29 / month`, or `$79 / month`;
- exactly one plan button has `aria-pressed="true"`; the others have
  `aria-pressed="false"`.

Selecting a plan must call a typed Python Citry Event handler over the mounted
Citry HTTP routes. Python looks up the plan in `PLANS` and returns a rendered
component that updates the chooser without navigating. The successful event
response must include the selected plan's rendered HTML. Repeated selections
and choosing a previous plan must work. Each page starts at `starter`; one
browser page's choices must not change another page's current or initial
selection. Keep the catalog on the server and accept a plan identifier as the
event input. The task only requires the three valid identifiers.

Use a local development secret for Citry. Mount its HTTP routes at `/citry`.
Serve its bundled browser assets from this app: grading has no outbound
internet access. Avoid browser errors. Keep dependencies at their preinstalled
versions. Simple CSS is enough; visual polish has no numeric score.

You may add workspace files. Finish by briefly describing what you implemented
and which checks you ran.
