"""Check existing GitHub Releases against files verified by the publication job without changing them."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class GitHubReleaseError(ValueError):
    """A release is absent, incomplete, or different from the verified files."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, _req: Any, _fp: Any, _code: int, _msg: str, _headers: Any, _newurl: str) -> None:
        """Keep the GitHub token on the exact API endpoint requested."""
        return


def fetch_release(*, repository: str, tag: str, token: str) -> tuple[int, dict[str, Any] | None]:
    """Read one release from GitHub's API, refusing every redirect."""
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None:
        raise GitHubReleaseError("repository must be an owner/repository name")
    if not tag or tag in (".", "..") or any(ord(char) < 32 for char in tag):
        raise GitHubReleaseError("release tag must not be empty or contain control characters")
    if not token:
        raise GitHubReleaseError("GH_TOKEN must be set")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/releases/tags/{urllib.parse.quote(tag, safe='')}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=60) as response:
            status = response.status
            if status != 200:
                raise GitHubReleaseError(f"GitHub release lookup returned HTTP {status}")
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return 404, None
        raise GitHubReleaseError(f"GitHub release lookup returned HTTP {error.code}") from error
    except (urllib.error.URLError, OSError) as error:
        raise GitHubReleaseError("GitHub release lookup failed") from error
    if not isinstance(payload, dict):
        raise GitHubReleaseError("GitHub release response must contain an object")
    return status, payload


class _HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> urllib.request.Request | None:
        """Allow public asset downloads to follow only HTTPS redirects."""
        if urllib.parse.urlsplit(newurl).scheme != "https":
            raise GitHubReleaseError("public release metadata redirected outside HTTPS")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _public_bytes(url: str) -> bytes:
    """Download public bytes without attaching any GitHub credentials."""
    try:
        with urllib.request.build_opener(_HTTPSRedirect()).open(url, timeout=60) as response:
            if response.status != 200:
                raise GitHubReleaseError(f"public release metadata returned HTTP {response.status}")
            return response.read()
    except (urllib.error.URLError, OSError) as error:
        raise GitHubReleaseError("could not download public release metadata") from error


def _verify_attestation(*, repository: str, tag: str, name: str, parent_digest: str, size: int, digest: str) -> None:
    """Accept a publish attestation only when PyPI records the same object for these bytes."""
    package, separator, version = tag.partition("@")
    if (
        not separator
        or package not in {"citry", "citry-core", "citry-lsp", "citry-ui", "pygments-citry"}
        or re.fullmatch(r"[0-9][A-Za-z0-9.+!-]*", version) is None
        or re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None
    ):
        raise GitHubReleaseError("publish attestations require a known PyPI package release")
    parent = name.removesuffix(".publish.attestation")
    encoded_tag = urllib.parse.quote(tag, safe="")
    encoded_name = urllib.parse.quote(name, safe="")
    data = _public_bytes(f"https://github.com/{repository}/releases/download/{encoded_tag}/{encoded_name}")
    if len(data) != size or "sha256:" + hashlib.sha256(data).hexdigest() != digest:
        raise GitHubReleaseError("publish attestation bytes differ from GitHub asset metadata")
    attestation = json.loads(data)
    encoded_parent = urllib.parse.quote(parent, safe="")
    provenance = json.loads(
        _public_bytes(f"https://pypi.org/integrity/{package}/{version}/{encoded_parent}/provenance")
    )
    bundles = provenance.get("attestation_bundles") if isinstance(provenance, dict) else None
    if not isinstance(attestation, dict) or not isinstance(bundles, list):
        raise GitHubReleaseError("PyPI publish attestation metadata is invalid")
    encoded_attestation = json.dumps(attestation, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if not any(
        isinstance(bundle, dict)
        and isinstance(bundle.get("attestations"), list)
        and any(
            json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False) == encoded_attestation
            for item in bundle["attestations"]
        )
        and isinstance(bundle.get("publisher"), dict)
        and bundle["publisher"].get("repository") == repository
        for bundle in bundles
    ):
        raise GitHubReleaseError("publish attestation does not match PyPI provenance")
    envelope = attestation.get("envelope")
    encoded_statement = envelope.get("statement") if isinstance(envelope, dict) else None
    if not isinstance(encoded_statement, str):
        raise GitHubReleaseError("publish attestation has no statement")
    statement = json.loads(base64.b64decode(encoded_statement, validate=True))
    if (
        not isinstance(statement, dict)
        or statement.get("subject") != [{"name": parent, "digest": {"sha256": parent_digest.removeprefix("sha256:")}}]
        or statement.get("predicateType") != "https://docs.pypi.org/attestations/publish/v1"
    ):
        raise GitHubReleaseError("publish attestation does not identify the approved package bytes")


