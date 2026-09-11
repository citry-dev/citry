# Test how agents build with Citry

This harness compares documentation entry points and a small consumer skill.
Each trial gives Codex an application task in a fresh Docker container. The
application directory is a host volume, so its files remain available after
the agent exits. The host records the prompt, timing, events, and grades.

The [September 2026 public record](results/2026-09-agent-docs/README.md)
contains 40 completed runs, their exact prompts, selected measurements and
grades, and instructions for repeating the procedure. It reports results
across three tasks and two models, with the limits of that comparison.

The agent image contains public packages and tools. Its build context is only
[`image/`](image/), with an explicit file allowlist. Citry's checkout,
contributor instructions, reference solutions, other trials, and graders are
absent from the agent container. Only the trial's `workspace/` is bind-mounted.
The selected skill is copied there for the two skill conditions.

## Build and verify

Requirements: Docker with a running Linux engine and host Python 3.10.0 or later.
The image contains Python 3.12.14, Node 22.23.2, Codex CLI 0.153.4, Citry 0.4.6,
FastAPI, pytest, and Playwright with Chromium. The complete Python dependency
closure is pinned in [`image/requirements.lock`](image/requirements.lock).
Prepared trials record the immutable image ID. Rebuilding can update Debian
packages, so use one image ID throughout a comparison.

From this directory:

```sh
python run.py build
python run.py verify
```

`verify` makes no model calls and uses disposable fake credentials. It tests
the actual container mounts, login-before-timing order, timeout cleanup,
positive reference solutions, and failing unfinished submissions. It also
checks that submission files cannot replace pytest or load their own pytest
configuration. Docker checks run on demand, keeping image builds and browser
startup out of ordinary repository checks.

## Authenticate before starting the stopwatch

The default login uses a device code. Open the displayed URL in your browser
and complete login before preparing or running trials:

```sh
python run.py login
```

If you prefer entering a container yourself:

```sh
python run.py login --method shell
codex -c 'cli_auth_credentials_store="file"' login --device-auth
exit
```

You can also copy one existing credential file. This mounts only that file in
a temporary helper container; it does not mount your Codex profile:

```sh
python run.py login --auth-file "$HOME/.codex/auth.json"
```

For API-key authentication, pipe the key through standard input:

```sh
printenv OPENAI_API_KEY | python run.py login --method api-key
```

Login state lives in the Docker volume `citry-agent-eval-auth`, outside the
application outputs. Each trial receives only `auth.json` in a fresh private
Codex volume. After the container stops, refreshed credentials are copied
back and the private volume is removed. Configurations, histories, memories,
and personal skills are not copied. Trials run sequentially to avoid competing
refresh-token writes and shared CPU contention.

Credentials are accessible to Codex and its processes inside that trial.
Treat raw transcripts and generated files as private: the harness keeps auth
out of its own logs, but cannot guarantee that agent-written output contains
no sensitive data. Grading containers receive no credentials.

