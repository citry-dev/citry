# Rich-message browser exploration

**Status:** Passed as a bounded browser proof on 2026-08-10.

## Question

A translation may use one filled Slot several times and may put those uses in
different positions in each locale. Can the browser switch between those
messages while keeping each rendered occurrence's DOM identity, application
state, focus, cleanup, and language ownership correct?

## Test shape

The English fixture uses `terms_link` twice and `help_link` once. The Arabic
fixture puts `help_link` first and uses `terms_link` three times. One switch
therefore has to move three existing ownership ranges and create a fourth. The
reverse switch removes that fourth range.

Each occurrence has a stable key made from the rich-message instance, Slot
name, and occurrence number. For example:

```text
rich:terms_link:0
rich:terms_link:1
rich:help_link:0
```

The probe represents each occurrence with comment caps, so a Slot may have no
single wrapper and may render several sibling nodes. A switch moves the whole
existing range instead of cloning its DOM. A new occurrence invokes the same
research-side factory again and gets a separate range. A removed occurrence
runs its cleanup once. This factory stands in for creating another Slot
occurrence; it is not a browser call into a Python `Slot`.

The probe also checks these failure paths before touching the DOM:

- a compiled message omits one required Slot;
- a wrapperless Arabic message falls back to English;
- a generated marker collides with catalog or application text.

## Result

The same result passed in Chromium 151, Firefox 153, and WebKit 26.5.

The marker protocol works for repeated Slots. Citry can generate one fresh
marker for each named fill, let Fluent repeat that marker, and turn the result
into separate occurrence keys. The checked fixture changed from these English
keys:

```text
rich:terms_link:0
rich:terms_link:1
rich:help_link:0
```

to these Arabic keys:

```text
rich:help_link:0
rich:terms_link:0
rich:terms_link:1
rich:terms_link:2
```

The first three ranges moved as the same DOM objects. Their input values,
event-listener state, focus, and text selection survived. The third
`terms_link` use invoked the research-side factory again and received its own
DOM range.
When that occurrence disappeared, its cleanup ran once. Focus moved to the
real provider wrapper because the focused control no longer existed. Every
created instance was eventually cleaned exactly once.

The proof also passed rootless and multi-node Slot content. It uses comment
caps around each occurrence, so the protocol does not require a private
host attribute, an extra visible element, or one root element from the filled
Slot.

One identity limit is unavoidable. Several uses of the same `$terms_link`
marker have no author-supplied identity beyond their order. Citry can preserve
`terms_link:0` and `terms_link:1`, but it cannot know that two identical uses
have swapped semantic roles. An author who needs that distinction must declare
two named Slots, such as `$primary_terms_link` and `$secondary_terms_link`.

## Language and direction result

The real `<c-i18n client tag="...">` wrapper can own the active message
language and direction. The probe changed that wrapper from
`lang="en-US" dir="ltr"` to `lang="ar" dir="rtl"` in the same synchronous
commit that moved the rich Slot ranges. A mutation observer and the commit
event saw only the complete new state.

Application-owned Slot nodes kept their own semantics. A Hebrew help button
kept `lang="he" dir="rtl"` as it moved. A Slot with no explicit override
inherited the provider's new language and direction. This gives the design a
plain ownership rule: translated text belongs to the i18n provider; content
inside a Slot belongs to the application and must carry its own `lang` or
`dir` when it differs from that provider.

A wrapperless rich message still cannot label fallback prose with a different
language. The probe rejected an Arabic switch that resolved the rich message
from English before it changed the DOM. This confirms the proposed v1 rule:
wrapperless `<c-trans>` requires equivalent-language coverage. A future API
that permits cross-language rich fallback needs a real metadata-bearing
element or a structured way to mark every translated text run.

## Safety and failure result

- Every resolution generated new 128-bit random markers, with one marker per
  named filled Slot. Repeated uses reused that Slot's marker.
- A forced catalog or scalar collision caused marker generation to retry.
- No marker reached the final DOM.
- Catalog text that looked like `<unsafe>` became an ordinary text node. It
  did not become translator-authored HTML.
- A compiled message that omitted a required Slot failed before any DOM,
  context, state, or cleanup change.
- The tiny 30-switch fixture stayed under the design's 50 ms p95 commit budget
  in each tested engine. This is a smoke gate, not the full catalog benchmark.

## Decision

Keep one fresh marker per named filled Slot and allow the translation to repeat
it any number of times. Give each rendered use the stable key `(rich message
instance, Slot name, occurrence number)`. Move a surviving ownership range,
create a new range for an added occurrence, and clean a removed range once.

Do not add an author-visible rich-message host attribute. The provider's real
wrapper owns active `lang` and `dir`; comment-capped message and Slot ranges own
the internal DOM update. Keep the existing rejection of cross-language
wrapperless rich fallback.

## What this did not prove

The probe uses a small production-shaped range reconciler. It does not yet
connect this protocol to Citry's current ownership manifest, component
lifecycle, Alpine morph, supplied-slot projection, retained ranges, or
teleports. That integration is the next browser-side Phase 0 task.

The follow-up in
[`../rich_client_runtime/prototype-report.md`](../rich_client_runtime/prototype-report.md)
found that the current browser runtime cannot invoke a Python `Slot` for an
added occurrence. It can move existing keyed ranges, but it also needs a new
source-aware occurrence record before those ranges keep the original fill's
caller scope. The production v1 rule therefore requires equal per-Slot counts
for in-page locale switching.

The fixture starts from compiled FTL that already contains `SLOT`. The Rust
compiler exploration separately proved that authored bare `{ $slot }` syntax
generates this private operation.

The probe does not provide a cross-language rich resolver. It deliberately
proves the rejection path. It also does not solve language markup for an
application Slot that has several roots in several languages; those authored
nodes still need their own semantic wrappers or attributes.

The checked evidence and exact reproduction commands are in
[`evidence.json`](evidence.json) and
[`prototype-environment.md`](prototype-environment.md).
