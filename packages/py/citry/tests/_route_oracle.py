"""
The regex Citry used to match a route path, kept as a reference for tests.

Each ``{name}`` is a named group of one or more characters other than
``/`` (other than ``.`` too for a dotless parameter), and the text around
it must appear as written. The route matcher and Django's ``reverse()``
must give the same answers as this regex, which can take time that grows
much faster than its input, so tests use it only on short inputs.
"""

from __future__ import annotations

import re

_PARAM_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def reference_route_regex(path: str, dotless_params: frozenset[str] = frozenset()) -> str:
    """Return the reference regex for a route path, as a pattern string."""
    pattern = ""
    last_end = 0
    for match in _PARAM_RE.finditer(path):
        pattern += re.escape(path[last_end : match.start()])
        characters = "[^/.]" if match.group(1) in dotless_params else "[^/]"
        pattern += f"(?P<{match.group(1)}>{characters}+)"
        last_end = match.end()
    pattern += re.escape(path[last_end:])
    return f"^{pattern}$"


def reference_match(path: str, dotless_params: frozenset[str], request_path: str) -> dict[str, str] | None:
    """Match a request path with the reference regex, as the whole path."""
    match = re.fullmatch(reference_route_regex(path, dotless_params), request_path)
    return None if match is None else match.groupdict()
