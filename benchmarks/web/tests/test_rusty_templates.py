"""Keep the experimental Rusty Templates adapter and focused schedule explicit."""

import json

import tomllib
from citry_bench import config

WEB = config.WEB
APP = WEB / "apps" / "django_rusty_templates"
RUSTY_COMMIT = "0725f875535b2fca93953a403a57df1d9b34e073"


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
        "commit_date": "2026-09-22",
        "license": "BSD-3-Clause",
        "status": "unreleased experimental",
        "prepare_requirements": ["Rust", "Maturin"],
    }


def test_rusty_variant_rewrites_every_empty_branch() -> None:
    template = (APP / "board.html").read_text(encoding="utf-8")
    assert "{% empty %}" not in template
    assert template.count("{% if ") >= 5
    assert template.count("{% else %}") >= 8


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
    for name in ("cohort", "cohort-local", "cohort-100x"):
        data = tomllib.loads((WEB / "profiles" / f"{name}.toml").read_text(encoding="utf-8"))
        assert set(data["apps"]) == expected
        assert len(data["apps"]) == 14


def test_rusty_migration_profile_is_exact_and_has_no_local_wheels() -> None:
    path = WEB / "profiles" / "vue-migration-rusty.toml"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    assert data == {
        "name": "vue-migration-rusty",
        "mode": "native",
        "apps": ["next", "nuxt", "django_rusty_templates"],
        "scenario": "project_board",
        "scenario_revision": "canonical-project-v1",
        "counts": [140, 1400],
        "browser": "chromium",
        "python": "3.12.13",
        "blocks": 3,
        "sessions": 1,
        "warmups": 0,
        "cycles": 2,
        "initial_timeout_ms": 30000,
        "action_timeout_ms": 15000,
        "cache": "cold-context",
        "network": "loopback",
        "compression": "identity",
        "seed": 1729,
        "publication": False,
    }
    assert "local_wheels" not in data
    assert config.profile("vue-migration-rusty") == data
