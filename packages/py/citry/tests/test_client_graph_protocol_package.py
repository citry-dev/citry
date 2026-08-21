"""CI checks for the standalone `citry-client-graph/1` protocol package."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

from citry import Citry, Component
from citry._protocol.client_graph import REVISION_ALIAS_LENGTH, canonical_json
from citry.ownership_manifest import COMMENT_PREFIX, PROTOCOL

_ROOT = Path(__file__).resolve().parents[4]
_VALIDATE = _ROOT / "packages" / "protocol" / "client_graph" / "v1" / "validate.py"
_MARKER = '<script type="application/json" data-citry-graph>'


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("citry_client_graph_validate", _VALIDATE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load()
SCHEMA = checker.load_json(checker.ROOT / "manifest.schema.json")


def _resign(manifest: dict) -> None:
    unsigned = {key: value for key, value in manifest.items() if key != "revision"}
    canonical = canonical_json(unsigned).encode("utf8")
    manifest["revision"] = hashlib.sha256(canonical).hexdigest()


def _manifest_of(html: str) -> dict:
    return json.loads(html.split(_MARKER, 1)[1].split("</script>", 1)[0])


def _server_manifest() -> dict:
    # Development mode so the manifest carries source provenance (`sourceLocations`),
    # which the location-based mutation tests below need.
    c = Citry(mode="development")

    class Child(Component):
        citry = c
        template = "<section><c-slot /></section>"

    class Page(Component):
        citry = c
        template = "<c-child><span>fill</span></c-child>"

        class Events:
            def save(self):
                return None

    return _manifest_of(Page().render().serialize())


def _fallback_manifest() -> dict:
    c = Citry(mode="development")

    class Child(Component):
        citry = c
        template = '<section><c-slot><i x-text="label"></i></c-slot></section>'

    class Page(Component):
        citry = c
        template = "<c-child />"

    return _manifest_of(Page().render().serialize())


def test_golden_fixtures_match_their_index_expectations():
    problems: list[str] = []
    entries = checker.check_index_entries(checker.load_json(checker.TESTS / "index.json"), problems)
    checker.check_index_matches_disk(entries, problems)
    for entry in entries:
        problems.extend(checker.check_fixture(entry, SCHEMA))
    assert problems == []
    # The corpus stays meaningful on both sides: valid fixtures to accept,
    # invalid fixtures to reject.
    expectations = {entry["expect"] for entry in entries}
    assert expectations == {"valid", "invalid"}


def test_wire_constants_are_locked_across_producer_schema_fixture_and_browser_consumer():
    fixture = checker.load_json(checker.TESTS / "minimal.manifest.json")
    runtime = (_ROOT / "packages/py/citry/citry/ext/dependencies/client/citry.js").read_text(encoding="utf-8")
    javascript = _ROOT / "packages/protocol/client_graph/v1/js/src"
    canonical_source = (javascript / "canonical.ts").read_text(encoding="utf-8")
    comments_source = (javascript / "comments.ts").read_text(encoding="utf-8")
    manifests_source = (javascript / "manifests.ts").read_text(encoding="utf-8")
    core_embed_source = (javascript / "core-embed.ts").read_text(encoding="utf-8")

    assert PROTOCOL == "citry-client-graph/1"
    assert COMMENT_PREFIX == "citry:g1"
    assert REVISION_ALIAS_LENGTH == 8
    assert SCHEMA["properties"]["protocol"]["const"] == PROTOCOL
    assert SCHEMA["properties"]["mode"]["enum"] == ["production", "development"]
    assert SCHEMA["properties"]["delimiters"]["properties"]["format"]["const"] == COMMENT_PREFIX
    assert fixture["protocol"] == PROTOCOL
    assert fixture["mode"] in {"production", "development"}
    assert fixture["delimiters"] == {"format": COMMENT_PREFIX}
    # The browser consumer receives the same constants and validator through
    # the one generated core region.
    assert f'PROTOCOL = "{PROTOCOL}"' in canonical_source
    assert f'OWNERSHIP_COMMENT_PREFIX = "{COMMENT_PREFIX}"' in comments_source
    assert "REVISION_ALIAS_LENGTH = 8" in comments_source
    assert "ownershipRevisionAlias" in core_embed_source
    assert "value.delimiters.format !== OWNERSHIP_COMMENT_PREFIX" in manifests_source
    assert 'value.mode !== "production" && value.mode !== "development"' in manifests_source
    assert "assertValidManifest" in core_embed_source
    assert runtime.count("/*<citry-client-graph-v1>*/") == 1
    assert runtime.count("/*</citry-client-graph-v1>*/") == 1
    assert "CitryClientGraphProtocol.assertValidManifest(manifest)" in runtime
    assert "validatePhysicalCaps(OWNERSHIP_COMMENT_PREFIX" not in runtime
    assert runtime.count("validatePhysicalCaps(") == 2
    assert "offsetUnit" not in runtime


def test_reference_reader_accepts_a_valid_manifest_larger_than_one_megabyte():
    manifest = checker.load_json(checker.TESTS / "minimal.manifest.json")
    manifest["mode"] = "production"
    manifest["graphs"][0]["componentClasses"][0]["className"] = "x" * 1_100_000
    _resign(manifest)

    assert len(json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode("utf8")) > 1_000_000
    assert checker.check_manifest(manifest, SCHEMA) == []


def test_tampered_revision_and_unknown_fields_are_rejected():
    manifest = checker.load_json(checker.TESTS / "minimal.manifest.json")
    manifest["revision"] = "0" * 64
    manifest["surprise"] = True
    problems = checker.check_manifest(manifest, SCHEMA)
    assert any("revision" in problem for problem in problems)
    assert any(
        "Additional properties" in problem or "unknown member" in problem or "top-level" in problem
        for problem in problems
    )


def test_render_ids_must_be_safe_for_case_insensitive_html_attribute_names():
    manifest = _server_manifest()
    manifest["graphs"][0]["componentInstances"][0]["renderId"] = "MixedCase"
    _resign(manifest)
    assert any("renderId is not safe" in problem for problem in checker.check_manifest(manifest, SCHEMA))


def test_resigned_manifest_with_an_unknown_reference_is_rejected():
    manifest = _server_manifest()
    manifest["graphs"][0]["componentInstances"][0]["classId"] = "NoSuchClass_000000"
    _resign(manifest)
    assert any("classId is unknown" in problem for problem in checker.check_manifest(manifest, SCHEMA))


def test_production_manifest_must_not_carry_provenance():
    # A production manifest that smuggles a location reference is rejected.
    c = Citry(mode="production")

    class Child(Component):
        citry = c
        template = "<section>child</section>"

    class Page(Component):
        citry = c

        class Events:
            def save(self):
                return None

        template = '<c-child @c-click="save()" />'

    manifest = _manifest_of(Page().render().serialize())
    assert manifest["mode"] == "production"
    assert manifest["graphs"][0]["sourceLocations"] == []
    manifest["graphs"][0]["nestedComponents"][0]["locationId"] = 1
    _resign(manifest)
    assert any("location reference" in problem for problem in checker.check_manifest(manifest, SCHEMA))


def test_resigned_manifest_with_inconsistent_relationships_is_rejected():
    bad_invocation = _server_manifest()
    graph = bad_invocation["graphs"][0]
    graph["componentInstances"][0]["invocationId"] = graph["nestedComponents"][0]["invocationId"]
    graph["componentInstances"][1]["invocationId"] = None
    _resign(bad_invocation)
    assert any("instance" in problem for problem in checker.check_manifest(bad_invocation, SCHEMA))

    bad_fill = _server_manifest()
    graph = bad_fill["graphs"][0]
    fill = graph["fills"][0]
    child = graph["componentInstances"][1]
    fill["ownerRenderId"] = child["renderId"]
    fill["ownerClassId"] = child["classId"]
    _resign(bad_fill)
    assert any("fill source location" in problem for problem in checker.check_manifest(bad_fill, SCHEMA))

    bad_region = _server_manifest()
    region = bad_region["graphs"][0]["slotRegions"][0]
    region["parentRegionId"] = region["regionId"]
    _resign(bad_region)
    assert any("region ancestry" in problem for problem in checker.check_manifest(bad_region, SCHEMA))

    bad_fill_kind = _server_manifest()
    graph = bad_fill_kind["graphs"][0]
    fill = graph["fills"][0]
    location = next(record for record in graph["sourceLocations"] if record["locationId"] == fill["locationId"])
    location["kind"] = "component-call"
    _resign(bad_fill_kind)
    assert any("source location kind" in problem for problem in checker.check_manifest(bad_fill_kind, SCHEMA))

    missing_supply_carrier = _server_manifest()
    missing_supply_carrier["graphs"][0]["fills"][0]["sourceInvocationId"] = None
    _resign(missing_supply_carrier)
    assert any(
        "supplied fill carrier" in problem for problem in checker.check_manifest(missing_supply_carrier, SCHEMA)
    )

    missing_fallback_carrier = _fallback_manifest()
    missing_fallback_carrier["graphs"][0]["fills"][0]["fallbackLocationId"] = None
    _resign(missing_fallback_carrier)
    assert any(
        "fallback location kind" in problem for problem in checker.check_manifest(missing_fallback_carrier, SCHEMA)
    )


def test_real_server_manifest_validates_in_both_modes():
    for mode in ("production", "development"):
        c = Citry(mode=mode)

        class Child(Component):
            citry = c
            js = """
              $component(() => {});
            """
            template = """
              <span>child</span>
            """

        class Page(Component):
            citry = c

            class Events:
                def save(self):
                    return None

            template = """
              <c-child $c-props="{n: 1}" @c-click="save({x: `)`})" />
            """

        assert checker.check_manifest(_manifest_of(Page().render().serialize()), SCHEMA) == []
