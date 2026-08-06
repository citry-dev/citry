"""Run the citry-events/1 package checker through pytest and jsonschema."""

import importlib.util
import json
import shutil
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_VALIDATE_PY = _REPO_ROOT / "packages" / "protocol" / "events" / "v1" / "validate.py"


def _load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location("citry_events_protocol_validate", _VALIDATE_PY)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load_checker()
_load_problems: list[str] = []
CALL_SCHEMA = checker.load_json(checker.ROOT / "call.schema.json", _load_problems)
RESULT_SCHEMA = checker.load_json(checker.ROOT / "result.schema.json", _load_problems)
DESCRIPTOR_SCHEMA = checker.load_json(checker.ROOT / "descriptor.schema.json", _load_problems)
MANIFEST_SCHEMA = checker.load_json(checker.ROOT / "manifest.schema.json", _load_problems)
_INDEX = checker.load_json(checker.TESTS_DIR / "index.json", _load_problems)
_entry_problems: list[str] = []
ENTRIES = checker.check_index_entries(_INDEX, _entry_problems)


def test_schema_and_index_files_load():
    assert _load_problems == []


def test_exchange_index_is_complete_and_well_formed():
    problems = list(_entry_problems)
    checker.check_index_matches_disk(ENTRIES, problems)
    assert problems == []


def test_swap_and_action_vocabularies_agree_across_schemas():
    assert checker.check_vocabulary_consistency(CALL_SCHEMA, RESULT_SCHEMA) == []


@pytest.mark.parametrize("entry", ENTRIES, ids=[entry["call"].removesuffix(".call.json") for entry in ENTRIES])
def test_exchange(entry):
    problems: list[str] = []
    checker.check_exchange(entry, CALL_SCHEMA, RESULT_SCHEMA, problems)
    assert problems == []


@pytest.mark.parametrize(
    ("label", "directory", "schema", "semantic_check"),
    [
        ("descriptors", checker.DESCRIPTORS_DIR, DESCRIPTOR_SCHEMA, None),
        ("manifests", checker.MANIFESTS_DIR, MANIFEST_SCHEMA, checker.manifest_semantic_errors),
    ],
)
def test_positive_and_negative_corpora(label, directory, schema, semantic_check):
    problems: list[str] = []
    checker.check_corpus(
        label=label,
        directory=directory,
        schema=schema,
        problems=problems,
        semantic_check=semantic_check,
    )
    assert problems == []


def test_protocol_records_reject_unknown_fields_but_application_bags_remain_open():
    call = json.loads((checker.TESTS_DIR / "data_only.call.json").read_text(encoding="utf-8"))
    call["extra"] = True
    assert checker.schema_errors(call, CALL_SCHEMA)

    call.pop("extra")
    call["calls"][0]["args"]["extensionValue"] = {"anything": [1, True, None]}
    assert checker.schema_errors(call, CALL_SCHEMA) == []


def test_results_stay_within_the_callers_advertised_capabilities():
    call = json.loads((checker.TESTS_DIR / "happy_render.call.json").read_text(encoding="utf-8"))
    result = json.loads((checker.TESTS_DIR / "happy_render.result.json").read_text(encoding="utf-8"))
    assert checker.capability_errors(call, result) == []

    call["capabilities"] = {"actions": ["data"], "swaps": ["replace"]}
    problems = checker.capability_errors(call, result)
    assert any("unadvertised action 'render'" in problem for problem in problems)
    assert any("unadvertised swap 'morph'" in problem for problem in problems)


def test_render_ids_are_case_safe_in_calls_actions_and_manifests():
    call = json.loads((checker.TESTS_DIR / "happy_render.call.json").read_text(encoding="utf-8"))
    call["calls"][0]["callerRenderId"] = "MixedCase"
    assert checker.schema_errors(call, CALL_SCHEMA)

    result = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "results": [
            {
                "ok": True,
                "actions": [{"action": "state", "targetRenderId": "MixedCase", "stateToken": "t"}],
            }
        ],
    }
    assert checker.schema_errors(result, RESULT_SCHEMA)

    manifest = json.loads((checker.MANIFESTS_DIR / "stateless.valid.json").read_text(encoding="utf-8"))
    manifest["componentInstances"][0]["renderId"] = "MixedCase"
    assert checker.schema_errors(manifest, MANIFEST_SCHEMA)


def _error_envelope(status, code):
    return {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "results": [{"ok": False, "error": {"status": status, "code": code, "message": "x"}}],
    }


