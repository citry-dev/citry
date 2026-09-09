# Simple components

Status: initial runtime integration on `perf/repeat-render-20260908`. The public
flag, declaration checks and rendering paths are implemented on this experimental
branch. Its first balanced large-page benchmark saves 26.63% in warmed time
versus ordinary Citry; see the research log's "Simple API measurement: public
declarations on the large page" section. Public documentation is written and the full repository gate passes.
The handoff records browser and documentation checks. The earlier prototype
results below describe separate experiments.

## Why a component should be able to give up instance identity

A presentation component often just turns inputs into HTML. Creating a component
instance, assigning it an ID, recording its invocation and supplied slots, running
instance hooks, and serializing its browser boundary can cost more than producing
that HTML.

`Component.simple = True` would let an author explicitly give up that independent
instance. Its template would keep its own variables while its output belongs to
the surrounding ordinary component. Citry would reject unsupported declarations
and calls, with a reason the author can act on. The flag would select a different
public contract, not promise that Citry will opportunistically find a faster path.

The user requested this flag and its strict errors after iterations 66 and 68 of
the repeat-render experiments. They also requested this dedicated design document.

## Prior art

The following implementations and tests were inspected before this design:

| Existing behavior | Implementation and implication |
| --- | --- |
| Class declarations and registration | `ComponentMeta.__new__` in `packages/py/citry/citry/component.py:344` composes schemas and extension declarations before registering a class. Validation must complete before registration exposes an invalid simple class. |
| Existing opt-in flag | `Component.pure` in `component.py:593` is an exact boolean, immutable after definition, and explicitly not inherited. `tests/test_component_pure.py` tests live children and repeated body work. A simple component makes a different promise. |
| Component construction | `_render_one` in `component_render.py:1002` creates the instance, binds ownership, constructs extension configs, runs data and render hooks, and builds output. A simple invocation must bypass these steps together. |
| Tag composition | `ComponentNode.render` in `nodes/__init__.py:1404` resolves inputs, collects slots, records an invocation and queues rendering. The simple decision belongs before slot capture and invocation recording. |
| Deferred rendering | `_settle_render` in `component_render.py:192` resolves children without recursive component calls and handles errors and replacement. Keep this scheduler and avoid finalizing the simple call's owner twice. |
| Templates and invalidation | `_get_compiled_template` in `component_render.py:1584` loads and compiles a template; the ordinary body builder applies template extensions and Const specialization. Validate the effective body, including extension output, and tie any prepared body to the template record. |
| Python-created values | `_render_value` in `citry_render.py:487` resolves component-like values and renders elements. Direct tags alone do not cover the public composition API. |
| Replacement and forwarding | `_replacement_parts` in `component_render.py:1524` queues elements returned or yielded by an ordinary render hook. `components/dynamic.py` forwards invocation metadata through the built-in dynamic selector. Both need explicit simple handling. |
| Standalone roots | `Citry.render_template` in `citry.py:329` uses the private transparent template root created in `components/__init__.py:31`. A simple root needs a render owner even though the selected simple class has no instance. |
| Slots | `SlotNode.render` in `nodes/__init__.py:2012` combines supply selection, physical placement, fallback and hooks. Iteration 66 only replaced an empty default outlet, not this general contract. |
| Inheritance and libraries | `ComponentMeta`, `_nested_declarations.py` and `library_component.py` preserve authored C3 declarations and materialize library classes per engine. Validate inherited declarations and materialized classes, not only the latest class namespace. |

These paths are Python runtime behavior. The initial implementation needs no
grammar, AST, compiler-output, PyO3, protocol-schema or native build change. The
Python authoring surface for `LibraryComponent` and introspection/tooling consumers
still need an explicit audit when the flag is added.

### What the experiments established

Iteration 66 manually selected the exact benchmark Button, Icon and HeroIcon
classes. Their data methods were audited to work without an instance; passing
`None` as `self` was an experimental shortcut, not an enforceable public contract.

Against ordinary Citry, the composed deferred variant saved a median paired
8.429 ms per warm render (27.4%, eight of eight joint wall/CPU wins). Executing
the callbacks immediately saved 9.473 ms (30.7%), but changed their order.
Removing instance identity and changing execution order are separate decisions.

Iteration 68 retained immediate execution and emitted text through a shared parts
list. It saved another independently measured 1.367 ms against iteration 66's
immediate variant (6.4%, eight of eight wins). Construction fell from 1,151 render
objects to 610. Those savings must not be added to the separately measured
iteration 66 savings.

