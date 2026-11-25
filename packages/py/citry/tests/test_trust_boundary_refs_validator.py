"""The trust-boundary reference validator reports a code or docs reference that no longer points at anything."""

from pathlib import Path

import pytest
from scripts.validators import trust_boundary_refs

_SHORT_FORMS = """\
- `pkg/` is `packages/py/pkg/pkg/`
- `docs/` is `docs_site/content/`
"""

_PYTHON = """\
from typing import TYPE_CHECKING

LIMIT = 5
first, (second, third) = 1, (2, 3)


class Checker:
    mode: str = "strict"

    def check(self, value):
        local = 1

        def helper():
            return local

        return helper()


def make_component():
    class Inner:
        def on_render(self):
            return None

    return Inner


if TYPE_CHECKING:
    pass
else:
    def fallback(): ...
"""

# One definition of each form the check reads. A name in a comment, in a
# string, after other code on its line, or in a call is not a definition.
_JAVASCRIPT = """\
// function commentOnly() {}
/*
 * function blockCommentOnly() {}
 */
export async function startApp(root) {
  const label = "function stringOnly() {";
  const host = {
    preflight(result) {
      return result;
    },
    mode: 1,
  };
  registerCallOnly(host);
  items.forEach(function () {
    callbackOnly(host, () => {
    });
  });
  return host;
}
function* ids() {}
export default class Store {
  static async load() {}
  get size() { return 1; }
  set extent(value) {}
  private readonly secret?: string;
  maybe!: number;
  limit = 3;
  hooks: Hooks = {};
  *entries() {}
  generic<T>(value: T) {}
  override render(
    context,
  ) {}
  public static create() {}
  protected guard() {}
}
declare const ambient: number;
const settings = 1;
let pending;
var legacy = 2;
enum Level { Low }
namespace Util {}
x => x;
Object.defineProperty(global, "pageNonce", { value: () => null });
export const wrapped = Object.defineProperty(global, "midLineOnly", {});
"""

_MODULE = "export const fromModule = 1;\n"

_TYPESCRIPT = """\
export function makeTarget<T>(input: string): { ok: boolean } {
  return { ok: input.length > 0 };
}
export type Options = { secret: string };
interface Shape {
  area(): number;
  label: string;
}
export abstract class Base {
  abstract measure(scale: number): number;
}
"""

_RUST = """\
// fn comment_only() {}
const NOTE: &str = "see impl Ghost { in the docs";
pub struct Writer<'a> {
    text: &'a str,
}

impl<'a> Writer<'a> {
    pub fn element(&mut self) -> &'a str {
        fn helper() {}
        self.text
    }
}

impl std::fmt::Display for Writer<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        Ok(())
    }
}

// `Id` is defined in another file of the crate.
impl From<[u8; 1]> for Id {
    fn from(bytes: [u8; 1]) -> Self {
        Id(bytes[0])
    }
}

impl<T>
    Pair<T>
{
    fn swap(&self) {}
}

unsafe impl Send for Handle {}

pub(crate) fn escape_text(text: &str) -> String {
    text.to_owned()
}

pub async fn fetch() {}
pub const fn limit_fn() {}
pub unsafe fn send_all() {}
static GLOBAL: u8 = 0;
pub union Bits {
    small: u8,
}

pub trait Render {
    fn render(&self);
}

pub enum Mode {
    Strict,
}

const LIMIT: usize = 3;
pub type Alias = u8;
mod tests {}
"""

_PEST = """\
// comment_rule = { "x" }
html_attribute = { name ~ "=" ~ value }
"""

_MARKDOWN = """\
---
title: Guide
# yaml comment
---
# Guide

## Check `c-bind` keys

## Short title { #stable-anchor }

## See [the **API**](api.md) <em>now</em>

## Limits

## Limits

## Notes { see #x }

<!--
## Hidden heading
-->

```md
## Not a heading
```
"""

