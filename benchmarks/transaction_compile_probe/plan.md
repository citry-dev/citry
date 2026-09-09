# Component transaction compilation experiment

## Prior art

`docs/design/performance.md` sections 6.9, 6.10, 10.9 and 10.10 record neutral
body-walker, generated-body and native-scalar experiments. Section 10.9 calls
wholesale Cython compilation a weaker option but records no measurement.
`component_render.py:_render_one` has the largest individual Python self time
in `round5-profile.json`. Component construction and input resolution are
smaller related transactions. The render-task records already use NamedTuple.

## Chosen design and falsifiers

Extract the existing source for `_render_one`, `Component.__init__`,
`ComponentMeta._create_instance` and `ComponentNode._resolve_inputs`. Compile
them into separate Cython modules with `annotation_typing=False`,
`infer_types=False`, `binding=True` and Python 3 language semantics. Disabling
annotation-based typing avoids introducing native type restrictions from the
runtime's existing annotations. These directives are described in the
[Cython compilation guide](https://docs.cython.org/en/latest/src/userguide/source_files_and_compilation.html).

Keep original helper and record objects through imports. Refresh the imported
globals before each untimed switch. Compiled method dispatch, object allocation,
callbacks and helper calls remain inside the complete-render timer. Compare
individual areas and the combined candidate against the original Python
functions, with alternating pairs and exact HTML and ownership snapshots.
An additional untimed render counts each selected compiled method's calls.

A smaller pure-Python refactor avoids another native build system but cannot
remove interpreter dispatch from the complete transaction. Compiling the whole
runtime may remove more crossings, but also changes more types, imports and
callback boundaries. This bounded experiment tests the transaction functions
first. Reject production adoption if the measured gain is small relative to
that build and compatibility cost, or if callbacks, errors, snapshots or HTML
change. Successful benchmark equivalence alone does not qualify every callback
or error path.

The functions are renamed `native_candidate`; their module, qualified name,
source locations and traceback metadata are not preserved. A module global
rebound during a render is not refreshed until the next switch. Introspection,
traceback shape and live global rebinding are therefore unqualified. This is
a CPython/version-specific experiment, not an `abi3`, PyPy or browser-wheel
implementation. No production dependency, compiler format or runtime is changed.

## Reproduce

From the optimization worktree, install the two experiment-only build tools
outside its environment:

```bash
uv pip install --python .venv/bin/python --target /tmp/citry-cython-build \
  Cython==3.3.0 setuptools==84.0.0
.venv/bin/python benchmarks/transaction_compile_probe/probe.py \
  --build --build-root /tmp/citry-transaction-compiled \
  --tool-root /tmp/citry-cython-build --case all --pairs 60 \
  --output /tmp/transaction-all.json
```

Run each case in a fresh Python process. Rebuilding or loading after a
`transaction_*` module has already been imported can reuse cached module code
while checking newer on-disk bytes; that use is outside this harness contract.
Omit `--build` to reuse the artifacts from a fresh process. Cases `render-one`, `construction` and
`inputs` isolate the areas; `construction` includes initialization and the
metaclass factory. The harness checks original function, generated source and
compiled artifact hashes, and requires the loaded extension to come from the
requested build directory. Reports retain build and runtime Python versions,
compiler directives, compiler output and artifact hashes. Build/import costs
and namespace refresh are excluded from the render timer.

## Evidence and decision

Sixty alternating pairs per run produced these observations:

| Candidate | Reference median, ms | Candidate median, ms | Median paired saving, ms | Favorable pairs |
|---|---:|---:|---:|---:|
| All four, initial | 31.947 | 31.376 | 0.487 | 49/60 |
| Construction | 32.140 | 31.998 | 0.091 | 45/60 |
| Render one component | 32.246 | 32.176 | 0.170 | 44/60 |
| Input resolution | 32.776 | 32.537 | 0.049 | 35/60 |
| All four, confirmation | 33.003 | 32.476 | 0.521 | 46/60 |

All runs match the four captured ownership snapshots and every HTML pair,
producing 1,013,746 bytes. The confirmation counts 342 native rendering,
initialization and construction calls each, plus 339 native input resolutions.
It also includes the stronger artifact/source checks added after review.
Earlier fresh-process reports predate those guards. Results are preserved in
`../results/performance-render/transaction-compiled-*.json`.

The combined candidate has a small repeatable benefit on this scenario, but
this does not justify shipping another compiler and native distribution path.
Retain it as research. The experiment does not test full-module compilation,
prove a limit on all native designs, or establish general behavioral equivalence.
A production proposal would need the existing supported Rust/PyO3 distribution
and a separately specified boundary. Current production benchmark and validation
results remain those in the main research log.
