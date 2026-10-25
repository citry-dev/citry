"""
Data for the browser converts and serializes in a bounded number of Python frames.

A Vue component's data nests about two levels for each `<c-for>` it sits in,
so a deep template sends deep data. These tests run each step that reads
that data under a recursion limit only a little above the frames already in
use, and check that the result is what a recursive copy gives.
"""

from __future__ import annotations

import json
import math
import random
import re
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component, Const, Secret
from citry._vue import prepared, serialization
from citry._vue.json_data import _DIRECT_JSON_DEPTH, _copy_evaluated_json, _json_plain, _secret_key_path
from citry.util import deep_json
from citry.util.html import script_json

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# Deeper than any recursion limit these tests set, so a walk that used one
# frame per level would fail.
DEEP = 2000


@contextmanager
def _frames_left(room: int) -> Iterator[None]:
    """Set the recursion limit to the frames in use plus ``room``."""
    depth = 0
    frame = sys._getframe()
    while frame is not None:
        depth += 1
        frame = frame.f_back
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(depth + room)
    try:
        yield
    finally:
        sys.setrecursionlimit(limit)


def _nested(depth: int, leaf: object, *, wrap: Callable[[object, int], object] | None = None) -> object:
    """Build ``depth`` levels around ``leaf``, alternating dicts and lists unless ``wrap`` says otherwise."""
    value = leaf
    for level in range(depth):
        if wrap is not None:
            value = wrap(value, level)
        elif level % 2:
            value = {"item": value, "n": level}
        else:
            value = [level, value]
    return value


def test_json_plain_copies_deep_data_in_bounded_frames() -> None:
    # Tuples, Consts and translated text inside deep data convert as they do near the top.
    value = _nested(DEEP, "bottom", wrap=lambda inner, level: (Const(inner),) if level % 3 == 0 else {"k": inner})
    expected = _nested(DEEP, "bottom", wrap=lambda inner, level: [inner] if level % 3 == 0 else {"k": inner})
    with _frames_left(150):
        plain = _json_plain(value)
    assert plain == expected


def test_json_plain_returns_containers_it_built_itself() -> None:
    shared: list[object] = ["shared"]
    value = _nested(DEEP, shared)
    plain = _json_plain(value)
    # Walk down level by level with a loop, comparing identities.
    source, copy = value, plain
    for _ in range(DEEP):
        assert copy is not source
        source = source["item"] if isinstance(source, dict) else source[1]  # type: ignore[index]
        copy = copy["item"] if isinstance(copy, dict) else copy[1]  # type: ignore[index]
    assert copy == shared
    assert copy is not shared


def _cycle_at(depth: int) -> object:
    loop: list[object] = []
    loop.append(_nested(depth, loop))
    return loop


@pytest.mark.parametrize(
    ("leaf", "error", "message"),
    [
        (math.nan, ValueError, "must contain only finite numbers, got nan"),
        (object(), TypeError, "must contain only dicts, lists, strings, numbers, booleans, and None, got object"),
        (Secret("hidden"), TypeError, r"must not contain a citry\.Secret"),
        ({1: "x"}, TypeError, "must use only string dict keys, got int key 1"),
    ],
)
@pytest.mark.parametrize("depth", [3, _DIRECT_JSON_DEPTH + 10, DEEP])
def test_json_plain_refuses_a_value_with_the_same_error_at_any_depth(
    leaf: object, error: type[Exception], message: str, depth: int
) -> None:
    # Values past `_DIRECT_JSON_DEPTH` go through the stack walk, which
    # must raise exactly what the direct calls raise.
    with pytest.raises(error, match=message):
        _json_plain(_nested(depth, leaf))


@pytest.mark.parametrize("depth", [3, _DIRECT_JSON_DEPTH + 10, DEEP])
def test_json_plain_refuses_a_loop_at_any_depth(depth: int) -> None:
    with pytest.raises(ValueError, match="must not contain itself"):
        _json_plain(_cycle_at(depth))


def test_json_plain_reports_the_first_refused_value_in_reading_order() -> None:
    # The first leaf fails only near the top and the second only deep down,
    # so the error names the first one whichever way each is walked.
    value = {"a": _nested(DEEP, math.inf), "b": _nested(3, object())}
    with pytest.raises(ValueError, match="got inf"):
        _json_plain(value)


