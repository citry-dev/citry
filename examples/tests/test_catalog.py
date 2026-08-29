import json

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by the Python 3.10 CI leg
    import tomli as tomllib

from examples._internal.catalog import EXAMPLES_ROOT, load_catalog
from examples._internal.qualify import interpolate, project_environment

EXPECTED_CITRY_APPS = {
    "demo-htmx": "app.components:citry_app",
    "demo-project-board": "app.components.page:citry_app",
    "starter-asgi": "app.components:citry_app",
    "starter-django": "project_explorer.components:citry_app",
    "starter-fastapi": "app.components:citry_app",
    "starter-flask": "app.components:citry_app",
    "starter-standalone": "app.components:citry_app",
    "starter-wsgi": "app.components:citry_app",
}
ENVIRONMENT_EXAMPLES = {
    "demo-project-board",
    "starter-asgi",
    "starter-django",
    "starter-fastapi",
    "starter-flask",
    "starter-wsgi",
}


def project_python(project) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(project.source.rglob("*.py"))
        if ".venv" not in path.parts and "__pycache__" not in path.parts
    )


def test_catalog_projects_have_complete_independent_inventory() -> None:
    projects = load_catalog()

    assert len({project.id for project in projects}) == len(projects)
    assert {project.host for project in projects} >= {
        "none",
        "fastapi",
        "django",
        "flask",
        "asgi",
        "wsgi",
    }
    for project in projects:
        assert project.source.is_dir()
        assert (project.source / "README.md").is_file()
        assert (project.source / "pyproject.toml").is_file()
        assert (project.source / "uv.lock").is_file()
        assert (project.source / "tests").is_dir()
        assert project.test[:2] == ("uv", "run")
        assert "../" not in project.source.joinpath("README.md").read_text()
        if project.is_web:
            assert (project.source / ".env.example").is_file()
            assert project.page_path == "/"
            assert project.citry_prefix == "/citry"
            assert project.serve is not None
            assert "{port}" in " ".join(project.serve)
        else:
            assert project.build is not None


def test_catalog_projects_include_locked_citry_editor_setup() -> None:
    assert not (EXAMPLES_ROOT / "starters" / ".vscode").exists()

    for project in load_catalog():
        settings = json.loads(project.source.joinpath(".vscode/settings.json").read_text(encoding="utf-8"))
        expected_settings = {
            "citry.python": "${workspaceFolder}/.venv/bin/python",
            "citry.app": EXPECTED_CITRY_APPS[project.id],
        }
        if project.id in ENVIRONMENT_EXAMPLES:
            expected_settings["citry.envFile"] = "${workspaceFolder}/.env.example"
        assert settings == expected_settings

        manifest = tomllib.loads(project.source.joinpath("pyproject.toml").read_text(encoding="utf-8"))
        assert "citry-lsp>=0.1,<0.2" in manifest["dependency-groups"]["dev"]

        lock = tomllib.loads(project.source.joinpath("uv.lock").read_text(encoding="utf-8"))
        locked_servers = [package for package in lock["package"] if package.get("name") == "citry-lsp"]
        assert len(locked_servers) == 1
        assert locked_servers[0]["version"].startswith("0.1.")


def test_profiles_lock_the_shared_starter_curriculum() -> None:
    for project in load_catalog():
        source = project_python(project)
        if project.profile == "starter-web-v1":
            assert "class State:" in source
            assert "class Events:" in source
            assert ':c-query.debounce.300ms="refresh"' in source
            assert "tipsOpen = !tipsOpen" in source
            assert "find_projects(state.query)" in source
        elif project.profile == "starter-standalone-v1":
            assert "class State:" not in source
            assert "class Events:" not in source
            assert 'deps_strategy="document"' in source
            assert "tipsOpen = !tipsOpen" in source


def test_starters_share_the_citry_visual_contract() -> None:
    expected_modes = {
        "none": "Standalone document",
        "fastapi": "FastAPI starter",
        "django": "Django starter",
        "flask": "Flask starter",
        "asgi": "Bare ASGI starter",
        "wsgi": "Bare WSGI starter",
    }
    for project in load_catalog():
        if project.kind != "starter":
            continue

        source = project_python(project)
        assert "--color-page: oklch(96.5% 0.005 250)" in source
        assert "--color-accent: oklch(55% 0.13 195)" in source
        assert "--color-link: oklch(52% 0.15 245)" in source
        assert 'class="brand__name">Citry</span>' in source
        assert 'class="site-title">Project Explorer</span>' in source
        assert f'class="mode-label">{expected_modes[project.host]}</span>' in source
        assert "brand__mark" not in source
        assert 'font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif' in source
        assert "radial-gradient" not in source
        assert "box-shadow:" not in source


def test_starter_readmes_follow_the_reader_workflow() -> None:
    common_sections = (
        "## What this starter shows",
        "## Requirements",
        "## Test the project",
        "## Remove the environment",
        "## Find the important code",
        "## Follow the data",
    )
    for project in load_catalog():
        if project.kind != "starter":
            continue

        readme = project.source.joinpath("README.md").read_text(encoding="utf-8")
        manifest = tomllib.loads(project.source.joinpath("pyproject.toml").read_text(encoding="utf-8"))
        citry_requirement = next(
            dependency for dependency in manifest["project"]["dependencies"] if dependency.startswith("citry>=")
        )
        minimum_citry = citry_requirement.removeprefix("citry>=").split(",", 1)[0]
        for section in common_sections:
            assert section in readme, f"{project.id} is missing the README section {section!r}"
        assert "Python 3.10 through 3.14" in readme
        assert f"Citry {minimum_citry}" in readme
        assert "PowerShell" in readme
        assert "https://citry.dev/" in readme

        if project.is_web:
            assert "## Run the project" in readme
            assert "## Prepare the project for production" in readme
            assert "State" in readme
            assert "browser can read it" in readme
            assert "Never put secrets in `State`." in readme
            assert "CSRF" in readme
        else:
            assert "## Render the page" in readme
            assert "## Prepare the page for publishing" in readme
            assert "This starter has no Citry Events." in readme


def test_projects_do_not_import_each_other_or_repository_helpers() -> None:
    for project in load_catalog():
        source = project_python(project)
        assert "examples.star" not in source
        assert "examples.demo" not in source
        assert "packages.py.citry" not in source
        assert "benchmarks." not in source


def test_catalog_paths_are_linked_from_examples_readme() -> None:
    readme = (EXAMPLES_ROOT / "README.md").read_text(encoding="utf-8")
    for project in load_catalog():
        assert f"({project.path.as_posix()}/)" in readme


def test_htmx_demo_uses_the_canonical_citry_mark() -> None:
    canonical = EXAMPLES_ROOT.parent / "docs_site" / "static" / "img" / "citry-mark.svg"
    demo_copy = EXAMPLES_ROOT / "demos" / "htmx" / "app" / "static" / "citry-mark.svg"

    assert demo_copy.read_bytes() == canonical.read_bytes()


def test_port_placeholder_is_resolved_without_shell_interpolation() -> None:
    assert interpolate(("server", "--port", "{port}", "127.0.0.1:{port}"), 43127) == [
        "server",
        "--port",
        "43127",
        "127.0.0.1:43127",
    ]


def test_qualification_commands_keep_the_candidate_install() -> None:
    assert project_environment()["UV_NO_SYNC"] == "1"
