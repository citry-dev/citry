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
- the symbol is defined in a code file. Python is read with `ast`.
  JavaScript, TypeScript, Rust, and Pest are read with patterns, after
  `_mask` blanks out their comments and strings, so a name in a comment or
  a brace in a string does not count. A dotted name must be defined
  directly inside the one before it;
- the anchor names a heading in the Markdown file: the heading's own
  `{ #id }` when it sets one, otherwise GitHub's slug of its text.

It also fails on any reference that cites a line number, so references
cannot drift again.

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
# same length. It may wrap onto the next line but not cross a blank line.
_CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)((?:(?!\n[ \t]*\n).)+?)(?<!`)\1(?!`)", re.DOTALL)
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")

# The doc's list of short forms, one item per line: - `citry/` is `packages/py/citry/citry/`
_SHORT_FORM = re.compile(r"^- `([\w.-]+/)` is `([\w./-]+/)`$", re.MULTILINE)

# A reference: a file path, then `:Symbol` or `#anchor`, or nothing for a
# path written alone.
_REFERENCE = re.compile(r"^(?P<path>[\w.-]+(?:/[\w.-]+)*\.(?P<ext>[A-Za-z]+))(?:(?P<sep>[:#])(?P<target>.*))?$")

# Line numbers inside a code span: `attrs.py:140`, `:140-153` (the file
# named earlier), `attrs.py:L140`, `attrs.py#L140`, `attrs.py, line 140`.
_LINE_NUMBER_SPAN = re.compile(
    r"^(?:[\w./-]*\.[A-Za-z]+)?(?::L?\d+(?:\s*-\s*L?\d+)?|#L\d+(?:-L?\d+)?)$"
    r"|^[\w./-]+\.[A-Za-z]+,?\s+\(?lines?\s+\d"
)
_FILE_EXTENSIONS = r"(?:py|pyi|js|mjs|cjs|ts|tsx|rs|pest|md|ya?ml|toml|json|css|html)"
# Line numbers outside a code span: attrs.py:140, or a GitHub #L140 link.
_LINE_NUMBER_TEXT = re.compile(rf"[\w./-]*[\w-]\.{_FILE_EXTENSIONS}(?::\d+|#L\d+)\b")
# A path in a code span followed by :140, "line 140", or "(lines 140-153)".
_LINE_NUMBER_AFTER_SPAN = re.compile(r"(?<!`)(`+)[^`\n]*\.[A-Za-z]+\1(?!`)\s*(?::\d+|,?\s*\(?lines?\s+\d+)")

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
    for span in spans:
        raw = span.group(2)
        # CommonMark reads a line break in a span as a space, and drops one
        # space at each end when both are there.
        content = raw.replace("\n", " ")
        if content.startswith(" ") and content.endswith(" ") and content.strip():
            content = content[1:-1]
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
        # at the repository root; followed by a symbol or an anchor it is a
        # reference that does not say which file it means.
        if sep is None:
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
# Brackets in masked source
# ---------------------------------------------------------------------------


class _Brackets:
    """
    Where each `{`, `(` and `[` in masked source opens and closes.

    Built once per file, so the checks below can ask which block holds a
    position without counting braces from the start of the file each time.
    """

    def __init__(self, masked: str) -> None:
        self.text = masked
        self.positions = [match.start() for match in re.finditer(r"[{}()\[\]]", masked)]
        self.close: dict[int, int] = {}
        self.open_of: dict[int, int] = {}
        # For each bracket, the index of the open bracket around it (-1 at
        # the top), so walking outward from a position is a chain of lookups.
        self.parent: list[int] = []
        stack: list[int] = []
        for index, position in enumerate(self.positions):
            if masked[position] in "{([":
                self.parent.append(stack[-1] if stack else -1)
                stack.append(index)
            else:
                if stack:
                    opening = self.positions[stack.pop()]
                    self.close[opening] = position
                    self.open_of[position] = opening
                self.parent.append(stack[-1] if stack else -1)

    def enclosing(self, position: int) -> Iterator[int]:
        """Yield the open brackets around `position`, innermost first."""
        index = bisect.bisect_left(self.positions, position) - 1
        if index >= 0 and self.text[self.positions[index]] not in "{([":
            index = self.parent[index]
        while index >= 0:
            yield self.positions[index]
            index = self.parent[index]

    def innermost(self, position: int) -> int:
        return next(self.enclosing(position), -1)

    def closing(self, opening: int) -> int:
        return self.close.get(opening, len(self.text))


