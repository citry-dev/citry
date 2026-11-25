"""Keep the experimental Rusty Templates adapter and focused schedule explicit."""

import json

import tomllib
from citry_bench import config

WEB = config.WEB
APP = WEB / "apps" / "django_rusty_templates"
RUSTY_COMMIT = "6d10c20f09dd88fbbf4c75a93847f47655a864f4"


def test_rusty_adapter_uses_official_backend_and_builds_only_its_git_dependency() -> None:
    declaration = config.adapter(APP)
    assert declaration["name"] == "django_rusty_templates"
    assert declaration["runtime"] == "python"
    assert declaration["allow_dependency_build"] is True
    assert declaration["rendering"] == "server"
    assert declaration["transport"] == "http"
    assert declaration["local_wheels"] == []
    source = (APP / "app.py").read_text(encoding="utf-8")
    assert '"django_rusty_templates.RustyTemplates"' in source
    assert "django.template.loader" in source
    assert "DjangoTemplates" not in source


def test_rusty_dependency_lock_and_provenance_are_exact() -> None:
    pyproject = (APP / "pyproject.toml").read_text(encoding="utf-8")
    lock = (APP / "uv.lock").read_text(encoding="utf-8")
    provenance = json.loads((APP / "provenance.json").read_text(encoding="utf-8"))
    assert f"@{RUSTY_COMMIT}" in pyproject
    assert RUSTY_COMMIT in lock
    assert provenance["package"] == {
        "name": "django-rusty-templates",
        "version": "0.1.0",
        "source": "https://github.com/LilyFirefly/django-rusty-templates",
        "commit": RUSTY_COMMIT,
        "commit_date": "2026-11-24",
        "license": "BSD-3-Clause",
        "status": "unreleased experimental",
        "prepare_requirements": ["Rust", "Maturin"],
    }


def test_rusty_app_renders_the_django_apps_templates_unchanged() -> None:
    # The comparison with Django means something only while both engines are
    # given the same template text, so any edit to one copy must reach the other.
    django_app = WEB / "apps" / "django_htmx_alpine"
    for name in ("board.html", "page.html"):
        assert (APP / name).read_bytes() == (django_app / name).read_bytes(), name


def test_maintained_cohort_profiles_include_fourteen_adapters() -> None:
    expected = {
        "citry",
        "django_htmx_alpine",
        "django_rusty_templates",
        "fasthtml",
        "reactpy",
        "tetra",
        "unicorn",
        "reflex",
        "jinja_htmx_alpine",
        "django_components",
        "python_vue",
        "python_react",
        "next",
        "nuxt",
    }
    for name in ("cohort", "cohort-100x", "release-0.6.0"):
        data = tomllib.loads((WEB / "profiles" / f"{name}.toml").read_text(encoding="utf-8"))
        assert set(data["apps"]) == expected
        assert len(data["apps"]) == 14