def test_secret_key_path_finds_a_deep_secret_in_bounded_frames() -> None:
    value = {"rows": _nested(DEEP, Secret("hidden"), wrap=lambda inner, _level: [inner])}
    with _frames_left(150):
        path = _secret_key_path(value)
    assert path == '["rows"]' + "[0]" * DEEP


def test_secret_key_path_skips_a_loop_and_finds_the_secret_after_it() -> None:
    loop: list[object] = []
    loop.append(loop)
    assert _secret_key_path({"a": loop, "b": {"c": Secret("hidden")}}) == '["b"]["c"]'


def test_copy_evaluated_json_copies_deep_data_in_bounded_frames() -> None:
    value = _nested(DEEP, "bottom")
    with _frames_left(150):
        copy = _copy_evaluated_json(value)
    assert copy == value
    # Walk down level by level with a loop: every container is a new one.
    source, copied = value, copy
    for _ in range(DEEP):
        assert copied is not source
        source = source["item"] if isinstance(source, dict) else source[1]  # type: ignore[index]
        copied = copied["item"] if isinstance(copied, dict) else copied[1]  # type: ignore[index]


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        -0.0,
        5e-324,
        2**64,
        "</script> \u2028 caf\u00e9 \U0001f600 \ud800",
        [],
        {},
        (1, "a"),
        {"b": [1, {"z": None, "a": 2.5}], "a": True, 3: "int key", 0.5: "float key", None: "null key"},
    ],
)
@pytest.mark.parametrize("sort_keys", [False, True])
@pytest.mark.parametrize("ensure_ascii", [False, True])
def test_deep_json_dumps_writes_what_json_dumps_writes(value: object, sort_keys: bool, ensure_ascii: bool) -> None:
    if sort_keys and isinstance(value, dict) and len({type(key) for key in value}) > 1:
        # Keys of several types cannot be sorted, and both raise the same error.
        with pytest.raises(TypeError, match="not supported between instances"):
            json.dumps(value, sort_keys=True)
        with pytest.raises(TypeError, match="not supported between instances"):
            deep_json.dumps(value, sort_keys=True, ensure_ascii=ensure_ascii)
        return
    expected = json.dumps(
        value, allow_nan=False, separators=(",", ":"), sort_keys=sort_keys, ensure_ascii=ensure_ascii
    )
    assert deep_json.dumps(value, sort_keys=sort_keys, ensure_ascii=ensure_ascii) == expected


@pytest.mark.parametrize(
    ("value", "error", "message"),
    [
        ([1, math.nan], ValueError, "Out of range float values are not JSON compliant"),
        ({"a": object()}, TypeError, "Object of type object is not JSON serializable"),
        ({(1,): 1}, TypeError, "keys must be str, int, float, bool or None, not tuple"),
        (_cycle_at(3), ValueError, "Circular reference detected"),
    ],
)
def test_deep_json_dumps_raises_what_json_dumps_raises(value: object, error: type[Exception], message: str) -> None:
    with pytest.raises(error, match=message):
        json.dumps(value, allow_nan=False)
    with pytest.raises(error, match=message):
        deep_json.dumps(value, sort_keys=False, ensure_ascii=True)


def test_deep_json_dumps_writes_deep_data_in_bounded_frames() -> None:
    value = _nested(DEEP, "</b>")
    with _frames_left(150):
        text = deep_json.dumps(value, sort_keys=True, ensure_ascii=True)
    assert text == json.dumps(value, separators=(",", ":"), sort_keys=True)


def test_script_json_writes_deep_data_in_bounded_frames() -> None:
    # On Python 3.11 `json.dumps` runs out of frames here, and script_json
    # writes the same text with its stack instead.
    value = _nested(DEEP, "</b>")
    with _frames_left(150):
        text = script_json(value, sort_keys=True)
    assert text == json.dumps(value, separators=(",", ":"), sort_keys=True).replace("<", "\\u003c")


def test_script_json_writes_the_same_text_when_json_dumps_runs_out_of_frames(monkeypatch: pytest.MonkeyPatch) -> None:
    # Only some interpreters stop `json.dumps` at this depth, so the test
    # stops it itself for every container, on any version. Scalars still go
    # through the real function, as the stack writer writes them with it.
    real_dumps = json.dumps
    value = {"rows": [{"b": "</p>", "a": [1, 2.5, None, True]}], "z": "caf\u00e9"}

    def dumps_without_frames(data: object, **kwargs: object) -> str:
        if isinstance(data, (dict, list, tuple)):
            raise RecursionError
        return real_dumps(data, **kwargs)  # type: ignore[arg-type]

    expected = script_json(value, sort_keys=True)
    monkeypatch.setattr(json, "dumps", dumps_without_frames)
    assert script_json(value, sort_keys=True) == expected


