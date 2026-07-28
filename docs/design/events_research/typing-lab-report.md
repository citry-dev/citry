# Typing lab: handler-signature designs for citry Events

Empirical study of what typing spelling gives users real IDE/typechecker
support inside `class Events:` when the framework rebuilds that class at
runtime and static checkers only ever see the user's bare source classes.
Experiment files live in `typing-lab/` next to this report; every verdict
below was produced by actually running the file and both checkers on it.

## Setup

| Tool | Version | Notes |
|---|---|---|
| Runtime Python | 3.13.12 (`/Users/mac/repos/citry/.venv/bin/python`) | System `python3` is 3.9.6, below citry's floor, so it was not used. All runtime verdicts are from 3.13.12; version-dependent points for 3.10-3.12 are flagged in "Version dependence" below. |
| mypy | 1.19.1 (compiled), `/Users/mac/repos/citry/.venv/bin/mypy` | Run with `--check-untyped-defs` to match the repo config. Default `python_version` (3.13). |
| pyright | 1.1.411 (resolved by `npx pyright`) | Run with `--pythonversion 3.13`; default typeCheckingMode ("standard"). Without the pin, npx pyright picked up the system Python 3.9 environment and emitted spurious `reveal_type is unknown import symbol` errors against 3.9 stubs; those disappeared with the pin and are excluded from the verdicts. |
| typing_extensions | 4.15.0 (venv) | Only needed for P9 (PEP 696 TypeVar default) on Python < 3.13. |

Repo facts (asked in the brief):

- `from __future__ import annotations` is the citry convention: 51 of 56
  `.py` files under `/Users/mac/repos/citry/packages/py/citry/citry` have it.
- `[tool.mypy]` in `/Users/mac/repos/citry/pyproject.toml` is modest:
  `check_untyped_defs = true`, `ignore_missing_imports = true`, plus
  `disallow_untyped_defs = true` overrides for `citry_core.*` and
  `pygments_citry.*`. No plugin, no strict mode globally, nothing that
  changes name-resolution behavior. So the results here transfer directly.
- Relevant design context (`docs/design/events.md` 3.2, 3.3): `self.state`
  is the typed State, `None` when the component declares no State, and the
  extension binds wire args against handler signature annotations at
  runtime. That last point means annotations must also be resolvable at
  runtime, so each experiment probes `typing.get_type_hints` too.

## Verdict matrix

"Runtime" = imports and runs on 3.13.12. "gth" = `get_type_hints` with no
help; "gth+localns" = with a framework-supplied `localns={"State": ...}`.
"State" in a checker column means `reveal_type` showed the intended
`MyComp.State`; FAIL means the checker reports the name unresolved and the
revealed type is `Any` (mypy) / `Unknown` (pyright).

