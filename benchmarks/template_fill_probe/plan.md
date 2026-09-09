# Remove unused fallback objects and generic template-fill call contexts

## Prior art and scope

Iteration 20 delayed initialization of unused fallback Slots but retained a lazy
wrapper, and regressed complete rendering. SlotNode.render still builds every
fallback before invoking a supplied fill. `_TemplateSlotContent._render` reads
fallback only when `_fallback_var` is set and reads slot data only for a binding.
An exact ordinary template callable with neither binding therefore does not need
those two call-context values. This experiment changes that whole fill invocation
path instead of introducing another lazy wrapper.

For an eligible supplied template fill, retain the outlet source record and the
fallback source/fill rows in their original order, but omit the unused fallback
Slot, content callable, scratch dictionary and weak-reference binding. Invoke the
template body directly with the live provides mapping, keeping active ownership
capture, result conversion, physical wrapping, error boundaries and outlet hooks.
Skip SlotData/SlotContext construction only for exact ordinary data inputs when
the selected template callable cannot read them. Preserve fresh render/context
construction and the body execution itself. Custom functions, fallback/data-aware
fills, changed helper methods or unsupported input shapes use the original path.

The omission needs explicit falsification: custom Slot constructors/call methods,
content replacement, ownership callbacks and record constructors can expose the
fallback or alter the chosen fill after initial eligibility. The prototype must
not claim broad compatibility from output equality alone. In particular, public
fallback-aware Python callbacks must keep receiving a real mutable Slot. Any
missing guard discovered during qualification remains a recorded failure.

## Measurement decision

Compare full HTML and four canonical ownership snapshots in fresh processes and
run the existing 625-test rendering/ownership selection. Count omitted fallbacks
and direct calls outside timing. Test fallback access and callback replacement
boundaries before considering adoption. Cython and ABI work remain parked; no
production sources or native binaries change for this experiment.

If the fixture checks support measurement, retain eight balanced randomized
fresh-process pairs, six initial and 80 warm renders each, ordinary GC and all
samples. No other tests/builds overlap timing. Require seven joint wall/CPU wins
and a median paired reduction of at least 1 ms in process mean warm time to
justify the new execution path. Keep second renders separate. A timing pass
requires broader qualification; it cannot erase a known compatibility failure.
A failed screen rejects this representation without another guard expansion.

## Boundary checks before main timing

The retained contracts probe reproduces two failures. Replacing the selected
slot's content while constructing the supply-selection record makes the
reference invoke the new callable with its fallback, while the candidate raises
AttributeError. A callable that compares equal to the original template-render
helper defeats the tuple-equality checks: reference calls it, candidate skips it.
Ordinary template fills and a Python callback that renders its fallback match.

These failures block adoption. The main eight-pair run is diagnostic: determine
whether the unchanged benchmark fixture saves enough time to justify repairing
the execution path. A failed performance screen ends this prototype without
adding more guards. The 625 selected tests pass but do not cover these failures.
Other review findings (constructor and normalization-helper rebinding, and
resuming a retained SlotNode context outside active capture) remain untested.

## Decision correction after the user's threshold question

The 1 ms requirement above was declared before timing and the measured candidate
missed it. That historical fact remains recorded. It was too strict a default
for this Python-only candidate: the change adds no compiler, binary, ABI target
or packaging step. The broader research mode does not itself justify a higher
minimum saving. The user challenged the threshold after the result was reported.

Under the earlier 0.25 ms and seven-joint-win screen, the measured 0.370244 ms
saving with seven joint wins supports repairing and qualifying this candidate.
This is an explicit reassessment after measurement, not a pass of its original
predeclared screen. Both reproduced compatibility failures still block adoption.
The repaired candidate must be measured again because its runtime costs can
change. Keep the original plan bytes in plan.md.measured.txt and the earlier
prescreen archive for their respective report hashes.
