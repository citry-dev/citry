"""Tests for the ``Script``/``Style`` dependency objects (``citry/extensions/dependencies/types.py``)."""

import pytest

from citry import Citry, Component, Script, Style


class TestScript:
    def test_url_renders_script_src(self):
        script = Script(url="/static/a.js")
        assert script.render() == '<script src="/static/a.js"></script>'

    def test_inline_content_is_wrapped_by_default(self):
        script = Script(content="console.log('hi');")
        assert script.render() == "<script>(function() {\nconsole.log('hi');\n})();</script>"

    def test_wrap_false_keeps_content_as_is(self):
        script = Script(content="console.log('hi');", wrap=False)
        assert script.render() == "<script>console.log('hi');</script>"

    def test_module_type_is_never_wrapped(self):
        script = Script(content="import './x.js';", attrs={"type": "module"})
        assert script.render() == """<script type="module">import './x.js';</script>"""

    def test_js_mime_type_is_wrapped(self):
        script = Script(content="x();", attrs={"type": "text/javascript"})
        assert script.render() == '<script type="text/javascript">(function() {\nx();\n})();</script>'

    def test_extra_attrs_render(self):
        script = Script(url="/a.js", attrs={"defer": True})
        assert script.render() == '<script defer src="/a.js"></script>'

    def test_html_protocol_returns_the_rendered_tag(self):
        script = Script(url="/a.js")
        assert script.__html__() == script.render()

    def test_url_and_content_together_raise(self):
        with pytest.raises(ValueError, match="both"):
            Script(url="/a.js", content="x();").render()

    def test_neither_url_nor_content_raises(self):
        with pytest.raises(ValueError, match="either"):
            Script().render()

    def test_content_with_own_end_tag_raises(self):
        with pytest.raises(ValueError, match="</script"):
            Script(content="var s = '</script>';").render()

    def test_json_round_trip(self):
        script = Script(
            content="x();",
            attrs={"type": "module"},
            kind="component",
            origin_class_id="Card_a1b2c3",
            wrap=False,
        )
        assert Script.from_json(script.to_json()) == script
        assert Script.from_json(script.to_json()).wrap is False

    def test_render_json_shape(self):
        script = Script(url="/a.js", attrs={"defer": True})
        assert script.render_json() == {"tag": "script", "attrs": {"defer": True, "src": "/a.js"}, "content": ""}

    def test_equal_by_url(self):
        assert Script(url="/a.js") == Script(url="/a.js", attrs={"defer": True})
        assert Script(url="/a.js") != Script(url="/b.js")

    def test_equal_by_content_when_inline(self):
        assert Script(content="x();") == Script(content="x();")
        assert Script(content="x();") != Script(content="y();")

    def test_script_never_equals_style(self):
        assert Script(url="/a.css") != Style(url="/a.css")

    def test_dedupe_keeps_first_occurrence(self):
        first = Script(url="/a.js", attrs={"defer": True})
        items = [first, Script(url="/a.js"), Script(url="/b.js")]
        deduped = list(dict.fromkeys(items))
        assert deduped == [first, Script(url="/b.js")]
        assert deduped[0] is first


class TestStyle:
    def test_url_renders_link(self):
        style = Style(url="/static/p.css", attrs={"media": "print"})
        assert style.render() == '<link media="print" rel="stylesheet" href="/static/p.css"/>'

    def test_inline_content_renders_style_tag(self):
        style = Style(content=".card { color: red; }")
        assert style.render() == "<style>.card { color: red; }</style>"

    def test_content_with_own_end_tag_raises(self):
        with pytest.raises(ValueError, match="</style"):
            Style(content="/* </style> */").render()

    def test_json_round_trip(self):
        style = Style(url="/p.css", attrs={"media": "print"}, kind="extra", origin_class_id="Card_a1b2c3")
        assert Style.from_json(style.to_json()) == style

    def test_equal_by_url(self):
        assert Style(url="/a.css") == Style(url="/a.css", attrs={"media": "print"})
        assert Style(url="/a.css") != Style(url="/b.css")


class TestScriptStyleAsDependenciesEntries:
    def test_entries_pass_through_resolution_unchanged(self):
        c = Citry()
        cdn_script = Script(url="https://cdn.example.com/chart.js", attrs={"defer": True})
        print_style = Style(url="/static/print.css")

        class Chart(Component):
            citry = c
            template = "<p>x</p>"

            class Dependencies:
                js = [cdn_script]
                css = {"print": [print_style]}

        deps = Chart.get_dependencies()
        assert deps.js == (cdn_script,)
        assert deps.js[0] is cdn_script
        assert deps.css["print"] == (print_style,)
        assert deps.css["print"][0] is print_style
