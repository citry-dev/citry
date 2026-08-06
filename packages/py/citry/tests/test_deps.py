"""Tests for the built-in ``dependencies`` extension (the ``Dependencies`` class)."""

# ruff: noqa: ANN

import ast
import gc
import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from weakref import ref

import pytest

import citry.ext.dependencies
from citry import Citry, Component, Extension, Markup
from citry.ext.dependencies import CitryDependencies, DependenciesExtension, Script, get_dependencies


@pytest.fixture
def make_component_module(tmp_path, monkeypatch):
    """
    Write a component module (plus asset files) to disk and import it.

    Components defined in the generated module have a real ``.py`` file, so
    the relative-to-module-dir resolution tier applies to them. Returns the
    imported module. Modules are removed from ``sys.modules`` on teardown.
    Mirrors the fixture of the same name in test_assets.py.
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


class TestPublicSurface:
    """The public-API rule: `citry.ext.<name>` is a pure re-export surface."""

    def test_all_exposes_the_documented_surface(self):
        assert citry.ext.dependencies.__all__ == [
            "CitryDependencies",
            "DependenciesExtension",
            "Dependency",
            "DependencyRecord",
            "OnDependenciesContext",
            "Script",
            "Style",
            "get_dependencies",
        ]
        for name in citry.ext.dependencies.__all__:
            assert hasattr(citry.ext.dependencies, name), f"{name} is in __all__ but not importable"

    def test_init_has_no_def_or_class_statements(self):
        # The public __init__ carries imports and __all__ only, so the API
        # definition never shares a file with implementation (which lives in
        # the sibling modules, e.g. extension.py).
        source = Path(citry.ext.dependencies.__file__).read_text(encoding="utf-8")
        offenders = [
            node.name
            for node in ast.walk(ast.parse(source))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]
        assert offenders == []


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

    def test_bare_callable_js_and_css_resolve_lazily(self, tmp_path):
        (tmp_path / "lazy.js").write_text("")
        (tmp_path / "lazy.css").write_text("")
        c = Citry(dirs=[tmp_path])
        calls = {"js": 0, "css": 0}

        def js_entry():
            calls["js"] += 1
            return "lazy.js"

        def css_entry():
            calls["css"] += 1
            return "lazy.css"

        class Card(Component):
            citry = c

            class Dependencies:
                js = js_entry
                css = {"print": css_entry}

        class BareCssCard(Component):
            citry = c

            class Dependencies:
                css = css_entry

        assert calls == {"js": 0, "css": 0}
        assert Card.get_dependencies() == CitryDependencies(
            js=(tmp_path / "lazy.js",),
            css={"print": (tmp_path / "lazy.css",)},
        )
        assert calls == {"js": 1, "css": 1}
        assert BareCssCard.get_dependencies().css == {"all": (tmp_path / "lazy.css",)}
        assert calls == {"js": 1, "css": 2}

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

    def test_absolute_path_entries_are_inlined_as_local_files(self, tmp_path):
        css_path = tmp_path / "absolute.css"
        js_path = tmp_path / "absolute.js"
        css_path.write_text(".absolute-path { color: green; }")
        js_path.write_text("globalThis.absolutePath = true;")
        c = Citry()

        class Page(Component):
            citry = c
            template = """
                <html><head></head><body>page</body></html>
            """

            class Dependencies:
                css = [css_path]
                js = [lambda: js_path]

        html = str(Page())

        assert ".absolute-path { color: green; }" in html
        assert "globalThis.absolutePath = true;" in html
        assert f'href="{css_path.as_posix()}"' not in html
        assert f'src="{js_path.as_posix()}"' not in html

    def test_missing_path_entry_raises_instead_of_becoming_a_url(self, tmp_path):
        missing = tmp_path / "missing.css"
        c = Citry()

        class Card(Component):
            citry = c

            class Dependencies:
                css = [missing]

        with pytest.raises(FileNotFoundError, match=r"missing\.css"):
            Card.get_dependencies()

    def test_absolute_path_glob_expands_to_local_files(self, tmp_path):
        first = tmp_path / "a.css"
        second = tmp_path / "b.css"
        first.write_text(".a {}")
        second.write_text(".b {}")
        c = Citry()

        class Card(Component):
            citry = c

            class Dependencies:
                css = [tmp_path / "*.css"]

        assert Card.get_dependencies().css == {"all": (first, second)}

    def test_unmatched_string_glob_stays_an_unresolved_route(self):
        c = Citry()

        class Card(Component):
            citry = c

            class Dependencies:
                js = "missing/*.js"

        assert Card.get_dependencies().js == ("missing/*.js",)

    @pytest.mark.parametrize("absolute", [False, True], ids=["relative", "absolute"])
    def test_unmatched_path_glob_raises(self, tmp_path, absolute):
        pattern = tmp_path / "missing" / "*.js" if absolute else Path("missing/*.js")
        c = Citry(dirs=[tmp_path])

        class Card(Component):
            citry = c

            class Dependencies:
                js = pattern

        with pytest.raises(FileNotFoundError, match=r"missing/.+\.js"):
            Card.get_dependencies()

    def test_relative_path_glob_ignores_directory_only_matches(self, tmp_path):
        first_root = tmp_path / "first"
        second_root = tmp_path / "second"
        (first_root / "only-directory").mkdir(parents=True)
        second_root.mkdir()
        css_path = second_root / "only-file.css"
        css_path.write_text(".only-file {}")
        c = Citry(dirs=[first_root, second_root])

        class Card(Component):
            citry = c

            class Dependencies:
                css = [Path("only*")]

        assert Card.get_dependencies().css == {"all": (css_path,)}

    def test_url_forms_pass_through_glob_expansion(self):
        c = Citry()

        class Card(Component):
            citry = c

            class Dependencies:
                js = [
                    "http://example.com/style.min.js",
                    "://example.com/proto-relative.js",
                    "https://cdn.example.com/lib.*.min.js",
                    "/static/v*/w.js",
                ]

        # URL-shaped entries come back unchanged, glob characters and all;
        # they are never treated as filesystem patterns.
        assert Card.get_dependencies().js == (
            "http://example.com/style.min.js",
            "://example.com/proto-relative.js",
            "https://cdn.example.com/lib.*.min.js",
            "/static/v*/w.js",
        )

    def test_str_subclass_resolves_like_a_plain_string(self, tmp_path):
        (tmp_path / "style.css").write_text("")
        c = Citry(dirs=[tmp_path])

        class Text(str):
            __slots__ = ()

        class Card(Component):
            citry = c

            class Dependencies:
                css = [Text("style.css")]

        assert Card.get_dependencies().css == {"all": (tmp_path / "style.css",)}

    def test_prerendered_str_subclass_passes_through(self):
        c = Citry()
        tag = Markup('<link href="pre.css" rel="stylesheet">')

        class Card(Component):
            citry = c

            class Dependencies:
                css = [tag]

        # A str subclass with __html__ (e.g. Markup) is a pre-rendered
        # tag, not a path, and is kept as the very same object.
        deps = Card.get_dependencies()
        assert deps.css == {"all": (tag,)}
        assert deps.css["all"][0] is tag

    def test_pathlike_entry_resolves_like_its_string_form(self, tmp_path):
        (tmp_path / "style.css").write_text("")
        c = Citry(dirs=[tmp_path])

        class PathObj:
            def __fspath__(self):
                return "style.css"

        class ViaPathLike(Component):
            citry = c

            class Dependencies:
                css = PathObj()  # a single entry, not wrapped in a list

        class ViaString(Component):
            citry = c

            class Dependencies:
                css = "style.css"

        assert ViaPathLike.get_dependencies().css == {"all": (tmp_path / "style.css",)}
        assert ViaPathLike.get_dependencies() == ViaString.get_dependencies()

    def test_callable_entries_may_return_any_entry_form(self, tmp_path):
        (tmp_path / "a.js").write_text("")
        (tmp_path / "b.js").write_text("")
        c = Citry(dirs=[tmp_path])
        script = Script(url="https://cdn.example.com/lib.js")
        tag = Markup("<script>inline</script>")

        class Card(Component):
            citry = c

            class Dependencies:
                js = [
                    lambda: "a.js",
                    lambda: Path("b.js"),
                    lambda: "https://cdn.example.com/x.js",
                    lambda: tag,
                    lambda: script,
                ]

        # A callable's return value goes through the same type rules as a
        # direct entry: paths resolve to files, URLs stay strings, and
        # pre-rendered tags and Script/Style objects pass through unchanged.
        deps = Card.get_dependencies()
        assert deps.js == (
            tmp_path / "a.js",
            tmp_path / "b.js",
            "https://cdn.example.com/x.js",
            tag,
            script,
        )
        assert deps.js[4] is script

    @pytest.mark.parametrize("value", [b"a.js", ["a.js"]], ids=["bytes", "list"])
    def test_callable_returning_an_unsupported_type_raises(self, value):
        c = Citry()

        class Card(Component):
            citry = c

            class Dependencies:
                js = [lambda: value]

        with pytest.raises(TypeError, match=r"Unknown Dependencies entry .* on Card"):
            Card.get_dependencies()

    def test_entries_stay_untouched_until_first_resolve(self, tmp_path):
        (tmp_path / "lazy.js").write_text("")
        (tmp_path / "counted.css").write_text("")
        c = Citry(dirs=[tmp_path])
        calls = {"callable": 0, "fspath": 0, "html": 0, "str": 0}

        class CountingPath:
            def __fspath__(self):
                calls["fspath"] += 1
                return "counted.css"

            def __str__(self):
                calls["str"] += 1
                return "counted.css"

        class CountingTag:
            def __html__(self):
                calls["html"] += 1
                return "<script>tag</script>"

        def entry():
            calls["callable"] += 1
            return "lazy.js"

        tag = CountingTag()

        class Card(Component):
            citry = c

            class Dependencies:
                js = [entry, tag]
                css = [CountingPath()]

        # Declaring the class must not touch any entry (django-components
        # issue #522: users call URL helpers inside __html__/__str__, and
        # those must not run at import time).
        assert calls == {"callable": 0, "fspath": 0, "html": 0, "str": 0}

        deps = Card.get_dependencies()
        # The first resolve invokes callables and reads path objects; __html__
        # stays untouched (it runs only when the tag is emitted into a page).
        assert calls == {"callable": 1, "fspath": 1, "html": 0, "str": 0}
        assert deps.js == (tmp_path / "lazy.js", tag)
        assert deps.css == {"all": (tmp_path / "counted.css",)}

    @pytest.mark.parametrize(
        ("attr", "match"),
        [
            (
                "js",
                r"Dependencies\.js must be a path, a list of paths, or a callable; got <class 'int'> on BadCard",
            ),
            (
                "css",
                r"Dependencies\.css must be a path, a list, or a dict of media types; got <class 'int'> on BadCard",
            ),
        ],
    )
    def test_wrong_declaration_type_raises_naming_the_component(self, attr, match):
        c = Citry()
        card = type(
            "BadCard",
            (Component,),
            {"citry": c, "Dependencies": type("Dependencies", (), {attr: 123})},
        )

        with pytest.raises(ValueError, match=match):
            card.get_dependencies()

    def test_wrong_css_media_value_raises_naming_media_and_component(self):
        c = Citry()

        class BadCard(Component):
            citry = c

            class Dependencies:
                css = {"screen": 123}

        with pytest.raises(
            ValueError,
            match=r"Dependencies\.css\['screen'\].*got <class 'int'> on BadCard",
        ):
            BadCard.get_dependencies()

    @pytest.mark.parametrize(
        "declaration",
        [
            {"js": [b"path/script.js"]},
            {"css": {"screen": b"path/style.css"}},
            {"css": b"path/style.css"},
            {"js": bytearray(b"path/script.js")},
        ],
        ids=["list-entry", "dict-value", "bare-value", "bytearray"],
    )
    def test_bytes_entries_raise_naming_component_and_entry(self, declaration):
        # Every shape a bytes path can arrive in gets the same error naming
        # the component and the offending value (a bytes value in a dict must
        # not be expanded into meaningless integer bytes).
        c = Citry()
        card = type(
            "ByteCard",
            (Component,),
            {"citry": c, "Dependencies": type("Dependencies", (), dict(declaration))},
        )

        with pytest.raises(TypeError, match=r"Unknown Dependencies entry .*path.* on ByteCard"):
            card.get_dependencies()

    def test_declared_but_empty_dependencies_contribute_nothing(self):
        # An empty Dependencies class is legal and identical to no declaration.
        c = Citry()
        card = type(
            "EmptyDeps",
            (Component,),
            {"citry": c, "Dependencies": type("Dependencies", (), {})},
        )

        deps = card.get_dependencies()
        assert deps.js == ()
        assert deps.css == {}


class TestModuleRelativeEntries:
    """Entries declared in a component's own module resolve next to its ``.py`` file first."""

    def test_glob_searches_the_module_dir_before_citry_dirs(self, tmp_path, make_component_module):
        # The js pattern matches in BOTH the module dir and a Citry dir; the
        # module dir is searched first, and the first dir with any match wins
        # whole (no per-file union across dirs).
        citry_dir = tmp_path / "citry_dir"
        (citry_dir / "assets").mkdir(parents=True)
        (citry_dir / "assets" / "m1.js").write_text("")
        (citry_dir / "assets" / "citry-only.js").write_text("")
        (citry_dir / "fallthrough.css").write_text("")

        module = make_component_module(
            "glob_module_comp",
            "from citry import Citry, Component\n"
            f"c = Citry(dirs=[{str(citry_dir)!r}])\n"
            "class GlobCard(Component):\n"
            "    citry = c\n"
            "    class Dependencies:\n"
            "        js = 'assets/*.js'\n"
            "        css = 'fallthrough.*'\n",
            files={"assets/m1.js": "", "assets/m2.js": ""},
            module_dir="pkg_glob",
        )

        module_root = tmp_path / "pkg_glob"
        deps = module.GlobCard.get_dependencies()
        assert deps.js == (
            module_root / "assets" / "m1.js",
            module_root / "assets" / "m2.js",
        )
        # A pattern with no module-dir match falls through to the Citry dirs.
        assert deps.css == {"all": (citry_dir / "fallthrough.css",)}

    def test_module_less_component_glob_searches_citry_dirs(self, tmp_path):
        (tmp_path / "dynamic").mkdir()
        first = tmp_path / "dynamic" / "a.js"
        second = tmp_path / "dynamic" / "b.js"
        first.write_text("")
        second.write_text("")
        c = Citry(dirs=[tmp_path])
        dependencies = type("Dependencies", (), {"js": "dynamic/*.js"})
        card = type(
            "DynamicCard",
            (Component,),
            {"__module__": None, "citry": c, "Dependencies": dependencies},
        )

        assert card.get_dependencies().js == (first, second)

    def test_relative_entries_anchor_to_the_defining_module(self, tmp_path, make_component_module):
        # A decoy with the same relative name sits in the Citry dirs; the
        # entry declared in the module must resolve next to the module's .py
        # file, not against the Citry dirs or the rendering page's location.
        citry_dir = tmp_path / "citry_dir"
        citry_dir.mkdir()
        (citry_dir / "widget.js").write_text("globalThis.decoy = true;")

        module = make_component_module(
            "rel_widget_comp",
            "from citry import Citry, Component\n"
            f"c = Citry(dirs=[{str(citry_dir)!r}])\n"
            "class RelWidget(Component):\n"
            "    citry = c\n"
            '    template = """\n'
            "        <span>widget</span>\n"
            '    """\n'
            "    class Dependencies:\n"
            "        js = 'widget.js'\n",
            files={"widget.js": "globalThis.fromModule = true;"},
            module_dir="pkg_rel",
        )

        # The first resolution happens inside a nested render: the widget is
        # embedded in a page defined in THIS file (a different directory).
        class Page(Component):
            citry = module.c
            template = """
                <html><head></head><body><c-rel-widget /></body></html>
            """

        html = str(Page())
        assert "globalThis.fromModule = true;" in html
        assert "globalThis.decoy" not in html
        assert module.RelWidget.get_dependencies().js == (tmp_path / "pkg_rel" / "widget.js",)

    def test_plain_definition_entry_anchors_to_the_definition_module(self, tmp_path, make_component_module):
        citry_dir = tmp_path / "citry_dir"
        citry_dir.mkdir()
        (citry_dir / "library.js").write_text("globalThis.decoy = true;")

        module = make_component_module(
            "library_definition_comp",
            "from citry import Citry, Component\n"
            f"c = Citry(dirs=[{str(citry_dir)!r}])\n"
            "class LibraryDefinition:\n"
            "    class Dependencies:\n"
            "        js = 'library.js'\n"
            "class Bound(LibraryDefinition, Component):\n"
            "    citry = c\n",
            files={"library.js": "globalThis.fromDefinition = true;"},
            module_dir="pkg_definition",
        )

        assert module.Bound.get_dependencies().js == (tmp_path / "pkg_definition" / "library.js",)


