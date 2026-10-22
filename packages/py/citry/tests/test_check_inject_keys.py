"""
Tests for ``citry.template.unknown-inject-key``, which ``citry check`` reports with the app loaded.

A component reads a shared value with ``self.inject("key")``. The rule walks
up from each template that renders the component and reports a key that no
``<c-provide>``, ``provide()`` call, or ``render(provides={...})`` key on
the way gives. When no template renders the component, it compares the key
with every key the app provides. The benchmark's m50 case (a card that reads
``bord`` under a page that provides ``board``) must be reported, and the
ways a key can legitimately arrive must stay silent.

Each test writes a small app module, because the rule reads the components'
Python source.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
import textwrap
import types
import typing
from typing import TYPE_CHECKING

import pytest

from citry._app_selection import CheckAppSelection
from citry._checker import check_project
from citry._provide_keys import _in_standard_library, engine_inject_keys, provides_argument_keys

if TYPE_CHECKING:
    from pathlib import Path

_CODE = "citry.template.unknown-inject-key"

_HEADER = """\
from citry import Citry, Component, LintSettings

engine = Citry(autodiscover=False{options})
"""

# The benchmark's card: it reads the board's name that the page provides.
_CARD_SOURCE = '''
class Card(Component):
    citry = engine

    def template_data(self, kwargs, slots):
        board = READ
        return {"name": board.name}

    template = """
      <p>{{ name }}</p>
    """
'''


def _card(key: str = "board", *, read: str | None = None) -> str:
    """Return the card's source, reading ``key`` with ``self.inject(key)`` or with the given ``read`` expression."""
    return _CARD_SOURCE.replace("READ", read if read is not None else f'self.inject("{key}")')


def _page(name: str, template: str, *, body: str = "") -> str:
    """Return the source of a component class with the given template and data method body."""
    method = f"\n    def template_data(self, kwargs, slots):\n{textwrap.indent(body, ' ' * 8)}\n        return {{}}\n"
    return f'''
class {name}(Component):
    citry = engine
{method if body else ""}
    template = """
{textwrap.indent(textwrap.dedent(template).strip(), " " * 6)}
    """
'''


_counter = [0]


def _findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *parts: str,
    options: str = "",
    files: dict[str, str] | None = None,
) -> list[tuple[str, str, str]]:
    """Load an app built from ``parts`` and return each finding's severity, covered source text, and message."""
    _counter[0] += 1
    name = f"inject_app_{_counter[0]}"
    source = _HEADER.format(options=options) + "".join(parts)
    app_file = tmp_path / f"{name}.py"
    app_file.write_text(source, encoding="utf-8")
    for relative, text in (files or {}).items():
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / relative).write_text(textwrap.dedent(text), encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, app_file)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # The rule reads each class's module from `sys.modules`, as for an imported app.
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    report = check_project(CheckAppSelection(spec=f"{name}:engine", engine=module.engine), tmp_path)
    encoded = source.encode()
    return [
        (
            finding.severity,
            encoded[finding.start_index : finding.end_index].decode(),
            finding.message,
        )
        for finding in report.findings
        if finding.code == _CODE
        and finding.start_index is not None
        and finding.end_index is not None
        and finding.origin.startswith(str(app_file))
        # The range counts in the Python file the origin names.
        and finding.source_kind == "file"
    ]


_BOARD_PROVIDES = """
<c-provide key="board" name="Projects">
  <c-card />
</c-provide>
"""


def test_the_benchmark_misspelled_key_is_reported_with_the_provided_key(tmp_path, monkeypatch):
    found = _findings(tmp_path, monkeypatch, _card("bord"), _page("Board", _BOARD_PROVIDES))

    assert found == [
        (
            "warning",
            '"bord"',
            "No component above Card provides 'bord', so self.inject('bord') raises KeyError when the page renders. "
            "Did you mean 'board'?",
        )
    ]


