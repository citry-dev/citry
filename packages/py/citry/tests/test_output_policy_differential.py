"""
Compare the Rust output checks with the frozen Python copy of their rules.

Rust runs the strict-CSP and JavaScript-policy rules for `serialize()`
(`citry/_output_policy.py`); `_output_policy_reference.py` keeps the Python
rules it replaced. This test builds pages from a fixed seed, runs every
check in every mode on both sides, and compares everything a caller can
observe: the ordered findings, the warning or error each validator reports,
any exception, the HTML with omit markers removed, and the Vue body check's
answer.

A failure prints the seed and the smallest page that still differs, found
by deleting top-level pieces of the page one at a time.
"""

from __future__ import annotations

import base64
import random
import warnings
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

import pytest

from citry import _output_policy
from citry._csp_validation import _CspRenderValidator
from citry._javascript_policy import _JavascriptPolicy
from citry._output_html import scan_output_html

from ._output_policy_reference import (
    ReferenceCspValidator,
    ReferenceJavascriptPolicy,
    reference_server_copy_passes_csp,
)

if TYPE_CHECKING:
    from collections.abc import Callable

SEED = 274
PAGES = 2000
MARKER = "data-citry-omit-handler-0123abcd"
TRUST_PREFIX = "data-citry-security-feed"
COMPONENT_CLASSES = {"known": "Known", "other": "Other", "": "Empty"}

# ---------------------------------------------------------------------------
# The page generator
# ---------------------------------------------------------------------------

_TAGS = [
    "a", "iframe", "object", "embed", "form", "button", "input", "select", "textarea", "div", "span",
    "section", "svg", "math", "title", "noscript", "template", "table", "p", "script", "style", "link",
]  # fmt: skip
_SCRIPT_TYPES = [
    None, "", "module", "Module ;x", "module;x", " text/javascript ", "TEXT/JavaScript", "application/json",
    "importmap", "speculationrules", "speculationrules;x", "text/plain", "text/javascript;charset=utf-8",
    "text/livescript", "\ttext/x-javascript\n", "&#116;ext/javascript", "&#x6D;odule",
]  # fmt: skip
_ACTIVATION = [
    "v-if", "v-for", "v-show", "v-text", "v-html", "v-show.x", ":hidden", "v-bind:hidden", ":href",
    "v-bind:href", ":href.prop", ":action", ":formaction", ":src", ":value", ":title", "@click",
    "@click.prevent", "v-on", "v-on:click", "v-model", "V-IF", "v-", "@", ":",
]  # fmt: skip
_PLAIN = ["hidden", "form", "value", "name", "title", "id", "class", "type", "media", "rel"]
_EVENTS = ["onclick", "ONLOAD", "on", "onx", "On", "oncommand", "onscrollsnapchange", "o", "onclick\u017f"]
_URL_NAMES = ["href", "src", "action", "formaction", "xlink:href", "data", "HREF"]
_CIDS = ["data-cid-known", "data-cid-other", "data-cid-unknown", "data-cid-", "DATA-CID-KNOWN"]
_CITRY = ["data-citry", "data-citry-manifest", "data-citryx", f"{TRUST_PREFIX}-0", f"{TRUST_PREFIX.upper()}-1"]
_REFERENCES = [
    "&amp;", "&amp", "&ampx;", "&AMP", "&notit;", "&notin;", "&not", "&bogus;", "&#128;", "&#129;",
    "&#159;", "&#xD800;", "&#xdfff;", "&#1;", "&#11;", "&#0;", "&#13;", "&#x110000;", "&#1114111;",
    "&#xFFFE;", "&#x1FFFF;", "&#xFDD0;", "&#;", "&#x;", "&#xg", "&#12a", "&Tab;", "&NewLine;", "&colon;",
    "&NotEqualTilde;", "&acE;", "&" + "a" * 31 + ";", "&" + "b" * 32 + ";", "&" + "c" * 33 + ";",
    "&amp" + "x" * 40 + ";", "&#" + "0" * 20 + "106;", "&#00000000000000000000000000065", "&#x0000006A;",
    "&lt;script&gt;", "&#X73;", "&", "&&amp;",
]  # fmt: skip
_JS_LETTERS = {
    "s": ["s", "S", "\u017f", "&#115;", "&#x73;", "&#0000115;"],
    "i": ["i", "I", "\u0131", "\u0130", "&#105;"],
    "j": ["j", "J", "&#106;", "&#x6a;"],
}