Device login may need enabling in account settings. See the official
[headless authentication guidance](https://learn.chatgpt.com/docs/auth).
The harness does not authenticate or start a model call during build,
verification, or preparation.

## Run one trial

Choose an available model explicitly. Its identifier is passed unchanged to
Codex; the harness does not select a model based on your personal profile.

```sh
python run.py prepare --case cards --arm llms \
  --model YOUR_MODEL --effort high --timeout 900
```

The command prints the new run directory. Inspect its `prompt.md` and
`run.json`, then pass that directory to the following commands:

```sh
python run.py run runs/cards-llms-RUN_ID
python run.py grade runs/cards-llms-RUN_ID
```

Replace the example directory with the actual printed path. Preparation and
authentication finish before timing begins. The measured interval starts
immediately before launching `docker exec ... codex exec` and ends after
confirmed container removal. It includes Codex startup, model and tool work,
and the short Docker shutdown overhead. It excludes image setup, login,
Git initialization, transcript processing, and grading. On timeout, the
container and its background processes are terminated.

Every trial has two CPUs, 4 GB RAM, a 512-process limit, and a read-only image.
The workspace, temporary files, and private Codex volume are writable. The
agent has public network access and live web search. Public upstream cloning
and searching for evaluation solutions are prohibited in the common prompt;
that is an instruction, not a network filter. No host ports or Docker socket
are exposed. Standard Docker networking can still reach accessible network
services, so this is filesystem isolation rather than an internet allowlist.

The baseline includes Codex's bundled capabilities. It excludes locally
installed personal or repository capabilities. Agent delegation is disabled
in every trial to keep execution conditions consistent.

## Prepare the pilot or a larger comparison

The default plan has two tasks, two conditions, and two repetitions, shuffled
with a recorded seed. Preparing it makes eight application directories and
a plan file without starting any agents:

```sh
python run.py plan --model YOUR_MODEL --seed 17
```

Execute the printed plan path to run and grade its trials sequentially:

```sh
python run.py execute runs/plan-PLAN_ID.json
```

The default per-trial limit is 900 seconds. Eight trials can therefore use
up to about two hours of agent time, plus setup and grading. `execute` starts
real model calls using the authenticated account. A timeout remains in the
results; an authentication or harness error stops the batch for inspection.
Trials cannot be resumed or silently overwritten. Prepare a fresh trial for
a retry and retain the failed record.

To compare all entry points and instruction forms explicitly:

```sh
python run.py plan --model YOUR_MODEL --cases cards browser \
  --arms homepage llms full guidance skill inline skill-auto \
  --repetitions 2 --seed 17
```

This larger plan has 28 trials. It is optional; use the pilot to decide which
comparisons are worth running. Keep `events` for a later task if you revise
the skill after seeing pilot results.

| Condition | What differs from the shared task prompt |
|---|---|
| `homepage` | A pointer to `https://citry.dev/` |
| `llms` | A pointer to `https://citry.dev/llms.txt` |
| `full` | A pointer to `https://citry.dev/llms-full.txt` |
| `guidance` | The index plus a short instruction to fetch relevant pages, check the version, and verify the result |
| `skill` | The index plus an explicitly invoked `citry-consumer` skill |
| `inline` | The index plus the exact skill body pasted into the prompt |
| `skill-auto` | The index with the skill installed for automatic discovery |

All conditions may discover other public documentation. The comparison
measures the starting instruction, not exclusive access to a particular URL.
The skill is an experimental candidate, not an established best practice.
Its body is the single source for the `inline` condition.

## Tasks and grading

| Case | Required behavior | Automated checks |
|---|---|---|
| `cards` | Typed product cards with slots, safe text, prices, and fallback content | 6 |
| `browser` | Two independent Alpine counters served by FastAPI | 3 |
| `events` | Plan selection through Python Citry Events and rendered updates | 3 |

The task files state entrypoints and selectors so agents know the observable
contract. Grading uses fresh containers with no outbound network, a read-only
submission, and graders mounted only after the agent container is gone.
The host requires the expected number of successful tests in JUnit output.
Unfinished starters are negative controls; references establish that the
tasks are solvable with the installed public package.

Automated behavioral success does not prove every requested implementation
choice. Review source for the checks described in
[`grading/README.md`](grading/README.md), particularly reusable components
and typed Python Events. Grading is designed for ordinary coding agents,
not hostile code attempting to tamper with its evaluator from inside a
submitted application. The agent receives no hidden-test feedback during a
timed trial.

## Read results

```sh
python run.py report > runs/report.json
```

Each trial keeps:

- `workspace/`: the agent's application, tests, and initial Git commit;
- `prompt.md` and `run.json`: exact instructions, input hashes, model, effort,
  image ID, status, wall time, and token usage when emitted by Codex;
- `container.json` and `versions.json`: actual mounts and installed tools;
- `events.jsonl`, `stderr.log`, and `final.md`: raw events, diagnostics, and
  the final agent message;
- `grade/`: test output, JUnit details, and the recorded behavioral result.

An exit code of zero means Codex finished, not that the application passed.
Missing usage is unknown, not zero cost. Compare failures and timeouts alongside
successful runs; do not calculate efficiency only for successes. The harness
records total agent time, not time to the first working implementation. Review
the transcript to classify retrieval failures, truncation, invented APIs,
skill activation, and verification attempts. It does not infer those judgments
from keyword counts or convert tokens into a monetary estimate.

This first setup tests **live public documentation** with a fixed package.
The task prompts state Citry 0.4.6, but root documentation can evolve. Use the
trial's UTC start and finish times and the retrieved URLs visible in its
transcript when investigating a mismatch.
Do not describe these runs as a frozen-documentation experiment. A controlled
documentation snapshot would require a separate serving and retrieval setup.

Compare matched tasks under the same model, effort, image, and time limit.
The pilot diagnoses failures; it does not establish statistical significance.
If guidance fixes repeated failures, validate it on a task not used to tune it
before deciding to maintain a dedicated skill.

## Recover from an interrupted harness

An ordinary timeout or Ctrl-C stops the trial container and saves its status.
If the host process or Docker daemon dies abruptly, inspect the recorded ID
and remove that trial's `citry-eval-ID` container before grading or retrying.
Its private credential volume is `citry-eval-ID-home`. The host lock is
`runs/.active/owner` and contains the owning trial ID. Clear that lock only
after confirming its container has stopped. Log in again if refreshed
credentials could not be saved. Preserve the incomplete result and prepare
a new trial; it is not a valid completed sample.

The default `runs/` directory is Git-ignored. If using `--out` elsewhere,
choose a private directory outside version control. Credentials can be
removed after all trials stop with:

```sh
docker volume rm citry-agent-eval-auth
```
