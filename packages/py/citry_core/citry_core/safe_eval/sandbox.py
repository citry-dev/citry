"""
A sandbox layer that ensures unsafe operations cannot be performed.
Useful when the Python expression itself comes from an untrusted source.

Based on the Jinja v3.1.6 sandbox implementation.
See https://github.com/pallets/jinja/blob/5ef70112a1ff19c05324ff889dd30405b1002044/src/jinja2/sandbox.py

We do NOT support:
- Builtins. If you need to use `len()`, `str()`, `int()`, `list()`, `dict()`, etc.,
  you'll have to pass them as variables.
- "safe" range. Jinja puts limit on the number of items a range may produce.
  We don't expose `range()` function to the sandboxed code at all.
- "Immutable" sandbox (e.g. raising when mutating a list).
- Async functions, coroutines, etc.
- `str.format` and `str.format_map` are not allowed as they can be used to access unsafe variables.
  Use f-strings instead.

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
import types
from typing import Any, Callable, Dict, Optional, Set, Tuple, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

#: Unsafe function attributes.
UNSAFE_FUNCTION_ATTRIBUTES: Set[str] = set()

#: Unsafe method attributes. Function attributes are unsafe for methods too.
UNSAFE_METHOD_ATTRIBUTES: Set[str] = set()

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
UNSAFE_BUILTIN_FUNCTIONS: Dict[Any, Optional[str]] = {
    getattr(builtins, attr): replacement
    for attr, replacement in _UNSAFE_BUILTIN_FUNCTION_NAMES.items()
    if hasattr(builtins, attr)
}

# These are not allowed as they can be used to access unsafe variables,
# e.g. `"a{0.b.__builtins__[__import__]}b".format({"b": 42})`
# Use f-strings instead.
UNSAFE_FUNCTIONS: Dict[Any, Optional[str]] = {
    str.format: "Use f-strings instead.",
    str.format_map: "Use f-strings instead.",
}


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
    f.unsafe_callable = True  # type: ignore
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
    elif hasattr(types, "AsyncGeneratorType") and isinstance(
        obj, types.AsyncGeneratorType
    ):
        if attr in UNSAFE_ASYNC_GENERATOR_ATTRIBUTES:
            return True
    return attr.startswith("__")


def is_safe_attribute(obj: Any, attr: str) -> bool:
    """
    Check if the attribute of an object is safe to access.

    Unsafe attributes are:
    - Starting with an underscore `_`
    - Internal attributes as set by `_is_internal_attribute`.
    """
    # Non-string subscripts should be fine, as they should be found only
    # as list slices.
    if not isinstance(attr, str):
        return True
    return not (attr.startswith("_") or _is_internal_attribute(obj, attr))


def is_safe_callable(obj: Any) -> Tuple[bool, Optional[str]]:
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
    - `str.format` or `str.format_map` (use f-strings instead)
    """
    # Check for bound methods (e.g., "string".format())
    # Handle both regular methods (types.MethodType) and built-in methods (builtin_function_or_method)
    underlying_func = None
    if isinstance(obj, types.MethodType):
        # Regular Python method - has __func__ attribute
        underlying_func = obj.__func__
    elif (
        hasattr(obj, "__self__")
        and hasattr(obj, "__name__")
        and not hasattr(obj, "__func__")
    ):
        # Built-in method descriptor (e.g., str.format, str.format_map)
        # These are bound methods that don't have __func__, but we can get the original descriptor
        try:
            underlying_func = getattr(type(obj.__self__), obj.__name__)
        except (AttributeError, TypeError):
            pass

    if underlying_func is not None:
        # Check marks on inner function (decorated with @unsafe or alters_data)
        if getattr(underlying_func, "unsafe_callable", False) or getattr(
            underlying_func, "alters_data", False
        ):
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

    return (True, None)


def is_safe_variable(var_name: str) -> bool:
    """
    Check if a variable is safe to access.

    Unsafe variables are:
    - Starting with an underscore `_`
    """
    return not var_name.startswith("_")