def _javascript_text(rng: random.Random) -> str:
    """`javascript:` hidden behind case, references, and whitespace a browser ignores."""
    prefix = rng.choice(["", " ", "\x00", "&#0;", "\t\n", "&#32;", "&Tab;", "\x01 ", "\u00a0"])
    out = [prefix]
    for letter in "javascript":
        options = _JS_LETTERS.get(letter, [letter, letter.upper(), f"&#{ord(letter)};"])
        out.append(rng.choice(options))
        if rng.random() < 0.15:
            out.append(rng.choice(["\t", "\n", "\r", "&#9;", "&#10;", "&Tab;", "&NewLine;", " ", "\x0b"]))
    out.append(rng.choice([":", "&colon;", "&#58;", ";", "", ":"]))
    out.append(rng.choice(["alert(1)", "", "x"]))
    return "".join(out)


def _document(rng: random.Random, depth: int) -> str:
    """A small HTML document for `srcdoc` and `data:` URLs."""
    pieces = [rng.choice(["<p>hi</p>", "<b>x</b>", "", "text"])]
    roll = rng.random()
    if roll < 0.25:
        pieces.append(f"<script{_script_type_attribute(rng)}>run()</script>")
    elif roll < 0.4:
        pieces.append('<a onclick="x()">a</a>')
    elif roll < 0.55:
        pieces.append(f'<a href="{_javascript_text(rng)}">a</a>')
    elif roll < 0.75 and depth < 6:
        nested = _document(rng, depth + 1)
        if rng.random() < 0.5:
            pieces.append(f'<iframe srcdoc="{_escape(nested, rng)}"></iframe>')
        else:
            pieces.append(f'<iframe src="{_data_url(rng, nested)}"></iframe>')
    elif roll < 0.8:
        pieces.append("<title><script>inert()</script></title>")
    return "".join(pieces)


def _deep_document(rng: random.Random) -> str:
    """Documents nested three to six deep, so the depth limit decides some of them."""
    document = rng.choice(["<p>inert</p>", "<script>run()</script>", "<b>x</b>"])
    for _ in range(rng.randint(3, 6)):
        if rng.random() < 0.5:
            document = f'<iframe srcdoc="{_escape(document, rng)}"></iframe>'
        else:
            document = f'<iframe src="data:text/html,{quote(document)}"></iframe>'
    return document


def _escape(text: str, rng: random.Random | None = None) -> str:
    # A legacy reference without `;`, such as `&lt` or `&ltscript`, still
    # decodes, by its longest known prefix.
    less_than = "&lt;" if rng is None else rng.choice(["&lt;", "&lt;", "&lt", "&LT", "&#60", "&#x3c;"])
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", less_than)


def _data_url(rng: random.Random, document: str) -> str:
    header = rng.choice([
        "data:text/html", "DATA:Text/HTML", " data:text/html", "data:text/html;charset=utf-8",
        "data:text/html ;x", "data:text/plain", "data:", "data:text/htmlx", "\x00data:text/html",
    ])  # fmt: skip
    roll = rng.random()
    if roll < 0.4:
        encoded = base64.b64encode(document.encode()).decode()
        variant = rng.random()
        if variant < 0.15:
            encoded += "="
        elif variant < 0.25:
            encoded = encoded.rstrip("=")
        elif variant < 0.32:
            encoded = encoded[:2] + "!" + encoded[2:]
        elif variant < 0.38:
            encoded = quote(encoded)
        elif variant < 0.42:
            encoded = encoded[:-1] + "%" + encoded[-1:]
        return f"{header};base64,{encoded}"
    if roll < 0.5:
        return f"{header}{rng.choice(['', ';base64'])}"
    if roll < 0.6:
        # Bytes that are not valid UTF-8 decode to U+FFFD, also inside a
        # tag name, where dropping them instead would make a <script>.
        broken = rng.choice(["%ff", "%fe", "%C3%28", "%ed%a0%80", "%F0%9F%98", "%c0%af", "%e2%82"])
        return f"{header},%3Cp%3E{broken}%3C/p%3E%3Cscr{broken}ipt%3Ex()%3C/script%3E{quote(document)}"
    return f"{header},{quote(document, safe=rng.choice(['', '<>/= ']))}%%41%4%zz"


