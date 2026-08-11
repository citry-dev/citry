"""Engine-neutral component definitions published as an explicit library."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import md5
from types import MappingProxyType, ModuleType
from typing import TYPE_CHECKING, Any, ClassVar, cast
from weakref import ReferenceType, ref

from citry.assets import validate_asset_pairs
from citry.citry import Citry  # noqa: TC001 - required by public runtime annotations
from citry.citry_element import CitryElement  # noqa: TC001 - required by public runtime annotations
from citry.citry_render import CitryRender  # noqa: TC001 - required by public runtime annotations
from citry.component_registry import (
    BUILTIN_COMPONENT_NAMES,
    STRUCTURAL_TAG_NAMES,
    _normalize_name,
    _pascal_to_kebab,
    _validate_component_name,
)
from citry.util.misc import get_import_path

if TYPE_CHECKING:
    from collections.abc import Iterator

    from citry.component import Component

    class _LibraryComponentAuthoringBase:
        """Checker-only instance surface available after materialization."""

        citry: ClassVar[Citry]
        id: str
        kwargs: Any
        slots: Any
        raw_kwargs: dict[str, Any]
        raw_slots: dict[str, Any]
        parent: Component | None
        root: Component

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any] | None: ...

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, Any] | None: ...

        def css_data(self, kwargs: Any, slots: Any) -> dict[str, Any] | None: ...

        @classmethod
        def on_dependencies(
            cls,
            scripts: list[Any],
            styles: list[Any],
        ) -> tuple[list[Any], list[Any]] | None: ...

        def on_render(self) -> Any: ...

        def provide(self, key: str, value: Any = ..., /, **data: Any) -> None: ...

        def inject(self, key: str, default: Any = ...) -> Any: ...

        def unprovide(self, key: str, /) -> None: ...

        @property
        def ancestors(self) -> Iterator[Component]: ...
else:
    # Component imports this module to obtain LibraryComponentMeta, so the
    # concrete type is bound once component.py has finished loading. Static
    # checkers still see the Component instance authoring surface above,
    # without treating an inert definition as a concrete Component class.
    Component = Any
    _LibraryComponentAuthoringBase = object

_LIBRARY_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_DEFINITION_FLAG = "_citry_is_library_component_definition"
_DEFINITION_ROOT_FLAG = "_citry_library_component_root"
_COMPONENT_ROOT_FLAG = "_citry_component_root"
_SEALED_FLAG = "_citry_library_component_sealed"
_MATERIALIZATION_TOKEN = object()

LibraryComponentIdentity = tuple[str, str]
"""The portable module and qualified-name identity of one definition."""


class LibraryComponentContextError(RuntimeError):
    """Report that a library invocation has no Citry instance to resolve through."""


class LibraryNotInstalled(RuntimeError):
    """Report that no active library installation can satisfy an invocation."""


class LibraryInstallationStale(RuntimeError):
    """Report that a retained installation is not the Citry instance's active generation."""


class LibraryManifestChanged(RuntimeError):
    """Report an incompatible manifest for an already installed library name."""


def _definition_identity(definition: type[LibraryComponent]) -> LibraryComponentIdentity:
    """Return the portable identity used to detect conflicting generations."""
    return definition.__module__, definition.__qualname__


def _component_names(definition: type[LibraryComponent]) -> tuple[str, ...]:
    """Return the registry names a materialized definition will claim."""
    configured_name = getattr(definition, "name", None)
    raw_name = configured_name or definition.__name__
    if not isinstance(raw_name, str):
        msg = f"Library component {definition.__name__}.name must be a string or None."
        raise TypeError(msg)
    _validate_component_name(raw_name)
    if configured_name:
        return (_normalize_name(raw_name),)
    return tuple(dict.fromkeys((_normalize_name(raw_name), _pascal_to_kebab(raw_name))))


