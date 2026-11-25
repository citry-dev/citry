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

# A brace inside a regex, a string, or a template would close `startApp`
# early if it were read as code, and then `host` would not be found in it.
_JAVASCRIPT = """\
/* function commentOnly() {} */
(function (global) {
  "use strict";
  const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  function startApp(root) {
    const localOnly = 1;
    const pattern = /[}]/g;
    const label = "function stringOnly() }";
    const text = `}${"}"}`;
    function matches(value) {
      return /}/.test(value);
    }
    if (root) {
      const fallback = () => null;
    }
    const host = {
      preflight(result) {
        const nested = { deepKey: 1 };
        return result;
      },
    };
    return host;
  }
  const settings = Object.freeze({
    setup(props) { return props; },
  });
  class Store { load() { return 1; } }
  Object.defineProperty(global, "pageNonce", { value: () => null });
  const helper = (value) => {
    const inner = value;
  };
  const load = async ({ id }) => {
    const step = id;
  };
  const LIMIT_JS = 3;
  function later() {
    const deep = 1;
  }
  function collect(items) {
    items.forEach((item) => {
      const seen = item;
    });
  }
})(window);
"""

# TypeScript: a return type with braces, an object type in a parameter or
# a type alias, a class field holding an arrow function, `let` with no
# value, the second name of one `const`, an object whose properties sit
# side by side, and a block under a `switch` label.
_TYPESCRIPT = """\
export function makeTarget(input: string): { ok: boolean } {
  const target = { ok: input.length > 0 };
  return target;
}
export function configure(opts: { nonce: string }, second: number): void {
  const applied = opts.nonce;
}
type Options = { secret: string };
export class Widget {
  handler: Handler = (event) => {
    const local = event;
  };
}
let pending;
const FIRST = 1, SECOND = 2;
const settings = {
  mode: 1,
  load() { const sibling = 1; },
};
switch (FIRST) {
  default: {
    const fromDefault = 1;
  }
}
"""

