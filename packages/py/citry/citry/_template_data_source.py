"""Conservative source-shape analysis for component data methods."""

from __future__ import annotations

import ast
import copy
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from citry.analysis import LspPosition, LspRange
from citry.util.css import validate_css_var_name

_MAX_FLOW_STATES = 32


@dataclass(frozen=True, slots=True)
class TemplateDataSourceDefinition:
    """One literal key and optional value expression in Python source."""

    key_range: LspRange
    value_range: LspRange | None


@dataclass(frozen=True, slots=True)
class TemplateDataSourceRoot:
    """One mapping key proven on at least one reachable return path."""

    name: str
    presence: Literal["always", "conditional"]
    origins: frozenset[Literal["literal", "kwargs"]]
    definitions: tuple[TemplateDataSourceDefinition, ...]


@dataclass(frozen=True, slots=True)
class TemplateDataSourceShape:
    """Known roots and whether arbitrary additional roots may exist."""

    roots: tuple[TemplateDataSourceRoot, ...]
    completeness: Literal["closed", "open"]
    open_reasons: tuple[str, ...]
    preserves_kwargs_extras: bool = False
    parameters: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _Root:
    origins: frozenset[Literal["literal", "kwargs"]]
    definitions: tuple[TemplateDataSourceDefinition, ...] = ()


@dataclass(slots=True)
class _Mapping:
    roots: dict[str, _Root] = field(default_factory=dict)
    open_reasons: set[str] = field(default_factory=set)
    tainted: bool = False
    kind: Literal["mapping", "kwargs"] = "mapping"

    def copy(self) -> _Mapping:
        return _Mapping(dict(self.roots), set(self.open_reasons), self.tainted, self.kind)


@dataclass(slots=True)
class _State:
    names: dict[str, int] = field(default_factory=dict)
    heap: dict[int, _Mapping] = field(default_factory=dict)
    next_id: int = 0

    def copy(self) -> _State:
        return _State(dict(self.names), {key: value.copy() for key, value in self.heap.items()}, self.next_id)

    def store(self, value: _Mapping) -> int:
        identity = self.next_id
        self.next_id += 1
        self.heap[identity] = value
        return identity


def analyze_template_data_source(
    source: str,
    class_qualname: str,
    *,
    kwargs_fields: tuple[str, ...] | None,
) -> TemplateDataSourceShape | None:
    """
    Infer roots from one exact, undecorated ``template_data`` method.

    ``None`` means the module or requested owner cannot be matched safely.
    Unsupported runtime shapes instead return an open result without guesses.
    """
    shape = _analyze_data_method_source(
        source,
        class_qualname,
        method_name="template_data",
        kwargs_fields=kwargs_fields,
    )
    if shape is None:
        return None
    invalid = tuple(root.name for root in shape.roots if not _template_root_name(root.name))
    if not invalid:
        return shape
    # Runtime dictionary keys are broader than template identifiers. Keep the
    # shared mapping analysis broad, then make the template namespace strict.
    reasons = (*shape.open_reasons, "computed or non-identifier mapping key")
    return TemplateDataSourceShape(
        tuple(root for root in shape.roots if _template_root_name(root.name)),
        "open",
        tuple(sorted(set(reasons))),
        shape.preserves_kwargs_extras,
        shape.parameters,
    )


def analyze_css_data_source(source: str, class_qualname: str) -> TemplateDataSourceShape | None:
    """Infer exact custom-property suffixes from one ``css_data`` method."""
    shape = _analyze_data_method_source(
        source,
        class_qualname,
        method_name="css_data",
        kwargs_fields=None,
    )
    if shape is None:
        return None
    retained = tuple(root for root in shape.roots if _css_root_name(root.name))
    if len(retained) == len(shape.roots):
        return shape
    reasons = (*shape.open_reasons, "invalid CSS custom-property mapping key")
    return TemplateDataSourceShape(retained, "open", tuple(sorted(set(reasons))), parameters=shape.parameters)


def analyze_js_data_source(source: str, class_qualname: str) -> TemplateDataSourceShape | None:
    """Infer exact browser-scope names from one ``js_data`` method."""
    shape = _analyze_data_method_source(
        source,
        class_qualname,
        method_name="js_data",
        kwargs_fields=None,
    )
    if shape is None:
        return None
    retained = tuple(root for root in shape.roots if _js_root_name(root.name))
    if len(retained) == len(shape.roots):
        return shape
    reasons = (*shape.open_reasons, "mapping key is not a JavaScript scope identifier")
    return TemplateDataSourceShape(retained, "open", tuple(sorted(set(reasons))), parameters=shape.parameters)