@pytest.mark.parametrize(
    "card",
    [
        pytest.param(_card("board"), id="provided-key"),
        pytest.param(_card(read='self.inject("bord", None)'), id="positional-default"),
        pytest.param(_card(read='self.inject("bord", default=None)'), id="keyword-default"),
        pytest.param(_card(read="self.inject(KEY)"), id="expression-key"),
        pytest.param(_card(read='[other := self, other.inject("bord")][1]'), id="other-receiver"),
    ],
)
def test_provided_keys_defaults_and_expression_keys_are_not_reported(tmp_path, monkeypatch, card):
    assert _findings(tmp_path, monkeypatch, "KEY = 'bord'\n", card, _page("Board", _BOARD_PROVIDES)) == []


def test_a_key_that_only_another_page_provides_is_reported(tmp_path, monkeypatch):
    # `Other` provides the key, but it never renders the card.
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("board"),
        _page("Board", "<main><c-card /></main>"),
        _page("Other", '<c-provide key="board" name="x"><p>no card</p></c-provide>'),
    )

    assert [message for _severity, _text, message in found] == [
        "No component above Card provides 'board', so self.inject('board') raises KeyError when the page"
        " renders. Provide 'board' above Card, or pass a default to inject()."
    ]


def test_a_component_rendered_on_two_paths_is_not_reported_when_one_provides_the_key(tmp_path, monkeypatch):
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("board"),
        _page("Board", _BOARD_PROVIDES),
        _page("Plain", "<main><c-card /></main>"),
    )

    assert found == []


@pytest.mark.parametrize(
    ("pages", "reported"),
    [
        pytest.param(
            [_page("Board", "<c-card />", body='self.provide("board", name="x")')],
            False,
            id="provide-in-the-writing-component",
        ),
        pytest.param(
            [
                _page("Column", "<c-card />"),
                _page("Board", "<c-column />", body='self.provide("board", name="x")'),
            ],
            False,
            id="provide-further-up",
        ),
        pytest.param(
            [
                _page("Column", "<c-card />"),
                _page("Board", '<c-provide key="board" name="x"><c-column /></c-provide>'),
            ],
            False,
            id="c-provide-further-up",
        ),
        pytest.param(
            [_page("Board", "<c-card />", body="self.provide(BOARD_KEY, name='x')")],
            False,
            id="module-constant-key",
        ),
        pytest.param(
            [_page("Column", "<c-card />"), _page("Board", "<c-column />")],
            True,
            id="nothing-on-the-way",
        ),
    ],
)
def test_keys_provided_in_python_and_further_up_count(tmp_path, monkeypatch, pages, reported):
    found = _findings(tmp_path, monkeypatch, "BOARD_KEY = 'board'\n", _card("board"), *pages)

    assert bool(found) is reported


_LAYOUT_SLOT = """
<div>
  <c-provide key="board" name="x">
    <c-slot name="body" />
  </c-provide>
  <c-slot />
</div>
"""


@pytest.mark.parametrize(
    ("page", "reported"),
    [
        pytest.param(
            '<c-layout><c-fill name="body"><c-card /></c-fill></c-layout>',
            False,
            id="fill-of-a-slot-inside-c-provide",
        ),
        pytest.param("<c-layout><c-card /></c-layout>", True, id="default-slot-outside-c-provide"),
        pytest.param(
            '<c-layout><c-fill name="body"><c-if cond="True"><c-card /></c-if></c-fill></c-layout>',
            False,
            id="nested-inside-the-fill",
        ),
        pytest.param(
            '<c-layout><c-if cond="True"><c-fill name="body"><c-card /></c-fill></c-if></c-layout>',
            False,
            id="fill-inside-c-if",
        ),
        pytest.param(
            '<c-layout><c-fill c-name="slot_name"><c-card /></c-fill></c-layout>',
            False,
            id="fill-name-written-as-an-expression",
        ),
    ],
)
def test_slot_content_sees_the_keys_around_the_slot_that_renders_it(tmp_path, monkeypatch, page, reported):
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("board"),
        _page("Layout", _LAYOUT_SLOT),
        _page("Board", page),
    )

    assert bool(found) is reported


def test_a_slot_passed_on_to_another_component_keeps_its_keys(tmp_path, monkeypatch):
    # Shell passes its own slot content into Layout's `body` slot, which Layout wraps in <c-provide>.
    shell = _page("Shell", '<c-layout><c-fill name="body"><c-slot /></c-fill></c-layout>')
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("board"),
        _page("Layout", _LAYOUT_SLOT),
        shell,
        _page("Board", "<c-shell><c-card /></c-shell>"),
    )

    assert found == []


