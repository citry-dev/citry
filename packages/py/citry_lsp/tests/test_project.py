"""Tests for the bounded project-import worker."""

from __future__ import annotations

import json
import subprocess

from citry import Citry
from citry_lsp.project import load_project


def test_project_worker_captures_output_and_returns_copied_registry(tmp_path):
    (tmp_path / "app.py").write_text(
        "from citry import Citry, Component\n"
        "print('project says hello')\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template = '<article></article>'\n"
        "    class Kwargs:\n"
        "        title: str\n",
        encoding="utf-8",
    )

    state = load_project(tmp_path, "app:engine")

    assert state.status.mode == "registry"
    assert state.status.registry_ready is True
    assert state.status.message is not None
    assert "project says hello" in state.status.message
    assert state.analysis is not None
    assert "card" in state.analysis.component_names
    assert state.catalog is not None
    assert state.catalog.get("c-card") is not None


def test_project_worker_turns_system_exit_into_syntax_only_degradation(tmp_path):
    (tmp_path / "app.py").write_text("raise SystemExit(7)\n", encoding="utf-8")

    state = load_project(tmp_path, "app:engine")

    assert state.status.mode == "syntax-only"
    assert state.status.registry_ready is False
    assert state.status.message is not None
    assert "SystemExit" in state.status.message


def test_project_worker_timeout_degrades_without_hanging_server(tmp_path):
    (tmp_path / "app.py").write_text(
        "import time\ntime.sleep(10)\n",
        encoding="utf-8",
    )

    state = load_project(tmp_path, "app:engine", timeout=0.05)

    assert state.status.mode == "syntax-only"
    assert state.status.message is not None
    assert "startup limit" in state.status.message


def test_no_app_selects_reported_syntax_only_mode(tmp_path):
    state = load_project(tmp_path, None)

    assert state.status.mode == "syntax-only"
    assert state.status.app is None
    assert "No Citry app configured" in (state.status.message or "")
    assert state.status.to_dict()["mode"] == "syntax-only"
    assert state.status.python_expression_provider == "ruff@0.14.10+45bbb4cbff"


def test_worker_process_and_json_failures_degrade(tmp_path, monkeypatch):
    responses = [
        subprocess.CompletedProcess([], 9, stdout="", stderr="worker crashed"),
        subprocess.CompletedProcess([], 0, stdout="not json", stderr=""),
        subprocess.CompletedProcess([], 2, stdout='{"ok": false, "error": "bad app"}', stderr=""),
        subprocess.CompletedProcess([], 2, stdout="[]", stderr=""),
    ]

    def run(*_args, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr("citry_lsp.project.subprocess.run", run)

    messages = [(load_project(tmp_path, "app:engine").status.message or "") for _ in range(4)]

    assert "without a response" in messages[0]
    assert "worker crashed" in messages[0]
    assert "invalid JSON" in messages[1]
    assert "bad app" in messages[2]
    assert "status 2" in messages[3]


def test_worker_protocol_and_version_mismatches_degrade(tmp_path, monkeypatch):
    engine = Citry(autodiscover=False)
    base = {
        "ok": True,
        "analysis": engine.template_analysis().to_dict(),
        "catalog": engine.inspect_components(include_builtins=True, resolve_assets=True).to_dict(),
    }
    payloads = [
        {**base, "analysis": None},
        {**base, "catalog": {**base["catalog"], "citry_version": "development"}},
        {**base, "catalog": {**base["catalog"], "schema_version": 999}},
    ]

    def run(*_args, **_kwargs):
        payload = payloads.pop(0)
        return subprocess.CompletedProcess([], 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr("citry_lsp.project.subprocess.run", run)

    messages = [(load_project(tmp_path, "app:engine").status.message or "") for _ in range(3)]

    assert "protocol mismatch" in messages[0]
    assert "outside this server's supported" in messages[1]
    assert "schema 999 is unsupported" in messages[2]
