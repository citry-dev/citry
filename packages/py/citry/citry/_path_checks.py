"""
Ask the host web app whether it serves a path, so a link to a missing page or file is reported before anyone clicks it.

Citry does not know the routes or static files of the app it is mounted in.
The framework integrations do: ``citry.contrib.flask.mount()``,
``citry.contrib.fastapi.mount()`` and ``citry.contrib.django.urlpatterns()``
each register a path checker on the Citry instance they receive. A path
checker is a function that takes one root-relative path, such as
``/about``, and answers whether one of the host's routes or static files
serves it. ``citry check`` and the editor's app worker then call the
registered checkers for each literal ``href``, ``src`` and ``action`` path
in the app's templates.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

from citry._inline_assets import normalize_inline_asset
from citry._linting import _component_lint_info
from citry._markup_lint import one_slip_from
from citry._registry_lint import template_urls
from citry.assets import _find_pair_declaration, _inspect_asset_path, module_dir
from citry_core.template_parser import parse_template

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from citry.citry import Citry


@dataclass(frozen=True, slots=True)
class PathLookup:
    """
    What a host's path checker knows about one path.

    Attributes:
        found: Whether one of the host's routes or static files serves the path.
        nearby: For a path the host does not serve, paths it does serve that a
            reader may have meant, such as the literal routes and the files
            in the same static folder. Citry suggests one of them when it is
            one typing slip away.

    """

    found: bool
    nearby: tuple[str, ...] = ()


# A function that answers for one root-relative path as the browser requests it: decoded,
# with `.` and `..` segments resolved, and without the query and fragment.
PathChecker: TypeAlias = "Callable[[str], PathLookup]"


@dataclass(frozen=True, slots=True)
class PathVerdict:
    """
    The answer for one path once every registered checker has been asked.

    Attributes:
        found: Whether any checker, or Citry's own routes, serves the path.
        suggestion: For a missing path, a served path one typing slip away.

    """

    found: bool
    suggestion: str | None = None


@dataclass(frozen=True, slots=True)
class PathCheckResults:
    """
    The verdicts for a set of paths, and the paths no verdict could be given for.

    Attributes:
        verdicts: Each path a checker answered for, by path.
        failures: Each path a checker raised on, with the error, in path
            order. Such a path is not reported, because the failing checker
            may serve it.

    """

    verdicts: dict[str, PathVerdict] = field(default_factory=dict)
    failures: tuple[tuple[str, str], ...] = ()


def register_path_checker(engine: Citry, checker: PathChecker, *, host: object = None) -> None:
    """
    Let ``citry check`` and the editor ask the host app whether it serves a path.

    The framework integrations call this from ``mount()`` or
    ``urlpatterns()``. The checker runs only when a check asks for it, so it
    sees the routes the app adds after mounting Citry. ``host`` is the app
    the checker asks: mounting Citry into the same app again replaces its
    checker, so an app that a test or factory builds again and again does
    not leave old apps' routes behind to hide a typo.
    """
    if host is not None:
        engine._path_checkers[:] = [entry for entry in engine._path_checkers if entry[0] is not host]
    engine._path_checkers.append((host, checker))


def has_path_checkers(engine: Citry) -> bool:
    """Return whether any integration registered a path checker on ``engine``."""
    return bool(engine._path_checkers)


def is_citry_path(engine: Citry, path: str) -> bool:
    """Return whether ``path`` is under the prefix Citry's own routes are mounted at."""
    prefix = engine.mounted_prefix
    return bool(prefix) and (path == prefix or path.startswith(f"{prefix}/"))


