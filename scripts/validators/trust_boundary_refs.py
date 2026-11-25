"""
Check that every code and docs reference in the trust-boundary design doc still points at something.

`docs/design/trust_boundaries.md` says, for each input that reaches the page,
which function checks it and which docs section states the rule. It cites
code as `path:Symbol` (`citry/attrs.py:validate_html_attr_name`) and a
Markdown section as `path#anchor` (`docs/security.md#authorize-every-event`),
so a reference keeps working while lines move and breaks only when the thing
it names is renamed, moved, or deleted. This check finds those breaks. For
every code span that is a file path (with a `/` in it, or a file at the
repository root), alone or followed by `:Symbol` or `#anchor`, it checks
that:

- the file exists;
- the symbol is defined in that file. Python is read with `ast`, so a
  name must sit where the symbol says: its first name at the top of the
  file, and each later name in the body of the one before it. JavaScript,
  TypeScript, Rust, and Pest are read with a few patterns that match a
  definition at the start of a line, and each part of the symbol
  (`a.b.c`, or `Type::method`) only has to be defined somewhere in the file;
- the anchor names a heading in the Markdown file: the heading's own
  `{ #id }` when it sets one, otherwise GitHub's slug of its text.

It also fails on a line number written in a reference or right after one,
so references cannot drift again.

The short path forms (`citry/` for `packages/py/citry/citry/` and the
others) are read from the list in the doc itself, so the doc and this check
always agree on them. The check proves that each name still exists, not
that the row still describes it; the Mechanism 7 security pass checks that.
"""

import ast
import bisect
import re
import unicodedata
from collections.abc import Callable, Iterator
from functools import cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DOC = Path("docs/design/trust_boundaries.md")

# A CommonMark code span: a run of backticks, then text, then a run of the
# same length. It may wrap onto the next line of a paragraph, but not into a
# blank line, a new table row, or a new list item.
_CODE_SPAN = re.compile(
    r"(?<!`)(`+)(?!`)((?:(?!\n[ \t]*(?:\n|\||(?:[-*+]|\d+[.)])[ \t])).)+?)(?<!`)\1(?!`)", re.DOTALL
)
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")

# The doc's list of short forms, one item per line: - `citry/` is `packages/py/citry/citry/`
_SHORT_FORM = re.compile(r"^- `([\w.-]+/)` is `([\w./-]+/)`$", re.MULTILINE)

# A reference: a file path, then `:Symbol` or `#anchor`, or nothing for a
# path written alone.
_REFERENCE = re.compile(r"^(?P<path>[\w.-]+(?:/[\w.-]+)*\.(?P<ext>[A-Za-z]+))(?:(?P<sep>[:#])(?P<target>.*))?$")

# Line numbers inside a code span: `attrs.py:140`, `:140-153` (the file
# named earlier), `attrs.py:L140`, `attrs.py#L140`, `attrs.py, line 140`.
_FILE_EXTENSIONS = r"(?:py|pyi|js|mjs|cjs|ts|tsx|rs|pest|md|ya?ml|toml|json|css|html)"
_LINE_NUMBER_SPAN = re.compile(
    rf"^(?:[\w./-]*\.{_FILE_EXTENSIONS})?(?::L?\d+(?:\s*-\s*L?\d+)?|#L\d+(?:-L?\d+)?)$"
    rf"|^[\w./-]+\.{_FILE_EXTENSIONS},?\s+\(?(?:(?:at|on)\s+)?lines?\s+\d"
)
# Line numbers outside a code span: attrs.py:140, or a GitHub #L140 link.
_LINE_NUMBER_TEXT = re.compile(rf"[\w./-]*[\w-]\.{_FILE_EXTENSIONS}(?::\d+|#L\d+)\b")
# A path or reference in a code span followed by :140, "line 140", "at line
# 140", or "(lines 140-153)".
_LINE_NUMBER_AFTER_SPAN = re.compile(
    r"(?<!`)(`+)[^`\n]*\.[A-Za-z]+(?:[:#][^`\n]*)?\1(?!`)\s*(?::\d+|,?\s*\(?(?:(?:at|on)\s+)?lines?\s+\d+)"
)