def _analyze_data_method_source(
    source: str,
    class_qualname: str,
    *,
    method_name: Literal["template_data", "js_data", "css_data"],
    kwargs_fields: tuple[str, ...] | None,
) -> TemplateDataSourceShape | None:
    """Run the mapping-flow pass for one exact component data method."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return None
    class_node = _class_for_qualname(tree, class_qualname)
    if class_node is None or class_node.decorator_list:
        return None
    bindings = [statement for statement in class_node.body if _statement_binds_name(statement, method_name)]
    if (
        len(bindings) != 1
        or not isinstance(bindings[0], ast.FunctionDef)
        or bindings[0].name != method_name
        or bindings[0].decorator_list
    ):
        return None
    method = bindings[0]
    positional = (*method.args.posonlyargs, *method.args.args)
    if _function_contains_yield(method):
        return TemplateDataSourceShape(
            (),
            "open",
            (f"generator {method_name} method",),
            preserves_kwargs_extras=False,
            parameters=tuple(argument.arg for argument in positional),
        )
    kwargs_name = positional[1].arg if method_name == "template_data" and len(positional) >= 2 else None
    initial = _State()
    if kwargs_name is not None:
        initial.names[kwargs_name] = initial.store(_kwargs_mapping(kwargs_fields))
    returns, falls_through = _analyze_block(
        source,
        method.body,
        [initial],
        kwargs_name=kwargs_name,
        kwargs_fields=kwargs_fields,
    )
    if falls_through:
        returns.append(_Mapping())
    if not returns:
        returns.append(_Mapping(open_reasons={"method has no reachable normal return"}))
    return _merge_returns(returns, tuple(argument.arg for argument in positional))


def python_class_defines_direct_method(source: str, class_qualname: str, method_name: str) -> bool | None:
    """Return direct method presence, or ``None`` for unprovable source."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return None
    class_node = _class_for_qualname(tree, class_qualname)
    if class_node is None or class_node.decorator_list:
        return None
    matches = [statement for statement in class_node.body if _statement_binds_name(statement, method_name)]
    if len(matches) > 1:
        return None
    return bool(matches)


def python_class_direct_method_first_line(
    source: str,
    class_qualname: str,
    method_name: str,
) -> int | None:
    """Return the authored first line of one exact direct function binding."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return None
    class_node = _class_for_qualname(tree, class_qualname)
    if class_node is None:
        return None
    bindings = [statement for statement in class_node.body if _statement_binds_name(statement, method_name)]
    if len(bindings) != 1 or not isinstance(bindings[0], ast.FunctionDef) or bindings[0].name != method_name:
        return None
    method = bindings[0]
    return min((decorator.lineno for decorator in method.decorator_list), default=method.lineno)


def python_class_resolution_signature(source: str, class_qualname: str) -> str | None:
    """Fingerprint source that can change one loaded class resolution chain."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return None
    class_node = _class_for_qualname(tree, class_qualname)
    if class_node is None:
        return None
    _canonicalize_resolution_source(tree, _local_resolution_classes(tree, class_node))
    fingerprint = ast.dump(tree, annotate_fields=True, include_attributes=False)
    return hashlib.sha256(fingerprint.encode()).hexdigest()


def python_class_asset_resolution_signature(
    source: str,
    class_qualname: str,
    kind: Literal["template", "js", "css"] = "template",
) -> str | None:
    """Fingerprint class resolution and asset bindings while ignoring typed interfaces."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return None
    class_node = _class_for_qualname(tree, class_qualname)
    if class_node is None or _class_has_dynamic_asset_namespace(class_node):
        return None
    if _static_asset_declarations(tree, class_node, kind) is None:
        return None
    asset_classes = {*_asset_component_classes(tree), id(class_node)}
    _canonicalize_resolution_source(
        tree,
        _local_resolution_classes(tree, class_node),
        omit_component_interfaces=True,
        asset_classes=asset_classes,
    )
    # A per-class dependency closure keeps an edit to one shared-template
    # consumer from invalidating unrelated consumers in the same module. The
    # closure still retains imports, aliases, selectors, and base classes that
    # can change this class's effective MRO or asset declaration.
    target_projection = _asset_class_projection(class_node, kind)
    pending = {
        node.id
        for node in ast.walk(target_projection)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    included: dict[int, ast.AST] = {}
    seen_names: set[str] = set()
    while pending - seen_names:
        name = (pending - seen_names).pop()
        seen_names.add(name)
        for index, statement in enumerate(tree.body):
            if statement is class_node or not _statement_binds_name(statement, name):
                continue
            projection = (
                _asset_class_projection(statement, kind)
                if isinstance(statement, ast.ClassDef) and id(statement) in asset_classes
                else statement
            )
            included[index] = projection
            pending.update(
                node.id
                for node in ast.walk(projection)
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
            )
    fingerprint = repr(
        (
            class_qualname,
            ast.dump(target_projection, annotate_fields=True, include_attributes=False),
            tuple(
                (index, ast.dump(statement, annotate_fields=True, include_attributes=False))
                for index, statement in sorted(included.items())
            ),
        )
    )
    return hashlib.sha256(fingerprint.encode()).hexdigest()


def python_class_static_asset_matches(
    source: str,
    class_qualname: str,
    inline_value: object,
    file_value: object,
    kind: Literal["template", "js", "css"] = "template",
) -> bool:
    """Prove that one direct static asset declaration matches runtime state."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return False
    class_node = _class_for_qualname(tree, class_qualname)
    if class_node is None:
        return False
    if _module_has_direct_asset_mutation(tree, kind):
        return False
    declarations = _static_asset_declarations(tree, class_node, kind)
    if not declarations:
        return False
    inline = declarations.get(kind)
    file = declarations.get(f"{kind}_file")
    return _static_asset_value_matches(inline, inline_value) and _static_asset_value_matches(file, file_value)


