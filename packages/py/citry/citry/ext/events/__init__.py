"""
The ``events`` built-in extension: event handlers declared on components.

A component declares its event handlers in a nested ``Events`` class, and
declares what round-trips between the browser and those handlers in a
``State`` class (or a ``State = SomeClass`` assignment)::

    class TodoList(Component):
        class Kwargs:
            project_id: int
            query: str = ""

        class State:
            project_id: int
            query: str = ""

        class Events:
            def search(self, data: SearchIn, state):
                return TodoList(
                    project_id=state.project_id,
                    query=data.query,
                )

This extension owns that contract:

- Which methods are handlers: every public ``def`` on the component's own
  ``Events`` class, and nothing else. Underscore ``def``s are private
  helpers; underscore attributes are configuration (``_guard``, ``_context``,
  ``_csrf``, ``_methods``, ``_debounce``, ``_throttle``, ``_topics``).
- The handler signature: parameters come from the fixed vocabulary
  ``data``, ``state``, ``context``, ``request``, ``event``, and anything
  else fails at class definition.
- The State treatment: the class is rebuilt as a mutable dataclass, its
  underscore meta (``_public``, ``_model``, ``_storage``, ``_max_bytes``,
  ``_max_age``) is validated, and at render time the State instance is
  captured from the component's kwargs (or its ``state_data()`` method).
- The per-handler ``@event`` decorator for overriding the component-level
  configuration on one handler.

The optional typed base for ``Events`` classes is exported at the root as
``citry.Events``. Design: ``docs/design/events.md``.
"""

from citry.ext.events import actions
from citry.ext.events.csrf import X_CITRY_EVENTS_HEADER
from citry.ext.events.dispatcher import CallEvent, EventRequest, EventsDispatcher, TransportContext
from citry.ext.events.errors import EventError
from citry.ext.events.extension import EventsExtension
from citry.ext.events.files import UploadedFile
from citry.ext.events.handlers import event
from citry.ext.events.routes import get_event_url
from citry.ext.events.view_events import ViewEvents

__all__ = [
    "X_CITRY_EVENTS_HEADER",
    "CallEvent",
    "EventError",
    "EventRequest",
    "EventsDispatcher",
    "EventsExtension",
    "TransportContext",
    "UploadedFile",
    "ViewEvents",
    "actions",
    "event",
    "get_event_url",
]
