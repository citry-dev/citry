"""
Ask Rust to write the JSON of an ordinary component's leaf data (level B2 of the native render path).

A leaf program is a component template compiled into one reusable program
with no component or slot nodes; its leaf data is the values that program
sends to the browser. When assembly (``assemble_typed_render`` in
``citry/_vue/direct_capture.py``) records an occurrence whose body is one
leaf program (an ordinary component, or a ``simple = "vue"`` row that Rust
did not read), it copies
each leaf value into the occurrence's ``preparedData`` dict, and serialize
later writes that dict as JSON. On the precompile path, where no browser
hook reads or changes prepared data, assembly calls ``take`` first. When
Rust wrote every value, assembly stores ``PLACEHOLDER`` under each key
instead of a copy, so every reader of the dict's keys sees the same keys as
without Rust, and the manifest encoder writes each value's JSON at its key.

Rust writes only exact plain data: ``None``, ``bool``, an ``int`` within
64 bits, a finite ``float``, a ``str`` with a UTF-8 form, and exact
``dict`` (with exact ``str`` keys), ``list`` and ``tuple`` containers,
nested at most 200 deep and with no container inside itself. For anything
else ``take`` returns a reason, and assembly converts the leaf in Python as
it does without Rust, so Python raises its own errors, such as its refusal
of a ``citry.Secret``. ``docs/design/native_render.md`` lists every case.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from citry._vue import native_render as _native_render

if TYPE_CHECKING:
    from citry_core import _rust


class _LeafJsonPlaceholder:
    """
    The value assembly stores under a leaf key whose JSON Rust wrote.

    JSON encoding refuses it, so an item written without Rust's JSON fails
    loudly instead of sending a wrong value. Copying or pickling it gives
    back the one instance, which the encoder recognizes by identity. No
    user value can be this object: assembly copies every other value into
    plain JSON types first.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "<leaf JSON written by Rust>"

    def __copy__(self) -> _LeafJsonPlaceholder:
        return self

    def __deepcopy__(self, memo: object) -> _LeafJsonPlaceholder:
        return self

    def __reduce__(self) -> str:
        # Pickle stores a reference to the module attribute, so loading it
        # gives back this same object.
        return "PLACEHOLDER"


PLACEHOLDER = _LeafJsonPlaceholder()


def take(values: dict[str, object]) -> _rust.native_render._LeafJson | str:
    """
    Return Rust's JSON of one leaf's data, or the reason Python must convert it.

    Assembly calls this only on the Rust path (``native_render.ACTIVE``), so
    the Rust module is loaded. The reason is ``value_read_key`` when the data
    holds a key other code reads values from, or Rust's own reason
    (``not_plain``, ``non_finite``, ``big_int``, ``not_utf8``, ``cycle``,
    ``too_deep``). A Rust panic raises ``RuntimeError``.
    """
    # Other code reads these two keys' values from the occurrence's dict, so
    # they must hold real values: the Events extension and the protocol's
    # checks read opaqueHtml, and the prepared view's call references read
    # calls. Leaf programs write only citry-prefixed keys, so no page reaches
    # this guard. Two lookups cost less than a set test over every key.
    if "opaqueHtml" in values or "calls" in values:
        return "value_read_key"
    native = cast("type[_rust.native_render]", _native_render.native)
    return native._leaf_values_json(values, PLACEHOLDER)