def _static_asset_declarations(
    tree: ast.Module,
    node: ast.ClassDef,
    kind: Literal["template", "js", "css"] = "template",
) -> dict[str, tuple[Literal["literal", "path"], str | None]] | None:
    """Return direct, side-effect-free asset values or decline the class."""
    declarations: dict[str, tuple[Literal["literal", "path"], str | None]] = {}
    for statement in node.body:
        names = [name for name in (kind, f"{kind}_file") if _statement_binds_name(statement, name)]
        if not names:
            continue
        if len(names) != 1 or names[0] in declarations:
            return None
        name = names[0]
        value: ast.expr | None = None
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == name
        ) or (isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)):
            value = statement.value
        if value is None:
            return None
        descriptor = _static_asset_value(tree, node, name, value)
        if descriptor is None:
            return None
        declarations[name] = descriptor
    return declarations


def _static_asset_value(
    tree: ast.Module,
    class_node: ast.ClassDef,
    name: str,
    value: ast.expr,
) -> tuple[Literal["literal", "path"], str | None] | None:
    if isinstance(value, ast.Constant) and (type(value.value) is str or value.value is None):
        return "literal", value.value
    if not name.endswith("_file") or not isinstance(value, ast.Call) or value.keywords or len(value.args) != 1:
        return None
    argument = value.args[0]
    if not isinstance(argument, ast.Constant) or type(argument.value) is not str:
        return None
    path_names, pathlib_names = _pathlib_bindings_before(tree, class_node)
    direct_path = isinstance(value.func, ast.Name) and value.func.id in path_names
    qualified_path = (
        isinstance(value.func, ast.Attribute)
        and value.func.attr == "Path"
        and isinstance(value.func.value, ast.Name)
        and value.func.value.id in pathlib_names
    )
    if not direct_path and not qualified_path:
        return None
    return "path", argument.value


def _pathlib_bindings_before(tree: ast.Module, class_node: ast.ClassDef) -> tuple[set[str], set[str]]:
    path_names: set[str] = set()
    pathlib_names: set[str] = set()
    for statement in tree.body:
        if statement is class_node:
            break
        for name in tuple(path_names):
            if _statement_binds_name(statement, name):
                path_names.remove(name)
        for name in tuple(pathlib_names):
            if _statement_binds_name(statement, name):
                pathlib_names.remove(name)
        if isinstance(statement, ast.ImportFrom) and statement.module == "pathlib" and statement.level == 0:
            for alias in statement.names:
                if alias.name == "Path":
                    path_names.add(alias.asname or alias.name)
        elif isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name == "pathlib":
                    pathlib_names.add(alias.asname or alias.name)
    return path_names, pathlib_names


def _static_asset_value_matches(
    descriptor: tuple[Literal["literal", "path"], str | None] | None,
    runtime_value: object,
) -> bool:
    if descriptor is None:
        return runtime_value is None
    kind, value = descriptor
    if kind == "literal":
        return (runtime_value is None or type(runtime_value) is str) and runtime_value == value
    expected = Path(value or "")
    return type(runtime_value) is type(expected) and runtime_value == expected


def _asset_class_projection(
    node: ast.ClassDef,
    kind: Literal["template", "js", "css"] = "template",
) -> ast.ClassDef:
    """Keep only class statements that can select one effective asset."""
    projected = copy.deepcopy(node)
    names = ("citry", kind, f"{kind}_file", f"{kind}_lang")
    projected.body = [
        statement for statement in projected.body if any(_statement_binds_name(statement, name) for name in names)
    ] or [ast.Pass()]
    return projected


def _class_has_dynamic_asset_namespace(node: ast.ClassDef) -> bool:
    """Reject class construction that can hide an asset binding from the AST."""
    if node.decorator_list or any(keyword.arg == "metaclass" for keyword in node.keywords):
        return True
    dynamic_names = {"exec", "locals", "vars"}
    for statement in node.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if statement.name == "__init_subclass__":
                return True
            continue
        if isinstance(statement, ast.ClassDef):
            continue
        if any(
            isinstance(candidate, ast.Call)
            and isinstance(candidate.func, ast.Name)
            and candidate.func.id in dynamic_names
            for candidate in ast.walk(statement)
        ):
            return True
    return False