def _script_type_attribute(rng: random.Random) -> str:
    value = rng.choice(_SCRIPT_TYPES)
    if value is None:
        return ""
    if value == "" and rng.random() < 0.5:
        return " type"
    if rng.random() < 0.1:
        return f' type="{value}" TYPE="module"'
    return f' type="{value}"'


def _value(rng: random.Random, name: str, tag: str) -> str:
    lowered = name.lower()
    roll = rng.random()
    if lowered == "srcdoc":
        if roll < 0.15:
            return _escape(_deep_document(rng), rng)
        return _escape(_document(rng, 0), rng) if roll < 0.9 else "&lt;script&gt;" * 2
    if lowered in {"href", "src", "action", "formaction", "xlink:href", "data"}:
        if tag in _DOCUMENT_ATTRIBUTE and roll < 0.45:
            return _data_url(rng, _document(rng, 0))
        if roll < 0.75:
            return _javascript_text(rng)
        if roll < 0.7 and tag in _DOCUMENT_ATTRIBUTE:
            return _data_url(rng, _document(rng, 0))
        return rng.choice(["/next", "", "#", "https://example.com/?a=1&b=2", "&#x6A;"])
    if lowered == "type":
        return rng.choice(["button", "submit", "SUBMIT", "reset", "text", "", "Button", "image", "module"])
    if roll < 0.3:
        return "".join(rng.choice([*_REFERENCES, "x", " ", "\u017f", "\U0001f600", "\x00"]) for _ in range(3))
    return rng.choice(["", "x", "save()", "open", "a b", "1", "\u00e9t\u00e9"])


_DOCUMENT_ATTRIBUTE = {"iframe": ["src", "srcdoc"], "object": ["data"], "embed": ["src"]}


def _attribute(rng: random.Random, tag: str, marker: bool) -> str:
    roll = rng.random()
    if tag in _DOCUMENT_ATTRIBUTE and rng.random() < 0.6:
        # Most of an embedding tag's attributes hold a document.
        name = rng.choice(_DOCUMENT_ATTRIBUTE[tag])
    elif roll < 0.12:
        name = rng.choice(_EVENTS)
    elif roll < 0.32:
        name = rng.choice(_URL_NAMES)
    elif roll < 0.4:
        name = rng.choice(["srcdoc", "SrcDoc"])
    elif roll < 0.58:
        name = rng.choice(_ACTIVATION)
    elif roll < 0.68:
        name = rng.choice(_CIDS)
    elif roll < 0.74:
        name = rng.choice(_CITRY)
    elif roll < 0.8 and marker:
        name = rng.choice([MARKER, MARKER.upper()])
    else:
        name = rng.choice(_PLAIN)
    value = _value(rng, name, tag)
    style = rng.random()
    if style < 0.15:
        return name
    if style < 0.2:
        return f"{name}="
    if style < 0.55:
        return f'{name}="{value.replace(chr(34), "&quot;")}"'
    if style < 0.8:
        return f"{name}='{value.replace(chr(39), '&#39;')}'"
    if value and not any(c in value for c in " \t\n\r\f\"'<>=`"):
        return f"{name}={value}"
    return f'{name} = "{value.replace(chr(34), "")}"'