def check_paths(engine: Citry, paths: Iterable[str], *, deadline: float | None = None) -> PathCheckResults:
    """
    Ask every registered checker about each path, and suggest a served path for a missing one.

    A path under the prefix Citry's own routes are mounted at is served by
    Citry, so it is found without asking. A path is found when any checker
    finds it, because an app may mount Citry into more than one host. A
    checker that raises leaves its path without a verdict. Past
    ``deadline``, a ``time.monotonic()`` value, the remaining paths get no
    verdict either, so a slow host cannot hold up the caller.
    """
    checkers = tuple(checker for _host, checker in engine._path_checkers)
    verdicts: dict[str, PathVerdict] = {}
    failures: list[tuple[str, str]] = []
    for path in sorted(set(paths)):
        if deadline is not None and time.monotonic() > deadline:
            break
        if is_citry_path(engine, path):
            verdicts[path] = PathVerdict(found=True)
            continue
        nearby: set[str] = set()
        failure = None
        found = False
        for checker in checkers:
            try:
                lookup = checker(path)
            except Exception as exc:  # noqa: BLE001 - a host's routing code may raise anything
                failure = _error_detail(exc)
                continue
            if lookup.found:
                found = True
                break
            nearby.update(lookup.nearby)
        if found:
            verdicts[path] = PathVerdict(found=True)
        elif failure is not None:
            failures.append((path, failure))
        else:
            verdicts[path] = PathVerdict(found=False, suggestion=_suggestion(path, nearby))
    return PathCheckResults(verdicts, tuple(failures))


def _suggestion(path: str, nearby: set[str]) -> str | None:
    """Return the first served path, in sorted order, that ``path`` misspells by one slip."""
    for candidate in sorted(nearby):
        if candidate != path and one_slip_from(path, candidate):
            return candidate
    return None


def _error_detail(exc: BaseException) -> str:
    detail = str(exc)
    error_type = type(exc).__name__
    return f"{error_type}: {detail}" if detail else error_type


def engine_path_verdicts(engine: Citry) -> dict[str, object]:
    """
    Check every literal link path in the app's templates, for the editor's app worker.

    The worker runs once and exits, so the editor cannot call the host's
    checkers later. The worker sends these verdicts instead, and the editor
    reports only the paths checked when the app loaded. ``checked`` is false when
    no integration registered a checker, and the editor then reports nothing.
    """
    if not has_path_checkers(engine):
        return {"checked": False, "verdicts": {}}
    paths: set[str] = set()
    for component in {id(component): component for component in engine.components.values()}.values():
        # A component that turns the rule off needs no answers, and asking
        # costs the editor time while it loads the app.
        if engine._is_builtin_component(component):
            continue
        if _component_lint_info(engine, component).rule_unknown_url == "ignore":
            continue
        source = _template_source(engine, component)
        if source is None:
            continue
        try:
            template = parse_template(source)
        except (SyntaxError, ValueError):
            continue
        paths.update(url.path for url in template_urls(template, parse_nested=parse_template))
    # The worker must answer the editor within its own time limit, so a slow
    # host leaves the remaining links unchecked instead of failing the load.
    results = check_paths(engine, paths, deadline=time.monotonic() + _EDITOR_CHECK_SECONDS)
    return {
        "checked": True,
        "verdicts": {
            path: {"found": verdict.found, "suggestion": verdict.suggestion}
            for path, verdict in sorted(results.verdicts.items())
        },
    }


# How long the editor's app worker may spend asking the host about links.
# The worker's whole run is limited to 15 seconds (`WORKER_TIMEOUT_SECONDS`
# in citry_lsp), and importing the app usually takes most of that.
_EDITOR_CHECK_SECONDS = 3.0


def _template_source(engine: Citry, component: type) -> str | None:
    """Read one component's authored template, or ``None`` when it has none or it cannot be read."""
    try:
        owner, inline, filepath = _find_pair_declaration(component, "template", "template_file")
        if type(inline) is str:
            return normalize_inline_asset(inline)
        if not isinstance(filepath, (str, Path)):
            return None
        inspection = _inspect_asset_path(filepath, owner_dir=module_dir(owner), search_dirs=engine.settings.dirs)
        resolved = inspection.resolved_path
        return None if resolved is None else resolved.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001 - one unreadable template is left out; citry check reports it
        return None


__all__: list[str] = []