The fixed examples passed bounded HTML, ownership, dependency, error and browser
checks. They did not establish a general class classifier, all extension behavior,
all composition entry points or Django parity. See
[`performance_render_research.md`](performance_render_research.md), iterations 66-68, for
methods, artifacts and limitations.

## Proposed authoring API

A simple component can expose its declared kwargs without a custom data method:

```citry
class Label(Component):
    simple = True

    class Kwargs:
        text: str

    template = """
        <span>{{ text }}</span>
    """
```

The inherited default data method exposes the validated kwargs as template
variables. A custom data method must be an explicit static method, so Citry does
not need to create an instance or pretend one exists:

```citry
class UpperLabel(Component):
    simple = True

    class Kwargs:
        text: str

    @staticmethod
    def template_data(kwargs, slots):
        return {"text": kwargs.text.upper()}

    template = """
        <span>{{ text }}</span>
    """
```

The static method keeps the ordinary two-input calling convention. It receives
a fresh kwargs mapping or declared kwargs schema, and a slots mapping or declared
Slots schema. Supplied default content is a real lazy `Slot`, so the callback can
consume it or return it as template data. Content still evaluates in its caller's
scope. The first implementation supports the restricted Slots declaration below.

Initially accept an ordinary synchronous Python function inside `staticmethod`,
with a signature callable with the two positional inputs. Reject coroutine
functions, generator functions and arbitrary callable objects at definition time.
Before ordinary normalization, reject awaitable and generator return values
explicitly. Ordinary normalization alone accepts generators yielding pairs, so
this is an additional simple-mode restriction. A decorator
must leave an accepted static function descriptor, not hide an instance-binding
requirement behind a custom descriptor.

`simple` must be an exact `bool`; reject `1`, `None`, strings and descriptors.
`simple=True` inherits, but every subclass is validated independently. A subclass may explicitly declare `simple=False` to
use the ordinary contract. Freeze the effective flag after class creation.
This differs deliberately from `pure`, whose determinism promise does not inherit.

## Eligibility and strict errors

Validation has three boundaries. Definition checks inspect the effective class,
template checks inspect the loaded and transformed template, and call checks
inspect the actual invocation. Neither a cold render nor a repeated render may
silently use the ordinary pipeline after a failed simple check.

| Area | Proposed initial rule | Failure boundary |
| --- | --- | --- |
| Data method | Inherited default, or synchronous `@staticmethod template_data(kwargs, slots)`; no instance or class method | Class definition; report the method and required form |
| Instance behavior | Keep the exact supported base descriptors for constructors, lifecycle and instance accessors; permit authored helper functions only as explicit static methods | Class definition, including inherited overrides |
| Assets | No effective `js`, `js_file`, `css`, `css_file`, `messages` or `messages_file`; no JS/CSS data methods or dependency override | Class definition, including inherited assets |
| Extension configuration | No explicit instance-bearing configuration such as Events, State, Cache, Dependencies or I18n; generated default configs are not authored opt-ins | Class definition after resolving authored inheritance |
| Templates | Inline or file-backed template using supported ordinary HTML, expressions, branches, loops and nested component calls | Effective template preparation |
| Content outlet | Initially no outlet, or an empty implicit default outlet; no named/dynamic slots, slot data, required/fallback semantics | Effective template preparation, including inactive branches |
| Content supplied to a call | Initially absent or implicit default content; reject explicit named fills and unsupported Python slot supplies | Tag/element validation before rendering the simple body |
| Component identity directives | No component-level client bindings or keyed/morphable range metadata on the simple invocation | Call validation, including dynamic bindings |
| Unknown nodes/providers | Accept an enumerated set of built-in runtime node types; reject other transformed nodes until their behavior is supported explicitly | Effective template preparation |
| Invalid kwargs or returned data | Preserve ordinary schema construction and output normalization errors | Every call, before template execution |

An empty asset string is still an authored asset declaration; do not use its
truthiness to classify the class. Conversely, an engine-generated extension
configuration is not evidence that the author requested that feature. Resolve
both cases from the effective authored declarations.

Simple HTML supports ordinary `c-bind` attribute spreads. The i18n extension
leaves these as ordinary attribute nodes because a simple body has no translation
collector of its own. Template validation rejects literal `$c-tr` bindings,
including inactive branches; attribute resolution rejects bindings supplied
through a spread on any render, even if their value is false. A caller's active
translation catalog does not enable bindings inside a simple body. Ordinary
caller content and ordinary child components retain their translation behavior.

The validator must name the component and the unsupported field, method or
template location. Examples of the intended error messages:

```text
Component Badge uses simple=True but declares css.
Component Badge uses simple=True; template_data must be a static method.
Component Panel uses simple=True; named slot 'header' is unsupported.
Component Badge uses simple=True; c-key requires component identity.
```

