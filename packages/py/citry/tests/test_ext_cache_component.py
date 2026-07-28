"""Public Phase 3 coverage for per-component render caching."""

from __future__ import annotations

import gc
import json
import logging
import weakref
from dataclasses import field
from types import MappingProxyType

import pytest

from citry import Citry, Component, Const, Extension, InMemoryCache, Slot
from citry.ext.cache import CacheKeyError, OnComponentCacheHitContext, component_cache_key
from citry.ext.cache.artifact import _decode_artifact
from citry.ext.debug import Debug
from citry.ownership import OwnershipState, QueueState


class _RecordingCache(InMemoryCache):
    def __init__(self) -> None:
        super().__init__()
        self.gets: list[str] = []
        self.sets: list[tuple[str, float | None]] = []

    def get(self, key: str) -> str | None:
        self.gets.append(key)
        return super().get(key)

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        self.sets.append((key, ttl))
        super().set(key, value, ttl)


def _cache_records(caplog):
    return [record for record in caplog.records if hasattr(record, "citry_cache_outcome")]


class TestComponentCacheConfiguration:
    def test_defaults_and_engine_ttl_are_exposed_without_engine_only_fields(self):
        app = Citry(
            extensions_defaults={
                "cache": {
                    "ttl": 45,
                    "namespace": "shop",
                    "generation": "release-1",
                    "max_entry_bytes": 5_000,
                },
            },
        )

        class Card(Component):
            citry = app

        assert Card.Cache.enabled is False
        assert Card.Cache.ttl == 45
        assert Card.Cache.version == 1
        assert not hasattr(Card.Cache, "namespace")
        assert not hasattr(Card.Cache, "generation")
        assert not hasattr(Card.Cache, "max_entry_bytes")

    def test_component_cache_config_is_inherited(self):
        app = Citry()

        class Base(Component):
            citry = app

            class Cache:
                enabled = True
                ttl = None
                version = "card-v2"

        class Child(Base):
            pass

        assert Child.Cache.enabled is True
        assert Child.Cache.ttl is None
        assert Child.Cache.version == "card-v2"

    def test_child_cache_declaration_adds_to_parent_config(self):
        app = Citry()

        class Base(Component):
            citry = app

            class Cache:
                enabled = True
                version = "base"

        class Child(Base):
            class Cache:
                ttl = 12

        assert Child.Cache.enabled is True
        assert Child.Cache.ttl == 12
        assert Child.Cache.version == "base"

    def test_transparent_child_checks_automatically_inherited_cache_config(self):
        app = Citry()

        class Base(Component):
            citry = app

            class Cache:
                enabled = True

        with pytest.raises(ValueError, match="transparent"):

            class Child(Base):
                transparent = True

                class Cache:
                    ttl = 12

    @pytest.mark.parametrize(
        ("field_name", "value", "message"),
        [
            ("cache_name", "secondary", "unknown component Cache field"),
            ("include_slots", True, "unknown component Cache field"),
            ("namespace", "shop", "unknown component Cache field"),
            ("generation", "v1", "unknown component Cache field"),
            ("max_entry_bytes", 100, "unknown component Cache field"),
            ("enabled", 1, "enabled must be an exact bool"),
            ("ttl", True, "ttl must be"),
            ("ttl", -1, "ttl must be"),
            ("version", True, "version must be"),
            ("version", "", "version must be"),
            ("version", "\ud800", "valid UTF-8 text"),
            ("vary", staticmethod(lambda kwargs, slots: (kwargs, slots)), "synchronous instance method"),
        ],
    )
    def test_invalid_fields_fail_at_class_definition(self, field_name, value, message):
        app = Citry()
        cache_declaration = type("Cache", (), {field_name: value})

        with pytest.raises(ValueError, match=message):

            class Invalid(Component):
                citry = app
                Cache = cache_declaration

    def test_transparent_component_cannot_enable_component_cache(self):
        app = Citry()

        with pytest.raises(ValueError, match="cannot be enabled on a transparent component"):

            class Transparent(Component):
                citry = app
                transparent = True

                class Cache:
                    enabled = True


