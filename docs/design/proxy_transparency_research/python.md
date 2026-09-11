# Python proposal draft

Status: prepared for review on 2026-09-11; not posted.

Recommended destination: a new [Python Ideas discussion](https://discuss.python.org/c/ideas/6),
referencing the closed [CPython #36120](https://github.com/python/cpython/issues/36120).
That issue already proposed `__is__`; this should be presented as a reconsideration
with a concrete use case, rather than another report of the existing behavior.

## Title

Transparent metadata proxies: revisiting an opt-in hook for `is` / `is not`

## Body

I would like to revisit whether Python could support proxy-aware identity
comparisons, through an opt-in object method such as `__is__` or a more restricted
runtime protocol. The motivation is passing values with framework metadata through
ordinary application callbacks without requiring those callbacks to know about
the wrappers.

I have read the earlier [proposal for an `is` hook](https://github.com/python/cpython/issues/36120).
The compatibility and performance objections there apply here too: code traversing
object graphs or copying objects needs actual identity, and even retaining an
actual-identity fast path before consulting a hook can change existing results.
Opt-in by a proxy class would not make all code receiving that proxy compatible.
This is a language-design question, not a claim that current Python violates its
[identity-comparison specification](https://docs.python.org/3/reference/expressions.html#is-not).

### Concrete failure

In [Citry](https://github.com/citry-dev/citry), a Python component framework, we
mark known-constant template inputs with a proxy based on `wrapt.ObjectProxy`.
That marker lets the renderer precompute stable template expressions and retain
that information when a callback forwards the input. The earlier callback API
let authors inspect that marker explicitly, although ordinary component code
was expected to work without doing so.

For example, a component accepting `True`, a breakpoint string, or `None` might
contain this ordinary Python logic:

```python
def container_class(fluid):
    if fluid is True:
        return "container-fluid"
    if fluid is None:
        return "container"
    return f"container-{fluid}"
```

With CPython 3.14.3 and wrapt 2.2.2:

```python
from wrapt import ObjectProxy

print(container_class(True))               # container-fluid
print(container_class(ObjectProxy(True)))  # container-True
print(container_class(None))               # container
print(container_class(ObjectProxy(None)))  # container-None
```

Equality, truth conversion, and `isinstance` can appear normal while these
branches silently change. A user reported this in [Citry #107](https://github.com/citry-dev/citry/issues/107#issuecomment-5631429948).
Checking a caller-owned sentinel has the same problem. Replacing `is` with `==`
throughout application and third-party code would not preserve identity semantics.

### Current workaround and measurements

We now unwrap fields whose outer value is `Const(...)` before component code
runs and keep constant metadata separately. Those marked roots are deeply
cleaned; ordinary containers with manually nested markers remain unchanged.
For a returned template field, we recover the marker when its name and object
identity match the normalized marked input. Renamed or replaced stable outputs
need an explicit declaration.

After several optimization rounds, the large benchmark's warm render times are
37.40 ms / 28.18 ms for its ordinary / simple-component variants, compared with
33.77 ms / 24.62 ms in the historical recorded release: **10.7% / 14.4% longer**.
These are application-level historical comparisons. They do not isolate the
cost of normalization, metadata handling, or identity checks, and are not a wrapt
benchmark or a prediction of what a Python hook would save. The
[Citry follow-up](https://github.com/citry-dev/citry/issues/124)
records the workaround and measurement context.

### What would need a design

Our desired behavior is that an explicitly opted-in proxy can participate in
`is` and `is not` as its target, including with `True`, `None`, and sentinels,
while remaining inspectable as a wrapper when requested. Would a restricted
runtime protocol for this be worth investigating?

A viable proposal would have to address:

- Actual wrapper identity for copying, graph traversal, debugging, and lifetime
  management, including existing code that already uses `is` for those tasks.
- Symmetry, both operand orders, nested proxies, cycles, and retargetable proxies.
- Consistency with `id()`, `operator.is_()`, singleton pattern matching, and C API
  identity checks. A Python-only method hook would not cover all of these.
- Whether identity tests may run user code, raise exceptions, or become reentrant,
  and the performance effect on ordinary objects that do not opt in.
- How to preserve compatibility for third-party code without requiring it to
  replace every identity test with a new operation.

There are also separate transparency limits: `re.fullmatch()` and `str.join()`
reject wrapped strings, as already discussed in [wrapt #174](https://github.com/GrahamDumpleton/wrapt/issues/174).
An `is` hook alone would not make arbitrary proxies fully interchangeable with
their targets.

Is there an existing proposal beyond #36120 that addresses these constraints?
If changing `is` remains unsuitable, is there a runtime-supported proxy approach
that could preserve existing callback behavior while carrying optional metadata?