Type errors describe unsupported method/input shapes; value errors describe an
invalid declaration value or incompatible combination. Parse and existing schema
errors retain their current exception types and source context. A render-time
simple error follows the ordinary enclosing error boundary; errors must not be
converted into empty output or ordinary rendering.

### Initial slot schema restriction

The private declaration validator accepts an omitted `Slots` schema, an empty
plain field class, or a plain field class with one optional field named `default`,
defaulting to `None`, typically annotated `Slot | None`. Citry's generated dataclass must accept and store
the supplied value. Authored dataclasses, custom schema metaclasses, constructor
hooks, factories, `InitVar`, `ClassVar`, non-input fields and non-None defaults are
rejected. Ordinary kwargs and template-data schemas retain their existing adapter
choices.

This restriction is structural. Inspecting a dataclass field whose default is
None does not prove that its constructor leaves missing content absent: a custom
initializer or `__post_init__` can create a fill. The first implementation uses
the known plain-field conversion rather than inferring arbitrary constructor
behavior. The rendering path must still validate supplied content and preserve
real slot values for the callback; a checked schema alone does not implement that
contract.

The validator uses the same paired inheritance rule as the asset loader. For
example, a child declaring `css=None` resets an inherited `css_file` too. It also
compares descriptor definitions without binding them, including class-valued
descriptors implemented by a metaclass, and checks the actual callback function's
signature rather than a decorator's advertised signature.

### What the flag does not prove

A static method can read a global, call another function or have a side effect.
Citry can enforce that it is called without an instance. It cannot prove arbitrary
Python purity from a method signature, bytecode scan or absence of assets.
The initial contract therefore runs the callback for every invocation.
Likewise, the method validator compares descriptors and their declared forms; it
does not try to infer whether an arbitrary instance method happens to avoid
instance state. The implementation must enumerate the permitted base descriptors
and class-level hooks before accepting a class.

The absence of JS/CSS declarations does not imply that the emitted HTML contains
no JavaScript behavior. Ordinary DOM Alpine attributes can use the surrounding
scope, and an authored `x-data` can establish a DOM scope. The restriction concerns
an independent Citry component instance and its features. Template validation must
describe concrete unsupported constructs, not claim to prove all embedded code
free of effects.

The recursive scalar/container guard in iteration 66 was part of that experiment's
trusted-input restriction. Removing instance identity does not by itself prove
that this deep guard is necessary. The public implementation should retain normal
kwargs and data normalization unless a falsifier demonstrates a specific required
restriction; any narrower input rule must be documented and tested explicitly.

## Rendering and observable behavior

### Variables, ownership and descendants

A simple template gets fresh variables from its own data method. Caller variables
do not become implicit template inputs. Supplied default content still evaluates
where the caller wrote it.

Preserve ordinary template-global precedence: engine globals, then per-render
globals, then normalized component data. These variables do not require an
independent component instance. The experimental adapters rejected globals, so
the public implementation needs tests for shadowing, changed globals between
renders and isolation between concurrent render calls.

The simple call has no live Component instance, render ID, independent browser
scope or separately addressable range. Its DOM output belongs to the surrounding
ordinary component. Ordinary descendants retain their own identity, dependencies,
hooks and error handling. Their logical parent skips the simple class; lexical
source information must still identify the actual template that contains them.
Physical placement through an ordinary receiver's slot must remain correct.

The simple call inherits the provided values active at its call site. It cannot
change them through instance `provide()` or read them through instance `inject()`.
Ordinary descendants and caller content continue to use the existing provide
rules at their own rendering sites.

### Physical boundaries for transparent callers

A transparent caller can own both its enclosing result and interior renders for
control flow, simple calls and supplied content. Repeating its ownership ID on
those render objects does not create additional component instances. When the
caller participates in the browser graph, it still needs exactly one pair of
physical boundary comments.

Manifest preparation selects the render explicitly marked as the transparent
component's whole output. Interior renders retain the caller's identity but do
not carry that marker. They may appear before or after the whole output, as
when tabs collect declarations and later render their lazy slot content in
separate buttons and panels. Slot-region records preserve that content's
ownership. Serialization emits the component boundary only at the marked
whole output. Repeating a marked output in separate positions, or including an
identity with no marked output, raises an error during manifest preparation.

The render pipeline preserves this marker through hook replacements. Retained
cache frames encode it as an exact boolean and replay restores it. Cache entries
missing the field fail validation and follow the normal cache-miss path. The
pre-1.0 artifact and runtime compatibility versions remain 1, as required by
the repository's compatibility policy. No browser protocol field changes.
Server and browser checks cover ordinary and simple interiors under transparent
callers; the final integration suite also covers tabs' remote caller-owned fills.

