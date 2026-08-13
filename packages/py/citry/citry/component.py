"""
The Component base class.

A Component is a reusable unit of UI. It owns a template, optionally
defines typed inputs (via inner classes), and produces rendered output
through its lifecycle methods.

Calling a Component class returns a CitryElement (composition phase),
not a rendered string. Rendering happens when ``.render()`` is called
on the CitryElement.

Example:
    Minimal component::

        from citry import Component

        class Greeting(Component):
            template = '<p>Hello {{ name }}!</p>'

            def template_data(self, kwargs, slots):
                return {"name": kwargs.get("name", "World")}

        # Composition - returns a CitryElement
        element = Greeting(name="World")

        # Rendering - produces a CitryRender; serialize() (or str()) -> HTML
        html = element.render().serialize()

    Component with typed inputs::

        from citry import Component

        class Card(Component):
            template = '''
                <div class="card">
                    <h2>{{ title }}</h2>
                    <div>{{ body }}</div>
                </div>
            '''

            class Kwargs:
                title: str
                body: str = ""

            def template_data(self, kwargs, slots):
                return {
                    "title": kwargs.title,
                    "body": kwargs.body,
                }

        # Compose without rendering
        card = Card(title="Hello", body="Content")

"""

from __future__ import annotations

from contextvars import ContextVar
from hashlib import md5
from re import sub
from typing import TYPE_CHECKING, Any, ClassVar, cast

from citry._class_introspection import _safe_class_text, _static_class_dict, _static_class_mro
from citry._linting import _validate_component_lint
from citry._nested_declarations import (
    NestedClassDeclaration,
    _active_nested_class_declarations,
    _capture_nested_declarations,
    _compose_nested_declaration_class,
    _convert_to_slotted_dataclass,
    _get_nested_class_declarations,
    _is_dataclass_family,
    _nested_declaration_bases,
)
from citry.assets import load_css, load_js, load_messages, load_template, validate_asset_pairs
from citry.assets import reset_files as _reset_files_impl
from citry.assets import reset_template as _reset_template_impl
from citry.citry import Citry, citry
from citry.citry_element import CitryElement, _ElementMorphMetadata
from citry.ext.dependencies import get_dependencies as _get_dependencies_impl
from citry.introspection import _new_definition_id
from citry.library_component import (
    _DEFINITION_FLAG,
    _MATERIALIZATION_TOKEN,
    LibraryComponentMeta,
    _bind_component_runtime_type,
)
from citry.provide import BLOCKED, MISSING, inject_value, make_provided, validate_provide_key
from citry.slots import Slot, normalize_slot_fills
from citry.util.id import gen_render_id, validate_render_id
from citry.util.misc import get_import_path, to_dict

_DEFER_INPUT_FINALIZATION: ContextVar[bool] = ContextVar("citry_defer_input_finalization", default=False)
_DATA_SCHEMA_NAMES = ("Kwargs", "Slots", "TemplateData", "JsData", "CssData")

if TYPE_CHECKING:
    from collections.abc import Iterator

    from citry.citry_render import OnRenderGenerator, RenderReplacement
    from citry.citry_template import CitryTemplate
    from citry.ext.cache import CacheConfig
    from citry.ext.dependencies import CitryDependencies, DependenciesConfig, Dependency
    from citry.ext.events.config import Events as EventsConfig
    from citry.ext.i18n import I18n as I18nConfig
    from citry.ownership import ComponentInvocationId, ComponentTagClientBindingRecord, OwnershipGraph


def _schema_adapter_family(schema: type) -> str:
    """Classify the runtime construction protocol of one authored schema."""
    namespace = _static_class_dict(schema)
    if "__dataclass_fields__" in namespace:
        return "dataclass"
    schema_mro = _static_class_mro(schema)
    if tuple in schema_mro and "_fields" in namespace:
        return "namedtuple"
    mro_namespaces = (_static_class_dict(candidate) for candidate in schema_mro)
    protocol_names = {name for candidate_namespace in mro_namespaces for name in candidate_namespace}
    if "model_fields" in protocol_names:
        return "pydantic-v2"
    if "__fields__" in protocol_names:
        return "pydantic-v1"
    return "plain"


def _validate_schema_composition(
    component_class: type,
    name: str,
    declarations: tuple[NestedClassDeclaration, ...],
) -> bool:
    """Reject adapter combinations whose constructors cannot represent every C3 branch."""
    declaration_bases = _nested_declaration_bases(declarations)
    if len(declaration_bases) < 2:
        return False

    families = {_schema_adapter_family(schema) for schema in declaration_bases}
    component_name = _safe_class_text(component_class, "__name__") or "Component"
    dataclass_family = families <= {"plain", "dataclass"}
    if len(families) > 1 and not dataclass_family:
        rendered = ", ".join(sorted(families))
        msg = (
            f"Component {component_name}: nested {name} declarations from multiple C3 branches"
            f" use incompatible schema adapters ({rendered}). Use one adapter family across the branches."
        )
        raise ValueError(msg)
    family = "dataclass" if dataclass_family else next(iter(families))
    if family == "namedtuple":
        msg = (
            f"Component {component_name}: NamedTuple {name} declarations from multiple C3 branches"
            " cannot be combined without silently dropping fields. Use plain nested field classes"
            " or one explicitly composed schema."
        )
        raise ValueError(msg)
    if family != "dataclass":
        return False
    if sum("__slots__" in _static_class_dict(schema) for schema in declaration_bases) > 1:
        msg = (
            f"Component {component_name}: slotted dataclass {name} declarations from multiple C3 branches"
            " have incompatible instance layouts. Use plain nested field classes or unslotted dataclasses."
        )
        raise ValueError(msg)
    dataclass_params = [
        _static_class_dict(schema).get("__dataclass_params__")
        for schema in declaration_bases
        if "__dataclass_fields__" in _static_class_dict(schema)
    ]
    frozen_modes = {bool(getattr(params, "frozen", False)) for params in dataclass_params}
    if len(frozen_modes) > 1:
        msg = (
            f"Component {component_name}: frozen and non-frozen dataclass {name} declarations"
            " from multiple C3 branches cannot share one generated constructor."
        )
        raise ValueError(msg)
    return frozen_modes == {True}