def verify_release(
    *,
    status: int,
    payload: Mapping[str, Any] | None,
    tag: str,
    assets_dir: Path,
    repository: str = "",
    require_existing: bool = False,
) -> bool:
    """
    Accept a missing release or one whose complete asset set matches local files.

    Extra PyPI publish attestations are accepted only when they match PyPI
    provenance and identify the verified package bytes. Draft, partial, or
    different releases require manual reconciliation. This check never edits
    an existing release or replaces its assets.
    """
    if status == 404 and payload is None:
        if require_existing:
            raise GitHubReleaseError("the required GitHub Release does not exist")
        return False
    if status != 200 or payload is None:
        raise GitHubReleaseError(f"could not verify the GitHub Release; HTTP {status}")
    if payload.get("draft") is not False or payload.get("tag_name") != tag:
        raise GitHubReleaseError("existing release is a draft or has a different tag; reconcile it manually")
    if assets_dir.is_symlink() or not assets_dir.is_dir():
        raise GitHubReleaseError("verified assets directory must be a directory")
    expected: dict[str, tuple[int, str]] = {}
    for path in assets_dir.iterdir():
        if path.is_symlink() or not path.is_file():
            raise GitHubReleaseError("verified assets directory must contain only regular files")
        data = path.read_bytes()
        expected[path.name] = (len(data), "sha256:" + hashlib.sha256(data).hexdigest())
    if not expected:
        raise GitHubReleaseError("verified assets directory must not be empty")
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise GitHubReleaseError("existing release has no assets list; reconcile it manually")
    actual: dict[str, tuple[int, str]] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise GitHubReleaseError("existing release contains an invalid asset")
        name = asset.get("name")
        size = asset.get("size")
        digest = asset.get("digest")
        if (
            not isinstance(name, str)
            or name in actual
            or type(size) is not int
            or size < 0
            or not isinstance(digest, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None
            or asset.get("state") != "uploaded"
        ):
            raise GitHubReleaseError("existing release has unverified or duplicate assets; reconcile it manually")
        actual[name] = (size, digest)
    for name in actual.keys() - expected.keys():
        parent = name.removesuffix(".publish.attestation")
        if (
            not name.endswith(".publish.attestation")
            or parent not in expected
            or not parent.endswith((".whl", ".tar.gz"))
        ):
            raise GitHubReleaseError("existing release has unrelated extra assets; reconcile it manually")
        size, digest = actual[name]
        _verify_attestation(
            repository=repository, tag=tag, name=name, parent_digest=expected[parent][1], size=size, digest=digest
        )
    actual = {name: identity for name, identity in actual.items() if name in expected}
    if actual != expected:
        raise GitHubReleaseError("existing release assets differ from the verified files; reconcile it manually")
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Check whether publication can create a release or reuse its exact assets."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--assets-dir", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--require-existing", action="store_true")
    args = parser.parse_args(argv)
    try:
        status, payload = fetch_release(repository=args.repository, tag=args.tag, token=os.environ.get("GH_TOKEN", ""))
        exists = verify_release(
            status=status,
            payload=payload,
            tag=args.tag,
            repository=args.repository,
            assets_dir=args.assets_dir,
            require_existing=args.require_existing,
        )
        result = f"release_exists={'true' if exists else 'false'}\n"
        if args.github_output is not None:
            with args.github_output.open("a", encoding="utf-8") as output:
                output.write(result)
    except (GitHubReleaseError, OSError, ValueError) as error:
        sys.stderr.write(f"GitHub Release verification error: {error}\n")
        return 1
    sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