def _element(rng: random.Random, depth: int, marker: bool) -> str:
    tag = rng.choice(_TAGS)
    count = rng.choice([0, 0, 1, 1, 2, 3, 4])
    attributes = [_attribute(rng, tag, marker) for _ in range(count)]
    if tag == "script" and rng.random() < 0.7:
        attributes.insert(rng.randrange(len(attributes) + 1), _script_type_attribute(rng).strip())
    # No space before an attribute exercises how an omit marker is removed
    # next to its neighbor.
    separators = [rng.choice([" ", " ", "\n", "  ", "\t", ""]) for _ in attributes]
    attrs = "".join(sep + attr if attr else "" for sep, attr in zip(separators, attributes, strict=True))
    start = f"<{tag.upper() if rng.random() < 0.1 else tag}{attrs}{rng.choice(['', '', ' /', '/'])}>"
    if tag in {"script", "style"}:
        body = rng.choice(["run()", "", "a<b", "<!--<script>x</script>-->", "p{}", "</scrip>", "<\\/script>"])
    elif depth < 3:
        body = "".join(_piece(rng, depth + 1, marker) for _ in range(rng.choice([0, 1, 2])))
    else:
        body = "x"
    end = "" if rng.random() < 0.1 else f"</{tag}>"
    return start + body + end


# References that decode to nothing, or to one character, so a fallback
# attribute holding one is empty or not.
_MAYBE_EMPTY = ["&#1;", "&#129;", "&#141;", "&#xFFFE;", "&#0;", "&#13;", "&#127;", "&#159;", "&#xFDD0;", "", "a"]


def _fallback_control(rng: random.Random) -> str:
    """A control whose static fallback depends on whether one value decodes to nothing."""
    value = rng.choice(_MAYBE_EMPTY)
    return rng.choice([
        f'<a @click="go()" href="{value}">a</a>',
        f'<button @click="go()" form="{value}">b</button>',
        f'<input @click="go()" type="{value}button">',
        f'<section :href="u" href="{value}">s</section>',
        f'<form :action="u" action="{value}"></form>',
    ])  # fmt: skip


def _piece(rng: random.Random, depth: int, marker: bool) -> str:
    roll = rng.random()
    if roll < 0.05:
        return _fallback_control(rng)
    if roll < 0.7:
        return _element(rng, depth, marker)
    if roll < 0.8:
        return rng.choice(["text", "a &amp; b", "<!-- <script>x</script> -->", "\u00e9", " "])
    if roll < 0.85:
        return "<!DOCTYPE html>"
    return rng.choice(["<br>", "<img src=x onerror=y>", "<svg><script/></svg>", "<svg><style>s</style></svg>"])


def _page(rng: random.Random, marker: bool) -> list[str]:
    pieces = [_piece(rng, 0, marker) for _ in range(rng.randint(1, 6))]
    tail = rng.random()
    if tail < 0.05:
        pieces.append(rng.choice(["<a href='x", "<!-- open", "<script>open", "<style>open", "<div", "<a\0b c=d>"]))
    elif tail < 0.07:
        pieces.append("\ud800")
    return pieces


# ---------------------------------------------------------------------------
# Running both sides
# ---------------------------------------------------------------------------


def _outcome(call: Callable[[], object]) -> tuple[object, ...]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            value = call()
        except Exception as error:  # noqa: BLE001 - the error is part of what is compared
            return ("error", type(error).__name__, str(error), [str(w.message) for w in caught])
    return ("value", value, [(w.category.__name__, str(w.message)) for w in caught])


def _tag_starts(html: str) -> list[int]:
    try:
        return [node.start_tag.token.start_index for node in scan_output_html(html).elements]
    except Exception:  # noqa: BLE001 - an unreadable page has no tags to trust
        return []


