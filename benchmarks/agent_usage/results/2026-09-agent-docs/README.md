# Citry documentation and agent instructions: September 2026

All 40 recorded runs passed their automated checks across three small Citry
tasks and two Codex models. The candidate consumer skill showed no observed
correctness advantage. Its timing differences varied by model and batch, so
these results support using the documentation index as a practical starting
point without establishing a reliable speed effect.

The runs took place on September 8, 2026, from 17:01:52 to 22:41:10 UTC.
They contain 132 passing test executions, including repeated checks of the
same tasks. Total measured agent time was 9,318.156 seconds, or 155.3 minutes.
Every run completed before its 900-second limit, recorded no runner errors,
and confirmed that its container stopped. Grades recorded no failures,
errors, or skipped tests.

## What was compared

The allocation was uneven. Only Terra attempted cards and browser counters;
both models attempted Events. The later Events batches repeated two of the
three earlier instruction conditions.

| Batch | Model | Task | Instructions | Attempts per condition |
|---|---|---|---|---:|
| `pilot-terra` | `gpt-5.6-terra` | Cards and browser counters | Homepage, index | 2 per task |
| `events-terra` | `gpt-5.6-terra` | Events | Index, guidance, skill | 2 |
| `events-luna` | `gpt-5.6-luna` | Events | Index, guidance, skill | 2 |
| `repeat-terra` | `gpt-5.6-terra` | Events | Index, skill | 5 |
| `repeat-luna` | `gpt-5.6-luna` | Events | Index, skill | 5 |

Every condition received the common environment instructions and a detailed
task with required entrypoints, behavior, and selectors. The condition changed
the documentation instruction:

- **Homepage** (`homepage`): `Use https://citry.dev/.`
- **Index** (`llms`): `Use https://citry.dev/llms.txt.`
- **Guidance** (`guidance`): the index plus instructions to fetch relevant
  Markdown guides and API references, check version compatibility, and run
  the implementation.
- **Skill** (`skill`): the index plus an explicit `$citry-consumer` request.
  The [candidate skill](citry-consumer/SKILL.md) was installed in the trial
  workspace under `.agents/skills/citry-consumer/SKILL.md`.

The skill tells agents how to find documentation and verify their work.
Its contents stayed unchanged across these runs. The harness also supports
bulk documentation, inline skill text, and automatic skill discovery; those
conditions were not run in this experiment.

## Recorded results

All times below are seconds. Each row reports all attempts in that batch,
task, and condition. Compare matched rows within a batch; different tasks
and execution periods introduce other sources of variation.

| Batch | Task | Instructions | Passed | Mean | Median | Minimum | Maximum |
|---|---|---|---:|---:|---:|---:|---:|
| Pilot Terra | Cards | Homepage | 2/2 | 141.362 | 141.362 | 127.684 | 155.040 |
| Pilot Terra | Cards | Index | 2/2 | 120.669 | 120.669 | 114.228 | 127.109 |
| Pilot Terra | Counters | Homepage | 2/2 | 189.091 | 189.091 | 180.758 | 197.424 |
| Pilot Terra | Counters | Index | 2/2 | 181.581 | 181.581 | 155.778 | 207.383 |
| Events Terra | Events | Index | 2/2 | 216.704 | 216.704 | 177.612 | 255.796 |
| Events Terra | Events | Guidance | 2/2 | 305.278 | 305.278 | 226.992 | 383.563 |
| Events Terra | Events | Skill | 2/2 | 317.954 | 317.954 | 287.252 | 348.656 |
| Events Luna | Events | Index | 2/2 | 295.141 | 295.141 | 268.214 | 322.068 |
| Events Luna | Events | Guidance | 2/2 | 349.349 | 349.349 | 287.453 | 411.245 |
| Events Luna | Events | Skill | 2/2 | 241.622 | 241.622 | 218.417 | 264.826 |
| Repeat Terra | Events | Index | 5/5 | 203.948 | 181.786 | 156.597 | 278.654 |
| Repeat Terra | Events | Skill | 5/5 | 209.902 | 200.296 | 173.390 | 250.367 |
| Repeat Luna | Events | Index | 5/5 | 258.099 | 245.964 | 209.313 | 322.922 |
| Repeat Luna | Events | Skill | 5/5 | 248.182 | 215.218 | 183.587 | 360.555 |

