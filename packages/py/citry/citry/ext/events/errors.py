"""
The user-facing error of the ``events`` extension, and its wire shape.

A handler or guard raises :class:`EventError` to answer a call with a
structured error instead of actions: the client receives
``{status, code, message, fieldErrors?}`` and surfaces ``message`` as the human
summary and ``fieldErrors`` as the per-field map next to inputs (design
``docs/design/events.md`` 3.7 and 4.3). One class with a ``status`` argument
covers forbidden, not-found, and conflict without an exception zoo.

This module also maps a failed schema validation (the structured
``ValidationResult`` of the sibling ``schemas`` module) onto the same wire
shape: the 422 ``invalid_args`` error object, with the validator's per-field
messages as ``fieldErrors``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from citry._protocol.events import build_error

if TYPE_CHECKING:
    from citry.ext.events.schemas import ValidationResult

# The wire code of each user-raisable status. Every row is protocol
# vocabulary (packages/protocol/events/v1, spec.md section 4.5): 403 ->
# "forbidden" (also pinned by design events.md 3.7), 404 -> "not_found",
# 409 -> "conflict", and 422 -> "invalid_args" (shared with schema
# validation). A status outside this map ships the protocol's catch-all
# code "error" together with the raised status, unchanged.
_STATUS_CODES = {
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "invalid_args",
}
_FALLBACK_CODE = "error"

# What schema-validation failures say as the human summary; the real content
# is the per-field map (design events.md 3.7).
_INVALID_ARGS_MESSAGE = "Invalid event arguments."


class EventError(Exception):
    """
    A structured error an event handler or guard raises to answer a call.

    The client receives the ``status``, a stable string ``code`` derived from
    it, the ``message`` as the human summary (a toast or banner), and
    ``fieldErrors`` as the per-field error map surfaced next to inputs
    (for example, ``$error('submit')?.fieldErrors``). Raising it anywhere in a
    handler, a guard, or the
    ``_context`` hook turns the call into that error response; it never
    becomes a host 500.

    Attributes:
        message: The human summary of the error.
        fields: Per-field error messages, keyed by data-schema field name
            (e.g. ``{"email": "Enter a valid email address."}``). Empty when
            the error is not about specific fields.
        status: The HTTP status of the error (400 to 599). ``422`` (the
            default) is a validation failure; ``403``, ``404``, and ``409``
            cover forbidden, not found, and conflict.

    Example:
        ```python
        from citry.ext.events import EventError

        class DocumentEditor(Component):
            class State:
                document_id: int

            class Events:
                def _guard(self):
                    user = user_from_request(self.request)
                    if can_edit(user, self.state.document_id):
                        return
                    raise EventError(
                        "You cannot edit this document.",
                        status=403,
                    )

                def subscribe(self, data: SubscribeIn):
                    if is_taken(data.email):
                        raise EventError(
                            "Please fix the errors below.",
                            fields={"email": "This address is already subscribed."},
                        )
        ```

    """

    def __init__(self, message: str, fields: Mapping[str, str] | None = None, status: int = 422) -> None:
        if not isinstance(message, str) or not message:
            msg = f"EventError: message must be a non-empty string; got {message!r}."
            raise ValueError(msg)
        if isinstance(status, bool) or not isinstance(status, int) or not 400 <= status <= 599:
            msg = f"EventError: status must be an HTTP error status (400 to 599); got {status!r}."
            raise ValueError(msg)
        if fields is not None and (
            not isinstance(fields, Mapping)
            or not all(isinstance(key, str) and isinstance(value, str) for key, value in fields.items())
        ):
            msg = (
                f"EventError: fields must map field names to messages,"
                f' e.g. {{"email": "Enter a valid email address."}}; got {fields!r}.'
            )
            raise ValueError(msg)
        super().__init__(message)
        self.message = message
        self.fields: dict[str, str] = dict(fields) if fields else {}
        self.status = status

    @property
    def code(self) -> str:
        """The stable wire code for the error's status (e.g. ``"forbidden"`` for 403)."""
        return _STATUS_CODES.get(self.status, _FALLBACK_CODE)


def invalid_args_error(result: ValidationResult) -> EventError:
    """
    The ``EventError`` for a failed schema validation.

    Wraps the validator's per-field messages as the 422 ``invalid_args``
    error, the same shape a handler raises by hand, so the client handles
    both identically.

    Args:
        result: A failed ``ValidationResult`` from
            [`validate_args`][citry.ext.events.schemas.validate_args].

    Returns:
        The 422 error carrying the result's field messages.

    Raises:
        ValueError: When the result did not fail (there is no error to build).

    """
    if result.ok:
        msg = "invalid_args_error() takes a failed ValidationResult; this one succeeded."
        raise ValueError(msg)
    return EventError(_INVALID_ARGS_MESSAGE, fields=result.fields, status=422)


def wire_error(error: EventError) -> dict[str, Any]:
    """
    The wire object of an ``EventError``: what a failed call's result carries.

    The shape is ``{status, code, message}`` plus ``fieldErrors`` when the error
    has per-field messages (design ``events.md`` 4.3).

    Args:
        error: The error to encode.

    Returns:
        The JSON-ready error object.

    """
    return build_error(error.status, error.code, error.message, error.fields)
