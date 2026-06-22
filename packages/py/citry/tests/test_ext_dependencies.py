"""Tests for the built-in ``dependencies`` extension (the ``Dependencies`` class)."""

# ruff: noqa: ANN

import pytest

from citry import Citry, CitryDependencies, Component, Extension
from citry.extensions.dependencies import DependenciesExtension, get_dependencies


class TestBuiltinExtension:
    def test_every_citry_instance_has_the_builtin(self):
        c = Citry()
        extension = c.extensions.get_extension("dependencies")
        assert isinstance(extension, DependenciesExtension)

    def test_builtin_name_is_reserved(self):
        class Impostor(Extension):
            name = "dependencies"

        with pytest.raises(ValueError, match="dependencies"):
            Citry(extensions=[Impostor])

    def test_component_gets_dependencies_config_attached(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class Dependencies:
                js = ["/static/a.js"]

        captured = []

        class Probe(Extension):
            name = "probe"

            def on_component_data(self, ctx):
                captured.append(ctx.component.dependencies)

        c2 = Citry(extensions=[Probe])

        class Card2(Component):
            citry = c2
            template = "<p>x</p>"

        str(Card2())
        # The per-instance config (component.dependencies) is attached by the
        # extension manager, like any extension config.
        assert len(captured) == 1
        assert isinstance(captured[0], DependenciesExtension.Config)
        # And the rebuilt config class exists on the component class.
        assert issubclass(Card.Dependencies, DependenciesExtension.Config)


class TestShapes:
    def test_single_entries_normalize(self, tmp_path):
        (tmp_path / "a.js").write_text("")
        (tmp_path / "a.css").write_text("")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c

            class Dependencies:
                js = "a.js"
                css = "a.css"

        deps = Card.get_dependencies()
        assert isinstance(deps, CitryDependencies)
        assert deps.js == (tmp_path / "a.js",)
        assert deps.css == {"all": (tmp_path / "a.css",)}

    def test_css_dict_by_media_type(self, tmp_path):
        (tmp_path / "a.css").write_text("")
        (tmp_path / "p.css").write_text("")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c

            class Dependencies:
                css = {"all": ["a.css"], "print": "p.css"}

        deps = Card.get_dependencies()
        assert deps.css == {
            "all": (tmp_path / "a.css",),
            "print": (tmp_path / "p.css",),
        }

    def test_urls_and_unresolved_paths_pass_through(self):
        c = Citry()

        class Card(Component):
            citry = c

            class Dependencies:
                js = ["https://unpkg.com/x.js", "/static/y.js", "missing/z.js"]

        deps = Card.get_dependencies()
        assert deps.js == ("https://unpkg.com/x.js", "/static/y.js", "missing/z.js")

    def test_callable_entries_resolve_lazily(self, tmp_path):
        (tmp_path / "lazy.js").write_text("")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c

            class Dependencies:
                js = [lambda: "lazy.js"]

        assert Card.get_dependencies().js == (tmp_path / "lazy.js",)

    def test_glob_expansion_is_sorted(self, tmp_path):
        (tmp_path / "vendor").mkdir()
        (tmp_path / "vendor" / "b.js").write_text("")
        (tmp_path / "vendor" / "a.js").write_text("")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c

            class Dependencies:
                js = "vendor/*.js"

        assert Card.get_dependencies().js == (
            tmp_path / "vendor" / "a.js",
            tmp_path / "vendor" / "b.js",
        )

    def test_prerendered_tag_passes_through(self):
        c = Citry()

        class Tag:
            def __html__(self):
                return "<script>inline</script>"

        tag = Tag()

        class Card(Component):
            citry = c

            class Dependencies:
                js = [tag]

        assert Card.get_dependencies().js == (tag,)


class TestInheritanceAndMerge:
    def test_extend_true_inherits_bases_first(self):
        c = Citry()

        class Parent(Component):
            citry = c

            class Dependencies:
                js = ["/static/parent.js", "/static/shared.js"]

        class Child(Parent):
            citry = c

            class Dependencies:
                js = ["/static/child.js", "/static/shared.js"]

        deps = Child.get_dependencies()
        # Bases first, own entries last (the specialized class's CSS/JS comes
        # later in document order, so it wins cascade ties); duplicates keep
        # their first-seen position.
        assert deps.js == ("/static/parent.js", "/static/shared.js", "/static/child.js")

    def test_extend_false_does_not_inherit(self):
        c = Citry()

        class Parent(Component):
            citry = c

            class Dependencies:
                js = ["/static/parent.js"]

        class Child(Parent):
            citry = c

            class Dependencies:
                extend = False
                js = ["/static/child.js"]

        assert Child.get_dependencies().js == ("/static/child.js",)

    def test_extend_list_inherits_from_named_classes_only(self):
        c = Citry()

        class Parent(Component):
            citry = c

            class Dependencies:
                js = ["/static/parent.js"]

        class Other(Component):
            citry = c

            class Dependencies:
                js = ["/static/other.js"]

        class Child(Parent):
            citry = c

            class Dependencies:
                extend = [Other]
                js = ["/static/child.js"]

        # Named bases first, own entries last.
        assert Child.get_dependencies().js == ("/static/other.js", "/static/child.js")

    def test_dependencies_none_blocks_inheritance(self):
        c = Citry()

        class Parent(Component):
            citry = c

            class Dependencies:
                js = ["/static/parent.js"]

        class Child(Parent):
            citry = c
            Dependencies = None

        assert not Child.get_dependencies()

    def test_undeclared_child_inherits_without_duplication(self):
        c = Citry()

        class Parent(Component):
            citry = c

            class Dependencies:
                js = ["/static/parent.js"]

        class Child(Parent):
            citry = c

        assert Child.get_dependencies().js == ("/static/parent.js",)

    def test_css_merges_per_media_type_bases_first(self):
        c = Citry()

        class Parent(Component):
            citry = c

            class Dependencies:
                css = {"all": ["/static/base.css"], "print": ["/static/p.css"]}

        class Child(Parent):
            citry = c

            class Dependencies:
                css = ["/static/child.css"]

        deps = Child.get_dependencies()
        assert deps.css == {
            "all": ("/static/base.css", "/static/child.css"),
            "print": ("/static/p.css",),
        }

    def test_citry_dependencies_add_keeps_left_first(self):
        first = CitryDependencies(js=("a.js",), css={"all": ("x.css",)})
        second = CitryDependencies(js=("b.js", "a.js"), css={"all": ("y.css",), "print": ("p.css",)})
        merged = first + second
        assert merged.js == ("a.js", "b.js")
        assert merged.css == {"all": ("x.css", "y.css"), "print": ("p.css",)}


class TestResets:
    def test_reset_files_drops_the_merged_cache(self, tmp_path):
        (tmp_path / "one.js").write_text("")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c

            class Dependencies:
                js = "*.js"

        assert Card.get_dependencies().js == (tmp_path / "one.js",)
        # A new file appears; the cached merge does not see it until reset.
        (tmp_path / "two.js").write_text("")
        assert Card.get_dependencies().js == (tmp_path / "one.js",)
        Card.reset_files()
        assert Card.get_dependencies().js == (
            tmp_path / "one.js",
            tmp_path / "two.js",
        )

    def test_dependency_files_register_in_the_index(self, tmp_path):
        file_path = tmp_path / "dep.js"
        file_path.write_text("")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c

            class Dependencies:
                js = "dep.js"

        Card.get_dependencies()
        assert c.get_components_for_file(file_path) == [Card]


class TestModuleFunction:
    def test_get_dependencies_function_matches_classmethod(self):
        c = Citry()

        class Card(Component):
            citry = c

            class Dependencies:
                js = ["/static/a.js"]

        assert get_dependencies(Card) == Card.get_dependencies()
