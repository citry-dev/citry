# wrapt contribution draft

Status: prepared for review on 2026-09-11; not posted.

Recommended destination: a focused follow-up comment on the closed
[wrapt #174](https://github.com/GrahamDumpleton/wrapt/issues/174), which describes
the same scalar-metadata use case. The body below can serve as that contribution.
The title is supplied if maintainers prefer a separate documentation/guidance issue.
Do not file another bug asserting that `ObjectProxy` can override Python's current
identity operator. [#244](https://github.com/GrahamDumpleton/wrapt/issues/244) is a
separate possible destination for discussion specifically about result propagation.

## Title

Scalar metadata proxies: identity limits, builtin compatibility, and possible upstream support

## Body

We encountered the same use case described in [#174](https://github.com/GrahamDumpleton/wrapt/issues/174):
carrying metadata with scalar values while application developers use them without
knowing they are proxies. I would like to contribute a concrete production case
and ask whether additional guidance or future upstream support would be useful.

In [Citry](https://github.com/citry-dev/citry), a component framework, `Const(value)`
uses an `ObjectProxy` subclass to mark inputs that remain constant across renders.
We wanted ordinary callbacks to use those values normally, optionally inspect the
marker, and forward the original proxy in their returned template data so the
renderer could keep its precomputation information.

### Reproduction without Citry

The following behavior was reproduced with CPython 3.14.3 and wrapt 2.2.2:

```python
import os
import re
from wrapt import ObjectProxy

flag = ObjectProxy(True)
missing = ObjectProxy(None)
text = ObjectProxy("span")

assert bool(flag)
assert isinstance(text, str)
assert str(text) == "span"
assert (flag is True) is False
assert (missing is None) is False

for consume in (
    lambda: re.fullmatch(r"[a-z]+", text),
    lambda: "".join([text]),
    lambda: os.fspath(text),
):
    try:
        print(consume())
    except TypeError as error:
        print(type(error).__name__, error)
```

All three consumers raise `TypeError`. Running the same consumers on the
underlying string succeeds. `BaseObjectProxy` and `AutoObjectProxy` also reproduce
these particular failures in that environment.

The identity case silently selected the wrong CSS class in a component using
`if fluid is True`; `is None` checks were affected too. String proxies also
reached path lookup and validation libraries. [Citry #107](https://github.com/citry-dev/citry/issues/107)
has the reports.

### What we understand and what we are asking

We understand that Python's `is` has no overload hook and that wrapt alone cannot
change that. We also read [#296](https://github.com/GrahamDumpleton/wrapt/issues/296)
and the [proxy documentation](https://wrapt.readthedocs.io/en/latest/wrappers.html#special-object-methods):
choosing `BaseObjectProxy`, `AutoObjectProxy`, or a custom protocol method can
address some differences, but does not provide arbitrary identity or builtin
compatibility. A custom `__fspath__` can address path conversion separately; it
does not repair `is`, regex matching, or string joining. The
[2.3.0 release notes](https://wrapt.readthedocs.io/en/latest/changes.html#version-2-3-0)
also describe conditional `AutoObjectProxy` support when the target implements
`__fspath__`. That covers path-like targets; a plain string does not define that
method. Our reproduction above is specifically from 2.2.2.

Could the documentation collect these distinctions in a small compatibility
table, particularly warning that successful `isinstance` and equality checks do
not establish transparency to ordinary consumers? Is there a recommended approach
for metadata-bearing scalar proxies beyond unwrapping before arbitrary user code
and keeping metadata separately?

We are preparing a Python Ideas proposal referencing the closed
[CPython #36120](https://github.com/python/cpython/issues/36120), which proposed an
`is` hook and received compatibility and performance objections. If Python ever
adopts a suitable proxy protocol, would support in wrapt be a useful follow-up?
We are not asking wrapt to implement an unsupported `__is__` today.

### Workaround and impact

We now unwrap fields whose outer value is `Const(...)` before component code
runs and maintain metadata separately. Those marked roots are deeply cleaned;
ordinary containers with manually nested markers remain unchanged. We recover
constness for final template fields with the same name and object identity as
the normalized marked inputs. This fixes the reported application behavior,
but adds bookkeeping and cannot retain every arbitrary forwarding path
automatically.

After optimization, our large benchmark ends at 37.40 ms / 28.18 ms warm render
time, compared with 33.77 ms / 24.62 ms in the historical recorded release,
or **10.7% / 14.4% longer** for its ordinary / simple-component variants. This is
an application-level historical comparison, not a wrapt microbenchmark. It does
not isolate the cost of normalization, metadata handling, or identity checks.
[Citry #124](https://github.com/citry-dev/citry/issues/124)
tracks the future restoration of proxy forwarding and the measurement context.

We also found [#244](https://github.com/GrahamDumpleton/wrapt/issues/244). Our
immediate goal was forwarding the same marked value, not wrapping every method
result. Any propagation through arithmetic or item access would need separate
rules about which results are actually constant and which protocols permit a
proxy result. We would be happy to contribute that narrower use case there if it
would help.
