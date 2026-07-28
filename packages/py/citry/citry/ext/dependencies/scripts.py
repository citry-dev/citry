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
    citry:<class_id>:js:<hash>       a generated js_data() variables script
    citry:<class_id>:css:<hash>      a generated css_data() variables stylesheet

Design: docs/design/dependencies.md section 4.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from hashlib import md5, sha256
from typing import TYPE_CHECKING

from citry.constness import const_value
from citry.ext.dependencies.types import Script, ScriptType, Style
from citry.util.css import serialize_css_var_value, validate_css_var_name

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry import Citry
    from citry.component import Component

_CACHE_PREFIX = "citry"

# `$component(` in a component's JS is sugar for registering the callback
# with the client-side manager under this component's class id.
_COMPONENT_RE = re.compile(r"\$component\s*\(")


@dataclass(frozen=True, slots=True)
class _VariablesScriptCapture:
    """Canonical source and exact cache value for one variables dependency."""

    source_json: str
    variables_hash: str
    cache_value: str


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

    ``$component(({ els, id, data }) => { ... })`` becomes
    ``Citry.manager.registerComponent("<class_id>", ...)``: the callback is
    registered with the client-side manager, which runs it for every rendered
    instance of this component (the elements carrying the instance's
    ``data-cid-<id>`` marker, with the instance's ``js_data()`` result).
    """
    return _COMPONENT_RE.sub(f'Citry.manager.registerComponent("{class_id}", ', js_content)


def _component_content(script_type: ScriptType, comp_cls: type[Component]) -> str | None:
    """Return substantive component JS/CSS, treating blank content as absent."""
    content = comp_cls.get_js() if script_type == "js" else comp_cls.get_css()
    return content if content and content.strip() else None


def has_component_asset(script_type: ScriptType, comp_cls: type[Component]) -> bool:
    """Whether the component carries non-whitespace JS or CSS content."""
    return _component_content(script_type, comp_cls) is not None


def uses_component(comp_cls: type[Component]) -> bool:
    """Whether the class's JS registers a per-instance callback via ``$component``."""
    content = _component_content("js", comp_cls)
    return content is not None and "$component" in content


def _component_script(script_type: ScriptType, comp_cls: type[Component]) -> Script | Style | None:
    """Build the class-level cached object for the component's current content."""
    content = _component_content(script_type, comp_cls)
    if content is None:
        return None
    if script_type == "js":
        transformed = transform_component(content, comp_cls.class_id)
        return Script(kind="component", content=transformed, origin_class_id=comp_cls.class_id)

    return Style(kind="component", content=content, origin_class_id=comp_cls.class_id)


def _cache_component_script(
    script_type: ScriptType,
    comp_cls: type[Component],
    *,
    force: bool = False,
) -> tuple[Script | Style, str] | None:
    """Return this class version's object and make the shared cache agree with it."""
    script = _component_script(script_type, comp_cls)
    if script is None:
        return None

    cache = comp_cls.citry.cache
    serialized = json.dumps(script.to_json())
    content_hash = md5(serialized.encode(), usedforsecurity=False).hexdigest()[:12]
    versioned_key = gen_component_cache_key(comp_cls.class_id, script_type, content_hash)
    if force or cache.get(versioned_key) != serialized:
        cache.set(versioned_key, serialized)

    # Keep the original stable key for old URLs and integrations. It is a
    # mutable compatibility entry, so every reader validates it against its
    # current class before returning. Generated URLs use the immutable key.
    stable_key = gen_cache_key(comp_cls.class_id, script_type)
    if force or cache.get(stable_key) != serialized:
        cache.set(stable_key, serialized)
    # Return the object built from this class, rather than reading the shared
    # key again. An old and new worker can legitimately alternate writes
    # during a rolling deployment; neither may serve the other's version.
    return script, content_hash


def cache_component_js(comp_cls: type[Component], *, force: bool = False) -> None:
    """
    Store the class's ``Component.js`` in the cache as a serialized ``Script``.

    The ``$component`` sugar is expanded here, once per class, so both the
    inlined tag and the URL-served file carry the expanded form. Does nothing
    for a component with no JS. Skips the write when the stored payload already
    matches this class version, unless ``force`` is set (used after a file
    reset). A deterministic class ID can be shared by replacement classes, so
    existence alone is not enough to establish a cache hit.
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
    cached = citry.cache.get(gen_component_cache_key(class_id, script_type, content_hash))
    if cached is None:
        return None
    data = json.loads(cached)
    return Script.from_json(data) if script_type == "js" else Style.from_json(data)


def get_script(
    script_type: ScriptType, comp_cls: type[Component], variables_hash: str | None = None
) -> Script | Style | None:
    """Read one cached object, validating class-level content against the current class."""
    if variables_hash is None:
        class_cached = _cache_component_script(script_type, comp_cls)
        return None if class_cached is None else class_cached[0]
    serialized = comp_cls.citry.cache.get(gen_cache_key(comp_cls.class_id, script_type, variables_hash))
    if serialized is None:
        return None
    data = json.loads(serialized)
    return Script.from_json(data) if script_type == "js" else Style.from_json(data)


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


def _hash_vars(data: Mapping[str, object]) -> tuple[str, str]:
    """
    Hash one ``js_data()``/``css_data()`` result.

    Returns ``(json_text, hash)``. The hash keys the generated variables
    script: identical data, however many instances or renders produce it,
    shares one cached script, and the browser receives it once.
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
    return json_text, sha256(json_text.encode()).hexdigest()[:32]


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


def _js_vars_capture(class_id: str, source_json: str) -> _VariablesScriptCapture:
    _canonical_variables_json(source_json)
    variables_hash = sha256(source_json.encode()).hexdigest()[:32]
    encoded = base64.b64encode(source_json.encode()).decode()
    content = f'Citry.manager.registerComponentData("{class_id}", "{variables_hash}", JSON.parse(atob("{encoded}")));'
    script = Script(kind="variables", content=content, origin_class_id=class_id)
    return _VariablesScriptCapture(
        source_json=source_json,
        variables_hash=variables_hash,
        cache_value=json.dumps(script.to_json()),
    )


def _css_vars_capture(class_id: str, source_json: str) -> _VariablesScriptCapture:
    data = _canonical_variables_json(source_json)
    variables_hash = sha256(source_json.encode()).hexdigest()[:32]
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
        cache_value=json.dumps(style.to_json()),
    )


