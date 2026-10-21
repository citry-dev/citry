"""The ``Secret`` marker: a server-only value that Citry refuses to send to the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, NoReturn, TypeVar, final

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")

# The text a Secret shows wherever Python turns it into text: a template's
# `{{ token }}`, an HTML attribute, a log line, or a traceback.
_MASK = "***"


@final
class Secret(Generic[T]):
    """
    Wrap a server-only value, such as an API token, so Citry never sends it to the browser.

    Citry sends everything [`Component.js_data()`][citry.Component.js_data]
    returns to the browser, where anyone can read it in the page source.
    Wrap a value in `Secret` to have Citry refuse to send it.

    Rendering a component whose `js_data()` holds a `Secret` anywhere in its
    result raises `TypeError` that names the component and the key, before
    any HTML is sent. A `Secret` in a
    [`Component.css_data()`][citry.Component.css_data] value or a State
    field raises `ValueError`. `citry --app ... check` also warns when it can
    see the `Secret` in `js_data()`: a module constant returned by name, or
    a field annotated `Secret[...]`.

    On the server a `Secret` keeps its value hidden. Call
    [`get_secret_value()`][citry.Secret.get_secret_value] where you need the
    value, for example to call an API in an event handler. Everywhere Python
    turns it into text it shows `***` instead: `str()`, `repr()`, f-strings,
    logs, and `{{ token }}` in a template. So passing a `Secret` to a
    template or to a child component's `Kwargs` is allowed and never prints
    the value.

    Annotate a `Kwargs` or `TemplateData` field as `Secret[str]` (or
    `Secret[bytes]`, and so on) so a plain value passed there is rejected.
    The type in brackets is only for type checkers:
    [`check_input_types`][citry.LintSettings] tests that the value is a
    `Secret`, not what it holds.

    A `Secret` cannot be changed after it is created. Two secrets are equal
    when their values are equal, but a `Secret` never equals a plain value:
    `API_TOKEN == sent` is always `False`. To check a value a user sent, use
    `hmac.compare_digest(API_TOKEN.get_secret_value(), sent)`, which takes
    the same time whatever the input. A `Secret` hashes like its
    value, so it can be a dict key when the value can. `bool()` is the
    truth value of the wrapped value, so `if token:` tells whether a token
    is set. Copying or pickling a `Secret` keeps the value, so a pickle
    still holds it in readable form.

    Citry detects only values you wrap. A secret kept in a plain `str` is
    sent like any other string.

    Args:
        value: The value to keep on the server. Any type works.

    Raises:
        TypeError: When `value` is already a `Secret`. Pass that `Secret` on
            as it is instead of wrapping it again.

    Example:
        Read a token on the server, and send the browser only the result:

        ```citry
        import os

        from citry import Component, Secret

        API_TOKEN = Secret(os.environ["API_TOKEN"])


        class Board(Component):
            def template_data(self, kwargs, slots):
                token = API_TOKEN.get_secret_value()
                return {"rows": load_rows(token)}

            def js_data(self, kwargs, slots):
                # Returning API_TOKEN here raises TypeError.
                return {"apiBase": "/api"}

            template = '''
              <ul>
                <c-for each="row in rows">
                  <li>{{ row }}</li>
                </c-for>
              </ul>
            '''
        ```

    """

    __slots__ = ("_secret_value",)
    _secret_value: T

    def __init__(self, value: T) -> None:
        # Wrapping twice would make get_secret_value() return another Secret,
        # which then fails far from here when the caller uses it as a string.
        if isinstance(value, Secret):
            msg = (
                "Secret() received a value that is already a Secret. "
                "Pass that Secret on as it is instead of wrapping it again."
            )
            raise TypeError(msg)
        # __setattr__ refuses every write, so the one write goes through object.
        object.__setattr__(self, "_secret_value", value)

    def get_secret_value(self) -> T:
        """
        Return the wrapped value.

        Call it only in server code that needs the value itself. Returning
        the result from `js_data()`, or writing it into a template, sends it
        to the browser as an ordinary value.

        Returns:
            The value given to `Secret(...)`.

        Example:
            ```python
            token = API_TOKEN.get_secret_value()
            ```

        """
        return self._secret_value

    # A Secret is immutable, so nothing can swap its value after code has
    # checked it, and the hash below stays valid.
    def __setattr__(self, name: str, value: object) -> NoReturn:
        msg = f"Secret is immutable; cannot set {name!r}. Create a new Secret instead."
        raise AttributeError(msg)

    def __delattr__(self, name: str) -> NoReturn:
        msg = f"Secret is immutable; cannot delete {name!r}."
        raise AttributeError(msg)

    # Every way Python turns the object into text shows the mask. Templates
    # render a value with str(), so `{{ token }}` writes `***` too.
    def __repr__(self) -> str:
        return f"Secret('{_MASK}')"

    def __str__(self) -> str:
        return _MASK

    def __format__(self, format_spec: str) -> str:
        # A spec such as `{token:>10}` pads the mask; the default for an
        # object would raise instead.
        return format(_MASK, format_spec)

    def __eq__(self, other: object) -> bool:
        # Comparing with a plain value is always False, so code cannot test a
        # Secret against a guessed string by accident.
        if not isinstance(other, Secret):
            return NotImplemented
        return bool(self._secret_value == other._secret_value)

    def __hash__(self) -> int:
        # Equal secrets hash alike; an unhashable value makes the Secret
        # unhashable too, as a tuple holding it would be. The value is mixed
        # with a tag because `hash(12345)` is 12345 itself.
        return hash(("citry.Secret", self._secret_value))

    def __bool__(self) -> bool:
        return bool(self._secret_value)

    # copy, deepcopy, and pickle rebuild the Secret through __init__, because
    # __setattr__ blocks the default way they restore slot values.
    def __reduce__(self) -> tuple[Callable[[Any], Secret[Any]], tuple[Any]]:
        return (Secret, (self._secret_value,))

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Any:
        """
        Let a Pydantic model field be annotated `Secret[...]`.

        Pydantic calls this when it builds a model. The field accepts only a
        `Secret` instance and keeps it as it is. Pydantic's own error for a
        plain value prints that value; set `hide_input_in_errors=True` in the
        model's config to keep it out of the message.
        """
        # Pydantic is optional, and only Pydantic itself calls this hook, so the
        # import happens here rather than for every Citry user.
        from pydantic_core import core_schema  # noqa: PLC0415

        return core_schema.is_instance_schema(cls)


__all__ = ["Secret"]