def _build_component_data_schema(component_class: type, name: str) -> object:
    """Build one effective core schema from its authored C3 declaration chain."""
    raw_declarations = _get_nested_class_declarations(component_class, name)
    if raw_declarations:
        nearest_value = raw_declarations[0].value
        if nearest_value is None or not isinstance(nearest_value, type):
            return nearest_value

    declarations = _active_nested_class_declarations(component_class, name)
    if not declarations:
        return None
    frozen = _validate_schema_composition(component_class, name, declarations)

    first_owner = declarations[0].declaring_class
    if first_owner is not component_class:
        owner_namespace = _static_class_dict(first_owner)
        if (
            "_citry_raw_nested_declarations" in owner_namespace
            and declarations == _active_nested_class_declarations(first_owner, name)
            and name in owner_namespace
        ):
            inherited = owner_namespace[name]
            if inherited is None or isinstance(inherited, type):
                return inherited

    effective = _compose_nested_declaration_class(component_class, name)
    effective = cast("type", effective)

    # An explicitly decorated dataclass keeps its authored options when it is
    # the whole declaration. Supported plain and dataclass combinations become
    # one slotted effective class after the adapter compatibility check above.
    effective_namespace = _static_class_dict(effective)
    if len(_nested_declaration_bases(declarations)) == 1 and "__dataclass_fields__" in effective_namespace:
        return effective
    if all(_is_dataclass_family(declaration.value) for declaration in declarations):  # type: ignore[arg-type]
        return _convert_to_slotted_dataclass(effective, owner=component_class, name=name, frozen=frozen)
    return effective