def _module_has_direct_asset_mutation(
    tree: ast.Module,
    kind: Literal["template", "js", "css"] = "template",
) -> bool:
    """Reject post-class asset writes whose target identity may be aliased."""
    asset_names = {kind, f"{kind}_file"}
    for statement in tree.body:
        if isinstance(statement, ast.ClassDef):
            continue
        for candidate in ast.walk(statement):
            if (
                isinstance(candidate, ast.Attribute)
                and isinstance(candidate.ctx, (ast.Store, ast.Del))
                and candidate.attr in asset_names
            ):
                return True
            if not isinstance(candidate, ast.Call) or len(candidate.args) < 2:
                continue
            attribute_name = candidate.args[1]
            if not isinstance(attribute_name, ast.Constant) or attribute_name.value not in asset_names:
                continue
            if isinstance(candidate.func, ast.Name) and candidate.func.id in {"setattr", "delattr"}:
                return True
            if isinstance(candidate.func, ast.Attribute) and candidate.func.attr in {"__setattr__", "__delattr__"}:
                return True
    return False


def _analyze_block(
    source: str,
    statements: list[ast.stmt],
    states: list[_State],
    *,
    kwargs_name: str | None,
    kwargs_fields: tuple[str, ...] | None,
) -> tuple[list[_Mapping], list[_State]]:
    returns: list[_Mapping] = []
    active = states
    for statement in statements:
        if not active:
            break
        next_states: list[_State] = []
        for state in active:
            if isinstance(statement, ast.Raise):
                continue
            if isinstance(statement, ast.Return):
                returns.append(
                    _returned_mapping(
                        source,
                        statement.value,
                        state,
                        kwargs_name=kwargs_name,
                        kwargs_fields=kwargs_fields,
                    )
                )
                continue
            if isinstance(statement, ast.If):
                _taint_referenced_mappings(statement.test, state)
                _remove_bound_mapping_names(statement.test, state)
                truth = _constant_truth(statement.test)
                branches = (
                    (statement.body,)
                    if truth is True
                    else (statement.orelse,)
                    if truth is False
                    else (statement.body, statement.orelse)
                )
                for branch in branches:
                    branch_returns, branch_states = _analyze_block(
                        source,
                        branch,
                        [state.copy()],
                        kwargs_name=kwargs_name,
                        kwargs_fields=kwargs_fields,
                    )
                    returns.extend(branch_returns)
                    next_states.extend(branch_states)
                continue
            _apply_statement(
                source,
                statement,
                state,
                kwargs_name=kwargs_name,
                kwargs_fields=kwargs_fields,
            )
            next_states.append(state)
        if len(next_states) > _MAX_FLOW_STATES:
            return [
                _Mapping(open_reasons={"analysis branch limit exceeded"}, tainted=True),
            ], []
        active = next_states
    return returns, active


def _apply_statement(
    source: str,
    statement: ast.stmt,
    state: _State,
    *,
    kwargs_name: str | None,
    kwargs_fields: tuple[str, ...] | None,
) -> None:
    if any(isinstance(node, ast.NamedExpr) for node in ast.walk(statement)):
        _taint_referenced_mappings(statement, state)
        _remove_bound_mapping_names(statement, state)
        return
    if isinstance(statement, (ast.Assign, ast.AnnAssign)):
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        value = statement.value
        if len(targets) == 1 and isinstance(targets[0], ast.Name):
            target = targets[0].id
            if isinstance(value, ast.Name) and value.id in state.names:
                state.names[target] = state.names[value.id]
                return
            mapping = _mapping_expression(
                source,
                value,
                state,
                kwargs_name=kwargs_name,
                kwargs_fields=kwargs_fields,
            )
            if mapping is None:
                if value is not None:
                    _taint_referenced_mappings(value, state)
                state.names.pop(target, None)
            else:
                state.names[target] = state.store(mapping)
            return
        if len(targets) == 1 and isinstance(targets[0], ast.Subscript):
            _assign_subscript(source, targets[0], value, state)
            return
        _taint_referenced_mappings(statement, state)
        _remove_bound_mapping_names(statement, state)
        return
    if (
        isinstance(statement, ast.AugAssign)
        and isinstance(statement.op, ast.BitOr)
        and isinstance(statement.target, ast.Name)
        and statement.target.id in state.names
    ):
        update = _mapping_expression(
            source,
            statement.value,
            state,
            kwargs_name=kwargs_name,
            kwargs_fields=kwargs_fields,
        )
        mapping = state.heap[state.names[statement.target.id]]
        if mapping.kind == "kwargs":
            _taint_referenced_mappings(statement.value, state)
            mapping.tainted = True
            mapping.open_reasons.add("kwargs carrier used as a mutable mapping")
            return
        if update is None:
            _taint_referenced_mappings(statement.value, state)
            mapping.tainted = True
            mapping.open_reasons.add("unknown mapping union")
        else:
            _merge_mapping_write(mapping, update)
        return
    if isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
        identity = state.names.pop(statement.target.id, None)
        if identity is not None:
            mapping = state.heap[identity]
            mapping.tainted = True
            mapping.open_reasons.add("mapping used by unsupported augmented assignment")
        _taint_referenced_mappings(statement.value, state)
        return
    if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
        if _apply_known_call(source, statement.value, state, kwargs_name, kwargs_fields):
            return
        _taint_referenced_mappings(statement, state)
        return
    if isinstance(statement, ast.Delete):
        for delete_target in statement.targets:
            if isinstance(delete_target, ast.Subscript):
                _delete_subscript(delete_target, state)
            elif isinstance(delete_target, ast.Name):
                state.names.pop(delete_target.id, None)
            else:
                _taint_referenced_mappings(delete_target, state)
        return
    if isinstance(statement, (ast.Pass, ast.Global, ast.Nonlocal)):
        return
    # Loops, try/with/match, arbitrary stores, and nested scopes can mutate or
    # capture a tracked mapping. Taint only mappings they actually reference so
    # a later fresh literal can still be inferred.
    _taint_referenced_mappings(statement, state)
    _remove_bound_mapping_names(statement, state)