_INNER = _page("Inner", '<c-provide key="board" name="x"><c-slot /></c-provide>')


@pytest.mark.parametrize(
    ("owner", "page"),
    [
        pytest.param("<c-inner><c-slot /></c-inner>", "<c-owner><c-card /></c-owner>", id="slot-in-the-body"),
        pytest.param(
            '<c-inner><c-if cond="True"><c-slot /></c-if></c-inner>',
            "<c-owner><c-card /></c-owner>",
            id="slot-under-c-if-in-the-body",
        ),
        pytest.param("<c-inner><c-slot><c-card /></c-slot></c-inner>", "<c-owner />", id="fallback-content"),
    ],
)
def test_a_slot_written_in_another_components_body_gets_that_components_keys(tmp_path, monkeypatch, owner, page):
    # Owner passes its slot content, or its fallback, into Inner's default slot, which Inner wraps in <c-provide>.
    found = _findings(tmp_path, monkeypatch, _card("board"), _INNER, _page("Owner", owner), _page("Board", page))

    assert found == []


def test_a_slot_owner_that_provides_in_python_counts(tmp_path, monkeypatch):
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("board"),
        _page("Layout", "<div><c-slot /></div>", body='self.provide("board", name="x")'),
        _page("Board", "<c-layout><c-card /></c-layout>"),
    )

    assert found == []


@pytest.mark.parametrize(
    "page",
    [
        pytest.param('<c-provide c-key="key_name" name="x"><c-card /></c-provide>', id="c-provide-c-key"),
        pytest.param('<c-component c-is="wrapper"><c-card /></c-component>', id="dynamic-slot-owner"),
        pytest.param('<c-layout c-body="<><c-card /></>" />', id="markup-in-a-component-attribute"),
    ],
)
def test_a_path_through_a_provider_citry_cannot_read_is_not_reported(tmp_path, monkeypatch, page):
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("bord"),
        _page("Layout", "<div>{{ body }}<c-slot /></div>"),
        _page("Board", page),
    )

    assert found == []


def test_a_provide_call_with_an_expression_key_counts_as_any_key_on_its_path(tmp_path, monkeypatch):
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("bord"),
        _page("Board", "<c-card />", body="self.provide(kwargs['key'], name='x')"),
    )

    assert found == []


def test_a_component_no_template_renders_is_compared_with_every_key_the_app_provides(tmp_path, monkeypatch):
    # Python renders Card, so any key the app provides anywhere counts.
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("bord"),
        _page("Other", '<c-provide key="board" name="x"><p>x</p></c-provide>'),
    )

    assert found == [
        (
            "warning",
            '"bord"',
            "Nothing in your app provides 'bord', so self.inject('bord') in Card raises KeyError when the page"
            " renders. Did you mean 'board'?",
        )
    ]
    assert (
        _findings(
            tmp_path,
            monkeypatch,
            _card("board"),
            _page("Other", '<c-provide key="board" name="x"><p>x</p></c-provide>'),
        )
        == []
    )


def test_a_component_only_a_dynamic_c_component_renders_uses_every_provided_key(tmp_path, monkeypatch):
    page = _page("Board", '<c-provide key="board" name="x"><c-component c-is="picked" /></c-provide>')

    assert _findings(tmp_path, monkeypatch, _card("board"), page) == []
    assert [text for _severity, text, _message in _findings(tmp_path, monkeypatch, _card("bord"), page)] == ['"bord"']


@pytest.mark.parametrize(
    ("views", "reported"),
    [
        pytest.param('Card().render(provides={"board": board})', False, id="dict-literal"),
        pytest.param("Card().render(provides=dict(board=board))", False, id="dict-call"),
        pytest.param("Card().render(provides={BOARD_KEY: board})", False, id="module-constant-key"),
        pytest.param("Card().render(provides=shared)", True, id="built-elsewhere"),
    ],
)
def test_render_provides_keys_in_project_files_count(tmp_path, monkeypatch, views, reported):
    # views.py is never imported: the rule reads the project's Python files as text.
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("board"),
        _page("Board", "<c-card />"),
        files={"views.py": f"BOARD_KEY = 'board'\n\n\ndef page(board, shared):\n    return {views}\n"},
    )

    assert bool(found) is reported


