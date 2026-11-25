"""
Check that every code and docs reference in the trust-boundary design doc still points at something.

`docs/design/trust_boundaries.md` says, for each input that reaches the page,
which function checks it and which docs section states the rule. It cites
code as `path:Symbol` (`citry/attrs.py:validate_html_attr_name`) and a
Markdown section as `path#anchor` (`docs/security.md#authorize-every-event`),
so a reference keeps working while lines move and breaks only when the thing
it names is renamed, moved, or deleted. This check finds those breaks:

- every cited file exists, including a path written alone;
- the symbol is defined in a code file. Python is read with `ast`.
  JavaScript, TypeScript, Rust, and Pest are read with patterns, after
  `_mask` blanks out their comments and strings, so a name in a comment or
  a brace in a string does not count;
- the anchor names a heading in the Markdown file: the heading's own
  `{ #id }` when it sets one, otherwise GitHub's slug of its text;
- no reference cites a line number, so references cannot drift again.

The short path forms (`citry/` for `packages/py/citry/citry/` and the
others) are read from the list in the doc itself, so the doc and this check
always agree on them. The check proves that each name still exists, not
that the row still describes it; the Mechanism 7 security pass checks that.
"""

import ast
import re
import unicodedata
from collections.abc import Callable, Iterator
from functools import cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DOC = Path("docs/design/trust_boundaries.md")

_CODE_SPAN = re.compile(r"`([^`\n]+)`")

# The doc's list of short forms, one item per line: - `citry/` is `packages/py/citry/citry/`
_SHORT_FORM = re.compile(r"^- `([\w.-]+/)` is `([\w./-]+/)`$", re.MULTILINE)

# A reference: a file path, then `:Symbol` or `#anchor`, or nothing for a
# path written alone.
_REFERENCE = re.compile(r"^(?P<path>[\w.-]+(?:/[\w.-]+)*\.(?P<ext>[A-Za-z]+))(?:(?P<sep>[:#])(?P<target>.*))?$")

# A line number in a code span: `citry/attrs.py:140`, `attrs.py:140-153`,
# or `:140` on its own for the file named earlier.
_LINE_NUMBER_SPAN = re.compile(r"^(?:[\w./-]*\.[A-Za-z]+)?:\d+(?:-\d+)?$")

# A line number outside a code span: `attrs.py:140`, or a GitHub `#L140` link.
_LINE_NUMBER_TEXT = re.compile(r"[\w-]\.(?:py|js|ts|rs|pest|md|ya?ml)(?::\d+|#L\d+)")

# One name in a symbol; JavaScript allows `$` in names.
_NAME = r"[A-Za-z_$][\w$]*"
_DOTTED_SYMBOL = re.compile(rf"^{_NAME}(?:\.{_NAME})*$")
_RUST_SYMBOL = re.compile(r"^[A-Za-z_]\w*(?:::[A-Za-z_]\w*)?$")
_PEST_SYMBOL = re.compile(r"^[A-Za-z_]\w*$")

_FIX = "find where it moved and update the row"


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

    problems: list[str] = []
    files = _SourceFiles(root)
    for number, line in enumerate(text.splitlines(), start=1):
        where = f"{DOC}:{number}"
        problems.extend(
            f"{where}: `{match.group(0)}` outside a code span cites a line number; "
            "cite the function, class, or heading instead"
            for match in _LINE_NUMBER_TEXT.finditer(_CODE_SPAN.sub("", line))
        )
        for span in _CODE_SPAN.findall(line):
            problem = _check_span(span, short_forms, files)
            if problem:
                problems.append(f"{where}: `{span}`: {problem}")
    return problems


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
    if "/" not in path:
        # A bare file name such as `vue.md` is prose; one followed by a
        # symbol or anchor is a reference that does not say which file.
        if sep is None:
            return None
        return "write the file's path from the repository root, or with a short form such as `citry/`"

    real = _expand(path, short_forms)
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


def _within(region: tuple[int, int], position: int) -> bool:
    return region[0] < position < region[1]


def _not_defined(name: str, owner: str, path: str) -> str:
    where = f"`{owner}` in {path}" if owner else path
    return f"`{name}` is no longer defined in {where}; {_FIX}"


# ---------------------------------------------------------------------------
# Markdown anchors
# ---------------------------------------------------------------------------

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
# Python-Markdown's attr_list syntax, which the docs site uses to keep an
# anchor stable when a heading's text changes: ## Short title { #old-anchor }
_OWN_ID = re.compile(r"[ \t]*\{:?[ \t]*#([\w-]+)[^}]*\}$")


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
    fence: str | None = None
    for line in _without_front_matter(source.splitlines()):
        # A `#` line inside a fenced code block is code, not a heading.
        fence_match = _FENCE.match(line)
        if fence_match:
            marker, rest = fence_match.groups()
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not rest.strip():
                fence = None
            continue
        if fence is not None:
            continue
        heading = _ATX_HEADING.match(line)
        if heading is None:
            continue
        content = re.sub(r"[ \t]+#+$", "", heading.group(2) or "")
        own_id = _OWN_ID.search(content)
        if own_id:
            anchors.add(own_id.group(1))
            own_id_for_slug[_github_slug(content)] = own_id.group(1)
            continue
        # GitHub numbers a repeated slug: `limits`, `limits-1`, `limits-2`.
        slug = _github_slug(content)
        seen = counts.get(slug, 0)
        counts[slug] = seen + 1
        anchors.add(slug if seen == 0 else f"{slug}-{seen}")
    return frozenset(anchors), own_id_for_slug


