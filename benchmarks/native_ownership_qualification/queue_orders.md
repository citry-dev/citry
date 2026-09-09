# Retain Python queue-order fields in the native journal

## Prior art

`ownership.py::_next_order` uses Python integers; RenderQueueRecord retains those
values. The standalone journal's `CallRow` converts enqueued/rendered/settled
orders to u64, then recreates Python integers in `queue()`. Capture, bind,
settle, queue assignment and retirement increments all participate. The retained
boundary report proves rejection at `2**64` and partial invocation retirement
when an increment starts at `2**64 - 1`. Native retirement's exact-integer
conversion currently propagates overflow instead of requesting Python fallback.

## Chosen representation and alternatives

Store queue orders as Python object references, like the invocation fields.
Capture/bind/settle and queue assignment retain those references; exports clone
them. GC visits all added references. Keep the existing optional rendered/settled
fields. Retirement increments a Python integer and stores that value, so crossing
the u64 boundary does not create a partial overflow failure. Existing cached
immutable rows keep their earlier values.

Portable relationship calculation still uses u64 IDs/orders. Its adapter rejects
out-of-range exact integers as UnsupportedRetirement before native mutation,
allowing the existing Python path to process the graph. Do not broaden numeric
relationships or add a big-integer Rust dependency merely to retain Python row
fields. The native API stub still accepts/returns int for these orders; Python
integers already include the boundary values. The PyO3 implementation signature
changes only inside the standalone benchmark module.

Keeping u64 plus a special overflow path would require guards throughout capture,
binding and settlement and preserve integer reconstruction on ordinary exports.
A separate arbitrary-precision Rust type would duplicate Python's representation
and add conversion and packaging work. Retaining references directly is simpler
and matches how the other stored fields already work.

## Falsifiers, errors and scope

Repeat the four boundary observations; require successful exact values beyond
u64 and consistent invocation/queue state. Compare retained queue-order identity,
replay/rollback, failed-queue behavior and constructor/field cycles. Exercise
retirement with out-of-range IDs/orders through the Python fallback and compare
snapshots. Run all non-browser package tests with the candidate in the pytest
process; existing subprocess bootstraps remain outside that qualification.
Then rerun the complete-render production-reference screen on the rebuilt
artifact, retaining source hashes and all samples. Require seven joint wins and
0.25 ms median paired mean wall saving for the full candidate; this comparison
does not isolate the representation's incremental performance.

Invalid table indexes/record widths still raise. Arbitrary direct writes of
inconsistent invocation and queue identities, custom order arithmetic callbacks,
reentrant destructors and allocation-failure atomicity remain unqualified.
This fixes the demonstrated numeric representation failure, not every possible
partial mutation on unexpected private input.

No shipping registration, wrapper/stub, parser/AST/compiler or five language
implementations change in this step. Native core extraction and production
packaging remain the next structural plan. This written plan precedes the
PyO3 signature changes; ExitPlanMode is unavailable in this session.
