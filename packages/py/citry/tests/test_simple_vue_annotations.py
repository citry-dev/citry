"""
A ``simple = "vue"`` component whose class body holds an annotation.

This module deliberately has no ``from __future__ import annotations``: on
Python 3.14 an annotated class body then stores the function that builds
``__annotations__`` (``__annotate_func__``) instead of the dict, and the
first read caches the dict it builds in the class namespace
(``__annotations_cache__``). Both must count as class metadata, not as
members the component declares.
"""

import pytest

from citry import Citry, Component
from citry.component_render import _simple_vue_admission

from ._render_paths import render_both


class _AnnotatedBase:
    """A plain base whose annotation the component inherits."""

    label: str = "base"


def _render_annotated() -> str:
    app = Citry(autodiscover=False)

    class Counter(_AnnotatedBase, Component):
        citry = app
        simple = "vue"
        start: int = 3
        template = """
            <p>Count 3</p>
        """

    return Counter().render().serialize(deps_strategy="ignore")


def test_an_annotated_simple_vue_class_renders_on_both_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    rust, _python = render_both(_render_annotated, monkeypatch)
    assert "Count 3" in str(rust.result)


class _Annotated:
    count: int = 1


class _Unannotated:
    count = 1


@pytest.mark.parametrize("base", [_Annotated, _Unannotated], ids=["annotated", "unannotated"])
def test_reading_a_plain_bases_annotations_keeps_the_admission(base: type) -> None:
    app = Citry(autodiscover=False)

    class Counter(base, Component):  # type: ignore[valid-type,misc]
        citry = app
        simple = "vue"
        template = """
            <p>Count</p>
        """

    # Building the first record moves the i18n registry generation, which the
    # record's key holds, so that record is stale at once; the test compares
    # against the second record.
    _simple_vue_admission(Counter)
    admission = _simple_vue_admission(Counter)
    assert admission.rejection is None
    # Reading the base's annotations can add entries to its namespace (on
    # 3.14 always, earlier only for a base without annotations); it changes
    # nothing the admission depends on.
    base.__annotations__  # noqa: B018
    assert _simple_vue_admission(Counter) is admission
