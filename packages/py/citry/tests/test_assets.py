"""Tests for primary asset loading: template/JS/CSS pairs, resolution, resets."""

# ruff: noqa: ANN

import gc
import importlib
import re
import sys
import threading
from pathlib import Path
from typing import cast
from weakref import ref

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

    def _make(
        module_name: str,
        py_source: str,
        files: dict[str, str] | None = None,
        *,
        module_dir: str | None = None,
    ):
        root = tmp_path / module_dir if module_dir is not None else tmp_path
        root.mkdir(parents=True, exist_ok=True)
        for relpath, content in (files or {}).items():
            file_path = root / relpath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        (root / f"{module_name}.py").write_text(py_source)
        monkeypatch.syspath_prepend(str(root))
        importlib.invalidate_caches()
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

            def template_data(self, kwargs, slots):
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

    def test_unrelated_classes_sharing_a_template_file_get_own_copies(self, tmp_path):
        # Two unrelated components naming the same file each resolve their
        # own template object (djc's cached-loader guarantee, without the
        # shared Django loader cache).
        (tmp_path / "shared.html").write_text("<p>{{ x }}</p>")
        c = Citry(dirs=[tmp_path])

        class One(Component):
            citry = c
            template_file = "shared.html"

        class Two(Component):
            citry = c
            template_file = "shared.html"

        t_one, t_two = One.get_template(), Two.get_template()
        assert t_one is not t_two
        assert t_one.source == t_two.source

    def test_unrelated_classes_with_identical_inline_source_get_own_copies(self):
        # The inline variant of the same guarantee: identical template strings
        # still produce one template object per class, each with its own origin.
        c = Citry()

        class Alpha(Component):
            citry = c
            template = "<p>{{ x }}</p>"

        class Beta(Component):
            citry = c
            template = "<p>{{ x }}</p>"

        t_alpha, t_beta = Alpha.get_template(), Beta.get_template()
        assert t_alpha is not t_beta
        assert t_alpha.source == t_beta.source
        assert t_alpha.origin.endswith("::Alpha")
        assert t_beta.origin.endswith("::Beta")

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

            def template_data(self, kwargs, slots):
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


class TestLazyLoading:
    def test_nothing_is_read_from_disk_at_class_definition_time(self, tmp_path):
        c = Citry(dirs=[tmp_path])

        # None of the declared files exist yet, so if class creation resolved
        # or read any of them, it would raise FileNotFoundError right here.
        class Card(Component):
            citry = c
            template_file = "later.html"
            js_file = "later.js"
            css_file = "later.css"

        (tmp_path / "later.html").write_text("<p>later</p>")
        (tmp_path / "later.js").write_text("console.log('later');")
        (tmp_path / "later.css").write_text(".later {}")

        # First access serves content that only appeared after the class was
        # created, so the disk reads can only have happened now.
        template = Card.get_template()
        assert template is not None
        assert template.source == "<p>later</p>"
        assert Card.get_js() == "console.log('later');"
        assert Card.get_css() == ".later {}"


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

    def test_one_member_none_is_allowed(self):
        # A set member plus an explicit None partner is legal (only two SET
        # members conflict); the set member is served.
        c = Citry()

        class Fine(Component):
            citry = c
            template = "<p>inline</p>"
            js = "console.log('inline');"
            js_file = None

        assert Fine.get_js() == "console.log('inline');"


# Values each level of a component chain declares when its mode is "declare".
_CHAIN_ASSETS = {
    "gp": {"template": "<p>gp</p>", "js": "console.log('gp')", "css": ".gp {}"},
    "p": {"template": "<p>p</p>", "js": "console.log('p')", "css": ".p {}"},
    "ch": {"template": "<p>ch</p>", "js": "console.log('ch')", "css": ".ch {}"},
}