def _mapping_expression(
    source: str,
    expression: ast.expr | None,
    state: _State,
    *,
    kwargs_name: str | None,
    kwargs_fields: tuple[str, ...] | None,
) -> _Mapping | None:
    if isinstance(expression, ast.Dict):
        result = _Mapping()
        for key, value in zip(expression.keys, expression.values, strict=True):
            if key is None:
                unpacked = _unpacked_mapping(
                    source,
                    value,
                    state,
                    kwargs_name=kwargs_name,
                    kwargs_fields=kwargs_fields,
                )
                if unpacked is None:
                    _taint_referenced_mappings(value, state)
                    result.open_reasons.add("unknown mapping unpack")
                    result.roots = {name: _Root(root.origins) for name, root in result.roots.items()}
                else:
                    _merge_mapping_write(result, unpacked)
                continue
            _taint_referenced_mappings(key, state)
            _taint_referenced_mappings(value, state)
            name = _literal_root_name(key)
            if name is None:
                result.open_reasons.add("computed or non-identifier mapping key")
                result.roots = {root_name: _Root(root.origins) for root_name, root in result.roots.items()}
                continue
            result.roots[name] = _Root(
                frozenset({"literal"}),
                _source_definitions(source, key, value),
            )
        return result
    return None


def _unpacked_mapping(
    source: str,
    expression: ast.expr,
    state: _State,
    *,
    kwargs_name: str | None,
    kwargs_fields: tuple[str, ...] | None,
) -> _Mapping | None:
    if isinstance(expression, ast.Name):
        identity = state.names.get(expression.id)
        if identity is not None:
            mapping = state.heap[identity]
            if mapping.kind == "kwargs" or mapping.tainted:
                return None
            return mapping.copy()
    return _mapping_expression(
        source,
        expression,
        state,
        kwargs_name=kwargs_name,
        kwargs_fields=kwargs_fields,
    )


def _returned_mapping(
    source: str,
    expression: ast.expr | None,
    state: _State,
    *,
    kwargs_name: str | None,
    kwargs_fields: tuple[str, ...] | None,
) -> _Mapping:
    if expression is None or (isinstance(expression, ast.Constant) and expression.value is None):
        return _Mapping()
    if isinstance(expression, ast.Name):
        identity = state.names.get(expression.id)
        if identity is not None:
            returned = state.heap[identity].copy()
            if returned.tainted:
                return _Mapping(open_reasons={"mapping escaped to unsupported code"}, tainted=True)
            return returned
    expression_mapping = _mapping_expression(
        source,
        expression,
        state,
        kwargs_name=kwargs_name,
        kwargs_fields=kwargs_fields,
    )
    if expression_mapping is not None:
        return expression_mapping
    return _Mapping(open_reasons={"unsupported return expression"}, tainted=True)


def _kwargs_mapping(fields: tuple[str, ...] | None) -> _Mapping:
    if fields is None:
        return _Mapping(open_reasons={"kwargs schema is unavailable"}, kind="kwargs")
    return _Mapping(
        {name: _Root(frozenset({"kwargs"})) for name in fields},
        kind="kwargs",
    )