# The check reads `path:Symbol` and `path#anchor`, so a docs heading in
# quotes (or in backticks, in parentheses) after a Markdown path, or a
# function or class name beside a code file's path written alone, would pass
# whatever the name says. The common wordings of these two shapes are
# rejected; other wordings are left to review.
_QUOTED_HEADING = re.compile(
    r"`[\w./-]+\.md`(?:\s+\(|,\s)\s*[\"\u201c][^\"\u201d\n]*[\"\u201d]|`[\w./-]+\.md`\s+\(`[^`\n]+`\)"
)
_CODE_PATH_ALONE = r"`[\w./-]+/[\w.-]+\.(?:py|js|mjs|ts|rs|pest)`"
# A name, not another file: `Class.method` and `name()` count, `vue.js` does not.
_BARE_NAME = r"`(?![\w.]*\.(?:py|js|mjs|ts|rs|pest|md|ya?ml|json|toml|css|html)`)[A-Za-z_][\w.]*(?:\(\))?`"
_NAME_BESIDE_PATH = re.compile(
    rf"{_BARE_NAME}(?:\s+in\s+|\s+\(|,\s*){_CODE_PATH_ALONE}|{_CODE_PATH_ALONE}(?:,\s*|\s+\(){_BARE_NAME}"
)

# One name in a symbol; JavaScript allows `$` in names.
_NAME = r"[A-Za-z_$][\w$]*"
_DOTTED_SYMBOL = re.compile(rf"^{_NAME}(?:\.{_NAME})*$")
_RUST_SYMBOL = re.compile(r"^[A-Za-z_]\w*(?:::[A-Za-z_]\w*)?$")
_PEST_SYMBOL = re.compile(r"^[A-Za-z_]\w*$")

_FIX = "find where it moved, or fix the spelling, and update the row"


def check(root: Path = REPO_ROOT) -> list[str]:
    doc_path = root / DOC
    if not doc_path.exists():
        return [f"{DOC} not found"]
    text = doc_path.read_text(encoding="utf-8")

    short_forms = dict(_SHORT_FORM.findall(text))
    if not short_forms:
        # Without the list every short path would read as missing, so say
        # what is wrong once instead of reporting each reference.
        return [f'{DOC}: found no short path forms (lines such as "- `citry/` is `packages/py/citry/citry/`")']

    # Backticks in a fenced block are code, not span delimiters, so blank
    # the block before pairing them; offsets stay the same.
    prose = _blank_fenced_blocks(text)
    line_starts = [0, *(match.end() for match in re.finditer(r"\n", prose))]

    def where(offset: int) -> str:
        return f"{DOC}:{bisect.bisect_right(line_starts, offset)}"

    problems: list[str] = []
    files = _SourceFiles(root)
    spans = list(_CODE_SPAN.finditer(prose))
    outside = list(prose)
    for span in spans:
        outside[span.start(2) : span.end(2)] = re.sub(r"[^\n]", " ", span.group(2))
    line_numbers = [*_LINE_NUMBER_TEXT.finditer("".join(outside)), *_LINE_NUMBER_AFTER_SPAN.finditer(prose)]
    problems.extend(
        f"{where(match.start())}: {_quote(match.group(0))} cites a line number; "
        "cite the function, class, or heading instead"
        for match in sorted(line_numbers, key=lambda match: match.start())
    )
    problems.extend(
        f"{where(match.start())}: {_quote(match.group(0))} cannot be checked; "
        "cite the section as `path#anchor` or the function or class as `path:Symbol`"
        for match in sorted(
            [*_QUOTED_HEADING.finditer(prose), *_NAME_BESIDE_PATH.finditer(prose)], key=lambda match: match.start()
        )
    )
    for span in spans:
        raw = span.group(2)
        # CommonMark reads a line break in a span as a space, and drops one
        # space at each end when both are there.
        # A stray space at one end alone would hide the reference, so both
        # ends are trimmed for the check.
        content = raw.replace("\n", " ").strip()
        if "\n" in raw and _REFERENCE.match(raw.split()[0]) and re.search(r"[:#]", raw.split()[0]):
            problems.append(f"{where(span.start())}: `{content}`: keep a reference on one line so it can be read")
            continue
        problem = _check_span(content, short_forms, files)
        if problem:
            problems.append(f"{where(span.start())}: `{content}`: {problem}")
    return problems