| # | User spelling | Runtime | gth / gth+localns | mypy 1.19.1 | pyright 1.1.411 |
|---|---|---|---|---|---|
| P1a | param `state: State`, no future | FAIL: NameError at import | n/a | FAIL | FAIL |
| P1b | param `state: State`, future | OK | NameError / OK | FAIL | FAIL |
| P1c | param `state: "State"` | OK | NameError / OK | FAIL | FAIL |
| P1d | param `state: "MyComp.State"` | OK | OK | **State** | **State** |
| P1e | param `state: MyComp.State`, no future | FAIL: NameError at import | n/a | State (TRAP: accepts code that crashes) | FAIL (matches runtime) |
| P1f | param `state: MyComp.State`, future | OK | OK | **State** | **State** |
| P2a | class attr `state: State`, no future | FAIL: NameError at import | n/a | FAIL | FAIL |
| P2b | class attr `state: State`, future | OK | NameError / OK | FAIL | FAIL |
| P2c | class attr `state: "State"` | OK | NameError / OK | FAIL | FAIL |
| P2d | class attr `state: "MyComp.State"` | OK | OK | **State** | **State** |
| P3a | `class Events(EventsBase["MyComp.State"])` | OK; `__orig_bases__` holds `ForwardRef('MyComp.State')` | n/a | **State** | **State** |
| P3b | `class Events(EventsBase[State])`, bare | **OK**; `__orig_bases__` holds the real class | n/a | **State** | **State** |
| P3c | undefined name in base expr, WITH future | FAIL: NameError at import (proof: future never rescues base exprs) | n/a | FAIL | FAIL |
| P3d | P3b plus future import | OK, identical to P3b | n/a | **State** | **State** |
| P4 | plain `EventsBase` with `state: Any` | OK; state typo only found at runtime | n/a | actions/request/event typed; state = Any, typos silent | same |
| P5a | all-args, bare `State` param, future | OK | NameError / OK | FAIL on state; all other params typed | same |
| P5b | all-args, `"MyComp.State"` param | OK | OK | **all params typed** | **all params typed** |
| P6 | bare `class Events:` + decorator / `__getattr__` tricks | OK (import only) | n/a | no typed state possible: error or Any | same |
| P7 | bare `State()` in a method BODY | FAIL: NameError at call time | n/a | flagged | flagged |
| P8 | combined generic base (state + actions + request + event) | OK, typed mutation works | n/a | **all members typed**; unsubscripted base -> Any | same (Unknown) |
| P9 | P8 + PEP 696 `TypeVar("S", default=None)` | OK | n/a | subscripted -> **State**; bare base -> **None** | same |

Bottom line before the details: bare `State` is dead in every annotation
position on both checkers; the qualified string `"MyComp.State"` (or
unquoted `MyComp.State` under the future import) works everywhere; and the
generic base `class Events(EventsBase[State])` is the only spelling that is
green on runtime AND both checkers with the bare, unquoted sibling name.

## The scoping fact underneath all of it

Class bodies do not create enclosing scopes (PEP 227 rules). From inside
the `Events` class body, or inside its methods, the name `State` defined in
`MyComp`'s body is invisible, to the runtime and to both checkers alike.
There is exactly one place where `State` IS visible: the base-class list of
`class Events(...)`, because that expression is evaluated while `MyComp`'s
class body is still executing, where `State` is a local. This is the same
reason `class B(A): ...` works for sibling nested classes. Both checkers
model this correctly (P3b clean on both). The brief expected a NameError
here; the experiment refutes that, and it is the load-bearing result of
this lab.

## Per-pattern details

The shared stub in every file (elided below):

```python
class Component:
    pass
```

plus, for P3/P8/P9:

```python
S = TypeVar("S")            # P9: TypeVar("S", default=None) from typing_extensions

class EventsBase(Generic[S]):
    state: S
```

and for P4/P8: `ActionsNS`, `Request`, `EventMeta` as small module-level
classes, declared on `EventsBase` as `actions: ActionsNS` etc.

### P1: parameter annotation referencing the sibling State

```python
class MyComp(Component):
    class State:
        query: str = ""

    class Events:
        def search(self, state: State) -> None:   # variants: "State", "MyComp.State", MyComp.State
            reveal_type(state)
```

- **Bare `State`** (p1a/p1b): without the future import the file does not
  even import (`NameError: name 'State' is not defined`, raised while the
  `def` executes inside the Events class body). With the future import it
  runs, but both checkers still reject it:
  - mypy: `error: Name "State" is not defined [name-defined]`, revealed `Any`
  - pyright: `error: "State" is not defined (reportUndefinedVariable)`, revealed `Unknown`
- **Quoted `"State"`** (p1c): imports fine, same checker rejection. Quoting
  defers evaluation but does not change the resolution scope.
- **Quoted `"MyComp.State"`** (p1d): clean on both checkers, revealed
  `State` on both. `get_type_hints` resolves it with no help (MyComp is a
  module global by then).