# Inheritance matrix over a GrandParent -> Parent -> Child chain. Each level
# either declares its own template/js/css, nulls all three ("no asset"), or
# passes (mentions none of them). Expected: which level's values each of the
# three classes resolves to, top-down (None = asset-less). Ports the
# TestSubclassingAttributes matrix from django-components
# (`django-components/tests/test_component_media.py`).
_CHAIN_CASES = [
    pytest.param(("declare", "declare", "declare"), ("gp", "p", "ch"), id="every-level-declares"),
    pytest.param(("null", "declare", "pass"), (None, "p", "p"), id="redeclared-below-a-null"),
    pytest.param(("null", "null", "pass"), (None, None, None), id="null-all-the-way-down"),
    pytest.param(("declare", "pass", "pass"), ("gp", "gp", "gp"), id="inherited-two-levels-down"),
    pytest.param(("declare", "null", "pass"), ("gp", None, None), id="nulled-in-the-middle"),
    pytest.param(("declare", "pass", "declare"), ("gp", "gp", "ch"), id="overridden-at-the-leaf"),
    pytest.param(("null", "pass", "declare"), (None, None, "ch"), id="reintroduced-at-the-leaf"),
]


def _build_component_chain(citry, modes):
    """
    Build a GrandParent -> Parent -> Child component chain, one mode per level.

    ``declare`` sets the level's own inline template/js/css (from
    ``_CHAIN_ASSETS``), ``null`` sets all three to ``None``, and ``pass``
    leaves the pairs unmentioned so the level inherits.
    """
    levels = (("gp", "GrandParent"), ("p", "Parent"), ("ch", "Child"))
    chain: list[type[Component]] = []
    base: type[Component] = Component
    for (level_key, class_name), mode in zip(levels, modes, strict=True):
        attrs: dict[str, object] = {}
        if base is Component:
            # Only the chain root needs the Citry binding; subclasses inherit it.
            attrs["citry"] = citry
        if mode == "declare":
            attrs.update(_CHAIN_ASSETS[level_key])
        elif mode == "null":
            attrs.update(template=None, js=None, css=None)
        base = cast("type[Component]", type(class_name, (base,), attrs))
        chain.append(base)
    return chain


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

    def test_plain_mixin_uses_component_engine_search_dirs(self, tmp_path):
        (tmp_path / "mixin.html").write_text("<p>Mixin file</p>")
        c = Citry(dirs=[tmp_path])

        class AssetMixin:
            template_file = "mixin.html"

        class Card(AssetMixin, Component):
            citry = c

        template = Card.get_template()

        assert template is not None
        assert template.source == "<p>Mixin file</p>"

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

    def test_inherited_files_resolve_relative_to_declaring_module(self, make_component_module):
        make_component_module(
            "asset_owner_base",
            "from citry import Citry, Component\n"
            "c = Citry()\n"
            "class Base(Component):\n"
            "    citry = c\n"
            "    template_file = 'base.html'\n"
            "    js_file = 'base.js'\n"
            "    css_file = 'base.css'\n",
            files={
                "base.html": "<html><head></head><body>BASE TEMPLATE</body></html>",
                "base.js": "globalThis.baseAsset = true;",
                "base.css": ".base-asset { color: green; }",
            },
            module_dir="pkg_a",
        )
        child_module = make_component_module(
            "asset_owner_child",
            "from asset_owner_base import Base\nclass Child(Base):\n    pass\n",
            files={
                "base.html": "<html><head></head><body>CHILD DECOY</body></html>",
                "base.js": "globalThis.childDecoy = true;",
                "base.css": ".child-decoy { color: red; }",
            },
            module_dir="pkg_b",
        )

        html = str(child_module.Child())

        assert "BASE TEMPLATE" in html
        assert ".base-asset { color: green; }" in html
        assert "globalThis.baseAsset = true;" in html
        assert "CHILD DECOY" not in html
        assert "childDecoy" not in html
        assert ".child-decoy" not in html

    @pytest.mark.parametrize(("modes", "expected"), _CHAIN_CASES)
    def test_three_level_chain_resolves_each_pair_per_class(self, modes, expected):
        c = Citry()
        chain = _build_component_chain(c, modes)

        for cls, source_level in zip(chain, expected, strict=True):
            template = cls.get_template()
            if source_level is None:
                assert template is None
                assert cls.get_js() is None
                assert cls.get_css() is None
            else:
                assert template is not None
                assert template.source == _CHAIN_ASSETS[source_level]["template"]
                assert cls.get_js() == _CHAIN_ASSETS[source_level]["js"]
                assert cls.get_css() == _CHAIN_ASSETS[source_level]["css"]

    def test_pass_through_subclasses_get_their_own_template_objects(self):
        c = Citry()

        class GrandParent(Component):
            citry = c
            template = "<p>Shared</p>"

        class Parent(GrandParent):
            pass

        class Child(Parent):
            pass

        grandparent_template = GrandParent.get_template()
        parent_template = Parent.get_template()
        child_template = Child.get_template()
        assert grandparent_template is not None
        assert parent_template is not None
        assert child_template is not None

        # Each class resolves and caches its own template object; nothing is
        # shared by reference down the chain.
        assert parent_template.source == grandparent_template.source
        assert child_template.source == grandparent_template.source
        assert parent_template is not grandparent_template
        assert child_template is not grandparent_template
        assert child_template is not parent_template

        # The origin names the class the template was resolved for, so errors
        # point at the subclass the user actually rendered.
        assert grandparent_template.origin.endswith("::GrandParent")
        assert parent_template.origin.endswith("::Parent")
        assert child_template.origin.endswith("::Child")

        # Repeated access serves each class's own cached object.
        assert Parent.get_template() is parent_template
        assert Child.get_template() is child_template

    def test_explicit_none_on_the_file_member_also_erases(self):
        c = Citry()

        class Parent(Component):
            citry = c
            template = "<p>Parent</p>"

        class Child(Parent):
            template_file = None

        # The pair is one inheritance unit: nulling either member is a full
        # "no template" declaration, so the parent's inline value does not
        # leak through the other member.
        assert Child.get_template() is None
        parent_template = Parent.get_template()
        assert parent_template is not None
        assert parent_template.source == "<p>Parent</p>"


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

    def test_reload_cycles_do_not_stack_index_entries(self, tmp_path):
        # Every asset resolution re-registers the class for its file; the
        # index must dedupe, or each hot-reload cycle would add another
        # entry and invalidate_file would reset the same class repeatedly.
        file_path = tmp_path / "card.html"
        file_path.write_text("<p>x</p>")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            template_file = "card.html"

        class Extra(Component):
            citry = c
            template_file = "card.html"

        for _ in range(5):
            str(Card())
            str(Extra())
            Card.reset_template()
            Extra.reset_template()

        assert c.get_components_for_file(file_path) == [Card, Extra]
        assert c.invalidate_file(file_path) == [Card, Extra]

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
        css_path = tmp_path / "card.css"
        js_path.write_text("js-v1")
        css_path.write_text("css-v1")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            js_file = "card.js"
            css_file = "card.css"

        assert Card.get_js() == "js-v1"
        assert Card.get_css() == "css-v1"
        js_path.write_text("js-v2")
        css_path.write_text("css-v2")
        # Without a reset, the cached JS and CSS are served.
        assert Card.get_js() == "js-v1"
        assert Card.get_css() == "css-v1"
        # One reset drops both caches.
        Card.reset_files()
        assert Card.get_js() == "js-v2"
        assert Card.get_css() == "css-v2"

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

    def test_unregistered_class_is_pruned_from_the_index(self, tmp_path):
        file_path = tmp_path / "card.html"
        file_path.write_text("<p>x</p>")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            template_file = "card.html"

        str(Card())
        card_ref = ref(Card)
        assert c.get_components_for_file(file_path) == [Card]
        # The index holds only weak references, but defining the class above
        # auto-registered it and the registry keeps a strong reference, so a
        # bare `del` would not free it. Unregister first; the render cache must
        # not become another owner of the class.
        c.unregister(Card)
        del Card
        gc.collect()
        assert card_ref() is None
        assert c.get_components_for_file(file_path) == []

    def test_render_after_unregister_does_not_retain_the_class(self, tmp_path):
        file_path = tmp_path / "card.html"
        file_path.write_text("<p>x</p>")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c
            template_file = "card.html"

        element = Card()
        c.unregister(Card)
        assert ">x</p>" in str(element)
        card_ref = ref(Card)

        del element
        del Card
        gc.collect()

        assert card_ref() is None
        assert c.get_components_for_file(file_path) == []

    def test_reset_template_acts_only_on_the_called_class(self, tmp_path):
        file_path = tmp_path / "card.html"
        file_path.write_text("<p>v1</p>")
        c = Citry(dirs=[tmp_path])

        class Parent(Component):
            citry = c
            template_file = "card.html"

        class Child(Parent):
            pass

        assert "v1" in str(Parent())
        assert "v1" in str(Child())
        file_path.write_text("<p>v2</p>")
        Parent.reset_template()
        # The child caches its own copy, so the parent's reset does not reach it.
        assert "v2" in str(Parent())
        assert "v1" in str(Child())
        # The file index lists every class loaded from the file; resetting each
        # indexed class is the hot-reload route that refreshes them all.
        assert c.get_components_for_file(file_path) == [Parent, Child]
        for comp_cls in c.get_components_for_file(file_path):
            comp_cls.reset_template()
        assert "v2" in str(Child())

    def test_reset_files_acts_only_on_the_called_class(self, tmp_path):
        js_path = tmp_path / "card.js"
        js_path.write_text("v1")
        c = Citry(dirs=[tmp_path])

        class Parent(Component):
            citry = c
            js_file = "card.js"

        class Child(Parent):
            pass

        assert Parent.get_js() == "v1"
        assert Child.get_js() == "v1"
        js_path.write_text("v2")
        Parent.reset_files()
        assert Parent.get_js() == "v2"
        assert Child.get_js() == "v1"
        # JS/CSS files land in the same file index, so the subclass's own
        # cached copy is reachable the same way as templates.
        assert c.get_components_for_file(js_path) == [Parent, Child]
        Child.reset_files()
        assert Child.get_js() == "v2"


