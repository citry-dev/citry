# Measure slot preparation and direct record export together

The slot-preparation and direct-export experiments each showed a positive median
saving in process mean render time against the existing native backend, but each reaches only six of eight
joint wall/CPU wins. Slot preparation also changes which records are exported,
so adding the separate measured savings would not establish a combined benefit.
This comparison installs both existing operations together. It adds no native
surface or production source changes; grouped fill binding remains disabled.

Prior art and qualification are in `native_slot_region_probe/plan.md` and
`native_record_export_probe/plan.md`, their adapters/contracts and research
iterations twenty-eight and twenty-nine. Compose the native graph initializer
that configures tuple construction with the slot capture method that prepares
regions. Both use the same existing storage backend and replay fallback. Every
prototype limitation from the two parent plans remains in force.

Before timing, rerun the slot callback/replay cases and ownership, manifest and
cache-replay suites with the composition installed. Count all six direct-export
families outside timing and require 2,828 calls: 304 fewer than direct export
without slot preparation. This verifies the expected combined activation; it
does not establish its timing. Compare every reached snapshot and full HTML.

Use eight balanced randomized fresh-process pairs, six warmups and 80 complete
renders per worker with normal GC and no excluded samples. The reference uses
the existing native backend; both variants load the same artifact. Require seven
joint wall/CPU wins and at least 0.25 ms median paired mean wall saving. Keep all
required snapshot/export work inside timing. Record the two parent adapters,
combined adapter, harness and native sources/artifacts. No CPU-heavy checks or
builds overlap timing. A passing result supports broader qualification and a
new production-reference comparison, not adding historical gains or adopting
the experimental backend as a shipping replacement.

The incremental comparison passed with eight joint wins and 0.569 ms median
paired mean wall saving. `production_probe.py` now applies the same process
method against production ownership, with candidate activation only in the
native workers. Use a new balanced order seed, retain the same artifact and all
samples, and compare snapshots against production directly. This measures the
whole current combination rather than adding prior savings. Compatibility
qualification still follows separately.
