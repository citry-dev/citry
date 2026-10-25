"""
A compiled route pattern matches a path in one left-to-right pass.

Two of the dependency routes place parameters next to each other with only
a ``.`` between them (``cache/{class_id}.{script_type}`` and
``cache/{class_id}.{vars_hash}.{script_type}``). Each parameter before a
literal stops at that literal, so a long path that never matches is
rejected after one scan rather than by searching every split point. These
tests lock both the matched values and the one-pass behaviour.
"""

from __future__ import annotations

import time

import pytest

from citry.util.routing import compile_route_pattern

_BOUND_SECONDS = 0.5


@pytest.mark.parametrize(
    ("route", "path", "expected"),
    [
        (
            "cache/{class_id}.{script_type}",
            "cache/Table_a1b2c3.js",
            {"class_id": "Table_a1b2c3", "script_type": "js"},
        ),
        (
            "cache/{class_id}.{vars_hash}.{script_type}",
            "cache/Table_a1b2c3.0f1e2d3c.css",
            {"class_id": "Table_a1b2c3", "vars_hash": "0f1e2d3c", "script_type": "css"},
        ),
        ("asset/{file_name}", "asset/9f8e7d6c.css", {"file_name": "9f8e7d6c.css"}),
        ("render/{family}/{state}", "render/buttons/default", {"family": "buttons", "state": "default"}),
    ],
)
def test_route_patterns_match_valid_paths(route: str, path: str, expected: dict[str, str]) -> None:
    match = compile_route_pattern(route).match(path)
    assert match is not None
    assert match.groupdict() == expected


@pytest.mark.parametrize(
    "route",
    ["cache/{class_id}.{script_type}", "cache/{class_id}.{vars_hash}.{script_type}"],
)
def test_adjacent_parameter_routes_reject_a_long_path_in_one_pass(route: str) -> None:
    pattern = compile_route_pattern(route)
    # A long run of `.`-separated parts with a final `/` never matches: a
    # route segment holds no `/`. With the parameters bounded by the `.`,
    # this is one scan; the earlier open-ended parameters made it grow with
    # the square (two parameters) or the cube (three) of the length.
    path = route.split("/", 1)[0] + "/" + "a." * 20_000 + "/"
    start = time.perf_counter()
    assert pattern.match(path) is None
    assert time.perf_counter() - start < _BOUND_SECONDS
