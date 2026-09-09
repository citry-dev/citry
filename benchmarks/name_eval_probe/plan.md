# Reuse the evaluation path for a simple variable

## Prior art

`safe_eval()` in `packages/py/citry_core/citry_core/safe_eval/eval.py`
compiles once, but each evaluation still calls its error wrapper, a generated
lambda, the decorated `variable()` function, and `is_safe_variable()`.
The transformer in `crates/python_safe_eval/src/transformer.rs:886` rewrites
an external name to a checked lookup with source positions. The runtime
policy in `sandbox.py:245` checks the name on every call. Custom mappings
can execute arbitrary code during the lookup.

`docs/design/performance.md` section 5 already moves error-position extraction
off the successful path. Section 6.7 explains why attribute checks cannot be
precomputed from the key: the runtime object affects their result.
`packages/py/citry_core/tests/test_safe_eval.py` covers extra validators,
unsafe names, mapping access, and formatted source ranges.

One untimed render at commit `26312d08` counted 1,904 bare-name evaluations
among 2,541 expression evaluations. This count describes complete expressions,
not the larger number of variable accesses inside compound expressions.

## Experiment

For an exact ASCII identifier, combine the successful single-positional-argument
call, live variable policy check, and mapping lookup in one closure. Keep both
layers of error formatting: the variable operation always adds its position;
the outer layer formats an exception only if it remains unprocessed. Retain the
ordinary evaluator for keyword calls and invalid argument counts. It also
handles all other expression shapes.

The experiment uses the existing Rust transform before choosing the candidate.
Python keywords, Unicode names, whitespace, comments, and string subclasses
stay on the ordinary path. A production implementation must also retain that
path when an extra variable validator or a substituted variable interceptor is
present. The safety policy and mapping lookup stay live on every evaluation.
No result or context value is cached.

The benchmark records node evaluators during their ordinary first compilation,
then swaps those evaluators outside timed renders. Compilation and switches
are excluded from repeated-render timing. Full HTML and ownership snapshots
must agree. The benchmark does not qualify arbitrary mutations of function
code objects or closure cells.

## Alternatives and decision

Inlining every intercepted operation would affect many more error and callback
paths. A first-render safety decision would skip a live policy check. Test the
simple-name case first, retaining those checks and the existing compiler output.

Use two runs of 60 alternating render pairs, taking less than a minute. Adopt
only if each run saves at least 0.15 ms by the median paired difference and
improves at least 40 pairs. A smaller or inconsistent benefit does not justify
another evaluation path. Any difference in lookup order, exceptions, security
checks, or output falsifies equivalence and must be fixed before adoption.

Qualification should compare mutable mappings, missing and private names,
callback failures including `StopIteration`, keyword and invalid calls, extra
validators, and names outside the candidate subset. Existing core tests are the
least expensive boundary for sandbox and source-message behavior; render pairs
cover integration. The final repository checks cover packaging and typing.

## Result and reproduction

Keep the active helper. Two final comparisons save 0.198 ms (43/60 favorable
pairs) and 0.274 ms (42/60 favorable pairs), meeting the stated threshold.
All four ownership snapshots and all HTML pairs match. The 300 focused
evaluator tests pass and explicitly assert which evaluator is active.

The first identity-preserving version assumed a positional constant layout
that did not match Python 3.14.3. Its guard selected the general evaluator.
The two `name-eval-inactive*.json` reports therefore compare ordinary
evaluators and provide no timing evidence for the shortcut. This was caught
by the reproduction guard and independently by review. The implementation
now finds the unique exact string and token tuple by type and value in the
compiled constants. It reuses those objects without assuming their order.

The production helper and its regression cases live in the core package.
Run the comparison from the optimization checkout:

```bash
.venv/bin/python benchmarks/name_eval_probe/probe.py \
  --output /tmp/name-eval.json
```

The harness loads the reference compiler from commit `26312d08`. It refuses
to run if the intended nodes do not select the shortcut. Keyword and invalid
calls execute the retained generated evaluator. An unrecognized constant
layout also uses the general evaluator in production. The operation formatter
is read from the error module and the expression formatter from the evaluator
module, matching their existing namespaces.

Keeping the fallback adds one callable and its closure per eligible compiled
expression. Those objects follow the existing node-evaluator lifetime. The
constant scan and allocation happen during compilation and are excluded from
this repeated-render experiment; this comparison establishes no first-render
speedup or memory reduction. No application data or policy result is cached.

Earlier prototype timings precede key-identity and formatter-namespace
corrections. The active reports are `name-eval-active.json` and
`name-eval-active-confirmation.json` in `benchmarks/results/repeat-render/`.
The harness checks active evaluator names outside timed renders. Arbitrary
code-object/closure mutation and interpreter versions outside the tested
Python 3.14.3 environment remain unqualified.
The active reports predate a change to the absent-helper diagnostic text only;
their timing loop and activation checks match the retained harness.
