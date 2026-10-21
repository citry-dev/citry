"""The ``Secret`` marker: a server-only value that Citry refuses to send to the browser."""

from __future__ import annotations

import hmac
from typing import TYPE_CHECKING, Any, Generic, NoReturn, TypeVar, cast, final

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

    Rendering a component raises a `TypeError` that names the component and
    the key, before any HTML is sent, when a `Secret` is anywhere in the
    dicts and lists `js_data()` returns. A `Secret` in a
    [`Component.css_data()`][citry.Component.css_data] value or a State
    field raises `ValueError`, whether or not the component has CSS.
    `citry --app ... check` also warns when it can see the `Secret`: a
    module-level `Secret` that `js_data()` puts in its result, such as
    `{"token": API_TOKEN}`, or reads from an attribute stored on a module
    or a plain class, such as `config.API_TOKEN` (not through a property or
    a lazy settings object), or a `JsData` field annotated `Secret[str]`.

    A `Secret` that `js_data()` returns in another place, such as inside a
    dataclass instance nested in the result, as a dict key, or in a set, is
    refused too, but by the `TypeError` for any value JSON cannot carry,
    which does not name the key.

    On the server a `Secret` keeps its value hidden. Call
    [`get_secret_value()`][citry.Secret.get_secret_value] where you need the
    value, for example to call an API in an event handler. Everywhere Python
    turns it into text it shows `***` instead: `str()`, `repr()`, f-strings,
    logs, and `{{ token }}` in a template. So passing a `Secret` to a
    template or to a child component's `Kwargs` is allowed and never prints
    the value.

    A child that uses the render cache cannot take a `Secret` this way.
    Without `Cache.vary()`, its cache key is built from all of its kwargs,
    and a `Secret` cannot be part of a key, so rendering raises
    [`CacheKeyError`][citry.ext.cache.CacheKeyError]. Return values that are
    not secret, such as a user id, from that child's `Cache.vary()`, or
    leave the child uncached.

    Annotate a `Kwargs` or `TemplateData` field as `Secret[str]` (or
    `Secret[bytes]`, and so on) so a plain value passed there is rejected.
    The type in brackets is only for type checkers:
    [`check_input_types`][citry.LintSettings] tests that the value is a
    `Secret`, not what it holds. When `Kwargs` is a Pydantic model,
    Pydantic's own error for a plain value prints that value; add
    `model_config = ConfigDict(hide_input_in_errors=True)` to the model to
    keep it out of the message.

    A `Secret` never equals a plain value: `API_TOKEN == sent` is always
    `False`. To check a value a user sent, use `hmac.compare_digest`, which
    takes the same time however much of the input matches:

    ```python
    token = API_TOKEN.get_secret_value().encode()
    matches = hmac.compare_digest(token, sent.encode())
    ```

    Compare bytes, as here: `compare_digest` raises `TypeError` for text
    that is not ASCII. Two secrets are equal when their values are equal.
    When both values are `str`, or both are `bytes`, they are compared with
    `hmac.compare_digest`. Any other values are compared with `==`.

    A `Secret` cannot be changed after it is created. It can be a dict key
    when its value is hashable, and equal secrets hash alike. `bool()` is
    the truth value of the wrapped value, so `if token:` tells whether a
    token is set. Copying or pickling a `Secret` keeps the value, so a
    pickle still holds it in readable form.

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
        left: object = self._secret_value
        right: object = other._secret_value
        # `==` on text stops at the first differing character, so the time it
        # takes tells an attacker how much of a guess was right.
        # compare_digest takes the same time whatever matches, but accepts
        # only ASCII text, so text is compared as its UTF-8 bytes. A lone
        # surrogate cannot be encoded strictly, and "surrogatepass" keeps it
        # from raising.
        # A str or bytes subclass holds the same text, so it takes the same
        # constant-time path rather than falling back to its own `==`. The
        # real class is tested, because `isinstance` would believe an
        # object that only claims to be a str.
        left_type = type(left)
        right_type = type(right)
        if issubclass(left_type, str) and issubclass(right_type, str):
            return hmac.compare_digest(
                str.encode(cast("str", left), "utf-8", "surrogatepass"),
                str.encode(cast("str", right), "utf-8", "surrogatepass"),
            )
        if issubclass(left_type, bytes) and issubclass(right_type, bytes):
            return hmac.compare_digest(cast("bytes", left), cast("bytes", right))
        return bool(left == right)

    def __hash__(self) -> int:
        # Equal secrets hash alike; an unhashable value makes the Secret
        # unhashable too, as a tuple holding it would be. A bare `hash()` of
        # a small int is the int itself, so the tag keeps a printed hash from
        # showing such a value as it is. It does not hide the value from
        # anyone who can hash a guess the same way and compare.
        return hash(("citry.Secret", _plain_text(self._secret_value)))

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


def _plain_text(value: object) -> object:
    """
    Return a str or bytes subclass value as an exact str or bytes, and any other value unchanged.

    Equality treats a subclass like its base type, so the hash must too:
    a subclass's own ``__hash__`` could otherwise give equal secrets
    different hashes.
    """
    value_type = type(value)
    if value_type is not str and issubclass(value_type, str):
        return str.__str__(cast("str", value))
    if value_type is not bytes and issubclass(value_type, bytes):
        # `bytes(value)` would call the subclass's own `__bytes__`.
        return bytes.__getitem__(cast("bytes", value), slice(None))
    return value


__all__ = ["Secret"]
