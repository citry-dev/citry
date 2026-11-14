"""
Django's ``reverse()`` gives the same URLs for Citry's routes as before, quickly.

"The same" holds for routes mounted without a parent pattern whose
parameter accepts ``/``; under such a parent, ``reverse()`` can now refuse
a URL whose Citry part the route would split differently.

The Django integration keeps a regex for each Citry route with
parameters, which ``reverse()`` reads to build a URL and then searches the
URL with. These tests compare ``reverse()`` through that pattern with
``reverse()`` through the regex Citry used before (``_route_oracle``), on
generated routes and values, and check that the time ``reverse()`` takes
grows in step with the length of the values. The timing tests compare
values with ones eight times as long, so the result does not depend on how
fast the machine is.
"""

from __future__ import annotations

import random
import re
import types
from typing import Any

import pytest

from citry import Citry, Extension
from citry.util.routing import RouteResponse, URLRoute, route_reverse_regex

from ._growth import assert_grows_in_step
from ._route_oracle import reference_route_regex

django = pytest.importorskip("django", reason="the Django adapter tests need django")

# Each timing test compares values with ones this many times as long.
_GROWTH_FACTOR = 8


@pytest.fixture(scope="module", autouse=True)
def _django_settings() -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(ALLOWED_HOSTS=["*"])
        django.setup()


def _handler(_request: object, **params: str) -> RouteResponse:
    return RouteResponse(content=repr(params))


def _urlconf(routes: list[URLRoute]) -> tuple[Any, list[str]]:
    """
    Mount ``routes`` from an extension, and the same routes through the earlier regex.

    Each route ``r<i>`` gets a twin ``old<i>``, a plain ``re_path`` with
    the regex Citry used before, at the same full path.
    """
    from django.urls import re_path

    from citry.contrib.django import urlpatterns

    class Probe(Extension):
        name = "probe"
        urls = routes

    patterns = urlpatterns(Citry(extensions=[Probe]))
    probe = [pattern for pattern in patterns if (pattern.name or "").startswith("r")]
    full_paths = []
    for route in routes:
        full_path = f"ext/probe/{route.path}"
        full_paths.append(full_path)
        regex = reference_route_regex(full_path, route.dotless_params)
        probe.append(re_path(regex, _handler, name=route.name.replace("r", "old", 1)))
    urlconf = types.ModuleType("citry_reverse_urlconf")
    urlconf.urlpatterns = probe
    return urlconf, full_paths


def _reverse(urlconf: Any, name: str, **call: Any) -> str | None:
    from django.urls import NoReverseMatch, reverse

    try:
        return reverse(name, urlconf=urlconf, **call)
    except NoReverseMatch:
        return None


def test_reverse_gives_the_earlier_urls_on_generated_routes_and_values() -> None:
    rng = random.Random(602)  # noqa: S311 - test data, not secrets
    names = ["a", "b", "c", "d"]
    texts = [".", "-", "x", "/", ".x", "x.", "-.-", "--", "\n"]
    value_characters = [".", "-", "x", "/", "\n", "é", "%"]
    routes = []
    for index in range(150):
        count = rng.randint(1, 4)
        path = rng.choice([*texts, ""]) + "".join(
            "{" + name + "}" + (rng.choice(texts) if position < count - 1 else rng.choice([*texts, ""]))
            for position, name in enumerate(names[:count])
        )
        # A path that starts with `/` would follow `ext/probe/` with an empty segment.
        path = path.lstrip("/")
        dotless = frozenset(name for name in names[:count] if rng.random() < 0.4)
        routes.append(URLRoute(path, handler=_handler, name=f"r{index}", dotless_params=dotless))
    urlconf, _full_paths = _urlconf(routes)

    accepted = refused = 0
    for index, route in enumerate(routes):
        params = [name for name in names if "{" + name + "}" in route.path]
        for _ in range(30):
            values = {name: "".join(rng.choice(value_characters) for _ in range(rng.randint(0, 4))) for name in params}
            expected = _reverse(urlconf, f"old{index}", kwargs=values)
            assert _reverse(urlconf, f"r{index}", kwargs=values) == expected, (
                route.path,
                route.dotless_params,
                values,
            )
            # Positional values go through the same check.
            positional = [values[name] for name in params]
            assert _reverse(urlconf, f"r{index}", args=positional) == _reverse(urlconf, f"old{index}", args=positional)
            accepted += expected is not None
            refused += expected is None
    # Both answers came up often enough to mean something.
    assert accepted > 500
    assert refused > 500


def test_reverse_refuses_values_the_route_would_not_match() -> None:
    urlconf, _full_paths = _urlconf(
        [URLRoute("files/{name}.{ext}", handler=_handler, name="r0", dotless_params=frozenset({"name"}))]
    )
    assert _reverse(urlconf, "r0", kwargs={"name": "report", "ext": "txt"}) == "/ext/probe/files/report.txt"
    # The route splits `a.b.txt` as name="a", so it matches and reverse() accepts it, as before.
    assert _reverse(urlconf, "r0", kwargs={"name": "a.b", "ext": "txt"}) == "/ext/probe/files/a.b.txt"
    assert _reverse(urlconf, "r0", kwargs={"name": "a/b", "ext": "txt"}) is None
    assert _reverse(urlconf, "r0", kwargs={"name": "", "ext": "txt"}) is None