def _assign_subscript(source: str, target: ast.Subscript, value: ast.expr | None, state: _State) -> None:
    if not isinstance(target.value, ast.Name) or target.value.id not in state.names:
        _taint_referenced_mappings(target, state)
        if value is not None:
            _taint_referenced_mappings(value, state)
        return
    mapping = state.heap[state.names[target.value.id]]
    if mapping.kind == "kwargs":
        _taint_referenced_mappings(target.slice, state)
        if value is not None:
            _taint_referenced_mappings(value, state)
        mapping.tainted = True
        mapping.open_reasons.add("kwargs carrier used as a mutable mapping")
        return
    _taint_referenced_mappings(target.slice, state)
    if value is not None:
        _taint_referenced_mappings(value, state)
    name = _literal_root_name(target.slice)
    if name is None:
        mapping.open_reasons.add("computed mapping mutation")
        mapping.roots = {root_name: _Root(root.origins) for root_name, root in mapping.roots.items()}
        return
    mapping.roots[name] = _Root(
        frozenset({"literal"}),
        _source_definitions(source, target.slice, value),
    )


def _delete_subscript(target: ast.Subscript, state: _State) -> None:
    if not isinstance(target.value, ast.Name) or target.value.id not in state.names:
        return
    mapping = state.heap[state.names[target.value.id]]
    if mapping.kind == "kwargs":
        _taint_referenced_mappings(target.slice, state)
        mapping.tainted = True
        mapping.open_reasons.add("kwargs carrier used as a mutable mapping")
        return
    _taint_referenced_mappings(target.slice, state)
    name = _literal_root_name(target.slice)
    if name is None:
        mapping.tainted = True
        mapping.open_reasons.add("computed mapping deletion")
    else:
        mapping.roots.pop(name, None)


def _apply_known_call(
    source: str,
    call: ast.Call,
    state: _State,
    kwargs_name: str | None,
    kwargs_fields: tuple[str, ...] | None,
) -> bool:
    if not isinstance(call.func, ast.Attribute) or not isinstance(call.func.value, ast.Name):
        return False
    identity = state.names.get(call.func.value.id)
    if identity is None:
        return False
    mapping = state.heap[identity]
    if mapping.kind == "kwargs":
        return False
    if call.func.attr == "clear" and not call.args and not call.keywords:
        mapping.roots.clear()
        return True
    if call.func.attr == "pop" and len(call.args) in {1, 2} and not call.keywords:
        for argument in call.args:
            _taint_referenced_mappings(argument, state)
        name = _literal_root_name(call.args[0])
        if name is None:
            mapping.tainted = True
            mapping.open_reasons.add("computed mapping pop")
        else:
            mapping.roots.pop(name, None)
        return True
    if call.func.attr == "update" and len(call.args) <= 1:
        update = _Mapping()
        if call.args:
            unpacked = _unpacked_mapping(
                source,
                call.args[0],
                state,
                kwargs_name=kwargs_name,
                kwargs_fields=kwargs_fields,
            )
            if unpacked is None:
                _taint_referenced_mappings(call.args[0], state)
                mapping.open_reasons.add("unknown mapping update")
                mapping.roots = {name: _Root(root.origins) for name, root in mapping.roots.items()}
            else:
                _merge_mapping_write(update, unpacked)
        for keyword in call.keywords:
            if keyword.arg is None:
                _taint_referenced_mappings(keyword.value, state)
                mapping.open_reasons.add("unknown mapping update")
                mapping.roots = {name: _Root(root.origins) for name, root in mapping.roots.items()}
            else:
                _taint_referenced_mappings(keyword.value, state)
                update.roots[keyword.arg] = _Root(frozenset({"literal"}))
        _merge_mapping_write(mapping, update)
        return True
    return False


def _merge_mapping_write(target: _Mapping, source: _Mapping) -> None:
    target.roots.update(source.roots)
    target.open_reasons.update(source.open_reasons)
    target.tainted = target.tainted or source.tainted


def _taint_referenced_mappings(node: ast.AST, state: _State) -> None:
    referenced = {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id in state.names
    }
    for name in referenced:
        mapping = state.heap[state.names[name]]
        mapping.tainted = True
        mapping.open_reasons.add("mapping referenced by unsupported code")


def _remove_bound_mapping_names(node: ast.AST, state: _State) -> None:
    """Forget tracked locals rebound by an unsupported source shape."""
    for name in tuple(state.names):
        if _statement_binds_name(node, name):
            state.names.pop(name, None)


def _merge_returns(returns: list[_Mapping], parameters: tuple[str, ...]) -> TemplateDataSourceShape:
    names = sorted({name for returned in returns for name in returned.roots})
    roots: list[TemplateDataSourceRoot] = []
    for name in names:
        present = [returned.roots[name] for returned in returns if name in returned.roots]
        definitions = tuple(dict.fromkeys(definition for root in present for definition in root.definitions))
        roots.append(
            TemplateDataSourceRoot(
                name=name,
                presence="always" if len(present) == len(returns) else "conditional",
                origins=frozenset(origin for root in present for origin in root.origins),
                definitions=definitions,
            )
        )
    reasons = tuple(sorted({reason for returned in returns for reason in returned.open_reasons}))
    return TemplateDataSourceShape(
        roots=tuple(roots),
        completeness="open" if reasons or any(returned.tainted for returned in returns) else "closed",
        open_reasons=reasons,
        preserves_kwargs_extras=any(returned.kind == "kwargs" for returned in returns),
        parameters=parameters,
    )


