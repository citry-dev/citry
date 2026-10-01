"""Build analyzer-ready Python context for one authored template expression."""

from __future__ import annotations

import ast
import builtins
import copy
import itertools
import re
import symtable
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Literal

from citry_core.template_parser import HtmlAttrKind, TemplateElement, parse_template

if TYPE_CHECKING:
    from collections.abc import Callable

# A type display may use these names without importing them.
_BUILTIN_NAMES = frozenset(dir(builtins))


@dataclass(frozen=True, slots=True)
class TemplatePythonControl:
    """
    One enclosing condition, loop clause, or unknown lexical binding.

    Attributes:
        kind: Generated Python structure required for this scope.
        source: Authored Python expression or loop clause.
        names: Names introduced by an unknown lexical binding.
        free_names: Parser-proven free root names used by this control.

    """

    kind: Literal["if", "for", "unknown"]
    source: str
    names: tuple[str, ...] = ()
    free_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TemplatePythonQuery:
    """
    One exact Python host together with the controls active at that host.

    Attributes:
        source: Authored Python source copied into analyzer input.
        start_index: Inclusive UTF-8 byte index in the template.
        end_index: Exclusive UTF-8 byte index in the template.
        host_kind: Template construct that owns the expression.
        controls: Enclosing template controls in lexical order.
        free_names: Parser-proven free root names used by the expression.
        attribute_target: For a ``c-*`` attribute value, the tag as written
            and the attribute name without its ``c-`` prefix, such as
            ``("c-TaskCard", "task")``; otherwise ``None``.

    """

    source: str
    start_index: int
    end_index: int
    host_kind: Literal["interpolation", "attribute", "loop"]
    controls: tuple[TemplatePythonControl, ...] = ()
    free_names: tuple[str, ...] = ()
    attribute_target: tuple[str, str] | None = None


@dataclass(frozen=True, slots=True)
class TemplatePythonRoot:
    """
    One proven template name and how the shadow should read its value.

    Attributes:
        name: Exact Python identifier exposed to the template.
        presence: Whether every proven path includes the root.
        access: Runtime carrier access needed to read the value.
        type_module: Importable module that owns the field type, when proven.
        type_qualname: Qualified schema class that declares the field.
        type_display: Detached annotation text for an analysis-only variable.

    """

    name: str
    presence: Literal["always", "conditional"]
    access: Literal["mapping", "attribute", "mixed", "analysis"] = "mapping"
    type_module: str | None = None
    type_qualname: str | None = None
    type_display: str | None = None

    def __post_init__(self) -> None:
        try:
            parsed_name = ast.parse(self.name, mode="eval").body
        except (SyntaxError, UnicodeEncodeError, ValueError) as err:
            msg = f"Invalid template Python root name: {self.name!r}"
            raise ValueError(msg) from err
        if not isinstance(parsed_name, ast.Name) or parsed_name.id != self.name:
            msg = f"Invalid template Python root name: {self.name!r}"
            raise ValueError(msg)
        if self.presence not in {"always", "conditional"}:
            msg = f"Invalid template Python root presence: {self.presence!r}"
            raise ValueError(msg)
        if self.access not in {"mapping", "attribute", "mixed", "analysis"}:
            msg = f"Invalid template Python root access: {self.access!r}"
            raise ValueError(msg)
        if (self.type_module is None) != (self.type_qualname is None):
            msg = "Template Python root type provenance must provide both module and qualified name"
            raise ValueError(msg)
        if self.type_display is not None:
            display = _canonical_type_display(self.type_display)
            if display is None:
                msg = f"Invalid template Python root type display: {self.type_display!r}"
                raise ValueError(msg)
            object.__setattr__(self, "type_display", display)


@dataclass(frozen=True, slots=True)
class TemplatePythonValueType:
    """
    The type an attribute value must have, so the analyzer checks the value against it.

    A ``c-task="..."`` value on ``<c-TaskCard>`` must match the child's
    ``Kwargs.task`` annotation. The generated Python assigns the authored
    value to a variable annotated with this type, so ty reports a mismatch
    on the value itself.

    Attributes:
        annotation: A Python annotation written the way Citry formats schema
            types, such as ``app.store.Task | None`` or ``Task``.
        module: The module whose names an unqualified annotation uses, such
            as the module that declares the child's ``Kwargs``.

    """

    annotation: str
    module: str | None = None


@dataclass(frozen=True, slots=True)
class ShadowPythonCopy:
    """
    One generated copy of the queried authored expression.

    Attributes:
        shadow_start: Inclusive Python string index in generated source.
        shadow_end: Exclusive Python string index in generated source.
        template_start: Inclusive UTF-8 byte index in the template.
        template_end: Exclusive UTF-8 byte index in the template.

    """

    shadow_start: int
    shadow_end: int
    template_start: int
    template_end: int


@dataclass(frozen=True, slots=True)
class ShadowPythonSourceCopy:
    """
    One unchanged source-module range retained in the virtual document.

    Attributes:
        shadow_start: Inclusive Python string index in generated source.
        shadow_end: Exclusive Python string index in generated source.
        source_start: Inclusive Python string index in source input.
        source_end: Exclusive Python string index in source input.

    """

    shadow_start: int
    shadow_end: int
    source_start: int
    source_end: int


@dataclass(frozen=True, slots=True)
class ShadowPythonDocument:
    """
    A virtual Python document and every exact authored expression copy.

    Attributes:
        source: Complete generated Python source.
        copies: Exact authored template expression copies.
        source_copies: Unchanged ranges copied from the Python source input.
        query_function: Start and end string offsets of the generated
            ``__citry_analyze_template`` function, from the start of its
            ``def`` line to the end of its body, so a caller can cut it out
            without parsing the source again; ``None`` when unknown.

    """

    source: str
    copies: tuple[ShadowPythonCopy, ...]
    source_copies: tuple[ShadowPythonSourceCopy, ...] = ()
    query_function: tuple[int, int] | None = None


def template_python_query_at(
    template: Any,
    index: int,
    *,
    parse_nested: Callable[[str], Any] = parse_template,
) -> TemplatePythonQuery | None:
    """Return the Python expression or loop clause containing one parser byte index."""
    if type(index) is not int or index < 0:
        return None
    return _query_in_template(template, index, (), base_index=0, parse_nested=parse_nested)


def template_python_queries(
    template: Any,
    *,
    parse_nested: Callable[[str], Any] = parse_template,
) -> tuple[TemplatePythonQuery, ...]:
    """Return every Python-valued host with its exact lexical context."""
    indexes = _query_start_indexes(template, base_index=0, parse_nested=parse_nested)
    queries: list[TemplatePythonQuery] = []
    seen: set[tuple[int, int, str]] = set()
    for index in sorted(indexes):
        query = _query_in_template(template, index, (), base_index=0, parse_nested=parse_nested)
        if query is None:
            continue
        key = query.start_index, query.end_index, query.host_kind
        if key not in seen:
            seen.add(key)
            queries.append(query)
    return tuple(queries)


def template_static_input_queries(
    template: Any,
    *,
    parse_nested: Callable[[str], Any] = parse_template,
) -> tuple[TemplatePythonQuery, ...]:
    """
    Return a query for each quoted static attribute on a ``c-*`` component tag.

    ``<c-TaskCard lane="todo">`` passes the string ``"todo"`` as the
    ``lane`` input, so the quoted text, quotes included, is a Python string
    literal with the value the child receives, and it can be checked
    against the child's input type like a ``c-lane`` value. Citry passes the
    text as written, without decoding character references, so the literal
    matches it exactly. A value with a backslash, which Python would read
    as an escape, or with a line break, which a quoted literal cannot hold,
    is left out, and so is an unquoted or empty value: an empty or missing
    value passes ``True``.
    """
    queries: list[TemplatePythonQuery] = []
    _collect_static_input_queries(template, queries, base_index=0, parse_nested=parse_nested)
    return tuple(sorted(queries, key=lambda query: query.start_index))


