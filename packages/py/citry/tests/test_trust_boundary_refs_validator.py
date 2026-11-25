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
  function startApp(root) {
    const pattern = /[}]/g;
    const label = "function stringOnly() }";
    const text = `}${"}"}`;
    const host = {
      preflight(result) {
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
  function outside() {}
})(window);
"""

# The same for the `impl Writer` block: a brace in a char, a string, or a
# raw string would end it before `element`.
_RUST = """\
// fn comment_only() {}
pub struct Writer<'a> {
    text: &'a str,
}

impl<'a> Writer<'a> {
    const OPEN: char = '}';
    const CLOSE: &'static str = "}";
    const RAW: &'static str = r#"} fn raw_only() {"#;

    pub fn element(&mut self) -> &'a str {
        self.text
    }
}

impl std::fmt::Display for Writer<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        Ok(())
    }
}

pub fn escape_text(text: &str) -> String {
    text.to_owned()
}
"""

_PEST = """\
// comment_rule = { "x" }
html_attribute = { name ~ "=" ~ value }
"""

_MARKDOWN = """\
---
title: Guide
---
# Guide

## Check `c-bind` keys

## Short title { #stable-anchor }

## Limits

## Limits

```md
## Not a heading
```
"""

_FILES = {
    "packages/py/pkg/pkg/mod.py": _PYTHON,
    "packages/py/pkg/pkg/data.yml": "key: value\n",
    "packages/js/app/src/runtime.js": _JAVASCRIPT,
    "crates/demo/src/lib.rs": _RUST,
    "crates/demo/src/grammar.pest": _PEST,
    "docs_site/content/guide.md": _MARKDOWN,
}

# One reference for each form the doc may use; prose spans such as
# `vue.md`, `:class` and `Component.js` are not references.
_GOOD_REFERENCES = """\
`pkg/mod.py:LIMIT`, `pkg/mod.py:Checker.check`, `pkg/mod.py:Checker.mode`,
`pkg/mod.py:make_component.Inner.on_render`, `pkg/mod.py:fallback`, `pkg/mod.py`,
`packages/js/app/src/runtime.js:startApp.host.preflight`, `packages/js/app/src/runtime.js:settings.setup`,
`packages/js/app/src/runtime.js:Store.load`, `packages/js/app/src/runtime.js:pageNonce`,
`crates/demo/src/lib.rs:Writer`, `crates/demo/src/lib.rs:Writer::element`, `crates/demo/src/lib.rs:Writer::fmt`,
`crates/demo/src/lib.rs:escape_text`, `crates/demo/src/grammar.pest:html_attribute`,
`docs/guide.md#guide`, `docs/guide.md#check-c-bind-keys`, `docs/guide.md#stable-anchor`, `docs/guide.md#limits-1`,
`vue.md`, `:class`, `Component.js`.
"""


def _repository(tmp_path: Path, references: str = _GOOD_REFERENCES, *, short_forms: str = _SHORT_FORMS) -> Path:
    files = {str(trust_boundary_refs.DOC): f"# Doc\n\n{short_forms}\n{references}", **_FILES}
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
        ("`pkg/mod.py:missing`", "`missing` is no longer defined in pkg/mod.py; find where it moved"),
        ("`pkg/mod.py:Checker.missing`", "`missing` is no longer defined in `Checker` in pkg/mod.py"),
        ("`pkg/mod.py:helper`", "`helper` is no longer defined in pkg/mod.py"),
        ("`pkg/mod.py:Checker.check.local`", "`local` is no longer defined in `Checker.check`"),
        ("`pkg/mod.py:LIMIT.real`", "`LIMIT` in pkg/mod.py is a value"),
        # A JavaScript name in a comment or a string is not a definition,
        # and a later name must sit inside the earlier one's body.
        ("`packages/js/app/src/runtime.js:commentOnly`", "`commentOnly` is no longer defined"),
        ("`packages/js/app/src/runtime.js:stringOnly`", "`stringOnly` is no longer defined"),
        ("`packages/js/app/src/runtime.js:Store.preflight`", "`preflight` is no longer defined in `Store`"),
        # Rust methods need their type, and only the type's own blocks count.
        ("`crates/demo/src/lib.rs:element`", "cite it as `Type::element`"),
        ("`crates/demo/src/lib.rs:Other::element`", "has no `impl` or `trait` block for `Other`"),
        ("`crates/demo/src/lib.rs:Writer::escape_text`", "`escape_text` is no longer defined in an `impl`"),
        ("`crates/demo/src/lib.rs:raw_only`", "`raw_only` is no longer defined"),
        ("`crates/demo/src/lib.rs:comment_only`", "`comment_only` is no longer defined"),
        ("`crates/demo/src/lib.rs:Writer.element`", "write the symbol as `name` or `Type::method`"),
        ("`crates/demo/src/grammar.pest:comment_rule`", "rule `comment_rule` is no longer defined"),
        # Markdown anchors: a fenced `#` line is not a heading, and a
        # heading with its own id is cited by that id.
        ("`docs/guide.md#not-a-heading`", "docs/guide.md has no heading with the anchor `#not-a-heading`"),
        ("`docs/guide.md#short-title--stable-anchor-`", "cite `docs/guide.md#stable-anchor`"),
        ("`docs/guide.md:Guide`", "cite a Markdown section as `docs/guide.md#heading-anchor`"),
        ("`pkg/mod.py#LIMIT`", "cite code as `pkg/mod.py:Symbol`"),
        # Files: short forms expand, and every path must exist.
        ("`pkg/gone.py:run`", "pkg/gone.py (read as packages/py/pkg/pkg/gone.py) does not exist"),
        ("`pkg/gone.md`", "pkg/gone.md (read as packages/py/pkg/pkg/gone.md) does not exist"),
        ("`mod.py:LIMIT`", "write the file's path from the repository root"),
        ("`pkg/data.yml:key`", "cannot check a symbol in a .yml file; cite the file alone"),
        # Line numbers are refused in every form.
        ("`pkg/mod.py:12`", "cites a line number"),
        ("`pkg/mod.py:12-14`", "cites a line number"),
        ("`:12`", "cites a line number"),
        ("see pkg/mod.py:12", "outside a code span cites a line number"),
    ],
)
def test_a_reference_that_points_at_nothing_is_reported(tmp_path: Path, reference: str, expected: str) -> None:
    root = _repository(tmp_path, _GOOD_REFERENCES + reference + "\n")

    problems = trust_boundary_refs.check(root)

    assert len(problems) == 1, problems
    assert expected in problems[0]
    # Each problem names the doc line and the reference it is about.
    assert problems[0].startswith(f"{trust_boundary_refs.DOC}:{_GOOD_REFERENCES.count(chr(10)) + 6}: ")


def test_a_doc_without_the_short_form_list_is_reported_once(tmp_path: Path) -> None:
    # Without the list every short path would be reported as missing.
    root = _repository(tmp_path, short_forms="")

    problems = trust_boundary_refs.check(root)

    assert len(problems) == 1
    assert problems[0].startswith(f"{trust_boundary_refs.DOC}: found no short path forms")
