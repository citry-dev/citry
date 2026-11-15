"""
Tests that the editor reads the data Citry writes for it from every Citry 1.x.

Citry writes the i18n index, the link verdicts, and the component catalog;
the app worker only passes them on. During 1.x Citry only adds keys to
them, so the readers must ignore a key they do not know, accept a missing
key that only turns a feature off, and still reject a known key with the
wrong type. Each test starts from what the real worker writes, then adds,
removes, or breaks one key.
"""

from __future__ import annotations

import copy
import json
from textwrap import dedent
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry
from citry_lsp import app_worker
from citry_lsp import project as project_module
from citry_lsp.catalog import CatalogIndex
from citry_lsp.project import I18nProjectIndex

if TYPE_CHECKING:
    from pathlib import Path

_I18N_APP = '''
from citry import Citry, Component
from citry.ext.i18n import FormatRegistry, NumberFormat

engine = Citry(
    autodiscover=False,
    extensions_defaults={
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US",),
            "formats": FormatRegistry(number={"measurement": NumberFormat()}),
        }
    },
)

class Page(Component):
    citry = engine
    template = '{{ tr("account-greeting", name="Ada") }}'
    messages = """
    # @param {str} $name - User name.
    account-greeting = Welcome, { $name }.
    account-wrapper = { account-greeting }
    """
'''


@pytest.fixture
def worker_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Return what the real app worker writes for an app with one translated component."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "readers_i18n_app.py").write_text(dedent(_I18N_APP), encoding="utf-8")
    return app_worker._run("readers_i18n_app:engine", tmp_path)


@pytest.fixture
def i18n_payload(worker_payload: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(worker_payload["extensions"]["i18n"])


def _index_facts(index: I18nProjectIndex) -> tuple[object, ...]:
    """Return everything the editor reads from an index, to compare two of them."""
    return (
        index.available,
        index.configured,
        index.revision,
        index.locales,
        index.outputs,
        index.references,
        index.profiles,
    )


def _with_extra_keys(payload: dict[str, Any]) -> dict[str, Any]:
    """Add a key a later Citry 1.x could write to every record of an i18n index."""
    newer = copy.deepcopy(payload)
    newer["later"] = 1
    newer["profiles"]["later"] = {"number": ["x"]}
    for output in newer["outputs"]:
        output["later"] = 1
        output["definition"]["later"] = 1
        for parameter in output["interface"].values():
            parameter["later"] = 1
            for declaration in parameter["declarations"]:
                declaration["later"] = 1
    for reference in newer["references"]:
        reference["later"] = 1
    return newer


def test_the_real_i18n_index_has_every_record_these_tests_change(i18n_payload):
    # The other tests only prove something when each record is present.
    assert i18n_payload["available"] is True
    assert i18n_payload["references"]
    greeting = next(output for output in i18n_payload["outputs"] if output["message"] == "account-greeting")
    assert greeting["interface"]["name"]["declarations"][0]["description"] == "User name."
    assert greeting["interface"]["name"]["declarations"][0]["annotated"] is True


def test_the_i18n_index_ignores_keys_a_newer_citry_adds(i18n_payload):
    newer = I18nProjectIndex(_with_extra_keys(i18n_payload))

    assert _index_facts(newer) == _index_facts(I18nProjectIndex(i18n_payload))
    # A profile namespace the editor does not know is not copied.
    assert set(newer.profiles) == {"format", "parse"}


def test_an_unavailable_i18n_index_ignores_keys_a_newer_citry_adds():
    index = I18nProjectIndex({"version": 1, "available": False, "configured": False, "later": 1})

    assert index.available is False
    assert index.outputs == {}


def test_the_i18n_index_reads_without_its_references(i18n_payload):
    del i18n_payload["references"]

    index = I18nProjectIndex(i18n_payload)

    assert index.references == ()
    assert index.message_ids() == ("account-greeting", "account-wrapper")


def test_a_parameter_declaration_reads_without_its_description_or_annotated_flag(i18n_payload):
    greeting = next(output for output in i18n_payload["outputs"] if output["message"] == "account-greeting")
    declaration = greeting["interface"]["name"]["declarations"][0]
    del declaration["description"]
    del declaration["annotated"]

    output = I18nProjectIndex(i18n_payload).output("account-greeting")

    assert output is not None
    [parameter] = output.parameters
    assert parameter.descriptions == ()
    assert parameter.declarations[0].description is None
    assert parameter.declarations[0].annotated is False


def _drop(path: tuple[object, ...]):
    def change(payload: dict[str, Any]) -> None:
        target: Any = payload
        for step in path[:-1]:
            target = target[step]
        del target[path[-1]]

    return change


def _set(path: tuple[object, ...], value: object):
    def change(payload: dict[str, Any]) -> None:
        target: Any = payload
        for step in path[:-1]:
            target = target[step]
        target[path[-1]] = value

    return change


_DECLARATION = ("outputs", 0, "interface", "name", "declarations", 0)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        # A key every Citry 1.x writes and the editor cannot do without.
        (_drop(("revision",)), "missing fields"),
        (_drop(("outputs",)), "missing fields"),
        (_drop(("profiles",)), "missing fields"),
        (_drop(("profiles", "parse")), "profile metadata is invalid"),
        (_drop(("outputs", 0, "interface")), "output metadata is invalid"),
        (_drop(("outputs", 0, "definition", "start")), "definition metadata is invalid"),
        (_drop(("references", 0, "token")), "reference metadata is invalid"),
        (_drop(("outputs", 0, "interface", "name", "direct")), "parameter metadata is missing fields"),
        (_drop((*_DECLARATION, "path")), "parameter declaration is invalid"),
        # A known key with the wrong type.
        (_set(("version",), 2), "version 2 is unsupported"),
        (_set(("references",), {}), "references must be a list"),
        (_set(("locales",), "en-US"), "locales are invalid"),
        (_set(("profiles", "format"), []), "format profile metadata is invalid"),
        (_set(("outputs", 0, "owner"), 7), "output identity is invalid"),
        (_set(("outputs", 0, "definition", "line"), "3"), "definition range is invalid"),
        (_set((*_DECLARATION, "annotated"), "yes"), "parameter declaration is invalid"),
        (_set((*_DECLARATION, "description"), 7), "parameter description is invalid"),
    ],
)
def test_the_i18n_index_still_rejects_wrong_data(i18n_payload, change, message):
    # Sort the outputs so index 0 is always the message with a parameter.
    i18n_payload["outputs"].sort(key=lambda output: output["token"])
    change(i18n_payload)

    with pytest.raises(ValueError, match=message):
        I18nProjectIndex(i18n_payload)


