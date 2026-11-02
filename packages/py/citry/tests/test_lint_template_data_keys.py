"""
``Lint.template_data_keys``: a component lists the keys its ``template_data()`` returns.

Only ``citry check`` and the editor read the list. It closes the template's
namespace when Citry cannot read the method, and the checker warns when the
method writes a literal key that the list leaves out.
"""

from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component
from citry._app_selection import CheckAppSelection
from citry._checker import check_project
from citry._diagnostic_catalog import TEMPLATE_UNDECLARED_TEMPLATE_DATA_KEY, TEMPLATE_UNKNOWN_VARIABLE
from citry._linting import TemplateLintInfo, _component_lint_info

if TYPE_CHECKING:
    from pathlib import Path


def _built(kwargs: object) -> dict[str, object]:
    """A helper whose result Citry cannot read from the method's source."""
    return {"title": str(kwargs), "subtitle": ""}


def _codes(engine: Citry, tmp_path: Path) -> list[tuple[str, str]]:
    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    return [(finding.code, finding.message) for finding in report.findings]


def test_the_list_closes_the_namespace_of_a_method_citry_cannot_read(tmp_path: Path) -> None:
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine

        class Lint:
            template_data_keys = ("title", "subtitle")

        def template_data(self, kwargs, slots):
            return _built(kwargs)

        template = """
          <h2>{{ title }}</h2>
          <p>{{ subtitel }}</p>
        """

    # `subtitel` is a typo the list rules out; `title` is listed.
    assert _codes(engine, tmp_path) == [
        (TEMPLATE_UNKNOWN_VARIABLE, "Template variable 'subtitel' is not available in this template."),
    ]


def test_without_the_list_the_same_template_is_only_unknown(tmp_path: Path) -> None:
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine

        def template_data(self, kwargs, slots):
            return _built(kwargs)

        template = """
          <h2>{{ title }}</h2>
        """

    # Citry cannot tell a typo from a helper's key, so it can only say so.
    [(code, message)] = _codes(engine, tmp_path)
    assert code == TEMPLATE_UNKNOWN_VARIABLE
    assert "could not determine" in message


_DRIFT_MODULE = """
from citry import Citry, Component

engine = Citry(autodiscover=False)


def _built(kwargs):
    return {"title": str(kwargs)}


class Card(Component):
    citry = engine

    class Lint:
        template_data_keys = ("title",)

    def template_data(self, kwargs, slots):
        data = _built(kwargs)
        data["badge"] = "new"
        return data

    template = "<h2>{{ title }}</h2>"
"""


def test_a_literal_key_the_list_leaves_out_is_a_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Citry reads the method from its file, so the component lives in one.
    module_file = tmp_path / "citry_tests_drift_card.py"
    # CR LF line endings on every platform, so a Windows checkout is not the
    # only place that exercises how the finding counts line breaks.
    module_file.write_text(_DRIFT_MODULE, encoding="utf-8", newline="\r\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, "citry_tests_drift_card", raising=False)
    module = importlib.import_module("citry_tests_drift_card")

    report = check_project(CheckAppSelection(spec="app:engine", engine=module.engine), tmp_path)

    [finding] = report.findings
    assert finding.code == TEMPLATE_UNDECLARED_TEMPLATE_DATA_KEY
    assert finding.severity == "warning"
    assert finding.message == (
        "template_data() returns 'badge', but Lint.template_data_keys does not list it. "
        "Add 'badge' to the list so it names every key the method returns."
    )
    assert finding.origin == f"{module_file} (citry_tests_drift_card.Card.template_data)"
    # The range points at the key in the component's Python file.
    assert finding.source_kind == "file"
    assert b"\r\n" in module_file.read_bytes()
    # The offsets count each line break as one "\n" byte, as Python reads a text
    # file, so slice the text as Python reads it, not the raw bytes on disk.
    text = module_file.read_text(encoding="utf-8")
    assert text.encode("utf-8")[finding.start_index : finding.end_index] == b'"badge"'
    # The module is ASCII, so the character index of the key is also its UTF-16 column.
    key_index = text.index('"badge"')
    assert finding.line == text.count("\n", 0, key_index)
    assert finding.column == key_index - (text.rfind("\n", 0, key_index) + 1)
    assert finding.end_line == finding.line
    assert finding.end_column == finding.column + len('"badge"')
    assert report.exit_code == 0
    sys.modules.pop("citry_tests_drift_card", None)


def test_a_subclass_list_replaces_the_base_list() -> None:
    engine = Citry(autodiscover=False)

    class Base(Component):
        citry = engine

        class Lint:
            template_data_keys = ["b", "a"]

    class Child(Base):
        class Lint:
            template_data_keys = frozenset({"c"})

    assert _component_lint_info(engine, Base).template_data_keys == ("a", "b")
    assert _component_lint_info(engine, Child).template_data_keys == ("c",)


@pytest.mark.parametrize(
    ("value", "error", "match"),
    [
        ("title", TypeError, "must be a tuple, list, or frozenset of strings"),
        ({"title": str}, TypeError, "must be a tuple, list, or frozenset of strings"),
        (("title", 3), TypeError, "must be a tuple, list, or frozenset of strings"),
        (("title", "not a name"), ValueError, "'not a name', which is not a template variable name"),
        (("class",), ValueError, "'class', which is not a template variable name"),
        (("title", "title"), ValueError, "names 'title' more than once"),
    ],
)
def test_an_invalid_list_fails_when_the_class_is_defined(value: object, error: type[Exception], match: str) -> None:
    with pytest.raises(error, match=match):

        class Card(Component):
            class Lint:
                template_data_keys = value


def test_a_template_data_schema_and_a_list_cannot_both_name_the_keys() -> None:
    with pytest.raises(TypeError, match=r"declares both a TemplateData schema and Lint\.template_data_keys"):

        class Card(Component):
            class TemplateData:
                title: str

            class Lint:
                template_data_keys = ("title",)


def test_a_subclass_with_a_template_data_schema_replaces_an_inherited_list() -> None:
    engine = Citry(autodiscover=False)

    class Base(Component):
        citry = engine

        class Lint:
            check_input_types = False
            template_data_keys = ("title",)

    # A library component lists its keys; an app's subclass may still
    # describe its data with a schema, which then names the keys.
    class Child(Base):
        class TemplateData:
            title: str

    assert _component_lint_info(engine, Base).template_data_keys == ("title",)
    assert _component_lint_info(engine, Child).template_data_keys is None


def test_none_clears_an_inherited_list() -> None:
    engine = Citry(autodiscover=False)

    class Base(Component):
        citry = engine

        class Lint:
            template_data_keys = ("title",)

    class Child(Base):
        class Lint:
            template_data_keys = None

    assert _component_lint_info(engine, Child).template_data_keys is None


def test_the_list_reaches_the_editor_through_the_lint_record() -> None:
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine

        class Lint:
            template_data_keys = ("title",)

    info = _component_lint_info(engine, Card)
    assert TemplateLintInfo.from_dict(info.to_dict()) == info
    # A record from a citry without the field still reads, as no list.
    record = info.to_dict()
    del record["template_data_keys"]
    assert TemplateLintInfo.from_dict(record).template_data_keys is None
