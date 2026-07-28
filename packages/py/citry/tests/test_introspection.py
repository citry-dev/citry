"""Tests for the component-introspection value model and schema adapter."""

from __future__ import annotations

import gc
import json
import math
import sys
import typing
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError, InitVar, dataclass, field, replace
from importlib import import_module
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from threading import Barrier, Event
from types import ModuleType
from typing import Annotated, Any, ClassVar, ForwardRef, Literal, NamedTuple, TypeVar
from weakref import ref

import pytest
from pydantic import BaseModel, Field
from pydantic.v1 import BaseModel as BaseModelV1
from pydantic.v1 import Field as FieldV1

from citry import (
    AssetInfo,
    Citry,
    CitryLifecycleInProgress,
    Component,
    ComponentAssets,
    ComponentCatalog,
    ComponentExtensionInfo,
    ComponentInfo,
    ComponentIntrospectionContext,
    ComponentIntrospectionError,
    ComponentSchemas,
    Extension,
    ExtensionVersion,
    FieldInfo,
    NotRegistered,
    SchemaInfo,
)
from citry._schema_introspection import (
    _format_annotation,
    _inspect_component_schemas,
    _inspect_schema_class,
)
from citry.util.misc import FieldSpec, get_fields

ABSENT_SCHEMA = SchemaInfo(kind="absent", declared_on=None, import_path=None, fields=())
NONE_ASSET = AssetInfo(
    kind="none",
    declared_on=None,
    owner_file=None,
    declared_path=None,
    resolution="not-applicable",
    resolved_path=None,
    searched_paths=(),
)


def _schemas(*, kwargs: SchemaInfo = ABSENT_SCHEMA) -> ComponentSchemas:
    return ComponentSchemas(
        kwargs=kwargs,
        slots=ABSENT_SCHEMA,
        template_data=ABSENT_SCHEMA,
        js_data=ABSENT_SCHEMA,
        css_data=ABSENT_SCHEMA,
    )


def _assets(*, template: AssetInfo = NONE_ASSET) -> ComponentAssets:
    return ComponentAssets(template=template, js=NONE_ASSET, css=NONE_ASSET)


def _component_info(
    engine_id: str,
    *,
    name: str = "card",
    class_id: str = "Card_a1b2c3",
    aliases: tuple[str, ...] = (),
    schemas: ComponentSchemas | None = None,
    assets: ComponentAssets | None = None,
    extensions: tuple[ComponentExtensionInfo, ...] = (),
) -> ComponentInfo:
    return ComponentInfo(
        class_id=class_id,
        engine_id=engine_id,
        definition_id=f"definition-{class_id}",
        name=name,
        aliases=aliases,
        class_name="Card",
        module="shop.card",
        qualname="Card",
        import_path="shop.card.Card",
        python_file=Path(__file__).resolve(),
        description="Žluťoučký card.",
        transparent=False,
        builtin=False,
        schemas=schemas or _schemas(),
        assets=assets or _assets(),
        extensions=extensions,
    )


def _reload_like_component(app: Citry, registry_name: str) -> type[Component]:
    return type(
        "ReloadedComponent",
        (Component,),
        {
            "__module__": __name__,
            "__qualname__": "ReloadedComponent",
            "citry": app,
            "name": registry_name,
            "template": """
                <p>x</p>
            """,
        },
    )


def _install_module(monkeypatch, module_name: str, python_file: Path) -> ModuleType:
    """Install one already-loaded module record with a real Python file path."""
    python_file.parent.mkdir(parents=True, exist_ok=True)
    python_file.write_text("# Introspection test module.\n")
    module = ModuleType(module_name)
    module.__file__ = str(python_file)
    monkeypatch.setitem(sys.modules, module_name, module)
    return module


class TestRuntimeIdentity:
    def test_engine_identity_is_stable_distinct_and_survives_clear(self):
        first = Citry(autodiscover=False)
        second = Citry(autodiscover=False)

        original = first.engine_id
        first.clear()

        assert first.engine_id == original
        assert first.engine_id != second.engine_id

        first.engine_id = original
        first._engine_id = original
        with pytest.raises(AttributeError, match="engine identity"):
            first.engine_id = "replacement"
        with pytest.raises(AttributeError, match="engine identity"):
            first._engine_id = "replacement"
        with pytest.raises(AttributeError, match="engine identity"):
            del first.engine_id
        with pytest.raises(AttributeError, match="engine identity"):
            del first._engine_id

    def test_citry_instances_reject_shallow_and_deep_copying(self):
        app = Citry(autodiscover=False)

        with pytest.raises(TypeError, match="cannot be copied"):
            copy(app)
        with pytest.raises(TypeError, match="cannot be copied"):
            deepcopy(app)

    def test_definition_identity_is_own_stable_and_immutable(self):
        app = Citry(autodiscover=False)

        class Card(Component):
            citry = app
            template = """
                <p>x</p>
            """

        class Child(Card):
            pass

        original = Card.definition_id
        class_id = Card.class_id
        assert Card.definition_id == original
        assert Child.definition_id != original
        assert "_definition_id" in Card.__dict__
        assert "_definition_id" in Child.__dict__

        Card.definition_id = original
        Card.class_id = class_id
        Card._class_id = class_id
        with pytest.raises(AttributeError, match="definition identity"):
            Card.definition_id = "replacement"
        with pytest.raises(AttributeError, match="definition identity"):
            del Card.definition_id
        with pytest.raises(AttributeError, match="class identity"):
            Card.class_id = "replacement"
        with pytest.raises(AttributeError, match="class identity"):
            Card._class_id = "replacement"
        with pytest.raises(AttributeError, match="class identity"):
            del Card.class_id
        with pytest.raises(AttributeError, match="class identity"):
            del Card._class_id

    @pytest.mark.parametrize("field_name", ["class_id", "_class_id", "definition_id", "_definition_id"])
    def test_component_class_body_cannot_preseed_identity_fields(self, field_name):
        app = Citry(autodiscover=False)

        with pytest.raises(ValueError, match="read-only identity"):
            type("ForgedCard", (Component,), {"citry": app, field_name: "forged"})

    def test_definition_identity_exists_before_class_created_hook(self):
        seen: list[tuple[str, str]] = []

        class IdentityExtension(Extension):
            name = "identity"

            def on_component_class_created(self, ctx):
                seen.append((ctx.citry.engine_id, ctx.component_class.definition_id))

        app = Citry(extensions=[IdentityExtension], autodiscover=False)

        class Card(Component):
            citry = app
            template = """
                <p>x</p>
            """

        assert seen == [(app.engine_id, Card.definition_id)]

    def test_class_created_hook_cannot_forge_lazy_class_identity(self):
        errors: list[AttributeError] = []

        class IdentityExtension(Extension):
            name = "identity"

            def on_component_class_created(self, ctx):
                try:
                    ctx.component_class._class_id = "forged"
                except AttributeError as err:
                    errors.append(err)

        app = Citry(extensions=[IdentityExtension], autodiscover=False)

        class Card(Component):
            citry = app

        assert len(errors) == 1
        assert "class identity" in str(errors[0])
        assert Card.class_id != "forged"
        assert app.get_component_by_class_id(Card.class_id) is Card

    def test_alias_and_reregistration_preserve_definition_identity(self):
        app = Citry(autodiscover=False)

        class Card(Component):
            citry = app
            template = """
                <p>x</p>
            """

        definition_id = Card.definition_id
        app.register(Card, "product-card")
        app.unregister(Card)
        app.register(Card)

        assert Card.definition_id == definition_id

    def test_hot_replacement_keeps_class_id_and_changes_definition_id(self):
        app = Citry(autodiscover=False)
        original = _reload_like_component(app, "original")
        retained = (app.engine_id, original.class_id, original.definition_id)

        app.unregister(original)
        replacement = _reload_like_component(app, "replacement")

        assert replacement.class_id == retained[1]
        assert replacement.definition_id != retained[2]
        assert app.get_component_by_class_id(retained[1]) is replacement
        assert (app.engine_id, replacement.class_id, replacement.definition_id) != retained

    def test_same_path_definitions_in_two_engines_have_distinct_runtime_tokens(self):
        first = Citry(autodiscover=False)
        second = Citry(autodiscover=False)
        first_card = _reload_like_component(first, "first")
        second_card = _reload_like_component(second, "second")

        assert first_card.class_id == second_card.class_id
        assert first.engine_id != second.engine_id
        assert first_card.definition_id != second_card.definition_id

    def test_runtime_token_allocator_is_unique_under_concurrency(self):
        with ThreadPoolExecutor(max_workers=8) as executor:
            engine_ids = list(executor.map(lambda _index: Citry(autodiscover=False).engine_id, range(100)))

        assert len(engine_ids) == len(set(engine_ids))

    def test_definition_identity_does_not_retain_unregistered_class(self):
        app = Citry(autodiscover=False)

        class Card(Component):
            citry = app
            template = """
                <p>x</p>
            """

        card_ref = ref(Card)
        assert Card.definition_id
        app.unregister(Card)
        del Card
        gc.collect()

        assert card_ref() is None