def _collect_static_input_queries(
    template: Any,
    queries: list[TemplatePythonQuery],
    *,
    base_index: int,
    parse_nested: Callable[[str], Any],
) -> None:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node: Any = element._0
        tag_name = node.start_tag.name.content
        for attr in node.start_tag.attrs:
            name = attr.key.content
            value = attr.value
            if attr.kind == HtmlAttrKind.Template and attr.inner_value is not None:
                nested = _nested_template(attr.inner_value.content, parse_nested)
                if nested is not None:
                    nested_template, nested_start = nested
                    _collect_static_input_queries(
                        nested_template,
                        queries,
                        base_index=base_index + attr.inner_value.start_index + nested_start,
                        parse_nested=parse_nested,
                    )
                continue
            if (
                attr.kind != HtmlAttrKind.Static
                or not tag_name.lower().startswith("c-")
                or value is None
                or attr.quote_char not in {'"', "'"}
                or attr.inner_value is None
                or not attr.inner_value.content
                or "\\" in value.content
                or "\n" in value.content
                or "\r" in value.content
            ):
                continue
            queries.append(
                TemplatePythonQuery(
                    value.content,
                    base_index + value.start_index,
                    base_index + value.end_index,
                    "attribute",
                    attribute_target=(tag_name, name),
                )
            )
        body = getattr(node, "body", None)
        if body is not None:
            _collect_static_input_queries(body, queries, base_index=base_index, parse_nested=parse_nested)


def build_inferred_template_shadow(
    module_source: str,
    class_qualname: str,
    roots: tuple[TemplatePythonRoot, ...],
    query: TemplatePythonQuery,
    *,
    source_module: str | None = None,
    source_is_package: bool = False,
    kwargs_type: tuple[str, str] | None = None,
    value_type: TemplatePythonValueType | None = None,
) -> ShadowPythonDocument | None:
    """
    Copy one proven ``template_data`` method and evaluate the query at each return.

    With ``value_type``, such as a component input's type, the generated
    code also assigns the query's value to a variable annotated with that
    type, so ty checks the value against it.
    """
    tree = _parsed_module(module_source)
    if tree is None:
        return None
    class_node = _class_for_qualname(tree, class_qualname)
    if class_node is None or class_node.decorator_list:
        return None
    methods = [
        statement
        for statement in class_node.body
        if isinstance(statement, ast.FunctionDef) and statement.name == "template_data"
    ]
    if len(methods) != 1:
        return None
    # citry.analysis imports this module at load time and the data-method
    # analyzer imports citry.analysis, so importing it here breaks the cycle.
    from citry._template_data_source import data_method_call_parameters  # noqa: PLC0415

    # Only an instance, static, or class method has a known call shape. The
    # copy keeps that decorator, so the kwargs annotation must go on the same
    # parameter the runtime fills with kwargs.
    call_parameters = data_method_call_parameters(tree, class_node, methods[0])
    if call_parameters is None:
        return None
    # The call parameters are the tail of the positional list, after any receiver.
    positional_count = len(methods[0].args.posonlyargs) + len(methods[0].args.args)
    kwargs_index = positional_count - len(call_parameters) if call_parameters else None

    placeholder = _query_placeholder(
        module_source,
        roots,
        query,
        generated_inputs=(source_module or "", *(kwargs_type or ()), *_value_type_inputs(value_type)),
    )
    value_check = _value_check(value_type, module_source, roots, query, source_module=source_module)
    # The generated code binds template names inside this copied method, so a
    # method local with the same name, such as `resolved: list[Row]` next to a
    # template loop `c-for="resolved in items"`, would lend its declared type
    # to the template name. Renaming those locals gives each template name its
    # own type, while the copied method computes the same value.
    conflicts = _renamable_method_locals(module_source, class_qualname) & _template_bound_names(roots, query)
    prepared = _prepared_template_data_method(
        module_source,
        class_qualname,
        conflicts,
        source_module,
        source_is_package=source_is_package,
    )
    if prepared is None:
        return None
    # The prepared method is shared by every query, so each query edits its own copy.
    duplicate = copy.deepcopy(prepared)
    duplicate.name = "__citry_analyze_template"
    duplicate.returns = None
    import_source = ""
    if kwargs_type is not None:
        module, qualname = kwargs_type
        positional = (*duplicate.args.posonlyargs, *duplicate.args.args)
        if not _qualified_identifier(module) or not _qualified_identifier(qualname) or kwargs_index is None:
            return None
        if module == source_module:
            class_prefix = f"{class_qualname}."
            scoped_qualname = qualname.removeprefix(class_prefix)
            positional[kwargs_index].annotation = ast.parse(scoped_qualname, mode="eval").body
        else:
            alias = "__citry_schema_module"
            positional[kwargs_index].annotation = ast.parse(f"{alias}.{qualname}", mode="eval").body
            import_source = f"import {module} as {alias}\n"
    type_imports, type_references = _root_type_imports(roots, source_module=source_module)
    transformer = _ReturnQueryTransformer(
        roots,
        query,
        type_imports,
        type_references,
        placeholder,
        direct_attribute_owner=kwargs_type,
        value_check=value_check,
    )
    duplicate.body = transformer.transform_body(duplicate.body)
    if transformer.return_count == 0:
        return None
    rewritten_module = _rewritten_module(module_source, source_module, source_is_package=source_is_package)
    if rewritten_module is None:
        return None
    method_source = ast.unparse(duplicate)

    shadow_module_source, source_copies = rewritten_module
    source_insertion = _line_after(module_source, class_node.end_lineno)
    insertion = _shadow_offset_for_source(source_copies, source_insertion)
    if insertion is None:
        return None
    indent = _line_indent(module_source, methods[0].lineno)
    if not indent:
        return None
    method_lines = method_source.splitlines()
    indented_method = "\n".join(f"{indent}{line}" if line else "" for line in method_lines)
    indented_import = f"{indent}{import_source}" if import_source else ""
    inserted = f"\n{indented_import}{indented_method}\n"
    shadow = f"{shadow_module_source[:insertion]}{inserted}{shadow_module_source[insertion:]}"
    # The function starts at its `def` line, after any decorator lines that
    # ast.unparse writes one per line, and ends where the copied method ends.
    method_start = insertion + 1 + len(indented_import)
    decorator_count = len(duplicate.decorator_list)
    query_function = None
    if len(method_lines) > decorator_count and method_lines[decorator_count].startswith(
        "def __citry_analyze_template("
    ):
        def_start = method_start + sum(len(indent) + len(line) + 1 for line in method_lines[:decorator_count])
        query_function = (def_start, method_start + len(indented_method))
    return _replace_query_placeholders(
        shadow,
        query,
        placeholder=placeholder,
        source_copies=_source_copies_after_insertion(source_copies, insertion, len(inserted)),
        query_function=query_function,
    )


def build_schema_template_shadow(
    module_source: str,
    schema_qualname: str,
    roots: tuple[TemplatePythonRoot, ...],
    query: TemplatePythonQuery,
    *,
    source_module: str | None = None,
    source_is_package: bool = False,
    value_type: TemplatePythonValueType | None = None,
) -> ShadowPythonDocument | None:
    """
    Evaluate a query against fields on one exact authored schema class.

    With ``value_type``, such as a component input's type, the generated
    code also assigns the query's value to a variable annotated with that
    type, so ty checks the value against it.
    """
    if not _qualified_identifier(schema_qualname):
        return None
    rewritten_module = _rewritten_module(module_source, source_module, source_is_package=source_is_package)
    if rewritten_module is None:
        return None
    shadow_module_source, source_copies = rewritten_module
    placeholder = _query_placeholder(
        module_source,
        roots,
        query,
        generated_inputs=(source_module or "", schema_qualname, *_value_type_inputs(value_type)),
    )
    value_check = _value_check(value_type, module_source, roots, query, source_module=source_module)
    type_imports, type_references = _root_type_imports(roots, source_module=source_module)
    lines = [
        *type_imports,
        f"def __citry_analyze_template(__citry_data: {schema_qualname}) -> None:",
    ]
    lines.extend(
        _root_binding_lines(
            roots,
            data_name="__citry_data",
            indent="    ",
            type_references=type_references,
        )
    )
    lines.extend(_unknown_binding_lines(roots, query, indent="    "))
    lines.extend(_query_lines(query, indent="    ", placeholder=placeholder, value_check=value_check))
    generated = "\n".join(lines)
    shadow = f"{shadow_module_source}\n\n{generated}\n"
    # The generated function follows its import lines and ends the source.
    generated_start = len(shadow_module_source) + 2
    function_start = generated_start + sum(len(line) + 1 for line in type_imports)
    return _replace_query_placeholders(
        shadow,
        query,
        placeholder=placeholder,
        source_copies=source_copies,
        query_function=(function_start, generated_start + len(generated)),
    )


