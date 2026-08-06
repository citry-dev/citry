"""Public Phase 5 coverage for Cache extension component introspection."""

from __future__ import annotations

import gc
from dataclasses import field
from weakref import ref

from citry import Citry, Component, ComponentExtensionInfo


def _cache_entry(app: Citry, component: type[Component]) -> ComponentExtensionInfo:
    info = app.inspect_component(component, include_extensions=("cache",))
    assert len(info.extensions) == 1
    return info.extensions[0]


class TestCacheIntrospectionShape:
    def test_version_one_shape_is_exact_and_omits_engine_secrets(self) -> None:
        app = Citry(
            autodiscover=False,
            extensions_defaults={
                "cache": {
                    "ttl": 45,
                    "namespace": "private-shop",
                    "generation": "private-release",
                    "max_entry_bytes": 123_456,
                }
            },
        )

        class Card(Component):
            citry = app

        catalog = app.inspect_components(include_extensions=("cache",))

        assert catalog.to_dict()["extension_versions"] == {"cache": 1}
        assert _cache_entry(app, Card) == ComponentExtensionInfo(
            name="cache",
            introspection_version=1,
            data={
                "enabled": False,
                "ttl": 45.0,
                "version": {"kind": "integer", "value": "0x1"},
                "variation": "default",
                "default_variation_slot_source": "possible",
            },
        )
        wire = catalog.to_json()
        assert "private-shop" not in wire
        assert "private-release" not in wire
        assert "max_entry_bytes" not in wire

    def test_inherited_custom_config_is_effective_without_calling_vary(self) -> None:
        app = Citry(autodiscover=False)
        vary_calls = 0

        class Base(Component):
            citry = app

            class Cache:
                enabled = True
                ttl = None
                version = "card-v2"

                def vary(self, kwargs, slots):
                    nonlocal vary_calls
                    vary_calls += 1
                    raise AssertionError("introspection called Cache.vary()")

        class Child(Base):
            pass

        assert _cache_entry(app, Child) == ComponentExtensionInfo(
            name="cache",
            introspection_version=1,
            data={
                "enabled": True,
                "ttl": None,
                "version": {"kind": "string", "value": "card-v2"},
                "variation": "custom",
                "default_variation_slot_source": "not-applicable",
            },
        )
        assert vary_calls == 0

    def test_zero_ttl_and_arbitrary_size_integer_version_are_portable(self) -> None:
        app = Citry(autodiscover=False)
        huge_version = 10**80

        class Card(Component):
            citry = app

            class Cache:
                enabled = True
                ttl = 0
                version = huge_version

            class Slots:
                pass

        catalog = app.inspect_components(include_extensions=("cache",))
        entry = _cache_entry(app, Card)

        assert entry == ComponentExtensionInfo(
            name="cache",
            introspection_version=1,
            data={
                "enabled": True,
                "ttl": 0.0,
                "version": {"kind": "integer", "value": hex(huge_version)},
                "variation": "default",
                "default_variation_slot_source": "none",
            },
        )
        assert hex(huge_version) in catalog.to_json()


class TestCacheIntrospectionSafety:
    def test_slot_source_classification_does_not_execute_factories_or_assets(self) -> None:
        app = Citry(autodiscover=False)
        factory_calls = 0
        render_calls = 0

        def slot_factory():
            nonlocal factory_calls
            factory_calls += 1
            raise AssertionError("introspection called a Slot default factory")

        class Card(Component):
            citry = app
            template_file = "missing-cache-introspection.html"

            class Cache:
                enabled = True

            class Slots:
                body: object | None = field(default_factory=slot_factory)

            def template_data(self, kwargs, slots):
                nonlocal render_calls
                render_calls += 1
                raise AssertionError("introspection rendered the component")

        entry = _cache_entry(app, Card)

        assert entry == ComponentExtensionInfo(
            name="cache",
            introspection_version=1,
            data={
                "enabled": True,
                "ttl": 300.0,
                "version": {"kind": "integer", "value": "0x1"},
                "variation": "default",
                "default_variation_slot_source": "possible",
            },
        )
        assert factory_calls == 0
        assert render_calls == 0

    def test_opaque_slots_schema_reports_possible_source(self) -> None:
        app = Citry(autodiscover=False)

        class OpaqueBase:
            pass

        class OpaqueSlots(OpaqueBase):
            pass

        class Card(Component):
            citry = app
            Slots = OpaqueSlots

        expected = ComponentExtensionInfo(
            name="cache",
            introspection_version=1,
            data={
                "enabled": False,
                "ttl": 300.0,
                "version": {"kind": "integer", "value": "0x1"},
                "variation": "default",
                "default_variation_slot_source": "possible",
            },
        )
        assert _cache_entry(app, Card) == expected

    def test_static_lookup_bypasses_component_metaclass_attribute_hooks(self) -> None:
        app = Citry(autodiscover=False)
        armed = False

        class HostileMeta(type(Component)):
            def __getattribute__(cls, name):
                if armed and name == "Cache":
                    raise AssertionError("introspection used dynamic Cache lookup")
                return super().__getattribute__(name)

        class Card(Component, metaclass=HostileMeta):
            citry = app

            class Cache:
                enabled = True

        armed = True
        assert _cache_entry(app, Card).name == "cache"

    def test_fragment_builtin_has_no_misleading_component_cache_entry(self) -> None:
        app = Citry(autodiscover=False)

        catalog = app.inspect_components(include_builtins=True, include_extensions=("cache",))
        wire = catalog.to_dict()
        cache = next(component for component in wire["components"] if component["name"] == "cache")

        assert wire["extension_versions"] == {"cache": 1}
        assert cache["builtin"] is True
        assert cache["transparent"] is True
        assert cache["extensions"] == {}

    def test_retained_catalog_does_not_keep_unregistered_component_alive(self) -> None:
        app = Citry(autodiscover=False)

        class Card(Component):
            citry = app

        card_ref = ref(Card)
        catalog = app.inspect_components(include_extensions=("cache",))
        app.unregister(Card)
        del Card
        gc.collect()

        assert catalog.to_dict()["extension_versions"] == {"cache": 1}
        assert card_ref() is None
