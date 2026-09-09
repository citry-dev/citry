# Keep child references until the final HTML join

## Prior art

`packages/py/citry/citry/serialize.py::serialize_render_result` first builds
frames with text segments and child placeholders. Its second pass joins every
frame into a string, inserting already finished child strings. Deeply nested
output can therefore copy the same text repeatedly. The shared discussion at
https://chatgpt.com/share/6aa06f46-2524-83eb-84a8-08d280d94087 proposed retaining
symbolic chunks until assembly finishes. The discussion supplied no measurement of this suggestion.

The existing serializer already uses iterative traversal and preserves marker
inheritance, ownership caps, extension insertion points and whole-page security
checks. `test_markers.py`, `test_serialize_security.py` and
`test_ownership_manifest.py` cover those contracts. No parser, compiler, native
binding or public type changes are needed for this experiment.

## Experiment and decision

Keep the current bottom-up frame order and lookup rule, but store lists of text
and references to previously built lists. Flatten the root iteratively and join
once before whole-page hooks. An unknown or not-yet-built placeholder keeps its
literal text. Looking up arbitrary frames during a top-down walk could change
that behavior or introduce cycles, so do not use that alternative. Keep a
single-segment leaf as its original string to avoid a redundant list.

First record untimed assembly volume and compare representative synthetic deep,
wide, empty and unresolved-placeholder frames. Then use two runs of 60
alternating complete large render pairs, with deterministic IDs, complete HTML
equality and ownership snapshot equality. Adopt only if both runs save at least
0.15 ms by the median paired difference and improve at least 40 pairs. Stop a
clearly losing first run rather than repeating it. Python traversal may cost
more than the avoided C string copies; a deep synthetic win alone does not
justify a production change.

This is an opt-in benchmark outside ordinary CI. It reuses the existing large
scenario and native artifact, takes seconds and adds no release gate. If it
qualifies, run focused serializer/security/ownership tests and add boundary
regressions for authored placeholders and deeply nested output before the final
repository checks. If it fails, retain the experiment and result without
changing the runtime.

## Result and reproduction

Do not adopt this candidate. The large scenario's reference median was
31.414 ms and its candidate median was 31.441 ms. The median paired saving
was 0.023 ms, with 36 of 60 pairs improving. It fails the stated threshold;
no confirmation run is warranted. All four ownership snapshots and all timed
HTML pairs matched. Five synthetic cases also matched, including forward and
self references that must retain literal placeholder text.

The synthetic deep chain with a 100,000-character leaf improved from 1.195 ms
to 0.154 ms for assembly alone. This establishes a useful case for the
representation, but does not qualify it for the default Citry benchmark.
The six real serialization calls contained 325 frames and produced 327,312
characters at their roots before hooks. Frames with placeholders
accounted for 2,090,273 joined-output characters. These are character lengths,
not measured bytes copied or allocation traffic. Hooks subsequently change
the output; the final benchmark HTML contains 1,013,746 bytes.

Run the opt-in comparison from this checkout:

```bash
.venv/bin/python benchmarks/serialization_assembly_probe/probe.py \
  --output /tmp/assembly-symbolic.json
```

The retained report is `benchmarks/results/repeat-render/assembly-symbolic.json`.
No production serializer source changed and no new ordinary-CI test was added.
The equality checks qualify the experiment's measured cases, not every
possible extension or custom string subtype. A future adaptive or native
implementation would need its own complete-render comparison and boundary
qualification.
