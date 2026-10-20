"""Run a framework's static stages on one working copy and capture what each tool printed, unparsed."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .work import command_env, env_dir, placeholder

if TYPE_CHECKING:
    from pathlib import Path

    from .config import Framework


@dataclass(frozen=True)
class StageOutput:
    """What one stage's command printed, kept unparsed so a parser change needs no rerun."""

    argv: list[str]
    stdout: str = ""
    stderr: str = ""
    # None when the command ran past the stage's timeout and was stopped.
    exit_code: int | None = None
    timeout: int = 0

    @property
    def timed_out(self) -> bool:
        return self.exit_code is None


def run_stages(framework: Framework, work: Path) -> list[StageOutput]:
    """Run every static stage of one framework on one working copy, in the order framework.toml lists them."""
    env = env_dir(framework)
    outputs = []
    for stage in framework.stages:
        argv = [placeholder(part, framework, env, work) for part in stage.argv]
        try:
            completed = subprocess.run(
                argv,
                cwd=work,
                env=command_env(framework, env, work, stage.env),
                capture_output=True,
                text=True,
                timeout=stage.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            outputs.append(StageOutput(argv, timeout=stage.timeout))
            continue
        outputs.append(StageOutput(argv, completed.stdout, completed.stderr, completed.returncode, stage.timeout))
    return outputs
