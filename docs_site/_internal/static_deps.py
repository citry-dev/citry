"""
Write Citry's client runtimes to disk for the static build.

A page that uses a component with JavaScript loads Citry's small client runtime
(the part that wires up component scripts in the browser). Interactive examples
also load the Events runtime. When the live dev server runs, both are served
from the ``/citry`` mount. A built site is just flat files with no server, so
the build writes both runtimes under ``<output>/citry/`` at the URLs emitted by
the pages.

The runtime is written for every build. With the default ``document``
serialization each component's own JS and CSS, and any per-instance data scripts,
are placed directly inside the page that uses them, so they need no separate file.
The one exception is a ``fragment`` (an HTML fragment loaded on demand): it
references its component's JS/CSS by URL (``<prefix>/cache/<class_id>.js``) so the
client runtime can fetch them when the fragment is inserted. The dev server serves
those from the component class; a static site has none, so ``export_fragment_deps``
writes them as flat files at the same URLs. Only the fragments example needs this.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
