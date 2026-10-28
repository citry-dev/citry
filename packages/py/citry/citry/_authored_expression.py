"""Parse a Python expression the way Citry's parser and evaluator read it."""

from __future__ import annotations

import ast


def parse_authored_expression(source: str) -> ast.Expression:
    r"""
    Parse ``source`` inside ``(\n...\n)``, as Citry's parser and evaluator do.

    The wrapper lets an author write an expression that is valid only inside
    parentheses, such as a conditional whose ``else`` sits on its own line, or
    start it on an indented line, as in a multi-line attribute value. Analysis
    that parses the bare text would reject what rendering accepts. The
    parentheses add no node to the tree, and line numbers are moved back by
    the wrapper's first line, so positions point into ``source``. The one
    exception is a tuple or generator that is the whole expression, such as
    ``a, b``: Python counts the wrapper's parentheses as part of that node, so
    its own range starts before ``source`` and ends after it. Its children's
    positions are right.

    Raises:
        SyntaxError: If ``source`` is not one Python expression.
        ValueError: If ``source`` holds text Python cannot encode, such as a
            lone surrogate.

    """
    tree = ast.parse(f"(\n{source}\n)", mode="eval")
    # Columns need no change: each line of `source` keeps its own columns, and
    # the wrapper only adds the line before them.
    ast.increment_lineno(tree, -1)
    return tree
