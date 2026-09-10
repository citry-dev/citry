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