@cache
def _brackets(masked: str) -> _Brackets:
    return _Brackets(masked)


# ---------------------------------------------------------------------------
# JavaScript and TypeScript
# ---------------------------------------------------------------------------


def _check_javascript(path: str, source: str, symbol: str) -> str | None:
    if not _DOTTED_SYMBOL.match(symbol):
        return _not_a_symbol(symbol, f"dotted names, such as `{path}:object.method`")
    masked = _mask(source, "js")
    brackets = _brackets(masked)
    names = symbol.split(".")
    parent_bodies: list[int] = []
    for index, name in enumerate(names):
        candidates = _javascript_definitions(masked, name)
        # The first name must sit outside every named definition: at the top
        # of the file, or in the anonymous function that wraps client.js, so
        # a local of the same name inside some function does not count. Each
        # later name must sit in the body of the one before it, with only
        # control blocks and anonymous callbacks in between.
        owners = parent_bodies if index else [-1]
        found = [(start, end) for start, end in candidates if _javascript_owner_body(brackets, start) in owners]
        if not found:
            return _not_defined(name, ".".join(names[:index]), path)
        parent_bodies = [body for _, end in found if (body := _block_after(brackets, end)) is not None]
        if not parent_bodies and index + 1 < len(names):
            owner = ".".join(names[: index + 1])
            return f"`{owner}` in {path} has no body to hold `{names[index + 1]}`; cite `{path}:{owner}` itself"
    return None


# The ways a JavaScript or TypeScript name is defined, as a test of the text
# just before the name and a test of the text from the name's end. The name
# itself is found first with a plain word search, which keeps this fast.
_JS_MODIFIERS = r"(?:(?:async|static|get|set|public|private|protected|readonly|override|declare|abstract)\s+)*"
_JS_DEFINITION_FORMS = (
    # function name(  /  function* name<T>(
    (re.compile(r"\bfunction\b\s*\*?\s*\Z"), re.compile(r"\s*[<(]")),
    (re.compile(r"\b(?:class|interface|enum|namespace)\s+\Z"), re.compile(r"")),
    (re.compile(r"\btype\s+\Z"), re.compile(r"\s*(?:<[^<>]*>)?\s*=")),
    # const name =  /  let name: Type =
    (re.compile(r"\b(?:const|let|var)\s+\Z"), re.compile(r"\s*[=:]")),
    # A method in a class or object: name(params) {  /  async name<T>(params): Type {
    (
        re.compile(rf"(?:^|[\s,{{;]){_JS_MODIFIERS}\*?\s*\Z", re.MULTILINE),
        re.compile(r"\s*(?:<[^<>]*>)?\s*\([^()]*(?:\([^()]*\)[^()]*)*\)\s*(?::[^{;=]*)?\{"),
    ),
    # A class field: name = value  /  readonly name: Type = value
    (
        re.compile(rf"(?:^|[;{{])\s*{_JS_MODIFIERS}\Z", re.MULTILINE),
        re.compile(r"\s*[?!]?\s*(?::[^=;{}()]*)?=(?![=>])"),
    ),
    # An object property: name: value
    (re.compile(r"(?:^|[{,])\s*\Z", re.MULTILINE), re.compile(r"\s*:(?!:)")),
    # "name": value  /  Object.defineProperty(target, "name", ...)
    (re.compile(r"(?:^|[{,])\s*[\"']\Z", re.MULTILINE), re.compile(r"[\"']\s*:(?!:)")),
)
# Object.defineProperty(target, "name", ...): the one form whose name sits
# inside the parentheses of a call.
_JS_DEFINE_PROPERTY = (re.compile(r"\bObject\.defineProperty\(\s*[\w$.]+\s*,\s*[\"']\Z"), re.compile(r"[\"']"))
# Far enough back to hold a definition's keywords, and a defineProperty
# call split over lines.
_JS_LOOKBACK = 200
# A block that one of these opens belongs to the code around it, not to a
# definition of its own.
_JS_CONTROL_KEYWORDS = frozenset({"if", "for", "while", "switch", "catch", "with", "else", "try", "finally", "do"})


