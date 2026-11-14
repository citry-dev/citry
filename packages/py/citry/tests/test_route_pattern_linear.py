"""
A route matches a request path in time that grows in step with the path's length.

Every adapter matches a request with ``match_route_pattern``, which splits
the path at each ``/`` and then splits each segment between its parameters
without trying every possible split. These tests lock three things: the
matcher gives the same values as the route's regex
(``compile_route_pattern``, which Django keeps for ``reverse()``), it
refuses a route with two parameters side by side, and the time it takes
grows in step with the path's length. The timing tests compare a path with
one eight times as long, so the result does not depend on how fast the
machine is.
"""

from __future__ import annotations

import random
import re

import pytest

from citry import Citry, Extension
from citry.util.routing import (
    RouteResponse,
    URLRoute,
    check_route_table,
    compile_route_pattern,
    match_route,
    match_route_pattern,
)

from ._growth import assert_grows_in_step

# Each timing test compares a path with one this many times as long.
_GROWTH_FACTOR = 8


def _handler(_request: object, **params: str) -> RouteResponse:
    return RouteResponse(content=repr(params))


def _builtin_cache_routes() -> list:
    from citry.ext.dependencies.routes import dependency_routes

    return [route for route in dependency_routes(Citry(autodiscover=False)) if route.path.startswith("cache/")]


def _regex_match(route: str, dotless: frozenset[str], path: str) -> dict[str, str] | None:
    match = compile_route_pattern(route, dotless).fullmatch(path)
    return None if match is None else match.groupdict()


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
        assert match_route_pattern(route.path, route.dotless_params, path) == expected


def test_builtin_cache_routes_reject_a_long_path_quickly() -> None:
    # A long run of `.`-separated parts: with a final `/` it has one segment
    # too many, and without it the last parameter takes everything after the
    # dotless ones.
    def path(parts: int) -> str:
        return "cache/" + "a." * parts + "x"

    for route in _builtin_cache_routes():

        def match_and_reject(request_path: str, route=route) -> None:
            assert match_route_pattern(route.path, route.dotless_params, request_path + "/") is None
            matched = match_route_pattern(route.path, route.dotless_params, request_path)
            assert matched is not None
            assert matched["script_type"].endswith(".x")

        assert_grows_in_step(match_and_reject, path(2_500), path(20_000), factor=_GROWTH_FACTOR)


@pytest.mark.parametrize(
    ("route", "path", "expected"),
    [
        ("files/{name}.json", "files/my.data.json", {"name": "my.data"}),
        ("dl/{name}.{ext}", "dl/archive.tar.gz", {"name": "archive.tar", "ext": "gz"}),
        ("post/{slug}-{id}", "post/my-cool-post-42", {"slug": "my-cool-post", "id": "42"}),
    ],
)
def test_a_route_without_dotless_params_matches_as_before(route: str, path: str, expected: dict[str, str]) -> None:
    assert match_route_pattern(route, frozenset(), path) == expected
    assert _regex_match(route, frozenset(), path) == expected


def test_match_route_pattern_gives_the_regex_answer_on_generated_routes() -> None:
    rng = random.Random(4285)  # noqa: S311 - test data, not secrets
    names = ["a", "b", "c", "d"]
    texts = ["", ".", "-", "x", "/", ".x", "x.", "--", "{1}", "\n", "é"]
    path_characters = [".", "-", "x", "/", "y", "\n", "é"]
    compared = refused = 0
    for _ in range(600):
        count = rng.randint(1, 4)
        between = [rng.choice(texts) for _ in range(count)]
        route = rng.choice(texts) + "".join(
            "{" + name + "}" + text for name, text in zip(names, between, strict=False)
        )
        dotless = frozenset(name for name in names[:count] if rng.random() < 0.4)
        # A parameter followed directly by the next one has no single split.
        if "" in between[:-1]:
            with pytest.raises(ValueError, match="next to each other"):
                match_route_pattern(route, dotless, "x")
            refused += 1
            continue
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
            compared += 1
    # Both kinds of route came up often enough to mean something.
    assert compared > 10_000
    assert refused > 50