# The same for the `impl Writer` block: a brace in a char, a string, or a
# raw string would end it before `element`.
_RUST = """\
// fn comment_only() {}
/* outer /* nested */ fn nested_comment_only() {} */
pub struct Writer<'a> {
    text: &'a str,
}
pub struct Other;
pub struct Id(u8);
pub struct Wrap<F>(F);

impl<'a> Writer<'a> {
    const OPEN: char = '}';
    const CLOSE: &'static str = "}";
    const RAW: &'static str = r#"say "}" fn raw_only() {"#;

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

impl<'s, 'a> IntoIterator for &'s Writer<'a> {
    type Item = char;
    type IntoIter = std::vec::IntoIter<char>;
    fn into_iter(self) -> Self::IntoIter {
        Vec::new().into_iter()
    }
}

impl From<[u8; 1]> for Id {
    fn from(bytes: [u8; 1]) -> Self {
        Id(bytes[0])
    }
}

impl<F: Fn() -> u8> Wrap<F> {
    fn call(&self) -> u8 {
        (self.0)()
    }
}

impl Other {
    pub fn other_method(&self) {}
}

pub fn escape_text(text: &str) -> String {
    fn local_helper() {}
    text.to_owned()
}

pub trait Render {
    fn render(&self);
}

mod tests {
    struct Other;

    impl Other {
        fn only_in_tests(&self) {}
    }

    fn test_helper() {}
}
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
    "packages/js/app/src/types.ts": _TYPESCRIPT,
    "crates/demo/src/lib.rs": _RUST,
    "crates/demo/src/grammar.pest": _PEST,
    "docs_site/content/guide.md": _MARKDOWN,
}

_JS = "packages/js/app/src/runtime.js"
_TS = "packages/js/app/src/types.ts"
_RS = "crates/demo/src/lib.rs"

# One reference for each form the doc may use; prose spans such as
# `vue.md`, `:class` and `Component.js` are not references.
_GOOD_REFERENCES = f"""\
`pkg/mod.py:LIMIT`, `pkg/mod.py:third`, `pkg/mod.py:Checker.check`, `pkg/mod.py:Checker.mode`,
`pkg/mod.py:make_component.Inner.on_render`, `pkg/mod.py:fallback`, `pkg/mod.py`,
`{_JS}:own`, `{_JS}:startApp.host.preflight`, `{_JS}:startApp.fallback`, `{_JS}:startApp.matches`,
`{_JS}:settings.setup`, `{_JS}:Store.load`, `{_JS}:pageNonce`, `{_JS}:helper.inner`, `{_JS}:load.step`,
`{_JS}:later.deep`, `{_JS}:collect.seen`, `{_TS}:makeTarget.target`, `{_TS}:configure.applied`, `{_TS}:Options`,
`{_TS}:Widget.handler.local`, `{_TS}:pending`, `{_TS}:SECOND`, `{_TS}:settings.load.sibling`, `{_TS}:fromDefault`,
`{_RS}:Writer`, `{_RS}:Writer::element`, `{_RS}:Writer::fmt`, `{_RS}:Writer::into_iter`, `{_RS}:Id::from`,
`{_RS}:Wrap::call`, `{_RS}:Other::other_method`, `{_RS}:escape_text`, `{_RS}:Render::render`,
`crates/demo/src/grammar.pest:html_attribute`,
`docs/guide.md#guide`, `docs/guide.md#check-c-bind-keys`, `docs/guide.md#stable-anchor`,
`docs/guide.md#see-the-api-now`, `docs/guide.md#limits-1`, `docs/guide.md#notes--see-x-`,
`ROOT.md#root-heading`, `ROOT.md`, `vue.md`, `:class`, `Component.js`, `example.com:8000`,
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
        # A JavaScript name in a comment or a string is not a definition; a
        # local does not stand for a top-level name; a later name must sit in
        # the body of the one before it, not deeper.
        (f"`{_JS}:commentOnly`", "`commentOnly` is not defined"),
        (f"`{_JS}:stringOnly`", "`stringOnly` is not defined"),
        (f"`{_JS}:localOnly`", "`localOnly` is not defined"),
        (f"`{_JS}:Store.preflight`", "`preflight` is not defined in `Store`"),
        (f"`{_JS}:startApp.preflight`", "`preflight` is not defined in `startApp`"),
        (f"`{_JS}:startApp.host.preflight.deepKey`", "`deepKey` is not defined in `startApp.host.preflight`"),
        (f"`{_JS}:inner`", "`inner` is not defined in packages/js/app/src/runtime.js"),
        (f"`{_JS}:LIMIT_JS.deep`", "`LIMIT_JS` in packages/js/app/src/runtime.js has no body"),
        # TypeScript: a return type, an object type, and a parameter do not
        # move a name to another level, and a keyword is not a definition.
        (f"`{_TS}:target`", "`target` is not defined in packages/js/app/src/types.ts"),
        (f"`{_TS}:nonce`", "`nonce` is not defined in packages/js/app/src/types.ts"),
        (f"`{_TS}:secret`", "`secret` is not defined in packages/js/app/src/types.ts"),
        (f"`{_TS}:second`", "`second` is not defined in packages/js/app/src/types.ts"),
        (f"`{_TS}:Widget.local`", "`local` is not defined in `Widget`"),
        (f"`{_TS}:settings.mode.sibling`", "`settings.mode` in packages/js/app/src/types.ts has no body"),
        (f"`{_TS}:if`", "`if` is not defined"),
        # Rust methods need their type, only the type's own blocks count, and
        # an item inside a function is not a free item.
        (f"`{_RS}:element`", "cite it as `Type::element`"),
        (f"`{_RS}:Missing::element`", "has no `impl` or `trait` block for `Missing`"),
        (f"`{_RS}:Writer::other_method`", "`other_method` is not defined in an `impl` or `trait` block for `Writer`"),
        (f"`{_RS}:Writer::helper`", "`helper` is not defined in an `impl` or `trait` block for `Writer`"),
        (f"`{_RS}:local_helper`", "is defined inside another item"),
        (f"`{_RS}:test_helper`", "is defined inside another item"),
        (f"`{_RS}:Other::only_in_tests`", "`only_in_tests` is not defined in an `impl` or `trait` block for `Other`"),
        (f"`{_RS}:Render::paint`", "`paint` is not defined in an `impl` or `trait` block for `Render`"),
        (f"`{_RS}:raw_only`", "`raw_only` is not defined"),
        (f"`{_RS}:comment_only`", "`comment_only` is not defined"),
        (f"`{_RS}:nested_comment_only`", "`nested_comment_only` is not defined"),
        (f"`{_RS}:Writer.element`", "`Writer.element` is not a symbol name"),
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
