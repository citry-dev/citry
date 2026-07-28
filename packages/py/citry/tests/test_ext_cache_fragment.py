"""Public Phase 4 coverage for the transparent ``<c-cache>`` component."""

from __future__ import annotations

import logging
import math

import pytest

from citry import Citry, Component, Extension, InMemoryCache
from citry.component_registry import AlreadyRegistered
from citry.ext.cache import CacheKeyError, OnComponentCacheHitContext, fragment_cache_key
from citry.ext.debug import Debug
from citry.ownership import OwnershipState


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


class TestFragmentCacheSurface:
    def test_cache_is_a_reserved_transparent_builtin(self):
        app = Citry()
        cache_component = app.get("cache")

        assert cache_component.transparent is True
        assert cache_component.name == "cache"

        with pytest.raises(AlreadyRegistered, match="reserved for the built-in <c-cache>"):

            class Cache(Component):
                citry = app

    def test_named_fill_is_rejected_by_the_builtin_schema(self):
        app = Citry()

        class Page(Component):
            citry = app
            template = """
            <c-cache key="fragment">
              <c-fill name="other">content</c-fill>
            </c-cache>
            """

        with pytest.raises(SyntaxError, match="does not allow a slot named 'other'"):
            str(Page())

    def test_key_is_required_by_the_builtin_schema(self):
        app = Citry()

        class Page(Component):
            citry = app
            template = """
            <c-cache>content</c-cache>
            """

        with pytest.raises(SyntaxError, match="must have one of the following attributes: 'key', 'c-key'"):
            str(Page())

    def test_unknown_control_is_rejected_by_the_builtin_schema(self):
        app = Citry()

        class Page(Component):
            citry = app
            template = """
            <c-cache key="fragment" backend="other">content</c-cache>
            """

        with pytest.raises(SyntaxError, match="Found invalid attributes: backend"):
            str(Page())

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"key": ""}, "exact non-empty string"),
            ({"key": "\ud800"}, "valid UTF-8 text"),
            ({"key": 1}, "exact non-empty string"),
            ({"key": "fragment", "ttl": True}, "ttl must be"),
            ({"key": "fragment", "ttl": -1}, "ttl must be"),
            ({"key": "fragment", "ttl": math.inf}, "ttl must be"),
            ({"key": "fragment", "ttl": math.nan}, "ttl must be"),
            ({"key": "fragment", "ttl": 10**5_000}, "representable as finite seconds"),
            ({"key": "fragment", "version": True}, "version must be"),
            ({"key": "fragment", "version": ""}, "version must be"),
            ({"key": "fragment", "version": "\ud800"}, "valid UTF-8 text"),
            ({"key": "fragment", "enabled": 1}, "enabled must be an exact bool"),
        ],
    )
    def test_invalid_runtime_controls_fail_exactly(self, kwargs, message):
        app = Citry()

        class Page(Component):
            citry = app

            class Kwargs:
                key: object
                ttl: object = 30
                version: object = 1
                enabled: object = True

            template = """
            <c-cache
              c-key="key"
              c-ttl="ttl"
              c-version="version"
              c-enabled="enabled"
            >
              body
            </c-cache>
            """

        with pytest.raises(ValueError, match=message):
            str(Page(**kwargs))

    def test_key_and_version_subclasses_are_rejected(self):
        class StringSubclass(str):
            __slots__ = ()

        class IntegerSubclass(int):
            pass

        app = Citry()

        class Page(Component):
            citry = app

            class Kwargs:
                key: object
                version: object

            template = """
            <c-cache c-key="key" c-version="version">body</c-cache>
            """

        with pytest.raises(ValueError, match="exact non-empty string"):
            str(Page(key=StringSubclass("fragment"), version=1))
        with pytest.raises(ValueError, match="version must be"):
            str(Page(key="fragment", version=IntegerSubclass(1)))

    def test_bypass_still_validates_scalars_but_does_not_encode_vary(self):
        backend = _RecordingCache()
        app = Citry(cache=backend)
        cyclic: list[object] = []
        cyclic.append(cyclic)

        class Page(Component):
            citry = app

            class Kwargs:
                key: object
                vary: object
                enabled: bool

            template = """
            <c-cache c-key="key" c-vary="vary" c-enabled="enabled">body</c-cache>
            """

        assert "body" in str(Page(key="fragment", vary=cyclic, enabled=False))
        assert backend.gets == []
        assert backend.sets == []
        with pytest.raises(ValueError, match="exact non-empty string"):
            str(Page(key=1, vary=cyclic, enabled=False))

    def test_enabled_fragment_rejects_cyclic_variation_before_backend_access(self):
        backend = _RecordingCache()
        app = Citry(cache=backend)
        cyclic: list[object] = []
        cyclic.append(cyclic)

        class Page(Component):
            citry = app

            class Kwargs:
                vary: object

            template = """
            <c-cache key="fragment" c-vary="vary">body</c-cache>
            """

        with pytest.raises(CacheKeyError, match="cycle"):
            str(Page(vary=cyclic))
        assert backend.gets == []
        assert backend.sets == []


