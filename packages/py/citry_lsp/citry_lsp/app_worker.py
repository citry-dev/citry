"""One-shot, transport-isolated Citry app discovery worker."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
import tempfile
import tokenize
from functools import cache, lru_cache
from pathlib import Path
from types import FunctionType, ModuleType
from typing import TYPE_CHECKING, Any, Literal

from citry import Citry, ComponentLibrary
from citry._class_introspection import _safe_class_text, _static_class_dict, _static_class_mro
from citry._component_introspection import _loaded_python_file
from citry._linting import _component_lint_variable_owners
from citry._schema_introspection import _inspect_schema_class
from citry.analysis import (
    python_application_lint_variable_range,
    python_class_asset_resolution_signature,
    python_class_direct_method_first_line,
    python_class_resolution_signature,
    python_class_static_asset_matches,
    python_component_lint_variable_range,
)
from citry.assets import _find_pair_declaration
from citry.ext.events.extension import _component_events_info

if TYPE_CHECKING:
    from citry import TemplateAnalysis
    from citry.introspection import ComponentCatalog

_SOURCE_ANALYSIS_VERSION = 1


def _load_target(spec: str) -> Any:
    module_name, separator, attribute = spec.partition(":")
    if not separator or not module_name or not attribute:
        msg = "app must be 'module:attribute', e.g. 'myproject.app:engine'"
        raise ValueError(msg)
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


def _library_engine(library: ComponentLibrary, spec: str) -> Citry:
    # Disabling discovery keeps the copied registry limited to Citry's built-ins
    # and the one library the editor explicitly selected.
    engine = Citry(autodiscover=False)
    try:
        engine.register_library(library)
    except ValueError as exc:
        # Only declared missing requirements justify wrapper guidance. Other
        # installation errors must keep their own diagnosis unchanged.
        missing_requirement = any(_extension_is_missing(engine, name) for name in library.required_extensions)
        if not missing_requirement:
            raise
        msg = (
            f"{exc} Library-only discovery does not include host-provided extensions; expose a configured "
            "Citry instance that installs this library and its required extensions, then point citry.app "
            f"to that instance instead of {spec!r}."
        )
        raise ValueError(msg) from exc
    return engine


def _extension_is_missing(engine: Citry, name: str) -> bool:
    """Return whether one declared library requirement needs a host app."""
    try:
        engine.extensions.get_extension(name)
    except ValueError:
        return True
    return False


def _error_message(exc: BaseException) -> str:
    detail = str(exc)
    kind = type(exc).__name__
    return f"{kind}: {detail}" if detail else kind


def _run(app: str, workspace: Path) -> dict[str, object]:
    os.chdir(workspace)
    workspace_text = str(workspace)
    if workspace_text not in sys.path:
        sys.path.insert(0, workspace_text)
    target = _load_target(app)
    # A real app keeps its configured state; a portable library gets the
    # deliberately narrower engine described by the editor setting.
    if isinstance(target, Citry):
        engine = target
        target_info = {"kind": "citry"}
    elif isinstance(target, ComponentLibrary):
        engine = _library_engine(target, app)
        target_info = {"kind": "component-library", "name": target.name}
    else:
        msg = f"app target {app!r} is {type(target).__name__}, not a Citry instance or ComponentLibrary"
        raise TypeError(msg)
    # Only copied analysis records cross back into the long-lived LSP process.
    analysis = engine.template_analysis()
    catalog = engine.inspect_components(
        include_builtins=True,
        resolve_assets=True,
        include_extensions=("events",),
    )
    return {
        "ok": True,
        "target": target_info,
        "analysis": analysis.to_dict(),
        "catalog": catalog.to_dict(),
        "source_analysis": _source_analysis(engine, catalog, analysis, app),
    }


def _source_analysis(
    engine: Citry,
    catalog: ComponentCatalog,
    analysis: TemplateAnalysis,
    app: str,
) -> dict[str, object]:
    """Copy static method-resolution provenance without retaining project objects."""
    by_definition: dict[str, type] = {}
    for component_class in engine.components.values():
        definition_id = _static_class_dict(component_class).get("_definition_id")
        if type(definition_id) is str:
            by_definition[definition_id] = component_class
    components: list[dict[str, object]] = []
    application_lint = _application_lint_sources(app, analysis)
    for component in catalog.components:
        selected_class = by_definition.get(component.definition_id)
        template_data_chain = (
            _data_resolution_chain(selected_class, engine, "template_data") if selected_class else None
        )
        css_data_chain = _data_resolution_chain(selected_class, engine, "css_data") if selected_class else None
        js_data_chain = _data_resolution_chain(selected_class, engine, "js_data") if selected_class else None
        template_asset_chain = _asset_resolution_chain(selected_class, engine, "template") if selected_class else None
        css_asset_chain = _asset_resolution_chain(selected_class, engine, "css") if selected_class else None
        js_asset_chain = _asset_resolution_chain(selected_class, engine, "js") if selected_class else None
        components.append(
            {
                "definition_id": component.definition_id,
                "template_data": {"resolution_chain": template_data_chain},
                "css_data": {"resolution_chain": css_data_chain},
                "js_data": {"resolution_chain": js_data_chain},
                "template_asset": {"resolution_chain": template_asset_chain},
                "css_asset": {"resolution_chain": css_asset_chain},
                "js_asset": {"resolution_chain": js_asset_chain},
                "events": _event_sources(selected_class) if selected_class else {"handlers": None, "state": None},
                "template_lint": {
                    "variables": _component_lint_sources(
                        selected_class,
                        analysis,
                        component.definition_id,
                        application_lint,
                    )
                },
            }
        )
    return {"version": _SOURCE_ANALYSIS_VERSION, "components": components}


def _event_sources(component_class: type) -> dict[str, object]:
    """Copy exact handler and public State origins without retaining project objects."""
    info = _component_events_info(component_class)
    if info is None:
        return {"handlers": [], "state": []}
    handlers: list[dict[str, str]] = []
    for wire_name, handler in info.handlers.items():
        func = handler.func
        module_name = getattr(func, "__module__", None)
        qualname = getattr(func, "__qualname__", None)
        source_name = inspect.getsourcefile(func)
        if (
            type(module_name) is not str
            or type(qualname) is not str
            or not qualname
            or "<locals>" in qualname
            or type(source_name) is not str
        ):
            return {"handlers": None, "state": None}
        source_file = Path(source_name).resolve()
        if not source_file.is_file() or qualname.rsplit(".", 1)[-1] != handler.method_name:
            return {"handlers": None, "state": None}
        handlers.append(
            {
                "name": wire_name,
                "method_name": handler.method_name,
                "module": module_name,
                "qualname": qualname,
                "file": source_file.as_posix(),
            }
        )
    if info.state_cls is None or info.state_meta is None:
        state: list[dict[str, object]] | None = []
    else:
        inspected = _inspect_schema_class(info.state_cls)
        if inspected is None:
            state = None
        else:
            state = []
            public = set(info.state_meta.public)
            for field in inspected:
                if field.name not in public:
                    continue
                if field.source_module is None or field.source_qualname is None or field.source_file is None:
                    state = None
                    break
                state.append(
                    {
                        "name": field.name,
                        "type_display": field.type_display,
                        "description": field.description,
                        "module": field.source_module,
                        "qualname": field.source_qualname,
                        "file": field.source_file.resolve().as_posix(),
                    }
                )
    return {"handlers": handlers, "state": state}


def _application_lint_sources(app: str, analysis: TemplateAnalysis) -> dict[str, dict[str, str]]:
    """Prove direct application settings without attempting Python evaluation."""
    module_name, _separator, target_name = app.partition(":")
    module = sys.modules.get(module_name)
    source_file = _loaded_module_file(module)
    if source_file is None:
        return {}
    source = _python_source(source_file)
    if source is None:
        return {}
    definitions: dict[str, dict[str, str]] = {}
    for variable in analysis.lint.template_variables:
        if variable.source != "application":
            continue
        if python_application_lint_variable_range(source, target_name, variable.name) is None:
            continue
        definitions[variable.name] = {
            "name": variable.name,
            "kind": "application",
            "owner": target_name,
            "file": source_file.as_posix(),
        }
    return definitions


def _component_lint_sources(
    selected_class: type | None,
    analysis: TemplateAnalysis,
    definition_id: str,
    application_lint: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    """Copy only variable origins proven by direct authored mappings."""
    lint = analysis.component_lint.get(definition_id)
    if lint is None:
        return []
    component_owners = _component_lint_variable_owners(selected_class) if selected_class is not None else {}
    definitions: list[dict[str, str]] = []
    for variable in lint.template_variables:
        if variable.source == "application":
            definition = application_lint.get(variable.name)
            if definition is not None:
                definitions.append(definition)
            continue
        if variable.source != "component":
            continue
        owner = component_owners.get(variable.name)
        source_file = _loaded_python_file(owner) if owner is not None else None
        owner_name = _safe_class_text(owner, "__qualname__") if owner is not None else None
        source = _python_source(source_file) if source_file is not None else None
        if (
            source_file is None
            or owner_name is None
            or source is None
            or python_component_lint_variable_range(source, owner_name, variable.name) is None
        ):
            continue
        definitions.append(
            {
                "name": variable.name,
                "kind": "component",
                "owner": owner_name,
                "file": source_file.as_posix(),
            }
        )
    return sorted(definitions, key=lambda item: item["name"])


def _loaded_module_file(module: ModuleType | None) -> Path | None:
    """Return one authored Python module path without importing another module."""
    if module is None:
        return None
    try:
        filename = inspect.getsourcefile(module)
    except (TypeError, OSError):
        return None
    if not filename:
        return None
    try:
        path = Path(filename).resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    return path if path.is_file() else None


def _data_resolution_chain(
    component_class: type,
    engine: Citry,
    method_name: str,
) -> list[dict[str, str]] | None:
    """Return concrete-to-owner provenance for one exact data method."""
    chain: list[dict[str, str]] = []
    mro = _static_class_mro(component_class)
    for index, candidate in enumerate(mro):
        namespace = _static_class_dict(candidate)
        source_record = _source_class_record(candidate)
        if source_record is None:
            return None
        record, source, source_file, module, qualname = source_record
        # ComponentLibrary materialization creates one positively marked,
        # engine-owned wrapper with no authored AST node of its own. Skip only
        # that wrapper; equal source text alone cannot prove generated classes
        # are equivalent to their authored bases.
        next_is_library_definition = (
            index + 1 < len(mro)
            and _static_class_dict(mro[index + 1]).get("_citry_is_library_component_definition") is True
        )
        materialized_library_wrapper = (
            index == 0
            and namespace.get("_citry_owner") is engine
            and namespace.get("_citry_is_library_component_definition") is False
            and next_is_library_definition
            and method_name not in namespace
        )
        if not materialized_library_wrapper:
            chain.append(record)
        if method_name in namespace:
            method = namespace[method_name]
            if (
                type(method) is not FunctionType
                or method.__module__ != module
                or method.__qualname__ != f"{qualname}.{method_name}"
                or not _code_file_matches(method, source_file)
                or python_class_direct_method_first_line(source, qualname, method_name)
                != method.__code__.co_firstlineno
            ):
                return None
            return chain
    return None


def _asset_resolution_chain(
    component_class: type,
    engine: Citry,
    kind: Literal["template", "js", "css"],
) -> list[dict[str, str]] | None:
    """Return complete concrete-to-owner provenance for one authored asset."""
    owner, inline_value, file_value = _find_pair_declaration(component_class, kind, f"{kind}_file")
    chain: list[dict[str, str]] = []
    mro = _static_class_mro(component_class)
    for index, candidate in enumerate(mro):
        source_record = _source_class_record(candidate, asset_kind=kind)
        if source_record is None:
            return None
        record, source, _source_file, _module, qualname = source_record
        if not _is_materialized_library_wrapper(candidate, mro, index, engine):
            chain.append(record)
        if candidate is owner:
            if not python_class_static_asset_matches(source, qualname, inline_value, file_value, kind):
                return None
            return chain
    return None


@cache
def _source_class_record(
    candidate: type,
    *,
    asset_kind: Literal["template", "js", "css"] | None = None,
) -> tuple[dict[str, str], str, Path, str, str] | None:
    """Copy and memoize one class fingerprint for this one-shot worker."""
    module = _safe_class_text(candidate, "__module__")
    qualname = _safe_class_text(candidate, "__qualname__")
    source_file = _loaded_python_file(candidate)
    if module is None or qualname is None or source_file is None or not source_file.is_absolute():
        return None
    source = _python_source(source_file)
    if source is None:
        return None
    resolution = (
        python_class_asset_resolution_signature(source, qualname, asset_kind)
        if asset_kind is not None
        else python_class_resolution_signature(source, qualname)
    )
    if resolution is None:
        return None
    return (
        {
            "module": module,
            "qualname": qualname,
            "file": source_file.as_posix(),
            "resolution": resolution,
        },
        source,
        source_file,
        module,
        qualname,
    )


def _is_materialized_library_wrapper(
    candidate: type,
    mro: tuple[type, ...],
    index: int,
    engine: Citry,
) -> bool:
    """Identify only Citry's positively marked engine-owned library wrapper."""
    namespace = _static_class_dict(candidate)
    next_is_library_definition = (
        index + 1 < len(mro)
        and _static_class_dict(mro[index + 1]).get("_citry_is_library_component_definition") is True
    )
    return (
        index == 0
        and namespace.get("_citry_owner") is engine
        and namespace.get("_citry_is_library_component_definition") is False
        and next_is_library_definition
        and "template_data" not in namespace
    )


