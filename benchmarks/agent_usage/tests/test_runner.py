"""Check isolation, treatment inputs, and stopped-run grading without model calls."""

# unittest keeps host-side verification runnable with Python's standard library.
# ruff: noqa: PT009, PT027

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("agent_usage_runner", ROOT / "run.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

# This executable never invokes Codex or a model. It probes the same container
# mounts and timer path while emitting the public JSON event shape.
FAKE_CODEX = """#!/usr/local/bin/python
import json
import pathlib
import sys
import time

if "login" in sys.argv:
    time.sleep(1)
    assert pathlib.Path("/home/agent/.codex/auth.json").is_file()
    sys.exit(0)

prompt = sys.stdin.read()
assert "Time limit:" in prompt
assert not pathlib.Path("/grader").exists()
assert not pathlib.Path("/Users/mac/repos/citry").exists()
assert not pathlib.Path("/workspace/CLAUDE.md").exists()
assert not pathlib.Path("/var/run/docker.sock").exists()
assert not pathlib.Path("/home/agent/.codex/config.toml").exists()
assert not pathlib.Path("/home/agent/.codex/AGENTS.md").exists()
pathlib.Path("/workspace/probe.txt").write_text("isolated")
if "smoke-timeout" in sys.argv:
    time.sleep(30)
print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"Smoke completed"}}))
print(json.dumps({"type":"turn.completed","usage":{"input_tokens":11,"output_tokens":7}}))
"""


class InputTests(unittest.TestCase):
    """Verify the declared treatment is the only extra content copied to subjects."""

    def test_inline_uses_exact_skill_body(self) -> None:
        body = runner.skill_body()
        self.assertIn(body, runner.prompt("cards", "inline", 10))
        self.assertNotIn(body, runner.prompt("cards", "llms", 10))
        self.assertNotIn("$citry-consumer", runner.prompt("cards", "skill-auto", 10))
        self.assertIn("$citry-consumer", runner.prompt("cards", "skill", 10))

    def test_prepare_copies_only_starter_and_selected_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, patch.object(runner, "image_id", return_value="sha256:test"):
            for arm in runner.ARMS:
                options = argparse.Namespace(
                    case="cards", arm=arm, timeout=15, model="test", effort="high", out=Path(temporary), image="test"
                )
                directory = runner.prepare(options)
                workspace = directory / "workspace"
                self.assertEqual((workspace / ".agents").exists(), arm in {"skill", "skill-auto"})
                self.assertFalse((workspace / "task.md").exists())
                self.assertFalse((workspace / "run.json").exists())
                self.assertFalse((workspace / "CLAUDE.md").exists())
                self.assertFalse((workspace / "grading").exists())
                self.assertFalse((workspace / "reference").exists())

    def test_reports_incomplete_and_malformed_events(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "events.jsonl"
            path.write_text('garbage\n[]\n{"type":"turn.failed","error":"interrupted"}\n')
            summary = runner.event_summary(path)
            self.assertFalse(summary["turn_completed"])
            self.assertEqual(summary["malformed_lines"], 2)
            self.assertEqual(len(summary["errors"]), 1)
            self.assertEqual(summary["usage"], {})

    def test_input_symlinks_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path / "link").symlink_to(ROOT / "common.md")
            with self.assertRaises(ValueError):
                runner.tree_hash(path)

    def test_host_result_write_does_not_follow_submission_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            sentinel = path / "sentinel"
            sentinel.write_text("unchanged")
            results = path / "grade"
            results.mkdir()
            (results / "result.tmp").symlink_to(sentinel)
            (results / "result.json").symlink_to(sentinel)
            runner.write_json(results / "result.json", {"passed": False})
            self.assertEqual(sentinel.read_text(), "unchanged")
            self.assertFalse((results / "result.json").is_symlink())
            self.assertEqual(json.loads((results / "result.json").read_text()), {"passed": False})
            with self.assertRaises(ValueError):
                runner.read_artifact(results / "result.tmp")

    def test_batch_stops_after_interruption_or_agent_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan = Path(temporary) / "plan.json"
            plan.write_text(json.dumps({"runs": ["first", "second"]}))
            for status in ("interrupted", "agent_error", "incomplete", "harness_error"):
                with (
                    patch.object(runner, "run") as run,
                    patch.object(runner, "grade") as grade,
                    patch.object(runner, "load_run", return_value=(Path("first"), {"status": status, "id": "first"})),
                ):
                    with self.assertRaises(ValueError):
                        runner.execute(argparse.Namespace(plan=plan, auth_volume="unused"))
                    self.assertEqual(run.call_count, 1)
                    grade.assert_not_called()


@unittest.skipUnless(os.environ.get("CITRY_AGENT_EVAL_DOCKER") == "1", "opt-in Docker verification")
class DockerTests(unittest.TestCase):
    """Exercise the real Docker lifecycle with fake credentials and no model API."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.base = os.environ.get("CITRY_AGENT_EVAL_IMAGE", runner.IMAGE)
        cls.fake = "citry-eval-smoke:" + uuid.uuid4().hex[:10]
        cls.auth = "citry-eval-smoke-auth-" + uuid.uuid4().hex[:10]
        context = cls.root / "image"
        context.mkdir()
        (context / "codex").write_text(FAKE_CODEX)
        (context / "Dockerfile").write_text(
            f"FROM {cls.base}\nUSER root\n"
            "RUN rm /usr/local/bin/codex\nCOPY --chmod=755 codex /usr/local/bin/codex\nUSER agent\n"
        )
        runner.docker("build", "-q", "-t", cls.fake, str(context), capture=True)
        runner.docker("volume", "create", cls.auth, capture=True)
        runner.auth_helper(
            cls.base, cls.auth, "from pathlib import Path; Path('/auth/auth.json').write_text('{\"smoke\":true}')"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        runner.docker("volume", "rm", cls.auth, capture=True)
        runner.docker("image", "rm", cls.fake, capture=True)
        cls.temporary.cleanup()

    def prepare(self, model: str = "smoke", case: str = "cards", image: str | None = None) -> Path:
        return runner.prepare(
            argparse.Namespace(
                case=case,
                arm="llms",
                model=model,
                timeout=1 if model == "smoke-timeout" else 10,
                effort="high",
                image=image or self.fake,
                out=self.root / "runs",
            )
        )

    def test_isolation_and_untimed_login(self) -> None:
        directory = self.prepare()
        started = time.monotonic()
        runner.run(argparse.Namespace(directory=directory, auth_volume=self.auth))
        total = time.monotonic() - started
        manifest = json.loads((directory / "run.json").read_text())
        self.assertEqual(manifest["status"], "completed")
        self.assertGreaterEqual(total - manifest["elapsed_seconds"], 1)
        self.assertEqual(manifest["usage"], {"input_tokens": 11, "output_tokens": 7})
        self.assertEqual((directory / "workspace/probe.txt").read_text(), "isolated")
        audit = json.loads((directory / "container.json").read_text())[0]
        mounts = {mount["Destination"] for mount in audit["Mounts"]}
        self.assertEqual(mounts, {"/workspace", "/home/agent/.codex"})
        self.assertFalse((directory / "workspace/auth.json").exists())
        with self.assertRaises(ValueError):
            runner.run(argparse.Namespace(directory=directory, auth_volume=self.auth))

    def test_timeout_stops_container(self) -> None:
        directory = self.prepare(model="smoke-timeout")
        runner.run(argparse.Namespace(directory=directory, auth_volume=self.auth))
        manifest = json.loads((directory / "run.json").read_text())
        self.assertEqual(manifest["status"], "timeout")
        self.assertFalse(manifest["turn_completed"])
        result = subprocess.run(
            [runner.DOCKER, "inspect", "citry-eval-" + manifest["id"]], capture_output=True, check=False
        )
        self.assertNotEqual(result.returncode, 0)

    def test_missing_auth_does_not_start_timer(self) -> None:
        empty = "citry-eval-smoke-empty-" + uuid.uuid4().hex[:10]
        runner.docker("volume", "create", empty, capture=True)
        try:
            directory = self.prepare()
            with self.assertRaises(subprocess.CalledProcessError):
                runner.run(argparse.Namespace(directory=directory, auth_volume=empty))
            manifest = json.loads((directory / "run.json").read_text())
            self.assertEqual(manifest["status"], "preflight_error")
            self.assertNotIn("started_at", manifest)
            self.assertFalse((directory / "events.jsonl").exists())
        finally:
            runner.docker("volume", "rm", empty, capture=True)

    def test_references_pass_and_empty_starters_fail(self) -> None:
        for case in runner.CASES:
            with self.subTest(case=case):
                directory = self.prepare(case=case, image=self.base)
                workspace = directory / "workspace"
                shutil.copytree(ROOT / "reference" / case, workspace, dirs_exist_ok=True)
                # Submission files must not replace trusted test tools or config.
                (workspace / "pytest.py").write_text("raise RuntimeError('submission pytest loaded')\n")
                (workspace / "conftest.py").write_text("raise RuntimeError('submission conftest loaded')\n")
                (workspace / "sitecustomize.py").write_text("raise RuntimeError('submission sitecustomize loaded')\n")
                path, manifest = runner.load_run(directory)
                manifest["status"] = "reference"
                runner.write_json(path / "run.json", manifest)
                runner.grade(argparse.Namespace(directory=directory))
                grade = json.loads((directory / "grade/result.json").read_text())
                if not grade["passed"]:
                    self.fail((directory / "grade/output.log").read_text())
                empty = self.prepare(case=case, image=self.base)
                path, manifest = runner.load_run(empty)
                manifest["status"] = "negative-control"
                runner.write_json(path / "run.json", manifest)
                runner.grade(argparse.Namespace(directory=empty))
                grade = json.loads((empty / "grade/result.json").read_text())
                self.assertFalse(grade["passed"])


if __name__ == "__main__":
    unittest.main()
