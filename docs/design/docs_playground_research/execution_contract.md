# Playground execution and learning contract

**Date:** 2026-07-28
**Status:** Stage 3 recommendation
**Scope:** preview-value semantics, Python diagnostics, the first starter, and
the already accepted Run plus Auto-run control model

This record settles how one Python module produces the HTML shown by the Citry
playground. It also recommends the module visitors should see first. It does
not authorize production page work while the runtime and containment gate in
[`runtime_feasibility.md`](runtime_feasibility.md) remains open.

The recommendation is:

1. Preview the module's final expression.
2. Accept only `str` and its `Markup` subclass, `CitryElement`, and
   `CitryRender`.
3. Capture stdout and stderr as console data. Never interpret them as preview
   HTML.
4. Do not inject a playground-only `render(value)` function. A visitor who
   wants an explicit Citry render can end with `Card().render()`, which uses the
   public API and produces `CitryRender`.
5. Reject top-level await in the first release and execute code with ordinary
   module semantics.
6. Start with the medium typed Card-like module in this record. Do not ship a
   preset selector in the first release.

The accepted run trigger is a separate decision. The page always exposes Run
and also exposes an Auto-run toggle. Neither control changes which Python value
becomes the preview.

## Evidence and method

The research began with the product patterns in
[`product_survey.md`](product_survey.md), the browser runtime constraints in
[`runtime_feasibility.md`](runtime_feasibility.md), the provisional first-time
reader in [`../docs_content.md`](../docs_content.md), and the current rendering
contract in
[`docs_site/content/concepts/rendering.md`](../../../docs_site/content/concepts/rendering.md).

The executable proof contains:

- [`preview_runner.py`](execution_proof/preview_runner.py), with all four Stage
  3 candidates;
- [`starter_candidates.py`](execution_proof/starter_candidates.py), with the
  three starter modules; and
- [`test_preview_runner.py`](execution_proof/test_preview_runner.py), with the
  behavior matrix and source-position checks.

The proof was run on CPython 3.13.12 with the current checkout imported through
the workspace environment. Installed distribution metadata reported
`citry==0.2.0`, `citry-core==1.4.0`, and `MarkupSafe==3.0.3`. The checkout
contains newer source work, so this is evidence for the current tree, not a
claim that the published Citry 0.2.0 wheel has every current API behavior.

```sh
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q \
  docs/design/docs_playground_research/execution_proof/test_preview_runner.py
```

The result was 76 passing tests. Ruff also passed for the proof directory:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run ruff check \
  docs/design/docs_playground_research/execution_proof
