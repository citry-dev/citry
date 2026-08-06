"""Tests for the Citry global instance."""

# ruff: noqa: ANN

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from citry import Citry, CitrySettings, Component, Extension
from citry import citry as default_citry


class TestCitryInstance:
    def test_create_empty(self):
        c = Citry()
        # A fresh instance carries exactly the built-in components (created
        # lazily on the first lookup), nothing else.
        assert set(c.components) == {"provide", "cache", "component", "element", "error-fallback", "js", "css"}

    def test_repr(self):
        c = Citry()
        assert repr(c) == "Citry(components=0)"

    def test_mode_defaults_to_production(self):
        assert Citry().mode == "production"

    def test_mode_development_is_stored(self):
        assert Citry(mode="development").mode == "development"

    def test_invalid_mode_rejected_at_construction(self):
        # A typo must fail loudly, not silently ship or omit developer output.
        with pytest.raises(ValueError, match="mode must be one of"):
            Citry(mode="staging")
        with pytest.raises(ValueError, match="mode must be one of"):
            CitrySettings(mode="prod")

    def test_clear(self):
        c = Citry()

        class A(Component):
            citry = c

        assert "a" in c.components
        c.clear()
        # User components are gone; the built-ins are recreated on lookup.
        assert set(c.components) == {"provide", "cache", "component", "element", "error-fallback", "js", "css"}

    def test_settings_stored(self):
        # Citry now takes a typed settings schema (CitrySettings) rather than
        # arbitrary kwargs. extensions_defaults is stored on it.
        c = Citry(extensions_defaults={"view": {"ttl": 60}})
        assert c.settings.extensions_defaults == {"view": {"ttl": 60}}
        assert c.settings.extensions == ()

    def test_registry_storage_is_not_public(self):
        import citry

        c = Citry()
        assert not hasattr(c, "registry")
        assert not hasattr(citry, "ComponentRegistry")


class TestDefaultCitryInstance:
    def test_default_instance_is_citry(self):
        assert isinstance(default_citry, Citry)

    def test_default_instance_is_stable(self):
        from citry import citry as d2

        assert default_citry is d2


class TestCitryComponentAssignment:
    def test_component_assigned_to_default(self):
        class MyComp(Component):
            pass

        assert MyComp.citry is default_citry
        assert default_citry.has("mycomp")

    def test_component_assigned_to_explicit_citry(self):
        c = Citry()

        class MyComp(Component):
            citry = c

        assert c.has("mycomp")

    def test_components_on_different_instances(self):
        c1 = Citry()
        c2 = Citry()

        class CompA(Component):
            citry = c1

        class CompB(Component):
            citry = c2

        assert c1.has("compa")
        assert not c1.has("compb")
        assert c2.has("compb")
        assert not c2.has("compa")


class TestSecretAndEventRegistries:
    def test_defaults(self):
        c = Citry()
        assert c.settings.secret is None
        assert c.settings.event_result_resolvers == ()
        assert c.settings.event_payload_codecs == ()

    def test_secret_string_is_stored_as_one_element_list(self):
        c = Citry(secret="k1")  # noqa: S106 - a dummy test secret, not a credential
        assert c.settings.secret == ["k1"]

    def test_secret_list_is_stored_as_given(self):
        # The rotation form: the first entry signs, all entries verify.
        c = Citry(secret=["new-key", "old-key"])
        assert c.settings.secret == ["new-key", "old-key"]

    def test_secret_string_and_list_forms_are_equivalent(self):
        assert CitrySettings(secret="k1") == CitrySettings(secret=["k1"])  # noqa: S106 - a dummy test secret

    def test_secret_list_is_copied_at_construction(self):
        # The settings hold their own copy: mutating the caller's list after
        # construction must not change the frozen settings.
        keys = ["new-key", "old-key"]
        c = Citry(secret=keys)
        keys.append("rogue-key")
        assert c.settings.secret == ["new-key", "old-key"]

    def test_secret_list_is_copied_when_constructing_settings_directly(self):
        # The copy is made by CitrySettings itself, so direct construction is
        # covered too, not just the Citry(...) path.
        keys = ["k1"]
        settings = CitrySettings(secret=keys)
        keys.append("rogue-key")
        assert settings.secret == ["k1"]

    def test_event_result_resolvers_ride_the_constructor(self):
        # Two sentinels, so the assertion locks identity and order (resolvers
        # are tried in order; the first one to claim a value wins).
        first, second = object(), object()
        c = Citry(event_result_resolvers=[first, second])
        assert c.settings.event_result_resolvers == (first, second)

    def test_event_payload_codecs_ride_the_constructor(self):
        # Two sentinels, so the assertion locks identity and order (codecs
        # are checked in the given order, before the built-in ones).
        first, second = object(), object()
        c = Citry(event_payload_codecs=[first, second])
        assert c.settings.event_payload_codecs == (first, second)

    def test_event_result_resolvers_copied_into_a_tuple_at_direct_construction(self):
        # CitrySettings itself makes the tuple, so direct construction is
        # covered too, not just the Citry(...) path: the stored value is a
        # tuple (matching the field type), and mutating the caller's list
        # afterwards cannot change the frozen settings.
        first, second = object(), object()
        resolvers = [first, second]
        settings = CitrySettings(event_result_resolvers=resolvers)
        resolvers.append(object())
        assert isinstance(settings.event_result_resolvers, tuple)
        assert settings.event_result_resolvers == (first, second)

    def test_event_payload_codecs_copied_into_a_tuple_at_direct_construction(self):
        # The same guarantee for codecs: direct construction stores its own
        # tuple, not the caller's list.
        first, second = object(), object()
        codecs = [first, second]
        settings = CitrySettings(event_payload_codecs=codecs)
        codecs.append(object())
        assert isinstance(settings.event_payload_codecs, tuple)
        assert settings.event_payload_codecs == (first, second)

    def test_settings_reject_assignment(self):
        c = Citry(secret="k1", event_result_resolvers=[object()], event_payload_codecs=[object()])  # noqa: S106 - dummy test secret
        for field_name, value in [
            ("secret", "other"),
            ("event_result_resolvers", ()),
            ("event_payload_codecs", ()),
        ]:
            with pytest.raises(FrozenInstanceError):
                setattr(c.settings, field_name, value)


