# Avoid repeated protocol inspection for exact strings and render objects

`_render_value()` spends about 1.095 instrumented ms across expressions and
slot callbacks in the large scenario. An untimed type count at those two
aliases after Const
unwrapping found 274 exact CitryRender values, 79 exact strings and 30 Markup
values. Python's runtime protocol check searches instance attributes even
after a negative class check. Exact strings cannot gain instance attributes;
exact CitryRender objects have slots and an ordinary object base.

Compare a candidate that skips instance protocol inspection for these two
types. Keep Const unwrapping and Slot dispatch before the shortcut. Check
protocol subclass membership on each call, preserving explicit registration.
For CitryRender, require its original class identity and object base, and no
class-defined protocol member, custom attribute getter or class override.
Capture trusted identities once when the probe imports; check the live
CitryElement, CitryRender and PhysicalRegionPart aliases so replaced types
cannot change the later element or structural branches. Include `__getattr__`
in the render-class guards for Python 3.10/3.11's dynamic protocol lookup.
Subclasses, Markup, instance-defined protocol values and
changed render classes retain the original path. Keep escaping live for text.
Do not cache arbitrary negative class/protocol decisions.

First compare complete renders in eight balanced randomized process pairs,
80 samples each after six warmups, with ordinary GC enabled. Require seven
joint wall/CPU wins and at least 0.25 ms median reduction in process mean wall
time before proposing production adoption. Match every HTML digest and native
artifact; check all reached ownership snapshots separately. Prototype guards
and branch counts must be exercised outside timing. Retain all pairs.

Falsifiers include changing output types, escaping, Const behavior, component
resolution count, protocol registration, subclass or instance-defined methods,
changed class members/bases, replaced runtime aliases and callback errors.
Private edits to protocol implementation/metadata need separate qualification;
this experiment does not silently assume every arbitrary monkeypatch is safe.
No grammar, compiler, AST or native surface changes are involved. Only after
complete-render evidence and independent review should production code change.
