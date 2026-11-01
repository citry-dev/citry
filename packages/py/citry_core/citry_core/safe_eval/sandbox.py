"""
A sandbox layer that refuses unsafe names and calls in a Python expression.

Based on the Jinja v3.1.6 sandbox implementation.
See https://github.com/pallets/jinja/blob/5ef70112a1ff19c05324ff889dd30405b1002044/src/jinja2/sandbox.py

What the sandbox does
---------------------
It checks every variable, attribute, item, and call that the expression text writes.
It refuses:

- Names that start with `_`: variables, attributes (so no `obj.__class__`), and string
  item keys (`data["_key"]`).
- Calls to functions that are dangerous by themselves, such as `eval`, `getattr`, and `open`.
  The check compares the function, not its name, so a function passed in under another
  name, or wrapped in `functools.partial`, is refused too.
- Text formatting that follows paths written inside the string: `format` and `format_map`
  of any string type (`str`, its subclasses such as `markupsafe.Markup`, and
  `collections.UserString`), every method of a `string.Formatter`, and building an
  `operator.attrgetter` or `operator.methodcaller`. Use f-strings instead.
- Functions marked with `@unsafe` or `alters_data = True`.

What the sandbox does not promise
---------------------------------
It is a second layer of protection. It does not make a template from a stranger safe to run.

- It does not limit the objects you pass in. Every attribute and method of a context
  object whose name does not start with `_` can be read and called, so what such an
  object can reach or do is available to the expression. A secret in a public attribute
  is readable, and a public method that deletes data can be called. Mark such a method
  with `@unsafe`, or leave the object out of the context.
- It checks only the lookups and calls that the expression text writes. A function that
  you pass in and that calls other functions or looks up names from text does so without
  these checks. Examples are `map`, `functools.reduce`, a `key=` argument of `sorted` or
  `list.sort`, a `getattr`-style helper, `inspect`, `importlib`, and `logging.Formatter`
  with `{` style. Do not pass such helpers in.
- It hides an item key that starts with `_` only when the expression writes the lookup
  itself. `data["_key"]` is refused, but `data.get("_key")`, iterating over `data`, and
  `"%(_key)s" % data` read the same item.
- It does not limit time or memory. `9 ** 9 ** 9` and `"x" * 10**10` run until the process
  runs out of resources.
- The expression text must come from the template author. Request data belongs in the
  context, as a value.

A name the generated code uses for its own checks (`variable`, `attribute`, `subscript`,
`call`, `assign`, `slice`, `interpolation`, `template`, `format`, `source`, `context`) cannot
be a lambda parameter or comprehension variable. The Rust transformer refuses it with a
`SyntaxError`, because the name would replace the check inside that scope.

We do NOT support:
- Builtins. If you need to use `len()`, `str()`, `int()`, `list()`, `dict()`, etc.,
  you'll have to pass them as variables.
- "safe" range. Jinja puts limit on the number of items a range may produce.
  We don't expose `range()` function to the sandboxed code at all.
- "Immutable" sandbox (e.g. raising when mutating a list).
- Async functions, coroutines, etc.
- The string formatting methods above. Jinja runs them through a sandboxed formatter;
  we refuse them. Use f-strings instead, which the transformer rewrites so that every
  lookup inside is checked.

We add these safety features not present in Jinja:
- Prevent users from calling unsafe builtins like `eval` even if they were passed as variables.

To mark custom functions as unsafe, use the `@unsafe` decorator.

Example:
```python
@unsafe
def delete(self):
    pass
```

"""

import builtins
import contextlib
import functools
import operator
import string
import types
from collections import UserString
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

#: Unsafe function attributes.
UNSAFE_FUNCTION_ATTRIBUTES: set[str] = set()

#: Unsafe method attributes. Function attributes are unsafe for methods too.
UNSAFE_METHOD_ATTRIBUTES: set[str] = set()

#: unsafe generator attributes.
UNSAFE_GENERATOR_ATTRIBUTES = {"gi_frame", "gi_code"}