@cache
def _javascript_definitions(masked: str, name: str) -> list[tuple[int, int]]:
    """
    Find where `name` is defined.

    Each result is the name's start and the position right after the name
    (after its closing quote, for a quoted name), where its parameters or
    value begin.
    """
    brackets = _brackets(masked)
    found: list[tuple[int, int]] = []
    for word in re.finditer(rf"(?<![\w$]){re.escape(name)}(?![\w$])", masked):
        # A definition sits in a block or at the top, never inside the
        # parentheses of a call or a parameter list.
        opening = brackets.innermost(word.start())
        forms = _JS_DEFINITION_FORMS if opening == -1 or masked[opening] == "{" else (_JS_DEFINE_PROPERTY,)
        before = masked[max(0, word.start() - _JS_LOOKBACK) : word.start()]
        for prefix, suffix in forms:
            after = suffix.match(masked, word.end())
            if after and prefix.search(before):
                quoted = after.group(0)[:1] in ("'", '"')
                found.append((word.start(), word.end() + 1 if quoted else word.end()))
                break
    return found


def _javascript_named_block(brackets: _Brackets, opening: int) -> bool:
    """
    Say whether a `{` opens the body of a named definition.

    A control block (`if (x) {`, `else {`) and an anonymous function or
    object (`function (x) {`, a callback such as `items.map((x) => {`)
    return False: a definition inside one belongs to the named definition
    around it.
    """
    masked = brackets.text
    head = _javascript_text_before(masked, opening)
    # `head` starts here in `masked`; it only loses trailing spaces.
    base = max(0, opening - _JS_LOOKBACK)
    if not head or head[-1] in ";{}" or _last_name(head) in _JS_CONTROL_KEYWORDS:
        return False  # a bare block, or one after `else`, `try`, `finally`, or `do`
    # A parameter or condition list, with an optional TypeScript return
    # annotation: `if (x) {`, `name(x) {`, `function name(x) {`, `function (x) {`.
    signature = re.search(r"\)\s*(?::[^{};=()]*)?$", head)
    if signature:
        list_open = brackets.open_of.get(base + signature.start(), -1)
        before_list = re.sub(r"<[^<>]*>$", "", _javascript_text_before(masked, list_open)).rstrip()
        called = _last_name(before_list)
        if called in _JS_CONTROL_KEYWORDS:
            return False
        if called == "function":
            # `const name = function (x) {` is named by what it is assigned to.
            return _javascript_assigned(re.sub(r"(?:\basync\s+)?function$", "", before_list))
        return called is not None
    if head.endswith("=>"):
        # An arrow function: named only when assigned, as in `const name = (x) => {`.
        params = head[:-2].rstrip()
        if params.endswith(")"):
            params = _javascript_text_before(masked, brackets.open_of.get(base + len(params) - 1, -1))
        else:
            params = re.sub(rf"{_NAME}$", "", params)
        return _javascript_assigned(re.sub(r"\basync$", "", params.rstrip()).rstrip())
    if re.search(rf"\b(?:class|interface|enum|namespace)\s+{_NAME}[^{{}};]*$", head):
        return True
    if head[-1] in "(,":
        # An object passed to a call, as in `const name = Object.freeze({`.
        call_open = brackets.innermost(opening)
        callee = re.sub(r"(?:\bnew\s+)?[\w$.]+$", "", _javascript_text_before(masked, call_open)).rstrip()
        return _javascript_assigned(callee)
    return _javascript_assigned(head)


def _javascript_text_before(masked: str, position: int) -> str:
    return masked[max(0, position - _JS_LOOKBACK) : max(position, 0)].rstrip()


def _last_name(text: str) -> str | None:
    word = re.search(rf"(?<![\w$.])({_NAME})$", text)
    return word.group(1) if word else None


def _javascript_assigned(text: str) -> bool:
    """Say whether `text` ends where a value is given a name: `const name =`, `name:`, or `name =`."""
    return (
        re.search(
            rf"(?:\b(?:const|let|var)\s+{_NAME}\s*(?::[^=;{{}}]*)?=|(?:^|[{{,;])\s*[\"']?{_NAME}[\"']?\s*[:=])$",
            text,
            re.MULTILINE,
        )
        is not None
    )