_FILES = {
    "ROOT.md": "# Root\n\n## Root heading\n",
    "packages/py/pkg/pkg/mod.py": _PYTHON,
    "packages/py/pkg/pkg/data.yml": "key: value\n",
    "packages/js/app/src/runtime.js": _JAVASCRIPT,
    "packages/js/app/src/module.mjs": _MODULE,
    "packages/js/app/src/types.ts": _TYPESCRIPT,
    "crates/demo/src/lib.rs": _RUST,
    "crates/demo/src/grammar.pest": _PEST,
    "docs_site/content/guide.md": _MARKDOWN,
}

_JS = "packages/js/app/src/runtime.js"
_MJS = "packages/js/app/src/module.mjs"
_TS = "packages/js/app/src/types.ts"
_RS = "crates/demo/src/lib.rs"

# One reference for each form the doc may use; prose spans such as
# `vue.md`, `:class` and `Component.js` are not references.
_GOOD_REFERENCES = f"""\
`pkg/mod.py:LIMIT`, `pkg/mod.py:third`, `pkg/mod.py:Checker.check`, `pkg/mod.py:Checker.mode`,
`pkg/mod.py:make_component.Inner.on_render`, `pkg/mod.py:fallback`, `pkg/mod.py`,
`{_JS}:startApp`, `{_JS}:ids`, `{_JS}:Store`, `{_JS}:settings`, `{_JS}:pending`, `{_JS}:legacy`,
`{_JS}:ambient`, `{_JS}:Level`, `{_JS}:Util`, `{_JS}:startApp.host`, `{_JS}:startApp.host.preflight`,
`{_JS}:startApp.host.mode`, `{_JS}:Store.load`, `{_JS}:Store.size`, `{_JS}:Store.extent`, `{_JS}:Store.secret`,
`{_JS}:Store.maybe`, `{_JS}:Store.limit`, `{_JS}:Store.hooks`, `{_JS}:Store.entries`, `{_JS}:Store.generic`,
`{_JS}:Store.render`, `{_JS}:Store.create`, `{_JS}:Store.guard`, `{_JS}:pageNonce`, `{_MJS}:fromModule`,
`{_TS}:makeTarget`, `{_TS}:Options`, `{_TS}:Shape`, `{_TS}:Shape.area`, `{_TS}:Shape.label`, `{_TS}:Base.measure`,
`{_RS}:Writer`, `{_RS}:Writer::element`, `{_RS}:Writer::fmt`, `{_RS}:Id::from`, `{_RS}:Pair::swap`,
`{_RS}:Handle::send_all`, `{_RS}:Render::render`, `{_RS}:escape_text`, `{_RS}:fetch`, `{_RS}:limit_fn`,
`{_RS}:send_all`, `{_RS}:GLOBAL`, `{_RS}:Bits`, `{_RS}:Mode`, `{_RS}:LIMIT`, `{_RS}:Alias`, `{_RS}:tests`,
`crates/demo/src/grammar.pest:html_attribute`,
`docs/guide.md#guide`, `docs/guide.md#check-c-bind-keys`, `docs/guide.md#stable-anchor`,
`docs/guide.md#see-the-api-now`, `docs/guide.md#limits-1`, `docs/guide.md#notes--see-x-`,
`ROOT.md#root-heading`, `ROOT.md`, `vue.md`, `:class`, `Component.js`, `example.com:8000`, `pkg/mod.py`, `conftest.py`,
and ``- `x` `` in a double-backtick span.
"""


def _doc(references: str, short_forms: str = _SHORT_FORMS) -> str:
    return f"# Doc\n\n{short_forms}\n{references}"