```

The runner has not yet been executed inside the pinned Pyodide 314.0.3 and
Python 3.14.2 browser tuple. That repetition belongs to the runtime acceptance
matrix and must pass before implementation approval.

## Decision: preview the final expression

The playground executes one Python module. If its last statement is an
expression, the value of that expression is the preview candidate. The runner
normalizes that value while the expression is executing so a serialization
failure retains the expression's `<playground>` source line.

These endings are equivalent at the preview boundary:

```python
Welcome(name="Ada")
```

```python
Welcome(name="Ada").render()
```

```python
str(Welcome(name="Ada"))
```

They produce `CitryElement`, `CitryRender`, and `str`, respectively. The first
form is the canonical starter ending because it has no wrapper to explain and
keeps the component value visible. The second is the explicit public Citry
alternative. The third matches the everyday serialization API.

The final expression rule is playground behavior, similar to an interactive
Python display hook. The code remains valid when copied into a `.py` module,
but ordinary Python will not display its unassigned final expression. The UI
must say this next to the result contract and point out that a normal script
uses `str(...)` or `print(...)` when it wants terminal output.

### Accepted result types

| Final value | Behavior |
| --- | --- |
| `str` | Use the exact string as preview HTML. |
| `markupsafe.Markup` | Use it as preview HTML because `Markup` is a `str` subclass. |
| `CitryElement` | Call `str(value)`, which renders and serializes it. |
| `CitryRender` | Call `value.serialize()`. |
| No final expression | Return a `missing_preview` Python-panel diagnostic. |
| `None` | Return a `none_preview` diagnostic with the accepted forms. |
| Any other object | Return `unsupported_preview_type`, name the type, and list the accepted forms. |

`str` and `Markup` are accepted values, not declarations that the content is
safe. All produced HTML remains hostile input to the separately sandboxed
preview iframe.

### AST execution algorithm

The proof implements this sequence:

1. Parse with `ast.parse(source, filename="<playground>", mode="exec")`.
2. Reject top-level `await`, `async for`, and `async with` with an actionable
   source-linked diagnostic. Definitions of ordinary and async functions
   remain legal.
3. If the last statement is a previewable `ast.Expr`, replace only that
   statement with an assignment whose right side calls the private normalizer.
4. Generate result and normalizer names which do not occur anywhere in the
   source text. This handles normal user declarations of the same private
   names.
5. Apply `ast.copy_location` to the generated nodes and compile the modified
   module once with the filename `<playground>` and `dont_inherit=True`.
6. Clear known Citry-owned state, execute in a fresh module namespace named
   `__playground__`, and capture stdout and stderr independently. A conventional
   `if __name__ == "__main__"` block therefore does not run.
7. Return either normalized HTML or a structured diagnostic. The parent keeps
   the last successful iframe separately, according to the stale-result model
   in the main design.

Normalization is part of the replacement expression rather than a step after
`exec()`. That detail made Citry validation and render failures include the
visitor's final expression line. The named `preview` prototype, which
normalized after execution, lost that line for an assigned `CitryElement`.

The private names prevent accidental source collisions. They are not a
security boundary. Visitor code can inspect or mutate its global namespace,
and the browser containment design must already treat the whole Python run as
hostile.

### Python edge cases

| Case | Contract |
| --- | --- |
| Future import | It remains in its original legal position and its compiler flag applies. |
| Several statements separated by semicolons | The last AST expression is previewed once. Earlier statements retain their order. |
| Module docstring followed by a final expression | `__doc__` remains intact and the later expression is previewed. |
| Module containing only a string literal | Treat it as a docstring and report no preview. Rewriting it would change ordinary module metadata. Use `html = "..."; html` to preview a literal-only module. |
| Empty module or final assignment | Execute it, preserve captured output, then report that a preview expression is missing. |
| `if __name__ == "__main__"` | Do not enter the block because the fresh module is named `__playground__`. Keep the preview expression at module level. |
| Private result names in source | Choose a deterministic unused suffix and continue. |
| Syntax error | Report `<playground>`, line, and column without running the module. |
| Runtime or render error | Keep visitor and generated-source frames, the deepest relevant `<playground>` line, and the exception message. Remove runner and absolute host paths. |
| Top-level await or top-level async statement | Reject in the first release as inconsistent with ordinary module execution. |

Top-level await would require a public async lifecycle, cancellation behavior,
and copyability guidance that the single-module product has not designed. The
runner can revisit it only with those contracts and equivalent Worker tests.

## Candidate comparison

The survey found no industry-wide Python output convention, so all four
candidates were executed rather than selected by precedent.

| Criterion | Final expression | `render(value)` helper | Printed stdout | Named `preview` |
| --- | --- | --- | --- | --- |
| First useful ending | `Card()` | `render(Card())` | `print(Card())` | `preview = Card()` |
| Copyable Python | Valid; a normal module simply does not display the expression | Fails outside the playground unless a new helper is supplied | Valid and visibly writes to a terminal | Valid but does not visibly render in a normal module |
| Citry explicit path | `Card().render()` already works | Duplicates the meaning of the public `.render()` method | Uses `__str__` implicitly | Requires a reserved global |
| Accepted types can stay narrow | Yes | Yes | No; `print()` stringifies arbitrary objects | Yes |
| Logs stay separate from HTML | Yes | Yes | No | Yes |
| Citry render traceback points to user source | Yes, through the final expression wrapper | Yes, through the helper call | Yes, through the `print()` call | Not without another transform or a source heuristic |
| Missing-value rule | Final statement is not an expression | Helper was not called | Stdout is empty | Global was not assigned |
| Hidden playground machinery | One documented display rule and private AST names | Public-looking injected function | Special meaning for all stdout | Reserved global plus post-execution lookup |

The proof exercised a string, `CitryElement`, `CitryRender`, missing output,
`None`, an unrelated object, multiple prints, syntax failure, and a Citry render
failure for every candidate. It also exercised `Markup` for the two serious
candidates.

The printed-stdout candidate demonstrated the central failure directly:

```text
<p>preview</p>
debug record
{'unrelated': 1}
```

All three lines became iframe HTML. `print(None)` and `print(object())` were
also accepted because `print()` erases the intended type boundary. This makes
ordinary debugging output capable of changing the page and is therefore
rejected.

The named value is strict but adds ceremony without making copied code render.
Its simplest implementation also loses the assignment frame when rendering is
deferred until after module execution. It is rejected.

The explicit helper is clear at the call site and its prototype preserved
tracebacks, but it creates a function which does not exist in a normal module.
It also competes with Citry's real `CitryElement.render()` API. It is rejected
as both the required and optional contract. The existing final-expression
forms provide explicitness without introducing a playground API.

## Stdout, stderr, and diagnostics

stdout and stderr are run metadata, not preview values. Capture them in order
and return them beside the HTML or failure. The first UI may expose them in an
expandable Console section within the Python diagnostic tray. If that section
is deferred, diagnostics must still state that output was captured rather than
silently dropping it.

The Worker response needs these fields at minimum:

```text
run id
status
HTML or no HTML
stdout
stderr
diagnostic kind
message
filename
line
column
formatted traceback
```

Python diagnostics remain persistent in the left panel until a successful run
or an explicit dismissal. A short live-region announcement may accompany the
update but cannot replace it. Client-side iframe failures remain right-panel
diagnostics and do not change the Python output contract.

Traceback filtering is part of the boundary, not a presentation option. Keep
visitor frames such as `<playground>` and safe generated-source frames, plus
Citry's component-aware exception message. Remove `preview_runner.py`, runner
function names, Python AST internals, and absolute host paths before returning
diagnostics to the page.

The proof distinguishes:

- syntax failure;
- ordinary Python runtime or Citry render failure;
- missing preview expression;
- preview expression returning `None`;
- unsupported preview type;
- rejected top-level async behavior;
- explicit-helper multiple calls, retained only as comparison evidence; and
- `SystemExit` or `KeyboardInterrupt`, which become an execution-stopped
  outcome rather than escaping the runner boundary.

Loading, timeout, Worker restart, stale result, and internal protocol failures
belong to the outer browser state machine. They must not be mislabeled as a
Python source error.

## Run and Auto-run stay separate

The control shape has already been accepted:

- Run is always visible and `Ctrl+Enter` or `Cmd+Enter` invokes it immediately.
- Auto-run is a user-toggleable debounced run after edits.

The following is a separate policy hypothesis. It is not approved by the
preview-value decision and needs browser performance and first-reader evidence:

1. Run the built-in starter once after the pinned runtime is ready, even if a
   returning visitor previously disabled Auto-run.
2. Start Auto-run enabled for a first visit so the page behaves like the live
   editor promised by the top-level Try it link.
3. Remember an explicit toggle choice in a versioned browser-local setting.
4. Use a 500 ms idle debounce as the starting value, replace queued cold-start
   edits with the newest source, and let Run bypass the debounce.
5. Turn Auto-run off after a hard timeout or Worker crash and explain how to
   retry. Do not turn it off for syntax, validation, or render errors, which are
   normal while editing.
6. Keep the previous successful result visibly stale while a run is pending or
   has failed.

The 500 ms value is a measurement candidate, not a performance fact or accepted
default. Stage 5 must specify the candidates, behavior, and measurement hooks.
Stage 6 must approve or replace the default, persistence, debounce, and
failure-pause rules using browser performance and first-reader evidence,
without reopening the final-expression contract.

## Starter comparison

All three candidates use the current public Citry API and finish with the
recommended implicit preview expression.

| Candidate | Source size | Meaningful first edit | Concepts introduced | Visible payoff | Unexplained infrastructure | Next link |
| --- | ---: | --- | --- | --- | --- | --- |
| Minimal visible component | 124 bytes, 10 lines | Change one heading | `Component`, `template`, final expression | Immediate but little evidence beyond static HTML | None | Your first component |
| Typed welcome card | 684 bytes, 31 lines | Change `name` or `accent` in the final call | typed `Kwargs`, a Python text transformation, template expression, CSS data, component CSS, final expression | Normalized text and color respond in one small module | Two data hooks need short labels | Your first component, then Card example |
| Two-component feature list | 612 bytes, 35 lines | Change one feature label | typed input, data, nested component tag, composition, CSS | Shows reuse and composition | Registration and two class roles need explanation | Build a page from components |

The line and byte counts come from the exact strings in
[`starter_candidates.py`](execution_proof/starter_candidates.py). Serialized
HTML was 60, 515, and 421 bytes respectively in the host proof; generated
render ids make byte counts observational rather than stable snapshot values.

### Recommended starter

Use the typed welcome card:

```python
from citry import Component


