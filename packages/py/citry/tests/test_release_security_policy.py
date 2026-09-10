"""Publishing policy rejects changes that cross the release credential boundary."""

import shutil
from pathlib import Path

import pytest
import yaml
from scripts.validators.release_security import check


@pytest.fixture
def workflows(tmp_path):
    source = Path(__file__).resolve().parents[4] / ".github/workflows"
    shutil.copytree(source, tmp_path / ".github/workflows")
    return tmp_path


def _change(root, filename, edit):
    path = root / ".github/workflows" / filename
    value = yaml.safe_load(path.read_text())
    edit(value)
    path.write_text(yaml.safe_dump(value))


def test_current_workflows_pass(workflows):
    assert check(workflows) == []


def test_tag_cannot_run_before_publication(workflows):
    _change(workflows, "py--citry--publish.yml", lambda value: value["jobs"]["tag"].update(needs=["verify-version"]))
    assert any("only after verified publication" in error for error in check(workflows))


def test_qualification_cannot_use_publish_environment(workflows):
    _change(workflows, "py--citry--publish.yml", lambda value: value["jobs"]["build"].update(environment="pypi"))
    assert any("outside its publication job" in error for error in check(workflows))


def test_tag_cannot_execute_historical_release_code(workflows):
    _change(
        workflows,
        "py--citry--publish.yml",
        lambda value: value["jobs"]["tag"]["steps"][0]["with"].update(ref="${{ inputs.release_commit }}"),
    )
    assert any("trusted workflow source" in error for error in check(workflows))


def test_publisher_cannot_read_release_app_key(workflows):
    _change(
        workflows,
        "py--citry--publish.yml",
        lambda value: value["jobs"]["release"].update(env={"KEY": "${{ secrets.RELEASE_APP_PRIVATE_KEY }}"}),
    )
    assert any("outside its isolated write job" in error for error in check(workflows))


def test_tag_requires_its_own_release_environment(workflows):
    _change(workflows, "py--citry--publish.yml", lambda value: value["jobs"]["tag"].pop("environment"))
    assert any("isolated release environment" in error for error in check(workflows))


def test_unregistered_workflow_cannot_create_protected_tags(workflows):
    path = workflows / ".github/workflows/unregistered.yml"
    path.write_text(yaml.safe_dump({"jobs": {"tag": {"steps": [{"run": "python -m scripts.release_tag create"}]}}}))
    assert any("outside the package publishers" in error for error in check(workflows))


def test_tag_cannot_ignore_failed_publication(workflows):
    _change(workflows, "py--citry--publish.yml", lambda value: value["jobs"]["tag"].update({"if": "always()"}))
    assert any("successful dependencies" in error for error in check(workflows))
