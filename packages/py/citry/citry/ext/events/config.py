"""
The per-component ``Events`` config class, which doubles as the typing base.

This is the class the extension system rebuilds every component's
``class Events:`` on (the ``Extension.Config`` mechanism), so it is also where
the per-call ambient attributes (``self.state``, ``self.context``,
``self.request``, ``self.event``) are declared. Because the woven class and
the typing base are the same class, a user subclassing it gains editor and
type-checker support without changing anything at runtime.

The generic pattern (a ``TypeVar`` with a PEP 696 default, subscripted with
the sibling State class in the base list) is the one spelling verified green
on runtime, mypy, and pyright; see
``docs/design/events_research/typing-lab-report.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic

from typing_extensions import TypeVar

from citry.extension import ExtensionConfig

if TYPE_CHECKING:
    from citry.util.routing import RouteRequest

# The State type carried by ``self.state``. The PEP 696 default makes the
# bare, unsubscripted base type ``self.state`` as ``None``, matching the
# stateless-handlers contract (no State class means ``state`` is ``None``).
StateT = TypeVar("StateT", default=None)


class Events(ExtensionConfig, Generic[StateT]):
    """
    Optional typed base for a component's ``Events`` class.

    A component's ``class Events:`` needs no base class: the built-in
    ``events`` extension rebuilds it on this class either way, so subclassing
    is purely a typing aid and changes nothing at runtime. Subscript the base
    with the component's State class to type ``self.state`` for editors and
    type checkers (mypy and pyright):

    Example:
        ```python
        import citry
        from citry import Component

        class TodoState:
            project_id: int
            query: str = ""

        class TodoList(Component):
            State = TodoState

            class Events(citry.Events[TodoState]):
                def refresh(self) -> None:
                    self.state.query  # typed as str
        ```

        On a component with no State class, subclass the bare base:
        ``self.state`` is then typed (and is) ``None``.

    Attributes:
        state: The component's State instance for the call being handled;
            ``None`` when the component declares no State class.
        context: Whatever the ``_context`` hook returned for the call being
            handled; ``None`` when no hook is configured.
        request: A framework-neutral view of the request that carried the
            call ([`RouteRequest`][citry.RouteRequest]).
        event: Metadata about the call being handled.

    """

    state: StateT
    context: Any
    request: RouteRequest
    event: Any
