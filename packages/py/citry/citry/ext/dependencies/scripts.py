"""
Caching of components' processed JS and CSS.

A component class's ``Component.js`` / ``Component.css`` content is shared by
every instance, so it is stored once, as a serialized :class:`Script` /
:class:`Style`, in the ``Citry`` instance's cache. Two consumers read it:

- The emission step at serialize time (``emission.py``), which renders the
  cached objects into the page.
- The script-serving URL endpoint (``routes.py``), which is also why the
  cache is the pluggable ``Citry.cache``: with a shared backend, the worker
  that serves a script need not be the one that rendered the page.

Keys follow django-components' scheme with a citry prefix::

    citry:<class_id>:js              the class's Component.js
    citry:<class_id>:css             the class's Component.css
    citry:<class_id>:js:component:<hash>   one content-addressed JS version
    citry:<class_id>:css:component:<hash>  one content-addressed CSS version
    citry:<class_id>:css:<hash>      a generated css_data() variables stylesheet

Citry writes no ``js_data()`` entry; those values go into the page itself.
This module never serves a ``citry:<class_id>:js:<hash>`` entry (see
``get_script``).

The ``css_data()`` stylesheets go to ``Citry.cache`` only when a cache is
configured. Without one, each page puts its own into this process's store of
page files as it is written, which ``CitrySettings.vue_asset_max_bytes``
limits (``citry.ext.dependencies.emission.publish_css_data_stylesheets``).

Design: docs/design/dependencies.md section 4.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import time
from dataclasses import dataclass
from functools import lru_cache
from hashlib import md5, sha256
from typing import TYPE_CHECKING, Literal, cast
from weakref import WeakSet

from citry._class_introspection import _safe_class_text
from citry.cache import _forget_stored_key, _remember_confirmed, _store_if_missing, _store_unless_matched
from citry.constness import _unwrap_const_markers, const_value
from citry.ext.dependencies.types import Script, ScriptType, Style
from citry.secret import Secret
from citry.util.css import SECRET_IN_CSS_DATA_ADVICE, serialize_css_var_value, validate_css_var_name
from citry.util.logger import logger

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry import Citry
    from citry.component import Component

_CACHE_PREFIX = "citry"

_REGEX_PREFIX_KEYWORDS = frozenset(
    {
        "await",
        "case",
        "delete",
        "do",
        "else",
        "in",
        "instanceof",
        "new",
        "return",
        "throw",
        "typeof",
        "void",
        "yield",
    }
)
_CONTROL_PAREN_KEYWORDS = frozenset({"catch", "for", "if", "switch", "while", "with"})
_CLASS_EXPRESSION_PREFIX_TOKENS = _REGEX_PREFIX_KEYWORDS | frozenset(
    {
        "!",
        "%",
        "&",
        "(",
        "*",
        "+",
        ",",
        "-",
        "/",
        ":",
        "<",
        "=",
        ">",
        "?",
        "[",
        "^",
        "|",
        "~",
        "=>",
    }
)


def _is_identifier_start(char: str) -> bool:
    """Approximate ECMAScript IdentifierStart without decoding escapes."""
    return char in "_$" or char.isidentifier()


def _is_identifier_part(char: str) -> bool:
    """Approximate ECMAScript IdentifierPart without decoding escapes."""
    return _is_identifier_start(char) or char.isdigit() or char in "\u200c\u200d" or f"a{char}".isidentifier()


def _skip_quoted(js_content: str, index: int, quote: str) -> int:
    """Return the first position after one JS string literal."""
    index += 1
    while index < len(js_content):
        char = js_content[index]
        if char == "\\":
            index += 2
        elif char == quote:
            return index + 1
        else:
            index += 1
    return index


def _skip_line_comment(js_content: str, index: int) -> int:
    newline = js_content.find("\n", index + 2)
    return len(js_content) if newline == -1 else newline


def _skip_block_comment(js_content: str, index: int) -> int:
    end = js_content.find("*/", index + 2)
    return len(js_content) if end == -1 else end + 2


def _skip_regex(js_content: str, index: int) -> int:
    """Return the first position after one JS regex literal and its flags."""
    index += 1
    in_character_class = False
    while index < len(js_content):
        char = js_content[index]
        if char == "\\":
            index += 2
            continue
        if char == "[":
            in_character_class = True
        elif char == "]":
            in_character_class = False
        elif char == "/" and not in_character_class:
            index += 1
            while index < len(js_content) and _is_identifier_part(js_content[index]):
                index += 1
            return index
        elif char in "\r\n":
            return index
        index += 1
    return index


def _skip_space_and_comments(js_content: str, index: int) -> int:
    while index < len(js_content):
        if js_content[index].isspace():
            index += 1
        elif js_content.startswith("//", index):
            index = _skip_line_comment(js_content, index)
        elif js_content.startswith("/*", index):
            index = _skip_block_comment(js_content, index)
        else:
            break
    return index


def _followed_by_block(js_content: str, call_open: int) -> bool:
    """Whether the parenthesized expression is followed by ``{``."""
    index = call_open
    depth = 0
    can_start_regex = True
    while index < len(js_content):
        char = js_content[index]
        if char.isspace():
            index += 1
            continue
        if js_content.startswith("//", index):
            index = _skip_line_comment(js_content, index)
            continue
        if js_content.startswith("/*", index):
            index = _skip_block_comment(js_content, index)
            continue
        if char in "'\"":
            index = _skip_quoted(js_content, index, char)
            can_start_regex = False
            continue
        if char == "`":
            index = _scan_template_literal(js_content, index, [])
            can_start_regex = False
            continue
        if char == "/" and can_start_regex:
            index = _skip_regex(js_content, index)
            can_start_regex = False
            continue
        if _is_identifier_start(char):
            start = index
            index += 1
            while index < len(js_content) and _is_identifier_part(js_content[index]):
                index += 1
            can_start_regex = js_content[start:index] in _REGEX_PREFIX_KEYWORDS
            continue
        if char.isdigit():
            index += 1
            while index < len(js_content) and (js_content[index].isalnum() or js_content[index] in "._"):
                index += 1
            can_start_regex = False
            continue
        if char == "(":
            depth += 1
            can_start_regex = True
        elif char == ")":
            depth -= 1
            if depth == 0:
                next_token = _skip_space_and_comments(js_content, index + 1)
                return next_token < len(js_content) and js_content[next_token] == "{"
            can_start_regex = False
        elif char in "]}":
            can_start_regex = False
        elif char in "[{,;:?~=!%^&*+-|<>":
            can_start_regex = True
        else:
            can_start_regex = False
        index += 1
    return False


def _is_component_declaration(
    recent_tokens: list[str],
    brace_contexts: list[str],
) -> bool:
    """Whether ``$component`` occupies a function or method name position."""
    if recent_tokens[-1:] == ["function"]:
        return True
    if recent_tokens[-2:] == ["function", "*"]:
        return True

    if brace_contexts[-1:] == ["class"]:
        return True
    if brace_contexts[-1:] != ["object"]:
        return False

    index = len(recent_tokens) - 1
    while index >= 0 and recent_tokens[index] in {
        "*",
        "async",
        "get",
        "set",
        "static",
    }:
        index -= 1
    return index >= 0 and recent_tokens[index] in {"{", "}", ",", ";"}


def _scan_template_literal(
    js_content: str,
    index: int,
    spans: list[tuple[int, int, int]],
) -> int:
    """Skip template text while scanning each ``${...}`` expression."""
    index += 1
    while index < len(js_content):
        char = js_content[index]
        if char == "\\":
            index += 2
        elif char == "`":
            return index + 1
        elif js_content.startswith("${", index):
            index = _scan_js_code(js_content, index + 2, spans, stop_at_brace=True)
        else:
            index += 1
    return index


def _scan_js_code(
    js_content: str,
    index: int,
    spans: list[tuple[int, int, int]],
    *,
    stop_at_brace: bool = False,
) -> int:
    """Find live ``$component(...)`` calls in one bounded JS code region."""
    can_start_regex = True
    brace_depth = 0
    brace_contexts: list[str] = []
    paren_contexts: list[bool] = []
    bracket_depth = 0
    previous_identifier: str | None = None
    property_access = False
    recent_tokens: list[str] = []
    pending_class_depth: tuple[int, int, int] | None = None

    while index < len(js_content):
        char = js_content[index]

        if char.isspace():
            index += 1
            continue
        if js_content.startswith("//", index):
            index = _skip_line_comment(js_content, index)
            continue
        if js_content.startswith("/*", index):
            index = _skip_block_comment(js_content, index)
            continue
        if char in "'\"":
            index = _skip_quoted(js_content, index, char)
            can_start_regex = False
            previous_identifier = None
            recent_tokens.append("value")
            continue
        if char == "`":
            index = _scan_template_literal(js_content, index, spans)
            can_start_regex = False
            previous_identifier = None
            recent_tokens.append("value")
            continue
        if char == "/" and can_start_regex:
            index = _skip_regex(js_content, index)
            can_start_regex = False
            previous_identifier = None
            recent_tokens.append("value")
            continue
        if _is_identifier_start(char):
            start = index
            is_property_access = property_access
            index += 1
            while index < len(js_content) and _is_identifier_part(js_content[index]):
                index += 1
            identifier_end = index
            identifier = js_content[start:index]
            call_open = _skip_space_and_comments(js_content, index)
            if (
                identifier == "$component"
                and not property_access
                and call_open < len(js_content)
                and js_content[call_open] == "("
                and not (
                    _followed_by_block(js_content, call_open)
                    and _is_component_declaration(
                        recent_tokens,
                        brace_contexts,
                    )
                )
            ):
                spans.append((start, identifier_end, call_open + 1))
            can_start_regex = identifier in _REGEX_PREFIX_KEYWORDS
            previous_identifier = identifier
            property_access = False
            if (
                identifier == "class"
                and not is_property_access
                and not (call_open < len(js_content) and js_content[call_open] == "(")
                and (
                    brace_contexts[-1:] != ["class"]
                    or (recent_tokens[-1:] and recent_tokens[-1] in _CLASS_EXPRESSION_PREFIX_TOKENS)
                )
            ):
                pending_class_depth = (
                    len(paren_contexts),
                    bracket_depth,
                    len(brace_contexts),
                )
            recent_tokens.append(identifier)
            continue
        if char.isdigit():
            index += 1
            while index < len(js_content):
                if js_content[index].isalnum() or js_content[index] in "._":
                    index += 1
                else:
                    break
            can_start_regex = False
            previous_identifier = None
            recent_tokens.append("value")
            continue
        if char == "{":
            brace_depth += 1
            current_depth = (
                len(paren_contexts),
                bracket_depth,
                len(brace_contexts),
            )
            if pending_class_depth == current_depth:
                brace_contexts.append("class")
                pending_class_depth = None
            elif recent_tokens[-1:] == ["=>"]:
                brace_contexts.append("block")
            elif recent_tokens[-1:] and recent_tokens[-1] in {
                "(",
                ",",
                ":",
                "=",
                "[",
                "return",
                "yield",
            }:
                brace_contexts.append("object")
            else:
                brace_contexts.append("block")
            can_start_regex = True
        elif char == "}":
            if stop_at_brace and brace_depth == 0:
                return index + 1
            brace_depth -= 1
            if brace_contexts:
                brace_contexts.pop()
            can_start_regex = False
        elif char == "(":
            paren_contexts.append(previous_identifier in _CONTROL_PAREN_KEYWORDS)
            can_start_regex = True
        elif char == ")":
            can_start_regex = paren_contexts.pop() if paren_contexts else False
        elif char in "]":
            bracket_depth -= 1
            can_start_regex = False
        elif char in ".[":
            can_start_regex = char == "["
            property_access = char == "."
            if char == "[":
                bracket_depth += 1
        elif char in ",;:?~=!%^&*+-|<>":
            can_start_regex = True
            property_access = False
            if char in ",:;=" and pending_class_depth == (
                len(paren_contexts),
                bracket_depth,
                len(brace_contexts),
            ):
                pending_class_depth = None
        else:
            can_start_regex = False
            property_access = False
        if js_content.startswith("=>", index):
            recent_tokens.append("=>")
            index += 2
            previous_identifier = None
            property_access = False
            can_start_regex = True
            continue
        recent_tokens.append(char)
        previous_identifier = None
        index += 1
    return index


def _component_call_spans(js_content: str) -> list[tuple[int, int, int]]:
    """Return OXC-authenticated spans for live, bare ``$component(...)`` calls."""
    from citry._browser_expressions import analyze_browser_component_source  # noqa: PLC0415

    analysis = analyze_browser_component_source(js_content)
    if not analysis.valid:
        return []
    encoded = js_content.encode("utf-8")

    def char_index(byte_index: int) -> int:
        return len(encoded[:byte_index].decode("utf-8"))

    return [
        (
            char_index(call.callee_start_index),
            char_index(call.callee_end_index),
            char_index(call.open_paren_end_index),
        )
        for call in analysis.component_calls
    ]


@dataclass(frozen=True, slots=True)
class _VariablesScriptCapture:
    """Canonical source and exact cache value for one variables dependency."""

    source_json: str
    variables_hash: str
    cache_value: str


@dataclass(frozen=True, slots=True)
class _ComponentScriptCapture:
    """Derived class asset data reused by every instance of one exact class."""

    script: Script | Style | None
    serialized: str | None
    content_hash: str | None
    uses_component: bool


_COMPONENT_SCRIPT_CAPTURE = "_citry_component_script_capture"

# A fixed label that turns each secret into the key that names `css_data()`
# stylesheets. It differs from the State token label, so the two keys differ.
# As for State tokens, the label is the HMAC key and the secret is the
# message: the secret is often shared with other code (Django's
# `SECRET_KEY`, for one), and code that returns HMAC-SHA256 of any text
# under the raw secret must not be able to hand out this key.
_CSS_DATA_KEY_LABEL = b"citry.dependencies.css-data-name"
# An engine with no secret and no configured cache uses this random key,
# made once per process: its stylesheets never leave this process, so no
# other worker has to compute the same names. Engines in one process share
# it, so they write the same page for the same values.
_PROCESS_CSS_DATA_KEY = secrets.token_bytes(32)
# Engines already warned that they name `css_data()` stylesheets without a
# key, so each engine logs the warning once rather than on every render.
_WARNED_UNKEYED_ENGINES: WeakSet[Citry] = WeakSet()


@lru_cache(maxsize=16)
def _css_data_key(secret: str) -> bytes:
    """Return the key that names ``css_data()`` stylesheets for one ``secret`` entry."""
    # Kept per entry, because every render with css_data() needs it and a
    # deployment has only one secret plus a few rotation entries.
    return hmac.new(_CSS_DATA_KEY_LABEL, secret.encode("utf-8"), sha256).digest()


def _css_data_keys(citry: Citry) -> tuple[bytes | None, ...]:
    """
    Return the keys that name this engine's ``css_data()`` stylesheets, the one for new stylesheets first.

    Citry names a stylesheet's URL with a hash of its values. Without a key,
    anyone could hash a guessed value, request that URL, and learn from the
    answer whether some visitor's page used the value. With a key, only the
    server can name a stylesheet.

    Each entry of the ``secret`` setting gives one key, so a URL named
    before a key rotation still resolves while the old secret stays listed.
    With no secret, an engine that keeps its stylesheets in this process
    uses a random key made once per process. ``None`` means no key: an
    engine with a configured cache and no secret, whose workers have no
    shared key to agree on.
    """
    configured = citry.settings.secret
    if configured:
        return tuple(_css_data_key(entry) for entry in configured)
    # _vue.events imports this module, so importing it here at load time
    # would be circular.
    from citry._vue.events import keeps_assets_in_process_only  # noqa: PLC0415

    if not keeps_assets_in_process_only(citry):
        return (None,)
    return (_PROCESS_CSS_DATA_KEY,)


def _css_data_hash(key: bytes | None, source_json: str) -> str:
    """Return the name of the stylesheet built from ``source_json``: 32 hex characters of its keyed hash."""
    data = source_json.encode()
    digest = sha256(data) if key is None else hmac.new(key, data, sha256)
    return digest.hexdigest()[:32]


def _new_css_data_key(citry: Citry) -> bytes | None:
    """Return the key that names this engine's new ``css_data()`` stylesheets, warning once when there is none."""
    key = _css_data_keys(citry)[0]
    if key is None and citry not in _WARNED_UNKEYED_ENGINES:
        # A deployed app does not read the docs again, so the log is where an
        # app with a configured cache and no secret learns about the gap.
        _WARNED_UNKEYED_ENGINES.add(citry)
        logger.warning(
            "Citry has a configured cache but no secret, so it names css_data() stylesheets with a plain"
            " hash of their values. Anyone who guesses a css_data() value can then work out its stylesheet"
            " URL and learn from the answer whether some visitor's page used that value. Set the secret"
            " setting (citry.contrib.django.secret() in a Django project) when css_data() returns values"
            " that differ between visitors."
        )
    return key


def _css_data_key_for(citry: Citry, source_json: str, variables_hash: str) -> tuple[bool, bytes | None]:
    """
    Find the key of this engine that hashes ``source_json`` to ``variables_hash``.

    Returns ``(True, key)``, or ``(False, None)`` when no key does.
    """
    # A name is hex. `compare_digest` raises for text that is not ASCII,
    # which a render cache entry could hold, so such a name simply fails.
    if not variables_hash.isascii():
        return False, None
    for key in _css_data_keys(citry):
        # The name comes from the request, so compare without leaking how much of it matched.
        if hmac.compare_digest(_css_data_hash(key, source_json), variables_hash):
            return True, key
    return False, None


def gen_cache_key(class_id: str, script_type: ScriptType, variables_hash: str | None = None) -> str:
    """The cache key for one component script (see the module docstring for the scheme)."""
    if variables_hash:
        return f"{_CACHE_PREFIX}:{class_id}:{script_type}:{variables_hash}"
    return f"{_CACHE_PREFIX}:{class_id}:{script_type}"


def gen_component_cache_key(class_id: str, script_type: ScriptType, content_hash: str) -> str:
    """The immutable cache key for one version of a class-level script."""
    return f"{_CACHE_PREFIX}:{class_id}:{script_type}:component:{content_hash}"


def transform_component(js_content: str, class_id: str) -> str:
    """
    Expand the ``$component(`` sugar in a component's JS.

    ``$component({...})`` becomes a partially applied
    ``__citryRuntime.registerTypeOptions`` call carrying the component class ID
    and a content digest. Repeated pages may register the same trusted Options
    source without replacing it, while different source under the same type
    identity remains a collision.
    """
    spans = _component_call_spans(js_content)
    if not spans:
        return js_content

    return _transform_component_spans(js_content, class_id, spans)


def _transform_component_spans(
    js_content: str,
    class_id: str,
    spans: list[tuple[int, int, int]],
) -> str:
    """Expand already-scanned ``$component`` calls without a second JS pass."""
    source_hash = hashlib.sha256(js_content.encode()).hexdigest()
    replacement = f'__citryRuntime.registerTypeOptions.bind(null, "{class_id}", "{source_hash}")('
    parts: list[str] = []
    previous_end = 0
    for start, identifier_end, end in spans:
        trivia = js_content[identifier_end : end - 1]
        parts.extend((js_content[previous_end:start], replacement, trivia))
        previous_end = end
    parts.append(js_content[previous_end:])
    return "".join(parts)


def _component_content(script_type: ScriptType, comp_cls: type[Component]) -> str | None:
    """Return substantive component JS/CSS, treating blank content as absent."""
    content = comp_cls.get_js() if script_type == "js" else comp_cls.get_css()
    return content if content and content.strip() else None


def has_component_asset(script_type: ScriptType, comp_cls: type[Component]) -> bool:
    """Whether the component carries non-whitespace JS or CSS content."""
    return _component_script_capture(script_type, comp_cls).script is not None


def uses_component(comp_cls: type[Component]) -> bool:
    """Whether the class's JS registers a per-instance callback via ``$component``."""
    return _component_script_capture("js", comp_cls).uses_component


def _component_script_capture(
    script_type: ScriptType,
    comp_cls: type[Component],
) -> _ComponentScriptCapture:
    """Derive one exact class's asset once, without trusting inherited state."""
    captures = vars(comp_cls).get(_COMPONENT_SCRIPT_CAPTURE)
    if captures is not None and script_type in captures:
        return captures[script_type]

    def store(capture: _ComponentScriptCapture) -> _ComponentScriptCapture:
        # Runs under the engine's `_template_source_lock`. Keep a capture
        # another thread stored first, so every render sends the browser the
        # same script.
        stored = vars(comp_cls).get(_COMPONENT_SCRIPT_CAPTURE)
        if stored is not None and script_type in stored:
            return stored[script_type]
        setattr(comp_cls, _COMPONENT_SCRIPT_CAPTURE, {**(stored or {}), script_type: capture})
        return capture

    # Reading the JS or CSS can run the class's `on_js_loaded` or
    # `on_css_loaded` hooks, so the capture is built with no lock held.
    return comp_cls.citry._load_and_store(lambda: _build_component_script_capture(script_type, comp_cls), store)


def _build_component_script_capture(
    script_type: ScriptType,
    comp_cls: type[Component],
) -> _ComponentScriptCapture:
    """Derive one exact class's asset from its current JS or CSS, without storing it."""
    content = _component_content(script_type, comp_cls)
    uses_component_call = False
    script: Script | Style | None = None
    if content is not None:
        if script_type == "js":
            spans = _component_call_spans(content)
            uses_component_call = bool(spans)
            if spans:
                content = _transform_component_spans(content, comp_cls.class_id, spans)
            script = Script(kind="component", content=content, origin_class_id=comp_cls.class_id)
        else:
            script = Style(kind="component", content=content, origin_class_id=comp_cls.class_id)

    serialized = None if script is None else json.dumps(script.to_json())
    content_hash = None if serialized is None else md5(serialized.encode(), usedforsecurity=False).hexdigest()[:12]
    return _ComponentScriptCapture(
        script=script,
        serialized=serialized,
        content_hash=content_hash,
        uses_component=uses_component_call,
    )


def _component_script(script_type: ScriptType, comp_cls: type[Component]) -> Script | Style | None:
    """Build the class-level cached object for the component's current content."""
    return _component_script_capture(script_type, comp_cls).script


def _cache_component_script(
    script_type: ScriptType,
    comp_cls: type[Component],
    *,
    force: bool = False,
) -> tuple[Script | Style, str] | None:
    """Return this class version's object and make the shared cache agree with it."""
    capture = _component_script_capture(script_type, comp_cls)
    if capture.script is None:
        return None
    if capture.serialized is None or capture.content_hash is None:
        raise RuntimeError("A present component asset has no serialized capture.")

    citry = comp_cls.citry
    cache = citry.cache
    serialized = capture.serialized
    # The versioned key is named by the payload's hash, so a key the backend
    # holds holds this payload: check it at most once per recheck interval
    # instead of reading it back on every render.
    versioned_key = gen_component_cache_key(comp_cls.class_id, script_type, capture.content_hash)
    # Keep the original stable key for old URLs and integrations. It is a
    # mutable compatibility entry, so every reader validates it against its
    # current class before returning. Generated URLs use the immutable key.
    # Its value changes with the class, so it is compared, again at most once
    # per recheck interval for one class version.
    stable_key = gen_cache_key(comp_cls.class_id, script_type)
    if force:
        # A caller that passes `force` rewrites both entries whatever this
        # process remembers about them.
        cache.set(versioned_key, serialized)
        cache.set(stable_key, serialized)
        now = time.monotonic()
        _remember_confirmed(citry, versioned_key, None, now)
        _remember_confirmed(citry, stable_key, capture.content_hash, now)
    else:
        _store_if_missing(citry, cache, versioned_key, lambda: serialized)
        _store_unless_matched(citry, cache, stable_key, serialized, capture.content_hash)
    # Return the object built from this class, rather than reading the shared
    # key again. An old and new worker can legitimately alternate writes
    # during a rolling deployment; neither may serve the other's version.
    return capture.script, capture.content_hash


def cache_component_js(comp_cls: type[Component], *, force: bool = False) -> None:
    """
    Store the class's ``Component.js`` in the cache as a serialized ``Script``.

    The ``$component`` sugar is expanded here, once per class, so both the
    inlined tag and the URL-served file carry the expanded form. Does nothing
    for a component with no JS. Each process checks the stored payload at most
    once a minute, and writes it when it is missing or differs; ``force``
    writes it at once.
    """
    _cache_component_script("js", comp_cls, force=force)


def cache_component_css(comp_cls: type[Component], *, force: bool = False) -> None:
    """The CSS counterpart of :func:`cache_component_js`."""
    _cache_component_script("css", comp_cls, force=force)


def component_script_hash(script_type: ScriptType, comp_cls: type[Component]) -> str | None:
    """Cache and return the content hash used in this class version's script URL."""
    cached = _cache_component_script(script_type, comp_cls)
    return None if cached is None else cached[1]


def get_cached_component_script(
    citry: Citry,
    class_id: str,
    script_type: ScriptType,
    content_hash: str,
) -> Script | Style | None:
    """Read one immutable class-level script version by its URL hash."""
    key = gen_component_cache_key(class_id, script_type, content_hash)
    cached = citry.cache.get(key)
    if cached is None:
        # The backend no longer holds it; the next store must write it again
        # instead of trusting this process's record that it is stored.
        _forget_stored_key(citry, key)
        return None
    data = json.loads(cached)
    return Script.from_json(data) if script_type == "js" else Style.from_json(data)


def get_script(
    script_type: ScriptType,
    comp_cls: type[Component],
    variables_hash: str | None = None,
    *,
    even_refusal_cost: bool = False,
) -> Script | Style | None:
    """
    Read one cached object, validating class-level content against the current class.

    A ``css_data()`` stylesheet is built again from its stored values with
    the current check (see ``_rebuild_css_data_stylesheet``). A ``js_data()``
    script is never served, because Citry writes those values only into the
    page. ``even_refusal_cost`` is for a route that answers a request: it
    makes every refused ``css_data()`` name cost the same cache work (see
    ``_read_css_data_stylesheet``).
    """
    if variables_hash is None:
        class_cached = _cache_component_script(script_type, comp_cls)
        return None if class_cached is None else class_cached[0]
    # A `citry:<class_id>:js:<hash>` entry can only come from an earlier
    # release (0.1.0 to 0.5.1 wrote one for every js_data() result, with no
    # expiry), and anyone who guesses a js_data() value can compute its
    # name, so a variables hash for JavaScript always misses.
    if script_type == "js":
        return None
    return _read_css_data_stylesheet(comp_cls, variables_hash, even_refusal_cost=even_refusal_cost)[0]


# A key no Citry release writes. A refused name that has no leftover entry
# to delete reads this key instead, so every refused name makes the same
# number of cache calls, and takes about the same time, whatever the cache
# holds. A read, not a delete: a delete is a write, and on some backends
# (SQLite under `DiskCache`) every write takes a lock that all processes
# share, so a stream of 404s would slow every worker down.
_UNUSED_CSS_DATA_KEY = f"{_CACHE_PREFIX}:css-data-miss"


def delete_leftover_entry(citry: Citry, key: str) -> None:
    """Delete a cache entry that only an earlier release writes, keeping the request's answer a 404 if that fails."""
    # This runs while answering a request that already gets a 404. A backend
    # that refuses writes (a read-only replica, say) must not turn that
    # answer into a 500; the entry is then refused again on the next request.
    try:
        citry.cache.delete(key)
    except Exception:  # noqa: BLE001 - any backend error; the answer stays 404
        # Debug, not warning: a request can trigger this, so it must not flood the log.
        logger.debug("Citry could not delete a cache entry that an earlier release left.", exc_info=True)
    _forget_stored_key(citry, key)


def _read_css_data_stylesheet(
    comp_cls: type[Component], variables_hash: str, *, even_refusal_cost: bool
) -> tuple[Style | None, bool]:
    """
    Read one ``css_data()`` stylesheet, deleting an entry under its name that an earlier release left.

    Returns ``(stylesheet, gone)``. ``stylesheet`` is ``None`` when this
    engine would not serve the name. ``gone`` is ``True`` when no entry is
    left under the name: none was stored, or this call deleted one.

    A request can choose any name, and a refused leftover takes one cache
    delete that a miss does not. With ``even_refusal_cost``, every other
    refusal from a shared cache makes one more read instead, so each
    refusal makes two cache calls and the response time does not tell a
    leftover from a miss.
    """
    # _vue.events imports this module, so importing it here at load time
    # would be circular.
    from citry._vue.events import css_data_stylesheet, keeps_assets_in_process_only  # noqa: PLC0415

    citry = comp_cls.citry
    key = gen_cache_key(comp_cls.class_id, "css", variables_hash)
    # Without a configured cache, css_data() stylesheets live only in this
    # process's store of page files, which no other release can write.
    if keeps_assets_in_process_only(citry):
        serialized = css_data_stylesheet(citry, key)
        if serialized is None:
            return None, True
        return _rebuild_css_data_stylesheet(citry, comp_cls.class_id, variables_hash, _json_or_none(serialized)), False
    serialized = citry.cache.get(key)
    data = None if serialized is None else _json_or_none(serialized)
    rebuilt = (
        None if serialized is None else _rebuild_css_data_stylesheet(citry, comp_cls.class_id, variables_hash, data)
    )
    if rebuilt is not None:
        return rebuilt, False
    if serialized is not None and _left_by_an_earlier_release(citry, variables_hash, data):
        # Deleting a refused leftover means the next request for the same
        # name is a plain miss. A worker of the earlier release that still
        # links it writes it again on its next render.
        delete_leftover_entry(citry, key)
        return None, True
    if even_refusal_cost:
        citry.cache.get(_UNUSED_CSS_DATA_KEY)
    return None, serialized is None


def _json_or_none(serialized: str) -> object:
    """Parse a stored entry, or return ``None`` for one that an older release wrote as plain text."""
    try:
        return json.loads(serialized)
    except ValueError:
        return None


def _left_by_an_earlier_release(citry: Citry, variables_hash: str, data: object) -> bool:
    """Return whether a refused ``css_data()`` entry can only have been written by an earlier release."""
    # 0.1.0 and 0.2.0 stored only the text, and an entry that is not JSON
    # comes from no release this one can read.
    if type(data) is not dict or type(data.get("source")) is not str:
        return True
    # A name that is the plain hash of its values was made without a key.
    # An engine that names its stylesheets without a key accepts such a
    # name, so for that engine it is not a leftover. A name made under
    # another key, such as a secret this worker does not hold yet, stays.
    return None not in _css_data_keys(citry) and hmac.compare_digest(
        _css_data_hash(None, data["source"]), variables_hash
    )


# How every `css_data()` stylesheet Citry has written since 0.6.0 begins:
# the class id in a comment, then the rule for the stylesheet's marker.
_CSS_DATA_STYLESHEET_HEAD = re.compile(r"/\* ([^\s*]+) \*/\n\[data-ccss-([0-9a-f]{1,64})\] \{\n")


def even_css_data_copy_refusal_cost(citry: Citry) -> None:
    """
    Do the cache work that refusing a stored copy of a ``css_data()`` stylesheet does.

    Refusing a copy makes three cache calls after reading the copy: it
    reads the copy's ``css_data()`` entry, then deletes leftovers or reads
    an unused key. A request that found no copy calls this, so its 404
    makes as many cache calls as a refusal.
    """
    for _ in range(3):
        citry.cache.get(_UNUSED_CSS_DATA_KEY)


def check_css_data_stylesheet_copy(citry: Citry, text: str) -> Literal["serve", "refuse", "delete"]:
    """
    Decide whether a stylesheet read from a shared cache may be served as a Vue page file.

    On an interactive page, a ``css_data()`` stylesheet is also published
    as a Vue page file, at a URL named by the sha256 of its bytes. A shared
    cache can still hold such a file that an earlier release wrote under a
    name made without a key, and anyone who guesses its values can compute
    that URL. Such a file is served only when the ``cache/`` route would
    serve the same bytes, so both URLs apply the same check.

    Returns ``"serve"`` for those bytes, and for any stylesheet that is not
    a ``css_data()`` stylesheet. Returns ``"delete"`` when no ``css_data()``
    entry is left under the stylesheet's name, so the caller deletes the
    copy too, with ``delete_leftover_entry``. Returns ``"refuse"``
    otherwise, after reading an unused key, so a refusal makes as many
    cache calls as a miss (see ``even_css_data_copy_refusal_cost``).
    """
    match = _CSS_DATA_STYLESHEET_HEAD.match(text)
    if match is None:
        return "serve"
    class_id, variables_hash = match.groups()
    # The `cache/` route answers 404 for a class this engine does not know.
    # The copy stays, because a worker that knows the class, such as one
    # already running the next deploy, may link it.
    try:
        comp_cls = citry.get_component_by_class_id(class_id)
    except KeyError:
        even_css_data_copy_refusal_cost(citry)
        return "refuse"
    current, gone = _read_css_data_stylesheet(comp_cls, variables_hash, even_refusal_cost=True)
    if current is not None and current.content == text:
        return "serve"
    # With no entry left under its name, the copy cannot be served again
    # until a render writes both back, so it goes too. When the entry was
    # only evicted, a worker whose page links the copy writes it back on a
    # render once its recheck interval
    # (`citry.cache._STORED_KEY_RECHECK_SECONDS`) has passed.
    if gone:
        return "delete"
    # A refused name has already made its extra call in the read above; a
    # stylesheet rebuilt with other bytes, such as one another release
    # wrote, has not. The caller makes no delete, so its call is made here.
    if current is not None:
        citry.cache.get(_UNUSED_CSS_DATA_KEY)
    citry.cache.get(_UNUSED_CSS_DATA_KEY)
    return "refuse"


def _rebuild_css_data_stylesheet(citry: Citry, class_id: str, variables_hash: str, data: object) -> Style | None:
    """
    Build a stored ``css_data()`` stylesheet again from its stored values, or return None when that is not possible.

    A shared cache can hold a stylesheet that an older Citry wrote, and the
    browser fetches it by URL long after the render. Serving the stored text
    would skip the checks this version applies to each value, so the values
    go through ``serialize_css_var_value`` again here, as they do in a
    render. An entry with no stored values, values the current check
    refuses, or values that do not match the hash in the URL counts as
    missing; the next render that uses those values stores the stylesheet
    again.
    """
    # An earlier version stored only the text, so there is nothing to build from.
    if type(data) is not dict or type(data.get("source")) is not str:
        return None
    # The URL names the values it was made for; an entry for other values is
    # not this stylesheet, and neither is one named under a key this engine
    # does not hold.
    found, key = _css_data_key_for(citry, data["source"], variables_hash)
    if not found:
        return None
    # A value the current check refuses must not reach the browser.
    try:
        rebuilt = _css_vars_capture(class_id, data["source"], key)
    except (TypeError, ValueError):
        return None
    return Style.from_json(json.loads(rebuilt.cache_value))


def get_component_script(script_type: ScriptType, comp_cls: type[Component]) -> Script | Style | None:
    """
    The class's own JS/CSS as a cached object, repopulating the cache on a miss.

    This is the lazy-repopulation rule (docs/design/dependencies.md section
    4.3): class-level scripts can always be rebuilt from the class itself, so
    a cache miss (fresh process, evicted entry) just re-caches and retries.

    Returns ``None`` when the component has no JS/CSS at all.
    """
    cached = _cache_component_script(script_type, comp_cls)
    return None if cached is None else cached[0]


def _json_default(value: object) -> object:
    # A data value may be a `Const` marker (a transparent proxy around the
    # real value, see citry/constness.py): the marker rides through kwargs
    # into the data methods' results. The JSON encoder rejects proxies, so
    # unwrap here; anything else genuinely is not serializable.
    unwrapped = const_value(value)
    if unwrapped is value:
        msg = f"Object of type {type(value).__name__} is not JSON serializable"
        raise TypeError(msg)
    return unwrapped


def _vars_json(data: Mapping[str, object]) -> str:
    """
    Write one ``css_data()`` result as the canonical JSON text that names its stylesheet.

    Identical data, however many instances or renders produce it, gives the
    same text, so it shares one stylesheet and the browser receives it once.
    """
    for name in data:
        if type(name) is not str:
            msg = f"Component data mapping keys must be exact strings; got {type(name).__name__} key {name!r}."
            raise TypeError(msg)
    json_text = json.dumps(
        data,
        allow_nan=False,
        default=_json_default,
        separators=(",", ":"),
    )
    return json_text


def _canonical_variables_json(source_json: str) -> dict[str, object]:
    """Parse the exact canonical JSON shape emitted by variable hashing."""

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for name, value in pairs:
            if name in result:
                raise ValueError(f"Duplicate JSON object key {name!r}.")
            result[name] = value
        return result

    try:
        data = json.loads(
            source_json,
            object_pairs_hook=unique_object,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as err:
        raise ValueError("Variables source is not strict JSON.") from err
    if type(data) is not dict or any(type(name) is not str for name in data):
        raise ValueError("Variables source must be a JSON object with string keys.")
    canonical = json.dumps(data, allow_nan=False, separators=(",", ":"))
    if canonical != source_json:
        raise ValueError("Variables source is not canonical JSON.")
    return data


def _css_vars_capture(class_id: str, source_json: str, key: bytes | None) -> _VariablesScriptCapture:
    data = _canonical_variables_json(source_json)
    # `key` comes from `_css_data_keys`, so an outsider cannot compute this
    # name from a guessed value.
    variables_hash = _css_data_hash(key, source_json)
    lines: list[str] = []
    for name, value in data.items():
        try:
            validate_css_var_name(name)
            serialized_value = serialize_css_var_value(value)
        except (TypeError, ValueError) as error:
            msg = f"Component {class_id!r} css_data() entry {name!r} cannot be emitted: {error}"
            raise ValueError(msg) from error
        lines.append(f"  --{name}: {serialized_value};")
    content = "\n".join([f"/* {class_id} */", f"[data-ccss-{variables_hash}] {{", *lines, "}"])
    style = Style(kind="variables", content=content, origin_class_id=class_id)
    return _VariablesScriptCapture(
        source_json=source_json,
        variables_hash=variables_hash,
        # The stored entry keeps the values it was built from, so a read
        # can build the stylesheet again with this version's checks rather
        # than trust text that another version wrote.
        cache_value=json.dumps({**style.to_json(), "source": source_json}),
    )


def _reject_secret_css_data(comp_cls: type[Component], css_data: Mapping[str, object]) -> None:
    """
    Raise when a ``css_data()`` value is or holds a ``citry.Secret``, whether or not the component has CSS.

    A component without CSS never builds the stylesheet that would refuse
    the value, so without this check the same mistake would fail only once
    CSS is added. With CSS, the stylesheet would refuse a list or dict with
    a message that does not mention the Secret, so this check runs first
    there too. The caller skips it when ``css_data()`` returned nothing, so
    most renders pay nothing.

    Raises:
        ValueError: When an entry holds a ``Secret``, naming the component
            by its class name, as the ``js_data()`` and State errors do,
            the entry, and where inside the entry the ``Secret`` sits.

    """
    for name, value in css_data.items():
        path = _secret_path(value)
        if path is None:
            continue
        where = f" at {path}" if path else ""
        msg = f"Component {comp_cls.__name__}: css_data() entry {name!r} holds a citry.Secret{where}, "
        raise ValueError(msg + SECRET_IN_CSS_DATA_ADVICE)


def _secret_path(value: object) -> str | None:
    """
    Return where the first ``citry.Secret`` sits inside one ``css_data()`` value, or None when there is none.

    The path is written the way Python reads it back, such as ``[0]`` or
    ``["dark"]["token"]``, and is empty for a Secret that is the value
    itself. Only built-in dicts, lists, and tuples are opened, because
    reading any other object could run its code; such an object is not
    searched, and with CSS the stylesheet then refuses it as a value CSS
    cannot hold. The walk uses a list rather than recursion, so a deeply
    nested value cannot exhaust Python's stack.
    """
    # Each entry keeps the keys that lead to it, and only the keys of the
    # path to a Secret are turned into text, so no other key's code runs.
    pending: list[tuple[object, tuple[object, ...]]] = [(value, ())]
    seen: set[int] = set()
    while pending:
        current, keys = pending.pop()
        # Markers are removed by their exact type, so a wrapped lazy object
        # is not asked for its class.
        unwrapped, current = _unwrap_const_markers(current)
        if not unwrapped:
            # A Const that wraps itself fails with its own error later.
            continue
        current_type = type(current)
        if current_type is Secret:
            return "".join(_key_text(key) for key in keys)
        # A container that holds itself is opened only once.
        if id(current) in seen:
            continue
        if current_type is dict:
            seen.add(id(current))
            items = list(cast("dict[object, object]", current).items())
            # Reversed, so the first item is the first one taken back off the list.
            pending.extend((item, (*keys, key)) for key, item in reversed(items))
        elif current_type is list or current_type is tuple:
            seen.add(id(current))
            indexed = list(enumerate(cast("list[object]", current)))
            pending.extend((item, (*keys, index)) for index, item in reversed(indexed))
    return None


def _key_text(key: object) -> str:
    """Write one key of a path the way Python reads it back, or name the type of a key that has no plain text."""
    if type(key) is str:
        return f"[{json.dumps(key, ensure_ascii=False)}]"
    if type(key) is int or type(key) is bool or type(key) is float or key is None:
        return f"[{key!r}]"
    # The key's own text could run its code, so only its type is named.
    return f"[<{_safe_class_text(type(key), '__name__') or 'other'} key>]"


def _cache_component_css_vars_capture(
    comp_cls: type[Component],
    css_data: Mapping[str, object],
) -> _VariablesScriptCapture | None:
    # Checked before the early return below, so a Secret fails the render
    # whether or not the component has CSS to read it.
    _reject_secret_css_data(comp_cls, css_data)
    if not has_component_asset("css", comp_cls):
        return None
    # JSON encoding rejects non-finite numbers before the canonical capture can
    # name the offending CSS entry. Preflight every exact-string entry through
    # the same serializer so all supported and rejected scalar types receive
    # the component-local diagnostic. The canonical capture repeats this check
    # because cache artifacts enter below this live-Python boundary.
    for name, value in css_data.items():
        if type(name) is not str:
            continue
        try:
            validate_css_var_name(name)
            serialize_css_var_value(const_value(value))
        except (TypeError, ValueError) as error:
            msg = f"Component {comp_cls.class_id!r} css_data() entry {name!r} cannot be emitted: {error}"
            raise ValueError(msg) from error
    source_json = _vars_json(css_data)
    # New stylesheets are named with the first key, which follows the first `secret` entry.
    capture = _css_vars_capture(comp_cls.class_id, source_json, _new_css_data_key(comp_cls.citry))
    _store_css_data_stylesheet(comp_cls.citry, comp_cls.class_id, capture)
    return capture


def _store_css_data_stylesheet(citry: Citry, class_id: str, capture: _VariablesScriptCapture) -> None:
    """
    Write one ``css_data()`` stylesheet to a configured cache, so any worker can serve its URL.

    Each distinct ``css_data()`` result is its own stylesheet, so values that
    change per request (a per-user color, say) make a new one each time.
    Without a configured cache, the engine's default cache has no limit, so
    it never receives them: the page publishes them into this process's
    store of page files when it is written (see
    ``citry.ext.dependencies.emission.publish_css_data_stylesheets``).
    """
    # _vue.events imports this module, so importing it here at load time
    # would be circular.
    from citry._vue.events import keeps_assets_in_process_only  # noqa: PLC0415

    if keeps_assets_in_process_only(citry):
        return
    # The key is named by the stylesheet's inputs, not its bytes, and a
    # worker of another Citry version may have written other bytes, so the
    # stored value is compared on every render and replaced when it differs.
    key = gen_cache_key(class_id, "css", capture.variables_hash)
    if citry.cache.get(key) != capture.cache_value:
        citry.cache.set(key, capture.cache_value)


def cache_component_css_vars(comp_cls: type[Component], css_data: Mapping[str, object]) -> str | None:
    """
    Build the stylesheet delivering one distinct ``css_data()`` result, returning its hash.

    With a configured cache, the stylesheet is also written there; without
    one, the page that uses it stores it when it is written.

    The stylesheet defines the data as CSS custom properties scoped to the
    instances rendered with this data: their root elements carry a
    ``data-ccss-<hash>`` marker, and the stylesheet targets it::

        [data-ccss-a1b2c3] {
          --row-color: red;
        }

    so the component's CSS reads them with ``var(--row-color)``. Identical
    data shares one stylesheet. Returns ``None`` when the class has no CSS
    (there is nothing that could read the properties).
    """
    capture = _cache_component_css_vars_capture(comp_cls, css_data)
    return None if capture is None else capture.variables_hash


# A served file's extension becomes part of its URL, of the name a request
# sends back, and of its cache key. Only these ASCII characters reach the
# server as the page wrote them: a browser cuts the URL at `#` or `?`,
# turns `\` into `/`, and sends other characters percent-encoded, which
# some servers hand on undecoded (a WSGI server gives the path as latin-1).
# None of them is a space or control character, which some backends refuse
# in a key (memcached through Django) and would answer 500 instead of 404.
# Memcached allows keys of up to 250 bytes, and 128 characters of extension
# keep the whole key, with Citry's prefix and a host framework's own
# prefix, below that.
_ASSET_EXTENSION_SHAPE = re.compile(r"[A-Za-z0-9._~+-]{0,128}")
_ASSET_HASH_SHAPE = re.compile(r"[0-9a-f]{12}")


def servable_asset_extension(extension: str) -> bool:
    """Return whether a local file with this extension can be linked as ``asset/<hash>.<extension>``."""
    return _ASSET_EXTENSION_SHAPE.fullmatch(extension) is not None


def servable_asset_name(file_name: str) -> bool:
    """Return whether ``file_name`` has the ``<12 hex>.<extension>`` shape that ``cache_asset`` writes."""
    content_hash, dot, extension = file_name.partition(".")
    return bool(dot) and _ASSET_HASH_SHAPE.fullmatch(content_hash) is not None and servable_asset_extension(extension)


def gen_asset_cache_key(file_name: str) -> str:
    """The cache key for one served ``Dependencies`` file (``file_name`` is ``<content hash>.<ext>``)."""
    return f"{_CACHE_PREFIX}:asset:{file_name}"


def cache_asset(citry: Citry, content: str, extension: str) -> str:
    """
    Store one local file's content for the asset endpoint, returning its name.

    The name is ``<content hash>.<ext>``: the hash fingerprints the URL, so a
    changed file gets a new URL and browsers can cache the old one forever.
    """
    file_name = f"{md5(content.encode(), usedforsecurity=False).hexdigest()[:12]}.{extension}"
    # The name is the content's hash, so the backend is asked at most once
    # per recheck interval whether it holds the file.
    _store_if_missing(citry, citry.cache, gen_asset_cache_key(file_name), lambda: content)
    return file_name


def evict_component_scripts(comp_cls: type[Component]) -> None:
    """
    Drop the class's cached JS and CSS, so the next use re-caches from fresh
    content. Called on ``Component.reset_files()``.
    """
    if _COMPONENT_SCRIPT_CAPTURE in vars(comp_cls):
        delattr(comp_cls, _COMPONENT_SCRIPT_CAPTURE)
    evict_component_script_keys(comp_cls.citry, comp_cls.class_id)


def evict_component_script_keys(citry: Citry, class_id: str) -> None:
    """Drop class-level JS and CSS cache entries for one stable class ID after unregistration."""
    for script_type in ("js", "css"):
        key = gen_cache_key(class_id, script_type)
        citry.cache.delete(key)
        _forget_stored_key(citry, key)