def _for_and_empty_chain(depth: int) -> type[Component]:
    """Build a Vue component whose template nests ``depth`` `<c-for>` tags, each followed by `<c-empty>`."""
    engine = Citry(autodiscover=False)
    opening = "".join(f'<c-for each="x{level} in items">' for level in range(depth))
    closing = "</c-for><c-empty>none</c-empty>" * depth

    class Chain(Component):
        citry = engine

        def template_data(self, kwargs, slots):
            return {"items": [1], "n": 7}

        template = opening + "{{ n }}" + closing
        js = """
$component({});
"""

    return Chain


def test_a_deep_c_for_chain_renders_with_little_stack_left() -> None:
    # Each level adds about two levels to the data Vue receives, so at 256
    # the data nests deeper than the 500 frames left for Citry after the
    # 200 the host application uses.
    chain = _for_and_empty_chain(256)
    chain().render().serialize()  # the first render compiles and caches outside the limit

    def render_below(frames: int) -> str:
        if frames:
            return render_below(frames - 1)
        return chain().render().serialize()

    with _frames_left(200 + 500):
        html = render_below(200)
    # Vue's server render shows the one row's value inside the host.
    assert re.match(r'<div id="citry-vue-[0-9a-f]+">7</div><script', html)


@pytest.mark.parametrize(
    "text",
    [
        '{"b": [1, 2.5, -0.0, 1e300, 12345678901234567890], "a": {"x": null, "y": true, "z": false}}',
        '  [ "\\u00e9\\ud83d\\ude00", "\\n\\t\\"", "", [], {} ]  ',
        '{"a": 1, "a": 2}',
        "[NaN, Infinity, -Infinity]",
        '"plain"',
        "-3",
    ],
)
def test_deep_json_loads_reads_what_json_loads_reads(text: str) -> None:
    # `repr` compares NaN, which never equals itself, and the sign of -0.0.
    assert repr(deep_json.loads(text)) == repr(json.loads(text))
    assert repr(deep_json.loads(text.encode("utf-16"))) == repr(json.loads(text.encode("utf-16")))
    pairs: list[object] = []
    constants: list[str] = []

    def keep_pairs(items: list[tuple[str, object]]) -> object:
        pairs.append(items)
        return ("object", items)

    def keep_constant(name: str) -> object:
        constants.append(name)
        return name

    ours = deep_json.loads(text, object_pairs_hook=keep_pairs, parse_constant=keep_constant)
    ours_calls = (list(pairs), list(constants))
    pairs.clear()
    constants.clear()
    assert ours == json.loads(text, object_pairs_hook=keep_pairs, parse_constant=keep_constant)
    # The hooks run for the same objects and constants, in the same order.
    assert ours_calls == (pairs, constants)


@pytest.mark.parametrize(
    "text",
    ["", "[1,]", '{"a" 1}', '{"a": 1,}', "[1 2]", '"\\x"', '"a', "tru", "[1]x", "﻿[1]", "{1: 2}", "01"],
)
def test_deep_json_loads_refuses_what_json_loads_refuses(text: str) -> None:
    with pytest.raises(json.JSONDecodeError):
        json.loads(text)
    with pytest.raises(json.JSONDecodeError):
        deep_json.loads(text)


def test_deep_json_loads_reads_deep_text_in_bounded_frames() -> None:
    text = "[" * DEEP + '{"k": 1}' + "]" * DEEP
    with _frames_left(150):
        value = deep_json.loads(text)
    expected = json.loads(text)
    assert value == expected


def _deep_data_page(*, vue: bool) -> type[Component]:
    engine = Citry(autodiscover=False)

    class DeepData(Component):
        citry = engine

        def js_data(self, kwargs, slots):
            # Nested deeper than the frames left, so a walk that used one
            # frame per level would fail.
            return {"deep": _nested(DEEP, "bottom")}

        def template_data(self, kwargs, slots):
            return {"label": "deep"}

        template = """
<p>{{ label }}</p>
"""

    if vue:
        DeepData.js = """
$component({});
"""
    return DeepData


@pytest.mark.parametrize("vue", [False, True])
def test_deep_js_data_renders_with_little_stack_left(vue: bool) -> None:
    page = _deep_data_page(vue=vue)
    page().render().serialize()  # the first render compiles and caches outside the limit
    with _frames_left(300):
        html = page().render().serialize()
    assert "deep" in html