def test_render_provides_files_in_virtual_environments_are_skipped(tmp_path, monkeypatch):
    venv = tmp_path / "env"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("home = /usr\n", encoding="utf-8")
    (venv / "lib.py").write_text('render(provides={"board": 1})\n', encoding="utf-8")

    found = _findings(tmp_path, monkeypatch, _card("board"), _page("Board", "<c-card />"))

    assert len(found) == 1


def test_provides_argument_keys_reads_literal_keys_only():
    tree = ast.parse(
        'E = "e"\nf(provides={"a": 1, **rest, b: 2, E: 3}); g(provides=dict(c=1, **more)); h(other={"d": 1})'
    )

    assert sorted(provides_argument_keys(tree)) == ["a", "c", "e"]


def test_render_provides_keys_imported_from_a_loaded_module_count(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "board_keys", types.SimpleNamespace(BOARD="board"))
    views = (
        "import board_keys\nfrom board_keys import BOARD\n\n\n"
        "def page(board):\n    return Card().render(provides={BOARD: board})\n"
    )
    attribute = views.replace("{BOARD: board}", "{board_keys.BOARD: board}")

    # A keys module the app never imported is read from the project folder.
    on_disk = views.replace("board_keys", "disk_keys")

    for source in (views, attribute, on_disk):
        files = {"views.py": source, "disk_keys.py": "BOARD = 'board'\n"}
        found = _findings(tmp_path, monkeypatch, _card("board"), _page("Board", "<c-card />"), files=files)
        assert found == []


@pytest.mark.parametrize(
    "views",
    [
        pytest.param("from .keys import BOARD\n", id="relative-import"),
        pytest.param("from shop import keys\n", id="module-from-a-package"),
    ],
)
def test_render_provides_keys_imported_from_a_project_package_count(tmp_path, monkeypatch, views):
    use = "BOARD" if "BOARD" in views else "keys.BOARD"
    files = {
        "shop/__init__.py": "",
        "shop/keys.py": "BOARD = 'board'\n",
        "shop/views.py": f"{views}\n\ndef page(board):\n    return Card().render(provides={{{use}: board}})\n",
    }

    assert _findings(tmp_path, monkeypatch, _card("board"), _page("Board", "<c-card />"), files=files) == []


def test_a_project_inside_a_folder_named_tests_still_finds_placed_components(tmp_path, monkeypatch):
    # Only folders inside the project mark test files, not the folders around it.
    project = tmp_path / "tests" / "project"
    project.mkdir(parents=True)
    found = _findings(
        project,
        monkeypatch,
        _card("board"),
        _page("Layout", '<c-provide c-key="key_name" name="x"><c-slot /></c-provide>'),
        files={"views.py": "def page():\n    return str(Layout(slots={'default': Card()}))\n"},
    )

    assert found == []


def test_a_decorated_provide_call_without_source_still_counts(tmp_path, monkeypatch):
    # The mixin sits in an `if` block, so Citry reads its compiled methods, through the decorator.
    mixin = """
import functools

if True:
    def logged(method):
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            return method(*args, **kwargs)
        return wrapper

    class ProvidesBoard:
        @logged
        def template_data(self, kwargs, slots):
            self.provide("board", name="x")
            return {}
"""
    board = _page("Board", "<c-card />").replace("class Board(Component):", "class Board(ProvidesBoard, Component):")

    assert _findings(tmp_path, monkeypatch, mixin, _card("board"), board) == []


def test_a_project_package_named_like_a_standard_module_is_not_skipped(tmp_path, monkeypatch):
    # The class's file decides, so a project's own `profile` package is read.
    module = types.ModuleType("profile")
    module.__file__ = str(tmp_path / "profile" / "__init__.py")
    monkeypatch.setitem(sys.modules, "profile", module)
    project_class = type("Mixin", (), {"__module__": "profile"})

    assert not _in_standard_library(project_class)
    assert _in_standard_library(typing.Generic)