#: unsafe attributes on coroutines
UNSAFE_COROUTINE_ATTRIBUTES = {"cr_frame", "cr_code"}

#: unsafe attributes on async generators
UNSAFE_ASYNC_GENERATOR_ATTRIBUTES = {"ag_code", "ag_frame"}

# Builtin functions that users have no business calling in sandboxed code.
# We check for these as it may happen that these functons were passed as variables,
# and the user may try to call them.
# Dictionary mapping unsafe functions to replacement messages.
_UNSAFE_BUILTIN_FUNCTION_NAMES = {
    "__build_class__": None,
    "__import__": None,
    "__loader__": None,
    "aiter": None,
    "anext": None,
    "breakpoint": None,
    "classmethod": None,
    "compile": None,
    "delattr": None,
    "eval": None,
    "exec": None,
    "exit": None,
    "getattr": None,
    "globals": None,
    "help": None,
    "input": None,
    "locals": None,
    "memoryview": None,
    "open": None,
    "property": None,
    "quit": None,
    "setattr": None,
    "staticmethod": None,
    "super": None,
    "vars": None,
}
UNSAFE_BUILTIN_FUNCTIONS: dict[Any, str | None] = {
    getattr(builtins, attr): replacement
    for attr, replacement in _UNSAFE_BUILTIN_FUNCTION_NAMES.items()
    if hasattr(builtins, attr)
}

# `format` and `format_map` read the attribute and item paths written inside the string,
# e.g. `"a{0.b.__builtins__[__import__]}b".format({"b": 42})`, and they look each field up
# with the real `getattr`, so the checks in this module never see the lookup. Every string
# type that has such methods is refused, not only `str`: `str` subclasses may define their
# own (`markupsafe.Markup` does), `collections.UserString` is not a `str` subclass and calls
# the real `str.format`, and `string.Formatter` is the object that does the lookup.
# Use f-strings instead.
_FORMAT_MESSAGE = "Use f-strings instead."

#: The methods that format a string by following the paths written inside it.
_FORMAT_METHOD_NAMES = frozenset({"format", "format_map"})

#: The public methods of `string.Formatter`. Each one either follows a path or hands
#: out the pieces a path is built from, so all of them are refused on a formatter.
_FORMATTER_METHOD_NAMES = frozenset(name for name in vars(string.Formatter) if not name.startswith("_"))

#: Attribute names that need the extra string-type check in `is_safe_attribute`. Checking
#: this set first keeps the extra `isinstance` calls off the path of every other name.
_FORMATTING_ATTRIBUTE_NAMES = _FORMAT_METHOD_NAMES | _FORMATTER_METHOD_NAMES

# The functions below are what a class lookup returns, such as `UserString.format`. They are
# refused by identity. A subclass's own override (`Markup.format`) is a different function
# that cannot be listed ahead of time, so `is_safe_attribute` refuses it by the type of the
# object it is read from, and `_formatting_method_message` refuses a bound one by its owner.
UNSAFE_FUNCTIONS: dict[Any, str | None] = {
    str.format: _FORMAT_MESSAGE,
    str.format_map: _FORMAT_MESSAGE,
    UserString.format: _FORMAT_MESSAGE,
    UserString.format_map: _FORMAT_MESSAGE,
    **{
        function: _FORMAT_MESSAGE
        for function in vars(string.Formatter).values()
        if isinstance(function, types.FunctionType)
    },
    # These build a function that reads an attribute or calls a method named by a string
    # (`attrgetter("__class__")(obj)`), with the real `getattr`. They are refused when
    # called, so the template author cannot choose the path. A reader that the app built
    # with its own path is a plain callable and keeps working.
    operator.attrgetter: "Read the attribute in the expression instead.",
    operator.methodcaller: "Call the method in the expression instead.",
}

# Exact instances of these built-ins cannot be any of Python's frame/code/
# callable/generator internals checked by ``_is_internal_attribute``. Attribute
# names beginning with ``_`` are still rejected before this fast path. Keep the
# check exact: subclasses may carry arbitrary behavior and must use the full
# policy below.
_SAFE_EXACT_ATTRIBUTE_TYPES = frozenset(
    {
        type(None),
        bool,
        int,
        float,
        complex,
        str,
        bytes,
        bytearray,
        list,
        tuple,
        dict,
        set,
        frozenset,
        range,
        slice,
    }
)


