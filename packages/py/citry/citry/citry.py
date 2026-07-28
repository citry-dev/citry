"""
The Citry global instance - scopes all component state.

A Citry instance owns a component registry, settings, and transient
rendering state. Every Component subclass is assigned to a Citry instance,
either by declaring ``citry = my_citry`` in its class body or by using the
default instance.

Example:
    Using the default instance (most common)::

        from citry import Component

        class MyTable(Component):
            template = "<table>...</table>"

    Using a custom instance::

        from citry import Citry, Component

        my_citry = Citry()

        class MyTable(Component):
            citry = my_citry
            template = "<table>...</table>"

    Isolated instances for testing::

        def test_my_component():
            test_citry = Citry()
            # Components registered here don't leak to other tests
            class MyTable(Component):
                citry = test_citry
                template = "..."

"""

from __future__ import annotations

import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from types import ModuleType  # noqa: TC003 - required by register_library's public runtime annotation
from typing import TYPE_CHECKING, Any, Literal
from weakref import WeakValueDictionary, ref

from citry._class_introspection import _static_class_dict
from citry._component_introspection import _build_component_catalog, _build_component_info
from citry.autodiscovery import import_component_modules
from citry.cache import CitryCache, InMemoryCache
from citry.component_registry import (
    BUILTIN_COMPONENT_NAMES,
    AlreadyRegistered,
    NotRegistered,
    _ComponentRegistry,
    _normalize_name,
    _RegistryState,
)
from citry.constness import ConstBodyCache
from citry.extension import ExtensionManager
from citry.introspection import _new_engine_id
from citry.settings import CitrySettings
from citry.tag_rules import build_tag_rules

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
    from types import FrameType
    from weakref import ReferenceType

    from citry.component import Component
    from citry.extension import Extension, ExtensionCommand
    from citry.introspection import ComponentCatalog, ComponentInfo
    from citry.library_component import (
        ComponentLibrary,
        LibraryComponent,
        LibraryComponentIdentity,
        LibraryInstallation,
    )
    from citry.util.routing import URLRoute
    from citry_core.template_parser import TagRules


@dataclass(frozen=True, slots=True)
class _RegistrationState:
    """Citry-owned state restored when initialization fails partway through."""

    registry: _RegistryState
    classes_by_id: dict[str, type[Component]]
    file_index: dict[str, tuple[ReferenceType[type[Component]], ...]]
    tag_rules_cache: dict[str, TagRules] | None
    discovered: bool
    library_installations: dict[str, LibraryInstallation]
    library_components: dict[type[LibraryComponent], type[Component]]
    library_definition_identities: dict[LibraryComponentIdentity, type[LibraryComponent]]
    library_definitions_by_class: dict[type[Component], type[LibraryComponent]]


@dataclass(frozen=True, slots=True)
class _RegistrationRecord:
    """One registry mutation during a module import and its active modules."""

    name: str
    comp_cls: type[Component]
    origin_modules: frozenset[str]
    added: bool


