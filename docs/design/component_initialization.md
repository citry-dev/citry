# Design: component initialization and concurrent first use

**Status (2026-07-23): design agreed; built.** This document defines when a
Citry instance becomes ready for concurrent component lookup, how lazy first
use behaves, and why Citry reports a competing lifecycle operation rather than
waiting for it.

The public startup operation is [`Citry.initialize()`](../../packages/py/citry/citry/citry.py).
It gives a server a known point at which component Python modules have been
imported, component classes and built-ins have registered, and parse-time tag
rules have been built. Template, JavaScript, and CSS asset files remain lazy.

For user-facing setup, see
[`Registration and autodiscovery`](../../docs_site/content/concepts/registration.md)
and [`Web frameworks`](../../docs_site/content/web-frameworks.md).

---

## 1. Prior art and current lifecycle

The implementation joins four existing operations that already mutate or
derive related state:

1. [`Citry.autodiscover()`](../../packages/py/citry/citry/citry.py) imports
   component modules through
   [`import_component_modules`](../../packages/py/citry/citry/autodiscovery.py).
   Class definitions register themselves through `ComponentMeta`.
2. [`ComponentMeta.__new__`](../../packages/py/citry/citry/component.py) runs
   extension class-created hooks, initializes extension config classes, and
   registers the new component.
3. The private registry's built-in initializer creates seven built-in components
   classes on first engine lookup.
4. [`Citry._tag_rules`](../../packages/py/citry/citry/citry.py) derives and
   caches parser rules from every registered component's `Kwargs` and `Slots`.

Discovery and built-in creation already had retryable rollback. Registration
and unregistration already restored Citry-owned state when an extension hook
raised. Those transactions are deliberately local: Python module side effects
and extension-owned state cannot generally be undone.

The missing contract was isolation. The boolean attempt flags described
same-thread progress, but they did not distinguish the thread performing the
work from another thread. A second thread could therefore inspect or mutate
the first thread's working state.

## 2. Confirmed failure modes

Deterministic thread harnesses reproduced these outcomes before this design:

- A lookup could report `NotRegistered` while another thread was still
  importing the module that defined the requested component.
- A lookup could receive a partially created built-in or discovered component,
  followed by rollback removing that class from the registry. A retry then
  created a different class object for the same name.
- A registration could invalidate tag rules while another thread was building
  them. The older build could publish afterwards and leave a stale cache.
- A registration, unregistration, or clear could succeed while another
  operation held a rollback snapshot. A later failure could restore that
  snapshot and erase or resurrect the competing thread's mutation.
- Discovery could clear its running flag just before publishing its completed
  flag, allowing a second scan to begin in that publication gap.
- A built-in attempt must authorize only the classes carrying that engine's
  private token. Extension hooks running during the attempt cannot claim a
  reserved name.

These are one family of bug: a transaction-like operation exposed its working
state to a thread that was not part of that operation.

## 3. Why a competing thread never waits

Waiting appears convenient, but Python imports make an unconditional wait
unsafe. The reproduced cycle is:

1. Thread B starts importing a component module and holds Python's per-module
   import lock.
2. Thread A starts Citry discovery and reaches that module, so A waits for B's
   import lock.
3. The module being executed by B performs a Citry lookup.
4. If B waits for A's discovery, A and B wait for each other forever.

Python's import deadlock detector tracks cycles between import locks. It cannot
see a wait on an unrelated Citry condition, event, or mutex, so it cannot break
this cycle for Citry.

Citry therefore raises
[`CitryLifecycleInProgress`](../../packages/py/citry/citry/lifecycle.py)
immediately when a different thread owns component lifecycle work. It never
waits for that owner. The caller may retry after the operation finishes, while
servers avoid the situation by initializing before request concurrency begins.

## 4. Public startup contract

### `Citry.initialize()`

`app.initialize()` is synchronous, returns `None`, and completes these steps in
order:

1. Run configured autodiscovery when `app.settings.autodiscover` is true.
2. Create and register every built-in component.
3. Build and validate tag rules for the current registry.

Repeated successful calls are safe. Existing completed work is reused. A
registration or unregistration invalidates the tag rules, so a later call
rebuilds them.

The method respects `autodiscover=False`. A caller that wants an explicit scan
under that setting uses:

```python
app.autodiscover()
app.initialize()
```

Initialization prepares component registration and parser metadata. It leaves
these operations for normal lazy use:

- Loading `template_file`, `js_file`, or `css_file`.
- Compiling every component template.
- Reading component dependency files.
- Creating render instances or rendering HTML.

