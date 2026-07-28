"""
Drive the `citry-client-graph/1` fixture corpus through the browser runtime.

The protocol package's ``tests/index.json`` declares, per fixture, whether
a conforming consumer accepts or rejects it. This suite holds the browser
runtime to those declarations:

- every invalid fixture must be rejected by manifest staging (or, for entries
  marked ``"harness": "adoption"``, by adoption preparation) with the error
  the index records, and never by the missing-physical-cap fallback;
- every valid fixture's canonical scenario, rendered live, must commit in the
  browser under exactly the revision the frozen fixture carries.

Staging is fail-closed and checks the manifest JSON before physical caps, so
invalid fixtures run against an empty cap root with no DOM arranged.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

pytestmark = pytest.mark.e2e

_TESTS_DIR = Path(__file__).resolve().parents[1]
_FIXTURES = _TESTS_DIR.parents[3] / "packages" / "protocol" / "client_graph" / "v1" / "tests"


def _load_conformance() -> Any:
    """Load the producer-conformance module (the canonical scenario renders) by path."""
    path = _TESTS_DIR / "test_client_graph_conformance.py"
    spec = importlib.util.spec_from_file_location("client_graph_conformance", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Dataclass string annotations resolve through sys.modules[cls.__module__],
    # so the module must be registered before its classes are created.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


conformance = _load_conformance()
INDEX = json.loads((_FIXTURES / "index.json").read_text(encoding="utf8"))
STAGE_ENTRIES = [entry for entry in INDEX if entry["expect"] == "invalid" and entry.get("harness", "stage") == "stage"]
ADOPTION_ENTRIES = [entry for entry in INDEX if entry["expect"] == "invalid" and entry.get("harness") == "adoption"]


def _host_html() -> str:
    """A minimal client-active page whose document build inlines the runtime."""
    from citry import Citry, Component

    engine = Citry()

    class Host(Component):
        citry = engine
        js = """
          $component(() => {});
        """
        template = """
          <p>host</p>
        """

    return Host().render().serialize()


def _fixture(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf8"))


def _resign(manifest: dict) -> None:
    unsigned = {key: value for key, value in manifest.items() if key != "revision"}
    canonical = json.dumps(unsigned, separators=(",", ":"), sort_keys=True).encode("utf8")
    manifest["revision"] = hashlib.sha256(canonical).hexdigest()


@pytest.mark.parametrize("entry", STAGE_ENTRIES, ids=lambda entry: entry["manifest"])
def test_staging_rejects_invalid_fixture(page: Any, serve_document: Any, entry: dict) -> None:
    page.goto(serve_document(_host_html()) + "/")
    page.wait_for_function("window.Citry && Citry.manager && !!Citry.manager._stageOwnershipManifest")

    result = page.evaluate(
        """
        (manifest) => {
          try {
            Citry.manager._stageOwnershipManifest(manifest, document.createElement("div"));
            return { threw: false, message: "" };
          } catch (error) {
            return { threw: true, message: String((error && error.message) || error) };
          }
        }
        """,
        _fixture(entry["manifest"]),
    )

    assert result["threw"], f"{entry['manifest']} staged successfully but must be rejected"
    # A missing-cap throw would mean the fixture's JSON defect never fired and
    # the empty cap root failed the staging instead, proving nothing.
    assert "missing physical cap" not in result["message"], result["message"]
    expected = entry.get("browserProblem")
    if expected is not None:
        assert expected in result["message"], f"{entry['manifest']}: {result['message']}"


@pytest.mark.parametrize(
    ("payload_type", "field_path", "bad_value"),
    [
        ("props", "key", 7),
        ("props", "payload.expression", 7),
        ("alpine-handler", "payload.expression", 7),
        ("citry-dom-event", "payload.classId", 7),
        ("citry-dom-event", "payload.event", 7),
        ("citry-dom-event", "payload.handler", 7),
        ("citry-dom-event", "payload.args", False),
        ("citry-dom-event", "payload.key", False),
        ("citry-poll", "payload.classId", 7),
        ("citry-poll", "payload.handler", 7),
        ("citry-poll", "payload.args", False),
    ],
)
def test_staging_rejects_wrong_client_binding_string_field_type(
    page: Any,
    serve_document: Any,
    payload_type: str,
    field_path: str,
    bad_value: object,
) -> None:
    manifest = _fixture("component_tag_client_bindings.manifest.json")
    bindings = manifest["graphs"][0]["nestedComponents"][0]["clientBindings"]
    binding = next(item for item in bindings if item["payload"]["type"] == payload_type)
    if field_path == "key":
        binding["key"] = bad_value
    else:
        binding["payload"][field_path.removeprefix("payload.")] = bad_value
    _resign(manifest)

    page.goto(serve_document(_host_html()) + "/")
    page.wait_for_function("window.Citry && Citry.manager && !!Citry.manager._stageOwnershipManifest")
    result = page.evaluate(
        """
        (candidate) => {
          try {
            Citry.manager._stageOwnershipManifest(candidate, document.createElement("div"));
            return { threw: false, message: "" };
          } catch (error) {
            return { threw: true, message: String((error && error.message) || error) };
          }
        }
        """,
        manifest,
    )

    assert result["threw"], f"{field_path} accepted {bad_value!r}"
    assert f"{field_path} must be a string" in result["message"]


@pytest.mark.parametrize("entry", ADOPTION_ENTRIES, ids=lambda entry: entry["manifest"])
def test_adoption_rejects_invalid_fixture(page: Any, serve_document: Any, entry: dict) -> None:
    manifest = _fixture(entry["manifest"])
    # The flat cap builder below only covers root component instances; a
    # fixture with slot regions or nested components would need real
    # producer-arranged nesting.
    assert all(not graph["slotRegions"] and not graph["nestedComponents"] for graph in manifest["graphs"])

    page.goto(serve_document(_host_html()) + "/")
    page.wait_for_function("window.Citry && Citry.manager && !!Citry.manager.ownership._prepareAdoption")

    result = page.evaluate(
        """
        (manifest) => {
          let caps = "";
          manifest.graphs.forEach((graph, graphIndex) => {
            graph.componentInstances.forEach((instance) => {
              const key =
                manifest.delimiters.format + ":" + manifest.revision +
                ":" + graphIndex + ":i:" + instance.instanceId;
              caps += "<!--" + key + ":s--><!--" + key + ":e-->";
            });
          });
          const template = document.createElement("template");
          template.innerHTML = caps;
          try {
            Citry.manager.ownership._prepareAdoption(manifest, template.content);
            return { threw: false, message: "" };
          } catch (error) {
            return { threw: true, message: String((error && error.message) || error) };
          }
        }
        """,
        manifest,
    )

    assert result["threw"], f"{entry['manifest']} prepared for adoption but must be rejected"
    assert "missing physical cap" not in result["message"], result["message"]
    expected = entry.get("browserProblem")
    if expected is not None:
        assert expected in result["message"], f"{entry['manifest']}: {result['message']}"


def test_browser_accepts_a_valid_manifest_larger_than_one_megabyte(page: Any, serve_document: Any) -> None:
    manifest = _fixture("minimal.manifest.json")
    manifest["mode"] = "production"
    manifest["graphs"][0]["componentClasses"][0]["className"] = "x" * 1_100_000
    _resign(manifest)

    page.goto(serve_document(_host_html()) + "/")
    page.wait_for_function("window.Citry && Citry.manager && !!Citry.manager._stageOwnershipManifest")
    result = page.evaluate(
        """
        (manifest) => {
          const root = document.createElement("div");
          const instance = manifest.graphs[0].componentInstances[0];
          const key = manifest.delimiters.format + ":" + manifest.revision + ":0:i:" + instance.instanceId;
          root.append(document.createComment(key + ":s"), document.createComment(key + ":e"));
          const staged = Citry.manager._stageOwnershipManifest(manifest, root);
          return { revision: staged.revision, bytes: new TextEncoder().encode(JSON.stringify(manifest)).byteLength };
        }
        """,
        manifest,
    )

    assert result["revision"] == manifest["revision"]
    assert result["bytes"] > 1_000_000


@pytest.mark.parametrize("name", sorted(conformance.SCENARIOS))
def test_browser_commits_scenario_render_under_the_frozen_revision(page: Any, serve_document: Any, name: str) -> None:
    html = conformance.SCENARIOS[name]()
    manifest = conformance.manifest_from_html(html)

    page.goto(serve_document(html) + "/")
    page.wait_for_function(
        "window.Citry && Citry.manager && Citry.manager.ownership && Citry.manager.ownership.revisions().length >= 1",
        timeout=8000,
    )

    revisions = page.evaluate("Citry.manager.ownership.revisions()")
    assert manifest["revision"] in revisions
    # The live render must also still be the frozen contract, so browser
    # acceptance is proven for the fixture itself, not just today's producer.
    frozen = json.loads((_FIXTURES / f"{name}.manifest.json").read_text(encoding="utf8"))
    assert manifest["revision"] == frozen["revision"]
