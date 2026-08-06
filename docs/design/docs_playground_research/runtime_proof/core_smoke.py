"""Direct citry_core smoke test for the matching Pyodide runtime."""

# Runtime assertions are the contract of this standalone Pyodide smoke script.
# ruff: noqa: S101

import json
import sys
from importlib.metadata import version

from citry_core.html_transform import mark_html
from citry_core.safe_eval import safe_eval
from citry_core.template_parser import compile_template, parse_template

source = "<section><h1>{{ title }}</h1></section>"
parsed = parse_template(source)
compiled = compile_template(parsed)
evaluated = safe_eval("value * 2")({"value": 21})
segments, placeholders = mark_html(
    "<main><p>Hello</p></main>",
    ["data-citry"],
    "c-render-id",
)

result = {
    "compiled_has_generate_template": "def generate_template" in compiled,
    "core_version": version("citry-core"),
    "marked": segments[0],
    "placeholders": placeholders,
    "safe_eval": evaluated,
    "python": sys.version,
    "used_variables": [token.content for token in parsed.used_variables],
}

assert result["used_variables"] == ["title"]
assert result["compiled_has_generate_template"] is True
assert result["safe_eval"] == 42
assert result["marked"] == '<main data-citry=""><p>Hello</p></main>'
assert result["placeholders"] == []

json.dumps(result, sort_keys=True)
