"""HTTP delivery for the i18n browser runtime and exact catalog partitions."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from citry.util.routing import RouteResponse, URLRoute

from .emission import MESSAGES_PATH, RUNTIME_PATH, client_runtime_resource

if TYPE_CHECKING:
    from citry.util.routing import RouteRequest

    from .extension import I18nExtension

_JSON_TYPE = "application/json"
_NO_STORE = (("Cache-Control", "no-store"),)
_MAX_REQUEST_BYTES = 64 * 1024
_MAX_ROOTS = 512


def i18n_routes(extension: I18nExtension) -> list[URLRoute]:
    """Return the browser-runtime and message-partition routes."""

    def serve_runtime(_request: RouteRequest) -> RouteResponse:
        return client_runtime_resource(extension.citry).response()

    def serve_messages(request: RouteRequest) -> RouteResponse:
        try:
            payload = _decode_request(request)
            if payload["catalog_revision"] != extension.catalog_revision:
                raise ValueError("the requested catalog revision is stale")
            artifact = extension.browser_artifact(
                locale=cast("str", payload["locale"]),
                outputs=cast("tuple[str, ...]", payload["outputs"]),
                messages=cast("tuple[str, ...]", payload["messages"]),
            )
        except (TypeError, ValueError) as error:
            body = json.dumps(
                {"error": {"code": "I18N_BROWSER_REQUEST_INVALID", "message": str(error)}},
                separators=(",", ":"),
            )
            return RouteResponse(content=body, content_type=_JSON_TYPE, status=400, headers=_NO_STORE)
        return RouteResponse(
            content=json.dumps(artifact, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
            content_type=_JSON_TYPE,
            headers=_NO_STORE,
        )

    return [
        URLRoute(RUNTIME_PATH, handler=serve_runtime, name="citry_i18n_runtime", methods=("GET",)),
        URLRoute(MESSAGES_PATH, handler=serve_messages, name="citry_i18n_messages", methods=("POST",)),
    ]


def _decode_request(request: RouteRequest) -> dict[str, object]:
    if len(request.body) > _MAX_REQUEST_BYTES:
        raise ValueError(f"i18n browser request exceeds {_MAX_REQUEST_BYTES} bytes")
    if request.content_type.split(";", 1)[0].strip().lower() != _JSON_TYPE:
        raise ValueError("i18n browser requests require Content-Type application/json")
    try:
        value = json.loads(request.body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("i18n browser request is not valid UTF-8 JSON") from error
    if type(value) is not dict or set(value) != {
        "catalog_revision",
        "locale",
        "messages",
        "outputs",
        "schema_version",
    }:
        raise ValueError("i18n browser request has unknown or missing fields")
    data = cast("dict[str, Any]", value)
    if data["schema_version"] != 1:
        raise ValueError("i18n browser request schema_version must be 1")
    if type(data["catalog_revision"]) is not str or not data["catalog_revision"]:
        raise ValueError("i18n browser request catalog_revision must be a non-empty string")
    if type(data["locale"]) is not str or not data["locale"]:
        raise ValueError("i18n browser request locale must be a non-empty string")
    for field in ("outputs", "messages"):
        raw = data[field]
        if type(raw) is not list or len(raw) > _MAX_ROOTS:
            raise ValueError(f"i18n browser request {field} must be a list of at most {_MAX_ROOTS} strings")
        if any(type(item) is not str or not item for item in raw):
            raise ValueError(f"i18n browser request {field} must contain only non-empty strings")
        if len(set(raw)) != len(raw):
            raise ValueError(f"i18n browser request {field} contains duplicates")
        data[field] = tuple(raw)
    return data


__all__ = ["i18n_routes"]