def test_a_project_folder_too_large_to_read_turns_the_rule_off(tmp_path, monkeypatch):
    # Past the limit Citry cannot see every `render(provides=...)` key.
    monkeypatch.setattr("citry._provide_keys._MAX_PROJECT_FILES", 0)

    assert _findings(tmp_path, monkeypatch, _card("bord"), _page("Board", _BOARD_PROVIDES)) == []


@pytest.mark.parametrize(
    ("parts", "files"),
    [
        pytest.param(
            (
                _page("Widget", "<c-card />"),
                _page("Board", '<c-provide key="board" name="x">{{ widget }}</c-provide>', body="widget = Widget()"),
            ),
            {},
            id="built-in-a-data-method",
        ),
        pytest.param(
            (_page("Widget", "<c-card />"), _page("Layout", '<c-provide key="board" name="x"><c-slot /></c-provide>')),
            {"views.py": "def page():\n    return str(Layout(slots={'default': Widget()}))\n"},
            id="passed-in-slots",
        ),
    ],
)
def test_a_component_python_places_inside_other_content_is_not_reported_below(tmp_path, monkeypatch, parts, files):
    # Widget renders under Board's or Layout's <c-provide>, which Citry cannot see from the templates.
    assert _findings(tmp_path, monkeypatch, _card("board"), *parts, files=files) == []


def test_a_component_python_places_through_a_variable_is_not_reported_below(tmp_path, monkeypatch):
    views = "def page():\n    widget = Widget()\n    return str(Layout(slots={'default': widget}))\n"
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("board"),
        _page("Widget", "<c-card />"),
        _page("Layout", '<c-provide key="board" name="x"><c-slot /></c-provide>'),
        files={"views.py": views},
    )

    assert found == []


def test_a_component_python_places_and_no_template_uses_is_not_reported(tmp_path, monkeypatch):
    # Card goes straight into Layout's slot, under a key Citry cannot read.
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("board"),
        _page("Layout", '<c-provide c-key="key_name" name="x"><c-slot /></c-provide>'),
        files={"views.py": "def page():\n    return str(Layout(slots={'default': Card()}))\n"},
    )

    assert found == []


def test_a_test_file_that_places_a_component_does_not_hide_it(tmp_path, monkeypatch):
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("bord"),
        _page("Board", _BOARD_PROVIDES),
        _page("Layout", "<c-slot />"),
        files={"tests/test_layout.py": "def test_it():\n    str(Layout(slots={'default': Card()}))\n"},
    )

    assert len(found) == 1


def test_a_page_python_renders_on_its_own_still_gets_its_children_checked(tmp_path, monkeypatch):
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("board"),
        _page("Board", "<c-card />"),
        files={"views.py": "def page():\n    return str(Board())\n"},
    )

    assert len(found) == 1


_TREE = '''
class Tree(Component):
    citry = engine

    def template_data(self, kwargs, slots):
        self.inject("board")
        return {"kids": []}

    template = """
      <ul><c-for each="kid in kids"><c-tree /></c-for></ul>
    """
'''


def test_a_component_written_only_in_its_own_template_uses_every_provided_key(tmp_path, monkeypatch):
    # Python renders the outermost tree, under whatever the page provides.
    layout = _page("Layout", '<c-provide key="board" name="x"><c-slot /></c-provide>')

    assert _findings(tmp_path, monkeypatch, _TREE, layout) == []
    assert len(_findings(tmp_path, monkeypatch, _TREE)) == 1


_MIXINS = '''
class ProvidesBoard:
    def template_data(self, kwargs, slots):
        self.provide("board", name="x")
        return {}


class ReadsBoard:
    def template_data(self, kwargs, slots):
        self.inject("bord")
        return {}


class Board(ProvidesBoard, Component):
    citry = engine
    template = """
      <c-card />
    """


class Tile(ReadsBoard, Component):
    citry = engine
    template = """
      <p>x</p>
    """
'''