@dataclass(frozen=True, slots=True)
class ShadowRevealDocument:
    """
    A copy of a module that asks ty for the type of chosen expressions.

    Each chosen expression is wrapped in ``reveal_type(...)``, which returns
    its argument unchanged, so ty reports the expression's type as a
    ``revealed-type`` finding that starts at the expression.

    Attributes:
        source: Complete generated Python source.
        reveals: Start and end string offsets of each wrapped expression in
            ``source``, in the order the expressions were requested.

    """

    source: str
    reveals: tuple[tuple[int, int], ...]


def build_reveal_shadow(
    module_source: str,
    spans: tuple[tuple[int, int], ...],
    *,
    source_module: str | None = None,
    source_is_package: bool = False,
) -> ShadowRevealDocument | None:
    """
    Copy one module and wrap each expression span in ``reveal_type()``.

    ``spans`` are start and end string offsets in ``module_source``, each
    covering one whole expression; they must not overlap. Relative imports
    are made absolute, as in the template shadows, because ty reads the copy
    as a sibling file. Returns ``None`` when the module cannot be copied,
    already uses the name ``reveal_type``, or a span is not a whole
    expression of unchanged source.
    """
    if not spans or re.search(r"\breveal_type\b", module_source):
        # A module's own `reveal_type` would replace the analyzer's built-in one.
        return None
    ordered = sorted(spans)
    if any(start >= end for start, end in ordered) or any(
        earlier[1] > later[0] for earlier, later in itertools.pairwise(ordered)
    ):
        return None
    rewritten = _rewritten_module(module_source, source_module, source_is_package=source_is_package)
    if rewritten is None:
        return None
    shadow, copies = rewritten
    mapped: list[tuple[int, int]] = []
    for start, end in spans:
        shadow_start = _shadow_offset_for_source(copies, start)
        shadow_end = _shadow_offset_for_source(copies, end)
        # Both ends must come from one unchanged range, so the text between
        # them is exactly the authored expression.
        if shadow_start is None or shadow_end is None or shadow_end - shadow_start != end - start:
            return None
        if shadow[shadow_start:shadow_end] != module_source[start:end]:
            return None
        mapped.append((shadow_start, shadow_end))
    opening, closing = "reveal_type((", "))"
    # Splice from the last span backwards so earlier offsets stay valid, then
    # shift each span by the text inserted before it.
    for shadow_start, shadow_end in sorted(mapped, reverse=True):
        shadow = f"{shadow[:shadow_start]}{opening}{shadow[shadow_start:shadow_end]}{closing}{shadow[shadow_end:]}"
    reveals = []
    for shadow_start, shadow_end in mapped:
        inserted_before = sum(len(opening) + len(closing) for other_start, _ in mapped if other_start < shadow_start)
        start = shadow_start + inserted_before + len(opening)
        reveals.append((start, start + shadow_end - shadow_start))
    try:
        ast.parse(shadow)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        # A span that was not a whole expression breaks the copy.
        return None
    return ShadowRevealDocument(shadow, tuple(reveals))


class _ReturnQueryTransformer(ast.NodeTransformer):
    """Replace method returns while leaving nested definition scopes untouched."""

    def __init__(
        self,
        roots: tuple[TemplatePythonRoot, ...],
        query: TemplatePythonQuery,
        type_imports: list[str],
        type_references: dict[tuple[str, str], str],
        placeholder: str,
        *,
        direct_attribute_owner: tuple[str, str] | None,
        value_check: tuple[list[str], str] | None = None,
    ) -> None:
        self.roots = roots
        self.value_check = value_check
        self.query = query
        self.type_imports = type_imports
        self.type_references = type_references
        self.placeholder = placeholder
        self.direct_attribute_owner = direct_attribute_owner
        self.bound_names = _template_bound_names(roots, query)
        self.return_count = 0

    def transform_body(self, statements: list[ast.stmt]) -> list[ast.stmt]:
        transformed: list[ast.stmt] = []
        for statement in statements:
            value = self.visit(statement)
            if isinstance(value, list):
                transformed.extend(value)
            elif isinstance(value, ast.stmt):
                transformed.append(value)
        return transformed

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        return node

    def visit_Return(self, node: ast.Return) -> list[ast.stmt]:
        if node.value is None:
            return [node]
        self.return_count += 1
        assignment = ast.Assign(
            targets=[ast.Name(id="__citry_data", ctx=ast.Store())],
            value=node.value,
        )
        # ty remembers the type of each literal key read from the variable a
        # dict was assigned to, but not from a second name that variable is
        # copied into. Reading roots from the returned variable itself keeps
        # `data["size"]` as precise as the value the method stored there. A
        # variable that the generated code itself assigns, such as a root of
        # the same name that could not be renamed, is read through the copy.
        data_name = (
            node.value.id
            if isinstance(node.value, ast.Name) and node.value.id not in self.bound_names
            else "__citry_data"
        )
        generated = ast.parse(
            "\n".join(
                [
                    *self.type_imports,
                    *_root_binding_lines(
                        self.roots,
                        data_name=data_name,
                        indent="",
                        type_references=self.type_references,
                        direct_attribute_owner=self.direct_attribute_owner,
                        present_keys=_literal_dict_keys(node.value),
                    ),
                    *_unknown_binding_lines(self.roots, self.query, indent=""),
                    *_query_lines(
                        self.query,
                        indent="",
                        placeholder=self.placeholder,
                        value_check=self.value_check,
                    ),
                ]
            )
        ).body
        returned_name = ast.copy_location(ast.Name(id="__citry_data", ctx=ast.Load()), node)
        replacement_return = ast.copy_location(ast.Return(value=returned_name), node)
        # ast.unparse reads statement positions, so the new statements borrow
        # the position of the return they replace.
        ast.copy_location(assignment, node)
        return [assignment, *generated, replacement_return]


def _return_affected_by_finally(method: ast.FunctionDef) -> bool:
    """Return whether a finally suite can change an instrumented return."""

    class Finder(ast.NodeVisitor):
        found = False

        def visit(self, node: ast.AST) -> None:
            if isinstance(node, ast.Try) or type(node).__name__ == "TryStar":
                self._visit_try(node)
                return
            super().visit(node)

        def visit_FunctionDef(self, _node: ast.FunctionDef) -> None:
            return None

        def visit_AsyncFunctionDef(self, _node: ast.AsyncFunctionDef) -> None:
            return None

        def visit_ClassDef(self, _node: ast.ClassDef) -> None:
            return None

        def _visit_try(self, node: ast.AST) -> None:
            finalbody = getattr(node, "finalbody", ())
            if finalbody and _contains_return(node):
                self.found = True
                return
            for statement in getattr(node, "body", ()):  # ast.Try and newer ast.TryStar
                self.visit(statement)
            for handler in getattr(node, "handlers", ()):
                self.visit(handler)
            for statement in getattr(node, "orelse", ()):
                self.visit(statement)
            for statement in finalbody:
                self.visit(statement)

    finder = Finder()
    for statement in method.body:
        finder.visit(statement)
    return finder.found


