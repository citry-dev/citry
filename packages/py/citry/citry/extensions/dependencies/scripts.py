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
    citry:<class_id>:js:<hash>       a generated js_data() variables script
    citry:<class_id>:css:<hash>      a generated css_data() variables stylesheet

Design: docs/design/dependencies.md section 4.
"""

from __future__ import annotations

import base64
import json
import re
from hashlib import md5
from typing import TYPE_CHECKING

from citry.constness import const_value
from citry.extensions.dependencies.types import Script, ScriptType, Style
from citry.util.css import serialize_css_var_value

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry import Citry
    from citry.component import Component

_CACHE_PREFIX = "citry"

# `$onComponent(` in a component's JS is sugar for registering the callback
# with the client-side manager under this component's class id.
_ONCOMPONENT_RE = re.compile(r"\$onComponent\s*\(")


def gen_cache_key(class_id: str, script_type: ScriptType, variables_hash: str | None = None) -> str:
    """The cache key for one component script (see the module docstring for the scheme)."""
    if variables_hash:
        return f"{_CACHE_PREFIX}:{class_id}:{script_type}:{variables_hash}"
    return f"{_CACHE_PREFIX}:{class_id}:{script_type}"


def transform_oncomponent(js_content: str, class_id: str) -> str:
    """
    Expand the ``$onComponent(`` sugar in a component's JS.

    ``$onComponent(({ els, id, data }) => { ... })`` becomes
    ``Citry.manager.registerComponent("<class_id>", ...)``: the callback is
    registered with the client-side manager, which runs it for every rendered
    instance of this component (the elements carrying the instance's
    ``data-cid-<id>`` marker, with the instance's ``js_data()`` result).
    """
    return _ONCOMPONENT_RE.sub(f'Citry.manager.registerComponent("{class_id}", ', js_content)


def uses_oncomponent(comp_cls: type[Component]) -> bool:
    """Whether the class's JS registers a per-instance callback via ``$onComponent``."""
    content = comp_cls.get_js()
    return content is not None and "$onComponent" in content


def cache_component_js(comp_cls: type[Component], *, force: bool = False) -> None:
    """
    Store the class's ``Component.js`` in the cache as a serialized ``Script``.

    The ``$onComponent`` sugar is expanded here, once per class, so both the
    inlined tag and the URL-served file carry the expanded form. Does nothing
    for a component with no JS. Skips the write when the entry already exists,
    unless ``force`` is set (used after a file reset).
    """
    content = comp_cls.get_js()
    if not content or not content.strip():
        return
    cache = comp_cls.citry.cache
    key = gen_cache_key(comp_cls.class_id, "js")
    if not force and cache.has(key):
        return
    transformed = transform_oncomponent(content, comp_cls.class_id)
    script = Script(kind="component", content=transformed, origin_class_id=comp_cls.class_id)
    cache.set(key, json.dumps(script.to_json()))


def cache_component_css(comp_cls: type[Component], *, force: bool = False) -> None:
    """The CSS counterpart of :func:`cache_component_js`."""
    content = comp_cls.get_css()
    if not content or not content.strip():
        return
    cache = comp_cls.citry.cache
    key = gen_cache_key(comp_cls.class_id, "css")
    if not force and cache.has(key):
        return
    style = Style(kind="component", content=content, origin_class_id=comp_cls.class_id)
    cache.set(key, json.dumps(style.to_json()))


def get_script(
    script_type: ScriptType, comp_cls: type[Component], variables_hash: str | None = None
) -> Script | Style | None:
    """Read one cached script back as a ``Script``/``Style`` object, or ``None`` when absent."""
    cached = comp_cls.citry.cache.get(gen_cache_key(comp_cls.class_id, script_type, variables_hash))
    if cached is None:
        return None
    data = json.loads(cached)
    return Script.from_json(data) if script_type == "js" else Style.from_json(data)


def get_component_script(script_type: ScriptType, comp_cls: type[Component]) -> Script | Style | None:
    """
    The class's own JS/CSS as a cached object, repopulating the cache on a miss.

    This is the lazy-repopulation rule (docs/design/dependencies.md section
    4.3): class-level scripts can always be rebuilt from the class itself, so
    a cache miss (fresh process, evicted entry) just re-caches and retries.

    Returns ``None`` when the component has no JS/CSS at all.
    """
    script = get_script(script_type, comp_cls)
    if script is not None:
        return script
    if script_type == "js":
        cache_component_js(comp_cls)
    else:
        cache_component_css(comp_cls)
    return get_script(script_type, comp_cls)


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
    json_text = json.dumps(data, default=_json_default)
    return json_text, md5(json_text.encode(), usedforsecurity=False).hexdigest()[:6]


def cache_component_js_vars(comp_cls: type[Component], js_data: Mapping[str, object]) -> str | None:
    """
    Cache the script delivering one distinct ``js_data()`` result, returning its hash.

    The script registers the data with the client-side manager
    (``Citry.manager.registerComponentData``); the manager hands it to the
    component's ``$onComponent`` callback for each instance rendered with
    this data. The JSON rides as base64, so data values cannot break out of
    the ``<script>`` tag. Returns ``None`` when the class has no JS (there is
    no callback the data could reach).
    """
    if not uses_oncomponent(comp_cls):
        return None
    json_text, vars_hash = _hash_vars(js_data)
    cache = comp_cls.citry.cache
    key = gen_cache_key(comp_cls.class_id, "js", vars_hash)
    if not cache.has(key):
        encoded = base64.b64encode(json_text.encode()).decode()
        content = (
            f'Citry.manager.registerComponentData("{comp_cls.class_id}", "{vars_hash}",'
            f' JSON.parse(atob("{encoded}")));'
        )
        script = Script(kind="variables", content=content, origin_class_id=comp_cls.class_id)
        cache.set(key, json.dumps(script.to_json()))
    return vars_hash


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
    if not comp_cls.get_css():
        return None
    _, vars_hash = _hash_vars(css_data)
    cache = comp_cls.citry.cache
    key = gen_cache_key(comp_cls.class_id, "css", vars_hash)
    if not cache.has(key):
        lines = [f"  --{name}: {serialize_css_var_value(value)};" for name, value in css_data.items()]
        content = "\n".join([f"/* {comp_cls.class_id} */", f"[data-ccss-{vars_hash}] {{", *lines, "}"])
        style = Style(kind="variables", content=content, origin_class_id=comp_cls.class_id)
        cache.set(key, json.dumps(style.to_json()))
    return vars_hash


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
    cache = comp_cls.citry.cache
    cache.delete(gen_cache_key(comp_cls.class_id, "js"))
    cache.delete(gen_cache_key(comp_cls.class_id, "css"))
