# This file adds typing for the API exposed from Rust via maturin.
#
# IMPORTANT: The filename `_rust.pyi` matches the `<rust_module_name>` part of
# the `module-name` setting in `pyproject.toml` (`tool.maturin.module-name = "citry_core._rust"`).
# This ensures type checkers can find the type stubs for the Rust extension module.
#
# Since the Rust code exposed to Python is scoped under modules, we need to define
# the API as class attributes, e.g.
#
# ```py
# class template_parser:
#     class Tag:
#         ...
# ```
#
# So that in Python we can access it as:
#
# ```py
# from citry_core import _rust
# _rust.template_parser.Tag(...)
# ```
#
# Notes:
# - Functions without `self` are treated as module-level functions.
#   This matches how typeshed defines modules.

from typing import Dict, List, Literal, Optional, Set, Tuple, Union

########################################################
# HTML transform
########################################################

class html_transform:
    def transform_html(
        html: str,
        root_attributes: List[str],
        all_attributes: List[str],
        check_end_names: Optional[bool] = None,
        track_added_attributes_for_tags_with_this_attribute: Optional[str] = None,
    ) -> tuple[str, Dict[str, List[str]]]:
        """
        Transform given HTML string.

        This function performs the following transformations:

        1. **Add root attributes**: Attributes specified in `root_attributes` are added
        only to root-level elements (elements at depth 0).

        2. **Add attributes to all elements**: Attributes specified in `all_attributes`
        are added to every element in the HTML.

        In addition, this transformer also:

        1. **Tracks added attributes**: If `track_added_attributes_for_tags_with_this_attribute`
        is set, captures which attributes were added to elements that have the specified
        attribute, returning a dictionary mapping attribute values to lists of attributes added to tag.

        2. **Validates end tags**: If `check_end_names` is enabled, validates that
        closing tags match their corresponding opening tags.

        **Arguments**

        - `html` (str): The HTML string to transform. Can be a fragment or full document.
        - `root_attributes` (List[str]): List of attribute names to add to root elements only.
        - `all_attributes` (List[str]): List of attribute names to add to all elements.
        - `check_end_names` (Optional[bool]): Whether to validate matching of end tags. Defaults to False.
        - `track_added_attributes_for_tags_with_this_attribute` (Optional[str]): If set, captures which attributes were added to elements with this attribute.

        **Returns**

        A tuple containing:
            - The transformed HTML string
            - A dictionary mapping captured attribute values to lists of attributes that were added
                to those elements. Only populated if `track_added_attributes_for_tags_with_this_attribute` is set, otherwise empty dict.

        **Example**

        ```python
        >>> html = '<div data-id="123"><p>Hello</p></div>'
        >>> html, captured = transform_html(html, ['data-root-id'], ['data-v-123'], track_added_attributes_for_tags_with_this_attribute='data-id')
        >>> print(captured)
        {'123': ['data-root-id', 'data-v-123']}
        ```

        **Raises**

        ValueError: If the HTML is malformed or cannot be parsed.
        """

########################################################
# Safe eval
########################################################

class safe_eval:
    def safe_eval(source: str) -> str:
        """
        Transform a Python expression string to make it safe for evaluation.

        This function takes a Python expression string and transforms it into safe code
        by wrapping potentially unsafe operations (like variable access, function calls,
        attribute access, etc.) with sandboxed function calls.

        **Args:**

        - source (str): The Python expression string to transform.

        **Returns:**

        - str: The transformed Python expression as a string.

        **Raises:**

        - SyntaxError: If the input is not valid Python syntax or contains forbidden constructs.

        **Examples:**

        ```python
        >>> safe_eval("my_var + 1")
        'variable("my_var") + 1'

        >>> safe_eval("lambda x: x + my_var")
        'lambda x: x + variable("my_var")'
        ```

        **Transformations:**

        The following transformations are applied to make expressions safe for evaluation:

        1. **Variable access** - `my_var` → `variable("my_var")`
        2. **Function calls** - `foo(1, 2, a=3, *args, **kwargs)` → `call(foo, 1, 2, a=x, *args, **kwargs)`
        3. **Attribute access** - `obj.attr` → `attribute(obj, "attr")`
        4. **Subscript access** - `obj[key]` → `subscript(obj, key)`
        5. **Walrus operator** - `(x := value)` → `assign("x", value)`

        Because of the changes above, we also need to transform:

        6. **Slice notation** - `obj[1:10:2]` → `subscript(obj, slice(1, 10, 2))`
           - Because slice syntax is valid only inside square brackets.
        7. **F-strings** - `f"Hello {price!r:.2f}"` → `format("Hello {}", (variable("price"), "r", ".2f"))`
           - To avoid issues with quote escaping and enable error reporting
        8. **T-strings** - `t"Hello {name!r:>10}"` → `template("Hello ", interpolation(variable("name"), "expr", "r", ">10"))`
           - To avoid issues with quote escaping
        """
        ...
