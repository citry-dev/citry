"""
Tests for the optional expression sandbox toggle
(``Citry(sandbox_expressions=...)``, default on).

The promise: turning the sandbox off produces byte-identical output for any
successful render, and only removes the access controls. These render the same
templates under both modes and compare, and check that an expression the
sandbox rejects succeeds when the sandbox is off.
"""

import re
import sys
from types import MappingProxyType

import pytest

from citry import Citry, Component, SecurityError
from citry_core.safe_eval import SecurityError as CoreSecurityError
from citry_core.safe_eval import compile_expr

from ._render_paths import render_both


def _norm(html: str) -> str:
    # Render ids are a per-render counter in the test suite; normalize them so
    # two separate renders compare on everything except the ids themselves.
    return re.sub(r"c\d+", "cN", html)


def test_security_error_is_the_exact_citry_core_class():
    assert SecurityError is CoreSecurityError


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


def _eval_hides_builtins() -> bool:
    """Whether this interpreter's ``eval`` finds no builtins behind an empty ``__builtins__`` mapping."""
    try:
        eval("len", {"__builtins__": MappingProxyType({})})  # noqa: S307
    except NameError:
        return True
    return False


def test_unsandboxed_evaluation_cannot_change_the_shared_builtins_mapping():
    # Every unsandboxed evaluation gets the same __builtins__ mapping, and it
    # is read-only, so an expression cannot change it for the next one.
    plant = compile_expr("__builtins__.update({'len': lambda x: 999})", sandboxed=False)
    with pytest.raises(AttributeError):
        plant({})  # the read-only mapping refuses mutation


@pytest.mark.skipif(
    not _eval_hides_builtins(),
    reason="this interpreter's eval still finds builtins when __builtins__ is an empty mapping",
)
def test_unsandboxed_evaluation_exposes_no_builtins():
    # On CPython an empty __builtins__ hides every builtin, matching the sandbox.
    use = compile_expr("len([1, 2, 3])", sandboxed=False)
    with pytest.raises(NameError):
        use({})


# The template text holds the six characters `\ud800`, an escape for a lone
# surrogate. Python decodes it to U+D800; an evaluator that decoded it to
# U+FFFD (the replacement character) reads the other key, so the page shows
# FFFD instead of SURR.
_SURROGATE_ROW = r"row['\ud800']"
_SURROGATE_DATA = r"data['\ud800']"
_SURROGATE_TEMPLATES = [
    f"<p>{{{{ {_SURROGATE_ROW} }}}}</p>",
    f"<p>{{{{ {_SURROGATE_ROW} or '' }}}}</p>",
    f'<p c-title="{_SURROGATE_ROW}">x</p>',
    f'<c-Child c-label="{_SURROGATE_ROW}" />',
    f"<p c-if=\"{_SURROGATE_ROW} == 'SURR'\">SURR</p>",
    f'<i c-for="it in {_SURROGATE_DATA}">{{{{ it }}}}</i>',
    f"<i c-for=\"it in {_SURROGATE_DATA}\">{{{{ it or '' }}}}</i>",
    f"<p>{{{{ f'{{{_SURROGATE_ROW}}}' }}}}</p>",
]
# The f-string template reuses its quote and a backslash inside the
# replacement field, which Python's own parser accepts only from 3.12
# (PEP 701). The sandbox parses it on every version, but with the sandbox off
# Python itself compiles the expression, so that case needs 3.12.
_PEP_701_TEMPLATE = _SURROGATE_TEMPLATES[-1]


def _render_surrogate_key(body: str, *, kind: bool | str, sandbox: bool) -> str:
    """Render ``body`` as a component's template with the data below, and return which key it read: SURR or FFFD."""
    engine = Citry(secret="x" * 32, autodiscover=False, sandbox_expressions=sandbox)

    class Child(Component):
        citry = engine

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

        template = """
            <b>{{ label }}</b>
        """

    class Leaf(Component):
        citry = engine
        simple = kind
        template = body

    class Page(Component):
        citry = engine

        def template_data(self, kwargs, slots):
            # chr() builds both keys because the ruff linter also decodes a
            # surrogate escape to U+FFFD, and would flag the two keys as one
            # repeated dict key.
            surrogate, replacement = chr(0xD800), chr(0xFFFD)
            return {
                "row": {surrogate: "SURR", replacement: "FFFD"},
                "data": {surrogate: ["SURR"], replacement: ["FFFD"]},
            }

        template = """
            <c-Leaf c-row="row" c-data="data" />
        """

    html = Page().render().serialize(deps_strategy="ignore")
    assert ("SURR" in html) != ("FFFD" in html), html
    return "SURR" if "SURR" in html else "FFFD"


@pytest.mark.parametrize("sandbox", [True, False], ids=["sandbox", "no-sandbox"])
@pytest.mark.parametrize("body", _SURROGATE_TEMPLATES)
def test_every_evaluator_reads_a_lone_surrogate_escape_as_python_does(
    body: str, sandbox: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    if body == _PEP_701_TEMPLATE and not sandbox and sys.version_info < (3, 12):
        pytest.skip("Python compiles this f-string only from 3.12 (PEP 701)")
    # Citry evaluates some of these templates with its generated leaf
    # evaluator (for simple paths) and the rest with the expression sandbox,
    # or plain Python when the sandbox is off. render_both renders on the
    # Rust and Python paths and checks they match; both must read U+D800.
    rust, _python = render_both(
        lambda: _render_surrogate_key(body, kind=False, sandbox=sandbox),
        monkeypatch,
    )
    assert rust.result == "SURR"


@pytest.mark.parametrize("sandbox", [True, False], ids=["sandbox", "no-sandbox"])
@pytest.mark.parametrize("body", [_SURROGATE_TEMPLATES[i] for i in (0, 2, 3, 5)])
def test_simple_vue_components_read_a_lone_surrogate_escape_as_python_does(
    body: str, sandbox: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A `simple = "vue"` component reads its template with the generated
    # leaf evaluator only (Citry rejects the other templates above for this
    # kind of component).
    rust, _python = render_both(
        lambda: _render_surrogate_key(body, kind="vue", sandbox=sandbox),
        monkeypatch,
    )
    assert rust.result == "SURR"