### Hooks and collected data

Simple invocations do not run component instance hooks or default-outlet slot
hooks. Definition/registration and supported template preparation hooks remain
class-level work. Ordinary ancestors and descendants retain their hooks.

Caller hooks may replace the whole output or recover a child error. Collected
dependencies and the recovered-error flag must survive those operations. The
shape of a simple template's interior parts is not a stable API: implementations
may join finished strings and omit interior render objects. Hooks that inspect
interior parts cannot rely on the ordinary component representation.

General context-merge hooks need explicit qualification before adopting the
shared collected-data dictionary from iteration 68. The first public
implementation may preserve ordinary merges while removing component boundaries.
Any remaining unsupported extension behavior must be rejected or documented as
outside the simple contract, with a concrete condition; a hidden fallback is not
acceptable.

### Scheduling and repeated rendering

Preserve deferred execution for direct simple tags in the initial API. Resolve
call inputs at the caller's usual stage, then run the data callback when the
scheduler reaches the invocation. Keep ordinary descendants on the scheduler as
well, including deeply nested compositions. Immediate recursive composition is
not implied by `simple=True`.

Python-created values must be audited against their existing execution point;
the ordinary expression path currently renders such values immediately. Do not
claim one universal callback order across syntax that already schedules
differently. Within each supported entry point, removal of instance identity
should not silently change when application callbacks execute.

An iterative scheduler alone does not make a deep simple tree safe. The current
serializer's `_append_frame_parts` recursively descends interior renders, while
ordinary child component roots are processed separately through placeholders.
Removing those component roots can turn a formerly safe chain into recursive
serialization. Either collapse completed simple interiors while preserving
metadata, or walk interiors iteratively. Depth qualification must finish both
rendering and `serialize()`/`str()`, without increasing the recursion limit, and
must cover physical-region wrappers and transparent owners too.

`simple=True` does not cache rendered output. A repeated call receives current
inputs and executes its data callback again. `pure=True`, when separately
declared, keeps its own body-reuse promise and must retain live nested calls.
Iteration 68 found that returning a plain string to a pure parent accidentally
made two callbacks disappear; the public implementation needs a regression test
for that case.

### Python composition and root rendering

The public feature must cover direct tags, `Component()` composition values,
component-like/library values and direct `.render()` calls. It must validate
manually constructed elements as well as the convenient class call.
The same audit includes simple elements returned or yielded from an ordinary
`on_render` hook, and targets reached through the built-in `<c-component>`
selector. Inspect forwarded invocation IDs, bindings and morph metadata before
accepting the target; the selector must not bypass a restriction that a direct
tag would enforce. `<c-element>` renders an ordinary HTML element rather than
selecting a simple class, but its separate element-metadata behavior needs a
regression check when shared forwarding code changes.

Dynamic selection retains the ordinary selector instance and its hooks. Its
input hooks run before it resolves the target, as they do for ordinary targets.
When the target is simple, the existing selector becomes the owner of that
content and completes the pending invocation itself; Citry does not create an
instance of the selected simple class. A Python-root selector or an already-bound
selector alias keeps its existing binding and does not attach supplies twice.
This path retains selector overhead, unlike a direct simple tag.

The selector carries the authored presence of explicit fills and range directives
until the target is known, including across selector subclasses and forwarding
chains. These restrictions and component bindings are checked before accepting a
simple target. Manually supplied element metadata is rejected too. The selected
simple body retains its own source information. Component tags authored in that
body use the selector as their parent; supplied content retains its caller's
scope.

An already-rendered `CitryRender` retains its original owner and ordinary
descendant identities when embedded. It is not an unrendered simple call and must
not be silently rebased onto the insertion owner. Test both an embedded composed
element and an embedded result from a prior root render, including dependencies
and graph references.

An embedded simple value carries the actual insertion context through value
conversion, slot calls and i18n bindings. Expression evaluation establishes that
context before an explicit Python `Slot()` call can execute. An explicit nested
render root replaces the ambient insertion context, including when it uses a
different engine. Provided-value overrides travel with the particular slot/value
call rather than being replaced with the enclosing context's original mapping.

A root has no surrounding component. Reuse the standalone-template root mechanism
or provide an equivalent explicit render owner, without constructing an instance
of the selected simple class. This infrastructure owner can incur root setup cost.
It must collect and serialize ordinary descendant dependencies correctly and must
not become an independent browser instance for the simple class.