def test_provide_and_inject_calls_in_mixins_count(tmp_path, monkeypatch):
    found = _findings(tmp_path, monkeypatch, _card("board"), _MIXINS, _page("Page", "<c-board /><c-tile />"))

    # Card gets `board` from the mixin's provide(); the mixin's inject("bord") is reported once, naming Tile.
    assert [message for _severity, _text, message in found] == [
        "No component above Tile provides 'bord', so self.inject('bord') raises KeyError when the page"
        " renders. Provide 'bord' above Tile, or pass a default to inject()."
    ]


def test_the_rule_follows_the_settings_and_the_component_lint_class(tmp_path, monkeypatch):
    parts = (_card("bord"), _page("Board", _BOARD_PROVIDES))
    ignore = ", lint=LintSettings(rule_unknown_inject_key='ignore')"
    error = ", lint=LintSettings(rule_unknown_inject_key='error')"

    assert _findings(tmp_path, monkeypatch, *parts, options=ignore) == []
    assert [item[0] for item in _findings(tmp_path, monkeypatch, *parts, options=error)] == ["error"]
    lint = "    class Lint:\n        rule_unknown_inject_key = 'ignore'\n"
    silenced = _card("bord").replace("    citry = engine\n", f"    citry = engine\n\n{lint}", 1)
    assert _findings(tmp_path, monkeypatch, silenced, _page("Board", _BOARD_PROVIDES)) == []


# Reader is registered too. The page renders it without the key, so only
# the subclasses can bring the key.
_BASE = '''
class Reader(Component):
    citry = engine

    def template_data(self, kwargs, slots):
        self.inject("board")
        return {}

    template = """
      <p>x</p>
    """


class Card(Reader):
    citry = engine


class Tile(Reader):
    citry = engine
'''


@pytest.mark.parametrize(
    ("page", "reported"),
    [
        pytest.param("<c-reader /><c-card /><c-tile />", True, id="no-subclass-gets-the-key"),
        pytest.param(
            '<c-reader /><c-card /><c-provide key="board" name="x"><c-tile /></c-provide>',
            False,
            id="one-subclass-gets-it",
        ),
    ],
)
def test_an_inject_call_on_a_base_class_is_reported_once_unless_a_subclass_gets_the_key(
    tmp_path, monkeypatch, page, reported
):
    found = _findings(tmp_path, monkeypatch, _BASE, _page("Board", page))

    assert len(found) == int(reported)
    if reported:
        assert "above Reader provides 'board'" in found[0][2]


def test_a_template_that_cannot_be_parsed_turns_the_rule_off(tmp_path, monkeypatch):
    # The broken template could render the card under any provider.
    found = _findings(
        tmp_path,
        monkeypatch,
        _card("bord"),
        _page("Board", _BOARD_PROVIDES),
        _page("Broken", "<c-if>"),
    )

    assert found == []


@pytest.mark.parametrize(
    ("hidden", "reported"),
    [
        pytest.param(
            'type("Hidden", (Component,), {"citry": engine, "template": "<p>x</p>"})\n', True, id="provides-nothing"
        ),
        pytest.param(
            'type("Hidden", (Component,), {"citry": engine, "template": "<p>x</p>",'
            ' "template_data": lambda self, kwargs, slots: self.provide(KEY) or {}})\n',
            False,
            id="calls-provide",
        ),
    ],
)
def test_a_component_without_source_counts_by_whether_its_code_calls_provide(tmp_path, monkeypatch, hidden, reported):
    # A class built with type() has no class statement, so Citry looks at its compiled methods instead.
    found = _findings(tmp_path, monkeypatch, "KEY = 'x'\n", _card("bord"), hidden)

    assert bool(found) is reported


def test_the_editor_record_carries_the_keys_and_component_ids(tmp_path, monkeypatch):
    _findings(tmp_path, monkeypatch, _card("bord"), _page("Board", _BOARD_PROVIDES))
    module = sys.modules[f"inject_app_{_counter[0]}"]
    module.engine.initialize()

    record = engine_inject_keys(module.engine, tmp_path)
    card = next(item for item in record["classes"] if item["qualname"] == "Card")  # type: ignore[union-attr]

    assert record["checked"] is True
    assert card["provided"] == ["board"]
    assert card["everywhere"] is False
    assert card["definition_ids"] == [module.Card.definition_id]