def _scenario_results(html: str, rng: random.Random, *, second: str | None = None) -> list[tuple[object, ...]]:
    """Run every mode on `html` on both sides and return pairs of outcomes."""
    results: list[tuple[object, ...]] = []
    starts = _tag_starts(html)
    marker_prefix = rng.choice([None, "", TRUST_PREFIX, "data-cid-"])
    # Only the Vue body check trusts no tag by its attributes.
    js_prefix = TRUST_PREFIX if marker_prefix is None else marker_prefix
    # The settled page: after the hooks, possibly a different page that
    # repeats some raw elements of the one before them.
    settled = html if second is None else second
    settled_starts = starts if second is None else _tag_starts(second)
    settled_trusted = frozenset(rng.sample(settled_starts, k=min(len(settled_starts), rng.randint(0, 2))))

    for mode in ("warn", "strict"):
        for remember in (False, True):
            outcomes = []
            for cls in (_CspRenderValidator, ReferenceCspValidator):
                validator = cls(mode)

                def run(validator: Any = validator, remember: bool = remember) -> object:
                    if remember:
                        validator.validate_pre_extension_html(html, component_classes=COMPONENT_CLASSES)
                    validator.validate_settled_html(
                        settled,
                        marker_prefix=marker_prefix,
                        trusted_tag_starts=settled_trusted,
                        component_classes=COMPONENT_CLASSES,
                    )
                    return list(validator._findings)

                outcomes.append((_outcome(run), _outcome(validator.report)))
            results.append(("csp", mode, remember, *outcomes))

    for mode in ("warn", "omit", "forbid"):
        for remember in (False, True):
            for marker in (None, MARKER):
                outcomes = []
                for cls in (_JavascriptPolicy, ReferenceJavascriptPolicy):
                    policy = cls(mode)

                    def run(policy: Any = policy, marker: str | None = marker, remember: bool = remember) -> object:
                        if remember:
                            policy.validate_pre_extension_html(html, component_classes=COMPONENT_CLASSES)
                        cleaned = policy.validate_settled_html(
                            settled,
                            marker_prefix=js_prefix,
                            trusted_tag_starts=settled_trusted,
                            component_classes=COMPONENT_CLASSES,
                            omit_handler_marker=marker,
                        )
                        return cleaned, list(policy._findings)

                    outcomes.append((_outcome(run), _outcome(policy.report)))
                results.append(("js", mode, remember, marker, *outcomes))

    # One Rust read serves both validators, as serialize() shares it.
    for js_mode in ("warn", "omit", "forbid"):
        results.append(("shared", js_mode, *_shared_results(settled, js_mode, js_prefix, settled_trusted)))

    results.append(
        (
            "gate",
            _outcome(lambda: _output_policy.server_copy_passes_csp(html, "strict")),
            _outcome(lambda: reference_server_copy_passes_csp(html, "strict")),
        )
    )
    return results


def _shared_results(
    settled: str, js_mode: str, js_prefix: str, settled_trusted: frozenset[int]
) -> tuple[tuple[object, ...], tuple[object, ...]]:
    """Check one page for both validators with one Rust read, and each Python copy on its own."""
    csp_real = _CspRenderValidator("warn")
    js_real = _JavascriptPolicy(js_mode)  # type: ignore[arg-type]
    csp_copy = ReferenceCspValidator("warn")
    js_copy = ReferenceJavascriptPolicy(js_mode)  # type: ignore[arg-type]

    def shared() -> object:
        check = _output_policy.check_output_html(
            settled,
            csp=True,
            javascript=js_mode,  # type: ignore[arg-type]
            marker_prefix=js_prefix,
            trusted_tag_starts=settled_trusted,
            omit_handler_marker=MARKER,
        )
        cleaned = js_real.validate_settled_html(
            settled,
            marker_prefix=js_prefix,
            trusted_tag_starts=settled_trusted,
            component_classes=COMPONENT_CLASSES,
            omit_handler_marker=MARKER,
            check=check,
        )
        if cleaned is settled:
            csp_real.validate_settled_html(
                settled,
                marker_prefix=js_prefix,
                trusted_tag_starts=settled_trusted,
                component_classes=COMPONENT_CLASSES,
                check=check,
            )
        return cleaned is settled, list(js_real._findings), list(csp_real._findings)

    def separate() -> object:
        cleaned = js_copy.validate_settled_html(
            settled,
            marker_prefix=js_prefix,
            trusted_tag_starts=settled_trusted,
            component_classes=COMPONENT_CLASSES,
            omit_handler_marker=MARKER,
        )
        if cleaned == settled:
            csp_copy.validate_settled_html(
                settled,
                marker_prefix=js_prefix,
                trusted_tag_starts=settled_trusted,
                component_classes=COMPONENT_CLASSES,
            )
        return cleaned == settled, list(js_copy._findings), list(csp_copy._findings)

    return _outcome(shared), _outcome(separate)