def _contains_return(node: ast.AST) -> bool:
    """Find a return without crossing into a nested definition scope."""

    class Finder(ast.NodeVisitor):
        found = False

        def visit_FunctionDef(self, _node: ast.FunctionDef) -> None:
            return None

        def visit_AsyncFunctionDef(self, _node: ast.AsyncFunctionDef) -> None:
            return None

        def visit_ClassDef(self, _node: ast.ClassDef) -> None:
            return None

        def visit_Return(self, _node: ast.Return) -> None:
            self.found = True

    finder = Finder()
    for child in ast.iter_child_nodes(node):
        finder.visit(child)
    return finder.found


def _prune_unreachable_statements(node: ast.AST) -> None:
    """Remove statements after an unconditional suite terminator."""
    terminators = (ast.Return, ast.Raise, ast.Break, ast.Continue)
    for field, value in ast.iter_fields(node):
        if isinstance(value, list) and all(isinstance(item, ast.stmt) for item in value):
            retained: list[ast.stmt] = []
            for statement in value:
                _prune_unreachable_statements(statement)
                retained.append(statement)
                if isinstance(statement, terminators):
                    break
            setattr(node, field, retained)
        elif isinstance(value, ast.AST):
            _prune_unreachable_statements(value)


@lru_cache(maxsize=64)
def _prepared_template_data_method(
    module_source: str,
    class_qualname: str,
    conflicts: frozenset[str],
    source_module: str | None,
    *,
    source_is_package: bool,
) -> ast.FunctionDef | None:
    """
    Copy one ``template_data`` method and apply every change that does not depend on the query.

    Every expression of a template builds its shadow from the same method, so
    the unreachable-code pruning, the local renames, and the relative-import
    rewrite are done once per module text and set of renamed names. The
    returned tree is shared: callers copy it before changing it.
    """
    tree = _parsed_module(module_source)
    class_node = _class_for_qualname(tree, class_qualname) if tree is not None else None
    if class_node is None:
        return None
    methods = [
        statement
        for statement in class_node.body
        if isinstance(statement, ast.FunctionDef) and statement.name == "template_data"
    ]
    if len(methods) != 1:
        return None
    duplicate = copy.deepcopy(methods[0])
    if _return_affected_by_finally(duplicate):
        # A finally return can replace an earlier value after that earlier
        # return was evaluated. Querying both sites would create a false type
        # result, so this uncommon control-flow shape deliberately degrades.
        return None
    _prune_unreachable_statements(duplicate)
    _rename_conflicting_locals(
        duplicate,
        local_names=conflicts,
        template_names=conflicts,
        occupied=module_source,
    )
    # The generated statements added later hold no relative imports, so the
    # method's own imports can be made absolute before they are added.
    if not _rewrite_relative_imports(duplicate, source_module, source_is_package=source_is_package):
        return None
    return duplicate


@lru_cache(maxsize=32)
def _renamable_method_locals(module_source: str, class_qualname: str) -> frozenset[str]:
    """
    Return the names local to one class's ``template_data`` method that can be renamed safely.

    Python's own symbol table answers this, parameters included. A name
    the method declares ``global`` or only reads is not local. A local is
    left out when a function, class, or lambda nested in the method binds
    the same name itself or reads a global of that name, because renaming
    every occurrence would then change what that nested code means, such as
    a nested function called by keyword or a nested class's attribute. On
    Python 3.12 and later the table also lists a comprehension's loop
    variable as a method local, and the same rule covers it.
    """
    try:
        table = symtable.symtable(module_source, "<citry-template-data>", "exec")
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return frozenset()
    for part in class_qualname.split("."):
        found = _named_child_table(table, part, "class")
        if found is None:
            return frozenset()
        table = found
    method = _named_child_table(table, "template_data", "function")
    if not isinstance(method, symtable.Function):
        return frozenset()
    kept: set[str] = set()
    pending = list(method.get_children())
    while pending:
        nested = pending.pop()
        pending.extend(nested.get_children())
        kept.update(
            symbol.get_name()
            for symbol in nested.get_symbols()
            if symbol.is_local() or symbol.is_parameter() or symbol.is_global() or symbol.is_nonlocal()
        )
    return frozenset(method.get_locals()) - kept


def _named_child_table(table: symtable.SymbolTable, name: str, kind: str) -> symtable.SymbolTable | None:
    """Return the one child scope of this kind and name, looking through a generic's type-parameter scope."""
    matches: list[symtable.SymbolTable] = []
    for child in table.get_children():
        if child.get_name() != name:
            continue
        if child.get_type() == kind:
            matches.append(child)
        elif child.get_type() == "type parameters":
            # `class Board[T]:` (Python 3.12+) wraps the class in a scope
            # that holds the type parameters.
            matches.extend(inner for inner in child.get_children() if inner.get_type() == kind)
    return matches[0] if len(matches) == 1 else None


def _template_bound_names(roots: tuple[TemplatePythonRoot, ...], query: TemplatePythonQuery) -> frozenset[str]:
    """Return every name the generated template code binds or reads."""
    names = {root.name for root in roots}
    names.update(query.free_names)
    for control in query.controls:
        names.update(control.names)
        names.update(control.free_names)
    return frozenset(names)


def _rename_conflicting_locals(
    method: ast.FunctionDef,
    *,
    local_names: frozenset[str],
    template_names: frozenset[str],
    occupied: str,
) -> None:
    """
    Rename the method locals that a template name would otherwise reuse.

    The method is a private copy, and ``local_names`` holds only locals that
    no nested scope binds or reads as a global, so every occurrence of such
    a name in the method body, nested functions included, means the
    method's local and can be renamed together. The renamed copy computes
    the same values. The method's decorators, defaults, and annotations run
    in the class body, so they keep their names.
    """
    conflicts = local_names & template_names
    if not conflicts:
        return
    redirected = {
        name
        for statement in method.body
        for node in ast.walk(statement)
        if isinstance(node, (ast.Global, ast.Nonlocal))
        for name in node.names
        if name in conflicts
    }
    # `import a.b` binds `a` to the top package, and an alias would bind the
    # submodule, so a name bound that way cannot be renamed either.
    redirected.update(
        alias.name.split(".", 1)[0]
        for statement in method.body
        for node in ast.walk(statement)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.asname is None and "." in alias.name
    )
    renames: dict[str, str] = {}
    for name in sorted(conflicts - redirected):
        candidate = f"__citry_local_{name}"
        suffix = 0
        # A generated name that already appears in the module could refer to
        # something real, so it gets a number until it is unused.
        while candidate in occupied or candidate in renames.values():
            suffix += 1
            candidate = f"__citry_local_{name}_{suffix}"
        renames[name] = candidate
    if not renames:
        return

    arguments = method.args
    starred = tuple(item for item in (arguments.vararg, arguments.kwarg) if item is not None)
    for parameter in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs, *starred):
        parameter.arg = renames.get(parameter.arg, parameter.arg)
    for statement in method.body:
        for node in ast.walk(statement):
            if isinstance(node, ast.Name) and node.id in renames:
                node.id = renames[node.id]
            elif isinstance(node, ast.arg) and node.arg in renames:
                node.arg = renames[node.arg]
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                node.name = renames.get(node.name, node.name)
            elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name in renames:
                node.name = renames[node.name]
            elif isinstance(node, ast.MatchMapping) and node.rest in renames:
                node.rest = renames[node.rest]
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    bound = alias.asname or alias.name
                    if bound in renames:
                        alias.asname = renames[bound]


def _literal_dict_keys(value: ast.expr) -> frozenset[str]:
    """
    Return the string keys that a returned dict literal always sets itself.

    A `**other` spread may replace the keys written before it, so only the
    keys after the last spread count.
    """
    if not isinstance(value, ast.Dict):
        return frozenset()
    last_spread = max((index for index, key in enumerate(value.keys) if key is None), default=-1)
    return frozenset(
        key.value
        for key in value.keys[last_spread + 1 :]
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    )