class TestFrozenValueModel:
    def test_records_are_frozen_slotted_values(self):
        assert not hasattr(ABSENT_SCHEMA, "__dict__")
        with pytest.raises(FrozenInstanceError):
            ABSENT_SCHEMA.kind = "opaque"

    def test_public_groups_reject_non_record_members(self):
        with pytest.raises(TypeError, match="kwargs"):
            ComponentSchemas(
                kwargs="bad",
                slots=ABSENT_SCHEMA,
                template_data=ABSENT_SCHEMA,
                js_data=ABSENT_SCHEMA,
                css_data=ABSENT_SCHEMA,
            )
        with pytest.raises(TypeError, match="template"):
            ComponentAssets(template="bad", js=NONE_ASSET, css=NONE_ASSET)

    def test_literal_state_fields_reject_string_subclasses(self):
        class StringSubclass(str):
            __slots__ = ()

        with pytest.raises(ValueError, match="schema kind"):
            SchemaInfo(kind=StringSubclass("absent"), declared_on=None, import_path=None, fields=())
        with pytest.raises(ValueError, match="field type fidelity"):
            FieldInfo(
                name="title",
                required=True,
                type_display="str",
                type_fidelity=StringSubclass("normalized"),
                default_kind="missing",
                default_value_state="not-applicable",
                default_value=None,
                description=None,
            )
        with pytest.raises(ValueError, match="field default kind"):
            FieldInfo(
                name="title",
                required=True,
                type_display="str",
                type_fidelity="normalized",
                default_kind=StringSubclass("missing"),
                default_value_state="not-applicable",
                default_value=None,
                description=None,
            )
        with pytest.raises(ValueError, match="field default value state"):
            FieldInfo(
                name="title",
                required=True,
                type_display="str",
                type_fidelity="normalized",
                default_kind="missing",
                default_value_state=StringSubclass("not-applicable"),
                default_value=None,
                description=None,
            )
        with pytest.raises(ValueError, match="asset kind"):
            AssetInfo(
                kind=StringSubclass("none"),
                declared_on=None,
                owner_file=None,
                declared_path=None,
                resolution="not-applicable",
                resolved_path=None,
                searched_paths=(),
            )
        with pytest.raises(ValueError, match="asset resolution"):
            AssetInfo(
                kind="none",
                declared_on=None,
                owner_file=None,
                declared_path=None,
                resolution=StringSubclass("not-applicable"),
                resolved_path=None,
                searched_paths=(),
            )

    @pytest.mark.parametrize(
        ("changes", "message"),
        [
            ({"required": False}, "required exactly"),
            ({"type_display": None}, "normalized field type"),
            ({"type_display": 0, "type_fidelity": "unavailable"}, "unavailable type"),
            ({"default_value_state": "available"}, "not-applicable"),
        ],
    )
    def test_field_info_rejects_contradictory_states(self, changes, message):
        values = {
            "name": "title",
            "required": True,
            "type_display": "str",
            "type_fidelity": "normalized",
            "default_kind": "missing",
            "default_value_state": "not-applicable",
            "default_value": None,
            "description": None,
        }
        values.update(changes)
        with pytest.raises(ValueError, match=message):
            FieldInfo(**values)

    def test_available_null_is_distinct_from_omitted_value(self):
        available = FieldInfo(
            name="value",
            required=False,
            type_display="Any",
            type_fidelity="normalized",
            default_kind="value",
            default_value_state="available",
            default_value=None,
            description=None,
        )
        omitted = FieldInfo(
            name="value",
            required=False,
            type_display="Any",
            type_fidelity="normalized",
            default_kind="value",
            default_value_state="omitted",
            default_value=None,
            description=None,
        )

        assert available.default_value is None
        assert available.default_value_state != omitted.default_value_state

    def test_available_default_is_defensively_copied_and_frozen(self):
        raw = {"z": [1, 2], "a": {"ok": True}}
        info = FieldInfo(
            name="config",
            required=False,
            type_display="dict[str, Any]",
            type_fidelity="normalized",
            default_kind="value",
            default_value_state="available",
            default_value=raw,
            description=None,
        )
        raw["z"].append(3)
        raw["a"]["ok"] = False

        component = _component_info(
            "engine",
            schemas=_schemas(
                kwargs=SchemaInfo(
                    kind="fields",
                    declared_on="shop.card.Card",
                    import_path="shop.card.Card.Kwargs",
                    fields=(info,),
                )
            ),
        )
        catalog = ComponentCatalog(
            schema_version=1,
            citry_version="1.0.0",
            engine_id="engine",
            extension_versions=(),
            components=(component,),
        )

        value = catalog.to_dict()["components"][0]["schemas"]["kwargs"]["fields"][0]["default_value"]
        assert value == {"a": {"ok": True}, "z": [1, 2]}

    def test_public_json_record_constructors_accept_ordinary_dicts_and_lists(self):
        field_info = FieldInfo(
            name="config",
            required=False,
            type_display="dict[str, list[int]]",
            type_fidelity="normalized",
            default_kind="value",
            default_value_state="available",
            default_value={"values": [1, 2]},
            description=None,
        )
        extension_info = ComponentExtensionInfo(
            name="example",
            introspection_version=1,
            data={"values": [1, 2]},
        )

        assert tuple(field_info.default_value) == (("values", (1, 2)),)
        assert tuple(extension_info.data) == (("values", (1, 2)),)

    @pytest.mark.parametrize(
        ("left", "right"),
        [
            (True, 1),
            (1, 1.0),
            (0.0, -0.0),
            ({"x": 1}, [["x", 1]]),
            ([True, {"x": 1}], [1, [["x", 1]]]),
        ],
    )
    def test_frozen_json_equality_preserves_json_types(self, left, right):
        def make_info(value):
            return FieldInfo(
                name="value",
                required=False,
                type_display=None,
                type_fidelity="unavailable",
                default_kind="value",
                default_value_state="available",
                default_value=value,
                description=None,
            )

        left_info = make_info(left)
        right_info = make_info(right)

        assert left_info != right_info
        assert right_info != left_info
        assert len({left_info, right_info}) == 2

    def test_extension_json_equality_distinguishes_objects_from_pair_arrays(self):
        object_info = ComponentExtensionInfo(name="example", introspection_version=1, data={"value": {"x": 1}})
        array_info = ComponentExtensionInfo(
            name="example",
            introspection_version=1,
            data={"value": [["x", 1]]},
        )

        assert object_info != array_info
        assert array_info != object_info
        assert len({object_info, array_info}) == 2

    @pytest.mark.parametrize(
        "value",
        [2**53, -(2**53), math.nan, math.inf, object(), {1: "bad"}],
    )
    def test_available_default_rejects_non_portable_value(self, value):
        with pytest.raises(ValueError, match="portable JSON"):
            FieldInfo(
                name="value",
                required=False,
                type_display=None,
                type_fidelity="unavailable",
                default_kind="value",
                default_value_state="available",
                default_value=value,
                description=None,
            )

    @pytest.mark.parametrize("value", [2**53 - 1, -(2**53 - 1)])
    def test_available_default_accepts_safe_integer_boundaries(self, value):
        info = FieldInfo(
            name="value",
            required=False,
            type_display="int",
            type_fidelity="normalized",
            default_kind="value",
            default_value_state="available",
            default_value=value,
            description=None,
        )

        assert info.default_value == value

    def test_available_default_rejects_cycles_but_accepts_shared_children(self):
        cycle = []
        cycle.append(cycle)
        with pytest.raises(ValueError, match="portable JSON"):
            FieldInfo(
                name="cycle",
                required=False,
                type_display=None,
                type_fidelity="unavailable",
                default_kind="value",
                default_value_state="available",
                default_value=cycle,
                description=None,
            )

        child = [1]
        shared = FieldInfo(
            name="shared",
            required=False,
            type_display=None,
            type_fidelity="unavailable",
            default_kind="value",
            default_value_state="available",
            default_value=[child, child],
            description=None,
        )
        assert shared.default_value == ((1,), (1,))

    @pytest.mark.parametrize("value", ["\ud800", {"\ud800": "x"}, {"key": "\udfff"}])
    def test_portable_json_rejects_unpaired_surrogates(self, value):
        with pytest.raises(ValueError, match="portable JSON"):
            FieldInfo(
                name="value",
                required=False,
                type_display=None,
                type_fidelity="unavailable",
                default_kind="value",
                default_value_state="available",
                default_value=value,
                description=None,
            )

    def test_catalog_record_strings_reject_unpaired_surrogates(self):
        with pytest.raises(ValueError, match="surrogate"):
            ExtensionVersion("\ud800", 1)
        with pytest.raises(ValueError, match="surrogate"):
            FieldInfo(
                name="value",
                required=False,
                type_display="\ud800",
                type_fidelity="normalized",
                default_kind="value",
                default_value_state="omitted",
                default_value=None,
                description=None,
            )

    @pytest.mark.parametrize(
        ("changes", "error", "message"),
        [
            ({"required": 1}, TypeError, "required must be a bool"),
            ({"description": object()}, TypeError, "description must be a string"),
            (
                {
                    "required": False,
                    "default_kind": "value",
                    "default_value_state": "not-applicable",
                },
                ValueError,
                "value default must be omitted, available, or unsupported",
            ),
            (
                {
                    "required": False,
                    "default_kind": "value",
                    "default_value_state": "omitted",
                    "default_value": "unexpected",
                },
                ValueError,
                "carry no value",
            ),
            (
                {
                    "required": False,
                    "default_kind": "value",
                    "default_value_state": "unsupported",
                    "default_value": "unexpected",
                },
                ValueError,
                "carry no value",
            ),
        ],
    )
    def test_field_info_rejects_invalid_public_field_states(self, changes, error, message):
        values = {
            "name": "title",
            "required": True,
            "type_display": "str",
            "type_fidelity": "normalized",
            "default_kind": "missing",
            "default_value_state": "not-applicable",
            "default_value": None,
            "description": None,
        }
        values.update(changes)

        with pytest.raises(error, match=message):
            FieldInfo(**values)

    def test_deep_portable_default_reports_a_value_error(self):
        value = None
        for _ in range(1_500):
            value = [value]

        with pytest.raises(ValueError, match="portable JSON"):
            FieldInfo(
                name="deep",
                required=False,
                type_display=None,
                type_fidelity="unavailable",
                default_kind="value",
                default_value_state="available",
                default_value=value,
                description=None,
            )

    def test_frozen_record_equality_and_hashing_are_type_sensitive(self):
        field_info = FieldInfo(
            name="config",
            required=False,
            type_display=None,
            type_fidelity="unavailable",
            default_kind="value",
            default_value_state="available",
            default_value={"values": [1, 2]},
            description=None,
        )
        same_field = replace(field_info)
        extension_info = ComponentExtensionInfo(
            name="example",
            introspection_version=1,
            data={"values": [1, 2]},
        )
        same_extension = ComponentExtensionInfo(
            name="example",
            introspection_version=1,
            data=extension_info.data,
        )

        assert field_info == same_field
        assert hash(field_info) == hash(same_field)
        assert field_info != object()
        assert extension_info == same_extension
        assert hash(extension_info) == hash(same_extension)
        assert extension_info != object()
        assert extension_info.data != tuple(extension_info.data)
        assert hash(extension_info.data) == hash(same_extension.data)

    @pytest.mark.parametrize(
        ("fields", "message"),
        [
            ([], "must be a tuple"),
            (("not-a-field",), "only FieldInfo"),
        ],
    )
    def test_schema_info_rejects_invalid_field_containers(self, fields, message):
        with pytest.raises(TypeError, match=message):
            SchemaInfo(
                kind="fields",
                declared_on="shop.Card",
                import_path="shop.Card.Kwargs",
                fields=fields,
            )

    def test_schema_info_rejects_duplicate_field_names(self):
        field_info = FieldInfo(
            name="value",
            required=True,
            type_display="str",
            type_fidelity="normalized",
            default_kind="missing",
            default_value_state="not-applicable",
            default_value=None,
            description=None,
        )

        with pytest.raises(ValueError, match="field names must be unique"):
            SchemaInfo(
                kind="fields",
                declared_on="shop.Card",
                import_path="shop.Card.Kwargs",
                fields=(field_info, field_info),
            )

    @pytest.mark.parametrize(
        "schema",
        [
            SchemaInfo(kind="absent", declared_on=None, import_path=None, fields=()),
            SchemaInfo(kind="absent", declared_on="shop.Mixin", import_path=None, fields=()),
            SchemaInfo(kind="fields", declared_on="shop.Card", import_path="shop.Card.Kwargs", fields=()),
            SchemaInfo(kind="opaque", declared_on="shop.Card", import_path="shop.Custom", fields=()),
        ],
    )
    def test_schema_info_accepts_every_valid_kind(self, schema):
        assert schema.kind in {"absent", "fields", "opaque"}

    def test_schema_info_rejects_invalid_state_combinations(self):
        field_info = FieldInfo(
            name="x",
            required=True,
            type_display="int",
            type_fidelity="normalized",
            default_kind="missing",
            default_value_state="not-applicable",
            default_value=None,
            description=None,
        )
        with pytest.raises(ValueError, match="absent schema"):
            SchemaInfo(kind="absent", declared_on=None, import_path="shop.Schema", fields=())
        with pytest.raises(ValueError, match="absent schema"):
            SchemaInfo(kind="absent", declared_on=None, import_path=None, fields=(field_info,))
        with pytest.raises(ValueError, match="opaque schema"):
            SchemaInfo(
                kind="opaque",
                declared_on="shop.Card",
                import_path="shop.Schema",
                fields=(field_info,),
            )

    @pytest.mark.parametrize("kind", ["fields", "opaque"])
    @pytest.mark.parametrize(
        ("declared_on", "import_path"),
        [
            (None, "shop.Schema"),
            ("shop.Card", None),
        ],
    )
    def test_declared_schema_info_requires_owner_and_schema_paths(self, kind, declared_on, import_path):
        with pytest.raises(ValueError, match="non-empty string"):
            SchemaInfo(kind=kind, declared_on=declared_on, import_path=import_path, fields=())

    def test_asset_info_accepts_all_file_resolution_states(self, tmp_path):
        declared_on = f"{__name__}.Card"
        candidate = (tmp_path / "card.html").resolve()
        common = {
            "kind": "file",
            "declared_on": declared_on,
            "owner_file": Path(__file__).resolve(),
            "declared_path": "card.html",
        }

        not_requested = AssetInfo(**common, resolution="not-requested", resolved_path=None, searched_paths=())
        resolved = AssetInfo(
            **common,
            resolution="resolved",
            resolved_path=candidate,
            searched_paths=(candidate,),
        )
        missing = AssetInfo(
            **common,
            resolution="missing",
            resolved_path=None,
            searched_paths=(candidate,),
        )
        unavailable = AssetInfo(
            kind="file",
            declared_on=declared_on,
            owner_file=None,
            declared_path="card.html",
            resolution="unavailable",
            resolved_path=None,
            searched_paths=(),
        )

        assert {not_requested.resolution, resolved.resolution, missing.resolution, unavailable.resolution} == {
            "not-requested",
            "resolved",
            "missing",
            "unavailable",
        }

    def test_asset_info_rejects_contradictory_and_relative_paths(self):
        with pytest.raises(ValueError, match=r"absolute pathlib\.Path"):
            AssetInfo(
                kind="inline",
                declared_on="shop.Card",
                owner_file=Path("card.py"),
                declared_path=None,
                resolution="not-applicable",
                resolved_path=None,
                searched_paths=(),
            )
        with pytest.raises(ValueError, match="winning path"):
            AssetInfo(
                kind="file",
                declared_on="shop.Card",
                owner_file=None,
                declared_path="card.html",
                resolution="resolved",
                resolved_path=(Path.cwd() / "missing-card.html").resolve(),
                searched_paths=((Path.cwd() / "missing-other.html").resolve(),),
            )
        with pytest.raises(ValueError, match=r"searched_paths entry must be an absolute pathlib\.Path"):
            AssetInfo(
                kind="file",
                declared_on="shop.Card",
                owner_file=None,
                declared_path="card.html",
                resolution="missing",
                resolved_path=None,
                searched_paths=(None,),
            )
        with pytest.raises(ValueError, match="relative"):
            AssetInfo(
                kind="file",
                declared_on="shop.Card",
                owner_file=Path(__file__).resolve(),
                declared_path="/absolute/card.html",
                resolution="unavailable",
                resolved_path=None,
                searched_paths=(),
            )

    @pytest.mark.parametrize(
        ("changes", "error", "message"),
        [
            ({"searched_paths": []}, TypeError, "searched_paths must be a tuple"),
            ({"kind": "none", "declared_path": "card.html"}, ValueError, "absent asset"),
            (
                {"kind": "none", "resolved_path": (Path.cwd() / "card.html").resolve()},
                ValueError,
                "absent asset",
            ),
            (
                {"kind": "none", "searched_paths": ((Path.cwd() / "card.html").resolve(),)},
                ValueError,
                "absent asset",
            ),
            ({"kind": "none", "resolution": "not-requested"}, ValueError, "absent asset"),
            ({"kind": "none", "owner_file": Path(__file__).resolve()}, ValueError, "owner file"),
            ({"kind": "inline"}, ValueError, "declared_on must be a non-empty string"),
            (
                {
                    "kind": "inline",
                    "declared_on": "shop.Card",
                    "declared_path": "card.html",
                },
                ValueError,
                "inline asset",
            ),
            (
                {
                    "kind": "inline",
                    "declared_on": "shop.Card",
                    "resolution": "missing",
                },
                ValueError,
                "inline asset",
            ),
            (
                {
                    "kind": "inline",
                    "declared_on": "shop.Card",
                    "resolved_path": (Path.cwd() / "card.html").resolve(),
                },
                ValueError,
                "inline asset",
            ),
            (
                {
                    "kind": "inline",
                    "declared_on": "shop.Card",
                    "searched_paths": ((Path.cwd() / "card.html").resolve(),),
                },
                ValueError,
                "inline asset",
            ),
            (
                {
                    "kind": "file",
                    "declared_path": "card.html",
                    "resolution": "not-requested",
                },
                ValueError,
                "declared_on must be a non-empty string",
            ),
            (
                {
                    "kind": "file",
                    "declared_on": "shop.Card",
                    "resolution": "not-requested",
                },
                ValueError,
                "declared_path must be a non-empty string",
            ),
            (
                {
                    "kind": "file",
                    "declared_on": "shop.Card",
                    "declared_path": "card.html",
                    "resolution": "not-requested",
                    "searched_paths": ((Path.cwd() / "card.html").resolve(),),
                },
                ValueError,
                "unresolved file asset",
            ),
            (
                {
                    "kind": "file",
                    "declared_on": "shop.Card",
                    "declared_path": "card.html",
                    "resolution": "not-requested",
                    "resolved_path": (Path.cwd() / "card.html").resolve(),
                },
                ValueError,
                "unresolved file asset",
            ),
            (
                {
                    "kind": "file",
                    "declared_on": "shop.Card",
                    "declared_path": "card.html",
                    "resolution": "missing",
                },
                ValueError,
                "missing file asset",
            ),
            (
                {
                    "kind": "file",
                    "declared_on": "shop.Card",
                    "declared_path": "card.html",
                    "resolution": "missing",
                    "resolved_path": (Path.cwd() / "card.html").resolve(),
                    "searched_paths": ((Path.cwd() / "card.html").resolve(),),
                },
                ValueError,
                "missing file asset",
            ),
            (
                {
                    "kind": "file",
                    "declared_on": "shop.Card",
                    "owner_file": Path(__file__).resolve(),
                    "declared_path": "card.html",
                    "resolution": "unavailable",
                },
                ValueError,
                "unavailable file asset",
            ),
            (
                {
                    "kind": "file",
                    "declared_on": "shop.Card",
                    "declared_path": "card.html",
                    "resolution": "unavailable",
                    "resolved_path": (Path.cwd() / "card.html").resolve(),
                },
                ValueError,
                "unavailable file asset",
            ),
            (
                {
                    "kind": "file",
                    "declared_on": "shop.Card",
                    "declared_path": "card.html",
                    "resolution": "unavailable",
                    "searched_paths": ((Path.cwd() / "card.html").resolve(),),
                },
                ValueError,
                "unavailable file asset",
            ),
            (
                {
                    "kind": "file",
                    "declared_on": "shop.Card",
                    "declared_path": "card.html",
                    "resolution": "missing",
                    "searched_paths": (Path("card.html"),),
                },
                ValueError,
                "absolute pathlib.Path",
            ),
            (
                {
                    "kind": "file",
                    "declared_on": "shop.Card",
                    "declared_path": "card.html",
                },
                ValueError,
                "Invalid resolution",
            ),
        ],
    )
    def test_asset_info_rejects_remaining_invalid_state_shapes(self, changes, error, message):
        values = {
            "kind": "none",
            "declared_on": None,
            "owner_file": None,
            "declared_path": None,
            "resolution": "not-applicable",
            "resolved_path": None,
            "searched_paths": (),
        }
        values.update(changes)

        with pytest.raises(error, match=message):
            AssetInfo(**values)

    @pytest.mark.parametrize(
        ("factory", "message"),
        [
            (lambda: ExtensionVersion("", 1), "non-empty string"),
            (lambda: ExtensionVersion(1, 1), "non-empty string"),
            (lambda: ExtensionVersion(name="example", introspection_version=True), "positive integer"),
            (lambda: ExtensionVersion("example", 0), "positive integer"),
            (lambda: ExtensionVersion("example", -1), "positive integer"),
            (lambda: ExtensionVersion("example", 1.0), "positive integer"),
            (lambda: ComponentExtensionInfo("", 1, {}), "non-empty string"),
            (lambda: ComponentExtensionInfo(1, 1, {}), "non-empty string"),
            (
                lambda: ComponentExtensionInfo(name="example", introspection_version=True, data={}),
                "positive integer",
            ),
            (lambda: ComponentExtensionInfo("example", -1, {}), "positive integer"),
            (lambda: ComponentExtensionInfo("example", 1.0, {}), "positive integer"),
            (lambda: ComponentExtensionInfo("example", 1, []), "exact built-in dict"),
        ],
    )
    def test_extension_records_reject_invalid_identity_version_and_data(self, factory, message):
        with pytest.raises(ValueError, match=message):
            factory()

    @pytest.mark.parametrize(
        ("changes", "error", "message"),
        [
            ({"aliases": []}, TypeError, "aliases must be a tuple"),
            ({"extensions": []}, TypeError, "extensions must be a tuple"),
            ({"aliases": ("",)}, ValueError, "non-empty strings"),
            ({"aliases": ("alias", "alias")}, ValueError, "unique, sorted"),
            ({"aliases": ("zeta", "alpha")}, ValueError, "unique, sorted"),
            ({"aliases": ("card",)}, ValueError, "exclude the primary name"),
            ({"transparent": 1}, TypeError, "must be bool values"),
            ({"builtin": 1}, TypeError, "must be bool values"),
            ({"schemas": "bad"}, TypeError, "introspection records"),
            ({"assets": "bad"}, TypeError, "introspection records"),
            ({"extensions": ("bad",)}, TypeError, "ComponentExtensionInfo values"),
        ],
    )
    def test_component_info_rejects_invalid_public_fields(self, changes, error, message):
        with pytest.raises(error, match=message):
            replace(_component_info("engine"), **changes)

    def test_component_info_rejects_unsorted_extension_metadata(self):
        extensions = (
            ComponentExtensionInfo("zeta", 1, {}),
            ComponentExtensionInfo("alpha", 1, {}),
        )

        with pytest.raises(ValueError, match="unique and sorted"):
            replace(_component_info("engine"), extensions=extensions)

        duplicate = ComponentExtensionInfo("example", 1, {})
        with pytest.raises(ValueError, match="unique and sorted"):
            replace(_component_info("engine"), extensions=(duplicate, duplicate))

    @pytest.mark.parametrize("field_name", ["class_name", "module", "qualname", "import_path", "description"])
    def test_component_info_optional_text_fields_reject_non_strings(self, field_name):
        with pytest.raises(TypeError, match=rf"{field_name} must be a string or None"):
            replace(_component_info("engine"), **{field_name: 1})

    @pytest.mark.parametrize("indent", [True, "2", 1.5])
    def test_catalog_json_rejects_non_integer_indentation(self, indent):
        catalog = ComponentCatalog(
            schema_version=1,
            citry_version="1.0.0",
            engine_id="engine",
            extension_versions=(),
            components=(),
        )

        with pytest.raises(TypeError, match="indent must be an integer or None"):
            catalog.to_json(indent=indent)

    def test_catalog_json_rejects_negative_indentation(self):
        catalog = ComponentCatalog(
            schema_version=1,
            citry_version="1.0.0",
            engine_id="engine",
            extension_versions=(),
            components=(),
        )

        with pytest.raises(ValueError, match="indent cannot be negative"):
            catalog.to_json(indent=-1)

    @pytest.mark.parametrize(
        ("changes", "error", "message"),
        [
            ({"schema_version": True}, ValueError, "schema_version"),
            ({"schema_version": 2}, ValueError, "schema_version"),
            ({"citry_version": ""}, ValueError, "non-empty string"),
            ({"engine_id": ""}, ValueError, "non-empty string"),
            ({"extension_versions": []}, TypeError, "must be a tuple"),
            ({"components": []}, TypeError, "must be a tuple"),
            ({"extension_versions": ("bad",)}, TypeError, "ExtensionVersion values"),
            ({"components": ("bad",)}, TypeError, "ComponentInfo values"),
        ],
    )
    def test_component_catalog_rejects_invalid_envelope_fields(self, changes, error, message):
        values = {
            "schema_version": 1,
            "citry_version": "1.0.0",
            "engine_id": "engine",
            "extension_versions": (),
            "components": (),
        }
        values.update(changes)

        with pytest.raises(error, match=message):
            ComponentCatalog(**values)

    def test_component_catalog_rejects_unsorted_extension_versions(self):
        with pytest.raises(ValueError, match="unique and sorted"):
            ComponentCatalog(
                schema_version=1,
                citry_version="1.0.0",
                engine_id="engine",
                extension_versions=(ExtensionVersion("zeta", 1), ExtensionVersion("alpha", 1)),
                components=(),
            )

        duplicate = ExtensionVersion("example", 1)
        with pytest.raises(ValueError, match="unique and sorted"):
            ComponentCatalog(
                schema_version=1,
                citry_version="1.0.0",
                engine_id="engine",
                extension_versions=(duplicate, duplicate),
                components=(),
            )

    def test_component_catalog_rejects_cross_record_inconsistencies(self):
        first = _component_info("engine", name="alpha", class_id="Alpha_a1b2c3")

        with pytest.raises(ValueError, match="belong to the catalog's engine"):
            ComponentCatalog(1, "1.0.0", "other", (), (first,))

        duplicate_definition = replace(
            _component_info("engine", name="beta", class_id="Beta_a1b2c3"),
            definition_id=first.definition_id,
        )
        with pytest.raises(ValueError, match="definition IDs"):
            ComponentCatalog(1, "1.0.0", "engine", (), (first, duplicate_definition))

        beta = _component_info("engine", name="beta", class_id="Beta_a1b2c3")
        with pytest.raises(ValueError, match="canonical order"):
            ComponentCatalog(1, "1.0.0", "engine", (), (beta, first))

        extension = ComponentExtensionInfo("example", 2, {})
        extended = replace(first, extensions=(extension,))
        with pytest.raises(ValueError, match="extension-version envelope"):
            ComponentCatalog(
                1,
                "1.0.0",
                "engine",
                (ExtensionVersion("example", 1),),
                (extended,),
            )

    def test_catalog_to_dict_and_json_match_complete_version_one_shape(self):
        field_info = FieldInfo(
            name="title",
            required=True,
            type_display="str",
            type_fidelity="normalized",
            default_kind="missing",
            default_value_state="not-applicable",
            default_value=None,
            description=None,
        )
        kwargs = SchemaInfo(
            kind="fields",
            declared_on="shop.card.Card",
            import_path="shop.card.Card.Kwargs",
            fields=(field_info,),
        )
        template = AssetInfo(
            kind="file",
            declared_on="shop.card.Card",
            owner_file=Path(__file__).resolve(),
            declared_path="card.html",
            resolution="not-requested",
            resolved_path=None,
            searched_paths=(),
        )
        extension = ComponentExtensionInfo(
            name="events",
            introspection_version=1,
            data={"handlers": [], "label": "Žluťoučký"},
        )
        component = _component_info(
            "engine",
            aliases=("product-card",),
            schemas=_schemas(kwargs=kwargs),
            assets=_assets(template=template),
            extensions=(extension,),
        )
        catalog = ComponentCatalog(
            schema_version=1,
            citry_version="1.0.0",
            engine_id="engine",
            extension_versions=(ExtensionVersion("events", 1),),
            components=(component,),
        )

        result = catalog.to_dict()
        assert result == {
            "schema_version": 1,
            "citry_version": "1.0.0",
            "engine_id": "engine",
            "extension_versions": {"events": 1},
            "components": [
                {
                    "class_id": "Card_a1b2c3",
                    "engine_id": "engine",
                    "definition_id": "definition-Card_a1b2c3",
                    "name": "card",
                    "aliases": ["product-card"],
                    "class_name": "Card",
                    "module": "shop.card",
                    "qualname": "Card",
                    "import_path": "shop.card.Card",
                    "python_file": Path(__file__).resolve().as_posix(),
                    "description": "Žluťoučký card.",
                    "transparent": False,
                    "builtin": False,
                    "schemas": {
                        "kwargs": {
                            "kind": "fields",
                            "declared_on": "shop.card.Card",
                            "import_path": "shop.card.Card.Kwargs",
                            "fields": [
                                {
                                    "name": "title",
                                    "required": True,
                                    "type_display": "str",
                                    "type_fidelity": "normalized",
                                    "default_kind": "missing",
                                    "default_value_state": "not-applicable",
                                    "default_value": None,
                                    "description": None,
                                },
                            ],
                        },
                        "slots": {"kind": "absent", "declared_on": None, "import_path": None, "fields": []},
                        "template_data": {
                            "kind": "absent",
                            "declared_on": None,
                            "import_path": None,
                            "fields": [],
                        },
                        "js_data": {"kind": "absent", "declared_on": None, "import_path": None, "fields": []},
                        "css_data": {"kind": "absent", "declared_on": None, "import_path": None, "fields": []},
                    },
                    "assets": {
                        "template": {
                            "kind": "file",
                            "declared_on": "shop.card.Card",
                            "owner_file": Path(__file__).resolve().as_posix(),
                            "declared_path": "card.html",
                            "resolution": "not-requested",
                            "resolved_path": None,
                            "searched_paths": [],
                        },
                        "js": {
                            "kind": "none",
                            "declared_on": None,
                            "owner_file": None,
                            "declared_path": None,
                            "resolution": "not-applicable",
                            "resolved_path": None,
                            "searched_paths": [],
                        },
                        "css": {
                            "kind": "none",
                            "declared_on": None,
                            "owner_file": None,
                            "declared_path": None,
                            "resolution": "not-applicable",
                            "resolved_path": None,
                            "searched_paths": [],
                        },
                    },
                    "extensions": {
                        "events": {
                            "introspection_version": 1,
                            "data": {"handlers": [], "label": "Žluťoučký"},
                        },
                    },
                },
            ],
        }
        assert catalog.to_json() == json.dumps(
            result,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        assert "Žluťoučký" in catalog.to_json(indent=2)
        assert catalog.to_json() == catalog.to_json()

    def test_to_dict_returns_fresh_mutable_trees(self):
        catalog = ComponentCatalog(
            schema_version=1,
            citry_version="1.0.0",
            engine_id="engine",
            extension_versions=(),
            components=(_component_info("engine"),),
        )
        first = catalog.to_dict()
        second = catalog.to_dict()

        first["components"].clear()
        assert len(second["components"]) == 1
        assert len(catalog.to_dict()["components"]) == 1

    def test_catalog_rejects_duplicate_runtime_and_registration_identities(self):
        first = _component_info("engine", name="alpha", class_id="Shared_a1b2c3")
        duplicate_class = _component_info("engine", name="beta", class_id="Shared_a1b2c3")
        with pytest.raises(ValueError, match="class IDs"):
            ComponentCatalog(
                schema_version=1,
                citry_version="1.0.0",
                engine_id="engine",
                extension_versions=(),
                components=(first, duplicate_class),
            )

        overlapping_alias = _component_info(
            "engine",
            name="beta",
            class_id="Beta_a1b2c3",
            aliases=("alpha",),
        )
        with pytest.raises(ValueError, match="registration names"):
            ComponentCatalog(
                schema_version=1,
                citry_version="1.0.0",
                engine_id="engine",
                extension_versions=(),
                components=(first, overlapping_alias),
            )


class TestSchemaAdapter:
    def test_all_roles_distinguish_framework_absence_explicit_none_fields_and_opaque(self):
        app = Citry(autodiscover=False)

        class OpaqueBase:
            pass

        class OpaqueSchema(OpaqueBase):
            value: str

        class Card(Component):
            citry = app
            Kwargs = None

            class Slots:
                body: str

            TemplateData = OpaqueSchema

        schemas = _inspect_component_schemas(Card)

        assert schemas.kwargs == SchemaInfo(
            kind="absent",
            declared_on=f"{__name__}.TestSchemaAdapter.test_all_roles_distinguish_framework_absence_explicit_none_fields_and_opaque.<locals>.Card",
            import_path=None,
            fields=(),
        )
        assert schemas.slots.kind == "fields"
        assert schemas.template_data.kind == "opaque"
        assert schemas.js_data == ABSENT_SCHEMA
        assert schemas.css_data == ABSENT_SCHEMA

    def test_component_schema_binding_reports_composed_c3_owner_and_none_shadow(self):
        app = Citry(autodiscover=False)

        @dataclass
        class MixinKwargs:
            mixin: str

        class SchemaMixin:
            Kwargs = MixinKwargs

        class MixedCard(SchemaMixin, Component):
            citry = app

        class Replacement(MixedCard):
            class Kwargs:
                own: int

        class Reopened(MixedCard):
            Kwargs = None

        mixed = _inspect_component_schemas(MixedCard).kwargs
        replacement = _inspect_component_schemas(Replacement).kwargs
        reopened = _inspect_component_schemas(Reopened).kwargs

        assert mixed.declared_on.endswith(".<locals>.SchemaMixin")
        assert [item.name for item in mixed.fields] == ["mixin"]
        assert replacement.declared_on.endswith(".<locals>.Replacement")
        assert [item.name for item in replacement.fields] == ["mixin", "own"]
        assert reopened.kind == "absent"
        assert reopened.declared_on.endswith(".<locals>.Reopened")

    def test_multiple_branch_schema_path_names_the_effective_receiving_component(self):
        app = Citry(autodiscover=False)

        class Left(Component):
            citry = app

            class Kwargs:
                left: str

        class Right(Component):
            citry = app

            class Kwargs:
                right: str

        class Combined(Left, Right):
            pass

        schema = _inspect_component_schemas(Combined).kwargs

        assert schema.declared_on is not None
        assert schema.declared_on.endswith(".<locals>.Left")
        assert schema.import_path is not None
        assert schema.import_path.endswith(".<locals>.Combined.Kwargs")
        assert [item.name for item in schema.fields] == ["right", "left"]

    def test_schema_role_rejects_a_non_class_binding(self):
        app = Citry(autodiscover=False)

        class Card(Component):
            citry = app
            Kwargs = 42

        with pytest.raises(TypeError, match=r"Card\.Kwargs must be a class or None"):
            _inspect_component_schemas(Card)

    def test_schema_role_requires_safe_owner_and_schema_import_paths(self):
        app = Citry(autodiscover=False)

        class Schema(NamedTuple):
            value: str

        Schema.__module__ = ""

        class Card(Component):
            citry = app
            Kwargs = Schema

        with pytest.raises(TypeError, match="safe import paths"):
            _inspect_component_schemas(Card)

        class SafeSchema:
            value: str

        class UnsafeOwner:
            __module__ = ""
            Kwargs = SafeSchema

        class OwnedCard(UnsafeOwner, Component):
            citry = app

        with pytest.raises(TypeError, match="safe import paths"):
            _inspect_component_schemas(OwnedCard)

    @pytest.mark.parametrize("attribute", ["Kwargs", "Slots", "TemplateData", "JsData", "CssData"])
    def test_explicit_none_schema_role_requires_safe_owner_provenance(self, attribute):
        app = Citry(autodiscover=False)
        component_class = type(
            "Generated",
            (Component,),
            {
                "__module__": "",
                "citry": app,
                attribute: None,
            },
        )

        with pytest.raises(TypeError, match=rf"owner of the {attribute} schema binding"):
            app.inspect_component(component_class)

    def test_dataclass_fields_include_inheritance_defaults_factories_and_descriptions(self):
        calls = 0

        def factory():
            nonlocal calls
            calls += 1
            return [1]

        @dataclass
        class Base:
            inherited: str

        @dataclass
        class Schema(Base):
            count: int = field(default=3, metadata={"description": "Count."})
            made: list[int] = field(default_factory=factory)
            hidden: int = field(default=4, init=False)
            incoming: InitVar[str] = "ignored"
            class_value: ClassVar[int] = 5

        fields_info = _inspect_schema_class(Schema, include_default_values=True)

        assert fields_info is not None
        assert [item.name for item in fields_info] == ["inherited", "count", "made", "incoming"]
        assert [item.default_kind for item in fields_info] == ["missing", "value", "factory", "value"]
        assert fields_info[1].description == "Count."
        assert fields_info[1].default_value == 3
        assert fields_info[2].default_value_state == "not-applicable"
        assert calls == 0
        assert get_fields(Schema) == [
            FieldSpec("inherited", required=True),
            FieldSpec("count", required=False),
            FieldSpec("made", required=False),
            FieldSpec("incoming", required=False),
        ]

    def test_real_pydantic_v2_and_v1_protocols(self):
        factories = 0

        def factory():
            nonlocal factories
            factories += 1
            return [1]

        class V2Schema(BaseModel):
            required: int = Field(description="Required v2.")
            value: list[int] = Field(default=[1], description="Value v2.")
            made: list[int] = Field(default_factory=factory)

        class V1Schema(BaseModelV1):
            required: int = FieldV1(description="Required v1.")
            value: list[int] = FieldV1(default=[1], description="Value v1.")
            made: list[int] = FieldV1(default_factory=factory)

        v2 = _inspect_schema_class(V2Schema, include_default_values=True)
        v1 = _inspect_schema_class(V1Schema, include_default_values=True)

        assert v2 is not None
        assert v1 is not None
        assert [(item.name, item.required, item.default_kind) for item in v2] == [
            ("required", True, "missing"),
            ("value", False, "value"),
            ("made", False, "factory"),
        ]
        assert [(item.name, item.required, item.default_kind) for item in v1] == [
            ("required", True, "missing"),
            ("value", False, "value"),
            ("made", False, "factory"),
        ]
        assert [item.description for item in v2] == ["Required v2.", "Value v2.", None]
        assert [item.description for item in v1] == ["Required v1.", "Value v1.", None]
        assert v2[1].default_value == (1,)
        assert v1[1].default_value == (1,)
        assert factories == 0

    def test_named_tuple_uses_runtime_fields_defaults_and_annotations(self):
        class Schema(NamedTuple):
            title: str
            count: int = 3

        fields_info = _inspect_schema_class(Schema, include_default_values=True)

        assert fields_info is not None
        assert [(item.name, item.required, item.type_display) for item in fields_info] == [
            ("title", True, "str"),
            ("count", False, "int"),
        ]
        assert fields_info[1].default_value == 3

    def test_named_tuple_can_fall_back_to_static_constructor_annotations(self):
        class Schema(NamedTuple):
            title: str

        Schema.__annotations__ = {}
        fields_info = _inspect_schema_class(Schema)

        assert fields_info is not None
        assert fields_info[0].type_display == "str"

    def test_inherited_named_tuple_can_fall_back_to_owner_constructor_annotations(self):
        class Base(NamedTuple):
            title: str

        class Schema(Base):
            pass

        Base.__annotations__ = {}
        fields_info = _inspect_schema_class(Schema)

        assert fields_info is not None
        assert fields_info[0].type_display == "str"

    def test_inherited_named_tuple_ignores_custom_subclass_constructor_annotations(self):
        calls = 0

        def side_effect():
            nonlocal calls
            calls += 1
            return int

        class Base(NamedTuple):
            title: str

        class Schema(Base):
            def __new__(cls, title: side_effect()):
                return tuple.__new__(cls, (title,))

        before = calls
        fields_info = _inspect_schema_class(Schema)

        assert fields_info is not None
        assert fields_info[0].type_display == "str"
        assert calls == before

    def test_empty_string_annotation_is_unavailable_without_hiding_the_field(self):
        Schema = dataclass(type("Schema", (), {"__annotations__": {"value": ""}}))

        fields_info = _inspect_schema_class(Schema)

        assert fields_info is not None
        assert fields_info[0].type_display is None
        assert fields_info[0].type_fidelity == "unavailable"
        assert get_fields(Schema) == [FieldSpec("value", required=True)]

    def test_default_values_are_omitted_by_default_and_unsupported_without_user_methods(self):
        calls = {"iter": 0, "repr": 0}

        class HostileList(list):
            def __iter__(self):
                calls["iter"] += 1
                raise AssertionError

        class HostileObject:
            def __repr__(self):
                calls["repr"] += 1
                raise AssertionError

        class FieldProtocol:
            annotation = object()
            default_factory = None
            description = None

            def __init__(self, default):
                self.default = default

            def is_required(self):
                return False

        class OmittedSchema:
            model_fields = {"value": FieldProtocol(HostileObject())}

        class UnsupportedSchema:
            model_fields = {
                "list": FieldProtocol(HostileList([1])),
                "object": FieldProtocol(HostileObject()),
                "integer": FieldProtocol(2**53),
            }

        omitted = _inspect_schema_class(OmittedSchema)
        unsupported = _inspect_schema_class(UnsupportedSchema, include_default_values=True)

        assert omitted is not None
        assert omitted[0].default_value_state == "omitted"
        assert unsupported is not None
        assert [item.default_value_state for item in unsupported] == ["unsupported"] * 3
        assert calls == {"iter": 0, "repr": 0}

    @pytest.mark.parametrize(
        ("annotation", "expected"),
        [
            ("Card", "Card"),
            (None, "None"),
            (Any, "Any"),
            (ForwardRef("Card"), "Card"),
            (list[int], "list[int]"),
            (tuple[str, ...], "tuple[str, ...]"),
            (dict[str, int], "dict[str, int]"),
            (set[str], "set[str]"),
            (frozenset[str], "frozenset[str]"),
            (type[str], "type[str]"),
            (Sequence[int], "Sequence[int]"),
            (Mapping[str, int], "Mapping[str, int]"),
            (Callable[[str, int], bool], "Callable[[str, int], bool]"),
            (Callable[..., bool], "Callable[..., bool]"),
            (Literal[None, True, 2, 1.5, "x"], 'Literal[None, True, 2, 1.5, "x"]'),  # noqa: PYI061
            (Annotated[list[int], object()], "list[int]"),
            (str | None, "str | None"),
        ],
    )
    def test_safe_type_formatter_supported_vocabulary(self, annotation, expected):
        assert _format_annotation(annotation) == expected

    def test_safe_type_formatter_handles_type_var_and_user_class(self):
        Value = TypeVar("Value")

        class Payload:
            pass

        assert _format_annotation(Value) == "Value"
        assert _format_annotation(Payload).endswith(".<locals>.Payload")

    def test_safe_type_formatter_rejects_unsupported_values_without_repr(self):
        calls = 0

        class Hostile:
            def __repr__(self):
                nonlocal calls
                calls += 1
                raise AssertionError

        assert _format_annotation(Hostile()) is None
        assert _format_annotation(Literal[math.nan]) is None
        assert _format_annotation(Literal[()]) is None
        assert _format_annotation(ClassVar[int]) is None
        assert calls == 0

    @pytest.mark.parametrize(
        "annotation",
        [
            typing.Union[int, Literal[()]],  # noqa: UP007 - preserve the typing form under test
            list[Literal[()]],
            Literal[b"bytes"],
        ],
    )
    def test_safe_type_formatter_rejects_partially_unsupported_forms(self, annotation):
        assert _format_annotation(annotation) is None

    def test_safe_type_formatter_rejects_a_cyclic_typing_form(self):
        annotation = typing.List[int]  # noqa: UP006 - mutate the typing alias runtime object
        original_arguments = annotation.__args__
        annotation.__args__ = (annotation,)
        try:
            assert _format_annotation(annotation) is None
        finally:
            annotation.__args__ = original_arguments

    def test_safe_type_formatter_rejects_excessive_supported_nesting(self):
        annotation = int
        for _ in range(1_500):
            annotation = list[annotation]

        assert _format_annotation(annotation) is None

    def test_hostile_annotation_attributes_are_never_accessed(self):
        calls = 0

        class HostileAnnotation:
            def __getattribute__(self, name):
                nonlocal calls
                calls += 1
                raise AssertionError(name)

        annotation = HostileAnnotation()

        @dataclass
        class Schema:
            value: object

        Schema.__dataclass_fields__["value"].type = annotation

        fields_info = _inspect_schema_class(Schema)

        assert fields_info is not None
        assert fields_info[0].type_display is None
        assert get_fields(Schema) == [FieldSpec("value", required=True)]
        assert calls == 0

    def test_typing_form_rejects_hostile_non_tuple_arguments_without_iteration(self):
        calls = 0

        class HostileList(list):
            def __iter__(self):
                nonlocal calls
                calls += 1
                raise AssertionError

        annotation = typing.List[int]  # noqa: UP006 - exercise the typing alias runtime object
        original_arguments = annotation.__args__
        annotation.__args__ = HostileList([int])
        try:
            assert _format_annotation(annotation) is None
            assert calls == 0
        finally:
            annotation.__args__ = original_arguments

    def test_typing_union_with_mutated_empty_arguments_is_unavailable(self):
        annotation = typing.Union[int, str]  # noqa: UP007 - mutate the typing union runtime object
        original_arguments = annotation.__args__
        annotation.__args__ = ()
        try:
            assert _format_annotation(annotation) is None
        finally:
            annotation.__args__ = original_arguments

    def test_hostile_class_module_is_unavailable_without_truthiness(self):
        calls = 0

        class HostileModule:
            def __bool__(self):
                nonlocal calls
                calls += 1
                raise AssertionError

            def __eq__(self, other):
                nonlocal calls
                calls += 1
                raise AssertionError(other)

        annotation = type("Payload", (), {"__module__": HostileModule()})
        assert _format_annotation(annotation) is None
        assert calls == 0

    def test_class_import_path_bypasses_hostile_metaclass_module_descriptor(self):
        calls = 0

        class Meta(type):
            @property
            def __module__(cls):
                nonlocal calls
                calls += 1
                raise AssertionError

        class Payload(metaclass=Meta):
            pass

        assert _format_annotation(Payload).endswith(".<locals>.Payload")
        assert calls == 0

    def test_schema_records_do_not_retain_component_or_schema_classes(self):
        app = Citry(autodiscover=False)

        class Card(Component):
            citry = app

            class Kwargs:
                title: str

        schema_class = Card.Kwargs
        card_ref = ref(Card)
        schema_ref = ref(schema_class)
        info = _inspect_component_schemas(Card)
        app.unregister(Card)
        del Card
        del schema_class
        gc.collect()

        assert info.kwargs.fields[0].type_display == "str"
        assert card_ref() is None
        assert schema_ref() is None


class TestCatalogQueries:
    def test_missing_distribution_metadata_uses_unknown_version(self, monkeypatch):
        def missing_distribution(_name):
            raise PackageNotFoundError

        monkeypatch.setattr("citry._component_introspection.version", missing_distribution)

        assert Citry(autodiscover=False).inspect_components().citry_version == "unknown"

    def test_synthetic_module_file_is_not_reported_as_a_python_path(self, monkeypatch):
        app = Citry(autodiscover=False)
        module_name = "citry_test_synthetic_component"
        module = ModuleType(module_name)
        module.__file__ = "<generated>"
        monkeypatch.setitem(sys.modules, module_name, module)
        component_class = type(
            "Generated",
            (Component,),
            {
                "__module__": module_name,
                "citry": app,
                "template": """
                <p>generated</p>
                """,
            },
        )

        info = app.inspect_component(component_class)

        assert info.python_file is None

    def test_unloaded_component_module_is_not_reported_as_a_python_path(self):
        app = Citry(autodiscover=False)
        module_name = "citry_test_unloaded_component"
        assert module_name not in sys.modules
        component_class = type(
            "Generated",
            (Component,),
            {
                "__module__": module_name,
                "citry": app,
            },
        )

        info = app.inspect_component(component_class)

        assert info.module == module_name
        assert info.python_file is None

    def test_generated_component_without_module_identity_uses_nullable_metadata(self):
        app = Citry(autodiscover=False)
        component_class = type("Generated", (Component,), {"__module__": "", "citry": app})

        info = app.inspect_component(component_class)

        assert info.module is None
        assert info.import_path is None
        assert info.python_file is None

    def test_plural_query_groups_aliases_selects_primary_names_and_sorts(self):
        app = Citry(autodiscover=False)

        class DefaultCard(Component):
            citry = app

        class ExplicitCard(Component):
            citry = app
            name = "FeaturedCard"

        class FallbackCard(Component):
            citry = app

        app.unregister("fallback-card")
        app.register(FallbackCard, "z-last")
        app.register(FallbackCard, "a-first")
        app.register(DefaultCard, "default-alias")

        catalog = app.inspect_components()
        by_class = {component.class_name: component for component in catalog.components}

        assert tuple(component.name for component in catalog.components) == tuple(
            sorted(component.name for component in catalog.components)
        )
        assert by_class["DefaultCard"].name == "default-card"
        assert by_class["DefaultCard"].aliases == ("default-alias", "defaultcard")
        assert by_class["ExplicitCard"].name == "featuredcard"
        assert by_class["ExplicitCard"].aliases == ("featured-card",)
        assert by_class["FallbackCard"].name == "a-first"
        assert by_class["FallbackCard"].aliases == ("fallbackcard", "z-last")

    def test_singular_query_is_case_insensitive_and_alias_does_not_change_primary(self):
        app = Citry(autodiscover=False)

        class ProductCard(Component):
            citry = app

        app.register(ProductCard, "legacy-card")

        by_primary = app.inspect_component("PRODUCT-CARD")
        by_alias = app.inspect_component("LEGACY-CARD")
        by_class = app.inspect_component(ProductCard)

        assert by_primary == by_alias == by_class
        assert by_alias.name == "product-card"
        assert by_alias.aliases == ("legacy-card", "productcard")

    def test_singular_query_rejects_missing_foreign_unregistered_and_invalid_inputs(self):
        app = Citry(autodiscover=False)
        foreign_app = Citry(autodiscover=False)

        class LocalCard(Component):
            citry = app

        class ForeignCard(Component):
            citry = foreign_app

        app.unregister(LocalCard)

        with pytest.raises(NotRegistered):
            app.inspect_component("missing")
        with pytest.raises(NotRegistered):
            app.inspect_component(LocalCard)
        with pytest.raises(NotRegistered):
            app.inspect_component(ForeignCard)
        with pytest.raises(TypeError, match="name or component class"):
            app.inspect_component(42)

    def test_query_options_are_explicit_and_extension_requests_are_not_ignored(self):
        app = Citry(autodiscover=False)

        with pytest.raises(TypeError, match="include_builtins"):
            app.inspect_components(include_builtins=1)
        with pytest.raises(TypeError, match="resolve_assets"):
            app.inspect_components(resolve_assets=1)
        with pytest.raises(TypeError, match="include_default_values"):
            app.inspect_components(include_default_values=1)
        with pytest.raises(TypeError, match="not a string"):
            app.inspect_components(include_extensions="events")
        catalog = app.inspect_components(include_extensions=("events",))
        assert catalog.extension_versions == (ExtensionVersion("events", 1),)

    def test_lazy_query_initializes_builtins_but_filters_them_by_default(self):
        app = Citry()

        assert not app._registry._builtins_ready()
        assert not app._discovered

        core_catalog = app.inspect_components()
        full_catalog = app.inspect_components(include_builtins=True)

        assert app._registry._builtins_ready()
        assert app._discovered
        assert core_catalog.components == ()
        assert len(full_catalog.components) == 7
        assert all(component.builtin for component in full_catalog.components)

    def test_builtin_alias_stays_filtered_and_builtin_subclass_is_a_user_component(self):
        app = Citry(autodiscover=False)
        provide = app.get("provide")
        app.register(provide, "legacy-provide")

        class UserProvide(provide):
            name = "user-provide"

        core_catalog = app.inspect_components()
        full_catalog = app.inspect_components(include_builtins=True)

        assert tuple(component.class_name for component in core_catalog.components) == ("UserProvide",)
        assert core_catalog.components[0].builtin is False
        provide_info = next(component for component in full_catalog.components if component.class_name == "Provide")
        assert provide_info.builtin is True
        assert "legacy-provide" in provide_info.aliases

    def test_component_metadata_uses_own_docstring_effective_transparency_and_loaded_file(self):
        app = Citry(autodiscover=False)

        class Base(Component):
            """Base documentation that the child must not inherit."""

            citry = app
            transparent = True

        class Child(Base):
            pass

        base = app.inspect_component(Base)
        child = app.inspect_component(Child)

        assert base.description == "Base documentation that the child must not inherit."
        assert child.description is None
        assert child.transparent is True
        assert child.python_file == Path(__file__).resolve()
        assert child.import_path is not None
        assert child.import_path.endswith(".<locals>.Child")

    def test_query_does_not_execute_custom_component_metaclass_attribute_hooks(self):
        active = False
        calls: list[str] = []

        class Meta(type(Component)):
            def __getattribute__(cls, name):
                if active and name in {"__dict__", "__mro__"}:
                    calls.append(name)
                    raise AssertionError(name)
                return super().__getattribute__(name)

        app = Citry(autodiscover=False)

        class Card(Component, metaclass=Meta):
            """Safe static description."""

            citry = app
            template_file = "missing.html"

            class Kwargs:
                title: str

        active = True
        try:
            info = app.inspect_component(Card, resolve_assets=True)
        finally:
            active = False

        assert info.description == "Safe static description."
        assert info.schemas.kwargs.fields[0].name == "title"
        assert info.assets.template.resolution == "missing"
        assert calls == []

    def test_schema_default_values_are_opt_in_and_factories_never_run(self):
        calls = 0

        def factory():
            nonlocal calls
            calls += 1
            return [1]

        app = Citry(autodiscover=False)

        class Card(Component):
            citry = app

            @dataclass
            class Kwargs:
                count: int = 3
                made: list[int] = field(default_factory=factory)

        omitted = app.inspect_component(Card)
        included = app.inspect_component(Card, include_default_values=True)

        assert omitted.schemas.kwargs.fields[0].default_value_state == "omitted"
        assert included.schemas.kwargs.fields[0].default_value == 3
        assert included.schemas.kwargs.fields[1].default_value_state == "not-applicable"
        assert calls == 0

    def test_fresh_queries_follow_alias_removal_and_hot_replacement(self):
        app = Citry(autodiscover=False)
        original = _reload_like_component(app, "original")
        app.register(original, "old-alias")
        retained = app.inspect_component(original)

        app.unregister("old-alias")
        without_alias = app.inspect_component(original)
        app.unregister(original)
        replacement = _reload_like_component(app, "replacement")
        fresh = app.inspect_component(replacement)

        assert retained.aliases == ("old-alias",)
        assert without_alias.aliases == ()
        assert retained.class_id == fresh.class_id
        assert retained.definition_id != fresh.definition_id
        assert app.get_component_by_class_id(fresh.class_id) is replacement

    def test_same_component_path_in_two_engines_has_distinct_catalog_runtime_identity(self):
        first_app = Citry(autodiscover=False)
        second_app = Citry(autodiscover=False)
        first_class = _reload_like_component(first_app, "first")
        second_class = _reload_like_component(second_app, "second")

        first = first_app.inspect_component(first_class)
        second = second_app.inspect_component(second_class)

        assert first.class_id == second.class_id
        assert first.engine_id != second.engine_id
        assert first.definition_id != second.definition_id

    def test_in_flight_query_keeps_its_copied_generation_and_aliases(self, monkeypatch):
        citry_module = import_module("citry.citry")
        app = Citry(autodiscover=False)
        original = _reload_like_component(app, "original")
        app.register(original, "old-alias")
        original_builder = citry_module._build_component_info
        started = Event()
        resume = Event()

        def blocking_builder(*args, **kwargs):
            started.set()
            assert resume.wait(timeout=5)
            return original_builder(*args, **kwargs)

        monkeypatch.setattr(citry_module, "_build_component_info", blocking_builder)
        with ThreadPoolExecutor(max_workers=1) as executor:
            pending = executor.submit(app.inspect_component, "old-alias")
            assert started.wait(timeout=5)
            app.unregister(original)
            replacement = _reload_like_component(app, "replacement")
            resume.set()
            retained = pending.result(timeout=5)

        monkeypatch.setattr(citry_module, "_build_component_info", original_builder)
        fresh = app.inspect_component(replacement)

        assert retained.name == "original"
        assert retained.aliases == ("old-alias",)
        assert retained.definition_id == original.definition_id
        assert fresh.definition_id == replacement.definition_id
        assert fresh.definition_id != retained.definition_id

    def test_query_fails_fast_while_another_thread_owns_lifecycle_state(self):
        app = Citry(autodiscover=False)
        started = Event()
        resume = Event()

        def hold_lifecycle():
            with app._registry._lifecycle.operation("test lifecycle work"):
                started.set()
                assert resume.wait(timeout=5)

        with ThreadPoolExecutor(max_workers=1) as executor:
            pending = executor.submit(hold_lifecycle)
            assert started.wait(timeout=5)
            with pytest.raises(CitryLifecycleInProgress, match="test lifecycle work"):
                app.inspect_components()
            resume.set()
            pending.result(timeout=5)

    def test_retained_catalog_does_not_keep_unregistered_component_alive(self):
        app = Citry(autodiscover=False)

        class Card(Component):
            citry = app
            template_file = "missing.html"

        card_ref = ref(Card)
        catalog = app.inspect_components(resolve_assets=True)
        app.unregister(Card)
        del Card
        gc.collect()

        assert catalog.components[0].assets.template.resolution == "missing"
        assert app._file_index == {}
        assert card_ref() is None


class TestExtensionMetadataQueries:
    def test_requested_extensions_are_preflighted_deduplicated_and_called_in_canonical_order(self):
        calls: list[tuple[str, str]] = []
        contexts: list[ComponentIntrospectionContext] = []

        class Zeta(Extension):
            name = "zeta"
            introspection_version = 2

            def inspect_component(self, ctx):
                calls.append((self.name, ctx.info.name))
                contexts.append(ctx)
                return {"source": self.name}

        class Alpha(Extension):
            name = "alpha"
            introspection_version = 1

            def inspect_component(self, ctx):
                calls.append((self.name, ctx.info.name))
                contexts.append(ctx)
                return {"source": self.name}

        app = Citry(extensions=[Zeta, Alpha], autodiscover=False)

        class ZCard(Component):
            citry = app

        class ACard(Component):
            citry = app

        requested = (name for name in ("zeta", "alpha", "zeta"))
        catalog = app.inspect_components(include_extensions=requested)

        assert calls == [
            ("alpha", "a-card"),
            ("zeta", "a-card"),
            ("alpha", "z-card"),
            ("zeta", "z-card"),
        ]
        assert [(item.name, item.introspection_version) for item in catalog.extension_versions] == [
            ("alpha", 1),
            ("zeta", 2),
        ]
        assert all(ctx.citry is app and ctx.info.extensions == () for ctx in contexts)
        assert contexts[0].component_class is ACard
        assert contexts[0].info is contexts[1].info
        assert contexts[2].component_class is ZCard
        assert contexts[2].info is contexts[3].info
        assert [entry.name for entry in catalog.components[0].extensions] == ["alpha", "zeta"]

    def test_unrequested_inspector_never_runs_and_none_preserves_only_envelope_version(self):
        calls = 0

        class OptionalMetadata(Extension):
            name = "optional_metadata"
            introspection_version = 3

            def inspect_component(self, ctx):
                nonlocal calls
                calls += 1

        app = Citry(extensions=[OptionalMetadata], autodiscover=False)

        core = app.inspect_components()
        requested = app.inspect_components(include_extensions=("optional_metadata",))

        assert core.extension_versions == ()
        assert calls == 0
        assert requested.components == ()
        assert [(item.name, item.introspection_version) for item in requested.extension_versions] == [
            ("optional_metadata", 3)
        ]

    @pytest.mark.parametrize("requested", [42, "events", [""], [1]])
    def test_extension_selection_rejects_invalid_iterables_and_entries(self, requested):
        app = Citry(autodiscover=False)

        with pytest.raises(TypeError, match=r"include_extensions|extension names"):
            app.inspect_components(include_extensions=requested)

    def test_missing_or_unsupported_extension_fails_before_any_callback(self):
        calls = 0

        class Valid(Extension):
            name = "valid"
            introspection_version = 1

            def inspect_component(self, ctx):
                nonlocal calls
                calls += 1
                return {}

        class Unsupported(Extension):
            name = "unsupported"

        app = Citry(extensions=[Valid, Unsupported], autodiscover=False)

        class Card(Component):
            citry = app

        with pytest.raises(ComponentIntrospectionError, match="not installed"):
            app.inspect_component(Card, include_extensions=("valid", "missing"))
        with pytest.raises(ComponentIntrospectionError, match="does not implement"):
            app.inspect_component(Card, include_extensions=("valid", "unsupported"))
        assert calls == 0

    @pytest.mark.parametrize("version", [None, 0, -1, True, 1.0, "1"])
    def test_requested_inspector_requires_exact_positive_integer_version(self, version):
        class InvalidVersion(Extension):
            name = "invalid_version"
            introspection_version = version

            def inspect_component(self, ctx):
                return {}

        app = Citry(extensions=[InvalidVersion], autodiscover=False)

        with pytest.raises(ComponentIntrospectionError, match="positive integer"):
            app.inspect_components(include_extensions=("invalid_version",))

    def test_noncallable_inspector_member_is_unsupported(self):
        class InvalidInspector(Extension):
            name = "invalid_inspector"
            introspection_version = 1
            inspect_component = 42

        app = Citry(extensions=[InvalidInspector], autodiscover=False)

        with pytest.raises(ComponentIntrospectionError, match="does not implement"):
            app.inspect_components(include_extensions=("invalid_inspector",))

    def test_inherited_inspector_capability_is_supported(self):
        class BaseInspector(Extension):
            name = "base_inspector"
            introspection_version = 4

            def inspect_component(self, ctx):
                return {"name": ctx.info.name}

        class ChildInspector(BaseInspector):
            name = "child_inspector"

        app = Citry(extensions=[ChildInspector], autodiscover=False)

        class Card(Component):
            citry = app

        info = app.inspect_component(Card, include_extensions=("child_inspector",))

        assert info.extensions[0].introspection_version == 4
        assert (
            info.extensions[0].data
            == ComponentExtensionInfo(name="expected", introspection_version=1, data={"name": "card"}).data
        )

    def test_singular_query_copies_publication_and_matches_catalog_entry(self):
        publication = {"items": [1]}

        class Metadata(Extension):
            name = "metadata"
            introspection_version = 1

            def inspect_component(self, ctx):
                return publication

        app = Citry(extensions=[Metadata], autodiscover=False)

        class Card(Component):
            citry = app

        singular = app.inspect_component(Card, include_extensions=("metadata",))
        catalog = app.inspect_components(include_extensions=("metadata",))
        publication["items"].append(2)

        assert singular == catalog.components[0]
        assert (
            singular.extensions[0].data
            == ComponentExtensionInfo(name="expected", introspection_version=1, data={"items": [1]}).data
        )
        first = catalog.to_dict()
        second = catalog.to_dict()
        first["components"][0]["extensions"]["metadata"]["data"]["items"].append(3)
        assert second["components"][0]["extensions"]["metadata"]["data"]["items"] == [1]

    @pytest.mark.parametrize(
        "publication",
        [
            [],
            (),
            1,
            {"unsafe": 2**53},
            {"nan": math.nan},
            {"path": Path("x")},
            {"class": Component},
            {"callable": lambda: None},
            {1: "value"},
            {"surrogate": "\ud800"},
        ],
    )
    def test_invalid_publication_is_wrapped_with_extension_and_component_context(self, publication):
        class InvalidMetadata(Extension):
            name = "invalid_metadata"
            introspection_version = 1

            def inspect_component(self, ctx):
                return publication

        app = Citry(extensions=[InvalidMetadata], autodiscover=False)

        class Card(Component):
            citry = app

        with pytest.raises(ComponentIntrospectionError, match=r"invalid_metadata.*card") as captured:
            app.inspect_component(Card, include_extensions=("invalid_metadata",))
        assert captured.value.extension_name == "invalid_metadata"
        assert captured.value.component_name == "card"
        assert captured.value.__cause__ is not None

    def test_frozen_json_wrappers_are_rejected_at_root_and_nested_publication_boundaries(self):
        frozen = ComponentExtensionInfo(name="seed", introspection_version=1, data={"x": 1}).data

        class FrozenMetadata(Extension):
            name = "frozen_metadata"
            introspection_version = 1

            def inspect_component(self, ctx):
                return self.publication

        extension = FrozenMetadata()
        app = Citry(extensions=[extension], autodiscover=False)

        class Card(Component):
            citry = app

        for publication in (frozen, {"nested": frozen}):
            extension.publication = publication
            with pytest.raises(ComponentIntrospectionError):
                app.inspect_component(Card, include_extensions=("frozen_metadata",))

    def test_container_subclasses_and_arbitrary_objects_are_rejected_without_user_hooks(self):
        calls = {"iter": 0, "repr": 0, "str": 0}

        class HostileList(list):
            def __iter__(self):
                calls["iter"] += 1
                raise AssertionError

        class HostileObject:
            def __repr__(self):
                calls["repr"] += 1
                raise AssertionError

            def __str__(self):
                calls["str"] += 1
                raise AssertionError

        class InvalidMetadata(Extension):
            name = "invalid_metadata"
            introspection_version = 1

            def inspect_component(self, ctx):
                return self.publication

        extension = InvalidMetadata()
        app = Citry(extensions=[extension], autodiscover=False)

        class Card(Component):
            citry = app

        for publication in ({"items": HostileList([1])}, {"object": HostileObject()}):
            extension.publication = publication
            with pytest.raises(ComponentIntrospectionError):
                app.inspect_component(Card, include_extensions=("invalid_metadata",))
        assert calls == {"iter": 0, "repr": 0, "str": 0}

    def test_cycles_are_rejected_and_shared_children_are_accepted(self):
        cycle: list[object] = []
        cycle.append(cycle)
        child = [1]

        class Metadata(Extension):
            name = "metadata"
            introspection_version = 1

            def inspect_component(self, ctx):
                return self.publication

        extension = Metadata()
        app = Citry(extensions=[extension], autodiscover=False)

        class Card(Component):
            citry = app

        extension.publication = {"cycle": cycle}
        with pytest.raises(ComponentIntrospectionError):
            app.inspect_component(Card, include_extensions=("metadata",))
        extension.publication = {"shared": [child, child]}
        info = app.inspect_component(Card, include_extensions=("metadata",))
        assert (
            info.extensions[0].data
            == ComponentExtensionInfo(name="expected", introspection_version=1, data={"shared": [[1], [1]]}).data
        )

    def test_inspector_error_is_wrapped_without_calling_exception_str(self):
        string_calls = 0

        class HostileError(RuntimeError):
            def __str__(self):
                nonlocal string_calls
                string_calls += 1
                raise AssertionError

        class Failing(Extension):
            name = "failing"
            introspection_version = 1

            def inspect_component(self, ctx):
                raise HostileError

        app = Citry(extensions=[Failing], autodiscover=False)

        class Card(Component):
            citry = app

        with pytest.raises(ComponentIntrospectionError, match=r"failing.*card.*HostileError") as captured:
            app.inspect_component(Card, include_extensions=("failing",))
        assert type(captured.value.__cause__) is HostileError
        assert string_calls == 0

    def test_inspector_can_reenter_core_inspection_without_lifecycle_lock(self):
        class Recursive(Extension):
            name = "recursive"
            introspection_version = 1

            def inspect_component(self, ctx):
                nested = ctx.citry.inspect_component(ctx.component_class)
                return {"nested_name": nested.name}

        app = Citry(extensions=[Recursive], autodiscover=False)

        class Card(Component):
            citry = app

        info = app.inspect_component(Card, include_extensions=("recursive",))
        assert (
            info.extensions[0].data
            == ComponentExtensionInfo(name="expected", introspection_version=1, data={"nested_name": "card"}).data
        )

    def test_core_never_reflects_extension_config_or_runs_unrequested_inspectors(self):
        calls = {"publisher": 0, "unrequested": 0, "repr": 0}

        class HostileSecret:
            def __repr__(self):
                calls["repr"] += 1
                raise AssertionError

        class Publisher(Extension):
            name = "publisher"
            introspection_version = 1

            def inspect_component(self, ctx):
                calls["publisher"] += 1
                return {"public": "allowed"}

        class Unrequested(Extension):
            name = "unrequested"
            introspection_version = 1

            def inspect_component(self, ctx):
                calls["unrequested"] += 1
                raise AssertionError

        app = Citry(extensions=[Publisher, Unrequested], autodiscover=False)

        class Card(Component):
            citry = app

            class Publisher:
                secret = HostileSecret()

        core = app.inspect_component(Card)
        published = app.inspect_component(Card, include_extensions=("publisher",))

        assert core.extensions == ()
        assert (
            published.extensions[0].data
            == ComponentExtensionInfo(name="expected", introspection_version=1, data={"public": "allowed"}).data
        )
        assert calls == {"publisher": 1, "unrequested": 0, "repr": 0}

    def test_blocking_inspector_does_not_block_unregister_or_mix_snapshot_generations(self):
        started = Event()
        resume = Event()

        class Blocking(Extension):
            name = "blocking"
            introspection_version = 1

            def inspect_component(self, ctx):
                started.set()
                assert resume.wait(timeout=5)
                return {"definition_id": ctx.info.definition_id}

        app = Citry(extensions=[Blocking], autodiscover=False)
        original = _reload_like_component(app, "original")
        app.register(original, "old-alias")

        with ThreadPoolExecutor(max_workers=1) as executor:
            pending = executor.submit(
                app.inspect_component,
                original,
                include_extensions=("blocking",),
            )
            assert started.wait(timeout=5)
            app.unregister(original)
            replacement = _reload_like_component(app, "replacement")
            resume.set()
            retained = pending.result(timeout=5)

        fresh = app.inspect_component(replacement)
        retained_data = dict(retained.extensions[0].data)

        assert retained.name == "original"
        assert retained.aliases == ("old-alias",)
        assert retained_data["definition_id"] == original.definition_id
        assert retained.definition_id != fresh.definition_id

    def test_concurrent_queries_enter_the_same_inspector_without_global_serialization(self):
        barrier = Barrier(2)

        class Concurrent(Extension):
            name = "concurrent"
            introspection_version = 1

            def inspect_component(self, ctx):
                barrier.wait(timeout=5)
                return {"name": ctx.info.name}

        app = Citry(extensions=[Concurrent], autodiscover=False)

        class Card(Component):
            citry = app

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(app.inspect_component, Card, include_extensions=("concurrent",)) for _index in range(2)
            ]
            results = [future.result(timeout=5) for future in futures]
        assert results[0] == results[1]

    def test_retained_extension_catalog_does_not_keep_unregistered_class_alive(self):
        class Metadata(Extension):
            name = "metadata"
            introspection_version = 1

            def inspect_component(self, ctx):
                return {"name": ctx.info.name}

        app = Citry(extensions=[Metadata], autodiscover=False)

        class Card(Component):
            citry = app

        card_ref = ref(Card)
        catalog = app.inspect_components(include_extensions=("metadata",))
        app.unregister(Card)
        del Card
        gc.collect()

        assert (
            catalog.components[0].extensions[0].data
            == ComponentExtensionInfo(name="expected", introspection_version=1, data={"name": "card"}).data
        )
        assert card_ref() is None


