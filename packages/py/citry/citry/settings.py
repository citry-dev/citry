"""
The Citry settings schema.

``CitrySettings`` is the typed, immutable configuration for a ``Citry`` instance.
It starts small and grows field-by-field as the engine does. Unknown settings
are rejected: ``Citry`` accepts only the fields defined here.

See ``docs/design/extensions.md`` section 5.2 for the rationale (a real schema
object, not a loose dict).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, get_args

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from citry.cache import CitryCache
    from citry.extension import Extension

# The build environment (dev_prod_mode.md). Defined as a real value, not only a
# type annotation, so the allowed set can be derived from it for validation.
Mode = Literal["production", "development"]
_ALLOWED_MODES: tuple[str, ...] = get_args(Mode)


@dataclass(frozen=True, slots=True)
class CitrySettings:
    """
    Immutable settings for a ``Citry`` instance.

    Attributes:
        extensions: The extensions to install on the instance. Each entry is
            an ``Extension`` subclass, a ready-made instance, or an import
            string like ``"myapp.extensions.MyExtension"``. The set is fixed
            once the instance is constructed.
        extensions_defaults: Default config values for extensions, keyed by
            extension name, e.g. ``{"events": {"_csrf": True}}``. When an
            extension reads a config field for a component, the component's
            own nested config class wins, a value given here fills in next,
            and the extension's built-in default comes last.
        dirs: Directories searched when resolving a component's asset files
            (``template_file``, ``js_file``, ``css_file``, and ``Dependencies``
            entries), after the directory of the component's own ``.py`` file.
            Entries are converted to ``Path`` and must be absolute; this is
            validated at construction (a relative entry raises ``ValueError``).
        cache: Where citry stores what it caches: a
            [`CitryCache`][citry.CitryCache] object or an import string
            like ``"myapp.caching.MyCache"``. ``None`` gives the instance its
            own in-memory cache. The live backend built from this setting is
            ``Citry.cache``.
        sandbox_expressions: Whether template expressions (``{{ ... }}`` and
            dynamic ``c-*`` attributes) are evaluated in the security sandbox.
            On by default. Turning it off evaluates expressions as plain Python,
            which is faster but removes security guardrails.
            Only do so when every template comes from a trusted source.
        autodiscover: Whether to import the component modules under ``dirs`` the
            first time a component is looked up, so their classes register
            themselves without being imported by hand. On by default; when no
            ``dirs`` are set there is nothing to scan, so the default instance
            does nothing. The directories must be importable (on
            ``sys.path``/``PYTHONPATH``). See ``Citry.autodiscover`` and
            ``citry.autodiscovery``.
        mode: The build environment, ``"production"`` (the default) or
            ``"development"``. It is the single source of truth for whether the
            engine includes developer-only output: in ``"development"`` the
            built-in ``debug`` extension is auto-registered (visual component
            boundaries) and the client ownership graph carries source
            provenance. An unrecognized value raises ``ValueError`` at
            construction. See ``docs/design/dev_prod_mode.md``.
        template_globals: Variables exposed to every component's template
            without being returned from each ``template_data()``. They are
            merged into every component's template variables on render, so a
            template can reference one directly (``{{ site_name }}``). A
            component's own ``template_data`` wins when it returns a key of the
            same name, so globals act as defaults. The value given here is the
            starting set; the live, editable copy is ``Citry.template_globals``,
            which is how you add or change a global after the instance exists
            (including the default instance, created at import before your code
            runs).
        id_generator: A function returning the per-render id stamped on each
            component instance (``component.id``, which drives the
            ``data-cid-<id>`` markers that scope a component's CSS and JS on the
            page). Given as a callable or a ``"path.to.func"`` import string;
            passing a class also works: it is called once, and the resulting
            object is used as the generator (handy when the generator keeps
            state, like a counter). ``None`` uses the built-in generator. Override
            it for stable ids in snapshot tests. The generator must return ids
            that are unique among the components on one page and contain only
            lowercase ASCII letters, digits, hyphens, and underscores. The
            lowercase rule is required because the id is embedded in an HTML
            attribute name. This does not touch ``class_id``, which stays a
            stable hash of the component's import path.
        secret: The signing secret for values citry hands to the browser and
            must recognize when they come back, such as the state the Events
            extension round-trips on each event call. A single string is the
            common form. A list means key rotation: the first entry signs new
            values, and a value signed by any entry still verifies, so
            already-issued values stay valid while a new key rolls out. A bare
            string is stored as a one-element list. ``None`` (the default)
            means no secret is set. Django projects can reuse their existing
            key by passing ``citry.contrib.django.secret()``.
        event_result_resolvers: Result resolvers for the Events extension.
            When an event handler returns a value, citry converts it into the
            actions sent back to the browser (the instructions the client
            runtime applies: re-render this component, redirect, and so on).
            A resolver adds support for your own return types: it is given the
            handler's return value and either converts it into those actions
            or declines, letting the next resolver try. Resolvers run in
            order, after the built-in conversions; the first one to convert
            the value wins.
        event_payload_codecs: Payload codecs for the Events extension's HTTP
            endpoints. A codec reads one request format (identified by its
            content type) into the event call the extension expects, so
            clients are not limited to the built-in JSON, form, and query
            formats. Codecs given here are tried before the built-in ones, in
            order.

    """

    extensions: Sequence[type[Extension] | Extension | str] = ()
    extensions_defaults: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    dirs: tuple[Path, ...] = ()
    cache: CitryCache | str | None = None
    sandbox_expressions: bool = True
    autodiscover: bool = True
    mode: Mode = "production"
    template_globals: Mapping[str, Any] = field(default_factory=dict)
    # Advanced/niche settings
    id_generator: Callable[[], str] | str | None = None
    secret: str | list[str] | None = None
    event_result_resolvers: Sequence[Any] = ()
    event_payload_codecs: Sequence[Any] = ()

    def __post_init__(self) -> None:
        # Copy every input into its immutable stored shape, so a direct
        # CitrySettings(...) is as safe as one built through Citry(...):
        # changing a caller's list or dict after construction cannot reach
        # into these frozen settings, and both construction paths store the
        # same shape.

        # The build environment is a fixed set of strings. Reject an unknown
        # value here so a typo cannot silently ship or omit developer output;
        # every later read of the mode can then trust it (dev_prod_mode.md).
        if self.mode not in _ALLOWED_MODES:
            msg = f"Citry mode must be one of {_ALLOWED_MODES}, got {self.mode!r}"
            raise ValueError(msg)

        # Extensions are copied into a tuple of their own.
        object.__setattr__(self, "extensions", tuple(self.extensions))

        # Asset search dirs must be absolute, the same rule django-components
        # has for COMPONENTS.dirs. Relative lookups need no entry here: a
        # component's files already resolve against its own .py file. Each
        # entry is converted to Path and the whole is stored as a tuple.
        dir_paths = tuple(Path(d) for d in self.dirs)
        for dir_path in dir_paths:
            if not dir_path.is_absolute():
                msg = f"Citry dirs must be absolute paths, got {str(dir_path)!r}"
                raise ValueError(msg)
        object.__setattr__(self, "dirs", dir_paths)

        # The two config mappings are stored as fresh dicts, so changing the
        # caller's mapping cannot change these frozen settings.
        object.__setattr__(self, "extensions_defaults", dict(self.extensions_defaults))
        object.__setattr__(self, "template_globals", dict(self.template_globals))

        # A bare-string secret is stored as a one-element list, so readers
        # always see the rotation form: first entry signs, every entry verifies.
        if isinstance(self.secret, str):
            object.__setattr__(self, "secret", [self.secret])
        elif self.secret is not None:
            # A copy, so changing the caller's list cannot change these settings.
            object.__setattr__(self, "secret", list(self.secret))

        # The resolver and codec sequences are copied into tuples of their own.
        object.__setattr__(self, "event_result_resolvers", tuple(self.event_result_resolvers))
        object.__setattr__(self, "event_payload_codecs", tuple(self.event_payload_codecs))