@pytest.mark.parametrize(
    ("route", "path", "expected"),
    [
        # Each earlier parameter takes as much as it can.
        ("{a}-{b}", "x-y-z", {"a": "x-y", "b": "z"}),
        ("{a}.{b}.{c}", "w.x.y.z", {"a": "w.x", "b": "y", "c": "z"}),
        ("v{a}.{b}/{c}-{d}.js", "vx.y.z/p-q-r.js", {"a": "x.y", "b": "z", "c": "p-q", "d": "r"}),
        ("{a}.{b}", "x.y.z", {"a": "x.y", "b": "z"}),
        ("{a}-{b}", "x-", None),
        ("{a}-{b}", "x-y/", None),
        # A parameter holds any character but `/`, a newline included.
        ("{a}-{b}", "x-y\n", {"a": "x", "b": "y\n"}),
        ("call", "call\n", None),
    ],
)
def test_several_parameters_in_one_segment(route: str, path: str, expected: dict[str, str] | None) -> None:
    assert match_route_pattern(route, frozenset(), path) == expected
    assert _regex_match(route, frozenset(), path) == expected


def test_dotless_params_split_at_the_first_dot() -> None:
    route = "files/{name}.{ext}"
    assert match_route_pattern(route, frozenset(), "files/report.v2.txt") == {"name": "report.v2", "ext": "txt"}
    assert match_route_pattern(route, frozenset({"name"}), "files/report.v2.txt") == {
        "name": "report",
        "ext": "v2.txt",
    }


def test_only_the_matched_routes_dotless_params_apply() -> None:
    # The parent's dotless_params names `name`, but only the child, which
    # has the handler, decides how its full path is matched.
    routes = [
        URLRoute(
            "files/{name}",
            dotless_params=frozenset({"name"}),
            children=[URLRoute(".{ext}", handler=_handler)],
        )
    ]
    matched = match_route(routes, "files/report.v2.txt")
    assert matched is not None
    assert matched.params == {"name": "report.v2", "ext": "txt"}


@pytest.mark.parametrize(
    ("routes", "message"),
    [
        pytest.param(
            [URLRoute("{year}{month}", handler=_handler)],
            "'{year}{month}' puts the parameters {year} and {month} next to each other",
            id="one-path",
        ),
        pytest.param(
            [URLRoute("ext/", children=[URLRoute("files/{name}{ext}", handler=_handler, name="file")])],
            "'files/{name}{ext}' (name 'file', full path 'ext/files/{name}{ext}') puts the parameters",
            id="one-path-below-a-parent",
        ),
        pytest.param(
            [URLRoute("files/{name}", name="files", children=[URLRoute("{ext}", handler=_handler)])],
            "'{ext}' is joined to the path before it, 'files/{name}' (name 'files'), as plain text,"
            " which makes 'files/{name}{ext}'",
            id="parent-and-child",
        ),
        pytest.param(
            [URLRoute("files/{a}{b}/", name="group", children=[URLRoute("x", handler=_handler)])],
            "'files/{a}{b}/' (name 'group'), a parent of 'x' (full path 'files/{a}{b}/x'), puts the parameters",
            id="inside-a-parent",
        ),
        pytest.param(
            [URLRoute("pkg/{name}/{name}", handler=_handler)],
            "'pkg/{name}/{name}' uses the parameter {name} twice",
            id="repeated-name",
        ),
        pytest.param(
            [URLRoute("pkg/{name}/", children=[URLRoute("{name}", handler=_handler)])],
            "One comes from the earlier path 'pkg/{name}/' and one from '{name}'",
            id="repeated-name-across-parent-and-child",
        ),
    ],
)
def test_check_route_table_refuses_an_ambiguous_route(routes: list[URLRoute], message: str) -> None:
    with pytest.raises(ValueError, match=re.escape(message)):
        check_route_table(routes)


def test_check_route_table_accepts_parameters_with_text_between_them() -> None:
    check_route_table(
        [
            URLRoute("files/{name}.{ext}", handler=_handler),
            URLRoute(
                "files/{name}", children=[URLRoute("/{ext}", handler=_handler), URLRoute("-{v}", handler=_handler)]
            ),
            # A parent without a handler is checked only as part of its children's paths.
            URLRoute("{a}", children=[URLRoute("-{b}", handler=_handler)]),
            *_builtin_cache_routes(),
        ]
    )


def test_a_route_that_skipped_the_check_is_refused_on_every_request() -> None:
    # match_route checks each full path too, so a table that was never
    # mounted cannot quietly pick one of the splits.
    routes = [URLRoute("files/{name}", children=[URLRoute("{ext}", handler=_handler)])]
    with pytest.raises(ValueError, match="next to each other"):
        match_route(routes, "files/abc")