def _javascript_owner_body(brackets: _Brackets, position: int) -> int:
    """Return the `{` of the nearest named definition's body around `position`, or -1 at the top level."""
    for opening in brackets.enclosing(position):
        if brackets.text[opening] == "{" and _javascript_named_block(brackets, opening):
            return opening
    return -1


def _block_after(brackets: _Brackets, position: int) -> int | None:
    """
    Return the `{` that opens the body of the definition whose name ends at `position`.

    Skips what can come between a name and its body: TypeScript type
    parameters, `=` or `:`, `async`, and one parameter list, so the
    destructured parameter in `({a}) => {` is not read as the body. A body
    that a call wraps, as in `Object.freeze({`, is the first brace.
    """
    masked = brackets.text
    index = _skip_space(masked, position)
    if masked.startswith("<", index):
        index = _skip_space(masked, _matching_angle(masked, index) + 1)
    if masked.startswith(("=", ":"), index) and not masked.startswith("=>", index):
        index = _skip_space(masked, index + 1)
        if re.match(r"async\b", masked[index : index + 6]):
            index = _skip_space(masked, index + len("async"))
    if masked.startswith("(", index):
        index = brackets.closing(index) + 1
    opening = masked.find("{", index)
    statement_end = masked.find(";", index)
    if opening == -1 or -1 < statement_end < opening:
        return None
    return opening


# ---------------------------------------------------------------------------
# Rust and Pest
# ---------------------------------------------------------------------------

# An `impl` or `trait` item starts its line (after `pub` or `unsafe`); this
# leaves out `impl Trait` written in a function's argument or return type.
_RUST_BLOCK_START = re.compile(
    r"^[ \t]*(?:pub(?:\([^)\n]*\))?[ \t]+)?(?:unsafe[ \t]+)?(?:auto[ \t]+)?(?P<kind>impl|trait)\b", re.MULTILINE
)


def _check_rust(path: str, source: str, symbol: str) -> str | None:
    if not _RUST_SYMBOL.match(symbol):
        return _not_a_symbol(symbol, f"`name` or `Type::method`, such as `{path}:Writer::element`")
    masked = _mask(source, "rust")
    brackets = _brackets(masked)
    blocks = _rust_blocks(masked)
    if "::" not in symbol:
        item = re.compile(
            rf"\b(?:fn|struct|enum|trait|type|union|mod|const|static)\s+{re.escape(symbol)}\b"
            rf"|\bmacro_rules!\s*{re.escape(symbol)}\b"
        )
        positions = [match.start() for match in item.finditer(masked)]
        # A free item sits at the top of the file or in a `mod` block; one
        # in an `impl` or `trait` block needs its type, and one inside a
        # function is local to it.
        if any(all(_rust_opens_mod(masked, opening) for opening in brackets.enclosing(at)) for at in positions):
            return None
        impl_openings = {opening for _, (opening, _) in blocks}
        if any(opening in impl_openings for at in positions for opening in brackets.enclosing(at)):
            return f"`{symbol}` in {path} is defined in an `impl` or `trait` block; cite it as `Type::{symbol}`"
        if positions:
            return f"`{symbol}` in {path} is defined inside another item; cite the item that holds it"
        return _not_defined(symbol, "", path)
    type_name, member = symbol.split("::")
    owned = [opening for owner, (opening, _) in blocks if owner == type_name]
    if not owned:
        return f"{path} has no `impl` or `trait` block for `{type_name}`; {_FIX}"
    member_item = re.compile(rf"\b(?:fn|const|type)\s+{re.escape(member)}\b")
    for opening in owned:
        for match in member_item.finditer(masked, opening, brackets.closing(opening)):
            # Directly in the block, not in a function nested in a method.
            if brackets.innermost(match.start()) == opening:
                return None
    return f"`{member}` is not defined in an `impl` or `trait` block for `{type_name}` in {path}; {_FIX}"


def _rust_opens_mod(masked: str, opening: int) -> bool:
    return re.search(r"\bmod\s+\w+\s*$", masked[max(0, opening - 100) : opening]) is not None


