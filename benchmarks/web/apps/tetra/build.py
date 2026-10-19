"""Build this adapter's component assets during preparation, before measurement."""

import base64
import hashlib
import io
import json
import platform
import tarfile
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


def build() -> None:
    here = Path(__file__).parent
    key = (
        ("darwin" if platform.system() == "Darwin" else "linux")
        + "-"
        + {
            "arm64": "arm64",
            "aarch64": "arm64",
            "x86_64": "x64",
        }[platform.machine()]
    )
    if platform.system() not in ("Darwin", "Linux"):
        raise ValueError("This adapter build currently supports macOS and Linux")
    source = json.loads((here / "esbuild.json").read_text())[key]
    url = source["url"]
    if urlsplit(url).scheme != "https":
        raise ValueError("esbuild archive URL must use HTTPS")
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 - HTTPS is required above.
        archive = response.read()
    actual = "sha512-" + base64.b64encode(hashlib.sha512(archive).digest()).decode()
    if actual != source["integrity"]:
        raise ValueError("esbuild archive differs from its pinned integrity")
    target = here / "generated"
    target.mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        member = tar.getmember("package/bin/esbuild")
        if not member.isfile():
            raise ValueError("esbuild archive member is not a regular file")
        binary = tar.extractfile(member)
        if binary is None:
            raise ValueError("esbuild archive has no executable")
        (target / "esbuild").write_bytes(binary.read())
    (target / "esbuild").chmod(0o755)
    (target / "esbuild-provenance.json").write_text(
        json.dumps(
            {
                "version": "0.27.2",
                "platform": key,
                **source,
                "archive_sha256": hashlib.sha256(archive).hexdigest(),
                "binary_sha256": hashlib.sha256((target / "esbuild").read_bytes()).hexdigest(),
                "member": "package/bin/esbuild",
            },
            indent=2,
        )
        + "\n"
    )
    # Import only after installing the compiler; no build runs during app startup.
    import app  # noqa: F401, PLC0415
    from django.core.management import call_command  # noqa: PLC0415

    call_command("tetrabuild", "board_app.default")
    output = here / "board_app" / "static" / "board_app" / "tetra" / "default"
    built = {}
    for extension in ("js", "css"):
        name = (output / f"board_app_default.{extension}.filename").read_text().strip()
        if Path(name).name != name or not name.endswith(f".{extension}"):
            raise ValueError("Tetra emitted an invalid component asset filename")
        data = (output / name).read_bytes()
        if not data:
            raise ValueError("Tetra emitted an empty component asset")
        built[str((output / name).relative_to(here))] = hashlib.sha256(data).hexdigest()
    (target / "component-assets.json").write_text(json.dumps(built, indent=2) + "\n")


if __name__ == "__main__":
    build()