def _repository(tmp_path: Path, references: str = _GOOD_REFERENCES, *, short_forms: str = _SHORT_FORMS) -> Path:
    files = {str(trust_boundary_refs.DOC): _doc(references, short_forms), **_FILES}
    for relative, text in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def test_a_doc_whose_references_all_resolve_passes(tmp_path: Path) -> None:
    assert trust_boundary_refs.check(_repository(tmp_path)) == []


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        # Python names resolve from the module down, through classes and functions.
        ("`pkg/mod.py:missing`", "`missing` is not defined in pkg/mod.py; find where it moved"),
        ("`pkg/mod.py:Checker.missing`", "`missing` is not defined in `Checker` in pkg/mod.py"),
        ("`pkg/mod.py:helper`", "`helper` is not defined in pkg/mod.py"),
        ("`pkg/mod.py:Checker.check.local`", "`local` is not defined in `Checker.check`"),
        ("`pkg/mod.py:LIMIT.real`", "`LIMIT` in pkg/mod.py is a value"),
        ("`pkg/mod.py:check()`", "`check()` is not a symbol name"),
        # JavaScript and TypeScript: each part of the name must be defined
        # somewhere in the file; a name in a comment, in a string, or in a
        # call statement is not a definition.
        (f"`{_JS}:startApp.hots`", "`hots` is not defined in packages/js/app/src/runtime.js; find where it moved"),
        (f"`{_JS}:startApps.host`", "`startApps` is not defined in packages/js/app/src/runtime.js"),
        (f"`{_JS}:commentOnly`", "`commentOnly` is not defined"),
        (f"`{_JS}:blockCommentOnly`", "`blockCommentOnly` is not defined"),
        (f"`{_JS}:stringOnly`", "`stringOnly` is not defined"),
        (f"`{_JS}:registerCallOnly`", "`registerCallOnly` is not defined"),
        (f"`{_JS}:callbackOnly`", "`callbackOnly` is not defined"),
        (f"`{_JS}:midLineOnly`", "`midLineOnly` is not defined"),
        (f"`{_JS}:x`", "`x` is not defined"),
        (f"`{_JS}:Store.load()`", "`Store.load()` is not a symbol name"),
        (f"`{_TS}:makeTargets`", "`makeTargets` is not defined in packages/js/app/src/types.ts"),
        # Rust: a method needs its type and its own name; a name in a comment
        # is not a definition.
        (f"`{_RS}:Writer::elemnt`", "`elemnt` is not defined in crates/demo/src/lib.rs"),
        (f"`{_RS}:Missing::element`", "`Missing` is not defined in crates/demo/src/lib.rs"),
        (f"`{_RS}:Ghost::element`", "`Ghost` is not defined in crates/demo/src/lib.rs"),
        (f"`{_RS}:missing_fn`", "`missing_fn` is not defined in crates/demo/src/lib.rs"),
        (f"`{_RS}:comment_only`", "`comment_only` is not defined"),
        (f"`{_RS}:Writer.element`", "`Writer.element` is not a symbol name"),
        # Pest: the rule must start a line, and a rule in a comment does not count.
        ("`crates/demo/src/grammar.pest:html_atribute`", "rule `html_atribute` is not defined"),
        ("`crates/demo/src/grammar.pest:comment_rule`", "rule `comment_rule` is not defined"),
        # Markdown anchors: front matter, an HTML comment, and a fenced block
        # hold no headings, and a heading with its own id is cited by that id.
        ("`docs/guide.md#yaml-comment`", "docs/guide.md has no heading with the anchor `#yaml-comment`"),
        ("`docs/guide.md#hidden-heading`", "docs/guide.md has no heading with the anchor `#hidden-heading`"),
        ("`docs/guide.md#not-a-heading`", "docs/guide.md has no heading with the anchor `#not-a-heading`"),
        ("`docs/guide.md#short-title--stable-anchor-`", "cite `docs/guide.md#stable-anchor`"),
        ("`docs/guide.md#x`", "docs/guide.md has no heading with the anchor `#x`"),
        ("`ROOT.md#missing`", "ROOT.md has no heading with the anchor `#missing`"),
        ("`docs/guide.md:Guide`", "cite a Markdown section as `docs/guide.md#heading-anchor`"),
        ("`pkg/mod.py#LIMIT`", "cite code as `pkg/mod.py:Symbol`"),
        # Files: short forms expand, and every path must exist.
        ("`pkg/gone.py:run`", "pkg/gone.py (read as packages/py/pkg/pkg/gone.py) does not exist"),
        ("`pkg/gone.md`", "pkg/gone.md (read as packages/py/pkg/pkg/gone.md) does not exist"),
        ("`mod.py:LIMIT`", "write the file's path from the repository root"),
        ("`pkg/data.yml:key`", "cannot check a symbol in a .yml file; cite the file alone"),
        # A double-backtick span does not hide the reference after it, and a
        # reference may not wrap onto the next line.
        ("`` a`b `` then `pkg/mod.py:NOPE`", "`NOPE` is not defined"),
        ("`pkg/mod.py:Checker.check\nand more`", "keep a reference on one line"),
        # A heading in quotes, or a name beside a path written alone, would
        # pass unchecked, so each must be written as a reference.
        ('`docs/guide.md` ("Guide")', "cannot be checked; cite the section as `path#anchor`"),
        ('`docs/guide.md`, "Guide"', "cannot be checked; cite the section as `path#anchor`"),
        ("`Checker` in `pkg/mod.py`", "cannot be checked; cite the section as `path#anchor` or the function"),
        ("`check` (`pkg/mod.py`)", "cannot be checked"),
        ("`pkg/mod.py`, `check`", "cannot be checked"),
        ("`pkg/mod.py` (`Checker`)", "cannot be checked"),
        ("`Writer` in `crates/demo/src/lib.rs`", "cannot be checked"),
        ("`docs/guide.md` (\u201cGuide\u201d)", "cannot be checked"),
        ("`docs/guide.md` (`limits`)", "cannot be checked"),
        # Line numbers are refused in every form.
        ("`pkg/mod.py:12`", "cites a line number"),
        ("`pkg/mod.py:12-14`", "cites a line number"),
        ("`:12`", "cites a line number"),
        ("`pkg/mod.py:L12`", "cites a line number"),
        ("`pkg/mod.py#L12`", "cites a line number"),
        ("`pkg/mod.py, line 12`", "cites a line number"),
        ("`pkg/mod.py`:12", "`` `pkg/mod.py`:12 `` cites a line number"),
        ("`pkg/mod.py` (lines 12-14)", "cites a line number"),
        ("`pkg/mod.py:LIMIT` (line 12)", "cites a line number"),
        ("`pkg/mod.py` at line 12", "cites a line number"),
        ("see pkg/mod.py:12", "`pkg/mod.py:12` cites a line number"),
    ],
)
def test_a_reference_that_points_at_nothing_is_reported(tmp_path: Path, reference: str, expected: str) -> None:
    root = _repository(tmp_path, _GOOD_REFERENCES + reference + "\n")

    problems = trust_boundary_refs.check(root)

    assert len(problems) == 1, problems
    assert expected in problems[0]
    # Each problem starts with the doc line it is about.
    doc = _doc(_GOOD_REFERENCES + reference)
    line = doc.count("\n", 0, doc.index(reference)) + 1
    assert problems[0].startswith(f"{trust_boundary_refs.DOC}:{line}: ")


