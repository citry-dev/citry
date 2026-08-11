"""
Private component registry storage.

Each ``Citry`` instance owns one registry. Components are registered
automatically at class definition time (via the metaclass), or manually via
``citry.register()`` for a same-engine alias or re-registration.

Name normalization follows Vue's convention: a PascalCase class name
is registered under both the lowercased form (``mycard``) and the
kebab-case form (``my-card``). Lookups are case-insensitive, matching
how the Rust compiler lowercases tag names.

"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from citry.lifecycle import _LifecycleCoordinator
from citry_core.template_parser import RESERVED_TAG_NAMES

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.component import Component

BUILTIN_COMPONENT_NAMES: Final = frozenset(
    {"provide", "cache", "component", "element", "error-fallback", "js", "css", "i18n", "trans"}
)
"""Component names reserved for built-in tags.

Core component classes live in ``citry/components/``. Extension-owned classes,
such as ``cache``, ``i18n``, and ``trans``, live with their extensions.
"""

STRUCTURAL_TAG_NAMES: Final = frozenset(name.removeprefix("c-") for name in RESERVED_TAG_NAMES)
"""Names the template parser interprets directly instead of resolving through
the component registry. Single-sourced from the Rust parser."""


class AlreadyRegistered(Exception):
    """Raised when registering a component under a name that is already taken."""


class NotRegistered(Exception):
    """Raised when looking up a component name that is not registered."""


def _pascal_to_kebab(name: str) -> str:
    """
    Convert a PascalCase name to kebab-case.

    ``MyCard`` -> ``my-card``, ``HTMLParser`` -> ``html-parser``
    """
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", s)
    return s.lower()


def _normalize_name(name: str) -> str:
    """Normalize a component name for registry lookup (lowercased)."""
    return name.lower()


# Tag names must start with an ASCII letter, then letters, digits,
# hyphens, underscores, or dots. Matches the grammar's html_tag_name
# rule (minus the c- prefix).
_VALID_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9\-_.]*$")


def _validate_component_name(name: str) -> None:
    """Validate that a name is usable as an HTML tag name (after the c- prefix)."""
    if not _VALID_NAME_RE.fullmatch(name):
        msg = (
            f"Invalid component name: {name!r}. "
            f"Must start with a letter and contain only "
            f"letters, digits, hyphens, underscores, or dots."
        )
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class _RegistryState:
    """The Citry-owned registry state restored after failed initialization."""

    name_to_cls: dict[str, type[Component]]
    cls_to_names: dict[int, set[str]]
    builtins_registered: bool


class _ComponentRegistry:
    """
    Store one Citry instance's component-name mappings and lifecycle state.

    A single component class may be registered under multiple names
    (e.g. ``mycard`` and ``my-card``). The registry maintains a reverse
    map so unregister-by-class is O(1).

    The registry owns the built-in components' lifecycle: the names in
    ``BUILTIN_COMPONENT_NAMES`` are reserved (user registrations under them
    are rejected), and the owning Citry instance creates the built-ins on the
    first lookup (see ``_ensure_builtins``).
    Initialization counts as complete only after every built-in registers.

    This is private storage rather than a second public API. Citry owns every
    mutation so hooks, class-ID lookup, cached tag rules, and discovery state
    remain consistent. Lifecycle work is synchronous and owned by one thread
    at a time. Reads and mutations from another thread raise
    [`CitryLifecycleInProgress`][citry.CitryLifecycleInProgress] rather than
    exposing an incomplete built-in or registration attempt.
    """

    def __init__(self, owner: Citry) -> None:
        # name -> component class (all names normalized/lowercased)
        self._name_to_cls: dict[str, type[Component]] = {}
        # class id -> set of registered names (reverse map)
        self._cls_to_names: dict[int, set[str]] = {}
        self._owner = owner
        self._lifecycle = _LifecycleCoordinator()
        self._builtins_registered = False
        self._initializing_builtins = False
        # Built-in classes carry this exact private object through their
        # metaclass call. It authorizes that class only, unlike a registry-wide
        # switch that would also admit user classes created by extension hooks.
        self._builtin_registration_token = object()

    def _register(
        self,
        comp_cls: type[Component],
        name: str | None = None,
        *,
        is_builtin: bool = False,
    ) -> None:
        """Register directly, after the owning Citry has handled its state."""
        if name is not None:
            _validate_component_name(name)
            names = [_normalize_name(name)]
        else:
            raw_name = getattr(comp_cls, "name", None) or comp_cls.__name__
            _validate_component_name(raw_name)
            lowered = _normalize_name(raw_name)
            kebab = _pascal_to_kebab(raw_name)
            names = list(dict.fromkeys([lowered, kebab]))

        for n in names:
            # Structural tags are consumed by the parser and can never resolve
            # through this registry, so accepting one would create an
            # unreachable component.
            if n in STRUCTURAL_TAG_NAMES:
                raise AlreadyRegistered(
                    f"Cannot register {comp_cls.__name__!r} as {n!r}: "
                    f"the name is reserved for the structural <c-{n}> tag."
                )

            if not is_builtin and n in BUILTIN_COMPONENT_NAMES:
                raise AlreadyRegistered(
                    f"Cannot register {comp_cls.__name__!r} as {n!r}: "
                    f"the name is reserved for the built-in <c-{n}> component."
                )

            if is_builtin and n not in BUILTIN_COMPONENT_NAMES:
                msg = f"Cannot register {comp_cls.__name__!r} as an internal built-in under non-built-in name {n!r}."
                raise ValueError(msg)

        cls_id = id(comp_cls)
        for n in names:
            existing = self._name_to_cls.get(n)
            if existing is not None:
                if existing is comp_cls:
                    continue
                raise AlreadyRegistered(
                    f"Cannot register {comp_cls.__name__!r} as {n!r}: already taken by {existing.__name__!r}."
                )
            self._name_to_cls[n] = comp_cls
            if cls_id not in self._cls_to_names:
                self._cls_to_names[cls_id] = set()
            self._cls_to_names[cls_id].add(n)

    def _register_builtin(self, comp_cls: type[Component], token: object) -> None:
        """Register one class carrying this registry's private built-in authority."""
        if token is not self._builtin_registration_token or not self._initializing_builtins:
            msg = f"Cannot register {comp_cls.__name__!r} as a built-in outside built-in initialization."
            raise RuntimeError(msg)
        self._register(comp_cls, is_builtin=True)

    def _unregister(self, comp_cls_or_name: type[Component] | str) -> None:
        """Unregister directly, after the owning Citry has handled its state."""
        # Case: unregister by name
        if isinstance(comp_cls_or_name, str):
            name = _normalize_name(comp_cls_or_name)
            if name in BUILTIN_COMPONENT_NAMES:
                msg = f"The built-in <c-{name}> cannot be unregistered."
                raise ValueError(msg)
            if name not in self._name_to_cls:
                raise NotRegistered(f"No component registered as {name!r}.")
            comp_cls = self._name_to_cls.pop(name)
            cls_names = self._cls_to_names.get(id(comp_cls))
            if cls_names is not None:
                cls_names.discard(name)
                if not cls_names:
                    del self._cls_to_names[id(comp_cls)]
            return

        # Case: unregister by class
        comp_cls = comp_cls_or_name
        cls_id = id(comp_cls)
        names_to_remove = self._cls_to_names.get(cls_id)
        if not names_to_remove:
            raise NotRegistered(f"Component {comp_cls.__name__!r} is not registered.")
        builtin_names = names_to_remove & BUILTIN_COMPONENT_NAMES
        if builtin_names:
            name = sorted(builtin_names)[0]
            msg = f"The built-in <c-{name}> cannot be unregistered."
            raise ValueError(msg)
        del self._cls_to_names[cls_id]
        for n in names_to_remove:
            self._name_to_cls.pop(n, None)

    def _clear(self) -> None:
        """Clear registry-owned state without calling back into an owning Citry."""
        self._name_to_cls.clear()
        self._cls_to_names.clear()
        self._builtins_registered = False

    def _snapshot_state(self) -> _RegistryState:
        """Copy durable registry state for an internal initialization attempt."""
        return _RegistryState(
            name_to_cls=dict(self._name_to_cls),
            cls_to_names={cls_id: set(names) for cls_id, names in self._cls_to_names.items()},
            builtins_registered=self._builtins_registered,
        )

    def _restore_state(self, state: _RegistryState) -> None:
        """Restore a snapshot without firing registration hooks."""
        self._name_to_cls.clear()
        self._name_to_cls.update(state.name_to_cls)
        self._cls_to_names.clear()
        self._cls_to_names.update({cls_id: set(names) for cls_id, names in state.cls_to_names.items()})
        self._builtins_registered = state.builtins_registered

    def _has_class(self, comp_cls: type[Component]) -> bool:
        """
        Whether this exact class is registered (under any name).

        Used by autodiscovery to re-register only the components that a cleared
        registry is missing, so a re-scan skips ones already present. Does not
        create the built-ins (it asks about a specific user class), so it has no
        side effects.
        """
        with self._lifecycle.read("check component class registration"):
            return id(comp_cls) in self._cls_to_names

    def _builtins_ready(self) -> bool:
        """Whether a Citry read needs no built-in factory work."""
        return self._builtins_registered

    def _get(self, normalized_name: str) -> type[Component]:
        """Read one normalized name while lifecycle access is already protected."""
        comp_cls = self._name_to_cls.get(normalized_name)
        if comp_cls is None:
            raise NotRegistered(f"No component registered as {normalized_name!r}.")
        return comp_cls

    def _has(self, normalized_name: str) -> bool:
        """Check one normalized name while lifecycle access is already protected."""
        return normalized_name in self._name_to_cls

    def _all(self) -> dict[str, type[Component]]:
        """Copy registrations while lifecycle access is already protected."""
        return dict(self._name_to_cls)

    def _ensure_builtins(self) -> None:
        """
        Create and register the built-in components after one successful attempt.

        Built-ins (``<c-provide>``, ``<c-cache>``, ``<c-component>``,
        ``<c-element>``, ``<c-error-fallback>``, ``<c-js>``, ``<c-css>``) are ordinary
        Component subclasses bound to one Citry instance, so each instance
        needs its own. The owner creates them on the first lookup rather than
        up front: the default Citry instance is constructed while
        ``citry/citry.py`` is still importing, when the component module cannot
        be imported yet. By the time anything looks a component up, imports
        are complete.
        """
        if self._builtins_registered or self._initializing_builtins:
            return
        self._initializing_builtins = True
        owner_state = self._owner._snapshot_registration_state()
        try:
            self._owner._create_builtin_components()
            missing = BUILTIN_COMPONENT_NAMES - self._name_to_cls.keys()
            if missing:
                names = ", ".join(f"<c-{name}>" for name in sorted(missing))
                msg = f"Built-in initialization completed without registering: {names}."
                raise RuntimeError(msg)
        except BaseException:
            self._owner._restore_registration_state(owner_state)
            raise
        else:
            self._builtins_registered = True
        finally:
            self._initializing_builtins = False

    def __len__(self) -> int:
        """Number of unique component classes registered."""
        with self._lifecycle.read("count registered components"):
            return len({id(c) for c in self._name_to_cls.values()})

    def __repr__(self) -> str:
        return f"_ComponentRegistry({len(self)} components)"
