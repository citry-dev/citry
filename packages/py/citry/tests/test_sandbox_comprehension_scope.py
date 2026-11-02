"""
A `<c-for>` loop cannot reach Python's builtins through its iterable.

Citry runs a `<c-for>` clause as a generator expression, and Python evaluates an iterable
before its loop variable exists. A name the iterable reads is therefore a context
variable, also when it matches a loop variable. These tests render real components in both
sandbox modes.
"""

import platform

import pytest

from citry import Citry, Component

# PyPy adds the builtins to every namespace it evaluates in, so the unsandboxed mode reaches
# them there by design (`sandbox_expressions=False` is for trusted templates only).
IS_PYPY = platform.python_implementation() == "PyPy"


def _page(app: Citry, name: str, iterable: str, **context: object) -> type[Component]:
    class Page(Component):
        citry = app
        template = f"""
            <ul><c-for each="{name} in {iterable}"><li>{{{{ {name} }}}}</li></c-for></ul>
        """

        def template_data(self, kwargs, slots):
            return context

    return Page


UNSANDBOXED_ON_CPYTHON = pytest.param(
    False, marks=pytest.mark.skipif(IS_PYPY, reason="PyPy adds the builtins to every namespace")
)


@pytest.mark.parametrize("sandbox", [True, False])
@pytest.mark.parametrize("name", ["repr", "getattr", "type"])
def test_a_loop_variable_cannot_name_its_own_iterable(sandbox, name):
    # A control: `<c-for>` does not let a loop variable reuse a name its own iterable
    # reads, so this direct form never reached the sandbox. The nested form below does.
    page = _page(Citry(sandbox_expressions=sandbox), name, f"[{name}]")
    with pytest.raises(SyntaxError, match=f"Cannot define variable '{name}'"):
        page().render().serialize()


@pytest.mark.parametrize("name", ["repr", "getattr", "type"])
def test_a_nested_iterable_reads_the_context_with_the_sandbox_on(name):
    page = _page(Citry(), "item", f"[{name} for {name} in [{name}]]")
    with pytest.raises(KeyError, match=f"'{name}'"):
        page().render().serialize()
    page = _page(Citry(), "item", f"[{name} for {name} in [{name}]]", **{name: "mine"})
    assert "<li>mine</li>" in page().render().serialize()


@pytest.mark.parametrize("sandbox", [True, UNSANDBOXED_ON_CPYTHON])
def test_a_nested_iterable_never_shows_a_builtin(sandbox):
    page = _page(Citry(sandbox_expressions=sandbox), "item", "[repr for repr in [repr]]")
    with pytest.raises((KeyError, NameError), match="repr") as caught:
        page().render().serialize()
    assert "built-in" not in str(caught.value)
