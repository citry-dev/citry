"""
Check that the trust-boundary design doc names every extension hook, Events action, and security setting.

`docs/design/trust_boundaries.md` says, for each input that reaches the page,
who may supply it and which function checks it. A new extension hook or
Events action is the most likely way for a new input to reach the page, and
also the easiest to add without updating that doc. So this check reads the
places those names are declared and fails when one of them is not written
in the doc at the start of a code span (in backticks). It proves the doc mentions each name,
not that the row is right; the security pass checks the row.

The names come from the source, read as Python syntax rather than imported,
so the check stays fast and works without the packages installed:

- every public method of `Extension` in `citry/extension.py`;
- every hook an extension fires by name, from the string passed to
  `.emit("...")` or `_extensions_with_hook("...")` anywhere in the `citry`
  package (such as the Events extension's `on_event`);
- every name in `__all__` of `citry/ext/events/actions.py`, except the
  `Action` base class;
- every `security_*` field of the settings class in `citry/settings.py`.

A hook that does not reach the page still needs a mention, so that adding a
hook is a decision about the doc rather than something it misses.
"""

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DOC = Path("docs/design/trust_boundaries.md")
EXTENSION_MODULE = Path("packages/py/citry/citry/extension.py")
ACTIONS_MODULE = Path("packages/py/citry/citry/ext/events/actions.py")
SETTINGS_MODULE = Path("packages/py/citry/citry/settings.py")
PACKAGE_DIR = Path("packages/py/citry/citry")

# The two ways Citry calls a hook by its name; a call, not a docstring, so an
# example such as `emit("on_my_event", ...)` in prose is not picked up.
_HOOK_CALLERS = frozenset({"emit", "_extensions_with_hook"})

# `Action` is the shared base class; handlers return its subclasses, which
# are the names that carry a row.
_SKIPPED_ACTIONS = frozenset({"Action"})


def _class_named(tree: ast.Module, name: str) -> ast.ClassDef | None:
    return next((node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name), None)


def _extension_hooks(source: str) -> list[str]:
    extension = _class_named(ast.parse(source), "Extension")
    if extension is None:
        return []
    # Public methods and properties are the hooks an extension overrides;
    # `_` names are Citry's own helpers.
    return [
        node.name
        for node in extension.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and not node.name.startswith("_")
    ]


def _named_hooks(package: Path) -> list[str]:
    names: set[str] = set()
    for path in sorted(package.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in _HOOK_CALLERS
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                names.add(node.args[0].value)
    return sorted(names)


def _action_names(source: str) -> list[str]:
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        ):
            names = ast.literal_eval(node.value)
            return [name for name in names if name not in _SKIPPED_ACTIONS]
    return []


def _security_settings(source: str) -> list[str]:
    # The settings class is the one that declares `security_csp`; reading
    # every annotated `security_*` field there picks up a new one.
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.ClassDef):
            continue
        fields = [
            item.target.id
            for item in node.body
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
        ]
        if "security_csp" in fields:
            return [name for name in fields if name.startswith("security_")]
    return []


def _named_in_doc(doc: str, name: str) -> bool:
    # A name counts when it opens a code span, as in `on_serialize`,
    # `on_serialize()`, `Redirect(url=)`, or `Extension.urls`.
    return re.search(rf"`(?:Extension\.)?{re.escape(name)}[`(]", doc) is not None


def check(root: Path = REPO_ROOT) -> list[str]:
    doc_path = root / DOC
    if not doc_path.exists():
        return [f"{DOC} not found"]
    doc = doc_path.read_text(encoding="utf-8")

    sources = {
        "extension hook": (EXTENSION_MODULE, _extension_hooks),
        "Events action": (ACTIONS_MODULE, _action_names),
        "security setting": (SETTINGS_MODULE, _security_settings),
    }
    problems: list[str] = []
    # Hooks fired by name live across the package, so they are read from the
    # directory rather than from one module.
    package = root / PACKAGE_DIR
    hooks = _named_hooks(package) if package.is_dir() else []
    if not hooks:
        problems.append(f"found no hooks fired by name under {PACKAGE_DIR}; update {Path(__file__).name}")
    problems.extend(
        f"extension hook `{name}` (fired by name under {PACKAGE_DIR}) has no row in {DOC}; add one, or list it "
        "with the inputs that do not reach the page"
        for name in hooks
        if not _named_in_doc(doc, name)
    )
    for kind, (module, read_names) in sources.items():
        path = root / module
        if not path.exists():
            problems.append(f"{module} not found")
            continue
        names = read_names(path.read_text(encoding="utf-8"))
        if not names:
            # An empty list means the source changed shape, and the check
            # would otherwise pass without checking anything.
            problems.append(f"found no {kind} names in {module}; update {Path(__file__).name}")
            continue
        problems.extend(
            f"{kind} `{name}` ({module}) has no row in {DOC}; add one, or list it with the inputs that do not reach "
            "the page"
            for name in names
            if not _named_in_doc(doc, name)
        )
    return problems