@cache
def _rust_blocks(masked: str) -> list[tuple[str, tuple[int, int]]]:
    """Return the type each `impl` or `trait` block belongs to, with the block's extent."""
    brackets = _brackets(masked)
    blocks: list[tuple[str, tuple[int, int]]] = []
    for match in _RUST_BLOCK_START.finditer(masked):
        opening = _rust_block_opening(masked, match.end())
        if opening is None:
            continue
        header = masked[match.end() : opening]
        owner = _rust_trait_name(header) if match.group("kind") == "trait" else _rust_self_type(header)
        if owner:
            blocks.append((owner, (opening, brackets.closing(opening))))
    return blocks


def _rust_block_opening(masked: str, start: int) -> int | None:
    """Return the `{` that opens an item's block, or None for an item that ends with `;` first."""
    # Outside `(` and `[`, so the `;` in `impl From<[u8; 16]> for Id` does not end the header.
    depth = 0
    for index in range(start, len(masked)):
        char = masked[index]
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif depth == 0 and char == "{":
            return index
        elif depth == 0 and char == ";":
            return None
    return None


def _rust_trait_name(header: str) -> str | None:
    name = re.match(r"\s*([A-Za-z_]\w*)", header)
    return name.group(1) if name else None


def _rust_self_type(header: str) -> str | None:
    """Return the type an `impl` block is for: `Writer` in `impl<'a> Writer<'a>` and in `impl Display for Writer`."""
    # The `>` of `->` in a bound such as `F: Fn() -> u8` is not a bracket.
    text = header.replace("->", "  ").strip()
    if text.startswith("<"):
        text = text[_matching_angle(text, 0) + 1 :]
    text = re.split(r"\bwhere\b", text, maxsplit=1)[0]
    # `for` outside angle brackets separates the trait from the type.
    depth = 0
    for match in re.finditer(r"[<>]|\bfor\b", text):
        piece = match.group(0)
        if piece == "<":
            depth += 1
        elif piece == ">":
            depth -= 1
        elif depth == 0:
            text = text[match.end() :]
            break
    path = re.match(r"\s*(?:&\s*(?:'\w+\s+)?(?:mut\s+)?)?(?:dyn\s+)?([\w:]+)", text)
    return path.group(1).rsplit("::", 1)[-1] if path else None


def _check_pest(path: str, source: str, symbol: str) -> str | None:
    if not _PEST_SYMBOL.match(symbol):
        return _not_a_symbol(symbol, f"one grammar rule, such as `{path}:html_attribute`")
    rule = re.compile(rf"^[ \t]*{re.escape(symbol)}\s*=\s*[_@$!]?\s*\{{", re.MULTILINE)
    if rule.search(_mask(source, "pest")):
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


# ---------------------------------------------------------------------------
# Masking: blank out comments, strings, and regular expressions
# ---------------------------------------------------------------------------

# Where the next comment, string, or regular expression can start.
_MASK_START = {
    "js": re.compile(r"""[/'"`]"""),
    # Rust raw strings: r"...", r#"..."#, br"...", cr"..."
    "rust": re.compile(r"""[/'"]|(?<!\w)[bc]?r#*\""""),
    "pest": re.compile(r"""[/'"]"""),
}
_RUST_CHAR = re.compile(r"'(?:\\(?:u\{[0-9a-fA-F]{1,6}\}|x[0-9a-fA-F]{2}|.)|[^\\'\n])'")
# Before one of these, a `/` in JavaScript starts a regular expression
# rather than a division.
_REGEX_AFTER_CHAR = frozenset("(,=:[!&|?{};+-*%<>~^")
_REGEX_AFTER_WORD = frozenset(
    {"return", "typeof", "instanceof", "in", "of", "new", "delete", "void", "throw", "case", "do", "else"}
    | {"yield", "await"}
)