def unsafe(f: F) -> F:
    """
    Marks a function or method as unsafe.

    Example:
    ```python
    @unsafe
    def delete(self):
        pass
    ```

    """
    f.unsafe_callable = True  # type: ignore[attr-defined]
    return f


def _is_internal_attribute(obj: Any, attr: str) -> bool:
    """
    Test if the attribute is an internal Python attribute.

    >>> _is_internal_attribute(str, "mro")
    True
    >>> _is_internal_attribute(str, "upper")
    False
    """
    if isinstance(obj, types.FunctionType):
        if attr in UNSAFE_FUNCTION_ATTRIBUTES:
            return True
    elif isinstance(obj, types.MethodType):
        if attr in UNSAFE_FUNCTION_ATTRIBUTES or attr in UNSAFE_METHOD_ATTRIBUTES:
            return True
    elif isinstance(obj, type):
        if attr == "mro":
            return True
    elif isinstance(obj, (types.CodeType, types.TracebackType, types.FrameType)):
        return True
    elif isinstance(obj, types.GeneratorType):
        if attr in UNSAFE_GENERATOR_ATTRIBUTES:
            return True
    elif hasattr(types, "CoroutineType") and isinstance(obj, types.CoroutineType):
        if attr in UNSAFE_COROUTINE_ATTRIBUTES:
            return True
    # Kept nested (not collapsed) to stay parallel with the CoroutineType branch above.
    elif hasattr(types, "AsyncGeneratorType") and isinstance(obj, types.AsyncGeneratorType):  # noqa: SIM102
        if attr in UNSAFE_ASYNC_GENERATOR_ATTRIBUTES:
            return True
    return attr.startswith("__")


def _is_formatting_member(obj: Any, attr: str) -> bool:
    """
    Test if reading `attr` from `obj` gives a method that formats text by following paths.

    That is `format` or `format_map` on a `str` subclass or `collections.UserString` (the
    object or the class itself), and any method of `string.Formatter` on a formatter or a
    formatter class. Exact `str` and `UserString` are left out: their methods are known
    functions that `is_safe_callable` refuses with a message when they are called.

    >>> _is_formatting_member(string.Formatter(), "vformat")
    True
    >>> _is_formatting_member("text", "format")
    False
    """
    is_class = isinstance(obj, type)

    def derives_from(kinds: type | tuple[type, ...]) -> bool:
        return issubclass(obj, kinds) if is_class else isinstance(obj, kinds)

    if derives_from(string.Formatter):
        return attr in _FORMATTER_METHOD_NAMES
    if attr in _FORMAT_METHOD_NAMES and derives_from((str, UserString)):
        return (obj if is_class else type(obj)) not in (str, UserString)
    return False


def is_safe_attribute(obj: Any, attr: str) -> bool:
    """
    Check if the attribute of an object is safe to access.

    Unsafe attributes are:
    - Starting with an underscore `_`
    - Internal attributes as set by `_is_internal_attribute`.
    - The methods that format text by following paths inside it: `format` and
      `format_map` on a `str` subclass or `UserString`, and the methods of a
      `string.Formatter` (see `_is_formatting_member`).
    """
    # Non-string subscripts should be fine, as they should be found only
    # as list slices.
    if not isinstance(attr, str):
        return True
    if attr.startswith("_"):
        return False
    if type(obj) in _SAFE_EXACT_ATTRIBUTE_TYPES:
        return True
    # The name test comes first so that no other attribute pays for the `isinstance` calls.
    if attr in _FORMATTING_ATTRIBUTE_NAMES and _is_formatting_member(obj, attr):
        return False
    return not _is_internal_attribute(obj, attr)


def unsafe_attribute_hint(attr: str) -> str | None:
    """Return advice to show with a refused attribute, or None when there is none."""
    return _FORMAT_MESSAGE if attr in _FORMATTING_ATTRIBUTE_NAMES else None