@pytest.mark.parametrize(
    ("path", "values", "length"),
    [
        # A `/` in the last value leaves the URL with one segment too many,
        # which the earlier regex found only after trying every split. The
        # length is short enough that the earlier regex still finishes, and
        # fails this test.
        pytest.param("pkg/{a}-{b}-{c}", lambda n: {"a": "-" * n, "b": "-", "c": "y/"}, 1_600, id="refused"),
        pytest.param("pkg/{a}.{b}.{c}", lambda n: {"a": "." * n, "b": ".", "c": "/"}, 1_600, id="refused-dots"),
        # Long values that the route matches.
        pytest.param("pkg/{a}-{b}-{c}", lambda n: {"a": "-" * n, "b": "-" * n, "c": "y"}, 20_000, id="accepted"),
        pytest.param(
            "pkg/{a}-{b}/{c}.js",
            lambda n: {"a": "x-" * n, "b": "y", "c": "z." * n},
            20_000,
            id="accepted-segments",
        ),
    ],
)
def test_reverse_takes_time_in_step_with_the_values(path: str, values: Any, length: int) -> None:
    urlconf, _full_paths = _urlconf([URLRoute(path, handler=_handler, name="r0")])
    expected_match = _reverse(urlconf, "r0", kwargs=values(1)) is not None

    def run(size: int) -> None:
        assert (_reverse(urlconf, "r0", kwargs=values(size)) is not None) == expected_match

    assert_grows_in_step(run, length // _GROWTH_FACTOR, length, factor=_GROWTH_FACTOR)


@pytest.mark.parametrize(
    ("path", "url", "length"),
    [
        # Each URL fails only at its end, after every parameter could have
        # taken part of the long run. The length is short enough that the
        # earlier regex still finishes, and fails this test.
        pytest.param("pkg/{a}-{b}-{c}", lambda n: "pkg/" + "-" * n + "y/", 1_600, id="refused"),
        pytest.param("pkg/{a}.{b}.{c}.js", lambda n: "pkg/" + "." * n + "x", 1_600, id="refused-tail"),
        pytest.param("pkg/{a}-{b}-{c}", lambda n: "pkg/" + "x-" * n + "y", 20_000, id="accepted"),
    ],
)
def test_the_regex_alone_takes_time_in_step_with_the_url(path: str, url: Any, length: int) -> None:
    # The converters refuse most bad URLs before reverse() runs the regex,
    # so check the regex on its own too.
    regex = re.compile(route_reverse_regex(path))
    expected = regex.search(url(4)) is not None

    def run(size: int) -> None:
        assert (regex.search(url(size)) is not None) == expected

    assert_grows_in_step(run, length // _GROWTH_FACTOR, length, factor=_GROWTH_FACTOR)


def test_a_reverse_call_that_stops_part_way_does_not_change_the_next_one() -> None:
    from django.urls import include, path, register_converter

    class Picky:
        regex = "[a-z]+"

        def to_python(self, value: str) -> str:
            return value

        def to_url(self, value: str) -> str:
            # Refusing here stops reverse() part way through the values.
            if value == "no":
                raise ValueError(value)
            return value

    register_converter(Picky, "citry_picky")

    class Probe(Extension):
        name = "probe"
        urls = [URLRoute("f/{a}.{b}", handler=_handler, name="r0", dotless_params=frozenset({"a", "b"}))]

    from citry.contrib.django import urlpatterns

    urlconf = types.ModuleType("citry_reverse_stop_urlconf")
    urlconf.urlpatterns = [path("<citry_picky:p>/", include(urlpatterns(Citry(extensions=[Probe]))))]
    # `a` is converted before the parent's `p` refuses the call.
    assert _reverse(urlconf, "r0", kwargs={"a": "x", "p": "no", "b": "y"}) is None
    # A dotless `a` cannot hold a `.`, whatever an earlier call left behind.
    assert _reverse(urlconf, "r0", kwargs={"b": "y", "a": "u.v", "p": "ok"}) is None
    assert _reverse(urlconf, "r0", kwargs={"b": "y", "a": "u", "p": "ok"}) == "/ok/ext/probe/f/u.y"


def test_without_the_other_values_a_dotless_value_with_a_dot_is_refused() -> None:
    # Django always hands the converter all values; a direct call has none.
    from citry.contrib.django import _citry_route_pattern_class

    pattern = _citry_route_pattern_class()("f/{a}.{b}", frozenset({"a"}), name=None)
    assert pattern.converters["b"].to_url("x.y") == "x.y"
    with pytest.raises(ValueError, match="dotless"):
        pattern.converters["a"].to_url("x.y")