def _quote(text: str) -> str:
    """Wrap text in a code span, with a longer backtick run when the text holds backticks."""
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def _blank_fenced_blocks(text: str) -> str:
    lines = text.split("\n")
    fence: str | None = None
    for index, line in enumerate(lines):
        match = _FENCE.match(line)
        if fence is None and match:
            fence = match.group(1)
        elif fence is not None:
            if (
                match
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
                and not match.group(2).strip()
            ):
                fence = None
            lines[index] = " " * len(line)
    return "\n".join(lines)


def _check_span(span: str, short_forms: dict[str, str], files: "_SourceFiles") -> str | None:
    """Return what is wrong with one code span, or None when it is fine or is not a reference."""
    if _LINE_NUMBER_SPAN.match(span):
        return (
            "cites a line number, which goes stale when the code moves; name the enclosing function, "
            "class, or heading instead (`path:Symbol` or `path#anchor`)"
        )
    match = _REFERENCE.match(span)
    if match is None:
        return None
    path, ext, sep, target = match.group("path", "ext", "sep", "target")
    real = _expand(path, short_forms)
    if "/" not in path and not files.exists(real):
        # A bare file name such as `vue.md` is prose unless the file sits
        # at the repository root, and `example.com:8000` is not a file at
        # all; a code or Markdown name followed by a symbol or an anchor is
        # a reference that does not say which file it means.
        if sep is None or (ext not in _SYMBOL_CHECKERS and ext != "md"):
            return None
        return "write the file's path from the repository root, or with a short form such as `citry/`"
    if not files.exists(real):
        read_as = f" (read as {real})" if real != path else ""
        return f"{path}{read_as} does not exist; find where the file moved and update the row"
    if sep is None:
        return None
    if not target:
        return f"nothing follows `{sep}`; name a symbol after `:` or a heading anchor after `#`"
    if ext == "md":
        if sep == ":":
            return f"`:` names a code symbol; cite a Markdown section as `{path}#heading-anchor`"
        return _check_anchor(path, files.read(real), target)
    if sep == "#":
        return f"`#` names a Markdown heading; cite code as `{path}:Symbol`"
    checker = _SYMBOL_CHECKERS.get(ext)
    if checker is None:
        return f"cannot check a symbol in a .{ext} file; cite the file alone (`{path}`)"
    return checker(path, files.read(real), target)


def _expand(path: str, short_forms: dict[str, str]) -> str:
    for short, full in short_forms.items():
        if path.startswith(short):
            return full + path[len(short) :]
    return path


