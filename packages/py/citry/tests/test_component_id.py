"""
Tests for the per-component render id (``gen_id`` / ``gen_render_id``).

These call the real generators directly. The autouse ``_deterministic_render_ids``
fixture (conftest) only patches ``citry.component.gen_render_id`` to a counter for
deterministic marker assertions, so the production generators here are untouched.
"""

import re

from citry.util.id import gen_id, gen_render_id


def test_gen_id_is_six_base62_chars():
    pattern = re.compile(r"[0-9A-Za-z]{6}")
    assert all(pattern.fullmatch(gen_id()) for _ in range(200))


def test_gen_render_id_prefixes_c():
    pattern = re.compile(r"c[0-9A-Za-z]{6}")
    assert all(pattern.fullmatch(gen_render_id()) for _ in range(200))


def test_ids_are_unique_within_a_process():
    # Ids are a counter off a random base, so a run of them never collides: this
    # is what guarantees no two components on one page share a marker.
    ids = [gen_id() for _ in range(20000)]
    assert len(set(ids)) == len(ids)


def test_consecutive_ids_differ():
    first = gen_id()
    second = gen_id()
    assert first != second