class TestCatalogAssetQueries:
    def test_asset_declaration_requires_safe_owner_provenance(self):
        app = Citry(autodiscover=False)

        class UnsafeOwner:
            __module__ = ""
            template = """
            <p>unsafe owner</p>
            """

        class Card(UnsafeOwner, Component):
            citry = app

        with pytest.raises(TypeError, match="determine declaration provenance"):
            app.inspect_component(Card)

    def test_inline_none_and_explicit_none_records_preserve_provenance_without_source(self):
        app = Citry(autodiscover=False)

        class Inline(Component):
            citry = app
            template = """
                <p>private-template-source</p>
            """
            js = """
                console.log("private-js-source");
            """
            css = """
                .private-css-source { color: red; }
            """

        class Assetless(Component):
            citry = app

        class Base(Component):
            citry = app
            template = """
                <p>base source</p>
            """

        class Shadow(Base):
            template = None

        inline = app.inspect_component(Inline)
        empty = app.inspect_component(Assetless)
        shadow = app.inspect_component(Shadow)
        serialized = app.inspect_components().to_json()

        assert [inline.assets.template.kind, inline.assets.js.kind, inline.assets.css.kind] == [
            "inline",
            "inline",
            "inline",
        ]
        assert inline.assets.template.owner_file == Path(__file__).resolve()
        assert empty.assets.template == NONE_ASSET
        assert shadow.assets.template.kind == "none"
        assert shadow.assets.template.declared_on is not None
        assert shadow.assets.template.declared_on.endswith(".<locals>.Shadow")
        assert shadow.assets.template.owner_file == Path(__file__).resolve()
        assert "private-template-source" not in serialized
        assert "private-js-source" not in serialized
        assert "private-css-source" not in serialized

    def test_file_resolution_covers_absolute_configured_missing_and_unavailable(self, tmp_path):
        configured = tmp_path / "configured"
        configured.mkdir()
        (configured / "configured.html").write_text("configured")
        absolute = tmp_path / "absolute.js"
        absolute.write_text("absolute")
        app = Citry(dirs=[configured], autodiscover=False)

        Configured = type(
            "Configured",
            (Component,),
            {
                "__module__": "citry_test_missing_configured_module",
                "citry": app,
                "template_file": "configured.html",
            },
        )
        Absolute = type(
            "Absolute",
            (Component,),
            {
                "__module__": "citry_test_missing_absolute_module",
                "citry": app,
                "js_file": absolute,
            },
        )
        Missing = type(
            "Missing",
            (Component,),
            {
                "__module__": "citry_test_missing_absolute_target_module",
                "citry": app,
                "css_file": tmp_path / "missing.css",
            },
        )
        unavailable_app = Citry(autodiscover=False)
        Unavailable = type(
            "Unavailable",
            (Component,),
            {
                "__module__": "citry_test_missing_unavailable_module",
                "citry": unavailable_app,
                "template_file": "nowhere.html",
            },
        )

        configured_info = app.inspect_component(Configured, resolve_assets=True).assets.template
        absolute_info = app.inspect_component(Absolute, resolve_assets=True).assets.js
        missing_info = app.inspect_component(Missing, resolve_assets=True).assets.css
        unavailable_info = unavailable_app.inspect_component(Unavailable, resolve_assets=True).assets.template

        assert configured_info.resolution == "resolved"
        assert configured_info.resolved_path == (configured / "configured.html").resolve()
        assert configured_info.searched_paths == ((configured / "configured.html").resolve(),)
        assert absolute_info.declared_path == absolute.as_posix()
        assert absolute_info.resolution == "resolved"
        assert absolute_info.resolved_path == absolute
        assert absolute_info.searched_paths == (absolute,)
        assert missing_info.resolution == "missing"
        assert missing_info.searched_paths == (tmp_path / "missing.css",)
        assert unavailable_info.resolution == "unavailable"
        assert unavailable_info.searched_paths == ()
        for module_name in (
            "citry_test_missing_configured_module",
            "citry_test_missing_absolute_module",
            "citry_test_missing_absolute_target_module",
            "citry_test_missing_unavailable_module",
        ):
            assert module_name not in sys.modules

    @pytest.mark.parametrize("resolve_assets", [False, True])
    def test_arbitrary_pathlike_declaration_is_rejected_without_calling_fspath(self, resolve_assets):
        calls = 0

        class HostilePathLike:
            def __fspath__(self):
                nonlocal calls
                calls += 1
                raise AssertionError

        app = Citry(autodiscover=False)

        class Card(Component):
            citry = app
            template_file = HostilePathLike()

        with pytest.raises(TypeError, match=r"string or concrete pathlib\.Path"):
            app.inspect_component(Card, resolve_assets=resolve_assets)
        assert calls == 0

    def test_resolution_uses_declaring_base_module_and_preserves_candidate_order(self, tmp_path, monkeypatch):
        base_dir = tmp_path / "base"
        child_dir = tmp_path / "child"
        first_root = tmp_path / "first"
        second_root = tmp_path / "second"
        for directory in (base_dir, child_dir, first_root, second_root):
            directory.mkdir()
        (base_dir / "card.html").write_text("base")
        (child_dir / "card.html").write_text("child decoy")
        (second_root / "search.css").write_text("winner")
        base_module = _install_module(monkeypatch, "citry_test_asset_base", base_dir / "base.py")
        child_module = _install_module(monkeypatch, "citry_test_asset_child", child_dir / "child.py")
        app = Citry(dirs=[first_root, second_root], autodiscover=False)

        Base = type(
            "Base",
            (Component,),
            {
                "__module__": base_module.__name__,
                "citry": app,
                "template_file": "card.html",
            },
        )
        Child = type("Child", (Base,), {"__module__": child_module.__name__})
        Search = type(
            "Search",
            (Component,),
            {
                "__module__": child_module.__name__,
                "citry": app,
                "css_file": "search.css",
            },
        )

        inherited = app.inspect_component(Child, resolve_assets=True).assets.template
        searched = app.inspect_component(Search, resolve_assets=True).assets.css

        assert inherited.declared_on == "citry_test_asset_base.Base"
        assert inherited.owner_file == (base_dir / "base.py").absolute()
        assert inherited.resolved_path == (base_dir / "card.html").resolve()
        assert searched.resolved_path == (second_root / "search.css").resolve()
        assert searched.searched_paths == (
            child_dir / "search.css",
            first_root / "search.css",
            (second_root / "search.css").resolve(),
        )

    def test_plain_mixin_supplies_module_provenance_but_engine_supplies_search_roots(self, tmp_path, monkeypatch):
        mixin_dir = tmp_path / "mixin"
        search_root = tmp_path / "assets"
        mixin_dir.mkdir()
        search_root.mkdir()
        (search_root / "mixin.js").write_text("mixin")
        mixin_module = _install_module(monkeypatch, "citry_test_asset_mixin", mixin_dir / "mixin.py")
        app = Citry(dirs=[search_root], autodiscover=False)
        AssetMixin = type(
            "AssetMixin",
            (),
            {
                "__module__": mixin_module.__name__,
                "js_file": "mixin.js",
            },
        )
        Card = type("Card", (AssetMixin, Component), {"__module__": __name__, "citry": app})

        asset = app.inspect_component(Card, resolve_assets=True).assets.js

        assert asset.declared_on == "citry_test_asset_mixin.AssetMixin"
        assert asset.owner_file == (mixin_dir / "mixin.py").absolute()
        assert asset.searched_paths == (
            mixin_dir / "mixin.js",
            (search_root / "mixin.js").resolve(),
        )
        assert asset.resolved_path == (search_root / "mixin.js").resolve()

    def test_no_resolution_does_not_touch_filesystem_or_asset_runtime_state(self, monkeypatch):
        app = Citry(autodiscover=False)

        class Card(Component):
            citry = app
            template_file = "card.html"
            js_file = "card.js"
            css_file = "card.css"

        def fail_exists(_path):
            raise AssertionError("Path.exists() must not run")

        monkeypatch.setattr(Path, "exists", fail_exists)
        info = app.inspect_component(Card)

        assert info.assets.template.resolution == "not-requested"
        assert info.assets.js.resolution == "not-requested"
        assert info.assets.css.resolution == "not-requested"
        assert "_citry_template" not in Card.__dict__
        assert "_resolved_js" not in Card.__dict__
        assert "_resolved_css" not in Card.__dict__
        assert app._file_index == {}

    def test_resolution_reads_no_content_runs_no_hooks_and_releases_lifecycle_guard(self, tmp_path, monkeypatch):
        for filename in ("card.html", "card.js", "card.css"):
            (tmp_path / filename).write_text(filename)
        hook_calls: list[str] = []

        class Hooks(Extension):
            name = "hooks"

            def on_template_loaded(self, ctx):
                hook_calls.append(ctx.content)
                return ctx.content

            def on_js_loaded(self, ctx):
                hook_calls.append(ctx.content)
                return ctx.content

            def on_css_loaded(self, ctx):
                hook_calls.append(ctx.content)
                return ctx.content

        app = Citry(extensions=[Hooks], dirs=[tmp_path], autodiscover=False)

        class Card(Component):
            citry = app
            template_file = "card.html"
            js_file = "card.js"
            css_file = "card.css"

        started = Event()
        resume = Event()
        original_exists = Path.exists

        def blocking_exists(path):
            if path.name == "card.html":
                started.set()
                assert resume.wait(timeout=5)
            return original_exists(path)

        def fail_read_text(*_args, **_kwargs):
            raise AssertionError("Asset content must not be read")

        monkeypatch.setattr(Path, "exists", blocking_exists)
        monkeypatch.setattr(Path, "read_text", fail_read_text)
        with ThreadPoolExecutor(max_workers=1) as executor:
            pending = executor.submit(app.inspect_component, Card, resolve_assets=True)
            assert started.wait(timeout=5)
            app.register(Card, "registered-during-resolution")
            resume.set()
            info = pending.result(timeout=5)

        assert info.aliases == ()
        assert hook_calls == []
        assert "_citry_template" not in Card.__dict__
        assert "_resolved_js" not in Card.__dict__
        assert "_resolved_css" not in Card.__dict__
        assert app._file_index == {}