class _SourceFiles:
    """Read each cited file once; the doc cites some files dozens of times."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._texts: dict[str, str] = {}

    def exists(self, relative: str) -> bool:
        return (self._root / relative).is_file()

    def read(self, relative: str) -> str:
        if relative not in self._texts:
            self._texts[relative] = (self._root / relative).read_text(encoding="utf-8")
        return self._texts[relative]


def _not_defined(name: str, owner: str, path: str) -> str:
    where = f"`{owner}` in {path}" if owner else path
    return f"`{name}` is not defined in {where}; {_FIX}"


def _not_a_symbol(symbol: str, example: str) -> str:
    return f"`{symbol}` is not a symbol name; write it as {example}"


# ---------------------------------------------------------------------------
# Markdown anchors
# ---------------------------------------------------------------------------

_ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
# Python-Markdown's attr_list syntax, which the docs site uses to keep an
# anchor stable when a heading's text changes: ## Short title { #old-anchor }
_ATTRIBUTE_LIST = re.compile(r"[ \t]*\{:?[ \t]*([^{}]*?)[ \t]*\}$")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def _check_anchor(path: str, source: str, anchor: str) -> str | None:
    anchors, own_id_for_slug = _markdown_anchors(source)
    if anchor in anchors:
        return None
    if anchor in own_id_for_slug:
        return (
            f"that heading sets its own anchor; cite `{path}#{own_id_for_slug[anchor]}`, "
            "which stays the same when the heading's text changes"
        )
    return f"{path} has no heading with the anchor `#{anchor}`; find the section the row means and use its anchor"


@cache
def _markdown_anchors(source: str) -> tuple[frozenset[str], dict[str, str]]:
    """
    Return every heading anchor in a Markdown file.

    The second value maps GitHub's slug of a heading that sets its own id to
    that id, so the error for the slug can name the anchor to use.
    """
    anchors: set[str] = set()
    own_id_for_slug: dict[str, str] = {}
    counts: dict[str, int] = {}
    # A heading in an HTML comment or a fenced block is not shown, so it has
    # no anchor; blanking keeps the other lines where they were.
    visible = _blank_fenced_blocks(_HTML_COMMENT.sub(lambda match: re.sub(r"[^\n]", " ", match.group(0)), source))
    for line in _without_front_matter(visible.split("\n")):
        heading = _ATX_HEADING.match(line)
        if heading is None:
            continue
        content = re.sub(r"[ \t]+#+$", "", heading.group(2) or "")
        own_id = _own_id(content)
        if own_id is not None:
            anchors.add(own_id)
            own_id_for_slug[_github_slug(content)] = own_id
            continue
        # GitHub numbers a repeated slug: `limits`, `limits-1`, `limits-2`.
        slug = _github_slug(content)
        seen = counts.get(slug, 0)
        counts[slug] = seen + 1
        anchors.add(slug if seen == 0 else f"{slug}-{seen}")
    return frozenset(anchors), own_id_for_slug


def _own_id(heading: str) -> str | None:
    """Return the id an attr_list at the end of a heading sets (`{ #id }`, `{: .note #id }`), if any."""
    attributes = _ATTRIBUTE_LIST.search(heading)
    if attributes is None:
        return None
    tokens = attributes.group(1).split()
    # Every token of an attribute list is `.class`, `#id`, or `key=value`;
    # anything else means the braces are part of the heading's text.
    if not tokens or not all(token[0] in ".#" or "=" in token for token in tokens):
        return None
    ids = [token[1:] for token in tokens if token.startswith("#") and len(token) > 1]
    return ids[-1] if ids else None


def _without_front_matter(lines: list[str]) -> list[str]:
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return lines[index + 1 :]
    return lines


def _github_slug(heading: str) -> str:
    """Return the anchor GitHub gives a heading: its rendered text, lowercased, with punctuation dropped."""
    # Keep the text of code spans and links; drop HTML tags and emphasis
    # markers, which GitHub does not show as text.
    codes: list[str] = []

    def hold_code(match: re.Match[str]) -> str:
        codes.append(match.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`+([^`]*?)`+", hold_code, heading)
    text = re.sub(r"!?\[([^\]]*)\](?:\([^)]*\)|\[[^\]]*\])", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text)
    text = re.sub(r"(?<!\w)[*_](.+?)[*_](?!\w)", r"\1", text)
    text = re.sub(r"\x00(\d+)\x00", lambda match: codes[int(match.group(1))], text)
    # Like GitHub, keep letters, marks, numbers, `_`, `-`, and spaces, then
    # turn each space into a hyphen without merging neighbors.
    kept = "".join(char for char in text.strip().lower() if char in "-_ " or unicodedata.category(char)[0] in "LMN")
    return kept.replace(" ", "-")


# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

_PythonDefinition = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
# `type X = ...` exists from Python 3.12; the repository supports 3.11.
_TYPE_ALIAS: type | None = getattr(ast, "TypeAlias", None)


def _check_python(path: str, source: str, symbol: str) -> str | None:
    if not _DOTTED_SYMBOL.match(symbol):
        return _not_a_symbol(symbol, f"dotted names, such as `{path}:Class.method`")
    try:
        body: list[ast.stmt] = _parse_python(source).body
    except SyntaxError as error:
        return f"{path} does not parse as Python ({error.msg}, line {error.lineno})"
    # Assignments count at module level and in a class body (a constant or
    # a class attribute), not inside a function, where they are locals.
    allow_assignment = True
    names = symbol.split(".")
    for index, name in enumerate(names):
        found = _python_member(body, name, allow_assignment=allow_assignment)
        if found is None:
            return _not_defined(name, ".".join(names[:index]), path)
        if not isinstance(found, _PythonDefinition):
            if index + 1 < len(names):
                owner = ".".join(names[: index + 1])
                return f"`{owner}` in {path} is a value, not a function or class; cite `{path}:{owner}` itself"
            return None
        body = found.body
        allow_assignment = isinstance(found, ast.ClassDef)
    return None


@cache
def _parse_python(source: str) -> ast.Module:
    return ast.parse(source)


def _python_member(body: list[ast.stmt], name: str, *, allow_assignment: bool) -> ast.stmt | None:
    """Find a definition of `name` in one block, looking into its `if`, `try`, and `with` blocks too."""
    for statement in body:
        if isinstance(statement, _PythonDefinition):
            # A def or class is a definition; what is inside it belongs to
            # the next name in the symbol, not to this block.
            if statement.name == name:
                return statement
            continue
        if allow_assignment and name in _assigned_names(statement):
            return statement
        # A definition under `if TYPE_CHECKING:` or in a `try` fallback
        # still belongs to this block.
        for inner in _nested_blocks(statement):
            found = _python_member(inner, name, allow_assignment=allow_assignment)
            if found is not None:
                return found
    return None


def _assigned_names(statement: ast.stmt) -> list[str]:
    targets: list[ast.expr]
    if isinstance(statement, ast.Assign):
        targets = list(statement.targets)
    elif isinstance(statement, ast.AnnAssign):
        targets = [statement.target]
    elif _TYPE_ALIAS is not None and isinstance(statement, _TYPE_ALIAS):
        targets = [statement.name]  # type: ignore[attr-defined]  # narrowed through a runtime type
    else:
        return []
    names: list[str] = []
    while targets:
        # Unpacking can nest: `a, (b, c) = ...` assigns all three.
        target = targets.pop()
        if isinstance(target, ast.Tuple | ast.List):
            targets.extend(target.elts)
        elif isinstance(target, ast.Starred):
            targets.append(target.value)
        elif isinstance(target, ast.Name):
            names.append(target.id)
    return names


def _nested_blocks(statement: ast.stmt) -> Iterator[list[ast.stmt]]:
    for field in ("body", "orelse", "finalbody"):
        block = getattr(statement, field, None)
        if isinstance(block, list):
            yield block
    for handler in getattr(statement, "handlers", []):
        yield handler.body
    for case in getattr(statement, "cases", []):
        yield case.body


# ---------------------------------------------------------------------------
# JavaScript, TypeScript, Rust, and Pest
# ---------------------------------------------------------------------------

# These files are read with a few patterns, and a name counts when any one of
# them finds it defined anywhere in the file. Each pattern starts at the
# beginning of a line (after indentation and keywords such as `export` or
# `pub`), so a name after `//` or in the middle of a line does not count,
# and no reader of comments and strings is needed. What does count: a line
# inside a block comment or a multi-line string that starts like a
# definition, a control keyword such as `if (x) {`, a parameter line, and a
# plain reassignment. The check also cannot see that a name was renamed when
# another definition with the same name is left in the file. Python files do
# not have these gaps: `ast` reads them in full.

_JS_MODIFIERS = (
    r"(?:(?:export|default|declare|abstract|static|async|get|set|public|private|protected|readonly|override)[ \t]+)*"
)
_JS_DEFINITIONS = tuple(
    re.compile(pattern, re.MULTILINE)
    for pattern in (
        # function name  /  class Name  /  const name  /  type Name
        rf"^[ \t]*{_JS_MODIFIERS}"
        rf"(?:function[ \t]*\*?|class|interface|enum|namespace|type|const|let|var)[ \t]+({_NAME})",
        # A method, an object property, or a class field: name(  name<T>(  name:  name =
        # After the `(`, the parameters must run on to the next line, or close with a
        # `{` (a method) or `: Type;` (a signature) after them, so that a call
        # such as `own(x) || own(y)) {` or `foo(a, () => {` is not a method.
        rf"^[ \t]*{_JS_MODIFIERS}\*?[ \t]*({_NAME})[ \t]*[?!]?[ \t]*"
        r"(?:(?:<[^>\n]*>)?\((?:[ \t]*$|[^()\n]*(?:\([^()\n]*\)[^()\n]*)*"
        r"\)[ \t]*(?::[^\n{;=]*;|(?::[^\n{;=]*)?\{))|:|=(?![=>]))",
        # A property added to an object: Object.defineProperty(target, "name", ...)
        rf"^[ \t]*Object\.defineProperty\(\s*[\w$.]+\s*,\s*[\"']({_NAME})[\"']",
    )
)

_IDENTIFIER = r"[A-Za-z_]\w*"
# fn name  /  pub(crate) struct Name  /  pub const fn name  /  const NAME: T
_RUST_ITEM = re.compile(
    r"^[ \t]*(?:pub(?:\([^)\n]*\))?[ \t]+)?(?:(?:async|const|unsafe)[ \t]+)*"
    rf"(?:fn|struct|enum|trait|type|union|mod|const|static)[ \t]+({_IDENTIFIER})\b",
    re.MULTILINE,
)
# An `impl` line and the lines of its header up to the `{`, which name the
# type the block is for (`impl<'a> Writer<'a> {`, `impl Display for Writer {`).
_RUST_IMPL = re.compile(r"^[ \t]*(?:unsafe[ \t]+)?impl\b([^{]*)", re.MULTILINE)

# A Pest rule starts its line: name = { ... }
_PEST_RULE = re.compile(rf"^[ \t]*({_IDENTIFIER})[ \t]*=", re.MULTILINE)


@cache
def _javascript_names(source: str) -> frozenset[str]:
    return frozenset(match.group(1) for pattern in _JS_DEFINITIONS for match in pattern.finditer(source))


@cache
def _rust_names(source: str) -> tuple[frozenset[str], frozenset[str]]:
    """Return the names of the items a Rust file defines, and the names in the headers of its `impl` blocks."""
    items = frozenset(match.group(1) for match in _RUST_ITEM.finditer(source))
    impl_names = frozenset(
        name for match in _RUST_IMPL.finditer(source) for name in re.findall(_IDENTIFIER, match.group(1))
    )
    return items, impl_names


def _check_javascript(path: str, source: str, symbol: str) -> str | None:
    if not _DOTTED_SYMBOL.match(symbol):
        return _not_a_symbol(symbol, f"dotted names, such as `{path}:object.method`")
    defined = _javascript_names(source)
    # Each part of a dotted name must be defined somewhere in the file; where
    # one sits inside another is not checked.
    missing = next((name for name in symbol.split(".") if name not in defined), None)
    return None if missing is None else _not_defined(missing, "", path)


def _check_rust(path: str, source: str, symbol: str) -> str | None:
    if not _RUST_SYMBOL.match(symbol):
        return _not_a_symbol(symbol, f"`name` or `Type::method`, such as `{path}:Writer::element`")
    items, impl_names = _rust_names(source)
    type_name, separator, member = symbol.rpartition("::")
    # A type counts when the file defines it or has an `impl` for it, since
    # the type may be defined in another file of the crate.
    if separator and type_name not in items | impl_names:
        return _not_defined(type_name, "", path)
    return None if member in items else _not_defined(member, "", path)


def _check_pest(path: str, source: str, symbol: str) -> str | None:
    if not _PEST_SYMBOL.match(symbol):
        return _not_a_symbol(symbol, f"one grammar rule, such as `{path}:html_attribute`")
    if symbol in {match.group(1) for match in _PEST_RULE.finditer(source)}:
        return None
    return f"rule `{symbol}` is not defined in {path}; {_FIX}"


_SYMBOL_CHECKERS: dict[str, Callable[[str, str, str], str | None]] = {
    "py": _check_python,
    "js": _check_javascript,
    "mjs": _check_javascript,
    "ts": _check_javascript,
    "rs": _check_rust,
    "pest": _check_pest,
}
