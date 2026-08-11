# Toast maintainer notes

Runtime implementation: [`ctoast.py`](ctoast.py).

Before changing the public contract, update the
[`Toast specification`](../../../../../../docs/design/ui_components/toast.md).
Follow the package
[`component policy`](../../../docs/component-authoring.md). The public guide is
[`api.md`](api.md), and its structured reference is [`api.yml`](api.yml).

Keep these runtime invariants together:

- one persistent Region owns the visible queue, stable polite/assertive
  announcers, timers, F6 focus access, and modal pause;
- message content is plain data, never executable markup or a slot renderer;
- a dismissed ID stays suppressed until its producer removes that ID;
- queued messages receive neither a timer nor an announcement before they are
  promoted into the visible limit; and
- retained component roots preserve remaining lifetime, focus identity, and
  announcement episodes without letting obsolete tasks survive cleanup.

Public examples live in [`snippets/`](snippets/). Focused runtime tests live in
[`tests/e2e/`](tests/e2e/), and the reusable quality state lives in
[`quality/scenario.py`](quality/scenario.py). These repository-only files are
excluded from the wheel.
