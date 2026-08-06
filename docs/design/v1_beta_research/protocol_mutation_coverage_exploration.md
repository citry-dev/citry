# Protocol mutation coverage exploration

**Status (2026-08-04): explored; GitHub issue #54 closed as not planned.**

Issue #54 opened with 35 shared protocol mutations, 32 directly covered
constraints, and 472 inventoried constraints. During this exploration,
concurrent client-graph work moved the live totals to 38 mutations, 35 directly
covered constraints, and 476 constraints. This note tests whether the current
441-entry difference represents distinct risks or mostly repeated uses of the
same validator behavior.

## Recommendation

Do not implement a one-case-per-constraint expansion. Keep complete constraint
ownership, the representative cross-language mutations, the fixture corpora,
and the real server and browser boundary tests. Add a new exact mutation when
a schema change, validator change, or discovered bug gives it a concrete
reason to exist.

This is not a claim that every validator branch is exhaustively tested. It is
a decision that one case per schema pointer is a poor proxy for that goal.

## What the remaining 441 entries are

| Schema keyword | Uncovered occurrences | Share |
| --- | ---: | ---: |
| `required` | 139 | 31.5% |
| `type` | 132 | 29.9% |
| `const` | 52 | 11.8% |
| `additionalProperties` | 33 | 7.5% |
| All other keywords | 85 | 19.3% |

The first four routine shapes account for 356 entries, or 80.7 percent. The
441 entries collapse to 169 keyword-and-value combinations even before
accounting for shared validators. Common repetitions include 42 object type
checks, 40 string type checks, 33 closed-object checks, 21 non-empty-string
checks, and 19 integer type checks.

The registries route all 476 constraints to 23 validator families. A schema
edit changes the relevant count and fingerprint, forcing review even when it
does not receive a new mutation. The 38 current mutation records cover 35
specific constraints and prove matching Python and JavaScript issue paths and
categories. The earlier numbers in issue #54 remain correct for the snapshot
when it was opened.

## Why the reported mutation count is not test coverage

The exact-mutation report counts only cases linked to one canonical schema
pointer. It does not count other tests that execute the same behavior. For
example:

- the Events JavaScript tests exercise calls beyond the 16-call `maxItems`
  limit;
- Python tests reject HTTP status 600, exercising the result error maximum;
- the client-graph canonicalization corpus exercises the safe-integer maximum;
- descriptor, manifest, result, graph, and relationship fixture suites contain
  invalid examples outside the shared mutation index; and
- real dispatcher and browser tests exercise atomic rejection and side effects
  that JSON Schema cannot describe.

The existing corpus contains 19 Events exchanges, 9 descriptors, 8 Events
manifests, and 47 client-graph examples. The final browser matrix passed 594
tests across Chromium, Firefox, and WebKit.

A broad exploratory Python run passed 4,148 tests and reproduced two already
recorded failures from concurrent work. Combined embedded-protocol branch
coverage was 78.19 percent. That number includes builders, carriers, and
relationship logic, while some standalone tests execute the byte-identical
canonical packages instead of the embedded paths. It therefore cannot prove
per-constraint completeness, but it also shows that a 100-percent schema
mutation count would not imply complete runtime branch coverage.

The independent Stage 6 review found strict-JSON ordering and integral-number
differences. Neither was represented by the proposed one-defect mutations:
cycles are not JSON values, and a mathematically integral `1.0` is valid for a
JSON Schema integer. Focused adversarial cases found those problems where a
schema-pointer quota would not.

## Cost and likely payoff

Each new mutation needs a valid seed that reaches the intended nested record,
one isolated edit, an expected first issue, Python and JavaScript execution,
and maintenance whenever first-error ordering changes. Nested definitions and
unions make automatic seed selection the difficult part. Solving it generally
would move the tooling toward the schema compiler or generator that the design
explicitly rejected.

The likely bugs from the repeated constraints are narrower:

- a required or allowed field list disagrees with the schema;
- one field calls the wrong scalar helper;
- a discriminator or range is implemented differently in Python and
  JavaScript; or
- a newly added schema rule has no runtime implementation.

Ownership fingerprints catch the last case at review time. Representative
mutations exercise the shared helpers and first-error contract. Positive and
invalid fixtures exercise complete records. Adding hundreds of cases would
improve field-by-field rejection proof, but it would not improve semantic,
transport, atomicity, strict-language-value, or DOM coverage.

As a useful comparison, the official JSON Schema Test Suite groups
representative valid and invalid examples by keyword or behavior. It
specifically invites new coverage for bugs found in real implementations. That
does not dictate Citry's policy, but it supports behavior-driven cases over a
raw schema-occurrence quota:
[JSON Schema Test Suite](https://github.com/json-schema-org/JSON-Schema-Test-Suite).

## Better policy

Keep these rules instead of an exhaustive quota:

1. Every schema constraint must have exactly one validator-family owner.
2. A schema change must update the ownership fingerprint and receive review.
3. A new schema keyword or distinct validator branch gets a representative
   Python and JavaScript mutation.
4. A protocol drift bug gets the smallest regression case that would have
   caught it.
5. Real incoming boundaries remain strict and atomic before product code acts.
6. Revisit broader mutation generation only after repeated drift shows that
   these controls are insufficient.

If a future hardening pass is wanted, start with the validator families that
have no directly attributed mutation and add only cases that exercise a new
branch. Do not restore the target of 472 mutation cases.

## Commands used

```bash
uv run --no-sync python -m packages.protocol._tooling.check \
  packages/protocol/events/v1 packages/protocol/client_graph/v1
uv run --no-sync pytest -q packages/py/citry/tests \
  packages/protocol/_tooling/tests \
  --cov=citry._protocol.events \
  --cov=citry._protocol.client_graph \
  --cov-branch --cov-report=term-missing --cov-fail-under=0
```
