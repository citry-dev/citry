"""Published citry 0.2.0 with the compatible custom core 1.3.0 wheel."""

# This executes a standalone runtime matrix inside Pyodide. Assertions,
# dynamic module execution, intentionally retained state, and compact Citry
# callback signatures are part of the proof rather than application code.
# ruff: noqa: ANN001, ANN201, ARG002, S101, S102, S108, SIM105

import builtins
import json
import sys
from importlib.metadata import version
from pathlib import Path

from citry import Citry, Component, citry


class Badge(Component):
    class Kwargs:
        label: str

    template = "<strong>{{ label }}</strong>"

    def template_data(self, kwargs, slots):
        return {"label": kwargs.label}


class Showcase(Component):
    css = ".showcase { color: rebeccapurple; }"
    js = """
      console.log("plain Citry JavaScript");
      $component(() => {});
    """
    template = """
      <section class="showcase">
        <h1>{{ title }}</h1>
        <c-if cond="items">
          <ul><c-for each="item in items"><li><c-badge c-label="item" /></li></c-for></ul>
        </c-if>
      </section>
    """

    def template_data(self, kwargs, slots):
        return kwargs


html = str(Showcase(title="Pyodide", items=["one", "two"]))
assert "<h1>Pyodide</h1>" in html
assert ">one</strong>" in html
assert ">two</strong>" in html
assert ".showcase { color: rebeccapurple; }" in html
assert 'console.log("plain Citry JavaScript")' in html
assert "$component(() => {})" in html

repeat_source = """
class Repeated(Component):
    citry = repeat_app
    template = "<p>{{ value }}</p>"
    def template_data(self, kwargs, slots):
        return kwargs
rendered = str(Repeated(value=expected))
"""
repeat_outputs = []
repeat_app = Citry(id_generator=lambda: "fixed")
for index in range(100):
    repeat_app.clear()
    namespace = {
        "Component": Component,
        "expected": "stable",
        "repeat_app": repeat_app,
    }
    if index == 25:
        try:
            compile("class Broken(", "<playground>", "exec")
        except SyntaxError:
            pass
    if index == 50:

        class Broken(Component):
            template = "{{ missing }}"

        try:
            str(Broken())
        except KeyError:
            pass
        citry.clear()
    exec(compile(repeat_source, "<playground>", "exec"), namespace)
    repeat_outputs.append(namespace["rendered"])

assert len(set(repeat_outputs)) == 1
assert ">stable</p>" in repeat_outputs[0]

builtins._citry_playground_probe = True
sys.modules["_citry_playground_probe"] = object()
probe_file = Path("/tmp/citry-playground-probe.txt")
probe_file.write_text("persists", encoding="utf-8")
citry.clear()
residual_state = {
    "builtins": getattr(builtins, "_citry_playground_probe", False),
    "filesystem": probe_file.exists(),
    "sys_modules": "_citry_playground_probe" in sys.modules,
}
assert all(residual_state.values())

json.dumps(
    {
        "citry": version("citry"),
        "citry_core": version("citry-core"),
        "html_bytes": len(html.encode()),
        "repeat_count": len(repeat_outputs),
        "residual_state_after_citry_clear": residual_state,
    },
    sort_keys=True,
)