def _predicted_class_id(definition: type[LibraryComponent]) -> str:
    """Calculate the class ID of a concrete class with definition provenance."""
    digest = md5(get_import_path(definition).encode(), usedforsecurity=False).hexdigest()[:6]
    route_name = re.sub(r"[^A-Za-z0-9_-]+", "-", definition.__name__).strip("-_") or "Component"
    return f"{route_name}_{digest}"


class LibraryComponentMeta(type):
    """Create inert library definitions whose calls defer engine selection."""

    def __new__(mcs, name: str, bases: tuple[type, ...], attrs: dict[str, Any], **kwargs: Any) -> type:
        has_definition_base = any(
            base.__dict__.get(_DEFINITION_FLAG, False) or base.__dict__.get(_DEFINITION_ROOT_FLAG, False)
            for base in bases
        )
        has_component_base = any(getattr(base, _COMPONENT_ROOT_FLAG, False) for base in bases)
        is_root = attrs.get(_DEFINITION_ROOT_FLAG, False) is True
        is_definition = has_definition_base and not has_component_base and not is_root

        if is_definition:
            reserved = {
                "citry",
                "class_id",
                "definition_id",
                "_citry_owner",
                "_class_id",
                "_definition_id",
            } & attrs.keys()
            if reserved:
                rendered = ", ".join(sorted(reserved))
                msg = f"Library component {name} cannot declare engine-specific field(s): {rendered}."
                raise ValueError(msg)
            validate_asset_pairs(name, attrs)

        cls = super().__new__(mcs, name, bases, attrs, **kwargs)
        type.__setattr__(cls, _DEFINITION_FLAG, is_definition)
        return cls

    def __setattr__(cls, name: str, value: Any) -> None:
        """Keep published definition behavior stable across installed classes."""
        is_sealed_definition = cls.__dict__.get(_DEFINITION_FLAG, False) and cls.__dict__.get(_SEALED_FLAG, False)
        if is_sealed_definition:
            msg = (
                f"Cannot change published library component {cls.__name__}.{name}. "
                "Define a new component class and manifest generation."
            )
            raise AttributeError(msg)
        super().__setattr__(name, value)

    def __delattr__(cls, name: str) -> None:
        """Keep fields present on a published definition."""
        is_sealed_definition = cls.__dict__.get(_DEFINITION_FLAG, False) and cls.__dict__.get(_SEALED_FLAG, False)
        if is_sealed_definition:
            msg = (
                f"Cannot delete published library component {cls.__name__}.{name}. "
                "Define a new component class and manifest generation."
            )
            raise AttributeError(msg)
        super().__delattr__(name)

    def __call__(cls, /, **kwargs: Any) -> LibraryComponentInvocation:
        """Return a deferred invocation while keeping ``slots`` separate."""
        if cls.__dict__.get(_DEFINITION_ROOT_FLAG, False):
            raise TypeError("LibraryComponent is an abstract publishing base and cannot be called directly.")
        if not cls.__dict__.get(_DEFINITION_FLAG, False):
            return cast("LibraryComponentInvocation", super().__call__(**kwargs))
        slots = kwargs.pop("slots", None)
        if slots is None:
            slot_values: Mapping[str, Any] = {}
        elif isinstance(slots, Mapping):
            slot_values = slots
        else:
            msg = f"{cls.__name__}() slots must be a mapping or None; got {type(slots).__name__}."
            raise TypeError(msg)
        return LibraryComponentInvocation(
            definition=cast("type[LibraryComponent]", cls),
            kwargs=MappingProxyType(dict(kwargs)),
            slots=MappingProxyType(dict(slot_values)),
        )


class LibraryComponent(_LibraryComponentAuthoringBase, metaclass=LibraryComponentMeta):
    """
    Define a component once for materialization into multiple Citry instances.

    A subclass has the same authored surface as [`Component`][citry.Component]:
    templates, methods, nested schemas, extension declarations, and assets all
    live on the class. Defining it has no registry side effects. Calling it
    returns a [`LibraryComponentInvocation`][citry.LibraryComponentInvocation]
    that resolves through the Citry instance active at render time.
    """

    _citry_library_component_root: ClassVar[bool] = True
    name: ClassVar[str | None] = None
    """Optional explicit registry name, with the same behavior as ``Component.name``."""