The registry stays mutable. Applications may register or unregister later,
then call `initialize()` again when they want tag rules eagerly rebuilt.

## 5. Lifecycle coordinator

Each `Citry` instance has one private component registry and one lifecycle
coordinator owned by that registry. Every engine-level registration,
discovery, lookup, initialization, and clearing operation uses that same
coordinator, so related state cannot drift behind separate locks.

The coordinator contains:

- A small state mutex.
- One atomically published ownership record containing the logical owner thread
  ID, nested entries, root operation name, and reentry policy.

The mutex is held only while claiming or releasing ownership, checking for a
competing owner, or performing one final raw mapping/cache read. Module imports,
component factories, extension hooks, and cache callbacks run without the
mutex held. The logical owner remains recorded across that work.

This separation matters. A mutex held across an import would recreate the
import-lock cycle. Releasing all ownership across an import would expose
partial state.

### Protected state

The logical owner covers:

- Registry name and reverse-class mappings.
- Built-in attempt and completion state.
- Citry's class-ID index.
- Configured discovery attempt and completion state.
- The per-module registration journal and registration snapshots.
- Tag-rule invalidation, construction, and publication.
- The class-created extension hooks and config setup that precede registration.

The class object itself is created before the claim. Citry-managed hooks and
publication begin only after the class resolves its owning Citry instance.

### Atomic ready reads

A completed lookup uses a short read path:

1. Acquire the state mutex.
2. Reject a different logical owner, if present.
3. Confirm the required discovery, built-ins, and cache state is ready.
4. Perform the final dictionary or cache read before releasing the mutex.

The final read must stay inside that block. A readiness check followed by an
unprotected read would allow `clear()` or registration to claim ownership in
between.

If lazy work is required, the caller claims logical ownership and retains it
through the completed discovery or built-in work and the final lookup.

## 6. Reentry rules

Lifecycle APIs and extension hooks are synchronous. Thread identity therefore
identifies the current operation. Async lifecycle hooks would require a future
task-aware design.

| Operation | No current owner | Same thread owns lifecycle | Another thread owns lifecycle |
|---|---|---|---|
| Ready `get`, `has`, `components`, class-ID lookup, or tag-rule read | Read under the state mutex | Read current working state | Raise `CitryLifecycleInProgress` |
| Lazy Citry lookup | Own discovery, built-ins, and final read | Allow implicit lookup of state registered so far | Raise `CitryLifecycleInProgress` |
| Tag-rule construction | Own build through publication | Allow nested construction when a hook requests it | Raise `CitryLifecycleInProgress` |
| Register or unregister | Own mutation through hooks or rollback | Allow nested hook-driven mutation | Raise `CitryLifecycleInProgress` |
| Component class-created hooks and registration | Own both as one operation | Allow nested class definitions | Raise `CitryLifecycleInProgress` |
| Explicit `autodiscover()` | Own the complete scan | Raise `RuntimeError` | Raise `CitryLifecycleInProgress` |
| Explicit `initialize()` | Own all initialization steps | Raise `RuntimeError` | Raise `CitryLifecycleInProgress` |
| `clear()` | Own every clear step and callback | Raise `RuntimeError` | Raise `CitryLifecycleInProgress` |

Implicit same-thread reads are necessary during imports and built-in creation.
For example, a registration hook may look up a built-in that registered earlier
in the same factory attempt. Such a lookup sees the owner's current working
state. It may still report a later component as absent because source order has
not reached it yet.

Explicit recursive initialization and discovery are rejected because partial
state cannot count as successfully initialized. `clear()` rejects every nested
lifecycle access, including from a cache callback, so the registry cannot be
rebuilt halfway through clearing it.

## 7. Failure and retry behavior

Logical ownership is released in a `finally` block for every `BaseException`,
including cancellation-style exceptions such as `KeyboardInterrupt`. The
ownership record uses a unique entry token for each nested operation. Cleanup
can therefore tell whether that entry was published even if an asynchronous
exception lands between claiming ownership and entering the operation body.

An initialization failure leaves the instance retryable. It is not a global
transaction over Python:

- The failing module's Citry registration changes are rolled back.
- Earlier modules that imported successfully remain registered.
- Successfully imported dependency modules remain registered because Python
  caches them and will not execute them again on retry.
- A failed built-in attempt restores the complete pre-attempt built-in and
  Citry registration state.
- Arbitrary Python module side effects and extension-owned effects remain the
  responsibility of their authors.

A server should abort startup or explicitly retry when `initialize()` raises.

## 8. Server startup placement

Call `initialize()` after startup-time registrations and configuration, and
before starting request threads:

