"""The ``citry watch`` command: hot-reload component files during development."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from citry.command import CommandArg, style_success, style_warning
from citry.extension import ExtensionCommand
from citry.reload import watch

if TYPE_CHECKING:
    from citry.component import Component


class WatchCommand(ExtensionCommand):
    """Watch component files and reload changed templates, JS, and CSS in place."""

    name = "watch"
    help = "Watch component files and hot-reload changed templates/JS/CSS."
    arguments = (
        CommandArg(
            ["--path", "-p"],
            action="append",
            help="A directory to watch (repeatable). Defaults to the engine's configured dirs.",
        ),
    )

    def handle(self, **kwargs: Any) -> None:
        # Bound by the runner; absent only if invoked outside the CLI.
        if self.citry is None:
            return

        given = kwargs.get("path")
        roots = [Path(entry) for entry in given] if given else None

        def report(changed: set[Path], reset: list[type[Component]]) -> None:
            names = ", ".join(cls.__name__ for cls in reset) or "no loaded component"
            for changed_path in sorted(changed):
                print(style_success(f"reloaded {changed_path}") + f" ({names})")

        try:
            handle = watch(self.citry, roots=roots, on_reload=report)
        except ValueError as exc:
            print(style_warning(str(exc)))
            raise SystemExit(1) from exc

        print("citry: watching for component file changes (Ctrl-C to stop)")
        try:
            handle.wait()
        except KeyboardInterrupt:
            pass
        finally:
            handle.stop()
        print("citry: stopped watching")