_QUERY_PLACEHOLDER_BASE = "__citry_template_expression_query__"


def _root_binding_lines(
    roots: tuple[TemplatePythonRoot, ...],
    *,
    data_name: str,
    indent: str,
    type_references: dict[tuple[str, str], str] | None = None,
    direct_attribute_owner: tuple[str, str] | None = None,
    present_keys: frozenset[str] = frozenset(),
) -> list[str]:
    lines: list[str] = []
    for root in roots:
        if not root.name.isidentifier():
            continue
        owner_type = None
        if root.type_module is not None and root.type_qualname is not None and type_references is not None:
            owner_type = type_references.get((root.type_module, root.type_qualname))
        root_owner = (root.type_module, root.type_qualname)
        if root.access == "analysis":
            # Analysis-only globals do not come from the copied TemplateData
            # carrier. The caller has canonicalized this expression-shaped
            # annotation, so ty can read it without retaining the runtime value.
            value = f"__citry_cast({root.type_display}, None)" if root.type_display is not None else "__citry_Unknown"
        elif (
            root.access == "attribute" and direct_attribute_owner is not None and root_owner == direct_attribute_owner
        ):
            # In inferred shadows this is the effective, annotated Kwargs
            # object. Referencing it directly avoids a component class name
            # that an authored method local or parameter may shadow.
            value = f"{data_name}.{root.name}"
        elif owner_type is not None:
            value = f"__citry_cast({owner_type}, {data_name}).{root.name}"
        elif root.access == "attribute":
            value = f"{data_name}.{root.name}"
        elif root.access == "mixed":
            value = f'{data_name}["{root.name}"] if isinstance({data_name}, dict) else {data_name}.{root.name}'
        elif root.presence == "conditional" and root.name not in present_keys:
            # `dict.get()` answers with the union of every value in the dict,
            # so it is used only when this return may lack the key.
            value = f'{data_name}.get("{root.name}")'
        else:
            value = f'{data_name}["{root.name}"]'
        lines.append(f"{indent}{root.name} = {value}")
    return lines


def _root_type_imports(
    roots: tuple[TemplatePythonRoot, ...],
    *,
    source_module: str | None,
) -> tuple[list[str], dict[tuple[str, str], str]]:
    """Build stable imports for field owners without parsing annotation text."""
    owners = sorted(
        {
            (root.type_module, root.type_qualname)
            for root in roots
            if root.type_module is not None
            and root.type_qualname is not None
            and _qualified_identifier(root.type_module)
            and _qualified_identifier(root.type_qualname)
        }
    )
    imported = [owner for owner in owners if owner[0] != source_module]
    module_aliases = {owner: f"__citry_type_{imported.index(owner)}" for owner in imported}
    references = {
        owner: owner[1] if owner[0] == source_module else f"{module_aliases[owner]}.{owner[1]}" for owner in owners
    }
    needs_cast = bool(references) or any(root.access == "analysis" and root.type_display for root in roots)
    needs_unknown = any(root.access == "analysis" and root.type_display is None for root in roots)
    if not needs_cast and not needs_unknown:
        return [], {}
    imports: list[str] = []
    if needs_cast:
        imports.append("from typing import cast as __citry_cast")
    if needs_unknown:
        imports.append("from typing import Any as __citry_Unknown")
    imports.extend(f"import {module} as {module_aliases[(module, qualname)]}" for module, qualname in imported)
    imports.extend(
        f"import {module}"
        for module in sorted(
            {
                module
                for root in roots
                if root.type_display is not None
                for module in _annotation_modules(root.type_display)
                if module != source_module
            }
        )
    )
    return imports, references


def _annotation_modules(value: str) -> tuple[str, ...]:
    """Return importable module prefixes referenced by a safe type display."""
    try:
        expression = ast.parse(value, mode="eval")
    except (SyntaxError, UnicodeEncodeError, ValueError, MemoryError, RecursionError):
        return ()
    modules: set[str] = set()
    for node in ast.walk(expression):
        if not isinstance(node, ast.Attribute):
            continue
        parts = [node.attr]
        owner = node.value
        while isinstance(owner, ast.Attribute):
            parts.append(owner.attr)
            owner = owner.value
        if not isinstance(owner, ast.Name):
            continue
        parts.append(owner.id)
        parts.reverse()
        module = ".".join(parts[:-1])
        if _qualified_identifier(module):
            modules.add(module)
    return tuple(sorted(modules))


def _canonical_type_display(value: object) -> str | None:
    """Accept only one passive annotation expression for generated source."""
    if type(value) is not str or not value:
        return None
    try:
        value.encode("utf-8")
        expression = ast.parse(value, mode="eval")
    except (SyntaxError, UnicodeEncodeError, ValueError, MemoryError, RecursionError):
        return None
    forbidden = (
        ast.Await,
        ast.Call,
        ast.DictComp,
        ast.GeneratorExp,
        ast.IfExp,
        ast.Lambda,
        ast.ListComp,
        ast.NamedExpr,
        ast.SetComp,
        ast.Yield,
        ast.YieldFrom,
    )
    if any(isinstance(node, forbidden) for node in ast.walk(expression)):
        return None
    return ast.unparse(expression.body)


def _unknown_binding_lines(
    roots: tuple[TemplatePythonRoot, ...],
    query: TemplatePythonQuery,
    *,
    indent: str,
) -> list[str]:
    """Mask unproven names so Python builtins never become template globals."""
    loaded = set(query.free_names)
    loaded.update(name for control in query.controls for name in control.free_names)
    proven = {root.name for root in roots}
    proven.update(name for control in query.controls for name in control.names)
    unknown = sorted(loaded - proven)
    if not unknown:
        return []
    return [
        f"{indent}from typing import Any as __citry_Unknown",
        *(f"{indent}{name}: __citry_Unknown = None" for name in unknown if name.isidentifier()),
    ]


def _query_lines(
    query: TemplatePythonQuery,
    *,
    indent: str,
    placeholder: str,
    value_check: tuple[list[str], str] | None = None,
) -> list[str]:
    lines: list[str] = []
    current = indent
    for control in query.controls:
        if control.kind == "if":
            # Put generated punctuation after a newline so an authored Python
            # comment cannot consume the closing parenthesis and colon.
            lines.append(f"{current}if (")
            lines.extend(f"{current}    {line}" for line in control.source.splitlines())
            lines.append(f"{current}):")
            current += "    "
        elif control.kind == "for":
            if not control.names:
                return []
            target = control.names[0] if len(control.names) == 1 else f"({', '.join(control.names)})"
            yielded = control.names[0] if len(control.names) == 1 else f"({', '.join(control.names)})"
            source_lines = control.source.splitlines()
            if not source_lines:
                return []
            lines.append(f"{current}for {target} in [")
            lines.append(f"{current}    {yielded}")
            lines.append(f"{current}    for {source_lines[0]}")
            lines.extend(f"{current}    {line}" for line in source_lines[1:])
            lines.append(f"{current}]:")
            current += "    "
        else:
            for name in control.names:
                lines.append(f"{current}from typing import Any as __citry_Any")
                lines.append(f"{current}{name}: __citry_Any = None")
    if value_check is None:
        lines.append(f"{current}{placeholder}")
        return lines
    # Assigning the value to an annotated name makes ty report a mismatch
    # over the parenthesized value, which maps back to the authored text.
    imports, annotation = value_check
    lines.extend(f"{current}{line}" for line in imports)
    lines.append(f"{current}{_VALUE_CHECK_PREFIX}_value: {annotation} = {placeholder}")
    return lines


# Generated names for a value check. They must not contain the query
# placeholder, which is replaced by text everywhere it appears.
_VALUE_CHECK_PREFIX = "__citry_checked"


