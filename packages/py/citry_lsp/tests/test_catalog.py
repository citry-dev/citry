"""Tests for strict catalog validation and URI ownership."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from citry_lsp.catalog import CatalogIndex, _component_record, _optional_str, _required_str, _schema_fields


def _schema(*, fields: list[object] | None = None) -> dict[str, object]:
    return {
        "kind": "fields" if fields else "absent",
        "declared_on": "tests.Card" if fields else None,
        "import_path": "tests.Card.Schema" if fields else None,
        "namespace_policy": "closed" if fields else "unknown",
        "fields": fields or [],
    }


def _asset(*, kind: str = "none", resolved_path: Path | None = None) -> dict[str, object]:
    return {
        "kind": kind,
        "declared_on": "tests.Card" if kind != "none" else None,
        "owner_file": None,
        "declared_path": resolved_path.name if resolved_path is not None else None,
        "resolution": "resolved" if resolved_path is not None else "not-applicable",
        "resolved_path": str(resolved_path) if resolved_path is not None else None,
        "searched_paths": [str(resolved_path)] if resolved_path is not None else [],
    }


def _component(*, name: str = "card", aliases: list[str] | None = None) -> dict[str, object]:
    return {
        "class_id": f"tests.Card:{name}",
        "engine_id": "tests.engine",
        "definition_id": f"tests.Card:{name}:definition",
        "name": name,
        "aliases": aliases or [],
        "class_name": None,
        "module": None,
        "qualname": None,
        "import_path": None,
        "python_file": None,
        "description": None,
        "transparent": False,
        "builtin": False,
        "schemas": {
            "kwargs": _schema(),
            "slots": _schema(),
            "template_data": _schema(),
            "js_data": _schema(),
            "css_data": _schema(),
        },
        "assets": {
            "template": _asset(),
            "js": _asset(),
            "css": _asset(),
        },
        "extensions": {},
    }


def _catalog(*components: object) -> dict[str, object]:
    return {
        "schema_version": 1,
        "citry_version": "0.4.0",
        "engine_id": "tests.engine",
        "extension_versions": {},
        "components": list(components),
    }


def test_catalog_rejects_invalid_envelopes_and_duplicate_names():
    with pytest.raises(ValueError, match="must be a dict"):
        CatalogIndex(None)
    with pytest.raises(ValueError, match="envelope is invalid"):
        CatalogIndex({})
    with pytest.raises(ValueError, match="duplicate registered"):
        CatalogIndex(_catalog(_component(aliases=["CARD"])))


def test_catalog_ownership_rejects_non_file_and_handles_authority(tmp_path):
    template_path = tmp_path / "folder name" / "card.html"
    payload = _component()
    payload["assets"] = {
        "template": _asset(kind="file", resolved_path=template_path),
        "js": _asset(),
        "css": _asset(),
    }
    catalog = CatalogIndex(_catalog(payload))

    assert catalog.owns_template_uri("https://example.test/card.html") is False
    assert catalog.owns_template_uri("file://example.test/card.html") is False
    assert catalog.owns_template_uri(template_path.as_uri()) is True


def test_catalog_preserves_all_schema_asset_and_field_provenance(tmp_path):
    component = _component()
    field = {
        "name": "title",
        "required": True,
        "type_display": "str",
        "type_fidelity": "normalized",
        "default_kind": "missing",
        "default_value_state": "not-applicable",
        "default_value": None,
        "description": "Card title.",
        "source_module": "tests.cards",
        "source_qualname": "Card.Kwargs",
        "source_file": str((tmp_path / "cards.py").resolve()),
    }
    schemas = component["schemas"]
    assert isinstance(schemas, dict)
    schemas["kwargs"] = _schema(fields=[field])
    schemas["template_data"] = _schema(fields=[{**field, "name": "page"}])
    schemas["js_data"] = _schema(fields=[{**field, "name": "open"}])
    schemas["css_data"] = _schema(fields=[{**field, "name": "accent"}])
    assets = component["assets"]
    assert isinstance(assets, dict)
    for role in ("template", "js", "css"):
        assets[role] = _asset(kind="file", resolved_path=tmp_path / f"card.{role}")
    component["extensions"] = {"events": {"introspection_version": 1, "data": {"handlers": []}}}
    payload = _catalog(component)
    payload["extension_versions"] = {"events": 1}

    catalog = CatalogIndex(payload)
    card = catalog.get("card")

    assert card is not None
    assert card.schemas.kwargs.fields[0].source_qualname == "Card.Kwargs"
    assert card.schemas.template_data.fields[0].name == "page"
    assert card.schemas.js_data.fields[0].name == "open"
    assert card.schemas.css_data.fields[0].name == "accent"
    assert card.assets.js.resolved_path == tmp_path / "card.js"
    assert card.assets.css.resolved_path == tmp_path / "card.css"
    assert card.class_id == "tests.Card:card"
    assert card.extensions == {"events": {"introspection_version": 1, "data": {"handlers": ()}}}
    assert catalog.extension_versions == {"events": 1}


def test_catalog_asset_index_keeps_every_owner_of_a_shared_file(tmp_path):
    shared = tmp_path / "shared.css"
    first = _component(name="first")
    second = _component(name="second")
    for component in (first, second):
        assets = component["assets"]
        assert isinstance(assets, dict)
        assets["css"] = _asset(kind="file", resolved_path=shared)

    catalog = CatalogIndex(_catalog(first, second))

    assert [owner.name for owner in catalog.asset_owners(shared.as_uri(), "css")] == ["first", "second"]


def test_catalog_inline_index_uses_structured_owner_without_a_base_component(tmp_path):
    source = tmp_path / "components.py"
    child = _component(name="child")
    assets = child["assets"]
    assert isinstance(assets, dict)
    template = _asset(kind="inline")
    template.update(
        {
            "declared_on": "library.cards.BaseCard",
            "owner_file": str(source),
            "owner_module": "library.cards",
            "owner_qualname": "BaseCard",
        }
    )
    assets["template"] = template

    catalog = CatalogIndex(_catalog(child))

    assert [
        component.name for component in catalog.inline_asset_consumers(source.as_uri(), "template", "BaseCard")
    ] == ["child"]
    assert catalog.inline_asset_consumers(source.as_uri(), "template", "Child") == ()


def test_catalog_distinguishes_bare_names_from_prefixed_tag_names():
    catalog = CatalogIndex(
        _catalog(
            _component(name="button"),
            _component(name="c-button", aliases=["cbutton"]),
        )
    )

    assert catalog.get("c-button") is not None
    assert catalog.get("c-button").name == "c-button"
    assert catalog.get_tag("c-button") is not None
    assert catalog.get_tag("c-button").name == "button"
    assert catalog.get_tag("c-c-button") is not None
    assert catalog.get_tag("c-c-button").name == "c-button"
    assert catalog.get_tag("button") is None
    assert catalog.get_tag("c-Button").name == "button"
    assert catalog.get_tag("C-Button") is None


def test_component_record_rejects_invalid_shapes():
    with pytest.raises(ValueError, match="entries must be dicts"):
        _component_record(None)

    invalid = _component()
    invalid["aliases"] = [1]
    with pytest.raises(ValueError, match="aliases are invalid"):
        _component_record(invalid)

    invalid = _component()
    invalid["schemas"] = None
    with pytest.raises(ValueError, match="schemas are invalid"):
        _component_record(invalid)

    invalid = _component()
    invalid["assets"] = None
    with pytest.raises(ValueError, match="assets are invalid"):
        _component_record(invalid)


def test_field_and_string_validators_reject_malformed_catalog_values():
    with pytest.raises(ValueError, match="schema is invalid"):
        _schema_fields(None, "card", "kwargs")
    with pytest.raises(ValueError, match="field is invalid"):
        _schema_fields(
            {
                "kind": "fields",
                "declared_on": None,
                "import_path": None,
                "namespace_policy": "closed",
                "fields": [{"name": "title", "required": 1}],
            },
            "card",
            "kwargs",
        )
    with pytest.raises(ValueError, match="non-empty string"):
        _required_str("", "field name")
    with pytest.raises(ValueError, match="string or None"):
        _optional_str(Path("card.py"), "python_file")

    assert _optional_str(None, "description") is None


def test_catalog_rejects_editor_relevant_cross_field_invariants(tmp_path):
    field = {
        "name": "title",
        "required": True,
        "type_display": "str",
        "type_fidelity": "normalized",
        "default_kind": "missing",
        "default_value_state": "not-applicable",
        "default_value": None,
        "description": None,
        "source_module": "tests.cards",
        "source_qualname": "Card.Kwargs",
        "source_file": str((tmp_path / "cards.py").resolve()),
    }
    valid = _component()
    schemas = valid["schemas"]
    assert isinstance(schemas, dict)
    schemas["kwargs"] = _schema(fields=[field])

    malformed: list[dict[str, object]] = []

    absent_with_fields = deepcopy(valid)
    absent_schema = absent_with_fields["schemas"]["kwargs"]
    absent_schema["kind"] = "absent"
    malformed.append(_catalog(absent_with_fields))

    contradictory_field = deepcopy(valid)
    contradictory_field["schemas"]["kwargs"]["fields"][0]["default_kind"] = "value"
    malformed.append(_catalog(contradictory_field))

    partial_source = deepcopy(valid)
    partial_source["schemas"]["kwargs"]["fields"][0]["source_qualname"] = None
    malformed.append(_catalog(partial_source))

    relative_source = deepcopy(valid)
    relative_source["schemas"]["kwargs"]["fields"][0]["source_file"] = "cards.py"
    malformed.append(_catalog(relative_source))

    non_utf8_text = deepcopy(valid)
    non_utf8_text["description"] = "bad\ud800"
    malformed.append(_catalog(non_utf8_text))

    invalid_asset = deepcopy(valid)
    invalid_asset["assets"]["template"] = {
        **_asset(),
        "kind": "inline",
        "declared_on": "tests.Card",
        "resolution": "resolved",
    }
    malformed.append(_catalog(invalid_asset))

    wrong_engine = deepcopy(valid)
    wrong_engine["engine_id"] = "other.engine"
    malformed.append(_catalog(wrong_engine))

    invalid_extension = deepcopy(valid)
    invalid_extension["extensions"] = {"events": {"introspection_version": 1, "data": {}}}
    invalid_extension_catalog = _catalog(invalid_extension)
    invalid_extension_catalog["extension_versions"] = {"events": 2}
    malformed.append(invalid_extension_catalog)

    for payload in malformed:
        with pytest.raises(ValueError, match=r".+"):
            CatalogIndex(payload)


def test_catalog_freezes_default_and_extension_json(tmp_path):
    field = {
        "name": "options",
        "required": False,
        "type_display": "dict[str, object]",
        "type_fidelity": "normalized",
        "default_kind": "value",
        "default_value_state": "available",
        "default_value": {"items": [1]},
        "description": None,
        "source_module": None,
        "source_qualname": None,
        "source_file": None,
    }
    component = _component()
    component["schemas"]["kwargs"] = _schema(fields=[field])
    component["extensions"] = {"events": {"introspection_version": 1, "data": {"items": [1]}}}
    payload = _catalog(component)
    payload["extension_versions"] = {"events": 1}

    catalog = CatalogIndex(payload)
    card = catalog.components[0]

    assert card.kwargs[0].default_value == {"items": (1,)}
    assert card.extensions["events"]["data"] == {"items": (1,)}
    with pytest.raises(TypeError):
        card.kwargs[0].default_value["extra"] = True
