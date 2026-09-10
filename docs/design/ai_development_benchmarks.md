# Design: compare AI development across web frameworks

Status: proposed, 2026-09-10. No agent evaluation has been run for this design.

The question is whether an agent delivers a correct application change more
reliably, quickly or cheaply with Citry, and whether its diagnostic tools explain
any advantage. A fast renderer and a convincing demo do not answer that question.
The result must permit a loss, a tie or a benefit limited to certain tasks.

## Prior art and the question each comparison answers

Citry's [AI-agent guide](../../docs_site/content/getting-started/ai-agents.md)
provides documentation and project setup instructions. Its app-aware checker is
`citry --app module:attribute check`; compiler failures also surface while loading
or rendering templates. The current [rendering benchmark](benchmarking.md) times
fixed implementations, not an agent's ability to change them. The companion
[framework interaction design](framework_interaction_benchmarks.md) measures the
resulting application's browser behavior, a separate outcome.

SWE-bench evaluates patches against repository tests in isolated environments.
That is useful prior art for reproducible patch evaluation, but its existing
issues do not provide equivalent tasks across Citry and other UI frameworks.
[Evaluation guide](https://www.swebench.com/SWE-bench/guides/evaluation/)

WebArena evaluates functional outcomes in self-hosted applications; BrowserGym
provides browser task environments and trace tooling. Those are useful patterns
for our browser assertions and retained traces. They evaluate agents operating
websites, so their scores are not evidence about agents implementing websites.
[WebArena paper](https://webarena.dev/static/paper.pdf),
[BrowserGym](https://github.com/ServiceNow/BrowserGym)

Run two comparisons, with distinct interpretations:

| Comparison | Question | Limit |
| --- | --- | --- |
| Same application tasks across frameworks | Which complete stack helps this agent finish? | Includes API design, familiarity, documentation and tooling together |
| Same framework with diagnostic feedback enabled or withheld | Does that framework's optional checker feedback help? | Does not isolate its compiler or prove another framework has equivalent diagnostics |

## An application designed independently of Citry

Author a new small project-management application with six screens: project list,
project detail, editable board, member permissions, activity feed and settings.
Include filtering, pagination, nested dialogs/forms, repeated items, server
validation, optimistic updates and persisted state. Aim for roughly 15-30 authored
UI components and several thousand application lines, excluding dependencies and
generated code. Match capabilities, not line counts or file layouts.

Create the product specification and acceptance scenarios before choosing an
implementation. Implement idiomatic versions with an identical fixture database
and domain rules. Where practical, share framework-independent Python domain
code; record adapters and backend differences rather than forcing unnatural
architecture. A maintainer familiar with each stack reviews its baseline and
reference solutions. All versions must pass the same black-box acceptance suite
before tasks are introduced.

Publish original harness/application code under an explicit permissive license
with a dependency and asset license inventory. Keep evaluation tasks and hidden
oracles private until the first frozen run. A newly authored app reduces exposure
to public solutions but cannot establish that model training contained no similar
code. If a public app is used later, record its exact commit, license, attribution
and third-party asset rights, and treat it as a separate external-validity cohort.
Do not assume that a recently created GitHub repository is absent from training.

Pilot with Citry, Django + HTMX + Alpine, and FastHTML. Add one stateful Python UI
framework from the interaction cohort after its baseline and task equivalence
are reviewed. This keeps the first result about Python-authored applications;
Django + React can be a later separately labeled mixed-language comparison.
Use one prequalified Citry configuration throughout, rather than switching
performance flags after seeing task outcomes.

## Eight task families and their hidden oracles

Each task starts independently from its own clean baseline commit. Avoid chaining
successful tasks, which gives later attempts different starting points.
Write scored prompts as product-level requirements with equivalent information,
not framework-specific implementation instructions. Review whether each defect
can arise naturally in every stack. If a framework prevents it by construction
or lacks a credible equivalent, record that property and use a separate native
capability case; do not inject a contrived bug merely to force a paired task.
Freeze the shared-task set before scoring and report the resulting coverage.

| Task | Required behavior and hidden checks |
| --- | --- |
| Rename a component input across a reusable form | All callers updated; defaults, validation and rendered output remain correct |
| Repair nested content scope | A supplied button updates its caller; the receiver and sibling retain their own state |
| Fix list identity after sorting/deletion | Selection, input text and focus remain attached to the same logical item |
| Add dependent filters and pagination | URL state, empty results, reset behavior and query count stay correct |
| Add a validated edit dialog | Invalid data stays local; success persists once; reopen shows current state |
| Repair out-of-order server responses | Older replies cannot overwrite newer state; reconnect/retry behavior is specified |
| Enforce a role change throughout the UI and backend | Hidden controls and direct unauthorized requests both behave correctly |
| Add a reusable summary with a regression constraint | Correct data and accessibility; no accidental extra requests or full-page reload |

Include both defect repair and feature addition. At least half the tasks must be
ordinary application work, not deliberately selected to match Citry diagnostics.
Publish that taxonomy before execution. Use variants with different fixture values
and equivalent wording so a memorized expected string cannot pass.

The hidden suite checks persistence and authorization through the server as well
as browser behavior. Include existing regressions, keyboard navigation and
adversarial values where the task requires them. A task fails if any mandatory
acceptance condition fails; report individual condition outcomes separately.

Human-reviewed reference patches must pass every task in every participating
stack. Add known incorrect patches that the oracles must reject: hard-coded
fixture responses, UI-only permission checks, dropped event handlers, suppressed
errors and modified test runners. If the oracle misses those mutants, repair and
freeze the task before running agents. Do not revise an oracle after inspecting
which framework won; a discovered defective task invalidates all its paired cells
and requires a disclosed corrected rerun.

## Agent environment and diagnostic feedback

Use two frozen model versions representing lower and middle price/capability
ranges, selected before the scored run using separate calibration tasks. Record
exact provider/model identifiers, sampling parameters, supported reasoning setting,
context limit, agent harness version and tool definitions. Tier labels alone are
not reproducible. Keep the harness and tools identical across frameworks.

Every attempt gets the same product task, fixture state, hardware resources,
public tests, terminal and browser tools, and a version-matched local documentation
snapshot. Provide equal-quality setup/verification instructions and retrieval
access, not an identical token count of framework documentation. Record what was
retrieved. Disable unrestricted external search in the controlled study so hidden
solutions and changing documentation cannot leak between runs. A later normal-web
workflow study can measure that different usage separately.

Optional diagnostics have two conditions:

1. Feedback enabled: after each submitted patch checkpoint, the harness runs the
   framework's declared diagnostic bundle and returns its output to the agent.
2. Feedback withheld: the harness runs the identical bundle at those checkpoints,
   retains its output for analysis, and returns only a fixed checkpoint receipt.

The bundle lists exact commands, versions, coverage and timeout policy. For Citry
it includes the app-aware template checker. Other stacks receive their actual
available template checks, type checks or lint commands, reviewed by an expert;
absence of an equivalent checker is recorded, not filled with a bespoke advantage.
Common formatting, Python lint and type-check commands stay available in both
conditions. The primary cross-framework contrast uses each stack's normal optional
diagnostic feedback enabled. The primary within-Citry contrast changes only the
app-aware Citry checker feedback, holding the common tools fixed. If a competitor
needs several framework-specific commands in its optional bundle, label its
within-framework result as a bundle effect, not the effect of one tool.

Agents may always run the same public tests and normal application build/start
commands. Runtime and compiler errors remain visible when those commands produce
them. This experiment therefore isolates optional diagnostic feedback, not all
Citry error messages. Do not disable essential compilation to manufacture a
"compiler off" condition.

The controlled runner exposes the optional diagnostics through its checkpoint
interface only. A checkpoint occurs after each completed edit-tool call or shell
edit batch, detected from the application diff, before the next model turn.
Apply that policy in both conditions and record all checkpoints. Different patches
and checkpoint counts still take different amounts of checking time; a common
policy does not equalize actual compute cost. Report that measured cost and the
fact that shadow checks differ from everyday lint-free development.

Audit terminal/process traces for standalone checker invocations, including CI or
test wrappers that expose the optional bundle. Ordinary builds, runtime compiler
errors and agent-authored tests remain allowed even if they share internal code
with the checker; the forbidden interface must be specified precisely in each
adapter. Intercept standalone invocations through the controlled runner where
possible. A leaked result is a recorded protocol violation, not a clean control.
Retain every initially assigned attempt and its outcome in the primary
assigned-policy analysis, with violation rates per condition. A separate
protocol-compliant sensitivity analysis cannot replace those attempts or the
primary denominator. Leakage prevents a clean interpretation of withholding;
disclose it and repair the harness for a new frozen study, rather than rerunning
only inconvenient attempts. A second natural-use study can make tools available
and observe whether agents choose them; availability alone is not evidence that
a tool was used.

Use isolated containers, fresh browser profiles and no memory shared between
attempts. The agent edits application files only. Hidden tests and evaluator code are outside the agent-readable filesystem,
process namespace and network access as well as outside its writable environment.
Export only the submitted application patch into a separate trusted evaluator.
Apply it to the pinned clean baseline, reinstall locked dependencies, rebuild
artifacts and reset the database, filesystem fixtures and browser profile before
running hidden tests. The agent's running process, manually altered database and
untracked build output are not deliverables. Never return hidden results to the
agent. Execution policy and reset machinery cannot be modified by the attempt.
Reject changes that disable required behavior or manipulate evaluation entry
points. Retain the submitted diff even when the attempt fails.

## Budgets, repetitions and outcome measures

Start with a pilot of three tasks, three frameworks, one model, two feedback
conditions and two independent repetitions: 36 attempts. Use it to repair task
ambiguity, estimate variance and validate the harness, not announce a winner.

A proposed scored run has eight tasks, four frameworks, two models, two feedback
conditions and three repetitions: 384 attempts. Randomize framework/condition order
within task/model blocks and spread blocks across comparable service periods.
Match seeds when a provider supports them, without claiming deterministic API
responses. Pilot tasks and scored task variants must be disjoint.

Proposed per-attempt limits are 20 minutes and 40,000 total billed model tokens,
whichever is reached first. Record provider token categories and enforce the
available accounting; a provider that cannot expose necessary usage needs a
predeclared substitute limit and separate reporting. The maximum model-token
allowance is 15.36 million for the 384 initially assigned scored attempts. Pilot,
calibration, infrastructure retries and judge calls require separate recorded
caps and are not included in that allowance. Before execution, compute currency
estimates from the selected providers' actual input/output/cached-token prices
and all those separate budgets. These are proposed experimental
limits, not a claim that all tasks fit them or that costs are already known.

| Measure | Definition |
| --- | --- |
| Correct completion rate | Fraction passing all mandatory hidden conditions within budget, from one independent attempt each |
| Completion by time | Fraction completed correctly at each elapsed-time threshold, including unsolved attempts |
| Time and cost | Task receipt to final patch, model service/tool/check time, billed token categories and currency |
| Delivered defects | Failed acceptance categories in the final patch, with overlapping assertions grouped and grouping rules published |
| Regressions | Previously passing behavior broken by the final patch |
| Diagnostic effect | Paired change in completion, defect categories, time and cost when optional feedback is available |
| Repair process | Patch/check cycles, repeated error signatures, invalid API references and time until each issue is resolved |

Completion-by-time credits the final submitted patch only if it passes the
hidden evaluator; its completion timestamp is submission time, not the later
evaluation finish. On a budget stop, export the last complete checkpoint, grade
it by the same rules and assign the actual budget-stop timestamp if it passes. Report budget
stops separately. A temporarily correct intermediate patch does not count if the
final patch regresses; earliest-passing-checkpoint analysis would be a separate
retrospective study with no hidden feedback to the agent.

A compiler error during work is useful feedback, not automatically a delivered
mistake. Counting raw errors would penalize a framework for detecting more of
them. Keep intermediate diagnostic counts separate from final defects. Final
failed assertions are an objective result; root-cause grouping is a reviewed
interpretation, with links back to those assertions.

Do not compare only the duration of successful attempts: that excludes the hard
failures and can make a worse framework appear faster. Show completion-by-time
curves and budget exhaustion alongside conditional successful-run durations.
Provider or harness outages are infrastructure failures with a recorded policy;
agent-caused broken builds, hangs and wrong patches remain scored outcomes.
No manual rescue is allowed within a scored attempt.

Report per-task/model/condition results and paired framework differences with
uncertainty clustered by task, not thousands of individual tool calls. Repetitions
on eight tasks do not establish broad software-engineering generality. Use pilot
variance to decide whether more task families are needed before public claims.
Keep primary endpoints fixed; label secondary comparisons and avoid choosing a
favorable task subset after seeing results.

## A strong model as reviewer, not the correctness oracle

A stronger model can review maintainability, suspicious shortcuts and defect
categories after objective tests. It cannot reliably replace browser/server
oracles or decide whether an unexecuted feature works. Give it a frozen rubric,
reference requirements, the patch and test evidence. Do not let it execute
instructions embedded in the submitted source.

Hide model identity, condition, timing and framework branding where feasible;
source syntax can still reveal the framework, so do not claim complete blinding.
Randomize comparison order. Have a second independent reviewer rescore a
preselected sample, calibrate against human labels, publish agreement and send
material disagreements to a human. Report qualitative scores separately from
functional success. A judge preference must not turn a failed test into a pass.

## Artifacts and permissible conclusions

Retain task/base/reference hashes, dependency and documentation snapshots,
container/browser/model versions, prompts, tool trajectories, checkpoints,
submitted patches, hidden test version/results, browser traces, usage records,
timeouts and scoring decisions. Public reports redact credentials and fixture
personal data. Keep large logs, model traces and experimental probes in a dedicated
benchmark artifact store or research branch; merge maintained specifications and
approved harness code through the normal PR process.

Publish a statement such as "On these tasks with these models, Citry with its
checker completed X of Y attempts, compared with ..." only after the run. A
within-Citry feedback benefit supports the value of that tool in this setting;
it does not by itself show that compiler design caused a cross-framework gap.
"Best for AI development" needs repeated results across task families, models and
independently reviewed implementations. This design tests that claim rather than
assuming it.