class TestComponentCacheLookup:
    def test_enabled_component_misses_then_hits(self):
        calls: list[str] = []
        app = Citry()

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            class Kwargs:
                name: str

            template = """
            <p>Hello {{ name }}</p>
            """

            def template_data(self, kwargs, slots):
                calls.append(kwargs.name)
                return super().template_data(kwargs, slots)

        first = str(Card(name="Ada"))
        second = str(Card(name="Ada"))

        assert "Hello Ada" in first
        assert "Hello Ada" in second
        assert calls == ["Ada"]
        key = component_cache_key(Card, vary={"name": "Ada"})
        assert _decode_artifact(app.cache.get(key))

    def test_disabled_component_never_touches_backend(self):
        backend = _RecordingCache()
        app = Citry(cache=backend)
        calls = 0

        class Card(Component):
            citry = app

            class Cache:
                enabled = False

            template = """
            <p>card</p>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        str(Card())
        str(Card())

        assert calls == 2
        assert backend.gets == []
        assert backend.sets == []

    @pytest.mark.parametrize("ttl", [0, 0.0, -0.0])
    def test_zero_ttl_bypasses_variation_and_backend(self, ttl):
        backend = _RecordingCache()
        app = Citry(cache=backend)
        vary_calls = 0
        configured_ttl = ttl

        class Card(Component):
            citry = app

            class Cache:
                enabled = True
                ttl = configured_ttl

                def vary(self, kwargs, slots):
                    nonlocal vary_calls
                    vary_calls += 1
                    return {}

            template = """
            <p>card</p>
            """

        str(Card())
        assert vary_calls == 0
        assert backend.gets == []
        assert backend.sets == []

    @pytest.mark.parametrize("ttl", [0.25, None])
    def test_positive_and_no_expiry_ttl_reach_backend(self, ttl):
        backend = _RecordingCache()
        app = Citry(cache=backend)
        configured_ttl = ttl

        class Card(Component):
            citry = app

            class Cache:
                enabled = True
                ttl = configured_ttl

            template = """
            <p>card</p>
            """

        str(Card())
        assert len(backend.sets) == 1
        assert backend.sets[0][1] == ttl

    def test_positive_ttl_expires_through_public_component_rendering(self, monkeypatch):
        now = [100.0]
        monkeypatch.setattr("citry.cache.time.monotonic", lambda: now[0])
        app = Citry()
        calls = 0

        class Card(Component):
            citry = app

            class Cache:
                enabled = True
                ttl = 5

            template = """
            <p>render {{ generation }}</p>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {"generation": calls}

        assert "render 1" in str(Card())

        now[0] = 104.99
        assert "render 1" in str(Card())
        assert calls == 1

        now[0] = 105.0
        assert "render 2" in str(Card())
        assert calls == 2

    def test_distinct_inputs_create_distinct_entries_and_exact_deletion_misses(self):
        app = Citry()
        calls = 0

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            class Kwargs:
                count: int

            template = """
            <p>{{ count }}</p>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return super().template_data(kwargs, slots)

        str(Card(count=1))
        str(Card(count=2))
        str(Card(count=1))
        assert calls == 2

        key = component_cache_key(Card, vary={"count": 1})
        app.cache.delete(key)
        str(Card(count=1))
        assert calls == 3

    def test_typed_default_and_explicit_equal_value_share_an_entry(self):
        factory_calls = 0
        data_calls = 0
        app = Citry()

        def make_count():
            nonlocal factory_calls
            factory_calls += 1
            return 7

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            class Kwargs:
                count: int = field(default_factory=make_count)

            template = """
            <p>{{ count }}</p>
            """

            def template_data(self, kwargs, slots):
                nonlocal data_calls
                data_calls += 1
                return super().template_data(kwargs, slots)

        str(Card())
        str(Card(count=7))

        assert factory_calls == 1
        assert data_calls == 1

    def test_input_hook_mutation_precedes_typed_variation(self):
        class Normalize(Extension):
            name = "normalize"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_input(self, ctx):
                ctx.kwargs["name"] = ctx.kwargs["name"].casefold()

        app = Citry(extensions=[Normalize])
        calls = 0

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            class Kwargs:
                name: str

            template = """
            <p>{{ name }}</p>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return super().template_data(kwargs, slots)

        assert "ada" in str(Card(name="ADA"))
        assert "ada" in str(Card(name="Ada"))
        assert calls == 1

    def test_const_and_live_inputs_remain_distinct(self):
        app = Citry()
        calls = 0

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <p>{{ value }}</p>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return super().template_data(kwargs, slots)

        str(Card(value=1))
        str(Card(value=Const(1)))
        assert calls == 2


