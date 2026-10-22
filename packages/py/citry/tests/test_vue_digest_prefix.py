"""The shared-prefix digest gives exactly the ids the full digest gives."""

from __future__ import annotations

import hashlib
import json

import pytest

from citry._vue.direct_capture import _digest, _DigestPrefix

# Values in the shapes the placement and occurrence ids hash: template text,
# spans, class ids, routes, and keys, including text JSON has to escape.
TEMPLATE = '<c-for each="row in rows">\n  <c-Row #c-key="row.id" c-row="row" />\n</c-for>'
PREFIXES = [
    ((TEMPLATE, 12, 48, "app.Row"), ()),
    ((TEMPLATE, 0, 0, "app.Row"), ("slot@abc", "default")),
    ("citryOccurrence0123456789abcdef01234567",),
    ("ünïcödé ✓ 𝄞", None, True, 1.5),
    ('"quoted" \\ back\\slash \t tab \x00 nul', [], {}),
]
RESTS = [
    (("explicit", "row-1"),),
    (("explicit", "Ζήτα 🎉"),),
    (("explicit", '</script><!-- "x" \\ \n'),),
    (("explicit", ""),),
    ("citryPlacement0123456789abcdef01234567",),
    (("unkeyed",), 0, {"b": 1, "a": [2, 3]}),
]


@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize("rest", RESTS)
def test_prefix_digest_matches_full_digest(prefix: tuple[object, ...], rest: tuple[object, ...]) -> None:
    assert _DigestPrefix(*prefix).digest(*rest) == _digest(*prefix, *rest)


def test_digest_keeps_its_json_framing() -> None:
    values = (("src", 1, 2, "app.Row"), (), ("explicit", "ü"))
    text = json.dumps(values, sort_keys=True, separators=(",", ":"))
    assert _digest(*values) == hashlib.sha256(text.encode()).hexdigest()


def test_one_prefix_serves_many_rows_without_carrying_state() -> None:
    prefix = _DigestPrefix(TEMPLATE, 12, 48, "app.Row")
    for key in ("a", "b", "a"):
        assert prefix.digest(("explicit", key)) == _digest(TEMPLATE, 12, 48, "app.Row", ("explicit", key))


def test_empty_prefix_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one value"):
        _DigestPrefix()