class TestSettingsNormalizedAtDirectConstruction:
    # CitrySettings.__post_init__ normalizes every field, so a direct
    # CitrySettings(...) is as safe and immutable as one built through Citry(...):
    # each stored value is the annotated shape and holds no reference the caller
    # can still mutate after construction.

    def test_extensions_copied_into_a_tuple(self):
        # Import strings stand in for extension specs (CitrySettings stores them;
        # ExtensionManager is what builds them). The stored value is a tuple, and
        # appending to the caller's list afterwards cannot change it.
        specs = ["path.To.Ext", "other.Ext"]
        settings = CitrySettings(extensions=specs)
        specs.append("rogue.Ext")
        assert isinstance(settings.extensions, tuple)
        assert settings.extensions == ("path.To.Ext", "other.Ext")

    def test_dirs_coerced_to_paths_and_copied_into_a_tuple(self, tmp_path):
        # str entries become Path, stored as a tuple; mutating the caller's list
        # afterwards cannot change the frozen settings.
        sub = tmp_path / "components"
        dirs = [str(tmp_path), str(sub)]
        settings = CitrySettings(dirs=dirs)
        dirs.append(str(tmp_path / "rogue"))
        assert isinstance(settings.dirs, tuple)
        assert settings.dirs == (tmp_path, sub)
        assert all(isinstance(d, Path) for d in settings.dirs)

    def test_dirs_reject_relative_paths(self):
        # The same absolute-path contract Citry(...) enforces, now guaranteed on
        # the direct construction path too.
        with pytest.raises(ValueError, match="absolute"):
            CitrySettings(dirs=["relative/path"])

    def test_dirs_absolute_handling_matches_citry(self, tmp_path):
        # Both paths coerce and validate dirs identically: an absolute str lands
        # as the same Path tuple, and a relative entry is rejected either way.
        assert CitrySettings(dirs=[str(tmp_path)]).dirs == Citry(dirs=[str(tmp_path)]).settings.dirs
        with pytest.raises(ValueError, match="absolute"):
            Citry(dirs=["relative/path"])

    def test_extensions_defaults_copied_into_a_fresh_dict(self):
        # A fresh dict, so rebinding or adding keys on the caller's mapping
        # afterwards cannot change the frozen settings.
        defaults = {"view": {"ttl": 60}}
        settings = CitrySettings(extensions_defaults=defaults)
        defaults["view"] = {"ttl": 999}
        defaults["cache"] = {"ttl": 5}
        assert isinstance(settings.extensions_defaults, dict)
        assert settings.extensions_defaults == {"view": {"ttl": 60}}

    def test_template_globals_copied_into_a_fresh_dict(self):
        # A fresh dict, un-aliased from the caller's mapping.
        globals_seed = {"site_name": "acme"}
        settings = CitrySettings(template_globals=globals_seed)
        globals_seed["site_name"] = "evil"
        globals_seed["extra"] = 1
        assert isinstance(settings.template_globals, dict)
        assert settings.template_globals == {"site_name": "acme"}

    def test_citry_and_direct_settings_normalize_equally(self, tmp_path):
        # The invariant: for the same inputs, both construction paths produce
        # equal, fully normalized settings.
        class Marker(Extension):
            name = "marker"

        resolver, codec = object(), object()
        common = {
            "extensions": [Marker],
            "extensions_defaults": {"view": {"ttl": 60}},
            "dirs": [str(tmp_path)],
            "template_globals": {"site_name": "acme"},
            "secret": "k1",
            "event_result_resolvers": [resolver],
            "event_payload_codecs": [codec],
        }
        from_citry = Citry(**common).settings
        from_direct = CitrySettings(**common)
        assert from_citry == from_direct