In the five-attempt repeats, the skill mean was 2.9% higher than the index
mean for Terra and 3.8% lower for Luna. In the earlier two-attempt batches,
those differences were larger. These are descriptions of observed durations,
not estimates of a dependable benefit or penalty from the skill.

## Charts for the devlog

The [initial Events chart](charts/events-timings.png) and
[repeat Events chart](charts/repeat-timings.png) show every attempt as a circle
and each condition's mean as a diamond. Models and batches stay separate;
both figures use the same time scale. SVG copies are in [charts/](charts/).

Regenerate these recording assets from this directory's `records.json`:

```sh
uv run --no-project --python 3.13 --with matplotlib \
  python render_charts.py
```

This command only draws the saved measurements; it starts no model runs.

## Tasks, environment, and measurement

The public tasks and graders define the checks:

| Task | Required behavior | Checks |
|---|---|---:|
| [Cards](../../cases/cards/task.md) | Typed component inputs, slots, escaped text, prices, fallback content, and independent render calls | [6](../../grading/test_cards.py) |
| [Counters](../../cases/browser/task.md) | Two reusable Alpine counters, independent state, initial HTML, reset, and local assets | [3](../../grading/test_browser.py) |
| [Events](../../cases/events/task.md) | Typed Python Events, server catalog lookup, rendered updates, repeated selections, and independent pages | [3](../../grading/test_events.py) |

Each task has a small initial application under its `starter/` directory.
The [grading guide](../../grading/README.md) distinguishes behavioral checks
from implementation choices that need source review. Passing the checks does
not establish production readiness or complete coverage of the requested
implementation.

All runs used high reasoning effort, two CPUs, 4 GB RAM, a 512-process limit,
and the same local Docker image ID. [versions.json](versions.json) records
Python 3.12.14, Node 22.23.2, Codex CLI 0.153.4, Citry 0.4.6, and the other
reported package versions. The [Dockerfile](../../image/Dockerfile) and
[dependency lock](../../image/requirements.lock) describe the image build.

The [runner](../../run.py) gave each agent a fresh application directory and
public network access. Agents could fetch live documentation and inspect
installed package source. The repository checkout, contributor instructions,
reference solutions, other trials, and graders were not mounted in their
containers. The common prompt prohibited cloning upstream and searching for
evaluation solutions; this was an instruction, not a network restriction.
Personal configurations and skills were excluded. Codex's bundled
capabilities remained available, and agent delegation was disabled.

All attempts ran sequentially. The first three plans shuffled their conditions
with seed 17; the two repeat plans used seed 42. Timing started immediately
before launching Codex and ended after confirmed container removal. It
includes startup, model and tool work, agent-authored verification, and
shutdown. It excludes preparation, authentication, and independent grading.
The grader ran afterward in a separate container with no outbound network,
no credentials, and a read-only submission.

Before the Events batches, the common environment wording was clarified to
identify Python Playwright and its APIs. The original cards/counters prompts
were preserved. The two [common](common-original.md)
[versions](common-python-playwright.md) are extracted from the saved prompts;
the seven complete files under [prompts/](prompts/) preserve their exact
recorded bytes. Each run identifies its prompt file and SHA-256 hash.

## What the public record contains

[records.json](records.json) contains all 40 runs from the five recorded
plans, with their original order and repetition numbers. It includes only
selected configuration values, timestamps, status, durations, raw usage
counters, input hashes, and grade fields. The artifact map gives hashes for
the published prompts, common wording, skill snapshot, and version record.
Recorded runner, grader, task, and skill hashes matched the repository inputs
when this record was prepared; the saved prompt hashes also matched every run.

Usage counters are Codex's accumulated reported fields. Cached input is not
a separate quantity to add to total input, and reasoning output is not a
separate quantity to add to total output. These values do not measure unique
documentation size or monetary cost. An absent usage value means unknown.

