"""The executable client-graph Python package and its embedded copy."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest

from citry import Citry, Component, ownership_manifest
from citry._protocol import client_graph

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from packages.protocol._tooling import apply_operations, load_cases, load_json_value  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

PROTOCOL_ROOT = ROOT / "packages" / "protocol" / "client_graph" / "v1"
CASES = tuple(
    case for case in load_cases(PROTOCOL_ROOT / "tests" / "conformance-cases.json") if "python" in case.implementations
)
VALIDATORS: dict[str, Callable[[Any], client_graph.ValidationIssue | None]] = {
    "manifest.schema.json": client_graph.validate_manifest,
}


def _mutated(case: Any) -> Any:
    seed = load_json_value(PROTOCOL_ROOT / "tests" / case.seed)
    return apply_operations(seed, case.operations)


@pytest.mark.parametrize("case", CASES, ids=[case.case_id for case in CASES])
def test_embedded_runtime_matches_each_shared_issue(case: Any) -> None:
    issue = VALIDATORS[case.schema](_mutated(case))
    assert issue is not None
    assert issue.path == case.expected.path
    assert issue.category == case.expected.category


def test_runtime_accepts_every_valid_fixture_and_rejects_every_invalid_fixture() -> None:
    tests = PROTOCOL_ROOT / "tests"
    for entry in json.loads((tests / "index.json").read_text(encoding="utf8")):
        manifest = json.loads((tests / entry["manifest"]).read_text(encoding="utf8"))
        issue = client_graph.validate_manifest(manifest)
        assert (issue is None) == (entry["expect"] == "valid"), (entry["manifest"], issue)


def test_builders_copy_records_before_signing_the_manifest() -> None:
    component_class = client_graph.build_component_class("Page_1", "Page")
    instance = client_graph.build_component_instance(
        instance_id=1,
        render_id="page_1",
        class_id="Page_1",
        invocation_id=None,
        parent_render_id=None,
        transparent=False,
    )
    graph = client_graph.build_graph(
        graph_id=0,
        component_classes=[component_class],
        component_instances=[instance],
        source_locations=[],
        nested_components=[],
        component_execution_order_constraints=[],
        fills=[],
        slot_regions=[],
    )
    manifest = client_graph.build_manifest("production", [graph])
    component_class["className"] = "Changed"
    instance["renderId"] = "changed"
    graph["componentClasses"].clear()
    assert manifest["graphs"][0]["componentClasses"] == [{"classId": "Page_1", "className": "Page"}]
    assert manifest["graphs"][0]["componentInstances"][0]["renderId"] == "page_1"
    assert client_graph.validate_manifest(manifest) is None


def test_nested_component_builder_accepts_only_the_closed_morph_mode() -> None:
    values = {
        "invocation_id": 1,
        "source_render_id": "parent",
        "source_class_id": "Parent_1",
        "location_id": None,
        "tag_name": "child",
        "target_class_id": "Child_1",
        "morph_key": None,
        "target_render_id": "child",
        "parent_region_id": None,
        "client_bindings": [],
    }
    assert client_graph.build_nested_component(**values, morph_mode=None)["morphMode"] is None
    assert client_graph.build_nested_component(**values, morph_mode="ignore")["morphMode"] == "ignore"

    for invalid, category in ((False, "type"), ("replace", "enum")):
        with pytest.raises(client_graph.ProtocolValueError) as raised:
            client_graph.build_nested_component(**values, morph_mode=cast("Any", invalid))
        assert raised.value.issue.path == "/morphMode"
        assert raised.value.issue.category == category


def test_manifest_relationships_are_binding_at_construction() -> None:
    component_class = client_graph.build_component_class("Page_1", "Page")
    instance = client_graph.build_component_instance(
        instance_id=1,
        render_id="page_1",
        class_id="Missing_1",
        invocation_id=None,
        parent_render_id=None,
        transparent=False,
    )
    graph = client_graph.build_graph(
        graph_id=0,
        component_classes=[component_class],
        component_instances=[instance],
        source_locations=[],
        nested_components=[],
        component_execution_order_constraints=[],
        fills=[],
        slot_regions=[],
    )
    with pytest.raises(client_graph.ProtocolValueError) as raised:
        client_graph.build_manifest("production", [graph])
    assert raised.value.issue.path == "/graphs/0/componentInstances/0/classId"
    assert raised.value.issue.category == "semantic"


@pytest.mark.parametrize(
    ("graph_id", "category"),
    [(-1, "range"), (1.5, "type"), (9_007_199_254_740_992, "range"), (10**400, "strict_json")],
)
def test_manifest_builder_reports_invalid_numbers_as_protocol_issues(graph_id: Any, category: str) -> None:
    fixture = load_json_value(PROTOCOL_ROOT / "tests" / "minimal.manifest.json")
    fixture["graphs"][0]["graphId"] = graph_id
    with pytest.raises(client_graph.ProtocolValueError) as raised:
        client_graph.build_manifest("production", fixture["graphs"])
    assert raised.value.issue.path == "/graphs/0/graphId"
    assert raised.value.issue.category == category


def test_runtime_rejects_python_values_that_cannot_cross_the_wire() -> None:
    manifest = load_json_value(PROTOCOL_ROOT / "tests" / "minimal.manifest.json")
    manifest["graphs"][0]["graphId"] = 10**400
    issue = client_graph.validate_manifest(manifest)
    assert issue is not None
    assert issue.path == "/graphs/0/graphId"
    assert issue.category == "strict_json"

    cyclic = load_json_value(PROTOCOL_ROOT / "tests" / "minimal.manifest.json")
    cyclic["graphs"].append(cyclic)
    issue = client_graph.validate_manifest(cyclic)
    assert issue is not None
    assert issue.path == "/graphs/1"
    assert issue.category == "strict_json"


def test_manifest_mode_type_returns_an_issue_and_builder_error() -> None:
    manifest = load_json_value(PROTOCOL_ROOT / "tests" / "minimal.manifest.json")
    manifest["mode"] = {}

    issue = client_graph.validate_manifest(manifest)
    assert issue is not None
    assert issue.path == "/mode"
    assert issue.category == "type"

    with pytest.raises(client_graph.ProtocolValueError) as raised:
        client_graph.build_manifest(cast("Any", {}), manifest["graphs"])
    assert raised.value.issue.path == "/mode"
    assert raised.value.issue.category == "type"


def test_structural_faults_follow_schema_field_order() -> None:
    top_level = load_json_value(PROTOCOL_ROOT / "tests" / "minimal.manifest.json")
    top_level["graphs"] = {}
    top_level["delimiters"] = []
    issue = client_graph.validate_manifest(top_level)
    assert issue is not None
    assert issue.path == "/graphs"
    assert issue.category == "type"

    locations = load_json_value(PROTOCOL_ROOT / "tests" / "component_tag_client_bindings.manifest.json")
    location = locations["graphs"][0]["sourceLocations"][0]
    location["sourceOffset"]["start"] = "bad"
    location["mappingKey"] = 7
    issue = client_graph.validate_manifest(locations)
    assert issue is not None
    assert issue.path == "/graphs/0/sourceLocations/0/sourceOffset/start"
    assert issue.category == "type"

    bindings = load_json_value(PROTOCOL_ROOT / "tests" / "component_tag_client_bindings.manifest.json")
    payload = bindings["graphs"][0]["nestedComponents"][0]["clientBindings"][2]["payload"]
    payload["prevent"] = 0
    payload["key"] = 7
    issue = client_graph.validate_manifest(bindings)
    assert issue is not None
    assert issue.path == "/graphs/0/nestedComponents/0/clientBindings/2/payload/prevent"
    assert issue.category == "type"


def test_canonical_json_normalizes_decoded_integer_forms() -> None:
    assert client_graph.canonical_json({"value": 1.0}) == '{"value":1}'
    assert client_graph.canonical_json({"value": "\ud83d\ude00"}) == '{"value":"😀"}'
    with pytest.raises(ValueError, match="decoded integer"):
        client_graph.canonical_json({"value": 1.5})


def test_ownership_comment_builder_and_parser_share_the_literal_prefix() -> None:
    revision = "a" * 64
    comment = client_graph.format_ownership_comment(revision, 0, "i", 3, "s")
    assert comment == f"<!--citry:g1:{revision}:0:i:3:s-->"
    assert client_graph.parse_ownership_comment(comment[4:-3]) == {
        "revision": revision,
        "graphId": "0",
        "kind": "i",
        "recordId": "3",
        "side": "s",
        "key": f"citry:g1:{revision}:0:i:3",
    }
    with pytest.raises(client_graph.ProtocolValueError):
        client_graph.format_ownership_comment(revision, 0, cast("Any", []), 3, "s")
    assert client_graph.parse_ownership_comment(f"citry:g1:{revision}:\u0660:i:\u0663:s") is None


def test_product_preparation_calls_the_protocol_manifest_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = Citry(mode="production")

    class Page(Component):
        citry = engine
        js = """
          $component(() => {});
        """
        template = """
          <p>page</p>
        """

    calls = 0
    original = ownership_manifest.assemble_manifest

    def recording_build(mode: str, graphs: Any, *, audit: bool) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return original(mode, graphs, audit=audit)

    monkeypatch.setattr(ownership_manifest, "assemble_manifest", recording_build)
    artifact = ownership_manifest.prepare_ownership_manifest(cast("Any", Page()).render())
    assert calls == 1
    assert client_graph.validate_manifest(artifact.manifest) is None


def test_artifact_json_revalidates_a_mutated_manifest() -> None:
    engine = Citry(mode="production")

    class Page(Component):
        citry = engine
        js = """
          $component(() => {});
        """
        template = """
          <p>page</p>
        """

    artifact = ownership_manifest.prepare_ownership_manifest(cast("Any", Page()).render())
    artifact.manifest["unexpected"] = True
    with pytest.raises(client_graph.ProtocolValueError) as raised:
        artifact.json()
    assert raised.value.issue.path == "/unexpected"
    assert raised.value.issue.category == "unknown_field"


def test_artifact_json_rejects_schema_drift_even_when_resigned() -> None:
    engine = Citry(mode="production")

    class Page(Component):
        citry = engine
        js = """
          $component(() => {});
        """
        template = """
          <p>page</p>
        """

    artifact = ownership_manifest.prepare_ownership_manifest(cast("Any", Page()).render())
    artifact.manifest["graphs"][0]["componentClasses"][0]["className"] = 7
    unsigned = {key: value for key, value in artifact.manifest.items() if key != "revision"}
    artifact.manifest["revision"] = client_graph.revision_for(unsigned)

    with pytest.raises(client_graph.ProtocolValueError) as raised:
        artifact.json()
    assert raised.value.issue.path == "/graphs/0/componentClasses/0/className"
    assert raised.value.issue.category == "type"


def test_canonical_and_embedded_packages_are_byte_identical() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/sync_protocol_python.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
