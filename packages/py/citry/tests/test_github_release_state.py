"""Publication reuses only complete releases whose assets match verified bytes."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import urllib.error
from email.message import Message
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from scripts.verify_github_release import (
    GitHubReleaseError,
    _HTTPSRedirect,
    _NoRedirect,
    _public_bytes,
    _verify_attestation,
    fetch_release,
    main,
    verify_release,
)

if TYPE_CHECKING:
    from pathlib import Path

TAG = "citry@0.5.0"
PLACEHOLDER = "test-token"


def _release(tmp_path: Path) -> dict[str, Any]:
    (tmp_path / "approved.whl").write_bytes(b"approved")
    return {
        "draft": False,
        "tag_name": TAG,
        "assets": [
            {
                "name": "approved.whl",
                "size": 8,
                "digest": "sha256:" + hashlib.sha256(b"approved").hexdigest(),
                "state": "uploaded",
            }
        ],
    }


def test_accepts_exact_existing_release(tmp_path: Path) -> None:
    assert verify_release(status=200, payload=_release(tmp_path), tag=TAG, assets_dir=tmp_path)


@pytest.mark.parametrize(
    "change", ["draft", "tag", "missing", "extra", "size", "digest", "no_digest", "duplicate", "state"]
)
def test_rejects_incomplete_or_different_release(tmp_path: Path, change: str) -> None:
    release = _release(tmp_path)
    asset = release["assets"][0]
    if change == "draft":
        release["draft"] = True
    elif change == "tag":
        release["tag_name"] = "citry@0.4.0"
    elif change == "missing":
        release["assets"] = []
    elif change == "extra":
        release["assets"].append({**asset, "name": "extra.whl"})
    elif change == "size":
        asset["size"] += 1
    elif change == "digest":
        asset["digest"] = "sha256:" + "0" * 64
    elif change == "no_digest":
        del asset["digest"]
    elif change == "duplicate":
        release["assets"].append(asset)
    else:
        asset["state"] = "starter"
    with pytest.raises(GitHubReleaseError, match="manually"):
        verify_release(status=200, payload=release, tag=TAG, assets_dir=tmp_path)


def test_missing_release_is_allowed_only_before_creation(tmp_path: Path) -> None:
    assert not verify_release(status=404, payload=None, tag=TAG, assets_dir=tmp_path)
    with pytest.raises(GitHubReleaseError, match="does not exist"):
        verify_release(status=404, payload=None, tag=TAG, assets_dir=tmp_path, require_existing=True)


@pytest.mark.parametrize("status", [301, 401, 403, 429, 500])
def test_rejects_unexpected_http_status(tmp_path: Path, status: int) -> None:
    with pytest.raises(GitHubReleaseError, match=f"HTTP {status}"):
        verify_release(status=status, payload=None, tag=TAG, assets_dir=tmp_path)


def test_api_uses_fixed_host_and_refuses_redirects() -> None:
    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = b'{"draft": false}'
    with patch("scripts.verify_github_release.urllib.request.build_opener") as build:
        build.return_value.open.return_value = response
        assert fetch_release(repository="citry-dev/citry", tag=TAG, token=PLACEHOLDER) == (200, {"draft": False})
        handler = build.call_args.args[0]
        assert isinstance(handler, _NoRedirect)
        handler.redirect_request(None, None, 302, "", {}, "https://other.example")
        request = build.return_value.open.call_args.args[0]
        assert request.full_url == "https://api.github.com/repos/citry-dev/citry/releases/tags/citry%400.5.0"


@pytest.mark.parametrize("status", [302, 403, 404, 500])
def test_api_http_errors(status: int) -> None:
    error = urllib.error.HTTPError("https://api.github.com/", status, "error", Message(), io.BytesIO())
    with patch("scripts.verify_github_release.urllib.request.build_opener") as build:
        build.return_value.open.side_effect = error
        if status == 404:
            assert fetch_release(repository="citry-dev/citry", tag=TAG, token=PLACEHOLDER) == (404, None)
        else:
            with pytest.raises(GitHubReleaseError, match=f"HTTP {status}"):
                fetch_release(repository="citry-dev/citry", tag=TAG, token=PLACEHOLDER)


def test_api_network_error_does_not_expose_credentials() -> None:
    with patch("scripts.verify_github_release.urllib.request.build_opener") as build:
        build.return_value.open.side_effect = urllib.error.URLError("sensitive detail")
        with pytest.raises(GitHubReleaseError, match=r"^GitHub release lookup failed$"):
            fetch_release(repository="citry-dev/citry", tag=TAG, token=PLACEHOLDER)


def test_cli_outputs_success_only_after_verification(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    release = _release(assets)
    output = tmp_path / "output"
    monkeypatch.setenv("GH_TOKEN", "test-token")
    args = [
        "--repository",
        "citry-dev/citry",
        "--tag",
        TAG,
        "--assets-dir",
        str(assets),
        "--github-output",
        str(output),
    ]
    with patch("scripts.verify_github_release.fetch_release", return_value=(200, release)):
        assert main(args) == 0
    assert output.read_text() == "release_exists=true\n"
    release["draft"] = True
    with patch("scripts.verify_github_release.fetch_release", return_value=(200, release)):
        assert main(args) == 1
    assert output.read_text() == "release_exists=true\n"


def test_api_rejects_nonobject_json() -> None:
    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = json.dumps([]).encode()
    with patch("scripts.verify_github_release.urllib.request.build_opener") as build:
        build.return_value.open.return_value = response
        with pytest.raises(GitHubReleaseError, match="object"):
            fetch_release(repository="citry-dev/citry", tag=TAG, token=PLACEHOLDER)


def _attestation() -> dict[str, Any]:
    statement = {
        "subject": [{"name": "approved.whl", "digest": {"sha256": hashlib.sha256(b"approved").hexdigest()}}],
        "predicateType": "https://docs.pypi.org/attestations/publish/v1",
    }
    return {"version": 1, "envelope": {"statement": base64.b64encode(json.dumps(statement).encode()).decode()}}


@pytest.mark.parametrize(
    "change",
    ["none", "different_provenance", "different_subject", "different_bytes", "wrong_publisher", "missing_provenance"],
)
def test_extra_attestation_must_match_pypi_and_approved_bytes(tmp_path: Path, change: str) -> None:
    release = _release(tmp_path)
    attestation = _attestation()
    if change == "different_subject":
        statement = json.loads(base64.b64decode(attestation["envelope"]["statement"]))
        statement["subject"][0]["digest"]["sha256"] = "0" * 64
        attestation["envelope"]["statement"] = base64.b64encode(json.dumps(statement).encode()).decode()
    data = json.dumps(attestation).encode()
    release["assets"].append(
        {
            "name": "approved.whl.publish.attestation",
            "size": len(data),
            "digest": "sha256:" + hashlib.sha256(data).hexdigest(),
            "state": "uploaded",
        }
    )
    provenance = {
        "attestation_bundles": [
            {
                "attestations": [attestation] if change != "different_provenance" else [],
                "publisher": {"repository": "elsewhere/repo" if change == "wrong_publisher" else "citry-dev/citry"},
            }
        ]
    }
    downloads: list[bytes | Exception] = [data, json.dumps(provenance).encode()]
    if change == "different_bytes":
        downloads[0] = b"different"
    elif change == "missing_provenance":
        downloads[1] = GitHubReleaseError("could not download public release metadata")
    with patch("scripts.verify_github_release._public_bytes", side_effect=downloads) as download:
        if change == "none":
            assert verify_release(
                status=200, payload=release, tag=TAG, assets_dir=tmp_path, repository="citry-dev/citry"
            )
            assert download.call_args_list[0].args == (
                "https://github.com/citry-dev/citry/releases/download/citry%400.5.0/approved.whl.publish.attestation",
            )
            assert download.call_args_list[1].args == (
                "https://pypi.org/integrity/citry/0.5.0/approved.whl/provenance",
            )
        else:
            with pytest.raises(GitHubReleaseError):
                verify_release(status=200, payload=release, tag=TAG, assets_dir=tmp_path, repository="citry-dev/citry")


def test_attestation_exception_is_not_available_for_vscode(tmp_path: Path) -> None:
    release = _release(tmp_path)
    release["tag_name"] = "vscode-citry@0.1.3"
    data = json.dumps(_attestation()).encode()
    release["assets"].append(
        {
            "name": "approved.whl.publish.attestation",
            "size": len(data),
            "digest": "sha256:" + hashlib.sha256(data).hexdigest(),
            "state": "uploaded",
        }
    )
    with pytest.raises(GitHubReleaseError, match="known PyPI"):
        verify_release(
            status=200, payload=release, tag="vscode-citry@0.1.3", assets_dir=tmp_path, repository="citry-dev/citry"
        )


def test_public_download_sends_no_token_and_requires_https_redirects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GH_TOKEN", PLACEHOLDER)
    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = b"public bytes"
    with patch("scripts.verify_github_release.urllib.request.build_opener") as build:
        build.return_value.open.return_value = response
        assert _public_bytes("https://github.com/public/file") == b"public bytes"
        assert build.return_value.open.call_args.args == ("https://github.com/public/file",)
        handler = build.call_args.args[0]
        assert isinstance(handler, _HTTPSRedirect)
        with pytest.raises(GitHubReleaseError, match="outside HTTPS"):
            handler.redirect_request(None, None, 302, "", {}, "http://untrusted.example")


@pytest.mark.parametrize("version", [True, 1.0])
def test_attestation_comparison_preserves_json_value_types(version: bool | float) -> None:
    published = _attestation()
    sidecar = {**published, "version": version}
    data = json.dumps(sidecar).encode()
    provenance = {
        "attestation_bundles": [{"attestations": [published], "publisher": {"repository": "citry-dev/citry"}}]
    }
    with (
        patch("scripts.verify_github_release._public_bytes", side_effect=[data, json.dumps(provenance).encode()]),
        pytest.raises(GitHubReleaseError, match="does not match PyPI provenance"),
    ):
        _verify_attestation(
            repository="citry-dev/citry",
            tag=TAG,
            name="approved.whl.publish.attestation",
            parent_digest="sha256:" + hashlib.sha256(b"approved").hexdigest(),
            size=len(data),
            digest="sha256:" + hashlib.sha256(data).hexdigest(),
        )
