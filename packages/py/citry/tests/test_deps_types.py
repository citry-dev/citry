"""Tests for the ``Script``/``Style`` dependency objects (``citry/ext/dependencies/types.py``)."""

from dataclasses import replace

import pytest

from citry import Citry, Component
from citry._javascript_policy import _JavascriptPolicy
from citry._serialization_security import _browser_loader_descriptor
from citry.ext.dependencies import Script, Style


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

    @pytest.mark.parametrize(
        ("script_type", "content", "wrapped"),
        [
            ("", "const x = 1;", True),
            ("application/javascript", "const x = 1;", True),
            ("importmap", '{"imports": {}}', False),
            ("speculationrules", '{"prefetch": []}', False),
            ("application/json", '{"data": true}', False),
        ],
    )
    def test_additional_script_type_wrap_rules(self, script_type, content, wrapped):
        html = Script(content=content, attrs={"type": script_type}).render()
        expected_content = f"(function() {{\n{content}\n}})();" if wrapped else content

        assert html == f'<script type="{script_type}">{expected_content}</script>'

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


class _HidingUrl(str):
    """A str subclass that answers every check as if it held a harmless URL."""

    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return hash("/safe.css")

    def __str__(self) -> str:
        return "/safe.css"

    def __html__(self) -> str:
        return "/safe.css"

    def startswith(self, *_args: object, **_kwargs: object) -> bool:
        return False

    def lower(self) -> str:
        return "/safe.css"


class TestUrlStrSubclass:
    """A ``str`` subclass URL is stored as its plain text, so every check reads that text."""

    @pytest.mark.parametrize("dependency_cls", [Script, Style])
    def test_django_safestring_url_serializes(self, dependency_cls):
        # django-compressor passes its output URL as a SafeString.
        safestring = pytest.importorskip("django.utils.safestring")
        dependency = dependency_cls(url=safestring.SafeString("/static/CACHE/out.js"))

        assert type(dependency.url) is str
        descriptor = _browser_loader_descriptor(dependency)
        assert descriptor["kind"] == "external"
        assert descriptor["url"] == "/static/CACHE/out.js"
        assert type(descriptor["url"]) is str

    def test_subclass_url_is_plain_after_replace_and_assignment(self):
        script = replace(Script(url="/a.js"), url=_HidingUrl("/b.js"))
        assert type(script.url) is str
        assert script.url == "/b.js"

        script.url = _HidingUrl("/c.js")
        assert type(script.url) is str
        assert script.url == "/c.js"

    def test_subclass_cannot_hide_a_javascript_url_from_the_policy(self):
        # Without the plain copy, __html__ would show the policy "/safe.css".
        policy = _JavascriptPolicy("forbid")
        style = Style(url=_HidingUrl("javascript:alert(1)"))

        assert policy.process_dependencies([style], position="test") == []
        with pytest.raises(ValueError, match="a javascript: URL"):
            policy.report()

    def test_subclass_url_renders_its_own_text(self):
        script = Script(url=_HidingUrl("/real.js"))
        assert script.render() == '<script src="/real.js"></script>'

    def test_url_mismatch_is_still_refused(self, monkeypatch):
        script = Script(url="/static/a.js")
        monkeypatch.setattr(Script, "_render", lambda _self: ("script", {"src": "/static/other.js"}, ""))

        with pytest.raises(ValueError, match="URL differs from its structured dependency URL"):
            _browser_loader_descriptor(script)

    def test_subclass_url_that_skips_the_plain_copy_is_still_refused(self):
        # object.__setattr__ skips Dependency.__setattr__; the exact-type
        # check at serialization still refuses the subclass that gets through.
        script = Script(url="/static/a.js")
        object.__setattr__(script, "url", _HidingUrl("/static/a.js"))

        with pytest.raises(ValueError, match="URL differs from its structured dependency URL"):
            _browser_loader_descriptor(script)
