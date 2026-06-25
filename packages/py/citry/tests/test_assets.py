"""Tests for primary asset loading: template/JS/CSS pairs, resolution, resets."""

# ruff: noqa: ANN

import importlib
import sys
from pathlib import Path

import pytest

from citry import Citry, CitryTemplate, Component, Extension


@pytest.fixture
def make_component_module(tmp_path, monkeypatch):
    """
    Write a component module (plus asset files) to disk and import it.

    Components defined in the generated module have a real ``.py`` file, so
    the relative-to-module-dir resolution tier applies to them. Returns the
    imported module. Modules are removed from ``sys.modules`` on teardown.
    """
    imported: list[str] = []

    def _make(module_name: str, py_source: str, files: dict[str, str] | None = None):
        for relpath, content in (files or {}).items():
            file_path = tmp_path / relpath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        (tmp_path / f"{module_name}.py").write_text(py_source)
        monkeypatch.syspath_prepend(str(tmp_path))
        module = importlib.import_module(module_name)
        imported.append(module_name)
        return module

    yield _make

    for module_name in imported:
        sys.modules.pop(module_name, None)


class TestTemplateFile:
    def test_template_file_relative_to_module(self, make_component_module):
        module = make_component_module(
            "comp_tpl_rel",
            "from citry import Citry, Component\n"
            "c = Citry()\n"
            "class Card(Component):\n"
            "    citry = c\n"
            "    template_file = 'card.html'\n",
            files={"card.html": "<p>From file</p>"},
        )
        template = module.Card.get_template()
        assert isinstance(template, CitryTemplate)
        assert template.source == "<p>From file</p>"
        assert template.filepath is not None
        assert template.origin == str(template.filepath)

    def test_template_file_via_citry_dirs(self, tmp_path):
        (tmp_path / "card.html").write_text("<p>Via dirs</p>")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            template_file = "card.html"

        template = Card.get_template()
        assert template is not None
        assert template.source == "<p>Via dirs</p>"

    def test_template_file_absolute_path(self, tmp_path):
        file_path = tmp_path / "abs.html"
        file_path.write_text("<p>Absolute</p>")
        c = Citry()

        class Card(Component):
            citry = c
            template_file = str(file_path)

        template = Card.get_template()
        assert template is not None
        assert template.source == "<p>Absolute</p>"
        assert template.filepath == file_path

    def test_template_file_renders_end_to_end(self, tmp_path):
        (tmp_path / "greet.html").write_text("<p>{{ name }}</p>")
        c = Citry(dirs=[tmp_path])

        class Greet(Component):
            citry = c
            template_file = "greet.html"

            def template_data(self, kwargs, slots=None):
                return {"name": kwargs["name"]}

        assert "World" in str(Greet(name="World"))

    def test_missing_file_raises_with_searched_locations(self, tmp_path):
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            template_file = "nope.html"

        with pytest.raises(FileNotFoundError, match=r"nope\.html"):
            Card.get_template()

    def test_inline_template_origin_names_class(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>Inline</p>"

        template = Card.get_template()
        assert template is not None
        assert template.filepath is None
        assert template.origin.endswith("::Card")

    def test_no_template_returns_none(self):
        c = Citry()

        class Card(Component):
            citry = c

        assert Card.get_template() is None

    def test_loaded_template_is_cached_per_class(self, tmp_path):
        file_path = tmp_path / "cached.html"
        file_path.write_text("<p>v1</p>")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            template_file = "cached.html"

        first = Card.get_template()
        file_path.write_text("<p>v2</p>")
        second = Card.get_template()
        assert second is first
        assert second.source == "<p>v1</p>"

    def test_compiled_form_fills_the_same_struct(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ x }}</p>"

            def template_data(self, kwargs, slots=None):
                return {"x": kwargs["x"]}

        template = Card.get_template()
        assert template is not None
        assert template.generate is None
        str(Card(x="hi"))
        # The render compiled the template into the same cached struct.
        assert Card.get_template() is template
        assert template.generate is not None
        assert "x" in template.used_vars

    def test_parse_error_names_the_origin(self, tmp_path):
        (tmp_path / "broken.html").write_text("<c-if>unclosed")
        c = Citry(dirs=[tmp_path])

        class Broken(Component):
            citry = c
            template_file = "broken.html"

        with pytest.raises(Exception, match=r"broken\.html"):
            str(Broken())


class TestJsCssFiles:
    def test_js_and_css_files_load(self, tmp_path):
        (tmp_path / "card.js").write_text("console.log('hi');")
        (tmp_path / "card.css").write_text(".card { color: red; }")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            js_file = "card.js"
            css_file = "card.css"

        assert Card.get_js() == "console.log('hi');"
        assert Card.get_css() == ".card { color: red; }"

    def test_inline_js_and_css(self):
        c = Citry()

        class Card(Component):
            citry = c
            js = "console.log(1)"
            css = ".a {}"

        assert Card.get_js() == "console.log(1)"
        assert Card.get_css() == ".a {}"

    def test_fields_stay_raw_declarations(self, tmp_path):
        (tmp_path / "x.js").write_text("var x;")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            js_file = "x.js"

        Card.get_js()
        # The class fields are never rewritten; the accessors hold the content.
        assert Card.js is None
        assert Card.js_file == "x.js"


