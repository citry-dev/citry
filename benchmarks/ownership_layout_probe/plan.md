# Give the ownership collector native field offsets

## Prior art

`OwnershipGraph.__init__` in `packages/py/citry/citry/ownership.py:659` creates
the collector's counters, row tables, indexes and source-site cache. Iteration
44 compiled the entire module while retaining an ordinary Python class, saving
0.445 ms and missing the 1 ms requirement for a new distribution path.
Iterations 45 and 46 changed source-row storage and readers but did not pass
the timing and compatibility screens. Those experiments leave repeated field
access throughout capture as an unmeasured group of operations.

The [Cython pure Python guide](https://docs.cython.org/en/latest/src/tutorial/pure.html)
documents `@cython.cclass` and public object field declarations; its
[extension type guide](https://docs.cython.org/en/latest/src/userguide/extension_types.html)
describes native layouts, dynamic dictionaries, weak references and subclassing.
This experiment tests that layout across the existing collector methods.
It does not add parser, compiler, Rust binding or public production contracts.

## Design and alternatives

Compile a temporary copy of the whole ownership module, declaring the fields
assigned by `OwnershipGraph.__init__` as public Python-object fields on a Cython
extension class. Keep a dynamic `__dict__` and weak-reference support. Counters
remain arbitrary-precision Python objects, tables keep their current contents,
and callbacks retain their existing positions in the method source. Record
both original and transformed source hashes and the declared fields.

Use iteration 44's isolated compiler tools and directives, with a separate build
directory and report. Import the compiled module under its real package name
before any Citry import. Production source and the regular native binary stay
unchanged. Compiling the ordinary class again would repeat iteration 44;
writing many individual Rust field helpers would introduce additional calls
without testing this larger group of accesses.

Fixed fields can bypass Python descriptors, change `vars(graph)`, limit class
mutation and alter uninitialized-field behavior. A successful render cannot
qualify these differences. First build/import and run a minimal render; inspect
any concrete compiler or runtime failure before adapting the probe. The built
class rejects class mutation, and its scope constructor bypasses a replacement
class in module globals. The untimed observer therefore wraps the existing
render scope and attaches snapshot/source methods to each actual graph instance;
timed workers use the original scope and methods. Retain counterexamples
for class overrides, instance overrides, subclass descriptors and field access.

## Decision and verification

The predeclared performance screen is seven of eight joint wall/CPU wins and
at least 1 ms median paired reduction in process mean wall time. Workers retain
six initial renders and 80 warm renders, normal GC and all observations;
the actual second render is reported separately. No tests or builds overlap
timing. Before the main run, compare complete HTML and all four canonical
snapshots and verify the native class layout and module path. Run the existing
ownership checks and preserve failures as experiment limitations.

Failing the screen ends this candidate. Passing supports further compatibility
work, not shipping Cython: descriptor and callback behavior, introspection,
replay, GC, interpreter/platform support and packaging still need qualification.
If the build or ordinary render fails, retain that failure and its cause;
there is no speed claim without an active candidate.