class WelcomeCard(Component):
    class Kwargs:
        name: str
        accent: str

    def template_data(self, kwargs: Kwargs, slots):
        return {"name": kwargs.name.strip().title()}

    def css_data(self, kwargs: Kwargs, slots):
        return {"accent": kwargs.accent}

    template = """
      <article class="welcome-card">
        <p>Welcome, <strong>{{ name }}</strong>.</p>
      </article>
    """

    css = """
      .welcome-card {
        padding: 1rem;
        border-top: 0.25rem solid var(--accent);
        border-radius: 0.5rem;
        background: #f6f3ff;
      }
    """


WelcomeCard(name="ada lovelace", accent="#6f42c1")
```

The minimal candidate is faster to scan but proves little that ordinary HTML
does not already do. The composition candidate shows an important strength but
asks the reader to understand two class roles and component lookup before the
first edit. The card earns its extra lines by making both Python data and
component-owned CSS visibly editable.

Do not use `components_step9.py` as the starter. It is part of a longer journey
and contains state, browser behavior, actions, composition, and host context
which cannot be explained by the initial workspace.

### Relationship to Getting started

The playground is a zero-install evaluation and experimentation surface. It
does not replace the guided tutorial or become the canonical owner of Card
behavior.

After the first successful edit, show a brief invitation such as "Build this
step by step" linking to
[`Your first component`](../../../docs_site/content/getting-started/your-first-component.md).
That tutorial owns file placement, installation, terminal rendering, slots,
limitations, and the complete learning sequence. The playground starter is a
shorter cousin with no slot so it can focus on one input-to-HTML-to-CSS loop.

Do not add a preset selector in the first release. Keep the minimal and
composition candidates as verified future presets. Add them only after the
runtime payload, reset behavior, and first-reader comprehension are measured.

## Error modes and recovery

| Failure | Runner response | Product recovery |
| --- | --- | --- |
| Parse or compile failure | Source-linked syntax diagnostic; no execution | Keep the prior result stale and run again after edit |
| Missing, `None`, or unsupported preview | Specific contract diagnostic | Show accepted endings and keep prior result stale |
| Citry validation, render, or serialization failure | Filtered traceback with `<playground>` frames and component-aware message | Expand details, preserve source, rerun after edit |
| stdout or stderr output | Capture separately, whether the run succeeds or fails | Show in optional console; never put it in iframe HTML |
| Top-level async construct | Source-linked unsupported diagnostic | Define async work inside a function or use supported synchronous code |
| `SystemExit` or `KeyboardInterrupt` | Execution-stopped diagnostic | Start the next run in the normal lifecycle |
| Infinite loop or unresponsive native call | No Python response | Outer deadline terminates Worker, disables Auto-run, and offers Retry |
| Dynamic tampering with injected private globals | Internal runner failure | Discard Worker and start a fresh generation |
| Malicious or failing preview script | Right-panel iframe diagnostic | Keep parent isolated; reset or rerun source |

The proof catches Python control-flow exceptions for comparison. A production
Worker must still have an outer JavaScript failure boundary because Python or
WebAssembly can terminate before it constructs a structured result.

## Gate result and falsifiers

Stage 3 recommends approval of:

- final-expression preview with the strict normalization table above;
- no injected `render(value)`, named global, or stdout-as-HTML fallback;
- the typed welcome card as the only initial starter;
- no initial preset selector;
- a direct handoff from the playground to Your first component; and
- the accepted Run plus toggleable Auto-run control shape, separately from the
  still-unvalidated defaults and timing hypothesis above.

Reopen this decision if the exact pinned Pyodide runner cannot preserve future
imports or `<playground>` source positions, if current Citry release artifacts
do not expose the tested `CitryElement` and `CitryRender` behavior, or if a
first-reader test shows that the final-expression rule is materially less
understandable than a copyable public API alternative. Do not reopen it merely
because a final editor library exposes a different internal evaluation hook.

Before product integration, repeat the complete proof in the exact manifest
tuple, add it to the browser Worker protocol test, and verify the user-visible
diagnostic text with the final editor's line and column conventions.