class ComponentMeta(LibraryComponentMeta):
    """
    Metaclass for Component classes.

    At class definition time, this metaclass:
    1. Reads the ``citry`` field (or uses the default Citry instance).
    2. Registers the component class with its Citry instance.
    3. Combines inner data classes (Kwargs, Slots, etc.) through the component
       C3 MRO and converts plain field declarations to slotted dataclasses.
    """

    # Per-class cache for the class_id property (stored on each component
    # class's own __dict__, never inherited).
    _class_id: str

    # Runtime identity is stamped on each class object before extension hooks.
    _definition_id: str

    def __setattr__(cls, name: str, value: Any) -> None:  # noqa: N805
        """Keep a concrete component bound to its class-definition owner."""
        namespace = _static_class_dict(cls)
        class_name = _safe_class_text(cls, "__name__") or "Component"
        if name == "_citry_builtin_token" and name in namespace:
            if value is namespace[name]:
                return
            msg = f"Cannot change {class_name}'s built-in component identity."
            raise AttributeError(msg)
        if name in {"class_id", "_class_id"} and "_definition_id" in namespace:
            if namespace.get("_class_id") is value:
                return
            msg = f"Cannot change {class_name}'s stable component class identity."
            raise AttributeError(msg)
        if name in {"definition_id", "_definition_id"} and "_definition_id" in namespace:
            if value is namespace["_definition_id"]:
                return
            msg = f"Cannot change {class_name}'s component definition identity."
            raise AttributeError(msg)
        if name in {"citry", "_citry_owner"} and "_citry_owner" in namespace:
            owner = namespace["_citry_owner"]
            if value is owner:
                return
            msg = (
                f"Cannot change {class_name}.citry after the component class is defined. "
                "Define a new component class for the other Citry instance."
            )
            raise AttributeError(msg)
        nested_names = namespace.get("_citry_nested_declaration_names")
        if isinstance(nested_names, frozenset) and name in nested_names:
            if namespace.get(name) is value:
                return
            msg = (
                f"Cannot rebind {class_name}.{name} after the component class is defined."
                " Define a new component subclass with a new nested declaration."
            )
            raise AttributeError(msg)
        super().__setattr__(name, value)

    def __delattr__(cls, name: str) -> None:  # noqa: N805
        """Keep the concrete component's owning Citry attribute present."""
        namespace = _static_class_dict(cls)
        class_name = _safe_class_text(cls, "__name__") or "Component"
        if name == "_citry_builtin_token" and name in namespace:
            msg = f"Cannot delete {class_name}'s built-in component identity."
            raise AttributeError(msg)
        if name in {"class_id", "_class_id"} and "_definition_id" in namespace:
            msg = f"Cannot delete {class_name}'s stable component class identity."
            raise AttributeError(msg)
        if name in {"definition_id", "_definition_id"} and "_definition_id" in namespace:
            msg = f"Cannot delete {class_name}'s component definition identity."
            raise AttributeError(msg)
        if name in {"citry", "_citry_owner"} and "_citry_owner" in namespace:
            msg = f"Cannot delete {class_name}.citry after the component class is defined."
            raise AttributeError(msg)
        nested_names = namespace.get("_citry_nested_declaration_names")
        if isinstance(nested_names, frozenset) and name in nested_names:
            msg = (
                f"Cannot delete {class_name}.{name} after the component class is defined."
                " Define a new component subclass with the desired declaration."
            )
            raise AttributeError(msg)
        super().__delattr__(name)

    @property
    def class_id(cls) -> str:  # noqa: N805
        """
        A stable, URL-safe identifier for this component class, e.g.
        ``"Table_a1b2c3"``: the class name plus a short hash of its full
        import path.

        Deterministic across processes and restarts (it is derived from the
        import path, not from object identity), so it can key cache entries
        and script URLs that one worker writes and another serves. Reverse
        lookup goes through ``Citry.get_component_by_class_id``.
        """
        cached = cast("str | None", _static_class_dict(cls).get("_class_id"))
        if cached is None:
            import_path = get_import_path(cls)
            digest = md5(import_path.encode(), usedforsecurity=False).hexdigest()[:6]
            class_name = _safe_class_text(cls, "__name__") or "Component"
            route_name = sub(r"[^A-Za-z0-9_-]+", "-", class_name).strip("-_") or "Component"
            cached = f"{route_name}_{digest}"
            type.__setattr__(cls, "_class_id", cached)
        return cached

    @property
    def definition_id(cls) -> str:  # noqa: N805
        """
        Return this exact component class generation's runtime identity.

        The token is assigned before class-created extension hooks run. It is
        preserved when the same class gains an alias or is re-registered, while
        defining a replacement class creates a different token even when both
        classes share a stable [`class_id`][citry.Component.class_id].

        Returns:
            A non-time-derived token intended only for same-process identity
            comparisons. It changes after a process restart.

        """
        return cast("str", _static_class_dict(cls)["_definition_id"])

    def __new__(  # noqa: PYI034
        mcs,
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, Any],
        *,
        _citry_builtin: object | None = None,
        _citry_internal: object | None = None,
        _citry_library_materialization: object | None = None,
    ) -> ComponentMeta:
        # Detect whether we're defining the Component base class itself
        # vs a user subclass like `class MyCard(Component): ...`.
        #
        # A class is an instance of its metaclass. So once Component is
        # created (with metaclass=ComponentMeta), `isinstance(Component,
        # ComponentMeta)` is True. Any subclass of Component will have
        # Component in its `bases`, and Component passes the isinstance
        # check.
        #
        # When ComponentMeta.__new__ runs for Component itself, none of
        # its bases (just `object`) are instances of ComponentMeta, so
        # the check is False and we skip registration.
        #
        # When it runs for `class MyCard(Component)`, bases contains
        # Component, which IS an instance of ComponentMeta, so the check
        # is True and we proceed with registration.
        is_component_subclass = any(isinstance(b, ComponentMeta) for b in bases)
        if not is_component_subclass:
            cls = cast("ComponentMeta", super().__new__(mcs, name, bases, attrs))
            type.__setattr__(cls, "_definition_id", _new_definition_id())
            if attrs.get("_citry_component_root", False):
                root_component = cast("type[Component]", cls)
                type.__setattr__(cls, "_citry_owner", root_component.citry)
            return cls

        library_definition = next((base for base in bases if base.__dict__.get(_DEFINITION_FLAG, False)), None)
        if library_definition is not None and _citry_library_materialization is not _MATERIALIZATION_TOKEN:
            msg = (
                f"Cannot bind library component {library_definition.__name__!r} by subclassing Component directly. "
                "Publish its ComponentLibrary through Citry.register_library()."
            )
            raise TypeError(msg)
        if library_definition is None and _citry_library_materialization is not None:
            raise TypeError("Library component materialization requires a LibraryComponent definition base.")
        if _citry_builtin is not None and _citry_internal is not None:
            raise TypeError("A component cannot be both a registered built-in and a private internal component.")

        reserved_identities = {"class_id", "_class_id", "definition_id", "_definition_id"} & attrs.keys()
        if reserved_identities:
            reserved = ", ".join(sorted(reserved_identities))
            msg = f"Component {name} cannot declare read-only identity field(s): {reserved}."
            raise ValueError(msg)

        # Setting both members of an asset pair (e.g. `template` and
        # `template_file`) on the same class is an error; fail at class
        # definition. See docs/design/asset_loading.md section 3.2.
        validate_asset_pairs(name, attrs)

        # Extensions replace nested declarations with effective runtime
        # classes later in this method. Keep the authored objects so every
        # consumer can resolve the same C3 chain after that replacement.
        authored_namespace = dict(attrs)

        cls = cast("type[Component]", super().__new__(mcs, name, bases, attrs))
        type.__setattr__(cls, "_definition_id", _new_definition_id())

        if _citry_builtin is not None:
            type.__setattr__(cls, "_citry_builtin_token", _citry_builtin)

        # Resolve the Citry instance from the explicit or inherited binding,
        # then stamp it onto this concrete class. The own immutable binding
        # prevents later base-class changes from moving a registered subclass.
        citry_instance = cls.citry
        type.__setattr__(cls, "citry", citry_instance)
        type.__setattr__(cls, "_citry_owner", citry_instance)

        # Extension config classes are synthesized for one engine during the
        # base component's class-created lifecycle. Reusing that concrete base
        # under another engine would carry the first engine's config into the
        # second before its hooks run. Packages define a fresh component tree
        # for each receiving engine instead.
        foreign_base = next(
            (
                base
                for base in bases
                if isinstance(base, ComponentMeta)
                and not base.__dict__.get("_citry_component_root", False)
                and base.__dict__.get("_citry_owner") is not citry_instance
            ),
            None,
        )
        if foreign_base is not None:
            msg = (
                f"Cannot define {name!r} for this Citry instance from component base "
                f"{foreign_base.__name__!r}, which belongs to another Citry instance."
            )
            raise ValueError(msg)

        extensions = citry_instance.extensions
        nested_names = {*_DATA_SCHEMA_NAMES, "Lint", "State", *(ext.class_name for ext in extensions._extensions)}
        _capture_nested_declarations(cls, authored_namespace, nested_names)
        type.__setattr__(cls, "_citry_nested_declaration_names", frozenset(nested_names))

        # Lint is configuration rather than render data, so validate its C3
        # declarations without converting it into a runtime dataclass.
        _validate_component_lint(cls)

        # Core schemas use the same declaration chain as extension configs.
        # Plain field classes become one slotted dataclass after composition;
        # explicit adapters such as Pydantic and NamedTuple keep their own
        # construction model.
        for data_class_name in _DATA_SCHEMA_NAMES:
            if _get_nested_class_declarations(cls, data_class_name):
                type.__setattr__(cls, data_class_name, _build_component_data_schema(cls, data_class_name))

        # Class-created hooks may define more components, so they and the final
        # registration share one lifecycle owner. Another thread can never see
        # only the extension setup for a class that has not registered yet.
        with citry_instance._component_class_lifecycle():
            # Let extensions rebuild their nested config classes as subclasses
            # of their Config base (e.g. ``class View:`` -> a subclass of the
            # view extension's Config), before registration.
            extensions.on_component_class_created(cls)
            extensions._init_component_class(cls)

            # Register with the Citry instance. Uses the class name (or
            # Component.name override) as the registration name; Citry.register()
            # handles normalization, duplicate detection, and registered hooks.
            if _citry_internal is not None:
                citry_instance._registry._authorize_internal(cls, _citry_internal)
            elif _citry_builtin is None:
                citry_instance.register(cls)
            else:
                citry_instance._register_builtin(cls, _citry_builtin)

        return cls

    # mypy ignores a metaclass __call__ return type, so it mistypes `MyComp()` as the class (pyright is correct).
    def __call__(cls, /, **kwargs: Any) -> CitryElement:  # type: ignore[override]  # noqa: N805
        """
        Intercept ``MyComp(title="Hi")`` to return a CitryElement.

        ``cls`` is positional-only (``/``) so a component may take a keyword
        argument named ``cls`` (for example an HTML ``class`` passed as
        ``MyComp(cls="card")``) without colliding with the metaclass's own
        first parameter.

        ``slots`` is a reserved input name: it is taken out of the kwargs and
        carried separately as the component's slot fills
        (``MyComp(title="Hi", slots={"header": ...})``), so a component cannot
        take a regular kwarg named ``slots``.

        In citry, calling a Component class is the **composition** phase.
        It creates a CitryElement that describes what to render, without
        rendering it yet. Actual Component instances are created later
        during the **rendering** phase via ``_create_instance()``.

        This is analogous to React's ``<MyComp title="Hi" />`` producing
        a RenderElement, not a rendered DOM node.
        """
        slots = kwargs.pop("slots", None)
        return CitryElement(cls, kwargs, slots)  # type: ignore[arg-type]

    def _create_instance(cls, **init_kwargs: Any) -> Component:  # noqa: N805
        """
        Create an actual Component instance (internal, for rendering).

        Bypasses ``__call__`` (which returns a CitryElement) by going
        through ``type.__call__`` directly. This is how the rendering
        pipeline creates real Component instances with render-time state
        (render_id, resolved context, etc.).

        Not part of the public API.
        """
        # In Python, writing `MyClass()` calls `type(MyClass).__call__(MyClass)`,
        # i.e. the metaclass's __call__. Our ComponentMeta.__call__ returns a
        # CitryElement. To create an actual instance, we skip our metaclass and
        # call type.__call__ directly, which is the base implementation that runs
        # cls.__new__ + cls.__init__ and returns a real instance of cls.
        defer_input_finalization = bool(init_kwargs.pop("_defer_input_finalization", False))
        token = _DEFER_INPUT_FINALIZATION.set(defer_input_finalization)
        try:
            return type.__call__(cls, **init_kwargs)  # type: ignore[return-value]
        finally:
            _DEFER_INPUT_FINALIZATION.reset(token)


