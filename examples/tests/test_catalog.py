from examples.tools.catalog import EXAMPLES_ROOT, load_catalog
from examples.tools.qualify import interpolate


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


def test_port_placeholder_is_resolved_without_shell_interpolation() -> None:
    assert interpolate(("server", "--port", "{port}", "127.0.0.1:{port}"), 43127) == [
        "server",
        "--port",
        "43127",
        "127.0.0.1:43127",
    ]
