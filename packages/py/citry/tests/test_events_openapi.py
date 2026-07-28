"""
Tests for the events OpenAPI command (WP14): the document builder, the
``--only-data`` filter, and the command plumbing (docs/design/events.md 9).

The full-document assertion is authored observe-then-lock: build the real
document for the two-component fixture app, read it, lock it. Only the
path keys interpolate the fixture classes' ``class_id`` (a hash of their
import path); everything else is literal.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, ClassVar
from uuid import UUID

import pytest

import citry.ext.events as events_entrypoint
from citry import Citry, Component
from citry.command import run
from citry.ext.events import actions, event
from citry.ext.events.files import UploadedFile
from citry.ext.events.openapi import OpenApiCommand, build_openapi_document
from citry.ext.events.results import coerce_result

SIGNING_KEY = "test-secret-key"

_ENVELOPE_200 = {"description": "The citry-events/1 result envelope."}
_DATA_200_DESCRIPTION = (
    "The handler's data value (citry-events/1 envelope callers receive it as the result's data action)."
)
_RESPONSE_422 = {
    "description": "The args did not validate; per-field messages ride in results[0].error.fieldErrors.",
    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/EventErrorEnvelope"}}},
}
# Non-GET operations document the CSRF header, so a client generated from
# the document sends it and passes the check (design 7.4).
_HEADER_PARAMETER = {
    "name": "X-Citry-Events",
    "in": "header",
    "required": True,
    "schema": {"type": "string"},
    "description": (
        "CSRF protection of the events endpoints: JSON requests without this header"
        ' are rejected with 403. Any value passes; the citry runtime sends "1".'
    ),
}


def test_document_builder_is_not_exported_from_the_events_entrypoint() -> None:
    assert "build_openapi_document" not in events_entrypoint.__all__
    assert not hasattr(events_entrypoint, "build_openapi_document")


def _citry(**kwargs):
    c = Citry(secret=SIGNING_KEY, **kwargs)
    c.set_mounted_prefix("/citry")
    return c


def _two_component_app():
    """The fixture app: two components covering every operation shape."""
    c = _citry()

    class Priority(Enum):
        LOW = "low"
        NORMAL = "normal"

    class SearchIn:
        q: str = ""
        limit: int = 10

    class SaveIn:
        title: str
        tags: list[str]
        priority: Priority = Priority.NORMAL
        due: date | None = None

    class ContactIn:
        email: str
        message: str = ""

    class TodoList(Component):
        citry = c

        class Events:
            @event(methods=("GET",))
            def search(self, data: SearchIn) -> dict:
                """Search the list; answers the matching items."""
                return {"q": data.q, "items": []}

            def save(self, data: SaveIn) -> "dict[str, int]":
                """Save one item."""
                return {"saved": 1}

            def archive(self):
                return None

        template = """
            <ul></ul>
        """

    class ContactCard(Component):
        citry = c

        class Events:
            def submit(self, data: ContactIn, request):
                """Send the message to the site owner."""
                return {"sent": True}

            def ping(self) -> dict[str, str]:
                """
                Ping the card.

                Answers a static payload.
                """
                return {"pong": "ok"}

        template = """
            <p>card</p>
        """

    return c, TodoList, ContactCard


################################################
# THE DOCUMENT
################################################


class TestDocument:
    def test_two_component_app_full_document(self):
        c, todo, card = _two_component_app()
        document = build_openapi_document(c)
        assert document == {
            "openapi": "3.1.0",
            "info": {
                "title": "Citry events",
                "version": "citry-events/1",
                "description": (
                    "One operation per component event handler, dispatched over the per-event route."
                    ' Paths are relative to the prefix the citry routes are mounted under (for example "/citry").'
                ),
            },
            "paths": {
                f"/ext/events/e/{card.class_id}/ping": {
                    "post": {
                        "operationId": "ContactCard_ping",
                        "description": "Ping the card.\n\nAnswers a static payload.",
                        "parameters": [_HEADER_PARAMETER],
                        "responses": {
                            "200": {
                                "description": _DATA_200_DESCRIPTION,
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object", "additionalProperties": {"type": "string"}},
                                    },
                                },
                            },
                            "422": _RESPONSE_422,
                        },
                    },
                },
                f"/ext/events/e/{card.class_id}/submit": {
                    "post": {
                        "operationId": "ContactCard_submit",
                        "description": "Send the message to the site owner.",
                        "parameters": [_HEADER_PARAMETER],
                        # A JSON body on the per-event route is the flat data
                        # schema (the call envelope rides its own vendor media
                        # type); the form content type is the no-JS path.
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ContactIn"},
                                },
                                "application/x-www-form-urlencoded": {
                                    "schema": {"$ref": "#/components/schemas/ContactIn"},
                                },
                            },
                        },
                        "responses": {"200": _ENVELOPE_200, "422": _RESPONSE_422},
                    },
                },
                f"/ext/events/e/{todo.class_id}/archive": {
                    "post": {
                        "operationId": "TodoList_archive",
                        "parameters": [_HEADER_PARAMETER],
                        "responses": {"200": _ENVELOPE_200, "422": _RESPONSE_422},
                    },
                },
                f"/ext/events/e/{todo.class_id}/save": {
                    "post": {
                        "operationId": "TodoList_save",
                        "description": "Save one item.",
                        "parameters": [_HEADER_PARAMETER],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SaveIn"},
                                },
                                "application/x-www-form-urlencoded": {
                                    "schema": {"$ref": "#/components/schemas/SaveIn"},
                                },
                            },
                        },
                        "responses": {
                            "200": {
                                "description": _DATA_200_DESCRIPTION,
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object", "additionalProperties": {"type": "integer"}},
                                    },
                                },
                            },
                            "422": _RESPONSE_422,
                        },
                    },
                },
                f"/ext/events/e/{todo.class_id}/search": {
                    "get": {
                        "operationId": "TodoList_search",
                        "description": "Search the list; answers the matching items.",
                        "parameters": [
                            {"name": "q", "in": "query", "required": False, "schema": {"type": "string"}},
                            {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
                        ],
                        "responses": {
                            "200": {
                                "description": _DATA_200_DESCRIPTION,
                                "content": {"application/json": {"schema": {"type": "object"}}},
                            },
                            "422": _RESPONSE_422,
                        },
                    },
                },
            },
            "components": {
                "schemas": {
                    "ContactIn": {
                        "type": "object",
                        "properties": {"email": {"type": "string"}, "message": {"type": "string"}},
                        "additionalProperties": False,
                        "required": ["email"],
                    },
                    "EventError": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "status": {"type": "integer"},
                            "code": {"type": "string"},
                            "message": {"type": "string"},
                            "fieldErrors": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                                "description": "One message per failed field, keyed by the data-schema field path.",
                            },
                        },
                        "required": ["status", "code", "message"],
                    },
                    "EventErrorEnvelope": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "protocol": {"const": "citry-events/1"},
                            "requestId": {"type": "string"},
                            "results": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "ok": {"const": False},
                                        "sendSequence": {"type": "integer", "minimum": 0},
                                        "error": {"$ref": "#/components/schemas/EventError"},
                                    },
                                    "required": ["ok", "error"],
                                },
                            },
                        },
                        "required": ["protocol", "requestId", "results"],
                    },
                    "Priority": {"type": "string", "enum": ["low", "normal"]},
                    "SaveIn": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "priority": {"$ref": "#/components/schemas/Priority"},
                            "due": {"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]},
                        },
                        "additionalProperties": False,
                        "required": ["title", "tags"],
                    },
                    "SearchIn": {
                        "type": "object",
                        "properties": {"q": {"type": "string"}, "limit": {"type": "integer"}},
                        "additionalProperties": False,
                    },
                },
            },
        }

    def test_document_is_deterministic(self):
        c, _todo, _card = _two_component_app()
        first = json.dumps(build_openapi_document(c))
        second = json.dumps(build_openapi_document(c))
        assert first == second

    def test_operations_and_schemas_are_sorted(self):
        # Dict equality cannot see ordering, so the emission order is locked
        # on its own: components by name, events by wire name, schemas by
        # schema name.
        c, todo, card = _two_component_app()
        document = build_openapi_document(c)
        assert list(document["paths"]) == [
            f"/ext/events/e/{card.class_id}/ping",
            f"/ext/events/e/{card.class_id}/submit",
            f"/ext/events/e/{todo.class_id}/archive",
            f"/ext/events/e/{todo.class_id}/save",
            f"/ext/events/e/{todo.class_id}/search",
        ]
        assert list(document["components"]["schemas"]) == [
            "ContactIn",
            "EventError",
            "EventErrorEnvelope",
            "Priority",
            "SaveIn",
            "SearchIn",
        ]

    def test_only_data_keeps_json_returning_handlers(self):
        c, todo, card = _two_component_app()
        document = build_openapi_document(c, only_data=True)
        # archive (no annotation) and submit (unannotated return) drop out,
        # and with them the ContactIn schema nothing references anymore.
        assert sorted(document["paths"]) == [
            f"/ext/events/e/{card.class_id}/ping",
            f"/ext/events/e/{todo.class_id}/save",
            f"/ext/events/e/{todo.class_id}/search",
        ]
        assert sorted(document["components"]["schemas"]) == [
            "EventError",
            "EventErrorEnvelope",
            "Priority",
            "SaveIn",
            "SearchIn",
        ]

    def test_handler_docstrings_become_descriptions(self):
        c, todo, card = _two_component_app()
        document = build_openapi_document(c)
        save = document["paths"][f"/ext/events/e/{todo.class_id}/save"]["post"]
        assert save["description"] == "Save one item."
        # A docstring-less handler carries no description at all.
        archive = document["paths"][f"/ext/events/e/{todo.class_id}/archive"]["post"]
        assert "description" not in archive
        # Multi-line docstrings arrive dedented, exactly as inspect cleans them.
        ping = document["paths"][f"/ext/events/e/{card.class_id}/ping"]["post"]
        assert ping["description"] == "Ping the card.\n\nAnswers a static payload."

    def test_get_handler_args_become_query_parameters(self):
        c, todo, _card = _two_component_app()
        document = build_openapi_document(c)
        search = document["paths"][f"/ext/events/e/{todo.class_id}/search"]["get"]
        assert "requestBody" not in search
        assert search["parameters"] == [
            {"name": "q", "in": "query", "required": False, "schema": {"type": "string"}},
            {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
        ]

    def test_unresolvable_return_annotation_leaves_the_response_untyped(self):
        # Return annotations are advisory; one that does not resolve gets the
        # generic envelope response instead of failing the build.
        c = _citry()

        class Odd(Component):
            citry = c

            class Events:
                def poke(self) -> "NoSuchThing":  # noqa: F821 - the point of the test
                    return None

            template = """
                <p>odd</p>
            """

        document = build_openapi_document(c)
        operation = document["paths"][f"/ext/events/e/{Odd.class_id}/poke"]["post"]
        assert operation["responses"]["200"] == _ENVELOPE_200

    def test_no_event_handlers_gives_an_empty_document(self):
        c = _citry()

        class Plain(Component):
            citry = c

            template = """
                <p>plain</p>
            """

        document = build_openapi_document(c)
        assert document["paths"] == {}
        assert document["components"] == {"schemas": {}}


class TestSchemaProjection:
    def test_request_schema_covers_the_runtime_annotation_table(self):
        c = _citry()
        factory_calls = 0

        def generated_default():
            nonlocal factory_calls
            factory_calls += 1
            raise AssertionError("OpenAPI generation must not execute schema defaults")

        class TextChoice(Enum):
            FIRST = "first"
            SECOND = "second"

        class NumberChoice(Enum):
            FIRST = 1
            SECOND = 2

        class MixedChoice(Enum):
            TEXT = "text"
            NUMBER = 1

        class Nested:
            label: str

        @dataclass
        class MatrixIn:
            anything: Any
            opaque: object
            enabled: bool
            ratio: float
            bare_list: list
            bare_tuple: tuple
            bare_set: set
            bare_dict: dict
            bare_mapping: Mapping
            numbers: list[int]
            names: set[str]
            repeated: tuple[int, ...]
            pair: tuple[int, str]
            scores: dict[str, float]
            aliases: Mapping[str, str]
            identifier: UUID
            created_at: datetime
            due: date
            starts_at: time
            amount: Decimal
            upload: UploadedFile
            text_choice: TextChoice
            number_choice: NumberChoice
            mixed_choice: MixedChoice
            nested: Nested
            optional_count: int | None
            label: str = ""
            generated: list[str] = field(default_factory=generated_default)
            internal: int = field(default=0, init=False)

        class MatrixCard(Component):
            citry = c

            class Events:
                def submit(self, data: MatrixIn):
                    return None

            template = """
                <p>matrix</p>
            """

        document = build_openapi_document(c)
        operation = document["paths"][f"/ext/events/e/{MatrixCard.class_id}/submit"]["post"]
        assert operation["requestBody"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/MatrixIn",
        }
        assert document["components"]["schemas"]["MatrixIn"] == {
            "type": "object",
            "properties": {
                "anything": {},
                "opaque": {},
                "enabled": {"type": "boolean"},
                "ratio": {"type": "number"},
                "bare_list": {"type": "array"},
                "bare_tuple": {"type": "array"},
                "bare_set": {"type": "array", "uniqueItems": True},
                "bare_dict": {"type": "object"},
                "bare_mapping": {"type": "object"},
                "numbers": {"type": "array", "items": {"type": "integer"}},
                "names": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
                "repeated": {"type": "array", "items": {"type": "integer"}},
                "pair": {
                    "type": "array",
                    "prefixItems": [{"type": "integer"}, {"type": "string"}],
                    "minItems": 2,
                    "maxItems": 2,
                },
                "scores": {"type": "object", "additionalProperties": {"type": "number"}},
                "aliases": {"type": "object", "additionalProperties": {"type": "string"}},
                "identifier": {"type": "string", "format": "uuid"},
                "created_at": {"type": "string", "format": "date-time"},
                "due": {"type": "string", "format": "date"},
                "starts_at": {"type": "string", "format": "time"},
                "amount": {"type": "string", "format": "decimal"},
                "upload": {"type": "string", "format": "binary"},
                "text_choice": {"$ref": "#/components/schemas/TextChoice"},
                "number_choice": {"$ref": "#/components/schemas/NumberChoice"},
                "mixed_choice": {"$ref": "#/components/schemas/MixedChoice"},
                "nested": {"$ref": "#/components/schemas/Nested"},
                "optional_count": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                "label": {"type": "string"},
                "generated": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
            "required": [
                "anything",
                "opaque",
                "enabled",
                "ratio",
                "bare_list",
                "bare_tuple",
                "bare_set",
                "bare_dict",
                "bare_mapping",
                "numbers",
                "names",
                "repeated",
                "pair",
                "scores",
                "aliases",
                "identifier",
                "created_at",
                "due",
                "starts_at",
                "amount",
                "upload",
                "text_choice",
                "number_choice",
                "mixed_choice",
                "nested",
                "optional_count",
            ],
        }
        assert document["components"]["schemas"]["TextChoice"] == {
            "type": "string",
            "enum": ["first", "second"],
        }
        assert document["components"]["schemas"]["NumberChoice"] == {
            "type": "integer",
            "enum": [1, 2],
        }
        assert document["components"]["schemas"]["MixedChoice"] == {
            "enum": ["text", 1],
        }
        assert "internal" not in document["components"]["schemas"]["MatrixIn"]["properties"]
        assert factory_calls == 0

    def test_schema_names_reserved_names_and_recursion_are_safe(self):
        c = _citry()
        first_payload = type(
            "Payload",
            (),
            {"__module__": __name__, "__annotations__": {"first": str}},
        )
        second_payload = type(
            "Payload",
            (),
            {"__module__": __name__, "__annotations__": {"second": int}},
        )
        third_payload = type(
            "Payload",
            (),
            {"__module__": __name__, "__annotations__": {"third": bool}},
        )
        reserved_payload = type(
            "EventError",
            (),
            {"__module__": __name__, "__annotations__": {"user_message": str}},
        )
        recursive_payload = type(
            "RecursivePayload",
            (),
            {"__module__": __name__, "__annotations__": {}},
        )
        recursive_payload.__annotations__["child"] = recursive_payload | None

        class CollisionCard(Component):
            citry = c

            class Events:
                def a_first(self, data: first_payload):
                    return None

                def b_second(self, data: second_payload):
                    return None

                def c_third(self, data: third_payload):
                    return None

                def recursive(self, data: recursive_payload):
                    return None

                def reserved(self, data: reserved_payload):
                    return None

            template = """
                <p>collisions</p>
            """

        document = build_openapi_document(c)
        schemas = document["components"]["schemas"]
        assert schemas["Payload"]["properties"] == {"first": {"type": "string"}}
        assert schemas["Payload_2"]["properties"] == {"second": {"type": "integer"}}
        assert schemas["Payload_3"]["properties"] == {"third": {"type": "boolean"}}
        assert schemas["EventError"]["properties"]["status"] == {"type": "integer"}
        assert schemas["EventError_2"]["properties"] == {"user_message": {"type": "string"}}
        assert schemas["RecursivePayload"]["properties"]["child"] == {
            "anyOf": [
                {"$ref": "#/components/schemas/RecursivePayload"},
                {"type": "null"},
            ],
        }

        request_refs = {
            event_name: document["paths"][f"/ext/events/e/{CollisionCard.class_id}/{event_name}"]["post"][
                "requestBody"
            ]["content"]["application/json"]["schema"]["$ref"]
            for event_name in ("a_first", "b_second", "c_third", "recursive", "reserved")
        }
        assert request_refs == {
            "a_first": "#/components/schemas/Payload",
            "b_second": "#/components/schemas/Payload_2",
            "c_third": "#/components/schemas/Payload_3",
            "recursive": "#/components/schemas/RecursivePayload",
            "reserved": "#/components/schemas/EventError_2",
        }

    def test_same_named_components_get_unique_deterministic_operation_ids(self):
        c = _citry()

        class FirstScope:
            class Twin(Component):
                citry = c
                name = "first-twin"

                class Events:
                    def ping(self):
                        return None

                template = """
                    <p>first</p>
                """

        class SecondScope:
            class Twin(Component):
                citry = c
                name = "second-twin"

                class Events:
                    def ping(self):
                        return None

                template = """
                    <p>second</p>
                """

        document = build_openapi_document(c)
        operation_ids = [operation["post"]["operationId"] for operation in document["paths"].values()]
        assert operation_ids == ["Twin_ping", "Twin_ping_2"]
        assert json.dumps(document) == json.dumps(build_openapi_document(c))
        assert FirstScope.Twin.class_id != SecondScope.Twin.class_id

    def test_typed_returns_and_only_data_follow_the_runtime_data_channel(self):
        @dataclass
        class FirstOut:
            first: str

        @dataclass
        class SecondOut:
            second: int

        class OutputResolver:
            def resolve(self, value, events):
                if isinstance(value, FirstOut):
                    return [actions.Data({"first": value.first})]
                if isinstance(value, SecondOut):
                    return [actions.Data({"second": value.second})]
                return None

        c = _citry(event_result_resolvers=[OutputResolver()])

        class Status(Enum):
            READY = "ready"

        class ReturnCard(Component):
            citry = c

            class Events:
                def bare_dict(self) -> dict:
                    return {}

                def enum_value(self) -> Status:
                    return Status.READY

                def mapping(self) -> Mapping[str, int]:
                    return {}

                def mixed(self) -> dict[str, int] | int:
                    return {}

                def nothing(self) -> None:
                    return None

                def optional(self) -> FirstOut | None:
                    return None

                def scalar(self) -> int:
                    return 1

                def schema(self) -> FirstOut:
                    return FirstOut(first="one")

                def union(self) -> FirstOut | SecondOut:
                    return FirstOut(first="one")

            template = """
                <p>returns</p>
            """

        document = build_openapi_document(c)

        def response_schema(name):
            operation = document["paths"][f"/ext/events/e/{ReturnCard.class_id}/{name}"]["post"]
            return operation["responses"]["200"].get("content", {}).get("application/json", {}).get("schema")

        assert response_schema("bare_dict") == {"type": "object"}
        assert response_schema("mapping") == {"type": "object", "additionalProperties": {"type": "integer"}}
        assert response_schema("optional") == {"$ref": "#/components/schemas/FirstOut"}
        assert response_schema("schema") == {"$ref": "#/components/schemas/FirstOut"}
        assert response_schema("union") == {
            "anyOf": [
                {"$ref": "#/components/schemas/FirstOut"},
                {"$ref": "#/components/schemas/SecondOut"},
            ],
        }
        for name in ("enum_value", "mixed", "nothing", "scalar"):
            assert response_schema(name) is None

        coerced = coerce_result(
            FirstOut(first="one"),
            resolvers=c.settings.event_result_resolvers,
            handler="schema",
        )
        assert len(coerced) == 1
        assert isinstance(coerced[0], actions.Data)
        assert coerced[0].value == {"first": "one"}

        only_data = build_openapi_document(c, only_data=True)
        assert set(only_data["paths"]) == {
            f"/ext/events/e/{ReturnCard.class_id}/bare_dict",
            f"/ext/events/e/{ReturnCard.class_id}/mapping",
            f"/ext/events/e/{ReturnCard.class_id}/optional",
            f"/ext/events/e/{ReturnCard.class_id}/schema",
            f"/ext/events/e/{ReturnCard.class_id}/union",
        }

    def test_get_without_data_or_with_an_empty_schema_omits_empty_input_sections(self):
        c = _citry()

        class EmptyIn:
            marker: ClassVar[int] = 1

        class ReadCard(Component):
            citry = c

            class Events:
                @event(methods=("GET",))
                def empty(self, data: EmptyIn):
                    return None

                @event(methods=("GET",))
                def ping(self):
                    return None

            template = """
                <p>read</p>
            """

        document = build_openapi_document(c)
        for event_name in ("empty", "ping"):
            operation = document["paths"][f"/ext/events/e/{ReadCard.class_id}/{event_name}"]["get"]
            assert "parameters" not in operation
            assert "requestBody" not in operation


class TestPydanticSchemas:
    def test_pydantic_model_schema_is_delegated_to_pydantic(self):
        pydantic = pytest.importorskip("pydantic", reason="exercises the Pydantic delegation")

        class PydanticResolver:
            def resolve(self, value, events):
                if isinstance(value, pydantic.BaseModel):
                    return [actions.Data(value.model_dump(mode="json"))]
                return None

        c = _citry(event_result_resolvers=[PydanticResolver()])

        class ContactModel(pydantic.BaseModel):
            email: str
            message: str = ""

        class Card(Component):
            citry = c

            class Events:
                def submit(self, data: ContactModel) -> ContactModel:
                    return data

            template = """
                <p>card</p>
            """

        document = build_openapi_document(c)
        operation = document["paths"][f"/ext/events/e/{Card.class_id}/submit"]["post"]
        ref = {"$ref": "#/components/schemas/ContactModel"}
        # The request documents flat JSON and the form content type (the
        # call envelope rides its own vendor media type); the response is JSON.
        assert operation["requestBody"]["content"] == {
            "application/json": {"schema": ref},
            "application/x-www-form-urlencoded": {"schema": ref},
        }
        assert operation["responses"]["200"]["content"]["application/json"]["schema"] == ref
        # The named entry is Pydantic's own JSON Schema (shape-checked, not
        # locked: its exact output belongs to Pydantic's version).
        named = document["components"]["schemas"]["ContactModel"]
        assert set(named["properties"]) == {"email", "message"}
        assert named["required"] == ["email"]

        model = ContactModel(email="a@example.com")
        coerced = coerce_result(model, resolvers=c.settings.event_result_resolvers, handler="submit")
        assert len(coerced) == 1
        assert isinstance(coerced[0], actions.Data)
        assert coerced[0].value == {"email": "a@example.com", "message": ""}

    def test_nested_definitions_are_lifted_once_for_multiple_models(self):
        pydantic = pytest.importorskip("pydantic", reason="exercises nested Pydantic schemas")
        c = _citry()

        class AddressModel(pydantic.BaseModel):
            city: str

        class ContactModel(pydantic.BaseModel):
            address: AddressModel

        class DeliveryModel(pydantic.BaseModel):
            address: AddressModel

        class Card(Component):
            citry = c

            class Events:
                def contact(self, data: ContactModel):
                    return None

                def delivery(self, data: DeliveryModel):
                    return None

            template = """
                <p>card</p>
            """

        schemas = build_openapi_document(c)["components"]["schemas"]
        assert "$defs" not in schemas["ContactModel"]
        assert "$defs" not in schemas["DeliveryModel"]
        assert schemas["ContactModel"]["properties"]["address"] == {
            "$ref": "#/components/schemas/AddressModel",
        }
        assert schemas["DeliveryModel"]["properties"]["address"] == {
            "$ref": "#/components/schemas/AddressModel",
        }
        assert schemas["AddressModel"]["properties"]["city"]["type"] == "string"

    def test_nested_definition_name_conflict_raises_a_pointed_error(self):
        pydantic = pytest.importorskip("pydantic", reason="exercises nested Pydantic schemas")
        c = _citry()
        plain_address = type(
            "AddressModel",
            (),
            {"__module__": __name__, "__annotations__": {"postal_code": str}},
        )

        class AddressModel(pydantic.BaseModel):
            city: str

        class ContactModel(pydantic.BaseModel):
            address: AddressModel

        class Card(Component):
            citry = c

            class Events:
                def a_plain(self, data: plain_address):
                    return None

                def b_contact(self, data: ContactModel):
                    return None

            template = """
                <p>card</p>
            """

        with pytest.raises(ValueError, match="Pydantic nested model clashes with another schema class"):
            build_openapi_document(c)


################################################
# THE COMMAND
################################################


class TestCommand:
    def test_writes_the_document_to_out(self, tmp_path, capsys):
        c, todo, _card = _two_component_app()
        target = tmp_path / "openapi.json"
        exit_code = run(OpenApiCommand, ["--out", str(target)], citry=c)
        assert exit_code == 0
        document = json.loads(target.read_text(encoding="utf-8"))
        assert document == build_openapi_document(c)
        assert f"/ext/events/e/{todo.class_id}/save" in document["paths"]
        assert str(target) in capsys.readouterr().out

    def test_prints_the_document_to_stdout_by_default(self, capsys):
        c, _todo, card = _two_component_app()
        run(OpenApiCommand, [], citry=c)
        printed = json.loads(capsys.readouterr().out)
        assert printed == build_openapi_document(c)
        assert f"/ext/events/e/{card.class_id}/ping" in printed["paths"]

    def test_only_data_flag_filters_the_output(self, capsys):
        c, todo, _card = _two_component_app()
        run(OpenApiCommand, ["--only-data"], citry=c)
        printed = json.loads(capsys.readouterr().out)
        assert printed == build_openapi_document(c, only_data=True)
        assert f"/ext/events/e/{todo.class_id}/archive" not in printed["paths"]

    def test_without_an_engine_exits_1_and_points_at_the_cli(self, capsys):
        # Failure exits 1 like the sibling commands, so a scripted run cannot
        # mistake "nothing was written" for success.
        with pytest.raises(SystemExit) as exc:
            run(OpenApiCommand, [], citry=None)
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "citry ext run events openapi" in captured.err

    def test_registered_on_the_events_extension(self):
        c = _citry()
        assert OpenApiCommand in c.commands["events"]