- **Unquoted `MyComp.State`, no future** (p1e): crashes at import
  (`NameError: name 'MyComp' is not defined`; the class is not bound during
  its own body). **pyright correctly rejects it; mypy accepts it** and
  reveals `MyComp.State`. This is a real trap: in a file without the future
  import, mypy blesses a spelling that cannot import. Docs must never show
  this form without the future import.
- **Unquoted `MyComp.State`, with future** (p1f): clean everywhere. Since
  the future import is the citry house convention (51/56 files), this is
  the natural no-quotes spelling for parameter annotations.
- **Runtime introspection**: for the bare/quoted-bare variants that import,
  `get_type_hints(search)` raises NameError unless the framework passes
  `localns={"State": comp_cls.State}`; with that localns it resolves. So
  the framework CAN rescue bare `State` at runtime for its own coercion
  machinery, but no checker will ever accept it, so it must not be the
  documented spelling.

### P2: class-level `state: State` annotation on Events

Same three spellings as class attributes, `self.state` used in a method.
Results mirror P1 exactly:

- Bare, no future (p2a): NameError at import. Class-level annotations ARE
  evaluated at runtime (unlike annotations local to a function body).
- Bare with future (p2b) and quoted `"State"` (p2c): import OK, both
  checkers reject, `self.state` is Any/Unknown. `get_type_hints(Events)`
  needs the framework localns.
- Quoted `"MyComp.State"` (p2d): clean on both; `self.state` -> `State`,
  `self.state.query` -> `str`; `get_type_hints` resolves unaided.

P2d works, but every component must repeat its own class name in a magic
string, and the framework learns nothing from it that it does not already
know. Strictly worse ergonomics than P3 for the same result.

### P3: generic base `EventsBase(Generic[S])` with `state: S`

```python
class MyComp(Component):
    class State:
        query: str = ""

    class Events(EventsBase[State]):        # p3b: bare, unquoted; p3a: EventsBase["MyComp.State"]
        def search(self) -> None:
            reveal_type(self.state)          # State on both checkers
            reveal_type(self.state.query)    # str on both checkers
```

- **p3a, quoted `"MyComp.State"`**: runs; `__orig_bases__` is
  `(EventsBase[ForwardRef('MyComp.State')],)`, so the framework would have
  to resolve a string. Both checkers infer `self.state` as `State`.
- **p3b, bare `State`**: **runs** (see "the scoping fact" above) and
  `__orig_bases__` is `(EventsBase[MyComp.State],)`, `get_args` returns the
  real class object, zero string resolution needed by the framework. Both
  checkers infer `self.state` as `State` and `self.state.query` as `str`.
- **p3c**: with an undefined name in the base list, the file crashes at
  import even WITH the future import, confirming base expressions always
  evaluate. The future import is irrelevant to P3 either way (p3d behaves
  identically to p3b). The flip side: a typo in the base subscript fails
  fast at import on every Python version, which is the best failure mode
  available.
- Lab note: the `__orig_bases__` probe lines in the mains are flagged by
  both checkers (typeshed does not declare the attribute on `type`). That
  is framework-internal scaffolding, not user ceremony; framework code
  reads it via `types.get_original_bases()` (typed, 3.12+) or
  `getattr(cls, "__orig_bases__")` on 3.10/3.11.
- Ordering constraint: `State` must be defined before `Events` in the
  component body. That matches how the docs already order the classes.
- Reasoned, not tested: a component subclass that replaces `State` must
  also re-subscript (`class Events(Parent.Events, EventsBase[State])` or
  redeclare), otherwise checkers keep seeing the parent's State. Standard
  generics behavior; worth one line in user docs eventually.

### P4: plain (non-generic) base, `state: Any`

`self.actions` -> `ActionsNS`, `self.request.method` -> `str`,
`self.event` -> `EventMeta` on both checkers: a plain base does type the
fixed members fully. The measured loss for state is total:
`reveal_type(self.state)` is `Any` on both checkers,
`self.state.no_such_field` passes both checkers silently and raises
`AttributeError` at runtime. Autocomplete on state fields: none.