@dataclass(frozen=True, slots=True)
class LibraryComponentInvocation:
    """
    Remember one engine-neutral component call until rendering selects Citry.

    Attributes:
        definition: The exact inert definition object that was called.
        kwargs: A read-only copy of the component keyword arguments.
        slots: A read-only copy of the reserved slot-fill mapping.

    """

    definition: type[LibraryComponent]
    kwargs: Mapping[str, Any]
    slots: Mapping[str, Any]

    @property
    def identity(self) -> LibraryComponentIdentity:
        """Return the definition's logical source identity for diagnostics."""
        return _definition_identity(self.definition)

    def __citry_element__(self, citry: Citry, /) -> CitryElement:
        """Compose this invocation through ``citry``'s active installation."""
        return self.resolve(citry)

    def resolve(self, citry: Citry) -> CitryElement:
        """
        Resolve this invocation to a concrete component element.

        Args:
            citry: The Citry instance whose installed concrete class should be
                used.

        Returns:
            A normal [`CitryElement`][citry.CitryElement] associated with the
            supplied instance.

        Raises:
            TypeError: If ``citry`` is not a Citry instance.
            LibraryNotInstalled: If no active installation contains this
                exact definition generation.

        """
        from citry.citry import Citry  # noqa: PLC0415

        if not isinstance(citry, Citry):
            msg = "LibraryComponentInvocation.resolve() requires a Citry instance."
            raise TypeError(msg)
        component_class = citry._resolve_library_component(self.definition)
        component_factory = cast("Any", component_class)
        return cast("CitryElement", component_factory(**dict(self.kwargs), slots=dict(self.slots)))

    def render(
        self,
        *,
        citry: Citry | None = None,
        template_globals: Mapping[str, Any] | None = None,
        provides: Mapping[str, Any] | None = None,
    ) -> CitryRender:
        """
        Render this invocation through an explicit Citry instance.

        Args:
            citry: The instance with the component's library installed.
            template_globals: Values added to this render's template globals.
            provides: Values the root and its rendered descendants may read
                with ``inject()``.

        Returns:
            The resulting deferred render tree.

        Raises:
            LibraryComponentContextError: If ``citry`` is omitted. Contextual
                resolution is supplied automatically only when the invocation
                appears inside another component tree.

        """
        if citry is None:
            msg = (
                "Rendering a library component invocation requires a Citry instance. "
                "Pass citry=app outside a component tree, or place the invocation in "
                "a component template where Citry can resolve it contextually."
            )
            raise LibraryComponentContextError(msg)
        return self.resolve(citry).render(template_globals=template_globals, provides=provides)

    def __str__(self) -> str:
        return str(self.render())


