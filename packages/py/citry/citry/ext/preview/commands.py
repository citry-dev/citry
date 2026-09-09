"""CLI entry points sharing one command-owned preview host."""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, cast

from citry.command import CommandArg
from citry.ext.preview.capture import capture, fetch_catalog, preflight, validate_remote_catalog
from citry.ext.preview.extension import PreviewExtension, Selection
from citry.ext.preview.host import PreviewServer
from citry.ext.preview.rendering import PreviewRenderer
from citry.ext.preview.routes import preview_routes
from citry.extension import ExtensionCommand

_SELECTION_ARGS = (
    CommandArg("components", nargs="?", help="Comma-separated registered component names."),
    CommandArg(
        ["--dir", "-d"], action="append", dest="dirs", help="Component source paths relative to the working directory."
    ),
    CommandArg("--variant", action="append", dest="variants", help="Select a variant slug on each component."),
)


def _renderer(
    command: ExtensionCommand, components: str | None, dirs: list[str] | None, variants: list[str] | None
) -> PreviewRenderer:
    if command.citry is None:
        raise ValueError("Select a Citry app with --app module:app.")
    names = tuple(name.strip() for name in components.split(",")) if components is not None else ()
    if any(not name for name in names):
        raise ValueError("Component names must not contain empty comma-separated entries.")
    selection = Selection(names, tuple(dirs or ()), tuple(variants or ()), Path.cwd())
    extension = cast("PreviewExtension", command.citry.extensions.get_extension("preview"))
    command.citry.initialize()
    return PreviewRenderer(extension, selection)


class ServeCommand(ExtensionCommand):
    """Keep preview pages and their gallery available until interrupted."""

    name = "serve"
    help = "Serve component previews and the gallery without launching a browser."
    arguments = (
        *_SELECTION_ARGS,
        CommandArg("--port", type=int, default=8001, help="Loopback port; 0 selects a free port."),
    )

    def handle(
        self,
        components: str | None = None,
        dirs: list[str] | None = None,
        variants: list[str] | None = None,
        port: int = 8001,
        **_kwargs: Any,
    ) -> None:
        """Start the isolated host; Ctrl-C stops only the owned server."""
        try:
            renderer = _renderer(self, components, dirs, variants)
            renderer.catalog(urls=False)
            with PreviewServer(renderer.citry, preview_routes(renderer), port=port) as server:
                sys.stdout.write(f"Preview gallery: {server.base_url}/ext/preview/gallery\n")
                sys.stdout.write(f"Preview catalog: {server.base_url}/ext/preview/catalog\n")
                sys.stdout.flush()
                server.wait()
        except KeyboardInterrupt:
            return
        except Exception as exc:
            sys.stderr.write(f"Preview serve failed: {exc}\n")
            raise SystemExit(1) from exc


class RenderCommand(ExtensionCommand):
    """Capture each selected variant through the same pages served by serve."""

    name = "render"
    help = "Capture component preview PNGs with Chromium."
    arguments = (
        *_SELECTION_ARGS,
        CommandArg(["--outdir", "-o"], default="./preview_imgs", help="PNG and manifest output directory."),
        CommandArg("--overwrite", action="store_true", help="Replace selected output files."),
        CommandArg("--base-url", help="Mounted Citry root of an existing preview serve session."),
        CommandArg("--timeout", type=float, default=30.0, help="Maximum seconds per variant."),
        CommandArg("--ready-selector", help="Wait for an application-owned visible element."),
    )

    def handle(
        self,
        components: str | None = None,
        dirs: list[str] | None = None,
        variants: list[str] | None = None,
        outdir: str = "./preview_imgs",
        overwrite: bool = False,
        base_url: str | None = None,
        timeout: float = 30.0,
        ready_selector: str | None = None,
        **_kwargs: Any,
    ) -> None:
        """Capture independently and return a nonzero exit status on any failure."""
        try:
            if not math.isfinite(timeout) or timeout <= 0:
                raise ValueError("Preview timeout must be positive and finite.")
            renderer = _renderer(self, components, dirs, variants)
            local = renderer.catalog(urls=False)
            if not local["components"]:
                sys.stdout.write("No component previews are available.\n")
                return
            preflight(local, Path(outdir), overwrite=overwrite)
            options: dict[str, Any] = {"overwrite": overwrite, "timeout": timeout, "ready_selector": ready_selector}
            if base_url is not None:
                remote = validate_remote_catalog(local, fetch_catalog(base_url), base_url)
                manifest = capture(remote, base_url, Path(outdir), **options)
            else:
                with PreviewServer(renderer.citry, preview_routes(renderer)) as server:
                    manifest = capture(renderer.catalog(), server.base_url, Path(outdir), **options)
            sys.stdout.write(f"Captured {len(manifest['captures'])} previews in {outdir}.\n")
        except KeyboardInterrupt as exc:
            sys.stderr.write("Preview capture interrupted.\n")
            raise SystemExit(130) from exc
        except Exception as exc:
            sys.stderr.write(f"Preview capture failed: {exc}\n")
            raise SystemExit(1) from exc
