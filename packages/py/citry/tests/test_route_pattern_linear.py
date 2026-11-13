"""
A route matches a request path in time that grows in step with the path's length.

Two of the dependency routes place parameters next to each other with only
a ``.`` between them. They list those parameters in ``dotless_params``, so
each one stops at the next dot and a long path that never matches is
rejected after one scan of the regex. Any other route with several
parameters in one path segment is matched by ``match_route_pattern``
without the regex, which would try every way to split the segment between
the parameters. These tests lock the matched values, the one-pass
behaviour, and that ``match_route_pattern`` gives the regex's answer.
"""

from __future__ import annotations

import random
import time

import pytest

from citry import Citry, Extension
from citry.util.routing import RouteResponse, URLRoute, compile_route_pattern, match_route, match_route_pattern

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


def _regex_match(route: str, dotless: frozenset[str], path: str) -> dict[str, str] | None:
    match = compile_route_pattern(route, dotless).fullmatch(path)
    return None if match is None else match.groupdict()


def test_match_route_pattern_gives_the_regex_answer_on_generated_routes() -> None:
    rng = random.Random(4285)  # noqa: S311 - test data, not secrets
    names = ["a", "b", "c", "d"]
    texts = ["", ".", "-", "x", "/", ".x", "x.", "--", "{1}", "\n", "é"]
    path_characters = [".", "-", "x", "/", "y", "\n", "é"]
    for _ in range(400):
        count = rng.randint(1, 4)
        route = rng.choice(texts) + "".join("{" + name + "}" + rng.choice(texts) for name in names[:count])
        dotless = frozenset(name for name in names[:count] if rng.random() < 0.4)
        for _ in range(40):
            # Filling the route's own parameters gives many paths that match.
            path = route
            for name in names:
                filled = "".join(rng.choice(path_characters) for _ in range(rng.randint(0, 4)))
                path = path.replace("{" + name + "}", filled)
            if rng.random() < 0.3:
                path = "".join(rng.choice(path_characters) for _ in range(rng.randint(0, 12)))
            expected = _regex_match(route, dotless, path)
            got = match_route_pattern(route, dotless, path)
            assert got == expected, (route, sorted(dotless), path)
            # The handler gets the parameters as keyword arguments in route order.
            assert list(got or {}) == list(expected or {})


@pytest.mark.parametrize(
    ("route", "path", "expected"),
    [
        # Each earlier parameter takes as much as it can.
        ("{a}-{b}", "x-y-z", {"a": "x-y", "b": "z"}),
        ("{a}{b}{c}", "wxyz", {"a": "wx", "b": "y", "c": "z"}),
        ("v{a}.{b}/{c}-{d}.js", "vx.y.z/p-q-r.js", {"a": "x.y", "b": "z", "c": "p-q", "d": "r"}),
        ("{a}.{b}", "x.y.z", {"a": "x.y", "b": "z"}),
        ("{a}-{b}", "x-", None),
        ("{a}-{b}", "x-y/", None),
        ("{a}-{b}", "x-y\n", {"a": "x", "b": "y\n"}),
    ],
)
def test_several_parameters_in_one_segment(route: str, path: str, expected: dict[str, str] | None) -> None:
    assert match_route_pattern(route, frozenset(), path) == expected
    assert _regex_match(route, frozenset(), path) == expected


@pytest.mark.parametrize(
    ("route", "dotless", "path"),
    [
        # Each path almost matches and then fails at its end, so the regex
        # tries every split of the long segment: about 5 s, 2 s and 1.5 s.
        # A final `/` or a missing suffix is caught before the segment is split.
        ("{a}-{b}", frozenset(), "-" * 50_000 + "/"),
        ("{a}-{b}-{c}", frozenset(), "-" * 1_500 + "/"),
        ("{a}{b}{c}{d}", frozenset(), "x" * 300 + "/"),
        ("{a}-{b}-{c}x", frozenset(), "-" * 1_500),
        # These pass the quick checks, so the segment is split between the
        # parameters before the last one fails at the `.`: about 4 s and 2.5 s
        # on the regex.
        ("{a}-{b}-{c}", frozenset({"c"}), "-" * 1_500 + "."),
        ("{a}{b}{c}{d}", frozenset({"d"}), "x" * 300 + "."),
    ],
    ids=["two", "three", "four-adjacent", "three-with-suffix", "three-split", "four-split"],
)
def test_several_parameters_in_one_segment_reject_a_long_path_quickly(
    route: str, dotless: frozenset[str], path: str
) -> None:
    start = time.perf_counter()
    assert match_route_pattern(route, dotless, path) is None
    assert time.perf_counter() - start < _BOUND_SECONDS


def test_several_parameters_in_one_segment_split_a_long_path_quickly() -> None:
    # A route without dotless parameters: the regex takes time growing with
    # the square of the run of `-` when the `.` is missing.
    route = "pkg/{name}-{version}.{build}"
    start = time.perf_counter()
    matched = match_route_pattern(route, frozenset(), "pkg/" + "-" * 80_000 + ".1")
    assert match_route_pattern(route, frozenset(), "pkg/" + "-" * 80_000) is None
    assert time.perf_counter() - start < _BOUND_SECONDS
    assert matched == {"name": "-" * 79_998, "version": "-", "build": "1"}


def test_an_extension_route_with_several_parameters_in_one_segment_matches_quickly() -> None:
    def handler(_request: object, name: str, version: str, build: str) -> RouteResponse:
        return RouteResponse(content=f"{name} {version} {build}")

    class Probe(Extension):
        name = "probe"
        urls = [URLRoute("pkg/{name}-{version}-{build}", handler=handler)]

    app = Citry(extensions=[Probe])
    matched = match_route(app.urls, "ext/probe/pkg/my-lib-1.2-3")
    assert matched is not None
    assert matched.params == {"name": "my-lib", "version": "1.2", "build": "3"}

    start = time.perf_counter()
    assert match_route(app.urls, "ext/probe/pkg/" + "-" * 1_500 + "/") is None
    assert time.perf_counter() - start < _BOUND_SECONDS
