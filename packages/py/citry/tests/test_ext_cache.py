"""Phase 1 tests for render-cache configuration, keys, and invalidation."""

import re
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from citry import Citry, Component, Const, Extension, InMemoryCache, Slot
from citry.ext.cache import CacheKeyError, component_cache_key, fragment_cache_key
from citry.ext.cache import keys as cache_keys
from citry.ext.cache.limits import _MAX_ARTIFACT_BYTES, _validate_artifact_text_size


def _cache_extension(app):
    return app.extensions.get_extension("cache")


class TestCacheEngineDefaults:
    def test_builtin_defaults(self):
        defaults = _cache_extension(Citry())._defaults
        assert defaults.ttl == 300.0
        assert defaults.namespace is None
        assert defaults.generation is None
        assert defaults.max_entry_bytes == 1_000_000

    def test_configured_defaults_are_copied(self):
        cache_defaults = {
            "ttl": 45,
            "namespace": "shop",
            "generation": "release-7",
            "max_entry_bytes": None,
        }
        app = Citry(extensions_defaults={"cache": cache_defaults})
        cache_defaults["ttl"] = 1
        cache_defaults["namespace"] = "changed"

        defaults = _cache_extension(app)._defaults
        assert defaults.ttl == 45.0
        assert defaults.namespace == "shop"
        assert defaults.generation == "release-7"
        assert defaults.max_entry_bytes is None

    @pytest.mark.parametrize(
        "fields",
        [
            {"ttl": True},
            {"ttl": -1},
            {"ttl": float("nan")},
            {"ttl": "5"},
            {"namespace": ""},
            {"namespace": 1},
            {"namespace": "\ud800"},
            {"generation": "release"},
            {"max_entry_bytes": True},
            {"max_entry_bytes": 0},
            {"enabled": True},
            {"version": "v1"},
            {"vary": ()},
            {"unknown": 1},
        ],
    )
    def test_invalid_engine_defaults_fail_at_construction(self, fields):
        with pytest.raises(ValueError, match="cache"):
            Citry(extensions_defaults={"cache": fields})

    def test_component_cache_declaration_is_available_from_phase_3(self):
        app = Citry()

        class Plain(Component):
            citry = app

        assert Plain.Cache.enabled is False
        assert Plain.Cache.ttl == 300
        assert Plain.Cache.version == 1

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

        assert Card.Cache.enabled is True

    @pytest.mark.parametrize(
        ("mode", "version"),
        [("unknown", None), ("stateless", None), ("payload", 0), ("deny", True)],
    )
    def test_invalid_extension_cache_compatibility_fails_at_construction(self, mode, version):
        class Invalid(Extension):
            name = "invalid"
            render_cache_mode = mode
            render_cache_version = version

        with pytest.raises(ValueError, match="render_cache"):
            Citry(extensions=[Invalid])

    def test_artifact_byte_cap_primitive_rejects_before_future_json_parsing(self):
        assert _validate_artifact_text_size("{}") == 2
        assert _validate_artifact_text_size("€") == 3
        with pytest.raises(ValueError, match="exact strings"):
            _validate_artifact_text_size(b"{}")
        with pytest.raises(ValueError, match="16 MiB"):
            _validate_artifact_text_size("x" * (_MAX_ARTIFACT_BYTES + 1))
        with pytest.raises(ValueError, match="16 MiB"):
            _validate_artifact_text_size("€" * ((_MAX_ARTIFACT_BYTES // 3) + 1))


class TestCacheKeyEncoding:
    def test_public_helpers_reject_wrong_owner_types(self):
        with pytest.raises(TypeError, match="Component class"):
            component_cache_key(object(), vary=())
        with pytest.raises(TypeError, match="Citry instance"):
            fragment_cache_key(object(), "sidebar")

    def test_physical_shapes_are_fixed_ascii_digests(self):
        app = Citry()

        fragment = fragment_cache_key(app, "sidebar")

        class Card(Component):
            citry = app

        component = component_cache_key(Card, vary={"id": 7})
        assert re.fullmatch(r"citry:render:v1:f:[0-9a-f]{64}", fragment)
        assert re.fullmatch(r"citry:render:v1:c:[0-9a-f]{64}", component)
        assert fragment.isascii()
        assert component.isascii()

    def test_raw_identity_and_variation_do_not_leak_into_key(self):
        app = Citry()
        key = fragment_cache_key(app, "private-sidebar", vary={"token": "secret-user-token"})
        assert "private-sidebar" not in key
        assert "secret-user-token" not in key

    def test_component_helper_does_not_construct_or_run_hooks(self):
        calls = 0

        class Probe(Extension):
            name = "probe"

            def on_component_input(self, ctx):
                nonlocal calls
                calls += 1

        app = Citry(extensions=[Probe])

        class Card(Component):
            citry = app

        key = component_cache_key(Card, vary={"id": 1})
        app.cache.set(key, "artifact")
        app.cache.delete(key)
        assert app.cache.get(key) is None
        assert calls == 0

    @pytest.mark.parametrize(
        ("left", "right"),
        [
            (1, True),
            (1, 1.0),
            (1, "1"),
            (b"1", "1"),
            ([1, 2], (1, 2)),
            ([1, 2], [2, 1]),
            (0.0, -0.0),
        ],
    )
    def test_semantically_distinct_values_have_distinct_keys(self, left, right):
        app = Citry()
        assert fragment_cache_key(app, "x", vary=left) != fragment_cache_key(app, "x", vary=right)

    def test_dict_order_and_repeated_acyclic_references_are_stable(self):
        app = Citry()
        shared = [1, 2]
        first = {"b": shared, "a": shared}
        second = {"a": [1, 2], "b": [1, 2]}
        assert fragment_cache_key(app, "x", vary=first) == fragment_cache_key(app, "x", vary=second)

    def test_fragment_controls_unwrap_outer_const_but_components_preserve_it(self):
        app = Citry()

        class Card(Component):
            citry = app

        assert fragment_cache_key(app, Const("x"), vary=Const(1), version=Const("v1")) == fragment_cache_key(
            app,
            "x",
            vary=1,
            version="v1",
        )
        assert component_cache_key(Card, vary=Const(1)) != component_cache_key(Card, vary=1)

    def test_delimiter_shaped_values_and_cache_kinds_do_not_collide(self):
        app = Citry()

        class Card(Component):
            citry = app

        assert fragment_cache_key(app, "x", vary=["a", "b"]) != fragment_cache_key(app, "x", vary=["a,b"])
        assert component_cache_key(Card, vary={"x": ["a", "b"]}) != fragment_cache_key(
            app,
            Card.class_id,
            vary={"x": ["a", "b"]},
        )

    def test_large_bounded_integer_does_not_hit_python_decimal_limits(self):
        assert fragment_cache_key(Citry(), "x", vary=1 << 20_000)

    @pytest.mark.parametrize(
        "value",
        [
            float("nan"),
            float("inf"),
            {1, 2},
            lambda: None,
            Slot("content"),
        ],
    )
    def test_unsupported_values_name_the_variation_path(self, value):
        with pytest.raises(CacheKeyError, match="vary") as error:
            fragment_cache_key(Citry(), "x", vary={"field": value})
        assert error.value.path.startswith("vary")

    def test_collection_subclasses_are_rejected(self):
        class Values(list):
            pass

        with pytest.raises(CacheKeyError, match="Values"):
            fragment_cache_key(Citry(), "x", vary=Values([1]))

    def test_cycles_are_rejected_but_do_not_overflow_python(self):
        value = []
        value.append(value)
        with pytest.raises(CacheKeyError, match="cycle"):
            fragment_cache_key(Citry(), "x", vary=value)

    def test_depth_limit(self):
        value = None
        for _ in range(33):
            value = [value]
        with pytest.raises(CacheKeyError, match="depth"):
            fragment_cache_key(Citry(), "x", vary=value)

    def test_node_limit(self):
        assert fragment_cache_key(Citry(), "x", vary=[None] * 9_999)
        with pytest.raises(CacheKeyError, match="10,000"):
            fragment_cache_key(Citry(), "x", vary=[None] * 10_000)

    def test_encoded_byte_limit(self):
        with pytest.raises(CacheKeyError, match="64 KiB"):
            fragment_cache_key(Citry(), "x", vary="x" * 70_000)

    def test_json_structure_counts_toward_the_encoded_byte_limit(self):
        assert fragment_cache_key(Citry(), "x", vary=[True] * 5_000)
        with pytest.raises(CacheKeyError, match="64 KiB"):
            fragment_cache_key(Citry(), "x", vary=[True] * 6_000)

    def test_multibyte_text_limit_rejects_before_json_serialization(self, monkeypatch):
        class FailingEncoder:
            def iterencode(self, value):
                pytest.fail("oversized multibyte text reached JSON serialization")

        monkeypatch.setattr(cache_keys, "_JSON_ENCODER", FailingEncoder())
        with pytest.raises(CacheKeyError, match="64 KiB"):
            fragment_cache_key(Citry(), "x", vary="€" * 22_000)

    def test_aggregate_byte_limit_rejects_before_full_serialization(self, monkeypatch):
        original_encoder = cache_keys._JSON_ENCODER

        class GuardedEncoder:
            def iterencode(self, value):
                for index, chunk in enumerate(original_encoder.iterencode(value)):
                    if index > 200:
                        pytest.fail("canonical encoder walked the full oversized variation")
                    yield chunk

        monkeypatch.setattr(cache_keys, "_JSON_ENCODER", GuardedEncoder())
        shared = "x" * 60_000
        with pytest.raises(CacheKeyError, match="64 KiB"):
            fragment_cache_key(Citry(), "x", vary=[shared] * 9_999)

    @pytest.mark.parametrize(
        "vary",
        [
            [b"x" * 30_000] * 9_999,
            [1 << 120_000] * 9_999,
        ],
    )
    def test_repeated_large_scalars_reject_before_json_serialization(self, monkeypatch, vary):
        class FailingEncoder:
            def iterencode(self, value):
                pytest.fail("oversized scalar content reached JSON serialization")

        monkeypatch.setattr(cache_keys, "_JSON_ENCODER", FailingEncoder())
        with pytest.raises(CacheKeyError, match="64 KiB"):
            fragment_cache_key(Citry(), "x", vary=vary)

    def test_oversized_bytes_and_integer_versions_are_rejected(self):
        with pytest.raises(CacheKeyError, match="bytes value"):
            fragment_cache_key(Citry(), "x", vary=b"x" * (cache_keys._MAX_KEY_BYTES + 1))
        with pytest.raises(CacheKeyError, match="integer is too large"):
            fragment_cache_key(Citry(), "x", vary=1 << (cache_keys._MAX_KEY_BYTES * 4))
        with pytest.raises(CacheKeyError, match="version"):
            fragment_cache_key(Citry(), "x", version=1 << (cache_keys._MAX_KEY_BYTES * 4))

    def test_dict_keys_must_be_exact_strings(self):
        with pytest.raises(CacheKeyError, match="dict keys"):
            fragment_cache_key(Citry(), "x", vary={1: "value"})

    @pytest.mark.parametrize("version", [True, 1.0, "", "\ud800", None])
    def test_invalid_versions_are_rejected(self, version):
        with pytest.raises(ValueError, match="version"):
            fragment_cache_key(Citry(), "x", version=version)

    @pytest.mark.parametrize("name", ["", "\ud800", 1, True])
    def test_invalid_fragment_names_are_rejected(self, name):
        with pytest.raises(ValueError, match="fragment"):
            fragment_cache_key(Citry(), name)

    @pytest.mark.parametrize("vary", ["\ud800", {"\ud800": "value"}])
    def test_non_utf8_variation_text_is_rejected_contextually(self, vary):
        with pytest.raises(CacheKeyError, match="valid UTF-8 text") as error:
            fragment_cache_key(Citry(), "x", vary=vary)
        assert error.value.path == "vary"


class TestCacheKeyScopeAndCompatibility:
    def test_local_keys_differ_between_engines(self):
        assert fragment_cache_key(Citry(), "x") != fragment_cache_key(Citry(), "x")

    def test_namespace_without_generation_remains_engine_local(self):
        first = Citry(extensions_defaults={"cache": {"namespace": "shop"}})
        second = Citry(extensions_defaults={"cache": {"namespace": "shop"}})
        assert fragment_cache_key(first, "x") != fragment_cache_key(second, "x")

    def test_namespace_and_generation_make_keys_shared(self):
        defaults = {"cache": {"namespace": "shop", "generation": "release-7"}}
        first = Citry(extensions_defaults=defaults)
        second = Citry(extensions_defaults=defaults)
        assert fragment_cache_key(first, "x", vary={"id": 1}) == fragment_cache_key(
            second,
            "x",
            vary={"id": 1},
        )

    def test_extension_version_and_order_participate(self):
        class First(Extension):
            name = "first"
            render_cache_mode = "stateless"
            render_cache_version = 1

        class FirstV2(Extension):
            name = "first"
            render_cache_mode = "stateless"
            render_cache_version = 2

        class Second(Extension):
            name = "second"
            render_cache_mode = "stateless"
            render_cache_version = 1

        defaults = {"cache": {"namespace": "shop", "generation": "release-7"}}
        v1 = Citry(extensions=[First, Second], extensions_defaults=defaults)
        v2 = Citry(extensions=[FirstV2, Second], extensions_defaults=defaults)
        reordered = Citry(extensions=[Second, First], extensions_defaults=defaults)
        assert fragment_cache_key(v1, "x") != fragment_cache_key(v2, "x")
        assert fragment_cache_key(v1, "x") != fragment_cache_key(reordered, "x")

    def test_large_extension_version_uses_bounded_hex_encoding(self):
        class LargeVersion(Extension):
            name = "large_version"
            render_cache_mode = "stateless"
            render_cache_version = 10**5_000

        assert fragment_cache_key(Citry(extensions=[LargeVersion]), "x")

    def test_aggregate_extension_metadata_rejects_before_json_serialization(self, monkeypatch):
        class First(Extension):
            name = ("a" * 22_000) + "_first"
            render_cache_mode = "stateless"
            render_cache_version = 1

        class Second(Extension):
            name = ("b" * 22_000) + "_second"
            render_cache_mode = "stateless"
            render_cache_version = 1

        class Third(Extension):
            name = ("c" * 22_000) + "_third"
            render_cache_mode = "stateless"
            render_cache_version = 1

        class FailingEncoder:
            def iterencode(self, value):
                pytest.fail("oversized extension metadata reached JSON serialization")

        app = Citry(extensions=[First, Second, Third])
        monkeypatch.setattr(cache_keys, "_JSON_ENCODER", FailingEncoder())
        with pytest.raises(CacheKeyError, match="64 KiB"):
            fragment_cache_key(app, "x")


class TestCacheRevision:
    def test_registration_and_initialization_do_not_change_keys(self):
        app = Citry()
        before = fragment_cache_key(app, "x")

        class Card(Component):
            citry = app

        app.initialize()
        assert fragment_cache_key(app, "x") == before

    def test_template_and_file_resets_change_keys(self):
        app = Citry()

        class Card(Component):
            citry = app
            template = """
            <p>card</p>
            """

        first = fragment_cache_key(app, "x")
        Card.reset_template()
        second = fragment_cache_key(app, "x")
        Card.reset_files()
        third = fragment_cache_key(app, "x")
        assert len({first, second, third}) == 3

    def test_only_final_alias_removal_changes_keys(self):
        app = Citry()

        class MyCard(Component):
            citry = app

        before = fragment_cache_key(app, "x")
        app.unregister("mycard")
        assert fragment_cache_key(app, "x") == before
        app.unregister("my-card")
        assert fragment_cache_key(app, "x") != before

    def test_clear_advances_before_a_backend_clear_failure(self):
        class FailingClear(InMemoryCache):
            def clear(self):
                super().clear()
                raise RuntimeError("clear failed")

        app = Citry(cache=FailingClear())
        before = fragment_cache_key(app, "x")
        with pytest.raises(RuntimeError, match="clear failed"):
            app.clear()
        assert fragment_cache_key(app, "x") != before

    def test_files_reset_advances_after_a_hook_failure(self):
        class FailingReset(Extension):
            name = "failing_reset"

            def on_files_reset(self, ctx):
                raise RuntimeError("reset failed")

        app = Citry(extensions=[FailingReset])

        class Card(Component):
            citry = app

        before = fragment_cache_key(app, "x")
        with pytest.raises(RuntimeError, match="reset failed"):
            Card.reset_files()
        assert fragment_cache_key(app, "x") != before

    def test_rejected_unregistration_does_not_change_keys(self):
        class Reject(Extension):
            name = "reject"

            def on_component_unregistered(self, ctx):
                raise RuntimeError("keep registered")

        app = Citry(extensions=[Reject])

        class Card(Component):
            citry = app

        before = fragment_cache_key(app, "x")
        with pytest.raises(RuntimeError, match="keep registered"):
            app.unregister(Card)
        assert fragment_cache_key(app, "x") == before

    def test_reset_hides_new_revision_until_downstream_hooks_finish(self):
        entered = Event()
        release = Event()
        key_started = Event()

        class BlockingReset(Extension):
            name = "blocking_reset"

            def on_files_reset(self, ctx):
                entered.set()
                assert release.wait(timeout=2)

        app = Citry(extensions=[BlockingReset])

        class Card(Component):
            citry = app

        before = fragment_cache_key(app, "x")

        def build_key():
            key_started.set()
            return fragment_cache_key(app, "x")

        with ThreadPoolExecutor(max_workers=2) as executor:
            reset = executor.submit(Card.reset_files)
            assert entered.wait(timeout=2)
            concurrent_key = executor.submit(build_key)
            assert key_started.wait(timeout=2)
            try:
                assert not concurrent_key.done()
            finally:
                release.set()
            reset.result()
            assert concurrent_key.result() != before

    def test_hot_replacement_advances_once_at_final_unregistration(self):
        app = Citry()
        extension = _cache_extension(app)

        def define_card():
            class Card(Component):
                citry = app

            return Card

        first = define_card()
        before = extension._revision_snapshot()
        class_id = first.class_id
        app.unregister(first)
        after_unregister = extension._revision_snapshot()
        second = define_card()
        assert second.class_id == class_id
        assert after_unregister == before + 1
        assert extension._revision_snapshot() == after_unregister

    def test_revision_increments_are_thread_safe(self):
        extension = _cache_extension(Citry())
        before = extension._revision_snapshot()

        def advance() -> None:
            for _ in range(500):
                extension._advance_revision()

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(advance) for _ in range(8)]
            for future in futures:
                future.result()

        assert extension._revision_snapshot() == before + 4_000
