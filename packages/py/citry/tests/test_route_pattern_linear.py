"""
A compiled route pattern matches a path in one left-to-right pass.

Two of the dependency routes place parameters next to each other with only
a ``.`` between them. They list those parameters in ``dotless_params``, so
each one stops at the next dot and a long path that never matches is
rejected after one scan. A route without ``dotless_params`` keeps matching as
before. These tests
lock the matched values, the one-pass behaviour, and the unchanged default.
"""

from __future__ import annotations

import time

import pytest

from citry.util.routing import compile_route_pattern

_BOUND_SECONDS = 0.5


def _builtin_cache_routes() -> list:
    from citry import Citry
    from citry.ext.dependencies.routes import dependency_routes

    return [route for route in dependency_routes(Citry(autodiscover=False)) if route.path.startswith("cache/")]


def test_builtin_cache_routes_match_valid_paths() -> None:
    by_path = {route.path: route for route in _builtin_cache_routes()}
    cases = [
        ("cache/{class_id}.{script_type}", "cache/Table_a1b2c3.js", {"class_id": "Table_a1b2c3", "script_type": "js"}),
        (
            "cache/{class_id}.{vars_hash}.{script_type}",
            "cache/Table_a1b2c3.0f1e2d3c.css",
            {"class_id": "Table_a1b2c3", "vars_hash": "0f1e2d3c", "script_type": "css"},
        ),
    ]
    for route_path, path, expected in cases:
        route = by_path[route_path]
        match = compile_route_pattern(route.path, route.dotless_params).match(path)
        assert match is not None
        assert match.groupdict() == expected


def test_builtin_cache_routes_reject_a_long_path_in_one_pass() -> None:
    # A long run of `.`-separated parts with a final `/` never matches. With
    # the parameters stopping at each `.`, this is one scan rather than a
    # search over every way to split the dots.
    path = "cache/" + "a." * 20_000 + "/"
    for route in _builtin_cache_routes():
        pattern = compile_route_pattern(route.path, route.dotless_params)
        start = time.perf_counter()
        assert pattern.match(path) is None
        assert time.perf_counter() - start < _BOUND_SECONDS


@pytest.mark.parametrize(
    ("route", "path", "expected"),
    [
        ("files/{name}.json", "files/my.data.json", {"name": "my.data"}),
        ("dl/{name}.{ext}", "dl/archive.tar.gz", {"name": "archive.tar", "ext": "gz"}),
        ("post/{slug}-{id}", "post/my-cool-post-42", {"slug": "my-cool-post", "id": "42"}),
    ],
)
def test_a_route_without_dotless_params_matches_as_before(route: str, path: str, expected: dict[str, str]) -> None:
    match = compile_route_pattern(route).match(path)
    assert match is not None
    assert match.groupdict() == expected
