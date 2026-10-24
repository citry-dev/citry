"""Exercise the installed citry-core public API outside the repository."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import sysconfig
from importlib.metadata import version

from citry_core import _rust
from citry_core.html_transform import mark_html
from citry_core.i18n import CatalogCompiler, canonicalize_locale, locale_direction
from citry_core.safe_eval import safe_eval
from citry_core.template_formatter import format_template, prepare_embedded_format
from citry_core.template_parser import analyze_browser_source, compile_template, parse_template


def main() -> None:
    """Run one installed call through every public capability family."""
    expected_version = os.environ["CITRY_CORE_EXPECTED_VERSION"]
    installed_version = version("citry-core")
    if installed_version != expected_version:
        raise RuntimeError(f"expected citry-core {expected_version}, found {installed_version}")

    source = "<section><h1>{{ title }}</h1></section>"
    parsed = parse_template(source)
    compiled = compile_template(parsed)
    formatted = format_template("<main><p>Hello</p></main>")
    evaluated = safe_eval("value * 2")({"value": 21})
    browser_analysis = analyze_browser_source("known + local.value", "expression")
    embedded_plan = prepare_embedded_format(
        "<main><script>const  answer=41+1;</script><style>.card{color:red}</style></main>"
    )
    compile_request = {
        "schema_version": 1,
        "active_locales": ["en-US"],
        "fallbacks": {},
        "packages": [{"name": "app", "source_locale": "en-US", "exports": ["rich"]}],
        "catalogs": [
            {
                "path": "app/en-US.ftl",
                "package": "app",
                "layer": "app",
                "precedence": 0,
                "locale": "en-US",
                "source": "# @param {Slot} $link\nrich = Start { $link }, again { $link }.\n",
            }
        ],
    }
    catalog = CatalogCompiler().compile(json.dumps(compile_request))
    rich = json.loads(catalog.resolve_rich_json("en-US", "rich", "{}", '["link"]'))
    # The native render module ships in every wheel, including the ones
    # whose interpreter takes the Python path, so check it imports and that
    # its hashing gives Python's answer.
    native_ids = _rust.native_render._RunDigests('["site"', '["parent"').member_ids("key")
    native_placement = "citryPlacement" + hashlib.sha256(b'["site",["explicit","key"]]').hexdigest()[:24]
    native_child = "citryOccurrence" + hashlib.sha256(f'["parent","{native_placement}"]'.encode()).hexdigest()[:24]
    # Read one row through the C API (its float goes through CPython's own
    # formatter) and write it with the occurrence writer, as citry calls them.
    # Only the interpreters citry runs this code on do it: PyPy, Pyodide and
    # free-threaded builds take citry's Python path, so a row read there would
    # test code no user runs.
    reads_rows = (
        sys.implementation.name == "cpython"
        and sys.platform != "emscripten"
        and not sysconfig.get_config_var("Py_GIL_DISABLED")
    )
    native_row_json: str | None = None
    native_occurrences: str | None = None
    if reads_rows:
        native = _rust.native_render
        plan = native._RowPlan(
            (("text", "citryText0", ("p", "v", ())), ("open", "citryAttrs0", (("data-n", ("p", "n", ())),))),
            (("v", (("scalar",), (), None)), ("n", (("scalar",), (), None))),
            (),
            32,
            2**53 - 1,
        )
        native_row = plan.read({"v": 0.1, "n": 2**60}, frozenset({str, int, bool, float}))
        native_item: dict[str, object] = {
            "definitionId": "d",
            "id": "o",
            "parentId": None,
            "placementKey": None,
            "preparedData": {"calls": {}},
            "renderId": "r",
            "serverData": {},
            "typeKey": "t",
        }
        if native_row is None:
            raise RuntimeError("the native render module declined a plain row")
        native_row_json = native_row.prepared_json
        native_occurrences = native._encode_occurrences([native_item], {"o": native_row}, json.dumps)
    # The largest expressions the depth check accepts (97 chained additions,
    # 65 nested lists, 97 attribute lookups) must still be evaluated, parsed
    # and formatted here. On Pyodide the WebAssembly engine's own call stack
    # cannot grow, so this checks that the Rust passes fit in it; the
    # formatter's frames are the largest. One more level must give the clean
    # error instead of a crash.
    deepest_sum = safe_eval("1" + "+1" * 97)({})
    deepest_lists_parse = bool(parse_template("{{ " + "[" * 65 + "]" * 65 + " }}").elements)
    deepest_formats = all(
        "<p>" in format_template("<p>{{ " + expression + " }}</p>")
        for expression in ("[" * 65 + "]" * 65, "a" + ".b" * 97, "1" + "+1" * 97)
    )
    try:
        safe_eval("1" + "+1" * 98)
    except SyntaxError as error:
        too_deep_rejected = "expression is nested too deeply" in str(error)
    else:
        too_deep_rejected = False
    segments, placeholders = mark_html(
        "<main><p>Hello</p></main>",
        ["data-citry"],
        "c-render-id",
    )

    checks = {
        "compiled": "def generate_template" in compiled,
        "deepest_formats": deepest_formats,
        "deepest_lists_parse": deepest_lists_parse,
        "deepest_sum": deepest_sum,
        "embedded_languages": [request.language.value for request in embedded_plan.requests],
        "extension": _rust.__file__,
        "formatted": formatted,
        "locale": canonicalize_locale("en-us"),
        "marked": segments[0],
        "native_render_ids": native_ids == (native_placement, native_child),
        "native_render_row": native_row_json,
        "native_render_occurrences": native_occurrences,
        "placeholders": placeholders,
        "python": sys.version,
        "safe_eval": evaluated,
        "browser_references": [reference.name for reference in browser_analysis.references],
        "browser_source_valid": browser_analysis.valid,
        "rich_slot_count": sum(segment["type"] == "slot" for segment in rich["segments"]),
        "rich_has_private_marker": "__CITRY_SLOT_" in json.dumps(rich),
        "text_direction": locale_direction("ar"),
        "too_deep_rejected": too_deep_rejected,
        "used_variables": [token.content for token in parsed.used_variables],
        "version": installed_version,
    }
    expected = {
        "compiled": True,
        "deepest_formats": True,
        "deepest_lists_parse": True,
        "deepest_sum": 98,
        "embedded_languages": ["javascript", "css"],
        "locale": "en-US",
        "marked": '<main data-citry=""><p>Hello</p></main>',
        "native_render_ids": True,
        "placeholders": [],
        "safe_eval": 42,
        "browser_references": ["known", "local"],
        "browser_source_valid": True,
        "rich_slot_count": 2,
        "rich_has_private_marker": False,
        "text_direction": "rtl",
        "too_deep_rejected": True,
        "used_variables": ["title"],
    }
    if reads_rows:
        expected["native_render_row"] = (
            '{"calls":{},"citryAttrs0":{"data-n":"1152921504606846976"},"citryText0":"0.1"}'
        )
        expected["native_render_occurrences"] = (
            '[{"definitionId":"d","id":"o","parentId":null,"placementKey":null,'
            '"preparedData":{"calls":{},"citryAttrs0":{"data-n":"1152921504606846976"},"citryText0":"0.1"},'
            '"renderId":"r","serverData":{},"typeKey":"t"}]'
        )
    for name, value in expected.items():
        if checks[name] != value:
            raise RuntimeError(f"citry-core smoke check {name!r} returned {checks[name]!r}, expected {value!r}")
    if "<main>" not in checks["formatted"]:
        raise RuntimeError(f"template formatter returned unexpected output: {checks['formatted']!r}")

    sys.stdout.write(json.dumps(checks, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