def _code_file_matches(method: FunctionType, source_file: Path) -> bool:
    """Prove a function code object came from the claimed authored file."""
    filename = method.__code__.co_filename
    if not filename or (filename.startswith("<") and filename.endswith(">")):
        return False
    try:
        code_file = Path(filename)
        if not code_file.is_absolute():
            code_file = code_file.absolute()
        return code_file.resolve() == source_file.resolve()
    except (OSError, RuntimeError, ValueError):
        return False


@lru_cache(maxsize=128)
def _python_source(source_file: Path) -> str | None:
    """Read one already-loaded Python module with its declared encoding."""
    try:
        with tokenize.open(source_file) as source_stream:
            return source_stream.read()
    except (OSError, SyntaxError, UnicodeError):
        return None


def _captured_worker(app: str, workspace: Path) -> dict[str, object]:
    """Capture Python and file-descriptor output while project code runs."""
    stdout_fd = os.dup(1)
    stderr_fd = os.dup(2)
    try:
        with tempfile.TemporaryFile(mode="w+b") as output:
            os.dup2(output.fileno(), 1)
            os.dup2(output.fileno(), 2)
            try:
                payload = _run(app, workspace)
            except (BaseException, SystemExit) as exc:  # noqa: BLE001 - worker serializes all project failures
                payload = {"ok": False, "error": _error_message(exc)}
            finally:
                sys.stdout.flush()
                sys.stderr.flush()
            output.seek(0)
            captured = output.read(16384).decode("utf-8", errors="replace").strip()
            if captured:
                payload["project_output"] = captured
    finally:
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        os.close(stderr_fd)
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True).encode("utf-8")
    os.write(stdout_fd, encoded)
    os.write(stdout_fd, b"\n")
    os.close(stdout_fd)
    return payload


def main(argv: list[str] | None = None) -> int:
    """Load one app and emit one JSON envelope to the parent server."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--app", required=True)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args(argv)
    payload = _captured_worker(args.app, args.workspace.resolve())
    return 0 if payload.get("ok") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__: list[str] = []
