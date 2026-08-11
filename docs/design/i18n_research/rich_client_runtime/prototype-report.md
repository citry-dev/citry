# Rich messages in Citry's current browser runtime

**Status:** Bounded exploration passed. A later exploration resolves its
caller-scope conclusion for equal-count switches.

## What this checked

The earlier rich-message browser exploration used a small research range
manager. This exploration used Citry's current ownership graph, real component
ranges, supplied Slots, Events fragments, retained components, and Alpine
teleports.

It ran four checks in Chromium, Firefox, and WebKit:

1. Move three already-rendered keyed Slot occurrences in the browser.
2. Use a server Events fragment to add a fourth occurrence, then remove it.
3. Put an original caller-owned Slot behind a keyed child component.
4. Run Citry's existing tests for ordinary supplied Slots, teleports, repeated
   slot mirrors, and rejection of native component cloning.

## What worked

Citry can move an already-rendered keyed component range in one browser task.
All three browsers kept the same DOM nodes and logical component records. Input
values, focus, text selection, retained component state, teleport placement,
and teleport-local state survived. No cleanup ran. A failed preflight left the
page unchanged.

This is useful, but the probe had to read Citry's private ownership records and
move their comment-capped ranges itself. The current public browser runtime has
no checked operation for this move.

The normal Citry behavior also still works. An ordinary supplied Slot keeps its
caller scope, teleported content keeps its placement and event path, and normal
repeated slot mirrors keep one source. Native cloning of a server-rendered
client-active component is correctly rejected in all three browsers.

## What this integration path could not do

The keyed-child integration used by this probe could not combine these two
requirements:

- give each translated Slot occurrence its own stable keyed component range;
- keep the original fill's caller-side Alpine scope.

Passing the lazy Slot into a keyed child component created valid keyed ranges,
but the rendered fill could not see the caller's `owner` value. Forwarding the
same Slot through a normal child `<c-slot>` did render the caller value, but
Citry then rejected the ownership manifest with:

```text
slot region ownership does not match its fill
```

The count-changing server fragment also fell short. It added and removed the
requested occurrence, and the outer occurrence records kept their logical
identity. However, it recreated the surviving nested input components and the
teleported button. DOM identity, focus, teleport-local state, and clean
one-time lifecycle behavior were lost. After the round trip, two ownership
revisions remained instead of returning to one. When focus was inside the
removed occurrence, the generic morph code did not move focus to the locale
provider.

Finally, the browser has no way to call a Python `Slot` to create a brand-new
occurrence. Copying the existing DOM is not a substitute because Citry rightly
rejects cloned client-active components.

## Decision

Repeated rich Slots remain part of the authoring model. A server render may
invoke the same lazy Slot as many times as the selected message needs.

Browser locale switching is narrower for now:

- Citry may reorder only Slot occurrences that already exist and have stable
  keys.
- A client-switchable rich call must use the same occurrence count for each
  named Slot in every selectable locale until Citry has a browser creation
  protocol.
- The keyed-child approach in this exploration is not the production path.
  The follow-up exploration shows that a direct Slot call already creates a
  distinct source-aware region while keeping the original fill's caller scope.
- Count-changing rich switches must use navigation or a later server/browser
  protocol that preserves surviving ranges. The current Events morph is not
  sufficient.

The follow-up
[`source-aware relocation exploration`](../rich_client_relocation/prototype-report.md)
supersedes the first proposed addition: the existing `slotRegion` record is
enough for the equal-count path. The remaining implementation needs are:

1. A checked, atomic operation that relocates a set of existing Slot ranges and
   updates `lang` and `dir` in the same commit.
2. A later browser creation protocol if in-page locale changes must add new
   occurrences. It must create a fresh component instance, not clone DOM.

The locale-switch code must also own focus recovery when it removes the focused
occurrence.

## Evidence and limits

[`evidence.json`](evidence.json) contains equal semantic results for Chromium
151.0.7922.34, Firefox 153.0, and WebKit 26.5. The harness also runs Citry's
existing ownership tests in all three browsers. Normal and optimized Python
reproduction commands are in
[`prototype-environment.md`](prototype-environment.md).

This exploration does not cover provider inheritance, stale locale generations,
catalog chunk loading, cache variation, or a browser component blueprint.
