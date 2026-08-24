from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomllib

EXAMPLES_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = EXAMPLES_ROOT / "catalog.toml"


@dataclass(frozen=True, slots=True)
class ExampleProject:
    id: str
    kind: str
    path: Path
    host: str
    python: str
    test: tuple[str, ...]
    profile: str
    docs: tuple[str, ...]
    build: tuple[str, ...] | None = None
    serve: tuple[str, ...] | None = None
    page_path: str | None = None
    citry_prefix: str | None = None

    @property
    def source(self) -> Path:
        return EXAMPLES_ROOT / self.path

    @property
    def is_web(self) -> bool:
        return self.serve is not None


def _command(value: Any, field: str, project_id: str) -> tuple[str, ...] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{project_id}: {field} must be a non-empty string array")
    return tuple(value)


def load_catalog(path: Path = CATALOG_PATH) -> tuple[ExampleProject, ...]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError(f"{path}: unsupported catalog schema")

    projects = []
    seen = set()
    for raw in data.get("projects", []):
        project_id = raw.get("id")
        if not isinstance(project_id, str) or not project_id:
            raise ValueError(f"{path}: every project needs an id")
        if project_id in seen:
            raise ValueError(f"{path}: duplicate project id {project_id!r}")
        seen.add(project_id)
        relative = Path(raw["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"{project_id}: path must stay under examples/")
        projects.append(
            ExampleProject(
                id=project_id,
                kind=raw["kind"],
                path=relative,
                host=raw["host"],
                python=raw["python"],
                test=_command(raw.get("test"), "test", project_id) or (),
                build=_command(raw.get("build"), "build", project_id),
                serve=_command(raw.get("serve"), "serve", project_id),
                page_path=raw.get("page_path"),
                citry_prefix=raw.get("citry_prefix"),
                profile=raw["profile"],
                docs=tuple(raw.get("docs", [])),
            )
        )
    if not projects:
        raise ValueError(f"{path}: catalog contains no projects")
    return tuple(projects)


def select_projects(ids: list[str] | None) -> tuple[ExampleProject, ...]:
    projects = load_catalog()
    if not ids:
        return projects
    wanted = set(ids)
    selected = tuple(project for project in projects if project.id in wanted)
    missing = wanted - {project.id for project in selected}
    if missing:
        raise ValueError(f"Unknown example project(s): {', '.join(sorted(missing))}")
    return selected