| Host | Recommended point |
|---|---|
| FastAPI or Starlette | Root application lifespan, before `yield` |
| Django | Project `AppConfig.ready()` |
| Flask | Application factory, after mounting and before returning the app |
| Bare ASGI | Root host lifespan |
| Bare WSGI | Before handing the callable to a threaded server |
| Worker or CLI process | Before starting worker threads |

Construction and route mounting remain configuration-only operations. Running
discovery in `Citry.__init__` would break the common module pattern where
discovered components import the `app` variable whose assignment is still in
progress. Mounting also cannot supply a universal startup hook: notably, an
ASGI application's mounted subapplication lifespan is not guaranteed to run.

## 9. Scope and non-goals

This protocol guarantees isolation for component discovery, registration,
built-in creation, clearing, class-ID lookup, and tag-rule publication.

It is not a blanket claim that every lazy render cache is thread-safe. Template
and asset caches keep their own synchronization contracts. `initialize()` does
not force those caches to populate.

Public component lookups go through `app.get()`, `app.has()`, and
`app.components`; all three complete configured discovery and built-in
initialization. Class-ID lookup and `repr(app)` do not trigger lazy
initialization; they only read the current state atomically.

Component class garbage collection invokes no Citry lifecycle operation,
registry mutation, cached-body eviction, or extension callback. The registry
holds a strong reference to every registered class, so a class that is eligible
for collection has already lost its final registry name, or its entire owning
engine is unreachable. Mutating the registry during collection would therefore
be either redundant or unobservable.

For explicit component removal, extensions release deterministic resources in
`on_component_unregistered`. `Citry.clear()` is a bulk engine teardown: it
clears engine-owned registries and caches without emitting per-component
unregistration hooks. Garbage collection runs no extension hooks. Memory-only
indexes use weak references. Caches whose values can release arbitrary Python
objects attach no weakref callback and prune dead entries during ordinary
locked operations.
Citry does not run extension callbacks from Python finalizers. Python may
invoke a finalizer while arbitrary code or any thread holds a lock, and its
data-model documentation warns that blocking from `__del__` can deadlock the
interrupted code.

## 10. Alternatives considered

### Wait for the active initializer

Rejected because of the reproduced Python import-lock deadlock. A timeout only
delays the same failure and makes request latency depend on an arbitrary value.

### Initialize in the constructor or mount helpers

Rejected because constructor discovery can import the application object before
its assignment completes, and mount helpers are not universal process-startup
hooks.

### Require explicit initialization for every use

Rejected because direct rendering and small single-threaded scripts benefit
from lazy initialization. The fail-fast fallback gives those uses a safe
boundary without making startup ceremony mandatory.

### Build an isolated staging registry

Rejected because imports and extension hooks can reach the live Citry instance,
and arbitrary Python side effects cannot be staged. It adds substantial
complexity while a first concurrent lookup still cannot safely infer whether a
missing name will appear later in the scan.

### Run cleanup from a nonblocking finalizer

Rejected because skipping a busy lock makes hook delivery timing-dependent,
while running the hook still permits arbitrary extension code to acquire a
different lock held by the interrupted thread. It fixes one call path without
making finalization safe.

### Defer finalizer cleanup until later lifecycle work

Rejected because retaining the class for a later callback resurrects it, the
callback may never run when the engine receives no later call, and a callback
failure would surface from an unrelated operation. Deterministic cleanup
already has the explicit unregistration hook.

### Make the lifecycle mutex reentrant

Rejected because garbage collection could then mutate registry state in the
middle of an atomic ready read. It also leaves every other application lock
reachable from an extension callback exposed to the same problem.

## 11. Regression coverage

The Python suite locks the contract with deterministic event-based tests for:

- Complete and idempotent `Citry.initialize()` behavior.
- `autodiscover=False` and explicit scan behavior.
- Failure, `BaseException`, and recursive-call retry behavior.
- Partial discovery and partial built-ins hidden from competing threads.
- A real per-module import-lock cycle that completes through fail-fast access.
- Registration, unregistration, and clear isolation from rollback snapshots.
- Component class-created hooks covered before registration begins.
- Component class collection while the lifecycle mutex is held, checked in a
  bounded child process so a regression cannot hang pytest.
- Cached-body collection while an unrelated mutex is held, checked in a
  bounded child process, plus later-access pruning of the dead cache key.
- Stale tag-rule publication prevented during concurrent registration.
- Concurrent read-only access after startup initialization.

These tests use events and barriers for ordering. Timeouts are test-failure
guards, not part of the runtime protocol.
