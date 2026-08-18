"""Exercise the installed citry-core public API outside the repository."""

from __future__ import annotations

import json
import os
import sys
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
    valid_browser_source, browser_references = analyze_browser_source("known + local.value", "expression")
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
    segments, placeholders = mark_html(
        "<main><p>Hello</p></main>",
        ["data-citry"],
        "c-render-id",
    )

    checks = {
        "compiled": "def generate_template" in compiled,
        "embedded_languages": [request.language.value for request in embedded_plan.requests],
        "extension": _rust.__file__,
        "formatted": formatted,
        "locale": canonicalize_locale("en-us"),
        "marked": segments[0],
        "placeholders": placeholders,
        "python": sys.version,
        "safe_eval": evaluated,
        "browser_references": [name for name, _start, _end in browser_references],
        "browser_source_valid": valid_browser_source,
        "rich_slot_count": sum(segment["type"] == "slot" for segment in rich["segments"]),
        "rich_has_private_marker": "__CITRY_SLOT_" in json.dumps(rich),
        "text_direction": locale_direction("ar"),
        "used_variables": [token.content for token in parsed.used_variables],
        "version": installed_version,
    }
    expected = {
        "compiled": True,
        "embedded_languages": ["javascript", "css"],
        "locale": "en-US",
        "marked": '<main data-citry=""><p>Hello</p></main>',
        "placeholders": [],
        "safe_eval": 42,
        "browser_references": ["known", "local"],
        "browser_source_valid": True,
        "rich_slot_count": 2,
        "rich_has_private_marker": False,
        "text_direction": "rtl",
        "used_variables": ["title"],
    }
    for name, value in expected.items():
        if checks[name] != value:
            raise RuntimeError(f"citry-core smoke check {name!r} returned {checks[name]!r}, expected {value!r}")
    if "<main>" not in checks["formatted"]:
        raise RuntimeError(f"template formatter returned unexpected output: {checks['formatted']!r}")

    sys.stdout.write(json.dumps(checks, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
