"""
Keep GitHub Actions caches out of the package publish workflows.

A cache restored on `main` may have been saved by any earlier run on `main`,
in any workflow, by any action that run used. A release job that restores one
lets every one of those runs choose files that end up in the bytes it builds
or publishes. So every job in a `*--publish.yml` workflow starts from a clean
runner instead, and pays for it with a cold build.

This validator reads each publish workflow as YAML and reports:

- a step that uses an action outside a short list of actions reviewed for
  caching, so a new action (including one that caches by default, such as
  setup-go) needs a review and an entry here before a release job can use it;
- a reviewed action whose cache is not turned off: setup-uv must set
  `enable-cache: false` and setup-node `package-manager-cache: false`,
  because both cache by default, and no step may set a `cache` or `sccache`
  input to anything but false;
- a job that calls a reusable workflow, whose steps this validator cannot see;
- any mention of sccache in an `env:` entry, a `run:` script, or an action
  input, because sccache can save to and restore from the GitHub Actions
  cache (`SCCACHE_GHA_ENABLED`), and a script can turn it on through
  `$GITHUB_ENV`.
"""

from pathlib import Path

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]

# Every action a publish job may use, compared without the `@ref` and in
# lower case, as GitHub matches action names. Each maps to the input that
# turns off a cache the action would otherwise use by default, or None when
# the action caches only through a `cache` or `sccache` input, or not at all.
_REVIEWED_ACTIONS: dict[str, str | None] = {
    "actions/attest-build-provenance": None,
    "actions/checkout": None,
    "actions/create-github-app-token": None,
    "actions/download-artifact": None,
    "actions/setup-node": "package-manager-cache",
    "actions/setup-python": None,
    "actions/upload-artifact": None,
    "astral-sh/setup-uv": "enable-cache",
    "dtolnay/rust-toolchain": None,
    "pnpm/action-setup": None,
    "pyo3/maturin-action": None,
    "pypa/gh-action-pypi-publish": None,
}
# Inputs that, set to anything but false, make an action restore a cache.
_CACHE_INPUTS = ("cache", "sccache")
_REASON = "publish jobs must not restore or save a cache"


def _is_explicitly_false(value: object) -> bool:
    """Read an off switch: only `false` turns it off, since setup-node reads an empty value as on."""
    return value is False or str(value).strip().lower() == "false"


def _input_is_off(value: object) -> bool:
    """Read a `cache` or `sccache` input: `false`, `"false"`, and an empty value leave the cache off."""
    return value is None or _is_explicitly_false(value) or str(value).strip() == ""


def _mentions_sccache(value: object) -> bool:
    return "sccache" in str(value).lower()


def _env_errors(where: str, env: object) -> list[str]:
    """Report an `env:` block that sends the Rust compiler through sccache or turns on its Actions storage."""
    if not isinstance(env, dict):
        return []
    return [
        f"{where} sets {name}; {_REASON}"
        for name, value in env.items()
        if _mentions_sccache(name) or _mentions_sccache(value)
    ]


def _step_errors(where: str, step: dict[str, object]) -> list[str]:
    """Report a step that restores or saves a cache, or uses an action nobody reviewed for caching."""
    errors = _env_errors(where, step.get("env"))
    # A script can turn sccache on for later steps through $GITHUB_ENV.
    if _mentions_sccache(step.get("run", "")):
        errors.append(f"{where} mentions sccache in its script; {_REASON}")
    callee = str(step.get("uses", "")).split("@", 1)[0].strip().lower()
    if not callee:
        return errors
    if callee not in _REVIEWED_ACTIONS:
        errors.append(
            f"{where} uses {callee}, which is not reviewed for caching; "
            "check its defaults and add it to release_caches.py"
        )
        return errors
    raw = step.get("with")
    # GitHub matches input names without regard to case.
    settings = {str(key).lower(): value for key, value in raw.items()} if isinstance(raw, dict) else {}
    errors.extend(
        f"{where} sets {name}: {settings[name]!r} on {callee}; {_REASON}"
        for name in _CACHE_INPUTS
        if name in settings and not _input_is_off(settings[name])
    )
    # An input that passes options through, such as maturin's docker-options,
    # could still turn sccache on.
    errors.extend(
        f"{where} mentions sccache in its {name} input; {_REASON}"
        for name, value in settings.items()
        if name != "sccache" and _mentions_sccache(value)
    )
    off_switch = _REVIEWED_ACTIONS[callee]
    # A missing input leaves the action's own default, which caches.
    if off_switch and not _is_explicitly_false(settings.get(off_switch)):
        errors.append(f"{where} must set {off_switch}: false on {callee}; {_REASON}")
    return errors


def check(root: Path = ROOT) -> list[str]:
    """Report every cache a publish workflow would restore or save."""
    errors: list[str] = []
    directory = root / ".github" / "workflows"
    # GitHub runs both spellings of the YAML extension.
    paths = sorted([*directory.glob("*--publish.yml"), *directory.glob("*--publish.yaml")])
    for path in paths:
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(workflow, dict):
            continue
        # Messages name files with forward slashes on every OS, as the repository does.
        label = path.relative_to(root).as_posix()
        errors.extend(_env_errors(label, workflow.get("env")))
        jobs = workflow.get("jobs")
        for job_name, job in (jobs if isinstance(jobs, dict) else {}).items():
            if not isinstance(job, dict):
                continue
            where = f"{label} job {job_name}"
            if job.get("uses"):
                errors.append(f"{where} calls a reusable workflow, whose caches this validator cannot check")
            errors.extend(_env_errors(where, job.get("env")))
            for index, step in enumerate(job.get("steps") or [], start=1):
                if isinstance(step, dict):
                    name = step.get("name") or step.get("uses") or f"#{index}"
                    errors.extend(_step_errors(f"{where} step {name!r}", step))
    return errors
