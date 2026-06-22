"""Tests for JS/CSS variables delivery: vars scripts, ``data-ccss`` markers, the manifest, the runtime."""

import base64
import json
import re

from citry import Citry, Component
from citry.util.css import serialize_css_var_value

ON_COMPONENT_JS = "$onComponent(({ els, data }) => { els[0].textContent = data.rows; });"


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
            js = ON_COMPONENT_JS

            def js_data(self, kwargs, slots=None):
                return {"rows": 3}

        html = str(_page(c)())
        assert f'Citry.manager.registerComponentData("{Widget.class_id}"' in html
        encoded = re.search(r'JSON\.parse\(atob\("([^"]+)"\)\)', html)
        assert json.loads(_unb64(encoded.group(1))) == {"rows": 3}

    def test_records_carry_the_hashes(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = ON_COMPONENT_JS
            css = ".w { color: var(--row-color); }"

            def js_data(self, kwargs, slots=None):
                return {"rows": 3}

            def css_data(self, kwargs, slots=None):
                return {"row-color": "red"}

        rendered = _page(c)().render()
        record = next(r for r in rendered.context.extra["dependencies"] if r.class_id == Widget.class_id)
        assert re.fullmatch(r"[0-9a-f]{6}", record.js_vars_hash)
        assert re.fullmatch(r"[0-9a-f]{6}", record.css_vars_hash)

    def test_identical_data_shares_one_script(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = ON_COMPONENT_JS

            def js_data(self, kwargs, slots=None):
                return {"rows": 3}

        page = _page(c, template="<main><c-widget /><c-widget /></main>")
        html = str(page())
        assert html.count(f'registerComponentData("{Widget.class_id}"') == 1

    def test_distinct_data_gets_distinct_scripts(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>{{ rows }}</span>"
            js = ON_COMPONENT_JS

            class Kwargs:
                rows: int

            def template_data(self, kwargs, slots=None):
                return {"rows": kwargs.rows}

            def js_data(self, kwargs, slots=None):
                return {"rows": kwargs.rows}

        page = _page(c, template="<main><c-widget rows='1' /><c-widget rows='2' /></main>")
        html = str(page())
        assert html.count(f'registerComponentData("{Widget.class_id}"') == 2

    def test_data_round_trips_through_base64(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = ON_COMPONENT_JS

            def js_data(self, kwargs, slots=None):
                # A value that must not break out of the <script> tag.
                return {"html": "</script><b>boom</b>"}

        html = str(_page(c)())
        assert "</script><b>boom</b>" not in html
        encoded = re.search(r'JSON\.parse\(atob\("([^"]+)"\)\)', html)
        assert json.loads(_unb64(encoded.group(1))) == {"html": "</script><b>boom</b>"}

    def test_js_data_without_component_js_is_not_delivered(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            css = ".w {}"  # has assets, so it is recorded; but no JS

            def js_data(self, kwargs, slots=None):
                return {"rows": 3}

        page = _page(c)
        rendered = page().render()
        record = next(r for r in rendered.context.extra["dependencies"] if r.class_id == Widget.class_id)
        assert record.js_vars_hash is None
        assert f'registerComponentData("{Widget.class_id}"' not in rendered.serialize()


class TestOnComponentTransform:
    def test_sugar_expands_to_register_component(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = ON_COMPONENT_JS

        str(_page(c)())  # render, so the script is processed and cached
        # The cached (and thus emitted/served) form carries the expansion.
        from citry.extensions.dependencies.scripts import get_component_script

        script = get_component_script("js", Widget)
        assert "$onComponent" not in script.content
        assert f'Citry.manager.registerComponent("{Widget.class_id}", ' in script.content


class TestCssVars:
    def test_stylesheet_and_root_marker_match(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            css = ".w { color: var(--row-color); }"

            def css_data(self, kwargs, slots=None):
                return {"row-color": "red"}

        html = str(_page(c)())
        marker = re.search(r"data-ccss-([0-9a-f]{6})", html)
        assert marker is not None
        vars_hash = marker.group(1)
        # The marker sits on the widget's root element...
        assert re.search(rf'<span[^>]*data-ccss-{vars_hash}=""', html)
        # ...and the generated stylesheet scopes the custom property to it.
        assert f"[data-ccss-{vars_hash}] {{\n  --row-color: red;\n}}" in html
        # The component's own CSS is emitted too.
        assert ".w { color: var(--row-color); }" in html

    def test_css_data_without_component_css_is_not_delivered(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log(1);"  # has assets, but no CSS

            def css_data(self, kwargs, slots=None):
                return {"row-color": "red"}

        html = str(_page(c)())
        assert "data-ccss-" not in html

    def test_serialize_css_var_value(self):
        assert serialize_css_var_value(None) == ""
        assert serialize_css_var_value(3) == "3"
        assert serialize_css_var_value(1.5) == "1.5"
        assert serialize_css_var_value("red") == "red"
        assert serialize_css_var_value("Helvetica Neue") == '"Helvetica Neue"'
        assert serialize_css_var_value("calc(100% - 20px)") == "calc(100% - 20px)"


class TestManifestAndRuntime:
    def test_manifest_carries_the_component_calls(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = ON_COMPONENT_JS

            def js_data(self, kwargs, slots=None):
                return {"rows": 3}

        rendered = _page(c, template="<main><c-widget /><c-widget /></main>")().render()
        record_ids = [r.component_id for r in rendered.context.extra["dependencies"]]
        manifest = _manifest(rendered.serialize())
        assert manifest is not None
        calls = [[_unb64(part) if part is not None else None for part in call] for call in manifest["calls"]]
        assert [call[0] for call in calls] == [Widget.class_id, Widget.class_id]
        assert [call[1] for call in calls] == record_ids
        assert all(re.fullmatch(r"[0-9a-f]{6}", call[2]) for call in calls)

    def test_manifest_marks_url_dependencies_as_loaded(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = ON_COMPONENT_JS

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
            js = ON_COMPONENT_JS

        html = str(_page(c, template="<main><c-widget /><c-widget /></main>")())
        assert html.count("Citry's client-side dependency manager") == 1
        # The runtime precedes the component script that calls into it.
        assert html.index("client-side dependency manager") < html.index("registerComponent(")

    def test_no_callbacks_no_runtime_no_manifest(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log(1);"  # plain JS, no $onComponent

        html = str(_page(c)())
        assert "dependency manager" not in html
        assert _manifest(html) is None


class TestSimpleStrategy:
    def test_simple_skips_the_js_runtime_but_keeps_css_vars(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = ON_COMPONENT_JS
            css = ".w { color: var(--row-color); }"

            def js_data(self, kwargs, slots=None):
                return {"rows": 3}

            def css_data(self, kwargs, slots=None):
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