def test_the_editor_loads_an_app_whose_citry_writes_newer_i18n_data(tmp_path, worker_payload):
    worker_payload["extensions"]["i18n"] = _with_extra_keys(worker_payload["extensions"]["i18n"])
    worker_payload["paths"] = {"checked": True, "verdicts": {"/about": {"found": True, "later": 1}}, "later": 1}

    state = project_module._project_from_worker_output(
        tmp_path, "readers_i18n_app:engine", 0, json.dumps(worker_payload), ""
    )

    assert state.status.mode == "registry", state.status.message
    assert state.i18n is not None
    assert state.i18n.message_ids() == ("account-greeting", "account-wrapper")
    assert state.path_verdicts == {"/about": (True, None)}


def test_link_verdicts_ignore_keys_a_newer_citry_adds():
    verdicts = project_module._path_verdicts(
        {
            "checked": True,
            "verdicts": {"/abuot": {"found": False, "suggestion": "/about", "later": 1}},
            "later": 1,
        }
    )

    assert verdicts == {"/abuot": (False, "/about")}


def test_a_link_verdict_reads_without_its_suggestion():
    verdicts = project_module._path_verdicts({"checked": True, "verdicts": {"/abuot": {"found": False}}})

    assert verdicts == {"/abuot": (False, None)}


@pytest.mark.parametrize(
    "value",
    [
        {"verdicts": {}},
        {"checked": True},
        {"checked": "yes", "verdicts": {}},
        {"checked": True, "verdicts": []},
        {"checked": True, "verdicts": {"/about": {"suggestion": None}}},
        {"checked": True, "verdicts": {"/about": {"found": "yes", "suggestion": None}}},
        {"checked": True, "verdicts": {"/about": {"found": False, "suggestion": 7}}},
    ],
)
def test_link_verdicts_still_reject_wrong_data(value):
    with pytest.raises(ValueError, match="path verdict"):
        project_module._path_verdicts(value)


@pytest.fixture
def catalog_payload() -> dict[str, Any]:
    engine = Citry(autodiscover=False)
    return engine.inspect_components(include_builtins=True, resolve_assets=True).to_dict()


def test_the_component_catalog_ignores_keys_a_newer_citry_adds(catalog_payload):
    newer = copy.deepcopy(catalog_payload)
    newer["later"] = 1
    for component in newer["components"]:
        component["later"] = 1
        for schema in component["schemas"].values():
            schema["later"] = 1
            for field in schema["fields"]:
                field["later"] = 1
        for asset in component["assets"].values():
            asset["later"] = 1

    assert CatalogIndex(newer).components == CatalogIndex(catalog_payload).components


def test_a_catalog_component_reads_without_its_optional_description(catalog_payload):
    del catalog_payload["components"][0]["description"]

    assert CatalogIndex(catalog_payload).components[0].description is None


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (_drop(("components", 0, "builtin")), "builtin must be a bool"),
        (_set(("components", 0, "transparent"), "yes"), "transparent must be a bool"),
        (_set(("schema_version",), 2), "envelope is invalid"),
    ],
)
def test_the_component_catalog_still_rejects_wrong_data(catalog_payload, change, message):
    change(catalog_payload)

    with pytest.raises(ValueError, match=message):
        CatalogIndex(catalog_payload)