class TestComponentCacheVariation:
    def test_custom_vary_receives_read_only_effective_snapshots(self):
        app = Citry()
        seen: list[tuple[object, object, object]] = []
        data_calls = 0

        class Product:
            def __init__(self, pk, label):
                self.pk = pk
                self.label = label

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

                def vary(self, kwargs, slots):
                    seen.append((type(kwargs), type(slots), self.component))
                    with pytest.raises(TypeError):
                        kwargs["product"] = None
                    return {"product_id": kwargs["product"].pk}

            class Kwargs:
                product: object

            template = """
            <p>{{ label }}</p>
            """

            def template_data(self, kwargs, slots):
                nonlocal data_calls
                data_calls += 1
                return {"label": kwargs.product.label}

        assert "one" in str(Card(product=Product(1, "one")))
        assert "one" in str(Card(product=Product(1, "one")))

        assert data_calls == 1
        assert len(seen) == 2
        assert all(kwargs_type is MappingProxyType for kwargs_type, _slots_type, _component in seen)
        assert all(slots_type is MappingProxyType for _kwargs_type, slots_type, _component in seen)
        assert all(type(component) is Card for _kwargs_type, _slots_type, component in seen)

    def test_unsupported_custom_variation_raises_before_backend_access(self):
        backend = _RecordingCache()
        app = Citry(cache=backend)

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

                def vary(self, kwargs, slots):
                    return object()

        with pytest.raises(CacheKeyError, match="unsupported value type object"):
            str(Card())
        assert backend.gets == []