@dataclass(frozen=True, slots=True)
class ComponentLibrary:
    """
    Declare one ordered, engine-neutral collection of library components.

    Construct the manifest after all class decorators have completed. A valid
    manifest seals its definitions against later class-attribute mutation.

    Attributes:
        name: Stable lowercase package identity inside one Citry instance.
        components: Definitions in their deterministic registration order.
        required_extensions: Exact extension names required before any class
            is materialized.

    """

    name: str
    components: Sequence[type[LibraryComponent]]
    required_extensions: Sequence[str] = ()
    _signature: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Normalize and validate the complete portable manifest."""
        if not isinstance(self.name, str) or not _LIBRARY_NAME_RE.fullmatch(self.name):
            msg = (
                "ComponentLibrary.name must start with a lowercase letter or digit and contain "
                "only lowercase letters, digits, dots, underscores, or hyphens."
            )
            raise ValueError(msg)

        components = _ordered_manifest_values(self.components, field_name="components")
        requirements = _ordered_manifest_values(self.required_extensions, field_name="required_extensions")
        object.__setattr__(self, "components", components)
        object.__setattr__(self, "required_extensions", requirements)
        if not components:
            raise ValueError("ComponentLibrary.components must contain at least one definition.")

        definition_identities: set[LibraryComponentIdentity] = set()
        seen_objects: set[type[LibraryComponent]] = set()
        claimed_names: dict[str, type[LibraryComponent]] = {}
        class_ids: dict[str, type[LibraryComponent]] = {}
        signature_components: list[tuple[LibraryComponentIdentity, tuple[str, ...], str]] = []
        for definition in components:
            is_definition = isinstance(definition, LibraryComponentMeta) and definition.__dict__.get(
                _DEFINITION_FLAG, False
            )
            if not is_definition:
                msg = "ComponentLibrary.components must contain LibraryComponent definition classes."
                raise TypeError(msg)
            if definition in seen_objects:
                msg = f"ComponentLibrary {self.name!r} contains {definition.__name__!r} more than once."
                raise ValueError(msg)
            seen_objects.add(definition)

            identity = _definition_identity(definition)
            if identity in definition_identities:
                rendered = ".".join(identity)
                msg = f"ComponentLibrary {self.name!r} contains duplicate definition identity {rendered!r}."
                raise ValueError(msg)
            definition_identities.add(identity)

            names = _component_names(definition)
            for component_name in names:
                if component_name in STRUCTURAL_TAG_NAMES or component_name in BUILTIN_COMPONENT_NAMES:
                    msg = f"Library component {definition.__name__!r} claims reserved name {component_name!r}."
                    raise ValueError(msg)
                previous = claimed_names.get(component_name)
                if previous is not None:
                    msg = (
                        f"Library components {previous.__name__!r} and {definition.__name__!r} "
                        f"both claim registry name {component_name!r}."
                    )
                    raise ValueError(msg)
                claimed_names[component_name] = definition

            class_id = _predicted_class_id(definition)
            previous_id = class_ids.get(class_id)
            if previous_id is not None:
                msg = (
                    f"Library components {previous_id.__name__!r} and {definition.__name__!r} "
                    f"share stable class ID {class_id!r}."
                )
                raise ValueError(msg)
            class_ids[class_id] = definition
            signature_components.append((identity, names, class_id))

        seen_requirements: set[str] = set()
        for requirement in requirements:
            if (
                not isinstance(requirement, str)
                or not requirement.isidentifier()
                or not requirement.islower()
                or requirement in seen_requirements
            ):
                msg = "ComponentLibrary.required_extensions must contain unique lowercase Python identifiers."
                raise ValueError(msg)
            seen_requirements.add(requirement)

        signature: tuple[object, ...] = (self.name, tuple(signature_components), requirements)
        object.__setattr__(self, "_signature", signature)
        for definition in components:
            for base in definition.__mro__:
                if base is LibraryComponent:
                    break
                if base.__dict__.get(_DEFINITION_FLAG, False):
                    type.__setattr__(base, _SEALED_FLAG, True)


def _ordered_manifest_values(value: Sequence[Any], *, field_name: str) -> tuple[Any, ...]:
    """Copy one explicitly ordered manifest collection or reject ambiguous inputs."""
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        msg = f"ComponentLibrary.{field_name} must be an ordered, non-string sequence."
        raise TypeError(msg)
    return tuple(value)


@dataclass(frozen=True, slots=True)
class LibraryInstallation:
    """
    An immutable handle to one committed generation installed into Citry.

    Retaining this handle does not make it active after
    [`Citry.clear()`][citry.Citry.clear]. Component access validates the exact
    active generation before returning a class.

    Attributes:
        library: The manifest used for this generation.
        engine_id: The receiving Citry instance's stable runtime identity.

    """

    library: ComponentLibrary
    engine_id: str
    _citry_ref: ReferenceType[Citry] = field(repr=False)
    _components: Mapping[type[LibraryComponent], type[Component]] = field(repr=False)

    @property
    def is_active(self) -> bool:
        """Return whether this is still the Citry instance's exact active record."""
        citry = self._citry_ref()
        return citry is not None and citry._is_library_installation_active(self)

    @property
    def classes(self) -> tuple[type[Component], ...]:
        """Return concrete component classes in manifest order if this record is active."""
        citry = self._active_citry()
        citry._validate_library_installation(self)
        return tuple(self._components[item] for item in self.library.components)

    @property
    def definitions(self) -> tuple[type[LibraryComponent], ...]:
        """Return the engine-neutral definitions in manifest order."""
        return cast("tuple[type[LibraryComponent], ...]", self.library.components)

    def component(self, definition: type[LibraryComponent]) -> type[Component]:
        """
        Return the installed concrete class for an exact definition generation.

        Args:
            definition: One exact definition object from this manifest.

        Returns:
            The concrete Component class associated with this installation.

        Raises:
            LibraryInstallationStale: If the Citry instance was cleared or a
                newer installation generation is active.
            KeyError: If the definition is outside this library.

        """
        citry = self._active_citry()
        if definition not in self._components:
            rendered = ".".join(_definition_identity(definition))
            msg = f"Component library {self.library.name!r} has no definition {rendered!r}."
            raise KeyError(msg)
        component_class = citry._resolve_library_component(definition, installation=self)
        if self._components[definition] is not component_class:
            msg = f"Component library {self.library.name!r} has inconsistent installed component state."
            raise LibraryInstallationStale(msg)
        return component_class

    def __getitem__(self, definition: type[LibraryComponent]) -> type[Component]:
        """Return ``component(definition)`` for concise advanced access."""
        return self.component(definition)

    def _active_citry(self) -> Citry:
        """Return the live owner or report a retired installation handle."""
        citry = self._citry_ref()
        if citry is None or not citry._is_library_installation_active(self):
            msg = f"Component library installation {self.library.name!r} is no longer active."
            raise LibraryInstallationStale(msg)
        return citry