class TestConcurrentLoading:
    def test_concurrent_first_render_never_sees_a_half_resolved_template(self):
        c = Citry()

        class Racer(Component):
            citry = c
            template = "<p>Concurrent</p>"
            js = "console.log('conc')"

        thread_count = 8
        barrier = threading.Barrier(thread_count)
        results: list[str] = []
        errors: list[Exception] = []

        def render_once():
            # Any failure must surface in the main thread's assertions, so
            # catch everything the render could raise.
            try:
                barrier.wait(timeout=5)
                results.append(str(Racer()))
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=render_once) for _ in range(thread_count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        assert not any(thread.is_alive() for thread in threads)
        assert errors == []
        assert len(results) == thread_count
        # Only the per-render id may differ between the outputs; a partially
        # resolved template would show up as a wrong or truncated body in the
        # renders that raced the first one.
        normalized = {re.sub(r"data-cid-\w+", "data-cid-x", html) for html in results}
        assert len(normalized) == 1
        html = normalized.pop()
        assert "Concurrent" in html
        assert "console.log('conc')" in html
        # The race left the class with one fully compiled cached template.
        template = Racer.get_template()
        assert template is not None
        assert template.generate is not None


class TestDirsValidation:
    def test_relative_dir_raises(self):
        with pytest.raises(ValueError, match="absolute"):
            Citry(dirs=["relative/path"])

    def test_dirs_land_on_settings(self, tmp_path):
        c = Citry(dirs=[tmp_path])
        assert c.settings.dirs == (Path(tmp_path),)

    def test_str_dir_entries_convert_to_paths(self, tmp_path):
        # A plain string entry is accepted and stored as a Path.
        c = Citry(dirs=[str(tmp_path)])
        assert c.settings.dirs == (Path(tmp_path),)