def _without_front_matter(lines: list[str]) -> list[str]:
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return lines[index + 1 :]
    return lines


def _github_slug(heading: str) -> str:
    """Return the anchor GitHub gives a heading: its rendered text, lowercased, with punctuation dropped."""
    # Keep the text of code spans, links, and images; drop HTML tags and
    # emphasis markers, which GitHub does not show as text.
    codes: list[str] = []

    def hold_code(match: re.Match[str]) -> str:
        codes.append(match.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`+([^`]*?)`+", hold_code, heading)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
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
        return f"write the symbol as dotted names, such as `{path}:Class.method`"
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
                return f"`{'.'.join(names[: index + 1])}` in {path} is a value, so it has no `{names[index + 1]}`"
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
        targets = statement.targets
    elif isinstance(statement, ast.AnnAssign):
        targets = [statement.target]
    elif _TYPE_ALIAS is not None and isinstance(statement, _TYPE_ALIAS):
        targets = [statement.name]  # type: ignore[attr-defined]  # narrowed through a runtime type
    else:
        return []
    names: list[str] = []
    for target in targets:
        elements = target.elts if isinstance(target, ast.Tuple | ast.List) else [target]
        names.extend(element.id for element in elements if isinstance(element, ast.Name))
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
# JavaScript and TypeScript
# ---------------------------------------------------------------------------


def _check_javascript(path: str, source: str, symbol: str) -> str | None:
    if not _DOTTED_SYMBOL.match(symbol):
        return f"write the symbol as dotted names, such as `{path}:object.method`"
    masked = _mask(source, "js")
    # The first name may be defined at any depth: client.js wraps all of its
    # code in one anonymous function, so nothing in it is at the top level.
    regions = [(-1, len(masked))]
    names = symbol.split(".")
    for index, name in enumerate(names):
        definitions = [
            (start, end)
            for start, end in _javascript_definitions(masked, name)
            if any(_within(region, start) for region in regions)
        ]
        if not definitions:
            return _not_defined(name, ".".join(names[:index]), path)
        # Each later name must be defined inside the body of the one before.
        regions = [block for _, end in definitions if (block := _block_after(masked, end))]
        if not regions and index + 1 < len(names):
            return f"`{'.'.join(names[: index + 1])}` in {path} has no body, so it has no `{names[index + 1]}`"
    return None


# The ways a JavaScript or TypeScript name is defined, as a test of the text
# just before the name and a test of the text from the name's end. The name
# itself is found first with a plain word search, which keeps this fast.
_JS_MODIFIERS = r"(?:(?:async|static|get|set|public|private|protected|readonly|override)\s+)*"
_JS_DEFINITION_FORMS = (
    # function name(  /  function* name<T>(
    (re.compile(r"\bfunction\b\s*\*?\s*\Z"), re.compile(r"\s*[<(]")),
    (re.compile(r"\bclass\s+\Z"), re.compile(r"")),
    # const name =  /  let name: Type =
    (re.compile(r"\b(?:const|let|var)\s+\Z"), re.compile(r"\s*[=:]")),
    # A method in a class or object: name(params) {  /  async name<T>(params): Type {
    (
        re.compile(rf"(?:^|[\s,{{;]){_JS_MODIFIERS}\*?\s*\Z", re.MULTILINE),
        re.compile(r"\s*(?:<[^<>]*>)?\s*\([^()]*(?:\([^()]*\)[^()]*)*\)\s*(?::[^{;=]*)?\{"),
    ),
    # An object property: name: value
    (re.compile(r"(?:^|[{,])\s*\Z", re.MULTILINE), re.compile(r"\s*:(?!:)")),
    # "name": value  /  Object.defineProperty(target, "name", ...)
    (re.compile(r"(?:^|[{,])\s*([\"'])\Z", re.MULTILINE), re.compile(r"[\"']\s*:(?!:)")),
    (re.compile(r"\bObject\.defineProperty\(\s*[\w$.]+\s*,\s*[\"']\Z"), re.compile(r"[\"']")),
)
# Far enough back to hold a definition's keywords, and a defineProperty
# call split over lines.
_JS_LOOKBACK = 200


@cache
def _javascript_definitions(masked: str, name: str) -> list[tuple[int, int]]:
    """
    Find where `name` is defined.

    Each result is the name's start and the position right after the name
    (after its closing quote, for a quoted name), where its parameters or
    value begin.
    """
    found: list[tuple[int, int]] = []
    for word in re.finditer(rf"(?<![\w$]){re.escape(name)}(?![\w$])", masked):
        before = masked[max(0, word.start() - _JS_LOOKBACK) : word.start()]
        for prefix, suffix in _JS_DEFINITION_FORMS:
            after = suffix.match(masked, word.end())
            if after and prefix.search(before):
                # A quoted name ends after its closing quote.
                quoted = after.group(0)[:1] in ("'", '"')
                end = word.end() + 1 if quoted else word.end()
                found.append((word.start(), end))
                break
    return found


def _block_after(masked: str, position: int) -> tuple[int, int] | None:
    """
    Return the `{ ... }` body of the definition whose name ends at `position`.

    Skips what can come between a name and its body: TypeScript type
    parameters, `=` or `:`, `async`, and one parameter list, so the
    destructured parameter in `({a}) => {` is not read as the body. A body
    that a call wraps, as in `Object.freeze({`, is the first brace.
    """
    index = _skip_space(masked, position)
    if masked.startswith("<", index):
        index = _skip_space(masked, _matching(masked, index, "<", ">") + 1)
    if masked.startswith(("=", ":"), index) and not masked.startswith("=>", index):
        index = _skip_space(masked, index + 1)
        if re.match(r"async\b", masked[index : index + 6]):
            index = _skip_space(masked, index + len("async"))
    if masked.startswith("(", index):
        index = _matching(masked, index, "(", ")") + 1
    opening = masked.find("{", index)
    statement_end = masked.find(";", index)
    if opening == -1 or -1 < statement_end < opening:
        return None
    return opening, _matching(masked, opening, "{", "}")


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
        return f"write the symbol as `name` or `Type::method`, such as `{path}:Writer::element`"
    masked = _mask(source, "rust")
    blocks = _rust_blocks(masked)
    if "::" not in symbol:
        item = re.compile(
            rf"\b(?:fn|struct|enum|trait|type|union|mod|const|static)\s+{re.escape(symbol)}\b"
            rf"|\bmacro_rules!\s*{re.escape(symbol)}\b"
        )
        positions = [match.start() for match in item.finditer(masked)]
        # A method needs its type in the reference, so a match inside an
        # `impl` or `trait` block does not count as a free item.
        if any(not any(_within(block, position) for _, block in blocks) for position in positions):
            return None
        if positions:
            return f"`{symbol}` in {path} is defined inside an `impl` or `trait` block; cite it as `Type::{symbol}`"
        return _not_defined(symbol, "", path)
    type_name, member = symbol.split("::")
    owned = [block for owner, block in blocks if owner == type_name]
    if not owned:
        return f"{path} has no `impl` or `trait` block for `{type_name}`; {_FIX}"
    member_item = re.compile(rf"\b(?:fn|const|type)\s+{re.escape(member)}\b")
    if any(member_item.search(masked, start, end) for start, end in owned):
        return None
    return f"`{member}` is no longer defined in an `impl` or `trait` block for `{type_name}` in {path}; {_FIX}"


@cache
def _rust_blocks(masked: str) -> list[tuple[str, tuple[int, int]]]:
    """Return the type each `impl` or `trait` block belongs to, with the block's extent."""
    blocks: list[tuple[str, tuple[int, int]]] = []
    for match in _RUST_BLOCK_START.finditer(masked):
        opening = masked.find("{", match.end())
        statement_end = masked.find(";", match.end())
        if opening == -1 or -1 < statement_end < opening:
            continue
        header = masked[match.end() : opening]
        owner = _rust_trait_name(header) if match.group("kind") == "trait" else _rust_self_type(header)
        if owner:
            blocks.append((owner, (opening, _matching(masked, opening, "{", "}"))))
    return blocks


def _rust_trait_name(header: str) -> str | None:
    name = re.match(r"\s*([A-Za-z_]\w*)", header)
    return name.group(1) if name else None


def _rust_self_type(header: str) -> str | None:
    """Return the type an `impl` block is for: `Writer` in `impl<'a> Writer<'a>` and in `impl Display for Writer`."""
    text = header.strip()
    if text.startswith("<"):
        text = text[_matching(text, 0, "<", ">") + 1 :]
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
        return f"name one grammar rule, such as `{path}:html_attribute`"
    rule = re.compile(rf"^[ \t]*{re.escape(symbol)}\s*=\s*[_@$!]?\s*\{{", re.MULTILINE)
    if rule.search(_mask(source, "pest")):
        return None
    return f"rule `{symbol}` is no longer defined in {path}; {_FIX}"


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
            # Without a closing quote it is a lifetime, such as 'a.
            end = literal.end() if literal else index + 1
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
    index = start + 1
    in_class = False
    while index < len(source):
        char = source[index]
        if char == "\\":
            index += 2
            continue
        if char == "\n":
            return index  # a regex never spans lines, so this was not one
        if char == "[":
            in_class = True
        elif char == "]":
            in_class = False
        elif char == "/" and not in_class:
            return index + 1
        index += 1
    return len(source)


def _skip_space(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _matching(text: str, opening: int, open_char: str, close_char: str) -> int:
    """Return the index of the character that closes the one at `opening`, or the text's end."""
    depth = 0
    for index in range(opening, len(text)):
        char = text[index]
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return index
    return len(text)