class Component(metaclass=ComponentMeta):
    """
    Base class for all Citry components.

    A component is a reusable unit of UI defined by:

    - A **template** (Citry template syntax)
    - Optional **typed inputs** (via inner ``Kwargs``, ``Slots`` classes)
    - A **data method** that maps inputs to template variables

    Subclass this to define your own components. At minimum, set
    ``template`` (inline string) or ``template_file`` (path to file).
    """

    _citry_component_root: ClassVar[bool] = True
    _citry_owner: ClassVar[Citry]

    class_id: ClassVar[str]
    """Stable import-derived identity shared by reloads of this component path.

    The read-only value is suitable for routes and cross-process logical
    identity. Combine it with [`Citry.engine_id`][citry.Citry.engine_id] and
    ``definition_id`` when retained metadata must match one exact live class
    generation in the current process.
    """

    definition_id: ClassVar[str]
    """Opaque process-lifetime identity of this exact component class object.

    The read-only value exists before class-created extension hooks run. An
    alias or re-registration preserves it, while defining a replacement class
    creates a different value even when ``class_id`` remains the same.
    """

    citry: ClassVar[Citry] = citry
    """The Citry instance that owns this component class.

    Defaults to the module-level default instance. Set this inside the class
    body to assign a component to a specific instance. The binding cannot be
    changed or deleted after the class is defined. A subclass of a concrete
    component uses the same owner; define a fresh component tree when another
    engine needs its own copy.
    """

    transparent: ClassVar[bool] = False
    """Whether this component's output joins the surrounding component's
    serialization frame.

    A transparent component is structural rather than visual: its rendered
    output gets no ``data-cid-<id>`` marker and is not framed as a child
    component at serialize time. Used by built-ins like ``<c-provide>`` that
    only wrap content. Hooks, the render id, and dependency merging behave
    the same as for any component.
    """

    name: ClassVar[str | None] = None
    """Override the name under which this component is registered.

    By default, the class name is used (lowercased + kebab-case).
    Set this to register under a specific name instead::

        class MyWidget(Component):
            name = "fancy-widget"
            # registered as "fancy-widget", not "mywidget" / "my-widget"
    """

    template: ClassVar[str | None] = None
    """Inline template string (Citry template syntax).

    Mutually exclusive with ``template_file``. Read the loaded template with
    ``get_template()``.
    """

    template_file: ClassVar[str | None] = None
    """Path to a template file. Mutually exclusive with ``template``.

    Resolved relative to the directory of the class that declares the value
    first, then relative to the owning component's ``Citry(dirs=...)`` entries;
    absolute paths are used as-is. A subclass that inherits this declaration
    therefore keeps the declaring class's file location. A plain mixin can
    declare the path while the component still supplies the owning engine.
    """

    messages: ClassVar[str | None] = None
    """Inline source-locale Fluent messages for this component.

    Mutually exclusive with ``messages_file``. Declare the source language with
    ``I18n.messages_locale``. A registered message asset activates server
    source-mode translation for the complete engine catalog, even without
    engine i18n settings. Read the loaded source with ``get_messages()``.
    """

    messages_file: ClassVar[str | None] = None
    """Path to source-locale Fluent messages, resolved like ``template_file``.

    This has the same source-mode and ``I18n.messages_locale`` contract as
    ``messages``.
    """

    js: ClassVar[str | None] = None
    """Inline primary JS for this component. Mutually exclusive with
    ``js_file``. Read the loaded content with ``get_js()``."""

    js_file: ClassVar[str | None] = None
    """Path to the component's primary JS file. Mutually exclusive with
    ``js``. Resolved like ``template_file``."""

    css: ClassVar[str | None] = None
    """Inline primary CSS for this component.

    Mutually exclusive with ``css_file``. Citry adds these selectors to the
    page exactly as written, so they can style any matching element. Use class
    names specific to the component to avoid styling something else by
    accident. Values returned by ``css_data()`` become custom properties for
    one rendered use of the component. Read the loaded content with
    ``get_css()``.
    """

    css_file: ClassVar[str | None] = None
    """Path to the component's primary CSS file. Mutually exclusive with
    ``css``. Resolved like ``template_file``."""

    Cache: ClassVar[type | None] = None
    """Optional output-cache settings owned by the Cache extension.

    Define a nested ``Cache`` class to enable caching, set its TTL and version,
    or return additional variation values. Citry rebuilds the declaration on
    [`CacheConfig`][citry.CacheConfig] when it creates the component class.
    """

    Dependencies: ClassVar[type | None] = None
    """Optional secondary JavaScript and CSS assets.

    Define a nested ``Dependencies`` class with ``js``, ``css``, ``extend``,
    or ``local_files``. Read the normalized merged result with
    [`get_dependencies()`][citry.Component.get_dependencies]. Citry rebuilds
    the declaration on [`DependenciesConfig`][citry.DependenciesConfig].
    """

    I18n: ClassVar[type | None] = None
    """Optional per-component settings for the built-in i18n extension.

    Define ``client_messages`` here when browser code uses a finite dynamic
    message name that static analysis cannot discover. The instance-level
    [`i18n`][citry.Component.i18n] value provides translation, formatting,
    parsing, and the explicit locale context during a render.
    """

    Kwargs: ClassVar[type | None] = None
    """Optional typed keyword arguments.

    Define as a plain class with type annotations. The metaclass
    combines it with parent component declarations and converts the result to
    a dataclass (with slots) automatically::

        class Card(Component):
            class Kwargs:
                title: str
                body: str = ""
    """

    Slots: ClassVar[type | None] = None
    """Optional typed slot definitions, inherited like [`Kwargs`][citry.Component.Kwargs].

    Use [`SlotInput`][citry.SlotInput] for places where people can add content.
    A field without a default must be filled whenever the component is used.
    The ``required`` attribute on ``<c-slot>`` checks something different: it
    raises an error only if Citry renders that tag without content.
    """

    State: ClassVar[type | None] = None
    """Optional typed values that survive between server event calls.

    Define ``State`` as a plain nested class with type annotations. The Events
    extension combines inherited declarations and converts the result to a
    mutable, slotted dataclass automatically::

        class Search(Component):
            class State:
                query: str = ""
                page: int = 1

    State must contain only JSON-serializable values. By default, every field
    is readable and writable in the browser. Use ``_public`` to choose which
    fields the browser may read and ``_model`` to choose which public fields
    it may change. ``_storage`` is ``"signed"`` by default and may be set to
    ``"server"``. ``_max_bytes`` defaults to 8192 bytes, and ``_max_age``
    accepts a ``datetime.timedelta`` or ``None`` for no expiry.

    Citry starts State from same-named keyword arguments and field defaults.
    Define ``state_data(self, kwargs, slots)`` when the values need to be
    derived instead. Assign ``State = None`` on a subclass to stop inheriting
    its parent's State declaration.
    """

    Events: ClassVar[type | None] = None
    """Optional server event handlers for this component.

    Define ``Events`` as a nested class. Every public method is an event
    handler; underscore-prefixed methods and attributes are private helpers or
    configuration::

        class Counter(Component):
            class State:
                count: int = 0

            class Events:
                def increment(self, state):
                    state.count += 1

    Citry combines inherited ``Events`` declarations in component C3 order.
    A child method overrides a same-named parent method, while ``Events = None``
    stops inherited declarations. The built-in Events extension rebuilds the
    effective nested class on its runtime config base.

    A plain nested class works without imports. To type handler attributes such
    as ``self.state`` and ``self.request``, subclass the generic
    [`Events`][citry.Events] base and parameterize it with the component's State
    class. See [`event`][citry.ext.events.event] for per-handler options.
    """

    Lint: ClassVar[type | None] = None
    """Optional per-component template-lint settings.

    Define a nested ``Lint`` class with
    ``rule_unknown_template_variable`` and/or ``template_variables``. Nested
    declarations compose through the component C3 order. Assign ``None`` to
    return to the Citry instance's application lint policy.
    """

    TemplateData: ClassVar[type | None] = None
    """Optional typed template data output, inherited like [`Kwargs`][citry.Component.Kwargs]."""

    JsData: ClassVar[type | None] = None
    """Optional typed schema for the ``js_data()`` output. Like
    ``TemplateData``, it inherits through component C3 and a plain annotated
    class converts to a dataclass."""

    CssData: ClassVar[type | None] = None
    """Optional typed schema for the ``css_data()`` output. Like
    ``TemplateData``, it inherits through component C3 and a plain annotated
    class converts to a dataclass."""

    _citry_template: ClassVar[CitryTemplate | None] = None
    """Internal: this component's loaded template (the ``CitryTemplate``,
    which also carries the compiled form once first rendered), resolved once
    per class and cached here (the Citry analog of Django's
    ``Component._template``). Populated and read via ``__dict__`` by the
    asset loader and the render pipeline; read it through ``get_template()``,
    not directly.
    """

    # ----- Instance fields -----
    # Declared here for typing and documentation. Values are set in
    # __init__, which is called by _render_impl via _create_instance().
    # Not available during composition (MyComp() returns a CitryElement).

    id: str
    """Unique render ID for this component instance.

    A fresh ID is minted every time a CitryElement is rendered, so the
    same CitryElement rendered twice produces two distinct IDs.
    """

    kwargs: Any
    """The resolved keyword arguments.

    If the component defines a ``Kwargs`` dataclass, this is an instance
    of that class. Otherwise, a plain dict.
    """

    raw_kwargs: dict[str, Any]
    """The keyword arguments as a plain dict, even if a ``Kwargs``
    dataclass is defined. Useful when you need dict access regardless
    of typing.
    """

    slots: Any
    """The resolved slot fills, with every value normalized to a ``Slot``.

    If the component defines a ``Slots`` dataclass, this is an instance
    of that class. Otherwise, a plain dict.
    """

    raw_slots: dict[str, Slot]
    """The slot fills as a plain dict of ``Slot`` values, even if a ``Slots``
    dataclass is defined. Useful when you need dict access regardless
    of typing.
    """

    cache: CacheConfig
    """The Cache extension settings bound to this rendered component."""

    dependencies: DependenciesConfig
    """The Dependencies extension settings bound to this rendered component."""

    events: EventsConfig[Any]
    """The Events extension settings and event URL helper for this component."""

    i18n: I18nConfig
    """Translation, formatting, parsing, and locale access for this component."""

    parent: Component | None
    """The component that wrote this one into its template. None for a root
    component, and for one rendered standalone (e.g. an element handed into
    an expression as ``{{ element }}``).

    The link follows authorship, not slot placement: a component written
    inside a ``<c-fill>`` keeps the fill's author as its parent, no matter
    whose slot the content lands in. (This differs from Vue, whose
    ``$parent`` points at the slot host.) To ask "what am I rendered
    inside, slots included", use ``provide``/``inject``, which travels the
    render path and crosses slot boundaries.
    """

    root: Component
    """The component at the top of the ``parent`` chain (the same
    authorship rule as ``parent``).

    For root components, ``self.root is self``. Never None.
    """

    _provides_inherited: dict[str, Any]
    """Internal: the provide/inject entries this instance inherited from the
    render path above it (captured where its tag sits). Read by ``inject``.
    """

    _provides_own: dict[str, Any] | None
    """Internal: outgoing entries registered via ``provide`` or
    ``unprovide`` (``None`` until the first such call), passed on to
    descendants and never visible to this component's own ``inject``.
    """

    _component_tag_client_bindings: tuple[ComponentTagClientBindingRecord, ...]
    """Client bindings from the nested component tag, kept separate from kwargs."""

    _element_morph_metadata: _ElementMorphMetadata | None
    """Private metadata for the dynamic ordinary-element built-in."""

    _ownership_invocation_id: ComponentInvocationId | None
    """Internal invocation record selected for this rendered instance."""

    _ownership_graph: OwnershipGraph
    """Internal graph that owns this rendered instance's typed records."""

    def __init__(
        self,
        # The public field is `component.id`, so the parameter shadows the builtin on purpose.
        id: str | None = None,  # noqa: A002
        kwargs: Any = None,
        slots: Any = None,
        parent: Component | None = None,
        provides: dict[str, Any] | None = None,
    ) -> None:
        cls = type(self)

        # Render id precedence: an explicit id wins; then this instance's
        # id_generator override (CitrySettings.id_generator); then the built-in
        # generator. The built-in stays a module-level call so a test can swap
        # it for every instance at once by patching gen_render_id.
        if id is not None:
            render_id = id
        elif cls.citry.id_generator is not None:
            render_id = cls.citry.id_generator()
        else:
            render_id = gen_render_id()
        self.id = validate_render_id(render_id)

        # Normalize inputs to plain dicts. kwargs/slots may arrive as a dict,
        # a NamedTuple, or a dataclass (e.g. a typed `Kwargs`/`Slots`
        # instance), so run them through `to_dict`. The outer `dict(...)`
        # copies, so mutations during one render never leak back into a
        # CitryElement that may be rendered again.
        raw_kwargs: dict[str, Any] = dict(to_dict(kwargs)) if kwargs is not None else {}
        # Slot inputs (strings, functions, elements, renders, Slot instances)
        # additionally normalize to `Slot` values; `normalize_slot_fills`
        # builds a fresh dict, so the copy is preserved.
        # `element.slots` is `slots or {}`, so the common no-slots case is a falsy
        # empty dict, not None. A truthiness check skips the `normalize_slot_fills`
        # call (which would just rebuild an empty dict) for that case.
        raw_slots: dict[str, Slot] = normalize_slot_fills(to_dict(slots), component_name=cls.__name__) if slots else {}

        # raw_ variants are always plain dicts
        self.raw_kwargs = raw_kwargs
        self.raw_slots = raw_slots

        if _DEFER_INPUT_FINALIZATION.get():
            # During the real render path, input hooks receive and mutate the
            # authoritative raw mappings before typed defaults, factories, and
            # validators run. These temporary aliases are not final typed views.
            self.kwargs = raw_kwargs
            self.slots = raw_slots
        else:
            # Direct private _create_instance() callers do not run extension
            # hooks, so preserve their immediately typed historical behavior.
            self._finalize_inputs()

        self.parent = parent
        self.root = parent.root if parent is not None else self

        # The inherited mapping is shared, not copied: a component that
        # provides builds a new mapping instead of changing an existing one,
        # so sharing is safe.
        self._provides_inherited = provides if provides is not None else {}
        # Allocated lazily by `provide()` or `unprovide()`; most components
        # use neither. Readers guard with truthiness, so `None` reads the same
        # as an empty dict.
        self._provides_own = None
        self._element_morph_metadata = None

    def _finalize_inputs(self) -> None:
        """Normalize hook-mutated slots and publish both typed inputs atomically."""
        cls = type(self)
        raw_slots = normalize_slot_fills(self.raw_slots, component_name=cls.__name__) if self.raw_slots else {}
        typed_kwargs = cls.Kwargs(**self.raw_kwargs) if cls.Kwargs is not None else self.raw_kwargs
        typed_slots = cls.Slots(**raw_slots) if cls.Slots is not None else raw_slots
        self.raw_slots = raw_slots
        self.kwargs = typed_kwargs
        self.slots = typed_slots

    # The base returns kwargs, so a component's inputs are readable in its
    # template with no override. `slots` stays unused, hence its noqa.
    def template_data(
        self,
        kwargs: Any,
        slots: Any,  # noqa: ARG002
    ) -> dict[str, Any] | None:
        """
        Return the template variables.

        By default this returns ``kwargs``, so a component's inputs are usable
        in its template without an override: a ``Kwargs`` field named ``title``
        is available to the template as ``{{ title }}``. Override this to map
        the inputs to a different set of variables. The returned value may be a
        dict, a ``NamedTuple``, or the typed ``TemplateData`` instance, and a
        declared ``TemplateData`` validates and normalizes it either way.
        Schema defaults and coercions are materialized in the mapping that the
        template's expressions see.

        A returned variable wins over a ``template_globals`` entry of the same
        name, so an input shadows a same-named global (globals act as
        defaults). Unlike ``js_data`` and ``css_data``, which stay opt-in and
        return ``None`` by default, template variables never cross into the
        browser: they only make names resolvable to the template's own
        expressions.

        Args:
            kwargs: The keyword arguments passed to the component.
            slots: The slot fills passed to the component.

        Returns:
            A mapping of template variables. Defaults to the component's
            ``kwargs``; return your own mapping to override, or ``None`` for no
            variables.

        """
        return kwargs

    def js_data(
        self,
        kwargs: Any,  # noqa: ARG002
        slots: Any,  # noqa: ARG002
    ) -> dict[str, Any] | None:
        """
        Return the JS variables for this render.

        Override this to expose per-render data to the component's browser
        behavior. The dict is serialized to strict JSON, seeded into the
        component's Alpine scope, and delivered to its ``$component`` callback
        as ``data`` when one exists. Identical JSON is transported only once,
        while every rendered instance receives a fresh mutable value graph.
        Consumed by the built-in ``dependencies`` extension.

        Args:
            kwargs: The keyword arguments passed to the component.
            slots: The slot fills passed to the component.

        Returns:
            A dict of JS variables, or None for no variables.

        """
        return None

    def css_data(
        self,
        kwargs: Any,  # noqa: ARG002
        slots: Any,  # noqa: ARG002
    ) -> dict[str, Any] | None:
        """
        Return the CSS variables for this render.

        Override this to expose per-render values to the component's CSS
        (``Component.css``) as CSS custom properties: a returned
        ``{"row-color": "red"}`` is usable in the CSS as
        ``var(--row-color)``, scoped to this component's elements. Identical
        data across renders shares one generated stylesheet. Consumed by the
        built-in ``dependencies`` extension.

        Keys are custom-property name suffixes, without the leading ``--``.
        Values must be strings, finite numbers, or ``None``. Citry escapes
        quoted strings and rejects names or raw values that could escape the
        generated declaration. It checks structural containment, while the
        browser remains responsible for full CSS value grammar and whether a
        value is valid for the property that consumes it.

        Args:
            kwargs: The keyword arguments passed to the component.
            slots: The slot fills passed to the component.

        Returns:
            A dict of CSS variables, or None for no variables.

        """
        return None

    # The base implementation ignores its arguments; they are the documented
    # signature for subclasses to override, hence the noqa's.
    @classmethod
    def on_dependencies(
        cls,
        scripts: list[Dependency],  # noqa: ARG003
        styles: list[Dependency],  # noqa: ARG003
    ) -> tuple[list[Dependency], list[Dependency]] | None:
        """
        Hook to adjust this component's JS/CSS tags before they enter the page.

        Called at serialize time, once per rendered instance of this
        component, with the ``Script``/``Style`` entries this component
        contributes (its ``Dependencies`` entries and its own
        ``Component.js``/``css``). Return a ``(scripts, styles)`` pair to
        replace the lists, mutate them in place, or return ``None`` (the
        default) to keep them. Removing the component's own script entries
        can break the component's behavior in the browser; this hook is for
        adding attributes, reordering, or dropping entries you know are
        provided elsewhere.

        To adjust the *page-wide* lists instead (every component's tags,
        after de-duplication), implement an extension with an
        ``on_dependencies`` method (see
        ``citry.ext.dependencies.OnDependenciesContext``).
        """
        return None

    def on_render(self) -> RenderReplacement | OnRenderGenerator | None:
        """
        Hook to replace or post-process this component's rendered output.

        Called when this component is rendered without a successful component
        cache hit, after ``template_data`` and just before the template
        renders. A cache hit reuses the completed output and skips data
        methods, slots, the template, and this hook. Return ``None`` (the
        default) to render the template as usual. Return content to use it as
        the component's whole output instead; the template is then not
        rendered at all. Accepted content:

        - a ``str``, used as-is (NOT autoescaped: it is this component's own
          output, the same trust as its template; never concatenate untrusted
          input into it)
        - a composed element (``OtherComponent(title="hi")``), rendered in
          this component's place
        - an already-rendered ``CitryRender``, inlined
        - a ``Slot``, invoked with no data
        - a ``ComponentLike``, resolved against this component's Citry instance

        Because ``None`` means "no replacement", return ``""`` to output
        literally nothing.

        Everything the hook needs is on ``self``: ``kwargs``, ``slots``,
        ``parent``, ``inject()``. To pass data to the template, use
        ``template_data``; this hook is for replacing output. If the hook
        depends on ambient data while component caching is enabled, include
        that data in the cache variation inputs.

        For example, render a placeholder instead of the template when there
        is no data::

            class MyTable(Component):
                template = "<table>...</table>"

                def on_render(self):
                    if not self.raw_kwargs.get("rows"):
                        return "<p>No data</p>"
                    return None

        **Generator form.** Include a ``yield`` to also see the component's
        finished output, children included, and react to it - for example to
        catch a failing child (this is how error boundaries work)::

            class Guarded(Component):
                template = "..."

                def on_render(self):
                    # BEFORE: runs just before the template renders.
                    result, error = yield

                    # AFTER: result is the completed CitryRender, or None
                    # if rendering failed (then error is the exception).
                    if error is not None:
                        return "<p>Something went wrong</p>"
                    return None

        The protocol:

        - A bare ``yield`` (or ``yield None``) on the first yield means
          "render my template as usual"; yielding content means "use this as
          my output instead" (same accepted values as above).
        - The yield receives ``(result, error)`` once that output has fully
          settled: ``result`` is the live ``CitryRender`` (not a string; do
          not serialize it here unless you are replacing the output with the
          serialized form), or ``None`` when rendering failed, with ``error``
          set. Exactly one of the two is set.
        - You can yield any number of times; each ``yield <content>``
          replaces the output, renders it, and receives the new
          ``(result, error)``. A bare ``yield`` after the first answers
          immediately with the current result unchanged.
        - End with ``return <content>`` to set the final output, ``raise`` to
          make that the component's error, or plain ``return`` to keep the
          current result (an unhandled error keeps bubbling).
        """
        return None

    def provide(self, key: str, value: Any = MISSING, /, **data: Any) -> None:
        """
        Make one value available to this component's descendants.

        Any component rendered below this one (including components inside
        slot content rendered below it) can read the data with
        ``self.inject(key)``. The data does NOT enter the template variables;
        descendants opt in explicitly.

        Pass a direct positional value when the caller already owns the value
        object. Or pass keyword fields and Citry will freeze them into an
        immutable payload whose fields are read as attributes::

            class Page(Component):
                template = '<c-user-card />'

                def template_data(self, kwargs, slots):
                    self.provide("user_data", user=kwargs["user"])
                    return {}

            class UserCard(Component):
                template = '<div>{{ name }}</div>'

                def template_data(self, kwargs, slots):
                    return {"name": self.inject("user_data").user}

            class LocaleRoot(Component):
                def template_data(self, kwargs, slots):
                    self.provide("citry_i18n", kwargs.locale_context)
                    return {}

        In templates, the same thing is written with the ``<c-provide>``
        built-in component: ``<c-provide key="user_data" c-user="user">``.

        Args:
            key: Name the data is provided under (a non-empty identifier).
                Positional-only, so a data field named ``key`` is allowed.
            value: One direct value. It is passed through unchanged.
            **data: Fields Citry freezes into one immutable payload. A call
                cannot pass both a direct value and keyword fields.

        """
        validate_provide_key(key)
        if value is not MISSING and data:
            raise TypeError("Component.provide() accepts either one direct value or keyword fields, not both.")
        if self._provides_own is None:
            self._provides_own = {}
        self._provides_own[key] = make_provided(data) if value is MISSING else value

    def inject(self, key: str, default: Any = MISSING) -> Any:
        """
        Read data a component above this one provided under ``key``.

        The data must have been provided by a component on the render path
        above this one (via ``Component.provide`` or the ``<c-provide>``
        built-in); the nearest provider wins when the same key is provided
        twice. A component's own ``provide`` calls are visible to its
        descendants only, never to its own ``inject``.

        A direct value is returned unchanged. Keyword fields passed to
        ``provide()`` return an immutable payload with those fields as
        attributes: ``self.inject("user_data").user``. Injection works during
        ``template_data`` and keeps working after the render for as long as the
        component instance is kept.

        Args:
            key: The name the data was provided under.
            default: Returned when nothing was provided under ``key``. An
                explicit ``None`` works. Without a default, a missing key
                raises ``KeyError``.

        """
        return inject_value(self._provides_inherited, key, default, type(self).__name__)

    def unprovide(self, key: str, /) -> None:
        """
        Hide an inherited provide from this component's descendants.

        The component may still inject the inherited value itself. Components
        rendered below it observe the key as missing unless a nearer component
        provides a new value under the same key. Call this from
        ``template_data`` when content below a component boundary must establish
        a fresh context before using a compound child.

        Args:
            key: The provide key to hide below this component.

        """
        validate_provide_key(key)
        if self._provides_own is None:
            self._provides_own = {}
        self._provides_own[key] = BLOCKED

    @property
    def ancestors(self) -> Iterator[Component]:
        """
        All ancestor components, nearest first: the parent, then the parent's
        parent, up to and including the root. Empty for a root component.

        Useful to check where a component sits, e.g.::

            is_themed = any(isinstance(c, Theme) for c in self.ancestors)

        The chain follows who *wrote* the component, the same as ``parent``:
        a component written inside a ``<c-fill>`` has the fill's author as
        its parent, not the component whose slot rendered it. So the check
        above holds when ``Theme``'s own template renders this component;
        for "am I rendered inside a Theme, slots included", have ``Theme``
        ``provide`` a value and ``inject`` it here, which travels the render
        path and crosses slot boundaries.
        """
        current = self.parent
        while current is not None:
            yield current
            current = current.parent

    # ----- Asset accessors -----
    # Thin delegates into citry/assets.py and the built-in `dependencies`
    # extension. The class fields (template, js_file, ...) stay exactly as
    # declared; these classmethods return the resolved/loaded values, cached
    # once per class. They are accessors, not override points: supplying a
    # template dynamically by overriding get_template() is unsupported.
    # See docs/design/asset_loading.md section 3.1.

    @classmethod
    def get_template(cls) -> CitryTemplate | None:
        """
        The loaded template (a ``CitryTemplate``), or ``None`` for a
        template-less component. Resolved from ``template`` /
        ``template_file`` once per class; ``on_template_loaded`` applied.
        """
        return load_template(cls)

    @classmethod
    def get_js(cls) -> str | None:
        """
        The loaded primary JS content, or ``None``. Resolved from ``js`` /
        ``js_file`` once per class; ``on_js_loaded`` applied.
        """
        return load_js(cls)

    @classmethod
    def get_messages(cls) -> str | None:
        """Return the loaded ``messages`` / ``messages_file`` source, or ``None``."""
        return load_messages(cls)

    @classmethod
    def get_css(cls) -> str | None:
        """
        The loaded primary CSS content, or ``None``. Resolved from ``css`` /
        ``css_file`` once per class; ``on_css_loaded`` applied.
        """
        return load_css(cls)

    @classmethod
    def get_dependencies(cls) -> CitryDependencies:
        """
        The merged secondary assets from this component's (and, per
        ``Dependencies.extend``, its bases') nested ``Dependencies`` class.
        Owned by the built-in ``dependencies`` extension.
        """
        return _get_dependencies_impl(cls)

    @classmethod
    def reset_template(cls) -> None:
        """
        Clear this class's loaded template (and its compiled form and cached
        ``Const`` optimization results), so the next render re-reads it.
        Subclasses that inherit this template cache their own copies; reset
        them too (``Citry.get_components_for_file`` lists every class using
        a given file).
        """
        _reset_template_impl(cls)

    @classmethod
    def reset_files(cls) -> None:
        """
        Clear this class's loaded messages/JS/CSS (and, via the ``on_files_reset``
        hook, extension state such as the merged ``Dependencies``), so the
        next access re-reads them.
        """
        _reset_files_impl(cls)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"


_bind_component_runtime_type(Component)
