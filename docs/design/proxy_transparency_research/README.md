# Proxy transparency: upstream research and review drafts

Prepared on 2026-09-11 after the fix for Citry #107. The upstream texts are
drafts for review and have not been posted.

- [Python title and body](python.md): propose an Ideas discussion that revisits
  the existing, closed request for an identity hook.
- [wrapt title and body](wrapt.md): contribute the Citry case to the existing
  scalar-proxy discussion; use the title only if a separate issue is preferred.
- Citry's [future proxy restoration issue](https://github.com/citry-dev/citry/issues/124)
  remains the tracker for restoring proxy forwarding into component methods.

## Search scope and findings

Searched the CPython and wrapt issue trackers, Python Discussions, and indexed
Python mailing-list archives for identity hooks, `__is__`, transparent proxies,
wrapped `None`, and builtin consumers of proxies. Read the relevant issue bodies
and maintainer comments. This is a targeted search, not a claim that no other
discussion exists. wrapt's GitHub Discussions feature is disabled; its issue
tracker contains the direct prior reports.

| Prior discussion | Status checked on 2026-09-11 | Relevance and suggested treatment |
|---|---|---|
| [CPython #36120: hook method for `is`](https://github.com/python/cpython/issues/36120) | Opened 2002-02-18; closed 2013-05-07 | Direct predecessor to the proposed `__is__` hook. The discussion identifies copying, graph traversal, backwards compatibility, and identity-test cost as problems. Cite it in a new Ideas discussion with the Citry use case. |
| [Python Ideas: Demoting the `is` operator](https://discuss.python.org/t/demoting-the-is-operator-to-avoid-an-identity-crisis/86) | Started 2018-09-29 | Discusses literal identity misuse and objections to invoking dunder methods. It is related background, not an existing proxy-specific proposal to revive. |
| [CPython #63270: weakref proxy in-place operators](https://github.com/python/cpython/issues/63270) | Open | Graham Dumpleton discusses proxy forwarding when an operation returns its original object. Different scope from identity customization; do not add the `is` proposal there. |
| [CPython #76864: `isinstance` / `__class__`](https://github.com/python/cpython/issues/76864) | Open | Related implicit-hook and type-observation behavior, not the identity proposal. |
| [wrapt #174: Wrapping basic types](https://github.com/GrahamDumpleton/wrapt/issues/174) | Closed 2021-08-04 | Direct match: storing metadata on scalar proxies, then having `str.join` and regex reject them. The maintainer explains the builtin-consumer constraint. Prefer a focused contribution here over a duplicate bug. |
| [wrapt #244: Sticky/Viral ObjectProxy](https://github.com/GrahamDumpleton/wrapt/issues/244) | Closed 2026-04-13 | Discusses propagating annotations through results and explicitly mentions avoiding wrapped `None`. The closing comment invites concrete use cases but explains that generic result wrapping conflicts with required return types. Relevant if pursuing result propagation separately. |
| [wrapt #296: Improve ObjectProxy](https://github.com/GrahamDumpleton/wrapt/issues/296) | Closed 2026-01-15 | Explains protocol choices, selective support, and custom proxy methods. Its closing comment directs concrete remaining requests to focused new issues. |
| [wrapt #103: Proxies lose proxy-ness inside wrapped methods](https://github.com/GrahamDumpleton/wrapt/issues/103) | Closed | Explains that a wrapped method's `self` is the target. This is a different limitation from retaining a marker when forwarding an unchanged value. |

Python's [developer communication guide](https://devguide.python.org/developer-workflow/communication-channels/#discuss-python-org)
identifies Ideas as the place for new feature discussions. The proposed hook
would change the current [identity-comparison contract](https://docs.python.org/3/reference/expressions.html#is-not).
An opt-in wrapper does not make that change automatically backwards compatible
for code receiving it.

wrapt's [proxy documentation](https://wrapt.readthedocs.io/en/latest/wrappers.html#special-object-methods)
explains `BaseObjectProxy`, `AutoObjectProxy`, and selective special-method
support. These address particular protocol gaps; they do not change Python's
identity operator. The proposed wrapt text asks for guidance and conditional
future support, rather than a library-only implementation of `is` dispatch.

## Local reproduction

The small examples in the drafts were checked with CPython 3.14.3 and wrapt
2.2.2. `ObjectProxy`, `BaseObjectProxy`, and `AutoObjectProxy` all reproduce the
identity, regex, string-joining, and wrapped-string `os.fspath` failures in this
environment. These are version-specific observations, not a claim that every
listed protocol failure is unavoidable or remains identical in newer releases.
The [2.3.0 release notes](https://wrapt.readthedocs.io/en/latest/changes.html#version-2-3-0)
add conditional `AutoObjectProxy.__fspath__` support for targets that implement
that protocol. This concerns path-like targets; ordinary strings do not define
`__fspath__`.

## Benchmark context

The final ordinary-value implementation has root-only deep unwrapping,
same-key/object-identity const recovery, and the subsequent bookkeeping
optimization. Warm-render times were:

| Variant | Historical release | Saved implementation before bookkeeping optimization | Final implementation |
|---|---:|---:|---:|
| Ordinary | 33.7709479375 ms | 39.86388850625 ms | 37.39555205 ms |
| Simple | 24.62381614375 ms | 29.5939978875 ms | 28.17882863125 ms |

The final result is 10.7% / 14.4% longer than the historical recorded release.
The matched before/after bookkeeping comparison is a 6.2% / 4.8% reduction.
These are different comparisons. Neither isolates the cost of the `is` operator
or predicts the performance of an upstream proxy protocol.

The historical record is
`benchmarks/results/publication-20260910-release-0.5.0.json`.
The final report in this workspace session is
`/tmp/citry-107-publication-bookkeeping-vs-root-only.json`.
It used ten fresh-process blocks per source/variant, six initial renders and
80 warm renders per worker, retaining outputs with normal garbage collection.
Application projections matched, browser manifests validated, and all 361
benchmark input hashes remained unchanged. The simple variant enables the
simple-component path for three selected classes in the same large scenario.

## Changelog

The existing `Unreleased` entry in the root `CHANGELOG.md` already records the
ordinary-value fix, same-key/object-identity recovery, and the treatment of
manually nested markers. No duplicate release note is needed.
