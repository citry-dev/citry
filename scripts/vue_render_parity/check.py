"""
Compare the server's hydration HTML with Vue's own server rendering.

When a page hydrates, the server writes the HTML inside the Vue host (the
`div` Vue mounts into) by running each
compiled render function in Rust (`crates/citry_vue_compiler/src/
server_render.rs`) over the manifest the browser receives. Vue then adopts
that HTML, so it must be what Vue itself renders from the same code and
data. This check runs every page the non-browser Python tests and the
benchmark board's server tests prepare through both renderers and compares
the results:

1. `collect.py` (a pytest plugin) records each prepared page while the test
   suite runs: its manifest, component tags and compiled definitions.
2. This script reads each page's render functions into Rust programs and
   runs them with `citry_core._rust.vue._render_for_hydration`, the call the
   server makes, with the page-size threshold at 0.
3. `render.mjs` renders the same page with Vue 3.5.42's `renderToString`
   from the client package's `node_modules`, running each definition's
   browser JavaScript.
4. The two HTML strings are compared token by token (see `compare`).

A page the Rust renderer declines as a whole (it mounts in the browser) is
counted as declined, not compared. Inside a compared page, an element the
Rust renderer wrote as a shell (`data-allow-mismatch="children"`, contents
left to the browser) is compared by its own tag and attributes only; the
Citry HTML it carries until the browser runtime removes it is not compared.

Run from the repository root after `pnpm install` and a native build:

    .venv/bin/python scripts/vue_render_parity/check.py            # collect + compare
    .venv/bin/python scripts/vue_render_parity/check.py --reuse    # compare the last corpus

Collection runs the non-browser test suite once with the recorder plugin
(about the cost of the `fast` pytest profile); pass extra pytest arguments
after `--` to narrow it. The exit status is 1 when any compared page
differs or Vue fails to render a page Rust wrote.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from citry_core import _rust

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DEFAULT_CORPUS = ROOT / ".vue-render-parity"

# The pytest runs whose pages form the corpus: the default test paths
# without browser tests (the selection CI's pytest job uses), then the
# benchmark board app's server tests when this checkout has them. The board
# configures Django for its whole process, so it runs on its own.
BOARD_APP_TESTS = ROOT / "benchmarks/web/apps/citry_vue/test_app.py"
DEFAULT_RUNS = [
    ["-m", "not e2e", "-n", "4", "--dist", "loadfile"],
    *([[str(BOARD_APP_TESTS.relative_to(ROOT))]] if BOARD_APP_TESTS.is_file() else []),
]

VOID_TAGS = frozenset(
    ["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"]
)
SHELL_MARKER = "data-allow-mismatch"
PATCHED_MARKER = "data-citry-parity-patched"
SHOW_MARKER = "data-citry-parity-show"
TEXT_MARKER = "data-citry-parity-text"


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------


class _Tokens(HTMLParser):
    """Split HTML into start, end, text and comment tokens, without repairing the tree."""

    def __init__(self) -> None:
        # Character references are decoded, so `&quot;` and `"` compare equal.
        super().__init__(convert_charrefs=True)
        self.tokens: list[tuple[Any, ...]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # A valueless attribute (`checked`) and an empty one (`checked=""`)
        # are the same to the browser, which also keeps the first of two
        # attributes with one name.
        values: dict[str, str] = {}
        for name, value in attrs:
            values.setdefault(name, value or "")
        self.tokens.append(("start", tag, values))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # The browser ignores `/>` on a non-void element and leaves it open,
        # so no end token is added.
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag not in VOID_TAGS:
            self.tokens.append(("end", tag))

    def handle_data(self, data: str) -> None:
        # Adjacent text vnodes are written back to back; the parser reads
        # them as one text either way.
        if self.tokens and self.tokens[-1][0] == "text":
            self.tokens[-1] = ("text", self.tokens[-1][1] + data)
        else:
            self.tokens.append(("text", data))

    def handle_comment(self, data: str) -> None:
        self.tokens.append(("comment", data))


class _ShellContents(HTMLParser):
    """Find the contents of each shell element in the Rust HTML, as byte ranges."""

    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=False)
        self.line_starts = [0, *(match.end() for match in re.finditer("\n", html))]
        self.ranges: list[tuple[int, int]] = []
        self.depth = 0
        self.start = 0

    def position(self) -> int:
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in VOID_TAGS:
            return
        if self.depth:
            self.depth += 1
        elif dict(attrs).get(SHELL_MARKER) == "children":
            self.depth = 1
            self.start = self.position() + len(self.get_starttag_text() or "")

    def handle_endtag(self, tag: str) -> None:
        if self.depth and tag not in VOID_TAGS:
            self.depth -= 1
            if not self.depth:
                self.ranges.append((self.start, self.position()))


def without_shell_contents(html: str) -> str:
    """
    Remove what the Rust side wrote inside each shell.

    That is Citry's HTML for the shell's contents, shown only until the
    browser runtime removes it right before Vue hydrates, so it is never
    compared with Vue's render.
    """
    finder = _ShellContents(html)
    finder.feed(html)
    finder.close()
    output, position = [], 0
    for start, end in finder.ranges:
        output.append(html[position:start])
        position = end
    output.append(html[position:])
    return "".join(output)


def tokens(html: str) -> list[tuple[Any, ...]]:
    parser = _Tokens()
    parser.feed(html)
    parser.close()
    return parser.tokens


def style_declarations(value: str) -> list[tuple[str, str]]:
    """Split a style attribute into (property, value) pairs, ignoring spacing."""
    output = []
    for part in value.split(";"):
        name, _, text = part.partition(":")
        if name.strip():
            output.append((name.strip().lower(), " ".join(text.split())))
    return output


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


@dataclass
class Outcome:
    shells: int = 0
    # Elements compared, and elements of Vue's output skipped inside shells.
    elements: int = 0
    skipped: int = 0
    # Attributes Vue wrote that the Rust side left for hydration to set.
    left_to_hydration: Counter[str] = field(default_factory=Counter)
    mismatch: str | None = None


def compare_attributes(tag: str, rust: dict[str, str], vue: dict[str, str], outcome: Outcome) -> str | None:
    vue = dict(vue)
    patched = set(json.loads(vue.pop(PATCHED_MARKER, "[]")))
    shows = vue.pop(SHOW_MARKER, None) is not None
    vue.pop(TEXT_MARKER, None)
    for name in sorted(set(rust) | set(vue)):
        if name in rust and name in vue:
            same = (
                style_declarations(rust[name]) == style_declarations(vue[name])
                if name == "style"
                else rust[name] == vue[name]
            )
            if same:
                continue
            if name == "style" and shows:
                # `v-show` sets `display` while hydrating, so the Rust side
                # may leave it out, but a `display` it did write must match.
                rust_style = style_declarations(rust[name])
                strip = [item for item in style_declarations(vue[name]) if item[0] != "display"]
                if all(item[0] != "display" for item in rust_style) and strip == rust_style:
                    outcome.left_to_hydration["style (v-show display)"] += 1
                    continue
            return f"<{tag}> attribute {name}: rust={rust[name]!r} vue={vue[name]!r}"
        if name in vue:
            # Vue's server renderer writes `class=""`/`style=""` for a null
            # value, where the client's `patchProp` removes the attribute.
            # The Rust side follows the client.
            if name in {"class", "style"} and vue[name].strip() == "":
                continue
            if name in patched:
                outcome.left_to_hydration[name] += 1
                continue
            if name == "style" and shows and all(item[0] == "display" for item in style_declarations(vue[name])):
                outcome.left_to_hydration["style (v-show display)"] += 1
                continue
            return f"<{tag}> attribute {name}: rust=<absent> vue={vue[name]!r}"
        return f"<{tag}> attribute {name}: rust={rust[name]!r} vue=<absent>"
    return None


def _context(items: list[tuple[Any, ...]], index: int) -> str:
    def show(token: tuple[Any, ...]) -> str:
        kind = token[0]
        if kind == "start":
            attrs = "".join(
                f" {name}={value!r}"
                for name, value in token[2].items()
                if name not in {PATCHED_MARKER, SHOW_MARKER, TEXT_MARKER}
            )
            return f"<{token[1]}{attrs}>"
        if kind == "end":
            return f"</{token[1]}>"
        if kind == "comment":
            return f"<!--{token[1]}-->"
        return repr(token[1])

    return " ".join(show(token) for token in items[max(0, index - 4) : index + 3])


def compare(rust_html: str, vue_html: str) -> Outcome:
    """
    Walk both token lists together; return the first difference, if any.

    Rules, each matching a place where the two renderers may differ without
    the browser seeing a different page:

    - character references are decoded and adjacent text is joined;
    - a valueless attribute equals the same attribute with an empty value;
    - `style` values compare as declaration lists (spacing is not kept by
      style texts that differ only in spacing give the same declarations);
    - an empty `class` or `style` from Vue's server renderer equals no
      attribute (the client removes a null class or style);
    - an attribute Vue sets again while hydrating (the render lists it as
      dynamic, a `value` on input or option, any key of a custom element)
      may be missing on the Rust side, as may `display` under `v-show`;
    - an element whose only content is `v-text` may be empty on the Rust
      side (hydration sets its text), but text it wrote must match;
    - a Rust shell element skips Vue's contents for that element.
    """
    outcome = Outcome()
    rust = tokens(rust_html)
    vue = tokens(vue_html)
    i = j = 0
    while i < len(rust) and j < len(vue):
        r, v = rust[i], vue[j]
        if r[0] != v[0] or (r[0] in {"start", "end"} and r[1] != v[1]):
            outcome.mismatch = f"rust: {_context(rust, i)}\n      vue:  {_context(vue, j)}"
            return outcome
        if r[0] == "start":
            rust_attrs = dict(r[2])
            shell = rust_attrs.pop(SHELL_MARKER, None) == "children"
            outcome.elements += 1
            problem = compare_attributes(r[1], rust_attrs, v[2], outcome)
            if problem is not None:
                outcome.mismatch = f"{problem}\n      rust: {_context(rust, i)}\n      vue:  {_context(vue, j)}"
                return outcome
            if (
                not shell
                and TEXT_MARKER in v[2]
                and i + 1 < len(rust)
                and rust[i + 1] == ("end", r[1])
                and j + 2 < len(vue)
                and vue[j + 1][0] == "text"
                and vue[j + 2] == ("end", r[1])
            ):
                # The Rust side left the `v-text` for hydration to set, so
                # Vue's text for this element is skipped.
                outcome.left_to_hydration["textContent (v-text)"] += 1
                j += 1
            if shell and r[1] not in VOID_TAGS:
                outcome.shells += 1
                # Skip Vue's contents up to this element's end tag.
                depth = 1
                j += 1
                while j < len(vue) and depth:
                    token = vue[j]
                    if token[0] == "start":
                        outcome.skipped += 1
                        depth += 0 if token[1] in VOID_TAGS else 1
                    elif token[0] == "end":
                        depth -= 1
                    j += 1
                if depth:
                    outcome.mismatch = f"Vue's contents for shell <{r[1]}> never close"
                    return outcome
                j -= 1
                i += 1
                if i >= len(rust) or rust[i] != ("end", r[1]):
                    outcome.mismatch = f"shell <{r[1]}> is not empty"
                    return outcome
        elif r[0] in {"text", "comment"} and r[1] != v[1]:
            outcome.mismatch = f"rust: {_context(rust, i)}\n      vue:  {_context(vue, j)}"
            return outcome
        i += 1
        j += 1
    if i < len(rust) or j < len(vue):
        outcome.mismatch = f"length: rust: {_context(rust, i)}\n      vue:  {_context(vue, j)}"
    return outcome


def mutations(html: str, vue_html: str) -> list[tuple[str, str]]:
    """
    Return small wrong variants of the Rust HTML that `compare` must reject.

    Every run checks the comparison itself this way, so a rule that grows
    too lenient (or a walk that stops early) fails the check instead of
    reporting a clean result.
    """
    variants = []
    anchor = html.find("<!--[-->")
    if anchor >= 0:
        variants.append(("drop a Fragment anchor", html[:anchor] + html[anchor + len("<!--[-->") :]))
    attribute = re.search(r'\s[a-z][a-z0-9-]*="', html)
    if attribute is not None and not html[attribute.start() :].startswith(f' {SHELL_MARKER}="'):
        at = attribute.end()
        variants.append(("change an attribute value", html[:at] + "parity-mutation " + html[at:]))
    text = re.search(r">([^<]*\S[^<]*)<", html)
    if text is not None:
        at = text.end(1)
        variants.append(("change a text", html[:at] + "!" + html[at:]))
    # The allowances for attributes Vue sets while hydrating must not hide
    # an attribute the Rust side wrote and then lost, or a `display` added.
    # Only a name Vue never sets while hydrating on this page must be kept.
    patched = {
        name
        for token in tokens(vue_html)
        if token[0] == "start"
        for name in json.loads(token[2].get(PATCHED_MARKER, "[]"))
    }
    written = next(
        (
            match
            for match in re.finditer(r'\s([a-z][a-z0-9-]*)="[^"]*"', html)
            if match.group(1) not in patched and match.group(1) != SHELL_MARKER
        ),
        None,
    )
    if written is not None:
        variants.append(("drop a written attribute", html[: written.start()] + html[written.end() :]))
    tag = re.search(r"<([a-z][a-z0-9]*)(?=[\s>])", html)
    if tag is not None and ' style="' not in html[tag.start() : html.find(">", tag.start())]:
        at = tag.end()
        variants.append(("add display: none", html[:at] + ' style="display: none;"' + html[at:]))
    return variants


# ---------------------------------------------------------------------------
# Running both renderers
# ---------------------------------------------------------------------------


def load_corpus(corpus: Path) -> list[dict[str, Any]]:
    pages: dict[str, dict[str, Any]] = {}
    for path in sorted(corpus.glob("corpus-*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            page = json.loads(line)
            if '"rootId"' in page["manifest"]:
                pages.setdefault(page["digest"], page)
    return list(pages.values())


# Pages where the token check and the full parse disagreed (see rust_render).
check_disagreements: list[dict[str, Any]] = []


def rust_render(page: dict[str, Any], programs_cache: dict[str, Any]) -> tuple[str | None, str | None, list[Any]]:
    programs = {}
    for definition_id, definition in page["definitions"].items():
        if definition_id not in programs_cache:
            try:
                programs_cache[definition_id] = _rust.vue._read_server_render_program(
                    definition["code"] or "", definition["dynamicElements"]
                )
            except ValueError:
                # Production drops a definition it cannot read; its
                # occurrences are then declined like any unknown part.
                programs_cache[definition_id] = None
        if programs_cache[definition_id] is not None:
            programs[definition_id] = programs_cache[definition_id]
    result = _rust.vue._render_for_hydration(programs, page["manifest"], page["tags"], 0)
    # Production first checks the written tokens against stored parser
    # answers and parses the whole HTML only when that check cannot decide.
    # Parsing every page as well shows the two checks agree on this corpus.
    if result != _rust.vue._render_for_hydration(programs, page["manifest"], page["tags"], 0, full_parse_check=True):
        check_disagreements.append(page)
    html, _count, _shells, declines, reason = result
    return html, reason, declines


def vue_render(pages: list[dict[str, Any]]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        pages_path = Path(directory) / "pages.json"
        results_path = Path(directory) / "results.json"
        pages_path.write_text(
            json.dumps([{key: page[key] for key in ("digest", "manifest", "tags", "definitions")} for page in pages]),
            encoding="utf-8",
        )
        # Node comes from PATH, as `pnpm` does for the check gate.
        command = ["node", str(HERE / "render.mjs"), str(pages_path), str(results_path)]
        subprocess.run(command, check=True)
        return json.loads(results_path.read_text(encoding="utf-8"))


def collect(corpus: Path, pytest_args: list[str]) -> None:
    for old in corpus.glob("corpus-*.jsonl"):
        old.unlink()
    for run in [pytest_args] if pytest_args else DEFAULT_RUNS:
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            "scripts.vue_render_parity.collect",
            f"--vue-render-parity-corpus={corpus}",
            *run,
        ]
        # A failing test does not invalidate the pages other tests recorded,
        # so the exit status is not checked here.
        subprocess.run(command, cwd=ROOT, check=False)


def say(line: str) -> None:
    sys.stdout.write(line + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS, help="directory holding corpus-*.jsonl")
    parser.add_argument("--reuse", action="store_true", help="compare the existing corpus without running pytest")
    parser.add_argument("--report", type=Path, help="write every page's result as JSON here")
    parser.add_argument("pytest_args", nargs="*", help="pytest arguments for collection (after --)")
    args = parser.parse_args()
    if not args.reuse:
        collect(args.corpus, args.pytest_args)
    pages = load_corpus(args.corpus)
    if not pages:
        sys.stderr.write("no pages recorded\n")
        return 1

    programs_cache: dict[str, Any] = {}
    written = []
    declined: Counter[str] = Counter()
    decline_codes: Counter[str] = Counter()
    report: list[dict[str, Any]] = []
    # A page prepared without the compiled definitions the serializer builds
    # before delivery (`early_selected_tree`), such as a plugin payload test,
    # has no programs to run; the server only writes hydration HTML when
    # that tree exists.
    no_definitions = [page for page in pages if page["missingDefinitions"]]
    for page in pages:
        if page["missingDefinitions"]:
            continue
        html, reason, declines = rust_render(page, programs_cache)
        for code, _detail, _component, _shell, _content in declines:
            decline_codes[code] += 1
        if html is None:
            declined[reason or "unknown"] += 1
            report.append({"digest": page["digest"], "test": page["test"], "declined": reason, "declines": declines})
        else:
            written.append((page, html, declines))

    vue = vue_render([page for page, _html, _declines in written])
    mismatches = []
    vue_errors = []
    shells = elements = skipped = 0
    # Pages where Vue read a browser-only value but the Rust side declined
    # nothing. Usually the value feeds a key Vue sets while hydrating (a
    # dynamic key, `v-text`, `v-show`) or a listener, which the server leaves
    # out; a Rust read of a browser-only value that happened to give the same
    # HTML would also land here, so the list is printed for a person to read.
    unexplained_reads = []
    left: Counter[str] = Counter()
    mutations_tried = 0
    undetected = []
    for page, html, declines in written:
        result = vue["results"][page["digest"]]
        entry: dict[str, Any] = {"digest": page["digest"], "test": page["test"], "rust": html, "declines": declines}
        if "error" in result:
            vue_errors.append((page, result["error"]))
            entry["vueError"] = result["error"]
        else:
            rust_html = without_shell_contents(html)
            outcome = compare(rust_html, result["html"])
            shells += outcome.shells
            elements += outcome.elements
            skipped += outcome.skipped
            left.update(outcome.left_to_hydration)
            if outcome.mismatch is None:
                for name, variant in mutations(rust_html, result["html"]):
                    mutations_tried += 1
                    if compare(variant, result["html"]).mismatch is None:
                        undetected.append((page, name))
            if result.get("browserReads") and not declines:
                unexplained_reads.append(page)
            entry["vue"] = result["html"]
            entry["mismatch"] = outcome.mismatch
            if outcome.mismatch is not None:
                mismatches.append((page, outcome.mismatch))
        report.append(entry)
    if args.report:
        args.report.write_text(json.dumps(report, indent=1), encoding="utf-8")

    definitions = {definition_id for page in pages for definition_id in page["definitions"]}
    unread = sum(1 for program in programs_cache.values() if program is None)
    partly = sum(1 for program in programs_cache.values() if program is not None and not program.fully_supported)
    say(f"Vue {vue['vue']}: {len(pages)} pages, {len(definitions)} compiled render functions")
    say(f"  render functions the Rust reader declined: {unread}; read with unsupported parts: {partly}")
    say(f"  pages recorded without compiled definitions, skipped: {len(no_definitions)}")
    say(f"  pages declined as a whole (mount in the browser): {sum(declined.values())} {dict(declined)}")
    say(f"  pages compared: {len(written) - len(vue_errors)}, shells inside them: {shells}")
    say(f"  elements compared: {elements}; elements of Vue's output inside shells, not compared: {skipped}")
    say(f"  attributes left for hydration to set: {dict(left)}")
    say(f"  decline reasons (pages and shells): {dict(decline_codes.most_common())}")
    for page, error in vue_errors:
        say(f"VUE ERROR {page['test']}: {error}")
    for page, mismatch in mismatches:
        say(f"MISMATCH {page['test']} ({page['digest'][:12]})\n      {mismatch}")
    for page, name in undetected:
        say(f"COMPARISON TOO LENIENT {page['test']} ({page['digest'][:12]}): {name} was not reported")
    say(f"  wrong variants of the Rust HTML rejected: {mutations_tried - len(undetected)}/{mutations_tried}")
    for page in unexplained_reads:
        say(f"NOTE {page['test']} ({page['digest'][:12]}): Vue read a browser-only value, Rust declined nothing")
    # A page whose written HTML the browser would parse differently is a
    # renderer defect, not a supported decline.
    unparsed = declined.get("browser-structure", 0)
    compared = len(written) - len(vue_errors)
    say(f"  mismatches: {len(mismatches)}, Vue errors: {len(vue_errors)}, parse-check failures: {unparsed}")
    for page in check_disagreements:
        say(f"PARSE CHECKS DISAGREE {page['test']} ({page['digest'][:12]}): token check and full parse differ")
    say(f"  pages where the token check and the full parse disagree: {len(check_disagreements)}")
    if compared == 0:
        say("FAIL no page was compared")
    failed = mismatches or vue_errors or undetected or unparsed or check_disagreements or compared == 0
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