def _formatting_method_message(obj: Any) -> str | None:
    """
    Return the refusal message if `obj` is a bound method that formats text by following paths.

    This looks at the object the method is bound to, not at the function, because a `str`
    subclass defines its own `format` function and each one is a different function.
    """
    owner = getattr(obj, "__self__", None)
    if owner is None:
        return None
    # Every method of a formatter is refused: `vformat`, `get_field` and the rest take
    # part in the same path lookup as `format`.
    if isinstance(owner, string.Formatter):
        return _FORMAT_MESSAGE
    if isinstance(owner, (str, UserString)) and getattr(obj, "__name__", None) in _FORMAT_METHOD_NAMES:
        return _FORMAT_MESSAGE
    return None


def is_safe_callable(obj: Any) -> tuple[bool, str | None]:
    """
    Check if an object is safely callable.

    Returns:
        Tuple of (is_safe, replacement_message)
        - is_safe: True if safe to call, False otherwise
        - replacement_message: Optional string suggesting a replacement, None if not applicable

    Unsafe callables are:
    - Decorated with `@unsafe`
    - Marked with `obj.alters_data = True` (Django convention)
    - Unsafe builtins (e.g. `eval`)
    - `format` or `format_map` of any `str` instance, subclasses included, and of
      `collections.UserString` (use f-strings instead)
    - Every method of a `string.Formatter` instance
    - `operator.attrgetter` and `operator.methodcaller`, which would let the template name
      the attribute to read
    - A `functools.partial` of any of the above

    """
    # Check for bound methods (e.g., "string".format())
    # Handle both regular methods (types.MethodType) and built-in methods (builtin_function_or_method)
    underlying_func = None
    if isinstance(obj, types.MethodType):
        # Regular Python method - has __func__ attribute
        underlying_func = obj.__func__
    elif hasattr(obj, "__self__") and hasattr(obj, "__name__") and not hasattr(obj, "__func__"):
        # Built-in method descriptor (e.g., str.format, str.format_map)
        # These are bound methods that don't have __func__, but we can get the original descriptor
        with contextlib.suppress(AttributeError, TypeError):
            underlying_func = getattr(type(obj.__self__), obj.__name__)

    if underlying_func is not None:
        # Check marks on inner function (decorated with @unsafe or alters_data)
        if getattr(underlying_func, "unsafe_callable", False) or getattr(underlying_func, "alters_data", False):
            return (False, None)
        # Check if the underlying function is in our unsafe dictionaries
        if underlying_func in UNSAFE_FUNCTIONS:
            return (False, UNSAFE_FUNCTIONS[underlying_func])
        if underlying_func in UNSAFE_BUILTIN_FUNCTIONS:
            return (False, UNSAFE_BUILTIN_FUNCTIONS[underlying_func])

    # Check marks on the outer function (decorated with @unsafe or alters_data)
    if getattr(obj, "unsafe_callable", False) or getattr(obj, "alters_data", False):
        return (False, None)

    # Check identity for unbound functions
    if obj in UNSAFE_FUNCTIONS:
        return (False, UNSAFE_FUNCTIONS[obj])
    if obj in UNSAFE_BUILTIN_FUNCTIONS:
        return (False, UNSAFE_BUILTIN_FUNCTIONS[obj])

    # Check the type the method is bound to. The identity checks above know `str.format`
    # but not the `format` that a subclass such as `Markup` defines for itself.
    message = _formatting_method_message(obj)
    if message is not None:
        return (False, message)

    # A partial calls its wrapped function with some arguments filled in, so it is as
    # safe as that function. Without this, `partial(getattr, obj)` would be a way to call
    # a refused function under another name.
    if isinstance(obj, functools.partial):
        return is_safe_callable(obj.func)

    return (True, None)


def is_safe_variable(var_name: str) -> bool:
    """
    Check if a variable is safe to access.

    Unsafe variables are:
    - Starting with an underscore `_`
    """
    return not var_name.startswith("_")