def _literal_root_name(node: ast.expr) -> str | None:
    if not isinstance(node, ast.Constant) or type(node.value) is not str or not node.value:
        return None
    # Each public data surface applies its own name grammar after the shared
    # mapping-flow pass. Keeping literal strings here lets JS scope names use
    # their own identifier rules without weakening template or CSS analysis.
    return node.value


def _template_root_name(name: str) -> bool:
    try:
        parsed = ast.parse(name, mode="eval").body
    except SyntaxError:
        return False
    return isinstance(parsed, ast.Name) and parsed.id == name


def _css_root_name(name: str) -> bool:
    try:
        validate_css_var_name(name)
    except (TypeError, ValueError):
        return False
    return True


def _js_root_name(name: str) -> bool:
    """Keep names that can be seeded as unqualified browser variables."""
    return name.isidentifier() and not name.startswith("__")


def _class_for_qualname(tree: ast.Module, qualname: str) -> ast.ClassDef | None:
    if not qualname or "<locals>" in qualname:
        return None
    parts = qualname.split(".")
    bodies: list[list[ast.stmt]] = [tree.body]
    current: ast.ClassDef | None = None
    for part in parts:
        matches = [
            statement
            for body in bodies
            for statement in body
            if isinstance(statement, ast.ClassDef) and statement.name == part
        ]
        if len(matches) != 1:
            return None
        current = matches[0]
        bodies = [current.body]
    return current


def _local_resolution_classes(tree: ast.Module, target: ast.ClassDef) -> set[int]:
    """Find target and simple same-module bases whose live assets are editable."""
    classes: dict[str, ast.ClassDef] = {}
    aliases: dict[str, str] = {}
    for statement in tree.body:
        if isinstance(statement, ast.ClassDef):
            if statement.name in classes:
                classes.pop(statement.name, None)
            else:
                classes[statement.name] = statement
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and isinstance(statement.value, ast.Name)
        ):
            aliases[statement.target.id] = statement.value.id
        elif (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Name)
        ):
            aliases[statement.targets[0].id] = statement.value.id

    selected = {id(target)}
    pending = [target]
    while pending:
        current = pending.pop()
        for base in current.bases:
            if not isinstance(base, ast.Name):
                continue
            name = base.id
            seen: set[str] = set()
            while name in aliases and name not in seen:
                seen.add(name)
                name = aliases[name]
            candidate = classes.get(name)
            if candidate is not None and id(candidate) not in selected:
                selected.add(id(candidate))
                pending.append(candidate)
    return selected


def _asset_component_classes(tree: ast.Module) -> set[int]:
    """Find ordinary local component classes for asset-only canonicalization."""
    component_symbols: set[str] = set()
    citry_modules: set[str] = set()
    aliases: dict[str, str] = {}
    classes: dict[str, ast.ClassDef] = {}
    for statement in tree.body:
        if isinstance(statement, ast.ImportFrom) and statement.level == 0 and statement.module == "citry":
            for alias in statement.names:
                if alias.name in {"Component", "LibraryComponent"}:
                    component_symbols.add(alias.asname or alias.name)
        elif isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name == "citry":
                    citry_modules.add(alias.asname or alias.name)
        elif isinstance(statement, (ast.Assign, ast.AnnAssign)) and isinstance(statement.value, ast.Name):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            if len(targets) == 1 and isinstance(targets[0], ast.Name):
                aliases[targets[0].id] = statement.value.id
        elif isinstance(statement, ast.ClassDef):
            classes[statement.name] = statement

    selected: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, node in classes.items():
            if name in selected:
                continue
            is_component = False
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_name = base.id
                    seen: set[str] = set()
                    while base_name in aliases and base_name not in seen:
                        seen.add(base_name)
                        base_name = aliases[base_name]
                    is_component = base_name in component_symbols or base_name in selected
                elif (
                    isinstance(base, ast.Attribute)
                    and isinstance(base.value, ast.Name)
                    and base.value.id in citry_modules
                ):
                    is_component = base.attr in {"Component", "LibraryComponent"}
                if is_component:
                    break
            if is_component:
                selected.add(name)
                changed = True
    return {id(classes[name]) for name in selected}


