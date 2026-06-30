"""
Tests for the optional expression sandbox toggle
(``Citry(sandbox_expressions=...)``, default on).

The promise: turning the sandbox off produces byte-identical output for any
successful render, and only removes the access controls. These render the same
templates under both modes and compare, and check that an expression the
sandbox rejects succeeds when the sandbox is off.
"""

import re

import pytest

from citry import Citry, Component
from citry_core.safe_eval import SecurityError, compile_expr


def _norm(html: str) -> str:
    # Render ids are a per-render counter in the test suite; normalize them so
    # two separate renders compare on everything except the ids themselves.
    return re.sub(r"c\d+", "cN", html)


def _render_tricky(c: Citry) -> str:
    """Render a page exercising the cases where plain eval could diverge."""

    class Row(Component):
        citry = c
        template = '<li class="{{ kind }}">{{ label }}</li>'

        def template_data(self, kwargs, slots):
            return {"kind": kwargs["kind"], "label": kwargs["label"]}

    class Page(Component):
        citry = c
        # - a <c-for> whose filter reads an OUTER variable (skip): the loop is a
        #   generator expression, the scoping case that motivated evaluating with
        #   one shared namespace.
        # - a computed component input (prefix + item).
        # - a walrus plus a comprehension that also reads the outer `skip`.
        template = (
            "<ul>"
            '<c-for each="item in items if item != skip">'
            '<c-Row c-kind="\'row\'" c-label="prefix + item" />'
            "</c-for>"
            "</ul>"
            "<p>{{ (kept := [x for x in items if x != skip]) and prefix + kept[0] }}</p>"
        )

        def template_data(self, kwargs, slots):
            return {"items": ["a", "b", "c"], "skip": "b", "prefix": "p-"}

    return _norm(Page().render().serialize())


def test_sandbox_off_is_byte_identical_to_sandbox_on():
    on = _render_tricky(Citry())
    off = _render_tricky(Citry(sandbox_expressions=False))
    assert on == off
    # And it really rendered the tricky bits: the filtered loop dropped "b",
    # the computed label kept the others, and the walrus/comprehension ran.
    assert "p-a" in on
    assert "p-c" in on
    assert ">p-b<" not in on


def test_default_is_sandboxed_and_blocks_unsafe_access():
    c = Citry()

    class Bad(Component):
        citry = c
        template = "{{ obj._secret }}"  # underscore attribute: blocked by the sandbox

        def template_data(self, kwargs, slots):
            return {"obj": kwargs["obj"]}

    holder = type("Holder", (), {"_secret": "hidden"})()
    with pytest.raises(SecurityError):
        Bad(obj=holder).render().serialize()


def test_sandbox_off_allows_what_the_sandbox_blocks():
    c = Citry(sandbox_expressions=False)

    class Open(Component):
        citry = c
        template = "{{ obj._secret }}"  # the same blocked access, now permitted

        def template_data(self, kwargs, slots):
            return {"obj": kwargs["obj"]}

    holder = type("Holder", (), {"_secret": "hidden"})()
    assert Open(obj=holder).render().serialize() == "hidden"


def test_unsandboxed_evaluation_exposes_no_builtins_and_cannot_plant_them():
    # Unsandboxed evaluation exposes no builtins (matching the sandbox), and the
    # builtins mapping is read-only and shared, so one expression cannot mutate
    # __builtins__ to leak a fake builtin into another expression's evaluation.
    plant = compile_expr("__builtins__.update({'len': lambda x: 999})", sandboxed=False)
    with pytest.raises(AttributeError):
        plant({})  # the read-only mapping refuses mutation
    use = compile_expr("len([1, 2, 3])", sandboxed=False)
    with pytest.raises(NameError):
        use({})  # len is still not a builtin here