### P5: all-args handler signature

```python
def search(self, state: State, context: AppContext, event: EventMeta,
           request: Request, query: str = "") -> None: ...
```

- Every module-level annotation (`AppContext`, `EventMeta`, `Request`,
  `str`) is typed correctly on both checkers with zero ceremony, including
  the arbitrary user-owned `context: AppContext`. Checkers do not care that
  the framework, not the user, calls the method.
- The `state` parameter inherits P1's scoping problem unchanged: bare
  `State` fails both checkers even under the future import (p5a); it must
  be `"MyComp.State"` (p5b, clean everywhere) or unquoted `MyComp.State`
  under the future import (per p1f).
- So all-args is viable, but its state parameter drags in the qualified
  spelling, per handler. With several handlers per component that is the
  worst ceremony-per-handler of the viable options.

### P6: can a bare `class Events:` get typed `self.state`? No.

- Identity class decorator typed `(type[T]) -> type[T]`, with
  `@dataclass_transform()`: both checkers still error on `self.state`
  (mypy `"Events" has no attribute "state"`, pyright
  `Cannot access attribute "state" for class "Events*"`).
  `dataclass_transform` only changes synthesis of fields declared on the
  decorated class; it cannot pull members from a sibling class. A decorator
  cannot change the type of the class it returns without losing the class's
  own members (Python typing has no intersection type).
- A base with `def __getattr__(self, name: str) -> Any`: makes the errors
  go away by making everything `Any`, including
  `self.state.no_such_field`. That is silencing, not typing: no
  autocomplete, and typos hide too.
- A mypy plugin could synthesize the member, but pyright has no plugin
  system, so the plugin route abandons VS Code/Pylance users entirely.
  Verdict: without a base class or an explicit annotation there is no way
  to give bare `class Events:` a typed `self.state` on both checkers.

### P7: bare `State()` in a method body

Imports fine (nothing is evaluated at definition time), then
`NameError: name 'State' is not defined` at call time; both checkers flag
the line, so at least the mistake is visible in the IDE before it ships.
`MyComp.State()` in a body works (module-global lookup at call time). This
bounds what examples can show: any handler or `render()`-style method that
constructs classes must use the `MyComp.State` qualified form in its body.

### P8 and P9: the assembled design

P8 combines P3 and P4 on one base (`state: S` plus typed `actions`,
`request`, `event`). Everything is typed on both checkers, including the
mutation `self.state.query = q`. A stateless component writing
`class Events(EventsBase):` (no subscript) degrades to `Any`/`Unknown` for
state, which is silent.

P9 fixes that degradation with PEP 696: `S = TypeVar("S", default=None)`
(from `typing_extensions`; native `typing` only on 3.13+). Then a bare
`class Events(EventsBase):` yields `self.state` revealed as **`None` on
both checkers**, which is exactly the documented contract in
events.md 3.2 ("stateless handlers: `self.state` is `None`"), and any
attribute access on it is an immediate checker error instead of silent Any.
Runtime works on 3.13.12 with typing_extensions 4.15.0; both mypy 1.19.1
and pyright 1.1.411 fully support the default. (pyright emits only a
stub-source warning for typing_extensions because the lab did not point it
at the venv; cosmetic.)

## Version dependence (Python >= 3.10, < 4.0)

Runtime verdicts were measured on 3.13.12 only. Transfer to 3.10-3.12:

- The scoping rules that drive every result (class bodies do not nest,
  base lists evaluate in the enclosing scope, class-level annotations are
  evaluated, function-signature annotations are evaluated at `def` time
  unless the future import is present) are unchanged across 3.10-3.13. No
  measured conclusion above is version-dependent in that range.
- Subscripting a user generic with a string (P3a) wraps it in `ForwardRef`
  on all of 3.10-3.13 (long-standing `typing._type_check` behavior).
- PEP 696 defaults (P9) need `typing_extensions.TypeVar` at runtime on
  3.10-3.12; `typing.TypeVar` gains `default=` in 3.13. One small runtime
  dependency for older Pythons.
