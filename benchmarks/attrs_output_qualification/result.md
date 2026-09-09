# Packaged compact attribute keys did not pass qualification

The standalone prototype passed its screen, but the ordinary packaged
implementation did not reproduce that gain. Three of eight process pairs
improved both clocks; median paired mean savings were -0.035789 ms wall and
-0.016650 ms CPU. The Python fallback also exceeded its 0.10 ms regression
limit, at -0.170350 ms wall and -0.170631 ms CPU. The tiny native comparison
passed its non-regression margin, with 0.004923 ms wall saving and six joint
wins. Keep all three results; the tiny result does not justify adopting a
candidate that failed the other required comparisons.

All 19 repository phases passed, coverage was 88.74%, browser tests passed
553 cases, and Linux-target mypy checked 536 files. These checks establish
behavior for the archived candidate. They do not turn failed performance
qualification into a performance improvement.

A subsequent diagnostic counted 495 cache hits, no misses and no miss-path
string casts in one warm fixture render. It compared the standalone and
packaged native key functions on those same 495 maps in alternating batches.
Their median difference was about 0.00023 ms per set of maps, with the packaged
function slightly faster. That isolated result does not explain the differing
whole-render outcomes. It excludes cache lookup, formatting, root rendering
and process-to-process heap variation. The cause of the discrepancy remains
unisolated, and no whole-render comparison was rerun to seek a passing result.

## Reproduce the rejected implementation

`candidate.patch` contains all proposed production, test, stub and pointer
changes against the source at `4d5db99`. The regular runtime is restored after
this rejection. Apply the patch only in a separate checkout where its context
matches; use `git apply --check` first. Then build the extension from
`packages/py/citry_core` with the worktree's maturin:

```sh
../../../.venv/bin/maturin develop \
  --profile release-wheel --features abi3-py310
```

Run `benchmarks/attrs_output_qualification/probe.py` from the worktree root
with its Python. The recorded large, tiny and fallback seeds are 20261005,
20261006 and 20261007, respectively. All use eight pairs and 80 measured
renders after six initial renders. The tiny case uses `--size sm`; the Python
fallback uses environment variable `CITRY_ATTRS_OUTPUT_PYTHON=1`. Supply a new
`--output` path so the original results remain intact.

The runner requires the applied candidate and rebuilt extension. Its reference
is the archived original formatter, compiled against live module globals.
Both variants load the same artifact. The reports' `experiment_only: false`
means ordinary candidate source was timed; it does not mean the candidate was
adopted. `diagnose.py` additionally requires the
standalone extension built by `native_attrs_output_probe`; it is a diagnostic,
not the adoption benchmark. Timing reports retain exact source/artifact hashes.
To verify those production hashes after restoration, apply the archived patch
in a separate checkout or compare reconstructed files without changing runtime.

The measured candidate artifact has SHA-256
`71f278f655855eb1b4d5d03383233c4f24442ed705f430e12b9b1a74e5d6f859`.
The qualified runtime's restored artifact has SHA-256
`321af83391e96c3770513de105b53f51e0cb2af60ea254857faa85b8fc9f71c7`.
Binaries are local build artifacts; the patch, source, lockfile and reports
are the durable evidence. The source restoration adds no user release note.