def _value_check(
    value_type: TemplatePythonValueType | None,
    module_source: str,
    roots: tuple[TemplatePythonRoot, ...],
    query: TemplatePythonQuery,
    *,
    source_module: str | None,
) -> tuple[list[str], str] | None:
    """Return the imports and annotation for a value check, or ``None`` to check nothing."""
    if value_type is None:
        return None
    occupied = (
        module_source,
        query.source,
        *(control.source for control in query.controls),
        *(root.name for root in roots),
        value_type.annotation,
        value_type.module or "",
    )
    # A user name containing this prefix could clash with the generated
    # names, so skip the check. A user name that hides a name the annotation
    # uses, such as a local `list`, only makes the check miss a mistake.
    if any(_VALUE_CHECK_PREFIX in value for value in occupied):
        return None
    return _value_check_source(value_type, alias_prefix=f"{_VALUE_CHECK_PREFIX}_type", source_module=source_module)


# Names Citry's schema type display takes from `typing` or `collections.abc`.
_TYPING_DISPLAY_NAMES = frozenset({"Any", "Callable", "Literal", "Mapping", "Optional", "Sequence", "Union"})


def _value_check_source(
    value_type: TemplatePythonValueType,
    *,
    alias_prefix: str,
    source_module: str | None,
) -> tuple[list[str], str] | None:
    """
    Rewrite a type display into an annotation that resolves inside generated code.

    A dotted name such as ``app.store.Task`` imports its module under a private
    alias, and a bare name such as ``Task`` is read from ``value_type.module``,
    where the annotation was written. Names such as ``Literal`` and
    ``Sequence`` come from ``typing``, and builtins stay as they are. A name from
    ``source_module`` stays bare: the generated code is a copy of that module,
    and importing the real module would name a different class.
    """
    display = _canonical_type_display(value_type.annotation)
    if display is None:
        return None
    expression = ast.parse(display, mode="eval")
    aliases: dict[str, str] = {}
    unresolved = False

    def alias(module: str) -> str:
        return aliases.setdefault(module, f"{alias_prefix}_{len(aliases)}")

    class Qualifier(ast.NodeTransformer):
        def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
            parts: list[str] = [node.attr]
            owner: ast.expr = node.value
            while isinstance(owner, ast.Attribute):
                parts.append(owner.attr)
                owner = owner.value
            if not isinstance(owner, ast.Name):
                return self.generic_visit(node)
            parts.append(owner.id)
            parts.reverse()
            module = ".".join(parts[:-1])
            if module == source_module:
                return ast.Name(parts[-1], ast.Load())
            return ast.Attribute(ast.Name(alias(module), ast.Load()), parts[-1], ast.Load())

        def visit_Name(self, node: ast.Name) -> ast.AST:
            nonlocal unresolved
            if node.id in _BUILTIN_NAMES:
                return node
            if node.id in _TYPING_DISPLAY_NAMES:
                return ast.Attribute(ast.Name(alias("typing"), ast.Load()), node.id, ast.Load())
            if value_type.module is None or not _qualified_identifier(value_type.module):
                unresolved = True
                return node
            if value_type.module == source_module:
                return node
            return ast.Attribute(ast.Name(alias(value_type.module), ast.Load()), node.id, ast.Load())

    rewritten = Qualifier().visit(expression)
    if unresolved or not all(_qualified_identifier(module) for module in aliases):
        return None
    imports = [f"import {module} as {name}" for module, name in aliases.items()]
    return imports, ast.unparse(rewritten)


def _value_type_inputs(value_type: TemplatePythonValueType | None) -> tuple[str, ...]:
    """Return the value type's text, so the generated names avoid it too."""
    if value_type is None:
        return ()
    return (value_type.annotation, value_type.module or "")


def _query_placeholder(
    module_source: str,
    roots: tuple[TemplatePythonRoot, ...],
    query: TemplatePythonQuery,
    *,
    generated_inputs: tuple[str, ...],
) -> str:
    """Choose a generated name that cannot collide with copied user input."""
    occupied = [
        module_source,
        query.source,
        *(control.source for control in query.controls),
        *(control_name for control in query.controls for control_name in control.names),
        *(root.name for root in roots),
        *(root.type_module or "" for root in roots),
        *(root.type_qualname or "" for root in roots),
        *generated_inputs,
    ]
    candidate = _QUERY_PLACEHOLDER_BASE
    suffix = 0
    while any(candidate in value for value in occupied):
        suffix += 1
        candidate = f"{_QUERY_PLACEHOLDER_BASE}_{suffix}"
    return candidate


def _replace_query_placeholders(
    source: str,
    query: TemplatePythonQuery,
    *,
    placeholder: str,
    source_copies: tuple[ShadowPythonSourceCopy, ...],
    query_function: tuple[int, int] | None = None,
) -> ShadowPythonDocument | None:
    if placeholder not in source:
        return None
    replacement = f"[\nNone for {query.source}\n]" if query.host_kind == "loop" else f"(\n{query.source}\n)"
    retained: list[str] = []
    copies: list[ShadowPythonCopy] = []
    cursor = 0
    output_length = 0
    matches = tuple(re.finditer(re.escape(placeholder), source))
    for match in matches:
        prefix = source[cursor : match.start()]
        retained.extend((prefix, replacement))
        output_length += len(prefix)
        expression_prefix = "[\nNone for " if query.host_kind == "loop" else "(\n"
        expression_start = output_length + len(expression_prefix)
        expression_end = expression_start + len(query.source)
        copies.append(
            ShadowPythonCopy(
                expression_start,
                expression_end,
                query.start_index,
                query.end_index,
            )
        )
        output_length += len(replacement)
        cursor = match.end()
    retained.append(source[cursor:])
    adjusted_source_copies = tuple(
        ShadowPythonSourceCopy(
            _offset_after_replacements(item.shadow_start, matches, len(replacement), len(placeholder)),
            _offset_after_replacements(item.shadow_end, matches, len(replacement), len(placeholder)),
            item.source_start,
            item.source_end,
        )
        for item in source_copies
    )
    # Every placeholder sits inside the generated function, so its start stays
    # put and its end moves by the length each replacement adds.
    adjusted_function = (
        (
            _offset_after_replacements(query_function[0], matches, len(replacement), len(placeholder)),
            _offset_after_replacements(query_function[1], matches, len(replacement), len(placeholder)),
        )
        if query_function is not None
        else None
    )
    return ShadowPythonDocument("".join(retained), tuple(copies), adjusted_source_copies, adjusted_function)


def _offset_after_replacements(
    offset: int,
    matches: tuple[re.Match[str], ...],
    replacement_length: int,
    placeholder_length: int,
) -> int:
    delta = replacement_length - placeholder_length
    return offset + sum(delta for match in matches if match.end() <= offset)


def _class_for_qualname(module: ast.Module, qualname: str) -> ast.ClassDef | None:
    parts = qualname.split(".")
    if not parts or "<locals>" in parts:
        return None
    body: list[ast.stmt] = module.body
    matched: ast.ClassDef | None = None
    for part in parts:
        candidates = [
            statement for statement in body if isinstance(statement, ast.ClassDef) and statement.name == part
        ]
        if len(candidates) != 1:
            return None
        matched = candidates[0]
        body = matched.body
    return matched


# Every expression in a template builds its own shadow from the same owner
# module, so the parsed tree and its import rewrite are computed once per
# module text and reused. A few entries cover the files one check visits in turn.
@lru_cache(maxsize=8)
def _parsed_module(source: str) -> ast.Module | None:
    """Parse one module; callers must copy any part they change, because the tree is shared."""
    try:
        return ast.parse(source)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return None


@lru_cache(maxsize=8)
def _rewritten_module(
    source: str,
    source_module: str | None,
    *,
    source_is_package: bool,
) -> tuple[str, tuple[ShadowPythonSourceCopy, ...]] | None:
    """Return the module with relative imports made absolute, computed once per module text."""
    tree = _parsed_module(source)
    if tree is None:
        return None
    return _rewrite_module_relative_imports(source, tree, source_module, source_is_package=source_is_package)


