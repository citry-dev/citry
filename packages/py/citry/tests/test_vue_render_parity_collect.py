"""The render parity collector finds the render code in compiled definitions."""

from __future__ import annotations

from scripts.vue_render_parity.collect import render_code

from citry._vue.compiler import NativeCompiler


def test_the_parity_collector_cuts_the_render_code_out_of_a_compiled_definition() -> None:
    # The collector finds the code by the lines around it in the browser
    # JavaScript. When `_vue/compiler.py` changes those lines, it records no
    # code and the parity check would compare nothing, so this compiles a real
    # definition and checks the cut.
    compiled = NativeCompiler().compile("<p>{{ name }}</p>", type_key="T")
    code = render_code(compiled.javascript)
    assert code is not None
    assert code.startswith("function render(")
    assert code.rstrip().endswith("}")
    assert "__citryRuntimeDefinitions" not in code