def _cache_component_js_vars_capture(
    comp_cls: type[Component],
    js_data: Mapping[str, object],
) -> _VariablesScriptCapture | None:
    if not uses_component(comp_cls):
        return None
    source_json, _variables_hash = _hash_vars(js_data)
    capture = _js_vars_capture(comp_cls.class_id, source_json)
    cache = comp_cls.citry.cache
    key = gen_cache_key(comp_cls.class_id, "js", capture.variables_hash)
    if cache.get(key) != capture.cache_value:
        cache.set(key, capture.cache_value)
    return capture


def _cache_component_css_vars_capture(
    comp_cls: type[Component],
    css_data: Mapping[str, object],
) -> _VariablesScriptCapture | None:
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
    source_json, _variables_hash = _hash_vars(css_data)
    capture = _css_vars_capture(comp_cls.class_id, source_json)
    cache = comp_cls.citry.cache
    key = gen_cache_key(comp_cls.class_id, "css", capture.variables_hash)
    if cache.get(key) != capture.cache_value:
        cache.set(key, capture.cache_value)
    return capture


def cache_component_js_vars(comp_cls: type[Component], js_data: Mapping[str, object]) -> str | None:
    """
    Cache the script delivering one distinct ``js_data()`` result, returning its hash.

    The script registers the data with the client-side manager
    (``Citry.manager.registerComponentData``); the manager hands it to the
    component's ``$component`` callback for each instance rendered with
    this data. The JSON rides as base64, so data values cannot break out of
    the ``<script>`` tag. Returns ``None`` when the class has no JS (there is
    no callback the data could reach).
    """
    capture = _cache_component_js_vars_capture(comp_cls, js_data)
    return None if capture is None else capture.variables_hash


def cache_component_css_vars(comp_cls: type[Component], css_data: Mapping[str, object]) -> str | None:
    """
    Cache the stylesheet delivering one distinct ``css_data()`` result, returning its hash.

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
    key = gen_asset_cache_key(file_name)
    if not citry.cache.has(key):
        citry.cache.set(key, content)
    return file_name


def evict_component_scripts(comp_cls: type[Component]) -> None:
    """
    Drop the class's cached JS and CSS, so the next use re-caches from fresh
    content. Called on ``Component.reset_files()``.
    """
    evict_component_script_keys(comp_cls.citry, comp_cls.class_id)


def evict_component_script_keys(citry: Citry, class_id: str) -> None:
    """Drop class-level JS and CSS cache entries for one stable class ID after unregistration."""
    citry.cache.delete(gen_cache_key(class_id, "js"))
    citry.cache.delete(gen_cache_key(class_id, "css"))