def _rewrite_module_relative_imports(
    source: str,
    module: ast.Module,
    source_module: str | None,
    *,
    source_is_package: bool,
) -> tuple[str, tuple[ShadowPythonSourceCopy, ...]] | None:
    """Rewrite copied relative imports while retaining every unchanged range."""
    # The complete authored module is copied into a virtual sibling that ty
    # cannot associate with its package. Helpers and base classes can supply
    # inferred values too, so imports in every copied scope need the same
    # absolute spelling as imports on the selected component itself.
    relative = sorted(
        (node for node in ast.walk(module) if isinstance(node, ast.ImportFrom) and node.level > 0),
        key=lambda node: (node.lineno, node.col_offset),
    )
    if not relative:
        return source, (ShadowPythonSourceCopy(0, len(source), 0, len(source)),)
    if source_module is None or not _qualified_identifier(source_module):
        return None
    replacements: list[tuple[int, int, str]] = []
    for statement in relative:
        rewritten = _absolute_relative_import(
            statement,
            source_module,
            source_is_package=source_is_package,
            allow_star=True,
        )
        if rewritten is None or statement.end_lineno is None or statement.end_col_offset is None:
            return None
        start = _ast_source_offset(source, statement.lineno, statement.col_offset)
        end = _ast_source_offset(source, statement.end_lineno, statement.end_col_offset)
        if start is None or end is None or end < start:
            return None
        replacements.append((start, end, ast.unparse(rewritten)))

    output: list[str] = []
    copies: list[ShadowPythonSourceCopy] = []
    source_cursor = 0
    shadow_cursor = 0
    for start, end, replacement in replacements:
        unchanged = source[source_cursor:start]
        output.append(unchanged)
        if unchanged:
            copies.append(
                ShadowPythonSourceCopy(
                    shadow_cursor,
                    shadow_cursor + len(unchanged),
                    source_cursor,
                    start,
                )
            )
        output.append(replacement)
        shadow_cursor += len(unchanged) + len(replacement)
        source_cursor = end
    unchanged = source[source_cursor:]
    output.append(unchanged)
    if unchanged:
        copies.append(
            ShadowPythonSourceCopy(
                shadow_cursor,
                shadow_cursor + len(unchanged),
                source_cursor,
                len(source),
            )
        )
    return "".join(output), tuple(copies)


def _shadow_offset_for_source(
    copies: tuple[ShadowPythonSourceCopy, ...],
    source_offset: int,
) -> int | None:
    """Map one unchanged source boundary into the rewritten module."""
    for item in copies:
        if item.source_start <= source_offset <= item.source_end:
            return item.shadow_start + source_offset - item.source_start
    return None


def _source_copies_after_insertion(
    copies: tuple[ShadowPythonSourceCopy, ...],
    insertion: int,
    inserted_length: int,
) -> tuple[ShadowPythonSourceCopy, ...]:
    """Keep source maps on both sides of an inserted analyzer method."""
    adjusted: list[ShadowPythonSourceCopy] = []
    for item in copies:
        if item.shadow_end <= insertion:
            adjusted.append(item)
            continue
        if item.shadow_start >= insertion:
            adjusted.append(
                ShadowPythonSourceCopy(
                    item.shadow_start + inserted_length,
                    item.shadow_end + inserted_length,
                    item.source_start,
                    item.source_end,
                )
            )
            continue

        source_split = item.source_start + insertion - item.shadow_start
        adjusted.extend(
            (
                ShadowPythonSourceCopy(
                    item.shadow_start,
                    insertion,
                    item.source_start,
                    source_split,
                ),
                ShadowPythonSourceCopy(
                    insertion + inserted_length,
                    item.shadow_end + inserted_length,
                    source_split,
                    item.source_end,
                ),
            )
        )
    return tuple(adjusted)


def _rewrite_relative_imports(
    node: ast.AST,
    source_module: str | None,
    *,
    source_is_package: bool,
) -> bool:
    """Rewrite local relative imports and reject function-invalid stars."""
    if source_module is None or not _qualified_identifier(source_module):
        return not any(isinstance(candidate, ast.ImportFrom) and candidate.level > 0 for candidate in ast.walk(node))
    module_name = source_module
    valid = True

    class Rewriter(ast.NodeTransformer):
        def visit_ImportFrom(self, item: ast.ImportFrom) -> ast.ImportFrom:
            nonlocal valid
            if item.level == 0:
                return item
            replacement = _absolute_relative_import(
                item,
                module_name,
                source_is_package=source_is_package,
            )
            if replacement is None:
                valid = False
                return item
            return ast.copy_location(replacement, item)

    Rewriter().visit(node)
    return valid


def _absolute_relative_import(
    node: ast.ImportFrom,
    source_module: str,
    *,
    source_is_package: bool,
    allow_star: bool = False,
) -> ast.ImportFrom | None:
    """Convert one relative import using the copied module's proven name."""
    if not allow_star and any(alias.name == "*" for alias in node.names):
        return None
    module_parts = source_module.split(".")
    parent_count = len(module_parts) - node.level + int(source_is_package)
    if parent_count < 0:
        return None
    absolute_parts = module_parts[:parent_count]
    if node.module is not None:
        absolute_parts.extend(node.module.split("."))
    if not absolute_parts:
        return None
    return ast.ImportFrom(
        module=".".join(absolute_parts),
        names=copy.deepcopy(node.names),
        level=0,
    )


def _ast_source_offset(source: str, lineno: int, byte_column: int) -> int | None:
    """Convert CPython's UTF-8 AST column to a Python string offset."""
    lines = source.splitlines(keepends=True)
    if lineno < 1 or lineno > len(lines) or byte_column < 0:
        return None
    line = lines[lineno - 1]
    encoded = line.encode()
    if byte_column > len(encoded):
        return None
    try:
        column = len(encoded[:byte_column].decode())
    except UnicodeDecodeError:
        return None
    return sum(len(item) for item in lines[: lineno - 1]) + column


def _qualified_identifier(value: str) -> bool:
    return bool(value) and all(part.isidentifier() for part in value.split("."))


def _line_after(source: str, lineno: int | None) -> int:
    if lineno is None:
        return len(source)
    starts = [0]
    starts.extend(match.end() for match in re.finditer("\n", source))
    return starts[lineno] if lineno < len(starts) else len(source)


def _line_indent(source: str, lineno: int) -> str:
    """Return the exact whitespace prefix of one one-based source line."""
    lines = source.splitlines()
    if lineno < 1 or lineno > len(lines):
        return ""
    match = re.match(r"[ \t\f]*", lines[lineno - 1])
    return match.group() if match is not None else ""


def _query_in_template(
    template: Any,
    index: int,
    controls: tuple[TemplatePythonControl, ...],
    *,
    base_index: int,
    parse_nested: Callable[[str], Any],
) -> TemplatePythonQuery | None:
    branch_conditions: list[tuple[str, tuple[str, ...]]] = []
    for element in template.elements:
        value: Any = element._0
        if isinstance(element, TemplateElement.Expr):
            start = base_index + value.value.start_index
            end = base_index + value.value.end_index
            if start <= index <= end:
                return TemplatePythonQuery(
                    value.value.content,
                    start,
                    end,
                    "interpolation",
                    controls,
                    _used_names(value),
                )
            branch_conditions.clear()
            continue
        if isinstance(element, TemplateElement.Text):
            if value.token.content.strip():
                branch_conditions.clear()
            continue
        if not isinstance(element, TemplateElement.Node):
            continue
        branch_kind = _condition_branch_kind(value)
        if branch_kind not in {"elif", "else"}:
            branch_conditions.clear()
        prior_branch_controls = tuple(
            TemplatePythonControl("if", f"not (\n{source}\n)", free_names=free_names)
            for source, free_names in branch_conditions
        )
        query = _query_in_node(
            value,
            index,
            (*controls, *prior_branch_controls),
            base_index=base_index,
            parse_nested=parse_nested,
        )
        if query is not None:
            return query
        condition = _condition_control(value)
        if branch_kind in {"if", "elif"}:
            branch_conditions.append(
                (condition.source, condition.free_names) if condition is not None else ("True", ())
            )
        elif branch_kind == "else":
            branch_conditions.clear()
    return None


