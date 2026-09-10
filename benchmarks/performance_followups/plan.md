# Four bounded performance experiments

Only the four avenues recorded in the research log are authorized for this
follow-up. Keep all probes and results on the research branch. Do not merge
these files into main or resume Cython/ABI work.

## 1. Remaining presentation declarations

The candidate opts the twelve qualifying declarations into the existing public
simple API. ListComponent is excluded because its named `empty` slot outlet violates that
API; an empty default slot outlet is supported. Convert only authored data callbacks that do not reference their instance
to static methods. Do not alter runtime methods or remove data callbacks.

The control already opts Button, Icon and HeroIcon into simple, as in the released
optimized benchmark. The candidate adds MenuList, Table, Breadcrumbs, TabsStatic,
ProjectStatusUpdates, ProjectOutputBadge, ProjectOutputs, ProjectOutputsSummary,
ProjectInfo, ProjectNotes, Navbar and ProjectPage. A simple ProjectPage adds the
documented transparent root owner. Expect exactly one additional TemplateRoot
call and unchanged counts for all other component calls and all 34 authored data
methods (325 calls). Generated identities fall from 146 to 116. Simple intentionally changes
independent identity and hook semantics; content equivalence does not erase that
public API difference.

Run all six permutations of control, candidate and the existing Django fixture
in separate processes. Shuffle the six orders with fixed seed 20260910, and use
the same explicit PYTHONHASHSEED for all three workers within each block. Each process performs six initial renders and 80 warmed
renders, with normal garbage collection and every timed output retained until
timing ends. Report the actual second render separately from warmed renders.
Vary fixed-width Citry IDs on every render. Check every timed Citry result with
the established application-content projection and manifest validation after
timing. Require the expected number of manifests and records in every graph;
require all four untimed ownership snapshot count vectors to match qualification. Observe full ownership snapshots and callback counts outside timing.
Django generates random CSRF tokens and time-relative text; its raw hashes need
not match between renders. Strict output verification here applies only to Citry.
Django is a timing reference with different output/features, not an equivalent
Citry ownership or event implementation.

Record raw wall/CPU observations, source/native hashes, qualification/plan hashes and activation evidence.
Use process-block mean differences as the six paired observations, with a
Student-t interval (five degrees of freedom). A configuration gain must preserve
the checks above, save wall and CPU time in all six blocks, and have both paired
95% intervals above zero. There is no arbitrary 1 ms floor: this proposal adds
no runtime implementation or build complexity. A smaller reproducible saving
can still justify opting appropriate declarations into the existing API.

The native baseline is the current local build, SHA-256
`a4f2430612277e22e99a657f43902feb8198a6cec471eb01180e811a791c9500`.
Both Citry variants use these exact bytes. Do not compare its absolute times
directly with the older retained native build's historical measurements.

Post-measurement editorial note: the named-slot clarification above was added
after measurement during independent review. The report retains the hash of the
method text used for measurement; this clarification changes no procedure.

## 2. Dynamic HTML without a component and slot outlet

Prior art: `components/dynamic.py` computes validated opening/closing strings
around one default slot; `ComponentNode.render` records an invocation, collects
slots and queues that built-in. Static tag choices already compile to literal
HTML. `component_dynamic.md` and `test_component_dynamic.py` define ordered
attribute merging, tag validation, void-body errors and attribute hooks.
`_simple_runtime.py` already establishes a caller-owned template contract, but
the built-in's instance callback cannot opt into that API.

The one candidate specializes eligible existing ComponentNode instances when
created, without changing grammar, AST or compiler output. Dynamic tag and
attribute resolution still use current inputs. It reuses the built-in's actual
attribute formatter and the ordinary body walker. Calls with explicit fills or
morph metadata stay on the existing path; programmatic built-in calls also stay
ordinary. No native or ABI work is involved.

This is an experimental contract change: these selected built-in invocations
lose independent identity, component hooks and slot-outlet hooks. Attribute hooks
still receive the authoring component. Body evaluation happens while walking the
caller rather than after scheduling the built-in. Do not promote this as a
transparent implementation optimization. Plain HTML node semantics are the
proposed contract; general component semantics are the control.

Qualification must preserve projected application content, valid manifests and
all authored callback counts, with only DynamicElement component calls removed.
Check dynamic tag changes, escaping and void rejection directly. A whole-page
failure rejects this candidate before timing. If qualification passes, use six
balanced paired fresh-process blocks with matched hash seeds, 80 warmed renders,
retained outputs and wall/CPU intervals. There is no build-complexity floor, but
any saving must be reported alongside the explicit contract costs. No fallback
variation or second candidate will be tried in this avenue.

Additional contract difference found during review: a non-void element's whitespace-only body is
preserved as ordinary HTML content; the existing component slot collector drops
it. This is observable output, not just an ownership change. Nested dynamic
elements also use Python body recursion. Both control and candidate passed depths
20, 40 and 60; both hit the existing generated-Python nesting limit at depth100.
This checks the tested envelope, not unbounded recursion safety or equivalent
behavior under a lower user-selected recursion limit.

Post-measurement wording clarification from independent review: attribute hooks,
not just child-body expressions, execute earlier while walking the caller. The
recorded method hash identifies the text frozen for measurement. No measurement
procedure or prototype implementation changed after the run.

The exact text used for attempt2 is retained as `dynamic-method-measured.md`
beside its timing report, including the wording before review clarifications.
