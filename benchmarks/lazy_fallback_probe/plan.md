# Delay unused fallback-slot initialization

One warm large-page render creates 274 template fallback Slots. The candidate
initializes 80 of them on first attribute access. All 274 fallbacks still
record their source occurrence and logical fill. The original factory also
allocates a `_TemplateSlotContent`, a scratch dictionary and a weak reference
from that callable back to each Slot. The candidate avoids those allocations
for the 194 fallbacks that receive no attribute access.

The prior-art search covered `SlotNode.render`, `_make_body_slot`,
`_TemplateSlotContent`, `Slot.__init__`, `Slot.__call__`, and
`OwnershipGraph.record_template_fill` and `capture_slot_call`. The graph
records source and fill rows immediately, then binds the Slot through a weak
dictionary. Those steps do not need the Slot's initialized fields. Calls,
saved fallback values, custom slot functions and ownership snapshots must
continue to work.

The experiment creates a private subclass with the same slot layout as Slot.
Its `contents` field initially holds the arguments needed to initialize a
template fallback. On the first attribute read it changes its class to Slot
and performs the existing field and content-callable initialization. Normal
attribute access therefore has no extra wrapper after initialization.
`Slot.__call__` reaches that initialization when it reads the content callable.
The fallback's ownership row and weak binding are recorded at the original
point, whether or not initialization ever happens.

This representation has limits requiring qualification before adoption.
`type(fallback)` can observe the private subclass before initialization;
`fallback.__class__` initializes it and returns Slot. Constructor overrides
or class changes could alter what delayed initialization does. Python
interpreter support for the class assignment, copy/pickle behavior, weak
references, saved fallbacks, reentrant calls, failure order and replay
rollback need explicit checks. Pre-initialization writes and deletes are
incompatible: an `extra` write is overwritten, a `contents` write corrupts
the pending arguments, and deleting an unset field raises early. Direct
descriptor access can expose the pending tuple. A constructor failure after
the class assignment leaves a partially initialized ordinary Slot. The benchmark alone does not establish production suitability. The factory only changes fallback Slots; named and implicit
fills follow the original factory.

First compare eight balanced randomized fresh-process pairs, with six warmups
and 80 complete renders per worker. Normal GC remains enabled and every sample
is retained. Require seven joint wall/CPU wins and at least 0.25 ms median
process-pair mean wall saving before designing production adoption. Match
every HTML digest and native artifact, and compare all reached ownership
snapshots separately. Untimed counts must show lazy fallback creation and
initialization. A missed screen rejects this candidate as the next production
change, not every possible way to delay slot work.