class TestComponentCacheSlots:
    @pytest.mark.parametrize("content", ["body", Slot("body"), lambda _ctx: "body"])
    def test_supplied_slot_requires_custom_variation(self, content):
        app = Citry()

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            class Slots:
                body: object | None = None

            template = """
            <c-slot name="body" />
            """

        with pytest.raises(CacheKeyError, match="effective Slot content"):
            str(Card(slots={"body": content}))

    def test_typed_slot_default_and_factory_require_custom_variation(self):
        app = Citry()

        class DefaultCard(Component):
            citry = app

            class Cache:
                enabled = True

            class Slots:
                body: object | None = "DEFAULT"

        class FactoryCard(Component):
            citry = app

            class Cache:
                enabled = True

            class Slots:
                body: object | None = field(default_factory=lambda: "DEFAULT")

        for component in (DefaultCard, FactoryCard):
            with pytest.raises(CacheKeyError, match="effective Slot content"):
                str(component())

    def test_slot_added_by_input_hook_requires_custom_variation(self):
        class AddBody(Extension):
            name = "add_body"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_input(self, ctx):
                ctx.slots["body"] = "FROM HOOK"

        app = Citry(extensions=[AddBody])

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            class Slots:
                body: object | None = None

            template = """
            <c-slot name="body" />
            """

        with pytest.raises(CacheKeyError, match="effective Slot content"):
            str(Card())

    def test_optional_none_and_in_template_fallback_are_cacheable(self):
        app = Citry()
        calls = 0

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            class Slots:
                body: object | None = field(default_factory=lambda: None)

            template = """
            <c-slot name="body">FALLBACK</c-slot>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        assert "FALLBACK" in str(Card())
        assert "FALLBACK" in str(Card())
        assert calls == 1

    def test_custom_vary_allows_slot_hit_without_rendering_new_fill(self):
        app = Citry()

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

                def vary(self, kwargs, slots):
                    return {"placement": kwargs["placement"]}

            class Kwargs:
                placement: str

            class Slots:
                body: object | None = None

            template = """
            <c-slot name="body" />
            """

        assert "FIRST" in str(Card(placement="same", slots={"body": "FIRST"}))

        def explode(_ctx):
            raise AssertionError("a cache hit rendered its replacement Slot")

        assert "FIRST" in str(Card(placement="same", slots={"body": explode}))


class TestComponentCacheLifecycle:
    def test_hit_hook_runs_after_replay_and_render_hooks_are_skipped(self):
        calls: list[str] = []
        hits: list[OnComponentCacheHitContext] = []

        class Probe(Extension):
            name = "probe"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_input(self, ctx):
                if type(ctx.component).__name__ == "Card":
                    calls.append("input")

            def on_component_data(self, ctx):
                if type(ctx.component).__name__ == "Card":
                    calls.append("data-hook")

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Card":
                    calls.append("rendered-hook")

            def on_component_cache_hit(self, ctx):
                instance = next(
                    record
                    for record in ctx.component._ownership_graph.snapshot().logical_instances
                    if record.render_id == ctx.component.id
                )
                assert instance.state == OwnershipState.ACTIVE
                queue = next(
                    record
                    for record in ctx.component._ownership_graph.snapshot().render_queue
                    if record.invocation_id == instance.invocation_id
                )
                assert queue.state == QueueState.SETTLED
                hits.append(ctx)
                calls.append("hit")

        app = Citry(extensions=[Probe])

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <p>card</p>
            """

            def template_data(self, kwargs, slots):
                calls.append("data")
                return {}

            def on_render(self):
                calls.append("render")

        class Page(Component):
            citry = app
            template = """
            <c-card />
            """

        str(Page())
        str(Page())

        assert calls == ["input", "data", "data-hook", "render", "rendered-hook", "input", "hit"]
        assert len(hits) == 1
        assert hits[0].kind == "component"
        assert type(hits[0].component) is Card
        assert len(hits[0].key_digest) == 64
        assert hits[0].artifact_bytes > 0
        assert hits[0].frame_count == 1

    def test_failing_hit_observer_is_isolated_and_later_observers_run(self, caplog):
        seen: list[str] = []

        class Failing(Extension):
            name = "failing"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_cache_hit(self, ctx):
                seen.append("failing")
                raise RuntimeError("observer secret must not be logged")

        class Later(Extension):
            name = "later"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_cache_hit(self, ctx):
                seen.append("later")
                return "ignored"

        app = Citry(extensions=[Failing, Later])

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <p>card</p>
            """

        str(Card())
        with caplog.at_level(logging.ERROR, logger="citry"):
            assert "card" in str(Card())

        assert seen == ["failing", "later"]
        assert "extension=failing exception=RuntimeError" in caplog.text
        assert "observer secret" not in caplog.text

    def test_hit_context_is_not_built_without_observer_or_debug_logging(self, monkeypatch):
        app = Citry()

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <p>card</p>
            """

        str(Card())

        import citry.ext.cache.extension as cache_extension_module

        monkeypatch.setattr(
            cache_extension_module,
            "OnComponentCacheHitContext",
            lambda **kwargs: pytest.fail(f"unexpected hit context allocation: {kwargs}"),
        )
        monkeypatch.setattr(
            cache_extension_module,
            "_key_digest",
            lambda key: pytest.fail(f"unexpected digest calculation: {key}"),
        )
        str(Card())

    def test_nested_hit_precedes_outer_store_and_outer_hit_suppresses_inner(self, caplog):
        hits: list[tuple[str, object]] = []

        class Observe(Extension):
            name = "observe"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_cache_hit(self, ctx):
                hits.append((type(ctx.component).__name__, dict(ctx.component.raw_kwargs)))

        app = Citry(extensions=[Observe])

        class Inner(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <i>inner</i>
            """

        class Outer(Component):
            citry = app

            class Cache:
                enabled = True

            class Kwargs:
                page: int

            template = """
            <div>{{ page }}<c-inner /></div>
            """

        str(Outer(page=1))
        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger="citry"):
            str(Outer(page=2))

        records = _cache_records(caplog)
        inner_hit = next(index for index, record in enumerate(records) if record.citry_cache_outcome == "hit")
        outer_store = next(
            index
            for index, record in enumerate(records)
            if record.citry_cache_outcome == "store" and record.citry_cache_component == "Outer"
        )
        assert inner_hit < outer_store
        assert hits == [("Inner", {})]

        hits.clear()
        str(Outer(page=2))
        assert hits == [("Outer", {"page": 2})]

    def test_sibling_hit_notifications_follow_source_order(self):
        names: list[str] = []

        class Observe(Extension):
            name = "observe"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_cache_hit(self, ctx):
                names.append(ctx.component.kwargs.name)

        app = Citry(extensions=[Observe])

        class Item(Component):
            citry = app

            class Cache:
                enabled = True

            class Kwargs:
                name: str

            template = """
            <span>{{ name }}</span>
            """

        class Page(Component):
            citry = app
            template = """
            <c-item c-name="'first'" />
            <c-item c-name="'second'" />
            """

        str(Page())
        str(Page())
        assert names == ["first", "second"]

    def test_nested_hit_uses_the_current_parent(self):
        app = Citry()
        child_calls = 0

        class CachedChild(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <span>child</span>
            """

            def template_data(self, kwargs, slots):
                nonlocal child_calls
                child_calls += 1
                return {}

        class FirstParent(Component):
            citry = app
            template = """
            <div class="first"><c-cached-child /></div>
            """

        class SecondParent(Component):
            citry = app
            template = """
            <section class="second"><c-cached-child /></section>
            """

        assert 'class="first"' in str(FirstParent())
        assert 'class="second"' in str(SecondParent())
        assert child_calls == 1

    def test_error_does_not_publish(self):
        app = Citry()

        class Broken(Component):
            citry = app

            class Cache:
                enabled = True

            def template_data(self, kwargs, slots):
                raise ValueError("deliberate")

        key = component_cache_key(Broken, vary={})
        for _attempt in range(2):
            with pytest.raises(ValueError, match="deliberate"):
                str(Broken())
        assert app.cache.get(key) is None

    def test_version_change_forces_a_miss(self):
        app = Citry()
        calls = 0

        class Card(Component):
            citry = app

            class Cache:
                enabled = True
                version = 1

            template = """
            <p>card</p>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        str(Card())
        str(Card())
        Card.Cache.version = 2
        str(Card())
        assert calls == 2


class TestComponentCacheDiagnostics:
    def test_hit_miss_store_and_bypass_are_safe_structured_debug_records(self, caplog):
        app = Citry()

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <p>secret output</p>
            """

        with caplog.at_level(logging.DEBUG, logger="citry"):
            str(Card(cache_dimension="raw-variation-secret"))
            str(Card(cache_dimension="raw-variation-secret"))

        records = _cache_records(caplog)
        assert [record.citry_cache_outcome for record in records] == ["miss", "store", "hit"]
        assert all(record.citry_cache_class_id == Card.class_id for record in records)
        assert "raw-variation-secret" not in caplog.text
        assert "secret output" not in caplog.text

    def test_corrupt_and_incompatible_entries_are_diagnosed_then_overwritten(self, caplog):
        app = Citry()

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <p>card</p>
            """

        key = component_cache_key(Card, vary={})
        app.cache.set(key, "not-json")
        with caplog.at_level(logging.DEBUG, logger="citry"):
            str(Card())
        assert "corrupt-entry" in [record.citry_cache_outcome for record in _cache_records(caplog)]

        artifact_wire = json.loads(app.cache.get(key))
        artifact_wire["artifact_version"] += 1
        app.cache.set(key, json.dumps(artifact_wire))
        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger="citry"):
            str(Card())
        assert "incompatible-entry" in [record.citry_cache_outcome for record in _cache_records(caplog)]
        assert _decode_artifact(app.cache.get(key))

    def test_stale_css_capture_is_rejected_against_current_whitespace_css(self, caplog):
        backend = InMemoryCache()
        first_calls = 0
        second_calls = 0

        def make_card(app, css_source, generation):
            class Card(Component):
                citry = app

                class Cache:
                    enabled = True

                template = """
                <p>{{ generation }}</p>
                """
                css = css_source

                def template_data(self, kwargs, slots):
                    nonlocal first_calls, second_calls
                    if generation == "first":
                        first_calls += 1
                    else:
                        second_calls += 1
                    return {"generation": generation}

                def css_data(self, kwargs, slots):
                    return {"accent": "red"}

            return Card

        shared_defaults = {"cache": {"namespace": "css-replay", "generation": "v1"}}
        first_app = Citry(cache=backend, extensions_defaults=shared_defaults)
        FirstCard = make_card(
            first_app,
            """
            p { color: var(--accent); }
            """,
            "first",
        )
        key = component_cache_key(FirstCard, vary={})
        assert "first" in str(FirstCard())
        stale_value = backend.get(key)
        assert stale_value is not None

        second_app = Citry(cache=backend, extensions_defaults=shared_defaults)
        SecondCard = make_card(
            second_app,
            """
            """,
            "second",
        )
        assert SecondCard.class_id == FirstCard.class_id
        assert component_cache_key(SecondCard, vary={}) == key

        with caplog.at_level(logging.DEBUG, logger="citry"):
            html = str(SecondCard())

        assert "second" in html
        assert "data-ccss-" not in html
        assert first_calls == 1
        assert second_calls == 1
        assert backend.get(key) != stale_value
        rejected = [record for record in _cache_records(caplog) if record.citry_cache_reason == "replay-rejected"]
        assert len(rejected) == 1
        assert rejected[0].citry_cache_outcome == "incompatible-entry"

    def test_entry_above_absolute_read_cap_is_an_oversized_miss(self, caplog, monkeypatch):
        import citry.ext.cache.artifact as artifact_module
        import citry.ext.cache.limits as limits_module

        monkeypatch.setattr(artifact_module, "_MAX_ARTIFACT_BYTES", 1_024)
        monkeypatch.setattr(limits_module, "_MAX_ARTIFACT_BYTES", 1_024)
        app = Citry()

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <p>card</p>
            """

        key = component_cache_key(Card, vary={})
        app.cache.set(key, "x" * 1_025)

        with caplog.at_level(logging.DEBUG, logger="citry"):
            assert "card" in str(Card())

        records = _cache_records(caplog)
        assert records[0].citry_cache_outcome == "oversized-entry"
        assert records[0].citry_cache_reason == "absolute-limit"
        assert _decode_artifact(app.cache.get(key))

    def test_oversized_and_active_debug_bypass_are_diagnosed_without_storage(self, caplog):
        small_app = Citry(extensions_defaults={"cache": {"max_entry_bytes": 100}})

        class Large(Component):
            citry = small_app

            class Cache:
                enabled = True

            template = """
            <p>
              This output is deliberately large enough that its detached ownership
              artifact exceeds one hundred bytes.
            </p>
            """

        debug_app = Citry(
            extensions=[Debug],
            extensions_defaults={"debug": {"highlight_components": True}},
        )

        class Highlighted(Component):
            citry = debug_app
            render_calls = 0

            class Cache:
                enabled = True

            template = """
            <p>highlighted</p>
            """

            def template_data(self, kwargs, slots):
                type(self).render_calls += 1
                return {}

        with caplog.at_level(logging.DEBUG, logger="citry"):
            str(Large())
            str(Highlighted())
            second_highlighted = str(Highlighted())

        outcomes = [record.citry_cache_outcome for record in _cache_records(caplog)]
        assert "oversized-entry" in outcomes
        assert "bypass" in outcomes
        assert any(record.citry_cache_reason == "debug-active" for record in _cache_records(caplog))
        assert small_app.cache.get(component_cache_key(Large, vary={})) is None
        assert Highlighted.render_calls == 2
        assert "citry-debug-component" in second_highlighted

    def test_deny_mode_extension_skips_storage_with_a_typed_reason(self, caplog):
        class DenyOutputCaching(Extension):
            name = "deny_output_caching"

            def on_component_rendered(self, ctx):
                return None

        app = Citry(extensions=[DenyOutputCaching])

        class Card(Component):
            citry = app
            render_calls = 0

            class Cache:
                enabled = True

            template = """
            <p>card</p>
            """

            def template_data(self, kwargs, slots):
                type(self).render_calls += 1
                return {}

        with caplog.at_level(logging.DEBUG, logger="citry"):
            str(Card())
            str(Card())

        denied = [record for record in _cache_records(caplog) if record.citry_cache_reason == "extension-denied"]
        assert Card.render_calls == 2
        assert len(denied) == 2
        assert all(record.citry_cache_extension == "deny_output_caching" for record in denied)
        assert app.cache.get(component_cache_key(Card, vary={})) is None


class TestComponentCacheFailuresAndLifetime:
    def test_cyclic_extension_payload_skips_storage_instead_of_failing_render(self, caplog):
        class CyclicPayload(Extension):
            name = "cyclic_payload"
            render_cache_mode = "payload"
            render_cache_version = 1

            def export_render_cache(self, ctx):
                payload = {}
                payload["self"] = payload
                return payload

        app = Citry(extensions=[CyclicPayload])

        class Card(Component):
            citry = app
            render_calls = 0

            class Cache:
                enabled = True

            template = """
            <p>card</p>
            """

            def template_data(self, kwargs, slots):
                type(self).render_calls += 1
                return {}

        with caplog.at_level(logging.DEBUG, logger="citry"):
            assert "card" in str(Card())
            assert "card" in str(Card())

        rejected = [record for record in _cache_records(caplog) if record.citry_cache_reason == "artifact-rejected"]
        assert Card.render_calls == 2
        assert len(rejected) == 2
        assert app.cache.get(component_cache_key(Card, vary={})) is None

    def test_non_string_backend_value_is_a_corrupt_miss(self, caplog):
        class NonStringOnce(_RecordingCache):
            def __init__(self):
                super().__init__()
                self.first = True

            def get(self, key):
                if self.first:
                    self.first = False
                    return object()
                return super().get(key)

        backend = NonStringOnce()
        app = Citry(cache=backend)

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <p>card</p>
            """

        with caplog.at_level(logging.DEBUG, logger="citry"):
            assert "card" in str(Card())
        assert "corrupt-entry" in [record.citry_cache_outcome for record in _cache_records(caplog)]
        assert _decode_artifact(backend.get(component_cache_key(Card, vary={})))

    def test_revision_change_inside_backend_set_removes_old_publication(self):
        app = Citry()
        extension = app.extensions.get_extension("cache")
        original_set = app.cache.set

        def invalidating_set(key, value, ttl=None):
            original_set(key, value, ttl=ttl)
            extension._advance_revision()

        app.cache.set = invalidating_set

        class Card(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <p>card</p>
            """

        old_key = component_cache_key(Card, vary={})
        assert "card" in str(Card())
        assert app.cache.get(old_key) is None

    def test_backend_get_and_set_errors_propagate(self):
        class BrokenGet(_RecordingCache):
            def get(self, key):
                raise RuntimeError("get failed")

        class BrokenSet(_RecordingCache):
            def set(self, key, value, ttl=None):
                raise RuntimeError("set failed")

        for backend, message in ((BrokenGet(), "get failed"), (BrokenSet(), "set failed")):
            app = Citry(cache=backend)

            class Card(Component):
                citry = app

                class Cache:
                    enabled = True

                template = """
                <p>card</p>
                """

            with pytest.raises(RuntimeError, match=message):
                str(Card())

    def test_cached_artifact_does_not_retain_unregistered_component_class(self):
        app = Citry()

        def render_and_release():
            class Temporary(Component):
                citry = app

                class Cache:
                    enabled = True

                template = """
                <p>temporary</p>
                """

            str(Temporary())
            class_ref = weakref.ref(Temporary)
            app.unregister(Temporary)
            return class_ref

        class_ref = render_and_release()
        gc.collect()
        assert class_ref() is None
