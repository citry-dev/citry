"""
The built-in ``citry`` command-line commands and the tree builder.

:func:`build_cli` assembles the root command tree for a resolved ``Citry``
engine: the core ``check``, ``format``, ``list``, ``inspect``, ``create``, and
``watch`` commands plus ``citry ext list`` and
``citry ext run <extension> <command>``. The tree is built per invocation
because the ``ext run`` subcommands depend on which extensions the engine has
installed.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Any, cast

from citry._app_selection import CheckAppSelection
from citry.command import CommandArg
from citry.commands.check import build_check_command
from citry.commands.create import CreateCommand
from citry.commands.ext_list import ExtListCommand
from citry.commands.format import FormatCommand
from citry.commands.inspect import InspectCommand
from citry.commands.list import ListCommand
from citry.commands.watch import WatchCommand
from citry.extension import ExtensionCommand

if TYPE_CHECKING:
    from collections.abc import Sequence

    from citry.citry import Citry


def _citry_version() -> str:
    """The installed ``citry`` version, or ``"unknown"`` if it cannot be read."""
    try:
        return version("citry")
    except PackageNotFoundError:
        return "unknown"


def grouping_command(
    name: str,
    help_text: str,
    subcommands: Sequence[type[ExtensionCommand]],
    arguments: Sequence[CommandArg] = (),
) -> type[ExtensionCommand]:
    """
    Synthesize a command that routes to ``subcommands`` (and may carry ``arguments``).

    It has no ``handle`` of its own, so invoking it without a subcommand prints
    its help. Used for the command-tree nodes (``citry``, ``ext``, ``run``, and
    the per-extension routing nodes) whose shape depends on the live engine.
    """
    class_name = f"{name.replace('-', ' ').title().replace(' ', '')}Command"
    namespace: dict[str, Any] = {
        "name": name,
        "help": help_text,
        "subcommands": tuple(subcommands),
        "arguments": tuple(arguments),
    }
    return cast("type[ExtensionCommand]", type(class_name, (ExtensionCommand,), namespace))


def build_ext_run_command(citry: Citry) -> type[ExtensionCommand]:
    """
    Build the ``run`` command, with one routing node per extension that declares
    commands. ``citry ext run <extension> <command>`` resolves to that extension's
    command; ``citry ext run <extension>`` (no command) lists what it offers.
    """
    routing = [
        grouping_command(name, f"Commands provided by the {name!r} extension.", commands)
        for name, commands in citry.commands.items()
    ]
    return grouping_command("run", "Run a command provided by an extension.", routing)


def build_cli(citry: Citry, *, check_selection: CheckAppSelection | None = None) -> type[ExtensionCommand]:
    """Build the root command tree, binding ``check`` to ``citry`` by default."""
    if check_selection is None:
        check_selection = CheckAppSelection(engine=citry)
    ext = grouping_command(
        "ext",
        "Inspect and run extension commands.",
        (ExtListCommand, build_ext_run_command(citry)),
    )
    return grouping_command(
        "citry",
        "Fully typed frontend framework for Python with server events and Alpine.js, inspired by Vue and Livewire.",
        (
            build_check_command(check_selection),
            FormatCommand,
            ListCommand,
            InspectCommand,
            CreateCommand,
            WatchCommand,
            ext,
        ),
        arguments=(CommandArg("--version", action="version", version=f"citry {_citry_version()}"),),
    )
