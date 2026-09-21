"""
Write Citry's client runtimes and prepared assets to the static build.

A page that uses a component with JavaScript loads Citry's small client runtime
(the part that wires up component scripts in the browser). Interactive examples
also load the Events runtime. When the live dev server runs, both are served
from the ``/citry`` mount. A built site is just flat files with no server, so
the build writes both runtimes under ``<output>/citry/`` at the URLs emitted by
the pages.

The runtime is written for every build. Prepared document serialization retains
owned JS and CSS as content-addressed browser assets, so the build exports the
artifacts referenced by the generated prepared manifests. A ``fragment`` (an
HTML fragment loaded on demand) also
references its component's JS/CSS by URL (``<prefix>/cache/<class_id>.js``) so the
client runtime can fetch them when the fragment is inserted. The dev server serves
those from the component class; a static site has none, so ``export_fragment_deps``
writes them as flat files at the same URLs. Only the fragments example needs this.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from lxml import html as lxml_html

from citry.ext.dependencies.routes import RUNTIME_PATH as DEPENDENCIES_RUNTIME_PATH
from citry.ext.events.routes import (
    EVENTS_RUNTIME_SRC,
)
from citry.ext.events.routes import (
    RUNTIME_PATH as EVENTS_RUNTIME_PATH,
)

if TYPE_CHECKING:
    from pathlib import Path

    from citry import Citry
    from citry.component import Component

# Where the build serves Citry's routes from (the dev server uses the same
# value). The runtime is written under this prefix so the URL the pages emit,
# "<prefix>/citry.js", resolves to the file on disk.
CITRY_MOUNT_PREFIX = "/citry"


def export_runtime(output_dir: Path, citry_instance: Citry) -> Path:
    """
    Write the client runtimes and return the base runtime path.

    The destination mirrors the URL the pages reference: a prefix of ``/citry``
    writes ``<output_dir>/citry/citry.js`` and
    ``<output_dir>/citry/ext/events/runtime.js``.
    """
    # _runtime_js() returns the runtime source (shipped with citry as package
    # data); it is exactly what the "/citry/citry.js" route serves at runtime.
    from citry.ext.dependencies.emission import _runtime_js  # noqa: PLC0415

    prefix = (citry_instance.mounted_prefix or CITRY_MOUNT_PREFIX).strip("/")
    dest = output_dir / prefix / DEPENDENCIES_RUNTIME_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_runtime_js(), encoding="utf-8")

    events_dest = output_dir / prefix / EVENTS_RUNTIME_PATH
    events_dest.parent.mkdir(parents=True, exist_ok=True)
    events_dest.write_bytes(EVENTS_RUNTIME_SRC.read_bytes())
    return dest


def _prepared_owned_assets(html: str, citry_instance: Citry) -> set[tuple[str, str]]:
    """Read owned asset identities from exact generated prepared calls."""
    document = lxml_html.document_fromstring(html)
    marker = "CitryStable.startPrepared("
    suffix = ").catch(error => queueMicrotask(() => { throw error; }));"
    digest_pattern = re.compile(r"[0-9a-f]{64}")
    prefix = (citry_instance.mounted_prefix or CITRY_MOUNT_PREFIX).strip("/")
    referenced: set[tuple[str, str]] = set()
    decoder = json.JSONDecoder()

    def collect(manifest: object) -> None:
        if type(manifest) is not dict or manifest.get("protocol") != "citry-vue-prepared/1":
            raise RuntimeError("A generated prepared transport has invalid manifest metadata.")
        definitions = manifest.get("definitions")
        if type(definitions) is not list:
            raise RuntimeError("A generated prepared manifest has invalid definition metadata.")
        for asset in definitions:
            digest = asset.get("sha256") if type(asset) is dict else None
            if type(digest) is not str or digest_pattern.fullmatch(digest) is None:
                raise RuntimeError("A generated prepared manifest has an invalid definition digest.")
            expected = f"/{prefix}/ext/events/definitions/{digest}.js"
            if asset.get("url") != expected:
                raise RuntimeError("A generated prepared manifest has an unexpected definition URL.")
            referenced.add(("js", digest))
        for collection, extension in (("scripts", "js"), ("styles", "css")):
            values = manifest.get(collection)
            if type(values) is not list:
                raise RuntimeError("A generated prepared manifest has invalid asset metadata.")
            for asset in values:
                asset_source = asset.get("source") if type(asset) is dict else None
                if type(asset_source) is not dict or asset_source.get("kind") != "owned":
                    continue
                digest = asset_source.get("sha256")
                if type(digest) is not str or digest_pattern.fullmatch(digest) is None:
                    raise RuntimeError("A generated prepared manifest has an invalid owned asset digest.")
                directory = "definitions" if extension == "js" else "assets"
                expected = f"/{prefix}/ext/events/{directory}/{digest}.{extension}"
                if asset_source.get("url") != expected:
                    raise RuntimeError("A generated prepared manifest has an unexpected owned asset URL.")
                referenced.add((extension, digest))

    bootstrap_prefix = f"(function() {{\n{marker}"
    bootstrap_suffix = f"{suffix}\n}})();"
    for script in document.xpath("//script[not(@src)]"):
        source = script.text or ""
        if source.startswith(bootstrap_prefix) and source.endswith(bootstrap_suffix):
            payload, consumed = decoder.raw_decode(source[len(bootstrap_prefix) :])
            if source[len(bootstrap_prefix) + consumed :] != bootstrap_suffix:
                raise RuntimeError("A generated prepared bootstrap has invalid framing.")
            collect(payload.get("manifest") if type(payload) is dict else None)
            continue
        if script.get("type") != "application/json" or script.get("data-citry-vue-fragment") is None:
            continue
        fragment = json.loads(source)
        vue = fragment.get("vue") if type(fragment) is dict else None
        prepared = vue.get("prepared") if type(vue) is dict else None
        if type(vue) is not dict or vue.get("protocol") != "citry-vue-fragment/1" or type(prepared) is not dict:
            raise RuntimeError("A generated prepared fragment has invalid metadata.")
        collect(prepared.get("manifest"))
    return referenced


def export_prepared_page_assets(html: str, output_dir: Path, citry_instance: Citry) -> list[Path]:
    """Export retained artifacts immediately after rendering one prepared page."""
    from citry._vue.events import definition_bundle, style_asset  # noqa: PLC0415

    prefix = (citry_instance.mounted_prefix or CITRY_MOUNT_PREFIX).strip("/")
    written: list[Path] = []
    for extension, digest in sorted(_prepared_owned_assets(html, citry_instance)):
        content = (
            definition_bundle(citry_instance, digest) if extension == "js" else style_asset(citry_instance, digest)
        )
        if content is None:
            raise RuntimeError(f"A prepared {extension} asset referenced by the docs build was not retained.")
        directory = "definitions" if extension == "js" else "assets"
        dest = output_dir / prefix / "ext" / "events" / directory / f"{digest}.{extension}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        written.append(dest)
    return written


def validate_prepared_assets(output_dir: Path, citry_instance: Citry) -> None:
    """Require every completed page's prepared owned assets to exist."""
    prefix = (citry_instance.mounted_prefix or CITRY_MOUNT_PREFIX).strip("/")
    for html_path in output_dir.rglob("*.html"):
        for extension, digest in _prepared_owned_assets(html_path.read_text(encoding="utf-8"), citry_instance):
            directory = "definitions" if extension == "js" else "assets"
            if not (output_dir / prefix / "ext" / "events" / directory / f"{digest}.{extension}").is_file():
                raise RuntimeError("A prepared asset referenced by the docs build was not exported.")


def export_fragment_deps(output_dir: Path, comp_cls: type[Component]) -> list[Path]:
    """
    Write a component's class-level JS/CSS to the URLs a rendered fragment fetches.

    A ``fragment`` render points the client runtime at ``<prefix>/cache/<class_id>.js``
    and ``.css`` (whichever the component has). The dev server serves those from the
    class; here we write them as flat files at the same paths, next to the runtime,
    so an inserted fragment loads its assets on a static site. Returns the files
    written (empty if the component ships no JS or CSS).
    """
    from citry.ext.dependencies.routes import script_url  # noqa: PLC0415
    from citry.ext.dependencies.scripts import get_component_script  # noqa: PLC0415

    written: list[Path] = []
    for script_type in ("js", "css"):
        script = get_component_script(script_type, comp_cls)
        if script is None or script.content is None:
            continue
        # script_url() -> "<prefix>/cache/<class_id>.<type>"; drop the leading
        # slash so it joins under output_dir, matching the runtime's layout.
        dest = output_dir / script_url(comp_cls, script_type).lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(script.content, encoding="utf-8")
        written.append(dest)
    return written