@cache
def _mask(source: str, language: str) -> str:
    """
    Return `source` with the inside of every comment, string, and regex replaced by spaces.

    Offsets and line breaks stay where they were, so a brace count or a
    pattern match on the result reads only code. A JavaScript string that
    holds a single name (`"pageNonce"`) is kept, because a property name can
    be written that way, and such a string holds no brace.
    """
    chars = list(source)
    length = len(source)
    start_pattern = _MASK_START[language]

    def blank(start: int, end: int) -> None:
        for index in range(start, end):
            if chars[index] != "\n":
                chars[index] = " "

    index = 0
    while (found := start_pattern.search(source, index)) is not None:
        index = found.start()
        char = source[index]
        if source.startswith("//", index):
            end = source.find("\n", index)
            end = length if end == -1 else end
        elif source.startswith("/*", index):
            end = _block_comment_end(source, index, nested=language == "rust")
        elif char in "bcr":
            # Only the Rust pattern starts with a letter: a raw string.
            hashes = found.group(0).count("#")
            close = source.find('"' + "#" * hashes, found.end())
            end = length if close == -1 else close + 1 + hashes
        elif char == "'" and language == "rust":
            literal = _RUST_CHAR.match(source, index)
            if literal is None:
                # A lifetime such as 'a: keep it, since an `impl` header
                # needs it to tell `&'a Type` from a type named `a`.
                index += 1
                continue
            end = literal.end()
        elif char in "'\"":
            end = _string_end(source, index, multiline=language == "rust")
            if language == "js" and re.fullmatch(_NAME, source[index + 1 : end - 1]):
                index = end
                continue
        elif char == "`":
            end = _template_end(source, index)
        elif char == "/" and language == "js" and _starts_regex(source, index):
            end = _regex_end(source, index)
        else:
            index += 1
            continue
        blank(index, end)
        index = end
    return "".join(chars)


def _block_comment_end(source: str, start: int, *, nested: bool) -> int:
    depth = 0
    index = start
    while index < len(source):
        if source.startswith("/*", index):
            depth += 1
            index += 2
        elif source.startswith("*/", index):
            depth -= 1
            index += 2
            if depth == 0 or not nested:
                return index
        else:
            index += 1
    return len(source)


def _string_end(source: str, start: int, *, multiline: bool) -> int:
    """Return the index just past the closing quote; a JS or Pest string that does not close ends at the line end."""
    quote = source[start]
    index = start + 1
    while index < len(source):
        char = source[index]
        if char == "\\":
            index += 2
            continue
        if char == quote:
            return index + 1
        if char == "\n" and not multiline:
            return index
        index += 1
    return len(source)


def _template_end(source: str, start: int) -> int:
    """Return the index just past a JavaScript template literal, reading through its `${ }` parts."""
    index = start + 1
    while index < len(source):
        char = source[index]
        if char == "\\":
            index += 2
        elif char == "`":
            return index + 1
        elif source.startswith("${", index):
            index = _substitution_end(source, index + 2)
        else:
            index += 1
    return len(source)


def _substitution_end(source: str, index: int) -> int:
    """Return the index just past the `}` that closes a template's `${`."""
    depth = 1
    while index < len(source):
        char = source[index]
        if char in "'\"":
            index = _string_end(source, index, multiline=False)
        elif char == "`":
            index = _template_end(source, index)
        else:
            depth += {"{": 1, "}": -1}.get(char, 0)
            index += 1
            if depth == 0:
                return index
    return len(source)


def _starts_regex(source: str, index: int) -> bool:
    before = index - 1
    while before >= 0 and source[before].isspace():
        before -= 1
    if before < 0 or source[before] in _REGEX_AFTER_CHAR:
        return True
    word_end = before + 1
    while before >= 0 and (source[before].isalnum() or source[before] in "_$"):
        before -= 1
    return source[before + 1 : word_end] in _REGEX_AFTER_WORD


def _regex_end(source: str, start: int) -> int:
    """Return the index just past a regular expression, or just past the `/` when it was a division after all."""
    index = start + 1
    in_class = False
    while index < len(source):
        char = source[index]
        if char == "\\":
            index += 2
            continue
        if char == "\n":
            # A regex never spans lines, so this `/` was not one; blank only
            # the `/` rather than the code after it.
            return start + 1
        if char == "[":
            in_class = True
        elif char == "]":
            in_class = False
        elif char == "/" and not in_class:
            return index + 1
        index += 1
    return start + 1


def _skip_space(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _matching_angle(text: str, opening: int) -> int:
    """Return the index of the `>` that closes the `<` at `opening`, or the text's end."""
    depth = 0
    for index in range(opening, len(text)):
        char = text[index]
        if char == "<":
            depth += 1
        elif char == ">" and text[index - 1] != "=":
            depth -= 1
            if depth == 0:
                return index
    return len(text)
