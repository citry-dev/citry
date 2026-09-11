# Grade a submitted consumer app

Run these tests only after the subject agent has stopped. Mount the submitted
files at `/workspace`, this entire directory at `/grader`, and an empty
writable result directory at `/results`. Keep `/workspace` and `/grader`
read-only. Set `PYTHONDONTWRITEBYTECODE=1` and
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. Start the grader in `/grader` and omit
`PYTHONPATH`.
The grading image supplies the pinned dependencies and Chromium. Disable
outbound networking and provide no API credentials.

For one case, run:

```sh
python -I -m pytest -q -p no:cacheprovider -c /dev/null \
  --rootdir=/grader --confcutdir=/grader \
  /grader/test_cards.py --junitxml=/results/junit.xml
```

Use `test_browser.py` or `test_events.py` for those cases. Each case runs in a
fresh container. `conftest.py` starts and stops Uvicorn for the browser cases
and permits browser requests only to that local server. For local development,
`SUBMISSION_DIR` can override `/workspace`.
Copy this directory outside the repository before local pytest runs so the
repository's own pytest configuration and fixtures do not affect grading.
The grader imports its dependencies before adding the submission to Python's
import path. Uvicorn also starts with isolated Python and receives the
submission directory through `--app-dir`.

The cases contain six card tests, three counter tests, and three event tests.
The card checks inspect the component's public schemas and parsed HTML. The
counter checks cover initial server HTML, Alpine availability, independent
updates, negative values, reset, reload, and separate pages. The event checks
cover selection, repeated updates, rendered HTTP event responses, pressed
button states, and separate pages. Browser exceptions fail the active test.

These checks measure observable behavior. They do not prove that every part
of a submission follows the requested implementation method. A source review
must assess component reuse, typed counter inputs, typed Python event handlers,
and use of Citry templates and slots. CSS quality is unscored. Report that
review separately from the executable pass rate.

The `reference` directory is for harness validation and must never be mounted
in a subject container. Its apps implement the same public tasks and run
through these same graders. The `events` case is reserved for evaluation
after pilot-driven documentation changes; do not use its prompt or reference
to tune those changes.
