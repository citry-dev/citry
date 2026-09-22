"""Tests for JavaScript/CSS data delivery through native Vue and static CSS."""

import base64
import json
import re

import pytest

from citry import Citry, Component
from citry.ext.dependencies.scripts import (
    transform_component,
    uses_component,
)
from citry.util.css import is_css_func, serialize_css_var_value, validate_css_var_name

COMPONENT_JS = "$component({ onServerRender({ component }) { component.$el.textContent = component.rows; } });"


def _page(c, template="<html><head></head><body><c-widget /></body></html>"):
    return type("Page", (Component,), {"citry": c, "template": template})


def _manifest(html):
    """Extract and decode the page manifest JSON, or None when absent."""
    match = re.search(r'<script type="application/json" data-citry>(.*?)</script>', html, re.DOTALL)
    if match is None:
        return None
    return json.loads(match.group(1))


def _unb64(value):
    return base64.b64decode(value).decode()


def _decoded_calls(html):
    return [
        [_unb64(call[0]), _unb64(call[1]), None if call[2] is None else _unb64(call[2]), call[3]]
        for call in _manifest(html)["calls"]
    ]


def _prepared(html):
    match = re.search(r"CitryStable\.startPrepared\((\{.*\})\)\.catch", html, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))["manifest"]


class TestJsVars:
    def test_vars_script_registers_the_data(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

            def js_data(self, kwargs, slots):
                return {"rows": 3}

        manifest = _prepared(str(_page(c)()))
        occurrence = next(item for item in manifest["occurrences"] if item["typeKey"] == Widget.class_id)
        assert occurrence["serverData"] == {"rows": 3}

    @pytest.mark.parametrize("key", [1, True, None])
    def test_js_data_mapping_keys_must_be_exact_strings(self, key):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

            def js_data(self, kwargs, slots):
                return {key: "value"}

        with pytest.raises(TypeError, match=r"prepared Vue data object keys must be strings"):
            str(_page(c)())

    def test_records_carry_the_hashes(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS
            css = ".w { color: var(--row-color); }"

            def js_data(self, kwargs, slots):
                return {"rows": 3}

            def css_data(self, kwargs, slots):
                return {"row-color": "red"}

        rendered = _page(c)().render()
        record = next(r for r in rendered.context.extra["dependencies"] if r.class_id == Widget.class_id)
        assert record.js_vars_hash is None
        assert re.fullmatch(r"[0-9a-f]{32}", record.css_vars_hash)

    def test_identical_data_shares_one_script(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

            def js_data(self, kwargs, slots):
                return {"rows": 3}

        page = _page(c, template="<main><c-widget /><c-widget /></main>")
        manifest = _prepared(str(page()))
        assert sum(item["typeKey"] == Widget.class_id for item in manifest["occurrences"]) == 2

    def test_distinct_data_gets_distinct_scripts(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>{{ rows }}</span>"
            js = COMPONENT_JS

            class Kwargs:
                rows: int

            def template_data(self, kwargs, slots):
                return {"rows": kwargs.rows}

            def js_data(self, kwargs, slots):
                return {"rows": kwargs.rows}

        page = _page(c, template='<main><c-widget c-rows="1" /><c-widget c-rows="2" /></main>')
        rendered = page().render()
        records = [record for record in rendered.context.extra["dependencies"] if record.class_id == Widget.class_id]
        html = rendered.serialize()

        assert len(records) == 2
        values = [
            item["serverData"]["rows"] for item in _prepared(html)["occurrences"] if item["typeKey"] == Widget.class_id
        ]
        assert values == [1, 2]

    def test_data_round_trips_through_base64(self):
        c = Citry()
        payload = {
            "html": "</script><b>boom</b>",
            "lat": 40.7128,
            "lng": -74.006,
            "markers": [
                {"lat": 40.7128, "lng": -74.006, "title": "Marker 1"},
                {"lat": 40.758, "lng": -73.9855, "title": "Marker 2"},
            ],
        }

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

            def js_data(self, kwargs, slots):
                return payload

        html = str(_page(c)())
        assert "</script><b>boom</b>" not in html
        occurrence = next(item for item in _prepared(html)["occurrences"] if item["typeKey"] == Widget.class_id)
        assert occurrence["serverData"] == payload

    @pytest.mark.parametrize("asset_kind", ["js", "css"])
    def test_non_json_data_value_raises_naming_its_type(self, asset_kind):
        c = Citry()

        def data_method(self, kwargs, slots):
            return {"bad": object()}

        attrs = {
            "citry": c,
            "template": """
                <span>widget</span>
            """,
            asset_kind: (
                """
                    $component(() => {});
                """
                if asset_kind == "js"
                else """
                    .widget { color: teal; }
                """
            ),
            f"{asset_kind}_data": data_method,
        }
        type("Widget", (Component,), attrs)

        error_type = TypeError if asset_kind == "js" else ValueError
        error_match = (
            "prepared Vue data must be strict JSON, got object"
            if asset_kind == "js"
            else r"css_data\(\) entry 'bad'.*object is not supported"
        )
        with pytest.raises(error_type, match=error_match):
            str(_page(c)())

    @pytest.mark.parametrize("js_data", [{}, None], ids=["empty", "none"])
    def test_empty_js_data_emits_call_without_variables(self, js_data):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

            def js_data(self, kwargs, slots):
                return js_data

        rendered = _page(c)().render()
        html = rendered.serialize()
        occurrence = next(item for item in _prepared(html)["occurrences"] if item["typeKey"] == Widget.class_id)
        assert occurrence["serverData"] == {}

    def test_js_data_without_component_js_is_delivered_to_native_vue(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            css = ".w {}"  # has assets, so it is recorded; but no JS

            def js_data(self, kwargs, slots):
                return {"rows": 3}

        page = _page(c)
        rendered = page().render()
        occurrence = next(
            item for item in _prepared(rendered.serialize())["occurrences"] if item["typeKey"] == Widget.class_id
        )
        assert occurrence["serverData"] == {"rows": 3}

    def test_js_data_with_plain_js_is_delivered(self):
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log(1);"  # has JS, but no $component callback to hand data to
            css = ".w { color: var(--row-color); }"

            def js_data(self, kwargs, slots):
                return {"rows": 3}

            def css_data(self, kwargs, slots):
                return {"row-color": "red"}

        # Same js_data with a $component callback: its record carries the hash
        # a vars script for {"rows": 3} would be cached under.
        class Control(Component):
            citry = c
            template = "<span>c</span>"
            js = COMPONENT_JS

            def js_data(self, kwargs, slots):
                return {"rows": 3}

        page = _page(c, template="<html><head></head><body><c-widget /><c-control /></body></html>")
        rendered = page().render()
        html = rendered.serialize()
        data = {item["typeKey"]: item["serverData"] for item in _prepared(html)["occurrences"]}
        assert data[Widget.class_id] == {"rows": 3}
        assert data[Control.class_id] == {"rows": 3}
        from citry._vue.events import definition_bundle

        scripts = _prepared(html)["scripts"]
        assert any("console.log(1);" in definition_bundle(c, item["source"]["sha256"]).decode() for item in scripts)


class TestComponentTransform:
    def test_sugar_expands_to_register_component(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

        str(_page(c)())  # render, so the script is processed and cached
        # The cached (and thus emitted/served) form carries the expansion.
        from citry.ext.dependencies.scripts import get_component_script

        script = get_component_script("js", Widget)
        assert "$component" not in script.content
        assert f'CitryStable.registerTypeOptions.bind(null, "{Widget.class_id}", "' in script.content

    @pytest.mark.parametrize(
        "source",
        [
            "const value = '$component(() => {})';",
            'const value = "$component(() => {})";',
            "// $component(() => {})\nconst value = 1;",
            "/* $component(() => {}) */ const value = 1;",
            "const value = `$component(() => {})`;",
            "const value = /[$]component[(]/;",
            "if (ready) /[$]component[(]/.test(value);",
            "object.$component(() => {});",
            "const not$component = () => {}; not$component();",
            "function $component() {}",
            "function $component()\n{}",
            "function* $component() {}",
            "const object = { $component() {} };",
            "const object = { get $component() {} };",
            "const object = { async $component() {} };",
            "class Widget { $component() {} }",
            "class Widget { static $component() {} }",
            "class Widget { first() {} $component() {} }",
            "class Widget { value = 1\n$component() {} }",
            "class Widget { #$component() {} }",
            "class Outer { Inner = class { $component() {} } }",
            "class Outer { Inner = class Nested { $component() {} } }",
            "class Outer { Inner = new class { $component() {} } }",
            "class Outer { Kind = typeof class { $component() {} } }",
        ],
    )
    def test_non_code_and_other_identifiers_are_not_transformed(self, source):
        assert transform_component(source, "example") == source

    @pytest.mark.parametrize(
        "source",
        [
            "$component(() => {});",
            "$component \n (() => {});",
            "$component/* why */(() => {});",
            "const value = `${$component(() => {})}`;",
            "const value = total / $component(() => {});",
            "$component(handler)\n{\n  cleanup();\n}",
            "const result = $component(handler)\n{\n  cleanup();\n}",
            "const object = { class() {\n  $component(handler)\n  { cleanup(); }\n} };",
            "class Widget { class() {\n  $component(handler)\n  { cleanup(); }\n} }",
            "class Holder {\n  class\n  run() {\n    $component(handler)\n    { cleanup(); }\n  }\n}",
            "const naïve = true; $component /* λ */ ({ props: { 'display-name': String } });",
        ],
    )
    def test_actual_calls_are_transformed(self, source):
        result = transform_component(source, "example")

        assert "$component" not in result
        assert 'CitryStable.registerTypeOptions.bind(null, "example", "' in result

    def test_call_followed_by_block_activates_component_runtime(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "$component(handler)\n{\n  cleanup();\n}"

        assert uses_component(Widget) is True

    def test_call_inside_method_named_class_activates_runtime(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = """
                const object = { class() {
                  $component(handler)
                  { cleanup(); }
                } };
            """

        assert uses_component(Widget) is True

    @pytest.mark.parametrize(
        "source",
        [
            "const value = '$component(() => {})';",
            "// $component(() => {})",
            "const value = `$component(() => {})`;",
            "const value = /[$]component[(]/;",
            "function $component() {}",
            "const object = { $component() {} };",
            "class Widget { $component() {} }",
            "class Widget { value = 1\n$component() {} }",
            "class Widget { #$component() {} }",
        ],
    )
    def test_non_code_occurrences_do_not_activate_component_runtime(self, source):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = source

        assert uses_component(Widget) is False


class TestCssVars:
    def test_css_function_detection(self):
        for value in [
            "calc(100% - 20px)",
            "var(--color)",
            "url(image.png)",
            "rgba(255, 0, 0, 0.5)",
            "linear-gradient(to right, red, blue)",
            "rgb(255, 0, 0)",
            "hsla(120, 100%, 50%, 0.5)",
            "  calc(100%)",
        ]:
            assert is_css_func(value) is True

        for value in ["Hello World", "red", "#ff0000", "100px", ""]:
            assert is_css_func(value) is False

    @pytest.mark.parametrize("key", [1, True, None])
    def test_css_data_mapping_keys_must_be_exact_strings(self, key):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            css = ".w { color: var(--x); }"

            def css_data(self, kwargs, slots):
                return {key: "red"}

        with pytest.raises(TypeError, match=r"mapping keys must be exact strings; got .* key"):
            Widget().render()

    def test_stylesheet_and_root_marker_match(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            css = ".w { color: var(--row-color); }"

            def css_data(self, kwargs, slots):
                return {"row-color": "red"}

        html = str(_page(c)())
        marker = re.search(r"data-ccss-([0-9a-f]{32})", html)
        assert marker is not None
        vars_hash = marker.group(1)
        # The marker sits on the widget's root element...
        assert re.search(rf'<span[^>]*data-ccss-{vars_hash}=""', html)
        # ...and the generated stylesheet scopes the custom property to it.
        assert f"[data-ccss-{vars_hash}] {{\n  --row-color: red;\n}}" in html
        # The component's own CSS is emitted too.
        assert ".w { color: var(--row-color); }" in html

    def test_multiple_values_share_one_scoped_stylesheet(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = '<span class="w">w</span>'
            css = ".w { width: var(--width); content: var(--label); background: var(--gradient); }"

            def css_data(self, kwargs, slots):
                return {
                    "width": "100px",
                    "label": "Hello World",
                    "gradient": "linear-gradient(to right, red, blue)",
                    "color": "rgba(255, 0, 0, 0.5)",
                }

        html = str(_page(c)())
        marker = re.search(r"data-ccss-([0-9a-f]{32})", html)
        assert marker is not None
        vars_hash = marker.group(1)
        assert (
            f"[data-ccss-{vars_hash}] {{\n"
            '  --width: 100px;\n  --label: "Hello World";\n'
            "  --gradient: linear-gradient(to right, red, blue);\n"
            "  --color: rgba(255, 0, 0, 0.5);\n}"
        ) in html

    def test_identical_css_data_shares_hash_markers_and_stylesheet(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = """
                <span class="widget">widget</span>
            """
            css = """
                .widget { color: var(--accent); }
            """

            def css_data(self, kwargs, slots):
                return {"accent": "teal"}

        page = _page(
            c,
            template="""
                <main><c-widget /><c-widget /></main>
            """,
        )
        rendered = page().render()
        records = [record for record in rendered.context.extra["dependencies"] if record.class_id == Widget.class_id]
        hashes = [record.css_vars_hash for record in records]
        html = rendered.serialize()

        assert len(records) == 2
        assert hashes[0] is not None
        assert hashes == [hashes[0], hashes[0]]
        assert re.fullmatch(r"[0-9a-f]{32}", hashes[0])
        assert html.count(f'data-ccss-{hashes[0]}=""') == 2
        assert html.count(f"[data-ccss-{hashes[0]}] {{") == 1
        assert html.count(".widget { color: var(--accent); }") == 1

    @pytest.mark.parametrize("css_data", [{}, None], ids=["empty", "none"])
    def test_empty_css_data_emits_no_variables(self, css_data):
        c = Citry()

        class Widget(Component):
            citry = c
            template = '<span class="w">w</span>'
            css = ".w { color: red; }"

            def css_data(self, kwargs, slots):
                return css_data

        rendered = _page(c)().render()
        record = next(r for r in rendered.context.extra["dependencies"] if r.class_id == Widget.class_id)
        html = rendered.serialize()

        assert record.css_vars_hash is None
        assert "data-ccss-" not in html
        assert ".w { color: red; }" in html

    def test_distinct_css_data_gets_distinct_scoped_stylesheets(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = '<span class="w">w</span>'
            css = ".w { color: var(--row-color); }"

            class Kwargs:
                color: str

            def css_data(self, kwargs, slots):
                return {"row-color": kwargs.color}

        page = _page(
            c,
            template='<main><c-widget color="red" /><c-widget color="green" /></main>',
        )
        rendered = page().render()
        records = [r for r in rendered.context.extra["dependencies"] if r.class_id == Widget.class_id]
        hashes = [record.css_vars_hash for record in records]
        html = rendered.serialize()

        assert len(records) == 2
        assert all(hash_ is not None and re.fullmatch(r"[0-9a-f]{32}", hash_) for hash_ in hashes)
        assert hashes[0] != hashes[1]
        assert f'data-ccss-{hashes[0]}=""' in html
        assert f'data-ccss-{hashes[1]}=""' in html
        assert f"[data-ccss-{hashes[0]}] {{\n  --row-color: red;\n}}" in html
        assert f"[data-ccss-{hashes[1]}] {{\n  --row-color: green;\n}}" in html
        assert html.count(".w { color: var(--row-color); }") == 1

    def test_css_data_without_component_css_is_not_delivered(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log(1);"  # has assets, but no CSS

            def css_data(self, kwargs, slots):
                return {"row-color": "red"}

        html = str(_page(c)())
        assert "data-ccss-" not in html

    def test_serialize_css_var_value(self):
        assert serialize_css_var_value(None) == ""
        assert serialize_css_var_value(3) == "3"
        assert serialize_css_var_value(1.5) == "1.5"
        assert serialize_css_var_value("red") == "red"
        assert serialize_css_var_value("Helvetica Neue") == '"Helvetica Neue"'
        assert serialize_css_var_value('Helvetica "Neue"') == '"Helvetica \\"Neue\\""'
        assert serialize_css_var_value("first\nsecond") == '"first\\a second"'
        assert serialize_css_var_value("semi; colon") == '"semi; colon"'
        assert serialize_css_var_value("calc(100% - 20px)") == "calc(100% - 20px)"

    @pytest.mark.parametrize("value", ["\0", "contains \0 whitespace"])
    def test_css_value_rejects_null_before_any_string_quoting(self, value):
        with pytest.raises(ValueError, match="null character"):
            serialize_css_var_value(value)

    @pytest.mark.parametrize(
        "name",
        ["", "row color", "x; } body { color", "x:y", "x\\y", "x\0y", "\ud800"],
    )
    def test_invalid_custom_property_name_is_rejected(self, name):
        c = Citry()

        class Widget(Component):
            citry = c
            template = '<span class="w">w</span>'
            css = ".w { color: var(--safe); }"

            def css_data(self, kwargs, slots):
                return {name: "red"}

        with pytest.raises(ValueError, match=r"css_data\(\) entry .* cannot be emitted: CSS custom-property name"):
            str(_page(c)())

    @pytest.mark.parametrize("name", ["row-color", "123", "-accent", "café", "色"])
    def test_valid_custom_property_name_suffix(self, name):
        validate_css_var_name(name)

    def test_quoted_css_value_cannot_escape_the_generated_declaration(self):
        payload = 'red"; } body { outline: 99px solid red; } x { color: "blue'
        serialized = serialize_css_var_value(payload)

        assert serialized == '"red\\"; } body { outline: 99px solid red; } x { color: \\"blue"'

        c = Citry()

        class Widget(Component):
            citry = c
            template = '<span class="w">w</span>'
            css = ".w { color: var(--x); }"

            def css_data(self, kwargs, slots):
                return {"x": payload}

        html = str(_page(c)())
        assert f"  --x: {serialized};" in html
        assert "\nbody {" not in html

    @pytest.mark.parametrize(
        "value",
        [
            "red;}body{outline:red",
            "calc(1);}",
            "red}",
            "calc(100%",
            "red/*",
            '"unterminated',
            "red\\",
            "([)]",
            "\0",
            "\ud800",
        ],
    )
    def test_structurally_invalid_unquoted_css_value_is_rejected(self, value):
        with pytest.raises(ValueError, match="CSS value"):
            serialize_css_var_value(value)

    @pytest.mark.parametrize(
        "value",
        [
            "url(data:image/svg+xml;utf8,<svg></svg>)",
            'url("data:image/svg+xml;utf8,<svg></svg>")',
            "calc((100% - 20px) / 2)",
            "func(foo;bar)",
            "var(--fallback, rgb(1, 2, 3))",
            "token/**/value",
        ],
    )
    def test_structurally_complete_complex_css_value_is_allowed(self, value):
        assert serialize_css_var_value(value) == value

    @pytest.mark.parametrize("end_tag", ["</style>", "</StYlE>"])
    def test_style_end_tag_in_css_data_is_rejected(self, end_tag):
        c = Citry()

        class Widget(Component):
            citry = c
            template = '<span class="w">w</span>'
            css = ".w { content: var(--payload); }"

            def css_data(self, kwargs, slots):
                return {"payload": f"{end_tag}<script>boom()</script>"}

        with pytest.raises(ValueError, match="</style"):
            str(_page(c)())

    @pytest.mark.parametrize("value", [True, False, ["red"], {"color": "red"}])
    def test_non_scalar_css_data_value_is_rejected(self, value):
        with pytest.raises(TypeError, match="CSS data values must be strings, numbers, or None"):
            serialize_css_var_value(value)

    @pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_css_number_is_rejected(self, value):
        with pytest.raises(ValueError, match="CSS data numbers must be finite"):
            serialize_css_var_value(value)

    @pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_css_number_error_identifies_the_component_entry(self, value):
        c = Citry()

        class Widget(Component):
            citry = c
            template = '<span class="w">w</span>'
            css = ".w { color: var(--x); }"

            def css_data(self, kwargs, slots):
                return {"x": value}

        with pytest.raises(ValueError, match=r"Component .* css_data\(\) entry 'x'.*numbers must be finite"):
            Widget().render()

    def test_non_scalar_css_data_error_identifies_the_component_entry(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = '<span class="w">w</span>'
            css = ".w { color: var(--x); }"

            def css_data(self, kwargs, slots):
                return {"x": ["red"]}

        with pytest.raises(ValueError, match=r"css_data\(\) entry 'x'.*list is not supported"):
            str(_page(c)())


class TestManifestAndRuntime:
    def test_prepared_manifest_carries_component_occurrences(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

            def js_data(self, kwargs, slots):
                return {"rows": 3}

        rendered = _page(c, template="<main><c-widget /><c-widget /></main>")().render()
        occurrences = [
            item for item in _prepared(rendered.serialize())["occurrences"] if item["typeKey"] == Widget.class_id
        ]
        assert len(occurrences) == 2
        assert all(item["serverData"] == {"rows": 3} for item in occurrences)

    def test_native_manifest_carries_declared_url_dependencies(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

            class Dependencies:
                js = ["https://cdn.example.com/lib.js"]
                css = {"all": "/static/theme.css"}

        manifest = _prepared(str(_page(c)()))
        assert any(item["source"]["url"] == "https://cdn.example.com/lib.js" for item in manifest["scripts"])
        assert any(item["source"]["url"] == "/static/theme.css" for item in manifest["styles"])

    def test_runtime_inlined_once_when_callbacks_exist(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

        html = str(_page(c, template="<main><c-widget /><c-widget /></main>")())
        assert html.count("<script>/* Citry interactive runtime.") == 1
        assert (
            html.index("Citry Vue runtime")
            < html.index("registerTypeOptions")
            < html.rindex("CitryStable.startPrepared(")
        )

    def test_plain_component_javascript_uses_native_vue_runtime(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log(1);"  # plain JS, no $component

        html = str(_page(c)())
        assert "Citry Vue runtime" in html
        assert "startPrepared" in html


class TestSimpleStrategy:
    def test_simple_skips_the_js_runtime_but_keeps_css_vars(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS
            css = ".w { color: var(--row-color); }"

            def js_data(self, kwargs, slots):
                return {"rows": 3}

            def css_data(self, kwargs, slots):
                return {"row-color": "red"}

        html = _page(c)().render().serialize(deps_strategy="simple")
        # No manager, no manifest, no per-instance JS delivery.
        assert "dependency manager" not in html
        assert _manifest(html) is None
        assert "registerComponentData" not in html
        # The component's own JS is still emitted (it just has no manager to
        # register with; plain JS components work fine under "simple").
        assert "registerTypeOptions" in html
        # CSS variables are pure CSS and keep working.
        assert "data-ccss-" in html
        assert "--row-color: red;" in html