@pytest.mark.parametrize("status", [400, 410, 503, 599])
def test_generic_error_code_carries_any_error_status(status):
    assert checker.schema_errors(_error_envelope(status, "error"), RESULT_SCHEMA) == []


@pytest.mark.parametrize("status", [200, 302, 600])
def test_generic_error_code_rejects_non_error_statuses(status):
    assert checker.schema_errors(_error_envelope(status, "error"), RESULT_SCHEMA)


def test_null_request_id_is_reserved_for_one_transport_edge_error():
    edge = _error_envelope(400, "protocol_mismatch")
    edge["requestId"] = None
    assert checker.schema_errors(edge, RESULT_SCHEMA) == []

    edge["results"] = [{"ok": True, "actions": []}]
    assert checker.schema_errors(edge, RESULT_SCHEMA)

    edge["results"] = [
        {"ok": False, "error": {"status": 400, "code": "protocol_mismatch", "message": "x"}},
        {"ok": False, "error": {"status": 400, "code": "protocol_mismatch", "message": "x"}},
    ]
    assert checker.schema_errors(edge, RESULT_SCHEMA)

    edge["results"] = [{"ok": False, "error": {"status": 422, "code": "invalid_args", "message": "x"}}]
    assert checker.schema_errors(edge, RESULT_SCHEMA)

    edge["results"] = [
        {
            "ok": False,
            "error": {
                "status": 400,
                "code": "protocol_mismatch",
                "message": "x",
                "fieldErrors": {"name": "unavailable"},
            },
        }
    ]
    assert checker.schema_errors(edge, RESULT_SCHEMA)

    edge["results"] = [
        {
            "ok": False,
            "sendSequence": 0,
            "error": {"status": 400, "code": "protocol_mismatch", "message": "x"},
        }
    ]
    assert checker.schema_errors(edge, RESULT_SCHEMA)


def test_builtin_checker_enforces_the_null_request_id_edge(monkeypatch):
    monkeypatch.setattr(checker, "jsonschema", None)
    edge = _error_envelope(400, "protocol_mismatch")
    edge["requestId"] = None
    edge["results"] = [{"ok": True, "actions": []}]
    assert checker.schema_errors(edge, RESULT_SCHEMA)

    edge["results"] = [
        {
            "ok": False,
            "sendSequence": 0,
            "error": {"status": 400, "code": "protocol_mismatch", "message": "x"},
        }
    ]
    assert checker.schema_errors(edge, RESULT_SCHEMA)

    edge["results"] = [{"ok": False, "error": {"status": 422, "code": "invalid_args", "message": "x"}}]
    assert checker.schema_errors(edge, RESULT_SCHEMA)


def test_open_application_values_still_have_to_be_strict_json():
    result = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "results": [{"ok": True, "actions": [{"action": "data", "value": float("inf")}]}],
    }
    assert checker.schema_errors(result, RESULT_SCHEMA)


@pytest.mark.parametrize("use_builtin_checker", [False, True])
def test_data_actions_reject_non_blocking_timing(monkeypatch, use_builtin_checker):
    if use_builtin_checker:
        monkeypatch.setattr(checker, "jsonschema", None)
    result = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "results": [
            {
                "ok": True,
                "actions": [{"action": "data", "value": {"saved": True}, "delay": 0.25}],
            }
        ],
    }
    assert checker.schema_errors(result, RESULT_SCHEMA) == []

    result["results"][0]["actions"][0]["wait"] = False
    assert checker.schema_errors(result, RESULT_SCHEMA)


def test_a_broken_exchange_is_reported_by_name(tmp_path):
    tests_copy = tmp_path / "tests"
    shutil.copytree(checker.TESTS_DIR, tests_copy)
    mutated = tests_copy / "happy_render.result.json"
    envelope = json.loads(mutated.read_text(encoding="utf-8"))
    envelope["requestId"] = "r_tampered"
    mutated.write_text(json.dumps(envelope), encoding="utf-8")

    entry = next(entry for entry in ENTRIES if entry["call"] == "happy_render.call.json")
    problems: list[str] = []
    checker.check_exchange(entry, CALL_SCHEMA, RESULT_SCHEMA, problems, tests_dir=tests_copy)
    assert any("happy_render.result.json" in problem for problem in problems)


def test_standalone_checker_passes_with_builtin_backend(monkeypatch, capsys):
    monkeypatch.setattr(checker, "jsonschema", None)
    assert checker.main() == 0
    assert "built-in checker" in capsys.readouterr().out