def test_a_dotted_name_only_needs_each_part_defined_somewhere_in_the_file(tmp_path: Path) -> None:
    # The accepted limit of the pattern check: `host` is defined inside
    # `startApp`, not in `Store`, and `escape_text` and `helper` are not
    # methods of `Writer`, yet all three pass because each part exists in its
    # file.
    root = _repository(tmp_path, f"`{_JS}:Store.host`, `{_RS}:Writer::escape_text`, `{_RS}:Writer::helper`\n")

    assert trust_boundary_refs.check(root) == []


def test_a_doc_without_the_short_form_list_is_reported_once(tmp_path: Path) -> None:
    # Without the list every short path would be reported as missing.
    root = _repository(tmp_path, short_forms="")

    problems = trust_boundary_refs.check(root)

    assert len(problems) == 1
    assert problems[0].startswith(f"{trust_boundary_refs.DOC}: found no short path forms")


def test_a_stray_backtick_in_one_table_row_does_not_hide_the_next_row(tmp_path: Path) -> None:
    # A code span never runs from one table row into the next, as on GitHub.
    root = _repository(tmp_path, _GOOD_REFERENCES + "| a ` stray |\n| `pkg/mod.py:NOPE` |\n")

    problems = trust_boundary_refs.check(root)

    assert len(problems) == 1
    assert "`NOPE` is not defined" in problems[0]