The export omits local absolute paths, authentication metadata, raw commands,
container inspections, transcripts, and submitted applications. Readers can
recompute the reported measurements and run the public tasks again. This
record does not allow independent regrading or source review of the original
submissions.

## Recompute the totals

From this result directory, the following uses only the public JSON:

```sh
python - <<'PY'
import json
from pathlib import Path

runs = json.loads(Path("records.json").read_text())["runs"]
print("Runs:", len(runs))
print("Passed:", sum(run["grade"]["passed"] for run in runs))
print("Test executions:", sum(run["grade"]["tests"] for run in runs))
print("Seconds:", round(sum(r["elapsed_seconds"] for r in runs), 3))
PY
```

The outputs are 40 runs, 40 passes, 132 test executions, and 9,318.156 seconds.

## Repeat the procedure

Use a disposable checkout containing this record and matching runner, grader,
task, starter, and skill hashes. Follow the harness's
[build, verification, and login instructions](../../README.md#build-and-verify)
from `benchmarks/agent_usage/`. A recorded local image ID is provenance, not
a public image download. Rebuilding can change Debian packages; record the
new image ID and keep that image fixed across your comparison.

These commands prepare the same five allocations. They do not start model
calls. Preparation saves each prompt, so changing the common wording for the
next batch does not alter already prepared runs.

```sh
record=results/2026-09-agent-docs
cp "$record/citry-consumer/SKILL.md" \
  treatments/citry-consumer/SKILL.md
cp "$record/common-original.md" common.md
python run.py plan --model gpt-5.6-terra \
  --cases cards browser --arms homepage llms \
  --repetitions 2 --seed 17 --effort high --timeout 900 \
  --out runs/reproduction/pilot-terra

cp "$record/common-python-playwright.md" common.md
python run.py plan --model gpt-5.6-terra --cases events \
  --arms llms guidance skill --repetitions 2 --seed 17 \
  --effort high --timeout 900 --out runs/reproduction/events-terra
python run.py plan --model gpt-5.6-luna --cases events \
  --arms llms guidance skill --repetitions 2 --seed 17 \
  --effort high --timeout 900 --out runs/reproduction/events-luna
python run.py plan --model gpt-5.6-terra --cases events \
  --arms llms skill --repetitions 5 --seed 42 \
  --effort high --timeout 900 --out runs/reproduction/repeat-terra
python run.py plan --model gpt-5.6-luna --cases events \
  --arms llms skill --repetitions 5 --seed 42 \
  --effort high --timeout 900 --out runs/reproduction/repeat-luna
```

Compare the prepared prompt hashes with this record before starting. Use the
recorded model identifiers if your account offers them; replacing a model
creates a different comparison. Each preparation prints its new plan path.
Execute those plans one at a time, replacing `PLAN_ID` with the printed ID:

```sh
python run.py execute \
  runs/reproduction/pilot-terra/plan-PLAN_ID.json
```

Repeat `execute` for the other four printed plan paths. Execution starts real
model calls and grades each result. The 40 runs have a combined upper limit
of ten hours of agent time, plus setup and grading. The
[harness README](../../README.md#read-results) explains private output storage,
reporting, and interrupted-run recovery. No new model calls were made to
prepare this public record.

## Limits on interpretation

The experiment tests starting instructions with a fixed installed package and
live public documentation. Agents could discover other documentation and read
installed source in every condition. An index-condition success therefore
does not show that the website alone supplied everything the agent needed.
The detailed task prompt also supplied substantial implementation guidance.

The task and model allocation is small and uneven, and models ran at different
times. Documentation, network conditions, and model service behavior were
not frozen. New runs can reproduce the procedure and inputs without producing
the same applications or timing. All attempts passed, so this sample did not
distinguish reliability between conditions. It establishes neither statistical
significance nor equivalence, and it does not cover larger applications or
agents generally.

The skill condition changed both instruction content and how that content
was supplied. It does not isolate the effect of skill packaging. These
results give no observed correctness reason to require this candidate skill
for the tested tasks. Different tasks, models, or skill contents could produce
different results.
