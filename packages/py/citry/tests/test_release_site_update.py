"""The privileged release job accepts only the generated site artifact."""

import json
from pathlib import Path

import pytest
from scripts.apply_release_site_update import apply_update


def _published_runtime() -> dict:
    version = "1.0.0"
    return {
        "schema_version": 1,
        "protocol_version": 1,
        "source": "published",
        "pyodide": {
            "version": "314.0.3",
            "python": "3.14.2",
            "index_url": "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/",
            "module_url": "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/pyodide.mjs",
        },
        "citry": {"version": version, "core_version": version, "ui_version": version},
        "packages": [
            {
                "name": name,
                "version": version,
                "source": "pypi",
                "filename": f"{name.replace('-', '_')}-{version}-py3-none-any.whl",
                "sha256": "a" * 64,
            }
            for name in ("citry-core", "citry", "citry-ui")
        ],
    }


def _artifact(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "artifact"
    repository = tmp_path / "repository"
    for root in (source, repository / "docs_site"):
        (root / "versions").mkdir(parents=True)
        (root / "versions/versions.json").write_text("[]\n")
        (root / "static/playground").mkdir(parents=True)
        (root / "static/playground/runtime.json").write_text(
            json.dumps(_published_runtime()) + "\n",
            encoding="utf-8",
        )
    return source, repository


def test_update_replaces_generated_tree_and_preserves_source(tmp_path: Path) -> None:
    source, repository = _artifact(tmp_path)
    (repository / "docs_site/versions/stale.html").write_text("stale")
    (repository / "source.py").write_text("unchanged")
    (source / "versions/new.html").write_text("new")
    runtime_text = json.dumps(_published_runtime()) + "\n"
    (source / "static/playground/runtime.json").write_text(runtime_text, encoding="utf-8")
    apply_update(source, repository)
    assert not (repository / "docs_site/versions/stale.html").exists()
    assert (repository / "docs_site/versions/new.html").read_text() == "new"
    assert (repository / "source.py").read_text() == "unchanged"
    assert (repository / "docs_site/static/playground/runtime.json").read_text() == runtime_text


@pytest.mark.parametrize("extra", [".github/workflows/attack.yml", "static/playground/attack.js", "source.py"])
def test_unexpected_file_rejected_before_writing(tmp_path: Path, extra: str) -> None:
    source, repository = _artifact(tmp_path)
    path = source / extra
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("unexpected")
    with pytest.raises(ValueError, match="unexpected path"):
        apply_update(source, repository)
    assert (repository / "docs_site/versions/versions.json").read_text() == "[]\n"


def test_symlink_rejected_before_writing(tmp_path: Path) -> None:
    source, repository = _artifact(tmp_path)
    (source / "versions/linked").symlink_to(repository / "docs_site/versions")
    with pytest.raises(ValueError, match="non-regular"):
        apply_update(source, repository)


def test_incomplete_artifact_rejected_before_writing(tmp_path: Path) -> None:
    source, repository = _artifact(tmp_path)
    (source / "static/playground/runtime.json").unlink()
    with pytest.raises(ValueError, match="must contain"):
        apply_update(source, repository)


@pytest.mark.parametrize(
    "runtime",
    [
        '{"source": "workspace", "packages": []}\n',
        '{"source": "published", "packages": [{"name": "citry", "source": "url", "url": "./local/citry.whl"}]}\n',
        '{"source": "published", "packages": [{"name": "citry", "source": "url", "url": "citry.whl"}]}\n',
    ],
)
def test_release_site_update_rejects_unpublished_or_relative_runtime(tmp_path: Path, runtime: str) -> None:
    source, repository = _artifact(tmp_path)
    (source / "static/playground/runtime.json").write_text(runtime)

    with pytest.raises(ValueError, match="not publishable"):
        apply_update(source, repository)
