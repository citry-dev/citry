"""
Short ids for rendered components (e.g. ``c1a2b3c4d``).

Every rendered component instance gets one. It scopes the component's CSS and JS
to its own elements on the page (through ``data-cid-<id>`` markers) and is used
as a lookup key by the browser-side code. The id is not a secret; it only has to
be unique among the components on a single rendered page.

An id is generated in two steps:

1. **Pick a number.** We keep a counter that goes 0, 1, 2, ... and start it at a
   random point, chosen once when this module is first loaded. Each id is the
   next number in that sequence. Counting upward means two ids in the same
   process are never equal (so two components on one page never collide), and
   the random starting point means two separate processes do not hand out the
   same sequence of ids.

2. **Turn the number into characters.** Ids use lowercase base 36. HTML
   attribute names are case-insensitive, so uppercase characters would let two
   distinct ids collapse onto one ``data-cid-*`` marker. Eight base-36
   characters preserve more space than the old six-character base-62 form.
   Rather than work out one character at a time, we build a table of all 36 x
   36 two-character pairs up front and split the number into four pairs.

The result has more address space than the prior mixed-case form, but is much
cheaper to produce than independent random draws: one counter step and four
table lookups. See docs/design/performance.md section 8.
"""

from __future__ import annotations

import itertools
import random
import re

from citry.constants import COMP_ID_PREFIX, UID_LENGTH

# Render ids are embedded in HTML attribute names and CSS attribute selectors.
# Keep their public override form to this lowercase, unescaped subset.
_ID_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_ID_BASE = len(_ID_ALPHABET)
_RENDER_ID_RE = re.compile(r"[a-z0-9_-]+")

# How many different ids exist: UID_LENGTH characters, each one of 36 choices.
# An id is a number somewhere in 0 .. _ID_SPACE - 1.
_ID_SPACE = _ID_BASE**UID_LENGTH

# A table of every two-character pair, in order, so ``_ID_CHUNK[n]`` is the pair
# for the number n (where 0 <= n < 36 * 36). Looking pairs up is faster than
# building the id one character at a time.
_ID_CHUNK = [_ID_ALPHABET[i // _ID_BASE] + _ID_ALPHABET[i % _ID_BASE] for i in range(_ID_BASE * _ID_BASE)]

# The counter, and the random point it starts from. Both are set once, when the
# module is first imported.
_id_base = random.randrange(_ID_SPACE)  # noqa: S311 (a DOM id, not a secret)
_id_counter = itertools.count()


def gen_id() -> str:
    """Return the next 8-character lowercase id, unique within the process."""
    # The next number in the sequence, wrapped back to the start if the counter
    # ever runs past the last id.
    value = (_id_base + next(_id_counter)) % _ID_SPACE
    # Split that number into four two-character pairs and look each up.
    value, low = divmod(value, _ID_BASE * _ID_BASE)
    value, middle_low = divmod(value, _ID_BASE * _ID_BASE)
    high, middle_high = divmod(value, _ID_BASE * _ID_BASE)
    return _ID_CHUNK[high] + _ID_CHUNK[middle_high] + _ID_CHUNK[middle_low] + _ID_CHUNK[low]


def gen_render_id() -> str:
    """Return a component render id: the ``c`` prefix plus a generated id."""
    return COMP_ID_PREFIX + gen_id()


def validate_render_id(value: object) -> str:
    """Return an id safe for Citry's case-insensitive HTML marker names."""
    if not isinstance(value, str):
        msg = f"Citry render ID must be a string, got {type(value).__name__}."
        raise TypeError(msg)
    if not _RENDER_ID_RE.fullmatch(value):
        msg = (
            f"Citry render ID {value!r} must use only lowercase ASCII letters, digits, hyphens, and underscores; "
            "render IDs are embedded in case-insensitive HTML attribute names."
        )
        raise ValueError(msg)
    return value