def _blocks_results(blocks: list[str]) -> list[tuple[object, ...]]:
    """Check several opaque blocks with one validator, as the Events path does."""
    results: list[tuple[object, ...]] = []
    for js_cls, csp_cls in (
        (_JavascriptPolicy, _CspRenderValidator),
        (ReferenceJavascriptPolicy, ReferenceCspValidator),
    ):
        policy, csp = js_cls("warn"), csp_cls("warn")

        def run(policy: Any = policy, csp: Any = csp) -> object:
            for block in blocks:
                policy.validate_pre_extension_html(block, component_classes={})
                csp.validate_pre_extension_html(block, component_classes={})
            for block in blocks:
                policy.validate_settled_html(
                    block, marker_prefix="data-cid-", trusted_tag_starts=frozenset(), component_classes={}
                )
                csp.validate_settled_html(
                    block, marker_prefix="data-cid-", trusted_tag_starts=frozenset(), component_classes={}
                )
            return list(policy._findings), list(csp._findings)

        results.append(_outcome(run))
    return [("blocks", *results)]


def _differences(results: list[tuple[object, ...]]) -> list[tuple[object, ...]]:
    differences = []
    for result in results:
        *label, real, copy = result
        if real != copy:
            differences.append((*label, real, copy))
    return differences


def _mismatch(pieces: list[str], rng_state: object, second: list[str] | None) -> list[tuple[object, ...]]:
    rng = random.Random()  # noqa: S311 - a seeded page generator, not a secret
    rng.setstate(rng_state)  # type: ignore[arg-type]
    html = "".join(pieces)
    return _differences(_scenario_results(html, rng, second=None if second is None else "".join(second)))


def _shrink(pieces: list[str], rng_state: object, second: list[str] | None) -> list[str]:
    """Delete top-level pieces one at a time while the two sides still differ."""
    changed = True
    while changed:
        changed = False
        for index in range(len(pieces)):
            candidate = pieces[:index] + pieces[index + 1 :]
            if candidate and _mismatch(candidate, rng_state, second):
                pieces = candidate
                changed = True
                break
    return pieces


@pytest.mark.parametrize("chunk", range(4))
def test_rust_output_checks_match_the_python_rules(chunk: int) -> None:
    rng = random.Random(f"{SEED}-{chunk}")  # noqa: S311 - a seeded page generator, not a secret
    for page_number in range(PAGES // 4):
        marker = rng.random() < 0.5
        pieces = _page(rng, marker)
        second = None
        if rng.random() < 0.3:
            # A settled page that repeats some raw elements of the page
            # before the hooks, drops others, and adds new ones.
            kept = [piece for piece in pieces if rng.random() < 0.7]
            # A repeated piece gives two identical raw elements, of which
            # only one may be trusted.
            second = kept + kept[: rng.randint(0, 2)] + _page(rng, marker)
        state = rng.getstate()
        differences = _mismatch(pieces, state, second)
        if differences:
            smallest = _shrink(pieces, state, second)
            pytest.fail(
                f"seed {SEED}-{chunk}, page {page_number}: the Rust checks differ from the Python rules\n"
                f"page: {''.join(smallest)!r}\nsettled page: {second and ''.join(second)!r}\n"
                f"first difference: {_mismatch(smallest, state, second)[:1]!r}"
            )
        if page_number % 10 == 0:
            blocks = ["".join(_page(rng, marker=False)) for _ in range(rng.randint(2, 4))]
            block_differences = _differences(_blocks_results(blocks))
            assert not block_differences, (blocks, block_differences)