def _canonicalize_resolution_source(
    tree: ast.Module,
    editable_classes: set[int],
    *,
    omit_component_interfaces: bool = False,
    asset_classes: set[int] | None = None,
) -> None:
    """Ignore only source edits that the LSP safely re-analyzes in place."""

    class Canonicalizer(ast.NodeTransformer):
        def __init__(self) -> None:
            self.class_stack: list[bool] = []
            self.asset_class_stack: list[bool] = []
            super().__init__()

        def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST | None:
            if (
                omit_component_interfaces
                and self.asset_class_stack
                and self.asset_class_stack[-1]
                and node.name in {"Kwargs", "Slots", "TemplateData", "JsData", "CssData"}
            ):
                return None
            self.class_stack.append(id(node) in editable_classes)
            self.asset_class_stack.append(asset_classes is not None and id(node) in asset_classes)
            self.generic_visit(node)
            self.asset_class_stack.pop()
            self.class_stack.pop()
            return node

        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
            if self.class_stack and (
                (self.asset_class_stack[-1] and omit_component_interfaces)
                or (self.class_stack[-1] and node.name in {"template_data", "js_data", "css_data"})
            ):
                node.body = [ast.Pass()]
                return node
            return self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
            if self.class_stack and (
                (self.asset_class_stack[-1] and omit_component_interfaces)
                or (self.class_stack[-1] and node.name in {"template_data", "js_data", "css_data"})
            ):
                node.body = [ast.Pass()]
                return node
            return self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> ast.AST:
            self.generic_visit(node)
            inline_assets = {
                target.id
                for target in node.targets
                if isinstance(target, ast.Name) and target.id in {"template", "js", "css"}
            }
            if (
                self.class_stack
                and ((self.asset_class_stack[-1] and omit_component_interfaces) or self.class_stack[-1])
                and len(inline_assets) == 1
                and isinstance(node.value, ast.Constant)
                and type(node.value.value) is str
            ):
                node.value = ast.Constant(f"<citry-inline-{next(iter(inline_assets))}>")
            return node

        def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
            self.generic_visit(node)
            if (
                self.class_stack
                and ((self.asset_class_stack[-1] and omit_component_interfaces) or self.class_stack[-1])
                and isinstance(node.target, ast.Name)
                and node.target.id in {"template", "js", "css"}
                and isinstance(node.value, ast.Constant)
                and type(node.value.value) is str
            ):
                node.value = ast.Constant(f"<citry-inline-{node.target.id}>")
            return node

    Canonicalizer().visit(tree)


def _constant_truth(node: ast.expr) -> bool | None:
    if isinstance(node, ast.Constant):
        return bool(node.value)
    return None


def _statement_binds_name(statement: ast.AST, name: str) -> bool:
    """Recognize any class-body path that may replace one direct binding."""
    found = False

    def visit(node: ast.AST) -> None:
        nonlocal found
        if found:
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found = node.name == name
            return
        if isinstance(node, ast.Lambda):
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            found = node.id == name
            return
        if isinstance(node, ast.alias):
            found = (node.asname or node.name.split(".", 1)[0]) == name
            return
        if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name == name:
            found = True
            return
        if isinstance(node, ast.MatchMapping) and node.rest == name:
            found = True
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(statement)
    return found


def _function_contains_yield(method: ast.FunctionDef) -> bool:
    """Detect generator behavior without descending into nested scopes."""

    def contains(node: ast.AST) -> bool:
        if isinstance(node, (ast.Yield, ast.YieldFrom)):
            return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            return False
        return any(contains(child) for child in ast.iter_child_nodes(node))

    return any(contains(statement) for statement in method.body)


def _node_range(source: str, node: ast.AST | None) -> LspRange | None:
    if node is None:
        return None
    lineno = getattr(node, "lineno", None)
    col_offset = getattr(node, "col_offset", None)
    end_lineno = getattr(node, "end_lineno", None)
    end_col_offset = getattr(node, "end_col_offset", None)
    if not isinstance(lineno, int) or not isinstance(col_offset, int):
        return None
    if not isinstance(end_lineno, int) or not isinstance(end_col_offset, int):
        return None
    return LspRange(
        _ast_position(source, lineno, col_offset),
        _ast_position(source, end_lineno, end_col_offset),
    )


def _source_definitions(
    source: str,
    key: ast.AST,
    value: ast.AST | None,
) -> tuple[TemplateDataSourceDefinition, ...]:
    key_range = _node_range(source, key)
    if key_range is None:
        return ()
    return (TemplateDataSourceDefinition(key_range, _node_range(source, value)),)


def _ast_position(source: str, lineno: int, byte_column: int) -> LspPosition:
    lines = source.splitlines(keepends=True)
    line = lines[lineno - 1]
    prefix = line.encode("utf-8")[:byte_column].decode("utf-8")
    return LspPosition(lineno - 1, len(prefix.encode("utf-16-le")) // 2)


__all__ = [
    "TemplateDataSourceDefinition",
    "TemplateDataSourceRoot",
    "TemplateDataSourceShape",
    "analyze_css_data_source",
    "analyze_js_data_source",
    "analyze_template_data_source",
    "python_class_asset_resolution_signature",
    "python_class_defines_direct_method",
    "python_class_direct_method_first_line",
    "python_class_resolution_signature",
    "python_class_static_asset_matches",
]