def _query_start_indexes(
    template: Any,
    *,
    base_index: int,
    parse_nested: Callable[[str], Any],
) -> set[int]:
    indexes: set[int] = set()
    for element in template.elements:
        value: Any = element._0
        if isinstance(element, TemplateElement.Expr):
            indexes.add(base_index + value.value.start_index)
            continue
        if not isinstance(element, TemplateElement.Node):
            continue
        for attr in value.start_tag.attrs:
            inner = attr.inner_value
            if inner is None:
                continue
            start = base_index + inner.start_index
            if attr.kind == HtmlAttrKind.Template:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    nested_template, nested_start = nested
                    indexes.update(
                        _query_start_indexes(
                            nested_template,
                            base_index=start + nested_start,
                            parse_nested=parse_nested,
                        )
                    )
            elif attr.kind == HtmlAttrKind.Expression or attr.kind == HtmlAttrKind.Meta:  # noqa: PLR1714
                indexes.add(start)
        body = getattr(value, "body", None)
        if body is not None:
            indexes.update(_query_start_indexes(body, base_index=base_index, parse_nested=parse_nested))
    return indexes


def _query_in_node(
    node: Any,
    index: int,
    controls: tuple[TemplatePythonControl, ...],
    *,
    base_index: int,
    parse_nested: Callable[[str], Any],
) -> TemplatePythonQuery | None:
    condition = _condition_control(node)
    loop = _loop_control(node)
    body_controls = (
        *controls,
        *((condition,) if condition is not None else ()),
        *((loop,) if loop is not None else ()),
    )
    unknown_controls = _unknown_binding_controls(node, loop)
    body_controls = (*body_controls, *unknown_controls)

    for attr in node.start_tag.attrs:
        inner = attr.inner_value
        if inner is None:
            continue
        start = base_index + inner.start_index
        end = base_index + inner.end_index
        if not (start <= index <= end):
            continue
        name = attr.key.content
        if attr.kind == HtmlAttrKind.Template:
            nested = _nested_template(inner.content, parse_nested)
            if nested is None:
                return None
            nested_template, nested_start = nested
            nested_controls = body_controls if _attribute_sees_loop(name) else controls
            return _query_in_template(
                nested_template,
                index,
                nested_controls,
                base_index=start + nested_start,
                parse_nested=parse_nested,
            )
        if not (attr.kind == HtmlAttrKind.Expression or attr.kind == HtmlAttrKind.Meta):  # noqa: PLR1714
            return None
        attr_controls = controls
        host_kind: Literal["attribute", "loop"] = "attribute"
        if _is_loop_attribute(node, name):
            # A combined condition runs before its loop, so it can narrow the
            # iterable while the loop target itself is still unavailable.
            if condition is not None:
                attr_controls = (*attr_controls, condition)
            host_kind = "loop"
        elif not _is_condition_attribute(node, name):
            attr_controls = body_controls
        # A `c-*` value that sets an attribute or a component input can be
        # checked against that target's type; control attributes cannot.
        target = (
            (node.start_tag.name.content, name.removeprefix("c-"))
            if attr.kind == HtmlAttrKind.Expression
            and host_kind == "attribute"
            and name.startswith("c-")
            and _attribute_sees_loop(name)
            else None
        )
        return TemplatePythonQuery(
            inner.content,
            start,
            end,
            host_kind,
            attr_controls,
            _used_names(attr),
            target,
        )

    body = getattr(node, "body", None)
    if body is not None and _node_body_contains(node, index, base_index=base_index):
        return _query_in_template(body, index, body_controls, base_index=base_index, parse_nested=parse_nested)
    return None


def _condition_control(node: Any) -> TemplatePythonControl | None:
    tag_name = node.start_tag.name.content
    names = {"cond"} if tag_name in {"c-if", "c-elif"} else {"c-if", "c-elif"}
    for attr in node.start_tag.attrs:
        if attr.key.content in names and attr.inner_value is not None and attr.kind == HtmlAttrKind.Expression:
            return TemplatePythonControl("if", attr.inner_value.content, free_names=_used_names(attr))
    return None


def _condition_branch_kind(node: Any) -> Literal["if", "elif", "else"] | None:
    tag_name = node.start_tag.name.content
    branch_names: tuple[tuple[str, Literal["if", "elif", "else"]], ...] = (
        ("c-if", "if"),
        ("c-elif", "elif"),
        ("c-else", "else"),
    )
    for authored, branch in branch_names:
        if tag_name == authored:
            return branch
    names = {attr.key.content for attr in node.start_tag.attrs}
    for authored, branch in branch_names:
        if authored in names:
            return branch
    return None


def _loop_control(node: Any) -> TemplatePythonControl | None:
    tag_name = node.start_tag.name.content
    name = "each" if tag_name == "c-for" else "c-for"
    for attr in node.start_tag.attrs:
        if attr.key.content == name and attr.inner_value is not None:
            introduced = tuple(token.content for token in node.introduced_variables)
            return TemplatePythonControl("for", attr.inner_value.content, introduced, _used_names(attr))
    return None


def _unknown_binding_controls(node: Any, loop: TemplatePythonControl | None) -> tuple[TemplatePythonControl, ...]:
    loop_names = frozenset(loop.names if loop is not None else ())
    return tuple(
        TemplatePythonControl("unknown", "", (token.content,))
        for token in node.introduced_variables
        if token.content not in loop_names
    )


def _used_names(value: Any) -> tuple[str, ...]:
    """Copy parser-owned free-name order without retaining AST objects."""
    return tuple(dict.fromkeys(token.content for token in value.used_variables))


def _is_condition_attribute(node: Any, name: str) -> bool:
    tag_name = node.start_tag.name.content
    return (tag_name in {"c-if", "c-elif"} and name == "cond") or name in {"c-if", "c-elif"}


def _is_loop_attribute(node: Any, name: str) -> bool:
    return (node.start_tag.name.content == "c-for" and name == "each") or name == "c-for"


def _attribute_sees_loop(name: str) -> bool:
    return name not in {"c-if", "c-elif", "c-else", "c-for", "c-empty"}


def _node_body_contains(node: Any, index: int, *, base_index: int) -> bool:
    body = getattr(node, "body", None)
    end_tag = getattr(node, "end_tag", None)
    if body is None or end_tag is None:
        return False
    return base_index + node.start_tag.token.end_index <= index <= base_index + end_tag.token.start_index


def _nested_template(source: str, parse_nested: Callable[[str], Any]) -> tuple[Any, int] | None:
    stripped = source.lstrip()
    leading = len(source) - len(stripped)
    if stripped.startswith("<>") and stripped.rstrip().endswith("</>"):
        trailing = len(stripped.rstrip()) - len("</>")
        content_start = leading + len("<>")
        content_end = leading + trailing
    else:
        content_start = leading
        content_end = len(source.rstrip())
    if content_end < content_start:
        return None
    try:
        nested_start = len(source[:content_start].encode())
        return parse_nested(source[content_start:content_end]), nested_start
    except (SyntaxError, ValueError):
        return None


__all__ = [
    "ShadowPythonCopy",
    "ShadowPythonDocument",
    "ShadowPythonSourceCopy",
    "ShadowRevealDocument",
    "TemplatePythonControl",
    "TemplatePythonQuery",
    "TemplatePythonRoot",
    "build_inferred_template_shadow",
    "build_reveal_shadow",
    "build_schema_template_shadow",
    "template_python_queries",
    "template_python_query_at",
    "template_static_input_queries",
]