class TestInheritanceAndMerge:
    def test_unhashable_prerendered_entries_dedupe_without_rendering_early(self):
        calls: list[str] = []

        @dataclass
        class Tag:
            content: str
            label: str = field(compare=False)

            def __html__(self):
                calls.append(self.label)
                return self.content

        c = Citry()
        first = Tag("<script>globalThis.firstSeen = true;</script>", "first")
        duplicate = Tag("<script>globalThis.firstSeen = true;</script>", "duplicate")

        class Parent(Component):
            citry = c
            template = """
                <p>parent</p>
            """

            class Dependencies:
                js = [first]

        class Child(Parent):
            citry = c

            class Dependencies:
                js = [duplicate]

        deps = Child.get_dependencies()
        assert deps.js == (first,)
        assert deps.js[0] is first
        assert calls == []

        html = str(Child())
        assert html.count("<script>globalThis.firstSeen = true;</script>") == 1
        assert calls == ["first"]

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

    def test_extend_false_on_a_parent_cuts_only_above_that_parent(self):
        c = Citry()

        class Grandparent(Component):
            citry = c

            class Dependencies:
                js = ["/static/grandparent.js"]

        class PlainParent(Component):
            citry = c

            class Dependencies:
                js = ["/static/plain-parent.js"]

        class CutParent(Grandparent):
            citry = c

            class Dependencies:
                extend = False
                js = ["/static/cut-parent.js"]

        class Child(PlainParent, CutParent):
            citry = c

            class Dependencies:
                js = ["/static/child.js"]

        # `extend = False` on CutParent stops inheritance from ITS ancestors
        # (the grandparent); CutParent's own entries still reach the child.
        assert Child.get_dependencies().js == (
            "/static/plain-parent.js",
            "/static/cut-parent.js",
            "/static/child.js",
        )

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

    def test_extend_list_on_a_parent_replaces_only_that_parents_bases(self):
        c = Citry()

        class Grandparent(Component):
            citry = c

            class Dependencies:
                js = ["/static/grandparent.js"]

        class Other(Component):
            citry = c

            class Dependencies:
                js = ["/static/other.js"]

        class Parent(Grandparent):
            citry = c

            class Dependencies:
                extend = [Other]
                js = ["/static/parent.js"]

        class Child(Parent):
            citry = c

            class Dependencies:
                js = ["/static/child.js"]

        # The parent's extend list swaps its real base (the grandparent) for
        # `Other`; the child still inherits from the parent normally.
        assert Child.get_dependencies().js == (
            "/static/other.js",
            "/static/parent.js",
            "/static/child.js",
        )

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

    def test_dependencies_none_on_a_middle_class_cuts_ancestors_above_it(self):
        c = Citry()

        class Grandparent(Component):
            citry = c

            class Dependencies:
                js = ["/static/grandparent.js"]

        class Parent(Grandparent):
            citry = c
            Dependencies = None

        class Child(Parent):
            citry = c

            class Dependencies:
                js = ["/static/child.js"]

        # The middle class's `None` stops inheritance for everything above
        # it; the child's own declaration still applies.
        assert Child.get_dependencies().js == ("/static/child.js",)

    def test_dependencies_none_on_one_base_drops_only_that_branch(self):
        c = Citry()

        class MutedGrandparent(Component):
            citry = c

            class Dependencies:
                js = ["/static/muted-grandparent.js"]

        class MutedBase(MutedGrandparent):
            citry = c
            Dependencies = None

        class KeptBase(Component):
            citry = c

            class Dependencies:
                js = ["/static/kept-base.js"]

        class Child(KeptBase, MutedBase):
            citry = c

            class Dependencies:
                js = ["/static/child.js"]

        # The muted branch contributes nothing, not even its own ancestors;
        # the other base and the child keep their relative order.
        assert Child.get_dependencies().js == ("/static/kept-base.js", "/static/child.js")

    def test_undeclared_child_inherits_without_duplication(self):
        c = Citry()

        class Parent(Component):
            citry = c

            class Dependencies:
                js = ["/static/parent.js"]

        class Child(Parent):
            citry = c

        assert Child.get_dependencies().js == ("/static/parent.js",)

    def test_grandparent_reaches_child_through_undeclared_middle(self):
        c = Citry()

        class Grandparent(Component):
            citry = c

            class Dependencies:
                js = ["/static/grandparent.js"]

        class Parent(Grandparent):
            citry = c

        class Child(Parent):
            citry = c

            class Dependencies:
                js = ["/static/child.js"]

        # The grandparent's entries appear once, before the child's.
        assert Child.get_dependencies().js == ("/static/grandparent.js", "/static/child.js")

    def test_undeclared_leaf_inherits_ancestors_farthest_first(self):
        c = Citry()

        class Grandparent(Component):
            citry = c

            class Dependencies:
                js = ["/static/grandparent.js"]

        class Parent(Grandparent):
            citry = c

            class Dependencies:
                js = ["/static/parent.js"]

        class Child(Parent):
            citry = c

        assert Child.get_dependencies().js == ("/static/grandparent.js", "/static/parent.js")

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

    def test_extend_list_merges_in_written_order(self):
        # extend = [A, B] contributes A's entries, then B's, then the class's
        # own, so a later listed class's stylesheet wins a cascade tie.
        c = Citry()

        class A(Component):
            citry = c

            class Dependencies:
                js = ["/static/a.js"]

        class B(Component):
            citry = c

            class Dependencies:
                js = ["/static/b.js"]

        class Card(Component):
            citry = c

            class Dependencies:
                extend = [A, B]
                js = ["/static/own.js"]

        assert Card.get_dependencies().js == ("/static/a.js", "/static/b.js", "/static/own.js")

    def test_plain_definition_assets_follow_the_same_branch_rules(self):
        # Reusable definition bases contribute their source declarations.
        # An explicit extend list still replaces the ordinary base branches.
        c = Citry()

        class Mixin:
            class Dependencies:
                js = ["/static/mixin.js"]

        class ListedPlain:
            class Dependencies:
                js = ["/static/listed.js"]

        class Card(Mixin, Component):
            citry = c

            class Dependencies:
                extend = [ListedPlain]
                js = ["/static/own.js"]

        assert Card.get_dependencies().js == ("/static/listed.js", "/static/own.js")

        class DefaultBranches(Mixin, Component):
            citry = c

        assert DefaultBranches.get_dependencies().js == ("/static/mixin.js",)

    @pytest.mark.parametrize("removal", ["unregister", "clear"])
    def test_closure_bearing_declaration_does_not_retain_removed_component(self, removal):
        app = Citry(autodiscover=False)

        def make_component():
            class RetainedTag:
                def __html__(self):
                    return RetainedCard.__name__

            class RetainedCard(Component):
                citry = app

                class Dependencies:
                    def js():
                        return RetainedTag()

            return RetainedCard

        retained_card = make_component()
        retained_ref = ref(retained_card)
        assert retained_card.get_dependencies().js
        if removal == "unregister":
            app.unregister(retained_card)
        else:
            app.clear()
        del retained_card
        gc.collect()

        assert retained_ref() is None


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