class TestFragmentCacheLookup:
    def test_top_level_fragment_misses_then_hits_without_a_wrapper(self):
        app = Citry()
        calls = 0

        class Item(Component):
            citry = app
            template = """
            <b>hello</b>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        class Page(Component):
            citry = app
            template = """
            <c-cache key="top-level"><c-item /></c-cache>
            """

        first = str(Page())
        second = str(Page())

        assert "hello" in first
        assert "hello" in second
        assert "c-cache" not in first
        assert calls == 1
        assert app.cache.get(fragment_cache_key(app, "top-level")) is not None

    def test_static_and_equal_computed_keys_share_an_entry(self):
        app = Citry()
        calls: list[str] = []

        class First(Component):
            citry = app
            template = """
            <b>first</b>
            """

            def template_data(self, kwargs, slots):
                calls.append("first")
                return {}

        class Page(Component):
            citry = app
            template = """
            <c-cache key="shared"><c-first /></c-cache>
            <c-cache c-key="'shared'"><c-first /></c-cache>
            """

        html = str(Page())

        assert html.count("first") == 2
        assert calls == ["first"]

    def test_same_key_reuses_first_artifact_when_another_call_site_has_a_different_body(self):
        app = Citry()
        calls: list[str] = []

        class First(Component):
            citry = app
            template = """
            <b>first</b>
            """

            def template_data(self, kwargs, slots):
                calls.append("first")
                return {}

        class Second(Component):
            citry = app
            template = """
            <b>second</b>
            """

            def template_data(self, kwargs, slots):
                calls.append("second")
                return {}

        class Page(Component):
            citry = app
            template = """
            <c-cache key="shared-body"><c-first /></c-cache>
            <c-cache key="shared-body"><c-second /></c-cache>
            """

        html = str(Page())

        assert html.count("first") == 2
        assert "second" not in html
        assert calls == ["first"]

    def test_structured_variation_creates_independent_entries(self):
        app = Citry()
        calls = 0

        class Item(Component):
            citry = app

            class Kwargs:
                value: str

            template = """
            <span>{{ value }}</span>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return super().template_data(kwargs, slots)

        class Page(Component):
            citry = app

            class Kwargs:
                value: str

            template = """
            <c-cache key="varied" c-vary="{'value': value}">
              <c-item c-value="value" />
            </c-cache>
            """

        assert "alpha" in str(Page(value="alpha"))
        assert "beta" in str(Page(value="beta"))
        assert "alpha" in str(Page(value="alpha"))
        assert calls == 2

    def test_each_field_in_structured_variation_misses_independently(self):
        app = Citry()
        calls: list[tuple[str, str]] = []

        class Item(Component):
            citry = app

            class Kwargs:
                language: str
                section: str

            template = """
            <span>{{ language }}/{{ section }}</span>
            """

            def template_data(self, kwargs, slots):
                calls.append((kwargs.language, kwargs.section))
                return super().template_data(kwargs, slots)

        class Page(Component):
            citry = app

            class Kwargs:
                language: str
                section: str

            template = """
            <c-cache
              key="two-field-variation"
              c-vary="[language, section]"
            >
              <c-item
                c-language="language"
                c-section="section"
              />
            </c-cache>
            """

        matrix = [
            ("en", "home"),
            ("en", "about"),
            ("fr", "home"),
            ("en", "home"),
            ("en", "about"),
            ("fr", "home"),
        ]
        for language, section in matrix:
            assert f"{language}/{section}" in str(Page(language=language, section=section))

        assert calls == [("en", "home"), ("en", "about"), ("fr", "home")]

    @pytest.mark.parametrize(
        ("enabled", "ttl"),
        [(False, 30), (True, 0), (True, -0.0)],
    )
    def test_disabled_and_zero_ttl_render_without_backend_access(self, enabled, ttl):
        backend = _RecordingCache()
        app = Citry(cache=backend)
        calls = 0

        class Item(Component):
            citry = app
            template = """
            <b>item</b>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        class Page(Component):
            citry = app

            class Kwargs:
                enabled: bool
                ttl: float

            template = """
            <c-cache key="bypass" c-enabled="enabled" c-ttl="ttl">
              <c-item />
            </c-cache>
            """

        str(Page(enabled=enabled, ttl=ttl))
        str(Page(enabled=enabled, ttl=ttl))

        assert calls == 2
        assert backend.gets == []
        assert backend.sets == []

    @pytest.mark.parametrize("ttl", [0.25, None])
    def test_ttl_is_forwarded_to_the_engine_backend(self, ttl):
        backend = _RecordingCache()
        app = Citry(cache=backend)
        configured_ttl = ttl

        class Page(Component):
            citry = app
            template = """
            <c-cache key="ttl" c-ttl="configured_ttl">body</c-cache>
            """

            def template_data(self, kwargs, slots):
                return {"configured_ttl": configured_ttl}

        assert "body" in str(Page())
        assert backend.sets[-1][1] == ttl

    def test_omitted_ttl_uses_the_engine_cache_default(self):
        backend = _RecordingCache()
        app = Citry(cache=backend, extensions_defaults={"cache": {"ttl": 17}})

        class Page(Component):
            citry = app
            template = """
            <c-cache key="default-ttl">body</c-cache>
            """

        assert "body" in str(Page())
        assert backend.sets[-1][1] == 17

    def test_empty_output_is_cached_and_not_treated_as_a_miss(self):
        hits: list[OnComponentCacheHitContext] = []

        class Observe(Extension):
            name = "observe"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_cache_hit(self, ctx):
                hits.append(ctx)

        app = Citry(extensions=[Observe])

        class Page(Component):
            citry = app
            template = """
            <c-cache key="empty" />
            """

        assert str(Page()).strip() == ""
        assert str(Page()).strip() == ""
        assert len(hits) == 1
        assert hits[0].kind == "fragment"
        assert hits[0].component is not None
        assert hits[0].frame_count >= 1


class TestFragmentCacheOwnershipAndNesting:
    def test_literal_slot_replays_the_current_callers_fill(self):
        app = Citry()
        fill_calls: list[str] = []

        class FillContent(Component):
            citry = app
            template = """
            <strong>caller fill</strong>
            """

            def template_data(self, kwargs, slots):
                fill_calls.append(self.id)
                return {}

        class Card(Component):
            citry = app
            template = """
            <c-cache key="literal-slot">
              <c-slot name="body">fallback</c-slot>
            </c-cache>
            """

        class Page(Component):
            citry = app
            template = """
            <c-card>
              <c-fill name="body">
                <c-fill-content />
              </c-fill>
            </c-card>
            """

        first = Page().render()
        assert "caller fill" in first.serialize()
        first_snapshot = first.context.ownership.snapshot()
        first_page = next(
            record
            for record in first_snapshot.logical_instances
            if record.state == OwnershipState.ACTIVE and record.class_id == Page.class_id
        )
        first_content = next(
            record
            for record in first_snapshot.logical_instances
            if record.state == OwnershipState.ACTIVE and record.class_id == FillContent.class_id
        )

        second = Page().render()
        assert "caller fill" in second.serialize()
        second_snapshot = second.context.ownership.snapshot()
        second_page = next(
            record
            for record in second_snapshot.logical_instances
            if record.state == OwnershipState.ACTIVE and record.class_id == Page.class_id
        )
        second_content = next(
            record
            for record in second_snapshot.logical_instances
            if record.state == OwnershipState.ACTIVE and record.class_id == FillContent.class_id
        )
        current_fill = next(
            record
            for record in second_snapshot.logical_fills
            if record.state == OwnershipState.ACTIVE
            and record.slot_name == "body"
            and record.lexical_owner_render_id == second_page.render_id
        )

        assert fill_calls == [first_content.render_id]
        assert second_page.render_id != first_page.render_id
        assert second_content.render_id != first_content.render_id
        assert second_content.logical_parent_render_id == second_page.render_id
        assert current_fill.lexical_owner_render_id == second_page.render_id

    def test_same_artifact_twice_gets_distinct_body_component_ids(self):
        app = Citry()
        calls = 0

        class Item(Component):
            citry = app
            template = """
            <span>item</span>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        class Page(Component):
            citry = app
            template = """
            <div>
              <c-cache key="twice"><c-item /></c-cache>
              <c-cache key="twice"><c-item /></c-cache>
            </div>
            """

        rendered = Page().render()
        html = rendered.serialize()
        active = [
            record
            for record in rendered.context.ownership.snapshot().logical_instances
            if record.state == OwnershipState.ACTIVE and record.class_id == Item.class_id
        ]

        assert calls == 1
        assert len(active) == 2
        assert len({record.render_id for record in active}) == 2
        assert all(f"data-cid-{record.render_id}" in html for record in active)

    def test_fragment_hit_rebinds_body_ownership_to_the_current_writer(self):
        app = Citry()

        class Item(Component):
            citry = app
            template = """
            <span>item</span>
            """

        class FirstPage(Component):
            citry = app
            template = """
            <c-cache key="writer"><c-item /></c-cache>
            """

        class SecondPage(Component):
            citry = app
            template = """
            <c-cache key="writer"><c-item /></c-cache>
            """

        FirstPage().render()
        second = SecondPage().render()
        snapshot = second.context.ownership.snapshot()
        page = next(
            record
            for record in snapshot.logical_instances
            if record.state == OwnershipState.ACTIVE and record.class_id == SecondPage.class_id
        )
        item = next(
            record
            for record in snapshot.logical_instances
            if record.state == OwnershipState.ACTIVE and record.class_id == Item.class_id
        )

        assert item.logical_parent_render_id == page.render_id

    def test_inner_hit_precedes_outer_store_and_outer_hit_suppresses_inner(self, caplog):
        hits: list[str] = []

        class Observe(Extension):
            name = "observe"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_cache_hit(self, ctx):
                if ctx.kind == "fragment":
                    hits.append(ctx.component.kwargs.key)

        app = Citry(extensions=[Observe])
        calls = 0

        class Item(Component):
            citry = app
            template = """
            <span>item</span>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        class Page(Component):
            citry = app

            class Kwargs:
                outer: int

            template = """
            <c-cache key="outer" c-vary="outer">
              <c-cache key="inner"><c-item /></c-cache>
            </c-cache>
            """

        str(Page(outer=1))
        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger="citry"):
            str(Page(outer=2))

        records = [record for record in caplog.records if hasattr(record, "citry_cache_outcome")]
        inner_hit = next(index for index, record in enumerate(records) if record.citry_cache_outcome == "hit")
        outer_store = next(index for index, record in enumerate(records) if record.citry_cache_outcome == "store")
        assert inner_hit < outer_store
        assert calls == 1
        assert hits == ["inner"]

        str(Page(outer=2))
        assert hits == ["inner", "outer"]

    def test_sibling_fragment_hit_notifications_follow_source_order(self):
        hits: list[str] = []

        class Observe(Extension):
            name = "observe"
            render_cache_mode = "stateless"
            render_cache_version = 1

            def on_component_cache_hit(self, ctx):
                if ctx.kind == "fragment":
                    hits.append(ctx.component.kwargs.key)

        app = Citry(extensions=[Observe])

        class Page(Component):
            citry = app
            template = """
            <c-cache key="first">one</c-cache>
            <c-cache key="second">two</c-cache>
            """

        str(Page())
        str(Page())
        assert hits == ["first", "second"]

    def test_component_cache_inside_fragment_reuses_each_layer(self):
        app = Citry()
        calls = 0

        class Item(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <span>item</span>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        class Page(Component):
            citry = app
            template = """
            <c-cache key="outer-fragment"><c-item /></c-cache>
            """

        assert "item" in str(Page())
        assert "item" in str(Page())
        app.cache.delete(fragment_cache_key(app, "outer-fragment"))
        assert "item" in str(Page())
        assert calls == 1

    def test_nested_same_key_fragments_complete_without_locking_or_recursion(self):
        app = Citry()
        calls = 0

        class Item(Component):
            citry = app
            template = """
            <span>item</span>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        class Page(Component):
            citry = app
            template = """
            <c-cache key="same"><c-cache key="same"><c-item /></c-cache></c-cache>
            """

        assert "item" in str(Page())
        assert "item" in str(Page())
        assert calls == 1

    def test_fragment_inside_component_cache_is_suppressed_by_the_outer_hit(self):
        app = Citry()
        calls = 0

        class Item(Component):
            citry = app
            template = """
            <span>item</span>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        class CachedOuter(Component):
            citry = app

            class Cache:
                enabled = True

            template = """
            <c-cache key="inner-fragment"><c-item /></c-cache>
            """

        assert "item" in str(CachedOuter())
        app.cache.delete(fragment_cache_key(app, "inner-fragment"))
        assert "item" in str(CachedOuter())
        assert calls == 1


class TestFragmentCacheFailures:
    def test_body_error_does_not_poison_the_entry(self):
        app = Citry()
        calls = 0

        class Flaky(Component):
            citry = app
            template = """
            <span>{{ value }}</span>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise RuntimeError("boom")
                return {"value": "ok"}

        class Page(Component):
            citry = app
            template = """
            <c-cache key="flaky"><c-flaky /></c-cache>
            """

        with pytest.raises(RuntimeError, match="boom"):
            str(Page())
        assert "ok" in str(Page())
        assert "ok" in str(Page())
        assert calls == 2

    def test_exact_helper_deletion_forces_a_fresh_body_render(self):
        app = Citry()
        calls = 0

        class Item(Component):
            citry = app
            template = """
            <span>item</span>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        class Page(Component):
            citry = app
            template = """
            <c-cache key="delete-me"><c-item /></c-cache>
            """

        str(Page())
        str(Page())
        app.cache.delete(fragment_cache_key(app, "delete-me"))
        str(Page())
        assert calls == 2

    def test_recovered_body_error_is_rendered_but_never_published(self):
        app = Citry()
        calls = 0

        class Failing(Component):
            citry = app

            def on_render(self):
                nonlocal calls
                calls += 1
                raise RuntimeError("boom")

        class Page(Component):
            citry = app
            template = """
            <c-cache key="recovered">
              <c-error-fallback fallback="safe"><c-failing /></c-error-fallback>
            </c-cache>
            """

        assert "safe" in str(Page())
        assert "safe" in str(Page())
        assert calls == 2
        assert app.cache.get(fragment_cache_key(app, "recovered")) is None

    def test_active_debug_bypasses_fragment_lookup_and_storage(self):
        backend = _RecordingCache()
        app = Citry(
            cache=backend,
            extensions=[Debug],
            extensions_defaults={"debug": {"highlight_components": True}},
        )
        calls = 0

        class Item(Component):
            citry = app
            template = """
            <span>item</span>
            """

            def template_data(self, kwargs, slots):
                nonlocal calls
                calls += 1
                return {}

        class Page(Component):
            citry = app
            template = """
            <c-cache key="debug"><c-item /></c-cache>
            """

        assert "citry-debug-component" in str(Page())
        assert "citry-debug-component" in str(Page())
        assert calls == 2
        assert backend.gets == []
        assert backend.sets == []

    def test_fragment_diagnostics_hide_raw_inputs_and_component_identity(self, caplog):
        app = Citry()

        class Page(Component):
            citry = app
            template = """
            <c-cache key="private-key" c-vary="{'token': 'private-vary'}">
              private-body
            </c-cache>
            """

        with caplog.at_level(logging.DEBUG, logger="citry"):
            str(Page())
            str(Page())

        records = [record for record in caplog.records if hasattr(record, "citry_cache_outcome")]
        assert records
        assert all(record.citry_cache_kind == "fragment" for record in records)
        assert all(record.citry_cache_component is None for record in records)
        assert all(record.citry_cache_class_id is None for record in records)
        assert "private-key" not in caplog.text
        assert "private-vary" not in caplog.text
        assert "private-body" not in caplog.text
