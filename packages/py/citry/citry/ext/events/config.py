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

    def url(
        self,
        name: str,
        *,
        query: dict[str, Any] | None = None,
        fragment: str | None = None,
    ) -> str:
        """
        Build the URL that calls one of this component's event handlers.

        Call it on the component while it renders, usually in
        `template_data()`, to point a plain HTML form or a link at a handler.
        Outside a render, use
        [`get_event_url()`][citry.ext.events.get_event_url] with the
        component class instead.

        Args:
            name: The handler's name: the method name, or the name given
                with `@event(name=...)`.
            query: Query parameters to add to the URL. Default: none.
            fragment: Text for the `#fragment` part of the URL. Default:
                none.

        Returns:
            The handler's URL path with `query` and `fragment` added, for
            example `"/citry/ext/events/e/Signup_a1b2c3/submit"`.

        Raises:
            ValueError: When the component has no handler named `name`.
            RuntimeError: When no web framework integration is mounted, so
                the URL would point nowhere, or when you call `url()` on an
                `Events` object you created yourself instead of on
                `self.events` of a component.

        Example:
            ```python
            class Signup(Component):
                class Events:
                    def submit(self, data: SignupIn) -> None:
                        create_account(data.email)

                def template_data(self, kwargs, slots):
                    return {"submit_url": self.events.url("submit")}
            ```

        """
        # Only the copy that the events extension builds for each component
        # knows which component it belongs to; an instance made by hand
        # does not, so there is no handler to point the URL at.
        component_class = getattr(self, "component_class", None)
        if component_class is None:
            msg = (
                "Events.url() was called on an Events object that belongs to no component. "
                "Call it as self.events.url(...) inside a component, or use "
                "get_event_url(MyComponent, ...) outside a render."
            )
            raise RuntimeError(msg)
        # The route module imports the handler module, which imports this
        # class, so importing it at the top would be circular.
        from citry.ext.events.routes import get_event_url  # noqa: PLC0415

        return get_event_url(component_class, name, query=query, fragment=fragment)