- Lab scaffolding only: `typing.reveal_type` and `typing.dataclass_transform`
  are 3.11+; on 3.10 they come from typing_extensions. Irrelevant to the
  patterns themselves.
- **Python 3.14 flag** (inside citry's `<4.0` range, outside the brief's
  3.10-3.13 window): PEP 649 makes all annotations lazy. The three
  "fails fast at import" cells (P1a, P1e, P2a) stop failing at import; the
  NameError moves to whenever annotations are introspected, i.e. into the
  framework's arg-binding step. Checker verdicts are unaffected. This
  strengthens the case against ever documenting the bare/unquoted-qualified
  no-future spellings: today they fail loudly at import; on 3.14 they fail
  late and inside framework code.

## Notes for the framework side (from the get_type_hints probes)

- With the P3/P8/P9 design the framework gets the State class as a real
  object from `__orig_bases__` (p3b: `get_args(...)` returned
  `<class 'MyComp.State'>`); no string resolution at all for state.
- For handler parameter annotations (wire args, P5-style), the framework
  should call `get_type_hints(handler, localns={...})` seeded with at least
  the component's own nested classes and the component name. That makes
  even bare `State` resolvable at runtime (verified), but since no checker
  accepts bare `State`, docs should only ever show module-level types or
  the `MyComp.State` qualified form for parameters.

## Ranked recommendation

1. **Generic base, bare subscript, PEP 696 default (P3b + P8 + P9):**
   `class Events(citry.EventsBase[State]):` with
   `S = TypeVar("S", default=None)` and the fixed members
   (`actions`, `request`, `event`) declared on the base with real types.
   This is the only design that is green on runtime and BOTH checkers with
   no quoting, no future-import dependence, and no repetition of the
   component name. Users get full autocomplete and checking on
   `self.state`, `self.actions`, `self.request`, `self.event`; typed
   mutation of state fields works; a stateless `class Events(EventsBase):`
   types `self.state` as `None`, matching the documented contract, and the
   missing-subscript mistake surfaces as a checker error on first field
   access instead of silent Any. A typo in the subscript fails fast at
   import on every version. Ceremony: one base class and one subscript per
   component, and State must be declared above Events. Cost: a
   typing_extensions runtime dependency for Python < 3.13. The bare-class
   `class Events:` spelling can still be accepted at runtime; it just gets
   no state typing (P6 proves nothing can fix that), so the base is the
   documented, recommended form rather than a hard requirement.
2. **All-args signatures for wire args only (P5), on top of option 1:**
   ordinary typed parameters for user wire args are fully green on both
   checkers with zero ceremony, so keep them. Do not thread state through
   a parameter: it would need the `"MyComp.State"` qualified spelling per
   handler, which is the same information the base subscript already
   carries once.
3. **Class-level `state: "MyComp.State"` on Events (P2d):** works on both
   checkers and needs no framework types at all, but repeats the component
   name in a string in every component and gives the framework nothing
   machine-readable. Acceptable as a documented fallback for users who
   refuse the base class; not the headline design.
4. **Plain non-generic base (P4):** types the fixed members but leaves
   `self.state` as Any with silently-passing typos. Only worth it if
   generics were rejected outright, and P3's results remove the reason to
   reject them.
5. **Ruled out by evidence:** bare `State` in any annotation position
   (rejected by both checkers everywhere, and a runtime crash without the
   future import); unquoted `MyComp.State` without the future import (mypy
   accepts it while the interpreter crashes on import, the worst possible
   combination); decorator or `__getattr__` tricks on a bare class (P6:
   errors or Any on both checkers; a mypy plugin cannot cover pyright).

One caution to carry into the docs regardless of design: method BODIES must
construct sibling classes as `MyComp.State()`, never bare `State()` (P7),
and component subclasses that replace State need their Events re-subscripted
(reasoned from generics semantics, not separately tested).