# Benefits over module-level globals:
# - All transient state has a maximum lifetime bound to the Citry
#     instance. Deleting the instance cleans up everything.
# - Tests can use isolated instances for clean state.
# - Multiple independent component trees can coexist.
class Citry:
    """
    Global instance that scopes all component state.

    A Citry instance owns:

    - A private component-name registry reached through the engine's methods
    - Settings (to be expanded as the engine grows)
    - Transient rendering state

    All Component classes are assigned to a Citry instance at class
    definition time. If no instance is specified, the default instance
    is used.

    Call :meth:`initialize` after startup-time registration and before a
    server starts request threads. Lazy initialization remains available, but
    a thread that encounters lifecycle work owned by another thread receives
    [`CitryLifecycleInProgress`][citry.CitryLifecycleInProgress].

    """

    def __init__(
        self,
        extensions: Sequence[type[Extension] | Extension | str] = (),
        extensions_defaults: Mapping[str, Mapping[str, Any]] | None = None,
        dirs: Sequence[str | Path] = (),
        cache: CitryCache | str | None = None,
        sandbox_expressions: bool = True,
        autodiscover: bool = True,
        mode: Literal["production", "development"] = "production",
        template_globals: Mapping[str, Any] | None = None,
        id_generator: Callable[[], str] | str | None = None,
        secret: str | list[str] | None = None,
        event_result_resolvers: Sequence[Any] = (),
        event_payload_codecs: Sequence[Any] = (),
    ) -> None:
        self._engine_id = _new_engine_id()
        # CitrySettings.__post_init__ copies every field into its immutable
        # stored shape (tuples, Path conversion and absolute-path validation for
        # dirs, fresh dict copies), so this path and a direct CitrySettings(...)
        # produce identical settings. Here we only fill in defaults for the None
        # values this friendlier public constructor accepts.
        self.settings = CitrySettings(
            extensions=extensions,
            extensions_defaults=extensions_defaults if extensions_defaults is not None else {},
            # dirs accepts str or Path entries; __post_init__ converts them to
            # tuple[Path, ...] (validating they are absolute), which mypy cannot
            # follow across the dataclass boundary.
            dirs=dirs,  # type: ignore[arg-type]
            cache=cache,
            sandbox_expressions=sandbox_expressions,
            autodiscover=autodiscover,
            mode=mode,
            id_generator=id_generator,
            template_globals=template_globals if template_globals is not None else {},
            secret=secret,
            event_result_resolvers=event_result_resolvers,
            event_payload_codecs=event_payload_codecs,
        )

        # The live template globals: variables injected into every component's
        # template variables on render (see CitrySettings.template_globals).
        # Seeded from settings as a separate dict, so changing them on the
        # instance (citry.template_globals["x"] = ...) leaves the construction
        # mapping untouched, and the default instance - created at import, before
        # user code runs - can still be configured after the fact.
        self.template_globals: dict[str, Any] = dict(self.settings.template_globals)

        # The build environment (dev_prod_mode.md), validated in the settings.
        # Read directly off the instance by the pieces that vary by environment:
        # the built-in extension set below, and the client ownership graph.
        self.mode: Literal["production", "development"] = self.settings.mode

        # The cache backend (docs/design/dependencies.md section 10): derived
        # content such as the dependencies extension's processed JS/CSS lives
        # here. Built from the settings spec; defaults to a per-instance
        # in-memory cache.
        self.cache: CitryCache = self._build_cache(cache)
        # The override for the per-render component id, resolved from the
        # settings spec to a live callable. None means "use the built-in
        # generator" (the fallback lives at the mint site in component.py).
        self.id_generator: Callable[[], str] | None = self._resolve_id_generator(id_generator)
        # Private component-name storage also coordinates lifecycle state and
        # creates the built-ins (<c-provide>, ...) on first use.
        self._registry = _ComponentRegistry(self)

        # Autodiscovery (see autodiscover()). When the autodiscover setting is
        # on, the component modules under settings.dirs are imported the first
        # time a component is looked up, so their classes register themselves.
        # _discovered records that the scan completed for the current registry;
        # clear() resets it so the next lookup rebuilds the registry (the scan
        # re-registers components from already-imported modules, see
        # citry.autodiscovery). _discovering guards the case where registering a
        # discovered component routes back through this instance (the guard makes
        # that re-entrant call a no-op, not a nested scan).
        self._discovered: bool = False
        self._discovering: bool = False

        # When a component is rendered and some of its template data is
        # wrapped in `Const()` ("this value is the same on every render"),
        # the parts of the template that depend only on those values are
        # computed once and stored here, so later renders reuse them instead
        # of re-computing. One entry per component class and combination of
        # Const values; old entries are dropped when the cache is full.
        # See citry/constness.py.
        self._const_body_cache = ConstBodyCache()

        # Parse-time validation rules derived from the registered components'
        # Kwargs/Slots declarations (see citry/tag_rules.py). Built on first
        # template parse; invalidated whenever the registry changes.
        self._tag_rules_cache: dict[str, TagRules] | None = None

        # File-to-component reverse index: absolute file path -> weakrefs to the
        # component classes whose assets resolved to that file. This is what
        # hot reload queries: a watcher (or test) asks get_components_for_file()
        # which classes to reset when a file changes. See
        # docs/design/asset_loading.md section 8.
        self._file_index: dict[str, list[ReferenceType[type[Component]]]] = {}

        # Guards _file_index so a watcher thread can read it (and prune dead
        # weakrefs) while a render thread registers a newly resolved file. The
        # reset caches the invalidation then drives are already thread-safe on
        # their own (the const-body cache holds its own lock).
        self._index_lock = threading.Lock()

        # class_id -> component class reverse index, maintained at registration.
        # This is how the script-serving endpoint finds the class a cached
        # JS/CSS script belongs to (docs/design/dependencies.md section 4.1).
        # Weak values, so unregistered classes can be garbage-collected.
        self._classes_by_id: WeakValueDictionary[str, type[Component]] = WeakValueDictionary()

        # Set only around one autodiscovered module import. Registry mutations
        # append their exact names so a failed parent import can retain work done
        # by dependency modules that Python cached successfully.
        self._registration_journal: list[_RegistrationRecord] | None = None

        # An atomic registration block publishes new classes only. Tracking the
        # nesting depth lets unregister() reject removals whose cache and hook
        # effects are intentionally outside the registration snapshot.
        self._atomic_registration_depth = 0

        # Published component libraries are part of the same lifecycle state
        # as the registry. Definitions and concrete classes are both exact
        # process-local keys; portable identities detect conflicting reloads.
        self._library_installations: dict[str, LibraryInstallation] = {}
        self._library_components: dict[type[LibraryComponent], type[Component]] = {}
        self._library_definition_identities: dict[LibraryComponentIdentity, type[LibraryComponent]] = {}
        self._library_definitions_by_class: dict[type[Component], type[LibraryComponent]] = {}

        # Where this instance's routes are mounted in the host web app, e.g.
        # "/citry". Recorded by the web-integration adapters' mount() call
        # (docs/design/dependencies.md section 9.3); None means no
        # integration is mounted, and URL building raises with guidance.
        self._mounted_prefix: str | None = None

        # The extension/hook system, scoped to this Citry instance (DJC #1413).
        # Extensions are present from construction, so hooks fire immediately.
        self.extensions = ExtensionManager(self, self.settings.extensions)
        self.extensions.on_extension_created()

    def __repr__(self) -> str:
        return f"Citry(components={len(self._registry)})"

    def __setattr__(self, name: str, value: Any) -> None:
        """Keep this engine's process-lifetime identity stable."""
        if name in {"engine_id", "_engine_id"} and "_engine_id" in self.__dict__:
            if value is self.__dict__["_engine_id"]:
                return
            msg = "Cannot change a Citry instance's engine identity."
            raise AttributeError(msg)
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        """Keep this engine's process-lifetime identity present."""
        if name in {"engine_id", "_engine_id"} and "_engine_id" in self.__dict__:
            msg = "Cannot delete a Citry instance's engine identity."
            raise AttributeError(msg)
        super().__delattr__(name)

    def __copy__(self) -> None:
        """Reject shallow copies, which cannot preserve engine ownership."""
        msg = "Citry instances cannot be copied. Construct a new Citry instance instead."
        raise TypeError(msg)

    def __deepcopy__(self, memo: dict[int, Any]) -> None:
        """Reject deep copies, which cannot safely clone extensions and caches."""
        del memo
        msg = "Citry instances cannot be copied. Construct a new Citry instance instead."
        raise TypeError(msg)

    @property
    def engine_id(self) -> str:
        """
        Return this engine's opaque process-lifetime identity token.

        The value is stable for this ``Citry`` instance, including across
        [`clear()`][citry.Citry.clear], and differs for another instance in the
        same process. Component-introspection consumers combine it with
        [`Component.class_id`][citry.Component.class_id] and
        [`Component.definition_id`][citry.Component.definition_id] when they
        need to confirm that retained metadata still describes an exact live
        component generation.

        Returns:
            A non-time-derived token intended only for same-process identity
            comparisons. It changes after a process restart.

        """
        return self._engine_id

    def _snapshot_registration_state(self) -> _RegistrationState:
        """Copy the engine-owned state that component registration mutates."""
        with self._index_lock:
            file_index = {path: tuple(refs) for path, refs in self._file_index.items()}
        return _RegistrationState(
            registry=self._registry._snapshot_state(),
            classes_by_id=dict(self._classes_by_id.items()),
            file_index=file_index,
            tag_rules_cache=self._tag_rules_cache,
            discovered=self._discovered,
            library_installations=dict(self._library_installations),
            library_components=dict(self._library_components),
            library_definition_identities=dict(self._library_definition_identities),
            library_definitions_by_class=dict(self._library_definitions_by_class),
        )

    def _restore_registration_state(
        self,
        state: _RegistrationState,
        *,
        preserve_file_classes: set[type[Component]] | None = None,
    ) -> None:
        """Restore an internal snapshot without firing compensating hooks."""
        self._registry._restore_state(state.registry)
        self._classes_by_id.clear()
        self._classes_by_id.update(state.classes_by_id)
        self._tag_rules_cache = state.tag_rules_cache
        self._discovered = state.discovered
        self._library_installations.clear()
        self._library_installations.update(state.library_installations)
        self._library_components.clear()
        self._library_components.update(state.library_components)
        self._library_definition_identities.clear()
        self._library_definition_identities.update(state.library_definition_identities)
        self._library_definitions_by_class.clear()
        self._library_definitions_by_class.update(state.library_definitions_by_class)
        self._restore_component_file_index(state.file_index, preserve_classes=preserve_file_classes)

    def _restore_component_file_index(
        self,
        snapshot: dict[str, tuple[ReferenceType[type[Component]], ...]],
        *,
        preserve_classes: set[type[Component]] | None = None,
    ) -> None:
        """Restore indexed files while retaining concurrent loads for active classes."""
        active_classes = set(self._classes_by_id.values())
        if preserve_classes:
            active_classes.update(preserve_classes)
        with self._index_lock:
            current = {path: tuple(refs) for path, refs in self._file_index.items()}
            restored: dict[str, list[ReferenceType[type[Component]]]] = {}
            for path in dict.fromkeys((*snapshot, *current)):
                refs: list[ReferenceType[type[Component]]] = []
                seen: set[type[Component]] = set()
                for comp_ref in snapshot.get(path, ()):
                    comp_cls = comp_ref()
                    if comp_cls is not None and comp_cls not in seen:
                        refs.append(comp_ref)
                        seen.add(comp_cls)
                for comp_ref in current.get(path, ()):
                    comp_cls = comp_ref()
                    if comp_cls is not None and comp_cls in active_classes and comp_cls not in seen:
                        refs.append(comp_ref)
                        seen.add(comp_cls)
                if refs:
                    restored[path] = refs
            self._file_index = restored

    def _merge_component_file_index(
        self,
        snapshot: dict[str, tuple[ReferenceType[type[Component]], ...]],
        component_classes: set[type[Component]],
    ) -> None:
        """Restore indexed files for successful dependency classes retained after import failure."""
        if not component_classes:
            return
        with self._index_lock:
            for path, source_refs in snapshot.items():
                eligible_refs = [item for item in source_refs if item() in component_classes]
                if not eligible_refs:
                    continue
                target_refs = self._file_index.setdefault(path, [])
                seen = {comp_cls for item in target_refs if (comp_cls := item()) is not None}
                for comp_ref in eligible_refs:
                    comp_cls = comp_ref()
                    if comp_cls in component_classes and comp_cls not in seen:
                        target_refs.append(comp_ref)
                        seen.add(comp_cls)

    @contextmanager
    def atomic_registration(self) -> Iterator[None]:
        """
        Publish a group of component registrations together.

        Component classes defined inside the block register normally and fire
        the normal class and registration hooks. If the block raises, Citry
        restores its component names, class-ID and file indexes, tag rules,
        and discovery state to their values at entry. Another thread receives
        [`CitryLifecycleInProgress`][citry.CitryLifecycleInProgress] rather
        than observing or changing the group before it commits.

        This context manager is additive: it publishes new classes and aliases;
        [`unregister()`][citry.Citry.unregister] rejects removals inside the
        block. Start the block outside other component lifecycle operations;
        nested atomic-registration blocks are rejected. Ordinary component
        definitions and their hooks remain reentrant inside the block.

        Rollback covers the Citry registration and installation indexes listed
        above. Rendered-output caches, side effects that extension hooks or
        ordinary Python write elsewhere, and registrations made to another
        Citry instance are outside the transaction.

        Yields:
            None. Component factories return their own created classes; the
            context manager only owns publication and rollback.

        Raises:
            CitryLifecycleInProgress: If another thread owns component
                lifecycle work for this Citry instance.
            RuntimeError: If called inside another component lifecycle
                operation on the same thread.

        Example:
            ```python
            with app.atomic_registration():
                class AcmeButton(Component):
                    citry = app
            ```

        """
        with self._registry._lifecycle.operation("atomic component registration", reentrant=False):
            state = self._snapshot_registration_state()
            self._atomic_registration_depth += 1
            try:
                yield
            except BaseException:
                self._restore_registration_state(state)
                raise
            finally:
                self._atomic_registration_depth -= 1

    def register_library(self, library: ComponentLibrary | ModuleType) -> LibraryInstallation:
        """
        Materialize and publish an engine-neutral component library.

        A library package may be passed directly when it exposes its manifest
        as ``__citry_library__``. Registration creates a distinct concrete
        Component class for every definition and this Citry instance. The
        classes and immutable installation record become visible together.

        Repeating the same manifest and exact definition generation returns the
        existing installation without rerunning component hooks. Clear the
        Citry instance before installing a reloaded or changed manifest with
        the same library name.

        Args:
            library: A [`ComponentLibrary`][citry.ComponentLibrary] or imported
                package exposing one as ``__citry_library__``.

        Returns:
            The exact active [`LibraryInstallation`][citry.LibraryInstallation].

        Raises:
            LibraryManifestChanged: If the library name is already associated
                with another manifest or definition generation.
            LibraryInstallationStale: If internal registry mutation damaged an
                active installation.
            ValueError: If a required extension is not installed or a component
                identity collides with existing state.
            AlreadyRegistered: If a registry name is already occupied.
            CitryLifecycleInProgress: If another thread owns lifecycle work.
            RuntimeError: If registration is attempted recursively.

        Example:
            ```python
            import citry_ui
            from citry import Citry

            app = Citry()
            installed = app.register_library(citry_ui)
            ```

        """
        manifest = _coerce_component_library(library)
        with self.atomic_registration():
            existing = self._library_installations.get(manifest.name)
            if existing is not None:
                same_definitions = len(existing.library.components) == len(manifest.components) and all(
                    left is right for left, right in zip(existing.library.components, manifest.components, strict=True)
                )
                if existing.library._signature != manifest._signature or not same_definitions:
                    msg = (
                        f"Component library {manifest.name!r} is already installed from another manifest "
                        "or definition generation. Clear this Citry instance before replacing it."
                    )
                    raise LibraryManifestChanged(msg)
                self._validate_library_installation_locked(existing)
                return existing

            for extension_name in manifest.required_extensions:
                try:
                    self.extensions.get_extension(extension_name)
                except ValueError as cause:
                    msg = (
                        f"Cannot install component library {manifest.name!r}: required extension "
                        f"{extension_name!r} is not installed."
                    )
                    raise ValueError(msg) from cause

            for definition in manifest.components:
                identity = _definition_identity(definition)
                previous_definition = self._library_definition_identities.get(identity)
                if previous_definition is not None and previous_definition is not definition:
                    rendered = ".".join(identity)
                    msg = f"Library definition identity {rendered!r} is already installed from another generation."
                    raise LibraryManifestChanged(msg)
                if definition in self._library_components:
                    rendered = ".".join(identity)
                    msg = f"Library definition {rendered!r} already belongs to another installed library."
                    raise ValueError(msg)

                for component_name in _component_names(definition):
                    occupied = self._registry._name_to_cls.get(component_name)
                    if occupied is not None:
                        raise AlreadyRegistered(
                            f"Cannot install component library {manifest.name!r}: registry name "
                            f"{component_name!r} is already taken by {occupied.__name__!r}."
                        )
                class_id = _predicted_class_id(definition)
                occupied_id = self._classes_by_id.get(class_id)
                if occupied_id is not None:
                    raise AlreadyRegistered(
                        f"Cannot install component library {manifest.name!r}: class_id {class_id!r} "
                        f"is already registered by {occupied_id.__name__!r}."
                    )

            concrete_by_definition: dict[type[LibraryComponent], type[Component]] = {}
            for definition in manifest.components:
                concrete = _materialize_library_component(definition, self)
                if concrete.citry is not self:
                    msg = f"Materialized library component {definition.__name__!r} belongs to another Citry instance."
                    raise RuntimeError(msg)
                if concrete.class_id != _predicted_class_id(definition):
                    msg = f"Materialized library component {definition.__name__!r} has an unstable class identity."
                    raise RuntimeError(msg)
                for component_name in _component_names(definition):
                    if self._registry._name_to_cls.get(component_name) is not concrete:
                        msg = (
                            f"Materialized library component {definition.__name__!r} did not claim "
                            f"registry name {component_name!r}."
                        )
                        raise RuntimeError(msg)
                if self._classes_by_id.get(concrete.class_id) is not concrete:
                    msg = f"Materialized library component {definition.__name__!r} is absent from the class-ID index."
                    raise RuntimeError(msg)
                concrete_by_definition[definition] = concrete

            installation = _new_library_installation(self, manifest, concrete_by_definition)
            self._library_installations[manifest.name] = installation
            for definition, concrete in concrete_by_definition.items():
                self._library_components[definition] = concrete
                self._library_definition_identities[_definition_identity(definition)] = definition
                self._library_definitions_by_class[concrete] = definition
            self._validate_library_installation_locked(installation)
            return installation

    def get_library_installation(self, name: str) -> LibraryInstallation:
        """
        Return one exact active component-library installation.

        Args:
            name: The manifest's case-sensitive library name.

        Returns:
            The current immutable installation handle.

        Raises:
            LibraryNotInstalled: If no library with ``name`` is active.
            LibraryInstallationStale: If private registry mutation damaged the
                installation record.
            CitryLifecycleInProgress: If another thread owns lifecycle work.

        """
        if not isinstance(name, str):
            raise TypeError("get_library_installation() name must be a string.")
        with self._registry._lifecycle.read("look up a component library installation"):
            installation = self._library_installations.get(name)
            if installation is None:
                raise LibraryNotInstalled(f"Component library {name!r} is not installed for this Citry instance.")
            self._validate_library_installation_locked(installation)
            return installation

    def _resolve_library_component(
        self,
        definition: type[LibraryComponent],
        *,
        installation: LibraryInstallation | None = None,
    ) -> type[Component]:
        """Resolve an exact inert definition through committed installation state."""
        with self._registry._lifecycle.read("resolve a library component"):
            if installation is not None:
                self._validate_library_installation_locked(installation)
            concrete = self._library_components.get(definition)
            if concrete is None:
                rendered = ".".join(_definition_identity(definition))
                msg = (
                    f"Library component {rendered!r} is not installed for this Citry instance. "
                    "Call register_library() during application setup."
                )
                raise LibraryNotInstalled(msg)
            if installation is not None and concrete not in installation._components.values():
                rendered = ".".join(_definition_identity(definition))
                msg = f"Library component {rendered!r} does not belong to installation {installation.library.name!r}."
                raise LibraryNotInstalled(msg)
            return concrete

    def _validate_library_installation(self, installation: LibraryInstallation) -> None:
        """Validate a retained handle under lifecycle read protection."""
        with self._registry._lifecycle.read("validate a component library installation"):
            self._validate_library_installation_locked(installation)

    def _validate_library_installation_locked(self, installation: LibraryInstallation) -> None:
        """Check one installation while lifecycle access is already protected."""
        if self._library_installations.get(installation.library.name) is not installation:
            msg = f"Component library installation {installation.library.name!r} is no longer active."
            raise LibraryInstallationStale(msg)
        for definition, concrete in installation._components.items():
            if self._library_components.get(definition) is not concrete:
                msg = (
                    f"Component library installation {installation.library.name!r} has inconsistent definition state."
                )
                raise LibraryInstallationStale(msg)
            if self._library_definition_identities.get(_definition_identity(definition)) is not definition:
                msg = f"Component library installation {installation.library.name!r} has inconsistent identity state."
                raise LibraryInstallationStale(msg)
            if self._library_definitions_by_class.get(concrete) is not definition:
                msg = f"Component library installation {installation.library.name!r} has inconsistent class state."
                raise LibraryInstallationStale(msg)
            if self._classes_by_id.get(concrete.class_id) is not concrete:
                msg = f"Component library installation {installation.library.name!r} has a missing class ID."
                raise LibraryInstallationStale(msg)
            for component_name in _component_names(definition):
                if self._registry._name_to_cls.get(component_name) is not concrete:
                    msg = (
                        f"Component library installation {installation.library.name!r} has a missing or "
                        f"replaced registry name {component_name!r}."
                    )
                    raise LibraryInstallationStale(msg)

    def _is_library_installation_active(self, installation: LibraryInstallation) -> bool:
        """Return whether a retained handle is the exact complete active record."""
        with self._registry._lifecycle.read("check a component library installation"):
            try:
                self._validate_library_installation_locked(installation)
            except LibraryInstallationStale:
                return False
            return True

    @contextmanager
    def _registration_transaction(self) -> Iterator[None]:
        """Roll back one module import while retaining successful new dependencies."""
        state = self._snapshot_registration_state()
        modules_before = frozenset(sys.modules)
        previous_journal = self._registration_journal
        journal: list[_RegistrationRecord] = []
        self._registration_journal = journal
        try:
            yield
        except BaseException:
            failed_state = self._snapshot_registration_state()
            imported_dependencies = sys.modules.keys() - modules_before
            # Importlib removes the failing module from sys.modules but keeps
            # dependencies that finished importing. Preserve their exact names
            # and aliases: retrying the parent will not execute them again.
            # Built-ins remain part of the outer attempt and must still roll
            # back as one complete set.
            builtin_classes = {
                failed_state.registry.name_to_cls[name]
                for name in BUILTIN_COMPONENT_NAMES
                if name in failed_state.registry.name_to_cls
            }
            dependency_classes = {
                record.comp_cls
                for record in journal
                if record.added
                and record.origin_modules & imported_dependencies
                and record.comp_cls not in builtin_classes
                and record.comp_cls.__module__ in sys.modules
                and (
                    state.registry.name_to_cls.get(record.name) is None
                    or state.registry.name_to_cls.get(record.name) is record.comp_cls
                )
            }
            self._restore_registration_state(state, preserve_file_classes=dependency_classes)
            restored_dependency_classes: set[type[Component]] = set()
            restored_dependency_changed = False
            for record in journal:
                name = record.name
                comp_cls = record.comp_cls
                if not (record.origin_modules & imported_dependencies) or comp_cls in builtin_classes:
                    continue
                # Do not retain an alias pointing at a class from the failing
                # parent module, which importlib has removed from its cache.
                if comp_cls.__module__ not in sys.modules:
                    continue
                if record.added:
                    existing = self._registry._name_to_cls.get(name)
                    if existing is not None and existing is not comp_cls:
                        continue
                    self._registry._name_to_cls[name] = comp_cls
                    self._registry._cls_to_names.setdefault(id(comp_cls), set()).add(name)
                    self._classes_by_id[comp_cls.class_id] = comp_cls
                    restored_dependency_classes.add(comp_cls)
                elif self._registry._name_to_cls.get(name) is comp_cls:
                    self._registry._name_to_cls.pop(name)
                    remaining_names = self._registry._cls_to_names.get(id(comp_cls))
                    if remaining_names is not None:
                        remaining_names.discard(name)
                        if not remaining_names:
                            self._registry._cls_to_names.pop(id(comp_cls))
                            if self._classes_by_id.get(comp_cls.class_id) is comp_cls:
                                self._classes_by_id.pop(comp_cls.class_id, None)
                restored_dependency_changed = True
            if restored_dependency_classes:
                self._merge_component_file_index(failed_state.file_index, restored_dependency_classes)
            if restored_dependency_changed:
                self._tag_rules_cache = None
            raise
        finally:
            self._registration_journal = previous_journal

    def register(self, comp_cls: type[Component], name: str | None = None) -> None:
        """
        Register an additional name for a component owned by this instance.

        Component classes register automatically when they are defined. This
        method supports same-engine aliases and re-registering a class after it
        was removed. A class owned by another ``Citry`` instance is rejected.

        Fires ``on_component_registered`` once per call, after the registry
        accepts the class.

        Raises:
            AlreadyRegistered: If the requested name or class ID belongs to a
                different component, or the name is reserved.
            ValueError: If the component belongs to another Citry instance, is
                a retired built-in generation, or the requested name is invalid.
            CitryLifecycleInProgress: If another thread is changing component
                lifecycle state.

        """
        with self._registry._lifecycle.operation("component registration"):
            self._register_component(comp_cls, name)

    def _register_builtin(self, comp_cls: type[Component], token: object) -> None:
        """Register one class carrying this instance's private built-in authority."""
        with self._registry._lifecycle.operation("built-in component registration"):
            self._register_component(comp_cls, builtin_token=token)

    @contextmanager
    def _component_class_lifecycle(self) -> Iterator[None]:
        """Protect class-created hooks and registration as one lifecycle operation."""
        with self._registry._lifecycle.operation("component class creation"):
            yield

    def _register_component(
        self,
        comp_cls: type[Component],
        name: str | None = None,
        *,
        builtin_token: object | None = None,
    ) -> None:
        """Register a class and roll back Citry-owned state if a hook rejects it."""
        if comp_cls.__dict__.get("_citry_owner") is not self:
            msg = (
                f"Cannot register {comp_cls.__name__!r} with this Citry instance: "
                "a component class may only be registered with its owning Citry instance."
            )
            raise ValueError(msg)
        if builtin_token is None and comp_cls.__dict__.get("_citry_builtin_token") is not None:
            is_current_builtin = any(
                self._registry._name_to_cls.get(name) is comp_cls for name in BUILTIN_COMPONENT_NAMES
            )
            if not is_current_builtin:
                msg = f"Cannot register retired built-in component {comp_cls.__name__!r}."
                raise ValueError(msg)
        state = self._snapshot_registration_state()
        names_before = set(self._registry._cls_to_names.get(id(comp_cls), ()))
        journal_start = len(self._registration_journal) if self._registration_journal is not None else None
        try:
            existing = self._classes_by_id.get(comp_cls.class_id)
            if existing is not None and existing is not comp_cls:
                msg = (
                    f"Cannot register {comp_cls.__name__!r}: class_id {comp_cls.class_id!r} "
                    f"is already registered by {existing.__name__!r}."
                )
                raise AlreadyRegistered(msg)

            if builtin_token is None:
                self._registry._register(comp_cls, name)
            else:
                self._registry._register_builtin(comp_cls, builtin_token)
            names_added = tuple(
                registered_name
                for registered_name, registered_cls in self._registry._name_to_cls.items()
                if registered_cls is comp_cls and registered_name not in names_before
            )
            if self._registration_journal is not None and names_added:
                origin_modules = self._registration_origin_modules()
                self._registration_journal.extend(
                    _RegistrationRecord(
                        name=registered_name,
                        comp_cls=comp_cls,
                        origin_modules=origin_modules,
                        added=True,
                    )
                    for registered_name in names_added
                )
            self._classes_by_id[comp_cls.class_id] = comp_cls
            self._tag_rules_cache = None
            registered_name = name or getattr(comp_cls, "name", None) or comp_cls.__name__
            self.extensions.on_component_registered(registered_name, comp_cls)
        except BaseException:
            if self._registration_journal is not None and journal_start is not None:
                del self._registration_journal[journal_start:]
            self._restore_registration_state(state)
            raise

    @staticmethod
    def _registration_origin_modules() -> frozenset[str]:
        """Module names active on the call path of a registration."""
        modules: set[str] = set()
        frame: FrameType | None = sys._getframe(1)
        while frame is not None:
            module_name = frame.f_globals.get("__name__")
            if isinstance(module_name, str):
                modules.add(module_name)
            frame = frame.f_back
        return frozenset(modules)

    def unregister(self, comp_cls_or_name: type[Component] | str) -> None:
        """
        Unregister one name or all names for a component owned by this instance.

        Fires ``on_component_unregistered`` once per call, after the registry
        removes the class.

        Raises:
            NotRegistered: If the requested class or name is not registered.
            ValueError: If asked to remove a built-in's canonical name or
                unregister the built-in class.
            CitryLifecycleInProgress: If another thread is changing component
                lifecycle state.
            RuntimeError: If called inside `atomic_registration()` on this
                thread; atomic registration is additive.

        """
        with self._registry._lifecycle.operation("component unregistration"):
            if self._atomic_registration_depth:
                msg = "Cannot unregister a component inside Citry.atomic_registration(); the block is additive."
                raise RuntimeError(msg)
            # Resolve the class (and a representative name) before removal, so
            # the hook context is populated whether called by class or by name.
            if isinstance(comp_cls_or_name, str):
                self._registry._ensure_builtins()
                comp_cls = self._registry._get(_normalize_name(comp_cls_or_name))
                removed_name = comp_cls_or_name
            else:
                comp_cls = comp_cls_or_name
                removed_name = getattr(comp_cls, "name", None) or comp_cls.__name__
            library_definition = self._library_definitions_by_class.get(comp_cls)
            if library_definition is not None:
                managed_names = set(_component_names(library_definition))
                removes_managed_name = (
                    not isinstance(comp_cls_or_name, str) or _normalize_name(comp_cls_or_name) in managed_names
                )
                if removes_managed_name:
                    msg = (
                        f"Cannot unregister library-managed component {comp_cls.__name__!r} or one of its "
                        "manifest names. Clear the Citry instance to retire the complete installation."
                    )
                    raise ValueError(msg)
            state = self._snapshot_registration_state()
            names_before = tuple(
                registered_name
                for registered_name, registered_cls in self._registry._name_to_cls.items()
                if registered_cls is comp_cls
            )
            journal_start = len(self._registration_journal) if self._registration_journal is not None else None
            try:
                self._registry._unregister(comp_cls_or_name)
                names_removed = tuple(
                    registered_name
                    for registered_name in names_before
                    if self._registry._name_to_cls.get(registered_name) is not comp_cls
                )
                if self._registration_journal is not None and names_removed:
                    origin_modules = self._registration_origin_modules()
                    self._registration_journal.extend(
                        _RegistrationRecord(
                            name=registered_name,
                            comp_cls=comp_cls,
                            origin_modules=origin_modules,
                            added=False,
                        )
                        for registered_name in names_removed
                    )
                # A PascalCase component may have two registry aliases. Keep
                # reverse lookup alive until its final name is removed, then
                # release the class ID so a replacement class can claim it.
                if not self._registry._has_class(comp_cls) and self._classes_by_id.get(comp_cls.class_id) is comp_cls:
                    self._classes_by_id.pop(comp_cls.class_id, None)
                self._tag_rules_cache = None
                self.extensions.on_component_unregistered(removed_name, comp_cls)
                # A component can remain registered under another alias, and a
                # hook may change that answer. Retire its render bodies only
                # after the hooks accept a final removal.
                if not self._registry._has_class(comp_cls):
                    self._evict_component_cache(comp_cls)
                    self.extensions._advance_render_cache_revision()
            except BaseException:
                if self._registration_journal is not None and journal_start is not None:
                    del self._registration_journal[journal_start:]
                self._restore_registration_state(state)
                raise

    def _has_component_class(self, comp_cls: type[Component]) -> bool:
        """Whether this exact Citry-bound component class has any registered name."""
        return self._registry._has_class(comp_cls)

    def get(self, name: str) -> type[Component]:
        """
        Look up a component by name.

        Args:
            name: Registered component name, matched case-insensitively.

        Returns:
            The registered component class.

        Raises:
            NotRegistered: If no component has this name after discovery.
            CitryLifecycleInProgress: If another thread is changing component
                lifecycle state.

        """
        normalized = _normalize_name(name)
        with self._registry._lifecycle.read("look up a component"):
            if self._registry_ready():
                return self._registry._get(normalized)
        with self._registry._lifecycle.operation("component discovery and registry initialization"):
            self._ensure_registry_ready()
            with self._registry._lifecycle.read("look up a component"):
                return self._registry._get(normalized)

    def has(self, name: str) -> bool:
        """
        Check whether a component name is registered.

        Args:
            name: Registered component name, matched case-insensitively.

        Returns:
            Whether the name is registered after discovery.

        Raises:
            CitryLifecycleInProgress: If another thread is changing component
                lifecycle state.

        """
        normalized = _normalize_name(name)
        with self._registry._lifecycle.read("check component registration"):
            if self._registry_ready():
                return self._registry._has(normalized)
        with self._registry._lifecycle.operation("component discovery and registry initialization"):
            self._ensure_registry_ready()
            with self._registry._lifecycle.read("check component registration"):
                return self._registry._has(normalized)

    @property
    def components(self) -> dict[str, type[Component]]:
        """
        All registered components as a name-to-class mapping.

        Raises:
            CitryLifecycleInProgress: If another thread is changing component
                lifecycle state.

        """
        with self._registry._lifecycle.read("read registered components"):
            if self._registry_ready():
                return self._registry._all()
        with self._registry._lifecycle.operation("component discovery and registry initialization"):
            self._ensure_registry_ready()
            with self._registry._lifecycle.read("read registered components"):
                return self._registry._all()

    def inspect_components(
        self,
        *,
        include_builtins: bool = False,
        resolve_assets: bool = False,
        include_default_values: bool = False,
        include_extensions: Iterable[str] = (),
    ) -> ComponentCatalog:
        """
        Return an immutable catalog of the currently registered components.

        The method completes normal lazy discovery and built-in creation, then
        copies the registry once. Schema and asset metadata are built from that
        copy after lifecycle coordination is released. Asset inspection never
        reads source content or changes render and hot-reload caches.

        Args:
            include_builtins: Include Citry's framework component classes.
            resolve_assets: Check declared asset paths on the filesystem and
                report resolved, missing, and searched paths.
            include_default_values: Copy portable literal schema defaults into
                field metadata. Default factories are never called.
            include_extensions: Installed extensions whose versioned component
                metadata inspectors should run. Names are deduplicated and
                sorted; no inspector runs unless explicitly requested.

        Returns:
            A canonically ordered [`ComponentCatalog`][citry.ComponentCatalog]
            containing copied values only.

        Raises:
            TypeError: If a boolean option is not a bool or
                ``include_extensions`` is a string or non-iterable.
            ComponentIntrospectionError: If a requested extension is missing,
                unsupported, fails, or publishes invalid metadata.
            CitryLifecycleInProgress: If another thread is changing component
                lifecycle state.

        """
        self._validate_introspection_bool(include_builtins, "include_builtins")
        self._validate_introspection_bool(resolve_assets, "resolve_assets")
        self._validate_introspection_bool(include_default_values, "include_default_values")
        inspectors = self.extensions._prepare_component_inspectors(include_extensions)
        registrations = self.components
        return _build_component_catalog(
            self,
            registrations,
            include_builtins=include_builtins,
            resolve_assets=resolve_assets,
            include_default_values=include_default_values,
            inspectors=inspectors,
        )

    def inspect_component(
        self,
        component: str | type[Component],
        *,
        resolve_assets: bool = False,
        include_default_values: bool = False,
        include_extensions: Iterable[str] = (),
    ) -> ComponentInfo:
        """
        Inspect one component selected from a copied registry snapshot.

        A string is matched case-insensitively as a registered component name.
        A class must be owned by this engine and present under at least one
        name. Looking up an alias does not change the record's deterministic
        primary name.

        Args:
            component: A registered name or exact registered component class.
            resolve_assets: Check declared asset paths on the filesystem.
            include_default_values: Copy portable literal schema defaults.
            include_extensions: Installed extensions whose versioned metadata
                inspectors should run. Names are deduplicated and sorted.

        Returns:
            A value-only [`ComponentInfo`][citry.ComponentInfo] record.

        Raises:
            TypeError: If ``component`` is neither a string nor a class, a
                boolean option is not a bool, or ``include_extensions`` is a
                string or non-iterable.
            NotRegistered: If the name or exact class is absent from the copied
                registry snapshot.
            ComponentIntrospectionError: If a requested extension is missing,
                unsupported, fails, or publishes invalid metadata.
            CitryLifecycleInProgress: If another thread is changing component
                lifecycle state.

        """
        self._validate_introspection_bool(resolve_assets, "resolve_assets")
        self._validate_introspection_bool(include_default_values, "include_default_values")
        inspectors = self.extensions._prepare_component_inspectors(include_extensions)
        registrations = self.components

        if isinstance(component, str):
            normalized = str.lower(component)
            comp_cls = registrations.get(normalized)
            if comp_cls is None:
                raise NotRegistered(f"No component registered as {normalized!r}.")
        elif isinstance(component, type):
            comp_cls = next((candidate for candidate in registrations.values() if candidate is component), None)
            if comp_cls is None:
                name = type.__dict__["__name__"].__get__(component)
                raise NotRegistered(f"Component {name!r} is not registered with this Citry instance.")
        else:
            msg = "Citry.inspect_component() component must be a registered name or component class."
            raise TypeError(msg)

        names = tuple(sorted(name for name, candidate in registrations.items() if candidate is comp_cls))
        info = _build_component_info(
            self,
            comp_cls,
            names,
            builtin=self._is_builtin_component(comp_cls),
            resolve_assets=resolve_assets,
            include_default_values=include_default_values,
        )
        return self.extensions._inspect_component_extensions(comp_cls, info, inspectors)

    @staticmethod
    def _validate_introspection_bool(value: object, name: str) -> None:
        if type(value) is not bool:
            msg = f"Citry introspection option {name!r} must be a bool."
            raise TypeError(msg)

    def _is_builtin_component(self, comp_cls: type[Component]) -> bool:
        """Return whether this engine created the exact built-in class."""
        token = _static_class_dict(comp_cls).get("_citry_builtin_token")
        return token is self._registry._builtin_registration_token

    def initialize(self) -> None:
        """
        Prepare component registration state before starting worker threads.

        This imports configured component modules when autodiscovery is enabled,
        creates Citry's built-in components, and builds the current parse-time
        tag rules. Component template, JavaScript, and CSS asset files remain
        lazy and are loaded when rendering needs them.

        Call this after startup-time component registration and before a server
        begins handling requests concurrently. Repeated successful calls are
        safe; a later registration invalidates tag rules, and another call
        rebuilds them.

        Initialization is retryable rather than globally transactional. If a
        module import fails, components from earlier successful module imports
        may remain registered, while the incomplete work is retried later.

        Returns:
            None.

        Raises:
            CitryLifecycleInProgress: If another thread is changing component
                lifecycle state.
            RuntimeError: If called recursively from an active lifecycle hook
                or initialization on this thread.

        """
        with self._registry._lifecycle.operation("Citry.initialize()", reentrant=False):
            self._ensure_tag_rules()

    def autodiscover(self, dirs: Sequence[str | Path] | None = None) -> list[str]:
        """
        Import this instance's component modules so their classes register.

        With no argument, imports every component module under the instance's
        ``dirs`` - the same scan the ``autodiscover`` setting performs
        automatically on first use - and marks that automatic scan done, so it
        will not run again. Pass ``dirs`` to import an extra set of directories
        on demand without affecting the automatic scan.

        The directories must be importable: each one (or a parent of it) is on
        ``sys.path``/``PYTHONPATH``, which is how a component file is mapped to
        the import name Python uses for it. A directory that holds component
        modules but is not importable raises ``ValueError``.

        Returns the dotted import paths of the modules that were imported. Safe
        to call more than once: an already-imported module has its components
        re-registered directly, so a call after ``clear()`` rebuilds the
        registry and a call that changes nothing is a no-op.

        A scan is marked complete only after every module imports successfully.
        If one module raises, registrations it made to this ``Citry`` instance
        during that import are rolled back, and a later call can retry it.
        Earlier modules and dependency modules that imported successfully
        remain registered. Python side effects and registrations made to
        another ``Citry`` instance are outside this rollback. Calling
        ``autodiscover()`` recursively from a component module raises
        ``RuntimeError``.

        Raises:
            CitryLifecycleInProgress: If another thread is changing component
                lifecycle state.
            RuntimeError: If a component module starts another autodiscovery
                scan on the same instance.

        """
        if dirs is None:
            marks_configured_scan = True
            search_dirs = self.settings.dirs
        else:
            marks_configured_scan = False
            search_dirs = tuple(Path(d) for d in dirs)
        with self._registry._lifecycle.operation("Citry.autodiscover()", reentrant=False):
            imported = self._run_discovery(search_dirs)
            if marks_configured_scan:
                self._discovered = True
            return imported

    @property
    def urls(self) -> tuple[URLRoute, ...]:
        """
        This instance's HTTP route table (framework-neutral ``URLRoute``s).

        The web-integration adapters (``citry.contrib.asgi`` and friends)
        mount these into the host application; the routes serve cached
        component JS/CSS, the client runtime, and extension endpoints.
        """
        return self.extensions.urls

    @property
    def commands(self) -> dict[str, tuple[type[ExtensionCommand], ...]]:
        """
        This instance's CLI commands, keyed by extension name.

        Each registered extension contributes the commands it declares in
        ``Extension.commands``; the ``citry`` command-line tool reaches one as
        ``citry ext run <extension name> <command name>``. See
        ``ExtensionManager.commands`` for ordering and the uniqueness guarantee.
        """
        return self.extensions.commands

    @property
    def mounted_prefix(self) -> str | None:
        """Where this instance's routes are mounted (e.g. ``"/citry"``), or ``None`` when nothing is mounted."""
        return self._mounted_prefix

    def set_mounted_prefix(self, prefix: str) -> None:
        """
        Record where this instance's routes are mounted in the host app.

        The adapters' ``mount()`` call this; call it directly only in a
        process that builds URLs without mounting the routes itself (for
        example a worker that renders fragments served by another process).
        ``prefix`` must start with ``/``; a trailing ``/`` is dropped.
        """
        if not prefix.startswith("/"):
            msg = f"Mount prefix must start with '/', got {prefix!r}"
            raise ValueError(msg)
        self._mounted_prefix = prefix.rstrip("/")

    def build_url(self, path: str) -> str:
        """
        An absolute URL path for one of this instance's routes.

        ``path`` is the route's full path (no leading slash), e.g.
        ``"cache/Table_a1b2c3.js"``. Raises ``RuntimeError`` when no web
        integration is mounted, since the URL would point nowhere.
        """
        if self._mounted_prefix is None:
            msg = (
                "Cannot build a citry URL: no web integration is mounted."
                " Mount one (e.g. citry.contrib.fastapi.mount(app, citry_instance))"
                " or call set_mounted_prefix() in processes that only build URLs."
            )
            raise RuntimeError(msg)
        return f"{self._mounted_prefix}/{path}"

    def get_component_by_class_id(self, class_id: str) -> type[Component]:
        """
        Look up a registered component class by its ``class_id``.

        ``class_id`` is the stable identifier (``MyComp.class_id``) used in
        cache keys and script URLs. Raises ``KeyError`` when no registered
        class has that id.

        Raises:
            KeyError: If no registered component has this class ID.
            CitryLifecycleInProgress: If another thread is changing component
                lifecycle state.

        """
        with self._registry._lifecycle.read("look up a component class ID"):
            comp_cls = self._classes_by_id.get(class_id)
            if comp_cls is None:
                msg = f"No component class with class_id {class_id!r} is registered with this Citry instance"
                raise KeyError(msg)
            return comp_cls

    @staticmethod
    def _build_cache(spec: CitryCache | str | None) -> CitryCache:
        """
        Build the live cache backend from the settings spec.

        ``None`` gives a fresh in-memory cache. An import string is resolved
        like extension specs are: ``"path.to.Cache"`` names either a class
        (instantiated with no arguments) or a ready-made backend object.
        """
        if spec is None:
            return InMemoryCache()
        if isinstance(spec, str):
            module_path, _, attr_name = spec.rpartition(".")
            resolved = getattr(import_module(module_path), attr_name)
            spec = resolved() if isinstance(resolved, type) else resolved
        if not isinstance(spec, CitryCache):
            msg = (
                f"Citry cache must provide get/set/delete/has (see citry.cache.CitryCache), got {type(spec).__name__}"
            )
            raise TypeError(msg)
        return spec

    @staticmethod
    def _resolve_id_generator(spec: Callable[[], str] | str | None) -> Callable[[], str] | None:
        """
        Build the render-id generator override from the settings spec.

        ``None`` means no override (the built-in generator is used). An import
        string is resolved like the cache spec: ``"path.to.gen"`` names either a
        callable or a class, and a class is instantiated once into the generator
        (so a stateful one, such as a counter, keeps its state per instance).
        The result must be callable.
        """
        if spec is None:
            return None
        if isinstance(spec, str):
            module_path, _, attr_name = spec.rpartition(".")
            spec = getattr(import_module(module_path), attr_name)
        if isinstance(spec, type):
            spec = spec()
        if not callable(spec):
            msg = f"Citry id_generator must be callable (a function returning a str), got {type(spec).__name__}"
            raise TypeError(msg)
        return spec

    def _create_builtin_components(self) -> None:
        """
        Create this instance's built-in components (the registry's factory).

        Called by the private registry on its first component lookup. Defining the built-in
        classes registers them through the normal metaclass path.
        """
        # Imported here, not at module load: component.py (which the built-in
        # components are made of) imports this module.
        from citry.components import make_builtin_components  # noqa: PLC0415

        make_builtin_components(self)

    def _ensure_discovered(self) -> None:
        """
        Import the component modules under ``settings.dirs`` once, on first use.

        Driven by the ``autodiscover`` setting. Runs at the first component
        lookup (``get``/``has``/``components``) or template compile
        (``_tag_rules``), so every component defined under ``dirs`` is registered
        before any template that references it is parsed. A no-op when
        autodiscovery is off or no ``dirs`` are set. See ``Citry.autodiscover``.
        """
        if self._discovered or self._discovering or not self.settings.autodiscover:
            return
        if not self.settings.dirs:
            self._discovered = True
            return
        self._run_discovery(self.settings.dirs)
        self._discovered = True

    def _discovery_ready(self) -> bool:
        """Whether a public Citry read needs no configured discovery work."""
        return self._discovered or not self.settings.autodiscover

    def _registry_ready(self) -> bool:
        """Whether discovery and built-ins are ready for one atomic read."""
        return self._discovery_ready() and self._registry._builtins_ready()

    def _ensure_registry_ready(self) -> None:
        """Complete lazy discovery and built-ins while this thread owns the lifecycle."""
        self._ensure_discovered()
        self._registry._ensure_builtins()

    def _run_discovery(self, dirs: tuple[Path, ...]) -> list[str]:
        """
        Scan ``dirs`` and import their component modules, under the re-entrancy
        guard. Returns the imported module names. The guard makes a lookup that
        fires while a discovered component is registering short-circuit (see
        ``_ensure_discovered``) rather than start a nested scan.
        """
        if self._discovering:
            msg = "Citry autodiscovery is already running; a component module cannot call autodiscover() recursively."
            raise RuntimeError(msg)
        self._discovering = True
        try:
            return import_component_modules(dirs, registration_transaction=self._registration_transaction)
        finally:
            self._discovering = False

    def _tag_rules(self) -> dict[str, TagRules]:
        """
        Parse-time validation rules for templates parsed under this instance.

        Derived from the registered components' ``Kwargs``/``Slots``
        declarations (see ``citry/tag_rules.py``), so a template using a
        declared component fails at parse time on unknown or missing
        kwargs/fills. Cached; the cache resets whenever a component is
        registered or unregistered.
        """
        with self._registry._lifecycle.read("read tag rules"):
            if self._registry_ready() and self._tag_rules_cache is not None:
                return self._tag_rules_cache
        with self._registry._lifecycle.operation("tag-rule construction"):
            return self._ensure_tag_rules()

    def _ensure_tag_rules(self) -> dict[str, TagRules]:
        """Build and publish complete tag rules while this thread owns the lifecycle."""
        # Discovery and built-ins must finish first: build_tag_rules reads the
        # whole registry, so publishing from a partial set would make later
        # template validation depend on thread timing.
        self._ensure_registry_ready()
        if self._tag_rules_cache is None:
            self._tag_rules_cache = build_tag_rules(self)
        return self._tag_rules_cache

    def _evict_component_cache(self, comp_cls: type[Component]) -> None:
        """Forget one component class's cached template work (see ``_const_body_cache``)."""
        self._const_body_cache.evict_component(comp_cls)

    # ----- Asset file index (what hot reload queries) -----

    def _register_component_file(self, path: Path, comp_cls: type[Component]) -> None:
        """Record that ``comp_cls`` loaded an asset from ``path``."""
        key = str(Path(path).resolve())
        with self._index_lock:
            refs = self._file_index.setdefault(key, [])
            if not any(existing() is comp_cls for existing in refs):
                refs.append(ref(comp_cls))

    def get_components_for_file(self, path: str | Path) -> list[type[Component]]:
        """
        The component classes whose assets resolved to ``path``.

        Most callers want :meth:`invalidate_file`, which both finds these
        classes and resets them. This lower-level lookup is for a caller that
        wants the classes without resetting (a custom hot-reload handler, a
        test). Dead weakrefs are pruned on read.
        """
        key = str(Path(path).resolve())
        with self._index_lock:
            refs = self._file_index.get(key)
            if not refs:
                return []

            alive: list[type[Component]] = []
            alive_refs: list[ReferenceType[type[Component]]] = []
            for comp_ref in refs:
                comp_cls = comp_ref()
                if comp_cls is not None:
                    alive.append(comp_cls)
                    alive_refs.append(comp_ref)
            self._file_index[key] = alive_refs
            return alive

    def invalidate_file(self, path: str | Path) -> list[type[Component]]:
        """
        Drop cached template/JS/CSS for every component that loaded an asset
        from ``path``, so the next render re-reads it from disk.

        Returns the component classes it reset. An empty list means the file
        backs no loaded component, which a hot-reload handler can read as "not
        mine" and, if it wants, fall through to a full restart. This is the
        host-neutral call a file watcher drives; see the watcher in
        :mod:`citry.reload` and ``docs/design/hot_reload.md``.
        """
        classes = self.get_components_for_file(path)
        for comp_cls in classes:
            # A file backs only one asset kind, but the index does not record
            # which; each reset is a cheap no-op when its cache is unset, so
            # calling both is the simplest correct choice.
            comp_cls.reset_template()
            comp_cls.reset_files()
        return classes

    def invalidate_all(self) -> list[type[Component]]:
        """
        Reset cached template/JS/CSS for every component that has loaded a file,
        so the next render re-reads them all from disk. Returns the reset classes
        (in first-seen order).

        For when a change cannot be mapped to a single path: a bulk edit, a
        branch switch, or a custom watcher reporting an event it cannot resolve
        to one file. Unlike :meth:`clear`, this leaves the registry and
        autodiscovery untouched.
        """
        # First-seen order, de-duplicated: a class can be indexed under several
        # files (template + js + css), and dict keys preserve insertion order.
        unique: dict[type[Component], None] = {}
        with self._index_lock:
            for refs in self._file_index.values():
                for comp_ref in refs:
                    comp_cls = comp_ref()
                    if comp_cls is not None:
                        unique.setdefault(comp_cls, None)
        classes = list(unique)
        for comp_cls in classes:
            comp_cls.reset_template()
            comp_cls.reset_files()
        return classes

    def clear(self) -> None:
        """
        Clear registrations and caches, and re-arm autodiscovery.

        Raises:
            CitryLifecycleInProgress: If another thread is changing component
                lifecycle state.
            RuntimeError: If called from another lifecycle operation on this
                thread.

        """
        with self._registry._lifecycle.operation("Citry.clear()", reentrant=False, blocks_nested=True):
            with self.extensions._render_cache_invalidation():
                self._registry._clear()
                self._const_body_cache.clear()
                with self._index_lock:
                    self._file_index.clear()
                self._classes_by_id.clear()
                self._library_installations.clear()
                self._library_components.clear()
                self._library_definition_identities.clear()
                self._library_definitions_by_class.clear()
                self._tag_rules_cache = None
                # Re-arm autodiscovery: the next lookup re-runs the dirs scan and
                # rebuilds the registry. Even though the modules are already
                # imported, the scan re-registers their components.
                self._discovered = False
                # A shared backend may not want a full wipe; the built-in
                # in-memory cache supports it. The revision guard remains held
                # so new keys cannot be stored before this clear finishes.
                cache_clear = getattr(self.cache, "clear", None)
                if callable(cache_clear):
                    cache_clear()


# Complete the ComponentLike protocol annotation now that Citry exists.
from citry.component_like import _bind_citry_runtime_type  # noqa: E402

_bind_citry_runtime_type(Citry)

# Import after Citry is defined so library_component can expose resolvable
# runtime annotations without participating in Citry's class-definition cycle.
from citry.library_component import (  # noqa: E402
    ComponentLibrary,
    LibraryComponent,
    LibraryComponentIdentity,
    LibraryInstallation,
    LibraryInstallationStale,
    LibraryManifestChanged,
    LibraryNotInstalled,
    _coerce_component_library,
    _component_names,
    _definition_identity,
    _materialize_library_component,
    _new_library_installation,
    _predicted_class_id,
)

# The default Citry instance, used when Component.citry is not set.
# Created eagerly at import time. If Citry.__init__ grows dependencies
# that import from this package, switch to __getattr__-based laziness.
citry = Citry()