Before adoption, settle whether all accepted Python default content can preserve
caller ownership. Reject unsupported supplies explicitly while their semantics
are incomplete. A root or Python call must not quietly switch the selected class
back to an ordinary component.

## Validation lifetime and changing definitions

Class validation must cover the effective C3 inheritance chain, including mixins,
inherited descriptors, library materialization and declarations modified by
class-created hooks. Read descriptors statically rather than executing a property
to decide whether a class qualifies. Failed validation must leave no registered
simple class that can render.

A once-validated class cannot become unsupported through a later assignment while
continuing to use its prepared path. Use immutable effective declarations or
explicit revalidation and invalidation. Freezing the flag alone is insufficient:
changing a base method, template provider, nested schema or extension generation
can also invalidate an assumption. The implementation must choose and test a
specific rule for each supported mutation path.

Template validation belongs to the effective template record. Loading a file or
running a template transformer can change what a class actually renders. Validate
all branches, not only the branch taken by the first input. `reset_template()`
and `reset_files()` must discard any prepared simple body so that an unsupported
replacement is rejected before its body runs.

Validate before Const specialization discards branches. Follow nested template
attributes and provider-produced bodies as well as the outer body. Keep lexical
scope explicit: a slot outlet authored inside content that the simple template
passes to an ordinary child still belongs to the simple template. The ordinary
child's own template is checked under that child's mode. Named fills that the
simple template supplies to an ordinary descendant are not named fills supplied
to the simple class, and should retain their ordinary behavior. Traversing every
descendant node under one blanket slot restriction would confuse these cases.

Do not repeatedly scan unchanged class definitions and complete template trees on
every warm invocation. Cache structural validation with its actual invalidation
owner; validate dynamic call inputs every time.

## Implementation stages and falsifiers

1. **Define and validate declarations.** Add the flag, class checks and typing
   surface. Cover inheritance, mixins, library materialization, exact booleans,
   rejected methods/assets/configs and failed registration. Decide the callback
   slot argument and mutation rules before publishing their behavior.
2. **Implement the common invocation path.** Use the existing deferred scheduler,
   fresh template variables and caller ownership. Validate the effective template
   and each call. Cover default content, Python composition and explicit roots;
   retain structured ordinary descendants and context merges.
3. **Qualify behavior.** Compare rendered application HTML with ordinary components
   while accounting for the declared identity difference. Check full ownership
   records, dependencies, whitespace, loops, slots crossing owners, transparent
   callers, errors, recovery, replacement and callback counts/order. Exercise
   class/template changes and concurrent renders. Test deep compositions through
   completed serialization without raising the Python recursion limit.
4. **Measure the public implementation.** Compare ordinary and explicitly simple
   versions of the same benchmark classes in balanced fresh processes. Measure
   cold, actual second and warm renders separately. Record validation and root
   costs, output size, IDs and callback activation. Rerun Django before making a
   new parity comparison. The fixed adapters are historical controls only.
5. **Finish the public surface.** Update user docs, API docstrings, the owning
   changelog and affected introspection/tooling behavior. Run independent
   technical and separate prose review, then the full repository gate and Linux
   type-check branch before treating the feature as working.

Commit each completed area and record measurements and rejected attempts in the
separate research log. No change to the adopted performance timeline is justified
by this design document alone.

The design fails qualification if unsupported calls render silently, changing a
definition bypasses validation, content acquires the wrong owner or scope, child
dependencies disappear, errors finalize the caller twice, callbacks disappear
under a pure parent, or supported deep composition becomes recursive. A wall-time
win cannot compensate for any of those failures.

## Alternatives considered

**Automatically infer simple classes.** Rejected for this feature: absence of
assets does not prove that an author accepts losing instance identity or hooks.
An explicit contract allows Citry to reject incompatible features clearly.

**Expose iteration 66's exact implementation behind a boolean.** Rejected: the
allowlist, `None` instance argument, fixed templates and direct-tag-only dispatch
are manually audited experiment assumptions. A public flag needs enforceable
rules and coverage of the ordinary composition paths.

**Make all selected calls immediate.** Deferred execution is the initial choice
because the experiments proved an observable callback-order change. Immediate
execution and larger shared-buffer optimizations can be measured separately once
the public semantics are qualified.

**Retain an ordinary component instance but skip selected hooks.** This could
preserve more API behavior, but it retains instance construction and ownership
work that the selected presentation components do not require. Experiments 61-62
tested a different intermediate design: they removed the live instance while
preserving ownership identity, and did not meet their measured screen. They do
not establish the performance of a retained-instance variant. The chosen
direction follows the positive measurements from removing both the independent
instance and its ownership boundary in iterations 63-66.