class TestPairValidation:
    def test_both_template_members_raise_at_class_definition(self):
        c = Citry()
        with pytest.raises(ValueError, match="template"):

            class Bad(Component):
                citry = c
                template = "<p></p>"
                template_file = "x.html"

    def test_both_js_members_raise(self):
        c = Citry()
        with pytest.raises(ValueError, match="js"):

            class Bad(Component):
                citry = c
                js = "var x;"
                js_file = "x.js"

    def test_both_none_is_allowed(self):
        c = Citry()

        class Fine(Component):
            citry = c
            template = None
            template_file = None

        assert Fine.get_template() is None


class TestInheritance:
    def test_unset_pair_inherits_parent_template(self):
        c = Citry()

        class Parent(Component):
            citry = c
            template = "<p>Parent</p>"

        class Child(Parent):
            citry = c

        template = Child.get_template()
        assert template is not None
        assert template.source == "<p>Parent</p>"

    def test_child_file_shadows_parent_inline(self, tmp_path):
        (tmp_path / "child.html").write_text("<p>Child file</p>")
        c = Citry(dirs=[tmp_path])

        class Parent(Component):
            citry = c
            template = "<p>Parent inline</p>"

        class Child(Parent):
            citry = c
            template_file = "child.html"

        template = Child.get_template()
        assert template is not None
        assert template.source == "<p>Child file</p>"

    def test_explicit_none_makes_child_template_less(self):
        c = Citry()

        class Parent(Component):
            citry = c
            template = "<p>Parent</p>"

        class Child(Parent):
            citry = c
            template = None

        assert Child.get_template() is None


class TestLoadingHooks:
    def test_on_template_loaded_fires_for_file_template(self, tmp_path):
        (tmp_path / "card.html").write_text("<p>raw</p>")

        class Upper(Extension):
            name = "upper"

            def on_template_loaded(self, ctx):
                return ctx.content.replace("raw", "hooked")

        c = Citry(extensions=[Upper], dirs=[tmp_path])

        class Card(Component):
            citry = c
            template_file = "card.html"

        template = Card.get_template()
        assert template is not None
        assert template.source == "<p>hooked</p>"

    def test_on_js_and_css_loaded_fire(self):
        seen: list[tuple[str, str]] = []

        class Recorder(Extension):
            name = "recorder"

            def on_js_loaded(self, ctx):
                seen.append(("js", ctx.content))
                return ctx.content + ";/*js-hook*/"

            def on_css_loaded(self, ctx):
                seen.append(("css", ctx.content))
                return ctx.content + "/*css-hook*/"

        c = Citry(extensions=[Recorder])

        class Card(Component):
            citry = c
            js = "var x;"
            css = ".a {}"

        assert Card.get_js() == "var x;;/*js-hook*/"
        assert Card.get_css() == ".a {}/*css-hook*/"
        assert ("js", "var x;") in seen
        assert ("css", ".a {}") in seen


class TestFileIndexAndResets:
    def test_file_index_maps_file_to_classes(self, tmp_path):
        file_path = tmp_path / "card.html"
        file_path.write_text("<p>x</p>")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            template_file = "card.html"

        Card.get_template()
        assert c.get_components_for_file(file_path) == [Card]
        assert c.get_components_for_file(tmp_path / "other.html") == []

    def test_reset_template_rereads_file(self, tmp_path):
        file_path = tmp_path / "card.html"
        file_path.write_text("<p>v1</p>")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            template_file = "card.html"

        assert "v1" in str(Card())
        file_path.write_text("<p>v2</p>")
        # Without a reset, the cached template is served.
        assert "v1" in str(Card())
        Card.reset_template()
        assert "v2" in str(Card())

    def test_reset_files_rereads_js_and_css(self, tmp_path):
        js_path = tmp_path / "card.js"
        js_path.write_text("v1")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            js_file = "card.js"

        assert Card.get_js() == "v1"
        js_path.write_text("v2")
        assert Card.get_js() == "v1"
        Card.reset_files()
        assert Card.get_js() == "v2"

    def test_clear_empties_file_index(self, tmp_path):
        file_path = tmp_path / "card.html"
        file_path.write_text("<p>x</p>")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            template_file = "card.html"

        Card.get_template()
        c.clear()
        assert c.get_components_for_file(file_path) == []


class TestDirsValidation:
    def test_relative_dir_raises(self):
        with pytest.raises(ValueError, match="absolute"):
            Citry(dirs=["relative/path"])

    def test_dirs_land_on_settings(self, tmp_path):
        c = Citry(dirs=[tmp_path])
        assert c.settings.dirs == (Path(tmp_path),)
