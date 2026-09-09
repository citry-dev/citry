"""Cache final strings after live primitive attribute contribution collection."""

from __future__ import annotations
import __future__

import ast
import inspect
import textwrap
from threading import RLock
from typing import Any

from citry import attrs, client_directives, nodes
from citry.extension import ExtensionManager

NODE = nodes.ElementAttrsNode
ORIGINAL = NODE.render
METHODS = {
    name: getattr(NODE, name)
    for name in ("_resolve", "_resolve_with_spread", "_runtime_extension_candidate", "_format")
}
MANAGER_METHODS = {
    name: getattr(ExtensionManager, name)
    for name in ("has_attrs_resolved_hook", "_attrs_resolved_extensions", "_extensions_with_hook")
}
MERGE_HELPERS = {
    name: getattr(attrs, name)
    for name in (
        "_merge_resolved_attrs",
        "_normalize_class_contributions",
        "_merge_class_strings",
        "_class_tokens",
        "_collect_class",
        "_collect_style",
        "parse_string_style",
    )
}
PROPS_HELPERS = (
    nodes.has_client_props_key,
    client_directives.has_client_props_key,
    client_directives.is_client_props_key,
)
CACHE: dict[tuple[Any, ...], str] = {}
LOCK = RLock()


def method_tree(function: Any) -> tuple[ast.Module, int]:
    """Read the exact source whose collection and finishing paths are being split."""
    source, line = inspect.getsourcelines(function)
    return ast.parse(textwrap.dedent("".join(source))), line


def compile_method(tree: ast.Module, line: int, name: str) -> Any:
    """Share runtime globals so live helper calls keep their original targets."""
    tree.body[0].name = name
    tree.body[0].decorator_list = []
    ast.fix_missing_locations(tree)
    ast.increment_lineno(tree, line - 1)
    exec(  # noqa: S102 - benchmark-only extraction from inspected runtime methods
        compile(tree, ORIGINAL.__code__.co_filename, "exec", flags=__future__.annotations.compiler_flag),
        nodes.__dict__,
    )
    return nodes.__dict__[name]


spread, line = method_tree(METHODS["_resolve_with_spread"])
if not isinstance(spread.body[0].body[-1], ast.Return):
    raise TypeError("The spread resolver shape changed")
spread.body[0].body[-1].value = ast.Name(id="items", ctx=ast.Load())
COLLECT_SPREAD = compile_method(spread, line, "_probe_collect_spread")
plain, line = method_tree(METHODS["_resolve"])
branch = plain.body[0].body[1]
if not isinstance(branch, ast.If) or not isinstance(branch.body[-1], ast.Assign):
    raise TypeError("The ordinary resolver shape changed")
plain.body[0].body = [*branch.body[:-1], ast.Return(value=ast.Name(id="items", ctx=ast.Load()))]
COLLECT_PLAIN = compile_method(plain, line, "_probe_collect_plain")
finish, line = method_tree(METHODS["_resolve"])
finish.body[0].args.args.append(ast.arg(arg="items"))
finish.body[0].body = ast.parse("merged = _merge_resolved_attrs(items)").body + finish.body[0].body[2:]
FINISH_RESOLVE = compile_method(finish, line, "_probe_finish_resolve")
finish_render, line = method_tree(ORIGINAL)
finish_render.body[0].args.args.append(ast.arg(arg="items"))
finish_render.body[0].body[0] = ast.parse("resolved = _probe_finish_resolve(self, context, items)").body[0]
FINISH = compile_method(finish_render, line, "_probe_finish_render")


def key_for(items: list[Any]) -> tuple[Any, ...] | None:
    """Admit immutable values whose ordered contributions can identify final text."""
    if len(items) > 16:
        return None
    chars = 0
    for key, value in items:
        if (
            type(key) is not str
            or key.lower().startswith(("#", "$", "@c-", ":c-", "c-$c-"))
            or key.lower().startswith("data-cev")
        ):
            return None
        chars += len(key)
        if type(value) is str:
            chars += len(value)
        elif value is not None and type(value) is not bool:
            return None
        if chars > 2048:
            return None
    return tuple(items)


def eligible(node: Any, context: Any) -> bool:
    """Keep changed helpers and applicable attrs hooks on the original finishing path."""
    if not attrs._has_default_attr_formatting(nodes._format_resolved_attrs_to_str):
        return False
    if nodes._merge_resolved_attrs is not MERGE_HELPERS["_merge_resolved_attrs"]:
        return False
    if any(getattr(attrs, name) is not original for name, original in MERGE_HELPERS.items()):
        return False
    if (
        nodes.has_client_props_key is not PROPS_HELPERS[0]
        or client_directives.has_client_props_key is not PROPS_HELPERS[1]
        or client_directives.is_client_props_key is not PROPS_HELPERS[2]
    ):
        return False
    component = context.component
    if component is None:
        return True
    manager = component.citry.extensions
    if type(manager) is not ExtensionManager:
        return False
    if any(
        getattr(type(manager), name) is not original or name in manager.__dict__
        for name, original in MANAGER_METHODS.items()
    ):
        return False
    runtime_candidate = node._has_runtime_events_candidate if not node._has_spread else False
    return not manager.has_attrs_resolved_hook(runtime_candidate=runtime_candidate)


def render(self: Any, context: Any) -> Any:
    """Reuse only final text; expressions and spread validation still run each time."""
    if type(self) is not NODE or any(
        getattr(type(self), name) is not original or name in self.__dict__ for name, original in METHODS.items()
    ):
        return ORIGINAL(self, context)
    items = COLLECT_SPREAD(self, context) if self._has_spread else COLLECT_PLAIN(self, context)
    key = key_for(items)
    can_reuse = key is not None and eligible(self, context)
    if can_reuse:
        cached = CACHE.get(key)
        if cached is not None:
            return cached
    output = FINISH(self, context, items)
    if can_reuse and type(output) is str and eligible(self, context):
        with LOCK:
            if key not in CACHE and len(CACHE) >= 256:
                CACHE.pop(next(iter(CACHE)))
            CACHE[key] = output
    return output


def install(changed: bool) -> None:
    """Start each comparison with empty caches and its selected node renderer."""
    CACHE.clear()
    nodes._attrs_output_cache.clear()
    NODE.render = render if changed else ORIGINAL
