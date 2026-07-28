"""Phase 2 tests for the detached render-cache artifact format."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace

import pytest

from citry import Citry, Component
from citry.ext.cache import component_cache_key
from citry.ext.cache.artifact import (
    ArtifactExtension,
    ArtifactFrame,
    ArtifactFramePart,
    ArtifactPlaceholderPart,
    ArtifactRegionPart,
    ArtifactTextPart,
    CachedRenderArtifact,
    FrozenJsonObject,
    _decode_artifact,
    _encode_artifact,
    _freeze_object,
    _thaw_json,
)
from citry.ext.cache.errors import CacheArtifactError
from citry.ext.cache.limits import _MAX_ARTIFACT_BYTES, _MAX_ARTIFACT_DEPTH, _MAX_ARTIFACT_RECORDS


def _artifact() -> CachedRenderArtifact:
    return CachedRenderArtifact(
        root_frame=0,
        frames=(
            ArtifactFrame(
                instance=0,
                class_id="example.Page",
                class_name="Page",
                is_component_root=True,
                root_markers=("data-cache-probe",),
                parts=(
                    ArtifactTextPart("<main>"),
                    ArtifactFramePart(1),
                    ArtifactPlaceholderPart("deps:js"),
                    ArtifactTextPart("</main>"),
                ),
            ),
            ArtifactFrame(
                instance=1,
                class_id="example.Card",
                class_name="Card",
                is_component_root=True,
                root_markers=(),
                parts=(ArtifactRegionPart(0, ArtifactTextPart("<p>cached</p>")),),
            ),
        ),
        ownership=FrozenJsonObject(
            (
                ("instances", ("boundary", "descendant")),
                ("regions", (0,)),
            )
        ),
        extensions=(
            ArtifactExtension(
                name="dependencies",
                version=1,
                payload=FrozenJsonObject((("records", ("example.Page", "example.Card")),)),
            ),
        ),
    )


class TestArtifactCodec:
    def test_round_trip_is_deterministic_and_immutable(self):
        artifact = _artifact()
        encoded = _encode_artifact(artifact)

        assert _encode_artifact(artifact) == encoded
        assert _decode_artifact(encoded) == artifact
        assert "c1" not in encoded
        with pytest.raises(FrozenInstanceError):
            artifact.root_frame = 1

    def test_empty_output_is_a_valid_hit_value(self):
        artifact = CachedRenderArtifact(
            root_frame=0,
            frames=(
                ArtifactFrame(
                    instance=0,
                    class_id="example.Empty",
                    class_name="Empty",
                    is_component_root=True,
                    root_markers=(),
                    parts=(),
                ),
            ),
            ownership=FrozenJsonObject(()),
            extensions=(),
        )
        assert _decode_artifact(_encode_artifact(artifact)) == artifact

    def test_decode_is_safe_to_repeat_concurrently(self):
        encoded = _encode_artifact(_artifact())
        with ThreadPoolExecutor(max_workers=8) as executor:
            decoded = list(executor.map(_decode_artifact, [encoded] * 100))
        assert decoded == [_artifact()] * 100

    @pytest.mark.parametrize(
        ("value", "match"),
        [
            ("not json", "JSON"),
            (
                '{"artifact_version":2,"citry_version":1,"created_by":"citry-python",'
                '"root_frame":0,"frames":[],"ownership":{},"extensions":[]}',
                "artifact_version",
            ),
            ('{"artifact_version":1,"artifact_version":1}', "duplicate"),
            ('{"artifact_version":NaN}', "finite JSON"),
        ],
    )
    def test_malformed_json_is_rejected_as_an_artifact_error(self, value, match):
        with pytest.raises(CacheArtifactError, match=match):
            _decode_artifact(value)

    def test_literal_surrogate_is_corrupt_text_not_an_oversized_artifact(self):
        with pytest.raises(CacheArtifactError, match="valid UTF-8") as error:
            _decode_artifact("\ud800")

        assert "exceeding max_entry_bytes" not in str(error.value)

    def test_backend_value_must_be_an_exact_string(self):
        with pytest.raises(CacheArtifactError, match="exact strings"):
            _decode_artifact(b"{}")

    def test_escaped_surrogate_is_rejected_during_wire_validation(self):
        wire = json.loads(_encode_artifact(_artifact()))
        wire["frames"][0]["parts"][0][1] = "\ud800"
        encoded = json.dumps(wire)
        assert r"\ud800" in encoded

        with pytest.raises(CacheArtifactError, match=r"parts\[0\]\[1\].*valid UTF-8"):
            _decode_artifact(encoded)

    def test_typed_artifact_surrogate_is_rejected_before_json_encoding(self):
        first_frame = _artifact().frames[0]
        malformed = replace(
            _artifact(),
            frames=(
                replace(first_frame, parts=(ArtifactTextPart("\ud800"), *first_frame.parts[1:])),
                *_artifact().frames[1:],
            ),
        )

        with pytest.raises(CacheArtifactError, match=r"parts\[0\].*valid UTF-8"):
            _encode_artifact(malformed)

    def test_unknown_fields_are_rejected(self):
        wire = json.loads(_encode_artifact(_artifact()))
        wire["surprise"] = True
        with pytest.raises(CacheArtifactError, match="unknown field"):
            _decode_artifact(json.dumps(wire))

    def test_bool_is_not_accepted_as_an_integer_reference(self):
        wire = json.loads(_encode_artifact(_artifact()))
        wire["root_frame"] = True
        with pytest.raises(CacheArtifactError, match="root_frame"):
            _decode_artifact(json.dumps(wire))

    def test_frame_reference_cycle_is_rejected(self):
        wire = json.loads(_encode_artifact(_artifact()))
        wire["frames"][1]["parts"] = [["frame", 0]]
        with pytest.raises(CacheArtifactError, match="cycle"):
            _decode_artifact(json.dumps(wire))

    def test_shared_frame_occurrence_is_rejected(self):
        wire = json.loads(_encode_artifact(_artifact()))
        wire["frames"][0]["parts"].insert(2, ["frame", 1])
        with pytest.raises(CacheArtifactError, match="more than once"):
            _decode_artifact(json.dumps(wire))

    def test_unreachable_frame_is_rejected(self):
        wire = json.loads(_encode_artifact(_artifact()))
        wire["frames"][0]["parts"] = [["text", "only root"]]
        with pytest.raises(CacheArtifactError, match="unreachable"):
            _decode_artifact(json.dumps(wire))

    def test_depth_limit_is_reported_without_recursion_failure(self):
        nested = "null"
        for _ in range(140):
            nested = f"[{nested}]"
        wire = (
            '{"artifact_version":1,"citry_version":1,"created_by":"citry-python",'
            '"root_frame":0,"frames":[],"ownership":'
            f'{nested},"extensions":[]}}'
        )
        with pytest.raises(CacheArtifactError, match="depth"):
            _decode_artifact(wire)

    def test_typed_region_depth_is_rejected_before_recursive_wire_conversion(self):
        part = ArtifactTextPart("deep")
        for index in range(_MAX_ARTIFACT_DEPTH + 2):
            part = ArtifactRegionPart(index, part)
        frame = replace(_artifact().frames[0], parts=(part,))
        artifact = replace(_artifact(), frames=(frame,), extensions=())

        with pytest.raises(CacheArtifactError, match="depth"):
            _encode_artifact(artifact)

    def test_record_limit_is_enforced_during_wire_validation(self):
        wire = json.loads(_encode_artifact(_artifact()))
        wire["ownership"] = {"records": [[] for _ in range(_MAX_ARTIFACT_RECORDS)]}

        with pytest.raises(CacheArtifactError, match="100,000 structural record"):
            _decode_artifact(json.dumps(wire))

    def test_extension_names_must_be_unique(self):
        wire = json.loads(_encode_artifact(_artifact()))
        wire["extensions"].append(wire["extensions"][0])
        with pytest.raises(CacheArtifactError, match="duplicate extension"):
            _decode_artifact(json.dumps(wire))

    @pytest.mark.parametrize(
        "marker",
        [
            'data-cid="archived-id"',
            "data-cid-archived-id",
            'data-citry-key="archived:key"',
            'data-probe="unterminated',
        ],
    )
    def test_boundary_reserved_or_malformed_markers_are_rejected(self, marker):
        wire = json.loads(_encode_artifact(_artifact()))
        wire["frames"][0]["root_markers"] = [marker]
        with pytest.raises(CacheArtifactError, match=r"marker|attribute"):
            _decode_artifact(json.dumps(wire))

    def test_encode_rejects_duplicate_frozen_json_keys(self):
        malformed = CachedRenderArtifact(
            root_frame=0,
            frames=_artifact().frames,
            ownership=FrozenJsonObject((("x", 1), ("x", 2))),
            extensions=(),
        )
        with pytest.raises(CacheArtifactError, match="unique"):
            _encode_artifact(malformed)

    def test_encode_wraps_json_integer_serialization_failures(self):
        artifact = replace(
            _artifact(),
            ownership=FrozenJsonObject((("huge", 10**5_000),)),
        )

        with pytest.raises(CacheArtifactError, match="Could not encode cached render artifact"):
            _encode_artifact(artifact)

    @pytest.mark.parametrize(
        ("artifact", "error", "match"),
        [
            (None, TypeError, "Expected"),
            (replace(_artifact(), root_frame=True), CacheArtifactError, "root_frame"),
            (replace(_artifact(), frames=list(_artifact().frames)), CacheArtifactError, "immutable tuple"),
            (replace(_artifact(), extensions=list(_artifact().extensions)), CacheArtifactError, "immutable tuple"),
            (
                replace(_artifact(), ownership=FrozenJsonObject((("z", 1), ("a", 2)))),
                CacheArtifactError,
                "sorted",
            ),
            (
                replace(_artifact(), ownership=FrozenJsonObject((("x", object()),))),
                CacheArtifactError,
                "unsupported",
            ),
            (
                replace(_artifact(), extensions=(object(),)),
                CacheArtifactError,
                "ArtifactExtension",
            ),
            (
                replace(_artifact(), extensions=(replace(_artifact().extensions[0], name=""),)),
                CacheArtifactError,
                "must not be empty",
            ),
            (
                replace(_artifact(), extensions=(replace(_artifact().extensions[0], version=0),)),
                CacheArtifactError,
                "positive",
            ),
            (replace(_artifact(), frames=(object(),)), CacheArtifactError, "ArtifactFrame"),
            (
                replace(
                    _artifact(),
                    frames=(replace(_artifact().frames[0], instance=-1), *_artifact().frames[1:]),
                ),
                CacheArtifactError,
                "non-negative",
            ),
            (
                replace(
                    _artifact(),
                    frames=(replace(_artifact().frames[0], class_id=""), *_artifact().frames[1:]),
                ),
                CacheArtifactError,
                "must not be empty",
            ),
            (
                replace(
                    _artifact(),
                    frames=(replace(_artifact().frames[0], is_component_root=1), *_artifact().frames[1:]),
                ),
                CacheArtifactError,
                "must be a bool",
            ),
            (
                replace(
                    _artifact(),
                    frames=(
                        replace(_artifact().frames[0], instance=None),
                        *_artifact().frames[1:],
                    ),
                ),
                CacheArtifactError,
                "identity without an instance",
            ),
            (
                replace(
                    _artifact(),
                    frames=(replace(_artifact().frames[0], class_id=None), *_artifact().frames[1:]),
                ),
                CacheArtifactError,
                "requires class_id",
            ),
            (
                replace(
                    _artifact(),
                    frames=(replace(_artifact().frames[0], root_markers=[]), *_artifact().frames[1:]),
                ),
                CacheArtifactError,
                "immutable tuple",
            ),
            (
                replace(
                    _artifact(),
                    frames=(
                        replace(_artifact().frames[0], root_markers=("data-probe", "data-probe")),
                        *_artifact().frames[1:],
                    ),
                ),
                CacheArtifactError,
                "duplicate marker",
            ),
            (
                replace(
                    _artifact(),
                    frames=(replace(_artifact().frames[0], parts=[]), *_artifact().frames[1:]),
                ),
                CacheArtifactError,
                "immutable tuple",
            ),
        ],
        ids=lambda value: type(value).__name__,
    )
    def test_typed_artifact_validation_rejects_invalid_shapes(self, artifact, error, match):
        with pytest.raises(error, match=match):
            _encode_artifact(artifact)

    @pytest.mark.parametrize(
        ("mutate", "match"),
        [
            (lambda wire: wire.pop("created_by"), "missing required field"),
            (lambda wire: wire.__setitem__("created_by", "foreign"), "created_by"),
            (lambda wire: wire.__setitem__("citry_version", 2), "citry_version"),
            (lambda wire: wire.__setitem__("frames", {}), "frames.*array"),
            (lambda wire: wire.__setitem__("extensions", {}), "extensions.*array"),
            (lambda wire: wire["frames"].__setitem__(0, []), "JSON object"),
            (lambda wire: wire["frames"][0].pop("parts"), "missing required field"),
            (lambda wire: wire["frames"][0].__setitem__("instance", -1), "non-negative"),
            (lambda wire: wire["frames"][0].__setitem__("class_id", ""), "must not be empty"),
            (lambda wire: wire["frames"][0].__setitem__("component_root", 1), "must be a bool"),
            (lambda wire: wire["frames"][0].__setitem__("instance", None), "identity without"),
            (lambda wire: wire["frames"][0].__setitem__("class_name", None), "requires class_id"),
            (lambda wire: wire["frames"][0].__setitem__("root_markers", {}), "root_markers.*array"),
            (lambda wire: wire["frames"][0].__setitem__("root_markers", [1]), "exact string"),
            (lambda wire: wire["frames"][0].__setitem__("parts", {}), "parts.*array"),
            (lambda wire: wire["frames"][0].__setitem__("parts", [[]]), "string part tag"),
            (lambda wire: wire["frames"][0].__setitem__("parts", [["text", 1]]), "exact string"),
            (lambda wire: wire["frames"][0].__setitem__("parts", [["frame", -1]]), "non-negative"),
            (lambda wire: wire["frames"][0].__setitem__("parts", [["placeholder", ""]]), "must not be empty"),
            (lambda wire: wire["frames"][0].__setitem__("parts", [["region", 0]]), "malformed"),
            (lambda wire: wire["extensions"].__setitem__(0, []), "JSON object"),
            (lambda wire: wire["extensions"][0].pop("payload"), "missing required field"),
            (lambda wire: wire["extensions"][0].__setitem__("name", ""), "must not be empty"),
            (lambda wire: wire["extensions"][0].__setitem__("version", 0), "positive"),
            (lambda wire: wire["extensions"][0].__setitem__("payload", []), "must be a JSON object"),
            (lambda wire: wire.__setitem__("frames", []), "at least one frame"),
            (lambda wire: wire.__setitem__("root_frame", 99), "existing frame"),
            (lambda wire: wire["frames"][0].__setitem__("parts", [["frame", 99]]), "missing frame"),
        ],
    )
    def test_wire_validation_rejects_invalid_shapes(self, mutate, match):
        wire = json.loads(_encode_artifact(_artifact()))
        mutate(wire)
        with pytest.raises(CacheArtifactError, match=match):
            _decode_artifact(json.dumps(wire))

    def test_codec_limits_and_private_freeze_helpers(self):
        encoded = _encode_artifact(_artifact())
        with pytest.raises(ValueError, match="max_entry_bytes"):
            _encode_artifact(_artifact(), max_entry_bytes=True)
        with pytest.raises(CacheArtifactError, match="exceeding max_entry_bytes"):
            _encode_artifact(_artifact(), max_entry_bytes=len(encoded) - 1)
        with pytest.raises(CacheArtifactError, match="JSON object"):
            _freeze_object([], "payload")
        with pytest.raises(CacheArtifactError, match="non-string"):
            _freeze_object({1: "bad"}, "payload")
        with pytest.raises(CacheArtifactError, match="non-finite"):
            _freeze_object({"value": float("inf")}, "payload")
        with pytest.raises(CacheArtifactError, match="unsupported"):
            _freeze_object({"value": object()}, "payload")
        with pytest.raises(CacheArtifactError, match="unsupported"):
            _thaw_json(object())

    def test_max_entry_bytes_counts_utf8_bytes_not_characters(self):
        first_frame = _artifact().frames[0]
        artifact = replace(
            _artifact(),
            frames=(
                replace(first_frame, parts=(ArtifactTextPart("příliš"), *first_frame.parts[1:])),
                *_artifact().frames[1:],
            ),
        )
        encoded = _encode_artifact(artifact)
        byte_size = len(encoded.encode("utf-8"))
        assert byte_size > len(encoded)

        assert _encode_artifact(artifact, max_entry_bytes=byte_size) == encoded
        with pytest.raises(CacheArtifactError, match="exceeding max_entry_bytes"):
            _encode_artifact(artifact, max_entry_bytes=len(encoded))

    def test_absolute_format_cap_rejects_backend_reads_and_publication(self):
        oversized_text = "x" * (_MAX_ARTIFACT_BYTES + 1)
        with pytest.raises(CacheArtifactError, match="exceeding max_entry_bytes"):
            _decode_artifact(oversized_text)

        first_frame = _artifact().frames[0]
        artifact = replace(
            _artifact(),
            frames=(
                replace(first_frame, parts=(ArtifactTextPart(oversized_text), *first_frame.parts[1:])),
                *_artifact().frames[1:],
            ),
        )
        with pytest.raises(CacheArtifactError, match="exceeding max_entry_bytes"):
            _encode_artifact(artifact)


class TestArtifactCorruptionIntegration:
    @pytest.mark.parametrize("escaped", [False, True], ids=["literal-surrogate", "escaped-surrogate"])
    def test_surrogate_backend_values_miss_and_are_overwritten(self, escaped):
        app = Citry()
        renders = 0

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

                def vary(self, kwargs, slots):
                    return "stable"

            template = """
            <p>hello</p>
            """

            def template_data(self, kwargs, slots):
                nonlocal renders
                renders += 1
                return {}

        assert "hello" in str(Card())
        key = component_cache_key(Card, vary="stable")
        stored = app.cache.get(key)
        assert stored is not None

        if escaped:
            wire = json.loads(stored)
            wire["frames"][0]["parts"][0][1] = "\ud800"
            corrupt = json.dumps(wire)
        else:
            corrupt = "\ud800"
        app.cache.set(key, corrupt)

        assert "hello" in str(Card())
        assert renders == 2
        assert app.cache.get(key) != corrupt

        assert "hello" in str(Card())
        assert renders == 2