@pytest.mark.parametrize(
    ("route", "dotless", "build", "length"),
    [
        # Each path makes the route's regex try every split of the long
        # segment. The matcher rejects the first four before it splits the
        # segment (one segment too many, or a missing suffix).
        ("{a}-{b}", frozenset(), lambda n: "-" * n + "/", 50_000),
        ("{a}-{b}-{c}", frozenset(), lambda n: "-" * n + "/", 50_000),
        ("{a}-{b}-{c}x", frozenset(), lambda n: "-" * n, 50_000),
        ("{a}.{b}.{c}", frozenset(), lambda n: "." * n + "/", 50_000),
        # These reach the split and fail only after searching the whole
        # segment: the search from the right, the split at each `.`, and
        # the general walk for a dotless parameter followed by other text.
        ("{a}-{b}-{c}", frozenset(), lambda n: "x" * n + "-y", 50_000),
        ("{a}.{b}.{c}", frozenset({"a", "b"}), lambda n: "x" * n + ".y", 50_000),
        ("{a}-{b}.{c}", frozenset({"b"}), lambda n: "-" * n + "x", 8_000),
        ("{a}.{b}-{c}", frozenset({"a", "c"}), lambda n: "x." + "-" * n + ".", 8_000),
    ],
    ids=[
        "two",
        "three",
        "three-with-suffix",
        "three-dots",
        "from-the-right",
        "at-dots",
        "general-walk",
        "general-walk-dot-first",
    ],
)
def test_several_parameters_in_one_segment_reject_a_long_path_quickly(
    route: str, dotless: frozenset[str], build, length: int
) -> None:
    def reject(path: str) -> None:
        assert match_route_pattern(route, dotless, path) is None

    short = length // _GROWTH_FACTOR
    assert_grows_in_step(reject, build(short), build(length), factor=_GROWTH_FACTOR)


def test_several_parameters_in_one_segment_split_a_long_path_quickly() -> None:
    # A route without dotless parameters, so the split depends on the
    # whole run of `-`.
    route = "pkg/{name}-{version}.{build}"
    length = 80_000

    def match_both(dashes: int) -> None:
        matched = match_route_pattern(route, frozenset(), "pkg/" + "-" * dashes + ".1")
        assert match_route_pattern(route, frozenset(), "pkg/" + "-" * dashes) is None
        assert matched == {"name": "-" * (dashes - 2), "version": "-", "build": "1"}

    assert_grows_in_step(match_both, length // _GROWTH_FACTOR, length, factor=_GROWTH_FACTOR)


def _probe_app(routes: list[URLRoute]) -> Citry:
    class Probe(Extension):
        name = "probe"
        urls = routes

    return Citry(extensions=[Probe])


@pytest.mark.parametrize(
    "routes",
    [
        pytest.param([URLRoute("files/{name}.{ext}", handler=_handler)], id="one-path"),
        pytest.param(
            [URLRoute("files/{name}", children=[URLRoute(".{ext}", handler=_handler)])], id="parent-and-child"
        ),
    ],
)
def test_an_extension_route_with_parameters_around_a_dot_matches_quickly(routes: list[URLRoute]) -> None:
    app = _probe_app(routes)
    check_route_table(app.urls)
    matched = match_route(app.urls, "ext/probe/files/report.v2.txt")
    assert matched is not None
    assert matched.params == {"name": "report.v2", "ext": "txt"}

    def reject(dots: int) -> None:
        # The `.` run fills the segment, and the final `/` adds a segment
        # the route does not have.
        assert match_route(app.urls, "ext/probe/files/" + "." * dots + "/") is None
        # One segment with no `.` that can end `name`.
        assert match_route(app.urls, "ext/probe/files/" + "x" * dots) is None

    def split(dots: int) -> None:
        matched = match_route(app.urls, "ext/probe/files/" + "a." * dots + "x")
        assert matched is not None
        assert matched.params["ext"] == "x"

    for run in (reject, split):
        assert_grows_in_step(run, 20_000 // _GROWTH_FACTOR, 20_000, factor=_GROWTH_FACTOR)


def test_an_extension_route_with_several_parameters_in_one_segment_matches_quickly() -> None:
    app = _probe_app([URLRoute("pkg/{name}-{version}-{build}", handler=_handler)])
    matched = match_route(app.urls, "ext/probe/pkg/my-lib-1.2-3")
    assert matched is not None
    assert matched.params == {"name": "my-lib", "version": "1.2", "build": "3"}

    def match_and_reject(dashes: int) -> None:
        assert match_route(app.urls, "ext/probe/pkg/" + "-" * dashes) is not None
        # Only one `-` for the two the route needs, after a long `name`.
        assert match_route(app.urls, "ext/probe/pkg/" + "x" * dashes + "-y") is None

    assert_grows_in_step(match_and_reject, 8_000 // _GROWTH_FACTOR, 8_000, factor=_GROWTH_FACTOR)
