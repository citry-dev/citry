# Locate remaining public simple work

Run each variant in its own process:

```sh
.venv/bin/python benchmarks/simple_api_probe/diagnosis.py simple \
  --output /tmp/simple-diagnosis.json
.venv/bin/python benchmarks/simple_api_probe/diagnosis.py ordinary \
  --output /tmp/ordinary-diagnosis.json
```

The script uses the same scenario loader as the public-API timing comparison.
After six initial renders it profiles twenty renders with cProfile and retains
every function row, including self time, cumulative time and call counts. It then
observes constructor calls in one separate render and times component preparation
and finalization across ten further renders. Every observed output must equal the
last initial output within its variant. IDs are reset to the same values on every
diagnostic render; the balanced timing benchmark varies IDs instead.

The constructor observer counts only the most-derived Python initializer for
each render object, so a subclass calling its superclass is counted once. Identity
frames, which hold immutable render identity metadata, are reported separately
from render objects. The component timers subtract
nested measured intervals, but their setup and cleanup overhead can remain in an
enclosing timer. They include ordinary work executed inside each interval,
including supplied content, and omit scheduler and serialization work outside
those intervals. They do not partition the complete page cost or predict savings.

The slot inventory records keys in the element's `slots` mapping at component
preparation. Simple tag bodies travel separately, so an empty mapping does not
mean that a simple call supplied no content. The declaration inventory reads the
authored Python class bodies and effective asset declarations. It identifies
classes worth reviewing; it does not prove inheritance, configuration, template
or call compatibility with simple mode.

The script checks source and native artifact hashes before and after observation.
Profile overhead changes the reported times, so use the ordinary/simple counts
and relative function weights to choose experiments. Use the separate balanced
benchmark to decide whether an implementation saves rendering time.