def test_prepared_server_data_is_copied_the_same_way_at_any_depth(monkeypatch: pytest.MonkeyPatch) -> None:
    value = {"rows": [{"b": (1, 2.5), "a": "é"}, None], "n": True}
    expected = prepared._detach_object(value, "server_data")
    # The standard round trip stops on deep data on some interpreters, so
    # the test stops it itself to check the copy that replaces it.
    real_dumps = json.dumps

    def dumps_without_frames(data: object, **kwargs: object) -> str:
        if isinstance(data, (dict, list, tuple)):
            raise RecursionError
        return real_dumps(data, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(json, "dumps", dumps_without_frames)
    copy = prepared._detach_object(value, "server_data")
    assert copy == expected
    assert repr(copy) == repr(expected)


def test_prepared_server_data_that_holds_itself_is_refused() -> None:
    loop: list[object] = []
    loop.append(loop)
    # The key check stops at the loop, and the encoder then reports it.
    with pytest.raises(ValueError, match="Circular reference detected"):
        prepared._detach_object({"loop": loop}, "server_data")


def test_prepared_server_data_with_a_bad_key_deep_down_is_refused() -> None:
    with pytest.raises(TypeError, match="contains a non-string object key"):
        prepared._detach_object({"deep": _nested(DEEP, {1: "x"})}, "server_data")


class _Text(str):
    __slots__ = ()


class _Number(float):
    def __repr__(self) -> str:
        return "a number"


def test_prepared_server_data_fallback_copies_subclasses_as_the_round_trip_does(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = {"t": _Text("text"), "n": _Number(2.5), "rows": ((1, True), [None, -0.0])}
    expected = prepared._detach_object(value, "server_data")
    real_dumps = json.dumps

    def dumps_without_frames(data: object, **kwargs: object) -> str:
        if isinstance(data, (dict, list, tuple)):
            raise RecursionError
        return real_dumps(data, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(json, "dumps", dumps_without_frames)
    copy = prepared._detach_object(value, "server_data")
    assert repr(copy) == repr(expected)
    assert type(copy["t"]) is str
    assert type(copy["n"]) is float


def _random_json_value(rng: random.Random, depth: int) -> object:
    roll = rng.random()
    if depth > 4 or roll < 0.4:
        scalars = [None, True, False, 0, -12, 2**70, 1.5, -0.0, 1e-7, "", "a\u00e9\n", "\ud83d\ude00"]
        return rng.choice(scalars)
    if roll < 0.7:
        return {rng.choice("abcde"): _random_json_value(rng, depth + 1) for _ in range(rng.randrange(4))}
    return [_random_json_value(rng, depth + 1) for _ in range(rng.randrange(4))]


def test_deep_json_loads_matches_json_loads_on_random_documents() -> None:
    rng = random.Random(393)  # noqa: S311 - a seeded fixture, not a secret
    for _ in range(300):
        value = _random_json_value(rng, 0)
        text = json.dumps(value, indent=rng.choice([None, 1]), ensure_ascii=rng.random() < 0.5)
        assert repr(deep_json.loads(text)) == repr(json.loads(text))
        # A damaged copy is refused by both or read the same by both.
        cut = rng.randrange(len(text) + 1)
        damaged = text[:cut] + rng.choice(["", ",", "]", "\u0661", " x"]) + text[cut + 1 :]
        if re.search(r"\\u(?![0-9a-fA-F]{4})", damaged):
            # A broken `\u` escape is the one case PyPy's own decoder reads
            # differently (see `deep_json`); skip it so the test holds there.
            continue
        try:
            expected = repr(json.loads(damaged))
        except json.JSONDecodeError:
            with pytest.raises(json.JSONDecodeError):
                deep_json.loads(damaged)
        else:
            assert repr(deep_json.loads(damaged)) == expected


def test_a_vue_fragment_mount_reads_deep_prepared_data_back(monkeypatch: pytest.MonkeyPatch) -> None:
    real_loads = json.loads

    def loads_without_frames(text: object, **kwargs: object) -> object:
        raise RecursionError

    text = json.dumps({"deep": _nested(DEEP, "bottom")})
    expected = real_loads(text)
    monkeypatch.setattr(json, "loads", loads_without_frames)
    assert serialization._loads_own_json(text) == expected