def _coerce_component_library(value: ComponentLibrary | ModuleType) -> ComponentLibrary:
    """Resolve a manifest directly or through a package's conventional attribute."""
    if isinstance(value, ComponentLibrary):
        return value
    if isinstance(value, ModuleType):
        manifest = getattr(value, "__citry_library__", None)
        if isinstance(manifest, ComponentLibrary):
            return manifest
        msg = f"Module {value.__name__!r} must expose a ComponentLibrary as __citry_library__."
        raise TypeError(msg)
    msg = "register_library() requires a ComponentLibrary or module exposing __citry_library__."
    raise TypeError(msg)


def _materialize_library_component(
    definition: type[LibraryComponent],
    citry: Citry,
) -> type[Component]:
    """Create and register one concrete Component while preserving source provenance."""
    from citry.component import Component, ComponentMeta  # noqa: PLC0415

    namespace = {
        "__doc__": definition.__doc__,
        "__module__": definition.__module__,
        "__qualname__": definition.__qualname__,
        "citry": citry,
    }
    concrete = ComponentMeta(
        definition.__name__,
        (definition, Component),
        namespace,
        _citry_library_materialization=_MATERIALIZATION_TOKEN,
    )
    return cast("type[Component]", concrete)


def _new_library_installation(
    citry: Citry,
    library: ComponentLibrary,
    components: Mapping[type[LibraryComponent], type[Component]],
) -> LibraryInstallation:
    """Build the immutable record committed by ``Citry.register_library``."""
    return LibraryInstallation(
        library=library,
        engine_id=citry.engine_id,
        _citry_ref=ref(citry),
        _components=MappingProxyType(dict(components)),
    )


def _bind_component_runtime_type(component_type: type[Component]) -> None:
    """Complete public runtime annotations after component.py finishes importing."""
    globals()["Component"] = component_type


__all__ = [
    "ComponentLibrary",
    "LibraryComponent",
    "LibraryComponentContextError",
    "LibraryComponentInvocation",
    "LibraryInstallation",
    "LibraryInstallationStale",
    "LibraryManifestChanged",
    "LibraryNotInstalled",
]
