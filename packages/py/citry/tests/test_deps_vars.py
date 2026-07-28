"""Tests for JS/CSS variables delivery: vars scripts, ``data-ccss`` markers, the manifest, the runtime."""

import base64
import json
import re

import pytest

from citry import Citry, Component
from citry.ext.dependencies.scripts import gen_cache_key
from citry.util.css import is_css_func, serialize_css_var_value, validate_css_var_name

COMPONENT_JS = "$component(({ els, data }) => { els[0].textContent = data.rows; });"


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


class TestJsVars:
    def test_vars_script_registers_the_data(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

            def js_data(self, kwargs, slots):
                return {"rows": 3}

        html = str(_page(c)())
        assert f'Citry.manager.registerComponentData("{Widget.class_id}"' in html
        encoded = re.search(r'JSON\.parse\(atob\("([^"]+)"\)\)', html)
        assert json.loads(_unb64(encoded.group(1))) == {"rows": 3}

    @pytest.mark.parametrize("key", [1, True, None])
    def test_js_data_mapping_keys_must_be_exact_strings(self, key):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

            def js_data(self, kwargs, slots):
                return {key: "value"}

        with pytest.raises(TypeError, match=r"mapping keys must be exact strings; got .* key"):
            Widget().render()

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
        assert re.fullmatch(r"[0-9a-f]{32}", record.js_vars_hash)
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
        html = str(page())
        assert html.count(f'registerComponentData("{Widget.class_id}"') == 1

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
        hashes = [record.js_vars_hash for record in records]
        html = rendered.serialize()

        assert len(records) == 2
        assert all(hash_ is not None and re.fullmatch(r"[0-9a-f]{32}", hash_) for hash_ in hashes)
        assert hashes[0] != hashes[1]

        registered = re.findall(
            rf'Citry\.manager\.registerComponentData\("{re.escape(Widget.class_id)}", "([^"]+)", '
            r'JSON\.parse\(atob\("([^"]+)"\)\)\);',
            html,
        )
        payloads_by_hash = {hash_: json.loads(_unb64(encoded)) for hash_, encoded in registered}
        assert payloads_by_hash == {hashes[0]: {"rows": 1}, hashes[1]: {"rows": 2}}

        calls = [[_unb64(part) if part is not None else None for part in call] for call in _manifest(html)["calls"]]
        assert calls == [
            [Widget.class_id, records[0].component_id, hashes[0]],
            [Widget.class_id, records[1].component_id, hashes[1]],
        ]

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
        encoded = re.search(r'JSON\.parse\(atob\("([^"]+)"\)\)', html)
        assert json.loads(_unb64(encoded.group(1))) == payload

    @pytest.mark.parametrize("asset_kind", ["js", "css"])
    def test_non_json_data_value_raises_naming_its_type(self, asset_kind):
        c = Citry()

        def data_method(_self, _kwargs, _slots):
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
            "Object of type object is not JSON serializable"
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
        record = next(r for r in rendered.context.extra["dependencies"] if r.class_id == Widget.class_id)
        html = rendered.serialize()
        calls = [[_unb64(part) if part is not None else None for part in call] for call in _manifest(html)["calls"]]

        assert record.js_vars_hash is None
        assert f'Citry.manager.registerComponentData("{Widget.class_id}"' not in html
        assert calls == [[Widget.class_id, record.component_id, None]]

    def test_js_data_without_component_js_is_not_delivered(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            css = ".w {}"  # has assets, so it is recorded; but no JS

            def js_data(self, kwargs, slots):
                return {"rows": 3}

        page = _page(c)
        rendered = page().render()
        record = next(r for r in rendered.context.extra["dependencies"] if r.class_id == Widget.class_id)
        assert record.js_vars_hash is None
        assert f'registerComponentData("{Widget.class_id}"' not in rendered.serialize()

    def test_js_data_with_plain_js_is_not_delivered(self):
        c = Citry()

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
        records = {r.class_id: r for r in rendered.context.extra["dependencies"]}
        html = rendered.serialize()
        vars_hash = records[Control.class_id].js_vars_hash

        # No callback could receive the data, so no vars script is cached or emitted...
        assert records[Widget.class_id].js_vars_hash is None
        assert not c.cache.has(gen_cache_key(Widget.class_id, "js", vars_hash))
        assert f'registerComponentData("{Widget.class_id}"' not in html
        # ...while the control with the same data gets both.
        assert c.cache.has(gen_cache_key(Control.class_id, "js", vars_hash))
        assert f'registerComponentData("{Control.class_id}"' in html
        # The plain JS itself still ships, and the css side is unaffected.
        assert "console.log(1);" in html
        css_vars_hash = records[Widget.class_id].css_vars_hash
        assert c.cache.has(gen_cache_key(Widget.class_id, "css", css_vars_hash))
        assert f"[data-ccss-{css_vars_hash}] {{\n  --row-color: red;\n}}" in html


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
        assert f'Citry.manager.registerComponent("{Widget.class_id}", ' in script.content


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
    def test_manifest_carries_the_component_calls(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

            def js_data(self, kwargs, slots):
                return {"rows": 3}

        rendered = _page(c, template="<main><c-widget /><c-widget /></main>")().render()
        record_ids = [r.component_id for r in rendered.context.extra["dependencies"]]
        manifest = _manifest(rendered.serialize())
        assert manifest is not None
        calls = [[_unb64(part) if part is not None else None for part in call] for call in manifest["calls"]]
        assert [call[0] for call in calls] == [Widget.class_id, Widget.class_id]
        assert [call[1] for call in calls] == record_ids
        assert all(re.fullmatch(r"[0-9a-f]{32}", call[2]) for call in calls)

    def test_manifest_marks_url_dependencies_as_loaded(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

            class Dependencies:
                js = ["https://cdn.example.com/lib.js"]
                css = {"all": "/static/theme.css"}

        manifest = _manifest(str(_page(c)()))
        assert [_unb64(url) for url in manifest["markLoaded"]["js"]] == ["https://cdn.example.com/lib.js"]
        assert [_unb64(url) for url in manifest["markLoaded"]["css"]] == ["/static/theme.css"]

    def test_runtime_inlined_once_when_callbacks_exist(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = COMPONENT_JS

        html = str(_page(c, template="<main><c-widget /><c-widget /></main>")())
        assert html.count("Citry's client-side dependency manager") == 1
        # The runtime precedes the component script that calls into it.
        assert html.index("client-side dependency manager") < html.index("registerComponent(")

    def test_no_callbacks_no_runtime_no_manifest(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log(1);"  # plain JS, no $component

        html = str(_page(c)())
        assert "dependency manager" not in html
        assert _manifest(html) is None


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
        assert "registerComponent(" in html
        # CSS variables are pure CSS and keep working.
        assert "data-ccss-" in html
        assert "--row-color: red;" in html
