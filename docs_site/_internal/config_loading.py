"""Small strict-loading helpers shared by docs-site configuration files."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


class DocsConfigError(ValueError):
    """A maintainer-facing docs configuration file is invalid."""


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise DocsConfigError(f"duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_yaml(path: Path) -> Any:
    """Load YAML while rejecting duplicate mapping keys."""
    if not path.is_file():
        raise DocsConfigError(f"docs configuration file does not exist: {path}")
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DocsConfigError(f"cannot read YAML configuration {path}: {exc}") from exc
    try:
        return yaml.load(source, Loader=_UniqueKeyLoader)  # noqa: S506 - safe subclass
    except DocsConfigError as exc:
        raise DocsConfigError(f"{path}: {exc}") from exc
    except (TypeError, yaml.YAMLError) as exc:
        raise DocsConfigError(f"invalid YAML in {path}: {exc}") from exc


def require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise DocsConfigError(f"{label} must be a mapping with string keys")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise DocsConfigError(f"{label} must be a list")
    return value


def require_keys(
    value: Mapping[str, Any],
    label: str,
    *,
    required: set[str] | frozenset[str] = frozenset(),
    optional: set[str] | frozenset[str] = frozenset(),
) -> None:
    keys = set(value)
    missing = required - keys
    unknown = keys - required - optional
    if missing:
        raise DocsConfigError(f"{label} is missing required key(s): {', '.join(sorted(missing))}")
    if unknown:
        raise DocsConfigError(f"{label} has unknown key(s): {', '.join(sorted(unknown))}")


def require_str(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        suffix = "a string" if allow_empty else "a non-empty string"
        raise DocsConfigError(f"{label} must be {suffix}")
    return value


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise DocsConfigError(f"{label} must be a boolean")
    return value


def require_int(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise DocsConfigError(f"{label} must be an integer greater than or equal to {minimum}")
    return value


def require_str_list(value: Any, label: str) -> tuple[str, ...]:
    items = require_list(value, label)
    result = tuple(require_str(item, f"{label}[{index}]") for index, item in enumerate(items))
    if len(result) != len(set(result)):
        raise DocsConfigError(f"{label} contains duplicate values")
    return result


def require_relative_posix_path(value: Any, label: str, *, suffix: str | None = None) -> PurePosixPath:
    raw = require_str(value, label)
    path = PurePosixPath(raw)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise DocsConfigError(f"{label} must be a safe repository-relative POSIX path")
    if suffix is not None and path.suffix != suffix:
        raise DocsConfigError(f"{label} must end in {suffix}")
    return path
