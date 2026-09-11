Implement the task below in /workspace using the installed Citry package.
This directory is an application project. Python, Node, Git, curl, ripgrep,
pytest, and Playwright with Chromium are available.

Keep the installed dependency versions. Put the application and any tests you
write in /workspace. You may use public documentation and inspect installed
package source. Do not clone the upstream repository or search for evaluation
solutions. Use the available terminal and browser libraries to check your work.
Complete the task autonomously within the time limit. In your final response,
state what works, what you tested, and any remaining problems.

Time limit: 900 seconds.

Use https://citry.dev/.

# Build two independent counters

Implement `app.py` with a FastAPI ASGI application exported as `app`, using
the installed `citry==0.4.6` public API and its Alpine integration. The evaluator
starts `python -m uvicorn app:app --host 127.0.0.1 --port PORT` in the workspace.

Serve a complete HTML page at `GET /`. Render two instances of one reusable
Citry counter component, with typed inputs for its identifier and initial
value. The first has `id="counter-a"` and starts at `2`; the second has
`id="counter-b"` and starts at `10`. Within each counter, provide:

- `[data-role="value"]`, whose visible text is the current integer;
- `button[data-action="increment"]`, which adds one;
- `button[data-action="decrement"]`, which subtracts one, including below zero;
- `button[data-action="reset"]`, which restores that counter's initial value.

Keep state independent for every counter and browser page. Use Alpine state
owned by each Citry component instance. Changes happen in the browser without
an HTTP request or page navigation. Reloading the page restores `2` and `10`.
All controls must be visible, labelled, and clickable. The server-rendered
HTML must already contain both initial values.

Serve the browser runtime and component assets from this application using
the installed package. Grading has no outbound internet access, so the page
must work without a CDN. Avoid browser errors during load and interaction.
Simple CSS is enough; visual polish has no numeric score.

You may add workspace files. Keep dependencies at their preinstalled versions.
Finish by briefly describing what you implemented and which checks you ran.
