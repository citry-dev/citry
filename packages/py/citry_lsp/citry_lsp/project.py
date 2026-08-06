"""Bounded project discovery and server-side registry state."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from citry import TemplateAnalysis
from citry_lsp.catalog import CatalogIndex
from citry_lsp.protocol import (
    CATALOG_SCHEMA_VERSION,
    SUPPORTED_CITRY_SERIES,
    ProjectStatus,
)

if TYPE_CHECKING:
    from pathlib import Path

    from citry_lsp.catalog import ComponentRecord

WORKER_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True, slots=True)
class ProjectState:
    """One immutable project-analysis generation."""

    status: ProjectStatus
    analysis: TemplateAnalysis | None = None
    catalog: CatalogIndex | None = None
    _slot_data_fields: dict[str, dict[str, tuple[str, ...]]] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Index portable slot-data rules once for completion and hover."""
        indexed: dict[str, dict[str, tuple[str, ...]]] = {}
        if self.analysis is not None:
            raw_rules = self.analysis.to_dict().get("tag_rules")
            if type(raw_rules) is dict:
                for tag_name, raw_rule in raw_rules.items():
                    if type(tag_name) is not str or type(raw_rule) is not dict:
                        continue
                    raw_slots = raw_rule.get("slot_data_fields")
                    if type(raw_slots) is not dict:
                        continue
                    slots: dict[str, tuple[str, ...]] = {}
                    for slot_name, raw_fields in raw_slots.items():
                        if (
                            type(slot_name) is str
                            and type(raw_fields) is list
                            and all(type(item) is str for item in raw_fields)
                        ):
                            slots[slot_name] = tuple(raw_fields)
                    indexed[tag_name.lower()] = slots
        object.__setattr__(self, "_slot_data_fields", indexed)

    def component_slot_data_fields(
        self,
        component: ComponentRecord,
        slot_name: str,
    ) -> tuple[str, ...] | None:
        """Return a known slot-data field set, preserving known empty shapes."""
        for registered_name in component.registered_names:
            slots = self._slot_data_fields.get(f"c-{registered_name}".lower())
            if slots is not None and slot_name in slots:
                return slots[slot_name]
        return None


def load_project(workspace: Path, app: str | None, *, timeout: float = WORKER_TIMEOUT_SECONDS) -> ProjectState:
    """Load registry facts through a bounded worker or select syntax-only mode."""
    workspace = workspace.resolve()
    if app is None:
        return ProjectState(
            ProjectStatus(
                interpreter=sys.executable,
                workspace=str(workspace),
                mode="syntax-only",
                message="No Citry app configured; registry-derived checks and editor features are disabled.",
            )
        )
    command = [
        sys.executable,
        "-m",
        "citry_lsp.app_worker",
        "--app",
        app,
        "--workspace",
        str(workspace),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return _failure(workspace, app, f"App discovery exceeded the {timeout:g}s startup limit.")
    if not completed.stdout.strip():
        detail = completed.stderr.strip()
        message = f"App worker exited with status {completed.returncode} without a response."
        if detail:
            message = f"{message} {detail[:1000]}"
        return _failure(workspace, app, message)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return _failure(workspace, app, f"App worker returned invalid JSON: {exc}")
    if type(payload) is not dict or payload.get("ok") is not True:
        worker_detail: object = payload.get("error") if type(payload) is dict else None
        message = str(worker_detail or f"App worker exited with status {completed.returncode}.")
        return _failure(workspace, app, message)
    raw_catalog = payload.get("catalog")
    if type(raw_catalog) is dict:
        raw_schema_version = raw_catalog.get("schema_version")
        if type(raw_schema_version) is int and raw_schema_version != CATALOG_SCHEMA_VERSION:
            raw_citry_version = raw_catalog.get("citry_version")
            return _failure(
                workspace,
                app,
                f"Component catalog schema {raw_schema_version} is unsupported.",
                citry_version=raw_citry_version if type(raw_citry_version) is str else None,
                catalog_schema_version=raw_schema_version,
            )
    try:
        analysis = TemplateAnalysis.from_dict(payload.get("analysis"))
        catalog = CatalogIndex(raw_catalog)
    except (TypeError, ValueError) as exc:
        return _failure(workspace, app, f"App worker protocol mismatch: {exc}")
    series = _version_series(catalog.citry_version)
    if series != SUPPORTED_CITRY_SERIES:
        expected = ".".join(str(part) for part in SUPPORTED_CITRY_SERIES)
        return _failure(
            workspace,
            app,
            f"Citry {catalog.citry_version} is outside this server's supported {expected}.x series.",
            citry_version=catalog.citry_version,
            catalog_schema_version=catalog.schema_version,
        )
    if catalog.schema_version != CATALOG_SCHEMA_VERSION:
        return _failure(
            workspace,
            app,
            f"Component catalog schema {catalog.schema_version} is unsupported.",
            citry_version=catalog.citry_version,
            catalog_schema_version=catalog.schema_version,
        )
    project_output = payload.get("project_output")
    status_message: str | None = (
        f"Project output was captured during discovery: {project_output}" if project_output else None
    )
    return ProjectState(
        ProjectStatus(
            interpreter=sys.executable,
            workspace=str(workspace),
            app=app,
            mode="registry",
            registry_ready=True,
            citry_version=catalog.citry_version,
            catalog_schema_version=catalog.schema_version,
            message=status_message,
        ),
        analysis=analysis,
        catalog=catalog,
    )


def _failure(
    workspace: Path,
    app: str,
    message: str,
    *,
    citry_version: str | None = None,
    catalog_schema_version: int | None = None,
) -> ProjectState:
    return ProjectState(
        ProjectStatus(
            interpreter=sys.executable,
            workspace=str(workspace),
            app=app,
            mode="syntax-only",
            registry_ready=False,
            citry_version=citry_version,
            catalog_schema_version=catalog_schema_version,
            message=f"App unavailable; using syntax-only analysis. {message}",
        )
    )


def _version_series(version: str) -> tuple[int, int] | None:
    try:
        major, minor, *_ = version.split(".")
        return int(major), int(minor)
    except (TypeError, ValueError):
        return None


__all__ = ["WORKER_TIMEOUT_SECONDS", "ProjectState", "load_project"]
